import type { AppProps } from 'next/app'
import '@/styles/globals.css'
import analytics from '../lib/analytics'
import { useEffect } from 'react'

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    // Initialize analytics on app startup
    analytics.initialize().catch(error => {
      console.warn('Analytics initialization failed:', error);
    });
  }, []);

  return <Component {...pageProps} />
}