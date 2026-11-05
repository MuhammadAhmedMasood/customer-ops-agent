"""Langfuse tracing for graph runs. Off unless the Langfuse keys are set."""

import os

from langfuse.langchain import CallbackHandler


def tracing_config(ticket_id: str, tags: list[str]) -> dict:
    """LangChain/LangGraph run config that sends a trace of the run to Langfuse."""
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        return {}
    return {
        # The handler records every node, LLM call, prompt, output, token count and timing.
        "callbacks": [CallbackHandler()],
        "metadata": {
            "langfuse_trace_name": "process_ticket",
            "langfuse_session_id": ticket_id,  # group all runs for one ticket
            "langfuse_tags": tags,
        },
    }
