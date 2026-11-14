
#!/usr/bin/env python
"""Generate M3 polar-stereographic elevation, slope and hillshade PNG layers."""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib

# Project root
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.terrain.slope import horn_slope_deg

DATA_DIR = ROOT / "data"
TILE_DIR = DATA_DIR / "dem_tiles"
OUTPUT_DIR = DATA_DIR / "layers"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def make_rgba(array, cmap_name):
    """Convert a numeric array into a transparent RGBA PNG."""
    valid = np.isfinite(array)

    if not valid.any():
        raise ValueError("Array contains no valid pixels")

    values = array[valid]
    vmin, vmax = np.percentile(values, [2, 98])

    if vmax <= vmin:
        vmin = float(values.min())
        vmax = float(values.max())
        if vmax <= vmin:
            vmax = vmin + 1.0

    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.colormaps[cmap_name]

    rgba = cmap(norm(np.nan_to_num(array, nan=vmin)), bytes=True)
    rgba[~valid, 3] = 0

    return Image.fromarray(rgba, mode="RGBA"), float(vmin), float(vmax)


def make_hillshade(
    elevation,
    resolution_m,
    azimuth_deg=315,
    altitude_deg=45
):
    """
    Generate a grayscale terrain hillshade.

    This is a visualization derivative, not actual lunar illumination.
    """
    valid = np.isfinite(elevation)

    if not valid.any():
        raise ValueError("Elevation array contains no valid pixels")

    # Calculate terrain gradients.
    dz_dy, dz_dx = np.gradient(elevation, resolution_m)

    # Convert angles to radians.
    azimuth = np.radians(azimuth_deg)
    altitude = np.radians(altitude_deg)

    # Calculate terrain surface normal.
    normal_length = np.sqrt(dz_dx**2 + dz_dy**2 + 1.0)

    # Calculate relative illumination.
    shade = (
        np.sin(altitude)
        - dz_dx * np.cos(altitude) * np.sin(azimuth)
        - dz_dy * np.cos(altitude) * np.cos(azimuth)
    ) / normal_length

    # Keep values between 0 and 1.
    shade = np.clip(shade, 0.0, 1.0)

    # Preserve missing terrain pixels.
    shade[~valid] = np.nan

    return make_rgba(shade, "gray")


def project_south_polar(lat, lon, R, k0, lon0):
    """Same spherical south-polar stereographic projection as F14."""
    phi = np.radians(np.asarray(lat, dtype=np.float64))
    lam = np.radians(np.asarray(lon, dtype=np.float64) - lon0)

    rho = 2.0 * R * k0 * np.tan(np.pi / 4.0 + phi / 2.0)

    x = rho * np.sin(lam)
    y = rho * np.cos(lam)

    return x, y


def generate():
    tile_files = sorted(TILE_DIR.glob("*.npz"))

    if not tile_files:
        raise FileNotFoundError(f"No DEM tiles found in {TILE_DIR}")

    result = {
        "schema_version": "1.0",
        "description": "M3 south-polar stereographic DEM map layers",
        "crs": {
            "name": "Moon (2015) - Sphere / Ocentric / South Polar",
            "authority": "IAU:30135",
            "projection": "polar_stereographic_south",
            "linear_units": "metres",
            "frame": "MOON_2015_SPHERE_OCENTRIC"
        },
        "coordinate_conversion": {
            "input": "latitude and east-positive longitude in degrees",
            "output": "zero-based image pixel coordinates",
            "formula": [
                "phi = radians(latitude)",
                "lambda = radians(longitude - lon0_deg)",
                "rho = 2 * R_m * k0 * tan(pi/4 + phi/2)",
                "x = rho * sin(lambda)",
                "y = rho * cos(lambda)",
                "pixel_x = (x - x_left_m) / resolution_m",
                "pixel_y = (y_top_m - y) / resolution_m"
            ],
            "inverse_formula": [
                "x = x_left_m + pixel_x * resolution_m",
                "y = y_top_m - pixel_y * resolution_m",
                "rho = hypot(x, y)",
                "phi = 2 * atan(rho / (2 * R_m * k0)) - pi/2",
                "lambda = radians(lon0_deg) + atan2(x, y)",
                "latitude = degrees(phi)",
                "longitude = normalize_degrees(degrees(lambda))"
            ],
            "pixel_origin": "top-left",
            "pixel_coordinates": "continuous; pixel centres are at col+0.5, row+0.5"
        },
        "tiles": {}
    }

    for path in tile_files:
        print(f"Processing {path.name} ...")

        with np.load(path) as data:
            z = np.asarray(data["z"], dtype=np.float32)
            meta = json.loads(str(data["meta"]))

        grid = meta["grid"]
        proj = meta["projection"]

        height, width = z.shape
        resolution = float(grid["res_m"])
        x_left = float(grid["x_left_m"])
        y_top = float(grid["y_top_m"])

        if z.shape != (int(grid["height"]), int(grid["width"])):
            raise ValueError(f"Grid shape mismatch in {path.name}")

        if not np.isfinite(z).any():
            raise ValueError(f"No valid elevation pixels in {path.name}")

        # Calculate slope using the existing F14 Horn algorithm.
        padded = np.pad(z, 1, mode="constant", constant_values=np.nan)
        slope = horn_slope_deg(padded, resolution)

        # Generate elevation image.
        elevation_img, elev_min, elev_max = make_rgba(z, "terrain")

        # Generate slope image.
        slope_img, slope_min, slope_max = make_rgba(slope, "inferno")

        # Generate derived hillshade image.
        hillshade_img, hillshade_min, hillshade_max = make_hillshade(
            z,
            resolution,
            azimuth_deg=315,
            altitude_deg=45
        )

        site_id = path.stem

        elevation_file = f"elevation_{site_id}.png"
        slope_file = f"slope_{site_id}.png"
        hillshade_file = f"hillshade_{site_id}.png"

        # Save all three images.
        elevation_img.save(OUTPUT_DIR / elevation_file)
        slope_img.save(OUTPUT_DIR / slope_file)
        hillshade_img.save(OUTPUT_DIR / hillshade_file)

        # Projected outer edges of the tile.
        x_right = x_left + width * resolution
        y_bottom = y_top - height * resolution

        result["tiles"][site_id] = {
            "width_px": width,
            "height_px": height,
            "resolution_m": resolution,
            "projected_bounds_m": {
                "left": x_left,
                "bottom": y_bottom,
                "right": x_right,
                "top": y_top
            },
            "layers": {
                "elevation": {
                    "file": f"layers/{elevation_file}",
                    "units": "m",
                    "colormap": "terrain",
                    "display_min": elev_min,
                    "display_max": elev_max
                },
                "slope": {
                    "file": f"layers/{slope_file}",
                    "units": "degrees",
                    "colormap": "inferno",
                    "display_min": slope_min,
                    "display_max": slope_max
                },
                "hillshade": {
                    "file": f"layers/{hillshade_file}",
                    "units": "relative_shading_0_to_1",
                    "method": "derived terrain hillshade",
                    "sun_azimuth_deg": 315,
                    "sun_altitude_deg": 45,
                    "display_min": hillshade_min,
                    "display_max": hillshade_max
                }
            },
            "projection_parameters": {
                "R_m": float(proj["R_m"]),
                "k0": float(proj["k0"]),
                "lon0_deg": float(proj["lon0_deg"])
            },
            "grid_origin": {
                "x_left_m": x_left,
                "y_top_m": y_top
            },
            "valid_elevation_pixels": int(np.isfinite(z).sum()),
            "valid_slope_pixels": int(np.isfinite(slope).sum())
        }

        print(f"  Elevation: {elevation_file}")
        print(f"  Slope:     {slope_file}")
        print(f"  Hillshade: {hillshade_file}")
        print(f"  Dimensions: {width} x {height}")

    output_json = DATA_DIR / "layers.json"

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("\nMap layer generation completed.")
    print(f"Sites processed: {len(result['tiles'])}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Metadata file: {output_json}")


if __name__ == "__main__":
    generate()
