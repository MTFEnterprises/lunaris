import { useState } from 'react';
import type { MouseEvent as ReactMouseEvent } from 'react';
import { POWER_HOURS, SITES } from './data';
import { useReady } from './hooks';

/* ================================================================== */
/*  Pure SVG / HTML charts (no chart library required)                 */
/* ================================================================== */
function smoothPath(pts: [number, number][]) {
  if (pts.length < 2) return '';
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] ?? pts[i];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[i + 2] ?? p2;
    const c1x = p1[0] + (p2[0] - p0[0]) / 6;
    const c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6;
    const c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C${c1x},${c1y} ${c2x},${c2y} ${p2[0]},${p2[1]}`;
  }
  return d;
}

interface AreaChartProps {
  id: string;
  data: number[];
  labels?: string[];
  unit?: string;
  height?: number;
  compact?: boolean;
  color?: string;
}

export function AreaChart({ id, data, labels, unit = '', height = 180, compact = false, color = '#22d3ee' }: AreaChartProps) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 600;
  const H = height;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const pad = (max - min) * 0.15 || 1;
  const lo = min - pad;
  const hi = max + pad;
  const pts: [number, number][] = data.map((v, i) => [(i / (data.length - 1)) * W, H - ((v - lo) / (hi - lo)) * H]);
  const line = smoothPath(pts);
  const area = `${line} L${W},${H} L0,${H} Z`;

  const onMove = (e: ReactMouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const i = Math.round(((e.clientX - rect.left) / rect.width) * (data.length - 1));
    setHover(Math.max(0, Math.min(data.length - 1, i)));
  };

  const hp = hover !== null && hover < pts.length ? pts[hover] : null;
  const leftPct = hp ? (hp[0] / W) * 100 : 0;
  const topPct = hp ? (hp[1] / H) * 100 : 0;

  return (
    <div>
      <div className="relative" style={{ height }} onMouseMove={compact ? undefined : onMove} onMouseLeave={compact ? undefined : () => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-full w-full overflow-visible">
          <defs>
            <linearGradient id={`area-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.45" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>
          {!compact &&
            [0.25, 0.5, 0.75].map((f) => (
              <line key={f} x1="0" x2={W} y1={H * f} y2={H * f} stroke="rgba(255,255,255,0.07)" strokeDasharray="4 6" vectorEffect="non-scaling-stroke" />
            ))}
          <path d={area} fill={`url(#area-${id})`} />
          <path d={line} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
        </svg>

        {hp && hover !== null && (
          <>
            <div className="pointer-events-none absolute bottom-0 top-0 w-px bg-cyan-300/30" style={{ left: `${leftPct}%` }} />
            <div
              className="pointer-events-none absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-cyan-400 shadow-[0_0_14px_rgba(34,211,238,0.9)]"
              style={{ left: `${leftPct}%`, top: `${topPct}%` }}
            />
            <div
              className="pointer-events-none absolute -translate-x-1/2 whitespace-nowrap rounded-lg border border-white/10 bg-slate-950/90 px-2.5 py-1 text-[11px] text-slate-100"
              style={{ left: `${Math.max(12, Math.min(88, leftPct))}%`, top: -34 }}
            >
              <span className="font-semibold text-cyan-300">{data[hover]}{unit}</span>
              {labels && <span className="ml-1.5 text-slate-400">{labels[hover]}</span>}
            </div>
          </>
        )}
      </div>
      {!compact && labels && (
        <div className="mt-2 flex justify-between text-[10px] text-slate-500">
          <span>{labels[0]}</span>
          <span>{labels[Math.floor(labels.length / 2)]}</span>
          <span>{labels[labels.length - 1]}</span>
        </div>
      )}
    </div>
  );
}

interface DonutProps {
  segments: { label: string; value: number; color: string }[];
  centerValue: string;
  centerLabel: string;
}

export function Donut({ segments, centerValue, centerLabel }: DonutProps) {
  const total = segments.reduce((s, x) => s + x.value, 0);
  const r = 52;
  const C = 2 * Math.PI * r;
  let acc = 0;
  return (
    <div className="relative h-40 w-40">
      <svg viewBox="0 0 140 140" className="h-full w-full -rotate-90">
        <circle cx="70" cy="70" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" />
        {segments.map((s) => {
          const len = (s.value / total) * C;
          const el = (
            <circle
              key={s.label}
              cx="70"
              cy="70"
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={`${Math.max(len - 4, 1)} ${C - len + 4}`}
              strokeDashoffset={-acc}
            />
          );
          acc += len;
          return el;
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white">{centerValue}</span>
        <span className="text-[10px] uppercase tracking-widest text-slate-400">{centerLabel}</span>
      </div>
    </div>
  );
}

export function PowerBars({ height = 110 }: { height?: number }) {
  const ready = useReady(500);
  const max = Math.max(...POWER_HOURS.map((p) => p.kw));
  return (
    <div>
      <div className="flex items-end gap-2.5 border-b border-white/10 pb-2" style={{ height }}>
        {POWER_HOURS.map((p, idx) => {
          const now = idx === POWER_HOURS.length - 1;
          return (
            <div key={p.label} className="flex h-full flex-1 flex-col justify-end">
              <div
                className={`group relative w-full rounded-t-md transition-all duration-1000 ease-out ${
                  now ? 'bg-cyan-400 shadow-[0_0_14px_rgba(34,211,238,0.7)]' : 'bg-gradient-to-t from-sky-800/70 to-sky-400/60 hover:from-sky-600 hover:to-cyan-300'
                }`}
                style={{ height: ready ? `${(p.kw / max) * 100}%` : '0%' }}
              >
                <span className="pointer-events-none absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-950/90 px-1.5 py-0.5 text-[10px] font-semibold text-cyan-200 opacity-0 transition group-hover:opacity-100">
                  {p.kw} kW
                </span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex gap-2.5">
        {POWER_HOURS.map((p, idx) => (
          <span key={p.label} className={`flex-1 text-center font-mono text-[10px] ${idx === POWER_HOURS.length - 1 ? 'font-bold text-cyan-400' : 'text-slate-500'}`}>
            {p.label}
          </span>
        ))}
      </div>
    </div>
  );
}

/** Horizontal safety-score comparison of all landing sites (click a row to select it). */
export function SiteSafetyChart({ selected, onSelect }: { selected: number; onSelect: (i: number) => void }) {
  const ready = useReady(400);
  const rows = SITES.map((s, i) => ({ s, i })).sort((a, b) => b.s.safety - a.s.safety);
  return (
    <div className="space-y-3">
      {rows.map(({ s, i }) => {
        const active = i === selected;
        const bar =
          s.safety >= 90
            ? 'from-emerald-500 to-teal-400'
            : s.safety >= 80
              ? 'from-cyan-500 to-blue-500'
              : s.safety >= 70
                ? 'from-amber-500 to-orange-500'
                : 'from-rose-500 to-red-500';
        return (
          <button key={s.code} onClick={() => onSelect(i)} className="block w-full text-left">
            <div className="mb-1 flex justify-between text-[11px]">
              <span className={active ? 'font-semibold text-cyan-300' : 'text-slate-300'}>{s.name}</span>
              <span className="font-mono font-bold text-slate-100">{s.safety}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full border border-white/5 bg-white/10">
              <div
                className={`h-full rounded-full bg-gradient-to-r transition-all duration-1000 ease-out ${bar} ${active ? 'shadow-[0_0_12px_rgba(34,211,238,0.7)]' : ''}`}
                style={{ width: ready ? `${s.safety}%` : '0%' }}
              />
            </div>
          </button>
        );
      })}
    </div>
  );
}
