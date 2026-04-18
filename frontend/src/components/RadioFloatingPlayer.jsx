// CineWorld Studio's — Floating mini radio player.
//
// Appears on LEFT side by default (can be dragged anywhere, position persisted).
// A circular red widget that shows:
//   • A 7-bar equalizer at the TOP of the circle (animated when playing)
//   • ⏯ play/pause button below the equalizer (does NOT overlap it)
//   • ✕ close at top-left: stops radio + hides widget
//   • Station name (small chip below the circle)

import React from 'react';
import { useRadio } from '../contexts/RadioContext';
import { Play, Pause, X, Loader2 } from 'lucide-react';
import { useDraggable } from '../hooks/useDraggable';

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
  const { dragProps, isDragging } = useDraggable({
    storageKey: 'cw_radio_player_pos',
    size: 64,
    anchor: 'left',
  });

  // Only render once the user has selected (or is playing) a station
  if (!currentStation) return null;

  const handleToggle = (e) => { e.stopPropagation(); toggle(); };
  const handleStop = (e) => { e.stopPropagation(); stop(); };

  return (
    <div
      data-testid="radio-floating-player"
      {...dragProps}
      className="fixed z-[58] left-3 select-none
                 bottom-[calc(env(safe-area-inset-bottom)+132px)]"
    >
      <div className="relative" style={{ animation: isDragging ? 'none' : 'radioFloatIn 0.4s ease-out' }}>
        {/* Glow ring (stronger when playing) */}
        <div
          className={`absolute inset-0 rounded-full pointer-events-none ${isPlaying ? 'animate-[radioGlow_1.8s_ease-in-out_infinite]' : ''}`}
          style={{
            boxShadow: isPlaying
              ? '0 0 18px 6px rgba(239,68,68,0.55), 0 0 36px 10px rgba(239,68,68,0.30)'
              : '0 0 10px 2px rgba(239,68,68,0.25)',
          }}
          aria-hidden
        />

        {/* Red circle */}
        <div
          className={`relative w-16 h-16 rounded-full
                     bg-gradient-to-br from-red-500 via-red-600 to-red-800
                     border-2 ${isPlaying ? 'border-amber-300' : 'border-red-300/60'}
                     shadow-xl shadow-red-900/60
                     flex flex-col items-center overflow-visible pt-1.5`}
        >
          {/* Equalizer — top area, NEVER covered */}
          <div className="pointer-events-none">
            <MiniEqualizer active={isPlaying} />
          </div>

          {/* Play/pause — placed below equalizer, fully inside the circle */}
          <button
            onClick={handleToggle}
            data-no-drag="true"
            data-testid="radio-floating-toggle"
            className="mt-[3px] w-8 h-8 rounded-full bg-white/95 hover:bg-white text-red-600 flex items-center justify-center active:scale-90 transition shadow"
            aria-label={isPlaying ? 'Metti in pausa la radio' : 'Riproduci la radio'}
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
          </button>

          {/* Close (top-left) — stops radio + hides widget */}
          <button
            onClick={handleStop}
            data-no-drag="true"
            data-testid="radio-floating-close"
            className="absolute -top-1 -left-1 w-5 h-5 rounded-full bg-gray-900/95 hover:bg-gray-800 text-white/90 flex items-center justify-center border border-white/25 active:scale-90 transition shadow"
            aria-label="Spegni e chiudi la radio"
          >
            <X className="w-3 h-3" />
          </button>
        </div>

        {/* Station name chip below */}
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
      `}</style>
    </div>
  );
}
