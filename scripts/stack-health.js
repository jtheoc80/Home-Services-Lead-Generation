#!/usr/bin/env node

/**
 * Stack Health Monitor

 * 
 * Node 20 compatible script with no external dependencies
 * Checks health of Vercel, Railway, and Supabase infrastructure
 * 
 * Environment Variables:
 * - VERCEL_TOKEN: Vercel API token
 * - RAILWAY_TOKEN: Railway API token  
 * - SUPABASE_URL: Supabase project URL
 * - SUPABASE_SERVICE_ROLE: Supabase service role key
 * - FRONTEND_URL: Frontend URL (optional fallback for Vercel)
 * - RAILWAY_SERVICE_ID: Railway service ID (optional for GraphQL queries)
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFileSync } from 'fs';
import https from 'https';
import http from 'http';
import { URL, fileURLToPath } from 'url';

const execAsync = promisify(exec);

class StackHealthChecker {
  constructor() {
    this.results = {
      timestamp: new Date().toISOString(),
      vercel: { ok: false, message: '', latencyMs: 0 },
      railway: { ok: false, message: '', latencyMs: 0 },
      supabase: { ok: false, message: '', latencyMs: 0 }
    };
  }

  /**
   * Make HTTP/HTTPS request with built-in modules only
   */
  async makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const urlObj = new URL(url);
      const isHttps = urlObj.protocol === 'https:';
      const client = isHttps ? https : http;
      
      const requestOptions = {
        hostname: urlObj.hostname,
        port: urlObj.port || (isHttps ? 443 : 80),
        path: urlObj.pathname + urlObj.search,
        method: options.method || 'GET',
        headers: options.headers || {},
        timeout: 10000
      };

      const req = client.request(requestOptions, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          const latencyMs = Date.now() - startTime;
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: data,
            latencyMs
          });
        });
      });

      req.on('error', (error) => {
        const latencyMs = Date.now() - startTime;
        reject({ ...error, latencyMs });
      });

      req.on('timeout', () => {
        req.destroy();
        const latencyMs = Date.now() - startTime;
        reject({ message: 'Request timeout', latencyMs });
      });

      if (options.body) {
        req.write(options.body);
      }
      
      req.end();
    });
  }

  /**
   * Check Vercel deployment health
   */
  async checkVercel() {
    const startTime = Date.now();
    
    try {
      const vercelToken = process.env.VERCEL_TOKEN;
      const frontendUrl = process.env.FRONTEND_URL;

      if (!vercelToken && !frontendUrl) {
        throw new Error('Neither VERCEL_TOKEN nor FRONTEND_URL provided');
      }

      let healthUrl = frontendUrl ? `${frontendUrl}/api/health` : null;

      // Try to get latest READY deployment from Vercel CLI as specified in requirements
      if (vercelToken) {
        try {
          const { stdout } = await execAsync(
            `vercel ls --json --token ${vercelToken}`,
            `vercel ls --json`,
            { timeout: 15000, env: { ...process.env, VERCEL_TOKEN: vercelToken } }
          );
          
          const deployments = JSON.parse(stdout);
          const readyDeployment = deployments.find(d => d.state === 'READY');
          
          if (readyDeployment) {
            healthUrl = `https://${readyDeployment.url}/api/health`;
          } else if (!frontendUrl) {
            throw new Error('No READY deployment found and no FRONTEND_URL fallback');
          }
        } catch (vercelError) {
          // If vercel ls --json fails, try alternative approaches
          if (vercelError.message.includes('unknown or unexpected option')) {
            // Try using Vercel API directly as fallback
            try {
              const response = await this.makeRequest('https://api.vercel.com/v2/deployments', {
                headers: {
                  'Authorization': `Bearer ${vercelToken}`,
                  'Content-Type': 'application/json'
                }
              });

              if (response.statusCode === 200) {
                const data = JSON.parse(response.body);
                const readyDeployment = data.deployments?.find(d => d.state === 'READY');
                
                if (readyDeployment) {
                  healthUrl = `https://${readyDeployment.url}/api/health`;
                } else if (!frontendUrl) {
                  throw new Error('No READY deployment found via API and no FRONTEND_URL fallback');
                }
              } else {
                throw new Error(`Vercel API returned status ${response.statusCode}`);
              }
            } catch (apiError) {
              if (!frontendUrl) {
                throw new Error(`Vercel CLI --json not supported and API failed: ${apiError.message}`);
              }
              // Fall back to FRONTEND_URL
            }
          } else if (!frontendUrl) {
            throw new Error(`Failed to get Vercel deployment: ${vercelError.message}`);
          }
          // Fall back to FRONTEND_URL if available
        }
      }

      if (!healthUrl) {
        throw new Error('No health URL determined');
      }

      // Check health endpoint
      const response = await this.makeRequest(healthUrl);
      
      if (response.statusCode === 200) {
        this.results.vercel = {
          ok: true,
          message: `Health check passed: ${healthUrl}`,
          latencyMs: response.latencyMs
        };
      } else {
        throw new Error(`Health check failed with status ${response.statusCode}`);
      }

    } catch (error) {
      let message = error.message;
      if (error.code === 'ENOTFOUND') {
        message = `Network error: Cannot resolve hostname ${error.hostname}`;
      } else if (error.code === 'ECONNREFUSED') {
        message = `Connection refused: ${error.hostname}:${error.port}`;
      } else if (!message) {
        message = typeof error === 'string' ? error : JSON.stringify(error);
      }
      
      this.results.vercel = {
        ok: false,
        message,
        latencyMs: error.latencyMs || (Date.now() - startTime)
      };
    }
  }

  /**
   * Check Railway service health
   */
  async checkRailway() {
    const startTime = Date.now();
    
    try {
      const railwayToken = process.env.RAILWAY_TOKEN;
      const railwayServiceId = process.env.RAILWAY_SERVICE_ID;

      if (!railwayToken) {
        throw new Error('RAILWAY_TOKEN not provided');
      }

      // If service ID provided, use GraphQL v2 API
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

        const graphqlResult = JSON.parse(response.body);
        if (graphqlResult.errors) {
          throw new Error(`Railway GraphQL errors: ${JSON.stringify(graphqlResult.errors)}`);
        }

        const serviceStatus = graphqlResult.data?.service;
        if (serviceStatus) {
          this.results.railway = {
            ok: true,
            message: `Service status: ${serviceStatus.status || 'unknown'}`,
            latencyMs: response.latencyMs
          };
        } else {
          throw new Error('Service not found or no data returned');
        }
      } else {
        // Fallback: basic GraphQL auth check
        const response = await this.makeRequest('https://backboard.railway.app/graphql/v2', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${railwayToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            query: 'query { me { id name } }'
          })
        });

        if (response.statusCode === 200) {
          const result = JSON.parse(response.body);
          if (result.data?.me) {
            this.results.railway = {
              ok: true,
              message: 'Railway API accessible (no RAILWAY_SERVICE_ID provided)',
              latencyMs: response.latencyMs
            };
          } else {
            throw new Error('Invalid response from Railway API');
          }
        } else {
          throw new Error(`Railway API failed with status ${response.statusCode}`);
        }
      }

    } catch (error) {
      let message = error.message;
      if (error.code === 'ENOTFOUND') {
        message = `Network error: Cannot resolve hostname ${error.hostname}`;
      } else if (error.code === 'ECONNREFUSED') {
        message = `Connection refused: ${error.hostname}:${error.port}`;
      } else if (!message) {
        message = typeof error === 'string' ? error : JSON.stringify(error);
      }
      
      this.results.railway = {
        ok: false,
        message,
        latencyMs: error.latencyMs || (Date.now() - startTime)
      };
    }
  }

  /**
   * Check Supabase health via leads table operations
   */
  async checkSupabase() {
    const startTime = Date.now();
    
    try {
      const supabaseUrl = process.env.SUPABASE_URL;
      const supabaseServiceRole = process.env.SUPABASE_SERVICE_ROLE;

      if (!supabaseUrl || !supabaseServiceRole) {
        throw new Error('SUPABASE_URL or SUPABASE_SERVICE_ROLE not provided');
      }

      // Insert a test record into leads table
      const insertPayload = {
        source: 'stack-health-monitor',
        name: 'Health Check Test',
        email: 'health-check@example.com',
        created_at: new Date().toISOString()
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
        throw new Error(`Failed to insert test record: ${insertResponse.statusCode} - ${insertResponse.body}`);
      }

      // Select latest record to verify read functionality
      const selectResponse = await this.makeRequest(`${supabaseUrl}/rest/v1/leads?source=eq.stack-health-monitor&limit=1&order=created_at.desc`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${supabaseServiceRole}`,
          'apikey': supabaseServiceRole
        }
      });

      if (selectResponse.statusCode !== 200) {
        throw new Error(`Failed to select test record: ${selectResponse.statusCode}`);
      }

      const selectData = JSON.parse(selectResponse.body);
      const totalLatency = insertResponse.latencyMs + selectResponse.latencyMs;
      
      this.results.supabase = {
        ok: true,
        message: `Database operations successful (${selectData.length} records found)`,
        latencyMs: totalLatency
      };

    } catch (error) {
      let message = error.message;
      if (error.code === 'ENOTFOUND') {
        message = `Network error: Cannot resolve hostname ${error.hostname}`;
      } else if (error.code === 'ECONNREFUSED') {
        message = `Connection refused: ${error.hostname}:${error.port}`;
      } else if (!message) {
        message = typeof error === 'string' ? error : JSON.stringify(error);
      }
      
      this.results.supabase = {
        ok: false,
        message,
        latencyMs: error.latencyMs || (Date.now() - startTime)
      };
    }
  }

  /**
   * Generate Markdown summary for stdout
   */
  generateMarkdownSummary() {
    const allOk = this.results.vercel.ok && this.results.railway.ok && this.results.supabase.ok;
    const emoji = allOk ? '✅' : '❌';
    
    let markdown = `# ${emoji} Stack Health Check\n\n`;
    markdown += `**Timestamp:** ${this.results.timestamp}\n\n`;
    
    markdown += `| Service | Status | Latency | Message |\n`;
    markdown += `|---------|--------|---------|----------|\n`;
    
    ['vercel', 'railway', 'supabase'].forEach(service => {
      const result = this.results[service];
      const statusEmoji = result.ok ? '✅' : '❌';
      const status = result.ok ? 'OK' : 'FAILED';
      markdown += `| ${service.charAt(0).toUpperCase() + service.slice(1)} | ${statusEmoji} ${status} | ${result.latencyMs}ms | ${result.message} |\n`;
    });

    const okCount = [this.results.vercel, this.results.railway, this.results.supabase].filter(r => r.ok).length;
    markdown += `\n**Summary:** ${okCount}/3 services healthy\n`;

    return markdown;
  }

  /**
   * Run all health checks
   */
  async runAllChecks() {
    console.log('🔍 Starting stack health checks...\n');

    // Run checks in parallel for better performance
    await Promise.all([
      this.checkVercel(),
      this.checkRailway(), 
      this.checkSupabase()
    ]);

    // Write JSON results
    writeFileSync('stack-health.json', JSON.stringify(this.results, null, 2));

    // Generate and output Markdown summary to stdout
    const markdownSummary = this.generateMarkdownSummary();
    console.log(markdownSummary);

    // Exit with appropriate code
    const allOk = this.results.vercel.ok && this.results.railway.ok && this.results.supabase.ok;
    process.exit(allOk ? 0 : 1);
  }
}

// Run if called directly
if (fileURLToPath(import.meta.url) === process.argv[1]) {
  const checker = new StackHealthChecker();
  checker.runAllChecks().catch(error => {
    console.error('💥 Fatal error:', error.message);
    process.exit(1);
  });
}

export default StackHealthChecker;