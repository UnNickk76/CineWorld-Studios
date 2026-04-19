import React, { useEffect, useRef, useState } from 'react';
import { X, Share2, Play, Pause, Eye } from 'lucide-react';
import { toast } from 'sonner';

/**
 * TrailerPlayerModal — Fullscreen cinematic trailer player.
 * Mobile gestures: tap=skip, hold=pause, swipe-down=exit, X button always visible.
 * Plays frames with dynamic cadence (backend-provided duration_ms per frame).
 */
export default function TrailerPlayerModal({ trailer, contentTitle, contentId, api, onClose }) {
  const [idx, setIdx] = useState(0);
  const [paused, setPaused] = useState(false);
  const [viewRegistered, setViewRegistered] = useState(false);
  const frameTimer = useRef(null);
  const holdTimer = useRef(null);
  const startY = useRef(0);
  const token = (typeof window !== 'undefined' ? localStorage.getItem('token') : null) || '';

  const frames = trailer?.frames || [];
  const cur = frames[idx];
  const isLast = idx >= frames.length - 1;

  // Auto-advance
  useEffect(() => {
    if (paused || !cur) return;
    const dur = cur.duration_ms || 3000;
    frameTimer.current = setTimeout(() => {
      if (idx < frames.length - 1) setIdx(i => i + 1);
      else onClose?.();
    }, dur);
    return () => clearTimeout(frameTimer.current);
  }, [idx, paused, cur, frames.length, onClose]);

  // Register view once
  useEffect(() => {
    if (!viewRegistered && trailer && contentId) {
      setViewRegistered(true);
      api.post(`/trailers/${contentId}/view`).catch(() => {});
    }
  }, [api, contentId, trailer, viewRegistered]);

  // Tap skip (except on X button)
  const handleTap = (e) => {
    if (e.target.closest('[data-nocapture]')) return;
    if (idx < frames.length - 1) setIdx(i => i + 1);
    else onClose?.();
  };
  const handleHold = () => { holdTimer.current = setTimeout(() => setPaused(true), 300); };
  const handleRelease = () => { clearTimeout(holdTimer.current); if (paused) setPaused(false); };

  // Swipe down to exit
  const onTouchStart = (e) => { startY.current = e.touches[0].clientY; handleHold(); };
  const onTouchEnd = (e) => {
    handleRelease();
    const dy = e.changedTouches[0].clientY - startY.current;
    if (dy > 80) onClose?.();
  };

  const resolveImg = (url) => {
    if (!url) return null;
    if (url.startsWith('data:') || url.startsWith('http')) return url;
    if (url.startsWith('/api/')) {
      const sep = url.includes('?') ? '&' : '?';
      return `${process.env.REACT_APP_BACKEND_URL}${url}${sep}auth=${encodeURIComponent(token)}`;
    }
    return url;
  };

  const shareUrl = () => {
    if (!contentId) return;
    const url = `${window.location.origin}/trailer/${contentId}`;
    if (navigator.share) {
      navigator.share({ title: contentTitle || 'Guarda il trailer', url }).catch(() => {});
    } else {
      navigator.clipboard.writeText(url);
      toast.success('Link trailer copiato!');
    }
  };

  if (!trailer || frames.length === 0) return null;

  return (
    <div
      className="fixed inset-0 z-[200] bg-black select-none touch-none"
      onClick={handleTap}
      onMouseDown={handleHold}
      onMouseUp={handleRelease}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
      data-testid="trailer-player-modal"
    >
      {/* Image layer (ken-burns lieve) */}
      {cur?.image_url && (
        <img
          src={resolveImg(cur.image_url)}
          alt=""
          key={idx}
          className="absolute inset-0 w-full h-full object-cover animate-trailer-kenburns"
          draggable={false}
        />
      )}
      {/* Vignetta */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/70 pointer-events-none" />

      {/* Tagline overlay */}
      {cur?.tagline && (
        <div className="absolute inset-0 flex items-center justify-center px-6 pointer-events-none">
          <p
            key={`t-${idx}`}
            className={`text-center ${isLast ? "font-['Bebas_Neue'] text-5xl tracking-widest text-yellow-400" : "text-white/95 text-xl font-semibold"} drop-shadow-[0_4px_16px_rgba(0,0,0,0.9)] animate-trailer-fade`}
            style={{ textShadow: '0 2px 20px rgba(0,0,0,0.95)' }}
          >
            {cur.tagline}
          </p>
        </div>
      )}

      {/* Progress dots */}
      <div className="absolute top-3 left-0 right-0 flex justify-center gap-1 px-3 pointer-events-none">
        {frames.map((_, i) => (
          <div key={i} className={`h-[2px] rounded-full flex-1 max-w-[40px] ${i < idx ? 'bg-yellow-400' : i === idx ? 'bg-yellow-400/60' : 'bg-white/20'}`} />
        ))}
      </div>

      {/* Top bar */}
      <div className="absolute top-6 left-0 right-0 flex items-center justify-between px-4" data-nocapture>
        <div className="flex items-center gap-2">
          <Eye className="w-3 h-3 text-white/70" />
          <span className="text-[11px] text-white/70">{(trailer.views_count || 0) + (viewRegistered ? 1 : 0)}</span>
          {trailer.trending && <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/80 text-white font-bold">🔥 TRENDING</span>}
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-300 font-bold uppercase">{trailer.tier}</span>
        </div>
        <div className="flex items-center gap-2">
          {paused && <Pause className="w-4 h-4 text-white/80" />}
          <button onClick={(e) => { e.stopPropagation(); shareUrl(); }} className="w-8 h-8 rounded-full bg-white/10 backdrop-blur flex items-center justify-center" data-testid="trailer-share-btn">
            <Share2 className="w-4 h-4 text-white" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); onClose?.(); }} className="w-8 h-8 rounded-full bg-white/10 backdrop-blur flex items-center justify-center" data-testid="trailer-close-btn">
            <X className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>

      {/* Bottom hint */}
      <div className="absolute bottom-4 left-0 right-0 text-center text-[9px] text-white/40 pointer-events-none">
        Tocca per saltare · Tieni premuto per pausa · Scorri giù per uscire
      </div>

      <style>{`
        @keyframes trailer-kenburns { 0%{transform:scale(1.02) translate(0,0)} 100%{transform:scale(1.08) translate(-1%,-1%)} }
        .animate-trailer-kenburns { animation: trailer-kenburns linear forwards; animation-duration: ${cur?.duration_ms || 3000}ms; }
        @keyframes trailer-fade { 0%{opacity:0; transform: translateY(6px)} 20%,80%{opacity:1; transform: translateY(0)} 100%{opacity:0; transform: translateY(-4px)} }
        .animate-trailer-fade { animation: trailer-fade ease-in-out forwards; animation-duration: ${cur?.duration_ms || 3000}ms; }
      `}</style>
    </div>
  );
}
