"""
ORM models. Works unchanged on Postgres or MySQL.
"""
import uuid
import datetime as dt

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class HCP(Base):
    """A Healthcare Professional the rep interacts with."""
    __tablename__ = "hcps"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False, index=True)
    specialty = Column(String(255), nullable=True)
    hospital = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    """A single logged HCP interaction (meeting, call, email, etc.)."""
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=True)
    hcp_name = Column(String(255), nullable=True)  # denormalized, used before HCP is matched/created

    interaction_type = Column(
        Enum("Meeting", "Call", "Email", "Conference", "Sample Drop", "Other", name="interaction_type_enum"),
        default="Meeting",
    )
    interaction_date = Column(String(20), nullable=True)   # YYYY-MM-DD
    interaction_time = Column(String(10), nullable=True)   # HH:MM

    attendees = Column(String(500), nullable=True)
    topics = Column(Text, nullable=True)

    materials_shared = Column(JSON, default=list)      # ["Brochure", ...]
    samples_distributed = Column(JSON, default=list)   # ["Sample A", ...]

    sentiment = Column(Enum("Positive", "Neutral", "Negative", name="sentiment_enum"), nullable=True)
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)

    # Raw text the rep typed in chat, kept for audit / re-summarization
    source_text = Column(Text, nullable=True)
    created_via = Column(Enum("form", "chat", name="created_via_enum"), default="form")

    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    followups = relationship("FollowUp", back_populates="interaction", cascade="all, delete-orphan")


class FollowUp(Base):
    """A follow-up task created by the schedule_followup tool."""
    __tablename__ = "followups"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    interaction_id = Column(String(36), ForeignKey("interactions.id"), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(String(20), nullable=True)  # YYYY-MM-DD
    status = Column(Enum("Pending", "Done", name="followup_status_enum"), default="Pending")
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    interaction = relationship("Interaction", back_populates="followups")
