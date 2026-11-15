export default function Unavailable({ reason, label = 'Unavailable' }: { reason?: string | null; label?: string }) {
  return (
    <span title={reason ?? undefined} className="text-slate-500">
      {label}
    </span>
  );
}
