"""API authentication and role-based access control.

Authorization is enforced **here, on the backend**. The frontend hides controls
for roles that cannot use them, but that is presentation only: a caller can
forge any request with curl unless the API independently rejects it. Every
protected route in this application must therefore depend on :func:`require_auth`
(and usually :func:`require_roles`) rather than trusting the client.

Design notes
------------
* The signing secret is read from ``JWT_SECRET``. There is deliberately **no
  fallback default**. A hardcoded fallback is worse than no auth at all: it
  looks configured, it is committed to git, and anyone reading the repository
  can mint a valid token for any role. When the secret is absent this module
  raises 503 and refuses to issue or accept tokens.
* Tokens are issued by this API rather than forwarded from Supabase Auth so the
  browser never has to handle a long-lived provider credential.
* Supabase's ``service_role`` key bypasses Row Level Security. That makes the
  API layer the enforcement point for authorisation, which is exactly what the
  dependency below provides.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"

# Keep sessions short. This is an administrative system handling land records,
# so a leaked token should stop working quickly.
ACCESS_TOKEN_TTL_MINUTES = int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "60"))

# If the bearer token is missing entirely the client is unauthenticated (401).
# If it is present but unusable the credential is invalid (401 as well, but with a
# different message so the cause is obvious in logs).
_bearer = HTTPBearer(auto_error=False)

JWT_SECRET_NOT_SET = (
    "API authentication is not configured. Set JWT_SECRET on the server."
)


def get_jwt_secret() -> str:
    """Return the signing secret, or raise 503 if it is not configured.

    The value is stripped before use. Shell assignment is a classic source of
    invisible trailing characters -- `set JWT_SECRET=abc && cmd` on Windows keeps
    the space before `&&` as part of the value -- and an unstripped secret turns
    into a silent 401 on every single request with no useful diagnostic.
    """
    secret = (os.getenv("JWT_SECRET") or "").strip()
    if not secret:
        raise HTTPException(status_code=503, detail=JWT_SECRET_NOT_SET)
    return secret


def create_access_token(
    *,
    user_id: str,
    officer_id: str,
    role: str,
    full_name: str,
    state: str | None = None,
    district: str | None = None,
) -> str:
    """Issue a signed access token for a verified officer."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "officer_id": officer_id,
        "role": role,
        "full_name": full_name,
        "state": state,
        "district": district,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Validate a token's signature and expiry, or raise 401."""
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """FastAPI dependency: reject the request unless it carries a valid token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def require_roles(*allowed_roles: str):
    """Build a dependency that additionally enforces role membership.

    Usage::

        @router.get("/parcels/geojson", dependencies=[Depends(require_roles("CENTRAL"))])

    The token's ``role`` claim is the only input trusted here. It is signed by
    this server, so a client cannot escalate its own role.
    """

    def _dependency(principal: dict = Depends(require_auth)) -> dict:
        role = principal.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not permitted to perform this action.",
            )
        return principal

    return _dependency
