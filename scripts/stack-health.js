#!/usr/bin/env node

/**
 * Stack Health Monitor
 * Checks the health of all infrastructure components:
 * - Vercel (Frontend deployment)
 * - Railway (Backend service) 
 * - Supabase (Database and Auth)
 * - Overall system health
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
    supabase: { status: 'unknown', message: '', responseTime: 0 },
    frontend: { status: 'unknown', message: '', responseTime: 0 }
  }
};

async function makeRequest(url, options = {}) {
  const start = Date.now();
  try {
    const response = await fetch(url, {
      timeout: 10000,
      ...options
    });
    const responseTime = Date.now() - start;
    return { response, responseTime };
  } catch (error) {
    const responseTime = Date.now() - start;
    return { error, responseTime };
  }
}

async function checkVercel() {
  console.log('🔍 Checking Vercel status...');
  
  if (!config.vercelToken) {
    results.services.vercel = {
      status: 'error',
      message: 'VERCEL_TOKEN not configured',
      responseTime: 0
    };
    return;
  }

  try {
    const { response, responseTime, error } = await makeRequest(
      'https://api.vercel.com/v2/user',
      {
        headers: {
          'Authorization': `Bearer ${config.vercelToken}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (error) {
      throw error;
    }

    if (response.ok) {
      const userData = await response.json();
      results.services.vercel = {
        status: 'healthy',
        message: `API accessible, user: ${userData.user?.username || 'unknown'}`,
        responseTime
      };
    } else {
      results.services.vercel = {
        status: 'error',
        message: `API returned ${response.status}: ${response.statusText}`,
        responseTime
      };
    }
  } catch (error) {
    results.services.vercel = {
      status: 'error',
      message: `Connection failed: ${error.message}`,
      responseTime: error.responseTime || 0
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
    const { response, responseTime, error } = await makeRequest(
      'https://backboard.railway.app/graphql',
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
      responseTime: error.responseTime || 0
    };
  }
}

async function checkSupabase() {
  console.log('🗄️ Checking Supabase status...');
  
  if (!config.supabaseUrl) {
    results.services.supabase = {
      status: 'error',
      message: 'SUPABASE_URL not configured',
      responseTime: 0
    };
    return;
  }

  try {
    // Check REST API health
    const healthUrl = `${config.supabaseUrl.replace(/\/$/, '')}/rest/v1/`;
    const { response, responseTime, error } = await makeRequest(healthUrl, {
      headers: {
        'apikey': config.supabaseServiceRole || '',
        'Content-Type': 'application/json'
      }
    });

    if (error) {
      throw error;
    }

    if (response.ok) {
      results.services.supabase = {
        status: 'healthy',
        message: 'REST API accessible and responding',
        responseTime
      };
    } else {
      results.services.supabase = {
        status: 'error',
        message: `REST API returned ${response.status}: ${response.statusText}`,
        responseTime
      };
    }
  } catch (error) {
    results.services.supabase = {
      status: 'error',
      message: `Connection failed: ${error.message}`,
      responseTime: error.responseTime || 0
    };
  }
}

async function checkFrontend() {
  console.log('🌐 Checking Frontend health...');
  
  if (!config.frontendUrl) {
    results.services.frontend = {
      status: 'error',
      message: 'FRONTEND_URL not configured',
      responseTime: 0
    };
    return;
  }

  try {
    const healthUrl = `${config.frontendUrl.replace(/\/$/, '')}/api/health`;
    const { response, responseTime, error } = await makeRequest(healthUrl);

    if (error) {
      throw error;
    }

    if (response.ok) {
      const healthData = await response.json();
      results.services.frontend = {
        status: 'healthy',
        message: `Health check passed, uptime: ${healthData.uptime}s`,
        responseTime
      };
    } else {
      results.services.frontend = {
        status: 'error',
        message: `Health check returned ${response.status}: ${response.statusText}`,
        responseTime
      };
    }
  } catch (error) {
    results.services.frontend = {
      status: 'error',
      message: `Connection failed: ${error.message}`,
      responseTime: error.responseTime || 0
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
    checkSupabase(),
    checkFrontend()
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

  // Write exit code file for workflow detection
  const exitCode = results.overall.status === 'healthy' ? 0 : 1;
  writeFileSync(join(outputDir, '.stack-health-exit-code'), exitCode.toString());

  console.log(`\n🏁 Health check completed with status: ${results.overall.status}`);
  
  // Exit with appropriate code
  process.exit(exitCode);
}

// Handle uncaught errors gracefully
process.on('uncaughtException', (error) => {
  console.error('💥 Uncaught Exception:', error.message);
  writeFileSync(join(__dirname, '..', '.stack-health-exit-code'), '1');
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  console.error('💥 Unhandled Rejection:', reason);
  writeFileSync(join(__dirname, '..', '.stack-health-exit-code'), '1');
  process.exit(1);
});

main().catch((error) => {
  console.error('💥 Fatal Error:', error.message);
  writeFileSync(join(__dirname, '..', '.stack-health-exit-code'), '1');
  process.exit(1);
});