"""
Health check API endpoint for monitoring service status.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

try:
    import redis
    import psycopg2
    from sqlalchemy import create_engine
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    redis = None
    psycopg2 = None
    create_engine = None
    SQLAlchemyError = Exception

from .settings import settings

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health check service for monitoring dependencies."""
    
    def __init__(self):
        self.settings = settings
        
    def check_database(self) -> bool:
        """Check database connectivity."""
        try:
            if create_engine is None:
                logger.warning("SQLAlchemy not available, skipping database check")
                return False
                
            engine = create_engine(self.settings.database_url)
            with engine.connect() as connection:
                # Simple ping query
                result = connection.execute(text("SELECT 1"))
                return result.fetchone() is not None
                
        except (SQLAlchemyError, Exception) as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def check_redis(self) -> bool:
        """Check Redis connectivity."""
        try:
            if redis is None:
                logger.warning("Redis not available, skipping Redis check")
                return False
                
            redis_client = redis.from_url(self.settings.redis_url)
            redis_client.ping()
            return True
            
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        db_status = self.check_database()
        redis_status = self.check_redis()
        
        overall_ok = db_status and redis_status
        
        return {
            "ok": overall_ok,
            "env": self.settings.app_env,
            "db": db_status,
            "redis": redis_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"  # Could be pulled from package.json or git
        }


class HealthAPI:
    """API handler for health check endpoints."""
    
    def __init__(self):
        self.health_checker = HealthChecker()
    
    def handle_health_check(self) -> Dict[str, Any]:
        """
        Handle health check request.
        
        Returns:
            Dictionary with health status information
        """
        try:
            status = self.health_checker.get_health_status()
            logger.info(f"Health check performed: {status}")
            return status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "ok": False,
                "env": settings.app_env,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Request ID middleware functionality
class RequestLogger:
    """Request logging with IDs and account tracking."""
    
    @staticmethod
    def generate_request_id() -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())
    
    @staticmethod
    def log_request(request_id: str, method: str, path: str, account_id: str = None, 
                   status_code: int = None, response_time_ms: float = None) -> None:
        """
        Log request details with standardized format.
        
        Args:
            request_id: Unique request identifier
            method: HTTP method (GET, POST, etc.)
            path: Request path/route
            account_id: User account ID if available
            status_code: HTTP response status code
            response_time_ms: Response time in milliseconds
        """
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if account_id:
            log_data["account_id"] = account_id
            
        if status_code:
            log_data["status_code"] = status_code
            
        if response_time_ms:
            log_data["response_time_ms"] = round(response_time_ms, 2)
        
        # Log based on status code level
        if status_code:
            if 200 <= status_code < 300:
                logger.info(f"Request completed: {json.dumps(log_data)}")
            elif 400 <= status_code < 500:
                logger.warning(f"Client error: {json.dumps(log_data)}")
            elif 500 <= status_code < 600:
                logger.error(f"Server error: {json.dumps(log_data)}")
            else:
                logger.info(f"Request logged: {json.dumps(log_data)}")
        else:
            logger.info(f"Request started: {json.dumps(log_data)}")


# Global instances
health_api = HealthAPI()
request_logger = RequestLogger()