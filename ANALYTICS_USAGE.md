# Analytics Tracking Usage Examples

This document demonstrates how to use the analytics tracking functionality for cancellation and reactivation flows.

## Backend Usage

### Basic Configuration

Set environment variables in your `.env` file:

```bash
ANALYTICS_PROVIDER=posthog  # 'none'|'posthog'|'segment'|'mixpanel'|'ga4'
ANALYTICS_API_KEY=your_analytics_api_key_here
```

### Tracking Cancellation Events

```python
from app.utils.analytics import track_cancellation_event

# Track user-initiated cancellation
track_cancellation_event(
    account_id='user_123',
    user_id='user_123',
    cancellation_reason='too_expensive',
    subscription_type='premium',
    event_type='user_intent'
)

# Track system-driven cancellation (e.g., payment failure)
track_cancellation_event(
    account_id='user_456',
    user_id='user_456',
    cancellation_reason='payment_failed',
    subscription_type='basic',
    event_type='system_driven'
)
```

### Tracking Reactivation Events

```python
from app.utils.analytics import track_reactivation_event

# Track user reactivation from email campaign
track_reactivation_event(
    account_id='user_123',
    user_id='user_123',
    reactivation_source='email_campaign',
    subscription_type='premium',
    event_type='user_intent'
)

# Track automatic reactivation after payment update
track_reactivation_event(
    account_id='user_456',
    user_id='user_456',
    reactivation_source='payment_updated',
    subscription_type='basic',
    event_type='system_driven'
)
```

### Custom Event Tracking

```python
from app.utils.analytics import get_analytics_service

analytics = get_analytics_service()

analytics.track_event(
    event_name='custom_event',
    event_type='user_intent',
    account_id='user_123',
    user_id='user_123',
    properties={
        'custom_property': 'value',
        'numeric_value': 42
    }
)
```

## Frontend Usage

### Basic Configuration

Set environment variables in your `.env.local` file:

```bash
NEXT_PUBLIC_ANALYTICS_PROVIDER=posthog  # 'none'|'posthog'|'segment'|'mixpanel'|'ga4'
NEXT_PUBLIC_ANALYTICS_API_KEY=your_analytics_api_key_here
```

### Tracking Cancellation Events

```typescript
import { trackCancellationEvent } from '../lib/analytics';

// Track cancellation from UI
const handleCancellation = async () => {
  await trackCancellationEvent({
    userId: 'user_123',
    cancellationReason: 'too_expensive',
    subscriptionType: 'premium',
    eventType: 'user_intent'
  });
  
  // Proceed with cancellation logic
};
```

### Tracking Reactivation Events

```typescript
import { trackReactivationEvent } from '../lib/analytics';

// Track reactivation from UI
const handleReactivation = async () => {
  await trackReactivationEvent({
    userId: 'user_123',
    reactivationSource: 'pricing_page',
    subscriptionType: 'premium',
    eventType: 'user_intent'
  });
  
  // Proceed with reactivation logic
};
```

### Custom Event Tracking

```typescript
import { getAnalyticsService } from '../lib/analytics';

const analytics = getAnalyticsService();

await analytics.trackEvent({
  eventName: 'custom_frontend_event',
  eventType: 'user_intent',
  userId: 'user_123',
  properties: {
    page: 'pricing',
    source: 'button_click'
  }
});
```

## React Component Examples

### Cancellation Button Component

```tsx
import React from 'react';
import { trackCancellationEvent } from '../lib/analytics';

interface CancelSubscriptionButtonProps {
  userId: string;
  subscriptionType: string;
  onCancel: () => void;
}

const CancelSubscriptionButton: React.FC<CancelSubscriptionButtonProps> = ({
  userId,
  subscriptionType,
  onCancel
}) => {
  const handleCancel = async () => {
    // Track the cancellation intent
    await trackCancellationEvent({
      userId,
      cancellationReason: 'user_initiated',
      subscriptionType,
      eventType: 'user_intent'
    });
    
    // Call the actual cancellation logic
    onCancel();
  };

  return (
    <button 
      onClick={handleCancel}
      className="bg-red-500 text-white px-4 py-2 rounded"
    >
      Cancel Subscription
    </button>
  );
};
```

### Reactivation Component

```tsx
import React from 'react';
import { trackReactivationEvent } from '../lib/analytics';

interface ReactivationOfferProps {
  userId: string;
  subscriptionType: string;
  onReactivate: () => void;
}

const ReactivationOffer: React.FC<ReactivationOfferProps> = ({
  userId,
  subscriptionType,
  onReactivate
}) => {
  const handleReactivate = async () => {
    // Track the reactivation intent
    await trackReactivationEvent({
      userId,
      reactivationSource: 'offer_banner',
      subscriptionType,
      eventType: 'user_intent'
    });
    
    // Call the actual reactivation logic
    onReactivate();
  };

  return (
    <div className="bg-blue-100 p-4 rounded">
      <h3>Welcome Back!</h3>
      <p>Reactivate your {subscriptionType} subscription with a special offer.</p>
      <button 
        onClick={handleReactivate}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Reactivate Now
      </button>
    </div>
  );
};
```

## Provider-Specific Setup

### PostHog Setup

Backend:
```bash
pip install posthog
```

Frontend:
```bash
npm install posthog-js
```

### Segment Setup

Backend:
```bash
pip install analytics-python
```

Frontend (automatically loads via CDN)

### Mixpanel Setup

Backend:
```bash
pip install mixpanel
```

Frontend:
```bash
npm install mixpanel-browser
```

### Google Analytics 4 Setup

Backend:
```bash
pip install google-analytics-data
```

Frontend (automatically loads via gtag script)

## Database Schema

The analytics events are stored in the `analytics_events` table:

```sql
CREATE TABLE IF NOT EXISTS analytics_events (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID,
  user_id TEXT,
  event_name TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('user_intent', 'system_driven')),
  properties JSONB,
  provider TEXT,
  provider_event_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

## Testing

Run the analytics tests:

```bash
cd backend
python -m pytest tests/test_analytics.py -v
```

All 17 tests should pass, covering:
- Configuration validation
- Event tracking functionality
- Provider integration
- Helper functions
- Error handling