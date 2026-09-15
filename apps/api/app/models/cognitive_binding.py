from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utc_now


class CognitiveBinding(Base):
    """Configuration mapping an AIIdentity to a Cognitive Provider (LLM)."""
    __tablename__ = "cognitive_bindings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ai_identity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_identities.id", ondelete="RESTRICT"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    
    # Opaque pointer to Secret Manager; null for local unauthenticated models
    credential_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Selects the active brain. Handled at application level.
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
