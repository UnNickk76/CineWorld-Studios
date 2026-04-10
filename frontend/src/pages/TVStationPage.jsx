// CineWorld - TV Station Page (Pure Netflix Dashboard + Modals)
// Setup wizard + Netflix-only visual dashboard
// All management lives inside TVMenuModal, SeriesDetailModal, PalinsestoModal

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import {
  Radio, Tv, Sparkles, Film, Plus, ChevronRight, ChevronLeft,
  Loader2, DollarSign, Eye, Globe, Menu as MenuIcon
} from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

// Modals
import { SeriesDetailModal } from '../components/SeriesDetailModal';
import { PalinsestoModal } from '../components/PalinsestoModal';
import { TVMenuModal } from '../components/TVMenuModal';

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
  const [scheduledItems, setScheduledItems] = useState([]);

  // Setup wizard
  const [setupStep, setSetupStep] = useState(0);
  const [stationName, setStationName] = useState('');
  const [selectedNation, setSelectedNation] = useState('Italia');
  const [adSeconds, setAdSeconds] = useState(30);
  const [setupLoading, setSetupLoading] = useState(false);
  const [newStationId, setNewStationId] = useState(null);

  // Modals state
  const [showMenu, setShowMenu] = useState(false);
  const [selectedContent, setSelectedContent] = useState(null); // for SeriesDetailModal
  const [palinsestoSeries, setPalinsestoSeries] = useState(null); // for PalinsestoModal
  const [filmDetail, setFilmDetail] = useState(null); // for film popup

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

  // Setup wizard handlers
  const submitStep1 = async () => {
    if (!stationName.trim()) return toast.error('Inserisci un nome');
    setSetupLoading(true);
    try {
      const res = await api.post('/tv-stations/setup-step1', { infra_id: infraId, station_name: stationName, nation: selectedNation });
      setNewStationId(res.data.station.id);
      setSetupStep(2);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setSetupLoading(false);
  };

  const submitStep2 = async () => {
    setSetupLoading(true);
    try {
      await api.post('/tv-stations/setup-step2', { station_id: newStationId, ad_seconds: adSeconds });
      toast.success('Emittente TV configurata!');
      navigate(`/tv-station/${newStationId}`, { replace: true });
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setSetupLoading(false);
  };

  // Handle click on any content poster
  const handleContentClick = (item) => {
    const isSeries = item.type === 'anime' || item.type === 'tv_series' || item.content_type === 'anime' || item.content_type === 'tv_series' || item.num_episodes > 0;
    if (isSeries) {
      setSelectedContent(item);
    } else {
      setFilmDetail(item);
    }
  };

  // === SETUP STEP 1 ===
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
                  <Input value={stationName} onChange={(e) => setStationName(e.target.value)} placeholder="es. CineWorld TV, NeoFlix, TeleStudio..." maxLength={30} className="bg-black/40 border-white/10" data-testid="station-name-input" />
                  <p className="text-[10px] text-gray-600 mt-1">{stationName.length}/30 caratteri - Non potrai cambiarlo!</p>
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-2 block">Nazione</label>
                  <div className="grid grid-cols-3 gap-1.5 max-h-48 overflow-y-auto">
                    {NATIONS.map(n => (
                      <button key={n} onClick={() => setSelectedNation(n)} className={`text-xs px-2 py-1.5 rounded-lg border transition-all ${selectedNation === n ? 'bg-red-500/20 border-red-500/50 text-red-400' : 'bg-black/20 border-white/5 text-gray-400 hover:border-white/15'}`} data-testid={`nation-${n}`}>{n}</button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
            <Button className="w-full h-12 bg-red-500 hover:bg-red-600 font-['Bebas_Neue'] text-lg" onClick={submitStep1} disabled={setupLoading || !stationName.trim()} data-testid="step1-submit">
              {setupLoading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : null}
              PROSEGUI <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          </motion.div>
        </div>
      </div>
    );
  }

  // === SETUP STEP 2 ===
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
              <p className="text-sm text-gray-500 mt-1">Step 2: Pubblicità</p>
            </div>
            <Card className="bg-[#111113] border-red-500/20 mb-4">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400">Secondi di Pubblicità per Contenuto</span>
                  <span className="text-lg font-bold text-red-400">{adSeconds}s</span>
                </div>
                <input type="range" min="0" max="120" value={adSeconds} onChange={(e) => setAdSeconds(Number(e.target.value))} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500" data-testid="ad-slider" />
                <div className="flex justify-between text-[9px] text-gray-600 mt-1">
                  <span>0s (no ads)</span><span>60s</span><span>120s (max)</span>
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
            <Button className="w-full h-12 bg-red-500 hover:bg-red-600 font-['Bebas_Neue'] text-lg mt-4" onClick={submitStep2} disabled={setupLoading} data-testid="step2-submit">
              {setupLoading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : null}
              AVVIA L'EMITTENTE <Radio className="w-5 h-5 ml-2" />
            </Button>
          </motion.div>
        </div>
      </div>
    );
  }

  // Loading
  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center pt-16">
      <Loader2 className="w-8 h-8 text-red-400 animate-spin" />
    </div>
  );

  // Not found
  if (!station) return (
    <div className="min-h-screen bg-[#0A0A0B] text-white flex items-center justify-center pt-16">
      <p className="text-gray-500">Stazione non trovata</p>
    </div>
  );

  // === PURE NETFLIX DASHBOARD ===
  const allContentsEmpty = !enrichedContents.films.length && !enrichedContents.tv_series.length && !enrichedContents.anime.length;

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-14" data-testid="tv-station-page">
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
            <Button size="sm" variant="outline" className="h-8 text-xs border-white/10 gap-1.5" onClick={() => setShowMenu(true)} data-testid="tv-menu-btn">
              <MenuIcon className="w-3.5 h-3.5" /> Menu
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

      {/* Netflix Content Area */}
      <div className="px-3">
        {!allContentsEmpty ? (
          <>
            {/* Prossimamente */}
            {scheduledItems.length > 0 && (
              <NetflixRow title="Prossimamente" items={scheduledItems} color="cyan-400" onItemClick={handleContentClick} isScheduled />
            )}

            {/* Airing now - show series/anime that are currently airing */}
            {(() => {
              const airingNow = [...(enrichedContents.tv_series || []), ...(enrichedContents.anime || [])].filter(i => i.broadcast_state === 'airing');
              return airingNow.length > 0 ? <NetflixRow title="In Onda Ora" items={airingNow} color="green-400" onItemClick={handleContentClick} showBroadcastBadge /> : null;
            })()}

            <NetflixRow title="Consigliati" items={netflixSections.consigliati} color="white" onItemClick={handleContentClick} />
            <NetflixRow title="Del Momento" items={netflixSections.del_momento} color="red-400" onItemClick={handleContentClick} />
            <NetflixRow title="I Piu Visti" items={netflixSections.piu_visti} color="yellow-400" onItemClick={handleContentClick} />

            {/* Show all films in a row */}
            {enrichedContents.films.length > 0 && (
              <NetflixRow title="Film" items={enrichedContents.films} color="yellow-400" onItemClick={handleContentClick} />
            )}
            {/* Show all series */}
            {enrichedContents.tv_series.length > 0 && (
              <NetflixRow title="Serie TV" items={enrichedContents.tv_series} color="blue-400" onItemClick={handleContentClick} showBroadcastBadge />
            )}
            {/* Show all anime */}
            {enrichedContents.anime.length > 0 && (
              <NetflixRow title="Anime" items={enrichedContents.anime} color="orange-400" onItemClick={handleContentClick} showBroadcastBadge />
            )}
          </>
        ) : isOwner ? (
          <>
            {/* Empty palinsesto structure with placeholder slots */}
            <EmptyPalinsestoRow title="Prossimamente" color="cyan-400" slots={3} onSlotClick={() => setShowMenu(true)} />
            <EmptyPalinsestoRow title="In Onda Ora" color="green-400" slots={2} onSlotClick={() => setShowMenu(true)} />
            <EmptyPalinsestoRow title="Consigliati" color="white" slots={4} onSlotClick={() => setShowMenu(true)} />
            <EmptyPalinsestoRow title="Del Momento" color="red-400" slots={3} onSlotClick={() => setShowMenu(true)} />
            <EmptyPalinsestoRow title="I Piu Visti" color="yellow-400" slots={3} onSlotClick={() => setShowMenu(true)} />
            <EmptyPalinsestoRow title="Film" color="yellow-400" slots={3} onSlotClick={() => setShowMenu(true)} />
            <EmptyPalinsestoRow title="Serie TV" color="blue-400" slots={2} onSlotClick={() => setShowMenu(true)} />
            <EmptyPalinsestoRow title="Anime" color="orange-400" slots={2} onSlotClick={() => setShowMenu(true)} />
          </>
        ) : (
          <div className="text-center py-12">
            <Radio className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Nessun contenuto in programmazione</p>
          </div>
        )}
      </div>

      {/* === MODALS === */}

      {/* TV Menu Modal (4 sections) */}
      <TVMenuModal
        open={showMenu}
        onClose={() => setShowMenu(false)}
        station={station}
        enrichedContents={enrichedContents}
        capacity={capacity}
        shareData={shareData}
        infraLevel={infraLevel}
        onRefresh={() => loadStation(stationId)}
        onOpenPalinsesto={(series) => setPalinsestoSeries(series)}
        onOpenContentDetail={(item) => {
          setShowMenu(false);
          handleContentClick({ ...item, id: item.id, type: item._contentType || item.content_type });
        }}
      />

      {/* Series/Anime Detail Modal */}
      <SeriesDetailModal
        open={!!selectedContent}
        onClose={() => setSelectedContent(null)}
        series={selectedContent}
        stationId={stationId}
        isOwner={isOwner}
        onManagePalinsesto={(series) => setPalinsestoSeries(series)}
      />

      {/* Palinsesto Modal */}
      <PalinsestoModal
        open={!!palinsestoSeries}
        onClose={() => setPalinsestoSeries(null)}
        series={palinsestoSeries}
        stationId={stationId}
        onRefresh={() => loadStation(stationId)}
      />

      {/* Film Detail Popup */}
      {filmDetail && (
        <FilmDetailPopup
          film={filmDetail}
          onClose={() => setFilmDetail(null)}
        />
      )}
    </div>
  );
}

// Netflix-style horizontal scroll row
function NetflixRow({ title, items, color = 'white', onItemClick, isScheduled, showBroadcastBadge }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="mb-5">
      <h3 className={`text-sm font-bold mb-2 px-1 text-${color}`}>{title}</h3>
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
        {items.map((item, i) => {
          const bstate = item.broadcast_state;
          return (
            <div
              key={item.id || i}
              className="flex-shrink-0 w-[80px] group relative cursor-pointer"
              data-testid={`netflix-item-${item.id}`}
              onClick={() => onItemClick?.(item)}
            >
              <div className={`aspect-[2/3] rounded-lg overflow-hidden relative ${isScheduled ? 'ring-1 ring-cyan-500/30' : ''}`}>
                <img
                  src={posterSrc(item.poster_url)}
                  alt={item.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  loading="lazy"
                  onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300'; }}
                />
                {/* Broadcast state badge */}
                {showBroadcastBadge && bstate && bstate !== 'idle' && (
                  <div className="absolute top-1 left-1">
                    <Badge className={`text-[6px] h-3 border-0 px-1 ${
                      bstate === 'airing' ? 'bg-green-500/90 text-white' :
                      bstate === 'scheduled' ? 'bg-blue-500/80 text-white' :
                      bstate === 'completed' ? 'bg-cyan-500/80 text-white' :
                      bstate === 'reruns' ? 'bg-amber-500/80 text-white' :
                      'bg-gray-500/80 text-white'
                    }`}>
                      {bstate === 'airing' ? 'LIVE' : bstate === 'scheduled' ? 'PROG' : bstate === 'completed' ? 'FINE' : bstate === 'reruns' ? 'REP' : ''}
                    </Badge>
                  </div>
                )}
                {isScheduled && (
                  <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 p-1">
                    <Badge className="text-[6px] h-3 bg-cyan-500/20 text-cyan-400 border-0">
                      {item.status === 'in_theaters' ? 'Al cinema' : item.status === 'production' ? 'In produzione' : item.status}
                    </Badge>
                  </div>
                )}
              </div>
              <p className="text-[8px] font-medium truncate mt-1 px-0.5">{item.title}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Simple film detail popup (no management needed)
function FilmDetailPopup({ film, onClose }) {
  if (!film) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70" onClick={(e) => { e.stopPropagation(); onClose(); }}>
      <div className="bg-[#0F0F10] border border-white/10 rounded-xl max-w-sm w-[90vw] overflow-hidden" onClick={e => e.stopPropagation()} data-testid="film-detail-popup">
        <div className="aspect-video relative">
          <img src={posterSrc(film.poster_url)} alt={film.title} className="w-full h-full object-cover" />
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-[#0F0F10] via-[#0F0F10]/60 to-transparent p-3 pt-8">
            <h2 className="font-['Bebas_Neue'] text-lg leading-tight">{film.title}</h2>
          </div>
          <button onClick={onClose} className="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/60 flex items-center justify-center text-white hover:bg-black/80">
            <span className="text-sm">&#10005;</span>
          </button>
        </div>
        <div className="p-3 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            {(film.genre || film.genre_name) && <Badge className="text-[9px] bg-white/10 text-gray-300">{film.genre || film.genre_name}</Badge>}
            {film.quality_score > 0 && <span className="text-[10px] font-bold text-yellow-400">{film.quality_score}/100</span>}
          </div>
          {film.description && <p className="text-[10px] text-gray-400 line-clamp-3">{film.description}</p>}
        </div>
      </div>
    </div>
  );
}

// Empty palinsesto row with placeholder slots (film icon, clickable)
function EmptyPalinsestoRow({ title, color, slots, onSlotClick }) {
  return (
    <div className="mb-4">
      <h3 className={`font-['Bebas_Neue'] text-sm text-${color} mb-2 tracking-wide`}>{title}</h3>
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
        {Array.from({ length: slots }).map((_, i) => (
          <div
            key={i}
            className="flex-shrink-0 w-[80px] cursor-pointer group"
            onClick={onSlotClick}
            data-testid={`empty-slot-${title.toLowerCase().replace(/\s/g,'-')}-${i}`}
          >
            <div className="aspect-[2/3] rounded-lg border border-dashed border-white/10 bg-white/[0.02] flex items-center justify-center group-hover:border-red-500/30 group-hover:bg-red-500/5 transition-all">
              <Film className="w-5 h-5 text-gray-600 group-hover:text-red-400 transition-colors" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

