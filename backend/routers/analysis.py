"""Compare, assessment, report, thermal (501). Owner: M1."""
from fastapi import APIRouter

from schemas import (
    AssessmentData,
    AssessmentRequest,
    CompareData,
    CompareRequest,
    Envelope,
    ReportData,
    ReportRequest,
    ThermalRequest,
)
from services import envelopes

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/compare", response_model=Envelope[CompareData], summary="Compare up to 3 scenarios, or date scan")
def compare(req: CompareRequest):
    return envelopes.compare(req)


@router.post("/assessment", response_model=Envelope[AssessmentData], summary="Requirements -> pass/fail/unknown")
def assessment(req: AssessmentRequest):
    return envelopes.assessment(req)


@router.post("/report", response_model=Envelope[ReportData], summary="All data for the report page")
def report(req: ReportRequest):
    return envelopes.report(req)


@router.post("/thermal/analysis", summary="Not available (Tier 4): always 501 + UNAVAILABLE")
def thermal(req: ThermalRequest):
    envelopes.thermal_not_available()
