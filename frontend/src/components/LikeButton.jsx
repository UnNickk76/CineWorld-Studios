import React, { useEffect, useState, useRef, useContext } from 'react';
import { Heart, User } from 'lucide-react';
import RecentLikesPopup from './RecentLikesPopup';
import { AuthContext } from '../contexts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const avatarSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

const fmt = (n) => {
  if (n == null) return '0';
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return String(n);
};

const MILESTONES = [100, 500, 1000, 5000];
const LONG_PRESS_MS = 500;

/**
 * LikeButton — red heart with user likes. Long-press (or right-click on desktop)
 * opens a popup with the latest 20 likers (avatar+nick+timestamp).
 * Shows 2 overlapping avatars preview next to count if any likes exist.
 */
export default function LikeButton({ contentId, context, api, count = 0, liked = false, onChange, variant = 'pill', disabled = false, testId }) {
  const { api: ctxApi } = useContext(AuthContext);
  const effectiveApi = api || ctxApi;
  const [busy, setBusy] = useState(false);
  const [burst, setBurst] = useState(false);
  const [localCount, setLocalCount] = useState(count);
  const [localLiked, setLocalLiked] = useState(liked);
  const [showRecent, setShowRecent] = useState(false);
  const [previewAvatars, setPreviewAvatars] = useState([]);

  const longPressTimer = useRef(null);
  const longPressTriggered = useRef(false);

  useEffect(() => { setLocalCount(count); setLocalLiked(liked); }, [count, liked]);

  // Fetch first 2 avatars for preview (only if count > 0)
  useEffect(() => {
    if (!contentId || !context || !effectiveApi) return;
    if (localCount <= 0) { setPreviewAvatars([]); return; }
    let cancelled = false;
    effectiveApi.get(`/content/${contentId}/likes/recent`, { params: { context, limit: 2 } })
      .then(r => { if (!cancelled) setPreviewAvatars(r.data.likers || []); })
      .catch(() => { if (!cancelled) setPreviewAvatars([]); });
    return () => { cancelled = true; };
  }, [contentId, context, effectiveApi, localCount]);

  const doToggleLike = async () => {
    if (busy || disabled || !contentId) return;
    setBusy(true);
    const wasLiked = localLiked;
    const optimisticCount = localCount + (wasLiked ? -1 : 1);
    setLocalLiked(!wasLiked); setLocalCount(Math.max(0, optimisticCount));
    try {
      const r = await effectiveApi.post(`/content/${contentId}/like`, { context });
      const newCount = r.data?.count ?? optimisticCount;
      const newLiked = !!r.data?.liked;
      setLocalCount(newCount); setLocalLiked(newLiked);
      onChange?.({ count: newCount, liked: newLiked, system_count: r.data?.system_count });
      if (newLiked && MILESTONES.includes(newCount)) {
        setBurst(true);
        setTimeout(() => setBurst(false), 1400);
      }
    } catch (err) {
      setLocalLiked(wasLiked); setLocalCount(count);
      const msg = err?.response?.data?.detail || 'Errore like';
      import('sonner').then(({ toast }) => toast.error(msg)).catch(() => {});
    } finally { setBusy(false); }
  };

  const startLongPress = (e) => {
    longPressTriggered.current = false;
    clearTimeout(longPressTimer.current);
    longPressTimer.current = setTimeout(() => {
      longPressTriggered.current = true;
      setShowRecent(true);
    }, LONG_PRESS_MS);
  };

  const cancelLongPress = () => {
    clearTimeout(longPressTimer.current);
  };

  const onClick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    if (longPressTriggered.current) {
      longPressTriggered.current = false;
      return;
    }
    doToggleLike();
  };

  const onContextMenu = (e) => {
    // Right-click opens recent likes on desktop
    e.preventDefault();
    e.stopPropagation();
    setShowRecent(true);
  };

  const baseCls = variant === 'chip'
    ? 'inline-flex items-center gap-1 px-2 py-1 rounded-full bg-black/30 backdrop-blur-sm border border-white/10'
    : 'inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-black/40 backdrop-blur border border-white/15 shadow';

  return (
    <>
      <button
        onClick={onClick}
        onContextMenu={onContextMenu}
        onTouchStart={startLongPress}
        onTouchEnd={cancelLongPress}
        onTouchCancel={cancelLongPress}
        onTouchMove={cancelLongPress}
        onMouseDown={startLongPress}
        onMouseUp={cancelLongPress}
        onMouseLeave={cancelLongPress}
        disabled={busy}
        className={`${baseCls} relative transition-transform active:scale-95 ${disabled ? 'opacity-90' : 'hover:scale-105'} select-none touch-none`}
        title={disabled ? 'Tieni premuto per vedere chi ha messo like' : (localLiked ? 'Tap: togli like • Tieni premuto: vedi chi' : 'Tap: metti like • Tieni premuto: vedi chi')}
        data-testid={testId || `like-btn-${context}`}
      >
        <Heart className={`w-4 h-4 transition-all ${localLiked ? 'fill-red-500 text-red-500 scale-110' : 'text-white/90'}`} />
        <span className={`text-[11px] font-bold ${localLiked ? 'text-red-400' : 'text-white/90'}`}>{fmt(localCount)}</span>
        {/* overlapping avatars preview */}
        {previewAvatars.length > 0 && (
          <span className="flex -space-x-1.5 ml-1" data-testid="like-preview-avatars">
            {previewAvatars.slice(0, 2).map((p, i) => (
              <span key={i} className="w-4 h-4 rounded-full bg-gray-700 border border-black/60 overflow-hidden flex items-center justify-center flex-shrink-0">
                {p.avatar_url ? (
                  <img src={avatarSrc(p.avatar_url)} alt="" className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                ) : (
                  <User className="w-2.5 h-2.5 text-gray-500" />
                )}
              </span>
            ))}
          </span>
        )}
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

      <RecentLikesPopup
        open={showRecent}
        onClose={() => setShowRecent(false)}
        contentId={contentId}
        context={context}
      />
    </>
  );
}

/**
 * SystemLikeBadge — blue heart, read-only, represents system reactions (hype-based).
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
 * PreReleaseSnapshotBadge — trophy with Prossimamente totals.
 */
export function PreReleaseSnapshotBadge({ snapshot, context }) {
  if (!snapshot) return null;
  const s = snapshot[context];
  if (!s) return null;
  const total = (s.real || 0) + (s.system || 0);
  if (total === 0) return null;
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-yellow-500/15 border border-yellow-500/30" title={`Snapshot Prossimamente: ${s.real} reali + ${s.system} sistema`} data-testid={`snapshot-badge-${context}`}>
      <span className="text-[9px] font-bold text-yellow-300">{fmt(total)}</span>
    </span>
  );
}
