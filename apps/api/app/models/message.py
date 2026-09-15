from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utc_now


class Message(Base):
    """An individual message within a conversation."""
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="RESTRICT"), nullable=False)
    
    # Strictly bound roles: system, user, assistant, tool
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    
    # If role='user', who sent it?
    sender_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    
    # If role='assistant', which AI generated it?
    sender_ai_identity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_identities.id", ondelete="RESTRICT"), nullable=True)
    
    # If role='tool', which tool execution does this correspond to?
    tool_call_id: Mapped[str | None] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        CheckConstraint("role IN ('system', 'user', 'assistant', 'tool')", name="messages_role_check"),
    )
