# M3 Data Sources and Provenance

## 1. Purpose

This document records the external datasets used by M3 (Terrain and
Geospatial Data), how they are processed, and their known limitations.

The project must distinguish published source data from student-generated
derivatives. A processed image or analysis result is not automatically an
official NASA product.

## 1.1 Authoritative reference portals

These are source and cross-check portals supplied for the project. A portal
link alone does not establish a site coordinate, elevation, DEM frame, or
dataset provenance; those claims require an identifiable product or
feature-specific record from the source.

| Portal | Role in LUNARIS | Use in the backend |
|---|---|---|
| https://quickmap.lroc.asu.edu/ | LROC/ASU lunar imagery and topography reference | Cite for terrain review; do not claim a downloaded dataset without product metadata. |
| https://trek.nasa.gov/moon/ | NASA Moon Trek lunar terrain/visualization reference | Cite for site review; do not infer exact point coordinates from the homepage alone. |
| https://ssd.jpl.nasa.gov/horizons/ | JPL Horizons ephemeris reference and cross-check | Cite for M2 ephemeris validation; runtime uses precomputed vectors. |
| https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/ | Canadian Space Agency lunar exploration reference | Cite educational/context material; not a terrain or ephemeris dataset. |

## 2. Main elevation dataset — NASA LOLA

| Field | Value |
|---|---|
| Provider | NASA Goddard Space Flight Center / LOLA |
| Product | LDEM_80S_80MPP_ADJ.TIF |
| Product type | Lunar Digital Elevation Model |
| Format | GeoTIFF |
| Nominal resolution | 80 metres per pixel |
| Coverage | Lunar south polar region, approximately 80°S to the pole |
| Published elevation units | Metres |
| Source file URL | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF |
| NASA product information | https://pgda.gsfc.nasa.gov/products/90 |
| Local source-file size | 189,158,392 bytes (observed; the existing `file_size_mb` is MiB-like and ambiguously named) |
| Retrieval date | Unknown (`retrieved_utc: null`) |
| Product version | Unknown (`product_version: null`) |
| Verification status | VERIFIED for product identity, frame interpretation, and published units; acquisition metadata incomplete |

NASA's LOLA product information identifies LDEM products as surface
elevation maps and lists the 80 m/pixel south-polar product. The published
product page lists this exact filename at approximately 181 MB. It states
that the large-area DEM GeoTIFFs use south-polar stereographic X/Y
coordinates in metres and the `MOON_ME` reference frame of JPL DE421.
M2 subsequently confirmed the local raster's actual frame is `MOON_ME` and
the embedded IAU:30135 datum label is an erroneous/alias descriptor. This
confirmation was reported by the project owner on 2026-11-15; no separate
M2 document or source URL was supplied.

### Local file inspection

The local GeoTIFF was inspected using Rasterio. The observed properties are:

- Dimensions: 7600 × 7600 pixels.
- Pixel resolution: 80 m.
- Projected bounds: -304000 m to +304000 m in X and Y.
- Data type: float32.
- No-data value: NaN.
- Observed elevation range: approximately -7295.52 m to +7026.33 m.
- GeoTIFF CRS reported by the local file: IAU:30135, Moon (2015) Sphere /
  Ocentric / South Polar.
- Embedded CRS WKT identifies the underlying sphere/datum as IAU:30100.
- Band unit metadata: not populated.
- Local-file SHA-256: `82030DCBDD7C4BB0C7D858E9B4B293B9F2CDA5A543BA31EC0F42784BD6BEEE5A`.
- GeoTIFF tags report GMT 6.5.0 / `grdmath` processing; they do not provide
  a retrieval date or product version.

The SHA-256 identifies the local bytes only; it has not been matched against
a checksum published by NASA.

The local project records elevation values in metres based on the published
product description. The original GeoTIFF band unit field was not populated;
the product-level unit is verified, but the missing local band-unit field is
preserved in metadata.

### Coordinate-frame reconciliation

NASA PGDA Product 90 describes the large-area DEM products, including this
filename, as using the `MOON_ME` reference frame of the JPL DE421 ephemeris.
The locally inspected GeoTIFF's embedded WKT instead identifies IAU:30135 /
Moon (2015) Sphere Ocentric (with underlying datum IAU:30100).

PROJ's IAU 2015 CRS registry defines IAU:30135 as Moon (2015) - Sphere /
Ocentric / South Polar, based on the IAU coordinate-system report
(https://raw.githubusercontent.com/OSGeo/PROJ/master/data/sql/iau.sql).
NAIF documents that its IAU/IAG-report `IAU_MOON` realization does not
exactly agree with the DE-421 `MOON_ME` realization; the reported difference
reaches about 0.0051 degrees (approximately 155 m) over 2000-2020
(https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/frames.html and
`kernels/moon_080317.tf`). Therefore the embedded datum label must not be
silently treated as interchangeable with `MOON_ME`.

The reported M2 decision resolves the local product interpretation for this
project: input site coordinates are interpreted in `MOON_ME`, and the raster
grid's numeric south-polar projection parameters are used directly. Those
parameters are radius 1,737,400 m, standard parallel −90°, central meridian
0°, and zero false easting/northing. Terrain code intentionally does not use
the embedded IAU geodetic datum for coordinate conversion. No raster pixels
were spatially transformed. The observed `IAU:30135` WKT and local SHA-256
remain recorded as file properties; the hash has not been matched to a
publisher checksum. This M2 confirmation is an internal project decision,
not independent proof of the local bytes or a publisher-corrected WKT.

The source GeoTIFF remains local and Git-ignored. Retrieval date and product
version remain unknown; those fields are null, and APIs continue to report
the resulting `DEM_META_INCOMPLETE` warning. The shared `docs/conventions.md`
is M1-owned and still contains its earlier pending-M2 text; M1 should update
that convention entry to reflect the reported decision.

## 2.1 Candidate-region coordinates

The six records in `data/sites.json` contain IAU Gazetteer center solution 1
for their corresponding named features. The linked feature pages were
checked and returned HTTP 200 on 2026-11-15. Each page states
planetographic latitude and east-positive longitude in the range -180 to
180 degrees. These are published feature centers, not independently
published Artemis candidate-region centers or selected landing points.
Elevation is `null` because the Gazetteer does not publish an elevation for
these center coordinates; no DEM-sampled height is claimed.

| Site label | Gazetteer feature | Latitude | East longitude | Elevation | Source |
|---|---|---:|---:|---|---|
| Shackleton Rim | Shackleton crater (Feature 5450), center solution 1 | -89.67 | 129.78 | `null` | https://planetarynames.wr.usgs.gov/Feature/5450 |
| Malapert Massif | Mons Malapert (Feature 16338), center solution 1 | -85.98 | -1.67 | `null` | https://planetarynames.wr.usgs.gov/Feature/16338 |
| de Gerlache Rim | de Gerlache crater (Feature 1439), center solution 1 | -88.48 | -88.34 | `null` | https://planetarynames.wr.usgs.gov/Feature/1439 |
| Nobile Rim | Nobile crater (Feature 4321), center solution 1 | -85.28 | 53.27 | `null` | https://planetarynames.wr.usgs.gov/Feature/4321 |
| Haworth | Haworth crater (Feature 14502), center solution 1 | -86.90 | -4.00 | `null` | https://planetarynames.wr.usgs.gov/Feature/14502 |
| Shoemaker | Shoemaker crater (Feature 5494), center solution 1 | -88.14 | 45.91 | `null` | https://planetarynames.wr.usgs.gov/Feature/5494 |

NASA's Artemis III candidate-region announcement includes Malapert Massif:
https://www.nasa.gov/news-release/nasa-identifies-candidate-regions-for-landing-next-americans-on-moon/
This supports choosing the Mons Malapert feature over the separate Malapert
crater, but does not make the Gazetteer center the NASA region center. The
labels Shackleton Rim, de Gerlache Rim, and Nobile Rim similarly do not imply
that these coordinates are points on the crater rims.

The six feature centers all project inside the local 80 m DEM extent and have
non-nodata source pixels under the M2-approved `MOON_ME` interpretation. The
tiles, horizons, and map layers were regenerated using the explicit spherical
projection parameters above. Gazetteer pages do not identify their
coordinate frame; M2 approved interpreting these project anchors in
`MOON_ME`. They remain published crater/feature centers, not Artemis
candidate-polygon centers or landing points.

## 3. Local DEM tiles

The large source DEM is processed offline into smaller site-centred tiles.

Generated files:

- data/dem_tiles/shackleton_rim.npz
- data/dem_tiles/malapert_massif.npz
- data/dem_tiles/de_gerlache_rim.npz
- data/dem_tiles/nobile_rim.npz
- data/dem_tiles/haworth.npz
- data/dem_tiles/shoemaker.npz

Tile properties:

- Nominal resolution: 80 m per pixel.
- Dimensions: 1251 × 1251 pixels per tile.
- Format: compressed NumPy NPZ.
- Elevation array: float values in metres.
- Each tile includes metadata describing its site, grid origin, resolution,
  projection parameters, and source information.

Generation script:

scripts/terrain/make_dem_tiles.py

The original large GeoTIFF is an offline source file and must not be
committed to the repository. Only the lightweight processed tiles and
required metadata should be version-controlled.

## 4. Terrain analysis outputs

M3 uses the local DEM tiles to produce:

- Site elevation and horizon information.
- Terrain slope analysis using the Horn 3 × 3 method.
- Preliminary terrain roughness estimates.
- Preliminary landing hazard classifications.

Relevant implementation files:

- backend/terrain/terrain.py
- backend/terrain/horizon.py
- backend/terrain/slope.py
- backend/terrain/hazard.py

These are project-generated analyses. They are not official NASA landing
safety assessments.

## 5. Map visualization layers

Generated visualization files are stored in data/layers/.

Current outputs include:

- Six elevation PNGs, one per site.
- Six slope PNGs, one per site.
- data/layers.json, containing image dimensions, projected bounds,
  resolution, CRS information, and coordinate conversion metadata.

Generation script:

scripts/terrain/generate_map_layers.py

The elevation and slope PNGs are visualization derivatives generated from
the local DEM tiles. They should not be described as raw NASA raster
products.

A derived hillshade layer has been generated for all six DEM tiles.

The hillshade is calculated from the elevation arrays using terrain
gradients, with an assumed shading azimuth of 315 degrees and altitude
of 45 degrees. It is exported as a grayscale RGBA PNG for visualization.

This hillshade is a terrain visualization derivative only. It does not
represent actual lunar sunlight, solar illumination, or time-dependent
illumination conditions.

No verified solar illumination raster is currently included.

## 6. Published PSR and Diviner research sources

The following sources are relevant to future integration of permanently
shadowed region (PSR) and lunar temperature information.

### NASA LOLA south-polar PSR products

NASA PGDA product page:
https://pgda.gsfc.nasa.gov/products/90

The page lists south-polar PSR products, including a GeoTIFF map and
supporting CSV and shapefile files. These are published source products;
they have not yet been integrated into the LUNARIS map.

### Lunar South Pole Atlas

https://www.lpi.usra.edu/lunar/lunar-south-pole-atlas/

The Lunar and Planetary Institute provides published south-polar maps
showing topography and permanently shadowed regions. It also provides a
near-surface temperature map based on model data and the LRO Diviner
instrument.

### Diviner temperature data

https://www.diviner.ucla.edu/data

The Diviner team provides global and polar temperature maps and links to
the NASA Planetary Data System archive. The archive page identifies
Reduced Data Record Version 3.1.

The published polar-temperature reference is:

Williams, J.-P., Greenhagen, B. T., Paige, D. A., Schorghofer, N.,
Sefton-Nash, E., Hayne, P. O., Lucey, P. G., Siegler, M. A., and Aye,
K.-M. (2019). Seasonal polar temperatures on the Moon. Journal of
Geophysical Research, 124, 2505–2521.

These sources establish that published PSR and temperature information
exists. They do not establish that the corresponding raster data has
already been downloaded, reprojected, or integrated into LUNARIS.

## 7. Limitations and responsible use

- The nominal DEM resolution does not represent every small surface
  feature.
- Missing or invalid DEM pixels must not be estimated silently.
- Slope and roughness outputs are preliminary.
- A derived hillshade is not a solar illumination model.
- Published PSR boundaries and temperature maps must retain their source
  attribution, resolution, coordinate system, and limitations.
- Different datasets must not be overlaid until their coordinate frames
  and map grids have been checked.
- LUNARIS outputs are student-project decision support, not certified
  landing-site assessments or official NASA products.

## 8. Outstanding verification tasks

- [ ] Match the local DEM bytes to a publisher checksum or acquisition record if available, and confirm the retrieval date.
- [ ] Resolve the local GeoTIFF CRS and NASA PGDA reference-frame discrepancy.
- [ ] Record the source product version and complete provenance metadata.
- [x] Generate derived hillshade PNG layers for all six DEM tiles.
- [ ] Obtain and verify an actual solar illumination dataset.
- [ ] Evaluate PSR and Diviner data for future geospatial integration.
- [ ] Record retrieval dates, versions, coordinate systems, and processing
      steps for any additional datasets actually downloaded.

## 9. NASA lunar south-pole map background

- Source: NASA Science Photojournal, "The Lunar South Pole".
- Image identifier: PIA13523.
- Official source: https://science.nasa.gov/photojournal/the-lunar-south-pole/
- Mission: Lunar Reconnaissance Orbiter (LRO).
- Instrument: Wide Angle Camera (WAC).
- Image description: LROC WAC mosaic of the lunar south-pole region.
- Approximate regional width: 600 km.
- Original downloaded file: `data/MOON.jpg`.
- Repository PNG: `data/layers/moon_south_pole.png`.
- PNG dimensions: 1521 x 1521 pixels.
- Processing: JPEG converted to RGBA PNG using Pillow; no reprojection
  or georeferencing has been performed.
- Credit: NASA/GSFC/Arizona State University.

This image is provided as a visual map background only. It must not be
treated as a georeferenced elevation, slope, or solar illumination layer.
Map alignment and geographic bounds must be independently verified
before using it as a geographically accurate overlay.
