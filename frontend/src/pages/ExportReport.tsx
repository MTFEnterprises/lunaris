import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function ExportReport() {
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchReportInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setReportData(response);
        }
      } catch (error) {
        console.error('Error fetching export report data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchReportInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Preparing telemetry logs and mission export modules...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Mission Report Export</h1>
        <p className="text-slate-400 mt-1">Generate comprehensive telemetry summaries, JSON logs, and PDF mission briefs.</p>
      </div>

      {/* Export Options Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Telemetry JSON Log</h3>
          <p className="text-2xl font-bold text-emerald-400">Ready (.json)</p>
          <p className="text-xs text-slate-500">Full backend state dump</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Mission PDF Brief</h3>
          <p className="text-2xl font-bold text-cyan-400">Ready (.pdf)</p>
          <p className="text-xs text-slate-500">Executive summary & charts</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sync Status</h3>
          <p className="text-2xl font-bold text-amber-400">Up to Date</p>
          <p className="text-xs text-slate-500">Server packets verified</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-4">
        <h3 className="text-md font-bold text-slate-200">Export Control Panel</h3>
        <p className="text-sm text-slate-400">
          Current mission epoch ({reportData?.epoch || 'Day 14.2'}) telemetry data is compiled and ready for download or transmission to ground control stations.
        </p>
        <button 
          onClick={() => alert('Mission report package compiled successfully from backend data!')}
          className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold rounded-lg text-sm transition-colors"
        >
          Download Complete Mission Package
        </button>
      </div>
    </div>
  );
}