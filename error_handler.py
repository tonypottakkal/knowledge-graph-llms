"""
Frontend Error Handler Module

This module provides comprehensive error handling for JavaScript console errors
and visualization failures in the knowledge graph application.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class ErrorType(Enum):
    """Enumeration of different error types that can occur in the frontend."""
    BROWSER_EXTENSION = "browser_extension"
    UI_LIBRARY_DEPENDENCY = "ui_library_dependency"
    VISUALIZATION_RENDERING = "visualization_rendering"
    CONTENT_SECURITY_POLICY = "content_security_policy"
    NETWORK_CONNECTION = "network_connection"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Enumeration of error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Data class for storing error context information."""
    error_type: str
    component: str
    provider: str
    user_action: str
    timestamp: datetime
    technical_details: Dict[str, Any]
    user_message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM


@dataclass
class VisualizationConfig:
    """Configuration for visualization error handling."""
    enable_csp: bool = True
    suppress_warnings: bool = True
    fallback_enabled: bool = True
    retry_attempts: int = 3
    security_level: str = "strict"


class FrontendErrorHandler:
    """
    Handles frontend JavaScript errors and provides user-friendly error messages
    with appropriate fallback mechanisms.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize the error handler with configuration.
        
        Args:
            config: Configuration for error handling behavior
        """
        self.config = config or VisualizationConfig()
        self.logger = logging.getLogger(__name__)
        self._error_patterns = self._initialize_error_patterns()
        self._fallback_options = self._initialize_fallback_options()
        
    def _initialize_error_patterns(self) -> Dict[ErrorType, List[str]]:
        """Initialize regex patterns for error categorization."""
        return {
            ErrorType.BROWSER_EXTENSION: [
                r"content_script\.js.*Cannot read properties of undefined.*'control'",
                r"content_script\.js.*shouldOfferCompletionListForField",
                r"content_script\.js.*elementWasFocused",
                r"content_script\.js.*focusInEventHandler"
            ],
            ErrorType.UI_LIBRARY_DEPENDENCY: [
                r"`preventOverflow` modifier is required by `hide` modifier",
                r"isModifierRequired.*preventOverflow",
                r"modifier.*required.*order to work"
            ],
            ErrorType.VISUALIZATION_RENDERING: [
                r"PyVis.*network.*failed",
                r"vis\.js.*error",
                r"network\.setData.*error",
                r"Cannot read properties.*nodes"
            ],
            ErrorType.CONTENT_SECURITY_POLICY: [
                r"Refused to.*unsafe-inline",
                r"Content Security Policy.*violated",
                r"CSP.*directive.*violated"
            ],
            ErrorType.NETWORK_CONNECTION: [
                r"Failed to fetch",
                r"NetworkError",
                r"ERR_NETWORK_CHANGED",
                r"ERR_INTERNET_DISCONNECTED"
            ]
        }
    
    def _initialize_fallback_options(self) -> Dict[ErrorType, Dict[str, Any]]:
        """Initialize fallback options for different error types."""
        return {
            ErrorType.BROWSER_EXTENSION: {
                "action": "isolate_form_fields",
                "message": "Browser extension interference detected. Form protection enabled.",
                "user_visible": False
            },
            ErrorType.UI_LIBRARY_DEPENDENCY: {
                "action": "load_dependencies",
                "message": "Loading required UI dependencies...",
                "user_visible": True
            },
            ErrorType.VISUALIZATION_RENDERING: {
                "action": "fallback_renderer",
                "message": "Using alternative visualization renderer.",
                "user_visible": True
            },
            ErrorType.CONTENT_SECURITY_POLICY: {
                "action": "adjust_csp",
                "message": "Adjusting security policies for visualization.",
                "user_visible": False
            },
            ErrorType.NETWORK_CONNECTION: {
                "action": "retry_connection",
                "message": "Network issue detected. Retrying connection...",
                "user_visible": True
            }
        }
    
    def categorize_error(self, error_message: str) -> ErrorType:
        """
        Categorize an error message based on predefined patterns.
        
        Args:
            error_message: The error message to categorize
            
        Returns:
            ErrorType: The categorized error type
        """
        error_lower = error_message.lower()
        
        for error_type, patterns in self._error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    self.logger.debug(f"Categorized error as {error_type.value}: {pattern}")
                    return error_type
        
        return ErrorType.UNKNOWN
    
    def determine_severity(self, error_type: ErrorType, error_message: str) -> ErrorSeverity:
        """
        Determine the severity of an error based on its type and content.
        
        Args:
            error_type: The categorized error type
            error_message: The original error message
            
        Returns:
            ErrorSeverity: The determined severity level
        """
        # Browser extension errors are typically low severity
        if error_type == ErrorType.BROWSER_EXTENSION:
            return ErrorSeverity.LOW
        
        # UI library dependency issues are medium severity
        if error_type == ErrorType.UI_LIBRARY_DEPENDENCY:
            return ErrorSeverity.MEDIUM
        
        # Visualization rendering failures are high severity
        if error_type == ErrorType.VISUALIZATION_RENDERING:
            return ErrorSeverity.HIGH
        
        # CSP violations are medium severity unless they block functionality
        if error_type == ErrorType.CONTENT_SECURITY_POLICY:
            if "blocked" in error_message.lower():
                return ErrorSeverity.HIGH
            return ErrorSeverity.MEDIUM
        
        # Network errors are high severity
        if error_type == ErrorType.NETWORK_CONNECTION:
            return ErrorSeverity.HIGH
        
        return ErrorSeverity.MEDIUM
    
    def handle_visualization_error(self, error: Exception, context: Dict[str, Any]) -> ErrorContext:
        """
        Handle visualization-specific errors with appropriate fallback mechanisms.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            ErrorContext: Processed error context with user message and fallback options
        """
        error_message = str(error)
        error_type = self.categorize_error(error_message)
        severity = self.determine_severity(error_type, error_message)
        
        # Generate user-friendly message
        user_message = self.generate_user_message(error_type, context.get('provider', 'unknown'))
        
        # Create error context
        error_context = ErrorContext(
            error_type=error_type.value,
            component=context.get('component', 'visualization'),
            provider=context.get('provider', 'unknown'),
            user_action=context.get('user_action', 'generate_graph'),
            timestamp=datetime.now(),
            technical_details={
                'original_error': error_message,
                'error_class': error.__class__.__name__,
                'context': context
            },
            user_message=user_message,
            severity=severity
        )
        
        # Log technical details
        self.log_technical_details(error, error_context)
        
        return error_context
    
    def generate_user_message(self, error_type: ErrorType, provider: str = 'unknown') -> str:
        """
        Generate a user-friendly error message based on error type and provider.
        
        Args:
            error_type: The categorized error type
            provider: The LLM provider being used
            
        Returns:
            str: User-friendly error message with actionable guidance
        """
        base_messages = {
            ErrorType.BROWSER_EXTENSION: (
                "Browser extension interference detected. This doesn't affect the application's "
                "functionality, but you may see some console warnings."
            ),
            ErrorType.UI_LIBRARY_DEPENDENCY: (
                "Loading visualization dependencies. The graph may take a moment to appear properly."
            ),
            ErrorType.VISUALIZATION_RENDERING: (
                f"Unable to render the knowledge graph using the standard visualization. "
                f"This may be due to the complexity of the generated graph or a temporary issue "
                f"with the {provider} provider. Please try again or use a different provider."
            ),
            ErrorType.CONTENT_SECURITY_POLICY: (
                "Security policies are being adjusted to display the visualization safely."
            ),
            ErrorType.NETWORK_CONNECTION: (
                f"Network connection issue detected while communicating with {provider}. "
                f"Please check your internet connection and try again."
            ),
            ErrorType.UNKNOWN: (
                "An unexpected error occurred. Please try refreshing the page or "
                "contact support if the issue persists."
            )
        }
        
        return base_messages.get(error_type, base_messages[ErrorType.UNKNOWN])
    
    def log_technical_details(self, error: Exception, context: ErrorContext) -> None:
        """
        Log detailed technical information for debugging purposes.
        
        Args:
            error: The original exception
            context: The error context with additional details
        """
        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(context.severity, logging.WARNING)
        
        self.logger.log(
            log_level,
            f"Frontend error in {context.component}: {context.error_type} "
            f"(severity: {context.severity.value})",
            extra={
                'error_type': context.error_type,
                'component': context.component,
                'provider': context.provider,
                'user_action': context.user_action,
                'timestamp': context.timestamp.isoformat(),
                'technical_details': context.technical_details
            }
        )
    
    def get_fallback_options(self, error_type: ErrorType) -> Dict[str, Any]:
        """
        Get fallback options for a specific error type.
        
        Args:
            error_type: The error type to get fallback options for
            
        Returns:
            Dict containing fallback action and configuration
        """
        return self._fallback_options.get(error_type, {
            "action": "display_error",
            "message": "An error occurred. Please try again.",
            "user_visible": True
        })
    
    def should_suppress_error(self, error_type: ErrorType) -> bool:
        """
        Determine if an error should be suppressed from user display.
        
        Args:
            error_type: The error type to check
            
        Returns:
            bool: True if the error should be suppressed
        """
        if not self.config.suppress_warnings:
            return False
        
        # Suppress browser extension errors as they don't affect functionality
        if error_type == ErrorType.BROWSER_EXTENSION:
            return True
        
        # Suppress CSP adjustments as they're handled automatically
        if error_type == ErrorType.CONTENT_SECURITY_POLICY:
            return True
        
        return False
    
    def get_retry_strategy(self, error_type: ErrorType) -> Dict[str, Any]:
        """
        Get retry strategy for recoverable errors.
        
        Args:
            error_type: The error type to get retry strategy for
            
        Returns:
            Dict containing retry configuration
        """
        strategies = {
            ErrorType.NETWORK_CONNECTION: {
                "max_attempts": self.config.retry_attempts,
                "backoff_factor": 2.0,
                "initial_delay": 1.0
            },
            ErrorType.VISUALIZATION_RENDERING: {
                "max_attempts": 2,
                "backoff_factor": 1.5,
                "initial_delay": 0.5
            },
            ErrorType.UI_LIBRARY_DEPENDENCY: {
                "max_attempts": 3,
                "backoff_factor": 1.0,
                "initial_delay": 0.1
            }
        }
        
        return strategies.get(error_type, {
            "max_attempts": 1,
            "backoff_factor": 1.0,
            "initial_delay": 0.0
        })


# Utility functions for common error handling patterns

def handle_javascript_console_errors(console_errors: List[str]) -> List[ErrorContext]:
    """
    Process a list of JavaScript console errors and return categorized error contexts.
    
    Args:
        console_errors: List of error messages from JavaScript console
        
    Returns:
        List of ErrorContext objects with categorized and processed errors
    """
    handler = FrontendErrorHandler()
    processed_errors = []
    
    for error_msg in console_errors:
        try:
            # Create a mock exception for processing
            mock_error = Exception(error_msg)
            context = {
                'component': 'javascript_console',
                'user_action': 'page_load',
                'provider': 'browser'
            }
            
            error_context = handler.handle_visualization_error(mock_error, context)
            processed_errors.append(error_context)
            
        except Exception as e:
            # Fallback error handling
            handler.logger.error(f"Failed to process console error: {error_msg}, {str(e)}")
    
    return processed_errors


def get_error_suppression_script() -> str:
    """
    Generate JavaScript code to suppress known harmless console errors.
    
    Returns:
        str: JavaScript code for error suppression
    """
    return """
    // Suppress known harmless browser feature warnings
    (function() {
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
        
        console.error = function(...args) {
            const message = args.join(' ');
            // Only suppress content_script errors, not application errors
            if (message.includes('content_script.js') && 
                message.includes('Cannot read properties of undefined')) {
                return; // Suppress browser extension errors
            }
            originalError.apply(console, args);
        };
    })();
    """


class ErrorTracker:
    """
    Tracks and correlates errors across the application for debugging and analytics.
    """
    
    def __init__(self):
        """Initialize the error tracker."""
        self.error_history: List[ErrorContext] = []
        self.error_correlations: Dict[str, List[str]] = {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = logging.getLogger(f"{__name__}.tracker")
    
    def track_error(self, error_context: ErrorContext) -> str:
        """
        Track an error and assign it a unique identifier.
        
        Args:
            error_context: The error context to track
            
        Returns:
            str: Unique error identifier
        """
        error_id = f"{self.session_id}_{len(self.error_history):04d}"
        error_context.technical_details['error_id'] = error_id
        
        self.error_history.append(error_context)
        self._update_correlations(error_context)
        
        self.logger.info(f"Tracked error {error_id}: {error_context.error_type}")
        return error_id
    
    def _update_correlations(self, error_context: ErrorContext) -> None:
        """
        Update error correlations to identify patterns.
        
        Args:
            error_context: The error context to correlate
        """
        correlation_key = f"{error_context.component}_{error_context.error_type}"
        
        if correlation_key not in self.error_correlations:
            self.error_correlations[correlation_key] = []
        
        self.error_correlations[correlation_key].append(
            error_context.technical_details.get('error_id', 'unknown')
        )
    
    def get_error_patterns(self) -> Dict[str, Any]:
        """
        Analyze error patterns and return insights.
        
        Returns:
            Dict containing error pattern analysis
        """
        if not self.error_history:
            return {"total_errors": 0, "patterns": {}}
        
        # Count errors by type
        error_counts = {}
        severity_counts = {}
        component_counts = {}
        
        for error in self.error_history:
            error_counts[error.error_type] = error_counts.get(error.error_type, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            component_counts[error.component] = component_counts.get(error.component, 0) + 1
        
        # Identify frequent error patterns
        frequent_patterns = {
            key: ids for key, ids in self.error_correlations.items() 
            if len(ids) > 2
        }
        
        return {
            "total_errors": len(self.error_history),
            "session_id": self.session_id,
            "error_types": error_counts,
            "severity_distribution": severity_counts,
            "component_distribution": component_counts,
            "frequent_patterns": frequent_patterns,
            "last_error_time": self.error_history[-1].timestamp.isoformat() if self.error_history else None
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorContext]:
        """
        Get the most recent errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent ErrorContext objects
        """
        return self.error_history[-limit:] if self.error_history else []
    
    def clear_old_errors(self, max_age_hours: int = 24) -> int:
        """
        Clear errors older than the specified age.
        
        Args:
            max_age_hours: Maximum age of errors to keep in hours
            
        Returns:
            int: Number of errors cleared
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        initial_count = len(self.error_history)
        
        self.error_history = [
            error for error in self.error_history 
            if error.timestamp > cutoff_time
        ]
        
        cleared_count = initial_count - len(self.error_history)
        if cleared_count > 0:
            self.logger.info(f"Cleared {cleared_count} old errors")
        
        return cleared_count


# Global error tracker instance
_global_error_tracker = None


def get_error_tracker() -> ErrorTracker:
    """
    Get the global error tracker instance.
    
    Returns:
        ErrorTracker: The global error tracker
    """
    global _global_error_tracker
    if _global_error_tracker is None:
        _global_error_tracker = ErrorTracker()
    return _global_error_tracker


def track_frontend_error(error: Exception, context: Dict[str, Any]) -> str:
    """
    Convenience function to track a frontend error.
    
    Args:
        error: The exception that occurred
        context: Additional context about the error
        
    Returns:
        str: Unique error identifier
    """
    handler = FrontendErrorHandler()
    error_context = handler.handle_visualization_error(error, context)
    
    tracker = get_error_tracker()
    return tracker.track_error(error_context)


# Import required modules for datetime operations
from datetime import timedelta