#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing for Multi-LLM Knowledge Graph Generator

This script conducts thorough testing of all supported LLM providers,
validates consistent functionality, and tests provider switching capabilities.
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_factory import LLMProviderFactory
from llm_config import LLMConfigManager
from generate_knowledge_graph import generate_knowledge_graph, extract_graph_data


@dataclass
class TestResult:
    """Test result data structure."""
    provider: str
    model: str
    test_name: str
    success: bool
    duration: float
    error_message: str = ""
    graph_nodes: int = 0
    graph_edges: int = 0
    additional_data: Dict[str, Any] = None


class EndToEndTester:
    """Comprehensive end-to-end testing for multi-LLM support."""
    
    def __init__(self):
        """Initialize the tester with factory and config manager."""
        self.factory = LLMProviderFactory()
        self.config_manager = LLMConfigManager()
        self.test_results: List[TestResult] = []
        
        # Test text for knowledge graph generation
        self.test_text = """
        Artificial Intelligence (AI) is a branch of computer science that aims to create 
        intelligent machines. Machine Learning is a subset of AI that enables computers 
        to learn without being explicitly programmed. Deep Learning is a subset of 
        Machine Learning that uses neural networks with multiple layers. Natural Language 
        Processing (NLP) is another branch of AI that helps computers understand human language.
        
        Python is a popular programming language used in AI development. TensorFlow and 
        PyTorch are popular frameworks for building machine learning models. OpenAI 
        develops advanced AI systems like GPT models. Google created TensorFlow and 
        has developed various AI technologies.
        """
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive end-to-end tests for all providers.
        
        Returns:
            Dict[str, Any]: Complete test results summary
        """
        print("=" * 80)
        print("MULTI-LLM KNOWLEDGE GRAPH GENERATOR - END-TO-END TESTING")
        print("=" * 80)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test 1: Provider Configuration Validation
        print("🔧 Testing provider configurations...")
        config_results = self._test_provider_configurations()
        
        # Test 2: Connection Validation
        print("\n🔗 Testing provider connections...")
        connection_results = self._test_provider_connections()
        
        # Test 3: Knowledge Graph Generation
        print("\n📊 Testing knowledge graph generation...")
        generation_results = self._test_knowledge_graph_generation()
        
        # Test 4: Provider Switching
        print("\n🔄 Testing provider switching...")
        switching_results = self._test_provider_switching()
        
        # Test 5: Error Handling
        print("\n⚠️  Testing error handling...")
        error_handling_results = self._test_error_handling()
        
        # Compile final results
        final_results = {
            "test_timestamp": datetime.now().isoformat(),
            "configuration_tests": config_results,
            "connection_tests": connection_results,
            "generation_tests": generation_results,
            "switching_tests": switching_results,
            "error_handling_tests": error_handling_results,
            "summary": self._generate_test_summary()
        }
        
        # Print summary
        self._print_test_summary(final_results)
        
        return final_results
    
    def _test_provider_configurations(self) -> Dict[str, Any]:
        """Test provider configuration validation."""
        results = {}
        available_providers = self.config_manager.get_available_providers()
        
        for provider in available_providers:
            print(f"  Testing {provider} configuration...")
            start_time = time.time()
            
            try:
                # Test configuration validation
                is_valid, error_msg = self.config_manager.validate_provider_config(provider)
                
                # Get provider config
                if is_valid:
                    config = self.config_manager.get_provider_config(provider)
                    required_vars = self.config_manager.get_required_env_vars(provider)
                else:
                    config = None
                    required_vars = []
                
                duration = time.time() - start_time
                
                result = TestResult(
                    provider=provider,
                    model="N/A",
                    test_name="configuration_validation",
                    success=is_valid,
                    duration=duration,
                    error_message=error_msg or "",
                    additional_data={
                        "config_keys": list(config.keys()) if config else [],
                        "required_env_vars": required_vars
                    }
                )
                
                self.test_results.append(result)
                results[provider] = {
                    "valid": is_valid,
                    "error": error_msg,
                    "duration": duration,
                    "required_vars": required_vars
                }
                
                status = "✅ PASS" if is_valid else "❌ FAIL"
                print(f"    {status} - {duration:.2f}s")
                if not is_valid:
                    print(f"    Error: {error_msg}")
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                
                result = TestResult(
                    provider=provider,
                    model="N/A",
                    test_name="configuration_validation",
                    success=False,
                    duration=duration,
                    error_message=error_msg
                )
                
                self.test_results.append(result)
                results[provider] = {
                    "valid": False,
                    "error": error_msg,
                    "duration": duration
                }
                
                print(f"    ❌ FAIL - {duration:.2f}s")
                print(f"    Exception: {error_msg}")
        
        return results
    
    def _test_provider_connections(self) -> Dict[str, Any]:
        """Test provider connection validation."""
        results = {}
        available_providers = self.config_manager.get_available_providers()
        
        for provider in available_providers:
            print(f"  Testing {provider} connection...")
            start_time = time.time()
            
            try:
                # First check if configuration is valid
                is_valid, config_error = self.config_manager.validate_provider_config(provider)
                if not is_valid:
                    duration = time.time() - start_time
                    results[provider] = {
                        "connected": False,
                        "error": f"Configuration invalid: {config_error}",
                        "duration": duration
                    }
                    print(f"    ⏭️  SKIP - Configuration invalid")
                    continue
                
                # Test connection
                is_connected, conn_error = self.factory.validate_connection(provider)
                duration = time.time() - start_time
                
                result = TestResult(
                    provider=provider,
                    model="N/A",
                    test_name="connection_validation",
                    success=is_connected,
                    duration=duration,
                    error_message=conn_error or ""
                )
                
                self.test_results.append(result)
                results[provider] = {
                    "connected": is_connected,
                    "error": conn_error,
                    "duration": duration
                }
                
                status = "✅ PASS" if is_connected else "❌ FAIL"
                print(f"    {status} - {duration:.2f}s")
                if not is_connected:
                    print(f"    Error: {conn_error}")
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                
                result = TestResult(
                    provider=provider,
                    model="N/A",
                    test_name="connection_validation",
                    success=False,
                    duration=duration,
                    error_message=error_msg
                )
                
                self.test_results.append(result)
                results[provider] = {
                    "connected": False,
                    "error": error_msg,
                    "duration": duration
                }
                
                print(f"    ❌ FAIL - {duration:.2f}s")
                print(f"    Exception: {error_msg}")
        
        return results
    
    def _test_knowledge_graph_generation(self) -> Dict[str, Any]:
        """Test knowledge graph generation with each provider."""
        results = {}
        available_providers = self.config_manager.get_available_providers()
        
        for provider in available_providers:
            print(f"  Testing {provider} knowledge graph generation...")
            
            # Check if provider is properly configured and connected
            is_valid, _ = self.config_manager.validate_provider_config(provider)
            if not is_valid:
                print(f"    ⏭️  SKIP - Configuration invalid")
                results[provider] = {"skipped": True, "reason": "Configuration invalid"}
                continue
            
            is_connected, _ = self.factory.validate_connection(provider)
            if not is_connected:
                print(f"    ⏭️  SKIP - Connection failed")
                results[provider] = {"skipped": True, "reason": "Connection failed"}
                continue
            
            # Get available models for this provider
            available_models = self.factory.get_available_models(provider)
            if not available_models:
                print(f"    ⏭️  SKIP - No models available")
                results[provider] = {"skipped": True, "reason": "No models available"}
                continue
            
            # Test with the first available model
            model = available_models[0]
            start_time = time.time()
            
            try:
                # Generate knowledge graph
                net = generate_knowledge_graph(
                    self.test_text,
                    provider=provider,
                    model=model,
                    temperature=0.0
                )
                
                duration = time.time() - start_time
                
                # Analyze the generated graph
                if net and hasattr(net, 'nodes') and hasattr(net, 'edges'):
                    node_count = len(net.nodes)
                    edge_count = len(net.edges)
                    success = node_count > 0 and edge_count > 0
                else:
                    node_count = 0
                    edge_count = 0
                    success = False
                
                result = TestResult(
                    provider=provider,
                    model=model,
                    test_name="knowledge_graph_generation",
                    success=success,
                    duration=duration,
                    graph_nodes=node_count,
                    graph_edges=edge_count,
                    additional_data={
                        "text_length": len(self.test_text),
                        "temperature": 0.0
                    }
                )
                
                self.test_results.append(result)
                results[provider] = {
                    "success": success,
                    "model": model,
                    "duration": duration,
                    "nodes": node_count,
                    "edges": edge_count
                }
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"    {status} - {duration:.2f}s (Nodes: {node_count}, Edges: {edge_count})")
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                
                result = TestResult(
                    provider=provider,
                    model=model,
                    test_name="knowledge_graph_generation",
                    success=False,
                    duration=duration,
                    error_message=error_msg
                )
                
                self.test_results.append(result)
                results[provider] = {
                    "success": False,
                    "model": model,
                    "duration": duration,
                    "error": error_msg
                }
                
                print(f"    ❌ FAIL - {duration:.2f}s")
                print(f"    Error: {error_msg}")
        
        return results
    
    def _test_provider_switching(self) -> Dict[str, Any]:
        """Test switching between providers during active sessions."""
        print("  Testing provider switching scenarios...")
        results = {}
        
        # Get providers that are properly configured and connected
        working_providers = []
        for provider in self.config_manager.get_available_providers():
            is_valid, _ = self.config_manager.validate_provider_config(provider)
            is_connected, _ = self.factory.validate_connection(provider)
            if is_valid and is_connected:
                working_providers.append(provider)
        
        if len(working_providers) < 2:
            print("    ⏭️  SKIP - Need at least 2 working providers for switching test")
            return {"skipped": True, "reason": "Insufficient working providers"}
        
        # Test switching between first two working providers
        provider1, provider2 = working_providers[0], working_providers[1]
        print(f"    Testing switch: {provider1} → {provider2}")
        
        start_time = time.time()
        
        try:
            # Generate graph with first provider
            models1 = self.factory.get_available_models(provider1)
            net1 = generate_knowledge_graph(
                self.test_text,
                provider=provider1,
                model=models1[0] if models1 else None,
                temperature=0.0
            )
            
            # Switch to second provider and generate graph
            models2 = self.factory.get_available_models(provider2)
            net2 = generate_knowledge_graph(
                self.test_text,
                provider=provider2,
                model=models2[0] if models2 else None,
                temperature=0.0
            )
            
            duration = time.time() - start_time
            
            # Validate both graphs were generated successfully
            success1 = net1 and hasattr(net1, 'nodes') and len(net1.nodes) > 0
            success2 = net2 and hasattr(net2, 'nodes') and len(net2.nodes) > 0
            overall_success = success1 and success2
            
            result = TestResult(
                provider=f"{provider1}→{provider2}",
                model=f"{models1[0] if models1 else 'default'}→{models2[0] if models2 else 'default'}",
                test_name="provider_switching",
                success=overall_success,
                duration=duration,
                additional_data={
                    "provider1_nodes": len(net1.nodes) if success1 else 0,
                    "provider2_nodes": len(net2.nodes) if success2 else 0,
                    "provider1_edges": len(net1.edges) if success1 else 0,
                    "provider2_edges": len(net2.edges) if success2 else 0
                }
            )
            
            self.test_results.append(result)
            results["switching_test"] = {
                "success": overall_success,
                "provider1": provider1,
                "provider2": provider2,
                "duration": duration,
                "provider1_success": success1,
                "provider2_success": success2
            }
            
            status = "✅ PASS" if overall_success else "❌ FAIL"
            print(f"    {status} - {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            result = TestResult(
                provider=f"{provider1}→{provider2}",
                model="N/A",
                test_name="provider_switching",
                success=False,
                duration=duration,
                error_message=error_msg
            )
            
            self.test_results.append(result)
            results["switching_test"] = {
                "success": False,
                "provider1": provider1,
                "provider2": provider2,
                "duration": duration,
                "error": error_msg
            }
            
            print(f"    ❌ FAIL - {duration:.2f}s")
            print(f"    Error: {error_msg}")
        
        return results
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and recovery scenarios."""
        results = {}
        
        # Test 1: Invalid provider
        print("    Testing invalid provider handling...")
        start_time = time.time()
        try:
            generate_knowledge_graph(self.test_text, provider="invalid_provider")
            results["invalid_provider"] = {"success": False, "error": "Should have failed"}
        except Exception as e:
            duration = time.time() - start_time
            results["invalid_provider"] = {
                "success": True,
                "error_caught": str(e),
                "duration": duration
            }
            print(f"      ✅ Correctly caught invalid provider error - {duration:.2f}s")
        
        # Test 2: Invalid model (for providers that support model selection)
        for provider in self.config_manager.get_available_providers():
            is_valid, _ = self.config_manager.validate_provider_config(provider)
            if not is_valid:
                continue
                
            print(f"    Testing invalid model for {provider}...")
            start_time = time.time()
            try:
                generate_knowledge_graph(
                    self.test_text,
                    provider=provider,
                    model="invalid_model_name_12345"
                )
                results[f"{provider}_invalid_model"] = {
                    "success": False,
                    "error": "Should have failed"
                }
            except Exception as e:
                duration = time.time() - start_time
                results[f"{provider}_invalid_model"] = {
                    "success": True,
                    "error_caught": str(e),
                    "duration": duration
                }
                print(f"      ✅ Correctly caught invalid model error - {duration:.2f}s")
            break  # Only test one provider to save time
        
        return results
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests
        
        # Group results by test type
        test_types = {}
        for result in self.test_results:
            test_type = result.test_name
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "passed": 0, "failed": 0}
            
            test_types[test_type]["total"] += 1
            if result.success:
                test_types[test_type]["passed"] += 1
            else:
                test_types[test_type]["failed"] += 1
        
        # Calculate average durations
        avg_durations = {}
        for test_type in test_types:
            durations = [r.duration for r in self.test_results if r.test_name == test_type]
            avg_durations[test_type] = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "test_types": test_types,
            "average_durations": avg_durations,
            "total_duration": sum(r.duration for r in self.test_results)
        }
    
    def _print_test_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        summary = results["summary"]
        
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        print("\nTest Type Breakdown:")
        for test_type, stats in summary["test_types"].items():
            avg_duration = summary["average_durations"][test_type]
            print(f"  {test_type}: {stats['passed']}/{stats['total']} passed "
                  f"(avg: {avg_duration:.2f}s)")
        
        print("\nProvider Status:")
        for provider in self.config_manager.get_available_providers():
            config_valid = results["configuration_tests"].get(provider, {}).get("valid", False)
            connected = results["connection_tests"].get(provider, {}).get("connected", False)
            generation_success = results["generation_tests"].get(provider, {}).get("success", False)
            
            status_icons = []
            if config_valid:
                status_icons.append("🔧")
            if connected:
                status_icons.append("🔗")
            if generation_success:
                status_icons.append("📊")
            
            status = "".join(status_icons) if status_icons else "❌"
            print(f"  {provider}: {status}")
        
        print("\nLegend: 🔧 = Config Valid, 🔗 = Connected, 📊 = Graph Generation")
        
        # Save detailed results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nDetailed results saved to: {results_file}")
        except Exception as e:
            print(f"\nWarning: Could not save results file: {e}")


def main():
    """Main function to run end-to-end tests."""
    tester = EndToEndTester()
    results = tester.run_all_tests()
    
    # Return exit code based on test results
    summary = results["summary"]
    if summary["failed_tests"] == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {summary['failed_tests']} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())