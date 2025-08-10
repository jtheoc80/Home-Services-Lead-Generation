#!/usr/bin/env node
/**
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
    process.exit(1);
  });
}

export default StackHealthMonitor;