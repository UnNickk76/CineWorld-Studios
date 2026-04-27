// CineWorld Studio's - Dashboard (Vetrina Mobile-First)
// Sections: LaPrima, Eventi WOW, Prossimamente/Ultimi per tipo

import React, { useState, useEffect, useCallback, useContext, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, LanguageContext, useTranslations, useProductionMenu } from '../contexts';
import { useSWR } from '../contexts/GameStore';
import { LaPrimaSection } from '../components/LaPrimaSection';
import { ComingSoonSection } from '../components/ComingSoonSection';
import BestHighlightsLeaderboard from '../components/BestHighlightsLeaderboard';
import FeaturedTrailersStrip from '../components/FeaturedTrailersStrip';
import UltimiTrailerStrip from '../components/UltimiTrailerStrip';
import VelionCinematicEvent from '../components/VelionCinematicEvent';
import { ProducerBadge } from '../components/ProducerBadge';
import { LampoLightning } from '../components/LampoLightning';
import TvRightsBadge from '../components/TvRightsBadge';
import VmRatingBadge from '../components/VmRatingBadge';
import TvMarketModal from '../components/TvMarketModal';
import TvMarketDashboardWidget from '../components/TvMarketDashboardWidget';
import { SectionSortMenu, sortItems, DEFAULT_SORT_OPTIONS } from '../components/SectionSortMenu';
import ProssimamenteDetailModal from '../components/ProssimamenteDetailModal';
import { MasterpieceBadge, PlayerBadge } from '../components/PlayerBadge';
import { PurchasedScreenplayBadge } from '../components/PurchasedScreenplayBadge';
import { AttendanceTrendBadge } from '../components/AttendanceTrendBadge';
import { Card, CardContent } from '../components/ui/card';

const FilmDetailV3 = lazy(() => import('../components/v3/FilmDetailV3'));
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { Avatar, AvatarImage, AvatarFallback } from '../components/ui/avatar';
import { AvatarWithLogo } from '../components/StudioName';
import {
  Film, Sparkles, ChevronRight, Globe, Loader2, DollarSign, TrendingUp, Heart,
  Clapperboard, MapPin, Building, Tv, Star, Menu as MenuIcon, Clock,
  Store, Pen, Gamepad2, Trophy, Target, Award, Radio, Users
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400';
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};


const RiCinemaShowcase = ({ api, navigate }) => {
  const [events, setEvents] = useState([]);
  useEffect(() => {
    const BACKEND = process.env.REACT_APP_BACKEND_URL || '';
    const token = localStorage.getItem('cineworld_token');
    fetch(`${BACKEND}/api/ri-cinema/showcase`, { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json()).then(d => setEvents(d?.events || [])).catch(() => {});
  }, []);
  if (events.length === 0) return null;
  const BACKEND = process.env.REACT_APP_BACKEND_URL || '';
  return (
    <div className="px-1 mb-4" data-testid="ri-cinema-showcase">
      <h2 className="text-sm font-bold text-white mb-2 flex items-center gap-1.5">
        <Film className="w-3.5 h-3.5 text-amber-400" />
        Evento Ri-Cinema
        <span className="text-[8px] text-amber-400/60 bg-amber-500/10 px-1.5 py-0.5 rounded font-normal">{events.length} attivi</span>
      </h2>
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {events.map(ev => (
          <div key={ev.id} className="flex-shrink-0 w-[110px] rounded-lg border border-amber-500/20 bg-[#111113] overflow-hidden cursor-pointer active:scale-95 transition-transform"
            onClick={() => navigate(`/films`)}>
            <div className="relative h-[140px] bg-gray-800">
              {ev.poster_url && <img src={ev.poster_url?.startsWith('/') ? `${BACKEND}${ev.poster_url}` : ev.poster_url} alt="" className="w-full h-full object-cover" />}
              {ev.is_cult && <span className="absolute top-1 left-1 text-[7px] bg-yellow-500/90 text-black font-black px-1 rounded">CULT</span>}
              <span className="absolute bottom-1 right-1 text-[7px] bg-black/70 text-amber-400 font-bold px-1 rounded">{ev.day_number}/{ev.days}gg</span>
            </div>
            <div className="p-1.5">
              <p className="text-[8px] font-bold text-white truncate">{ev.film_title}</p>
              <p className="text-[7px] text-gray-500 truncate">{ev.host_name}</p>
              <p className="text-[7px] text-cyan-400">{(ev.total_spectators || 0).toLocaleString()} spett.</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};



/* ─── Prossimamente V3 Serie/Anime ─── */
const ProssimamenteV3Section = ({ onItemClick }) => {
  const { api, user } = useContext(AuthContext);
  const [data, setData] = useState({ coming_soon: [], airing: [] });
  const [sortValue, setSortValue] = useState(() => localStorage.getItem('sort_prossimamente_v3') || 'newest');
  useEffect(() => { localStorage.setItem('sort_prossimamente_v3', sortValue); }, [sortValue]);
  useEffect(() => {
    api.get('/pipeline-series-v3/prossimamente').then(r => setData(r.data || {})).catch(() => {});
  }, [api]);
  // Solo "in arrivo" — esclude le serie/anime che sono gia' iniziate ad andare in onda
  // (quelle vanno mostrate in "Ultimi Aggiornamenti Serie TV").
  const rawItems = [...(data.coming_soon || [])];
  const items = sortItems(rawItems, sortValue);
  return (
    <div className="mb-4 rounded-xl" data-testid="prossimamente-v3">
      <Card className="bg-gradient-to-r from-indigo-500/10 to-purple-500/5 border border-indigo-500/20">
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-['Bebas_Neue'] text-base flex items-center gap-2">
              <Tv className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-indigo-400">IN ARRIVO SU TV</span>
            </h3>
            {items.length > 0 && (
              <SectionSortMenu
                value={sortValue}
                onChange={setSortValue}
                options={DEFAULT_SORT_OPTIONS}
                testId="sort-prossimamente-v3"
              />
            )}
          </div>
          {items.length > 0 ? (
            <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
              {items.map(item => (
                <button key={item.id}
                  onClick={() => onItemClick?.(item)}
                  data-testid={`prossimamente-v3-item-${item.id}`}
                  className="flex-shrink-0 w-24 rounded-lg overflow-hidden border border-indigo-500/15 bg-black/30 text-left hover:border-indigo-400/40 active:scale-[0.97] transition-all">
                  <div className="aspect-[2/3] bg-gray-800 relative">
                    {item.poster_url ? <img src={posterSrc(item.poster_url)} alt="" className="w-full h-full object-cover" /> :
                      <div className="w-full h-full flex items-center justify-center">{item.type === 'anime' ? <Sparkles className="w-4 h-4 text-gray-700" /> : <Tv className="w-4 h-4 text-gray-700" />}</div>}
                    {item.aired_count != null && (
                      <div className="absolute bottom-0.5 right-0.5 px-1 py-0.5 rounded bg-black/80 text-[6px] text-indigo-400 font-bold">{item.aired_count}/{item.total_episodes} EP</div>
                    )}
                    {(item.type === 'tv_movie' || item.is_tv_movie) && (
                      <div className="absolute top-0.5 right-0.5 px-1 py-0.5 rounded bg-cyan-500/90 text-[6px] text-black font-black uppercase tracking-wider">Film TV</div>
                    )}
                    {item.pipeline_state && item.pipeline_state !== 'released' && (
                      <div className="status-pulse-glow absolute top-0.5 left-0.5 px-1 py-0.5 rounded-full bg-amber-500/80 text-[5px] text-black font-black uppercase">{item.pipeline_state}</div>
                    )}
                    <ProducerBadge
                      producerNickname={item.producer?.nickname || item.producer_nickname}
                      producerId={item.user_id || item.producer?.id}
                      currentUserId={user?.id}
                      variant="bottom-left"
                      size="xs"
                    />
                    <LampoLightning item={item} variant="bottom-left" size="xs" />
                    {item.vm_rating && (
                      <div className="absolute top-4 left-0.5 z-20">
                        <VmRatingBadge rating={item.vm_rating} size="xs" />
                      </div>
                    )}
                    {item.tv_rights_active_contract_id && item.tv_rights_station_name && (
                      <span className="absolute bottom-1 right-1 z-10 px-1 py-0.5 rounded text-[6px] font-black uppercase bg-cyan-400 text-black border border-cyan-300/50 shadow flex items-center gap-0.5 max-w-[80%] truncate">
                        📺 {item.tv_rights_station_name}
                      </span>
                    )}
                  </div>
                  <div className="p-1">
                    <p className="text-[7px] font-bold text-white truncate">{item.title}</p>
                    <p className="text-[6px] text-gray-500">{item.producer?.production_house_name || item.producer_house || item.producer?.nickname || item.producer_nickname || ''}</p>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2 py-4 rounded-lg border border-dashed border-indigo-500/20 bg-indigo-500/5" data-testid="prossimamente-v3-empty">
              <Clock className="w-3.5 h-3.5 text-indigo-400/50" />
              <span className="text-[10px] text-indigo-300/60 italic">Nessun contenuto in arrivo</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};


const Dashboard = () => {
  const { user, api, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();

  // Data from batch
  const [recentReleases, setRecentReleases] = useState([]);
  const [aBreveCinema, setABreveCinema] = useState([]);
  const [selectedFilmId, setSelectedFilmId] = useState(null);
  const [mySeries, setMySeries] = useState([]);
  const [myAnime, setMyAnime] = useState([]);
  const [rightsModalContent, setRightsModalContent] = useState(null);
  const [eventiWow, setEventiWow] = useState([]);

  // Ordinamento per-sezione (persistito in localStorage)
  const [sortRecentFilms, setSortRecentFilms] = useState(() => localStorage.getItem('sort_recent_films') || 'newest');
  const [sortRecentSeries, setSortRecentSeries] = useState(() => localStorage.getItem('sort_recent_series') || 'newest');
  const [sortRecentAnime, setSortRecentAnime] = useState(() => localStorage.getItem('sort_recent_anime') || 'newest');
  useEffect(() => { localStorage.setItem('sort_recent_films', sortRecentFilms); }, [sortRecentFilms]);
  useEffect(() => { localStorage.setItem('sort_recent_series', sortRecentSeries); }, [sortRecentSeries]);
  useEffect(() => { localStorage.setItem('sort_recent_anime', sortRecentAnime); }, [sortRecentAnime]);

  // Dialogs that must remain for gameplay
  const [pendingFilms, setPendingFilms] = useState([]);
  const [shootingFilms, setShootingFilms] = useState([]);
  const [releasePopup, setReleasePopup] = useState(null);
  const [distConfig, setDistConfig] = useState(null);
  const [selectedZone, setSelectedZone] = useState('national');
  const [selectedContinent, setSelectedContinent] = useState('europe');
  const [releasing, setReleasing] = useState(false);
  const [hasStudio, setHasStudio] = useState(false);
  const [releaseSuccess, setReleaseSuccess] = useState(null);
  const [shootingPopup, setShootingPopup] = useState(null);
  const [shootingDays, setShootingDays] = useState(5);
  const [shootingConfig, setShootingConfig] = useState(null);
  const [startingShooting, setStartingShooting] = useState(false);
  const [endingShootingEarly, setEndingShootingEarly] = useState(false);
  const [showShootingDialog, setShowShootingDialog] = useState(false);
  const [showWelcomeStats, setShowWelcomeStats] = useState(false);
  const [levelInfo, setLevelInfo] = useState(null);

  // SideMenu — now global, just track open state for translate
  const [menuOpen, setMenuOpen] = useState(false);
  // Cinematic event for Eventi WOW
  const [cinematicWow, setCinematicWow] = useState(null);
  // V3 series/anime detail modal (dashboard "IN ARRIVO SU TV")
  const [prossimamenteDetailId, setProssimamenteDetailId] = useState(null);

  // Sync with global side menu
  useEffect(() => {
    const onOpen = () => setMenuOpen(true);
    const onClose = () => setMenuOpen(false);
    const onToggle = () => setMenuOpen(p => !p);
    window.addEventListener('global-sidemenu-open', onOpen);
    window.addEventListener('global-sidemenu-close', onClose);
    window.addEventListener('global-sidemenu-toggle', onToggle);
    window.addEventListener('dashboard-toggle-menu', onToggle);
    return () => {
      window.removeEventListener('global-sidemenu-open', onOpen);
      window.removeEventListener('global-sidemenu-close', onClose);
      window.removeEventListener('global-sidemenu-toggle', onToggle);
      window.removeEventListener('dashboard-toggle-menu', onToggle);
    };
  }, []);
  // Old-style action grid
  const [showActionGrid, setShowActionGrid] = useState(false);
  const [tvStationCount, setTvStationCount] = useState(0);
  const [arenaActions, setArenaActions] = useState(0);
  const [contestCount, setContestCount] = useState(0);
  const { setIsOpen: openProductionMenu } = useProductionMenu();

  // SWR batch data
  const { data: batchData } = useSWR('/dashboard/batch');

  // Fetch level info for welcome section
  useEffect(() => {
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {});
  }, [api]);

  // Load recent releases directly from V3 endpoint (independent of economy/stats)
  useEffect(() => {
    api.get('/pipeline-v3/recent-releases').then(r => {
      if (r.data?.items?.length) setRecentReleases(r.data.items);
    }).catch(() => {});
  }, [api]);

  // Load "a breve cinema" films (post La Prima, distribuzione confermata, non ancora rilasciati)
  useEffect(() => {
    api.get('/la-prima/coming-to-cinemas').then(r => {
      setABreveCinema(r.data?.items || []);
    }).catch(() => setABreveCinema([]));
  }, [api]);

  useEffect(() => {
    if (!batchData) return;
    const d = batchData;
    if (d.recent_releases?.length) setRecentReleases(prev => prev.length ? prev : d.recent_releases);
    // Ultimi aggiornamenti Serie TV/Anime: usa feed GLOBALE (visibile a tutti).
    // Fallback alla lista del proprietario se il feed globale non è ancora popolato.
    setMySeries((d.recent_series_global && d.recent_series_global.length > 0) ? d.recent_series_global : (d.my_series || []));
    setMyAnime((d.recent_anime_global && d.recent_anime_global.length > 0) ? d.recent_anime_global : (d.my_anime || []));
    setPendingFilms(d.pending_films || []);
    setHasStudio(d.has_studio || false);
    setShootingFilms(d.shooting_films || []);

    // Derive "Eventi WOW" from recent releases (high quality/masterpiece = EPICO/LEGGENDARIO)
    const wow = (d.recent_releases || [])
      .filter(f => f.quality_score >= 75 || f.is_masterpiece)
      .map(f => ({
        id: f.id,
        titolo: f.title,
        testo: f.is_masterpiece
          ? `Capolavoro! ${f.producer_nickname} ha rilasciato "${f.title}"!`
          : `${f.producer_nickname} ha rilasciato "${f.title}"`,
        rarita: f.is_masterpiece || f.quality_score >= 90 ? 'LEGGENDARIO' : 'EPICO',
        poster: f.poster_url,
        quality: f.quality_score,
        producer: f.producer_nickname,
        filmId: f.id,
      }))
      .slice(0, 3);
    setEventiWow(wow);
  }, [batchData]);

  // Side effects (catchup, shooting config, heartbeat)
  useEffect(() => {
    const fetchExtra = async () => {
      try {
        const catchupRes = await api.post('/catchup/process');
        if (catchupRes.data.catchup_revenue > 0) {
          toast.success(`Bentornato! Recuperati $${catchupRes.data.catchup_revenue.toLocaleString()} per ${catchupRes.data.hours_missed} ore offline!`, { duration: 6000 });
          refreshUser();
        }
      } catch {}
      try {
        const configRes = await api.get('/films/shooting/config');
        setShootingConfig(configRes.data);
      } catch {}
      try {
        const tvRes = await api.get('/tv-stations/my');
        setTvStationCount(tvRes.data.stations?.length || 0);
      } catch {}
      try {
        const pvpRes = await api.get('/pvp/status');
        setArenaActions(pvpRes.data?.remaining_actions || 0);
      } catch {}
    };
    fetchExtra();
    const heartbeat = setInterval(() => { api.post('/activity/heartbeat').catch(() => {}); }, 5 * 60 * 1000);
    return () => clearInterval(heartbeat);
  }, [api]);

  // Listen for side menu toggle — handled by global listener above

  // Release handlers (kept for gameplay)
  const openReleasePopup = async (film) => {
    setReleasePopup(film);
    setSelectedZone('national');
    setSelectedContinent('europe');
    try { const res = await api.get('/distribution/config'); setDistConfig(res.data); } catch {}
  };

  const getZoneCost = () => {
    if (!distConfig) return { funds: 0, cinepass: 0 };
    const zone = distConfig.zones[selectedZone];
    if (!zone) return { funds: 0, cinepass: 0 };
    const qf = 1.0 + ((releasePopup?.quality_score || 50) - 50) / 200;
    const isDirectRelease = releasePopup?.status === 'pending_release';
    return {
      funds: isDirectRelease ? Math.round(zone.base_cost * qf * 0.7) : Math.round(zone.base_cost * qf),
      cinepass: isDirectRelease ? Math.max(1, zone.cinepass_cost - 1) : zone.cinepass_cost
    };
  };

  const handleRelease = async () => {
    if (!releasePopup || !distConfig) return;
    setReleasing(true);
    try {
      let filmId = releasePopup.id;
      let releaseEvents = null;
      if (releasePopup.status === 'pending_release') {
        const pipelineRes = await api.post(`/film-pipeline/${releasePopup.id}/release`);
        if (pipelineRes.data.success) { filmId = pipelineRes.data.film_id; releaseEvents = pipelineRes.data; }
      }
      const res = await api.post(`/films/${filmId}/release`, { distribution_zone: selectedZone, distribution_continent: selectedZone === 'continental' ? selectedContinent : null });
      if (res.data.success) {
        setPendingFilms(prev => prev.filter(f => f.id !== releasePopup.id));
        setReleasePopup(null);
        setReleaseSuccess({
          title: releasePopup.title, revenue: res.data.opening_day_revenue,
          zone: selectedZone === 'national' ? 'Nazionale' : selectedZone === 'continental' ? 'Continentale' : 'Mondiale',
          poster: releasePopup.poster_url, events: releaseEvents?.events, quality_score: releaseEvents?.quality_score,
          imdb_rating: releaseEvents?.imdb_rating, critics: releaseEvents?.critics, tier: releaseEvents?.tier,
        });
        refreshUser().catch(() => {});
      }
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore nel rilascio'); }
    finally { setReleasing(false); }
  };

  const getShootingCost = (film, days) => Math.round((film?.total_budget || film?.production_cost || 500000) * 0.15 * days);

  const handleStartShooting = async () => {
    if (!shootingPopup) return;
    setStartingShooting(true);
    try {
      const res = await api.post(`/films/${shootingPopup.id}/start-shooting`, { shooting_days: shootingDays });
      if (res.data.success) {
        toast.success(res.data.message);
        setPendingFilms(prev => prev.filter(f => f.id !== shootingPopup.id));
        setShootingPopup(null);
        const shootRes = await api.get('/films/shooting');
        setShootingFilms(shootRes.data?.films || []);
        refreshUser().catch(() => {});
      }
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
    finally { setStartingShooting(false); }
  };

  const handleEndShootingEarly = async (filmId) => {
    setEndingShootingEarly(true);
    try {
      const res = await api.post(`/films/${filmId}/end-shooting-early`);
      if (res.data.success) {
        toast.success(res.data.message);
        setShootingFilms(prev => prev.filter(f => f.id !== filmId));
        const pendRes = await api.get('/films/pending');
        setPendingFilms(pendRes.data || []);
        refreshUser().catch(() => {});
      }
    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
    finally { setEndingShootingEarly(false); }
  };

  const openEvento = (evento) => {
    setCinematicWow({
      tier: evento.rarita === 'LEGGENDARIO' ? 'legendary' : 'epic',
      text: evento.testo,
      event_type: 'positive',
      project_type: 'film',
      title: evento.titolo,
      created_at: Date.now().toString(),
      // Film details for the expanded card
      film_id: evento.filmId,
      film_title: evento.titolo,
      film_poster: evento.poster,
      film_quality: evento.quality,
      film_producer: evento.producer,
    });
  };

  return (
    <>
      {cinematicWow && (
        <VelionCinematicEvent events={[cinematicWow]} onAllDone={() => setCinematicWow(null)} />
      )}

      <div>
        <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="dashboard">

          {/* Welcome header */}
          <div className="mb-4" data-testid="dashboard-welcome">
            <div className="flex items-center justify-between gap-2">
              <p className="text-gray-400 text-xs">Benvenuto in CineWorld Studio's,</p>
              {user?.is_guest && (
                <button
                  type="button"
                  onClick={() => window.dispatchEvent(new Event('open-guest-convert'))}
                  data-testid="guest-register-rec-btn"
                  aria-label="Salva progressi — Registrati"
                  title="Salva progressi — Registrati"
                  className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-red-600 hover:bg-red-500 text-white text-[9px] font-black uppercase tracking-wider shadow-lg shadow-red-900/60 animate-pulse"
                  style={{ animationDuration: '2s' }}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" style={{ animationDuration: '1.2s' }} />
                  <span>REC</span>
                </button>
              )}
            </div>
            <button className="text-left w-full" onClick={() => setShowWelcomeStats(p => !p)} data-testid="welcome-nickname-btn">
              <div className="flex items-center gap-2 mt-1">
                {/* Avatar + Logo sovrapposti */}
                <AvatarWithLogo avatarUrl={user?.avatar_url} logoUrl={user?.logo_url} nickname={user?.nickname} size="sm" />
                {/* Nickname + Logo + Production House */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <PlayerBadge badge={user?.badge} badgeExpiry={user?.badge_expiry} badges={user?.badges} size="md" />
                    <span className="text-base font-bold text-yellow-400 truncate">{user?.nickname || 'Player'}</span>
                    {user?.role === 'CO_ADMIN' && <span className="text-[7px] font-mono text-red-400 bg-red-500/10 px-1 py-0.5 rounded">CO-ADMIN</span>}
                    {user?.role === 'MOD' && <span className="text-[7px] font-mono text-blue-400 bg-blue-500/10 px-1 py-0.5 rounded">MOD</span>}
                  </div>
                  {user?.production_house_name && (
                    <div className="flex items-center gap-1 -mt-0.5">
                      <span className="text-[10px] text-gray-500 truncate">{user.production_house_name}</span>
                    </div>
                  )}
                </div>
              </div>
            </button>
            {showWelcomeStats && (
              <div className="mt-2 space-y-2">
                {/* Avatar grande + Logo ben visibili */}
                <div className="flex items-center gap-3">
                  <AvatarWithLogo avatarUrl={user?.avatar_url} logoUrl={user?.logo_url} nickname={user?.nickname} size="md" />
                  {/* Level/Fame */}
                  {levelInfo && (
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] font-bold text-yellow-500/80 bg-yellow-500/10 border border-yellow-500/20 rounded px-1.5 py-0.5">LV {levelInfo.level}</span>
                        <span className="text-[9px] text-amber-400/70 bg-amber-500/10 border border-amber-500/15 rounded px-1.5 py-0.5">Fama {levelInfo.fame?.toLocaleString()}</span>
                      </div>
                      <div className="mt-1 h-1 bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-yellow-600 to-amber-400 rounded-full" style={{ width: `${(levelInfo.xp_progress || 0) * 100}%` }} />
                      </div>
                      <p className="text-[8px] text-gray-600 mt-0.5">{levelInfo.current_xp?.toLocaleString()} / {levelInfo.xp_needed?.toLocaleString()} XP</p>
                    </div>
                  )}
                </div>
                {/* Stats grid */}
                {batchData?.stats && (
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2 border border-white/5 cursor-pointer active:scale-95 transition-transform" onClick={() => navigate('/films')}>
                      <Film className="w-4 h-4 text-yellow-500/70" />
                      <div><p className="text-sm font-bold text-white">{batchData.stats.total_films}</p><p className="text-[8px] text-gray-500">Films</p></div>
                      <ChevronRight className="w-3 h-3 text-gray-600 ml-auto" />
                    </div>
                    <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2 border border-white/5 cursor-pointer active:scale-95 transition-transform" onClick={() => navigate('/finanze')} data-testid="stat-incassi">
                      <DollarSign className="w-4 h-4 text-green-500/70" />
                      <div><p className="text-sm font-bold text-white">${batchData.stats.total_revenue >= 1000000 ? `${(batchData.stats.total_revenue / 1000000).toFixed(1)}M` : batchData.stats.total_revenue >= 1000 ? `${(batchData.stats.total_revenue / 1000).toFixed(0)}K` : batchData.stats.total_revenue?.toLocaleString()}</p><p className="text-[8px] text-gray-500">Incassi</p></div>
                      <ChevronRight className="w-3 h-3 text-gray-600 ml-auto" />
                    </div>
                    <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2 border border-white/5 cursor-pointer active:scale-95 transition-transform" onClick={() => navigate('/social')}>
                      <Heart className="w-4 h-4 text-red-400/70" />
                      <div><p className="text-sm font-bold text-white">{batchData.stats.total_likes}</p><p className="text-[8px] text-gray-500">Like</p></div>
                      <ChevronRight className="w-3 h-3 text-gray-600 ml-auto" />
                    </div>
                    <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2 border border-white/5 cursor-pointer active:scale-95 transition-transform" onClick={() => navigate('/statistics')}>
                      <Star className="w-4 h-4 text-blue-400/70" />
                      <div><p className="text-sm font-bold text-white">{Math.round(batchData.stats.average_quality)}%</p><p className="text-[8px] text-gray-500">Qualità</p></div>
                      <ChevronRight className="w-3 h-3 text-gray-600 ml-auto" />
                    </div>
                  </div>
                )}

                {/* Extra stats — Spettatori + Best Film */}
                {batchData?.stats && (
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2 border border-white/5 cursor-pointer active:scale-95 transition-transform hover:border-cyan-500/30" onClick={() => navigate('/spettatori')} data-testid="stat-spettatori">
                      <Users className="w-4 h-4 text-cyan-400/70" />
                      <div><p className="text-sm font-bold text-white">{batchData.stats.total_spectators ? (batchData.stats.total_spectators >= 1000000 ? `${(batchData.stats.total_spectators/1000000).toFixed(1)}M` : batchData.stats.total_spectators >= 1000 ? `${Math.floor(batchData.stats.total_spectators/1000)}K` : batchData.stats.total_spectators) : '0'}</p><p className="text-[8px] text-gray-500">Spettatori Totali</p></div>
                    </div>
                    {batchData.stats.best_film && (
                      <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2 border border-white/5">
                        <Award className="w-4 h-4 text-yellow-400/70" />
                        <div><p className="text-[10px] font-bold text-white truncate">{batchData.stats.best_film}</p><p className="text-[8px] text-gray-500">Miglior Film</p></div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 1. LaPrima */}
          <div className="mb-4 rounded-xl glow-gold" data-testid="dashboard-la-prima">
            <LaPrimaSection compact />
          </div>

          {/* 1.5 Evento Ri-Cinema */}
          <RiCinemaShowcase api={api} navigate={navigate} />

          {/* 1.75 Ultimi Trailer (fresh from AI, all tiers) — sostituisce 'Trailer da non perdere' (ridondante) */}
          <UltimiTrailerStrip limit={12} />

          {/* 1.8 Best Highlights — Top trailer post-lancio */}
          <BestHighlightsLeaderboard limit={10} />

          {/* 2. Eventi WOW */}
          {eventiWow.length > 0 && (
            <div className="px-1 mb-4" data-testid="eventi-wow-section">
              <h2 className="text-sm font-bold text-white mb-2 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
                Eventi WOW
              </h2>
              <div className="flex overflow-x-auto gap-2.5 pb-1" style={{ scrollbarWidth: 'none' }}>
                {eventiWow.map(evento => (
                  <div
                    key={evento.id}
                    onClick={() => openEvento(evento)}
                    className={`min-w-[140px] h-[90px] rounded-lg p-2 cursor-pointer relative overflow-hidden backdrop-blur-sm border border-white/10 active:scale-95 transition-transform flex gap-2 ${
                      evento.rarita === 'LEGGENDARIO' ? 'glow-gold bg-gradient-to-br from-yellow-900/30 to-amber-900/10' : 'glow-purple bg-gradient-to-br from-purple-900/30 to-violet-900/10'
                    }`}
                    data-testid={`evento-wow-${evento.id}`}
                  >
                    {/* Mini poster */}
                    {evento.poster && (
                      <img src={posterSrc(evento.poster)} alt="" className="h-full w-[45px] object-cover rounded flex-shrink-0" onError={e => { e.target.style.display = 'none'; }} />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-[10px] font-bold text-white leading-tight truncate">{evento.titolo}</div>
                      <div className="text-[8px] opacity-70 line-clamp-2 mt-0.5 leading-tight">{evento.testo}</div>
                    </div>
                    <div className={`absolute bottom-1 right-2 text-[7px] font-bold ${
                      evento.rarita === 'LEGGENDARIO' ? 'text-yellow-400' : 'text-purple-400'
                    }`}>
                      {evento.rarita}
                    </div>
                    {evento.quality > 0 && (
                      <div className="absolute top-1 right-1.5">
                        <Star className={`w-2.5 h-2.5 ${evento.rarita === 'LEGGENDARIO' ? 'text-yellow-400' : 'text-purple-400'}`} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Prossimamente FILM */}
          <div className="mb-4 rounded-xl glow-blue" data-testid="dashboard-coming-soon-film">
            <ComingSoonSection compact filterType="film" sectionTitle="PROSSIMAMENTE FILM" />
          </div>

          {/* TV Market Dashboard Widget — cruscotto produttore TV */}
          <div className="mb-4">
            <TvMarketDashboardWidget />
          </div>

          {/* 4. Ultimi Aggiornamenti FILM */}
          {/* 4. Ultimi Film Al Cinema */}
          <div className="mb-4 rounded-xl glow-purple" data-testid="recent-releases-film">
            <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/5 border border-purple-500/20">
              <CardContent className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-['Bebas_Neue'] text-base flex items-center gap-2">
                    <Film className="w-3.5 h-3.5 text-yellow-400" />
                    ULTIMI FILM AL CINEMA
                  </h3>
                  <div className="flex items-center gap-1.5">
                    <SectionSortMenu
                      value={sortRecentFilms}
                      onChange={setSortRecentFilms}
                      options={DEFAULT_SORT_OPTIONS}
                      testId="sort-recent-films"
                    />
                    <Button variant="ghost" size="sm" onClick={() => navigate('/social')} className="h-5 text-[9px] text-purple-400 hover:text-purple-300 px-1.5">
                      CineBoard <ChevronRight className="w-2.5 h-2.5 ml-0.5" />
                    </Button>
                  </div>
                </div>
                {(aBreveCinema.length > 0 || recentReleases.length > 0) ? (
                  <div className="flex overflow-x-auto gap-2 pb-1" style={{ scrollbarWidth: 'none' }}>
                    {/* Post-La Prima films awaiting release (dimmed + orange pulsing border).
                        Hide A-BREVE card when the same film is ALREADY in theaters (in recentReleases
                        with status=in_theaters) to avoid duplicate. Keep it visible while the film is
                        still in La Prima / not yet released. */}
                    {aBreveCinema
                      .filter(ab => !recentReleases.some(r =>
                        (r.source_project_id === ab.film_id || r.id === ab.film_id) &&
                        r.status === 'in_theaters'
                      ))
                      .map(film => (
                      <div key={`abreve-${film.film_id}`} className="flex-shrink-0 w-[72px] cursor-pointer group" onClick={() => {
                        if (film.owner_user_id && user?.id && film.owner_user_id === user.id) {
                          window.dispatchEvent(new CustomEvent('open-film-actions', { detail: { film: { ...film, id: film.film_id } } }));
                        } else {
                          navigate(`/films/${film.film_id}`);
                        }
                      }} data-testid={`a-breve-cinema-${film.film_id}`}>
                        <div className="aspect-[2/3] relative rounded-lg overflow-hidden border-2 border-orange-500/70 animate-pulse-border-orange">
                          {film.poster_url ? (
                            <img src={posterSrc(film.poster_url)} alt={film.title} className="w-full h-full object-cover opacity-55 grayscale-[30%] group-hover:scale-105 active:scale-110 transition-transform" loading="lazy"
                              onError={(e) => { e.target.style.display = 'none'; }} />
                          ) : (
                            <div className="w-full h-full bg-black" />
                          )}
                          {film.from_purchased_screenplay && (
                            <PurchasedScreenplayBadge mode={film.purchased_screenplay_mode}
                                                      source={film.purchased_screenplay_source}
                                                      size="sm" />
                          )}
                          <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/50 to-black/85" />
                          <div className="absolute inset-0 flex flex-col items-center justify-center px-1 text-center">
                            <div className="status-pulse-glow text-orange-300">
                              <p className="text-[6px] font-bold tracking-wider uppercase leading-none">A breve</p>
                              <p className="text-[7px] font-black text-orange-200 truncate uppercase w-full leading-tight mt-0.5">{film.a_breve_scope}</p>
                            </div>
                          </div>
                        </div>
                        <p className="text-[7px] font-semibold truncate mt-0.5 text-gray-300">{film.title}</p>
                        <p className="text-[6px] text-gray-500 truncate">{film.owner_nickname}</p>
                      </div>
                    ))}
                    {sortItems(recentReleases, sortRecentFilms).slice(0, 10).map(film => (
                      <div key={film.id} className="flex-shrink-0 w-[72px] cursor-pointer group" onClick={() => {
                        if (film.user_id && user?.id && film.user_id === user.id) {
                          window.dispatchEvent(new CustomEvent('open-film-actions', { detail: { film } }));
                        } else {
                          navigate(`/films/${film.id}`);
                        }
                      }} data-testid={`recent-film-${film.id}`}>
                        <div className={`aspect-[2/3] relative rounded-lg overflow-hidden ${film.status === 'in_theaters' ? 'border-2 border-emerald-500/50' : ''}`} style={{ boxShadow: film.status === 'premiere_live' ? '0 0 8px rgba(212,175,55,0.3)' : film.status === 'in_theaters' ? '0 0 8px rgba(80,220,110,0.35)' : 'none' }}>
                          <MasterpieceBadge isMasterpiece={film.is_masterpiece} size="xs" />
                          {film.from_purchased_screenplay && (
                            <PurchasedScreenplayBadge mode={film.purchased_screenplay_mode}
                                                      source={film.purchased_screenplay_source}
                                                      size="sm" />
                          )}
                          <img src={posterSrc(film.poster_url)} alt={film.title} className="w-full h-full object-cover group-hover:scale-105 active:scale-110 transition-transform" loading="lazy" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
                          {/* Status badge — LIVE pulse for in_theaters */}
                          {film.status === 'in_theaters' && (
                            <div className="absolute top-0.5 right-0.5 flex items-center gap-0.5 bg-black/70 rounded px-1 py-0.5">
                              <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                              <span className="text-[5px] font-bold text-green-400">LIVE</span>
                            </div>
                          )}
                          {film.status && film.status !== 'released' && film.status !== 'completed' && (
                            <div className={`status-pulse-glow absolute bottom-0 inset-x-0 py-0.5 flex items-center justify-center gap-0.5 text-[5px] font-bold tracking-wider ${
                              film.status === 'premiere_live' ? 'bg-amber-600/90 text-amber-100' :
                              film.status === 'in_theaters' ? 'bg-green-600/90 text-green-100' :
                              film.status === 'lampo_ready' ? 'bg-amber-500/90 text-amber-50' :
                              film.status === 'lampo_scheduled' ? 'bg-orange-500/90 text-orange-50' :
                              'bg-blue-600/80 text-blue-100'
                            }`}>
                              <span>
                                {film.status === 'premiere_live' ? 'LA PRIMA' :
                                 film.status === 'in_theaters' ? 'AL CINEMA' :
                                 film.status === 'lampo_ready' ? '⚡ LAMPO! · A BREVE AL CINEMA' :
                                 film.status === 'lampo_scheduled' ? `⚡ LAMPO! · DAL ${new Date(film.scheduled_release_at || film.released_at).toLocaleDateString('it-IT', {day:'2-digit', month:'2-digit'})}` :
                                 'IN USCITA'}
                              </span>
                            </div>
                          )}
                          {film.status === 'in_theaters' && (
                            <AttendanceTrendBadge trend={film.attendance_trend} status={film.status} className="absolute bottom-0.5 right-0.5" />
                          )}
                          {film.virtual_likes > 0 && (
                            <div className="absolute top-0.5 left-0.5 bg-black/70 rounded px-0.5 py-0.5 flex items-center gap-0.5">
                              <Heart className="w-1.5 h-1.5 text-pink-400 fill-pink-400" />
                              <span className="text-[6px] text-pink-300">{film.virtual_likes}</span>
                            </div>
                          )}
                          <ProducerBadge
                            producerNickname={film.producer_nickname}
                            producerId={film.user_id}
                            currentUserId={user?.id}
                            variant="bottom-left"
                            size="xs"
                          />
                          <LampoLightning item={film} variant="bottom-left" size="xs" />
                          <TvRightsBadge item={film} onClick={(it) => setRightsModalContent({ ...it, type: 'film' })} position="bottom-right" />
                        </div>
                        <p className="text-[7px] font-semibold truncate mt-0.5">{film.title}</p>
                        <p className="text-[6px] text-gray-500 truncate">{film.producer_house || film.producer_nickname}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <Film className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                    <p className="text-[9px] text-gray-600">Nessun film al cinema</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 5. Prossimamente SERIE TV */}
          <div className="mb-4 rounded-xl glow-blue" data-testid="dashboard-coming-soon-series">
            <ComingSoonSection compact filterType="tv_series" sectionTitle="PROSSIMAMENTE SERIE TV" />
          </div>

          {/* 5b. Prossimamente V3 Serie/Anime */}
          <ProssimamenteV3Section onItemClick={(item) => {
            // I Film TV puntano al modal Film, non al modal Serie
            if (item?.type === 'tv_movie' || item?.is_tv_movie) {
              setSelectedFilmId(item.id);
            } else {
              setProssimamenteDetailId(item?.id || item);
            }
          }} />

          {/* 6. Ultimi Aggiornamenti SERIE TV */}
          <div className="mb-4 rounded-xl glow-purple" data-testid="recent-releases-series">
            <Card className="bg-gradient-to-r from-blue-500/10 to-cyan-500/5 border border-blue-500/20">
              <CardContent className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-['Bebas_Neue'] text-base flex items-center gap-2">
                    <Tv className="w-3.5 h-3.5 text-blue-400" />
                    ULTIMI AGGIORNAMENTI SERIE TV
                  </h3>
                  <div className="flex items-center gap-1.5">
                    <SectionSortMenu
                      value={sortRecentSeries}
                      onChange={setSortRecentSeries}
                      options={DEFAULT_SORT_OPTIONS}
                      testId="sort-recent-series"
                    />
                    <Button variant="ghost" size="sm" onClick={() => navigate('/films?view=series')} className="h-5 text-[9px] text-blue-400 hover:text-blue-300 px-1.5">
                      Vedi <ChevronRight className="w-2.5 h-2.5 ml-0.5" />
                    </Button>
                  </div>
                </div>
                {mySeries.length > 0 ? (
                  <div className="flex overflow-x-auto gap-2 pb-1" style={{ scrollbarWidth: 'none' }}>
                    {sortItems(mySeries, sortRecentSeries).slice(0, 10).map(s => (
                      <div key={s.id} className="flex-shrink-0 w-[72px] cursor-pointer group" onClick={() => navigate(`/series/${s.id}`)} data-testid={`recent-series-${s.id}`}>
                        <div className="aspect-[2/3] relative rounded-lg overflow-hidden">
                          {s.poster_url ? (
                            <img src={posterSrc(s.poster_url)} alt={s.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" />
                          ) : (
                            <div className="w-full h-full bg-blue-500/10 flex items-center justify-center"><Tv className="w-5 h-5 text-blue-400/30" /></div>
                          )}
                          <Badge className={`absolute top-0.5 right-0.5 text-[5px] px-0.5 py-0 leading-tight ${s.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'}`}>
                            {s.status === 'completed' ? 'DONE' : s.status}
                          </Badge>
                          <ProducerBadge
                            producerNickname={s.producer_nickname}
                            producerId={s.user_id}
                            currentUserId={user?.id}
                            variant="bottom-left"
                            size="xs"
                          />
                          <LampoLightning item={s} variant="bottom-left" size="xs" />
                          <TvRightsBadge item={s} onClick={(it) => setRightsModalContent(it)} position="bottom-right" />
                        </div>
                        <p className="text-[7px] font-semibold truncate mt-0.5">{s.title}</p>
                        {(s.producer_house || s.producer_nickname) && <p className="text-[6px] text-gray-500 truncate">{s.producer_house || s.producer_nickname}</p>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[10px] text-gray-500 text-center py-3">Nessuna serie TV ancora</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 7. Prossimamente ANIME */}
          <div className="mb-4 rounded-xl glow-blue" data-testid="dashboard-coming-soon-anime">
            <ComingSoonSection compact filterType="anime" sectionTitle="PROSSIMAMENTE ANIME" />
          </div>

          {/* 8. Ultimi Aggiornamenti ANIME */}
          <div className="mb-4 rounded-xl glow-purple" data-testid="recent-releases-anime">
            <Card className="bg-gradient-to-r from-orange-500/10 to-amber-500/5 border border-orange-500/20">
              <CardContent className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-['Bebas_Neue'] text-base flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-orange-400" />
                    ULTIMI AGGIORNAMENTI ANIME
                  </h3>
                  <div className="flex items-center gap-1.5">
                    <SectionSortMenu
                      value={sortRecentAnime}
                      onChange={setSortRecentAnime}
                      options={DEFAULT_SORT_OPTIONS}
                      testId="sort-recent-anime"
                    />
                    <Button variant="ghost" size="sm" onClick={() => navigate('/films?view=anime')} className="h-5 text-[9px] text-orange-400 hover:text-orange-300 px-1.5">
                      Vedi <ChevronRight className="w-2.5 h-2.5 ml-0.5" />
                    </Button>
                  </div>
                </div>
                {myAnime.length > 0 ? (
                  <div className="flex overflow-x-auto gap-2 pb-1" style={{ scrollbarWidth: 'none' }}>
                    {sortItems(myAnime, sortRecentAnime).slice(0, 10).map(a => (
                      <div key={a.id} className="flex-shrink-0 w-[72px] cursor-pointer group" onClick={() => navigate(`/series/${a.id}`)} data-testid={`recent-anime-${a.id}`}>
                        <div className="aspect-[2/3] relative rounded-lg overflow-hidden">
                          {a.poster_url ? (
                            <img src={posterSrc(a.poster_url)} alt={a.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" />
                          ) : (
                            <div className="w-full h-full bg-orange-500/10 flex items-center justify-center"><Sparkles className="w-5 h-5 text-orange-400/30" /></div>
                          )}
                          <Badge className={`absolute top-0.5 right-0.5 text-[5px] px-0.5 py-0 leading-tight ${a.status === 'completed' ? 'bg-green-500' : 'bg-orange-500'}`}>
                            {a.status === 'completed' ? 'DONE' : a.status}
                          </Badge>
                          <ProducerBadge
                            producerNickname={a.producer_nickname}
                            producerId={a.user_id}
                            currentUserId={user?.id}
                            variant="bottom-left"
                            size="xs"
                          />
                          <LampoLightning item={a} variant="bottom-left" size="xs" />
                          <TvRightsBadge item={a} onClick={(it) => setRightsModalContent(it)} position="bottom-right" />
                        </div>
                        <p className="text-[7px] font-semibold truncate mt-0.5">{a.title}</p>
                        {(a.producer_house || a.producer_nickname) && <p className="text-[6px] text-gray-500 truncate">{a.producer_house || a.producer_nickname}</p>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[10px] text-gray-500 text-center py-3">Nessun anime ancora</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Old-style Action Grid (Foto 2) — accessible from other triggers */}
          {showActionGrid && (
            <div className="mb-6 space-y-2" data-testid="action-grid">
              {/* PRODUCI! - full width */}
              <button
                className="w-full flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-yellow-500/20 to-amber-500/10 border border-yellow-500/30 active:scale-[0.98] transition-transform"
                onClick={() => { setShowActionGrid(false); openProductionMenu(true); }}
                data-testid="action-produci"
              >
                <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center flex-shrink-0">
                  <Clapperboard className="w-5 h-5 text-yellow-400" />
                </div>
                <div className="text-left">
                  <p className="font-['Bebas_Neue'] text-base text-yellow-400">PRODUCI!</p>
                  <p className="text-[10px] text-gray-400">Nuova produzione</p>
                </div>
              </button>

              {/* 2x2 grid */}
              <div className="grid grid-cols-2 gap-2">
                <ActionCard icon={<Store className="w-4 h-4 text-orange-400" />} title="MERCATO" subtitle="Film scartati" color="orange" onClick={() => { setShowActionGrid(false); navigate('/marketplace'); }} testId="action-mercato" />
                <ActionCard icon={<Pen className="w-4 h-4 text-green-400" />} title="SCENEGGIATURE" subtitle="Trame pronte" color="green" onClick={() => { setShowActionGrid(false); navigate('/emerging-screenplays'); }} testId="action-sceneggiature" />
                <ActionCard icon={<Trophy className="w-4 h-4 text-cyan-400" />} title="CONTEST" subtitle="Guadagna CinePass" color="cyan" badge={contestCount > 0 ? contestCount : null} onClick={() => { setShowActionGrid(false); navigate('/games'); }} testId="action-contest" />
                <ActionCard icon={<Gamepad2 className="w-4 h-4 text-blue-400" />} title="MINIGIOCHI + SFIDE" subtitle="Gioca e sfida!" color="blue" onClick={() => { setShowActionGrid(false); navigate('/minigiochi'); }} testId="action-minigiochi" />
                <ActionCard icon={<Target className="w-4 h-4 text-red-400" />} title="ARENA" subtitle={`${arenaActions} azioni`} color="red" badge={arenaActions > 0 ? arenaActions : null} onClick={() => { setShowActionGrid(false); navigate('/pvp-arena'); }} testId="action-arena" />
                <ActionCard icon={<Award className="w-4 h-4 text-pink-400" />} title="FESTIVAL" subtitle="Premi cinema" color="pink" onClick={() => { setShowActionGrid(false); navigate('/festivals'); }} testId="action-festival" />
              </div>

              {/* LE MIE TV! - full width */}
              <button
                className="w-full flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-red-500/15 to-rose-500/5 border border-red-500/20 active:scale-[0.98] transition-transform"
                onClick={() => { setShowActionGrid(false); navigate('/my-tv'); }}
                data-testid="action-le-mie-tv"
              >
                <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center flex-shrink-0">
                  <Radio className="w-5 h-5 text-red-400" />
                </div>
                <div className="text-left">
                  <p className="font-['Bebas_Neue'] text-base text-red-400">LE MIE TV!</p>
                  <p className="text-[10px] text-gray-400">{tvStationCount} emittente{tvStationCount !== 1 ? 'i' : ''} televisiv{tvStationCount !== 1 ? 'e' : 'a'}</p>
                </div>
              </button>
            </div>
          )}

          {/* ===== GAMEPLAY DIALOGS (preserved from original) ===== */}

          {/* Shooting Dialog */}
          <Dialog open={showShootingDialog} onOpenChange={setShowShootingDialog}>
            <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
                  <Clapperboard className="w-5 h-5 text-red-400" /> CIAK, SI GIRA!
                  {shootingFilms.length > 0 && <Badge className="bg-red-500 text-white text-xs">{shootingFilms.length}</Badge>}
                </DialogTitle>
              </DialogHeader>
              {shootingFilms.length > 0 ? (
                <div className="space-y-2">
                  {shootingFilms.map(sf => {
                    const progress = sf.shooting_days > 0 ? (sf.shooting_days_completed / sf.shooting_days) * 100 : 0;
                    const lastEvent = sf.shooting_events?.[sf.shooting_events.length - 1];
                    return (
                      <div key={sf.id} className="bg-black/30 rounded-lg p-2 border border-white/5" data-testid={`shooting-dialog-film-${sf.id}`}>
                        <div className="flex items-center gap-2 mb-1.5">
                          {sf.poster_url && <img src={posterSrc(sf.poster_url)} alt="" className="w-8 h-12 rounded object-cover" loading="lazy" />}
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold truncate">{sf.title}</p>
                            <p className="text-[10px] text-gray-500">Giorno {sf.shooting_days_completed}/{sf.shooting_days} | Bonus: +{sf.shooting_bonus}%</p>
                          </div>
                          <Button size="sm" variant="outline" className="h-6 text-[10px] px-2 border-red-500/30 text-red-300 hover:bg-red-500/10" onClick={() => handleEndShootingEarly(sf.id)} disabled={endingShootingEarly} data-testid={`end-early-dialog-${sf.id}`}>
                            {endingShootingEarly ? '...' : `Chiudi (${sf.early_end_cinepass_cost} CP)`}
                          </Button>
                        </div>
                        <div className="w-full bg-gray-800 rounded-full h-1.5 mb-1">
                          <div className="bg-gradient-to-r from-red-500 to-amber-500 h-1.5 rounded-full transition-all" style={{ width: `${progress}%` }} />
                        </div>
                        {lastEvent && (
                          <p className="text-[9px] text-gray-400">
                            Ultimo evento: <span className={lastEvent.bonus > 0 ? 'text-green-400' : lastEvent.bonus < 0 ? 'text-red-400' : 'text-gray-400'}>
                              {lastEvent.name} ({lastEvent.bonus > 0 ? '+' : ''}{lastEvent.bonus}%)
                            </span>
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-6">
                  <Clapperboard className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-500 text-sm">Nessun film in riprese.</p>
                </div>
              )}
            </DialogContent>
          </Dialog>

          {/* Release Film Popup */}
          <Dialog open={!!releasePopup} onOpenChange={() => setReleasePopup(null)}>
            <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[85vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
                  <Globe className="w-5 h-5 text-amber-400" /> DISTRIBUZIONE FILM
                </DialogTitle>
                <DialogDescription className="text-gray-400 text-xs">Scegli dove far uscire il tuo film</DialogDescription>
              </DialogHeader>
              {releasePopup && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3 bg-black/30 rounded-lg p-3 border border-white/5">
                    <img src={posterSrc(releasePopup.poster_url)} alt={releasePopup.title} className="w-12 h-16 object-cover rounded" />
                    <div>
                      <p className="font-semibold text-sm">{releasePopup.title}</p>
                      <p className="text-xs text-gray-400">Qualità: {(releasePopup.quality_score || 0).toFixed(0)}%</p>
                    </div>
                  </div>
                  <div>
                    <Label className="text-xs mb-2 block">Zona di distribuzione</Label>
                    <RadioGroup value={selectedZone} onValueChange={setSelectedZone} className="space-y-2">
                      {distConfig && Object.entries(distConfig.zones).map(([key, zone]) => {
                        const cost = getZoneCost();
                        return (
                          <div key={key} className={`flex items-center gap-3 p-2 rounded-lg border transition-colors cursor-pointer ${selectedZone === key ? 'border-amber-500/50 bg-amber-500/10' : 'border-white/5 bg-black/20 hover:border-white/15'}`} onClick={() => setSelectedZone(key)}>
                            <RadioGroupItem value={key} id={key} />
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                {key === 'national' && <MapPin className="w-3 h-3 text-green-400" />}
                                {key === 'continental' && <Globe className="w-3 h-3 text-blue-400" />}
                                {key === 'world' && <Globe className="w-3 h-3 text-purple-400" />}
                                <span className="text-sm font-medium">{zone.name}</span>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-yellow-400">${cost.funds.toLocaleString()}</p>
                              <p className="text-[10px] text-cyan-400">{cost.cinepass} CP</p>
                            </div>
                          </div>
                        );
                      })}
                    </RadioGroup>
                  </div>
                  {selectedZone === 'continental' && distConfig && (
                    <div>
                      <Label className="text-xs mb-1 block">Continente</Label>
                      <Select value={selectedContinent} onValueChange={setSelectedContinent}>
                        <SelectTrigger className="bg-black/30 border-white/10 h-8 text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent className="bg-[#1A1A1A] border-white/10">
                          {Object.entries(distConfig.continents).map(([key, name]) => (
                            <SelectItem key={key} value={key} className="text-xs">{name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  {releasePopup?.status === 'pending_release' && (
                    <div className="bg-orange-500/10 rounded-lg p-2 border border-orange-500/20">
                      <p className="text-[10px] text-orange-400 font-medium">Rilascio diretto: costo -30% ma qualità capped a 5.8 IMDb</p>
                    </div>
                  )}
                  <div className="bg-green-500/10 rounded-lg p-2 border border-green-500/20">
                    <div className="flex items-center gap-2 mb-1"><TrendingUp className="w-3 h-3 text-green-400" /><span className="text-xs font-medium text-green-400">Stima incasso giorno 1</span></div>
                    <p className="text-lg font-bold text-green-400">${((releasePopup.opening_day_revenue || 0) * (distConfig?.zones?.[selectedZone]?.revenue_multiplier || 1)).toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                  </div>
                  {hasStudio && releasePopup.status === 'pending_release' && (
                    <Button variant="outline" size="sm" className="w-full border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10" onClick={() => { setReleasePopup(null); navigate('/infrastructure'); }}>
                      <Building className="w-4 h-4 mr-2" /> Porta in Studio di Produzione
                    </Button>
                  )}
                  {releasePopup.status === 'pending_release' && (
                    <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 space-y-2" data-testid="shooting-option">
                      <div className="flex items-center gap-2"><Clapperboard className="w-4 h-4 text-red-400" /><span className="text-sm font-semibold text-red-300">Inizia le Riprese</span></div>
                      <div className="flex items-center gap-2">
                        <label className="text-xs text-gray-400 shrink-0">Giorni:</label>
                        <input type="range" min="1" max="10" value={shootingDays} onChange={(e) => setShootingDays(parseInt(e.target.value))} className="flex-1 h-1.5 accent-red-500" data-testid="shooting-days-slider" />
                        <span className="text-sm font-bold text-white w-6 text-center">{shootingDays}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-1 text-center text-[10px]">
                        <div className="bg-black/30 rounded p-1"><p className="text-gray-500">Bonus</p><p className="text-green-400 font-bold">+{shootingConfig?.bonus_curve?.[shootingDays] || (shootingDays * 4)}%</p></div>
                        <div className="bg-black/30 rounded p-1"><p className="text-gray-500">Costo</p><p className="text-yellow-400 font-bold">${getShootingCost(releasePopup, shootingDays).toLocaleString()}</p></div>
                        <div className="bg-black/30 rounded p-1"><p className="text-gray-500">Durata</p><p className="text-white font-bold">{shootingDays}g</p></div>
                      </div>
                      <Button size="sm" className="w-full bg-red-500/20 text-red-300 hover:bg-red-500/30" onClick={() => { setShootingPopup({ ...releasePopup, _directorImg: Math.random() < 0.5 ? '/images/shooting/director_female.jpeg' : '/images/shooting/director_male.jpeg' }); setReleasePopup(null); }} data-testid="start-shooting-from-release">
                        <Clapperboard className="w-4 h-4 mr-2" /> Inizia le Riprese ({shootingDays} giorni)
                      </Button>
                    </div>
                  )}
                </div>
              )}
              <DialogFooter className="gap-2">
                <Button variant="outline" size="sm" onClick={() => setReleasePopup(null)} className="border-white/10">Annulla</Button>
                <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-black font-bold" onClick={handleRelease} disabled={releasing} data-testid="confirm-release-btn">
                  {releasing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Rilascia nelle Sale'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Release Success */}
          <Dialog open={!!releaseSuccess} onOpenChange={(open) => { if (!open) setReleaseSuccess(null); }}>
            <DialogContent className="bg-[#0a0a0a] border-amber-500/30 max-w-sm p-0 overflow-hidden">
              <div className="relative">
                <img src="https://customer-assets.emergentagent.com/job_0f5ad56a-c26f-4f77-9bc6-853ae85e3ca2/artifacts/69t544vn_IMG_0554.jpeg" alt="CineWorld Cinema" className="w-full h-44 object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent" />
                <div className="absolute bottom-2 left-3 right-3"><p className="text-amber-400 font-['Bebas_Neue'] text-2xl leading-tight">IN SALA ORA!</p></div>
              </div>
              {releaseSuccess && (
                <div className="px-4 pb-4 space-y-3">
                  <div className="flex items-center gap-3">
                    {releaseSuccess.poster && <img src={releaseSuccess.poster} alt="" className="w-12 h-16 rounded object-cover border border-white/10" />}
                    <div><p className="font-bold text-base">{releaseSuccess.title}</p><p className="text-xs text-amber-400">Distribuzione {releaseSuccess.zone}</p></div>
                  </div>
                  {(releaseSuccess.quality_score || releaseSuccess.imdb_rating) && (
                    <div className="flex gap-2">
                      {releaseSuccess.quality_score && (<div className="flex-1 bg-blue-500/10 border border-blue-500/20 rounded-lg p-2 text-center"><p className="text-[10px] text-gray-400">Qualita</p><p className="text-lg font-bold text-blue-400">{releaseSuccess.quality_score.toFixed(0)}%</p></div>)}
                      {releaseSuccess.imdb_rating && (<div className="flex-1 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-2 text-center"><p className="text-[10px] text-gray-400">IMDB</p><p className="text-lg font-bold text-yellow-400">{releaseSuccess.imdb_rating.toFixed(1)}</p></div>)}
                      {releaseSuccess.tier && (<div className="flex-1 bg-purple-500/10 border border-purple-500/20 rounded-lg p-2 text-center"><p className="text-[10px] text-gray-400">Tier</p><p className="text-lg font-bold text-purple-400">{releaseSuccess.tier}</p></div>)}
                    </div>
                  )}
                  {releaseSuccess.events?.length > 0 && (
                    <div className="space-y-1.5">
                      {releaseSuccess.events.map((ev, i) => (
                        <div key={i} className="bg-white/5 rounded-lg p-2 flex items-center gap-2">
                          <Sparkles className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                          <div><p className="text-[11px] font-semibold">{ev.headline}</p>{ev.quality_impact && <p className="text-[9px] text-green-400">+{ev.quality_impact} qualita</p>}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {releaseSuccess.critics?.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-[10px] text-gray-500 uppercase">Recensioni</p>
                      {releaseSuccess.critics.slice(0, 2).map((c, i) => (
                        <div key={i} className="bg-white/5 rounded p-1.5 text-[10px]">
                          <span className="text-gray-400">{c.outlet}:</span> <span className={c.score >= 7 ? 'text-green-400' : c.score >= 5 ? 'text-yellow-400' : 'text-red-400'}>{c.score}/10</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-center">
                    <p className="text-[10px] text-gray-400 mb-0.5">Incasso Giorno 1</p>
                    <p className="text-2xl font-bold text-green-400">${releaseSuccess.revenue?.toLocaleString()}</p>
                  </div>
                  <Button className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold" onClick={() => setReleaseSuccess(null)} data-testid="close-release-success">Fantastico!</Button>
                </div>
              )}
            </DialogContent>
          </Dialog>

          {/* Shooting Confirmation Dialog */}
          <Dialog open={!!shootingPopup} onOpenChange={(open) => { if (!open) setShootingPopup(null); }}>
            <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-sm">
              <DialogHeader><DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2"><Clapperboard className="w-5 h-5 text-red-400" /> CIAK, SI GIRA!</DialogTitle></DialogHeader>
              {shootingPopup && (
                <div className="space-y-3">
                  <div className="relative rounded-lg overflow-hidden">
                    <img src={shootingPopup._directorImg || '/images/shooting/director_female.jpeg'} alt="Director on set" className="w-full h-40 object-cover rounded-lg" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                    <div className="absolute bottom-2 left-3 right-3"><p className="font-['Bebas_Neue'] text-lg text-white drop-shadow-lg">{shootingPopup.title}</p><p className="text-xs text-gray-300">Qualità: {(shootingPopup.quality_score || 0).toFixed(0)}%</p></div>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-gray-400 shrink-0">Giorni di riprese:</label>
                    <input type="range" min="1" max="10" value={shootingDays} onChange={(e) => setShootingDays(parseInt(e.target.value))} className="flex-1 h-1.5 accent-red-500" data-testid="shooting-confirm-slider" />
                    <span className="text-lg font-bold text-white w-6 text-center">{shootingDays}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div className="bg-green-500/10 rounded-lg p-2 border border-green-500/20"><p className="text-[10px] text-gray-400">Bonus qualità</p><p className="text-lg font-bold text-green-400">+{shootingConfig?.bonus_curve?.[shootingDays] || (shootingDays * 4)}%</p></div>
                    <div className="bg-yellow-500/10 rounded-lg p-2 border border-yellow-500/20"><p className="text-[10px] text-gray-400">Costo riprese</p><p className="text-lg font-bold text-yellow-400">${getShootingCost(shootingPopup, shootingDays).toLocaleString()}</p></div>
                  </div>
                  <p className="text-[10px] text-gray-500 text-center">Ogni giorno ci saranno eventi casuali che influenzano il bonus!</p>
                </div>
              )}
              <DialogFooter className="gap-2">
                <Button variant="outline" size="sm" onClick={() => setShootingPopup(null)} className="border-white/10">Annulla</Button>
                <Button size="sm" className="bg-red-500 hover:bg-red-600 text-white font-bold" onClick={handleStartShooting} disabled={startingShooting} data-testid="confirm-shooting-btn">
                  {startingShooting ? <Loader2 className="w-4 h-4 animate-spin" /> : `Inizia Riprese (${shootingDays}g)`}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

        </div>
      </div>

      {/* V3 Film Detail Modal */}
      {selectedFilmId && (
        <Suspense fallback={null}>
          <FilmDetailV3 filmId={selectedFilmId} onClose={() => setSelectedFilmId(null)} />
        </Suspense>
      )}

      {/* Prossimamente V3 Serie/Anime Detail Modal */}
      <ProssimamenteDetailModal
        open={!!prossimamenteDetailId}
        onClose={() => setProssimamenteDetailId(null)}
        seriesId={prossimamenteDetailId}
      />

      {/* TV Rights Modal — apre il market in vista panoramica per mostrare contratto attivo */}
      {rightsModalContent && (
        <TvMarketModal
          open={!!rightsModalContent}
          onClose={() => setRightsModalContent(null)}
          content={rightsModalContent}
        />
      )}
    </>
  );
};

export default Dashboard;

function ActionCard({ icon, title, subtitle, color, badge, onClick, testId }) {
  return (
    <button
      className={`flex flex-col items-center justify-center gap-1 p-3 rounded-xl border border-${color}-500/20 bg-${color}-500/5 active:scale-[0.95] transition-transform relative`}
      onClick={onClick}
      data-testid={testId}
    >
      {badge && (
        <span className={`absolute top-1 right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-${color}-500 text-white text-[8px] font-bold flex items-center justify-center`}>
          {badge}
        </span>
      )}
      <div className={`w-8 h-8 rounded-lg bg-${color}-500/15 flex items-center justify-center`}>
        {icon}
      </div>
      <p className={`font-['Bebas_Neue'] text-xs text-${color}-400 leading-tight text-center`}>{title}</p>
      <p className="text-[8px] text-gray-500 leading-tight">{subtitle}</p>
    </button>
  );
}
