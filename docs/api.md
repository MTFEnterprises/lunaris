# LUNARIS API reference

Owner: M1. Generated from the running backend (real responses, long arrays shortened with `...`).

- **Live base URL:** https://lunaris-ecru.vercel.app
- **OpenAPI schema (JSON):** https://lunaris-ecru.vercel.app/api/openapi.json  (NOT `/openapi.json`; only `/api/*` reaches the backend)
- **Interactive docs:** https://lunaris-ecru.vercel.app/api/docs
- **Local:** `cd backend && uvicorn main:app --reload` then http://127.0.0.1:8000/api/docs

> LUNARIS is an independent student prototype. It is not a NASA product and not flight-certified. Results are preliminary decision support.

## Conventions
Latitude -90..90 (south negative). Longitude east-positive. Azimuth 0 = North, clockwise. Times are UTC ISO 8601 (`2027-03-14T06:00:00Z`). Default step 30 min. Frame `MOON_ME`. Valid start dates: 2027-01-01 to 2027-12-31.
A place is either `{"site_id": "..."}` or `{"lat": .., "lon": ..}` (not both). Custom points get geometric Sun/Earth only; terrain fields are `null` + a warning.

## Response envelope
Every success response is:
```json
{"data": {}, "provenance": {"class": "CALCULATED", "inputs": [], "assumptions": [], "generated_utc": "...", "reason": null}, "warnings": [], "cached": false}
```
`provenance.class` is one of OBSERVED, PUBLISHED, CALCULATED, ESTIMATED, ILLUSTRATIVE, UNAVAILABLE. `cached: true` means the same request was answered from cache (original `generated_utc` kept). Fallback answers are labelled in `warnings`.

## Error format
```json
{"error": {"code": "INVALID_COORDINATE", "message": "...", "details": {}}}
```
| HTTP | Meaning | Codes |
|---|---|---|
| 400 | Invalid input | INVALID_REQUEST, INVALID_COORDINATE, INVALID_DATE, EMPTY_SCENARIO |
| 404 | Not found | SITE_NOT_FOUND, NOT_FOUND |
| 501 | Feature not available | FEATURE_NOT_AVAILABLE |
| 503 | Data/service unavailable (after 10 s timeout + 2 retries) | SERVICE_UNAVAILABLE |
| 500 | Unexpected | INTERNAL_ERROR |

## Endpoints

### `GET /api/health`
Service status, data files present, disclaimer.

Response `200`:
```json
{
  "data": {
    "status": "healthy",
    "project": "LUNARIS",
    "version": "1.0.0",
    "data_versions": {
      "sites": "present",
      "dem_meta": "present",
      "layers": "present",
      "ephemeris": "present",
      "window_metrics": "present"
    },
    "disclaimer": "LUNARIS is an independent student prototype. It is not a NASA product, NASA has not approved any part of it, and its calculations are preliminary decision support, not flight-certified."
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [],
    "assumptions": [],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [],
  "cached": false
}
```

### `GET /api/sites`
List of the 6 candidate regions (curated).

Response `200`:
```json
{
  "data": {
    "sites": [
      {
        "id": "shackleton_rim",
        "name": "Shackleton Rim",
        "region": null,
        "lat": -89.9,
        "lon": 0.0,
        "source_url": "https://trek.nasa.gov/",
        "class": "PUBLISHED",
        "notes": null,
        "kind": "candidate_region",
        "height_m": 4200.0
      },
      {
        "id": "malapert_massif",
        "name": "Malapert Massif",
        "region": null,
        "lat": -84.9,
        "lon": 34.5,
        "source_url": "https://trek.nasa.gov/",
        "class": "PUBLISHED",
        "notes": null,
        "kind": "candidate_region",
        "height_m": 5000.0
      },
      {
        "id": "de_gerlache_rim",
        "name": "de Gerlache Rim",
        "region": null,
        "lat": -88.5,
        "lon": -91.0,
        "source_url": "https://trek.nasa.gov/",
        "class": "PUBLISHED",
        "notes": null,
        "kind": "candidate_region",
        "height_m": 3500.0
      },
      {
        "id": "nobile_rim",
        "name": "Nobile Rim",
        "region": null,
        "lat": -85.2,
        "lon": 53.0,
        "source_url": "https://trek.nasa.gov/",
        "class": "PUBLISHED",
        "notes": null,
        "kind": "candidate_region",
        "height_m": 2500.0
      },
      "... (6 items total)"
    ]
  },
  "provenance": {
    "class": "PUBLISHED",
    "inputs": [
      {
        "name": "Shackleton Rim",
        "version": null,
        "retrieved_utc": null,
        "url": "https://trek.nasa.gov/"
      },
      {
        "name": "Malapert Massif",
        "version": null,
        "retrieved_utc": null,
        "url": "https://trek.nasa.gov/"
      },
      {
        "name": "de Gerlache Rim",
        "version": null,
        "retrieved_utc": null,
        "url": "https://trek.nasa.gov/"
      },
      {
        "name": "Nobile Rim",
        "version": null,
        "retrieved_utc": null,
        "url": "https://trek.nasa.gov/"
      },
      "... (6 items total)"
    ],
    "assumptions": [],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "Site 'shackleton_rim': the source link is a general website, not a specific page. Add the exact published page.",
    "Site 'malapert_massif': the source link is a general website, not a specific page. Add the exact published page.",
    "Site 'de_gerlache_rim': the source link is a general website, not a specific page. Add the exact published page.",
    "Site 'nobile_rim': the source link is a general website, not a specific page. Add the exact published page.",
    "... (6 values total)"
  ],
  "cached": false
}
```

### `GET /api/sites/malapert_massif`
One site by id. Unknown id -> 404 SITE_NOT_FOUND.

Response `200`:
```json
{
  "data": {
    "id": "malapert_massif",
    "name": "Malapert Massif",
    "region": null,
    "lat": -84.9,
    "lon": 34.5,
    "source_url": "https://trek.nasa.gov/",
    "class": "PUBLISHED",
    "notes": null,
    "kind": "candidate_region",
    "height_m": 5000.0
  },
  "provenance": {
    "class": "PUBLISHED",
    "inputs": [
      {
        "name": "Malapert Massif",
        "version": null,
        "retrieved_utc": null,
        "url": "https://trek.nasa.gov/"
      }
    ],
    "assumptions": [],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [],
  "cached": false
}
```

### `POST /api/ephemeris`
Sun and Earth at one instant (geometric), with countdowns to sunset/Earthset.

Request:
```json
{
  "site_id": "malapert_massif",
  "time_utc": "2027-03-14T06:00:00Z"
}
```

Response `200`:
```json
{
  "data": {
    "site": {
      "id": "malapert_massif",
      "name": "Malapert Massif",
      "lat": -84.9,
      "lon": 34.5,
      "source": "https://trek.nasa.gov/"
    },
    "frame": "MOON_ME",
    "time_utc": "2027-03-14T06:00:00Z",
    "sun": {
      "el": 0.9778,
      "az": 69.3586
    },
    "earth": {
      "el": 10.1487,
      "az": 320.5039
    },
    "sun_lit_geom": true,
    "earth_vis_geom": true,
    "hours_to_sunset": 294.0,
    "hours_to_earthset": 189.0
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [
      {
        "name": "Sun/Earth ephemeris (NAIF SPICE, precomputed offline; cross-check: JPL Horizons)",
        "version": null,
        "retrieved_utc": null,
        "url": "https://ssd.jpl.nasa.gov/horizons/"
      }
    ],
    "assumptions": [
      "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
      "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
      "Earth 'visible' means a geometric communication opportunity only, not a radio link (antenna, power and DSN schedule are separate).",
      "No atmospheric refraction (the Moon has no atmosphere).",
      "... (5 values total)"
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "Instant values are geometric (sphere). Use the timeline for terrain-corrected visibility."
  ],
  "cached": false
}
```

### `POST /api/illumination`
Sun-only time series (geometric and terrain-corrected).

Request:
```json
{
  "site_id": "malapert_massif",
  "start_utc": "2027-03-14T00:00:00Z",
  "hours": 24
}
```

Response `200`:
```json
{
  "data": {
    "site": {
      "id": "malapert_massif",
      "name": "Malapert Massif",
      "lat": -84.9,
      "lon": 34.5,
      "source": "https://trek.nasa.gov/"
    },
    "frame": "MOON_ME",
    "horizon": {
      "deg": [
        -2.45,
        -2.36,
        -2.18,
        -2.04,
        "... (360 values total)"
      ],
      "dem": {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "resolution_m": 80.0,
        "coverage": "South polar region; projected bounds -304000 to 304000 metres",
        "retrieved_utc": ""
      },
      "approx": false
    },
    "timeseries": {
      "start_utc": "2027-03-14T00:00:00Z",
      "step_min": 30,
      "sun_el": [
        0.7303,
        0.7511,
        0.7719,
        0.7926,
        "... (49 values total)"
      ],
      "sun_az": [
        72.3957,
        72.1426,
        71.8895,
        71.6364,
        "... (49 values total)"
      ],
      "earth_el": [
        10.2333,
        10.2272,
        10.2208,
        10.2144,
        "... (49 values total)"
      ],
      "earth_az": [
        320.3361,
        320.3496,
        320.3632,
        320.3769,
        "... (49 values total)"
      ],
      "sun_lit_geom": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ],
      "sun_lit_terrain": [
        false,
        false,
        false,
        false,
        "... (49 values total)"
      ],
      "earth_vis_geom": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ],
      "earth_vis_terrain": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ]
    },
    "metrics": {
      "sunlit_geom_pct": 100.0,
      "sunlit_terrain_pct": 6.12,
      "earth_geom_pct": 100.0,
      "earth_terrain_pct": 100.0,
      "longest_dark_h": 23.0,
      "longest_comms_gap_h": 0.0,
      "max_sun_el_deg": 1.6863
    }
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [
      {
        "name": "Sun/Earth ephemeris (NAIF SPICE, precomputed offline; cross-check: JPL Horizons)",
        "version": null,
        "retrieved_utc": null,
        "url": "https://ssd.jpl.nasa.gov/horizons/"
      },
      {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "version": null,
        "retrieved_utc": "",
        "url": null
      }
    ],
    "assumptions": [
      "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
      "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
      "Earth 'visible' means a geometric communication opportunity only, not a radio link (antenna, power and DSN schedule are separate).",
      "No atmospheric refraction (the Moon has no atmosphere).",
      "... (5 values total)"
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "DEM retrieval time is missing in the horizon file (M3 must fill it)."
  ],
  "cached": false
}
```

### `POST /api/communication`
Earth-visibility time series. Geometric communication opportunity only, not a radio link claim.

Request:
```json
{
  "site_id": "malapert_massif",
  "start_utc": "2027-03-14T00:00:00Z",
  "hours": 24
}
```

Response `200`:
```json
{
  "data": {
    "site": {
      "id": "malapert_massif",
      "name": "Malapert Massif",
      "lat": -84.9,
      "lon": 34.5,
      "source": "https://trek.nasa.gov/"
    },
    "frame": "MOON_ME",
    "horizon": {
      "deg": [
        -2.45,
        -2.36,
        -2.18,
        -2.04,
        "... (360 values total)"
      ],
      "dem": {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "resolution_m": 80.0,
        "coverage": "South polar region; projected bounds -304000 to 304000 metres",
        "retrieved_utc": ""
      },
      "approx": false
    },
    "timeseries": {
      "start_utc": "2027-03-14T00:00:00Z",
      "step_min": 30,
      "sun_el": [
        0.7303,
        0.7511,
        0.7719,
        0.7926,
        "... (49 values total)"
      ],
      "sun_az": [
        72.3957,
        72.1426,
        71.8895,
        71.6364,
        "... (49 values total)"
      ],
      "earth_el": [
        10.2333,
        10.2272,
        10.2208,
        10.2144,
        "... (49 values total)"
      ],
      "earth_az": [
        320.3361,
        320.3496,
        320.3632,
        320.3769,
        "... (49 values total)"
      ],
      "sun_lit_geom": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ],
      "sun_lit_terrain": [
        false,
        false,
        false,
        false,
        "... (49 values total)"
      ],
      "earth_vis_geom": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ],
      "earth_vis_terrain": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ]
    },
    "metrics": {
      "sunlit_geom_pct": 100.0,
      "sunlit_terrain_pct": 6.12,
      "earth_geom_pct": 100.0,
      "earth_terrain_pct": 100.0,
      "longest_dark_h": 23.0,
      "longest_comms_gap_h": 0.0,
      "max_sun_el_deg": 1.6863
    }
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [
      {
        "name": "Sun/Earth ephemeris (NAIF SPICE, precomputed offline; cross-check: JPL Horizons)",
        "version": null,
        "retrieved_utc": null,
        "url": "https://ssd.jpl.nasa.gov/horizons/"
      },
      {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "version": null,
        "retrieved_utc": "",
        "url": null
      }
    ],
    "assumptions": [
      "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
      "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
      "Earth 'visible' means a geometric communication opportunity only, not a radio link (antenna, power and DSN schedule are separate).",
      "No atmospheric refraction (the Moon has no atmosphere).",
      "... (5 values total)"
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "DEM retrieval time is missing in the horizon file (M3 must fill it)."
  ],
  "cached": false
}
```

### `POST /api/timeline`
Full data format v2 time series (Sun + Earth + horizon + metrics). Used by Sky View and Timeline.

Request:
```json
{
  "site_id": "malapert_massif",
  "start_utc": "2027-03-14T00:00:00Z",
  "hours": 24
}
```

Response `200`:
```json
{
  "data": {
    "site": {
      "id": "malapert_massif",
      "name": "Malapert Massif",
      "lat": -84.9,
      "lon": 34.5,
      "source": "https://trek.nasa.gov/"
    },
    "frame": "MOON_ME",
    "horizon": {
      "deg": [
        -2.45,
        -2.36,
        -2.18,
        -2.04,
        "... (360 values total)"
      ],
      "dem": {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "resolution_m": 80.0,
        "coverage": "South polar region; projected bounds -304000 to 304000 metres",
        "retrieved_utc": ""
      },
      "approx": false
    },
    "timeseries": {
      "start_utc": "2027-03-14T00:00:00Z",
      "step_min": 30,
      "sun_el": [
        0.7303,
        0.7511,
        0.7719,
        0.7926,
        "... (49 values total)"
      ],
      "sun_az": [
        72.3957,
        72.1426,
        71.8895,
        71.6364,
        "... (49 values total)"
      ],
      "earth_el": [
        10.2333,
        10.2272,
        10.2208,
        10.2144,
        "... (49 values total)"
      ],
      "earth_az": [
        320.3361,
        320.3496,
        320.3632,
        320.3769,
        "... (49 values total)"
      ],
      "sun_lit_geom": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ],
      "sun_lit_terrain": [
        false,
        false,
        false,
        false,
        "... (49 values total)"
      ],
      "earth_vis_geom": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ],
      "earth_vis_terrain": [
        true,
        true,
        true,
        true,
        "... (49 values total)"
      ]
    },
    "metrics": {
      "sunlit_geom_pct": 100.0,
      "sunlit_terrain_pct": 6.12,
      "earth_geom_pct": 100.0,
      "earth_terrain_pct": 100.0,
      "longest_dark_h": 23.0,
      "longest_comms_gap_h": 0.0,
      "max_sun_el_deg": 1.6863
    }
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [
      {
        "name": "Sun/Earth ephemeris (NAIF SPICE, precomputed offline; cross-check: JPL Horizons)",
        "version": null,
        "retrieved_utc": null,
        "url": "https://ssd.jpl.nasa.gov/horizons/"
      },
      {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "version": null,
        "retrieved_utc": "",
        "url": null
      }
    ],
    "assumptions": [
      "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
      "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
      "Earth 'visible' means a geometric communication opportunity only, not a radio link (antenna, power and DSN schedule are separate).",
      "No atmospheric refraction (the Moon has no atmosphere).",
      "... (5 values total)"
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "DEM retrieval time is missing in the horizon file (M3 must fill it)."
  ],
  "cached": false
}
```

### `POST /api/power/estimate`
Estimated solar power for a panel (ESTIMATED, simple model).

Request:
```json
{
  "site_id": "malapert_massif",
  "start_utc": "2027-03-14T00:00:00Z",
  "hours": 24,
  "panel": {
    "area_m2": 10,
    "efficiency": 0.28,
    "losses": 0.1,
    "tilt_deg": 0,
    "azimuth_deg": 0
  }
}
```

Response `200`:
```json
{
  "data": {
    "start_utc": "2027-03-14T00:00:00Z",
    "step_min": 30,
    "power_w": [
      0.0,
      0.0,
      0.0,
      0.0,
      "... (49 values total)"
    ],
    "peak_w": 102.175,
    "energy_wh": 151.55
  },
  "provenance": {
    "class": "ESTIMATED",
    "inputs": [
      {
        "name": "Sun/Earth ephemeris (NAIF SPICE, precomputed offline; cross-check: JPL Horizons)",
        "version": null,
        "retrieved_utc": null,
        "url": "https://ssd.jpl.nasa.gov/horizons/"
      },
      {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "version": null,
        "retrieved_utc": "",
        "url": null
      }
    ],
    "assumptions": [
      "Simplified model: P = A * efficiency * I * max(0, cos(theta)) * (1 - losses).",
      "No shadowing by terrain, dust or degradation.",
      "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
      "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
      "... (7 values total)"
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "DEM retrieval time is missing in the horizon file (M3 must fill it)."
  ],
  "cached": false
}
```

### `POST /api/terrain/horizon`
Horizon profile (360 values, index = azimuth) plus DEM metadata.

Request:
```json
{
  "site_id": "malapert_massif"
}
```

Response `200`:
```json
{
  "data": {
    "site": {
      "id": "malapert_massif",
      "name": "Malapert Massif",
      "lat": -84.9,
      "lon": 34.5,
      "source": "https://trek.nasa.gov/"
    },
    "frame": "MOON_ME",
    "horizon": {
      "deg": [
        -2.45,
        -2.36,
        -2.18,
        -2.04,
        "... (360 values total)"
      ],
      "dem": {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "resolution_m": 80.0,
        "coverage": "South polar region; projected bounds -304000 to 304000 metres",
        "retrieved_utc": ""
      },
      "approx": false
    }
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [
      {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "version": null,
        "retrieved_utc": "",
        "url": null
      }
    ],
    "assumptions": [
      "Horizon = highest terrain angle per azimuth, with curvature drop d^2/(2R), R = 1737.4 km."
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "DEM retrieval time is missing in the horizon file (M3 must fill it)."
  ],
  "cached": false
}
```

### `POST /api/terrain/slope`
Slope and hazard summary around the site (preliminary, not certified).

Request:
```json
{
  "site_id": "malapert_massif",
  "radius_m": 500
}
```

Response `200`:
```json
{
  "data": {
    "site": {
      "id": "malapert_massif",
      "name": "Malapert Massif",
      "lat": -84.9,
      "lon": 34.5,
      "source": "https://trek.nasa.gov/"
    },
    "radius_m": 500.0,
    "slope_mean_deg": 6.9,
    "slope_max_deg": 11.4,
    "roughness_m": 7.3,
    "profile": {
      "az_deg": 0.0,
      "step_m": 79.8,
      "sampling": "nearest_pixel",
      "distance_m": [
        -479.0,
        -399.2,
        -319.4,
        -239.5,
        "... (13 values total)"
      ],
      "elevation_m": [
        6391.6,
        6387.7,
        6383.1,
        6380.7,
        "... (13 values total)"
      ]
    },
    "hazard_flags": [
      "UNKNOWN:NO_LIMITS"
    ]
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [],
    "assumptions": [
      "Hazard flags are preliminary; thresholds are documented by the terrain module."
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "DEM_UNVERIFIED: dem_meta.json is not verified (status is 'PENDING_VERIFICATION'); results assume DEM heights are metres.",
    "DEM_META_INCOMPLETE: retrieved_utc is missing in dem_meta.json."
  ],
  "cached": false
}
```

### `POST /api/compare`
Compare 1 to 3 scenarios, or date_scan over many start dates.

Request:
```json
{
  "mode": "scenarios",
  "scenarios": [
    {
      "site_id": "malapert_massif",
      "start_utc": "2027-03-14T00:00:00Z",
      "hours": 24,
      "label": "A"
    },
    {
      "site_id": "shackleton_rim",
      "start_utc": "2027-03-14T00:00:00Z",
      "hours": 24,
      "label": "B"
    }
  ]
}
```

Response `200`:
```json
{
  "data": {
    "mode": "scenarios",
    "items": [
      {
        "label": "A",
        "site": {
          "id": "malapert_massif",
          "name": "Malapert Massif",
          "lat": -84.9,
          "lon": 34.5,
          "source": "https://trek.nasa.gov/"
        },
        "metrics": {
          "sunlit_geom_pct": 100.0,
          "sunlit_terrain_pct": 6.12,
          "earth_geom_pct": 100.0,
          "earth_terrain_pct": 100.0,
          "longest_dark_h": 23.0,
          "longest_comms_gap_h": 0.0,
          "max_sun_el_deg": 1.6863
        },
        "horizon_approx": false,
        "warnings": [
          "DEM retrieval time is missing in the horizon file (M3 must fill it)."
        ]
      },
      {
        "label": "B",
        "site": {
          "id": "shackleton_rim",
          "name": "Shackleton Rim",
          "lat": -89.9,
          "lon": 0.0,
          "source": "https://trek.nasa.gov/"
        },
        "metrics": {
          "sunlit_geom_pct": 0.0,
          "sunlit_terrain_pct": 0.0,
          "earth_geom_pct": 100.0,
          "earth_terrain_pct": 100.0,
          "longest_dark_h": 24.5,
          "longest_comms_gap_h": 0.0,
          "max_sun_el_deg": -0.842
        },
        "horizon_approx": false,
        "warnings": [
          "DEM retrieval time is missing in the horizon file (M3 must fill it)."
        ]
      }
    ],
    "site": null,
    "scan": null
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [
      {
        "name": "Sun/Earth ephemeris (NAIF SPICE, precomputed offline; cross-check: JPL Horizons)",
        "version": null,
        "retrieved_utc": null,
        "url": "https://ssd.jpl.nasa.gov/horizons/"
      },
      {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "version": null,
        "retrieved_utc": "",
        "url": null
      }
    ],
    "assumptions": [
      "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
      "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
      "Earth 'visible' means a geometric communication opportunity only, not a radio link (antenna, power and DSN schedule are separate).",
      "No atmospheric refraction (the Moon has no atmosphere).",
      "... (5 values total)"
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "A: DEM retrieval time is missing in the horizon file (M3 must fill it).",
    "B: DEM retrieval time is missing in the horizon file (M3 must fill it)."
  ],
  "cached": false
}
```

### `POST /api/compare`
Date scan: same site, many start dates (must be T00:00:00Z).

Request:
```json
{
  "mode": "date_scan",
  "date_scan": {
    "site_id": "malapert_massif",
    "start_dates": [
      "2027-03-01T00:00:00Z",
      "2027-03-02T00:00:00Z"
    ],
    "hours": 708
  }
}
```

Response `200`:
```json
{
  "data": {
    "mode": "date_scan",
    "items": null,
    "site": {
      "id": "malapert_massif",
      "name": "Malapert Massif",
      "lat": -84.9,
      "lon": 34.5,
      "source": "https://trek.nasa.gov/"
    },
    "scan": [
      {
        "start_utc": "2027-03-01T00:00:00Z",
        "metrics": {
          "sunlit_geom_pct": 45.59,
          "sunlit_terrain_pct": 37.9,
          "earth_geom_pct": 64.64,
          "earth_terrain_pct": 100.0,
          "longest_dark_h": 335.0,
          "longest_comms_gap_h": 0.0,
          "max_sun_el_deg": 4.0695
        }
      },
      {
        "start_utc": "2027-03-02T00:00:00Z",
        "metrics": {
          "sunlit_geom_pct": 45.59,
          "sunlit_terrain_pct": 37.9,
          "earth_geom_pct": 68.03,
          "earth_terrain_pct": 100.0,
          "longest_dark_h": 311.0,
          "longest_comms_gap_h": 0.0,
          "max_sun_el_deg": 4.0695
        }
      }
    ]
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [
      {
        "name": "data/window_metrics_malapert_massif.json (precomputed offline)",
        "version": null,
        "retrieved_utc": null,
        "url": null
      }
    ],
    "assumptions": [
      "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
      "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
      "Earth 'visible' means a geometric communication opportunity only, not a radio link (antenna, power and DSN schedule are separate).",
      "No atmospheric refraction (the Moon has no atmosphere).",
      "... (5 values total)"
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [],
  "cached": false
}
```

### `POST /api/assessment`
Requirements -> pass / fail / unknown. Never pass when data is missing.

Request:
```json
{
  "scenario": {
    "site_id": "malapert_massif",
    "start_utc": "2027-03-14T00:00:00Z",
    "hours": 24
  },
  "requirements": [
    {
      "id": "min_sunlit",
      "threshold": 50,
      "basis": "terrain"
    },
    {
      "id": "min_earth",
      "threshold": 30,
      "basis": "terrain"
    },
    {
      "id": "max_dark_hours",
      "threshold": 100,
      "basis": "terrain"
    }
  ]
}
```

Response `200`:
```json
{
  "data": {
    "overall": "fail",
    "results": [
      {
        "id": "min_sunlit",
        "status": "fail",
        "measured": 6.12,
        "threshold": 50.0,
        "unit": "percent",
        "basis": "terrain",
        "reason": "Minimum sunlit time: measured 6.1 percent does not meet the requirement of at least 50 percent (terrain basis).",
        "confidence": "medium",
        "missing_info": [],
        "recommended_investigation": "Try another site or start date (Date-shift explorer) and compare."
      },
      {
        "id": "min_earth",
        "status": "pass",
        "measured": 100.0,
        "threshold": 30.0,
        "unit": "percent",
        "basis": "terrain",
        "reason": "Minimum Earth visibility (geometric communication opportunity): measured 100.0 percent meets the requirement of at least 30 percent (terrain basis).",
        "confidence": "medium",
        "missing_info": [],
        "recommended_investigation": ""
      },
      {
        "id": "max_dark_hours",
        "status": "pass",
        "measured": 23.0,
        "threshold": 100.0,
        "unit": "hours",
        "basis": "terrain",
        "reason": "Maximum continuous darkness: measured 23.0 hours meets the requirement of at most 100 hours (terrain basis).",
        "confidence": "medium",
        "missing_info": [],
        "recommended_investigation": ""
      }
    ],
    "score": {
      "value": 55.5,
      "formula": "score = 0.4*sunlit_terrain_pct + 0.3*earth_terrain_pct + 0.3*(100 - min(100, 100*longest_dark_h/max_dark_h)), max_dark_h = 100",
      "weights": {
        "sunlit_terrain_pct": 0.4,
        "earth_terrain_pct": 0.3,
        "dark": 0.3
      }
    },
    "disclaimer": "Preliminary decision support. Not NASA-approved, not flight-certified."
  },
  "provenance": {
    "class": "CALCULATED",
    "inputs": [
      {
        "name": "Sun/Earth ephemeris (NAIF SPICE, precomputed offline; cross-check: JPL Horizons)",
        "version": null,
        "retrieved_utc": null,
        "url": "https://ssd.jpl.nasa.gov/horizons/"
      },
      {
        "name": "LDEM_80S_80MPP_ADJ.TIF",
        "version": null,
        "retrieved_utc": "",
        "url": null
      }
    ],
    "assumptions": [
      "Each requirement compares a computed metric with your threshold (>= or <=).",
      "Missing data gives 'unknown', never 'pass'.",
      "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
      "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
      "... (7 values total)"
    ],
    "generated_utc": "2026-11-14T17:44:00Z",
    "reason": null
  },
  "warnings": [
    "DEM retrieval time is missing in the horizon file (M3 must fill it)."
  ],
  "cached": false
}
```

### `POST /api/report`
Everything the report page needs in one response.

Request:
```json
{
  "scenario": {
    "site_id": "malapert_massif",
    "start_utc": "2027-03-14T00:00:00Z",
    "hours": 24
  },
  "requirements": [
    {
      "id": "min_sunlit",
      "threshold": 50,
      "basis": "terrain"
    }
  ]
}
```

Response `200`:
```json
{
  "data": {
    "report_id": "f6837a001df0",
    "request_hash": "f6837a001df05be6419a9c3daca06224215092641d22b6beceece951e5412757",
    "app_version": "1.0.0",
    "generated_utc": "2026-11-14T17:44:00Z",
    "sections": {
      "scenario": {
        "site": {
          "id": "malapert_massif",
          "name": "Malapert Massif",
          "lat": -84.9,
          "lon": 34.5,
          "source": "https://trek.nasa.gov/"
        },
        "frame": "MOON_ME",
        "horizon": {
          "deg": [
            -2.45,
            -2.36,
            -2.18,
            -2.04,
            "... (360 values total)"
          ],
          "dem": {
            "name": "LDEM_80S_80MPP_ADJ.TIF",
            "resolution_m": 80.0,
            "coverage": "South polar region; projected bounds -304000 to 304000 metres",
            "retrieved_utc": ""
          },
          "approx": false
        },
        "timeseries": {
          "start_utc": "2027-03-14T00:00:00Z",
          "step_min": 30,
          "sun_el": [
            0.7303,
            0.7511,
            0.7719,
            0.7926,
            "... (49 values total)"
          ],
          "sun_az": [
            72.3957,
            72.1426,
            71.8895,
            71.6364,
            "... (49 values total)"
          ],
          "earth_el": [
            10.2333,
            10.2272,
            10.2208,
            10.2144,
            "... (49 values total)"
          ],
          "earth_az": [
            320.3361,
            320.3496,
            320.3632,
            320.3769,
            "... (49 values total)"
          ],
          "sun_lit_geom": [
            true,
            true,
            true,
            true,
            "... (49 values total)"
          ],
          "sun_lit_terrain": [
            false,
            false,
            false,
            false,
            "... (49 values total)"
          ],
          "earth_vis_geom": [
            true,
            true,
            true,
            true,
            "... (49 values total)"
          ],
          "earth_vis_terrain": [
            true,
            true,
            true,
            true,
            "... (49 values total)"
          ]
        },
        "metrics": {
          "sunlit_geom_pct": 100.0,
          "sunlit_terrain_pct": 6.12,
          "earth_geom_pct": 100.0,
          "earth_terrain_pct": 100.0,
          "longest_dark_h": 23.0,
          "longest_comms_gap_h": 0.0,
          "max_sun_el_deg": 1.6863
        }
      },
      "terrain": {
        "horizon_available": true,
        "dem": {
          "name": "LDEM_80S_80MPP_ADJ.TIF",
          "resolution_m": 80.0,
          "coverage": "South polar region; projected bounds -304000 to 304000 metres",
          "retrieved_utc": ""
        }
      },
      "assessment": {
        "overall": "fail",
        "results": [
          {
            "id": "min_sunlit",
            "status": "fail",
            "measured": 6.12,
            "threshold": 50.0,
            "unit": "percent",
            "basis": "terrain",
            "reason": "Minimum sunlit time: measured 6.1 percent does not meet the requirement of at least 50 percent (terrain basis).",
            "confidence": "medium",
            "missing_info": [],
            "recommended_investigation": "Try another site or start date (Date-shift explorer) and compare."
          }
        ],
        "score": {
          "value": 55.5,
          "formula": "score = 
```

### `POST /api/thermal/analysis`
Not available (Tier 4). Always 501 + UNAVAILABLE by design.

Request:
```json
{
  "site_id": "malapert_massif"
}
```

Response `501`:
```json
{
  "error": {
    "code": "FEATURE_NOT_AVAILABLE",
    "message": "Thermal analysis is a design note only (Tier 4) and is not implemented.",
    "details": {
      "class": "UNAVAILABLE",
      "reason": "Thermal modelling is out of scope for this prototype."
    }
  }
}
```

## Error examples

**lat 95 -> 400 INVALID_COORDINATE** (got 400)
```json
{
  "error": {
    "code": "INVALID_COORDINATE",
    "message": "Invalid coordinate: latitude must be -90..90 (south negative), longitude must be -180..180 (east positive).",
    "details": {
      "errors": [
        {
          "field": "lat",
          "message": "Input should be less than or equal to 90",
          "type": "less_than_equal"
        }
      ]
    }
  }
}
```

**bad date -> 400 INVALID_DATE** (got 400)
```json
{
  "error": {
    "code": "INVALID_DATE",
    "message": "Invalid date: use UTC ISO 8601, e.g. 2027-03-14T06:00:00Z, inside the supported date window.",
    "details": {
      "errors": [
        {
          "field": "start_utc",
          "message": "Value error, 'not-a-date' is not ISO 8601. Example: 2027-03-14T06:00:00Z",
          "type": "value_error"
        }
      ]
    }
  }
}
```

**empty scenarios -> 400 EMPTY_SCENARIO** (got 400)
```json
{
  "error": {
    "code": "EMPTY_SCENARIO",
    "message": "At least one scenario is required (maximum 3).",
    "details": {
      "errors": [
        {
          "field": "scenarios",
          "message": "List should have at least 1 item after validation, not 0",
          "type": "too_short"
        }
      ]
    }
  }
}
```

**unknown site -> 404 SITE_NOT_FOUND** (got 404)
```json
{
  "error": {
    "code": "SITE_NOT_FOUND",
    "message": "Site 'nope' was not found.",
    "details": {
      "site_id": "nope"
    }
  }
}
```
