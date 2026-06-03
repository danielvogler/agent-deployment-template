"""Unit tests for agent tools — no network, no GCP credentials required."""
from agent.tools.example_tools import get_current_datetime, web_search
from agent.tools.response_models import SearchResult


def test_get_current_datetime_returns_iso_string():
    result = get_current_datetime()
    assert isinstance(result, str)
    assert "T" in result
    assert "Z" in result or "+" in result  # timezone present


def test_get_current_datetime_is_utc():
    result = get_current_datetime()
    # ISO format with UTC offset ends in +00:00 or Z
    assert result.endswith("+00:00") or result.endswith("Z")


def test_web_search_stub_returns_results(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    results = web_search("test query")
    assert len(results) >= 1
    assert isinstance(results[0], SearchResult)


def test_web_search_stub_contains_query_in_snippet(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    results = web_search("hello world")
    assert "hello world" in results[0].snippet


def test_web_search_result_has_required_fields(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    results = web_search("anything")
    r = results[0]
    assert r.title
    assert r.url
    assert r.snippet
