// CineWorld - La Mia TV (My TV Dashboard)
// Manage all series/anime: airing, completed, catalog, pipeline
// Broadcast episodes, renew seasons, send to TV

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Slider } from '../components/ui/slider';
import {
  Radio, Tv, Sparkles, Film, Loader2, Play, RefreshCw, Send,
  Star, Eye, ChevronRight, Clock, Trophy, BarChart3, Zap,
  CheckCircle, Lock, Unlock, ArrowRight, Archive
} from 'lucide-react';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300';
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};

const TABS = [
  { id: 'airing', label: 'In Onda', icon: Radio, color: 'text-green-400' },
  { id: 'completed', label: 'Completate', icon: Trophy, color: 'text-cyan-400' },
  { id: 'catalog', label: 'Catalogo', icon: Archive, color: 'text-amber-400' },
  { id: 'pipeline', label: 'In Produzione', icon: Film, color: 'text-purple-400' },
];

export default function EmittenteTVPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('airing');
  const [broadcasting, setBroadcasting] = useState(null);
  const [renewModal, setRenewModal] = useState(null);
  const [renewCp, setRenewCp] = useState(0);
  const [renewLoading, setRenewLoading] = useState(false);
  const [sendingToTv, setSendingToTv] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('/pipeline-series-v3/tv/my-dashboard');
      setData(res.data);
      // Auto-select first non-empty tab
      if (!res.data.airing?.length && res.data.completed?.length) setActiveTab('completed');
      else if (!res.data.airing?.length && !res.data.completed?.length && res.data.catalog?.length) setActiveTab('catalog');
      else if (!res.data.airing?.length && !res.data.completed?.length && !res.data.catalog?.length && res.data.pipeline?.length) setActiveTab('pipeline');
    } catch {
      toast.error('Errore caricamento dati TV');
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleBroadcast = async (seriesId) => {
    setBroadcasting(seriesId);
    try {
      const res = await api.post(`/pipeline-series-v3/tv/broadcast-episode/${seriesId}`);
      const ep = res.data.episode;
      toast.success(
        `Ep. ${ep.number} "${ep.title}" trasmesso! CWSv: ${ep.cwsv_display}`,
        { duration: 4000 }
      );
      if (res.data.all_aired) {
        toast.info('Tutti gli episodi trasmessi! Serie completata.', { duration: 3000 });
      }
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore trasmissione');
    } finally {
      setBroadcasting(null);
    }
  };

  const handleRenew = async () => {
    if (!renewModal) return;
    setRenewLoading(true);
    try {
      const res = await api.post(`/pipeline-series-v3/series/${renewModal.id}/renew-season`, {
        speedup_cp: renewCp,
      });
      toast.success(
        `Stagione ${res.data.season_number} creata! ${res.data.lock_days > 0 ? `Lock: ${res.data.lock_days}g` : 'Subito disponibile!'}`,
        { duration: 4000 }
      );
      setRenewModal(null);
      setRenewCp(0);
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore rinnovo');
    } finally {
      setRenewLoading(false);
    }
  };

  const handleSendToTv = async (seriesId) => {
    setSendingToTv(seriesId);
    try {
      await api.post(`/pipeline-series-v3/tv/send-to-tv/${seriesId}`);
      toast.success('Serie inviata in TV!');
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore invio a TV');
    } finally {
      setSendingToTv(null);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center pt-16" data-testid="my-tv-loading">
      <Loader2 className="w-8 h-8 text-teal-400 animate-spin" />
    </div>
  );

  const stats = data?.stats || {};
  const totalContent = stats.airing_count + stats.completed_count + stats.catalog_count + stats.pipeline_count;
  const isEmpty = totalContent === 0;

  if (isEmpty) return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pt-16 pb-20 px-4" data-testid="my-tv-empty">
      <div className="max-w-md mx-auto text-center mt-16">
        <div className="w-20 h-20 rounded-full bg-teal-500/10 flex items-center justify-center mx-auto mb-4">
          <Tv className="w-10 h-10 text-teal-400" />
        </div>
        <h1 className="text-xl font-bold mb-2">La Mia TV</h1>
        <p className="text-gray-400 text-sm mb-6">
          Non hai ancora serie o anime. Crea una Serie TV o un Anime nella pipeline per iniziare!
        </p>
        <div className="flex gap-3 justify-center">
          <Button className="bg-blue-600 hover:bg-blue-700 text-sm" onClick={() => navigate('/create-series')} data-testid="my-tv-create-series">
            <Tv className="w-4 h-4 mr-1.5" /> Crea Serie TV
          </Button>
          <Button className="bg-orange-600 hover:bg-orange-700 text-sm" onClick={() => navigate('/create-anime')} data-testid="my-tv-create-anime">
            <Sparkles className="w-4 h-4 mr-1.5" /> Crea Anime
          </Button>
        </div>
      </div>
    </div>
  );

  const currentItems = activeTab === 'airing' ? (data?.airing || [])
    : activeTab === 'completed' ? (data?.completed || [])
    : activeTab === 'catalog' ? (data?.catalog || [])
    : (data?.pipeline || []);

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pt-16 pb-20" data-testid="my-tv-page">
      {/* Header */}
      <div className="px-4 pt-4 pb-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-lg bg-teal-500/15 flex items-center justify-center">
              <Tv className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold leading-tight">La Mia TV</h1>
              <p className="text-[10px] text-gray-500">Gestisci le tue Serie TV e Anime</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" className="h-8 text-xs border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
              onClick={() => navigate('/create-series')} data-testid="my-tv-new-series">
              <Tv className="w-3.5 h-3.5 mr-1" /> Serie TV
            </Button>
            <Button size="sm" variant="outline" className="h-8 text-xs border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
              onClick={() => navigate('/create-anime')} data-testid="my-tv-new-anime">
              <Sparkles className="w-3.5 h-3.5 mr-1" /> Anime
            </Button>
          </div>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-4 gap-2 mb-3">
          <StatCard label="In Onda" value={stats.airing_count} icon={<Radio className="w-3.5 h-3.5" />} color="text-green-400" bg="bg-green-500/10" />
          <StatCard label="Completate" value={stats.completed_count} icon={<Trophy className="w-3.5 h-3.5" />} color="text-cyan-400" bg="bg-cyan-500/10" />
          <StatCard label="Episodi" value={stats.total_episodes_aired} icon={<Play className="w-3.5 h-3.5" />} color="text-amber-400" bg="bg-amber-500/10" />
          <StatCard label="Incasso" value={formatRevenue(stats.total_revenue)} icon={<BarChart3 className="w-3.5 h-3.5" />} color="text-emerald-400" bg="bg-emerald-500/10" />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-[#111113] rounded-lg p-1">
          {TABS.map(tab => {
            const count = activeTab === tab.id ? currentItems.length : (
              tab.id === 'airing' ? data?.airing?.length :
              tab.id === 'completed' ? data?.completed?.length :
              tab.id === 'catalog' ? data?.catalog?.length :
              data?.pipeline?.length
            ) || 0;
            return (
              <button key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-1 py-2 rounded-md text-[11px] font-medium transition-all
                  ${activeTab === tab.id ? 'bg-[#1A1A1D] text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'}`}
                data-testid={`my-tv-tab-${tab.id}`}
              >
                <tab.icon className={`w-3.5 h-3.5 ${activeTab === tab.id ? tab.color : ''}`} />
                {tab.label}
                {count > 0 && <span className="text-[9px] ml-0.5 opacity-60">{count}</span>}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="px-4">
        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
            {currentItems.length === 0 ? (
              <EmptyTab tab={activeTab} />
            ) : (
              <div className="space-y-3">
                {currentItems.map((item) => (
                  activeTab === 'airing' ? (
                    <AiringCard key={item.id} series={item} onBroadcast={handleBroadcast} broadcasting={broadcasting} />
                  ) : activeTab === 'completed' ? (
                    <CompletedCard key={item.id} series={item} onRenew={() => { setRenewModal(item); setRenewCp(0); }} />
                  ) : activeTab === 'catalog' ? (
                    <CatalogCard key={item.id} series={item} onSendToTv={handleSendToTv} sending={sendingToTv} />
                  ) : (
                    <PipelineCard key={item.id} project={item} navigate={navigate} />
                  )
                ))}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Renew Season Modal */}
      <Dialog open={!!renewModal} onOpenChange={(o) => { if (!o) { setRenewModal(null); setRenewCp(0); } }}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-[380px] [&>button]:hidden" data-testid="renew-season-modal">
          <DialogHeader>
            <DialogTitle className="text-base flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-cyan-400" />
              Rinnovo Stagione
            </DialogTitle>
            <DialogDescription className="text-xs text-gray-400">
              {renewModal?.title} - S{(renewModal?.season_number || 1) + 1}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="bg-[#111113] rounded-lg p-3 border border-white/5">
              <p className="text-xs text-gray-400 mb-1">Velocizza con CinePass</p>
              <div className="flex items-center gap-3">
                <Slider
                  value={[renewCp]}
                  onValueChange={([v]) => setRenewCp(v)}
                  max={30}
                  step={1}
                  className="flex-1"
                />
                <Badge className="bg-amber-500/15 text-amber-400 border-0 text-xs min-w-[50px] justify-center">
                  {renewCp} CP
                </Badge>
              </div>
              <div className="flex justify-between mt-2 text-[10px] text-gray-500">
                <span>0 CP = 30 giorni</span>
                <span>15 CP = 15 giorni</span>
                <span>30 CP = subito</span>
              </div>
            </div>
            <div className="bg-cyan-500/5 rounded-lg p-3 border border-cyan-500/10">
              <div className="flex items-center gap-2 mb-1.5">
                {renewCp >= 30 ? <Unlock className="w-4 h-4 text-green-400" /> : <Lock className="w-4 h-4 text-amber-400" />}
                <span className="text-sm font-medium">
                  {renewCp >= 30 ? 'Disponibile subito' : renewCp >= 15 ? `Lock: ${Math.max(0, 30 - renewCp)} giorni` : `Lock: ${30 - renewCp} giorni`}
                </span>
              </div>
              <p className="text-[10px] text-gray-400">
                Il cast e il poster verranno ereditati dalla stagione precedente. Il CWSv base parte dal valore della S{renewModal?.season_number || 1} con variazione +-10%.
              </p>
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" className="text-xs border-white/10" onClick={() => setRenewModal(null)}>
              Annulla
            </Button>
            <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700 text-xs" onClick={handleRenew} disabled={renewLoading} data-testid="confirm-renew-btn">
              {renewLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <RefreshCw className="w-3.5 h-3.5 mr-1" />}
              Rinnova S{(renewModal?.season_number || 1) + 1}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}


/* ─── Sub-components ─── */

function StatCard({ label, value, icon, color, bg }) {
  return (
    <div className={`rounded-lg ${bg} border border-white/5 p-2.5 text-center`}>
      <div className={`${color} flex items-center justify-center mb-1`}>{icon}</div>
      <div className="text-sm font-bold">{value ?? 0}</div>
      <div className="text-[9px] text-gray-500">{label}</div>
    </div>
  );
}

function EmptyTab({ tab }) {
  const msgs = {
    airing: { icon: Radio, text: 'Nessuna serie in onda', sub: 'Rilascia una serie con "Prossimamente TV" per iniziare a trasmettere' },
    completed: { icon: Trophy, text: 'Nessuna serie completata', sub: 'Le serie i cui episodi sono stati tutti trasmessi appariranno qui' },
    catalog: { icon: Archive, text: 'Catalogo vuoto', sub: 'Le serie rilasciate senza "Prossimamente TV" finiscono qui' },
    pipeline: { icon: Film, text: 'Nessun progetto in corso', sub: 'Crea una nuova serie o anime per iniziare' },
  };
  const m = msgs[tab] || msgs.airing;
  return (
    <div className="text-center py-12" data-testid={`my-tv-empty-${tab}`}>
      <m.icon className="w-10 h-10 text-gray-700 mx-auto mb-3" />
      <p className="text-gray-400 text-sm mb-1">{m.text}</p>
      <p className="text-gray-600 text-[11px]">{m.sub}</p>
    </div>
  );
}

function AiringCard({ series, onBroadcast, broadcasting }) {
  const isAnime = series.type === 'anime';
  const aired = series.aired_episodes || 0;
  const total = series.total_episodes || 0;
  const progress = total > 0 ? (aired / total) * 100 : 0;
  const nextEp = series.next_episode;
  const cwsv = series.quality_score || series.cwsv_display || '?';
  const isBroadcasting = broadcasting === series.id;

  return (
    <Card className="bg-[#111113] border-white/5 overflow-hidden" data-testid={`airing-card-${series.id}`}>
      <CardContent className="p-0">
        <div className="flex">
          {/* Poster */}
          <div className="relative w-[90px] h-[130px] flex-shrink-0">
            <img src={posterSrc(series.poster_url)} alt="" className="w-full h-full object-cover" onError={e => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent to-[#111113]" />
            <Badge className={`absolute top-1.5 left-1.5 text-[8px] border-0 ${isAnime ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}>
              {isAnime ? 'ANIME' : 'SERIE TV'}
            </Badge>
          </div>

          {/* Info */}
          <div className="flex-1 p-3 flex flex-col justify-between min-w-0">
            <div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold truncate">{series.title}</h3>
                <Badge className="bg-green-500/15 text-green-400 border-0 text-[9px] flex-shrink-0">
                  <Radio className="w-2.5 h-2.5 mr-0.5" /> IN ONDA
                </Badge>
              </div>
              {series.genre_name && <p className="text-[10px] text-gray-500 mt-0.5">{series.genre_name} {series.season_number > 1 ? `- S${series.season_number}` : ''}</p>}
            </div>

            {/* Progress */}
            <div className="mt-2">
              <div className="flex justify-between text-[10px] text-gray-400 mb-1">
                <span>Episodi: {aired}/{total}</span>
                <span className="flex items-center gap-1">
                  <Star className="w-2.5 h-2.5 text-amber-400" />
                  CWSv {typeof cwsv === 'number' ? cwsv.toFixed(1) : cwsv}
                </span>
              </div>
              <div className="h-1.5 bg-[#1A1A1D] rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all" style={{ width: `${progress}%` }} />
              </div>
            </div>

            {/* Broadcast button */}
            {nextEp && (
              <Button
                size="sm"
                className="mt-2 h-8 text-[11px] bg-green-600 hover:bg-green-700 w-full"
                onClick={() => onBroadcast(series.id)}
                disabled={isBroadcasting}
                data-testid={`broadcast-btn-${series.id}`}
              >
                {isBroadcasting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Play className="w-3.5 h-3.5 mr-1" />}
                Trasmetti Ep. {nextEp.number}: "{nextEp.title}"
              </Button>
            )}
          </div>
        </div>

        {/* Episode list (last 3 revealed) */}
        <EpisodeList episodes={series.episodes} />
      </CardContent>
    </Card>
  );
}

function EpisodeList({ episodes }) {
  if (!episodes || episodes.length === 0) return null;
  const revealed = episodes.filter(e => e.revealed);
  if (revealed.length === 0) return null;
  const last3 = revealed.slice(-3).reverse();

  return (
    <div className="border-t border-white/5 px-3 py-2">
      <p className="text-[9px] text-gray-500 mb-1.5 uppercase tracking-wider">Ultimi episodi trasmessi</p>
      <div className="space-y-1">
        {last3.map(ep => (
          <div key={ep.number} className="flex items-center justify-between text-[10px]">
            <div className="flex items-center gap-1.5 text-gray-300">
              <CheckCircle className="w-3 h-3 text-green-500" />
              <span>Ep. {ep.number}</span>
              <span className="text-gray-500 truncate max-w-[140px]">{ep.title}</span>
            </div>
            <Badge className="bg-amber-500/10 text-amber-400 border-0 text-[9px]">
              {ep.cwsv_display || (ep.cwsv ? ep.cwsv.toFixed(1) : '?')}
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}

function CompletedCard({ series, onRenew }) {
  const isAnime = series.type === 'anime';
  const cwsv = series.quality_score || 0;

  return (
    <Card className="bg-[#111113] border-white/5 overflow-hidden" data-testid={`completed-card-${series.id}`}>
      <CardContent className="p-0">
        <div className="flex">
          <div className="relative w-[90px] h-[120px] flex-shrink-0">
            <img src={posterSrc(series.poster_url)} alt="" className="w-full h-full object-cover" onError={e => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent to-[#111113]" />
            <Badge className={`absolute top-1.5 left-1.5 text-[8px] border-0 ${isAnime ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}>
              {isAnime ? 'ANIME' : 'SERIE'}
            </Badge>
          </div>
          <div className="flex-1 p-3 flex flex-col justify-between min-w-0">
            <div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold truncate">{series.title}</h3>
                <Badge className="bg-cyan-500/15 text-cyan-400 border-0 text-[9px] flex-shrink-0">COMPLETATA</Badge>
              </div>
              <p className="text-[10px] text-gray-500 mt-0.5">
                {series.genre_name} - S{series.season_number || 1} - {series.total_episodes} ep.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-1.5 text-[10px] text-gray-400">
              <span className="flex items-center gap-0.5"><Star className="w-3 h-3 text-amber-400" /> {typeof cwsv === 'number' && cwsv <= 10 ? cwsv.toFixed(1) : cwsv}</span>
              {series.total_revenue > 0 && <span className="flex items-center gap-0.5"><BarChart3 className="w-3 h-3 text-emerald-400" /> ${formatRevenue(series.total_revenue)}</span>}
            </div>
            <div className="flex gap-2 mt-2">
              {series.has_renewal ? (
                <Badge className="bg-purple-500/15 text-purple-400 border-0 text-[10px]">
                  <RefreshCw className="w-3 h-3 mr-1" /> S{series.renewal_season} in produzione
                </Badge>
              ) : (
                <Button size="sm" className="h-7 text-[10px] bg-cyan-600 hover:bg-cyan-700" onClick={onRenew} data-testid={`renew-btn-${series.id}`}>
                  <RefreshCw className="w-3 h-3 mr-1" /> Rinnova S{(series.season_number || 1) + 1}
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function CatalogCard({ series, onSendToTv, sending }) {
  const isAnime = series.type === 'anime';
  const isSending = sending === series.id;

  return (
    <Card className="bg-[#111113] border-white/5 overflow-hidden" data-testid={`catalog-card-${series.id}`}>
      <CardContent className="p-0">
        <div className="flex">
          <div className="relative w-[90px] h-[110px] flex-shrink-0">
            <img src={posterSrc(series.poster_url)} alt="" className="w-full h-full object-cover" onError={e => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'; }} />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent to-[#111113]" />
          </div>
          <div className="flex-1 p-3 flex flex-col justify-between min-w-0">
            <div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold truncate">{series.title}</h3>
                <Badge className={`text-[8px] border-0 ${isAnime ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}>
                  {isAnime ? 'ANIME' : 'SERIE'}
                </Badge>
              </div>
              <p className="text-[10px] text-gray-500 mt-0.5">{series.genre_name} - {series.total_episodes} episodi</p>
            </div>
            <Button size="sm" className="mt-2 h-7 text-[10px] bg-teal-600 hover:bg-teal-700 w-full"
              onClick={() => onSendToTv(series.id)} disabled={isSending} data-testid={`send-tv-btn-${series.id}`}>
              {isSending ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Send className="w-3.5 h-3.5 mr-1" />}
              Invia in TV
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function PipelineCard({ project, navigate }) {
  const isAnime = project.type === 'anime';
  const stateLabelMap = {
    idea: 'Idea', hype: 'Hype', cast: 'Cast', prep: 'Preparazione',
    ciak: 'Riprese', finalcut: 'Final Cut', marketing: 'Marketing',
    distribution: 'Distribuzione TV', release_pending: 'In Uscita',
  };

  return (
    <Card className="bg-[#111113] border-white/5 overflow-hidden cursor-pointer active:scale-[0.98] transition-transform"
      onClick={() => navigate(isAnime ? '/create-anime' : '/create-series')}
      data-testid={`pipeline-card-${project.id}`}>
      <CardContent className="p-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0">
            {isAnime ? <Sparkles className="w-6 h-6 text-orange-400" /> : <Tv className="w-6 h-6 text-blue-400" />}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold truncate">{project.title}</h3>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge className="bg-purple-500/15 text-purple-400 border-0 text-[9px]">
                {stateLabelMap[project.pipeline_state] || project.pipeline_state}
              </Badge>
              {project.season_number > 1 && <span className="text-[10px] text-gray-500">S{project.season_number}</span>}
              <span className="text-[10px] text-gray-500">{project.num_episodes} ep.</span>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-600 flex-shrink-0" />
        </div>
      </CardContent>
    </Card>
  );
}


function formatRevenue(val) {
  if (!val || val === 0) return '0';
  if (val >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
  if (val >= 1e3) return `${(val / 1e3).toFixed(0)}K`;
  return val.toString();
}
