import type { Envelope, ScenarioData } from '../api/types';
import ProvenanceBadge from '../components/ProvenanceBadge';
import Unavailable from '../components/Unavailable';

export default function TimelineConnected({ timeline }: { timeline: Envelope<ScenarioData> | null }) {
  if (!timeline) return <Unavailable label="Timeline unavailable" />;
  const { timeseries, metrics } = timeline.data;
  return (
    <section className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold text-white">Timeline</h1>
        <p className="mt-1 text-sm text-slate-400">Geometric and terrain-corrected visibility are shown separately.</p>
      </header>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Metric label="Sunlit geometric" value={formatMetric(metrics.sunlit_geom_pct)} />
        <Metric label="Sunlit terrain" value={formatMetric(metrics.sunlit_terrain_pct)} />
        <Metric label="Earth visible geometric" value={formatMetric(metrics.earth_geom_pct)} />
        <Metric label="Earth visible terrain" value={formatMetric(metrics.earth_terrain_pct)} />
        <Metric label="Longest dark interval" value={formatMetric(metrics.longest_dark_h, ' h')} />
        <Metric label="Longest communication gap" value={formatMetric(metrics.longest_comms_gap_h, ' h')} />
      </section>
      <section className="mission-card overflow-x-auto rounded-2xl p-5 sm:p-6">
        <table className="w-full min-w-[760px] text-left text-xs">
          <thead className="border-b border-white/10 text-slate-500">
            <tr>
              <th className="px-3 py-2">Step</th>
              <th className="px-3 py-2">Sun el</th>
              <th className="px-3 py-2">Sun geom</th>
              <th className="px-3 py-2">Sun terrain</th>
              <th className="px-3 py-2">Earth el</th>
              <th className="px-3 py-2">Earth geom</th>
              <th className="px-3 py-2">Earth terrain</th>
            </tr>
          </thead>
          <tbody>
            {timeseries.sun_el.map((_, index) => (
              <tr key={index} className="border-b border-white/5 text-slate-300">
                <td className="px-3 py-2 font-mono">{index * timeseries.step_min} min</td>
                <td className="px-3 py-2 font-mono">{numberCell(timeseries.sun_el[index], '°')}</td>
                <td className="px-3 py-2">{booleanCell(timeseries.sun_lit_geom?.[index])}</td>
                <td className="px-3 py-2">{booleanCell(timeseries.sun_lit_terrain?.[index])}</td>
                <td className="px-3 py-2 font-mono">{numberCell(timeseries.earth_el[index], '°')}</td>
                <td className="px-3 py-2">{booleanCell(timeseries.earth_vis_geom?.[index])}</td>
                <td className="px-3 py-2">{booleanCell(timeseries.earth_vis_terrain?.[index])}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <ProvenanceBadge provenance={timeline.provenance} cached={timeline.cached} warnings={timeline.warnings} />
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="mission-card rounded-xl p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-2 font-mono text-lg text-cyan-300">{value}</p>
    </div>
  );
}

function formatMetric(value: number | null, suffix = '%'): string {
  return value === null ? 'Unavailable' : `${value}${suffix}`;
}

function numberCell(value: number | null | undefined, suffix: string): React.ReactNode {
  return value == null ? <Unavailable /> : `${value}${suffix}`;
}

function booleanCell(value: boolean | null | undefined): React.ReactNode {
  return value == null ? <Unavailable /> : value ? 'Yes' : 'No';
}
