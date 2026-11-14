# LUNARIS Conventions (single authoritative source)

Owner: M1. Any change must be announced to the whole team and logged in `docs/decisions.md`.

| Item | Decision |
|---|---|
| Latitude | -90 to 90 degrees, south is negative |
| Longitude | East-positive, -180 to 180 degrees |
| Frame | Moon body-fixed, `MOON_ME` (decision D1). M2 must still confirm from official SPICE/LOLA docs that the DEM frame matches, and record the result here |
| Height | Meters above the reference sphere (R = 1737.4 km) |
| Azimuth | 0 = North, 90 = East, clockwise |
| Elevation | Degrees above local horizontal |
| Time | UTC, ISO 8601, for example `2027-03-14T06:00:00Z` |
| Time step | 30 minutes (default) |
| Units | degree, meter, hour, watt, watt-hour |

## Data classes (label every important value)
OBSERVED, PUBLISHED, CALCULATED, ESTIMATED, ILLUSTRATIVE, UNAVAILABLE.

## Error format
```json
{"error": {"code": "INVALID_COORDINATE", "message": "...", "details": {}}}
```
HTTP codes: 400 invalid input, 404 site not found, 501 feature not available yet, 503 data or service unavailable.

## Response envelope
```json
{"data": {}, "provenance": {}, "warnings": [], "cached": false}
```

## Open items (to settle at the Thursday 12 Nov schema meeting)
- Frame choice (MOON_ME vs MOON_PA) and longitude convention check.
- Date window for date-shift: draft is 1 Jan 2027 to 31 Dec 2027. Decide what happens to the last 29 days (window runs into 2028).
- Role of the two scores: date-shift ranking (frontend formula) vs requirements assessment (backend).
- How the DEM and SPICE kernels reach the server (download at build time vs precomputed only).
