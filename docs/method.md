# M3 Terrain Method and Limitations

## Scope and status

This note describes M3 calculations and map products. LUNARIS is an
independent student prototype; these outputs are not official NASA products
or flight-certified assessments.

The six coordinates in `data/sites.json` are published IAU Gazetteer
solution-1 feature centers, not independently published Artemis region
centers or selected landing points. Their elevations remain null. Tiles,
horizons, and layers have been regenerated from these feature centers. M2
confirmed, as reported by the project owner on 2026-11-15, that the local
raster and these project anchors are to be interpreted in `MOON_ME`. Retrieval
date and product version remain unknown, and independent geographic alignment
validation has not been performed.

## Source raster and projection

The local source file is `LDEM_80S_80MPP_ADJ.TIF`, listed by the NASA
Goddard Planetary Geodesy and Cartography Working Group (PGDA) as an
80 m/pixel LOLA south-polar elevation product covering 80°S to the pole.
The product page describes large-area products as south-polar
stereographic X/Y in metres and MOON_ME (JPL DE421). The local GeoTIFF
metadata instead declares IAU:30135 / Moon-2015 Sphere Ocentric. M2 confirmed
that this embedded datum label is erroneous/alias for the local product. Its
observed dimensions are 7600 × 7600, bounds are ±304,000 m, band type is
float32, no-data is NaN, and observed elevation range is approximately
-7295.52 to +7026.33 m. The band-unit tag is unset. Retrieval date and
product version are unknown. The M2 confirmation is an internal project
decision; no separate written evidence or source URL was supplied.

`scripts/terrain/make_dem_tiles.py` reads numeric projection parameters from
the WKT (sphere radius 1,737,400 m, standard parallel −90°, central meridian
0°, false easting/northing 0), but uses `MOON_ME` coordinates directly rather
than the embedded IAU datum transform. It checks projection round trips and
compares sampled tile values against direct source-DEM reads. The sample
comparison is not independent geographic control-point validation.

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
`(column + 0.5, row + 0.5)`. These transforms use the M2-approved
`MOON_ME` interpretation and the numeric projection parameters above.
Raster pixel coordinates were not
reprojected; the local `IAU:30135` authority is retained only as an observed
WKT property, not used as the input frame.
The inverse projection in `data/layers.json` maps a selected continuous
pixel coordinate back to latitude/longitude using the same spherical
parameters; this is a projection round-trip, not independent confirmation of
alignment with lunar control points.

## Horizon

`backend/terrain/horizon.py` samples 360 great-circle rays on a sphere with
radius 1,737,400 m. Index `i` is azimuth `i` degrees, with 0° North, 90°
East, clockwise. Samples are taken at one projected DEM pixel-size step,
up to 150 km. Each destination is projected directly from `MOON_ME`
latitude/longitude using the explicit spherical parameters and sampled from
the containing pixel (nearest-pixel sampling; no interpolation).
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
`scripts/terrain/generate_horizons.py`. Each has 360 available bins, stores
its published Gazetteer feature-center coordinates and source URL, and
records the algorithm, generation time, and `M2_CONFIRMED_MOON_ME` status.
They retain a warning that retrieval date and product version are unknown.
Generation does not establish scientific agreement with lunar ground truth.

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

Slope and roughness API metrics are calculated from the regenerated tiles
because `dem_meta.json` records verified product identity, frame
interpretation, and published metre units. The API still reports
`DEM_META_INCOMPLETE` for the unknown retrieval date and product version.
Hazard assessment remains UNKNOWN when those provenance warnings block
promotion. Map slope images are visualization derivatives, not verified
landing-safety metrics.

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

1. Attach M2's written decision or authoritative source for the reported
   `MOON_ME` interpretation; M1 should update the shared convention record.
2. The source feature centers are authoritative Gazetteer values, but they
   are not exact centers for NASA's 15 × 15 km Artemis regions or landing
   points. M2 confirmed them as the intended project anchors and approved
   interpreting them in the project `MOON_ME` frame; the Gazetteer pages do
   not specify that frame.
3. Six `data/window_metrics_<site_id>.json` files have been regenerated as
   **PRELIMINARY**. M2 must review/regenerate them from the current M3
   coordinate interpretation; the existing files still contain pre-signoff
   frame warnings.
4. Perform a documented manual comparison against a named terrain feature
   in an authoritative geospatial viewer; no such check is claimed here.
5. All six M1 fallback scenarios were regenerated before the frame
   confirmation; M1 should refresh them. M1/M5 should consume the explicit
   site-center, bounds, and projection metadata in `data/layers.json`.
