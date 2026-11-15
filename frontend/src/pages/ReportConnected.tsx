import { useState } from 'react';
import { assess, report } from '../api/client';
import type { AssessmentData, Envelope, ReportData, RequirementRequest } from '../api/types';
import ErrorState from '../components/ErrorState';
import Loading from '../components/Loading';
import ProvenanceBadge from '../components/ProvenanceBadge';
import Unavailable from '../components/Unavailable';

const INITIAL_REQUIREMENTS: RequirementRequest[] = [
  { id: 'min_sunlit', threshold: 50, basis: 'terrain' },
  { id: 'min_earth', threshold: 30, basis: 'terrain' },
  { id: 'max_dark_hours', threshold: 100, basis: 'terrain' },
];

export default function ReportConnected({ siteId, startDate }: { siteId: string; startDate: string }) {
  const [requirements, setRequirements] = useState(INITIAL_REQUIREMENTS);
  const [assessment, setAssessment] = useState<Envelope<AssessmentData> | null>(null);
  const [reportResult, setReportResult] = useState<Envelope<ReportData> | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  async function runReport() {
    setLoading(true);
    setError(null);
    const scenario = { site_id: siteId, start_utc: `${startDate}T00:00:00Z`, hours: 24 };
    try {
      const [assessmentResponse, reportResponse] = await Promise.all([
        assess(scenario, requirements),
        report(scenario, requirements),
      ]);
      setAssessment(assessmentResponse);
      setReportResult(reportResponse);
    } catch (reason) {
      setError(reason);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold text-white">Assessment & Report</h1>
        <p className="mt-1 text-sm text-slate-400">Requirements are evaluated by the backend; unknown is not pass.</p>
      </header>
      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
        <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">Requirements</h2>
        <div className="mt-4 space-y-3">
          {requirements.map((requirement, index) => (
            <div key={requirement.id} className="grid gap-2 sm:grid-cols-[1fr_120px_140px]">
              <label className="text-xs text-slate-400">
                Requirement
                <select value={requirement.id} onChange={(event) => updateRequirement(setRequirements, index, 'id', event.target.value as RequirementRequest['id'])} className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-2 py-2 text-sm text-slate-100">
                  <option value="min_sunlit">Minimum sunlit</option>
                  <option value="min_earth">Minimum Earth visible</option>
                  <option value="max_dark_hours">Maximum dark hours</option>
                </select>
              </label>
              <label className="text-xs text-slate-400">
                Threshold
                <input type="number" value={requirement.threshold} onChange={(event) => updateRequirement(setRequirements, index, 'threshold', Number(event.target.value))} className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-2 py-2 text-sm text-slate-100" />
              </label>
              <label className="text-xs text-slate-400">
                Basis
                <select value={requirement.basis} onChange={(event) => updateRequirement(setRequirements, index, 'basis', event.target.value as RequirementRequest['basis'])} className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950 px-2 py-2 text-sm text-slate-100">
                  <option value="terrain">Terrain</option>
                  <option value="geometric">Geometric</option>
                </select>
              </label>
            </div>
          ))}
        </div>
        <button onClick={() => void runReport()} disabled={loading || !siteId} className="mt-4 rounded-lg bg-cyan-300 px-4 py-2 text-xs font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50">
          Generate backend report
        </button>
      </section>
      {loading && <Loading label="Generating assessment and report…" />}
      {error && <ErrorState error={error} />}
      {assessment && <AssessmentResult result={assessment} />}
      {reportResult && <ReportResult result={reportResult} />}
    </section>
  );
}

function AssessmentResult({ result }: { result: Envelope<AssessmentData> }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">Assessment</h2>
        <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-widest text-cyan-300">{result.data.overall}</span>
      </div>
      <div className="mt-4 space-y-3">
        {result.data.results.map((item) => (
          <div key={item.id} className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-semibold text-white">{item.id}</span>
              <span className={item.status === 'pass' ? 'text-emerald-300' : item.status === 'fail' ? 'text-rose-300' : 'text-amber-300'}>{item.status}</span>
            </div>
            <p className="mt-2 text-xs text-slate-400">{item.reason || <Unavailable />}</p>
            <p className="mt-1 text-xs text-slate-500">Measured: {item.measured === null ? <Unavailable /> : item.measured} · Threshold: {item.threshold} · Confidence: {item.confidence}</p>
            {item.missing_info.map((missing) => <p key={missing} className="mt-1 text-xs text-amber-300">{missing}</p>)}
          </div>
        ))}
      </div>
      <ProvenanceBadge provenance={result.provenance} cached={result.cached} warnings={result.warnings} />
    </section>
  );
}

function ReportResult({ result }: { result: Envelope<ReportData> }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">Full report response</h2>
      <pre className="mt-4 max-h-[560px] overflow-auto rounded-xl border border-white/10 bg-slate-950/70 p-4 text-xs leading-relaxed text-slate-300">
        {JSON.stringify(result.data, null, 2)}
      </pre>
      <div className="mt-4"><ProvenanceBadge provenance={result.provenance} cached={result.cached} warnings={result.warnings} /></div>
    </section>
  );
}

function updateRequirement<K extends keyof RequirementRequest>(
  setRequirements: React.Dispatch<React.SetStateAction<RequirementRequest[]>>,
  index: number,
  key: K,
  value: RequirementRequest[K],
) {
  setRequirements((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item));
}
