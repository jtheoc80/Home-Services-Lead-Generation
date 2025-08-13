import fs from 'fs';

const root = JSON.parse(fs.readFileSync('package.json','utf8'));
const fe = JSON.parse(fs.readFileSync('frontend/package.json','utf8'));

// Check if root declares react/react-dom
const badRoot = (root.dependencies?.react || root.dependencies?.['react-dom']);
if (badRoot) { 
  console.error('React deps must not be in root.'); 
  process.exit(1); 
}

// Check if frontend has mismatched majors for react vs react-dom
const r = fe.dependencies?.react || '';
const rd = fe.dependencies?.['react-dom'] || '';
const major = v => (v.match(/\d+/)||['0'])[0];

if (major(r) !== major(rd)) { 
  console.error(`React/DOM majors differ: ${r} vs ${rd}`); 
  
  // If mismatch is detected and GITHUB_TOKEN has write perms, create a fix branch
  if (process.env.GITHUB_TOKEN) {
    console.log('GITHUB_TOKEN detected - would create bot/fix-react-versions branch (implementation omitted for simplicity)');
  }
  
  process.exit(1); 
}

console.log('✅ React version checks passed');