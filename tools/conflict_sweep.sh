#!/bin/bash

# tools/conflict_sweep.sh
# Script to sweep and resolve git conflicts in the repository

set -euo pipefail

echo "🔍 Conflict Sweep Script"
echo "========================"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check for merge conflicts
echo "Checking for merge conflicts..."
conflicted_files=$(git diff --name-only --diff-filter=U 2>/dev/null || true)

if [ -z "$conflicted_files" ]; then
    echo "✅ No merge conflicts found"
else
    echo "⚠️  Found merge conflicts in:"
    echo "$conflicted_files"
    echo ""
    echo "To resolve conflicts, you can:"
    echo "1. Manually edit the files to resolve conflicts"
    echo "2. Use 'git checkout --ours <file>' to keep our version"
    echo "3. Use 'git checkout --theirs <file>' to keep their version"
    echo "4. Use the conflict resolver: npx tsx tools/bots/resolveConflicts.ts"
    exit 1
fi

# Check for uncommitted changes
echo "Checking for uncommitted changes..."
if ! git diff --quiet HEAD 2>/dev/null; then
    echo "⚠️  Found uncommitted changes:"
    git status --porcelain
    echo ""
    echo "Consider committing or stashing changes before proceeding"
else
    echo "✅ No uncommitted changes"
fi

# Check for untracked files that might cause conflicts
echo "Checking for untracked files..."
untracked_files=$(git ls-files --others --exclude-standard 2>/dev/null || true)

if [ -n "$untracked_files" ]; then
    echo "⚠️  Found untracked files:"
    echo "$untracked_files"
    echo ""
    echo "Consider adding to .gitignore or committing if needed"
else
    echo "✅ No problematic untracked files"
fi

# Check remote status
echo "Checking remote sync status..."
if git remote -v | grep -q origin; then
    git fetch origin > /dev/null 2>&1 || true
    
    current_branch=$(git branch --show-current)
    if git show-ref --verify --quiet "refs/remotes/origin/$current_branch"; then
        ahead=$(git rev-list --count HEAD..origin/$current_branch 2>/dev/null || echo "0")
        behind=$(git rev-list --count origin/$current_branch..HEAD 2>/dev/null || echo "0")
        
        if [ "$ahead" -gt 0 ]; then
            echo "⚠️  Branch is $ahead commits behind origin/$current_branch"
            echo "Consider: git pull origin $current_branch"
        elif [ "$behind" -gt 0 ]; then
            echo "ℹ️  Branch is $behind commits ahead of origin/$current_branch"
        else
            echo "✅ Branch is in sync with origin"
        fi
    else
        echo "ℹ️  Remote branch origin/$current_branch does not exist"
    fi
else
    echo "ℹ️  No remote 'origin' configured"
fi

echo ""
echo "🎉 Conflict sweep completed successfully!"