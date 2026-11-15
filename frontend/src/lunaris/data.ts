export type TabName = 'Dashboard' | 'Site Picker' | 'Sky View' | 'Timeline' | 'Compare' | 'Map' | 'Report';
export type LinkState = 'connecting' | 'online' | 'offline';

export const NAV_ITEMS: { name: TabName; icon: string; desc: string; group: string }[] = [
  { name: 'Dashboard', icon: 'grid', group: 'Overview', desc: 'Mission overview and selected site' },
  { name: 'Site Picker', icon: 'pin', group: 'Overview', desc: 'Choose a curated south-pole candidate' },
  { name: 'Sky View', icon: 'sun', group: 'Analysis', desc: 'Sun and Earth geometry' },
  { name: 'Timeline', icon: 'clock', group: 'Analysis', desc: 'Illumination and communication windows' },
  { name: 'Compare', icon: 'route', group: 'Analysis', desc: 'Compare scenarios and date shifts' },
  { name: 'Map', icon: 'layers', group: 'Terrain', desc: 'DEM-derived map layers' },
  { name: 'Report', icon: 'list', group: 'Output', desc: 'Assessment and provenance report' },
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
