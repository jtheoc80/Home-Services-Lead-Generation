-- Notifications table migration
-- Creates table for managing user notifications across different channels

CREATE TABLE IF NOT EXISTS notifications (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL,
  lead_id BIGINT NOT NULL,
  channel TEXT NOT NULL CHECK (channel IN ('inapp', 'email', 'sms')),
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'failed', 'read')),
  created_at TIMESTAMPTZ DEFAULT now(),
  sent_at TIMESTAMPTZ
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_notifications_account_id ON notifications(account_id);
CREATE INDEX IF NOT EXISTS idx_notifications_lead_id ON notifications(lead_id);
CREATE INDEX IF NOT EXISTS idx_notifications_channel ON notifications(channel);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_notifications_account_status ON notifications(account_id, status);
CREATE INDEX IF NOT EXISTS idx_notifications_lead_channel ON notifications(lead_id, channel);

-- Add comments for documentation
COMMENT ON TABLE notifications IS 'User notifications for lead updates and system events';
COMMENT ON COLUMN notifications.account_id IS 'User account identifier for notification targeting';
COMMENT ON COLUMN notifications.lead_id IS 'Lead identifier this notification relates to';
COMMENT ON COLUMN notifications.channel IS 'Delivery channel: inapp, email, or sms';
COMMENT ON COLUMN notifications.status IS 'Notification lifecycle status: queued, sent, failed, or read';
COMMENT ON COLUMN notifications.created_at IS 'Timestamp when notification was created';
COMMENT ON COLUMN notifications.sent_at IS 'Timestamp when notification was successfully sent';