from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utc_now


class Conversation(Base):
    """A threaded interaction log within a Habitat."""
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    habitat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("habitats.id", ondelete="RESTRICT"), nullable=False)
    
    # Optional descriptive title for the thread
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
