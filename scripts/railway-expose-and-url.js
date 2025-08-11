#!/usr/bin/env node

/**
 * Railway Service Exposure and URL Script
 * 
 * This script uses Railway's GraphQL v2 API to:
 * 1. Check if a service is exposed to the internet
 * 2. Expose the service if it's not already exposed
 * 3. Create a domain if one doesn't exist
 * 4. Print the public HTTPS URL
 */

const RAILWAY_GRAPHQL_ENDPOINT = 'https://backboard.railway.app/graphql/v2';

// Read environment variables
const RAILWAY_TOKEN = process.env.RAILWAY_TOKEN;
const RAILWAY_SERVICE_ID = process.env.RAILWAY_SERVICE_ID;
const RAILWAY_ENV_ID = process.env.RAILWAY_ENV_ID;

// Input validation
if (!RAILWAY_TOKEN) {
  console.error('❌ Error: RAILWAY_TOKEN environment variable is required');
  process.exit(1);
}

if (!RAILWAY_SERVICE_ID) {
  console.error('❌ Error: RAILWAY_SERVICE_ID environment variable is required');
  process.exit(1);
}

console.log('🚀 Starting Railway service exposure process...');
console.log(`📋 Service ID: ${RAILWAY_SERVICE_ID}`);
if (RAILWAY_ENV_ID) {
  console.log(`📋 Environment ID: ${RAILWAY_ENV_ID}`);
}

/**
 * Make a GraphQL request to Railway API
 */
async function makeGraphQLRequest(query, variables = {}) {
  try {
    const response = await fetch(RAILWAY_GRAPHQL_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${RAILWAY_TOKEN}`
      },
      body: JSON.stringify({
        query,
        variables
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    if (data.errors) {
      throw new Error(`GraphQL errors: ${data.errors.map(e => e.message).join(', ')}`);
    }

    return data.data;
  } catch (error) {
    console.error('❌ GraphQL request failed:', error.message);
    throw error;
  }
}

/**
 * Query service information
 */
async function getServiceInfo() {
  const query = `
    query GetService($serviceId: String!) {
      service(id: $serviceId) {
        id
        expose
        domains {
          host
          httpsRedirect
        }
        environment {
          id
          name
        }
      }
    }
  `;

  console.log('📡 Fetching service information...');
  const data = await makeGraphQLRequest(query, { serviceId: RAILWAY_SERVICE_ID });
  
  if (!data.service) {
    throw new Error(`Service with ID ${RAILWAY_SERVICE_ID} not found`);
  }

  return data.service;
}

/**
 * Expose service to the internet
 */
async function exposeService() {
  const mutation = `
    mutation ExposeService($serviceId: String!) {
      serviceUpdate(id: $serviceId, input: { expose: true }) {
        id
        expose
      }
    }
  `;

  console.log('🌐 Exposing service to the internet...');
  const data = await makeGraphQLRequest(mutation, { serviceId: RAILWAY_SERVICE_ID });
  
  if (!data.serviceUpdate) {
    throw new Error('Failed to expose service');
  }

  console.log('✅ Service exposed successfully');
  return data.serviceUpdate;
}

/**
 * Create a domain for the service
 */
async function createDomain() {
  // Generate a randomized host name
  const randomSuffix = Math.random().toString(36).substring(2, 8);
  const host = `${RAILWAY_SERVICE_ID.substring(0, 8)}-auto-${randomSuffix}`;

  const mutation = `
    mutation CreateServiceDomain($serviceId: String!, $host: String!) {
      serviceDomainCreate(serviceId: $serviceId, host: $host) {
        id
        host
        httpsRedirect
      }
    }
  `;

  console.log(`🔗 Creating domain: ${host}.railway.app`);
  const data = await makeGraphQLRequest(mutation, { 
    serviceId: RAILWAY_SERVICE_ID, 
    host 
  });
  
  if (!data.serviceDomainCreate) {
    throw new Error('Failed to create domain');
  }

  console.log('✅ Domain created successfully');
  return data.serviceDomainCreate;
}

/**
 * Main execution function
 */
async function main() {
  try {
    // Step 1: Get current service information
    const service = await getServiceInfo();
    
    console.log(`📊 Service expose status: ${service.expose ? '✅ Exposed' : '❌ Not exposed'}`);
    console.log(`📊 Existing domains: ${service.domains.length}`);
    
    // Step 2: Expose service if not already exposed
    if (!service.expose) {
      await exposeService();
    } else {
      console.log('✅ Service already exposed');
    }
    
    // Step 3: Create domain if none exists
    let domain;
    if (service.domains.length === 0) {
      domain = await createDomain();
    } else {
      domain = service.domains[0];
      console.log(`✅ Using existing domain: ${domain.host}`);
    }
    
    // Step 4: Construct and print the public URL
    const protocol = domain.httpsRedirect !== false ? 'https' : 'http';
    const publicUrl = `${protocol}://${domain.host}`;
    
    console.log('');
    console.log('🎉 Service is ready!');
    console.log(`🔗 Public URL: ${publicUrl}`);
    console.log('');
    
    // Output for GitHub Actions
    console.log(`::set-output name=public_url::${publicUrl}`);
    
  } catch (error) {
    console.error('');
    console.error('❌ Failed to expose Railway service:', error.message);
    console.error('');
    process.exit(1);
  }
}

// Execute the main function
await main();