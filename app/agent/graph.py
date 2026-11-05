"""Wire the nodes into a LangGraph graph."""

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    approval_check,
    check_injection,
    classify,
    compute_facts,
    draft_reply,
    escalate_flagged,
    fault_window_check,
    lookup_order,
    retrieve_policy,
    route_after_check,
    write_back,
)
from app.agent.state import TicketState

builder = StateGraph(TicketState)
builder.add_node("check_injection", check_injection)
builder.add_node("escalate_flagged", escalate_flagged)
builder.add_node("classify", classify)
builder.add_node("lookup_order", lookup_order)
builder.add_node("compute_facts", compute_facts)
builder.add_node("retrieve_policy", retrieve_policy)
builder.add_node("draft_reply", draft_reply)
builder.add_node("fault_window_check", fault_window_check)
builder.add_node("approval_check", approval_check)
builder.add_node("write_back", write_back)

builder.add_edge(START, "check_injection")
# route_after_check returns the name of the next node: "escalate_flagged" or "classify".
builder.add_conditional_edges("check_injection", route_after_check, ["escalate_flagged", "classify"])
builder.add_edge("escalate_flagged", "write_back")

builder.add_edge("classify", "lookup_order")
builder.add_edge("lookup_order", "compute_facts")
builder.add_edge("compute_facts", "retrieve_policy")
builder.add_edge("retrieve_policy", "draft_reply")
builder.add_edge("draft_reply", "fault_window_check")
builder.add_edge("fault_window_check", "approval_check")
builder.add_edge("approval_check", "write_back")
builder.add_edge("write_back", END)

graph = builder.compile()
