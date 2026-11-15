import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/site-picker', label: 'Site Picker' },
  { path: '/sky-view', label: 'Sky View' },
  { path: '/sun-earth-analysis', label: 'Sun & Earth Analysis' },
  { path: '/power-model', label: 'Power Model' },
  { path: '/thermal-analysis', label: 'Thermal Analysis' },
  { path: '/communication-link', label: 'Communication Link' },
  { path: '/comparison', label: 'Comparison' },
  { path: '/date-shift', label: 'Date Shift' },
  { path: '/terrain-analysis', label: 'Terrain Analysis' },
  { path: '/hazard-mapping', label: 'Hazard Mapping' },
  { path: '/export-report', label: 'Export Report' },
  { path: '/mission-planner', label: 'Mission Planner' },
  { path: '/settings', label: 'Settings' },
  { path: '/help-guide', label: 'Help Guide' },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-slate-900 text-slate-200 h-screen p-4 flex flex-col border-r border-slate-800">
      <div className="text-xl font-bold text-cyan-400 mb-6 tracking-wider">LUNARIS M4</div>
      <nav className="flex-1 space-y-1 overflow-y-auto pr-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`block px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-cyan-500 text-white font-medium'
                  : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}