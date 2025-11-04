from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from pyvis.network import Network
from llm_factory import LLMProviderFactory
from pyvis_config import PyVisConfigManager, SecurityConfig, DependencyConfig, create_secure_pyvis_html
from error_handler import FrontendErrorHandler, track_frontend_error

import asyncio
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize factory
factory = LLMProviderFactory()

# Default configuration - can be overridden by function parameters
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o"


# Extract graph data from input text
async def extract_graph_data(text, provider=DEFAULT_PROVIDER, model=None, temperature=0.0):
    """
    Asynchronously extracts graph data from input text using a graph transformer.

    Args:
        text (str): Input text to be processed into graph format.
        provider (str): LLM provider to use ('openai', 'ollama', 'custom')
        model (str, optional): Model name to use (uses provider default if None)
        temperature (float): Temperature setting for the LLM

    Returns:
        list: A list of GraphDocument objects containing nodes and relationships.
        
    Raises:
        ValueError: If provider configuration is invalid
        ConnectionError: If provider connection fails
        RuntimeError: If graph extraction fails with provider-specific guidance
    """
    def _extract_operation():
        # Create LLM instance using factory
        llm = factory.create_llm(provider=provider, model=model, temperature=temperature)
        
        # Create graph transformer with the LLM
        graph_transformer = LLMGraphTransformer(llm=llm)
        
        # Process documents
        documents = [Document(page_content=text)]
        return graph_transformer.aconvert_to_graph_documents(documents)
    
    try:
        # Execute the extraction operation
        graph_documents = await _extract_operation()
        
        logger.info("Successfully extracted graph data using %s provider with model %s", provider, model or 'default')
        return graph_documents
        
    except Exception as e:
        # Use centralized error handling
        _, user_message, _ = handle_provider_error(
            provider, "graph_extraction", e, 
            {"model": model, "temperature": temperature, "text_length": len(text)}
        )
        raise RuntimeError(user_message) from e


def visualize_graph(graph_documents, use_secure_config=True):
    """
    Visualizes a knowledge graph using PyVis with enhanced error handling and security.

    Args:
        graph_documents (list): A list of GraphDocument objects with nodes and relationships.
        use_secure_config (bool): Whether to use secure PyVis configuration

    Returns:
        pyvis.network.Network: The visualized network graph object.
    """
    error_handler = FrontendErrorHandler()
    
    try:
        # Initialize PyVis configuration manager
        if use_secure_config:
            security_config = SecurityConfig(
                enable_csp=True,
                allow_inline_scripts=False,
                allow_inline_styles=True
            )
            dependency_config = DependencyConfig(
                use_cdn=True,
                local_fallback=True
            )
            config_manager = PyVisConfigManager(security_config, dependency_config)
        else:
            config_manager = None

        # Create network with enhanced configuration
        net = Network(
            height="1200px", 
            width="100%", 
            directed=True,
            notebook=False, 
            bgcolor="#222222", 
            font_color="white", 
            filter_menu=True, 
            cdn_resources='remote'
        )

        nodes = graph_documents[0].nodes
        relationships = graph_documents[0].relationships

        # Build lookup for valid nodes
        node_dict = {node.id: node for node in nodes}
        
        # Filter out invalid edges and collect valid node IDs
        valid_edges = []
        valid_node_ids = set()
        for rel in relationships:
            if rel.source.id in node_dict and rel.target.id in node_dict:
                valid_edges.append(rel)
                valid_node_ids.update([rel.source.id, rel.target.id])

        # Add valid nodes to the graph with error handling
        nodes_added = 0
        for node_id in valid_node_ids:
            node = node_dict[node_id]
            try:
                net.add_node(node.id, label=node.id, title=node.type, group=node.type)
                nodes_added += 1
            except Exception as e:
                logger.warning(f"Failed to add node {node_id}: {str(e)}")
                continue

        # Add valid edges to the graph with error handling
        edges_added = 0
        for rel in valid_edges:
            try:
                net.add_edge(rel.source.id, rel.target.id, label=rel.type.lower())
                edges_added += 1
            except Exception as e:
                logger.warning(f"Failed to add edge {rel.source.id} -> {rel.target.id}: {str(e)}")
                continue

        logger.info(f"Successfully added {nodes_added} nodes and {edges_added} edges to the graph")

        # Configure graph layout and physics with error handling
        try:
            net.set_options("""
                {
                    "physics": {
                        "forceAtlas2Based": {
                            "gravitationalConstant": -100,
                            "centralGravity": 0.01,
                            "springLength": 200,
                            "springConstant": 0.08
                        },
                        "minVelocity": 0.75,
                        "solver": "forceAtlas2Based"
                    },
                    "interaction": {
                        "hover": true,
                        "selectConnectedEdges": false
                    },
                    "nodes": {
                        "font": {"color": "white"},
                        "borderWidth": 2
                    },
                    "edges": {
                        "font": {"color": "white", "align": "middle"},
                        "arrows": {"to": {"enabled": true}}
                    }
                }
            """)
        except Exception as e:
            logger.warning(f"Failed to set graph options: {str(e)}")

        output_file = "knowledge_graph.html"
        
        try:
            if use_secure_config and config_manager:
                # Generate secure HTML with proper dependency management
                import json
                
                # Get nodes and edges data from PyVis network
                nodes_data = net.get_nodes()
                edges_data = net.get_edges()
                
                nodes_js = f"var nodes = new vis.DataSet({json.dumps(nodes_data)});"
                edges_js = f"var edges = new vis.DataSet({json.dumps(edges_data)});"
                
                secure_html = create_secure_pyvis_html(nodes_js, edges_js, config_manager)
                
                # Write secure HTML to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(secure_html)
                
                logger.info(f"Secure graph saved to {os.path.abspath(output_file)}")
            else:
                # Use standard PyVis save method
                net.save_graph(output_file)
                logger.info(f"Standard graph saved to {os.path.abspath(output_file)}")
            
            return net
            
        except Exception as e:
            error_context = {
                'component': 'visualization',
                'user_action': 'save_graph',
                'provider': 'pyvis',
                'nodes_count': nodes_added,
                'edges_count': edges_added
            }
            
            error_id = track_frontend_error(e, error_context)
            logger.error(f"Error saving graph (ID: {error_id}): {str(e)}")
            
            # Try fallback save method
            try:
                net.save_graph(f"fallback_{output_file}")
                logger.info(f"Fallback graph saved to fallback_{output_file}")
                return net
            except Exception as fallback_error:
                logger.error(f"Fallback save also failed: {str(fallback_error)}")
                return None

    except Exception as e:
        error_context = {
            'component': 'visualization',
            'user_action': 'create_graph',
            'provider': 'pyvis'
        }
        
        error_id = track_frontend_error(e, error_context)
        logger.error(f"Visualization creation failed (ID: {error_id}): {str(e)}")
        return None


def generate_knowledge_graph(text, provider=DEFAULT_PROVIDER, model=None, temperature=0.0, **kwargs):
    """
    Generates and visualizes a knowledge graph from input text.

    This function runs the graph extraction asynchronously and then visualizes
    the resulting graph using PyVis. Maintains backward compatibility with
    existing code while supporting new provider functionality.

    Args:
        text (str): Input text to convert into a knowledge graph.
        provider (str): LLM provider to use ('openai', 'ollama', 'custom')
        model (str, optional): Model name to use (uses provider default if None)
        temperature (float): Temperature setting for the LLM
        **kwargs: Additional provider-specific parameters

    Returns:
        pyvis.network.Network: The visualized network graph object.
        
    Raises:
        ValueError: If provider configuration is invalid
        ConnectionError: If provider connection fails
        RuntimeError: If graph generation fails with provider-specific guidance
    """
    try:
        logger.info("Generating knowledge graph using %s provider", provider)
        
        # Validate provider configuration before proceeding
        is_valid, error_msg = validate_provider_connection(provider, model)
        if not is_valid:
            raise ValueError(f"Provider validation failed: {error_msg}")
        
        graph_documents = asyncio.run(extract_graph_data(text, provider, model, temperature))
        net = visualize_graph(graph_documents)
        logger.info("Knowledge graph generation completed successfully")
        return net
    except Exception as e:
        logger.error("Knowledge graph generation failed: %s", str(e))
        # Provide provider-specific error context
        error_guidance = get_provider_error_guidance(provider, str(e))
        raise RuntimeError(f"Knowledge graph generation failed: {error_guidance}") from e


# Backward compatibility function - maintains original function signature
def generate_knowledge_graph_legacy(text):
    """
    Legacy function for backward compatibility.
    
    Generates knowledge graph using default OpenAI provider.
    This function is maintained for backward compatibility with existing code.
    
    Args:
        text (str): Input text to convert into a knowledge graph.
        
    Returns:
        pyvis.network.Network: The visualized network graph object.
    """
    return generate_knowledge_graph(text, provider=DEFAULT_PROVIDER)


def validate_provider_connection(provider, model=None):
    """
    Validate connection to the specified provider before graph generation.
    
    Uses centralized error handling to provide consistent validation
    across all providers with specific troubleshooting guidance.
    
    Args:
        provider (str): Provider name to validate
        model (str, optional): Model name to test
        
    Returns:
        tuple: (is_valid, error_message)
    """
    def _validation_operation():
        # Create LLM instance for testing
        llm = factory.create_llm(provider=provider, model=model)
        
        # Validate connection
        is_connected, error_msg = factory.validate_connection(provider, llm)
        
        if not is_connected:
            raise ConnectionError(error_msg)
        
        return True
    
    # Use safe operation wrapper
    success, result = safe_provider_operation(
        provider, _validation_operation, "connection_validation"
    )
    
    if success:
        logger.info("Provider %s connection validated successfully", provider)
        return True, None
    else:
        logger.warning("Provider %s connection failed: %s", provider, result)
        return False, result


def get_provider_error_guidance(provider, error_message):
    """
    Get user-friendly error guidance for provider-specific issues.
    
    Provides consistent error handling across all providers with specific
    troubleshooting guidance based on error patterns.
    
    Args:
        provider (str): Provider name
        error_message (str): Original error message
        
    Returns:
        str: User-friendly error guidance with actionable steps
    """
    try:
        guidance = factory.config_manager.get_provider_documentation(provider)
        error_lower = error_message.lower()
        
        # Common error patterns across all providers
        if "timeout" in error_lower:
            return f"Connection timeout with {provider}. Please check your network connection and try again."
        
        if "network" in error_lower or "connection refused" in error_lower:
            return f"Network connection failed to {provider}. Please check your internet connection and provider status."
        
        # Provider-specific error handling
        if provider == "openai":
            return _get_openai_error_guidance(error_lower, error_message, guidance)
        elif provider == "ollama":
            return _get_ollama_error_guidance(error_lower, error_message, guidance)
        elif provider == "custom":
            return _get_custom_error_guidance(error_lower, error_message, guidance)
        else:
            return f"Unknown provider '{provider}': {error_message}"
            
    except Exception as e:
        logger.error("Error generating guidance: %s", str(e))
        return f"Error with {provider} provider: {error_message}. Please check your configuration."


def _get_openai_error_guidance(error_lower, error_message, guidance):
    """Get OpenAI-specific error guidance."""
    if "api_key" in error_lower or "authentication" in error_lower or "unauthorized" in error_lower:
        return f"OpenAI authentication failed. {guidance['setup']}. Verify your API key is correct and active."
    elif "rate_limit" in error_lower or "quota" in error_lower:
        return "OpenAI rate limit or quota exceeded. Please wait and try again, or check your usage limits at https://platform.openai.com/usage"
    elif "model" in error_lower and "not found" in error_lower:
        return "OpenAI model not found. Please check the model name or try a different model like 'gpt-4o' or 'gpt-3.5-turbo'."
    elif "billing" in error_lower or "payment" in error_lower:
        return "OpenAI billing issue. Please check your payment method and account status at https://platform.openai.com/account/billing"
    elif "server" in error_lower or "503" in error_lower or "502" in error_lower:
        return "OpenAI service temporarily unavailable. Please try again in a few moments or check https://status.openai.com"
    else:
        return f"OpenAI error: {error_message}. {guidance['troubleshooting']}"


def _get_ollama_error_guidance(error_lower, error_message, guidance):
    """Get Ollama-specific error guidance."""
    if "connect" in error_lower or "service" in error_lower or "refused" in error_lower:
        return f"Cannot connect to Ollama service. {guidance['setup']}. Make sure Ollama is running with 'ollama serve'."
    elif "model" in error_lower and ("not found" in error_lower or "pull" in error_lower):
        available_models = get_available_models("ollama")
        models_text = ", ".join(available_models[:5])  # Show first 5 models
        return f"Ollama model not available. Try pulling the model first: 'ollama pull <model-name>'. Available models: {models_text}"
    elif "port" in error_lower or "11434" in error_lower:
        return "Ollama port issue. Ensure Ollama is running on the correct port (default: 11434) and not blocked by firewall."
    elif "memory" in error_lower or "resource" in error_lower:
        return "Ollama resource issue. The model may be too large for available memory. Try a smaller model or free up system resources."
    else:
        return f"Ollama error: {error_message}. {guidance['troubleshooting']}"


def _get_custom_error_guidance(error_lower, error_message, guidance):
    """Get custom provider-specific error guidance."""
    if "url" in error_lower or "endpoint" in error_lower or "404" in error_lower:
        return f"Custom provider endpoint issue. {guidance['setup']}. Verify the CUSTOM_LLM_BASE_URL is correct and accessible."
    elif "api_key" in error_lower or "authentication" in error_lower or "unauthorized" in error_lower:
        return f"Custom provider authentication failed. {guidance['setup']}. Check your CUSTOM_LLM_API_KEY is valid."
    elif "ssl" in error_lower or "certificate" in error_lower:
        return "SSL/Certificate error with custom provider. Verify the endpoint uses valid HTTPS certificates."
    elif "format" in error_lower or "json" in error_lower:
        return "Custom provider response format issue. Ensure the provider uses OpenAI-compatible API format."
    else:
        return f"Custom provider error: {error_message}. {guidance['troubleshooting']}"


def get_available_providers():
    """
    Get list of available LLM providers.
    
    Returns:
        list: List of available provider names
    """
    return factory.config_manager.get_available_providers()


def get_available_models(provider):
    """
    Get available models for the specified provider.
    
    Args:
        provider (str): Provider name
        
    Returns:
        list: List of available model names
    """
    return factory.get_available_models(provider)


def handle_provider_error(provider, operation, error, context=None):
    """
    Centralized error handling for provider operations.
    
    Provides consistent error handling and logging across all provider operations
    with specific guidance for different types of failures.
    
    Args:
        provider (str): Provider name
        operation (str): Operation being performed (e.g., 'connection', 'generation')
        error (Exception): The original error
        context (dict, optional): Additional context information
        
    Returns:
        tuple: (error_type, user_message, technical_details)
    """
    error_message = str(error)
    error_lower = error_message.lower()
    
    # Determine error type for categorization
    if "authentication" in error_lower or "api_key" in error_lower or "unauthorized" in error_lower:
        error_type = "authentication"
    elif "connect" in error_lower or "network" in error_lower or "timeout" in error_lower:
        error_type = "connection"
    elif "model" in error_lower and "not found" in error_lower:
        error_type = "model_not_found"
    elif "rate_limit" in error_lower or "quota" in error_lower:
        error_type = "rate_limit"
    elif "server" in error_lower or "503" in error_lower or "502" in error_lower:
        error_type = "service_unavailable"
    else:
        error_type = "unknown"
    
    # Get user-friendly guidance
    user_message = get_provider_error_guidance(provider, error_message)
    
    # Log technical details
    technical_details = {
        "provider": provider,
        "operation": operation,
        "error_type": error_type,
        "original_error": error_message,
        "context": context or {}
    }
    
    logger.error("Provider operation failed: %s", technical_details)
    
    return error_type, user_message, technical_details


def safe_provider_operation(provider, operation_func, operation_name, *args, **kwargs):
    """
    Safely execute a provider operation with comprehensive error handling.
    
    Args:
        provider (str): Provider name
        operation_func (callable): Function to execute
        operation_name (str): Name of the operation for logging
        *args: Arguments to pass to operation_func
        **kwargs: Keyword arguments to pass to operation_func
        
    Returns:
        tuple: (success, result_or_error_message)
    """
    try:
        result = operation_func(*args, **kwargs)
        logger.info("Provider operation succeeded: %s with %s", operation_name, provider)
        return True, result
    except Exception as e:
        _, user_message, _ = handle_provider_error(
            provider, operation_name, e, {"args": args, "kwargs": kwargs}
        )
        return False, user_message