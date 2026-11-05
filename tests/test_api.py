"""API tests: order lookup, helpdesk replies and approval, webhook."""

from app.api import webhook
from app.api.models import MAX_MESSAGE_CHARS

TICKET = {
    "ticket_id": "T-1",
    "customer_email": "sophia.evans@example.com",
    "subject": "Late",
    "message": "Where is my order?",
    "order_id": "SC-1005",
}


def test_get_order(client):
    response = client.get("/orders/SC-1005")
    assert response.status_code == 200
    assert response.json()["item"] == "Coffee machine"
    assert response.json()["status"] == "delayed"


def test_get_missing_order_is_404(client):
    assert client.get("/orders/SC-9999").status_code == 404


def test_reply_without_approval_is_sent(client):
    response = client.post("/helpdesk/T-1/reply", json={"reply_text": "Hi", "action": "none"})
    assert response.status_code == 201
    assert response.json()["status"] == "sent"

    replies = client.get("/helpdesk/T-1").json()
    assert [r["reply_text"] for r in replies] == ["Hi"]


def test_reply_with_invalid_action_is_422(client):
    response = client.post("/helpdesk/T-1/reply", json={"reply_text": "Hi", "action": "teleport"})
    assert response.status_code == 422


def test_approve_pending_reply(client):
    client.post(
        "/helpdesk/T-1/reply",
        json={"reply_text": "Being reviewed", "action": "refund", "needs_approval": True},
    )
    assert client.get("/helpdesk/T-1").json()[0]["status"] == "pending_approval"

    response = client.post("/helpdesk/T-1/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    # Nothing left to approve.
    assert client.post("/helpdesk/T-1/approve").status_code == 404


def test_approve_with_nothing_pending_is_404(client):
    client.post("/helpdesk/T-1/reply", json={"reply_text": "Hi", "action": "none"})
    assert client.post("/helpdesk/T-1/approve").status_code == 404


def test_webhook_accepts_and_schedules_processing(client, monkeypatch):
    # Replace the real agent with a fake that just records the call.
    processed = []
    monkeypatch.setattr(webhook, "process_ticket", processed.append)

    response = client.post("/webhook/ticket", json=TICKET)
    assert response.status_code == 202
    assert response.json() == {"ticket_id": "T-1", "status": "accepted"}
    assert processed == ["T-1"]


def test_webhook_rejects_duplicate_and_bad_payload(client, monkeypatch):
    monkeypatch.setattr(webhook, "process_ticket", lambda ticket_id: None)

    client.post("/webhook/ticket", json=TICKET)
    assert client.post("/webhook/ticket", json=TICKET).status_code == 409

    bad = {**TICKET, "ticket_id": "T-2", "customer_email": "not-an-email"}
    assert client.post("/webhook/ticket", json=bad).status_code == 422


def test_webhook_rejects_oversized_message_before_any_processing(client, monkeypatch):
    processed = []
    monkeypatch.setattr(webhook, "process_ticket", processed.append)

    at_limit = {**TICKET, "message": "x" * MAX_MESSAGE_CHARS}
    assert client.post("/webhook/ticket", json=at_limit).status_code == 202

    too_long = {**TICKET, "ticket_id": "T-2", "message": "x" * (MAX_MESSAGE_CHARS + 1)}
    response = client.post("/webhook/ticket", json=too_long)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_long"
    assert processed == ["T-1"]  # the oversized ticket never reached the agent


def test_webhook_rate_limit_per_ip(client, monkeypatch):
    monkeypatch.setattr(webhook, "process_ticket", lambda ticket_id: None)

    def send(ticket_id: str, ip: str):
        return client.post(
            "/webhook/ticket",
            json={**TICKET, "ticket_id": ticket_id},
            headers={"X-Forwarded-For": ip},
        )

    for i in range(10):
        assert send(f"T-{i}", "1.1.1.1").status_code == 202

    blocked = send("T-10", "1.1.1.1")
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "60"

    # A different IP has its own limit.
    assert send("T-11", "2.2.2.2").status_code == 202
