import { useEffect, useMemo, useState } from 'react';
import { compare, ApiError } from '../api/client';
import type { Envelope, Site } from '../api/types';
import ErrorState from '../components/ErrorState';
import Loading from '../components/Loading';
import ProvenanceBadge from '../components/ProvenanceBadge';
import Unavailable from '../components/Unavailable';

type CompareResponse = {
  mode: string;
  items: Array<{
    label: string;
    site: Site;
    metrics: Record<string, number | null>;
    horizon_approx: boolean;
    warnings: string[];
  }> | null;
  site: Site | null;
  scan: Array<{ start_utc: string; metrics: Record<string, number | null> }> | null;
};

const METRICS = [
  { key: 'sunlit_geom_pct', label: 'Sunlit · geometric' },
  { key: 'sunlit_terrain_pct', label: 'Sunlit · terrain corrected' },
  { key: 'earth_geom_pct', label: 'Earth visible · geometric' },
  { key: 'earth_terrain_pct', label: 'Earth visible · terrain corrected' },
  { key: 'longest_dark_h', label: 'Longest dark interval' },
  { key: 'longest_comms_gap_h', label: 'Longest Earth-visibility gap' },
] as const;

export default function CompareConnected({
  sites,
  selectedId,
  startDate,
}: {
  sites: Site[];
  selectedId: string;
  startDate: string;
}) {
  const [mode, setMode] = useState<'scenarios' | 'date_scan'>('scenarios');
  const [scenarioIds, setScenarioIds] = useState<string[]>(selectedId ? [selectedId] : []);
  const [scanEnd, setScanEnd] = useState(startDate);
  const [hours, setHours] = useState(24);
  const [result, setResult] = useState<Envelope<CompareResponse> | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  const availableSites = useMemo(() => sites.filter((site) => site.id), [sites]);

  useEffect(() => {
    if (!selectedId) return;
    setScenarioIds((current) => current.length === 0 ? [selectedId] : current);
  }, [selectedId]);

  async function runCompare() {
    setLoading(true);
    setError(null);
    try {
      const body = mode === 'scenarios'
        ? {
            mode,
            scenarios: scenarioIds.map((site_id, index) => ({
              site_id,
              start_utc: `${startDate}T00:00:00Z`,
              hours,
              label: String.fromCharCode(65 + index),
            })),
          }
        : {
            mode,
            date_scan: {
              site_id: selectedId,
              start_dates: datesBetween(startDate, scanEnd),
              hours,
            },
          };
      setResult(await compare(body));
    } catch (reason) {
      setError(reason);
    } finally {
      setLoading(false);
    }
  }

  function updateScenario(index: number, siteId: string) {
    setScenarioIds((current) => current.map((value, itemIndex) => itemIndex === index ? siteId : value));
  }

  return (
    <section className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold text-white">Compare</h1>
        <p className="mt-1 text-sm text-slate-400">Backend comparison results only; unknown is never treated as pass.</p>
      </header>
      <section className="mission-card rounded-2xl p-5 sm:p-6">
        <div className="flex flex-wrap gap-2">
          {(['scenarios', 'date_scan'] as const).map((value) => (
            <button
              key={value}
              onClick={() => setMode(value)}
              className={`rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-widest ${mode === value ? 'bg-cyan-300 text-slate-950' : 'border border-white/10 text-slate-400'}`}
            >
              {value === 'date_scan' ? 'Date shift' : 'Scenarios'}
            </button>
          ))}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {mode === 'scenarios' ? (
            scenarioIds.map((siteId, index) => (
              <label key={index} className="text-xs text-slate-400">
                Scenario {String.fromCharCode(65 + index)}
                <select value={siteId} onChange={(event) => updateScenario(index, event.target.value)} className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-2 py-2 text-sm text-slate-100">
                  {availableSites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
                </select>
              </label>
            ))
          ) : (
            <label className="text-xs text-slate-400">
              Scan end date
              <input type="date" min={startDate} max="2027-12-31" value={scanEnd} onChange={(event) => setScanEnd(event.target.value)} className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-2 py-2 text-sm text-slate-100" />
            </label>
          )}
          <label className="text-xs text-slate-400">
            Window hours
            <input type="number" min="1" max="744" value={hours} onChange={(event) => setHours(Number(event.target.value))} className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-2 py-2 text-sm text-slate-100" />
          </label>
        </div>
        {mode === 'scenarios' && scenarioIds.length < 3 && (
          <button onClick={() => setScenarioIds((current) => [...current, selectedId])} className="mt-4 mr-2 rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-300 hover:border-cyan-300/50">
            Add scenario
          </button>
        )}
        {mode === 'scenarios' && scenarioIds.length > 1 && (
          <button onClick={() => setScenarioIds((current) => current.slice(0, -1))} className="mt-4 rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-300 hover:border-cyan-300/50">
            Remove last
          </button>
        )}
        <button onClick={() => void runCompare()} disabled={loading || (mode === 'scenarios' && scenarioIds.length === 0) || (mode === 'date_scan' && datesBetween(startDate, scanEnd).length === 0)} className="mt-4 block rounded-lg bg-cyan-300 px-4 py-2 text-xs font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50">
          Run backend comparison
        </button>
      </section>
      {loading && <Loading label="Comparing backend scenarios…" />}
      {error && <ErrorState error={error} />}
      {result && <CompareResult result={result} />}
    </section>
  );
}

function CompareResult({ result }: { result: Envelope<CompareResponse> }) {
  const rows = result.data.mode === 'date_scan' ? result.data.scan : result.data.items;
  return (
    <section className="mission-card space-y-4 rounded-2xl p-5 sm:p-6">
      <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">Backend result</h2>
      {rows?.map((row, index) => {
        const label = 'label' in row ? `${row.label} · ${row.site.name}` : row.start_utc;
        const warnings = 'warnings' in row ? row.warnings : [];
        return (
          <div key={label} className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-semibold text-white">{label}</h3>
              {'horizon_approx' in row && <span className="text-xs text-slate-500">Horizon approximate: {row.horizon_approx ? 'Yes' : 'No'}</span>}
            </div>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {METRICS.map(({ key, label: metricLabel }) => (
                <div key={key}>
                  <p className="text-[11px] text-slate-500">{metricLabel}</p>
                  <p className="font-mono text-sm text-cyan-300">{row.metrics[key] == null ? <Unavailable /> : row.metrics[key]}</p>
                </div>
              ))}
            </div>
            {warnings.map((warning) => <p key={warning} className="mt-3 text-xs text-amber-300">{warning}</p>)}
            {index === 0 && <p className="mt-3 text-xs text-slate-500">Every metric above is returned by `/api/compare`.</p>}
          </div>
        );
      })}
      {!rows?.length && <Unavailable label="No comparison rows returned" />}
      <ProvenanceBadge provenance={result.provenance} cached={result.cached} warnings={result.warnings} />
    </section>
  );
}

function datesBetween(start: string, end: string): string[] {
  const first = new Date(`${start}T00:00:00Z`);
  const last = new Date(`${end}T00:00:00Z`);
  if (Number.isNaN(first.valueOf()) || Number.isNaN(last.valueOf()) || first > last) return [];
  const dates: string[] = [];
  for (const current = new Date(first); current <= last; current.setUTCDate(current.getUTCDate() + 1)) {
    dates.push(current.toISOString().slice(0, 10) + 'T00:00:00Z');
  }
  return dates;
}
