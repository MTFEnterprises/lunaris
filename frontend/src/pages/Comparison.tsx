import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function Comparison() {
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchComparisonInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setComparisonData(response);
        }
      } catch (error) {
        console.error('Error fetching comparison data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchComparisonInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading site comparison metrics...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Mission Landing Site Comparison</h1>
        <p className="text-slate-400 mt-1">Comparative safety index, illumination duration, and terrain roughness across selected sites.</p>
      </div>

      {/* Comparison Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-3">
          <h3 className="text-lg font-semibold text-slate-200">Site Alpha (Mare Tranquillitatis)</h3>
          <p className="text-sm text-slate-400">Safety Index: <span className="text-emerald-400 font-bold">High</span></p>
          <p className="text-sm text-slate-400">Illumination Window: <span className="text-cyan-400 font-bold">354 Hours</span></p>
          <p className="text-xs text-slate-500">Flat basaltic plain, minimal slope obstruction.</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-3">
          <h3 className="text-lg font-semibold text-slate-200">Site Beta (Oceanus Procellarum)</h3>
          <p className="text-sm text-slate-400">Safety Index: <span className="text-amber-400 font-bold">Moderate</span></p>
          <p className="text-sm text-slate-400">Illumination Window: <span className="text-cyan-400 font-bold">320 Hours</span></p>
          <p className="text-xs text-slate-500">Contains minor crater rims and undulating regolith hills.</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Comparative Analysis Summary</h3>
        <p className="text-sm text-slate-400">
          Current mission epoch ({comparisonData?.epoch || 'Day 14.2'}) favors Site Alpha for long-term photovoltaic efficiency and stable thermal constraints.
        </p>
      </div>
    </div>
  );
}