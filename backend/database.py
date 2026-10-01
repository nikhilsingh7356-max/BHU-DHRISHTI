"""Shared Supabase access for the Bhu-Drishti API.

The client is created lazily rather than at import time. Building it eagerly
crashes the entire application whenever the environment variables are absent —
first local run, missing ``.env``, or a CI job without secrets — which turns a
configuration gap into a total outage instead of a clear 503 on the routes that
actually need the database.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import HTTPException

# load_dotenv() is a no-op when no .env file is present, so importing this module
# stays safe in environments that inject variables directly (systemd, Vercel).
load_dotenv()

DB_NOT_CONFIGURED_DETAIL = (
    "Database is not configured. Set SUPABASE_URL and SUPABASE_KEY."
)

_client = None


def get_supabase():
    """Return the process-wide Supabase client.

    Raises:
        HTTPException: 503 when the database is not configured.
    """
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise HTTPException(status_code=503, detail=DB_NOT_CONFIGURED_DETAIL)

        from supabase import create_client

        _client = create_client(url, key)
    return _client


def is_configured() -> bool:
    """True when both Supabase variables are present."""
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))
