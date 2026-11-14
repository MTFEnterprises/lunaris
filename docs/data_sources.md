# M3 Data Sources and Provenance

## 1. Purpose

This document records the external datasets used by M3 (Terrain and
Geospatial Data), how they are processed, and their known limitations.

The project must distinguish published source data from student-generated
derivatives. A processed image or analysis result is not automatically an
official NASA product.

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
| Verification status | PENDING_VERIFICATION |

NASA's LOLA product information identifies LDEM products as surface
elevation maps and lists the 80 m/pixel south-polar product. The published
product information describes south-polar stereographic X/Y coordinates
in metres.

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
- Band unit metadata: not populated.

The local project records elevation values in metres based on the published
product description. The original GeoTIFF band unit field was not populated,
so this interpretation remains subject to final metadata verification.

### Coordinate-frame verification warning

The current NASA PGDA product page describes its large-area DEM products
using the MOON_ME reference frame of the JPL DE421 ephemeris. The locally
inspected GeoTIFF reports IAU:30135 / MOON_2015_SPHERE_OCENTRIC.

These descriptions must not be assumed to be interchangeable. M2/M3 must
verify the exact downloaded product, its label/metadata, and its coordinate
frame before declaring the project frame fully verified.

Until then, retain the existing project convention and mark this dataset's
frame verification as pending.

The local GeoTIFF reports `IAU:30135` / Moon-2015 Sphere Ocentric. The NASA
PGDA product page identifies the large-area DEM product family as MOON_ME
(JPL DE421). This is an unresolved source-file/product-page discrepancy,
not evidence that the two frames can be interchanged. The source raster
remains local and is ignored by Git; do not generate or publish site-aligned
products until M2/M3 agree on the coordinate-frame handling.

## 2.1 Candidate-region coordinates

The six records in `data/sites.json` are candidate regions, not confirmed
landing points. Their previous numeric coordinates and `height_m` values
were paired only with the generic Moon Trek homepage and had no published
coordinate definition (for example, named-feature center versus a selected
region point). They are therefore now `null`, with `coords_class` set to
`UNAVAILABLE`; no source URL is claimed. This is intentionally not replaced
with crater-center coordinates or guessed values.

| Candidate region | Latitude | Longitude | Elevation | Source / definition |
|---|---:|---:|---:|---|
| Shackleton Rim | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | No authoritative point-specific source recorded |
| Malapert Massif | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | No authoritative point-specific source recorded |
| de Gerlache Rim | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | No authoritative point-specific source recorded |
| Nobile Rim | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | No authoritative point-specific source recorded |
| Haworth | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | No authoritative point-specific source recorded |
| Shoemaker | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | No authoritative point-specific source recorded |

Once an authoritative source and coordinate definition are selected, the
site-specific DEM tiles, horizons, slope/map layers, and any M2 outputs
derived from the sites must be regenerated or revalidated. Obtain M1/M2
agreement before changing the project frame or refreshing shared outputs.

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

- [ ] Confirm the exact source product and retrieval date of the local DEM.
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
