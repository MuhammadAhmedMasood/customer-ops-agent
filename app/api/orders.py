"""Mock order API: look up a single order by its ID."""

from contextlib import closing

from fastapi import APIRouter, HTTPException

from app.api.models import Order
from app.db.database import get_connection

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: str):
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return dict(row)
