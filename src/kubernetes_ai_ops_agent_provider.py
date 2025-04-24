import os
from typing import Dict, List, Any, Optional
from agents import Agent
from agents.model_settings import ModelSettings
from mcp_server_provider_impl import MCPServerProviderImpl

# Default model settings with temperature=1.0
DEFAULT_MODEL_SETTINGS = ModelSettings(temperature=1.0)


class KubernetesAIOpsAgentProvider:
    """
    This class encapsulates Kubernetes, Prometheus, and Time MCP servers and returns an OpenAI Agent instance
    that can interact with Kubernetes clusters, Prometheus metrics, and perform time-related operations.

    Usage example:

        # Create an instance of the agent provider
        agent_provider = KubernetesAIOpsAgentProvider()
        # Initialize the provider and get the agent
        agent = await agent_provider.initialize()
        
        # Use the agent for operations
        result = await Runner.run(agent, input="Query your Kubernetes status, related metrics, and current time")
        print(result.final_output)
        
        # When done, clean up resources
        await agent_provider.cleanup()
    """
    def __init__(self):
        """
        Initialize the KubernetesAgentContext with a server provider.
        If no server provider is given, creates a default one.
        """
        # Use the provided server_provider or create a default one
        # Create MCP server configuration
        mcp_config = {
            "mcpServers": {
                "kubernetes": {
                    "command": "npx",
                    "args": ["mcp-server-kubernetes"]
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
        self.server_provider = MCPServerProviderImpl(mcp_config)
        
        # Initialize agent
        self.agent = None
        self.initialized = False
        
    def _get_prometheus_env(self) -> Dict[str, str]:
        """
        Get Prometheus configuration environment variables.
        
        Returns:
            A dictionary of Prometheus environment variables
        """
        prom_env = {
            "PROMETHEUS_URL": os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
        }
        
        # Add optional authentication variables if they exist in environment
        if os.getenv("PROMETHEUS_USERNAME"):
            prom_env["PROMETHEUS_USERNAME"] = os.getenv("PROMETHEUS_USERNAME")
        if os.getenv("PROMETHEUS_PASSWORD"):
            prom_env["PROMETHEUS_PASSWORD"] = os.getenv("PROMETHEUS_PASSWORD")
        if os.getenv("PROMETHEUS_TOKEN"):
            prom_env["PROMETHEUS_TOKEN"] = os.getenv("PROMETHEUS_TOKEN")
            
        return prom_env

    async def initialize(self) -> Agent:
        """
        Initialize the MCP server provider and create an agent instance.
        This method is a wrapper around __aenter__() for clearer semantics.
        
        Returns:
            An OpenAI Agent instance
        """
        if not self.initialized:
            self.agent = await self.__aenter__()
            self.initialized = True
        return self.agent
    
    async def cleanup(self):
        """
        Clean up the MCP server provider and release all resources.
        This method is a wrapper around __aexit__() for clearer semantics.
        """
        if self.initialized:
            await self.__aexit__(None, None, None)
            self.initialized = False
    
    def get_agent(self) -> Agent:
        """
        Get the current agent instance.
        
        Returns:
            The initialized OpenAI Agent instance or None if not initialized
        """
        return self.agent

    async def __aenter__(self):
        """
        Initialize the MCP server provider and create an agent instance.
        
        Returns:
            An OpenAI Agent instance
        """
        # Initialize the MCP server provider
        await self.server_provider.__aenter__()
        
        # Get all initialized MCP servers
        mcp_servers = self.server_provider.get_servers()
        
        # Create and return an OpenAI Agent instance with the provided instructions
        self.agent = await self._create_agent(mcp_servers=mcp_servers)
        return self.agent

    async def _create_agent(
        self,
        mcp_servers: List[Any],
        model_settings: Optional[ModelSettings] = None
    ) -> Agent:
        """
        Create an OpenAI Agent instance with the provided MCP servers and settings.
        
        Args:
            mcp_servers: List of MCP servers to use with the agent
            model_settings: Optional ModelSettings to configure the agent
            
        Returns:
            An OpenAI Agent instance
        """
        # Use the provided model_settings or the default ones
        settings = model_settings or DEFAULT_MODEL_SETTINGS
        
        # Create an OpenAI Agent instance with the provided instructions
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
            model_settings=settings
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up the MCP server provider.
        """
        if self.server_provider:
            await self.server_provider.__aexit__(exc_type, exc_val, exc_tb)
            self.agent = None