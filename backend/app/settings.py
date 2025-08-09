"""
Centralized settings for Home Services Lead Generation backend.

This module uses Pydantic for configuration management with environment variable support.
All configuration values should be defined here rather than hardcoded throughout the application.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://localhost/leadledger",
        env="DATABASE_URL",
        description="PostgreSQL database connection URL"
    )
    
    # Registry and scope configuration
    registry_path: str = Field(
        default=str(Path(__file__).parent.parent.parent / "config" / "registry.yaml"),
        env="REGISTRY_PATH",
        description="Path to the registry YAML file"
    )
    
    launch_scope: str = Field(
        default="houston",
        env="LAUNCH_SCOPE",
        description="Geographic scope for initial launch (houston, texas, national)"
    )
    
    default_region: str = Field(
        default="tx-houston",
        env="DEFAULT_REGION",
        description="Default region slug for new accounts"
    )
    
    # Export and access control
    allow_exports: bool = Field(
        default=False,
        env="ALLOW_EXPORTS",
        description="Whether to allow data exports (admin-only when True)"
    )
    
    # ML and scoring
    use_ml_scoring: bool = Field(
        default=False,
        env="USE_ML_SCORING", 
        description="Whether to use machine learning for lead scoring"
    )
    
    # Scheduling
    cron_scrape_utc: str = Field(
        default="0 5 * * *",
        env="CRON_SCRAPE_UTC",
        description="Cron schedule for nightly scraping (UTC timezone)"
    )
    
    # Notification settings
    notification_batch_size: int = Field(
        default=100,
        env="NOTIFICATION_BATCH_SIZE",
        description="Number of notifications to process in each batch"
    )
    
    min_score_threshold: float = Field(
        default=70.0,
        env="MIN_SCORE_THRESHOLD",
        description="Minimum lead score to trigger notifications"
    )
    
    # External service configuration
    sendgrid_api_key: Optional[str] = Field(
        default=None,
        env="SENDGRID_API_KEY",
        description="SendGrid API key for email notifications"
    )
    
    twilio_account_sid: Optional[str] = Field(
        default=None,
        env="TWILIO_ACCOUNT_SID",
        description="Twilio Account SID for SMS notifications"
    )
    
    twilio_auth_token: Optional[str] = Field(
        default=None,
        env="TWILIO_AUTH_TOKEN",
        description="Twilio Auth Token for SMS notifications"
    )
    
    # Redis configuration (for caching and job queues)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis connection URL for caching and queues"
    )
    
    # Admin configuration
    admin_emails: list[str] = Field(
        default_factory=list,
        env="ADMIN_EMAILS",
        description="Comma-separated list of admin email addresses"
    )
    
    # Application environment
    environment: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment (development, staging, production)"
    )
    
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode"
    )
    
    # Logging configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            """Custom parsing for environment variables."""
            if field_name == "admin_emails":
                return [email.strip() for email in raw_val.split(",") if email.strip()]
            return cls.json_loads(raw_val)


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the database URL for the current environment."""
    return settings.database_url


def is_houston_scope() -> bool:
    """Check if we're running in Houston-only scope."""
    return settings.launch_scope.lower() == "houston"


def exports_allowed() -> bool:
    """Check if data exports are allowed."""
    return settings.allow_exports


def get_active_jurisdictions() -> list[str]:
    """Get list of active jurisdiction slugs based on launch scope."""
    if is_houston_scope():
        return ["tx-harris", "tx-fort-bend", "tx-brazoria", "tx-galveston"]
    # Add logic for other scopes when implemented
    return []


def get_notification_settings() -> dict:
    """Get notification-related settings."""
    return {
        "batch_size": settings.notification_batch_size,
        "min_score_threshold": settings.min_score_threshold,
        "sendgrid_api_key": settings.sendgrid_api_key,
        "twilio_account_sid": settings.twilio_account_sid,
        "twilio_auth_token": settings.twilio_auth_token,
    }