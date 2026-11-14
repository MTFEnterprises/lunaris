# M3 Terrain and Geospatial Data Audit

**Audit outcome: M3 is not complete.** This audit distinguishes implemented software behavior from verified scientific inputs. Site coordinates and the DEM reference frame remain unresolved, so dependent products are explicitly withheld rather than presented as validated.

## Scope and project responsibilities

The Master Guide assigns M1 the application/API integration, M2 the lunar ephemeris and illumination work, M3 terrain/geospatial data, M4 the interface, and M5 mapping/visualization. This audit changes M3-owned code, data status, and documentation only. Integration expectations requiring another team's changes are recorded as handoffs.

The audit read the Master Guide, M3 requirements, shared conventions and decisions, data-source documentation, thermal research, terrain methods and code, map-layer generation and outputs, DEM metadata and tiles, horizon outputs, and relevant tests. The repository was on `feature/m3-terrain`. Pre-existing changes in `README.md` and `backend/terrain/hazard.py`, and untracked `data/MOON.jpg`, were left untouched.

## Requirement-by-requirement status

| Requirement | Status | Findings |
|---|---|---|
| M3-01 Candidate-site coordinates | **PARTIALLY COMPLETE** | The six site records are explicitly unavailable: no coordinate, elevation, or source URL is treated as verified. Exact authoritative feature-center coordinates and coordinate definitions are still required. |
| M3-02 Frames and conventions | **NEEDS M1/M2 COORDINATION** | Code uses a polar stereographic raster and the documented horizon convention, but the local raster identifies `IAU:30135` / Moon-2015 Sphere Ocentric while the project convention and M2 use `MOON_ME`. No frame conversion or convention change was made. |
| M3-03 DEM provenance and metadata | **PARTIALLY COMPLETE** | Local raster/tile properties were inspected and unknown provenance fields remain unknown. Product/frame identity, retrieval date, product version, and elevation units are not sufficiently established for scientific use. |
| M3-04 Map layers and M5 handoff | **NEEDS M1/M2/M5 COORDINATION** | Layers are generated from the local DEM and are RGBA PNGs. Their pixel-to-geographic inverse transform is now described, but site alignment is pending frame and coordinate confirmation. The background image is not georeferenced. |
| M3-05 Horizon algorithm and outputs | **PARTIALLY COMPLETE** | The algorithm uses 360 clockwise-from-north azimuth bins and lunar curvature correction. Incomplete rays now produce unavailable bins. Existing numeric vectors are preserved as unverified, not served as valid output; regeneration/provenance is still needed. |
| M3-06 Scientific/manual validation | **PARTIALLY COMPLETE** | Synthetic algorithm tests cover relevant code behaviors, including east-facing direction, curvature, nodata/out-of-coverage, and projection round-trip cases. No manual validation against a known real crater or authoritative terrain reference was performed. |
| M3-07 Slope and roughness | **PARTIALLY COMPLETE** | Metric calculations and units are documented, and output is unavailable when DEM metadata is unverified. M1 adapter expectations still assume successful curated-site responses and need coordination. |
| M3-08 PSR and temperature research | **UNAVAILABLE** | LOLA PSR and Diviner material remains research-only; no validated PSR proximity or temperature dataset is integrated. These outputs must not be interpreted as available. |
| F18 thermal design | **COMPLETE (design only)** | Future thermal design is documented; it is not an implemented or validated thermal product. |
| F27 rover-operations design | **COMPLETE (design only)** | Future rover-operations design is documented; it is not an implemented terrain/thermal capability. |

### M3-01: Candidate-site coordinates

`data/sites.json` no longer presents the six coordinates, elevations, or source URLs as verified. This is a conservative status, not a claim that the sites lack known coordinates. Exact coordinates must be confirmed from authoritative, feature-specific sources with the coordinate frame, longitude convention, reference location (for example, rim point versus massif center), and elevation definition stated.

Changing a confirmed coordinate can change the selected DEM tile and pixel, horizon vector, site-centered map layers, and any site-dependent M2 window/illumination metrics. Regenerate and validate those dependent products only after M1/M2 agree on the coordinate definition and frame. Global/Moon-centered ephemeris vectors do not depend on a candidate-site coordinate.

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

The six tile files total 32.18 MiB. The 18 map-layer PNGs total 29.51 MiB, or 61.69 MiB combined before application code and dependencies. A Vercel deployment/package-size check was not run. Deployment configuration should be checked to ensure these static assets are served as assets rather than unintentionally bundled into a serverless function.

### M3-04: Map layers and M5 handoff

The layer references resolve to 18 existing PNG files. They are 1,251 × 1,251 RGBA images. Elevation and hillshade images have no transparent pixels for the checked tiles; slope images have a transparent border around unavailable edge pixels. RGBA mode alone should not be mistaken for meaningful transparency throughout an image.

Layers are derived from the local DEM, but their alignment to the candidate-site coordinates is pending frame/coordinate confirmation. The hillshade is a fixed-azimuth terrain visualization, **not** actual sunlight or solar illumination. The NASA south-pole background image attribution is documented (NASA/JPL, PIA13523; <https://photojournal.jpl.nasa.gov/catalog/PIA13523>), but that image is not georeferenced and must not be assumed to align precisely with the DEM. Layer geographic bounds and the pixel-to-geographic inverse formula are exposed in `data/layers.json`; M5 should not infer bounds from image dimensions.

### M3-05: Horizon algorithm and outputs

`backend/terrain/horizon.py` produces 360 azimuth samples. The curvature correction is applied using the configured lunar radius, observer height is accounted for, and rays use nearest-pixel terrain sampling. If a ray has incomplete coverage, the code now returns null for that azimuth instead of preserving a potentially underestimating maximum from only part of the ray.

The six checked horizon JSON files each retain a 360-value legacy vector under `unverified_output`; the active `deg` field is null and the output is marked `PENDING_VERIFICATION`/approximate. The legacy vectors have not been independently proven scientifically correct. Their generation time and algorithm version are not established. Do not feed `unverified_output` to downstream calculations as a validated horizon. No full regeneration is warranted until sites and frame are confirmed.

### M3-06: Scientific and manual validation

Automated M3 tests passed (commands and totals below). They establish tested software behavior on synthetic fixtures, not scientific agreement with lunar ground truth. No manual known-crater comparison, independent geographic-control-point validation, or expert review was performed. Those remain required before claiming scientific validation.

### M3-07: Slope and roughness

Slope is expressed in degrees; roughness is the RMS elevation residual in meters over the local fitting neighborhood. The API's established field names include mean/max slope and roughness, with a slope profile where available. Coverage is local to the DEM and edge/nodata neighborhoods may be incomplete. These are terrain metrics, not rover traversability classifications.

Slope outputs now remain unavailable when DEM metadata is absent or unverified rather than exposing numerically computed values as trusted measurements. `backend/terrain/hazard.py` had a pre-existing user modification and was not changed during this audit. Its pre-existing API/threshold behavior was not redefined.

### M3-08: PSR and temperature

`docs/research_thermal.md` and `docs/future_thermal.md` describe research and future work. No validated LOLA PSR or Diviner products are integrated into the current terrain API. PSR distance/proximity and temperature outputs are therefore **UNAVAILABLE**, not zero, estimated, or implied by hillshade.

## Confirmed problems and changes made

1. Curated candidate-site positions had no adequate, feature-specific verification. Updated all six site records to unavailable rather than retaining unsupported coordinate/elevation/source claims.
2. DEM frame identity conflicts with the shared `MOON_ME` convention. Documented the evidence and uncertainty; did not silently transform or change frames.
3. Slope metrics could be exposed despite pending DEM provenance/frame verification. They now remain unavailable until the metadata is verified.
4. An incomplete horizon ray could retain a potentially underestimated maximum. It now yields an unavailable bin.
5. Existing horizon vectors lacked established current-algorithm provenance. Preserved them under `unverified_output` and made the active horizon unavailable.
6. Map-layer geographic conversion and alignment limitations were insufficiently explicit. Added inverse-transform metadata and documented pending site alignment and background-image limitations.
7. Added M3 methods/limitations documentation and tests for unverified DEM handling and projection round-trip behavior.

No unrelated files were edited. The pre-existing `README.md`, `backend/terrain/hazard.py`, and untracked `data/MOON.jpg` changes remain untouched.

## Files changed

- `backend/terrain/horizon.py` — unavailable bins for incomplete rays.
- `backend/terrain/test_m3.py` — test incomplete-ray behavior.
- `backend/terrain/slope.py` — gate metrics on verified DEM metadata; inverse projection support.
- `backend/terrain/test_slope.py` — tests for metadata gating and projection round-trip.
- `scripts/terrain/generate_map_layers.py` — emit inverse projection metadata.
- `data/sites.json` — mark unsupported coordinates, elevations, and source URLs unavailable.
- `data/horizon_*.json` (six files) — preserve legacy vectors as unverified and withhold active vectors.
- `data/dem_meta.json` — distinguish observed properties from unverified provenance.
- `data/layers.json` — inverse transformation and pending-alignment status.
- `docs/data_sources.md` — provenance, coordinate, and frame limitations.
- `docs/method.md` — M3 methods and limitations.
- `docs/m3_audit.md` — this audit report.

## Verification actually run

| Check | Result |
|---|---|
| `pytest backend\terrain\test_m3.py backend\terrain\test_slope.py backend\terrain\test_hazard.py -q` | **Passed: 143 passed.** |
| `pytest -q` | **Not fully passing: 229 passed, 4 failed, 1 skipped.** Three ephemeris adapter tests and one slope adapter test in `backend/tests/test_adapters.py` expect HTTP 200 for a curated site. The now-unavailable site coordinates correctly produce 503, so those existing M1 integration expectations need coordination/update; this audit did not edit the M1 test file. |
| Python compilation check on modified Python files | **Passed.** |
| M3-scoped `git diff --check` | **Passed.** |
| Repository-wide `git diff --check` | **Failed on pre-existing trailing whitespace at `backend/terrain/hazard.py:7`**, within the user's pre-existing edit; intentionally left unchanged. |
| JSON validation | **Passed for 9 relevant JSON files.** |
| DEM-tile check | **Passed for all six:** each is 1,251 × 1,251 at 80 m; metadata is consistent. |
| Horizon-file check | **Passed structural check for all six:** each has 360 finite legacy values under `unverified_output`; active `deg` is unavailable. This is not scientific validation of the legacy vectors. |
| Map-layer references and images | **Passed:** all 18 references exist and are 1,251 × 1,251 RGBA PNGs. Transparency is limited as described above. |
| Known-crater/manual alignment validation | **Not performed.** |
| Vercel deployment/package validation | **Not performed.** |

## Uncertainties and authoritative confirmation required

1. Authoritative, feature-specific latitude, longitude, elevation, and coordinate definitions for Shackleton Rim, Malapert Massif, de Gerlache Rim, Nobile Rim, Haworth, and Shoemaker.
2. Whether the exact local DEM product is in a frame compatible with `MOON_ME`, and, if not, the approved transformation and responsible owner.
3. Original DEM retrieval date, product version, declared vertical units/datum, and license/redistribution terms.
4. Independent validation of DEM-to-site alignment and horizon/slope outputs against a known feature or authoritative reference.
5. Horizon artifact generation time/version and a reproducible procedure for regenerating all six site outputs.
6. Deployment behavior for the approximately 61.69 MiB of committed tile and map PNG outputs.

## Required handoffs

- **M1:** Update/agree on the four stale adapter expectations in `backend/tests/test_adapters.py` and the API/UI behavior for unavailable curated sites. Do not restore fabricated coordinates just to satisfy HTTP-200 expectations.
- **M2:** Resolve the raster frame versus `MOON_ME` decision before any frame conversion or site-dependent illumination/window products are regenerated. Confirm which site-dependent M2 artifacts must be recomputed after coordinates are verified.
- **M5:** Consume explicit bounds/transform from `data/layers.json`, but treat site alignment as pending until M1/M2 coordinate and frame decisions are complete. Do not georeference the PIA13523 background by assumption or treat hillshade as solar illumination.
- **M4 (dependent UX):** Coordinate display/disable behavior for unavailable site-derived layers and metrics with M1; do not imply that null site data means zero or safe terrain.

## Remaining manual actions

1. Obtain and record authoritative feature-specific site coordinates and elevation definitions.
2. Get M1/M2 agreement on the coordinate frame and any transformation.
3. Confirm DEM product/version, retrieval provenance, units, and redistribution terms from authoritative product records.
4. After those decisions, regenerate affected tiles/site-centered layers/horizons and site-dependent M2 outputs; validate against independent terrain control points.
5. Update M1 adapter tests/API integration and M5 layer consumption with the owners.
6. Run the Vercel deployment/package check and a manual known-crater/alignment review.
7. Rerun focused and full tests after M1 integration changes. Do not mark M3 complete until the blocked scientific inputs and validations are resolved.

## Git readiness and suggested commands

Changes are **not ready for an uncoordinated integration** because the full suite has four M1 adapter failures and the frame/site decisions remain pending. After reviewing the handoffs and deciding to submit this conservative status update, the exact commands for the current branch are:

```powershell
git add backend/terrain/horizon.py backend/terrain/test_m3.py backend/terrain/slope.py backend/terrain/test_slope.py scripts/terrain/generate_map_layers.py data/sites.json data/horizon_*.json data/dem_meta.json data/layers.json docs/data_sources.md docs/method.md docs/m3_audit.md
git diff --cached --check
git commit -m "m3: mark unverified terrain outputs unavailable" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push -u origin feature/m3-terrain
```

Do not stage or commit the pre-existing `README.md`, `backend/terrain/hazard.py`, or `data/MOON.jpg` changes as part of this M3 update.
