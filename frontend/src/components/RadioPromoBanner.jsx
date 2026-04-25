// CineWorld Studio's — Radio Promo Banner (sticky, always visible when active)
//
// New UX (18/04/2026):
// • ALWAYS visible when banner.should_show === true (not gated by isPlaying).
// • Semi-transparent, sits above bottom nav in ALL pages.
// • Click behavior:
//     - user_has_tv=false → navigates to /infrastructure?promo=radio (applies 80% off),
//                           then dismisses the banner permanently.
//     - user_has_tv=true  → just dismisses the banner (no navigation).
// • Small "X" on the right also dismisses permanently.

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useRadio } from '../contexts/RadioContext';
import { X, Radio, Tv, Sparkles } from 'lucide-react';

export function RadioPromoBanner() {
  const { banner, dismissBanner } = useRadio();
  const navigate = useNavigate();
  const location = useLocation();

  // Hide on auth/login screens (no token yet)
  if (!banner?.should_show) return null;
  if (['/auth', '/recovery/password', '/recovery/nickname', '/reset-password'].some(p => location.pathname.startsWith(p))) {
    return null;
  }

  const handleClick = () => {
    if (banner.user_has_tv) {
      // Already owns a TV: just dismiss, no redirect
      dismissBanner();
    } else {
      // No TV: go to infrastructure with the promo flag, then dismiss
      navigate('/infrastructure?promo=radio');
      dismissBanner();
    }
  };

  const handleClose = (e) => {
    e.stopPropagation();
    dismissBanner();
  };

  return (
    <div
      data-testid="radio-promo-banner"
      onClick={handleClick}
      className="fixed left-1/2 -translate-x-1/2 z-[55] cursor-pointer select-none
                 bottom-[calc(env(safe-area-inset-bottom)+68px)]
                 w-[calc(100vw-12px)] max-w-md
                 backdrop-blur-md bg-gradient-to-r from-red-600/55 via-pink-600/50 to-amber-500/55
                 border border-white/15 rounded-xl shadow-lg shadow-black/40
                 animate-[promoFadeUp_0.45s_ease-out]"
    >
      <div className="flex items-center gap-2 px-3 py-2">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-white/15 shrink-0">
          <Radio className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 mb-0.5">
            <Sparkles className="w-3 h-3 text-yellow-200" />
            <span className="text-[9px] font-bold text-yellow-100 tracking-[0.15em] uppercase">Radio Promo</span>
            <span className="ml-auto px-1.5 py-0.5 rounded bg-black/40 text-[9px] font-mono font-bold text-yellow-200">
              -{banner.discount_percent || 80}%
            </span>
          </div>
          {banner.user_has_tv ? (
            <p className="text-[11px] font-semibold text-white leading-tight truncate">
              <Tv className="w-3 h-3 inline mr-0.5" /> Hai già la tua Emittente TV — ascolta la radio in La Mia TV!
            </p>
          ) : (
            <p className="text-[11px] font-semibold text-white leading-tight truncate">
              <Tv className="w-3 h-3 inline mr-0.5" /> 80% di sconto: soldi, crediti, livello, fama — tocca!
            </p>
          )}
        </div>
        <button
          onClick={handleClose}
          data-testid="radio-promo-banner-close"
          className="shrink-0 w-6 h-6 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center text-white/90 active:scale-90 transition"
          aria-label="Chiudi banner"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      <style>{`
        @keyframes promoFadeUp {
          from { transform: translate(-50%, 80%); opacity: 0; }
          to { transform: translate(-50%, 0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
