import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  title?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Unhandled rendering error in ErrorBoundary:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center p-8 bg-bgCard border border-borderColor rounded-2xl text-center space-y-4 my-4 max-w-lg mx-auto shadow-lg">
          <div className="w-12 h-12 rounded-full bg-dangerBg border border-dangerBorder flex items-center justify-center text-dangerText">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-textPrimary mb-1">
              {this.props.title || 'Something went wrong rendering this component'}
            </h3>
            <p className="text-xs text-textMuted leading-relaxed font-mono bg-bgInput p-2 rounded-lg border border-borderMuted text-left overflow-x-auto max-h-24">
              {this.state.error?.message || 'Unknown runtime exception'}
            </p>
          </div>
          <button
            onClick={this.handleRetry}
            className="px-4 py-2 bg-accent hover:bg-accentHover text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all shadow-md shadow-accent/20"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
