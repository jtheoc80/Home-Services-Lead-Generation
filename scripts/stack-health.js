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

export default { main, checkVercel, checkRailway, checkSupabase, analyzeOverallHealth, generateMarkdownSummary, sendSlackNotification };
