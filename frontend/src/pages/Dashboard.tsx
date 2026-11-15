import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getLunarData } from '../services/api';
import { HOME_ZOOM, HOURS_24, INSIGHTS, makePoint, MISSION, missionTone, NAV_ITEMS, ORBIT, POWER_24H, SITES, SUBSYSTEMS } from '../lunaris/data';
import type { LinkState, LunarData, StreamPoint, TabName, Toast, ToastType } from '../lunaris/data';
import { computeLunar } from '../lunaris/lunar';
import { useNow } from '../lunaris/hooks';
import { AreaChart, SiteSafetyChart } from '../lunaris/charts';
import { Icon, IconBtn, LinkPill, Meter, Panel, PanelHeader, Pill, Reveal, StatCard, UtcClock } from '../lunaris/ui';
import MoonGlobe from '../lunaris/MoonGlobe';
import Sidebar from '../lunaris/Sidebar';
import { MoonPhaseCard, SiteCard, TrendCard } from '../lunaris/HeroCards';
import { AlertsView, CommsView, LandingSimView, LifeSupportView, NavigationView, OrbitView, PayloadsView, RadiationView, ResourcesView, RoverView } from '../lunaris/moreViews';
import { PlannerView, PowerThermalView, SitePickerView, TelemetryView, TerrainView } from '../lunaris/views';
import Disclaimer from '../components/Disclaimer';

export default function Dashboard() {
  const [tab, setTab] = useState<TabName>('Dashboard');
  const [selected, setSelected] = useState(0);
  const [rotating, setRotating] = useState(true);
  const [zoom, setZoom] = useState(HOME_ZOOM);
  const [resetSignal, setResetSignal] = useState(0);
  const [collapsed, setCollapsed] = useState(false);
  const [sidebarHidden, setSidebarHidden] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [searchFocus, setSearchFocus] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [link, setLink] = useState<LinkState>('connecting');
  const [data, setData] = useState<LunarData | null>(null);
  const [stream, setStream] = useState<StreamPoint[]>(() => {
    const t = Date.now();
    return Array.from({ length: 24 }, (_, i) => makePoint(i, t - (24 - i) * 3000));
  });

  const toastId = useRef(0);
  const streamN = useRef(24);
  const wasOnline = useRef(false);

  /* ---- this page owns the whole screen: hide anything rendered behind it (old layouts / sidebars) ---- */
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  /* ---- real lunar state (recomputed every minute) ---- */
  const now = useNow(60000);
  const lunar = useMemo(() => computeLunar(now), [now]);

  /* ---- toasts ---- */
  const toast = useCallback((title: string, message: string, type: ToastType = 'info') => {
    const id = ++toastId.current;
    setToasts((t) => [...t.slice(-3), { id, title, message, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);

  /* ---- backend polling ---- */
  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const d = (await getLunarData()) as unknown as LunarData | null | undefined;
        if (cancelled) return;
        if (d) {
          setData(d);
          setLink('online');
          if (!wasOnline.current) {
            wasOnline.current = true;
            toast('Backend connected', 'Live data is flowing from /api.', 'success');
          }
        } else {
          setLink('offline');
        }
      } catch {
        if (!cancelled) setLink('offline');
      }
    };
    void tick();
    const id = setInterval(() => void tick(), 3000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [toast]);

  /* ---- simulated telemetry stream ---- */
  useEffect(() => {
    const id = setInterval(() => {
      streamN.current += 1;
      setStream((s) => [...s.slice(-29), makePoint(streamN.current, Date.now())]);
    }, 3000);
    return () => clearInterval(id);
  }, []);

  /* ---- search ---- */
  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return SITES.map((s, i) => ({ s, i })).filter(({ s }) => s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q));
  }, [query]);

  const pageResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? NAV_ITEMS.filter((n) => n.name.toLowerCase().includes(q)) : [];
  }, [query]);

  const goPage = (t: TabName) => {
    setTab(t);
    setQuery('');
    setSearchFocus(false);
  };

  const pickSite = (i: number) => {
    setSelected(i);
    setTab('Dashboard');
    setQuery('');
    setSearchFocus(false);
    toast('Site selected', SITES[i].name, 'success');
  };

  const step = (d: number) => setSelected((s) => (s + d + SITES.length) % SITES.length);
  const fromGlobe = (i: number) => {
    setSelected(i);
    toast('Site selected', SITES[i].name, 'success');
  };

  const irradiance = data?.telemetry?.solarIrradiance !== undefined ? String(data.telemetry.solarIrradiance) : '1,361';
  const navMeta = NAV_ITEMS.find((n) => n.name === tab);
  const homeSteps = MISSION.filter((m) => m.home);

  return (
    <div className="fixed inset-0 z-[100] overflow-y-auto overflow-x-hidden bg-[#050811] text-slate-100">
      <Sidebar
        tab={tab}
        onTab={setTab}
        collapsed={collapsed}
        hidden={sidebarHidden}
        onToggle={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
        link={link}
      />

      <div className={`min-h-screen transition-all duration-300 ${sidebarHidden ? 'lg:pl-0' : collapsed ? 'lg:pl-[84px]' : 'lg:pl-64'}`}>
        {/* ------------------------- top bar ------------------------- */}
        <header className={`sticky top-0 z-30 flex h-12 items-center gap-3 px-4 sm:px-6 xl:px-8 ${tab === 'Dashboard' ? 'bg-gradient-to-b from-[#050811]/80 to-transparent' : 'border-b border-white/10 bg-[#050811]/80 backdrop-blur-xl'}`}>
          <button
            onClick={() => {
              if (window.matchMedia('(min-width: 1024px)').matches) setSidebarHidden((h) => !h);
              else setMobileOpen(true);
            }}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-200 transition hover:border-cyan-300/50 hover:text-cyan-200"
            aria-label="Toggle sidebar"
            title="Show / hide sidebar"
          >
            <Icon name="menu" className="h-5 w-5" />
          </button>
          <div className="hidden min-w-0 md:block">
            <h1 className="truncate text-sm font-bold text-white">{tab}</h1>
            <p className="truncate text-[11px] text-slate-500">{navMeta?.desc}</p>
          </div>

          <div className="relative mx-auto w-full max-w-md">
            <Icon name="search" className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setSearchFocus(true)}
              onBlur={() => setSearchFocus(false)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  if (results.length > 0) pickSite(results[0].i);
                  else if (pageResults.length > 0) goPage(pageResults[0].name);
                }
                if (e.key === 'Escape') setQuery('');
              }}
              placeholder="Search pages or landing sites…"
              className="w-full rounded-full border border-white/10 bg-white/5 py-2 pl-10 pr-4 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-300/50 focus:bg-white/[0.08]"
            />
            {searchFocus && query.trim() !== '' && (
              <div className="absolute left-0 right-0 top-11 max-h-80 overflow-y-auto rounded-2xl border border-white/10 bg-[#0a1020]/95 shadow-2xl backdrop-blur-xl">
                {results.length === 0 && pageResults.length === 0 && <p className="px-4 py-3 text-xs text-slate-500">Nothing matches “{query}”</p>}
                {pageResults.map((n) => (
                  <button key={n.name} onMouseDown={() => goPage(n.name)} className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm hover:bg-white/5">
                    <Icon name={n.icon} className="h-4 w-4 text-cyan-300" />
                    <span className="flex-1 truncate text-slate-100">{n.name}</span>
                    <span className="text-[10px] uppercase tracking-widest text-slate-500">Page</span>
                  </button>
                ))}
                {results.map(({ s, i }) => (
                  <button key={s.code} onMouseDown={() => pickSite(i)} className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left text-sm hover:bg-white/5">
                    <span className="truncate text-slate-100">{s.name}</span>
                    <span className="font-mono text-[10px] text-cyan-300">{s.code}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="hidden items-center gap-2 xl:flex">
            <UtcClock />
            <LinkPill state={link} />
          </div>
          <IconBtn icon="bell" title="Notifications" onClick={() => toast('All clear', 'No active alerts for Mission M5.')} />
        </header>

        {/* --------------------------- views -------------------------- */}
        {tab === 'Dashboard' && (
          <main className="relative">
            {/* full-screen moon background (fixed, behind everything) */}
            <div
              className={`fixed inset-y-0 right-0 left-0 z-0 bg-[radial-gradient(ellipse_at_center,#0c1733_0%,#050811_78%)] transition-all duration-300 ${
                sidebarHidden ? 'lg:left-0' : collapsed ? 'lg:left-[84px]' : 'lg:left-64'
              }`}
            >
              <MoonGlobe selected={selected} onSelect={fromGlobe} rotating={rotating} resetSignal={resetSignal} zoom={zoom} sunLon={lunar.sunLon} />
            </div>

            {/* hero overlay: empty areas let the mouse reach the moon */}
            <section className="pointer-events-none relative z-10 flex min-h-[calc(100vh-3rem)] w-full flex-col justify-between gap-6 px-3 py-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-cyan-300">Mission Control</p>
                <h2 className="mt-1 text-3xl font-extrabold text-white">{data?.mission ?? 'LUNARIS M5'}</h2>
                <p className="mt-1 font-mono text-[11px] text-slate-400">{data?.epoch ?? now.toISOString().slice(0, 19).replace('T', ' ') + ' UTC'}</p>
              </div>

              <div className="grid flex-1 items-end gap-5 xl:grid-cols-[280px_minmax(0,1fr)_280px]">
                <div className="pointer-events-auto space-y-5">
                  <SiteCard index={selected} onPrev={() => step(-1)} onNext={() => step(1)} />
                  <TrendCard stream={stream} />
                </div>
                <div className="h-[40vh] xl:h-auto" />
                <Reveal delay={100} className="pointer-events-auto">
                  <MoonPhaseCard lunar={lunar} siteIndex={selected} now={now} compact />
                </Reveal>
              </div>

              <div className="flex flex-wrap items-end justify-between gap-3">
                <button
                  onClick={() => setTab('Site Picker')}
                  className="pointer-events-auto inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-5 py-2.5 text-sm font-bold text-slate-950 shadow-[0_0_30px_rgba(34,211,238,0.35)] transition hover:brightness-110"
                >
                  Explore Sites
                  <Icon name="arrow" className="h-4 w-4" />
                </button>
                <div className="pointer-events-auto hidden md:block">
                  <Pill tone="cyan">Drag to rotate · click a hotspot</Pill>
                </div>
                <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-white/10 bg-slate-950/60 p-1.5 backdrop-blur-md">
                  <IconBtn icon="minus" title="Zoom out" onClick={() => setZoom((z) => Math.min(5, +(z + 0.4).toFixed(1)))} />
                  <IconBtn icon="plus" title="Zoom in" onClick={() => setZoom((z) => Math.max(1.8, +(z - 0.4).toFixed(1)))} />
                  <IconBtn icon={rotating ? 'pause' : 'play'} title={rotating ? 'Pause rotation' : 'Resume rotation'} onClick={() => setRotating((r) => !r)} />
                  <IconBtn
                    icon="reset"
                    title="Reset view"
                    onClick={() => {
                      setZoom(HOME_ZOOM);
                      setResetSignal((n) => n + 1);
                    }}
                  />
                </div>
              </div>
            </section>

            {/* everything below the hero scrolls over the fixed moon */}
            <div className="relative z-10 bg-[linear-gradient(to_bottom,transparent,rgba(5,8,17,0.9)_200px)] pt-10">
              <div className="mx-auto max-w-[1700px] space-y-5 px-4 pb-8 sm:px-6 xl:px-8">
            {/* KPI row */}
            <Reveal delay={150}>
              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard label="Orbit Altitude" value={`${ORBIT.altitude} km`} sub="Circular lunar orbit" color="text-cyan-300" icon="moon" />
                <StatCard label="Velocity" value={`${ORBIT.velocity} km/s`} sub="Orbital speed" color="text-emerald-300" icon="pulse" />
                <StatCard label="Inclination" value={`${ORBIT.inclination}°`} sub="To lunar equator" color="text-sky-300" icon="target" />
                <StatCard label="Signal Latency" value={`${ORBIT.latency} s`} sub="Round trip to Earth" color="text-amber-300" icon="clock" />
              </section>
            </Reveal>

            {/* charts */}
            <Reveal delay={200}>
              <section className="grid gap-5 xl:grid-cols-3">
                <Panel className="p-5 xl:col-span-2">
                  <PanelHeader title="Power Generation · 24 h" right={<Pill tone="green">Nominal</Pill>} />
                  <AreaChart id="home24" data={POWER_24H} labels={HOURS_24} unit=" kW" height={210} />
                </Panel>
                <Panel className="p-5">
                  <PanelHeader title="Landing Site Safety" />
                  <SiteSafetyChart selected={selected} onSelect={setSelected} />
                </Panel>
              </section>
            </Reveal>

            {/* AI insights */}
            <Reveal delay={250}>
              <section>
                <div className="mb-3 flex items-center gap-2">
                  <Icon name="sparkle" className="h-4 w-4 text-cyan-300" />
                  <h3 className="text-[11px] font-bold uppercase tracking-widest text-slate-400">AI Insights</h3>
                </div>
                <div className="grid gap-4 lg:grid-cols-3">
                  {INSIGHTS.map((c) => (
                    <Panel key={c.title} className="p-5">
                      <div className="flex items-center justify-between gap-3">
                        <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-cyan-300">
                          <Icon name={c.icon} className="h-5 w-5" />
                        </span>
                        <Pill tone={c.tone}>{c.chip}</Pill>
                      </div>
                      <p className="mt-4 font-bold text-white">{c.title}</p>
                      <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{c.text}</p>
                    </Panel>
                  ))}
                </div>
              </section>
            </Reveal>

            {/* health + timeline */}
            <Reveal delay={300}>
              <section className="grid gap-5 lg:grid-cols-2">
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
                <Panel className="p-5">
                  <PanelHeader title="Mission Timeline" right={<IconBtn icon="arrow" title="Open planner" onClick={() => setTab('Mission Planner')} />} />
                  <ul className="space-y-3">
                    {homeSteps.map((m) => (
                      <li key={m.name} className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-white">{m.name}</p>
                          <p className="font-mono text-[11px] text-slate-500">{m.when}</p>
                        </div>
                        <Pill tone={missionTone(m.status)}>{m.status}</Pill>
                      </li>
                    ))}
                  </ul>
                </Panel>
              </section>
            </Reveal>
              </div>
            </div>
          </main>
        )}

        {tab === 'Site Picker' && <SitePickerView selected={selected} onSelect={setSelected} lunar={lunar} />}
        {tab === 'Telemetry' && <TelemetryView stream={stream} />}
        {tab === 'Power & Thermal' && <PowerThermalView irradiance={irradiance} />}
        {tab === 'Terrain & Hazard' && <TerrainView selected={selected} onSelect={setSelected} />}
        {tab === 'Mission Planner' && <PlannerView />}
        {tab === 'Orbit Tracker' && <OrbitView />}
        {tab === 'Communications' && <CommsView stream={stream} />}
        {tab === 'Navigation' && <NavigationView />}
        {tab === 'Landing Simulator' && <LandingSimView selected={selected} onSelect={setSelected} lunar={lunar} />}
        {tab === 'Rover Ops' && <RoverView />}
        {tab === 'Science Payloads' && <PayloadsView />}
        {tab === 'Resources' && <ResourcesView selected={selected} onSelect={setSelected} />}
        {tab === 'Radiation' && <RadiationView />}
        {tab === 'Life Support' && <LifeSupportView />}
        {tab === 'Alerts & Logs' && <AlertsView />}
      </div>

      {/* ---------------------------- toasts --------------------------- */}
      <div className="pointer-events-none fixed bottom-5 right-5 z-[60] space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`min-w-[240px] rounded-xl border px-4 py-3 shadow-2xl backdrop-blur-xl ${
              t.type === 'success' ? 'border-emerald-400/30 bg-emerald-950/80' : 'border-cyan-400/30 bg-slate-900/90'
            }`}
          >
            <p className="text-xs font-bold text-white">{t.title}</p>
            <p className="text-[11px] text-slate-300">{t.message}</p>
          </div>
        ))}
      </div>
      <div className="relative z-20 mt-8 bg-[#050811]">
        <Disclaimer />
      </div>
    </div>
  );
}
