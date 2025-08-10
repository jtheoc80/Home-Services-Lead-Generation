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
 * - OPENAI_API_KEY: OpenAI API key
 * - SLACK_WEBHOOK: Slack webhook URL (optional)
 * - FRONTEND_URL: Frontend URL (optional fallback for Vercel)
 * - RAILWAY_SERVICE_ID: Railway service ID (optional for GraphQL queries)

 */

import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFileSync } from 'fs';
import https from 'https';
import http from 'http';

import { URL, fileURLToPath } from 'url';
=======
import { URL } from 'url';
import { fileURLToPath } from 'url';


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
        source: 'monitor',
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

export default StackHealthChecker;
=======
 * - AUTO_REMEDIATE: Enable auto-remediation (optional)
 */

import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = {
  vercelToken: process.env.VERCEL_TOKEN,
  railwayToken: process.env.RAILWAY_TOKEN,
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseServiceRole: process.env.SUPABASE_SERVICE_ROLE,
  frontendUrl: process.env.FRONTEND_URL,
  slackWebhook: process.env.SLACK_WEBHOOK,
  autoRemediate: process.env.AUTO_REMEDIATE === 'true',
};

const results = {
  timestamp: new Date().toISOString(),
  overall: { status: 'unknown', issues: [] },
  services: {
    vercel: { status: 'unknown', message: '', responseTime: 0 },
    railway: { status: 'unknown', message: '', responseTime: 0 },
    supabase: { status: 'unknown', message: '', responseTime: 0 }
  }
};

async function makeRequest(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  const start = Date.now();
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    const responseTime = Date.now() - start;
    return { response, responseTime };
  } catch (error) {
    clearTimeout(timeoutId);
    const responseTime = Date.now() - start;
    return { error, responseTime };
  }
}

async function checkVercel() {
  console.log('🔍 Checking Vercel status...');
  
  if (!config.vercelToken && !config.frontendUrl) {
    results.services.vercel = {
      status: 'error',
      message: 'VERCEL_TOKEN or FRONTEND_URL not configured',
      responseTime: 0
    };
    return;
  }

  try {
    let healthUrl = config.frontendUrl ? `${config.frontendUrl}/api/health` : null;

    // First, get the latest READY deployment if token is available
    if (config.vercelToken) {
      const { response: deploymentsResponse, responseTime: apiTime, error: apiError } = await makeRequest(
        'https://api.vercel.com/v6/deployments?limit=20',
        {
          headers: {
            'Authorization': `Bearer ${config.vercelToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (apiError) {
        if (!config.frontendUrl) {
          throw apiError;
        }
        // Fall back to FRONTEND_URL if available
      } else if (!deploymentsResponse.ok) {
        if (!config.frontendUrl) {
          results.services.vercel = {
            status: 'error',
            message: `API returned ${deploymentsResponse.status}: ${deploymentsResponse.statusText}`,
            responseTime: apiTime
          };
          return;
        }
        // Fall back to FRONTEND_URL
      } else {
        const deploymentsData = await deploymentsResponse.json();
        const readyDeployment = deploymentsData.deployments?.find(d => d.readyState === 'READY');
        
        if (readyDeployment) {
          healthUrl = `https://${readyDeployment.url}/api/health`;
        } else if (!config.frontendUrl) {
          results.services.vercel = {
            status: 'error',
            message: 'No READY deployments found',
            responseTime: apiTime
          };
          return;
        }
      }
    }

    if (!healthUrl) {
      throw new Error('No health URL determined');
    }

    // Now check the health endpoint
    const { response: healthResponse, responseTime: healthTime, error: healthError } = await makeRequest(healthUrl);

    if (healthError) {
      results.services.vercel = {
        status: 'error',
        message: `Health check failed: ${healthError.message}`,
        responseTime: healthTime
      };
      return;
    }

    if (healthResponse.ok) {
      results.services.vercel = {
        status: 'healthy',
        message: `Health check passed: ${healthUrl}`,
        responseTime: healthTime
      };
    } else {
      results.services.vercel = {
        status: 'error',
        message: `Health endpoint returned ${healthResponse.status}`,
        responseTime: healthTime
      };
    }
  } catch (error) {
    results.services.vercel = {
      status: 'error',
      message: `Connection failed: ${error.message}`,
      responseTime: 0
    };
  }
}

async function checkRailway() {
  console.log('🚂 Checking Railway status...');
  
  if (!config.railwayToken) {
    results.services.railway = {
      status: 'error',
      message: 'RAILWAY_TOKEN not configured',
      responseTime: 0
    };
    return;
  }

  try {
    // Check Railway GraphQL API for service status
    const { response, responseTime, error } = await makeRequest(
      'https://backboard.railway.app/graphql/v2',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${config.railwayToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: `query { me { id name } }`
        })
      }
    );

    if (error) {
      throw error;
    }

    if (response.ok) {
      const data = await response.json();
      if (data.data?.me) {
        results.services.railway = {
          status: 'healthy',
          message: `GraphQL API accessible, user: ${data.data.me.name || data.data.me.id}`,
          responseTime
        };
        
        // If we have a Railway URL, check its health endpoint
        const railwayUrl = process.env.RAILWAY_STATIC_URL || process.env.RAILWAY_URL;
        if (railwayUrl) {
          try {
            const healthUrl = `${railwayUrl}/api/health`;
            const { response: healthResponse, responseTime: healthTime } = await makeRequest(healthUrl);
            
            if (healthResponse && healthResponse.ok) {
              results.services.railway.message += `, health endpoint OK (${healthTime}ms)`;
            }
          } catch (healthError) {
            // Non-critical if health endpoint fails
            results.services.railway.message += ', health endpoint not accessible';
          }
        }
      } else {
        results.services.railway = {
          status: 'error',
          message: 'GraphQL API returned invalid response',
          responseTime
        };
      }
    } else {
      results.services.railway = {
        status: 'error',
        message: `API returned ${response.status}: ${response.statusText}`,
        responseTime
      };
    }
  } catch (error) {
    results.services.railway = {
      status: 'error',
      message: `Connection failed: ${error.message}`,
      responseTime: 0
    };
  }
}

async function checkSupabase() {
  console.log('🗄️ Checking Supabase status...');
  
  if (!config.supabaseUrl || !config.supabaseServiceRole) {
    results.services.supabase = {
      status: 'error',
      message: 'SUPABASE_URL or SUPABASE_SERVICE_ROLE not configured',
      responseTime: 0
    };
    return;
  }

  try {
    const startTime = Date.now();
    
    // Step 1: Insert a test record into leads table
    const insertPayload = {
      source: 'stack-health-monitor',
      name: 'Health Check Test',
      email: 'health-check@example.com',
      created_at: new Date().toISOString()
    };

    const { response: insertResponse, error: insertError } = await makeRequest(
      `${config.supabaseUrl}/rest/v1/leads`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${config.supabaseServiceRole}`,
          'Content-Type': 'application/json',
          'apikey': config.supabaseServiceRole,
          'Prefer': 'return=representation'
        },
        body: JSON.stringify(insertPayload)
      }
    );

    if (insertError) {
      throw new Error(`Insert failed: ${insertError.message}`);
    }

    if (!insertResponse.ok) {
      throw new Error(`Insert failed with status ${insertResponse.status}`);
    }

    // Step 2: Select the latest record from leads table
    const { response: selectResponse, error: selectError } = await makeRequest(
      `${config.supabaseUrl}/rest/v1/leads?source=eq.stack-health-monitor&limit=1&order=created_at.desc`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${config.supabaseServiceRole}`,
          'apikey': config.supabaseServiceRole
        }
      }
    );

    if (selectError) {
      throw new Error(`Select failed: ${selectError.message}`);
    }

    if (!selectResponse.ok) {
      throw new Error(`Select failed with status ${selectResponse.status}`);
    }

    const selectData = await selectResponse.json();
    const totalTime = Date.now() - startTime;

    results.services.supabase = {
      status: 'healthy',
      message: `Database operations successful (${selectData.length} records found)`,
      responseTime: totalTime
    };

  } catch (error) {
    const totalTime = Date.now() - startTime;
    results.services.supabase = {
      status: 'error',
      message: `Smoke test failed: ${error.message}`,
      responseTime: totalTime
    };
  }
}

function analyzeOverallHealth() {
  console.log('📊 Analyzing overall health...');
  
  const services = Object.values(results.services);
  const healthyCount = services.filter(s => s.status === 'healthy').length;
  const errorCount = services.filter(s => s.status === 'error').length;
  
  results.overall.issues = Object.entries(results.services)
    .filter(([_, service]) => service.status === 'error')
    .map(([name, service]) => ({
      service: name,
      message: service.message
    }));

  if (errorCount === 0) {
    results.overall.status = 'healthy';
  } else if (errorCount === services.length) {
    results.overall.status = 'critical';
  } else {
    results.overall.status = 'degraded';
  }

  console.log(`Overall status: ${results.overall.status} (${healthyCount}/${services.length} services healthy)`);
}

function generateMarkdownSummary() {
  const statusEmoji = {
    healthy: '✅',
    degraded: '⚠️',
    critical: '❌',
    error: '❌',
    warning: '⚠️',
    unknown: '❓'
  };

  let markdown = `# Stack Health Report\n\n`;
  markdown += `**Timestamp:** ${results.timestamp}\n`;
  markdown += `**Overall Status:** ${statusEmoji[results.overall.status]} ${results.overall.status.toUpperCase()}\n\n`;

  markdown += `## Service Status\n\n`;
  
  for (const [serviceName, service] of Object.entries(results.services)) {
    const emoji = statusEmoji[service.status];
    markdown += `### ${emoji} ${serviceName.charAt(0).toUpperCase() + serviceName.slice(1)}\n`;
    markdown += `- **Status:** ${service.status}\n`;
    markdown += `- **Message:** ${service.message}\n`;
    markdown += `- **Response Time:** ${service.responseTime}ms\n\n`;
  }

  if (results.overall.issues.length > 0) {
    markdown += `## Issues Detected\n\n`;
    results.overall.issues.forEach((issue, index) => {
      markdown += `${index + 1}. **${issue.service}**: ${issue.message}\n`;
    });
    markdown += `\n`;
  }

  markdown += `## Next Steps\n\n`;
  if (results.overall.status === 'healthy') {
    markdown += `All services are operating normally. No action required.\n`;
  } else {
    markdown += `The following services require attention:\n`;
    results.overall.issues.forEach(issue => {
      markdown += `- Fix ${issue.service}: ${issue.message}\n`;
    });
    
    if (config.autoRemediate) {
      markdown += `\n⚡ Auto-remediation is enabled and will be attempted.\n`;
    }
  }

  return markdown;
}

async function sendSlackNotification() {
  if (!config.slackWebhook || results.overall.status === 'healthy') {
    return;
  }

  console.log('📢 Sending Slack notification...');

  const statusEmoji = {
    degraded: '⚠️',
    critical: '🚨'
  };

  const failingServices = results.overall.issues.map(issue => issue.service).join(', ');
  const runUrl = process.env.GITHUB_SERVER_URL && process.env.GITHUB_REPOSITORY && process.env.GITHUB_RUN_ID
    ? `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`
    : 'N/A';
  
  const message = {
    text: `${statusEmoji[results.overall.status]} Stack Monitor Alert`,
    blocks: [
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Stack Health Alert* ${statusEmoji[results.overall.status]}\n*Status:* ${results.overall.status.toUpperCase()}\n*Failing Services:* ${failingServices}`
        }
      },
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Issues:*\n${results.overall.issues.map(issue => `• *${issue.service}*: ${issue.message}`).join('\n')}`
        }
      },
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Run Link:* <${runUrl}|View Workflow Run>`
        }
      }
    ]
  };

  try {
    const response = await fetch(config.slackWebhook, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(message)
    });

    if (response.ok) {
      console.log('✅ Slack notification sent successfully');
    } else {
      console.error(`❌ Failed to send Slack notification: ${response.status}`);
    }
  } catch (error) {
    console.error(`❌ Error sending Slack notification: ${error.message}`);
  }
}

async function main() {
  console.log('🚀 Starting stack health check...\n');

  // Run all health checks
  await Promise.all([
    checkVercel(),
    checkRailway(),
    checkSupabase()
  ]);

  // Analyze results
  analyzeOverallHealth();

  // Generate outputs
  const markdown = generateMarkdownSummary();
  
  // Save results to files
  const outputDir = join(__dirname, '..');
  writeFileSync(join(outputDir, 'stack-health.json'), JSON.stringify(results, null, 2));
  
  // Output markdown to stdout (will be captured by workflow)
  console.log('\n' + markdown);

  // Send Slack notification if needed
  await sendSlackNotification();

  console.log(`\n🏁 Health check completed with status: ${results.overall.status}`);
  
  // Exit with appropriate code
  const exitCode = results.overall.status === 'healthy' ? 0 : 1;
  process.exit(exitCode);
}

// Handle uncaught errors gracefully
process.on('uncaughtException', (error) => {
  console.error('💥 Uncaught Exception:', error.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  console.error('💥 Unhandled Rejection:', reason);
  process.exit(1);
});

// Run if called directly
if (fileURLToPath(import.meta.url) === process.argv[1]) {
  main().catch((error) => {
    console.error('💥 Fatal Error:', error.message);

    process.exit(1);
  });
}

export default StackHealthChecker;

export default main;


