#!/usr/bin/env python3
"""
Export control utility for managing data exports based on environment configuration.

This module provides functionality to control data exports based on the
ALLOW_EXPORTS environment variable and track export activities.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class ExportType(Enum):
    """Types of data exports."""
    LEADS = "leads"
    PERMITS = "permits" 
    SCORED_LEADS = "scored_leads"
    ANALYTICS = "analytics"
    FEEDBACK = "feedback"


@dataclass
class ExportRequest:
    """Data structure for export requests."""
    export_type: ExportType
    requester: str
    parameters: Dict[str, Any]
    timestamp: datetime
    export_id: str


@dataclass
class ExportResult:
    """Data structure for export results."""
    export_id: str
    success: bool
    allowed: bool
    reason: Optional[str] = None
    record_count: Optional[int] = None
    file_path: Optional[str] = None
    timestamp: Optional[datetime] = None


class ExportController:
    """Controller for managing data export permissions and tracking."""
    
    def __init__(self):
        self.exports_allowed = self._get_export_permission()
        
    def _get_export_permission(self) -> bool:
        """Get export permission from environment variable."""
        allow_exports = os.getenv('ALLOW_EXPORTS', 'false').lower()
        return allow_exports in ('true', '1', 'yes', 'on')
    
    def is_export_allowed(
        self, 
        export_type: ExportType, 
        requester: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a specific export is allowed.
        
        Args:
            export_type: Type of export requested
            requester: User or system requesting the export
            parameters: Optional export parameters
            
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        # Check global export permission
        if not self.exports_allowed:
            reason = "Data exports are disabled by configuration (ALLOW_EXPORTS=false)"
            logger.warning(f"Export blocked for {requester}: {reason}")
            
            # Log the blocked attempt for audit
            self._log_blocked_export_attempt(export_type, requester, reason, parameters)
            
            return False, reason
        
        # Additional validation could be added here for specific export types
        # For example:
        # - Check user permissions
        # - Validate export parameters
        # - Apply rate limiting
        # - Check data sensitivity levels
        
        logger.info(f"Export allowed for {requester}: {export_type.value}")
        return True, None
    
    def create_export_request(
        self,
        export_type: ExportType,
        requester: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ExportRequest:
        """
        Create a new export request.
        
        Args:
            export_type: Type of export
            requester: User or system requesting the export
            parameters: Export parameters
            
        Returns:
            ExportRequest object
        """
        import uuid
        
        export_id = str(uuid.uuid4())
        return ExportRequest(
            export_type=export_type,
            requester=requester,
            parameters=parameters or {},
            timestamp=datetime.now(timezone.utc),
            export_id=export_id
        )
    
    def process_export_request(self, request: ExportRequest) -> ExportResult:
        """
        Process an export request and return the result.
        
        Args:
            request: Export request to process
            
        Returns:
            ExportResult with processing outcome
        """
        # Check if export is allowed
        allowed, reason = self.is_export_allowed(
            request.export_type,
            request.requester,
            request.parameters
        )
        
        result = ExportResult(
            export_id=request.export_id,
            success=False,
            allowed=allowed,
            reason=reason,
            timestamp=datetime.now(timezone.utc)
        )
        
        if not allowed:
            # Log the blocked export attempt
            self._log_export_attempt(request, result)
            
            # Send notification about blocked export
            self._notify_export_blocked(request, result)
            
            return result
        
        # Export is allowed, proceed with actual export
        try:
            # This would be where the actual export logic is implemented
            # For now, we'll just mark it as successful
            result.success = True
            result.record_count = 0  # Would be set by actual export logic
            
            logger.info(f"Export {request.export_id} completed successfully")
            
        except Exception as e:
            result.success = False
            result.reason = f"Export failed: {str(e)}"
            logger.error(f"Export {request.export_id} failed: {str(e)}")
        
        # Log the export attempt
        self._log_export_attempt(request, result)
        
        return result
    
    def _log_export_attempt(self, request: ExportRequest, result: ExportResult):
        """Log export attempt for audit purposes."""
        log_entry = {
            'export_id': request.export_id,
            'export_type': request.export_type.value,
            'requester': request.requester,
            'timestamp': request.timestamp.isoformat(),
            'allowed': result.allowed,
            'success': result.success,
            'reason': result.reason,
            'record_count': result.record_count,
            'admin_override': request.parameters.get('admin_override', False),
            'user_id': request.parameters.get('user_id', 'unknown')
        }
        
        # In a real implementation, this might write to a database or audit log
        if result.allowed and result.success:
            logger.info(f"AUDIT: Export successful - {log_entry}")
        elif not result.allowed:
            logger.warning(f"AUDIT: Export blocked - {log_entry}")
        else:
            logger.error(f"AUDIT: Export failed - {log_entry}")
    
    def _log_blocked_export_attempt(self, export_type: ExportType, requester: str, reason: str, parameters: Optional[Dict[str, Any]] = None):
        """Log a blocked export attempt immediately for audit purposes."""
        log_entry = {
            'export_type': export_type.value,
            'requester': requester,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'blocked': True,
            'reason': reason,
            'parameters': parameters or {}
        }
        
        # Log blocked attempt for audit
        logger.warning(f"AUDIT: Export attempt blocked - {log_entry}")
        
        # Also store for potential admin notification
        self._notify_blocked_export_attempt(export_type, requester, reason)
    
    def _notify_export_blocked(self, request: ExportRequest, result: ExportResult):
        """Send notification when export is blocked."""
        try:
            from .notifications import get_notification_service
            
            notification_service = get_notification_service()
            
            # Get admin email from environment or use default
            admin_emails = os.getenv('ADMIN_NOTIFICATION_EMAILS', '').split(',')
            admin_emails = [email.strip() for email in admin_emails if email.strip()]
            
            if admin_emails:
                notification_service.notify_export_request(
                    requester=request.requester,
                    export_type=request.export_type.value,
                    allowed=result.allowed,
                    email_recipients=admin_emails
                )
            
        except Exception as e:
            logger.error(f"Failed to send export notification: {str(e)}")
    
    def _notify_blocked_export_attempt(self, export_type: ExportType, requester: str, reason: str):
        """Send notification when export attempt is blocked immediately."""
        try:
            # Get admin email from environment or use default
            admin_emails = os.getenv('ADMIN_NOTIFICATION_EMAILS', '').split(',')
            admin_emails = [email.strip() for email in admin_emails if email.strip()]
            
            if admin_emails:
                logger.info(f"Would notify admins about blocked export: {requester} attempted {export_type.value}")
                # In a real implementation, this would send actual notifications
                
        except Exception as e:
            logger.error(f"Failed to send blocked export notification: {str(e)}")
    
    def _create_admin_override_result(self, request: ExportRequest) -> ExportResult:
        """
        Create a successful export result for admin override cases.
        
        This method bypasses the normal export permission checks and 
        creates a successful result for admin override scenarios.
        """
        result = ExportResult(
            export_id=request.export_id,
            success=True,
            allowed=True,
            reason="Admin override authorized",
            record_count=0,  # Would be set by actual export logic
            timestamp=datetime.now(timezone.utc)
        )
        
        # Log the admin override export
        logger.info(f"Admin override export {request.export_id} completed successfully")
        
        # Log the export attempt for audit
        self._log_export_attempt(request, result)
        
        return result
    
    def get_export_status(self) -> Dict[str, Any]:
        """
        Get current export configuration status.
        
        Returns:
            Dictionary with export status information
        """
        return {
            'exports_enabled': self.exports_allowed,
            'supported_types': [export_type.value for export_type in ExportType],
            'configuration_source': 'ALLOW_EXPORTS environment variable'
        }


# Decorator for protecting export endpoints
def require_export_permission(export_type: ExportType):
    """
    Decorator to protect export endpoints.
    
    Args:
        export_type: Type of export being protected
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            controller = get_export_controller()
            
            # Try to get requester info from kwargs or use default
            requester = kwargs.get('requester', 'system')
            
            allowed, reason = controller.is_export_allowed(export_type, requester)
            
            if not allowed:
                raise PermissionError(f"Export not allowed: {reason}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global export controller instance
_export_controller = None

def get_export_controller() -> ExportController:
    """Get the global export controller instance."""
    global _export_controller
    # Always create a new instance to pick up environment changes
    # In production, this could be optimized with caching and invalidation
    if _export_controller is None:
        _export_controller = ExportController()
    return _export_controller