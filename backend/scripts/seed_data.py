import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.models.models import (
    Base, Role, Permission, RolePermission, Department, State, District, Tehsil,
    Village, Profile, Project, ProjectStatusHistory, Parcel, ParcelOwner,
    ProjectParcel, ProjectDocument, JurisdictionRule, SLARule, WorkflowInstance,
    WorkflowTask, WorkflowTransition, CompensationCase, CompensationPayment,
    RRCase, Objection, Hearing, GISVerification, AuditLog, ProjectActivity,
    Notification,
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


async def create_roles_permissions(session):
    print("Creating roles and permissions...")
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
        existing = (await session.execute(
            select(Role).where(Role.name == name)
        )).scalar_one_or_none()
        if not existing:
            session.add(Role(
                id=uuid.UUID(ROLE_UUIDS[name]),
                name=name,
                description=desc,
            ))
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
    }

    permission_ids = {}
    for module, perms in modules.items():
        for perm_name in perms:
            existing = (await session.execute(
                select(Permission).where(Permission.name == perm_name)
            )).scalar_one_or_none()
            if not existing:
                perm = Permission(name=perm_name, module=module)
                session.add(perm)
                await session.flush()
                permission_ids[perm_name] = perm.id
            else:
                permission_ids[perm_name] = existing.id

    all_perms = list(permission_ids.values())

    for name in role_defs:
        role_id = uuid.UUID(ROLE_UUIDS[name])
        existing_rp = (await session.execute(
            select(RolePermission).where(RolePermission.role_id == role_id)
        )).scalars().all()
        if not existing_rp:
            for perm_id in all_perms:
                session.add(RolePermission(role_id=role_id, permission_id=perm_id))
    await session.flush()


async def create_departments(session):
    print("Creating departments...")
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
    for name, code, level in dept_data:
        existing = (await session.execute(
            select(Department).where(Department.code == code)
        )).scalar_one_or_none()
        if not existing:
            session.add(Department(name=name, code=code, level=level))
    await session.flush()


async def create_geography(session):
    print("Creating states, districts, tehsils, villages...")
    state_data = [
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
        ("Rajasthan", "RJ", [
            ("Jaipur", "JAI", [("Jaipur City", "JAIC", "302001"), ("Amer", "AME", "303104")]),
            ("Jodhpur", "JOD", [("Jodhpur City", "JODC", "342001"), ("Osian", "OSI", "342303")]),
        ]),
        ("Tamil Nadu", "TN", [
            ("Chennai", "CHE", [("Chennai Central", "CHEC", "600001"), ("Tambaram", "TAM", "600045")]),
            ("Coimbatore", "COI", [("Coimbatore City", "COIC", "641001"), ("Pollachi", "POL", "642001")]),
        ]),
    ]

    for state_name, state_code, districts in state_data:
        result = await session.execute(
            select(State).where(State.code == state_code)
        )
        state = result.scalar_one_or_none()
        if not state:
            state = State(name=state_name, code=state_code)
            session.add(state)
            await session.flush()
        for dist_name, dist_code, tehsils in districts:
            result = await session.execute(
                select(District).where(District.code == dist_code, District.state_id == state.id)
            )
            district = result.scalar_one_or_none()
            if not district:
                district = District(name=dist_name, code=dist_code, state_id=state.id)
                session.add(district)
                await session.flush()
            for teh_name, teh_code, pin in tehsils:
                result = await session.execute(
                    select(Tehsil).where(Tehsil.code == teh_code, Tehsil.district_id == district.id)
                )
                tehsil = result.scalar_one_or_none()
                if not tehsil:
                    tehsil = Tehsil(name=teh_name, code=teh_code, district_id=district.id)
                    session.add(tehsil)
                    await session.flush()
                result = await session.execute(
                    select(Village).where(Village.name == teh_name, Village.tehsil_id == tehsil.id)
                )
                if not result.scalar_one_or_none():
                    session.add(Village(name=teh_name, code=f"V{teh_code}", tehsil_id=tehsil.id, pin_code=pin))
    await session.flush()


async def create_users(session):
    print("Creating demo users...")
    user_defs = [
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

    result = await session.execute(select(State).where(State.code == "MH"))
    mh = result.scalar_one_or_none()

    users = {}
    for email, pwd, name, role_name in user_defs:
        existing = (await session.execute(
            select(Profile).where(Profile.email == email)
        )).scalar_one_or_none()
        if existing:
            users[role_name] = existing
            continue
        role_id = uuid.UUID(ROLE_UUIDS[role_name])
        user = Profile(
            email=email,
            password_hash=hash_password(pwd),
            full_name=name,
            role_id=role_id,
            state_id=mh.id if mh else None,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.flush()
        users[role_name] = user
    return users


async def create_jurisdiction_rules(session):
    print("Creating jurisdiction rules...")
    rules = [
        {
            "rule_code": "JR-NH-01",
            "conditions": {"project_type": "NATIONAL_HIGHWAY"},
            "result": {
                "appropriate_govt": "Central Government",
                "acquiring_body": "National Highways Authority of India",
                "authority": "Central Authority under NHAI",
            },
            "source_reference": "NHAI Act, 1988",
        },
        {
            "rule_code": "JR-RL-01",
            "conditions": {"project_type": "RAILWAY"},
            "result": {
                "appropriate_govt": "Central Government",
                "acquiring_body": "Ministry of Railways",
                "authority": "Railway Land Acquisition Authority",
            },
            "source_reference": "Railways Act, 1989",
        },
        {
            "rule_code": "JR-ST-01",
            "conditions": {"project_type": "DAM"},
            "result": {
                "appropriate_govt": "State Government",
                "acquiring_body": "State Water Resources Department",
                "authority": "State Acquisition Authority",
            },
            "source_reference": "Land Acquisition Act, 2013",
        },
        {
            "rule_code": "JR-URB-01",
            "conditions": {"project_type": "URBAN_DEVELOPMENT"},
            "result": {
                "appropriate_govt": "State Government",
                "acquiring_body": "Urban Development Authority",
                "authority": "District Level Authority",
            },
            "source_reference": "Land Acquisition Act, 2013",
        },
        {
            "rule_code": "JR-DEF-01",
            "conditions": {"project_type": "DEFENCE"},
            "result": {
                "appropriate_govt": "Central Government",
                "acquiring_body": "Ministry of Defence",
                "authority": "Central Authority under Defence",
            },
            "source_reference": "Defence Estate Act",
        },
    ]
    for r in rules:
        existing = (await session.execute(
            select(JurisdictionRule).where(JurisdictionRule.rule_code == r["rule_code"])
        )).scalar_one_or_none()
        if not existing:
            session.add(JurisdictionRule(
                rule_code=r["rule_code"],
                rule_version="1.0",
                effective_from=datetime(2020, 1, 1),
                conditions=r["conditions"],
                result=r["result"],
                source_reference=r["source_reference"],
                is_active=True,
            ))
    await session.flush()


async def create_sla_rules(session):
    print("Creating SLA rules...")
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
        result = await session.execute(
            select(SLARule).where(
                SLARule.from_status == from_s,
                SLARule.to_status == to_s,
            )
        )
        if not result.scalar_one_or_none():
            session.add(SLARule(
                from_status=from_s, to_status=to_s,
                max_duration_hours=hours,
                role_id=uuid.UUID(ROLE_UUIDS[role_name]),
                priority=priority, is_active=True,
            ))
    await session.flush()


async def create_projects(session, users):
    print("Creating demo projects and parcels...")
    result = await session.execute(select(State).where(State.code == "MH"))
    mh = result.scalar_one_or_none()
    result = await session.execute(select(District).where(District.code == "MUM", District.state_id == mh.id))
    mumbai = result.scalar_one_or_none()
    result = await session.execute(select(Tehsil).where(Tehsil.code == "MUMC"))
    mumbai_tehsil = result.scalar_one_or_none()
    result = await session.execute(select(Village).where(Village.code == "VMUMC"))
    mumbai_village = result.scalar_one_or_none()

    result = await session.execute(select(District).where(District.code == "PUN", District.state_id == mh.id))
    pune = result.scalar_one_or_none()
    result = await session.execute(select(Tehsil).where(Tehsil.code == "PUNC"))
    pune_tehsil = result.scalar_one_or_none()
    result = await session.execute(select(Village).where(Village.code == "VPUNC"))
    pune_village = result.scalar_one_or_none()

    result = await session.execute(select(State).where(State.code == "KA"))
    ka = result.scalar_one_or_none()
    result = await session.execute(select(District).where(District.code == "BLR", District.state_id == ka.id))
    blr = result.scalar_one_or_none()
    result = await session.execute(select(Tehsil).where(Tehsil.code == "BLRN"))
    blr_tehsil = result.scalar_one_or_none()
    result = await session.execute(select(Village).where(Village.code == "VBLRN"))
    blr_village = result.scalar_one_or_none()

    result = await session.execute(select(State).where(State.code == "GJ"))
    gj = result.scalar_one_or_none()
    result = await session.execute(select(District).where(District.code == "AMD", District.state_id == gj.id))
    amd = result.scalar_one_or_none()
    result = await session.execute(select(Tehsil).where(Tehsil.code == "AMDC"))
    amd_tehsil = result.scalar_one_or_none()
    result = await session.execute(select(Village).where(Village.code == "VAMDC"))
    amd_village = result.scalar_one_or_none()

    num_projects = (await session.execute(select(func.count(Project.id)))).scalar() or 0

    project_defs = [
        {
            "name": "Mumbai-Pune Expressway Expansion",
            "description": "Expansion of existing expressway corridor from 6 to 8 lanes",
            "project_type": "NATIONAL_HIGHWAY",
            "purpose": "Improve connectivity between Mumbai and Pune",
            "public_category": "INFRASTRUCTURE",
            "state": mh, "district": mumbai, "tehsil": mumbai_tehsil, "village": mumbai_village,
            "status": "GIS_VERIFICATION",
            "estimated_cost": Decimal("8500000000"),
            "priority": 1,
        },
        {
            "name": "Nagpur Metro Rail Phase II",
            "description": "Extension of metro rail network to suburban areas",
            "project_type": "RAILWAY",
            "purpose": "Urban public transport connectivity",
            "public_category": "TRANSPORT",
            "state": mh, "district": pune, "tehsil": pune_tehsil, "village": pune_village,
            "status": "SUBmitted".upper(),
            "estimated_cost": Decimal("12000000000"),
            "priority": 2,
        },
        {
            "name": "Varun Dam Construction Project",
            "description": "Multi-purpose dam for irrigation and drinking water",
            "project_type": "DAM",
            "status": "PUBLIC_HEARING",
            "public_category": "WATER",
            "state": ka, "district": blr, "tehsil": blr_tehsil, "village": blr_village,
            "estimated_cost": Decimal("4500000000"),
            "priority": 2,
        },
        {
            "name": "Bengaluru Tech Park Development",
            "description": "Development of IT park with residential and commercial zones",
            "project_type": "URBAN_DEVELOPMENT",
            "status": "COMPENSATION_ASSESSMENT",
            "public_category": "IT_INFRASTRUCTURE",
            "state": ka, "district": blr, "tehsil": blr_tehsil, "village": blr_village,
            "estimated_cost": Decimal("3000000000"),
            "priority": 3,
        },
        {
            "name": "Dholera Smart City Industrial Corridor",
            "description": "Industrial corridor with smart city infrastructure",
            "project_type": "INDUSTRIAL_CORRIDOR",
            "status": "DRAFT",
            "public_category": "INDUSTRIAL",
            "state": gj, "district": amd, "tehsil": amd_tehsil, "village": amd_village,
            "estimated_cost": Decimal("25000000000"),
            "priority": 1,
        },
        {
            "name": "Surat Coastal Highway",
            "description": "Coastal highway connecting ports and industrial zones",
            "project_type": "NATIONAL_HIGHWAY",
            "status": "APPROVED",
            "public_category": "INFRASTRUCTURE",
            "state": gj, "district": amd, "tehsil": amd_tehsil, "village": amd_village,
            "estimated_cost": Decimal("5500000000"),
            "priority": 2,
        },
        {
            "name": "Solar Power Plant - Rajasthan",
            "description": "Utility scale solar power generation facility",
            "project_type": "POWER_PROJECT",
            "status": "DRAFT",
            "public_category": "ENERGY",
            "state": mh, "district": pune, "tehsil": pune_tehsil, "village": pune_village,
            "estimated_cost": Decimal("8000000000"),
            "priority": 3,
        },
        {
            "name": "Defence Research Complex Pune",
            "description": "Advanced defence research and development facility",
            "project_type": "DEFENCE",
            "status": "UNDER_REVIEW",
            "public_category": "DEFENCE",
            "state": mh, "district": pune, "tehsil": pune_tehsil, "village": pune_village,
            "estimated_cost": Decimal("15000000000"),
            "priority": 1,
        },
        {
            "name": "Rural Road Network Upgrade",
            "description": "Upgrade rural roads in convergence with PMGSY",
            "project_type": "URBAN_DEVELOPMENT",
            "status": "COMPLETED",
            "public_category": "RURAL",
            "state": ka, "district": blr, "tehsil": blr_tehsil, "village": blr_village,
            "estimated_cost": Decimal("2000000000"),
            "priority": 4,
        },
    ]

    count = 0
    created_projects = []
    for pdef in project_defs:
        code = f"BD-{datetime.utcnow().year}-{num_projects + count + 1:05d}"
        sponsor = users.get("PROJECT_SPONSOR")
        project = Project(
            project_code=code,
            name=pdef["name"],
            description=pdef["description"],
            project_type=pdef["project_type"],
            purpose=pdef.get("purpose"),
            public_category=pdef.get("public_category"),
            sponsor_id=sponsor.department_id if sponsor else None,
            proposed_area_sq_m=Decimal("500000"),
            state_id=pdef["state"].id if pdef["state"] else None,
            district_id=pdef["district"].id if pdef["district"] else None,
            tehsil_id=pdef["tehsil"].id if pdef["tehsil"] else None,
            village_id=pdef["village"].id if pdef["village"] else None,
            start_date=datetime.utcnow() - timedelta(days=30),
            target_completion_date=datetime.utcnow() + timedelta(days=730),
            priority=pdef.get("priority", 3),
            estimated_cost=pdef["estimated_cost"],
            funding_source="Government of India",
            status=pdef["status"],
            created_by=sponsor.id if sponsor else None,
            version=1,
        )
        session.add(project)
        await session.flush()

        instance = WorkflowInstance(project_id=project.id, current_status=pdef["status"])
        session.add(instance)

        history = ProjectStatusHistory(
            project_id=project.id, previous_status=None,
            new_status=pdef["status"], changed_by=project.created_by or sponsor.id,
            comment="Initial project creation",
        )
        session.add(history)

        activity = ProjectActivity(
            project_id=project.id, actor_id=sponsor.id if sponsor else None,
            activity_type="PROJECT_CREATED",
            description=f"Project {project.name} created",
        )
        session.add(activity)

        created_projects.append((project, instance, pdef))
        count += 1

    await session.flush()
    return created_projects


async def create_parcels(session, projects):
    print("Creating parcels, owners, documents...")
    parcel_index = (await session.execute(select(func.count(Parcel.id)))).scalar() or 0
    all_created = []
    owner_index = 0

    base_lat = 19.0
    base_lon = 72.8

    for project, instance, pdef in projects:
        num_parcels = 8 if pdef["status"] != "DRAFT" else 4
        for i in range(num_parcels):
            parcel_index += 1
            lat = base_lat + (i * 0.03)
            lon = base_lon + (i * 0.02)
            geom = make_polygon_geojson(lat, lon, 0.002)
            area = calculate_area_from_geojson(geom) or 40000

            parcel = Parcel(
                parcel_code=f"PRC-{parcel_index:06d}",
                survey_number=f"SV-{parcel_index}",
                khasra_number=f"KH-{parcel_index}",
                ulpin=f"ULPIN{i:06d}{str(project.id)[:8]}",
                village_id=pdef["village"].id if pdef["village"] else None,
                tehsil_id=pdef["tehsil"].id if pdef["tehsil"] else None,
                district_id=pdef["district"].id if pdef["district"] else None,
                state_id=pdef["state"].id if pdef["state"] else None,
                land_type="AGRICULTURAL",
                ownership_type="PRIVATE",
                area_sq_m=Decimal(str(round(area, 2))),
                geometry=geom,
                current_status="IDENTIFIED",
            )
            session.add(parcel)
            await session.flush()

            session.add(ProjectParcel(
                project_id=project.id,
                parcel_id=parcel.id,
                acquired_area_sq_m=Decimal(str(round(area, 2))),
            ))

            owner_names = ["Ramesh Kumar", "Suresh Patel", "Kavita Desai", "Mahesh Reddy"]
            for j, oname in enumerate(owner_names):
                owner_index += 1
                session.add(ParcelOwner(
                    parcel_id=parcel.id,
                    owner_name=oname,
                    father_husband_name=f"Father of {oname}",
                    gender="Male" if j % 2 == 0 else "Female",
                    age=35 + j * 5,
                    aadhaar_last4=f"{1000 + j:04d}",
                    relation_to_holder="Owner",
                    is_primary=(j == 0),
                    contact_phone=f"9{j}{i}{parcel_index}123450",
                    address=f"Village, Tehsil, District, State - 400001",
                ))

            await session.flush()

            session.add(GISVerification(
                project_id=project.id,
                parcel_id=parcel.id,
                verified_by=None,
                geometry_valid=True,
                area_match=True,
                overlap_detected=False,
                overlap_parcel_ids=[],
                outside_boundary=False,
                verification_notes="Automatic GIS verification on seed",
            ))

            all_created.append(parcel)
    await session.flush()
    return all_created


async def create_documents(session, projects, users):
    print("Creating documents...")
    docs = []
    for project, instance, pdef in projects:
        if pdef["status"] == "DRAFT":
            continue
        types = ["LAND_RECORD", "SURVEY_MAP", "NOTIFICATION_ORDER", "ENVIRONMENT_CLEARANCE"]
        for t in types:
            doc = ProjectDocument(
                project_id=project.id,
                document_type=t,
                title=f"{pdef['name']} - {t.replace('_', ' ').title()}",
                file_name=f"{t.lower()}_{project.id}.pdf",
                file_path=f"/uploads/{t.lower()}_{project.id}.pdf",
                file_size=250000,
                mime_type="application/pdf",
                status="PENDING" if t == "LAND_RECORD" else "APPROVED",
                uploaded_by=users.get("PROJECT_SPONSOR").id if users.get("PROJECT_SPONSOR") else None,
                verified_by=users.get("VERIFICATION_OFFICER").id if users.get("VERIFICATION_OFFICER") else None,
            )
            session.add(doc)
            docs.append(doc)
    await session.flush()


async def create_compensation_and_rr(session, projects, users):
    print("Creating compensation cases and RR cases...")
    for project, instance, pdef in projects:
        result = await session.execute(
            select(Parcel).limit(5)
        )
        parcels = result.scalars().all()
        result = await session.execute(select(ParcelOwner).limit(5))
        owners = result.scalars().all()

        if pdef["status"] in ("COMPENSATION_ASSESSMENT", "APPROVED", "IN_PROGRESS", "COMPLETED"):
            for idx, parcel in enumerate(parcels[:3]):
                owner = owners[idx] if idx < len(owners) else owners[0]
                case = CompensationCase(
                    parcel_id=parcel.id,
                    project_id=project.id,
                    landowner_id=owner.id,
                    assessed_value=Decimal("2500000"),
                    land_area_sq_m=parcel.area_sq_m,
                    compensation_components={
                        "land_value": "2000000",
                        "structures": "300000",
                        "trees_crops": "200000",
                        "solatium": "500000",
                    },
                    total_amount=Decimal("3000000"),
                    status="APPROVED" if pdef["status"] in ("APPROVED", "IN_PROGRESS", "COMPLETED") else "ASSESSED",
                    assigned_officer_id=users.get("COMPENSATION_OFFICER").id if users.get("COMPENSATION_OFFICER") else None,
                )
                session.add(case)
                await session.flush()

                if pdef["status"] in ("APPROVED", "IN_PROGRESS", "COMPLETED"):
                    session.add(CompensationPayment(
                        case_id=case.id,
                        amount=Decimal("3000000"),
                        payment_method="Bank Transfer",
                        payment_reference=f"PAY-{case.id}",
                        payment_date=datetime.utcnow() - timedelta(days=25),
                        status="COMPLETED",
                        approved_by=users.get("CENTRAL_AUTHORITY").id if users.get("CENTRAL_AUTHORITY") else None,
                    ))

                result = await session.execute(
                    select(ParcelOwner)
                    .where(ParcelOwner.parcel_id == parcel.id)
                    .limit(1)
                )
                owner1 = result.scalars().first()
                if owner1:
                    session.add(RRCase(
                        project_id=project.id,
                        parcel_id=parcel.id,
                        landowner_id=owner1.id,
                        family_members_count=4,
                        eligibility_status="ELIGIBLE",
                        entitlement_details={"monetary": "1500000", "alternative_land": "500 sq m"},
                        assistance_type="Monetary + Alternative land",
                        assigned_officer_id=users.get("RR_OFFICER").id if users.get("RR_OFFICER") else None,
                        status="ELIGIBLE",
                    ))
        await session.flush()


async def db_execute_once(session, model, **kwargs):
    conditions = []
    for k, v in kwargs.items():
        column = getattr(model, k)
        import sqlalchemy
        conditions.append(column == v)
    return await session.execute(select(model).where(*conditions))


async def create_objections(session, projects, users):
    print("Creating objections and hearings...")
    for project, instance, pdef in projects:
        if pdef["status"] in ("PUBLIC_HEARING", "COMPENSATION_ASSESSMENT", "APPROVED"):
            count = (await session.execute(select(func.count(Objection.id)))).scalar() or 0
            objection = Objection(
                objection_code=f"OBJ-{count + 1:05d}",
                project_id=project.id,
                category="VALUATION_DISPUTE",
                description="Landowner disputes the compensation valuation method applied",
                status="UNDER_REVIEW",
                created_by=users.get("PROJECT_SPONSOR").id if users.get("PROJECT_SPONSOR") else None,
            )
            session.add(objection)
            await session.flush()
            session.add(Hearing(
                objection_id=objection.id,
                hearing_date=datetime.utcnow() + timedelta(days=7),
                hearing_officer_id=users.get("DISTRICT_ADMIN").id if users.get("DISTRICT_ADMIN") else None,
                location="District Collector Office",
            ))
    await session.flush()


async def create_notifications_and_audit(session, users):
    print("Creating notifications and audit logs...")
    for role_name, user in users.items():
        session.add(Notification(
            user_id=user.id,
            title="Welcome to Bhu-Drishti",
            message="Your account has been created successfully. Explore the system.",
            notification_type="INFO",
            entity_type="profile",
        ))
    session.add(AuditLog(
        actor_id=users.get("SUPER_ADMIN").id if users.get("SUPER_ADMIN") else None,
        actor_email="superadmin@bhudrishti.gov.in",
        action="SEED_DATA",
        entity_type="system",
        meta={"reason": "Initial data seeding"},
    ))
    await session.flush()


async def main():
    engine = create_async_engine(settings.async_database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        try:
            await create_roles_permissions(session)
            await create_departments(session)
            await create_geography(session)
            users = await create_users(session)
            await create_jurisdiction_rules(session)
            await create_sla_rules(session)
            projects = await create_projects(session, users)
            parcels = await create_parcels(session, projects)
            await create_documents(session, projects, users)
            await create_compensation_and_rr(session, projects, users)
            await create_objections(session, projects, users)
            await create_notifications_and_audit(session, users)
            await session.commit()
            print("Seed data created successfully!")
        except Exception as e:
            await session.rollback()
            print(f"Error seeding data: {e}")
            raise
        finally:
            await engine.dispose()


import asyncio

if __name__ == "__main__":
    asyncio.run(main())
