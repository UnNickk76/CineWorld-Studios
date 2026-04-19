import React, { useEffect, useState } from 'react';
import { Heart } from 'lucide-react';

const fmt = (n) => {
  if (n == null) return '0';
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return String(n);
};

const MILESTONES = [100, 500, 1000, 5000];

/**
 * LikeButton — cuore rosso cliccabile (user likes).
 *
 * Props:
 *  contentId, context ('poster'|'screenplay'|'trailer'), api
 *  count, liked, onChange(newState: {count, liked})
 *  variant: 'pill' (default glass bottom-left) | 'chip' (compact inline)
 *  disabled: boolean
 *  testId: data-testid
 */
export default function LikeButton({ contentId, context, api, count = 0, liked = false, onChange, variant = 'pill', disabled = false, testId }) {
  const [busy, setBusy] = useState(false);
  const [burst, setBurst] = useState(false);
  const [localCount, setLocalCount] = useState(count);
  const [localLiked, setLocalLiked] = useState(liked);

  useEffect(() => { setLocalCount(count); setLocalLiked(liked); }, [count, liked]);

  const handleClick = async (e) => {
    e.stopPropagation();
    if (busy || disabled || !contentId) return;
    setBusy(true);
    const wasLiked = localLiked;
    const optimisticCount = localCount + (wasLiked ? -1 : 1);
    setLocalLiked(!wasLiked); setLocalCount(Math.max(0, optimisticCount));
    try {
      const r = await api.post(`/content/${contentId}/like`, { context });
      const newCount = r.data?.count ?? optimisticCount;
      const newLiked = !!r.data?.liked;
      setLocalCount(newCount); setLocalLiked(newLiked);
      onChange?.({ count: newCount, liked: newLiked, system_count: r.data?.system_count });
      // Burst on milestone crossing
      if (newLiked && MILESTONES.includes(newCount)) {
        setBurst(true);
        setTimeout(() => setBurst(false), 1400);
      }
    } catch (err) {
      // revert
      setLocalLiked(wasLiked); setLocalCount(count);
    } finally { setBusy(false); }
  };

  const baseCls = variant === 'chip'
    ? 'inline-flex items-center gap-1 px-2 py-1 rounded-full bg-black/30 backdrop-blur-sm border border-white/10'
    : 'inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-black/40 backdrop-blur border border-white/15 shadow';

  return (
    <button
      onClick={handleClick}
      disabled={busy || disabled}
      className={`${baseCls} transition-transform active:scale-95 ${disabled ? 'opacity-60 cursor-not-allowed' : 'hover:scale-105'} select-none`}
      title={disabled ? 'Non puoi mettere like ai tuoi contenuti' : (localLiked ? 'Togli like' : 'Metti like')}
      data-testid={testId || `like-btn-${context}`}
    >
      <Heart className={`w-4 h-4 transition-all ${localLiked ? 'fill-red-500 text-red-500 scale-110' : 'text-white/90'}`} />
      <span className={`text-[11px] font-bold ${localLiked ? 'text-red-400' : 'text-white/90'}`}>{fmt(localCount)}</span>
      {burst && (
        <span className="pointer-events-none absolute -top-2 -left-2 -right-2 -bottom-2 flex items-center justify-center">
          {[0, 1, 2, 3, 4].map(i => (
            <Heart key={i} className="absolute w-4 h-4 fill-red-500 text-red-500 animate-like-burst" style={{ animationDelay: `${i * 80}ms`, left: `${20 + i * 12}%` }} />
          ))}
        </span>
      )}
      <style>{`
        @keyframes like-burst { 0%{opacity:1; transform: translateY(0) scale(0.6)} 100%{opacity:0; transform: translateY(-38px) scale(1.2)} }
        .animate-like-burst { animation: like-burst 1.2s ease-out forwards; }
      `}</style>
    </button>
  );
}

/**
 * SystemLikeBadge — cuore blu, read-only, rappresenta reazioni sistema (hype-based).
 */
export function SystemLikeBadge({ count = 0, variant = 'pill', testId }) {
  const baseCls = variant === 'chip'
    ? 'inline-flex items-center gap-1 px-2 py-1 rounded-full bg-black/30 backdrop-blur-sm border border-blue-400/20'
    : 'inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-black/40 backdrop-blur border border-blue-400/25 shadow';
  return (
    <span className={baseCls} title="Reazioni del pubblico stimate dall'hype" data-testid={testId || 'system-like-badge'}>
      <Heart className="w-4 h-4 fill-blue-500 text-blue-500" />
      <span className="text-[11px] font-bold text-blue-300">{fmt(count)}</span>
    </span>
  );
}

/**
 * PreReleaseSnapshotBadge — trofeo fisso con totali Prossimamente.
 */
export function PreReleaseSnapshotBadge({ snapshot, context }) {
  if (!snapshot) return null;
  const s = snapshot[context];
  if (!s) return null;
  const total = (s.real || 0) + (s.system || 0);
  if (total === 0) return null;
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-yellow-500/15 border border-yellow-500/30" title={`Snapshot Prossimamente: ${s.real} reali + ${s.system} sistema`} data-testid={`snapshot-badge-${context}`}>
      <span className="text-[9px] font-bold text-yellow-300">📊 {fmt(total)}</span>
    </span>
  );
}
