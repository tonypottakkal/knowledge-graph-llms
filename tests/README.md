# Multi-LLM Knowledge Graph Generator - Test Suite

This directory contains comprehensive tests for the Multi-LLM Knowledge Graph Generator, validating multi-provider support, provider switching functionality, and system integration.

## Test Scripts

### Core Testing Scripts

- **`test_end_to_end.py`** - Comprehensive end-to-end testing of all providers
  - Tests provider configurations, connections, and knowledge graph generation
  - Validates consistent functionality across OpenAI, Ollama, and custom providers
  - Includes error handling and recovery flow testing

- **`test_provider_switching.py`** - Multi-provider switching functionality tests
  - Tests switching between providers during active sessions
  - Validates configuration persistence and session state management
  - Requires at least 2 working providers

- **`test_single_provider_switching.py`** - Single provider switching simulation
  - Simulates provider switching using one working provider
  - Tests model switching, configuration persistence, and session management
  - Validates error recovery and fallback mechanisms

- **`test_app_integration.py`** - Streamlit app integration testing
  - Tests UI integration with multi-LLM provider system
  - Validates provider selection, model selection, and connection testing UI
  - Tests graph generation integration and error handling in app context

### Legacy Testing

- **`test_factory.py`** - Basic factory functionality test (legacy)
  - Simple validation of LLM factory implementation
  - Provider configuration and connection testing

## Running Tests

### Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (optional, for full testing):
   ```bash
   # For OpenAI testing
   export OPENAI_API_KEY=your-openai-api-key
   
   # For custom provider testing
   export CUSTOM_LLM_API_KEY=your-custom-api-key
   export CUSTOM_LLM_BASE_URL=https://api.your-provider.com/v1
   
   # For Ollama (if not using defaults)
   export OLLAMA_BASE_URL=http://localhost:11434
   ```

3. For Ollama testing, ensure Ollama is running:
   ```bash
   ollama serve
   ollama pull llama2  # or any other model
   ```

### Running Individual Tests

```bash
# Comprehensive end-to-end testing
python tests/test_end_to_end.py

# Provider switching tests (requires 2+ working providers)
python tests/test_provider_switching.py

# Single provider switching simulation
python tests/test_single_provider_switching.py

# Streamlit app integration tests
python tests/test_app_integration.py

# Legacy factory tests
python tests/test_factory.py
```

### Running All Tests

```bash
# Run all tests in sequence
for test in tests/test_*.py; do
    echo "Running $test..."
    python "$test"
    echo "---"
done
```

## Test Results

Test results are automatically saved as JSON files in this directory:

- `test_results_YYYYMMDD_HHMMSS.json` - End-to-end test results
- `switching_test_results_TIMESTAMP.json` - Provider switching test results
- `switching_simulation_results_TIMESTAMP.json` - Single provider simulation results
- `app_integration_results_TIMESTAMP.json` - App integration test results

## Test Coverage

### Provider Testing
- ✅ OpenAI GPT models (requires API key and quota)
- ✅ Ollama local models (requires Ollama service)
- ✅ Custom external providers (requires configuration)

### Functionality Testing
- ✅ Provider configuration validation
- ✅ Connection testing and validation
- ✅ Knowledge graph generation consistency
- ✅ Error handling and recovery
- ✅ Session state management
- ✅ Provider switching functionality
- ✅ UI integration with Streamlit

### Performance Testing
- ✅ Response time measurement
- ✅ Resource usage validation
- ✅ Connection resilience testing

## Expected Results

With a properly configured environment:

- **Ollama Provider**: Should pass all tests if service is running locally
- **OpenAI Provider**: May fail due to API quota limits in test environments
- **Custom Provider**: Requires proper environment variable configuration

## Troubleshooting

### Common Issues

1. **"No working providers found"**
   - Ensure at least one provider is properly configured
   - Check environment variables and service availability

2. **OpenAI quota exceeded**
   - Expected in test environments with limited API quotas
   - Tests will skip OpenAI-specific functionality

3. **Ollama connection failed**
   - Ensure Ollama service is running: `ollama serve`
   - Check that models are available: `ollama list`

4. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check that you're running from the correct directory

### Getting Help

For detailed test results and analysis, see `TESTING_REPORT.md` in this directory.

## Test Development

When adding new tests:

1. Follow the existing naming convention: `test_*.py`
2. Include comprehensive error handling
3. Save results to JSON files with timestamps
4. Update this README with new test descriptions
5. Ensure tests can run independently

## Requirements Validation

These tests validate the following requirements:

- **4.1**: Consistent graph extraction across providers
- **4.2**: Preserved functionality when switching providers  
- **4.3**: Transparent handling of provider-specific formats
- **4.4**: Provider-specific error messages with guidance
- **5.5**: Standard functionality requirements for all providers