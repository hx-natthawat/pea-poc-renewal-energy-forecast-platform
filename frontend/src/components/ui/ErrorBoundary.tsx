"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="bg-white rounded-lg shadow-md p-4 sm:p-6 border-l-4 border-red-500">
          <div className="flex items-start">
            <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6 text-red-500 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm sm:text-base font-semibold text-gray-800 mb-1">
                Something went wrong
              </h3>
              <p className="text-xs sm:text-sm text-gray-600 mb-3">
                This component encountered an error and couldn't render properly.
              </p>
              {this.state.error && (
                <details className="mb-3">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                    Error details
                  </summary>
                  <pre className="mt-2 p-2 bg-gray-50 rounded text-xs text-red-600 overflow-auto max-h-32">
                    {this.state.error.message}
                  </pre>
                </details>
              )}
              <button
                type="button"
                onClick={this.handleRetry}
                className="inline-flex items-center px-3 py-1.5 text-xs sm:text-sm font-medium text-white bg-[#74045F] hover:bg-[#5a0349] rounded-md transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                Try again
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
