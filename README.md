# LUNARIS

**Lunar Landing Intelligence, Analysis and Mission Planning System**
*Explore. Compare. Analyze. Plan.*

Built by MTF Science Labs for the NASA International Space Apps Challenge 2026 ("The Next Frontier").

**Live App & API:** [https://vercel.app](https://vercel.app)

> LUNARIS is an independent student prototype. It is **not** an official NASA product, NASA has not approved any site shown, and calculations are **not** flight-certified.

## Team

| Member | Name | Role | Branch | Folder |
|---|---|---|---|---|
| M1 | Muhammad Taha Faisal | Project Lead, Backend Platform | `feature/m1-platform` | `backend/`, `docs/`, `scripts/` |
| M2 | Muhammad Huzaifa | Science Engine (ephemeris, Sun, Earth, power) | `feature/m2-science` | `backend/science/` |
| M3 | Ahmad Ashfaq | Terrain and Geospatial Data | `feature/m3-terrain` | `backend/terrain/`, `data/` |
| M4 | Ahmed Hassan | Frontend Application | `feature/m4-frontend` | `frontend/` (`api`, `state`, `pages`) |
| M5 | Muhammad Rayan Manzoor | Visualization, Design, Content | `feature/m5-visuals` | `frontend/src/components/`, `styles/` |

## Repo layout

## Rules (short version)

1. Branch name: `feature/mN-...` (example: `feature/m2-science`). Never push directly to `main`.
2. Open a Pull Request, M1 reviews, **squash merge** into `main`.
3. `main` must always be deployable.
4. Merge at least twice a day. Last 4 hours: bug fixes only.
5. Do not change `docs/conventions.md` or the data format without telling M1 (everyone depends on them).
6. Never commit secrets, big DEM or kernel files (GitHub limit 100 MB). Commit scripts that download them.
7. Never invent scientific data. If data is missing, show `UNAVAILABLE`.

## Tech stack

Frontend: React, TypeScript, Vite, Tailwind, Recharts, Leaflet, three.js. Backend: Python 3.14, FastAPI, NumPy. Hosting: Vercel (Unified Web + Serverless API).