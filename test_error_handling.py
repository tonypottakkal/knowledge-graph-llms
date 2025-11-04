#!/usr/bin/env python3
"""
Test script for frontend error handling functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from error_handler import FrontendErrorHandler, handle_javascript_console_errors, get_error_tracker
from pyvis_config import PyVisConfigManager, SecurityConfig, DependencyConfig
from streamlit_security import StreamlitSecurityManager, IframeSandboxConfig

def test_error_handler():
    """Test the FrontendErrorHandler functionality."""
    print("Testing FrontendErrorHandler...")
    
    handler = FrontendErrorHandler()
    
    # Test error categorization
    test_errors = [
        "content_script.js:1 Uncaught TypeError: Cannot read properties of undefined (reading 'control')",
        "`preventOverflow` modifier is required by `hide` modifier in order to work",
        "Unrecognized feature: 'ambient-light-sensor'",
        "PyVis network rendering failed",
        "Some random error"
    ]
    
    for error_msg in test_errors:
        error_type = handler.categorize_error(error_msg)
        user_message = handler.generate_user_message(error_type)
        should_suppress = handler.should_suppress_error(error_type)
        
        print(f"Error: {error_msg[:50]}...")
        print(f"  Type: {error_type.value}")
        print(f"  Suppress: {should_suppress}")
        print(f"  Message: {user_message[:80]}...")
        print()

def test_pyvis_config():
    """Test the PyVisConfigManager functionality."""
    print("Testing PyVisConfigManager...")
    
    security_config = SecurityConfig(enable_csp=True)
    dependency_config = DependencyConfig(use_cdn=True)
    
    config_manager = PyVisConfigManager(security_config, dependency_config)
    
    # Test HTML template generation
    template = config_manager.get_secure_html_template()
    
    print(f"Generated template length: {len(template)} characters")
    print("Template includes CSP:", "Content-Security-Policy" in template)
    print("Template includes error suppression:", "suppressPatterns" in template)
    print("Template includes error boundary:", "error-overlay" in template)
    print()

def test_streamlit_security():
    """Test the StreamlitSecurityManager functionality."""
    print("Testing StreamlitSecurityManager...")
    
    iframe_config = IframeSandboxConfig(
        allow_scripts=True,
        allow_same_origin=False
    )
    
    security_manager = StreamlitSecurityManager(iframe_config)
    
    # Test configuration
    print(f"Session ID: {security_manager._session_id[:8]}...")
    print(f"Allow scripts: {security_manager.iframe_config.allow_scripts}")
    print(f"Allow same origin: {security_manager.iframe_config.allow_same_origin}")
    print()

def test_error_tracking():
    """Test the error tracking functionality."""
    print("Testing error tracking...")
    
    # Simulate some console errors
    console_errors = [
        "content_script.js:1 Uncaught TypeError: Cannot read properties of undefined (reading 'control')",
        "`preventOverflow` modifier is required by `hide` modifier in order to work",
        "Unrecognized feature: 'battery'"
    ]
    
    processed_errors = handle_javascript_console_errors(console_errors)
    
    print(f"Processed {len(processed_errors)} console errors")
    
    # Track the processed errors
    tracker = get_error_tracker()
    for error_context in processed_errors:
        tracker.track_error(error_context)
    
    patterns = tracker.get_error_patterns()
    
    print(f"Total tracked errors: {patterns['total_errors']}")
    if 'error_types' in patterns and patterns['error_types']:
        print(f"Error types: {list(patterns['error_types'].keys())}")
    else:
        print("No error types tracked yet")
    print()

def test_error_suppression_script():
    """Test the error suppression JavaScript generation."""
    print("Testing error suppression script...")
    
    from error_handler import get_error_suppression_script
    
    script = get_error_suppression_script()
    
    print(f"Script length: {len(script)} characters")
    print("Includes extension protection:", "content_script" in script)
    print("Includes warning suppression:", "suppressPatterns" in script)
    print("Includes form protection:", "protectFormFields" in script)
    print()

def main():
    """Run all tests."""
    print("=" * 60)
    print("Frontend Error Handling Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_error_handler()
        test_pyvis_config()
        test_streamlit_security()
        test_error_tracking()
        test_error_suppression_script()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())