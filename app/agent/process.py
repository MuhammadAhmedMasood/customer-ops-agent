"""Processing a ticket after the webhook has accepted it: run the agent graph."""

from contextlib import closing

from app.agent.graph import graph
from app.db.database import get_connection
from app.tracing import tracing_config


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
        _save(ticket_id, status="failed", category=None)
        return

    if result["injection_flagged"]:
        print(f"[process_ticket] {ticket_id}: flagged, escalated", flush=True)
        _save(ticket_id, status="flagged", category=None)
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
    _save(ticket_id, status="processed", category=result["category"])


def _save(ticket_id: str, status: str, category: str | None) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            "UPDATE tickets SET status = ?, category = ? WHERE ticket_id = ?",
            (status, category, ticket_id),
        )
        conn.commit()
