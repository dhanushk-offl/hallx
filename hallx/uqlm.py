"""Compatibility exports for UQLM-style naming."""

from hallx.core import Hallx as UQLM
from hallx.types import HallxHighRiskError as UQLMHighRiskError

__all__ = ["UQLM", "UQLMHighRiskError"]
