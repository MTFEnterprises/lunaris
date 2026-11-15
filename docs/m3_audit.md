# M3 Terrain and Geospatial Data Audit

**Audit outcome: M3 remains partially complete.** The six published IAU Gazetteer feature centers are recorded and dependent M3 assets have been regenerated. The selected points are feature centers, not verified centers of the NASA Artemis candidate polygons, and the DEM frame remains pending M2 confirmation; outputs are explicitly marked preliminary.

## Scope and project responsibilities

The Master Guide assigns M1 the application/API integration, M2 the lunar ephemeris and illumination work, M3 terrain/geospatial data, M4 the interface, and M5 mapping/visualization. This audit changes M3-owned code, data status, and documentation only. Integration expectations requiring another team's changes are recorded as handoffs.

The audit read the Master Guide, M3 requirements, shared conventions and decisions, data-source documentation, thermal research, terrain methods and code, map-layer generation and outputs, DEM metadata and tiles, horizon outputs, and relevant tests. The repository was on `feature/m3-terrain`. Pre-existing changes in `README.md` and `backend/terrain/hazard.py`, and untracked `data/MOON.jpg`, were left untouched.

## Requirement-by-requirement status

| Requirement | Status | Findings |
|---|---|---|
| M3-01 Candidate-site coordinates | **PARTIALLY COMPLETE** | All six solution-1 IAU Gazetteer feature centers and page-specific URLs are recorded as PUBLISHED, with null heights. They are not verified Artemis polygon centers or landing points. |
| M3-02 Frames and conventions | **NEEDS M1/M2 COORDINATION** | Code uses a polar stereographic raster and the documented horizon convention, but the local raster identifies `IAU:30135` / Moon-2015 Sphere Ocentric while the project convention and M2 use `MOON_ME`. No frame conversion or convention change was made. |
| M3-03 DEM provenance and metadata | **PARTIALLY COMPLETE** | Local raster/tile properties were inspected and unknown provenance fields remain unknown. Product/frame identity, retrieval date, product version, and elevation units are not sufficiently established for scientific use. |
| M3-04 Map layers and M5 handoff | **NEEDS M1/M2/M5 COORDINATION** | Layers were regenerated and include each site's feature-center coordinates/source, bounds, and inverse transform. They remain preliminary pending DEM-frame confirmation; the background image is not georeferenced. |
| M3-05 Horizon algorithm and outputs | **PARTIALLY COMPLETE** | Six vectors were regenerated with the current 360-bin algorithm and 0° North/90° East clockwise convention. All six have full 360-bin coverage in this run; DEM/MOON_ME frame compatibility remains pending M2. |
| M3-06 Scientific/manual validation | **PARTIALLY COMPLETE** | Synthetic algorithm tests cover relevant code behaviors, including east-facing direction, curvature, nodata/out-of-coverage, and projection round-trip cases. No manual validation against a known real crater or authoritative terrain reference was performed. |
| M3-07 Slope and roughness | **PARTIALLY COMPLETE** | Metric calculations and units are documented; API slope values remain unavailable while DEM metadata is pending verification. Adapter tests reflect that contract. |
| M3-08 PSR and temperature research | **UNAVAILABLE** | LOLA PSR and Diviner material remains research-only; no validated PSR proximity or temperature dataset is integrated. These outputs must not be interpreted as available. |
| F18 thermal design | **COMPLETE (design only)** | Future thermal design is documented; it is not an implemented or validated thermal product. |
| F27 rover-operations design | **COMPLETE (design only)** | Future rover-operations design is documented; it is not an implemented terrain/thermal capability. |

### M3-01: Candidate-site coordinates

`data/sites.json` now uses solution 1 from each feature-specific IAU Gazetteer page. All six feature pages and NASA's Artemis candidate-region release returned HTTP 200 on 2026-11-15. The Gazetteer pages state planetographic latitude and east-positive longitude in -180..180. Heights remain null because these pages do not publish elevations at the center coordinates.

The Malapert choice is **Mons Malapert** (Gazetteer Feature 16338), not the separate Malapert crater (Feature 3603), because NASA's Artemis III candidate-region announcement names “Malapert Massif.” This does not establish that the Mons center is the exact center of NASA's 15 × 15 km candidate region. The labels “Shackleton Rim,” “de Gerlache Rim,” and “Nobile Rim” remain project labels; the stored coordinates are crater centers, not rim points.

Changing the selected point can change the DEM tile and pixel, horizon vector, map layers, and site-dependent M2 metrics. M2 confirmed on 2026-11-15 that the Gazetteer feature centers are the intended project anchors; this does not assert that they are exact Artemis candidate-region centers or landing points. Tiles, horizons, layers, all six M2 window-metric files, and the three supported M1 fallback scenarios have been regenerated from those centers. The M2 files and fallback outputs remain explicitly preliminary pending DEM-frame confirmation. Global/Moon-centered ephemeris vectors do not depend on a candidate-site coordinate.

### M3-02: Coordinate frames and conventions

- Shared project and M2 convention: `MOON_ME`; the local GeoTIFF reports `IAU:30135` / Moon-2015 Sphere Ocentric. The source-product page and local raster metadata are not enough to resolve whether they are the same usable frame for this workflow.
- Local raster projection: polar stereographic, with raster coordinates in meters; the raster extent is approximately ±304,000 m, with 80 m pixels.
- Horizon convention in code: 0° north, 90° east, increasing clockwise. The implementation uses the east component for the 90° direction.
- Curvature correction in code: distance-squared over twice the lunar radius, using 1,737,400 m. Observer elevation is included relative to the sampled terrain.
- Sampling uses the nearest raster pixel. This is a documented limitation; it is not sub-pixel interpolation.
- A polar-stereographic inverse pixel-to-latitude/longitude transform is described in the generated layer metadata and has a projection round-trip test. This does not resolve the raster's datum/frame conflict.

No evidence justified silently transforming the raster, changing the project convention, or declaring the local DEM frame equivalent to `MOON_ME`.

### M3-03: DEM provenance and metadata

The local source file inspected was `LDEM_80S_80MPP_ADJ.TIF`: 7,600 × 7,600 pixels, nominal 80 m pixel spacing, float32 elevations, NaN nodata, and observed elevation range approximately −7,295.52 to +7,026.33 m. The band unit metadata is unset. The source file is approximately 189,158,392 bytes and is Git-ignored/not tracked.

All six committed DEM tiles were checked: each is 1,251 × 1,251 at 80 m. The tile metadata was checked for internal consistency. These observations describe the local files, but do not validate their geodetic frame, exact product/version, retrieval date, licensing terms, or elevation-unit declaration. Unknown values remain unknown in `data/dem_meta.json`; no retrieval date or version was invented. The NASA product-information page is recorded as a source lead: <https://pgda.gsfc.nasa.gov/products/78>.

The six regenerated tile files total 32.32 MiB. The 18 map-layer PNGs total 29.60 MiB, or 61.91 MiB combined before application code and dependencies. A Vercel deployment/package-size check was not run. Deployment configuration should be checked to ensure these static assets are served as assets rather than unintentionally bundled into a serverless function.

### M3-04: Map layers and M5 handoff

The layer references resolve to 18 existing PNG files. They are 1,251 × 1,251 RGBA images. Elevation and hillshade images have no transparent pixels for the checked tiles; slope images have a transparent border around unavailable edge pixels. RGBA mode alone should not be mistaken for meaningful transparency throughout an image.

Layers are derived from the local DEM and use the confirmed project site anchors, but their alignment remains preliminary pending frame confirmation. The hillshade is a fixed-azimuth terrain visualization, **not** actual sunlight or solar illumination. The NASA south-pole background image attribution is documented (NASA/JPL, PIA13523; <https://photojournal.jpl.nasa.gov/catalog/PIA13523>), but that image is not georeferenced and must not be assumed to align precisely with the DEM. Layer geographic bounds and the pixel-to-geographic inverse formula are exposed in `data/layers.json`; M5 should not infer bounds from image dimensions.

### M3-05: Horizon algorithm and outputs

`backend/terrain/horizon.py` produces 360 azimuth samples. The curvature correction is applied using the configured lunar radius, observer height is accounted for, and rays use nearest-pixel terrain sampling. If a ray has incomplete coverage, the code now returns null for that azimuth instead of preserving a potentially underestimating maximum from only part of the ray.

`scripts/terrain/generate_horizons.py` regenerated all six outputs from the local DEM on 2026-11-15. Each output has 360 bins, stores its feature-center coordinates and source, and records the generation time, algorithm, and `PENDING_M2_CONFIRMATION` frame status. All rays had complete coverage in this run. Generation does not establish scientific frame correctness.

### M3-06: Scientific and manual validation

Automated M3 tests passed (commands and totals below). They establish tested software behavior on synthetic fixtures, not scientific agreement with lunar ground truth. No manual known-crater comparison, independent geographic-control-point validation, or expert review was performed. Those remain required before claiming scientific validation.

### M3-07: Slope and roughness

Slope is expressed in degrees; roughness is the RMS elevation residual in meters over the local fitting neighborhood. The API's established field names include mean/max slope and roughness, with a slope profile where available. Coverage is local to the DEM and edge/nodata neighborhoods may be incomplete. These are terrain metrics, not rover traversability classifications.

Slope API outputs remain unavailable when DEM metadata is absent or unverified rather than exposing numerically computed values as trusted measurements. Map slope images have been regenerated from the local raster but are visualization derivatives, not verified API terrain measurements. `backend/terrain/hazard.py` had a pre-existing user modification and was not changed during this audit. Its pre-existing API/threshold behavior was not redefined.

### M3-08: PSR and temperature

`docs/research_thermal.md` and `docs/future_thermal.md` describe research and future work. No validated LOLA PSR or Diviner products are integrated into the current terrain API. PSR distance/proximity and temperature outputs are therefore **UNAVAILABLE**, not zero, estimated, or implied by hillshade.

## Confirmed problems and changes made

1. Replaced unsupported site coordinates with the six proposal's authoritative Gazetteer solution-1 feature centers, retaining null heights and source links.
2. DEM frame identity conflicts with the shared `MOON_ME` convention. Documented the evidence and uncertainty; did not silently transform or change frames.
3. Slope metrics could be exposed despite pending DEM provenance/frame verification. They now remain unavailable until the metadata is verified.
4. An incomplete horizon ray could retain a potentially underestimated maximum. It now yields an unavailable bin.
5. Existing horizon vectors lacked established current-algorithm provenance. Regenerated them with the current algorithm and recorded generation/provenance plus the pending-frame warning.
6. Map-layer geographic conversion and alignment limitations were insufficiently explicit. Added inverse-transform metadata and documented pending site alignment and background-image limitations.
7. Added M3 methods/limitations documentation and tests for unverified DEM handling and projection round-trip behavior.

No unrelated files were edited. The pre-existing `README.md`, `backend/terrain/hazard.py`, and untracked `data/MOON.jpg` changes remain untouched.

## Files changed

- `backend/terrain/horizon.py` — unavailable bins for incomplete rays.
- `backend/terrain/test_m3.py` — test incomplete-ray behavior.
- `backend/terrain/slope.py` — gate metrics on verified DEM metadata; inverse projection support.
- `backend/terrain/test_slope.py` — tests for metadata gating and projection round-trip.
- `scripts/terrain/generate_map_layers.py` — emit inverse projection metadata.
- `scripts/terrain/generate_horizons.py` — reproducible six-site horizon generation with provenance.
- `scripts/ephemeris/precompute_ephemeris.py`, `backend/science/runtime.py`, `backend/services/scenario_service.py` — generate preliminary metric provenance and expose pending-frame warnings through date-scan.
- `scripts/terrain/make_dem_tiles.py` — use 50 km half-width by default and carry DEM frame/provenance in tile metadata.
- `backend/tests/test_adapters.py` — verify ephemeris for the now-published curated coordinate and unavailable slope while DEM metadata remains pending.
- `backend/tests/test_runtime.py`, `backend/tests/test_api.py` — verify preliminary metric status and warning propagation.
- `data/sites.json` — publish feature-center coordinates, source URLs, and honest null elevations.
- `data/dem_tiles/*.npz`, `data/horizon_*.json`, `data/layers/*.png` — regenerate outputs for the six feature centers.
- `data/window_metrics_*.json` — regenerate all six M2 metric files as preliminary pending frame confirmation.
- `backend/fallback/scenarios/*_2027-03-14.json` — regenerate the three supported M1 fallback scenarios with pending-frame warnings.
- `data/dem_meta.json` — distinguish observed properties from unverified provenance.
- `data/layers.json` — inverse transformation and pending-alignment status.
- `docs/data_sources.md`, `docs/decisions.md` — provenance, coordinate choice, Malapert resolution, and pending frame decision.
- `docs/method.md` — M3 methods and limitations.
- `docs/m3_audit.md` — this audit report.

## Verification actually run

| Check | Result |
|---|---|
| `& ".venv\Scripts\python.exe" -m pytest -q` | **Passed: 235 passed, 1 skipped in 9.51s**, after regenerating M3, provisional M2, and supported M1 fallback outputs. |
| Python compilation | **Passed** for the ephemeris/terrain generators, runtime, scenario service, and related tests. |
| `git diff --check -- backend/terrain/horizon.py backend/terrain/slope.py backend/terrain/test_m3.py backend/terrain/test_slope.py backend/tests/test_adapters.py backend/tests/test_api.py backend/tests/test_runtime.py backend/science/runtime.py backend/services/scenario_service.py data docs scripts` | **Passed** (only a line-ending notice for `docs/data_sources.md`). |
| Repository-wide `git diff --check` | **Failed on pre-existing trailing whitespace at `backend/terrain/hazard.py:7`**, within the user's pre-existing edit; intentionally left unchanged. |
| JSON and site records | **Passed:** all six records have coordinates, a per-site source URL, `PUBLISHED` class, and null height. |
| DEM-tile check | **Passed for all six:** regenerated tiles are 1,251 × 1,251 at 80 m, finite with no NaN pixels, and match site coordinates; the generator cross-checks projection and values against the source DEM. |
| Horizon-file check | **Passed structurally for all six:** regenerated vectors have exactly 360 finite bins and record generation/algorithm/source; all are flagged `PENDING_M2_CONFIRMATION`. |
| Map-layer references and images | **Passed:** all 18 references exist, are 1,251 × 1,251 RGBA PNGs, and carry the matching published site centers. |
| M2 window metrics | **Passed structurally:** six files, 365 daily windows each, with `PRELIMINARY`, `MOON_ME` ephemeris frame, source coordinates, generation timestamp, and pending-frame warnings. |
| M1 fallbacks | **Passed structurally:** three supported scenarios regenerated and carry `PENDING_M2_CONFIRMATION` warnings. |
| Date-scan API smoke check | **Passed:** returns the provisional metric and an explicit pending-frame warning. |
| Known-crater/manual alignment validation | **Not performed.** |
| Vercel deployment/package validation | **Not performed.** |

## Uncertainties and authoritative confirmation required

1. Whether M1/M2 intend to anchor their candidate regions at these Gazetteer feature centers or at specific Artemis region centers / selected landing points. **Resolved for the current project outputs:** M2 confirmed the Gazetteer centers as the intended anchors; they are not claimed to be exact Artemis region centers or landing points.
2. Whether the exact local DEM product is in a frame compatible with `MOON_ME`, and, if not, the approved transformation and responsible owner.
3. Original DEM retrieval date, product version, declared vertical units/datum, and license/redistribution terms.
4. Independent validation of DEM-to-site alignment and horizon/slope outputs against a known feature or authoritative reference.
5. Confirm the provisional M2 window metrics and M1 fallback outputs after frame sign-off; regenerate final versions then.
6. Deployment behavior for the regenerated tile and map PNG bundle.

## Required handoffs

- **M1:** Adapter tests were updated to expect geometric ephemeris to work with published feature centers and slope values to remain unavailable until DEM metadata is verified. Three supported fallback scenarios have been regenerated with preliminary warnings; refresh them after M2 sign-off.
- **M2 (Huzaifa):** Six `data/window_metrics_<site_id>.json` files have been regenerated, each with 365 daily windows and `status: PRELIMINARY`. M2 confirmed the Gazetteer feature centers as intended project anchors; they are not claimed to be exact Artemis region centers. The local DEM frame remains IAU:30135 and has not been signed off as compatible with `MOON_ME`. Keep the outputs preliminary until frame sign-off, then regenerate using `& ".venv\Scripts\python.exe" -c "from scripts.ephemeris.precompute_ephemeris import generate_all_site_window_metrics; generate_all_site_window_metrics()"`. Do not run the script's full `__main__` unless ephemeris kernels are also intended to be rebuilt.
- **M5:** Consume explicit bounds/transform from `data/layers.json`, but treat site alignment as preliminary until the DEM/MOON_ME frame decision is complete. Do not georeference the PIA13523 background by assumption or treat hillshade as solar illumination.
- **M4 (dependent UX):** Coordinate display/disable behavior for unavailable site-derived layers and metrics with M1; do not imply that null site data means zero or safe terrain.

## Remaining manual actions

1. Obtain M1/M2 confirmation of DEM-frame compatibility and any required approved transformation. The intended Gazetteer feature-center anchors are confirmed; they are not exact Artemis region centers.
2. After that agreement, regenerate final M2 window metrics and refresh M1 fallback scenarios; current generated values are provisional.
3. Confirm DEM product/version, retrieval provenance, units, and redistribution terms from authoritative product records.
4. Perform independent terrain-control-point / known-crater alignment validation.
5. Run the Vercel deployment/package check. Do not call these data scientifically final until the frame and region-anchor questions are resolved.

## Git readiness and suggested commands

M3 coordinate and product changes, plus provisional dependent metrics/fallbacks, are ready for M1/M2 review. The intended site anchors are confirmed; scientific sign-off still requires the pending DEM-frame decision.

```powershell
git add backend/terrain/horizon.py backend/terrain/test_m3.py backend/terrain/slope.py backend/terrain/test_slope.py backend/tests/test_adapters.py backend/tests/test_api.py backend/tests/test_runtime.py backend/science/runtime.py backend/services/scenario_service.py backend/fallback/scenarios/shackleton_rim_2027-03-14.json backend/fallback/scenarios/malapert_massif_2027-03-14.json backend/fallback/scenarios/haworth_2027-03-14.json scripts/ephemeris/precompute_ephemeris.py scripts/terrain/make_dem_tiles.py scripts/terrain/generate_map_layers.py scripts/terrain/generate_horizons.py data/sites.json data/dem_tiles/*.npz data/horizon_*.json data/window_metrics_*.json data/layers/*.png data/dem_meta.json data/layers.json docs/data_sources.md docs/decisions.md docs/method.md docs/m3_audit.md
git diff --cached --check
git commit -m "m3: publish Gazetteer centers and regenerate terrain products" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push -u origin feature/m3-terrain
```

Do not stage or commit the pre-existing `README.md`, `backend/terrain/hazard.py`, or `data/MOON.jpg` changes as part of this M3 update.
