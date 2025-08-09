/**
 * Universal Analytics Wrapper
 * 
 * Supports PostHog, Segment, Mixpanel, GA4 via environment configuration.
 * Provides a unified interface for tracking events across different providers.
 */

interface AnalyticsEvent {
  event: string;
  properties?: Record<string, any>;
}

type AnalyticsProvider = 'posthog' | 'segment' | 'mixpanel' | 'ga4' | 'none';

interface AnalyticsConfig {
  provider: AnalyticsProvider;
  apiKey?: string;
  measurementId?: string; // For GA4
}

class Analytics {
  private config: AnalyticsConfig;
  private initialized = false;

  constructor() {
    this.config = this.getConfigFromEnv();
  }

  private getConfigFromEnv(): AnalyticsConfig {
    const provider = (process.env.NEXT_PUBLIC_ANALYTICS_PROVIDER || 'none') as AnalyticsProvider;
    
    return {
      provider,
      apiKey: process.env.NEXT_PUBLIC_ANALYTICS_API_KEY,
      measurementId: process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID,
    };
  }

  async initialize(): Promise<void> {
    if (this.initialized || this.config.provider === 'none') {
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
      }
      this.initialized = true;
    } catch (error) {
      console.warn('Analytics initialization failed:', error);
    }
  }

  private async initializePostHog(): Promise<void> {
    if (!this.config.apiKey) return;
    
    try {
      // Use completely dynamic import to avoid build-time resolution
      const posthogModule = await eval(`import('posthog-js')`);
      const posthog = posthogModule.default;
      posthog.init(this.config.apiKey, {
        api_host: 'https://app.posthog.com',
        loaded: (posthog: any) => {
          if (process.env.NODE_ENV === 'development') {
            posthog.debug();
          }
        }
      });
    } catch (error) {
      console.warn('PostHog library not available:', error);
    }
  }

  private async initializeSegment(): Promise<void> {
    if (!this.config.apiKey) return;

    // Load Segment Analytics.js
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.async = true;
    script.src = 'https://cdn.segment.com/analytics.js/v1/' + this.config.apiKey + '/analytics.min.js';
    document.head.appendChild(script);

    // Initialize analytics object
    (window as any).analytics = (window as any).analytics || [];
    const analytics = (window as any).analytics;

    if (analytics.initialize) return;

    analytics.invoked = true;
    analytics.methods = [
      'trackSubmit', 'trackClick', 'trackLink', 'trackForm', 'pageview', 'identify',
      'reset', 'group', 'track', 'ready', 'alias', 'debug', 'page', 'once', 'off', 'on'
    ];

    analytics.factory = function(t: string) {
      return function() {
        const e = Array.prototype.slice.call(arguments);
        e.unshift(t);
        analytics.push(e);
        return analytics;
      };
    };

    for (let t = 0; t < analytics.methods.length; t++) {
      const e = analytics.methods[t];
      analytics[e] = analytics.factory(e);
    }

    analytics.load = function(t: string, e?: any) {
      const n = document.createElement('script');
      n.type = 'text/javascript';
      n.async = !0;
      n.src = 'https://cdn.segment.com/analytics.js/v1/' + t + '/analytics.min.js';
      const a = document.getElementsByTagName('script')[0];
      a.parentNode?.insertBefore(n, a);
      analytics._loadOptions = e;
    };

    analytics.load(this.config.apiKey);
  }

  private async initializeMixpanel(): Promise<void> {
    if (!this.config.apiKey) return;

    try {
      // Use completely dynamic import to avoid build-time resolution
      const mixpanelModule = await eval(`import('mixpanel-browser')`);
      const mixpanel = mixpanelModule.default;
      mixpanel.init(this.config.apiKey, {
        debug: process.env.NODE_ENV === 'development',
        track_pageview: true,
        persistence: 'localStorage'
      });
    } catch (error) {
      console.warn('Mixpanel library not available:', error);
    }
  }

  private async initializeGA4(): Promise<void> {
    if (!this.config.measurementId) return;

    // Load gtag
    const script1 = document.createElement('script');
    script1.async = true;
    script1.src = `https://www.googletagmanager.com/gtag/js?id=${this.config.measurementId}`;
    document.head.appendChild(script1);

    // Initialize gtag
    (window as any).dataLayer = (window as any).dataLayer || [];
    function gtag(...args: any[]) {
      (window as any).dataLayer.push(args);
    }
    (window as any).gtag = gtag;

    gtag('js', new Date());
    gtag('config', this.config.measurementId);
  }

  /**
   * Track an analytics event
   * @param event - Event name
   * @param properties - Optional event properties
   */
  track(event: string, properties?: Record<string, any>): void {
    // Skip if analytics is disabled
    if (this.config.provider === 'none') {
      return;
    }

    // Skip if not initialized
    if (!this.initialized) {
      console.warn('Analytics not initialized. Call analytics.initialize() first.');
      return;
    }

    try {
      switch (this.config.provider) {
        case 'posthog':
          this.trackPostHog(event, properties);
          break;
        case 'segment':
          this.trackSegment(event, properties);
          break;
        case 'mixpanel':
          this.trackMixpanel(event, properties);
          break;
        case 'ga4':
          this.trackGA4(event, properties);
          break;
      }
    } catch (error) {
      console.warn('Analytics tracking failed:', error);
    }
  }

  private trackPostHog(event: string, properties?: Record<string, any>): void {
    if (typeof window !== 'undefined' && (window as any).posthog) {
      (window as any).posthog.capture(event, properties);
    }
  }

  private trackSegment(event: string, properties?: Record<string, any>): void {
    if (typeof window !== 'undefined' && (window as any).analytics) {
      (window as any).analytics.track(event, properties);
    }
  }

  private trackMixpanel(event: string, properties?: Record<string, any>): void {
    if (typeof window !== 'undefined' && (window as any).mixpanel) {
      (window as any).mixpanel.track(event, properties);
    }
  }

  private trackGA4(event: string, properties?: Record<string, any>): void {
    if (typeof window !== 'undefined' && (window as any).gtag) {
      // Convert properties to GA4 format
      const eventParameters = properties || {};
      (window as any).gtag('event', event, eventParameters);
    }
  }

  /**
   * Identify a user (where supported)
   * @param userId - User identifier
   * @param traits - User traits/properties
   */
  identify(userId: string, traits?: Record<string, any>): void {
    if (this.config.provider === 'none' || !this.initialized) {
      return;
    }

    try {
      switch (this.config.provider) {
        case 'posthog':
          if (typeof window !== 'undefined' && (window as any).posthog) {
            (window as any).posthog.identify(userId, traits);
          }
          break;
        case 'segment':
          if (typeof window !== 'undefined' && (window as any).analytics) {
            (window as any).analytics.identify(userId, traits);
          }
          break;
        case 'mixpanel':
          if (typeof window !== 'undefined' && (window as any).mixpanel) {
            (window as any).mixpanel.identify(userId);
            if (traits) {
              (window as any).mixpanel.people.set(traits);
            }
          }
          break;
        case 'ga4':
          if (typeof window !== 'undefined' && (window as any).gtag) {
            (window as any).gtag('config', this.config.measurementId, {
              user_id: userId,
              custom_map: traits
            });
          }
          break;
      }
    } catch (error) {
      console.warn('Analytics identify failed:', error);
    }
  }

  /**
   * Reset user identification (useful for logout)
   */
  reset(): void {
    if (this.config.provider === 'none' || !this.initialized) {
      return;
    }

    try {
      switch (this.config.provider) {
        case 'posthog':
          if (typeof window !== 'undefined' && (window as any).posthog) {
            (window as any).posthog.reset();
          }
          break;
        case 'segment':
          if (typeof window !== 'undefined' && (window as any).analytics) {
            (window as any).analytics.reset();
          }
          break;
        case 'mixpanel':
          if (typeof window !== 'undefined' && (window as any).mixpanel) {
            (window as any).mixpanel.reset();
          }
          break;
      }
    } catch (error) {
      console.warn('Analytics reset failed:', error);
    }
  }
}

// Create and export singleton instance
const analytics = new Analytics();

export default analytics;
export type { AnalyticsProvider, AnalyticsConfig };