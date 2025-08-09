import { NextApiRequest, NextApiResponse } from 'next';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';

const execAsync = promisify(exec);

interface MLInferenceRequest {
  leads: Array<{
    id: number;
    features: {
      rating_numeric?: number;
      estimated_deal_value?: number;
      feedback_age_days?: number;
      has_contact_issues?: boolean;
      has_qualification_issues?: boolean;
      is_weekend_feedback?: boolean;
      feedback_hour?: number;
    };
  }>;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    return handleMLInference(req, res);
  } else {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleMLInference(req: NextApiRequest, res: NextApiResponse) {
  try {
    // Check if ML is enabled
    if (process.env.ENABLE_ML_SCORING !== 'true') {
      return res.status(400).json({ error: 'ML scoring is disabled' });
    }

    const request: MLInferenceRequest = req.body;
    
    if (!request.leads || request.leads.length === 0) {
      return res.status(400).json({ error: 'No leads provided for inference' });
    }

    // Check if model exists
    const modelDir = path.join(process.cwd(), '..', 'backend', 'models');
    const latestModelPath = path.join(modelDir, 'latest_model.json');
    
    try {
      await fs.access(latestModelPath);
    } catch {
      return res.status(503).json({ 
        error: 'ML model not available. Please train a model first.' 
      });
    }

    // Prepare inference data
    const inferenceData = {
      leads: request.leads.map(lead => ({
        id: lead.id,
        features: {
          rating_numeric: lead.features.rating_numeric || 0,
          estimated_deal_value: lead.features.estimated_deal_value || 0,
          feedback_age_days: lead.features.feedback_age_days || 0,
          has_contact_issues: lead.features.has_contact_issues || false,
          has_qualification_issues: lead.features.has_qualification_issues || false,
          is_weekend_feedback: lead.features.is_weekend_feedback || false,
          feedback_hour: lead.features.feedback_hour || 12
        }
      }))
    };

    // Run Python inference script
    const scriptPath = path.join(process.cwd(), '..', 'backend', 'app', 'ml_inference.py');
    const inputJson = JSON.stringify(inferenceData);
    
    try {
      const { stdout, stderr } = await execAsync(
        `echo '${inputJson}' | python3 "${scriptPath}"`,
        { 
          cwd: path.join(process.cwd(), '..', 'backend'),
          timeout: 30000 // 30 second timeout
        }
      );

      if (stderr) {
        console.error('ML inference stderr:', stderr);
      }

      const results = JSON.parse(stdout);
      
      res.status(200).json({
        message: 'ML inference completed',
        data: results
      });
    } catch (error) {
      console.error('ML inference execution error:', error);
      return res.status(500).json({ 
        error: 'ML inference failed',
        details: error instanceof Error ? error.message : 'Unknown error'
      });
    }

  } catch (error) {
    console.error('ML inference API error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}