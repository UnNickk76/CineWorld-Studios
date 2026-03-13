import React from 'react';
import { RefreshCw } from 'lucide-react';

export const LoadingSpinner = ({ text }) => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3" data-testid="loading-spinner">
    <div className="relative">
      <div className="w-10 h-10 border-2 border-yellow-500/20 rounded-full" />
      <div className="w-10 h-10 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin absolute inset-0" />
    </div>
    <p className="text-sm text-gray-400 animate-pulse">{text || 'Caricamento...'}</p>
  </div>
);

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error?.message, error?.stack, errorInfo?.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 p-4" data-testid="error-boundary">
          <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
            <span className="text-2xl text-red-500">!</span>
          </div>
          <h2 className="text-lg font-bold text-white">Qualcosa è andato storto</h2>
          <p className="text-sm text-gray-400 text-center max-w-md">
            Si è verificato un errore nel caricamento di questa sezione.
          </p>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-black rounded-lg font-medium hover:bg-yellow-400 transition-colors"
            data-testid="error-retry-btn"
          >
            <RefreshCw className="w-4 h-4" /> Riprova
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
