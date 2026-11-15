/* ================================================================== */
/*  Types and sample data used across the LUNARIS dashboard            */
/*  (Replace the sample arrays with your own API data when ready.)     */
/* ================================================================== */

export type TabName =
  | 'Dashboard'
  | 'Site Picker'
  | 'Orbit Tracker'
  | 'Navigation'
  | 'Landing Simulator'
  | 'Rover Ops'
  | 'Mission Planner'
  | 'Telemetry'
  | 'Communications'
  | 'Power & Thermal'
  | 'Life Support'
  | 'Radiation'
  | 'Terrain & Hazard'
  | 'Science Payloads'
  | 'Resources'
  | 'Alerts & Logs';

export type Tone = 'green' | 'amber' | 'rose' | 'cyan' | 'slate';
export type LinkState = 'connecting' | 'online' | 'offline';
export type ToastType = 'success' | 'info';

// Shape of the backend response (all optional, the UI has safe fallbacks)
export interface LunarData {
  mission?: string;
  epoch?: string;
  telemetry?: { solarIrradiance?: string | number };
}

export interface Site {
  code: string;
  name: string;
  lat: number;
  lon: number;
  safety: number; // landing safety score, %
  slope: number; // degrees
  boulder: number; // % of area covered by boulders
  crater: number; // crater density index 0-100
}

export interface Toast {
  id: number;
  title: string;
  message: string;
  type: ToastType;
}

export interface StreamPoint {
  label: string;
  power: number;
  snr: number;
  temp: number;
}

/* ---------------------------- navigation --------------------------- */
export const NAV_ITEMS: { name: TabName; icon: string; desc: string; group: string; live?: boolean }[] = [
  { name: 'Dashboard', icon: 'grid', group: 'Overview', desc: 'Mission overview and 3D lunar globe', live: true },
  { name: 'Site Picker', icon: 'pin', group: 'Overview', desc: 'Compare candidate landing sites' },
  { name: 'Orbit Tracker', icon: 'orbit', group: 'Operations', desc: 'Live orbit position, period and speed' },
  { name: 'Navigation', icon: 'compass', group: 'Operations', desc: 'Delta-v budget and descent profile' },
  { name: 'Landing Simulator', icon: 'rocket', group: 'Operations', desc: 'Interactive go / no-go landing check' },
  { name: 'Rover Ops', icon: 'rover', group: 'Operations', desc: 'Surface rover status and tasks' },
  { name: 'Mission Planner', icon: 'calendar', group: 'Operations', desc: 'Operations timeline and milestones' },
  { name: 'Telemetry', icon: 'pulse', group: 'Systems', desc: 'Live signal traces and packet log' },
  { name: 'Communications', icon: 'signal', group: 'Systems', desc: 'Deep Space Network link and light-time' },
  { name: 'Power & Thermal', icon: 'bolt', group: 'Systems', desc: 'Generation, storage and thermal margins' },
  { name: 'Life Support', icon: 'life', group: 'Systems', desc: 'Habitat atmosphere and consumables' },
  { name: 'Radiation', icon: 'shield', group: 'Systems', desc: 'Surface dose rate and space weather' },
  { name: 'Terrain & Hazard', icon: 'mountain', group: 'Science', desc: 'LiDAR hazard metrics per site' },
  { name: 'Science Payloads', icon: 'flask', group: 'Science', desc: 'Instrument status and data volume' },
  { name: 'Resources', icon: 'layers', group: 'Science', desc: 'Water-ice and mineral prospecting' },
  { name: 'Alerts & Logs', icon: 'list', group: 'Monitoring', desc: 'System events and warnings' },
];

/* ------------------------------ globe ------------------------------ */
export const HOME_ZOOM = 3.2;

export const SITES: Site[] = [
  { code: 'SITE-ALPHA', name: 'Mare Tranquillitatis', lat: 0.67, lon: 23.47, safety: 96.4, slope: 3.2, boulder: 0.2, crater: 14 },
  { code: 'SITE-BETA', name: 'Oceanus Procellarum', lat: 18.4, lon: -57.4, safety: 88.2, slope: 5.8, boulder: 1.1, crater: 28 },
  { code: 'SITE-GAMMA', name: 'South Pole-Aitken', lat: -53.0, lon: -169.0, safety: 74.5, slope: 9.4, boulder: 3.8, crater: 61 },
  { code: 'SITE-DELTA', name: 'Mare Imbrium', lat: 32.8, lon: -15.6, safety: 91.3, slope: 4.1, boulder: 0.7, crater: 22 },
  { code: 'SITE-EPSILON', name: 'Shackleton Rim', lat: -88.5, lon: 0, safety: 68.9, slope: 11.6, boulder: 4.4, crater: 78 },
];

export const ORBIT = { altitude: '108.4', velocity: '1.63', inclination: '28.5', latency: '2.68' };

/* ------------------------------ charts ----------------------------- */
export const POWER_HOURS = [
  { label: 'T-5H', kw: 2.25 },
  { label: 'T-4H', kw: 3.4 },
  { label: 'T-3H', kw: 2.6 },
  { label: 'T-2H', kw: 4.25 },
  { label: 'T-1H', kw: 3.7 },
  { label: 'NOW', kw: 4.82 },
];

export const HOURS_24 = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
export const POWER_24H = Array.from({ length: 24 }, (_, i) =>
  +(4.2 + Math.sin(i / 3.5) * 0.5 + Math.cos(i / 1.6) * 0.15).toFixed(2)
);

export const SUBSYSTEMS = [
  { label: 'X-Band Deep Space Comms', value: 98.4, bar: 'from-cyan-500 to-blue-500', text: 'text-cyan-400' },
  { label: 'Terrain Hazard Avoidance', value: 100, bar: 'from-emerald-500 to-teal-400', text: 'text-emerald-400' },
  { label: 'Thermal Radiator Efficiency', value: 88, bar: 'from-amber-500 to-orange-500', text: 'text-amber-400' },
];

export const MISSION = [
  { name: 'Launch & Trans-Lunar Injection', when: 'T-12:00:00', status: 'Completed', progress: 100, home: false },
  { name: 'Lunar Orbit Insertion', when: 'T-02:10:00', status: 'Completed', progress: 100, home: true },
  { name: 'Surface LiDAR Scan', when: 'Running now', status: 'In Progress', progress: 72, home: true },
  { name: 'Landing Site Certification', when: 'T+02:00:00', status: 'Scheduled', progress: 0, home: false },
  { name: 'Rover Deployment', when: 'T+04:30:00', status: 'Scheduled', progress: 0, home: true },
  { name: 'Regolith Sampling', when: 'T+12:00:00', status: 'Scheduled', progress: 0, home: false },
  { name: 'Lunar Night Survival Prep', when: 'T+96:00:00', status: 'Scheduled', progress: 0, home: false },
];

export const INSIGHTS: { icon: string; title: string; chip: string; tone: Tone; text: string }[] = [
  {
    icon: 'route',
    title: 'Descent Trajectory',
    chip: '99.8% Match',
    tone: 'green',
    text: 'Orbital insertion vector aligned with Site Alpha. Zero propellant correction required.',
  },
  {
    icon: 'sun',
    title: 'Solar Flux Peak',
    chip: '+120°C Surface',
    tone: 'amber',
    text: 'Radiator louvers operating at 88% efficiency. Internal avionics stable at 22.5°C.',
  },
  {
    icon: 'battery',
    title: 'Battery Reserve (SoC)',
    chip: '92.4% Charged',
    tone: 'cyan',
    text: 'Photovoltaic array generating 4.8 kW surplus power for the upcoming lunar night cycle.',
  },
];

/* ----------------------------- helpers ----------------------------- */
export const missionTone = (s: string): Tone => (s === 'Completed' ? 'green' : s === 'In Progress' ? 'cyan' : 'slate');
export const slopeTone = (s: number): Tone => (s < 6 ? 'green' : s < 10 ? 'amber' : 'rose');
export const slopeLabel = (s: number) => (s < 6 ? 'Safe' : s < 10 ? 'Caution' : 'Hazard');

export const fmtLat = (v: number) => `${Math.abs(v).toFixed(2)}° ${v >= 0 ? 'N' : 'S'}`;
export const fmtLon = (v: number) => `${Math.abs(v).toFixed(2)}° ${v >= 0 ? 'E' : 'W'}`;

export const siteSeries = (s: Site) =>
  Array.from({ length: 18 }, (_, i) => Math.min(99.9, +(s.safety + Math.sin(i / 2.2 + s.slope) * 1.6).toFixed(1)));

export const makePoint = (n: number, ts: number): StreamPoint => ({
  label: new Date(ts).toLocaleTimeString('en-GB'),
  power: +(4.8 + Math.sin(n / 4) * 0.25 + Math.cos(n / 2.3) * 0.08).toFixed(2),
  snr: +(24.5 + Math.sin(n / 5) * 0.8).toFixed(1),
  temp: +(22.5 + Math.sin(n / 9) * 0.4).toFixed(1),
});
