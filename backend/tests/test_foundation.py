"""Tests for errors.py, provenance.py, schemas.py (master guide Section 14, tests 1-4)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from errors import (
    FeatureNotAvailable,
    ServiceUnavailable,
    SiteNotFound,
    register_exception_handlers,
)
from provenance import DataClass, make_provenance, unavailable
from schemas import (
    CompareRequest,
    Envelope,
    HealthData,
    Horizon,
    IlluminationRequest,
    SiteInfo,
    SitesData,
    Timeseries,
)

# A tiny app that exercises the real error handlers + real schemas.
app = FastAPI()
register_exception_handlers(app)


@app.post("/illum")
def illum(req: IlluminationRequest):
    return {"ok": True}


@app.post("/compare")
def compare(req: CompareRequest):
    return {"ok": True}


@app.get("/boom/{kind}")
def boom(kind: str):
    if kind == "site":
        raise SiteNotFound("zzz")
    if kind == "501":
        raise FeatureNotAvailable("Thermal analysis is not available yet.")
    if kind == "503":
        raise ServiceUnavailable("Horizon data missing.")
    raise RuntimeError("secret internals")


@app.get("/envelope")
def envelope():
    return Envelope[SitesData](
        data=SitesData(
            sites=[SiteInfo(id="a", name="A", lat=None, lon=None, **{"class": "PUBLISHED"})]
        ),
        provenance=make_provenance(DataClass.PUBLISHED),
    )


client = TestClient(app, raise_server_exceptions=False)
GOOD = {"site_id": "x", "start_utc": "2027-03-14T06:00:00Z"}


# 1. invalid latitude -> 400 INVALID_COORDINATE
def test_lat_95_is_invalid_coordinate():
    r = client.post("/illum", json={"lat": 95, "lon": 0, "start_utc": "2027-03-14T06:00:00Z"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_COORDINATE"


# 2. invalid date -> 400
@pytest.mark.parametrize("bad", ["not-a-date", "2027-03-14T06:00:00", "2030-01-01T00:00:00Z"])
def test_bad_date_is_400(bad):
    r = client.post("/illum", json={"site_id": "x", "start_utc": bad})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_DATE"


# 3. empty scenario -> clear error
def test_empty_scenarios_list():
    r = client.post("/compare", json={"mode": "scenarios", "scenarios": []})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "EMPTY_SCENARIO"


def test_missing_scenarios_is_400():
    r = client.post("/compare", json={"mode": "scenarios"})
    assert r.status_code == 400


def test_more_than_three_scenarios_is_400():
    r = client.post("/compare", json={"scenarios": [GOOD] * 4})
    assert r.status_code == 400


def test_three_scenarios_ok():
    assert client.post("/compare", json={"scenarios": [GOOD] * 3}).status_code == 200


# site must be id XOR lat+lon
@pytest.mark.parametrize(
    "body",
    [
        {"start_utc": "2027-03-14T06:00:00Z"},
        {"site_id": "x", "lat": 1, "lon": 1, "start_utc": "2027-03-14T06:00:00Z"},
        {"lat": -89.5, "start_utc": "2027-03-14T06:00:00Z"},
        {"site_id": "x", "latitude": 1, "start_utc": "2027-03-14T06:00:00Z"},
    ],
)
def test_bad_site_reference(body):
    r = client.post("/illum", json=body)
    assert r.status_code == 400
    assert set(r.json()["error"]) == {"code", "message", "details"}


def test_custom_coordinate_and_defaults_ok():
    r = client.post("/illum", json={"lat": -89.5, "lon": 0, "start_utc": "2027-03-14T06:00:00Z"})
    assert r.status_code == 200
    m = IlluminationRequest(lat=-89.5, lon=0, start_utc="2027-03-14T06:00:00+00:00")
    assert (m.hours, m.step_min, m.start_utc) == (708, 30, "2027-03-14T06:00:00Z")


def test_window_past_ephemeris_end_is_400():
    r = client.post("/illum", json={"site_id": "x", "start_utc": "2028-01-20T00:00:00Z"})
    assert r.status_code == 400


def test_date_scan_start_must_be_2027():
    body = {
        "mode": "date_scan",
        "date_scan": {"site_id": "x", "start_dates": ["2028-01-05T00:00:00Z"]},
    }
    assert client.post("/compare", json=body).status_code == 400


# 4. site not found + other status codes + no traceback leak
def test_error_status_codes():
    assert client.get("/boom/site").status_code == 404
    assert client.get("/boom/501").status_code == 501
    assert client.get("/boom/503").status_code == 503
    r = client.get("/boom/crash")
    assert r.status_code == 500
    assert "secret internals" not in r.text
    assert client.get("/nope").json()["error"]["code"] == "NOT_FOUND"


# provenance
def test_unavailable_needs_reason():
    with pytest.raises(ValueError):
        make_provenance(DataClass.UNAVAILABLE)
    assert unavailable("no DEM").reason == "no DEM"


def test_envelope_json_shape_uses_class_key():
    body = client.get("/envelope").json()
    assert set(body) == {"data", "provenance", "warnings", "cached"}
    assert body["provenance"]["class"] == "PUBLISHED"
    assert body["data"]["sites"][0]["class"] == "PUBLISHED"
    assert body["cached"] is False


# data format v2 rules
def test_horizon_must_be_360():
    with pytest.raises(ValueError):
        Horizon(deg=[0.0] * 10)
    assert Horizon(deg=None, approx=True).deg is None


def test_timeseries_equal_lengths():
    with pytest.raises(ValueError):
        Timeseries(start_utc="2027-01-01T00:00:00Z", sun_el=[1.0, 2.0], sun_az=[1.0])


def test_health_data_defaults():
    assert HealthData(version="1.0.0").status == "healthy"
