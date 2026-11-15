import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function PowerModel() {
  const [powerData, setPowerData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchPowerInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setPowerData(response);
        }
      } catch (error) {
        console.error('Error fetching power model data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPowerInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading power generation and battery status...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Power Generation & Storage Model</h1>
        <p className="text-slate-400 mt-1">Real-time photovoltaic output, battery state of charge (SoC), and power distribution.</p>
      </div>

      {/* Power Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Solar Generation</h3>
          <p className="text-2xl font-bold text-emerald-400">4.8 kW</p>
          <p className="text-xs text-slate-500">Peak photovoltaic array output</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Battery Storage (SoC)</h3>
          <p className="text-2xl font-bold text-cyan-400">92.4%</p>
          <p className="text-xs text-slate-500">Li-ion secondary cell reserves</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">System Load</h3>
          <p className="text-2xl font-bold text-amber-400">2.1 kW</p>
          <p className="text-xs text-slate-500">Active avionics and life support</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Energy Balance Status</h3>
        <p className="text-sm text-slate-400">
          Power generation exceeds current consumption load by 2.7 kW. Battery bank is actively charging under nominal solar flux conditions.
        </p>
      </div>
    </div>
  );
}