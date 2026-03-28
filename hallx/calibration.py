"""Feedback storage and calibration metrics."""

from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from hallx.types import HallxResult

try:
    import sqlite3  # type: ignore
except ImportError as exc:  # pragma: no cover
    sqlite3 = None  # type: ignore[assignment]
    _SQLITE_IMPORT_ERROR = exc
else:
    _SQLITE_IMPORT_ERROR = None


_ALLOWED_LABELS = {"correct", "hallucinated"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_label(label: str) -> str:
    value = label.strip().lower()
    aliases = {
        "safe": "correct",
        "ok": "correct",
        "valid": "correct",
        "unsafe": "hallucinated",
        "wrong": "hallucinated",
    }
    value = aliases.get(value, value)
    if value not in _ALLOWED_LABELS:
        raise ValueError("label must be one of: correct, hallucinated")
    return value


def default_feedback_db_path() -> str:
    """Return default feedback DB path, overridable via env.

    Resolution order:
    1) HALLX_FEEDBACK_DB
    2) OS-appropriate user data directory
    """
    configured = os.getenv("HALLX_FEEDBACK_DB", "").strip()
    if configured:
        return configured
    return str(_default_feedback_dir() / "feedback.sqlite3")


def _default_feedback_dir() -> Path:
    home = Path.home()
    system = platform.system().lower()

    if system == "windows":
        root = (
            os.getenv("LOCALAPPDATA", "").strip()
            or os.getenv("APPDATA", "").strip()
            or str(home / "AppData" / "Local")
        )
        return Path(root) / "hallx"

    if system == "darwin":
        return home / "Library" / "Application Support" / "hallx"

    # Linux/Unix/server default with XDG support.
    xdg_data_home = os.getenv("XDG_DATA_HOME", "").strip()
    if xdg_data_home:
        return Path(xdg_data_home) / "hallx"
    return home / ".local" / "share" / "hallx"


class FeedbackStore:
    """SQLite-backed storage for Hallx post-review outcomes."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if sqlite3 is None:
            raise RuntimeError(
                "sqlite3 is not available in this Python runtime; install Python with sqlite support"
            ) from _SQLITE_IMPORT_ERROR
        self.db_path = db_path or default_feedback_db_path()
        self._ensure_parent_dir()
        self._init_schema()

    def record_outcome(
        self,
        result: HallxResult,
        label: str,
        metadata: Optional[Mapping[str, Any]] = None,
        prompt: Optional[str] = None,
        response_excerpt: Optional[str] = None,
    ) -> int:
        """Persist reviewed outcome and return inserted row id."""
        normalized_label = _normalize_label(label)
        payload = {
            "created_at": _utc_now_iso(),
            "label": normalized_label,
            "confidence": float(result.confidence),
            "risk_level": str(result.risk_level),
            "schema_score": float(result.scores.get("schema", 1.0)),
            "consistency_score": float(result.scores.get("consistency", 1.0)),
            "grounding_score": float(result.scores.get("grounding", 1.0)),
            "issues_json": json.dumps(list(result.issues), ensure_ascii=True),
            "recommendation_json": json.dumps(dict(result.recommendation), ensure_ascii=True),
            "metadata_json": json.dumps(dict(metadata or {}), ensure_ascii=True),
            "prompt": (prompt or "")[:2000],
            "response_excerpt": (response_excerpt or "")[:2000],
        }

        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO feedback_outcomes (
                    created_at, label, confidence, risk_level,
                    schema_score, consistency_score, grounding_score,
                    issues_json, recommendation_json, metadata_json,
                    prompt, response_excerpt
                )
                VALUES (
                    :created_at, :label, :confidence, :risk_level,
                    :schema_score, :consistency_score, :grounding_score,
                    :issues_json, :recommendation_json, :metadata_json,
                    :prompt, :response_excerpt
                )
                """,
                payload,
            )
            return int(cur.lastrowid)

    def calibration_report(self, window_days: Optional[int] = None) -> Dict[str, Any]:
        """Return summary metrics and threshold suggestion."""
        rows = self._fetch_rows(window_days=window_days)
        total = len(rows)
        if total == 0:
            return {
                "total": 0,
                "correct": 0,
                "hallucinated": 0,
                "hallucination_rate": 0.0,
                "by_risk_level": {"high": {}, "medium": {}, "low": {}},
                "suggested_threshold": None,
            }

        correct = sum(1 for row in rows if row[0] == "correct")
        hallucinated = total - correct
        by_risk = self._risk_level_metrics(rows)
        threshold, threshold_metrics = self._best_threshold(rows)

        return {
            "total": total,
            "correct": correct,
            "hallucinated": hallucinated,
            "hallucination_rate": hallucinated / float(total),
            "by_risk_level": by_risk,
            "suggested_threshold": threshold,
            "threshold_metrics": threshold_metrics,
        }

    def _risk_level_metrics(self, rows: Iterable[Tuple[str, float, str]]) -> Dict[str, Dict[str, Any]]:
        metrics: Dict[str, Dict[str, Any]] = {}
        for risk_level in ("high", "medium", "low"):
            selected = [row for row in rows if row[2] == risk_level]
            count = len(selected)
            if count == 0:
                metrics[risk_level] = {"count": 0, "hallucinated": 0, "hallucination_rate": 0.0}
                continue
            hallucinated = sum(1 for row in selected if row[0] == "hallucinated")
            metrics[risk_level] = {
                "count": count,
                "hallucinated": hallucinated,
                "hallucination_rate": hallucinated / float(count),
            }
        return metrics

    def _best_threshold(self, rows: List[Tuple[str, float, str]]) -> Tuple[float, Dict[str, float]]:
        best_threshold = 0.4
        best_f1 = -1.0
        best_metrics = {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        thresholds = [idx / 100.0 for idx in range(10, 91, 5)]
        for threshold in thresholds:
            tp = fp = fn = 0
            for label, confidence, _ in rows:
                predicted_hallucinated = confidence < threshold
                is_hallucinated = label == "hallucinated"
                if predicted_hallucinated and is_hallucinated:
                    tp += 1
                elif predicted_hallucinated and not is_hallucinated:
                    fp += 1
                elif (not predicted_hallucinated) and is_hallucinated:
                    fn += 1

            precision = tp / float(tp + fp) if tp + fp else 0.0
            recall = tp / float(tp + fn) if tp + fn else 0.0
            f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
                best_metrics = {"precision": precision, "recall": recall, "f1": f1}

        return best_threshold, best_metrics

    def _fetch_rows(self, window_days: Optional[int] = None) -> List[Tuple[str, float, str]]:
        query = "SELECT label, confidence, risk_level FROM feedback_outcomes"
        params: List[Any] = []

        if window_days is not None:
            if window_days <= 0:
                raise ValueError("window_days must be > 0")
            since = datetime.now(timezone.utc) - timedelta(days=window_days)
            query += " WHERE created_at >= ?"
            params.append(since.isoformat())

        with self._connect() as conn:
            cur = conn.execute(query, params)
            data = cur.fetchall()
        return [(str(row[0]), float(row[1]), str(row[2])) for row in data]

    def _ensure_parent_dir(self) -> None:
        if self.db_path == ":memory:":
            return
        Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> Any:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    label TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    schema_score REAL NOT NULL,
                    consistency_score REAL NOT NULL,
                    grounding_score REAL NOT NULL,
                    issues_json TEXT NOT NULL,
                    recommendation_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response_excerpt TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feedback_created_at
                ON feedback_outcomes(created_at)
                """
            )
