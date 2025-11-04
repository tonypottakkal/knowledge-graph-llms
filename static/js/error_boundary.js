/**
 * Visualization Error Boundary
 * 
 * Provides comprehensive error handling and recovery mechanisms for
 * knowledge graph visualizations with fallback rendering options.
 */

class VisualizationErrorBoundary {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            maxRetries: 3,
            retryDelay: 1000,
            fallbackEnabled: true,
            debugMode: false,
            onError: null,
            onRetry: null,
            onFallback: null,
            ...options
        };
        
        this.retryCount = 0;
        this.currentError = null;
        this.fallbackRenderer = null;
        this.originalContent = null;
        
        this.initialize();
    }
    
    initialize() {
        if (!this.container) {
            console.error(`Container with ID '${this.containerId}' not found`);
            return;
        }
        
        // Store original content
        this.originalContent = this.container.innerHTML;
        
        // Set up global error handlers
        this.setupGlobalErrorHandlers();
        
        // Add error boundary styles
        this.addErrorBoundaryStyles();
        
        console.log(`Error boundary initialized for container: ${this.containerId}`);
    }
    
    setupGlobalErrorHandlers() {
        // Handle JavaScript errors
        window.addEventListener('error', (event) => {
            if (this.isVisualizationError(event)) {
                this.catchError(event.error, {
                    type: 'javascript_error',
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno
                });
            }
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            if (this.isVisualizationError(event)) {
                this.catchError(event.reason, {
                    type: 'promise_rejection',
                    promise: event.promise
                });
            }
        });
        
        // Handle vis.js specific errors
        if (typeof vis !== 'undefined') {
            const originalNetworkConstructor = vis.Network;
            const errorBoundary = this;
            
            vis.Network = function(container, data, options) {
                try {
                    return new originalNetworkConstructor(container, data, options);
                } catch (error) {
                    errorBoundary.catchError(error, {
                        type: 'vis_network_constructor',
                        container: container,
                        data: data,
                        options: options
                    });
                    throw error;
                }
            };
        }
    }
    
    isVisualizationError(event) {
        // Check if error is related to visualization
        const errorMessage = event.error ? event.error.message : event.reason;
        const filename = event.filename || '';
        
        return (
            filename.includes('vis-network') ||
            filename.includes('vis.js') ||
            errorMessage.includes('vis') ||
            errorMessage.includes('network') ||
            errorMessage.includes(this.containerId) ||
            (event.target && event.target.id === this.containerId)
        );
    }
    
    catchError(error, errorInfo = {}) {
        this.currentError = {
            error: error,
            info: errorInfo,
            timestamp: new Date().toISOString(),
            retryCount: this.retryCount
        };
        
        console.error('Visualization error caught by boundary:', error, errorInfo);
        
        // Call custom error handler if provided
        if (this.options.onError) {
            this.options.onError(error, errorInfo);
        }
        
        // Determine error type and response
        const errorType = this.categorizeError(error, errorInfo);
        
        // Show error UI
        this.renderError(errorType);
        
        // Attempt recovery if possible
        if (this.canRetry(errorType)) {
            this.scheduleRetry();
        } else if (this.options.fallbackEnabled) {
            this.renderFallback(errorType);
        }
    }
    
    categorizeError(error, errorInfo) {
        const errorMessage = error.message || error.toString();
        const errorLower = errorMessage.toLowerCase();
        
        if (errorLower.includes('network') || errorLower.includes('fetch')) {
            return 'network_error';
        } else if (errorLower.includes('data') || errorLower.includes('dataset')) {
            return 'data_error';
        } else if (errorLower.includes('render') || errorLower.includes('draw')) {
            return 'rendering_error';
        } else if (errorLower.includes('memory') || errorLower.includes('heap')) {
            return 'memory_error';
        } else if (errorInfo.type === 'vis_network_constructor') {
            return 'initialization_error';
        } else {
            return 'unknown_error';
        }
    }
    
    canRetry(errorType) {
        const retryableErrors = ['network_error', 'rendering_error', 'initialization_error'];
        return (
            retryableErrors.includes(errorType) &&
            this.retryCount < this.options.maxRetries
        );
    }
    
    scheduleRetry() {
        const delay = this.options.retryDelay * Math.pow(2, this.retryCount); // Exponential backoff
        
        setTimeout(() => {
            this.retryVisualization();
        }, delay);
    }
    
    retryVisualization() {
        this.retryCount++;
        
        console.log(`Retrying visualization (attempt ${this.retryCount}/${this.options.maxRetries})`);
        
        // Call custom retry handler if provided
        if (this.options.onRetry) {
            this.options.onRetry(this.retryCount);
        }
        
        // Clear error display
        this.clearError();
        
        // Show loading state
        this.showLoading(`Retrying... (${this.retryCount}/${this.options.maxRetries})`);
        
        // Attempt to reinitialize visualization
        try {
            if (typeof initializeVisualization === 'function') {
                initializeVisualization();
            } else {
                // Fallback: reload the page
                location.reload();
            }
        } catch (error) {
            console.error('Retry failed:', error);
            this.catchError(error, { type: 'retry_failed' });
        }
    }
    
    renderError(errorType) {
        const errorMessages = {
            network_error: {
                title: 'Network Error',
                message: 'Unable to load visualization data. Please check your connection.',
                icon: '🌐'
            },
            data_error: {
                title: 'Data Error',
                message: 'There was an issue with the graph data. Please try regenerating.',
                icon: '📊'
            },
            rendering_error: {
                title: 'Rendering Error',
                message: 'The visualization could not be rendered. Trying alternative display.',
                icon: '🎨'
            },
            memory_error: {
                title: 'Memory Error',
                message: 'The graph is too large to display. Try with smaller text.',
                icon: '💾'
            },
            initialization_error: {
                title: 'Initialization Error',
                message: 'Failed to initialize the visualization engine.',
                icon: '⚙️'
            },
            unknown_error: {
                title: 'Visualization Error',
                message: 'An unexpected error occurred while creating the graph.',
                icon: '❌'
            }
        };
        
        const errorConfig = errorMessages[errorType] || errorMessages.unknown_error;
        
        const errorHtml = `
            <div class="error-boundary-container">
                <div class="error-content">
                    <div class="error-icon">${errorConfig.icon}</div>
                    <h3 class="error-title">${errorConfig.title}</h3>
                    <p class="error-message">${errorConfig.message}</p>
                    
                    ${this.canRetry(errorType) ? `
                        <div class="error-actions">
                            <button class="retry-button" onclick="errorBoundary.retryVisualization()">
                                Retry (${this.retryCount}/${this.options.maxRetries})
                            </button>
                        </div>
                    ` : ''}
                    
                    ${this.options.fallbackEnabled ? `
                        <div class="error-actions">
                            <button class="fallback-button" onclick="errorBoundary.renderFallback('${errorType}')">
                                Show Alternative View
                            </button>
                        </div>
                    ` : ''}
                    
                    ${this.options.debugMode ? `
                        <details class="error-details">
                            <summary>Technical Details</summary>
                            <pre class="error-stack">${this.currentError.error.stack || 'No stack trace available'}</pre>
                        </details>
                    ` : ''}
                </div>
            </div>
        `;
        
        this.container.innerHTML = errorHtml;
    }
    
    renderFallback(errorType) {
        console.log('Rendering fallback visualization for error type:', errorType);
        
        // Call custom fallback handler if provided
        if (this.options.onFallback) {
            this.options.onFallback(errorType);
        }
        
        // Create fallback visualization
        const fallbackHtml = `
            <div class="fallback-container">
                <div class="fallback-header">
                    <h3>📋 Knowledge Graph Summary</h3>
                    <p>The interactive visualization is unavailable. Here's a text-based summary:</p>
                </div>
                
                <div class="fallback-content">
                    <div class="fallback-section">
                        <h4>🔗 Graph Structure</h4>
                        <p>This knowledge graph contains interconnected concepts and relationships extracted from your text.</p>
                        <div id="fallback-stats"></div>
                    </div>
                    
                    <div class="fallback-section">
                        <h4>💡 Suggestions</h4>
                        <ul>
                            <li>Try refreshing the page</li>
                            <li>Use a different browser</li>
                            <li>Reduce the input text size</li>
                            <li>Check your internet connection</li>
                        </ul>
                    </div>
                    
                    <div class="fallback-actions">
                        <button class="refresh-button" onclick="location.reload()">
                            🔄 Refresh Page
                        </button>
                        <button class="retry-button" onclick="errorBoundary.retryVisualization()">
                            🔁 Try Again
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = fallbackHtml;
        
        // Try to populate fallback stats if data is available
        this.populateFallbackStats();
    }
    
    populateFallbackStats() {
        const statsContainer = document.getElementById('fallback-stats');
        if (!statsContainer) return;
        
        // Try to extract stats from global variables or localStorage
        let stats = { nodes: 0, edges: 0 };
        
        try {
            if (typeof nodes !== 'undefined' && typeof edges !== 'undefined') {
                stats.nodes = nodes.length || 0;
                stats.edges = edges.length || 0;
            }
        } catch (e) {
            // Ignore errors when accessing global variables
        }
        
        statsContainer.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">${stats.nodes}</span>
                    <span class="stat-label">Concepts</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.edges}</span>
                    <span class="stat-label">Relationships</span>
                </div>
            </div>
        `;
    }
    
    showLoading(message = 'Loading visualization...') {
        const loadingHtml = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p class="loading-message">${message}</p>
            </div>
        `;
        
        this.container.innerHTML = loadingHtml;
    }
    
    clearError() {
        // Remove error-specific classes and content
        this.container.classList.remove('error-state', 'fallback-state');
    }
    
    reset() {
        this.retryCount = 0;
        this.currentError = null;
        this.clearError();
        
        if (this.originalContent) {
            this.container.innerHTML = this.originalContent;
        }
    }
    
    addErrorBoundaryStyles() {
        if (document.getElementById('error-boundary-styles')) {
            return; // Styles already added
        }
        
        const styles = `
            <style id="error-boundary-styles">
                .error-boundary-container {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 400px;
                    background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
                    border-radius: 8px;
                    padding: 20px;
                    color: white;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .error-content {
                    text-align: center;
                    max-width: 500px;
                }
                
                .error-icon {
                    font-size: 48px;
                    margin-bottom: 16px;
                }
                
                .error-title {
                    margin: 0 0 12px 0;
                    font-size: 24px;
                    font-weight: 600;
                    color: #ff6b6b;
                }
                
                .error-message {
                    margin: 0 0 24px 0;
                    font-size: 16px;
                    line-height: 1.5;
                    color: #cccccc;
                }
                
                .error-actions {
                    margin: 16px 0;
                }
                
                .retry-button, .fallback-button, .refresh-button {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    margin: 0 8px;
                    transition: background-color 0.2s;
                }
                
                .retry-button:hover, .refresh-button:hover {
                    background: #45a049;
                }
                
                .fallback-button {
                    background: #2196F3;
                }
                
                .fallback-button:hover {
                    background: #1976D2;
                }
                
                .error-details {
                    margin-top: 24px;
                    text-align: left;
                }
                
                .error-details summary {
                    cursor: pointer;
                    color: #ffa726;
                    font-weight: 500;
                }
                
                .error-stack {
                    background: #1a1a1a;
                    padding: 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    color: #e0e0e0;
                    overflow-x: auto;
                    margin-top: 8px;
                }
                
                .loading-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 400px;
                    background: #222222;
                    border-radius: 8px;
                    color: white;
                }
                
                .loading-spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid #333;
                    border-top: 4px solid #4CAF50;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 16px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .loading-message {
                    font-size: 16px;
                    color: #cccccc;
                }
                
                .fallback-container {
                    background: #2d2d2d;
                    border-radius: 8px;
                    padding: 24px;
                    color: white;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .fallback-header h3 {
                    margin: 0 0 8px 0;
                    color: #4CAF50;
                }
                
                .fallback-section {
                    margin: 24px 0;
                }
                
                .fallback-section h4 {
                    margin: 0 0 12px 0;
                    color: #ffa726;
                }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 16px;
                    margin: 16px 0;
                }
                
                .stat-item {
                    background: #1a1a1a;
                    padding: 16px;
                    border-radius: 6px;
                    text-align: center;
                }
                
                .stat-number {
                    display: block;
                    font-size: 24px;
                    font-weight: bold;
                    color: #4CAF50;
                }
                
                .stat-label {
                    display: block;
                    font-size: 12px;
                    color: #cccccc;
                    margin-top: 4px;
                }
                
                .fallback-actions {
                    margin-top: 24px;
                    text-align: center;
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }
}

// Global error boundary instance
let errorBoundary = null;

// Initialize error boundary when DOM is ready
function initializeErrorBoundary(containerId = 'mynetworkid', options = {}) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            errorBoundary = new VisualizationErrorBoundary(containerId, options);
        });
    } else {
        errorBoundary = new VisualizationErrorBoundary(containerId, options);
    }
    
    return errorBoundary;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VisualizationErrorBoundary, initializeErrorBoundary };
}