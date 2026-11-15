/**
 * Real lunar calculations (computed from the current date, no backend needed).
 *
 * Model: mean synodic month (29.530588853 days) counted from a known new moon.
 * Accuracy: the Moon's true phase differs from this mean model by up to about
 * +/- 14 hours, which is fine for a mission-control display.
 *
 * Sun position on the Moon: the sub-solar point sits on the lunar equator and
 * its selenographic longitude moves west by 360 degrees per synodic month:
 *   new moon -> 180, first quarter -> +90, full moon -> 0, last quarter -> -90.
 * (Real sub-solar latitude varies only about +/- 1.5 degrees, ignored here.)
 */

export const SYNODIC = 29.530588853; // days
const REF_NEW_MOON_JD = 2451550.26; // new moon of 2000-01-06 18:14 UTC

export interface LunarState {
  age: number; // days since last new moon
  fraction: number; // 0..1 through the cycle
  illumination: number; // % of the visible disc that is lit
  name: string;
  waxing: boolean;
  sunLon: number; // sub-solar selenographic longitude, degrees (east positive)
  nextNew: Date;
  nextFull: Date;
}

export function julianDay(d: Date) {
  return d.getTime() / 86400000 + 2440587.5;
}

/** Wrap an angle to the range (-180, 180]. */
export function wrap180(v: number) {
  const x = (((v + 180) % 360) + 360) % 360 - 180;
  return x === -180 ? 180 : x;
}

export function phaseName(f: number) {
  if (f < 0.03 || f >= 0.97) return 'New Moon';
  if (f < 0.22) return 'Waxing Crescent';
  if (f < 0.28) return 'First Quarter';
  if (f < 0.47) return 'Waxing Gibbous';
  if (f < 0.53) return 'Full Moon';
  if (f < 0.72) return 'Waning Gibbous';
  if (f < 0.78) return 'Last Quarter';
  return 'Waning Crescent';
}

export function computeLunar(date: Date): LunarState {
  const age = (((julianDay(date) - REF_NEW_MOON_JD) % SYNODIC) + SYNODIC) % SYNODIC;
  const fraction = age / SYNODIC;
  const illumination = ((1 - Math.cos(2 * Math.PI * fraction)) / 2) * 100;
  const daysToNew = SYNODIC - age;
  const daysToFull = fraction < 0.5 ? SYNODIC / 2 - age : SYNODIC * 1.5 - age;
  return {
    age,
    fraction,
    illumination,
    name: phaseName(fraction),
    waxing: fraction < 0.5,
    sunLon: wrap180(180 - 360 * fraction),
    nextNew: new Date(date.getTime() + daysToNew * 86400000),
    nextFull: new Date(date.getTime() + daysToFull * 86400000),
  };
}

/** Elevation of the Sun above the local horizon at a lunar surface point (degrees). */
export function sunElevation(lat: number, lon: number, sunLon: number, sunLat = 0) {
  const r = Math.PI / 180;
  const s =
    Math.sin(lat * r) * Math.sin(sunLat * r) +
    Math.cos(lat * r) * Math.cos(sunLat * r) * Math.cos((lon - sunLon) * r);
  return Math.asin(Math.max(-1, Math.min(1, s))) / r;
}

export interface SunEvent {
  kind: 'sunset' | 'sunrise';
  days: number;
}

/** Time until the next sunset (if it is day) or sunrise (if it is night) at a longitude. */
export function nextSunEvent(lon: number, sunLon: number): SunEvent {
  const rate = 360 / SYNODIC; // degrees of sun motion per day
  const d = wrap180(lon - sunLon); // grows with time
  const isDay = Math.abs(d) < 90;
  const target = isDay ? 90 : -90;
  const delta = (((target - d) % 360) + 360) % 360;
  return { kind: isDay ? 'sunset' : 'sunrise', days: delta / rate };
}

export function formatDuration(days: number) {
  const totalH = Math.max(0, Math.round(days * 24));
  const d = Math.floor(totalH / 24);
  const h = totalH % 24;
  return d > 0 ? `${d} d ${h} h` : `${h} h`;
}

export function formatShortDate(d: Date) {
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
}
