# F18 — Future Thermal Design Note

## 1. Purpose

This document describes a possible future thermal-awareness capability
for LUNARIS.

F18 is a design and planning task only. It does not implement a thermal
simulation, temperature prediction model, or thermal-control system.

The purpose is to identify useful thermal information for future lunar
south-polar mission planning.

## 2. Motivation

The lunar south-polar environment contains areas with very different
illumination and thermal conditions.

Permanently shadowed regions may remain extremely cold, while illuminated
areas can experience substantially different surface temperatures.

Thermal conditions may affect:

- Landing-site selection.
- Rover and equipment placement.
- Battery and electronics operation.
- Thermal insulation requirements.
- Scientific instrument operation.
- Mission duration and operational planning.

A future LUNARIS thermal feature could help users understand these
environmental constraints.

## 3. Proposed data inputs

A future implementation may use:

| Input | Possible source | Purpose |
|---|---|---|
| Surface temperature maps | LRO Diviner | Understand regional thermal conditions |
| PSR boundaries | NASA LOLA PSR products | Identify permanently shadowed terrain |
| Elevation data | NASA LOLA DEM | Provide terrain context |
| Illumination information | Verified solar illumination datasets or models | Understand sunlight availability |
| Site coordinates | LUNARIS site catalogue | Associate environmental data with sites |

Every dataset must retain its source, version, units, coordinate system,
resolution, coverage, and retrieval date.

## 4. Proposed future capabilities

### 4.1 Temperature visualization

Display published temperature data as an optional map layer.

The layer should:
- Include a temperature legend and units.
- Identify whether values are measured, derived, or modeled.
- Show the source and data date.
- Display missing data transparently.
- Avoid implying that coarse-resolution values describe every small
  terrain feature.

### 4.2 PSR awareness

Display verified PSR boundaries as a separate map layer.

Users should be able to:
- Toggle the PSR layer.
- Inspect whether a site is inside or near a mapped PSR.
- View the source and area threshold used by the PSR product.

A PSR boundary must come from a documented source or validated model.

### 4.3 Thermal planning indicators

A future version could provide preliminary indicators such as:

- Availability of published temperature information.
- Distance to mapped PSRs.
- Availability of verified illumination information.
- Potential thermal-data coverage gaps.

These indicators must not be presented as engineering certification.

## 5. Proposed software architecture

A future implementation could separate thermal functionality into:

1. Data acquisition and provenance.
2. Raster validation and coordinate transformation.
3. Thermal data processing.
4. API response and metadata.
5. Optional frontend map visualization.

Possible future backend module:

backend/thermal/

Possible future map layers:

data/layers/temperature/
data/layers/psr/

These paths are design suggestions only. They do not indicate that these
modules or datasets currently exist.

## 6. Data validation and safety

Before any thermal layer is used:

- Verify source authenticity and version.
- Verify temperature units (Kelvin or Celsius).
- Check the time period represented by the dataset.
- Check spatial resolution and coverage.
- Check coordinate frame and map alignment.
- Preserve no-data values.
- Clearly label modeled or estimated values.
- Do not invent values for missing pixels.

Thermal conclusions should account for uncertainty and limitations in
the source data.

## 7. Current implementation status

| Feature | Status |
|---|---|
| Thermal design documented | PLANNED |
| Diviner research sources identified | DOCUMENTED |
| Temperature raster integrated | NOT IMPLEMENTED |
| Thermal prediction model | NOT IMPLEMENTED |
| Thermal API | NOT IMPLEMENTED |
| Thermal frontend layer | NOT IMPLEMENTED |

## 8. Future development steps

1. Select an appropriate published Diviner dataset.
2. Download and document the original data.
3. Verify its coordinate system, units, resolution, and time coverage.
4. Validate alignment with the LUNARIS south-polar DEM.
5. Design a temperature-layer metadata format.
6. Implement data processing only after validation.
7. Add an optional map layer and clear legend.
8. Test missing-data handling and coordinate alignment.

## 9. Important limitation

F18 is a future design note, not an operational thermal assessment.

LUNARIS must not claim to predict equipment survival, battery life,
surface temperature at an exact landing point, or thermal safety unless
a separately validated model and suitable data are implemented.
