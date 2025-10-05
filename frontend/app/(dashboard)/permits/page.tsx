'use client';

import { useState } from 'react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { Search, FileText, MapPin, Calendar, DollarSign, Hash } from 'lucide-react';

type Permit = {
  id: string;
  address: string;
  trade: string;
  status: string;
  submitted_at?: string | null;
  value?: number;
  county?: string;
};

export default function PermitsPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Permit[]>([]);
  const [recent, setRecent] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function searchPermits(e?: React.FormEvent, directQuery?: string) {
    e?.preventDefault();
    const searchQuery = directQuery || query;
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      // TODO: wire to your real backend/scraper
      const mock: Permit[] = [
        { 
          id: searchQuery, 
          address: searchQuery, 
          trade: 'Roofing', 
          status: 'Submitted', 
          submitted_at: new Date().toISOString(),
          value: 45000,
          county: 'Harris'
        },
      ];
      setResults(mock);
      setRecent((prev) => [searchQuery, ...prev.filter((q) => q !== searchQuery)].slice(0, 5));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 space-y-6 bg-gradient-to-br from-gray-50 to-white min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Permits Search</h1>
          <p className="text-slate-600 mt-1">Search Texas permits by address, permit number, or county</p>
        </div>
      </div>

      {/* Search Card */}
      <Card className="p-6 border-l-4 border-navy-600">
        <form onSubmit={searchPermits} className="space-y-4">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by address, permit #, or county..."
              className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-300 outline-none focus:ring-2 focus:ring-navy-500 focus:border-navy-500 transition-all text-gray-900 placeholder:text-slate-400"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto px-8 py-3 bg-navy-600 text-white font-medium rounded-xl hover:bg-navy-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-all duration-200 shadow-soft"
          >
            {loading ? 'Searching...' : 'Search Permits'}
          </button>
        </form>
      </Card>

      {/* Recent Searches */}
      {recent.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Recent Searches</h2>
          <div className="flex flex-wrap gap-2">
            {recent.map((q) => (
              <button
                key={q}
                onClick={() => {
                  setQuery(q);
                  void searchPermits(undefined, q);
                }}
                className="px-4 py-2 rounded-full border border-slate-300 text-sm text-slate-700 hover:bg-navy-50 hover:border-navy-300 hover:text-navy-700 transition-all duration-200"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <Card className="overflow-hidden">
          <div className="bg-navy-50 border-b border-slate-200 px-6 py-4">
            <h3 className="text-lg font-semibold text-navy-800 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Search Results ({results.length})
            </h3>
          </div>
          
          <div className="divide-y divide-slate-200">
            {results.map((permit) => (
              <div key={permit.id} className="p-6 hover:bg-slate-50 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-start gap-3">
                      <MapPin className="w-5 h-5 text-navy-600 mt-0.5" />
                      <div>
                        <h4 className="font-semibold text-gray-900">{permit.address}</h4>
                        {permit.county && (
                          <p className="text-sm text-slate-600 mt-1">{permit.county} County</p>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <Hash className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-600">ID: <span className="font-medium text-gray-900">{permit.id}</span></span>
                      </div>
                      
                      {permit.submitted_at && (
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-slate-400" />
                          <span className="text-slate-600">
                            {new Date(permit.submitted_at).toLocaleDateString()}
                          </span>
                        </div>
                      )}

                      {permit.value && (
                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4 text-slate-400" />
                          <span className="font-medium text-gray-900">
                            ${permit.value.toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge variant="texas" size="sm">{permit.trade}</Badge>
                    <Badge 
                      variant={permit.status === 'Submitted' ? 'warning' : 'default'}
                      size="sm"
                    >
                      {permit.status}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Empty State */}
      {results.length === 0 && !loading && (
        <Card className="p-12 text-center">
          <FileText className="w-16 h-16 mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results yet</h3>
          <p className="text-slate-600">Start by searching for a permit using the search box above</p>
        </Card>
      )}
    </div>
  );
}
