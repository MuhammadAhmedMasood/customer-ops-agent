"""Pydantic models: the shape of data going in and out of the API."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

OrderStatus = Literal["processing", "shipped", "delivered", "delayed", "returned"]
Action = Literal["none", "refund", "reship", "escalate"]


class Order(BaseModel):
    order_id: str
    customer_name: str
    email: str
    item: str
    price_gbp: float
    status: OrderStatus
    order_date: date
    delivery_date: date | None  # None until the order is delivered


# Size limits on what a customer can send. Everything here may end up in an LLM prompt,
# so these cap the input tokens (and cost) per ticket. Roughly 4 characters = 1 token.
MAX_SUBJECT_CHARS = 200
MAX_MESSAGE_CHARS = 4000  # about 1,000 tokens


class TicketIn(BaseModel):
    """The payload the helpdesk sends to our webhook when a ticket arrives."""

    ticket_id: str = Field(min_length=1, max_length=64)
    # A simple "something@something.something" check, not full email validation.
    customer_email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    subject: str = Field(min_length=1, max_length=MAX_SUBJECT_CHARS)
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    order_id: str | None = Field(default=None, max_length=32)


class TicketAccepted(BaseModel):
    ticket_id: str
    status: Literal["accepted"] = "accepted"


class ReplyIn(BaseModel):
    """What the agent sends when it writes back to the helpdesk."""

    reply_text: str = Field(min_length=1)
    action: Action = "none"
    needs_approval: bool = False


class ReplyOut(ReplyIn):
    """A stored reply: everything in ReplyIn, plus fields the database adds."""

    id: int
    ticket_id: str
    # sent: no approval needed. pending_approval -> approved via POST /helpdesk/{id}/approve.
    status: Literal["sent", "pending_approval", "approved"]
    created_at: datetime
