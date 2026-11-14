"""Site lookup via M3's get_site / get_sites. Owner: M1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from errors import ServiceUnavailable, SiteNotFound
from provenance import DataClass
from schemas import SiteInfo, SiteOut, SiteRef
from services._util import build_model, call_with_retry, get, load


@dataclass
class ResolvedSite:
    site: SiteOut
    site_id: str | None
    lat: float
    lon: float


def site_info(raw: Any) -> SiteInfo:
    cls_raw = get(raw, "class") or get(raw, "cls") or DataClass.PUBLISHED.value
    try:
        cls = DataClass(getattr(cls_raw, "value", cls_raw))
    except ValueError as exc:
        raise ServiceUnavailable(f"Site has an unknown data class '{cls_raw}'.") from exc
    return build_model(
        SiteInfo,
        id=get(raw, "id"),
        name=get(raw, "name"),
        region=get(raw, "region"),
        lat=get(raw, "lat"),
        lon=get(raw, "lon"),
        source_url=get(raw, "source_url") or get(raw, "source"),
        cls=cls,
        notes=get(raw, "notes"),
    )


def list_sites() -> list[SiteInfo]:
    fn = load("terrain.terrain", "get_sites")
    return [site_info(s) for s in (call_with_retry(fn) or [])]


def find_site(site_id: str) -> SiteInfo:
    fn = load("terrain.terrain", "get_site")
    raw = call_with_retry(fn, site_id)
    if raw is None:
        raise SiteNotFound(site_id)
    return site_info(raw)


def resolve_site(ref: SiteRef) -> ResolvedSite:
    """Turn site_id or lat+lon into coordinates (never invents coordinates)."""
    if ref.site_id is not None:
        info = find_site(ref.site_id)
        if info.lat is None or info.lon is None:
            raise ServiceUnavailable(
                f"Coordinates for site '{ref.site_id}' are UNAVAILABLE (no confirmed published source).",
                {"site_id": ref.site_id},
            )
        return ResolvedSite(
            SiteOut(id=info.id, name=info.name, lat=info.lat, lon=info.lon, source=info.source_url),
            info.id,
            info.lat,
            info.lon,
        )
    assert ref.lat is not None and ref.lon is not None  # guaranteed by SiteRef validator
    return ResolvedSite(SiteOut(lat=ref.lat, lon=ref.lon), None, ref.lat, ref.lon)
