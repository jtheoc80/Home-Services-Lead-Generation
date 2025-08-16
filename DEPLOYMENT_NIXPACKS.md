# Deployment Configuration

This project uses a **backend-only Nixpacks configuration** for Railway deployment.

## Architecture

- **Backend**: Deployed on Railway using Nixpacks (Python/FastAPI)
- **Frontend**: Deployed separately on Vercel (Next.js)

## Backend Deployment (Railway + Nixpacks)

The `nixpacks.toml` configuration deploys the FastAPI backend with:

### Build Process

Nixpacks will:
1. Install Python 3.11, Poetry, and PostgreSQL (only - no Node.js)
2. Set up Python symlinks for compatibility
3. Install Poetry and configure it
4. Install Python dependencies with `poetry install --without dev`
5. Skip npm/Node.js build steps (explicitly disabled)
6. Start the backend with `poetry run python backend/main.py`

### Key Configuration Features

- **Provider control**: Explicitly configures only Python provider to prevent Node.js auto-detection
- **Streamlined build**: No npm dependencies or build steps that can cause conflicts
- **Faster deployment**: Reduced package downloads and build time
- **Python-only focus**: Optimized for backend-only deployment scenario

### Environment Variables Required

Set the following environment variables in Railway:

```
SENDGRID_API_KEY=your_sendgrid_api_key_here
REDIS_URL=redis://username:password@host:port/database
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=your_actual_supabase_url
SUPABASE_SERVICE_KEY=your_actual_supabase_service_key
SUPABASE_JWT_SECRET=your_actual_jwt_secret
```

## Frontend Deployment

The frontend (Next.js) is deployed separately on Vercel and requires these environment variables:

```
NEXT_PUBLIC_SUPABASE_URL=your_actual_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_actual_supabase_anon_key
NEXT_PUBLIC_SITE_URL=https://your-domain.com
NEXT_PUBLIC_API_BASE=https://your-backend-url.com
NEXT_PUBLIC_DEFAULT_REGION=tx-houston
```