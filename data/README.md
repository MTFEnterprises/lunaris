# Data

Precomputed outputs shared between M2, M3, M1, M4, M5. Do not commit raw DEM or SPICE kernel files.

Expected files (filled during the event):

- `sites.json` (M3): site list with published coordinates and source links
- `horizon_<id>.json` (M3): 360 values per site
- `dem_meta.json` (M3): DEM name, resolution, coverage, retrieval time
- `timeseries_<id>.json` (M2): 30 minute series per site
- `window_metrics_<id>.json` (M2): 29.5 day window metrics per start date
- `layers/*.png` and `layers.json` (M3): map layers

Missing data must be shown as `UNAVAILABLE`, never invented.
