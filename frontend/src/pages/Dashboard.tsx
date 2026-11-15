import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { ApiError, getEphemeris, getPowerEstimate, getSites, getTerrainSlope, getTimeline } from '../api/client';
import type { Envelope, EphemerisData, PowerEstimateData, ScenarioData, Site, TerrainSlopeData } from '../api/types';
import ErrorState from '../components/ErrorState';
import Loading from '../components/Loading';
import ProvenanceBadge from '../components/ProvenanceBadge';
import Disclaimer from '../components/Disclaimer';
import SkyScene3D from '../components/SkyScene3D';
import LunarContext from '../components/LunarContext';
import { DEFAULT_START_UTC, NAV_ITEMS, formatLatitude, formatLongitude, formatNumber } from '../lunaris/data';
import type { LinkState, TabName } from '../lunaris/data';
import Sidebar from '../lunaris/Sidebar';
import SkyViewConnected from './SkyViewConnected';
import TimelineConnected from './TimelineConnected';
import CompareConnected from './CompareConnected';
import MapConnected from './MapConnected';
import ReportConnected from './ReportConnected';

const POWER_PANEL = {
  area_m2: 2,
  efficiency: 0.28,
  losses: 0,
  tilt_deg: 0,
  azimuth_deg: 0,
};

export default function Dashboard() {
  const [tab, setTab] = useState<TabName>('Dashboard');
  const [sites, setSites] = useState<Envelope<{ sites: Site[] }> | null>(null);
  const [siteId, setSiteId] = useState('');
  const [startDate, setStartDate] = useState(DEFAULT_START_UTC.slice(0, 10));
  const [searchText, setSearchText] = useState('');
  const [ephemeris, setEphemeris] = useState<Envelope<EphemerisData> | null>(null);
  const [timeline, setTimeline] = useState<Envelope<ScenarioData> | null>(null);
  const [powerEstimate, setPowerEstimate] = useState<Envelope<PowerEstimateData> | null>(null);
  const [slopeEstimate, setSlopeEstimate] = useState<Envelope<TerrainSlopeData> | null>(null);
  const [dataError, setDataError] = useState<unknown>(null);
  const [powerError, setPowerError] = useState<unknown>(null);
  const [slopeError, setSlopeError] = useState<unknown>(null);
  const [loadingSites, setLoadingSites] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [loadingPower, setLoadingPower] = useState(false);
  const [loadingSlope, setLoadingSlope] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const selectedSite = useMemo(
    () => sites?.data.sites.find((site) => site.id === siteId) ?? null,
    [sites, siteId],
  );
  const startUtc = `${startDate}T00:00:00Z`;
  const link: LinkState = (error instanceof ApiError && error.status >= 500)
    || (dataError instanceof ApiError && dataError.status >= 500)
    ? 'offline'
    : loadingSites || loadingData || loadingPower || loadingSlope
      ? 'connecting'
      : 'online';

  useEffect(() => {
    let active = true;
    getSites()
      .then((response) => {
        if (!active) return;
        setSites(response);
        setSiteId((current) => current || response.data.sites[0]?.id || '');
      })
      .catch((reason) => active && setError(reason))
      .finally(() => active && setLoadingSites(false));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!siteId) return;
    let active = true;
    setLoadingData(true);
    setDataError(null);
    Promise.all([
      getEphemeris({ site_id: siteId, time_utc: startUtc }),
      getTimeline({ site_id: siteId, start_utc: startUtc, hours: 24 }),
    ])
      .then(([instant, scenario]) => {
        if (!active) return;
        setEphemeris(instant);
        setTimeline(scenario);
      })
      .catch((reason) => {
        if (!active) return;
        setEphemeris(null);
        setTimeline(null);
        setDataError(reason);
      })
      .finally(() => active && setLoadingData(false));
    return () => {
      active = false;
    };
  }, [siteId, startUtc]);

  useEffect(() => {
    if (!siteId) return;
    let active = true;
    setPowerEstimate(null);
    setPowerError(null);
    setLoadingPower(true);
    getPowerEstimate({
      site_id: siteId,
      start_utc: startUtc,
      hours: 24,
      step_min: 60,
      panel: POWER_PANEL,
    })
      .then((response) => active && setPowerEstimate(response))
      .catch((reason) => active && setPowerError(reason))
      .finally(() => active && setLoadingPower(false));
    return () => {
      active = false;
    };
  }, [siteId, startUtc]);

  useEffect(() => {
    if (!siteId) return;
    let active = true;
    setSlopeEstimate(null);
    setSlopeError(null);
    setLoadingSlope(true);
    getTerrainSlope({ site_id: siteId })
      .then((response) => active && setSlopeEstimate(response))
      .catch((reason) => active && setSlopeError(reason))
      .finally(() => active && setLoadingSlope(false));
    return () => {
      active = false;
    };
  }, [siteId]);

  const currentPage = NAV_ITEMS.find((item) => item.name === tab);
  const searchQuery = searchText.trim().toLowerCase();
  const pageResults = searchQuery
    ? NAV_ITEMS.filter((item) => item.name.toLowerCase().includes(searchQuery))
    : [];
  const siteResults = searchQuery
    ? (sites?.data.sites ?? []).filter((site) => site.name.toLowerCase().includes(searchQuery))
    : [];

  return (
    <div className="min-h-screen bg-transparent text-slate-100">
      <Sidebar
        tab={tab}
        onTab={setTab}
        collapsed={collapsed}
        hidden={false}
        onToggle={() => setCollapsed((value) => !value)}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
        link={link}
      />
      <div className={`min-h-screen transition-all duration-300 ${collapsed ? 'lg:pl-[84px]' : 'lg:pl-64'}`}>
        <header className="sticky top-0 z-30 flex min-h-16 flex-wrap items-center gap-3 border-b border-cyan-100/10 bg-[#050811]/80 px-4 py-2 backdrop-blur-xl sm:px-6 xl:px-8">
          <button
            className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 lg:hidden"
            onClick={() => setMobileOpen(true)}
          >
            Menu
          </button>
          <div>
            <p className="text-sm font-bold text-white">{tab}</p>
            <p className="text-[11px] text-slate-500">{currentPage?.desc}</p>
          </div>
          <div className="relative hidden min-w-48 max-w-sm flex-1 lg:block">
            <input
              aria-label="Search pages or candidate sites"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="Search pages or candidate sites..."
              className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-xs text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/50"
            />
            {searchQuery && (
              <div className="absolute left-0 right-0 top-full z-50 mt-2 max-h-80 overflow-y-auto rounded-xl border border-cyan-100/15 bg-[#091326]/95 p-2 shadow-2xl backdrop-blur-xl">
                {pageResults.map((item) => (
                  <button
                    key={`page-${item.name}`}
                    onClick={() => {
                      setTab(item.name);
                      setSearchText('');
                    }}
                    className="block w-full rounded-lg px-3 py-2 text-left text-xs text-slate-200 hover:bg-cyan-300/10"
                  >
                    {item.name} <span className="text-slate-500">· screen</span>
                  </button>
                ))}
                {siteResults.map((site) => (
                  <button
                    key={`site-${site.id}`}
                    onClick={() => {
                      setSiteId(site.id);
                      setTab('Dashboard');
                      setSearchText('');
                    }}
                    className="block w-full rounded-lg px-3 py-2 text-left text-xs text-slate-200 hover:bg-cyan-300/10"
                  >
                    {site.name} <span className="text-slate-500">· site</span>
                  </button>
                ))}
                {pageResults.length === 0 && siteResults.length === 0 && (
                  <p className="px-3 py-2 text-xs text-slate-500">No matching screen or site.</p>
                )}
              </div>
            )}
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className={`hidden rounded-full border px-2.5 py-1 text-[10px] uppercase tracking-widest sm:inline-flex ${link === 'online' ? 'border-emerald-300/20 bg-emerald-300/5 text-emerald-200' : link === 'connecting' ? 'border-amber-300/20 bg-amber-300/5 text-amber-200' : 'border-rose-300/20 bg-rose-300/5 text-rose-200'}`}>
              API {link}
            </span>
            <label className="hidden text-[10px] uppercase tracking-widest text-slate-500 sm:block" htmlFor="global-site">
              Site
            </label>
            <select
              id="global-site"
              value={siteId}
              onChange={(event) => setSiteId(event.target.value)}
              className="max-w-[190px] rounded-lg border border-white/10 bg-white/5 px-2 py-2 text-xs text-slate-100"
              disabled={loadingSites}
            >
              {sites?.data.sites.map((site) => (
                <option key={site.id} value={site.id} className="bg-slate-900">
                  {site.name}
                </option>
              ))}
            </select>
            <label className="hidden text-[10px] uppercase tracking-widest text-slate-500 sm:block" htmlFor="global-date">
              UTC date
            </label>
            <input
              id="global-date"
              type="date"
              min="2027-01-01"
              max="2027-12-31"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              className="rounded-lg border border-white/10 bg-white/5 px-2 py-2 text-xs text-slate-100"
            />
          </div>
        </header>

        <main className="mx-auto max-w-[1600px] space-y-5 px-4 py-6 sm:px-6 xl:px-8">
          {loadingSites && <Loading label="Loading curated candidate sites…" />}
          {error && <ErrorState error={error} />}
          {dataError && <ErrorState error={dataError} />}
          {!loadingSites && !error && (
            <>
              {tab === 'Dashboard' && (
                <DashboardView
                  site={selectedSite}
                  ephemeris={ephemeris}
                  timeline={timeline}
                  powerEstimate={powerEstimate}
                  slopeEstimate={slopeEstimate}
                  powerError={powerError}
                  slopeError={slopeError}
                  startUtc={startUtc}
                  loading={loadingData}
                  loadingPower={loadingPower}
                  loadingSlope={loadingSlope}
                />
              )}
              {tab === 'Site Picker' && (
                <SitePickerView sites={sites?.data.sites ?? []} selectedId={siteId} onSelect={setSiteId} />
              )}
              {tab === 'Sky View' && <SkyViewConnected timeline={timeline} />}
              {tab === 'Timeline' && <TimelineConnected timeline={timeline} />}
              {tab === 'Compare' && <CompareConnected sites={sites?.data.sites ?? []} selectedId={siteId} startDate={startDate} />}
              {tab === 'Map' && <MapConnected site={selectedSite} />}
              {tab === 'Report' && <ReportConnected siteId={siteId} startDate={startDate} />}
            </>
          )}
        </main>
        <Disclaimer />
      </div>
    </div>
  );
}

function DashboardView({
  site,
  ephemeris,
  timeline,
  powerEstimate,
  slopeEstimate,
  powerError,
  slopeError,
  startUtc,
  loading,
  loadingPower,
  loadingSlope,
}: {
  site: Site | null;
  ephemeris: Envelope<EphemerisData> | null;
  timeline: Envelope<ScenarioData> | null;
  powerEstimate: Envelope<PowerEstimateData> | null;
  slopeEstimate: Envelope<TerrainSlopeData> | null;
  powerError: unknown;
  slopeError: unknown;
  startUtc: string;
  loading: boolean;
  loadingPower: boolean;
  loadingSlope: boolean;
}) {
  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.32em] text-cyan-300">Mission control · lunar south pole</p>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-white sm:text-4xl">LUNARIS</h1>
          <p className="mt-2 text-sm text-slate-400">
            {site?.name ?? 'Selected candidate site'} <span className="px-1 text-slate-600">/</span> Scenario UTC{' '}
            <span className="font-mono text-slate-300">{startUtc}</span>
          </p>
        </div>
        <span className="rounded-full border border-cyan-200/15 bg-cyan-300/[0.06] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-cyan-100">
          {loading ? 'Updating analysis' : timeline?.warnings.length ? 'Preliminary analysis' : 'Backend analysis'}
        </span>
      </section>
      {loading && <Loading label="Loading ephemeris and timeline…" />}
      <SkyScene3D
        site={site}
        ephemeris={ephemeris}
        timeline={timeline}
        powerEstimate={powerEstimate}
        slopeEstimate={slopeEstimate}
        powerError={powerError}
        slopeError={slopeError}
        loading={loading}
        loadingPower={loadingPower}
        loadingSlope={loadingSlope}
      />
      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(300px,0.7fr)]">
        <MetricPanel title="Illumination and Earth-visibility window" envelope={timeline}>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <Result label="Sunlit · geometric" value={formatNumber(timeline?.data.metrics.sunlit_geom_pct ?? null, '%')} />
            <Result label="Sunlit · terrain corrected" value={formatNumber(timeline?.data.metrics.sunlit_terrain_pct ?? null, '%')} />
            <Result label="Earth visible · geometric" value={formatNumber(timeline?.data.metrics.earth_geom_pct ?? null, '%')} />
            <Result label="Earth visible · terrain corrected" value={formatNumber(timeline?.data.metrics.earth_terrain_pct ?? null, '%')} />
            <Result label="Longest dark interval" value={formatNumber(timeline?.data.metrics.longest_dark_h ?? null, ' h')} />
            <Result label="Longest Earth-visibility gap" value={formatNumber(timeline?.data.metrics.longest_comms_gap_h ?? null, ' h')} />
          </div>
          <p className="mt-4 text-xs leading-5 text-slate-500">
            Earth visibility is a geometric opportunity, not a radio-link or DSN schedule. Terrain-corrected values remain preliminary while DEM-frame compatibility is unresolved.
          </p>
        </MetricPanel>
        <LunarContext />
      </section>
    </div>
  );
}

function SitePickerView({ sites, selectedId, onSelect }: { sites: Site[]; selectedId: string; onSelect: (id: string) => void }) {
  return (
    <section className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-white">Candidate sites</h1>
        <p className="mt-1 text-sm text-slate-400">Sites are loaded only from GET /api/sites.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sites.map((site) => (
          <article
            key={site.id}
            className={`mission-card rounded-2xl transition ${selectedId === site.id ? 'ring-1 ring-cyan-300/50' : 'hover:border-cyan-100/30'}`}
          >
            <button onClick={() => onSelect(site.id)} className="w-full p-5 text-left">
              <h2 className="font-bold text-white">{site.name}</h2>
              <p className="mt-2 text-xs text-slate-400">{formatLatitude(site.lat)} · {formatLongitude(site.lon)}</p>
              <p className="mt-2 text-xs text-slate-400">
                Elevation: {site.height_m === null ? 'Not published' : `${site.height_m} m`}
              </p>
              <p className="mt-3 text-xs leading-5 text-slate-400">{site.notes ?? 'Site definition unavailable.'}</p>
              <p className="mt-3 text-xs text-slate-500">Class: {site.class}</p>
            </button>
            {site.source_url && (
              <a
                href={site.source_url}
                target="_blank"
                rel="noreferrer"
                className="mx-5 mb-5 inline-block text-xs text-cyan-300 underline decoration-cyan-300/40 underline-offset-2"
              >
                Coordinate source
              </a>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function MetricPanel({ title, envelope, children }: { title: string; envelope: Envelope<unknown> | null; children: ReactNode }) {
  return (
    <section className="mission-card rounded-2xl p-5 sm:p-6">
      <h2 className="text-sm font-bold uppercase tracking-widest text-slate-300">{title}</h2>
      <div className="mt-4">{children}</div>
      {envelope && <div className="mt-4"><ProvenanceBadge provenance={envelope.provenance} cached={envelope.cached} warnings={envelope.warnings} /></div>}
    </section>
  );
}

function Result({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-xl font-semibold text-cyan-100">{value}</p>
    </div>
  );
}
