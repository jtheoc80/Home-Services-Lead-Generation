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
      process.exit(2);
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
}