"""Small, sandboxed text-file tools for agents."""

import logging
from pathlib import Path

from langchain_core.tools import tool

BASE_DIR = (Path(__file__).resolve().parents[2] / "files").resolve()
logger = logging.getLogger(__name__)


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
    logger.info("Writing file: path=%s content_length=%d", path.relative_to(BASE_DIR), len(content))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Successfully wrote {filename}"


@tool
def read_file(filename: str) -> str:
    """Read a UTF-8 text file beneath the workspace files directory."""
    path = _safe_path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"File does not exist: {filename}")
    content = path.read_text(encoding="utf-8")
    logger.info("Reading file: path=%s content_length=%d", path.relative_to(BASE_DIR), len(content))
    return content




def tool_capabilities() -> list[object]:
    """Return the tool objects that can be registered with an agent."""
    logger.debug("Providing file tools: write_file, read_file")
    return [write_file, read_file]
