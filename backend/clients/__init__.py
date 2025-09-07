"""
Auto-generated Python API client for LeadLedgerPro
Generated from OpenAPI specification

This module provides a convenient wrapper around the generated API client.
"""

import os
from typing import Optional

try:
    # Try importing the generated client
    from .leadledderpro_client.api_client import ApiClient
    from .leadledderpro_client.configuration import Configuration
    from .leadledderpro_client.api.admin_api import AdminApi
    from .leadledderpro_client.api.auth_api import AuthApi
    from .leadledderpro_client.api.export_api import ExportApi
    from .leadledderpro_client.api.health_api import HealthApi
    from .leadledderpro_client.api.monitoring_api import MonitoringApi
    from .leadledderpro_client.api.root_api import RootApi
    from .leadledderpro_client.api.subscription_api import SubscriptionApi

    # Models
    from .leadledderpro_client.models.cancellation_request import CancellationRequest
    from .leadledderpro_client.models.reactivation_request import ReactivationRequest
    from .leadledderpro_client.models.export_data_request import ExportDataRequest
    from .leadledderpro_client.models.http_validation_error import HTTPValidationError
    from .leadledderpro_client.models.validation_error import ValidationError

    class LeadLedgerProClient:
        """
        Convenient wrapper for the LeadLedgerPro API client
        """

        def __init__(
            self, base_url: Optional[str] = None, api_key: Optional[str] = None
        ):
            """
            Initialize the API client

            Args:
                base_url: Base URL for the API (defaults to localhost:8000)
                api_key: API key for authentication
            """
            config = Configuration()
            config.host = base_url or os.getenv("API_BASE", "http://localhost:8000")

            if api_key:
                config.api_key["Authorization"] = api_key
                config.api_key_prefix["Authorization"] = "Bearer"

            self.api_client = ApiClient(config)

            # Initialize API endpoints
            self.admin = AdminApi(self.api_client)
            self.auth = AuthApi(self.api_client)
            self.export = ExportApi(self.api_client)
            self.health = HealthApi(self.api_client)
            self.monitoring = MonitoringApi(self.api_client)
            self.root = RootApi(self.api_client)
            self.subscription = SubscriptionApi(self.api_client)

    # Export everything for easy imports
    __all__ = [
        "LeadLedgerProClient",
        "ApiClient",
        "Configuration",
        "AdminApi",
        "AuthApi",
        "ExportApi",
        "HealthApi",
        "MonitoringApi",
        "RootApi",
        "SubscriptionApi",
        "CancellationRequest",
        "ReactivationRequest",
        "ExportDataRequest",
        "HTTPValidationError",
        "ValidationError",
    ]

except ImportError as import_error:
    # Fallback if generated client is not available
    import_error_msg = str(import_error)

    class LeadLedgerProClient:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "Generated API client not available. "
                f"Import error: {import_error_msg}. "
                "Please run the OpenAPI client generation workflow."
            )

    __all__ = ["LeadLedgerProClient"]
