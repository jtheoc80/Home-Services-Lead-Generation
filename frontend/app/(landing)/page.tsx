"use client";

import { useState, useEffect } from "react";
import Card from "@/components/ui/Card";
import StatCard from "@/components/ui/StatCard";
import Badge from "@/components/ui/Badge";
import { 
  MapPin, 
  TrendingUp, 
  Target, 
  Users, 
  Building, 
  Zap, 
  Shield, 
  BarChart3,
  ArrowRight,
  Star,
  CheckCircle
} from "lucide-react";

interface Stats {
  activeCounties: number;
  totalLeads: number;
  qualifiedLeads: number;
  successRate: number;
  countyBreakdown: Record<string, number>;
}

const features = [
  {
    icon: <MapPin className="w-6 h-6" />,
    title: "Texas Statewide Coverage",
    description: "Harris, Fort Bend, Brazoria, and Galveston counties with plans for Austin, San Antonio, and Dallas"
  },
  {
    icon: <Target className="w-6 h-6" />,
    title: "AI-Powered Lead Scoring",
    description: "ML-driven algorithm weighing recency, project value, residential signals, and trade specificity"
  },
  {
    icon: <Zap className="w-6 h-6" />,
    title: "Real-Time Updates",
    description: "Nightly automated scraping with GitHub Actions-powered data collection at 6 AM UTC"
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    title: "Advanced Analytics",
    description: "Track conversion rates, ROI by lead source, and performance metrics across trade types"
  },
  {
    icon: <Shield className="w-6 h-6" />,
    title: "Secure & Compliant",
    description: "Supabase-powered JWT authentication with role-based access and enterprise security"
  },
  {
    icon: <Users className="w-6 h-6" />,
    title: "Trade-Specific Filtering",
    description: "HVAC, Roofing, Electrical, Plumbing, and more with intelligent categorization"
  }
];

const texasCounties = [
  { name: "Houston", county: "Harris", population: "4.7M" },
  { name: "Harris County", county: "Harris", population: "4.7M" },
  { name: "Dallas", county: "Dallas", population: "7.6M" },
  { name: "Austin", county: "Travis", population: "2.3M" }
];

export default function HomePage() {
  const [selectedCounty, setSelectedCounty] = useState<string>('');
  const [stats, setStats] = useState<Stats>({
    activeCounties: 0,
    totalLeads: 0,
    qualifiedLeads: 0,
    successRate: 0,
    countyBreakdown: {}
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/stats')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch stats');
        return res.json();
      })
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch stats:', err);
        setLoading(false);
      });
  }, []);

  const displayStats = [
    { 
      label: "Active Counties", 
      value: loading ? "..." : String(stats.activeCounties), 
      icon: <MapPin className="w-6 h-6" />, 
      variant: "texas" as const 
    },
    { 
      label: "Total Leads", 
      value: loading ? "..." : stats.totalLeads.toLocaleString(), 
      icon: <Building className="w-6 h-6" />, 
      variant: "default" as const 
    },
    { 
      label: "Qualified Leads", 
      value: loading ? "..." : stats.qualifiedLeads.toLocaleString(), 
      icon: <Target className="w-6 h-6" />, 
      variant: "success" as const 
    },
    { 
      label: "Success Rate", 
      value: loading ? "..." : `${stats.successRate}%`, 
      icon: <TrendingUp className="w-6 h-6" />, 
      variant: "warning" as const 
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section - Split Layout */}
      <section className="relative overflow-hidden bg-gradient-to-br from-navy-800 via-navy-900 to-slate-900">
        <div className="absolute inset-0 bg-gradient-to-br from-navy-800/95 to-slate-900/95"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
        }}></div>
        
        <div className="relative mx-auto max-w-7xl px-6 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Hero Content */}
            <div className="space-y-8">
              <Badge variant="score" size="lg" className="bg-navy-600/30 text-navy-100 border-navy-500">
                <Star className="w-4 h-4 mr-2" />
                Texas #1 Lead Generation Platform
              </Badge>
              
              <h1 className="text-5xl lg:text-6xl font-bold text-white">
                Intelligent Home Services Lead Generation
              </h1>
              
              <p className="text-xl text-slate-300 leading-relaxed">
                Automatically scrape and enrich public building permit data across Texas. 
                Get exclusive leads with intelligent scoring before your competition even knows they exist.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <button 
                  onClick={() => (location.href = "/dashboard")}
                  className="inline-flex items-center justify-center px-8 py-4 bg-navy-600 text-white font-semibold rounded-lg hover:bg-navy-500 transition-all duration-300 shadow-lg group"
                >
                  View Dashboard
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </button>
                
                <button 
                  onClick={() => (location.href = "/leads")}
                  className="inline-flex items-center justify-center px-8 py-4 bg-transparent border-2 border-slate-400 text-slate-200 font-semibold rounded-lg hover:bg-slate-800 hover:border-slate-300 transition-all duration-300"
                >
                  Browse Leads
                </button>
              </div>
            </div>

            {/* Right: Live Stats Card */}
            <div className="lg:block">
              <Card variant="glass" className="p-8 backdrop-blur-xl bg-slate-800/40 border-slate-700/50">
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-white mb-2">Live Platform Stats</h3>
                  <p className="text-slate-300">Real-time data from Texas</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  {displayStats.map((stat, index) => (
                    <div key={index} className="bg-slate-700/30 backdrop-blur-sm rounded-lg p-4 text-center border border-slate-600/30">
                      <div className="text-slate-400 mb-2">{stat.icon}</div>
                      <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                      <div className="text-sm text-slate-300">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Texas Counties Section - Horizontal Scroll on Mobile */}
      <section className="py-16 bg-gray-50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Statewide Texas Coverage
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl">
              Currently covering major Texas metropolitan areas with expansion planned for Austin, San Antonio, and Dallas
            </p>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {texasCounties.map((county, index) => {
              const permits = stats.countyBreakdown[county.county] || 0;
              return (
                <div
                  key={index}
                  onClick={() => setSelectedCounty(county.name.toLowerCase().replace(' county', ''))}
                  className="cursor-pointer"
                >
                  <Card 
                    variant="glass" 
                    hover 
                    className="p-6 text-center group h-full"
                  >
                    <div className="space-y-4">
                      <div className="w-16 h-16 mx-auto bg-navy-100 rounded-2xl flex items-center justify-center group-hover:bg-navy-200 transition-colors">
                        <MapPin className="w-8 h-8 text-navy-600" />
                      </div>
                      
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-2">{county.name}</h3>
                        <p className="text-sm text-gray-600 mb-3">Pop: {county.population}</p>
                        
                        <Badge variant="default" size="sm" className="bg-navy-100 text-navy-700">
                          {loading ? '...' : permits.toLocaleString()} leads
                        </Badge>
                      </div>
                    </div>
                  </Card>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section - 2-Column Asymmetric Layout */}
      <section className="py-16 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Advanced Lead Generation Features
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl">
              Everything you need to identify, score, and convert high-quality home service leads
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Large Featured Card */}
            <div className="lg:row-span-2">
              <Card hover className="p-8 h-full bg-gradient-to-br from-navy-50 to-slate-100 group">
                <div className="space-y-6 h-full flex flex-col">
                  <div className="w-16 h-16 bg-navy-200 rounded-2xl flex items-center justify-center group-hover:bg-navy-300 transition-colors">
                    <div className="text-navy-700">
                      {features[0].icon}
                    </div>
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-gray-900 mb-4">
                      {features[0].title}
                    </h3>
                    <p className="text-gray-600 text-lg leading-relaxed">
                      {features[0].description}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-slate-200">
                    <div className="flex items-center text-navy-700 font-semibold group-hover:gap-2 transition-all">
                      <span>Learn more</span>
                      <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Regular Feature Cards */}
            {features.slice(1).map((feature, index) => (
              <Card key={index} hover className="p-6 group">
                <div className="space-y-4">
                  <div className="w-12 h-12 bg-navy-100 rounded-xl flex items-center justify-center group-hover:bg-navy-200 transition-colors">
                    <div className="text-navy-600">
                      {feature.icon}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-navy-800 to-navy-900">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <div className="space-y-8">
            <h2 className="text-4xl lg:text-5xl font-bold text-white">
              Ready to Transform Your Lead Generation?
            </h2>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
              Join contractors across Texas who are already using our platform to identify 
              high-value opportunities before their competition.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button 
                onClick={() => (location.href = "/dashboard")}
                className="inline-flex items-center justify-center px-8 py-4 bg-navy-600 text-white font-semibold rounded-lg hover:bg-navy-500 transition-all duration-300 shadow-lg"
              >
                <CheckCircle className="w-5 h-5 mr-2" />
                Get Started Now
              </button>
              
              <button 
                onClick={() => (location.href = "/leads-test")}
                className="inline-flex items-center justify-center px-8 py-4 bg-transparent border-2 border-slate-400 text-slate-200 font-semibold rounded-lg hover:bg-slate-800 hover:border-slate-300 transition-all duration-300"
              >
                Try Demo
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
