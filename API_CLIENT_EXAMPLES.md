# API Client Usage Examples

## TypeScript Frontend Client

```typescript
import { apiClient, LeadLedgerProApiClient, createApiClient } from './src/lib/api-client';

// Using the default client
async function checkHealth() {
  try {
    const health = await apiClient.health.healthCheck();
    console.log('Health status:', health);
  } catch (error) {
    console.error('Health check failed:', error);
  }
}

// Using a custom configured client
const customClient = createApiClient({
  basePath: 'https://api.leadledderpro.com',
  headers: {
    'Authorization': 'Bearer your-jwt-token'
  }
});

async function getCurrentUser() {
  try {
    const user = await customClient.auth.getCurrentUser();
    console.log('Current user:', user);
  } catch (error) {
    console.error('Failed to get user:', error);
  }
}

// Subscription management
async function cancelSubscription(userId: string, reason?: string) {
  try {
    const result = await apiClient.subscription.cancelSubscription({
      cancellationRequest: {
        user_id: userId,
        reason_category: 'user_request',
        reason_notes: reason
      }
    });
    console.log('Subscription cancelled:', result);
  } catch (error) {
    console.error('Failed to cancel subscription:', error);
  }
}
```

## Python Backend Client

```python
from backend.clients import LeadLedgerProClient

# Create a client instance
client = LeadLedgerProClient(
    base_url='http://localhost:8000',
    api_key='your-api-key'
)

# Health check
try:
    health = client.health.health_check()
    print(f"Health status: {health}")
except Exception as e:
    print(f"Health check failed: {e}")

# Get subscription status
try:
    status = client.subscription.get_subscription_status(user_id='user123')
    print(f"Subscription status: {status}")
except Exception as e:
    print(f"Failed to get subscription status: {e}")

# Export data
from backend.clients.leadledderpro_client import ExportDataRequest

try:
    export_request = ExportDataRequest(
        export_type='leads',
        format='csv',
        filters={'region': 'texas'}
    )
    result = client.export.export_data(export_data_request=export_request)
    print(f"Export result: {result}")
except Exception as e:
    print(f"Export failed: {e}")
```