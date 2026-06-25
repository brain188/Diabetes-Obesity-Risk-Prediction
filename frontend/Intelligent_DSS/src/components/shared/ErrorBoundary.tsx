import { Component, type ReactNode, type ErrorInfo } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary] Caught render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center min-h-[320px] gap-4 p-8">
          <div className="p-4 rounded-full bg-red-50 border border-red-200">
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
          <div className="text-center max-w-md">
            <h2 className="text-lg font-semibold text-foreground mb-1">Something went wrong</h2>
            <p className="text-sm text-muted-foreground mb-3">
              {this.state.error.message || "An unexpected error occurred while rendering this page."}
            </p>
            <details className="text-left text-xs text-muted-foreground/60 bg-muted rounded-lg p-3 mb-4">
              <summary className="cursor-pointer font-medium">Technical details</summary>
              <pre className="mt-2 whitespace-pre-wrap break-all">{this.state.error.stack}</pre>
            </details>
          </div>
          <button
            onClick={() => this.setState({ error: null })}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <RefreshCw className="h-4 w-4" /> Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
