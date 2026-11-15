# M3 Terrain Method and Limitations

## Scope and status

This note describes M3 calculations and map products. LUNARIS is an
independent student prototype; these outputs are not official NASA products
or flight-certified assessments.

The six coordinates in `data/sites.json` are published IAU Gazetteer
solution-1 feature centers, not independently published Artemis region
centers or selected landing points. Their elevations remain null. Tiles,
horizons, and layers have been regenerated from these feature centers.
Those products are preliminary: the local DEM's `IAU:30135` / Moon-2015
Ocentric frame has not yet been confirmed compatible with the project's
`MOON_ME` convention. Do not treat them as frame-validated until M2 confirms.

## Source raster and projection

The local source file is `LDEM_80S_80MPP_ADJ.TIF`, listed by the NASA
Goddard Planetary Geodesy and Cartography Working Group (PGDA) as an
80 m/pixel LOLA south-polar elevation product covering 80°S to the pole.
The product page describes large-area products as south-polar
stereographic X/Y in metres and MOON_ME (JPL DE421). The local GeoTIFF
metadata instead declares IAU:30135 / Moon-2015 Sphere Ocentric. Its
observed dimensions are 7600 × 7600, bounds are ±304,000 m, band type is
float32, no-data is NaN, and observed elevation range is approximately
-7295.52 to +7026.33 m. The band-unit tag is unset. Retrieval date and
product version are unknown.

`scripts/terrain/make_dem_tiles.py` reads the raster's own CRS parameters,
cuts a tile around each supplied coordinate, and checks its spherical
stereographic projection against pyproj and tile heights against
`terrain.elevation_at`. This verifies the implementation against the
declared local CRS; it does **not** resolve the reference-frame mismatch or
validate the site coordinates.

The map-layer grid records a north-up pixel origin, projected bounds,
resolution, and projection parameters. The forward transform is:

```text
phi = radians(latitude)
lambda = radians(east_positive_longitude - lon0)
rho = 2 * R * k0 * tan(pi/4 + phi/2)
x = rho * sin(lambda)
y = rho * cos(lambda)
pixel_x = (x - x_left) / resolution
pixel_y = (y_top - y) / resolution
```

Coordinates refer to continuous pixel positions; pixel centres are
`(column + 0.5, row + 0.5)`. These transforms describe the local raster
projection only. Geographic alignment to M2's frame is pending.
The inverse projection in `data/layers.json` maps a selected continuous
pixel coordinate back to latitude/longitude using the same spherical
parameters; this is a projection round-trip, not confirmation of the
unresolved body-fixed frame.

## Horizon

`backend/terrain/horizon.py` samples 360 great-circle rays on a sphere with
radius 1,737,400 m. Index `i` is azimuth `i` degrees, with 0° North, 90°
East, clockwise. Samples are taken at one projected DEM pixel-size step,
up to 150 km. Each destination is transformed to the DEM CRS and sampled
from the containing pixel (nearest-pixel sampling; no interpolation).
For observer height `z0`, sample height `z`, and surface distance `d`, the
calculated angle is:

```text
degrees(atan2((z - z0) - d*d/(2*R), d))
```

The maximum valid angle along a complete ray is its horizon bin. If the
observer height is omitted, `z0` is read from the containing DEM pixel; if
an explicit `height_m` is supplied, that value is used and identified as a
user-supplied height. An unavailable observer pixel is not silently
interpolated.

Sampling limitations are material: nearest-pixel sampling can miss narrow
features; an 80 m grid does not resolve smaller terrain; the 150 km cutoff
omits more distant relief; and nodata or out-of-coverage samples can hide a
higher obstruction. A ray with any missing sample now returns a null bin
rather than a potentially underestimated maximum. Any partial horizon is
marked approximate; an incomplete bin disables terrain-corrected use in
the API.

The six horizon files were regenerated on 2026-11-15 using
`scripts/terrain/generate_horizons.py`. Each has 360 bins, stores its
published Gazetteer feature-center coordinates and source URL, and records
the algorithm, generation time, and pending frame status. Elevation values
are sampled from the local DEM, but alignment with `MOON_ME` remains
unverified; generation does not establish scientific frame correctness.

## Slope, roughness, profile, and hazard

- **Point and window slope:** Horn 3 × 3 elevation gradient, reported in
  degrees at the local DEM pixel scale. The projected pixel size is divided
  by the local polar-stereographic scale factor to approximate ground
  spacing. Window slope maximum and mean use the same local scale factor.
- **Roughness:** RMS height residual after fitting and removing a
  least-squares plane to valid pixel centres within the requested radius;
  units are metres. Window radius, valid-data fraction, and clipping are
  reported.
- **Profile:** nearest-pixel elevation samples along a great-circle line,
  at approximately one local DEM pixel per sample; azimuth is clockwise
  from North. Missing samples remain null.
- **Hazard:** only caller-supplied slope, roughness, and radius limits are
  used. Missing, partial, approximate, or unverified DEM data yields
  UNKNOWN. There are no universal safety thresholds; all results are
  preliminary decision support.

Slope and roughness API metrics remain unavailable unless DEM metadata is
present and marked verified with metre vertical units. Current
`dem_meta.json` is pending verification, so the regenerated map slope images
are visualization derivatives, not verified production terrain metrics.

## Map imagery and F17/F18/F27

Elevation and slope PNGs are transparent RGBA visualization derivatives
from the site tiles. Hillshade uses a fixed assumed azimuth of 315° and
altitude of 45°; it is **not** solar illumination. All referenced site
layer images are 1251 × 1251 pixels. The PIA13523 NASA/LRO WAC south-pole
image is a visual background only and has no georeferencing in this
project.

Published LOLA PSR products and Diviner temperature sources are documented
in `docs/research_thermal.md`, but no PSR or Diviner raster has been
integrated. PSR proximity and temperature outputs are therefore
UNAVAILABLE. `docs/future_thermal.md` (F18) and `docs/future_rover.md`
(F27) are design notes only, not implemented models or operational tools.

## Required validation and handoffs

1. M2 must confirm or resolve the DEM/MOON_ME frame discrepancy; current
   generated outputs explicitly remain preliminary pending that decision.
2. The source feature centers are now authoritative Gazetteer values, but
   they are not exact centers for NASA's 15 × 15 km Artemis regions or
   landing points. M1/M2 must decide whether those feature centers are the
   intended application anchors.
3. Six `data/window_metrics_<site_id>.json` files have been regenerated as
   **PRELIMINARY** and their `date_scan` API responses include frame warnings.
   M2 must review the frame/anchor decision and regenerate them as verified
   outputs after sign-off.
4. Perform a documented manual comparison against a named terrain feature
   in an authoritative geospatial viewer; no such check is claimed here.
5. Three supported M1 fallback scenarios were regenerated; M1 should refresh
   them after M2 frame/anchor sign-off. M1/M5 should consume the explicit
   site-center, bounds, and projection metadata in `data/layers.json`, and
   must treat frame alignment as pending.
