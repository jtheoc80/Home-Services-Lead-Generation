"""
Application settings and configuration management.
Supports production and staging environments via APP_ENV variable.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application configuration settings"""
    
    def __init__(self):
        self.app_env = os.getenv('APP_ENV', 'production').lower()
        self.is_staging = self.app_env == 'staging'
        self.is_production = self.app_env == 'production'
        
    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable with staging suffix support.
        In staging mode, first try KEY_STAGING, then fall back to KEY.
        """
        if self.is_staging:
            staging_key = f"{key}_STAGING"
            staging_value = os.getenv(staging_key)
            if staging_value is not None:
                return staging_value
        
        return os.getenv(key, default)
    
    @property
    def database_url(self) -> str:
        """Database connection URL"""
        return self.get_env_var('DATABASE_URL', 'sqlite:///./data/permits/permits.db')
    
    @property
    def redis_url(self) -> str:
        """Redis connection URL"""
        return self.get_env_var('REDIS_URL', 'redis://localhost:6379/0')
    
    @property
    def secret_key(self) -> str:
        """Secret key for app security"""
        return self.get_env_var('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    @property
    def debug(self) -> bool:
        """Debug mode flag"""
        debug_val = self.get_env_var('DEBUG', 'false' if self.is_production else 'true')
        return debug_val.lower() in ('true', '1', 'yes', 'on')
    
    @property
    def api_host(self) -> str:
        """API server host"""
        return self.get_env_var('API_HOST', '0.0.0.0')
    
    @property
    def api_port(self) -> int:
        """API server port"""
        return int(self.get_env_var('API_PORT', '8000'))
    
    @property
    def allow_exports(self) -> bool:
        """Whether data exports are allowed"""
        exports_val = self.get_env_var('ALLOW_EXPORTS', 'false')
        return exports_val.lower() in ('true', '1', 'yes', 'on')
    
    @property
    def sendgrid_api_key(self) -> Optional[str]:
        """SendGrid API key for email notifications"""
        return self.get_env_var('SENDGRID_API_KEY')
    
    @property
    def twilio_sid(self) -> Optional[str]:
        """Twilio Account SID"""
        return self.get_env_var('TWILIO_SID')
    
    @property
    def twilio_token(self) -> Optional[str]:
        """Twilio Auth Token"""
        return self.get_env_var('TWILIO_TOKEN')
    
    @property
    def twilio_from(self) -> Optional[str]:
        """Twilio phone number for sending SMS"""
        return self.get_env_var('TWILIO_FROM')


# Global settings instance
settings = Settings()