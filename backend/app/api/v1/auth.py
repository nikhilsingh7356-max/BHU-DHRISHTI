from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.security.dependencies import get_db, get_current_user
from app.security.jwt import create_access_token, create_refresh_token
from app.services import auth_service
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    UserResponse, UserWithPermissions
)
from app.models.models import Profile, Role, Permission
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        profile = await auth_service.register_user(
            db=db,
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            role_id=data.role_id,
            phone=data.phone,
            department_id=data.department_id,
            state_id=data.state_id,
            district_id=data.district_id,
        )
        from app.audit.service import log_action
        await log_action(
            db=db, actor_id=profile.id, actor_email=profile.email,
            action="REGISTER_USER", entity_type="profile", entity_id=profile.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return {
            "success": True,
            "data": {"id": str(profile.id), "email": profile.email, "full_name": profile.full_name},
            "message": "Registration successful",
        }
    except HTTPException as e:
        raise e


@router.post("/login")
async def login(
    data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    profile = await auth_service.authenticate_user(db, data.email, data.password)

    access_token = create_access_token({"sub": str(profile.id)})
    refresh_token = create_refresh_token({"sub": str(profile.id)})

    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).where(Role.id == profile.role_id)
    )
    role = result.scalar_one_or_none()

    role_obj = None
    if role:
        role_obj = {
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
            "permissions": [
                {"id": str(p.id), "name": p.name, "module": p.module}
                for p in role.permissions
            ],
        }

    from app.audit.service import log_action
    await log_action(
        db=db, actor_id=profile.id, actor_email=profile.email,
        action="LOGIN", entity_type="profile", entity_id=profile.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(profile.id),
                "email": profile.email,
                "full_name": profile.full_name,
                "phone": profile.phone,
                "role": role_obj,
                "is_active": profile.is_active,
                "is_verified": profile.is_verified,
                "department_id": str(profile.department_id) if profile.department_id else None,
                "state_id": str(profile.state_id) if profile.state_id else None,
                "district_id": str(profile.district_id) if profile.district_id else None,
                "last_login": profile.last_login.isoformat() if profile.last_login else None,
            },
        },
        "message": "Login successful",
    }


@router.post("/refresh")
async def refresh(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    tokens = await auth_service.refresh_token(db, data.refresh_token)
    return {
        "success": True,
        "data": tokens,
        "message": "Token refreshed",
    }


@router.get("/me")
async def get_me(
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Profile)
        .options(
            selectinload(Profile.role).selectinload(Role.permissions),
        )
        .where(Profile.id == current_user.id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    role = None
    if user.role:
        role = {
            "id": str(user.role.id),
            "name": user.role.name,
            "description": user.role.description,
            "permissions": [
                {"id": str(p.id), "name": p.name, "module": p.module}
                for p in user.role.permissions
            ],
        }

    return {
        "success": True,
        "data": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": role,
            "department_id": str(user.department_id) if user.department_id else None,
            "state_id": str(user.state_id) if user.state_id else None,
            "district_id": str(user.district_id) if user.district_id else None,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
        "message": "User profile",
    }
