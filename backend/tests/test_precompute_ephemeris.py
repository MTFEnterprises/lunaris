from __future__ import annotations

import json

import pytest

import scripts.ephemeris.precompute_ephemeris as precompute


@pytest.mark.parametrize(
    ("anchor_status", "frame_status", "expected_status", "warning_fragment"),
    [
        ("CONFIRMED_PROJECT_ANCHOR", "VERIFIED", "VERIFIED", None),
        (
            "CONFIRMED_PROJECT_ANCHOR",
            "PENDING_M2_CONFIRMATION",
            "PRELIMINARY",
            "DEM horizon frame",
        ),
        ("PENDING", "VERIFIED", "PRELIMINARY", "site coordinates"),
    ],
)
def test_window_metrics_status_requires_confirmed_anchor_and_frame(
    tmp_path,
    monkeypatch,
    anchor_status,
    frame_status,
    expected_status,
    warning_fragment,
):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    sites_path = tmp_path / "sites.json"
    sites_path.write_text(
        json.dumps(
            {
                "sites": [
                    {
                        "id": "test_site",
                        "lat": -89.0,
                        "lon": 12.0,
                        "coords_class": "PUBLISHED",
                        "anchor_status": anchor_status,
                        "coords_source_url": "https://example.invalid/site",
                        "notes": "Test feature center.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "horizon_test_site.json").write_text(
        json.dumps(
            {
                "coordinate_frame_status": frame_status,
                "dem": {"frame": "MOON_2015_SPHERE_OCENTRIC"},
                "horizon": {"deg": [0.0] * 360},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(precompute, "DATA_DIR", data_dir)
    monkeypatch.setattr(
        "backend.science.runtime.compute_timeseries",
        lambda **kwargs: {"metrics": {"sunlit_geom_pct": 50.0}},
    )

    written = precompute.generate_all_site_window_metrics(
        sites_path=sites_path,
        step_days=365,
    )

    payload = json.loads(written[0].read_text(encoding="utf-8"))
    assert payload["status"] == expected_status
    assert payload["site_coordinates"]["anchor_status"] == anchor_status
    if warning_fragment is None:
        assert payload["warnings"] == []
    else:
        assert any(warning_fragment in warning for warning in payload["warnings"])
