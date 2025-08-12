#!/usr/bin/env tsx

import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface JsonConflictSummary {
  total: number;
  resolved: number;
  failed: string[];
  skipped: string[];
}

class JsonConflictResolver {
  private summary: JsonConflictSummary = {
    total: 0,
    resolved: 0,
    failed: [],
    skipped: []
  };

  private isJsonOrLockFile(filePath: string): boolean {
    const jsonLockPatterns = [
      '**/*.json',
      '**/package-lock.json',
      '**/yarn.lock',
      '**/pnpm-lock.yaml',
      '**/*lock*.json'
    ];

    return jsonLockPatterns.some(pattern => {
      const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
      return regex.test(filePath);
    });
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

  private async resolveFile(filePath: string): Promise<boolean> {
    try {
      // For JSON and lock files, prefer 'theirs' (incoming changes) as they are usually dependency updates
      execSync(`git checkout --theirs "${filePath}"`, { stdio: 'pipe' });
      execSync(`git add "${filePath}"`, { stdio: 'pipe' });
      console.log(`✓ Resolved ${filePath} using --theirs (incoming changes)`);
      return true;
    } catch (error) {
      console.error(`✗ Failed to resolve ${filePath}:`, error);
      return false;
    }
  }

  async resolve(): Promise<void> {
    console.log(`🔄 Starting JSON conflict resolution...`);
    
    const conflictedFiles = await this.getConflictedFiles();
    if (conflictedFiles.length === 0) {
      console.log('✅ No conflicted files found');
      return;
    }

    // Filter to only JSON and lock files
    const jsonConflictedFiles = conflictedFiles.filter(file => this.isJsonOrLockFile(file));
    const nonJsonFiles = conflictedFiles.filter(file => !this.isJsonOrLockFile(file));

    this.summary.total = jsonConflictedFiles.length;

    if (nonJsonFiles.length > 0) {
      console.log(`📋 Found ${nonJsonFiles.length} non-JSON conflicted files (will be skipped):`);
      nonJsonFiles.forEach(file => console.log(`   - ${file}`));
      this.summary.skipped = nonJsonFiles;
    }

    if (jsonConflictedFiles.length === 0) {
      console.log('✅ No JSON or lock file conflicts found');
      if (nonJsonFiles.length > 0) {
        console.log(`⚠️  ${nonJsonFiles.length} non-JSON files still have conflicts`);
        process.exit(2);
      }
      return;
    }

    console.log(`📋 Found ${jsonConflictedFiles.length} JSON/lock file conflicts:`);
    jsonConflictedFiles.forEach(file => console.log(`   - ${file}`));

    for (const filePath of jsonConflictedFiles) {
      console.log(`\n🔍 Processing: ${filePath}`);

      // Skip binary files
      if (this.isBinaryFile(filePath)) {
        console.log(`⚠️  Skipping binary file: ${filePath}`);
        this.summary.skipped.push(filePath);
        continue;
      }

      const resolved = await this.resolveFile(filePath);
      if (resolved) {
        this.summary.resolved++;
      } else {
        this.summary.failed.push(filePath);
      }
    }

    // Verify no JSON conflicts remain
    const remainingConflicts = (await this.getConflictedFiles()).filter(file => this.isJsonOrLockFile(file));
    
    this.printSummary();
    
    if (remainingConflicts.length > 0) {
      console.log(`\n❌ ${remainingConflicts.length} JSON/lock files still have conflicts:`);
      remainingConflicts.forEach(file => console.log(`   - ${file}`));
      process.exit(2);
    } else if (this.summary.failed.length > 0) {
      console.log(`\n❌ ${this.summary.failed.length} JSON/lock files failed to resolve`);
      process.exit(2);
    } else if (nonJsonFiles.length > 0) {
      console.log(`\n⚠️  All JSON/lock conflicts resolved, but ${nonJsonFiles.length} non-JSON files still have conflicts`);
      process.exit(2);
    } else {
      console.log('\n✅ All JSON/lock conflicts resolved successfully!');
    }
  }

  private printSummary(): void {
    console.log(`\n📊 JSON Conflict Resolution Summary:`);
    console.log(`   JSON/Lock files: ${this.summary.total}`);
    console.log(`   Resolved: ${this.summary.resolved}`);
    console.log(`   Failed: ${this.summary.failed.length}`);
    console.log(`   Skipped (non-JSON): ${this.summary.skipped.length}`);
    
    if (this.summary.failed.length > 0) {
      console.log(`\n❌ Failed files:`);
      this.summary.failed.forEach(file => console.log(`   - ${file}`));
    }
  }

  getSummary(): JsonConflictSummary {
    return { ...this.summary };
  }
}

// Main execution
async function main() {
  try {
    const resolver = new JsonConflictResolver();
    await resolver.resolve();
  } catch (error) {
    console.error('❌ JSON conflict resolution failed:', error);
    process.exit(1);
  }
}

// Only run if this file is being executed directly
if (fileURLToPath(import.meta.url) === process.argv[1]) {
  main();
}

export { JsonConflictResolver };