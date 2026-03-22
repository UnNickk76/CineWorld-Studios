import React, { useState, useEffect, useContext, useCallback } from 'react';
import { AuthContext } from '../contexts';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Clock, Flame, Film, Tv, Sparkles, Loader2, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, Shield, Newspaper, MessageCircle } from 'lucide-react';
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
    const interval = setInterval(calc, 30000);
    return () => clearInterval(interval);
  }, [targetDate]);
  return remaining;
}

function HypeBar({ score }) {
  const maxHype = 50;
  const pct = Math.min(100, (score / maxHype) * 100);
  const color = score >= 30 ? 'from-orange-500 to-red-500' : score >= 15 ? 'from-yellow-500 to-orange-500' : 'from-gray-500 to-yellow-500';
  return (
    <div className="w-full" data-testid="hype-bar">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[8px] text-gray-500 uppercase tracking-wider">Hype</span>
        <span className="text-[9px] font-bold text-orange-400">{score}</span>
      </div>
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function NewsEvent({ event }) {
  const typeColors = {
    positive: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    negative: 'text-red-400 bg-red-500/10 border-red-500/20',
    backfire: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    neutral: 'text-gray-400 bg-gray-500/10 border-gray-500/20',
  };
  const c = typeColors[event.type] || typeColors.neutral;
  return (
    <div className={`px-2 py-1 rounded text-[9px] border ${c}`} data-testid="news-event">
      {event.text}
    </div>
  );
}

function ComingSoonCard({ item, api, onRefresh }) {
  const [expanded, setExpanded] = useState(false);
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [interacting, setInteracting] = useState(null);
  const [localHype, setLocalHype] = useState(item.hype_score || 0);
  const countdown = useCountdown(item.scheduled_release_at);
  const poster = posterSrc(item.poster_url);
  const typeIcon = item.content_type === 'anime' ? Sparkles : item.content_type === 'tv_series' ? Tv : Film;
  const TypeIcon = typeIcon;
  const typeLabel = item.content_type === 'anime' ? 'Anime' : item.content_type === 'tv_series' ? 'Serie TV' : 'Film';
  const typeColor = item.content_type === 'anime' ? 'text-pink-400 bg-pink-500/10' : item.content_type === 'tv_series' ? 'text-blue-400 bg-blue-500/10' : 'text-yellow-400 bg-yellow-500/10';

  const loadDetails = useCallback(async () => {
    if (!api) return;
    setLoading(true);
    try {
      const res = await api.get(`/coming-soon/${item.id}/details`);
      setDetails(res.data);
      setLocalHype(res.data.hype_score || 0);
    } catch { }
    finally { setLoading(false); }
  }, [api, item.id]);

  useEffect(() => {
    if (expanded && !details) loadDetails();
  }, [expanded, details, loadDetails]);

  const interact = async (action) => {
    setInteracting(action);
    try {
      const res = await api.post(`/coming-soon/${item.id}/interact`, { action });
      const d = res.data;
      if (d.outcome === 'backfire') {
        toast.info(d.message, { icon: '🔄' });
      } else if (d.outcome === 'success') {
        toast.success(d.message);
      } else {
        toast.info(d.message);
      }
      setLocalHype(prev => Math.max(0, prev + (d.effects?.hype || 0)));
      // Refresh details
      loadDetails();
      if (onRefresh) onRefresh();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
    finally { setInteracting(null); }
  };

  return (
    <Card className="bg-[#111113] border-white/5 hover:border-white/10 transition-all overflow-hidden"
      data-testid={`coming-soon-card-${item.id}`}>
      <CardContent className="p-0">
        {/* Compact header - always visible */}
        <div className="flex gap-0 cursor-pointer" onClick={() => setExpanded(!expanded)}>
          {/* Poster */}
          <div className="w-20 h-28 flex-shrink-0 bg-gradient-to-br from-gray-900 to-black relative">
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
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-cyan-400" />
                <span className="text-[10px] font-bold text-cyan-400">{countdown}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-0.5">
                  <Flame className="w-3 h-3 text-orange-400" />
                  <span className="text-[10px] font-bold text-orange-400">{localHype}</span>
                </div>
                {expanded ?
                  <ChevronUp className="w-3 h-3 text-gray-500" /> :
                  <ChevronDown className="w-3 h-3 text-gray-500" />
                }
              </div>
            </div>
          </div>
        </div>

        {/* Expanded section */}
        {expanded && (
          <div className="border-t border-white/5 p-3 space-y-3" data-testid={`coming-soon-expanded-${item.id}`}>
            {loading && !details ? (
              <div className="flex justify-center py-3"><Loader2 className="w-4 h-4 animate-spin text-gray-500" /></div>
            ) : (
              <>
                {/* Hype Bar */}
                <HypeBar score={localHype} />

                {/* Pre-trama */}
                {(details?.pre_screenplay || item.pre_screenplay) && (
                  <div className="p-2 rounded bg-white/[0.02] border border-white/5">
                    <p className="text-[9px] text-gray-500 mb-0.5 uppercase tracking-wider">Anteprima</p>
                    <p className="text-[10px] text-gray-400 italic leading-relaxed line-clamp-3">
                      "{details?.pre_screenplay || item.pre_screenplay}"
                    </p>
                  </div>
                )}

                {/* Audience expectation */}
                {details?.audience_expectation && (
                  <div className="flex items-center gap-2">
                    <Shield className="w-3 h-3 text-blue-400" />
                    <span className="text-[9px] text-gray-500">Aspettative pubblico:</span>
                    <Badge className={`text-[8px] h-4 ${
                      details.audience_expectation === 'Altissime' ? 'bg-emerald-500/15 text-emerald-400' :
                      details.audience_expectation === 'Alte' ? 'bg-blue-500/15 text-blue-400' :
                      details.audience_expectation === 'Medie' ? 'bg-yellow-500/15 text-yellow-400' :
                      'bg-red-500/15 text-red-400'
                    }`}>{details.audience_expectation}</Badge>
                  </div>
                )}

                {/* News Events */}
                {details?.news_events?.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-1">
                      <Newspaper className="w-3 h-3 text-gray-500" />
                      <span className="text-[9px] text-gray-500 uppercase tracking-wider">Notizie</span>
                    </div>
                    <div className="space-y-1 max-h-[100px] overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
                      {details.news_events.slice(-4).reverse().map((evt, i) => (
                        <NewsEvent key={i} event={evt} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Auto Comments */}
                {details?.auto_comments?.length > 0 && (
                  <div className="space-y-1">
                    <div className="flex items-center gap-1">
                      <MessageCircle className="w-3 h-3 text-gray-500" />
                      <span className="text-[9px] text-gray-500 uppercase tracking-wider">Commenti</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {details.auto_comments.slice(-4).map((c, i) => (
                        <span key={i} className="text-[8px] text-gray-500 bg-white/[0.03] px-1.5 py-0.5 rounded-full border border-white/5">
                          "{c.text}"
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Interaction Stats */}
                {details && (
                  <div className="flex items-center gap-3 text-[9px]">
                    <div className="flex items-center gap-1 text-emerald-400">
                      <ThumbsUp className="w-3 h-3" />{details.support_count}
                    </div>
                    <div className="flex items-center gap-1 text-red-400">
                      <ThumbsDown className="w-3 h-3" />{details.boycott_count}
                    </div>
                    {details.max_boycott_reached && (
                      <Badge className="text-[7px] bg-red-500/10 text-red-400 border border-red-500/20">Max boicottaggi</Badge>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                {details && !details.is_own_content && details.daily_actions_remaining > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-[8px] text-gray-600">
                      {details.daily_actions_remaining} azioni rimaste oggi ({details.interact_cost} CP ciascuna)
                    </p>
                    <div className="flex gap-2">
                      <Button size="sm"
                        className="flex-1 bg-emerald-600/80 hover:bg-emerald-600 text-white text-[10px] h-7"
                        disabled={interacting !== null}
                        onClick={() => interact('support')}
                        data-testid={`support-btn-${item.id}`}>
                        {interacting === 'support' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <ThumbsUp className="w-3 h-3 mr-1" />}
                        Supporta
                      </Button>
                      <Button size="sm"
                        className="flex-1 bg-red-600/80 hover:bg-red-600 text-white text-[10px] h-7"
                        disabled={interacting !== null || details.max_boycott_reached}
                        onClick={() => interact('boycott')}
                        data-testid={`boycott-btn-${item.id}`}>
                        {interacting === 'boycott' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <ThumbsDown className="w-3 h-3 mr-1" />}
                        Boicotta
                      </Button>
                    </div>
                  </div>
                )}

                {details?.is_own_content && (
                  <p className="text-[9px] text-gray-600 text-center italic">Questo e' un tuo progetto</p>
                )}

                {details && !details.is_own_content && details.daily_actions_remaining <= 0 && (
                  <p className="text-[9px] text-amber-400/70 text-center">Limite giornaliero raggiunto</p>
                )}
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function ComingSoonSection({ compact = false }) {
  const { api } = useContext(AuthContext);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadItems = useCallback(() => {
    if (!api) return;
    api.get('/coming-soon').then(r => setItems(r.data.items || [])).catch(() => {}).finally(() => setLoading(false));
  }, [api]);

  useEffect(() => {
    loadItems();
    const interval = setInterval(loadItems, 60000);
    return () => clearInterval(interval);
  }, [loadItems]);

  if (loading) return null;

  return (
    <div className="space-y-2" data-testid="coming-soon-section">
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4 text-cyan-400" />
        <h3 className="text-sm font-bold text-white">Prossimamente</h3>
        {items.length > 0 && <Badge className="bg-cyan-500/20 text-cyan-400 text-[8px] h-4">{items.length}</Badge>}
      </div>
      {items.length === 0 ? (
        <div className="p-4 rounded-lg border border-dashed border-gray-700/50 text-center" data-testid="coming-soon-empty">
          <Clock className="w-6 h-6 mx-auto mb-1 text-gray-700" />
          <p className="text-[10px] text-gray-600">Nessun contenuto in arrivo</p>
          <p className="text-[8px] text-gray-700">I film in Coming Soon appariranno qui</p>
        </div>
      ) : (
        <div className={compact ? 'space-y-2' : 'grid grid-cols-1 sm:grid-cols-2 gap-2'}>
          {items.slice(0, compact ? 3 : 10).map(item => (
            <ComingSoonCard key={item.id} item={item} api={api} onRefresh={loadItems} />
          ))}
        </div>
      )}
    </div>
  );
}
