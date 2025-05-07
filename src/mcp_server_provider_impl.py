from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List
from contextlib import AsyncExitStack

from interfaces import MCPServerProvider
from agents.mcp import MCPServerStdio

__all__ = ["MCPServerProviderImpl"]


class MCPServerProviderImpl(MCPServerProvider):
    """Manage *multiple* :class:`MCPServerStdio` instances as **one** async CM.

    Usage::

        async with MCPServerProviderImpl.from_file("config.json") as provider:
            k8s_server = provider.get_server("kubernetes")
    """

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def __init__(self, config: Dict[str, Any], *, include_system_env: bool = True) -> None:
        self._cfg = config
        self._include_system_env = include_system_env
        self._servers: dict[str, Any] = {}
        self._stack: AsyncExitStack | None = None
        self._validate()

    @classmethod
    def from_file(cls, path: str | os.PathLike[str], **kw: Any) -> "MCPServerProviderImpl":
        with Path(path).expanduser().open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        return cls(data, **kw)

    # ------------------------------------------------------------------
    # Async context‑manager protocol
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "MCPServerProviderImpl":
        self._stack = AsyncExitStack()
        await self._enter_servers()
        return self

    async def __aexit__(self, et, ev, tb):
        if self._stack is None:
            return False

        try:
            return await self._stack.__aexit__(et, ev, tb)
        except Exception as eg:
            import logging, traceback

            logging.error("Error while cleaning MCP servers – suppressed: %s", " ".join(traceback.format_exception(eg)))
            return True

    # ------------------------------------------------------------------
    # Public API required by MCPServerProvider interface
    # ------------------------------------------------------------------
    def get_servers(self) -> List[Any]:
        """Return *all* active MCP server instances."""
        return list(self._servers.values())

    def get_server(self, name: str) -> Any:
        """Return a single MCP server by **logical name**."""
        try:
            return self._servers[name]
        except KeyError as exc:  # re‑raise with clearer context
            raise KeyError(f"server '{name}' not found; available: {list(self._servers)}") from exc

    # Alias for convenience – allows ``provider["kubernetes"]``
    __getitem__ = get_server

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _validate(self) -> None:
        if not isinstance(self._cfg, dict) or "mcpServers" not in self._cfg:
            raise ValueError("config must be a mapping with key 'mcpServers'")
        if not isinstance(self._cfg["mcpServers"], dict):
            raise ValueError("'mcpServers' must map names to server specs")

    async def _enter_servers(self) -> None:
        assert self._stack is not None  # for type checkers
        for name, spec in self._cfg["mcpServers"].items():
            cmd = spec["command"]
            if shutil.which(cmd) is None:
                raise RuntimeError(f"Executable '{cmd}' for '{name}' not found on PATH")

            params: dict[str, Any] = {"command": cmd, "args": spec.get("args", [])}
            
            final_env: dict[str, str] = {}
            if self._include_system_env:
                final_env.update(os.environ)
            
            if spec_env := spec.get("env"):
                final_env.update(spec_env)
            
            if final_env:
                params["env"] = final_env

            server_cm = MCPServerStdio(name=f"{name} server", params=params)
            server = await self._stack.enter_async_context(server_cm)
            self._servers[name] = server