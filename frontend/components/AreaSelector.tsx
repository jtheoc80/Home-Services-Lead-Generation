import React, { useState, useEffect } from 'react'

interface Area {
  name: string
  code: string
}

interface AreasByType {
  zips: Area[]
  council_districts: Area[]
  super_neighborhoods: Area[]
}

interface FocusArea {
  account_id: string
  mode: 'zip' | 'council' | 'neighborhood' | 'radius'
  codes?: string[]
  center_lat?: number
  center_lon?: number
  radius_miles?: number
}

interface AreaSelectorProps {
  accountId: string
  onSave?: (focusArea: FocusArea) => void
}

export default function AreaSelector({ accountId, onSave }: AreaSelectorProps) {
  const [availableAreas, setAvailableAreas] = useState<AreasByType>({
    zips: [],
    council_districts: [],
    super_neighborhoods: []
  })
  const [focusMode, setFocusMode] = useState<'zip' | 'council' | 'neighborhood' | 'radius'>('zip')
  const [selectedCodes, setSelectedCodes] = useState<string[]>([])
  const [radiusCenter, setRadiusCenter] = useState({ lat: HOUSTON_CENTER_LAT, lon: HOUSTON_CENTER_LON }) // Houston center
  const [radiusMiles, setRadiusMiles] = useState(10)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')

  // Load available areas on mount
  useEffect(() => {
    loadAvailableAreas()
    loadUserFocusArea()
  }, [accountId])

  const loadAvailableAreas = async () => {
    try {
      // Mock API call - in real implementation, this would call the backend API
      const mockAreas: AreasByType = {
        zips: [
          { name: "Houston Heights - 77008", code: "77008" },
          { name: "Downtown - 77002", code: "77002" },
          { name: "River Oaks - 77019", code: "77019" },
          { name: "Montrose - 77006", code: "77006" },
          { name: "Bellaire - 77401", code: "77401" }
        ],
        council_districts: [
          { name: "District A", code: "A" },
          { name: "District B", code: "B" },
          { name: "District C", code: "C" },
          { name: "District D", code: "D" },
          { name: "District E", code: "E" }
        ],
        super_neighborhoods: [
          { name: "Greater Heights", code: "HEIGHTS" },
          { name: "Near Northside", code: "NEAR_NORTHSIDE" },
          { name: "Montrose", code: "MONTROSE" },
          { name: "Museum District", code: "MUSEUM" },
          { name: "River Oaks", code: "RIVER_OAKS" },
          { name: "Galleria/Uptown", code: "GALLERIA" }
        ]
      }
      setAvailableAreas(mockAreas)
    } catch (error) {
      console.error('Error loading areas:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadUserFocusArea = async () => {
    try {
      // Mock API call - load user's saved focus area
      // In real implementation, this would call the backend API
      console.log('Loading focus area for account:', accountId)
    } catch (error) {
      console.error('Error loading user focus area:', error)
    }
  }

  const handleCodeToggle = (code: string) => {
    setSelectedCodes(prev => 
      prev.includes(code) 
        ? prev.filter(c => c !== code)
        : [...prev, code]
    )
  }

  const handleSave = async () => {
    setSaving(true)
    setSavedMessage('')
    
    try {
      const focusArea: FocusArea = {
        account_id: accountId,
        mode: focusMode,
        ...(focusMode === 'radius' 
          ? {
              center_lat: radiusCenter.lat,
              center_lon: radiusCenter.lon,
              radius_miles: radiusMiles
            }
          : {
              codes: selectedCodes
            }
        )
      }

      // Mock API call - save focus area
      // In real implementation, this would call the backend API
      console.log('Saving focus area:', focusArea)
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setSavedMessage('Focus area saved successfully!')
      onSave?.(focusArea)
      
      // Clear message after 3 seconds
      setTimeout(() => setSavedMessage(''), 3000)
      
    } catch (error) {
      console.error('Error saving focus area:', error)
      setSavedMessage('Error saving focus area. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">Loading geographic areas...</div>
      </div>
    )
  }

  const getCurrentAreas = () => {
    switch (focusMode) {
      case 'zip': return availableAreas.zips
      case 'council': return availableAreas.council_districts
      case 'neighborhood': return availableAreas.super_neighborhoods
      default: return []
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Set Your Focus Area</h3>
      
      {/* Mode Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Filter Type</label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <button
            onClick={() => setFocusMode('zip')}
            className={`p-2 rounded text-sm font-medium ${
              focusMode === 'zip' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            ZIP Codes
          </button>
          <button
            onClick={() => setFocusMode('council')}
            className={`p-2 rounded text-sm font-medium ${
              focusMode === 'council' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Council Districts
          </button>
          <button
            onClick={() => setFocusMode('neighborhood')}
            className={`p-2 rounded text-sm font-medium ${
              focusMode === 'neighborhood' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Super Neighborhoods
          </button>
          <button
            onClick={() => setFocusMode('radius')}
            className={`p-2 rounded text-sm font-medium ${
              focusMode === 'radius' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Custom Radius
          </button>
        </div>
      </div>

      {/* Area Selection */}
      {focusMode !== 'radius' ? (
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Select {focusMode === 'zip' ? 'ZIP Codes' : 
                   focusMode === 'council' ? 'Council Districts' : 
                   'Super Neighborhoods'}
          </label>
          <div className="max-h-60 overflow-y-auto border rounded p-4 space-y-2">
            {getCurrentAreas().map((area) => (
              <label key={area.code} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedCodes.includes(area.code)}
                  onChange={() => handleCodeToggle(area.code)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm">{area.name}</span>
              </label>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {selectedCodes.length} area{selectedCodes.length !== 1 ? 's' : ''} selected
          </p>
        </div>
      ) : (
        <div className="mb-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Center Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={radiusCenter.lat}
                onChange={(e) => setRadiusCenter(prev => ({ ...prev, lat: parseFloat(e.target.value) }))}
                className="w-full px-3 py-2 border rounded focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Center Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={radiusCenter.lon}
                onChange={(e) => setRadiusCenter(prev => ({ ...prev, lon: parseFloat(e.target.value) }))}
                className="w-full px-3 py-2 border rounded focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Radius (miles)</label>
            <input
              type="number"
              min="1"
              max="50"
              value={radiusMiles}
              onChange={(e) => setRadiusMiles(parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      )}

      {/* Save Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleSave}
          disabled={saving || (focusMode !== 'radius' && selectedCodes.length === 0)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Focus Area'}
        </button>
        
        {savedMessage && (
          <span className={`text-sm ${
            savedMessage.includes('Error') ? 'text-red-600' : 'text-green-600'
          }`}>
            {savedMessage}
          </span>
        )}
      </div>
      
      {/* Help Text */}
      <div className="mt-4 text-xs text-gray-500">
        <p>Your focus area will be automatically applied to future lead searches and dashboard views.</p>
      </div>
    </div>
  )
}