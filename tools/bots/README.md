# Bot Control (botctl) - Compatibility Layer

This directory contains the Bot Control compatibility layer that consolidates legacy bot commands under a unified `botctl` interface.

## 🚨 Migration Notice

**Legacy bot commands are deprecated and will be removed in 60 days.**

All bot functionality has been consolidated under `botctl` with new command names. Legacy commands still work via compatibility shims, but you should migrate to the new names.

## Quick Start

```bash
# Show migration guide
npm run botctl:help

# Run new commands
npm run botctl:audit:qb    # Environment/security audit
npm run botctl:e2e:jt      # E2E smoke tests  
npm run botctl:db:wire     # Database setup/validation

# Or use directly
npx tsx tools/bots/index.ts audit:qb
npx tsx tools/bots/index.ts e2e:jt
npx tsx tools/bots/index.ts db:wire
```

## Command Mappings

| Legacy Command | New Command | Description |
|----------------|-------------|-------------|
| `env-auditor`, `audit-env`, `env:audit` | `audit:qb` | Environment and security auditing |
| `e2e-smoke`, `smoke-e2e`, `e2e:smoke` | `e2e:jt` | End-to-end smoke testing |
| `db-setup`, `setup-db`, `db:setup`, `schema:setup` | `db:wire` | Database setup and schema validation |

## For GitHub Actions

### Current (works but deprecated):
```yaml
- name: Run E2E tests
  run: tsx scripts/legacy/e2e-smoke.ts
```

### Recommended:
```yaml
- name: Run E2E tests  
  run: npm run botctl:e2e:jt
  # or: npx tsx tools/bots/index.ts e2e:jt
```

## Files Structure

```
tools/bots/
├── index.ts              # Main botctl compatibility layer
└── README.md             # This file

scripts/legacy/           # Temporary shim scripts (deprecated)
├── env-auditor.ts        # @deprecated - use botctl audit:qb
├── e2e-smoke.ts          # @deprecated - use botctl e2e:jt  
└── db-setup.ts           # @deprecated - use botctl db:wire
```

## Testing

```bash
# Test compatibility layer
npm run test:botctl

# Test individual commands
npx tsx tools/bots/index.ts migrate-help
npx tsx tools/bots/index.ts e2e-smoke --help
```

## Migration Checklist

- [ ] Update GitHub Actions workflows to use new command names
- [ ] Update documentation and README files  
- [ ] Update CI/CD pipelines and automation scripts
- [ ] Train team members on new command structure
- [ ] Set calendar reminder for legacy removal date (60 days)

## Timeline

- **Now**: Legacy commands work via shims with deprecation warnings
- **60 days**: Legacy commands and shims will be removed
- **Action Required**: Update all references to use new `botctl` commands

## Support

For questions about migration or issues with the compatibility layer:

1. Run `npm run botctl:help` for detailed migration guidance
2. Check `docs/CHANGELOG.md` for complete migration information
3. Test changes with `npm run test:botctl`