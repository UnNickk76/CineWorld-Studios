import React, { useEffect, useRef, useState } from 'react';
import { X, Share2, Play, Pause, Eye, Volume2, VolumeX, Smile, Send } from 'lucide-react';
import { toast } from 'sonner';
import { createTrailerAudio } from './trailerAudio';
import LikeButton, { SystemLikeBadge } from './LikeButton';

const EMOJIS = ['🔥', '🎬', '😱', '😂', '❤️', '🤯', '😴', '🍿', '👀', '🤔'];

/**
 * TrailerPlayerModal — Fullscreen cinematic trailer player.
 * Fase 2: Sound FX procedurali per genere + sistema Reazioni emoji+frase.
 * Mobile gestures: tap=skip, hold=pause, swipe-down=exit, X button always visible.
 */
export default function TrailerPlayerModal({ trailer, contentTitle, contentId, contentGenre = '', contentOwnerId, currentUserId, api, onClose }) {
  const [idx, setIdx] = useState(0);
  const [paused, setPaused] = useState(false);
  const [viewRegistered, setViewRegistered] = useState(false);
  const [audioOn, setAudioOn] = useState(false);
  const [showReactions, setShowReactions] = useState(false);
  const [reactions, setReactions] = useState([]);
  const [selectedEmoji, setSelectedEmoji] = useState('🔥');
  const [reactionText, setReactionText] = useState('');
  const [submittingReaction, setSubmittingReaction] = useState(false);
  const [likes, setLikes] = useState({ count: 0, liked: false, system_count: 0 });
  const frameTimer = useRef(null);
  const holdTimer = useRef(null);
  const startY = useRef(0);
  const audioRef = useRef(null);
  const token = (typeof window !== 'undefined' ? localStorage.getItem('cineworld_token') : null) || '';

  const frames = trailer?.frames || [];
  const cur = frames[idx];
  const isLast = idx >= frames.length - 1;

  // Initialize audio once
  useEffect(() => {
    audioRef.current = createTrailerAudio(contentGenre);
    return () => { audioRef.current?.stop(); };
  }, [contentGenre]);

  // Fetch reactions on mount
  useEffect(() => {
    if (!contentId) return;
    api.get(`/trailers/${contentId}/reactions`).then(r => setReactions(r.data?.reactions || [])).catch(() => {});
    api.get(`/content/${contentId}/likes?context=trailer`).then(r => {
      const tr = r.data?.likes?.trailer;
      if (tr) setLikes({ count: tr.count || 0, liked: tr.liked_by_me || false, system_count: tr.system_count || 0 });
    }).catch(() => {});
  }, [api, contentId]);

  // Auto-advance
  useEffect(() => {
    if (paused || showReactions || !cur) return;
    const dur = cur.duration_ms || 3000;
    frameTimer.current = setTimeout(() => {
      if (idx < frames.length - 1) setIdx(i => i + 1);
      else { setPaused(true); setShowReactions(true); }  // al termine: apre reazioni
    }, dur);
    return () => clearTimeout(frameTimer.current);
  }, [idx, paused, showReactions, cur, frames.length]);

  // Register view once
  useEffect(() => {
    if (!viewRegistered && trailer && contentId) {
      setViewRegistered(true);
      api.post(`/trailers/${contentId}/view`).catch(() => {});
    }
  }, [api, contentId, trailer, viewRegistered]);

  const toggleAudio = (e) => {
    e.stopPropagation();
    if (audioOn) { audioRef.current?.stop(); setAudioOn(false); }
    else { audioRef.current?.start(); setAudioOn(true); }
  };

  // Tap skip (except controls)
  const handleTap = (e) => {
    if (e.target.closest('[data-nocapture]')) return;
    if (showReactions) return;
    if (idx < frames.length - 1) setIdx(i => i + 1);
    else { setPaused(true); setShowReactions(true); }
  };
  const handleHold = () => { holdTimer.current = setTimeout(() => setPaused(true), 300); };
  const handleRelease = () => { clearTimeout(holdTimer.current); if (paused && !showReactions) setPaused(false); };

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

  const submitReaction = async () => {
    if (!selectedEmoji) return;
    setSubmittingReaction(true);
    try {
      const r = await api.post(`/trailers/${contentId}/reactions`, { emoji: selectedEmoji, text: reactionText });
      setReactions(prev => {
        const without = prev.filter(x => x.user_id !== r.data.reaction.user_id);
        return [r.data.reaction, ...without];
      });
      setReactionText('');
      toast.success('Reazione inviata!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally { setSubmittingReaction(false); }
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
      {cur?.image_url && (
        <img
          src={resolveImg(cur.image_url)}
          alt=""
          key={idx}
          className="absolute inset-0 w-full h-full object-cover animate-trailer-kenburns"
          draggable={false}
        />
      )}
      <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/70 pointer-events-none" />

      {cur?.tagline && !showReactions && (
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
          {trailer.highly_anticipated && <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/80 text-white font-bold">🎭 MOLTO ATTESO</span>}
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-300 font-bold uppercase">{trailer.tier}</span>
        </div>
        <div className="flex items-center gap-2">
          {paused && !showReactions && <Pause className="w-4 h-4 text-white/80" />}
          <button onClick={toggleAudio} className="w-8 h-8 rounded-full bg-white/10 backdrop-blur flex items-center justify-center" data-testid="trailer-audio-toggle" title={audioOn ? 'Disattiva audio' : 'Attiva audio'}>
            {audioOn ? <Volume2 className="w-4 h-4 text-white" /> : <VolumeX className="w-4 h-4 text-white" />}
          </button>
          <button onClick={(e) => { e.stopPropagation(); setShowReactions(v => !v); setPaused(true); }} className="w-8 h-8 rounded-full bg-white/10 backdrop-blur flex items-center justify-center" data-testid="trailer-reactions-btn">
            <Smile className="w-4 h-4 text-white" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); shareUrl(); }} className="w-8 h-8 rounded-full bg-white/10 backdrop-blur flex items-center justify-center" data-testid="trailer-share-btn">
            <Share2 className="w-4 h-4 text-white" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); onClose?.(); }} className="w-8 h-8 rounded-full bg-white/10 backdrop-blur flex items-center justify-center" data-testid="trailer-close-btn">
            <X className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>

      {/* Reactions panel — appare a fine trailer o on-demand */}
      {showReactions && (
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black via-black/95 to-transparent pt-8 pb-4 px-4" data-nocapture onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-[14px] font-bold text-white">La tua reazione</h3>
            <span className="text-[10px] text-gray-400">{reactions.length} reazioni</span>
          </div>
          {/* Emoji picker */}
          <div className="flex gap-1 overflow-x-auto pb-2 mb-2" data-testid="trailer-emoji-picker">
            {EMOJIS.map(e => (
              <button
                key={e}
                onClick={() => setSelectedEmoji(e)}
                className={`flex-shrink-0 w-10 h-10 rounded-lg text-xl flex items-center justify-center transition-all ${selectedEmoji === e ? 'bg-yellow-500/30 border-2 border-yellow-400 scale-110' : 'bg-white/5 border border-white/10'}`}>
                {e}
              </button>
            ))}
          </div>
          {/* Text input + send */}
          <div className="flex items-center gap-2 mb-3">
            <input
              value={reactionText}
              onChange={e => setReactionText(e.target.value.slice(0, 30))}
              placeholder="Aggiungi una frase (max 30)"
              className="flex-1 bg-white/5 border border-white/10 rounded-full px-3 py-2 text-[12px] text-white placeholder:text-gray-500 focus:outline-none focus:border-yellow-500/50"
              data-testid="trailer-reaction-input"
            />
            <span className="text-[9px] text-gray-500">{reactionText.length}/30</span>
            <button
              onClick={submitReaction}
              disabled={submittingReaction || !selectedEmoji}
              className="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center disabled:opacity-40"
              data-testid="trailer-reaction-submit">
              <Send className="w-4 h-4 text-black" />
            </button>
          </div>
          {/* Live reactions list */}
          <div className="max-h-32 overflow-y-auto space-y-1.5" data-testid="trailer-reactions-list">
            {reactions.length === 0 ? (
              <p className="text-center text-[10px] text-gray-500 py-3">Nessuna reazione ancora. Sii il primo!</p>
            ) : reactions.slice(0, 15).map((r, i) => (
              <div key={`${r.user_id}-${i}`} className="flex items-center gap-2 bg-white/[0.04] rounded-lg px-2 py-1.5 border border-white/5">
                <span className="text-lg">{r.emoji}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-bold text-yellow-300 truncate">{r.nickname}</p>
                  {r.text && <p className="text-[10px] text-gray-300 truncate">{r.text}</p>}
                </div>
              </div>
            ))}
          </div>
          <button onClick={() => { setShowReactions(false); setPaused(false); if (isLast) onClose?.(); }} className="w-full mt-2 py-2 text-[10px] text-gray-500 hover:text-yellow-400">
            {isLast ? 'Chiudi trailer' : 'Continua a guardare'}
          </button>
        </div>
      )}

      {/* Bottom hint + likes row (se reazioni chiuse) */}
      {!showReactions && (
        <>
          <div className="absolute bottom-14 left-0 right-0 flex items-center justify-between px-4 pointer-events-none" data-testid="trailer-player-likes">
            <div className="flex items-center gap-1 pointer-events-auto">
              <LikeButton
                contentId={contentId}
                context="trailer"
                api={api}
                count={likes.count}
                liked={likes.liked}
                disabled={contentOwnerId === currentUserId}
                onChange={s => setLikes(prev => ({ ...prev, count: s.count, liked: s.liked, system_count: s.system_count ?? prev.system_count }))}
                variant="chip"
              />
            </div>
            <div className="pointer-events-auto">
              <SystemLikeBadge count={likes.system_count} variant="chip" />
            </div>
          </div>
          <div className="absolute bottom-4 left-0 right-0 text-center text-[9px] text-white/40 pointer-events-none">
            Tocca per saltare · Tieni premuto per pausa · Scorri giù per uscire
          </div>
        </>
      )}

      <style>{`
        @keyframes trailer-kenburns { 0%{transform:scale(1.02) translate(0,0)} 100%{transform:scale(1.08) translate(-1%,-1%)} }
        .animate-trailer-kenburns { animation: trailer-kenburns linear forwards; animation-duration: ${cur?.duration_ms || 3000}ms; }
        @keyframes trailer-fade { 0%{opacity:0; transform: translateY(6px)} 20%,80%{opacity:1; transform: translateY(0)} 100%{opacity:0; transform: translateY(-4px)} }
        .animate-trailer-fade { animation: trailer-fade ease-in-out forwards; animation-duration: ${cur?.duration_ms || 3000}ms; }
      `}</style>
    </div>
  );
}
