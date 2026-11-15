import { NAV_ITEMS } from './data';
import type { LinkState, TabName } from './data';
import { Icon } from './ui';

interface SidebarProps {
  tab: TabName;
  onTab: (t: TabName) => void;
  collapsed: boolean;
  hidden: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onClose: () => void;
  link: LinkState;
}

export default function Sidebar({ tab, onTab, collapsed, hidden, onToggle, mobileOpen, onClose, link }: SidebarProps) {
  const linkDot = link === 'online' ? 'bg-emerald-400' : link === 'connecting' ? 'bg-amber-400' : 'bg-rose-400';
  const linkText = link === 'online' ? 'Backend online' : link === 'connecting' ? 'Connecting…' : 'Backend offline';

  return (
    <>
      {/* mobile overlay */}
      <div
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity lg:hidden ${mobileOpen ? 'opacity-100' : 'pointer-events-none opacity-0'}`}
      />

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/10 bg-[#070b17]/95 backdrop-blur-xl transition-all duration-300 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        } ${hidden ? 'lg:-translate-x-full' : 'lg:translate-x-0'} ${collapsed ? 'lg:w-[84px]' : 'lg:w-64'}`}
      >
        {/* brand */}
        <div className={`flex h-16 items-center gap-3 border-b border-white/10 px-5 ${collapsed ? 'lg:justify-center lg:px-0' : ''}`}>
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 text-slate-950 shadow-[0_0_20px_rgba(34,211,238,0.5)]">
            <Icon name="moon" className="h-5 w-5" />
          </span>
          <div className={`min-w-0 ${collapsed ? 'lg:hidden' : ''}`}>
            <p className="text-sm font-extrabold tracking-[0.25em] text-white">LUNARIS</p>
            <p className="text-[10px] uppercase tracking-widest text-cyan-300">Lunar mission browser</p>
          </div>
          <button onClick={onClose} className="ml-auto text-slate-400 hover:text-white lg:hidden" aria-label="Close menu">
            <Icon name="close" className="h-5 w-5" />
          </button>
        </div>

        {/* navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
          {NAV_ITEMS.map((item, idx) => {
            const active = item.name === tab;
            const newGroup = idx === 0 || NAV_ITEMS[idx - 1].group !== item.group;
            return (
              <div key={item.name}>
                {newGroup && (
                  <>
                    <p className={`px-3 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500 ${idx === 0 ? '' : 'pt-4'} ${collapsed ? 'lg:hidden' : ''}`}>
                      {item.group}
                    </p>
                    {idx > 0 && <div className={`my-2 hidden h-px bg-white/10 ${collapsed ? 'lg:block' : ''}`} />}
                  </>
                )}
              <button
                onClick={() => {
                  onTab(item.name);
                  onClose();
                }}
                title={item.name}
                className={`group relative flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-medium transition ${
                  active
                    ? 'bg-gradient-to-r from-cyan-400/20 to-blue-500/5 text-white ring-1 ring-cyan-300/30'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                } ${collapsed ? 'lg:justify-center' : ''}`}
              >
                {active && <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r bg-cyan-300 shadow-[0_0_12px_rgba(103,232,249,0.9)]" />}
                <Icon name={item.icon} className={`h-5 w-5 shrink-0 ${active ? 'text-cyan-300' : ''}`} />
                <span className={`flex-1 truncate ${collapsed ? 'lg:hidden' : ''}`}>{item.name}</span>
                {item.live && (
                  <span className={`h-2 w-2 shrink-0 animate-pulse rounded-full bg-emerald-400 ${collapsed ? 'lg:absolute lg:right-3 lg:top-2' : ''}`} />
                )}
              </button>
              </div>
            );
          })}
        </nav>

        {/* status + collapse + user */}
        <div className="space-y-3 border-t border-white/10 p-3">
          <div className={`flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-[11px] text-slate-300 ${collapsed ? 'lg:justify-center' : ''}`}>
            <span className={`h-2 w-2 shrink-0 animate-pulse rounded-full ${linkDot}`} />
            <span className={collapsed ? 'lg:hidden' : ''}>{linkText}</span>
          </div>

          <button
            onClick={onToggle}
            className={`hidden w-full items-center gap-3 rounded-xl px-3 py-2 text-xs text-slate-400 transition hover:bg-white/5 hover:text-white lg:flex ${collapsed ? 'justify-center' : ''}`}
          >
            <Icon name={collapsed ? 'expand' : 'collapse'} className="h-4 w-4" />
            <span className={collapsed ? 'hidden' : ''}>Collapse sidebar</span>
          </button>

          <div className={`flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.04] p-2.5 ${collapsed ? 'lg:justify-center lg:p-2' : ''}`}>
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 text-xs font-bold text-white">AH</span>
            <div className={`min-w-0 ${collapsed ? 'lg:hidden' : ''}`}>
              <p className="truncate text-xs font-semibold text-white">Prototype session</p>
              <p className="truncate text-[10px] text-slate-500">Local browser</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
