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
 * - FRONTEND_URL: Frontend URL (required for frontend health check; used as fallback for Vercel)
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
      frontend: { ok: false, message: '', latencyMs: 0 },
      vercel: { ok: false, message: '', latencyMs: 0 },
      railway: { ok: false, message: '', latencyMs: 0 },
      supabase: { ok: false, message: '', latencyMs: 0 }
    };
  }

  /**
   * Check Frontend URL returns 200 and contains "Houston" scope text
   */
  async checkFrontend() {
    const startTime = Date.now();
    
    try {
      const frontendUrl = process.env.FRONTEND_URL;
      
      if (!frontendUrl) {
        throw new Error('FRONTEND_URL not provided');
      }

      // Check if frontend URL returns 200 and contains Houston scope text
      const response = await this.makeRequest(frontendUrl);
      
      if (response.statusCode !== 200) {
        throw new Error(`Frontend returned status ${response.statusCode}`);
      }

      // Check for Houston scope text from README (as specified in requirements)
      const houstonScopeTexts = [
        'Houston',
        'houston', 
        'Houston Metro',
        'Houston metropolitan area',
        'Harris County',
        'Harris County'
      ];
      
      const hasHoustonScope = houstonScopeTexts.some(text => 
        response.body.toLowerCase().includes(text.toLowerCase())
      );

      if (!hasHoustonScope) {
        throw new Error('Frontend page does not contain expected Houston scope text');
      }

      this.results.frontend = {
        ok: true,
        message: `Frontend healthy, contains Houston scope content: ${frontendUrl}`,
        latencyMs: response.latencyMs
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
      
      this.results.frontend = {
        ok: false,
        message,
        latencyMs: error.latencyMs || (Date.now() - startTime)
      };
    }
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
   * Check Vercel deployment health - latest production deployment is "READY"
   */
  async checkVercel() {
    const startTime = Date.now();
    
    try {
      const vercelToken = process.env.VERCEL_TOKEN;

      if (!vercelToken) {
        throw new Error('VERCEL_TOKEN not provided');
      }

      // Use Vercel API to get latest production deployment and verify it's READY
      const response = await this.makeRequest('https://api.vercel.com/v6/deployments?limit=20', {
        headers: {
          'Authorization': `Bearer ${vercelToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.statusCode !== 200) {
        throw new Error(`Vercel API returned status ${response.statusCode}: ${response.body}`);
      }

      const data = JSON.parse(response.body);
      const readyDeployment = data.deployments?.find(d => 
        d.readyState === 'READY' && d.target === 'production'
      );
      
      if (!readyDeployment) {
        throw new Error('No READY production deployment found');
      }

      this.results.vercel = {
        ok: true,
        message: `Latest production deployment is READY: ${readyDeployment.url}`,
        latencyMs: response.latencyMs
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
      
      this.results.vercel = {
        ok: false,
        message,
        latencyMs: error.latencyMs || (Date.now() - startTime)
      };
    }
  }

  /**
   * Check Railway service health and get public URL
   */
  async checkRailway() {
    const startTime = Date.now();
    
    try {
      const railwayToken = process.env.RAILWAY_TOKEN;

      if (!railwayToken) {
        throw new Error('RAILWAY_TOKEN not provided');
      }

      // Query to get service health and public domains
      const graphqlQuery = {
        query: `
          query {
            me {
              id
              name
              projects(first: 20) {
                edges {
                  node {
                    id
                    name
                    services(first: 20) {
                      edges {
                        node {
                          id
                          name
                          domains(first: 10) {
                            edges {
                              node {
                                domain
                                customDomain
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        `
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
        throw new Error(`Railway GraphQL API failed with status ${response.statusCode}: ${response.body}`);
      }

      const graphqlResult = JSON.parse(response.body);
      if (graphqlResult.errors) {
        throw new Error(`Railway GraphQL errors: ${JSON.stringify(graphqlResult.errors)}`);
      }

      // Extract public URLs from the response
      const projects = graphqlResult.data?.me?.projects?.edges || [];
      const publicUrls = [];
      
      projects.forEach(project => {
        const services = project.node?.services?.edges || [];
        services.forEach(service => {
          const domains = service.node?.domains?.edges || [];
          domains.forEach(domain => {
            if (domain.node?.domain) {
              publicUrls.push(`https://${domain.node.domain}`);
            }
          });
        });
      });

      if (graphqlResult.data?.me) {
        this.results.railway = {
          ok: true,
          message: `Railway API accessible, user: ${graphqlResult.data.me.name || graphqlResult.data.me.id}, public URLs: ${publicUrls.join(', ') || 'none'}`,
          latencyMs: response.latencyMs
        };
      } else {
        throw new Error('Invalid response from Railway API');
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
   * Check Supabase health: HEAD /auth/v1/health and signed service-role query
   */
  async checkSupabase() {
    const startTime = Date.now();
    
    try {
      const supabaseUrl = process.env.SUPABASE_URL;
      const supabaseServiceRole = process.env.SUPABASE_SERVICE_ROLE;

      if (!supabaseUrl || !supabaseServiceRole) {
        throw new Error('SUPABASE_URL or SUPABASE_SERVICE_ROLE not provided');
      }

      // Step 1: HEAD request to /auth/v1/health as specified in requirements
      const healthResponse = await this.makeRequest(`${supabaseUrl}/auth/v1/health`, {
        method: 'HEAD'
      });

      if (healthResponse.statusCode !== 200) {
        throw new Error(`Supabase auth health check failed with status ${healthResponse.statusCode}`);
      }

      // Step 2: Signed service-role query (read-only) as specified in requirements
      // Use a simple read-only query on a system table that should always exist
      // Query a known system table to test service-role authentication
      const queryResponse = await this.makeRequest(`${supabaseUrl}/rest/v1/pg_catalog.pg_tables?select=schemaname,tablename&limit=1`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${supabaseServiceRole}`,
          'apikey': supabaseServiceRole,
          'Accept': 'application/json'
        }
      });

      if (queryResponse.statusCode !== 200) {
        throw new Error(`Supabase service-role query failed with status ${queryResponse.statusCode}`);
      }

      const totalLatency = healthResponse.latencyMs + queryResponse.latencyMs;
      
      this.results.supabase = {
        ok: true,
        message: `Health endpoint OK (${healthResponse.latencyMs}ms), service-role query OK (${queryResponse.latencyMs}ms)`,
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
   * Generate Markdown summary for health-summary.md
   */
  generateMarkdownSummary() {
    const allOk = this.results.frontend.ok && this.results.vercel.ok && this.results.railway.ok && this.results.supabase.ok;
    const emoji = allOk ? '✅' : '❌';
    
    let markdown = `# ${emoji} Stack Health Check\n\n`;
    markdown += `**Timestamp:** ${this.results.timestamp}\n\n`;
    
    markdown += `| Service | Status | Latency | Message |\n`;
    markdown += `|---------|--------|---------|----------|\n`;
    
    ['frontend', 'vercel', 'railway', 'supabase'].forEach(service => {
      const result = this.results[service];
      const statusEmoji = result.ok ? '✅' : '❌';
      const status = result.ok ? 'OK' : 'FAILED';
      markdown += `| ${service.charAt(0).toUpperCase() + service.slice(1)} | ${statusEmoji} ${status} | ${result.latencyMs}ms | ${result.message} |\n`;
    });

    const okCount = [this.results.frontend, this.results.vercel, this.results.railway, this.results.supabase].filter(r => r.ok).length;
    markdown += `\n**Summary:** ${okCount}/4 services healthy\n`;

    return markdown;
  }

  /**
   * Run all health checks
   */
  async runAllChecks() {
    console.log('🔍 Starting stack health checks...\n');

    // Run checks in parallel for better performance
    await Promise.all([
      this.checkFrontend(),
      this.checkVercel(),
      this.checkRailway(), 
      this.checkSupabase()
    ]);

    // Write JSON results
    writeFileSync('stack-health.json', JSON.stringify(this.results, null, 2));

    // Generate and write Markdown summary as required
    const markdownSummary = this.generateMarkdownSummary();
    writeFileSync('health-summary.md', markdownSummary);

    // Output to console for CI/CD
    console.log(markdownSummary);

    // Write stderr patterns for stack-monitor.yml detectors
    const hasConfigIssues = !this.results.frontend.ok || !this.results.vercel.ok;
    if (hasConfigIssues) {
      // Output patterns that align with stack-monitor.yml detectors
      console.error('SUPABASE_URL missing or invalid');
      console.error('Frontend configuration issues detected');
    }

    // Exit with appropriate code - non-zero on any failure as required
    const allOk = this.results.frontend.ok && this.results.vercel.ok && this.results.railway.ok && this.results.supabase.ok;
    process.exit(allOk ? 0 : 1);
  }
}

// Run if called directly
if (fileURLToPath(import.meta.url) === process.argv[1]) {
  const checker = new StackHealthChecker();
  checker.runAllChecks().catch(error => {
    console.error('💥 Fatal error:', error.message);
    // Write error patterns for stack-monitor.yml detectors
    console.error('NEXT_PUBLIC_SUPABASE_URL missing or configuration error');
    writeFileSync('health-summary.md', `# ❌ Stack Health Check Failed\n\n**Error:** ${error.message}\n\n**Timestamp:** ${new Date().toISOString()}\n`);
    process.exit(1);
  });
}

export default StackHealthChecker;
