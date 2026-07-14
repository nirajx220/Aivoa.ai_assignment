"""
Plain CRUD helpers. Shared by:
  - app/routes/interactions.py  (structured-form REST endpoints)
  - app/agent/tools.py          (LangGraph tools used by the chat agent)
Keeping this in one place means the form and the chat agent can never
drift apart in behaviour.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app import models


def find_or_create_hcp(db: Session, name: str) -> Optional[models.HCP]:
    if not name:
        return None
    hcp = db.query(models.HCP).filter(models.HCP.name.ilike(name.strip())).first()
    if not hcp:
        hcp = models.HCP(name=name.strip())
        db.add(hcp)
        db.commit()
        db.refresh(hcp)
    return hcp


def search_hcps(db: Session, query: str, limit: int = 10):
    q = db.query(models.HCP)
    if query:
        q = q.filter(models.HCP.name.ilike(f"%{query}%"))
    return q.limit(limit).all()


def create_interaction(db: Session, data: dict, created_via: str = "form") -> models.Interaction:
    hcp = find_or_create_hcp(db, data.get("hcp_name")) if data.get("hcp_name") else None
    interaction = models.Interaction(
        hcp_id=hcp.id if hcp else None,
        hcp_name=data.get("hcp_name"),
        interaction_type=data.get("interaction_type") or "Meeting",
        interaction_date=data.get("interaction_date"),
        interaction_time=data.get("interaction_time"),
        attendees=data.get("attendees"),
        topics=data.get("topics"),
        materials_shared=data.get("materials_shared") or [],
        samples_distributed=data.get("samples_distributed") or [],
        sentiment=data.get("sentiment"),
        outcomes=data.get("outcomes"),
        follow_up_actions=data.get("follow_up_actions"),
        source_text=data.get("source_text"),
        created_via=created_via,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def get_interaction(db: Session, interaction_id: str) -> Optional[models.Interaction]:
    return db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()


def list_interactions(db: Session, hcp_name: Optional[str] = None, limit: int = 50):
    q = db.query(models.Interaction).order_by(models.Interaction.created_at.desc())
    if hcp_name:
        q = q.filter(models.Interaction.hcp_name.ilike(f"%{hcp_name}%"))
    return q.limit(limit).all()


def update_interaction(db: Session, interaction_id: str, data: dict) -> Optional[models.Interaction]:
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        return None
    if data.get("hcp_name"):
        hcp = find_or_create_hcp(db, data["hcp_name"])
        interaction.hcp_id = hcp.id if hcp else None
    for field, value in data.items():
        if value is not None and hasattr(interaction, field):
            setattr(interaction, field, value)
    db.commit()
    db.refresh(interaction)
    return interaction


def clear_interaction_fields(db: Session, interaction_id: str, fields: list) -> Optional[models.Interaction]:
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        return None
    for field in fields:
        if hasattr(interaction, field):
            current = getattr(interaction, field)
            setattr(interaction, field, [] if isinstance(current, list) else None)
    db.commit()
    db.refresh(interaction)
    return interaction


def delete_interaction(db: Session, interaction_id: str) -> bool:
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        return False
    db.delete(interaction)
    db.commit()
    return True


def create_followup(db: Session, interaction_id: str, description: str, due_date: Optional[str] = None) -> models.FollowUp:
    followup = models.FollowUp(interaction_id=interaction_id, description=description, due_date=due_date)
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return followup
