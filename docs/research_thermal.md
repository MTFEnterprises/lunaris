# F17 — Published PSR and Lunar Temperature Research

## 1. Purpose

This document records published research and public datasets related to
permanently shadowed regions (PSRs) and lunar polar temperatures.

F17 is a research and data-source task. Published data availability does
not mean that the data has already been downloaded, processed, or
integrated into LUNARIS.

## 2. Current research status

**Status: PUBLISHED RESEARCH AVAILABLE — NOT YET INTEGRATED**

Publicly available sources include:
- NASA LOLA south-polar PSR products.
- LRO Diviner global and polar temperature maps.
- Lunar and Planetary Institute south-pole atlas maps.

No PSR boundary layer or Diviner temperature raster is currently included
in the LUNARIS map outputs.

## 3. Permanently Shadowed Regions (PSRs)

### NASA LOLA south-polar PSR product

Official source:
https://pgda.gsfc.nasa.gov/products/90

NASA's "A New View of the Lunar South Pole from LOLA" page lists the
following PSR products:

| Product | Description |
|---|---|
| LPSR_80S_20MPP_ADJ.TIF | PSR raster map |
| LPSR_80S_20MPP_ADJ.SHP | PSR polygon shapefile |
| LPSR_80S_20MPP_ADJ.CSV | PSR attribute table |
| LPSR_80S_20MPP_ADJ_1km2.SHP | Shapefile containing PSRs larger than 1 km² |

The full PSR product listing reports 506,349 PSRs. The subset larger than
1 km² contains 1,531 regions.

The raster product has a nominal pixel scale of 20 metres per pixel.
The NASA product page describes its large-area products using south-polar
stereographic X/Y coordinates in metres and the MOON_ME reference frame
of the JPL DE421 ephemeris.

The product page requests citation of:

Barker et al. (2023), Planetary Science Journal, 4, 183.
DOI: https://doi.org/10.3847/PSJ/acf3e1

Data DOI:
https://doi.org/10.60903/gsfcpgda-lola-spole

### Lunar and Planetary Institute atlas

Official source:
https://www.lpi.usra.edu/lunar/lunar-south-pole-atlas/

The atlas provides published south-pole maps showing topography and
permanently shadowed regions. Its 80°S-to-pole map uses LOLA elevation
data and displays PSRs larger than 10 km².

The atlas also provides maps for other south-polar coverage limits and
different data products. The area threshold and source product must be
checked before using a map as a complete PSR inventory.

Reference:

Stopar, J. and Meyer, H. (2019). Topography and Permanently Shaded
Regions (PSRs) of the Moon's South Pole (80°S to Pole).
Lunar and Planetary Institute Regional Planetary Image Facility,
LPI Contribution 2170.

## 4. Diviner lunar polar temperatures

### Official Diviner data source

https://www.diviner.ucla.edu/data

Diviner is the Lunar Reconnaissance Orbiter Lunar Radiometer Experiment.
Its public data page provides links to global and south/north polar
temperature maps and the NASA Planetary Data System archive.

The Diviner data page states that archived Reduced Data Records have
been reprocessed to RDR Version 3.1, including updated frames,
instrument SPICE kernels, activity flags, and quality flags.

The data page recommends the following reference for polar temperature
data:

Williams, J.-P., Greenhagen, B. T., Paige, D. A., Schorghofer, N.,
Sefton-Nash, E., Hayne, P. O., Lucey, P. G., Siegler, M. A., and
Aye, K.-M. (2019). Seasonal polar temperatures on the Moon.
Journal of Geophysical Research: Planets, 124, 2505–2521.

### Lunar South Pole temperature atlas

The Lunar and Planetary Institute provides a map titled:

"Near-Surface Temperatures Modeled for the Moon's South Pole
(85°S to Pole)"

Source:
https://www.lpi.usra.edu/lunar/lunar-south-pole-atlas/

This map is based on modeled temperature data released by Paige et al.
and observations from the LRO Diviner instrument. The map is overlaid
on LOLA-derived hillshaded terrain.

Reference:

Stopar, J. (2019). Near-Surface Temperatures Modeled at the Moon's
South Pole (85°S to Pole). Lunar and Planetary Institute Regional
Planetary Image Facility, LPI Contribution 2216.

Important distinction:
The atlas map is a published model-based temperature visualization.
It must not be described as a direct measurement at every map pixel
without checking the underlying dataset and its methodology.

## 5. Relevance to LUNARIS sites

The published datasets may help assess environmental context around
the project's south-polar sites:

- Shackleton Rim
- Malapert Massif
- de Gerlache Rim
- Nobile Rim
- Haworth
- Shoemaker

Before using any source for a site, verify that its spatial coverage
includes the site and that the coordinate reference system is compatible
with the LUNARIS map.

A source map's visual overlap is not sufficient proof of accurate
geospatial alignment.

## 6. Integration requirements

Before adding PSR or temperature data to LUNARIS:

1. Download the original dataset from its official source.
2. Record the exact product name, version, retrieval date, and citation.
3. Inspect its CRS, coordinate frame, units, resolution, and no-data values.
4. Confirm that its coverage includes the intended LUNARIS sites.
5. Reproject or transform only after checking the source and target frames.
6. Preserve the original source data separately from processed outputs.
7. Validate alignment against known geographic features or control points.
8. Add source attribution and limitations to the map legend and metadata.
9. Do not infer temperatures or PSR boundaries where source data is absent.

NASA PGDA products use the MOON_ME frame of DE421. The existing local
LUNARIS DEM reports IAU:30135 / MOON_2015_SPHERE_OCENTRIC. This difference
must be resolved before combining the datasets.

## 7. Current LUNARIS implementation status

| Item | Status |
|---|---|
| Published PSR research identified | AVAILABLE |
| Published Diviner polar temperature research identified | AVAILABLE |
| Official source links documented | AVAILABLE |
| PSR raster downloaded into LUNARIS | NOT INTEGRATED |
| PSR polygon layer generated | NOT INTEGRATED |
| Diviner temperature raster integrated | NOT INTEGRATED |
| Coordinate-frame compatibility verified | PENDING |
| LUNARIS PSR/temperature map layer | NOT AVAILABLE |

The project must not display fabricated PSR boundaries, temperature values,
or solar illumination information.

## 8. References

1. Barker, M. K. et al. (2023). A New View of the Lunar South Pole
   from LOLA. Planetary Science Journal, 4, 183.
   https://doi.org/10.3847/PSJ/acf3e1

2. Stopar, J. and Meyer, H. (2019). Topography and Permanently Shaded
   Regions (PSRs) of the Moon's South Pole (80°S to Pole).
   LPI Contribution 2170.

3. Stopar, J. (2019). Near-Surface Temperatures Modeled at the Moon's
   South Pole (85°S to Pole). LPI Contribution 2216.

4. Williams, J.-P. et al. (2019). Seasonal polar temperatures on the
   Moon. Journal of Geophysical Research: Planets, 124, 2505–2521.

5. Diviner Data Portal:
   https://www.diviner.ucla.edu/data

6. NASA LOLA South Pole Products:
   https://pgda.gsfc.nasa.gov/products/90
