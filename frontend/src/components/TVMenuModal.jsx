// CineWorld - TV Menu Modal (Hub Gestione Emittente)
// 4 sections: Contenuti, Palinsesto, Pubblicità, Statistiche TV

import React, { useState, useEffect, useRef, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { useConfirm } from './ConfirmDialog';
import {
  Tv, Sparkles, Film, Settings, Plus, X, Loader2, DollarSign, Eye,
  TrendingUp, Check, Trash2, BarChart3, Clock, Users, Zap,
  RefreshCw, Ban, ChevronRight, Radio, Star, Snowflake
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300';
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};

const TABS = [
  { id: 'contenuti', label: 'Contenuti', icon: Film },
  { id: 'palinsesto', label: 'Palinsesto', icon: Zap },
  { id: 'pubblicita', label: 'Pubblicità', icon: DollarSign },
  { id: 'gestione', label: 'Gestione', icon: Settings },
  { id: 'statistiche', label: 'Statistiche', icon: BarChart3 },
];

const DELAY_OPTIONS = [
  { hours: 6, label: '6 ore' },
  { hours: 12, label: '12 ore' },
  { hours: 24, label: '24 ore' },
  { hours: 48, label: '2 giorni' },
  { hours: 96, label: '4 giorni' },
  { hours: 144, label: '6 giorni' },
];

export function TVMenuModal({ open, onClose, station, enrichedContents, capacity, shareData, infraLevel, onRefresh, onOpenPalinsesto, onOpenContentDetail }) {
  const { api } = useContext(AuthContext);
  const gameConfirm = useConfirm();
  const [activeTab, setActiveTab] = useState('contenuti');
  const [contentLoading, setContentLoading] = useState(false);
  const [availableContent, setAvailableContent] = useState({ films: [], tv_series: [], anime: [] });
  const [showAddType, setShowAddType] = useState(null);
  const [settingsAd, setSettingsAd] = useState(station?.ad_seconds || 30);
  const [savingSettings, setSavingSettings] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  // Prossimamente state
  const [upcomingItems, setUpcomingItems] = useState([]);
  const [showAddUpcoming, setShowAddUpcoming] = useState(false);
  const [availableUpcoming, setAvailableUpcoming] = useState({ films: [], tv_series: [], anime: [] });
  const [upcomingLoading, setUpcomingLoading] = useState(false);
  const [timerPopup, setTimerPopup] = useState(null); // { content, contentType }
  const [addingUpcoming, setAddingUpcoming] = useState(false);

  // Stile branding state
  const [availableStyles, setAvailableStyles] = useState([]);
  const [selectedStyle, setSelectedStyle] = useState(station?.style || 'default');
  const [savingStyle, setSavingStyle] = useState(false);

  useEffect(() => {
    if (open && station) {
      setSettingsAd(station.ad_seconds || 30);
      setSelectedStyle(station.style || 'default');
      loadUpcoming();
      // Load available branding styles once
      api.get('/tv-stations/available-styles').then(r => setAvailableStyles(r.data?.styles || [])).catch(() => {});
    }
  }, [open, station]);

  if (!station) return null;

  const stationId = station.id;
  const contents = enrichedContents || { films: [], tv_series: [], anime: [] };
  const allSeries = [...(contents.tv_series || []), ...(contents.anime || [])];

  // Load upcoming content (new system + old scheduled_for_tv system merged)
  async function loadUpcoming() {
    try {
      const [upRes, schRes] = await Promise.all([
        api.get(`/tv-stations/${stationId}/upcoming`),
        api.get(`/tv-stations/${stationId}/scheduled`).catch(() => ({ data: { items: [] } }))
      ]);
      const upItems = upRes.data.items || [];
      const schItems = (schRes.data.items || []).map(s => ({
        content_id: s.id,
        title: s.title,
        poster_url: s.poster_url,
        content_type: s.content_type,
        frozen: false,
        remaining_seconds: 0,
        _isOldScheduled: true,
      }));
      const upIds = new Set(upItems.map(u => u.content_id));
      const merged = [...upItems, ...schItems.filter(s => !upIds.has(s.content_id))];
      setUpcomingItems(merged);
    } catch { setUpcomingItems([]); }
  }

  // Open add content picker (for existing palette)
  const openAddContent = async (type) => {
    setShowAddType(type);
    setContentLoading(true);
    try {
      const res = await api.get(`/tv-stations/available-content/${stationId}`);
      setAvailableContent(res.data);
    } catch { toast.error('Errore caricamento contenuti'); }
    setContentLoading(false);
  };

  // Open add upcoming picker
  const openAddUpcomingPicker = async () => {
    setShowAddUpcoming(true);
    setUpcomingLoading(true);
    try {
      const res = await api.get(`/tv-stations/available-upcoming/${stationId}`);
      setAvailableUpcoming(res.data);
    } catch { toast.error('Errore caricamento'); }
    setUpcomingLoading(false);
  };

  const addContent = async (contentId, contentType) => {
    try {
      const res = await api.post('/tv-stations/add-content', { station_id: stationId, content_id: contentId, content_type: contentType });
      toast.success(res.data.message);
      onRefresh?.();
      openAddContent(contentType);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const removeContent = async (contentId) => {
    if (!await gameConfirm({ title: 'Rimuovere questo contenuto?', subtitle: 'Verrà tolto dal palinsesto TV.', confirmLabel: 'Rimuovi' })) return;
    try {
      await api.post('/tv-stations/remove-content', { station_id: stationId, content_id: contentId });
      toast.success('Contenuto rimosso');
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  // Add upcoming with timer
  const handleAddUpcoming = async (delayHours) => {
    if (!timerPopup) return;
    setAddingUpcoming(true);
    try {
      const res = await api.post('/tv-stations/add-upcoming', {
        station_id: stationId,
        content_id: timerPopup.content.id,
        content_type: timerPopup.contentType,
        delay_hours: delayHours,
      });
      toast.success(res.data.message);
      setTimerPopup(null);
      setShowAddUpcoming(false);
      loadUpcoming();

      // For series/anime with episodes → open PalinsestoModal
      if (timerPopup.contentType !== 'film' && (timerPopup.content.num_episodes || 0) > 0) {
        onClose();
        onOpenPalinsesto?.(timerPopup.content);
      }
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setAddingUpcoming(false);
  };

  const removeUpcoming = async (contentId) => {
    try {
      await api.post('/tv-stations/remove-upcoming', { station_id: stationId, content_id: contentId });
      toast.success('Rimosso dai Prossimamente');
      loadUpcoming();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  // Ad settings
  const saveSettings = async () => {
    setSavingSettings(true);
    try {
      await api.post('/tv-stations/update-ads', { station_id: stationId, ad_seconds: settingsAd });
      toast.success('Impostazioni salvate');
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setSavingSettings(false);
  };

  // Style update
  const saveStyle = async () => {
    setSavingStyle(true);
    try {
      await api.post('/tv-stations/update-style', { station_id: stationId, style: selectedStyle });
      toast.success('Stile aggiornato');
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setSavingStyle(false);
  };

  // Broadcast actions
  const retireSeries = async (contentId) => {
    if (!await gameConfirm({ title: 'Ritirare questa serie?', subtitle: 'Verrà rimossa dal palinsesto.', confirmLabel: 'Ritira' })) return;
    setActionLoading(`retire-${contentId}`);
    try {
      await api.post('/tv-stations/retire-series', { station_id: stationId, content_id: contentId });
      toast.success('Serie ritirata');
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const startReruns = async (contentId) => {
    if (!await gameConfirm({ title: 'Avviare le repliche?', subtitle: 'Audience ridotta al 40%.', confirmLabel: 'Avvia Repliche' })) return;
    setActionLoading(`reruns-${contentId}`);
    try {
      await api.post('/tv-stations/start-reruns', { station_id: stationId, content_id: contentId });
      toast.success('Repliche avviate');
      onRefresh?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) { onClose(); setShowAddType(null); setShowAddUpcoming(false); setTimerPopup(null); } }}>
      <DialogContent className="bg-[#0A0A0B] border-white/10 max-w-[460px] max-h-[90vh] overflow-hidden p-0 [&>button]:hidden" data-testid="tv-menu-modal">
        {/* Header */}
        <div className="px-4 pt-4 pb-2">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Radio className="w-5 h-5 text-red-500" />
              <h2 className="font-['Bebas_Neue'] text-xl text-red-500">{station.station_name}</h2>
            </div>
            <button onClick={onClose} className="w-7 h-7 rounded-full bg-white/5 flex items-center justify-center text-gray-400 hover:bg-white/10" data-testid="tv-menu-close">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1" data-testid="tv-menu-tabs">
            {TABS.map(tab => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} onClick={() => { setActiveTab(tab.id); setShowAddType(null); setShowAddUpcoming(false); setTimerPopup(null); }}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-[10px] font-medium transition-all ${activeTab === tab.id ? 'bg-red-500/15 text-red-400 border border-red-500/25' : 'text-gray-500 hover:text-gray-300'}`}
                  data-testid={`tab-${tab.id}`}
                >
                  <Icon className="w-3 h-3" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="overflow-y-auto px-4 pb-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>

          {/* === CONTENUTI TAB === */}
          {activeTab === 'contenuti' && !showAddType && !showAddUpcoming && !timerPopup && (
            <div className="space-y-3" data-testid="tab-contenuti-content">
              {/* Content rows: Film, Serie TV, Anime */}
              {['film', 'tv_series', 'anime'].map(type => {
                const labels = { film: 'Film', tv_series: 'Serie TV', anime: 'Anime' };
                const colors = { film: 'yellow', tv_series: 'blue', anime: 'orange' };
                const icons = { film: Film, tv_series: Tv, anime: Sparkles };
                const Icon = icons[type];
                const capKey = type === 'film' ? 'films' : type;
                const items = contents[capKey] || [];
                const maxItems = capacity?.[capKey] || 99;
                const canAdd = items.length < maxItems;
                return (
                  <div key={type}>
                    <div className="flex items-center gap-2 mb-1.5">
                      <Icon className={`w-3.5 h-3.5 text-${colors[type]}-400`} />
                      <span className="text-[10px] font-bold">{labels[type]}</span>
                      <Badge className="text-[8px] bg-white/5 border-0">{items.length}/{maxItems}</Badge>
                    </div>
                    <ScrollRow items={items} color={colors[type]} canAdd={canAdd} onAdd={() => openAddContent(type)} onRemove={removeContent} onItemClick={(item) => { if (onOpenContentDetail) onOpenContentDetail({...item, type: type, content_type: type}); }} />
                  </div>
                );
              })}

              {/* PROSSIMAMENTE section */}
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-[10px] font-bold">Prossimamente</span>
                  <Badge className="text-[8px] bg-cyan-500/15 text-cyan-400 border-0">{upcomingItems.length}</Badge>
                </div>
                <ScrollRow
                  items={upcomingItems.map(u => ({ id: u.content_id, title: u.title, poster_url: u.poster_url, _frozen: u.frozen, _remaining: u.remaining_seconds, _upcomingId: u.id, _contentType: u.content_type, content_type: u.content_type, type: u.content_type }))}
                  color="cyan"
                  canAdd={true}
                  onAdd={openAddUpcomingPicker}
                  onRemove={(id) => removeUpcoming(id)}
                  onItemClick={(item) => { if (onOpenContentDetail) { onOpenContentDetail(item); } }}
                  isUpcoming
                />
              </div>
            </div>
          )}

          {/* Add Content sub-view (for palette) */}
          {activeTab === 'contenuti' && showAddType && !showAddUpcoming && (
            <ContentPicker
              loading={contentLoading}
              items={showAddType === 'film' ? availableContent.films : showAddType === 'tv_series' ? availableContent.tv_series : availableContent.anime}
              type={showAddType}
              onBack={() => setShowAddType(null)}
              onSelect={(item) => addContent(item.id, showAddType)}
            />
          )}

          {/* Add Upcoming sub-view */}
          {activeTab === 'contenuti' && showAddUpcoming && !timerPopup && (
            <div data-testid="add-upcoming-subview">
              <button onClick={() => setShowAddUpcoming(false)} className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-white mb-2">
                <ChevronRight className="w-3 h-3 rotate-180" /> Torna
              </button>
              <p className="text-xs font-bold mb-2">Aggiungi ai Prossimamente</p>
              {upcomingLoading ? (
                <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 text-cyan-400 animate-spin" /></div>
              ) : (
                ['film', 'tv_series', 'anime'].map(type => {
                  const labels = { film: 'Film', tv_series: 'Serie TV', anime: 'Anime' };
                  const colors = { film: 'yellow', tv_series: 'blue', anime: 'orange' };
                  const items = type === 'film' ? availableUpcoming.films : type === 'tv_series' ? availableUpcoming.tv_series : availableUpcoming.anime;
                  if (!items || items.length === 0) return null;
                  return (
                    <div key={type} className="mb-3">
                      <p className={`text-[9px] font-bold text-${colors[type]}-400 mb-1 uppercase`}>{labels[type]}</p>
                      <div className="grid grid-cols-4 gap-1.5">
                        {items.slice(0, 12).map(item => (
                          <button key={item.id} className="group text-left" onClick={() => setTimerPopup({ content: item, contentType: type })} data-testid={`upcoming-pick-${item.id}`}>
                            <div className="aspect-[2/3] rounded-lg overflow-hidden border border-white/5 hover:border-cyan-500/40 transition-colors relative">
                              <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 flex items-center justify-center">
                                <Plus className="w-4 h-4 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                              {item.status && item.status !== 'completed' && item.status !== 'released' && (
                                <Badge className="absolute bottom-0.5 left-0.5 text-[5px] bg-orange-500/80 border-0">{item.status}</Badge>
                              )}
                            </div>
                            <p className="text-[6px] font-medium truncate mt-0.5">{item.title}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* Timer popup */}
          {activeTab === 'contenuti' && timerPopup && (
            <div data-testid="timer-popup">
              <button onClick={() => setTimerPopup(null)} className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-white mb-2">
                <ChevronRight className="w-3 h-3 rotate-180" /> Torna
              </button>
              <div className="text-center mb-3">
                <p className="text-xs font-bold mb-1">Quando va in programmazione?</p>
                <p className="text-[10px] text-gray-400 truncate">{timerPopup.content.title}</p>
                {timerPopup.contentType !== 'film' && (timerPopup.content.num_episodes || 0) === 0 && (
                  <div className="flex items-center justify-center gap-1 mt-1 text-[9px] text-amber-400">
                    <Snowflake className="w-3 h-3" />
                    <span>Senza episodi definiti, resterà congelato</span>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                {DELAY_OPTIONS.map(opt => (
                  <button
                    key={opt.hours}
                    onClick={() => handleAddUpcoming(opt.hours)}
                    disabled={addingUpcoming}
                    className="py-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-bold hover:bg-cyan-500/20 active:scale-95 transition-all disabled:opacity-40"
                    data-testid={`delay-${opt.hours}`}
                  >
                    {addingUpcoming ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* === PALINSESTO TAB === */}
          {activeTab === 'palinsesto' && (
            <div className="space-y-2" data-testid="tab-palinsesto-content">
              {allSeries.length === 0 ? (
                <div className="text-center py-8">
                  <Zap className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                  <p className="text-gray-500 text-xs">Nessuna serie/anime nel palinsesto</p>
                </div>
              ) : (
                allSeries.map(item => {
                  const bstate = item.broadcast_state || 'idle';
                  const isAnime = item.type === 'anime';
                  const totalEps = item.total_episodes || item.num_episodes || 0;
                  const airedEps = item.episodes_aired || 0;
                  const progress = totalEps > 0 ? (airedEps / totalEps) * 100 : 0;
                  const stateColors = { idle: 'bg-gray-500/20 text-gray-400', airing: 'bg-green-500/20 text-green-400', scheduled: 'bg-blue-500/20 text-blue-400', completed: 'bg-cyan-500/20 text-cyan-400', reruns: 'bg-amber-500/20 text-amber-400', retired: 'bg-red-500/20 text-red-400' };
                  const stateLabels = { idle: 'Non in onda', airing: 'In onda', scheduled: 'Programmata', completed: 'Completata', reruns: 'Repliche', retired: 'Ritirata' };
                  return (
                    <Card key={item.id} className="bg-[#111113] border-white/5 overflow-hidden" data-testid={`pali-card-${item.id}`}>
                      <CardContent className="p-0">
                        <div className="flex gap-2.5 p-2.5">
                          <div className="w-[45px] h-[67px] rounded-lg overflow-hidden flex-shrink-0">
                            <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 mb-1">
                              {isAnime ? <Sparkles className="w-3 h-3 text-orange-400" /> : <Tv className="w-3 h-3 text-blue-400" />}
                              <h3 className="text-[11px] font-bold truncate">{item.title}</h3>
                              <Badge className={`text-[7px] h-4 border-0 flex-shrink-0 ${stateColors[bstate]}`}>{stateLabels[bstate]}</Badge>
                            </div>
                            <div className="flex items-center gap-2 text-[9px] text-gray-500 mb-1.5">
                              <span>{totalEps} ep</span>
                              {bstate === 'airing' && <span className="text-green-400">Ep. {airedEps + 1}/{totalEps}</span>}
                              {item.broadcast_viewers > 0 && <span className="text-cyan-400">{item.broadcast_viewers.toLocaleString()} views</span>}
                            </div>
                            {bstate === 'airing' && (
                              <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden mb-1.5">
                                <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full" style={{ width: `${progress}%` }} />
                              </div>
                            )}
                            <div className="flex gap-1">
                              <Button size="sm" className="h-6 text-[9px] bg-yellow-500/15 text-yellow-400 hover:bg-yellow-500/25 px-2" onClick={() => { onClose(); onOpenPalinsesto?.(item); }} data-testid={`pali-manage-${item.id}`}>
                                <Settings className="w-2.5 h-2.5 mr-0.5" /> Gestisci
                              </Button>
                              {bstate === 'completed' && (
                                <Button size="sm" className="h-6 text-[9px] bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 px-2" onClick={() => startReruns(item.id)} disabled={actionLoading === `reruns-${item.id}`}>
                                  <RefreshCw className="w-2.5 h-2.5 mr-0.5" /> Repliche
                                </Button>
                              )}
                              {(bstate === 'completed' || bstate === 'reruns') && (
                                <Button size="sm" variant="outline" className="h-6 text-[9px] border-red-500/20 text-red-400 px-2" onClick={() => retireSeries(item.id)} disabled={actionLoading === `retire-${item.id}`}>
                                  <Ban className="w-2.5 h-2.5 mr-0.5" /> Ritira
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          )}

          {/* === PUBBLICITA === */}
          {activeTab === 'pubblicita' && (
            <div className="space-y-4" data-testid="tab-pubblicita-content">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400">Secondi di Pubblicità per Contenuto</span>
                  <span className="text-lg font-bold text-red-400">{settingsAd}s</span>
                </div>
                <input type="range" min="0" max="120" value={settingsAd} onChange={(e) => setSettingsAd(Number(e.target.value))} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500" data-testid="menu-ad-slider" />
                <div className="flex justify-between text-[9px] text-gray-600 mt-1"><span>0s</span><span>60s</span><span>120s</span></div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Card className={`${settingsAd > 60 ? 'bg-green-500/10 border-green-500/20' : 'bg-white/[0.03] border-white/5'}`}>
                  <CardContent className="p-3 text-center">
                    <DollarSign className="w-4 h-4 text-green-400 mx-auto mb-1" />
                    <p className="text-[9px] text-gray-500">Incasso</p>
                    <p className="text-sm font-bold text-green-400">{settingsAd > 60 ? 'ALTO' : settingsAd > 30 ? 'MEDIO' : 'BASSO'}</p>
                  </CardContent>
                </Card>
                <Card className={`${settingsAd < 30 ? 'bg-cyan-500/10 border-cyan-500/20' : 'bg-white/[0.03] border-white/5'}`}>
                  <CardContent className="p-3 text-center">
                    <Eye className="w-4 h-4 text-cyan-400 mx-auto mb-1" />
                    <p className="text-[9px] text-gray-500">Share</p>
                    <p className="text-sm font-bold text-cyan-400">{settingsAd < 30 ? 'ALTO' : settingsAd < 60 ? 'MEDIO' : 'BASSO'}</p>
                  </CardContent>
                </Card>
              </div>
              <Button className="w-full bg-red-500 hover:bg-red-600 font-bold" onClick={saveSettings} disabled={savingSettings || settingsAd === station.ad_seconds} data-testid="menu-save-ads">
                {savingSettings ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Check className="w-4 h-4 mr-1" />}
                Salva Impostazioni
              </Button>
            </div>
          )}

          {/* === GESTIONE === */}
          {activeTab === 'gestione' && (
            <div className="space-y-3" data-testid="tab-gestione-content">
              {/* Stile branding */}
              <Card className="bg-[#111113] border-white/5">
                <CardContent className="p-3">
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Stile Branding</p>
                  <p className="text-[10px] text-gray-600 mb-2">Definisce font, colore e glow del badge "In TV dal..." sui contenuti.</p>
                  {availableStyles.length === 0 ? (
                    <p className="text-[10px] text-gray-500 italic py-2">Caricamento stili...</p>
                  ) : (
                    <>
                      <div className="grid grid-cols-2 gap-1.5 mb-2">
                        {availableStyles.map(s => {
                          const isSel = selectedStyle === s.key;
                          return (
                            <button
                              key={s.key}
                              onClick={() => setSelectedStyle(s.key)}
                              data-testid={`gestione-style-${s.key}`}
                              className={`relative rounded-lg p-2 text-left border transition-all touch-manipulation ${isSel ? 'border-red-500 ring-2 ring-red-500/30' : 'border-white/10 hover:border-white/20'}`}
                              style={{ background: isSel ? `linear-gradient(135deg, ${s.color}22, transparent)` : 'rgba(255,255,255,0.02)' }}
                            >
                              <p className="text-[11px] font-bold leading-tight" style={{ color: s.color, fontFamily: s.font_family }}>{s.label}</p>
                              <p className="text-[8px] text-gray-500 leading-tight mt-0.5 line-clamp-1">{s.tagline}</p>
                              {isSel && <Check className="absolute top-1 right-1 w-3 h-3 text-red-400" />}
                            </button>
                          );
                        })}
                      </div>
                      <Button
                        size="sm"
                        className="w-full h-8 text-xs bg-red-500 hover:bg-red-600 font-bold"
                        onClick={saveStyle}
                        disabled={savingStyle || selectedStyle === (station.style || 'default')}
                        data-testid="save-style-btn"
                      >
                        {savingStyle ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <Check className="w-3.5 h-3.5 mr-1.5" />}
                        Applica Stile
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card className="bg-[#111113] border-white/5">
                <CardContent className="p-3">
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Gestione Emittente</p>
                  <div className="space-y-2">
                    <div className="bg-red-500/5 border border-red-500/15 rounded-lg p-3">
                      <p className="text-xs font-semibold text-red-400 mb-1">Azzera Palinsesto</p>
                      <p className="text-[10px] text-gray-500 mb-3">Rimuove tutti i contenuti dal palinsesto (film, serie, anime). Le statistiche verranno mantenute.</p>
                      <Button
                        size="sm"
                        className="w-full h-8 text-xs bg-red-500/15 text-red-400 hover:bg-red-500/25 border border-red-500/20"
                        onClick={async () => {
                          if (!await gameConfirm({
                            title: 'Azzerare il palinsesto?',
                            subtitle: 'Tutti i contenuti verranno rimossi dalla programmazione. Le statistiche saranno mantenute.',
                            confirmLabel: 'Azzera tutto',
                          })) return;
                          try {
                            await api.post('/tv-stations/clear-schedule', { station_id: station.id });
                            toast.success('Palinsesto azzerato!');
                            onRefresh?.();
                          } catch (err) {
                            toast.error(err.response?.data?.detail || 'Errore');
                          }
                        }}
                        data-testid="clear-schedule-btn"
                      >
                        <Trash2 className="w-3.5 h-3.5 mr-1.5" /> Azzera Palinsesto
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* === STATISTICHE === */}
          {activeTab === 'statistiche' && (
            <div className="space-y-3" data-testid="tab-statistiche-content">
              <div className="grid grid-cols-2 gap-2">
                <StatCard label="Share" value={`${shareData?.estimated_share || 0}%`} icon={<TrendingUp className="w-4 h-4" />} color="text-cyan-400" bgColor="bg-cyan-500/10" />
                <StatCard label="Ricavo/ora" value={`$${(shareData?.estimated_hourly_revenue || 0).toLocaleString()}`} icon={<DollarSign className="w-4 h-4" />} color="text-green-400" bgColor="bg-green-500/10" />
                <StatCard label="Viewers totali" value={(shareData?.total_viewers || 0).toLocaleString()} icon={<Users className="w-4 h-4" />} color="text-blue-400" bgColor="bg-blue-500/10" />
                <StatCard label="Qualità media" value={`${shareData?.avg_quality || 0}/100`} icon={<Star className="w-4 h-4" />} color="text-yellow-400" bgColor="bg-yellow-500/10" />
              </div>
              <Card className="bg-[#111113] border-white/5">
                <CardContent className="p-3 space-y-2">
                  {[
                    ['Livello infrastruttura', <span className="font-bold text-red-400">Lv.{infraLevel}</span>],
                    ['Contenuti nel palinsesto', <span className="font-bold">{shareData?.total_content || 0}/{capacity?.total || 7}</span>],
                    ['Nazione', <span className="font-bold">{station.nation}</span>],
                    ['Secondi pubblicità', <span className="font-bold">{station.ad_seconds}s</span>],
                    ['Ricavo giornaliero stimato', <span className="font-bold text-green-400">${(shareData?.estimated_daily_revenue || 0).toLocaleString()}</span>],
                    ['Revenue totale', <span className="font-bold text-green-400">${(station.total_revenue || 0).toLocaleString()}</span>],
                  ].map(([label, val], i) => (
                    <div key={i} className="flex items-center justify-between text-[10px]"><span className="text-gray-500">{label}</span>{val}</div>
                  ))}
                </CardContent>
              </Card>
              <div>
                <p className="text-[10px] text-gray-500 mb-2 uppercase tracking-wider">Contenuti per tipo</p>
                <div className="grid grid-cols-3 gap-2">
                  {[['Film', Film, 'yellow', contents.films?.length || 0], ['Serie TV', Tv, 'blue', contents.tv_series?.length || 0], ['Anime', Sparkles, 'orange', contents.anime?.length || 0]].map(([l, I, c, n]) => (
                    <div key={l} className={`bg-${c}-500/5 border border-${c}-500/15 rounded-lg p-2 text-center`}>
                      <I className={`w-4 h-4 text-${c}-400 mx-auto mb-1`} /><p className="text-sm font-bold">{n}</p><p className="text-[8px] text-gray-500">{l}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// === Sub-components ===

function ScrollRow({ items, color, canAdd, onAdd, onRemove, isUpcoming, onItemClick }) {
  const scrollRef = useRef(null);
  const [showArrow, setShowArrow] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const check = () => setShowArrow(el.scrollWidth > el.clientWidth && el.scrollLeft + el.clientWidth < el.scrollWidth - 10);
    check();
    el.addEventListener('scroll', check);
    return () => el.removeEventListener('scroll', check);
  }, [items]);

  return (
    <div className="relative">
      <div ref={scrollRef} className="flex gap-1.5 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
        {/* + card as first element */}
        {canAdd && (
          <button className={`flex-shrink-0 w-[52px] aspect-[2/3] rounded-lg border border-dashed border-${color}-500/30 flex items-center justify-center hover:border-${color}-500/60 hover:bg-${color}-500/5 transition-colors active:scale-95`} onClick={onAdd} data-testid={`add-card-${color}`}>
            <Plus className={`w-4 h-4 text-${color}-400`} />
          </button>
        )}
        {items.map(item => (
          <div key={item.id} className="flex-shrink-0 w-[52px] group relative">
            <div
              className={`aspect-[2/3] rounded-lg overflow-hidden relative ${onItemClick ? 'cursor-pointer' : ''}`}
              onClick={() => { if (onItemClick) onItemClick(item); }}
            >
              <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
              {isUpcoming && item._frozen && (
                <div className="absolute inset-0 bg-blue-900/40 flex items-center justify-center pointer-events-none">
                  <Snowflake className="w-4 h-4 text-blue-300" />
                </div>
              )}
              {isUpcoming && !item._frozen && item._remaining > 0 && (
                <div className="absolute bottom-0 inset-x-0 bg-black/80 px-0.5 py-0.5 text-center pointer-events-none">
                  <span className="text-[6px] text-cyan-400 font-bold">{formatCountdown(item._remaining)}</span>
                </div>
              )}
            </div>
            <p className="text-[6px] font-medium truncate mt-0.5">{item.title}</p>
            {/* Explicit delete button */}
            {onRemove && (
              <button
                className="mt-0.5 w-full flex items-center justify-center gap-0.5 text-[6px] text-red-400/70 hover:text-red-400 transition-colors"
                onClick={(e) => { e.stopPropagation(); onRemove(item.id); }}
                data-testid={`remove-item-${item.id}`}
              >
                <Trash2 className="w-2 h-2" /> Elimina
              </button>
            )}
          </div>
        ))}
        {items.length === 0 && !canAdd && (
          <p className="text-[9px] text-gray-600 py-3 pl-1">Vuoto</p>
        )}
      </div>
      {/* Arrow indicator for 20+ items */}
      {(showArrow || items.length >= 20) && (
        <div className={`absolute right-0 top-0 bottom-1 w-6 flex items-center justify-center bg-gradient-to-l from-[#0A0A0B] to-transparent pointer-events-none`}>
          <ChevronRight className={`w-4 h-4 text-${color}-400`} />
        </div>
      )}
    </div>
  );
}

function ContentPicker({ loading, items, type, onBack, onSelect }) {
  const labels = { film: 'Film', tv_series: 'Serie TV', anime: 'Anime' };
  return (
    <div data-testid="add-content-subview">
      <button onClick={onBack} className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-white mb-2">
        <ChevronRight className="w-3 h-3 rotate-180" /> Torna
      </button>
      <p className="text-xs font-bold mb-2">Aggiungi {labels[type]}</p>
      {loading ? (
        <div className="flex items-center justify-center py-8"><Loader2 className="w-5 h-5 text-red-400 animate-spin" /></div>
      ) : items.length === 0 ? (
        <p className="text-gray-500 text-[10px] text-center py-6">Nessun contenuto disponibile</p>
      ) : (
        <div className="grid grid-cols-4 gap-1.5">
          {items.map(item => (
            <button key={item.id} className="group text-left" onClick={() => onSelect(item)} data-testid={`add-item-${item.id}`}>
              <div className="aspect-[2/3] rounded-lg overflow-hidden border border-white/5 hover:border-red-500/40 transition-colors relative">
                <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 flex items-center justify-center">
                  <Plus className="w-5 h-5 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
              <p className="text-[7px] font-medium truncate mt-0.5">{item.title}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, icon, color, bgColor }) {
  return (
    <Card className={`${bgColor} border-white/5`}>
      <CardContent className="p-3 flex items-center gap-3">
        <div className={color}>{icon}</div>
        <div><p className="text-sm font-bold">{value}</p><p className="text-[9px] text-gray-500">{label}</p></div>
      </CardContent>
    </Card>
  );
}

function formatCountdown(seconds) {
  if (seconds <= 0) return 'ORA';
  const h = Math.floor(seconds / 3600);
  const d = Math.floor(h / 24);
  if (d > 0) return `${d}g ${h % 24}h`;
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}
