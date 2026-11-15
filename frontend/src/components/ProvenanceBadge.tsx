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
  return (
    <details className="text-[10px] text-slate-500">
      <summary className="cursor-pointer uppercase tracking-widest text-cyan-300/80">
        {provenance.class}
        {cached ? ' · cached' : ''}
      </summary>
      <div className="mt-2 space-y-1 rounded-lg border border-white/10 bg-black/20 p-2">
        {provenance.generated_utc && <p>Generated: {provenance.generated_utc}</p>}
        {provenance.reason && <p>Reason: {provenance.reason}</p>}
        {provenance.inputs.map((input) => (
          <p key={`${input.name}-${input.url ?? ''}`}>
            Source: {input.name}
            {input.url ? ` (${input.url})` : ''}
          </p>
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
