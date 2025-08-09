/**
 * Configuration management for LeadLedgerPro frontend.
 * Handles environment-specific settings and feature flags.
 */

export interface AppConfig {
  environment: 'production' | 'staging' | 'development';
  apiBaseUrl: string;
  isStaging: boolean;
  isProduction: boolean;
  isDevelopment: boolean;
  features: {
    showStagingBanner: boolean;
    enableDebugTools: boolean;
    enableAnalytics: boolean;
  };
  api: {
    timeout: number;
    retryAttempts: number;
  };
  ui: {
    stagingBannerText: string;
    stagingBannerColor: string;
  };
}

/**
 * Get configuration based on environment variables.
 */
function createConfig(): AppConfig {
  // Determine environment
  const env = (process.env.NEXT_PUBLIC_ENV || 'development').toLowerCase() as AppConfig['environment'];
  
  // API base URL configuration
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE || 
    (env === 'development' ? 'http://localhost:8000' : 
     env === 'staging' ? 'https://staging-api.leadledderpro.com' :
     'https://api.leadledderpro.com');

  // Environment checks
  const isStaging = env === 'staging';
  const isProduction = env === 'production';
  const isDevelopment = env === 'development';

  return {
    environment: env,
    apiBaseUrl,
    isStaging,
    isProduction,
    isDevelopment,
    features: {
      showStagingBanner: isStaging,
      enableDebugTools: isDevelopment || isStaging,
      enableAnalytics: isProduction,
    },
    api: {
      timeout: isDevelopment ? 10000 : 5000, // 10s for dev, 5s for prod/staging
      retryAttempts: isDevelopment ? 1 : 3,
    },
    ui: {
      stagingBannerText: 'STAGING ENVIRONMENT - Test Data Only',
      stagingBannerColor: '#f59e0b', // Amber color
    },
  };
}

// Export singleton config instance
export const config: AppConfig = createConfig();

/**
 * Utility function to log configuration info.
 * Useful for debugging environment setup.
 */
export function logConfigInfo(): void {
  if (typeof window !== 'undefined' && config.features.enableDebugTools) {
    console.group('🔧 LeadLedgerPro Configuration');
    console.log('Environment:', config.environment);
    console.log('API Base URL:', config.apiBaseUrl);
    console.log('Features:', config.features);
    console.groupEnd();
  }
}

/**
 * Check if we're running in a browser environment.
 */
export function isBrowser(): boolean {
  return typeof window !== 'undefined';
}

/**
 * Get API endpoint URL with proper base URL.
 */
export function getApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${config.apiBaseUrl}/${cleanEndpoint}`;
}

/**
 * Default fetch options with configuration.
 */
export function getDefaultFetchOptions(): RequestInit {
  return {
    headers: {
      'Content-Type': 'application/json',
      'X-Environment': config.environment,
    },
    // Add timeout handling in a real implementation
  };
}

/**
 * Environment-specific console logging.
 */
export const logger = {
  debug: (...args: any[]) => {
    if (config.features.enableDebugTools) {
      console.log('[DEBUG]', ...args);
    }
  },
  info: (...args: any[]) => {
    console.info('[INFO]', ...args);
  },
  warn: (...args: any[]) => {
    console.warn('[WARN]', ...args);
  },
  error: (...args: any[]) => {
    console.error('[ERROR]', ...args);
  },
};

// Log configuration on load in development/staging
if (isBrowser() && config.features.enableDebugTools) {
  logConfigInfo();
}