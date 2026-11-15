import type { Envelope, ScenarioData } from '../api/types';
import ProvenanceBadge from '../components/ProvenanceBadge';
import Unavailable from '../components/Unavailable';

export default function SkyViewConnected({ timeline }: { timeline: Envelope<ScenarioData> | null }) {
  if (!timeline) return <Unavailable label="Sky data unavailable" />;
  const { timeseries } = timeline.data;
  const first = (values: number[] | null) => values?.[0] ?? null;
  return (
    <section className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold text-white">Sky View</h1>
        <p className="mt-1 text-sm text-slate-400">Sun and Earth geometry from the selected backend timeline.</p>
      </header>
      <div className="grid gap-4 md:grid-cols-2">
        <AngleCard label="Sun" elevation={first(timeseries.sun_el)} azimuth={first(timeseries.sun_az)} />
        <AngleCard label="Earth" elevation={first(timeseries.earth_el)} azimuth={first(timeseries.earth_az)} />
      </div>
      <section className="mission-card rounded-2xl p-5 sm:p-6">
        <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">Horizon profile</h2>
        <p className="mt-2 text-xs text-slate-500">Index is azimuth in degrees: 0 = North, clockwise.</p>
        <div className="mt-4 max-h-64 overflow-auto rounded-lg border border-white/10">
          {timeline.data.horizon.deg ? (
            <div className="grid grid-cols-3 gap-px bg-white/10 text-xs">
              {timeline.data.horizon.deg.map((value, azimuth) => (
                <div key={azimuth} className="bg-slate-950/80 px-3 py-2">
                  <span className="text-slate-500">{azimuth}°</span>{' '}
                  <span className="font-mono text-slate-200">{value === null ? <Unavailable /> : `${value}°`}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="p-4 text-sm text-slate-500">Terrain horizon <Unavailable reason={timeline.provenance.reason} />.</p>
          )}
        </div>
      </section>
      <ProvenanceBadge provenance={timeline.provenance} cached={timeline.cached} warnings={timeline.warnings} />
    </section>
  );
}

function AngleCard({ label, elevation, azimuth }: { label: string; elevation: number | null; azimuth: number | null }) {
  return (
    <section className="mission-card rounded-2xl p-5 sm:p-6">
      <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">{label}</h2>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <Metric label="Elevation" value={elevation === null ? <Unavailable /> : `${elevation}°`} />
        <Metric label="Azimuth" value={azimuth === null ? <Unavailable /> : `${azimuth}°`} />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-lg text-cyan-300">{value}</p>
    </div>
  );
}
