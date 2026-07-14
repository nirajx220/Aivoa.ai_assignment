from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    interaction = crud.create_interaction(db, payload.dict(), created_via="form")
    return interaction


@router.get("", response_model=list[schemas.InteractionOut])
def list_interactions(hcp_name: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.list_interactions(db, hcp_name=hcp_name)


@router.get("/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = crud.get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    return interaction


@router.put("/{interaction_id}", response_model=schemas.InteractionOut)
def edit_interaction(interaction_id: str, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    interaction = crud.update_interaction(db, interaction_id, payload.dict(exclude_unset=True))
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    return interaction


@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: str, db: Session = Depends(get_db)):
    ok = crud.delete_interaction(db, interaction_id)
    if not ok:
        raise HTTPException(404, "Interaction not found")
    return {"deleted": True}


@router.get("/hcps/search", response_model=list[schemas.HCPOut])
def search_hcps(q: str = "", db: Session = Depends(get_db)):
    return crud.search_hcps(db, q)
