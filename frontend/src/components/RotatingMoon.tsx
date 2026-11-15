import Unavailable from './Unavailable';
import type { EphemerisData, Site } from '../api/types';

export default function RotatingMoon({
  site,
  ephemeris,
}: {
  site: Site | null;
  ephemeris: EphemerisData | null;
}) {
  const sun = ephemeris?.sun;
  const lightX = sun ? Math.round(50 + Math.cos((sun.az * Math.PI) / 180) * 28) : 50;
  const lightY = sun ? Math.round(50 - Math.sin((sun.el * Math.PI) / 180) * 28) : 50;
  const shadowOpacity = sun ? Math.max(0.18, Math.min(0.82, 0.58 - sun.el / 180)) : 0.55;

  return (
    <section className="overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.06] via-slate-950 to-cyan-400/[0.05] p-5 sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-cyan-300">Lunar orientation</p>
          <h2 className="mt-1 text-xl font-extrabold text-white">Rotating Moon</h2>
          <p className="mt-1 text-xs text-slate-400">Live API-backed lighting for the selected site and UTC date.</p>
        </div>
        <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-2 py-1 text-[10px] uppercase tracking-widest text-amber-200">
          Illustrative
        </span>
      </div>
      <div className="mt-5 grid items-center gap-6 md:grid-cols-[minmax(220px,0.8fr)_1fr]">
        <div className="flex min-h-[230px] items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-[#030711]">
          <div
            className="relative h-44 w-44 rounded-full shadow-[inset_-24px_-12px_42px_rgba(2,6,23,0.8),0_0_46px_rgba(148,163,184,0.2)] [animation:lunaris-moon-spin_24s_linear_infinite]"
            style={{
              background: `radial-gradient(circle at ${lightX}% ${lightY}%, #f8fafc 0%, #aeb8c8 34%, #667085 68%, #1e293b 100%)`,
            }}
          >
            <div className="absolute left-[22%] top-[25%] h-5 w-7 rounded-full bg-slate-500/30 shadow-[38px_32px_0_4px_rgba(71,85,105,0.22),-10px_60px_0_2px_rgba(71,85,105,0.25),48px_72px_0_3px_rgba(71,85,105,0.2)]" />
            <div className="absolute inset-y-0 right-0 w-1/3 rounded-r-full bg-slate-950" style={{ opacity: shadowOpacity }} />
          </div>
        </div>
        <div className="space-y-3">
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Selected site</p>
            <p className="mt-2 font-semibold text-white">{site?.name ?? 'Unavailable'}</p>
            <p className="mt-1 text-xs text-slate-400">
              {site?.lat === null || site?.lon === null || !site ? (
                <>Coordinates: <Unavailable reason="Site coordinates are unavailable" /></>
              ) : (
                'Coordinates are shown in the API-backed site cards.'
              )}
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
          </div>
          <p className="text-xs leading-5 text-slate-500">
            Lighting is derived from the API ephemeris response. The rotating surface remains illustrative and does not assert terrain alignment, scale, or a landing location.
          </p>
        </div>
      </div>
    </section>
  );
}
