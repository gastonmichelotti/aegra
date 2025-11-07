"""Soporte ODS ReactAgent Graph - Main graph definition"""

from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import SoporteState
from .context import SoporteContext
from .tools import TOOLS
from .nodes import load_context_node, agent_node, observer_node


def route_agent_output(state: SoporteState) -> Literal["tools", "observer", "__end__"]:
    """Routing function to determine next node after agent

    Args:
        state: Current graph state

    Returns:
        str: Next node name ("tools", "observer", or "__end__")
    """
    messages = state.messages
    last_message = messages[-1] if messages else None

    # Validate last message is an AIMessage
    if not isinstance(last_message, AIMessage):
        return "__end__"

    # Check if there are tool calls to execute
    if last_message.tool_calls:
        return "tools"

    # Check if we should run observer (conversation ending without tool calls)
    if state.should_observe:
        return "observer"

    # Otherwise, end the conversation
    return "__end__"


# Build the graph with context schema
builder = StateGraph(SoporteState, context_schema=SoporteContext)

# Add nodes
builder.add_node("load_context", load_context_node)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_node("observer", observer_node)

# Define edges
builder.set_entry_point("load_context")  # Always start by loading context
builder.add_edge("load_context", "agent")  # After loading context, go to agent

# Add conditional routing after agent
builder.add_conditional_edges(
    "agent",
    route_agent_output,
    {
        "tools": "tools",
        "observer": "observer",
        "__end__": END,
    }
)

builder.add_edge("tools", "agent")  # After tools, go back to agent
builder.add_edge("observer", END)  # After observer, end

# Compile the graph
# NOTE: Aegra will automatically inject checkpointer and store during compilation
graph = builder.compile(name="Soporte ODS Agent")
