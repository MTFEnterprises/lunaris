export type TabName =
  | 'Dashboard'
  | 'Site Picker'
  | 'Sky View'
  | 'Sun & Earth Analysis'
  | 'Power Model'
  | 'Thermal Analysis'
  | 'Communication Link'
  | 'Comparison'
  | 'Date Shift'
  | 'Terrain Analysis'
  | 'Hazard Mapping'
  | 'Export Report'
  | 'Mission Planner'
  | 'Settings'
  | 'Help Guide'
  | 'Telemetry';
export type LinkState = 'connecting' | 'online' | 'offline';

export const NAV_ITEMS: { name: TabName; icon: string; desc: string; group: string }[] = [
  { name: 'Dashboard', icon: 'grid', group: 'Overview', desc: 'Backend-derived mission overview' },
  { name: 'Site Picker', icon: 'pin', group: 'Overview', desc: 'Choose a sourced candidate site' },
  { name: 'Sky View', icon: 'sun', group: 'Analysis', desc: 'Sun and Earth orientation' },
  { name: 'Sun & Earth Analysis', icon: 'sun', group: 'Analysis', desc: 'Ephemeris angles and geometry' },
  { name: 'Date Shift', icon: 'clock', group: 'Analysis', desc: 'Change UTC date and inspect visibility windows' },
  { name: 'Comparison', icon: 'route', group: 'Analysis', desc: 'Compare backend-generated scenarios' },
  { name: 'Power Model', icon: 'layers', group: 'Analysis', desc: 'Backend solar power estimate' },
  { name: 'Communication Link', icon: 'route', group: 'Analysis', desc: 'Geometric Earth visibility, not DSN status' },
  { name: 'Terrain Analysis', icon: 'layers', group: 'Terrain', desc: 'DEM-derived terrain layers' },
  { name: 'Hazard Mapping', icon: 'layers', group: 'Terrain', desc: 'Terrain coverage and available hazard metrics' },
  { name: 'Thermal Analysis', icon: 'layers', group: 'Systems', desc: 'Unavailable until validated thermal data is integrated' },
  { name: 'Telemetry', icon: 'list', group: 'Systems', desc: 'No spacecraft telemetry feed is integrated' },
  { name: 'Mission Planner', icon: 'clock', group: 'Output', desc: 'Planning context from backend analysis' },
  { name: 'Export Report', icon: 'list', group: 'Output', desc: 'Generate backend assessment and report' },
  { name: 'Settings', icon: 'grid', group: 'Support', desc: 'Current site, date, and API status' },
  { name: 'Help Guide', icon: 'list', group: 'Support', desc: 'Data status and scientific limitations' },
];

export const DEFAULT_START_UTC = '2027-03-14T00:00:00Z';

export function formatLatitude(value: number | null): string {
  if (value === null) return 'Unavailable';
  return `${Math.abs(value).toFixed(4)}° ${value >= 0 ? 'N' : 'S'}`;
}

export function formatLongitude(value: number | null): string {
  if (value === null) return 'Unavailable';
  return `${Math.abs(value).toFixed(4)}° ${value >= 0 ? 'E' : 'W'}`;
}

export function formatNumber(value: number | null, suffix = ''): string {
  return value === null ? 'Unavailable' : `${value}${suffix}`;
}
