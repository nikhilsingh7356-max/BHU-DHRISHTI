# Bhu-Drishti — National Land Acquisition & Management System

> **Smart India Hackathon 2026 — Problem Statement PS 26016**
> A unified, GPS-verifiable, workflow-driven platform for the national land acquisition lifecycle.

Full-stack system: **FastAPI + async SQLAlchemy + PostgreSQL** (backend) and **Next.js 14** (frontend), covering the complete land acquisition process: project creation → submission → review → jurisdiction check → GIS verification → public hearing → compensation assessment → R&R planning → approval → execution.

---

## Tech Stack

| Layer    | Tech |
|----------|------|
| Backend  | Python 3.13, FastAPI, SQLAlchemy (async), Pydantic v2, Shapely |
| Database | PostgreSQL 16 (asyncpg) |
| Geospatial | GeoJSON stored as JSONB, spatial ops in Python/Shapely |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind, Recharts |
| Auth     | JWT (access + refresh), RBAC with roles & permissions |

---

## Quick Start

### 1. Prerequisites
- Node.js >= 18 (`node -v`)
- Python >= 3.10 (`python --version`)
- PostgreSQL 16 running locally

### 2. Database setup

Create the database and apply the schema (schema includes all tables, enums, roles, permissions, and role-permission mappings):

```bash
createdb -U postgres bhudrishti
psql -U postgres -d bhudrishti -f backend/migrations/001_initial_schema.sql
```

Set your DB credentials in `backend/.env` (see `.env.example`).

### 3. Backend

```bash
pip install -r backend/requirements.txt
cd backend
python -m scripts.seed_data    # loads roles, users, demo projects, parcels, jurisdiction/SLA rules, etc.
python run.py                  # serves on http://localhost:8000 (uvicorn, auto-reload)
```

Health check: `http://localhost:8000/api/v1/health`

### 4. Frontend

```bash
cd frontend
npm install
npm run dev                    # serves on http://localhost:3000
```

Backend API base URL is configurable in `frontend/src/lib/api.ts` (defaults to `http://localhost:8000`).

---

## Demo Accounts

All passwords follow the pattern `<Role>@123` for the matching account (e.g. `admin@bhudrishti.gov.in / Admin@123`).

| Role | Email / Password |
|------|------------------|
| Super Admin | `superadmin@bhudrishti.gov.in / Super@123` |
| Admin | `admin@bhudrishti.gov.in / Admin@123` |
| State Authority | `state@bhudrishti.gov.in / State@123` |
| District Collector | `district@bhudrishti.gov.in / District@123` |
| Land Acquisition Officer | `lao@bhudrishti.gov.in / Lao@123` |
| Project Sponsor | `sponsor@bhudrishti.gov.in / Sponsor@123` |
| GIS Officer | `gis@bhudrishti.gov.in / Gis@123` |
| Verification Officer | `verification@bhudrishti.gov.in / Verify@123` |
| Compensation Officer | `compensation@bhudrishti.gov.in / Comp@123` |
| R&R Officer | `rr@bhudrishti.gov.in / Rr@123` |
| Reviewer | `reviewer@bhudrishti.gov.in / Review@123` |
| Auditor | `auditor@bhudrishti.gov.in / Audit@123` |
| Viewer (read-only) | `viewer@bhudrishti.gov.in / Viewer@123` |

---

## Testing

Backend tests run against an isolated `bhudrishti_test` database:

```bash
cd backend
python -m pytest
```

Type-check / build the frontend:

```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## Architecture

```
frontend/  Next.js app (App Router) — pages, components, lib/api.ts, lib/auth.tsx
backend/
  app/
    main.py              FastAPI app, CORS, router wiring
    core/                config, security (JWT)
    db/                  async SQLAlchemy session
    models/              SQLAlchemy ORM models
    schemas/             Pydantic schemas
    api/v1/              Routers: auth, projects, parcels, documents, workflow,
                         verification, jurisdiction, gis, compensation, rr,
                         objections, hearings, sla, notifications, audit,
                         reports, admin, search, health
    services/            Business logic (jurisdiction engine, compensation calc, etc.)
    workflow/engine.py   Status transition state machine
  migrations/            SQL schema + seed
  scripts/seed_data.py   Demo data loader
  tests/                 pytest suite
```

The frontend is role-aware: the sidebar and enabled actions adapt to the logged-in user's role and permissions.

---

## Intended Architectural Deviations

These are deliberate, pragmatic choices (documented here so reviewers don't treat them as bugs):

1. **Workflow status vocabulary.** The workflow uses its own statuses
   (`DRAFT → SUBMITTED → UNDER_REVIEW → JURISDICTION_CHECK → GIS_VERIFICATION → PUBLIC_HEARING → COMPENSATION_ASSESSMENT → RR_PLANNING → APPROVED → IN_PROGRESS → COMPLETED`),
   not the spec's `project_status` enum. `projects.status` is `VARCHAR(50)`. The DB enum `project_status` exists but is unused. This is internally consistent and fully working.

2. **Geospatial storage.** PostGIS is **not** installed. Spatial data is stored as GeoJSON in JSONB columns, and spatial computations (point-in-polygon, distance, area) are done in Python/Shapely. If PostGIS becomes available, geometry columns can be added via `ALTER TABLE ... ADD COLUMN geom geometry(...)` without changing application logic.

3. **Permission vocabulary.** The `permissions` table contains names like `create_project`, `view_project`, `manage_users` (not dotted `projects.create` names from the schema draft). The auth endpoint returns the role object with its nested permissions; the frontend matches on these names.

4. **List API shape.** Paginated list endpoints return pagination fields at the **top level** of the response (`{ success, data: [...], total, page, page_size, total_pages }`), while a few endpoints (compensation, R&R) return a plain array in `data`. The frontend `unwrapList` helper normalizes both shapes.

---

## Repository Convenience

- Ports: backend `8000`, frontend `3000` (CORS allows `3000–3003`).
- Backend DSNs (sync + async) are in `backend/.env`.
- Demo data is fully transactional — re-running the seeder is safe.
