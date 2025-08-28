# Frontend

This is the Next.js frontend application for the Home Services Lead Generation platform.

## Environment Variables

The frontend requires the following environment variables to function properly:

- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anonymous/public key

### Setting Environment Variables in Vercel

To configure these environment variables for deployment on Vercel:

1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add the following variables:
   - **Variable name:** `NEXT_PUBLIC_SUPABASE_URL`
   - **Value:** Your Supabase project URL (e.g., `https://your-project.supabase.co`)
   - **Variable name:** `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **Value:** Your Supabase anonymous key

Make sure to set these variables for the appropriate environments (Development, Preview, Production) as needed.

### Local Development

For local development, copy `.env.example` to `.env.local` and fill in your actual values:

```bash
cp .env.example .env.local
```

Then edit `.env.local` with your Supabase credentials.