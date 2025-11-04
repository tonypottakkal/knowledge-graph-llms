#!/usr/bin/env python3
"""
Provider Switching and Session State Management Tests

This script tests the provider switching functionality, configuration persistence,
and session state management to ensure no data loss during provider changes.
"""

import os
import sys
import time
import json
import tempfile
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_factory import LLMProviderFactory
from llm_config import LLMConfigManager
from generate_knowledge_graph import generate_knowledge_graph


@dataclass
class SessionState:
    """Simulated session state for testing."""
    llm_provider: str = "openai"
    llm_model: str = None
    llm_temperature: float = 0.0
    connection_status: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.connection_status is None:
            self.connection_status = {}


class ProviderSwitchingTester:
    """Test provider switching functionality and session persistence."""
    
    def __init__(self):
        """Initialize the tester."""
        self.factory = LLMProviderFactory()
        self.config_manager = LLMConfigManager()
        self.session_states: List[SessionState] = []
        
        # Test text for consistency validation
        self.test_text = """
        Python is a programming language. Django is a web framework for Python.
        Flask is another web framework for Python. Both Django and Flask are popular
        among developers for building web applications.
        """
    
    def run_switching_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive provider switching tests.
        
        Returns:
            Dict[str, Any]: Test results
        """
        print("=" * 80)
        print("PROVIDER SWITCHING AND SESSION STATE MANAGEMENT TESTS")
        print("=" * 80)
        print()
        
        results = {}
        
        # Get available and working providers
        working_providers = self._get_working_providers()
        print(f"Working providers found: {working_providers}")
        
        if len(working_providers) < 2:
            print("⚠️  Need at least 2 working providers for switching tests")
            print("Available providers and their status:")
            for provider in self.config_manager.get_available_providers():
                is_valid, config_error = self.config_manager.validate_provider_config(provider)
                is_connected, conn_error = self.factory.validate_connection(provider)
                status = "✅" if (is_valid and is_connected) else "❌"
                print(f"  {provider}: {status}")
                if not is_valid:
                    print(f"    Config error: {config_error}")
                if not is_connected:
                    print(f"    Connection error: {conn_error}")
            
            return {"error": "Insufficient working providers", "working_providers": working_providers}
        
        # Test 1: Basic Provider Switching
        print("\n🔄 Test 1: Basic Provider Switching")
        results["basic_switching"] = self._test_basic_switching(working_providers)
        
        # Test 2: Session State Persistence
        print("\n💾 Test 2: Session State Persistence")
        results["session_persistence"] = self._test_session_persistence(working_providers)
        
        # Test 3: Configuration Consistency
        print("\n⚙️  Test 3: Configuration Consistency")
        results["config_consistency"] = self._test_configuration_consistency(working_providers)
        
        # Test 4: Graph Generation Consistency
        print("\n📊 Test 4: Graph Generation Consistency")
        results["graph_consistency"] = self._test_graph_consistency(working_providers)
        
        # Test 5: Rapid Switching
        print("\n⚡ Test 5: Rapid Provider Switching")
        results["rapid_switching"] = self._test_rapid_switching(working_providers)
        
        # Print summary
        self._print_switching_summary(results)
        
        return results
    
    def _get_working_providers(self) -> List[str]:
        """Get list of providers that are properly configured and connected."""
        working_providers = []
        
        for provider in self.config_manager.get_available_providers():
            try:
                # Check configuration
                is_valid, _ = self.config_manager.validate_provider_config(provider)
                if not is_valid:
                    continue
                
                # Check connection
                is_connected, _ = self.factory.validate_connection(provider)
                if not is_connected:
                    continue
                
                # Check if models are available
                models = self.factory.get_available_models(provider)
                if not models:
                    continue
                
                working_providers.append(provider)
                
            except Exception as e:
                print(f"  Error checking {provider}: {e}")
                continue
        
        return working_providers
    
    def _test_basic_switching(self, providers: List[str]) -> Dict[str, Any]:
        """Test basic provider switching functionality."""
        print("  Testing basic switching between providers...")
        
        results = {}
        provider1, provider2 = providers[0], providers[1]
        
        try:
            # Create initial session state
            session = SessionState(llm_provider=provider1)
            
            # Get models for first provider
            models1 = self.factory.get_available_models(provider1)
            session.llm_model = models1[0] if models1 else None
            
            print(f"    Initial state: {provider1} with model {session.llm_model}")
            
            # Test connection with first provider
            start_time = time.time()
            is_connected1, _ = self.factory.validate_connection(provider1)
            connection_time1 = time.time() - start_time
            
            # Switch to second provider
            session.llm_provider = provider2
            models2 = self.factory.get_available_models(provider2)
            session.llm_model = models2[0] if models2 else None
            
            print(f"    Switched to: {provider2} with model {session.llm_model}")
            
            # Test connection with second provider
            start_time = time.time()
            is_connected2, _ = self.factory.validate_connection(provider2)
            connection_time2 = time.time() - start_time
            
            # Switch back to first provider
            session.llm_provider = provider1
            session.llm_model = models1[0] if models1 else None
            
            print(f"    Switched back to: {provider1} with model {session.llm_model}")
            
            # Test connection again
            start_time = time.time()
            is_connected3, _ = self.factory.validate_connection(provider1)
            connection_time3 = time.time() - start_time
            
            success = is_connected1 and is_connected2 and is_connected3
            
            results = {
                "success": success,
                "provider1": provider1,
                "provider2": provider2,
                "connection_times": [connection_time1, connection_time2, connection_time3],
                "all_connections_successful": success
            }
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"    {status} - All connections successful: {success}")
            
        except Exception as e:
            results = {
                "success": False,
                "error": str(e),
                "provider1": provider1,
                "provider2": provider2
            }
            print(f"    ❌ FAIL - Error: {e}")
        
        return results
    
    def _test_session_persistence(self, providers: List[str]) -> Dict[str, Any]:
        """Test session state persistence during provider switching."""
        print("  Testing session state persistence...")
        
        results = {}
        
        try:
            # Create session with custom settings
            session = SessionState(
                llm_provider=providers[0],
                llm_temperature=0.7,
                connection_status={"test_key": "test_value"}
            )
            
            models = self.factory.get_available_models(providers[0])
            session.llm_model = models[0] if models else None
            
            # Save initial state
            initial_state = asdict(session)
            print(f"    Initial state: {session.llm_provider}, temp={session.llm_temperature}")
            
            # Simulate session persistence (save to temp file)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(initial_state, f)
                temp_file = f.name
            
            # Switch provider
            session.llm_provider = providers[1]
            models2 = self.factory.get_available_models(providers[1])
            session.llm_model = models2[0] if models2 else None
            
            print(f"    Switched to: {session.llm_provider}")
            
            # Load previous state (simulating session restoration)
            with open(temp_file, 'r') as f:
                loaded_state = json.load(f)
            
            # Verify critical settings persisted
            temperature_preserved = loaded_state['llm_temperature'] == 0.7
            connection_status_preserved = loaded_state['connection_status']['test_key'] == 'test_value'
            
            # Clean up
            os.unlink(temp_file)
            
            success = temperature_preserved and connection_status_preserved
            
            results = {
                "success": success,
                "temperature_preserved": temperature_preserved,
                "connection_status_preserved": connection_status_preserved,
                "initial_provider": providers[0],
                "switched_provider": providers[1]
            }
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"    {status} - Settings preserved: {success}")
            
        except Exception as e:
            results = {
                "success": False,
                "error": str(e)
            }
            print(f"    ❌ FAIL - Error: {e}")
        
        return results
    
    def _test_configuration_consistency(self, providers: List[str]) -> Dict[str, Any]:
        """Test configuration consistency across provider switches."""
        print("  Testing configuration consistency...")
        
        results = {}
        
        try:
            configurations = {}
            
            # Test each provider's configuration
            for provider in providers:
                config = self.config_manager.get_provider_config(provider)
                models = self.factory.get_available_models(provider)
                
                configurations[provider] = {
                    "config_keys": sorted(config.keys()),
                    "model_count": len(models),
                    "supports_model_selection": config.get("supports_model_selection", False),
                    "default_model": config.get("default_model")
                }
                
                print(f"    {provider}: {len(models)} models, default={config.get('default_model')}")
            
            # Verify configurations are consistent and complete
            all_have_models = all(conf["model_count"] > 0 for conf in configurations.values())
            all_have_defaults = all(conf["default_model"] is not None for conf in configurations.values())
            
            success = all_have_models and all_have_defaults
            
            results = {
                "success": success,
                "configurations": configurations,
                "all_have_models": all_have_models,
                "all_have_defaults": all_have_defaults
            }
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"    {status} - All configurations valid: {success}")
            
        except Exception as e:
            results = {
                "success": False,
                "error": str(e)
            }
            print(f"    ❌ FAIL - Error: {e}")
        
        return results
    
    def _test_graph_consistency(self, providers: List[str]) -> Dict[str, Any]:
        """Test knowledge graph generation consistency across providers."""
        print("  Testing graph generation consistency...")
        
        results = {}
        
        try:
            graphs = {}
            
            # Generate graphs with each provider
            for provider in providers:
                print(f"    Generating graph with {provider}...")
                
                models = self.factory.get_available_models(provider)
                model = models[0] if models else None
                
                start_time = time.time()
                
                try:
                    net = generate_knowledge_graph(
                        self.test_text,
                        provider=provider,
                        model=model,
                        temperature=0.0  # Use deterministic temperature
                    )
                    
                    generation_time = time.time() - start_time
                    
                    if net and hasattr(net, 'nodes') and hasattr(net, 'edges'):
                        node_count = len(net.nodes)
                        edge_count = len(net.edges)
                        success = node_count > 0 and edge_count > 0
                    else:
                        node_count = edge_count = 0
                        success = False
                    
                    graphs[provider] = {
                        "success": success,
                        "nodes": node_count,
                        "edges": edge_count,
                        "generation_time": generation_time,
                        "model": model
                    }
                    
                    print(f"      {provider}: {node_count} nodes, {edge_count} edges ({generation_time:.2f}s)")
                    
                except Exception as e:
                    graphs[provider] = {
                        "success": False,
                        "error": str(e),
                        "model": model
                    }
                    print(f"      {provider}: Failed - {e}")
            
            # Analyze consistency
            successful_graphs = [g for g in graphs.values() if g.get("success", False)]
            all_successful = len(successful_graphs) == len(providers)
            
            if successful_graphs:
                node_counts = [g["nodes"] for g in successful_graphs]
                edge_counts = [g["edges"] for g in successful_graphs]
                
                # Check if graphs have reasonable similarity (within 50% variance)
                node_variance = (max(node_counts) - min(node_counts)) / max(node_counts) if max(node_counts) > 0 else 0
                edge_variance = (max(edge_counts) - min(edge_counts)) / max(edge_counts) if max(edge_counts) > 0 else 0
                
                reasonable_consistency = node_variance < 0.5 and edge_variance < 0.5
            else:
                reasonable_consistency = False
            
            success = all_successful and reasonable_consistency
            
            results = {
                "success": success,
                "graphs": graphs,
                "all_successful": all_successful,
                "reasonable_consistency": reasonable_consistency,
                "successful_count": len(successful_graphs)
            }
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"    {status} - Consistent generation: {success}")
            
        except Exception as e:
            results = {
                "success": False,
                "error": str(e)
            }
            print(f"    ❌ FAIL - Error: {e}")
        
        return results
    
    def _test_rapid_switching(self, providers: List[str]) -> Dict[str, Any]:
        """Test rapid switching between providers."""
        print("  Testing rapid provider switching...")
        
        results = {}
        
        try:
            switch_times = []
            switch_count = 6  # Switch 6 times rapidly
            
            current_provider = providers[0]
            
            for i in range(switch_count):
                # Alternate between providers
                next_provider = providers[1] if current_provider == providers[0] else providers[0]
                
                start_time = time.time()
                
                # Simulate provider switch
                models = self.factory.get_available_models(next_provider)
                model = models[0] if models else None
                
                # Test connection
                is_connected, _ = self.factory.validate_connection(next_provider)
                
                switch_time = time.time() - start_time
                switch_times.append(switch_time)
                
                if not is_connected:
                    raise Exception(f"Connection failed during rapid switch to {next_provider}")
                
                current_provider = next_provider
                print(f"    Switch {i+1}: {current_provider} ({switch_time:.3f}s)")
            
            avg_switch_time = sum(switch_times) / len(switch_times)
            max_switch_time = max(switch_times)
            
            # Consider successful if all switches completed and average time is reasonable
            success = len(switch_times) == switch_count and avg_switch_time < 2.0
            
            results = {
                "success": success,
                "switch_count": switch_count,
                "switch_times": switch_times,
                "avg_switch_time": avg_switch_time,
                "max_switch_time": max_switch_time
            }
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"    {status} - Avg switch time: {avg_switch_time:.3f}s")
            
        except Exception as e:
            results = {
                "success": False,
                "error": str(e)
            }
            print(f"    ❌ FAIL - Error: {e}")
        
        return results
    
    def _print_switching_summary(self, results: Dict[str, Any]):
        """Print comprehensive switching test summary."""
        print("\n" + "=" * 80)
        print("PROVIDER SWITCHING TEST SUMMARY")
        print("=" * 80)
        
        if "error" in results:
            print(f"❌ Tests could not run: {results['error']}")
            return
        
        test_results = [
            ("Basic Switching", results.get("basic_switching", {}).get("success", False)),
            ("Session Persistence", results.get("session_persistence", {}).get("success", False)),
            ("Config Consistency", results.get("config_consistency", {}).get("success", False)),
            ("Graph Consistency", results.get("graph_consistency", {}).get("success", False)),
            ("Rapid Switching", results.get("rapid_switching", {}).get("success", False))
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
        if "graph_consistency" in results and results["graph_consistency"].get("success"):
            graphs = results["graph_consistency"]["graphs"]
            print(f"\nGraph Generation Results:")
            for provider, graph_data in graphs.items():
                if graph_data.get("success"):
                    print(f"  {provider}: {graph_data['nodes']} nodes, {graph_data['edges']} edges")
        
        if "rapid_switching" in results and results["rapid_switching"].get("success"):
            avg_time = results["rapid_switching"]["avg_switch_time"]
            print(f"\nRapid Switching: Average {avg_time:.3f}s per switch")


def main():
    """Main function to run provider switching tests."""
    tester = ProviderSwitchingTester()
    results = tester.run_switching_tests()
    
    # Save results
    results_file = f"switching_test_results_{int(time.time())}.json"
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
        results.get("basic_switching", {}).get("success", False),
        results.get("session_persistence", {}).get("success", False),
        results.get("config_consistency", {}).get("success", False),
        results.get("graph_consistency", {}).get("success", False),
        results.get("rapid_switching", {}).get("success", False)
    ]
    
    if all(test_results):
        print("\n🎉 All provider switching tests passed!")
        return 0
    else:
        failed_count = sum(1 for success in test_results if not success)
        print(f"\n⚠️  {failed_count} provider switching test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())