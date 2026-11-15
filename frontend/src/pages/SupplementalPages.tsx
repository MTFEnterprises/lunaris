import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { ApiError, getCommunication, getThermalAnalysis } from '../api/client';
import type {
  Envelope,
  EphemerisData,
  PowerEstimateData,
  ScenarioData,
  Site,
  TerrainSlopeData,
} from '../api/types';
import type { LinkState, TabName } from '../lunaris/data';
import ErrorState from '../components/ErrorState';
import Loading from '../components/Loading';
import ProvenanceBadge from '../components/ProvenanceBadge';
import Unavailable from '../components/Unavailable';
import MapConnected from './MapConnected';

export type SupplementalTab = Exclude<
  TabName,
  'Dashboard' | 'Site Picker' | 'Sky View' | 'Date Shift' | 'Comparison' | 'Terrain Analysis' | 'Export Report'
>;

export function getSupplementalTab(tab: TabName): SupplementalTab | null {
  switch (tab) {
    case 'Sun & Earth Analysis':
    case 'Power Model':
    case 'Thermal Analysis':
    case 'Communication Link':
    case 'Hazard Mapping':
    case 'Mission Planner':
    case 'Settings':
    case 'Help Guide':
    case 'Telemetry':
      return tab;
    default:
      return null;
  }
}

export default function SupplementalPage({
  tab,
  site,
  startUtc,
  link,
  ephemeris,
  timeline,
  powerEstimate,
  slopeEstimate,
}: {
  tab: SupplementalTab;
  site: Site | null;
  startUtc: string;
  link: LinkState;
  ephemeris: Envelope<EphemerisData> | null;
  timeline: Envelope<ScenarioData> | null;
  powerEstimate: Envelope<PowerEstimateData> | null;
  slopeEstimate: Envelope<TerrainSlopeData> | null;
}) {
  switch (tab) {
    case 'Sun & Earth Analysis':
      return <SunEarthAnalysis ephemeris={ephemeris} />;
    case 'Power Model':
      return <PowerModel estimate={powerEstimate} />;
    case 'Thermal Analysis':
      return <ThermalAnalysis site={site} />;
    case 'Communication Link':
      return <CommunicationLink site={site} startUtc={startUtc} />;
    case 'Hazard Mapping':
      return <HazardMapping site={site} slope={slopeEstimate} />;
    case 'Mission Planner':
      return <MissionPlanner timeline={timeline} powerEstimate={powerEstimate} />;
    case 'Settings':
      return <Settings site={site} startUtc={startUtc} link={link} ephemeris={ephemeris} />;
    case 'Help Guide':
      return <HelpGuide />;
    case 'Telemetry':
      return <UnavailablePage title="Telemetry" reason="No spacecraft or rover telemetry feed is connected to this backend." />;
  }
}

function SunEarthAnalysis({ ephemeris }: { ephemeris: Envelope<EphemerisData> | null }) {
  return (
    <Page
      title="Sun & Earth Analysis"
      subtitle="Backend ephemeris angles in the local horizon frame. Geometric visibility is not terrain clearance or a radio-link status."
    >
      {ephemeris ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric label="Sun elevation / azimuth" value={angleText(ephemeris.data.sun)} />
            <Metric label="Earth elevation / azimuth" value={angleText(ephemeris.data.earth)} />
            <Metric label="Frame" value={ephemeris.data.frame} />
            <Metric label="UTC instant" value={ephemeris.data.time_utc} />
          </div>
          <ProvenanceBadge provenance={ephemeris.provenance} cached={ephemeris.cached} warnings={ephemeris.warnings} />
        </>
      ) : <Unavailable label="Ephemeris data unavailable" />}
    </Page>
  );
}

function PowerModel({ estimate }: { estimate: Envelope<PowerEstimateData> | null }) {
  return (
    <Page
      title="Power Model"
      subtitle="Backend solar-power estimate. This is a model output, not lander telemetry or measured panel performance."
    >
      {estimate ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric label="Peak output" value={format(estimate.data.peak_w, ' W')} />
            <Metric label="Energy over interval" value={format(estimate.data.energy_wh, ' Wh')} />
            <Metric label="UTC start" value={estimate.data.start_utc} />
            <Metric label="Sample interval" value={`${estimate.data.step_min} min`} />
            <Metric
              label="Available samples"
              value={`${estimate.data.power_w.filter((value) => value !== null).length} / ${estimate.data.power_w.length}`}
            />
          </div>
          <ProvenanceBadge provenance={estimate.provenance} cached={estimate.cached} warnings={estimate.warnings} />
        </>
      ) : <Unavailable label="Power estimate unavailable" />}
    </Page>
  );
}

function CommunicationLink({ site, startUtc }: { site: Site | null; startUtc: string }) {
  const [communication, setCommunication] = useState<Envelope<ScenarioData> | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(Boolean(site));

  useEffect(() => {
    if (!site) {
      setCommunication(null);
      setLoading(false);
      return;
    }

    let active = true;
    setCommunication(null);
    setError(null);
    setLoading(true);
    getCommunication({ site_id: site.id, start_utc: startUtc, hours: 24 })
      .then((response) => active && setCommunication(response))
      .catch((reason: unknown) => active && setError(reason))
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, [site?.id, startUtc]);

  return (
    <Page
      title="Communication Link"
      subtitle="Earth visibility is a geometric opportunity only; no antenna, power budget, DSN schedule, or live link telemetry is modeled."
    >
      {loading && <Loading label="Loading backend Earth-visibility analysis…" />}
      {error && <ErrorState error={error} />}
      {communication ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric label="Earth visible · geometric" value={format(communication.data.metrics.earth_geom_pct, '%')} />
            <Metric label="Earth visible · terrain corrected" value={format(communication.data.metrics.earth_terrain_pct, '%')} />
            <Metric label="Longest visibility gap" value={format(communication.data.metrics.longest_comms_gap_h, ' h')} />
            <Metric label="UTC start" value={communication.data.timeseries.start_utc} />
          </div>
          <ProvenanceBadge provenance={communication.provenance} cached={communication.cached} warnings={communication.warnings} />
        </>
      ) : !loading && !error ? <Unavailable label="Backend Earth-visibility analysis unavailable" /> : null}
    </Page>
  );
}

function HazardMapping({ site, slope }: { site: Site | null; slope: Envelope<TerrainSlopeData> | null }) {
  return (
    <div className="space-y-5">
      <Page
        title="Hazard Mapping"
        subtitle="Shows available DEM-derived terrain products and backend slope flags; it is not a certified landing-safety map."
      >
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <Metric label="Selected site" value={site?.name ?? 'Unavailable'} />
          <Metric label="Mean slope" value={format(slope?.data.slope_mean_deg ?? null, '°')} />
          <Metric label="Maximum slope" value={format(slope?.data.slope_max_deg ?? null, '°')} />
          <Metric label="Roughness" value={format(slope?.data.roughness_m ?? null, ' m')} />
          <Metric label="Hazard flags" value={slope?.data.hazard_flags?.join(', ') || 'Unavailable'} />
          <Metric label="PSR proximity" value="Unavailable · not spatially integrated" />
        </div>
        {slope && <ProvenanceBadge provenance={slope.provenance} cached={slope.cached} warnings={slope.warnings} />}
        <p className="text-xs text-slate-500">Boulder density and independently validated landing-safety scores are not available.</p>
      </Page>
      <section className="mission-card space-y-3 rounded-2xl p-5 sm:p-6">
        <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">NASA LOLA PSR source</h2>
        <p className="text-sm leading-6 text-slate-400">
          NASA PGDA publishes a south-polar PSR inventory; its filtered vector product contains 1,531 regions larger than 1 km².
          LUNARIS has not aligned this product to the selected site grid, so no site overlap or distance is reported.
        </p>
        <div className="flex flex-wrap gap-4 text-xs">
          <a href="https://pgda.gsfc.nasa.gov/products/90" target="_blank" rel="noreferrer" className="text-cyan-300 underline underline-offset-2">
            NASA PGDA product and provenance
          </a>
          <a href="https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LPSR_80S_20MPP_ADJ_1km2.SHP" target="_blank" rel="noreferrer" className="text-cyan-300 underline underline-offset-2">
            Download &gt;1 km² PSR polygons
          </a>
          <a href="https://doi.org/10.3847/PSJ/acf3e1" target="_blank" rel="noreferrer" className="text-cyan-300 underline underline-offset-2">
            Barker et al. (2023)
          </a>
        </div>
        <p className="text-xs text-slate-500">The polygon subset omits smaller PSRs; source product compatibility and site-level results remain unverified.</p>
      </section>
      <MapConnected site={site} title="Hazard Mapping" />
    </div>
  );
}

function MissionPlanner({
  timeline,
  powerEstimate,
}: {
  timeline: Envelope<ScenarioData> | null;
  powerEstimate: Envelope<PowerEstimateData> | null;
}) {
  return (
    <Page
      title="Mission Planner"
      subtitle="Planning context from backend illumination, Earth-visibility, and power estimates—not a rover/lander command schedule."
    >
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <Metric label="Sunlit · terrain corrected" value={format(timeline?.data.metrics.sunlit_terrain_pct ?? null, '%')} />
        <Metric label="Earth visible · terrain corrected" value={format(timeline?.data.metrics.earth_terrain_pct ?? null, '%')} />
        <Metric label="Longest dark interval" value={format(timeline?.data.metrics.longest_dark_h ?? null, ' h')} />
        <Metric label="Peak modeled power" value={format(powerEstimate?.data.peak_w ?? null, ' W')} />
        <Metric label="Modeled energy" value={format(powerEstimate?.data.energy_wh ?? null, ' Wh')} />
        <Metric label="Analysis start" value={timeline?.data.timeseries.start_utc ?? 'Unavailable'} />
      </div>
      {timeline && <ProvenanceBadge provenance={timeline.provenance} cached={timeline.cached} warnings={timeline.warnings} />}
      {powerEstimate && <ProvenanceBadge provenance={powerEstimate.provenance} cached={powerEstimate.cached} warnings={powerEstimate.warnings} />}
    </Page>
  );
}

function Settings({
  site,
  startUtc,
  link,
  ephemeris,
}: {
  site: Site | null;
  startUtc: string;
  link: LinkState;
  ephemeris: Envelope<EphemerisData> | null;
}) {
  return (
    <Page title="Settings" subtitle="Site and date controls are in the top bar. These values are not stored as a mission configuration on the backend.">
      <div className="grid gap-3 sm:grid-cols-2">
        <Metric label="API status" value={link} />
        <Metric label="Selected site" value={site?.name ?? 'Unavailable'} />
        <Metric label="Analysis UTC" value={startUtc} />
        <Metric label="Ephemeris frame" value={ephemeris?.data.frame ?? 'Unavailable'} />
      </div>
      {site?.source_url && (
        <a href={site.source_url} target="_blank" rel="noreferrer" className="text-xs text-cyan-300 underline underline-offset-2">
          Open selected site's coordinate source
        </a>
      )}
    </Page>
  );
}

function HelpGuide() {
  return (
    <Page title="Help Guide" subtitle="How to interpret LUNARIS outputs and their provenance.">
      <ul className="space-y-3 text-sm leading-6 text-slate-300">
        <li><strong className="text-white">Calculated</strong> values come from the connected LUNARIS backend and include assumptions and warnings in the provenance panel.</li>
        <li><strong className="text-white">Unavailable</strong> means a required source, validated coverage, or backend capability is missing; it is not zero.</li>
        <li>Geometric Sun/Earth visibility uses a spherical Moon. Terrain-corrected values additionally depend on the DEM horizon and may be preliminary.</li>
        <li>Earth visibility is not a radio link or DSN schedule. Solar power is an estimate, not live power telemetry.</li>
        <li>Map layers are LUNARIS-derived from the cited DEM; the NASA context mosaic is not georeferenced to those tiles.</li>
      </ul>
    </Page>
  );
}

function ThermalAnalysis({ site }: { site: Site | null }) {
  const [unavailable, setUnavailable] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(Boolean(site));

  useEffect(() => {
    if (!site) {
      setLoading(false);
      setUnavailable(true);
      return;
    }

    let active = true;
    setLoading(true);
    setUnavailable(false);
    setError(null);
    getThermalAnalysis({ site_id: site.id })
      .then(() => {
        if (active) setError(new Error('The thermal endpoint returned an unexpected response; no thermal values are displayed.'));
      })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 501) {
          setUnavailable(true);
          return;
        }
        setError(reason);
      })
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, [site?.id]);

  return (
    <Page title="Thermal Analysis" subtitle="Published Diviner context is shown separately from unavailable site-specific analysis.">
      {loading && <Loading label="Checking backend thermal-data availability…" />}
      {error && <ErrorState error={error} />}
      {!loading && unavailable && (
        <div className="rounded-xl border border-amber-200/20 bg-amber-200/[0.04] p-4 text-sm leading-6 text-amber-100">
          <Unavailable label="UNAVAILABLE" reason="The backend thermal endpoint returns HTTP 501. No validated Diviner temperature product is integrated." />
          <p className="mt-2">These published regional values are context only. They are not measurements for {site?.name ?? 'the selected site'} and are not used in site scoring.</p>
        </div>
      )}
      <section className="mission-card space-y-4 rounded-2xl p-5 sm:p-6">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">Published Diviner context</h2>
          <p className="mt-2 text-sm text-slate-400">The LRO Diviner team reports these broad south-polar thermal conditions; they are not site-specific outputs.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric label="Reported PSR temperatures" value="As low as 25 K" />
          <Metric label="Some continuously sunlit crater rims" value="Around 220 K" />
        </div>
        <p className="text-xs text-slate-500">Published Diviner science summary values; no date, pixel, or measurement for the selected site is inferred.</p>
        <div className="flex flex-wrap gap-4 text-xs">
          <a href="https://www.diviner.ucla.edu/science" target="_blank" rel="noreferrer" className="text-cyan-300 underline underline-offset-2">
            Diviner science summary
          </a>
          <a href="https://www.diviner.ucla.edu/data" target="_blank" rel="noreferrer" className="text-cyan-300 underline underline-offset-2">
            Diviner data portal
          </a>
          <a href="https://pds-geosciences.wustl.edu/missions/lro/diviner.htm" target="_blank" rel="noreferrer" className="text-cyan-300 underline underline-offset-2">
            NASA PDS Diviner archive
          </a>
        </div>
      </section>
    </Page>
  );
}

function UnavailablePage({ title, reason }: { title: string; reason: string }) {
  return (
    <Page title={title} subtitle="No source-backed scientific or operational values are being substituted.">
      <div className="rounded-xl border border-amber-200/20 bg-amber-200/[0.04] p-4 text-sm leading-6 text-amber-100">
        <Unavailable label="UNAVAILABLE" reason={reason} />
        <p className="mt-2">{reason}</p>
      </div>
    </Page>
  );
}

function Page({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <section className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold text-white">{title}</h1>
        <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
      </header>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="mission-card rounded-xl p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-2 break-words font-mono text-sm text-cyan-300">{value}</p>
    </div>
  );
}

function angleText(angle: EphemerisData['sun']): string {
  return angle ? `${angle.el.toFixed(2)}° el · ${angle.az.toFixed(2)}° az` : 'Unavailable';
}

function format(value: number | null, suffix = ''): string {
  return value === null ? 'Unavailable' : `${value}${suffix}`;
}
