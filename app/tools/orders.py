"""Tool: fetch an order from the order API over HTTP."""

import httpx

from app.config import APP_BASE_URL


def fetch_order(order_id: str) -> dict | None:
    """Return the order as a dict, or None if the API says it doesn't exist."""
    response = httpx.get(f"{APP_BASE_URL}/orders/{order_id}", timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()  # any other error (500, etc.) raises an exception
    return response.json()
