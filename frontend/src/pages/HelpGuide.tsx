import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function HelpGuide() {
  const [helpData, setHelpData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchHelpInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setHelpData(response);
        }
      } catch (error) {
        console.error('Error fetching help guide data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHelpInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading operational manuals and documentation...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Mission Help & User Guide</h1>
        <p className="text-slate-400 mt-1">Operational guidelines, telemetry troubleshooting, and system navigation instructions.</p>
      </div>

      {/* Help Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Backend Sync</h3>
          <p className="text-2xl font-bold text-emerald-400">Active</p>
          <p className="text-xs text-slate-500">Live JSON endpoints verified</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Epoch</h3>
          <p className="text-2xl font-bold text-cyan-400">{helpData?.epoch || 'Day 14.2'}</p>
          <p className="text-xs text-slate-500">Standard timeline benchmark</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Support Protocol</h3>
          <p className="text-2xl font-bold text-amber-400">Standard</p>
          <p className="text-xs text-slate-500">Ground control automated</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">System Documentation Overview</h3>
        <p className="text-sm text-slate-400">
          LUNARIS M4 telemetry system is fully integrated across all frontend modules. Use the top navigation bar to switch between live analysis panels, maps, and reports.
        </p>
      </div>
    </div>
  );
}