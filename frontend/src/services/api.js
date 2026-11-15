// Vite proxy configuration uses '/api' prefix directly
const BASE_URL = '/api';

// 1. Fetch general lunar telemetry data
export const getLunarData = async () => {
  try {
    const response = await fetch(`${BASE_URL}/lunar-data`);
    if (!response.ok) {
      throw new Error('Failed to fetch lunar data');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching lunar data:', error);
    return null;
  }
};

// 2. Fetch all previously saved/locked landing sites from backend storage
export const getSavedSites = async () => {
  try {
    const response = await fetch(`${BASE_URL}/saved-sites`);
    if (!response.ok) {
      throw new Error('Failed to fetch saved sites');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching saved sites:', error);
    return null;
  }
};

// 3. Save landing site coordinates to backend via POST request
export const saveLandingSite = async (siteData) => {
  try {
    const response = await fetch(`${BASE_URL}/select-site`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(siteData),
    });
    
    if (!response.ok) {
      throw new Error('Failed to save landing site');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error saving landing site:', error);
    throw error;
  }
};

export default {
  getLunarData,
  getSavedSites,
  saveLandingSite,
};