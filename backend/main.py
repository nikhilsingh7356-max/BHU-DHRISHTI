import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:  # running from inside backend/: uvicorn main:app
    from routes.auth import router as auth_router
    from routes.parcels import router as parcels_router
    from routes.workflow import router as workflow_router
except ImportError:  # running as a package: python -m backend.main
    from .routes.auth import router as auth_router
    from .routes.parcels import router as parcels_router
    from .routes.workflow import router as workflow_router

app = FastAPI(
    title="Bhu-Drishti API",
    version="1.0.0",
)

# CORS: a wildcard origin cannot be combined with credentials — browsers reject
# that combination, so credentials are only enabled for an explicit allow-list.
#
# Both the dev server (5173) and the production preview server (4173) are listed:
# the README documents `npm run preview` as the way to verify a real build, and
# without 4173 here the previewed frontend is silently blocked by CORS and every
# request degrades to demo data for reasons that look like a backend outage.
DEFAULT_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:4173,http://127.0.0.1:4173"
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(parcels_router)
app.include_router(workflow_router)


@app.get("/")
def root():
    return {"message": "Bhu-Drishti API is running"}


@app.get("/health")
def health():
    """Liveness plus a real database reachability signal.

    Returning a flat `{"status": "ok"}` regardless of whether the database is
    reachable makes a broken deployment look healthy to any uptime monitor. The
    database probe is reported separately so the two can be distinguished.
    """
    payload = {"status": "ok", "database": "not_configured"}

    try:
        from database import get_supabase  # flat layout
    except ImportError:
        try:
            from .database import get_supabase  # package layout
        except ImportError:  # pragma: no cover - defensive
            return payload

    try:
        get_supabase().table("department_officer_registry").select("officer_id").limit(1).execute()
        payload["database"] = "reachable"
    except Exception:
        payload["database"] = "unreachable"

    return payload