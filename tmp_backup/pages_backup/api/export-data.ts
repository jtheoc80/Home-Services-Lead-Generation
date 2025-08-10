import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface ExportRequest {
  export_type: 'leads' | 'permits' | 'scored_leads' | 'analytics' | 'feedback';
  format?: 'csv' | 'json' | 'xlsx';
  filters?: {
    date_range?: {
      start: string;
      end: string;
    };
    score_threshold?: number;
    trade_tags?: string[];
  };
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    return handleExportRequest(req, res);
  } else if (req.method === 'GET') {
    return handleGetExportStatus(req, res);
  } else {
    res.setHeader('Allow', ['POST', 'GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleExportRequest(req: NextApiRequest, res: NextApiResponse) {
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

    const exportRequest: ExportRequest = req.body;
    
    // Validate export type
    const validTypes = ['leads', 'permits', 'scored_leads', 'analytics', 'feedback'];
    if (!exportRequest.export_type || !validTypes.includes(exportRequest.export_type)) {
      return res.status(400).json({ error: 'Invalid export_type' });
    }

    // Check export permissions
    const exportsAllowed = process.env.ALLOW_EXPORTS?.toLowerCase() === 'true';
    
    if (!exportsAllowed) {
      // Log the blocked export attempt
      console.warn(`Export blocked for user ${user.email}: ALLOW_EXPORTS=false`);
      
      // Send notification about blocked export if configured
      await notifyExportBlocked(user.email || 'unknown', exportRequest.export_type);
      
      return res.status(403).json({ 
        error: 'Data exports are currently disabled',
        reason: 'Export functionality is disabled by system configuration'
      });
    }

    // Generate export ID for tracking
    const exportId = generateExportId();
    
    // Log export request
    console.info(`Export requested by ${user.email}: ${exportRequest.export_type} (ID: ${exportId})`);

    // Process the export based on type
    let exportResult;
    
    switch (exportRequest.export_type) {
      case 'leads':
        exportResult = await exportLeads(exportRequest, user.id);
        break;
      case 'scored_leads':
        exportResult = await exportScoredLeads(exportRequest, user.id);
        break;
      case 'feedback':
        exportResult = await exportFeedback(exportRequest, user.id);
        break;
      default:
        return res.status(400).json({ error: 'Export type not implemented yet' });
    }

    // Send success notification
    await notifyExportSuccess(user.email || 'unknown', exportRequest.export_type, exportResult.recordCount);

    res.status(200).json({
      message: 'Export completed successfully',
      export_id: exportId,
      export_type: exportRequest.export_type,
      record_count: exportResult.recordCount,
      download_url: exportResult.downloadUrl,
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours
    });

  } catch (error) {
    console.error('Export request error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function handleGetExportStatus(req: NextApiRequest, res: NextApiResponse) {
  try {
    const exportsAllowed = process.env.ALLOW_EXPORTS?.toLowerCase() === 'true';
    
    res.status(200).json({
      exports_enabled: exportsAllowed,
      supported_types: ['leads', 'permits', 'scored_leads', 'analytics', 'feedback'],
      supported_formats: ['csv', 'json'],
      configuration_source: 'ALLOW_EXPORTS environment variable'
    });
  } catch (error) {
    console.error('Export status error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function exportLeads(request: ExportRequest, userId: string) {
  // This would implement actual lead export logic
  // For now, return a placeholder result
  
  console.log(`Exporting leads for user ${userId}`);
  
  // Simulated export logic
  const recordCount = 150; // Would be actual count from database
  const downloadUrl = `/api/downloads/leads_${Date.now()}.csv`;
  
  return {
    recordCount,
    downloadUrl
  };
}

async function exportScoredLeads(request: ExportRequest, userId: string) {
  // Get user's lead outcomes with scores
  const { data: outcomes, error } = await supabase
    .from('lead_outcomes')
    .select('*')
    .order('updated_at', { ascending: false })
    .limit(1000);

  if (error) {
    throw new Error(`Failed to fetch scored leads: ${error.message}`);
  }

  console.log(`Exporting ${outcomes?.length || 0} scored leads for user ${userId}`);
  
  // Simulated export file generation
  const recordCount = outcomes?.length || 0;
  const downloadUrl = `/api/downloads/scored_leads_${Date.now()}.csv`;
  
  return {
    recordCount,
    downloadUrl
  };
}

async function exportFeedback(request: ExportRequest, userId: string) {
  // Get user's feedback data
  const { data: feedback, error } = await supabase
    .from('lead_feedback')
    .select('*')
    .eq('account_id', userId)
    .order('created_at', { ascending: false });

  if (error) {
    throw new Error(`Failed to fetch feedback data: ${error.message}`);
  }

  console.log(`Exporting ${feedback?.length || 0} feedback records for user ${userId}`);
  
  const recordCount = feedback?.length || 0;
  const downloadUrl = `/api/downloads/feedback_${Date.now()}.csv`;
  
  return {
    recordCount,
    downloadUrl
  };
}

function generateExportId(): string {
  return `export_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

async function notifyExportBlocked(userEmail: string, exportType: string) {
  // Check if notification environment variables are configured
  const sendgridKey = process.env.SENDGRID_API_KEY;
  const adminEmails = process.env.ADMIN_NOTIFICATION_EMAILS?.split(',').map(e => e.trim()) || [];
  
  if (!sendgridKey || adminEmails.length === 0) {
    console.log('Export notification not sent: missing configuration');
    return;
  }

  // Log the notification (actual email sending would require backend integration)
  console.warn(`BLOCKED EXPORT: User ${userEmail} attempted to export ${exportType}`);
  
  // In a full implementation, this would call the backend notification service
  // For now, just log the attempted notification
  console.info(`Would notify admins: ${adminEmails.join(', ')}`);
}

async function notifyExportSuccess(userEmail: string, exportType: string, recordCount: number) {
  // Log successful export
  console.info(`EXPORT SUCCESS: User ${userEmail} exported ${recordCount} ${exportType} records`);
  
  // In a full implementation, this might send a notification email with download link
}