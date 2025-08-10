# Stack Monitor Bot Setup and Configuration

This document provides comprehensive guidance for setting up and configuring the `stack-monitor-bot` GitHub user account for automated monitoring and remediation workflows in the Home Services Lead Generation platform.

## Table of Contents

- [Bot Overview](#bot-overview)
- [Bot User Setup](#bot-user-setup)
- [Repository Collaboration](#repository-collaboration)
- [Fine-Grained Personal Access Token](#fine-grained-personal-access-token)
- [Token Storage and Usage](#token-storage-and-usage)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Bot Overview

### Bot Identity
- **Username**: `stack-monitor-bot`
- **Purpose**: Automated stack monitoring, health checks, and remediation
- **Repository Role**: Collaborator with write access
- **Primary Functions**:
  - Monitor stack health (Vercel, Railway, Supabase)
  - Create and update GitHub issues for detected problems
  - Trigger AI auto-remediation workflows
  - Generate automated pull requests for fixes

### Current Integrations
The `stack-monitor-bot` is integrated with the following workflows:
- **[Stack Monitor Workflow](../../.github/workflows/stack-monitor.yml)** - Runs health checks every 10 minutes
- **[AI Auto-PR Workflow](../../.github/workflows/ai-autopr.yml)** - Generates automated fix PRs
- **[Stack Health Script](../../scripts/stack-health.js)** - Core monitoring logic

---

## Bot User Setup

### 1. Create GitHub User Account

1. **Create a new GitHub account**:
   ```
   Username: stack-monitor-bot
   Email: stack-monitor-bot@yourdomain.com (use organization email)
   ```

2. **Configure the account**:
   - Set a clear profile name: "Stack Monitor Bot"
   - Add profile description: "Automated stack monitoring for [Organization]"
   - Upload a bot avatar (optional but recommended)

3. **Enable two-factor authentication** (required for fine-grained PATs):
   - Go to Settings → Password and authentication
   - Enable 2FA using an authenticator app
   - Save recovery codes securely

### 2. Verify Account Setup

```bash
# Test account access (replace with actual bot username)
curl -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/users/stack-monitor-bot
```

**Expected Response:**
```json
{
  "login": "stack-monitor-bot",
  "id": 123456789,
  "type": "User",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## Repository Collaboration

### Adding Bot as Repository Collaborator

#### Method 1: GitHub Web Interface

1. **Navigate to repository settings**:
   - Go to `https://github.com/[owner]/[repo]/settings/access`
   - Click "Manage access" → "Invite a collaborator"

2. **Add the bot user**:
   - Enter username: `stack-monitor-bot`
   - Select role: **Write** (required for creating issues and PRs)
   - Send invitation

3. **Accept invitation** (from bot account):
   - Log in as `stack-monitor-bot`
   - Go to GitHub notifications or check email
   - Accept the collaboration invitation

#### Method 2: GitHub CLI

```bash
# Add collaborator with write access
gh api repos/:owner/:repo/collaborators/stack-monitor-bot \
  --method PUT \
  --field permission=push

# Verify collaborator was added
gh api repos/:owner/:repo/collaborators/stack-monitor-bot
```

#### Method 3: GitHub API

```bash
# Add collaborator (requires admin token)
curl -X PUT \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_ADMIN_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/collaborators/stack-monitor-bot \
  -d '{"permission":"push"}'
```

### Required Permissions

The bot needs **Write** access to perform:
- ✅ Create and update issues
- ✅ Create pull requests
- ✅ Read repository contents
- ✅ Write to repository (for automated fixes)
- ✅ Access to repository secrets (for workflow triggers)

**Note**: Admin access is not required and should be avoided for security.

---

## Fine-Grained Personal Access Token

### Why Fine-Grained PATs?

Fine-grained Personal Access Tokens provide:
- **Specific repository access** (instead of all repositories)
- **Granular permissions** (only what the bot needs)
- **Better security** (limited scope reduces risk)
- **Audit trail** (better tracking of bot actions)

### Token Generation Steps

#### 1. Create Fine-Grained PAT

1. **Log in as `stack-monitor-bot`**

2. **Navigate to token settings**:
   - Go to Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Click "Generate new token"

3. **Configure token settings**:
   ```
   Token name: Home-Services-Stack-Monitor
   Expiration: 90 days (or per security policy)
   Description: Stack monitoring and auto-remediation for Home Services Lead Generation platform
   ```

4. **Select repository access**:
   - Choose "Selected repositories"
   - Add: `jtheoc80/Home-Services-Lead-Generation`

#### 2. Configure Repository Permissions

**Required permissions for stack monitoring:**

| Permission Category | Specific Permission | Access Level | Purpose |
|-------------------|-------------------|------------|---------|
| **Repository permissions** | | | |
| Actions | Actions | Read | Read workflow status |
| Contents | Contents | Read | Access repository files |
| Issues | Issues | Write | Create/update monitoring issues |
| Metadata | Metadata | Read | Access repository metadata |
| Pull requests | Pull requests | Write | Create automated fix PRs |
| **Account permissions** | | | |
| (None required) | | | |

**Detailed permission configuration:**
```json
{
  "actions": "read",
  "contents": "read", 
  "issues": "write",
  "metadata": "read",
  "pull_requests": "write"
}
```

#### 3. Generate and Secure Token

1. **Generate the token**:
   - Review permissions carefully
   - Click "Generate token"
   - **Copy the token immediately** (it will only be shown once)

2. **Secure token storage**:
   ```bash
   # Example token format (not a real token)
   github_pat_11ABCDEFG_xyzabcdefghijklmnopqrstuvwxyz123456789
   ```

### Token Validation

Test the token after generation:

```bash
# Test token access
curl -H "Authorization: token github_pat_11ABCDEFG_xyz..." \
  https://api.github.com/repos/jtheoc80/Home-Services-Lead-Generation

# Test specific permissions
curl -H "Authorization: token github_pat_11ABCDEFG_xyz..." \
  https://api.github.com/repos/jtheoc80/Home-Services-Lead-Generation/issues

# Test write access (create a test issue)
curl -X POST \
  -H "Authorization: token github_pat_11ABCDEFG_xyz..." \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/jtheoc80/Home-Services-Lead-Generation/issues \
  -d '{"title":"Bot Token Test","body":"Testing stack-monitor-bot access"}'
```

---

## Token Storage and Usage

### GitHub Repository Secrets

#### 1. Store Bot Token

**Add to repository secrets:**
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secret:
   ```
   Name: GITHUB_TOKEN_BOT
   Value: github_pat_11ABCDEFG_xyz... (the fine-grained PAT)
   ```

#### 2. Update Workflow Configurations

**Stack Monitor Workflow Usage:**
```yaml
# .github/workflows/stack-monitor.yml
jobs:
  stack-health-check:
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN_BOT }}  # Use bot token
          
      - name: Create or update GitHub issue
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN_BOT }}  # Use bot token
          script: |
            // Issue creation logic using bot identity
```

**AI Auto-PR Workflow Usage:**
```yaml
# .github/workflows/ai-autopr.yml
jobs:
  ai-autopr:
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN_BOT }}  # Use bot token for commits
          
      - name: Run AI Auto-PR script
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN_BOT }}  # Use bot token
```

### Token Usage Guidelines

#### When to Use `GITHUB_TOKEN_BOT` vs `GITHUB_TOKEN`

| Scenario | Use Token | Reason |
|----------|-----------|---------|
| **Stack monitoring issues** | `GITHUB_TOKEN_BOT` | Bot identity for automated issues |
| **Auto-remediation PRs** | `GITHUB_TOKEN_BOT` | Bot authorship for fixes |
| **Health check comments** | `GITHUB_TOKEN_BOT` | Consistent bot identity |
| **Manual workflows** | `GITHUB_TOKEN` | Human-initiated actions |
| **Security-sensitive operations** | `GITHUB_TOKEN` | Require human authorization |
| **Read-only operations** | Either | Both have read access |

#### Workflow Implementation Examples

**Conditional token usage:**
```yaml
# Use bot token for automated operations
- name: Automated stack monitoring
  if: github.event_name == 'schedule'
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN_BOT }}
  run: ./scripts/stack-health.js

# Use default token for manual operations  
- name: Manual troubleshooting
  if: github.event_name == 'workflow_dispatch'
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: ./scripts/manual-debug.js
```

**Bot identification in commits:**
```yaml
- name: Configure Git for bot commits
  run: |
    git config user.name "stack-monitor-bot"
    git config user.email "stack-monitor-bot@yourdomain.com"
```

---

## Security Best Practices

### Token Security

#### 1. Never Commit Secrets to Code

**❌ NEVER do this:**
```javascript
// WRONG - Never hardcode tokens
const token = "github_pat_11ABCDEFG_xyz...";
```

**✅ Always use environment variables:**
```javascript
// CORRECT - Use environment variables
const token = process.env.GITHUB_TOKEN_BOT;
if (!token) {
  throw new Error('GITHUB_TOKEN_BOT environment variable is required');
}
```

#### 2. Implement Token Validation

```javascript
// Token validation example
function validateGitHubToken(token) {
  if (!token) {
    throw new Error('GitHub token is required');
  }
  
  if (!token.startsWith('github_pat_') && !token.startsWith('ghp_')) {
    throw new Error('Invalid GitHub token format');
  }
  
  return token;
}

const botToken = validateGitHubToken(process.env.GITHUB_TOKEN_BOT);
```

#### 3. Log Security Events

**Safe logging (never log tokens):**
```javascript
// GOOD - Log token usage without exposing values
console.log('Using GitHub bot token for automated operation');
console.log(`Token type: ${token.startsWith('github_pat_') ? 'fine-grained' : 'classic'}`);
console.log(`Token prefix: ${token.substring(0, 15)}...`);

// NEVER log the full token
// console.log(`Token: ${token}`); // ❌ NEVER DO THIS
```

### Regular Security Maintenance

#### 1. Token Rotation Schedule

**Recommended rotation frequency:**
- **Production environments**: Every 90 days
- **Development environments**: Every 30 days
- **After security incidents**: Immediately

**Rotation procedure:**
```bash
# 1. Generate new fine-grained PAT (follow steps above)
# 2. Test new token
curl -H "Authorization: token NEW_TOKEN" https://api.github.com/user

# 3. Update GitHub repository secrets
# 4. Verify workflows work with new token
# 5. Revoke old token
```

#### 2. Access Monitoring

**Regular audits:**
```bash
# List collaborators
gh api repos/:owner/:repo/collaborators

# Check bot's recent activity
gh api users/stack-monitor-bot/events | jq '.[:5]'

# Review repository access
gh api user/repos --header "Authorization: token BOT_TOKEN"
```

#### 3. Scope Limitation

**Principle of least privilege:**
- ✅ Only grant required repository access
- ✅ Use most restrictive permissions possible
- ✅ Regularly review and reduce permissions
- ❌ Avoid organization-wide access
- ❌ Don't grant admin permissions unless absolutely necessary

### Emergency Security Procedures

#### 1. Token Compromise Response

**If you suspect token compromise:**

1. **Immediate actions:**
   ```bash
   # Revoke the compromised token immediately
   # Go to GitHub Settings → Developer settings → Personal access tokens
   # Click "Delete" on the compromised token
   ```

2. **Generate new token:**
   - Follow the [token generation steps](#fine-grained-personal-access-token)
   - Use different permissions if compromise was due to over-permissioning

3. **Update repository secrets:**
   - Replace `GITHUB_TOKEN_BOT` with new token
   - Verify all workflows still function

4. **Audit repository activity:**
   ```bash
   # Check for unauthorized changes
   git log --author="stack-monitor-bot" --since="1 week ago"
   
   # Review recent issues and PRs
   gh issue list --author="stack-monitor-bot"
   gh pr list --author="stack-monitor-bot"
   ```

#### 2. Repository Access Review

**Quarterly security review checklist:**
- [ ] Verify bot still needs repository access
- [ ] Review bot's recent activity for anomalies
- [ ] Confirm token permissions are still appropriate
- [ ] Test token functionality
- [ ] Check for any unauthorized repository access
- [ ] Review and update this documentation

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Token Authentication Failures

**Symptoms:**
- 401 Unauthorized errors in workflows
- "Bad credentials" API responses
- Workflows failing at authentication steps

**Quick Checks:**
```bash
# Test token validity
curl -I -H "Authorization: token $GITHUB_TOKEN_BOT" \
  https://api.github.com/user

# Check token permissions
curl -H "Authorization: token $GITHUB_TOKEN_BOT" \
  https://api.github.com/repos/:owner/:repo \
  -w "%{http_code}"
```

**Solutions:**
1. **Verify token in repository secrets**:
   - Go to repository Settings → Secrets and variables → Actions
   - Confirm `GITHUB_TOKEN_BOT` exists and is correctly formatted

2. **Check token expiration**:
   - Fine-grained PATs have expiration dates
   - Generate new token if expired

3. **Verify repository access**:
   - Ensure bot is still a collaborator
   - Check that repository permissions haven't changed

#### 2. Insufficient Permissions

**Symptoms:**
- 403 Forbidden errors when creating issues/PRs
- "Resource not accessible by integration" errors
- Workflows can read but not write

**Debugging:**
```bash
# Test specific permission
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN_BOT" \
  https://api.github.com/repos/:owner/:repo/issues \
  -d '{"title":"Permission Test"}'

# Check current permissions
curl -H "Authorization: token $GITHUB_TOKEN_BOT" \
  https://api.github.com/repos/:owner/:repo/collaborators/stack-monitor-bot/permission
```

**Solutions:**
1. **Verify collaborator permissions**:
   - Bot needs "Write" access (not just "Read")
   - Check repository collaboration settings

2. **Update fine-grained PAT permissions**:
   - Go to token settings → Edit token
   - Ensure "Issues: Write" and "Pull requests: Write" are enabled

#### 3. Bot Identity Issues

**Symptoms:**
- Actions appear under wrong user
- Git commits have incorrect author
- Issues/PRs not attributed to bot

**Solutions:**
```yaml
# Set git identity in workflows
- name: Configure Git for bot
  run: |
    git config user.name "stack-monitor-bot"
    git config user.email "stack-monitor-bot@homeservicesleadgen.com" # Replace with your actual organization domain if different

# Use bot token consistently
- name: Use bot token for all operations
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN_BOT }}
```

### Diagnostic Commands

#### Repository Access Check
```bash
# Verify bot can access repository
curl -H "Authorization: token $GITHUB_TOKEN_BOT" \
  https://api.github.com/repos/jtheoc80/Home-Services-Lead-Generation

# Check collaborator status
curl -H "Authorization: token $GITHUB_TOKEN_BOT" \
  https://api.github.com/repos/jtheoc80/Home-Services-Lead-Generation/collaborators/stack-monitor-bot
```

#### Workflow Debugging
```bash
# Check recent workflow runs
gh run list --workflow=stack-monitor.yml --limit=5

# Get specific workflow run logs
gh run view RUN_ID --log

# Test workflow manually
gh workflow run stack-monitor.yml
```

#### Token Information
```bash
# Get token information (safe - doesn't expose token)
curl -H "Authorization: token $GITHUB_TOKEN_BOT" \
  https://api.github.com/user | jq '{login, type, created_at}'

# Check rate limits
curl -H "Authorization: token $GITHUB_TOKEN_BOT" \
  https://api.github.com/rate_limit
```

---

## Support and Resources

### Related Documentation
- **[Operations Runbooks](./runbooks.md)** - Comprehensive troubleshooting guides
- **[Stack Monitor Documentation](../STACK_MONITOR.md)** - Technical implementation details
- **[GitHub Actions Runbook](../github-actions-runbook.md)** - Workflow troubleshooting

### External Resources
- **[GitHub Fine-grained PATs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-fine-grained-personal-access-token)** - Official documentation
- **[GitHub REST API](https://docs.github.com/en/rest)** - API reference
- **[GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)** - Secret management

### Emergency Contacts
- **Repository Owner**: [Repository Settings](https://github.com/jtheoc80/Home-Services-Lead-Generation/settings)
- **GitHub Support**: https://support.github.com (for platform issues)
- **Security Team**: contact_security@yourdomain.com (for security incidents)

---

*Last updated: January 2025*
*Document version: 1.0*
*Next review: April 2025*