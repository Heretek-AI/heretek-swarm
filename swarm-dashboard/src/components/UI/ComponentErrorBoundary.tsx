/**
 * ComponentErrorBoundary Component
 * 
 * Per-component error boundary for wrapping individual dashboard components.
 * Shows fallback UI instead of crashing the entire dashboard.
 * Logs errors to console and optionally to backend.
 */

import React, { Component, ErrorInfo, ReactNode, useState, useCallback } from 'react';
import createLogger from '../../utils/logger';

const logger = createLogger('ComponentErrorBoundary');

export interface ComponentErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode | ((error: Error, reset: () => void) => ReactNode);
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  className?: string;
  componentName?: string;
  logToBackend?: boolean;
  retryable?: boolean;
}

interface ComponentErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  retryCount: number;
}

export class ComponentErrorBoundary extends Component<ComponentErrorBoundaryProps, ComponentErrorBoundaryState> {
  constructor(props: ComponentErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, retryCount: 0 };
  }

  static getDerivedStateFromError(error: Error): ComponentErrorBoundaryState {
    return { hasError: true, error, retryCount: 0 };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const componentName = this.props.componentName || 'Unknown Component';
    
    logger.error(`Error in ${componentName}`, {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });

    this.setState({ errorInfo });
    this.props.onError?.(error, errorInfo);

    // Optionally log to backend
    if (this.props.logToBackend) {
      this.logToBackend(error, errorInfo);
    }
  }

  private async logToBackend(error: Error, errorInfo: ErrorInfo) {
    try {
      const apiKey = localStorage.getItem('api_key');
      const apiUrl = localStorage.getItem('api_url') || '';
      
      await fetch(`${apiUrl}/api/logs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {}),
        },
        body: JSON.stringify({
          level: 'error',
          message: `Component Error: ${this.props.componentName || 'Unknown'}`,
          context: {
            error: error.message,
            stack: error.stack,
            componentStack: errorInfo.componentStack,
            timestamp: new Date().toISOString(),
          },
        }),
      });
    } catch (logError) {
      logger.warn('Failed to log error to backend', { error: logError });
    }
  }

  handleRetry = () => {
    const maxRetries = 3;
    if (this.state.retryCount < maxRetries) {
      this.setState({ 
        hasError: false, 
        error: undefined, 
        errorInfo: undefined,
        retryCount: this.state.retryCount + 1 
      });
      logger.info(`Retrying component render`, { 
        attempt: this.state.retryCount + 1,
        maxRetries 
      });
    }
  };

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined, retryCount: 0 });
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        if (typeof this.props.fallback === 'function') {
          return this.props.fallback(this.state.error!, this.handleReset);
        }
        return this.props.fallback;
      }

      // Default fallback UI
      const componentName = this.props.componentName || 'Component';
      
      return (
        <div className={`${this.props.className || ''} p-4 bg-red-900/20 border border-red-500/50 rounded-xl`}>
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            
            <div className="flex-1 min-w-0">
              <h4 className="text-red-400 font-semibold">
                {componentName} encountered an error
              </h4>
              
              <p className="text-gray-400 text-sm mt-1">
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>
              
              {this.state.errorInfo && (
                <details className="mt-3">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                    Error details (click to expand)
                  </summary>
                  <pre className="mt-2 p-3 bg-gray-900 rounded-lg text-xs text-red-400 overflow-auto max-h-48 whitespace-pre-wrap break-words">
                    {this.state.error?.stack}
                  </pre>
                </details>
              )}
              
              <div className="flex gap-2 mt-4">
                {this.props.retryable !== false && this.state.retryCount < 3 && (
                  <button
                    onClick={this.handleRetry}
                    className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors font-medium"
                  >
                    Retry ({this.state.retryCount + 1}/3)
                  </button>
                )}
                <button
                  onClick={this.handleReset}
                  className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors font-medium"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * ErrorFallback Component
 * 
 * Simple error fallback for inline use.
 */
export interface ErrorFallbackProps {
  error: Error;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  componentName?: string;
}

export function ErrorFallback({ 
  error, 
  onRetry, 
  onDismiss, 
  className = '',
  componentName 
}: ErrorFallbackProps) {
  return (
    <div className={`${className} p-4 bg-red-900/20 border border-red-500/50 rounded-lg`}>
      <div className="flex items-start gap-3">
        <span className="text-red-400 text-lg">⚠️</span>
        <div className="flex-1">
          <h4 className="text-red-400 font-semibold text-sm">
            {componentName ? `${componentName} Error` : 'Error'}
          </h4>
          <p className="text-gray-400 text-sm mt-1">{error.message}</p>
          <div className="flex gap-2 mt-2">
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-xs text-red-400 hover:text-red-300 underline"
              >
                Try again
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-xs text-gray-400 hover:text-gray-300 underline"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * withErrorBoundary HOC
 * 
 * Higher-order component that wraps a component with an error boundary.
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: {
    componentName?: string;
    fallback?: ReactNode;
    logToBackend?: boolean;
  } = {}
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ComponentErrorBoundary
        componentName={options.componentName || WrappedComponent.displayName || WrappedComponent.name}
        fallback={options.fallback}
        logToBackend={options.logToBackend}
      >
        <WrappedComponent {...props} />
      </ComponentErrorBoundary>
    );
  };
}

export default ComponentErrorBoundary;
