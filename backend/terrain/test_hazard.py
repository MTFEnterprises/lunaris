
"""Tests for LUNARIS M3 - F15 landing hazard assessment."""

from types import SimpleNamespace

import pytest

from backend.terrain.hazard import (
    classify_cell,
    PASS,
    FAIL,
    UNKNOWN,
)


def make_result(**overrides):
    """Create a fake, complete terrain result for testing."""

    data = {
        "status": "OK",
        "approx": False,
        "radius_m": 10.0,
        "window": {
            "valid_fraction": 1.0,
            "clipped_by_tile": False,
        },
        "warnings": [],
        "slope_max_deg": 5.0,
        "roughness_rms_m": 0.2,
    }

    data.update(overrides)

    return SimpleNamespace(**data)


def test_cell_passes_when_all_measurements_are_within_limits():
    result = make_result()

    classification, reasons = classify_cell(
        result,
        max_slope_deg=10.0,
        max_roughness_m=0.5,
        min_radius_m=10.0,
    )

    assert classification == PASS
    assert reasons == []


def test_cell_fails_when_slope_exceeds_limit():
    result = make_result(slope_max_deg=15.0)

    classification, reasons = classify_cell(
        result,
        max_slope_deg=10.0,
        max_roughness_m=0.5,
        min_radius_m=10.0,
    )

    assert classification == FAIL
    assert any(
        reason["code"] == "SLOPE_EXCEEDS_LIMIT"
        for reason in reasons
    )


def test_cell_fails_when_roughness_exceeds_limit():
    result = make_result(roughness_rms_m=0.8)

    classification, reasons = classify_cell(
        result,
        max_slope_deg=10.0,
        max_roughness_m=0.5,
        min_radius_m=10.0,
    )

    assert classification == FAIL
    assert any(
        reason["code"] == "ROUGHNESS_EXCEEDS_LIMIT"
        for reason in reasons
    )


def test_partial_terrain_returns_unknown():
    result = make_result(status="PARTIAL")

    classification, reasons = classify_cell(
        result, 10.0, 0.5, 10.0
    )

    assert classification == UNKNOWN
    assert len(reasons) > 0


def test_approximate_terrain_returns_unknown():
    result = make_result(approx=True)

    classification, reasons = classify_cell(
        result, 10.0, 0.5, 10.0
    )

    assert classification == UNKNOWN
    assert len(reasons) > 0


def test_incomplete_dem_coverage_returns_unknown():
    result = make_result(
        window={
            "valid_fraction": 0.8,
            "clipped_by_tile": False,
        }
    )

    classification, reasons = classify_cell(
        result, 10.0, 0.5, 10.0
    )

    assert classification == UNKNOWN
    assert any(
        reason["code"] == "RADIUS_NOT_FULLY_EVALUATED"
        for reason in reasons
    )


def test_wrong_radius_returns_unknown():
    result = make_result(radius_m=5.0)

    classification, reasons = classify_cell(
        result, 10.0, 0.5, 10.0
    )

    assert classification == UNKNOWN
    assert any(
        reason["code"] == "RADIUS_MISMATCH"
        for reason in reasons
    )


def test_missing_slope_returns_unknown():
    result = make_result(slope_max_deg=None)

    classification, reasons = classify_cell(
        result, 10.0, 0.5, 10.0
    )

    assert classification == UNKNOWN
    assert any(
        reason["code"] == "SLOPE_MISSING"
        for reason in reasons
    )

from backend.terrain import hazard


def test_site_assessment_passes_with_verified_terrain(monkeypatch):
    result = make_result()

    monkeypatch.setattr(
        hazard,
        "get_slope",
        lambda *args, **kwargs: result,
    )

    assessment = hazard.evaluate_site(
        -85.0,
        20.0,
        max_slope_deg=10.0,
        max_roughness_m=0.5,
        min_radius_m=10.0,
        cell_size_m=20.0,
        half_extent_m=0.0,
    )

    assert assessment["summary"]["total"] == 1
    assert assessment["summary"]["pass"] == 1
    assert assessment["summary"]["site_class"] == PASS
    assert assessment["dem_verified"] is True
    assert assessment["statement"] == hazard.SAFETY_STATEMENT


def test_site_assessment_fails_when_slope_exceeds_limit(monkeypatch):
    result = make_result(slope_max_deg=20.0)

    monkeypatch.setattr(
        hazard,
        "get_slope",
        lambda *args, **kwargs: result,
    )

    assessment = hazard.evaluate_site(
        -85.0,
        20.0,
        max_slope_deg=10.0,
        max_roughness_m=0.5,
        min_radius_m=10.0,
        cell_size_m=20.0,
        half_extent_m=0.0,
    )

    assert assessment["summary"]["fail"] == 1
    assert assessment["summary"]["site_class"] == FAIL


def test_site_assessment_unknown_with_unverified_dem(monkeypatch):
    result = make_result(
        warnings=["DEM_UNVERIFIED: test metadata"],
    )

    monkeypatch.setattr(
        hazard,
        "get_slope",
        lambda *args, **kwargs: result,
    )

    assessment = hazard.evaluate_site(
        -85.0,
        20.0,
        max_slope_deg=10.0,
        max_roughness_m=0.5,
        min_radius_m=10.0,
        cell_size_m=20.0,
        half_extent_m=0.0,
    )

    assert assessment["summary"]["unknown"] == 1
    assert assessment["summary"]["site_class"] == UNKNOWN
    assert assessment["dem_verified"] is False
