"""Async Hallx checks using OpenAI adapter without grounding context."""

import asyncio
import os

from hallx import Hallx, OpenAIAdapter


async def main() -> None:
    adapter = OpenAIAdapter(
        model="gpt-4.1-mini",
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=1.2,
    )
    checker = Hallx(weights={"schema": 0.5, "consistency": 0.5, "grounding": 0.0})

    test_cases = [
        {
            "name": "Ambiguous history",
            "prompt": "Who was the greatest king in world history? Give one final answer with reason.",
        },
        {
            "name": "Hallucination-prone (future award)",
            "prompt": "Who won the Nobel Prize in Physics in 2027? Give one exact winner and institution.",
        },
        {
            "name": "Hallucination-prone (invented citation)",
            "prompt": "Provide a new 2026 Alzheimer's cure and include an exact source URL.",
        },
    ]

    for case in test_cases:
        prompt = case["prompt"]
        response = await adapter.agenerate(prompt)
        result = await checker.check_async(
            prompt=prompt,
            response=response,
            llm_adapter=adapter,
            consistency_runs=6,
        )

        print("\n==", case["name"], "==")
        print("Prompt:", prompt)
        print("LLM Response:", response)
        print("Confidence:", round(result.confidence, 3), "Risk Level:", result.risk_level)
        print("Scores:", result.scores)
        print("Issues:", result.issues)


if __name__ == "__main__":
    asyncio.run(main())
