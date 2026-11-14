"""LUNARIS request / response models (F33, data format v2). Owner: M1.

This file is the single source of truth for the API shape:
  * FastAPI builds /openapi.json from it.
  * M4 generates frontend/src/types/api.ts from that openapi.json
    (openapi-typescript), so changing a field here changes the frontend types.
  * Do NOT rename fields or endpoints silently - tell the team (guide, rule 1.2.8).

Layout:
  1. constants (frame, date window)         4. data format v2 (site/horizon/timeseries/metrics)
  2. validated input types (UTC time)        5. request models  (one per endpoint)
  3. envelope  {data, provenance, ...}       6. response `data` models (one per endpoint)

Coordinates: lat -90..90 (south negative), lon -180..180 (east positive).
Time: UTC ISO 8601 `2027-03-14T06:00:00Z`.  `null` = UNAVAILABLE.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from provenance import DISCLAIMER, DataClass, Provenance

# --------------------------------------------------------------------------- #
# 1. Constants (decisions D1, D2 in docs/decisions.md - change them there first)
# --------------------------------------------------------------------------- #
DEFAULT_FRAME = "MOON_ME"  # D1: stays until M2 proves otherwise from official docs
DATE_MIN = datetime(2027, 1, 1, tzinfo=timezone.utc)
START_DATE_MAX = datetime(2027, 12, 31, 23, 59, 59, tzinfo=timezone.utc)  # D2 start dates
DATE_MAX = datetime(2028, 1, 31, 23, 30, tzinfo=timezone.utc)  # D2 ephemeris coverage end
DEFAULT_STEP_MIN = 30
DEFAULT_WINDOW_HOURS = 708  # 29.5 days, one lunar day window
MAX_WINDOW_HOURS = 744  # 31 days


# --------------------------------------------------------------------------- #
# 2. Validated input types
# --------------------------------------------------------------------------- #
def _parse_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(
            f"'{value}' is not ISO 8601. Example: 2027-03-14T06:00:00Z"
        ) from exc
    if dt.tzinfo is None:
        raise ValueError("Time must include a timezone. Use UTC with a trailing 'Z'.")
    return dt.astimezone(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_time(value: str) -> str:
    dt = _parse_utc(value)
    if not (DATE_MIN <= dt <= DATE_MAX):
        raise ValueError(f"Time must be between {_fmt(DATE_MIN)} and {_fmt(DATE_MAX)} (UTC).")
    return _fmt(dt)


def _check_start_date(value: str) -> str:
    dt = _parse_utc(value)
    if not (DATE_MIN <= dt <= START_DATE_MAX):
        raise ValueError(
            f"Start date must be between {_fmt(DATE_MIN)} and {_fmt(START_DATE_MAX)} (UTC)."
        )
    return _fmt(dt)


UtcTime = Annotated[str, AfterValidator(_check_time)]
UtcStartDate = Annotated[str, AfterValidator(_check_start_date)]


# --------------------------------------------------------------------------- #
# 3. Envelope (every success response)
# --------------------------------------------------------------------------- #
T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """{"data": {...}, "provenance": {...}, "warnings": [], "cached": false}"""

    data: T
    provenance: Provenance
    warnings: list[str] = Field(default_factory=list)
    cached: bool = False


# --------------------------------------------------------------------------- #
# 4. Data format v2 (shared contract; frozen)
# --------------------------------------------------------------------------- #
class SiteOut(BaseModel):
    id: str | None = None
    name: str | None = None
    lat: float
    lon: float
    source: str | None = None


class DemMeta(BaseModel):
    name: str
    resolution_m: float
    coverage: str
    retrieved_utc: str


class Horizon(BaseModel):
    # 360 values, index = azimuth degree (0 = North, clockwise), value = horizon
    # elevation in degrees. null = terrain UNAVAILABLE for this point.
    deg: list[float | None] | None = None
    dem: DemMeta | None = None
    approx: bool = False

    @field_validator("deg")
    @classmethod
    def _360(cls, v: list[float | None] | None) -> list[float | None] | None:
        if v is not None and len(v) != 360:
            raise ValueError("horizon.deg must have exactly 360 values (index = azimuth).")
        return v


class Timeseries(BaseModel):
    start_utc: str
    step_min: int = DEFAULT_STEP_MIN
    sun_el: list[float | None] = Field(default_factory=list)
    sun_az: list[float | None] = Field(default_factory=list)
    earth_el: list[float | None] = Field(default_factory=list)
    earth_az: list[float | None] = Field(default_factory=list)
    sun_lit_geom: list[bool | None] = Field(default_factory=list)
    sun_lit_terrain: list[bool | None] = Field(default_factory=list)
    earth_vis_geom: list[bool | None] = Field(default_factory=list)
    earth_vis_terrain: list[bool | None] = Field(default_factory=list)

    @model_validator(mode="after")
    def _equal_lengths(self) -> "Timeseries":
        lengths = {
            name: len(getattr(self, name))
            for name in (
                "sun_el", "sun_az", "earth_el", "earth_az", "sun_lit_geom",
                "sun_lit_terrain", "earth_vis_geom", "earth_vis_terrain",
            )
            if getattr(self, name)
        }
        if len(set(lengths.values())) > 1:
            raise ValueError(f"Timeseries arrays must have equal length, got {lengths}.")
        return self


class Metrics(BaseModel):
    sunlit_geom_pct: float | None = None
    sunlit_terrain_pct: float | None = None
    earth_geom_pct: float | None = None
    earth_terrain_pct: float | None = None
    longest_dark_h: float | None = None
    longest_comms_gap_h: float | None = None
    max_sun_el_deg: float | None = None


class ScenarioData(BaseModel):
    """Data format v2. `provenance` lives in the envelope, not here."""

    site: SiteOut
    frame: str = DEFAULT_FRAME
    horizon: Horizon | None = None
    timeseries: Timeseries | None = None
    metrics: Metrics | None = None


# --------------------------------------------------------------------------- #
# 5. Requests
# --------------------------------------------------------------------------- #
class RequestModel(BaseModel):
    # Unknown fields (typos like "latitude") are a 400, not silently ignored.
    model_config = ConfigDict(extra="forbid")


class SiteRef(RequestModel):
    """A place: EITHER `site_id` OR (`lat` and `lon`)."""

    site_id: str | None = Field(default=None, min_length=1, max_length=64)
    lat: float | None = Field(default=None, ge=-90, le=90, description="South negative.")
    lon: float | None = Field(default=None, ge=-180, le=180, description="East positive.")

    @model_validator(mode="after")
    def _one_way_to_name_a_site(self) -> "SiteRef":
        has_id = self.site_id is not None
        has_lat = self.lat is not None
        has_lon = self.lon is not None
        if has_id and (has_lat or has_lon):
            raise ValueError("Give either site_id or lat+lon, not both.")
        if not has_id and not (has_lat and has_lon):
            raise ValueError("Give either site_id, or both lat and lon.")
        return self


class EphemerisRequest(SiteRef):
    time_utc: UtcTime


class TimeseriesRequest(SiteRef):
    start_utc: UtcTime
    hours: int = Field(default=DEFAULT_WINDOW_HOURS, ge=1, le=MAX_WINDOW_HOURS)
    step_min: int = Field(default=DEFAULT_STEP_MIN, ge=1, le=1440)

    @model_validator(mode="after")
    def _window_inside_ephemeris(self) -> "TimeseriesRequest":
        end = _parse_utc(self.start_utc) + timedelta(hours=self.hours)
        if end > DATE_MAX + timedelta(minutes=self.step_min):
            raise ValueError(
                f"start_utc + hours runs past the ephemeris window end ({_fmt(DATE_MAX)})."
            )
        return self


class IlluminationRequest(TimeseriesRequest):
    pass


class CommunicationRequest(TimeseriesRequest):
    pass


class TimelineRequest(TimeseriesRequest):
    pass


class HorizonRequest(SiteRef):
    pass


class SlopeRequest(SiteRef):
    # PROVISIONAL default - M3 confirms what radius makes sense.
    radius_m: float = Field(default=500.0, gt=0, le=10000)


class ThermalRequest(SiteRef):
    pass


class PanelSpec(BaseModel):
    """Simplified panel (F10). PROVISIONAL field names - M2 confirms."""

    model_config = ConfigDict(extra="forbid")

    area_m2: float = Field(gt=0)
    efficiency: float = Field(gt=0, le=1)
    losses: float = Field(default=0.0, ge=0, lt=1, description="Fraction, 0..1.")
    tilt_deg: float = Field(default=0.0, ge=0, le=180, description="0 = facing straight up.")
    azimuth_deg: float = Field(default=0.0, ge=0, lt=360, description="0 = North, clockwise.")


class PowerRequest(TimeseriesRequest):
    panel: PanelSpec


class ScenarioSpec(TimeseriesRequest):
    label: str | None = Field(default=None, max_length=60)


class DateScanSpec(SiteRef):
    start_dates: list[UtcStartDate] = Field(min_length=1, max_length=366)
    hours: int = Field(default=DEFAULT_WINDOW_HOURS, ge=1, le=MAX_WINDOW_HOURS)


class CompareRequest(RequestModel):
    """mode="scenarios": 1-3 scenarios side by side.
    mode="date_scan": same site, many start dates (date-shift explorer, from
    data/window_metrics_<id>.json)."""

    mode: Literal["scenarios", "date_scan"] = "scenarios"
    scenarios: list[ScenarioSpec] | None = Field(default=None, min_length=1, max_length=3)
    date_scan: DateScanSpec | None = None

    @model_validator(mode="after")
    def _matching_payload(self) -> "CompareRequest":
        if self.mode == "scenarios":
            if self.scenarios is None:
                raise ValueError("mode 'scenarios' needs a 'scenarios' list (1 to 3).")
            if self.date_scan is not None:
                raise ValueError("Remove 'date_scan' when mode is 'scenarios'.")
        else:
            if self.date_scan is None:
                raise ValueError("mode 'date_scan' needs a 'date_scan' object.")
            if self.scenarios is not None:
                raise ValueError("Remove 'scenarios' when mode is 'date_scan'.")
        return self


class Requirement(RequestModel):
    """Basic F26 requirements. Thresholds are percent (sun/earth) or hours (dark)."""

    id: Literal["min_sunlit", "min_earth", "max_dark_hours"]
    threshold: float = Field(ge=0)
    # Which visibility to judge. "terrain" needs a horizon; without one the
    # result is `unknown`, never silently switched to geometric.
    basis: Literal["terrain", "geometric"] = "terrain"

    @model_validator(mode="after")
    def _percent_range(self) -> "Requirement":
        if self.id in ("min_sunlit", "min_earth") and self.threshold > 100:
            raise ValueError("Percent thresholds must be 0..100.")
        return self


class AssessmentRequest(RequestModel):
    scenario: ScenarioSpec
    requirements: list[Requirement] = Field(min_length=1, max_length=20)


class ReportRequest(RequestModel):
    scenario: ScenarioSpec
    requirements: list[Requirement] | None = Field(default=None, max_length=20)


# --------------------------------------------------------------------------- #
# 6. Response `data` models (goes inside Envelope[...])
# --------------------------------------------------------------------------- #
class HealthData(BaseModel):
    status: Literal["healthy", "degraded"] = "healthy"
    project: str = "LUNARIS"
    version: str
    # e.g. {"sites": "...", "ephemeris": null}; null = file not present yet.
    data_versions: dict[str, str | None] = Field(default_factory=dict)
    disclaimer: str = DISCLAIMER


class SiteInfo(BaseModel):
    """One curated site (from M3's data/sites.json). lat/lon null = UNAVAILABLE."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    region: str | None = None
    lat: float | None = None
    lon: float | None = None
    source_url: str | None = None
    cls: DataClass = Field(default=DataClass.PUBLISHED, alias="class")
    notes: str | None = None


class SitesData(BaseModel):
    sites: list[SiteInfo]


class AngleOut(BaseModel):
    el: float
    az: float


class EphemerisData(BaseModel):
    site: SiteOut
    frame: str = DEFAULT_FRAME
    time_utc: str
    sun: AngleOut | None = None
    earth: AngleOut | None = None
    sun_lit_geom: bool | None = None
    earth_vis_geom: bool | None = None
    hours_to_sunset: float | None = None
    hours_to_earthset: float | None = None


class HorizonData(BaseModel):
    site: SiteOut
    frame: str = DEFAULT_FRAME
    horizon: Horizon


class SlopeData(BaseModel):
    """PROVISIONAL shape - M3 confirms SlopeResult fields."""

    site: SiteOut
    radius_m: float
    slope_mean_deg: float | None = None
    slope_max_deg: float | None = None
    roughness_m: float | None = None
    profile: list[dict[str, float | None]] | None = None
    hazard_flags: list[str] | None = None  # preliminary, thresholds documented by M3


class PowerData(BaseModel):
    """PROVISIONAL shape - M2 confirms PowerResult fields."""

    start_utc: str
    step_min: int
    power_w: list[float | None]
    peak_w: float | None = None
    energy_wh: float | None = None


class CompareItem(BaseModel):
    label: str | None = None
    site: SiteOut
    metrics: Metrics | None = None
    horizon_approx: bool = False
    warnings: list[str] = Field(default_factory=list)


class DateScanItem(BaseModel):
    start_utc: str
    metrics: Metrics | None = None


class CompareData(BaseModel):
    mode: Literal["scenarios", "date_scan"]
    items: list[CompareItem] | None = None  # mode = scenarios
    site: SiteOut | None = None  # mode = date_scan
    scan: list[DateScanItem] | None = None  # mode = date_scan


class RequirementResult(BaseModel):
    id: str
    status: Literal["pass", "fail", "unknown"]
    measured: float | None = None
    threshold: float
    unit: str
    basis: Literal["terrain", "geometric"] = "terrain"
    reason: str = ""
    confidence: Literal["high", "medium", "low"] = "low"
    missing_info: list[str] = Field(default_factory=list)
    recommended_investigation: str = ""


class ScoreInfo(BaseModel):
    """Optional ranking score (D3). Primary result is always pass/fail/unknown."""

    value: float | None = None
    formula: str = (
        "score = 0.4*sunlit_terrain_pct + 0.3*earth_terrain_pct "
        "+ 0.3*(100 - min(100, 100*longest_dark_h/max_dark_h)), max_dark_h = 100"
    )
    weights: dict[str, float] = Field(
        default_factory=lambda: {"sunlit_terrain_pct": 0.4, "earth_terrain_pct": 0.3, "dark": 0.3}
    )


class AssessmentData(BaseModel):
    overall: Literal["pass", "fail", "unknown"]
    results: list[RequirementResult]
    score: ScoreInfo | None = None
    disclaimer: str = "Preliminary decision support. Not NASA-approved, not flight-certified."


class ReportData(BaseModel):
    """Everything the report page needs in one JSON (F28). Sections filled in Tier 2."""

    report_id: str
    request_hash: str
    app_version: str
    generated_utc: str
    sections: dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = DISCLAIMER
