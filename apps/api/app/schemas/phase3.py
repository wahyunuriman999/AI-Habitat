from datetime import datetime
import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict


# --- Persistent Schemas ---

class CognitiveBindingCreate(BaseModel):
    provider: str
    model: str
    credential_ref: str | None = None
    is_default: bool = False

class CognitiveBindingUpdate(BaseModel):
    is_default: bool

class CognitiveBindingResponse(BaseModel):
    id: uuid.UUID
    ai_identity_id: uuid.UUID
    provider: str
    model: str
    credential_ref: str | None = None
    is_default: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Volatile Schemas (Runtime Boundary) ---

class Context(BaseModel):
    """The situational awareness projected by the Habitat."""
    habitat_id: uuid.UUID
    habitat_name: str
    ai_identity_name: str
    available_tools: list[str]

class Observation(BaseModel):
    """Input event received from the environment."""
    event: str
    content: Any

class Intent(BaseModel):
    """Data representation of a requested action. NOT an execution command."""
    intent_type: str
    payload: dict[str, Any]
    provider_used: str | None = None  # to verify which cognitive engine fulfilled it in tests
