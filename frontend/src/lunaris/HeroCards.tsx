import type { StreamPoint } from './data';
import { AreaChart } from './charts';
import { fmtLat, fmtLon, slopeLabel, slopeTone, SITES } from './data';
import { formatDuration, formatShortDate, nextSunEvent, sunElevation } from './lunar';
import type { LunarState } from './lunar';
import { Icon, IconBtn, Panel, PanelHeader, Pill } from './ui';

/* ------------------------- selected site card ----------------------- */
export function SiteCard({ index, onPrev, onNext }: { index: number; onPrev: () => void; onNext: () => void }) {
  const s = SITES[index];
  return (
    <Panel className="p-5">
      <PanelHeader
        title="Selected Site"
        right={
          <div className="flex gap-2">
            <IconBtn icon="left" onClick={onPrev} title="Previous site" />
            <IconBtn icon="right" onClick={onNext} title="Next site" />
          </div>
        }
      />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-lg font-extrabold text-white">{s.name}</p>
          <p className="mt-0.5 font-mono text-[11px] text-cyan-300">{s.code}</p>
        </div>
        <Pill tone={slopeTone(s.slope)}>{slopeLabel(s.slope)}</Pill>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-[11px]">
        <Cell label="Latitude" value={fmtLat(s.lat)} />
        <Cell label="Longitude" value={fmtLon(s.lon)} />
        <Cell label="Slope" value={`${s.slope}°`} />
        <Cell label="Safety" value={`${s.safety}%`} />
      </div>
    </Panel>
  );
}

function Cell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2">
      <p className="text-[9px] uppercase tracking-widest text-slate-500">{label}</p>
      <p className="mt-0.5 font-mono text-sm font-semibold text-slate-100">{value}</p>
    </div>
  );
}

/* --------------------------- phase drawing -------------------------- */
function PhaseDisc({ lunar, size = 84 }: { lunar: LunarState; size?: number }) {
  const r = 40;
  const p = lunar.fraction;
  const cos = Math.cos(2 * Math.PI * p);
  const rx = r * Math.abs(cos);
  const waxing = p < 0.5;
  // terminator: half circle on the lit side + half ellipse
  const sweepT = waxing ? (cos > 0 ? 0 : 1) : cos > 0 ? 1 : 0;
  const outerSweep = waxing ? 1 : 0;
  const d = `M50,10 A${r},${r} 0 0 ${outerSweep} 50,90 A${rx},${r} 0 0 ${sweepT} 50,10 Z`;
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} className="shrink-0">
      <circle cx="50" cy="50" r={r} fill="#111827" stroke="rgba(255,255,255,0.15)" />
      <path d={d} fill="#e5e7eb" />
      <circle cx="50" cy="50" r={r} fill="none" stroke="rgba(103,232,249,0.4)" strokeWidth="1" />
    </svg>
  );
}

/* ------------------------- live moon phase card --------------------- */
export function MoonPhaseCard({ lunar, siteIndex, now, compact = false }: { lunar: LunarState; siteIndex: number; now: Date; compact?: boolean }) {
  const s = SITES[siteIndex];
  const elev = sunElevation(s.lat, s.lon, lunar.sunLon);
  const isDay = elev > 0;
  const ev = nextSunEvent(s.lon, lunar.sunLon);

  return (
    <Panel className="p-5">
      <PanelHeader title="Live Lunar Phase" right={<Pill tone="cyan">Computed</Pill>} />
      <div className="flex items-center gap-4">
        <PhaseDisc lunar={lunar} />
        <div className="min-w-0">
          <p className="text-base font-extrabold leading-tight text-white">{lunar.name}</p>
          <p className="mt-0.5 text-3xl font-extrabold text-cyan-300">
            {lunar.illumination.toFixed(1)}
            <span className="text-base text-slate-400">%</span>
          </p>
          <p className="text-[11px] text-slate-500">illuminated · age {lunar.age.toFixed(1)} d</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <Cell label="Next Full" value={formatShortDate(lunar.nextFull)} />
        <Cell label="Next New" value={formatShortDate(lunar.nextNew)} />
      </div>

      <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate text-[11px] text-slate-400">
            <Icon name="sun" className="mr-1 inline h-3.5 w-3.5 text-amber-300" />
            Sun at {s.name}
          </p>
          <Pill tone={isDay ? 'amber' : 'slate'}>{isDay ? 'Daylight' : 'Night'}</Pill>
        </div>
        <div className="mt-2 flex items-end justify-between">
          <p className="font-mono text-xl font-bold text-white">{elev.toFixed(1)}°</p>
          <p className="text-right text-[11px] text-slate-400">
            next {ev.kind} in <span className="font-semibold text-slate-100">{formatDuration(ev.days)}</span>
          </p>
        </div>
      </div>

      <p className={`mt-3 text-[10px] leading-relaxed text-slate-500 ${compact ? 'hidden' : ''}`}>
        Calculated from today&apos;s UTC date ({now.toISOString().slice(0, 10)}) using the mean synodic month. Approximate (±14 h); the 3D moon is lit from this sun direction.
      </p>
    </Panel>
  );
}


/* ------------------------- live power trend card -------------------- */
export function TrendCard({ stream }: { stream: StreamPoint[] }) {
  const last = stream[stream.length - 1];
  return (
    <Panel className="p-5">
      <PanelHeader title="Live Power Trend" right={<Pill tone="green">Live</Pill>} />
      <div className="flex items-end justify-between">
        <p className="text-3xl font-extrabold text-cyan-300">
          {last.power}
          <span className="text-base text-slate-400"> kW</span>
        </p>
        <p className="text-[11px] text-slate-500">last {stream.length * 3} s</p>
      </div>
      <div className="mt-3">
        <AreaChart id="hero-trend" data={stream.map((p) => p.power)} height={80} compact />
      </div>
    </Panel>
  );
}
