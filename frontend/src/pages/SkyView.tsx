import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function SkyView() {
  const [skyData, setSkyData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchSkyInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setSkyData(response);
        }
      } catch (error) {
        console.error('Error fetching sky view data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSkyInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading celestial coordinates and sky grid...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Lunar Sky View & Celestial Grid</h1>
        <p className="text-slate-400 mt-1">Real-time stellar tracking, horizon elevation, and Earth positioning relative to LUNARIS M4.</p>
      </div>

      {/* Sky View Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-3">
          <h3 className="text-lg font-semibold text-slate-200">Current Mission Epoch</h3>
          <p className="text-xl font-bold text-cyan-400">{skyData?.epoch || 'Day 14.2 Lunar Noon'}</p>
          <p className="text-sm text-slate-400">Stellar alignment is optimal for optical and thermal observation.</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-3">
          <h3 className="text-lg font-semibold text-slate-200">Horizon Visibility Status</h3>
          <span className="inline-block px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs rounded-full font-medium">
            Clear Line of Sight
          </span>
          <p className="text-sm text-slate-400">Direct communication window with orbital relay is fully active.</p>
        </div>
      </div>

      {/* Visual Simulation Box */}
      <div className="bg-slate-950 border border-slate-800 p-8 rounded-xl text-center space-y-4">
        <div className="w-20 h-20 mx-auto rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center animate-pulse">
          <span className="text-cyan-400 text-2xl font-bold">🔭</span>
        </div>
        <h3 className="text-xl font-bold text-slate-100">Celestial Tracking Active</h3>
        <p className="text-sm text-slate-400 max-w-md mx-auto">
          Tracking coordinates synced with backend telemetry stream. No atmospheric distortion detected.
        </p>
      </div>
    </div>
  );
}