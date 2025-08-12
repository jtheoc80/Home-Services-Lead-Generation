#!/usr/bin/env tsx

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';

interface ConflictedFile {
  path: string;
  content: string;
  isJson: boolean;
}

interface JsonMergeOptions {
  prefer: 'higher' | 'ours' | 'theirs';
}

class JsonMergeBot {
  private options: JsonMergeOptions;

  constructor(options: JsonMergeOptions) {
    this.options = options;
  }

  private isJsonFile(filePath: string): boolean {
    return /\.(json|lock)$/i.test(filePath) || filePath === 'package-lock.json';
  }

  private getConflictedFiles(): ConflictedFile[] {
    try {
      const output = execSync('git diff --name-only --diff-filter=U', { encoding: 'utf8' });
      const conflictedPaths = output.trim().split('\n').filter(path => path.length > 0);
      
      return conflictedPaths.map(path => {
        const content = existsSync(path) ? readFileSync(path, 'utf8') : '';
        return {
          path,
          content,
          isJson: this.isJsonFile(path)
        };
      }).filter(file => file.isJson);
    } catch (error) {
      console.error('Failed to get conflicted files:', error);
      return [];
    }
  }

  private extractConflictMarkers(content: string): {
    hasConflicts: boolean;
    sections: Array<{
      ours: string;
      theirs: string;
      base?: string;
    }>;
  } {
    const conflictRegex = /<<<<<<< HEAD\n([\s\S]*?)\n=======\n([\s\S]*?)\n>>>>>>> .*/g;
    const sections: Array<{ ours: string; theirs: string; base?: string }> = [];
    let match;

    while ((match = conflictRegex.exec(content)) !== null) {
      sections.push({
        ours: match[1],
        theirs: match[2]
      });
    }

    return {
      hasConflicts: sections.length > 0,
      sections
    };
  }

  private compareVersions(version1: string, version2: string): number {
    // Remove leading v if present
    const v1 = version1.replace(/^v/, '');
    const v2 = version2.replace(/^v/, '');
    
    const parts1 = v1.split('.').map(n => parseInt(n, 10) || 0);
    const parts2 = v2.split('.').map(n => parseInt(n, 10) || 0);
    
    const maxLength = Math.max(parts1.length, parts2.length);
    
    for (let i = 0; i < maxLength; i++) {
      const part1 = parts1[i] || 0;
      const part2 = parts2[i] || 0;
      
      if (part1 > part2) return 1;
      if (part1 < part2) return -1;
    }
    
    return 0;
  }

  private mergeJsonObjects(ours: any, theirs: any): any {
    if (this.options.prefer === 'ours') {
      return ours;
    }
    
    if (this.options.prefer === 'theirs') {
      return theirs;
    }

    // Higher strategy - merge intelligently
    if (typeof ours !== 'object' || typeof theirs !== 'object' || 
        ours === null || theirs === null || 
        Array.isArray(ours) || Array.isArray(theirs)) {
      
      // For non-objects, prefer higher version if it looks like a version
      if (typeof ours === 'string' && typeof theirs === 'string') {
        const versionRegex = /^\d+(\.\d+)*(-\w+)?$/;
        if (versionRegex.test(ours) && versionRegex.test(theirs)) {
          return this.compareVersions(ours, theirs) >= 0 ? ours : theirs;
        }
      }
      
      return theirs; // Default to theirs for non-objects
    }

    const result = { ...ours };

    for (const [key, theirValue] of Object.entries(theirs)) {
      if (!(key in ours)) {
        result[key] = theirValue;
      } else {
        const ourValue = ours[key];
        
        // Special handling for version fields
        if ((key === 'version' || key.endsWith('Version')) && 
            typeof ourValue === 'string' && typeof theirValue === 'string') {
          const versionRegex = /^\d+(\.\d+)*(-\w+)?$/;
          if (versionRegex.test(ourValue) && versionRegex.test(theirValue)) {
            result[key] = this.compareVersions(ourValue, theirValue) >= 0 ? ourValue : theirValue;
            continue;
          }
        }

        // Special handling for dependencies
        if ((key === 'dependencies' || key === 'devDependencies' || key === 'peerDependencies') &&
            typeof ourValue === 'object' && typeof theirValue === 'object' &&
            ourValue !== null && theirValue !== null &&
            !Array.isArray(ourValue) && !Array.isArray(theirValue)) {
          result[key] = this.mergeDependencies(ourValue as Record<string, string>, theirValue as Record<string, string>);
          continue;
        }

        // Recursively merge objects
        if (typeof ourValue === 'object' && typeof theirValue === 'object' &&
            ourValue !== null && theirValue !== null &&
            !Array.isArray(ourValue) && !Array.isArray(theirValue)) {
          result[key] = this.mergeJsonObjects(ourValue, theirValue);
        } else {
          result[key] = theirValue; // Default to theirs
        }
      }
    }

    return result;
  }

  private mergeDependencies(ours: Record<string, string>, theirs: Record<string, string>): Record<string, string> {
    const result = { ...ours };

    for (const [pkg, theirVersion] of Object.entries(theirs)) {
      if (!(pkg in ours)) {
        result[pkg] = theirVersion;
      } else {
        const ourVersion = ours[pkg];
        
        // Try to pick higher version for dependencies
        const theirVersionClean = theirVersion.replace(/^[\^~>=<]/, '');
        const ourVersionClean = ourVersion.replace(/^[\^~>=<]/, '');
        
        const versionRegex = /^\d+(\.\d+)*(-\w+)?$/;
        if (versionRegex.test(ourVersionClean) && versionRegex.test(theirVersionClean)) {
          const comparison = this.compareVersions(ourVersionClean, theirVersionClean);
          result[pkg] = comparison >= 0 ? ourVersion : theirVersion;
        } else {
          result[pkg] = theirVersion; // Default to theirs if version comparison fails
        }
      }
    }

    return result;
  }

  private resolveJsonConflict(filePath: string, content: string): string {
    const { hasConflicts, sections } = this.extractConflictMarkers(content);
    
    if (!hasConflicts) {
      return content;
    }

    let resolvedContent = content;

    // Process each conflict section
    for (const section of sections) {
      try {
        let resolvedSection: string;

        if (this.options.prefer === 'ours') {
          resolvedSection = section.ours;
        } else if (this.options.prefer === 'theirs') {
          resolvedSection = section.theirs;
        } else {
          // Try to parse and merge JSON
          try {
            const oursJson = JSON.parse(section.ours);
            const theirsJson = JSON.parse(section.theirs);
            const merged = this.mergeJsonObjects(oursJson, theirsJson);
            resolvedSection = JSON.stringify(merged, null, 2);
          } catch {
            // If JSON parsing fails, fall back to simple preference
            resolvedSection = section.theirs;
          }
        }

        // Replace the conflict marker section with resolved content
        const conflictPattern = `<<<<<<< HEAD\n${section.ours}\n=======\n${section.theirs}\n>>>>>>> .*`;
        const regex = new RegExp(conflictPattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
        resolvedContent = resolvedContent.replace(regex, resolvedSection);
      } catch (error) {
        console.warn(`Failed to resolve conflict section in ${filePath}:`, error);
        // Keep the conflict markers if resolution fails
      }
    }

    return resolvedContent;
  }

  private stageFile(filePath: string): void {
    try {
      execSync(`git add "${filePath}"`);
      console.log(`✓ Staged resolved file: ${filePath}`);
    } catch (error) {
      console.error(`✗ Failed to stage file ${filePath}:`, error);
    }
  }

  async resolve(): Promise<void> {
    console.log(`🔄 Starting JSON conflict resolution with strategy: ${this.options.prefer}`);
    
    const conflictedFiles = this.getConflictedFiles();
    
    if (conflictedFiles.length === 0) {
      console.log('✅ No JSON files with conflicts found');
      return;
    }

    console.log(`📋 Found ${conflictedFiles.length} conflicted JSON files:`);
    conflictedFiles.forEach(file => console.log(`   - ${file.path}`));

    let resolvedCount = 0;

    for (const file of conflictedFiles) {
      console.log(`\n🔍 Processing: ${file.path}`);
      
      try {
        const resolvedContent = this.resolveJsonConflict(file.path, file.content);
        
        // Check if conflicts were actually resolved
        const stillHasConflicts = this.extractConflictMarkers(resolvedContent).hasConflicts;
        
        if (stillHasConflicts) {
          console.log(`⚠️  Some conflicts remain in ${file.path}, skipping`);
          continue;
        }

        // Write resolved content and stage
        writeFileSync(file.path, resolvedContent, 'utf8');
        this.stageFile(file.path);
        resolvedCount++;
        
        console.log(`✅ Resolved conflicts in ${file.path}`);
      } catch (error) {
        console.error(`❌ Failed to resolve ${file.path}:`, error);
      }
    }

    console.log(`\n📊 Resolution Summary:`);
    console.log(`   Strategy: ${this.options.prefer}`);
    console.log(`   Total files: ${conflictedFiles.length}`);
    console.log(`   Resolved: ${resolvedCount}`);
    
    if (resolvedCount === 0) {
      console.log('❌ No files were successfully resolved');
      process.exit(1);
    } else if (resolvedCount < conflictedFiles.length) {
      console.log(`⚠️  ${conflictedFiles.length - resolvedCount} files still have conflicts`);
      process.exit(2);
    } else {
      console.log('✅ All JSON conflicts resolved successfully!');
    }
  }
}

// Parse command line arguments
function parseArgs(): JsonMergeOptions {
  const args = process.argv.slice(2);
  let prefer: 'higher' | 'ours' | 'theirs' = 'higher';

  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--prefer=')) {
      const value = args[i].split('=')[1] as 'higher' | 'ours' | 'theirs';
      if (['higher', 'ours', 'theirs'].includes(value)) {
        prefer = value;
      } else {
        console.error(`❌ Invalid prefer value: ${value}. Must be one of: higher, ours, theirs`);
        process.exit(1);
      }
    }
  }

  return { prefer };
}

// Main execution
async function main() {
  try {
    const options = parseArgs();
    const bot = new JsonMergeBot(options);
    await bot.resolve();
  } catch (error) {
    console.error('❌ JSON merge bot failed:', error);
    process.exit(1);
  }
}

// Only run if this file is being executed directly
if (process.argv[1].endsWith('jsonResolve.ts') || process.argv[1].endsWith('jsonResolve.js')) {
  main();
}

export { JsonMergeBot };