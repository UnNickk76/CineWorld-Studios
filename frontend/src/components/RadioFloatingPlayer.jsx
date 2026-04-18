// CineWorld Studio's — Floating mini radio player.
//
// Shows a circular red pulsing widget in the bottom-right corner whenever a
// station is currently selected/playing. Features:
// • Glowing red ring that pulses softly while audio is playing.
// • Mini 5-bar equalizer animated at the top of the circle.
// • Central ⏯ button toggles play/pause WITHOUT closing the widget.
// • Small ✕ in the top-left of the circle stops radio + closes widget.

import React from 'react';
import { useRadio } from '../contexts/RadioContext';
import { Play, Pause, X, Loader2 } from 'lucide-react';

function MiniEqualizer({ active }) {
  return (
    <div className="flex items-end gap-[1px] h-3.5" aria-hidden>
      {[0, 1, 2, 3, 4].map(i => (
        <span
          key={i}
          className="w-[2px] rounded-sm bg-yellow-200"
          style={{
            height: active ? '100%' : '30%',
            animation: active ? `miniEqBar 0.75s ease-in-out ${i * 0.09}s infinite alternate` : 'none',
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

  // Only render once the user has selected (or is playing) a station
  if (!currentStation) return null;

  return (
    <div
      data-testid="radio-floating-player"
      className="fixed z-[58] right-3 select-none
                 bottom-[calc(env(safe-area-inset-bottom)+132px)]"
      style={{ animation: 'radioFloatIn 0.4s ease-out' }}
    >
      <div className="relative">
        {/* Glow ring (stronger when playing) */}
        <div
          className={`absolute inset-0 rounded-full ${isPlaying ? 'animate-[radioGlow_1.8s_ease-in-out_infinite]' : ''}`}
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
                     flex items-center justify-center overflow-visible`}
        >
          {/* Mini equalizer at the top */}
          <div className="absolute top-1.5 left-1/2 -translate-x-1/2">
            <MiniEqualizer active={isPlaying} />
          </div>

          {/* Central play/pause button */}
          <button
            onClick={toggle}
            data-testid="radio-floating-toggle"
            className="relative mt-3 w-9 h-9 rounded-full bg-white/95 hover:bg-white text-red-600 flex items-center justify-center active:scale-90 transition"
            aria-label={isPlaying ? 'Metti in pausa la radio' : 'Riproduci la radio'}
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
          </button>

          {/* Close (top-left) — stops radio + hides widget */}
          <button
            onClick={stop}
            data-testid="radio-floating-close"
            className="absolute -top-1 -left-1 w-5 h-5 rounded-full bg-gray-900/90 hover:bg-gray-800 text-white/90 flex items-center justify-center border border-white/20 active:scale-90 transition shadow"
            aria-label="Spegni e chiudi la radio"
          >
            <X className="w-3 h-3" />
          </button>
        </div>

        {/* Station name below (truncated) */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 whitespace-nowrap max-w-[128px] overflow-hidden">
          <p className="text-[9px] text-white/90 font-semibold bg-black/50 backdrop-blur-sm px-1.5 py-0.5 rounded truncate text-center">
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
