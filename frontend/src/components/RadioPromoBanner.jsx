// CineWorld Studio's — Radio Promo Banner (sticky, bottom)
// Visible only when banner.should_show = true.
// Disappears on X, on nav click, or after TV infra purchase (backend consumes).

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useRadio } from '../contexts/RadioContext';
import { X, Radio, Tv, Percent } from 'lucide-react';

export function RadioPromoBanner() {
  const { banner, dismissBanner, isPlaying } = useRadio();
  const navigate = useNavigate();

  // Show only if backend flag is active AND radio is currently playing
  if (!banner?.should_show || !isPlaying) return null;

  const handleClick = () => {
    navigate('/infrastructure?promo=radio');
  };

  const handleClose = (e) => {
    e.stopPropagation();
    dismissBanner();
  };

  return (
    <div
      data-testid="radio-promo-banner"
      onClick={handleClick}
      className="fixed left-1/2 -translate-x-1/2 z-[60] cursor-pointer
                 bottom-[calc(env(safe-area-inset-bottom)+76px)]
                 w-[calc(100vw-16px)] max-w-md
                 bg-gradient-to-r from-red-600 via-pink-600 to-amber-500
                 shadow-2xl shadow-red-900/50 rounded-xl border border-white/20
                 backdrop-blur-sm
                 animate-[slideUp_0.4s_ease-out]"
    >
      <div className="flex items-center gap-2 px-3 py-2.5">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-white/20 shrink-0">
          <Radio className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1">
            <span className="text-[10px] font-bold text-yellow-200 tracking-wider uppercase">Radio Promo</span>
            <span className="px-1.5 py-0.5 rounded bg-black/30 text-[9px] font-mono text-yellow-100 flex items-center gap-0.5">
              <Percent className="w-2.5 h-2.5" /> {banner.discount_percent || 80}
            </span>
          </div>
          <p className="text-xs font-bold text-white leading-tight mt-0.5 truncate">
            <Tv className="w-3 h-3 inline mr-1" /> Sconto {banner.discount_percent || 80}% su Emittente TV
          </p>
          <p className="text-[10px] text-white/80 leading-tight truncate">
            Tocca per acquistare la tua TV scontata
          </p>
        </div>
        <button
          onClick={handleClose}
          data-testid="radio-promo-banner-close"
          className="shrink-0 w-7 h-7 rounded-full bg-black/30 hover:bg-black/50 flex items-center justify-center text-white/90 active:scale-90 transition"
          aria-label="Chiudi banner"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <style>{`
        @keyframes slideUp {
          from { transform: translate(-50%, 120%); opacity: 0; }
          to { transform: translate(-50%, 0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
