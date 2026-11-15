import { useState } from 'react';
import { ORBIT, SITES, fmtLat, fmtLon } from './data';
import type { StreamPoint, Tone } from './data';
import { sunElevation } from './lunar';
import type { LunarState } from './lunar';
import { useNow } from './hooks';
import { AreaChart, Donut } from './charts';
import { Icon, Meter, Panel, PanelHeader, Pill, StatCard, ViewShell } from './ui';

/* Physical constants of the Moon (real values) */
const MU_MOON = 4902.8; // km^3 / s^2
const R_MOON = 1737.4; // km
const C_LIGHT = 299792.458; // km / s
const EARTH_MOON = 384400; // km (mean distance)

const Mini = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2">
    <p className="text-[9px] uppercase tracking-widest text-slate-500">{label}</p>
    <p className="mt-0.5 font-mono text-sm font-semibold text-slate-100">{value}</p>
  </div>
);

/* ============================ ORBIT TRACKER ========================== */
export function OrbitView() {
  const now = useNow(1000);
  const alt = parseFloat(ORBIT.altitude);
  const a = R_MOON + alt;
  const period = 2 * Math.PI * Math.sqrt(Math.pow(a, 3) / MU_MOON); // seconds
  const speed = Math.sqrt(MU_MOON / a); // km/s
  const phase = ((now.getTime() / 1000) % period) / period;
  const ang = phase * 2 * Math.PI;
  const altSeries = Array.from({ length: 24 }, (_, i) => +(alt + Math.sin((i / 24) * 2 * Math.PI) * 2.4).toFixed(1));
  const labels = Array.from({ length: 24 }, (_, i) => `${Math.round((i / 24) * (period / 60))} min`);

  return (
    <ViewShell title="Orbit Tracker" subtitle="Circular lunar orbit. Period and speed are calculated from real lunar gravity (μ = 4902.8 km³/s²).">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Altitude" value={`${alt.toFixed(1)} km`} sub="Above mean lunar radius" color="text-cyan-300" icon="moon" />
        <StatCard label="Orbital Speed" value={`${speed.toFixed(2)} km/s`} sub="v = √(μ / r)" color="text-emerald-300" icon="pulse" />
        <StatCard label="Period" value={`${(period / 60).toFixed(1)} min`} sub={`${(86400 / period).toFixed(1)} orbits per day`} color="text-sky-300" icon="clock" />
        <StatCard label="Inclination" value={`${ORBIT.inclination}°`} sub="To lunar equator" color="text-amber-300" icon="target" />
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5">
          <PanelHeader title="Live Position" right={<Pill tone="green">Tracking</Pill>} />
          <svg viewBox="0 0 300 300" className="mx-auto w-full max-w-[320px]">
            <defs>
              <radialGradient id="orbMoon" cx="40%" cy="38%" r="70%">
                <stop offset="0%" stopColor="#d4d4d8" />
                <stop offset="100%" stopColor="#52525b" />
              </radialGradient>
            </defs>
            <g transform="rotate(-20 150 150)">
              <ellipse cx="150" cy="150" rx="125" ry="75" fill="none" stroke="rgba(56,189,248,0.45)" strokeDasharray="4 5" />
              <circle cx={150 + 125 * Math.cos(ang)} cy={150 + 75 * Math.sin(ang)} r="6" fill="#fbbf24" />
              <circle cx={150 + 125 * Math.cos(ang)} cy={150 + 75 * Math.sin(ang)} r="12" fill="none" stroke="rgba(251,191,36,0.4)" />
            </g>
            <circle cx="150" cy="150" r="56" fill="url(#orbMoon)" />
          </svg>
          <p className="mt-2 text-center text-[11px] text-slate-500">Orbit progress: {(phase * 100).toFixed(1)}%</p>
        </Panel>

        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="Altitude Profile · one orbit" />
          <AreaChart id="orbalt" data={altSeries} labels={labels} unit=" km" height={200} />
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Mini label="Semi-major axis" value={`${a.toFixed(1)} km`} />
            <Mini label="Lunar radius" value={`${R_MOON} km`} />
            <Mini label="Latency" value={`${ORBIT.latency} s`} />
            <Mini label="Revolutions" value={`${Math.floor((now.getTime() / 1000) / period) % 100000}`} />
          </div>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ============================ COMMUNICATIONS ========================= */
const STATIONS = [
  { name: 'Goldstone (USA)', band: 'X-band 8.4 GHz', window: '02:10 – 09:40 UTC', tone: 'green' as Tone, state: 'In contact' },
  { name: 'Madrid (Spain)', band: 'X-band 8.4 GHz', window: '10:05 – 17:30 UTC', tone: 'slate' as Tone, state: 'Next pass' },
  { name: 'Canberra (Australia)', band: 'X-band 8.4 GHz', window: '18:00 – 01:20 UTC', tone: 'slate' as Tone, state: 'Scheduled' },
];

export function CommsView({ stream }: { stream: StreamPoint[] }) {
  const last = stream[stream.length - 1];
  const oneWay = EARTH_MOON / C_LIGHT;
  const margin = +(last.snr - 10).toFixed(1);
  return (
    <ViewShell title="Communications" subtitle="Deep Space Network link. Light-time is calculated from the real Earth–Moon distance.">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="One-way Light Time" value={`${oneWay.toFixed(3)} s`} sub="384,400 km at c" color="text-cyan-300" icon="signal" />
        <StatCard label="Round Trip" value={`${(oneWay * 2).toFixed(3)} s`} sub="Minimum, no processing" color="text-sky-300" icon="clock" />
        <StatCard label="Signal SNR" value={`${last.snr} dB`} sub="Live (sample stream)" color="text-emerald-300" icon="pulse" />
        <StatCard label="Link Margin" value={`${margin} dB`} sub="Above 10 dB threshold" color={margin >= 10 ? 'text-emerald-300' : 'text-amber-300'} icon="target" />
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="Downlink SNR (dB)" />
          <AreaChart id="commsnr" data={stream.map((p) => p.snr)} labels={stream.map((p) => p.label)} unit=" dB" height={190} color="#34d399" />
        </Panel>
        <Panel className="p-5">
          <PanelHeader title="Link Quality" />
          <div className="space-y-4 text-xs">
            {[
              ['Uplink (command)', 99.1, 'from-cyan-500 to-blue-500'],
              ['Downlink (telemetry)', 98.4, 'from-emerald-500 to-teal-400'],
              ['Packet success', 99.7, 'from-emerald-500 to-teal-400'],
            ].map(([n, v, g]) => (
              <div key={String(n)}>
                <div className="mb-1.5 flex justify-between">
                  <span className="text-slate-300">{n}</span>
                  <span className="font-mono font-bold text-slate-100">{v}%</span>
                </div>
                <Meter value={Number(v)} gradient={String(g)} />
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel className="p-5">
        <PanelHeader title="Ground Station Passes" />
        <div className="grid gap-3 md:grid-cols-3">
          {STATIONS.map((s) => (
            <div key={s.name} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-white">{s.name}</p>
                <Pill tone={s.tone}>{s.state}</Pill>
              </div>
              <p className="mt-2 font-mono text-[11px] text-slate-400">{s.band}</p>
              <p className="font-mono text-[11px] text-slate-500">{s.window}</p>
            </div>
          ))}
        </div>
      </Panel>
    </ViewShell>
  );
}

/* ============================== NAVIGATION =========================== */
const DV = [
  { name: 'Lunar Orbit Insertion', planned: 820, spent: 820 },
  { name: 'Orbit Trim', planned: 60, spent: 54 },
  { name: 'Descent Burn', planned: 1900, spent: 0 },
  { name: 'Hover & Landing', planned: 120, spent: 0 },
  { name: 'Contingency Reserve', planned: 250, spent: 0 },
];

const BURNS = [
  { t: 'T+00:35', name: 'Deorbit burn', tone: 'cyan' as Tone },
  { t: 'T+01:20', name: 'Powered descent initiation', tone: 'slate' as Tone },
  { t: 'T+01:42', name: 'Terrain-relative navigation', tone: 'slate' as Tone },
  { t: 'T+01:49', name: 'Touchdown', tone: 'slate' as Tone },
];

export function NavigationView() {
  const total = DV.reduce((s, d) => s + d.planned, 0);
  const spent = DV.reduce((s, d) => s + d.spent, 0);
  const remaining = Math.round(((total - spent) / total) * 100);
  const descent = Array.from({ length: 24 }, (_, i) => +(ORBIT.altitude ? 108.4 * Math.pow(1 - i / 23, 1.8) : 0).toFixed(1));
  const labels = Array.from({ length: 24 }, (_, i) => `T+${i * 5} s`);
  return (
    <ViewShell title="Navigation & Guidance" subtitle="Delta-v budget and powered-descent profile (sample mission plan).">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Δv Budget" value={`${total} m/s`} sub="Planned for the mission" color="text-cyan-300" icon="compass" />
        <StatCard label="Δv Used" value={`${spent} m/s`} sub="Burns completed" color="text-amber-300" icon="bolt" />
        <StatCard label="Propellant Left" value={`${remaining}%`} sub="Of the Δv budget" color="text-emerald-300" icon="battery" />
        <StatCard label="Trajectory Match" value="99.8%" sub="vs planned descent" color="text-sky-300" icon="route" />
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="Descent Altitude (km)" />
          <AreaChart id="descent" data={descent} labels={labels} unit=" km" height={200} />
        </Panel>
        <Panel className="flex flex-col items-center p-5">
          <div className="w-full">
            <PanelHeader title="Propellant" />
          </div>
          <Donut
            centerValue={`${remaining}%`}
            centerLabel="remaining"
            segments={[
              { label: 'Used', value: Math.max(spent, 1), color: '#f59e0b' },
              { label: 'Left', value: total - spent, color: '#22d3ee' },
            ]}
          />
        </Panel>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel className="p-5">
          <PanelHeader title="Δv Budget" />
          <div className="space-y-4">
            {DV.map((d) => (
              <div key={d.name}>
                <div className="mb-1.5 flex justify-between text-xs">
                  <span className="text-slate-300">{d.name}</span>
                  <span className="font-mono text-slate-400">
                    {d.spent} / {d.planned} m/s
                  </span>
                </div>
                <Meter value={d.spent} max={d.planned} gradient="from-cyan-500 to-blue-500" />
              </div>
            ))}
          </div>
        </Panel>
        <Panel className="p-5">
          <PanelHeader title="Burn Schedule" />
          <ul className="space-y-3">
            {BURNS.map((b) => (
              <li key={b.name} className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-white">{b.name}</p>
                  <p className="font-mono text-[11px] text-slate-500">{b.t}</p>
                </div>
                <Pill tone={b.tone}>{b.tone === 'cyan' ? 'Next' : 'Planned'}</Pill>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* =========================== LANDING SIMULATOR ======================= */
export function LandingSimView({ selected, onSelect, lunar }: { selected: number; onSelect: (i: number) => void; lunar: LunarState }) {
  const [vel, setVel] = useState(1.5);
  const [fuel, setFuel] = useState(35);
  const s = SITES[selected];
  const elev = sunElevation(s.lat, s.lon, lunar.sunLon);

  const pVel = vel > 2 ? (vel - 2) * 8 : 0;
  const pFuel = fuel < 20 ? (20 - fuel) * 1.2 : 0;
  const pLight = elev < 0 ? 18 : elev < 5 ? 8 : 0;
  const score = Math.max(0, Math.min(100, s.safety - pVel - pFuel - pLight));
  const verdict: { label: string; tone: Tone; color: string } =
    score >= 85 ? { label: 'GO', tone: 'green', color: 'text-emerald-300' } : score >= 70 ? { label: 'CAUTION', tone: 'amber', color: 'text-amber-300' } : { label: 'NO-GO', tone: 'rose', color: 'text-rose-300' };

  const rows: [string, number][] = [
    ['Site terrain safety (base)', s.safety],
    ['Touchdown speed penalty', -pVel],
    ['Low fuel penalty', -pFuel],
    ['Poor lighting penalty', -pLight],
  ];

  return (
    <ViewShell title="Landing Simulator" subtitle="Pick a site and tune the descent. The go/no-go score uses the site's terrain safety, your inputs and the live sun elevation.">
      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="1 · Choose site" />
          <div className="flex flex-wrap gap-2">
            {SITES.map((x, i) => (
              <button
                key={x.code}
                onClick={() => onSelect(i)}
                className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                  i === selected ? 'border-cyan-300/60 bg-cyan-400/15 text-cyan-200' : 'border-white/10 bg-white/5 text-slate-300 hover:border-white/25'
                }`}
              >
                {x.name}
              </button>
            ))}
          </div>

          <div className="mt-6">
            <PanelHeader title="2 · Descent settings" />
            <div className="grid gap-6 md:grid-cols-2">
              <label className="block">
                <div className="mb-2 flex justify-between text-xs">
                  <span className="text-slate-300">Touchdown speed</span>
                  <span className="font-mono font-bold text-cyan-300">{vel.toFixed(1)} m/s</span>
                </div>
                <input type="range" min={0.5} max={5} step={0.1} value={vel} onChange={(e) => setVel(Number(e.target.value))} className="w-full accent-cyan-400" />
                <p className="mt-1 text-[10px] text-slate-500">Safe limit: 2.0 m/s</p>
              </label>
              <label className="block">
                <div className="mb-2 flex justify-between text-xs">
                  <span className="text-slate-300">Fuel reserve at touchdown</span>
                  <span className="font-mono font-bold text-cyan-300">{fuel}%</span>
                </div>
                <input type="range" min={0} max={60} step={1} value={fuel} onChange={(e) => setFuel(Number(e.target.value))} className="w-full accent-cyan-400" />
                <p className="mt-1 text-[10px] text-slate-500">Recommended: 20% or more</p>
              </label>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Mini label="Latitude" value={fmtLat(s.lat)} />
            <Mini label="Longitude" value={fmtLon(s.lon)} />
            <Mini label="Slope" value={`${s.slope}°`} />
            <Mini label="Sun elevation" value={`${elev.toFixed(1)}°`} />
          </div>
        </Panel>

        <Panel className="p-5">
          <PanelHeader title="3 · Result" right={<Pill tone={verdict.tone}>{verdict.label}</Pill>} />
          <p className={`text-5xl font-extrabold ${verdict.color}`}>
            {score.toFixed(0)}
            <span className="text-xl text-slate-500">/100</span>
          </p>
          <div className="mt-3">
            <Meter value={score} gradient={score >= 85 ? 'from-emerald-500 to-teal-400' : score >= 70 ? 'from-amber-500 to-orange-500' : 'from-rose-500 to-red-500'} />
          </div>
          <ul className="mt-5 space-y-2 text-xs">
            {rows.map(([n, v]) => (
              <li key={n} className="flex justify-between gap-3 border-b border-white/5 pb-2">
                <span className="text-slate-400">{n}</span>
                <span className={`font-mono font-semibold ${v < 0 ? 'text-rose-300' : 'text-slate-100'}`}>{v > 0 ? v.toFixed(1) : v.toFixed(1)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-[10px] leading-relaxed text-slate-500">Simplified scoring model for demonstration. Not flight software.</p>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ================================ ROVER ============================== */
const ROVER_TASKS = [
  { name: 'Egress from lander', progress: 100, status: 'Done', tone: 'green' as Tone },
  { name: 'Drive to Waypoint A (320 m)', progress: 64, status: 'Running', tone: 'cyan' as Tone },
  { name: 'Regolith sample #1', progress: 0, status: 'Queued', tone: 'slate' as Tone },
  { name: 'Panoramic imaging', progress: 0, status: 'Queued', tone: 'slate' as Tone },
];

export function RoverView() {
  const battery = Array.from({ length: 18 }, (_, i) => +(96 - i * 0.9 + Math.sin(i / 2) * 0.8).toFixed(1));
  return (
    <ViewShell title="Rover Operations" subtitle="Surface rover status and task queue (sample data).">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Battery" value={`${battery[battery.length - 1]}%`} sub="Discharging slowly" color="text-emerald-300" icon="battery" />
        <StatCard label="Distance Driven" value="214 m" sub="Since deployment" color="text-cyan-300" icon="route" />
        <StatCard label="Speed" value="4.2 cm/s" sub="Autonomous drive" color="text-sky-300" icon="rover" />
        <StatCard label="Wheel Temp" value="−18 °C" sub="Within limits" color="text-amber-300" icon="sun" />
      </div>
      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="Battery Level (%)" />
          <AreaChart id="rover" data={battery} unit="%" height={190} color="#34d399" />
        </Panel>
        <Panel className="p-5">
          <PanelHeader title="Task Queue" />
          <ul className="space-y-4">
            {ROVER_TASKS.map((t) => (
              <li key={t.name}>
                <div className="mb-1.5 flex items-center justify-between gap-2">
                  <p className="truncate text-xs font-semibold text-white">{t.name}</p>
                  <Pill tone={t.tone}>{t.status}</Pill>
                </div>
                <Meter value={t.progress} gradient="from-cyan-500 to-blue-500" />
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* =============================== PAYLOADS ============================ */
const INSTRUMENTS = [
  { name: 'LiDAR Altimeter', power: 38, data: 420, tone: 'green' as Tone, state: 'Active', color: '#22d3ee' },
  { name: 'Neutron Spectrometer', power: 22, data: 90, tone: 'green' as Tone, state: 'Active', color: '#34d399' },
  { name: 'Ground Penetrating Radar', power: 45, data: 310, tone: 'amber' as Tone, state: 'Warming up', color: '#f59e0b' },
  { name: 'Panoramic Camera', power: 18, data: 640, tone: 'green' as Tone, state: 'Active', color: '#a78bfa' },
  { name: 'Seismometer', power: 6, data: 12, tone: 'slate' as Tone, state: 'Standby', color: '#f472b6' },
];

export function PayloadsView() {
  const totalData = INSTRUMENTS.reduce((s, i) => s + i.data, 0);
  const totalPower = INSTRUMENTS.reduce((s, i) => s + i.power, 0);
  return (
    <ViewShell title="Science Payloads" subtitle="Instrument status, power draw and data volume (sample data).">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Instruments" value={`${INSTRUMENTS.length}`} sub="On the payload bus" color="text-cyan-300" icon="flask" />
        <StatCard label="Payload Power" value={`${totalPower} W`} sub="Combined draw" color="text-amber-300" icon="bolt" />
        <StatCard label="Data Today" value={`${totalData} MB`} sub="Queued for downlink" color="text-emerald-300" icon="signal" />
      </div>
      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="Instruments" />
          <div className="space-y-3">
            {INSTRUMENTS.map((i) => (
              <div key={i.name} className="flex items-center justify-between gap-3 rounded-xl border border-white/5 bg-white/[0.03] px-4 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white">{i.name}</p>
                  <p className="font-mono text-[11px] text-slate-500">
                    {i.power} W · {i.data} MB
                  </p>
                </div>
                <Pill tone={i.tone}>{i.state}</Pill>
              </div>
            ))}
          </div>
        </Panel>
        <Panel className="flex flex-col items-center p-5">
          <div className="w-full">
            <PanelHeader title="Data Share" />
          </div>
          <Donut centerValue={`${totalData}`} centerLabel="MB total" segments={INSTRUMENTS.map((i) => ({ label: i.name, value: i.data, color: i.color }))} />
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ============================== RESOURCES ============================ */
// Sample prospecting estimates per site (same order as SITES)
const RESOURCES = [
  { ice: 0.4, ilmenite: 14, he3: 12 },
  { ice: 0.9, ilmenite: 9, he3: 8 },
  { ice: 1.6, ilmenite: 5, he3: 4 },
  { ice: 0.6, ilmenite: 11, he3: 10 },
  { ice: 5.6, ilmenite: 2, he3: 2 },
];

export function ResourcesView({ selected, onSelect }: { selected: number; onSelect: (i: number) => void }) {
  const r = RESOURCES[selected];
  const s = SITES[selected];
  return (
    <ViewShell title="Resource Prospecting" subtitle="Estimated water-ice, ilmenite and helium-3 per site (illustrative sample values).">
      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="Water Ice (% by mass)" />
          <div className="space-y-4">
            {SITES.map((x, i) => (
              <button key={x.code} onClick={() => onSelect(i)} className="block w-full text-left">
                <div className="mb-1.5 flex justify-between text-xs">
                  <span className={i === selected ? 'font-semibold text-cyan-300' : 'text-slate-300'}>{x.name}</span>
                  <span className="font-mono font-bold text-slate-100">{RESOURCES[i].ice}%</span>
                </div>
                <Meter value={RESOURCES[i].ice} max={6} gradient="from-sky-500 to-cyan-300" />
              </button>
            ))}
          </div>
        </Panel>
        <Panel className="p-5">
          <PanelHeader title={s.name} right={<Pill tone="cyan">Selected</Pill>} />
          <div className="space-y-4 text-xs">
            <div>
              <div className="mb-1.5 flex justify-between">
                <span className="text-slate-300">Ilmenite (TiO₂ rich)</span>
                <span className="font-mono font-bold text-slate-100">{r.ilmenite}%</span>
              </div>
              <Meter value={r.ilmenite} max={20} gradient="from-amber-500 to-orange-500" />
            </div>
            <div>
              <div className="mb-1.5 flex justify-between">
                <span className="text-slate-300">Helium-3 (ppb)</span>
                <span className="font-mono font-bold text-slate-100">{r.he3}</span>
              </div>
              <Meter value={r.he3} max={15} gradient="from-violet-500 to-fuchsia-500" />
            </div>
            <div className="grid grid-cols-2 gap-3 pt-2">
              <Mini label="Latitude" value={fmtLat(s.lat)} />
              <Mini label="Safety" value={`${s.safety}%`} />
            </div>
          </div>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ============================== RADIATION ============================ */
export function RadiationView() {
  const dose = Array.from({ length: 24 }, (_, i) => +(57 + Math.sin(i / 3) * 4 + Math.cos(i / 1.7) * 2).toFixed(1));
  const labels = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
  const current = dose[dose.length - 1];
  return (
    <ViewShell title="Radiation & Space Weather" subtitle="Surface dose rate. The Moon has no atmosphere, so about 57 µSv/h is typical (sample values around that level).">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Dose Rate" value={`${current} µSv/h`} sub="Surface dosimeter" color="text-cyan-300" icon="shield" />
        <StatCard label="Daily Dose" value={`${((current * 24) / 1000).toFixed(2)} mSv`} sub="Projected for 24 h" color="text-amber-300" icon="sun" />
        <StatCard label="Solar Activity" value="Quiet" sub="No flare in last 24 h" color="text-emerald-300" icon="pulse" />
        <StatCard label="Shelter Status" value="Not needed" sub="Below alert level" color="text-sky-300" icon="shield" />
      </div>
      <div className="grid gap-5 xl:grid-cols-3">
        <Panel className="p-5 xl:col-span-2">
          <PanelHeader title="Dose Rate · 24 h (µSv/h)" />
          <AreaChart id="rad" data={dose} labels={labels} unit=" µSv/h" height={200} color="#f59e0b" />
        </Panel>
        <Panel className="p-5">
          <PanelHeader title="Alert Levels" />
          <div className="space-y-4 text-xs">
            {[
              ['Normal (< 80 µSv/h)', 'from-emerald-500 to-teal-400', Math.min(100, (current / 80) * 100)],
              ['Elevated (80 – 200)', 'from-amber-500 to-orange-500', 0],
              ['Shelter (> 200)', 'from-rose-500 to-red-500', 0],
            ].map(([n, g, v]) => (
              <div key={String(n)}>
                <div className="mb-1.5 text-slate-300">{n}</div>
                <Meter value={Number(v)} gradient={String(g)} />
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ============================= LIFE SUPPORT ========================== */
const LIFE = [
  { label: 'Oxygen (O₂)', value: '20.9%', pct: 99, gradient: 'from-emerald-500 to-teal-400' },
  { label: 'Carbon dioxide (CO₂)', value: '0.04%', pct: 8, gradient: 'from-cyan-500 to-blue-500' },
  { label: 'Cabin pressure', value: '101.3 kPa', pct: 100, gradient: 'from-emerald-500 to-teal-400' },
  { label: 'Water reserve', value: '82%', pct: 82, gradient: 'from-sky-500 to-cyan-300' },
  { label: 'Humidity', value: '45%', pct: 45, gradient: 'from-cyan-500 to-blue-500' },
];

export function LifeSupportView() {
  const temp = Array.from({ length: 24 }, (_, i) => +(22 + Math.sin(i / 4) * 0.5).toFixed(2));
  const labels = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
  return (
    <ViewShell title="Life Support" subtitle="Habitat atmosphere and consumables (sample data).">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Cabin Temp" value="22.0 °C" sub="Setpoint 22 °C" color="text-cyan-300" icon="sun" />
        <StatCard label="Oxygen" value="20.9%" sub="Nominal" color="text-emerald-300" icon="life" />
        <StatCard label="Crew On Board" value="0 / 4" sub="Uncrewed phase" color="text-sky-300" icon="rover" />
        <StatCard label="Scrubber Load" value="12%" sub="CO₂ removal" color="text-amber-300" icon="pulse" />
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel className="p-5">
          <PanelHeader title="Atmosphere & Consumables" />
          <div className="space-y-4">
            {LIFE.map((l) => (
              <div key={l.label}>
                <div className="mb-1.5 flex justify-between text-xs">
                  <span className="text-slate-300">{l.label}</span>
                  <span className="font-mono font-bold text-slate-100">{l.value}</span>
                </div>
                <Meter value={l.pct} gradient={l.gradient} />
              </div>
            ))}
          </div>
        </Panel>
        <Panel className="p-5">
          <PanelHeader title="Cabin Temperature · 24 h (°C)" />
          <AreaChart id="cabin" data={temp} labels={labels} unit=" °C" height={200} />
        </Panel>
      </div>
    </ViewShell>
  );
}

/* ============================= ALERTS & LOGS ========================= */
type Sev = 'Info' | 'Warning' | 'Critical';
const SEV_TONE: Record<Sev, Tone> = { Info: 'cyan', Warning: 'amber', Critical: 'rose' };
const LOGS: { minAgo: number; sev: Sev; system: string; msg: string }[] = [
  { minAgo: 2, sev: 'Info', system: 'COMMS', msg: 'Downlink pass started with Goldstone.' },
  { minAgo: 9, sev: 'Info', system: 'NAV', msg: 'Orbit trim verified, error 0.2 m/s.' },
  { minAgo: 17, sev: 'Warning', system: 'THERMAL', msg: 'Radiator louver at 88% efficiency.' },
  { minAgo: 26, sev: 'Info', system: 'POWER', msg: 'Battery charge reached 92.4%.' },
  { minAgo: 41, sev: 'Warning', system: 'PAYLOAD', msg: 'GPR warm-up taking longer than expected.' },
  { minAgo: 58, sev: 'Info', system: 'LIDAR', msg: 'Surface scan 72% complete.' },
  { minAgo: 77, sev: 'Critical', system: 'COMMS', msg: 'Uplink dropped for 4 s, auto-recovered.' },
  { minAgo: 95, sev: 'Info', system: 'ROVER', msg: 'Waypoint A route approved.' },
  { minAgo: 130, sev: 'Warning', system: 'RAD', msg: 'Dose rate briefly above 70 µSv/h.' },
  { minAgo: 180, sev: 'Info', system: 'SYS', msg: 'Daily self-test passed.' },
];

export function AlertsView() {
  const now = useNow(60000);
  const [filter, setFilter] = useState<'All' | Sev>('All');
  const shown = LOGS.filter((l) => filter === 'All' || l.sev === filter);
  const count = (s: Sev) => LOGS.filter((l) => l.sev === s).length;
  return (
    <ViewShell title="Alerts & Logs" subtitle="Recent system events (sample log). Times are relative to now.">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Info" value={`${count('Info')}`} sub="Routine events" color="text-cyan-300" icon="list" />
        <StatCard label="Warnings" value={`${count('Warning')}`} sub="Needs attention" color="text-amber-300" icon="bell" />
        <StatCard label="Critical" value={`${count('Critical')}`} sub="Auto-recovered" color="text-rose-300" icon="shield" />
      </div>
      <Panel className="p-5">
        <div className="mb-4 flex flex-wrap gap-2">
          {(['All', 'Info', 'Warning', 'Critical'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
                filter === f ? 'border-cyan-300/60 bg-cyan-400/15 text-cyan-200' : 'border-white/10 bg-white/5 text-slate-400 hover:text-white'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <ul className="divide-y divide-white/5">
          {shown.map((l) => (
            <li key={`${l.minAgo}-${l.system}`} className="flex flex-wrap items-center gap-3 py-3 text-xs">
              <span className="w-14 font-mono text-slate-500">{new Date(now.getTime() - l.minAgo * 60000).toISOString().slice(11, 16)}</span>
              <Pill tone={SEV_TONE[l.sev]}>{l.sev}</Pill>
              <span className="w-20 font-mono font-semibold text-cyan-300">{l.system}</span>
              <span className="min-w-0 flex-1 text-slate-300">
                <Icon name="arrow" className="mr-1 inline h-3 w-3 text-slate-600" />
                {l.msg}
              </span>
            </li>
          ))}
        </ul>
      </Panel>
    </ViewShell>
  );
}
