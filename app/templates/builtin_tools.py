"""Approved implementation functions used by tool templates."""

import json
import logging
from pathlib import Path

import httpx
from langchain_core.tools import tool

BASE_DIR = (Path(__file__).resolve().parents[2] / "files").resolve()
logger = logging.getLogger(__name__)
_search_cache: dict[str, str] = {}
_search_budget: int | None = None


def set_search_budget(limit: int):
    global _search_budget
    previous = _search_budget
    _search_budget = limit
    return previous


def reset_search_budget(token) -> None:
    global _search_budget
    _search_budget = token


def _safe_path(filename: str) -> Path:
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename must be a non-empty string")
    path = (BASE_DIR / filename).resolve()
    try:
        path.relative_to(BASE_DIR)
    except ValueError as exc:
        raise ValueError("Invalid file path") from exc
    return path


@tool
def write_file(filename: str, content: str) -> str:
    """Write text content to a file beneath the workspace files directory."""
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    path = _safe_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Successfully wrote {filename}"


@tool
def read_file(filename: str) -> str:
    """Read a UTF-8 text file beneath the workspace files directory."""
    path = _safe_path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"File does not exist: {filename}")
    return path.read_text(encoding="utf-8")


def _topics(items: list[dict]) -> list[dict[str, str]]:
    results = []
    for item in items:
        if item.get("Text") and item.get("FirstURL"):
            results.append({"text": item["Text"], "url": item["FirstURL"]})
        results.extend(_topics(item.get("Topics", [])))
    return results


@tool
async def web_search(query: str) -> str:
    """Search the public web and return a short list of relevant results."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")

    normalized_query = " ".join(query.lower().split())
    if normalized_query in _search_cache:
        return _search_cache[normalized_query]

    global _search_budget
    budget = _search_budget
    if budget is not None:
        if budget <= 0:
            return json.dumps({
                "query": query,
                "results": [],
                "message": "Search limit reached. Use the results already returned.",
            })
        _search_budget = budget - 1

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
        )
        response.raise_for_status()
    payload = response.json()
    results = []
    if payload.get("AbstractText"):
        results.append({"text": payload["AbstractText"], "url": payload.get("AbstractURL", "")})
    results.extend(_topics(payload.get("RelatedTopics", [])))
    result = json.dumps({
        "query": query,
        "results": results[:5],
        "message": (
            "Use these results to complete the task. Do not retry the search."
            if results else
            "No structured results were returned. Do not retry the search; continue with the task."
        ),
    })
    _search_cache[normalized_query] = result
    return result
