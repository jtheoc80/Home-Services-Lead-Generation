#!/usr/bin/env node

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

// Run if called directly
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const checker = new StackHealthChecker();
  checker.runAllChecks().catch(error => {
    console.error('💥 Fatal error:', error.message);
    process.exit(1);
  });
}

export default StackHealthChecker;