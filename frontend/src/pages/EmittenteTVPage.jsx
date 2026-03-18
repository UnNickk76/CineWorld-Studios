// CineWorld - Emittente TV Page
// Full TV Network management: broadcast schedule, assign series, air episodes, track audience/revenue

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Radio, Tv, Sparkles, Lock, Clock, Users, DollarSign, TrendingUp, Loader2, Plus, X, Play, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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

  useEffect(() => { loadData(); }, [loadData]);

  const assignSeries = async (seriesId) => {
    if (!assigningSlot) return;
    setActionLoading(true);
    try {
      const res = await api.post('/emittente-tv/assign', { series_id: seriesId, timeslot: assigningSlot });
      toast.success(res.data.message);
      setAssigningSlot(null);
      loadData();
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
            toast.success(`"${r.series}" Ep.${r.episode}: ${r.audience?.toLocaleString()} spettatori, $${r.revenue?.toLocaleString()}`);
          }
        }
      }
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
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

  // Broadcasting slots configuration
  const SLOT_CONFIG = {
    daytime: { color: 'yellow', icon: Clock },
    prime_time: { color: 'red', icon: TrendingUp },
    late_night: { color: 'purple', icon: Clock },
  };

  // Series that aren't already broadcasting
  const broadcastSeriesIds = broadcasts.map(b => b.series_id);
  const availableForBroadcast = completedSeries.filter(s => !broadcastSeriesIds.includes(s.id));

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
      <div className="max-w-2xl mx-auto px-3">
        {/* Header */}
        <div className="flex items-center justify-between mb-4 mt-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/20 rounded-xl border border-emerald-500/30">
              <Radio className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h1 className="font-['Bebas_Neue'] text-2xl text-emerald-400" data-testid="emittente-title">La Tua TV</h1>
              <p className="text-xs text-gray-500">Gestisci il palinsesto</p>
            </div>
          </div>
          <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-white h-8 text-xs" onClick={airEpisodes} disabled={actionLoading || broadcasts.length === 0} data-testid="air-episode-btn">
            {actionLoading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Play className="w-3 h-3 mr-1" />}
            Manda in Onda
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <Card className="bg-[#111113] border-white/5">
            <CardContent className="p-2 text-center">
              <Users className="w-4 h-4 text-blue-400 mx-auto mb-1" />
              <p className="text-base font-bold">{(emittente?.total_audience_reached || 0).toLocaleString()}</p>
              <p className="text-[9px] text-gray-500">Audience Totale</p>
            </CardContent>
          </Card>
          <Card className="bg-[#111113] border-white/5">
            <CardContent className="p-2 text-center">
              <DollarSign className="w-4 h-4 text-green-400 mx-auto mb-1" />
              <p className="text-base font-bold text-green-400">${(emittente?.total_ad_revenue || 0).toLocaleString()}</p>
              <p className="text-[9px] text-gray-500">Ricavi Ads</p>
            </CardContent>
          </Card>
          <Card className="bg-[#111113] border-white/5">
            <CardContent className="p-2 text-center">
              <Tv className="w-4 h-4 text-purple-400 mx-auto mb-1" />
              <p className="text-base font-bold">{broadcasts.length}/3</p>
              <p className="text-[9px] text-gray-500">Slot Attivi</p>
            </CardContent>
          </Card>
        </div>

        {/* Timeslots */}
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Palinsesto</h3>
        <div className="space-y-2 mb-4">
          {Object.entries(timeslots).length > 0 ? Object.entries(timeslots).map(([key, slot]) => {
            const broadcast = broadcasts.find(b => b.timeslot === key);
            const cfg = SLOT_CONFIG[key] || { color: 'gray', icon: Clock };
            const SlotIcon = cfg.icon;
            return (
              <Card key={key} className="bg-[#111113] border-white/5" data-testid={`timeslot-${key}`}>
                <CardContent className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <SlotIcon className={`w-4 h-4 text-${cfg.color}-400`} />
                      <span className="text-sm font-bold">{slot.label}</span>
                      <span className="text-[10px] text-gray-500">{slot.time}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={`text-[9px] bg-${cfg.color}-500/10 text-${cfg.color}-400`}>x{slot.audience_mult} audience</Badge>
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
                          <span className="text-[10px] text-blue-400">{broadcast.total_audience?.toLocaleString()} spett.</span>
                        </div>
                        <Progress value={(broadcast.current_episode / broadcast.total_episodes) * 100} className="h-1 mt-1" />
                      </div>
                      <button onClick={() => removeSeries(key)} className="p-1.5 text-red-400/50 hover:text-red-400" data-testid={`remove-${key}`}>
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
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
            // Fallback timeslots
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
                <CardHeader className="pb-1">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm text-emerald-400">Assegna a: {timeslots[assigningSlot]?.label || assigningSlot}</CardTitle>
                    <button onClick={() => setAssigningSlot(null)} className="text-gray-500 hover:text-white"><X className="w-4 h-4" /></button>
                  </div>
                </CardHeader>
                <CardContent className="p-3 pt-0">
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
              Assegna le tue serie completate agli slot del palinsesto. Clicca "Manda in Onda" per trasmettere il prossimo episodio di ogni serie attiva. 
              L'audience dipende dalla qualità della serie e dalla fascia oraria. I ricavi pubblicitari vengono accreditati automaticamente.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
