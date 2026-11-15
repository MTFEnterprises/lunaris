import type { Provenance } from '../api/types';

export default function ProvenanceBadge({
  provenance,
  cached = false,
  warnings = [],
}: {
  provenance?: Provenance | null;
  cached?: boolean;
  warnings?: string[];
}) {
  if (!provenance) return null;
  const warningLabel = warnings.length === 0
    ? ''
    : ` · ${warnings.length} warning${warnings.length === 1 ? '' : 's'}`;
  return (
    <details className="text-[10px] text-slate-500">
      <summary className={`cursor-pointer uppercase tracking-widest ${warnings.length > 0 ? 'text-amber-300' : 'text-cyan-300/80'}`}>
        {provenance.class}
        {cached ? ' · cached' : ''}
        {warningLabel}
      </summary>
      <div className="mt-2 space-y-1 rounded-lg border border-white/10 bg-black/20 p-2">
        {provenance.generated_utc && <p>Generated: {provenance.generated_utc}</p>}
        {provenance.reason && <p>Reason: {provenance.reason}</p>}
        {provenance.inputs.map((input) => (
          <div key={`${input.name}-${input.url ?? ''}`} className="border-t border-white/5 pt-1">
            <p>Source: {input.name}</p>
            {input.url && (
              <a href={input.url} target="_blank" rel="noreferrer" className="break-all text-cyan-300 underline underline-offset-2">
                {input.url}
              </a>
            )}
            {input.version && <p>Version: {input.version}</p>}
            {input.retrieved_utc && <p>Retrieved: {input.retrieved_utc}</p>}
          </div>
        ))}
        {provenance.assumptions.map((assumption) => (
          <p key={assumption}>Assumption: {assumption}</p>
        ))}
        {warnings.map((warning) => (
          <p key={warning} className="text-amber-300">
            Warning: {warning}
          </p>
        ))}
      </div>
    </details>
  );
}
