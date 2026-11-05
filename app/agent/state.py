"""The state that flows through the graph. Each node reads it and returns updates."""

from typing import TypedDict


# total=False: keys can be missing until a node fills them in.
class TicketState(TypedDict, total=False):
    # From the webhook
    ticket_id: str
    customer_email: str
    subject: str
    message: str
    order_id: str | None
    today: str  # optional ISO date; evals set it so results don't drift. Default: real today.

    # Filled in by nodes
    injection_flagged: bool  # check_injection
    category: str  # classify
    order: dict | None  # lookup_order (None if no order found)
    facts: list[str]  # compute_facts: dates and deadlines worked out in code
    policy_snippets: list[dict]  # retrieve_policy: [{"section": "3.2", "text": "..."}]
    draft_reply: str  # draft_reply
    proposed_action: str  # draft_reply: none / refund / reship / escalate
    needs_approval: bool  # approval_check
    citations: list[str]  # draft_reply: section numbers cited in the reply, e.g. ["3.2"]
