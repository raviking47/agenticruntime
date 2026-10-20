"""Small YAML-backed catalog for registered tools and agents."""

from pathlib import Path
from typing import Any

import yaml


class YamlRegistry:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(__file__).with_name("registry.yaml")

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        if not self.path.exists():
            return {"tools": [], "agents": []}

        data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return {
            "tools": [
                {
                    "name": item.get("name"),
                    "capabilities": list(item.get("capabilities", [])),
                }
                for item in data.get("tools", [])
            ],
            "agents": [
                {
                    "name": item.get("name"),
                    "capabilities": list(item.get("capabilities", [])),
                }
                for item in data.get("agents", [])
            ],
        }

    def _write(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.path.write_text(
            yaml.safe_dump(data, sort_keys=False),
            encoding="utf-8",
        )

    def register_tool(self, name: str, capabilities: list[str]) -> None:
        data = self._read()
        entry = {"name": name, "capabilities": capabilities}
        data["tools"] = [item for item in data["tools"] if item.get("name") != name]
        data["tools"].append(entry)
        self._write(data)

    def register_agent(self, definition: Any) -> None:
        data = self._read()
        entry = {
            "name": definition.name,
            "capabilities": definition.capabilities,
        }
        data["agents"] = [item for item in data["agents"] if item.get("name") != definition.name]
        data["agents"].append(entry)
        self._write(data)

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        return self._read()
