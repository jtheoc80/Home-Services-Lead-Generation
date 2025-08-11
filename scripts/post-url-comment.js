#!/usr/bin/env node

/**
 * Post URL Comment Script
 * 
 * This script posts a comment with the Railway service URL to a GitHub commit or PR
 * when running in a GitHub Actions environment.
 */

// Read environment variables
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_REPOSITORY = process.env.GITHUB_REPOSITORY;
const GITHUB_SHA = process.env.GITHUB_SHA;
const GITHUB_EVENT_NAME = process.env.GITHUB_EVENT_NAME;
const GITHUB_REF = process.env.GITHUB_REF;
const PUBLIC_URL = process.argv[2];

// Check if we have the minimum required environment
if (!GITHUB_TOKEN || !GITHUB_REPOSITORY || !GITHUB_SHA) {
  console.log('ℹ️  GitHub environment not fully configured, skipping comment posting');
  process.exit(0);
}

if (!PUBLIC_URL) {
  console.error('❌ Error: Public URL must be provided as first argument');
  process.exit(1);
}

console.log('💬 Preparing to post GitHub comment...');
console.log(`📋 Repository: ${GITHUB_REPOSITORY}`);
console.log(`📋 SHA: ${GITHUB_SHA.substring(0, 7)}`);
console.log(`📋 Event: ${GITHUB_EVENT_NAME}`);
console.log(`📋 URL: ${PUBLIC_URL}`);

/**
 * Make a GitHub API request
 */
async function makeGitHubRequest(endpoint, method = 'GET', body = null) {
  try {
    const url = `https://api.github.com/repos/${GITHUB_REPOSITORY}${endpoint}`;
    
    const options = {
      method,
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'User-Agent': 'Railway-Expose-Script'
      }
    };

    if (body) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`GitHub API ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ GitHub API request failed:', error.message);
    throw error;
  }
}

/**
 * Find the PR number for the current commit/branch
 */
async function findPullRequestNumber() {
  try {
    // First, try to get PRs for the current commit
    const commitPRs = await makeGitHubRequest(`/commits/${GITHUB_SHA}/pulls`);
    
    if (commitPRs.length > 0) {
      return commitPRs[0].number;
    }

    // If no PR found for commit, try to find PR for the branch
    if (GITHUB_REF && GITHUB_REF.startsWith('refs/heads/')) {
      const branch = GITHUB_REF.replace('refs/heads/', '');
      const branchPRs = await makeGitHubRequest(`/pulls?head=${encodeURIComponent(`${GITHUB_REPOSITORY.split('/')[0]}:${branch}`)}&state=open`);
      
      if (branchPRs.length > 0) {
        return branchPRs[0].number;
      }
    }

    return null;
  } catch (error) {
    console.warn('⚠️  Could not determine PR number:', error.message);
    return null;
  }
}

/**
 * Post comment to a pull request
 */
async function postPullRequestComment(prNumber, message) {
  const body = {
    body: message
  };

  console.log(`💬 Posting comment to PR #${prNumber}...`);
  await makeGitHubRequest(`/issues/${prNumber}/comments`, 'POST', body);
  console.log('✅ Comment posted successfully');
}

/**
 * Post comment to a commit
 */
async function postCommitComment(message) {
  const body = {
    body: message
  };

  console.log(`💬 Posting comment to commit ${GITHUB_SHA.substring(0, 7)}...`);
  await makeGitHubRequest(`/commits/${GITHUB_SHA}/comments`, 'POST', body);
  console.log('✅ Comment posted successfully');
}

/**
 * Generate the comment message
 */
function generateCommentMessage() {
  const timestamp = new Date().toISOString();
  
  return `## 🚀 Railway Service Deployed

Your Railway service has been successfully exposed and is now available at:

**🔗 Public URL:** ${PUBLIC_URL}

---
*Automated comment posted at ${timestamp}*`;
}

/**
 * Main execution function
 */
async function main() {
  try {
    const message = generateCommentMessage();
    
    // Try to post to PR first, fall back to commit comment
    const prNumber = await findPullRequestNumber();
    
    if (prNumber) {
      await postPullRequestComment(prNumber, message);
    } else {
      console.log('ℹ️  No PR found, posting commit comment instead');
      await postCommitComment(message);
    }
    
    console.log('');
    console.log('🎉 Comment posted successfully!');
    console.log('');
    
  } catch (error) {
    console.error('');
    console.error('❌ Failed to post GitHub comment:', error.message);
    console.error('ℹ️  This is not a critical failure - the service is still deployed');
    console.error('');
    // Don't exit with error code as this is optional functionality
    process.exit(0);
  }
}

// Execute the main function
await main();