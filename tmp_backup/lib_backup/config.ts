/**
 * Frontend configuration for Home Services Lead Generation.
 * 
 * This module centralizes all frontend configuration by reading NEXT_PUBLIC_* 
 * environment variables. All configuration should be defined here rather than
 * scattered throughout the frontend codebase.
 */

interface AppConfig {
  // API and backend configuration
  apiBaseUrl: string;
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
 * Parse boolean environment variable with default fallback
 */
function parseBooleanEnv(value: string | undefined, defaultValue: boolean = false): boolean {
  if (!value) return defaultValue;
  return value.toLowerCase() === 'true';
}

/**
 * Parse array environment variable (comma-separated)
 */
function parseArrayEnv(value: string | undefined, defaultValue: string[] = []): string[] {
  if (!value) return defaultValue;
  return value.split(',').map(item => item.trim()).filter(Boolean);
}

/**
 * Get application configuration from environment variables
 */
export const config: AppConfig = {
  // API and backend configuration
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
  
  // Application scope and features  
  launchScope: process.env.NEXT_PUBLIC_LAUNCH_SCOPE || 'houston',
  defaultRegion: process.env.NEXT_PUBLIC_DEFAULT_REGION || 'tx-houston',
  exportsEnabled: parseBooleanEnv(process.env.NEXT_PUBLIC_EXPORTS_ENABLED),
  mlScoringEnabled: parseBooleanEnv(process.env.NEXT_PUBLIC_ML_SCORING_ENABLED),
  
  // UI configuration
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT || 'development',
  debugMode: parseBooleanEnv(process.env.NEXT_PUBLIC_DEBUG_MODE),
  showAdminFeatures: parseBooleanEnv(process.env.NEXT_PUBLIC_SHOW_ADMIN_FEATURES),
  
  // Notification configuration
  notificationsEnabled: parseBooleanEnv(process.env.NEXT_PUBLIC_NOTIFICATIONS_ENABLED, true),
  realTimeUpdates: parseBooleanEnv(process.env.NEXT_PUBLIC_REALTIME_UPDATES, true),
  
  // Geographic defaults
  defaultCounties: parseArrayEnv(process.env.NEXT_PUBLIC_DEFAULT_COUNTIES, [
    'tx-harris', 'tx-fort-bend', 'tx-brazoria', 'tx-galveston'
  ]),
  supportedRegions: parseArrayEnv(process.env.NEXT_PUBLIC_SUPPORTED_REGIONS, [
    'tx-houston'
  ]),
  
  // Feature flags
  features: {
    csvExport: parseBooleanEnv(process.env.NEXT_PUBLIC_FEATURE_CSV_EXPORT),
    bulkActions: parseBooleanEnv(process.env.NEXT_PUBLIC_FEATURE_BULK_ACTIONS, true),
    advancedFilters: parseBooleanEnv(process.env.NEXT_PUBLIC_FEATURE_ADVANCED_FILTERS, true),
    leadScoring: parseBooleanEnv(process.env.NEXT_PUBLIC_FEATURE_LEAD_SCORING, true),
    notifications: parseBooleanEnv(process.env.NEXT_PUBLIC_FEATURE_NOTIFICATIONS, true),
    analytics: parseBooleanEnv(process.env.NEXT_PUBLIC_FEATURE_ANALYTICS, true),
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