"""Sun / Earth / timeline / power endpoints (M2 science behind them). Owner: M1."""
from fastapi import APIRouter

from schemas import (
    CommunicationRequest,
    EphemerisData,
    EphemerisRequest,
    Envelope,
    IlluminationRequest,
    PowerData,
    PowerRequest,
    ScenarioData,
    TimelineRequest,
)
from services import envelopes

router = APIRouter(prefix="/api", tags=["science"])


@router.post("/ephemeris", response_model=Envelope[EphemerisData], summary="Sun/Earth at one time")
def ephemeris(req: EphemerisRequest):
    return envelopes.ephemeris(req)


@router.post("/illumination", response_model=Envelope[ScenarioData], summary="Sun timeseries + metrics")
def illumination(req: IlluminationRequest):
    return envelopes.scenario("illumination", req)


@router.post("/communication", response_model=Envelope[ScenarioData], summary="Earth timeseries + windows")
def communication(req: CommunicationRequest):
    return envelopes.scenario("communication", req)


@router.post("/timeline", response_model=Envelope[ScenarioData], summary="Full schema-v2 timeseries")
def timeline(req: TimelineRequest):
    return envelopes.scenario("timeline", req)


@router.post("/power/estimate", response_model=Envelope[PowerData], summary="Simplified solar power")
def power_estimate(req: PowerRequest):
    return envelopes.power(req)
