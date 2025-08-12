-- Demand Surge Forecast v1 Database Schema
-- Migration 006: Forecast system tables for learnable, defensible demand surge predictions

-- Surge Labels: Define "surge" as top-q percentile week in (permits + violations + bids) per region
CREATE TABLE IF NOT EXISTS surge_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id UUID REFERENCES regions(id),
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    permit_count INTEGER DEFAULT 0,
    violation_count INTEGER DEFAULT 0,
    bid_count INTEGER DEFAULT 0,
    total_activity INTEGER GENERATED ALWAYS AS (permit_count + violation_count + bid_count) STORED,
    percentile_rank NUMERIC, -- 0-100 percentile rank for this week
    is_surge BOOLEAN DEFAULT FALSE, -- top-q percentile flag
    surge_threshold_percentile NUMERIC DEFAULT 90, -- configurable threshold
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(region_id, week_start)
);

-- Forecast Features: Lagged trends, seasonality, contractor metrics, etc.
CREATE TABLE IF NOT EXISTS forecast_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id UUID REFERENCES regions(id),
    feature_date DATE NOT NULL,
    
    -- Lagged trends and seasonality
    permits_lag_1w INTEGER DEFAULT 0,
    permits_lag_2w INTEGER DEFAULT 0,
    permits_lag_4w INTEGER DEFAULT 0,
    permits_ma_4w NUMERIC DEFAULT 0, -- 4-week moving average
    permits_ma_12w NUMERIC DEFAULT 0, -- 12-week moving average
    permits_trend_4w NUMERIC DEFAULT 0, -- 4-week trend
    permits_seasonal_index NUMERIC DEFAULT 1, -- seasonal adjustment factor
    
    -- Contractor graph metrics
    active_contractors INTEGER DEFAULT 0,
    new_contractor_entries INTEGER DEFAULT 0,
    contractor_exits INTEGER DEFAULT 0,
    contractor_network_density NUMERIC DEFAULT 0,
    avg_contractor_capacity NUMERIC DEFAULT 0,
    
    -- Inspection and processing metrics
    inspection_backlog_days NUMERIC DEFAULT 0,
    avg_award_to_permit_lag_days NUMERIC DEFAULT 0,
    permit_approval_rate NUMERIC DEFAULT 0,
    
    -- Census and business density
    population_density NUMERIC DEFAULT 0,
    business_density NUMERIC DEFAULT 0,
    housing_unit_density NUMERIC DEFAULT 0,
    median_income NUMERIC DEFAULT 0,
    construction_employment_rate NUMERIC DEFAULT 0,
    
    -- External factors
    economic_indicator NUMERIC DEFAULT 0,
    weather_index NUMERIC DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(region_id, feature_date)
);

-- Model Predictions: Store forecast results with confidence intervals
CREATE TABLE IF NOT EXISTS forecast_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id UUID REFERENCES regions(id),
    forecast_date DATE NOT NULL, -- date the forecast was made
    target_week_start DATE NOT NULL, -- week being predicted
    target_week_end DATE NOT NULL,
    
    -- Model outputs
    p_surge NUMERIC NOT NULL, -- probability of surge (0-1)
    p80_lower NUMERIC NOT NULL, -- 80% confidence interval lower bound
    p80_upper NUMERIC NOT NULL, -- 80% confidence interval upper bound
    p20_lower NUMERIC NOT NULL, -- 20% confidence interval lower bound  
    p20_upper NUMERIC NOT NULL, -- 20% confidence interval upper bound
    predicted_activity INTEGER, -- predicted total activity count
    
    -- Model metadata
    model_version TEXT NOT NULL,
    model_type TEXT NOT NULL, -- 'hierarchical_ts', 'gradient_boost', 'ensemble'
    feature_importance JSONB, -- feature importance scores
    confidence_score NUMERIC DEFAULT 0, -- overall model confidence
    calibration_method TEXT, -- 'isotonic', 'platt', 'none'
    
    -- Validation metrics (when actuals become available)
    actual_surge BOOLEAN,
    actual_activity INTEGER,
    prediction_error NUMERIC,
    calibration_error NUMERIC,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(region_id, forecast_date, target_week_start, model_version)
);

-- Model Performance: Track cross-validation results and metrics
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version TEXT NOT NULL,
    model_type TEXT NOT NULL,
    validation_type TEXT NOT NULL, -- 'rolling_window_cv', 'time_series_split', 'backtest'
    
    -- Performance metrics
    pr_auc NUMERIC, -- Precision-Recall AUC
    brier_score NUMERIC, -- Brier score for probability calibration
    reliability_diagram JSONB, -- reliability plot data
    roc_auc NUMERIC,
    f1_score NUMERIC,
    precision NUMERIC,
    recall NUMERIC,
    
    -- Time series metrics
    mae NUMERIC, -- Mean Absolute Error
    rmse NUMERIC, -- Root Mean Square Error
    mape NUMERIC, -- Mean Absolute Percentage Error
    
    -- Validation period
    validation_start DATE,
    validation_end DATE,
    
    -- Hyperparameters and config
    model_config JSONB,
    feature_config JSONB,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(model_version, validation_type, validation_start, validation_end)
);

-- Forecast Jobs: Track weekly inference runs
CREATE TABLE IF NOT EXISTS forecast_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL, -- 'weekly_inference', 'backtest', 'model_training'
    job_status TEXT NOT NULL, -- 'running', 'completed', 'failed'
    
    -- Job parameters
    target_date DATE,
    regions_processed TEXT[], -- array of region IDs/slugs
    models_used TEXT[], -- array of model versions
    
    -- Results summary
    predictions_generated INTEGER DEFAULT 0,
    total_runtime_seconds NUMERIC DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB,
    
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Gold Forecast Table: Final output for API consumption
CREATE TABLE IF NOT EXISTS gold.forecast_nowx (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_slug TEXT NOT NULL,
    region_name TEXT NOT NULL,
    
    -- Current forecast
    forecast_week_start DATE NOT NULL,
    forecast_week_end DATE NOT NULL,
    p_surge NUMERIC NOT NULL,
    p80_lower NUMERIC NOT NULL,
    p80_upper NUMERIC NOT NULL,
    
    -- Comparison metrics
    prior_year_p_surge NUMERIC, -- same week last year
    surge_risk_change_pct NUMERIC, -- % change from last year
    
    -- Confidence and metadata
    confidence_score NUMERIC NOT NULL,
    model_version TEXT NOT NULL,
    last_updated TIMESTAMPTZ DEFAULT now(),
    
    -- API response optimization
    api_response_cache JSONB, -- pre-computed API response
    
    UNIQUE(region_slug, forecast_week_start)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_surge_labels_region_week ON surge_labels(region_id, week_start);
CREATE INDEX IF NOT EXISTS idx_forecast_features_region_date ON forecast_features(region_id, feature_date);
CREATE INDEX IF NOT EXISTS idx_forecast_predictions_region_target ON forecast_predictions(region_id, target_week_start);
CREATE INDEX IF NOT EXISTS idx_forecast_predictions_date ON forecast_predictions(forecast_date);
CREATE INDEX IF NOT EXISTS idx_model_performance_version ON model_performance(model_version);
CREATE INDEX IF NOT EXISTS idx_forecast_jobs_status ON forecast_jobs(job_status, started_at);
CREATE INDEX IF NOT EXISTS idx_gold_forecast_region ON gold.forecast_nowx(region_slug);
CREATE INDEX IF NOT EXISTS idx_gold_forecast_week ON gold.forecast_nowx(forecast_week_start);

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS gold;

-- Add trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_surge_labels_updated_at BEFORE UPDATE ON surge_labels FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_forecast_features_updated_at BEFORE UPDATE ON forecast_features FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_forecast_predictions_updated_at BEFORE UPDATE ON forecast_predictions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();