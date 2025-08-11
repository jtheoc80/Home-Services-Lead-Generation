# Dependabot Configuration

This repository now has automated dependency management configured via Dependabot.

## How it works

### 1. Dependency Monitoring
Dependabot monitors the following dependencies:
- **Frontend npm dependencies** (`frontend/package.json`)
- **Root npm dependencies** (`package.json`)
- **Backend Python dependencies** (`backend/requirements.txt`)
- **Permit leads Python dependencies** (`permit_leads/requirements.txt`)
- **GitHub Actions** (`.github/workflows/*.yml`)

### 2. Update Schedule
- **npm/pip dependencies**: Weekly on Mondays at 9:00 AM
- **GitHub Actions**: Monthly

### 3. Automated Workflow

When Dependabot creates a PR:

#### Patch Updates (e.g., 1.0.0 → 1.0.1)
- Automatically runs full test suite
- If tests pass ✅: Auto-approved and merged
- If tests fail ❌: Requires manual review

#### Minor/Major Updates (e.g., 1.0.0 → 1.1.0 or 2.0.0)
- Automatically runs full test suite
- Labeled with `needs-testing` regardless of test results
- Requires maintainer review before merging
- Comment added explaining the review requirement

### 4. Test Suite
The automated workflow runs:
- Environment validation
- Dependency installation
- Linting (tolerates pre-existing issues)
- Type checking (tolerates pre-existing issues)
- Build process (tolerates pre-existing issues)
- Compatibility tests for major dependencies
- Health checks where possible

### 5. Labels Applied
- `dependencies` - All dependency updates
- `frontend` / `backend` / `permit-leads` / `workspace` - Component-specific
- `auto-merge` - Patch updates that passed tests
- `needs-testing` - Minor/major updates requiring review
- `patch-update` / `minor-update` / `major-update` - Update type classification

## Manual Overrides

Maintainers can:
- Manually approve any PR to override auto-merge restrictions
- Add additional labels or reviewers as needed
- Close unwanted dependency updates
- Configure update schedules in `.github/dependabot.yml`

## Security Benefits

- Regular updates reduce vulnerability exposure
- Automated testing catches breaking changes early
- Conservative approach for major version updates
- Maintains audit trail of all dependency changes