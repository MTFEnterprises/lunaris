import type { Envelope, EphemerisData, Angle } from '../api/types';
import ProvenanceBadge from './ProvenanceBadge';
import Unavailable from './Unavailable';

function project(angle: Angle | null) {
  if (!angle) return null;
  const azimuth = (angle.az * Math.PI) / 180;
  const elevation = (angle.el * Math.PI) / 180;
  const radius = 34 * Math.cos(elevation);
  return {
    left: 50 + Math.sin(azimuth) * radius,
    top: 50 - Math.sin(elevation) * 34,
    depth: Math.cos(azimuth) * Math.cos(elevation),
  };
}

function SkyObject({ label, angle, tone }: { label: string; angle: Angle | null; tone: 'sun' | 'earth' }) {
  const position = project(angle);
  if (!position) {
    return (
      <div className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-400">
        {label}: <Unavailable />
      </div>
    );
  }

  const size = tone === 'sun' ? 56 : 44;
  return (
    <div
      className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2"
      style={{ left: `${position.left}%`, top: `${position.top}%`, zIndex: Math.round(position.depth * 10) + 10 }}
    >
      <div
        className={`flex items-center justify-center rounded-full border shadow-2xl ${tone === 'sun' ? 'border-amber-200/80 bg-amber-300 text-amber-950 shadow-amber-300/40' : 'border-cyan-100/70 bg-cyan-400 text-slate-950 shadow-cyan-300/40'}`}
        style={{ width: size, height: size }}
      >
        <span className="text-[10px] font-black uppercase">{label}</span>
      </div>
      <div className="rounded-md border border-white/10 bg-slate-950/85 px-2 py-1 text-center text-[10px] text-slate-200 backdrop-blur">
        <p className="font-bold">{label}</p>
        <p className="font-mono text-slate-400">{angle.el.toFixed(2)}° el · {angle.az.toFixed(2)}° az</p>
      </div>
    </div>
  );
}

export default function SkyScene3D({
  ephemeris,
  loading,
}: {
  ephemeris: Envelope<EphemerisData> | null;
  loading: boolean;
}) {
  return (
    <section className="overflow-hidden rounded-3xl border border-cyan-300/20 bg-gradient-to-br from-cyan-400/[0.08] via-slate-950 to-blue-500/[0.08] p-5 shadow-[0_0_45px_rgba(34,211,238,0.08)] sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-cyan-300">Geometric sky scene</p>
          <h2 className="mt-1 text-xl font-extrabold text-white">Sun and Earth at the selected UTC instant</h2>
          <p className="mt-1 text-xs text-slate-400">Interactive visual orientation from backend azimuth/elevation. Not to scale and not a radio-link simulation.</p>
        </div>
        <div className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-right text-[10px] text-slate-400">
          <p>Frame</p>
          <p className="font-mono text-cyan-200">{ephemeris?.data.frame ?? <Unavailable />}</p>
        </div>
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_220px]">
        <div className="relative min-h-[310px] overflow-hidden rounded-2xl border border-white/10 bg-[#030711] [perspective:900px]">
          <div className="absolute inset-8 rounded-full border border-cyan-300/15 shadow-[inset_0_0_50px_rgba(34,211,238,0.08)] [transform:rotateX(58deg)]">
            <div className="absolute inset-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white shadow-[0_0_18px_6px_rgba(255,255,255,0.35)]" />
          </div>
          <div className="absolute left-1/2 top-1/2 h-px w-[72%] -translate-x-1/2 bg-cyan-200/10" />
          <div className="absolute left-1/2 top-1/2 h-[72%] w-px -translate-x-1/2 -translate-y-1/2 bg-cyan-200/10" />
          <div className="absolute inset-0 flex items-center justify-center">
            {loading ? <p className="text-xs text-cyan-200">Loading ephemeris…</p> : (
              <>
                <SkyObject label="SUN" angle={ephemeris?.data.sun ?? null} tone="sun" />
                <SkyObject label="EARTH" angle={ephemeris?.data.earth ?? null} tone="earth" />
              </>
            )}
          </div>
          <div className="absolute bottom-3 left-3 rounded-md border border-white/10 bg-slate-950/80 px-2 py-1 text-[10px] text-slate-500">
            Observer: selected candidate site · azimuth 0° North, clockwise
          </div>
        </div>
        <div className="space-y-3">
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Site</p>
            <p className="mt-2 font-semibold text-white">{ephemeris?.data.site.name ?? 'Selected site'}</p>
            <p className="mt-1 text-xs text-slate-400">{ephemeris?.data.time_utc ?? <Unavailable />}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/20 p-4 text-xs text-slate-400">
            <p>Sunlit geometric: {ephemeris?.data.sun_lit_geom === null || !ephemeris ? <Unavailable /> : ephemeris.data.sun_lit_geom ? 'Yes' : 'No'}</p>
            <p className="mt-2">Earth geometric visibility: {ephemeris?.data.earth_vis_geom === null || !ephemeris ? <Unavailable /> : ephemeris.data.earth_vis_geom ? 'Yes' : 'No'}</p>
          </div>
          {ephemeris && <ProvenanceBadge provenance={ephemeris.provenance} cached={ephemeris.cached} warnings={ephemeris.warnings} />}
        </div>
      </div>
    </section>
  );
}
