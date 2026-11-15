import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function DateShift() {
  const [shiftData, setShiftData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchShiftInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setShiftData(response);
        }
      } catch (error) {
        console.error('Error fetching date shift data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchShiftInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading mission timeline and epoch shifts...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Mission Date & Epoch Shift</h1>
        <p className="text-slate-400 mt-1">Adjust mission timeline, calculate orbital propagation delays, and shift landing epochs.</p>
      </div>

      {/* Date Shift Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Current Epoch</h3>
          <p className="text-2xl font-bold text-cyan-400">{shiftData?.epoch || 'Day 14.2'}</p>
          <p className="text-xs text-slate-500">Active baseline timeline</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Time Offset</h3>
          <p className="text-2xl font-bold text-emerald-400">+0.00 Std</p>
          <p className="text-xs text-slate-500">Zero drift from UTC baseline</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Orbital Sync</h3>
          <p className="text-2xl font-bold text-amber-400">Synchronized</p>
          <p className="text-xs text-slate-500">Ephemeris table locked</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Timeline Management Note</h3>
        <p className="text-sm text-slate-400">
          Shifting the mission epoch updates all downstream landing calculations and solar illumination forecasts dynamically via backend telemetry.
        </p>
      </div>
    </div>
  );
}