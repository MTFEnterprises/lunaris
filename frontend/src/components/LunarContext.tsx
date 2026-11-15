import { useState } from 'react';
import { getLayerImageUrl } from '../api/client';

export default function LunarContext() {
  const [imageUnavailable, setImageUnavailable] = useState(false);

  return (
    <section className="mission-card rounded-2xl p-5 sm:p-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[0.25em] text-cyan-200">NASA source image</p>
          <h2 className="mt-1 text-base font-bold text-white">LROC WAC south-pole mosaic</h2>
        </div>
        <a
          href="https://science.nasa.gov/photojournal/the-lunar-south-pole/"
          target="_blank"
          rel="noreferrer"
          className="text-[10px] text-cyan-200 underline underline-offset-2"
        >
          NASA / GSFC / Arizona State University · PIA13523
        </a>
      </header>
      <div className="mt-4 flex min-h-40 items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-[#030711]">
        {imageUnavailable ? (
          <p className="p-5 text-xs text-slate-400">NASA context image unavailable from the backend.</p>
        ) : (
          <img
            src={getLayerImageUrl('moon_south_pole.png')}
            alt="LROC WAC polar-stereographic south-pole mosaic, 400 metres per pixel"
            onError={() => setImageUnavailable(true)}
            className="block h-auto max-h-64 w-full object-contain"
          />
        )}
      </div>
      <p className="mt-3 text-[10px] leading-5 text-slate-400">
        Polar stereographic context image, not a globe texture and not georeferenced to the DEM tiles.
        Terrain-to-site alignment remains preliminary pending independent control-point validation.
      </p>
      <p className="mt-3 text-[10px] text-slate-500">No live illumination overlay.</p>
    </section>
  );
}
