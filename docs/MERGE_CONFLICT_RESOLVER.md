# Merge Conflict Resolver Workflow

This workflow provides automated merge conflict resolution for pull requests using different strategies.

## Usage

The workflow is triggered manually using `workflow_dispatch` with the following inputs:

### Inputs

- **pr_number** (required): The pull request number to resolve conflicts for
- **strategy** (required): The merge conflict resolution strategy to use

### Strategy Options

#### `safe` (Default)
Conservative approach that only auto-resolves specific file types:
- **Documentation files**: `*.md`, `*.txt`, `CHANGELOG*`, `README*` → Uses "theirs" strategy
- **Configuration files**: `*.json`, `*.yml`, `*.yaml` → Uses "theirs" strategy  
- **Lock files**: `package-lock.json`, `*.lock`, `yarn.lock`, `poetry.lock` → Uses "theirs" strategy
- **Code files**: Requires manual resolution

#### `theirs-all`
Accepts all incoming changes from the PR branch for all conflicted files.

#### `ours-all`
Keeps all current changes from the base branch for all conflicted files.

## Example Usage for PR 175

To resolve conflicts in PR 175 using the safe strategy:

```yaml
# Manual trigger via GitHub Actions UI
pr_number: 175
strategy: safe
```

Or via GitHub CLI:

```bash
# Safe strategy (recommended)
gh workflow run merge-conflict-resolver.yml -f pr_number=175 -f strategy=safe

# Accept all incoming changes
gh workflow run merge-conflict-resolver.yml -f pr_number=175 -f strategy=theirs-all

# Keep all current changes
gh workflow run merge-conflict-resolver.yml -f pr_number=175 -f strategy=ours-all
```

## Workflow Process

1. **Validation**: Validates PR number and fetches PR information
2. **Branch Setup**: Fetches base and head branches, handles forks
3. **Merge Attempt**: Attempts merge with the specified strategy
4. **Path-based Resolution**: Applies conflict resolution rules based on file paths
5. **Commit & Push**: Commits resolved changes to a new branch
6. **Status Report**: Comments on the PR with resolution results

## Path-based Rules (Safe Strategy)

The `safe` strategy applies different resolution approaches based on file paths:

| File Type | Pattern | Resolution | Rationale |
|-----------|---------|------------|-----------|
| Documentation | `*.md`, `*.txt`, `README*`, `CHANGELOG*` | Accept incoming (theirs) | Documentation updates are usually additive |
| Configuration | `*.json`, `*.yml`, `*.yaml` | Accept incoming (theirs) | Config changes often come from feature branches |
| Lock files | `package-lock.json`, `*.lock`, `yarn.lock`, `poetry.lock` | Accept incoming (theirs) | Lock files should reflect latest dependencies |
| Code files | `*.js`, `*.ts`, `*.py`, etc. | Manual resolution required | Code conflicts need human review |

## Output

### Success
- Creates a new branch with resolved conflicts
- Pushes the resolved changes
- Comments on the PR with success details
- Provides workflow summary

### Failure  
- Lists files that still require manual resolution
- Comments on the PR with failed conflict details
- Fails the workflow to prevent silent issues

## Requirements

- PR must be in OPEN state
- Workflow requires `contents: write` and `pull-requests: write` permissions
- GitHub CLI (`gh`) is used for API interactions

## Limitations

- Cannot resolve semantic conflicts (code that merges cleanly but breaks functionality)
- Complex conflicts in code files require manual intervention
- Fork PRs require proper remote setup (handled automatically)

## Security Considerations

- Only accepts pre-defined strategy values
- Uses GitHub Actions bot for commits
- Requires appropriate repository permissions
- All actions are logged and auditable