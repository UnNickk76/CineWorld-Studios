// CineWorld Studio's — Popup di selezione stazioni radio.
//
// Modal a schermo intero richiamabile ovunque nell'app dal pallino blu
// sopra al cerchio radio fluttuante. Riproduce lo stesso elenco che c'è
// dentro "La Mia TV", ma in versione overlay con backdrop scuro.

import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useRadio } from '../contexts/RadioContext';
import { X, Radio as RadioIcon } from 'lucide-react';

export function RadioStationsPopup({ open, onClose }) {
  const { stations, currentStation, play } = useRadio();

  // Chiusura con tasto ESC + blocco scroll del body quando aperto
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  const handlePick = (st) => {
    play(st);
    onClose?.();
  };

  return createPortal(
    <div
      data-testid="radio-stations-popup"
      className="fixed inset-0 z-[200] flex items-end sm:items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-md animate-[popupFade_0.25s_ease-out]" />

      {/* Pannello */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-md mx-auto rounded-t-2xl sm:rounded-2xl
                   bg-gradient-to-br from-[#1a0b0f] via-[#120a18] to-[#0a0a0b]
                   border-t border-red-500/30 sm:border border-red-500/30
                   shadow-2xl shadow-red-900/40
                   max-h-[75vh] overflow-hidden flex flex-col
                   animate-[popupSlide_0.3s_ease-out]"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-gradient-to-r from-red-600/25 via-transparent to-transparent">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-red-500/20 border border-red-500/40 flex items-center justify-center shrink-0">
              <RadioIcon className="w-4 h-4 text-red-300" />
            </div>
            <div className="min-w-0">
              <p className="text-[9px] font-bold tracking-[0.2em] uppercase text-red-300/80">Radio Live</p>
              <p className="text-sm font-bold text-white truncate">Scegli una stazione</p>
            </div>
          </div>
          <button
            onClick={onClose}
            data-testid="radio-popup-close"
            className="shrink-0 w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 text-white flex items-center justify-center active:scale-90 transition"
            aria-label="Chiudi selezione radio"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Lista scrollabile */}
        <div className="overflow-y-auto px-3 py-3 grid grid-cols-2 gap-2">
          {stations.map((st) => {
            const active = currentStation?.id === st.id;
            return (
              <button
                key={st.id}
                onClick={() => handlePick(st)}
                data-testid={`radio-popup-station-${st.id}`}
                className={`text-left px-2.5 py-2 rounded-lg border transition active:scale-95
                  ${active
                    ? 'bg-red-500/15 border-red-400/60 text-white ring-1 ring-red-400/40'
                    : 'bg-white/5 border-white/5 hover:bg-white/10 text-gray-200'}`}
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-sm leading-none">{st.emoji}</span>
                  <span className="text-[11px] font-semibold truncate">{st.name}</span>
                </div>
                <p className="text-[9px] text-gray-400 truncate mt-0.5">{st.genre}</p>
              </button>
            );
          })}
        </div>

        <div className="px-4 py-2 text-[10px] text-gray-500 border-t border-white/5 text-center">
          {stations.length} stazioni disponibili
        </div>
      </div>

      <style>{`
        @keyframes popupFade {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes popupSlide {
          from { transform: translateY(24px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>
    </div>,
    document.body
  );
}
