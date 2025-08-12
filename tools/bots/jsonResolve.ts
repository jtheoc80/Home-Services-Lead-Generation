#!/usr/bin/env tsx

/**
 * JSON Resolve Bot
 * 
 * Resolves Git merge conflicts in package.json and lockfiles with intelligent merging.
 * Handles dependencies, scripts, and lockfile regeneration automatically.
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { dirname, join, basename } from 'path';
import { fileURLToPath } from 'url';
import { globby } from 'globby';
import { execa } from 'execa';
import * as semver from 'semver';
import stringify from 'json-stable-stringify';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface MergeResult {
  file: string;
  action: 'merged' | 'regenerated' | 'skipped';
  details?: string;
}

interface PackageJson {
  [key: string]: any;
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
  peerDependencies?: Record<string, string>;
  optionalDependencies?: Record<string, string>;
  scripts?: Record<string, string>;
}

class JsonConflictResolver {
  private results: MergeResult[] = [];

  /**
   * Get list of conflicted files from Git
   */
  private getConflictedFiles(): string[] {
    try {
      const output = execSync('git diff --name-only --diff-filter=U', { encoding: 'utf8' });
      return output.trim().split('\n').filter(file => file.length > 0);
    } catch (error) {
      console.error('Failed to get conflicted files:', error);
      return [];
    }
  }

  /**
   * Filter conflicted files to only target package.json and lockfiles
   */
  private filterTargetFiles(files: string[]): string[] {
    const targetPatterns = [
      '**/package.json',
      '**/package-lock.json',
      '**/pnpm-lock.yaml', 
      '**/yarn.lock'
    ];

    return files.filter(file => {
      return targetPatterns.some(pattern => {
        const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
        return regex.test(file);
      });
    });
  }

  /**
   * Read file content from a specific Git conflict side
   */
  private readGitSide(filePath: string, side: '2' | '3'): string | null {
    try {
      return execSync(`git show :${side}:${filePath}`, { encoding: 'utf8' });
    } catch (error) {
      console.warn(`Failed to read ${side === '2' ? 'ours' : 'theirs'} side of ${filePath}:`, error);
      return null;
    }
  }

  /**
   * Merge dependency objects with semver conflict resolution
   */
  private mergeDependencies(ours: Record<string, string> = {}, theirs: Record<string, string> = {}): Record<string, string> {
    const merged: Record<string, string> = { ...ours };

    for (const [pkg, theirVersion] of Object.entries(theirs)) {
      if (!merged[pkg]) {
        // Package only in theirs, add it
        merged[pkg] = theirVersion;
      } else if (merged[pkg] !== theirVersion) {
        // Conflict: choose higher semver with caret range
        try {
          const ourVersion = merged[pkg].replace(/^[\^~]/, '');
          const theirVersionClean = theirVersion.replace(/^[\^~]/, '');
          
          const comparison = semver.compare(ourVersion, theirVersionClean);
          if (comparison < 0) {
            // Their version is higher
            merged[pkg] = `^${theirVersionClean}`;
          } else if (comparison > 0) {
            // Our version is higher, add caret if not present
            merged[pkg] = merged[pkg].startsWith('^') ? merged[pkg] : `^${ourVersion}`;
          }
          // If equal, keep ours as-is
        } catch (semverError) {
          // Fallback to theirs if semver parsing fails
          console.warn(`Could not parse semver for ${pkg}: ${merged[pkg]} vs ${theirVersion}, using theirs`);
          merged[pkg] = theirVersion;
        }
      }
    }

    // Sort keys alphabetically for determinism
    const sortedMerged: Record<string, string> = {};
    Object.keys(merged).sort().forEach(key => {
      sortedMerged[key] = merged[key];
    });

    return sortedMerged;
  }

  /**
   * Merge scripts with conflict handling
   */
  private mergeScripts(ours: Record<string, string> = {}, theirs: Record<string, string> = {}): Record<string, string> {
    const merged: Record<string, string> = { ...ours };

    for (const [scriptName, theirScript] of Object.entries(theirs)) {
      if (!merged[scriptName]) {
        // Script only in theirs, add it
        merged[scriptName] = theirScript;
      } else if (merged[scriptName] !== theirScript) {
        // Conflict: keep ours and add theirs with suffix
        merged[`${scriptName}:theirs`] = theirScript;
      }
    }

    return merged;
  }

  /**
   * Merge two package.json objects according to the specified rules
   */
  private mergePackageJson(ours: PackageJson, theirs: PackageJson): PackageJson {
    const merged: PackageJson = { ...ours }; // Start with ours (root keys preference)

    // Merge dependencies
    if (ours.dependencies || theirs.dependencies) {
      merged.dependencies = this.mergeDependencies(ours.dependencies, theirs.dependencies);
    }

    if (ours.devDependencies || theirs.devDependencies) {
      merged.devDependencies = this.mergeDependencies(ours.devDependencies, theirs.devDependencies);
    }

    if (ours.peerDependencies || theirs.peerDependencies) {
      merged.peerDependencies = this.mergeDependencies(ours.peerDependencies, theirs.peerDependencies);
    }

    if (ours.optionalDependencies || theirs.optionalDependencies) {
      merged.optionalDependencies = this.mergeDependencies(ours.optionalDependencies, theirs.optionalDependencies);
    }

    // Merge scripts
    if (ours.scripts || theirs.scripts) {
      merged.scripts = this.mergeScripts(ours.scripts, theirs.scripts);
    }

    return merged;
  }

  /**
   * Resolve package.json conflicts
   */
  private async resolvePackageJson(filePath: string): Promise<boolean> {
    try {
      const oursContent = this.readGitSide(filePath, '2');
      const theirsContent = this.readGitSide(filePath, '3');

      if (!oursContent || !theirsContent) {
        console.error(`Failed to read both sides of ${filePath}`);
        return false;
      }

      const ours: PackageJson = JSON.parse(oursContent);
      const theirs: PackageJson = JSON.parse(theirsContent);

      const merged = this.mergePackageJson(ours, theirs);
      
      // Write merged content with stable stringify for determinism
      const mergedContent = stringify(merged, { space: 2 }) + '\n';
      writeFileSync(filePath, mergedContent, 'utf8');

      // Stage the file
      execSync(`git add "${filePath}"`);

      this.results.push({
        file: filePath,
        action: 'merged',
        details: 'JSON merged with dependency and script resolution'
      });

      console.log(`✓ Merged and staged ${filePath}`);
      return true;
    } catch (error) {
      console.error(`Failed to resolve package.json conflict in ${filePath}:`, error);
      this.results.push({
        file: filePath,
        action: 'skipped',
        details: `Error: ${error.message}`
      });
      return false;
    }
  }

  /**
   * Detect package manager type based on lockfile
   */
  private detectPackageManager(lockfilePath: string): 'npm' | 'pnpm' | 'yarn' | null {
    const filename = basename(lockfilePath);
    if (filename === 'package-lock.json') return 'npm';
    if (filename === 'pnpm-lock.yaml') return 'pnpm';
    if (filename === 'yarn.lock') return 'yarn';
    return null;
  }

  /**
   * Resolve lockfile conflicts by regenerating
   */
  private async resolveLockfile(filePath: string): Promise<boolean> {
    try {
      const packageManager = this.detectPackageManager(filePath);
      if (!packageManager) {
        console.error(`Unknown lockfile type: ${filePath}`);
        return false;
      }

      // Use ours side to get a valid file
      execSync(`git checkout --ours "${filePath}"`);

      const workingDir = dirname(filePath);
      
      // Regenerate lockfile without installing
      let regenerateCmd: string;
      switch (packageManager) {
        case 'npm':
          regenerateCmd = 'npm install --package-lock-only';
          break;
        case 'pnpm':
          regenerateCmd = 'pnpm install --lockfile-only';
          break;
        case 'yarn':
          regenerateCmd = 'yarn install --mode=update-lockfile || yarn install --no-immutable';
          break;
      }

      await execa('sh', ['-c', regenerateCmd], { cwd: workingDir });

      // Stage the regenerated lockfile
      execSync(`git add "${filePath}"`);

      this.results.push({
        file: filePath,
        action: 'regenerated',
        details: `Regenerated using ${packageManager}`
      });

      console.log(`✓ Regenerated and staged ${filePath} using ${packageManager}`);
      return true;
    } catch (error) {
      console.error(`Failed to resolve lockfile conflict in ${filePath}:`, error);
      this.results.push({
        file: filePath,
        action: 'skipped',
        details: `Error: ${error.message}`
      });
      return false;
    }
  }

  /**
   * Main resolution method
   */
  async resolve(): Promise<void> {
    console.log('🔄 Starting JSON conflict resolution...');

    const conflictedFiles = this.getConflictedFiles();
    if (conflictedFiles.length === 0) {
      console.log('✅ No conflicted files found');
      return;
    }

    const targetFiles = this.filterTargetFiles(conflictedFiles);
    if (targetFiles.length === 0) {
      console.log('ℹ️  No package.json or lockfiles in conflict');
      return;
    }

    console.log(`📋 Found ${targetFiles.length} target files in conflict:`);
    targetFiles.forEach(file => console.log(`   - ${file}`));

    // Process each file
    for (const filePath of targetFiles) {
      console.log(`\n🔍 Processing: ${filePath}`);

      if (filePath.endsWith('package.json')) {
        await this.resolvePackageJson(filePath);
      } else {
        // It's a lockfile
        await this.resolveLockfile(filePath);
      }
    }

    // Verify no conflicts remain
    const remainingConflicts = this.getConflictedFiles();
    const targetConflicts = this.filterTargetFiles(remainingConflicts);

    if (targetConflicts.length > 0) {
      console.log(`\n❌ ${targetConflicts.length} target files still have conflicts:`);
      targetConflicts.forEach(file => console.log(`   - ${file}`));
      process.exit(2);
    }

    // Print summary table
    this.printSummary();

    const hasErrors = this.results.some(r => r.action === 'skipped');
    if (hasErrors) {
      console.log('\n⚠️  Some files were skipped due to errors');
      process.exit(2);
    } else {
      console.log('\n✅ All conflicts resolved successfully!');
      process.exit(0);
    }
  }

  /**
   * Print summary table
   */
  private printSummary(): void {
    console.log('\n📊 Resolution Summary:');
    console.log('┌─────────────────────────────────────────────┬──────────────┬─────────────────────────────────┐');
    console.log('│ File                                        │ Action       │ Details                         │');
    console.log('├─────────────────────────────────────────────┼──────────────┼─────────────────────────────────┤');
    
    this.results.forEach(result => {
      const file = result.file.padEnd(43);
      const action = result.action.padEnd(12);
      const details = (result.details || '').substring(0, 31).padEnd(31);
      console.log(`│ ${file} │ ${action} │ ${details} │`);
    });
    
    console.log('└─────────────────────────────────────────────┴──────────────┴─────────────────────────────────┘');
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