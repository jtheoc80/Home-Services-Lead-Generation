# Git Secrets Setup for Home Services Lead Generation

This document provides setup instructions for git-secrets to prevent accidentally committing sensitive information like API keys, tokens, and other secrets.

## 📋 Overview

The repository is configured with git-secrets to automatically scan for and block commits containing:

- **Supabase** service role keys (`sb-*`) and JWT tokens (`ey*`)
- **Vercel** API tokens (`vercel_*`) and deploy hooks
- **Railway** API keys (`railway_*`, `dapi_*`, `rw_*`)
- **AWS** credentials (standard patterns)

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

Run the setup script from the repository root:

```bash
./scripts/setup-git-secrets.sh
```

### Option 2: Manual Setup

1. **Install git-secrets**:
   ```bash
   # Clone and install git-secrets
   git clone https://github.com/awslabs/git-secrets.git /tmp/git-secrets
   cd /tmp/git-secrets
   make install
   ```

2. **Configure the repository**:
   ```bash
   # Navigate to your repository
   cd /path/to/Home-Services-Lead-Generation
   
   # Install git-secrets hooks
   git secrets --install
   
   # Register AWS patterns
   git secrets --register-aws
   
   # Add custom patterns
   git secrets --add 'sb-[A-Za-z0-9_-]{32,}'                    # Supabase service role keys
   git secrets --add 'ey[A-Za-z0-9_-]{40,}'                     # JWT tokens
   git secrets --add 'vercel_[A-Za-z0-9_-]{24,}'                # Vercel API tokens
   git secrets --add 'railway_[A-Za-z0-9_-]{32,}'               # Railway API keys
   git secrets --add 'dapi_[A-Za-z0-9_-]{40,}'                  # Railway Deploy API keys
   ```

## 🧪 Testing the Setup

### Run the Test Suite

```bash
# Run the comprehensive test suite
python tests/test_git_secrets.py

# Or run specific tests
python -m unittest tests.test_git_secrets.GitSecretsTest.test_supabase_service_role_key_detection
```

### Manual Testing

1. **Test scanning a file**:
   ```bash
   git secrets --scan path/to/file
   ```

2. **Test scanning the entire repository**:
   ```bash
   git secrets --scan-history
   ```

3. **Create a test file with a fake secret**:
   ```bash
   echo "SUPABASE_KEY=sb-example-fake-key-for-testing-only" > test_secret.txt
   git secrets --scan test_secret.txt
   # Should fail with exit code 1
   rm test_secret.txt
   ```

## 🔧 Patterns Being Monitored

### Supabase
- Service role keys: `sb-[A-Za-z0-9_-]{32,}`
- JWT tokens: `ey[A-Za-z0-9_-]{40,}`
- API keys: `supabase_[A-Za-z0-9_-]{32,}`

### Vercel
- API tokens: `vercel_[A-Za-z0-9_-]{24,}`
- Deploy hooks: `[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}_[A-Za-z0-9_-]{32,}`

### Railway
- API keys: `railway_[A-Za-z0-9_-]{32,}`
- Deploy API keys: `dapi_[A-Za-z0-9_-]{40,}`
- Tokens: `rw_[A-Za-z0-9_-]{32,}`

### AWS (Standard)
- Access keys, secret keys, and session tokens

## ✅ Allowed Patterns

The following placeholder values are explicitly allowed and won't trigger warnings:

- `your_supabase_jwt_secret_here`
- `your_mapbox_token_here`
- `your_google_api_key_here`
- `your_sendgrid_api_key_here`
- `your_twilio_account_sid_here`
- `your_twilio_auth_token_here`
- `sb-example-key-placeholder`
- `vercel_example_token`
- `railway_example_key`

## 🚫 What Happens When Secrets Are Detected

When git-secrets detects a potential secret:

1. **Pre-commit hook**: Blocks the commit and shows an error message
2. **Commit message hook**: Scans commit messages for secrets
3. **Manual scan**: Returns exit code 1 and shows details

Example output:
```
[ERROR] Matched one or more prohibited patterns

Possible mitigations:
- Mark false positives as allowed using: git secrets --add --allowed 'pattern'
- List your configured patterns: git secrets --list
- Add additional patterns: git secrets --add 'pattern'
```

## 🛠️ Common Commands

### View Current Configuration
```bash
git secrets --list
```

### Add a New Pattern
```bash
git secrets --add 'new_pattern_regex'
```

### Allow a Specific String
```bash
git secrets --add --allowed 'specific_string_to_allow'
```

### Scan Specific Files
```bash
git secrets --scan file1.txt file2.py
```

### Scan Entire Repository History
```bash
git secrets --scan-history
```

### Remove Git Secrets (if needed)
```bash
git secrets --uninstall
```

## 🆘 Troubleshooting

### False Positives

If git-secrets incorrectly flags legitimate content:

1. **Temporary bypass**: Use `git commit --no-verify` (not recommended)
2. **Permanent fix**: Add to allowed patterns:
   ```bash
   git secrets --add --allowed 'legitimate_string'
   ```

### Hook Not Running

If the pre-commit hook isn't running:

1. Check hook permissions:
   ```bash
   ls -la .git/hooks/pre-commit
   ```

2. Reinstall hooks:
   ```bash
   git secrets --install --force
   ```

### Pattern Not Working

To test a specific pattern:

1. Check current patterns:
   ```bash
   git secrets --list
   ```

2. Test pattern manually:
   ```bash
   echo "test_string" | git secrets --scan --stdin
   ```

## 📚 Additional Resources

- [Git Secrets GitHub Repository](https://github.com/awslabs/git-secrets)
- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [Regular Expression Testing](https://regex101.com/)

## 🔒 Security Best Practices

1. **Never commit real secrets**: Use environment variables and `.env` files (git-ignored)
2. **Use secret management services**: Consider AWS Secrets Manager, HashiCorp Vault, etc.
3. **Regular audits**: Periodically scan your repository history
4. **Team education**: Ensure all team members understand secret management
5. **Backup verification**: Always test git-secrets configuration before relying on it

## 📞 Support

If you encounter issues with git-secrets setup:

1. Check the troubleshooting section above
2. Review the test suite output for specific failures
3. Create an issue in the repository with:
   - Error messages
   - Steps to reproduce
   - Output of `git secrets --list`