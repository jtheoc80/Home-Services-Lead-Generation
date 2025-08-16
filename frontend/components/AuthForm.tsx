'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { getSupabaseClient, isSupabaseConfigured } from '@/lib/supabase-browser';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { Mail, Lock, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react';

interface AuthFormProps {
  onSuccess?: () => void;
  redirectTo?: string;
}

export default function AuthForm({ onSuccess, redirectTo = '/dashboard' }: AuthFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'magic' | 'password'>('magic');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);
  const searchParams = useSearchParams();
  const redirectedFrom = searchParams?.get('redirectedFrom');

  // Determine final redirect destination
  const finalRedirectTo = redirectedFrom || redirectTo;

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setMessage({ type: 'error', text: 'Please enter your email address' });
      return;
    }

    if (!isSupabaseConfigured()) {
      setMessage({ 
        type: 'error', 
        text: 'Demo mode: Supabase authentication is not configured. This would normally send a magic link.' 
      });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      const supabase = getSupabaseClient();
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}${finalRedirectTo}`,
        },
      });

      if (error) {
        setMessage({ type: 'error', text: error.message });
      } else {
        const destinationMessage = redirectedFrom 
          ? `Check your email for the magic link to log in! You'll be redirected to ${redirectedFrom}.`
          : 'Check your email for the magic link to log in!';
        setMessage({
          type: 'success',
          text: destinationMessage,
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'An unexpected error occurred. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setMessage({ type: 'error', text: 'Please enter both email and password' });
      return;
    }

    if (!isSupabaseConfigured()) {
      setMessage({ 
        type: 'error', 
        text: 'Demo mode: Supabase authentication is not configured. This would normally sign you in.' 
      });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      const supabase = getSupabaseClient();
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setMessage({ type: 'error', text: error.message });
      } else {
        setMessage({ type: 'success', text: 'Successfully logged in!' });
        onSuccess?.();
        if (typeof window !== 'undefined') {
          window.location.href = finalRedirectTo;
        }
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'An unexpected error occurred. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md p-8" variant="glass">
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
          <p className="text-gray-600">Sign in to your LeadLedger Pro account</p>
        </div>

        {/* Mode Toggle */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            type="button"
            onClick={() => setMode('magic')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all ${
              mode === 'magic'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Mail className="w-4 h-4 inline-block mr-2" />
            Magic Link
          </button>
          <button
            type="button"
            onClick={() => setMode('password')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all ${
              mode === 'password'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Lock className="w-4 h-4 inline-block mr-2" />
            Password
          </button>
        </div>

        {/* Form */}
        <form onSubmit={mode === 'magic' ? handleMagicLink : handleEmailPassword} className="space-y-4">
          {/* Email Field */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                required
              />
            </div>
          </div>

          {/* Password Field (only in password mode) */}
          {mode === 'password' && (
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
          )}

          {/* Error/Success Message */}
          {message && (
            <div
              className={`p-4 rounded-lg flex items-center space-x-2 ${
                message.type === 'error'
                  ? 'bg-red-50 text-red-700 border border-red-200'
                  : 'bg-green-50 text-green-700 border border-green-200'
              }`}
            >
              {message.type === 'error' ? (
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
              ) : (
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
              )}
              <span className="text-sm">{message.text}</span>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading}
            className={`w-full py-3 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isLoading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>{mode === 'magic' ? 'Sending magic link...' : 'Signing in...'}</span>
              </div>
            ) : (
              <>
                {mode === 'magic' ? 'Send magic link' : 'Sign in'}
              </>
            )}
          </Button>
        </form>

        {/* Additional Info */}
        {mode === 'magic' && (
          <div className="text-center text-sm text-gray-600">
            <p>
              We'll send you a secure link to sign in instantly.
              <br />
              No password required!
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}