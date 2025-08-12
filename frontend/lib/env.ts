import { z } from 'zod';

/**
 * Environment variables validation schema using Zod
 * 
 * This module validates all required environment variables at build/runtime
 * and provides typed access to configuration values.
 */

// Boolean environment variable parser
const booleanString = z
  .string()
  .optional()
  .transform((val) => val === 'true')
  .pipe(z.boolean());

// String array environment variable parser (comma-separated)
const stringArray = z
  .string()
  .optional()
  .transform((val) => val ? val.split(',').map(item => item.trim()).filter(Boolean) : [])
  .pipe(z.array(z.string()));

// Required string with helpful error message
const requiredString = (name: string) => z
  .string()
  .min(1, `${name} is required and cannot be empty`);

// Optional string with default
const optionalString = (defaultValue: string = '') => z
  .string()
  .optional()
  .default(defaultValue);

/**
 * Environment variables schema
 */
const envSchema = z.object({
  // ===== REQUIRED SUPABASE CONFIGURATION =====
  NEXT_PUBLIC_SUPABASE_URL: requiredString('NEXT_PUBLIC_SUPABASE_URL'),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: requiredString('NEXT_PUBLIC_SUPABASE_ANON_KEY'),
  
  // ===== API CONFIGURATION =====
  NEXT_PUBLIC_API_BASE: optionalString('http://localhost:8000'),
  
  // ===== APPLICATION SCOPE =====
  NEXT_PUBLIC_LAUNCH_SCOPE: optionalString('houston'),
  NEXT_PUBLIC_DEFAULT_REGION: optionalString('tx-houston'),
  
  // ===== FEATURE FLAGS =====
  NEXT_PUBLIC_EXPORTS_ENABLED: booleanString.default(false),
  NEXT_PUBLIC_ML_SCORING_ENABLED: booleanString.default(false),
  NEXT_PUBLIC_SHOW_ADMIN_FEATURES: booleanString.default(false),
  NEXT_PUBLIC_NOTIFICATIONS_ENABLED: booleanString.default(true),
  NEXT_PUBLIC_REALTIME_UPDATES: booleanString.default(true),
  
  // ===== FEATURE TOGGLES =====
  NEXT_PUBLIC_FEATURE_CSV_EXPORT: booleanString.default(false),
  NEXT_PUBLIC_FEATURE_BULK_ACTIONS: booleanString.default(true),
  NEXT_PUBLIC_FEATURE_ADVANCED_FILTERS: booleanString.default(true),
  NEXT_PUBLIC_FEATURE_LEAD_SCORING: booleanString.default(true),
  NEXT_PUBLIC_FEATURE_NOTIFICATIONS: booleanString.default(true),
  NEXT_PUBLIC_FEATURE_ANALYTICS: booleanString.default(true),
  
  // ===== GEOGRAPHIC CONFIGURATION =====
  NEXT_PUBLIC_DEFAULT_COUNTIES: stringArray.default(['tx-harris', 'tx-fort-bend', 'tx-brazoria', 'tx-galveston']),
  NEXT_PUBLIC_SUPPORTED_REGIONS: stringArray.default(['tx-houston']),
  
  // ===== APPLICATION ENVIRONMENT =====
  NEXT_PUBLIC_ENVIRONMENT: optionalString('development'),
  NEXT_PUBLIC_DEBUG_MODE: booleanString.default(false),
  
  // ===== STRIPE CONFIGURATION =====
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: optionalString(''),
  
  // ===== OPTIONAL ANALYTICS =====
  NEXT_PUBLIC_GA_MEASUREMENT_ID: optionalString(''),
  NEXT_PUBLIC_SENTRY_DSN: optionalString(''),
  
  // ===== SERVER-SIDE ENVIRONMENT VARIABLES =====
  // These are only available in API routes and server components
  DATABASE_URL: z.string().optional(),
  NEXTAUTH_URL: optionalString('http://localhost:3000'),
  NEXTAUTH_SECRET: z.string().optional(),
  ALLOW_EXPORTS: booleanString.default(false),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),
  INTERNAL_BACKEND_WEBHOOK_URL: z.string().optional(),
  INTERNAL_WEBHOOK_TOKEN: z.string().optional(),
  SUPABASE_URL: z.string().optional(),
  SUPABASE_SERVICE_ROLE_KEY: z.string().optional(),
});

/**
 * Parse and validate environment variables
 */
function parseEnv() {
  try {
    return envSchema.parse(process.env);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.issues.map((err) => {
        const path = err.path.join('.');
        return `❌ ${path}: ${err.message}`;
      });
      
      console.error('🚨 Environment variable validation failed:');
      console.error(errorMessages.join('\n'));
      console.error('\n📋 Please check your .env.local file and ensure all required variables are set.');
      console.error('💡 See .env.example for reference values.');
      
      // In development, we can be more lenient, but still show warnings
      if (process.env.NODE_ENV === 'development') {
        console.warn('\n⚠️  Running in development mode with missing environment variables.');
        console.warn('Some features may not work correctly.');
      } else {
        // In production, fail fast
        process.exit(1);
      }
    }
    throw error;
  }
}

/**
 * Validated environment variables
 * This will fail at import time if validation fails
 */
export const env = parseEnv();

/**
 * Type-safe environment configuration
 */
export type Environment = z.infer<typeof envSchema>;

/**
 * Check if we're running in production
 */
export function isProduction(): boolean {
  return env.NEXT_PUBLIC_ENVIRONMENT === 'production';
}

/**
 * Check if we're running in development
 */
export function isDevelopment(): boolean {
  return env.NEXT_PUBLIC_ENVIRONMENT === 'development';
}

/**
 * Check if debug mode is enabled
 */
export function isDebugMode(): boolean {
  return env.NEXT_PUBLIC_DEBUG_MODE && !isProduction();
}

/**
 * Validate critical environment variables for client-side use
 * This should be called before initializing client-side services
 */
export function validateClientEnv(): void {
  const criticalVars = [
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  ];
  
  const missing = criticalVars.filter(varName => !env[varName as keyof Environment]);
  
  if (missing.length > 0) {
    throw new Error(
      `Missing critical environment variables: ${missing.join(', ')}\n` +
      'These variables are required for the application to function properly.'
    );
  }
}

/**
 * Validate server-side environment variables
 * This should be called in API routes that require server-side config
 */
export function validateServerEnv(requiredVars: (keyof Environment)[]): void {
  const missing = requiredVars.filter(varName => !env[varName]);
  
  if (missing.length > 0) {
    throw new Error(
      `Missing required server environment variables: ${missing.join(', ')}`
    );
  }
}

export default env;