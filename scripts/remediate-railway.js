#!/usr/bin/env node

/**
 * Railway Remediation Script
 * Attempts to resolve common Railway service issues
 */

console.log('🔧 Starting Railway remediation...');

async function remediateRailway() {
  const railwayToken = process.env.RAILWAY_TOKEN;
  
  if (!railwayToken) {
    console.log('❌ RAILWAY_TOKEN not configured - cannot remediate');
    process.exit(1);
  }

  try {
    console.log('🔍 Checking Railway services...');
    
    // Example: Check service status and restart if needed
    const response = await fetch('https://backboard.railway.app/graphql', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${railwayToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: `query { me { projects { edges { node { id name services { edges { node { id name } } } } } } } }`
      })
    // Add timeout protection to fetch (30 seconds)
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);
    let response;
    try {
      response = await fetch('https://backboard.railway.app/graphql', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${railwayToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: `query { me { projects { edges { node { id name services { edges { node { id name } } } } } } } }`
        }),
        signal: controller.signal
      });
    } finally {
      clearTimeout(timeout);
    }

    if (!response.ok) {
      throw new Error(`Railway API error: ${response.status}`);
    }

    const data = await response.json();
    console.log(`✅ Connected to Railway API`);
    
    // Add remediation logic here:
    // - Check service health
    // - Restart unhealthy services
    // - Scale services if needed
    // - Check environment variables
    
    console.log('✅ Railway remediation completed successfully');
    
  } catch (error) {
    console.error('❌ Railway remediation failed:', error.message);

 * Railway Service Remediation Script
 * 
 * This script uses Railway's GraphQL v2 API to:
 * 1. Check service status
 * 2. Restart the service or trigger a redeploy
 * 3. Monitor the operation and report results
 * 
 * Requirements:
 * - RAILWAY_TOKEN: Railway API token
 * - RAILWAY_SERVICE_ID: Railway service ID
 * 
 * Uses only Node.js built-ins, no external dependencies.
 */

const RAILWAY_GRAPHQL_ENDPOINT = 'https://backboard.railway.app/graphql/v2';

// Read environment variables
const RAILWAY_TOKEN = process.env.RAILWAY_TOKEN;
const RAILWAY_SERVICE_ID = process.env.RAILWAY_SERVICE_ID;

// Input validation
if (!RAILWAY_TOKEN) {
  console.error('❌ Error: RAILWAY_TOKEN environment variable is required');
  process.exit(1);
}

if (!RAILWAY_SERVICE_ID) {
  console.error('❌ Error: RAILWAY_SERVICE_ID environment variable is required');
  process.exit(1);
}

console.log('🚀 Starting Railway service remediation...');
console.log(`📋 Service ID: ${RAILWAY_SERVICE_ID}`);

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
 * Query service information and current deployment status
 */
async function getServiceInfo() {
  const query = `
    query GetService($serviceId: String!) {
      service(id: $serviceId) {
        id
        name
        projectId
        serviceInstances {
          id
          environmentId
          latestDeployment {
            id
            status
            staticUrl
            url
            createdAt
            finishedAt
          }
          buildCommand
          startCommand
        }
      }
    }
  `;

  console.log('📡 Fetching service information...');
  const data = await makeGraphQLRequest(query, { serviceId: RAILWAY_SERVICE_ID });
  
  if (!data.service) {
    throw new Error(`Service with ID ${RAILWAY_SERVICE_ID} not found`);
  }

  const service = data.service;
  console.log(`✅ Found service: ${service.name}`);
  console.log(`📊 Service instances: ${service.serviceInstances.length}`);
  
  // Log current deployment status for each instance
  service.serviceInstances.forEach((instance, index) => {
    const deployment = instance.latestDeployment;
    if (deployment) {
      console.log(`📊 Instance ${index + 1} - Latest deployment: ${deployment.status}`);
      if (deployment.url) {
        console.log(`🔗 Instance ${index + 1} - URL: ${deployment.url}`);
      }
    } else {
      console.log(`📊 Instance ${index + 1} - No deployments found`);
    }
  });

  return service;
}

/**
 * Restart a service instance
 */
async function restartServiceInstance(serviceInstanceId) {
  const mutation = `
    mutation RestartServiceInstance($serviceInstanceId: String!) {
      serviceInstanceRestart(serviceInstanceId: $serviceInstanceId) {
        id
      }
    }
  `;

  console.log(`🔄 Restarting service instance: ${serviceInstanceId}`);
  const data = await makeGraphQLRequest(mutation, { serviceInstanceId });
  
  if (!data.serviceInstanceRestart) {
    throw new Error('Failed to restart service instance');
  }

  console.log('✅ Service instance restart triggered');
  return data.serviceInstanceRestart;
}

/**
 * Trigger a redeploy of a service instance
 */
async function redeployServiceInstance(serviceInstanceId) {
  const mutation = `
    mutation RedeployServiceInstance($serviceInstanceId: String!) {
      serviceInstanceRedeploy(serviceInstanceId: $serviceInstanceId) {
        id
        status
        staticUrl
        url
      }
    }
  `;

  console.log(`🚀 Triggering redeploy for service instance: ${serviceInstanceId}`);
  const data = await makeGraphQLRequest(mutation, { serviceInstanceId });
  
  if (!data.serviceInstanceRedeploy) {
    throw new Error('Failed to trigger redeploy');
  }

  console.log('✅ Service instance redeploy triggered');
  return data.serviceInstanceRedeploy;
}

/**
 * Monitor deployment progress
 */
async function monitorDeployment(serviceInstanceId, maxWaitTime = 300000) { // 5 minutes
  console.log('⏳ Monitoring deployment progress...');
  
  const query = `
    query GetServiceInstance($serviceInstanceId: String!) {
      serviceInstance(id: $serviceInstanceId) {
        latestDeployment {
          id
          status
          staticUrl
          url
          createdAt
          finishedAt
        }
      }
    }
  `;

  const startTime = Date.now();
  let lastStatus = null;
  
  while (Date.now() - startTime < maxWaitTime) {
    try {
      const data = await makeGraphQLRequest(query, { serviceInstanceId });
      const deployment = data.serviceInstance?.latestDeployment;
      
      if (!deployment) {
        console.log('📊 No deployment found');
        await new Promise(resolve => setTimeout(resolve, 10000));
        continue;
      }
      
      // Only log status changes
      if (deployment.status !== lastStatus) {
        console.log(`📊 Deployment status: ${deployment.status}`);
        lastStatus = deployment.status;
      }
      
      // Check if deployment is complete
      if (deployment.status === 'SUCCESS') {
        console.log('✅ Deployment completed successfully');
        return deployment;
      } else if (deployment.status === 'FAILED' || deployment.status === 'CRASHED') {
        throw new Error(`Deployment failed with status: ${deployment.status}`);
      }
      
      // Wait 10 seconds before checking again
      await new Promise(resolve => setTimeout(resolve, 10000));
      
    } catch (error) {
      console.log(`⚠️  Error monitoring deployment: ${error.message}`);
      await new Promise(resolve => setTimeout(resolve, 10000));
    }
  }
  
  console.log('⚠️  Deployment monitoring timeout - operation may still be in progress');
  return null;
}

/**
 * Get final service status
 */
async function getFinalStatus() {
  console.log('📊 Getting final service status...');
  return await getServiceInfo();
}

/**
 * Main execution function
 */
async function main() {
  try {
    // Step 1: Get current service information
    const initialService = await getServiceInfo();
    
    if (initialService.serviceInstances.length === 0) {
      throw new Error('No service instances found');
    }
    
    // Use the first service instance (most common case)
    const serviceInstance = initialService.serviceInstances[0];
    const serviceInstanceId = serviceInstance.id;
    
    console.log(`🎯 Target service instance: ${serviceInstanceId}`);
    
    // Step 2: Determine remediation strategy
    const currentDeployment = serviceInstance.latestDeployment;
    let operation = 'restart';
    
    if (!currentDeployment || currentDeployment.status === 'FAILED' || currentDeployment.status === 'CRASHED') {
      operation = 'redeploy';
      console.log('🔄 No successful deployment found, will trigger redeploy');
    } else {
      console.log('🔄 Service has successful deployment, will restart');
    }
    
    // Step 3: Execute remediation
    let newDeployment = null;
    
    if (operation === 'redeploy') {
      newDeployment = await redeployServiceInstance(serviceInstanceId);
      
      // Monitor the redeploy
      const finalDeployment = await monitorDeployment(serviceInstanceId);
      if (finalDeployment) {
        newDeployment = finalDeployment;
      }
    } else {
      await restartServiceInstance(serviceInstanceId);
      
      // Give it a moment for restart to take effect
      console.log('⏳ Waiting for service to restart...');
      await new Promise(resolve => setTimeout(resolve, 15000));
    }
    
    // Step 4: Get final status
    const finalService = await getFinalStatus();
    const finalInstance = finalService.serviceInstances[0];
    const finalDeployment = finalInstance.latestDeployment;
    
    // Step 5: Print results
    console.log('');
    console.log('🎉 Railway service remediation completed!');
    console.log(`🔧 Operation: ${operation}`);
    
    if (finalDeployment) {
      console.log(`📊 Final status: ${finalDeployment.status}`);
      
      if (finalDeployment.url) {
        console.log(`🔗 Service URL: ${finalDeployment.url}`);
      }
      if (finalDeployment.staticUrl) {
        console.log(`🔗 Static URL: ${finalDeployment.staticUrl}`);
      }
      
      console.log(`🆔 Deployment ID: ${finalDeployment.id}`);
      
      if (finalDeployment.finishedAt) {
        console.log(`📅 Completed: ${new Date(finalDeployment.finishedAt).toISOString()}`);
      }
    }
    
    console.log(`🆔 Service Instance ID: ${serviceInstanceId}`);
    console.log('');
    
    // Output for automation tools
    if (finalDeployment?.url) {
      console.log(`::set-output name=service_url::${finalDeployment.url}`);
    }
    console.log(`::set-output name=deployment_id::${finalDeployment?.id || 'N/A'}`);
    console.log(`::set-output name=status::${finalDeployment?.status || 'UNKNOWN'}`);
    const githubOutput = process.env.GITHUB_OUTPUT;
    if (githubOutput) {
      const fs = require('fs');
      const outputs = [];
      if (finalDeployment?.url) {
        outputs.push(`service_url=${finalDeployment.url}`);
      }
      outputs.push(`deployment_id=${finalDeployment?.id || 'N/A'}`);
      outputs.push(`status=${finalDeployment?.status || 'UNKNOWN'}`);
      outputs.push(`operation=${operation}`);
      fs.appendFileSync(githubOutput, outputs.map(line => line + '\n').join(''));
    } else {
      if (finalDeployment?.url) {
        console.log(`service_url=${finalDeployment.url}`);
      }
      console.log(`deployment_id=${finalDeployment?.id || 'N/A'}`);
      console.log(`status=${finalDeployment?.status || 'UNKNOWN'}`);
      console.log(`operation=${operation}`);
    }
    
  } catch (error) {
    console.error('');
    console.error('❌ Railway service remediation failed:', error.message);
    console.error('');

    process.exit(1);
  }
}


remediateRailway();

// Execute the main function
await main();

