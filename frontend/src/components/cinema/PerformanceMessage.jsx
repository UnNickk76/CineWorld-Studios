// CineWorld Studio's — PerformanceMessage (Velion-style)
// Mostra un messaggio dinamico sull'andamento, aggiornato ogni ora.
// Quando hour_id cambia rispetto al precedente, mostra un badge "NUOVO" pulsante.
// Anche un alert in caso di rischio ritiro imminente.

import React, { useState, useEffect, useRef } from 'react';
import { Lightbulb, AlertTriangle, Sparkles } from 'lucide-react';

const CLASSIFICATION_STYLE = {
  great: { bg: 'from-emerald-900/40 to-zinc-900/30', ring: 'ring-emerald-700/40', text: 'text-emerald-200', dot: 'bg-emerald-400' },
  good: { bg: 'from-green-900/30 to-zinc-900/30', ring: 'ring-green-700/40', text: 'text-green-200', dot: 'bg-green-400' },
  ok: { bg: 'from-cyan-900/20 to-zinc-900/30', ring: 'ring-cyan-700/30', text: 'text-cyan-200', dot: 'bg-cyan-400' },
  declining: { bg: 'from-amber-900/30 to-zinc-900/30', ring: 'ring-amber-700/40', text: 'text-amber-200', dot: 'bg-amber-400' },
  bad: { bg: 'from-orange-900/30 to-zinc-900/30', ring: 'ring-orange-700/40', text: 'text-orange-200', dot: 'bg-orange-400' },
  flop: { bg: 'from-rose-900/40 to-zinc-900/30', ring: 'ring-rose-700/50', text: 'text-rose-200', dot: 'bg-rose-400' },
};

export const PerformanceMessage = ({ performance, contentId, recentHoldRatio }) => {
  const [showNewBadge, setShowNewBadge] = useState(false);
  const lastHourRef = useRef(null);
  const storageKey = `perf_msg_hour:${contentId}`;

  const cls = performance?.classification || 'ok';
  const style = CLASSIFICATION_STYLE[cls] || CLASSIFICATION_STYLE.ok;

  useEffect(() => {
    if (!performance?.hour_id || !contentId) return;
    try {
      const stored = localStorage.getItem(storageKey);
      const cur = String(performance.hour_id);
      if (stored && stored !== cur) {
        setShowNewBadge(true);
        setTimeout(() => setShowNewBadge(false), 8000);
      }
      localStorage.setItem(storageKey, cur);
      lastHourRef.current = cur;
    } catch { /* noop */ }
  }, [performance?.hour_id, contentId, storageKey]);

  if (!performance) return null;

  return (
    <div className="space-y-2" data-testid="performance-message">
      {/* Main message */}
      <div className={`relative rounded-xl bg-gradient-to-br ${style.bg} ring-1 ${style.ring} p-3`}>
        <div className="flex items-start gap-2">
          <div className="flex-shrink-0 mt-0.5">
            <div className="relative">
              <Lightbulb className={`w-4 h-4 ${style.text}`} />
              <span className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ${style.dot} animate-pulse`} />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-300">Velion AI</span>
              {showNewBadge && (
                <span className="text-[8px] font-black px-1.5 py-0.5 rounded-full bg-amber-500 text-zinc-900 animate-bounce flex items-center gap-0.5" data-testid="perf-new-badge">
                  <Sparkles className="w-2.5 h-2.5" /> NUOVO
                </span>
              )}
              {recentHoldRatio != null && (
                <span className={`text-[9px] font-bold ${recentHoldRatio >= 0.85 ? 'text-emerald-400' : recentHoldRatio >= 0.55 ? 'text-yellow-400' : 'text-rose-400'} ml-auto`}>
                  Hold: {Math.round(recentHoldRatio * 100)}%
                </span>
              )}
            </div>
            <div className={`text-xs leading-relaxed ${style.text}`}>
              {performance.message}
            </div>
            <div className="text-[9px] text-zinc-500 mt-1.5 italic">
              Aggiornato ogni ora · {cls.toUpperCase()}
            </div>
          </div>
        </div>
      </div>

      {/* Imminent withdraw risk alert */}
      {performance.is_imminent_withdraw_risk && (
        <div className="rounded-xl bg-rose-950/40 ring-1 ring-rose-700/50 p-2.5" data-testid="imminent-withdraw-alert">
          <div className="flex items-start gap-1.5">
            <AlertTriangle className="w-4 h-4 text-rose-300 flex-shrink-0 mt-0.5 animate-pulse" />
            <div className="text-[11px] text-rose-200 leading-snug">
              <strong>Rischio ritiro imminente</strong>: gli esercenti potrebbero ridurre le sale o programmare un ritiro anticipato del film.
              Considera l'opzione <span className="text-rose-100 font-bold">Ritira tu stesso</span> per limitare le perdite reputazionali.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceMessage;
