#!/usr/bin/env node

/**
 * Test script to validate health endpoints implementation
 * 
 * This script tests:
 * 1. Backend /healthz endpoint returns {status:"ok", db:"connected"|"down"}
 * 2. Frontend /api/health endpoint tests Supabase client init and proxies backend
 * 3. Stack health monitor hits both endpoints
 */

import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const results = [];

function log(message) {
  console.log(`[TEST] ${message}`);
  results.push(message);
}

async function makeRequest(url, timeout = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    const data = await response.json();
    return { ok: response.ok, status: response.status, data };
  } catch (error) {
    clearTimeout(timeoutId);
    return { ok: false, error: error.message };
  }
}

async function startServer(command, cwd, env) {
  return new Promise((resolve, reject) => {
    const serverProcess = spawn('sh', ['-c', command], { 
      cwd, 
      env: { ...process.env, ...env },
      stdio: 'pipe'
    });
    
    let output = '';
    serverProcess.stdout.on('data', (data) => {
      output += data.toString();
      // Check if server is ready
      if (output.includes('Uvicorn running on') || output.includes('Ready in')) {
        resolve(serverProcess);
      }
    });
    
    serverProcess.stderr.on('data', (data) => {
      output += data.toString();
    });
    
    serverProcess.on('error', reject);
    
    // Timeout after 30 seconds
    setTimeout(() => {
      reject(new Error('Server startup timeout'));
    }, 30000);
  });
}

async function runTests() {
  log('Starting health endpoints validation tests...');
  
  // Test environment variables
  const testEnv = {
    SUPABASE_JWT_SECRET: 'test_secret',
    SUPABASE_URL: 'https://test.supabase.co',
    SUPABASE_SERVICE_ROLE: 'test_service_role',
    NEXT_PUBLIC_SUPABASE_URL: 'https://test.supabase.co',
    NEXT_PUBLIC_SUPABASE_ANON_KEY: 'test_anon_key',
    NEXT_PUBLIC_API_BASE: 'http://localhost:8000'
  };
  
  let backendProcess, frontendProcess;
  
  try {
    // Start backend server
    log('Starting backend server...');
    backendProcess = await startServer(
      'python main.py',
      './backend',
      testEnv
    );
    log('✅ Backend server started');
    
    // Wait a moment for server to fully initialize
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Test backend /healthz endpoint
    log('Testing backend /healthz endpoint...');
    const backendHealth = await makeRequest('http://localhost:8000/healthz');
    
    if (backendHealth.ok && backendHealth.data.status === 'ok') {
      log('✅ Backend /healthz endpoint works correctly');
      log(`   - Status: ${backendHealth.data.status}`);
      log(`   - DB: ${backendHealth.data.db}`);
      log(`   - Version: ${backendHealth.data.version}`);
    } else {
      log('❌ Backend /healthz endpoint failed');
      log(`   - Error: ${backendHealth.error || JSON.stringify(backendHealth.data)}`);
    }
    
    // Start frontend server
    log('Starting frontend server...');
    frontendProcess = await startServer(
      'npm run dev',
      './frontend',
      testEnv
    );
    log('✅ Frontend server started');
    
    // Wait a moment for server to fully initialize
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Test frontend /api/health endpoint
    log('Testing frontend /api/health endpoint...');
    const frontendHealth = await makeRequest('http://localhost:3000/api/health');
    
    if (frontendHealth.ok) {
      log('✅ Frontend /api/health endpoint works correctly');
      log(`   - Overall status: ${frontendHealth.data.status}`);
      log(`   - Supabase initialized: ${frontendHealth.data.supabase.initialized}`);
      log(`   - Supabase message: ${frontendHealth.data.supabase.message}`);
      log(`   - Backend status: ${frontendHealth.data.backend.status}`);
      log(`   - Backend DB: ${frontendHealth.data.backend.db}`);
    } else {
      log('❌ Frontend /api/health endpoint failed');
      log(`   - Error: ${frontendHealth.error || JSON.stringify(frontendHealth.data)}`);
    }
    
    // Test stack health monitor
    log('Testing stack health monitor...');
    const stackHealthProcess = spawn('node', ['scripts/stack-health.js'], {
      env: {
        ...process.env,
        FRONTEND_URL: 'http://localhost:3000',
        RAILWAY_URL: 'http://localhost:8000',
        RAILWAY_TOKEN: 'fake_token',
        SUPABASE_URL: 'https://test.supabase.co',
        SUPABASE_SERVICE_ROLE: 'test_service_role'
      },
      stdio: 'pipe'
    });
    
    let stackOutput = '';
    stackHealthProcess.stdout.on('data', (data) => {
      stackOutput += data.toString();
    });
    
    stackHealthProcess.stderr.on('data', (data) => {
      stackOutput += data.toString();
    });
    
    await new Promise((resolve) => {
      stackHealthProcess.on('close', (code) => {
        if (stackOutput.includes('Health check passed: http://localhost:3000/api/health')) {
          log('✅ Stack health monitor hits frontend /api/health endpoint');
        } else {
          log('❌ Stack health monitor does not hit frontend /api/health endpoint');
        }
        
        if (stackOutput.includes('backend healthz')) {
          log('✅ Stack health monitor checks backend /healthz endpoint');
        } else {
          log('❌ Stack health monitor does not check backend /healthz endpoint');
        }
        
        resolve();
      });
    });
    
    log('Tests completed successfully!');
    
  } catch (error) {
    log(`❌ Test failed: ${error.message}`);
  } finally {
    // Clean up processes
    if (backendProcess) {
      log('Stopping backend server...');
      backendProcess.kill('SIGTERM');
    }
    if (frontendProcess) {
      log('Stopping frontend server...');
      frontendProcess.kill('SIGTERM');
    }
  }
  
  // Write results to file
  writeFileSync('health_endpoints_test_results.txt', results.join('\n'));
  log('Test results written to health_endpoints_test_results.txt');
}

// Run tests
runTests().catch(console.error);