export default function Loading({ label = 'Loading verified backend data…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-300/30 border-t-cyan-300" />
      {label}
    </div>
  );
}
