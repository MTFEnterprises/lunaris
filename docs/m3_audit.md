# M3 Terrain and Geospatial Data Audit

**Audit outcome: M3 remains partially complete.** M2's reported decision confirms the local raster and six selected project anchors are to be interpreted in `MOON_ME`. M3 coordinate conversion now uses the observed numeric south-polar parameters without applying the conflicting embedded IAU datum label, and tiles, horizons, and map layers have been regenerated. Acquisition date/version remain unknown; independent real-terrain alignment validation and downstream M1/M2 regeneration are still required.

## Scope and project responsibilities

The Master Guide assigns M1 the application/API integration, M2 the lunar ephemeris and illumination work, M3 terrain/geospatial data, M4 the interface, and M5 mapping/visualization. This audit changes M3-owned code, data status, and documentation only. Integration expectations requiring another team's changes are recorded as handoffs.

The audit read the Master Guide, M3 requirements, shared conventions and decisions, data-source documentation, thermal research, terrain methods and code, map-layer generation and outputs, DEM metadata and tiles, horizon outputs, and relevant tests. The repository was on `feature/m3-terrain`. Pre-existing changes in `README.md` and `backend/terrain/hazard.py`, and untracked `data/MOON.jpg`, were left untouched.

## Requirement-by-requirement status

| Requirement | Status | Findings |
|---|---|---|
| M3-01 Candidate-site coordinates | **PARTIALLY COMPLETE** | All six solution-1 IAU Gazetteer feature centers and page-specific URLs are recorded as PUBLISHED, with null heights. M2 confirmed them as the intended project anchors; they are not verified Artemis polygon centers or landing points. |
| M3-02 Frames and conventions | **M2 CONFIRMED; M1 HANDOFF OPEN** | M2's reported decision accepts the raster and selected site anchors as `MOON_ME`. Runtime and generators use the local numeric polar-projection parameters while ignoring the embedded IAU:30135 datum label. M1 must update the shared convention record. |
| M3-03 DEM provenance and metadata | **PARTIALLY COMPLETE** | Product identity, frame interpretation, and published metre units are recorded as verified. Local bytes have no publisher checksum match; retrieval date, product version, and redistribution terms remain unknown. |
| M3-04 Map layers and M5 handoff | **PARTIALLY COMPLETE** | Layers were regenerated using the explicit MOON_ME projection and include site coordinates/source, bounds, and inverse transform. The background image is not georeferenced; M5 should use the catalog bounds and preserve the provenance warning. |
| M3-05 Horizon algorithm and outputs | **PARTIALLY COMPLETE** | Six vectors were regenerated with the current 360-bin algorithm and 0° North/90° East clockwise convention. All have 360 available bins; outputs retain a warning for unknown retrieval date and product version. |
| M3-06 Scientific/manual validation | **PARTIALLY COMPLETE** | Synthetic algorithm tests cover relevant code behaviors, including east-facing direction, curvature, nodata/out-of-coverage, and projection round-trip cases. No manual validation against a known real crater or authoritative terrain reference was performed. |
| M3-07 Slope and roughness | **PARTIALLY COMPLETE** | API slope values are calculated from the regenerated MOON_ME tiles. Missing acquisition date/version remain explicit warnings; the metrics are not a landing-safety certification. |
| M3-08 PSR and temperature research | **UNAVAILABLE** | LOLA PSR and Diviner material remains research-only; no validated PSR proximity or temperature dataset is integrated. These outputs must not be interpreted as available. |
| F18 thermal design | **COMPLETE (design only)** | Future thermal design is documented; it is not an implemented or validated thermal product. |
| F27 rover-operations design | **COMPLETE (design only)** | Future rover-operations design is documented; it is not an implemented terrain/thermal capability. |

### M3-01: Candidate-site coordinates

`data/sites.json` now uses solution 1 from each feature-specific IAU Gazetteer page. All six feature pages and NASA's Artemis candidate-region release returned HTTP 200 on 2026-11-15. The Gazetteer pages state planetographic latitude and east-positive longitude in -180..180. Heights remain null because these pages do not publish elevations at the center coordinates.

The Malapert choice is **Mons Malapert** (Gazetteer Feature 16338), not the separate Malapert crater (Feature 3603), because NASA's Artemis III candidate-region announcement names “Malapert Massif.” This does not establish that the Mons center is the exact center of NASA's 15 × 15 km candidate region. The labels “Shackleton Rim,” “de Gerlache Rim,” and “Nobile Rim” remain project labels; the stored coordinates are crater centers, not rim points.

Changing the selected point can change the DEM tile and pixel, horizon vector, map layers, and site-dependent M2 metrics. M2 confirmed on 2026-11-15 that the Gazetteer feature centers are the intended project anchors; this does not assert that they are exact Artemis candidate-region centers or landing points. Tiles, horizons, layers, all six M2 window-metric files, and all six M1 fallback scenarios have been regenerated from those centers. The M2 files and fallback outputs remain explicitly preliminary pending DEM-frame confirmation. Global/Moon-centered ephemeris vectors do not depend on a candidate-site coordinate.

### M3-02: Coordinate frames and conventions

- Shared project and M2 convention: `MOON_ME`. NASA PGDA Product 90 states that its large-area DEM GeoTIFFs, including `LDEM_80S_80MPP_ADJ.TIF`, use `MOON_ME` of JPL DE421. The local file reports IAU:30135 / Moon (2015) Sphere Ocentric (underlying datum IAU:30100). M2's decision, as reported by the project owner on 2026-11-15, is that the local raster coordinates are `MOON_ME` and the embedded IAU datum label is erroneous/alias. No separate M2 evidence artifact was supplied.
- Local raster projection: polar stereographic, with raster coordinates in meters; the raster extent is approximately ±304,000 m, with 80 m pixels.
- Runtime and offline generation now parse the projection's numeric parameters from the local WKT (sphere radius 1,737,400 m, standard parallel −90°, central meridian 0°, false easting/northing 0) and project input coordinates as `MOON_ME`. They do not use the WKT's geodetic datum transform. Raster pixels were not reprojected.
- Horizon convention in code: 0° north, 90° east, increasing clockwise. The implementation uses the east component for the 90° direction.
- Curvature correction in code: distance-squared over twice the lunar radius, using 1,737,400 m. Observer elevation is included relative to the sampled terrain.
- Sampling uses the nearest raster pixel. This is a documented limitation; it is not sub-pixel interpolation.
- A polar-stereographic inverse pixel-to-latitude/longitude transform is described in the generated layer metadata and has a projection round-trip test. This does not resolve the raster's datum/frame conflict.

The M2 decision resolves the project interpretation but does not correct the source-file WKT or independently validate pixel-to-feature alignment. The local WKT and hash remain preserved as observed; no datum conversion is applied. M1 should update `docs/conventions.md` to reflect the reported sign-off.

### M3-03: DEM provenance and metadata

The local source file inspected was `LDEM_80S_80MPP_ADJ.TIF`: 7,600 × 7,600 pixels, nominal 80 m pixel spacing, float32 elevations, NaN nodata, and observed elevation range approximately −7,295.52 to +7,026.33 m. Its GeoTIFF band unit metadata is unset. The source file is 189,158,392 bytes and is Git-ignored/not tracked; its local SHA-256 is `82030DCBDD7C4BB0C7D858E9B4B293B9F2CDA5A543BA31EC0F42784BD6BEEE5A`. NASA PGDA Product 90 lists this filename at approximately 181 MB and states the product family's `MOON_ME` / JPL DE421 frame. M2's reported decision accepts the local raster as `MOON_ME` despite its embedded IAU:30135 label. The hash identifies the local file but has not been matched to a NASA-published checksum. Raster coordinate values were not transformed.

All six committed DEM tiles were regenerated using the M2-approved MOON_ME interpretation and checked at 1,251 × 1,251 pixels and 80 m. Tile values were compared against direct source-DEM samples using the same explicit projection formula. This is a consistency check, not an independent geographic control-point validation. Acquisition/retrieval history, product version, publisher checksum, and redistribution terms remain unknown. The publisher describes product elevations in metres, but the local GeoTIFF band unit is unset. Product 90 is the relevant large-area DEM product page; Product 78 describes separate 5 m site-region products and is not the source listing for this 80 m file.

The six regenerated tile files total 32.32 MiB. The map-layer directory totals 29.60 MiB; together they are about 61.92 MiB before application code and dependencies. Vercel's [current Function limits](https://vercel.com/docs/functions/limitations) document a 500 MB uncompressed package limit for Python Functions. The terrain-asset subtotal is below that limit, but the complete built function package and deployment were not measured; package status remains unverified.

### M3-04: Map layers and M5 handoff

The layer references resolve to 18 existing PNG files. They are 1,251 × 1,251 RGBA images. Elevation and hillshade images have no transparent pixels for the checked tiles; slope images have a transparent border around unavailable edge pixels. RGBA mode alone should not be mistaken for meaningful transparency throughout an image.

Layers are derived from the local DEM and use the M2-approved MOON_ME interpretation of the published feature centers. The hillshade is a fixed-azimuth terrain visualization, **not** actual sunlight or solar illumination. The NASA south-pole background image attribution is documented (NASA/JPL, PIA13523; <https://photojournal.jpl.nasa.gov/catalog/PIA13523>), but that image is not georeferenced and must not be assumed to align precisely with the DEM. Layer geographic bounds and the pixel-to-geographic inverse formula are exposed in `data/layers.json`; M5 should not infer bounds from image dimensions.

### M3-05: Horizon algorithm and outputs

`backend/terrain/horizon.py` produces 360 azimuth samples. The curvature correction is applied using the configured lunar radius, observer height is accounted for, and rays use nearest-pixel terrain sampling. If a ray has incomplete coverage, the code now returns null for that azimuth instead of preserving a potentially underestimating maximum from only part of the ray.

`scripts/terrain/generate_horizons.py` regenerated all six outputs from the local DEM on 2026-11-15. Each output has 360 bins, stores its feature-center coordinates and source, and records the generation time, algorithm, and `M2_CONFIRMED_MOON_ME` frame status. All rays had complete coverage in this run. The files retain a warning that retrieval date and product version are unknown. Generation does not establish scientific agreement with lunar ground truth.

### M3-06: Scientific and manual validation

Automated M3 tests passed (commands and totals below). They establish tested software behavior on synthetic fixtures, not scientific agreement with lunar ground truth. No manual known-crater comparison, independent geographic-control-point validation, or expert review was performed. Those remain required before claiming scientific validation.

### M3-07: Slope and roughness

Slope is expressed in degrees; roughness is the RMS elevation residual in meters over the local fitting neighborhood. The API's established field names include mean/max slope and roughness, with a slope profile where available. Coverage is local to the DEM and edge/nodata neighborhoods may be incomplete. These are terrain metrics, not rover traversability classifications.

Slope API outputs are available from the regenerated tiles because product identity, frame interpretation, and published units are marked verified. The API continues to emit `DEM_META_INCOMPLETE` for the unknown retrieval date and product version. Map slope images are visualization derivatives, not verified landing-safety measurements. `backend/terrain/hazard.py` was not changed; its blocking treatment of provenance warnings remains in effect.

### M3-08: PSR and temperature

`docs/research_thermal.md` and `docs/future_thermal.md` describe research and future work. No validated LOLA PSR or Diviner products are integrated into the current terrain API. PSR distance/proximity and temperature outputs are therefore **UNAVAILABLE**, not zero, estimated, or implied by hillshade.

## Confirmed problems and changes made

1. Replaced unsupported site coordinates with the six proposal's authoritative Gazetteer solution-1 feature centers, retaining null heights and source links.
2. The local GeoTIFF datum label conflicted with the product-page frame statement. Recorded the reported M2 decision and changed coordinate conversion to use explicit `MOON_ME` input with the raster's numeric projection parameters, without changing raster pixels.
3. Slope metrics were blocked while the frame was pending. They are now calculated from regenerated tiles; missing retrieval date/version remain API warnings and block downstream hazard promotion.
4. An incomplete horizon ray could retain a potentially underestimated maximum. It now yields an unavailable bin.
5. Existing horizon vectors lacked current-frame provenance. Regenerated all six with the current algorithm and recorded M2 frame status plus incomplete-acquisition metadata warning.
6. Map-layer geographic conversion and alignment limitations were insufficiently explicit. Added inverse-transform metadata and documented the approved coordinate interpretation and background-image limitations.
7. Added M3 methods/limitations documentation and tests for unverified DEM handling and projection round-trip behavior.

No unrelated files were edited. The pre-existing `README.md`, `backend/terrain/hazard.py`, and untracked `data/MOON.jpg` changes remain untouched.

## Files changed

- `backend/terrain/horizon.py`, `backend/terrain/terrain.py`, `backend/terrain/projection.py` — explicitly project MOON_ME coordinates using numeric CRS parameters, without datum-label transformations.
- `backend/terrain/test_m3.py` — test projection-parameter extraction independent of the embedded datum label.
- `backend/terrain/slope.py` — gate metrics on verified DEM metadata and warn when retrieval date/version are missing.
- `backend/terrain/test_slope.py` — verify incomplete acquisition metadata warns without suppressing calculated slope.
- `scripts/terrain/generate_map_layers.py` — emit MOON_ME alignment and inverse projection metadata.
- `scripts/terrain/generate_horizons.py` — regenerate six-site horizons with M2 frame status and provenance warning.
- `scripts/ephemeris/precompute_ephemeris.py`, `backend/science/runtime.py`, `backend/services/scenario_service.py` — generate preliminary metric provenance and expose pending-frame warnings through date-scan.
- `scripts/terrain/make_dem_tiles.py` — derive numeric projection parameters and regenerate tiles using MOON_ME coordinates.
- `backend/tests/test_adapters.py` — verify ephemeris for published coordinates and the current terrain API contract.
- `backend/tests/test_runtime.py`, `backend/tests/test_api.py` — verify preliminary metric status and warning propagation.
- `data/sites.json` — publish feature-center coordinates, source URLs, and honest null elevations.
- `data/dem_tiles/*.npz`, `data/horizon_*.json`, `data/layers/*.png` — regenerate outputs for the six feature centers.
- `data/window_metrics_*.json` — regenerate all six M2 metric files as preliminary pending frame confirmation.
- `backend/fallback/scenarios/*_2027-03-14.json` — regenerate all six M1 fallback scenarios with pending-frame warnings after merging the current M1 generator.
- `data/dem_meta.json` — record reported M2 frame decision while preserving unknown retrieval/version.
- `data/sites.json` — record the M2-approved project-frame interpretation.
- `data/dem_tiles/*.npz`, `data/horizon_*.json`, `data/layers/*.png` — regenerate M3 outputs with explicit MOON_ME projection.
- `data/layers.json` — inverse transform and M2-confirmed alignment status.
- `docs/data_sources.md`, `docs/decisions.md` — provenance, coordinate choice, Malapert resolution, and reported M2 frame decision.
- `docs/method.md` — M3 methods and limitations.
- `docs/m3_audit.md` — this audit report.

## Verification actually run

| Check | Result |
|---|---|
| `& ".venv\Scripts\python.exe" -m pytest -q --tb=short` | **265 passed, 1 skipped, 1 failed:** `test_moon_me_rotation_matches_naif_frame_kernel` cannot run because the four required local NAIF kernels are absent. They were not downloaded. |
| `& ".venv\Scripts\python.exe" -m pytest -q --tb=short -k 'not test_moon_me_rotation_matches_naif_frame_kernel'` | **265 passed, 1 skipped, 1 deselected.** |
| Targeted terrain/slope/API regression tests | **Passed** in the suite above, including the bound-datum lookup regression and the incomplete-provenance warning test. |
| Exact local DEM metadata and frame provenance | **Inspected:** 7,600 × 7,600 GeoTIFF, embedded IAU:30135 WKT, band unit unset, SHA-256 recorded. PGDA Product 90 declares `MOON_ME` / JPL DE421; the project owner reports M2 confirmed that interpretation for this local raster. The hash is not matched to a publisher checksum. |
| `git diff --check` | **Passed.** |
| JSON and site records | **Passed:** all six records have source URLs, `PUBLISHED` coordinates, null heights, and the reported M2-approved project-frame interpretation. |
| DEM-tile check | **Passed for all six:** 1,251 × 1,251 at 80 m, finite arrays, MOON_ME metadata, projection round-trip checked, and sampled values matched direct reads from the source DEM. |
| Regeneration consistency | **Passed:** all six elevation arrays and all six horizon vectors are numerically identical to the previous committed outputs; the regenerated assets clarify frame semantics and provenance metadata. |
| Horizon-file check | **Passed structurally for all six:** exactly 360 available bins, generated with the current algorithm, `M2_CONFIRMED_MOON_ME`, and an explicit missing retrieval/version warning. |
| Map-layer references and images | **Passed:** all 18 references resolve to 1,251 × 1,251 RGBA PNGs; catalog bounds, inverse transform, frame, and site definitions are recorded. |
| M2 window metrics | **Not refreshed in this M3 change:** six files remain `PRELIMINARY` and must be reviewed/regenerated by M2. |
| M1 fallbacks | **Not refreshed in this M3 change:** six existing scenarios retain their pre-signoff frame warnings and must be regenerated by M1. |
| Date-scan API smoke check | **Not rerun after frame sign-off:** it still consumes pre-signoff M2 metric files until M2 refreshes them. |
| Known-crater/manual alignment validation | **Not performed.** |
| Vercel asset-size estimate | **Complete function bundle not measured; deployment implications remain unverified.** |
| Vercel deployment/package validation | **Not performed.** |

## Uncertainties and authoritative confirmation required

1. The Gazetteer feature centers are confirmed as project anchors, not exact Artemis region centers or landing points; the Gazetteer pages do not publish their frame.
2. Attach the written M2 decision or authoritative source for the reported `MOON_ME` interpretation; the current record is a project-owner report, not an external evidence link.
3. Original DEM retrieval date, product version, checksum match, and redistribution terms remain unknown.
4. Independent validation of DEM-to-site alignment and horizon/slope outputs against a known feature or authoritative reference remains outstanding.
5. M2 window metrics and M1 fallback outputs still carry their pre-signoff warnings and need review/regeneration by their owners.
6. Deployment behavior for the regenerated tile and map PNG bundle remains unverified.

## Required handoffs

- **M1:** Update the M1-owned `docs/conventions.md` frame note and stale slope example in `docs/api.md` to reflect the reported M2 decision; refresh all six fallback scenarios from the current API and keep incomplete-provenance warnings visible.
- **M2 (Huzaifa):** Six `data/window_metrics_<site_id>.json` files remain `PRELIMINARY`. Review the regenerated M3 tiles/horizons and regenerate or confirm the six metrics using `& ".venv\Scripts\python.exe" -c "from scripts.ephemeris.precompute_ephemeris import generate_all_site_window_metrics; generate_all_site_window_metrics()"`. Do not run the script's full `__main__` unless ephemeris kernels are also intended to be rebuilt.
- **M5:** Consume explicit bounds/transform and the `MOON_ME` interpretation from `data/layers.json`. Do not georeference the PIA13523 background by assumption or treat hillshade as solar illumination.
- **M4 (dependent UX):** Coordinate display/disable behavior for unavailable site-derived layers and metrics with M1; do not imply that null site data means zero or safe terrain.

## Remaining manual actions

1. Attach M2's written decision or authoritative source for the reported `MOON_ME` interpretation, and have M1 update the shared convention record.
2. Have M2 review/regenerate its window metrics and M1 refresh fallback scenarios from the newly regenerated M3 outputs.
3. Confirm local-file checksum against a publisher-provided value if available, plus retrieval date, product version, and redistribution terms. The local SHA-256 is recorded for identification, not source authentication.
4. Perform independent terrain-control-point / known-crater alignment validation.
5. Measure the complete Vercel function bundle and deployment artifact; the terrain-only estimate is not a substitute. Do not call these data scientifically validated until independent geographic alignment checks are performed.

## Git readiness and suggested commands

The branch is `feature/m3-terrain`. M3's latest coordinate-frame changes and regenerated outputs require M1/M2 review; the PR is not yet merged, production deployment is unconfirmed, and the written M2 evidence is not attached to the repository.

From the isolated worktree after resolving the conflict:

```powershell
git status
git add docs/m3_audit.md
git diff --cached --check
git commit -m "Merge main into feature/m3-terrain and resolve audit conflict" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push origin HEAD:feature/m3-terrain
```

The merge into `feature/m3-terrain` is already pushed. Do not stage or commit the pre-existing `README.md`, `backend/terrain/hazard.py`, or `data/MOON.jpg` changes from the original worktree.
