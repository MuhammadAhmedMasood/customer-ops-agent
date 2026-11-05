"""The FastAPI app. Run with: uvicorn app.main:app --reload"""

from fastapi import FastAPI

import app.config  # noqa: F401  (loads .env before anything reads env vars)
from app.api import helpdesk, orders, webhook

app = FastAPI(title="ShopCo Customer Ops Agent")
app.include_router(orders.router)
app.include_router(helpdesk.router)
app.include_router(webhook.router)
