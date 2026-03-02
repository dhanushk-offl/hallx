from hallx.grounding import check_grounding


def test_grounding_with_context_scores_high() -> None:
    context = [
        "The Eiffel Tower is located in Paris.",
        "France is in Europe.",
    ]
    response = "The Eiffel Tower is located in Paris. France is in Europe."

    score, issues = check_grounding(response, context)

    assert score > 0.75
    assert issues == []


def test_grounding_without_context_skips() -> None:
    score, issues = check_grounding("text", [])

    assert score == 1.0
    assert any("skipped" in issue for issue in issues)


def test_forbidden_source_detection() -> None:
    score, issues = check_grounding(
        response="According to Wikipedia, result is 42. Source: http://fake.local/ref",
        context_docs=["Result is 42."],
        allow_web=False,
    )

    assert 0.0 <= score <= 1.0
    assert any("unverified" in issue or "fabricated" in issue for issue in issues)
