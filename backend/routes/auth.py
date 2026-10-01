import logging
import os
import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from supabase import create_client

try:  # package-relative: `python -m backend.main` from the repo root
    from ..database import get_supabase
    from ..security import create_access_token
except ImportError:  # flat layout: `uvicorn main:app` from inside backend/
    from database import get_supabase
    from security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class OfficerVerifyRequest(BaseModel):
    officer_id: str


class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered official email address")
    password: str = Field(..., min_length=1)


class LoginValidator(BaseModel):
    """Request-model level email shape check (returns the normalised value)."""

    email: str

    def normalised(self) -> str:
        value = self.email.strip()
        if not _EMAIL_RE.match(value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Enter a valid email address.",
            )
        return value.lower()


@router.post("/verify-officer")
def verify_officer(data: OfficerVerifyRequest):
    """Pre-seeded registry check."""
    try:
        response = (
            get_supabase()
            .table("department_officer_registry")
            .select("officer_id, full_name, designation, assigned_role, is_active")
            .eq("officer_id", data.officer_id)
            .eq("is_active", True)
            .execute()
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Officer registry lookup failed")
        raise HTTPException(
            status_code=502,
            detail="Registry is currently unavailable. Please retry.",
        )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Officer ID not found in Department of Land Resources registry.",
        )

    officer = response.data[0]

    return {
        "status": "VERIFIED",
        "officer_id": officer["officer_id"],
        "full_name": officer["full_name"],
        "designation": officer["designation"],
        "assigned_role": officer["assigned_role"],
    }


@router.post("/login")
def login(data: LoginRequest):
    """Authenticate an officer and issue an API access token."""

    email = LoginValidator(email=data.email).normalised()

    # Service-role client used for application database queries.
    client = get_supabase()

    # IMPORTANT:
    # Use a separate Supabase client for authentication.
    # sign_in_with_password() changes the auth session on its client.
    # Keeping it separate prevents the service-role client from being
    # changed to the user's JWT session.
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured. Set SUPABASE_URL and SUPABASE_KEY.",
        )

    auth_client = create_client(
        supabase_url,
        supabase_key,
    )

    # ── Gate 1: credential verification ──────────────────────────────
    try:
        auth_response = auth_client.auth.sign_in_with_password(
            {
                "email": email,
                "password": data.password,
            }
        )
    except Exception:
        logger.info("Credential verification failed for %s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = getattr(auth_response, "user", None)
    user_id = getattr(user, "id", None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Gate 2: application profile ─────────────────────────────────
    try:
        profile_response = (
            client.table("profiles")
            .select("id, bhoomi_id, officer_id, role, state, district")
            .eq("id", user_id)
            .execute()
        )
    except Exception:
        logger.exception("Profile lookup failed for user %s", user_id)
        raise HTTPException(
            status_code=502,
            detail="Unable to load your officer profile. Please retry.",
        )

    if not profile_response.data or not profile_response.data[0].get("officer_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not linked to a departmental officer record.",
        )

    profile = profile_response.data[0]

    # Temporary debugging
    print("DEBUG PROFILE:", profile)

    officer_id = profile["officer_id"]

    # Temporary debugging
    print("DEBUG OFFICER_ID:", repr(officer_id))

    # ── Gate 3: officer registry ─────────────────────────────────────
    try:
        registry_response = (
            client.table("department_officer_registry")
            .select(
                "officer_id, full_name, designation, assigned_role, is_active"
            )
            .eq("officer_id", officer_id)
            .eq("is_active", True)
            .execute()
        )
    except Exception:
        logger.exception("Registry lookup failed for officer %s", officer_id)
        raise HTTPException(
            status_code=502,
            detail="Registry is currently unavailable. Please retry.",
        )

    # Temporary debugging
    print("DEBUG REGISTRY:", registry_response.data)

    if not registry_response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your officer record is inactive or missing. Contact the administrator.",
        )

    officer = registry_response.data[0]

    token = create_access_token(
        user_id=user_id,
        officer_id=officer["officer_id"],
        role=officer["assigned_role"],
        full_name=officer["full_name"],
        state=profile.get("state"),
        district=profile.get("district"),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "officer_id": officer["officer_id"],
            "bhoomi_id": profile.get("bhoomi_id"),
            "name": officer["full_name"],
            "designation": officer["designation"],
            "role": officer["assigned_role"],
            "state": profile.get("state"),
            "district": profile.get("district"),
        },
    }