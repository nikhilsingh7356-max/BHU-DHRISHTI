# 🌍 BHU-DRISHTI

> **National Land Acquisition Control Tower** — A GIS-powered workflow management platform for monitoring land acquisition projects under the RFCTLARR Act.
>
> **Problem Statement:** PS 26016 (Ministry of Rural Development / DoLR)

---

## 📋 Table of Contents

- [About](#about)
- [Team](#team)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the App](#running-the-app)
- [Project Structure](#project-structure)
  - [Request path](#request-path)
- [Deployment](#deployment)
  - [Frontend  Vercel](#frontend--vercel)
  - [Checking which data you are seeing](#checking-which-data-you-are-seeing)
  - [Backend  Vercel (optional)](#backend--vercel-optional)
- [Development](#development)
  - [Available Scripts](#available-scripts)
  - [Performance measurement](#performance-measurement)
- [API Overview](#api-overview)
  - [Contracted endpoints - actual status](#contracted-endpoints---actual-status)
  - [Verifying the backend](#verifying-the-backend)
- [Contributing](#contributing)
- [License](#license)

---

## About

BHU-DRISHTI is a full-stack application that combines geographic information system (GIS) capabilities with the statutory workflow engine for land acquisition under the RFCTLARR Act. It enables government officers to:

- 🗺️ Visualize and track land parcels on interactive PostGIS-backed maps
- ⚙️ Manage the RFCTLARR statutory workflow (SIA study → Sec 11 → Sec 15 → Sec 19 → Sec 23 → Sec 38 → completion — seven stages)
- ⏱️ Monitor SLA deadlines and identify bottlenecks in real time
- 🔒 Verify officer identities and enforce role-based jurisdiction access
- 📄 Maintain a tamper-proof audit trail of all actions

---

## Team

| Name | Role | GitHub |
|------|------|--------|
| **Mukesh** | Database Architecture & Schema (Supabase / PostGIS) | [@themukeshdev](https://github.com/themukeshdev) |
| **Nikhil** | Backend — Officer Verification API | [@nikhilsingh7356-max](https://github.com/nikhilsingh7356-max) |
| **Deepak** | Backend — RFCTLARR Workflow State Machine | [@deepak-bca22](https://github.com/deepak-bca22) |
| **Alok** | Frontend — UI & Design System (React + Vite + Tailwind) | [@Alok9928](https://github.com/Alok9928) |
| **Aryan** | Team Member | [@tech-with-aryan](https://github.com/tech-with-aryan) |

> 📌 See [docs/sprints/day-1.md](docs/sprints/day-1.md) for detailed Day 1 task assignments and deliverables.

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  Frontend — React 19 + Vite + Tailwind                         │
│  TopBar · LevelNav · LoginModal · WorkflowTracker              │
│  WorkflowEngine · BottleneckAlerts · ParcelMapSection           │
│                        │                                      │
│                 ParcelMap (Leaflet, lazy chunk)                 │
└────────────────────────┬──────────────────────────────────────┘
                         │  HTTP/REST · Bearer JWT
                         ▼
┌───────────────────────────────────────────────────────────────┐
│  Backend — FastAPI / Uvicorn (port 8000)                        │
│                                                               │
│  CORS allowlist · security.py (JWT verify, RBAC)                │
│                                                               │
│   routes/auth.py      verify-officer · login                    │
│   routes/parcels.py   GET  geojson        [auth required]       │
│   routes/workflow.py  POST transition     [CENTRAL | STATE]     │
└────────────────────────┬──────────────────────────────────────┘
                         │  Supabase REST / PostgREST RPC
                         │  ⚠ service_role key BYPASSES RLS
                         ▼
┌───────────────────────────────────────────────────────────────┐
│  Database — Supabase (PostgreSQL + PostGIS)                     │
│  department_officer_registry · profiles                         │
│  projects · land_parcels (geometry Polygon 4326)                │
│  audit_logs            — RLS enabled on all five               │
└───────────────────────────────────────────────────────────────┘
```

**Flow:** React SPA → FastAPI routers → Supabase / PostGIS.

### Why the API re-implements authorisation

The backend talks to PostgREST with Supabase's `service_role` key, and
`service_role` **bypasses Row Level Security**. RLS alone therefore offers no
protection for an endpoint reached through this API. Each protected route
re-applies its own predicate:

| Route | Predicate enforced in code |
|---|---|
| `GET /api/v1/parcels/geojson` | `role = 'CENTRAL'` OR `created_by = caller` |
| `POST /api/v1/workflow/transition` | role must be `CENTRAL` or `STATE` (mirrors `projects_modify`) |

These predicates are load-bearing. Removing them would expose every land record
to any authenticated officer.

### Statutory stages

`public.project_stage` defines **seven** stages:

`SIA_STUDY → SEC_11_NOTIF → SEC_15_OBJECTION → SEC_19_DECLARATION → SEC_23_AWARD → SEC_38_POSSESSION → COMPLETED`

The transition endpoint enforces strictly-forward, one-step-at-a-time movement
using this declaration order as the source of truth. (Note: `docs/api-contracts.md`
illustrates a stage as *"Stage 4 of 8"*, which does not match the seven-value
enum — the enum wins.)


---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React + Vite | Client-side application (Port 5173) |
| **Styling** | Tailwind CSS | Utility-first CSS with Light Government Theme |
| **GIS Mapping** | Leaflet + react-leaflet | PostGIS-backed parcel map visualization |
| **Backend** | Python 3.11+ / FastAPI | REST API server (Port 8000) |
| **Database** | Supabase (PostgreSQL + PostGIS) | Spatial queries, auth, real-time |
| **Auth** | Supabase Auth + Officer Registry | Role-based access with officer verification |

---

## Getting Started

### Prerequisites

Ensure you have the following installed:

- **Python** 3.11 or higher
- **Node.js** 20 or higher (matches `engines.node` in `frontend/package.json`) and npm/yarn/pnpm
- **Supabase** account — create project at [supabase.com](https://supabase.com) and enable PostGIS
- **Git** — for version control

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-org/bhu-drishti.git
cd bhu-drishti
```

**2. Set up the backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Set up the frontend**
```bash
cd frontend
npm install
```

**4. Set up the environment**

```bash
# Backend — copy the template and fill in your own values
cd backend
cp .env.example .env        # On Windows: copy .env.example .env
```

```bash
# Frontend — leave VITE_API_BASE_URL empty to run in offline demo mode
cd ../frontend
cp .env.example .env        # On Windows: copy .env.example .env
```

Required and optional variables:

| Variable | Where | Required | Purpose |
| --- | --- | --- | --- |
| `SUPABASE_URL` | `backend/.env` | Yes | Supabase project URL |
| `SUPABASE_KEY` | `backend/.env` | Yes | **Service role** key. Required because PostGIS RPC needs it; the API re-applies RLS itself since `service_role` bypasses RLS |
| `JWT_SECRET` | `backend/.env` | **Yes** | Signs the JWTs issued by `POST /api/v1/auth/login`. There is deliberately no default: if unset, login is refused and protected routes return 503, so a deployment can never silently run on a well-known key. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ACCESS_TOKEN_TTL_MINUTES` | `backend/.env` | No | Access-token lifetime. Defaults to `60` |
| `CORS_ORIGINS` | `backend/.env` | Yes in deployment | Comma-separated allowed origins. Must be explicit — a wildcard cannot be combined with credentials. Include **both** `http://localhost:5173` and `http://localhost:4173` locally, since production auditing uses the preview port |
| `VITE_API_BASE_URL` | `frontend/.env` | No | Base URL of the API, e.g. `http://localhost:8000/api/v1`. **Leave empty for offline demo mode**, where the app uses bundled fixture data and a mock session. When it is set, credentials are verified by the real backend and a rejected password never becomes a successful demo login |

Never commit a filled-in `.env`. No credential belongs in this repository, in a commit, or in a chat message.

**5. Set up the database**

Run these in order in the Supabase SQL editor (or `psql`):

1. `database/01scheme.sql` — schemas, enums, tables, RLS policies
2. `database/02mockdata.sql` — seed officers, projects and sample parcels
3. `database/03parcels_geojson.sql` — **required** for `GET /api/v1/parcels/geojson`

> **Step 3 has not been executed in the environment used to verify this build.**
> That environment has no `psql`, no PostgreSQL runtime, no Docker, and no
> `SUPABASE_URL` / `SUPABASE_KEY`. PostGIS geometry output, live Supabase
> authentication, the workflow transition write path, and real parcel data are
> therefore all **unverified**. Script 3 only *adds* a function — it does not
> drop, truncate or update any table, so it is safe to run against a database
> that already holds live records, and re-running it is a no-op.

> `database/02mockdata.sql` inserts rows into `auth.users` with the literal
> placeholder `crypt_placeholder`. **This is not a working Supabase password**
> and those rows are not proof that sign-in works. Create real accounts through
> Supabase Auth (dashboard or admin API) before attempting a live login.

### Running the App

**Start the backend (API server)**

Run this from inside `backend/` — the app is `main`, not `app.main`:
```bash
cd backend
uvicorn main:app --reload --port 8000
# Swagger docs: http://localhost:8000/docs
```

**Start the frontend (development server)**
```bash
cd frontend
npm run dev
# App: http://localhost:5173
```

The app will be available at:
- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **Supabase Dashboard:** Your Supabase project URL

---

## Project Structure

```
bhu-drishti/
├── backend/                        # Python / FastAPI
│   ├── main.py                     # app, router registration, CORS, /health
│   ├── database.py                 # lazy Supabase client (fails closed if unconfigured)
│   ├── security.py                 # JWT issue/verify, require_auth, require_roles
│   ├── routes/
│   │   ├── auth.py                 # POST /auth/verify-officer, POST /auth/login
│   │   ├── parcels.py              # GET  /parcels/geojson   (auth required)
│   │   └── workflow.py             # POST /workflow/transition (CENTRAL|STATE)
│   ├── verify_auth.py              # JWT guard harness   -> 6/6
│   ├── verify_workflow.py          # workflow guards     -> 8/8
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                       # JavaScript / JSX (no TypeScript)
│   ├── public/
│   │   ├── robots.txt              # restrictive crawler policy
│   │   └── llms.txt
│   └── src/
│       ├── App.jsx                 # app shell, session, jurisdiction scoping
│       ├── main.jsx
│       ├── index.css               # z-index scale, Leaflet sizing
│       ├── lib/api.js              # API client, strict auth, mock fallback
│       ├── data/                   # mockData.js, parcelData.js, workflowData.js
│       └── components/
│           ├── alerts/BottleneckAlerts.jsx
│           ├── auth/LoginModal.jsx
│           ├── common/DataSourceBadge.jsx, ParcelSummary.jsx
│           ├── layout/TopBar.jsx
│           ├── map/ParcelMap.jsx, ParcelMapSection.jsx
│           ├── navigation/LevelNav.jsx
│           └── workflow/WorkflowEngine.jsx, WorkflowTracker.jsx
│
├── database/
│   ├── 01scheme.sql                # schemas, enums, tables, RLS
│   ├── 02mockdata.sql              # seed officers, projects, parcels
│   └── 03parcels_geojson.sql       # GeoJSON RPC — REQUIRED, run last
│
└── docs/
    ├── sprints/day-1.md            # Sprint planning
    ├── database-schme.md           # DB schema reference
    ├── api-contracts.md            # API endpoint contracts (5 endpoints)
    ├── architecture.md
    ├── ci-cd-guide.md
    ├── DOCUMENTATION_SETUP_GUIDE.md
    └── ui-guidelines.md            # UI/UX design standards
```

### Request path

```
React SPA  ──Bearer JWT──▶  FastAPI  ──service_role──▶  Supabase / PostGIS
```

The API holds Supabase's `service_role` key, which **bypasses Row Level Security**.
RLS alone therefore provides no protection: every protected route re-applies its
predicate in application code. Removing those predicates would expose all land
records, so they are load-bearing, not decorative.
```

---

## Deployment

### Frontend → Vercel

The repo-root `vercel.json` builds `frontend/` and serves `frontend/dist`, so
you can import the whole repository without configuring a root directory.

1. Push this repo to GitHub, then in Vercel choose **Add New → Project** and
   import it. Leave **Root Directory** empty and keep the detected framework
   settings (the `vercel.json` overrides them anyway).
2. Under **Settings → Environment Variables**, add:
   - `VITE_API_BASE_URL` — your backend base URL *including* the `/api/v1`
     prefix, e.g. `https://bhu-drishti-api.vercel.app/api/v1`.
   - `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (optional).
3. Deploy. Set the same variable on **Production**, **Preview** and
   **Development** if you want it to apply everywhere.

> **Important:** Vite inlines `VITE_*` variables at build time. After changing
> any `VITE_*` value you must redeploy for the new value to reach the browser.
>
> If `VITE_API_BASE_URL` is left unset the app still works — it falls back to
> the bundled mock data and logs a warning to the browser console.

### Checking which data you are seeing

Because the app degrades to bundled mock data whenever the backend is
unavailable, the top bar always reports the current mode so a misconfigured
deployment cannot be mistaken for working live data:

| Badge | Meaning | What to check |
|-------|---------|---------------|
| *(none)* | **Live** — the backend served the last request | — |
| `Connecting` | An API is configured; no response yet | Backend still cold-starting |
| `Demo data` | No `VITE_API_BASE_URL` set | Set the variable, then **redeploy** |
| `API unreachable` | Backend was configured but failed | The URL, the backend deployment, and its CORS allow-list |

Note that `API unreachable` still renders a usable map — the badge marks the
data as demo rather than blanking the screen.

### Backend → Vercel (optional)

Create a **separate** Vercel project for `backend/` with `backend/main.py` as the
entry point. Because `requirements.txt` is inside `backend/`, set **Root
Directory** to `backend`, or point the install/build commands at it explicitly.

Set these environment variables on that project:

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` | **Required.** Signing key for issued access tokens. No default exists — if unset, login is refused and protected routes return 503 |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase **service role** key (server-side only) |
| `ACCESS_TOKEN_TTL_MINUTES` | Optional. Access-token lifetime, default `60` |
| `CORS_ORIGINS` | Comma-separated list of allowed browser origins, including your frontend URL |

Generate a signing key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set it through your host's environment-variable settings. Do not commit it.

Use a real allow-list for `CORS_ORIGINS`. A wildcard origin cannot be combined
with credentialed requests — browsers reject that combination, so a wildcard
means authenticated calls fail.

---

## Development

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code |
| `feature/<ticket>-<slug>` | New features |
| `fix/<ticket>-<slug>` | Bug fixes |
| `docs/<topic>` | Documentation changes |

### Available Scripts

**Backend:**
```bash
# Run the API with auto-reload
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview the production build locally
npm run preview

# Lint
npm run lint
```

**Backend verification harnesses** (run against a live `uvicorn` on port 8000):
```bash
cd backend
python verify_auth.py       # JWT gate          -> 6/6
python verify_workflow.py   # workflow guards   -> 8/8
```

> There is no `npm test` script or `pytest` suite — the project ships no test
> framework. The two scripts above are the automated coverage that exists. They
> use an obviously non-production signing secret and mint their own tokens;
> neither reads real credentials.

### Performance measurement

**Always audit the production build, never the dev server.**

```bash
npm run build
npm run preview        # serves the built app on http://localhost:4173
```

The Vite dev server (`http://localhost:5173`) is not a production
representation of the app. It serves unminified sources, the React *development*
build, and one HTTP request per module, which inflates the measured payload from
roughly **95 KiB gzip** to about **9.1 MiB**. Running Lighthouse against it also
reports a bogus "minify JavaScript" opportunity of several megabytes that does
not exist in the deployed bundle.

For reference, the current production split is:

| Chunk | Raw | Gzip | Loaded |
| --- | --- | --- | --- |
| `index.html` | 2.4 KiB | 1.1 KiB | initial |
| `index-*.js` | 300.6 KiB | 88.2 KiB | initial |
| `index-*.css` | 33.1 KiB | 6.6 KiB | initial |
| `ParcelMap-*.js` | 168.3 KiB | 49.2 KiB | deferred |
| `ParcelMap-*.css` | 14.8 KiB | 6.3 KiB | deferred |

Leaflet, React-Leaflet and their CSS are split into a separate chunk that loads
only when the map scrolls near the viewport, so the initial critical payload is
about **95 KiB gzip**.

A Lighthouse run against the production preview (`localhost:4173`) measured
**Performance 96 desktop / 85 mobile**, **Accessibility 100** on both, and
**CLS 0**. The LCP element is an OpenStreetMap raster tile, so the score varies
by a few points between runs depending on third-party tile latency. Re-run
Lighthouse yourself before quoting a number.

---

## API Overview

Full API documentation is available in [docs/api-contracts.md](docs/api-contracts.md).

Once the backend is running, interactive API docs are available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Contracted endpoints — actual status

The specification in [docs/api-contracts.md](docs/api-contracts.md) defines **five**
endpoints. Four are implemented; one is deliberately not.

| Method | Endpoint | Status |
|--------|----------|--------|
| `POST` | `/api/v1/auth/verify-officer` | Implemented — registry whitelist check |
| `POST` | `/api/v1/auth/login` | Implemented — Supabase Auth + registry + profile checks, issues a JWT |
| `GET` | `/api/v1/parcels/geojson` | Implemented — authenticated GeoJSON read model |
| `POST` | `/api/v1/workflow/transition` | Implemented — stage transition with audit log |
| `GET` | `/api/v1/risk/evaluate/{ulpin}` | **Not implemented — returns 404.** See below |

Supporting routes: `GET /` and `GET /health`.

#### Why the risk endpoint is 404

The contract specifies this endpoint as *"Computes XGBoost-SHAP feature
contributions"*. **The repository contains no XGBoost model and no SHAP
feature-generation implementation.** The endpoint is intentionally not
implemented because there is nothing to serve. Implementing a substitute scorer
would invent model behaviour and would not satisfy the documented contract.

This 404 is a known, accepted gap — not a completed implementation. Producing a
risk score without the contracted model would misrepresent the system's
capability on real land-acquisition records.

#### Frontend calls with no contracted backend endpoint

The frontend also requests these paths. **None of them appear in
`docs/api-contracts.md`**, and no backend implementation was invented for them,
so they currently return 404 and the app degrades to fixture data:

- `/api/v1/bottlenecks`
- `/api/v1/jurisdictions`
- `/api/v1/workflow/history/{projectCode}`

These need a written contract and a schema before they can be built honestly.
The other table in this file below is an aspirational CRUD sketch, not the
current API.

<details>
<summary>Unimplemented CRUD sketch from the original README (not built)</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create a new project |
| `GET` | `/api/projects/{id}` | Get project details |
| `PUT` | `/api/projects/{id}` | Update a project |
| `DELETE` | `/api/projects/{id}` | Delete a project |
| `GET` | `/api/workflows` | List workflows |
| `POST` | `/api/workflows` | Create a workflow |
| `POST` | `/api/layers/upload` | Upload spatial data layer |

</details>

### Verifying the backend

Two harnesses run against a live `uvicorn` on port 8000:

```bash
cd backend
# JWT gate: valid token reaches the DB layer; wrong secret, expired, garbage,
# tampered and absent tokens are all rejected.          -> 6/6
python verify_auth.py
# Workflow transition guards, all reachable without a database.
#                                                       -> 8/8
python verify_workflow.py
```

Both use an obviously non-production signing secret and mint their own tokens;
neither reads real credentials.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contribution guidelines including:

- Branch naming conventions
- Commit message format
- PR review process
- Code style requirements

---

## Sprint Docs

| Sprint | Status | Link |
|--------|--------|------|
| Day 1 — Architecture & Base Setup | 🟢 Active | [day-1.md](docs/sprints/day-1.md) |

---

## License

*License TBD — add once decided.*

---

<p align="center">
  <sub>Built with 💚 by the BHU-DRISHTI team — Ministry of Rural Development / DoLR</sub>
</p>
