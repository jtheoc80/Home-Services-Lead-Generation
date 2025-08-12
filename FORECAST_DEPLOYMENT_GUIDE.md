# Demand Surge Forecast v1 - Deployment Guide

This document provides instructions for deploying and using the demand surge forecasting system.

## Overview

The Demand Surge Forecast v1 system provides learnable, defensible demand surge predictions based on civic & market signals. It implements:

- **Surge labeling**: Top-q percentile week detection in permits + violations + bids
- **ML pipeline**: Hierarchical time series + gradient boosted trees with calibration
- **API endpoints**: `/v1/signals/demand-index` returning region scores and confidence
- **Weekly reports**: "Region X projected 40% surge risk vs 10% last year"

## Prerequisites

- Python 3.11+
- PostgreSQL database (Supabase)
- Required packages installed via `pip install -r backend/requirements.txt`
- Additional ML packages: `pip install lightgbm xgboost plotly`

## Database Setup

1. **Run the migration**:
   ```sql
   -- Execute backend/app/migrations/006_forecast_system.sql
   -- This creates all forecast tables and the gold schema
   ```

2. **Add sample regions** (if not already present):
   ```sql
   INSERT INTO regions (slug, name, level, active) VALUES 
   ('tx-harris', 'Harris County', 'county', true),
   ('tx-galveston', 'Galveston County', 'county', true),
   ('tx-fort-bend', 'Fort Bend County', 'county', true);
   ```

## Environment Configuration

Ensure these environment variables are set:

```bash
# Database connection
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

# API configuration  
PORT=8000
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Optional: Debug and metrics
DEBUG_API_KEY=your_debug_key
ENABLE_METRICS=true
```

## Running the System

### 1. Start the API Server

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000` with endpoints:
- `GET /v1/signals/demand-index` - Get all region forecasts
- `GET /v1/signals/demand-index/{region_slug}` - Get specific region forecast
- `POST /v1/signals/demand-index/refresh` - Manually refresh forecasts

### 2. Run Weekly Inference Job

```bash
cd backend/app
python weekly_inference_job.py
```

Or schedule as a cron job:
```bash
# Run every Monday at 6 AM
0 6 * * 1 cd /path/to/project/backend/app && python weekly_inference_job.py
```

### 3. Generate Reports

```bash
# Generate impact projection report
cd reports
python -c "from impact_projection import get_impact_projection_reporter; reporter = get_impact_projection_reporter(); print(reporter.generate_weekly_report())"
```

## API Usage Examples

### Get All Region Forecasts

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/v1/signals/demand-index
```

Response:
```json
{
  "regions": [
    {
      "region_slug": "tx-harris",
      "region_name": "Harris County", 
      "p_surge": 0.35,
      "confidence_score": 0.85,
      "risk_level": "medium",
      "forecast_week_start": "2024-01-15",
      "forecast_week_end": "2024-01-21",
      "p80_bounds": {"lower": 0.25, "upper": 0.45},
      "p20_bounds": {"lower": 0.30, "upper": 0.40}
    }
  ],
  "total_regions": 1,
  "forecast_date": "2024-01-14T10:00:00"
}
```

### Get Specific Region Forecast

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/v1/signals/demand-index/tx-harris
```

Response:
```json
{
  "region": "tx-harris",
  "region_name": "Harris County",
  "score": 0.35,
  "confidence": 0.85, 
  "risk_level": "medium",
  "week_start": "2024-01-15",
  "week_end": "2024-01-21",
  "bounds": {
    "p80_lower": 0.25,
    "p80_upper": 0.45,
    "p20_lower": 0.30,
    "p20_upper": 0.40
  }
}
```

### Refresh Forecasts

```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/v1/signals/demand-index/refresh
```

## Model Training

To train models for a specific region:

```python
from backend.app.demand_forecast import get_demand_surge_forecaster
from datetime import date

forecaster = get_demand_surge_forecaster()

# Train models for a region (requires historical data)
region_id = "your-region-uuid"
results = forecaster.train_models(region_id)

print(f"Model performance: {results}")
```

## Monitoring and Maintenance

### 1. Check Job Status

Query the `forecast_jobs` table to monitor job execution:

```sql
SELECT job_type, job_status, started_at, completed_at, total_runtime_seconds
FROM forecast_jobs 
ORDER BY started_at DESC 
LIMIT 10;
```

### 2. Monitor Model Performance  

Check the `model_performance` table for model metrics:

```sql
SELECT model_version, model_type, roc_auc, brier_score, f1_score
FROM model_performance 
WHERE validation_type = 'time_series_cv'
ORDER BY roc_auc DESC;
```

### 3. Review Forecast Accuracy

Compare predictions with actual surge events:

```sql
SELECT 
  region_slug,
  p_surge,
  actual_surge,
  ABS(p_surge - CASE WHEN actual_surge THEN 1.0 ELSE 0.0 END) as prediction_error
FROM forecast_predictions 
WHERE actual_surge IS NOT NULL
ORDER BY prediction_error DESC;
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed and Python path is correct
2. **Database connection**: Verify Supabase credentials and network connectivity  
3. **Model training failures**: Check for sufficient historical data (minimum 50 samples)
4. **API authentication**: Ensure JWT tokens are valid and properly formatted

### Test the System

Run the test suite to verify everything is working:

```bash
python test_forecast_system.py
```

All tests should pass with output:
```
🎉 ALL TESTS PASSED!
Demand Surge Forecast v1 system is ready for deployment.
```

### Logs and Debugging

The system uses Python logging. Increase verbosity for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs for:
- Model training progress
- Feature engineering warnings  
- Database connection issues
- API request/response details

## Performance Optimization

### Database Indexing

The migration includes optimized indexes, but for large datasets consider:

```sql
-- Additional indexes for performance
CREATE INDEX CONCURRENTLY idx_leads_issue_date_region 
ON leads(issue_date, region_id) WHERE issue_date IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_forecast_predictions_forecast_date
ON forecast_predictions(forecast_date);
```

### Model Caching

Models are stored in memory after training. For production:

1. Implement model persistence (pickle/joblib)
2. Add model versioning and rollback capability
3. Cache feature computations for repeated forecasts

### API Rate Limiting

The system includes basic rate limiting. For production:

1. Implement Redis-based rate limiting
2. Add API key management
3. Monitor usage patterns and adjust limits

## Security Considerations

1. **API Authentication**: Always use JWT tokens for API access
2. **Database Access**: Use read-only credentials for forecast generation
3. **Environment Variables**: Never commit secrets to version control
4. **Input Validation**: Validate all region slugs and date inputs
5. **Error Handling**: Don't expose internal details in error messages

## Support and Maintenance

For ongoing support:

1. Monitor forecast accuracy monthly and retrain models quarterly
2. Update external data sources (census, economic indicators) annually
3. Review and adjust surge percentile thresholds based on business needs
4. Scale infrastructure based on usage patterns and data volume

The system is designed to be self-maintaining with minimal manual intervention once properly configured.