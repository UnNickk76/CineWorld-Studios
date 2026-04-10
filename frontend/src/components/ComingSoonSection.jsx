import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Dialog, DialogContent } from './ui/dialog';
import { Clock, Flame, Film, Tv, Sparkles, Loader2, ThumbsUp, ThumbsDown, ChevronRight, Shield, Newspaper, MessageCircle, Zap, FastForward, Search, AlertTriangle, Gavel, Swords, Target, X } from 'lucide-react';
import { toast } from 'sonner';
import { OutcomePopup, getOutcomeType } from './OutcomePopup';

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
  const hasTitle = event.title && event.title !== event.text;
  const hasMinutes = event.effect_minutes != null && event.effect_minutes !== 0;
  const isCineWorldNews = event.source === 'CineWorld News';

  return (
    <div className={`px-2 py-1.5 rounded text-[9px] border ${c}`} data-testid="news-event">
      {isCineWorldNews && (
        <span className="text-[7px] font-bold tracking-wider uppercase text-yellow-400/70 block mb-0.5">CineWorld News</span>
      )}
      {hasTitle ? (
        <>
          <span className="font-semibold">{event.title}</span>
          {event.desc && <span className="block text-[8px] opacity-70 italic mt-0.5">"{event.desc}"</span>}
          {hasMinutes && (
            <span className={`block mt-0.5 font-bold ${event.effect_minutes > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {event.effect_minutes > 0 ? '+' : ''}{event.effect_minutes} min
            </span>
          )}
        </>
      ) : (
        <span>{event.text}</span>
      )}
    </div>
  );
}

function SaboteurCard({ sab, contentId, api, onAction }) {
  const [acting, setActing] = useState(null);

  const counterAttack = async () => {
    setActing('counter');
    try {
      const res = await api.post('/pvp/counter-boycott', {
        content_id: contentId,
        mode: 'targeted',
        target_user_id: sab.user_id,
      });
      toast.success(res.data.message, { duration: 6000 });
      if (onAction) onAction();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore contro-attacco');
    } finally { setActing(null); }
  };

  const legalAction = async () => {
    setActing('legal');
    try {
      const res = await api.post('/pvp/legal-action', {
        target_user_id: sab.user_id,
        content_id: contentId,
      });
      if (res.data.won) {
        toast.success(res.data.message, { duration: 8000 });
      } else {
        toast.error(res.data.message, { duration: 6000 });
      }
      if (onAction) onAction();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore azione legale');
    } finally { setActing(null); }
  };

  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-red-500/5 border border-red-500/15" data-testid={`saboteur-${sab.user_id}`}>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-semibold text-white truncate">{sab.nickname}</p>
        <p className="text-[8px] text-red-400">{sab.boycott_type}</p>
      </div>
      <div className="flex gap-1 flex-shrink-0">
        <Button size="sm" className="h-6 px-2 text-[8px] bg-orange-600/80 hover:bg-orange-600 text-white"
          disabled={acting !== null} onClick={counterAttack} data-testid={`counter-attack-${sab.user_id}`}>
          {acting === 'counter' ? <Loader2 className="w-2.5 h-2.5 animate-spin" /> : <Swords className="w-2.5 h-2.5 mr-0.5" />}
          Attacca
        </Button>
        <Button size="sm" className="h-6 px-2 text-[8px] bg-purple-600/80 hover:bg-purple-600 text-white"
          disabled={acting !== null} onClick={legalAction} data-testid={`legal-action-${sab.user_id}`}>
          {acting === 'legal' ? <Loader2 className="w-2.5 h-2.5 animate-spin" /> : <Gavel className="w-2.5 h-2.5 mr-0.5" />}
          Causa
        </Button>
      </div>
    </div>
  );
}

// Compact horizontal card (poster + title + type + countdown)
function ComingSoonThumb({ item, onClick }) {
  const countdown = useCountdown(item.scheduled_release_at);
  const poster = posterSrc(item.poster_url);
  const isRemastering = item.is_remastering;
  const TypeIcon = item.content_type === 'anime' ? Sparkles : item.content_type === 'tv_series' ? Tv : Film;
  const typeLabel = isRemastering ? 'Remaster' : item.content_type === 'anime' ? 'Anime' : item.content_type === 'tv_series' ? 'Serie' : 'Film';
  const typeColor = isRemastering ? 'text-amber-400' : item.content_type === 'anime' ? 'text-pink-400' : item.content_type === 'tv_series' ? 'text-blue-400' : 'text-yellow-400';

  // Urgency calculation
  const diff = item.scheduled_release_at ? new Date(item.scheduled_release_at) - new Date() : Infinity;
  const isImminent = diff > 0 && diff < 1800000; // < 30 min
  const isUrgent = diff > 0 && diff < 7200000; // < 2h

  // Hype label
  const hype = item.hype_score || 0;
  const hypeLabel = hype >= 30 ? 'Attesissimo' : hype >= 15 ? 'In crescita' : hype > 0 ? 'Interesse basso' : null;
  const hypeColor = hype >= 30 ? 'text-red-400' : hype >= 15 ? 'text-orange-400' : 'text-gray-500';

  return (
    <div className="flex-shrink-0 w-[100px] cursor-pointer group" onClick={onClick}
      data-testid={`coming-soon-thumb-${item.id}`}>
      <div className={`aspect-[2/3] relative rounded-lg overflow-hidden bg-gradient-to-br from-gray-900 to-black ${isImminent ? 'ring-2 ring-red-500/60 animate-pulse' : isUrgent ? 'ring-1 ring-orange-500/40' : ''}`}>
        {poster ? (
          <img src={poster} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <TypeIcon className={`w-8 h-8 ${typeColor} opacity-20`} />
          </div>
        )}
        {/* Countdown overlay */}
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent p-1.5 pt-4">
          <div className="flex items-center gap-0.5">
            <Clock className="w-2.5 h-2.5 text-cyan-400" />
            <span className="text-[9px] font-bold text-cyan-300">{countdown}</span>
          </div>
          {/* Hype label */}
          {hypeLabel && (
            <p className={`text-[7px] font-semibold mt-0.5 ${hypeColor}`}>
              {hype >= 30 && <Flame className="w-2 h-2 inline mr-0.5" />}{hypeLabel}
            </p>
          )}
        </div>
        {/* Urgency badge */}
        {isImminent && (
          <div className="absolute top-1 left-1 px-1 py-0.5 bg-red-600/90 rounded text-[6px] font-bold text-white" data-testid="urgency-imminent">
            Uscita imminente
          </div>
        )}
        {!isImminent && isUrgent && (
          <div className="absolute top-1 left-1 px-1 py-0.5 bg-orange-600/80 rounded text-[6px] font-bold text-white" data-testid="urgency-soon">
            In uscita
          </div>
        )}
        {/* Type badge */}
        <div className={`absolute top-1 right-1 ${isImminent || isUrgent ? '' : ''}`}>
          <Badge className={`text-[6px] h-3 px-1 bg-black/70 ${typeColor} border-0`}>
            {typeLabel}
          </Badge>
        </div>
        {/* Hype indicator */}
        {hype > 0 && (
          <div className={`absolute ${isImminent || isUrgent ? 'top-5' : 'top-1'} left-1 flex items-center gap-0.5 bg-black/70 rounded px-1 py-0.5`}>
            <Flame className={`w-2 h-2 ${hype >= 30 ? 'text-red-400' : 'text-orange-400'}`} />
            <span className={`text-[7px] font-bold ${hype >= 30 ? 'text-red-300' : 'text-orange-300'}`}>{hype}</span>
          </div>
        )}
      </div>
      <p className="text-[8px] font-semibold truncate mt-1 group-hover:text-cyan-400 transition-colors">{item.title}</p>
      <div className="flex items-center gap-1">
        <p className="text-[7px] text-gray-600 truncate">{item.production_house}</p>
        {item.pipeline_status_label && (
          <span className="text-[6px] px-1 py-0.5 rounded bg-violet-500/15 text-violet-400 font-bold flex-shrink-0">
            {item.pipeline_status_label}
          </span>
        )}
      </div>
    </div>
  );
}

// Full detail dialog content
function ComingSoonDetail({ item, api, onRefresh, pvpStatus, onClose }) {
  const navigate = useNavigate();

  // V2 films: navigate to detail page (uses new ContentTemplate)
  if (item.is_v2) {
    const poster = posterSrc(item.poster_url);
    return (
      <div className="space-y-3" data-testid="coming-soon-v2-detail">
        {poster && <img src={poster} alt="" className="w-full aspect-[2/3] object-cover rounded-lg" />}
        <div className="text-center space-y-1">
          <h3 className="font-['Bebas_Neue'] text-xl text-white">{item.title}</h3>
          {item.genre_name && <p className="text-[10px] text-gray-400">{item.genre_name} {item.subgenres?.length > 0 && `• ${item.subgenres.join(', ')}`}</p>}
          {item.production_house && <p className="text-[9px] text-gray-500">di {item.production_house}</p>}
          {item.pipeline_status_label && (
            <span className="inline-block text-[9px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-400 font-bold">
              Fase: {item.pipeline_status_label}
            </span>
          )}
          {item.pre_imdb_score > 0 && (
            <p className="text-[9px] text-yellow-400">Pre-IMDb: {item.pre_imdb_score?.toFixed(1)}</p>
          )}
          <Button size="sm" className="mt-2 bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 border border-yellow-500/30"
            onClick={() => { onClose?.(); navigate(`/films/${item.id}`); }}>
            Vedi Dettaglio
          </Button>
        </div>
      </div>
    );
  }
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [interacting, setInteracting] = useState(null);
  const [outcomePopup, setOutcomePopup] = useState(null); // { type, title, message }
  const [speedingUp, setSpeedingUp] = useState(false);
  const [pvpActing, setPvpActing] = useState(null);
  const [localHype, setLocalHype] = useState(item.hype_score || 0);
  const countdown = useCountdown(item.scheduled_release_at);
  const poster = posterSrc(item.poster_url);
  const isRemastering = item.is_remastering;
  const TypeIcon = item.content_type === 'anime' ? Sparkles : item.content_type === 'tv_series' ? Tv : Film;
  const typeLabel = isRemastering ? 'In Aggiornamento' : item.content_type === 'anime' ? 'Anime' : item.content_type === 'tv_series' ? 'Serie TV' : 'Film';
  const typeColor = isRemastering ? 'text-amber-400 bg-amber-500/10' : item.content_type === 'anime' ? 'text-pink-400 bg-pink-500/10' : item.content_type === 'tv_series' ? 'text-blue-400 bg-blue-500/10' : 'text-yellow-400 bg-yellow-500/10';

  const invDiv = pvpStatus?.divisions?.investigative;
  const opsDiv = pvpStatus?.divisions?.operative;

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

  useEffect(() => { loadDetails(); }, [loadDetails]);

  const interact = async (action) => {
    setInteracting(action);
    try {
      const res = await api.post(`/coming-soon/${item.id}/interact`, { action });
      const d = res.data;
      const hypeChange = d.effects?.hype || 0;
      const outcomeType = getOutcomeType(action, d.outcome);
      const hypeMsg = hypeChange > 0 ? `+${hypeChange} Hype` : hypeChange < 0 ? `${hypeChange} Hype` : '';
      setOutcomePopup({
        type: outcomeType,
        title: item.title,
        message: d.message + (hypeMsg ? ` (${hypeMsg})` : ''),
      });
      setLocalHype(prev => Math.max(0, prev + hypeChange));
      loadDetails();
      if (onRefresh) onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setInteracting(null); }
  };

  const speedUp = async () => {
    setSpeedingUp(true);
    try {
      const res = await api.post(`/coming-soon/${item.id}/speed-up`);
      toast.success(res.data.message);
      loadDetails();
      if (onRefresh) onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setSpeedingUp(false); }
  };

  const pvpInvestigate = async () => {
    setPvpActing('investigate');
    try {
      const res = await api.post('/pvp/investigate', { content_id: item.id });
      if (res.data.found) toast.success(`Sabotatore scoperto: ${res.data.saboteur.nickname} - ${res.data.boycott_type}`, { duration: 8000 });
      else toast.error(res.data.message, { duration: 5000 });
      loadDetails();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore investigazione'); }
    finally { setPvpActing(null); }
  };

  const pvpDefense = async () => {
    setPvpActing('defense');
    try {
      const res = await api.post('/pvp/counter-boycott', { content_id: item.id, mode: 'defense' });
      toast.success(res.data.message, { duration: 5000 });
      setLocalHype(prev => prev + (res.data.hype_recovered || 0));
      loadDetails();
      if (onRefresh) onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore difesa'); }
    finally { setPvpActing(null); }
  };

  const saboteurs = details?.identified_saboteurs || [];

  return (
    <>
    <div className="space-y-3" data-testid={`coming-soon-detail-${item.id}`}>
      {/* Header with poster */}
      <div className="flex gap-3">
        <div className="w-24 h-36 flex-shrink-0 rounded-lg overflow-hidden bg-gray-900">
          {poster ? <img src={poster} alt="" className="w-full h-full object-cover" /> :
            <div className="w-full h-full flex items-center justify-center"><TypeIcon className="w-8 h-8 text-gray-700" /></div>}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1">
            <Badge className={`text-[7px] h-3.5 px-1.5 ${typeColor}`}><TypeIcon className="w-2 h-2 mr-0.5" />{typeLabel}</Badge>
            {item.genre_name && <Badge className="text-[7px] h-3.5 bg-white/5 text-gray-500">{item.genre_name}</Badge>}
          </div>
          <h3 className="text-sm font-bold text-white mb-0.5">{item.title}</h3>
          <p className="text-[10px] text-gray-500">{item.production_house}</p>
          <div className="flex items-center gap-3 mt-2">
            <div className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-xs font-bold text-cyan-400">{countdown}</span>
            </div>
            <div className="flex items-center gap-1">
              <Flame className="w-3.5 h-3.5 text-orange-400" />
              <span className="text-xs font-bold text-orange-400">{localHype}</span>
            </div>
          </div>
        </div>
      </div>

      {loading && !details ? (
        <div className="flex justify-center py-4"><Loader2 className="w-5 h-5 animate-spin text-gray-500" /></div>
      ) : (
        <>
          {/* Hype Bar with label */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className={`text-[9px] font-semibold ${
                localHype >= 30 ? 'text-red-400' : localHype >= 15 ? 'text-orange-400' : 'text-gray-500'
              }`}>
                {localHype >= 30 ? 'Film attesissimo' : localHype >= 15 ? 'Sta crescendo' : 'Interesse basso'}
              </span>
            </div>
            <HypeBar score={localHype} />
          </div>

          {/* Anteprima */}
          {(details?.pre_screenplay || item.pre_screenplay) && (
            <div className="p-2 rounded bg-white/[0.02] border border-white/5">
              <p className="text-[9px] text-gray-500 mb-0.5 uppercase tracking-wider">Anteprima</p>
              <p className="text-[10px] text-gray-400 italic leading-relaxed line-clamp-4">
                "{details?.pre_screenplay || item.pre_screenplay}"
              </p>
            </div>
          )}

          {/* Audience expectation + Status */}
          {details?.audience_expectation && (
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-blue-400" />
                <span className="text-[9px] text-gray-500">Aspettative:</span>
                <Badge className={`text-[8px] h-4 ${
                  details.audience_expectation === 'Altissime' ? 'bg-emerald-500/15 text-emerald-400' :
                  details.audience_expectation === 'Alte' ? 'bg-blue-500/15 text-blue-400' :
                  details.audience_expectation === 'Medie' ? 'bg-yellow-500/15 text-yellow-400' :
                  'bg-red-500/15 text-red-400'
                }`}>{details.audience_expectation}</Badge>
              </div>
              {details.project_status && (
                <Badge className={`text-[8px] h-4 ${
                  details.project_status === 'in_crescita' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                  details.project_status === 'in_crisi' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                  details.project_status === 'promettente' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                  'bg-gray-500/10 text-gray-400 border border-gray-500/20'
                }`}>
                  {details.project_status === 'in_crescita' ? 'In crescita' :
                   details.project_status === 'in_crisi' ? 'In crisi' :
                   details.project_status === 'promettente' ? 'Promettente' : 'Stabile'}
                </Badge>
              )}
            </div>
          )}

          {/* News Events */}
          {details?.news_events?.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1">
                <Newspaper className="w-3 h-3 text-gray-500" />
                <span className="text-[9px] text-gray-500 uppercase tracking-wider">Notizie</span>
              </div>
              <div className="space-y-1 max-h-[120px] overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
                {details.news_events.slice(-4).reverse().map((evt, i) => (
                  <NewsEvent key={i} event={evt} />
                ))}
              </div>
            </div>
          )}

          {/* Comments */}
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

          {/* OTHER PLAYER: Support/Boycott */}
          {details && !details.is_own_content && details.daily_actions_remaining > 0 && (
            <div className="space-y-1.5">
              <p className="text-[8px] text-gray-600">
                {details.daily_actions_remaining} azioni rimaste oggi ({details.interact_cost} CP ciascuna)
              </p>
              <div className="flex gap-2">
                <Button size="sm" className="flex-1 bg-emerald-600/80 hover:bg-emerald-600 text-white text-[10px] h-7"
                  disabled={interacting !== null} onClick={() => interact('support')} data-testid={`support-btn-${item.id}`}>
                  {interacting === 'support' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <ThumbsUp className="w-3 h-3 mr-1" />}
                  Supporta
                </Button>
                <Button size="sm" className="flex-1 bg-red-600/80 hover:bg-red-600 text-white text-[10px] h-7"
                  disabled={interacting !== null || details.max_boycott_reached} onClick={() => interact('boycott')} data-testid={`boycott-btn-${item.id}`}>
                  {interacting === 'boycott' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <ThumbsDown className="w-3 h-3 mr-1" />}
                  Boicotta
                </Button>
              </div>
            </div>
          )}

          {details && !details.is_own_content && details.daily_actions_remaining <= 0 && (
            <p className="text-[9px] text-amber-400/70 text-center">Limite giornaliero raggiunto</p>
          )}

          {/* OWN CONTENT: PvP Actions */}
          {details?.is_own_content && (
            <div className="space-y-2">
              <p className="text-[9px] text-gray-600 text-center italic">Questo e' un tuo progetto</p>

              {details.boycott_count > 0 && (
                <div className="space-y-2 p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-1.5">
                    <Swords className="w-3 h-3 text-yellow-500" />
                    <span className="text-[9px] font-bold text-yellow-500 uppercase tracking-wider">Azioni PvP</span>
                  </div>

                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1 bg-cyan-600/80 hover:bg-cyan-600 text-white text-[10px] h-7"
                      disabled={pvpActing !== null || !invDiv || invDiv.level === 0 || invDiv.daily_remaining <= 0}
                      onClick={pvpInvestigate} data-testid={`pvp-investigate-${item.id}`}>
                      {pvpActing === 'investigate' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Search className="w-3 h-3 mr-1" />}
                      Indaga
                    </Button>
                    <Button size="sm" className="flex-1 bg-orange-600/80 hover:bg-orange-600 text-white text-[10px] h-7"
                      disabled={pvpActing !== null || !opsDiv || opsDiv.level === 0 || opsDiv.daily_remaining <= 0}
                      onClick={pvpDefense} data-testid={`pvp-defense-${item.id}`}>
                      {pvpActing === 'defense' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Shield className="w-3 h-3 mr-1" />}
                      Difesa
                    </Button>
                  </div>

                  <div className="flex flex-wrap gap-1.5 text-[8px]">
                    {invDiv && invDiv.level > 0 ? (
                      <span className="text-cyan-400/70">Investigativa: {invDiv.daily_remaining}/{invDiv.daily_limit}</span>
                    ) : (
                      <span className="text-gray-600 flex items-center gap-0.5 cursor-pointer" onClick={() => { onClose?.(); navigate('/hq'); }}>
                        <Search className="w-2.5 h-2.5" /> Sblocca Investigativa
                      </span>
                    )}
                    {opsDiv && opsDiv.level > 0 ? (
                      <span className="text-orange-400/70">Operativa: {opsDiv.daily_remaining}/{opsDiv.daily_limit}</span>
                    ) : (
                      <span className="text-gray-600 flex items-center gap-0.5 cursor-pointer" onClick={() => { onClose?.(); navigate('/hq'); }}>
                        <Shield className="w-2.5 h-2.5" /> Sblocca Operativa
                      </span>
                    )}
                  </div>

                  {saboteurs.length > 0 && (
                    <div className="space-y-1.5 mt-1">
                      <div className="flex items-center gap-1">
                        <Target className="w-3 h-3 text-red-400" />
                        <span className="text-[9px] text-red-400 font-semibold">Sabotatori Identificati</span>
                      </div>
                      {saboteurs.map(sab => (
                        <SaboteurCard key={sab.user_id} sab={sab} contentId={item.id} api={api} onAction={loadDetails} />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {details.coming_soon_speedup_cap > 0 && details.coming_soon_speedup_used < details.coming_soon_speedup_cap && (
                <Button size="sm" className="w-full bg-purple-600/80 hover:bg-purple-600 text-white text-[10px] h-7"
                  disabled={speedingUp} onClick={speedUp} data-testid={`speedup-btn-${item.id}`}>
                  {speedingUp ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <FastForward className="w-3 h-3 mr-1" />}
                  Velocizza (-10%)
                </Button>
              )}
              {details.coming_soon_speedup_used > 0 && (
                <p className="text-[8px] text-gray-600 text-center">
                  Velocizzato: {Math.round(details.coming_soon_speedup_used * 100)}% / {Math.round(details.coming_soon_speedup_cap * 100)}% max
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>

    {outcomePopup && (
      <OutcomePopup
        open={!!outcomePopup}
        onClose={() => setOutcomePopup(null)}
        outcomeType={outcomePopup.type}
        title={outcomePopup.title}
        message={outcomePopup.message}
      />
    )}
    </>
  );
}

export function ComingSoonSection({ compact = false, filterType, sectionTitle }) {
  const { api } = useContext(AuthContext);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pvpStatus, setPvpStatus] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);

  const loadItems = useCallback(() => {
    if (!api) return;
    api.get('/coming-soon').then(r => {
      let sorted = (r.data.items || []).sort((a, b) => {
        const da = a.scheduled_release_at ? new Date(a.scheduled_release_at) : new Date('2099-01-01');
        const db = b.scheduled_release_at ? new Date(b.scheduled_release_at) : new Date('2099-01-01');
        return da - db;
      });
      if (filterType) {
        sorted = sorted.filter(item => item.content_type === filterType);
      }
      setItems(sorted);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [api, filterType]);

  const loadPvpStatus = useCallback(() => {
    if (!api) return;
    api.get('/pvp/status').then(r => setPvpStatus(r.data)).catch(() => {});
  }, [api]);

  useEffect(() => {
    loadItems();
    loadPvpStatus();
    const interval = setInterval(loadItems, 60000);
    return () => clearInterval(interval);
  }, [loadItems, loadPvpStatus]);

  if (loading) return null;

  const title = sectionTitle || 'Prossimamente';
  const typeColors = { film: 'text-yellow-400', tv_series: 'text-blue-400', anime: 'text-orange-400' };
  const TypeIcons = { film: Film, tv_series: Tv, anime: Sparkles };
  const TIcon = filterType ? (TypeIcons[filterType] || Clock) : Clock;
  const tColor = filterType ? (typeColors[filterType] || 'text-cyan-400') : 'text-cyan-400';

  return (
    <div data-testid={`coming-soon-section${filterType ? `-${filterType}` : ''}`}>
      <div className="flex items-center gap-2 mb-2 px-2 pt-2">
        <TIcon className={`w-3.5 h-3.5 ${tColor}`} />
        <h3 className="font-['Bebas_Neue'] text-base text-white">{title}</h3>
        {items.length > 0 && <Badge className="bg-cyan-500/20 text-cyan-400 text-[8px] h-4">{items.length}</Badge>}
      </div>

      {items.length === 0 ? (
        <div className="p-3 rounded-lg border border-dashed border-gray-700/50 text-center mx-2 mb-2" data-testid="coming-soon-empty">
          <Clock className="w-5 h-5 mx-auto mb-1 text-gray-700" />
          <p className="text-[10px] text-gray-600">Nessun contenuto in arrivo</p>
        </div>
      ) : (
        <div className="flex gap-2 overflow-x-auto pb-2 px-2" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}>
          {items.map(item => (
            <ComingSoonThumb key={item.id} item={item} onClick={() => setSelectedItem(item)} />
          ))}
        </div>
      )}

      <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
        <DialogContent className="bg-[#111113] border-white/10 text-white max-w-md max-h-[85vh] overflow-y-auto p-4"
          style={{ scrollbarWidth: 'thin' }}
          data-testid="coming-soon-dialog">
          {selectedItem && (
            <ComingSoonDetail
              item={selectedItem}
              api={api}
              onRefresh={loadItems}
              pvpStatus={pvpStatus}
              onClose={() => setSelectedItem(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
