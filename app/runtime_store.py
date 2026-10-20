"""SQLite persistence for template-backed runtime tools and agents."""

import json
import sqlite3
from pathlib import Path
from typing import Any


class RuntimeStore:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(__file__).with_name("runtime.db")
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runtime_tools (
                    name TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    capabilities TEXT NOT NULL,
                    template TEXT NOT NULL,
                    function_key TEXT NOT NULL,
                    arguments TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runtime_agents (
                    name TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    description TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    capabilities TEXT NOT NULL,
                    template TEXT NOT NULL,
                    work_key TEXT NOT NULL DEFAULT 'general'
                );
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(runtime_agents)")}
            if "work_key" not in columns:
                connection.execute(
                    "ALTER TABLE runtime_agents ADD COLUMN work_key TEXT NOT NULL DEFAULT 'general'"
                )

    def save_tool(self, *, name: str, description: str, capabilities: list[str],
                  template: str, function_key: str,
                  arguments: dict[str, Any] | None = None) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runtime_tools
                    (name, description, capabilities, template, function_key, arguments)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description=excluded.description,
                    capabilities=excluded.capabilities,
                    template=excluded.template,
                    function_key=excluded.function_key,
                    arguments=excluded.arguments
                """,
                (name, description, json.dumps(capabilities), template,
                 function_key, json.dumps(arguments or {})),
            )

    def save_agent(self, *, name: str, version: str, description: str,
                   instructions: str, capabilities: list[str],
                   template: str = "default_agent", work_key: str = "general") -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runtime_agents
                    (name, version, description, instructions, capabilities, template, work_key)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    version=excluded.version,
                    description=excluded.description,
                    instructions=excluded.instructions,
                    capabilities=excluded.capabilities,
                    template=excluded.template,
                    work_key=excluded.work_key
                """,
                (name, version, description, instructions, json.dumps(capabilities), template, work_key),
            )

    def tools(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM runtime_tools ORDER BY name").fetchall()
        return [
            {**dict(row), "capabilities": json.loads(row["capabilities"]),
             "arguments": json.loads(row["arguments"])}
            for row in rows
        ]

    def agents(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM runtime_agents ORDER BY name").fetchall()
        return [
            {**dict(row), "capabilities": json.loads(row["capabilities"])}
            for row in rows
        ]

    def execution_manifest(self) -> dict[str, list[dict[str, Any]]]:
        """Return the persisted callable references used for reconstruction."""
        return {"tools": self.tools(), "agents": self.agents()}
