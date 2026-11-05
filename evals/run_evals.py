"""Run every scenario through the real agent (real LLM) and print a results table.

Needs the API running (uvicorn app.main:app) and OPENAI_API_KEY in .env.
Run from the project root:
    python -m evals.run_evals
"""

import json
import sys
from pathlib import Path

import httpx
from langfuse import get_client

from app.agent.graph import graph
from app.config import APP_BASE_URL
from app.tracing import tracing_config

SCENARIOS_PATH = Path(__file__).parent / "scenarios.json"


def run_scenario(scenario: dict, eval_date: str) -> dict:
    """Run one scenario and return {check name: (passed, what we got)}."""
    result = graph.invoke(
        {"ticket_id": scenario["id"], "today": eval_date, **scenario["ticket"]},
        config=tracing_config(scenario["id"], tags=["eval"]),
    )

    category = "flagged" if result["injection_flagged"] else result["category"]
    action = result["proposed_action"]
    needs_approval = result["needs_approval"]
    citations = result["citations"]
    must_cite = scenario["must_cite"]

    return {
        "category": (category == scenario["expected_category"], category),
        "action": (action == scenario["expected_action"], action),
        "approval": (needs_approval == scenario["expected_needs_approval"], str(needs_approval)),
        # must_cite is a list of acceptable sections (citing any one passes).
        # None = no citation required (e.g. escalations), so this check is skipped.
        "citation": (None, "-") if must_cite is None
        else (any(s in citations for s in must_cite), ",".join(citations) or "none"),
    }


def cell(check: tuple) -> str:
    passed, got = check
    mark = "  " if passed is None else ("✓ " if passed else "✗ ")
    return mark + got


def main():
    try:
        httpx.get(f"{APP_BASE_URL}/docs", timeout=5)
    except httpx.ConnectError:
        sys.exit(f"Can't reach {APP_BASE_URL}. Start the API first: uvicorn app.main:app")

    data = json.loads(SCENARIOS_PATH.read_text())
    checks = ["category", "action", "approval", "citation"]
    totals = {name: [0, 0] for name in checks}  # name -> [passed, counted]

    print(f"Eval date: {data['eval_date']}\n")
    print(f"{'ID':<5}{'Description':<50}{'Category':<18}{'Action':<12}{'Approval':<10}{'Citation'}")
    print("-" * 112)

    for scenario in data["scenarios"]:
        try:
            results = run_scenario(scenario, data["eval_date"])
        except Exception as exc:  # one broken scenario shouldn't stop the run
            print(f"{scenario['id']:<5}ERROR: {exc!r}")
            for name in checks:
                totals[name][1] += 1
            continue

        for name in checks:
            passed = results[name][0]
            if passed is not None:
                totals[name][0] += passed  # True counts as 1, False as 0
                totals[name][1] += 1

        print(
            f"{scenario['id']:<5}{scenario['description'][:48]:<50}"
            f"{cell(results['category']):<18}{cell(results['action']):<12}"
            f"{cell(results['approval']):<10}{cell(results['citation'])}"
        )

    print("-" * 112)
    for name in checks:
        passed, counted = totals[name]
        print(f"{name:<10} {passed}/{counted}  ({passed / counted:.0%})")

    # Langfuse sends traces in the background; send any left before the script exits.
    get_client().flush()


if __name__ == "__main__":
    main()
