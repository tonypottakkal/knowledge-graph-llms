"""
LLM Provider Factory

This module implements a factory pattern for creating LLM instances from different providers,
with connection validation and error handling for each provider type.
"""

from typing import Dict, Any, Optional, Tuple
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from llm_config import LLMConfigManager
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Factory class for creating LLM instances from different providers.
    
    Supports OpenAI, Ollama, and custom external providers with
    connection validation and error handling.
    """
    
    def __init__(self):
        """Initialize the factory with configuration manager."""
        self.config_manager = LLMConfigManager()
    
    def create_llm(self, provider: str, model: Optional[str] = None, 
                   temperature: float = 0.0, max_tokens: Optional[int] = None,
                   **kwargs) -> BaseChatModel:
        """
        Create an LLM instance for the specified provider.
        
        Args:
            provider (str): Provider name ('openai', 'ollama', 'custom')
            model (Optional[str]): Model name to use (uses default if None)
            temperature (float): Temperature setting for the model
            max_tokens (Optional[int]): Maximum tokens for response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            BaseChatModel: Configured LLM instance
            
        Raises:
            ValueError: If provider is unsupported or configuration is invalid
            ConnectionError: If provider connection cannot be established
        """
        # Validate provider configuration
        is_valid, error_msg = self.config_manager.validate_provider_config(provider)
        if not is_valid:
            raise ValueError(f"Invalid provider configuration: {error_msg}")
        
        # Get provider configuration
        config = self.config_manager.get_provider_config(provider)
        
        # Use provided model or default
        if model is None:
            model = config.get("default_model")
        
        # Create provider-specific LLM instance
        if provider == "openai":
            return self._create_openai_llm(config, model, temperature, max_tokens, **kwargs)
        elif provider == "ollama":
            return self._create_ollama_llm(config, model, temperature, max_tokens, **kwargs)
        elif provider == "custom":
            return self._create_custom_llm(config, model, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _create_openai_llm(self, config: Dict[str, Any], model: str, 
                          temperature: float, max_tokens: Optional[int],
                          **kwargs) -> ChatOpenAI:
        """Create OpenAI LLM instance."""
        params = {
            "model": model,
            "temperature": temperature,
            "api_key": config["api_key"]
        }
        
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        
        # Add any additional OpenAI-specific parameters
        params.update(kwargs)
        
        try:
            llm = ChatOpenAI(**params)
            logger.info(f"Created OpenAI LLM with model: {model}")
            return llm
        except Exception as e:
            raise ConnectionError(f"Failed to create OpenAI LLM: {str(e)}")
    
    def _create_ollama_llm(self, config: Dict[str, Any], model: str,
                          temperature: float, max_tokens: Optional[int],
                          **kwargs) -> ChatOllama:
        """Create Ollama LLM instance."""
        base_url = config.get("ollama_base_url", "http://localhost:11434")
        
        params = {
            "model": model,
            "temperature": temperature,
            "base_url": base_url
        }
        
        if max_tokens is not None:
            params["num_predict"] = max_tokens  # Ollama uses num_predict instead of max_tokens
        
        # Add any additional Ollama-specific parameters
        params.update(kwargs)
        
        try:
            llm = ChatOllama(**params)
            logger.info(f"Created Ollama LLM with model: {model} at {base_url}")
            return llm
        except Exception as e:
            raise ConnectionError(f"Failed to create Ollama LLM: {str(e)}")
    
    def _create_custom_llm(self, config: Dict[str, Any], model: str,
                          temperature: float, max_tokens: Optional[int],
                          **kwargs) -> ChatOpenAI:
        """Create custom external provider LLM instance using OpenAI-compatible API."""
        base_url = config.get("custom_llm_base_url")
        api_key = config.get("api_key")
        
        if not base_url:
            raise ValueError("Custom provider requires CUSTOM_LLM_BASE_URL environment variable")
        
        params = {
            "model": model,
            "temperature": temperature,
            "api_key": api_key,
            "base_url": base_url
        }
        
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        
        # Add any additional custom provider parameters
        params.update(kwargs)
        
        try:
            llm = ChatOpenAI(**params)
            logger.info(f"Created custom LLM with model: {model} at {base_url}")
            return llm
        except Exception as e:
            raise ConnectionError(f"Failed to create custom LLM: {str(e)}")
    
    def validate_connection(self, provider: str, llm: Optional[BaseChatModel] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate connection to the specified provider.
        
        Args:
            provider (str): Provider name to validate
            llm (Optional[BaseChatModel]): LLM instance to test (creates new if None)
            
        Returns:
            Tuple[bool, Optional[str]]: (is_connected, error_message)
        """
        try:
            if provider == "openai":
                return self._validate_openai_connection(llm)
            elif provider == "ollama":
                return self._validate_ollama_connection(llm)
            elif provider == "custom":
                return self._validate_custom_connection(llm)
            else:
                return False, f"Unknown provider: {provider}"
        except Exception as e:
            return False, f"Connection validation failed: {str(e)}"
    
    def _validate_openai_connection(self, llm: Optional[BaseChatModel] = None) -> Tuple[bool, Optional[str]]:
        """Validate OpenAI connection."""
        try:
            if llm is None:
                llm = self.create_llm("openai")
            
            # Test with a simple message
            response = llm.invoke("Hello")
            if response and hasattr(response, 'content'):
                logger.info("OpenAI connection validated successfully")
                return True, None
            else:
                return False, "Invalid response from OpenAI API"
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return False, "Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable."
            elif "rate_limit" in error_msg.lower():
                return False, "OpenAI rate limit exceeded. Please try again later."
            else:
                return False, f"OpenAI connection failed: {error_msg}"
    
    def _validate_ollama_connection(self, llm: Optional[BaseChatModel] = None) -> Tuple[bool, Optional[str]]:
        """Validate Ollama connection."""
        config = self.config_manager.get_provider_config("ollama")
        base_url = config.get("ollama_base_url", "http://localhost:11434")
        
        try:
            # First check if Ollama service is running
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False, f"Ollama service not accessible at {base_url}. Please ensure Ollama is running with 'ollama serve'."
            
            # Check if any models are available
            data = response.json()
            models = data.get("models", [])
            if not models:
                return False, "No models found in Ollama. Please pull a model first (e.g., 'ollama pull llama2')."
            
            # Test LLM if provided
            if llm is not None:
                try:
                    test_response = llm.invoke("Hello")
                    if test_response and hasattr(test_response, 'content'):
                        logger.info("Ollama connection validated successfully")
                        return True, None
                    else:
                        return False, "Invalid response from Ollama"
                except Exception as llm_error:
                    # Check if it's a model-specific error
                    if "model" in str(llm_error).lower():
                        available_models = [model["name"] for model in models]
                        return False, f"Model not available. Available models: {', '.join(available_models)}"
                    else:
                        return False, f"Ollama LLM test failed: {str(llm_error)}"
            
            logger.info("Ollama service is accessible")
            return True, None
            
        except requests.RequestException as e:
            return False, f"Cannot connect to Ollama at {base_url}. Please ensure Ollama is installed and running with 'ollama serve'. Error: {str(e)}"
        except Exception as e:
            return False, f"Ollama connection failed: {str(e)}"
    
    def _validate_custom_connection(self, llm: Optional[BaseChatModel] = None) -> Tuple[bool, Optional[str]]:
        """Validate custom provider connection."""
        config = self.config_manager.get_provider_config("custom")
        base_url = config.get("custom_llm_base_url")
        api_key = config.get("api_key")
        
        if not base_url:
            return False, "Custom provider requires CUSTOM_LLM_BASE_URL environment variable"
        
        if not api_key:
            return False, "Custom provider requires CUSTOM_LLM_API_KEY environment variable"
        
        try:
            # Test basic connectivity to the endpoint with authentication
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Try to access models endpoint (common for OpenAI-compatible APIs)
            models_url = f"{base_url.rstrip('/')}/models"
            response = requests.get(models_url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                return False, "Authentication failed. Please check your CUSTOM_LLM_API_KEY."
            elif response.status_code == 404:
                # Models endpoint might not exist, try base URL
                response = requests.get(base_url, headers=headers, timeout=10)
            
            # Test LLM if provided
            if llm is not None:
                try:
                    test_response = llm.invoke("Hello")
                    if test_response and hasattr(test_response, 'content'):
                        logger.info("Custom provider connection validated successfully")
                        return True, None
                    else:
                        return False, "Invalid response from custom provider"
                except Exception as llm_error:
                    error_str = str(llm_error).lower()
                    if "authentication" in error_str or "unauthorized" in error_str:
                        return False, "Authentication failed. Please verify your CUSTOM_LLM_API_KEY."
                    elif "not found" in error_str or "404" in error_str:
                        return False, "Model or endpoint not found. Please verify your CUSTOM_LLM_BASE_URL and model name."
                    else:
                        return False, f"Custom provider LLM test failed: {str(llm_error)}"
            
            logger.info("Custom provider endpoint is accessible")
            return True, None
            
        except requests.RequestException as e:
            error_str = str(e).lower()
            if "timeout" in error_str:
                return False, f"Connection timeout to {base_url}. Please check the URL and network connectivity."
            elif "connection" in error_str:
                return False, f"Cannot connect to custom provider at {base_url}. Please verify the URL is correct and accessible."
            else:
                return False, f"Network error connecting to custom provider: {str(e)}"
        except Exception as e:
            return False, f"Custom provider connection failed: {str(e)}"
    
    def get_available_models(self, provider: str) -> list[str]:
        """
        Get available models for the specified provider.
        
        Args:
            provider (str): Provider name
            
        Returns:
            list[str]: List of available model names
        """
        if provider == "openai":
            return [
                "gpt-4o",
                "gpt-4o-mini", 
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ]
        elif provider == "ollama":
            return self.config_manager.get_ollama_models()
        elif provider == "custom":
            # For custom providers, return common model names
            # In practice, this would need to be configured per provider
            return [
                "gpt-3.5-turbo",
                "gpt-4",
                "claude-3-sonnet",
                "claude-3-haiku"
            ]
        else:
            return []
    
    def is_ollama_model_available(self, model_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a specific Ollama model is available locally.
        
        Args:
            model_name (str): Name of the model to check
            
        Returns:
            Tuple[bool, Optional[str]]: (is_available, error_message)
        """
        try:
            available_models = self.config_manager.get_ollama_models()
            
            # Check exact match first
            if model_name in available_models:
                return True, None
            
            # Check partial matches (e.g., "llama2" matches "llama2:latest")
            partial_matches = [m for m in available_models if model_name in m]
            if partial_matches:
                return True, None
            
            return False, f"Model '{model_name}' not found. Available models: {', '.join(available_models)}. Use 'ollama pull {model_name}' to download it."
            
        except Exception as e:
            return False, f"Failed to check Ollama models: {str(e)}"
    
    def validate_custom_endpoint(self, base_url: str, api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a custom endpoint URL and API key.
        
        Args:
            base_url (str): Base URL of the custom provider
            api_key (str): API key for authentication
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Validate URL format
        if not self.config_manager._is_valid_url(base_url):
            return False, "Invalid URL format. Please provide a valid HTTP/HTTPS URL."
        
        # Ensure URL ends with /v1 for OpenAI compatibility
        if not base_url.rstrip('/').endswith('/v1'):
            base_url = base_url.rstrip('/') + '/v1'
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Test connectivity
            response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, None
            elif response.status_code == 401:
                return False, "Authentication failed. Please check your API key."
            elif response.status_code == 404:
                # Try without /models endpoint
                response = requests.get(base_url, headers=headers, timeout=10)
                if response.status_code < 400:
                    return True, None
                else:
                    return False, f"Endpoint returned status {response.status_code}. Please verify the URL is correct."
            else:
                return False, f"Endpoint returned status {response.status_code}. Please verify the URL and API key."
                
        except requests.RequestException as e:
            return False, f"Connection failed: {str(e)}"