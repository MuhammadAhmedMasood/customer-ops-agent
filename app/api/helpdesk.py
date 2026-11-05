"""Mock helpdesk API: store replies to a ticket, list them, approve pending actions."""

from contextlib import closing

from fastapi import APIRouter, HTTPException

from app.api.models import ReplyIn, ReplyOut
from app.db.database import get_connection

router = APIRouter(prefix="/helpdesk", tags=["helpdesk"])


@router.post("/{ticket_id}/reply", response_model=ReplyOut, status_code=201)
def create_reply(ticket_id: str, reply: ReplyIn):
    status = "pending_approval" if reply.needs_approval else "sent"
    with closing(get_connection()) as conn:
        cur = conn.execute(
            "INSERT INTO replies (ticket_id, reply_text, action, needs_approval, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (ticket_id, reply.reply_text, reply.action, reply.needs_approval, status),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM replies WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


@router.get("/{ticket_id}", response_model=list[ReplyOut])
def list_replies(ticket_id: str):
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT * FROM replies WHERE ticket_id = ? ORDER BY id", (ticket_id,)
        ).fetchall()
    return [dict(row) for row in rows]


@router.post("/{ticket_id}/approve", response_model=ReplyOut)
def approve_reply(ticket_id: str):
    """A human approves the ticket's pending action (e.g. a refund over £50)."""
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT id FROM replies WHERE ticket_id = ? AND status = 'pending_approval' "
            "ORDER BY id DESC LIMIT 1",
            (ticket_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"No pending action for ticket {ticket_id}")

        conn.execute("UPDATE replies SET status = 'approved' WHERE id = ?", (row["id"],))
        conn.commit()
        updated = conn.execute("SELECT * FROM replies WHERE id = ?", (row["id"],)).fetchone()
    return dict(updated)
