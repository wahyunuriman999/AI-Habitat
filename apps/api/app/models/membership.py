from datetime import datetime, timezone
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utc_now


class HabitatMembership(Base):
    """Human relationship to a Habitat.
    
    Provides administrative authority and membership boundaries.
    """
    __tablename__ = "habitat_memberships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    habitat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("habitats.id", ondelete="RESTRICT"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("user_id", "habitat_id", name="uq_habitat_memberships_user_habitat"),
        CheckConstraint("role IN ('OWNER', 'MEMBER')", name="habitat_memberships_role_check"),
    )
