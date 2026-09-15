from app.core.database import Base

from app.models.user import User
from app.models.habitat import Habitat
from app.models.ai_identity import AIIdentity
from app.models.membership import HabitatMembership
from app.models.participation import HabitatParticipation
from app.models.cognitive_binding import CognitiveBinding

# Expose models and Base to Alembic and other modules easily
__all__ = [
    "Base",
    "User",
    "Habitat",
    "AIIdentity",
    "HabitatMembership",
    "HabitatParticipation",
    "CognitiveBinding",
]
