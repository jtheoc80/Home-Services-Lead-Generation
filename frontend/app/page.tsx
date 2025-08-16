"use client";

import { useState } from "react";
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

const stats = [
  { label: "Active Counties", value: "4", icon: <MapPin className="w-6 h-6" />, variant: "texas" as const },
  { label: "Total Permits", value: "3,959", icon: <Building className="w-6 h-6" />, variant: "default" as const },
  { label: "Qualified Leads", value: "847", icon: <Target className="w-6 h-6" />, variant: "success" as const },
  { label: "Success Rate", value: "89%", icon: <TrendingUp className="w-6 h-6" />, variant: "warning" as const }
];

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
  { name: "Harris County", permits: 2847, population: "4.7M" },
  { name: "Fort Bend County", permits: 689, population: "822K" },
  { name: "Brazoria County", permits: 234, population: "372K" },
  { name: "Galveston County", permits: 189, population: "342K" }
];

export default function HomePage() {


  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-600 via-brand-700 to-texas-600">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-600/90 to-texas-600/90"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
        }}></div>
        
        <div className="relative mx-auto max-w-7xl px-6 py-24 text-center">
          <div className="space-y-8">
            <div className="space-y-4">
              <Badge variant="score" size="lg" className="animate-bounce-gentle">
                <Star className="w-4 h-4 mr-2" />
                Texas #1 Lead Generation Platform
              </Badge>
              
              <h1 className="text-6xl font-bold text-white">
                LeadLedgerPro
                <span className="block bg-gradient-to-r from-yellow-200 to-orange-200 bg-clip-text text-transparent">
                  Lead Generation
                </span>
              </h1>
              
              <p className="mx-auto max-w-3xl text-xl text-white/90 leading-relaxed">
                Automatically scrape and enrich public building permit data across Texas. 
                Get exclusive leads with intelligent scoring before your competition even knows they exist.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button 
                onClick={() => (location.href = "/dashboard")}
                className="inline-flex items-center px-8 py-4 bg-white text-brand-700 font-semibold rounded-2xl hover:bg-gray-100 transition-all duration-300 shadow-soft-xl group"
              >
                View Dashboard
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
              
              <button 
                onClick={() => (location.href = "/leads")}
                className="inline-flex items-center px-8 py-4 bg-transparent border-2 border-white text-white font-semibold rounded-2xl hover:bg-white hover:text-brand-700 transition-all duration-300"
              >
                Browse Leads
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Real Numbers from Real Data
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Live statistics from our automated permit scraping and lead scoring system across Texas
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <StatCard
                key={index}
                label={stat.label}
                value={stat.value}
                icon={stat.icon}
                variant={stat.variant}
                hover
              />
            ))}
          </div>
        </div>
      </section>

      {/* Texas Counties Section */}
      <section className="py-16 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Statewide Texas Coverage
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Currently covering major Texas metropolitan areas with expansion planned for Austin, San Antonio, and Dallas
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {texasCounties.map((county, index) => (
              <Card 
                key={index} 
                variant="glass" 
                hover 
                className="p-6 text-center group cursor-pointer"
                onClick={() => setSelectedCounty(county.name.toLowerCase().replace(' county', ''))}
              >
                <div className="space-y-4">
                  <div className="w-16 h-16 mx-auto bg-texas-100 rounded-2xl flex items-center justify-center group-hover:bg-texas-200 transition-colors">
                    <MapPin className="w-8 h-8 text-texas-600" />
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">{county.name}</h3>
                    <p className="text-sm text-gray-600 mb-3">Population: {county.population}</p>
                    
                    <Badge variant="texas" size="sm">
                      {county.permits.toLocaleString()} active permits
                    </Badge>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-gradient-to-b from-gray-50 to-white">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Advanced Lead Generation Features
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Everything you need to identify, score, and convert high-quality home service leads
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} hover className="p-6 group">
                <div className="space-y-4">
                  <div className="w-12 h-12 bg-brand-100 rounded-xl flex items-center justify-center group-hover:bg-brand-200 transition-colors">
                    <div className="text-brand-600">
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
      <section className="py-16 bg-gradient-to-r from-brand-600 to-texas-600">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <div className="space-y-6">
            <h2 className="text-4xl font-bold text-white">
              Ready to Transform Your Lead Generation?
            </h2>
            <p className="text-xl text-white/90 max-w-2xl mx-auto">
              Join contractors across Texas who are already using our platform to identify 
              high-value opportunities before their competition.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button 
                onClick={() => (location.href = "/dashboard")}
                className="inline-flex items-center px-8 py-4 bg-white text-brand-700 font-semibold rounded-2xl hover:bg-gray-100 transition-all duration-300 shadow-soft-xl"
              >
                <CheckCircle className="w-5 h-5 mr-2" />
                Get Started Now
              </button>
              
              <button 
                onClick={() => (location.href = "/leads-test")}
                className="inline-flex items-center px-8 py-4 bg-transparent border-2 border-white text-white font-semibold rounded-2xl hover:bg-white hover:text-brand-700 transition-all duration-300"
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