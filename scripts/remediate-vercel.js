#!/usr/bin/env node

/**
 * Vercel Deployment Remediation Script
 * 
 * This script uses Vercel's REST API to:
 * 1. Find the latest non-draft deployment
 * 2. Trigger a redeploy of that deployment
 * 3. Print the new deployment URL and state
 * 
 * Requirements:
 * - VERCEL_TOKEN: Vercel API token
 * - TARGET_PROJECT: Optional target project ID/name
 * 
 * Uses only Node.js built-ins, no external dependencies.
 */

const VERCEL_API_BASE = 'https://api.vercel.com';

// Read environment variables
const VERCEL_TOKEN = process.env.VERCEL_TOKEN;
const TARGET_PROJECT = process.env.TARGET_PROJECT;

// Input validation
if (!VERCEL_TOKEN) {
  console.error('❌ Error: VERCEL_TOKEN environment variable is required');
  process.exit(1);
}

console.log('🚀 Starting Vercel deployment remediation...');
if (TARGET_PROJECT) {
  console.log(`📋 Target Project: ${TARGET_PROJECT}`);
}

/**
 * Make a request to Vercel API
 */
async function makeVercelRequest(endpoint, options = {}) {
  const url = `${VERCEL_API_BASE}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${VERCEL_TOKEN}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`❌ Vercel API request failed: ${error.message}`);
    throw error;
  }
}

/**
 * Get user/team information to determine scope
 */
async function getUserInfo() {
  console.log('👤 Fetching user information...');
  const data = await makeVercelRequest('/v2/user');
  return data.user || data;
}

/**
 * Get deployments for a project or user
 */
async function getDeployments(projectId = null, teamId = null) {
  console.log('📡 Fetching deployments...');
  
  let endpoint = '/v6/deployments';
  const params = new URLSearchParams();
  
  if (projectId) {
    params.append('projectId', projectId);
  }
  if (teamId) {
    params.append('teamId', teamId);
  }
  params.append('limit', '50'); // Get recent deployments
  
  if (params.toString()) {
    endpoint += `?${params.toString()}`;
  }

  const data = await makeVercelRequest(endpoint);
  return data.deployments || [];
}

/**
 * Find project by name or ID
 */
async function findProject(projectName, teamId = null) {
  console.log(`🔍 Searching for project: ${projectName}`);
  
  let endpoint = '/v9/projects';
  if (teamId) {
    endpoint += `?teamId=${teamId}`;
  }

  const data = await makeVercelRequest(endpoint);
  const projects = data.projects || [];
  
  // Try to find by exact name or ID
  const project = projects.find(p => 
    p.name === projectName || 
    p.id === projectName
  );
  
  if (!project) {
    throw new Error(`Project "${projectName}" not found`);
  }
  
  console.log(`✅ Found project: ${project.name} (${project.id})`);
  return project;
}

/**
 * Find the latest non-draft deployment
 */
function findLatestNonDraftDeployment(deployments) {
  console.log(`🔍 Analyzing ${deployments.length} deployments...`);
  
  // Filter out draft deployments and sort by creation date (newest first)
  const validDeployments = deployments
    .filter(d => {
      // Skip drafts and failed deployments
      return d.state !== 'BUILDING' && 
             d.state !== 'QUEUED' && 
             d.state !== 'INITIALIZING' &&
             d.readyState !== 'CANCELED' &&
             d.readyState !== 'ERROR';
    })
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  if (validDeployments.length === 0) {
    throw new Error('No valid deployments found');
  }

  const latest = validDeployments[0];
  console.log(`✅ Found latest deployment: ${latest.uid}`);
  console.log(`📊 State: ${latest.state}, Ready State: ${latest.readyState}`);
  console.log(`📅 Created: ${new Date(latest.createdAt).toISOString()}`);
  
  return latest;
}

/**
 * Trigger a redeploy of a deployment
 */
async function triggerRedeploy(deployment) {
  console.log(`🔄 Triggering redeploy of deployment: ${deployment.uid}`);
  
  const redeployData = {
    name: deployment.name,
    target: deployment.target || 'production',
    source: 'import',
    gitSource: deployment.gitSource || undefined
  };
  
  // Remove undefined values
  Object.keys(redeployData).forEach(key => {
    if (redeployData[key] === undefined) {
      delete redeployData[key];
    }
  });

  const newDeployment = await makeVercelRequest('/v13/deployments', {
    method: 'POST',
    body: JSON.stringify(redeployData)
  });

  console.log(`✅ New deployment triggered: ${newDeployment.uid}`);
  return newDeployment;
}

/**
 * Get deployment status
 */
async function getDeploymentStatus(deploymentId) {
  const data = await makeVercelRequest(`/v13/deployments/${deploymentId}`);
  return data;
}

/**
 * Wait for deployment to reach a final state
 */
async function waitForDeployment(deploymentId, maxWaitTime = 300000) { // 5 minutes
  console.log('⏳ Waiting for deployment to complete...');
  
  const startTime = Date.now();
  
  while (Date.now() - startTime < maxWaitTime) {
    const deployment = await getDeploymentStatus(deploymentId);
    
    console.log(`📊 Current state: ${deployment.state}, Ready state: ${deployment.readyState || 'N/A'}`);
    
    // Check if deployment is in a final state
    if (deployment.readyState === 'READY') {
      return deployment;
    } else if (deployment.readyState === 'ERROR' || deployment.readyState === 'CANCELED') {
      throw new Error(`Deployment failed with state: ${deployment.readyState}`);
    }
    
    // Wait 10 seconds before checking again
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
  
  throw new Error('Deployment timeout - taking longer than expected');
}

/**
 * Main execution function
 */
async function main() {
  try {
    // Get user information
    const userInfo = await getUserInfo();
    const teamId = userInfo.defaultTeamId || null;
    
    let projectId = null;
    
    // If TARGET_PROJECT is specified, find the project
    if (TARGET_PROJECT) {
      const project = await findProject(TARGET_PROJECT, teamId);
      projectId = project.id;
    }
    
    // Get deployments
    const deployments = await getDeployments(projectId, teamId);
    
    if (deployments.length === 0) {
      throw new Error('No deployments found');
    }
    
    // Find latest valid deployment
    const latestDeployment = findLatestNonDraftDeployment(deployments);
    
    // Trigger redeploy
    const newDeployment = await triggerRedeploy(latestDeployment);
    
    // Wait for deployment to complete
    const completedDeployment = await waitForDeployment(newDeployment.uid);
    
    // Print results
    const deploymentUrl = `https://${completedDeployment.url}`;
    
    console.log('');
    console.log('🎉 Deployment remediation completed successfully!');
    console.log(`🔗 New URL: ${deploymentUrl}`);
    console.log(`📊 State: ${completedDeployment.state}`);
    console.log(`📊 Ready State: ${completedDeployment.readyState}`);
    console.log(`🆔 Deployment ID: ${completedDeployment.uid}`);
    console.log('');
    
    // Output for automation tools
    console.log(`::set-output name=deployment_url::${deploymentUrl}`);
    console.log(`::set-output name=deployment_id::${completedDeployment.uid}`);
    console.log(`::set-output name=state::${completedDeployment.state}`);
    
  } catch (error) {
    console.error('');
    console.error('❌ Vercel deployment remediation failed:', error.message);
    console.error('');
    process.exit(1);
  }
}

// Execute the main function
await main();