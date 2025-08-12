#!/usr/bin/env tsx

/**
 * Database Wiring Tool for Supabase
 * 
 * Sets up the required database schema for the Home Services Lead Generation platform.
 * Executes DDL statements idempotently against Supabase using the postgres connection string.
 * 
 * Usage: npm run db:wire
 * 
 * Environment Variables:
 * - SUPABASE_DB_URL (required): Postgres connection string from Supabase
 * - LEADS_TEST_MODE (optional): Set to "true" to create temporary RLS policies for testing
 */

import { Client } from 'pg';

interface DbWireResult {
  created: string[];
  exists: string[];
  errors: string[];
}

/**
 * Validates required environment variables
 */
function validateEnvironment(): { supabaseDbUrl: string; leadsTestMode: boolean } {
  const supabaseDbUrl = process.env.SUPABASE_DB_URL;
  if (!supabaseDbUrl) {
    console.error('❌ Error: SUPABASE_DB_URL environment variable is required');
    process.exit(1);
  }

  const leadsTestMode = process.env.LEADS_TEST_MODE === 'true';
  
  console.log('🔍 Environment validation:');
  console.log(`   SUPABASE_DB_URL: ${supabaseDbUrl ? '✓ Set' : '✗ Missing'}`);
  console.log(`   LEADS_TEST_MODE: ${leadsTestMode ? '✓ Enabled' : '✗ Disabled'}`);
  
  return { supabaseDbUrl, leadsTestMode };
}

/**
 * Main DDL statements to execute
 */
const DDL_STATEMENTS = [
  {
    name: 'pgcrypto extension',
    sql: 'CREATE EXTENSION IF NOT EXISTS "pgcrypto";'
  },
  {
    name: 'leads table',
    sql: `CREATE TABLE IF NOT EXISTS public.leads (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      created_at timestamptz NOT NULL DEFAULT now(),
      name text,
      email text,
      phone text,
      source text,
      status text DEFAULT 'new',
      metadata jsonb
    );`
  },
  {
    name: 'leads RLS',
    sql: 'ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;'
  },
  {
    name: 'ingest_logs table',
    sql: `CREATE TABLE IF NOT EXISTS public.ingest_logs (
      id bigserial PRIMARY KEY,
      created_at timestamptz DEFAULT now(),
      trace_id uuid,
      stage text NOT NULL,
      ok boolean NOT NULL,
      details jsonb
    );`
  },
  {
    name: 'ingest_logs trace index',
    sql: 'CREATE INDEX IF NOT EXISTS idx_ingest_logs_trace ON public.ingest_logs(trace_id);'
  },
  {
    name: 'permits_raw_harris table',
    sql: `CREATE TABLE IF NOT EXISTS public.permits_raw_harris (
      event_id bigint PRIMARY KEY,
      permit_number text,
      permit_name text,
      app_type text,
      issue_date timestamptz,
      project_number text,
      full_address text,
      street_number numeric,
      street_name text,
      status text,
      raw jsonb,
      created_at timestamptz DEFAULT now()
    );`
  },
  {
    name: 'permits_raw_harris issue_date index',
    sql: 'CREATE INDEX IF NOT EXISTS idx_permits_harris_issue_date ON public.permits_raw_harris(issue_date DESC);'
  }
];

/**
 * Test mode RLS policies (only created when LEADS_TEST_MODE=true)
 */
const TEST_MODE_POLICIES = [
  {
    name: 'tmp_anon_insert policy',
    sql: `DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname='public' 
        AND tablename='leads' 
        AND policyname='tmp_anon_insert'
      ) THEN
        CREATE POLICY "tmp_anon_insert" ON public.leads 
        FOR INSERT TO anon WITH CHECK (true);
      END IF;
    END $$;`
  },
  {
    name: 'tmp_anon_select policy',
    sql: `DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname='public' 
        AND tablename='leads' 
        AND policyname='tmp_anon_select'
      ) THEN
        CREATE POLICY "tmp_anon_select" ON public.leads 
        FOR SELECT TO anon USING (true);
      END IF;
    END $$;`
  }
];

/**
 * Execute DDL statements in a transaction
 */
async function executeWiring(client: Client, leadsTestMode: boolean): Promise<DbWireResult> {
  const result: DbWireResult = {
    created: [],
    exists: [],
    errors: []
  };

  try {
    await client.query('BEGIN');
    
    // Execute main DDL statements
    for (const statement of DDL_STATEMENTS) {
      try {
        await client.query(statement.sql);
        result.created.push(statement.name);
      } catch (error: any) {
        if (error.message.includes('already exists')) {
          result.exists.push(statement.name);
        } else {
          result.errors.push(`${statement.name}: ${error.message}`);
        }
      }
    }

    // Execute test mode policies if enabled
    if (leadsTestMode) {
      for (const policy of TEST_MODE_POLICIES) {
        try {
          await client.query(policy.sql);
          result.created.push(policy.name);
        } catch (error: any) {
          result.errors.push(`${policy.name}: ${error.message}`);
        }
      }
    }

    if (result.errors.length > 0) {
      await client.query('ROLLBACK');
      return result;
    }

    await client.query('COMMIT');
    return result;
  } catch (error: any) {
    await client.query('ROLLBACK');
    result.errors.push(`Transaction error: ${error.message}`);
    return result;
  }
}

/**
 * Pretty-print the results summary
 */
function printSummary(result: DbWireResult, leadsTestMode: boolean): void {
  console.log('\n📊 Database Wiring Summary:');
  console.log('='.repeat(50));
  
  if (result.created.length > 0) {
    console.log('\n✅ Created:');
    result.created.forEach(item => console.log(`   • ${item}`));
  }
  
  if (result.exists.length > 0) {
    console.log('\n📋 Already exists:');
    result.exists.forEach(item => console.log(`   • ${item}`));
  }
  
  if (result.errors.length > 0) {
    console.log('\n❌ Errors:');
    result.errors.forEach(error => console.log(`   • ${error}`));
  }

  if (leadsTestMode) {
    console.log('\n🧪 Test Mode: Temporary RLS policies enabled for testing');
  }

  console.log('\n' + '='.repeat(50));
  
  const totalItems = result.created.length + result.exists.length;
  const hasErrors = result.errors.length > 0;
  
  if (hasErrors) {
    console.log(`❌ Failed: ${result.errors.length} errors occurred`);
  } else {
    console.log(`✅ Success: ${totalItems} database objects processed`);
  }
}

/**
 * Main function
 */
export async function main(): Promise<void> {
  console.log('🚀 Starting database wiring...\n');
  
  // Validate environment
  const { supabaseDbUrl, leadsTestMode } = validateEnvironment();
  
  // Create database client
  const client = new Client({
    connectionString: supabaseDbUrl,
    ssl: { rejectUnauthorized: false }
  });

  try {
    console.log('\n🔌 Connecting to database...');
    await client.connect();
    console.log('✅ Connected successfully');

    console.log('\n⚡ Executing DDL statements...');
    const result = await executeWiring(client, leadsTestMode);
    
    printSummary(result, leadsTestMode);
    
    if (result.errors.length > 0) {
      console.error('\n💥 Database wiring failed with errors');
      process.exit(1);
    }
    
    console.log('\n🎉 Database wiring completed successfully!');
    process.exit(0);
    
  } catch (error: any) {
    console.error('\n❌ Database connection failed:', error.message);
    process.exit(1);
  } finally {
    await client.end();
  }
}

// Run main function when script is executed directly
// In ES modules, we can check process.argv[1] to see if this file is being run directly
// Robust direct execution check for ES modules
const isDirectlyExecuted = (() => {
  // Only run if import.meta.url is available (ESM)
  if (typeof import.meta !== 'undefined' && import.meta.url) {
    const scriptPath = path.resolve(process.argv[1] || '');
    const modulePath = path.resolve(fileURLToPath(import.meta.url));
    return scriptPath === modulePath;
  }
  return false;
})();
if (isDirectlyExecuted) {
  main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}