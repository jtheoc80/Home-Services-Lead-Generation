const required = ['NEXT_PUBLIC_SUPABASE_URL','NEXT_PUBLIC_SUPABASE_ANON_KEY'];
const missing = required.filter(k => !process.env[k]);
if (missing.length) {
  console.error('Missing envs (set these in Vercel Project Settings → Environment Variables):', missing.join(', '));
  process.exit(1);
}
console.log('✅ Required environment variables are present');