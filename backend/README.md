# Backend Lead Feedback and ML Scoring System

This backend system provides lead feedback collection, ML model training, and intelligent lead scoring for the LeadLedgerPro application.

## Features

### 1. Lead Feedback API
- **Endpoint**: `/api/feedback`
- **Methods**: POST (submit), GET (retrieve)
- Captures contractor feedback on lead quality and outcomes
- Supports rating system: no_answer, bad_contact, not_qualified, quoted, won
- Stores deal band estimates and categorized reason codes

### 2. Lead Scoring API
- **Endpoint**: `/api/score-leads`
- **Method**: POST
- Provides both ML-based and rules-based scoring
- Feature flag controlled via `ENABLE_ML_SCORING` environment variable
- Returns calibrated scores (0-100) with confidence levels

### 3. ML Training Pipeline
- **Script**: `backend/app/train_model.py`
- **Scheduler**: `backend/scripts/nightly_training.sh`
- Trains Random Forest model with probability calibration
- Uses contractor feedback to create binary success labels
- Automatically handles feature engineering and model versioning

### 4. ML Inference Engine
- **Endpoint**: `/api/ml-inference`
- **Script**: `backend/app/ml_inference.py`
- Real-time lead scoring using trained models
- Graceful fallback to rules-based scoring if ML unavailable

## Database Schema

### lead_feedback Table
```sql
CREATE TABLE lead_feedback (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL REFERENCES auth.users(id),
  lead_id BIGINT NOT NULL,
  rating lead_rating NOT NULL,
  deal_band TEXT,
  reason_codes TEXT[],
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (account_id, lead_id)
);
```

### lead_outcomes Table
```sql
CREATE TABLE lead_outcomes (
  lead_id BIGINT PRIMARY KEY,
  win_label BOOLEAN,
  win_prob NUMERIC,
  calibrated_score NUMERIC,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

## Setup Instructions

### 1. Database Migration
Run the SQL migration to create required tables:
```bash
psql $DATABASE_URL < backend/app/migrations/001_feedback_tables.sql
```

### 2. Backend Dependencies
Install Python dependencies for ML training:
```bash
cd backend
pip install -r requirements.txt
```

### 3. Frontend API Dependencies
The APIs are implemented as Next.js API routes:
```bash
cd frontend
npm install @supabase/supabase-js
```

### 4. Environment Configuration
Configure environment variables in `frontend/.env`:
```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Database for ML Training
DATABASE_URL=postgresql://user:pass@host:port/db

# Feature Flags
ENABLE_ML_SCORING=false  # Start with rules-based
ENABLE_NIGHTLY_TRAINING=false  # Enable after initial setup
```

## API Usage Examples

### Submit Feedback
```javascript
const response = await fetch('/api/feedback', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    lead_id: 12345,
    rating: 'won',
    deal_band: '$15-50k',
    reason_codes: ['good_contact', 'qualified'],
    notes: 'Excellent lead, closed within 2 weeks'
  })
});
```

### Score Leads
```javascript
const response = await fetch('/api/score-leads', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    leads: [
      {
        id: 12345,
        address: '123 Main St',
        permit_value: 25000,
        trade_tags: ['roofing', 'windows'],
        created_at: '2024-01-15T10:00:00Z'
      }
    ],
    use_ml: true  // Optional: override feature flag
  })
});
```

## ML Training Setup

### 1. Initial Training
Once you have at least 50 feedback records:
```bash
cd backend
export DATABASE_URL="your_database_url"
python3 app/train_model.py
```

### 2. Scheduled Training
Set up nightly training with cron:
```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * /path/to/backend/scripts/nightly_training.sh
```

### 3. Enable ML Scoring
After successful training, enable ML scoring:
```bash
# In frontend/.env
ENABLE_ML_SCORING=true
ENABLE_NIGHTLY_TRAINING=true
```

## Monitoring and Maintenance

### Model Performance
- Training logs: `backend/logs/training_*.log`
- Model metrics stored in `backend/models/latest_model.json`
- Monitor accuracy and AUC scores over time

### Feature Flags
- `ENABLE_ML_SCORING`: Controls ML vs rules-based scoring
- `ENABLE_NIGHTLY_TRAINING`: Controls automatic model retraining
- `ENABLE_LEAD_FEEDBACK`: Controls feedback collection API

### Scaling Considerations
- Model files are stored locally (consider cloud storage for production)
- Python inference called via subprocess (consider microservice for scale)
- Database connections use connection pooling via Supabase

## Troubleshooting

### Common Issues

1. **ML Training Fails**
   - Check DATABASE_URL connectivity
   - Ensure minimum 50 feedback records
   - Verify Python dependencies installed

2. **ML Inference Not Working**
   - Check if model files exist in `backend/models/`
   - Verify Python dependencies on frontend server
   - Enable fallback to rules-based scoring

3. **API Authentication Errors**
   - Verify Supabase service role key
   - Check JWT token format in Authorization header
   - Ensure user exists in auth.users table

### Log Files
- Training logs: `backend/logs/training_*.log`
- API errors: Check Next.js console output
- Database errors: Monitor Supabase dashboard

## Security Notes

- Service role key has elevated privileges - keep secure
- Input validation on all API endpoints
- Rate limiting recommended for production
- User isolation via account_id in feedback table