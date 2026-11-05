"""Processing a ticket after the webhook has accepted it: run the agent graph."""

import json
from contextlib import closing

from app.agent.graph import graph
from app.db.database import get_connection
from app.tracing import tracing_config

# The parts of the final state worth showing on the demo page (GET /tickets/{id}).
RESULT_KEYS = [
    "injection_flagged", "category", "order_id", "order", "facts", "policy_snippets",
    "draft_reply", "proposed_action", "needs_approval", "citations",
]


def process_ticket(ticket_id: str) -> None:
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT ticket_id, customer_email, subject, message, order_id "
            "FROM tickets WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchone()

    try:
        result = graph.invoke(dict(row), config=tracing_config(ticket_id, tags=["webhook"]))
    except Exception as exc:
        # Background tasks have no caller to report errors to, so record the failure.
        print(f"[process_ticket] {ticket_id} failed: {exc!r}", flush=True)
        _save(ticket_id, status="failed", category=None, result=None)
        return

    summary = {key: result.get(key) for key in RESULT_KEYS}

    if result["injection_flagged"]:
        print(f"[process_ticket] {ticket_id}: flagged, escalated", flush=True)
        _save(ticket_id, status="flagged", category=None, result=summary)
        return

    order = result.get("order")
    print(
        f"[process_ticket] {ticket_id}: category={result['category']}, "
        f"order={order['order_id'] + ' (' + order['status'] + ')' if order else None}, "
        f"retrieved={[s['section'] for s in result['policy_snippets']]}, "
        f"action={result['proposed_action']}, needs_approval={result['needs_approval']}, "
        f"citations={result['citations']}",
        flush=True,
    )
    _save(ticket_id, status="processed", category=result["category"], result=summary)


def _save(ticket_id: str, status: str, category: str | None, result: dict | None) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            "UPDATE tickets SET status = ?, category = ?, result = ? WHERE ticket_id = ?",
            (status, category, json.dumps(result) if result else None, ticket_id),
        )
        conn.commit()
