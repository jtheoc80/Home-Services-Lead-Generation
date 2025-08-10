#!/usr/bin/env node

/**

 * Stack Health Monitor Script
 * 
 * This script monitors the health of the application stack by checking:
 * - Environment variables configuration
 * - Next.js build capability
 * - Supabase connectivity
 * - API health endpoints
 * 
 * Exit codes:
 * 0 - All checks passed
 * 1 - Environment configuration issues
 * 2 - Build failures
 * 3 - Supabase connectivity issues
 * 4 - Health endpoint issues
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

// Health check configuration
const REQUIRED_ENV_VARS = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY'
];

const FRONTEND_DIR = 'frontend';
const HEALTH_CHECK_TIMEOUT = 30000; // 30 seconds

/**
 * Execute shell command safely
 */
function execCommand(command, options = {}) {
  try {
    const result = execSync(command, { 
      encoding: 'utf8', 
      stdio: 'pipe',
      ...options 
    });
    return { success: true, output: result.trim() };
  } catch (error) {
    const stdout = error.stdout || '';
    const stderr = error.stderr || '';
    const combined = `${stdout}\n${stderr}`.trim();
    return { 
      success: false, 
      output: combined || error.message,
      code: error.status 
    };
  }
}

/**
 * Check for required environment variables
 */
function checkEnvironmentVariables() {
  console.log('🔍 Checking environment variables...');
  
  const issues = [];
  const envFiles = [
    path.join(FRONTEND_DIR, '.env.local'),
    path.join(FRONTEND_DIR, '.env'),
    '.env.local',
    '.env'
  ];
  
  let envFound = false;
  let envVars = {};
  
  // Try to find and read env files
  for (const envFile of envFiles) {
    if (fs.existsSync(envFile)) {
      envFound = true;
      try {
        const content = fs.readFileSync(envFile, 'utf8');
        // Parse env file
        content.split('\n').forEach(line => {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#')) {
            const [key, ...valueParts] = trimmed.split('=');
            if (key && valueParts.length > 0) {
              envVars[key.trim()] = valueParts.join('=').trim();
            }
          }
        });
      } catch (error) {
        console.log(`⚠️  Could not read ${envFile}: ${error.message}`);
      }
    }
  }
  
  // Also check process.env for environment variables
  for (const varName of REQUIRED_ENV_VARS) {
    if (process.env[varName]) {
      envVars[varName] = process.env[varName];
    }
  }
  
  // Check required variables
  for (const varName of REQUIRED_ENV_VARS) {
    if (!envVars[varName]) {
      issues.push(`Missing required environment variable: ${varName}`);
    } else if (envVars[varName].includes('your_') || envVars[varName].includes('placeholder')) {
      issues.push(`Environment variable ${varName} appears to be placeholder value`);
    }
  }
  
  if (!envFound && Object.keys(envVars).length === 0) {
    issues.push('No environment configuration files found (.env.local, .env)');
  }
  
  if (issues.length > 0) {
    console.log('❌ Environment issues found:');
    issues.forEach(issue => console.log(`   - ${issue}`));
    return { success: false, issues };
  }
  
  console.log('✅ Environment variables check passed');
  return { success: true, issues: [] };
}

/**
 * Check if Next.js build works
 */
function checkNextjsBuild() {
  console.log('🔨 Checking Next.js build capability...');
  
  if (!fs.existsSync(FRONTEND_DIR)) {
    const issue = 'Frontend directory not found';
    console.log(`❌ ${issue}`);
    return { success: false, issues: [issue] };
  }
  
  // Check if package.json exists
  const packageJsonPath = path.join(FRONTEND_DIR, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    const issue = 'Frontend package.json not found';
    console.log(`❌ ${issue}`);
    return { success: false, issues: [issue] };
  }
  
  // Check if node_modules exists
  const nodeModulesPath = path.join(FRONTEND_DIR, 'node_modules');
  if (!fs.existsSync(nodeModulesPath)) {
    console.log('📦 Installing dependencies first...');
    const installResult = execCommand(`cd ${FRONTEND_DIR} && npm install`, { 
      cwd: process.cwd(),
      timeout: 120000 
    });
    
    if (!installResult.success) {
      const issue = `npm install failed: ${installResult.output}`;
      console.log(`❌ ${issue}`);
      return { success: false, issues: [issue] };
    }
  }
  
  // Try to run Next.js build
  console.log('🏗️  Attempting Next.js build...');
  const buildResult = execCommand(`cd ${FRONTEND_DIR} && npm run build`, {
    cwd: process.cwd(),
    timeout: 180000 // 3 minutes timeout for build
  });
  
  if (!buildResult.success) {
    const issue = `Next.js build failed: ${buildResult.output}`;
    console.log(`❌ ${issue}`);
    return { success: false, issues: [issue] };
  }
  
  console.log('✅ Next.js build check passed');
  return { success: true, issues: [] };
}

/**
 * Check Supabase configuration
 */
function checkSupabaseConfig() {
  console.log('🔗 Checking Supabase configuration...');
  
  const issues = [];
  
  // Check if Supabase client can be initialized
  const supabaseLibPath = path.join(FRONTEND_DIR, 'lib');
  if (fs.existsSync(supabaseLibPath)) {
    const files = fs.readdirSync(supabaseLibPath);
    const supabaseFiles = files.filter(file => 
      file.toLowerCase().includes('supabase') && 
      (file.endsWith('.js') || file.endsWith('.ts'))
    );
    
    if (supabaseFiles.length === 0) {
      issues.push('No Supabase client configuration file found in lib/');
    } else {
      // Check if the Supabase client file has proper structure
      for (const file of supabaseFiles) {
        try {
          const content = fs.readFileSync(path.join(supabaseLibPath, file), 'utf8');
          if (!content.includes('createClient') && !content.includes('@supabase/supabase-js')) {
            issues.push(`Supabase client file ${file} may not be properly configured`);
          }
        } catch (error) {
          issues.push(`Could not read Supabase client file ${file}: ${error.message}`);
        }
      }
    }
  } else {
    issues.push('lib/ directory not found - Supabase client may not be configured');
  }
  
  if (issues.length > 0) {
    console.log('❌ Supabase configuration issues found:');
    issues.forEach(issue => console.log(`   - ${issue}`));
    return { success: false, issues };
  }
  
  console.log('✅ Supabase configuration check passed');
  return { success: true, issues: [] };
}

/**
 * Check for health endpoint
 */
function checkHealthEndpoint() {
  console.log('🏥 Checking health endpoint...');
  
  const healthEndpoints = [
    path.join(FRONTEND_DIR, 'pages', 'api', 'health.js'),
    path.join(FRONTEND_DIR, 'pages', 'api', 'health.ts'),
    path.join(FRONTEND_DIR, 'app', 'api', 'health', 'route.js'),
    path.join(FRONTEND_DIR, 'app', 'api', 'health', 'route.ts')
  ];
  
  const healthEndpointExists = healthEndpoints.some(endpoint => fs.existsSync(endpoint));
  
  if (!healthEndpointExists) {
    const issue = 'Health endpoint not found (pages/api/health.js|ts or app/api/health/route.js|ts)';
    console.log(`❌ ${issue}`);
    return { success: false, issues: [issue] };
  }
  
  console.log('✅ Health endpoint check passed');
  return { success: true, issues: [] };
}

/**
 * Generate fix instruction based on detected issues
 */
function generateFixInstruction(results) {
  const allIssues = results.flatMap(result => result.issues);
  
  if (allIssues.length === 0) {
    return null;
  }
  
  let instruction = 'Fix detected stack issues: ';
  const fixes = [];
  
  // Environment variable issues
  if (allIssues.some(issue => issue.includes('NEXT_PUBLIC_SUPABASE'))) {
    fixes.push('ensure NEXT_PUBLIC_SUPABASE_URL/ANON_KEY are properly configured and read only on client');
  }
  
  // Build issues
  if (allIssues.some(issue => issue.includes('build failed'))) {
    fixes.push('fix Next.js build errors');
    fixes.push('move Supabase init out of build-time');
  }
  
  // Supabase config issues
  if (allIssues.some(issue => issue.includes('Supabase'))) {
    fixes.push('fix Supabase client configuration');
  }
  
  // Health endpoint issues
  if (allIssues.some(issue => issue.includes('Health endpoint'))) {
    fixes.push('add health route at /api/health');
  }
  
  if (fixes.length === 0) {
    fixes.push('resolve configuration and build issues');
  }
  
  instruction += fixes.join('; ');
  return instruction;
}

/**
 * Main health check execution
 */
async function main() {
  console.log('🏥 Stack Health Monitor starting...');
  console.log('=' .repeat(50));
  
  const results = [];
  let exitCode = 0;
  
  try {
    // Run all health checks
    const envCheck = checkEnvironmentVariables();
    results.push(envCheck);
    
    const buildCheck = checkNextjsBuild();
    results.push(buildCheck);
    
    const supabaseCheck = checkSupabaseConfig();
    results.push(supabaseCheck);
    
    const healthCheck = checkHealthEndpoint();
    results.push(healthCheck);
    
    // Determine exit code based on issues
    if (!envCheck.success) exitCode = 1;
    else if (!buildCheck.success) exitCode = 2;
    else if (!supabaseCheck.success) exitCode = 3;
    else if (!healthCheck.success) exitCode = 4;
    
    console.log('=' .repeat(50));
    
    if (exitCode === 0) {
      console.log('✅ All health checks passed!');
    } else {
      console.log('❌ Health check failures detected');
      
      // Generate fix instruction for AI Auto PR
      const fixInstruction = generateFixInstruction(results);
      if (fixInstruction) {
        console.log('🤖 Suggested fix instruction:');
        console.log(`   ${fixInstruction}`);
        
        // Output instruction in a format that can be captured by the workflow
        console.log('---FIX-INSTRUCTION---');
        console.log(fixInstruction);
        console.log('---END-FIX-INSTRUCTION---');
      }
    }
    
  } catch (error) {
    console.error('❌ Health check script failed:', error.message);
    exitCode = 99;
  }
  
  process.exit(exitCode);
}

// Run the health check
main();
=======
 * Stack Health Monitoring Script
 * 
 * Comprehensive health check for Home Services Lead Generation platform
 * Monitors Vercel, Railway, and Supabase infrastructure
 */

import https from 'https';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Monitors the health of the Home Services Lead Generation platform stack,
 * including Vercel, Railway, and Supabase infrastructure.
 *
 * Key methods:
 * - {@link makeRequest}: Makes HTTP/HTTPS requests with timeout and logging.
 * - {@link checkVercel}: Checks the health of Vercel deployments.
 * - {@link checkRailway}: Checks the health of Railway services.
 * - {@link checkSupabase}: Checks the health of Supabase services.
 * - {@link log}: Logs messages with different levels and timestamps.
 *
 * @class
 * @param {Object} [options] - Configuration options.
 * @param {boolean} [options.verbose=false] - Enable verbose logging.
 * @param {boolean} [options.quick=false] - Enable quick health checks.
 * @param {string|null} [options.platform=null] - Platform to target.
 * @param {number} [options.timeout=10000] - Request timeout in milliseconds.
 *
 * @example
 * // Basic usage
 * const monitor = new StackHealthMonitor({ verbose: true, timeout: 5000 });
 * await monitor.checkVercel();
 * await monitor.checkRailway();
 * await monitor.checkSupabase();
 * console.log(monitor.results);
 */
class StackHealthMonitor {
  constructor(options = {}) {
    this.verbose = options.verbose || false;
    this.quick = options.quick || false;
    this.platform = options.platform || null;
    this.timeout = options.timeout || 10000;
    this.results = {};
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = {
      'info': '✅',
      'warn': '⚠️ ',
      'error': '❌',
      'debug': '🔍'
    }[level] || 'ℹ️ ';

    if (level === 'debug' && !this.verbose) return;
    
    console.log(`${prefix} [${timestamp}] ${message}`);
  }

  async makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
      const urlObj = new URL(url);
      const protocol = urlObj.protocol === 'https:' ? https : http;
      
      const reqOptions = {
        hostname: urlObj.hostname,
        port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
        path: urlObj.pathname + urlObj.search,
        method: options.method || 'GET',
        headers: {
          'User-Agent': 'StackHealthMonitor/1.0',
          ...options.headers
        },
        timeout: this.timeout
      };

      const req = protocol.request(reqOptions, (res) => {


/**
 * Stack Health Monitoring Script
 * 
 * Checks the health of Vercel, Railway, and Supabase services
 * and generates a JSON report with status, timings, and error messages.
 * 
 * Environment Variables:
 * - VERCEL_TOKEN: Vercel API token
 * - RAILWAY_TOKEN: Railway API token
 * - SUPABASE_URL: Supabase project URL
 * - SUPABASE_SERVICE_ROLE: Supabase service role key
 * - FRONTEND_URL: Frontend URL (fallback for Vercel check)
 * - RAILWAY_SERVICE_ID: Railway service ID (optional)
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFile } from 'fs/promises';
import https from 'https';
import http from 'http';
import { URL } from 'url';

const execAsync = promisify(exec);

class StackHealthChecker {
  constructor() {
    this.results = {
      timestamp: new Date().toISOString(),
      checks: {},
      summary: {
        total: 0,
        passed: 0,
        failed: 0
      }
    };
  }

  /**
   * Make HTTP/HTTPS request
   */
  async makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
      const urlObj = new URL(url);
      const isHttps = urlObj.protocol === 'https:';
      const client = isHttps ? https : http;
      
      const requestOptions = {
        hostname: urlObj.hostname,
        port: urlObj.port || (isHttps ? 443 : 80),
        path: urlObj.pathname + urlObj.search,
        method: options.method || 'GET',
        headers: options.headers || {},
        timeout: options.timeout || 10000
      };

      const req = client.request(requestOptions, (res) => {

        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,

            body: data,
            responseTime: Date.now() - startTime
          });
        });
      });

      const startTime = Date.now();
      
      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error(`Request timeout (${this.timeout}ms)`));
      });
      

            data: data
          });
        });
      });

      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });


      if (options.body) {
        req.write(options.body);
      }
      
      req.end();
    });
  }


  async checkVercel() {
    this.log('Checking Vercel deployment...', 'debug');
    
    const checks = {
      deployment: { status: 'unknown', details: null },
      health: { status: 'unknown', details: null },
      build: { status: 'unknown', details: null }
    };

    try {
      // Try to detect Vercel deployment URL from environment or config
      const vercelUrl = process.env.VERCEL_URL || 
                       process.env.NEXT_PUBLIC_VERCEL_URL ||
                       this.detectVercelUrl();

      if (!vercelUrl) {
        checks.deployment.status = 'warning';
        checks.deployment.details = 'No Vercel URL configured';
        this.log('No Vercel URL found in environment', 'warn');
        return checks;
      }

      // Check health endpoint
      try {
        const healthUrl = `https://${vercelUrl}/api/health`;
        const response = await this.makeRequest(healthUrl);
        
        if (response.statusCode === 200) {
          checks.health.status = 'healthy';
          checks.health.details = `Response time: ${response.responseTime}ms`;
          this.log(`Vercel health check passed (${response.responseTime}ms)`);
        } else {
          checks.health.status = 'unhealthy';
          checks.health.details = `HTTP ${response.statusCode}`;
          this.log(`Vercel health check failed: HTTP ${response.statusCode}`, 'error');
        }
      } catch (error) {
        checks.health.status = 'error';
        checks.health.details = error.message;
        this.log(`Vercel health check error: ${error.message}`, 'error');
      }

      // Check if deployment is accessible
      try {
        const response = await this.makeRequest(`https://${vercelUrl}`);
        checks.deployment.status = response.statusCode === 200 ? 'healthy' : 'unhealthy';
        checks.deployment.details = `HTTP ${response.statusCode}`;
      } catch (error) {
        checks.deployment.status = 'error';
        checks.deployment.details = error.message;
      }

    } catch (error) {
      this.log(`Vercel check failed: ${error.message}`, 'error');
      checks.deployment.status = 'error';
      checks.deployment.details = error.message;
    }

    return checks;
  }

  async checkRailway() {
    this.log('Checking Railway deployment...', 'debug');
    
    const checks = {
      deployment: { status: 'unknown', details: null },
      health: { status: 'unknown', details: null },
      port: { status: 'unknown', details: null }
    };

    try {
      // Try to detect Railway deployment URL
      const railwayUrl = process.env.RAILWAY_STATIC_URL ||
                        process.env.RAILWAY_URL ||
                        this.detectRailwayUrl();

      if (!railwayUrl) {
        checks.deployment.status = 'warning';
        checks.deployment.details = 'No Railway URL configured';
        this.log('No Railway URL found in environment', 'warn');
        return checks;
      }

      // Check health endpoint
      try {
        const healthUrl = `${railwayUrl}/api/health`;
        const response = await this.makeRequest(healthUrl);
        
        if (response.statusCode === 200) {
          checks.health.status = 'healthy';
          checks.health.details = `Response time: ${response.responseTime}ms`;
          this.log(`Railway health check passed (${response.responseTime}ms)`);
          
          // Parse health response for additional details
          try {
            const healthData = JSON.parse(response.body);
            if (healthData.uptime) {
              checks.port.status = 'healthy';
              checks.port.details = `Uptime: ${Math.floor(healthData.uptime)}s`;
            }
          } catch (e) {
            // Ignore JSON parse errors
          }
        } else {
          checks.health.status = 'unhealthy';
          checks.health.details = `HTTP ${response.statusCode}`;
          this.log(`Railway health check failed: HTTP ${response.statusCode}`, 'error');
        }
      } catch (error) {
        checks.health.status = 'error';
        checks.health.details = error.message;
        this.log(`Railway health check error: ${error.message}`, 'error');
      }

      // Check main deployment
      try {
        const response = await this.makeRequest(railwayUrl);
        checks.deployment.status = response.statusCode === 200 ? 'healthy' : 'unhealthy';
        checks.deployment.details = `HTTP ${response.statusCode}`;
      } catch (error) {
        checks.deployment.status = 'error';
        checks.deployment.details = error.message;
      }

    } catch (error) {
      this.log(`Railway check failed: ${error.message}`, 'error');
      checks.deployment.status = 'error';
      checks.deployment.details = error.message;
    }

    return checks;
  }

  async checkSupabase() {
    this.log('Checking Supabase connection...', 'debug');
    
    const checks = {
      connectivity: { status: 'unknown', details: null },
      auth: { status: 'unknown', details: null },
      database: { status: 'unknown', details: null }
    };

    try {
      const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
      const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

      if (!supabaseUrl) {
        checks.connectivity.status = 'error';
        checks.connectivity.details = 'SUPABASE_URL not configured';
        this.log('SUPABASE_URL not found in environment', 'error');
        return checks;
      }

      if (!supabaseKey) {
        checks.connectivity.status = 'warning';
        checks.connectivity.details = 'SUPABASE_ANON_KEY not configured';
        this.log('SUPABASE_ANON_KEY not found in environment', 'warn');
      }

      // Test basic connectivity
      try {
        const response = await this.makeRequest(`${supabaseUrl}/rest/v1/`, {
          headers: supabaseKey ? { 'apikey': supabaseKey } : {}
        });

        if (response.statusCode === 200) {
          checks.connectivity.status = 'healthy';
          checks.connectivity.details = `Response time: ${response.responseTime}ms`;
          this.log(`Supabase REST API accessible (${response.responseTime}ms)`);
        } else if (response.statusCode === 401) {
          checks.connectivity.status = 'warning';
          checks.connectivity.details = 'Authentication required (API key may be missing)';
          this.log('Supabase API key authentication issue', 'warn');
        } else {
          checks.connectivity.status = 'unhealthy';
          checks.connectivity.details = `HTTP ${response.statusCode}`;
          this.log(`Supabase connectivity issue: HTTP ${response.statusCode}`, 'error');
        }
      } catch (error) {
        checks.connectivity.status = 'error';
        checks.connectivity.details = error.message;
        this.log(`Supabase connectivity error: ${error.message}`, 'error');
      }

      // Test auth endpoint
      if (supabaseKey) {
        try {
          const authResponse = await this.makeRequest(`${supabaseUrl}/auth/v1/settings`, {
            headers: { 'apikey': supabaseKey }
          });

          if (authResponse.statusCode === 200) {
            checks.auth.status = 'healthy';
            checks.auth.details = 'Auth endpoint accessible';
            this.log('Supabase auth endpoint accessible');
          } else {
            checks.auth.status = 'unhealthy';
            checks.auth.details = `HTTP ${authResponse.statusCode}`;
          }
        } catch (error) {
          checks.auth.status = 'error';
          checks.auth.details = error.message;
        }
      }

      // Basic database connectivity (try to hit a simple endpoint)
      if (supabaseKey) {
        try {
          // Replace with a valid table name that exists in your Supabase project, e.g., 'users'
          const tableName = 'users'; // Change this if needed
          const dbResponse = await this.makeRequest(`${supabaseUrl}/rest/v1/${tableName}?select=*&limit=1`, {
            headers: { 'apikey': supabaseKey }
          });

          checks.database.status = dbResponse.statusCode === 200 ? 'healthy' : 'warning';
          checks.database.details = `HTTP ${dbResponse.statusCode}`;
        } catch (error) {
          checks.database.status = 'warning';
          checks.database.details = 'Cannot verify database (may require RLS policies)';
        }
      }

    } catch (error) {
      this.log(`Supabase check failed: ${error.message}`, 'error');
      checks.connectivity.status = 'error';
      checks.connectivity.details = error.message;
    }

    return checks;
  }

  detectVercelUrl() {
    // Try to read from vercel.json or package.json
    try {
      const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
      if (packageJson.homepage && packageJson.homepage.includes('vercel.app')) {
        return new URL(packageJson.homepage).hostname;
      }
    } catch (e) {
      // Ignore errors
    }
    return null;
  }

  detectRailwayUrl() {
    // Try to detect from common Railway environment patterns
    const railwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN;
    if (railwayDomain) {
      return `https://${railwayDomain}`;
    }
    return null;
  }

  formatResults() {
    const platforms = Object.keys(this.results);
    let output = '\n📊 Stack Health Report\n';
    output += '='.repeat(50) + '\n\n';

    platforms.forEach(platform => {
      const platformResults = this.results[platform];
      const platformName = platform.charAt(0).toUpperCase() + platform.slice(1);
      
      output += `🔹 ${platformName}\n`;
      
      Object.entries(platformResults).forEach(([check, result]) => {
        const icon = {
          'healthy': '✅',
          'unhealthy': '❌',
          'warning': '⚠️',
          'error': '💥',
          'unknown': '❓'
        }[result.status] || '❓';
        
        output += `   ${icon} ${check}: ${result.status}`;
        if (result.details) {
          output += ` (${result.details})`;
        }
        output += '\n';
      });
      output += '\n';
    });

    // Summary
    const allChecks = platforms.flatMap(p => Object.values(this.results[p]));
    const healthy = allChecks.filter(c => c.status === 'healthy').length;
    const total = allChecks.length;
    const healthPercent = total > 0 ? Math.round((healthy / total) * 100) : 0;

    output += `📈 Overall Health: ${healthy}/${total} checks passed (${healthPercent}%)\n`;
    
    if (healthPercent === 100) {
      output += '🎉 All systems operational!\n';
    } else if (healthPercent >= 75) {
      output += '✅ Systems mostly healthy\n';
    } else if (healthPercent >= 50) {
      output += '⚠️  Some issues detected\n';
    } else {
      output += '🚨 Critical issues detected\n';
    }

    return output;
  }

  async run() {
    this.log('Starting stack health check...');
    
    const platforms = this.platform ? [this.platform] : ['vercel', 'railway', 'supabase'];
    
    for (const platform of platforms) {
      try {
        switch (platform) {
          case 'vercel':
            this.results.vercel = await this.checkVercel();
            break;
          case 'railway':
            this.results.railway = await this.checkRailway();
            break;
          case 'supabase':
            this.results.supabase = await this.checkSupabase();
            break;
          default:
            this.log(`Unknown platform: ${platform}`, 'error');
        }
      } catch (error) {
        this.log(`Failed to check ${platform}: ${error.message}`, 'error');
        this.results[platform] = {
          error: { status: 'error', details: error.message }
        };
      }
    }

    console.log(this.formatResults());
    
    // Exit with error code if any critical issues
    const hasErrors = Object.values(this.results).some(platform =>
      Object.values(platform).some(check => check.status === 'error')
    );
    
    if (hasErrors) {
      this.log('Health check completed with errors', 'error');
      process.exit(1);
    } else {
      this.log('Health check completed successfully');

  /**
   * Check Vercel deployment status
   */
  async checkVercel() {
    const startTime = Date.now();
    const checkName = 'vercel';
    
    try {
      this.results.checks[checkName] = {
        name: 'Vercel Deployment',
        status: 'running',
        startTime: new Date().toISOString()
      };

      const vercelToken = process.env.VERCEL_TOKEN;
      const frontendUrl = process.env.FRONTEND_URL;

      if (!vercelToken && !frontendUrl) {
        throw new Error('Neither VERCEL_TOKEN nor FRONTEND_URL provided');
      }

      let healthUrl;

      // Try to get latest deployment from Vercel API
      if (vercelToken) {
        try {
          const { stdout } = await execAsync(
            `vercel ls --json`,
            { env: { ...process.env, VERCEL_TOKEN: vercelToken } }
          );
          const deployments = JSON.parse(stdout);
          
          const readyDeployment = deployments.find(d => d.state === 'READY');
          if (readyDeployment) {
            healthUrl = `https://${readyDeployment.url}/api/health`;
          }
        } catch (vercelError) {
          console.warn('Failed to get Vercel deployment, falling back to FRONTEND_URL');
          if (frontendUrl) {
            healthUrl = `${frontendUrl}/api/health`;
          } else {
            throw new Error('Failed to get Vercel deployment and no FRONTEND_URL fallback');
          }
        }
      } else {
        healthUrl = `${frontendUrl}/api/health`;
      }

      if (!healthUrl) {
        throw new Error('No health URL determined');
      }

      // Check health endpoint
      const response = await this.makeRequest(healthUrl);
      
      if (response.statusCode !== 200) {
        throw new Error(`Health check failed with status ${response.statusCode}`);
      }

      let healthData;
      try {
        healthData = JSON.parse(response.data);
      } catch {
        healthData = { status: 'unknown', response: response.data };
      }

      const duration = Date.now() - startTime;
      
      this.results.checks[checkName] = {
        name: 'Vercel Deployment',
        status: 'passed',
        url: healthUrl,
        duration: duration,
        response: healthData,
        endTime: new Date().toISOString()
      };

    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.checks[checkName] = {
        name: 'Vercel Deployment',
        status: 'failed',
        error: error.message,
        duration: duration,
        endTime: new Date().toISOString()
      };
    }
  }

  /**
   * Check Railway service status
   */
  async checkRailway() {
    const startTime = Date.now();
    const checkName = 'railway';
    
    try {
      this.results.checks[checkName] = {
        name: 'Railway Service',
        status: 'running',
        startTime: new Date().toISOString()
      };

      const railwayToken = process.env.RAILWAY_TOKEN;
      const railwayServiceId = process.env.RAILWAY_SERVICE_ID;

      if (!railwayToken) {
        throw new Error('RAILWAY_TOKEN not provided');
      }

      let serviceStatus;

      // If service ID provided, use GraphQL API
      if (railwayServiceId) {
        const graphqlQuery = {
          query: `
            query GetService($serviceId: String!) {
              service(id: $serviceId) {
                id
                name
                status
                createdAt
                updatedAt
              }
            }
          `,
          variables: {
            serviceId: railwayServiceId
          }
        };

        const response = await this.makeRequest('https://backboard.railway.app/graphql/v2', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${railwayToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(graphqlQuery)
        });

        if (response.statusCode !== 200) {
          throw new Error(`Railway GraphQL API failed with status ${response.statusCode}`);
        }

        const graphqlResult = JSON.parse(response.data);
        if (graphqlResult.errors) {
          throw new Error(`Railway GraphQL errors: ${JSON.stringify(graphqlResult.errors)}`);
        }

        serviceStatus = graphqlResult.data.service;
      } else {
        // Fallback: try to determine Railway public URL and check health
        // Note: This is a simplified approach since we don't have the public URL
        serviceStatus = { status: 'unknown', note: 'No RAILWAY_SERVICE_ID provided, cannot check via GraphQL' };
      }

      const duration = Date.now() - startTime;
      
      this.results.checks[checkName] = {
        name: 'Railway Service',
        status: 'passed',
        duration: duration,
        serviceId: railwayServiceId,
        serviceStatus: serviceStatus,
        endTime: new Date().toISOString()
      };

    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.checks[checkName] = {
        name: 'Railway Service',
        status: 'failed',
        error: error.message,
        duration: duration,
        endTime: new Date().toISOString()
      };
    }
  }

  /**
   * Check Supabase health via leads table
   */
  async checkSupabase() {
    const startTime = Date.now();
    const checkName = 'supabase';
    
    try {
      this.results.checks[checkName] = {
        name: 'Supabase Database',
        status: 'running',
        startTime: new Date().toISOString()
      };

      const supabaseUrl = process.env.SUPABASE_URL;
      const supabaseServiceRole = process.env.SUPABASE_SERVICE_ROLE;

      if (!supabaseUrl || !supabaseServiceRole) {
        throw new Error('SUPABASE_URL or SUPABASE_SERVICE_ROLE not provided');
      }

      // Insert a test record
      const insertPayload = {
        source: 'monitor',
        name: 'Ping'
      };

      const insertResponse = await this.makeRequest(`${supabaseUrl}/rest/v1/leads`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseServiceRole}`,
          'Content-Type': 'application/json',
          'apikey': supabaseServiceRole,
          'Prefer': 'return=representation'
        },
        body: JSON.stringify(insertPayload)
      });

      if (insertResponse.statusCode !== 201) {
        throw new Error(`Failed to insert test record: ${insertResponse.statusCode} - ${insertResponse.data}`);
      }

      // Select latest record to verify read functionality
      const selectResponse = await this.makeRequest(`${supabaseUrl}/rest/v1/leads?source=eq.monitor&limit=1&order=created_at.desc`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${supabaseServiceRole}`,
          'apikey': supabaseServiceRole
        }
      // First, check if 'created_at' column exists in the 'leads' table
      const schemaResponse = await this.makeRequest(`${supabaseUrl}/rest/v1/leads?select=*&limit=1`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${supabaseServiceRole}`,
          'apikey': supabaseServiceRole
        }
      });
      let orderClause = '';
      if (schemaResponse.statusCode === 200) {
        try {
          const schemaData = JSON.parse(schemaResponse.data);
          if (Array.isArray(schemaData) && schemaData.length > 0 && 'created_at' in schemaData[0]) {
            orderClause = '&order=created_at.desc';
          } else {
            // Document assumption and fallback
            // 'created_at' column not found; ordering omitted
          }
        } catch (e) {
          // If parsing fails, omit ordering
        }
      }
      const selectResponse = await this.makeRequest(`${supabaseUrl}/rest/v1/leads?source=eq.monitor&limit=1${orderClause}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${supabaseServiceRole}`,
          'apikey': supabaseServiceRole
        }
      });

      if (selectResponse.statusCode !== 200) {
        throw new Error(`Failed to select test record: ${selectResponse.statusCode}`);
      }

      const selectData = JSON.parse(selectResponse.data);
      
      const duration = Date.now() - startTime;
      
      this.results.checks[checkName] = {
        name: 'Supabase Database',
        status: 'passed',
        duration: duration,
        insertedRecord: JSON.parse(insertResponse.data),
        latestRecords: selectData.length,
        endTime: new Date().toISOString()
      };

    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.checks[checkName] = {
        name: 'Supabase Database',
        status: 'failed',
        error: error.message,
        duration: duration,
        endTime: new Date().toISOString()
      };
    }
  }

  /**
   * Generate summary statistics
   */
  generateSummary() {
    const checks = Object.values(this.results.checks);
    this.results.summary = {
      total: checks.length,
      passed: checks.filter(c => c.status === 'passed').length,
      failed: checks.filter(c => c.status === 'failed').length,
      totalDuration: checks.reduce((sum, c) => sum + (c.duration || 0), 0)
    };
  }

  /**
   * Generate Markdown summary for GitHub Actions
   */
  generateMarkdownSummary() {
    const { summary, checks } = this.results;
    const emoji = summary.failed === 0 ? '✅' : '❌';
    
    let markdown = `# ${emoji} Stack Health Check\n\n`;
    markdown += `**Summary:** ${summary.passed}/${summary.total} checks passed in ${summary.totalDuration}ms\n\n`;
    
    markdown += `| Service | Status | Duration | Details |\n`;
    markdown += `|---------|--------|----------|----------|\n`;
    
    Object.values(checks).forEach(check => {
      const statusEmoji = check.status === 'passed' ? '✅' : '❌';
      const duration = check.duration ? `${check.duration}ms` : 'N/A';
      const details = check.error || check.url || 'OK';
      markdown += `| ${check.name} | ${statusEmoji} ${check.status} | ${duration} | ${details} |\n`;
    });

    return markdown;
  }

  /**
   * Run all health checks
   */
  async runAllChecks() {
    console.log('🔍 Starting stack health checks...\n');

    // Run checks in parallel
    await Promise.all([
      this.checkVercel(),
      this.checkRailway(),
      this.checkSupabase()
    ]);

    this.generateSummary();

    // Write JSON results
    await writeFile('stack-health.json', JSON.stringify(this.results, null, 2));
    console.log('📄 Results written to stack-health.json\n');

    // Generate and output Markdown summary
    const markdownSummary = this.generateMarkdownSummary();
    console.log(markdownSummary);

    // Exit with error code if any checks failed
    if (this.results.summary.failed > 0) {
      console.error(`\n❌ ${this.results.summary.failed} check(s) failed`);
      process.exit(1);
    } else {
      console.log(`\n✅ All ${this.results.summary.total} checks passed`);

      process.exit(0);
    }
  }
}

    
// CLI handling
if (
  path.resolve(fileURLToPath(import.meta.url)) === path.resolve(process.argv[1])
) {
  const args = process.argv.slice(2);
  const options = {};

  // Parse command line arguments
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--verbose':
      case '-v':
        options.verbose = true;
        break;
      case '--quick':
      case '-q':
        options.quick = true;
        break;
      case '--platform':
      case '-p':
        options.platform = args[++i];
        break;
      case '--timeout':
      case '-t':
        options.timeout = parseInt(args[++i]) || 10000;
        break;
      case '--help':
      case '-h':
        console.log(`
Stack Health Monitor - Home Services Lead Generation Platform

Usage: node stack-health.js [options]

Options:
  --verbose, -v          Show detailed output
  --quick, -q           Run quick checks only
  --platform, -p <name>  Check specific platform (vercel|railway|supabase)
  --timeout, -t <ms>     Request timeout in milliseconds (default: 10000)
  --help, -h            Show this help

Examples:
  node stack-health.js                    # Check all platforms
  node stack-health.js --platform vercel # Check only Vercel
  node stack-health.js --verbose          # Detailed output
  node stack-health.js --quick            # Quick checks only
        `);
        process.exit(0);
        break;
    }
  }

  const monitor = new StackHealthMonitor(options);
  monitor.run().catch(error => {
    console.error('❌ Health check failed:', error.message);

// Run if called directly
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const checker = new StackHealthChecker();
  checker.runAllChecks().catch(error => {
    console.error('💥 Fatal error:', error.message);

    process.exit(1);
  });
}

export default StackHealthMonitor;

export default StackHealthChecker;


