#!/usr/bin/env node

/**
 * GitHub Actions Workflow Linter
 * 
 * Validates workflow files for common issues and best practices:
 * - Syntax validation (YAML parsing)
 * - Required secrets documentation
 * - Consistent step naming
 * - No duplicate steps
 * - Proper artifact naming
 * - No complex ternary expressions in conditions
 */

import { readFileSync, readdirSync } from 'fs';
import { join, basename } from 'path';
import { parse as parseYaml } from 'yaml';

class WorkflowLinter {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.workflowDir = '.github/workflows';
  }

  lint() {
    console.log('🔍 Linting GitHub Actions workflows...\n');
    
    const workflowFiles = readdirSync(this.workflowDir)
      .filter(file => file.endsWith('.yml') || file.endsWith('.yaml'));
    
    for (const file of workflowFiles) {
      this.lintWorkflow(file);
    }
    
    this.printResults();
    
    if (this.errors.length > 0) {
      process.exit(1);
    }
  }

  lintWorkflow(filename) {
    const filepath = join(this.workflowDir, filename);
    console.log(`📄 Checking ${filename}...`);
    
    let content, workflow;
    
    try {
      content = readFileSync(filepath, 'utf8');
      workflow = parseYaml(content);
    } catch (error) {
      this.addError(filename, 'YAML parsing failed', error.message);
      return;
    }

    this.checkWorkflowStructure(filename, workflow);
    this.checkSecrets(filename, workflow, content);
    this.checkSteps(filename, workflow);
    this.checkArtifacts(filename, workflow);
    this.checkConditionals(filename, content);
    
    console.log(`  ✅ ${filename} checked\n`);
  }

  checkWorkflowStructure(filename, workflow) {
    if (!workflow.name) {
      this.addWarning(filename, 'Missing workflow name');
    }
    
    if (!workflow.on) {
      this.addError(filename, 'Missing trigger configuration (on)');
    }
    
    if (!workflow.jobs || Object.keys(workflow.jobs).length === 0) {
      this.addError(filename, 'No jobs defined');
    }
  }

  checkSecrets(filename, workflow, content) {
    const secretPattern = /\$\{\{\s*secrets\.([A-Z_]+)\s*\}\}/g;
    const secretMatches = [...content.matchAll(secretPattern)];
    const secretsUsed = secretMatches.map(match => match[1]);
    
    if (secretsUsed.length > 0) {
      // Check if secrets are documented
      const hasDocumentation = content.includes('# Required secrets:') || 
                               content.includes('## Secrets') ||
                               content.includes('### Required Secrets');
      
      if (!hasDocumentation) {
        this.addWarning(filename, `Uses secrets but missing documentation. Required secrets: ${secretsUsed.join(', ')}`);
      }
    }
  }

  checkSteps(filename, workflow) {
    for (const [jobName, job] of Object.entries(workflow.jobs)) {
      if (!job.steps) continue;
      
      const stepNames = job.steps
        .filter(step => step.name)
        .map(step => step.name);
      
      // Check for duplicate step names
      const duplicates = stepNames.filter((name, index) => stepNames.indexOf(name) !== index);
      if (duplicates.length > 0) {
        this.addError(filename, `Job '${jobName}' has duplicate step names: ${duplicates.join(', ')}`);
      }
      
      // Check for nested step definitions (incomplete steps)
      for (const [stepIndex, step] of job.steps.entries()) {
        if (step.uses && !step.with && step.name && job.steps[stepIndex + 1]?.uses === step.uses) {
          this.addWarning(filename, `Job '${jobName}' step ${stepIndex + 1} appears to be incomplete or duplicated`);
        }
      }
    }
  }

  checkArtifacts(filename, workflow) {
    for (const [jobName, job] of Object.entries(workflow.jobs)) {
      if (!job.steps) continue;
      
      for (const step of job.steps) {
        if (step.uses?.includes('upload-artifact')) {
          const artifactName = step.with?.name;
          if (!artifactName) {
            this.addError(filename, `Job '${jobName}' uploads artifact without name`);
          } else if (typeof artifactName === 'string' && artifactName.includes('${{')) {
            // Check for stable naming patterns
            if (!artifactName.includes('steps.') || !artifactName.includes('.outputs.')) {
              this.addWarning(filename, `Job '${jobName}' uses potentially unstable artifact naming: ${artifactName}`);
            }
          }
        }
      }
    }
  }

  checkConditionals(filename, content) {
    // Check for complex ternary expressions in if conditions
    const complexTernaryPattern = /if:\s*.*\?\s*.*:\s*.*/g;
    const matches = [...content.matchAll(complexTernaryPattern)];
    
    if (matches.length > 0) {
      this.addWarning(filename, `Contains complex ternary expressions in conditions. Consider moving logic to JavaScript steps.`);
    }
    
    // Check for nested GitHub expressions
    const nestedExpressionPattern = /\$\{\{\s*[^}]*\$\{\{.*\}\}.*\}\}/g;
    const nestedMatches = [...content.matchAll(nestedExpressionPattern)];
    
    if (nestedMatches.length > 0) {
      this.addWarning(filename, `Contains nested GitHub expressions which can be unreliable`);
    }
  }

  addError(filename, type, message = '') {
    this.errors.push({ filename, type, message });
  }

  addWarning(filename, type, message = '') {
    this.warnings.push({ filename, type, message });
  }

  printResults() {
    console.log('📊 Linting Results:\n');
    
    if (this.errors.length === 0 && this.warnings.length === 0) {
      console.log('✅ All workflows are valid!\n');
      return;
    }
    
    if (this.errors.length > 0) {
      console.log('❌ Errors:');
      for (const error of this.errors) {
        console.log(`  ${error.filename}: ${error.type}${error.message ? ` - ${error.message}` : ''}`);
      }
      console.log();
    }
    
    if (this.warnings.length > 0) {
      console.log('⚠️  Warnings:');
      for (const warning of this.warnings) {
        console.log(`  ${warning.filename}: ${warning.type}${warning.message ? ` - ${warning.message}` : ''}`);
      }
      console.log();
    }
    
    console.log(`Summary: ${this.errors.length} errors, ${this.warnings.length} warnings\n`);
  }
}

// Main execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const linter = new WorkflowLinter();
  linter.lint();
}