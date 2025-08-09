#!/usr/bin/env python3
"""
Notification utilities for sending emails and SMS notifications.

This module provides utility functions for sending notifications using
SendGrid (email) and Twilio (SMS) services based on environment configuration.
"""

import os
import logging
from typing import Optional, Dict, Any, List
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


# Global notification service instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get the global notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service