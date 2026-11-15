import { useEffect, useMemo, useState } from 'react';
import { getLayerImageUrl, getLayers } from '../api/client';
import type { LayersCatalog, Site } from '../api/types';
import ErrorState from '../components/ErrorState';
import Loading from '../components/Loading';
import Unavailable from '../components/Unavailable';

export default function MapConnected({ site }: { site: Site | null }) {
  const [catalog, setCatalog] = useState<LayersCatalog | null>(null);
  const [layer, setLayer] = useState<'elevation' | 'slope' | 'hillshade'>('elevation');
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    let active = true;
    getLayers()
      .then((response) => active && setCatalog(response))
      .catch((reason) => active && setError(reason));
    return () => {
      active = false;
    };
  }, []);

  const tile = useMemo(() => (site ? catalog?.tiles[site.id] ?? null : null), [catalog, site]);
  const marker = site && tile ? projectPoint(site, tile) : null;
  const coordinatesUnavailable = !site || site.lat === null || site.lon === null;

  return (
    <section className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold text-white">Map</h1>
        <p className="mt-1 text-sm text-slate-400">DEM-derived layers and the LROC WAC south-pole background.</p>
      </header>
      {error && <ErrorState error={error} />}
      {!catalog && !error && <Loading label="Loading map catalogue…" />}
      {catalog && (
        <>
          <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-bold text-white">{site?.name ?? 'Selected site'}</h2>
                <p className="mt-1 text-xs text-slate-500">{catalog.site_alignment_status}: {catalog.site_alignment_note}</p>
              </div>
              <select value={layer} onChange={(event) => setLayer(event.target.value as typeof layer)} className="rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-xs text-slate-100">
                <option value="elevation">Elevation · DEM-derived</option>
                <option value="slope">Slope · DEM-derived</option>
                <option value="hillshade">Hillshade · DEM-derived</option>
              </select>
            </div>
            <div className="relative mt-5 overflow-hidden rounded-xl border border-white/10 bg-slate-950">
              {tile ? (
                <img src={getLayerImageUrl(tile.layers[layer].file)} alt={`${layer} DEM-derived layer for ${site?.name ?? 'selected site'}`} className="block h-auto w-full object-contain opacity-75 mix-blend-screen" />
              ) : (
                <div className="flex min-h-64 items-center justify-center">
                  <p className="rounded-lg bg-slate-950/80 p-3 text-xs text-amber-300">DEM-derived layer unavailable for this site.</p>
                </div>
              )}
              {tile && marker && (
                <div
                  className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-cyan-300 shadow-[0_0_16px_rgba(103,232,249,0.9)]"
                  style={{ left: `${marker.x}%`, top: `${marker.y}%` }}
                  title={`${site?.name ?? 'Site'} marker from DEM tile projection metadata`}
                />
              )}
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Marker is projected onto this DEM tile using its projection metadata.
              {coordinatesUnavailable && ' Marker unavailable: site coordinates are unavailable.'}
            </p>
          </section>
          <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
            <h2 className="font-bold text-white">Context image</h2>
            <p className="mt-1 text-xs text-slate-500">LROC WAC south-pole mosaic, Arizona State University.</p>
            <div className="mt-5 overflow-hidden rounded-xl border border-white/10 bg-slate-950">
              <img src="/api/layers/moon_south_pole.png" alt="LROC WAC south-pole context image, Arizona State University" className="block h-auto w-full opacity-70" />
            </div>
            <p className="mt-3 text-xs text-slate-500">Context image, not georeferenced to the DEM tile. No site marker is drawn on this image.</p>
          </section>
          <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 text-xs text-slate-400">
            <h2 className="font-bold uppercase tracking-widest text-slate-300">Projection metadata</h2>
            <p className="mt-2">CRS: {String(catalog.crs.name ?? 'Unavailable')} · {String(catalog.crs.authority ?? 'Unavailable')}</p>
            <p className="mt-1">Marker coordinates: {marker ? `${marker.x.toFixed(2)}%, ${marker.y.toFixed(2)}%` : <Unavailable reason={catalog.site_alignment_note} />}</p>
          </section>
        </>
      )}
    </section>
  );
}

function projectPoint(site: Site, tile: NonNullable<LayersCatalog['tiles'][string]>) {
  if (site.lat === null || site.lon === null) return null;
  const { R_m, k0, lon0_deg } = tile.projection_parameters;
  const { x_left_m, y_top_m } = tile.grid_origin;
  const latitude = (site.lat * Math.PI) / 180;
  const longitude = ((site.lon - lon0_deg) * Math.PI) / 180;
  const rho = 2 * R_m * k0 * Math.tan(Math.PI / 4 + latitude / 2);
  const x = rho * Math.sin(longitude);
  const y = rho * Math.cos(longitude);
  const pixelX = (x - x_left_m) / tile.resolution_m;
  const pixelY = (y_top_m - y) / tile.resolution_m;
  return { x: (pixelX / tile.width_px) * 100, y: (pixelY / tile.height_px) * 100 };
}
