"""Webhook the helpdesk calls when a new ticket arrives."""

import sqlite3
from contextlib import closing

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.agent.process import process_ticket
from app.api.models import TicketAccepted, TicketIn
from app.api.rate_limit import RateLimiter
from app.db.database import get_connection

router = APIRouter(prefix="/webhook", tags=["webhook"])

# Each IP may send at most 10 tickets per minute.
webhook_limiter = RateLimiter(max_requests=10, window_seconds=60)


@router.post(
    "/ticket",
    response_model=TicketAccepted,
    status_code=202,
    dependencies=[Depends(webhook_limiter)],  # runs before the route; may raise 429
)
def receive_ticket(ticket: TicketIn, background_tasks: BackgroundTasks):
    with closing(get_connection()) as conn:
        try:
            conn.execute(
                "INSERT INTO tickets (ticket_id, customer_email, subject, message, order_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (ticket.ticket_id, ticket.customer_email, ticket.subject,
                 ticket.message, ticket.order_id),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # ticket_id is the PRIMARY KEY, so a second insert with the same ID fails.
            raise HTTPException(status_code=409, detail=f"Ticket {ticket.ticket_id} already received")

    # Runs after the 202 response has been sent.
    background_tasks.add_task(process_ticket, ticket.ticket_id)
    return TicketAccepted(ticket_id=ticket.ticket_id)
