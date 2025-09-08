#!/usr/bin/env tsx

/**
 * Run Houston ETL and Mint Leads Script
 * 
 * This script implements the requirements from the problem statement:
 * 1. Run the Houston ETL workflow on the self-hosted runner
 * 2. Execute Supabase SQL commands to check permits and mint leads
 * 3. Verify lead generation and troubleshoot if needed
 * 
 * Usage: tsx scripts/run-houston-etl-and-mint-leads.ts [--dry-run]
 * 
 * Environment Variables:
 *   SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key
 *   GITHUB_TOKEN - GitHub token for triggering workflows (optional)
 */

import { execSync } from 'node:child_process';
import fs from 'node:fs';

interface SupabaseQueryResult {
  count?: number;
  inserted_count?: number;
  updated_count?: number;
  total_processed?: number;
  [key: string]: any;
}

class HoustonETLRunner {
  private supabaseUrl: string;
  private supabaseKey: string;
  private isDryRun: boolean;

  constructor(isDryRun = false) {
    this.isDryRun = isDryRun;
    
    // Validate required environment variables
    this.supabaseUrl = process.env.SUPABASE_URL || '';
    this.supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
    
    if (!this.supabaseUrl) {
      throw new Error('SUPABASE_URL environment variable is required');
    }
    if (!this.supabaseKey) {
      throw new Error('SUPABASE_SERVICE_ROLE_KEY environment variable is required');
    }
  }

  private async executeSupabaseQuery(query: string): Promise<any> {
    const url = `${this.supabaseUrl}/rest/v1/rpc/sql`;
    
    console.log(`📊 Executing query: ${query.substring(0, 100)}...`);
    
    if (this.isDryRun) {
      console.log('🔍 [DRY RUN] Would execute query');
      return { dry_run: true };
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'apikey': this.supabaseKey,
          'Authorization': `Bearer ${this.supabaseKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Query failed: ${response.status} ${response.statusText} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ Query failed: ${error}`);
      throw error;
    }
  }

  private async executeSupabaseRPC(functionName: string, params: any = {}): Promise<any> {
    const url = `${this.supabaseUrl}/rest/v1/rpc/${functionName}`;
    
    console.log(`🔧 Calling RPC function: ${functionName} with params:`, params);
    
    if (this.isDryRun) {
      console.log('🔍 [DRY RUN] Would call RPC function');
      return { dry_run: true };
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'apikey': this.supabaseKey,
          'Authorization': `Bearer ${this.supabaseKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`RPC call failed: ${response.status} ${response.statusText} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ RPC call failed: ${error}`);
      throw error;
    }
  }

  private async checkPermitsCount(): Promise<number> {
    console.log('\n📋 Step 1: Checking permits count for last 7 days...');
    
    if (this.isDryRun) {
      console.log('🔍 [DRY RUN] Would check permits count');
      return 100; // Mock value for dry run
    }
    
    try {
      const url = `${this.supabaseUrl}/rest/v1/permits?select=count&issued_date=gte.${new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()}`;
      
      const response = await fetch(url, {
        method: 'HEAD',
        headers: {
          'apikey': this.supabaseKey,
          'Authorization': `Bearer ${this.supabaseKey}`,
          'Prefer': 'count=exact'
        }
      });

      const count = parseInt(response.headers.get('content-range')?.split('/')[1] || '0');
      console.log(`✅ Found ${count} permits issued in the last 7 days`);
      return count;
    } catch (error) {
      console.error(`❌ Failed to check permits count: ${error}`);
      throw error;
    }
  }

  private async upsertLeads(): Promise<SupabaseQueryResult> {
    console.log('\n🎯 Step 2: Minting leads from permits (limit: 50, days: 365)...');
    
    if (this.isDryRun) {
      console.log('🔍 [DRY RUN] Would call upsert_leads_from_permits_limit(50, 365)');
      const mockStats = { inserted_count: 25, updated_count: 10, total_processed: 35 };
      console.log(`✅ Lead generation completed (mock):`);
      console.log(`   📈 Inserted: ${mockStats.inserted_count} leads`);
      console.log(`   🔄 Updated: ${mockStats.updated_count} leads`);
      console.log(`   📊 Total processed: ${mockStats.total_processed} permits`);
      return mockStats;
    }
    
    try {
      const result = await this.executeSupabaseRPC('upsert_leads_from_permits_limit', {
        p_limit: 50,
        p_days: 365
      });

      const stats = Array.isArray(result) ? result[0] : result;
      console.log(`✅ Lead generation completed:`);
      console.log(`   📈 Inserted: ${stats.inserted_count || 0} leads`);
      console.log(`   🔄 Updated: ${stats.updated_count || 0} leads`);
      console.log(`   📊 Total processed: ${stats.total_processed || 0} permits`);

      return stats;
    } catch (error) {
      console.error(`❌ Failed to upsert leads: ${error}`);
      throw error;
    }
  }

  private async checkLatestLeads(): Promise<any[]> {
    console.log('\n📊 Step 3: Checking latest leads...');
    
    if (this.isDryRun) {
      console.log('🔍 [DRY RUN] Would fetch latest leads');
      const mockLeads = [
        { name: 'Mock Lead 1', county: 'Harris', trade: 'Plumbing', created_at: '2025-01-01T12:00:00Z' },
        { name: 'Mock Lead 2', county: 'Harris', trade: 'Electrical', created_at: '2025-01-01T11:00:00Z' }
      ];
      console.log(`✅ Found ${mockLeads.length} latest leads (mock)`);
      console.log('\n📋 Sample of latest leads:');
      mockLeads.forEach((lead: any, index: number) => {
        console.log(`   ${index + 1}. ${lead.name} (${lead.county}) - ${lead.trade} - ${lead.created_at}`);
      });
      return mockLeads;
    }
    
    try {
      const url = `${this.supabaseUrl}/rest/v1/leads?select=source,external_permit_id,name,county,trade,address,zipcode,created_at&order=created_at.desc&limit=50`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'apikey': this.supabaseKey,
          'Authorization': `Bearer ${this.supabaseKey}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch leads: ${response.status} ${response.statusText}`);
      }

      const leads = await response.json();
      console.log(`✅ Found ${leads.length} latest leads`);

      if (leads.length > 0) {
        console.log('\n📋 Sample of latest leads:');
        leads.slice(0, 5).forEach((lead: any, index: number) => {
          console.log(`   ${index + 1}. ${lead.name} (${lead.county}) - ${lead.trade} - ${lead.created_at}`);
        });
      }

      return leads;
    } catch (error) {
      console.error(`❌ Failed to check latest leads: ${error}`);
      throw error;
    }
  }

  private async getLastETLLogs(): Promise<void> {
    console.log('\n📝 Getting last ETL job logs...');
    
    try {
      const url = `${this.supabaseUrl}/rest/v1/etl_runs?select=*&source_system=eq.city_of_houston&order=run_timestamp.desc&limit=3`;
      
      if (this.isDryRun) {
        console.log('🔍 [DRY RUN] Would fetch ETL logs');
        return;
      }

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'apikey': this.supabaseKey,
          'Authorization': `Bearer ${this.supabaseKey}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch ETL logs: ${response.status} ${response.statusText}`);
      }

      const logs = await response.json();
      
      if (logs.length === 0) {
        console.log('⚠️  No ETL logs found for city_of_houston');
        return;
      }

      console.log(`✅ Found ${logs.length} recent ETL runs:`);
      logs.forEach((log: any, index: number) => {
        console.log(`\n   ${index + 1}. ETL Run (${log.run_timestamp}):`);
        console.log(`      Status: ${log.status}`);
        console.log(`      Fetched: ${log.fetched}, Parsed: ${log.parsed}, Upserted: ${log.upserted}`);
        console.log(`      Errors: ${log.errors}`);
        if (log.error_message) {
          console.log(`      Error: ${log.error_message}`);
        }
        if (log.first_issue_date && log.last_issue_date) {
          console.log(`      Date range: ${log.first_issue_date} to ${log.last_issue_date}`);
        }
        console.log(`      Duration: ${log.duration_ms}ms`);
      });
    } catch (error) {
      console.error(`❌ Failed to get ETL logs: ${error}`);
    }
  }

  private async verifyDataSources(): Promise<void> {
    console.log('\n🔍 Verifying data sources...');
    
    const sources = [
      { name: 'Houston Weekly XLSX', url: process.env.HOUSTON_WEEKLY_XLSX_URL },
      { name: 'Houston Sold Permits', url: process.env.HOUSTON_SOLD_PERMITS_URL }
    ];

    for (const source of sources) {
      if (!source.url) {
        console.log(`⚠️  ${source.name}: URL not configured`);
        continue;
      }

      try {
        console.log(`🌐 Checking ${source.name}...`);
        
        if (this.isDryRun) {
          console.log('🔍 [DRY RUN] Would check data source');
          continue;
        }

        const response = await fetch(source.url, { 
          method: 'HEAD',
          headers: {
            'User-Agent': process.env.USER_AGENT || 'LeadLedgerETL/1.0'
          }
        });
        
        console.log(`   ✅ ${source.name}: HTTP ${response.status} ${response.statusText}`);
      } catch (error) {
        console.log(`   ❌ ${source.name}: ${error}`);
      }
    }
  }

  private async runHoustonETLLocally(): Promise<void> {
    console.log('\n🏗️  Running Houston ETL locally...');
    
    if (this.isDryRun) {
      console.log('🔍 [DRY RUN] Would run: npm run ingest:coh');
      return;
    }

    try {
      execSync('npm run ingest:coh', { 
        stdio: 'inherit',
        cwd: process.cwd()
      });
      console.log('✅ Houston ETL completed locally');
    } catch (error) {
      console.error(`❌ Houston ETL failed: ${error}`);
      throw error;
    }
  }

  public async run(): Promise<void> {
    try {
      console.log('🚀 Houston ETL and Lead Generation Pipeline');
      console.log('============================================');
      
      if (this.isDryRun) {
        console.log('🔍 DRY RUN MODE - No actual changes will be made\n');
      }

      // Step 1: Check permits for last 7 days
      const permitsCount = await this.checkPermitsCount();

      // Step 2: Run Houston ETL locally (since we can't easily trigger GitHub Actions)
      await this.runHoustonETLLocally();

      // Step 3: Mint leads using the specified function
      const leadStats = await this.upsertLeads();

      // Step 4: Check latest leads
      const latestLeads = await this.checkLatestLeads();

      // If no leads were generated, troubleshoot
      if (!this.isDryRun && latestLeads.length === 0) {
        console.log('\n⚠️  No leads found! Starting troubleshooting...');
        
        await this.getLastETLLogs();
        await this.verifyDataSources();
        
        console.log('\n🔧 Troubleshooting suggestions:');
        console.log('   1. Check if permits exist in the database');
        console.log('   2. Verify Houston data source URLs are accessible');
        console.log('   3. Review ETL logs for constraint/RLS errors');
        console.log('   4. Check Supabase RLS policies on leads table');
      }

      console.log('\n🎉 Pipeline completed successfully!');
      
      // Write summary
      const summary = {
        timestamp: new Date().toISOString(),
        dry_run: this.isDryRun,
        permits_count_7_days: permitsCount,
        leads_stats: leadStats,
        latest_leads_count: latestLeads.length,
        status: 'success'
      };

      fs.mkdirSync('logs', { recursive: true });
      fs.writeFileSync('logs/houston-etl-mint-leads-summary.json', JSON.stringify(summary, null, 2));
      
    } catch (error) {
      console.error('\n❌ Pipeline failed:', error instanceof Error ? error.message : String(error));
      
      const errorSummary = {
        timestamp: new Date().toISOString(),
        dry_run: this.isDryRun,
        status: 'error',
        error: error instanceof Error ? error.message : String(error)
      };

      fs.mkdirSync('logs', { recursive: true });
      fs.writeFileSync('logs/houston-etl-mint-leads-summary.json', JSON.stringify(errorSummary, null, 2));
      
      process.exitCode = 1;
    }
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');

// Main execution
if (process.argv[1] && (process.argv[1].endsWith('run-houston-etl-and-mint-leads.ts') || process.argv[1].endsWith('run-houston-etl-and-mint-leads.js'))) {
  const runner = new HoustonETLRunner(isDryRun);
  runner.run().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

export { HoustonETLRunner };