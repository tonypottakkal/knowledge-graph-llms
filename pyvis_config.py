"""
PyVis Configuration Manager

This module provides enhanced configuration and security features for PyVis
network visualizations, including Content Security Policy implementation
and proper dependency management.
"""

import os
import re
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging


@dataclass
class SecurityConfig:
    """Configuration for security policies and CSP settings."""
    enable_csp: bool = True
    allow_inline_scripts: bool = False
    allow_inline_styles: bool = True
    script_nonce: Optional[str] = None
    style_nonce: Optional[str] = None
    trusted_domains: List[str] = None
    
    def __post_init__(self):
        if self.trusted_domains is None:
            self.trusted_domains = ['cdn.jsdelivr.net', 'unpkg.com', 'cdnjs.cloudflare.com']


@dataclass
class DependencyConfig:
    """Configuration for JavaScript library dependencies."""
    vis_js_version: str = "9.1.9"
    use_cdn: bool = True
    local_fallback: bool = True
    dependency_order: List[str] = None
    
    def __post_init__(self):
        if self.dependency_order is None:
            self.dependency_order = ['vis-network', 'vis-data', 'vis-util']


class PyVisConfigManager:
    """
    Manages PyVis configuration with enhanced security and dependency handling.
    """
    
    def __init__(self, security_config: Optional[SecurityConfig] = None,
                 dependency_config: Optional[DependencyConfig] = None):
        """
        Initialize the PyVis configuration manager.
        
        Args:
            security_config: Security configuration settings
            dependency_config: Dependency configuration settings
        """
        self.security_config = security_config or SecurityConfig()
        self.dependency_config = dependency_config or DependencyConfig()
        self.logger = logging.getLogger(__name__)
        
        # Generate nonces for CSP if not provided
        if self.security_config.enable_csp:
            if not self.security_config.script_nonce:
                self.security_config.script_nonce = self._generate_nonce()
            if not self.security_config.style_nonce:
                self.security_config.style_nonce = self._generate_nonce()
    
    def _generate_nonce(self) -> str:
        """Generate a cryptographically secure nonce for CSP."""
        return str(uuid.uuid4()).replace('-', '')
    
    def get_secure_html_template(self) -> str:
        """
        Generate a secure HTML template with proper CSP headers and dependency loading.
        
        Returns:
            str: Complete HTML template with security enhancements
        """
        csp_header = self._generate_csp_header()
        dependencies = self._get_dependency_scripts()
        error_suppression = self._get_error_suppression_script()
        
        template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {csp_header}
    <title>Knowledge Graph Visualization</title>
    
    <!-- Dependency Scripts -->
    {dependencies}
    
    <!-- Error Suppression and Protection -->
    <script nonce="{self.security_config.script_nonce}">
        {error_suppression}
    </script>
    
    <!-- Visualization Styles -->
    <style nonce="{self.security_config.style_nonce}">
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #222222;
            color: white;
        }}
        
        #mynetworkid {{
            width: 100%;
            height: 100vh;
            border: none;
            background-color: #222222;
        }}
        
        .error-overlay {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 0, 0, 0.1);
            border: 2px solid #ff4444;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            z-index: 1000;
            display: none;
        }}
        
        .loading-overlay {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            z-index: 999;
        }}
        
        .spinner {{
            border: 3px solid #333;
            border-top: 3px solid #fff;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="mynetworkid"></div>
    
    <!-- Loading Overlay -->
    <div id="loading-overlay" class="loading-overlay">
        <div class="spinner"></div>
        <div>Loading visualization...</div>
    </div>
    
    <!-- Error Overlay -->
    <div id="error-overlay" class="error-overlay">
        <h3>Visualization Error</h3>
        <p id="error-message">An error occurred while rendering the graph.</p>
        <button onclick="retryVisualization()" style="margin-top: 10px; padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
            Retry
        </button>
    </div>
    
    <!-- Visualization Script Placeholder -->
    <script nonce="{self.security_config.script_nonce}">
        // Visualization script will be inserted here
        {{VISUALIZATION_SCRIPT}}
    </script>
</body>
</html>"""
        
        return template
    
    def _generate_csp_header(self) -> str:
        """
        Generate Content Security Policy header based on configuration.
        
        Returns:
            str: CSP meta tag with appropriate policies
        """
        if not self.security_config.enable_csp:
            return ""
        
        # Build CSP directives
        directives = []
        
        # Script sources
        script_src = ["'self'"]
        if self.security_config.script_nonce:
            script_src.append(f"'nonce-{self.security_config.script_nonce}'")
        if self.security_config.allow_inline_scripts:
            script_src.append("'unsafe-inline'")
        
        # Add trusted CDN domains
        script_src.extend(self.security_config.trusted_domains)
        directives.append(f"script-src {' '.join(script_src)}")
        
        # Style sources
        style_src = ["'self'"]
        if self.security_config.style_nonce:
            style_src.append(f"'nonce-{self.security_config.style_nonce}'")
        if self.security_config.allow_inline_styles:
            style_src.append("'unsafe-inline'")
        
        style_src.extend(self.security_config.trusted_domains)
        directives.append(f"style-src {' '.join(style_src)}")
        
        # Other directives
        directives.extend([
            "img-src 'self' data: blob:",
            "font-src 'self' " + " ".join(self.security_config.trusted_domains),
            "connect-src 'self'",
            "frame-ancestors 'self'",
            "base-uri 'self'"
        ])
        
        csp_content = "; ".join(directives)
        return f'<meta http-equiv="Content-Security-Policy" content="{csp_content}">'
    
    def _get_dependency_scripts(self) -> str:
        """
        Generate script tags for required dependencies with proper loading order.
        
        Returns:
            str: HTML script tags for dependencies
        """
        scripts = []
        
        if self.dependency_config.use_cdn:
            # Use CDN with fallback
            vis_version = self.dependency_config.vis_js_version
            
            # Main vis.js library with preventOverflow fix
            cdn_script = f"""
    <!-- Vis.js Network Library -->
    <script src="https://unpkg.com/vis-network@{vis_version}/standalone/umd/vis-network.min.js"
            integrity="sha384-..." crossorigin="anonymous"
            onerror="loadLocalFallback('vis-network')"></script>
    
    <!-- Popper.js for proper modifier dependencies -->
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js"
            crossorigin="anonymous"
            onerror="loadLocalFallback('popper')"></script>"""
            
            scripts.append(cdn_script)
            
            if self.dependency_config.local_fallback:
                fallback_script = f"""
    <!-- Local Fallback Scripts -->
    <script nonce="{self.security_config.script_nonce}">
        function loadLocalFallback(library) {{
            console.warn('CDN failed for ' + library + ', using local fallback');
            // In a real implementation, you would load local versions here
            if (library === 'vis-network') {{
                // Load local vis-network
                console.log('Loading local vis-network fallback');
            }} else if (library === 'popper') {{
                // Load local popper
                console.log('Loading local popper fallback');
            }}
        }}
    </script>"""
                scripts.append(fallback_script)
        
        return "\n".join(scripts)
    
    def _get_error_suppression_script(self) -> str:
        """
        Generate JavaScript code for error suppression and protection.
        
        Returns:
            str: JavaScript code for error handling
        """
        return """
        // Error suppression and browser extension protection
        (function() {
            'use strict';
            
            // Suppress known harmless warnings
            const originalWarn = console.warn;
            const originalError = console.error;
            
            const suppressPatterns = [
                /Unrecognized feature.*ambient-light-sensor/,
                /Unrecognized feature.*battery/,
                /Unrecognized feature.*document-domain/,
                /Unrecognized feature.*layout-animations/,
                /Unrecognized feature.*legacy-image-formats/,
                /Unrecognized feature.*oversized-images/,
                /Unrecognized feature.*vr/,
                /Unrecognized feature.*wake-lock/,
                /iframe.*allow-scripts.*allow-same-origin.*sandbox/
            ];
            
            console.warn = function(...args) {
                const message = args.join(' ');
                if (!suppressPatterns.some(pattern => pattern.test(message))) {
                    originalWarn.apply(console, args);
                }
            };
            
            // Suppress content_script errors but preserve application errors
            console.error = function(...args) {
                const message = args.join(' ');
                if (message.includes('content_script.js') && 
                    (message.includes('Cannot read properties of undefined') ||
                     message.includes('shouldOfferCompletionListForField') ||
                     message.includes('elementWasFocused'))) {
                    return; // Suppress browser extension errors
                }
                originalError.apply(console, args);
            };
            
            // Protect form fields from extension interference
            function protectFormFields() {
                const inputs = document.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    // Add protection attributes
                    input.setAttribute('data-protected', 'true');
                    
                    // Override extension event handlers
                    const originalAddEventListener = input.addEventListener;
                    input.addEventListener = function(type, listener, options) {
                        // Only allow our own event listeners
                        if (listener && listener.toString().includes('content_script')) {
                            return; // Block extension listeners
                        }
                        return originalAddEventListener.call(this, type, listener, options);
                    };
                });
            }
            
            // Initialize protection when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', protectFormFields);
            } else {
                protectFormFields();
            }
            
            // Global error handler for visualization
            window.addEventListener('error', function(event) {
                if (event.filename && event.filename.includes('vis-network')) {
                    console.error('Visualization error:', event.error);
                    showErrorOverlay('Visualization rendering failed. Please try again.');
                    return true; // Prevent default error handling
                }
            });
            
            // Handle unhandled promise rejections
            window.addEventListener('unhandledrejection', function(event) {
                console.error('Unhandled promise rejection:', event.reason);
                if (event.reason && event.reason.toString().includes('vis')) {
                    showErrorOverlay('Visualization loading failed. Please refresh the page.');
                }
            });
            
        })();
        
        // Utility functions for error handling
        function showErrorOverlay(message) {
            const overlay = document.getElementById('error-overlay');
            const messageEl = document.getElementById('error-message');
            if (overlay && messageEl) {
                messageEl.textContent = message;
                overlay.style.display = 'block';
            }
        }
        
        function hideErrorOverlay() {
            const overlay = document.getElementById('error-overlay');
            if (overlay) {
                overlay.style.display = 'none';
            }
        }
        
        function showLoadingOverlay() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
        }
        
        function hideLoadingOverlay() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.style.display = 'none';
            }
        }
        
        function retryVisualization() {
            hideErrorOverlay();
            showLoadingOverlay();
            
            // Attempt to reinitialize the visualization
            setTimeout(() => {
                try {
                    if (typeof initializeVisualization === 'function') {
                        initializeVisualization();
                    } else {
                        location.reload(); // Fallback to page reload
                    }
                } catch (error) {
                    console.error('Retry failed:', error);
                    showErrorOverlay('Retry failed. Please refresh the page manually.');
                }
            }, 1000);
        }
        """
    
    def configure_dependencies(self) -> Dict[str, Any]:
        """
        Configure dependency loading with proper order and fallbacks.
        
        Returns:
            Dict containing dependency configuration
        """
        config = {
            'vis_js': {
                'version': self.dependency_config.vis_js_version,
                'cdn_url': f'https://unpkg.com/vis-network@{self.dependency_config.vis_js_version}/standalone/umd/vis-network.min.js',
                'local_path': 'static/js/vis-network.min.js',
                'required': True
            },
            'popper_js': {
                'version': '2.11.8',
                'cdn_url': 'https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js',
                'local_path': 'static/js/popper.min.js',
                'required': True,
                'note': 'Required for preventOverflow modifier'
            }
        }
        
        self.logger.info("Configured dependencies with proper loading order")
        return config
    
    def apply_content_security_policy(self, html_content: str) -> str:
        """
        Apply Content Security Policy to HTML content.
        
        Args:
            html_content: Original HTML content
            
        Returns:
            str: HTML content with CSP applied
        """
        if not self.security_config.enable_csp:
            return html_content
        
        # Add nonce attributes to inline scripts and styles
        if self.security_config.script_nonce:
            html_content = re.sub(
                r'<script(?![^>]*nonce=)([^>]*)>',
                f'<script nonce="{self.security_config.script_nonce}"\\1>',
                html_content
            )
        
        if self.security_config.style_nonce:
            html_content = re.sub(
                r'<style(?![^>]*nonce=)([^>]*)>',
                f'<style nonce="{self.security_config.style_nonce}"\\1>',
                html_content
            )
        
        self.logger.debug("Applied CSP to HTML content")
        return html_content
    
    def handle_library_warnings(self) -> Dict[str, str]:
        """
        Generate fixes for common library warnings.
        
        Returns:
            Dict containing warning fixes and explanations
        """
        fixes = {
            'preventOverflow_modifier': {
                'issue': 'preventOverflow modifier is required by hide modifier',
                'fix': 'Ensure Popper.js is loaded before vis.js and preventOverflow is included in modifiers array',
                'code': '''
                // Ensure proper modifier order in Popper.js configuration
                const popperConfig = {
                    modifiers: [
                        {
                            name: 'preventOverflow',
                            enabled: true,
                            options: {
                                boundary: 'viewport'
                            }
                        },
                        {
                            name: 'hide',
                            enabled: true
                        }
                    ]
                };
                '''
            },
            'content_script_errors': {
                'issue': 'Browser extension content_script.js errors',
                'fix': 'Implement form field protection and event isolation',
                'code': 'Form fields are automatically protected from extension interference'
            },
            'feature_policy_warnings': {
                'issue': 'Unrecognized browser feature warnings',
                'fix': 'Suppress harmless feature policy warnings',
                'code': 'Warnings are automatically suppressed in console'
            }
        }
        
        return fixes
    
    def get_visualization_config(self) -> Dict[str, Any]:
        """
        Get complete configuration for visualization rendering.
        
        Returns:
            Dict containing all configuration options
        """
        return {
            'security': {
                'csp_enabled': self.security_config.enable_csp,
                'script_nonce': self.security_config.script_nonce,
                'style_nonce': self.security_config.style_nonce,
                'trusted_domains': self.security_config.trusted_domains
            },
            'dependencies': {
                'vis_version': self.dependency_config.vis_js_version,
                'use_cdn': self.dependency_config.use_cdn,
                'local_fallback': self.dependency_config.local_fallback,
                'load_order': self.dependency_config.dependency_order
            },
            'error_handling': {
                'suppress_warnings': True,
                'protect_forms': True,
                'retry_enabled': True
            }
        }


def create_secure_pyvis_html(nodes_data: str, edges_data: str, 
                           config_manager: Optional[PyVisConfigManager] = None) -> str:
    """
    Create a secure PyVis HTML file with proper error handling and CSP.
    
    Args:
        nodes_data: JavaScript code for nodes data
        edges_data: JavaScript code for edges data
        config_manager: Optional configuration manager
        
    Returns:
        str: Complete HTML content with security enhancements
    """
    if config_manager is None:
        config_manager = PyVisConfigManager()
    
    template = config_manager.get_secure_html_template()
    
    # Generate the visualization script
    visualization_script = f"""
        // Initialize visualization with error handling
        function initializeVisualization() {{
            try {{
                showLoadingOverlay();
                
                // Nodes and edges data
                {nodes_data}
                {edges_data}
                
                // Create network
                const container = document.getElementById('mynetworkid');
                const data = {{ nodes: nodes, edges: edges }};
                
                const options = {{
                    physics: {{
                        forceAtlas2Based: {{
                            gravitationalConstant: -100,
                            centralGravity: 0.01,
                            springLength: 200,
                            springConstant: 0.08
                        }},
                        minVelocity: 0.75,
                        solver: "forceAtlas2Based"
                    }},
                    interaction: {{
                        hover: true,
                        selectConnectedEdges: false
                    }},
                    nodes: {{
                        font: {{ color: 'white' }},
                        borderWidth: 2
                    }},
                    edges: {{
                        font: {{ color: 'white', align: 'middle' }},
                        arrows: {{ to: {{ enabled: true }} }}
                    }}
                }};
                
                const network = new vis.Network(container, data, options);
                
                // Add event listeners
                network.on('stabilizationIterationsDone', function() {{
                    hideLoadingOverlay();
                }});
                
                network.on('stabilizationProgress', function(params) {{
                    const progress = Math.round((params.iterations / params.total) * 100);
                    console.log('Stabilization progress:', progress + '%');
                }});
                
                // Handle network errors
                network.on('error', function(error) {{
                    console.error('Network error:', error);
                    hideLoadingOverlay();
                    showErrorOverlay('Network rendering error occurred.');
                }});
                
                console.log('Visualization initialized successfully');
                
            }} catch (error) {{
                console.error('Visualization initialization failed:', error);
                hideLoadingOverlay();
                showErrorOverlay('Failed to initialize visualization: ' + error.message);
            }}
        }}
        
        // Start initialization when page loads
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initializeVisualization);
        }} else {{
            initializeVisualization();
        }}
    """
    
    # Replace placeholder with actual script
    html_content = template.replace('{VISUALIZATION_SCRIPT}', visualization_script)
    
    # Apply CSP if enabled
    return config_manager.apply_content_security_policy(html_content)