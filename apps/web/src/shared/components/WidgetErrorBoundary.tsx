import React, { Component, ErrorInfo, ReactNode } from 'react';
import { WidgetErrorCard } from '../../features/dashboard/components/Skeletons';

interface WidgetErrorBoundaryProps {
  children: ReactNode;
  title?: string;
  message?: string;
  onRetry?: () => void;
}

interface WidgetErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class WidgetErrorBoundary extends Component<WidgetErrorBoundaryProps, WidgetErrorBoundaryState> {
  public state: WidgetErrorBoundaryState = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): WidgetErrorBoundaryState {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error('[WidgetErrorBoundary] Caught widget exception:', error, errorInfo);
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <WidgetErrorCard
          title={this.props.title || "Unable to render component"}
          message={this.props.message || "A rendering error occurred in this widget."}
          onRetry={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

export default WidgetErrorBoundary;
