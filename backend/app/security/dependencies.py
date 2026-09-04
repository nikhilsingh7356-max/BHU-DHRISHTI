from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db as _get_db
from app.security.jwt import verify_token
from app.models.models import Profile, Role, Permission, RolePermission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db():
    async for session in _get_db():
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Profile:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    token_type: str = payload.get("type", "access")
    if token_type != "access":
        raise credentials_exception
    result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.role).selectinload(Role.permissions))
        .where(Profile.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return user


def require_permission(permission_name: str):
    async def permission_checker(
        current_user: Profile = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> Profile:
        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned"
            )
        result = await db.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == current_user.role_id)
            .where(Permission.name == permission_name)
        )
        perm = result.scalar_one_or_none()
        if perm is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required"
            )
        return current_user
    return permission_checker


def require_role(role_name: str):
    async def role_checker(
        current_user: Profile = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> Profile:
        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned"
            )
        if current_user.role.name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        return current_user
    return role_checker
