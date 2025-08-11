#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Preflight script to check that .env.local exists and contains required keys
 */
function runPreflightChecks() {
  console.log('🚀 Running preflight checks...');
  
  const envLocalPath = path.join(__dirname, '..', '.env.local');
  const envExamplePath = path.join(__dirname, '..', '.env.local.example');
  
  // Check if .env.local exists
  if (!fs.existsSync(envLocalPath)) {
    console.error('❌ Preflight check failed: .env.local file not found');
    console.error('   Please copy .env.local.example to .env.local and set appropriate values');
    process.exit(1);
  }
  
  // Check if .env.local.example exists to get required keys
  if (!fs.existsSync(envExamplePath)) {
    console.error('❌ Preflight check failed: .env.local.example file not found');
    process.exit(1);
  }
  
  try {
    // Read both files
    const envLocalContent = fs.readFileSync(envLocalPath, 'utf8');
    const envExampleContent = fs.readFileSync(envExamplePath, 'utf8');
    
    // Extract keys from .env.local.example (lines that start with KEY=)
    const requiredKeys = envExampleContent
      .split('\n')
      .filter(line => line.trim() && !line.trim().startsWith('#'))
      .map(line => line.split('=')[0])
      .filter(key => key);
    
    // Extract keys from .env.local
    const localKeys = envLocalContent
      .split('\n')
      .filter(line => line.trim() && !line.trim().startsWith('#'))
      .map(line => {
        const idx = line.indexOf('=');
        return idx === -1 ? null : line.substring(0, idx).trim();
      })
      .filter(key => key);
    
    // Extract keys from .env.local
    const localKeys = envLocalContent
      .split('\n')
      .filter(line => line.trim() && !line.trim().startsWith('#'))
      .map(line => {
        const idx = line.indexOf('=');
        return idx === -1 ? null : line.substring(0, idx).trim();
      })
      .filter(key => key);
    
    // Check for missing keys
    const missingKeys = requiredKeys.filter(key => !localKeys.includes(key));
    
    if (missingKeys.length > 0) {
      console.error('❌ Preflight check failed: Missing required environment variables in .env.local:');
      missingKeys.forEach(key => console.error(`   - ${key}`));
      console.error('   Please check .env.local.example for reference');
      process.exit(1);
    }
    
    console.log('✅ Preflight checks passed: .env.local exists with all required keys');
    
  } catch (error) {
    console.error('❌ Preflight check failed: Error reading environment files');
    console.error(error.message);
    process.exit(1);
  }
}

runPreflightChecks();