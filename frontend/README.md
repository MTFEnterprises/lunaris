# LUNARIS frontend

The React/Vite application reads mission and terrain results from the same-origin
`/api` backend. It does not contain a second copy of site coordinates or perform
scientific calculations in the browser. NASA/USGS source records and the
backend-provided provenance are shown with the relevant results.

## Local development

Run the backend and frontend in separate terminals:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm ci
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000` by default. To use another
backend, set `LUNARIS_API_PROXY_TARGET` before starting Vite.

## Build and deployment

```powershell
npm run lint
npm run build
```

Vercel builds `frontend/` and routes `/api/*` to the Python function in
`api/index.py`. In production, the frontend uses same-origin `/api` requests;
the Vite development proxy is not used.

Unavailable or unverified science remains labeled as such. DEM-derived map
layers and the NASA context mosaic are distinct: the mosaic is not georeferenced
to the DEM, and terrain alignment remains preliminary until the DEM frame is
approved.
