# Decision Log

Record every shared decision here so all 5 members see the same thing.

| Date | Decision | Why | Decided by |
|---|---|---|---|
| 2026-11-09 | Repo layout: backend/, frontend/, data/, docs/ | Matches team plan | M1 |
| 2026-11-13 | Branch naming `feature/mN-...` (`feature/m1-platform` to `feature/m5-visuals`), squash merge, M1 reviews | Keep main deployable and allow Vercel preview URLs | M1 |
| 2026-11-13 | Single Vercel deployment (`https://vercel.app`) serving `/` and `/api/*` | Same-origin architecture, no CORS issues in production | M1 |
| 2026-11-15 | Use IAU Gazetteer center solution 1 for the six named M3 features; Malapert Massif maps to Mons Malapert (Feature 16338), not Malapert crater (Feature 3603) | Each selected center has a feature-specific Gazetteer record. NASA lists Malapert Massif as an Artemis III candidate region, but the Gazetteer feature center is not asserted to be the candidate-region center or a landing point. DEM product-frame compatibility with `MOON_ME` remains pending M2 confirmation; regenerated site products are preliminary until then. | M3 |

## Locked Defaults (Fri 13 Nov — Freeze before H0)
- [x] **D1 (Frame):** `MOON_ME` (Moon body-fixed), pending M2 final check against official SPICE/LOLA docs.
- [x] **D2 (Date Window):** Start dates `2027-01-01` to `2027-12-31` (ephemeris generated through `2028-01-31` to cover the final 29.5-day lunar window).
- [x] **D3 (Score Definitions):** Primary assessment is backend pass/fail/unknown (`POST /api/assessment`). Ranking score is strictly for UI comparison (`lib/score.ts`).
- [x] **D4 (DEM & Kernel Hosting):** Heavy SPICE kernels and LOLA DEM files stay offline on M2/M3 laptops. Only lightweight precomputed JSON/PNG outputs go into `data/`.
- [x] **D5 (Final API & Format v2):** Master API endpoints (Section 4.3) and Schema v2 (Section 4.4) frozen, including `date_scan` mode on `POST /api/compare`.
- [x] **D6 (Component Contracts):** Frontend component props locked in `frontend/src/types/components.ts`.
- [x] **D7 (Cut Order):** `F23 → F22 → F15 → F10 → F04 → F16` (keep basic PDF report `F28`).
