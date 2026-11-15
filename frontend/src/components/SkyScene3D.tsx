import { lazy, Suspense } from 'react';
import type {
  Angle,
  Envelope,
  EphemerisData,
  PowerEstimateData,
  ScenarioData,
  Site,
  TerrainSlopeData,
} from '../api/types';
import { formatLatitude, formatLongitude } from '../lunaris/data';
import ProvenanceBadge from './ProvenanceBadge';
import Unavailable from './Unavailable';

const RotatingMoon3D = lazy(() => import('./RotatingMoon3D'));

function project(angle: Angle | null) {
  if (!angle) return null;
  const azimuth = (angle.az * Math.PI) / 180;
  const elevation = (angle.el * Math.PI) / 180;
  const radius = 42 * Math.cos(elevation);
  return {
    left: 50 + Math.sin(azimuth) * radius,
    top: 50 - Math.sin(elevation) * 34,
    depth: Math.cos(azimuth) * Math.cos(elevation),
  };
}

function SkyObject({ label, angle, tone }: { label: string; angle: Angle | null; tone: 'sun' | 'earth' }) {
  const position = project(angle);
  if (!position) return null;

  const color = tone === 'sun'
    ? 'border-amber-100 bg-amber-300 text-amber-950 shadow-amber-300/40'
    : 'border-cyan-100 bg-cyan-300 text-slate-950 shadow-cyan-300/40';

  return (
    <div
      className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1.5"
      style={{ left: `${position.left}%`, top: `${position.top}%`, zIndex: Math.round(position.depth * 10) + 20 }}
    >
      <div className={`flex h-10 w-10 items-center justify-center rounded-full border shadow-[0_0_26px] ${color}`}>
        <span className="text-[9px] font-black uppercase">{label}</span>
      </div>
      <div className="rounded-md border border-white/10 bg-[#07101f]/90 px-2 py-1 text-center text-[9px] text-slate-200 backdrop-blur">
        <p className="font-mono">{angle.el.toFixed(1)}° el</p>
        <p className="font-mono text-slate-400">{angle.az.toFixed(1)}° az</p>
      </div>
    </div>
  );
}

export default function SkyScene3D({
  site,
  ephemeris,
  timeline,
  powerEstimate,
  slopeEstimate,
  powerError,
  slopeError,
  loading,
  loadingPower,
  loadingSlope,
}: {
  site: Site | null;
  ephemeris: Envelope<EphemerisData> | null;
  timeline: Envelope<ScenarioData> | null;
  powerEstimate: Envelope<PowerEstimateData> | null;
  slopeEstimate: Envelope<TerrainSlopeData> | null;
  powerError: unknown;
  slopeError: unknown;
  loading: boolean;
  loadingPower: boolean;
  loadingSlope: boolean;
}) {
  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="mission-stage relative min-h-[440px] overflow-hidden rounded-[2rem] border border-cyan-100/15 sm:min-h-[520px]">
        <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
          <div className="orbit-ring orbit-ring-one absolute left-1/2 top-1/2 h-[78%] w-[75%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/20" />
          <div className="orbit-ring orbit-ring-two absolute left-1/2 top-1/2 h-[92%] w-[92%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-blue-300/10" />
          <div className="absolute left-1/2 top-1/2 h-px w-[88%] -translate-x-1/2 bg-cyan-100/10" />
          <div className="absolute left-1/2 top-1/2 h-[84%] w-px -translate-x-1/2 -translate-y-1/2 bg-cyan-100/[0.06]" />
          <span className="absolute left-[17%] top-[35%] h-1 w-1 rounded-full bg-cyan-100 shadow-[0_0_12px_3px_rgba(103,232,249,0.65)]" />
          <span className="absolute right-[18%] top-[25%] h-1.5 w-1.5 rounded-full bg-white shadow-[0_0_12px_3px_rgba(255,255,255,0.55)]" />
          <span className="absolute bottom-[22%] right-[28%] h-1 w-1 rounded-full bg-blue-100 shadow-[0_0_10px_3px_rgba(147,197,253,0.6)]" />
        </div>

        <header className="absolute left-5 top-5 z-30 max-w-[70%]">
          <p className="text-[9px] font-bold uppercase tracking-[0.3em] text-cyan-200">Geometric sky · selected site</p>
          <h2 className="mt-1 text-lg font-bold text-white sm:text-xl">Sun and Earth orientation</h2>
          <p className="mt-1 text-[10px] text-slate-400 sm:text-xs">
            Backend azimuth/elevation on a local horizon. Orbit styling is illustrative, not to scale.
          </p>
        </header>

        <div className="absolute inset-0 z-10 flex items-center justify-center pt-20">
          <Suspense fallback={<p className="text-xs text-cyan-100">Loading Moon renderer…</p>}>
            <RotatingMoon3D
              showLabel={false}
              className="h-[min(70vw,360px)] w-[min(70vw,360px)] rounded-full border-0 bg-transparent"
            />
          </Suspense>
        </div>

        <div className="absolute inset-0">
          {loading
            ? <p className="absolute bottom-5 right-5 z-30 text-xs text-cyan-100">Updating ephemeris…</p>
            : (
              <>
                <SkyObject label="SUN" angle={ephemeris?.data.sun ?? null} tone="sun" />
                <SkyObject label="EARTH" angle={ephemeris?.data.earth ?? null} tone="earth" />
              </>
            )}
        </div>

        <div className="absolute bottom-4 left-4 z-30 rounded-lg border border-white/10 bg-[#07101f]/80 px-3 py-2 text-[10px] text-slate-400 backdrop-blur">
          {ephemeris?.data.frame ? `Ephemeris frame: ${ephemeris.data.frame}` : 'Ephemeris frame unavailable'}
          <span className="px-1.5 text-slate-600">·</span>
          0° North, azimuth clockwise
        </div>
      </div>

      <aside className="grid content-start gap-3 sm:grid-cols-2 xl:grid-cols-1">
        <SiteCard site={site} slope={slopeEstimate} error={slopeError} loading={loadingSlope} />
        <PowerCard estimate={powerEstimate} error={powerError} loading={loadingPower} />
        <EphemerisCard ephemeris={ephemeris} timeline={timeline} />
      </aside>
    </section>
  );
}

function SiteCard({
  site,
  slope,
  error,
  loading,
}: {
  site: Site | null;
  slope: Envelope<TerrainSlopeData> | null;
  error: unknown;
  loading: boolean;
}) {
  return (
    <section className="mission-card rounded-2xl p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[0.25em] text-cyan-200">Selected site</p>
          <h3 className="mt-1 text-base font-bold text-white">{site?.name ?? 'Unavailable'}</h3>
        </div>
        <span className="rounded-full border border-amber-200/20 bg-amber-200/[0.06] px-2 py-1 text-[9px] uppercase tracking-widest text-amber-100">
          Terrain preliminary
        </span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <SmallMetric label="Latitude" value={formatLatitude(site?.lat ?? null)} />
        <SmallMetric label="Longitude" value={formatLongitude(site?.lon ?? null)} />
        <SmallMetric label="Published elevation" value={site?.height_m == null ? 'Not published' : `${site.height_m} m`} />
        <SmallMetric
          label={`Mean slope · ${slope?.data.radius_m ?? 500} m radius`}
          value={loading ? 'Loading…' : error ? errorMessage(error) : slope?.data.slope_mean_deg == null ? 'Unavailable' : `${slope.data.slope_mean_deg.toFixed(2)}°`}
        />
      </div>
      {site?.source_url && (
        <a href={site.source_url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-[10px] text-cyan-200 underline underline-offset-2">
          Coordinate source
        </a>
      )}
      {slope?.data.slope_max_deg != null && (
        <p className="mt-2 text-[10px] text-slate-400">
          Max slope {slope.data.slope_max_deg.toFixed(2)}° · roughness {slope.data.roughness_m == null ? 'unavailable' : `${slope.data.roughness_m.toFixed(2)} m`}
        </p>
      )}
      {error && <p className="mt-2 text-[10px] text-rose-200">{errorMessage(error)}</p>}
      {slope?.warnings.map((warning) => <p key={warning} className="mt-2 text-[10px] leading-4 text-amber-200">{warning}</p>)}
      {slope && <div className="mt-2"><ProvenanceBadge provenance={slope.provenance} cached={slope.cached} warnings={slope.warnings} /></div>}
    </section>
  );
}

function PowerCard({
  estimate,
  error,
  loading,
}: {
  estimate: Envelope<PowerEstimateData> | null;
  error: unknown;
  loading: boolean;
}) {
  const values = estimate?.data.power_w ?? [];
  const path = powerPath(values);

  return (
    <section className="mission-card rounded-2xl p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[0.25em] text-cyan-200">Solar power estimate</p>
          <h3 className="mt-1 text-base font-bold text-white">24-hour model</h3>
        </div>
        <span className="rounded-full border border-violet-200/20 bg-violet-200/[0.06] px-2 py-1 text-[9px] uppercase tracking-widest text-violet-100">
          Estimated
        </span>
      </div>
      <p className="mt-1 text-[10px] text-slate-400">Model output, not live power telemetry.</p>
      <div className="mt-3 h-16 overflow-hidden rounded-lg border border-white/[0.06] bg-[#050b18]/70 p-1">
        {loading ? (
          <p className="flex h-full items-center justify-center text-[10px] text-slate-400">Calculating…</p>
        ) : error ? (
          <p className="flex h-full items-center justify-center text-center text-[10px] text-rose-200">{errorMessage(error)}</p>
        ) : path ? (
          <svg viewBox="0 0 240 64" role="img" aria-label="Backend-estimated solar power over 24 hours" className="h-full w-full">
            <path d={path} fill="none" stroke="#67e8f9" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        ) : (
          <p className="flex h-full items-center justify-center text-[10px] text-slate-400"><Unavailable /></p>
        )}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <SmallMetric label="Peak output" value={estimate?.data.peak_w == null ? 'Unavailable' : `${estimate.data.peak_w.toFixed(1)} W`} />
        <SmallMetric label="Energy estimate" value={estimate?.data.energy_wh == null ? 'Unavailable' : `${estimate.data.energy_wh.toFixed(1)} Wh`} />
      </div>
      <p className="mt-2 text-[9px] leading-4 text-slate-500">Assumed panel: 2 m², 28% efficiency, horizontal, 0% losses. Terrain shadowing and degradation are excluded.</p>
      {estimate && <div className="mt-2"><ProvenanceBadge provenance={estimate.provenance} cached={estimate.cached} warnings={estimate.warnings} /></div>}
    </section>
  );
}

function EphemerisCard({
  ephemeris,
  timeline,
}: {
  ephemeris: Envelope<EphemerisData> | null;
  timeline: Envelope<ScenarioData> | null;
}) {
  const data = ephemeris?.data;
  return (
    <section className="mission-card rounded-2xl p-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[0.25em] text-cyan-200">Local sky conditions</p>
          <h3 className="mt-1 text-base font-bold text-white">Sun / Earth geometry</h3>
        </div>
        {data && <span className="font-mono text-[9px] text-slate-500">{data.time_utc}</span>}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <SmallMetric label="Sun elevation / azimuth" value={data?.sun ? `${data.sun.el.toFixed(1)}° / ${data.sun.az.toFixed(1)}°` : 'Unavailable'} />
        <SmallMetric label="Earth elevation / azimuth" value={data?.earth ? `${data.earth.el.toFixed(1)}° / ${data.earth.az.toFixed(1)}°` : 'Unavailable'} />
        <SmallMetric label="Hours to sunset" value={data?.hours_to_sunset == null ? 'Unavailable' : `${data.hours_to_sunset.toFixed(1)} h`} />
        <SmallMetric label="Hours to Earthset" value={data?.hours_to_earthset == null ? 'Unavailable' : `${data.hours_to_earthset.toFixed(1)} h`} />
      </div>
      <p className="mt-2 text-[9px] leading-4 text-slate-500">
        Terrain horizon: {timeline?.data.horizon.deg ? timeline.data.horizon.approx ? 'approximate' : timeline.warnings.length ? 'preliminary' : 'available' : 'unavailable'}.
        Earth visibility is not a radio-link or DSN status.
      </p>
      {ephemeris && <div className="mt-2"><ProvenanceBadge provenance={ephemeris.provenance} cached={ephemeris.cached} warnings={ephemeris.warnings} /></div>}
    </section>
  );
}

function SmallMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg border border-white/[0.06] bg-[#050b18]/60 px-2.5 py-2">
      <p className="text-[9px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-1 break-words font-mono text-[11px] font-semibold text-slate-100">{value}</p>
    </div>
  );
}

function powerPath(values: Array<number | null>): string {
  const available = values.filter((value): value is number => value !== null && Number.isFinite(value));
  if (available.length < 2) return '';

  const minimum = Math.min(...available);
  const range = Math.max(...available) - minimum || 1;
  let hasCurrentSegment = false;
  return values.map((value, index) => {
    if (value === null || !Number.isFinite(value)) {
      hasCurrentSegment = false;
      return '';
    }
    const x = (index / Math.max(values.length - 1, 1)) * 236 + 2;
    const y = 58 - ((value - minimum) / range) * 50;
    const command = hasCurrentSegment ? 'L' : 'M';
    hasCurrentSegment = true;
    return `${command}${x.toFixed(1)} ${y.toFixed(1)}`;
  }).filter(Boolean).join(' ');
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Data unavailable.';
}
