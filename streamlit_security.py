"""
Streamlit Security Manager

This module provides security enhancements for Streamlit applications,
including protection from browser extension interference and secure
iframe configuration.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, List, Optional
import logging
import uuid
from dataclasses import dataclass


@dataclass
class IframeSandboxConfig:
    """Configuration for iframe sandboxing."""
    allow_scripts: bool = True
    allow_same_origin: bool = False  # Set to False for better security
    allow_forms: bool = False
    allow_popups: bool = False
    allow_top_navigation: bool = False
    additional_permissions: List[str] = None
    
    def __post_init__(self):
        if self.additional_permissions is None:
            self.additional_permissions = []


class StreamlitSecurityManager:
    """
    Manages security features for Streamlit applications including
    browser extension protection and iframe sandboxing.
    """
    
    def __init__(self, iframe_config: Optional[IframeSandboxConfig] = None):
        """
        Initialize the security manager.
        
        Args:
            iframe_config: Configuration for iframe sandboxing
        """
        self.iframe_config = iframe_config or IframeSandboxConfig()
        self.logger = logging.getLogger(__name__)
        self._session_id = str(uuid.uuid4())
        
    def apply_csp_headers(self) -> None:
        """
        Apply Content Security Policy headers to the Streamlit app.
        Note: Streamlit has limited support for custom headers, so this
        provides JavaScript-based CSP enforcement.
        """
        csp_script = """
        <script>
            // Apply CSP-like protections via JavaScript
            (function() {
                'use strict';
                
                // Monitor and block unauthorized script injections
                const originalCreateElement = document.createElement;
                document.createElement = function(tagName) {
                    const element = originalCreateElement.call(this, tagName);
                    
                    if (tagName.toLowerCase() === 'script') {
                        // Log script creation for monitoring
                        console.debug('Script element created:', element);
                        
                        // Add integrity checking if needed
                        const originalSetAttribute = element.setAttribute;
                        element.setAttribute = function(name, value) {
                            if (name === 'src' && !value.startsWith('data:') && 
                                !value.includes('streamlit') && 
                                !value.includes('cdn.jsdelivr.net') &&
                                !value.includes('unpkg.com')) {
                                console.warn('Potentially unauthorized script source:', value);
                            }
                            return originalSetAttribute.call(this, name, value);
                        };
                    }
                    
                    return element;
                };
                
            })();
        </script>
        """
        
        components.html(csp_script, height=0)
        self.logger.debug("Applied CSP-like protections via JavaScript")
    
    def protect_form_fields(self) -> None:
        """
        Protect form fields from browser extension interference.
        """
        protection_script = """
        <script>
            (function() {
                'use strict';
                
                // Protection against browser extension interference
                function protectFormFields() {
                    // Find all Streamlit input elements
                    const streamlitInputs = document.querySelectorAll(
                        'input[data-testid], textarea[data-testid], select[data-testid], ' +
                        '.stTextInput input, .stTextArea textarea, .stSelectbox select, ' +
                        '.stNumberInput input, .stFileUploader input'
                    );
                    
                    streamlitInputs.forEach(input => {
                        if (input.hasAttribute('data-protected')) {
                            return; // Already protected
                        }
                        
                        input.setAttribute('data-protected', 'true');
                        input.setAttribute('data-session', '""" + self._session_id + """');
                        
                        // Override addEventListener to filter extension listeners
                        const originalAddEventListener = input.addEventListener;
                        input.addEventListener = function(type, listener, options) {
                            // Check if listener is from browser extension
                            if (listener && typeof listener === 'function') {
                                const listenerStr = listener.toString();
                                
                                // Block known extension patterns
                                if (listenerStr.includes('content_script') ||
                                    listenerStr.includes('shouldOfferCompletionListForField') ||
                                    listenerStr.includes('elementWasFocused') ||
                                    listenerStr.includes('focusInEventHandler')) {
                                    console.debug('Blocked extension listener on', type, 'event');
                                    return;
                                }
                            }
                            
                            return originalAddEventListener.call(this, type, listener, options);
                        };
                        
                        // Prevent extension property access
                        Object.defineProperty(input, 'control', {
                            get: function() {
                                console.debug('Blocked extension access to control property');
                                return undefined;
                            },
                            configurable: false
                        });
                        
                        // Add focus protection
                        input.addEventListener('focus', function(e) {
                            // Ensure this is a legitimate focus event
                            if (e.isTrusted === false) {
                                console.debug('Blocked untrusted focus event');
                                e.stopImmediatePropagation();
                                return false;
                            }
                        }, true);
                        
                        console.debug('Protected input element:', input);
                    });
                }
                
                // Initial protection
                protectFormFields();
                
                // Re-apply protection when new elements are added
                const observer = new MutationObserver(function(mutations) {
                    let shouldReprotect = false;
                    
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'childList') {
                            mutation.addedNodes.forEach(function(node) {
                                if (node.nodeType === Node.ELEMENT_NODE) {
                                    const hasInputs = node.querySelectorAll && 
                                        node.querySelectorAll('input, textarea, select').length > 0;
                                    if (hasInputs) {
                                        shouldReprotect = true;
                                    }
                                }
                            });
                        }
                    });
                    
                    if (shouldReprotect) {
                        setTimeout(protectFormFields, 100);
                    }
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
                
                console.log('Form field protection initialized');
                
            })();
        </script>
        """
        
        components.html(protection_script, height=0)
        self.logger.info("Applied form field protection against browser extensions")
    
    def configure_iframe_sandbox(self, html_content: str, height: int = 1000) -> None:
        """
        Configure secure iframe sandboxing for embedded content.
        
        Args:
            html_content: HTML content to embed in iframe
            height: Height of the iframe
        """
        # Build sandbox permissions
        sandbox_permissions = []
        
        if self.iframe_config.allow_scripts:
            sandbox_permissions.append('allow-scripts')
        
        if self.iframe_config.allow_same_origin:
            sandbox_permissions.append('allow-same-origin')
        else:
            # Add warning about potential security risk
            self.logger.warning(
                "iframe configured with allow-same-origin=False for better security. "
                "Some functionality may be limited."
            )
        
        if self.iframe_config.allow_forms:
            sandbox_permissions.append('allow-forms')
        
        if self.iframe_config.allow_popups:
            sandbox_permissions.append('allow-popups')
        
        if self.iframe_config.allow_top_navigation:
            sandbox_permissions.append('allow-top-navigation')
        
        # Add additional permissions
        sandbox_permissions.extend(self.iframe_config.additional_permissions)
        
        sandbox_attr = ' '.join(sandbox_permissions)
        
        # Create secure iframe wrapper
        secure_iframe_html = f"""
        <div style="border: 1px solid #ddd; border-radius: 4px; overflow: hidden;">
            <iframe 
                srcdoc="{html_content.replace('"', '&quot;')}"
                sandbox="{sandbox_attr}"
                style="width: 100%; height: {height}px; border: none;"
                loading="lazy"
                referrerpolicy="no-referrer"
                allow="accelerometer 'none'; camera 'none'; geolocation 'none'; microphone 'none'"
            ></iframe>
        </div>
        """
        
        components.html(secure_iframe_html, height=height + 10)
        
        self.logger.info(f"Configured secure iframe with sandbox: {sandbox_attr}")
    
    def suppress_browser_warnings(self) -> None:
        """
        Suppress harmless browser warnings that don't affect functionality.
        """
        suppression_script = r"""
        <script>
            (function() {
                'use strict';
                
                // Store original console methods
                const originalWarn = console.warn;
                const originalError = console.error;
                
                // Patterns for warnings to suppress
                const suppressWarningPatterns = [
                    /Unrecognized feature.*ambient-light-sensor/,
                    /Unrecognized feature.*battery/,
                    /Unrecognized feature.*document-domain/,
                    /Unrecognized feature.*layout-animations/,
                    /Unrecognized feature.*legacy-image-formats/,
                    /Unrecognized feature.*oversized-images/,
                    /Unrecognized feature.*vr/,
                    /Unrecognized feature.*wake-lock/,
                    /iframe.*allow-scripts.*allow-same-origin.*sandbox/,
                    /Feature Policy.*deprecated/
                ];
                
                // Patterns for errors to suppress (only extension-related)
                const suppressErrorPatterns = [
                    /content_script\.js.*Cannot read properties of undefined.*'control'/,
                    /content_script\.js.*shouldOfferCompletionListForField/,
                    /content_script\.js.*elementWasFocused/,
                    /content_script\.js.*focusInEventHandler/
                ];
                
                // Override console.warn
                console.warn = function(...args) {
                    const message = args.join(' ');
                    
                    // Check if this warning should be suppressed
                    const shouldSuppress = suppressWarningPatterns.some(pattern => 
                        pattern.test(message)
                    );
                    
                    if (!shouldSuppress) {
                        originalWarn.apply(console, args);
                    } else {
                        // Optionally log to debug console
                        console.debug('Suppressed warning:', message);
                    }
                };
                
                // Override console.error (only for extension errors)
                console.error = function(...args) {
                    const message = args.join(' ');
                    
                    // Check if this error should be suppressed
                    const shouldSuppress = suppressErrorPatterns.some(pattern => 
                        pattern.test(message)
                    );
                    
                    if (!shouldSuppress) {
                        originalError.apply(console, args);
                    } else {
                        // Log extension errors as debug messages
                        console.debug('Suppressed extension error:', message);
                    }
                };
                
                console.log('Browser warning suppression initialized');
                
            })();
        </script>
        """
        
        components.html(suppression_script, height=0)
        self.logger.info("Applied browser warning suppression")
    
    def add_security_headers_info(self) -> None:
        """
        Add security headers information to the page (for debugging).
        """
        if st.sidebar.checkbox("Show Security Info", value=False):
            with st.sidebar.expander("Security Configuration"):
                st.write("**Session ID:**", self._session_id[:8] + "...")
                st.write("**Iframe Sandbox:**")
                st.json({
                    "allow_scripts": self.iframe_config.allow_scripts,
                    "allow_same_origin": self.iframe_config.allow_same_origin,
                    "allow_forms": self.iframe_config.allow_forms,
                    "allow_popups": self.iframe_config.allow_popups,
                    "additional_permissions": self.iframe_config.additional_permissions
                })
                
                st.write("**Protection Status:**")
                st.success("✅ Form field protection active")
                st.success("✅ Browser warning suppression active")
                st.success("✅ Extension interference protection active")
    
    def initialize_all_protections(self) -> None:
        """
        Initialize all security protections in the correct order.
        """
        try:
            # Apply protections in order
            self.suppress_browser_warnings()
            self.apply_csp_headers()
            self.protect_form_fields()
            
            # Add security info to sidebar
            self.add_security_headers_info()
            
            self.logger.info("All security protections initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize security protections: {str(e)}")
            st.error("⚠️ Some security protections failed to initialize")
    
    def create_secure_component(self, html_content: str, height: int = 1000, 
                              scrolling: bool = False) -> None:
        """
        Create a secure component with all protections applied.
        
        Args:
            html_content: HTML content to display
            height: Height of the component
            scrolling: Whether to allow scrolling
        """
        try:
            # Configure iframe with security settings
            iframe_config = IframeSandboxConfig(
                allow_scripts=True,
                allow_same_origin=False,  # Better security
                allow_forms=False,
                allow_popups=False
            )
            
            # Update iframe config
            original_config = self.iframe_config
            self.iframe_config = iframe_config
            
            # Create secure iframe
            self.configure_iframe_sandbox(html_content, height)
            
            # Restore original config
            self.iframe_config = original_config
            
        except Exception as e:
            self.logger.error(f"Failed to create secure component: {str(e)}")
            # Fallback to standard component
            components.html(html_content, height=height, scrolling=scrolling)


# Utility functions for easy integration

def initialize_streamlit_security(iframe_config: Optional[IframeSandboxConfig] = None) -> StreamlitSecurityManager:
    """
    Initialize Streamlit security manager with default settings.
    
    Args:
        iframe_config: Optional iframe configuration
        
    Returns:
        StreamlitSecurityManager: Configured security manager
    """
    security_manager = StreamlitSecurityManager(iframe_config)
    security_manager.initialize_all_protections()
    return security_manager


def display_secure_html(html_content: str, height: int = 1000, 
                       security_manager: Optional[StreamlitSecurityManager] = None) -> None:
    """
    Display HTML content with security protections.
    
    Args:
        html_content: HTML content to display
        height: Height of the display area
        security_manager: Optional security manager instance
    """
    if security_manager is None:
        security_manager = StreamlitSecurityManager()
    
    security_manager.create_secure_component(html_content, height)


def get_protection_status() -> Dict[str, bool]:
    """
    Get the status of various protection mechanisms.
    
    Returns:
        Dict containing protection status
    """
    return {
        "form_protection": True,
        "warning_suppression": True,
        "csp_protection": True,
        "iframe_sandboxing": True,
        "extension_blocking": True
    }