import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function MissionPlanner() {
  const [plannerData, setPlannerData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchPlannerInfo = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setPlannerData(response);
        }
      } catch (error) {
        console.error('Error fetching mission planner data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlannerInfo();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading mission schedule and timeline phases...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Mission Planner & Timeline</h1>
        <p className="text-slate-400 mt-1">Schedule operational milestones, sequence rover tasks, and manage surface deployment phases.</p>
      </div>

      {/* Planner Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Phase</h3>
          <p className="text-2xl font-bold text-emerald-400">Phase II (Surface Ops)</p>
          <p className="text-xs text-slate-500">Nominal deployment stage</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Scheduled Tasks</h3>
          <p className="text-2xl font-bold text-cyan-400">14 / 14 Completed</p>
          <p className="text-xs text-slate-500">Automated sequence check</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Timeline Status</h3>
          <p className="text-2xl font-bold text-amber-400">On Schedule</p>
          <p className="text-xs text-slate-500">Zero drift from ephemeris</p>
        </div>
      </div>

      {/* Status Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Mission Planning Summary</h3>
        <p className="text-sm text-slate-400">
          All milestones for epoch ({plannerData?.epoch || 'Day 14.2'}) are fully synchronized with the backend telemetry server. Ready for final system configurations.
        </p>
      </div>
    </div>
  );
}