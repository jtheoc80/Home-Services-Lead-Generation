#!/usr/bin/env tsx

import { request } from 'undici';
import { Command } from 'commander';

interface SmokeTestConfig {
  baseUrl: string;
  debug: boolean;
}

interface ApiResponse {
  ok?: boolean;
  trace_id?: string;
  data?: any;
  error?: string;
}

async function main() {
  const program = new Command();
  
  program
    .name('jtSmoke')
    .description('JT Smoke Test for Home Services Lead Generation API')
    .requiredOption('--baseUrl <url>', 'Base URL for the API (required)')
    .option('--debug', 'Enable debug mode to fetch trace information', false)
    .parse();

  const options = program.opts<SmokeTestConfig>();

  // Validate environment variables
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const debugApiKey = process.env.DEBUG_API_KEY;
  const testMode = process.env.LEADS_TEST_MODE;

  if (!supabaseUrl) {
    console.error('ERROR: NEXT_PUBLIC_SUPABASE_URL environment variable is required');
    process.exit(1);
  }

  if (!serviceRoleKey) {
    console.error('ERROR: SUPABASE_SERVICE_ROLE_KEY environment variable is required');
    process.exit(1);
  }

  if (!debugApiKey) {
    console.error('ERROR: DEBUG_API_KEY environment variable is required');
    process.exit(1);
  }

  // Log masked Supabase URL (show only suffix)
  const urlParts = supabaseUrl.split('.');
  const maskedUrl = urlParts.length > 1 ? `*****.${urlParts.slice(-2).join('.')}` : '*****';
  console.log(`Using Supabase URL: ${maskedUrl}`);
  
  if (testMode === 'true') {
    console.log('LEADS_TEST_MODE: enabled');
  }

  try {
    // Step 1: POST to /api/leads
    const email = `jt+${Date.now()}@example.com`;
    const leadData = {
      name: "JT Smoke",
      email: email,
      phone: "",
      source: "e2e"
    };

    console.log(`Step 1: Creating lead with email ${email}`);
    
    const createResponse = await request(`${options.baseUrl}/api/leads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(leadData)
    });

    if (createResponse.statusCode !== 201) {
      const errorBody = await createResponse.body.text();
      console.error(`FAIL: Step 1 - Expected status 201, got ${createResponse.statusCode}`);
      console.error('Response body:', errorBody);
      process.exit(1);
    }

    const createResult: ApiResponse = await createResponse.body.json();
    
    if (!createResult.ok || !createResult.trace_id) {
      console.error('FAIL: Step 1 - Expected { ok: true, trace_id }');
      console.error('Response:', createResult);
      process.exit(1);
    }

    const trace_id = createResult.trace_id;
    console.log(`Step 1: PASS - Lead created with trace_id: ${trace_id}`);

    // Step 2: GET /api/leads/recent and check email appears
    console.log('Step 2: Checking recent leads');
    
    const recentResponse = await request(`${options.baseUrl}/api/leads/recent`, {
      method: 'GET'
    });

    if (recentResponse.statusCode !== 200) {
      const errorBody = await recentResponse.body.text();
      console.error(`FAIL: Step 2 - Expected status 200, got ${recentResponse.statusCode}`);
      console.error('Response body:', errorBody);
      process.exit(1);
    }

    const recentResult: ApiResponse = await recentResponse.body.json();
    
    if (!recentResult.data || !Array.isArray(recentResult.data)) {
      console.error('FAIL: Step 2 - Expected data array in response');
      console.error('Response:', recentResult);
      process.exit(1);
    }

    const emailFound = recentResult.data.some((lead: any) => lead.email === email);
    
    if (!emailFound) {
      console.error(`FAIL: Step 2 - Email ${email} not found in recent leads`);
      console.error('Recent leads:', recentResult.data.map((l: any) => ({ email: l.email, created_at: l.created_at })));
      process.exit(1);
    }

    console.log(`Step 2: PASS - Email ${email} found in recent leads`);

    // Step 3: Debug trace (if --debug flag is provided)
    if (options.debug) {
      console.log(`Step 3: Fetching trace information for ${trace_id}`);
      
      const traceResponse = await request(`${options.baseUrl}/api/leads/trace/${trace_id}`, {
        method: 'GET',
        headers: {
          'X-Debug-Key': debugApiKey
        }
      });

      if (traceResponse.statusCode !== 200) {
        const errorBody = await traceResponse.body.text();
        console.error(`FAIL: Step 3 - Expected status 200, got ${traceResponse.statusCode}`);
        console.error('Response body:', errorBody);
        process.exit(1);
      }

      const traceResult = await traceResponse.body.json();
      
      if (!traceResult.ingest_logs || !Array.isArray(traceResult.ingest_logs)) {
        console.error('FAIL: Step 3 - Expected ingest_logs array in response');
        console.error('Response:', traceResult);
        process.exit(1);
      }

      console.log('Step 3: PASS - Trace stages in order:');
      traceResult.ingest_logs
        .sort((a: any, b: any) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
        .forEach((log: any, index: number) => {
          const status = log.ok ? 'OK' : 'FAIL';
          console.log(`  ${index + 1}. ${log.stage}: ${status} (${log.created_at})`);
          if (log.details && typeof log.details === 'object') {
            console.log(`     Details: ${JSON.stringify(log.details)}`);
          }
        });
    }

    // Success!
    console.log(`PASS ${trace_id}`);
    process.exit(0);

  } catch (error) {
    console.error('FAIL: Unexpected error during smoke test');
    console.error('Error:', error instanceof Error ? error.message : error);
    if (error instanceof Error && error.stack) {
      console.error('Stack:', error.stack);
    }
    process.exit(1);
  }
}

// Run the main function
main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});