'use client';

import { useEffect, useState } from 'react';

interface HealthStatus {
  frontend: string;
  backend: string;
  supabase: string;
}

export default function HealthBanner() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [envIssues, setEnvIssues] = useState<string[]>([]);

  useEffect(() => {
    // Only show in development
    if (process.env.NODE_ENV !== 'development') return;

    // Check for missing environment variables
    const issues: string[] = [];
    if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
      issues.push('NEXT_PUBLIC_SUPABASE_URL');
    }
    if (!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
      issues.push('NEXT_PUBLIC_SUPABASE_ANON_KEY');
    }
    if (!process.env.NEXT_PUBLIC_API_BASE) {
      issues.push('NEXT_PUBLIC_API_BASE');
    }
    setEnvIssues(issues);

    // Check health endpoint
    fetch('/api/health')
      .then(response => response.json())
      .then(data => setHealthStatus(data))
      .catch(() => setHealthStatus({ frontend: 'down', backend: 'down', supabase: 'down' }));
  }, []);

  // Don't render in production
  if (process.env.NODE_ENV !== 'development') return null;

  // Don't render if everything is OK and no env issues
  const hasIssues = envIssues.length > 0 || 
    (healthStatus && (healthStatus.frontend !== 'ok' || healthStatus.backend !== 'ok' || healthStatus.supabase !== 'ok'));

  if (!hasIssues) return null;

  return (
    <div className="bg-yellow-100 border-l-4 border-yellow-500 p-2 text-sm">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <span className="text-yellow-600">⚠️</span>
        </div>
        <div className="ml-2">
          <span className="text-yellow-800 font-medium">Development Health Issues:</span>
          {envIssues.length > 0 && (
            <span className="text-yellow-700 ml-2">
              Missing env vars: {envIssues.join(', ')}
            </span>
          )}
          {healthStatus && (
            <span className="text-yellow-700 ml-2">
              Health: Frontend={healthStatus.frontend}, Backend={healthStatus.backend}, Supabase={healthStatus.supabase}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}