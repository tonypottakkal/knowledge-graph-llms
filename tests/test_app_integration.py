#!/usr/bin/env python3
"""
Streamlit App Integration Test

This script tests the integration between the Streamlit app and the multi-LLM
provider system to validate provider switching and session state management.
"""

import os
import sys
import time
import json
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_factory import LLMProviderFactory
from llm_config import LLMConfigManager
from generate_knowledge_graph import generate_knowledge_graph


class StreamlitSessionState:
    """Mock Streamlit session state for testing."""
    
    def __init__(self):
        self.data = {
            'llm_provider': 'openai',
            'llm_model': None,
            'llm_temperature': 0.0,
            'connection_status': {}
        }
    
    def __getitem__(self, key):
        return self.data.get(key)
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __contains__(self, key):
        return key in self.data
    
    def get(self, key, default=None):
        return self.data.get(key, default)


class AppIntegrationTester:
    """Test Streamlit app integration with multi-LLM providers."""
    
    def __init__(self):
        """Initialize the tester."""
        self.factory = LLMProviderFactory()
        self.config_manager = LLMConfigManager()
        self.session_state = StreamlitSessionState()
        
        # Test text
        self.test_text = """
        Artificial Intelligence includes Machine Learning. Machine Learning includes 
        Deep Learning. Python is used for AI development. TensorFlow is a framework 
        for Machine Learning.
        """
    
    def run_app_integration_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive app integration tests.
        
        Returns:
            Dict[str, Any]: Test results
        """
        print("=" * 80)
        print("STREAMLIT APP INTEGRATION TESTS")
        print("=" * 80)
        print()
        
        results = {}
        
        # Find working provider
        working_provider = self._find_working_provider()
        if not working_provider:
            return {"error": "No working providers found for integration testing"}
        
        print(f"Using working provider: {working_provider}")
        
        # Test 1: Provider Selection UI Logic
        print("\n🎛️  Test 1: Provider Selection UI Logic")
        results["provider_selection"] = self._test_provider_selection_ui(working_provider)
        
        # Test 2: Model Selection UI Logic
        print("\n🤖 Test 2: Model Selection UI Logic")
        results["model_selection"] = self._test_model_selection_ui(working_provider)
        
        # Test 3: Connection Testing UI Logic
        print("\n🔍 Test 3: Connection Testing UI Logic")
        results["connection_testing"] = self._test_connection_testing_ui(working_provider)
        
        # Test 4: Graph Generation Integration
        print("\n📊 Test 4: Graph Generation Integration")
        results["graph_generation"] = self._test_graph_generation_integration(working_provider)
        
        # Test 5: Error Handling Integration
        print("\n⚠️  Test 5: Error Handling Integration")
        results["error_handling"] = self._test_error_handling_integration(working_provider)
        
        # Test 6: Session State Persistence
        print("\n💾 Test 6: Session State Persistence")
        results["session_persistence"] = self._test_session_state_persistence(working_provider)
        
        # Print summary
        self._print_integration_summary(results, working_provider)
        
        return results
    
    def _find_working_provider(self) -> Optional[str]:
        """Find a working provider for testing."""
        for provider in self.config_manager.get_available_providers():
            try:
                is_valid, _ = self.config_manager.validate_provider_config(provider)
                if not is_valid:
                    continue
                
                is_connected, _ = self.factory.validate_connection(provider)
                if not is_connected:
                    continue
                
                models = self.factory.get_available_models(provider)
                if not models:
                    continue
                
                return provider
                
            except Exception:
                continue
        
        return None
    
    def _test_provider_selection_ui(self, working_provider: str) -> Dict[str, Any]:
        """Test provider selection UI logic."""
        print("  Testing provider selection UI logic...")
        
        try:
            # Test getting available providers (like in app.py)
            available_providers = self.config_manager.get_available_providers()
            provider_display_names = self.config_manager.get_provider_display_names()
            
            # Simulate provider selection
            self.session_state['llm_provider'] = working_provider
            
            # Test provider configuration retrieval
            provider_config = self.config_manager.get_provider_config(working_provider)
            
            # Simulate UI state update
            if working_provider != self.session_state.get('llm_provider'):
                self.session_state['llm_model'] = None
                self.session_state['connection_status'] = {}
            
            success = (
                len(available_providers) > 0 and
                working_provider in provider_display_names and
                provider_config is not None and
                self.session_state['llm_provider'] == working_provider
            )
            
            print(f"    ✅ Provider selection logic working")
            print(f"    Available providers: {len(available_providers)}")
            print(f"    Selected provider: {working_provider}")
            
            return {
                "success": success,
                "available_providers": len(available_providers),
                "selected_provider": working_provider,
                "provider_config_keys": list(provider_config.keys()) if provider_config else []
            }
            
        except Exception as e:
            print(f"    ❌ Provider selection failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _test_model_selection_ui(self, working_provider: str) -> Dict[str, Any]:
        """Test model selection UI logic."""
        print("  Testing model selection UI logic...")
        
        try:
            # Test model retrieval (like in app.py)
            available_models = self.factory.get_available_models(working_provider)
            
            if not available_models:
                print("    ⚠️  No models available for testing")
                return {"success": False, "error": "No models available"}
            
            # Simulate model selection
            selected_model = available_models[0]
            self.session_state['llm_model'] = selected_model
            
            # Test model switching
            if len(available_models) > 1:
                # Switch to second model
                second_model = available_models[1]
                self.session_state['llm_model'] = second_model
                
                # Switch back to first model
                self.session_state['llm_model'] = selected_model
            
            success = (
                len(available_models) > 0 and
                self.session_state['llm_model'] == selected_model
            )
            
            print(f"    ✅ Model selection logic working")
            print(f"    Available models: {len(available_models)}")
            print(f"    Selected model: {selected_model}")
            
            return {
                "success": success,
                "available_models": len(available_models),
                "selected_model": selected_model,
                "models_list": available_models[:3]  # First 3 models
            }
            
        except Exception as e:
            print(f"    ❌ Model selection failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _test_connection_testing_ui(self, working_provider: str) -> Dict[str, Any]:
        """Test connection testing UI logic."""
        print("  Testing connection testing UI logic...")
        
        try:
            # Simulate connection test button click (like in app.py)
            connection_key = f"{working_provider}_{self.session_state.get('llm_model', 'default')}"
            
            # Test configuration validation
            is_valid, error_msg = self.config_manager.validate_provider_config(working_provider)
            
            if not is_valid:
                # Simulate error state
                self.session_state['connection_status'][connection_key] = {
                    'status': 'error',
                    'message': error_msg
                }
                connection_success = False
            else:
                # Test connection
                is_connected, conn_error = self.factory.validate_connection(working_provider)
                
                if is_connected:
                    self.session_state['connection_status'][connection_key] = {
                        'status': 'success',
                        'message': f"Successfully connected to {working_provider}"
                    }
                    connection_success = True
                else:
                    self.session_state['connection_status'][connection_key] = {
                        'status': 'error',
                        'message': conn_error or "Connection failed"
                    }
                    connection_success = False
            
            # Test status retrieval
            status_info = self.session_state['connection_status'].get(connection_key)
            
            success = (
                status_info is not None and
                'status' in status_info and
                'message' in status_info
            )
            
            status_emoji = "✅" if connection_success else "❌"
            print(f"    {status_emoji} Connection test logic working")
            print(f"    Connection status: {status_info['status'] if status_info else 'None'}")
            
            return {
                "success": success,
                "connection_successful": connection_success,
                "status_info": status_info,
                "connection_key": connection_key
            }
            
        except Exception as e:
            print(f"    ❌ Connection testing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _test_graph_generation_integration(self, working_provider: str) -> Dict[str, Any]:
        """Test graph generation integration with app logic."""
        print("  Testing graph generation integration...")
        
        try:
            # Simulate app's graph generation logic
            
            # 1. Check provider configuration (like in app.py)
            is_valid, error_msg = self.config_manager.validate_provider_config(working_provider)
            
            if not is_valid:
                print(f"    ⚠️  Configuration invalid: {error_msg}")
                return {
                    "success": False,
                    "error": f"Configuration invalid: {error_msg}",
                    "stage": "configuration_check"
                }
            
            # 2. Generate knowledge graph (like in app.py)
            models = self.factory.get_available_models(working_provider)
            model = models[0] if models else None
            
            start_time = time.time()
            
            net = generate_knowledge_graph(
                self.test_text,
                provider=working_provider,
                model=model,
                temperature=self.session_state.get('llm_temperature', 0.0)
            )
            
            generation_time = time.time() - start_time
            
            # 3. Validate graph output (like in app.py)
            if net and hasattr(net, 'nodes') and hasattr(net, 'edges'):
                node_count = len(net.nodes)
                edge_count = len(net.edges)
                success = node_count > 0 and edge_count > 0
            else:
                node_count = edge_count = 0
                success = False
            
            print(f"    ✅ Graph generation integration working")
            print(f"    Generated: {node_count} nodes, {edge_count} edges")
            print(f"    Generation time: {generation_time:.2f}s")
            
            return {
                "success": success,
                "provider": working_provider,
                "model": model,
                "nodes": node_count,
                "edges": edge_count,
                "generation_time": generation_time
            }
            
        except Exception as e:
            print(f"    ❌ Graph generation integration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _test_error_handling_integration(self, working_provider: str) -> Dict[str, Any]:
        """Test error handling integration with app logic."""
        print("  Testing error handling integration...")
        
        try:
            results = {}
            
            # Test 1: Invalid provider error handling
            try:
                generate_knowledge_graph(
                    self.test_text,
                    provider="invalid_provider"
                )
                results["invalid_provider"] = {"handled": False, "error": "Should have failed"}
            except Exception as e:
                # This should be caught and handled gracefully
                error_message = str(e)
                results["invalid_provider"] = {
                    "handled": True,
                    "error_message": error_message,
                    "user_friendly": "invalid_provider" in error_message.lower()
                }
                print("    ✅ Invalid provider error handled")
            
            # Test 2: Configuration error handling
            # Simulate missing environment variable
            original_env = os.environ.get('CUSTOM_LLM_API_KEY')
            if 'CUSTOM_LLM_API_KEY' in os.environ:
                del os.environ['CUSTOM_LLM_API_KEY']
            
            try:
                is_valid, error_msg = self.config_manager.validate_provider_config('custom')
                results["config_error"] = {
                    "handled": not is_valid,
                    "error_message": error_msg,
                    "user_friendly": "environment variable" in error_msg.lower() if error_msg else False
                }
                
                status = "✅" if not is_valid else "❌"
                print(f"    {status} Configuration error handled")
                
            finally:
                # Restore environment variable
                if original_env:
                    os.environ['CUSTOM_LLM_API_KEY'] = original_env
            
            # Test 3: Connection error simulation
            # This would normally test network failures, but we'll test with invalid model
            try:
                # Use working provider but invalid model
                net = generate_knowledge_graph(
                    self.test_text,
                    provider=working_provider,
                    model="definitely_invalid_model_name_12345"
                )
                results["connection_error"] = {"handled": False, "error": "Should have failed"}
            except Exception as e:
                error_message = str(e)
                results["connection_error"] = {
                    "handled": True,
                    "error_message": error_message,
                    "user_friendly": len(error_message) > 0
                }
                print("    ✅ Connection error handled")
            
            # Overall success
            all_handled = all(
                result.get("handled", False) 
                for result in results.values()
            )
            
            return {
                "success": all_handled,
                "results": results,
                "error_types_tested": len(results)
            }
            
        except Exception as e:
            print(f"    ❌ Error handling integration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _test_session_state_persistence(self, working_provider: str) -> Dict[str, Any]:
        """Test session state persistence logic."""
        print("  Testing session state persistence...")
        
        try:
            # Set up initial session state
            models = self.factory.get_available_models(working_provider)
            initial_model = models[0] if models else None
            
            self.session_state['llm_provider'] = working_provider
            self.session_state['llm_model'] = initial_model
            self.session_state['llm_temperature'] = 0.3
            self.session_state['connection_status'] = {
                f"{working_provider}_{initial_model}": {
                    'status': 'success',
                    'message': 'Connected'
                }
            }
            
            # Save initial state
            initial_state = dict(self.session_state.data)
            
            # Simulate operations that should preserve state
            operations = [
                "provider_info_lookup",
                "model_list_refresh", 
                "temperature_adjustment",
                "connection_retest"
            ]
            
            state_preserved_count = 0
            
            for operation in operations:
                # Perform operation
                if operation == "provider_info_lookup":
                    # Simulate looking up provider info
                    provider_config = self.config_manager.get_provider_config(working_provider)
                    
                elif operation == "model_list_refresh":
                    # Simulate refreshing model list
                    available_models = self.factory.get_available_models(working_provider)
                    
                elif operation == "temperature_adjustment":
                    # Simulate temperature change
                    self.session_state['llm_temperature'] = 0.7
                    
                elif operation == "connection_retest":
                    # Simulate connection retest
                    is_connected, _ = self.factory.validate_connection(working_provider)
                
                # Check if critical state is preserved
                critical_preserved = (
                    self.session_state['llm_provider'] == initial_state['llm_provider'] and
                    self.session_state['llm_model'] == initial_state['llm_model']
                )
                
                if critical_preserved:
                    state_preserved_count += 1
                
                print(f"    State after {operation}: {'✅' if critical_preserved else '❌'}")
            
            success = state_preserved_count == len(operations)
            
            return {
                "success": success,
                "operations_tested": len(operations),
                "state_preserved_count": state_preserved_count,
                "final_state": dict(self.session_state.data)
            }
            
        except Exception as e:
            print(f"    ❌ Session state persistence failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _print_integration_summary(self, results: Dict[str, Any], provider: str):
        """Print comprehensive integration test summary."""
        print("\n" + "=" * 80)
        print("STREAMLIT APP INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        if "error" in results:
            print(f"❌ Tests could not run: {results['error']}")
            return
        
        print(f"Provider tested: {provider}")
        print()
        
        test_results = [
            ("Provider Selection UI", results.get("provider_selection", {}).get("success", False)),
            ("Model Selection UI", results.get("model_selection", {}).get("success", False)),
            ("Connection Testing UI", results.get("connection_testing", {}).get("success", False)),
            ("Graph Generation Integration", results.get("graph_generation", {}).get("success", False)),
            ("Error Handling Integration", results.get("error_handling", {}).get("success", False)),
            ("Session State Persistence", results.get("session_persistence", {}).get("success", False))
        ]
        
        passed_tests = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        # Additional details
        if "graph_generation" in results and results["graph_generation"].get("success"):
            graph_data = results["graph_generation"]
            print(f"\nGraph Generation: {graph_data['nodes']} nodes, {graph_data['edges']} edges")
            print(f"Generation Time: {graph_data['generation_time']:.2f}s")
        
        if "model_selection" in results and results["model_selection"].get("success"):
            model_data = results["model_selection"]
            print(f"Model Selection: {model_data['available_models']} models available")
        
        if "error_handling" in results and results["error_handling"].get("success"):
            error_data = results["error_handling"]
            print(f"Error Handling: {error_data['error_types_tested']} error types tested")


def main():
    """Main function to run app integration tests."""
    tester = AppIntegrationTester()
    results = tester.run_app_integration_tests()
    
    # Save results
    results_file = f"app_integration_results_{int(time.time())}.json"
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {results_file}")
    except Exception as e:
        print(f"\nWarning: Could not save results file: {e}")
    
    # Return exit code based on results
    if "error" in results:
        return 1
    
    test_results = [
        results.get("provider_selection", {}).get("success", False),
        results.get("model_selection", {}).get("success", False),
        results.get("connection_testing", {}).get("success", False),
        results.get("graph_generation", {}).get("success", False),
        results.get("error_handling", {}).get("success", False),
        results.get("session_persistence", {}).get("success", False)
    ]
    
    if all(test_results):
        print("\n🎉 All app integration tests passed!")
        return 0
    else:
        failed_count = sum(1 for success in test_results if not success)
        print(f"\n⚠️  {failed_count} app integration test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())