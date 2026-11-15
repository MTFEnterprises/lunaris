import { useState } from 'react';
import { getLayerImageUrl } from '../api/client';
import type { EphemerisData, Site } from '../api/types';
import Unavailable from './Unavailable';

export default function LunarContext({
  site,
  ephemeris,
}: {
  site: Site | null;
  ephemeris: EphemerisData | null;
}) {
  const sun = ephemeris?.sun;
  const [imageUnavailable, setImageUnavailable] = useState(false);

  return (
    <section className="overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.06] via-slate-950 to-cyan-400/[0.05] p-5 sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-cyan-300">NASA source imagery</p>
          <h2 className="mt-1 text-xl font-extrabold text-white">Lunar south-pole context</h2>
          <p className="mt-1 text-xs text-slate-400">LROC Wide Angle Camera south-pole mosaic, served by the LUNARIS backend.</p>
        </div>
        <a
          href="https://science.nasa.gov/photojournal/the-lunar-south-pole/"
          target="_blank"
          rel="noreferrer"
          className="text-xs text-cyan-300 underline decoration-cyan-300/40 underline-offset-2"
        >
          NASA image source · PIA13523
        </a>
      </div>
      <div className="mt-5 grid items-center gap-6 md:grid-cols-[minmax(220px,0.8fr)_1fr]">
        <div className="flex min-h-[230px] items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-[#030711]">
          {imageUnavailable ? (
            <p className="p-6 text-sm text-slate-400">NASA context image unavailable from the backend.</p>
          ) : (
            <img
              src={getLayerImageUrl('moon_south_pole.png')}
              alt="NASA LROC WAC mosaic of the lunar south-pole region"
              onError={() => setImageUnavailable(true)}
              className="block h-auto max-h-[360px] w-full object-contain"
            />
          )}
        </div>
        <div className="space-y-3">
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Selected site</p>
            <p className="mt-2 font-semibold text-white">{site?.name ?? 'Unavailable'}</p>
            <p className="mt-1 font-mono text-xs text-slate-400">
              {site?.lat === null || site?.lon === null || !site
                ? <Unavailable reason="Site coordinates are unavailable" />
                : `${site.lat}°, ${site.lon}°`}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="rounded-xl border border-white/10 bg-black/20 p-3">
              <p className="uppercase tracking-widest text-slate-500">Sun elevation</p>
              <p className="mt-1 font-mono text-cyan-200">{sun ? `${sun.el.toFixed(2)}°` : <Unavailable />}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3">
              <p className="uppercase tracking-widest text-slate-500">Sun azimuth</p>
              <p className="mt-1 font-mono text-cyan-200">{sun ? `${sun.az.toFixed(2)}°` : <Unavailable />}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3">
              <p className="uppercase tracking-widest text-slate-500">Earth elevation</p>
              <p className="mt-1 font-mono text-cyan-200">{ephemeris?.earth ? `${ephemeris.earth.el.toFixed(2)}°` : <Unavailable />}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3">
              <p className="uppercase tracking-widest text-slate-500">Earth azimuth</p>
              <p className="mt-1 font-mono text-cyan-200">{ephemeris?.earth ? `${ephemeris.earth.az.toFixed(2)}°` : <Unavailable />}</p>
            </div>
          </div>
          <p className="text-xs leading-5 text-slate-500">
            This regional context image is not georeferenced to the DEM and does not show live illumination. Sun and Earth angles above come from the backend ephemeris response.
          </p>
        </div>
      </div>
    </section>
  );
}
