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