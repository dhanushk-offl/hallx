"""Feedback storage + calibration walkthrough.

Run:
    python samples/feedback_calibration.py
"""

from pathlib import Path

from hallx import Hallx


def main() -> None:
    db_path = Path(__file__).resolve().parent / "data" / "hallx-feedback.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    checker = Hallx(feedback_db_path=str(db_path))

    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
        "additionalProperties": False,
    }

    cases = [
        {
            "name": "Grounded answer",
            "prompt": "What is the capital of France?",
            "response": {"answer": "Paris"},
            "context": ["The capital of France is Paris."],
            "label": "correct",
        },
        {
            "name": "Ungrounded + fake citation",
            "prompt": "Who won Nobel Physics 2027?",
            "response": "According to Wikipedia, Dr. Jane Unknown won in 2027. Source: http://fake.local/ref",
            "context": ["As of this writing, the 2027 Nobel Prize in Physics has not been announced."],
            "label": "hallucinated",
        },
        {
            "name": "Schema mismatch",
            "prompt": "Return JSON answer",
            "response": {"unexpected": None},
            "context": ["Expected field is answer."],
            "label": "hallucinated",
        },
    ]

    print(f"Feedback DB: {db_path}")
    print("Recording reviewed outcomes...\n")

    for idx, case in enumerate(cases, start=1):
        result = checker.check(
            prompt=case["prompt"],
            response=case["response"],
            context=case["context"],
            schema=schema,
            allow_web_sources=False,
        )
        row_id = checker.record_outcome(
            result=result,
            label=case["label"],
            metadata={"sample_case": case["name"], "reviewer": "demo"},
            prompt=case["prompt"],
            response_excerpt=str(case["response"]),
        )
        print(f"[{idx}] {case['name']}")
        print(f"  confidence={result.confidence:.3f} risk={result.risk_level}")
        print(f"  issues={result.issues}")
        print(f"  stored_row_id={row_id}\n")

    report = checker.calibration_report(window_days=3650)
    print("Calibration report")
    print(f"  total={report['total']}")
    print(f"  correct={report['correct']}")
    print(f"  hallucinated={report['hallucinated']}")
    print(f"  hallucination_rate={report['hallucination_rate']:.3f}")
    print(f"  suggested_threshold={report['suggested_threshold']}")
    print(f"  threshold_metrics={report['threshold_metrics']}")
    print(f"  by_risk_level={report['by_risk_level']}")


if __name__ == "__main__":
    main()
