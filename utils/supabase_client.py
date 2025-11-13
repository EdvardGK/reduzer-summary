# -*- coding: utf-8 -*-
"""
Supabase client initialization and configuration
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

_supabase_client: Optional[Client] = None


def get_supabase() -> Optional[Client]:
    """
    Get or create Supabase client instance.

    Returns:
        Supabase client if configured, None otherwise

    Note:
        Returns None if SUPABASE_URL or SUPABASE_ANON_KEY not set.
        This allows the app to work without Supabase (session-only mode).
    """
    global _supabase_client

    # Return existing client if already initialized
    if _supabase_client is not None:
        return _supabase_client

    # Get configuration from environment
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    # Return None if not configured (graceful degradation)
    if not url or not key:
        return None

    # Initialize client
    try:
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        print(f"Warning: Could not initialize Supabase client: {e}")
        return None


def is_supabase_configured() -> bool:
    """
    Check if Supabase is properly configured.

    Returns:
        True if Supabase client can be initialized, False otherwise
    """
    return get_supabase() is not None


def reset_supabase_client():
    """
    Reset the Supabase client (useful for testing or config changes).
    """
    global _supabase_client
    _supabase_client = None
