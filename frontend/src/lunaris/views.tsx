import { fmtLat, fmtLon, HOURS_24, MISSION, missionTone, POWER_24H, SITES, siteSeries, slopeLabel, slopeTone, SUBSYSTEMS } from './data';
import type { StreamPoint } from './data';
import type { LunarState } from './lunar';
import { sunElevation } from './lunar';
import { AreaChart, Donut, PowerBars, SiteSafetyChart } from './charts';
import { Icon, Meter, Panel, PanelHeader, Pill, StatCard, ViewShell } from './ui';

/* ============================ SITE PICKER ============================ */
export function SitePickerView({ selected, onSelect, lunar }: { selected: number; onSelect: (i: number) => void; lunar: LunarState }) {
  return (
    <ViewShell title="Site Picker" subtitle="Compare candidate landing sites. Sun elevation is computed live from today's lunar phase.">
      <div className="grid gap-5 xl:grid-cols-3">
        <div className="grid gap-4 sm:grid-cols-2 xl:col-span-2">
          {SITES.map((s, i) => {
            const elev = sunElevation(s.lat, s.lon, lunar.sunLon);
            const active = i === selected;
            return (
              <button
                key={s.code}
                onClick={() => onSelect(i)}
                className={`rounded-2xl border p-5 text-left transition ${
                  active ? 'border-cyan-300/60 bg-cyan-400/10 shadow-[0_0_30px_rgba(34,211,238,0.15)]' : 'border-white/10 bg-white/[0.04] hover:border-white/25 hover:bg-white/[0.07]'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate font-bold text-white">{s.name}</p>
                    <p className="font-mono text-[11px] text-cyan-300">{s.code}</p>
                  </div>
                  <Pill tone={slopeTone(s.slope)}>{slopeLabel(s.slope)}</Pill>
                </div>
                <p className="mt-3 font-mono text-[11px] text-slate-400">
                  {fmtLat(s.lat)} · {fmtLon(s.lon)}
                </p>
                <div className="mt-4 flex items-end justify-between">
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500">Safety</p>
                    <p className="text-2xl font-extrabold text-white">{s.safety}%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] uppercase tracking-widest text-slate-500">Sun elevation</p>
                    <p className={`font-mono text-lg font-bold ${elev > 0 ? 'text-amber-300' : 'text-slate-500'}`}>{elev.toFixed(1)}°</p>
                  </div>
                </div>
                <div className="mt-3">
                  <Meter value={s.safety} gradient="from-cyan-500 to-emerald-400" />
                </div>
              </button>
            );
          })}
        </div>

        <Panel className="p-5">
          <PanelHeader title="Safety Ranking" />
          <SiteSafetyChart selected={selected} onSelect={onSelect} />
          <p className="mt-4 text-[10px] leading-relaxed text-slate-500">Safety scores are sample data. Connect your own dataset in data.ts.</p>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ============================== TELEMETRY ============================ */
export function TelemetryView({ stream }: { stream: StreamPoint[] }) {
  const last = stream[stream.length - 1];
  const labels = stream.map((p) => p.label);
  const recent = stream.slice(-8).reverse();
  return (
    <ViewShell title="Telemetry" subtitle="Live simulated signal traces (new sample every 3 seconds).">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Bus Power" value={`${last.power} kW`} sub="Photovoltaic array" color="text-cyan-300" icon="bolt" />
        <StatCard label="Signal SNR" value={`${last.snr} dB`} sub="X-band downlink" color="text-emerald-300" icon="pulse" />
        <StatCard label="Avionics Temp" value={`${last.temp} °C`} sub="Internal bay" color="text-amber-300" icon="sun" />
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel className="p-5">
          <PanelHeader title="Bus Power (kW)" />
          <AreaChart id="tp" data={stream.map((p) => p.power)} labels={labels} unit=" kW" height={170} />
        </Panel>
        <Panel className="p-5">
          <PanelHeader title="Signal-to-Noise (dB)" />
          <AreaChart id="ts" data={stream.map((p) => p.snr)} labels={labels} unit=" dB" height={170} color="#34d399" />
        </Panel>
      </div>

      <Panel className="p-5">
        <PanelHeader title="Packet Log" />
        <div className="overflow-x-auto">
          <table className="w-full min-w-[460px] text-left text-xs">
            <thead>
              <tr className="border-b border-white/10 text-[10px] uppercase tracking-widest text-slate-500">
                <th className="py-2 font-semibold">Time</th>
                <th className="py-2 font-semibold">Power</th>
                <th className="py-2 font-semibold">SNR</th>
                <th className="py-2 font-semibold">Temp</th>
              </tr>
            </thead>
            <tbody className="font-mono text-slate-200">
              {recent.map((p, i) => (
                <tr key={`${p.label}-${i}`} className="border-b border-white/5">
                  <td className="py-2 text-slate-400">{p.label}</td>
                  <td className="py-2">{p.power} kW</td>
                  <td className="py-2">{p.snr} dB</td>
                  <td className="py-2">{p.temp} °C</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </ViewShell>
  );
}

/* ========================== POWER & THERMAL ========================== */
export function PowerThermalView({ irradiance }: { irradiance: string }) {
  return (
    <ViewShell title="Power & Thermal" subtitle="Generation, storage and thermal margins.">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Generation" value="4.82 kW" sub="Array output now" color="text-cyan-300" icon="bolt" />
        <StatCard label="Battery SoC" value="92.4%" sub="Reserve for lunar night" color="text-emerald-300" icon="battery" />
        <StatCard label="Solar Irradiance" value={irradiance} sub="From backend (W/m²)" color="text-amber-300" icon="sun" />
        <StatCard label="Avionics" value="22.5 °C" sub="Within thermal limits" color="text-sky-300" icon="pulse" />
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="24-Hour Generation (kW)" />
          <AreaChart id="p24" data={POWER_24H} labels={HOURS_24} unit=" kW" height={200} />
        </Panel>
        <Panel className="flex flex-col items-center p-5">
          <div className="w-full">
            <PanelHeader title="Power Distribution" />
          </div>
          <Donut
            centerValue="4.82"
            centerLabel="kW total"
            segments={[
              { label: 'Comms', value: 38, color: '#22d3ee' },
              { label: 'Thermal', value: 27, color: '#f59e0b' },
              { label: 'Payload', value: 21, color: '#34d399' },
              { label: 'Avionics', value: 14, color: '#a78bfa' },
            ]}
          />
          <div className="mt-4 grid w-full grid-cols-2 gap-2 text-[11px] text-slate-300">
            {[
              ['Comms', 'bg-cyan-400'],
              ['Thermal', 'bg-amber-400'],
              ['Payload', 'bg-emerald-400'],
              ['Avionics', 'bg-violet-400'],
            ].map(([n, c]) => (
              <span key={n} className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${c}`} />
                {n}
              </span>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel className="p-5">
          <PanelHeader title="Last 6 Hours (kW)" />
          <PowerBars height={140} />
        </Panel>
        <Panel className="p-5">
          <PanelHeader title="Subsystem Health" />
          <div className="space-y-4">
            {SUBSYSTEMS.map((s) => (
              <div key={s.label}>
                <div className="mb-1.5 flex justify-between text-xs">
                  <span className="text-slate-300">{s.label}</span>
                  <span className={`font-mono font-bold ${s.text}`}>{s.value}%</span>
                </div>
                <Meter value={s.value} gradient={s.bar} />
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ========================= TERRAIN & HAZARD ========================== */
export function TerrainView({ selected, onSelect }: { selected: number; onSelect: (i: number) => void }) {
  const s = SITES[selected];
  return (
    <ViewShell title="Terrain & Hazard" subtitle="LiDAR-derived hazard metrics per candidate site.">
      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="Hazard Table" />
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-[10px] uppercase tracking-widest text-slate-500">
                  <th className="py-2 font-semibold">Site</th>
                  <th className="py-2 font-semibold">Slope</th>
                  <th className="py-2 font-semibold">Boulders</th>
                  <th className="py-2 font-semibold">Craters</th>
                  <th className="py-2 font-semibold">Rating</th>
                </tr>
              </thead>
              <tbody>
                {SITES.map((r, i) => (
                  <tr
                    key={r.code}
                    onClick={() => onSelect(i)}
                    className={`cursor-pointer border-b border-white/5 transition hover:bg-white/5 ${i === selected ? 'bg-cyan-400/10' : ''}`}
                  >
                    <td className="py-3 pr-3">
                      <p className="font-semibold text-white">{r.name}</p>
                      <p className="font-mono text-[10px] text-slate-500">{r.code}</p>
                    </td>
                    <td className="py-3 pr-3 font-mono text-slate-200">{r.slope}°</td>
                    <td className="py-3 pr-3 font-mono text-slate-200">{r.boulder}%</td>
                    <td className="w-40 py-3 pr-3">
                      <Meter value={r.crater} gradient="from-sky-500 to-violet-500" />
                    </td>
                    <td className="py-3">
                      <Pill tone={slopeTone(r.slope)}>{slopeLabel(r.slope)}</Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel className="p-5">
          <PanelHeader title={`${s.name} · Safety Trend`} />
          <AreaChart id="terr" data={siteSeries(s)} unit="%" height={150} color="#34d399" compact />
          <div className="mt-4 grid grid-cols-2 gap-3 text-[11px]">
            <div className="rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2">
              <p className="text-[9px] uppercase tracking-widest text-slate-500">Crater index</p>
              <p className="font-mono text-sm font-semibold text-slate-100">{s.crater}/100</p>
            </div>
            <div className="rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2">
              <p className="text-[9px] uppercase tracking-widest text-slate-500">Safety</p>
              <p className="font-mono text-sm font-semibold text-slate-100">{s.safety}%</p>
            </div>
          </div>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ========================== MISSION PLANNER ========================== */
export function PlannerView() {
  return (
    <ViewShell title="Mission Planner" subtitle="Operations timeline and milestones.">
      <Panel className="p-5 sm:p-6">
        <ol className="relative space-y-1 border-l border-white/10 pl-6">
          {MISSION.map((m) => (
            <li key={m.name} className="relative pb-5">
              <span
                className={`absolute -left-[31px] top-1 flex h-4 w-4 items-center justify-center rounded-full border-2 border-[#050811] ${
                  m.status === 'Completed' ? 'bg-emerald-400' : m.status === 'In Progress' ? 'animate-pulse bg-cyan-400' : 'bg-slate-600'
                }`}
              />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-semibold text-white">{m.name}</p>
                  <p className="font-mono text-[11px] text-slate-500">
                    <Icon name="clock" className="mr-1 inline h-3 w-3" />
                    {m.when}
                  </p>
                </div>
                <Pill tone={missionTone(m.status)}>{m.status}</Pill>
              </div>
              {m.progress > 0 && (
                <div className="mt-2 max-w-md">
                  <Meter value={m.progress} gradient={m.progress === 100 ? 'from-emerald-500 to-teal-400' : 'from-cyan-500 to-blue-500'} />
                </div>
              )}
            </li>
          ))}
        </ol>
      </Panel>
    </ViewShell>
  );
}
