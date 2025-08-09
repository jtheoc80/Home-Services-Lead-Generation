import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

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

  try {
    // Parse query parameters
    const page = parseInt(req.query.page as string) || 1;
    const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
    const status = req.query.status as string; // 'read', 'unread', or undefined for all
    const markAsRead = req.query.mark_as_read === 'true';
    
    const offset = (page - 1) * limit;

    // Build query
    let query = supabase
      .from('notifications')
      .select(`
        id,
        lead_id,
        channel,
        status,
        title,
        message,
        metadata,
        created_at,
        sent_at,
        read_at
      `, { count: 'exact' })
      .eq('account_id', user.id)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    // Filter by status if specified
    if (status === 'read') {
      query = query.not('read_at', 'is', null);
    } else if (status === 'unread') {
      query = query.is('read_at', null);
    }

    const { data: notifications, error, count } = await query;

    if (error) {
      throw error;
    }

    // Mark notifications as read if requested
    if (markAsRead && notifications && notifications.length > 0) {
      const notificationIds = notifications
        .filter(n => !n.read_at)
        .map(n => n.id);
      
      if (notificationIds.length > 0) {
        await supabase
          .from('notifications')
          .update({ 
        const readTimestamp = new Date().toISOString();
        await supabase
          .from('notifications')
          .update({ 
            read_at: readTimestamp,
            status: 'read'
          })
          .in('id', notificationIds);
      }
    }

    // Get unread count
    const { count: unreadCount } = await supabase
      .from('notifications')
      .select('id', { count: 'exact', head: true })
      .eq('account_id', user.id)
      .is('read_at', null);

    res.status(200).json({
      notifications: notifications || [],
      pagination: {
        page,
        limit,
        total: count || 0,
        totalPages: Math.ceil((count || 0) / limit),
        hasNext: offset + limit < (count || 0),
        hasPrev: page > 1
      },
      unread_count: unreadCount || 0,
      status_filter: status || 'all'
    });

  } catch (error) {
    console.error('Error fetching notifications:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}