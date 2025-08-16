
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Card from "@/components/ui/Card";
import { Building, ArrowRight, LogIn } from "lucide-react";

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogin = () => {
    setIsLoading(true);
    // For now, just redirect to dashboard
    // In a real implementation, this would handle Supabase authentication
    setTimeout(() => {
      router.push("/dashboard");
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 to-texas-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <Card className="p-8 space-y-6">
          {/* Logo/Header */}
          <div className="text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-brand-600 to-texas-600 rounded-2xl flex items-center justify-center">
              <Building className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Welcome Back</h1>
              <p className="text-gray-600">Sign in to access your lead dashboard</p>
            </div>
          </div>

          {/* Login Form */}
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors"
                placeholder="contractor@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors"
                placeholder="••••••••"
              />
            </div>

            <button
              onClick={handleLogin}
              disabled={isLoading}
              className={`w-full inline-flex items-center justify-center px-6 py-3 bg-brand-600 text-white font-medium rounded-xl hover:bg-brand-700 transition-colors space-x-2 ${
                isLoading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <LogIn className="w-4 h-4" />
              <span>{isLoading ? 'Signing in...' : 'Sign In'}</span>
              {!isLoading && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>

          {/* Footer */}
          <div className="text-center space-y-2">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <button className="text-brand-600 hover:text-brand-700 font-medium">
                Contact Sales
              </button>
            </p>
            <p className="text-xs text-gray-500">
              This is a demo login page. In production, this would integrate with Supabase authentication.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );


'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { supabase } from '@/lib/supabase-browser'
import { Mail, AlertCircle, CheckCircle } from 'lucide-react'

function LoginForm() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirectedFrom = searchParams.get('redirectedFrom')

  useEffect(() => {
    // Check if user is already logged in
    const checkUser = async () => {
      if (supabase) {
        const { data: { session } } = await supabase.auth.getSession()
        if (session) {
          // User is already logged in, redirect to intended page or dashboard
          const redirectTo = redirectedFrom || '/dashboard'
          router.push(redirectTo)
        }
      }
    }
    
    checkUser()

    // Listen for auth state changes
    if (supabase) {
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange(async (event, session) => {
        if (event === 'SIGNED_IN' && session) {
          // User signed in successfully, redirect to intended page
          const redirectTo = redirectedFrom || '/dashboard'
          router.push(redirectTo)
        }
      })

      return () => subscription.unsubscribe()
    }
  }, [router, redirectedFrom])

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!supabase) {
      setError('Authentication service is not available. Please check your configuration.')
      return
    }

    setLoading(true)
    setError('')
    setMessage('')

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/login${redirectedFrom ? `?redirectedFrom=${encodeURIComponent(redirectedFrom)}` : ''}`,
        },
      })

      if (error) {
        setError(error.message)
      } else {
        setMessage('Check your email for the login link!')
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="bg-blue-600 text-white p-3 rounded-full">
            <Mail className="h-8 w-8" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to LeadLedgerPro
        </h2>
        {redirectedFrom && (
          <p className="mt-2 text-center text-sm text-gray-600">
            Please sign in to access{' '}
            <span className="font-medium text-blue-600">{redirectedFrom}</span>
          </p>
        )}
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSignIn}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Enter your email"
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md">
                <AlertCircle className="h-5 w-5" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            {message && (
              <div className="flex items-center space-x-2 text-green-600 bg-green-50 p-3 rounded-md">
                <CheckCircle className="h-5 w-5" />
                <span className="text-sm">{message}</span>
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending...' : 'Send Magic Link'}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="text-center text-sm text-gray-600">
              We&apos;ll send you a secure link to sign in without a password.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="flex justify-center">
            <div className="bg-blue-600 text-white p-3 rounded-full">
              <Mail className="h-8 w-8" />
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Loading...
          </h2>
        </div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  )

'use client';

import { useEffect, useState } from 'react';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabase-browser';
import AuthForm from '@/components/AuthForm';

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Check if Supabase is configured
    if (!isSupabaseConfigured()) {
      setIsLoading(false);
      return;
    }

    // Check if user is already authenticated
    const checkAuth = async () => {
      try {
        const supabase = getSupabaseClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          window.location.href = '/dashboard';
        } else {
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Auth check error:', error);
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[600px] flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 -mx-6 -my-6">
      <div className="w-full max-w-md p-4">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">LL</span>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">LeadLedger Pro</h1>
          <p className="text-gray-600">Texas Home Services Lead Generation</p>
        </div>

        {isSupabaseConfigured() ? (
          <AuthForm />
        ) : (
          <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto">
                <span className="text-yellow-600 text-2xl">⚠️</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-900">Demo Mode</h2>
              <p className="text-gray-600">
                Supabase authentication is not configured. This is a demo of the authentication UI.
              </p>
              <div className="bg-gray-50 p-4 rounded-lg text-left">
                <p className="text-sm text-gray-700 mb-2">To enable authentication:</p>
                <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                  <li>Set up a Supabase project</li>
                  <li>Configure NEXT_PUBLIC_SUPABASE_URL</li>
                  <li>Configure NEXT_PUBLIC_SUPABASE_ANON_KEY</li>
                  <li>Enable email authentication in Supabase</li>
                </ol>
              </div>
            </div>
          </div>
        )}

        <div className="text-center mt-6">
          <p className="text-sm text-gray-600">
            New to LeadLedger Pro?{' '}
            <button
              onClick={() => window.location.href = '/'}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Learn more
            </button>
          </p>
        </div>
      </div>
    </div>
  );


}