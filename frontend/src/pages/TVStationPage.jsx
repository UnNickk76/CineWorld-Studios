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
  Loader2, DollarSign, Eye, TrendingUp, Globe, Check, Minus, Trash2, BarChart3
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

  // Settings popup
  const [showSettings, setShowSettings] = useState(false);
  const [settingsAd, setSettingsAd] = useState(30);
  const [savingSettings, setSavingSettings] = useState(false);

  const loadStation = useCallback(async (id) => {
    try {
      const res = await api.get(`/tv-stations/${id}`);
      setStation(res.data.station);
      setEnrichedContents(res.data.enriched_contents);
      setShareData(res.data.share_data);
      setNetflixSections(res.data.netflix_sections);
      setIsOwner(res.data.is_owner);
      setSettingsAd(res.data.station?.ad_seconds || 30);
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
            <div key={item.id || i} className="flex-shrink-0 w-[110px] group relative cursor-pointer" data-testid={`netflix-item-${item.id}`}>
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
              <p className="text-[10px] font-medium truncate mt-1 px-0.5">{item.title}</p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const ContentManagementRow = ({ type, label, icon: Icon, color, items }) => (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2 px-1">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 text-${color}-400`} />
          <span className="text-sm font-bold">{label}</span>
          <Badge className="text-[9px] bg-white/5">{items.length}</Badge>
        </div>
        {isOwner && (
          <Button size="sm" variant="ghost" className={`h-6 text-[10px] text-${color}-400`} onClick={() => openAddContent(type)} data-testid={`manage-add-${type}`}>
            <Plus className="w-3 h-3 mr-0.5" /> Aggiungi
          </Button>
        )}
      </div>
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
        {items.map((item) => (
          <div key={item.id} className="flex-shrink-0 w-[90px] group relative">
            <div className="aspect-[2/3] rounded-lg overflow-hidden">
              <img src={posterSrc(item.poster_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
              {isOwner && (
                <button className="absolute top-0.5 right-0.5 p-0.5 bg-black/70 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => removeContent(item.id)}>
                  <Trash2 className="w-2.5 h-2.5 text-red-400" />
                </button>
              )}
            </div>
            <p className="text-[8px] font-medium truncate mt-0.5">{item.title}</p>
          </div>
        ))}
        {isOwner && items.length === 0 && (
          <button className="flex-shrink-0 w-[90px] aspect-[2/3] rounded-lg border border-dashed border-white/10 flex items-center justify-center hover:border-red-500/30 transition-colors" onClick={() => openAddContent(type)}>
            <Plus className="w-5 h-5 text-gray-600" />
          </button>
        )}
      </div>
    </div>
  );

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
          <div className="grid grid-cols-4 gap-2 mt-3" data-testid="station-stats">
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
              <p className="text-sm font-bold text-yellow-400">{shareData.total_content}</p>
              <p className="text-[8px] text-gray-500">Contenuti</p>
            </div>
          </div>
        )}
      </div>

      <div className="px-3">
        {/* Netflix Sections */}
        {!allContentsEmpty ? (
          <>
            <NetflixRow title="Consigliati" items={netflixSections.consigliati} color="white" />
            <NetflixRow title="Del Momento" items={netflixSections.del_momento} color="red-400" />
            <NetflixRow title="I Più Visti" items={netflixSections.piu_visti} color="yellow-400" />
          </>
        ) : (
          <div className="text-center py-8">
            <Radio className="w-10 h-10 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Nessun contenuto in programmazione</p>
            {isOwner && <p className="text-gray-600 text-xs mt-1">Aggiungi film, serie TV o anime qui sotto</p>}
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
