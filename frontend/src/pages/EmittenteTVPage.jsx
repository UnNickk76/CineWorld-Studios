// CineWorld - Emittente TV Page
// Full TV Network management: broadcast schedule, live ratings, episode history

import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import {
  Radio, Tv, Sparkles, Lock, Clock, Users, DollarSign, TrendingUp, TrendingDown,
  Loader2, Plus, X, Play, Trash2, BarChart3, Eye, Activity, Minus, ChevronRight, ArrowUp, ArrowDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

export default function EmittenteTVPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [hasEmittente, setHasEmittente] = useState(false);
  const [emittente, setEmittente] = useState(null);
  const [broadcasts, setBroadcasts] = useState([]);
  const [timeslots, setTimeslots] = useState({});
  const [completedSeries, setCompletedSeries] = useState([]);
  const [assigningSlot, setAssigningSlot] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  // Live ratings
  const [liveData, setLiveData] = useState(null);
  const [livePolling, setLivePolling] = useState(false);
  // Episode history
  const [historyDialog, setHistoryDialog] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const unlockRes = await api.get('/production-studios/unlock-status');
      setHasEmittente(unlockRes.data.has_emittente_tv);

      if (unlockRes.data.has_emittente_tv) {
        const [bRes, tvRes, animeRes] = await Promise.all([
          api.get('/emittente-tv/broadcasts').catch(() => ({ data: { broadcasts: [], emittente: {}, timeslots: {} } })),
          api.get('/series-pipeline/my?series_type=tv_series').catch(() => ({ data: { series: [] } })),
          api.get('/series-pipeline/my?series_type=anime').catch(() => ({ data: { series: [] } })),
        ]);
        setBroadcasts(bRes.data.broadcasts || []);
        setEmittente(bRes.data.emittente || {});
        setTimeslots(bRes.data.timeslots || {});

        const allCompleted = [
          ...(tvRes.data.series || []).filter(s => s.status === 'completed').map(s => ({ ...s, typeLabel: 'Serie TV' })),
          ...(animeRes.data.series || []).filter(s => s.status === 'completed').map(s => ({ ...s, typeLabel: 'Anime' })),
        ];
        setCompletedSeries(allCompleted);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [api]);

  const fetchLiveRatings = useCallback(async () => {
    try {
      const res = await api.get('/emittente-tv/live-ratings');
      setLiveData(res.data);
    } catch (e) { /* silent */ }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  // Live ratings polling every 5 seconds
  useEffect(() => {
    if (!hasEmittente || loading) return;
    fetchLiveRatings();
    const interval = setInterval(fetchLiveRatings, 5000);
    setLivePolling(true);
    return () => { clearInterval(interval); setLivePolling(false); };
  }, [hasEmittente, loading, fetchLiveRatings]);

  const assignSeries = async (seriesId) => {
    if (!assigningSlot) return;
    setActionLoading(true);
    try {
      const res = await api.post('/emittente-tv/assign', { series_id: seriesId, timeslot: assigningSlot });
      toast.success(res.data.message);
      setAssigningSlot(null);
      loadData();
      fetchLiveRatings();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const removeSeries = async (slotKey) => {
    if (!window.confirm('Rimuovere questa serie dallo slot?')) return;
    setActionLoading(true);
    try {
      const res = await api.post('/emittente-tv/remove', { timeslot: slotKey });
      toast.success(res.data.message);
      loadData();
      fetchLiveRatings();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const airEpisodes = async () => {
    setActionLoading(true);
    try {
      const res = await api.post('/emittente-tv/air-episode');
      const results = res.data.results || [];
      if (results.length === 0) {
        toast.info('Nessun episodio da mandare in onda');
      } else {
        for (const r of results) {
          if (r.status === 'finished') {
            toast.info(`"${r.series}" ha terminato gli episodi`);
          } else {
            const trendIcon = r.trend === 'growing' ? '+' : r.trend === 'declining' ? '-' : '=';
            toast.success(
              `"${r.series}" Ep.${r.episode}/${r.total_episodes}: ${r.audience?.toLocaleString()} spettatori (${r.share_percent}% share ${trendIcon}), $${r.revenue?.toLocaleString()}`
            );
          }
        }
      }
      loadData();
      fetchLiveRatings();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const openHistory = async (broadcastId) => {
    setHistoryDialog(broadcastId);
    setHistoryLoading(true);
    try {
      const res = await api.get(`/emittente-tv/episode-history/${broadcastId}`);
      setHistoryData(res.data);
    } catch (e) { toast.error('Errore caricamento storico'); }
    setHistoryLoading(false);
  };

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center pt-16">
      <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
    </div>
  );

  if (!hasEmittente) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
        <div className="max-w-lg mx-auto px-4 flex flex-col items-center justify-center min-h-[60vh]">
          <div className="p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20 mb-4">
            <Radio className="w-12 h-12 text-emerald-400" />
          </div>
          <h1 className="font-['Bebas_Neue'] text-3xl text-emerald-400 mb-2" data-testid="emittente-locked-title">Emittente TV</h1>
          <p className="text-sm text-gray-400 text-center mb-6 max-w-xs">
            Costruisci la tua emittente televisiva per trasmettere serie TV e anime.
          </p>
          <Card className="bg-[#111113] border-emerald-500/20 w-full max-w-sm">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Livello richiesto</span>
                <span className="text-sm font-bold text-emerald-400">18</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Fama richiesta</span>
                <span className="text-sm font-bold text-emerald-400">200</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Costo</span>
                <span className="text-sm font-bold text-yellow-400">$5,000,000</span>
              </div>
              <Button className="w-full bg-emerald-500 hover:bg-emerald-600" onClick={() => navigate('/infrastructure')} data-testid="go-to-infra-btn">
                <Lock className="w-4 h-4 mr-2" /> Vai alle Infrastrutture
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const SLOT_CONFIG = {
    daytime: { color: 'yellow', icon: Clock, gradient: 'from-yellow-500/15 to-amber-500/5', border: 'border-yellow-500/20' },
    prime_time: { color: 'red', icon: TrendingUp, gradient: 'from-red-500/15 to-rose-500/5', border: 'border-red-500/20' },
    late_night: { color: 'purple', icon: Clock, gradient: 'from-purple-500/15 to-violet-500/5', border: 'border-purple-500/20' },
  };

  const broadcastSeriesIds = broadcasts.map(b => b.series_id);
  const availableForBroadcast = completedSeries.filter(s => !broadcastSeriesIds.includes(s.id));

  const TrendIcon = ({ trend }) => {
    if (trend === 'growing') return <ArrowUp className="w-3 h-3 text-green-400" />;
    if (trend === 'declining') return <ArrowDown className="w-3 h-3 text-red-400" />;
    return <Minus className="w-3 h-3 text-gray-500" />;
  };

  const MiniSparkline = ({ data, color = '#10b981' }) => {
    if (!data || data.length < 2) return null;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const w = 80;
    const h = 24;
    const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(' ');
    return (
      <svg width={w} height={h} className="opacity-80">
        <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  };

  const networkStats = liveData?.network_stats || {};
  const liveBroadcasts = liveData?.live_broadcasts || [];

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
      <div className="max-w-2xl mx-auto px-3">
        {/* Header */}
        <div className="flex items-center justify-between mb-3 mt-2">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/20 rounded-xl border border-emerald-500/30">
              <Radio className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="font-['Bebas_Neue'] text-2xl text-emerald-400" data-testid="emittente-title">La Tua TV</h1>
              <div className="flex items-center gap-1.5">
                <p className="text-[10px] text-gray-500">Emittente Televisiva</p>
                {livePolling && <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />}
                {livePolling && <span className="text-[9px] text-red-400 font-medium">LIVE</span>}
              </div>
            </div>
          </div>
          <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-white h-8 text-xs" onClick={airEpisodes} disabled={actionLoading || broadcasts.length === 0} data-testid="air-episode-btn">
            {actionLoading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Play className="w-3 h-3 mr-1" />}
            Manda in Onda
          </Button>
        </div>

        {/* Network Live Stats Banner */}
        {liveBroadcasts.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-3">
            <Card className="bg-gradient-to-r from-emerald-500/10 via-[#111113] to-cyan-500/10 border-emerald-500/20" data-testid="network-live-stats">
              <CardContent className="p-3">
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      <Eye className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-[9px] text-gray-500 uppercase">Live Viewers</span>
                    </div>
                    <motion.p
                      key={networkStats.total_live_viewers}
                      initial={{ scale: 1.1 }}
                      animate={{ scale: 1 }}
                      className="text-lg font-bold text-emerald-400"
                    >
                      {(networkStats.total_live_viewers || 0).toLocaleString()}
                    </motion.p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      <DollarSign className="w-3.5 h-3.5 text-green-400" />
                      <span className="text-[9px] text-gray-500 uppercase">Ricavi Ads</span>
                    </div>
                    <p className="text-lg font-bold text-green-400">${(networkStats.total_revenue || 0).toLocaleString()}</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      <Tv className="w-3.5 h-3.5 text-cyan-400" />
                      <span className="text-[9px] text-gray-500 uppercase">Slot Attivi</span>
                    </div>
                    <p className="text-lg font-bold text-cyan-400">{networkStats.active_slots || 0}/3</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Live Ratings Cards */}
        {liveBroadcasts.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-red-400" />
              <h3 className="text-sm font-semibold text-gray-300">Live Ratings</h3>
              <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
            </div>
            <div className="space-y-2">
              {liveBroadcasts.map(lb => {
                const cfg = SLOT_CONFIG[lb.timeslot] || SLOT_CONFIG.daytime;
                return (
                  <motion.div
                    key={lb.broadcast_id}
                    layout
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <Card
                      className={`bg-gradient-to-r ${cfg.gradient} ${cfg.border} border cursor-pointer hover:brightness-110 transition-all`}
                      onClick={() => openHistory(lb.broadcast_id)}
                      data-testid={`live-rating-${lb.timeslot}`}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            {lb.series_type === 'anime' ? <Sparkles className="w-4 h-4 text-orange-400" /> : <Tv className="w-4 h-4 text-blue-400" />}
                            <div>
                              <p className="text-xs font-semibold truncate max-w-[140px]">{lb.series_title}</p>
                              <p className="text-[9px] text-gray-500">{lb.timeslot_label} - Ep.{lb.current_episode}/{lb.total_episodes}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            <TrendIcon trend={lb.audience_trend} />
                            <MiniSparkline data={lb.sparkline} color={cfg.color === 'red' ? '#ef4444' : cfg.color === 'purple' ? '#a855f7' : '#eab308'} />
                          </div>
                        </div>
                        <div className="grid grid-cols-4 gap-2">
                          <div className="bg-black/20 rounded-lg p-1.5 text-center">
                            <motion.p key={lb.live_audience} initial={{ scale: 1.05 }} animate={{ scale: 1 }} className="text-sm font-bold text-white">
                              {lb.live_audience?.toLocaleString()}
                            </motion.p>
                            <p className="text-[8px] text-gray-500">Audience</p>
                          </div>
                          <div className="bg-black/20 rounded-lg p-1.5 text-center">
                            <p className="text-sm font-bold text-cyan-400">{lb.live_share}%</p>
                            <p className="text-[8px] text-gray-500">Share</p>
                          </div>
                          <div className="bg-black/20 rounded-lg p-1.5 text-center">
                            <p className="text-sm font-bold text-yellow-400">{lb.peak_audience?.toLocaleString()}</p>
                            <p className="text-[8px] text-gray-500">Picco</p>
                          </div>
                          <div className="bg-black/20 rounded-lg p-1.5 text-center">
                            <p className="text-sm font-bold text-green-400">${lb.total_revenue?.toLocaleString()}</p>
                            <p className="text-[8px] text-gray-500">Ricavi</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}

        {/* Palinsesto */}
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-gray-300">Palinsesto</h3>
        </div>
        <div className="space-y-2 mb-4">
          {Object.entries(timeslots).length > 0 ? Object.entries(timeslots).map(([key, slot]) => {
            const broadcast = broadcasts.find(b => b.timeslot === key);
            const cfg = SLOT_CONFIG[key] || SLOT_CONFIG.daytime;
            const SlotIcon = cfg.icon;
            return (
              <Card key={key} className={`bg-[#111113] ${cfg.border} border`} data-testid={`timeslot-${key}`}>
                <CardContent className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <SlotIcon className={`w-4 h-4 text-${cfg.color}-400`} />
                      <span className="text-sm font-bold">{slot.label}</span>
                      <span className="text-[10px] text-gray-500">{slot.time}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={`text-[9px] bg-${cfg.color}-500/10 text-${cfg.color}-400`}>x{slot.audience_mult}</Badge>
                      <span className="text-[9px] text-yellow-400">${slot.cost_per_day?.toLocaleString()}/g</span>
                    </div>
                  </div>
                  {broadcast ? (
                    <div className="bg-white/[0.03] rounded-lg p-2.5 flex items-center gap-2.5">
                      <div className={`w-10 h-14 rounded flex items-center justify-center flex-shrink-0 ${broadcast.series_type === 'anime' ? 'bg-orange-500/10' : 'bg-blue-500/10'}`}>
                        {broadcast.series_type === 'anime' ? <Sparkles className="w-5 h-5 text-orange-400" /> : <Tv className="w-5 h-5 text-blue-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{broadcast.series_title}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] text-gray-400">Ep. {broadcast.current_episode}/{broadcast.total_episodes}</span>
                          <span className="text-[10px] text-green-400">${broadcast.total_revenue?.toLocaleString()}</span>
                          <TrendIcon trend={broadcast.audience_trend} />
                        </div>
                        <Progress value={(broadcast.current_episode / broadcast.total_episodes) * 100} className="h-1 mt-1" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <button onClick={() => openHistory(broadcast.id)} className="p-1.5 text-cyan-400/50 hover:text-cyan-400" data-testid={`history-${key}`}>
                          <BarChart3 className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => removeSeries(key)} className="p-1.5 text-red-400/50 hover:text-red-400" data-testid={`remove-${key}`}>
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      className="w-full bg-white/[0.02] rounded-lg p-3 flex items-center justify-center border border-dashed border-white/10 hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all"
                      onClick={() => setAssigningSlot(key)}
                      data-testid={`assign-${key}`}
                    >
                      <Plus className="w-4 h-4 text-gray-500 mr-2" />
                      <span className="text-xs text-gray-500">Assegna una serie</span>
                    </button>
                  )}
                </CardContent>
              </Card>
            );
          }) : (
            ['daytime', 'prime_time', 'late_night'].map(key => (
              <Card key={key} className="bg-[#111113] border-white/5" data-testid={`timeslot-${key}`}>
                <CardContent className="p-3 text-center">
                  <p className="text-xs text-gray-500">{key.replace('_', ' ')}</p>
                  <button className="mt-2 text-[10px] text-emerald-400" onClick={() => setAssigningSlot(key)}>+ Assegna serie</button>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Assignment Panel */}
        <AnimatePresence>
          {assigningSlot && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }}>
              <Card className="bg-[#111113] border-emerald-500/20 mb-4" data-testid="assign-panel">
                <CardContent className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-emerald-400 font-semibold">Assegna a: {timeslots[assigningSlot]?.label || assigningSlot}</p>
                    <button onClick={() => setAssigningSlot(null)} className="text-gray-500 hover:text-white"><X className="w-4 h-4" /></button>
                  </div>
                  {availableForBroadcast.length === 0 ? (
                    <div className="text-center py-4">
                      <p className="text-xs text-gray-500 mb-2">Nessuna serie disponibile. Produci e completa una serie!</p>
                      <div className="flex gap-2 justify-center">
                        <Button size="sm" variant="outline" className="text-xs border-blue-500/30 text-blue-400" onClick={() => navigate('/create-series')}>Serie TV</Button>
                        <Button size="sm" variant="outline" className="text-xs border-orange-500/30 text-orange-400" onClick={() => navigate('/create-anime')}>Anime</Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {availableForBroadcast.map(s => (
                        <div key={s.id}
                          className="flex items-center gap-2 p-2 rounded-lg cursor-pointer border border-white/5 hover:bg-emerald-500/5 hover:border-emerald-500/20 transition-all"
                          onClick={() => assignSeries(s.id)}
                          data-testid={`assign-series-${s.id}`}
                        >
                          <div className={`w-8 h-10 rounded flex items-center justify-center ${s.type === 'anime' ? 'bg-orange-500/10' : 'bg-blue-500/10'}`}>
                            {s.type === 'anime' ? <Sparkles className="w-4 h-4 text-orange-400" /> : <Tv className="w-4 h-4 text-blue-400" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium truncate">{s.title}</p>
                            <p className="text-[10px] text-gray-500">{s.typeLabel} - {s.num_episodes} ep.</p>
                          </div>
                          <Badge className="bg-yellow-500/20 text-yellow-400 text-[9px]">{s.quality_score}/100</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Info */}
        <Card className="bg-[#111113] border-emerald-500/10">
          <CardContent className="p-3">
            <p className="text-[10px] text-gray-500 leading-relaxed">
              Assegna le tue serie completate agli slot del palinsesto. Clicca "Manda in Onda" per trasmettere il prossimo episodio.
              I Live Ratings si aggiornano ogni 5 secondi. L'audience dipende dalla qualita della serie, dalla fascia oraria e dal momentum.
              Clicca su una card live per vedere lo storico dettagliato degli episodi.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Episode History Dialog */}
      <Dialog open={!!historyDialog} onOpenChange={(open) => { if (!open) { setHistoryDialog(null); setHistoryData(null); } }}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-md max-h-[85vh] overflow-y-auto p-0" data-testid="history-dialog">
          <DialogHeader className="p-4 pb-0">
            <DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              Storico Episodi
            </DialogTitle>
          </DialogHeader>
          {historyLoading ? (
            <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-emerald-400 animate-spin" /></div>
          ) : historyData ? (
            <div className="p-4 pt-2 space-y-3">
              {/* Broadcast Info */}
              <div className="flex items-center gap-3 bg-white/[0.03] rounded-lg p-3">
                <div className={`w-10 h-14 rounded flex items-center justify-center ${historyData.broadcast.series_type === 'anime' ? 'bg-orange-500/10' : 'bg-blue-500/10'}`}>
                  {historyData.broadcast.series_type === 'anime' ? <Sparkles className="w-5 h-5 text-orange-400" /> : <Tv className="w-5 h-5 text-blue-400" />}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold">{historyData.broadcast.series_title}</p>
                  <p className="text-[10px] text-gray-500">{historyData.broadcast.timeslot_label} - Q: {historyData.broadcast.quality_score}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Badge className="text-[8px] bg-emerald-500/10 text-emerald-400">Ep. {historyData.broadcast.current_episode}/{historyData.broadcast.total_episodes}</Badge>
                    <TrendIcon trend={historyData.broadcast.audience_trend} />
                  </div>
                </div>
              </div>

              {/* Analytics Grid */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-blue-500/5 rounded-lg p-2 text-center border border-blue-500/10">
                  <p className="text-xs text-gray-500">Audience Media</p>
                  <p className="text-base font-bold text-blue-400">{historyData.analytics.avg_audience?.toLocaleString()}</p>
                </div>
                <div className="bg-yellow-500/5 rounded-lg p-2 text-center border border-yellow-500/10">
                  <p className="text-xs text-gray-500">Picco Massimo</p>
                  <p className="text-base font-bold text-yellow-400">{historyData.analytics.peak_audience?.toLocaleString()}</p>
                </div>
                <div className="bg-green-500/5 rounded-lg p-2 text-center border border-green-500/10">
                  <p className="text-xs text-gray-500">Ricavi Totali</p>
                  <p className="text-base font-bold text-green-400">${historyData.broadcast.total_revenue?.toLocaleString()}</p>
                </div>
                <div className="bg-cyan-500/5 rounded-lg p-2 text-center border border-cyan-500/10">
                  <p className="text-xs text-gray-500">Audience Totale</p>
                  <p className="text-base font-bold text-cyan-400">{historyData.broadcast.total_audience?.toLocaleString()}</p>
                </div>
              </div>

              {/* Audience Bar Chart */}
              {historyData.episodes.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-2 font-semibold">Audience per Episodio</p>
                  <div className="bg-black/30 rounded-lg p-3">
                    {(() => {
                      const eps = historyData.episodes;
                      const maxAud = Math.max(...eps.map(e => e.audience || 0));
                      return (
                        <div className="flex items-end gap-[3px] h-28">
                          {eps.map((ep, i) => {
                            const pct = maxAud > 0 ? (ep.audience / maxAud) * 100 : 0;
                            const isGrowing = ep.trend === 'growing';
                            const isDeclining = ep.trend === 'declining';
                            return (
                              <div key={i} className="flex-1 flex flex-col items-center gap-0.5 group relative">
                                <div className="absolute -top-6 left-1/2 -translate-x-1/2 hidden group-hover:block bg-black/90 text-[8px] text-white px-1.5 py-0.5 rounded whitespace-nowrap z-10">
                                  {ep.audience?.toLocaleString()} | ${ep.revenue?.toLocaleString()} | {ep.share_percent}%
                                </div>
                                <div
                                  className={`w-full rounded-t transition-all ${isGrowing ? 'bg-green-500' : isDeclining ? 'bg-red-500' : 'bg-cyan-500'}`}
                                  style={{ height: `${Math.max(4, pct)}%` }}
                                />
                                <span className="text-[7px] text-gray-600">{ep.number}</span>
                              </div>
                            );
                          })}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Episode List */}
              {historyData.episodes.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-2 font-semibold">Dettaglio Episodi</p>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {historyData.episodes.slice().reverse().map(ep => (
                      <div key={ep.number} className="flex items-center justify-between bg-white/[0.02] rounded p-2">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-gray-400 w-8">Ep.{ep.number}</span>
                          <TrendIcon trend={ep.trend} />
                        </div>
                        <div className="flex items-center gap-3 text-[10px]">
                          <span className="text-blue-400">{ep.audience?.toLocaleString()} spett.</span>
                          <span className="text-cyan-400">{ep.share_percent}%</span>
                          <span className="text-green-400">${ep.revenue?.toLocaleString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {historyData.episodes.length === 0 && (
                <p className="text-center text-gray-500 text-xs py-4">Nessun episodio ancora trasmesso</p>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
