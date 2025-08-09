/**
 * Analytics utilities for tracking cancellation and reactivation events.
 * 
 * This module provides utility functions for sending analytics events to various
 * providers (PostHog, Segment, Mixpanel, GA4) from the frontend.
 */

export interface AnalyticsConfig {
  provider: 'none' | 'posthog' | 'segment' | 'mixpanel' | 'ga4';
  apiKey?: string;
}

export interface EventProperties {
  [key: string]: any;
}

export interface TrackEventParams {
  eventName: string;
  eventType: 'user_intent' | 'system_driven';
  userId?: string;
  properties?: EventProperties;
}

class AnalyticsService {
  private config: AnalyticsConfig;
  private providerClient: any = null;
  private initialized = false;

  constructor(config?: AnalyticsConfig) {
    this.config = config || this.getConfigFromEnv();
    
    if (this.isEnabled()) {
      this.initializeProvider();
    }
  }

  private getConfigFromEnv(): AnalyticsConfig {
    return {
      provider: (process.env.NEXT_PUBLIC_ANALYTICS_PROVIDER as any) || 'none',
      apiKey: process.env.NEXT_PUBLIC_ANALYTICS_API_KEY,
    };
  }

  private isEnabled(): boolean {
    return this.config.provider !== 'none' && !!this.config.apiKey;
  }

  private async initializeProvider(): Promise<void> {
    if (this.initialized || typeof window === 'undefined') {
      return;
    }

    try {
      switch (this.config.provider) {
        case 'posthog':
          await this.initializePostHog();
          break;
        case 'segment':
          await this.initializeSegment();
          break;
        case 'mixpanel':
          await this.initializeMixpanel();
          break;
        case 'ga4':
          await this.initializeGA4();
          break;
        default:
          console.warn(`Unknown analytics provider: ${this.config.provider}`);
      }
      this.initialized = true;
    } catch (error) {
      console.error(`Failed to initialize ${this.config.provider} analytics:`, error);
    }
  }

  private async initializePostHog(): Promise<void> {
    try {
      const posthog = await this.dynamicImport('posthog-js');
      if (!posthog) {
        console.warn('PostHog library not available. Install with: npm install posthog-js');
        return;
      }
      posthog.init(this.config.apiKey!, {
        api_host: 'https://app.posthog.com',
      });
      this.providerClient = posthog;
      console.log('PostHog analytics initialized');
    } catch (error) {
      console.error('Failed to initialize PostHog analytics:', error);
    }
  }

  private async initializeSegment(): Promise<void> {
    try {
      // Segment Analytics.js 2.0
      if (!window.analytics) {
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.async = true;
        script.src = `https://cdn.segment.com/analytics.js/v1/${this.config.apiKey}/analytics.min.js`;
        document.head.appendChild(script);
        
        // Wait for Segment to load
        await new Promise((resolve) => {
          script.onload = resolve;
        });
      }
      
      this.providerClient = window.analytics;
      console.log('Segment analytics initialized');
    } catch (error) {
      console.error('Failed to initialize Segment analytics:', error);
    }
  }

  private async initializeMixpanel(): Promise<void> {
    try {
      const mixpanel = await this.dynamicImport('mixpanel-browser');
      if (!mixpanel) {
        console.warn('Mixpanel library not available. Install with: npm install mixpanel-browser');
        return;
      }
      mixpanel.init(this.config.apiKey!);
      this.providerClient = mixpanel;
      console.log('Mixpanel analytics initialized');
    } catch (error) {
      console.error('Failed to initialize Mixpanel analytics:', error);
    }
  }

  private async dynamicImport(moduleName: string): Promise<any> {
    try {
      // Use Function constructor to avoid static analysis
      const importFunc = new Function('moduleName', 'return import(moduleName)');
      const module = await importFunc(moduleName);
      return module.default || module;
    } catch (error) {
      console.warn(`Module ${moduleName} not available:`, error);
      return null;
    }
  }

  private async initializeGA4(): Promise<void> {
    try {
      // Google Analytics 4 via gtag
      const script1 = document.createElement('script');
      script1.async = true;
      script1.src = `https://www.googletagmanager.com/gtag/js?id=${this.config.apiKey}`;
      document.head.appendChild(script1);

      const script2 = document.createElement('script');
      script2.innerHTML = `
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', '${this.config.apiKey}');
      `;
      document.head.appendChild(script2);

      // Wait for gtag to be available
      await new Promise((resolve) => {
        script1.onload = resolve;
      });

      this.providerClient = window.gtag;
      console.log('GA4 analytics initialized');
    } catch (error) {
      console.error('Failed to initialize GA4 analytics:', error);
    }
  }

  async trackEvent({
    eventName,
    eventType,
    userId,
    properties = {},
  }: TrackEventParams): Promise<boolean> {
    if (!this.isEnabled()) {
      console.debug(`Analytics disabled, skipping event: ${eventName}`);
      return true;
    }

    // Ensure provider is initialized
    await this.initializeProvider();

    const enhancedProperties = {
      ...properties,
      event_type: eventType,
      timestamp: new Date().toISOString(),
    };

    try {
      // Track with provider
      const success = await this.trackWithProvider(eventName, userId, enhancedProperties);
      
      // Also send to backend for server-side logging
      await this.logToBackend(eventName, eventType, userId, enhancedProperties);
      
      return success;
    } catch (error) {
      console.error(`Failed to track event '${eventName}':`, error);
      return false;
    }
  }

  private async trackWithProvider(
    eventName: string,
    userId?: string,
    properties: EventProperties = {}
  ): Promise<boolean> {
    if (!this.providerClient) {
      return true; // Consider successful if no provider
    }

    try {
      switch (this.config.provider) {
        case 'posthog':
          if (userId) {
            this.providerClient.identify(userId);
          }
          this.providerClient.capture(eventName, properties);
          break;

        case 'segment':
          if (userId) {
            this.providerClient.identify(userId);
          }
          this.providerClient.track(eventName, properties);
          break;

        case 'mixpanel':
          if (userId) {
            this.providerClient.identify(userId);
          }
          this.providerClient.track(eventName, properties);
          break;

        case 'ga4':
          this.providerClient('event', eventName, properties);
          break;

        default:
          console.warn(`Tracking not implemented for provider: ${this.config.provider}`);
      }

      console.log(`Tracked event '${eventName}' with ${this.config.provider}`);
      return true;
    } catch (error) {
      console.error(`Failed to track event with ${this.config.provider}:`, error);
      return false;
    }
  }

  private async logToBackend(
    eventName: string,
    eventType: string,
    userId?: string,
    properties: EventProperties = {}
  ): Promise<void> {
    try {
      // Send event to backend API for server-side logging
      const response = await fetch('/api/analytics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_name: eventName,
          event_type: eventType,
          user_id: userId,
          properties,
        }),
      });

      if (!response.ok) {
        console.warn('Failed to log event to backend:', response.statusText);
      }
    } catch (error) {
      console.warn('Failed to send event to backend:', error);
    }
  }
}

// Global analytics service instance
let analyticsService: AnalyticsService | null = null;

export function getAnalyticsService(): AnalyticsService {
  if (!analyticsService) {
    analyticsService = new AnalyticsService();
  }
  return analyticsService;
}

export interface CancellationEventParams {
  userId?: string;
  cancellationReason?: string;
  subscriptionType?: string;
  eventType?: 'user_intent' | 'system_driven';
}

export async function trackCancellationEvent({
  userId,
  cancellationReason,
  subscriptionType,
  eventType = 'user_intent',
}: CancellationEventParams = {}): Promise<boolean> {
  const properties: EventProperties = {};
  
  if (cancellationReason) {
    properties.cancellation_reason = cancellationReason;
  }
  if (subscriptionType) {
    properties.subscription_type = subscriptionType;
  }

  return getAnalyticsService().trackEvent({
    eventName: 'subscription_cancelled',
    eventType,
    userId,
    properties,
  });
}

export interface ReactivationEventParams {
  userId?: string;
  reactivationSource?: string;
  subscriptionType?: string;
  eventType?: 'user_intent' | 'system_driven';
}

export async function trackReactivationEvent({
  userId,
  reactivationSource,
  subscriptionType,
  eventType = 'user_intent',
}: ReactivationEventParams = {}): Promise<boolean> {
  const properties: EventProperties = {};
  
  if (reactivationSource) {
    properties.reactivation_source = reactivationSource;
  }
  if (subscriptionType) {
    properties.subscription_type = subscriptionType;
  }

  return getAnalyticsService().trackEvent({
    eventName: 'subscription_reactivated',
    eventType,
    userId,
    properties,
  });
}

// Type declarations for global objects
declare global {
  interface Window {
    analytics?: any;
    gtag?: (...args: any[]) => void;
    dataLayer?: any[];
  }
}