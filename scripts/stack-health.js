#!/usr/bin/env node

/**
 * Stack Health Monitor Script
 * 
 * This script monitors the health of the application stack by checking:
 * - Environment variables configuration
 * - Next.js build capability
 * - Supabase connectivity
 * - API health endpoints
 * 
 * Exit codes:
 * 0 - All checks passed
 * 1 - Environment configuration issues
 * 2 - Build failures
 * 3 - Supabase connectivity issues
 * 4 - Health endpoint issues
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

// Health check configuration
const REQUIRED_ENV_VARS = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY'
];

const FRONTEND_DIR = 'frontend';
const HEALTH_CHECK_TIMEOUT = 30000; // 30 seconds

/**
 * Execute shell command safely
 */
function execCommand(command, options = {}) {
  try {
    const result = execSync(command, { 
      encoding: 'utf8', 
      stdio: 'pipe',
      ...options 
    });
    return { success: true, output: result.trim() };
  } catch (error) {
    const stdout = error.stdout || '';
    const stderr = error.stderr || '';
    const combined = `${stdout}\n${stderr}`.trim();
    return { 
      success: false, 
      output: combined || error.message,
      code: error.status 
    };
  }
}

/**
 * Check for required environment variables
 */
function checkEnvironmentVariables() {
  console.log('🔍 Checking environment variables...');
  
  const issues = [];
  const envFiles = [
    path.join(FRONTEND_DIR, '.env.local'),
    path.join(FRONTEND_DIR, '.env'),
    '.env.local',
    '.env'
  ];
  
  let envFound = false;
  let envVars = {};
  
  // Try to find and read env files
  for (const envFile of envFiles) {
    if (fs.existsSync(envFile)) {
      envFound = true;
      try {
        const content = fs.readFileSync(envFile, 'utf8');
        // Parse env file
        content.split('\n').forEach(line => {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#')) {
            const [key, ...valueParts] = trimmed.split('=');
            if (key && valueParts.length > 0) {
              envVars[key.trim()] = valueParts.join('=').trim();
            }
          }
        });
      } catch (error) {
        console.log(`⚠️  Could not read ${envFile}: ${error.message}`);
      }
    }
  }
  
  // Also check process.env for environment variables
  for (const varName of REQUIRED_ENV_VARS) {
    if (process.env[varName]) {
      envVars[varName] = process.env[varName];
    }
  }
  
  // Check required variables
  for (const varName of REQUIRED_ENV_VARS) {
    if (!envVars[varName]) {
      issues.push(`Missing required environment variable: ${varName}`);
    } else if (envVars[varName].includes('your_') || envVars[varName].includes('placeholder')) {
      issues.push(`Environment variable ${varName} appears to be placeholder value`);
    }
  }
  
  if (!envFound && Object.keys(envVars).length === 0) {
    issues.push('No environment configuration files found (.env.local, .env)');
  }
  
  if (issues.length > 0) {
    console.log('❌ Environment issues found:');
    issues.forEach(issue => console.log(`   - ${issue}`));
    return { success: false, issues };
  }
  
  console.log('✅ Environment variables check passed');
  return { success: true, issues: [] };
}

/**
 * Check if Next.js build works
 */
function checkNextjsBuild() {
  console.log('🔨 Checking Next.js build capability...');
  
  if (!fs.existsSync(FRONTEND_DIR)) {
    const issue = 'Frontend directory not found';
    console.log(`❌ ${issue}`);
    return { success: false, issues: [issue] };
  }
  
  // Check if package.json exists
  const packageJsonPath = path.join(FRONTEND_DIR, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    const issue = 'Frontend package.json not found';
    console.log(`❌ ${issue}`);
    return { success: false, issues: [issue] };
  }
  
  // Check if node_modules exists
  const nodeModulesPath = path.join(FRONTEND_DIR, 'node_modules');
  if (!fs.existsSync(nodeModulesPath)) {
    console.log('📦 Installing dependencies first...');
    const installResult = execCommand(`cd ${FRONTEND_DIR} && npm install`, { 
      cwd: process.cwd(),
      timeout: 120000 
    });
    
    if (!installResult.success) {
      const issue = `npm install failed: ${installResult.output}`;
      console.log(`❌ ${issue}`);
      return { success: false, issues: [issue] };
    }
  }
  
  // Try to run Next.js build
  console.log('🏗️  Attempting Next.js build...');
  const buildResult = execCommand(`cd ${FRONTEND_DIR} && npm run build`, {
    cwd: process.cwd(),
    timeout: 180000 // 3 minutes timeout for build
  });
  
  if (!buildResult.success) {
    const issue = `Next.js build failed: ${buildResult.output}`;
    console.log(`❌ ${issue}`);
    return { success: false, issues: [issue] };
  }
  
  console.log('✅ Next.js build check passed');
  return { success: true, issues: [] };
}

/**
 * Check Supabase configuration
 */
function checkSupabaseConfig() {
  console.log('🔗 Checking Supabase configuration...');
  
  const issues = [];
  
  // Check if Supabase client can be initialized
  const supabaseLibPath = path.join(FRONTEND_DIR, 'lib');
  if (fs.existsSync(supabaseLibPath)) {
    const files = fs.readdirSync(supabaseLibPath);
    const supabaseFiles = files.filter(file => 
      file.toLowerCase().includes('supabase') && 
      (file.endsWith('.js') || file.endsWith('.ts'))
    );
    
    if (supabaseFiles.length === 0) {
      issues.push('No Supabase client configuration file found in lib/');
    } else {
      // Check if the Supabase client file has proper structure
      for (const file of supabaseFiles) {
        try {
          const content = fs.readFileSync(path.join(supabaseLibPath, file), 'utf8');
          if (!content.includes('createClient') && !content.includes('@supabase/supabase-js')) {
            issues.push(`Supabase client file ${file} may not be properly configured`);
          }
        } catch (error) {
          issues.push(`Could not read Supabase client file ${file}: ${error.message}`);
        }
      }
    }
  } else {
    issues.push('lib/ directory not found - Supabase client may not be configured');
  }
  
  if (issues.length > 0) {
    console.log('❌ Supabase configuration issues found:');
    issues.forEach(issue => console.log(`   - ${issue}`));
    return { success: false, issues };
  }
  
  console.log('✅ Supabase configuration check passed');
  return { success: true, issues: [] };
}

/**
 * Check for health endpoint
 */
function checkHealthEndpoint() {
  console.log('🏥 Checking health endpoint...');
  
  const healthEndpoints = [
    path.join(FRONTEND_DIR, 'pages', 'api', 'health.js'),
    path.join(FRONTEND_DIR, 'pages', 'api', 'health.ts'),
    path.join(FRONTEND_DIR, 'app', 'api', 'health', 'route.js'),
    path.join(FRONTEND_DIR, 'app', 'api', 'health', 'route.ts')
  ];
  
  const healthEndpointExists = healthEndpoints.some(endpoint => fs.existsSync(endpoint));
  
  if (!healthEndpointExists) {
    const issue = 'Health endpoint not found (pages/api/health.js|ts or app/api/health/route.js|ts)';
    console.log(`❌ ${issue}`);
    return { success: false, issues: [issue] };
  }
  
  console.log('✅ Health endpoint check passed');
  return { success: true, issues: [] };
}

/**
 * Generate fix instruction based on detected issues
 */
function generateFixInstruction(results) {
  const allIssues = results.flatMap(result => result.issues);
  
  if (allIssues.length === 0) {
    return null;
  }
  
  let instruction = 'Fix detected stack issues: ';
  const fixes = [];
  
  // Environment variable issues
  if (allIssues.some(issue => issue.includes('NEXT_PUBLIC_SUPABASE'))) {
    fixes.push('ensure NEXT_PUBLIC_SUPABASE_URL/ANON_KEY are properly configured and read only on client');
  }
  
  // Build issues
  if (allIssues.some(issue => issue.includes('build failed'))) {
    fixes.push('fix Next.js build errors');
    fixes.push('move Supabase init out of build-time');
  }
  
  // Supabase config issues
  if (allIssues.some(issue => issue.includes('Supabase'))) {
    fixes.push('fix Supabase client configuration');
  }
  
  // Health endpoint issues
  if (allIssues.some(issue => issue.includes('Health endpoint'))) {
    fixes.push('add health route at /api/health');
  }
  
  if (fixes.length === 0) {
    fixes.push('resolve configuration and build issues');
  }
  
  instruction += fixes.join('; ');
  return instruction;
}

/**
 * Main health check execution
 */
async function main() {
  console.log('🏥 Stack Health Monitor starting...');
  console.log('=' .repeat(50));
  
  const results = [];
  let exitCode = 0;
  
  try {
    // Run all health checks
    const envCheck = checkEnvironmentVariables();
    results.push(envCheck);
    
    const buildCheck = checkNextjsBuild();
    results.push(buildCheck);
    
    const supabaseCheck = checkSupabaseConfig();
    results.push(supabaseCheck);
    
    const healthCheck = checkHealthEndpoint();
    results.push(healthCheck);
    
    // Determine exit code based on issues
    if (!envCheck.success) exitCode = 1;
    else if (!buildCheck.success) exitCode = 2;
    else if (!supabaseCheck.success) exitCode = 3;
    else if (!healthCheck.success) exitCode = 4;
    
    console.log('=' .repeat(50));
    
    if (exitCode === 0) {
      console.log('✅ All health checks passed!');
    } else {
      console.log('❌ Health check failures detected');
      
      // Generate fix instruction for AI Auto PR
      const fixInstruction = generateFixInstruction(results);
      if (fixInstruction) {
        console.log('🤖 Suggested fix instruction:');
        console.log(`   ${fixInstruction}`);
        
        // Output instruction in a format that can be captured by the workflow
        console.log('---FIX-INSTRUCTION---');
        console.log(fixInstruction);
        console.log('---END-FIX-INSTRUCTION---');
      }
    }
    
  } catch (error) {
    console.error('❌ Health check script failed:', error.message);
    exitCode = 99;
  }
  
  process.exit(exitCode);
}

// Run the health check
main();