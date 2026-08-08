"""Faithfulness verification backends (optional extras)."""

from hallx.faithfulness.base import FaithfulnessVerifier
from hallx.faithfulness.nli import LocalNLIChecker

__all__ = [
    "FaithfulnessVerifier",
    "LocalNLIChecker",
]