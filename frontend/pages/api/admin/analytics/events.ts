import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface AnalyticsQuery {
  from?: string; // YYYY-MM-DD
  to?: string;   // YYYY-MM-DD
  event?: string;
}

interface EventCount {
  event: string;
  count: number;
  first_seen: string;
  last_seen: string;
}

interface PropertySummary {
  property: string;
  values: Array<{
    value: string;
    count: number;
  }>;
}

interface AnalyticsResponse {
  dateRange: {
    from: string;
    to: string;
  };
  totalEvents: number;
  eventCounts: EventCount[];
  topProperties: PropertySummary[];
  cancelReasons?: Array<{
    reason: string;
    count: number;
  }>;
  reactivationStats?: {
    totalReactivations: number;
    avgDaysBetweenCancelAndReactivate: number;
    topPaymentProviders: Array<{
      provider: string;
      count: number;
    }>;
  };
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Get user from auth header
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Missing or invalid authorization header' });
    }

    const token = authHeader.split(' ')[1];
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    
    if (authError || !user) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    // Check if user is admin (you'll need to implement this based on your user roles)
    // For now, we'll skip this check
    // const isAdmin = await checkAdminRole(user.id);
    // if (!isAdmin) {
    //   return res.status(403).json({ error: 'Admin access required' });
    // }

    const query: AnalyticsQuery = req.query;
    
    // Set default date range (last 30 days)
    const toDate = query.to || new Date().toISOString().split('T')[0];
    const fromDate = query.from || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    // Build the base query
    let sqlQuery = `
      SELECT event, properties, created_at
      FROM analytics_events 
      WHERE created_at >= $1 AND created_at <= $2
    `;
    const queryParams = [fromDate, toDate + ' 23:59:59'];

    // Filter by event if specified
    if (query.event) {
      sqlQuery += ' AND event = $3';
      queryParams.push(query.event);
    }

    sqlQuery += ' ORDER BY created_at DESC';

    const { data: events, error } = await supabase.rpc('execute_sql', {
      query: sqlQuery,
      params: queryParams
    });

    if (error) {
      console.error('Analytics query failed:', error);
      return res.status(500).json({ error: 'Failed to retrieve analytics data' });
    }

    // Process the results
    const eventCounts: { [key: string]: { count: number; firstSeen: string; lastSeen: string } } = {};
    const propertyValues: { [key: string]: { [value: string]: number } } = {};
    const cancelReasons: { [key: string]: number } = {};
    const reactivationData: Array<any> = [];

    events.forEach((row: any) => {
      const event = row.event;
      const properties = row.properties || {};
      const createdAt = row.created_at;

      // Count events
      if (!eventCounts[event]) {
        eventCounts[event] = { count: 0, firstSeen: createdAt, lastSeen: createdAt };
      }
      eventCounts[event].count++;
      if (createdAt < eventCounts[event].firstSeen) {
        eventCounts[event].firstSeen = createdAt;
      }
      if (createdAt > eventCounts[event].lastSeen) {
        eventCounts[event].lastSeen = createdAt;
      }

      // Collect property values
      Object.entries(properties).forEach(([key, value]) => {
        if (typeof value === 'string' || typeof value === 'number') {
          if (!propertyValues[key]) {
            propertyValues[key] = {};
          }
          const stringValue = String(value);
          propertyValues[key][stringValue] = (propertyValues[key][stringValue] || 0) + 1;
        }
      });

      // Collect cancel reasons
      if (event === 'cancel.confirmed' && properties.reason) {
        cancelReasons[properties.reason] = (cancelReasons[properties.reason] || 0) + 1;
      }

      // Collect reactivation data
      if (event === 'reactivate.confirmed') {
        reactivationData.push(properties);
      }
    });

    // Format response
    const response: AnalyticsResponse = {
      dateRange: {
        from: fromDate,
        to: toDate
      },
      totalEvents: events.length,
      eventCounts: Object.entries(eventCounts).map(([event, data]) => ({
        event,
        count: data.count,
        first_seen: data.firstSeen,
        last_seen: data.lastSeen
      })).sort((a, b) => b.count - a.count),
      topProperties: Object.entries(propertyValues).map(([property, values]) => ({
        property,
        values: Object.entries(values)
          .map(([value, count]) => ({ value, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 10) // Top 10 values per property
      })).slice(0, 20), // Top 20 properties
      cancelReasons: Object.entries(cancelReasons)
        .map(([reason, count]) => ({ reason, count }))
        .sort((a, b) => b.count - a.count),
      reactivationStats: {
        totalReactivations: reactivationData.length,
        avgDaysBetweenCancelAndReactivate: 0, // Would need to calculate this with actual data
        topPaymentProviders: Object.entries(
          reactivationData.reduce((acc, data) => {
            if (data.payment_provider) {
              acc[data.payment_provider] = (acc[data.payment_provider] || 0) + 1;
            }
            return acc;
          }, {} as { [key: string]: number })
        ).map(([provider, count]) => ({ provider, count: count as number }))
         .sort((a, b) => b.count - a.count)
      }
    };

    res.status(200).json(response);

  } catch (error) {
    console.error('Analytics API error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}