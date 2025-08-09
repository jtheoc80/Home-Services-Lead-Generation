-- Subscription and cancellation tables migration
-- Creates tables for managing user subscriptions and cancellation tracking

-- Subscription status enum
CREATE TYPE subscription_status AS ENUM ('trial', 'active', 'cancelled', 'grace_period', 'expired');

-- Subscription plans enum
CREATE TYPE subscription_plan AS ENUM ('trial', 'basic', 'premium', 'enterprise');

-- User subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL, -- References auth.users(id) but using UUID for flexibility
  plan subscription_plan NOT NULL DEFAULT 'trial',
  status subscription_status NOT NULL DEFAULT 'trial',
  trial_start_date TIMESTAMPTZ,
  trial_end_date TIMESTAMPTZ,
  subscription_start_date TIMESTAMPTZ,
  subscription_end_date TIMESTAMPTZ,
  grace_period_end_date TIMESTAMPTZ,
  billing_cycle TEXT, -- 'monthly', 'yearly'
  amount_cents INTEGER, -- Subscription amount in cents
  payment_method TEXT, -- 'stripe', 'btc', 'eth', 'xrp'
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  -- Constraints
  UNIQUE (user_id), -- One subscription per user
  CHECK (trial_end_date > trial_start_date),
  CHECK (subscription_end_date IS NULL OR subscription_end_date > subscription_start_date),
  CHECK (amount_cents IS NULL OR amount_cents >= 0)
);

-- Cancellation records table for admin tracking
CREATE TABLE IF NOT EXISTS cancellation_records (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  subscription_id BIGINT NOT NULL REFERENCES user_subscriptions(id) ON DELETE CASCADE,
  cancellation_type TEXT NOT NULL CHECK (cancellation_type IN ('trial', 'paid')),
  reason_category TEXT, -- 'cost', 'not_satisfied', 'found_alternative', 'other'
  reason_notes TEXT, -- Free-form cancellation reason
  cancelled_at TIMESTAMPTZ DEFAULT now(),
  effective_date TIMESTAMPTZ, -- When cancellation actually takes effect
  grace_period_days INTEGER DEFAULT 0,
  
  -- Admin tracking fields
  processed_by UUID, -- Admin who processed the cancellation
  refund_issued BOOLEAN DEFAULT false,
  refund_amount_cents INTEGER,
  
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan ON user_subscriptions(plan);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_trial_end ON user_subscriptions(trial_end_date);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_subscription_end ON user_subscriptions(subscription_end_date);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_grace_end ON user_subscriptions(grace_period_end_date);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_updated_at ON user_subscriptions(updated_at);

CREATE INDEX IF NOT EXISTS idx_cancellation_records_user_id ON cancellation_records(user_id);
CREATE INDEX IF NOT EXISTS idx_cancellation_records_subscription_id ON cancellation_records(subscription_id);
CREATE INDEX IF NOT EXISTS idx_cancellation_records_type ON cancellation_records(cancellation_type);
CREATE INDEX IF NOT EXISTS idx_cancellation_records_cancelled_at ON cancellation_records(cancelled_at);
CREATE INDEX IF NOT EXISTS idx_cancellation_records_effective_date ON cancellation_records(effective_date);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_status ON user_subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_cancellation_records_user_type ON cancellation_records(user_id, cancellation_type);

-- Add comments for documentation
COMMENT ON TABLE user_subscriptions IS 'User subscription plans and billing information';
COMMENT ON TABLE cancellation_records IS 'Cancellation tracking for admin review and analytics';

COMMENT ON COLUMN user_subscriptions.user_id IS 'User account identifier';
COMMENT ON COLUMN user_subscriptions.plan IS 'Subscription plan type';
COMMENT ON COLUMN user_subscriptions.status IS 'Current subscription status';
COMMENT ON COLUMN user_subscriptions.trial_start_date IS 'When trial period began';
COMMENT ON COLUMN user_subscriptions.trial_end_date IS 'When trial period ends/ended';
COMMENT ON COLUMN user_subscriptions.subscription_start_date IS 'When paid subscription began';
COMMENT ON COLUMN user_subscriptions.subscription_end_date IS 'When subscription ends (null for active)';
COMMENT ON COLUMN user_subscriptions.grace_period_end_date IS 'End of grace period for cancelled paid subscriptions';
COMMENT ON COLUMN user_subscriptions.billing_cycle IS 'Billing frequency for paid subscriptions';
COMMENT ON COLUMN user_subscriptions.amount_cents IS 'Subscription cost in cents';
COMMENT ON COLUMN user_subscriptions.payment_method IS 'Payment method used';

COMMENT ON COLUMN cancellation_records.cancellation_type IS 'Whether this was a trial or paid subscription cancellation';
COMMENT ON COLUMN cancellation_records.reason_category IS 'Categorized reason for cancellation';
COMMENT ON COLUMN cancellation_records.reason_notes IS 'Detailed cancellation reason from user';
COMMENT ON COLUMN cancellation_records.effective_date IS 'When access actually terminates';
COMMENT ON COLUMN cancellation_records.grace_period_days IS 'Number of days in grace period';
COMMENT ON COLUMN cancellation_records.processed_by IS 'Admin who processed the cancellation';
COMMENT ON COLUMN cancellation_records.refund_issued IS 'Whether a refund was provided';
COMMENT ON COLUMN cancellation_records.refund_amount_cents IS 'Refund amount in cents if applicable';