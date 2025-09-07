#!/usr/bin/env tsx

/**
 * probeSources.ts - Source Health Monitoring Script
 * 
 * Probes various Texas data sources to monitor their health and availability.
 * Records health metrics in the source_health table for monitoring dashboards.
 */

import axios from "axios";
import { createClient } from '@supabase/supabase-js';

interface SourceHealthRecord {
  source_key: string;
  status: 'online' | 'offline' | 'limited';
  last_check: string;
  response_time_ms: number | null;
  error_message: string | null;
  records_available: number | null;
  metadata?: Record<string, any>;
}

interface DataSource {
  key: string;
  name: string;
  type: 'socrata' | 'csv' | 'arcgis' | 'api';
  url: string;
  headers?: Record<string, string>;
  timeout?: number;
}

class SourceHealthProbe {
  private supabase: any;
  private results: SourceHealthRecord[] = [];

  constructor() {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    
    if (!supabaseUrl || !supabaseKey) {
      throw new Error('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required');
    }
    
    this.supabase = createClient(supabaseUrl, supabaseKey);
  }

  /**
   * Define data sources to probe based on TX coverage documentation
   */
  private getDataSources(): DataSource[] {
    const sources: DataSource[] = [
      // Austin Socrata API
      {
        key: 'austin_socrata',
        name: 'City of Austin Permits',
        type: 'socrata',
        url: 'https://data.austintexas.gov/resource/3syk-w9eu.json',
        headers: {
          'X-App-Token': process.env.AUSTIN_SOCRATA_APP_TOKEN || ''
        },
        timeout: 15000
      },
      
      // San Antonio Socrata API  
      {
        key: 'sa_socrata',
        name: 'City of San Antonio Permits',
        type: 'socrata',
        url: 'https://data.sanantonio.gov/resource/5kh3-dhrv.json',
        headers: {
          'X-App-Token': process.env.SA_SOCRATA_APP_TOKEN || ''
        },
        timeout: 15000
      },
      
      // Dallas Socrata API
      {
        key: 'dallas_socrata',
        name: 'City of Dallas Permits',
        type: 'socrata',
        url: 'https://www.dallasopendata.com/resource/e7gq-4sah.json',
        timeout: 15000
      },
      
      // Houston CSV endpoint
      {
        key: 'houston_csv',
        name: 'City of Houston Permits CSV',
        type: 'csv',
        url: 'https://www.houstontx.gov/planning/DevelopReview/permits_issued.csv',
        timeout: 30000
      },
      
      // Harris County (placeholder - would need actual ArcGIS endpoint)
      {
        key: 'harris_county',
        name: 'Harris County ArcGIS',
        type: 'arcgis',
        url: 'https://services.arcgis.com/dummy/arcgis/rest/services/permits/FeatureServer/0/query',
        timeout: 20000
      }
    ];

    return sources;
  }

  /**
   * Probe a single data source
   */
  private async probeSource(source: DataSource): Promise<SourceHealthRecord> {
    const startTime = Date.now();
    const record: SourceHealthRecord = {
      source_key: source.key,
      status: 'offline',
      last_check: new Date().toISOString(),
      response_time_ms: null,
      error_message: null,
      records_available: null,
      metadata: {
        source_name: source.name,
        source_type: source.type,
        url: source.url
      }
    };

    try {
      console.log(`🔍 Probing ${source.name} (${source.key})...`);
      
      // Configure request options
      const requestConfig: any = {
        method: 'GET',
        url: source.url,
        timeout: source.timeout || 15000,
        headers: {
          'User-Agent': 'LeadLedgerPro-SourceHealthMonitor/1.0',
          ...source.headers
        }
      };

      // For Socrata APIs, add limit parameter to get just a small sample
      if (source.type === 'socrata') {
        requestConfig.params = { '$limit': 10 };
      }

      // For ArcGIS endpoints, add basic query parameters
      if (source.type === 'arcgis') {
        requestConfig.params = {
          'where': '1=1',
          'returnCountOnly': 'true',
          'f': 'json'
        };
      }

      const response = await axios(requestConfig);
      const responseTime = Date.now() - startTime;
      
      record.response_time_ms = responseTime;
      
      // Check response status
      if (response.status >= 200 && response.status < 300) {
        record.status = 'online';
        
        // Try to determine record count based on source type
        if (source.type === 'socrata' && Array.isArray(response.data)) {
          record.records_available = response.data.length;
          record.metadata!.sample_record_count = response.data.length;
        } else if (source.type === 'csv' && typeof response.data === 'string') {
          // Count lines in CSV (approximate)
          const lines = response.data.split('\n').length - 1; // Subtract header
          record.records_available = Math.max(0, lines);
          record.metadata!.csv_size_bytes = response.data.length;
        } else if (source.type === 'arcgis' && response.data?.count !== undefined) {
          record.records_available = response.data.count;
        }
        
        console.log(`  ✅ ${source.name}: ${responseTime}ms, ${record.records_available || 'unknown'} records`);
      } else {
        record.status = 'limited';
        record.error_message = `HTTP ${response.status}: ${response.statusText}`;
        console.log(`  ⚠️  ${source.name}: HTTP ${response.status}`);
      }
      
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      record.response_time_ms = responseTime;
      record.status = 'offline';
      
      if (error.code === 'ECONNREFUSED') {
        record.error_message = 'Connection refused';
      } else if (error.code === 'ETIMEDOUT') {
        record.error_message = 'Request timeout';
      } else if (error.response) {
        record.error_message = `HTTP ${error.response.status}: ${error.response.statusText}`;
      } else {
        record.error_message = error.message || 'Unknown error';
      }
      
      console.log(`  ❌ ${source.name}: ${record.error_message}`);
    }

    return record;
  }

  /**
   * Probe all data sources
   */
  private async probeAllSources(): Promise<void> {
    const sources = this.getDataSources();
    console.log(`🚀 Starting health probe for ${sources.length} data sources...\n`);

    // Probe sources in parallel for better performance
    const probePromises = sources.map(source => this.probeSource(source));
    this.results = await Promise.all(probePromises);

    console.log(`\n📊 Probe complete. Results:`);
    const online = this.results.filter(r => r.status === 'online').length;
    const limited = this.results.filter(r => r.status === 'limited').length;
    const offline = this.results.filter(r => r.status === 'offline').length;
    
    console.log(`  ✅ Online: ${online}`);
    console.log(`  ⚠️  Limited: ${limited}`);
    console.log(`  ❌ Offline: ${offline}`);
  }

  /**
   * Store results in Supabase
   */
  private async storeResults(): Promise<void> {
    try {
      console.log(`\n💾 Storing ${this.results.length} health records...`);
      
      // Try to insert directly first (table should exist)
      const { error } = await this.supabase
        .from('source_health')
        .insert(this.results);

      if (error) {
        if (error.message?.includes('does not exist') || error.code === '42P01') {
          console.log(`⚠️  source_health table doesn't exist. Please run the setup SQL first.`);
          console.log(`   Run: psql "$SUPABASE_URL" < sql/source_health_setup.sql`);
        }
        throw error;
      }

      console.log(`✅ Successfully stored health records`);
      
    } catch (error: any) {
      console.error(`❌ Failed to store health records:`, error.message);
      throw error;
    }
  }



  /**
   * Run the complete health probe process
   */
  async run(): Promise<void> {
    try {
      await this.probeAllSources();
      await this.storeResults();
      
      console.log(`\n🎉 Source health probe completed successfully!`);
      
      // Output summary for GitHub Actions
      const online = this.results.filter(r => r.status === 'online').length;
      const total = this.results.length;
      console.log(`\nSUMMARY: ${online}/${total} sources online`);
      
      // Exit with 0 on success
      process.exit(0);
      
    } catch (error: any) {
      console.error(`\n💥 Source health probe failed:`, error.message);
      
      // Exit with 1 on failure (but let GitHub Action continue)
      console.log('\nNote: GitHub Action will continue to show health summary from database');
      process.exit(1);
    }
  }
}

// Execute if run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const probe = new SourceHealthProbe();
  probe.run().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default SourceHealthProbe;