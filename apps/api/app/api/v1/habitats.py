from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_session
from app.core.errors import AppError, ErrorCode
from app.core.response import success_response
from app.api.dependencies import get_current_identity
from app.models.habitat import Habitat
from app.models.membership import HabitatMembership
from app.models.participation import HabitatParticipation
from app.models.ai_identity import AIIdentity
from app.models.user import User
from app.schemas.phase2 import HabitatCreate, HabitatResponse, ParticipationCreate, ParticipationResponse

router = APIRouter()

@router.post("", response_model=None, status_code=201)
async def create_habitat(
    data: HabitatCreate,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Atomic Habitat Genesis. Creates Habitat and OWNER Membership in one transaction."""
    habitat = Habitat(name=data.name)
    session.add(habitat)
    await session.flush() # flush to get habitat.id without committing
    
    membership = HabitatMembership(
        user_id=current_user.id,
        habitat_id=habitat.id,
        role="OWNER"
    )
    session.add(membership)
    
    await session.commit()
    await session.refresh(habitat)
    
    return success_response(data=HabitatResponse.model_validate(habitat).model_dump(mode="json"))

@router.get("/{id}", response_model=None)
async def get_habitat(
    id: uuid.UUID,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Get Habitat. Requires current user to have a membership (any role)."""
    membership = await session.execute(
        select(HabitatMembership).where(
            HabitatMembership.habitat_id == id,
            HabitatMembership.user_id == current_user.id
        )
    )
    if not membership.scalar_one_or_none():
        raise AppError(ErrorCode.NOT_FOUND, "Habitat not found.")
        
    habitat = await session.get(Habitat, id)
    if not habitat:
        raise AppError(ErrorCode.NOT_FOUND, "Habitat not found.")
        
    return success_response(data=HabitatResponse.model_validate(habitat).model_dump(mode="json"))


@router.post("/{id}/participations", response_model=None, status_code=201)
async def add_ai_participation(
    id: uuid.UUID,
    data: ParticipationCreate,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Add an AI to a Habitat.
    Requires CurrentIdentity to have OWNER role.
    Target AI and target Habitat must not be ARCHIVED.
    """
    membership_res = await session.execute(
        select(HabitatMembership).where(
            HabitatMembership.habitat_id == id,
            HabitatMembership.user_id == current_user.id
        )
    )
    membership = membership_res.scalar_one_or_none()
    
    if not membership:
        raise AppError(ErrorCode.NOT_FOUND, "Habitat not found.")
        
    if membership.role != "OWNER":
        raise AppError(ErrorCode.PERMISSION_DENIED, "Must be OWNER to add participation.")
        
    habitat = await session.get(Habitat, id)
    if not habitat or habitat.state == "ARCHIVED":
        raise AppError(ErrorCode.INVALID_ACTION_STATE, "Cannot add to an archived habitat.")
        
    ai_identity = await session.get(AIIdentity, data.ai_identity_id)
    if not ai_identity:
        raise AppError(ErrorCode.VALIDATION_ERROR, "AI Identity does not exist.")
        
    if ai_identity.state == "ARCHIVED":
        raise AppError(ErrorCode.INVALID_ACTION_STATE, "Cannot add an archived AI to a habitat.")
        
    participation = HabitatParticipation(
        ai_identity_id=ai_identity.id,
        habitat_id=habitat.id
    )
    session.add(participation)
    await session.commit()
    await session.refresh(participation)
    
    return success_response(data=ParticipationResponse.model_validate(participation).model_dump(mode="json"))

@router.get("/{id}/participations", response_model=None)
async def list_participations(
    id: uuid.UUID,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """List AIs in the habitat. Requires any membership role."""
    membership_res = await session.execute(
        select(HabitatMembership).where(
            HabitatMembership.habitat_id == id,
            HabitatMembership.user_id == current_user.id
        )
    )
    membership = membership_res.scalar_one_or_none()
    
    if not membership:
        raise AppError(ErrorCode.NOT_FOUND, "Habitat not found.")
        
    participations_res = await session.execute(
        select(HabitatParticipation).where(HabitatParticipation.habitat_id == id)
    )
    participations = participations_res.scalars().all()
    
    data = [ParticipationResponse.model_validate(p).model_dump(mode="json") for p in participations]
    return success_response(data=data)

from app.schemas.phase3 import Observation, Context
from app.core.runtime import RuntimeSession
from app.models.cognitive_binding import CognitiveBinding

@router.post("/{habitat_id}/participations/{ai_identity_id}/tick", response_model=None)
async def runtime_tick(
    habitat_id: uuid.UUID,
    ai_identity_id: uuid.UUID,
    observation: Observation,
    current_user: User = Depends(get_current_identity),
    session: AsyncSession = Depends(get_session)
):
    """Proof of Concept endpoint for Runtime Execution Boundary.
    Validates I-09 (Requires Participation).
    """
    # 1. Authorize human caller
    membership_res = await session.execute(
        select(HabitatMembership).where(
            HabitatMembership.habitat_id == habitat_id,
            HabitatMembership.user_id == current_user.id
        )
    )
    membership = membership_res.scalar_one_or_none()
    if not membership:
        raise AppError(ErrorCode.NOT_FOUND, "Habitat not found.")
        
    habitat = await session.get(Habitat, habitat_id)
    
    # 2. I-09 Validation: AI must participate in this Habitat and be ACTIVE
    participation_res = await session.execute(
        select(HabitatParticipation).where(
            HabitatParticipation.habitat_id == habitat_id,
            HabitatParticipation.ai_identity_id == ai_identity_id,
            HabitatParticipation.state == "ACTIVE"
        )
    )
    participation = participation_res.scalar_one_or_none()
    if not participation:
        raise AppError(ErrorCode.PERMISSION_DENIED, "AI Identity does not have an active participation in this Habitat.")
        
    ai_identity = await session.get(AIIdentity, ai_identity_id)
    
    # 3. Get Default Binding
    binding_res = await session.execute(
        select(CognitiveBinding).where(
            CognitiveBinding.ai_identity_id == ai_identity_id,
            CognitiveBinding.is_default == True
        )
    )
    binding = binding_res.scalar_one_or_none()
    
    # 4. Construct Context
    context = Context(
        habitat_id=habitat_id,
        habitat_name=habitat.name,
        ai_identity_name=ai_identity.name,
        available_tools=["mock_tool"]
    )
    
    # 5. Instantiate Volatile Runtime
    runtime = RuntimeSession(ai_identity_id, habitat_id, binding)
    
    # 6. Execute cognitive cycle (I-11 Intent is data, not side-effect)
    intent = runtime.tick(context, observation)
    
    # We return the Intent without doing any commits or executions
    return success_response(data=intent.model_dump(mode="json"))
