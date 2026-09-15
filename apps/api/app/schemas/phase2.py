from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    id: uuid.UUID
    state: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class HabitatCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class HabitatResponse(BaseModel):
    id: uuid.UUID
    name: str
    state: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AIIdentityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class AIIdentityUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    state: str | None = None


class AIIdentityResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_by_user_id: uuid.UUID
    state: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ParticipationCreate(BaseModel):
    ai_identity_id: uuid.UUID


class ParticipationResponse(BaseModel):
    id: uuid.UUID
    ai_identity_id: uuid.UUID
    habitat_id: uuid.UUID
    state: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
