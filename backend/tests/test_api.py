"""API tests with FAKE M2/M3 modules (master guide Section 14, tests 1-10).

The fake data below is test-only; it is never served by the real app.
"""
import json
import sys
import time
import types

import pytest
from fastapi.testclient import TestClient

import cache
import config
import fallback.loader as fb_loader
from assessment import compute_score
from main import app
from schemas import Metrics

client = TestClient(app, raise_server_exceptions=False)
START = "2027-03-14T06:00:00Z"
DEM = {"name": "TEST DEM", "resolution_m": 10, "coverage": "test", "retrieved_utc": "2026-11-14T00:00:00Z"}
# Same field names as M3's real data/sites.json
SITE_A = {"id": "site_a", "name": "Site A", "lat": -89.5, "lon": 10.0, "height_m": 100.0,
          "kind": "candidate_region", "coords_source_url": "https://example.org/a/page",
          "coords_class": "PUBLISHED"}
# Same shape as M3's real data/horizon_<id>.json
HORIZON_A = {"deg": [1.0] * 360, "dem": DEM, "approx": False, "class": "CALCULATED", "status": "OK"}
METRICS = {"sunlit_geom_pct": 70.0, "sunlit_terrain_pct": 60.0, "earth_geom_pct": 50.0,
           "earth_terrain_pct": 40.0, "longest_dark_h": 20.0, "longest_comms_gap_h": 30.0,
           "max_sun_el_deg": 1.5}


@pytest.fixture(autouse=True)
def _reset(monkeypatch, tmp_path):
    cache.clear()
    monkeypatch.setattr(config, "RETRY_BACKOFF_S", 0.0)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)  # empty data/ unless a test fills it
    # Block any real M2/M3 modules unless a test installs fakes.
    for name in ("terrain.slope", "terrain.hazard", "science.runtime"):
        monkeypatch.setitem(sys.modules, name, None)


class Fakes:
    def __init__(self, monkeypatch, data_dir):
        self.mp = monkeypatch
        self.data_dir = data_dir
        self.calls = {"compute": 0}
        self.compute_impl = self._compute

    def mod(self, name, **attrs):
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        self.mp.setitem(sys.modules, name, m)

    def _compute(self, lat, lon, start, hours, step, horizon_deg):
        self.calls["compute"] += 1
        terr = [True, False] if horizon_deg is not None else [None, None]
        return {"timeseries": {"start_utc": start, "step_min": step, "sun_el": [1.0, -1.0],
                               "sun_az": [10.0, 20.0], "earth_el": [2.0, 3.0], "earth_az": [5.0, 6.0],
                               "sun_lit_geom": [True, False], "sun_lit_terrain": [True, True],
                               "earth_vis_geom": [True, True], "earth_vis_terrain": [True, True]},
                "metrics": dict(METRICS)}

    def install(self):
        (self.data_dir / "sites.json").write_text(json.dumps({"sites": [SITE_A]}))
        (self.data_dir / "horizon_site_a.json").write_text(json.dumps(HORIZON_A))
        self.mod("terrain.slope", get_slope=lambda lat, lon, r: {"slope_mean_deg": 5.0, "slope_max_deg": 12.0, "roughness_m": 0.4})
        self.mod("terrain.hazard", get_hazard=lambda lat, lon: {"reasons": [{"class": "FAIL", "code": "SLOPE"}]})
        self.mod("science.runtime",
                 compute_timeseries=lambda *a: self.compute_impl(*a),
                 window_metrics=lambda sid, dates: [{"start_utc": d, "metrics": dict(METRICS)} for d in dates],
                 estimate_power=lambda ts, panel: {"power_w": [1.0, 0.0], "peak_w": 1.0, "energy_wh": 0.5})
        return self


@pytest.fixture
def fakes(monkeypatch, tmp_path):
    return Fakes(monkeypatch, tmp_path).install()


SCEN_A = {"site_id": "site_a", "start_utc": START}
SCEN_CUSTOM = {"lat": -89.5, "lon": 0.0, "start_utc": START}


# ---- 10: openapi, health ----------------------------------------------------
def test_openapi_opens():
    r = client.get("/api/openapi.json")
    assert r.status_code == 200 and "/api/timeline" in r.json()["paths"]


def test_health_envelope_without_data_is_degraded():
    body = client.get("/api/health").json()
    assert set(body) == {"data", "provenance", "warnings", "cached"}
    assert body["data"]["status"] == "degraded"
    assert body["provenance"]["class"] == "CALCULATED"


# ---- 1/2: validation through the real app -----------------------------------
def test_lat_95_gives_400_invalid_coordinate():
    r = client.post("/api/illumination", json={"lat": 95, "lon": 0, "start_utc": START})
    assert r.status_code == 400 and r.json()["error"]["code"] == "INVALID_COORDINATE"


def test_bad_date_gives_400():
    r = client.post("/api/timeline", json={"site_id": "a", "start_utc": "yesterday"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "INVALID_DATE"


def test_empty_compare_scenarios_is_clear_error():
    r = client.post("/api/compare", json={"scenarios": []})
    assert r.status_code == 400 and r.json()["error"]["code"] == "EMPTY_SCENARIO"


# ---- data / modules not merged yet -> 501, not a crash ----------------------
def test_missing_sites_file_gives_501():
    r = client.get("/api/sites")
    assert r.status_code == 501 and r.json()["error"]["code"] == "FEATURE_NOT_AVAILABLE"


def test_missing_science_runtime_gives_501(tmp_path):
    (tmp_path / "sites.json").write_text(json.dumps({"sites": [SITE_A]}))
    r = client.post("/api/timeline", json=SCEN_A)
    assert r.status_code == 501 and "science.runtime" in r.json()["error"]["message"]


# ---- 4: site not found ------------------------------------------------------
def test_site_not_found_404(fakes):
    assert client.get("/api/sites/zzz").status_code == 404
    assert client.post("/api/timeline", json={"site_id": "zzz", "start_utc": START}).status_code == 404


def test_sites_list_and_detail(fakes):
    body = client.get("/api/sites").json()
    site = body["data"]["sites"][0]
    assert site["class"] == "PUBLISHED" and site["kind"] == "candidate_region" and site["height_m"] == 100.0
    assert site["source_url"] == "https://example.org/a/page"
    assert body["provenance"]["inputs"][0]["url"] == "https://example.org/a/page"
    assert body["warnings"] == []
    assert client.get("/api/sites/site_a").json()["data"]["id"] == "site_a"


# ---- timeline: v2 shape + honesty about terrain ------------------------------
def test_timeline_curated_site_has_terrain(fakes):
    body = client.post("/api/timeline", json=SCEN_A).json()
    d = body["data"]
    assert d["site"]["id"] == "site_a" and d["frame"] == "MOON_ME"
    assert len(d["horizon"]["deg"]) == 360 and d["horizon"]["approx"] is False
    assert d["metrics"]["sunlit_terrain_pct"] == 60.0
    assert body["provenance"]["class"] == "CALCULATED" and body["provenance"]["assumptions"]


def test_timeline_custom_point_terrain_is_null_and_approx(fakes):
    body = client.post("/api/timeline", json=SCEN_CUSTOM).json()
    d = body["data"]
    assert d["horizon"]["deg"] is None and d["horizon"]["approx"] is True
    assert d["timeseries"]["sun_lit_terrain"] == [None, None]
    assert d["metrics"]["sunlit_terrain_pct"] is None and d["metrics"]["earth_terrain_pct"] is None
    assert d["metrics"]["sunlit_geom_pct"] == 70.0
    assert any("UNAVAILABLE" in w for w in body["warnings"])


def test_ephemeris_and_power_and_terrain(fakes):
    e = client.post("/api/ephemeris", json={"site_id": "site_a", "time_utc": START}).json()
    # /api/ephemeris is built from compute_timeseries index 0: sun el/az 1.0/10.0, sunset at step 1 = 0.5 h
    assert e["data"]["sun"] == {"el": 1.0, "az": 10.0} and e["data"]["hours_to_earthset"] is None
    assert e["data"]["hours_to_sunset"] == 0.5
    p = client.post("/api/power/estimate", json={**SCEN_A, "panel": {"area_m2": 1, "efficiency": 0.2}}).json()
    assert p["provenance"]["class"] == "ESTIMATED" and p["data"]["peak_w"] == 1.0
    h = client.post("/api/terrain/horizon", json={"site_id": "site_a"}).json()
    assert h["data"]["horizon"]["dem"]["name"] == "TEST DEM"
    h2 = client.post("/api/terrain/horizon", json={"lat": -89.5, "lon": 0}).json()
    assert h2["provenance"]["class"] == "UNAVAILABLE" and h2["provenance"]["reason"]
    s = client.post("/api/terrain/slope", json={"site_id": "site_a"}).json()
    assert s["data"]["hazard_flags"] == ["FAIL:SLOPE"]


# ---- 7: cache ---------------------------------------------------------------
def test_second_identical_request_is_cached(fakes):
    first = client.post("/api/timeline", json=SCEN_A).json()
    second = client.post("/api/timeline", json=SCEN_A).json()
    assert first["cached"] is False and second["cached"] is True
    assert fakes.calls["compute"] == 1
    assert second["provenance"]["generated_utc"] == first["provenance"]["generated_utc"]


# ---- 5/6: failures -> 503 ---------------------------------------------------
def test_module_failure_gives_503(fakes):
    def boom(*a):
        raise RuntimeError("ephemeris file corrupt")
    fakes.compute_impl = boom
    r = client.post("/api/timeline", json=SCEN_A)
    assert r.status_code == 503 and r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_timeout_retries_then_503(fakes, monkeypatch):
    monkeypatch.setattr(config, "CALL_TIMEOUT_S", 0.05)
    def slow(*a):
        time.sleep(0.3)
    fakes.compute_impl = slow
    r = client.post("/api/timeline", json=SCEN_A)
    assert r.status_code == 503 and "timed out" in r.json()["error"]["message"]
    assert r.json()["error"]["details"]["attempts"] == 3  # 1 try + 2 retries


def test_bad_shape_from_module_is_503_not_500(fakes):
    fakes.compute_impl = lambda *a: {"timeseries": {"sun_el": [1.0, 2.0], "sun_az": [1.0]}, "metrics": {}}
    assert client.post("/api/timeline", json=SCEN_A).status_code == 503


# ---- fallback (F32) ---------------------------------------------------------
def test_fallback_used_when_live_fails_and_is_labelled(fakes, monkeypatch, tmp_path):
    first = client.post("/api/timeline", json=SCEN_A).json()
    cache.clear()
    first["provenance"]["class"] = "ILLUSTRATIVE"
    (tmp_path / "x.json").write_text(json.dumps({
        "match": {"site_id": "site_a", "start_utc": START, "hours": 708}, "envelope": first}))
    monkeypatch.setattr(fb_loader, "FALLBACK_DIR", tmp_path)
    fakes.compute_impl = lambda *a: (_ for _ in ()).throw(RuntimeError("down"))
    r = client.post("/api/timeline", json=SCEN_A)
    body = r.json()
    assert r.status_code == 200 and body["cached"] is True
    assert body["provenance"]["class"] == "ILLUSTRATIVE"
    assert "fallback" in body["warnings"][0].lower()


# ---- 8: assessment ----------------------------------------------------------
def test_assessment_pass_fail(fakes):
    reqs = [{"id": "min_sunlit", "threshold": 50}, {"id": "min_earth", "threshold": 45},
            {"id": "max_dark_hours", "threshold": 30}]
    body = client.post("/api/assessment", json={"scenario": SCEN_A, "requirements": reqs}).json()
    st = {r["id"]: r["status"] for r in body["data"]["results"]}
    assert st == {"min_sunlit": "pass", "min_earth": "fail", "max_dark_hours": "pass"}
    assert body["data"]["overall"] == "fail"
    assert body["data"]["score"]["value"] == round(0.4 * 60 + 0.3 * 40 + 0.3 * 80, 1)


def test_assessment_missing_terrain_is_unknown_not_pass(fakes):
    reqs = [{"id": "min_sunlit", "threshold": 1}, {"id": "max_dark_hours", "threshold": 999}]
    body = client.post("/api/assessment", json={"scenario": SCEN_CUSTOM, "requirements": reqs}).json()
    assert [r["status"] for r in body["data"]["results"]] == ["unknown", "unknown"]
    assert body["data"]["overall"] == "unknown" and body["data"]["score"]["value"] is None
    assert body["data"]["results"][0]["missing_info"]


def test_assessment_geometric_basis_on_custom_point(fakes):
    reqs = [{"id": "min_sunlit", "threshold": 50, "basis": "geometric"}]
    r = client.post("/api/assessment", json={"scenario": SCEN_CUSTOM, "requirements": reqs}).json()
    assert r["data"]["results"][0]["status"] == "pass"
    assert r["data"]["results"][0]["confidence"] == "low"


def test_score_needs_every_input():
    assert compute_score(Metrics(sunlit_terrain_pct=50), True).value is None
    assert compute_score(None, True).value is None


# ---- compare / report / thermal ---------------------------------------------
def test_compare_three_scenarios(fakes):
    body = client.post("/api/compare", json={"scenarios": [SCEN_A, SCEN_CUSTOM, SCEN_A]}).json()
    items = body["data"]["items"]
    assert [i["label"] for i in items] == ["Scenario 1", "Scenario 2", "Scenario 3"]
    assert items[1]["horizon_approx"] is True and items[0]["horizon_approx"] is False


def test_date_scan_curated_ok_custom_501(fakes):
    ok = client.post("/api/compare", json={"mode": "date_scan", "date_scan": {
        "site_id": "site_a", "start_dates": [START, "2027-04-01T00:00:00Z"]}}).json()
    assert len(ok["data"]["scan"]) == 2 and ok["data"]["site"]["id"] == "site_a"
    r = client.post("/api/compare", json={"mode": "date_scan", "date_scan": {
        "lat": -89, "lon": 0, "start_dates": [START]}})
    assert r.status_code == 501


def test_date_scan_surfaces_preliminary_window_warnings(fakes):
    runtime = sys.modules["science.runtime"]
    runtime.window_metrics = lambda sid, dates: [
        {
            "start_utc": date,
            "metrics": dict(METRICS),
            "status": "PRELIMINARY",
            "warnings": ["DEM frame confirmation is pending."],
        }
        for date in dates
    ]
    body = client.post("/api/compare", json={"mode": "date_scan", "date_scan": {
        "site_id": "site_a", "start_dates": [START]}}).json()

    assert any("DEM frame confirmation is pending" in warning for warning in body["warnings"])
    assert any("PRELIMINARY" in warning for warning in body["warnings"])


def test_report_has_sections_and_hash(fakes):
    body = client.post("/api/report", json={"scenario": SCEN_A,
                       "requirements": [{"id": "min_sunlit", "threshold": 50}]}).json()["data"]
    assert len(body["request_hash"]) == 64 and body["report_id"] == body["request_hash"][:12]
    s = body["sections"]
    assert s["thermal"]["class"] == "UNAVAILABLE" and s["assessment"]["overall"] == "pass"
    assert s["limitations"] and body["disclaimer"]


# ---- 9: thermal -------------------------------------------------------------
def test_thermal_is_501_unavailable():
    r = client.post("/api/thermal/analysis", json={"site_id": "site_a"})
    assert r.status_code == 501
    assert r.json()["error"]["details"]["class"] == "UNAVAILABLE"


# ---- data files: honesty and robustness -------------------------------------
def test_home_page_source_link_is_warned(tmp_path):
    bad = {**SITE_A, "coords_source_url": "https://trek.nasa.gov/"}
    (tmp_path / "sites.json").write_text(json.dumps({"sites": [bad]}))
    body = client.get("/api/sites").json()
    assert any("general website" in w for w in body["warnings"])


def test_site_without_coordinates_is_listed_but_not_computable(fakes, tmp_path):
    nocoord = {**SITE_A, "id": "no_coord", "lat": None, "lon": None}
    (tmp_path / "sites.json").write_text(json.dumps({"sites": [SITE_A, nocoord]}))
    listed = client.get("/api/sites").json()
    assert any("UNAVAILABLE" in w for w in listed["warnings"])
    assert client.post("/api/timeline", json={"site_id": "no_coord", "start_utc": START}).status_code == 503


def test_curated_site_without_horizon_file_is_geometric_only(fakes, tmp_path):
    other = {**SITE_A, "id": "site_b"}
    (tmp_path / "sites.json").write_text(json.dumps({"sites": [SITE_A, other]}))
    body = client.post("/api/timeline", json={"site_id": "site_b", "start_utc": START}).json()
    assert body["data"]["horizon"]["deg"] is None and body["data"]["horizon"]["approx"] is True
    assert body["data"]["metrics"]["sunlit_terrain_pct"] is None
    assert any("horizon_site_b.json" in w for w in body["warnings"])


def test_horizon_with_gaps_disables_terrain(fakes, tmp_path):
    gappy = {**HORIZON_A, "deg": [1.0] * 359 + [None], "status": "PARTIAL_COVERAGE", "approx": True}
    (tmp_path / "horizon_site_a.json").write_text(json.dumps(gappy))
    body = client.post("/api/timeline", json=SCEN_A).json()
    assert body["data"]["horizon"]["deg"] is None
    assert any("partial coverage" in w for w in body["warnings"])


def test_horizon_file_without_dem_meta_is_503(fakes, tmp_path):
    (tmp_path / "horizon_site_a.json").write_text(json.dumps({"deg": [1.0] * 360, "approx": False}))
    assert client.post("/api/timeline", json=SCEN_A).status_code == 503


def test_empty_dem_retrieval_time_is_warned(fakes, tmp_path):
    h = {**HORIZON_A, "dem": {**DEM, "retrieved_utc": ""}}
    (tmp_path / "horizon_site_a.json").write_text(json.dumps(h))
    body = client.post("/api/timeline", json=SCEN_A).json()
    assert any("retrieval time is missing" in w for w in body["warnings"])


def test_utf16_files_are_readable(fakes, tmp_path):
    (tmp_path / "horizon_site_a.json").write_text(json.dumps(HORIZON_A), encoding="utf-16")
    assert client.post("/api/timeline", json=SCEN_A).status_code == 200


def test_broken_json_is_503_with_file_name(fakes, tmp_path):
    (tmp_path / "horizon_site_a.json").write_text("{not json")
    r = client.post("/api/timeline", json=SCEN_A)
    assert r.status_code == 503 and "horizon_site_a.json" in r.json()["error"]["message"]


def test_path_tricks_in_site_id_are_404(fakes):
    r = client.post("/api/terrain/horizon", json={"site_id": "../sites"})
    assert r.status_code == 404
