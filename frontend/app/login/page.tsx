
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