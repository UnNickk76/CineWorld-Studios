import React, { useEffect, useState, useContext, useRef } from 'react';
import { AuthContext } from '../../contexts';
import { Flame, Clock, Play, Loader2, X } from 'lucide-react';
import { toast } from 'sonner';

/**
 * ReHypeWindow — banner/card che appare nella pipeline V3/LAMPO del capitolo successivo
 * quando il cap. precedente sta per uscire dai cinema.
 * - Mostra timer countdown alla finestra
 * - Bottone "Attiva Re-Hype (Gratis)"
 * - Mini-card trailer Cap.1 (idea A)
 * - Badge "+X% bonus", "Cliffhanger boost", "Sold-out bonus"
 */
export default function ReHypeWindow({ sagaId, projectId, onActivated }) {
  const { api } = useContext(AuthContext);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [showTrailer, setShowTrailer] = useState(false);
  const [now, setNow] = useState(Date.now());
  const tickRef = useRef(null);

  useEffect(() => {
    if (!sagaId || !projectId) return;
    let abort = false;
    const fetch = async () => {
      try {
        const r = await api.get(`/sagas/${sagaId}/re-hype/status/${projectId}`);
        if (!abort) setStatus(r.data);
      } catch { /* silent */ }
    };
    fetch();
    const i = setInterval(fetch, 60000);
    return () => { abort = true; clearInterval(i); };
  }, [sagaId, projectId, api]);

  useEffect(() => {
    tickRef.current = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(tickRef.current);
  }, []);

  const activate = async () => {
    setBusy(true);
    try {
      const r = await api.post(`/sagas/${sagaId}/re-hype/activate/${projectId}`);
      toast.success(`🔥 Re-Hype attivata! +${r.data.bonus_pct}% hype per ${r.data.duration_hours}h`);
      // refresh
      const s = await api.get(`/sagas/${sagaId}/re-hype/status/${projectId}`);
      setStatus(s.data);
      onActivated?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore attivazione Re-Hype');
    } finally { setBusy(false); }
  };

  if (!status?.applicable) return null;

  const fmtTime = (ms) => {
    if (ms <= 0) return '0s';
    const total = Math.floor(ms / 1000);
    const d = Math.floor(total / 86400);
    const h = Math.floor((total % 86400) / 3600);
    const m = Math.floor((total % 3600) / 60);
    if (d > 0) return `${d}g ${h}h`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  };

  const windowStart = status.window_start ? new Date(status.window_start).getTime() : null;
  const windowEnd = status.window_end ? new Date(status.window_end).getTime() : null;
  const tilOpen = windowStart ? windowStart - now : null;
  const tilClose = windowEnd ? windowEnd - now : null;

  const isOpen = !!status.open_window;
  const isUsed = !!status.used_already;
  const isActivated = !!status.activated;

  const pf = status.prev_film || {};

  return (
    <>
      <style>{`
        @keyframes flameGlow { 0%, 100% { box-shadow: 0 0 0 0 rgba(251,146,60,0.5), 0 0 18px rgba(251,146,60,0.4); } 50% { box-shadow: 0 0 0 4px rgba(251,146,60,0), 0 0 30px rgba(251,146,60,0.7); } }
        .rehype-glow { animation: flameGlow 2s ease-in-out infinite; }
      `}</style>
      <div className={`rounded-xl border ${isOpen && !isUsed ? 'border-orange-500/50 bg-gradient-to-br from-orange-950/40 via-amber-950/30 to-zinc-900/40 rehype-glow' : 'border-zinc-700 bg-zinc-900/40'} p-3 mb-3`} data-testid="re-hype-window">
        <div className="flex items-center gap-2 mb-2">
          <Flame className={`w-4 h-4 ${isOpen ? 'text-orange-300' : 'text-zinc-500'}`} />
          <span className="text-[10px] uppercase tracking-wider font-bold text-orange-300">RE-HYPE WINDOW</span>
          {isUsed && <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold">ATTIVATA</span>}
        </div>

        {/* Mini-card trailer Cap.1 (idea A) */}
        {pf.trailer && (
          <div className="rounded-lg bg-black/40 border border-orange-500/20 p-2 mb-2 flex items-center gap-2" data-testid="rehype-trailer-card">
            <button
              onClick={() => setShowTrailer(true)}
              className="flex-shrink-0 w-12 h-12 rounded-full bg-orange-500 flex items-center justify-center hover:scale-105 transition-transform"
              data-testid="rehype-watch-prev-trailer"
            >
              <Play className="w-5 h-5 fill-white text-white ml-0.5" />
            </button>
            <div className="flex-1 min-w-0">
              <p className="text-[8px] uppercase text-orange-300 font-bold">Riguarda il Cap. precedente</p>
              <p className="text-[11px] font-bold text-white truncate">{pf.title}</p>
              <p className="text-[8px] text-orange-200/70">CWSv {(pf.cwsv || 0).toFixed(1)}</p>
            </div>
          </div>
        )}

        {/* Stato */}
        {!isOpen && !isUsed && (
          <p className="text-[10px] text-zinc-400">
            <Clock className="w-3 h-3 inline mr-1" />
            Si apre tra <span className="font-bold text-orange-300">{fmtTime(tilOpen)}</span>
          </p>
        )}
        {isOpen && !isUsed && (
          <>
            <p className="text-[10px] text-orange-200 mb-2">
              <Clock className="w-3 h-3 inline mr-1" />
              Finestra aperta · chiude tra <span className="font-bold text-amber-200">{fmtTime(tilClose)}</span>
            </p>
            <div className="flex flex-wrap gap-1 mb-2">
              <span className="px-1.5 py-0.5 rounded bg-orange-500/20 border border-orange-500/40 text-orange-200 text-[9px] font-bold">+{status.bonus_pct}% hype</span>
              <span className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-300 text-[9px] font-bold">{status.duration_hours}h</span>
              {status.cliffhanger_bonus && <span className="px-1.5 py-0.5 rounded bg-rose-500/20 border border-rose-500/40 text-rose-200 text-[9px] font-bold">💥 Cliffhanger +5%</span>}
              {status.sold_out_bonus && <span className="px-1.5 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-200 text-[9px] font-bold">🎟 Sold-out +12h</span>}
            </div>
            <button
              onClick={activate}
              disabled={busy}
              data-testid="rehype-activate-btn"
              className="w-full py-2.5 rounded-lg bg-gradient-to-r from-orange-500 to-red-600 text-white font-black text-xs flex items-center justify-center gap-1.5 hover:scale-[1.02] transition-transform disabled:opacity-50"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Flame className="w-3.5 h-3.5" />}
              {busy ? 'Attivazione…' : 'Attiva Re-Hype · GRATIS'}
            </button>
          </>
        )}
        {isUsed && isActivated && (
          <p className="text-[10px] text-emerald-300">
            <Flame className="w-3 h-3 inline mr-1" />
            Re-Hype attiva fino a <span className="font-bold">{fmtTime(tilClose)}</span> · +{status.bonus_pct}% hype applicato
          </p>
        )}
        {isUsed && !isActivated && (
          <p className="text-[10px] text-zinc-400">Re-Hype già usata per questo capitolo.</p>
        )}
      </div>

      {/* Player trailer Cap.1 modal */}
      {showTrailer && pf.trailer && (
        <div className="fixed inset-0 z-[200] bg-black/90 flex items-center justify-center p-3" onClick={() => setShowTrailer(false)} data-testid="rehype-trailer-modal">
          <div className="relative max-w-md w-full rounded-2xl bg-zinc-950 border border-orange-500/40 p-3" onClick={(e) => e.stopPropagation()}>
            <button onClick={() => setShowTrailer(false)} className="absolute top-2 right-2 text-zinc-400 hover:text-white"><X className="w-4 h-4" /></button>
            <p className="text-xs font-bold text-orange-300 mb-2">Trailer · {pf.title}</p>
            <div className="aspect-video bg-black rounded flex items-center justify-center text-zinc-500 text-xs">
              {pf.trailer.frames?.length > 0 ? (
                <img src={pf.trailer.frames[0]} alt="trailer frame" className="w-full h-full object-cover rounded" />
              ) : (
                'Anteprima non disponibile'
              )}
            </div>
            <p className="text-[9px] text-zinc-500 mt-2">{pf.trailer.duration_seconds || 8}s · {pf.trailer.frames?.length || 0} frame</p>
          </div>
        </div>
      )}
    </>
  );
}
