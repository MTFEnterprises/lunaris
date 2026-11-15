# M3 Terrain and Geospatial Data Audit

**Audit outcome: M3 remains partially complete.** The six published IAU Gazetteer feature centers are recorded and dependent M3 assets have been regenerated. The selected points are feature centers, not verified centers of the NASA Artemis candidate polygons, and the DEM frame remains pending M2 confirmation; outputs are explicitly marked preliminary.

## Scope and project responsibilities

The Master Guide assigns M1 the application/API integration, M2 the lunar ephemeris and illumination work, M3 terrain/geospatial data, M4 the interface, and M5 mapping/visualization. This audit changes M3-owned code, data status, and documentation only. Integration expectations requiring another team's changes are recorded as handoffs.

The audit read the Master Guide, M3 requirements, shared conventions and decisions, data-source documentation, thermal research, terrain methods and code, map-layer generation and outputs, DEM metadata and tiles, horizon outputs, and relevant tests. The repository was on `feature/m3-terrain`. Pre-existing changes in `README.md` and `backend/terrain/hazard.py`, and untracked `data/MOON.jpg`, were left untouched.

## Requirement-by-requirement status

| Requirement | Status | Findings |
|---|---|---|
| M3-01 Candidate-site coordinates | **PARTIALLY COMPLETE** | All six solution-1 IAU Gazetteer feature centers and page-specific URLs are recorded as PUBLISHED, with null heights. M2 confirmed them as the intended project anchors; they are not verified Artemis polygon centers or landing points. |
| M3-02 Frames and conventions | **NEEDS M1/M2 COORDINATION** | NASA PGDA Product 90 declares the large-area DEM product family to use `MOON_ME` / JPL DE421, while the exact local file's embedded WKT identifies `IAU:30135` / Moon-2015 Sphere Ocentric. Their relationship is unresolved. No frame conversion or convention change was made. |
| M3-03 DEM provenance and metadata | **PARTIALLY COMPLETE** | The exact filename is listed by PGDA Product 90 and local file properties/hash were recorded. The local embedded CRS conflicts with the product-page frame statement; no published checksum was matched. Retrieval date, version, and redistribution terms remain unknown. |
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

Changing the selected point can change the DEM tile and pixel, horizon vector, map layers, and site-dependent M2 metrics. M2 confirmed on 2026-11-15 that the Gazetteer feature centers are the intended project anchors; this does not assert that they are exact Artemis candidate-region centers or landing points. Tiles, horizons, layers, all six M2 window-metric files, and all six M1 fallback scenarios have been regenerated from those centers. The M2 files and fallback outputs remain explicitly preliminary pending DEM-frame confirmation. Global/Moon-centered ephemeris vectors do not depend on a candidate-site coordinate.

### M3-02: Coordinate frames and conventions

- Shared project and M2 convention: `MOON_ME`. NASA PGDA Product 90 states that its large-area DEM GeoTIFFs, including `LDEM_80S_80MPP_ADJ.TIF`, use `MOON_ME` of JPL DE421. M3's exact local-file inspection reports embedded WKT IAU:30135 / Moon (2015) Sphere Ocentric (underlying datum IAU:30100). PROJ defines that IAU CRS from the IAU coordinate-system report; NAIF documents that its IAU/IAG `IAU_MOON` and DE-421 `MOON_ME` realizations differ measurably. The PGDA declaration and local WKT have not been reconciled, so compatibility and any needed transformation remain unresolved.
- Local raster projection: polar stereographic, with raster coordinates in meters; the raster extent is approximately ±304,000 m, with 80 m pixels.
- Horizon convention in code: 0° north, 90° east, increasing clockwise. The implementation uses the east component for the 90° direction.
- Curvature correction in code: distance-squared over twice the lunar radius, using 1,737,400 m. Observer elevation is included relative to the sampled terrain.
- Sampling uses the nearest raster pixel. This is a documented limitation; it is not sub-pixel interpolation.
- A polar-stereographic inverse pixel-to-latitude/longitude transform is described in the generated layer metadata and has a projection round-trip test. This does not resolve the raster's datum/frame conflict.

No evidence justified silently transforming the raster, changing the project convention, or declaring the local DEM frame equivalent to `MOON_ME`. M3 must reconcile the exact local file metadata with the PGDA product statement or provide an approved transformation before M2 can sign off and publish final window metrics.

### M3-03: DEM provenance and metadata

The local source file inspected was `LDEM_80S_80MPP_ADJ.TIF`: 7,600 × 7,600 pixels, nominal 80 m pixel spacing, float32 elevations, NaN nodata, and observed elevation range approximately −7,295.52 to +7,026.33 m. Its GeoTIFF band unit metadata is unset. The source file is 189,158,392 bytes and is Git-ignored/not tracked; its local SHA-256 is `82030DCBDD7C4BB0C7D858E9B4B293B9F2CDA5A543BA31EC0F42784BD6BEEE5A`. NASA PGDA Product 90 lists this filename at approximately 181 MB and states the product family's `MOON_ME` / JPL DE421 frame. The local embedded WKT instead identifies IAU:30135 / Moon (2015) Sphere Ocentric. The hash identifies the local file but has not been matched to a NASA-published checksum. No transformation has been applied.

All six committed DEM tiles were checked: each is 1,251 × 1,251 at 80 m. The tile metadata was checked for internal consistency. These observations do not independently validate the local file's frame, acquisition/retrieval history, product version, or redistribution terms. The publisher describes the product elevations in metres, but the local GeoTIFF band unit is unset. Unknown values remain unknown in `data/dem_meta.json`; no retrieval date or version was invented. Product 90 is the relevant large-area DEM product page; Product 78 describes separate 5 m site-region products and is not the source listing for this 80 m file.

The six regenerated tile files total 32.32 MiB. The map-layer directory totals 29.60 MiB; together they are about 61.92 MiB before application code and dependencies. Vercel's [current Function limits](https://vercel.com/docs/functions/limitations) document a 500 MB uncompressed package limit for Python Functions. The terrain-asset subtotal is below that limit, but the complete built function package and deployment were not measured; package status remains unverified.

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
- `backend/fallback/scenarios/*_2027-03-14.json` — regenerate all six M1 fallback scenarios with pending-frame warnings after merging the current M1 generator.
- `data/dem_meta.json` — distinguish observed properties from unverified provenance.
- `data/layers.json` — inverse transformation and pending-alignment status.
- `docs/data_sources.md`, `docs/decisions.md` — provenance, coordinate choice, Malapert resolution, and pending frame decision.
- `docs/method.md` — M3 methods and limitations.
- `docs/m3_audit.md` — this audit report.

## Verification actually run

| Check | Result |
|---|---|
| `& ".venv\Scripts\python.exe" -m pytest -q` | **Passed: 235 passed, 1 skipped in 9.51s**, after regenerating M3, provisional M2, and supported M1 fallback outputs. |
| Full test suite on the merged PR branch | **259 passed, 1 skipped, 1 failed:** `test_moon_me_rotation_matches_naif_frame_kernel` could not run because the four required local NAIF kernels are absent. They were not downloaded. |
| Test suite excluding the unavailable-kernel case | **259 passed, 1 skipped, 1 deselected.** |
| Current DEM metadata/API regression tests | **Passed: 26 tests** across `backend/terrain/test_slope.py` and `backend/tests/test_adapters.py`. |
| Python compilation | **Passed** for the ephemeris/terrain generators, runtime, scenario service, and related tests. |
| Exact local DEM metadata and frame provenance | **Inspected:** 7,600 × 7,600 GeoTIFF, embedded IAU:30135 WKT, band unit unset, SHA-256 recorded. PGDA Product 90 declares `MOON_ME` / JPL DE421 for the product family; this discrepancy remains unresolved, and the hash was not matched to a publisher checksum. |
| `git diff --check` for current provenance/report changes | **Passed.** |
| Full merge diff whitespace check | **Inherited warnings:** trailing whitespace in merged `README.md` and `docs/api.md`; neither is part of the current M3 provenance edits. |
| JSON and site records | **Passed:** all six records have coordinates, a per-site source URL, `PUBLISHED` class, and null height. |
| DEM-tile check | **Passed for all six:** regenerated tiles are 1,251 × 1,251 at 80 m, finite with no NaN pixels, and match site coordinates; the generator cross-checks projection and values against the source DEM. |
| Horizon-file check | **Passed structurally for all six:** regenerated vectors have exactly 360 finite bins and record generation/algorithm/source; all are flagged `PENDING_M2_CONFIRMATION`. |
| Map-layer references and images | **Passed:** all 18 references exist, are 1,251 × 1,251 RGBA PNGs, and carry the matching published site centers. |
| M2 window metrics | **Passed structurally:** six files, 365 daily windows each, with `PRELIMINARY`, `MOON_ME` ephemeris frame, source coordinates, generation timestamp, and pending-frame warnings. |
| M1 fallbacks | **Passed structurally:** all six scenarios regenerated from the merged API and carry `PENDING_M2_CONFIRMATION` warnings. |
| Date-scan API smoke check | **Passed:** returns the provisional metric and an explicit pending-frame warning. |
| Known-crater/manual alignment validation | **Not performed.** |
| Vercel asset-size estimate | **Measured:** terrain tiles and layer directory total about 61.92 MiB. The current published Python Function limit is 500 MB uncompressed; complete package build/deployment size was **not verified**. |
| Vercel deployment/package validation | **Not performed.** |

## Uncertainties and authoritative confirmation required

1. The Gazetteer feature centers are confirmed as the intended project anchors by M2; they are not asserted to be exact Artemis region centers or landing points.
2. Whether the exact local DEM's IAU:30135 embedded WKT is compatible with the PGDA Product 90 `MOON_ME` / JPL DE421 product declaration, and, if not, the approved transformation and responsible owner.
3. Original DEM retrieval date, product version, local band-unit/datum declaration, and license/redistribution terms.
4. Independent validation of DEM-to-site alignment and horizon/slope outputs against a known feature or authoritative reference.
5. Confirm the provisional M2 window metrics and M1 fallback outputs after frame sign-off; regenerate final versions then.
6. Deployment behavior for the regenerated tile and map PNG bundle.

## Required handoffs

- **M1:** Adapter tests were updated to expect geometric ephemeris to work with published feature centers and slope values to remain unavailable until DEM metadata is verified. All six fallback scenarios have been regenerated from the merged API with preliminary warnings; refresh them after M2 frame sign-off.
- **M2 (Huzaifa):** Six `data/window_metrics_<site_id>.json` files currently have 365 daily windows and `status: PRELIMINARY`. The Gazetteer anchors are confirmed. M3's local-file inspection identifies `data/dem/LDEM_80S_80MPP_ADJ.TIF` (SHA-256 `82030DCBDD7C4BB0C7D858E9B4B293B9F2CDA5A543BA31EC0F42784BD6BEEE5A`): PGDA Product 90 declares the large-area DEM family `MOON_ME` / JPL DE421, while embedded WKT reports IAU:30135 / Moon (2015) Sphere Ocentric (underlying datum IAU:30100). This discrepancy is unresolved; no approved transformation has been identified or applied. M3 must confirm whether the product-page declaration governs this exact file or provide the approved transformation, source, and parameters. After frame confirmation, rerun metrics using `& ".venv\Scripts\python.exe" -c "from scripts.ephemeris.precompute_ephemeris import generate_all_site_window_metrics; generate_all_site_window_metrics()"`. Do not run the script's full `__main__` unless ephemeris kernels are also intended to be rebuilt.
- **M5:** Consume explicit bounds/transform from `data/layers.json`, but treat site alignment as preliminary until the DEM/MOON_ME frame decision is complete. Do not georeference the PIA13523 background by assumption or treat hillshade as solar illumination.
- **M4 (dependent UX):** Coordinate display/disable behavior for unavailable site-derived layers and metrics with M1; do not imply that null site data means zero or safe terrain.

## Remaining manual actions

1. Obtain M2's written decision on how to reconcile the PGDA Product 90 `MOON_ME` / JPL DE421 product statement with the local GeoTIFF's IAU:30135 embedded WKT. If M2 considers them incompatible, obtain the approved transformation and authoritative parameters before transforming or regenerating products.
2. After frame confirmation, regenerate final M2 window metrics and refresh all six M1 fallback scenarios; current generated values are provisional.
3. Confirm local-file checksum against a publisher-provided value if available, plus retrieval date, product version, and redistribution terms. The local SHA-256 is recorded for identification, not source authentication.
4. Perform independent terrain-control-point / known-crater alignment validation.
5. Measure the complete Vercel function bundle and deployment artifact; the terrain-only estimate is not a substitute. Do not call these data scientifically final until the frame question is resolved.

## Git readiness and suggested commands

The M3 changes are available for M1/M2 review. M2 confirmed the project site anchors; scientific sign-off remains blocked on the DEM frame decision. The PR merge conflict is limited to this audit file.

From the isolated worktree after resolving the conflict:

```powershell
git status
git add docs/m3_audit.md
git diff --cached --check
git commit -m "Merge main into feature/m3-terrain and resolve audit conflict" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push origin HEAD:feature/m3-terrain
```

The merge into `feature/m3-terrain` is already pushed. Do not stage or commit the pre-existing `README.md`, `backend/terrain/hazard.py`, or `data/MOON.jpg` changes from the original worktree.
