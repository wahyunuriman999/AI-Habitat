from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_session
from app.core.errors import AppError, ErrorCode
from app.core.response import success_response
from app.api.dependencies import get_current_identity
from app.models.ai_identity import AIIdentity
from app.models.user import User
from app.schemas.phase2 import AIIdentityCreate, AIIdentityUpdate, AIIdentityResponse

router = APIRouter()

@router.post("", response_model=None, status_code=201)
async def create_ai_identity(
    data: AIIdentityCreate,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Create AI independently with Genesis Fact (created_by_user_id)."""
    ai_identity = AIIdentity(
        name=data.name,
        created_by_user_id=current_user.id
    )
    session.add(ai_identity)
    await session.commit()
    await session.refresh(ai_identity)
    
    return success_response(data=AIIdentityResponse.model_validate(ai_identity).model_dump(mode="json"))

@router.get("/{id}", response_model=None)
async def get_ai_identity(
    id: uuid.UUID,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Get AI. Requires Identity Steward context."""
    ai_identity = await session.get(AIIdentity, id)
    
    # Hide existence if not steward
    if not ai_identity or ai_identity.created_by_user_id != current_user.id:
        raise AppError(ErrorCode.NOT_FOUND, "AI Identity not found.")
        
    return success_response(data=AIIdentityResponse.model_validate(ai_identity).model_dump(mode="json"))

@router.patch("/{id}", response_model=None)
async def update_ai_identity(
    id: uuid.UUID,
    data: AIIdentityUpdate,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Update AI. Requires Identity Steward context.
    State transitions are one-way: ACTIVE -> ARCHIVED.
    """
    ai_identity = await session.get(AIIdentity, id)
    
    if not ai_identity or ai_identity.created_by_user_id != current_user.id:
        raise AppError(ErrorCode.NOT_FOUND, "AI Identity not found.")
        
    if data.name is not None:
        ai_identity.name = data.name
        
    if data.state is not None:
        if data.state == "ARCHIVED" and ai_identity.state == "ACTIVE":
            ai_identity.state = "ARCHIVED"
        elif data.state == "ACTIVE" and ai_identity.state == "ARCHIVED":
            raise AppError(ErrorCode.INVALID_ACTION_STATE, "Cannot restore ARCHIVED AI.")
        elif data.state not in ["ACTIVE", "ARCHIVED"]:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Invalid state.")
            
    await session.commit()
    await session.refresh(ai_identity)
    
    return success_response(data=AIIdentityResponse.model_validate(ai_identity).model_dump(mode="json"))

from app.models.cognitive_binding import CognitiveBinding
from app.schemas.phase3 import CognitiveBindingCreate, CognitiveBindingUpdate, CognitiveBindingResponse


@router.post("/{id}/bindings", response_model=None, status_code=201)
async def create_binding(
    id: uuid.UUID,
    data: CognitiveBindingCreate,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Create CognitiveBinding (1:N). Requires Identity Steward context."""
    ai_identity = await session.get(AIIdentity, id)
    
    if not ai_identity or ai_identity.created_by_user_id != current_user.id:
        raise AppError(ErrorCode.NOT_FOUND, "AI Identity not found.")
        
    binding = CognitiveBinding(
        ai_identity_id=ai_identity.id,
        provider=data.provider,
        model=data.model,
        credential_ref=data.credential_ref,
        is_default=data.is_default
    )
    
    session.add(binding)
    await session.commit()
    await session.refresh(binding)
    
    return success_response(data=CognitiveBindingResponse.model_validate(binding).model_dump(mode="json"))

@router.get("/{id}/bindings", response_model=None)
async def list_bindings(
    id: uuid.UUID,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """List bindings. Requires Identity Steward context."""
    ai_identity = await session.get(AIIdentity, id)
    
    if not ai_identity or ai_identity.created_by_user_id != current_user.id:
        raise AppError(ErrorCode.NOT_FOUND, "AI Identity not found.")
        
    bindings_res = await session.execute(
        select(CognitiveBinding).where(CognitiveBinding.ai_identity_id == id)
    )
    bindings = bindings_res.scalars().all()
    
    data = [CognitiveBindingResponse.model_validate(b).model_dump(mode="json") for b in bindings]
    return success_response(data=data)

@router.patch("/{id}/bindings/{binding_id}", response_model=None)
async def update_binding(
    id: uuid.UUID,
    binding_id: uuid.UUID,
    data: CognitiveBindingUpdate,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Update binding (e.g. swap default). Requires Identity Steward context."""
    ai_identity = await session.get(AIIdentity, id)
    if not ai_identity or ai_identity.created_by_user_id != current_user.id:
        raise AppError(ErrorCode.NOT_FOUND, "AI Identity not found.")
        
    binding = await session.get(CognitiveBinding, binding_id)
    if not binding or binding.ai_identity_id != id:
        raise AppError(ErrorCode.NOT_FOUND, "Binding not found.")
        
    if data.is_default is not None:
        binding.is_default = data.is_default
        
    await session.commit()
    await session.refresh(binding)
    
    return success_response(data=CognitiveBindingResponse.model_validate(binding).model_dump(mode="json"))
