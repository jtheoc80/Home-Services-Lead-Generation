# AI Review Guidelines

This document provides guidelines for the AI Auto-PR bot when generating pull requests for the Home Services Lead Generation repository.

## Repository Context

This is a lead generation platform for home service contractors focused on the Houston metropolitan area. The system processes building permit data to identify leads for contractors.

### Architecture
- **Frontend**: Next.js application in `frontend/` directory
- **Backend**: Python FastAPI application in `backend/` directory  
- **Database**: PostgreSQL with Supabase
- **Data Processing**: Permit scraping and lead generation scripts
- **Deployment**: Railway and Vercel platforms

## Code Standards

### General Principles
- **Minimal Changes**: Make the smallest possible changes to achieve the goal
- **Preserve Functionality**: Never break existing working features
- **Follow Patterns**: Maintain consistency with existing code patterns
- **Safety First**: Prefer conservative changes over aggressive refactoring

### Frontend (Next.js/React)
- Use TypeScript where already established
- Follow existing component structure and naming conventions
- Maintain existing styling patterns (Tailwind CSS)
- Preserve accessibility features
- Keep components focused and single-responsibility

### Backend (Python/FastAPI)
- Follow PEP 8 style guidelines
- Maintain existing API patterns and response formats
- Preserve authentication and authorization mechanisms
- Keep database models consistent
- Use type hints where already established

### Scripts and Automation
- Use Node.js built-ins only (no external dependencies)
- Follow existing script patterns in `scripts/` directory
- Make scripts executable with proper shebang
- Include error handling and logging
- Use environment variables for configuration

## Safety Guidelines

### File Handling
- **Always** preserve binary files unchanged
- Skip files larger than 1MB to avoid token limits
- Respect `.gitignore` patterns
- Avoid modifying generated files (build artifacts, etc.)

### Database and Configuration
- **Never** modify production database schemas without explicit instruction
- Preserve existing environment variable patterns
- Don't hardcode secrets or API keys
- Maintain backward compatibility for configuration

### Dependencies
- Avoid adding new dependencies unless explicitly required
- If dependencies must be added, prefer well-established packages
- Update package.json/requirements.txt appropriately
- Test dependency changes thoroughly

## Common Tasks

### Adding New Features
1. Follow existing architectural patterns
2. Add appropriate error handling
3. Include logging where relevant
4. Consider mobile responsiveness for frontend changes
5. Maintain API consistency for backend changes

### Bug Fixes
1. Identify root cause before implementing fix
2. Make minimal changes to resolve the issue
3. Preserve existing behavior in unrelated areas
4. Add defensive programming where appropriate

### Refactoring
1. Only refactor when explicitly requested
2. Maintain existing interfaces and contracts
3. Preserve functionality exactly
4. Update related documentation if needed

## Specific Repository Considerations

### Houston-Focused Scope
- This platform is specifically scoped to Houston Metro area
- Don't add features for other geographic regions unless explicitly requested
- Maintain county-specific data handling patterns

### Lead Generation Pipeline
- Preserve the permit data collection workflow
- Maintain lead scoring and notification systems
- Keep dashboard-only access pattern (no CSV exports)
- Respect rate limiting for external API calls

### Security Considerations
- This handles sensitive business data (leads, contractor information)
- Preserve authentication boundaries
- Maintain data access controls
- Don't expose internal system details in frontend

## Review Checklist

Before submitting changes, ensure:
- [ ] No breaking changes to existing functionality
- [ ] Code follows existing patterns and conventions
- [ ] No hardcoded secrets or credentials
- [ ] Changes are minimal and focused
- [ ] Error handling is appropriate
- [ ] Documentation updated if needed
- [ ] Mobile responsiveness maintained (frontend)
- [ ] API contracts preserved (backend)

## Common Pitfalls to Avoid

1. **Over-Engineering**: Don't add unnecessary complexity
2. **Breaking Changes**: Avoid modifying existing APIs or interfaces
3. **Scope Creep**: Stay focused on the specific instruction
4. **Dependency Hell**: Avoid unnecessary package additions
5. **Security Issues**: Don't expose sensitive data or weaken security
6. **Performance Regression**: Maintain existing performance characteristics
7. **Mobile Breakage**: Don't break responsive design patterns

## When to Ask for Clarification

The AI should request clarification when:
- The instruction conflicts with existing architecture
- Changes would require breaking existing functionality
- Multiple valid approaches exist with significant tradeoffs
- The scope is unclear or potentially very large
- Security implications are unclear

## Quality Gates

All AI-generated changes should:
- Build successfully without warnings
- Pass existing tests (if any)
- Maintain responsive design
- Follow existing error handling patterns
- Include appropriate logging
- Preserve accessibility features
- Maintain API compatibility