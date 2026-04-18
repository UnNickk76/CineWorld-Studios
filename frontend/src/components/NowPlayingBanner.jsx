// CineWorld Studio's — Now Playing Banner (ICY metadata)
//
// Transparent sticky banner that appears when radio is playing AND track info
// (artist/title) is available from the ICY proxy. Closable (X) — when closed
// the radio continues playing, the banner simply hides until the user plays
// a new station.

import React, { useRef, useEffect, useState } from 'react';
import { useRadio } from '../contexts/RadioContext';
import { Music2, X } from 'lucide-react';

function useScrollAnimation(text) {
  const containerRef = useRef(null);
  const textRef = useRef(null);
  const [shouldScroll, setShouldScroll] = useState(false);
  const [duration, setDuration] = useState(14);

  useEffect(() => {
    if (!containerRef.current || !textRef.current) return;
    const cw = containerRef.current.clientWidth;
    const tw = textRef.current.scrollWidth;
    if (tw > cw + 4) {
      setShouldScroll(true);
      // Speed ~40px/sec
      setDuration(Math.max(10, Math.round((tw + cw) / 40)));
    } else {
      setShouldScroll(false);
    }
  }, [text]);

  return { containerRef, textRef, shouldScroll, duration };
}

export function NowPlayingBanner() {
  const { currentStation, isPlaying, nowPlaying, dismissNowPlaying } = useRadio();

  const artist = nowPlaying?.artist;
  const title = nowPlaying?.title;
  const hasData = Boolean(artist || title);
  const text = artist && title ? `${artist} — ${title}` : (title || artist || '');
  const { containerRef, textRef, shouldScroll, duration } = useScrollAnimation(text);

  if (!currentStation || !isPlaying || !hasData || nowPlaying?.dismissed) return null;

  return (
    <div
      data-testid="now-playing-banner"
      className="fixed left-1/2 -translate-x-1/2 z-[57] select-none pointer-events-auto
                 bottom-[calc(env(safe-area-inset-bottom)+218px)]
                 w-[calc(100vw-16px)] max-w-sm
                 backdrop-blur-lg bg-gradient-to-r from-black/55 via-red-950/45 to-black/55
                 border border-white/10 rounded-xl shadow-lg shadow-black/40
                 animate-[nowPlayFadeIn_0.45s_ease-out]"
      style={{ overflow: 'hidden' }}
    >
      <div className="flex items-center gap-2 px-2 py-1.5">
        <div className="shrink-0 w-7 h-7 rounded-lg bg-red-500/20 border border-red-400/30 flex items-center justify-center">
          <Music2 className="w-3.5 h-3.5 text-red-300" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[8px] uppercase tracking-[0.22em] text-red-300/80 font-bold leading-none">Now Playing</p>
          <div
            ref={containerRef}
            className="relative mt-0.5 overflow-hidden whitespace-nowrap"
            style={{ maskImage: 'linear-gradient(90deg, transparent 0, black 16px, black calc(100% - 16px), transparent 100%)',
                     WebkitMaskImage: 'linear-gradient(90deg, transparent 0, black 16px, black calc(100% - 16px), transparent 100%)' }}
          >
            <span
              ref={textRef}
              className={`inline-block text-[11px] text-white font-semibold ${shouldScroll ? 'pl-full' : ''}`}
              style={shouldScroll ? {
                animation: `nowPlayScroll ${duration}s linear infinite`,
                paddingLeft: '100%',
              } : undefined}
            >
              {text}
            </span>
          </div>
        </div>
        <button
          onClick={dismissNowPlaying}
          data-testid="now-playing-banner-close"
          className="shrink-0 w-6 h-6 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white/90 active:scale-90 transition"
          aria-label="Nascondi titolo brano"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      <style>{`
        @keyframes nowPlayFadeIn {
          from { transform: translate(-50%, 10px); opacity: 0; }
          to { transform: translate(-50%, 0); opacity: 1; }
        }
        @keyframes nowPlayScroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-100%); }
        }
      `}</style>
    </div>
  );
}
