-- ============================================================================
-- Bhu-Drishti Migration 002
-- DEMO / INTELLIGENCE DOMAIN TABLES
--
-- These tables back the SIH demo/presentation intelligence modules:
-- possession, escalations, data conflicts, health scores, historical
-- analytics, integration health, data provenance, dependencies, what-if
-- scenarios and resource prioritization.
--
-- In the local dev environment the schema is also (re)created automatically by
-- running `python -m scripts.seed_demo_data seed` (which calls
-- Base.metadata.create_all). This file documents the DDL for environments that
-- manage migrations manually.
-- ============================================================================

CREATE TABLE IF NOT EXISTS possessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    parcel_id UUID NOT NULL REFERENCES parcels(id),
    award_reference VARCHAR(100),
    possession_status VARCHAR(30) DEFAULT 'PENDING',
    possession_date TIMESTAMP,
    pending_reason TEXT,
    verification_status VARCHAR(30) DEFAULT 'PENDING',
    responsible_authority VARCHAR(200),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    escalation_code VARCHAR(30) UNIQUE NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id),
    stage VARCHAR(50),
    trigger_reason TEXT NOT NULL,
    level INTEGER DEFAULT 1,
    responsible_authority VARCHAR(200),
    status VARCHAR(30) DEFAULT 'OPEN',
    created_date TIMESTAMP DEFAULT now(),
    resolution_date TIMESTAMP,
    resolution_action TEXT,
    created_by UUID REFERENCES profiles(id),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS data_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conflict_code VARCHAR(30) UNIQUE NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id),
    parcel_id UUID REFERENCES parcels(id),
    source_a VARCHAR(200) NOT NULL,
    source_b VARCHAR(200) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(30) DEFAULT 'OPEN',
    resolution_reason TEXT,
    resolved_by UUID REFERENCES profiles(id),
    detected_at TIMESTAMP DEFAULT now(),
    resolved_at TIMESTAMP,
    evidence JSONB,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project_health_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    score FLOAT NOT NULL,
    band VARCHAR(30) NOT NULL,
    factors JSONB,
    computed_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS parcel_health_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id UUID NOT NULL REFERENCES parcels(id),
    project_id UUID REFERENCES projects(id),
    score FLOAT NOT NULL,
    band VARCHAR(30) NOT NULL,
    factors JSONB,
    computed_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS historical_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period VARCHAR(20) NOT NULL,
    entity_type VARCHAR(30) NOT NULL,
    entity_name VARCHAR(200) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    is_demo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS integration_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_name VARCHAR(200) NOT NULL,
    system_code VARCHAR(50) UNIQUE NOT NULL,
    integration_type VARCHAR(50),
    last_sync TIMESTAMP,
    status VARCHAR(30) DEFAULT 'NEVER_SYNCED',
    records_synced INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    conflicts INTEGER DEFAULT 0,
    api_response_time_ms INTEGER,
    last_error TEXT,
    is_demo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS data_provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    source_system VARCHAR(200) NOT NULL,
    source_record_id VARCHAR(100),
    created_by_name VARCHAR(200),
    creation_timestamp TIMESTAMP DEFAULT now(),
    last_updated TIMESTAMP,
    verification_status VARCHAR(30) DEFAULT 'PENDING',
    last_synchronization TIMESTAMP,
    supporting_document VARCHAR(500),
    is_demo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    from_stage VARCHAR(50),
    to_stage VARCHAR(50),
    dependency_type VARCHAR(50),
    dependency_description TEXT,
    is_satisfied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS what_if_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_code VARCHAR(30) UNIQUE NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id),
    title VARCHAR(300) NOT NULL,
    description TEXT,
    current_completion_label VARCHAR(100),
    simulated_completion_label VARCHAR(100),
    estimated_time_saved_days INTEGER,
    intervention TEXT,
    assumptions TEXT,
    is_demo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS resource_priorities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) UNIQUE,
    priority_score FLOAT NOT NULL,
    priority_rank INTEGER NOT NULL,
    reasoning TEXT,
    update_date TIMESTAMP DEFAULT now()
);
