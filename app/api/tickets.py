"""Read a ticket's processing status and the agent's result (used by the demo page)."""

import json
from contextlib import closing

from fastapi import APIRouter, HTTPException

from app.api.models import TicketStatus
from app.db.database import get_connection

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/{ticket_id}", response_model=TicketStatus)
def get_ticket(ticket_id: str):
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT ticket_id, status, category, result FROM tickets WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    ticket = dict(row)
    ticket["result"] = json.loads(ticket["result"]) if ticket["result"] else None
    return ticket
