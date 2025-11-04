#!/usr/bin/env python3
"""
Simple test script to verify the LLM factory implementation.
"""

from llm_factory import LLMProviderFactory
from llm_config import LLMConfigManager

def test_factory():
    """Test basic factory functionality."""
    print("Testing LLM Provider Factory...")
    
    # Initialize factory
    factory = LLMProviderFactory()
    config_manager = LLMConfigManager()
    
    # Test available providers
    providers = config_manager.get_available_providers()
    print(f"Available providers: {providers}")
    
    # Test provider configurations
    for provider in providers:
        print(f"\n--- Testing {provider} provider ---")
        
        # Check configuration
        is_valid, error = config_manager.validate_provider_config(provider)
        print(f"Configuration valid: {is_valid}")
        if not is_valid:
            print(f"Configuration error: {error}")
            continue
        
        # Get available models
        models = factory.get_available_models(provider)
        print(f"Available models: {models[:3]}...")  # Show first 3 models
        
        # Test connection validation (without creating LLM)
        is_connected, conn_error = factory.validate_connection(provider)
        print(f"Connection test: {is_connected}")
        if not is_connected:
            print(f"Connection error: {conn_error}")

if __name__ == "__main__":
    test_factory()