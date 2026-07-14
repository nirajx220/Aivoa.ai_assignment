"""
Shared state object that flows through every node of the LangGraph graph.
"""
from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    session_id: str
    user_message: str
    chat_history: List[Dict[str, str]]     # [{"role": "user"/"assistant", "content": "..."}]

    # set by the router node
    tool_name: Optional[str]
    tool_args: Dict[str, Any]

    # set by the execute_tool node
    tool_result: Dict[str, Any]

    # final output
    reply: str
    updates: Dict[str, Any]
    clear_fields: List[str]
    clear_all: bool
    interaction_id: Optional[str]
