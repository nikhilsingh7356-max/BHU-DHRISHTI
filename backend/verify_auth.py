"""Verification harness for the JWT gate on protected routes.

Runs against a live backend. The point of each case is stated in the name: a
regression that silently accepts a bad token must fail here.

Interpretation of the status codes:
  401  -> the API rejected the credential  (auth gate working)
  503  -> the credential was ACCEPTED and the request proceeded to the database
          layer, which then reported "database not configured". Auth passing is
          therefore observable as 503 in this unconfigured environment.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import jwt

BASE = os.getenv("BASE_URL", "http://localhost:8000")
SECRET = os.getenv("JWT_SECRET", "TEST-ONLY-NOT-A-REAL-SECRET-1234567890")
ALG = "HS256"
PROTECTED = f"{BASE}/api/v1/parcels/geojson"

WRONG_SECRET = "A-COMPLETELY-DIFFERENT-SECRET-0000000000"


def get(path, token=None):
    req = urllib.request.Request(path, method="GET")
    if token is not None:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def mint(secret=SECRET, *, expires_in=60, role="CENTRAL", officer="CEN-001"):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "officer_id": officer,
        "role": role,
        "full_name": "Test Officer",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=ALG)


def report(name, status, body, want):
    detail = (body or "").replace("\n", " ")[:90]
    ok = status in want
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"       -> HTTP {status}  expected {'/'.join(str(w) for w in want)}")
    print(f"       -> {detail}")
    return ok


results = []

# A correctly signed, unexpired token must pass the auth gate. With no database
# configured the request then fails at the data layer (503), which is how we
# observe that authentication succeeded.
results.append(
    report(
        "valid token passes the auth gate (reaches DB layer)",
        *get(PROTECTED, mint()),
        want={503},
    )
)

# The core security property: a token signed with a different key must never be
# accepted, no matter how well-formed its claims are.
results.append(
    report(
        "token signed with the WRONG secret is rejected",
        *get(PROTECTED, mint(WRONG_SECRET)),
        want={401},
    )
)

results.append(
    report(
        "expired token is rejected",
        *get(PROTECTED, mint(expires_in=-30)),
        want={401},
    )
)

results.append(
    report("garbage token is rejected", *get(PROTECTED, "not-a-jwt"), want={401}))

# Privilege escalation check: claims are only trustworthy because they are
# signed. An unsigned/tampered token must not authenticate.
tampered = mint().rsplit(".", 1)[0] + ".AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
results.append(report("tampered signature is rejected", *get(PROTECTED, tampered), want={401}))

results.append(report("absent token is rejected", *get(PROTECTED), want={401}))

print()
print(f"{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
