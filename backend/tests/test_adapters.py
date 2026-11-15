"""M1 adapter tests: /api/ephemeris and /api/terrain/slope against the real M2/M3 modules."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)
SITE = "shackleton_rim"
LAT = -89.9
LON = 0.0


def test_ephemeris_returns_sun_and_earth_angles():
    r = client.post("/api/ephemeris", json={"lat": LAT, "lon": LON, "time_utc": "2027-03-14T06:00:00Z"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert -90 <= d["sun"]["el"] <= 90 and 0 <= d["sun"]["az"] < 360
    assert -90 <= d["earth"]["el"] <= 90
    assert isinstance(d["sun_lit_geom"], bool)
    assert d["frame"]
    assert r.json()["provenance"]["class"] == "CALCULATED"


def test_ephemeris_countdown_is_none_or_non_negative():
    r = client.post("/api/ephemeris", json={"lat": LAT, "lon": LON, "time_utc": "2027-06-01T00:00:00Z"})
    assert r.status_code == 200, r.text
    for k in ("hours_to_sunset", "hours_to_earthset"):
        v = r.json()["data"][k]
        assert v is None or v >= 0


def test_ephemeris_near_end_of_coverage_does_not_crash():
    r = client.post("/api/ephemeris", json={"lat": LAT, "lon": LON, "time_utc": "2028-01-31T20:00:00Z"})
    assert r.status_code == 200, r.text


def test_ephemeris_custom_coordinate_works():
    r = client.post("/api/ephemeris", json={"lat": -89.5, "lon": 10.0, "time_utc": "2027-03-14T06:00:00Z"})
    assert r.status_code == 200, r.text


def test_ephemeris_bad_latitude_is_400():
    r = client.post("/api/ephemeris", json={"lat": 95, "lon": 0, "time_utc": "2027-03-14T06:00:00Z"})
    assert r.status_code == 400


def test_slope_curated_site_is_calculated_with_incomplete_provenance_warning():
    r = client.post("/api/terrain/slope", json={"site_id": SITE, "radius_m": 500})
    assert r.status_code == 200, r.text
    body = r.json()
    d = body["data"]
    assert d["slope_mean_deg"] is not None
    assert d["roughness_m"] is not None
    assert body["provenance"]["class"] == "CALCULATED"
    assert any("DEM_META_INCOMPLETE" in warning for warning in body["warnings"])

def test_curated_site_ephemeris_uses_published_coordinates():
    ephemeris = client.post("/api/ephemeris", json={"site_id": SITE, "time_utc": "2027-03-14T06:00:00Z"})
    assert ephemeris.status_code == 200, ephemeris.text
    data = ephemeris.json()["data"]
    assert data["site"]["lat"] == -89.67
    assert data["site"]["lon"] == 129.78
    assert data["frame"] == "MOON_ME"


def test_slope_outside_tiles_is_unavailable_not_invented():
    r = client.post("/api/terrain/slope", json={"lat": -60.0, "lon": 0.0, "radius_m": 500})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data"]["slope_mean_deg"] is None
    assert body["provenance"]["class"] == "UNAVAILABLE"


def test_stored_fallback_scenarios_load_and_are_labelled():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from fallback.loader import find_scenario

    env = find_scenario("shackleton_rim", "2027-03-14T06:00:00Z", 708)
    assert env is not None
    assert env.cached is True
    assert env.provenance.generated_utc
    assert "stored fallback" in env.warnings[0]


@pytest.mark.parametrize("site", ["de_gerlache_rim", "nobile_rim", "shoemaker"])
def test_added_fallback_scenarios_have_provenance(site):
    from fallback.loader import find_scenario

    env = find_scenario(site, "2027-03-14T06:00:00Z", 708)
    assert env is not None
    assert env.provenance.cls.value
    assert env.provenance.generated_utc
