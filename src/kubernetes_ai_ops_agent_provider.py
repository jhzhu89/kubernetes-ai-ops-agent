from contextlib import AsyncExitStack
import os
from typing import Any, Dict, List, Optional

from agents import Agent
from agents.model_settings import ModelSettings

from mcp_server_provider_impl import MCPServerProviderImpl

DEFAULT_MODEL_SETTINGS = ModelSettings(temperature=1.0)

__all__ = ["KubernetesAIOpsAgentProvider"]


class KubernetesAIOpsAgentProvider:
    """Async CM that yields a ready‑to‑use :class:`Agent`."""

    def __init__(self) -> None:
        self._stack: AsyncExitStack | None = None
        self._agent: Agent | None = None

    # ------------------------------------------------------------------
    # Async CM
    # ------------------------------------------------------------------
    async def __aenter__(self) -> Agent:  # noqa: D401 – public API
        self._stack = AsyncExitStack()

        provider = await self._stack.enter_async_context(
            MCPServerProviderImpl(
                {
                    "mcpServers": {
                        "kubernetes": {
                            "command": "npx",
                            "args": ["mcp-server-kubernetes"],
                        },
                        "prometheus": {
                            "command": "prometheus-mcp-server",
                            "env": self._get_prometheus_env()
                        },
                        "time": {
                            "command": "python",
                            "args": ["-m", "mcp_server_time"]
                        }
                    }
                }
            )
        )

        self._agent = await self._create_agent(provider.get_servers())
        return self._agent

    async def __aexit__(self, et, ev, tb):
        if self._stack is not None:
            return await self._stack.__aexit__(et, ev, tb)
        return False

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def get_agent(self) -> Agent:
        assert self._agent is not None, "agent not initialized – use 'async with' first"
        return self._agent

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _create_agent(
        self,
        mcp_servers: List[Any],
        model_settings: Optional[ModelSettings] = None,
    ) -> Agent:
        settings = model_settings or DEFAULT_MODEL_SETTINGS
        return Agent(
            name="KubernetesAIOpsAgent",
            instructions=(
                "You have access to multiple tool functions for querying different aspects of the Kubernetes cluster, "
                "Prometheus monitoring system, and time-related operations. "
                "Before providing a final answer, please use as many appropriate tools as possible to gather all relevant information. "
                "Do not stop after a single call – chain multiple tool actions if needed to ensure a thorough response. "
                "When using tools that require time parameters, always use the time server to get the precise current time."
            ),
            mcp_servers=mcp_servers,
            model_settings=settings,
        )

    def _get_prometheus_env(self) -> Dict[str, str]:
        prom_env = {
            "PROMETHEUS_URL": os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
        }
        
        if os.getenv("PROMETHEUS_USERNAME"):
            prom_env["PROMETHEUS_USERNAME"] = os.getenv("PROMETHEUS_USERNAME")
        if os.getenv("PROMETHEUS_PASSWORD"):
            prom_env["PROMETHEUS_PASSWORD"] = os.getenv("PROMETHEUS_PASSWORD")
        if os.getenv("PROMETHEUS_TOKEN"):
            prom_env["PROMETHEUS_TOKEN"] = os.getenv("PROMETHEUS_TOKEN")
            
        return prom_env

