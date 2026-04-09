// CineWorld - TV Station Page (Netflix-style)
// Setup wizard, content management, Netflix dashboard, ad settings

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import {
  Radio, Tv, Sparkles, Film, Settings, Plus, X, ChevronRight, ChevronLeft,
  Loader2, DollarSign, Eye, TrendingUp, Globe, Check, Minus, Trash2, BarChart3,
  Play, Pause, RotateCcw, Clock, Users, Zap, RefreshCw, Ban
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const NATIONS = [
  'Italia', 'USA', 'UK', 'Francia', 'Germania', 'Spagna', 'Giappone', 'Corea del Sud',
  'Brasile', 'India', 'Canada', 'Australia', 'Messico', 'Argentina', 'Cina', 'Russia',
  'Svezia', 'Norvegia', 'Paesi Bassi', 'Turchia'
];

const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300';
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};

export default function TVStationPage() {
  const { stationId } = useParams();
  const [searchParams] = useSearchParams();
  const infraId = searchParams.get('setup');
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [station, setStation] = useState(null);
  const [enrichedContents, setEnrichedContents] = useState({ films: [], tv_series: [], anime: [] });
  const [shareData, setShareData] = useState(null);
  const [netflixSections, setNetflixSections] = useState({});
  const [isOwner, setIsOwner] = useState(false);
  const [infraLevel, setInfraLevel] = useState(1);
  const [capacity, setCapacity] = useState({ films: 3, tv_series: 2, anime: 2, total: 7 });

  // Setup wizard
  const [setupStep, setSetupStep] = useState(0);
  const [stationName, setStationName] = useState('');
  const [selectedNation, setSelectedNation] = useState('Italia');
  const [adSeconds, setAdSeconds] = useState(30);
  const [setupLoading, setSetupLoading] = useState(false);
  const [newStationId, setNewStationId] = useState(null);

  // Content management
  const [showAddContent, setShowAddContent] = useState(null); // 'film' | 'tv_series' | 'anime'
  const [availableContent, setAvailableContent] = useState({ films: [], tv_series: [], anime: [] });
  const [contentLoading, setContentLoading] = useState(false);
  const [scheduledItems, setScheduledItems] = useState([]);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [schedulableContent, setSchedulableContent] = useState({ films: [], tv_series: [], anime: [] });
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [selectedTVContent, setSelectedTVContent] = useState(null);

  // Broadcast management
  const [showBroadcastDialog, setShowBroadcastDialog] = useState(null); // content_id
  const [broadcastDetail, setBroadcastDetail] = useState(null);
  const [broadcastLoading, setBroadcastLoading] = useState(false);
  const [showStartBroadcast, setShowStartBroadcast] = useState(null); // content_id
  const [broadcastInterval, setBroadcastInterval] = useState(1);
  const [startingBroadcast, setStartingBroadcast] = useState(false);

  // Settings popup
  const [showSettings, setShowSettings] = useState(false);
  const [settingsAd, setSettingsAd] = useState(30);
  const [savingSettings, setSavingSettings] = useState(false);

  const loadStation = useCallback(async (id) => {
    try {
      const [stRes, schRes] = await Promise.all([
        api.get(`/tv-stations/${id}`),
        api.get(`/tv-stations/${id}/scheduled`).catch(() => ({ data: { items: [] } }))
      ]);
      setStation(stRes.data.station);
      setEnrichedContents(stRes.data.enriched_contents);
      setShareData(stRes.data.share_data);
      setNetflixSections(stRes.data.netflix_sections);
      setIsOwner(stRes.data.is_owner);
      setSettingsAd(stRes.data.station?.ad_seconds || 30);
      setInfraLevel(stRes.data.infra_level || 1);
      setCapacity(stRes.data.capacity || { films: 3, tv_series: 2, anime: 2, total: 7 });
      setScheduledItems(schRes.data.items || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [api]);

  useEffect(() => {
    if (infraId) {
      setSetupStep(1);
      setLoading(false);
    } else if (stationId) {
      loadStation(stationId);
    } else {
      setLoading(false);
    }
  }, [stationId, infraId, loadStation]);

  // === SETUP ===
  const submitStep1 = async () => {
    if (!stationName.trim()) return toast.error('Inserisci un nome');
    setSetupLoading(true);
    try {
      const res = await api.post('/tv-stations/setup-step1', {
        infra_id: infraId,
        station_name: stationName,
        nation: selectedNation,
      });
      setNewStationId(res.data.station.id);
      setSetupStep(2);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setSetupLoading(false);
  };

  const submitStep2 = async () => {
    setSetupLoading(true);
    try {
      await api.post('/tv-stations/setup-step2', {
        station_id: newStationId,
        ad_seconds: adSeconds,
      });
      toast.success('Emittente TV configurata!');
      navigate(`/tv-station/${newStationId}`, { replace: true });
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setSetupLoading(false);
  };

  // === CONTENT MANAGEMENT ===
  const openAddContent = async (type) => {
    const sid = stationId || newStationId;
    if (!sid) return;
    setShowAddContent(type);
    setContentLoading(true);
    try {
      const res = await api.get(`/tv-stations/available-content/${sid}`);
      setAvailableContent(res.data);
    } catch (e) { toast.error('Errore caricamento contenuti'); }
    setContentLoading(false);
  };

  const openScheduleDialog = async () => {
    const sid = stationId || newStationId;
    if (!sid) return;
    setShowScheduleDialog(true);
    setScheduleLoading(true);
    try {
      const res = await api.get(`/tv-stations/schedulable-content/${sid}`);
      setSchedulableContent(res.data);
    } catch (e) { toast.error('Errore caricamento'); }
    setScheduleLoading(false);
  };

  const toggleSchedule = async (contentId, contentType) => {
    const sid = stationId || newStationId;
    try {
      const res = await api.post('/tv-stations/toggle-schedule-tv', {
        content_id: contentId, content_type: contentType, station_id: sid
      });
      if (res.data.scheduled_for_tv) {
        toast.success('Programmato per TV!');
      } else {
        toast.info('Rimosso dalla programmazione');
      }
      // Update local state
      setSchedulableContent(prev => {
        const key = contentType === 'film' ? 'films' : contentType;
        return { ...prev, [key]: prev[key].map(i => i.id === contentId ? { ...i, scheduled_for_tv: res.data.scheduled_for_tv } : i) };
      });
      loadStation(sid);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const addContent = async (contentId, contentType) => {
    const sid = stationId || newStationId;
    try {
      const res = await api.post('/tv-stations/add-content', {
        station_id: sid,
        content_id: contentId,
        content_type: contentType,
      });
      toast.success(res.data.message);
      if (sid === stationId) loadStation(sid);
      openAddContent(contentType);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const removeContent = async (contentId) => {
    const sid = stationId || newStationId;
    try {
      await api.post('/tv-stations/remove-content', { station_id: sid, content_id: contentId });
      toast.success('Contenuto rimosso');
      if (sid === stationId) loadStation(sid);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const saveSettings = async () => {
    setSavingSettings(true);
    try {
      await api.post('/tv-stations/update-ads', { station_id: stationId, ad_seconds: settingsAd });
      toast.success('Impostazioni salvate');
      setShowSettings(false);
      loadStation(stationId);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setSavingSettings(false);
  };

  // === BROADCAST FUNCTIONS ===
  const openBroadcastDetail = async (contentId) => {
    const sid = stationId || newStationId;
    if (!sid) return;
    setShowBroadcastDialog(contentId);
    setBroadcastLoading(true);
    try {
      const res = await api.get(`/tv-stations/${sid}/broadcast/${contentId}`);
      setBroadcastDetail(res.data);
    } catch (e) { toast.error('Errore caricamento trasmissione'); }
    setBroadcastLoading(false);
  };

  const startBroadcast = async (contentId) => {
    const sid = stationId || newStationId;
    setStartingBroadcast(true);
    try {
      const res = await api.post('/tv-stations/start-broadcast', {
        station_id: sid, content_id: contentId, air_interval_days: broadcastInterval
      });
      toast.success(res.data.message);
      setShowStartBroadcast(null);
      loadStation(sid);
      if (showBroadcastDialog === contentId) openBroadcastDetail(contentId);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setStartingBroadcast(false);
  };

  const retireSeries = async (contentId) => {
    const sid = stationId || newStationId;
    try {
      const res = await api.post('/tv-stations/retire-series', { station_id: sid, content_id: contentId });
      toast.success(res.data.message);
      loadStation(sid);
      if (showBroadcastDialog === contentId) openBroadcastDetail(contentId);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const startReruns = async (contentId) => {
    const sid = stationId || newStationId;
    try {
      const res = await api.post('/tv-stations/start-reruns', { station_id: sid, content_id: contentId });
      toast.success(res.data.message);
      loadStation(sid);
      if (showBroadcastDialog === contentId) openBroadcastDetail(contentId);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  // === SETUP WIZARD ===
  if (setupStep === 1) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
        <div className="max-w-md mx-auto px-4 pt-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="text-center mb-6">
              <div className="inline-block p-3 bg-red-500/20 rounded-2xl border border-red-500/30 mb-3">
                <Radio className="w-8 h-8 text-red-400" />
              </div>
              <h1 className="font-['Bebas_Neue'] text-3xl text-red-400" data-testid="setup-step1-title">Crea La Tua Emittente</h1>
              <p className="text-sm text-gray-500 mt-1">Step 1: Nome e Nazione</p>
            </div>
            <Card className="bg-[#111113] border-red-500/20 mb-4">
              <CardContent className="p-4 space-y-4">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Nome dell'Emittente (permanente)</label>
                  <Input
                    value={stationName}
                    onChange={(e) => setStationName(e.target.value)}
                    placeholder="es. CineWorld TV, NeoFlix, TeleStudio..."
                    maxLength={30}
                    className="bg-black/40 border-white/10"
                    data-testid="station-name-input"
                  />
                  <p className="text-[10px] text-gray-600 mt-1">{stationName.length}/30 caratteri - Non potrai cambiarlo!</p>
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-2 block">Nazione</label>
                  <div className="grid grid-cols-3 gap-1.5 max-h-48 overflow-y-auto">
                    {NATIONS.map(n => (
                      <button
                        key={n}
                        onClick={() => setSelectedNation(n)}
                        className={`text-xs px-2 py-1.5 rounded-lg border transition-all ${
                          selectedNation === n
                            ? 'bg-red-500/20 border-red-500/50 text-red-400'
                            : 'bg-black/20 border-white/5 text-gray-400 hover:border-white/15'
                        }`}
                        data-testid={`nation-${n}`}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
            <Button
              className="w-full h-12 bg-red-500 hover:bg-red-600 font-['Bebas_Neue'] text-lg"
              onClick={submitStep1}
              disabled={setupLoading || !stationName.trim()}
              data-testid="step1-submit"
            >
              {setupLoading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : null}
              PROSEGUI <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          </motion.div>
        </div>
      </div>
    );
  }

  if (setupStep === 2) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
        <div className="max-w-md mx-auto px-4 pt-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="text-center mb-6">
              <div className="inline-block p-3 bg-red-500/20 rounded-2xl border border-red-500/30 mb-3">
                <Radio className="w-8 h-8 text-red-400" />
              </div>
              <h1 className="font-['Bebas_Neue'] text-3xl text-red-400" data-testid="setup-step2-title">{stationName}</h1>
              <p className="text-sm text-gray-500 mt-1">Step 2: Pubblicità e Contenuti</p>
            </div>

            {/* Ad Slider */}
            <Card className="bg-[#111113] border-red-500/20 mb-4">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400">Secondi di Pubblicità per Contenuto</span>
                  <span className="text-lg font-bold text-red-400">{adSeconds}s</span>
                </div>
                <input
                  type="range" min="0" max="120" value={adSeconds} onChange={(e) => setAdSeconds(Number(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                  data-testid="ad-slider"
                />
                <div className="flex justify-between text-[9px] text-gray-600 mt-1">
                  <span>0s (no ads)</span>
                  <span>60s</span>
                  <span>120s (max)</span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <div className={`rounded-lg p-2 text-center ${adSeconds > 60 ? 'bg-green-500/10 border border-green-500/20' : 'bg-white/[0.03]'}`}>
                    <DollarSign className="w-3 h-3 text-green-400 mx-auto mb-0.5" />
                    <p className="text-[10px] text-gray-400">Incasso</p>
                    <p className="text-xs font-bold text-green-400">{adSeconds > 60 ? 'ALTO' : adSeconds > 30 ? 'MEDIO' : 'BASSO'}</p>
                  </div>
                  <div className={`rounded-lg p-2 text-center ${adSeconds < 30 ? 'bg-cyan-500/10 border border-cyan-500/20' : 'bg-white/[0.03]'}`}>
                    <Eye className="w-3 h-3 text-cyan-400 mx-auto mb-0.5" />
                    <p className="text-[10px] text-gray-400">Share</p>
                    <p className="text-xs font-bold text-cyan-400">{adSeconds < 30 ? 'ALTO' : adSeconds < 60 ? 'MEDIO' : 'BASSO'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Content Rows - Step 2 allows adding content */}
            <h3 className="text-sm text-gray-400 font-semibold mb-2">Aggiungi Contenuti (opzionale, puoi farlo dopo)</h3>
            {['film', 'tv_series', 'anime'].map((type) => {
              const labels = { film: 'Film', tv_series: 'Serie TV', anime: 'Anime' };
              const colors = { film: 'yellow', tv_series: 'blue', anime: 'orange' };
              const icons = { film: Film, tv_series: Tv, anime: Sparkles };
              const Icon = icons[type];
              return (
                <Card key={type} className="bg-[#111113] border-white/5 mb-2">
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Icon className={`w-4 h-4 text-${colors[type]}-400`} />
                        <span className="text-xs font-semibold">{labels[type]}</span>
                      </div>
                      <Button size="sm" variant="outline" className={`h-7 text-xs border-${colors[type]}-500/30 text-${colors[type]}-400`} onClick={() => openAddContent(type)} data-testid={`add-${type}-btn`}>
                        <Plus className="w-3 h-3 mr-1" /> Aggiungi
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}

            <Button
              className="w-full h-12 bg-red-500 hover:bg-red-600 font-['Bebas_Neue'] text-lg mt-4"
              onClick={submitStep2}
              disabled={setupLoading}
              data-testid="step2-submit"
            >
              {setupLoading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : null}
              AVVIA L'EMITTENTE <Radio className="w-5 h-5 ml-2" />
            </Button>
          </motion.div>
        </div>

        <ContentAddDialog
          showAddContent={showAddContent}
          setShowAddContent={setShowAddContent}
          availableContent={availableContent}
          contentLoading={contentLoading}
          addContent={addContent}
          posterSrc={posterSrc}
        />
      </div>
    );
  }

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center pt-16">
      <Loader2 className="w-8 h-8 text-red-400 animate-spin" />
    </div>
  );

  if (!station) return (
    <div className="min-h-screen bg-[#0A0A0B] text-white flex items-center justify-center pt-16">
      <p className="text-gray-500">Stazione non trovata</p>
    </div>
  );

  // === NETFLIX DASHBOARD ===
  const allContentsEmpty = !enrichedContents.films.length && !enrichedContents.tv_series.length && !enrichedContents.anime.length;

  const NetflixRow = ({ title, items, color = 'white' }) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="mb-5">
        <h3 className={`text-sm font-bold mb-2 px-1 text-${color}`}>{title}</h3>
        <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
          {items.map((item, i) => (
            <div key={item.id || i} className="flex-shrink-0 w-[80px] group relative cursor-pointer" data-testid={`netflix-item-${item.id}`} onClick={() => setSelectedTVContent(item)}>
              <div className="aspect-[2/3] rounded-lg overflow-hidden relative">
                <img
                  src={posterSrc(item.poster_url)}
                  alt={item.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  loading="lazy"
                  onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300'; }}
                />
                {isOwner && (
                  <button
                    className="absolute top-1 right-1 p-1 bg-black/70 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => { e.stopPropagation(); removeContent(item.id); }}
                    data-testid={`remove-content-${item.id}`}
                  >
                    <X className="w-3 h-3 text-red-400" />
                  </button>
                )}
              </div>
              <p className="text-[8px] font-medium truncate mt-1 px-0.5">{item.title}</p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const ContentManagementRow = ({ type, label, icon: Icon, color, items }) => {
    const capKey = type === 'film' ? 'films' : type;
    const maxItems = capacity[capKey] || 99;
    return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2 px-1">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 text-${color}-400`} />
          <span className="text-sm font-bold">{label}</span>
          <Badge className="text-[9px] bg-white/5">{items.length}/{maxItems}</Badge>
        </div>
        {isOwner && items.length < maxItems && (
          <Button size="sm" variant="ghost" className={`h-6 text-[10px] text-${color}-400`} onClick={() => openAddContent(type)} data-testid={`manage-add-${type}`}>
            <Plus className="w-3 h-3 mr-0.5" /> Aggiungi
          </Button>
        )}
        {isOwner && items.length >= maxItems && (
          <Badge className="text-[9px] bg-red-500/15 text-red-400">Pieno</Badge>
        )}
      </div>
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
        {items.map((item) => (
          <div key={item.id} className="flex-shrink-0 w-[70px] group relative">
            <div className="aspect-[2/3] rounded-lg overflow-hidden">
              <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
              {isOwner && (
                <button className="absolute top-0.5 right-0.5 p-0.5 bg-black/70 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => removeContent(item.id)}>
                  <Trash2 className="w-2.5 h-2.5 text-red-400" />
                </button>
              )}
            </div>
            <p className="text-[7px] font-medium truncate mt-0.5">{item.title}</p>
          </div>
        ))}
        {isOwner && items.length === 0 && (
          <button className="flex-shrink-0 w-[70px] aspect-[2/3] rounded-lg border border-dashed border-white/10 flex items-center justify-center hover:border-red-500/30 transition-colors" onClick={() => openAddContent(type)}>
            <Plus className="w-5 h-5 text-gray-600" />
          </button>
        )}
      </div>
    </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-14">
      {/* Netflix Header */}
      <div className="bg-gradient-to-b from-red-900/30 to-[#0A0A0B] px-3 pt-3 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-white">
              <ChevronLeft className="w-5 h-5" />
            </button>
            <Radio className="w-5 h-5 text-red-500" />
            <div>
              <h1 className="font-['Bebas_Neue'] text-xl text-red-500 leading-none" data-testid="station-name">{station.station_name}</h1>
              <div className="flex items-center gap-1.5">
                <Globe className="w-2.5 h-2.5 text-gray-500" />
                <span className="text-[9px] text-gray-500">{station.nation}</span>
                <span className="text-[9px] text-gray-600">|</span>
                <span className="text-[9px] text-gray-500">{station.owner_nickname}</span>
              </div>
            </div>
          </div>
          {isOwner && (
            <Button size="sm" variant="outline" className="h-7 text-[10px] border-white/10" onClick={() => setShowSettings(true)} data-testid="tv-settings-btn">
              <Settings className="w-3 h-3 mr-1" /> Menu
            </Button>
          )}
        </div>

        {/* Stats Bar */}
        {shareData && (
          <div className="grid grid-cols-5 gap-2 mt-3" data-testid="station-stats">
            <div className="bg-black/30 rounded-lg p-2 text-center">
              <p className="text-sm font-bold text-red-400">Lv.{infraLevel}</p>
              <p className="text-[8px] text-gray-500">Livello</p>
            </div>
            <div className="bg-black/30 rounded-lg p-2 text-center">
              <p className="text-sm font-bold text-cyan-400">{shareData.estimated_share}%</p>
              <p className="text-[8px] text-gray-500">Share</p>
            </div>
            <div className="bg-black/30 rounded-lg p-2 text-center">
              <p className="text-sm font-bold text-green-400">${shareData.estimated_hourly_revenue?.toLocaleString()}</p>
              <p className="text-[8px] text-gray-500">$/ora</p>
            </div>
            <div className="bg-black/30 rounded-lg p-2 text-center">
              <p className="text-sm font-bold text-blue-400">{shareData.total_viewers?.toLocaleString()}</p>
              <p className="text-[8px] text-gray-500">Viewers</p>
            </div>
            <div className="bg-black/30 rounded-lg p-2 text-center">
              <p className="text-sm font-bold text-yellow-400">{shareData.total_content}/{capacity.total}</p>
              <p className="text-[8px] text-gray-500">Palinsesto</p>
            </div>
          </div>
        )}
      </div>

      <div className="px-3">
        {/* Netflix Sections */}
        {!allContentsEmpty ? (
          <>
            {/* PROSSIMAMENTE section */}
            {scheduledItems.length > 0 && (
              <div className="mb-5">
                <h3 className="text-sm font-bold mb-2 px-1 text-cyan-400">Prossimamente</h3>
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
                  {scheduledItems.map((item) => (
                    <div key={item.id} className="flex-shrink-0 w-[80px] group relative cursor-pointer" data-testid={`scheduled-item-${item.id}`} onClick={() => setSelectedTVContent(item)}>
                      <div className="aspect-[2/3] rounded-lg overflow-hidden relative ring-1 ring-cyan-500/30">
                        <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 p-1">
                          <Badge className="text-[6px] h-3 bg-cyan-500/20 text-cyan-400 border-0">
                            {item.status === 'in_theaters' ? 'Al cinema' : item.status === 'production' ? 'In produzione' : item.status}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-[8px] font-medium truncate mt-1">{item.title}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <NetflixRow title="Consigliati" items={netflixSections.consigliati} color="white" />
            <NetflixRow title="Del Momento" items={netflixSections.del_momento} color="red-400" />
            <NetflixRow title="I Piu Visti" items={netflixSections.piu_visti} color="yellow-400" />
          </>
        ) : (
          <div className="text-center py-8">
            <Radio className="w-10 h-10 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Nessun contenuto in programmazione</p>
            {isOwner && <p className="text-gray-600 text-xs mt-1">Aggiungi film, serie TV o anime qui sotto</p>}
            {/* Show Prossimamente even when empty main content */}
            {isOwner && scheduledItems.length > 0 && (
              <div className="mt-4 text-left">
                <h3 className="text-sm font-bold mb-2 px-1 text-cyan-400">Prossimamente</h3>
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
                  {scheduledItems.map((item) => (
                    <div key={item.id} className="flex-shrink-0 w-[80px] cursor-pointer" onClick={() => setSelectedTVContent(item)}>
                      <div className="aspect-[2/3] rounded-lg overflow-hidden ring-1 ring-cyan-500/30">
                        <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                      </div>
                      <p className="text-[8px] font-medium truncate mt-1">{item.title}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Content Management (owner only) */}
        {isOwner && (
          <div className="mt-4 border-t border-white/5 pt-4">
            <h2 className="font-['Bebas_Neue'] text-lg text-red-400 mb-3">Gestione Contenuti</h2>
            <ContentManagementRow type="film" label="Film" icon={Film} color="yellow" items={enrichedContents.films} />
            <ContentManagementRow type="tv_series" label="Serie TV" icon={Tv} color="blue" items={enrichedContents.tv_series} />
            <ContentManagementRow type="anime" label="Anime" icon={Sparkles} color="orange" items={enrichedContents.anime} />
          </div>
        )}

        {/* === BROADCAST / PALINSESTO SECTION === */}
        {isOwner && (enrichedContents.tv_series.length > 0 || enrichedContents.anime.length > 0) && (
          <div className="mt-4 border-t border-white/5 pt-4" data-testid="broadcast-section">
            <h2 className="font-['Bebas_Neue'] text-lg text-red-400 mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4" /> Palinsesto Trasmissione
            </h2>
            {[...enrichedContents.tv_series, ...enrichedContents.anime].map((item) => {
              const bstate = item.broadcast_state || 'idle';
              const curEp = item.current_episode || 0;
              const totalEps = item.total_episodes || item.num_episodes || 0;
              const airsIn = item.next_air_at ? Math.max(0, Math.round((new Date(item.next_air_at) - new Date()) / 3600000)) : null;
              const progress = totalEps > 0 ? ((item.episodes_aired || 0) / totalEps) * 100 : 0;
              const isAnime = item.type === 'anime';

              const stateColors = {
                idle: 'bg-gray-500/20 text-gray-400',
                airing: 'bg-green-500/20 text-green-400',
                completed: 'bg-blue-500/20 text-blue-400',
                reruns: 'bg-amber-500/20 text-amber-400',
                retired: 'bg-red-500/20 text-red-400',
              };
              const stateLabels = {
                idle: 'Non in onda',
                airing: 'In onda',
                completed: 'Completata',
                reruns: 'Repliche',
                retired: 'Ritirata',
              };

              return (
                <Card key={item.id} className="bg-[#111113] border-white/5 mb-3 overflow-hidden" data-testid={`broadcast-card-${item.id}`}>
                  <CardContent className="p-0">
                    <div className="flex gap-3 p-3">
                      <div className="w-[50px] h-[75px] rounded-lg overflow-hidden flex-shrink-0">
                        <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-xs font-bold truncate">{item.title}</h3>
                          <Badge className={`text-[7px] h-4 border-0 flex-shrink-0 ${stateColors[bstate]}`}>
                            {stateLabels[bstate]}
                          </Badge>
                          {item.rerun_count > 0 && (
                            <Badge className="text-[7px] h-4 border-0 bg-amber-500/10 text-amber-400">
                              Rep.{item.rerun_count}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-[9px] text-gray-500 mb-1.5">
                          {isAnime ? <Sparkles className="w-2.5 h-2.5 text-orange-400" /> : <Tv className="w-2.5 h-2.5 text-blue-400" />}
                          <span>{totalEps} episodi</span>
                          {bstate === 'airing' && (
                            <>
                              <span className="text-gray-700">|</span>
                              <span className="text-green-400">Ep. {curEp + 1}/{totalEps}</span>
                              {airsIn !== null && (
                                <>
                                  <Clock className="w-2.5 h-2.5 text-gray-500" />
                                  <span>{airsIn <= 0 ? 'Ora!' : airsIn < 24 ? `${airsIn}h` : `${Math.round(airsIn / 24)}g`}</span>
                                </>
                              )}
                            </>
                          )}
                          {bstate === 'completed' && (
                            <>
                              <span className="text-gray-700">|</span>
                              <Users className="w-2.5 h-2.5" />
                              <span>{(item.broadcast_viewers || 0).toLocaleString()}</span>
                              <DollarSign className="w-2.5 h-2.5 text-green-400" />
                              <span className="text-green-400">${(item.broadcast_revenue || 0).toLocaleString()}</span>
                            </>
                          )}
                        </div>

                        {/* Progress bar */}
                        {bstate === 'airing' && (
                          <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all" style={{ width: `${progress}%` }} />
                          </div>
                        )}
                        {bstate === 'completed' && (
                          <div className="w-full h-1.5 bg-blue-500/30 rounded-full" />
                        )}

                        {/* Action buttons */}
                        <div className="flex gap-1.5 mt-2">
                          {bstate === 'idle' && (
                            <Button size="sm" className="h-6 text-[9px] bg-green-500 hover:bg-green-600 px-2" onClick={() => { setShowStartBroadcast(item.id); setBroadcastInterval(1); }} data-testid={`start-broadcast-${item.id}`}>
                              <Play className="w-2.5 h-2.5 mr-0.5" /> Avvia Trasmissione
                            </Button>
                          )}
                          {bstate === 'airing' && (
                            <Button size="sm" variant="outline" className="h-6 text-[9px] border-green-500/30 text-green-400 px-2" onClick={() => openBroadcastDetail(item.id)} data-testid={`view-broadcast-${item.id}`}>
                              <Eye className="w-2.5 h-2.5 mr-0.5" /> Dettagli
                            </Button>
                          )}
                          {bstate === 'completed' && (
                            <>
                              <Button size="sm" className="h-6 text-[9px] bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 px-2" onClick={() => startReruns(item.id)} data-testid={`reruns-${item.id}`}>
                                <RefreshCw className="w-2.5 h-2.5 mr-0.5" /> Repliche
                              </Button>
                              <Button size="sm" variant="outline" className="h-6 text-[9px] border-red-500/30 text-red-400 px-2" onClick={() => retireSeries(item.id)} data-testid={`retire-${item.id}`}>
                                <Ban className="w-2.5 h-2.5 mr-0.5" /> Ritira
                              </Button>
                              <Button size="sm" variant="outline" className="h-6 text-[9px] border-blue-500/30 text-blue-400 px-2" onClick={() => openBroadcastDetail(item.id)} data-testid={`detail-completed-${item.id}`}>
                                <BarChart3 className="w-2.5 h-2.5 mr-0.5" /> Stats
                              </Button>
                            </>
                          )}
                          {bstate === 'retired' && (
                            <Badge className="text-[8px] bg-red-500/10 text-red-400 border-0">Rimossa dal palinsesto</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Content Dialog */}
      <ContentAddDialog
        showAddContent={showAddContent}
        setShowAddContent={setShowAddContent}
        availableContent={availableContent}
        contentLoading={contentLoading}
        addContent={addContent}
        posterSrc={posterSrc}
      />

      {/* Schedule for TV Dialog */}
      <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-sm max-h-[80vh] overflow-y-auto p-0" data-testid="schedule-dialog">
          <DialogHeader className="p-4 pb-2">
            <DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2 text-cyan-400">
              <TrendingUp className="w-5 h-5" /> Programma per TV
            </DialogTitle>
          </DialogHeader>
          <div className="p-4 pt-0 space-y-3">
            <p className="text-[10px] text-gray-500">Tocca una locandina per programmare/deprogrammare.</p>
            {scheduleLoading ? (
              <div className="flex items-center justify-center py-8"><Loader2 className="w-6 h-6 text-cyan-400 animate-spin" /></div>
            ) : (
              <>
                {schedulableContent.films.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-yellow-400 mb-2 flex items-center gap-1"><Film className="w-3 h-3" /> Film al Cinema</h4>
                    <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
                      {schedulableContent.films.map(f => (
                        <button key={f.id} onClick={() => toggleSchedule(f.id, 'film')} className="flex-shrink-0 w-[70px] text-center" data-testid={`schedule-film-${f.id}`}>
                          <div className={`aspect-[2/3] rounded-lg overflow-hidden relative transition-all ${f.scheduled_for_tv ? 'ring-2 ring-cyan-400' : 'ring-1 ring-white/10 hover:ring-white/25'}`}>
                            <img src={posterSrc(f.poster_url)} alt="" className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                            <div className={`absolute top-1 right-1 w-5 h-5 rounded-full flex items-center justify-center ${f.scheduled_for_tv ? 'bg-cyan-500' : 'bg-black/60'}`}>
                              {f.scheduled_for_tv ? <Check className="w-3 h-3 text-white" /> : <Plus className="w-3 h-3 text-gray-400" />}
                            </div>
                          </div>
                          <p className="text-[8px] font-medium truncate mt-1 px-0.5">{f.title}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {schedulableContent.tv_series.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-blue-400 mb-2 flex items-center gap-1"><Tv className="w-3 h-3" /> Serie TV in Produzione</h4>
                    <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
                      {schedulableContent.tv_series.map(s => (
                        <button key={s.id} onClick={() => toggleSchedule(s.id, 'tv_series')} className="flex-shrink-0 w-[70px] text-center" data-testid={`schedule-series-${s.id}`}>
                          <div className={`aspect-[2/3] rounded-lg overflow-hidden relative transition-all ${s.scheduled_for_tv ? 'ring-2 ring-cyan-400' : 'ring-1 ring-white/10 hover:ring-white/25'}`}>
                            <img src={posterSrc(s.poster_url)} alt="" className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                            <div className={`absolute top-1 right-1 w-5 h-5 rounded-full flex items-center justify-center ${s.scheduled_for_tv ? 'bg-cyan-500' : 'bg-black/60'}`}>
                              {s.scheduled_for_tv ? <Check className="w-3 h-3 text-white" /> : <Plus className="w-3 h-3 text-gray-400" />}
                            </div>
                          </div>
                          <p className="text-[8px] font-medium truncate mt-1 px-0.5">{s.title}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {schedulableContent.anime.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-orange-400 mb-2 flex items-center gap-1"><Sparkles className="w-3 h-3" /> Anime in Produzione</h4>
                    <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
                      {schedulableContent.anime.map(a => (
                        <button key={a.id} onClick={() => toggleSchedule(a.id, 'anime')} className="flex-shrink-0 w-[70px] text-center" data-testid={`schedule-anime-${a.id}`}>
                          <div className={`aspect-[2/3] rounded-lg overflow-hidden relative transition-all ${a.scheduled_for_tv ? 'ring-2 ring-cyan-400' : 'ring-1 ring-white/10 hover:ring-white/25'}`}>
                            <img src={posterSrc(a.poster_url)} alt="" className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                            <div className={`absolute top-1 right-1 w-5 h-5 rounded-full flex items-center justify-center ${a.scheduled_for_tv ? 'bg-cyan-500' : 'bg-black/60'}`}>
                              {a.scheduled_for_tv ? <Check className="w-3 h-3 text-white" /> : <Plus className="w-3 h-3 text-gray-400" />}
                            </div>
                          </div>
                          <p className="text-[8px] font-medium truncate mt-1 px-0.5">{a.title}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {!schedulableContent.films.length && !schedulableContent.tv_series.length && !schedulableContent.anime.length && (
                  <div className="text-center py-6">
                    <p className="text-gray-500 text-xs">Nessun contenuto programmabile</p>
                    <p className="text-gray-600 text-[10px] mt-1">I film al cinema e le serie in produzione appariranno qui</p>
                  </div>
                )}
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-sm p-0" data-testid="settings-dialog">
          <DialogHeader className="p-4 pb-2">
            <DialogTitle className="font-['Bebas_Neue'] text-lg text-red-400 flex items-center gap-2">
              <Settings className="w-5 h-5" /> Menu Emittente
            </DialogTitle>
          </DialogHeader>
          <div className="p-4 pt-0 space-y-4">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Secondi di Pubblicità</label>
              <div className="flex items-center gap-3">
                <input type="range" min="0" max="120" value={settingsAd} onChange={(e) => setSettingsAd(Number(e.target.value))} className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500" />
                <span className="text-lg font-bold text-red-400 w-12 text-right">{settingsAd}s</span>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <div className="bg-green-500/5 rounded p-1.5 text-center">
                  <p className="text-[9px] text-gray-500">Incasso</p>
                  <p className="text-xs font-bold text-green-400">{settingsAd > 60 ? 'ALTO' : settingsAd > 30 ? 'MEDIO' : 'BASSO'}</p>
                </div>
                <div className="bg-cyan-500/5 rounded p-1.5 text-center">
                  <p className="text-[9px] text-gray-500">Share</p>
                  <p className="text-xs font-bold text-cyan-400">{settingsAd < 30 ? 'ALTO' : settingsAd < 60 ? 'MEDIO' : 'BASSO'}</p>
                </div>
              </div>
            </div>
            <Button className="w-full bg-red-500 hover:bg-red-600" onClick={saveSettings} disabled={savingSettings} data-testid="save-settings-btn">
              {savingSettings ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Check className="w-4 h-4 mr-1" />}
              Salva Impostazioni
            </Button>
            <div className="border-t border-white/5 pt-3 space-y-2">
              <Button variant="outline" className="w-full text-xs h-9 border-cyan-500/20 text-cyan-400" onClick={() => { setShowSettings(false); openScheduleDialog(); }} data-testid="schedule-tv-btn">
                <TrendingUp className="w-3 h-3 mr-2" /> Programma per TV
              </Button>
              <Button variant="outline" className="w-full text-xs h-9 border-white/10" onClick={() => { setShowSettings(false); openAddContent('film'); }}>
                <Film className="w-3 h-3 mr-2 text-yellow-400" /> Aggiungi Film
              </Button>
              <Button variant="outline" className="w-full text-xs h-9 border-white/10" onClick={() => { setShowSettings(false); openAddContent('tv_series'); }}>
                <Tv className="w-3 h-3 mr-2 text-blue-400" /> Aggiungi Serie TV
              </Button>
              <Button variant="outline" className="w-full text-xs h-9 border-white/10" onClick={() => { setShowSettings(false); openAddContent('anime'); }}>
                <Sparkles className="w-3 h-3 mr-2 text-orange-400" /> Aggiungi Anime
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Content Detail Popup */}
      <Dialog open={!!selectedTVContent} onOpenChange={(open) => { if (!open) setSelectedTVContent(null); }}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-sm p-0 overflow-hidden" data-testid="tv-content-detail-popup">
          {selectedTVContent && (() => {
            const c = selectedTVContent;
            return (
              <>
                <div className="aspect-video relative">
                  {c.poster_url ? (
                    <img src={posterSrc(c.poster_url)} alt={c.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-red-500/10 flex items-center justify-center">
                      <Film className="w-12 h-12 text-red-400/30" />
                    </div>
                  )}
                  <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-[#0F0F10] via-[#0F0F10]/60 to-transparent p-3 pt-8">
                    <h2 className="font-['Bebas_Neue'] text-lg leading-tight">{c.title}</h2>
                  </div>
                </div>
                <div className="p-3 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    {c.genre && <Badge className="text-[9px] bg-white/10 text-gray-300">{c.genre}</Badge>}
                    {c.genre_name && <Badge className="text-[9px] bg-white/10 text-gray-300">{c.genre_name}</Badge>}
                    {c.quality_score > 0 && <span className="text-[10px] font-bold text-yellow-400">{c.quality_score}/100</span>}
                    {c.num_episodes > 0 && <span className="text-[10px] text-gray-400">{c.num_episodes} ep.</span>}
                  </div>
                  {c.description && <p className="text-[10px] text-gray-400 line-clamp-3">{c.description}</p>}
                  {isOwner && (
                    <div className="flex gap-2 pt-2 border-t border-white/5">
                      <Button variant="outline" size="sm" className="flex-1 h-8 text-[10px] border-red-500/30 text-red-400" onClick={() => { removeContent(c.id); setSelectedTVContent(null); }} data-testid="tv-detail-remove">
                        <Trash2 className="w-3 h-3 mr-1" /> Togli dalla TV
                      </Button>
                      <Button variant="outline" size="sm" className="flex-1 h-8 text-[10px] border-green-500/30 text-green-400" onClick={() => setSelectedTVContent(null)} data-testid="tv-detail-keep">
                        <Check className="w-3 h-3 mr-1" /> Mantieni in TV
                      </Button>
                    </div>
                  )}
                </div>
              </>
            );
          })()}
        </DialogContent>
      </Dialog>

      {/* Start Broadcast Dialog */}
      <Dialog open={!!showStartBroadcast} onOpenChange={(open) => { if (!open) setShowStartBroadcast(null); }}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-sm p-0" data-testid="start-broadcast-dialog">
          <DialogHeader className="p-4 pb-2">
            <DialogTitle className="font-['Bebas_Neue'] text-lg text-green-400 flex items-center gap-2">
              <Play className="w-5 h-5" /> Avvia Trasmissione
            </DialogTitle>
          </DialogHeader>
          <div className="p-4 pt-0 space-y-4">
            <div>
              <label className="text-xs text-gray-400 mb-2 block">Intervallo tra episodi</label>
              <div className="grid grid-cols-4 gap-1.5">
                {[{v:0,l:'Binge'},{v:1,l:'1 giorno'},{v:2,l:'2 giorni'},{v:3,l:'3 giorni'}].map(opt => (
                  <button
                    key={opt.v}
                    onClick={() => setBroadcastInterval(opt.v)}
                    className={`text-xs px-2 py-2 rounded-lg border transition-all ${
                      broadcastInterval === opt.v
                        ? 'bg-green-500/20 border-green-500/50 text-green-400'
                        : 'bg-black/20 border-white/5 text-gray-400 hover:border-white/15'
                    }`}
                    data-testid={`interval-${opt.v}`}
                  >
                    {opt.l}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-4 gap-1.5 mt-1.5">
                {[{v:4,l:'4 giorni'},{v:5,l:'5 giorni'},{v:6,l:'6 giorni'},{v:7,l:'Settimanale'}].map(opt => (
                  <button
                    key={opt.v}
                    onClick={() => setBroadcastInterval(opt.v)}
                    className={`text-xs px-2 py-2 rounded-lg border transition-all ${
                      broadcastInterval === opt.v
                        ? 'bg-green-500/20 border-green-500/50 text-green-400'
                        : 'bg-black/20 border-white/5 text-gray-400 hover:border-white/15'
                    }`}
                    data-testid={`interval-${opt.v}`}
                  >
                    {opt.l}
                  </button>
                ))}
              </div>
            </div>
            <Card className="bg-black/30 border-white/5">
              <CardContent className="p-3 text-[10px] text-gray-400 space-y-1">
                <p>{broadcastInterval === 0 ? 'Tutti gli episodi vanno in onda subito' : `1 episodio ogni ${broadcastInterval} ${broadcastInterval === 1 ? 'giorno' : 'giorni'}`}</p>
                <p className="text-green-400/80">Il primo episodio va in onda immediatamente</p>
                {broadcastInterval === 0 && <p className="text-amber-400/80">Binge: tutto subito ma meno hype per episodio</p>}
              </CardContent>
            </Card>
            <Button
              className="w-full h-10 bg-green-500 hover:bg-green-600 font-['Bebas_Neue'] text-base"
              onClick={() => startBroadcast(showStartBroadcast)}
              disabled={startingBroadcast}
              data-testid="confirm-start-broadcast"
            >
              {startingBroadcast ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
              TRASMETTI
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Broadcast Detail Dialog */}
      <Dialog open={!!showBroadcastDialog} onOpenChange={(open) => { if (!open) { setShowBroadcastDialog(null); setBroadcastDetail(null); } }}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-md max-h-[85vh] overflow-y-auto p-0" data-testid="broadcast-detail-dialog">
          <DialogHeader className="p-4 pb-2">
            <DialogTitle className="font-['Bebas_Neue'] text-lg text-green-400 flex items-center gap-2">
              <Zap className="w-5 h-5" /> Trasmissione
            </DialogTitle>
          </DialogHeader>
          {broadcastLoading ? (
            <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-green-400 animate-spin" /></div>
          ) : broadcastDetail ? (
            <div className="px-4 pb-4 space-y-3">
              {/* Header */}
              <div className="flex gap-3">
                <div className="w-[60px] h-[90px] rounded-lg overflow-hidden flex-shrink-0">
                  <img src={posterSrc(broadcastDetail.series_poster)} alt="" className="w-full h-full object-cover" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                </div>
                <div>
                  <h3 className="text-sm font-bold">{broadcastDetail.series_title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className={`text-[8px] border-0 ${broadcastDetail.broadcast_state === 'airing' ? 'bg-green-500/20 text-green-400' : broadcastDetail.broadcast_state === 'completed' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'}`}>
                      {broadcastDetail.broadcast_state === 'airing' ? 'In onda' : broadcastDetail.broadcast_state === 'completed' ? 'Completata' : broadcastDetail.broadcast_state}
                    </Badge>
                    {broadcastDetail.rerun_count > 0 && <Badge className="text-[8px] bg-amber-500/10 text-amber-400 border-0">Repliche x{broadcastDetail.rerun_count}</Badge>}
                  </div>
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    <div className="text-center">
                      <p className="text-xs font-bold text-green-400">{broadcastDetail.current_episode}/{broadcastDetail.total_episodes}</p>
                      <p className="text-[8px] text-gray-500">Episodi</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs font-bold text-cyan-400">{(broadcastDetail.total_viewers || 0).toLocaleString()}</p>
                      <p className="text-[8px] text-gray-500">Viewers</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs font-bold text-green-400">${(broadcastDetail.total_revenue || 0).toLocaleString()}</p>
                      <p className="text-[8px] text-gray-500">Revenue</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all" style={{ width: `${broadcastDetail.total_episodes > 0 ? (broadcastDetail.current_episode / broadcastDetail.total_episodes) * 100 : 0}%` }} />
              </div>

              {/* Episode list */}
              <div className="space-y-1.5">
                {(broadcastDetail.episodes || []).map((ep) => {
                  const isAired = ep.broadcast_state === 'aired';
                  const isOnAir = ep.broadcast_state === 'on_air';
                  const typeIcons = { peak: 'text-amber-400', filler: 'text-gray-500', plot_twist: 'text-purple-400', season_finale: 'text-red-400', normal: 'text-gray-400' };
                  const typeLabels = { peak: 'PEAK', filler: 'FILLER', plot_twist: 'TWIST', season_finale: 'FINALE', normal: '' };

                  return (
                    <div key={ep.number} className={`rounded-lg p-2 flex items-center gap-2 ${isOnAir ? 'bg-green-500/10 border border-green-500/30' : isAired ? 'bg-white/[0.03]' : 'bg-black/20 opacity-50'}`} data-testid={`broadcast-ep-${ep.number}`}>
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${isOnAir ? 'bg-green-500 text-white' : isAired ? 'bg-white/10 text-white' : 'bg-white/5 text-gray-600'}`}>
                        {ep.number}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <p className="text-[10px] font-medium truncate">{ep.title || `Ep. ${ep.number}`}</p>
                          {typeLabels[ep.episode_type] && (
                            <span className={`text-[7px] font-bold ${typeIcons[ep.episode_type]}`}>{typeLabels[ep.episode_type]}</span>
                          )}
                        </div>
                        {ep.plot && <p className="text-[8px] text-gray-500 truncate">{ep.plot}</p>}
                      </div>
                      <div className="text-right flex-shrink-0">
                        {isAired && (
                          <div>
                            <p className="text-[9px] font-bold text-cyan-400">{(ep.viewers || 0).toLocaleString()}</p>
                            <p className="text-[8px] text-green-400">${(ep.revenue || 0).toLocaleString()}</p>
                          </div>
                        )}
                        {isOnAir && (
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                            <span className="text-[9px] text-green-400">LIVE</span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Post-season actions */}
              {broadcastDetail.broadcast_state === 'completed' && (
                <div className="flex gap-2 pt-2 border-t border-white/5">
                  <Button size="sm" className="flex-1 h-8 text-[10px] bg-amber-500/20 hover:bg-amber-500/30 text-amber-400" onClick={() => { startReruns(broadcastDetail.content_id); }} data-testid="dialog-reruns-btn">
                    <RefreshCw className="w-3 h-3 mr-1" /> Avvia Repliche
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1 h-8 text-[10px] border-red-500/30 text-red-400" onClick={() => { retireSeries(broadcastDetail.content_id); }} data-testid="dialog-retire-btn">
                    <Ban className="w-3 h-3 mr-1" /> Ritira
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="py-8 text-center text-gray-500 text-xs">Nessun dato</div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}


function ContentAddDialog({ showAddContent, setShowAddContent, availableContent, contentLoading, addContent, posterSrc }) {
  const labels = { film: 'Film', tv_series: 'Serie TV', anime: 'Anime' };
  const items = showAddContent === 'film' ? availableContent.films
    : showAddContent === 'tv_series' ? availableContent.tv_series
    : showAddContent === 'anime' ? availableContent.anime : [];

  return (
    <Dialog open={!!showAddContent} onOpenChange={(open) => { if (!open) setShowAddContent(null); }}>
      <DialogContent className="bg-[#0F0F10] border-white/10 max-w-sm max-h-[80vh] overflow-y-auto p-0" data-testid="add-content-dialog">
        <DialogHeader className="p-4 pb-2">
          <DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
            <Plus className="w-5 h-5 text-red-400" /> Aggiungi {labels[showAddContent]}
          </DialogTitle>
        </DialogHeader>
        <div className="p-4 pt-0">
          {contentLoading ? (
            <div className="flex items-center justify-center py-8"><Loader2 className="w-6 h-6 text-red-400 animate-spin" /></div>
          ) : items.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 text-xs">Nessun contenuto disponibile</p>
              {showAddContent === 'film' && <p className="text-gray-600 text-[10px] mt-1">I film sono inseribili solo dopo l'uscita dal cinema</p>}
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-2">
              {items.map(item => (
                <button
                  key={item.id}
                  className="group text-left"
                  onClick={() => addContent(item.id, showAddContent)}
                  data-testid={`select-content-${item.id}`}
                >
                  <div className="aspect-[2/3] rounded-lg overflow-hidden relative border border-white/5 hover:border-red-500/40 transition-colors">
                    <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                      <Plus className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>
                  <p className="text-[8px] font-medium truncate mt-0.5">{item.title}</p>
                  {item.quality_score && <p className="text-[7px] text-gray-500">Q: {item.quality_score}</p>}
                </button>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
