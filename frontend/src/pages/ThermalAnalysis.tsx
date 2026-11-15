import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function ThermalAnalysis() {
  const [thermalData, setThermalData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchThermalInfo = async () => {
      try {
        const response = await getLunarData();
        if (response && response.telemetry) {
          setThermalData(response.telemetry);
        }
      } catch (error) {
        console.error('Error fetching thermal analysis data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchThermalInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading thermal sensors and regolith temperatures...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Thermal Analysis & Regolith Heat</h1>
        <p className="text-slate-400 mt-1">Surface thermal dissipation, radiator efficiency, and internal structural temperatures.</p>
      </div>

      {/* Thermal Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Surface Thermal Range</h3>
          <p className="text-2xl font-bold text-cyan-400">{thermalData?.thermalRange || '+120°C to -130°C'}</p>
          <p className="text-xs text-slate-500">Regolith interface extremes</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Radiator Panels</h3>
          <p className="text-2xl font-bold text-emerald-400">Optimal (88%)</p>
          <p className="text-xs text-slate-500">Active heat rejection efficiency</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Internal Avionics Temp</h3>
          <p className="text-2xl font-bold text-amber-400">22.5°C</p>
          <p className="text-xs text-slate-500">Nominal climate control zone</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Thermal Equilibrium Status</h3>
        <p className="text-sm text-slate-400">
          All internal electronics and battery compartments remain well within safe operational limits. Radiator louvers are automatically adjusting to reflect intense solar glare.
        </p>
      </div>
    </div>
  );
}