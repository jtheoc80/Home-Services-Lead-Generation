import { createBrowserClient, createServerClient } from '@supabase/ssr'
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import type { CookieOptions } from '@supabase/ssr'

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// Browser-side client using SSR package
export function createBrowserSupabase() {
  return createBrowserClient(url, anon)
}

// Server-side client for server components using SSR package
export function createServerSupabase() {
  const cookieStore = cookies()
  
  return createServerClient(url, anon, {
    cookies: {
      get: (name: string) => cookieStore.get(name)?.value,
      set: (name: string, value: string, options: CookieOptions) => {
        try {
          cookieStore.set(name, value, options)
        } catch {
          // The `set` method was called from a Server Component.
          // This can be ignored if you have middleware refreshing
          // user sessions.
        }
      },
      remove: (name: string, options: CookieOptions) => {
        try {
          cookieStore.set(name, '', { ...options, maxAge: 0 })
        } catch {
          // The `remove` method was called from a Server Component.
          // This can be ignored if you have middleware refreshing
          // user sessions.
        }
      },
    },
  })
}

// Service role client for admin operations (use ONLY in route handlers/server tasks that must bypass RLS)
export function createServiceSupabase() {
  const service = process.env.SUPABASE_SERVICE_ROLE_KEY!
  return createClient(url, service, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  })
}