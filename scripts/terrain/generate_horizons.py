#!/usr/bin/env python
"""Regenerate the six published-feature-center horizons from the local DEM."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.terrain.horizon import horizon_at  # noqa: E402

DATA_DIR = ROOT / "data"
DEM_PATH = DATA_DIR / "dem" / "LDEM_80S_80MPP_ADJ.TIF"
SITES_PATH = DATA_DIR / "sites.json"
DEM_META_PATH = DATA_DIR / "dem_meta.json"
FRAME_STATUS = "PENDING_M2_CONFIRMATION"
FRAME_WARNING = (
    "The source raster reports IAU:30135 while project/M2 uses MOON_ME. "
    "This horizon was computed directly in the local raster frame and is "
    "preliminary until M2 confirms coordinate-frame compatibility."
)


def main() -> None:
    if not DEM_PATH.is_file():
        raise FileNotFoundError(f"Local LOLA DEM is required: {DEM_PATH}")

    sites_doc = json.loads(SITES_PATH.read_text(encoding="utf-8"))
    dem_meta = json.loads(DEM_META_PATH.read_text(encoding="utf-8"))
    generated_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for site in sites_doc["sites"]:
        if site["lat"] is None or site["lon"] is None:
            raise ValueError(f"{site['id']} has no published center coordinates")

        result = horizon_at(
            site["lat"],
            site["lon"],
            height_m=site["height_m"],
            dem_path=DEM_PATH,
            dem_meta_path=DEM_META_PATH,
        )
        if result["deg"] is None:
            raise RuntimeError(f"{site['id']} horizon unavailable: {result['status']}")
        if len(result["deg"]) != 360:
            raise RuntimeError(f"{site['id']} produced {len(result['deg'])} bins, expected 360")

        result.update(
            site={
                "id": site["id"],
                "name": site["name"],
                "lat": site["lat"],
                "lon": site["lon"],
                "height_m": site["height_m"],
                "coords_class": site["coords_class"],
                "coords_source_url": site["coords_source_url"],
                "definition": site["notes"],
            },
            coordinate_frame_status=FRAME_STATUS,
            generated_utc=generated_utc,
            algorithm="backend.terrain.horizon.horizon_at",
            warnings=[FRAME_WARNING],
        )
        result["status"] = f"{result['status']}; {FRAME_STATUS}"
        result["dem"].update(
            frame=dem_meta["frame"],
            crs_authority=dem_meta["crs"]["authority"],
            metadata_status=dem_meta["status"],
        )

        output = DATA_DIR / f"horizon_{site['id']}.json"
        output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        null_bins = sum(value is None for value in result["deg"])
        print(f"{site['id']}: 360 bins, {null_bins} unavailable, {result['status']} -> {output}")


if __name__ == "__main__":
    main()
