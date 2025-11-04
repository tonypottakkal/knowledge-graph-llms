"""
LLM Configuration Manager

This module provides centralized configuration management for multiple LLM providers,
handling environment variable loading, validation, and provider-specific settings.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse


@dataclass
class ProviderConfig:
    """Configuration schema for LLM providers."""
    name: str
    display_name: str
    requires_api_key: bool
    env_key_name: Optional[str]
    supports_model_selection: bool
    default_model: Optional[str]
    connection_test_required: bool
    additional_env_vars: Optional[Dict[str, str]] = None


class LLMConfigManager:
    """
    Centralized configuration manager for LLM providers.
    
    Handles environment variable loading, provider validation,
    and configuration management for multiple LLM services.
    """
    
    def __init__(self):
        """Initialize the configuration manager and load environment variables."""
        load_dotenv()
        self._providers = self._initialize_providers()
    
    def _initialize_providers(self) -> Dict[str, ProviderConfig]:
        """Initialize the supported provider configurations."""
        return {
            "openai": ProviderConfig(
                name="openai",
                display_name="OpenAI",
                requires_api_key=True,
                env_key_name="OPENAI_API_KEY",
                supports_model_selection=True,
                default_model="gpt-4o",
                connection_test_required=True
            ),
            "ollama": ProviderConfig(
                name="ollama",
                display_name="Ollama (Local)",
                requires_api_key=False,
                env_key_name=None,
                supports_model_selection=True,
                default_model="llama2",
                connection_test_required=True,
                additional_env_vars={"OLLAMA_BASE_URL": "http://localhost:11434"}
            ),
            "custom": ProviderConfig(
                name="custom",
                display_name="Custom External Provider",
                requires_api_key=True,
                env_key_name="CUSTOM_LLM_API_KEY",
                supports_model_selection=True,
                default_model="gpt-3.5-turbo",
                connection_test_required=True,
                additional_env_vars={"CUSTOM_LLM_BASE_URL": None}
            )
        }
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of available LLM provider names.
        
        Returns:
            List[str]: List of provider names
        """
        return list(self._providers.keys())
    
    def get_provider_display_names(self) -> Dict[str, str]:
        """
        Get mapping of provider names to display names.
        
        Returns:
            Dict[str, str]: Mapping of provider name to display name
        """
        return {name: config.display_name for name, config in self._providers.items()}
    
    def validate_provider_config(self, provider: str) -> tuple[bool, Optional[str]]:
        """
        Validate configuration for a specific provider.
        
        Args:
            provider (str): Provider name to validate
            
        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if provider not in self._providers:
            return False, f"Unknown provider: {provider}"
        
        config = self._providers[provider]
        
        # Check required API key
        if config.requires_api_key and config.env_key_name:
            api_key = os.getenv(config.env_key_name)
            if not api_key:
                return False, f"Missing required environment variable: {config.env_key_name}"
        
        # Check additional environment variables
        if config.additional_env_vars:
            for env_var, default_value in config.additional_env_vars.items():
                value = os.getenv(env_var, default_value)
                if value is None and provider == "custom" and env_var == "CUSTOM_LLM_BASE_URL":
                    return False, f"Missing required environment variable: {env_var}"
                
                # Validate URL format for base URLs
                if "BASE_URL" in env_var and value:
                    if not self._is_valid_url(value):
                        return False, f"Invalid URL format for {env_var}: {value}"
        
        return True, None
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Get configuration dictionary for a specific provider.
        
        Args:
            provider (str): Provider name
            
        Returns:
            Dict[str, Any]: Provider configuration including environment values
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider not in self._providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        config = self._providers[provider]
        result = {
            "name": config.name,
            "display_name": config.display_name,
            "supports_model_selection": config.supports_model_selection,
            "default_model": config.default_model,
            "connection_test_required": config.connection_test_required
        }
        
        # Add API key if required
        if config.requires_api_key and config.env_key_name:
            result["api_key"] = os.getenv(config.env_key_name)
        
        # Add additional environment variables
        if config.additional_env_vars:
            for env_var, default_value in config.additional_env_vars.items():
                key_name = env_var.lower().replace("_", "_")
                result[key_name] = os.getenv(env_var, default_value)
        
        return result
    
    def get_ollama_models(self) -> List[str]:
        """
        Retrieve available models from local Ollama service.
        
        Returns:
            List[str]: List of available Ollama model names
        """
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return models if models else ["llama2", "mistral", "codellama"]
            else:
                # Return common models as fallback
                return ["llama2", "mistral", "codellama", "llama2:13b", "mistral:7b"]
        except requests.RequestException:
            # Return common models if Ollama service is not available
            return ["llama2", "mistral", "codellama", "llama2:13b", "mistral:7b"]
    
    def get_required_env_vars(self, provider: str) -> List[str]:
        """
        Get list of required environment variables for a provider.
        
        Args:
            provider (str): Provider name
            
        Returns:
            List[str]: List of required environment variable names
        """
        if provider not in self._providers:
            return []
        
        config = self._providers[provider]
        required_vars = []
        
        if config.requires_api_key and config.env_key_name:
            required_vars.append(config.env_key_name)
        
        if config.additional_env_vars:
            for env_var, default_value in config.additional_env_vars.items():
                if default_value is None:  # Required if no default
                    required_vars.append(env_var)
        
        return required_vars
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except (ValueError, TypeError):
            return False
    
    def get_provider_documentation(self, provider: str) -> Dict[str, str]:
        """
        Get documentation and setup instructions for a provider.
        
        Args:
            provider (str): Provider name
            
        Returns:
            Dict[str, str]: Documentation with setup instructions and troubleshooting
        """
        docs = {
            "openai": {
                "setup": "Set OPENAI_API_KEY environment variable with your OpenAI API key from https://platform.openai.com/api-keys",
                "troubleshooting": "Ensure API key is valid and has sufficient credits. Check OpenAI status page for service issues."
            },
            "ollama": {
                "setup": "Install Ollama from https://ollama.ai and run 'ollama serve' to start the service. Pull models with 'ollama pull <model-name>'",
                "troubleshooting": "Ensure Ollama service is running on localhost:11434. Check available models with 'ollama list'"
            },
            "custom": {
                "setup": "Set CUSTOM_LLM_API_KEY and CUSTOM_LLM_BASE_URL environment variables for your external provider",
                "troubleshooting": "Verify the base URL is correct and the API key has proper permissions. Ensure the provider uses OpenAI-compatible API format."
            }
        }
        
        return docs.get(provider, {"setup": "No documentation available", "troubleshooting": "No troubleshooting guide available"})