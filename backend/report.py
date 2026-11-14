"""Report data assembly (F28 data). Owner: M1. M5 builds the printable page from this JSON.

Pure function: takes finished pieces, returns ReportData. Anything we do not have in
this version is written as an explicit UNAVAILABLE section (never left out silently).
"""

from __future__ import annotations

from config import APP_VERSION
from provenance import ProvenanceInput, utc_now_iso
from schemas import AssessmentData, DemMeta, ReportData, ScenarioData

LIMITATIONS = [
    "LUNARIS is an independent student prototype. It is not a NASA product and NASA has not approved it.",
    "Results are preliminary analysis, not flight-certified.",
    "'Earth visible' is a geometric communication opportunity, not a verified radio link.",
    "Geometric and terrain-corrected visibility are different results; terrain-corrected needs a DEM horizon.",
    "Power and thermal models are simplified (thermal is not implemented).",
]


def _unavailable(reason: str) -> dict:
    return {"class": "UNAVAILABLE", "reason": reason}


def assemble_report(
    *,
    request_hash: str,
    scenario: ScenarioData,
    terrain_available: bool,
    dem: DemMeta | None,
    assessment: AssessmentData | None,
    inputs: list[ProvenanceInput],
    assumptions: list[str],
) -> ReportData:
    sections = {
        "scenario": scenario.model_dump(mode="json"),
        "terrain": {
            "horizon_available": terrain_available,
            "dem": dem.model_dump(mode="json") if dem else _unavailable("No DEM metadata for this point."),
        },
        "assessment": (
            assessment.model_dump(mode="json")
            if assessment
            else _unavailable("No requirements were supplied.")
        ),
        "hazards": _unavailable("Landing-safety flags are not part of this report version."),
        "power": _unavailable("Power estimate is not included in this report version."),
        "thermal": _unavailable("Thermal analysis is a design note only (Tier 4)."),
        "assumptions": assumptions,
        "sources": [i.model_dump(mode="json") for i in inputs],
        "limitations": LIMITATIONS,
    }
    return ReportData(
        report_id=request_hash[:12],
        request_hash=request_hash,
        app_version=APP_VERSION,
        generated_utc=utc_now_iso(),
        sections=sections,
    )
