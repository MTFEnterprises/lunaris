#!/usr/bin/env python
"""LUNARIS M3 - OFFLINE: cut small DEM tiles for backend/terrain/slope.py

Run on your laptop in the M3 venv (needs rasterio, pyproj, numpy). NEVER on the
server. The big DEM GeoTIFF is not committed; only the small tiles are.

    python scripts/terrain/make_dem_tiles.py --dem path/to/dem.tif \
        --site shackleton_rim:LAT:LON --site malapert_massif:LAT:LON \
        --half-size-km 50

or  --sites-json data/sites.json   (entries with null lat/lon are skipped)

What it does, per site
  1. Reads the DEM's numeric polar-projection parameters, but interprets site
     coordinates in the M2-confirmed MOON_ME frame rather than the embedded
     IAU:30135 datum label.
  2. Writes data/dem_tiles/<site_id>.npz = heights (NaN = no data) + grid +
     projection parameters + a copy of the DEM identity from data/dem_meta.json.
  3. VERIFIES before trusting the tile (aborts on any mismatch):
       - the explicit MOON_ME projection round-trips latitude/longitude;
       - tile heights equal terrain.elevation_at() at random pixel centres.

The M2-approved frame interpretation is explicit: use MOON_ME latitude/longitude
with numeric projection parameters read from the local WKT, not its datum label.
The resulting projection is round-trip checked, and sampled tile values are
compared with direct source-DEM reads.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio
from pyproj import CRS
from rasterio.windows import Window

REPO = Path(__file__).resolve().parents[2]
TERRAIN_DIR = REPO / "backend" / "terrain"
sys.path.insert(0, str(REPO))

from backend.terrain.projection import south_polar_parameters


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"lunaris_{name}", TERRAIN_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod   # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


terrain = _load("terrain")   # DEM reading / coordinate logic (rasterio + pyproj)
slope = _load("slope")       # the runtime module whose maths we verify here

VALUE_TOL_M = 1e-3
N_CHECK = 300


# --------------------------------------------------------------------------- #
def derive_projection(dem_crs: CRS) -> dict:
    try:
        return south_polar_parameters(dem_crs)
    except ValueError as exc:
        raise SystemExit(f"Unsupported DEM projection: {exc}") from exc


def verify_projection(proj: dict, rng: np.random.Generator) -> None:
    """Verify the MOON_ME spherical projection's forward/inverse round trip."""
    for _ in range(N_CHECK):
        lat = float(rng.uniform(-89.9, -80.0))
        lon = float(rng.uniform(-180.0, 180.0))
        x, y = slope.project_south_polar(
            lat, lon, proj["R_m"], proj["k0"], proj["lon0_deg"]
        )
        lat2, lon2 = slope.unproject_south_polar(
            x, y, proj["R_m"], proj["k0"], proj["lon0_deg"]
        )
        lon_error = abs((float(lon2) - lon + 180.0) % 360.0 - 180.0)
        if abs(float(lat2) - lat) > 1e-9 or lon_error > 1e-9:
            raise SystemExit(
                f"MOON_ME projection round-trip failed at lat={lat}, lon={lon}."
            )


def verify_values(
    dem_path: Path,
    tile_path: Path,
    proj: dict,
    rng: np.random.Generator
) -> None:
    """Tile heights must equal terrain.elevation_at() (the DEM read directly)."""
    slope.clear_cache()
    tiles, errors = slope.load_tiles(tile_path.parent)
    tile = next((t for t in tiles if t.path == tile_path), None)
    if tile is None:
        raise SystemExit(f"Tile could not be re-read: {errors}")
    for _ in range(N_CHECK):
        r, c = int(rng.integers(0, tile.height)), int(rng.integers(0, tile.width))
        lat, lon = slope.unproject_south_polar(
            tile.x_left + (c + 0.5) * tile.res_m,
            tile.y_top - (r + 0.5) * tile.res_m,
            proj["R_m"],
            proj["k0"],
            proj["lon0_deg"],
        )
        lat, lon = float(lat), float(lon)
        ref = terrain.elevation_at(lat, lon, dem_path)
        mine = tile.elevation_at(lat, lon)
        if ref["class"] == "UNAVAILABLE":
            ok = mine is None
        else:
            ok = mine is not None and abs(mine - ref["value_m"]) <= VALUE_TOL_M
        if not ok:
            raise SystemExit(f"Tile value differs from terrain.elevation_at at "
                             f"lat={lat}, lon={lon}: tile={mine}, terrain={ref}.")


# --------------------------------------------------------------------------- #
def make_tile(dem_path: Path, site_id: str, lat: float, lon: float, half_km: float,
              out_dir: Path, dem_meta: dict) -> Path:
    rng = np.random.default_rng(0)
    with rasterio.open(dem_path) as src:
        if src.crs is None:
            raise SystemExit("DEM has no CRS.")
        dem_crs = CRS.from_user_input(src.crs.to_wkt())
        tr = src.transform
        if tr.b != 0 or tr.d != 0:
            raise SystemExit("Rotated rasters are not supported by the tile format.")
        res = terrain._resolution_m(src, dem_crs)
        if res is None:
            raise SystemExit("Cannot determine the pixel size in metres.")
        factor = dem_crs.axis_info[0].unit_conversion_factor or 1.0
        if abs(abs(tr.a) * factor - abs(tr.e) * factor) > 1e-6:
            raise SystemExit("Pixels are not square.")

        proj = derive_projection(dem_crs)
        x, y = slope.project_south_polar(
            lat, lon, proj["R_m"], proj["k0"], proj["lon0_deg"]
        )
        x, y = float(x), float(y)
        col_f, row_f = (~tr) * (x, y)
        half_px = int(math.ceil(half_km * 1000.0 / res))
        c0 = max(0, int(math.floor(col_f)) - half_px)
        r0 = max(0, int(math.floor(row_f)) - half_px)
        c1 = min(src.width, int(math.floor(col_f)) + half_px + 1)
        r1 = min(src.height, int(math.floor(row_f)) + half_px + 1)
        if c1 <= c0 or r1 <= r0:
            raise SystemExit(f"{site_id}: site is outside the DEM.")

        data = src.read(1, window=Window(c0, r0, c1 - c0, r1 - r0), masked=True)
        z = data.astype(np.float32).filled(np.nan)
        scale = src.scales[0] if src.scales else 1.0
        offset = src.offsets[0] if src.offsets else 0.0
        if scale != 1.0 or offset != 0.0:
            z = z * np.float32(scale) + np.float32(offset)
        z[~np.isfinite(z)] = np.nan

        x_left, y_top = tr * (c0, r0)
        verify_projection(proj, rng)

        meta = {
            "format_version": 1,
            "site_id": site_id,
            "site_lat": lat, "site_lon": lon,
            "grid": {"res_m": res, "x_left_m": x_left, "y_top_m": y_top,
                     "height": int(z.shape[0]), "width": int(z.shape[1])},
            "projection": proj,
            "vertical_units": dem_meta.get("vertical_units"),
            "dem": {k: dem_meta.get(k) for k in
                    ("name", "status", "coverage", "retrieved_utc",
                     "product_version", "frame", "crs", "source_url")},
        }
        if not meta["dem"]["name"]:
            meta["dem"]["name"] = dem_path.name

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{site_id}.npz"
    np.savez_compressed(out, z=z, meta=np.array(json.dumps(meta)))
    verify_values(dem_path, out, proj, rng)
    print(f"{site_id}: {z.shape[1]}x{z.shape[0]} px @ {res:g} m, "
          f"{out.stat().st_size / 1e6:.2f} MB, NaN pixels: {int(np.isnan(z).sum())} -> {out}")
    return out


def _sites_from_json(path: Path) -> list[tuple[str, float, float]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("sites", raw) if isinstance(raw, dict) else raw
    sites = []
    for it in items:
        sid, la, lo = it.get("id"), it.get("lat"), it.get("lon")
        if sid and la is not None and lo is not None:
            sites.append((str(sid), float(la), float(lo)))
        else:
            print(f"skipped {it.get('id')!r}: lat/lon not available (UNAVAILABLE)")
    return sites


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dem", required=True, type=Path)
    ap.add_argument("--site", action="append", default=[], metavar="ID:LAT:LON")
    ap.add_argument("--sites-json", type=Path)
    ap.add_argument("--half-size-km", type=float, default=50.0)
    ap.add_argument("--out", type=Path, default=REPO / "data" / "dem_tiles")
    ap.add_argument("--dem-meta", type=Path, default=REPO / "data" / "dem_meta.json")
    a = ap.parse_args()

    dem_meta = {}
    if a.dem_meta.is_file():
        dem_meta = json.loads(a.dem_meta.read_text(encoding="utf-8"))
    else:
        print(f"warning: {a.dem_meta} not found; tiles will carry no DEM identity")

    sites = []
    for s in a.site:
        sid, la, lo = s.split(":")
        sites.append((sid, float(la), float(lo)))
    if a.sites_json:
        sites += _sites_from_json(a.sites_json)
    if not sites:
        sys.exit("No sites given (use --site or --sites-json).")
    for sid, la, lo in sites:
        make_tile(a.dem, sid, la, lo, a.half_size_km, a.out, dem_meta)


if __name__ == "__main__":
    main()