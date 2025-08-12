
// tools/bots/jsonResolve.ts
// Auto-resolve conflicts in package.json + regenerate lockfiles the right way.
//
// Strategy:
// - package.json: union deps; on version clash pick a caret on the higher semver.
// - scripts: keep ours; add "<key>:theirs" if different to avoid losing commands.
// - lockfiles: never hand-merge; regen deterministically per workspace dir.
// - Only touches package.json and lockfiles; leaves everything else for humans.

import { execa } from "execa";
import * as fs from "fs/promises";
import * as path from "path";
import { globby } from "globby";
import semver from "semver";
import * as stringify from "json-stable-stringify";

type Dict = Record<string, string>;
type MergeSummary = { file: string; action: "merged" | "regenerated" | "skipped" };

const isPkgJson = (p: string) => p.endsWith("package.json");
const isNpmLock = (p: string) => p.endsWith("package-lock.json");
const isPnpmLock = (p: string) => p.endsWith("pnpm-lock.yaml");
const isYarnLock = (p: string) => p.endsWith("yarn.lock");

async function runGit(args: string[], opts: { cwd?: string } = {}) {
  const { stdout } = await execa("git", args, { stdio: ["ignore", "pipe", "pipe"], ...opts });
  return stdout.trim();
}

async function getConflictedFiles(): Promise<string[]> {
  const out = await runGit(["diff", "--name-only", "--diff-filter=U"]);
  return out ? out.split("\n").filter(Boolean) : [];
}

function mergeDeps(ours: Dict = {}, theirs: Dict = {}, prefer: "higher" | "ours" | "theirs" = "higher"): Dict {
  const keys = Array.from(new Set([...Object.keys(ours || {}), ...Object.keys(theirs || {})]));
  const out: Dict = {};
  for (const k of keys) {
    const a = ours?.[k];
    const b = theirs?.[k];
    if (a && !b) out[k] = a;
    else if (!a && b) out[k] = b;
    else if (a === b) out[k] = a!;
    else {
      // conflict: choose according to strategy
      if (prefer === "ours") out[k] = a!;
      else if (prefer === "theirs") out[k] = b!;
      else {
        // higher: pick caret on higher semver; fallback to theirs if unparsable
        const ca = semver.coerce(a!);
        const cb = semver.coerce(b!);
        if (ca && cb) {
          const higher = semver.rcompare(ca, cb) > 0 ? ca : cb;
          out[k] = `^${higher.version}`;
        } else {
          out[k] = b!;
        }
      }
    }
  }
  // sort keys for determinism
  return Object.fromEntries(Object.entries(out).sort(([ka], [kb]) => ka.localeCompare(kb)));
}

function mergeScripts(ours: Dict = {}, theirs: Dict = {}): Dict {
  const out: Dict = { ...(ours || {}) };
  for (const [k, v] of Object.entries(theirs || {})) {
    if (!(k in out)) {
      out[k] = v;
    } else if (out[k] !== v) {
      // keep ours, preserve theirs under suffix
      const alias = `${k}:theirs`;
      if (!(alias in out)) out[alias] = v;
    }
  }
  return Object.fromEntries(Object.entries(out).sort(([a], [b]) => a.localeCompare(b)));
}

async function readStageBlob(stage: 2 | 3, file: string): Promise<any> {
  // Stage 2 = ours, Stage 3 = theirs
  const blob = await execa("git", ["show", `:${stage}:${file}`], { stdout: "pipe" });
  let blob;
  try {
    blob = await execa("git", ["show", `:${stage}:${file}`], { stdout: "pipe" });
  } catch (e) {
    throw new Error(`Failed to read ${file} from git stage ${stage}: ${(e as Error).message}`);
  }
  try {
    return JSON.parse(blob.stdout);
  } catch (e) {
    throw new Error(`Failed to parse JSON from ${file} (stage ${stage}): ${(e as Error).message}`);
  }
}

async function writeJson(file: string, data: any) {
  const text = stringify(data, { space: 2 }) + "\n";
  await fs.writeFile(file, text, "utf8");
  await runGit(["add", file]);
}

async function mergePackageJson(file: string, prefer: "higher" | "ours" | "theirs"): Promise<MergeSummary> {
  const ours = await readStageBlob(2, file);
  const theirs = await readStageBlob(3, file);

  const merged = { ...theirs, ...ours }; // default prefer ours for root fields
  merged.dependencies = mergeDeps(ours.dependencies, theirs.dependencies, prefer);
  merged.devDependencies = mergeDeps(ours.devDependencies, theirs.devDependencies, prefer);
  merged.peerDependencies = mergeDeps(ours.peerDependencies, theirs.peerDependencies, prefer);
  merged.optionalDependencies = mergeDeps(ours.optionalDependencies, theirs.optionalDependencies, prefer);
  merged.scripts = mergeScripts(ours.scripts, theirs.scripts);

  // Fields we always prefer ours explicitly
  for (const k of ["name", "version", "type", "private", "engines"]) {
    if (ours?.[k] !== undefined) merged[k] = ours[k];
  }

  await writeJson(file, merged);
  return { file, action: "merged" };
}

async function regenLockfile(lockfile: string): Promise<MergeSummary> {
  const cwd = path.dirname(lockfile);

  // Reset to a non-conflicted state to allow install
  await execa("git", ["checkout", "--ours", lockfile]);
  await runGit(["add", lockfile]);

  // Detect manager and regenerate lock only
  if (isPnpmLock(lockfile)) {
    await execa("pnpm", ["install", "--lockfile-only"], { cwd, stdio: "inherit" });
  } else if (isYarnLock(lockfile)) {
    try {
      await execa("yarn", ["install", "--mode=update-lockfile"], { cwd, stdio: "inherit" });
    } catch {
      await execa("yarn", ["install", "--no-immutable"], { cwd, stdio: "inherit" }); // classic fallback
    }
  } else if (isNpmLock(lockfile)) {
    await execa("npm", ["install", "--package-lock-only"], { cwd, stdio: "inherit" });
  }

  await runGit(["add", lockfile]);
  return { file: lockfile, action: "regenerated" };
}

async function main() {
  const prefer = (process.argv.find(a => a.startsWith("--prefer="))?.split("=")[1] ??
    "higher") as "higher" | "ours" | "theirs";

  const conflicted = await getConflictedFiles();
  if (conflicted.length === 0) {
    console.log("No conflicted files. Nothing to do.");
    return;
  }

  // Limit to package.json and lockfiles
  const targets = await globby(
    conflicted.filter(f => isPkgJson(f) || isNpmLock(f) || isPnpmLock(f) || isYarnLock(f)),
    { dot: true }
  );

  const summaries: MergeSummary[] = [];
  for (const file of targets) {
    if (isPkgJson(file)) {
      summaries.push(await mergePackageJson(file, prefer));
    } else {
      summaries.push(await regenLockfile(file));
    }
  }

  // Ensure we cleared all conflicts for the targeted files
  const remain = await getConflictedFiles();
  const remainInteresting = remain.filter(f => isPkgJson(f) || isNpmLock(f) || isPnpmLock(f) || isYarnLock(f));
  if (remainInteresting.length > 0) {
    console.error("Some JSON/lock conflicts remain (human attention needed):");
    for (const f of remainInteresting) console.error(" -", f);
    process.exit(2);
  }

  // Print summary
  const lines = [
    ["file", "action"],
    ...summaries.map(s => [s.file, s.action]),
  ];
  const widths = [Math.max(...lines.map(l => l[0].length)), Math.max(...lines.map(l => l[1].length))];
  console.log("\nJSON Merge Bot Summary:");
  for (const [a, b] of lines) {
    console.log(a.padEnd(widths[0]), " | ", b.padEnd(widths[1]));
  }
}

main().catch(err => {
  console.error("jsonResolve failed:", err?.stderr || err?.message || err);
  process.exit(1);
});

#!/usr/bin/env tsx

/**
 * JSON Resolve Bot
 * 
 * Resolves Git merge conflicts in package.json and lockfiles with intelligent merging.
 * Handles dependencies, scripts, and lockfile regeneration automatically.
 * 
 * Usage:
 *   npx tsx tools/bots/jsonResolve.ts
 *   npm run bot:json-resolve
 * 
 * Features:
 * - Detects conflicted files using `git diff --name-only --diff-filter=U`
 * - Targets only package.json and lockfiles (package-lock.json, pnpm-lock.yaml, yarn.lock)
 * - Merges package.json with intelligent dependency resolution using semver
 * - Handles script conflicts by keeping ours and adding theirs with :theirs suffix
 * - Regenerates lockfiles using the appropriate package manager
 * - Provides detailed summary reporting
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
      'package.json',
      '**/package.json',
      'package-lock.json',
      '**/package-lock.json',
      'pnpm-lock.yaml',
      '**/pnpm-lock.yaml',
      'yarn.lock',
      '**/yarn.lock'
    ];

    return files.filter(file => {
      return targetPatterns.some(pattern => {
        const regex = new RegExp('^' + pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*') + '$');
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
        this.results.push({
          file: filePath,
          action: 'skipped',
          details: 'Unknown lockfile type'
        });
        return false;
      }

      // Use ours side to get a valid file
      execSync(`git checkout --ours "${filePath}"`);

      const workingDir = dirname(filePath);
      
      // Check if package.json exists in the working directory
      const packageJsonPath = join(workingDir, 'package.json');
      if (!existsSync(packageJsonPath)) {
        console.error(`No package.json found in ${workingDir} for lockfile regeneration`);
        this.results.push({
          file: filePath,
          action: 'skipped',
          details: 'No package.json found'
        });
        return false;
      }

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
      console.error(`Failed to resolve lockfile conflict in ${filePath}:`, error.message || error);
      this.results.push({
        file: filePath,
        action: 'skipped',
        details: `Error: ${error.message || 'Unknown error'}`
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

    // Process each file in the right order: package.json first, then lockfiles
    const packageJsonFiles = targetFiles.filter(f => f.endsWith('package.json'));
    const lockfileFiles = targetFiles.filter(f => !f.endsWith('package.json'));
    
    const orderedFiles = [...packageJsonFiles, ...lockfileFiles];

    for (const filePath of orderedFiles) {
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

