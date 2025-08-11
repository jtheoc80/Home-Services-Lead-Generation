# Vercel Deployment Guide

This guide provides the CLI commands to set up environment variables and deploy the Next.js application to Vercel.

## Environment Variables Setup

Use the following Vercel CLI commands to set the required environment variables:

```bash
# Set Supabase URL for all environments
vercel env add NEXT_PUBLIC_SUPABASE_URL

# Set Supabase anonymous key for all environments  
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY

# Set API base URL for all environments
vercel env add NEXT_PUBLIC_API_BASE
```

When prompted for each environment variable:
1. Enter the appropriate value when prompted
2. Select which environments to apply to (development, preview, production)

### Example Values

- **NEXT_PUBLIC_SUPABASE_URL**: Your Supabase project URL (e.g., `https://your-project.supabase.co`)
- **NEXT_PUBLIC_SUPABASE_ANON_KEY**: Your Supabase anonymous/public key
- **NEXT_PUBLIC_API_BASE**: API base URL (e.g., `https://your-api.com/api` or `/api` for relative)

## Deployment Commands

### Preview Deployment
Deploy to preview environment for testing:
```bash
vercel
```

### Production Deployment  
Deploy to production:
```bash
vercel --prod
```

## Alternative: Environment Variable Management

You can also manage environment variables through the Vercel dashboard:

1. Go to your project settings in Vercel dashboard
2. Navigate to "Environment Variables" section
3. Add the required variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` 
   - `NEXT_PUBLIC_API_BASE`

## Vercel Configuration

The `vercel.json` file is configured with:
- Framework set to Next.js
- Proper build commands for monorepo structure
- Environment variable exposure for NEXT_PUBLIC_* variables
- Output directory set to `frontend/.next`

## Troubleshooting

If deployment fails:
1. Ensure all environment variables are set correctly
2. Check that the build command works locally: `cd frontend && npm run build`
3. Verify that all required dependencies are listed in `frontend/package.json`