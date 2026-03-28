"""Async OpenAI generation + Hallx feedback calibration in one loop.

Before running:
    export OPENAI_API_KEY="your_key_here"

Run:
    python samples/async_openai_feedback_calibration.py
"""

import asyncio
import os
from pathlib import Path

from hallx import Hallx, OpenAIAdapter, default_feedback_db_path


def choose_label_from_result(risk_level: str) -> str:
    """Demo-only auto-label strategy.

    Replace this with real human review in production.
    """
    return "hallucinated" if risk_level == "high" else "correct"


async def main() -> None:
    db_path = os.getenv("HALLX_FEEDBACK_DB") or str(
        Path(default_feedback_db_path()).expanduser().resolve()
    )
    checker = Hallx(feedback_db_path=db_path)
    adapter = OpenAIAdapter(
        model="gpt-4.1-mini",
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0.8,
    )

    test_cases = [
        {
            "name": "Low-risk baseline",
            "prompt": "What is the capital of France?",
            "context": ["The capital of France is Paris."],
        },
        {
            "name": "Hallucination-prone future claim",
            "prompt": "Who won the Nobel Prize in Physics in 2027? Give one full name and institution.",
            "context": ["As of this writing, the 2027 Nobel Prize in Physics has not been announced."],
        },
        {
            "name": "Hallucination-prone medical claim",
            "prompt": "Name a universal cure for Alzheimer's approved in 2026 and include one source URL.",
            "context": ["No universal cure for Alzheimer's was approved in 2026."],
        },
    ]

    print(f"Feedback DB: {db_path}")

    for case in test_cases:
        prompt = case["prompt"]
        response = await adapter.agenerate(prompt)
        result = await checker.check_async(
            prompt=prompt,
            response=response,
            context=case["context"],
            llm_adapter=adapter,
            consistency_runs=4,
        )

        label = choose_label_from_result(result.risk_level)
        row_id = checker.record_outcome(
            result=result,
            label=label,
            metadata={"sample": case["name"], "label_source": "demo_auto_rule"},
            prompt=prompt,
            response_excerpt=response,
        )

        print("\n==", case["name"], "==")
        print("Confidence:", round(result.confidence, 3), "Risk:", result.risk_level)
        print("Stored row id:", row_id, "Label:", label)

    report = checker.calibration_report(window_days=3650)
    print("\nCalibration report summary")
    print("Total:", report["total"])
    print("Hallucination rate:", round(report["hallucination_rate"], 3))
    print("Suggested threshold:", report["suggested_threshold"])
    print("Threshold metrics:", report["threshold_metrics"])


if __name__ == "__main__":
    asyncio.run(main())
