# Knowledge Graph Generator

A Streamlit application that extracts graph data (entities and relationships) from text input using LangChain and multiple LLM providers, and generates interactive graphs. Supports OpenAI GPT models, local Ollama models, and custom external LLM providers.
![CleanShot 2025-05-28 at 13 11 46](https://github.com/user-attachments/assets/4fef9158-8dd8-432d-bb8a-b53953a82c6c)

👉 This repo is part of my project tutorial on Youtube:
[![](https://img.youtube.com/vi/O-T_6KOXML4/0.jpg)](https://www.youtube.com/watch?v=O-T_6KOXML4)

## Features

- **Multiple LLM Provider Support**: Choose between OpenAI, local Ollama models, Anthropic Claude, or custom external providers
- **Two input methods**: Text upload (.txt files) or direct text input
- **Interactive knowledge graph visualization**: Drag, zoom, and explore generated graphs
- **Customizable graph display**: Physics-based layout with filtering options
- **Provider-specific configuration**: Easy setup and switching between different LLM providers
- **Local model support**: Run completely offline with Ollama models
- **Secure credential management**: Environment variable-based API key handling

## Installation

### Prerequisites

- Python 3.8 or higher
- At least one of the following:
  - OpenAI API key (for GPT models)
  - Ollama installed locally (for local models)
  - API key for other supported providers (Anthropic, custom providers)

### Dependencies

The application requires the following Python packages:

- langchain (>= 0.1.0): Core LLM framework
- langchain-experimental (>= 0.0.45): Experimental LangChain features
- langchain-openai (>= 0.1.0): OpenAI integration for LangChain
- langchain-community (>= 0.0.20): Community LLM integrations (Ollama support)
- langchain-anthropic (>= 0.1.0): Anthropic Claude integration
- python-dotenv (>= 1.0.0): Environment variable support
- pyvis (>= 0.3.2): Graph visualization
- streamlit (>= 1.32.0): Web UI framework
- requests (>= 2.28.0): HTTP requests for provider validation

Install all required dependencies using the provided requirements.txt file:

```bash
pip install -r requirements.txt
```

### Setup

1. Clone this repository:
   ```bash
   git clone [repository-url]
   cd knowledge-graph-llms
   ```

   Note: Replace `[repository-url]` with the actual URL of this repository.

2. **Environment Configuration**: Copy the example environment file and configure your providers:
   ```bash
   cp .env.example .env
   ```

   Then edit the `.env` file with your provider credentials (see [Provider Setup](#provider-setup) below).

## Provider Setup

The application supports multiple LLM providers. You only need to configure the providers you plan to use.

### OpenAI Setup

1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add to your `.env` file:
   ```
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

**Supported Models**: gpt-4o, gpt-4o-mini, gpt-3.5-turbo, gpt-4-turbo

### Ollama Setup (Local Models)

Ollama allows you to run large language models locally on your machine.

1. **Install Ollama**:
   - **macOS**: `brew install ollama`
   - **Linux**: `curl -fsSL https://ollama.ai/install.sh | sh`
   - **Windows**: Download from [ollama.ai](https://ollama.ai)

2. **Start Ollama service**:
   ```bash
   ollama serve
   ```

3. **Pull a model** (choose one or more):
   ```bash
   # Recommended models for knowledge graph generation
   ollama pull llama3.1:8b      # Fast, good quality
   ollama pull llama3.1:70b     # Higher quality, slower
   ollama pull mistral:7b       # Alternative option
   ollama pull codellama:13b    # Good for structured output
   ```

4. **Optional configuration** in `.env` (only if using non-default settings):
   ```
   OLLAMA_BASE_URL=http://localhost:11434
   ```

**Troubleshooting Ollama**:
- Ensure Ollama service is running: `ollama list` should show your models
- Check service status: `curl http://localhost:11434/api/tags`
- If port 11434 is busy, change the port in Ollama settings and update `OLLAMA_BASE_URL`

### Anthropic Claude Setup

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
2. Add to your `.env` file:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
   ```

**Supported Models**: claude-3-5-sonnet-20241022, claude-3-haiku-20240307, claude-3-opus-20240229

### Custom Provider Setup

For other OpenAI-compatible APIs (Together AI, Anyscale, local servers, etc.):

1. Add to your `.env` file:
   ```
   CUSTOM_LLM_API_KEY=your-custom-provider-api-key
   CUSTOM_LLM_BASE_URL=https://api.your-provider.com/v1
   ```

**Examples**:
- **Together AI**: `CUSTOM_LLM_BASE_URL=https://api.together.xyz/v1`
- **Anyscale**: `CUSTOM_LLM_BASE_URL=https://api.endpoints.anyscale.com/v1`
- **Local OpenAI-compatible server**: `CUSTOM_LLM_BASE_URL=http://localhost:8000/v1`

## Running the Application

To run the Streamlit app:

```bash
streamlit run app.py
```

This will start the application and open it in your default web browser (typically at http://localhost:8501).

## Usage

1. **Select LLM Provider**: Choose your preferred provider from the dropdown in the sidebar
2. **Configure Provider**: 
   - For OpenAI/Anthropic: Select your preferred model
   - For Ollama: Choose from available local models
   - For Custom: The configured endpoint will be used automatically
3. **Choose Input Method**: Select "Upload txt" or "Input text" from the sidebar
4. **Provide Text**: Upload a .txt file or paste text directly into the text area
5. **Generate Graph**: Click "Generate Knowledge Graph" and wait for processing
6. **Explore Results**: Interact with the generated knowledge graph:
   - Drag nodes to rearrange the layout
   - Hover over nodes and edges for additional information
   - Zoom in/out using the mouse wheel
   - Use filters to focus on specific nodes and relationships

### Provider-Specific Notes

- **OpenAI**: Fastest processing, requires internet connection and API credits
- **Ollama**: Completely offline, slower processing, no API costs
- **Anthropic**: High-quality results, requires internet connection and API credits
- **Custom**: Performance varies by provider, check provider documentation for model capabilities

## How It Works

The application uses LangChain's experimental graph transformers with your chosen LLM provider to:
1. **Extract entities** from the input text using natural language processing
2. **Identify relationships** between entities through contextual analysis
3. **Generate a graph structure** representing the knowledge contained in the text
4. **Visualize the graph** using PyVis, creating an interactive web-based visualization

The multi-provider architecture allows you to:
- **Compare results** across different LLM providers
- **Choose based on your needs**: speed, cost, privacy, or quality
- **Work offline** with local Ollama models
- **Scale usage** by switching providers based on workload

## Troubleshooting

### Common Issues

**"Provider connection failed"**
- Check your API keys in the `.env` file
- Verify internet connection for cloud providers
- For Ollama: ensure the service is running (`ollama serve`)

**"Model not found"**
- OpenAI: Check if you have access to the selected model
- Ollama: Pull the model first (`ollama pull model-name`)
- Custom: Verify the model name is supported by your provider

**"Rate limit exceeded"**
- OpenAI/Anthropic: Check your API usage and billing
- Try switching to a different provider temporarily
- For high-volume usage, consider using local Ollama models

**Ollama-specific issues**:
- **Service not running**: Start with `ollama serve`
- **Model not available**: List models with `ollama list`, pull with `ollama pull model-name`
- **Port conflicts**: Change Ollama port and update `OLLAMA_BASE_URL` in `.env`
- **Memory issues**: Use smaller models (7B instead of 70B parameters)

**Performance issues**:
- **Slow generation**: Try smaller models or switch providers
- **Out of memory**: Reduce text input size or use cloud providers
- **Connection timeouts**: Check network stability and provider status

### Getting Help

1. Check the application logs in the Streamlit interface
2. Verify your `.env` configuration matches the `.env.example` format
3. Test provider connections using the built-in connection validation
4. For Ollama issues, check the Ollama logs: `ollama logs`

## License

This project is licensed under the MIT License - a permissive open source license that allows for free use, modification, and distribution of the software.

For more details, see the [MIT License](https://opensource.org/licenses/MIT) documentation.
