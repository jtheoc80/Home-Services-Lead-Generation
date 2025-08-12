#!/usr/bin/env python3
"""
Subscription management API endpoints.

Provides REST API endpoints for subscription operations including:
- Cancel subscription
- Reactivate subscription
- Get subscription status
- Admin cancellation records view
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .subscription_manager import (
    get_subscription_manager,
    SubscriptionInfo,
    CancellationRequest,
    SubscriptionStatus,
    SubscriptionPlan
)

# Configure logging
logger = logging.getLogger(__name__)


class SubscriptionAPI:
    """API handler for subscription operations."""
    
    def __init__(self):
        self.subscription_manager = get_subscription_manager()
    
    def cancel_subscription(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription cancellation request.
        
        Args:
            request_data: Dictionary containing:
                - user_id: User identifier
                - reason_category: Optional cancellation reason category
                - reason_notes: Optional detailed reason
                - processed_by: Optional admin user ID
                
        Returns:
            Dictionary with cancellation result
        """
        try:
            # Validate required fields
            user_id = request_data.get('user_id')
            if not user_id:
                return {
                    'success': False,
                    'error': 'user_id is required',
                    'status_code': 400
                }
            
            # Get current subscription (in real implementation, fetch from database)
            subscription = self._get_subscription_by_user_id(user_id)
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found',
                    'status_code': 404
                }
            
            # Check if already cancelled
            if subscription.status in [SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]:
                return {
                    'success': False,
                    'error': 'Subscription is already cancelled',
                    'status_code': 400
                }
            
            # Create cancellation request
            cancellation_request = CancellationRequest(
                user_id=user_id,
                reason_category=request_data.get('reason_category'),
                reason_notes=request_data.get('reason_notes'),
                processed_by=request_data.get('processed_by')
            )
            
            # Process cancellation
            result = self.subscription_manager.cancel_subscription(subscription, cancellation_request)
            
            if result['success']:
                # In real implementation, save updated subscription and cancellation record to database
                self._save_subscription_update(result['updated_subscription'])
                self._save_cancellation_record(result['cancellation_record'])
                
                return {
                    'success': True,
                    'data': {
                        'cancellation_type': result['cancellation_type'],
                        'effective_date': result['effective_date'].isoformat(),
                        'grace_period_days': result['grace_period_days'],
                        'message': result['message']
                    },
                    'status_code': 200
                }
            else:
                return {
                    'success': False,
                    'error': 'Cancellation processing failed',
                    'status_code': 500
                }
                
        except Exception as e:
            logger.error(f"Error processing cancellation: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'status_code': 500
            }
    
    def reactivate_subscription(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription reactivation request.
        
        Args:
            request_data: Dictionary containing:
                - user_id: User identifier
                
        Returns:
            Dictionary with reactivation result
        """
        try:
            # Validate required fields
            user_id = request_data.get('user_id')
            if not user_id:
                return {
                    'success': False,
                    'error': 'user_id is required',
                    'status_code': 400
                }
            
            # Get current subscription
            subscription = self._get_subscription_by_user_id(user_id)
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found',
                    'status_code': 404
                }
            
            # Check if subscription can be reactivated
            if subscription.status not in [SubscriptionStatus.CANCELLED, SubscriptionStatus.GRACE_PERIOD]:
                return {
                    'success': False,
                    'error': 'Subscription cannot be reactivated in current status',
                    'status_code': 400
                }
            
            # Process reactivation
            result = self.subscription_manager.reactivate_subscription(subscription)
            
            if result['success']:
                # In real implementation, save updated subscription to database
                self._save_subscription_update(result['updated_subscription'])
                
                return {
                    'success': True,
                    'data': {
                        'message': result['message'],
                        'status': result['updated_subscription'].status.value
                    },
                    'status_code': 200
                }
            else:
                return {
                    'success': False,
                    'error': 'Reactivation processing failed',
                    'status_code': 500
                }
                
        except Exception as e:
            logger.error(f"Error processing reactivation: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'status_code': 500
            }
    
    def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get current subscription status for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with subscription status
        """
        try:
            subscription = self._get_subscription_by_user_id(user_id)
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found',
                    'status_code': 404
                }
            
            return {
                'success': True,
                'data': {
                    'user_id': subscription.user_id,
                    'plan': subscription.plan.value,
                    'status': subscription.status.value,
                    'trial_end_date': subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
                    'subscription_end_date': subscription.subscription_end_date.isoformat() if subscription.subscription_end_date else None,
                    'grace_period_end_date': subscription.grace_period_end_date.isoformat() if subscription.grace_period_end_date else None,
                    'billing_cycle': subscription.billing_cycle,
                    'amount_cents': subscription.amount_cents
                },
                'status_code': 200
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'status_code': 500
            }
    
    def get_cancellation_records(self, 
                               admin_user_id: str, 
                               filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get cancellation records for admin review.
        
        Args:
            admin_user_id: Admin user requesting the records
            filters: Optional filters for the query
            
        Returns:
            Dictionary with cancellation records
        """
        try:
            # In real implementation, verify admin permissions
            if not self._is_admin_user(admin_user_id):
                return {
                    'success': False,
                    'error': 'Insufficient permissions',
                    'status_code': 403
                }
            
            # In real implementation, fetch from database with filters
            cancellation_records = self._get_cancellation_records_from_db(filters or {})
            
            return {
                'success': True,
                'data': {
                    'records': cancellation_records,
                    'total_count': len(cancellation_records)
                },
                'status_code': 200
            }
            
        except Exception as e:
            logger.error(f"Error getting cancellation records: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'status_code': 500
            }
    
    def _get_subscription_by_user_id(self, user_id: str) -> Optional[SubscriptionInfo]:
        """
        Get subscription information for a user.
        
        In a real implementation, this would query the database.
        For demo purposes, returns a mock subscription.
        """
        # Mock data for demonstration
        if user_id == "demo-trial-user":
            return SubscriptionInfo(
                id=1,
                user_id=user_id,
                plan=SubscriptionPlan.TRIAL,
                status=SubscriptionStatus.TRIAL,
                trial_start_date=datetime.utcnow(),
                trial_end_date=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
        elif user_id == "demo-paid-user":
            return SubscriptionInfo(
                id=2,
                user_id=user_id,
                plan=SubscriptionPlan.PREMIUM,
                status=SubscriptionStatus.ACTIVE,
                subscription_start_date=datetime.utcnow(),
                billing_cycle="monthly",
                amount_cents=4999,
                created_at=datetime.utcnow()
            )
        elif user_id == "demo-cancelled-user":
            return SubscriptionInfo(
                id=3,
                user_id=user_id,
                plan=SubscriptionPlan.BASIC,
                status=SubscriptionStatus.GRACE_PERIOD,
                subscription_start_date=datetime.utcnow(),
                grace_period_end_date=datetime.utcnow(),
                billing_cycle="monthly",
                amount_cents=2999,
                created_at=datetime.utcnow()
            )
        else:
            return None
    
    def _save_subscription_update(self, subscription: SubscriptionInfo) -> bool:
        """
        Save subscription update to database.
        
        In real implementation, this would update the database.
        """
        logger.info(f"Saving subscription update for user {subscription.user_id}")
        return True
    
    def _save_cancellation_record(self, record: Dict[str, Any]) -> bool:
        """
        Save cancellation record to database.
        
        In real implementation, this would insert into the database.
        """
        logger.info(f"Saving cancellation record for user {record['user_id']}")
        return True
    
    def _is_admin_user(self, user_id: str) -> bool:
        """
        Check if user has admin permissions.
        
        In real implementation, this would check user roles in database.
        """
        # Demo: users starting with "admin-" are considered admins
        return user_id.startswith("admin-")
    
    def _get_cancellation_records_from_db(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get cancellation records from database with filters.
        
        In real implementation, this would query the database.
        """
        # Mock data for demonstration
        return [
            {
                'id': 1,
                'user_id': 'demo-trial-user',
                'subscription_id': 1,
                'cancellation_type': 'trial',
                'reason_category': 'not_satisfied',
                'reason_notes': 'Service did not meet expectations',
                'cancelled_at': datetime.utcnow().isoformat(),
                'effective_date': datetime.utcnow().isoformat(),
                'grace_period_days': 0,
                'processed_by': None,
                'refund_issued': False
            },
            {
                'id': 2,
                'user_id': 'demo-paid-user',
                'subscription_id': 2,
                'cancellation_type': 'paid',
                'reason_category': 'cost',
                'reason_notes': 'Too expensive for current needs',
                'cancelled_at': datetime.utcnow().isoformat(),
                'effective_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'grace_period_days': 30,
                'processed_by': 'admin-user-123',
                'refund_issued': False
            }
        ]


# Global API instance
_subscription_api = None

def get_subscription_api() -> SubscriptionAPI:
    """Get the global subscription API instance."""
    global _subscription_api
    if _subscription_api is None:
        _subscription_api = SubscriptionAPI()
    return _subscription_api