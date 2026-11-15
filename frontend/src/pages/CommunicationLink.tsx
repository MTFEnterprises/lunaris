import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function CommunicationLink() {
  const [commData, setCommData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchCommInfo = async () => {
      try {
        const response = await getLunarData();
        if (response && response.telemetry) {
          setCommData(response.telemetry);
        }
      } catch (error) {
        console.error('Error fetching communication link data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCommInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading deep space network link parameters...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Deep Space Communication Link</h1>
        <p className="text-slate-400 mt-1">Earth-Moon round-trip latency, signal-to-noise ratio, and relay satellite status.</p>
      </div>

      {/* Communication Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Round-Trip Latency</h3>
          <p className="text-2xl font-bold text-emerald-400">{commData?.communicationDelay || '2.68 s'}</p>
          <p className="text-xs text-slate-500">Earth-Moon propagation delay</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Signal Strength (SNR)</h3>
          <p className="text-2xl font-bold text-cyan-400">24.5 dB</p>
          <p className="text-xs text-slate-500">X-band carrier frequency lock</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Uplink / Downlink Rate</h3>
          <p className="text-2xl font-bold text-amber-400">12.8 Mbps</p>
          <p className="text-xs text-slate-500">High-throughput data stream</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Relay Station Status</h3>
        <p className="text-sm text-slate-400">
          Direct line of sight with the Earth tracking station is optimal. Packet loss is currently at 0.00% with stable error-correction protocols active.
        </p>
      </div>
    </div>
  );
}