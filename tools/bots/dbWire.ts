#!/usr/bin/env tsx

/**

 * DB Wire Bot
 * 
 * Database wiring bot that performs database connectivity and health checks.
 * Tests Supabase connection and validates critical database operations.
 */

import { createClient } from '@supabase/supabase-js';
import { program } from 'commander';

interface DatabaseHealth {
  connection: boolean;
  tablesAccessible: boolean;
  readOperations: boolean;
  writeOperations: boolean;
  errors: string[];
}

class DatabaseWireChecker {
  private supabase;
  private readonly testTables = ['leads', 'regions', 'jurisdictions', 'plans'];

  constructor() {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || process.env.SUPABASE_DB_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_KEY;

    if (!supabaseUrl || !serviceRoleKey) {
      throw new Error('Missing required environment variables: SUPABASE_URL/NEXT_PUBLIC_SUPABASE_URL/SUPABASE_DB_URL and SUPABASE_SERVICE_ROLE_KEY/SUPABASE_KEY');
    }

    this.supabase = createClient(supabaseUrl, serviceRoleKey);
    console.log(`🔌 Initialized DB Wire with URL: ${supabaseUrl.replace(/\/\/.*@/, '//***@')}`);
  }

  /**
   * Test basic database connection
   */
  async testConnection(): Promise<boolean> {
    console.log('🔍 Testing database connection...');
    
    try {
      // Simple connection test - try to execute a basic query
      const { data, error } = await this.supabase
        .from('pg_stat_database')
        .select('datname')
        .limit(1);

      if (error) {
        console.error('❌ Connection test failed:', error.message);
        return false;
      }

      console.log('✅ Database connection successful');
      return true;
    } catch (error) {
      console.error('❌ Connection test failed:', error);
      return false;
    }
  }

  /**
   * Test table accessibility
   */
  async testTableAccess(): Promise<{ success: boolean; errors: string[] }> {
    console.log('📋 Testing table accessibility...');
    
    const errors: string[] = [];
    let successCount = 0;

    for (const tableName of this.testTables) {
      try {
        const { error } = await this.supabase
          .from(tableName)
          .select('*')
          .limit(1);

        if (error) {
          const errorMsg = `Table ${tableName}: ${error.message}`;
          console.warn(`⚠️ ${errorMsg}`);
          errors.push(errorMsg);
        } else {
          console.log(`✅ Table ${tableName} is accessible`);
          successCount++;
        }
      } catch (error) {
        const errorMsg = `Table ${tableName}: ${error}`;
        console.error(`❌ ${errorMsg}`);
        errors.push(errorMsg);
      }
    }

    const success = successCount > 0; // Success if at least one table is accessible
    console.log(`📊 Table access test: ${successCount}/${this.testTables.length} tables accessible`);
    
    return { success, errors };
  }

  /**
   * Test read operations
   */
  async testReadOperations(): Promise<{ success: boolean; errors: string[] }> {
    console.log('📖 Testing read operations...');
    
    const errors: string[] = [];
    let successCount = 0;

    // Test reading from accessible tables
    for (const tableName of this.testTables) {
      try {
        const { data, error } = await this.supabase
          .from(tableName)
          .select('*')
          .limit(5);

        if (error) {
          const errorMsg = `Read from ${tableName}: ${error.message}`;
          console.warn(`⚠️ ${errorMsg}`);
          errors.push(errorMsg);
        } else {
          console.log(`✅ Successfully read from ${tableName} (${data?.length || 0} rows)`);
          successCount++;
        }
      } catch (error) {
        const errorMsg = `Read from ${tableName}: ${error}`;
        console.error(`❌ ${errorMsg}`);
        errors.push(errorMsg);
      }
    }

    const success = successCount > 0;
    console.log(`📊 Read operations test: ${successCount}/${this.testTables.length} tables readable`);
    
    return { success, errors };
  }

  /**
   * Test write operations (safe test inserts)
   */
  async testWriteOperations(): Promise<{ success: boolean; errors: string[] }> {
    console.log('✏️ Testing write operations...');
    
    const errors: string[] = [];
    let writeTestPassed = false;

    // Test write operation on leads table (most likely to be writable)
    try {
      const testEmail = `dbwire-test-${Date.now()}@example.com`;
      
      // Attempt test insert
      const { data: insertData, error: insertError } = await this.supabase
        .from('leads')
        .insert({
          name: 'DB Wire Test',
          email: testEmail,
          source: 'dbwire',
          trace_tag: 'health-check'
        })
        .select();

      if (insertError) {
        const errorMsg = `Insert test failed: ${insertError.message}`;
        console.warn(`⚠️ ${errorMsg}`);
        errors.push(errorMsg);
      } else {
        console.log(`✅ Successfully inserted test record`);
        writeTestPassed = true;

        // Clean up - attempt to delete the test record
        if (insertData && insertData.length > 0) {
          const testId = insertData[0].id;
          const { error: deleteError } = await this.supabase
            .from('leads')
            .delete()
            .eq('id', testId);

          if (deleteError) {
            console.warn(`⚠️ Could not clean up test record: ${deleteError.message}`);
          } else {
            console.log(`🧹 Cleaned up test record`);
          }
        }
      }
    } catch (error) {
      const errorMsg = `Write test failed: ${error}`;
      console.error(`❌ ${errorMsg}`);
      errors.push(errorMsg);
    }

    if (writeTestPassed) {
      console.log(`📊 Write operations test: PASSED`);
    } else {
      console.log(`📊 Write operations test: FAILED`);
    }
    
    return { success: writeTestPassed, errors };
  }

  /**
   * Perform comprehensive database health check
   */
  async performHealthCheck(): Promise<DatabaseHealth> {
    console.log('🏥 Starting comprehensive database health check...');
    console.log('================================================');

    const health: DatabaseHealth = {
      connection: false,
      tablesAccessible: false,
      readOperations: false,
      writeOperations: false,
      errors: []
    };

    // Test connection
    health.connection = await this.testConnection();
    if (!health.connection) {
      health.errors.push('Database connection failed');
      return health; // Early exit if connection fails
    }

    // Test table access
    const tableTest = await this.testTableAccess();
    health.tablesAccessible = tableTest.success;
    health.errors.push(...tableTest.errors);

    // Test read operations
    const readTest = await this.testReadOperations();
    health.readOperations = readTest.success;
    health.errors.push(...readTest.errors);

    // Test write operations
    const writeTest = await this.testWriteOperations();
    health.writeOperations = writeTest.success;
    health.errors.push(...writeTest.errors);

    return health;
  }

  /**
   * Generate health report
   */
  generateHealthReport(health: DatabaseHealth): void {
    console.log('\n📊 Database Health Report');
    console.log('========================');
    console.log(`🔌 Connection: ${health.connection ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`📋 Table Access: ${health.tablesAccessible ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`📖 Read Operations: ${health.readOperations ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`✏️ Write Operations: ${health.writeOperations ? '✅ PASS' : '❌ FAIL'}`);

    const overallHealth = health.connection && health.tablesAccessible && health.readOperations;
    console.log(`\n🏥 Overall Health: ${overallHealth ? '✅ HEALTHY' : '❌ UNHEALTHY'}`);

    if (health.errors.length > 0) {
      console.log('\n⚠️ Issues Detected:');
      health.errors.forEach((error, index) => {
        console.log(`   ${index + 1}. ${error}`);
      });
    }

    console.log(`\n⏰ Health check completed at: ${new Date().toISOString()}`);
  }

  /**
   * Main execution method
   */
  async run(): Promise<void> {
    try {
      const health = await this.performHealthCheck();
      this.generateHealthReport(health);

      // Exit with appropriate code
      const isHealthy = health.connection && health.tablesAccessible && health.readOperations;
      if (!isHealthy) {
        console.log('\n❌ Database health check FAILED');
        process.exit(1);
      } else {
        console.log('\n✅ Database health check PASSED');
        process.exit(0);
      }
    } catch (error) {
      console.error('\n💥 DB Wire check failed:');
      console.error(error instanceof Error ? error.message : String(error));
  async run(): Promise<number> {
    try {
      const health = await this.performHealthCheck();
      this.generateHealthReport(health);

      // Return appropriate exit code
      const isHealthy = health.connection && health.tablesAccessible && health.readOperations;
      if (!isHealthy) {
        console.log('\n❌ Database health check FAILED');
        return 1;
      } else {
        console.log('\n✅ Database health check PASSED');
        return 0;
      }
    } catch (error) {
      console.error('\n💥 DB Wire check failed:');
      console.error(error instanceof Error ? error.message : String(error));
      return 2;
    }
  }
}

/**
 * Main entry point for the DB Wire bot
 */
export async function main(args: string[] = []): Promise<void> {
  const prog = program
    .name('db-wire')
    .description('Database wiring bot that performs connectivity and health checks')
    .action(async () => {
      const checker = new DatabaseWireChecker();
      await checker.run();
    });

  // Handle unhandled errors
  process.on('unhandledRejection', (reason, promise) => {
    console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
  });

  process.on('uncaughtException', (error) => {
    console.error('💥 Uncaught Exception:', error);
    process.exit(1);
  });

  // Parse CLI arguments
  await prog.parseAsync(args.length ? args : process.argv);
}

// Only run if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();

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
  const isDevOrTest = process.env.NODE_ENV === 'development' || process.env.NODE_ENV === 'test';
  const client = new Client({
    connectionString: supabaseDbUrl,
    ssl: isDevOrTest ? { rejectUnauthorized: false } : undefined
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