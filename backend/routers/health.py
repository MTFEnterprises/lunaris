"""GET /api/health. Owner: M1."""
from fastapi import APIRouter

import config
from provenance import DataClass, make_provenance
from schemas import Envelope, HealthData

router = APIRouter(prefix="/api", tags=["health"])


def _data_versions() -> dict[str, str | None]:
    d = config.DATA_DIR
    present = lambda ok: "present" if ok else None  # noqa: E731
    return {
        "sites": present((d / "sites.json").is_file()),
        "dem_meta": present((d / "dem_meta.json").is_file()),
        "layers": present((d / "layers.json").is_file()),
        "ephemeris": present(any(d.glob("ephemeris_*"))),
        "window_metrics": present(any(d.glob("window_metrics_*.json"))),
    }


@router.get("/health", response_model=Envelope[HealthData], summary="Service status")
def health() -> Envelope[HealthData]:
    versions = _data_versions()
    status = "healthy" if all(versions.values()) else "degraded"
    warnings = [f"Data file group '{k}' is not present yet." for k, v in versions.items() if v is None]
    return Envelope[HealthData](
        data=HealthData(status=status, version=config.APP_VERSION, data_versions=versions),
        provenance=make_provenance(DataClass.CALCULATED),
        warnings=warnings,
    )
