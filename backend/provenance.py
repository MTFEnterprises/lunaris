"""LUNARIS data classes and provenance (F31). Owner: M1.

Every API response carries:

    "provenance": {"class": "CALCULATED",
                   "inputs": [{"name": "...", "version": "...", "retrieved_utc": "...", "url": "..."}],
                   "assumptions": ["..."]}

Honesty rules (master guide 1.3):
  * Missing data  -> class UNAVAILABLE + a reason. Never hidden, never guessed.
  * Never invent a version or a retrieval time. If you do not know it, pass None.
  * Fallback / cached demo data must be labelled (source + retrieval time).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

DISCLAIMER = (
    "LUNARIS is an independent student prototype. It is not a NASA product, "
    "NASA has not approved any part of it, and its calculations are preliminary "
    "decision support, not flight-certified."
)


class DataClass(str, Enum):
    OBSERVED = "OBSERVED"          # measured by an instrument
    PUBLISHED = "PUBLISHED"        # taken from a published source (paper / agency page)
    CALCULATED = "CALCULATED"      # computed by our code from sourced inputs
    ESTIMATED = "ESTIMATED"        # simplified model or approximation
    ILLUSTRATIVE = "ILLUSTRATIVE"  # sample / demo data, not real analysis
    UNAVAILABLE = "UNAVAILABLE"    # we do not have it (reason required)


class ProvenanceInput(BaseModel):
    """One data source that fed a result (kernel, DEM, published page...)."""

    name: str
    version: str | None = None
    retrieved_utc: str | None = None
    url: str | None = None


class Provenance(BaseModel):
    # The JSON key is "class" (a Python keyword), so the attribute is `cls`.
    model_config = ConfigDict(populate_by_name=True)

    cls: DataClass = Field(alias="class")
    inputs: list[ProvenanceInput] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    # When this response was produced (UTC). A cached response keeps its ORIGINAL
    # time, so a cached result is never passed off as fresh.
    generated_utc: str | None = None
    # Why a value is UNAVAILABLE (only set when cls == UNAVAILABLE).
    reason: str | None = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def utc_now_iso() -> str:
    """Current time as 2027-03-14T06:00:00Z style string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def source(
    name: str,
    url: str | None = None,
    version: str | None = None,
    retrieved_utc: str | None = None,
) -> ProvenanceInput:
    return ProvenanceInput(name=name, url=url, version=version, retrieved_utc=retrieved_utc)


def make_provenance(
    cls: DataClass,
    inputs: list[ProvenanceInput] | None = None,
    assumptions: list[str] | None = None,
    reason: str | None = None,
) -> Provenance:
    if cls is DataClass.UNAVAILABLE and not reason:
        raise ValueError("UNAVAILABLE provenance needs a reason (honesty rule).")
    return Provenance(
        cls=cls,
        inputs=inputs or [],
        assumptions=assumptions or [],
        generated_utc=utc_now_iso(),
        reason=reason,
    )


def unavailable(reason: str, inputs: list[ProvenanceInput] | None = None) -> Provenance:
    return make_provenance(DataClass.UNAVAILABLE, inputs=inputs, reason=reason)


# Official links from the 13 Nov Resources tab (docs/resources_13nov.md).
# Only names + URLs; version / retrieval date are filled by whoever downloads data.
HORIZONS = source("JPL Horizons System", "https://ssd.jpl.nasa.gov/horizons/")
MOON_TREK = source("NASA Moon Trek", "https://trek.nasa.gov/moon/")
QUICKMAP = source("QuickMap (ASU / LROC, LRO data)", "https://quickmap.lroc.asu.edu/")
CSA_MOON = source(
    "Canadian Space Agency Moon exploration reference",
    "https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/",
)
