# Deployment Configuration

This project is configured to deploy the Next.js frontend as the primary application.

## Environment Variables Required

Set the following environment variables in your deployment platform:

```
NEXT_PUBLIC_SUPABASE_URL=your_actual_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_actual_supabase_anon_key
NEXT_PUBLIC_SITE_URL=https://your-domain.com
NEXT_PUBLIC_API_BASE=https://your-backend-url.com
NEXT_PUBLIC_DEFAULT_REGION=tx-houston
```

## Build Process

Nixpacks will:
1. Install Node.js 18 and npm
2. Navigate to the `frontend` directory
3. Run `npm ci` to install dependencies
4. Run `npm run build` to build the Next.js application
5. Start the application with `npm start`

## Backend

The backend (FastAPI) should be deployed separately. See `backend/` directory for deployment instructions.