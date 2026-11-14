"""Terrain endpoints (M3 behind them). Owner: M1."""
from fastapi import APIRouter

from schemas import Envelope, HorizonData, HorizonRequest, SlopeData, SlopeRequest
from services import envelopes

router = APIRouter(prefix="/api/terrain", tags=["terrain"])


@router.post("/horizon", response_model=Envelope[HorizonData], summary="360-point horizon + DEM meta")
def horizon(req: HorizonRequest):
    return envelopes.horizon(req)


@router.post("/slope", response_model=Envelope[SlopeData], summary="Slope, roughness, profile")
def slope(req: SlopeRequest):
    return envelopes.slope(req)
