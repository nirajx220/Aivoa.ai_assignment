"""
Tools the LangGraph agent can call. Each tool is a plain function taking a
DB session + args dict and returning a plain dict result. They are called
manually by the "execute_tool" node in graph.py (see that file for why we
don't rely on Groq-native function calling for gemma2-9b-it).

Tool 1: log_interaction      (mandatory)
Tool 2: edit_interaction     (mandatory)
Tool 3: delete_interaction
Tool 4: search_hcp
Tool 5: get_interaction_history
Tool 6: schedule_followup
"""
import json
import re
import datetime as dt
from sqlalchemy.orm import Session

from app import crud
from app.agent.llm import primary_llm, context_llm

FIELD_KEYS = [
    "hcp_name", "interaction_type", "interaction_date", "interaction_time",
    "attendees", "topics", "materials_shared", "samples_distributed",
    "sentiment", "outcomes", "follow_up_actions",
]

EXTRACTION_SYSTEM_PROMPT = f"""You extract structured HCP sales-interaction data from a sales
rep's free text. Return ONLY a JSON object with any of these keys that are
present in the text (omit keys not mentioned): {FIELD_KEYS}.
interaction_type must be one of: Meeting, Call, Email, Conference, Sample Drop, Other.
sentiment must be one of: Positive, Neutral, Negative.
interaction_date must be YYYY-MM-DD. Today's date is {dt.date.today().isoformat()}.
interaction_time must be 24-hour HH:MM.
materials_shared and samples_distributed are arrays of strings.
No prose, no markdown fences - JSON only.
"""

EDIT_EXTRACTION_SYSTEM_PROMPT = f"""You extract ONLY the new/changed field values from an edit
instruction for an HCP CRM interaction. Return ONLY a JSON object with any of
these keys that are changed: {FIELD_KEYS}. Omit fields not being edited.
If the rep says "change the name to James", return {{"hcp_name": "James"}}.
If the rep says "make the time 10 pm", return {{"interaction_time": "22:00"}}.
interaction_date must be YYYY-MM-DD. Today's date is {dt.date.today().isoformat()}.
interaction_time must be 24-hour HH:MM.
No prose, no markdown fences - JSON only.
"""


def _parse_date(value: str) -> str:
    if not value:
        return value
    raw = str(value).strip()
    if not raw or raw.lower() in {"unknown", "n/a", "none", "null"}:
        return None

    today = dt.date.today()
    lower = raw.lower()
    if lower == "today":
        return today.isoformat()
    if lower == "tomorrow":
        return (today + dt.timedelta(days=1)).isoformat()
    if lower == "yesterday":
        return (today - dt.timedelta(days=1)).isoformat()

    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", lower)
    cleaned = cleaned.replace(",", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    formats = [
        "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y",
        "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
    ]
    for fmt in formats:
        try:
            return dt.datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            pass
    return raw


def _parse_time(value: str) -> str:
    if not value:
        return value
    raw = str(value).strip()
    if not raw or raw.lower() in {"unknown", "n/a", "none", "null"}:
        return None

    cleaned = raw.lower().replace(".", "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", cleaned)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        meridiem = match.group(3)
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"
    return raw


def _normalize_extracted_fields(fields: dict) -> dict:
    normalized = {
        key: value
        for key, value in fields.items()
        if key in FIELD_KEYS and value not in (None, "", [], "unknown", "Unknown")
    }
    if "interaction_date" in normalized:
        parsed = _parse_date(normalized["interaction_date"])
        if parsed:
            normalized["interaction_date"] = parsed
        else:
            normalized.pop("interaction_date", None)
    if "interaction_time" in normalized:
        parsed = _parse_time(normalized["interaction_time"])
        if parsed:
            normalized["interaction_time"] = parsed
        else:
            normalized.pop("interaction_time", None)
    return normalized


def _extract_fields_with_llm(text: str, edit_mode: bool = False) -> dict:
    """Uses the PRIMARY model (gemma2-9b-it) for fast structured extraction."""
    messages = [
        ("system", EDIT_EXTRACTION_SYSTEM_PROMPT if edit_mode else EXTRACTION_SYSTEM_PROMPT),
        ("user", text),
    ]
    response = primary_llm.invoke(messages)
    raw = response.content.strip().strip("`")
    if raw.lower().startswith("json"):
        raw = raw[4:].strip()
    try:
        parsed = json.loads(raw)
        return _normalize_extracted_fields(parsed if isinstance(parsed, dict) else {})
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------
# Tool 1 (mandatory): log_interaction
# ---------------------------------------------------------------------
def log_interaction(db: Session, args: dict) -> dict:
    """
    Captures a brand-new interaction. `args["text"]` is the rep's raw
    message; the LLM (gemma2-9b-it) extracts entities from it, which are
    then persisted to the interactions table.
    """
    text = args.get("text", "")
    extracted = _extract_fields_with_llm(text)
    extracted["source_text"] = text
    interaction = crud.create_interaction(db, extracted, created_via="chat")
    return {
        "interaction_id": interaction.id,
        "updates": extracted,
        "message": f"Logged a new {extracted.get('interaction_type', 'Meeting').lower()}"
                    f"{' with ' + extracted['hcp_name'] if extracted.get('hcp_name') else ''}.",
    }


# ---------------------------------------------------------------------
# Tool 2 (mandatory): edit_interaction
# ---------------------------------------------------------------------
def edit_interaction(db: Session, args: dict) -> dict:
    """
    Modifies fields on an already-logged interaction. `args["interaction_id"]`
    identifies the record; `args["text"]` is the rep's edit instruction,
    which the LLM turns into a partial field update.
    """
    interaction_id = args.get("interaction_id")
    text = args.get("text", "")
    extracted = _extract_fields_with_llm(text, edit_mode=True)

    if not interaction_id:
        return {"error": "No active interaction to edit."}

    interaction = crud.update_interaction(db, interaction_id, extracted)
    if not interaction:
        return {"error": "Interaction not found."}

    return {
        "interaction_id": interaction.id,
        "updates": extracted,
        "message": "Updated the logged interaction.",
    }


# ---------------------------------------------------------------------
# Tool 3: delete_interaction (also used for "clear field" / "clear form")
# ---------------------------------------------------------------------
def delete_interaction(db: Session, args: dict) -> dict:
    interaction_id = args.get("interaction_id")
    fields = args.get("fields")  # optional: clear only specific fields
    clear_all = args.get("clear_all", False)

    if not interaction_id:
        return {"error": "No active interaction to delete/clear."}

    if fields:
        crud.clear_interaction_fields(db, interaction_id, fields)
        return {"cleared_fields": fields, "message": f"Cleared {', '.join(fields)}."}

    if clear_all:
        crud.delete_interaction(db, interaction_id)
        return {"deleted": True, "message": "Deleted the interaction."}

    return {"error": "Specify either fields to clear or clear_all."}


# ---------------------------------------------------------------------
# Tool 4: search_hcp
# ---------------------------------------------------------------------
def search_hcp(db: Session, args: dict) -> dict:
    query = args.get("query", "")
    matches = crud.search_hcps(db, query)
    return {
        "matches": [{"id": h.id, "name": h.name, "specialty": h.specialty} for h in matches],
        "message": f"Found {len(matches)} matching HCP(s) for '{query}'.",
    }


# ---------------------------------------------------------------------
# Tool 5: get_interaction_history
# ---------------------------------------------------------------------
def get_interaction_history(db: Session, args: dict) -> dict:
    """
    Pulls past interactions for an HCP and uses the CONTEXT model
    (llama-3.3-70b-versatile) to summarize them, since history can be long.
    """
    hcp_name = args.get("hcp_name", "")
    interactions = crud.list_interactions(db, hcp_name=hcp_name, limit=20)

    if not interactions:
        return {"message": f"No prior interactions found for {hcp_name}.", "history": []}

    history_text = "\n".join(
        f"- {i.interaction_date or '?'}: {i.topics or ''} (sentiment: {i.sentiment or 'n/a'})"
        for i in interactions
    )
    summary_resp = context_llm.invoke([
        ("system", "Summarize this HCP's interaction history in 2-3 sentences for a sales rep."),
        ("user", history_text),
    ])
    return {
        "message": summary_resp.content.strip(),
        "history": [{"date": i.interaction_date, "topics": i.topics, "sentiment": i.sentiment} for i in interactions],
    }


# ---------------------------------------------------------------------
# Tool 6: schedule_followup
# ---------------------------------------------------------------------
def schedule_followup(db: Session, args: dict) -> dict:
    interaction_id = args.get("interaction_id")
    description = args.get("description", "Follow up with HCP")
    due_date = args.get("due_date")

    if not interaction_id:
        return {"error": "No active interaction to attach a follow-up to."}

    followup = crud.create_followup(db, interaction_id, description, due_date)
    return {
        "followup_id": followup.id,
        "message": f"Scheduled follow-up: {description}" + (f" (due {due_date})" if due_date else ""),
    }


TOOL_REGISTRY = {
    "log_interaction": log_interaction,
    "edit_interaction": edit_interaction,
    "delete_interaction": delete_interaction,
    "search_hcp": search_hcp,
    "get_interaction_history": get_interaction_history,
    "schedule_followup": schedule_followup,
}
