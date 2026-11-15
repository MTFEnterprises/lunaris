import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import SitePicker from './pages/SitePicker';
import SkyView from './pages/SkyView';
import SunEarthAnalysis from './pages/SunEarthAnalysis';
import PowerModel from './pages/PowerModel';
import ThermalAnalysis from './pages/ThermalAnalysis';
import CommunicationLink from './pages/CommunicationLink';
import Comparison from './pages/Comparison';
import DateShift from './pages/DateShift';
import TerrainAnalysis from './pages/TerrainAnalysis';
import HazardMapping from './pages/HazardMapping';
import ExportReport from './pages/ExportReport';
import MissionPlanner from './pages/MissionPlanner';
import Settings from './pages/Settings';
import HelpGuide from './pages/HelpGuide';
import NotFound from './pages/NotFound';
import Telemetry from './pages/Telemetry';



function App() {
  return (
    <Router>
      <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
        {/* بائیں طرف سائیڈ بار */}
        <Sidebar />

        {/* دائیں طرف مین کنٹینٹ ایریا جہاں تمام پیجز شو ہوں گے */}
        <main className="flex-1 overflow-y-auto p-8 bg-slate-900/50">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/site-picker" element={<SitePicker />} />
            <Route path="/sky-view" element={<SkyView />} />
            <Route path="/sun-earth-analysis" element={<SunEarthAnalysis />} />
            <Route path="/power-model" element={<PowerModel />} />
            <Route path="/thermal-analysis" element={<ThermalAnalysis />} />
            <Route path="/communication-link" element={<CommunicationLink />} />
            <Route path="/comparison" element={<Comparison />} />
            <Route path="/date-shift" element={<DateShift />} />
            <Route path="/terrain-analysis" element={<TerrainAnalysis />} />
            <Route path="/hazard-mapping" element={<HazardMapping />} />
            <Route path="/export-report" element={<ExportReport />} />
            <Route path="/mission-planner" element={<MissionPlanner />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/help-guide" element={<HelpGuide />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;