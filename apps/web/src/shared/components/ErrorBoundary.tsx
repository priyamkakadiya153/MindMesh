import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackDescription?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      const title = this.props.fallbackTitle || 'Something went wrong';
      const description =
        this.props.fallbackDescription ||
        'An unexpected error occurred in this section. You can try refreshing the view.';

      return (
        <div
          role="alert"
          aria-live="assertive"
          className="p-6 my-4 rounded-2xl border border-dangerBorder bg-dangerBg/50 backdrop-blur-md text-center max-w-lg mx-auto shadow-lg space-y-3"
        >
          <div className="w-12 h-12 rounded-xl bg-dangerBg text-dangerText flex items-center justify-center mx-auto border border-dangerBorder/50">
            <AlertTriangle className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-textPrimary">{title}</h3>
            <p className="text-xs text-textMuted mt-1 leading-relaxed">{description}</p>
          </div>
          <button
            type="button"
            onClick={this.handleReset}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-accent hover:bg-accentHover text-white text-xs font-semibold rounded-xl shadow-md shadow-accent/20 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Try Again</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
