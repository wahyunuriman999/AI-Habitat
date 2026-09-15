"""Dependencies for AI Habitat API."""

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import AppError, ErrorCode
from app.models.user import User


async def get_current_identity(
    x_user_id: str | None = Header(None, description="Development Identity Context"),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency that extracts the development identity context.
    
    Verifies the user exists and is ACTIVE.
    """
    if not x_user_id:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="X-User-ID header is missing.",
            status_code=401,
        )
        
    try:
        import uuid
        user_uuid = uuid.UUID(x_user_id)
    except ValueError:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid X-User-ID format.",
            status_code=401,
        )

    result = await session.execute(
        select(User).where(User.id == user_uuid, User.state == "ACTIVE")
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Identity not found or not active.",
            status_code=401,
        )
        
    return user
