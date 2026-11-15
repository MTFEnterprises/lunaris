import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function Settings() {
  const [settingsData, setSettingsData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchSettingsInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setSettingsData(response);
        }
      } catch (error) {
        console.error('Error fetching settings data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSettingsInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading system configuration parameters...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">System Configuration & Settings</h1>
        <p className="text-slate-400 mt-1">Manage telemetry refresh rates, backend endpoint synchronization, and UI preferences.</p>
      </div>

      {/* Settings Options Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Telemetry Refresh Rate</h3>
          <p className="text-2xl font-bold text-emerald-400">1000 ms</p>
          <p className="text-xs text-slate-500">Real-time socket polling</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Backend API Status</h3>
          <p className="text-2xl font-bold text-cyan-400">Connected</p>
          <p className="text-xs text-slate-500">Express server active</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Unit System</h3>
          <p className="text-2xl font-bold text-amber-400">Metric (SI)</p>
          <p className="text-xs text-slate-500">Standard aerospace units</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Configuration Management</h3>
        <p className="text-sm text-slate-400">
          Mission parameters and server linkages are fully operational for epoch ({settingsData?.epoch || 'Day 14.2'}). 
        </p>
      </div>
    </div>
  );
}