# F27 — Future Rover Operations Design Note

## 1. Purpose

This document describes a possible future rover operations-planning
capability for LUNARIS.

F27 is a design and planning task only. It does not implement rover
autonomous navigation, motor control, or real-time rover operations.

The goal is to describe how LUNARIS could support preliminary planning
for rover movement across lunar south-polar terrain.

## 2. Motivation

Lunar south-polar terrain contains slopes, craters, ridges, rough surfaces,
and permanently shadowed regions.

These conditions may affect rover movement, communication, power
availability, and scientific operations.

A future rover-planning feature could help mission planners understand
terrain constraints before selecting a route.

## 3. Proposed data inputs

| Input | Source | Purpose |
|---|---|---|
| Elevation | NASA LOLA DEM | Understand terrain height and shape |
| Slope | M3 terrain analysis | Identify steep terrain |
| Roughness | M3 terrain analysis | Identify potentially difficult terrain |
| PSR boundaries | Published NASA PSR products | Identify permanently shadowed areas |
| Temperature | LRO Diviner datasets | Understand regional thermal conditions |
| Site coordinates | LUNARIS site catalogue | Define starting and destination locations |
| Rover constraints | Mission configuration | Apply rover-specific operating limits |

Every input must include its source, units, coordinate system, resolution,
and limitations.

## 4. Proposed future capabilities

### 4.1 Terrain-aware route planning

A future version could identify possible routes between selected points.

Route planning may consider:
- Maximum permitted slope.
- Surface roughness.
- Missing terrain coverage.
- Known obstacles and crater boundaries.
- Rover turning and movement constraints.

A route should not be labelled safe merely because its elevation and slope
data are available.

### 4.2 Terrain risk visualization

A future map could display:
- Steep-slope areas.
- Rough terrain.
- Areas with missing DEM coverage.
- Published PSR boundaries.
- Areas requiring additional investigation.

Unknown terrain must be shown as unknown, not treated as safe terrain.

### 4.3 Rover operating constraints

Different rover designs have different operating limits.

A future planner could accept configuration values such as:
- Maximum allowable slope.
- Minimum turning radius.
- Rover width and clearance.
- Maximum travel distance.
- Available power and energy budget.
- Communication constraints.

These values must come from a defined rover design or mission
configuration. LUNARIS must not invent universal rover limits.

### 4.4 Route assessment

A future route assessment could report:
- Total route distance.
- Maximum and average slope along the route.
- Terrain coverage completeness.
- Known risk areas.
- Uncertain or unavailable data.
- Reasons for rejecting a route.

All assessments would be preliminary decision-support information.

## 5. Proposed software architecture

A future implementation could be divided into:

1. Terrain data preparation.
2. Rover configuration and constraints.
3. Route generation.
4. Terrain-risk evaluation.
5. Route result and metadata.
6. Optional frontend visualization.

Possible future backend module:

backend/rover/

Possible future API endpoints:

- GET /api/rover/config
- POST /api/rover/plan
- GET /api/rover/plan/{plan_id}

These endpoints are suggestions only and are not implemented.

## 6. Validation and safety requirements

Before a route-planning feature is used:

- Verify all terrain inputs and their coordinate systems.
- Check DEM coverage along the complete route.
- Preserve missing and invalid terrain values.
- Apply rover-specific constraints from documented sources.
- Test route calculations using known terrain examples.
- Clearly report uncertain and unavailable areas.
- Avoid presenting a preliminary route as certified safe.
- Include source information and limitations in every result.

A future system should reject or flag routes that cross unknown terrain
rather than silently assuming that the terrain is traversable.

## 7. Current implementation status

| Feature | Status |
|---|---|
| Rover operations design documented | PLANNED |
| Elevation data available | IMPLEMENTED |
| Slope analysis available | IMPLEMENTED |
| Preliminary terrain hazard analysis | IMPLEMENTED |
| Rover-specific configuration | NOT IMPLEMENTED |
| Rover route planning | NOT IMPLEMENTED |
| Rover navigation or control | NOT IMPLEMENTED |
| Rover frontend interface | NOT IMPLEMENTED |

## 8. Future development steps

1. Select a specific rover design and obtain its operating constraints.
2. Define the route-planning input and output formats.
3. Prepare terrain cost and obstacle layers.
4. Select and test a route-planning algorithm.
5. Add explicit handling of unknown terrain.
6. Validate routes against sample terrain scenarios.
7. Add route visualization to the frontend.
8. Document assumptions, limitations, and safety warnings.

## 9. Important limitation

F27 is a future design note, not a rover navigation system.

LUNARIS must not claim that a proposed route is safe for a real rover
without validated rover specifications, suitable terrain data, and
appropriate engineering testing.
