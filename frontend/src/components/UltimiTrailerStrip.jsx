import React, { useContext, useEffect, useState } from 'react';
import { Play, Clock, Crown, Sparkles, Film } from 'lucide-react';
import { AuthContext } from '../contexts';
import TrailerPlayerModal from './TrailerPlayerModal';

/**
 * UltimiTrailerStrip — Dashboard strip con gli ultimi trailer generati (qualsiasi tier).
 * Stesso formato delle altre strip (horizontal scroll, poster card).
 */
export default function UltimiTrailerStrip({ limit = 10 }) {
  const { api, user } = useContext(AuthContext) || {};
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [trailerData, setTrailerData] = useState(null);

  useEffect(() => {
    if (!api) return;
    api.get('/events/trailers/recent', { params: { limit } })
      .then(r => setItems(r.data?.items || []))
      .catch(() => {});
  }, [api, limit]);

  const openTrailer = async (item) => {
    try {
      const r = await api.get(`/trailers/${item.content_id}`);
      if (r.data?.trailer) {
        setTrailerData(r.data.trailer);
        setSelected(item);
      }
    } catch { /* */ }
  };

  const posterUrl = (p) => {
    if (!p) return null;
    if (p.startsWith('http') || p.startsWith('data:')) return p;
    return `${process.env.REACT_APP_BACKEND_URL}${p}`;
  };

  const timeAgo = (iso) => {
    if (!iso) return '';
    const diffMin = Math.max(1, Math.floor((Date.now() - new Date(iso).getTime()) / 60000));
    if (diffMin < 60) return `${diffMin}m fa`;
    const h = Math.floor(diffMin / 60);
    if (h < 24) return `${h}h fa`;
    return `${Math.floor(h / 24)}g fa`;
  };

  return (
    <div className="mb-4" data-testid="ultimi-trailer-strip">
      <div className="flex items-center gap-2 mb-2 px-1">
        <Film className="w-4 h-4 text-sky-400" />
        <h3 className="text-[12px] font-black text-white uppercase tracking-wider">Ultimi Trailer</h3>
        <span className="text-[9px] text-gray-500">· freschi di AI</span>
        {items.length > 0 && <span className="ml-auto text-[9px] text-sky-400 font-bold">{items.length}</span>}
      </div>
      {items.length === 0 ? (
        <div className="px-3 py-5 rounded-xl border border-dashed border-sky-500/25 bg-sky-500/[0.03] text-center" data-testid="ultimi-trailer-empty">
          <p className="text-[10px] text-gray-400 mb-1">Nessun trailer recente. Crea il tuo primo!</p>
          <p className="text-[8px] text-gray-500">Vai su un tuo film → Idea → sub-fase Trailer, oppure da qualsiasi step in navigazione read-only.</p>
        </div>
      ) : (
      <div className="flex gap-2 overflow-x-auto pb-2 px-1 -mx-1 snap-x">
        {items.map(it => {
          const TierIcon = it.tier === 'pro' ? Crown : it.tier === 'cinematic' ? Sparkles : Film;
          const tierColor = it.tier === 'pro' ? 'from-amber-500 to-orange-500 border-amber-400'
                          : it.tier === 'cinematic' ? 'from-purple-500 to-fuchsia-500 border-purple-400'
                          : 'from-sky-600 to-blue-500 border-sky-400';
          const isHighlights = it.mode === 'highlights';
          return (
            <button
              key={it.content_id}
              onClick={() => openTrailer(it)}
              className={`snap-start flex-shrink-0 w-16 rounded-lg overflow-hidden border bg-black/40 text-left hover:scale-[1.03] transition-transform ${isHighlights ? 'border-amber-500/40' : 'border-sky-500/25'}`}
              data-testid={`recent-trailer-${it.content_id}`}>
              <div className="relative aspect-[2/3] bg-gray-900">
                {posterUrl(it.poster_url) && (
                  <img src={posterUrl(it.poster_url)} alt="" className="absolute inset-0 w-full h-full object-cover" onError={e => { e.target.style.display = 'none'; }} />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent" />
                <div className={`absolute top-0.5 right-0.5 flex items-center gap-0.5 px-1 py-0 rounded-full bg-gradient-to-br ${tierColor}`}>
                  <TierIcon className="w-2 h-2 text-white" />
                  <span className="text-[5px] font-black text-white uppercase">{it.tier}</span>
                </div>
                {isHighlights && (
                  <span className="absolute top-0.5 left-0.5 px-1 py-0 rounded-full bg-amber-500/80 text-[5px] font-black text-black">🏆</span>
                )}
                {!!it.tstar && (
                  <span className="absolute bottom-6 right-0.5 px-1 py-0 rounded-full bg-black/60 border border-yellow-400/40 text-[5px] font-bold text-yellow-300">T{Math.round(it.tstar)}</span>
                )}
                <div className="absolute bottom-0.5 left-0.5 right-0.5">
                  <p className="text-[6px] font-bold text-white truncate">{it.title}</p>
                  <p className="text-[5px] text-gray-400 truncate flex items-center gap-0.5">
                    <Clock className="w-1.5 h-1.5" /> {timeAgo(it.generated_at)}
                  </p>
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-4 h-4 rounded-full bg-white/90 flex items-center justify-center">
                    <Play className="w-2 h-2 text-black fill-black" />
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
      )}
      {selected && trailerData && (
        <TrailerPlayerModal
          trailer={trailerData}
          contentTitle={selected.title}
          contentGenre={selected.genre || ''}
          contentId={selected.content_id}
          currentUserId={user?.id}
          api={api}
          onClose={() => { setSelected(null); setTrailerData(null); }}
        />
      )}
    </div>
  );
}
