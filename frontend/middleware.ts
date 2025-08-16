import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Protected routes that require authentication
const protectedRoutes = ['/dashboard', '/leads']

// Routes that are allowed in test mode without authentication
const testModeAllowedRoutes = ['/leads/new', '/leads-test']

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check if we're in test mode
  const isTestMode = process.env.LEADS_TEST_MODE === 'true'
  
  // If in test mode, allow certain routes without authentication
  if (isTestMode && testModeAllowedRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next()
  }

  // Check if the current path is a protected route
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route))
  
  if (!isProtectedRoute) {
    return NextResponse.next()
  }

  // Get the session token from cookies
  // Look for common Supabase auth cookie patterns
  const accessToken = request.cookies.get('sb-access-token')?.value ||
                     request.cookies.get('supabase-auth-token')?.value ||
                     request.cookies.get('sb-1234567890abcdef-auth-token')?.value

  // Check for session in various cookie formats that Supabase might use
  let hasValidSession = false
  
  // Get all cookies and check for Supabase auth patterns
  const cookies = request.cookies
  const cookieNames = ['sb-access-token', 'supabase-auth-token']
  
  // Add dynamic cookie names that might contain project-specific tokens
  for (let i = 0; i < 10; i++) {
    cookieNames.push(`sb-${i}-auth-token`)
  }
  
  for (const cookieName of cookieNames) {
    const cookie = cookies.get(cookieName)
    if (cookie?.value) {
      try {
        // Try to parse as JSON (Supabase stores session data as JSON)
        const sessionData = JSON.parse(cookie.value)
        if (sessionData.access_token || sessionData.session?.access_token) {
          hasValidSession = true
          break
        }
      } catch {
        // If not JSON, treat the cookie value itself as a token
        if (cookie.value.length > 20) { // Basic check for token-like string
          hasValidSession = true
          break
        }
      }
    }
  }

  // If no valid session found, redirect to login
  if (!accessToken && !hasValidSession) {
    const redirectUrl = new URL('/login', request.url)
    redirectUrl.searchParams.set('redirectedFrom', pathname)
    return NextResponse.redirect(redirectUrl)
  }

  // If we have a token, assume it's valid for now
  // The client-side will handle more thorough validation
  return NextResponse.next()
}

// Configure which paths the middleware should run on
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|login).*)']
}