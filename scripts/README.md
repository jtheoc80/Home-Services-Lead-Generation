# Scripts Directory

This directory contains utility scripts for the Home Services Lead Generation project.

## set-vercel-supabase-env.sh

Sets up Supabase environment variables for all Vercel deployment environments (production, preview, development).

### Prerequisites

- Vercel CLI installed and authenticated
- Access to the Supabase project (anonymous key)

### Usage

```bash
./scripts/set-vercel-supabase-env.sh
```

### What it does

1. Sets `NEXT_PUBLIC_SUPABASE_URL` to `https://wsbnbncapkrdovrrghlh.supabase.co` for all environments
2. Prompts securely for `NEXT_PUBLIC_SUPABASE_ANON_KEY` (input is hidden)
3. Sets the anonymous key for all environments (production, preview, development)
4. Pulls environment variables to local `.env.local` file
5. Provides clear instructions and next steps

### Features

- **Secure input**: Anonymous key input is hidden for security
- **Error handling**: Comprehensive error checking and helpful error messages
- **Idempotent**: Can be run multiple times safely (updates existing variables)
- **Clear feedback**: Detailed progress messages and next steps

### Notes

- The script requires the Vercel CLI to be installed and authenticated
- The Supabase URL is hardcoded as per project requirements
- The script is executable and includes proper bash checks