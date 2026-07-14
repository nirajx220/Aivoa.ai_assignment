# AI-First HCP CRM — Log Interaction Module

An AI-first Customer Relationship Management module for pharma/life-science
field reps, focused on the **HCP (Healthcare Professional) Log Interaction
Screen**. Reps can log a visit either by filling a structured form or by
typing/chatting naturally — both write to the same record, kept in sync
through a LangGraph agent.

## Tech stack (per spec)

| Layer            | Choice                                              |
|-------------------|-----------------------------------------------------|
| Frontend          | React + Redux (Redux Toolkit)                       |
| Backend           | Python, FastAPI                                     |
| AI agent framework| LangGraph                                            |
| LLMs              | Groq — `gemma2-9b-it` (primary), `llama-3.3-70b-versatile` (context) |
| Database          | MySQL / Postgres via SQLAlchemy                      |
| Font              | Google Inter                                         |

## Folder structure

```
hcp-ai-crm/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example              # <- copy to .env, add your GROQ_API_KEY + DATABASE_URL
│   ├── run.py                    # uvicorn entrypoint
│   └── app/
│       ├── main.py               # FastAPI app, CORS, router registration
│       ├── config.py             # reads .env
│       ├── database.py           # SQLAlchemy engine/session
│       ├── models.py             # HCP, Interaction, FollowUp tables
│       ├── schemas.py            # Pydantic request/response models
│       ├── crud.py               # shared DB helpers (used by REST + agent tools)
│       ├── routes/
│       │   ├── interactions.py   # REST endpoints for the structured form
│       │   └── chat.py           # /api/chat -> invokes the LangGraph agent
│       └── agent/
│           ├── llm.py            # Groq client setup <- GROQ_API_KEY used here
│           ├── state.py          # LangGraph state schema
│           ├── tools.py          # the 6 agent tools
│           └── graph.py          # the LangGraph StateGraph (router->tool->respond)
└── frontend/
    ├── package.json
    ├── .env.example              # REACT_APP_API_BASE_URL (no keys needed client-side)
    ├── public/index.html         # loads Google Inter
    └── src/
        ├── index.js / App.js
        ├── api/api.js            # axios client
        ├── store/                # Redux Toolkit store + interactionSlice
        └── components/
            ├── LogInteractionScreen.js   # split-screen: form | chat
            ├── StructuredForm.js
            ├── ChatInterface.js
            └── LogInteractionScreen.css
```

## Where to put your API keys

Only one secret is needed, and it only ever lives on the **backend**:

```
backend/.env
-------------
GROQ_API_KEY=          # <- get this from https://console.groq.com/keys
GROQ_PRIMARY_MODEL=gemma2-9b-it
GROQ_CONTEXT_MODEL=llama-3.3-70b-versatile
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/hcp_crm
```

Copy `backend/.env.example` to `backend/.env` and fill it in. The key is
read once in `backend/app/config.py` and consumed in
`backend/app/agent/llm.py` — nowhere else in the codebase touches it, and
the React frontend never sees it (it only talks to your own FastAPI
backend).

## Running it locally

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in GROQ_API_KEY and DATABASE_URL
python run.py                # http://localhost:8000
```

**Database**: create an empty `hcp_crm` database in Postgres or MySQL first
(tables are auto-created on startup via `Base.metadata.create_all`).

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm start                    # http://localhost:3000
```

---

## LangGraph AI Agent & Tools

### Role of the LangGraph agent

The agent lives behind the chat panel of the Log Interaction Screen and
acts as the rep's conversational front door into the CRM. Instead of
requiring the rep to fill in ten separate form fields, they can just
describe what happened — the agent figures out *what CRM action that
implies* (log a new visit, edit one just logged, look up an HCP's history,
schedule a follow-up, or clear something that's wrong), executes that
action against the database, and returns a short confirmation, while also
pushing the structured field updates back to the UI so the form panel
stays in sync in real time. In effect, the agent is a thin reasoning layer
sitting between free-text and the same relational schema the structured
form writes to — reps get the speed of chat without the CRM ever losing
structured, queryable data.

Concretely, the agent (`backend/app/agent/graph.py`) runs a 3-step
LangGraph flow on every message:
1. **router** (`gemma2-9b-it`) — classifies the message into one of the
   tools below (or "none" for small talk/questions) and extracts the
   arguments that tool needs.
2. **execute_tool** — runs the corresponding Python function against the
   database.
3. **respond** — turns the tool's result into a short chat reply and
   packages the field-level updates for the frontend to apply.

### The six tools (`backend/app/agent/tools.py`)

1. **`log_interaction`** *(mandatory)* — Captures a brand-new interaction.
   Takes the rep's raw free text, sends it to the primary LLM
   (`gemma2-9b-it`) with an entity-extraction prompt that pulls out HCP
   name, interaction type, date/time, attendees, topics, materials
   shared, samples distributed, sentiment, outcomes, and follow-up
   actions, then persists the result as a new `Interaction` row (creating
   the `HCP` record if it doesn't exist yet).

2. **`edit_interaction`** *(mandatory)* — Modifies the interaction
   currently in progress. Takes an edit instruction in free text (e.g.
   "actually make the sentiment neutral"), re-runs the same LLM
   extraction to get a *partial* update, and applies only those fields to
   the existing row, leaving everything else untouched.

3. **`delete_interaction`** — Handles both "clear this one field" and
   "delete the whole interaction" requests, so the chat can also *undo*
   what it (or the form) just logged, not just add to it.

4. **`search_hcp`** — Looks up HCPs by (partial) name so the agent can
   confirm who a "Dr. Smith" actually refers to before logging against
   them, mirroring the "Search or select HCP" field in the form.

5. **`get_interaction_history`** — Pulls a given HCP's past interactions
   and summarizes them. This is where the **context model**
   (`llama-3.3-70b-versatile`) is used instead of the primary model,
   since summarizing a long history benefits from a larger context
   window and stronger reasoning than the fast primary model needs for
   single-turn extraction.

6. **`schedule_followup`** — Creates a follow-up task tied to the current
   interaction (e.g. "remind me to send the Phase III data next week"),
   writing to a separate `FollowUp` table so follow-ups can later be
   surfaced on a rep's task list.

## Output Deliverables note

This repo is structured to be pushed as-is to a single GitHub repository
(frontend + backend together) with this README as the submission's
explanation of the project and how to run it.
