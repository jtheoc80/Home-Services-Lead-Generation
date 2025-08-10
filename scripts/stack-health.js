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

const FRONTEND_DIR = process.env.FRONTEND_DIR || 'frontend';

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
 * Check for required environment variables and detect specific patterns
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
  
  // Check required variables with specific error patterns
  for (const varName of REQUIRED_ENV_VARS) {
    if (!envVars[varName]) {
      issues.push(`NEXT_PUBLIC_* missing: ${varName} is required but not found`);
    } else if (envVars[varName].includes('your_') || envVars[varName].includes('placeholder')) {
      issues.push(`NEXT_PUBLIC_* missing: ${varName} appears to be placeholder value`);
    }
  }
  
  if (!envFound && Object.keys(envVars).length === 0) {
    issues.push('NEXT_PUBLIC_* missing: No environment configuration files found (.env.local, .env)');
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
 * Check if Next.js build works and detect build-time Supabase issues
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
    const buildOutput = buildResult.output;
    const issues = [];
    
    // Check for specific patterns that indicate code/config issues
    if (buildOutput.includes('supabaseKey is required') || 
        buildOutput.includes('createClient') ||
        buildOutput.includes('Supabase')) {
      issues.push(`supabaseKey is required: Supabase client initialization failed during build - ${buildOutput}`);
    } else if (buildOutput.includes('NEXT_PUBLIC_')) {
      issues.push(`NEXT_PUBLIC_* missing: Environment variables not available during build - ${buildOutput}`);
    } else {
      issues.push(`Next.js build failed: ${buildOutput}`);
    }
    
    console.log(`❌ Build failed with issues:`);
    issues.forEach(issue => console.log(`   - ${issue}`));
    return { success: false, issues };
  }
  
  console.log('✅ Next.js build check passed');
  return { success: true, issues: [] };
}

/**
 * Check Supabase configuration and detect client-side issues
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
      issues.push('supabaseKey is required: No Supabase client configuration file found in lib/');
    } else {
      // Check if the Supabase client file has proper structure
      for (const file of supabaseFiles) {
        try {
          const content = fs.readFileSync(path.join(supabaseLibPath, file), 'utf8');
          
          // Check for server-side usage patterns that should be client-only
          if (content.includes('process.env') && !content.includes('NEXT_PUBLIC_')) {
          const supabaseEnvRegex = /process\.env\.(SUPABASE_URL|SUPABASE_ANON_KEY)/;
          const nextPublicEnvRegex = /process\.env\.NEXT_PUBLIC_SUPABASE_(URL|ANON_KEY)/;
          if (supabaseEnvRegex.test(content) && !nextPublicEnvRegex.test(content)) {
            issues.push(`supabaseKey is required: Supabase client in ${file} uses server-side Supabase environment variables (SUPABASE_URL or SUPABASE_ANON_KEY) instead of NEXT_PUBLIC_SUPABASE_*`);
          }
          
          if (!content.includes('createClient') && !content.includes('@supabase/supabase-js')) {
            issues.push(`supabaseKey is required: Supabase client file ${file} may not be properly configured`);
          }
        } catch (error) {
          issues.push(`supabaseKey is required: Could not read Supabase client file ${file}: ${error.message}`);
        }
      }
    }
  } else {
    issues.push('supabaseKey is required: lib/ directory not found - Supabase client may not be configured');
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
 * Check for Railway port binding issues
 */
function checkRailwayConfig() {
  console.log('🚂 Checking Railway configuration...');
  
  const issues = [];
  
  // Check for Dockerfile port configuration
  const dockerfilePath = 'Dockerfile';
  if (fs.existsSync(dockerfilePath)) {
    try {
      const dockerfileContent = fs.readFileSync(dockerfilePath, 'utf8');
      
      // Check if port is properly exposed
      if (!dockerfileContent.includes('EXPOSE')) {
        issues.push('port not bound: Dockerfile missing EXPOSE directive');
      }
      
      // Check for Railway-specific port binding
      if (!dockerfileContent.includes('$PORT') && !dockerfileContent.includes('${PORT}')) {
        issues.push('port not bound: Dockerfile not configured for Railway dynamic port binding ($PORT)');
      }
    } catch (error) {
      issues.push(`port not bound: Could not read Dockerfile: ${error.message}`);
    }
  } else {
    issues.push('port not bound: Dockerfile not found for Railway deployment');
  }
  
  // Check for start script configuration
  if (fs.existsSync(path.join(FRONTEND_DIR, 'package.json'))) {
    try {
      const packageContent = fs.readFileSync(path.join(FRONTEND_DIR, 'package.json'), 'utf8');
      const packageJson = JSON.parse(packageContent);
      
      if (!packageJson.scripts || !packageJson.scripts.start) {
        issues.push('port not bound: No start script found in package.json for Railway deployment');
      }
    } catch (error) {
      issues.push(`port not bound: Could not parse frontend package.json: ${error.message}`);
    }
  }
  
  if (issues.length > 0) {
    console.log('❌ Railway configuration issues found:');
    issues.forEach(issue => console.log(`   - ${issue}`));
    return { success: false, issues };
  }
  
  console.log('✅ Railway configuration check passed');
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
  
  // Check for specific patterns that require the requested fix instruction
  const hasSupabaseKeyIssue = allIssues.some(issue => issue.includes('supabaseKey is required'));
  const hasNextPublicIssue = allIssues.some(issue => issue.includes('NEXT_PUBLIC_* missing'));
  const hasPortBindingIssue = allIssues.some(issue => issue.includes('port not bound'));
  
  // If we have the specific code/config issues mentioned in the problem statement
  if (hasSupabaseKeyIssue || hasNextPublicIssue || hasPortBindingIssue) {
    return "Fix Next build/Supabase init: move Supabase client to client-only, ensure NEXT_PUBLIC_SUPABASE_* used only in browser, add /api/health, and adjust Dockerfile for Railway standalone.";
  }
  
  // Otherwise, generate a more generic fix instruction
  let instruction = 'Fix detected stack issues: ';
  const fixes = [];
  
  // Environment variable issues
  if (allIssues.some(issue => issue.includes('NEXT_PUBLIC_SUPABASE'))) {
    fixes.push('ensure NEXT_PUBLIC_SUPABASE_URL/ANON_KEY are properly configured');
  }
  
  // Build issues
  if (allIssues.some(issue => issue.includes('build failed'))) {
    fixes.push('fix Next.js build errors');
  }
  
  // Supabase config issues
  if (allIssues.some(issue => issue.includes('Supabase'))) {
    fixes.push('fix Supabase client configuration');
  }
  
  // Health endpoint issues
  if (allIssues.some(issue => issue.includes('Health endpoint'))) {
    fixes.push('add health route at /api/health');
  }
  
  // Railway issues
  if (allIssues.some(issue => issue.includes('Railway') || issue.includes('Dockerfile'))) {
    fixes.push('fix Railway deployment configuration');
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
    
    const railwayCheck = checkRailwayConfig();
    results.push(railwayCheck);
    
    // Determine exit code based on issues (prioritize first failure, but allow multiple issues)
    if (!envCheck.success) exitCode = 1;
    else if (!buildCheck.success) exitCode = 2;
    else if (!supabaseCheck.success) exitCode = 3;
    else if (!healthCheck.success) exitCode = 4;
    else if (!railwayCheck.success) exitCode = 5;
    
    // If we have both environment and other issues, keep environment as primary but note others
    const hasMultipleIssues = [envCheck, buildCheck, supabaseCheck, healthCheck, railwayCheck]
      .filter(check => !check.success).length > 1;
    
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