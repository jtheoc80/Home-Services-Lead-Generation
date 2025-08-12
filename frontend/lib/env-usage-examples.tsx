/**
 * Example usage of environment validation in Next.js components and API routes
 */

// Example 1: Using validated environment in a client component
import { config } from '@/lib/config';
import { env, validateClientEnv } from '@/lib/env';

export function ExampleClientComponent() {
  // Environment is validated at import time
  // If required variables are missing, the app will fail fast with clear error messages
  
  return (
    <div>
      <h1>App Configuration</h1>
      <p>Environment: {config.environment}</p>
      <p>Launch Scope: {config.launchScope}</p>
      <p>Exports Enabled: {config.exportsEnabled ? 'Yes' : 'No'}</p>
      <p>Debug Mode: {config.debugMode ? 'On' : 'Off'}</p>
      
      <h2>Feature Flags</h2>
      <ul>
        <li>CSV Export: {config.features.csvExport ? 'Enabled' : 'Disabled'}</li>
        <li>Bulk Actions: {config.features.bulkActions ? 'Enabled' : 'Disabled'}</li>
        <li>Analytics: {config.features.analytics ? 'Enabled' : 'Disabled'}</li>
      </ul>
    </div>
  );
}

// Example 2: Using environment validation in an API route
import { NextRequest, NextResponse } from 'next/server';
import { env, validateServerEnv } from '@/lib/env';

export async function GET(request: NextRequest) {
  try {
    // Validate that required server environment variables are present
    validateServerEnv(['DATABASE_URL', 'NEXTAUTH_SECRET']);
    
    // Use validated environment variables
    const dbUrl = env.DATABASE_URL;
    const authSecret = env.NEXTAUTH_SECRET;
    
    return NextResponse.json({ 
      status: 'ok',
      environment: env.NEXT_PUBLIC_ENVIRONMENT,
      hasDatabase: !!dbUrl,
      hasAuthSecret: !!authSecret 
    });
    
  } catch (error) {
    return NextResponse.json(
      { error: 'Environment validation failed', message: error.message },
      { status: 500 }
    );
  }
}

// Example 3: Early validation in app initialization
import { validateClientEnv } from '@/lib/env';

export function AppInitializer() {
  try {
    // Validate critical environment variables before app starts
    validateClientEnv();
    
    return <div>App initialized successfully</div>;
  } catch (error) {
    return (
      <div style={{ 
        backgroundColor: '#fee', 
        border: '1px solid #fcc', 
        padding: '1rem', 
        margin: '1rem' 
      }}>
        <h2>❌ Configuration Error</h2>
        <p>{error.message}</p>
        <p>Please check your environment variables and try again.</p>
      </div>
    );
  }
}