// CineWorld - TV Menu Modal (Hub Gestione Emittente)
// 4 sections: Contenuti, Palinsesto, Pubblicità, Statistiche TV

import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { Input } from './ui/input';
import { useConfirm } from './ConfirmDialog';
import {
  Tv, Sparkles, Film, Settings, Plus, X, Loader2, DollarSign, Eye,
  TrendingUp, Check, Trash2, BarChart3, Play, Clock, Users, Zap,
  RefreshCw, Ban, ChevronRight, Radio, Globe, Star, Calendar
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
  { id: 'statistiche', label: 'Statistiche', icon: BarChart3 },
];

export function TVMenuModal({ open, onClose, station, enrichedContents, capacity, shareData, infraLevel, onRefresh, onOpenPalinsesto }) {
  const { api } = useContext(AuthContext);
  const gameConfirm = useConfirm();
  const [activeTab, setActiveTab] = useState('contenuti');
  const [contentLoading, setContentLoading] = useState(false);
  const [availableContent, setAvailableContent] = useState({ films: [], tv_series: [], anime: [] });
  const [showAddType, setShowAddType] = useState(null);
  const [settingsAd, setSettingsAd] = useState(station?.ad_seconds || 30);
  const [savingSettings, setSavingSettings] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    if (open && station) setSettingsAd(station.ad_seconds || 30);
  }, [open, station]);

  if (!station) return null;

  const stationId = station.id;
  const contents = enrichedContents || { films: [], tv_series: [], anime: [] };
  const allSeries = [...(contents.tv_series || []), ...(contents.anime || [])];

  // Content management
  const openAddContent = async (type) => {
    setShowAddType(type);
    setContentLoading(true);
    try {
      const res = await api.get(`/tv-stations/available-content/${stationId}`);
      setAvailableContent(res.data);
    } catch { toast.error('Errore caricamento contenuti'); }
    setContentLoading(false);
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
    <Dialog open={open} onOpenChange={(o) => { if (!o) { onClose(); setShowAddType(null); } }}>
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

          {/* Tabs */}
          <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1" data-testid="tv-menu-tabs">
            {TABS.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setShowAddType(null); }}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-[10px] font-medium transition-all ${
                    activeTab === tab.id ? 'bg-red-500/15 text-red-400 border border-red-500/25' : 'text-gray-500 hover:text-gray-300'
                  }`}
                  data-testid={`tab-${tab.id}`}
                >
                  <Icon className="w-3 h-3" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab content */}
        <div className="overflow-y-auto px-4 pb-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>
          {/* === CONTENUTI === */}
          {activeTab === 'contenuti' && !showAddType && (
            <div className="space-y-3" data-testid="tab-contenuti-content">
              {['film', 'tv_series', 'anime'].map(type => {
                const labels = { film: 'Film', tv_series: 'Serie TV', anime: 'Anime' };
                const colors = { film: 'yellow', tv_series: 'blue', anime: 'orange' };
                const icons = { film: Film, tv_series: Tv, anime: Sparkles };
                const Icon = icons[type];
                const capKey = type === 'film' ? 'films' : type;
                const items = contents[capKey] || [];
                const maxItems = capacity?.[capKey] || 99;

                return (
                  <div key={type}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Icon className={`w-4 h-4 text-${colors[type]}-400`} />
                        <span className="text-xs font-bold">{labels[type]}</span>
                        <Badge className="text-[9px] bg-white/5 border-0">{items.length}/{maxItems}</Badge>
                      </div>
                      {items.length < maxItems && (
                        <Button size="sm" variant="ghost" className={`h-6 text-[10px] text-${colors[type]}-400`} onClick={() => openAddContent(type)} data-testid={`menu-add-${type}`}>
                          <Plus className="w-3 h-3 mr-0.5" /> Aggiungi
                        </Button>
                      )}
                    </div>
                    <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
                      {items.map(item => (
                        <div key={item.id} className="flex-shrink-0 w-[60px] group relative">
                          <div className="aspect-[2/3] rounded-lg overflow-hidden">
                            <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                            <button className="absolute top-0.5 right-0.5 p-0.5 bg-black/70 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => removeContent(item.id)}>
                              <Trash2 className="w-2.5 h-2.5 text-red-400" />
                            </button>
                          </div>
                          <p className="text-[7px] font-medium truncate mt-0.5">{item.title}</p>
                        </div>
                      ))}
                      {items.length === 0 && (
                        <button className="flex-shrink-0 w-[60px] aspect-[2/3] rounded-lg border border-dashed border-white/10 flex items-center justify-center hover:border-red-500/30 transition-colors" onClick={() => openAddContent(type)}>
                          <Plus className="w-4 h-4 text-gray-600" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Add Content sub-view */}
          {activeTab === 'contenuti' && showAddType && (
            <div data-testid="add-content-subview">
              <button onClick={() => setShowAddType(null)} className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-white mb-2">
                <ChevronRight className="w-3 h-3 rotate-180" /> Torna
              </button>
              <p className="text-xs font-bold mb-2">Aggiungi {showAddType === 'film' ? 'Film' : showAddType === 'tv_series' ? 'Serie TV' : 'Anime'}</p>
              {contentLoading ? (
                <div className="flex items-center justify-center py-8"><Loader2 className="w-5 h-5 text-red-400 animate-spin" /></div>
              ) : (() => {
                const items = showAddType === 'film' ? availableContent.films : showAddType === 'tv_series' ? availableContent.tv_series : availableContent.anime;
                return items.length === 0 ? (
                  <p className="text-gray-500 text-[10px] text-center py-6">Nessun contenuto disponibile</p>
                ) : (
                  <div className="grid grid-cols-4 gap-1.5">
                    {items.map(item => (
                      <button key={item.id} className="group text-left" onClick={() => addContent(item.id, showAddType)} data-testid={`add-item-${item.id}`}>
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
                );
              })()}
            </div>
          )}

          {/* === PALINSESTO === */}
          {activeTab === 'palinsesto' && (
            <div className="space-y-2" data-testid="tab-palinsesto-content">
              {allSeries.length === 0 ? (
                <div className="text-center py-8">
                  <Zap className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                  <p className="text-gray-500 text-xs">Nessuna serie/anime nel palinsesto</p>
                  <p className="text-gray-600 text-[10px] mt-1">Aggiungi contenuti nella sezione Contenuti</p>
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
                                <Button size="sm" className="h-6 text-[9px] bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 px-2" onClick={() => startReruns(item.id)} disabled={actionLoading === `reruns-${item.id}`} data-testid={`pali-reruns-${item.id}`}>
                                  <RefreshCw className="w-2.5 h-2.5 mr-0.5" /> Repliche
                                </Button>
                              )}
                              {(bstate === 'completed' || bstate === 'reruns') && (
                                <Button size="sm" variant="outline" className="h-6 text-[9px] border-red-500/20 text-red-400 px-2" onClick={() => retireSeries(item.id)} disabled={actionLoading === `retire-${item.id}`} data-testid={`pali-retire-${item.id}`}>
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
                <input
                  type="range" min="0" max="120" value={settingsAd}
                  onChange={(e) => setSettingsAd(Number(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                  data-testid="menu-ad-slider"
                />
                <div className="flex justify-between text-[9px] text-gray-600 mt-1">
                  <span>0s (no ads)</span><span>60s</span><span>120s (max)</span>
                </div>
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
              <Button
                className="w-full bg-red-500 hover:bg-red-600 font-bold"
                onClick={saveSettings}
                disabled={savingSettings || settingsAd === station.ad_seconds}
                data-testid="menu-save-ads"
              >
                {savingSettings ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Check className="w-4 h-4 mr-1" />}
                Salva Impostazioni
              </Button>
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
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-500">Livello infrastruttura</span>
                    <span className="font-bold text-red-400">Lv.{infraLevel}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-500">Contenuti nel palinsesto</span>
                    <span className="font-bold">{shareData?.total_content || 0}/{capacity?.total || 7}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-500">Nazione</span>
                    <span className="font-bold">{station.nation}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-500">Secondi pubblicità</span>
                    <span className="font-bold">{station.ad_seconds}s</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-500">Ricavo giornaliero stimato</span>
                    <span className="font-bold text-green-400">${(shareData?.estimated_daily_revenue || 0).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-500">Revenue totale</span>
                    <span className="font-bold text-green-400">${(station.total_revenue || 0).toLocaleString()}</span>
                  </div>
                </CardContent>
              </Card>
              {/* Content breakdown */}
              <div>
                <p className="text-[10px] text-gray-500 mb-2 uppercase tracking-wider">Contenuti per tipo</p>
                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-yellow-500/5 border border-yellow-500/15 rounded-lg p-2 text-center">
                    <Film className="w-4 h-4 text-yellow-400 mx-auto mb-1" />
                    <p className="text-sm font-bold">{contents.films?.length || 0}</p>
                    <p className="text-[8px] text-gray-500">Film</p>
                  </div>
                  <div className="bg-blue-500/5 border border-blue-500/15 rounded-lg p-2 text-center">
                    <Tv className="w-4 h-4 text-blue-400 mx-auto mb-1" />
                    <p className="text-sm font-bold">{contents.tv_series?.length || 0}</p>
                    <p className="text-[8px] text-gray-500">Serie TV</p>
                  </div>
                  <div className="bg-orange-500/5 border border-orange-500/15 rounded-lg p-2 text-center">
                    <Sparkles className="w-4 h-4 text-orange-400 mx-auto mb-1" />
                    <p className="text-sm font-bold">{contents.anime?.length || 0}</p>
                    <p className="text-[8px] text-gray-500">Anime</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function StatCard({ label, value, icon, color, bgColor }) {
  return (
    <Card className={`${bgColor} border-white/5`}>
      <CardContent className="p-3 flex items-center gap-3">
        <div className={color}>{icon}</div>
        <div>
          <p className="text-sm font-bold">{value}</p>
          <p className="text-[9px] text-gray-500">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}
