"""The FastAPI app. Run with: uvicorn app.main:app --reload"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

import app.config  # noqa: F401  (loads .env before anything reads env vars)
from app.api import helpdesk, orders, tickets, webhook

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="ShopCo Customer Ops Agent")
app.include_router(orders.router)
app.include_router(helpdesk.router)
app.include_router(webhook.router)
app.include_router(tickets.router)


@app.get("/", include_in_schema=False)
def demo_page():
    return FileResponse(STATIC_DIR / "index.html")
