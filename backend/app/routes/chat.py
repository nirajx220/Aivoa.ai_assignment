from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.agent.graph import run_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory per-session chat history + active interaction id.
# Fine for an assignment/demo; swap for Redis or a DB table in production.
_SESSIONS: dict = {}


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    session = _SESSIONS.setdefault(payload.session_id, {"history": [], "interaction_id": None})

    result = run_agent(
        db=db,
        session_id=payload.session_id,
        message=payload.message,
        chat_history=session["history"],
        interaction_id=session["interaction_id"],
    )

    session["history"].append({"role": "user", "content": payload.message})
    session["history"].append({"role": "assistant", "content": result["reply"]})
    session["interaction_id"] = result.get("interaction_id") or session["interaction_id"]

    return schemas.ChatResponse(
        reply=result["reply"],
        tool_used=result.get("tool_used"),
        updates=result.get("updates", {}),
        clear_fields=result.get("clear_fields", []),
        clear_all=result.get("clear_all", False),
        interaction_id=session["interaction_id"],
    )
