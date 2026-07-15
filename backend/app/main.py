from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routes import interactions, chat

# Creates tables if they don't exist yet. For real migrations, swap for Alembic.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First HCP CRM", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
