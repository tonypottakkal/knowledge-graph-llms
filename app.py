# Import necessary modules
import streamlit as st
import streamlit.components.v1 as components  # For embedding custom HTML
from generate_knowledge_graph import generate_knowledge_graph
from llm_factory import LLMProviderFactory
from llm_config import LLMConfigManager
from streamlit_security import initialize_streamlit_security, display_secure_html, IframeSandboxConfig
from error_handler import get_error_tracker

# Set up Streamlit page configuration
st.set_page_config(
    page_icon=None, 
    layout="wide",  # Use wide layout for better graph display
    initial_sidebar_state="auto", 
    menu_items=None
)

# Initialize security protections
@st.cache_resource
def get_security_manager():
    """Initialize and cache security manager."""
    iframe_config = IframeSandboxConfig(
        allow_scripts=True,
        allow_same_origin=False,  # Better security
        allow_forms=False,
        allow_popups=False
    )
    return initialize_streamlit_security(iframe_config)

security_manager = get_security_manager()

# Set the title of the app
st.title("Knowledge Graph From Text")

# Add helpful information about the app
with st.expander("ℹ️ About this app"):
    st.write("""
    This application generates interactive knowledge graphs from text using various LLM providers.
    
    **Supported Providers:**
    - **OpenAI**: GPT-4o, GPT-3.5-turbo, and other OpenAI models
    - **Ollama**: Local models like Llama2, Mistral, CodeLlama
    - **Custom**: Any OpenAI-compatible API endpoint
    
    **How to use:**
    1. Select your preferred LLM provider from the sidebar
    2. Configure the provider settings and test the connection
    3. Upload a text file or paste text directly
    4. Click "Generate Knowledge Graph" to create your visualization
    """)

# Initialize LLM components
@st.cache_resource
def get_llm_components():
    """Initialize and cache LLM factory and config manager."""
    config_manager = LLMConfigManager()
    factory = LLMProviderFactory()
    return config_manager, factory

config_manager, factory = get_llm_components()

def display_knowledge_graph_securely(net, security_manager):
    """Helper function to display knowledge graph with error handling."""
    if net:
        st.success("✅ Knowledge graph generated successfully!")
        
        # Read the generated HTML file
        output_file = "knowledge_graph.html"
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Display using secure component with error handling
            display_secure_html(html_content, height=1000, security_manager=security_manager)
            
        except Exception as display_error:
            st.error(f"❌ Error displaying graph: {str(display_error)}")
            
            # Fallback to standard display
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    components.html(f.read(), height=1000)
            except Exception as fallback_error:
                st.error(f"❌ Fallback display also failed: {str(fallback_error)}")
    else:
        st.error("❌ Failed to generate knowledge graph. Please check your configuration and try again.")

# Display current configuration status
col1, col2, col3 = st.columns(3)
with col1:
    if 'llm_provider' in st.session_state:
        provider_name = config_manager.get_provider_display_names().get(st.session_state.llm_provider, st.session_state.llm_provider)
        st.info(f"🔧 Provider: {provider_name}")
with col2:
    if 'llm_model' in st.session_state and st.session_state.llm_model:
        st.info(f"🤖 Model: {st.session_state.llm_model}")
with col3:
    if 'llm_temperature' in st.session_state:
        st.info(f"🌡️ Temperature: {st.session_state.llm_temperature}")

def display_error_guidance(error_message, provider, config_mgr):
    """Display comprehensive error guidance based on error type and provider."""
    error_lower = error_message.lower()
    
    if "authentication" in error_lower or "api_key" in error_lower:
        st.error("🔑 **Authentication Error**")
        st.write("Your API key appears to be invalid or missing.")
        if provider == 'openai':
            st.write("1. Check your OPENAI_API_KEY environment variable")
            st.write("2. Verify the key at https://platform.openai.com/api-keys")
            st.write("3. Ensure your account has sufficient credits")
        elif provider == 'custom':
            st.write("1. Check your CUSTOM_LLM_API_KEY environment variable")
            st.write("2. Verify the key with your provider")
    
    elif "connection" in error_lower or "network" in error_lower:
        st.error("🌐 **Connection Error**")
        st.write("Unable to connect to the LLM provider.")
        if provider == 'ollama':
            st.write("1. Ensure Ollama is running: `ollama serve`")
            st.write("2. Check if the service is accessible at http://localhost:11434")
            st.write("3. Verify the model is available: `ollama list`")
        else:
            st.write("1. Check your internet connection")
            st.write("2. Verify the provider's service status")
            st.write("3. Try again in a few moments")
    
    elif "model" in error_lower and "not found" in error_lower:
        st.error("🤖 **Model Error**")
        st.write("The selected model is not available.")
        if provider == 'ollama':
            model_name = st.session_state.get('llm_model', 'model')
            st.write(f"1. Pull the model: `ollama pull {model_name}`")
            st.write("2. Check available models: `ollama list`")
            st.write("3. Try a different model from the dropdown")
        else:
            st.write("1. Try a different model from the dropdown")
            st.write("2. Check if the model name is correct")
    
    elif "rate_limit" in error_lower or "quota" in error_lower:
        st.error("⏱️ **Rate Limit Error**")
        st.write("You've exceeded the provider's rate limits.")
        st.write("1. Wait a few minutes before trying again")
        st.write("2. Consider upgrading your plan if using a paid service")
        st.write("3. Try using a different provider temporarily")
    
    else:
        st.error("❓ **Unknown Error**")
        st.write("An unexpected error occurred.")
    
    # Show provider-specific troubleshooting
    docs = config_mgr.get_provider_documentation(provider)
    with st.expander("🔧 Additional Troubleshooting"):
        st.write("**Setup Instructions:**")
        st.write(docs['setup'])
        st.write("**General Troubleshooting:**")
        st.write(docs['troubleshooting'])
        
        # Add provider-specific tips
        if provider == 'ollama':
            st.write("**Ollama-specific tips:**")
            st.write("- Restart Ollama service: `ollama serve`")
            st.write("- Check system resources (RAM/CPU)")
            st.write("- Try a smaller model if running out of memory")
        elif provider == 'openai':
            st.write("**OpenAI-specific tips:**")
            st.write("- Check OpenAI status: https://status.openai.com")
            st.write("- Verify billing: https://platform.openai.com/account/billing")
            st.write("- Review usage: https://platform.openai.com/usage")
        elif provider == 'custom':
            st.write("**Custom provider tips:**")
            st.write("- Verify endpoint URL format")
            st.write("- Check API compatibility (OpenAI format)")
            st.write("- Test endpoint with curl or Postman")

# Initialize session state for LLM configuration
if 'llm_provider' not in st.session_state:
    st.session_state.llm_provider = 'openai'
if 'llm_model' not in st.session_state:
    st.session_state.llm_model = None
if 'llm_temperature' not in st.session_state:
    st.session_state.llm_temperature = 0.0
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = {}

# Sidebar section for LLM configuration
st.sidebar.title("LLM Configuration")

# Provider selection dropdown
available_providers = config_manager.get_available_providers()
provider_display_names = config_manager.get_provider_display_names()
provider_options = [provider_display_names[p] for p in available_providers]

selected_display_name = st.sidebar.selectbox(
    "Choose LLM Provider:",
    provider_options,
    index=available_providers.index(st.session_state.llm_provider) if st.session_state.llm_provider in available_providers else 0,
    help="""
    **OpenAI**: Cloud-based models with high quality results. Requires API key and internet connection.
    
    **Ollama (Local)**: Run models locally on your machine. No API key needed, but requires Ollama installation.
    
    **Custom External Provider**: Use any OpenAI-compatible API endpoint. Requires custom configuration.
    """
)

# Map display name back to provider name
selected_provider = None
for provider, display_name in provider_display_names.items():
    if display_name == selected_display_name:
        selected_provider = provider
        break

# Update session state if provider changed
if selected_provider != st.session_state.llm_provider:
    st.session_state.llm_provider = selected_provider
    st.session_state.llm_model = None  # Reset model selection
    st.session_state.connection_status = {}  # Reset connection status
    st.rerun()  # Refresh to update UI

# Show provider-specific information
current_provider = st.session_state.llm_provider
provider_config = config_manager.get_provider_config(current_provider)

# Provider information panel
with st.sidebar.expander(f"ℹ️ About {provider_config['display_name']}"):
    docs = config_manager.get_provider_documentation(current_provider)
    st.write("**Setup:**")
    st.write(docs['setup'])
    
    if current_provider == 'openai':
        st.write("**Benefits:** High-quality results, latest models, reliable service")
        st.write("**Requirements:** Internet connection, API key, usage costs")
    elif current_provider == 'ollama':
        st.write("**Benefits:** Privacy, no usage costs, works offline")
        st.write("**Requirements:** Local installation, sufficient RAM/storage")
    elif current_provider == 'custom':
        st.write("**Benefits:** Flexibility, use any compatible provider")
        st.write("**Requirements:** Valid API endpoint, proper authentication")

# Provider-specific configuration panels

# Model selection for providers that support it
if provider_config.get('supports_model_selection', False):
    if current_provider == 'ollama':
        # Dynamic model loading for Ollama with loading state
        with st.sidebar:
            if st.button("🔄 Refresh Models", help="Reload available Ollama models"):
                with st.spinner("Loading Ollama models..."):
                    # Clear cache and reload models
                    get_llm_components.clear()
                    config_manager, factory = get_llm_components()
        
        available_models = factory.get_available_models('ollama')
        if available_models:
            default_index = 0
            if st.session_state.llm_model and st.session_state.llm_model in available_models:
                default_index = available_models.index(st.session_state.llm_model)
            
            selected_model = st.sidebar.selectbox(
                "Select Ollama Model:",
                available_models,
                index=default_index,
                help="Choose from locally available Ollama models. Click 'Refresh Models' if you just pulled a new model."
            )
            st.session_state.llm_model = selected_model
        else:
            st.sidebar.warning("⚠️ No Ollama models found.")
            st.sidebar.info("💡 Pull a model first: `ollama pull llama2`")
            st.session_state.llm_model = "llama2"  # Default fallback
    
    elif current_provider == 'openai':
        # OpenAI model selection
        openai_models = factory.get_available_models('openai')
        default_index = 0
        if st.session_state.llm_model and st.session_state.llm_model in openai_models:
            default_index = openai_models.index(st.session_state.llm_model)
        
        selected_model = st.sidebar.selectbox(
            "Select OpenAI Model:",
            openai_models,
            index=default_index,
            help="Choose OpenAI model for knowledge graph generation"
        )
        st.session_state.llm_model = selected_model
    
    elif current_provider == 'custom':
        # Custom provider model selection
        custom_models = factory.get_available_models('custom')
        default_index = 0
        if st.session_state.llm_model and st.session_state.llm_model in custom_models:
            default_index = custom_models.index(st.session_state.llm_model)
        
        selected_model = st.sidebar.selectbox(
            "Select Model:",
            custom_models,
            index=default_index,
            help="Choose model for your custom provider"
        )
        st.session_state.llm_model = selected_model

# Temperature setting
st.session_state.llm_temperature = st.sidebar.slider(
    "Temperature:",
    min_value=0.0,
    max_value=1.0,
    value=st.session_state.llm_temperature,
    step=0.1,
    help="Controls randomness in model responses. Lower values are more deterministic."
)

# Provider-specific configuration and connection testing
st.sidebar.markdown("---")
st.sidebar.subheader("Provider Configuration")

# Custom endpoint configuration for external providers
if current_provider == 'custom':
    import os
    
    # Display current environment variable values (without exposing sensitive data)
    custom_base_url = os.getenv('CUSTOM_LLM_BASE_URL', '')
    custom_api_key = os.getenv('CUSTOM_LLM_API_KEY', '')
    
    st.sidebar.info("💡 Configure these environment variables:")
    st.sidebar.code("CUSTOM_LLM_BASE_URL=https://api.your-provider.com/v1")
    st.sidebar.code("CUSTOM_LLM_API_KEY=your-api-key")
    
    if custom_base_url:
        st.sidebar.success(f"✅ Base URL configured: {custom_base_url}")
    else:
        st.sidebar.error("❌ CUSTOM_LLM_BASE_URL not set")
    
    if custom_api_key:
        st.sidebar.success("✅ API Key configured")
    else:
        st.sidebar.error("❌ CUSTOM_LLM_API_KEY not set")

elif current_provider == 'openai':
    import os
    openai_api_key = os.getenv('OPENAI_API_KEY', '')
    
    if openai_api_key:
        st.sidebar.success("✅ OpenAI API Key configured")
    else:
        st.sidebar.error("❌ OPENAI_API_KEY not set")
        st.sidebar.info("💡 Set your OpenAI API key:")
        st.sidebar.code("OPENAI_API_KEY=sk-your-api-key")

elif current_provider == 'ollama':
    import os
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    st.sidebar.info(f"🔗 Ollama URL: {ollama_base_url}")
    
    # Show Ollama-specific help
    with st.sidebar.expander("Ollama Setup Help"):
        st.write("**Installation:**")
        st.write("1. Install Ollama from https://ollama.ai")
        st.write("2. Start service: `ollama serve`")
        st.write("3. Pull models: `ollama pull llama2`")
        st.write("4. List models: `ollama list`")

# Connection testing and status indicators
connection_key = f"{current_provider}_{st.session_state.llm_model}"

# Connection test button
if st.sidebar.button("🔍 Test Connection", help="Test connection to the selected LLM provider"):
    with st.sidebar:
        with st.spinner("Testing connection..."):
            try:
                # Validate provider configuration first
                is_valid, error_msg = config_manager.validate_provider_config(current_provider)
                
                if not is_valid:
                    st.session_state.connection_status[connection_key] = {
                        'status': 'error',
                        'message': error_msg
                    }
                else:
                    # Test connection using factory
                    is_connected, conn_error = factory.validate_connection(current_provider)
                    
                    if is_connected:
                        st.session_state.connection_status[connection_key] = {
                            'status': 'success',
                            'message': f"Successfully connected to {provider_display_names[current_provider]}"
                        }
                    else:
                        st.session_state.connection_status[connection_key] = {
                            'status': 'error',
                            'message': conn_error or "Connection failed"
                        }
            except Exception as e:
                st.session_state.connection_status[connection_key] = {
                    'status': 'error',
                    'message': f"Connection test failed: {str(e)}"
                }

# Display connection status
if connection_key in st.session_state.connection_status:
    status_info = st.session_state.connection_status[connection_key]
    
    if status_info['status'] == 'success':
        st.sidebar.success(f"✅ {status_info['message']}")
    elif status_info['status'] == 'error':
        st.sidebar.error(f"❌ {status_info['message']}")
        
        # Show troubleshooting guidance
        docs = config_manager.get_provider_documentation(current_provider)
        with st.sidebar.expander("🔧 Troubleshooting"):
            st.write("**Setup Instructions:**")
            st.write(docs['setup'])
            st.write("**Troubleshooting:**")
            st.write(docs['troubleshooting'])

# Error handling configuration section
st.sidebar.markdown("---")
st.sidebar.subheader("Error Handling")

# Show error tracking information
error_tracker = get_error_tracker()
error_patterns = error_tracker.get_error_patterns()

if error_patterns["total_errors"] > 0:
    with st.sidebar.expander("📊 Error Statistics"):
        st.write(f"**Total Errors:** {error_patterns['total_errors']}")
        if error_patterns["error_types"]:
            st.write("**Error Types:**")
            for error_type, count in error_patterns["error_types"].items():
                st.write(f"- {error_type}: {count}")

# Security status indicator
with st.sidebar.expander("🔒 Security Status"):
    st.success("✅ Browser extension protection active")
    st.success("✅ Content Security Policy enabled")
    st.success("✅ Form field protection active")
    st.success("✅ Error suppression active")

# Sidebar section for user input method
st.sidebar.markdown("---")
st.sidebar.title("Input document")
input_method = st.sidebar.radio(
    "Choose an input method:",
    ["Upload txt", "Input text"],  # Options for uploading a file or manually inputting text
)

# Case 1: User chooses to upload a .txt file
if input_method == "Upload txt":
    # File uploader widget in the sidebar
    uploaded_file = st.sidebar.file_uploader(label="Upload file", type=["txt"])
    
    if uploaded_file is not None:
        # Read the uploaded file content and decode it as UTF-8 text
        text = uploaded_file.read().decode("utf-8")
 
        # Button to generate the knowledge graph
        if st.sidebar.button("Generate Knowledge Graph"):
            # Check if provider is properly configured
            is_valid, error_msg = config_manager.validate_provider_config(st.session_state.llm_provider)
            
            if not is_valid:
                st.error(f"❌ Configuration Error: {error_msg}")
                st.info("Please configure the required environment variables and test the connection.")
            else:
                with st.spinner(f"Generating knowledge graph using {provider_display_names[st.session_state.llm_provider]}..."):
                    try:
                        # Call the function to generate the graph with selected provider
                        net = generate_knowledge_graph(
                            text,
                            provider=st.session_state.llm_provider,
                            model=st.session_state.llm_model,
                            temperature=st.session_state.llm_temperature
                        )
                        
                        # Display the graph securely
                        display_knowledge_graph_securely(net, security_manager)
                    
                    except Exception as e:
                        error_message = str(e)
                        st.error(f"❌ Error generating knowledge graph: {error_message}")
                        display_error_guidance(error_message, st.session_state.llm_provider, config_manager)

# Case 2: User chooses to directly input text
else:
    # Text area for manual input
    text = st.sidebar.text_area("Input text", height=300)

    if text:  # Check if the text area is not empty
        if st.sidebar.button("Generate Knowledge Graph"):
            # Check if provider is properly configured
            is_valid, error_msg = config_manager.validate_provider_config(st.session_state.llm_provider)
            
            if not is_valid:
                st.error(f"❌ Configuration Error: {error_msg}")
                st.info("Please configure the required environment variables and test the connection.")
            else:
                with st.spinner(f"Generating knowledge graph using {provider_display_names[st.session_state.llm_provider]}..."):
                    try:
                        # Call the function to generate the graph with selected provider
                        net = generate_knowledge_graph(
                            text,
                            provider=st.session_state.llm_provider,
                            model=st.session_state.llm_model,
                            temperature=st.session_state.llm_temperature
                        )
                        
                        # Display the graph securely
                        display_knowledge_graph_securely(net, security_manager)
                    
                    except Exception as e:
                        error_message = str(e)
                        st.error(f"❌ Error generating knowledge graph: {error_message}")
                        display_error_guidance(error_message, st.session_state.llm_provider, config_manager)