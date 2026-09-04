-- =============================================================================
-- Bhu-Drishti: National Land Acquisition & Management System
-- PostgreSQL 16 Initial Schema Migration
-- Version: 001
-- =============================================================================

-- Create the database if it does not exist
SELECT 'CREATE DATABASE bhudrishti' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'bhudrishti')\gexec

-- Connect to bhudrishti (run psql commands with: psql -U postgres -d bhudrishti)
\c bhudrishti

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- ENUM TYPES
-- =============================================================================

CREATE TYPE project_status AS ENUM (
    'DRAFT', 'SUBMITTED', 'UNDER_VERIFICATION', 'JURISDICTION_VERIFIED',
    'DOCUMENT_VERIFICATION', 'GIS_VERIFICATION', 'APPROVED_FOR_ACQUISITION',
    'ACQUISITION_IN_PROGRESS', 'AWARD_STAGE', 'COMPENSATION', 'R_AND_R',
    'POSSESSION', 'COMPLETED', 'RETURNED_FOR_CORRECTION', 'REJECTED',
    'ON_HOLD', 'CANCELLED'
);

CREATE TYPE parcel_status AS ENUM (
    'AVAILABLE', 'IDENTIFIED', 'UNDER_VERIFICATION', 'PROPOSED',
    'UNDER_ACQUISITION', 'ACQUIRED', 'POSSESSION_TAKEN', 'DISPUTED', 'REJECTED'
);

CREATE TYPE document_status AS ENUM (
    'UPLOADED', 'UNDER_REVIEW', 'VERIFIED', 'REJECTED', 'SUPERSEDED'
);

CREATE TYPE verification_status AS ENUM (
    'PENDING', 'APPROVED', 'REJECTED', 'CORRECTION_REQUESTED'
);

CREATE TYPE compensation_status AS ENUM (
    'ASSESSMENT_PENDING', 'UNDER_REVIEW', 'APPROVED', 'PAYMENT_PENDING',
    'PARTIALLY_PAID', 'PAID', 'DISPUTED'
);

CREATE TYPE rr_status AS ENUM (
    'IDENTIFIED', 'VERIFICATION', 'ELIGIBLE', 'PLAN_CREATED',
    'IN_PROGRESS', 'COMPLETED', 'DISPUTED'
);

CREATE TYPE objection_status AS ENUM (
    'SUBMITTED', 'UNDER_REVIEW', 'HEARING_SCHEDULED', 'DECIDED', 'CLOSED'
);

CREATE TYPE sla_status AS ENUM (
    'ON_TIME', 'DUE_SOON', 'BREACHED', 'COMPLETED'
);

CREATE TYPE notification_type AS ENUM (
    'WORKFLOW', 'SLA_WARNING', 'SLA_BREACH', 'APPROVAL', 'REJECTION',
    'DOCUMENT', 'COMPENSATION', 'RR', 'GENERAL'
);

CREATE TYPE action_type AS ENUM (
    'USER_LOGIN', 'USER_LOGOUT', 'PROJECT_CREATED', 'PROJECT_UPDATED',
    'PROJECT_STATUS_CHANGED', 'DOCUMENT_UPLOADED', 'DOCUMENT_VERIFIED',
    'DOCUMENT_REJECTED', 'PARCEL_ADDED', 'PARCEL_UPDATED', 'GIS_VERIFICATION',
    'WORKFLOW_TRANSITION', 'COMPENSATION_UPDATED', 'RR_UPDATED',
    'OBJECTION_SUBMITTED', 'HEARING_SCHEDULED', 'HEARING_DECIDED',
    'ROLE_CHANGED', 'SYSTEM_EVENT'
);

CREATE TYPE gender_type AS ENUM ('MALE', 'FEMALE', 'OTHER');

CREATE TYPE land_type AS ENUM (
    'RESIDENTIAL', 'AGRICULTURAL', 'COMMERCIAL', 'INDUSTRIAL',
    'FOREST', 'WASTELAND', 'GOVERNMENT', 'OTHER'
);

CREATE TYPE ownership_type AS ENUM (
    'PRIVATE', 'GOVERNMENT', 'COMMUNITY', 'INSTITUTIONAL', 'OTHER'
);

CREATE TYPE public_purpose_category AS ENUM (
    'NATIONAL_DEFENCE', 'PUBLIC_INFRASTRUCTURE', 'EDUCATIONAL', 'HEALTH',
    'HOUSING', 'ENVIRONMENTAL_CONSERVATION', 'URBAN_DEVELOPMENT',
    'RURAL_DEVELOPMENT', 'TRANSPORT', 'WATER_RESOURCES', 'ENERGY', 'OTHER'
);

CREATE TYPE priority_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

-- =============================================================================
-- 1. ROLES
-- =============================================================================

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 2. PERMISSIONS
-- =============================================================================

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    module VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 3. ROLE_PERMISSIONS
-- =============================================================================

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- =============================================================================
-- 4. DEPARTMENTS (hierarchical)
-- =============================================================================

CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE,
    parent_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    level VARCHAR(20),
    state_code VARCHAR(10),
    district_code VARCHAR(10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 5. STATES
-- =============================================================================

CREATE TABLE states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 6. DISTRICTS
-- =============================================================================

CREATE TABLE districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) NOT NULL,
    state_id UUID NOT NULL REFERENCES states(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(state_id, code)
);

-- =============================================================================
-- 7. TEHSILS
-- =============================================================================

CREATE TABLE tehsils (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(district_id, code)
);

-- =============================================================================
-- 8. VILLAGES
-- =============================================================================

CREATE TABLE villages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10),
    tehsil_id UUID NOT NULL REFERENCES tehsils(id) ON DELETE CASCADE,
    pin_code VARCHAR(10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tehsil_id, code)
);

-- =============================================================================
-- 9. PROFILES (users)
-- =============================================================================

CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    role_id UUID NOT NULL REFERENCES roles(id),
    department_id UUID REFERENCES departments(id),
    state_id UUID REFERENCES states(id),
    district_id UUID REFERENCES districts(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    avatar_url TEXT,
    last_login TIMESTAMPTZ,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 10. PROJECTS
-- =============================================================================

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(300) NOT NULL,
    description TEXT,
    project_type VARCHAR(50),
    purpose TEXT,
    public_category public_purpose_category,
    sponsor_id UUID REFERENCES profiles(id),
    land_requiring_body_id UUID REFERENCES departments(id),
    proposed_area_sq_m DECIMAL(15,2),
    state_id UUID REFERENCES states(id),
    district_id UUID REFERENCES districts(id),
    tehsil_id UUID REFERENCES tehsils(id),
    village_id UUID REFERENCES villages(id),
    start_date DATE,
    target_completion_date DATE,
    priority priority_level NOT NULL DEFAULT 'MEDIUM',
    estimated_cost DECIMAL(18,2),
    funding_source VARCHAR(200),
    status project_status NOT NULL DEFAULT 'DRAFT',
    created_by UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INT NOT NULL DEFAULT 1
);

-- =============================================================================
-- 11. PROJECT_STATUS_HISTORY
-- =============================================================================

CREATE TABLE project_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    previous_status project_status,
    new_status project_status NOT NULL,
    changed_by UUID NOT NULL REFERENCES profiles(id),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 12. PARCELS
-- =============================================================================

CREATE TABLE parcels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_code VARCHAR(20) UNIQUE,
    survey_number VARCHAR(50),
    khasra_number VARCHAR(50),
    ulpin VARCHAR(50),
    village_id UUID REFERENCES villages(id),
    tehsil_id UUID REFERENCES tehsils(id),
    district_id UUID REFERENCES districts(id),
    state_id UUID REFERENCES states(id),
    land_type land_type,
    ownership_type ownership_type,
    area_sq_m DECIMAL(15,2),
    geometry JSONB,
    current_status parcel_status NOT NULL DEFAULT 'IDENTIFIED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 13. PARCEL_OWNERS
-- =============================================================================

CREATE TABLE parcel_owners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id UUID NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    owner_name VARCHAR(200) NOT NULL,
    father_husband_name VARCHAR(200),
    gender gender_type,
    age INT,
    aadhaar_last4 VARCHAR(4),
    relation_to_holder VARCHAR(50),
    is_primary BOOLEAN NOT NULL DEFAULT true,
    contact_phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 14. PROJECT_PARCELS
-- =============================================================================

CREATE TABLE project_parcels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parcel_id UUID NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    acquired_area_sq_m DECIMAL(15,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, parcel_id)
);

-- =============================================================================
-- 15. PROJECT_DOCUMENTS
-- =============================================================================

CREATE TABLE project_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parcel_id UUID REFERENCES parcels(id) ON DELETE SET NULL,
    document_type VARCHAR(100) NOT NULL,
    title VARCHAR(300) NOT NULL,
    file_name VARCHAR(255),
    file_path TEXT,
    file_size BIGINT,
    mime_type VARCHAR(100),
    checksum VARCHAR(64),
    status document_status NOT NULL DEFAULT 'UPLOADED',
    uploaded_by UUID NOT NULL REFERENCES profiles(id),
    verified_by UUID REFERENCES profiles(id),
    verification_comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 16. DOCUMENT_VERSIONS
-- =============================================================================

CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES project_documents(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    file_path TEXT,
    file_name VARCHAR(255),
    file_size BIGINT,
    uploaded_by UUID NOT NULL REFERENCES profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 17. DOCUMENT_VERIFICATIONS
-- =============================================================================

CREATE TABLE document_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES project_documents(id) ON DELETE CASCADE,
    verifier_id UUID NOT NULL REFERENCES profiles(id),
    status verification_status NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 18. PROJECT_VERIFICATIONS
-- =============================================================================

CREATE TABLE project_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    verifier_id UUID NOT NULL REFERENCES profiles(id),
    verification_type VARCHAR(50) NOT NULL,
    status verification_status NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 19. JURISDICTION_RULES
-- =============================================================================

CREATE TABLE jurisdiction_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code VARCHAR(20) UNIQUE,
    rule_version VARCHAR(10) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    conditions JSONB NOT NULL,
    result JSONB NOT NULL,
    source_reference TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 20. JURISDICTION_DECISIONS
-- =============================================================================

CREATE TABLE jurisdiction_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    rule_id UUID REFERENCES jurisdiction_rules(id),
    suggested_appropriate_govt VARCHAR(200),
    suggested_acquiring_body VARCHAR(200),
    suggested_authority VARCHAR(200),
    confidence_score DECIMAL(3,2),
    reason TEXT,
    officer_verified BOOLEAN NOT NULL DEFAULT false,
    officer_id UUID REFERENCES profiles(id),
    officer_comment TEXT,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 21. WORKFLOW_INSTANCES
-- =============================================================================

CREATE TABLE workflow_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID UNIQUE NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    current_status project_status NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 22. WORKFLOW_TASKS
-- =============================================================================

CREATE TABLE workflow_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES profiles(id),
    assigned_role_id UUID REFERENCES roles(id),
    task_type VARCHAR(50) NOT NULL,
    title VARCHAR(300),
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    sla_deadline TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 23. WORKFLOW_TRANSITIONS
-- =============================================================================

CREATE TABLE workflow_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    task_id UUID REFERENCES workflow_tasks(id) ON DELETE SET NULL,
    from_status project_status,
    to_status project_status NOT NULL,
    actor_id UUID NOT NULL REFERENCES profiles(id),
    actor_role VARCHAR(50),
    comment TEXT,
    supporting_document_id UUID REFERENCES project_documents(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 24. NOTIFICATIONS
-- =============================================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    message TEXT NOT NULL,
    notification_type notification_type NOT NULL DEFAULT 'GENERAL',
    entity_type VARCHAR(50),
    entity_id UUID,
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 25. SLA_RULES
-- =============================================================================

CREATE TABLE sla_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_status project_status NOT NULL,
    to_status project_status,
    max_duration_hours INT NOT NULL,
    role_id UUID REFERENCES roles(id),
    priority priority_level,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 26. SLA_EVENTS
-- =============================================================================

CREATE TABLE sla_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_task_id UUID NOT NULL REFERENCES workflow_tasks(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES sla_rules(id),
    status sla_status NOT NULL DEFAULT 'ON_TIME',
    deadline TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    escalation_level INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 27. COMPENSATION_CASES
-- =============================================================================

CREATE TABLE compensation_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id UUID NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    landowner_id UUID NOT NULL REFERENCES parcel_owners(id) ON DELETE CASCADE,
    assessed_value DECIMAL(18,2),
    land_area_sq_m DECIMAL(15,2),
    compensation_components JSONB,
    total_amount DECIMAL(18,2),
    status compensation_status NOT NULL DEFAULT 'ASSESSMENT_PENDING',
    assigned_officer_id UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 28. COMPENSATION_PAYMENTS
-- =============================================================================

CREATE TABLE compensation_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES compensation_cases(id) ON DELETE CASCADE,
    amount DECIMAL(18,2) NOT NULL,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    payment_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    approved_by UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 29. RR_CASES (Rehabilitation & Resettlement)
-- =============================================================================

CREATE TABLE rr_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parcel_id UUID NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    landowner_id UUID NOT NULL REFERENCES parcel_owners(id) ON DELETE CASCADE,
    family_members_count INT,
    eligibility_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    entitlement_details JSONB,
    assistance_type VARCHAR(100),
    assigned_officer_id UUID REFERENCES profiles(id),
    status rr_status NOT NULL DEFAULT 'IDENTIFIED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 30. OBJECTIONS
-- =============================================================================

CREATE TABLE objections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objection_code VARCHAR(20) UNIQUE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parcel_id UUID REFERENCES parcels(id) ON DELETE SET NULL,
    landowner_id UUID REFERENCES parcel_owners(id) ON DELETE SET NULL,
    submission_date DATE NOT NULL DEFAULT CURRENT_DATE,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status objection_status NOT NULL DEFAULT 'SUBMITTED',
    created_by UUID NOT NULL REFERENCES profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 31. HEARINGS
-- =============================================================================

CREATE TABLE hearings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objection_id UUID NOT NULL REFERENCES objections(id) ON DELETE CASCADE,
    hearing_date TIMESTAMPTZ NOT NULL,
    hearing_officer_id UUID REFERENCES profiles(id),
    location VARCHAR(300),
    decision VARCHAR(50),
    decision_details TEXT,
    decision_date DATE,
    next_hearing_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 32. GIS_VERIFICATIONS
-- =============================================================================

CREATE TABLE gis_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parcel_id UUID NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    verified_by UUID NOT NULL REFERENCES profiles(id),
    geometry_valid BOOLEAN,
    area_match BOOLEAN,
    overlap_detected BOOLEAN,
    overlap_parcel_ids UUID[],
    outside_boundary BOOLEAN,
    conflict_details JSONB,
    verification_notes TEXT,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 33. AUDIT_LOGS
-- =============================================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES profiles(id),
    actor_email VARCHAR(255),
    action action_type NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    previous_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 34. PROJECT_ACTIVITY
-- =============================================================================

CREATE TABLE project_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL REFERENCES profiles(id),
    activity_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- profiles
CREATE INDEX idx_profiles_email ON profiles(email);
CREATE INDEX idx_profiles_role_id ON profiles(role_id);
CREATE INDEX idx_profiles_department_id ON profiles(department_id);
CREATE INDEX idx_profiles_state_id ON profiles(state_id);
CREATE INDEX idx_profiles_district_id ON profiles(district_id);

-- projects
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_sponsor_id ON projects(sponsor_id);
CREATE INDEX idx_projects_state_id ON projects(state_id);
CREATE INDEX idx_projects_district_id ON projects(district_id);
CREATE INDEX idx_projects_project_code ON projects(project_code);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_public_category ON projects(public_category);
CREATE INDEX idx_projects_priority ON projects(priority);

-- project_status_history
CREATE INDEX idx_project_status_history_project_id ON project_status_history(project_id);

-- parcels
CREATE INDEX idx_parcels_state_id ON parcels(state_id);
CREATE INDEX idx_parcels_district_id ON parcels(district_id);
CREATE INDEX idx_parcels_village_id ON parcels(village_id);
CREATE INDEX idx_parcels_current_status ON parcels(current_status);
CREATE INDEX idx_parcels_survey_number ON parcels(survey_number);
CREATE INDEX idx_parcels_ulpin ON parcels(ulpin);
CREATE INDEX idx_parcels_khasra_number ON parcels(khasra_number);

-- parcel_owners
CREATE INDEX idx_parcel_owners_parcel_id ON parcel_owners(parcel_id);

-- project_parcels
CREATE INDEX idx_project_parcels_project_id ON project_parcels(project_id);
CREATE INDEX idx_project_parcels_parcel_id ON project_parcels(parcel_id);

-- project_documents
CREATE INDEX idx_project_documents_project_id ON project_documents(project_id);
CREATE INDEX idx_project_documents_status ON project_documents(status);
CREATE INDEX idx_project_documents_document_type ON project_documents(document_type);
CREATE INDEX idx_project_documents_parcel_id ON project_documents(parcel_id);

-- document_versions
CREATE INDEX idx_document_versions_document_id ON document_versions(document_id);

-- document_verifications
CREATE INDEX idx_document_verifications_document_id ON document_verifications(document_id);

-- project_verifications
CREATE INDEX idx_project_verifications_project_id ON project_verifications(project_id);

-- jurisdiction_decisions
CREATE INDEX idx_jurisdiction_decisions_project_id ON jurisdiction_decisions(project_id);

-- workflow_tasks
CREATE INDEX idx_workflow_tasks_instance_id ON workflow_tasks(instance_id);
CREATE INDEX idx_workflow_tasks_assigned_to ON workflow_tasks(assigned_to);
CREATE INDEX idx_workflow_tasks_status ON workflow_tasks(status);
CREATE INDEX idx_workflow_tasks_sla_deadline ON workflow_tasks(sla_deadline);

-- workflow_transitions
CREATE INDEX idx_workflow_transitions_instance_id ON workflow_transitions(instance_id);
CREATE INDEX idx_workflow_transitions_actor_id ON workflow_transitions(actor_id);

-- notifications
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = false;

-- sla_events
CREATE INDEX idx_sla_events_status ON sla_events(status);
CREATE INDEX idx_sla_events_deadline ON sla_events(deadline);
CREATE INDEX idx_sla_events_workflow_task_id ON sla_events(workflow_task_id);
CREATE INDEX idx_sla_events_rule_id ON sla_events(rule_id);

-- compensation_cases
CREATE INDEX idx_compensation_cases_project_id ON compensation_cases(project_id);
CREATE INDEX idx_compensation_cases_status ON compensation_cases(status);
CREATE INDEX idx_compensation_cases_parcel_id ON compensation_cases(parcel_id);
CREATE INDEX idx_compensation_cases_landowner_id ON compensation_cases(landowner_id);

-- compensation_payments
CREATE INDEX idx_compensation_payments_case_id ON compensation_payments(case_id);

-- rr_cases
CREATE INDEX idx_rr_cases_project_id ON rr_cases(project_id);
CREATE INDEX idx_rr_cases_status ON rr_cases(status);
CREATE INDEX idx_rr_cases_parcel_id ON rr_cases(parcel_id);

-- objections
CREATE INDEX idx_objections_project_id ON objections(project_id);
CREATE INDEX idx_objections_status ON objections(status);

-- hearings
CREATE INDEX idx_hearings_objection_id ON hearings(objection_id);
CREATE INDEX idx_hearings_hearing_date ON hearings(hearing_date);

-- gis_verifications
CREATE INDEX idx_gis_verifications_project_id ON gis_verifications(project_id);
CREATE INDEX idx_gis_verifications_parcel_id ON gis_verifications(parcel_id);

-- audit_logs
CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX idx_audit_logs_entity_id ON audit_logs(entity_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_actor_entity ON audit_logs(actor_id, entity_type, entity_id);

-- project_activity
CREATE INDEX idx_project_activity_project_id ON project_activity(project_id);
CREATE INDEX idx_project_activity_actor_id ON project_activity(actor_id);
CREATE INDEX idx_project_activity_created_at ON project_activity(created_at);

-- departments
CREATE INDEX idx_departments_parent_id ON departments(parent_id);

-- jurisdiction_rules
CREATE INDEX idx_jurisdiction_rules_effective_from ON jurisdiction_rules(effective_from);
CREATE INDEX idx_jurisdiction_rules_is_active ON jurisdiction_rules(is_active);

-- sla_rules
CREATE INDEX idx_sla_rules_from_status ON sla_rules(from_status);

-- =============================================================================
-- SEED DATA: ROLES
-- =============================================================================

INSERT INTO roles (id, name, description) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'SUPER_ADMIN', 'System administrator with full access to all modules and settings'),
    ('a0000000-0000-0000-0000-000000000002', 'CENTRAL_AUTHORITY', 'Central government authority for oversight and approval of national-level projects'),
    ('a0000000-0000-0000-0000-000000000003', 'STATE_AUTHORITY', 'State-level authority responsible for state project oversight'),
    ('a0000000-0000-0000-0000-000000000004', 'DISTRICT_ADMIN', 'District-level administrator managing projects within the district'),
    ('a0000000-0000-0000-0000-000000000005', 'LAND_ACQUIRING_OFFICER', 'Officer responsible for land acquisition processes'),
    ('a0000000-0000-0000-0000-000000000006', 'PROJECT_SPONSOR', 'Entity sponsoring or proposing a project'),
    ('a0000000-0000-0000-0000-000000000007', 'SURVEYOR_GIS_OFFICER', 'Officer responsible for surveying, GIS mapping, and spatial verification'),
    ('a0000000-0000-0000-0000-000000000008', 'VERIFICATION_OFFICER', 'Officer responsible for document and project verification'),
    ('a0000000-0000-0000-0000-000000000009', 'COMPENSATION_OFFICER', 'Officer responsible for land compensation assessment and payment'),
    ('a0000000-0000-0000-0000-000000000010', 'RR_OFFICER', 'Officer responsible for Rehabilitation & Resettlement planning and execution'),
    ('a0000000-0000-0000-0000-000000000011', 'REVIEWER', 'Senior reviewer for final review and quality checks'),
    ('a0000000-0000-0000-0000-000000000012', 'AUDITOR', 'Auditor for compliance checks and audit trail review'),
    ('a0000000-0000-0000-0000-000000000013', 'VIEWER', 'Read-only access for monitoring and reporting');

-- =============================================================================
-- SEED DATA: PERMISSIONS
-- =============================================================================

INSERT INTO permissions (id, name, description, module) VALUES
    -- Projects
    ('b0000000-0000-0000-0000-000000000001', 'projects.create', 'Create new projects', 'projects'),
    ('b0000000-0000-0000-0000-000000000002', 'projects.read', 'View project details', 'projects'),
    ('b0000000-0000-0000-0000-000000000003', 'projects.update', 'Update project details', 'projects'),
    ('b0000000-0000-0000-0000-000000000004', 'projects.delete', 'Delete projects', 'projects'),
    ('b0000000-0000-0000-0000-000000000005', 'projects.submit', 'Submit projects for review', 'projects'),
    -- Parcels
    ('b0000000-0000-0000-0000-000000000006', 'parcels.create', 'Create new parcels', 'parcels'),
    ('b0000000-0000-0000-0000-000000000007', 'parcels.read', 'View parcel details', 'parcels'),
    ('b0000000-0000-0000-0000-000000000008', 'parcels.update', 'Update parcel details', 'parcels'),
    ('b0000000-0000-0000-0000-000000000009', 'parcels.delete', 'Delete parcels', 'parcels'),
    -- Documents
    ('b0000000-0000-0000-0000-000000000010', 'documents.upload', 'Upload documents', 'documents'),
    ('b0000000-0000-0000-0000-000000000011', 'documents.read', 'View documents', 'documents'),
    ('b0000000-0000-0000-0000-000000000012', 'documents.verify', 'Verify and approve documents', 'documents'),
    ('b0000000-0000-0000-0000-000000000013', 'documents.delete', 'Delete documents', 'documents'),
    -- Workflow
    ('b0000000-0000-0000-0000-000000000014', 'workflow.transition', 'Perform workflow transitions', 'workflow'),
    ('b0000000-0000-0000-0000-000000000015', 'workflow.assign', 'Assign workflow tasks', 'workflow'),
    ('b0000000-0000-0000-0000-000000000016', 'workflow.read', 'View workflow history', 'workflow'),
    -- Verification
    ('b0000000-0000-0000-0000-000000000017', 'verification.read', 'View verification records', 'verification'),
    ('b0000000-0000-0000-0000-000000000018', 'verification.verify', 'Perform verification actions', 'verification'),
    ('b0000000-0000-0000-0000-000000000019', 'verification.reject', 'Reject verification requests', 'verification'),
    -- Compensation
    ('b0000000-0000-0000-0000-000000000020', 'compensation.read', 'View compensation details', 'compensation'),
    ('b0000000-0000-0000-0000-000000000021', 'compensation.assess', 'Assess compensation amounts', 'compensation'),
    ('b0000000-0000-0000-0000-000000000022', 'compensation.approve', 'Approve compensation payments', 'compensation'),
    ('b0000000-0000-0000-0000-000000000023', 'compensation.process_payment', 'Process compensation payments', 'compensation'),
    -- Rehabilitation & Resettlement
    ('b0000000-0000-0000-0000-000000000024', 'rr.read', 'View R&R case details', 'rr'),
    ('b0000000-0000-0000-0000-000000000025', 'rr.assess', 'Assess R&R eligibility', 'rr'),
    ('b0000000-0000-0000-0000-000000000026', 'rr.plan', 'Create R&R plans', 'rr'),
    ('b0000000-0000-0000-0000-000000000027', 'rr.update', 'Update R&R cases', 'rr'),
    -- Jurisdiction
    ('b0000000-0000-0000-0000-000000000028', 'jurisdiction.read', 'View jurisdiction rules', 'jurisdiction'),
    ('b0000000-0000-0000-0000-000000000029', 'jurisdiction.suggest', 'Suggest jurisdiction decisions', 'jurisdiction'),
    ('b0000000-0000-0000-0000-000000000030', 'jurisdiction.confirm', 'Confirm jurisdiction decisions', 'jurisdiction'),
    -- GIS
    ('b0000000-0000-0000-0000-000000000031', 'gis.read', 'View GIS data', 'gis'),
    ('b0000000-0000-0000-0000-000000000032', 'gis.verify', 'Verify GIS data', 'gis'),
    ('b0000000-0000-0000-0000-000000000033', 'gis.upload_geometry', 'Upload geometry data', 'gis'),
    -- Audit
    ('b0000000-0000-0000-0000-000000000034', 'audit.read', 'View audit logs', 'audit'),
    ('b0000000-0000-0000-0000-000000000035', 'audit.export', 'Export audit logs', 'audit'),
    -- Notifications
    ('b0000000-0000-0000-0000-000000000036', 'notifications.read', 'View notifications', 'notifications'),
    ('b0000000-0000-0000-0000-000000000037', 'notifications.manage', 'Manage notification settings', 'notifications'),
    -- Admin
    ('b0000000-0000-0000-0000-000000000038', 'admin.users', 'Manage users', 'admin'),
    ('b0000000-0000-0000-0000-000000000039', 'admin.roles', 'Manage roles and permissions', 'admin'),
    ('b0000000-0000-0000-0000-000000000040', 'admin.departments', 'Manage departments', 'admin'),
    ('b0000000-0000-0000-0000-000000000041', 'admin.settings', 'Manage system settings', 'admin'),
    ('b0000000-0000-0000-0000-000000000042', 'admin.system', 'System-level administration', 'admin'),
    -- Reports
    ('b0000000-0000-0000-0000-000000000043', 'reports.read', 'View reports', 'reports'),
    ('b0000000-0000-0000-0000-000000000044', 'reports.export', 'Export reports', 'reports'),
    -- Objections
    ('b0000000-0000-0000-0000-000000000045', 'objections.read', 'View objections', 'objections'),
    ('b0000000-0000-0000-0000-000000000046', 'objections.create', 'File objections', 'objections'),
    ('b0000000-0000-0000-0000-000000000047', 'objections.review', 'Review and decide objections', 'objections'),
    -- Hearings
    ('b0000000-0000-0000-0000-000000000048', 'hearings.read', 'View hearing details', 'hearings'),
    ('b0000000-0000-0000-0000-000000000049', 'hearings.schedule', 'Schedule hearings', 'hearings'),
    ('b0000000-0000-0000-0000-000000000050', 'hearings.decide', 'Record hearing decisions', 'hearings');

-- =============================================================================
-- SEED DATA: ROLE_PERMISSIONS
-- =============================================================================

-- SUPER_ADMIN (a0000000-0000-0000-0000-000000000001) - FULL ACCESS
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000001', id FROM permissions;

-- CENTRAL_AUTHORITY (a0000000-0000-0000-0000-000000000002)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000002', id FROM permissions WHERE name IN (
    'projects.read', 'projects.update', 'projects.submit',
    'parcels.read',
    'documents.read', 'documents.verify',
    'workflow.read', 'workflow.transition',
    'verification.read', 'verification.verify', 'verification.reject',
    'compensation.read', 'compensation.approve',
    'rr.read',
    'jurisdiction.read', 'jurisdiction.confirm',
    'gis.read',
    'audit.read',
    'notifications.read',
    'reports.read', 'reports.export',
    'objections.read', 'objections.review',
    'hearings.read', 'hearings.decide'
);

-- STATE_AUTHORITY (a0000000-0000-0000-0000-000000000003)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000003', id FROM permissions WHERE name IN (
    'projects.create', 'projects.read', 'projects.update', 'projects.submit',
    'parcels.create', 'parcels.read', 'parcels.update',
    'documents.upload', 'documents.read', 'documents.verify',
    'workflow.read', 'workflow.transition', 'workflow.assign',
    'verification.read', 'verification.verify', 'verification.reject',
    'compensation.read', 'compensation.approve',
    'rr.read', 'rr.assess', 'rr.plan',
    'jurisdiction.read', 'jurisdiction.suggest', 'jurisdiction.confirm',
    'gis.read', 'gis.verify',
    'audit.read',
    'notifications.read', 'notifications.manage',
    'reports.read', 'reports.export',
    'objections.read', 'objections.review',
    'hearings.read', 'hearings.schedule', 'hearings.decide'
);

-- DISTRICT_ADMIN (a0000000-0000-0000-0000-000000000004)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000004', id FROM permissions WHERE name IN (
    'projects.create', 'projects.read', 'projects.update', 'projects.submit',
    'parcels.create', 'parcels.read', 'parcels.update',
    'documents.upload', 'documents.read', 'documents.verify',
    'workflow.read', 'workflow.transition', 'workflow.assign',
    'verification.read', 'verification.verify', 'verification.reject',
    'compensation.read', 'compensation.assess', 'compensation.approve',
    'rr.read', 'rr.assess', 'rr.plan', 'rr.update',
    'jurisdiction.read', 'jurisdiction.suggest',
    'gis.read', 'gis.verify', 'gis.upload_geometry',
    'audit.read',
    'notifications.read', 'notifications.manage',
    'reports.read', 'reports.export',
    'objections.read', 'objections.review',
    'hearings.read', 'hearings.schedule', 'hearings.decide'
);

-- LAND_ACQUIRING_OFFICER (a0000000-0000-0000-0000-000000000005)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000005', id FROM permissions WHERE name IN (
    'projects.read', 'projects.update', 'projects.submit',
    'parcels.create', 'parcels.read', 'parcels.update',
    'documents.upload', 'documents.read',
    'workflow.read', 'workflow.transition',
    'verification.read',
    'compensation.read', 'compensation.assess',
    'rr.read', 'rr.assess',
    'jurisdiction.read',
    'gis.read',
    'notifications.read',
    'objections.read',
    'hearings.read'
);

-- PROJECT_SPONSOR (a0000000-0000-0000-0000-000000000006)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000006', id FROM permissions WHERE name IN (
    'projects.create', 'projects.read', 'projects.update', 'projects.submit',
    'parcels.read',
    'documents.upload', 'documents.read',
    'workflow.read',
    'verification.read',
    'compensation.read',
    'rr.read',
    'jurisdiction.read',
    'gis.read',
    'notifications.read',
    'reports.read',
    'objections.read',
    'hearings.read'
);

-- SURVEYOR_GIS_OFFICER (a0000000-0000-0000-0000-000000000007)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000007', id FROM permissions WHERE name IN (
    'projects.read',
    'parcels.create', 'parcels.read', 'parcels.update',
    'documents.upload', 'documents.read',
    'workflow.read',
    'verification.read', 'verification.verify',
    'gis.read', 'gis.verify', 'gis.upload_geometry',
    'notifications.read'
);

-- VERIFICATION_OFFICER (a0000000-0000-0000-0000-000000000008)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000008', id FROM permissions WHERE name IN (
    'projects.read',
    'parcels.read',
    'documents.read', 'documents.verify',
    'workflow.read', 'workflow.transition',
    'verification.read', 'verification.verify', 'verification.reject',
    'jurisdiction.read', 'jurisdiction.suggest',
    'gis.read', 'gis.verify',
    'notifications.read',
    'objections.read', 'objections.review'
);

-- COMPENSATION_OFFICER (a0000000-0000-0000-0000-000000000009)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000009', id FROM permissions WHERE name IN (
    'projects.read',
    'parcels.read',
    'documents.upload', 'documents.read',
    'workflow.read',
    'verification.read',
    'compensation.read', 'compensation.assess', 'compensation.approve', 'compensation.process_payment',
    'notifications.read',
    'objections.read'
);

-- RR_OFFICER (a0000000-0000-0000-0000-000000000010)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000010', id FROM permissions WHERE name IN (
    'projects.read',
    'parcels.read',
    'documents.upload', 'documents.read',
    'workflow.read',
    'verification.read',
    'rr.read', 'rr.assess', 'rr.plan', 'rr.update',
    'notifications.read',
    'objections.read'
);

-- REVIEWER (a0000000-0000-0000-0000-000000000011)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000011', id FROM permissions WHERE name IN (
    'projects.read',
    'parcels.read',
    'documents.read', 'documents.verify',
    'workflow.read', 'workflow.transition',
    'verification.read', 'verification.verify', 'verification.reject',
    'compensation.read',
    'rr.read',
    'jurisdiction.read',
    'gis.read', 'gis.verify',
    'audit.read',
    'notifications.read',
    'reports.read',
    'objections.read', 'objections.review',
    'hearings.read', 'hearings.decide'
);

-- AUDITOR (a0000000-0000-0000-0000-000000000012)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000012', id FROM permissions WHERE name IN (
    'projects.read',
    'parcels.read',
    'documents.read',
    'workflow.read',
    'verification.read',
    'compensation.read',
    'rr.read',
    'jurisdiction.read',
    'gis.read',
    'audit.read', 'audit.export',
    'notifications.read',
    'reports.read', 'reports.export',
    'objections.read',
    'hearings.read'
);

-- VIEWER (a0000000-0000-0000-0000-000000000013)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'a0000000-0000-0000-0000-000000000013', id FROM permissions WHERE name IN (
    'projects.read',
    'parcels.read',
    'documents.read',
    'workflow.read',
    'verification.read',
    'compensation.read',
    'rr.read',
    'jurisdiction.read',
    'gis.read',
    'notifications.read',
    'reports.read',
    'objections.read',
    'hearings.read'
);

-- =============================================================================
-- DONE
-- =============================================================================
