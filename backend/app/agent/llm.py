"""
Groq LLM clients used by the LangGraph agent.

Per the assignment spec:
  - PRIMARY model: gemma2-9b-it -> used for fast intent routing + structured
    entity extraction (turning a rep's free text into form fields).
  - CONTEXT model: llama-3.3-70b-versatile -> used where a bigger context
    window / stronger reasoning helps, e.g. summarizing a long interaction
    history before the agent replies.

Get your Groq API key at https://console.groq.com/keys and put it in
backend/.env as GROQ_API_KEY (see .env.example). Nothing else in this file
needs to change.
"""
from langchain_groq import ChatGroq
from app.config import settings

# -----------------------------------------------------------------------
# GROQ_API_KEY IS READ HERE. Do not hard-code a key in this file -
# set it in backend/.env instead.
# -----------------------------------------------------------------------
primary_llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,          # <-- Groq API key used here
    model=settings.GROQ_PRIMARY_MODEL,      # gemma2-9b-it
    temperature=0.2,
)

context_llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,          # <-- Groq API key used here
    model=settings.GROQ_CONTEXT_MODEL,      # llama-3.3-70b-versatile
    temperature=0.3,
)
