"""Builds the final response envelope for each endpoint. Owner: M1.

Routers stay thin: they call one function here. Each function returns an
Envelope with provenance, warnings and (via the cache) the `cached` flag.
"""

from __future__ import annotations

import cache
import fallback.loader as fallback
from assessment import assess
from errors import FeatureNotAvailable, ServiceUnavailable
from provenance import DataClass, make_provenance, unavailable
from report import assemble_report
from schemas import (
    AssessmentRequest,
    CompareData,
    CompareItem,
    CompareRequest,
    EphemerisData,
    EphemerisRequest,
    Envelope,
    HorizonData,
    HorizonRequest,
    PowerData,
    PowerRequest,
    ReportData,
    ReportRequest,
    ScenarioData,
    SlopeData,
    SlopeRequest,
    TimeseriesRequest,
)
from services import scenario_service as sc
from services.scenario_service import ASSUMPTIONS, Bundle


def _dedupe(inputs):
    seen, out = set(), []
    for i in inputs:
        if i.name not in seen:
            seen.add(i.name)
            out.append(i)
    return out


def _scenario_provenance(bundle: Bundle):
    return make_provenance(DataClass.CALCULATED, _dedupe(bundle.inputs), ASSUMPTIONS)


# --------------------------------------------------------------------------- #
# Ephemeris, illumination / communication / timeline, power
# --------------------------------------------------------------------------- #
def ephemeris(req: EphemerisRequest) -> Envelope[EphemerisData]:
    def build():
        data = sc.instant(req, req.time_utc)
        return Envelope[EphemerisData](
            data=data,
            provenance=make_provenance(
                DataClass.CALCULATED, [sc.EPHEMERIS_SOURCE], ASSUMPTIONS
            ),
            warnings=["Instant values are geometric (sphere). Use the timeline for terrain-corrected visibility."],
        )

    return cache.cached_envelope("ephemeris", req, build)


def scenario(endpoint: str, req: TimeseriesRequest) -> Envelope[ScenarioData]:
    """Used by /illumination, /communication, /timeline (same v2 payload)."""

    def build():
        b = sc.build_scenario(req, req.start_utc, req.hours, req.step_min)
        return Envelope[ScenarioData](
            data=b.data, provenance=_scenario_provenance(b), warnings=b.warnings
        )

    try:
        return cache.cached_envelope(endpoint, req, build)
    except ServiceUnavailable:
        fb = fallback.find_scenario(req.site_id, req.start_utc, req.hours)
        if fb is not None:
            return fb
        raise


def power(req: PowerRequest) -> Envelope[PowerData]:
    def build():
        b = sc.build_scenario(req, req.start_utc, req.hours, req.step_min)
        data = sc.power(b, req.panel, req.start_utc, req.step_min)
        return Envelope[PowerData](
            data=data,
            provenance=make_provenance(
                DataClass.ESTIMATED,
                _dedupe(b.inputs),
                ["Simplified model: P = A * efficiency * I * max(0, cos(theta)) * (1 - losses).",
                 "No shadowing by terrain, dust or degradation.", *ASSUMPTIONS],
            ),
            warnings=b.warnings,
        )

    return cache.cached_envelope("power", req, build)


# --------------------------------------------------------------------------- #
# Terrain
# --------------------------------------------------------------------------- #
def horizon(req: HorizonRequest) -> Envelope[HorizonData]:
    def build():
        rs = sc.resolve_site(req)
        hz, warnings = sc.load_horizon(rs)
        if hz.deg is None:
            prov = unavailable(
                "No horizon data for this point.", [sc.source(hz.dem.name)] if hz.dem else None
            )
        else:
            prov = make_provenance(
                DataClass.CALCULATED,
                [sc.source(hz.dem.name, retrieved_utc=hz.dem.retrieved_utc)] if hz.dem else [],
                ["Horizon = highest terrain angle per azimuth, with curvature drop d^2/(2R), R = 1737.4 km."],
            )
        return Envelope[HorizonData](data=HorizonData(site=rs.site, horizon=hz), provenance=prov, warnings=warnings)

    return cache.cached_envelope("terrain_horizon", req, build)


def slope(req: SlopeRequest) -> Envelope[SlopeData]:
    def build():
        data, warnings = sc.slope(req, req.radius_m)
        return Envelope[SlopeData](
            data=data,
            provenance=make_provenance(
                DataClass.CALCULATED, [], ["Hazard flags are preliminary; thresholds are documented by the terrain module."]
            ),
            warnings=warnings,
        )

    return cache.cached_envelope("terrain_slope", req, build)


# --------------------------------------------------------------------------- #
# Compare, assessment, report
# --------------------------------------------------------------------------- #
def compare(req: CompareRequest) -> Envelope[CompareData]:
    def build():
        if req.mode == "scenarios":
            items, inputs = [], []
            for i, s in enumerate(req.scenarios or [], start=1):
                b = sc.build_scenario(s, s.start_utc, s.hours, s.step_min)
                items.append(
                    CompareItem(
                        label=s.label or f"Scenario {i}",
                        site=b.data.site,
                        metrics=b.data.metrics,
                        horizon_approx=not b.terrain_available,
                        warnings=b.warnings,
                    )
                )
                inputs += b.inputs
            return Envelope[CompareData](
                data=CompareData(mode="scenarios", items=items),
                provenance=make_provenance(DataClass.CALCULATED, _dedupe(inputs), ASSUMPTIONS),
                warnings=[f"{it.label}: {w}" for it in items for w in it.warnings],
            )
        site, scan, warnings, inputs = sc.date_scan(req.date_scan)
        return Envelope[CompareData](
            data=CompareData(mode="date_scan", site=site, scan=scan),
            provenance=make_provenance(DataClass.CALCULATED, inputs, ASSUMPTIONS),
            warnings=warnings,
        )

    return cache.cached_envelope("compare", req, build)


def assessment(req: AssessmentRequest) -> Envelope:
    from schemas import AssessmentData

    def build():
        s = req.scenario
        b = sc.build_scenario(s, s.start_utc, s.hours, s.step_min)
        result = assess(req.requirements, b.data.metrics, b.terrain_available, b.dem)
        return Envelope[AssessmentData](
            data=result,
            provenance=make_provenance(
                DataClass.CALCULATED,
                _dedupe(b.inputs),
                ["Each requirement compares a computed metric with your threshold (>= or <=).",
                 "Missing data gives 'unknown', never 'pass'.", *ASSUMPTIONS],
            ),
            warnings=b.warnings,
        )

    return cache.cached_envelope("assessment", req, build)


def report(req: ReportRequest) -> Envelope[ReportData]:
    def build():
        s = req.scenario
        b = sc.build_scenario(s, s.start_utc, s.hours, s.step_min)
        result = (
            assess(req.requirements, b.data.metrics, b.terrain_available, b.dem)
            if req.requirements
            else None
        )
        data = assemble_report(
            request_hash=cache.request_key("report", req),
            scenario=b.data,
            terrain_available=b.terrain_available,
            dem=b.dem,
            assessment=result,
            inputs=_dedupe(b.inputs),
            assumptions=ASSUMPTIONS,
        )
        return Envelope[ReportData](
            data=data,
            provenance=make_provenance(DataClass.CALCULATED, _dedupe(b.inputs), ASSUMPTIONS),
            warnings=b.warnings,
        )

    return cache.cached_envelope("report", req, build)


def thermal_not_available() -> None:
    raise FeatureNotAvailable(
        "Thermal analysis is a design note only (Tier 4) and is not implemented.",
        {"class": "UNAVAILABLE", "reason": "Thermal modelling is out of scope for this prototype."},
    )
