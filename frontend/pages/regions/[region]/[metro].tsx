import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { GetStaticPaths, GetStaticProps } from 'next';
import Footer from '@/components/Footer';
import RegionSelector from '@/components/RegionSelector';
import yaml from 'js-yaml';
import fs from 'fs';
import path from 'path';

interface Metro {
  id: string;
  region_id: string;
  display_name: string;
  short_name: string;
  center_lat: number;
  center_lng: number;
  radius_miles: number;
  description: string;
  seo_keywords: string[];
}

interface PageProps {
  metro: Metro;
  seoData: {
    title: string;
    description: string;
    keywords: string[];
  };
  leadStats?: {
    total_leads: number;
    recent_leads: number;
    top_trades: string[];
  };
}

export default function RegionPage({ metro, seoData, leadStats }: PageProps) {
  const router = useRouter();
  const [selectedRegion, setSelectedRegion] = useState(metro.region_id);
  const [selectedMetro, setSelectedMetro] = useState(metro.id);

  const handleRegionChange = (regionId: string, metroId: string) => {
    setSelectedRegion(regionId);
    setSelectedMetro(metroId);
    // Navigate to the new region page
    router.push(`/regions/${regionId}/${metroId}`);
  };

  return (
    <>
      <Head>
        <title>{seoData.title}</title>
        <meta name="description" content={seoData.description} />
        <meta name="keywords" content={seoData.keywords.join(', ')} />
        <meta property="og:title" content={seoData.title} />
        <meta property="og:description" content={seoData.description} />
        <meta property="og:type" content="website" />
        <link rel="canonical" href={`https://leadledgerpro.com/regions/${metro.region_id}/${metro.id}`} />
      </Head>
      
      <div className="min-h-screen bg-white flex flex-col">
        {/* Header */}
        <header className="bg-blue-600 text-white">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <Link href="/" className="text-2xl font-bold">LeadLedgerPro</Link>
              <nav className="space-x-4">
                <Link href="/signup" className="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100">
                  Sign Up
                </Link>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1">
          <div className="max-w-7xl mx-auto px-4 py-12">
            
            {/* Hero Section */}
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                {metro.display_name} Home Service Leads
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                {metro.description}
              </p>
              
              {/* Region Selector */}
              <div className="max-w-md mx-auto mb-8">
                <RegionSelector
                  selectedRegion={selectedRegion}
                  selectedMetro={selectedMetro}
                  onRegionChange={handleRegionChange}
                />
              </div>
              
              <div className="flex justify-center space-x-4">
                <Link 
                  href="/signup"
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-blue-700"
                >
                  Get {metro.short_name} Leads
                </Link>
              </div>
            </div>

            {/* Stats Section */}
            {leadStats && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                <div className="text-center bg-gray-50 rounded-lg p-6">
                  <div className="text-3xl font-bold text-blue-600 mb-2">
                    {leadStats.total_leads.toLocaleString()}
                  </div>
                  <div className="text-gray-600">Total Permits</div>
                </div>
                
                <div className="text-center bg-gray-50 rounded-lg p-6">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    {leadStats.recent_leads.toLocaleString()}
                  </div>
                  <div className="text-gray-600">This Month</div>
                </div>
                
                <div className="text-center bg-gray-50 rounded-lg p-6">
                  <div className="text-lg font-semibold text-purple-600 mb-2">
                    Top Trades
                  </div>
                  <div className="text-gray-600">
                    {leadStats.top_trades.join(', ')}
                  </div>
                </div>
              </div>
            )}

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">Local Data</h3>
                <p className="text-gray-600">
                  Building permits from {metro.display_name} municipalities and counties
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">Qualified Leads</h3>
                <p className="text-gray-600">
                  Pre-filtered residential permits with project details and values
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">Real-Time Updates</h3>
                <p className="text-gray-600">
                  Fresh {metro.short_name} leads delivered as permits are issued
                </p>
              </div>
            </div>

            {/* Coverage Area */}
            <div className="bg-gray-50 rounded-lg p-8 mb-12">
              <h2 className="text-2xl font-bold text-center mb-6">Coverage Area</h2>
              <div className="max-w-4xl mx-auto">
                <p className="text-center text-gray-600 mb-4">
                  Our {metro.display_name} coverage includes a {metro.radius_miles}-mile radius with these jurisdictions:
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {/* Note: In a real implementation, you'd get this from the metro data */}
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">Harris County</span>
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">City of Houston</span>
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">Montgomery County</span>
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">Fort Bend County</span>
                </div>
              </div>
            </div>

            {/* CTA Section */}
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Ready to Get {metro.short_name} Leads?
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Join contractors who are already growing their business with our {metro.display_name} permit data.
              </p>
              <Link 
                href="/signup"
                className="bg-blue-600 text-white px-8 py-4 rounded-lg text-xl font-medium hover:bg-blue-700 inline-block"
              >
                Start Free Trial
              </Link>
            </div>
          </div>
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  // Load regions configuration
  const configPath = path.join(process.cwd(), '..', 'config', 'regions.yaml');
  
  if (!fs.existsSync(configPath)) {
    return { paths: [], fallback: false };
  }

  const configFile = fs.readFileSync(configPath, 'utf8');
  const config = yaml.load(configFile) as any;

  // Generate paths for all active metros
  const paths: { params: { region: string; metro: string } }[] = [];
  
  for (const [regionId, regionData] of Object.entries(config.regions || {})) {
    if ((regionData as any).active) {
      for (const [metroId, metroData] of Object.entries((regionData as any).metros || {})) {
        if ((metroData as any).active) {
          paths.push({
            params: {
              region: regionId,
              metro: metroId
            }
          });
        }
      }
    }
  }

  return {
    paths,
    fallback: false
  };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const { region, metro } = params!;
  
  // Load regions configuration
  const configPath = path.join(process.cwd(), '..', 'config', 'regions.yaml');
  
  if (!fs.existsSync(configPath)) {
    return { notFound: true };
  }

  const configFile = fs.readFileSync(configPath, 'utf8');
  const config = yaml.load(configFile) as any;
  
  const regionData = config.regions?.[region as string];
  const metroData = regionData?.metros?.[metro as string];
  
  if (!regionData || !metroData || !regionData.active || !metroData.active) {
    return { notFound: true };
  }

  // Build metro object
  const metroObj: Metro = {
    id: metro as string,
    region_id: region as string,
    display_name: metroData.display_name,
    short_name: metroData.short_name,
    center_lat: metroData.center_lat,
    center_lng: metroData.center_lng,
    radius_miles: metroData.radius_miles,
    description: metroData.description,
    seo_keywords: metroData.seo_keywords || []
  };

  // Generate SEO data
  const seoConfig = config.seo_config || {};
  const seoData = {
    title: (seoConfig.title_template || '{metro} Home Services Leads | LeadLedgerPro')
      .replace('{metro}', metroData.display_name),
    description: (seoConfig.description_template || 'Quality home service contractor leads from building permits in {metro}.')
      .replace('{metro}', metroData.display_name),
    keywords: metroData.seo_keywords || []
  };

  // TODO: In a real implementation, you'd fetch lead stats from your database
  const leadStats = {
    total_leads: 1250,
    recent_leads: 89,
    top_trades: ['Roofing', 'Kitchen', 'HVAC']
  };

  return {
    props: {
      metro: metroObj,
      seoData,
      leadStats
    },
    revalidate: 3600 // Revalidate every hour
  };
};