// Auto-generated API client for LeadLedgerPro
// Generated from OpenAPI specification

import { Configuration, ConfigurationParameters } from './runtime';
import { 
  AdminApi,
  AuthApi,
  ExportApi,
  HealthApi,
  MonitoringApi,
  RootApi,
  SubscriptionApi
} from './apis';

export * from './apis';
export * from './models';
export { Configuration, ConfigurationParameters } from './runtime';

/**
 * API client collection with all available services
 */
export class LeadLedgerProApiClient {
  private configuration: Configuration;
  
  public readonly admin: AdminApi;
  public readonly auth: AuthApi;
  public readonly export: ExportApi;
  public readonly health: HealthApi;
  public readonly monitoring: MonitoringApi;
  public readonly root: RootApi;
  public readonly subscription: SubscriptionApi;

  constructor(config?: ConfigurationParameters) {
    this.configuration = new Configuration(config);
    
    this.admin = new AdminApi(this.configuration);
    this.auth = new AuthApi(this.configuration);
    this.export = new ExportApi(this.configuration);
    this.health = new HealthApi(this.configuration);
    this.monitoring = new MonitoringApi(this.configuration);
    this.root = new RootApi(this.configuration);
    this.subscription = new SubscriptionApi(this.configuration);
  }
}

/**
 * Create a configured API client instance
 */
export function createApiClient(config?: ConfigurationParameters): LeadLedgerProApiClient {
  return new LeadLedgerProApiClient(config);
}

/**
 * Default API client instance
 */
export const apiClient = createApiClient({
  basePath: typeof window !== 'undefined' 
    ? (process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000')
    : (process.env.API_BASE || 'http://localhost:8000')
});

export default apiClient;