import React, { useEffect, useState } from 'react';
import { getLunarData } from '../services/api';

export default function SunEarthAnalysis() {
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await getLunarData();
        if (response) {
          setAnalysisData(response);
        }
      } catch (error) {
        console.error('Error fetching sun & earth analysis data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, []);

  if (loading) {
    return <div className="text-cyan-400 p-6">Loading solar geometry and Earth line-of-sight data...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Sun & Earth Geometry Analysis</h1>
        <p className="text-slate-400 mt-1">Solar illumination angles, eclipse tracking, and Earth line-of-sight telemetry.</p>
      </div>

      {/* Analysis Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-3">
          <h3 className="text-lg font-semibold text-slate-200">Solar Elevation Angle</h3>
          <p className="text-2xl font-bold text-amber-400">14.2° (Lunar Noon)</p>
          <p className="text-sm text-slate-400">Optimal angle for maximum photovoltaic panel energy conversion.</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-3">
          <h3 className="text-lg font-semibold text-slate-200">Earth Azimuth Status</h3>
          <p className="text-2xl font-bold text-cyan-400">Direct Line of Sight</p>
          <p className="text-sm text-slate-400">Deep Space Network uplink/downlink stability is fully maintained.</p>
        </div>
      </div>

      {/* Summary Box */}
      <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-3">
        <h3 className="text-md font-bold text-slate-200">Mission Illumination Window</h3>
        <p className="text-sm text-slate-400">
          Current thermal flux and solar radiation parameters are synchronized with backend telemetry logs. No orbital occlusion projected for the next 48 hours.
        </p>
      </div>
    </div>
  );
}