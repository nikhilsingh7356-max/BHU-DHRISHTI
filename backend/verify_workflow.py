"""Live guard checks for POST /api/v1/workflow/transition.

Exercises every code path that can be reached WITHOUT a database, so the safety
properties are verified even though no Supabase instance exists here:

  1. no token            -> 401
  2. wrong-secret token  -> 401
  3. valid FIELD_OFFICER -> 403  (role gate, mirrors projects_modify RLS)
  4. valid DISTRICT      -> 403  (same gate)
  5. valid CENTRAL, blank remarks -> 422 (validated before any DB access)
  6. valid CENTRAL, bad stage     -> 422 (validated before any DB access)
  7. valid CENTRAL, terminal stage-> 409 (validated before any DB access)
  8. valid CENTRAL, well-formed   -> 503 (passes validation, then DB is absent)

Ordering matters: a request that passes validation must NOT be able to reach the
write path without a configured database, and none of 1-7 may touch the database.
"""

import json
import os
import sys

import jwt
import requests

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000")
SECRET = os.getenv("JWT_SECRET", "TEST-ONLY-NOT-A-REAL-SECRET-1234567890")
URL = f"{BASE}/api/v1/workflow/transition"
WRONG = "A-COMPLETELY-DIFFERENT-SECRET-0000000000"

passed = failed = 0


def check(label, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"[PASS] {label}\n       -> {detail}")
    else:
        failed += 1
        print(f"[FAIL] {label}\n       -> {detail}")


def token(role="CENTRAL", secret=SECRET, expires_in=60):
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "officer_id": "CEN-001",
        "name": "Test Officer",
        "role": role,
        "exp": int(__import__("time").time()) + expires_in,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


BODY = {
    "project_code": "PRJ-2026-0417",
    "current_stage": "SEC_11_NOTIF",
    "action_remarks": "Gazette notification published in district press.",
    "actor_bhoomi_id": "BH-CEN-DL-001",
}


def call(tok=None, body=None):
    headers = {"Content-Type": "application/json"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    r = requests.post(URL, headers=headers, json=body or BODY, timeout=30)
    try:
        detail = json.dumps(r.json().get("detail", ""))
    except Exception:
        detail = r.text[:120]
    return r.status_code, detail


print("=== POST /api/v1/workflow/transition guard matrix ===\n")

code, detail = call(None)
check("no token rejected", code == 401, f"HTTP {code} -> {detail}")

code, detail = call(token(secret=WRONG))
check("token signed with wrong secret rejected", code == 401, f"HTTP {code} -> {detail}")

for role in ("FIELD_OFFICER", "DISTRICT"):
    code, detail = call(token(role=role))
    check(f"{role} cannot transition (projects_modify gate)", code == 403, f"HTTP {code} -> {detail}")

code, detail = call(token(), {**BODY, "action_remarks": "   "})
check("blank remarks rejected before DB access", code == 422, f"HTTP {code} -> {detail}")

code, detail = call(token(), {**BODY, "current_stage": "NOT_A_STAGE"})
check("unknown stage rejected before DB access", code == 422, f"HTTP {code} -> {detail}")

code, detail = call(token(), {**BODY, "current_stage": "COMPLETED"})
check("terminal stage rejected before DB access", code == 409, f"HTTP {code} -> {detail}")

code, detail = call(token())
check(
    "well-formed CENTRAL request passes validation, then fails closed on absent DB",
    code == 503,
    f"HTTP {code} -> {detail}",
)

print(f"\n=== {passed}/{passed + failed} checks passed ===")
sys.exit(1 if failed else 0)
