import React, { useState, useEffect } from 'react';

interface Metro {
  id: string;
  region_id: string;
  display_name: string;
  short_name: string;
  center_lat: number;
  center_lng: number;
  radius_miles: number;
  description: string;
}

interface RegionsData {
  regions: Record<string, any>;
  default_region: string;
  default_metro: string;
  available_metros: Metro[];
}

interface RegionSelectorProps {
  selectedRegion?: string;
  selectedMetro?: string;
  onRegionChange?: (regionId: string, metroId: string) => void;
  className?: string;
}

export default function RegionSelector({ 
  selectedRegion, 
  selectedMetro, 
  onRegionChange,
  className = ""
}: RegionSelectorProps) {
  const [regionsData, setRegionsData] = useState<RegionsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRegions();
  }, []);

  const fetchRegions = async () => {
    try {
      const response = await fetch('/api/regions');
      if (!response.ok) {
        throw new Error('Failed to fetch regions');
      }
      const data = await response.json();
      setRegionsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleMetroChange = (metroId: string) => {
    if (!regionsData) return;
    
    const metro = regionsData.available_metros.find(m => m.id === metroId);
    if (metro && onRegionChange) {
      onRegionChange(metro.region_id, metroId);
    }
  };

  if (loading) {
    return (
      <div className={`${className}`}>
        <div className="animate-pulse">
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className}`}>
        <div className="text-red-600 text-sm">
          Error loading regions: {error}
        </div>
      </div>
    );
  }

  if (!regionsData) {
    return null;
  }

  const currentMetroId = selectedMetro || regionsData.default_metro;

  return (
    <div className={className}>
      <label htmlFor="metro-select" className="block text-sm font-medium text-gray-700 mb-2">
        Select Region
      </label>
      <select
        id="metro-select"
        value={currentMetroId}
        onChange={(e) => handleMetroChange(e.target.value)}
        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      >
        {regionsData.available_metros.map((metro) => (
          <option key={metro.id} value={metro.id}>
            {metro.display_name}
          </option>
        ))}
      </select>
      
      {regionsData.available_metros.find(m => m.id === currentMetroId) && (
        <p className="mt-1 text-xs text-gray-500">
          {regionsData.available_metros.find(m => m.id === currentMetroId)?.description}
        </p>
      )}
    </div>
  );
}