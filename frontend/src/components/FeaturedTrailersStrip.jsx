import React, { useContext, useEffect, useState } from 'react';
import { Play, Flame, Crown, Sparkles } from 'lucide-react';
import { AuthContext } from '../contexts';
import TrailerPlayerModal from './TrailerPlayerModal';

/**
 * FeaturedTrailersStrip — widget per Dashboard che mostra i trailer
 * Cinematico+PRO con trending_boost_until attivo (ultimi 72h).
 */
export default function FeaturedTrailersStrip() {
  const { api, user } = useContext(AuthContext) || {};
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [trailerData, setTrailerData] = useState(null);

  useEffect(() => {
    if (!api) return;
    api.get('/featured/trailers').then(r => setItems(r.data?.items || [])).catch(() => {});
  }, [api]);

  const openTrailer = async (item) => {
    try {
      const r = await api.get(`/trailers/${item.content_id}`);
      if (r.data?.trailer) {
        setTrailerData(r.data.trailer);
        setSelected(item);
      }
    } catch { /* */ }
  };

  const resolveImg = (url) => {
    if (!url) return null;
    if (url.startsWith('data:') || url.startsWith('http')) return url;
    const token = localStorage.getItem('token') || '';
    if (url.startsWith('/api/')) {
      const sep = url.includes('?') ? '&' : '?';
      return `${process.env.REACT_APP_BACKEND_URL}${url}${sep}auth=${encodeURIComponent(token)}`;
    }
    return `${process.env.REACT_APP_BACKEND_URL}/api/trailers/files/${url}?auth=${encodeURIComponent(token)}`;
  };

  if (!items.length) return null;

  return (
    <div className="mb-4" data-testid="featured-trailers-strip">
      <div className="flex items-center gap-2 mb-2 px-1">
        <Flame className="w-4 h-4 text-red-400" />
        <h3 className="text-[12px] font-black text-white uppercase tracking-wider">Trailer da non perdere</h3>
        <span className="text-[9px] text-gray-500">ultime 72h</span>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-2 px-1 -mx-1 snap-x">
        {items.map(it => {
          const TierIcon = it.tier === 'pro' ? Crown : Sparkles;
          const posterUrl = it.poster_url && (it.poster_url.startsWith('http') || it.poster_url.startsWith('data:')) ? it.poster_url : (it.poster_url ? `${process.env.REACT_APP_BACKEND_URL}${it.poster_url}` : null);
          const fallbackImg = resolveImg(it.first_frame_path);
          return (
            <button
              key={it.content_id}
              onClick={() => openTrailer(it)}
              className="snap-start flex-shrink-0 w-32 rounded-xl overflow-hidden border border-yellow-500/25 bg-black/40 text-left hover:scale-[1.03] transition-transform"
              data-testid={`featured-trailer-${it.content_id}`}>
              <div className="relative aspect-[2/3] bg-gray-900">
                {(posterUrl || fallbackImg) && (
                  <img src={posterUrl || fallbackImg} alt="" className="absolute inset-0 w-full h-full object-cover" onError={e => { e.target.style.display = 'none'; }} />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent" />
                <div className="absolute top-1 right-1 flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-yellow-500/30 border border-yellow-400/40">
                  <TierIcon className="w-2.5 h-2.5 text-yellow-300" />
                  <span className="text-[8px] font-black text-yellow-300 uppercase">{it.tier}</span>
                </div>
                {it.trending && <span className="absolute top-1 left-1 px-1.5 py-0.5 rounded-full bg-red-500/80 text-[8px] font-bold text-white">🔥</span>}
                <div className="absolute bottom-1 left-1 right-1">
                  <p className="text-[10px] font-bold text-white truncate">{it.title}</p>
                  {it.owner?.nickname && <p className="text-[8px] text-gray-400 truncate">di {it.owner.nickname}</p>}
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full bg-yellow-500/90 flex items-center justify-center">
                    <Play className="w-4 h-4 text-black fill-black" />
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
      {selected && trailerData && (
        <TrailerPlayerModal
          trailer={trailerData}
          contentTitle={selected.title}
          contentGenre={selected.genre || ''}
          contentId={selected.content_id}
          contentOwnerId={selected.owner && null}
          currentUserId={user?.id}
          api={api}
          onClose={() => { setSelected(null); setTrailerData(null); }}
        />
      )}
    </div>
  );
}
