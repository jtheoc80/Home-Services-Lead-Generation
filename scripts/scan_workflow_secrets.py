#!/usr/bin/env python3
"""
Workflow Secrets Scanner

Scans .github/workflows for specified patterns:
- secrets.SUPABASE_*
- secrets.*_PERMITS_URL
- VERCEL_TOKEN
- RAILWAY_TOKEN

Lists each file + secret name + whether it's required (fail if missing) or optional.
"""

import re
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class SecretUsage:
    """Represents a secret usage in a workflow file"""

    file_path: str
    secret_name: str
    pattern_type: str
    is_required: bool
    context: str
    line_number: int = 0


class WorkflowSecretsScanner:
    def __init__(self, workflows_dir: str):
        self.workflows_dir = Path(workflows_dir)
        self.patterns = {
            "supabase": re.compile(r"secrets\.SUPABASE_[A-Z_]+"),
            "permits_url": re.compile(r"secrets\.([A-Z_]*_PERMITS_URL)"),
            "vercel_token": re.compile(r"VERCEL_TOKEN"),
            "railway_token": re.compile(r"RAILWAY_TOKEN"),
        }
        self.secret_usages: List[SecretUsage] = []

    def scan_all_workflows(self) -> List[SecretUsage]:
        """Scan all workflow files for secret patterns"""
        if not self.workflows_dir.exists():
            raise FileNotFoundError(
                f"Workflows directory not found: {self.workflows_dir}"
            )

        for file_path in self.workflows_dir.glob("*.yml"):
            self._scan_workflow_file(file_path)

        for file_path in self.workflows_dir.glob("*.yaml"):
            self._scan_workflow_file(file_path)

        return self.secret_usages

    def _scan_workflow_file(self, file_path: Path):
        """Scan a single workflow file for secret patterns"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Search for patterns line by line for better context
            for line_num, line in enumerate(lines, 1):
                self._find_patterns_in_line(file_path, line, line_num, lines)

            # Also try to parse as YAML to understand structure
            try:
                yaml_content = yaml.safe_load(content)
                self._analyze_yaml_structure(file_path, yaml_content, content)
            except yaml.YAMLError:
                # If YAML parsing fails, we still have the line-by-line analysis
                pass

        except Exception as e:
            print(f"Warning: Error scanning {file_path}: {e}")

    def _find_patterns_in_line(
        self, file_path: Path, line: str, line_num: int, all_lines: List[str]
    ):
        """Find secret patterns in a single line"""
        for pattern_type, pattern in self.patterns.items():
            matches = pattern.findall(line)
            for match in matches:
                if pattern_type == "supabase":
                    secret_name = match.replace("secrets.", "")
                elif pattern_type == "permits_url":
                    secret_name = match
                else:  # vercel_token or railway_token
                    secret_name = match

                # Determine if this usage appears to be required
                is_required = self._determine_if_required(
                    line, secret_name, line_num, all_lines
                )

                usage = SecretUsage(
                    file_path=str(
                        file_path.relative_to(file_path.parent.parent.parent)
                    ),
                    secret_name=secret_name,
                    pattern_type=pattern_type,
                    is_required=is_required,
                    context=line.strip(),
                    line_number=line_num,
                )
                self.secret_usages.append(usage)

    def _analyze_yaml_structure(
        self, file_path: Path, yaml_content: dict, raw_content: str
    ):
        """Analyze YAML structure to better understand secret usage"""
        # This could be expanded to analyze the workflow structure
        # For now, we rely on the line-by-line analysis
        pass

    def _determine_if_required(
        self, line: str, secret_name: str, line_num: int, all_lines: List[str]
    ) -> bool:
        """
        Determine if a secret usage is required or optional based on context.

        Heuristics:
        1. If there's explicit validation checking for empty/missing, it's REQUIRED
        2. If there's a fallback pattern with ||, check the context
        3. If it's in a conditional step (if: conditions), it might be optional
        4. If it's used in env sections without validation, assume required
        """
        line_lower = line.lower()

        # Look for explicit validation patterns around this secret
        context_start = max(0, line_num - 10)
        context_end = min(len(all_lines), line_num + 10)
        context_lines = all_lines[context_start:context_end]
        context_text = " ".join(context_lines).lower()

        # Strong indicators of REQUIRED status
        if any(
            pattern in context_text
            for pattern in [
                f'if [ -z "${{{{ {secret_name.lower()} }}}}"',
                f'if [ -z "${{{{ env.{secret_name.lower()} }}}}"',
                f'if [ -z "${{{{ secrets.{secret_name.lower()} }}}}"',
                f"{secret_name.lower()} secret is not set",
                f"{secret_name.lower()} is required",
                "exit 1",  # Usually indicates failure if missing
            ]
        ):
            return True

        # Check for fallback patterns that might indicate optional
        if "||" in line and "secrets." in line:
            # Look for patterns like: secrets.TOKEN || 'default' or secrets.TOKEN || secrets.FALLBACK
            # If it has a fallback, it might be optional, but check context
            if "default" in line.lower() or '""' in line or "''" in line:
                return False  # Has a default value, likely optional
            else:
                # Fallback to another secret, likely still required (just flexible source)
                return True

        # Check if this is in a conditional step
        for i in range(max(0, line_num - 5), line_num):
            if i < len(all_lines) and "if:" in all_lines[i]:
                # This secret is used in a conditional step, might be optional
                return False

        # Check for specific patterns that indicate optional usage
        if any(
            phrase in line_lower
            for phrase in [
                "slack_webhook",  # Notifications are often optional
                "optional",
                "if provided",
            ]
        ):
            return False

        # Default to required for safety - better to be conservative
        return True

    def get_unique_secrets(self) -> Set[str]:
        """Get set of unique secret names found"""
        return set(usage.secret_name for usage in self.secret_usages)

    def group_by_file(self) -> Dict[str, List[SecretUsage]]:
        """Group secret usages by file"""
        result = {}
        for usage in self.secret_usages:
            if usage.file_path not in result:
                result[usage.file_path] = []
            result[usage.file_path].append(usage)
        return result

    def generate_report(self) -> str:
        """Generate a formatted report of findings"""
        report = []
        report.append("# Workflow Secrets Scanner Report")
        report.append("")

        # Summary
        total_files = len(set(usage.file_path for usage in self.secret_usages))
        total_secrets = len(self.get_unique_secrets())
        total_usages = len(self.secret_usages)

        report.append("## Summary")
        report.append(
            f"- **Files scanned:** {len(list(self.workflows_dir.glob('*.yml')) + list(self.workflows_dir.glob('*.yaml')))}"
        )
        report.append(f"- **Files with secrets:** {total_files}")
        report.append(f"- **Unique secrets found:** {total_secrets}")
        report.append(f"- **Total secret usages:** {total_usages}")
        report.append("")

        # Patterns found
        report.append("## Patterns Found")
        for pattern_type in [
            "supabase",
            "permits_url",
            "vercel_token",
            "railway_token",
        ]:
            count = len(
                [u for u in self.secret_usages if u.pattern_type == pattern_type]
            )
            report.append(
                f"- **{pattern_type.replace('_', ' ').title()}:** {count} usages"
            )
        report.append("")

        # Detailed findings by file
        report.append("## Detailed Findings")
        by_file = self.group_by_file()

        for file_path in sorted(by_file.keys()):
            usages = by_file[file_path]
            report.append(f"### {file_path}")
            report.append("")

            # Group by secret name to avoid duplicates
            by_secret = {}
            for usage in usages:
                if usage.secret_name not in by_secret:
                    by_secret[usage.secret_name] = usage

            for secret_name in sorted(by_secret.keys()):
                usage = by_secret[secret_name]
                required_status = "**Required**" if usage.is_required else "*Optional*"
                report.append(f"- `{usage.secret_name}` - {required_status}")
                report.append(f"  - Pattern type: {usage.pattern_type}")
                report.append(f"  - Context: `{usage.context}`")
            report.append("")

        # All unique secrets summary
        report.append("## All Unique Secrets")
        report.append("")
        for secret in sorted(self.get_unique_secrets()):
            # Determine overall required status (if any usage is required, mark as required)
            is_required = any(
                u.is_required for u in self.secret_usages if u.secret_name == secret
            )
            status = "Required" if is_required else "Optional"
            files_count = len(
                set(u.file_path for u in self.secret_usages if u.secret_name == secret)
            )
            report.append(
                f"- `{secret}` - **{status}** (used in {files_count} file{'s' if files_count > 1 else ''})"
            )

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Scan GitHub workflow files for secret patterns"
    )
    parser.add_argument(
        "--workflows-dir",
        default=".github/workflows",
        help="Path to workflows directory (default: .github/workflows)",
    )
    parser.add_argument(
        "--output", help="Output file for report (default: print to stdout)"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "csv", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    args = parser.parse_args()

    # Find workflows directory
    workflows_dir = Path(args.workflows_dir)
    if not workflows_dir.is_absolute():
        # Try relative to current directory
        if not workflows_dir.exists():
            # Try relative to script directory
            script_dir = Path(__file__).parent.parent
            workflows_dir = script_dir / args.workflows_dir

    if not workflows_dir.exists():
        print(f"Error: Workflows directory not found: {workflows_dir}")
        return 1

    # Run scanner
    scanner = WorkflowSecretsScanner(str(workflows_dir))
    usages = scanner.scan_all_workflows()

    if not usages:
        print("No secret patterns found in workflow files.")
        return 0

    # Generate report
    if args.format == "markdown":
        report = scanner.generate_report()
    elif args.format == "csv":
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["File", "Secret Name", "Required", "Pattern Type", "Context"])

        for usage in usages:
            writer.writerow(
                [
                    usage.file_path,
                    usage.secret_name,
                    "Yes" if usage.is_required else "No",
                    usage.pattern_type,
                    usage.context,
                ]
            )
        report = output.getvalue()
    elif args.format == "json":
        import json

        report_data = {
            "summary": {
                "total_usages": len(usages),
                "unique_secrets": len(scanner.get_unique_secrets()),
                "files_with_secrets": len(set(u.file_path for u in usages)),
            },
            "usages": [
                {
                    "file_path": usage.file_path,
                    "secret_name": usage.secret_name,
                    "is_required": usage.is_required,
                    "pattern_type": usage.pattern_type,
                    "context": usage.context,
                    "line_number": usage.line_number,
                }
                for usage in usages
            ],
        }
        report = json.dumps(report_data, indent=2)

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    exit(main())
