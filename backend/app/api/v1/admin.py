from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.models.models import (
    Profile, Role, Permission, Department, State, District, Tehsil, Village,
    SLARule, JurisdictionRule, RolePermission
)
from app.security.password import hash_password
from app.schemas.auth import UserCreate, RoleCreate, DepartmentCreate, SLARuleCreate
from app.core.config import settings

router = APIRouter()


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    role_id: UUID = Query(None),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    query = select(Profile).options(selectinload(Profile.role))
    count_query = select(func.count(Profile.id))
    if search:
        like = f"%{search}%"
        cond = or_(Profile.email.ilike(like), Profile.full_name.ilike(like))
        query = query.where(cond)
        count_query = count_query.where(cond)
    if role_id:
        query = query.where(Profile.role_id == role_id)
        count_query = count_query.where(Profile.role_id == role_id)
    if is_active is not None:
        query = query.where(Profile.is_active == is_active)
        count_query = count_query.where(Profile.is_active == is_active)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(Profile.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    users = result.scalars().all()
    data = [_user_dict(u) for u in users]
    return {
        "success": True,
        "data": data, "total": total, "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        "message": "Users retrieved",
    }


@router.post("/users", status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(select(Profile).where(Profile.email == data.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already exists")

    user = Profile(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role_id=data.role_id,
        department_id=data.department_id,
        state_id=data.state_id,
        district_id=data.district_id,
        is_active=data.is_active,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    return {
        "success": True,
        "data": _user_dict(user),
        "message": "User created",
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(select(Profile).where(Profile.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = ["full_name", "phone", "role_id", "department_id", "state_id", "district_id", "is_active"]
    for key in allowed:
        if key in data and data[key] is not None:
            setattr(user, key, data[key])

    await db.flush()
    return {
        "success": True,
        "data": _user_dict(user),
        "message": "User updated",
    }


@router.get("/roles")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(select(Role).options(selectinload(Role.permissions)))
    roles = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "permissions": [
                    {"id": str(p.id), "name": p.name, "module": p.module}
                    for p in (r.permissions or [])
                ],
            }
            for r in roles
        ],
        "message": "Roles retrieved",
    }


@router.get("/permissions")
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(select(Permission).order_by(Permission.module, Permission.name))
    permissions = result.scalars().all()
    return {
        "success": True,
        "data": [
            {"id": str(p.id), "name": p.name, "module": p.module}
            for p in permissions
        ],
        "message": "Permissions retrieved",
    }


@router.get("/departments")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(select(Department).order_by(Department.name))
    depts = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(d.id), "name": d.name, "code": d.code,
                "parent_id": str(d.parent_id) if d.parent_id else None,
                "level": d.level, "state_code": d.state_code,
                "district_code": d.district_code,
            }
            for d in depts
        ],
        "message": "Departments retrieved",
    }


@router.post("/departments", status_code=201)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    dept = Department(
        name=data.name, code=data.code, parent_id=data.parent_id,
        level=data.level, state_code=data.state_code,
        district_code=data.district_code,
    )
    db.add(dept)
    await db.flush()
    return {
        "success": True,
        "data": {"id": str(dept.id), "name": dept.name, "code": dept.code},
        "message": "Department created",
    }


@router.get("/states")
async def list_states(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(select(State).order_by(State.name))
    states = result.scalars().all()
    return {
        "success": True,
        "data": [
            {"id": str(s.id), "name": s.name, "code": s.code}
            for s in states
        ],
        "message": "States retrieved",
    }


@router.get("/districts")
async def list_districts(
    state_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    query = select(District).order_by(District.name)
    if state_id:
        query = query.where(District.state_id == state_id)
    result = await db.execute(query)
    districts = result.scalars().all()
    return {
        "success": True,
        "data": [
            {"id": str(d.id), "name": d.name, "code": d.code, "state_id": str(d.state_id)}
            for d in districts
        ],
        "message": "Districts retrieved",
    }


@router.get("/tehsils")
async def list_tehsils(
    district_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    query = select(Tehsil).order_by(Tehsil.name)
    if district_id:
        query = query.where(Tehsil.district_id == district_id)
    result = await db.execute(query)
    tehsils = result.scalars().all()
    return {
        "success": True,
        "data": [
            {"id": str(t.id), "name": t.name, "code": t.code, "district_id": str(t.district_id)}
            for t in tehsils
        ],
        "message": "Tehsils retrieved",
    }


@router.get("/villages")
async def list_villages(
    tehsil_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    query = select(Village).order_by(Village.name)
    if tehsil_id:
        query = query.where(Village.tehsil_id == tehsil_id)
    result = await db.execute(query)
    villages = result.scalars().all()
    return {
        "success": True,
        "data": [
            {"id": str(v.id), "name": v.name, "code": v.code, "tehsil_id": str(v.tehsil_id), "pin_code": v.pin_code}
            for v in villages
        ],
        "message": "Villages retrieved",
    }


@router.get("/sla-rules")
async def list_sla_rules(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(select(SLARule).order_by(SLARule.priority))
    rules = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(r.id), "from_status": r.from_status,
                "to_status": r.to_status, "max_duration_hours": r.max_duration_hours,
                "role_id": str(r.role_id) if r.role_id else None,
                "priority": r.priority, "is_active": r.is_active,
            }
            for r in rules
        ],
        "message": "SLA rules retrieved",
    }


@router.post("/sla-rules", status_code=201)
async def create_sla_rule(
    data: SLARuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    rule = SLARule(
        from_status=data.from_status,
        to_status=data.to_status,
        max_duration_hours=data.max_duration_hours,
        role_id=data.role_id,
        priority=data.priority,
        is_active=data.is_active,
    )
    db.add(rule)
    await db.flush()
    return {
        "success": True,
        "data": {"id": str(rule.id), "from": rule.from_status, "to": rule.to_status},
        "message": "SLA rule created",
    }


@router.get("/jurisdiction-rules")
async def list_jurisdiction_rules(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(select(JurisdictionRule).order_by(JurisdictionRule.rule_code))
    rules = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(r.id), "rule_code": r.rule_code,
                "rule_version": r.rule_version,
                "conditions": r.conditions, "result": r.result,
                "is_active": r.is_active,
                "source_reference": r.source_reference,
            }
            for r in rules
        ],
        "message": "Jurisdiction rules retrieved",
    }


@router.post("/jurisdiction-rules", status_code=201)
async def create_jurisdiction_rule(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    rule = JurisdictionRule(
        rule_code=data["rule_code"],
        rule_version=data.get("rule_version", "1.0"),
        conditions=data.get("conditions", {}),
        result=data.get("result", {}),
        source_reference=data.get("source_reference"),
        is_active=data.get("is_active", True),
    )
    db.add(rule)
    await db.flush()
    return {
        "success": True,
        "data": {"id": str(rule.id), "rule_code": rule.rule_code},
        "message": "Jurisdiction rule created",
    }


def _user_dict(u):
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "phone": u.phone,
        "role": {"id": str(u.role.id), "name": u.role.name} if u.role else None,
        "department_id": str(u.department_id) if u.department_id else None,
        "state_id": str(u.state_id) if u.state_id else None,
        "district_id": str(u.district_id) if u.district_id else None,
        "is_active": u.is_active,
        "is_verified": u.is_verified,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
