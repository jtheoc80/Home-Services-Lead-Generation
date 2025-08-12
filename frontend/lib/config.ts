/**
 * Frontend configuration for Home Services Lead Generation.
 * 
 * This module centralizes all frontend configuration by using validated
 * environment variables from lib/env.ts. All configuration should be 
 * defined here rather than scattered throughout the frontend codebase.
 */

import { env, validateClientEnv } from './env';

// Validate critical client environment variables at module load
validateClientEnv();

interface AppConfig {
  // API and backend configuration
  apiBaseUrl: string;
  apiBase: string;
  supabaseUrl: string;
  supabaseAnonKey: string;
  
  // Application scope and features
  launchScope: string;
  defaultRegion: string;
  exportsEnabled: boolean;
  mlScoringEnabled: boolean;
  
  // UI configuration
  environment: string;
  debugMode: boolean;
  showAdminFeatures: boolean;
  
  // Notification configuration
  notificationsEnabled: boolean;
  realTimeUpdates: boolean;
  
  // Geographic defaults
  defaultCounties: string[];
  supportedRegions: string[];
  
  // Feature flags
  features: {
    csvExport: boolean;
    bulkActions: boolean;
    advancedFilters: boolean;
    leadScoring: boolean;
    notifications: boolean;
    analytics: boolean;
  };
}

/**
 * Get application configuration from validated environment variables
 */
export const config: AppConfig = {
  // API and backend configuration
  apiBaseUrl: '/api', // Always use relative path for API routes
  apiBase: env.NEXT_PUBLIC_API_BASE,
  supabaseUrl: env.NEXT_PUBLIC_SUPABASE_URL,
  supabaseAnonKey: env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  
  // Application scope and features  
  launchScope: env.NEXT_PUBLIC_LAUNCH_SCOPE,
  defaultRegion: env.NEXT_PUBLIC_DEFAULT_REGION,
  exportsEnabled: env.NEXT_PUBLIC_EXPORTS_ENABLED,
  mlScoringEnabled: env.NEXT_PUBLIC_ML_SCORING_ENABLED,
  
  // UI configuration
  environment: env.NEXT_PUBLIC_ENVIRONMENT,
  debugMode: env.NEXT_PUBLIC_DEBUG_MODE,
  showAdminFeatures: env.NEXT_PUBLIC_SHOW_ADMIN_FEATURES,
  
  // Notification configuration
  notificationsEnabled: env.NEXT_PUBLIC_NOTIFICATIONS_ENABLED,
  realTimeUpdates: env.NEXT_PUBLIC_REALTIME_UPDATES,
  
  // Geographic defaults
  defaultCounties: env.NEXT_PUBLIC_DEFAULT_COUNTIES,
  supportedRegions: env.NEXT_PUBLIC_SUPPORTED_REGIONS,
  
  // Feature flags
  features: {
    csvExport: env.NEXT_PUBLIC_FEATURE_CSV_EXPORT,
    bulkActions: env.NEXT_PUBLIC_FEATURE_BULK_ACTIONS,
    advancedFilters: env.NEXT_PUBLIC_FEATURE_ADVANCED_FILTERS,
    leadScoring: env.NEXT_PUBLIC_FEATURE_LEAD_SCORING,
    notifications: env.NEXT_PUBLIC_FEATURE_NOTIFICATIONS,
    analytics: env.NEXT_PUBLIC_FEATURE_ANALYTICS,
  }
};

/**
 * Check if we're running in Houston-only scope
 */
export function isHoustonScope(): boolean {
  return config.launchScope.toLowerCase() === 'houston';
}

/**
 * Check if exports are enabled for the current user/environment
 */
export function areExportsEnabled(): boolean {
  return config.exportsEnabled;
}

/**
 * Get the list of active counties based on current scope
 */
export function getActiveCounties(): string[] {
  if (isHoustonScope()) {
    return config.defaultCounties;
  }
  // Add logic for other scopes when implemented
  return [];
}

/**
 * Check if a feature is enabled
 */
export function isFeatureEnabled(feature: keyof AppConfig['features']): boolean {
  return config.features[feature];
}

/**
 * Get API endpoint URL
 */
export function getApiUrl(endpoint: string): string {
  const path = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
  return config.apiBaseUrl + path;
}

/**
 * Get external API endpoint URL
 */
export function getExternalApiUrl(endpoint: string): string {
  const path = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
  return config.apiBase + path;
}

/**
 * Get display name for a jurisdiction slug
 */
export function getJurisdictionDisplayName(slug: string): string {
  const names: Record<string, string> = {
    'tx-harris': 'Harris County',
    'tx-fort-bend': 'Fort Bend County', 
    'tx-brazoria': 'Brazoria County',
    'tx-galveston': 'Galveston County',
  };
  return names[slug] || slug;
}

/**
 * Check if we're in production environment
 */
export function isProduction(): boolean {
  return config.environment === 'production';
}

/**
 * Check if debug mode is enabled
 */
export function isDebugMode(): boolean {
  return config.debugMode && !isProduction();
}

/**
 * Get configuration for notifications
 */
export function getNotificationConfig() {
  return {
    enabled: config.notificationsEnabled,
    realTime: config.realTimeUpdates,
    channels: ['inapp', 'email'] as const,
  };
}

export default config;