import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type { LinkState, Tone } from './data';
import { useNow, useReady } from './hooks';

/* ------------------------------ icons ------------------------------ */
const ICONS: Record<string, string> = {
  search: 'M21 21l-4.3-4.3M11 18a7 7 0 100-14 7 7 0 000 14z',
  bell: 'M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 01-3.4 0',
  settings: 'M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0M14 4v4M10 10v4M16 16v4',
  arrow: 'M7 17L17 7M8 7h9v9',
  plus: 'M12 5v14M5 12h14',
  minus: 'M5 12h14',
  pause: 'M10 5v14M16 5v14',
  play: 'M6 4l14 8-14 8z',
  reset: 'M3 12a9 9 0 103-6.7L3 8M3 3v5h5',
  left: 'M15 18l-6-6 6-6',
  right: 'M9 18l6-6-6-6',
  sparkle: 'M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z',
  send: 'M22 2L11 13M22 2l-7 20-4-9-9-4z',
  route: 'M5 19a2 2 0 100-4 2 2 0 000 4zM19 9a2 2 0 100-4 2 2 0 000 4zM7 17c6 0 2-10 10-10',
  sun: 'M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6L7 7M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4M12 16a4 4 0 100-8 4 4 0 000 8z',
  battery: 'M3 8h16v8H3zM21 11v2M6 10v4M10 10v4',
  target: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 16a4 4 0 100-8 4 4 0 000 8z',
  grid: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z',
  pin: 'M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11zM12 12a2.5 2.5 0 100-5 2.5 2.5 0 000 5z',
  pulse: 'M3 12h4l3-8 4 16 3-8h4',
  bolt: 'M13 2L4 14h7l-1 8 9-12h-7z',
  mountain: 'M3 20l6-10 4 6 3-4 5 8z',
  calendar: 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
  menu: 'M4 6h16M4 12h16M4 18h16',
  close: 'M6 6l12 12M18 6L6 18',
  collapse: 'M11 17l-5-5 5-5M18 17l-5-5 5-5',
  expand: 'M13 17l5-5-5-5M6 17l5-5-5-5',
  moon: 'M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z',
  clock: 'M12 7v5l3 2M12 21a9 9 0 100-18 9 9 0 000 18z',
  orbit: 'M21 12c0 2-4 4-9 4s-9-2-9-4 4-4 9-4 9 2 9 4zM12 10a2 2 0 100 4 2 2 0 000-4z',
  signal: 'M5 12.5a10 10 0 0114 0M8 15.5a6 6 0 018 0M12 19h.01M2 9a15 15 0 0120 0',
  compass: 'M12 21a9 9 0 100-18 9 9 0 000 18zM15.5 8.5l-2 5-5 2 2-5z',
  rocket: 'M5 15c-1 1-2 4-2 6 2 0 5-1 6-2M14 4c3-1 6-1 7-1 0 1 0 4-1 7l-6 6-6-6zM14 10h.01',
  rover: 'M3 15h18M5 15l1-5h9l3 5M7 19a2 2 0 100-4 2 2 0 000 4zM17 19a2 2 0 100-4 2 2 0 000 4z',
  flask: 'M9 3h6M10 3v6l-5 9a2 2 0 002 3h10a2 2 0 002-3l-5-9V3',
  layers: 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5',
  shield: 'M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z',
  life: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 16a4 4 0 100-8 4 4 0 000 8zM5.6 5.6l3.2 3.2M15.2 15.2l3.2 3.2M18.4 5.6l-3.2 3.2M8.8 15.2l-3.2 3.2',
  list: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
};

export function Icon({ name, className = 'h-4 w-4' }: { name: string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d={ICONS[name] ?? ICONS.grid} />
    </svg>
  );
}

/* ----------------------------- primitives -------------------------- */
export function Panel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-white/10 bg-slate-950/60 bg-gradient-to-b from-white/[0.08] to-white/[0.02] shadow-[0_10px_40px_rgba(0,0,0,0.5)] backdrop-blur-xl ${className}`}>
      {children}
    </div>
  );
}

export function PanelHeader({ title, right }: { title: string; right?: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h3 className="text-[11px] font-bold uppercase tracking-widest text-slate-400">{title}</h3>
      {right}
    </div>
  );
}

export function IconBtn({ icon = 'arrow', onClick, title }: { icon?: string; onClick?: () => void; title?: string }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/15 bg-white/5 text-slate-200 transition hover:border-cyan-300/60 hover:bg-cyan-400/10 hover:text-cyan-200"
    >
      <Icon name={icon} className="h-4 w-4" />
    </button>
  );
}

const TONE: Record<Tone, string> = {
  green: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300',
  amber: 'border-amber-400/30 bg-amber-400/10 text-amber-300',
  rose: 'border-rose-400/30 bg-rose-400/10 text-rose-300',
  cyan: 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200',
  slate: 'border-slate-500/30 bg-slate-500/10 text-slate-300',
};

export function Pill({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${TONE[tone]}`}>
      {children}
    </span>
  );
}

export function Reveal({ children, delay = 0, className = '' }: { children: ReactNode; delay?: number; className?: string }) {
  const [on, setOn] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setOn(true), 40 + delay);
    return () => clearTimeout(t);
  }, [delay]);
  return (
    <div className={`pointer-events-auto transition-all duration-700 ease-out ${on ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'} ${className}`}>
      {children}
    </div>
  );
}

export function Meter({ value, gradient, max = 100 }: { value: number; gradient: string; max?: number }) {
  const ready = useReady(300);
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
      <div
        className={`h-full rounded-full bg-gradient-to-r transition-all duration-1000 ease-out ${gradient}`}
        style={{ width: ready ? `${Math.max(0, Math.min(100, (value / max) * 100))}%` : '0%' }}
      />
    </div>
  );
}

export function StatCard({ label, value, sub, color = 'text-white', icon }: { label: string; value: string; sub: string; color?: string; icon?: string }) {
  return (
    <Panel className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-widest text-slate-400">{label}</p>
          <p className={`mt-2 truncate text-2xl font-extrabold ${color}`}>{value}</p>
          <p className="mt-1 truncate text-[11px] text-slate-500">{sub}</p>
        </div>
        {icon && (
          <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 ${color}`}>
            <Icon name={icon} className="h-5 w-5" />
          </span>
        )}
      </div>
    </Panel>
  );
}

export function LinkPill({ state }: { state: LinkState }) {
  const map = {
    online: { dot: 'bg-emerald-400', text: 'text-emerald-400', label: 'ACTIVE' },
    connecting: { dot: 'bg-amber-400', text: 'text-amber-400', label: 'CONNECTING' },
    offline: { dot: 'bg-rose-400', text: 'text-rose-400', label: 'OFFLINE' },
  }[state];
  return (
    <div className="flex items-center gap-2 whitespace-nowrap rounded-full border border-white/10 bg-slate-950/60 px-3 py-1.5 text-[11px] backdrop-blur-md">
      <span className={`h-2 w-2 animate-pulse rounded-full ${map.dot}`} />
      <span className="text-slate-400">DSN LINK:</span>
      <span className={`font-bold ${map.text}`}>{map.label}</span>
    </div>
  );
}

/** Live UTC clock (has its own timer so the rest of the page does not re-render). */
export function UtcClock() {
  const now = useNow(1000);
  return (
    <div className="flex items-center gap-2 whitespace-nowrap rounded-full border border-white/10 bg-slate-950/60 px-3 py-1.5 text-[11px] backdrop-blur-md">
      <Icon name="clock" className="h-3.5 w-3.5 text-cyan-300" />
      <span className="font-mono font-semibold text-slate-100">{now.toISOString().slice(11, 19)}</span>
      <span className="text-slate-500">UTC</span>
    </div>
  );
}

export function ViewShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <main className="mx-auto max-w-[1500px] space-y-5 px-4 py-6 sm:px-6 xl:px-8">
      <div>
        <h2 className="text-2xl font-extrabold text-white">{title}</h2>
        <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
      </div>
      {children}
    </main>
  );
}
