#!/usr/bin/env tsx

/**
 * QB Auditor - Security and Configuration Audit Tool
 * 
 * Performs QuickBooks-style auditing of environment variables, configuration files,
 * and potential security leaks in the Home Services Lead Generation platform.
 */

import { readFileSync, existsSync, readdirSync, statSync } from 'fs';
import { join, resolve } from 'path';

interface AuditResult {
  success: boolean;
  errors: string[];
  warnings: string[];
}

interface EnvCheck {
  name: string;
  present: boolean;
  value: string;
  masked: string;
}

class QBPlatformAuditor {
  private errors: string[] = [];
  private warnings: string[] = [];
  private rootDir: string;

  constructor() {
    this.rootDir = resolve(process.cwd());
  }

  /**
   * Main audit function - orchestrates all checks
   */
  async audit(): Promise<AuditResult> {
    console.log('🔍 QB Auditor - Security & Configuration Audit');
    console.log('==================================================\n');

    // Step 1: Environment variable checks
    this.checkEnvironmentVariables();

    // Step 2: Leak detection
    await this.performLeakDetection();

    // Step 3: Config file validation
    this.validateConfigFiles();

    // Step 4: Deployment configuration security
    this.validateDeploymentConfigs();

    // Print summary
    this.printSummary();

    return {
      success: this.errors.length === 0,
      errors: this.errors,
      warnings: this.warnings
    };
  }

  /**
   * Check presence of required environment variables
   */
  private checkEnvironmentVariables(): void {
    console.log('📋 Environment Variables Check');
    console.log('------------------------------');

    const requiredEnvs = [
      'NEXT_PUBLIC_SUPABASE_URL',
      'NEXT_PUBLIC_SUPABASE_ANON_KEY',
      'SUPABASE_SERVICE_ROLE_KEY',
      'SUPABASE_DB_URL',
      'LEADS_TEST_MODE',
      'DEBUG_API_KEY',
      'HC_ISSUED_PERMITS_URL',
      'REDIS_URL'
    ];

    const checks: EnvCheck[] = [];

    // Check for REDIS_URL or Upstash REST pair
    const hasRedisUrl = !!process.env.REDIS_URL;
    const hasUpstashPair = !!(process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN);

    for (const envName of requiredEnvs) {
      if (envName === 'REDIS_URL') {
        // Special handling for Redis - accept either REDIS_URL or Upstash pair
        if (hasRedisUrl) {
          checks.push({
            name: envName,
            present: true,
            value: process.env.REDIS_URL || '',
            masked: this.maskValue(process.env.REDIS_URL || '')
          });
        } else if (hasUpstashPair) {
          checks.push({
            name: 'REDIS_URL (Upstash REST)',
            present: true,
            value: `${process.env.UPSTASH_REDIS_REST_URL}`,
            masked: `${this.maskValue(process.env.UPSTASH_REDIS_REST_URL || '')} + token`
          });
        } else {
          checks.push({
            name: envName,
            present: false,
            value: '',
            masked: ''
          });
          this.errors.push(`❌ Missing Redis configuration: Set either REDIS_URL or both UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN`);
        }
      } else {
        const value = process.env[envName];
        const present = !!value;
        checks.push({
          name: envName,
          present,
          value: value || '',
          masked: present ? this.maskValue(value || '') : ''
        });

        if (!present) {
          this.errors.push(`❌ Missing required environment variable: ${envName}`);
        }
      }
    }

    // Handle SUPABASE_DB_URL vs DATABASE_URL
    if (!process.env.SUPABASE_DB_URL && process.env.DATABASE_URL) {
      this.warnings.push(`⚠️  Using DATABASE_URL instead of SUPABASE_DB_URL - consider updating to SUPABASE_DB_URL for clarity`);
      // Update the check to show DATABASE_URL as present
      const dbUrlCheck = checks.find(c => c.name === 'SUPABASE_DB_URL');
      if (dbUrlCheck) {
        dbUrlCheck.present = true;
        dbUrlCheck.value = process.env.DATABASE_URL || '';
        dbUrlCheck.masked = this.maskValue(process.env.DATABASE_URL || '');
        dbUrlCheck.name = 'SUPABASE_DB_URL (via DATABASE_URL)';
        // Remove the error for this specific case
        this.errors = this.errors.filter(e => !e.includes('SUPABASE_DB_URL'));
      }
    }

    // Print table
    console.log('┌─────────────────────────────────────┬────────┬──────────────────────┐');
    console.log('│ Environment Variable                │ Status │ Value (masked)       │');
    console.log('├─────────────────────────────────────┼────────┼──────────────────────┤');

    for (const check of checks) {
      const name = check.name.padEnd(35);
      const status = check.present ? '   ✓   ' : '   ✗   ';
      const masked = check.masked.padEnd(20);
      console.log(`│ ${name} │ ${status} │ ${masked} │`);
    }

    console.log('└─────────────────────────────────────┴────────┴──────────────────────┘\n');
  }

  /**
   * Perform leak detection checks
   */
  private async performLeakDetection(): Promise<void> {
    console.log('🔐 Leak Detection');
    console.log('------------------');

    // Check if any NEXT_PUBLIC_* values equal server secrets
    this.checkPublicVsServerSecrets();

    // Scan frontend directory for accidental secrets
    await this.scanFrontendForSecrets();

    console.log('');
  }

  /**
   * Check if any NEXT_PUBLIC_* values match server secrets
   */
  private checkPublicVsServerSecrets(): void {
    const publicVars = Object.keys(process.env)
      .filter(key => key.startsWith('NEXT_PUBLIC_'))
      .map(key => ({ key, value: process.env[key] }));

    const serverSecrets = [
      'SUPABASE_SERVICE_ROLE_KEY',
      'SUPABASE_JWT_SECRET',
      'STRIPE_SECRET_KEY',
      'STRIPE_WEBHOOK_SECRET',
      'DEBUG_API_KEY',
      'INTERNAL_WEBHOOK_TOKEN'
    ].map(key => ({ key, value: process.env[key] }))
     .filter(item => item.value);

    for (const publicVar of publicVars) {
      for (const secret of serverSecrets) {
        if (publicVar.value && publicVar.value === secret.value) {
          this.errors.push(`🚨 CRITICAL: Public variable ${publicVar.key} contains server secret ${secret.key}!`);
        }
      }
    }

    if (this.errors.filter(e => e.includes('CRITICAL')).length === 0) {
      console.log('✅ No NEXT_PUBLIC_* variables contain server secrets');
    }
  }

  /**
   * Scan frontend directory for accidental secret exposure
   */
  private async scanFrontendForSecrets(): Promise<void> {
    const frontendDir = join(this.rootDir, 'frontend');
    
    if (!existsSync(frontendDir)) {
      this.warnings.push('⚠️  Frontend directory not found - skipping secret scan');
      return;
    }

    const dangerousPatterns = [
      // Look for hardcoded JWT tokens (base64 encoded, starting with eyJ)
      /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*/g,
      // Look for hardcoded API keys with common prefixes
      /['"`](sk_live_|sk_test_|pk_live_|pk_test_)[A-Za-z0-9_]+['"`]/g,
      // Look for hardcoded Stripe webhook secrets
      /['"`]whsec_[A-Za-z0-9_]+['"`]/g,
      // Look for hardcoded tokens in KV pattern
      /['"`]AX[A-Za-z0-9_]{20,}['"`]/g,
      // Look for hardcoded supabase service role keys (JWT pattern)
      /['"\`]eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*service_role[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*['"\`]/g,
      // Look for hardcoded database URLs with credentials
      /['"`]postgres(ql)?:\/\/[^\/\s]+:[^\/\s]+@[^\/\s]+\/[^\/\s]+['"`]/g
    ];

    const foundSecrets = this.scanDirectoryForPatterns(frontendDir, dangerousPatterns, true);

    if (foundSecrets.length > 0) {
      for (const secret of foundSecrets) {
        this.errors.push(`🚨 HARDCODED SECRET: Found ${secret.pattern} in ${secret.file}:${secret.line}`);
      }
    } else {
      console.log('✅ No hardcoded secrets found in frontend directory');
    }
  }

  /**
   * Recursively scan directory for dangerous patterns
   */
  private scanDirectoryForPatterns(dir: string, patterns: RegExp[], checkHardcodedValues = false): Array<{file: string, pattern: string, line: number}> {
    const results: Array<{file: string, pattern: string, line: number}> = [];
    
    try {
      const entries = readdirSync(dir);
      
      for (const entry of entries) {
        const fullPath = join(dir, entry);
        const stat = statSync(fullPath);
        
        if (stat.isDirectory()) {
          // Skip node_modules, .git, .next directories
          if (['node_modules', '.git', '.next', 'dist', 'build'].includes(entry)) {
            continue;
          }
          results.push(...this.scanDirectoryForPatterns(fullPath, patterns, checkHardcodedValues));
        } else if (stat.isFile()) {
          // Only scan text files
          if (this.isTextFile(entry)) {
            const content = readFileSync(fullPath, 'utf-8');
            const lines = content.split('\n');
            
            for (let lineNum = 0; lineNum < lines.length; lineNum++) {
              const line = lines[lineNum];
              
              for (const pattern of patterns) {
                const matches = line.match(pattern);
                if (matches) {
                  // If checking for hardcoded values, skip if it's in an API route or lib file using process.env
                  if (checkHardcodedValues && this.isServerSideCode(fullPath) && line.includes('process.env')) {
                    continue;
                  }
                  
                  results.push({
                    file: fullPath.replace(this.rootDir, '.'),
                    pattern: matches[0].replace(/['"`]/g, '[REDACTED]'), // Mask the actual value
                    line: lineNum + 1
                  });
                }
              }
            }
          }
        }
      }
    } catch (error) {
      this.warnings.push(`⚠️  Could not scan directory ${dir}: ${error}`);
    }
    
    return results;
  }

  /**
   * Check if file is server-side code where environment variable usage is expected
   */
  private isServerSideCode(filePath: string): boolean {
    return filePath.includes('/api/') || 
           filePath.includes('/lib/') ||
           filePath.includes('server') ||
           filePath.endsWith('middleware.ts') ||
           filePath.endsWith('middleware.js');
  }

  /**
   * Check if file is likely a text file to scan
   */
  private isTextFile(filename: string): boolean {
    const textExtensions = ['.ts', '.tsx', '.js', '.jsx', '.json', '.env', '.md', '.txt', '.yml', '.yaml'];
    return textExtensions.some(ext => filename.endsWith(ext));
  }

  /**
   * Validate configuration files exist and contain required keys
   */
  private validateConfigFiles(): void {
    console.log('📁 Configuration Files');
    console.log('----------------------');

    const requiredKeys = [
      'NEXT_PUBLIC_SUPABASE_URL',
      'NEXT_PUBLIC_SUPABASE_ANON_KEY',
      'SUPABASE_SERVICE_ROLE_KEY',
      'LEADS_TEST_MODE',
      'DEBUG_API_KEY',
      'HC_ISSUED_PERMITS_URL',
      'REDIS_URL'
    ];

    // Check .env.example
    this.validateEnvExampleFile('.env.example', requiredKeys);

    // Check frontend/.env.local.example
    this.validateEnvExampleFile('frontend/.env.local.example', requiredKeys);

    console.log('');
  }

  /**
   * Validate a specific .env.example file
   */
  private validateEnvExampleFile(filePath: string, requiredKeys: string[]): void {
    const fullPath = join(this.rootDir, filePath);
    
    if (!existsSync(fullPath)) {
      this.errors.push(`❌ Missing file: ${filePath}`);
      return;
    }

    console.log(`✅ ${filePath} exists`);

    try {
      const content = readFileSync(fullPath, 'utf-8');
      const missingKeys = requiredKeys.filter(key => {
        // Check if key is present (commented or uncommented)
        return !content.includes(key);
      });

      if (missingKeys.length > 0) {
        for (const key of missingKeys) {
          this.errors.push(`❌ ${filePath} missing key: ${key}`);
        }
      } else {
        console.log(`✅ ${filePath} contains all required keys`);
      }
    } catch (error) {
      this.errors.push(`❌ Could not read ${filePath}: ${error}`);
    }
  }

  /**
   * Validate deployment configuration files for security issues
   */
  private validateDeploymentConfigs(): void {
    console.log('🚀 Deployment Configuration');
    console.log('----------------------------');

    // Check vercel.json
    this.validateVercelConfig();

    // Check railway.json
    this.validateRailwayConfig();

    console.log('');
  }

  /**
   * Validate vercel.json for security issues
   */
  private validateVercelConfig(): void {
    const vercelPath = join(this.rootDir, 'vercel.json');
    
    if (!existsSync(vercelPath)) {
      this.warnings.push('⚠️  vercel.json not found - skipping Vercel config check');
      return;
    }

    try {
      const content = readFileSync(vercelPath, 'utf-8');
      const config = JSON.parse(content);

      console.log('✅ vercel.json exists and is valid JSON');

      // Check headers for potential secret echoing
      if (config.headers) {
        for (const headerConfig of config.headers) {
          if (headerConfig.headers) {
            for (const header of headerConfig.headers) {
              const headerValue = header.value?.toLowerCase() || '';
              
              // Check for patterns that might echo secrets
              const dangerousPatterns = [
                'service_role', 'jwt_secret', 'secret_key', 'webhook_secret',
                'auth_token', 'api_key', 'private_key'
              ];

              for (const pattern of dangerousPatterns) {
                if (headerValue.includes(pattern)) {
                  this.errors.push(`🚨 vercel.json header may echo secrets: ${header.key}: ${header.value}`);
                }
              }
            }
          }
        }
      }

      if (this.errors.filter(e => e.includes('vercel.json header')).length === 0) {
        console.log('✅ vercel.json headers do not echo secrets');
      }

    } catch (error) {
      this.errors.push(`❌ Invalid vercel.json: ${error}`);
    }
  }

  /**
   * Validate railway.json for required configurations
   */
  private validateRailwayConfig(): void {
    const railwayPath = join(this.rootDir, 'railway.json');
    
    if (!existsSync(railwayPath)) {
      this.warnings.push('⚠️  railway.json not found - skipping Railway config check');
      return;
    }

    try {
      const content = readFileSync(railwayPath, 'utf-8');
      const config = JSON.parse(content);

      console.log('✅ railway.json exists and is valid JSON');

      // Check for healthcheck paths in deploy or services
      let hasHealthcheck = false;

      // Check top-level deploy config
      if (config.deploy?.healthcheckPath) {
        hasHealthcheck = true;
        console.log('✅ railway.json has healthcheck path in deploy config');
      }

      // Check services for healthcheck
      if (config.services) {
        for (const [serviceName, serviceConfig] of Object.entries(config.services)) {
          if ((serviceConfig as any)?.deploy?.healthcheckPath) {
            hasHealthcheck = true;
            console.log(`✅ railway.json service '${serviceName}' has healthcheck path`);
          }
        }
      }

      if (!hasHealthcheck) {
        this.warnings.push('⚠️  railway.json missing healthcheck paths - consider adding for better monitoring');
      }

    } catch (error) {
      this.errors.push(`❌ Invalid railway.json: ${error}`);
    }
  }

  /**
   * Mask sensitive values to show only last 4 characters
   */
  private maskValue(value: string): string {
    if (!value || value.length <= 4) {
      return '****';
    }
    
    const masked = '*'.repeat(Math.max(0, value.length - 4));
    return masked + value.slice(-4);
  }

  /**
   * Print audit summary and actionable fixes
   */
  private printSummary(): void {
    console.log('📊 Audit Summary');
    console.log('================');

    if (this.errors.length === 0 && this.warnings.length === 0) {
      console.log('🎉 All checks passed! Your configuration is secure.');
      return;
    }

    if (this.errors.length > 0) {
      console.log('\n❌ ERRORS (must fix):');
      console.log('---------------------');
      for (const error of this.errors) {
        console.log(error);
      }

      console.log('\n🔧 ACTIONABLE FIXES:');
      console.log('--------------------');
      this.printActionableFixes();
    }

    if (this.warnings.length > 0) {
      console.log('\n⚠️  WARNINGS (recommended fixes):');
      console.log('----------------------------------');
      for (const warning of this.warnings) {
        console.log(warning);
      }
    }

    console.log(`\n📈 Results: ${this.errors.length} errors, ${this.warnings.length} warnings`);
  }

  /**
   * Print actionable fix instructions
   */
  private printActionableFixes(): void {
    for (const error of this.errors) {
      if (error.includes('Missing required environment variable')) {
        const varName = error.split(': ')[1];
        console.log(`   • Set ${varName} in your .env file`);
        console.log(`   • Copy from .env.example: cp .env.example .env`);
        console.log(`   • Update the value in .env file`);
      }
      
      if (error.includes('Missing Redis configuration')) {
        console.log(`   • Set REDIS_URL=redis://localhost:6379/0 for local Redis`);
        console.log(`   • OR set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN for Upstash`);
      }

      if (error.includes('CRITICAL: Public variable')) {
        console.log(`   • Move server secret to server-only environment variable`);
        console.log(`   • Remove NEXT_PUBLIC_ prefix from server secrets`);
        console.log(`   • Update frontend code to use server-side API calls`);
      }

      if (error.includes('HARDCODED SECRET')) {
        const parts = error.split(' in ');
        if (parts.length > 1) {
          const file = parts[1].split(':')[0];
          console.log(`   • Remove hardcoded secrets from ${file}`);
          console.log(`   • Use environment variables instead of hardcoded values`);
          console.log(`   • Move sensitive values to .env file and reference via process.env`);
        }
      }

      if (error.includes('Missing file')) {
        const file = error.split(': ')[1];
        console.log(`   • Create ${file} with required environment variables`);
        console.log(`   • Use root .env.example as reference`);
      }
    }
  }
}

/**
 * Main execution function
 */
async function main(): Promise<void> {
  const auditor = new QBPlatformAuditor();
  
  try {
    const result = await auditor.audit();
    
    // Exit with appropriate code
    process.exit(result.success ? 0 : 1);
  } catch (error) {
    console.error('❌ Audit failed with error:', error);
    process.exit(1);
  }
}

// Run the auditor if this file is executed directly
if (fileURLToPath(import.meta.url) === process.argv[1]) {
  main();
}

export { QBPlatformAuditor };
=======

/**
 * QB Auditor Bot
 * 
 * Schema auditing bot that compares local and live database schemas.
 * Based on the existing schema-drift-check.ts script.
 */

import { createClient } from '@supabase/supabase-js';
import * as fs from 'fs/promises';
import * as path from 'path';
import { program } from 'commander';

interface TableColumn {
  column_name: string;
  data_type: string;
  is_nullable: string;
  column_default: string | null;
  character_maximum_length: number | null;
  numeric_precision: number | null;
  numeric_scale: number | null;
}

interface TableInfo {
  table_name: string;
  columns: TableColumn[];
  indexes: IndexInfo[];
  constraints: ConstraintInfo[];
}

interface IndexInfo {
  index_name: string;
  column_names: string[];
  is_unique: boolean;
  index_type: string;
}

interface ConstraintInfo {
  constraint_name: string;
  constraint_type: string;
  column_names: string[];
  referenced_table?: string;
  referenced_columns?: string[];
}

interface SchemaComparison {
  missingTables: string[];
  extraTables: string[];
  tableDifferences: {
    [tableName: string]: {
      missingColumns: string[];
      extraColumns: string[];
      modifiedColumns: Array<{
        column: string;
        local: string;
        live: string;
      }>;
      missingIndexes: string[];
      extraIndexes: string[];
      missingConstraints: string[];
      extraConstraints: string[];
    };
  };
}

class SchemaDriftChecker {
  private supabase;
  private modelsFilePath: string;

  constructor() {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !serviceRoleKey) {
      throw new Error('Missing required environment variables: NEXT_PUBLIC_SUPABASE_URL (or SUPABASE_URL) and SUPABASE_SERVICE_ROLE_KEY');
    }

    this.supabase = createClient(supabaseUrl, serviceRoleKey);
    this.modelsFilePath = path.join(process.cwd(), 'backend', 'app', 'models.sql');
  }

  /**
   * Extract table information from the live Supabase database
   */
  async extractLiveSchema(): Promise<Map<string, TableInfo>> {
    console.log('📊 Extracting live schema from Supabase...');
    
    const tables = new Map<string, TableInfo>();

    try {
      // Discover tables by attempting to query known tables from models.sql
      console.log('🔍 Discovering tables from models.sql definitions...');
      
      const localSchema = await this.extractLocalSchema();
      const knownTables = Array.from(localSchema.keys());
      
      for (const tableName of knownTables) {
        try {
          // Test if table exists by attempting to query it
          const { error } = await this.supabase
            .from(tableName)
            .select('*')
            .limit(0);

          if (!error) {
            // Table exists, but we can't get detailed schema info
            // So we'll mark it as existing with minimal info
            tables.set(tableName, {
              table_name: tableName,
              columns: [], // Will be detected as differences in comparison
              indexes: [],
              constraints: []
            });
            console.log(`✅ Confirmed table exists: ${tableName}`);
          } else {
            console.log(`⚠️ Table ${tableName} may not exist or is not accessible`);
          }
        } catch (tableError) {
          console.log(`⚠️ Could not check table ${tableName}:`, tableError);
        }
      }

      if (tables.size === 0) {
        throw new Error('Could not discover any tables. Please check Supabase connection and permissions.');
      }

      console.log(`✅ Discovered ${tables.size} tables using fallback method`);
      return tables;

    } catch (error) {
      console.error('❌ Failed to extract live schema:', error);
      throw new Error(`Could not extract schema from Supabase: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Parse local models.sql file to extract expected schema
   */
  async extractLocalSchema(): Promise<Map<string, TableInfo>> {
    console.log('📄 Parsing local models.sql file...');
    
    try {
      const sqlContent = await fs.readFile(this.modelsFilePath, 'utf-8');
      const tables = new Map<string, TableInfo>();
      
      // Normalize line endings and handle multiline content
      const normalizedContent = sqlContent.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
      
      // Find all CREATE TABLE statements with better regex handling
      const tableRegex = /CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)\s*\(([\s\S]*?)\);/gi;
      let match;
      
      while ((match = tableRegex.exec(normalizedContent)) !== null) {
        const tableName = match[1];
        const tableBody = match[2];
        
        // Skip duplicate table definitions (keep the last one)
        const columns = this.parseTableColumns(tableBody);
        const indexes = this.extractIndexesFromSQL(normalizedContent, tableName);
        const constraints = this.extractConstraintsFromTable(tableBody);

        tables.set(tableName, {
          table_name: tableName,
          columns,
          indexes,
          constraints
        });
      }

      console.log(`✅ Parsed ${tables.size} tables from models.sql`);
      return tables;
    } catch (error) {
      throw new Error(`Failed to read models.sql: ${error}`);
    }
  }

  /**
   * Compare local and live schemas
   */
  compareSchemas(localSchema: Map<string, TableInfo>, liveSchema: Map<string, TableInfo>): SchemaComparison {
    console.log('🔍 Comparing schemas...');
    
    const comparison: SchemaComparison = {
      missingTables: [],
      extraTables: [],
      tableDifferences: {}
    };

    // Find missing and extra tables
    const localTables = new Set(localSchema.keys());
    const liveTables = new Set(liveSchema.keys());

    comparison.missingTables = Array.from(localTables).filter(table => !liveTables.has(table));
    comparison.extraTables = Array.from(liveTables).filter(table => !localTables.has(table));

    // Compare common tables
    const commonTables = Array.from(localTables).filter(table => liveTables.has(table));
    
    for (const tableName of commonTables) {
      const localTable = localSchema.get(tableName)!;
      const liveTable = liveSchema.get(tableName)!;
      
      const tableDiff = this.compareTableStructure(localTable, liveTable);
      if (this.hasTableDifferences(tableDiff)) {
        comparison.tableDifferences[tableName] = tableDiff;
      }
    }

    return comparison;
  }

  /**
   * Generate migration SQL based on schema differences
   */
  generateMigrationSQL(comparison: SchemaComparison): string {
    console.log('📝 Generating migration SQL...');
    
    const migrations: string[] = [];
    migrations.push('-- Schema Drift Migration');
    migrations.push('-- Generated automatically by qb-auditor');
    migrations.push(`-- Generated at: ${new Date().toISOString()}`);
    migrations.push('');

    // Handle missing tables
    for (const tableName of comparison.missingTables) {
      migrations.push(`-- TODO: Add CREATE TABLE statement for missing table: ${tableName}`);
      migrations.push(`-- Please manually add the CREATE TABLE statement from models.sql`);
      migrations.push('');
    }

    // Handle extra tables
    for (const tableName of comparison.extraTables) {
      migrations.push(`-- WARNING: Extra table found in live schema: ${tableName}`);
      migrations.push(`-- Consider if this table should be added to models.sql or removed from live schema`);
      migrations.push('');
    }

    // Handle table differences
    for (const [tableName, diff] of Object.entries(comparison.tableDifferences)) {
      migrations.push(`-- Migrations for table: ${tableName}`);
      
      // Missing columns
      for (const column of diff.missingColumns) {
        migrations.push(`-- TODO: Add missing column ${column} to table ${tableName}`);
        migrations.push(`-- ALTER TABLE ${tableName} ADD COLUMN ${column} [TYPE];`);
      }

      // Extra columns
      for (const column of diff.extraColumns) {
        migrations.push(`-- WARNING: Extra column ${column} found in live table ${tableName}`);
        migrations.push(`-- Consider if this should be added to models.sql or removed from live schema`);
      }

      // Modified columns
      for (const mod of diff.modifiedColumns) {
        migrations.push(`-- Column ${mod.column} differs between local and live schema`);
        migrations.push(`-- Local: ${mod.local}`);
        migrations.push(`-- Live:  ${mod.live}`);
        migrations.push(`-- TODO: Review and add appropriate ALTER COLUMN statement`);
      }

      migrations.push('');
    }

    if (migrations.length === 4) {
      return '-- No schema drift detected\n-- All tables and columns match between local and live schemas\n';
    }

    return migrations.join('\n');
  }

  // Helper methods
  private parseTableColumns(tableBody: string): TableColumn[] {
    const columns: TableColumn[] = [];
    const lines = tableBody.split(',').map(line => line.trim()).filter(line => line.length > 0);
    
    for (const line of lines) {
      // Skip comments and table-level constraints
      if (line.startsWith('--') || /^CONSTRAINT\b/i.test(line)) {
        continue;
      }

      // Tokenize the line
      const tokens = line.split(/\s+/);
      if (tokens.length < 2) continue;

      // Extract column name and data type
      const columnName = tokens[0];
      let dataType = tokens[1];
      let i = 2;
      // If data type is multi-word (e.g., "DOUBLE PRECISION", "CHARACTER VARYING")
      while (i < tokens.length && !/^(NOT|NULL|DEFAULT|PRIMARY|UNIQUE|CHECK|REFERENCES)$/i.test(tokens[i])) {
        dataType += ' ' + tokens[i];
        i++;
      }

      // Initialize attributes
      let isNullable = 'YES';
      let columnDefault: string | null = null;

      // Scan for constraints and attributes
      for (; i < tokens.length; i++) {
        const token = tokens[i].toUpperCase();
        if (token === 'NOT' && tokens[i+1] && tokens[i+1].toUpperCase() === 'NULL') {
          isNullable = 'NO';
          i++;
        } else if (token === 'NULL') {
          isNullable = 'YES';
        } else if (token === 'DEFAULT' && tokens[i+1]) {
          columnDefault = tokens.slice(i+1).join(' ');
          break;
        }
        // Ignore PRIMARY, UNIQUE, CHECK, REFERENCES for column-level parsing
      }

      columns.push({
        column_name: columnName,
        data_type: dataType.toUpperCase(),
        is_nullable: isNullable,
        column_default: columnDefault,
        character_maximum_length: null,
        numeric_precision: null,
        numeric_scale: null
      });
    }
    
    return columns;
  }

  private extractIndexesFromSQL(sqlContent: string, tableName: string): IndexInfo[] {
    const indexes: IndexInfo[] = [];
    const indexRegex = new RegExp(`CREATE\\s+(?:UNIQUE\\s+)?INDEX\\s+(?:IF\\s+NOT\\s+EXISTS\\s+)?(\\w+)\\s+ON\\s+${tableName}\\s*\\(([^)]+)\\)`, 'gi');
    let match;

    while ((match = indexRegex.exec(sqlContent)) !== null) {
      const indexName = match[1];
      const columnList = match[2];
      indexes.push({
        index_name: indexName,
        column_names: columnList.split(',').map(col => col.trim()),
        is_unique: match[0].toUpperCase().includes('UNIQUE'),
        index_type: 'btree'
      });
    }

    return indexes;
  }

  private extractConstraintsFromTable(tableBody: string): ConstraintInfo[] {
    const constraints: ConstraintInfo[] = [];
    
    // Look for REFERENCES constraints
    const foreignKeyRegex = /(\w+)\s+.*?REFERENCES\s+(\w+)\((\w+)\)/gi;
    let match;

    while ((match = foreignKeyRegex.exec(tableBody)) !== null) {
      constraints.push({
        constraint_name: `fk_${match[1]}_${match[2]}`,
        constraint_type: 'FOREIGN KEY',
        column_names: [match[1]],
        referenced_table: match[2],
        referenced_columns: [match[3]]
      });
    }

    return constraints;
  }

  private compareTableStructure(localTable: TableInfo, liveTable: TableInfo) {
    const localColumns = new Set(localTable.columns.map(col => col.column_name));
    const liveColumns = new Set(liveTable.columns.map(col => col.column_name));

    const missingColumns = Array.from(localColumns).filter(col => !liveColumns.has(col));
    const extraColumns = Array.from(liveColumns).filter(col => !localColumns.has(col));

    const modifiedColumns: Array<{column: string; local: string; live: string}> = [];
    
    // Compare common columns
    const commonColumns = Array.from(localColumns).filter(col => liveColumns.has(col));
    for (const colName of commonColumns) {
      const localCol = localTable.columns.find(c => c.column_name === colName)!;
      const liveCol = liveTable.columns.find(c => c.column_name === colName)!;
      
      if (localCol.data_type !== liveCol.data_type || localCol.is_nullable !== liveCol.is_nullable) {
        modifiedColumns.push({
          column: colName,
          local: `${localCol.data_type} ${localCol.is_nullable}`,
          live: `${liveCol.data_type} ${liveCol.is_nullable}`
        });
      }
    }

    return {
      missingColumns,
      extraColumns,
      modifiedColumns,
      missingIndexes: [],
      extraIndexes: [],
      missingConstraints: [],
      extraConstraints: []
    };
  }

  private hasTableDifferences(diff: TableDifferences): boolean {
    return diff.missingColumns.length > 0 || 
           diff.extraColumns.length > 0 || 
           diff.modifiedColumns.length > 0 ||
           diff.missingIndexes.length > 0 ||
           diff.extraIndexes.length > 0 ||
           diff.missingConstraints.length > 0 ||
           diff.extraConstraints.length > 0;
  }

  /**
   * Main execution method
   */
  async run(): Promise<void> {
    try {
      console.log('🔍 QB Auditor - Schema Drift Detection Starting...');
      console.log('===============================================');

      // Extract schemas
      const [localSchema, liveSchema] = await Promise.all([
        this.extractLocalSchema(),
        this.extractLiveSchema()
      ]);

      // Compare schemas
      const comparison = this.compareSchemas(localSchema, liveSchema);

      // Check if there are any differences
      const hasDrift = comparison.missingTables.length > 0 || 
                     comparison.extraTables.length > 0 || 
                     Object.keys(comparison.tableDifferences).length > 0;

      if (!hasDrift) {
        console.log('✅ No schema drift detected!');
        console.log('📊 Summary:');
        console.log(`   - Local tables: ${localSchema.size}`);
        console.log(`   - Live tables: ${liveSchema.size}`);
        console.log('   - All schemas match perfectly');
        return;
      }

      // Generate migration
      const migrationSQL = this.generateMigrationSQL(comparison);

      console.log('⚠️  Schema drift detected!');
      console.log('📊 Summary:');
      console.log(`   - Missing tables: ${comparison.missingTables.length}`);
      console.log(`   - Extra tables: ${comparison.extraTables.length}`);
      console.log(`   - Tables with differences: ${Object.keys(comparison.tableDifferences).length}`);

      // Write migration file
      const migrationPath = path.join(process.cwd(), 'schema-drift-migration.sql');
      await fs.writeFile(migrationPath, migrationSQL);
      console.log(`📝 Migration SQL written to: ${migrationPath}`);

      // Write detailed comparison as JSON
      const comparisonPath = path.join(process.cwd(), 'schema-drift-details.json');
      await fs.writeFile(comparisonPath, JSON.stringify(comparison, null, 2));
      console.log(`📄 Detailed comparison written to: ${comparisonPath}`);

      process.exit(1); // Exit with code 1 to indicate drift found
      
    } catch (error) {
      console.error('❌ QB Auditor failed:');
      console.error(error instanceof Error ? error.message : String(error));
      return 1; // Exit code 1 to indicate drift found
      
    } catch (error) {
      console.error('❌ QB Auditor failed:');
      console.error(error instanceof Error ? error.message : String(error));
      return 2;
    }
  }
}

/**
 * Main entry point for the QB Auditor bot
 */
export async function main(args: string[] = []): Promise<void> {
  const prog = program
    .name('qb-auditor')
    .description('Schema auditing bot that compares local and live database schemas')
    .action(async () => {
      const checker = new SchemaDriftChecker();
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

