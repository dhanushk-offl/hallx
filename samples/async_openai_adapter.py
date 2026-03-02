"""Async check using OpenAI adapter."""

import asyncio
import os

from hallx import Hallx, OpenAIAdapter


async def main() -> None:
    adapter = OpenAIAdapter(
        model="gpt-4.1-mini",
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0.0,
    )
    checker = Hallx()

    response = await adapter.agenerate("What is the capital of France?")
    result = await checker.check_async(
        prompt="What is the capital of France?",
        response=response,
        context=["The capital of France is Paris."],
        llm_adapter=adapter,
        consistency_runs=3,
    )
    print(result.confidence, result.risk_level)


if __name__ == "__main__":
    asyncio.run(main())
