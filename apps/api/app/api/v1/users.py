from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.response import success_response
from app.models.user import User
from app.schemas.phase2 import UserResponse

router = APIRouter()

@router.post("", response_model=None, status_code=201)
async def create_user(
    session: AsyncSession = Depends(get_session)
):
    """Bootstrap endpoint to create a human user."""
    user = User()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return success_response(data=UserResponse.model_validate(user).model_dump(mode="json"))

@router.get("/{id}", response_model=None)
async def get_user(
    id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a user by ID (basic debug view, not heavily protected in Phase 2)."""
    user = await session.get(User, id)
    if not user:
        from app.core.errors import AppError, ErrorCode
        raise AppError(ErrorCode.NOT_FOUND, "User not found.")
    
    return success_response(data=UserResponse.model_validate(user).model_dump(mode="json"))
