"""Glue between the API and M2 (science) / M3 (terrain) functions. Owner: M1.

We only CALL the agreed function contract (master guide Section 5):

  M3  terrain.horizon.get_horizon(lat, lon, site_id)        -> deg[360]|None, dem, approx
  M3  terrain.slope.get_slope(lat, lon, radius_m)           -> slope result
  M3  terrain.hazard.get_hazard(lat, lon)                   -> hazard result (preliminary)
  M2  science.ephemeris.sun_earth_at(lat, lon, time_utc)    -> el/az + countdowns
  M2  science.illumination.compute_timeseries(lat, lon, start_utc, hours, step_min, horizon_deg)
  M2  science.illumination.window_metrics(site_id, start_dates)
  M2  science.power.estimate_power(timeseries, panel)

Result objects may be dicts, dataclasses, pydantic models or plain objects: we read
fields by name. Expected field names are listed next to each function below. If a
module returns None for something, we pass `null` on. We never fill gaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from errors import FeatureNotAvailable, ServiceUnavailable
from provenance import HORIZONS, ProvenanceInput, source
from schemas import (
    AngleOut,
    DateScanItem,
    DateScanSpec,
    DemMeta,
    EphemerisData,
    Horizon,
    Metrics,
    PanelSpec,
    PowerData,
    ScenarioData,
    SiteRef,
    SlopeData,
    Timeseries,
)
from services._util import as_dict, build_model, call_with_retry, get, load, plain
from services.site_service import ResolvedSite, resolve_site

ASSUMPTIONS = [
    "Sun and Earth positions come from precomputed ephemeris vectors (offline); no live SPICE on the server.",
    "Geometric visibility treats the Moon as a sphere; terrain-corrected visibility also uses the DEM horizon.",
    "Earth 'visible' means a geometric communication opportunity only, not a radio link (antenna, power and DSN schedule are separate).",
    "No atmospheric refraction (the Moon has no atmosphere).",
    "Preliminary analysis for planning. Not NASA-approved and not flight-certified.",
]
EPHEMERIS_SOURCE = source(
    "Sun/Earth ephemeris (NAIF SPICE, precomputed offline; cross-check: JPL Horizons)",
    HORIZONS.url,
)
_TERRAIN_FIELDS = ("sun_lit_terrain", "earth_vis_terrain")
_TS_FIELDS = (
    "sun_el", "sun_az", "earth_el", "earth_az",
    "sun_lit_geom", "sun_lit_terrain", "earth_vis_geom", "earth_vis_terrain",
)


@dataclass
class Bundle:
    data: ScenarioData
    raw: Any  # M2's own result, passed on to estimate_power
    terrain_available: bool
    dem: DemMeta | None
    warnings: list[str] = field(default_factory=list)
    inputs: list[ProvenanceInput] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Horizon (M3)
# --------------------------------------------------------------------------- #
def load_horizon(rs: ResolvedSite) -> tuple[Horizon, list[str]]:
    fn = load("terrain.horizon", "get_horizon")
    hz = call_with_retry(fn, rs.lat, rs.lon, rs.site_id)
    deg = plain(get(hz, "deg"))
    dem_raw = get(hz, "dem")
    warnings = [str(w) for w in (get(hz, "warnings") or [])]

    dem = None
    if dem_raw:
        d = as_dict(dem_raw)
        dem = build_model(
            DemMeta,
            name=d.get("name"),
            resolution_m=d.get("resolution_m"),
            coverage=d.get("coverage"),
            retrieved_utc=d.get("retrieved_utc"),
        )
    if deg is not None and dem is None:
        raise ServiceUnavailable(
            "Horizon data came without DEM metadata (name, resolution, coverage, retrieval time). "
            "Every horizon must carry it."
        )
    approx = bool(get(hz, "approx", deg is None)) or deg is None
    horizon = build_model(Horizon, deg=deg, dem=dem, approx=approx)
    if deg is None:
        warnings.append(
            "Terrain-corrected visibility is UNAVAILABLE for this point (no horizon data). "
            "Geometric values only."
        )
    return horizon, warnings


# --------------------------------------------------------------------------- #
# Scenario = horizon (M3) + timeseries (M2)
# --------------------------------------------------------------------------- #
def build_scenario(ref: SiteRef, start_utc: str, hours: int, step_min: int) -> Bundle:
    rs = resolve_site(ref)
    horizon, warnings = load_horizon(rs)

    compute = load("science.illumination", "compute_timeseries")
    raw = call_with_retry(compute, rs.lat, rs.lon, start_utc, hours, step_min, horizon.deg)

    ts_src = get(raw, "timeseries") or raw
    ts_kwargs = {f: plain(get(ts_src, f)) or [] for f in _TS_FIELDS}
    ts = build_model(
        Timeseries,
        start_utc=get(ts_src, "start_utc") or start_utc,
        step_min=get(ts_src, "step_min") or step_min,
        **ts_kwargs,
    )
    m_src = get(raw, "metrics") or raw
    metrics = build_model(Metrics, **{k: plain(get(m_src, k)) for k in Metrics.model_fields})
    warnings += [str(w) for w in (get(raw, "warnings") or [])]

    terrain_available = horizon.deg is not None
    if not terrain_available:
        # Honesty rule: terrain fields are null when there is no horizon, whatever M2 sent.
        n = max((len(getattr(ts, f)) for f in _TS_FIELDS), default=0)
        for f in _TERRAIN_FIELDS:
            setattr(ts, f, [None] * n)
        metrics.sunlit_terrain_pct = None
        metrics.earth_terrain_pct = None

    inputs = [EPHEMERIS_SOURCE]
    if horizon.dem:
        inputs.append(source(horizon.dem.name, retrieved_utc=horizon.dem.retrieved_utc))

    data = ScenarioData(site=rs.site, horizon=horizon, timeseries=ts, metrics=metrics)
    return Bundle(data, raw, terrain_available, horizon.dem, warnings, inputs)


# --------------------------------------------------------------------------- #
# Single instant (M2)  - expected fields on the result:
#   sun_el, sun_az, earth_el, earth_az, sun_lit_geom, earth_vis_geom,
#   hours_to_sunset, hours_to_earthset
# --------------------------------------------------------------------------- #
def instant(ref: SiteRef, time_utc: str) -> EphemerisData:
    rs = resolve_site(ref)
    fn = load("science.ephemeris", "sun_earth_at")
    raw = call_with_retry(fn, rs.lat, rs.lon, time_utc)

    def angle(prefix: str) -> AngleOut | None:
        el, az = plain(get(raw, f"{prefix}_el")), plain(get(raw, f"{prefix}_az"))
        return None if el is None or az is None else AngleOut(el=el, az=az)

    return build_model(
        EphemerisData,
        site=rs.site,
        time_utc=time_utc,
        sun=angle("sun"),
        earth=angle("earth"),
        sun_lit_geom=get(raw, "sun_lit_geom"),
        earth_vis_geom=get(raw, "earth_vis_geom"),
        hours_to_sunset=plain(get(raw, "hours_to_sunset")),
        hours_to_earthset=plain(get(raw, "hours_to_earthset")),
    )


# --------------------------------------------------------------------------- #
# Power (M2)  - expected fields: power_w, peak_w, energy_wh
# --------------------------------------------------------------------------- #
def power(bundle: Bundle, panel: PanelSpec, start_utc: str, step_min: int) -> PowerData:
    fn = load("science.power", "estimate_power")
    raw = call_with_retry(fn, bundle.raw, panel)
    return build_model(
        PowerData,
        start_utc=start_utc,
        step_min=step_min,
        power_w=plain(get(raw, "power_w")) or [],
        peak_w=plain(get(raw, "peak_w")),
        energy_wh=plain(get(raw, "energy_wh")),
    )


# --------------------------------------------------------------------------- #
# Slope + hazard (M3)
#   slope result fields: slope_mean_deg, slope_max_deg, roughness_m, profile
#   hazard result: flags (list of strings)  - preliminary
# --------------------------------------------------------------------------- #
def slope(ref: SiteRef, radius_m: float) -> tuple[SlopeData, list[str]]:
    rs = resolve_site(ref)
    fn = load("terrain.slope", "get_slope")
    raw = call_with_retry(fn, rs.lat, rs.lon, radius_m)
    warnings = [str(w) for w in (get(raw, "warnings") or [])]

    flags = None
    try:
        hz_fn = load("terrain.hazard", "get_hazard")
        hz = call_with_retry(hz_fn, rs.lat, rs.lon)
        flags = [str(f) for f in (plain(get(hz, "flags")) or [])]
        warnings += [str(w) for w in (get(hz, "warnings") or [])]
    except (FeatureNotAvailable, ServiceUnavailable) as exc:
        warnings.append(f"Hazard flags unavailable: {exc.message}")

    data = build_model(
        SlopeData,
        site=rs.site,
        radius_m=radius_m,
        slope_mean_deg=plain(get(raw, "slope_mean_deg")),
        slope_max_deg=plain(get(raw, "slope_max_deg")),
        roughness_m=plain(get(raw, "roughness_m")),
        profile=plain(get(raw, "profile")),
        hazard_flags=flags,
    )
    return data, warnings


# --------------------------------------------------------------------------- #
# Date scan (M2 precomputed window metrics) - per item: start_utc + metrics
# --------------------------------------------------------------------------- #
def date_scan(spec: DateScanSpec):
    rs = resolve_site(spec)
    if rs.site_id is None:
        raise FeatureNotAvailable(
            "Date scan uses precomputed data and works for curated sites only, not custom coordinates."
        )
    fn = load("science.illumination", "window_metrics")
    raw = call_with_retry(fn, rs.site_id, list(spec.start_dates)) or []

    items: list[DateScanItem] = []
    for w in raw:
        m_src = get(w, "metrics") or w
        items.append(
            build_model(
                DateScanItem,
                start_utc=get(w, "start_utc"),
                metrics=build_model(Metrics, **{k: plain(get(m_src, k)) for k in Metrics.model_fields}),
            )
        )
    warnings = []
    if len(items) != len(spec.start_dates):
        warnings.append(
            f"Requested {len(spec.start_dates)} start dates but precomputed data returned {len(items)}."
        )
    if spec.hours != 708:
        warnings.append("Precomputed windows are 29.5 days long; the 'hours' value was ignored.")
    inputs = [source(f"data/window_metrics_{rs.site_id}.json (precomputed offline)")]
    return rs.site, items, warnings, inputs
