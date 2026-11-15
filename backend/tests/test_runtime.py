"""Unit tests for LUNARIS M2 runtime science adapter (backend/science/runtime.py)."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import numpy as np
import pytest

from backend.science.runtime import (
    compute_timeseries,
    estimate_power,
    window_metrics,
)


def test_runtime_has_no_heavy_imports() -> None:
    """Verify runtime.py never imports spiceypy or rasterio (Vercel compatibility)."""
    runtime_path = Path(__file__).resolve().parents[1] / "science" / "runtime.py"
    tree = ast.parse(runtime_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])

    assert "spiceypy" not in imported
    assert "rasterio" not in imported


def test_compute_timeseries_no_horizon() -> None:
    """Without horizon_deg, terrain arrays and terrain metrics must strictly be None."""
    res = compute_timeseries(
        lat=-89.54,
        lon=0.0,
        start_utc="2027-03-14T00:00:00Z",
        hours=24,
        step_min=30,
        horizon_deg=None,
    )

    assert set(res.keys()) == {"timeseries", "metrics", "warnings"}
    ts = res["timeseries"]
    metrics = res["metrics"]

    assert ts["start_utc"] == "2027-03-14T00:00:00Z"
    assert ts["step_min"] == 30
    assert len(ts["sun_el"]) == 49
    assert len(ts["sun_az"]) == 49
    assert len(ts["earth_el"]) == 49
    assert len(ts["earth_az"]) == 49
    assert len(ts["sun_lit_geom"]) == 49
    assert len(ts["earth_vis_geom"]) == 49

    # Strict None when horizon is unavailable
    assert ts["sun_lit_terrain"] is None
    assert ts["earth_vis_terrain"] is None
    assert metrics["sunlit_terrain_pct"] is None
    assert metrics["earth_terrain_pct"] is None

    assert isinstance(metrics["sunlit_geom_pct"], float)
    assert isinstance(metrics["earth_geom_pct"], float)
    assert isinstance(metrics["longest_dark_h"], float)
    assert isinstance(metrics["longest_comms_gap_h"], float)
    assert isinstance(metrics["max_sun_el_deg"], float)


def test_compute_timeseries_with_terrain_horizon() -> None:
    """High terrain horizon (45 deg) should block low polar Sun and Earth visibility."""
    high_wall = [45.0] * 360
    res = compute_timeseries(
        lat=-89.54,
        lon=0.0,
        start_utc="2027-03-14T00:00:00Z",
        hours=24,
        step_min=30,
        horizon_deg=high_wall,
    )

    ts = res["timeseries"]
    metrics = res["metrics"]

    assert ts["sun_lit_terrain"] is not None
    assert ts["earth_vis_terrain"] is not None
    assert all(v is False for v in ts["sun_lit_terrain"])
    assert all(v is False for v in ts["earth_vis_terrain"])
    assert metrics["sunlit_terrain_pct"] == 0.0
    assert metrics["earth_terrain_pct"] == 0.0
    assert metrics["longest_dark_h"] == 24.5


def test_window_metrics_shackleton() -> None:
    """Precomputed window_metrics returns 29.5-day metrics for requested start dates."""
    dates = ["2027-01-01T00:00:00Z", "2027-06-15T00:00:00Z"]
    rows = window_metrics("shackleton_rim", dates)

    assert len(rows) == 2
    assert rows[0]["start_utc"] == "2027-01-01T00:00:00Z"
    assert rows[0]["metrics"] is not None
    assert "sunlit_geom_pct" in rows[0]["metrics"]
    assert "max_sun_el_deg" in rows[0]["metrics"]


def test_window_metrics_preserves_preliminary_status_and_warnings(tmp_path, monkeypatch) -> None:
    import backend.science.runtime as runtime

    start = "2027-01-01T00:00:00Z"
    payload = {
        "status": "PRELIMINARY",
        "warnings": ["DEM frame confirmation is pending."],
        "windows": {start: {"sunlit_geom_pct": 50.0}},
    }
    (tmp_path / "window_metrics_test_site.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    monkeypatch.setattr(runtime, "DATA_DIR", tmp_path)

    rows = runtime.window_metrics("test_site", [start])

    assert rows[0]["status"] == "PRELIMINARY"
    assert rows[0]["warnings"] == payload["warnings"]


def test_estimate_power_respects_terrain_shadow() -> None:
    """Terrain-blocked intervals must yield 0.0 W in estimate_power."""
    ts_res = compute_timeseries(
        lat=-89.54,
        lon=0.0,
        start_utc="2027-03-14T00:00:00Z",
        hours=12,
        step_min=30,
        horizon_deg=[45.0] * 360,
    )
    panel = {
        "area_m2": 2.0,
        "efficiency": 0.28,
        "losses": 0.1,
        "tilt_deg": 10.0,
        "azimuth_deg": 0.0,
    }
    pwr = estimate_power(ts_res["timeseries"], panel)

    assert set(pwr.keys()) == {"power_w", "peak_w", "energy_wh"}
    assert len(pwr["power_w"]) == 25
    assert pwr["peak_w"] == 0.0
    assert pwr["energy_wh"] == 0.0