import { NextApiRequest, NextApiResponse } from 'next';

interface AnalyticsEventData {
  event_name: string;
  event_type: 'user_intent' | 'system_driven';
  user_id?: string;
  account_id?: string;
  properties?: Record<string, any>;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  return handleTrackEvent(req, res);
}

async function handleTrackEvent(req: NextApiRequest, res: NextApiResponse) {
  try {
    const eventData: AnalyticsEventData = req.body;

    // Validate required fields
    if (!eventData.event_name || !eventData.event_type) {
      return res.status(400).json({
        error: 'Missing required fields: event_name and event_type are required'
      });
    }

    if (!['user_intent', 'system_driven'].includes(eventData.event_type)) {
      return res.status(400).json({
        error: 'Invalid event_type. Must be "user_intent" or "system_driven"'
      });
    }

    // In a real implementation, this would:
    // 1. Import the backend analytics service
    // 2. Call the backend analytics service to track the event
    // 3. Store the event in the database
    
    // For now, we'll just log the event
    console.log('Analytics event received:', {
      ...eventData,
      timestamp: new Date().toISOString(),
      source: 'frontend'
    });

    // TODO: Integrate with backend analytics service
    // This would typically involve:
    // - Calling a backend API endpoint
    // - Or directly using the backend analytics module (if available)
    // - Storing the event in the analytics_events table

    return res.status(200).json({
      success: true,
      message: 'Event tracked successfully'
    });

  } catch (error) {
    console.error('Error tracking analytics event:', error);
    return res.status(500).json({
      error: 'Internal server error while tracking event'
    });
  }
}