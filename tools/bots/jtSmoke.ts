#!/usr/bin/env tsx

/**
 * JT Smoke Test Bot
 * 
 * E2E smoke testing bot that validates the complete lead ingestion pipeline.
 * Based on the existing e2eLeadSmoke.ts script.
 */

import { program } from 'commander';

interface LeadPostResponse {
  ok?: boolean;
  trace_id?: string;
  data?: any;
  error?: string;
}

interface LeadsGetResponse {
  data?: any[];
  trace_id?: string;
  error?: string;
  count?: number;
}

async function smokePOST(baseUrl: string): Promise<{ ok: boolean; trace_id?: string; email: string }> {
  const timestamp = Date.now();
  // Using @example.com for test emails is safe: example.com is reserved for documentation/testing and will never receive real email.
  const smokeEmail = `smoke+${timestamp}@example.com`;
  
  const payload = {
    name: "Smoke",
    email: smokeEmail,
    source: "e2e", 
    trace_tag: "cli"
  };

  console.log(`🚀 POST ${baseUrl}/api/leads`);
  console.log(`📧 Testing with email: ${smokeEmail}`);

  try {
    const response = await fetch(`${baseUrl}/api/leads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    const data: LeadPostResponse = await response.json();
    
    console.log(`📊 Status: ${response.status}`);
    console.log(`📊 Response:`, JSON.stringify(data, null, 2));

    if (!response.ok) {
      throw new Error(`POST failed with status ${response.status}: ${data.error || 'Unknown error'}`);
    }

    if (!data.ok) {
      throw new Error(`Response missing 'ok: true'. Got: ${JSON.stringify(data)}`);
    }

    if (!data.trace_id) {
      throw new Error(`Response missing 'trace_id'. Got: ${JSON.stringify(data)}`);
    }

    console.log(`✅ POST succeeded with trace_id: ${data.trace_id}`);
    return { ok: true, trace_id: data.trace_id, email: smokeEmail };

  } catch (error: any) {
    console.error(`❌ POST failed:`, error.message);
    throw error;
  }
}

async function smokeGET(baseUrl: string, expectedEmail: string): Promise<boolean> {
  console.log(`🔍 GET ${baseUrl}/api/leads/recent`);
  console.log(`🔍 Looking for email: ${expectedEmail}`);

  try {
    const response = await fetch(`${baseUrl}/api/leads/recent`);
    const data: LeadsGetResponse = await response.json();
    
    console.log(`📊 Status: ${response.status}`);
    console.log(`📊 Response:`, JSON.stringify(data, null, 2));

    if (!response.ok) {
      throw new Error(`GET failed with status ${response.status}: ${data.error || 'Unknown error'}`);
    }

    if (!data.data) {
      throw new Error(`Response missing 'data' array. Got: ${JSON.stringify(data)}`);
    }

    // Look for our email in the recent leads
    const foundLead = data.data.find((lead: any) => lead.email === expectedEmail);
    
    if (!foundLead) {
      console.log(`📝 Available emails in recent leads:`, data.data.map((lead: any) => lead.email));
      throw new Error(`Expected email '${expectedEmail}' not found in recent leads`);
    }

    console.log(`✅ GET succeeded - found lead with email: ${expectedEmail}`);
    console.log(`📄 Lead data:`, JSON.stringify(foundLead, null, 2));
    return true;

  } catch (error: any) {
    console.error(`❌ GET failed:`, error.message);
    throw error;
  }
}

async function runSmokeTest(baseUrl: string): Promise<void> {
  console.log(`🧪 Starting E2E Lead Smoke Test`);
  console.log(`🎯 Target URL: ${baseUrl}`);
  console.log(`⏰ Started at: ${new Date().toISOString()}`);
  console.log('');

  const startTime = Date.now();

  try {
    // Step 1: POST a new lead
    const postResult = await smokePOST(baseUrl);
    console.log('');

    // Step 2: GET recent leads and verify our lead appears
    await smokeGET(baseUrl, postResult.email);
    console.log('');

    const duration = Date.now() - startTime;
    console.log(`✅ E2E Lead Smoke Test PASSED in ${duration}ms`);
    console.log(`🎉 All assertions succeeded:`);
    console.log(`   - POST /api/leads returned { ok: true, trace_id }`);
    console.log(`   - GET /api/leads/recent found the inserted email`);
    console.log(`   - trace_id: ${postResult.trace_id}`);
    console.log(`   - email: ${postResult.email}`);

  } catch (error: any) {
    const duration = Date.now() - startTime;
    console.log('');
    console.error(`❌ E2E Lead Smoke Test FAILED after ${duration}ms`);
    console.error(`💥 Error: ${error.message}`);
    console.error(`⏰ Failed at: ${new Date().toISOString()}`);
    
    // Exit with non-zero status for CI/CD failure detection
    // Propagate error to be handled at the module level
    throw error;
  }
}

/**
 * Main entry point for the JT Smoke bot
 */
export async function main(args: string[] = []): Promise<void> {
  const prog = program
    .name('jt-smoke')
    .description('E2E smoke test for lead ingestion pipeline')
    .requiredOption('--baseUrl <url>', 'Base URL of the application (e.g., https://your-app.vercel.app)')
    .action(async (options) => {
      await runSmokeTest(options.baseUrl);
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