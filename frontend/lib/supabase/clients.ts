// frontend/lib/supabase/clients.ts
import { createBrowserClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { createServerClient as createSSRClient } from '@supabase/ssr'
import type { CookieOptions } from '@supabase/ssr'
import { createClient as createAdminClient } from '@supabase/supabase-js'

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export function createBrowserSupabase() {
  return createBrowserClient(url, anon)
}

export function createServerSupabase() {
  return createSSRClient(url, anon, {
    cookies: {
      get: (name: string) => cookies().get(name)?.value,
      set: (name: string, value: string, options: CookieOptions) => {
        try {
          cookies().set(name, value, options)
        } catch (error) {
          // The `set` method was called from a Server Component.
          // This can be ignored if you have middleware refreshing
          // user sessions.
        }
      },
      remove: (name: string, options: CookieOptions) => {
        try {
          cookies().set(name, '', { ...options, maxAge: 0 })
        } catch (error) {
          // The `remove` method was called from a Server Component.
          // This can be ignored if you have middleware refreshing
          // user sessions.
        }
      },
    },
  })
}

// use ONLY in route handlers/server tasks that must bypass RLS
export function createServiceSupabase() {
  const service = process.env.SUPABASE_SERVICE_ROLE_KEY!
  return createAdminClient(url, service)
}