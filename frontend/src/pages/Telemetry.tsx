import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function Telemetry() {
  // State to store live telemetry data fetched from the backend API
  const [telemetryData, setTelemetryData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Fetch telemetry and sensor information when component mounts
    const fetchTelemetry = async () => {
      try {
        const response = await getLunarData();
        if (response && response.telemetry) {
          setTelemetryData(response.telemetry);
        }
      } catch (error) {
        console.error('Error fetching telemetry data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTelemetry();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading telemetry sensors from server...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Mission Telemetry & Sensors</h1>
        <p className="text-slate-400 mt-1">Real-time environmental and spacecraft telemetry streamed directly from the backend.</p>
      </div>

      {/* Telemetry Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Solar Irradiance</h3>
          <p className="text-2xl font-bold text-amber-400">{telemetryData?.solarIrradiance || 'N/A'}</p>
          <p className="text-xs text-slate-500">Nominal photon flux density</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Thermal Range</h3>
          <p className="text-2xl font-bold text-cyan-400">{telemetryData?.thermalRange || 'N/A'}</p>
          <p className="text-xs text-slate-500">Surface operational temperature</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Communication Delay</h3>
          <p className="text-2xl font-bold text-emerald-400">{telemetryData?.communicationDelay || 'N/A'}</p>
          <p className="text-xs text-slate-500">Earth-Moon round-trip latency</p>
        </div>
      </div>
    </div>
  );
}