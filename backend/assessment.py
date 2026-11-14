"""Assessment engine: requirements -> pass / fail / unknown (F26 engine). Owner: M1.

Rules (master guide + M1 PDF):
  * status is ONLY pass, fail or unknown.
  * Missing data (e.g. no terrain horizon) -> `unknown` with a reason. NEVER pass, never guess.
  * terrain basis is never silently replaced by geometric.
  * Always "preliminary decision support, not NASA-approved".

Pure functions: no network, no files. Easy to test.

PROVISIONAL (ask M2): `longest_dark_h` is a single metric. We assume it is the value
for the best available basis. Document the real definition in docs/methodology.md.
PROVISIONAL (ask M3): confidence never reaches "high" until the team agrees a DEM
resolution threshold. terrain+DEM metadata -> "medium"; geometric-only -> "low".
"""

from __future__ import annotations

from schemas import (
    AssessmentData,
    DemMeta,
    Metrics,
    Requirement,
    RequirementResult,
    ScoreInfo,
)

MAX_DARK_H = 100.0  # D3: default max_dark_h for the ranking score

_META = {
    # id: (metric family, unit, comparison, label)
    "min_sunlit": ("sunlit", "percent", ">=", "Minimum sunlit time"),
    "min_earth": ("earth", "percent", ">=", "Minimum Earth visibility (geometric communication opportunity)"),
    "max_dark_hours": ("dark", "hours", "<=", "Maximum continuous darkness"),
}


def _measure(req: Requirement, metrics: Metrics | None, terrain_available: bool):
    """Return (measured, missing_info, reason)."""
    if metrics is None:
        return None, ["metrics"], "No metrics were computed for this scenario."

    family = _META[req.id][0]
    terrain_basis = req.basis == "terrain"

    if terrain_basis and not terrain_available:
        return (
            None,
            ["terrain horizon (DEM) for this point"],
            "Terrain-corrected data is UNAVAILABLE for this point. "
            "Not judged; choose 'geometric' basis or a curated site.",
        )

    if family == "dark":
        value, field = metrics.longest_dark_h, "longest_dark_h"
    else:
        field = f"{family}_{'terrain' if terrain_basis else 'geom'}_pct"
        value = getattr(metrics, field)

    if value is None:
        return None, [field], f"Metric '{field}' is not available."
    return float(value), [], ""


def evaluate(
    req: Requirement,
    metrics: Metrics | None,
    terrain_available: bool,
    dem: DemMeta | None,
) -> RequirementResult:
    _, unit, op, label = _META[req.id]
    measured, missing, reason = _measure(req, metrics, terrain_available)

    if measured is None:
        return RequirementResult(
            id=req.id,
            status="unknown",
            measured=None,
            threshold=req.threshold,
            unit=unit,
            basis=req.basis,
            reason=reason,
            confidence="low",
            missing_info=missing,
            recommended_investigation=(
                "Use a curated site with a precomputed horizon, or evaluate on the "
                "geometric basis (clearly labelled)."
            ),
        )

    ok = measured >= req.threshold if op == ">=" else measured <= req.threshold
    word = "meets" if ok else "does not meet"
    sign = "at least" if op == ">=" else "at most"
    confidence = "medium" if (req.basis == "terrain" and dem is not None) else "low"
    return RequirementResult(
        id=req.id,
        status="pass" if ok else "fail",
        measured=round(measured, 2),
        threshold=req.threshold,
        unit=unit,
        basis=req.basis,
        reason=f"{label}: measured {measured:.1f} {unit} {word} the requirement of {sign} {req.threshold:g} {unit} ({req.basis} basis).",
        confidence=confidence,
        missing_info=[],
        recommended_investigation=(
            "" if ok else "Try another site or start date (Date-shift explorer) and compare."
        ),
    )


def overall_status(results: list[RequirementResult]) -> str:
    if any(r.status == "fail" for r in results):
        return "fail"
    if any(r.status == "unknown" for r in results):
        return "unknown"
    return "pass"


def compute_score(metrics: Metrics | None, terrain_available: bool) -> ScoreInfo:
    """D3 ranking score. Value is None unless every input exists (never guessed)."""
    info = ScoreInfo()
    if (
        metrics is None
        or not terrain_available
        or metrics.sunlit_terrain_pct is None
        or metrics.earth_terrain_pct is None
        or metrics.longest_dark_h is None
    ):
        return info
    dark_part = 100.0 - min(100.0, 100.0 * metrics.longest_dark_h / MAX_DARK_H)
    info.value = round(
        0.4 * metrics.sunlit_terrain_pct + 0.3 * metrics.earth_terrain_pct + 0.3 * dark_part, 1
    )
    return info


def assess(
    requirements: list[Requirement],
    metrics: Metrics | None,
    terrain_available: bool,
    dem: DemMeta | None,
) -> AssessmentData:
    results = [evaluate(r, metrics, terrain_available, dem) for r in requirements]
    return AssessmentData(
        overall=overall_status(results),
        results=results,
        score=compute_score(metrics, terrain_available),
    )
