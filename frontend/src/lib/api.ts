import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import {
  ApiResponse,
  ApiListResponse,
  PaginatedResponse,
  LoginResponse,
  User,
  Project,
  Parcel,
  ParcelOwner,
  Document,
  WorkflowState,
  Compensation,
  RRCase,
  Objection,
  Hearing,
  Notification,
  AuditLog,
  DashboardStats,
  GISVerification,
  Department,
  State,
  District,
  SLARule,
  JurisdictionRule,
  Role,
  Permission,
  HealthScore,
  DataConflict,
  Escalation,
  Possession,
  DependencyRecord,
  ResourcePriority,
  HistoricalAnalytic,
  IntegrationHealth,
  DataProvenance,
  WhatIfScenario,
  StatePerf,
  Bottleneck,
} from "./types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export function unwrapResult<T>(res: { data: ApiResponse<T> }): T {
  if (res.data.success) return res.data.data;
  throw new Error(res.data.message || "API Error");
}

export function unwrapList<T>(res: { data: ApiListResponse<T> }): PaginatedResponse<T> {
  const d = res.data;
  if (!d.success) throw new Error(String(d.message || "API Error"));
  const arr = Array.isArray(d.data) ? d.data : [];
  const total = d.total ?? arr.length;
  const page_size = d.page_size ?? (arr.length || 10);
  return {
    data: arr,
    total,
    page: d.page ?? 1,
    page_size,
    total_pages: d.total_pages ?? (page_size > 0 ? Math.ceil(total / page_size) : 1),
  };
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<ApiResponse<LoginResponse>>("/api/v1/auth/login", { email, password }),
  register: (data: { email: string; password: string; full_name: string; role_id?: number }) =>
    api.post<ApiResponse<LoginResponse>>("/api/v1/auth/register", data),
  refresh: (refresh_token: string) =>
    api.post<ApiResponse<{ access_token: string }>>("/api/v1/auth/refresh", { refresh_token }),
  me: () => api.get<ApiResponse<User>>("/api/v1/auth/me"),
};

export const projectApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<Project>>("/api/v1/projects/", { params }),
  get: (id: number) => api.get<ApiResponse<Project>>(`/api/v1/projects/${id}`),
  create: (data: Partial<Project>) => api.post<ApiResponse<Project>>("/api/v1/projects/", data),
  update: (id: number, data: Partial<Project>) => api.put<ApiResponse<Project>>(`/api/v1/projects/${id}`, data),
  submit: (id: number) => api.post<ApiResponse<Project>>(`/api/v1/projects/${id}/submit`),
  timeline: (id: number) =>
    api.get<ApiResponse<{ history: import("./types").StatusHistory[] }>>(`/api/v1/projects/${id}/timeline`),
  activity: (id: number) =>
    api.get<ApiResponse<{ activities: Record<string, unknown>[] }>>(`/api/v1/projects/${id}/activity`),
};

export const parcelApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<Parcel>>("/api/v1/parcels/", { params }),
  get: (id: number) => api.get<ApiResponse<Parcel>>(`/api/v1/parcels/${id}`),
  create: (data: Partial<Parcel>) => api.post<ApiResponse<Parcel>>("/api/v1/parcels/", data),
  update: (id: number, data: Partial<Parcel>) => api.put<ApiResponse<Parcel>>(`/api/v1/parcels/${id}`, data),
  addOwner: (id: number, data: Partial<ParcelOwner>) =>
    api.post<ApiResponse<ParcelOwner>>(`/api/v1/parcels/${id}/owners`, data),
};

export const documentApi = {
  listByProject: (projectId: number) =>
    api.get<ApiResponse<Document[]>>(`/api/v1/documents/project/${projectId}`),
  get: (id: number) => api.get<ApiResponse<Document>>(`/api/v1/documents/${id}`),
  upload: (formData: FormData) =>
    api.post<ApiResponse<Document>>("/api/v1/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  verify: (id: number, status: string, comment: string) =>
    api.put<ApiResponse<Document>>(`/api/v1/documents/${id}/verify`, { status, comment }),
};

export const workflowApi = {
  getProjectWorkflow: (projectId: number) =>
    api.get<ApiResponse<WorkflowState>>(`/api/v1/workflow/project/${projectId}`),
  transition: (projectId: number, new_status: string, comment: string, supporting_document_id?: number) =>
    api.post<ApiResponse<WorkflowState>>(`/api/v1/workflow/project/${projectId}/transition`, {
      new_status,
      comment,
      supporting_document_id,
    }),
  getTasks: (projectId: number) =>
    api.get<ApiResponse<import("./types").WorkflowTask[]>>(`/api/v1/workflow/project/${projectId}/tasks`),
};

export const jurisdictionApi = {
  suggest: (projectId: number) =>
    api.post<ApiResponse<import("./types").JurisdictionState>>(`/api/v1/jurisdiction/suggest/${projectId}`),
  confirm: (decisionId: number, comment: string) =>
    api.post<ApiResponse<import("./types").JurisdictionState>>(`/api/v1/jurisdiction/confirm/${decisionId}`, { comment }),
  getRules: () =>
    api.get<ApiResponse<JurisdictionRule[]>>("/api/v1/jurisdiction/rules"),
};

export const gisApi = {
  verify: (projectId: number, parcelId: number) =>
    api.post<ApiResponse<GISVerification>>(`/api/v1/gis/verify/${projectId}/${parcelId}`),
  getVerifications: (projectId: number) =>
    api.get<ApiResponse<GISVerification[]>>(`/api/v1/gis/project/${projectId}/verifications`),
};

export const compensationApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<Compensation>>("/api/v1/compensation/", { params }),
  get: (id: number) => api.get<ApiResponse<Compensation>>(`/api/v1/compensation/${id}`),
  create: (data: Partial<Compensation>) => api.post<ApiResponse<Compensation>>("/api/v1/compensation/", data),
  update: (id: number, data: Partial<Compensation>) =>
    api.put<ApiResponse<Compensation>>(`/api/v1/compensation/${id}`, data),
  approve: (id: number) => api.post<ApiResponse<Compensation>>(`/api/v1/compensation/${id}/approve`),
  addPayment: (id: number, data: { amount: number; payment_method: string; payment_reference: string }) =>
    api.post<ApiResponse<unknown>>(`/api/v1/compensation/${id}/payments`, data),
};

export const rrApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<RRCase>>("/api/v1/rr/", { params }),
  get: (id: number) => api.get<ApiResponse<RRCase>>(`/api/v1/rr/${id}`),
  create: (data: Partial<RRCase>) => api.post<ApiResponse<RRCase>>("/api/v1/rr/", data),
  update: (id: number, data: Partial<RRCase>) => api.put<ApiResponse<RRCase>>(`/api/v1/rr/${id}`, data),
};

export const objectionApi = {
  listByProject: (projectId: number) =>
    api.get<ApiResponse<Objection[]>>(`/api/v1/objections/project/${projectId}`),
  create: (data: Partial<Objection>) => api.post<ApiResponse<Objection>>("/api/v1/objections/", data),
};

export const hearingApi = {
  listByObjection: (objectionId: number) =>
    api.get<ApiResponse<Hearing[]>>(`/api/v1/hearings/objection/${objectionId}`),
  create: (data: Partial<Hearing>) => api.post<ApiResponse<Hearing>>("/api/v1/hearings/", data),
};

export const notificationApi = {
  list: () => api.get<ApiResponse<Notification[]>>("/api/v1/notifications/"),
  markRead: (id: number) => api.put<ApiResponse<unknown>>(`/api/v1/notifications/${id}/read`),
  markAllRead: () => api.put<ApiResponse<unknown>>("/api/v1/notifications/read-all"),
};

export const auditApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<AuditLog>>("/api/v1/audit/", { params }),
  exportCsv: (params?: Record<string, string | number>) =>
    api.get("/api/v1/audit/export", { params, responseType: "blob" }),
};

export const reportsApi = {
  dashboardStats: () => api.get<ApiResponse<DashboardStats>>("/api/v1/reports/dashboard-stats"),
  projectSummary: (id: number) => api.get<ApiResponse<Record<string, unknown>>>(`/api/v1/reports/project/${id}/summary`),
  compensationSummary: () => api.get<ApiResponse<Record<string, unknown>>>("/api/v1/reports/compensation-summary"),
  slaSummary: () => api.get<ApiResponse<Record<string, unknown>>>("/api/v1/reports/sla-summary"),
};

export const adminApi = {
  listUsers: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<User>>("/api/v1/admin/users", { params }),
  createUser: (data: { email: string; password: string; full_name: string; role_id: number }) =>
    api.post<ApiResponse<User>>("/api/v1/admin/users", data),
  updateUser: (id: number, data: Partial<User>) =>
    api.put<ApiResponse<User>>(`/api/v1/admin/users/${id}`, data),
  listRoles: () => api.get<ApiResponse<Role[]>>("/api/v1/admin/roles"),
  listPermissions: () => api.get<ApiResponse<Permission[]>>("/api/v1/admin/permissions"),
  listDepartments: () => api.get<ApiResponse<Department[]>>("/api/v1/admin/departments"),
  createDepartment: (data: Partial<Department>) =>
    api.post<ApiResponse<Department>>("/api/v1/admin/departments", data),
  listStates: () => api.get<ApiResponse<State[]>>("/api/v1/admin/states"),
  listDistricts: (stateId?: number) =>
    api.get<ApiResponse<District[]>>("/api/v1/admin/districts", { params: stateId ? { state_id: stateId } : undefined }),
  listSLARules: () => api.get<ApiResponse<SLARule[]>>("/api/v1/admin/sla-rules"),
  createSLARule: (data: Partial<SLARule>) =>
    api.post<ApiResponse<SLARule>>("/api/v1/admin/sla-rules", data),
  listJurisdictionRules: () => api.get<ApiResponse<JurisdictionRule[]>>("/api/v1/admin/jurisdiction-rules"),
  createJurisdictionRule: (data: Partial<JurisdictionRule>) =>
    api.post<ApiResponse<JurisdictionRule>>("/api/v1/admin/jurisdiction-rules", data),
};

export const searchApi = {
  search: (params: { q: string; type?: string; page?: number; page_size?: number }) =>
    api.get<ApiListResponse<Record<string, unknown>>>("/api/v1/search/", { params }),
};

export const healthApi = {
  check: () => api.get<ApiResponse<{ status: string; database: string }>>("/api/v1/health/"),
};

export const intelligenceApi = {
  projectHealth: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<HealthScore>>("/api/v1/intelligence/health/projects", { params }),
  parcelHealth: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<HealthScore>>("/api/v1/intelligence/health/parcels", { params }),
  conflicts: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<DataConflict>>("/api/v1/intelligence/conflicts", { params }),
  conflict: (id: string) => api.get<ApiResponse<DataConflict>>(`/api/v1/intelligence/conflicts/${id}`),
  escalations: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<Escalation>>("/api/v1/intelligence/escalations", { params }),
  possessions: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<Possession>>("/api/v1/intelligence/possessions", { params }),
  dependencies: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<DependencyRecord>>("/api/v1/intelligence/dependencies", { params }),
  priorities: () => api.get<ApiListResponse<ResourcePriority>>("/api/v1/intelligence/priorities"),
};

export const analyticsApi = {
  historical: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<HistoricalAnalytic>>("/api/v1/analytics/historical", { params }),
  statePerformance: () => api.get<ApiListResponse<StatePerf>>("/api/v1/analytics/historical/states"),
  bottlenecks: () => api.get<ApiListResponse<Bottleneck>>("/api/v1/analytics/historical/bottlenecks"),
  integrations: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<IntegrationHealth>>("/api/v1/analytics/integrations", { params }),
  provenance: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<DataProvenance>>("/api/v1/analytics/provenance", { params }),
  whatif: (params?: Record<string, string | number>) =>
    api.get<ApiListResponse<WhatIfScenario>>("/api/v1/analytics/whatif", { params }),
};

export default api;
