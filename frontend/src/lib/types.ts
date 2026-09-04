export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  permissions: string[];
  department_id?: number;
  state_id?: number;
  district_id?: number;
}

export interface Role {
  id?: number;
  name: string;
  description?: string;
  permissions?: Permission[];
}

export interface Permission {
  id: number;
  name: string;
  resource: string;
  action: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface Project {
  id: number;
  project_code: string;
  name: string;
  description: string;
  project_type: string;
  purpose: string;
  public_category: string;
  sponsor_id: number;
  land_requiring_body_id: number;
  proposed_area_sq_m: number;
  state_id: number;
  district_id: number;
  start_date: string;
  target_completion_date: string;
  priority: string;
  estimated_cost: number;
  status: string;
  funding_source?: string;
  created_at: string;
  updated_at?: string;
  state_name?: string;
  district_name?: string;
  sponsor_name?: string;
  parcels?: Parcel[];
  documents?: Document[];
  status_history?: StatusHistory[];
  workflow?: WorkflowState;
  jurisdiction?: JurisdictionState;
  compensation?: Compensation[];
  rr_cases?: RRCase[];
  objections?: Objection[];
  gis_verifications?: GISVerification[];
}

export interface Parcel {
  id: number;
  survey_number: string;
  khasra_number: string;
  village_id: number;
  tehsil_id: number;
  district_id: number;
  state_id: number;
  land_type: string;
  ownership_type: string;
  area_sq_m: number;
  geometry?: Record<string, unknown>;
  current_status: string;
  village_name?: string;
  tehsil_name?: string;
  district_name?: string;
  state_name?: string;
  owners?: ParcelOwner[];
}

export interface ParcelOwner {
  id: number;
  parcel_id: number;
  owner_name: string;
  father_husband_name: string;
  gender: string;
  age: number;
  is_primary: boolean;
  contact_phone: string;
  address: string;
}

export interface Document {
  id: number;
  project_id: number;
  title: string;
  document_type: string;
  file_path: string;
  file_name: string;
  uploaded_by: number;
  verification_status: string;
  verified_by?: number;
  verification_comment?: string;
  created_at: string;
}

export interface WorkflowState {
  current_status: string;
  allowed_transitions: string[];
  history: WorkflowHistory[];
  tasks: WorkflowTask[];
}

export interface WorkflowHistory {
  id: number;
  from_status: string;
  to_status: string;
  comment: string;
  actor_name: string;
  created_at: string;
}

export interface WorkflowTask {
  id: number;
  task_type: string;
  status: string;
  assigned_to: string;
  due_date: string;
  description: string;
}

export interface StatusHistory {
  id: number;
  status: string;
  comment: string;
  actor_name: string;
  created_at: string;
}

export interface JurisdictionState {
  id: number;
  project_id: number;
  suggested_jurisdiction: string;
  comment: string;
  status: string;
}

export interface Compensation {
  id: number;
  parcel_id: number;
  landowner_id: number;
  assessed_value: number;
  land_area_sq_m: number;
  total_amount: number;
  compensation_components: Record<string, unknown>;
  status: string;
  parcel?: Parcel;
  landowner?: ParcelOwner;
  created_at: string;
}

export interface RRCase {
  id: number;
  project_id: number;
  parcel_id: number;
  landowner_id: number;
  case_type: string;
  status: string;
  description: string;
  rehabilitation_plan: string;
  created_at: string;
  parcel?: Parcel;
  landowner?: ParcelOwner;
}

export interface Objection {
  id: number;
  project_id: number;
  parcel_id: number;
  category: string;
  description: string;
  status: string;
  created_at: string;
}

export interface Hearing {
  id: number;
  objection_id: number;
  hearing_date: string;
  location: string;
  status: string;
  created_at: string;
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  is_read: boolean;
  notification_type: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  action: string;
  entity_type: string;
  entity_id: number;
  actor_id: number;
  actor_name?: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface DashboardStats {
  totals: {
    projects: number;
    active: number;
    pending_verification: number;
    gis_pending: number;
    sla_breaches: number;
    compensation_pending: number;
    rr_pending: number;
    completed: number;
    rejected: number;
  };
  charts: {
    by_state: ChartData[];
    by_status: ChartData[];
    monthly: ChartData[];
    sla: ChartData[];
    compensation: ChartData[];
    parcel_area: ChartData[];
  };
}

export interface ChartData {
  name: string;
  value: number;
  [key: string]: string | number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

export interface ApiListResponse<T> {
  success: boolean;
  data: T[];
  message: string;
  total?: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
}

export interface ApiError {
  success: false;
  error_code: string;
  message: string;
}

export interface GISVerification {
  id: number;
  project_id: number;
  parcel_id: number;
  status: string;
  verified_area_sq_m: number;
  discrepancy: number;
  verified_at: string;
}

export interface Department {
  id: number;
  name: string;
  description: string;
}

export interface State {
  id: number;
  name: string;
  code: string;
}

export interface District {
  id: number;
  name: string;
  state_id: number;
  code: string;
}

export interface SLARule {
  id: number;
  from_status: string;
  to_status: string;
  max_hours: number;
  priority_override?: string;
}

export interface JurisdictionRule {
  id: number;
  project_type: string;
  public_category: string;
  jurisdiction_level: string;
  description: string;
}

export interface HealthScore {
  id: string;
  project_id?: string;
  parcel_id?: string;
  project_code?: string;
  project_name?: string;
  project_status?: string;
  parcel_code?: string;
  parcel_status?: string;
  score: number;
  band: string;
  factors?: Record<string, unknown>;
  computed_at?: string;
}

export interface DataConflict {
  id: string;
  conflict_code: string;
  project_id: string;
  parcel_id?: string;
  source_a: string;
  source_b: string;
  field_name: string;
  old_value?: Record<string, unknown> | null;
  new_value?: Record<string, unknown> | null;
  severity: string;
  status: string;
  resolution_reason?: string;
  detected_at?: string;
  resolved_at?: string;
}

export interface Escalation {
  id: string;
  escalation_code: string;
  project_id: string;
  project_code?: string;
  project_name?: string;
  stage: string;
  trigger_reason: string;
  level: number;
  responsible_authority?: string;
  status: string;
  created_date?: string;
  resolution_date?: string;
  resolution_action?: string;
}

export interface Possession {
  id: string;
  project_id: string;
  project_code?: string;
  parcel_id: string;
  parcel_code?: string;
  award_reference?: string;
  possession_status: string;
  possession_date?: string;
  pending_reason?: string;
  verification_status?: string;
  responsible_authority?: string;
}

export interface DependencyRecord {
  id: string;
  project_id: string;
  project_code?: string;
  project_name?: string;
  from_stage: string;
  to_stage: string;
  dependency_type: string;
  dependency_description?: string;
  is_satisfied: boolean;
}

export interface ResourcePriority {
  id: string;
  project_id: string;
  project_code?: string;
  project_name?: string;
  project_status?: string;
  priority_score: number;
  priority_rank: number;
  reasoning?: string;
  update_date?: string;
}

export interface HistoricalAnalytic {
  id: string;
  period: string;
  entity_type: string;
  entity_name: string;
  metric_name: string;
  metric_value: number;
  is_demo: boolean;
}

export interface IntegrationHealth {
  id: string;
  system_name: string;
  system_code: string;
  integration_type?: string;
  last_sync?: string;
  status: string;
  records_synced: number;
  failed_records: number;
  conflicts: number;
  api_response_time_ms?: number;
  last_error?: string;
  is_demo: boolean;
}

export interface DataProvenance {
  id: string;
  entity_type: string;
  entity_id: string;
  source_system: string;
  source_record_id?: string;
  created_by_name?: string;
  last_updated?: string;
  verification_status?: string;
  last_synchronization?: string;
  is_demo: boolean;
}

export interface WhatIfScenario {
  id: string;
  scenario_code: string;
  project_id: string;
  project_code?: string;
  project_name?: string;
  title: string;
  description?: string;
  current_completion_label?: string;
  simulated_completion_label?: string;
  estimated_time_saved_days?: number;
  intervention?: string;
  assumptions?: string;
  is_demo: boolean;
}

export interface StatePerf {
  state: string;
  avg_performance: number;
}

export interface Bottleneck {
  district: string;
  bottleneck_count: number;
}
