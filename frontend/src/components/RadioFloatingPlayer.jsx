// CineWorld Studio's — Floating mini radio player.
//
// • Cerchio rosso ancorato in basso a SINISTRA, poco sopra la bottom-navbar.
// • Trascinabile (useDraggable) — posizione salvata in localStorage.
// • Mini equalizer in alto + play/pause al centro (senza sovrapporsi).
// • ⬆ in un pallino BLU in alto a destra → apre il popup di selezione
//   stazioni in qualsiasi pagina (RadioStationsPopup).
// • ✕ in alto a sinistra → ferma la radio e nasconde il widget.

import React, { useState } from 'react';
import { useRadio } from '../contexts/RadioContext';
import { Play, Pause, X, Loader2, ListMusic } from 'lucide-react';
import { useDraggable } from '../hooks/useDraggable';
import { RadioStationsPopup } from './RadioStationsPopup';

function MiniEqualizer({ active }) {
  return (
    <div className="flex items-end justify-center gap-[2px] h-[18px] w-[28px]" aria-hidden>
      {[0, 1, 2, 3, 4, 5, 6].map(i => (
        <span
          key={i}
          className="w-[2px] rounded-sm bg-gradient-to-t from-amber-300 to-yellow-100"
          style={{
            height: active ? '100%' : '30%',
            animation: active ? `miniEqBar 0.75s ease-in-out ${i * 0.07}s infinite alternate` : 'none',
            transformOrigin: 'bottom',
          }}
        />
      ))}
      <style>{`
        @keyframes miniEqBar {
          0% { transform: scaleY(0.25); }
          50% { transform: scaleY(1); }
          100% { transform: scaleY(0.35); }
        }
      `}</style>
    </div>
  );
}

export function RadioFloatingPlayer() {
  const { currentStation, isPlaying, loading, toggle, stop } = useRadio();
  const [popupOpen, setPopupOpen] = useState(false);
  const { dragProps, isDragging } = useDraggable({
    storageKey: 'cw_radio_player_pos_v2',  // nuovo key: reset della vecchia posizione
    size: 64,
    anchor: 'left',
  });

  if (!currentStation) return null;

  const handleToggle = (e) => { e.stopPropagation(); toggle(); };
  const handleStop = (e) => { e.stopPropagation(); stop(); };
  const handleOpenStations = (e) => { e.stopPropagation(); setPopupOpen(true); };

  return (
    <>
    <div
      data-testid="radio-floating-player"
      {...dragProps}
      className="fixed z-[58] left-3 select-none
                 bottom-[calc(env(safe-area-inset-bottom)+76px)]"
    >
      <div className="relative" style={{ animation: isDragging ? 'none' : 'radioFloatIn 0.4s ease-out' }}>
        {/* Glow ring (più intenso in play) */}
        <div
          className={`absolute inset-0 rounded-full pointer-events-none ${isPlaying ? 'animate-[radioGlow_1.8s_ease-in-out_infinite]' : ''}`}
          style={{
            boxShadow: isPlaying
              ? '0 0 18px 6px rgba(239,68,68,0.55), 0 0 36px 10px rgba(239,68,68,0.30)'
              : '0 0 10px 2px rgba(239,68,68,0.25)',
          }}
          aria-hidden
        />

        {/* Cerchio rosso */}
        <div
          className={`relative w-16 h-16 rounded-full
                     bg-gradient-to-br from-red-500 via-red-600 to-red-800
                     border-2 ${isPlaying ? 'border-amber-300' : 'border-red-300/60'}
                     shadow-xl shadow-red-900/60
                     flex flex-col items-center overflow-visible pt-1.5`}
        >
          {/* Equalizer in alto, mai coperto */}
          <div className="pointer-events-none">
            <MiniEqualizer active={isPlaying} />
          </div>

          {/* Play/pause subito sotto */}
          <button
            onClick={handleToggle}
            data-no-drag="true"
            data-testid="radio-floating-toggle"
            className="mt-[3px] w-8 h-8 rounded-full bg-white/95 hover:bg-white text-red-600 flex items-center justify-center active:scale-90 transition shadow"
            aria-label={isPlaying ? 'Metti in pausa la radio' : 'Riproduci la radio'}
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
          </button>

          {/* ✕ in alto a sinistra — ferma radio e chiude widget */}
          <button
            onClick={handleStop}
            data-no-drag="true"
            data-testid="radio-floating-close"
            className="absolute -top-1 -left-1 w-5 h-5 rounded-full bg-gray-900/95 hover:bg-gray-800 text-white/90 flex items-center justify-center border border-white/25 active:scale-90 transition shadow"
            aria-label="Spegni e chiudi la radio"
          >
            <X className="w-3 h-3" />
          </button>

          {/* ⬆ pallino BLU in alto a destra — apre popup selezione stazioni */}
          <button
            onClick={handleOpenStations}
            data-no-drag="true"
            data-testid="radio-floating-stations"
            className="absolute -top-1 -right-1 w-6 h-6 rounded-full
                       bg-gradient-to-br from-sky-400 to-blue-600
                       flex items-center justify-center
                       border-2 border-white/80
                       active:scale-90 transition shadow-lg shadow-blue-900/50
                       animate-[stationPulse_2.2s_ease-in-out_infinite]"
            aria-label="Apri selezione stazioni radio"
          >
            <ListMusic className="w-3 h-3 text-white" strokeWidth={3} />
          </button>
        </div>

        {/* Chip nome stazione sotto */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 whitespace-nowrap max-w-[128px] overflow-hidden pointer-events-none">
          <p className="text-[9px] text-white/90 font-semibold bg-black/60 backdrop-blur-sm px-1.5 py-0.5 rounded truncate text-center">
            {currentStation.emoji} {currentStation.name}
          </p>
        </div>
      </div>

      <style>{`
        @keyframes radioFloatIn {
          from { transform: translateY(24px) scale(0.85); opacity: 0; }
          to { transform: translateY(0) scale(1); opacity: 1; }
        }
        @keyframes radioGlow {
          0%, 100% { box-shadow: 0 0 18px 6px rgba(239,68,68,0.55), 0 0 36px 10px rgba(239,68,68,0.30); }
          50% { box-shadow: 0 0 28px 9px rgba(239,68,68,0.75), 0 0 54px 18px rgba(239,68,68,0.45); }
        }
        @keyframes stationPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.7); transform: scale(1); }
          50% { box-shadow: 0 0 0 6px rgba(59,130,246,0); transform: scale(1.06); }
        }
      `}</style>
    </div>

    {/* Popup selezione stazioni (portale a document.body) */}
    <RadioStationsPopup open={popupOpen} onClose={() => setPopupOpen(false)} />
    </>
  );
}
