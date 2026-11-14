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
SITE_A = {"id": "site_a", "name": "Site A", "region": "R", "lat": -89.5, "lon": 10.0,
          "source_url": "https://example.org/a", "class": "PUBLISHED", "notes": None}
METRICS = {"sunlit_geom_pct": 70.0, "sunlit_terrain_pct": 60.0, "earth_geom_pct": 50.0,
           "earth_terrain_pct": 40.0, "longest_dark_h": 20.0, "longest_comms_gap_h": 30.0,
           "max_sun_el_deg": 1.5}


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    cache.clear()
    monkeypatch.setattr(config, "RETRY_BACKOFF_S", 0.0)
    # Block any real M2/M3 modules unless a test installs fakes.
    for name in ("terrain.terrain", "terrain.horizon", "terrain.slope", "terrain.hazard",
                 "science.ephemeris", "science.illumination", "science.power"):
        monkeypatch.setitem(sys.modules, name, None)


class Fakes:
    def __init__(self, monkeypatch):
        self.mp = monkeypatch
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
        self.mod("terrain.terrain",
                 get_sites=lambda: [SITE_A],
                 get_site=lambda sid: SITE_A if sid == "site_a" else None)
        self.mod("terrain.horizon",
                 get_horizon=lambda lat, lon, sid: {"deg": [1.0] * 360, "dem": DEM, "approx": False}
                 if sid == "site_a" else {"deg": None, "dem": None, "approx": True})
        self.mod("terrain.slope", get_slope=lambda lat, lon, r: {"slope_mean_deg": 5.0, "slope_max_deg": 12.0, "roughness_m": 0.4})
        self.mod("terrain.hazard", get_hazard=lambda lat, lon: {"flags": ["slope>10deg"]})
        self.mod("science.ephemeris", sun_earth_at=lambda lat, lon, t: {
            "sun_el": 1.2, "sun_az": 30.0, "earth_el": 4.0, "earth_az": 80.0,
            "sun_lit_geom": True, "earth_vis_geom": True, "hours_to_sunset": 50.0, "hours_to_earthset": None})
        self.mod("science.illumination",
                 compute_timeseries=lambda *a: self.compute_impl(*a),
                 window_metrics=lambda sid, dates: [{"start_utc": d, "metrics": dict(METRICS)} for d in dates])
        self.mod("science.power", estimate_power=lambda ts, panel: {"power_w": [1.0, 0.0], "peak_w": 1.0, "energy_wh": 0.5})
        return self


@pytest.fixture
def fakes(monkeypatch):
    return Fakes(monkeypatch).install()


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


# ---- modules not merged yet -> 501, not a crash -----------------------------
def test_missing_modules_give_501():
    r = client.get("/api/sites")
    assert r.status_code == 501 and r.json()["error"]["code"] == "FEATURE_NOT_AVAILABLE"


# ---- 4: site not found ------------------------------------------------------
def test_site_not_found_404(fakes):
    assert client.get("/api/sites/zzz").status_code == 404
    assert client.post("/api/timeline", json={"site_id": "zzz", "start_utc": START}).status_code == 404


def test_sites_list_and_detail(fakes):
    body = client.get("/api/sites").json()
    assert body["data"]["sites"][0]["class"] == "PUBLISHED"
    assert body["provenance"]["inputs"][0]["url"] == "https://example.org/a"
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
    assert e["data"]["sun"] == {"el": 1.2, "az": 30.0} and e["data"]["hours_to_earthset"] is None
    p = client.post("/api/power/estimate", json={**SCEN_A, "panel": {"area_m2": 1, "efficiency": 0.2}}).json()
    assert p["provenance"]["class"] == "ESTIMATED" and p["data"]["peak_w"] == 1.0
    h = client.post("/api/terrain/horizon", json={"site_id": "site_a"}).json()
    assert h["data"]["horizon"]["dem"]["name"] == "TEST DEM"
    h2 = client.post("/api/terrain/horizon", json={"lat": -89.5, "lon": 0}).json()
    assert h2["provenance"]["class"] == "UNAVAILABLE" and h2["provenance"]["reason"]
    s = client.post("/api/terrain/slope", json={"site_id": "site_a"}).json()
    assert s["data"]["hazard_flags"] == ["slope>10deg"]


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
