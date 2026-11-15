import React, { useState, useEffect } from 'react';
import { saveLandingSite, getSavedSites } from '../services/api';

export default function SitePicker() {
  const [selectedSite, setSelectedSite] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const [savedSitesList, setSavedSitesList] = useState<any[]>([]);

  const landingSites = [
    { id: 1, name: 'Site Alpha (Mare Tranquillitatis)', coords: '0.674° N, 23.472° E', safety: 'High' },
    { id: 2, name: 'Site Beta (Oceanus Procellarum)', coords: '2.15° S, 41.53° W', safety: 'Moderate' },
    { id: 3, name: 'Site Gamma (Schickard Basin)', coords: '44.3° S, 55.3° W', safety: 'Optimal' },
    { id: 4, name: 'Site Delta (Aristarchus Plateau)', coords: '23.7° N, 47.4° W', safety: 'Challenging' },
  ];

  // Fetch previously saved sites from backend when component mounts
  const fetchSavedSites = async () => {
    try {
      const result = await getSavedSites();
      if (result && result.data) {
        setSavedSitesList(result.data);
      }
    } catch (error) {
      console.error('Error loading saved sites history:', error);
    }
  };

  useEffect(() => {
    fetchSavedSites();
  }, []);

  // Handle site selection and send payload to Express backend API via POST request
  const handleLockSite = async (site: typeof landingSites[0]) => {
    setLoading(true);
    setMessage('');
    setSelectedSite(site.name);

    try {
      const payload = {
        siteId: site.id,
        siteName: site.name,
        coordinates: site.coords,
        safetyIndex: site.safety,
        timestamp: new Date().toISOString(),
        status: 'Locked'
      };

      const response = await saveLandingSite(payload);
      setMessage(response?.message || `Successfully locked and saved coordinates for ${site.name}!`);
      
      // Refresh the saved sites history list after successful post
      fetchSavedSites();
    } catch (error) {
      console.error('Failed to save landing site:', error);
      setMessage('Error: Failed to connect with backend server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">Landing Site Selector</h1>
        <p className="text-slate-400 mt-1">Select and lock optimal lunar landing coordinates for LUNARIS M4 mission.</p>
      </div>

      {/* Grid of available landing sites */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {landingSites.map((site) => (
          <div 
            key={site.id} 
            className={`bg-slate-900/80 border p-6 rounded-xl space-y-4 transition ${
              selectedSite === site.name ? 'border-cyan-500 shadow-lg shadow-cyan-500/10' : 'border-slate-800'
            }`}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold text-slate-100">{site.name}</h3>
                <p className="text-sm text-slate-400 mt-1">Coords: {site.coords}</p>
              </div>
              <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                site.safety === 'Optimal' || site.safety === 'High' 
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              }`}>
                {site.safety}
              </span>
            </div>

            <button
              onClick={() => handleLockSite(site)}
              disabled={loading}
              className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 text-white font-medium rounded-lg transition duration-200 shadow-md"
            >
              {loading && selectedSite === site.name ? 'Locking Coordinates...' : 'Confirm & Lock Site'}
            </button>
          </div>
        ))}
      </div>

      {/* Feedback message container */}
      {message && (
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <p className="text-sm text-cyan-400 font-medium">{message}</p>
        </div>
      )}

      {/* Locked Sites History Section */}
      <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl space-y-4">
        <h3 className="text-xl font-bold text-slate-100">Locked Sites History (Server Storage)</h3>
        {savedSitesList.length === 0 ? (
          <p className="text-sm text-slate-500">No sites locked yet. Select a site above to save it to the server.</p>
        ) : (
          <div className="space-y-3">
            {savedSitesList.map((item, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-slate-950 border border-slate-800/80 rounded-lg">
                <div>
                  <p className="text-sm font-semibold text-cyan-400">{item.siteName}</p>
                  <p className="text-xs text-slate-400">Coords: {item.coordinates} | Safety: {item.safetyIndex}</p>
                </div>
                <span className="text-xs text-slate-500">{new Date(item.timestamp).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}