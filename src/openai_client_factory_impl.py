import os
import dotenv
from openai import AsyncAzureOpenAI, AsyncOpenAI
from agents import set_default_openai_client
from agents import set_default_openai_api
from agents import set_tracing_disabled
from agents import enable_verbose_stdout_logging
from interfaces import OpenAIClientFactory


class OpenAIClientFactoryImpl(OpenAIClientFactory):
    """
    Factory class for creating and configuring OpenAI clients.
    Supports both Azure OpenAI and standard OpenAI.
    """
    
    def __init__(self, env_file_path: str = ".env", override_env: bool = False):
        """
        Initialize the OpenAI client factory.
        
        Args:
            env_file_path: Path to the .env file for environment variables
            override_env: Whether to override existing environment variables
        """
        self.env_file_path = env_file_path
        self.override_env = override_env
        
    def _load_environment(self) -> None:
        """Load environment variables from .env file if it exists."""
        dotenv.load_dotenv(dotenv_path=self.env_file_path, override=self.override_env)
    
    def create_client(self) -> AsyncAzureOpenAI | AsyncOpenAI:
        """
        Create an OpenAI client based on the environment configuration.
        
        Returns:
            AsyncAzureOpenAI or AsyncOpenAI client instance
        """
        self._load_environment()
        
        # Determine which OpenAI provider to use (azure or openai)
        openai_provider = os.getenv("OPENAI_PROVIDER", "azure").lower()
        
        if openai_provider == "azure":
            # Create AzureOpenAI client using environment variables
            return AsyncAzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_deployment=os.getenv("AZURE_OPENAI_MODEL")
            )
        else:  # openai
            # Create standard OpenAI client
            return AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                organization=os.getenv("OPENAI_ORGANIZATION", None),
                base_url=os.getenv("OPENAI_BASE_URL", None)
            )
    
    def configure_defaults(self) -> None:
        """Configure default settings for the OpenAI client globally."""
        client = self.create_client()
        set_default_openai_client(client)
        set_default_openai_api("chat_completions")
        set_tracing_disabled(True)
        enable_verbose_stdout_logging()


# Create a default instance for backwards compatibility
default_client_factory = OpenAIClientFactoryImpl()

# For backwards compatibility with existing code
def initialize_global_agent_settings():
    """
    Sets up the global agent settings for the OpenAI agents SDK.
    This function is kept for backwards compatibility.
    """
    default_client_factory.configure_defaults()

# Initialize global agent settings when the module is imported, for backwards compatibility
initialize_global_agent_settings()