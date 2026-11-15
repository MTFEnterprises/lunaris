# Decision Log

Record every shared decision here so all 5 members see the same thing.

| Date | Decision | Why | Decided by |
|---|---|---|---|
| 2026-11-09 | Repo layout: backend/, frontend/, data/, docs/ | Matches team plan | M1 |
| 2026-11-13 | Branch naming `feature/mN-...` (`feature/m1-platform` to `feature/m5-visuals`), squash merge, M1 reviews | Keep main deployable and allow Vercel preview URLs | M1 |
| 2026-11-13 | Single Vercel deployment (`https://lunaris-ecru.vercel.app`) serving `/` and `/api/*` | Same-origin architecture, no CORS issues in production | M1 |
| 2026-11-15 | Use IAU Gazetteer center solution 1 for the six named M3 features; Malapert Massif maps to Mons Malapert (Feature 16338), not Malapert crater (Feature 3603) | Each selected center has a feature-specific Gazetteer record. NASA lists Malapert Massif as an Artemis III candidate region, but the Gazetteer feature center is not asserted to be the candidate-region center or a landing point. DEM product-frame compatibility with `MOON_ME` remains pending M2 confirmation; regenerated site products are preliminary until then. | M3 |
| 2026-11-15 | Confirm the six IAU Gazetteer solution-1 feature centers as the intended project site anchors | This confirms the chosen project anchors only; they are not asserted to be exact Artemis candidate-region centers or landing points. Keep all terrain-dependent outputs preliminary until the `IAU:30135` / `MOON_ME` frame question is resolved. | M2 |
| 2026-11-15 | Interpret the local LOLA raster grid and six approved site anchors in `MOON_ME`; project with the numeric south-polar parameters recorded in `data/dem_meta.json` | The project owner reported M2 approval that the local raster is `MOON_ME` despite the embedded IAU:30135 datum label, and approved regenerating M3 tiles, horizons, and map layers with that interpretation. No transform was applied to raster pixels. Retrieval date, product version, and external M2 evidence remain unavailable. | M2 (reported by project owner) |

## Locked Defaults (Fri 13 Nov — Freeze before H0)
- [x] **D1 (Frame):** `MOON_ME` (Moon body-fixed), pending M2 final check against official SPICE/LOLA docs.
- [x] **D2 (Date Window):** Start dates `2027-01-01` to `2027-12-31` (ephemeris generated through `2028-01-31` to cover the final 29.5-day lunar window).
- [x] **D3 (Score Definitions):** Primary assessment is backend pass/fail/unknown (`POST /api/assessment`). Ranking score is strictly for UI comparison (`lib/score.ts`).
- [x] **D4 (DEM & Kernel Hosting):** Heavy SPICE kernels and LOLA DEM files stay offline on M2/M3 laptops. Only lightweight precomputed JSON/PNG outputs go into `data/`.
- [x] **D5 (Final API & Format v2):** Master API endpoints (Section 4.3) and Schema v2 (Section 4.4) frozen, including `date_scan` mode on `POST /api/compare`.
- [x] **D6 (Component Contracts):** Frontend component props locked in `frontend/src/types/components.ts`.
- [x] **D7 (Cut Order):** `F23 → F22 → F15 → F10 → F04 → F16` (keep basic PDF report `F28`).
- [x] **D8 (Unified Vercel deploy):** Site at `/`, API at `/api/*`, OpenAPI at `/api/openapi.json`, docs at `/api/docs`. Vercel uses `pyproject.toml` `[tool.vercel] entrypoint = "backend.main:app"`. Root Directory = repo root so `data/` is bundled.
- [x] **D9 (layers):** Map layer PNGs in `data/layers/` (described by `data/layers.json`) reach the browser by being served through the function; the current `vercel.json` keeps `data/` in the function bundle, while `public/` has no `layers/` build-copy step. Function bundle size must be checked against the Vercel limit in the official Vercel docs: NOT yet verified.
- [x] **D10 (fallback):** Fallback scenarios are generated from real `/api/timeline` output for all 6 curated sites in `backend/fallback/scenarios/`; every file carries its provenance class and `generated_utc`.
