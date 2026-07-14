"""
Central app configuration. Reads everything from environment variables
(loaded from backend/.env via python-dotenv). No secrets are hard-coded.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads backend/.env if present


class Settings:
    # ---- Groq / LLM ----
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")          # <-- set in .env
    GROQ_PRIMARY_MODEL: str = os.getenv("GROQ_PRIMARY_MODEL", "llama-3.1-8b-instant")
    GROQ_CONTEXT_MODEL: str = os.getenv("GROQ_CONTEXT_MODEL", "llama-3.3-70b-versatile")

    # ---- Database ----
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/hcp_crm",
    )

    # ---- CORS ----
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")


settings = Settings()

if not settings.GROQ_API_KEY:
    # We don't crash on import (so `alembic`/tooling can still run), but the
    # agent will refuse to run without a key. See agent/llm.py.
    print("[WARN] GROQ_API_KEY is not set. Add it to backend/.env before running the agent.")
