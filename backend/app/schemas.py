"""
Pydantic schemas for request/response validation.
"""
from typing import Optional, List
from pydantic import BaseModel


class InteractionBase(BaseModel):
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = "Meeting"
    interaction_date: Optional[str] = None
    interaction_time: Optional[str] = None
    attendees: Optional[str] = None
    topics: Optional[str] = None
    materials_shared: Optional[List[str]] = []
    samples_distributed: Optional[List[str]] = []
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionCreate(InteractionBase):
    created_via: Optional[str] = "form"


class InteractionUpdate(InteractionBase):
    """All fields optional - only send what changed."""
    pass


class InteractionOut(InteractionBase):
    id: str
    hcp_id: Optional[str] = None
    created_via: str

    class Config:
        from_attributes = True


class HCPOut(BaseModel):
    id: str
    name: str
    specialty: Optional[str] = None
    hospital: Optional[str] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    updates: dict = {}
    clear_fields: List[str] = []
    clear_all: bool = False
    interaction_id: Optional[str] = None
