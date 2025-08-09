import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface NotificationPreferences {
  min_score_threshold: number;
  counties: string[];
  channels: ('inapp' | 'email' | 'sms')[];
  trade_tags?: string[];
  value_threshold?: number;
  is_enabled: boolean;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
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

  if (req.method === 'GET') {
    return handleGetPreferences(req, res, user.id);
  } else if (req.method === 'PUT') {
    return handleUpdatePreferences(req, res, user.id);
  } else {
    res.setHeader('Allow', ['GET', 'PUT']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleGetPreferences(req: NextApiRequest, res: NextApiResponse, userId: string) {
  try {
    // Get user's notification preferences
    const { data: prefs, error } = await supabase
      .from('notification_prefs')
      .select('*')
      .eq('account_id', userId)
      .single();

    if (error && error.code !== 'PGRST116') { // PGRST116 = no rows returned
      throw error;
    }

    // Return default preferences if none exist
    const defaultPrefs: NotificationPreferences = {
      min_score_threshold: 70.0,
      counties: ['tx-harris', 'tx-fort-bend', 'tx-brazoria', 'tx-galveston'],
      channels: ['inapp'],
      trade_tags: [],
      value_threshold: null,
      is_enabled: true
    };

    const preferences = prefs ? {
      min_score_threshold: prefs.min_score_threshold,
      counties: prefs.counties || [],
      channels: prefs.channels || ['inapp'],
      trade_tags: prefs.trade_tags || [],
      value_threshold: prefs.value_threshold,
      is_enabled: prefs.is_enabled
    } : defaultPrefs;

    res.status(200).json({
      preferences,
      available_counties: [
        { slug: 'tx-harris', name: 'Harris County' },
        { slug: 'tx-fort-bend', name: 'Fort Bend County' },
        { slug: 'tx-brazoria', name: 'Brazoria County' },
        { slug: 'tx-galveston', name: 'Galveston County' }
      ],
      available_channels: [
        { value: 'inapp', label: 'In-App Notifications', enabled: true },
        { value: 'email', label: 'Email Notifications', enabled: true },
        { value: 'sms', label: 'SMS Notifications', enabled: false } // Disabled for MVP
      ]
    });

  } catch (error) {
    console.error('Error fetching notification preferences:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function handleUpdatePreferences(req: NextApiRequest, res: NextApiResponse, userId: string) {
  try {
    const preferences: NotificationPreferences = req.body;
    
    // Validate preferences
    if (typeof preferences.min_score_threshold !== 'number' || 
        preferences.min_score_threshold < 0 || 
        preferences.min_score_threshold > 100) {
      return res.status(400).json({ error: 'min_score_threshold must be between 0 and 100' });
    }

    if (!Array.isArray(preferences.counties)) {
      return res.status(400).json({ error: 'counties must be an array' });
    }

    if (!Array.isArray(preferences.channels) || preferences.channels.length === 0) {
      return res.status(400).json({ error: 'At least one notification channel must be selected' });
    }

    const validChannels = ['inapp', 'email', 'sms'];
    const invalidChannels = preferences.channels.filter(ch => !validChannels.includes(ch));
    if (invalidChannels.length > 0) {
      return res.status(400).json({ error: `Invalid channels: ${invalidChannels.join(', ')}` });
    }

    // Upsert preferences
    const { data, error } = await supabase
      .from('notification_prefs')
      .upsert({
        account_id: userId,
        min_score_threshold: preferences.min_score_threshold,
        counties: preferences.counties,
        channels: preferences.channels,
        trade_tags: preferences.trade_tags || [],
        value_threshold: preferences.value_threshold || null,
        is_enabled: preferences.is_enabled,
        updated_at: new Date().toISOString()
      }, {
        onConflict: 'account_id'
      })
      .select()
      .single();

    if (error) {
      throw error;
    }

    res.status(200).json({
      message: 'Notification preferences updated successfully',
      preferences: {
        min_score_threshold: data.min_score_threshold,
        counties: data.counties,
        channels: data.channels,
        trade_tags: data.trade_tags,
        value_threshold: data.value_threshold,
        is_enabled: data.is_enabled
      }
    });

  } catch (error) {
    console.error('Error updating notification preferences:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}