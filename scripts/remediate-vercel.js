#!/usr/bin/env node

/**
 * Vercel Deployment Remediation Script
 * 
 * This script uses Vercel's CLI to trigger a new deployment.
 * It executes `vercel deploy --prebuilt --prod` to create a production deployment.
 * 
 * Requirements:
 * - VERCEL_TOKEN: Vercel API token
 * - Must have vercel CLI available or use Vercel API directly
 * 
 * Uses only Node.js built-ins, no external dependencies.
 */

import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const VERCEL_TOKEN = process.env.VERCEL_TOKEN;

// Input validation
if (!VERCEL_TOKEN) {
  console.error('❌ Error: VERCEL_TOKEN environment variable is required');
  process.exit(1);
}

console.log('🚀 Starting Vercel deployment remediation...');

/**
 * Execute a shell command and return the result
 */
function execCommand(command, args = []) {
  return new Promise((resolve, reject) => {
    const childProcess = spawn(command, args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, VERCEL_TOKEN }
    });

    let stdout = '';
    let stderr = '';

    childProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    childProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    childProcess.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr, code });
      } else {
        reject(new Error(`Command failed with code ${code}: ${stderr || stdout}`));
      }
    });

    childProcess.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * Main execution function
 */
async function main() {
  try {
    console.log('🔄 Triggering Vercel production deployment...');
    
    // Execute vercel deploy --prebuilt --prod
    const result = await execCommand('npx', ['vercel', 'deploy', '--prebuilt', '--prod', '--yes']);
    
    // Parse the output to extract deployment URL
    const output = result.stdout + result.stderr;
    console.log('📄 Deployment output:');
    console.log(output);
    
    // Look for deployment URL in the output
    const urlMatch = output.match(/https:\/\/[^\s]+/);
    const deploymentUrl = urlMatch ? urlMatch[0] : null;
    
    // Print results
    console.log('');
    console.log('🎉 Vercel deployment completed successfully!');
    
    if (deploymentUrl) {
      console.log(`🔗 New URL: ${deploymentUrl}`);
    } else {
      console.log('⚠️  Could not extract deployment URL from output');
    }
    
    console.log(`📊 Exit code: ${result.code}`);
    console.log('');
    
    // Output for automation tools
    if (deploymentUrl) {
      console.log(`::set-output name=deployment_url::${deploymentUrl}`);
    }
    console.log(`::set-output name=status::success`);
    
    // GitHub Actions output file support
    const githubOutput = process.env.GITHUB_OUTPUT;
    if (githubOutput) {
      const outputs = [];
      if (deploymentUrl) {
        outputs.push(`deployment_url=${deploymentUrl}`);
      }
      outputs.push(`status=success`);
      writeFileSync(githubOutput, outputs.join('\n') + '\n', { flag: 'a' });
    }
    
    process.exit(0);
    
  } catch (error) {
    console.error('');
    console.error('❌ Vercel deployment failed:', error.message);
    console.error('');
    
    // Output failure status
    console.log(`::set-output name=status::failed`);
    const githubOutput = process.env.GITHUB_OUTPUT;
    if (githubOutput) {
      writeFileSync(githubOutput, `status=failed\n`, { flag: 'a' });
    }
    
    process.exit(1);
  }
}

// Execute the main function
await main();
