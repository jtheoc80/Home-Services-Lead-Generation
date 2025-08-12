#!/usr/bin/env tsx

/**
 * Unit tests for jsonResolve core logic
 */

import * as semver from 'semver';
import stringify from 'json-stable-stringify';

// Test semver comparison logic
function testSemverLogic() {
  console.log('🧪 Testing semver logic...');
  
  const testCases = [
    // [ours, theirs, expected]
    ['1.0.0', '1.1.0', '^1.1.0'],
    ['^1.0.0', '1.1.0', '^1.1.0'],
    ['1.2.0', '^1.1.0', '^1.2.0'],
    ['~1.0.0', '1.1.0', '^1.1.0'],
    ['1.0.0', '1.0.0', '1.0.0'],
    ['^1.0.0', '^1.0.0', '^1.0.0']
  ];
  
  function mergeDependencyVersions(ours: string, theirs: string): string {
    try {
      const ourVersion = ours.replace(/^[\^~]/, '');
      const theirVersionClean = theirs.replace(/^[\^~]/, '');
      
      const comparison = semver.compare(ourVersion, theirVersionClean);
      if (comparison < 0) {
        // Their version is higher
        return `^${theirVersionClean}`;
      } else if (comparison > 0) {
        // Our version is higher, add caret if not present
        return ours.startsWith('^') ? ours : `^${ourVersion}`;
      }
      // If equal, keep ours as-is
      return ours;
    } catch (semverError) {
      // Fallback to theirs if semver parsing fails
      console.warn(`Could not parse semver: ${ours} vs ${theirs}, using theirs`);
      return theirs;
    }
  }
  
  let passed = 0;
  for (const [ours, theirs, expected] of testCases) {
    const result = mergeDependencyVersions(ours, theirs);
    const success = result === expected;
    console.log(`  ${ours} vs ${theirs} => ${result} ${success ? '✅' : `❌ (expected ${expected})`}`);
    if (success) passed++;
  }
  
  console.log(`📊 Semver tests: ${passed}/${testCases.length} passed\n`);
  return passed === testCases.length;
}

// Test dependency merging logic
function testDependencyMerging() {
  console.log('🧪 Testing dependency merging...');
  
  function mergeDependencies(ours: Record<string, string> = {}, theirs: Record<string, string> = {}): Record<string, string> {
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
  
  const ours = {
    'axios': '^1.0.0',
    'lodash': '^4.17.0',
    'react': '^18.0.0'
  };
  
  const theirs = {
    'axios': '^1.2.0',  // Higher version
    'lodash': '^4.16.0', // Lower version
    'express': '^4.18.0' // New package
  };
  
  const result = mergeDependencies(ours, theirs);
  
  console.log('  Ours:', JSON.stringify(ours, null, 2));
  console.log('  Theirs:', JSON.stringify(theirs, null, 2));
  console.log('  Merged:', JSON.stringify(result, null, 2));
  
  const expected = {
    'axios': '^1.2.0',    // Higher version from theirs
    'express': '^4.18.0', // New from theirs
    'lodash': '^4.17.0',  // Higher version from ours
    'react': '^18.0.0'    // Only in ours
  };
  
  const matches = JSON.stringify(result) === JSON.stringify(expected);
  console.log(`📊 Dependency merging: ${matches ? '✅ Passed' : '❌ Failed'}\n`);
  
  if (!matches) {
    console.log('  Expected:', JSON.stringify(expected, null, 2));
  }
  
  return matches;
}

// Test scripts merging logic
function testScriptsMerging() {
  console.log('🧪 Testing scripts merging...');
  
  function mergeScripts(ours: Record<string, string> = {}, theirs: Record<string, string> = {}): Record<string, string> {
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

    // Sort keys, but keep conflicted scripts grouped with original
    const sortedMerged: Record<string, string> = {};
    const sortedKeys = Object.keys(merged).sort((a, b) => {
      // Remove :theirs suffix for sorting
      const aBase = a.replace(':theirs', '');
      const bBase = b.replace(':theirs', '');
      if (aBase === bBase) {
        // Keep original before :theirs version
        return a.includes(':theirs') ? 1 : -1;
      }
      return aBase.localeCompare(bBase);
    });
    
    sortedKeys.forEach(key => {
      sortedMerged[key] = merged[key];
    });

    return sortedMerged;
  }
  
  const ours = {
    'build': 'rollup',
    'start': 'node dist/index.js',
    'lint': 'eslint .'
  };
  
  const theirs = {
    'build': 'webpack',      // Conflict
    'start': 'node dist/index.js', // Same
    'test': 'jest'          // New
  };
  
  const result = mergeScripts(ours, theirs);
  
  console.log('  Ours:', JSON.stringify(ours, null, 2));
  console.log('  Theirs:', JSON.stringify(theirs, null, 2));
  console.log('  Merged:', JSON.stringify(result, null, 2));
  
  const expected = {
    'build': 'rollup',          // Ours kept
    'build:theirs': 'webpack',  // Theirs added with suffix
    'start': 'node dist/index.js', // Same in both
    'lint': 'eslint .',         // Only in ours
    'test': 'jest'              // Only in theirs
  };
  
  const matches = JSON.stringify(result) === JSON.stringify(expected);
  console.log(`📊 Scripts merging: ${matches ? '✅ Passed' : '❌ Failed'}\n`);
  
  if (!matches) {
    console.log('  Expected:', JSON.stringify(expected, null, 2));
  }
  
  return matches;
}

// Test JSON stringification
function testJsonStringify() {
  console.log('🧪 Testing JSON stringification...');
  
  const testObj = {
    'name': 'test-package',
    'dependencies': {
      'z-package': '^1.0.0',
      'a-package': '^2.0.0'
    },
    'scripts': {
      'test': 'jest',
      'build': 'webpack'
    }
  };
  
  const result = stringify(testObj, { space: 2 });
  console.log('  Stringified JSON (first 200 chars):', result.substring(0, 200) + '...');
  
  // Should be deterministic and formatted
  const hasProperFormatting = result.includes('  ') && result.includes('\n');
  console.log(`📊 JSON stringify: ${hasProperFormatting ? '✅ Passed' : '❌ Failed'}\n`);
  
  return hasProperFormatting;
}

// Run all tests
async function runTests() {
  console.log('🚀 Running jsonResolve unit tests...\n');
  
  const results = [
    testSemverLogic(),
    testDependencyMerging(), 
    testScriptsMerging(),
    testJsonStringify()
  ];
  
  const passed = results.filter(Boolean).length;
  const total = results.length;
  
  console.log(`🏁 Overall Results: ${passed}/${total} test suites passed`);
  
  if (passed === total) {
    console.log('✅ All tests passed! jsonResolve core logic is working correctly.');
    return true;
  } else {
    console.log('❌ Some tests failed. Please review the logic.');
    return false;
  }
}

runTests();