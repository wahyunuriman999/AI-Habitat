from datetime import datetime, timezone
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utc_now


class HabitatParticipation(Base):
    """AI contextual relationship to a Habitat.
    
    Provides explicit participation without implying authority.
    """
    __tablename__ = "habitat_participations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ai_identity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_identities.id", ondelete="RESTRICT"), nullable=False)
    habitat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("habitats.id", ondelete="RESTRICT"), nullable=False)
    state: Mapped[str] = mapped_column(String, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("ai_identity_id", "habitat_id", name="uq_habitat_participations_ai_habitat"),
        CheckConstraint("state IN ('ACTIVE', 'ARCHIVED')", name="habitat_participations_state_check"),
    )
