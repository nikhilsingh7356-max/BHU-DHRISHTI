/**
 * BHU-DRISHTI API Service Layer
 *
 * Provides typed accessors for FastAPI endpoints.
 * Falls back to mock data when the backend is unreachable,
 * so the UI works fully offline during demo.
 *
 * Environment variables (Vite):
 *   VITE_API_BASE_URL   — FastAPI base URL (e.g. http://localhost:8000/api/v1)
 *   VITE_SUPABASE_URL   — Supabase project URL (for direct client if needed)
 *   VITE_SUPABASE_ANON_KEY — Supabase anonymous key (frontend-safe only)
 */

import { MOCK_PARCEL_GEOJSON } from '../data/parcelData.js';

// ── Configuration ────────────────────────────────────────────────────

const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL;
const REQUEST_TIMEOUT_MS = 15000; // 15 seconds

// Normalise the base URL and strip a trailing slash so `${API_BASE}${path}`
// never produces a double slash.
const API_BASE = String(RAW_API_BASE || '').trim().replace(/\/+$/, '');

// Surfacing this once is far better than silently serving mock data forever —
// otherwise a missing/misnamed env var looks like a working integration.
if (!API_BASE) {
  console.warn(
    '[API] VITE_API_BASE_URL is not set — all requests are served from mock data. ' +
      'Set it to your deployed backend (e.g. https://your-api.vercel.app/api/v1) to enable live data.'
  );
}

/**
 * True when no backend URL is configured, i.e. this is an explicitly offline
 * demo build. The UI uses it to label the sign-in form honestly instead of
 * implying that credentials are being checked.
 */
export function isDemoMode() {
  return !API_BASE;
}

// ── Data-source status ───────────────────────────────────────────────
//
// Every request silently degrades to mock data when the backend is missing or
// unreachable. Without a visible signal, a broken deployment is
// indistinguishable from a working one — which is exactly the failure mode
// that wastes the most time. This store records what the last request actually
// did so the UI can say so out loud.

let dataSource = API_BASE ? 'connecting' : 'unconfigured';
const dataSourceListeners = new Set();

function setDataSource(next) {
  if (next === dataSource) return;
  dataSource = next;
  dataSourceListeners.forEach((listener) => listener());
}

export function subscribeDataSource(listener) {
  dataSourceListeners.add(listener);
  return () => dataSourceListeners.delete(listener);
}

/**
 * Current data-source status. One of:
 *   'unconfigured' — no VITE_API_BASE_URL set; mock data by design
 *   'connecting'   — base URL set, no request has completed yet
 *   'live'         — the last request was served by the backend
 *   'degraded'     — the backend was configured but failed; mock data in use
 */
export function getDataSource() {
  return dataSource;
}

/**
 * Server snapshot for useSyncExternalStore. Returns the module's initial value
 * rather than the current one, so a server render is deterministic and cannot
 * disagree with the client's first render.
 */
export function getServerDataSource() {
  return API_BASE ? 'connecting' : 'unconfigured';
}

// ── Helpers ──────────────────────────────────────────────────────────

/**
 * Get stored auth token (set after login).
 * Returns null if not authenticated.
 */
function getAuthToken() {
  try {
    return localStorage.getItem('bhu_drishti_token');
  } catch {
    return null;
  }
}

/**
 * Set/clear auth token after login/logout.
 */
export function setAuthToken(token) {
  try {
    if (token) localStorage.setItem('bhu_drishti_token', token);
    else localStorage.removeItem('bhu_drishti_token');
  } catch { /* private browsing */ }
}

/**
 * Fetch wrapper with timeout, auth, and error handling.
 * Returns null when backend is unavailable → consumer falls back to mock data.
 */
async function apiFetch(path, options = {}) {
  if (!API_BASE) {
    setDataSource('unconfigured');
    return null; // No backend configured → null = use mock
  }

  const url = `${API_BASE}${path}`;
  const token = getAuthToken();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      // Discard error body — may contain sensitive server internals
      await res.text().catch(() => '');
      console.warn(`[API] ${path} → ${res.status}`);
      setDataSource('degraded');
      return null;
    }

    const data = await res.json();

    // Basic shape validation for GeoJSON
    if (path.includes('geojson') && data) {
      if (!data.type || !Array.isArray(data.features)) {
        console.warn(`[API] ${path} returned malformed GeoJSON — features array missing`);
        setDataSource('degraded');
        return null;
      }
    }

    setDataSource('live');
    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      console.warn(`[API] ${path} timed out after ${REQUEST_TIMEOUT_MS}ms`);
    } else {
      console.warn(`[API] ${path} failed:`, err.message);
    }
    setDataSource('degraded');
    return null;
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ── Strict fetch (authentication) ────────────────────────────────────
//
// `apiFetch` deliberately returns null on failure so read-only endpoints can
// degrade to demo data. That behaviour is unacceptable for authentication: a
// rejected password would be indistinguishable from an unreachable backend and
// would silently become a *successful* login. Auth therefore uses a separate
// strict path that throws, so "you were denied" and "the server is down" stay
// distinguishable and neither is ever reported as success.

export class ApiError extends Error {
  constructor(message, { status = 0, code = 'error' } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function apiFetchStrict(path, options = {}) {
  if (!API_BASE) {
    throw new ApiError('Backend is not configured.', { code: 'unconfigured' });
  }

  const url = `${API_BASE}${path}`;
  const token = getAuthToken();

  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(url, { ...options, headers, signal: controller.signal });

    if (!res.ok) {
      // FastAPI reports errors as {"detail": ...}; surface that text so the UI
      // can explain *why* sign-in failed instead of showing a generic error.
      let detail = `Request failed (${res.status})`;
      try {
        const body = await res.json();
        if (typeof body?.detail === 'string') {
          detail = body.detail;
        } else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
          detail = body.detail[0].msg;
        }
      } catch { /* non-JSON error body */ }
      throw new ApiError(detail, { status: res.status, code: 'rejected' });
    }

    setDataSource('live');
    return await res.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err.name === 'AbortError') {
      throw new ApiError('The server took too long to respond.', { code: 'timeout' });
    }
    throw new ApiError('Unable to reach the server.', { code: 'network' });
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Officer Verification ─────────────────────────────────────────────

const MOCK_OFFICERS = [
  { id: 1, name: 'Ananya Sharma', designation: 'IAS', role: 'CENTRAL', bhoomiId: 'AG-2026-001' },
  { id: 2, name: 'Deepak Verma', designation: 'IAS', role: 'STATE', bhoomiId: 'UP-2026-012' },
  { id: 3, name: 'Ritu Patel', designation: 'SDM', role: 'DISTRICT', bhoomiId: 'UP-2026-047' },
  { id: 4, name: 'Arun Singh', designation: 'Tehsildar', role: 'PROJECT', bhoomiId: 'UP-2026-103' },
  { id: 5, name: 'Sunita Devi', designation: 'Patwari', role: 'FIELD', bhoomiId: 'UP-2026-218' },
];

export async function verifyOfficer(officerId) {
  // Matches the FastAPI contract: POST /api/v1/auth/verify-officer
  const data = await apiFetch('/auth/verify-officer', {
    method: 'POST',
    body: JSON.stringify({ officer_id: officerId }),
  });
  if (data) return data;

  // Mock fallback
  await delay(300);
  return MOCK_OFFICERS.find((o) => o.bhoomiId === officerId) || null;
}

// ── Login ────────────────────────────────────────────────────────────

/**
 * Authenticate an officer.
 *
 * Two modes, and the difference matters:
 *
 *  - **Backend configured** — the credentials are checked by the real API. A
 *    rejected password throws and the caller must surface the error. It is
 *    never converted into a demo session, because that would let anyone walk
 *    into a "successful" login with any password at all.
 *  - **No backend configured** — `VITE_API_BASE_URL` is empty, so this is
 *    explicitly an offline demo build and a mock session is issued.
 *
 * The role is deliberately NOT sent. The API derives it from
 * `department_officer_registry`; accepting a client-supplied role would let the
 * browser choose its own privileges.
 *
 * @throws {ApiError} when the backend is configured and refuses the sign-in.
 */
export async function login(email, password) {
  try {
    const data = await apiFetchStrict('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (data?.access_token) setAuthToken(data.access_token);
    return data;
  } catch (err) {
    if (err.code === 'unconfigured') {
      return demoLogin(email);
    }
    setDataSource('degraded');
    throw err;
  }
}

/**
 * Offline demo session. Only reachable when no backend URL is configured.
 */
async function demoLogin(email) {
  await delay(600);
  const localPart = email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const officer =
    MOCK_OFFICERS.find((o) => o.name.toLowerCase().includes(localPart.toLowerCase())) ||
    MOCK_OFFICERS[1];

  const mockToken = `demo-${Date.now()}`;
  setAuthToken(mockToken);
  return {
    access_token: mockToken,
    token_type: 'bearer',
    demo: true,
    user: {
      officer_id: `DEMO-${officer.bhoomiId}`,
      name: officer.name,
      designation: officer.designation,
      role: officer.role,
      state: 'Uttar Pradesh',
      district: 'Sitapur',
    },
  };
}

export function logout() {
  setAuthToken(null);
}

/**
 * True when this browser already holds a session token.
 *
 * Only a hint for the UI: it says "we have something to send", not "the token
 * is valid". A stored token may be expired or revoked, which the API will
 * reject with 401 on the next request.
 */
export function hasStoredSession() {
  return Boolean(getAuthToken());
}

// ── Workflow Transitions ─────────────────────────────────────────────

const MOCK_WORKFLOW_HISTORY = [
  { stage: 1, status: 'COMPLETED', actor: 'Ritu Patel', date: '2026-06-15', remarks: 'SIA study initiated' },
  { stage: 2, status: 'COMPLETED', actor: 'Ritu Patel', date: '2026-07-21', remarks: 'Public hearing conducted' },
  { stage: 3, status: 'IN_PROGRESS', actor: 'Deepak Verma', date: '2026-07-28', remarks: 'Objections under review' },
];

export async function fetchWorkflowHistory(projectCode) {
  const data = await apiFetch(`/workflow/history/${projectCode}`);
  if (data) return data;

  await delay(200);
  return MOCK_WORKFLOW_HISTORY;
}

export async function transitionWorkflow(projectCode, targetStage, remarks, actorBhoomiId) {
  const data = await apiFetch('/workflow/transition', {
    method: 'POST',
    body: JSON.stringify({
      project_code: projectCode,
      target_stage: targetStage,
      remarks,
      actor_bhoomi_id: actorBhoomiId,
    }),
  });
  if (data) return data;

  // Mock transition
  await delay(500);
  return {
    success: true,
    transition: {
      from_stage: targetStage - 1,
      to_stage: targetStage,
      timestamp: new Date().toISOString(),
      actor: actorBhoomiId,
    },
    message: `Workflow transitioned to Stage ${targetStage}`,
  };
}

// ── Parcels GeoJSON ──────────────────────────────────────────────────

/**
 * Fetch parcels as GeoJSON FeatureCollection.
 *
 * Supports filtering by:
 *   - project_code (string)
 *   - status (parcel_status enum)
 *   - risk_level ('High', 'Medium', 'Low')
 *   - district (string)
 *   - state (string)
 *
 * Returns null on API error so the caller can fall back to mock data.
 */
export async function fetchParcelsGeoJSON({ projectCode, status, riskLevel, district, state } = {}) {
  const params = new URLSearchParams();
  if (projectCode) params.set('project_code', projectCode);
  if (status) params.set('status', status);
  if (riskLevel) params.set('risk_level', riskLevel);
  if (district) params.set('district', district);
  if (state) params.set('state', state);

  const qs = params.toString();
  const path = `/parcels/geojson${qs ? `?${qs}` : ''}`;

  const data = await apiFetch(path);
  if (data) return data;

  // Mock fallback — filter MOCK_PARCEL_GEOJSON client-side.
  // Imported statically: a dynamic import here duplicates the module in the
  // bundle (it's already statically imported by ParcelMap), so the dynamic
  // import buys nothing.
  await delay(200);

  let features = MOCK_PARCEL_GEOJSON.features;
  if (status) features = features.filter((f) => f.properties.status === status);
  if (riskLevel) features = features.filter((f) => f.properties.risk_level === riskLevel);
  if (district) features = features.filter((f) => f.properties.district === district);
  if (state) features = features.filter((f) => f.properties.state === state);

  return { type: 'FeatureCollection', features };
}

/**
 * Convenience alias for components that want a simple "give me parcels" call.
 * Supports the same filter object as fetchParcelsGeoJSON.
 */
export async function getParcels(filters) {
  return fetchParcelsGeoJSON(filters);
}

// ── Risk Evaluation ──────────────────────────────────────────────────

export async function evaluateRisk(ulpin) {
  const data = await apiFetch(`/risk/evaluate/${ulpin}`);
  if (data) return data;

  await delay(400);
  return {
    ulpin,
    total_risk_score: `${Math.floor(Math.random() * 100)}%`,
    risk_band: 'Medium',
    factors: [
      { label: 'Encumbrance density', weight: 30, pct: `${Math.floor(Math.random() * 30)}%` },
      { label: 'Heritage proximity', weight: 15, pct: `${Math.floor(Math.random() * 15)}%` },
      { label: 'Forest clearance', weight: 20, pct: `${Math.floor(Math.random() * 20)}%` },
      { label: 'Acquisition difficulty', weight: 20, pct: `${Math.floor(Math.random() * 20)}%` },
      { label: 'Compensation gap', weight: 15, pct: `${Math.floor(Math.random() * 15)}%` },
    ],
    next_best_actions: [
      'Verify pending documents with District Authority',
      'Escalate compensation backlog to State Authority',
      'Schedule field inspection for possession readiness',
    ],
    evaluated_at: new Date().toISOString(),
  };
}

// ── Bottleneck Detection ─────────────────────────────────────────────

const MOCK_BOTTLENECKS = [
  {
    id: 'BOT-001',
    parcelId: 'parcel-001',
    type: 'SLA_BREACH',
    severity: 'CRITICAL',
    stage: 'Hearing of Objections',
    stageCode: 'SEC_15_OBJECTION',
    project: 'PRJ-2026-UP0417',
    projectName: 'Kanpur-Lucknow Greenfield Expressway',
    ulpin: 'UP26016SIT1001',
    district: 'Sitapur',
    state: 'Uttar Pradesh',
    description: 'Objection hearing exceeded 60-day statutory SLA — 3 contested ancestral titles unresolved',
    daysInStage: 78,
    statutoryThreshold: 60,
    daysOverdue: 18,
    riskScore: 87,
    owner: 'Deepak Verma, IAS',
    ownerRole: 'District Collector',
    action: 'Escalate pending hearings to State Revenue Board',
    detectedAt: '2026-08-19T10:00:00Z',
  },
  {
    id: 'BOT-002',
    parcelId: 'parcel-006',
    type: 'STAKEHOLDER',
    severity: 'CRITICAL',
    stage: 'Declaration',
    stageCode: 'SEC_19_DECLARATION',
    project: 'PRJ-2026-UP0417',
    projectName: 'Kanpur-Lucknow Greenfield Expressway',
    ulpin: 'UP26016SIT1006',
    district: 'Sitapur',
    state: 'Uttar Pradesh',
    description: 'Gram Sabha consent documentation incomplete — 2 of 3 required attestations missing',
    daysInStage: 14,
    statutoryThreshold: 30,
    daysOverdue: 0,
    riskScore: 91,
    owner: 'Ritu Patel, SDM',
    ownerRole: 'District Collector',
    action: 'Initiate Gram Sabha re-consultation under Sec 4(5)',
    detectedAt: '2026-08-28T09:15:00Z',
  },
  {
    id: 'BOT-003',
    parcelId: 'parcel-002',
    type: 'DOCUMENTATION',
    severity: 'HIGH',
    stage: 'Award & Solatium',
    stageCode: 'SEC_23_AWARD',
    project: 'PRJ-2026-UP0417',
    projectName: 'Kanpur-Lucknow Greenfield Expressway',
    ulpin: 'UP26016SIT1002',
    district: 'Sitapur',
    state: 'Uttar Pradesh',
    description: 'Solatium calculation pending for commercial structure valuation',
    daysInStage: 45,
    statutoryThreshold: 90,
    daysOverdue: 0,
    riskScore: 54,
    owner: 'Arun Singh',
    ownerRole: 'Tehsildar',
    action: 'Submit valuation report to Land Acquisition Collector',
    detectedAt: '2026-08-30T14:30:00Z',
  },
  {
    id: 'BOT-004',
    parcelId: 'parcel-005',
    type: 'ENCUMBRANCE',
    severity: 'MEDIUM',
    stage: 'Possession',
    stageCode: 'SEC_38_POSSESSION',
    project: 'PRJ-2026-UP0417',
    projectName: 'Kanpur-Lucknow Greenfield Expressway',
    ulpin: 'UP26016SIT1005',
    district: 'Sitapur',
    state: 'Uttar Pradesh',
    description: 'Possession memo pending — farmer awaiting final compensation disbursement confirmation',
    daysInStage: 22,
    statutoryThreshold: 30,
    daysOverdue: 0,
    riskScore: 15,
    owner: 'Sunita Devi',
    ownerRole: 'Field Officer',
    action: 'Verify compensation transfer and issue possession certificate',
    detectedAt: '2026-08-31T08:00:00Z',
  },
  {
    id: 'BOT-005',
    parcelId: 'parcel-007',
    type: 'DOCUMENTATION',
    severity: 'MEDIUM',
    stage: 'R&R Progress',
    stageCode: 'RR_PROGRESS',
    project: 'PRJ-2026-UP0417',
    projectName: 'Kanpur-Lucknow Greenfield Expressway',
    ulpin: 'UP26016SIT1007',
    district: 'Sitapur',
    state: 'Uttar Pradesh',
    description: 'R&R allotment pending — housing plot allocation awaiting State R&R Authority approval',
    daysInStage: 35,
    statutoryThreshold: 180,
    daysOverdue: 0,
    riskScore: 22,
    owner: 'Arun Singh',
    ownerRole: 'Tehsildar',
    action: 'Follow up with State R&R Authority for plot allocation approval',
    detectedAt: '2026-08-29T11:00:00Z',
  },
];

export async function fetchBottlenecks(projectCode) {
  const path = projectCode
    ? `/bottlenecks?project_code=${projectCode}`
    : '/bottlenecks';
  const data = await apiFetch(path);
  if (data) return data;

  await delay(250);
  if (projectCode) {
    return MOCK_BOTTLENECKS.filter((b) =>
      b.project.toLowerCase().includes(projectCode.toLowerCase())
    );
  }
  return MOCK_BOTTLENECKS;
}

// ── Jurisdiction / Geography ─────────────────────────────────────────

const MOCK_JURISDICTIONS = [
  { code: 'NATIONAL', name: 'National', level: 0 },
  { code: 'UP', name: 'Uttar Pradesh', level: 1, parent: 'NATIONAL' },
  { code: 'PRAYAGRAJ', name: 'Prayagraj', level: 2, parent: 'UP' },
  { code: 'SITAPUR', name: 'Sitapur', level: 2, parent: 'UP' },
];

export async function fetchJurisdictions(parentCode) {
  const data = await apiFetch(
    parentCode ? `/jurisdictions?parent=${parentCode}` : '/jurisdictions'
  );
  if (data) return data;

  await delay(150);
  if (parentCode) {
    return MOCK_JURISDICTIONS.filter((j) => j.parent === parentCode);
  }
  return MOCK_JURISDICTIONS;
}
