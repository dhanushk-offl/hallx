"""Optional LLM-as-judge groundedness scoring using any hallx adapter."""

import inspect
import re
from typing import Callable, Optional

from hallx.types import HallxAdapterError, LLMAdapter


_JUDGE_PROMPT_TEMPLATE = (
    "You are a strict factual-support judge. A claim is supported only if the "
    "EVIDENCE explicitly contains it. Reply ONLY with one integer from 0 to 100, "
    "where 100 means the claim is fully supported and 0 means it is not. "
    "Never explain.\n\n"
    "EVIDENCE:\n{evidence}\n\n"
    "CLAIM:\n{hypothesis}\n"
)


class GroundingJudge:
    """LLM-as-judge groundedness scorer reusing any hallx LLM adapter.

    Implements the ``hallx.faithfulness.base.FaithfulnessVerifier`` protocol, so a
    ``GroundingJudge`` instance can be passed directly as ``verifier=`` to
    ``Hallx.check(...)`` (with ``claims=True``) for LLM-judged claim grounding.
    """

    def __init__(
        self,
        llm_callable: Optional[Callable[[str], str]] = None,
        llm_adapter: Optional[LLMAdapter] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        if llm_callable is None and llm_adapter is None:
            raise ValueError("provide either llm_callable or llm_adapter")
        if llm_callable is not None and llm_adapter is not None:
            raise ValueError("provide only one of llm_callable or llm_adapter")
        self._llm_callable = llm_callable
        self._llm_adapter = llm_adapter
        self._system_prompt = system_prompt or (
            "You are a strict factual-support judge. Never hedge."
        )

    def verify(self, premise: str, hypothesis: str) -> float:
        """Synchronously score whether ``hypothesis`` is entailed by ``premise``."""
        prompt = self._prompt(premise, hypothesis)
        if self._llm_callable is not None:
            response = self._llm_callable(prompt)
        elif self._llm_adapter is not None:
            response = self._llm_adapter.generate(prompt, self._system_prompt)
        else:  # pragma: no cover
            raise HallxAdapterError("no judge backend configured")
        return self._parse(response)

    async def averify(self, premise: str, hypothesis: str) -> float:
        """Asynchronously verify the ``hypothesis`` against the ``premise``."""
        prompt = self._prompt(premise, hypothesis)
        if self._llm_callable is not None:
            response = self._llm_callable(prompt)
            if inspect.isawaitable(response):
                response = await response
        elif self._llm_adapter is not None:
            response = await self._llm_adapter.agenerate(prompt, self._system_prompt)
        else:  # pragma: no cover
            raise HallxAdapterError("no judge backend configured")
        return self._parse(response)

    def _prompt(self, premise: str, hypothesis: str) -> str:
        return _JUDGE_PROMPT_TEMPLATE.format(evidence=premise, hypothesis=hypothesis)

    def _parse(self, response: str) -> float:
        if not isinstance(response, str):
            return 0.0
        return _parse_judge_score(response)


def _parse_judge_score(response: str) -> float:
    """Extract a 0-100 integer from a judge response and normalize to [0, 1]."""
    if not response:
        raise ValueError("judge returned an empty response")
    match = re.search(r"\d{1,3}", response)
    if not match:
        raise ValueError("judge response contained no numeric score")
    value = float(match.group(0))
    return max(0.0, min(1.0, value / 100.0))