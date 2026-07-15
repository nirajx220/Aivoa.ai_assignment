"""
Central app configuration. Reads everything from environment variables
(loaded from backend/.env via python-dotenv). No secrets are hard-coded.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")         
    GROQ_PRIMARY_MODEL: str = os.getenv("GROQ_PRIMARY_MODEL", "llama-3.1-8b-instant")
    GROQ_CONTEXT_MODEL: str = os.getenv("GROQ_CONTEXT_MODEL", "llama-3.3-70b-versatile")

    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/hcp_crm",
    )

    # CORS. Use a comma-separated list for multiple allowed frontend URLs.
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

    @property
    def FRONTEND_ORIGINS(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.FRONTEND_ORIGIN.split(",")
            if origin.strip()
        ]


settings = Settings()

if not settings.GROQ_API_KEY:
    print("[WARN] GROQ_API_KEY is not set. Add it to backend/.env before running the agent.")
