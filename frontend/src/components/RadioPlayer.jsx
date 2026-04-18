// CineWorld Studio's — In-app Radio Player Widget
// Lives inside La Mia TV (TVStationPage). Full-featured player:
// - Play/pause/next/prev
// - Station list grid
// - Volume slider
// - Animated equalizer bars when playing

import React, { useState } from 'react';
import { useRadio } from '../contexts/RadioContext';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Radio as RadioIcon, Loader2 } from 'lucide-react';

function Equalizer({ active }) {
  // 7-bar CSS equalizer. Bars animate only when `active`.
  return (
    <div className="flex items-end gap-0.5 h-5" aria-hidden>
      {[0, 1, 2, 3, 4, 5, 6].map(i => (
        <span
          key={i}
          className={`w-1 rounded-sm ${active ? 'bg-gradient-to-t from-red-500 via-amber-400 to-yellow-200' : 'bg-gray-700'}`}
          style={{
            height: active ? '100%' : '20%',
            animation: active ? `eqBar 0.9s ease-in-out ${i * 0.08}s infinite alternate` : 'none',
            transformOrigin: 'bottom',
          }}
        />
      ))}
      <style>{`
        @keyframes eqBar {
          0% { transform: scaleY(0.25); }
          50% { transform: scaleY(1); }
          100% { transform: scaleY(0.4); }
        }
      `}</style>
    </div>
  );
}

export function RadioPlayer() {
  const {
    stations, currentStation, isPlaying, loading, volume,
    setVolume, play, toggle, next, prev
  } = useRadio();
  const [listOpen, setListOpen] = useState(false);
  // iOS Safari ignores HTML5 audio.volume programmatic changes — users must
  // use hardware volume buttons. Detect it and show a hint instead of a
  // misleading inert slider.
  const isIOS = useMemo(() => {
    if (typeof navigator === 'undefined') return false;
    const ua = navigator.userAgent || '';
    const platform = navigator.platform || '';
    return /iPad|iPhone|iPod/.test(ua)
      || (platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  }, []);

  return (
    <div
      data-testid="radio-player"
      className="my-4 rounded-2xl overflow-hidden
                 bg-gradient-to-br from-[#1a0b0f] via-[#0f0a15] to-[#0a0a0b]
                 border border-red-500/25 shadow-xl shadow-red-900/20"
    >
      {/* Header */}
      <div className="px-3 py-2.5 bg-gradient-to-r from-red-600/20 via-transparent to-transparent border-b border-white/5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-red-500/15 border border-red-500/30 flex items-center justify-center shrink-0">
              <RadioIcon className="w-4 h-4 text-red-400" />
            </div>
            <div className="min-w-0">
              <p className="text-[9px] font-bold tracking-[0.18em] uppercase text-red-400/90">La Mia Radio</p>
              <p className="text-xs text-white/90 font-semibold truncate">
                {currentStation ? `${currentStation.emoji || '📻'} ${currentStation.name}` : 'Scegli una stazione'}
              </p>
              {currentStation && (
                <p className="text-[10px] text-gray-400 truncate">{currentStation.genre}</p>
              )}
            </div>
          </div>
          <Equalizer active={isPlaying} />
        </div>
      </div>

      {/* Controls */}
      <div className="px-3 py-2.5 flex items-center gap-2">
        <button
          onClick={prev}
          disabled={!currentStation}
          data-testid="radio-prev-btn"
          className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 disabled:opacity-30 flex items-center justify-center text-white/90 active:scale-90 transition"
        >
          <SkipBack className="w-4 h-4" />
        </button>
        <button
          onClick={toggle}
          data-testid="radio-play-btn"
          className="w-10 h-10 rounded-full bg-gradient-to-br from-red-500 to-amber-500 hover:brightness-110 text-white flex items-center justify-center active:scale-95 shadow-lg shadow-red-900/40"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
        </button>
        <button
          onClick={next}
          disabled={!currentStation}
          data-testid="radio-next-btn"
          className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 disabled:opacity-30 flex items-center justify-center text-white/90 active:scale-90 transition"
        >
          <SkipForward className="w-4 h-4" />
        </button>

        {/* Volume — desktop/Android shows slider; iOS shows a hint */}
        {isIOS ? (
          <div
            className="flex items-center gap-1.5 ml-1 flex-1 text-[10px] text-gray-400"
            data-testid="radio-volume-ios-hint"
          >
            <Volume2 className="w-3.5 h-3.5 shrink-0 text-gray-500" />
            <span className="leading-tight truncate">Usa i tasti volume del dispositivo</span>
            <Info className="w-3 h-3 text-gray-600 shrink-0" aria-hidden />
          </div>
        ) : (
          <div className="flex items-center gap-1.5 ml-1 flex-1">
            <button
              onClick={() => setVolume(volume > 0 ? 0 : 0.7)}
              className="text-gray-400 hover:text-white"
              data-testid="radio-volume-btn"
            >
              {volume > 0 ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="w-full h-1 accent-red-500"
              data-testid="radio-volume-slider"
            />
          </div>
        )}
      </div>

      {/* Station picker toggle */}
      <button
        onClick={() => setListOpen(v => !v)}
        className="w-full px-3 py-1.5 text-[11px] text-gray-400 hover:text-white border-t border-white/5 flex items-center justify-between"
        data-testid="radio-stations-toggle"
      >
        <span>📻 {stations.length} stazioni disponibili</span>
        <span className="text-[9px]">{listOpen ? 'CHIUDI ▲' : 'MOSTRA ▼'}</span>
      </button>

      {listOpen && (
        <div className="px-2 pb-2 max-h-48 overflow-y-auto grid grid-cols-2 gap-1.5" data-testid="radio-stations-list">
          {stations.map(st => {
            const active = currentStation?.id === st.id;
            return (
              <button
                key={st.id}
                onClick={() => play(st)}
                data-testid={`radio-station-${st.id}`}
                className={`text-left px-2 py-1.5 rounded-lg border transition active:scale-95
                  ${active
                    ? 'bg-red-500/15 border-red-400/60 text-white'
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
      )}
    </div>
  );
}
