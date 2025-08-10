# Operations Runbooks

This document provides troubleshooting guides and operational procedures for the Home Services Lead Generation platform across three main infrastructure platforms: Vercel, Railway, and Supabase.

## Table of Contents

- [Vercel Troubleshooting](#vercel-troubleshooting)
- [Railway Troubleshooting](#railway-troubleshooting) 
- [Supabase Troubleshooting](#supabase-troubleshooting)
- [Health Monitoring](#health-monitoring)
- [Related Scripts](#related-scripts)

---

## Vercel Troubleshooting

### Common Failures

#### Missing Environment Variables
**Symptoms:**
- Build fails with "Environment variable not found" errors
- Application starts but API calls fail with 500 errors
- Supabase connection errors
- Missing NEXT_PUBLIC_* variables cause client-side failures

**Quick Checks:**
```bash
# Check if environment variables are set
vercel env ls --scope production
vercel env ls --scope preview
vercel env ls --scope development

# Specifically check for required NEXT_PUBLIC_ variables
vercel env ls | grep NEXT_PUBLIC
```

**Remediation:**
1. Use the automated setup script:
   ```bash
   ./scripts/set-vercel-supabase-env.sh
   ```

2. Or manually set required variables (including NEXT_PUBLIC_ variables):
   ```bash
   # Core Supabase variables
   vercel env add NEXT_PUBLIC_SUPABASE_URL production
   vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
   vercel env add SUPABASE_SERVICE_ROLE_KEY production
   
   # Application configuration
   vercel env add NEXT_PUBLIC_ENVIRONMENT production
   vercel env add NEXT_PUBLIC_DEFAULT_REGION production
   vercel env add NEXT_PUBLIC_LAUNCH_SCOPE production
   
   # Feature flags (examples based on .env.example)
   vercel env add NEXT_PUBLIC_FEATURE_LEAD_SCORING production
   vercel env add NEXT_PUBLIC_FEATURE_NOTIFICATIONS production
   vercel env add NEXT_PUBLIC_REALTIME_UPDATES production
   ```

3. Verify deployment environment configuration in `vercel.json`:
   ```json
   {
     "env": {
       "SKIP_ENV_VALIDATION": "1",
       "DISABLE_ESLINT": "true"
     }
   }
   ```

#### Wrong Root Directory
**Symptoms:**
- Build fails with "No package.json found"
- Vercel deploys root instead of frontend
- Build command not found

**Quick Checks:**
```bash
# Verify vercel.json configuration
cat vercel.json | grep -E "(buildCommand|outputDirectory|installCommand)"
```

**Current Expected Configuration:**
```json
{
  "buildCommand": "cd frontend && npm run build:production",
  "outputDirectory": "frontend/.next", 
  "installCommand": "cd frontend && npm install",
  "framework": "nextjs"
}
```

**Remediation:**
1. Ensure all commands include `cd frontend &&` prefix
2. Verify `outputDirectory` points to `frontend/.next`
3. Check that `installCommand` installs in frontend directory

#### Build Command Issues
**Symptoms:**
- ESLint errors blocking build
- TypeScript compilation failures
- Missing dependencies

**Quick Checks:**
```bash
# Test build locally
cd frontend && npm run build:production

# Check for linting issues
cd frontend && npm run lint

# Verify dependencies
cd frontend && npm audit
```

**Remediation:**
1. For ESLint blocking builds, the production build already disables it:
   ```json
   "build:production": "DISABLE_ESLINT=true next build"
   ```

2. For TypeScript errors:
   ```bash
   cd frontend && npx tsc --noEmit
   ```

3. For missing dependencies:
   ```bash
   cd frontend && npm install
   ```

#### Deployment Commands

#### Fetch Deployment Logs
```bash
# Get recent deployment logs
vercel logs <deployment-url>

# Get logs for specific function
vercel logs <deployment-url> --function=/api/health

# Stream live logs during deployment
vercel --prod --logs

# Get latest deployment and logs
vercel ls --limit=1 && vercel logs $(vercel ls --limit=1 | tail -1 | awk '{print $1}')
```

#### Redeploy Latest
```bash
# Get latest deployment URL
./scripts/vercel-latest-url.sh

# Redeploy from CLI
vercel --prod

# Force redeploy (bypass cache)
vercel --prod --force
```

#### Rollback Deployment
```bash
# List recent deployments
vercel ls

# Get specific deployment details
vercel inspect <deployment-url>

# Promote previous deployment
vercel promote <previous-deployment-url>
```

#### Environment Management
```bash
# List all environments
vercel env ls

# Pull environment variables locally
vercel env pull .env.local

# Remove problematic environment variable
vercel env rm <VAR_NAME> production
```

---

## Railway Troubleshooting

### Common Issues

#### SIGTERM/Port Issues
**Symptoms:**
- Application receives SIGTERM and shuts down
- "Port already in use" errors
- Health checks failing

**Quick Checks:**
```bash
# Check Railway service logs
railway logs --follow

# Verify health endpoint
curl https://<your-app>.railway.app/api/health

# Check port configuration
railway variables get PORT
```

**Remediation:**
1. Ensure application listens on `0.0.0.0:$PORT`:
   ```javascript
   const port = process.env.PORT || 3000;
   app.listen(port, '0.0.0.0', () => {
     console.log(`Server running on port ${port}`);
   });
   ```

2. Handle SIGTERM gracefully:
   ```javascript
   process.on('SIGTERM', () => {
     console.log('SIGTERM received, shutting down gracefully');
     server.close(() => {
       process.exit(0);
     });
   });
   ```

3. Set correct PORT environment variable:
   ```bash
   railway variables set PORT=3000
   ```

#### Dockerfile vs Nixpacks
**Symptoms:**
- Build fails with conflicting configurations
- Wrong runtime environment
- Missing system dependencies

**Quick Checks:**
```bash
# Check what Railway detected
railway status

# View build logs
railway logs --deployment

# Check for conflicting configs
ls Dockerfile nixpacks.toml
```

**Current Configuration:**
- **Nixpacks** is configured in `nixpacks.toml`:
  ```toml
  [variables]
  NODE_ENV = "production"

  [phases.setup]
  nixPkgs = ["nodejs_18", "npm-9_x"]

  [phases.install]
  cmd = "cd frontend && npm ci"

  [phases.build]
  cmd = "cd frontend && npm run build"

  [start]
  cmd = "cd frontend && npm start"
  ```

- **Dockerfile** exists for standalone Next.js: `frontend/Dockerfile`
  - Uses 3-stage build (deps, builder, runner)
  - Configured for `output: 'standalone'` mode in `next.config.mjs`
  - Copies standalone build artifacts: `.next/standalone`, `.next/static`
  - Runs with `node server.js` (standalone server)

**Remediation:**
1. **For Nixpacks issues**, update `nixpacks.toml`:
   ```bash
   # Edit nixpacks.toml to fix build commands
   vim nixpacks.toml
   ```

2. **To use Dockerfile with standalone Next.js**, remove `nixpacks.toml`:
   ```bash
   mv nixpacks.toml nixpacks.toml.backup
   railway up
   ```
   
   Then configure Railway to use frontend directory:
   ```bash
   # Set root directory in Railway dashboard or via CLI
   railway service set-directory <serviceName> frontend
   ```

3. **For hybrid setup** (frontend Nixpacks, backend Docker):
   - Use separate Railway services
   - Configure root directory in Railway dashboard

#### Health Check Path
**Symptoms:**
- Railway reports service as unhealthy
- Deployments marked as failed despite running
- Traffic not routing correctly

**Health Check Endpoint:** `/api/health`

**Quick Checks:**
```bash
# Test health endpoint locally
curl http://localhost:3000/api/health

# Test deployed endpoint
curl https://<your-app>.railway.app/api/health

# Check Railway health check configuration
railway service show
```

**Expected Response:**
```json
{
  "status": "ok",
  "uptime": 123.456
}
```

**Remediation:**
1. Verify health endpoint is accessible:
   ```bash
   curl -I https://<your-app>.railway.app/api/health
   ```

2. Configure Railway health check path in dashboard:
   - Go to Railway project settings
   - Set Health Check Path: `/api/health`
   - Set Health Check Timeout: `30` seconds

3. If endpoint is missing, the current implementation is in:
   `frontend/pages/api/health.js`

### Railway Commands

#### Restart Service
```bash
# Restart current service
railway service restart

# Restart specific service
railway service restart --service <service-name>

# Force restart with logs
railway service restart && railway logs --follow
```

#### Environment Setup
```bash
# Set Supabase environment variables
./scripts/set-railway-supabase-env.sh

# Manually set variables
railway variables set SUPABASE_URL=<url>
railway variables set SUPABASE_ANON_KEY=<key>

# Link project
railway link <project-id>
```

#### Deployment Management
```bash
# Deploy current branch
railway up

# Deploy with logs
railway up && railway logs --follow

# Check deployment status
railway status

# View environment variables
railway variables
```

---

## Supabase Troubleshooting

### Row Level Security (RLS) and Keys

#### RLS Configuration Issues
**Symptoms:**
- "Row Level Security policy violation" errors
- Users cannot access their own data
- Admin operations fail

**Quick Checks:**
```bash
# Test with service role key (bypasses RLS)
curl -X GET 'https://<project>.supabase.co/rest/v1/table_name' \
  -H "apikey: <service_role_key>" \
  -H "Authorization: Bearer <service_role_key>"

# Test with anon key (enforces RLS)
curl -X GET 'https://<project>.supabase.co/rest/v1/table_name' \
  -H "apikey: <anon_key>" \
  -H "Authorization: Bearer <anon_key>"
```

**Remediation:**
1. **Check RLS policies in Supabase dashboard:**
   - Go to Authentication > Policies
   - Verify policies exist for your tables
   - Test policies with different user roles

2. **Basic RLS policy examples:**
   ```sql
   -- Allow users to read their own data
   CREATE POLICY "Users can view own data" ON profiles
     FOR SELECT USING (auth.uid() = user_id);
   
   -- Allow authenticated users to insert
   CREATE POLICY "Authenticated users can insert" ON profiles
     FOR INSERT WITH CHECK (auth.uid() = user_id);
   ```

3. **Temporarily disable RLS for testing:**
   ```sql
   ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
   ```

#### API Key Issues
**Symptoms:**
- 401 Unauthorized errors
- "API key not found" errors
- Intermittent authentication failures

**Key Types and Usage:**
- **Anon Key** (`NEXT_PUBLIC_SUPABASE_ANON_KEY`): 
  - Client-side, public, enforces RLS
  - Safe to expose in frontend builds
  - Used for client-side operations
- **Service Role Key** (`SUPABASE_SERVICE_ROLE_KEY`): 
  - Server-side, private, bypasses RLS
  - Never expose in frontend/public builds
  - Used in API routes and server operations

**Where to Find Keys:**
1. **Supabase Dashboard** → Project Settings → API
2. **Project URL**: `https://your-project.supabase.co`
3. **Keys Section**: 
   - `anon` key → use as `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key → use as `SUPABASE_SERVICE_ROLE_KEY`

**Quick Checks:**
```bash
# Verify keys in Supabase dashboard
echo "Check: Project Settings > API"

# Test anon key
curl -X GET 'https://<project>.supabase.co/rest/v1/' \
  -H "apikey: <anon_key>"

# Test service role key  
curl -X GET 'https://<project>.supabase.co/rest/v1/' \
  -H "apikey: <service_role_key>"
```

**Remediation:**
1. **Regenerate keys if compromised:**
   - Go to Project Settings > API
   - Click "Reset" next to the compromised key
   - Update all applications with new key

2. **Verify key usage:**
   - Client-side: Use anon key only
   - Server-side: Use service role key
   - Never expose service role key in frontend

### Smoke Test Commands

#### cURL Tests
```bash
# Basic connectivity test
curl -X GET 'https://<project>.supabase.co/rest/v1/' \
  -H "apikey: <anon_key>"

# Test specific table read
curl -X GET 'https://<project>.supabase.co/rest/v1/profiles?select=*' \
  -H "apikey: <anon_key>" \
  -H "Authorization: Bearer <anon_key>"

# Test insert operation
curl -X POST 'https://<project>.supabase.co/rest/v1/test_table' \
  -H "apikey: <anon_key>" \
  -H "Authorization: Bearer <anon_key>" \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "created_at": "2025-01-01T00:00:00Z"}'

# Test authentication endpoint
curl -X POST 'https://<project>.supabase.co/auth/v1/signup' \
  -H "apikey: <anon_key>" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

#### Python Tests
```python
#!/usr/bin/env python3
"""
Supabase smoke test script
"""
import os
from supabase import create_client, Client

def test_supabase_connection():
    """Test basic Supabase connectivity and operations"""
    
    # Initialize client
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        return False
    
    try:
        supabase: Client = create_client(url, key)
        print("✅ Supabase client initialized")
        
        # Test basic query (replace 'profiles' with an actual table)
        response = supabase.table('profiles').select("*").limit(1).execute()
        print(f"✅ Database query successful: {len(response.data)} rows")
        
        # Test auth endpoint
        auth_response = supabase.auth.get_session()
        print("✅ Auth endpoint accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    exit(0 if success else 1)
```

#### Database Health Check
```sql
-- Check database connectivity
SELECT version();

-- Check table permissions
SELECT schemaname, tablename, hasinserts, hasselects, hasupdates, hasdeletes 
FROM pg_tables 
WHERE schemaname = 'public';

-- Check RLS status
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Check authentication users
SELECT count(*) as user_count FROM auth.users;
```

---

## Health Monitoring

### Comprehensive Health Check
Use the stack health monitoring script to check all platforms:

```bash
# Run comprehensive health check
node scripts/stack-health.js

# Quick platform status
./scripts/stack-health.js --quick

# Check specific platform
./scripts/stack-health.js --platform vercel
./scripts/stack-health.js --platform railway  
./scripts/stack-health.js --platform supabase
```

### Individual Health Endpoints

#### Railway Health Check
```bash
curl https://<your-app>.railway.app/api/health
```

#### Vercel Health Check
```bash
curl https://<your-app>.vercel.app/api/health
```

#### Custom Health Check Script
```javascript
// Basic health check for all platforms
const healthChecks = {
  railway: 'https://<app>.railway.app/api/health',
  vercel: 'https://<app>.vercel.app/api/health', 
  supabase: 'https://<project>.supabase.co/rest/v1/'
};

// Run: node -e "$(cat health-check.js)"
```

---

## Related Scripts

### Environment Setup Scripts
- **[`scripts/set-vercel-supabase-env.sh`](../../scripts/set-vercel-supabase-env.sh)** - Automated Vercel environment setup
- **[`scripts/set-railway-supabase-env.sh`](../../scripts/set-railway-supabase-env.sh)** - Automated Railway environment setup

### Deployment Scripts  
- **[`scripts/vercel-latest-url.sh`](../../scripts/vercel-latest-url.sh)** - Get latest Vercel deployment URL
- **[`scripts/railway-expose-and-url.js`](../../scripts/railway-expose-and-url.js)** - Railway deployment and URL management

### Monitoring Scripts
- **[`scripts/stack-health.js`](../../scripts/stack-health.js)** - Comprehensive platform health monitoring
- **[`frontend/pages/api/health.js`](../../frontend/pages/api/health.js)** - Application health endpoint

### Utility Scripts
- **[`scripts/post-url-comment.js`](../../scripts/post-url-comment.js)** - Automated deployment notifications

---

## Emergency Contacts & Resources

### Platform Documentation
- **Vercel**: https://vercel.com/docs
- **Railway**: https://docs.railway.app
- **Supabase**: https://supabase.com/docs

### Escalation Procedures
1. **Check platform status pages**:
   - Vercel: https://vercel-status.com
   - Railway: https://status.railway.app
   - Supabase: https://status.supabase.com

2. **Run automated diagnostics**:
   ```bash
   node scripts/stack-health.js --verbose
   ```

3. **Check recent deployments and changes**:
   ```bash
   git log --oneline -10
   vercel ls | head -5
   railway logs --tail 50
   ```

4. **Escalate to platform support** if infrastructure issue is confirmed

---

*Last updated: January 2025*