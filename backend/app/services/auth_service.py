from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.models import Profile, Role, Permission, RolePermission
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token, verify_token


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    role_id: UUID,
    phone: str = None,
    department_id: UUID = None,
    state_id: UUID = None,
    district_id: UUID = None,
) -> Profile:
    result = await db.execute(
        select(Profile).where(Profile.email == email.lower())
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    profile = Profile(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
        phone=phone,
        role_id=role_id,
        department_id=department_id,
        state_id=state_id,
        district_id=district_id,
        is_active=True,
        is_verified=True,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Profile:
    result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.role).selectinload(Role.permissions))
        .where(Profile.email == email.lower())
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not profile.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    if profile.locked_until and profile.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Try again later.",
        )

    if not verify_password(password, profile.password_hash):
        profile.failed_login_attempts = (profile.failed_login_attempts or 0) + 1
        if profile.failed_login_attempts >= 5:
            profile.locked_until = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            profile.locked_until = datetime.utcnow() + timedelta(minutes=30)
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    profile.failed_login_attempts = 0
    profile.locked_until = None
    profile.last_login = datetime.utcnow()
    await db.flush()
    return profile


async def refresh_token(db: AsyncSession, refresh_token_str: str) -> dict:
    payload = verify_token(refresh_token_str)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    result = await db.execute(
        select(Profile).where(Profile.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    access_token = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


async def get_profile_by_id(db: AsyncSession, user_id: UUID) -> Profile:
    result = await db.execute(
        select(Profile)
        .options(
            selectinload(Profile.role).selectinload(Role.permissions),
            selectinload(Profile.department),
        )
        .where(Profile.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_permissions_for_user(db: AsyncSession, user_id: UUID) -> list:
    result = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Profile, Profile.role_id == RolePermission.role_id)
        .where(Profile.id == user_id)
    )
    return result.scalars().all()
