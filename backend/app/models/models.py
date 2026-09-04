from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey,
    Enum as SAEnum, Index, UniqueConstraint, JSON, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
import uuid
import enum


class Base(DeclarativeBase):
    pass


class ProjectStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    JURISDICTION_CHECK = "JURISDICTION_CHECK"
    GIS_VERIFICATION = "GIS_VERIFICATION"
    PUBLIC_HEARING = "PUBLIC_HEARING"
    COMPENSATION_ASSESSMENT = "COMPENSATION_ASSESSMENT"
    RR_PLANNING = "RR_PLANNING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ParcelStatusEnum(str, enum.Enum):
    IDENTIFIED = "IDENTIFIED"
    VERIFIED = "VERIFIED"
    ACQUISITION_PENDING = "ACQUISITION_PENDING"
    ACQUIRED = "ACQUIRED"
    COMPENSATION_PAID = "COMPENSATION_PAID"
    DISPUTED = "DISPUTED"
    EXEMPTED = "EXEMPTED"


class TaskStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"


class TaskTypeEnum(str, enum.Enum):
    REVIEW = "REVIEW"
    APPROVAL = "APPROVAL"
    VERIFICATION = "VERIFICATION"
    ASSESSMENT = "ASSESSMENT"
    NOTIFICATION = "NOTIFICATION"
    GIS_CHECK = "GIS_CHECK"
    JURISDICTION_CHECK = "JURISDICTION_CHECK"
    COMPENSATION = "COMPENSATION"
    RR_PLANNING = "RR_PLANNING"
    HEARING = "HEARING"


class DocumentTypeEnum(str, enum.Enum):
    LAND_RECORD = "LAND_RECORD"
    OWNERSHIP_CERTIFICATE = "OWNERSHIP_CERTIFICATE"
    SURVEY_MAP = "SURVEY_MAP"
    NOTIFICATION_ORDER = "NOTIFICATION_ORDER"
    COMPENSATION_ORDER = "COMPENSATION_ORDER"
    RR_PLAN = "RR_PLAN"
    PUBLIC_HEARING_MINUTES = "PUBLIC_HEARING_MINUTES"
    ENVIRONMENT_CLEARANCE = "ENVIRONMENT_CLEARANCE"
    GIS_MAP = "GIS_MAP"
    JUDICIAL_ORDER = "JUDICIAL_ORDER"
    OTHER = "OTHER"


class DocumentStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UNDER_REVIEW = "UNDER_REVIEW"


class OwnershipTypeEnum(str, enum.Enum):
    PRIVATE = "PRIVATE"
    GOVERNMENT = "GOVERNMENT"
    COMMUNITY = "COMMUNITY"
    endOWMENT = "ENDOWMENT"
    WAQF = "WAQF"
    FOREST = "FOREST"


class LandTypeEnum(str, enum.Enum):
    AGRICULTURAL = "AGRICULTURAL"
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"
    FOREST = "FOREST"
    WASTELAND = "WASTELAND"
    WATER_BODY = "WATER_BODY"
    PUBLIC_PURPOSE = "PUBLIC_PURPOSE"


class ProjectTypeEnum(str, enum.Enum):
    NATIONAL_HIGHWAY = "NATIONAL_HIGHWAY"
    RAILWAY = "RAILWAY"
    DAM = "DAM"
    INDUSTRIAL_CORRIDOR = "INDUSTRIAL_CORRIDOR"
    URBAN_DEVELOPMENT = "URBAN_DEVELOPMENT"
    MINING = "MINING"
    POWER_PROJECT = "POWER_PROJECT"
    DEFENCE = "DEFENCE"
    OTHER = "OTHER"


class NotificationTypeEnum(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    SLA_BREACH = "SLA_BREACH"
    STATUS_CHANGE = "STATUS_CHANGE"
    ASSIGNMENT = "ASSIGNMENT"


class ObjectionStatusEnum(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    HEARING_SCHEDULED = "HEARING_SCHEDULED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    APPEALED = "APPEALED"


class CompensationStatusEnum(str, enum.Enum):
    ASSESSED = "ASSESSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PAID = "PAID"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"


class RRStatusEnum(str, enum.Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    PENDING_REVIEW = "PENDING_REVIEW"
    ASSISTANCE_PLANNED = "ASSISTANCE_PLANNED"
    ASSISTANCE_DELIVERED = "ASSISTANCE_DELIVERED"


class JurisdictionLevelEnum(str, enum.Enum):
    CENTRAL = "CENTRAL"
    STATE = "STATE"
    DISTRICT = "DISTRICT"


class Role(Base):
    __tablename__ = "roles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    profiles = relationship("Profile", back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    module = Column(String(50), nullable=False)
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)


class Department(Base):
    __tablename__ = "departments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    level = Column(Integer, default=1)
    state_code = Column(String(10))
    district_code = Column(String(10))
    parent = relationship("Department", remote_side=[id], backref="children")
    profiles = relationship("Profile", back_populates="department")


class State(Base):
    __tablename__ = "states"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    districts = relationship("District", back_populates="state")
    profiles = relationship("Profile", back_populates="state")


class District(Base):
    __tablename__ = "districts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=False)
    state = relationship("State", back_populates="districts")
    tehsils = relationship("Tehsil", back_populates="district")
    __table_args__ = (UniqueConstraint("code", "state_id"),)


class Tehsil(Base):
    __tablename__ = "tehsils"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=False)
    district = relationship("District", back_populates="tehsils")
    villages = relationship("Village", back_populates="tehsil")
    __table_args__ = (UniqueConstraint("code", "district_id"),)


class Village(Base):
    __tablename__ = "villages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    tehsil_id = Column(UUID(as_uuid=True), ForeignKey("tehsils.id"), nullable=False)
    pin_code = Column(String(10))
    tehsil = relationship("Tehsil", back_populates="villages")
    __table_args__ = (UniqueConstraint("code", "tehsil_id"),)


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=True)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    role = relationship("Role", back_populates="profiles")
    department = relationship("Department", back_populates="profiles")
    state = relationship("State", back_populates="profiles")


class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    project_type = Column(String(50), nullable=False)
    purpose = Column(Text)
    public_category = Column(String(100))
    sponsor_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    land_requiring_body_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    proposed_area_sq_m = Column(Numeric(15, 2))
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=True)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=True)
    tehsil_id = Column(UUID(as_uuid=True), ForeignKey("tehsils.id"), nullable=True)
    village_id = Column(UUID(as_uuid=True), ForeignKey("villages.id"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    target_completion_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=3)
    estimated_cost = Column(Numeric(15, 2))
    funding_source = Column(String(200))
    status = Column(String(50), default="DRAFT", nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    workflow_instance = relationship("WorkflowInstance", back_populates="project", uselist=False)
    parcels = relationship("Parcel", secondary="project_parcels", back_populates="projects")
    documents = relationship("ProjectDocument", back_populates="project")
    status_history = relationship("ProjectStatusHistory", back_populates="project")
    activity = relationship("ProjectActivity", back_populates="project")
    jurisdiction_decisions = relationship("JurisdictionDecision", back_populates="project")
    gis_verifications = relationship("GISVerification", back_populates="project")
    compensation_cases = relationship("CompensationCase", back_populates="project")
    rr_cases = relationship("RRCase", back_populates="project")
    objections = relationship("Objection", back_populates="project")
    sponsor = relationship("Department", foreign_keys=[sponsor_id])
    land_requiring_body = relationship("Department", foreign_keys=[land_requiring_body_id])
    creator = relationship("Profile", foreign_keys=[created_by])


class ProjectStatusHistory(Base):
    __tablename__ = "project_status_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    previous_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    comment = Column(Text)
    changed_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="status_history")
    changer = relationship("Profile", foreign_keys=[changed_by])


class Parcel(Base):
    __tablename__ = "parcels"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_code = Column(String(30), unique=True, nullable=False, index=True)
    survey_number = Column(String(50))
    khasra_number = Column(String(50))
    ulpin = Column(String(30), unique=True, nullable=True)
    village_id = Column(UUID(as_uuid=True), ForeignKey("villages.id"), nullable=False)
    tehsil_id = Column(UUID(as_uuid=True), ForeignKey("tehsils.id"), nullable=False)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"), nullable=False)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=False)
    land_type = Column(String(30), default="AGRICULTURAL")
    ownership_type = Column(String(30), default="PRIVATE")
    area_sq_m = Column(Numeric(15, 2), nullable=False)
    geometry = Column(JSONB, nullable=True)
    current_status = Column(String(30), default="IDENTIFIED")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owners = relationship("ParcelOwner", back_populates="parcel")
    projects = relationship("Project", secondary="project_parcels", back_populates="parcels")
    gis_verifications = relationship("GISVerification", back_populates="parcel")
    compensation_cases = relationship("CompensationCase", back_populates="parcel")
    rr_cases = relationship("RRCase", back_populates="parcel")
    village = relationship("Village")
    tehsil = relationship("Tehsil")
    district = relationship("District")
    state = relationship("State")


class ParcelOwner(Base):
    __tablename__ = "parcel_owners"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False)
    owner_name = Column(String(200), nullable=False)
    father_husband_name = Column(String(200))
    gender = Column(String(10))
    age = Column(Integer)
    aadhaar_last4 = Column(String(4))
    relation_to_holder = Column(String(50))
    is_primary = Column(Boolean, default=True)
    contact_phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    parcel = relationship("Parcel", back_populates="owners")


class ProjectParcel(Base):
    __tablename__ = "project_parcels"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False)
    acquired_area_sq_m = Column(Numeric(15, 2))
    __table_args__ = (UniqueConstraint("project_id", "parcel_id"),)


class ProjectDocument(Base):
    __tablename__ = "project_documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True)
    document_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    checksum = Column(String(64))
    status = Column(String(30), default="PENDING")
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    verification_comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project = relationship("Project", back_populates="documents")
    parcel = relationship("Parcel")
    uploader = relationship("Profile", foreign_keys=[uploaded_by])
    verifier = relationship("Profile", foreign_keys=[verified_by])


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("project_documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    checksum = Column(String(64))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("ProjectDocument")
    uploader = relationship("Profile")


class DocumentVerification(Base):
    __tablename__ = "document_verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("project_documents.id"), nullable=False)
    verifier_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    status = Column(String(30), nullable=False)
    comment = Column(Text)
    verified_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("ProjectDocument")
    verifier = relationship("Profile")


class ProjectVerification(Base):
    __tablename__ = "project_verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    verifier_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    verification_type = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False)
    comment = Column(Text)
    verified_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project")
    verifier = relationship("Profile")


class JurisdictionRule(Base):
    __tablename__ = "jurisdiction_rules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_code = Column(String(50), unique=True, nullable=False)
    rule_version = Column(String(10), default="1.0")
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    conditions = Column(JSONB, nullable=False)
    result = Column(JSONB, nullable=False)
    source_reference = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    decisions = relationship("JurisdictionDecision", back_populates="rule")


class JurisdictionDecision(Base):
    __tablename__ = "jurisdiction_decisions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("jurisdiction_rules.id"), nullable=False)
    suggested_appropriate_govt = Column(String(100))
    suggested_acquiring_body = Column(String(200))
    suggested_authority = Column(String(200))
    confidence_score = Column(Float)
    reason = Column(Text)
    officer_verified = Column(Boolean, default=False)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    officer_comment = Column(Text)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="jurisdiction_decisions")
    rule = relationship("JurisdictionRule", back_populates="decisions")
    officer = relationship("Profile", foreign_keys=[officer_id])


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), unique=True, nullable=False)
    current_status = Column(String(50), default="DRAFT")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project = relationship("Project", back_populates="workflow_instance")
    tasks = relationship("WorkflowTask", back_populates="instance")
    transitions = relationship("WorkflowTransition", back_populates="instance")


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    assigned_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    task_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(30), default="PENDING")
    sla_deadline = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    instance = relationship("WorkflowInstance", back_populates="tasks")
    assignee = relationship("Profile", foreign_keys=[assigned_to])
    assigned_role = relationship("Role", foreign_keys=[assigned_role_id])
    sla_events = relationship("SLAEvent", back_populates="task")


class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("workflow_tasks.id"), nullable=True)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    actor_role = Column(String(100))
    comment = Column(Text)
    supporting_document_id = Column(UUID(as_uuid=True), ForeignKey("project_documents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    instance = relationship("WorkflowInstance", back_populates="transitions")
    task = relationship("WorkflowTask")
    actor = relationship("Profile", foreign_keys=[actor_id])


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(30), default="INFO")
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("Profile")


class SLARule(Base):
    __tablename__ = "sla_rules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    max_duration_hours = Column(Integer, nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    priority = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SLAEvent(Base):
    __tablename__ = "sla_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_task_id = Column(UUID(as_uuid=True), ForeignKey("workflow_tasks.id"), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("sla_rules.id"), nullable=False)
    status = Column(String(30), default="ON_TRACK")
    deadline = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    escalation_level = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    task = relationship("WorkflowTask", back_populates="sla_events")
    rule = relationship("SLARule")


class CompensationCase(Base):
    __tablename__ = "compensation_cases"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    landowner_id = Column(UUID(as_uuid=True), ForeignKey("parcel_owners.id"), nullable=False)
    assessed_value = Column(Numeric(15, 2))
    land_area_sq_m = Column(Numeric(15, 2))
    compensation_components = Column(JSONB)
    total_amount = Column(Numeric(15, 2))
    status = Column(String(30), default="ASSESSED")
    assigned_officer_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    parcel = relationship("Parcel", back_populates="compensation_cases")
    project = relationship("Project", back_populates="compensation_cases")
    landowner = relationship("ParcelOwner")
    assigned_officer = relationship("Profile", foreign_keys=[assigned_officer_id])
    payments = relationship("CompensationPayment", back_populates="case")


class CompensationPayment(Base):
    __tablename__ = "compensation_payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("compensation_cases.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_reference = Column(String(200))
    payment_date = Column(DateTime, nullable=False)
    status = Column(String(30), default="PENDING")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("CompensationCase", back_populates="payments")
    approver = relationship("Profile", foreign_keys=[approved_by])


class RRCase(Base):
    __tablename__ = "rr_cases"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False)
    landowner_id = Column(UUID(as_uuid=True), ForeignKey("parcel_owners.id"), nullable=False)
    family_members_count = Column(Integer)
    eligibility_status = Column(String(30), default="PENDING_REVIEW")
    entitlement_details = Column(JSONB)
    assistance_type = Column(String(50))
    assigned_officer_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    status = Column(String(30), default="PENDING_REVIEW")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project = relationship("Project", back_populates="rr_cases")
    parcel = relationship("Parcel", back_populates="rr_cases")
    landowner = relationship("ParcelOwner")
    assigned_officer = relationship("Profile", foreign_keys=[assigned_officer_id])


class Objection(Base):
    __tablename__ = "objections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objection_code = Column(String(30), unique=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True)
    landowner_id = Column(UUID(as_uuid=True), ForeignKey("parcel_owners.id"), nullable=True)
    submission_date = Column(DateTime, default=datetime.utcnow)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="SUBMITTED")
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="objections")
    parcel = relationship("Parcel")
    landowner = relationship("ParcelOwner")
    creator = relationship("Profile", foreign_keys=[created_by])
    hearings = relationship("Hearing", back_populates="objection")


class Hearing(Base):
    __tablename__ = "hearings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objection_id = Column(UUID(as_uuid=True), ForeignKey("objections.id"), nullable=False)
    hearing_date = Column(DateTime, nullable=False)
    hearing_officer_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    location = Column(String(300))
    decision = Column(String(50))
    decision_details = Column(Text)
    decision_date = Column(DateTime, nullable=True)
    next_hearing_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    objection = relationship("Objection", back_populates="hearings")
    hearing_officer = relationship("Profile", foreign_keys=[hearing_officer_id])


class GISVerification(Base):
    __tablename__ = "gis_verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    geometry_valid = Column(Boolean)
    area_match = Column(Boolean)
    overlap_detected = Column(Boolean)
    overlap_parcel_ids = Column(JSON)
    outside_boundary = Column(Boolean)
    conflict_details = Column(JSONB)
    verification_notes = Column(Text)
    verified_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="gis_verifications")
    parcel = relationship("Parcel", back_populates="gis_verifications")
    verifier = relationship("Profile", foreign_keys=[verified_by])


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    actor_email = Column(String(255))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True))
    previous_value = Column(JSONB)
    new_value = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    meta = Column(JSONB, name="metadata")
    created_at = Column(DateTime, default=datetime.utcnow)
    actor = relationship("Profile", foreign_keys=[actor_id])


class ProjectActivity(Base):
    __tablename__ = "project_activity"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    meta = Column(JSONB, name="metadata")
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="activity")
    actor = relationship("Profile")


class Possession(Base):
    __tablename__ = "possessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False)
    award_reference = Column(String(100))
    possession_status = Column(String(30), default="PENDING")
    possession_date = Column(DateTime, nullable=True)
    pending_reason = Column(Text)
    verification_status = Column(String(30), default="PENDING")
    responsible_authority = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project = relationship("Project")
    parcel = relationship("Parcel")


class Escalation(Base):
    __tablename__ = "escalations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escalation_code = Column(String(30), unique=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    stage = Column(String(50))
    trigger_reason = Column(Text, nullable=False)
    level = Column(Integer, default=1)
    responsible_authority = Column(String(200))
    status = Column(String(30), default="OPEN")
    created_date = Column(DateTime, default=datetime.utcnow)
    resolution_date = Column(DateTime, nullable=True)
    resolution_action = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project = relationship("Project")
    creator = relationship("Profile")


class DataConflict(Base):
    __tablename__ = "data_conflicts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conflict_code = Column(String(30), unique=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True)
    source_a = Column(String(200), nullable=False)
    source_b = Column(String(200), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    severity = Column(String(20), default="MEDIUM")
    status = Column(String(30), default="OPEN")
    resolution_reason = Column(Text)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    evidence = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project")
    parcel = relationship("Parcel")
    resolver = relationship("Profile")


class ProjectHealthScore(Base):
    __tablename__ = "project_health_scores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    score = Column(Float, nullable=False)
    band = Column(String(30), nullable=False)
    factors = Column(JSONB)
    computed_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project")


class ParcelHealthScore(Base):
    __tablename__ = "parcel_health_scores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    score = Column(Float, nullable=False)
    band = Column(String(30), nullable=False)
    factors = Column(JSONB)
    computed_at = Column(DateTime, default=datetime.utcnow)
    parcel = relationship("Parcel")


class HistoricalAnalytics(Base):
    __tablename__ = "historical_analytics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period = Column(String(20), nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_name = Column(String(200), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IntegrationHealth(Base):
    __tablename__ = "integration_health"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_name = Column(String(200), nullable=False)
    system_code = Column(String(50), unique=True, nullable=False)
    integration_type = Column(String(50))
    last_sync = Column(DateTime, nullable=True)
    status = Column(String(30), default="NEVER_SYNCED")
    records_synced = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    conflicts = Column(Integer, default=0)
    api_response_time_ms = Column(Integer)
    last_error = Column(Text)
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataProvenance(Base):
    __tablename__ = "data_provenance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    source_system = Column(String(200), nullable=False)
    source_record_id = Column(String(100))
    created_by_name = Column(String(200))
    creation_timestamp = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, nullable=True)
    verification_status = Column(String(30), default="PENDING")
    last_synchronization = Column(DateTime, nullable=True)
    supporting_document = Column(String(500))
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Dependency(Base):
    __tablename__ = "dependencies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    from_stage = Column(String(50))
    to_stage = Column(String(50))
    dependency_type = Column(String(50))
    dependency_description = Column(Text)
    is_satisfied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project")


class WhatIfScenario(Base):
    __tablename__ = "what_if_scenarios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_code = Column(String(30), unique=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    current_completion_label = Column(String(100))
    simulated_completion_label = Column(String(100))
    estimated_time_saved_days = Column(Integer)
    intervention = Column(Text)
    assumptions = Column(Text)
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project")


class ResourcePriority(Base):
    __tablename__ = "resource_priorities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    priority_score = Column(Float, nullable=False)
    priority_rank = Column(Integer, nullable=False)
    reasoning = Column(Text)
    update_date = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project")
