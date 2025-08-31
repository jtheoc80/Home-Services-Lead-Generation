#!/usr/bin/env python3
"""
Supabase client module for Home Services Lead Generation.

This module provides a Supabase client instance configured with
the service role key for backend operations.
"""

import os
import logging
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Supabase client instance (global)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create a Supabase client instance using environment variables.

    This function creates a singleton Supabase client using the service role
    key for backend operations with elevated privileges.

    Returns:
        Client: Configured Supabase client instance

    Raises:
        ValueError: If required environment variables are not set
        Exception: If client creation fails
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is required")

    if not supabase_service_role:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")

    try:
        # Create Supabase client with service role key
        _supabase_client = create_client(supabase_url, supabase_service_role)
        logger.info("Supabase client initialized successfully")
        return _supabase_client

    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        raise Exception(f"Failed to initialize Supabase client: {e}")


def reset_client():
    """
    Reset the Supabase client instance.

    This is mainly used for testing purposes to clear the singleton.
    """
    global _supabase_client
    _supabase_client = None
