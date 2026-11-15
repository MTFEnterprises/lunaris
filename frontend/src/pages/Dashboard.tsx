import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { ApiError, getEphemeris, getSites, getTimeline } from '../api/client';
import type { Envelope, EphemerisData, ScenarioData, Site } from '../api/types';
import ErrorState from '../components/ErrorState';
import Loading from '../components/Loading';
import ProvenanceBadge from '../components/ProvenanceBadge';
import Unavailable from '../components/Unavailable';
import Disclaimer from '../components/Disclaimer';
import SkyScene3D from '../components/SkyScene3D';
import RotatingMoon from '../components/RotatingMoon';
import { DEFAULT_START_UTC, NAV_ITEMS, formatLatitude, formatLongitude, formatNumber } from '../lunaris/data';
import type { LinkState, TabName } from '../lunaris/data';
import Sidebar from '../lunaris/Sidebar';
import SkyViewConnected from './SkyViewConnected';
import TimelineConnected from './TimelineConnected';
import CompareConnected from './CompareConnected';
import MapConnected from './MapConnected';
import ReportConnected from './ReportConnected';

function Value({ value, suffix = '' }: { value: number | null; suffix?: string }) {
  return value === null ? <Unavailable /> : <>{value}{suffix}</>;
}

export default function Dashboard() {
  const [tab, setTab] = useState<TabName>('Dashboard');
  const [sites, setSites] = useState<Envelope<{ sites: Site[] }> | null>(null);
  const [siteId, setSiteId] = useState('');
  const [startDate, setStartDate] = useState(DEFAULT_START_UTC.slice(0, 10));
  const [ephemeris, setEphemeris] = useState<Envelope<EphemerisData> | null>(null);
  const [timeline, setTimeline] = useState<Envelope<ScenarioData> | null>(null);
  const [dataError, setDataError] = useState<unknown>(null);
  const [loadingSites, setLoadingSites] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const selectedSite = useMemo(
    () => sites?.data.sites.find((site) => site.id === siteId) ?? null,
    [sites, siteId],
  );
  const startUtc = `${startDate}T00:00:00Z`;
  const link: LinkState = error instanceof ApiError && error.status >= 500
    ? 'offline'
    : loadingSites || loadingData
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

  const currentPage = NAV_ITEMS.find((item) => item.name === tab);

  return (
    <div className="min-h-screen bg-[#050811] text-slate-100">
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
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-white/10 bg-[#050811]/90 px-4 backdrop-blur-xl sm:px-6 xl:px-8">
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
          <div className="ml-auto flex items-center gap-2">
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
                  startUtc={startUtc}
                  loading={loadingData}
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
              {tab !== 'Dashboard' && tab !== 'Site Picker' && (
                <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
                  <h1 className="text-2xl font-extrabold text-white">{tab}</h1>
                  <p className="mt-2 text-sm text-slate-400">
                    This view uses the shared site and UTC date selection. Backend-backed content is being added in the next integration step.
                  </p>
                  <p className="mt-4 text-sm text-amber-300">Unavailable until its documented endpoint is loaded.</p>
                </section>
              )}
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
  startUtc,
  loading,
}: {
  site: Site | null;
  ephemeris: Envelope<EphemerisData> | null;
  timeline: Envelope<ScenarioData> | null;
  startUtc: string;
  loading: boolean;
}) {
  return (
    <div className="space-y-5">
      <section>
        <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-cyan-300">CLPS Lunar Mission Browser</p>
        <h1 className="mt-1 text-3xl font-extrabold text-white">{site?.name ?? 'Selected site'}</h1>
        <p className="mt-1 font-mono text-[11px] text-slate-400">{startUtc}</p>
      </section>
      {loading && <Loading label="Loading ephemeris and timeline…" />}
      <SkyScene3D ephemeris={ephemeris} loading={loading} />
      <RotatingMoon site={site} ephemeris={ephemeris?.data ?? null} />
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Latitude" value={formatLatitude(site?.lat ?? null)} />
        <MetricCard label="Longitude" value={formatLongitude(site?.lon ?? null)} />
        <MetricCard label="Sun elevation" value={ephemeris ? <Value value={ephemeris.data.sun?.el ?? null} suffix="°" /> : <Unavailable />} provenance={ephemeris} />
        <MetricCard label="Earth elevation" value={ephemeris ? <Value value={ephemeris.data.earth?.el ?? null} suffix="°" /> : <Unavailable />} provenance={ephemeris} />
      </section>
      <section className="grid gap-5 lg:grid-cols-2">
        <MetricPanel title="Geometric and terrain results" envelope={timeline}>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <Result label="Sunlit geometric" value={formatNumber(timeline?.data.metrics.sunlit_geom_pct ?? null, '%')} />
            <Result label="Sunlit terrain" value={formatNumber(timeline?.data.metrics.sunlit_terrain_pct ?? null, '%')} />
            <Result label="Earth visible geometric" value={formatNumber(timeline?.data.metrics.earth_geom_pct ?? null, '%')} />
            <Result label="Earth visible terrain" value={formatNumber(timeline?.data.metrics.earth_terrain_pct ?? null, '%')} />
          </div>
          <p className="mt-4 text-xs text-slate-500">Earth visible means a geometric communication opportunity, not a radio link.</p>
        </MetricPanel>
        <MetricPanel title="Data status" envelope={ephemeris}>
          <div className="space-y-3 text-sm text-slate-300">
            <p>Frame: {ephemeris?.data.frame ?? <Unavailable />}</p>
            <p>Terrain horizon: {timeline?.data.horizon.deg ? 'Available' : <Unavailable reason={timeline?.provenance.reason} />}</p>
            <p>Cached: {timeline?.cached ? 'Yes' : 'No'}</p>
          </div>
        </MetricPanel>
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
          <button
            key={site.id}
            onClick={() => onSelect(site.id)}
            className={`rounded-2xl border p-5 text-left transition ${selectedId === site.id ? 'border-cyan-300/60 bg-cyan-300/10' : 'border-white/10 bg-white/[0.04] hover:border-white/30'}`}
          >
            <h2 className="font-bold text-white">{site.name}</h2>
            <p className="mt-2 text-xs text-slate-400">{formatLatitude(site.lat)} · {formatLongitude(site.lon)}</p>
            <p className="mt-3 text-xs uppercase tracking-widest text-slate-500">{site.kind ?? 'Unavailable'}</p>
            <p className="mt-3 text-xs text-slate-500">Class: {site.class}</p>
          </button>
        ))}
      </div>
    </section>
  );
}

function MetricCard({ label, value, provenance }: { label: string; value: ReactNode; provenance?: Envelope<unknown> | null }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <p className="text-[10px] uppercase tracking-widest text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-extrabold text-cyan-300">{value}</p>
      {provenance && <div className="mt-3"><ProvenanceBadge provenance={provenance.provenance} cached={provenance.cached} warnings={provenance.warnings} /></div>}
    </div>
  );
}

function MetricPanel({ title, envelope, children }: { title: string; envelope: Envelope<unknown> | null; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
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
      <p className="mt-1 font-mono text-lg text-slate-100">{value}</p>
    </div>
  );
}
