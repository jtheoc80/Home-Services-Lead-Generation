#!/usr/bin/env python3
"""
Notification utilities for sending emails and SMS notifications.

This module provides utility functions for sending notifications using
SendGrid (email) and Twilio (SMS) services based on environment configuration.
"""

import os
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration for notification services."""
    sendgrid_api_key: Optional[str] = None
    twilio_sid: Optional[str] = None
    twilio_token: Optional[str] = None
    twilio_from: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'NotificationConfig':
        """Create configuration from environment variables."""
        return cls(
            sendgrid_api_key=os.getenv('SENDGRID_API_KEY'),
            twilio_sid=os.getenv('TWILIO_SID'),
            twilio_token=os.getenv('TWILIO_TOKEN'),
            twilio_from=os.getenv('TWILIO_FROM')
        )


class EmailNotifier:
    """Email notification service using SendGrid."""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        """Lazy load SendGrid client."""
        if self._client is None and self.config.sendgrid_api_key:
            try:
                import sendgrid
                from sendgrid.helpers.mail import Mail
                self._client = sendgrid.SendGridAPIClient(api_key=self.config.sendgrid_api_key)
                self._mail_helper = Mail
            except ImportError:
                logger.warning("SendGrid library not installed. Email notifications disabled.")
                return None
        return self._client
    
    def is_enabled(self) -> bool:
        """Check if email notifications are enabled."""
        return bool(self.config.sendgrid_api_key and self._get_client())
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        from_email: str = "noreply@leadledgerpro.com",
        html_content: Optional[str] = None
    ) -> bool:
        """
        Send an email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Plain text content
            from_email: Sender email address
            html_content: Optional HTML content
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_enabled():
            logger.warning("Email notifications not enabled. Skipping email send.")
            return False
            
        try:
            client = self._get_client()
            mail = self._mail_helper(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=content,
                html_content=html_content
            )
            
            response = client.send(mail)
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False


class SMSNotifier:
    """SMS notification service using Twilio."""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        """Lazy load Twilio client."""
        if self._client is None and self.config.twilio_sid and self.config.twilio_token:
            try:
                from twilio.rest import Client
                self._client = Client(self.config.twilio_sid, self.config.twilio_token)
            except ImportError:
                logger.warning("Twilio library not installed. SMS notifications disabled.")
                return None
        return self._client
    
    def is_enabled(self) -> bool:
        """Check if SMS notifications are enabled."""
        return bool(
            self.config.twilio_sid and 
            self.config.twilio_token and 
            self.config.twilio_from and 
            self._get_client()
        )
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send an SMS notification.
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: SMS message content
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        if not self.is_enabled():
            logger.warning("SMS notifications not enabled. Skipping SMS send.")
            return False
            
        try:
            client = self._get_client()
            message_obj = client.messages.create(
                body=message,
                from_=self.config.twilio_from,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}. SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS to {to_number}: {str(e)}")
            return False


class NotificationService:
    """Unified notification service for email and SMS."""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig.from_env()
        self.email = EmailNotifier(self.config)
        self.sms = SMSNotifier(self.config)
    
    def notify_lead_processed(
        self,
        lead_count: int,
        email_recipients: Optional[List[str]] = None,
        sms_recipients: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send notification about processed leads.
        
        Args:
            lead_count: Number of leads processed
            email_recipients: List of email addresses to notify
            sms_recipients: List of phone numbers to notify
            
        Returns:
            Dictionary with notification results
        """
        results = {"email": False, "sms": False}
        
        message = f"Lead processing complete. {lead_count} leads processed and ready for review."
        
        # Send email notifications
        if email_recipients and self.email.is_enabled():
            for email in email_recipients:
                success = self.email.send_email(
                    to_email=email,
                    subject="Lead Processing Complete",
                    content=message
                )
                results["email"] = results["email"] or success
        
        # Send SMS notifications
        if sms_recipients and self.sms.is_enabled():
            for phone in sms_recipients:
                success = self.sms.send_sms(
                    to_number=phone,
                    message=message
                )
                results["sms"] = results["sms"] or success
        
        return results
    
    def notify_export_request(
        self,
        requester: str,
        export_type: str,
        allowed: bool,
        email_recipients: Optional[List[str]] = None
    ) -> bool:
        """
        Send notification about export request.
        
        Args:
            requester: User who requested the export
            export_type: Type of export requested
            allowed: Whether the export was allowed
            email_recipients: List of email addresses to notify
            
        Returns:
            True if notification was sent successfully
        """
        status = "ALLOWED" if allowed else "BLOCKED"
        subject = f"Data Export Request {status}"
        message = f"Export request by {requester} for {export_type} was {status.lower()}."
        
        if email_recipients and self.email.is_enabled():
            for email in email_recipients:
                return self.email.send_email(
                    to_email=email,
                    subject=subject,
                    content=message
                )
        
        return False


def process_new_lead_notifications() -> int:
    """
    Process notifications for new leads based on user preferences.
    
    This function is called after lead ingestion to create notifications
    for users who have matching preferences for the newly imported leads.
    
    Returns:
        Number of notifications created
    """
    import os
    import psycopg2
    
    try:
        # Get database connection
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.warning("DATABASE_URL not set, skipping notification processing")
            return 0
            
        conn = psycopg2.connect(db_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Find new leads (created in last hour) that match user preferences
        query = """
        WITH new_leads AS (
            SELECT 
                l.id,
                l.jurisdiction,
                l.lead_score,
                l.trade_tags,
                l.value,
                l.created_at
            FROM leads l
            WHERE l.created_at > NOW() - INTERVAL '1 hour'
            AND l.lead_score IS NOT NULL
        ),
        matching_prefs AS (
            SELECT 
                np.account_id,
                np.min_score_threshold,
                np.counties,
                np.channels,
                np.trade_tags AS pref_trade_tags,
                np.value_threshold,
                nl.id AS lead_id,
                nl.lead_score,
                nl.jurisdiction,
                nl.trade_tags AS lead_trade_tags,
                nl.value
            FROM notification_prefs np
            CROSS JOIN new_leads nl
            WHERE np.is_enabled = TRUE
            AND nl.lead_score >= np.min_score_threshold
            AND (
                np.counties IS NULL 
                OR np.counties = ARRAY[]::text[]
                OR nl.jurisdiction = ANY(np.counties)
            )
            AND (
                np.trade_tags IS NULL 
                OR np.trade_tags = ARRAY[]::text[]
                OR nl.trade_tags && np.trade_tags
            )
            AND (
                np.value_threshold IS NULL 
                OR nl.value >= np.value_threshold
            )
        )
        INSERT INTO notifications (account_id, lead_id, channel, title, message, metadata)
        SELECT 
            mp.account_id,
            mp.lead_id,
            unnest(mp.channels) as channel,
            'New High-Quality Lead Available',
            CONCAT(
                'A new lead with score ', 
                ROUND(mp.lead_score, 1), 
                ' is available in ', 
                mp.jurisdiction,
                CASE 
                    WHEN mp.value IS NOT NULL THEN CONCAT(' (Est. Value: $', ROUND(mp.value, 0), ')')
                    ELSE ''
                END
            ),
            jsonb_build_object(
                'lead_score', mp.lead_score,
                'jurisdiction', mp.jurisdiction,
                'estimated_value', mp.value,
                'trade_tags', mp.lead_trade_tags
            )
        FROM matching_prefs mp
        ON CONFLICT DO NOTHING
        RETURNING id;
        """
        
        cur.execute(query)
        results = cur.fetchall()
        notification_count = len(results)
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Created {notification_count} notifications for new leads")
        return notification_count
        
    except Exception as e:
        logger.error(f"Error processing new lead notifications: {e}")
        return 0


# Global notification service instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get the global notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service