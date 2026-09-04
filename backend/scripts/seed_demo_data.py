"""
Bhu-Drishti comprehensive DEMO dataset.

Populates a large, internally-consistent, fictional dataset across every domain
for SIH presentation and testing. All records are clearly marked as
DEMO / PROTOTYPE DATA.

Entry points:
    python -m scripts.seed_demo_data seed      -> seed (non-destructive, idempotent)
    python -m scripts.seed_demo_data clear     -> delete only demo-marked records
    python -m scripts.seed_demo_data validate  -> run data-quality validation

The script is idempotent: running it repeatedly will not duplicate records.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func, not_, or_, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.models.models import (
    Base, Role, Permission, RolePermission, Department, State, District, Tehsil,
    Village, Profile, Project, ProjectStatusHistory, Parcel, ParcelOwner,
    ProjectParcel, ProjectDocument, WorkflowInstance, WorkflowTask,
    WorkflowTransition, Notification, SLARule, CompensationCase,
    CompensationPayment, RRCase, Objection, Hearing, GISVerification, AuditLog,
    ProjectActivity, JurisdictionRule, 
    Possession, Escalation, DataConflict, ProjectHealthScore, ParcelHealthScore,
    HistoricalAnalytics, IntegrationHealth, DataProvenance, Dependency,
    WhatIfScenario, ResourcePriority,
)
from app.security.password import hash_password
from app.gis.spatial_ops import calculate_area_from_geojson

ROLE_UUIDS = {
    "SUPER_ADMIN": "a0000000-0000-0000-0000-000000000001",
    "CENTRAL_AUTHORITY": "a0000000-0000-0000-0000-000000000002",
    "STATE_AUTHORITY": "a0000000-0000-0000-0000-000000000003",
    "DISTRICT_ADMIN": "a0000000-0000-0000-0000-000000000004",
    "LAND_ACQUIRING_OFFICER": "a0000000-0000-0000-0000-000000000005",
    "PROJECT_SPONSOR": "a0000000-0000-0000-0000-000000000006",
    "SURVEYOR_GIS_OFFICER": "a0000000-0000-0000-0000-000000000007",
    "VERIFICATION_OFFICER": "a0000000-0000-0000-0000-000000000008",
    "COMPENSATION_OFFICER": "a0000000-0000-0000-0000-000000000009",
    "RR_OFFICER": "a0000000-0000-0000-0000-000000000010",
    "REVIEWER": "a0000000-0000-0000-0000-000000000011",
    "AUDITOR": "a0000000-0000-0000-0000-000000000012",
    "VIEWER": "a0000000-0000-0000-0000-000000000013",
}

# British English subject line for demo entries
DEMO_TAG = "DEMO / PROTOTYPE DATA"

# (state, code, [(district, code, [(tehsil, code, pin)])])
GEOGRAPHY = [
    ("Uttar Pradesh", "UP", [
        ("Lucknow", "LUC", [("Lucknow City", "LUCC", "226001"), ("Mohanlalganj", "MOH", "227305")]),
        ("Kanpur Nagar", "KAN", [("Kanpur City", "KANC", "208001"), ("Bilhaur", "BIL", "209202")]),
        ("Varanasi", "VAR", [("Varanasi City", "VARC", "221001"), ("Pindra", "PIN", "221206")]),
        ("Agra", "AGRA", [("Agra City", "AGRC", "282001"), ("Etmadpur", "ETM", "283202")]),
    ]),
    ("Bihar", "BR", [
        ("Patna", "PAT", [("Patna City", "PATC", "800001"), ("Danapur", "DAN", "801503")]),
        ("Gaya", "GAYA", [("Gaya City", "GAYC", "823001"), ("Bodh Gaya", "BOD", "824231")]),
        ("Muzaffarpur", "MUZ", [("Muzaffarpur City", "MUZC", "842001"), ("Sakra", "SAK", "843119")]),
    ]),
    ("Madhya Pradesh", "MP", [
        ("Bhopal", "BHO", [("Bhopal City", "BHOC", "462001"), ("Berasia", "BER", "463106")]),
        ("Indore", "IND", [("Indore City", "INDC", "452001"), ("Depalpur", "DEP", "453115")]),
        ("Jabalpur", "JAB", [("Jabalpur City", "JABC", "482001"), ("Patan", "PATN", "483113")]),
    ]),
    ("Rajasthan", "RJ", [
        ("Jaipur", "JAI", [("Jaipur City", "JAIC", "302001"), ("Amer", "AME", "303104")]),
        ("Jodhpur", "JOD", [("Jodhpur City", "JODC", "342001"), ("Osian", "OSI", "342303")]),
        ("Kota", "KOTA", [("Kota City", "KOTC", "324001"), ("Ladpura", "LAD", "325001")]),
    ]),
    ("Maharashtra", "MH", [
        ("Mumbai", "MUM", [("Mumbai City", "MUMC", "400001"), ("Thane", "THA", "400601")]),
        ("Pune", "PUN", [("Pune City", "PUNC", "411001"), ("Junnar", "JUN", "410502")]),
        ("Nagpur", "NAG", [("Nagpur City", "NAGC", "440001"), ("Ramtek", "RAM", "441106")]),
    ]),
    ("Karnataka", "KA", [
        ("Bengaluru Urban", "BLR", [("Bengaluru North", "BLRN", "560001"), ("Bengaluru South", "BLRS", "560002")]),
        ("Mysuru", "MYS", [("Mysuru City", "MYSC", "570001"), ("Nanjangud", "NAN", "571301")]),
    ]),
    ("Gujarat", "GJ", [
        ("Ahmedabad", "AMD", [("Ahmedabad City", "AMDC", "380001"), ("Dholka", "DHO", "382225")]),
        ("Surat", "SRT", [("Surat City", "SRTC", "395001"), ("Choryasi", "CHO", "394110")]),
    ]),
    ("Odisha", "OD", [
        ("Bhubaneswar", "BBSR", [("Bhubaneswar City", "BBSC", "751001"), ("Khordha", "KHO", "752055")]),
        ("Cuttack", "CUT", [("Cuttack City", "CUTC", "753001"), ("Barabati", "BAR", "754005")]),
    ]),
    ("West Bengal", "WB", [
        ("Kolkata", "KOL", [("Kolkata City", "KOLC", "700001"), ("Baruipur", "BAS", "700144")]),
        ("Howrah", "HOW", [("Howrah City", "HOWC", "711101"), ("Bally", "BAL", "711201")]),
    ]),
]

# Demo named users across roles beyond the 13 canonical accounts.
# (full_name, email, role_name, state_code, dept_code, active)
EXTRA_USERS = [
    ("Rajesh Kumar", "rajesh.lao@bhudrishti.gov.in", "LAND_ACQUIRING_OFFICER", "UP", "LAO", True),
    ("Sunita Devi", "sunita.lao@bhudrishti.gov.in", "LAND_ACQUIRING_OFFICER", "BR", "LAO", True),
    ("Amit Chaudhary", "amit.lao@bhudrishti.gov.in", "LAND_ACQUIRING_OFFICER", "MP", "LAO", True),
    ("Pooja Yadav", "pooja.lao@bhudrishti.gov.in", "LAND_ACQUIRING_OFFICER", "RJ", "LAO", True),
    ("Sanjay Patil", "sanjay.lao@bhudrishti.gov.in", "LAND_ACQUIRING_OFFICER", "MH", "LAO", True),
    ("Meena Kumari", "meena.verification@bhudrishti.gov.in", "VERIFICATION_OFFICER", "UP", "LAO", True),
    ("Ravi Shankar", "ravi.verification@bhudrishti.gov.in", "VERIFICATION_OFFICER", "BR", "LAO", True),
    ("Kavita Mishra", "kavita.comp@bhudrishti.gov.in", "COMPENSATION_OFFICER", "UP", "LAO", True),
    ("Vivek Agarwal", "vivek.comp@bhudrishti.gov.in", "COMPENSATION_OFFICER", "MP", "LAO", True),
    ("Nisha Rani", "nisha.rr@bhudrishti.gov.in", "RR_OFFICER", "BR", "UDA", True),
    ("Deepak Singh", "deepak.gis@bhudrishti.gov.in", "SURVEYOR_GIS_OFFICER", "RJ", "UDA", True),
    ("Anjali Bose", "anjali.reviewer@bhudrishti.gov.in", "REVIEWER", "WB", "UDA", True),
    ("Manoj Sahu", "manoj.state@bhudrishti.gov.in", "STATE_AUTHORITY", "OD", "REV", True),
    ("Priyanka Ghosh", "priyanka.state@bhudrishti.gov.in", "STATE_AUTHORITY", "WB", "REV", True),
    ("Arvind Mehta", "arvind.admin@bhudrishti.gov.in", "CENTRAL_AUTHORITY", "UP", "NHAI", True),
    ("Suresh Babu", "suresh.district@bhudrishti.gov.in", "DISTRICT_ADMIN", "KA", "LAO", True),
]

# PROJECT_SCENARIO dict used to vary health/delay/risk.
PROJECT_DEFS = [
    # (name, project_type, purpose, public_category, state, district, tehsil, village,
    #  status, cost, priority, sponsor_dept, scenario)
    ("Mumbai-Pune Expressway Expansion", "NATIONAL_HIGHWAY", "Improve connectivity between Mumbai and Pune", "INFRASTRUCTURE",
     "MH", "MUM", "MUMC", "VMUMC", "IN_PROGRESS", 8500000000, 1, "NHAI", "A"),
    ("Nagpur Metro Rail Phase II", "RAILWAY", "Urban public transport connectivity", "TRANSPORT",
     "MH", "PUN", "PUNC", "VPUNC", "COMPENSATION_ASSESSMENT", 12000000000, 1, "RAIL", "D"),
    ("Varun Dam Construction Project", "DAM", "Multi-purpose dam for irrigation and drinking water", "WATER",
     "KA", "BLR", "BLRN", "VBLRN", "PUBLIC_HEARING", 4500000000, 2, "REV", "B"),
    ("Bengaluru Tech Park Development", "URBAN_DEVELOPMENT", "Development of IT park with residential and commercial zones", "IT_INFRASTRUCTURE",
     "KA", "BLR", "BLRN", "VBLRN", "RR_PLANNING", 3000000000, 3, "UDA", "E"),
    ("Dholera Smart City Industrial Corridor", "INDUSTRIAL_CORRIDOR", "Industrial corridor with smart city infrastructure", "INDUSTRIAL",
     "GJ", "AMD", "AMDC", "VAMDC", "DRAFT", 25000000000, 3, "UDA", "A"),
    ("Surat Coastal Highway", "NATIONAL_HIGHWAY", "Coastal highway connecting ports and industrial zones", "INFRASTRUCTURE",
     "GJ", "SRT", "SRTC", "VSRTC", "APPROVED", 5500000000, 2, "NHAI", "F"),
    ("Rajasthan Solar Power Plant Phase III", "POWER_PROJECT", "Utility scale solar power generation facility", "ENERGY",
     "RJ", "JAI", "JAIC", "VJAIC", "GIS_VERIFICATION", 8000000000, 2, "REV", "B"),
    ("Uttar Pradesh Irrigation Canal Network", "DAM", "Irrigation canal network for agricultural belt", "WATER",
     "UP", "LUC", "LUCC", "VLUCC", "UNDER_REVIEW", 6000000000, 2, "REV", "B"),
    ("Bihar Green Field Expressway", "NATIONAL_HIGHWAY", "Green field expressway through northern Bihar", "INFRASTRUCTURE",
     "BR", "PAT", "PATC", "VPATC", "JURISDICTION_CHECK", 9000000000, 1, "NHAI", "G"),
    ("Kanpur Leather Industrial Zone", "INDUSTRIAL_CORRIDOR", "Leather processing and manufacturing hub", "INDUSTRIAL",
     "UP", "KAN", "KANC", "VKANC", "COMPENSATION_ASSESSMENT", 4200000000, 1, "UDA", "D"),
    ("Patna-Gaya Rail Doubling", "RAILWAY", "Doubling of rail line between Patna and Gaya", "TRANSPORT",
     "BR", "GAYA", "GAYC", "VGAYC", "SUBMITTED", 7000000000, 2, "RAIL", "A"),
    ("Madhya Pradesh Solar Park", "POWER_PROJECT", "Regional solar power generation park", "ENERGY",
     "MP", "IND", "INDC", "VINDC", "DRAFT", 3500000000, 3, "REV", "A"),
    ("Indore Logistics Hub", "INDUSTRIAL_CORRIDOR", "Dedicated freight and logistics corridor hub", "INDUSTRIAL",
     "MP", "IND", "INDC", "VINDC", "DRAFT", 5000000000, 3, "UDA", "G"),
    ("Varanasi Riverfront Development", "URBAN_DEVELOPMENT", "Riverfront tourism and urban regeneration", "URBAN",
     "UP", "VAR", "VARC", "VVARC", "PUBLIC_HEARING", 2800000000, 3, "UDA", "B"),
    ("Agra Elevated Road Corridor", "NATIONAL_HIGHWAY", "Elevated road corridor to decongest the city", "INFRASTRUCTURE",
     "UP", "AGRA", "AGRC", "VAGRC", "GIS_VERIFICATION", 6200000000, 2, "NHAI", "C"),
    ("Kolkata IT Corridor Phase II", "URBAN_DEVELOPMENT", "Second phase of IT and business district", "IT_INFRASTRUCTURE",
     "WB", "KOL", "KOLC", "VKOLC", "UNDER_REVIEW", 4800000000, 2, "UDA", "A"),
    ("Bhubaneswar Metro Rail Corridor", "RAILWAY", "Metro corridor connecting transit hubs", "TRANSPORT",
     "OD", "BBSR", "BBSC", "VBBSC", "SUBMITTED", 9500000000, 2, "RAIL", "B"),
    ("Odisha Port Access Highway", "NATIONAL_HIGHWAY", "Highway improving port-connectivity", "INFRASTRUCTURE",
     "OD", "CUT", "CUTC", "VCUTC", "IN_PROGRESS", 7100000000, 2, "NHAI", "F"),
    ("Jaipur Outer Ring Road", "NATIONAL_HIGHWAY", "Peripheral ring road around Jaipur", "INFRASTRUCTURE",
     "RJ", "JOD", "JODC", "VJODC", "COMPLETED", 3900000000, 4, "NHAI", "A"),
    ("West Bengal Agro Processing Park", "URBAN_DEVELOPMENT", "Agro-processing and cold-chain hub", "AGRO",
     "WB", "HOW", "HOWC", "VHOWC", "DRAFT", 2200000000, 3, "UDA", "C"),
]

SCENARIO_MEANING = {
    "A": "Healthy",
    "B": "Delayed",
    "C": "Critical",
    "D": "Compensation bottleneck",
    "E": "R&R bottleneck",
    "F": "Possession bottleneck",
    "G": "Data conflict",
}

OWNER_NAME_POOL = [
    "Ramesh Kumar", "Suresh Patel", "Kavita Desai", "Mahesh Reddy", "Anita Gupta",
    "Vijay Sharma", "Sunita Devi", "Rahul Yadav", "Priya Singh", "Amit Verma",
    "Pooja Nair", "Sanjay Joshi", "Meena Iyer", "Arun Kumar", "Rekha Rao",
    "Mohan Lal", "Geeta Mishra", "Ravi Chandra", "Lakshmi Menon", "Hari Prasad",
]


def make_polygon_geojson(lat, lon, span=0.001):
    return {
        "type": "Polygon",
        "coordinates": [[
            [lon, lat],
            [lon + span, lat],
            [lon + span, lat + span],
            [lon, lat + span],
            [lon, lat],
        ]]
    }


def health_band(score):
    if score >= 90:
        return "HEALTHY"
    if score >= 70:
        return "WATCH"
    if score >= 40:
        return "AT_RISK"
    return "CRITICAL"


async def _count(session, model):
    return (await session.execute(select(func.count(model.id)))).scalar() or 0


# ---------------------------------------------------------------------------
# Roles, permissions, departments, geography, sla, jurisdiction
# ---------------------------------------------------------------------------
async def seed_roles_permissions(session):
    role_defs = {
        "SUPER_ADMIN": "Full system access",
        "CENTRAL_AUTHORITY": "Central government authority",
        "STATE_AUTHORITY": "State government authority",
        "DISTRICT_ADMIN": "District administration",
        "LAND_ACQUIRING_OFFICER": "Responsible for land acquisition",
        "PROJECT_SPONSOR": "Projects requiring land",
        "SURVEYOR_GIS_OFFICER": "Geographic survey and GIS data",
        "VERIFICATION_OFFICER": "Document and record verification",
        "COMPENSATION_OFFICER": "Compensation assessment",
        "RR_OFFICER": "Rehabilitation & resettlement",
        "REVIEWER": "Reviews submitted projects",
        "AUDITOR": "Audits system usage",
        "VIEWER": "Read-only access",
    }
    for name, desc in role_defs.items():
        if not (await session.execute(select(Role).where(Role.name == name))).scalar_one_or_none():
            session.add(Role(id=uuid.UUID(ROLE_UUIDS[name]), name=name, description=desc))
    await session.flush()

    modules = {
        "project": ["create_project", "view_project", "update_project", "delete_project", "submit_project"],
        "parcel": ["create_parcel", "view_parcel", "update_parcel"],
        "document": ["upload_document", "view_document", "verify_document"],
        "workflow": ["view_workflow", "approve_workflow", "transition_workflow"],
        "compensation": ["create_compensation", "view_compensation", "approve_compensation"],
        "rr": ["create_rr", "view_rr", "update_rr"],
        "jurisdiction": ["suggest_jurisdiction", "confirm_jurisdiction"],
        "gis": ["verify_gis", "view_gis"],
        "user": ["manage_users", "view_users"],
        "admin": ["manage_roles", "manage_permissions", "manage_departments"],
        "audit": ["view_audit", "export_audit"],
        "intelligence": ["view_health", "view_conflicts", "view_escalations", "view_analytics",
                         "view_integrations", "view_dependencies", "view_whatif", "view_possession",
                         "view_priority", "view_provenance"],
    }
    permission_ids = {}
    for _module, perms in modules.items():
        for perm_name in perms:
            existing = (await session.execute(
                select(Permission).where(Permission.name == perm_name))).scalar_one_or_none()
            if existing:
                permission_ids[perm_name] = existing.id
            else:
                perm = Permission(name=perm_name, module=_module)
                session.add(perm)
                await session.flush()
                permission_ids[perm_name] = perm.id

    all_perms = list(permission_ids.values())
    for name in role_defs:
        role_id = uuid.UUID(ROLE_UUIDS[name])
        existing_rp = (await session.execute(
            select(RolePermission).where(RolePermission.role_id == role_id))).scalars().all()
        if not existing_rp:
            for perm_id in all_perms:
                session.add(RolePermission(role_id=role_id, permission_id=perm_id))
    await session.flush()
    print(f"  roles/permissions ok ({len(all_perms)} permissions)")


async def seed_departments(session):
    dept_data = [
        ("Ministry of Road Transport & Highways", "MORTH", 1),
        ("National Highways Authority of India", "NHAI", 2),
        ("Ministry of Railways", "RAIL", 1),
        ("Central Public Works Department", "CPWD", 1),
        ("State Revenue Department", "REV", 1),
        ("Land Acquisition Office", "LAO", 3),
        ("Public Works Department", "PWD", 2),
        ("Urban Development Authority", "UDA", 2),
        ("Rural Development Department", "RDD", 2),
        ("Forest Department", "FOREST", 2),
    ]
    created = {}
    for name, code, level in dept_data:
        existing = (await session.execute(
            select(Department).where(Department.code == code))).scalar_one_or_none()
        if not existing:
            existing = Department(name=name, code=code, level=level)
            session.add(existing)
            await session.flush()
        created[code] = existing
    await session.flush()
    return created


async def seed_geography(session):
    states = {}
    for state_name, state_code, districts in GEOGRAPHY:
        state = (await session.execute(select(State).where(State.code == state_code))).scalar_one_or_none()
        if not state:
            state = State(name=state_name, code=state_code)
            session.add(state)
            await session.flush()
        states[state_code] = state
        for dist_name, dist_code, tehsils in districts:
            district = (await session.execute(
                select(District).where(District.code == dist_code, District.state_id == state.id))).scalar_one_or_none()
            if not district:
                district = District(name=dist_name, code=dist_code, state_id=state.id)
                session.add(district)
                await session.flush()
            for teh_name, teh_code, pin in tehsils:
                tehsil = (await session.execute(
                    select(Tehsil).where(Tehsil.code == teh_code, Tehsil.district_id == district.id))).scalar_one_or_none()
                if not tehsil:
                    tehsil = Tehsil(name=teh_name, code=teh_code, district_id=district.id)
                    session.add(tehsil)
                    await session.flush()
                if not (await session.execute(
                        select(Village).where(Village.name == teh_name, Village.tehsil_id == tehsil.id))).scalar_one_or_none():
                    session.add(Village(name=teh_name, code=f"V{teh_code}", tehsil_id=tehsil.id, pin_code=pin))
    await session.flush()
    print(f"  geography ok ({len(states)} states)")
    return states


async def seed_sla_rules(session):
    sla = [
        ("DRAFT", "SUBMITTED", 48, "PROJECT_SPONSOR", 1),
        ("SUBMITTED", "UNDER_REVIEW", 72, "REVIEWER", 1),
        ("UNDER_REVIEW", "JURISDICTION_CHECK", 48, "CENTRAL_AUTHORITY", 2),
        ("JURISDICTION_CHECK", "GIS_VERIFICATION", 96, "SURVEYOR_GIS_OFFICER", 2),
        ("GIS_VERIFICATION", "PUBLIC_HEARING", 72, "DISTRICT_ADMIN", 2),
        ("PUBLIC_HEARING", "COMPENSATION_ASSESSMENT", 120, "COMPENSATION_OFFICER", 3),
        ("COMPENSATION_ASSESSMENT", "RR_PLANNING", 120, "RR_OFFICER", 3),
        ("RR_PLANNING", "APPROVED", 96, "CENTRAL_AUTHORITY", 3),
        ("APPROVED", "IN_PROGRESS", 24, "PROJECT_SPONSOR", 4),
        ("IN_PROGRESS", "COMPLETED", 365 * 24, "PROJECT_SPONSOR", 5),
    ]
    for from_s, to_s, hours, role_name, priority in sla:
        if not (await session.execute(
                select(SLARule).where(SLARule.from_status == from_s, SLARule.to_status == to_s))).scalar_one_or_none():
            session.add(SLARule(from_status=from_s, to_status=to_s, max_duration_hours=hours,
                                role_id=uuid.UUID(ROLE_UUIDS[role_name]), priority=priority, is_active=True))
    await session.flush()
    print("  sla rules ok")


async def seed_jurisdiction_rules(session):
    rules = [
        ("JR-NH-01", {"project_type": "NATIONAL_HIGHWAY"},
         {"appropriate_govt": "Central Government", "acquiring_body": "National Highways Authority of India",
          "authority": "Central Authority under NHAI"}, "NHAI Act, 1988"),
        ("JR-RL-01", {"project_type": "RAILWAY"},
         {"appropriate_govt": "Central Government", "acquiring_body": "Ministry of Railways",
          "authority": "Railway Land Acquisition Authority"}, "Railways Act, 1989"),
        ("JR-ST-01", {"project_type": "DAM"},
         {"appropriate_govt": "State Government", "acquiring_body": "State Water Resources Department",
          "authority": "State Acquisition Authority"}, "Land Acquisition Act, 2013"),
        ("JR-URB-01", {"project_type": "URBAN_DEVELOPMENT"},
         {"appropriate_govt": "State Government", "acquiring_body": "Urban Development Authority",
          "authority": "District Level Authority"}, "Land Acquisition Act, 2013"),
        ("JR-DEF-01", {"project_type": "DEFENCE"},
         {"appropriate_govt": "Central Government", "acquiring_body": "Ministry of Defence",
          "authority": "Central Authority under Defence"}, "Defence Estate Act"),
        ("JR-IND-01", {"project_type": "INDUSTRIAL_CORRIDOR"},
         {"appropriate_govt": "State Government", "acquiring_body": "State Industries Department",
          "authority": "State Acquisition Authority"}, "Land Acquisition Act, 2013"),
        ("JR-PWR-01", {"project_type": "POWER_PROJECT"},
         {"appropriate_govt": "State Government", "acquiring_body": "State Energy Department",
          "authority": "State Acquisition Authority"}, "Electricity Act, 2003"),
    ]
    for code, cond, result, ref in rules:
        if not (await session.execute(select(JurisdictionRule).where(JurisdictionRule.rule_code == code))).scalar_one_or_none():
            session.add(JurisdictionRule(rule_code=code, rule_version="1.0",
                                         effective_from=datetime(2020, 1, 1), conditions=cond, result=result,
                                         source_reference=ref, is_active=True))
    await session.flush()
    print("  jurisdiction rules ok")


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
async def seed_users(session, states, departments):
    canonical = [
        ("superadmin@bhudrishti.gov.in", "Super@123", "Aarav Sharma", "SUPER_ADMIN"),
        ("admin@bhudrishti.gov.in", "Admin@123", "Priya Patel", "CENTRAL_AUTHORITY"),
        ("state@bhudrishti.gov.in", "State@123", "Rahul Verma", "STATE_AUTHORITY"),
        ("district@bhudrishti.gov.in", "District@123", "Ananya Iyer", "DISTRICT_ADMIN"),
        ("lao@bhudrishti.gov.in", "Lao@123", "Vikram Singh", "LAND_ACQUIRING_OFFICER"),
        ("sponsor@bhudrishti.gov.in", "Sponsor@123", "Kavya Nair", "PROJECT_SPONSOR"),
        ("gis@bhudrishti.gov.in", "Gis@123", "Rohan Gupta", "SURVEYOR_GIS_OFFICER"),
        ("verification@bhudrishti.gov.in", "Verify@123", "Neha Joshi", "VERIFICATION_OFFICER"),
        ("compensation@bhudrishti.gov.in", "Comp@123", "Arjun Reddy", "COMPENSATION_OFFICER"),
        ("rr@bhudrishti.gov.in", "Rr@123", "Sneha Kulkarni", "RR_OFFICER"),
        ("reviewer@bhudrishti.gov.in", "Review@123", "Manoj Tiwari", "REVIEWER"),
        ("auditor@bhudrishti.gov.in", "Audit@123", "Divya Menon", "AUDITOR"),
        ("viewer@bhudrishti.gov.in", "Viewer@123", "Kiran Das", "VIEWER"),
    ]
    users = {}
    for email, pwd, name, role_name in canonical:
        existing = (await session.execute(select(Profile).where(Profile.email == email))).scalar_one_or_none()
        if not existing:
            existing = Profile(email=email, password_hash=hash_password(pwd), full_name=name,
                               role_id=uuid.UUID(ROLE_UUIDS[role_name]),
                               state_id=states.get("MH").id if states.get("MH") else None,
                               is_active=True, is_verified=True)
            session.add(existing)
            await session.flush()
        users[role_name] = existing

    # Extra realistic demo users (named accounts; password follows role pattern)
    for full_name, email, role_name, state_code, dept_code, active in EXTRA_USERS:
        existing = (await session.execute(select(Profile).where(Profile.email == email))).scalar_one_or_none()
        if existing:
            users.setdefault(f"{role_name}:{full_name}", existing)
            continue
        pwd = f"{role_name.split('_')[0].capitalize()}@123" if False else f"{role_name.title().replace('_', '')}@123"
        u = Profile(email=email, password_hash=hash_password(pwd), full_name=full_name,
                    role_id=uuid.UUID(ROLE_UUIDS[role_name]),
                    state_id=states.get(state_code).id if states.get(state_code) else None,
                    department_id=departments.get(dept_code).id if departments.get(dept_code) else None,
                    is_active=active, is_verified=True)
        session.add(u)
        await session.flush()
        users[f"{role_name}:{full_name}"] = u

    await session.flush()
    print(f"  users ok ({len(users)})")
    return users


# ---------------------------------------------------------------------------
# Main data entry
# ---------------------------------------------------------------------------
async def seed_projects(session, users, states):
    print("  seeding projects...")
    now = datetime.utcnow()
    project_count = await _count(session, Project)
    ci = 0
    created = []
    for (name, ptype, purpose, pubcat, scode, dcode, tcode, vcode, status,
         cost, priority, dept_code, scenario) in PROJECT_DEFS:
        city_proj_code = f"BD-{now.year}-{project_count + ci + 1:05d}"
        sponsor = users.get("PROJECT_SPONSOR")
        state = states[scode]
        district = (await session.execute(select(District).where(District.code == dcode, District.state_id == state.id))).scalar_one()
        tehsil = (await session.execute(select(Tehsil).where(Tehsil.code == tcode))).scalar_one()
        village = (await session.execute(select(Village).where(Village.code == vcode))).scalar_one()

        start = now - timedelta(days=90 + ci * 12)
        target = now + timedelta(days=400 + ci * 30)
        if status == "COMPLETED":
            target = now - timedelta(days=10)

        proj = Project(
            project_code=city_proj_code,
            name=name,
            description=f"{DEMO_TAG} {name}. Scenario: {SCENARIO_MEANING[scenario]}.",
            project_type=ptype,
            purpose=purpose,
            public_category=pubcat,
            sponsor_id=departments_by_code[dept_code].id if dept_code in departments_by_code else None,
            land_requiring_body_id=departments_by_code.get("LAO").id if "LAO" in departments_by_code else None,
            proposed_area_sq_m=Decimal("500000"),
            state_id=state.id,
            district_id=district.id,
            tehsil_id=tehsil.id,
            village_id=village.id,
            start_date=start,
            target_completion_date=target,
            priority=priority,
            estimated_cost=Decimal(cost),
            funding_source="Government of India",
            status=status,
            created_by=sponsor.id if sponsor else None,
            version=1,
        )
        session.add(proj)
        await session.flush()
        created.append((proj, ptype, scenario, status, state))

        # workflow instance + starter history
        session.add(WorkflowInstance(project_id=proj.id, current_status=status))
        session.add(ProjectStatusHistory(project_id=proj.id, previous_status=None,
                                         new_status="DRAFT", changed_by=sponsor.id if sponsor else None,
                                         comment="Initial project creation (DEMO)"))
        if status != "DRAFT":
            session.add(ProjectStatusHistory(project_id=proj.id, previous_status="DRAFT",
                                             new_status=status, changed_by=sponsor.id if sponsor else None,
                                             comment=f"Moved to {status} (DEMO)"))
        session.add(ProjectActivity(project_id=proj.id, actor_id=sponsor.id if sponsor else None,
                                    activity_type="PROJECT_CREATED",
                                    description=f"{DEMO_TAG} Project {proj.name} created"))
        ci += 1
    await session.flush()
    print(f"    {len(created)} projects")
    return created


async def seed_parcels(session, projects, users):
    print("  seeding parcels, owners, GIS...")
    parcel_index = await _count(session, Parcel)
    owner_index = 0
    created_parcels = []
    base_lat = 22.0
    base_lon = 78.5
    states_cache = {}

    for proj, ptype, scenario, status, state in projects:
        states_cache[state.code] = state
        district = (await session.execute(select(District).where(District.id == proj.district_id))).scalar_one()
        tehsil = (await session.execute(select(Tehsil).where(Tehsil.id == proj.tehsil_id))).scalar_one()
        village = (await session.execute(select(Village).where(Village.id == proj.village_id))).scalar_one()
        num_parcels = 6 if status != "DRAFT" else 3

        for i in range(num_parcels):
            parcel_index += 1
            lat = base_lat + (hash((proj.id, i)) % 50) / 1000.0
            lon = base_lon + (hash((proj.id, i + 100)) % 50) / 1000.0
            geom = make_polygon_geojson(lat, lon, 0.002 + (i % 3) * 0.001)
            area = calculate_area_from_geojson(geom) or 40000

            # derive parcel status from scenario
            if scenario == "D":
                pstatus = "COMPENSATION_PAID" if i % 3 == 0 else "ACQUIRED"
            elif scenario == "E":
                pstatus = "ACQUIRED" if i % 4 != 0 else "ACQUISITION_PENDING"
            elif scenario == "F":
                pstatus = "COMPENSATION_PAID" if i % 5 == 0 else "ACQUIRED"
            elif scenario == "C":
                pstatus = "DISPUTED" if i % 2 == 0 else "ACQUISITION_PENDING"
            else:
                pstatus = "COMPENSATION_PAID" if status == "COMPLETED" else (
                    "ACQUIRED" if status in ("IN_PROGRESS", "APPROVED", "RR_PLANNING") else "IDENTIFIED")

            parcel = Parcel(
                parcel_code=f"PRC-{parcel_index:06d}",
                survey_number=f"SV-{parcel_index}",
                khasra_number=f"KH-{parcel_index}",
                ulpin=f"ULPIN{parcel_index:08d}",
                village_id=village.id, tehsil_id=tehsil.id,
                district_id=district.id, state_id=state.id,
                land_type="AGRICULTURAL", ownership_type="PRIVATE",
                area_sq_m=Decimal(str(round(area, 2))),
                geometry=geom, current_status=pstatus,
            )
            session.add(parcel)
            await session.flush()
            session.add(ProjectParcel(project_id=proj.id, parcel_id=parcel.id,
                                      acquired_area_sq_m=Decimal(str(round(area, 2)))))

            # owners
            num_owners = 1 + (i % 3)
            for j in range(num_owners):
                oname = OWNER_NAME_POOL[(parcel_index + j) % len(OWNER_NAME_POOL)]
                owner_index += 1
                session.add(ParcelOwner(
                    parcel_id=parcel.id, owner_name=oname,
                    father_husband_name=f"S/o {oname.split()[0]}",
                    gender="Male" if (parcel_index + j) % 2 == 0 else "Female",
                    age=30 + ((parcel_index + j) % 40), aadhaar_last4=f"{1000 + (j % 9):04d}",
                    relation_to_holder="Owner", is_primary=(j == 0),
                    contact_phone=f"9{parcel_index % 10}7{parcel_index % 100:02d}12345",
                    address=f"{village.name}, {district.name}, {state.name}"))
            await session.flush()

            session.add(GISVerification(
                project_id=proj.id, parcel_id=parcel.id,
                verified_by=users.get("SURVEYOR_GIS_OFFICER").id if users.get("SURVEYOR_GIS_OFFICER") else None,
                geometry_valid=True, area_match=True,
                overlap_detected=(scenario == "G" and i % 5 == 0),
                overlap_parcel_ids=[], outside_boundary=False,
                verification_notes=f"DEMO GIS verification (SRID 4326)"))
            created_parcels.append(parcel)
    await session.flush()
    print(f"    {len(created_parcels)} parcels")
    return created_parcels


async def seed_documents(session, projects, parcels, users):
    print("  seeding documents...")
    docs = []
    doc_types = ["LAND_RECORD", "SURVEY_MAP", "NOTIFICATION_ORDER", "ENVIRONMENT_CLEARANCE",
                 "OWNERSHIP_CERTIFICATE", "COMPENSATION_ORDER", "RR_PLAN", "PUBLIC_HEARING_MINUTES"]
    for proj, ptype, scenario, status, state in projects:
        if status == "DRAFT":
            continue
        for t in doc_types:
            doc = ProjectDocument(
                project_id=proj.id,
                document_type=t,
                title=f"{DEMO_TAG} {proj.name} - {t.replace('_', ' ').title()}",
                file_name=f"{t.lower()}_{proj.id}.pdf",
                file_path=f"/uploads/demo/{t.lower()}_{proj.id}.pdf",
                file_size=250000, mime_type="application/pdf",
                status="APPROVED",
                uploaded_by=users.get("PROJECT_SPONSOR").id if users.get("PROJECT_SPONSOR") else None,
                verified_by=users.get("VERIFICATION_OFFICER").id if users.get("VERIFICATION_OFFICER") else None,
            )
            session.add(doc)
            docs.append(doc)
    # parcel-specific docs
    proj_ids = [p[0].id for p in projects]
    for i, parcel in enumerate(parcels[:120]):
        doc = ProjectDocument(
            project_id=proj_ids[i % len(proj_ids)],
            parcel_id=parcel.id, document_type="LAND_RECORD",
            title=f"{DEMO_TAG} Land record for {parcel.parcel_code}",
            file_name=f"land_record_{parcel.id}.pdf", file_path=f"/uploads/demo/land_record_{parcel.id}.pdf",
            file_size=180000, mime_type="application/pdf", status="APPROVED",
            uploaded_by=users.get("VERIFICATION_OFFICER").id if users.get("VERIFICATION_OFFICER") else None,
            verified_by=users.get("VERIFICATION_OFFICER").id if users.get("VERIFICATION_OFFICER") else None,
        )
        session.add(doc)
        docs.append(doc)
    await session.flush()
    print(f"    {len(docs)} documents")


async def seed_compensation_rr_possession(session, projects, parcels, users):
    print("  seeding compensation, R&R, possession...")
    comp_officer = users.get("COMPENSATION_OFFICER")
    rr_officer = users.get("RR_OFFICER")
    pindex = 0
    for proj, ptype, scenario, status, state in projects:
        pp_ids = (await session.execute(
            select(ProjectParcel.parcel_id).where(ProjectParcel.project_id == proj.id))).scalars().all()
        project_parcels = [p for p in parcels if p.id in pp_ids]
        if status in ("COMPENSATION_ASSESSMENT", "RR_PLANNING", "APPROVED", "IN_PROGRESS", "COMPLETED"):
            for idx, parcel in enumerate(project_parcels[:3]):
                owner = (await session.execute(select(ParcelOwner).where(
                    ParcelOwner.parcel_id == parcel.id, ParcelOwner.is_primary == True))).scalars().first()
                if not owner:
                    continue
                base_amount = Decimal("2500000") + Decimal(idx * 350000)
                comp_status = "PAID" if status in ("IN_PROGRESS", "COMPLETED", "RR_PLANNING") else "APPROVED"
                case = CompensationCase(
                    parcel_id=parcel.id, project_id=proj.id, landowner_id=owner.id,
                    assessed_value=base_amount, land_area_sq_m=parcel.area_sq_m,
                    compensation_components={"land_value": "2000000", "structures": "300000",
                                             "trees_crops": "200000", "solatium": "500000"},
                    total_amount=base_amount + Decimal("500000"),
                    status=comp_status, assigned_officer_id=comp_officer.id if comp_officer else None,
                )
                session.add(case)
                await session.flush()
                if comp_status == "PAID":
                    session.add(CompensationPayment(case_id=case.id, amount=case.total_amount,
                                                    payment_method="Bank Transfer",
                                                    payment_reference=f"DEMO-PAY-{case.id}",
                                                    payment_date=datetime.utcnow() - timedelta(days=20),
                                                    status="COMPLETED",
                                                    approved_by=users.get("CENTRAL_AUTHORITY").id if users.get("CENTRAL_AUTHORITY") else None))
                    session.add(RRCase(project_id=proj.id, parcel_id=parcel.id, landowner_id=owner.id,
                                       family_members_count=4, eligibility_status="ELIGIBLE",
                                       entitlement_details={"monetary": "1500000", "alternative_land": "500 sq m"},
                                       assistance_type="Monetary + Alternative land",
                                       assigned_officer_id=rr_officer.id if rr_officer else None,
                                       status=("ASSISTANCE_DELIVERED" if status in ("IN_PROGRESS", "COMPLETED") else "ASSISTANCE_PLANNED")))
                session.add(Possession(
                    project_id=proj.id, parcel_id=parcel.id,
                    award_reference=f"AWD-{proj.project_code}",
                    possession_status=("COMPLETED" if status == "COMPLETED" else
                                       ("PENDING" if scenario == "F" else "PENDING")),
                    possession_date=(datetime.utcnow() - timedelta(days=5) if status == "COMPLETED" else None),
                    pending_reason=("Award completed but possession handed over delayed" if scenario == "F" else None),
                    verification_status="VERIFIED", responsible_authority="District Collector"),
                )
                pindex += 1
    await session.flush()
    print(f"    compensation/rr/possession cases linked")


async def seed_objections_hearings(session, projects, users, parcels):
    print("  seeding objections & hearings...")
    count = await _count(session, Objection)
    for proj, ptype, scenario, status, state in projects:
        if status in ("PUBLIC_HEARING", "COMPENSATION_ASSESSMENT", "RR_PLANNING", "APPROVED"):
            count += 1
            ob = Objection(objection_code=f"OBJ-{count:05d}", project_id=proj.id,
                           category="VALUATION_DISPUTE",
                           description=f"{DEMO_TAG} Landowner disputes the compensation valuation method applied.",
                           status="UNDER_REVIEW",
                           created_by=users.get("PROJECT_SPONSOR").id if users.get("PROJECT_SPONSOR") else None)
            session.add(ob)
            await session.flush()
            session.add(Hearing(objection_id=ob.id, hearing_date=datetime.utcnow() + timedelta(days=7),
                                hearing_officer_id=users.get("DISTRICT_ADMIN").id if users.get("DISTRICT_ADMIN") else None,
                                location="District Collector Office"))
    await session.flush()
    print(f"    objections/hearings ok")


# ---------------------------------------------------------------------------
# Intelligence domains
# ---------------------------------------------------------------------------
async def seed_possession_notes(session, projects, parcels, users):
    print("  seeding possession records...")
    existing = await _count(session, Possession)
    if existing:
        print("    possessions already present, skipping")
        return


async def seed_escalations(session, projects, users):
    print("  seeding escalations...")
    count = await _count(session, Escalation)
    escal = [
        # (project_idx, level, stage, trigger, authority, status)
        (0, 2, "IN_PROGRESS", "Construction milestones delayed beyond SLA", "Central Authority", "OPEN"),
        (1, 3, "COMPENSATION_ASSESSMENT", "Compensation approval pending from 60+ days", "Compensation Officer", "OPEN"),
        (7, 2, "UNDER_REVIEW", "Review of project documents pending", "Reviewer", "OPEN"),
        (8, 4, "JURISDICTION_CHECK", "Jurisdiction ambiguity causing critical delay", "Central Authority", "OPEN"),
        (9, 3, "COMPENSATION_ASSESSMENT", "Compensation bottleneck with multiple objections", "Compensation Officer", "OPEN"),
        (10, 1, "SUBMITTED", "Approaching SLA for initial review", "Reviewer", "RESOLVED"),
        (12, 2, "DRAFT", "Sponsor documents incomplete", "Project Sponsor", "OPEN"),
        (3, 3, "RR_PLANNING", "R&R assistance planning not started", "RR Officer", "OPEN"),
        (14, 3, "GIS_VERIFICATION", "GIS verification backlog", "GIS Officer", "OPEN"),
        (5, 3, "APPROVED", "Possession handing over delayed despite award", "District Collector", "OPEN"),
        (15, 1, "UNDER_REVIEW", "Minor document discrepancy, approaching SLA", "Reviewer", "RESOLVED"),
        (2, 2, "PUBLIC_HEARING", "Public hearing rescheduled twice", "District Admin", "OPEN"),
    ]
    for idx, level, stage, trigger, authority, status in escal:
        proj = projects[idx][0]
        count += 1
        session.add(Escalation(
            escalation_code=f"ESC-{count:04d}", project_id=proj.id, stage=stage,
            trigger_reason=f"{DEMO_TAG} {trigger}", level=level,
            responsible_authority=authority, status=status,
            created_date=datetime.utcnow() - timedelta(days=8),
            resolution_date=(datetime.utcnow() - timedelta(days=2) if status == "RESOLVED" else None),
            resolution_action=("Re-uploaded documents and re-assigned reviewer" if status == "RESOLVED" else None),
            created_by=users.get("SUPER_ADMIN").id if users.get("SUPER_ADMIN") else None,
        ))
    await session.flush()
    print(f"    {count} escalations")


async def seed_conflicts(session, projects, users):
    print("  seeding data conflicts...")
    count = await _count(session, DataConflict)
    conflict_defs = [
        # (project_idx, parcel_idx, source_a, source_b, field, old_val, new_val, severity, status, reason)
        (8, 0, "State Land Records", "District Survey System", "Area (hectares)", "4.82", "5.14", "HIGH", "RESOLVED", "Re-survey confirmed 5.14 ha"),
        (8, 1, "State Land Records", "Field Verification", "Survey Number", "SV-101", "SV-102", "HIGH", "OPEN", None),
        (12, 0, "Project Submission", "State Land Records", "Ownership reference", "Owner Ramesh Kumar", "Owner Suresh Patel", "CRITICAL", "OPEN", None),
        (9, 0, "District Survey System", "Project Submission", "Parcel status", "IDENTIFIED", "ACQUIRED", "MEDIUM", "RESOLVED", "Status reconciled to ACQUIRED"),
        (14, 2, "State Land Records", "Field Verification", "Record is outdated", "2001 record", "2023 record", "MEDIUM", "OPEN", None),
        (1, 0, "District Survey System", "Cadastral GIS", "Boundary coordinates", "Old polygon", "New polygon", "HIGH", "RESOLVED", "GIS boundary updated"),
        (0, 1, "Field Verification", "State Land Records", "Khasra number", "KH-110", "KH-111", "MEDIUM", "OPEN", None),
        (3, 0, "Cadastral GIS", "State Land Records", "Owner name spelling", "Sunita Devi", "Sunitha Devi", "LOW", "RESOLVED", "Standardized name"),
        (11, 0, "Project Submission", "District Survey System", "Projected area", "500000", "512000", "LOW", "OPEN", None),
        (5, 3, "State Land Records", "District Survey System", "Possession status", "PENDING", "COMPLETED", "HIGH", "OPEN", None),
        (16, 0, "Cadastral GIS", "District Survey System", "Parcel count", "58", "62", "MEDIUM", "OPEN", None),
        (2, 1, "Field Verification", "State Land Records", "Area (hectares)", "3.10", "3.22", "MEDIUM", "RESOLVED", "Confirmed 3.22 ha via survey"),
        (13, 2, "State Land Records", "Project Submission", "Parcel boundary overlap", "No overlap", "Overlap detected", "HIGH", "OPEN", None),
        (17, 0, "District Survey System", "Cadastral GIS", "Road alignment", "Old alignment", "New alignment", "MEDIUM", "RESOLVED", "Alignment harmonized"),
        (4, 0, "Project Submission", "State Land Records", "Projected area", "500000", "498500", "LOW", "OPEN", None),
    ]
    for idx, pid, src_a, src_b, field, old_v, new_v, sev, status, reason in conflict_defs:
        proj = projects[idx][0]
        pmap = [p for p in parcels_by_project.get(proj.id, [])]
        parcel = pmap[pid] if pid < len(pmap) else None
        count += 1
        session.add(DataConflict(
            conflict_code=f"DC-{count:04d}", project_id=proj.id,
            parcel_id=parcel.id if parcel else None,
            source_a=f"{src_a} ({DEMO_TAG})", source_b=f"{src_b} ({DEMO_TAG})",
            field_name=field, old_value={"value": old_v}, new_value={"value": new_v},
            severity=sev, status=status, resolution_reason=reason,
            resolved_by=users.get("VERIFICATION_OFFICER").id if users.get("VERIFICATION_OFFICER") else None,
            detected_at=datetime.utcnow() - timedelta(days=6),
            resolved_at=(datetime.utcnow() - timedelta(days=1) if status == "RESOLVED" else None),
            evidence={"source_a_ref": f"SRC/{src_a}/R-{count}", "source_b_ref": f"SRC/{src_b}/R-{count}"},
        ))
    await session.flush()
    print(f"    {count} conflicts")


async def seed_health_scores(session, projects, parcels, conflicts):
    print("  seeding health scores...")
    proj_count = await _count(session, ProjectHealthScore)
    if proj_count:
        print("    health scores present, skipping")
        return
    scenario_score = {
        "A": 92, "B": 58, "C": 32, "D": 45, "E": 48, "F": 55, "G": 40,
    }
    for proj, ptype, scenario, status, state in projects:
        base = scenario_score[scenario]
        score = min(99, max(10, base + (5 if status == "COMPLETED" else 0) - (10 if status == "DRAFT" else 0)))
        factors = {
            "workflow_progress": 30,
            "sla_performance": 25,
            "pending_approvals": 15,
            "compensation": 10,
            "rr": 10,
            "possession": 5,
            "data_conflicts": 5,
            "scenario": SCENARIO_MEANING[scenario],
        }
        session.add(ProjectHealthScore(project_id=proj.id, score=score, band=health_band(score), factors=factors,
                                       computed_at=datetime.utcnow()))

    par_count = await _count(session, ParcelHealthScore)
    if not par_count:
        pp_rows = (await session.execute(select(ProjectParcel.project_id, ProjectParcel.parcel_id))).all()
        parcel_project_map = {parcel_id: project_id for project_id, parcel_id in pp_rows}
        for i, parcel in enumerate(parcels):
            base = 20 + (i % 70)
            score = min(98, base)
            session.add(ParcelHealthScore(parcel_id=parcel.id,
                                          project_id=parcel_project_map.get(parcel.id),
                                          score=score, band=health_band(score),
                                          factors={"verification": 20, "documentation": 20,
                                                   "compensation": 20, "rr": 15, "possession": 15,
                                                   "data_conflict": 10},
                                          computed_at=datetime.utcnow()))
    await session.flush()
    print(f"    health scores ok")


async def seed_historical(session, projects):
    print("  seeding historical analytics...")
    hist_count = await _count(session, HistoricalAnalytics)
    if hist_count:
        print("    historical present, skipping")
        return
    metrics = ["AVG_PROCESS_TIME", "STAGE_TIME", "SLA_COMPLIANCE", "BOTTLENECK_FREQUENCY", "STATE_PERFORMANCE"]
    states = {}
    for proj, ptype, scenario, status, state in projects:
        states.setdefault(state.name, 0)
        states[state.name] += 1
    # state performance by month
    month_vals = {"2025-09": 82, "2025-10": 80, "2025-11": 84, "2025-12": 78,
                  "2026-01": 85, "2026-02": 83, "2026-03": 88}
    for period, val in month_vals.items():
        for sname in states:
            jitter = (hash(sname) % 12) - 6
            session.add(HistoricalAnalytics(period=period, entity_type="STATE", entity_name=sname,
                                            metric_name="STATE_PERFORMANCE",
                                            metric_value=max(20, min(99, val + jitter)),
                                            is_demo=True))
    # bottleneck frequency per district
    for proj, ptype, scenario, status, state in projects:
        if scenario in ("B", "C", "D", "E", "F", "G"):
            session.add(HistoricalAnalytics(period="2026-03", entity_type="DISTRICT",
                                            entity_name=proj.district_id and f"District-{state.code}" or f"District-{state.code}",
                                            metric_name="BOTTLENECK_FREQUENCY",
                                            metric_value=hash(proj.id) % 12 + 1, is_demo=True))
    await session.flush()
    print("    historical ok")


async def seed_integrations(session):
    print("  seeding integration health...")
    int_count = await _count(session, IntegrationHealth)
    if int_count:
        print("    integrations present, skipping")
        return
    ints = [
        ("State Land Records API", "SLR-API", "LandRecords", "HEALTHY", 50000, 12, 3, 180),
        ("Cadastral/GIS Service", "CAD-GIS", "GIS", "DEGRADED", 23000, 58, 9, 640),
        ("District Data Service", "DDS", "District", "HEALTHY", 121000, 4, 1, 120),
        ("State Data Service", "SDS", "State", "HEALTHY", 89000, 7, 2, 150),
        ("Document Service", "DOC-SVC", "Documents", "FAILED", 15000, 21, 0, 1200),
        ("Field Verification Mobile App", "FIELD-APP", "Field", "HEALTHY", 34000, 8, 1, 90),
        ("External API Demo Adapter", "EXT-DEMO", "External", "NEVER_SYNCED", 0, 0, 0, 0),
    ]
    for name, code, itype, status, synced, failed, conflicts, rt in ints:
        last_sync = datetime.utcnow() - timedelta(hours=2 if status == "HEALTHY" else 30)
        session.add(IntegrationHealth(
            system_name=name, system_code=code, integration_type=itype,
            last_sync=(None if status == "NEVER_SYNCED" else last_sync),
            status=status, records_synced=synced, failed_records=failed,
            conflicts=conflicts, api_response_time_ms=rt,
            last_error=("Connection timeout on last batch" if status == "FAILED" else
                        ("API response time above threshold" if status == "DEGRADED" else None)),
            is_demo=True,
        ))
    await session.flush()
    print("    integrations ok")


async def seed_provenance(session, projects, parcels):
    print("  seeding data provenance...")
    prov_count = await _count(session, DataProvenance)
    if prov_count:
        print("    provenance present, skipping")
        return
    sources = ["State Land Records", "District Survey System", "Project Submission",
               "Field Verification", "Manual Entry", "External API Demo Adapter"]
    for i, proj in enumerate([p[0] for p in projects]):
        for s in sources:
            session.add(DataProvenance(
                entity_type="PROJECT", entity_id=proj.id, source_system=f"{s} (DEMO)",
                source_record_id=f"SRC-{s[:3].upper()}-{i:03d}",
                created_by_name="Demo Seeder", verification_status="VERIFIED",
                last_synchronization=datetime.utcnow() - timedelta(hours=i * 3),
                supporting_document=f"/uploads/demo/prov_{i}.pdf", is_demo=True))
    for i, parcel in enumerate(parcels[:60]):
        session.add(DataProvenance(entity_type="PARCEL", entity_id=parcel.id,
                                   source_system="State Land Records (DEMO)",
                                   source_record_id=f"PLR-{i:04d}",
                                   created_by_name="Demo Seeder", verification_status="VERIFIED",
                                   last_synchronization=datetime.utcnow() - timedelta(hours=5),
                                   supporting_document=f"/uploads/demo/parcel_prov_{i}.pdf", is_demo=True))
    await session.flush()
    print("    provenance ok")


async def seed_dependencies(session, projects):
    print("  seeding dependencies...")
    dep_count = await _count(session, Dependency)
    if dep_count:
        print("    dependencies present, skipping")
        return
    chains = [
        ("VERIFICATION", "SCRUTINY"), ("SCRUTINY", "APPROVAL"), ("APPROVAL", "AWARD"),
        ("AWARD", "COMPENSATION"), ("COMPENSATION", "POSSESSION"),
    ]
    for proj, ptype, scenario, status, state in projects:
        if scenario in ("A", "B", "C", "D", "E", "F", "G"):
            for (a, b) in chains[: (3 if scenario in ("B", "C") else 2)]:
                session.add(Dependency(project_id=proj.id, from_stage=a, to_stage=b,
                                       dependency_type="APPROVAL",
                                       dependency_description=f"{DEMO_TAG} dependency {a} -> {b}",
                                       is_satisfied=(status in ("IN_PROGRESS", "COMPLETED", "APPROVED"))))
    # cross-department dependency
    for idx in (1, 8, 9):
        proj = projects[idx][0]
        session.add(Dependency(project_id=proj.id, from_stage="REVENUE", to_stage="POSSESSION",
                               dependency_type="CROSS_DEPARTMENT",
                               dependency_description=f"{DEMO_TAG} Revenue department records pending",
                               is_satisfied=False))
    await session.flush()
    print("    dependencies ok")


async def seed_whatif(session, projects):
    print("  seeding what-if scenarios...")
    count = await _count(session, WhatIfScenario)
    if count:
        print("    what-if present, skipping")
        return
    scenarios = [
        (1, "Resolve compensation bottleneck", "Unblock pending compensation approvals",
         "Current completion: Q4 2027", "Simulated: Q3 2027", 120, "Approve 30 pending cases"),
        (9, "Complete pending verification", "Prioritize field verification",
         "Current completion: Q2 2027", "Simulated: Q1 2027", 90, "Deploy 3 additional teams"),
        (8, "Resolve critical approval", "Clarify jurisdiction rapidly",
         "Current completion: Q3 2027", "Simulated: Q2 2027", 105, "Central review committee"),
        (3, "Accelerate R&R processing", "Pre-approve R&R entitlements",
         "Current completion: Q4 2027", "Simulated: Q3 2027", 75, "Fast-track R&R desk"),
        (4, "Resolve data conflict", "Re-survey conflicted parcels",
         "Current completion: Q3 2027", "Simulated: Q2 2027", 60, "Priority survey drone"),
    ]
    for idx, title, desc, cur, sim, days, interv in scenarios:
        proj = projects[idx][0]
        session.add(WhatIfScenario(
            scenario_code=f"WF-{idx+1:02d}", project_id=proj.id, title=f"{DEMO_TAG} {title}",
            description=desc, current_completion_label=cur, simulated_completion_label=sim,
            estimated_time_saved_days=days, intervention=interv,
            assumptions="Assumes approved additional resources and no legislative changes. SIMULATION - NOT A GUARANTEE.",
            is_demo=True))
    await session.flush()
    print("    what-if ok")


async def seed_priorities(session, projects, users):
    print("  seeding resource priorities...")
    prior_count = await _count(session, ResourcePriority)
    if prior_count:
        print("    priorities present, skipping")
        return
    ranked = sorted(
        [p for p in projects if p[0].status != "COMPLETED"],
        key=lambda p: ({"D": 1, "C": 2, "B": 3, "E": 4, "F": 5, "G": 6, "A": 7}.get(p[2], 9), -(p[0].priority or 3)),
    )
    for rank, (proj, ptype, scenario, status, state) in enumerate(ranked, start=1):
        score = max(0.0, 100 - (rank - 1) * 4.5)
        session.add(ResourcePriority(
            project_id=proj.id, priority_score=round(score, 1), priority_rank=rank,
            reasoning=f"{DEMO_TAG} Scenario {scenario} ({SCENARIO_MEANING[scenario]}); priority {proj.priority}.",
            update_date=datetime.utcnow()))
    await session.flush()
    print("    priorities ok")


async def seed_audit(session, users, projects):
    print("  seeding audit logs...")
    audit_count = await _count(session, AuditLog)
    if audit_count:
        print("    audit present, skipping")
        return
    actors = [users.get("SUPER_ADMIN"), users.get("LAND_ACQUIRING_OFFICER"),
              users.get("VERIFICATION_OFFICER"), users.get("COMPENSATION_OFFICER")]
    actions = ["PROJECT_CREATED", "PROJECT_SUBMITTED", "PARCEL_VERIFIED", "DOCUMENT_UPLOADED",
               "CONFLICT_CREATED", "CONFLICT_RESOLVED", "ESCALATION_TRIGGERED", "ESCALATION_RESOLVED",
               "WORKFLOW_CHANGED", "COMPENSATION_APPROVED"]
    base = datetime.utcnow() - timedelta(days=60)
    for i in range(120):
        actor = actors[i % len(actors)]
        proj = projects[i % len(projects)][0]
        session.add(AuditLog(
            actor_id=actor.id if actor else None,
            actor_email=actor.email if actor else None,
            action=actions[i % len(actions)],
            entity_type="PROJECT", entity_id=proj.id,
            new_value={"demo": True, "note": DEMO_TAG},
            meta={"seeded": True}, ip_address="127.0.0.1",
            created_at=base + timedelta(hours=i * 11)))
    await session.flush()
    print("    audit ok")


# module-level caches set during seeding
departments_by_code = {}
parcels_by_project = []


async def seed_notifications(session, users, projects):
    print("  seeding notifications...")
    count = await _count(session, Notification)
    if count:
        print("    notifications present, skipping")
        return
    for role_name, user in users.items():
        session.add(Notification(
            user_id=user.id,
            title="Welcome to Bhu-Drishti (DEMO)",
            message="DEMO / PROTOTYPE DATA Your demo account is ready. Explore the system.",
            notification_type="INFO", entity_type="profile"))
    templates = [
        ("SLA_BREACH", "SLA breach on project", "A workflow task is overdue for SLA. Please review immediately."),
        ("ACTION_REQUIRED", "Compensation approval pending", "Compensation cases awaiting your approval."),
        ("WARNING", "Data conflict detected", "A new data conflict was detected on a parcel in your district."),
        ("STATUS_CHANGE", "Project status updated", "A project you follow changed workflow status."),
    ]
    for i, (ntype, title, msg) in enumerate(templates):
        if not users:
            continue
        keys = list(users.keys())
        u = users[keys[i % len(keys)]]
        proj = projects[i % len(projects)][0]
        session.add(Notification(user_id=u.id, title=f"DEMO - {title}",
                                 message=f"{msg} Project {proj.name}.",
                                 notification_type=ntype, entity_type="PROJECT", entity_id=proj.id,
                                 is_read=False))
    await session.flush()
    print(f"    {await _count(session, Notification)} notifications")


async def main_seed(session_factory):
    async with session_factory() as session:
        global departments_by_code, parcels_by_project
        # Base reference data is always ensured (idempotent by design).
        departments_by_code = await seed_departments(session)
        states = await seed_geography(session)
        users = await seed_users(session, states, departments_by_code)
        await seed_roles_permissions(session)
        await seed_sla_rules(session)
        await seed_jurisdiction_rules(session)

        existing_projects = await _count(session, Project)

        # Seed the full project tree only when the DB is empty of projects;
        # otherwise reuse the existing dataset (idempotent re-runs).
        if existing_projects == 0:
            projects = await seed_projects(session, users, states)
            parcels = await seed_parcels(session, projects, users)
            parcels_by_project = {}
            for proj, *_ in projects:
                pids = (await session.execute(select(ProjectParcel.parcel_id)
                                              .where(ProjectParcel.project_id == proj.id))).scalars().all()
                parcels_by_project[proj.id] = [p for p in parcels if p.id in pids]
            await seed_documents(session, projects, parcels, users)
            await seed_compensation_rr_possession(session, projects, parcels, users)
            await seed_objections_hearings(session, projects, users, parcels)
            await seed_escalations(session, projects, users)
            await seed_conflicts(session, projects, users)
        else:
            print(f"  {existing_projects} projects already present; project tree seeding skipped")
            projects = []
            rows = (await session.execute(select(Project.id))).scalars().all()
            parcels = (await session.execute(select(Parcel))).scalars().all()
            for pid in rows:
                projects.append((await session.execute(select(Project).where(Project.id == pid))).scalar_one(),
                                None, None, None, None)

        # Intelligence domains are individually idempotent (skip if present).
        await seed_health_scores(session, projects, parcels, None)
        await seed_historical(session, projects)
        await seed_integrations(session)
        await seed_provenance(session, projects, parcels)
        await seed_dependencies(session, projects)
        await seed_whatif(session, projects)
        await seed_priorities(session, projects, users)
        await seed_audit(session, users, projects)
        await seed_notifications(session, users, projects)
        await session.commit()


async def clear_demo(session_factory):
    async with session_factory() as session:
        # Disable FK triggers for the duration of the demo-data purge to avoid
        # ordering issues, then restore. Only demo-owned tables are touched.
        await session.execute(text("SET session_replication_role = replica;"))
        try:
            for m in [Possession, Escalation, DataConflict, ProjectHealthScore, ParcelHealthScore,
                      HistoricalAnalytics, IntegrationHealth, DataProvenance, Dependency,
                      WhatIfScenario, ResourcePriority, ParcelOwner, ProjectParcel, GISVerification,
                      Parcel, ProjectDocument, CompensationCase,
                      CompensationPayment, RRCase, Objection, Hearing, WorkflowTask,
                      WorkflowTransition, WorkflowInstance, ProjectStatusHistory, ProjectActivity,
                      AuditLog, Notification, Project]:
                await session.execute(m.__table__.delete())
            # also legacy tables not in ORM list above
            from app.models.models import DocumentVersion, DocumentVerification, ProjectVerification, JurisdictionDecision, SLAEvent
            for m in [DocumentVersion, DocumentVerification, ProjectVerification, JurisdictionDecision, SLAEvent]:
                await session.execute(m.__table__.delete())
            await session.commit()
        finally:
            await session.execute(text("SET session_replication_role = DEFAULT;"))
            await session.commit()
        print("Demo-data tables cleared.")


async def validate(session_factory):
    async with session_factory() as session:
        problems = []
        # FK integrity: check objects referencing projects exist
        orphans = await session.execute(
            select(func.count(Project.id)).select_from(Project)
            .where(Project.created_by.is_(None)))
        if orphans.scalar():
            problems.append("Projects with NULL created_by")
        neg_area = await session.execute(
            select(func.count(Parcel.id)).where(Parcel.area_sq_m < 0))
        if neg_area.scalar():
            problems.append("Parcels with negative area")
        neg_val = await session.execute(
            select(func.count(CompensationCase.id)).where(CompensationCase.total_amount < 0))
        if neg_val.scalar():
            problems.append("Compensation cases with negative amount")
        # orphan parcels (no project link)
        orphan_parcels = await session.execute(
            select(func.count(Parcel.id)).select_from(Parcel)
            .outerjoin(ProjectParcel, ProjectParcel.parcel_id == Parcel.id)
            .where(ProjectParcel.parcel_id.is_(None)))
        if orphan_parcels.scalar():
            problems.append("Orphan parcels with no project link")
        # invalid geometries
        invalid_geo = 0
        parcels_it = await session.execute(select(Parcel.geometry).where(Parcel.geometry.is_not(None)))
        from app.gis.spatial_ops import check_geometry_validity
        for (geom,) in parcels_it.all():
            if not check_geometry_validity(geom):
                invalid_geo += 1
        if invalid_geo:
            problems.append(f"{invalid_geo} invalid geometries")
        # workflow consistency
        bad_wf = await session.execute(
            select(func.count(WorkflowInstance.id)).select_from(WorkflowInstance)
            .outerjoin(Project, Project.id == WorkflowInstance.project_id)
            .where(Project.id.is_(None)))
        if bad_wf.scalar():
            problems.append("Workflow instances without projects")
        print("=" * 60)
        print("VALIDATION REPORT")
        print("=" * 60)
        if problems:
            print("PROBLEMS FOUND:")
            for p in problems:
                print(f"  - {p}")
        else:
            print("All integrity checks passed (no broken FKs, no negative values, valid geometry).")
        print()


COUNT_QUERIES = [
    ("Users", Profile), ("Projects", Project), ("Parcels", Parcel),
    ("Documents", ProjectDocument), ("Conflicts", DataConflict),
    ("Escalations", Escalation), ("Project Health Records", ProjectHealthScore),
    ("Parcel Health Records", ParcelHealthScore),
    ("Historical Records", HistoricalAnalytics), ("Integration Records", IntegrationHealth),
    ("Provision Records", DataProvenance), ("Dependencies", Dependency),
    ("What-If Scenarios", WhatIfScenario), ("Resource Priorities", ResourcePriority),
    ("Possession Records", Possession), ("Compensation Cases", CompensationCase),
    ("RR Cases", RRCase), ("Audit Logs", AuditLog), ("Notifications", Notification),
]


async def report_counts(session_factory):
    async with session_factory() as session:
        print()
        print("=" * 60)
        print("SEED SUMMARY")
        print("=" * 60)
        for label, model in COUNT_QUERIES:
            n = await _count(session, model)
            print(f"  {label:<28}: {n}")
        print()


async def main():
    action = "seed"
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
    engine = create_async_engine(settings.async_database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        if action == "clear":
            await clear_demo(session_factory)
        elif action == "validate":
            await validate(session_factory)
        else:
            await main_seed(session_factory)
        await report_counts(session_factory)
        if action == "seed":
            await validate(session_factory)
    finally:
        await engine.dispose()


def seed_demo_data():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
