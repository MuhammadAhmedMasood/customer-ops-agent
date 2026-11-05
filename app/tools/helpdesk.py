"""Tool: write a reply back to the helpdesk API over HTTP."""

import httpx

from app.config import APP_BASE_URL


def post_reply(ticket_id: str, reply_text: str, action: str, needs_approval: bool) -> dict:
    response = httpx.post(
        f"{APP_BASE_URL}/helpdesk/{ticket_id}/reply",
        json={"reply_text": reply_text, "action": action, "needs_approval": needs_approval},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
