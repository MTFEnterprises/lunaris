"""LUNARIS FastAPI app. Owner: M1.

Local:   cd backend && uvicorn main:app --reload      (docs at /api/docs)
Vercel:  api/index.py imports `app` from here; /api/* is routed to it.

NOTE: the OpenAPI schema is at /api/openapi.json (not /openapi.json), because on the
one-link Vercel deploy only /api/* reaches the backend. M4 generates types from it.
"""

import pathlib
import sys

_BACKEND_DIR = pathlib.Path(__file__).resolve().parent
for _p in (str(_BACKEND_DIR), str(_BACKEND_DIR.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from errors import register_exception_handlers
from routers import analysis, health, science, sites, terrain

app = FastAPI(
    title="LUNARIS Backend API",
    description=(
        "Lunar Landing Intelligence, Analysis and Mission Planning System. "
        "Independent student prototype. Not a NASA product, not flight-certified."
    ),
    version=config.APP_VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
)

register_exception_handlers(app)

# Production is same-origin (site and /api on one Vercel link), so CORS is only for
# local development (Vite dev server).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (health.router, sites.router, science.router, terrain.router, analysis.router):
    app.include_router(r)
