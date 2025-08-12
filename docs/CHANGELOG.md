# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Bot Control Compatibility Layer (`tools/bots/index.ts`)
- New consolidated bot commands under `botctl`:
  - `audit:qb` - Environment and security auditing (replaces Env Auditor)
  - `e2e:jt` - End-to-end smoke testing (replaces E2E Smoke)  
  - `db:wire` - Database setup and schema validation (replaces DB setup)

### Changed
- **BREAKING (60-day timeline)**: Bots consolidated under botctl. Old names still work via shims; removal in 60 days.

### Deprecated
- Legacy bot command names:
  - `env-auditor`, `audit-env`, `env:audit` → Use `botctl audit:qb`
  - `e2e-smoke`, `smoke-e2e`, `e2e:smoke` → Use `botctl e2e:jt`
  - `db-setup`, `setup-db`, `db:setup`, `schema:setup` → Use `botctl db:wire`
- Legacy shim scripts in `scripts/legacy/` directory
- **Timeline**: Legacy support will be removed in 60 days from this release

### Migration Guide

#### For Direct Script Usage:
```bash
# Old
npm run e2e:smoke
tsx scripts/env-auditor.ts
tsx scripts/db-setup.ts

# New  
npx tsx tools/bots/index.ts e2e:jt
npx tsx tools/bots/index.ts audit:qb
npx tsx tools/bots/index.ts db:wire
```

#### For GitHub Actions:
```yaml
# Old
- run: tsx scripts/legacy/e2e-smoke.ts

# New (recommended)
- run: npx tsx tools/bots/index.ts e2e:jt

# Or use npm scripts directly
- run: npm run e2e:smoke
```

#### Migration Checklist:
- [ ] Update GitHub Actions workflows to use new command names
- [ ] Update documentation and README files
- [ ] Update CI/CD pipelines and automation scripts
- [ ] Train team members on new command structure
- [ ] Set calendar reminder for legacy removal date

### Notes
- All legacy commands currently forward to their new equivalents
- Deprecation warnings are shown when using legacy commands
- Use `npx tsx tools/bots/index.ts migrate-help` for detailed migration guidance
- Legacy shims provide backward compatibility during transition period