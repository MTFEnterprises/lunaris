# Frontend

React + TypeScript + Vite + Tailwind. Owners: M4 (app, screens, state) and M5 (components, design).

Planned structure (created during the event):

```
src/api/         typed API client
src/types/       generated from backend /openapi.json
src/state/       scenario state and URL sync
src/pages/       16 screens
src/components/  M5 components (SkyView, Timeline, charts, SiteMap, Globe3D, DataBadge, ReportPage)
src/lib/         score.ts, url.ts
public/data/     static JSON for curated sites (fallback)
```

The website does no scientific calculation. All science runs in Python (M2, M3).
