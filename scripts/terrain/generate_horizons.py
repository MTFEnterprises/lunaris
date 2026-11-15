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
FRAME_STATUS = "M2_CONFIRMED_MOON_ME"
PROVENANCE_WARNING = (
    "DEM_META_INCOMPLETE: retrieval date and product version remain unknown."
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
            coordinate_frame_note=(
                "M2 confirmed MOON_ME interpretation. The numeric south-polar "
                "projection parameters are read from the local WKT; its "
                "IAU:30135 datum label is not used for coordinate conversion."
            ),
            generated_utc=generated_utc,
            algorithm="backend.terrain.horizon.horizon_at",
            warnings=[PROVENANCE_WARNING],
        )
        result["status"] = (
            f"{result['status']}; {FRAME_STATUS}; DEM_META_INCOMPLETE"
        )
        result["dem"].update(
            frame=dem_meta["frame"],
            crs_authority=dem_meta["crs"]["authority"],
            crs_authority_note=(
                "Observed embedded WKT; datum label rejected per M2 confirmation."
            ),
            metadata_status=dem_meta["status"],
        )

        output = DATA_DIR / f"horizon_{site['id']}.json"
        output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        null_bins = sum(value is None for value in result["deg"])
        print(f"{site['id']}: 360 bins, {null_bins} unavailable, {result['status']} -> {output}")


if __name__ == "__main__":
    main()
