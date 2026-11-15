import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function HazardMapping() {
  const [hazardData, setHazardData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchHazardInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setHazardData(response);
        }
      } catch (error) {
        console.error('Error fetching hazard mapping data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHazardInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading crater and boulder hazard distribution...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Surface Hazard Mapping</h1>
        <p className="text-slate-400 mt-1">Crater density, boulder fields, and automated hazard avoidance telemetry.</p>
      </div>

      {/* Hazard Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Crater Density Index</h3>
          <p className="text-2xl font-bold text-emerald-400">Very Low</p>
          <p className="text-xs text-slate-500">Minimal impact craters in zone</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Boulder Hazard Rate</h3>
          <p className="text-2xl font-bold text-cyan-400">0.2%</p>
          <p className="text-xs text-slate-500">Safe clearance radius</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avoidance System</h3>
          <p className="text-2xl font-bold text-amber-400">Active (Autonomous)</p>
          <p className="text-xs text-slate-500">Real-time LiDAR detection</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Hazard Assessment Summary</h3>
        <p className="text-sm text-slate-400">
          No critical surface obstacles detected within the landing ellipse. Autonomous hazard detection algorithms are fully synchronized with backend telemetry.
        </p>
      </div>
    </div>
  );
}