#!/usr/bin/env node
/**
 * Harris County permit scraping wrapper script
 * Converts --since=3d format to --days argument for permit_leads CLI
 */

const { spawn } = require('child_process');
const path = require('path');

function parseTimeString(timeStr) {
  const match = timeStr.match(/^(\d+)([dhm])$/);
  if (!match) {
    throw new Error(`Invalid time format: ${timeStr}. Use format like 3d, 24h, 5m`);
  }
  
  const [, value, unit] = match;
  const num = parseInt(value, 10);
  
  switch (unit) {
    case 'd': return num; // days
    case 'h': return Math.max(1, Math.ceil(num / 24)); // hours to days (round up, at least 1)
    case 'm': return Math.max(1, Math.ceil(num / (24 * 60))); // minutes to days (round up, at least 1)
    default: throw new Error(`Unknown time unit: ${unit}`);
  }
}

function main() {
  const args = process.argv.slice(2);
  const permitLeadsArgs = ['scrape', '--jurisdiction', 'tx-harris'];
  
  // Parse arguments
  let sinceValue = '7'; // default to 7 days
  let otherArgs = [];
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('--since=')) {
      sinceValue = arg.split('=')[1];
    } else if (arg === '--since') {
      sinceValue = args[++i];
    } else {
      otherArgs.push(arg);
    }
  }
  
  // Convert since to days
  try {
    const days = parseTimeString(sinceValue);
    permitLeadsArgs.push('--days', days.toString());
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
  
  // Add other arguments
  permitLeadsArgs.push(...otherArgs);
  
  console.log('Running:', 'python -m permit_leads', permitLeadsArgs.join(' '));
  
  // Execute the permit_leads command
  const child = spawn('python', ['-m', 'permit_leads', ...permitLeadsArgs], {
    stdio: 'inherit',
    cwd: path.join(__dirname, '..')
  });
  
  child.on('close', (code) => {
    process.exit(code);
  });
  
  child.on('error', (error) => {
    console.error('Failed to start permit_leads:', error);
    process.exit(1);
  });
}

if (require.main === module) {
  main();
}