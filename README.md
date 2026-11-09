# LUNARIS

**Lunar Landing Intelligence, Analysis and Mission Planning System**
*Explore. Compare. Analyze. Plan.*

Built by MTF Science Labs for the NASA International Space Apps Challenge 2026 ("The Next Frontier").

> LUNARIS is an independent student prototype. It is **not** an official NASA product, NASA has not approved any site shown, and calculations are **not** flight-certified.

## Team

| Member | Name | Role | Folder |
|---|---|---|---|
| M1 | Muhammad Taha Faisal | Project Lead, Backend Platform | `backend/`, `docs/` |
| M2 | Muhammad Huzaifa | Science Engine (ephemeris, Sun, Earth, power) | `backend/` (ephemeris, illumination, power, link) |
| M3 | Ahmed Ashfaq | Terrain and Geospatial Data | `backend/` (terrain, horizon, slope, hazard), `data/` |
| M4 | Ahmed Hassan | Frontend Application | `frontend/` |
| M5 | Muhammad Rayan Manzoor | Visualization, Design, Content | `frontend/src/components/` |

## Repo layout

```
backend/     FastAPI app, schemas, errors, provenance, cache, fallback, assessment, tests
frontend/    React + TypeScript + Vite + Tailwind app
data/        precomputed JSON (timeseries, horizon, window_metrics, sites) and map layers
docs/        conventions, decisions, API, methodology, test report, resources
```

## Rules (short version)

1. Branch name: `m<N>-<feature>` (example: `m3-horizon-mask`).
2. Open a Pull Request, M1 reviews, **squash merge** into `main`.
3. `main` must always be deployable.
4. Merge at least twice a day. Last 4 hours: bug fixes only.
5. Do not change `docs/conventions.md` or the data format without telling M1 (everyone depends on them).
6. Never commit secrets, big DEM or kernel files (GitHub limit 100 MB). Commit scripts that download them.
7. Never invent scientific data. If data is missing, show `UNAVAILABLE`.

See `CONTRIBUTING.md` for details.

## Tech stack

Frontend: React, TypeScript, Vite, Tailwind, Recharts, Leaflet, three.js. Backend: Python 3.11, FastAPI, NumPy. Hosting: Vercel (web), Render (API).
