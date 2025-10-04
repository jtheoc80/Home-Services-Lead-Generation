import { MapPin, Check } from "lucide-react";
import Card from "./Card";
import Badge from "./Badge";
import clsx from "clsx";

interface TexasCountyProps {
  selectedCounties: string[];
  onCountyChange: (counties: string[]) => void;
  showStats?: boolean;
}

const TEXAS_COUNTIES = [
  { name: "Harris County (Houston)", code: "harris", population: "4.7M", permits: 2847 },
  { name: "Dallas County", code: "dallas", population: "2.6M", permits: 1543 },
  { name: "Travis County (Austin)", code: "travis", population: "1.3M", permits: 892 },
  { name: "Fort Bend County", code: "fortbend", population: "822K", permits: 689 }
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

  const totalPermits = TEXAS_COUNTIES
    .filter(c => selectedCounties.includes(c.code))
    .reduce((sum, county) => sum + county.permits, 0);

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <MapPin className="w-5 h-5 text-texas-600" />
          <h3 className="text-lg font-semibold text-gray-900">Texas Counties</h3>
        </div>
        <button
          onClick={toggleAll}
          className="text-sm text-brand-600 hover:text-brand-700 font-medium"
        >
          {selectedCounties.length === TEXAS_COUNTIES.length ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      {showStats && (
        <div className="mb-4 p-3 bg-texas-50 rounded-lg border border-texas-200">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Selected Counties:</span>
              <span className="ml-2 font-semibold text-texas-700">
                {selectedCounties.length}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Active Permits:</span>
              <span className="ml-2 font-semibold text-texas-700">
                {totalPermits.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {TEXAS_COUNTIES.map((county) => {
          const isSelected = selectedCounties.includes(county.code);
          
          return (
            <div
              key={county.code}
              onClick={() => handleCountyToggle(county.code)}
              className={clsx(
                "flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all duration-200",
                isSelected
                  ? "bg-texas-50 border-texas-300 shadow-soft"
                  : "bg-white border-gray-200 hover:bg-gray-50"
              )}
            >
              <div className="flex items-center space-x-3">
                <div className={clsx(
                  "w-5 h-5 rounded border-2 flex items-center justify-center",
                  isSelected
                    ? "bg-texas-600 border-texas-600"
                    : "border-gray-300"
                )}>
                  {isSelected && <Check className="w-3 h-3 text-white" />}
                </div>
                
                <div>
                  <div className="font-medium text-gray-900">{county.name}</div>
                  <div className="text-sm text-gray-500">
                    Pop: {county.population}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <Badge variant="texas" size="sm">
                  {county.permits} permits
                </Badge>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}