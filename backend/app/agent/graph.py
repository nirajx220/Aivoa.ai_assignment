"""
The LangGraph agent.

Role of this agent (per assignment): it sits in the "Log Interaction Screen"
chat panel and manages the full lifecycle of an HCP interaction record on
the rep's behalf - understanding free text, deciding which CRM action it
implies, executing that action against the database, and replying in
plain language. It effectively replaces manual form-filling with
conversation while keeping the same underlying data model as the
structured form.

Graph shape:

    START -> router -> execute_tool -> respond -> END
                 \\_____________________________/
                  (router can also skip straight to respond
                   if the message needs no tool, e.g. a question)

- "router" (gemma2-9b-it): classifies the user's message into one of the
  6 tools in tools.py, or "none", and extracts the arguments that tool needs.
- "execute_tool": runs the plain Python tool function against the DB.
- "respond" (gemma2-9b-it, falling back to llama-3.3-70b-versatile for
  history-heavy turns): turns the tool's result into a short, friendly
  chat reply, and packages the field updates the frontend should apply.

Note on model choice: Groq's native OpenAI-style tool-calling is not
reliably supported on every model, and the assignment mandates gemma2-9b-it
specifically. So instead of LangGraph's built-in `bind_tools` / `ToolNode`,
we ask the LLM to return small JSON "decisions" that we parse and dispatch
ourselves. This keeps the mandated model compatible while still following
the standard LangGraph plan -> act -> respond pattern.
"""
import json
from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.llm import primary_llm
from app.agent import tools as tool_fns

TOOL_NAMES = list(tool_fns.TOOL_REGISTRY.keys())

ROUTER_SYSTEM_PROMPT = f"""You are the routing brain for an HCP (Healthcare
Professional) sales-CRM chat assistant. Given the conversation and the
rep's latest message, decide which single tool to call, if any.

Available tools: {TOOL_NAMES}
- log_interaction: rep is describing a NEW interaction to log (args: text)
- edit_interaction: rep wants to change/add info on the CURRENT interaction (args: text)
- delete_interaction: rep wants to clear a field or delete the whole interaction
  (args: fields = list of field names to clear, OR clear_all = true)
  Valid field names: hcp_name, interaction_type, interaction_date, interaction_time,
  attendees, topics, materials_shared, samples_distributed, sentiment, outcomes, follow_up_actions
- search_hcp: rep is looking up an HCP by name (args: query)
- get_interaction_history: rep wants past interaction history for an HCP (args: hcp_name)
- schedule_followup: rep wants to schedule/create a follow-up task (args: description, due_date)
- none: message is just a question or chit-chat, no CRM action needed

Respond with ONLY JSON: {{"tool": "<tool_name_or_none>", "args": {{...}}}}
No prose, no markdown fences.
"""


def router_node(state: AgentState) -> AgentState:
    history_snippet = "\n".join(
        f"{m['role']}: {m['content']}" for m in state.get("chat_history", [])[-6:]
    )
    prompt = f"Conversation so far:\n{history_snippet}\n\nLatest message: {state['user_message']}"

    resp = primary_llm.invoke([
        ("system", ROUTER_SYSTEM_PROMPT),
        ("user", prompt),
    ])
    raw = resp.content.strip().strip("`")
    if raw.lower().startswith("json"):
        raw = raw[4:].strip()

    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        decision = {"tool": "none", "args": {}}

    tool_name = decision.get("tool", "none")
    tool_args = decision.get("args", {}) or {}

    # always carry the raw text through for tools that need it
    tool_args.setdefault("text", state["user_message"])
    tool_args.setdefault("interaction_id", state.get("interaction_id"))

    state["tool_name"] = tool_name if tool_name in TOOL_NAMES else None
    state["tool_args"] = tool_args
    return state


def execute_tool_node(state: AgentState, db) -> AgentState:
    tool_name = state.get("tool_name")
    if not tool_name:
        state["tool_result"] = {}
        return state

    tool_fn = tool_fns.TOOL_REGISTRY[tool_name]
    result = tool_fn(db, state["tool_args"])
    state["tool_result"] = result

    if result.get("interaction_id"):
        state["interaction_id"] = result["interaction_id"]
    return state


def respond_node(state: AgentState) -> AgentState:
    result = state.get("tool_result", {})
    tool_name = state.get("tool_name")

    state["updates"] = result.get("updates", {})
    state["clear_fields"] = result.get("cleared_fields", [])
    state["clear_all"] = bool(result.get("deleted"))
    state["interaction_id"] = state.get("interaction_id")

    if result.get("error"):
        state["reply"] = result["error"]
        return state

    if tool_name is None:
        # No tool needed - just have the primary model answer conversationally.
        resp = primary_llm.invoke([
            ("system", "You are a concise, friendly HCP sales-CRM assistant. Answer helpfully in 1-3 sentences."),
            ("user", state["user_message"]),
        ])
        state["reply"] = resp.content.strip()
        return state

    # Tool already produced a good human-readable message; use it directly
    # (keeps latency low - no extra LLM round-trip needed on the happy path).
    state["reply"] = result.get("message", "Done.")
    return state


def build_graph(db):
    """
    `db` is a live SQLAlchemy session for this request, closed over so the
    execute_tool node can use it without threading it through state.
    """
    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("execute_tool", lambda state: execute_tool_node(state, db))
    graph.add_node("respond", respond_node)

    graph.set_entry_point("router")
    graph.add_edge("router", "execute_tool")
    graph.add_edge("execute_tool", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


def run_agent(db, session_id: str, message: str, chat_history: list, interaction_id: str = None) -> dict:
    app_graph = build_graph(db)
    initial_state: AgentState = {
        "session_id": session_id,
        "user_message": message,
        "chat_history": chat_history,
        "interaction_id": interaction_id,
    }
    final_state = app_graph.invoke(initial_state)
    return {
        "reply": final_state.get("reply", ""),
        "tool_used": final_state.get("tool_name"),
        "updates": final_state.get("updates", {}),
        "clear_fields": final_state.get("clear_fields", []),
        "clear_all": final_state.get("clear_all", False),
        "interaction_id": final_state.get("interaction_id"),
    }
