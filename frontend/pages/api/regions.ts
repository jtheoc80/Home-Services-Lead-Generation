import { NextApiRequest, NextApiResponse } from 'next';
import yaml from 'js-yaml';
import fs from 'fs';
import path from 'path';

interface RegionConfig {
  regions: Record<string, any>;
  default_region: string;
  default_metro: string;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    return handleGetRegions(req, res);
  } else {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleGetRegions(req: NextApiRequest, res: NextApiResponse) {
  try {
    // Load regions configuration
    const configPath = path.join(process.cwd(), '..', 'config', 'regions.yaml');
    
    if (!fs.existsSync(configPath)) {
      return res.status(500).json({ error: 'Regions configuration file not found' });
    }

    const configFile = fs.readFileSync(configPath, 'utf8');
    const config: RegionConfig = yaml.load(configFile) as RegionConfig;

    // Filter to only active regions and metros
    const activeRegions: Record<string, any> = {};
    
    for (const [regionId, regionData] of Object.entries(config.regions)) {
      const region = regionData as any;
      if (region.active) {
        const activeMetros: Record<string, any> = {};
        
        for (const [metroId, metroData] of Object.entries(region.metros || {})) {
          const metro = metroData as any;
          if (metro.active) {
            activeMetros[metroId] = {
              display_name: metro.display_name,
              short_name: metro.short_name,
              center_lat: metro.center_lat,
              center_lng: metro.center_lng,
              radius_miles: metro.radius_miles,
              description: metro.description,
              jurisdictions: metro.jurisdictions || []
            };
          }
        }
        
        if (Object.keys(activeMetros).length > 0) {
          activeRegions[regionId] = {
            display_name: region.display_name,
            short_name: region.short_name,
            timezone: region.timezone,
            metros: activeMetros
          };
        }
      }
    }

    // Return regions data
    const response = {
      regions: activeRegions,
      default_region: config.default_region,
      default_metro: config.default_metro,
      available_metros: Object.values(activeRegions).flatMap((region: any) =>
        Object.entries(region.metros).map(([metroId, metroData]: [string, any]) => ({
          id: metroId,
          region_id: Object.keys(activeRegions).find(rid => activeRegions[rid] === region),
          display_name: metroData.display_name,
          short_name: metroData.short_name,
          center_lat: metroData.center_lat,
          center_lng: metroData.center_lng,
          radius_miles: metroData.radius_miles,
          description: metroData.description
        }))
      )
    };

    res.status(200).json(response);
  } catch (error) {
    console.error('Get regions error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}