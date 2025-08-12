#!/usr/bin/env tsx

import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { globby } from 'globby';
import * as yaml from 'yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface ConflictStrategy {
  theirs?: string[];
  ours?: string[];
}

interface ConfigFile {
  strategies: {
    [key: string]: ConflictStrategy;
  };
}

class ConflictResolver {
  private strategy: string;
  private config: ConfigFile;

  constructor(strategy: string = 'safe') {
    this.strategy = strategy;
    this.config = this.loadConfig();
  }

  private loadConfig(): ConfigFile {
    const configPath = join(__dirname, '../../.github/auto-resolve.yml');
    
    if (existsSync(configPath)) {
      try {
        const configContent = readFileSync(configPath, 'utf8');
        return yaml.parse(configContent) as ConfigFile;
      } catch (error) {
        console.warn(`Warning: Failed to parse config file: ${error}`);
      }
    }

    // Default configuration if file doesn't exist or parsing fails
    return {
      strategies: {
        safe: {
          theirs: [
            '**/*lock*.json',
            '**/pnpm-lock.yaml',
            '**/yarn.lock',
            'package-lock.json',
            '**/*.md',
            '.github/**'
          ],
          ours: [
            '**/.env.example'
          ]
        }
      }
    };
  }

  private async getConflictedFiles(): Promise<string[]> {
    try {
      const output = execSync('git diff --name-only --diff-filter=U', { encoding: 'utf8' });
      return output.trim().split('\n').filter(file => file.length > 0);
    } catch (error) {
      console.error('Failed to get conflicted files:', error);
      return [];
    }
  }

  private isBinaryFile(filePath: string): boolean {
    try {
      // Check if file is binary by looking for null bytes in first 8000 bytes
      const buffer = readFileSync(filePath);
      const sample = buffer.subarray(0, Math.min(8000, buffer.length));
      return sample.includes(0);
    } catch {
      return false;
    }
  }

  private async matchesPattern(filePath: string, patterns: string[]): Promise<boolean> {
    if (!patterns || patterns.length === 0) return false;
    
    try {
      const matched = await globby([filePath], { 
        patterns,
        cwd: process.cwd(),
        absolute: false 
      });
      const matchedFiles = await globby(patterns, { 
        cwd: process.cwd(),
        absolute: false 
      });
      return matchedFiles.includes(filePath);
    } catch {
      // Fallback to simple pattern matching if globby fails
      return patterns.some(pattern => {
        const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
        return regex.test(filePath);
      });
    }
  }

  private async resolveFile(filePath: string, resolution: 'theirs' | 'ours'): Promise<boolean> {
    try {
      execSync(`git checkout --${resolution} "${filePath}"`, { stdio: 'pipe' });
      execSync(`git add "${filePath}"`, { stdio: 'pipe' });
      console.log(`✓ Resolved ${filePath} using --${resolution}`);
      return true;
    } catch (error) {
      console.error(`✗ Failed to resolve ${filePath} using --${resolution}:`, error);
      return false;
    }
  }

  private shouldSkipCriticalFile(filePath: string): boolean {
    const criticalFiles = [
      'package.json',
      'tsconfig.json',
      'pyproject.toml',
      'setup.py'
    ];

    const fileName = filePath.split('/').pop() || '';
    return criticalFiles.includes(fileName) && this.strategy === 'safe';
  }

  async resolve(): Promise<void> {
    console.log(`🔄 Starting conflict resolution with strategy: ${this.strategy}`);
    
    // Validate strategy first
    const strategyConfig = this.config.strategies[this.strategy];
    if (!strategyConfig && !['theirs-all', 'ours-all'].includes(this.strategy)) {
      console.error(`❌ Unknown strategy: ${this.strategy}`);
      console.log('Available strategies:', [...Object.keys(this.config.strategies), 'theirs-all', 'ours-all']);
      process.exit(1);
    }
    
    const conflictedFiles = await this.getConflictedFiles();
    if (conflictedFiles.length === 0) {
      console.log('✅ No conflicted files found');
      return;
    }

    console.log(`📋 Found ${conflictedFiles.length} conflicted files:`);
    conflictedFiles.forEach(file => console.log(`   - ${file}`));

    let resolvedCount = 0;
    const unresolvedFiles: string[] = [];

    for (const filePath of conflictedFiles) {
      console.log(`\n🔍 Processing: ${filePath}`);

      // Skip binary files
      if (this.isBinaryFile(filePath)) {
        console.log(`⚠️  Skipping binary file: ${filePath}`);
        unresolvedFiles.push(filePath);
        continue;
      }

      // Skip critical files in safe mode
      if (this.shouldSkipCriticalFile(filePath)) {
        console.log(`⚠️  Skipping critical file in safe mode: ${filePath}`);
        unresolvedFiles.push(filePath);
        continue;
      }

      let resolved = false;

      // Handle specific strategies
      if (this.strategy === 'theirs-all') {
        resolved = await this.resolveFile(filePath, 'theirs');
      } else if (this.strategy === 'ours-all') {
        resolved = await this.resolveFile(filePath, 'ours');
      } else if (strategyConfig) {
        // Use pattern-based resolution
        if (strategyConfig.theirs && await this.matchesPattern(filePath, strategyConfig.theirs)) {
          resolved = await this.resolveFile(filePath, 'theirs');
        } else if (strategyConfig.ours && await this.matchesPattern(filePath, strategyConfig.ours)) {
          resolved = await this.resolveFile(filePath, 'ours');
        } else {
          console.log(`⚠️  No matching pattern for: ${filePath} (skipping)`);
          unresolvedFiles.push(filePath);
        }
      } else {
        console.log(`⚠️  No strategy configuration for: ${this.strategy} (skipping)`);
        unresolvedFiles.push(filePath);
      }

      if (resolved) {
        resolvedCount++;
      } else if (!unresolvedFiles.includes(filePath)) {
        unresolvedFiles.push(filePath);
      }
    }

    // Verify no conflicts remain
    const remainingConflicts = await this.getConflictedFiles();
    
    console.log(`\n📊 Resolution Summary:`);
    console.log(`   Strategy: ${this.strategy}`);
    console.log(`   Total files: ${conflictedFiles.length}`);
    console.log(`   Resolved: ${resolvedCount}`);
    console.log(`   Unresolved: ${unresolvedFiles.length}`);
    
    if (remainingConflicts.length > 0) {
      console.log(`\n❌ ${remainingConflicts.length} files still have conflicts:`);
      remainingConflicts.forEach(file => console.log(`   - ${file}`));
      
      if (this.strategy === 'safe') {
        console.log('\n💡 Consider using "theirs-all" or "ours-all" strategy for remaining conflicts');
      }
      
      process.exit(2);
    } else if (unresolvedFiles.length > 0) {
      console.log(`\n⚠️  ${unresolvedFiles.length} files were skipped (critical files or no pattern match)`);
      if (this.strategy === 'safe') {
        console.log('💡 This is expected in safe mode for critical files');
      }
      process.exit(2);
    } else {
      console.log('\n✅ All conflicts resolved successfully!');
    }
  }
}

// Parse command line arguments
function parseArgs(): { strategy: string } {
  const args = process.argv.slice(2);
  let strategy = 'safe';

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--strategy' && i + 1 < args.length) {
      strategy = args[i + 1];
      break;
    }
  }

  return { strategy };
}

// Main execution
async function main() {
  try {
    const { strategy } = parseArgs();
    const resolver = new ConflictResolver(strategy);
    await resolver.resolve();
  } catch (error) {
    console.error('❌ Conflict resolution failed:', error);
    process.exit(1);
  }
}

// Only run if this file is being executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { ConflictResolver };