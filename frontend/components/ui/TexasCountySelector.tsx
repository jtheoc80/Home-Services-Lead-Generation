import { MapPin, Check, Users, Building2, TrendingUp, Star } from "lucide-react";
import Card from "./Card";
import Badge from "./Badge";
import clsx from "clsx";

interface TexasCountyProps {
  selectedCounties: string[];
  onCountyChange: (counties: string[]) => void;
  showStats?: boolean;
}

const TEXAS_COUNTIES = [
  { 
    name: "Greater Houston", 
    code: "harris", 
    population: "4.7M", 
    permits: 2847,
    county: "Harris County",
    hotLeads: 24,
    avgValue: "$85K"
  },
  { 
    name: "Dallas", 
    code: "dallas", 
    population: "2.6M", 
    permits: 1543,
    county: "Dallas County",
    hotLeads: 18,
    avgValue: "$72K"
  },
  { 
    name: "Austin", 
    code: "austin", 
    population: "1.0M", 
    permits: 892,
    county: "Travis County",
    hotLeads: 12,
    avgValue: "$95K"
  },
  { 
    name: "Fort Worth", 
    code: "tarrant", 
    population: "956K", 
    permits: 0,
    county: "Tarrant County",
    hotLeads: 0,
    avgValue: "$68K"
  },
  { 
    name: "San Antonio", 
    code: "bexar", 
    population: "1.5M", 
    permits: 0,
    county: "Bexar County",
    hotLeads: 0,
    avgValue: "$62K"
  },
  { 
    name: "El Paso", 
    code: "elpaso", 
    population: "678K", 
    permits: 0,
    county: "El Paso County",
    hotLeads: 0,
    avgValue: "$58K"
  }
];

export default function TexasCountySelector({
  selectedCounties,
  onCountyChange,
  showStats = true
}: TexasCountyProps) {
  const handleCountyToggle = (countyCode: string) => {
    if (selectedCounties.includes(countyCode)) {
      onCountyChange(selectedCounties.filter(c => c !== countyCode));
    } else {
      onCountyChange([...selectedCounties, countyCode]);
    }
  };

  const toggleAll = () => {
    if (selectedCounties.length === TEXAS_COUNTIES.length) {
      onCountyChange([]);
    } else {
      onCountyChange(TEXAS_COUNTIES.map(c => c.code));
    }
  };

  const stats = TEXAS_COUNTIES
    .filter(c => selectedCounties.includes(c.code))
    .reduce((acc, county) => ({
      metros: acc.metros + 1,
      population: acc.population + parseFloat(county.population.replace(/[MK]/g, match => match === 'M' ? '000000' : '000')),
      permits: acc.permits + county.permits,
      hotLeads: acc.hotLeads + county.hotLeads
    }), { metros: 0, population: 0, permits: 0, hotLeads: 0 });

  const formatPopulation = (pop: number) => {
    if (pop >= 1000000) return `${(pop / 1000000).toFixed(1)}M`;
    if (pop >= 1000) return `${(pop / 1000).toFixed(0)}K`;
    return pop.toString();
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <MapPin className="w-5 h-5 text-navy-600" />
            <h3 className="text-lg font-semibold text-gray-900">Texas Metro Areas</h3>
          </div>
          <p className="text-sm text-gray-500">Select markets to view leads</p>
        </div>
        <button
          onClick={toggleAll}
          className="text-sm text-navy-600 hover:text-navy-700 font-medium px-3 py-1.5 rounded-lg hover:bg-navy-50 transition-colors"
        >
          {selectedCounties.length === TEXAS_COUNTIES.length ? 'Clear All' : 'Select All'}
        </button>
      </div>

      {showStats && selectedCounties.length > 0 && (
        <div className="mb-6 p-4 bg-gradient-to-br from-navy-50 to-slate-50 rounded-xl border border-navy-200">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-navy-600 flex items-center justify-center">
                <Building2 className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Metro Areas</div>
                <div className="text-lg font-bold text-navy-700">{stats.metros}</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                <Users className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Population</div>
                <div className="text-lg font-bold text-blue-700">{formatPopulation(stats.population)}</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-green-600 flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Active Leads</div>
                <div className="text-lg font-bold text-green-700">{stats.permits.toLocaleString()}</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-orange-600 flex items-center justify-center">
                <Star className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Hot Leads</div>
                <div className="text-lg font-bold text-orange-700">{stats.hotLeads}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3">
        {TEXAS_COUNTIES.map((metro) => {
          const isSelected = selectedCounties.includes(metro.code);
          
          return (
            <div
              key={metro.code}
              onClick={() => handleCountyToggle(metro.code)}
              className={clsx(
                "relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 group",
                isSelected
                  ? "bg-gradient-to-br from-navy-50 to-blue-50 border-navy-400 shadow-md"
                  : "bg-white border-slate-200 hover:border-navy-300 hover:shadow-sm"
              )}
            >
              {/* Selection Indicator */}
              <div className="absolute top-3 right-3">
                <div className={clsx(
                  "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all",
                  isSelected
                    ? "bg-navy-600 border-navy-600 scale-110"
                    : "border-slate-300 group-hover:border-navy-400"
                )}>
                  {isSelected && <Check className="w-3 h-3 text-white" />}
                </div>
              </div>

              {/* Metro Info */}
              <div className="pr-8">
                <h4 className="font-semibold text-gray-900 mb-0.5">{metro.name}</h4>
                <p className="text-xs text-gray-500 mb-3">{metro.county}</p>
                
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500">Pop:</span>
                    <span className="ml-1 font-semibold text-gray-700">{metro.population}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Avg Value:</span>
                    <span className="ml-1 font-semibold text-gray-700">{metro.avgValue}</span>
                  </div>
                </div>

                {/* Leads Badge */}
                <div className="mt-3 flex items-center justify-between">
                  <Badge 
                    variant={isSelected ? "texas" : "default"} 
                    size="sm"
                  >
                    {metro.permits} leads
                  </Badge>
                  {metro.hotLeads > 0 && (
                    <div className="flex items-center space-x-1 text-xs font-medium text-orange-600">
                      <Star className="w-3 h-3 fill-orange-600" />
                      <span>{metro.hotLeads} hot</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}