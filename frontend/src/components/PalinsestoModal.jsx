// CineWorld - Palinsesto Modal
// Episode management + real calendar scheduling for series/anime

import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { Input } from './ui/input';
import { useConfirm } from './ConfirmDialog';
import {
  Tv, Sparkles, Play, Calendar, Clock, Eye, Users, Zap, RefreshCw, Ban,
  Loader2, ChevronDown, ChevronUp, Send, Timer, Star
} from 'lucide-react';
import { toast } from 'sonner';

export function PalinsestoModal({ open, onClose, series, stationId, onRefresh }) {
  const { api } = useContext(AuthContext);
  const gameConfirm = useConfirm();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedEp, setExpandedEp] = useState(null);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  // Schedule form state
  const [schedMode, setSchedMode] = useState('standard');
  const [schedDate, setSchedDate] = useState('');
  const [schedTime, setSchedTime] = useState('21:00');
  const [schedInterval, setSchedInterval] = useState(1);
  const [schedMarathonEps, setSchedMarathonEps] = useState(2);
  const [schedImmediate, setSchedImmediate] = useState(false);

  useEffect(() => {
    if (!open || !series || !stationId) return;
    loadDetail();
    // Set default date to tomorrow
    const tomorrow = new Date(Date.now() + 86400000);
    setSchedDate(tomorrow.toISOString().split('T')[0]);
  }, [open, series, stationId]);

  const loadDetail = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/tv-stations/${stationId}/broadcast/${series.id}`);
      setDetail(res.data);
    } catch { setDetail(null); }
    setLoading(false);
  };

  const doSchedule = async () => {
    let startDt;
    if (schedImmediate) {
      startDt = new Date().toISOString();
    } else {
      startDt = `${schedDate}T${schedTime}:00`;
    }
    setActionLoading('schedule');
    try {
      const body = {
        station_id: stationId,
        content_id: series.id,
        start_datetime: startDt,
        mode: schedMode,
        air_interval_days: schedMode === 'binge' ? 0 : schedInterval,
        marathon_eps_per_slot: schedMode === 'marathon' ? schedMarathonEps : 1,
        immediate_first: schedImmediate,
      };
      const res = await api.post('/tv-stations/schedule-broadcast', body);
      toast.success(res.data.message);
      setShowScheduleForm(false);
      loadDetail();
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore programmazione'); }
    setActionLoading(null);
  };

  const doRetire = async () => {
    if (!await gameConfirm({ title: 'Ritirare questa serie?', subtitle: 'Verrà rimossa dal palinsesto.', confirmLabel: 'Ritira' })) return;
    setActionLoading('retire');
    try {
      const res = await api.post('/tv-stations/retire-series', { station_id: stationId, content_id: series.id });
      toast.success(res.data.message);
      loadDetail();
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const doReruns = async () => {
    if (!await gameConfirm({ title: 'Avviare le repliche?', subtitle: 'Audience ridotta al 40%.', confirmLabel: 'Avvia Repliche' })) return;
    setActionLoading('reruns');
    try {
      const res = await api.post('/tv-stations/start-reruns', { station_id: stationId, content_id: series.id });
      toast.success(res.data.message);
      loadDetail();
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const doSendToTV = async () => {
    setActionLoading('send');
    try {
      const ctype = series.type === 'anime' || series.content_type === 'anime' ? 'anime' : 'tv_series';
      const res = await api.post('/tv-stations/add-content', { station_id: stationId, content_id: series.id, content_type: ctype });
      toast.success(res.data.message);
      loadDetail();
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  if (!series) return null;
  const bstate = detail?.broadcast_state || 'idle';
  const isAnime = series.type === 'anime' || series.content_type === 'anime';

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="bg-[#0F0F10] border-white/10 max-w-[420px] max-h-[90vh] overflow-y-auto p-0 [&>button]:hidden" data-testid="palinsesto-modal">
        <DialogHeader className="p-4 pb-2 flex-row items-center gap-2">
          <button onClick={onClose} className="w-7 h-7 rounded-full bg-white/5 flex items-center justify-center text-gray-400 hover:bg-white/10">✕</button>
          <div className="flex-1">
            <DialogTitle className="text-sm font-bold flex items-center gap-2">
              {isAnime ? <Sparkles className="w-4 h-4 text-orange-400" /> : <Tv className="w-4 h-4 text-blue-400" />}
              {series.title}
            </DialogTitle>
          </div>
          <Badge className={`text-[8px] border-0 ${bstate === 'airing' ? 'bg-green-500/20 text-green-400' : bstate === 'scheduled' ? 'bg-blue-500/20 text-blue-400' : bstate === 'completed' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-gray-500/20 text-gray-400'}`}>
            {bstate === 'airing' ? 'In onda' : bstate === 'scheduled' ? 'Programmata' : bstate === 'completed' ? 'Completata' : bstate === 'retired' ? 'Ritirata' : 'Non in onda'}
          </Badge>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12"><Loader2 className="w-5 h-5 text-gray-500 animate-spin" /></div>
        ) : (
          <div className="px-4 pb-4 space-y-3">
            {/* Actions bar */}
            <div className="flex flex-wrap gap-1.5" data-testid="palinsesto-actions">
              {(bstate === 'idle') && (
                <Button size="sm" className="h-7 text-[10px] bg-green-500/20 text-green-400 hover:bg-green-500/30" onClick={() => setShowScheduleForm(!showScheduleForm)} data-testid="btn-programma">
                  <Calendar className="w-3 h-3 mr-1" /> Programma Uscita
                </Button>
              )}
              {(bstate === 'idle') && (
                <Button size="sm" className="h-7 text-[10px] bg-blue-500/20 text-blue-400 hover:bg-blue-500/30" onClick={doSendToTV} disabled={actionLoading === 'send'} data-testid="btn-invia-tv">
                  <Send className="w-3 h-3 mr-1" /> Invia alla TV
                </Button>
              )}
              {(bstate === 'completed' || bstate === 'retired') && (
                <Button size="sm" className="h-7 text-[10px] bg-amber-500/20 text-amber-400 hover:bg-amber-500/30" onClick={doReruns} disabled={actionLoading === 'reruns'} data-testid="btn-replica">
                  <RefreshCw className="w-3 h-3 mr-1" /> Replica
                </Button>
              )}
              {(bstate === 'completed' || bstate === 'airing') && (
                <Button size="sm" variant="outline" className="h-7 text-[10px] border-red-500/20 text-red-400" onClick={doRetire} disabled={actionLoading === 'retire' || bstate === 'airing'} data-testid="btn-ritira">
                  <Ban className="w-3 h-3 mr-1" /> Ritira
                </Button>
              )}
              {(bstate === 'scheduled' || bstate === 'idle') && (
                <Button size="sm" className="h-7 text-[10px] bg-purple-500/20 text-purple-400 hover:bg-purple-500/30" onClick={() => { setSchedMode('binge'); setSchedImmediate(true); setShowScheduleForm(true); }} data-testid="btn-maratona">
                  <Zap className="w-3 h-3 mr-1" /> Maratona
                </Button>
              )}
            </div>

            {/* Schedule Form */}
            {showScheduleForm && (
              <Card className="bg-[#1A1A1C] border-yellow-500/20">
                <CardContent className="p-3 space-y-3">
                  <p className="text-[10px] text-yellow-400 font-bold uppercase tracking-wider">Programma Uscita</p>

                  {/* Mode selection */}
                  <div className="grid grid-cols-3 gap-1.5">
                    {[{v:'standard',l:'Standard',d:'1 ep/slot'},{v:'marathon',l:'Maratona',d:'2-3 ep/slot'},{v:'binge',l:'Binge',d:'Tutti subito'}].map(m => (
                      <button key={m.v} onClick={() => setSchedMode(m.v)} className={`p-2 rounded-lg text-center transition-all ${schedMode === m.v ? 'bg-yellow-500/15 border border-yellow-500/30 text-yellow-400' : 'bg-black/30 border border-white/5 text-gray-500 hover:border-white/15'}`}>
                        <p className="text-[10px] font-bold">{m.l}</p>
                        <p className="text-[8px] opacity-60">{m.d}</p>
                      </button>
                    ))}
                  </div>

                  {/* Date/Time (not for binge immediate) */}
                  {schedMode !== 'binge' && (
                    <div className="space-y-2">
                      <label className="flex items-center gap-2">
                        <input type="checkbox" checked={schedImmediate} onChange={(e) => setSchedImmediate(e.target.checked)} className="rounded" />
                        <span className="text-[10px] text-gray-400">Primo episodio subito</span>
                      </label>
                      {!schedImmediate && (
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <p className="text-[9px] text-gray-500 mb-1">Data inizio</p>
                            <Input type="date" value={schedDate} onChange={e => setSchedDate(e.target.value)} className="h-8 text-xs bg-black/30 border-white/10" data-testid="sched-date" />
                          </div>
                          <div>
                            <p className="text-[9px] text-gray-500 mb-1">Orario</p>
                            <Input type="time" value={schedTime} onChange={e => setSchedTime(e.target.value)} className="h-8 text-xs bg-black/30 border-white/10" data-testid="sched-time" />
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Interval */}
                  {schedMode !== 'binge' && (
                    <div>
                      <p className="text-[9px] text-gray-500 mb-1">Ogni quanti giorni</p>
                      <div className="flex gap-1">
                        {[1,2,3,7].map(d => (
                          <button key={d} onClick={() => setSchedInterval(d)} className={`flex-1 h-7 rounded-lg text-[10px] transition-all ${schedInterval === d ? 'bg-yellow-500/15 border border-yellow-500/30 text-yellow-400' : 'bg-black/30 border border-white/5 text-gray-500'}`}>
                            {d === 7 ? 'Settim.' : `${d}g`}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Marathon episodes per slot */}
                  {schedMode === 'marathon' && (
                    <div>
                      <p className="text-[9px] text-gray-500 mb-1">Episodi per slot</p>
                      <div className="flex gap-1">
                        {[2,3,4,5].map(n => (
                          <button key={n} onClick={() => setSchedMarathonEps(n)} className={`flex-1 h-7 rounded-lg text-[10px] ${schedMarathonEps === n ? 'bg-purple-500/15 border border-purple-500/30 text-purple-400' : 'bg-black/30 border border-white/5 text-gray-500'}`}>
                            {n} ep
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <Button className="w-full h-9 bg-gradient-to-r from-yellow-500 to-amber-500 text-black font-bold text-xs rounded-xl" onClick={doSchedule} disabled={actionLoading === 'schedule'} data-testid="confirm-schedule">
                    {actionLoading === 'schedule' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Calendar className="w-3 h-3 mr-1" />}
                    PROGRAMMA
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Episodes list */}
            <div data-testid="episodes-list">
              <p className="text-[10px] text-gray-500 mb-2 uppercase tracking-wider">Episodi ({detail?.total_episodes || 0})</p>
              <div className="space-y-1">
                {(detail?.episodes || []).map(ep => {
                  const isAired = ep.broadcast_state === 'aired';
                  const isOnAir = ep.broadcast_state === 'on_air';
                  const isPending = !isAired && !isOnAir;
                  const isExpanded = expandedEp === ep.number;
                  const typeLabels = { peak: 'PEAK', filler: 'FILLER', plot_twist: 'TWIST', season_finale: 'FINALE' };
                  const typeColors = { peak: 'text-amber-400', filler: 'text-gray-500', plot_twist: 'text-purple-400', season_finale: 'text-red-400' };

                  // Countdown for pending episodes
                  let countdown = null;
                  if (isPending && ep.release_datetime) {
                    const diff = new Date(ep.release_datetime) - new Date();
                    if (diff > 0) {
                      const days = Math.floor(diff / 86400000);
                      const hours = Math.floor((diff % 86400000) / 3600000);
                      countdown = days > 0 ? `${days}g ${hours}h` : `${hours}h`;
                    }
                  }

                  return (
                    <div key={ep.number}>
                      <div
                        onClick={() => (isAired || ep.mini_plot || ep.plot) ? setExpandedEp(isExpanded ? null : ep.number) : null}
                        className={`rounded-lg p-2.5 flex items-center gap-2 transition-all ${
                          isAired ? 'bg-white/[0.03] border border-green-500/10 cursor-pointer hover:bg-white/[0.05]'
                          : isOnAir ? 'bg-green-500/5 border border-green-500/20'
                          : (ep.mini_plot || ep.plot) ? 'bg-black/30 border border-white/5 cursor-pointer hover:bg-white/[0.05]'
                          : 'bg-black/20 opacity-40'
                        }`}
                        data-testid={`ep-${ep.number}`}
                      >
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${
                          isAired ? 'bg-green-500/20 text-green-400'
                          : isOnAir ? 'bg-green-500 text-white'
                          : 'bg-white/5 text-gray-600'
                        }`}>{ep.number}</div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <p className="text-[11px] font-medium truncate">{ep.title || `Episodio ${ep.number}`}</p>
                            {typeLabels[ep.episode_type] && <span className={`text-[7px] font-bold ${typeColors[ep.episode_type]}`}>{typeLabels[ep.episode_type]}</span>}
                          </div>
                          {isPending && countdown && (
                            <p className="text-[9px] text-gray-600 flex items-center gap-1"><Timer className="w-2.5 h-2.5" /> Esce tra {countdown}</p>
                          )}
                        </div>

                        <div className="text-right flex-shrink-0">
                          {isAired && (
                            <div className="flex items-center gap-2">
                              {ep.consensus_pct > 0 && (
                                <span className={`text-[10px] font-bold ${ep.consensus_pct >= 70 ? 'text-green-400' : ep.consensus_pct >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                                  {ep.consensus_pct}%
                                </span>
                              )}
                              <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                            </div>
                          )}
                          {!isAired && !isOnAir && (ep.mini_plot || ep.plot) && (
                            <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                          )}
                          {isOnAir && (
                            <div className="flex items-center gap-1">
                              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                              <span className="text-[9px] text-green-400 font-bold">LIVE</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Expanded details — shows plot for aired + mini_plot for all with synopsis */}
                      {isExpanded && (isAired || ep.mini_plot || ep.plot) && (
                        <div className="ml-9 mt-1 p-2.5 rounded-lg bg-white/[0.02] border border-white/5 space-y-2">
                          {(ep.plot || ep.mini_plot) && (
                            <p className="text-[10px] text-gray-400 italic leading-relaxed">
                              {ep.plot || ep.mini_plot}
                            </p>
                          )}
                          {isAired && (
                            <>
                              <div className="flex items-center gap-3 text-[10px]">
                                <span className="flex items-center gap-1 text-cyan-400"><Eye className="w-3 h-3" /> {(ep.viewers || 0).toLocaleString()} views</span>
                                <span className={`flex items-center gap-1 font-bold ${ep.consensus_pct >= 70 ? 'text-green-400' : ep.consensus_pct >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                                  <Star className="w-3 h-3" /> {ep.consensus_pct || 0}% consenso
                                </span>
                              </div>
                              {ep.broadcast_rating > 0 && (
                                <div className="flex items-center gap-1 text-[9px] text-gray-500">
                                  Rating: {ep.broadcast_rating}/10
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
