"""GET /api/sites and /api/sites/{id}. Data comes from M3 (terrain.terrain). Owner: M1."""
from urllib.parse import urlparse

from fastapi import APIRouter

from provenance import DataClass, make_provenance, source
from schemas import Envelope, SiteInfo, SitesData
from services import site_service

router = APIRouter(prefix="/api", tags=["sites"])


@router.get("/sites", response_model=Envelope[SitesData], summary="Curated landing sites")
def list_sites() -> Envelope[SitesData]:
    sites = site_service.list_sites()
    inputs = [source(s.name, url=s.source_url) for s in sites if s.source_url]
    warnings = [
        f"Site '{s.id}': coordinates are UNAVAILABLE (no confirmed published source)."
        for s in sites
        if s.lat is None or s.lon is None
    ]
    warnings += [
        f"Site '{s.id}': the source link is a general website, not a specific page. Add the exact published page."
        for s in sites
        if s.source_url and urlparse(s.source_url).path in ("", "/")
    ]
    return Envelope[SitesData](
        data=SitesData(sites=sites),
        provenance=make_provenance(DataClass.PUBLISHED, inputs),
        warnings=warnings,
    )


@router.get("/sites/{site_id}", response_model=Envelope[SiteInfo], summary="One site")
def get_site(site_id: str) -> Envelope[SiteInfo]:
    info = site_service.find_site(site_id)
    return Envelope[SiteInfo](
        data=info,
        provenance=make_provenance(
            DataClass.PUBLISHED, [source(info.name, url=info.source_url)] if info.source_url else []
        ),
    )
