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
      /['"`]eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*service_role[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*['"`]/g,
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
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { QBPlatformAuditor };