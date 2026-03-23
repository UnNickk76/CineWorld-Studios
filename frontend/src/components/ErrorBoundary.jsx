import React from 'react';
import { RefreshCw, Film as FilmIcon, AlertTriangle } from 'lucide-react';

// ─── Mini Step Bar for Film Cards ───
export const MiniStepBar = ({ status }) => {
  const steps = [
    { id: 'proposed', color: 'bg-yellow-500' },
    { id: 'coming_soon', color: 'bg-orange-500' },
    { id: 'casting', color: 'bg-cyan-500' },
    { id: 'screenplay', color: 'bg-green-500' },
    { id: 'pre_production', color: 'bg-blue-500' },
    { id: 'shooting', color: 'bg-purple-500' },
    { id: 'completed', color: 'bg-emerald-500' },
  ];
  
  const statusOrder = steps.map(s => s.id);
  const currentIdx = statusOrder.indexOf(status);
  
  return (
    <div className="mini-step-bar flex items-center gap-[2px] mt-1.5" data-testid="mini-step-bar">
      {steps.map((s, i) => (
        <div
          key={s.id}
          className={`mini-step h-[3px] rounded-full flex-1 transition-all ${
            i < currentIdx ? `${s.color} opacity-70 completed`
            : i === currentIdx ? `${s.color} active`
            : 'bg-gray-800'
          }`}
        />
      ))}
    </div>
  );
};

// ─── Cinematic Error Boundary (Film Glitch Effect) ───

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
      const errorMsg = this.state.error?.message || '';
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 p-4 relative error-glitch" data-testid="error-boundary">
          {/* Film reel decorative element */}
          <div className="relative">
            <div className="w-20 h-20 bg-red-500/5 rounded-full flex items-center justify-center border border-red-500/20">
              <FilmIcon className="w-8 h-8 text-red-400/80" />
            </div>
            <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500/20 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-3 h-3 text-red-400" />
            </div>
          </div>
          <div className="text-center space-y-1">
            <h2 className="text-base font-bold text-white">La pellicola si è inceppata!</h2>
            <p className="text-xs text-gray-500 max-w-xs">
              Un problema tecnico ha interrotto la scena. Il nostro team è al lavoro.
            </p>
          </div>
          {errorMsg && (
            <p className="text-[10px] text-red-400/50 text-center max-w-xs bg-red-500/5 p-2 rounded border border-red-500/10 font-mono">
              {errorMsg}
            </p>
          )}
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            className="flex items-center gap-2 px-5 py-2.5 bg-yellow-500 text-black rounded-full font-semibold text-sm hover:bg-yellow-400 transition-all hover:scale-105 active:scale-95"
            data-testid="error-retry-btn"
          >
            <RefreshCw className="w-4 h-4" /> Riprendi la scena
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Lightweight error boundary for individual tabs/sections - does NOT break the whole page
export class TabErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorMsg: '' };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, errorMsg: error?.message || '' };
  }

  componentDidCatch(error, errorInfo) {
    console.error(`TabErrorBoundary [${this.props.name || 'unknown'}]:`, error?.message);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-center relative" data-testid={`tab-error-${this.props.name || 'unknown'}`}>
          <div className="w-12 h-12 mx-auto mb-2 bg-red-500/5 rounded-full flex items-center justify-center border border-red-500/15">
            <FilmIcon className="w-5 h-5 text-red-400/60" />
          </div>
          <p className="text-xs text-gray-400 mb-0.5">Scena interrotta</p>
          {this.state.errorMsg && (
            <p className="text-[9px] text-red-400/40 mb-2 font-mono">{this.state.errorMsg}</p>
          )}
          <button
            onClick={() => this.setState({ hasError: false, errorMsg: '' })}
            className="text-[10px] text-yellow-400 hover:text-yellow-300 font-medium px-3 py-1 rounded-full border border-yellow-500/20 hover:bg-yellow-500/10 transition-all"
          >
            Riprendi
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
