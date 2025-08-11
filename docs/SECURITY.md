# Security Configuration for Home Services Lead Generation Platform

## CodeQL Configuration
This project uses GitHub CodeQL for Static Application Security Testing (SAST). The configuration includes:
- **Languages**: JavaScript/TypeScript and Python
- **Query Suites**: security-extended and security-and-quality
- **Schedule**: Daily at 2 AM UTC, plus on push/PR to main/develop branches

## Dependency Auditing Configuration

### npm audit
- **Severity Threshold**: moderate (blocks moderate, high, and critical vulnerabilities)
- **Scope**: Production dependencies only (`--omit=dev`)
- **Coverage**: Root package and frontend package

### pip-audit
- **Vulnerability Service**: PyPI advisory database
- **Format**: Columns format for readable output
- **Coverage**: backend/requirements.txt and permit_leads/requirements.txt
- **Timeout**: 300 seconds to handle network latency

## License Compliance Configuration

### Allowed Licenses
The following licenses are permitted for dependencies:
- **MIT**: Most permissive, widely used
- **Apache-2.0**: Permissive with patent protection
- **BSD-2-Clause**: Simplified BSD license
- **BSD-3-Clause**: Original BSD license
- **ISC**: Functionally equivalent to MIT
- **Unlicense**: Public domain
- **WTFPL**: Do What The F*ck You Want To Public License
- **CC0-1.0**: Creative Commons public domain dedication
- **CC-BY-4.0**: Creative Commons attribution license
- **0BSD**: Zero-clause BSD license
- **UNLICENSED**: For private/internal packages

### Prohibited Licenses
The following licenses will cause the build to fail:
- **GPL-3.0**: Strong copyleft requirements
- **AGPL-3.0**: Network copyleft (affects SaaS deployments)
- **LGPL-3.0**: Lesser GPL with linking restrictions

### License Check Process
1. **Node.js**: Uses `license-checker` package to scan npm dependencies
2. **Python**: Uses `pip-licenses` package with isolated virtual environments
3. **Enforcement**: Build fails if any prohibited licenses are detected

## Workflow Integration
The security checks run as a separate workflow (`security.yml`) that:
1. Runs in parallel with existing CI/CD pipelines
2. Provides detailed security reports
3. Fails the overall check if any security issue is detected
4. Runs on the same triggers as the main CI workflow

## Monitoring and Maintenance
- **Daily Scans**: Automated security scans run daily to catch new vulnerabilities
- **PR Integration**: All pull requests trigger security checks
- **License Updates**: Regularly review and update the allowed/prohibited license lists
- **Threshold Tuning**: Adjust severity thresholds based on project risk tolerance

## Troubleshooting Common Issues

### CodeQL Analysis Fails
- Check that all required dependencies are properly installed
- Verify that the code compiles without errors
- Review CodeQL logs for specific analysis issues

### npm audit Failures
- Run `npm audit` locally to see specific vulnerabilities
- Consider updating dependencies to patch versions
- Use `npm audit fix` for automatic fixes where possible

### pip-audit Timeouts
- Check network connectivity to PyPI
- Consider using a local PyPI mirror for faster dependency resolution
- Adjust timeout values if needed

### License Compliance Failures
- Review the specific license causing the failure
- Evaluate if the license should be added to the allowed list
- Consider alternative packages with compatible licenses
- Document any license exceptions that are approved