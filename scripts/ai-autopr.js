#!/usr/bin/env node

/**
 * AI Auto-PR Script
 * 
 * This script generates pull requests using OpenAI based on instructions.
 * It collects repository context, calls OpenAI API, and creates PRs automatically.
 * 
 * No external dependencies - uses only Node.js built-ins.
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

// Configuration
const MAX_CONTEXT_BYTES = 50000; // Limit context to prevent token overflow
const OPENAI_MODEL = 'gpt-4o-mini';
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';

// File patterns to include/exclude
const INCLUDE_PATTERNS = [
  '**/*.js', '**/*.ts', '**/*.jsx', '**/*.tsx',
  '**/*.py', '**/*.json', '**/*.yml', '**/*.yaml', 
  '**/*.md', '**/*.txt', '**/*.env.example',
  '**/*.css', '**/*.scss', '**/*.html'
];

const EXCLUDE_PATTERNS = [
  'node_modules/**', '.git/**', 'dist/**', 'build/**', 
  '*.log', '*.tmp', '**/*.min.js', '**/*.min.css',
  '**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.gif', '**/*.svg',
  '**/*.pdf', '**/*.zip', '**/*.tar.gz', '**/*.exe', '**/*.dll'
];

// Environment variables
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const INSTRUCTION = process.env.INSTRUCTION;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const ISSUE_NUMBER = process.env.ISSUE_NUMBER;
const COMMENT_ID = process.env.COMMENT_ID;

/**
 * Execute shell command and return output
 */
function execCommand(command, options = {}) {
  try {
    const result = execSync(command, { 
      encoding: 'utf8', 
      stdio: 'pipe',
      ...options 
    });
    return result.trim();
  } catch (error) {
    console.error(`Command failed: ${command}`);
    console.error(error.message);
    throw error;
  }
}

/**
 * Check if file path matches any pattern using simple glob matching
 */
function matchesPattern(filePath, patterns) {
  return patterns.some(pattern => {
    // Convert glob pattern to regex
    const regexPattern = pattern
      .replace(/\./g, '\\.')
      .replace(/\*\*/g, '.*')
      .replace(/\*/g, '[^/]*');
    
    const regex = new RegExp(`^${regexPattern}$`);
    return regex.test(filePath) || regex.test(path.basename(filePath));
  });
}

/**
 * Check if file is likely binary
 */
function isBinaryFile(filePath) {
  try {
    const stats = fs.statSync(filePath);
    if (stats.size > 1024 * 1024) return true; // Files > 1MB considered binary
    
    const buffer = fs.readFileSync(filePath, { encoding: null });
    // Check for null bytes (common in binary files)
    for (let i = 0; i < Math.min(buffer.length, 512); i++) {
      if (buffer[i] === 0) return true;
    }
    return false;
  } catch (error) {
    return true; // If we can't read it, assume binary
  }
}

/**
 * Collect repository files based on patterns
 */
function collectRepoFiles() {
  console.log('📁 Collecting repository files...');
  
  try {
    // Get all files using git ls-files (respects .gitignore)
    const allFiles = execCommand('git ls-files').split('\n').filter(f => f.trim());
    
    const collectedFiles = [];
    let totalBytes = 0;
    
    for (const file of allFiles) {
      // Skip if matches exclude patterns
      if (matchesPattern(file, EXCLUDE_PATTERNS)) {
        continue;
      }
      
      // Skip if doesn't match include patterns
      if (!matchesPattern(file, INCLUDE_PATTERNS)) {
        continue;
      }
      
      // Skip binary files
      if (isBinaryFile(file)) {
        continue;
      }
      
      try {
        const content = fs.readFileSync(file, 'utf8');
        const fileBytes = Buffer.byteLength(content, 'utf8');
        
        // Check if adding this file would exceed limit
        if (totalBytes + fileBytes > MAX_CONTEXT_BYTES) {
          console.log(`⚠️  Skipping ${file} - would exceed context limit`);
          continue;
        }
        
        collectedFiles.push({ path: file, content });
        totalBytes += fileBytes;
        
      } catch (error) {
        console.log(`⚠️  Could not read ${file}: ${error.message}`);
      }
    }
    
    console.log(`✅ Collected ${collectedFiles.length} files (${totalBytes} bytes)`);
    return collectedFiles;
    
  } catch (error) {
    console.error('❌ Error collecting files:', error.message);
    throw error;
  }
}

/**
 * Make HTTPS request to OpenAI API using fetch
 */
async function callOpenAI(messages) {
  const body = JSON.stringify({
    model: OPENAI_MODEL,
    messages: messages,
    temperature: 0.7,
    max_tokens: 4000
  });

  try {
    const response = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENAI_API_KEY}`
      },
      body: body
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`OpenAI API error (${response.status}): ${errorData}`);
    }

    const data = await response.json();
    
    if (data.error) {
      throw new Error(`OpenAI API error: ${data.error.message}`);
    }
    
    return data;
    
  } catch (error) {
    throw new Error(`OpenAI API request failed: ${error.message}`);
  }
}

/**
 * Parse multi-file response from OpenAI
 */
function parseMultiFileResponse(content) {
  const files = [];
  const sections = content.split(/^--- (.+?) ---$/gm);
  
  for (let i = 1; i < sections.length; i += 2) {
    const filePath = sections[i].trim();
    const fileContent = sections[i + 1]?.trim();
    
    if (filePath && fileContent) {
      files.push({ path: filePath, content: fileContent });
    }
  }
  
  return files;
}

/**
 * Create and push new branch with changes
 */
function createAndPushBranch(files, instruction) {
  const timestamp = Date.now();
  const branchName = `ai-autopr-${timestamp}`;
  
  console.log(`🌿 Creating branch: ${branchName}`);
  
  try {
    // Create new branch
    execCommand(`git checkout -b ${branchName}`);
    
    // Write files
    let changedFiles = 0;
    for (const file of files) {
      console.log(`📝 Writing file: ${file.path}`);
      
      // Ensure directory exists
      const dir = path.dirname(file.path);
      if (dir !== '.' && !fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      // Write file content
      fs.writeFileSync(file.path, file.content, 'utf8');
      changedFiles++;
    }
    
    if (changedFiles === 0) {
      console.log('⚠️  No files to commit');
      return null;
    }
    
    // Stage changes
    execCommand('git add .');
    
    // Commit changes
    const commitMessage = `AI Auto-PR: ${instruction.substring(0, 50)}${instruction.length > 50 ? '...' : ''}`;
    execCommand(`git commit -m "${commitMessage}"`);
    
    // Push branch
    execCommand(`git push origin ${branchName}`);
    
    console.log(`✅ Pushed ${changedFiles} changed files to branch ${branchName}`);
    return branchName;
    
  } catch (error) {
    console.error('❌ Error creating branch:', error.message);
    throw error;
  }
}

/**
 * Create pull request using GitHub CLI
 */
function createPullRequest(branchName, instruction, files) {
  console.log('📥 Creating pull request...');
  
  try {
    const title = `AI Auto-PR: ${instruction.substring(0, 60)}${instruction.length > 60 ? '...' : ''}`;
    
    const body = `## AI-Generated Pull Request

**Instruction:** ${instruction}

**Files modified:**
${files.map(f => `- \`${f.path}\``).join('\n')}

**Generated by:** AI Auto-PR Bot
${ISSUE_NUMBER ? `**Related issue:** #${ISSUE_NUMBER}` : ''}

---
*This PR was automatically generated by AI. Please review carefully before merging.*`;

    // Create PR using gh CLI
    const prUrl = execCommand(`gh pr create --title "${title}" --body "${body}" --head ${branchName} --base main`);
    
    console.log(`✅ Created pull request: ${prUrl}`);
    return prUrl;
    
  } catch (error) {
    console.error('❌ Error creating pull request:', error.message);
    throw error;
  }
}

/**
 * Main execution function
 */
async function main() {
  console.log('🤖 AI Auto-PR Bot starting...');
  
  // Validate environment
  if (!OPENAI_API_KEY) {
    console.error('❌ OPENAI_API_KEY environment variable is required');
    process.exit(1);
  }
  
  if (!INSTRUCTION) {
    console.error('❌ INSTRUCTION environment variable is required');
    process.exit(1);
  }
  
  console.log(`📋 Instruction: ${INSTRUCTION}`);
  
  try {
    // Collect repository context
    const repoFiles = collectRepoFiles();
    
    // Build context for OpenAI
    const repoContext = repoFiles
      .map(file => `--- ${file.path} ---\n${file.content}`)
      .join('\n\n');
    
    console.log('🧠 Calling OpenAI API...');
    
    // Prepare messages for OpenAI
    const messages = [
      {
        role: 'system',
        content: `You are an expert software developer. You will be given a codebase and an instruction. Your task is to make the minimal necessary changes to implement the instruction.

IMPORTANT: Your response must contain only the modified files in this exact format:
--- path/to/file.ext ---
[file content here]

--- path/to/another/file.ext ---  
[file content here]

Guidelines:
- Make minimal changes - only modify what's necessary
- Preserve existing code structure and style
- Don't break existing functionality
- Include complete file contents for any file you modify
- If creating new files, include them with their full paths
- Do not include unchanged files in your response`
      },
      {
        role: 'user',
        content: `Repository files:\n\n${repoContext}\n\nInstruction: ${INSTRUCTION}`
      }
    ];
    
    // Call OpenAI API
    const response = await callOpenAI(messages);
    const aiResponse = response.choices[0].message.content;
    
    console.log('📝 Parsing AI response...');
    
    // Parse the multi-file response
    const modifiedFiles = parseMultiFileResponse(aiResponse);
    
    if (modifiedFiles.length === 0) {
      console.log('⚠️  No files found in AI response');
      console.log('AI Response:', aiResponse);
      process.exit(1);
    }
    
    console.log(`✅ Parsed ${modifiedFiles.length} files from AI response`);
    
    // Create branch and push changes
    const branchName = createAndPushBranch(modifiedFiles, INSTRUCTION);
    
    if (!branchName) {
      console.log('❌ No changes to commit');
      process.exit(1);
    }
    
    // Create pull request
    const prUrl = createPullRequest(branchName, INSTRUCTION, modifiedFiles);
    
    console.log('🎉 AI Auto-PR completed successfully!');
    console.log(`📥 Pull Request: ${prUrl}`);
    
  } catch (error) {
    console.error('❌ AI Auto-PR failed:', error.message);
    process.exit(1);
  }
}

// Run the script
main();