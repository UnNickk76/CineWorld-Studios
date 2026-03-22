import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Clock, Flame, Film, Tv, Sparkles, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

function useCountdown(targetDate) {
  const [remaining, setRemaining] = useState('');
  useEffect(() => {
    if (!targetDate) return;
    const calc = () => {
      const diff = new Date(targetDate) - new Date();
      if (diff <= 0) { setRemaining('In uscita!'); return; }
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      setRemaining(h > 0 ? `${h}h ${m}m` : `${m}m`);
    };
    calc();
    const interval = setInterval(calc, 60000);
    return () => clearInterval(interval);
  }, [targetDate]);
  return remaining;
}

function ComingSoonCard({ item, api }) {
  const [hyping, setHyping] = useState(false);
  const [hyped, setHyped] = useState(false);
  const countdown = useCountdown(item.scheduled_release_at);
  const poster = posterSrc(item.poster_url);
  const typeIcon = item.content_type === 'anime' ? Sparkles : item.content_type === 'tv_series' ? Tv : Film;
  const TypeIcon = typeIcon;
  const typeLabel = item.content_type === 'anime' ? 'Anime' : item.content_type === 'tv_series' ? 'Serie TV' : 'Film';
  const typeColor = item.content_type === 'anime' ? 'text-pink-400 bg-pink-500/10' : item.content_type === 'tv_series' ? 'text-blue-400 bg-blue-500/10' : 'text-yellow-400 bg-yellow-500/10';

  const addHype = async () => {
    setHyping(true);
    try {
      const res = await api.post(`/coming-soon/${item.id}/hype`);
      if (res.data.already_hyped) {
        toast.info('Hai già aggiunto hype!');
      } else {
        toast.success('Hype aggiunto!');
        setHyped(true);
      }
    } catch { toast.error('Errore'); }
    finally { setHyping(false); }
  };

  return (
    <Card className="bg-[#111113] border-white/5 hover:border-white/10 transition-all overflow-hidden" data-testid={`coming-soon-card-${item.id}`}>
      <CardContent className="p-0">
        <div className="flex gap-0">
          {/* Poster */}
          <div className="w-20 h-28 flex-shrink-0 bg-gradient-to-br from-gray-900 to-black">
            {poster ? (
              <img src={poster} alt="" className="w-full h-full object-cover" loading="lazy" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <TypeIcon className={`w-6 h-6 ${typeColor.split(' ')[0]} opacity-30`} />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 p-2.5 min-w-0 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-1.5 mb-1">
                <Badge className={`text-[7px] h-3.5 px-1.5 ${typeColor}`}>
                  <TypeIcon className="w-2 h-2 mr-0.5" />{typeLabel}
                </Badge>
                {item.genre_name && <Badge className="text-[7px] h-3.5 bg-white/5 text-gray-500">{item.genre_name}</Badge>}
              </div>
              <h4 className="text-xs font-bold text-white truncate">{item.title}</h4>
              <p className="text-[9px] text-gray-600 truncate">{item.production_house}</p>
            </div>

            <div className="flex items-center justify-between mt-1.5">
              {/* Countdown */}
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-cyan-400" />
                <span className="text-[10px] font-bold text-cyan-400">{countdown}</span>
              </div>
              {/* Hype */}
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] text-orange-400 font-semibold">{(item.hype_score || 0) + (hyped ? 1 : 0)}</span>
                <button
                  onClick={addHype}
                  disabled={hyping || hyped}
                  className={`flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[9px] font-bold transition-all ${
                    hyped ? 'bg-orange-500/20 text-orange-400' : 'bg-orange-500/10 text-orange-400 hover:bg-orange-500/20'
                  }`}
                  data-testid={`hype-btn-${item.id}`}
                >
                  {hyping ? <Loader2 className="w-2.5 h-2.5 animate-spin" /> : <Flame className="w-2.5 h-2.5" />}
                  {hyped ? 'Hyped!' : 'Hype'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function ComingSoonSection({ compact = false }) {
  const { api } = useContext(AuthContext);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!api) return;
    api.get('/coming-soon').then(r => setItems(r.data.items || [])).catch(() => {}).finally(() => setLoading(false));
  }, [api]);

  if (loading) return null;
  if (items.length === 0) return null;

  return (
    <div className="space-y-2" data-testid="coming-soon-section">
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4 text-cyan-400" />
        <h3 className="text-sm font-bold text-white">Prossimamente</h3>
        <Badge className="bg-cyan-500/20 text-cyan-400 text-[8px] h-4">{items.length}</Badge>
      </div>
      <div className={compact ? 'space-y-2' : 'grid grid-cols-1 sm:grid-cols-2 gap-2'}>
        {items.slice(0, compact ? 3 : 10).map(item => (
          <ComingSoonCard key={item.id} item={item} api={api} />
        ))}
      </div>
    </div>
  );
}
