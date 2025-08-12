#!/usr/bin/env tsx

/**
 * JSON Resolve Bot
 * 
 * Standardizes JSON formatting and resolves JSON-related issues:
 * - Formats JSON files with consistent spacing and sorting
 * - Validates JSON syntax
 * - Resolves common JSON conflicts during merges
 * - Ensures deterministic JSON output
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { globby } from 'globby';
import { execSync } from 'child_process';
import * as semver from 'semver';
import { execa } from 'execa';
import stringify from 'json-stable-stringify';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface JsonResolveOptions {
  patterns: string[];
  dryRun: boolean;
  validate: boolean;
  format: boolean;
  verbose: boolean;
}

class JsonResolver {
  private options: JsonResolveOptions;
  private projectRoot: string;

  constructor(options: Partial<JsonResolveOptions> = {}) {
    this.options = {
      patterns: ['**/*.json', '!node_modules/**', '!.git/**'],
      dryRun: false,
      validate: true,
      format: true,
      verbose: false,
      ...options
    };
    this.projectRoot = join(__dirname, '../..');
  }

  /**
   * Main entry point for JSON resolution
   */
  async run(): Promise<void> {
    console.log('🔧 JSON Resolve Bot starting...');
    
    if (this.options.verbose) {
      console.log('Options:', this.options);
    }

    try {
      const jsonFiles = await this.findJsonFiles();
      console.log(`📁 Found ${jsonFiles.length} JSON files to process`);

      const results = {
        processed: 0,
        errors: 0,
        formatted: 0,
        validated: 0
      };

      for (const file of jsonFiles) {
        try {
          await this.processJsonFile(file, results);
        } catch (error) {
          console.error(`❌ Error processing ${file}:`, error);
          results.errors++;
        }
        results.processed++;
      }

      this.printSummary(results);
      
      if (results.errors > 0) {
        process.exit(1);
      }
    } catch (error) {
      console.error('❌ JSON Resolve Bot failed:', error);
      process.exit(1);
    }
  }

  /**
   * Find all JSON files matching the patterns
   */
  private async findJsonFiles(): Promise<string[]> {
    const files = await globby(this.options.patterns, {
      cwd: this.projectRoot,
      absolute: true,
      gitignore: true
    });
    
    return files.filter(file => 
      existsSync(file) && 
      file.endsWith('.json') &&
      !file.includes('node_modules') &&
      !file.includes('.git')
    );
  }

  /**
   * Process a single JSON file
   */
  private async processJsonFile(
    filePath: string, 
    results: { processed: number; errors: number; formatted: number; validated: number }
  ): Promise<void> {
    const relativePath = this.getRelativePath(filePath);
    
    if (this.options.verbose) {
      console.log(`🔍 Processing: ${relativePath}`);
    }

    const content = readFileSync(filePath, 'utf8');
    let jsonData: any;

    // Validate JSON syntax
    if (this.options.validate) {
      try {
        jsonData = JSON.parse(content);
        results.validated++;
        
        if (this.options.verbose) {
          console.log(`✅ Valid JSON: ${relativePath}`);
        }
      } catch (error) {
        throw new Error(`Invalid JSON syntax in ${relativePath}: ${error}`);
      }
    }

    // Format JSON if requested
    if (this.options.format) {
      const formattedContent = this.formatJson(jsonData || JSON.parse(content));
      
      if (content.trim() !== formattedContent.trim()) {
        if (this.options.dryRun) {
          console.log(`📝 Would format: ${relativePath}`);
        } else {
          writeFileSync(filePath, formattedContent);
          console.log(`📝 Formatted: ${relativePath}`);
        }
        results.formatted++;
      } else if (this.options.verbose) {
        console.log(`✨ Already formatted: ${relativePath}`);
      }
    }
  }

  /**
   * Format JSON with consistent styling
   */
  private formatJson(data: any): string {
    // Use json-stable-stringify for deterministic output
    const formatted = stringify(data, {
      space: 2,
      cmp: (a, b) => {
        // Custom sorting: put common keys first
        const keyOrder = ['name', 'version', 'description', 'type', 'key'];
        const aIndex = keyOrder.indexOf(a.key);
        const bIndex = keyOrder.indexOf(b.key);
        
        if (aIndex !== -1 && bIndex !== -1) {
          return aIndex - bIndex;
        }
        if (aIndex !== -1) return -1;
        if (bIndex !== -1) return 1;
        
        return a.key < b.key ? -1 : 1;
      }
    });
    
    return formatted + '\n';
  }

  /**
   * Get relative path from project root
   */
  private getRelativePath(filePath: string): string {
    return filePath.replace(this.projectRoot + '/', '');
  }

  /**
   * Print summary of operations
   */
  private printSummary(results: { processed: number; errors: number; formatted: number; validated: number }): void {
    console.log('\n📊 JSON Resolve Bot Summary:');
    console.log(`   Processed: ${results.processed} files`);
    console.log(`   Validated: ${results.validated} files`);
    console.log(`   Formatted: ${results.formatted} files`);
    
    if (results.errors > 0) {
      console.log(`   Errors: ${results.errors} files`);
    } else {
      console.log('   ✅ All files processed successfully');
    }
  }

  /**
   * Validate package.json dependencies for semver compliance
   */
  private validatePackageJson(data: any, filePath: string): void {
    if (basename(filePath) === 'package.json') {
      const deps = { ...data.dependencies, ...data.devDependencies };
      
      for (const [pkg, version] of Object.entries(deps)) {
        if (typeof version === 'string' && !semver.validRange(version)) {
          console.warn(`⚠️  Invalid semver range for ${pkg}: ${version}`);
        }
      }
    }
  }
}

/**
 * CLI interface
 */
export async function main(argv: string[] = process.argv): Promise<void> {
  const args = argv.slice(2);
  
  const options: Partial<JsonResolveOptions> = {
    dryRun: args.includes('--dry-run'),
    validate: !args.includes('--no-validate'),
    format: !args.includes('--no-format'),
    verbose: args.includes('--verbose') || args.includes('-v')
  };

  // Extract custom patterns if provided
  const patternIndex = args.indexOf('--patterns');
  if (patternIndex !== -1 && args[patternIndex + 1]) {
    options.patterns = args[patternIndex + 1].split(',');
  }

  const resolver = new JsonResolver(options);
  await resolver.run();
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('❌ JSON Resolve Bot crashed:', error);
    process.exit(1);
  });
}