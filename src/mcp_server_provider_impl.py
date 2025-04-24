import os
import json
import shutil
from typing import Dict, List, Any
from interfaces import MCPServerProvider


class MCPServerProviderImpl(MCPServerProvider):
    """
    A class for managing multiple MCP servers based on a configuration file.
    This class can create and manage MCPServerStdio instances from a JSON configuration.
    
    The configuration should follow this format:
    {
        "mcpServers": {
            "server_name1": {
                "command": "command_to_run",
                "args": ["arg1", "arg2"],
                "env": {
                    "ENV_VAR1": "value1",
                    "ENV_VAR2": "value2"
                }
            },
            "server_name2": {
                "command": "command_to_run2",
                "args": ["arg1", "arg2"]
            }
        }
    }
    
    Usage example:
    
        config = {
            "mcpServers": {
                "kubernetes": {
                    "command": "npx",
                    "args": ["mcp-server-kubernetes"]
                },
                "prometheus": {
                    "command": "prometheus-mcp-server",
                    "env": {
                        "PROMETHEUS_URL": "http://localhost:9090"
                    }
                }
            }
        }
        
        async with MCPServerManager(config) as manager:
            # Get initialized MCP servers
            mcp_servers = manager.get_servers()
            # Use the servers...
    """
    
    def __init__(self, config: Dict[str, Any], include_system_env: bool = True):
        """
        Initialize the MCP Server Manager with the given configuration.
        
        Args:
            config: A dictionary containing MCP server configurations
            include_system_env: Whether to include system environment variables
                               in the environment for each server
        """
        self.config = config
        self.server_objects = {}
        self.servers = {}
        self.include_system_env = include_system_env
        self.validate_config()
        
    def validate_config(self) -> None:
        """
        Validate the configuration structure.
        
        Raises:
            ValueError: If the configuration is invalid
        """
        if not isinstance(self.config, dict):
            raise ValueError("Configuration must be a dictionary")
            
        if "mcpServers" not in self.config:
            raise ValueError("Configuration must contain 'mcpServers' key")
            
        if not isinstance(self.config["mcpServers"], dict):
            raise ValueError("'mcpServers' must be a dictionary")
            
        for server_name, server_config in self.config["mcpServers"].items():
            if not isinstance(server_config, dict):
                raise ValueError(f"Server configuration for '{server_name}' must be a dictionary")
                
            if "command" not in server_config:
                raise ValueError(f"Server configuration for '{server_name}' must contain 'command' key")
    
    @staticmethod
    def load_config_from_file(path: str, include_system_env: bool = True) -> 'MCPServerProviderImpl':
        """
        Load configuration from a JSON file and create an MCPServerManager instance.
        
        Args:
            path: Path to the configuration file
            include_system_env: Whether to include system environment variables
                               in the environment for each server
            
        Returns:
            An instance of MCPServerManager
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        with open(path, 'r') as f:
            config = json.load(f)
        
        return MCPServerProviderImpl(config, include_system_env)
        
    async def __aenter__(self) -> MCPServerProvider:
        """
        Create and initialize all MCP servers from the configuration.
        
        Returns:
            self: The manager instance
            
        Raises:
            RuntimeError: If a command is not available
        """
        from agents.mcp import MCPServerStdio
        
        for server_name, server_config in self.config["mcpServers"].items():
            command = server_config["command"]
            
            # Check if the command is available
            if not shutil.which(command):
                raise RuntimeError(f"Command '{command}' for '{server_name}' is not installed.")
            
            # Prepare parameters for the MCPServerStdio
            params = {"command": command}
            
            if "args" in server_config:
                params["args"] = server_config["args"]
                
            # Handle environment variables
            server_env = {}
            
            # Include system environment if requested
            if self.include_system_env:
                server_env.update(os.environ)
                
            # Add server-specific environment variables from config
            if "env" in server_config:
                server_env.update(server_config["env"])
                
            # Only add env to params if it's not empty
            if server_env:
                params["env"] = server_env
            
            # Initialize the MCP server
            server_obj = MCPServerStdio(
                name=f"{server_name.capitalize()} Server",
                params=params,
            )
            
            server = await server_obj.__aenter__()
            
            # Store server object and server reference
            self.server_objects[server_name] = server_obj
            self.servers[server_name] = server
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Clean up all MCP servers.
        """
        for server_name, server_obj in self.server_objects.items():
            await server_obj.__aexit__(exc_type, exc_val, exc_tb)
    
    def get_servers(self) -> List[Any]:
        """
        Get a list of all initialized MCP servers.
        
        Returns:
            A list of MCP server instances
        """
        return list(self.servers.values())
    
    def get_server(self, name: str) -> Any:
        """
        Get a specific MCP server by name.
        
        Args:
            name: Name of the server to retrieve
            
        Returns:
            The requested MCP server instance
            
        Raises:
            KeyError: If the server with the given name doesn't exist
        """
        if name not in self.servers:
            raise KeyError(f"Server '{name}' not found")
            
        return self.servers[name]