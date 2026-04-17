// CineWorld Studio's — I Miei Contenuti (unified content page)
// 4 tabs: Film, Saghe e Sequel, Serie TV, Anime
// Grid with small posters (4 cols mobile), popup with 6 actions for owner
// Also supports "I Suoi" mode for viewing another player's content

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import {
  Film, Tv, Sparkles, BookOpen, Eye, Megaphone, Store, Trash2, Wand2,
  X, Loader2, AlertTriangle, ChevronDown
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};

const TABS = [
  { id: 'film', label: 'Film', icon: Film, color: 'text-yellow-400', bg: 'bg-yellow-500/15' },
  { id: 'saghe', label: 'Saghe', icon: BookOpen, color: 'text-purple-400', bg: 'bg-purple-500/15' },
  { id: 'serie', label: 'Serie TV', icon: Tv, color: 'text-blue-400', bg: 'bg-blue-500/15' },
  { id: 'anime', label: 'Anime', icon: Sparkles, color: 'text-orange-400', bg: 'bg-orange-500/15' },
];

export default function MyFilms({ playerId, playerName, isPublicView }) {
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'film';

  const [films, setFilms] = useState([]);
  const [series, setSeries] = useState([]);
  const [anime, setAnime] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionPopup, setActionPopup] = useState(null); // { item, type }
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [confirmSell, setConfirmSell] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [regenLoading, setRegenLoading] = useState(null);

  const isOwner = !isPublicView && !playerId;
  const targetId = playerId || user?.id;

  const loadData = useCallback(async () => {
    if (!targetId) return;
    setLoading(true);
    try {
      if (isOwner) {
        const [filmsRes, seriesRes, animeRes] = await Promise.all([
          api.get('/films/my').catch(() => ({ data: [] })),
          api.get('/series-pipeline/my?series_type=tv_series').catch(() => ({ data: { series: [] } })),
          api.get('/series-pipeline/my?series_type=anime').catch(() => ({ data: { series: [] } })),
        ]);
        setFilms(Array.isArray(filmsRes.data) ? filmsRes.data : []);
        setSeries(seriesRes.data?.series || []);
        setAnime(animeRes.data?.series || []);
      } else {
        // Public view: get player's content
        const [filmsRes, seriesRes] = await Promise.all([
          api.get(`/players/${targetId}/films`).catch(() => ({ data: { films: [] } })),
          api.get(`/players/${targetId}/series`).catch(() => ({ data: { series: [] } })),
        ]);
        const allFilms = filmsRes.data?.films || filmsRes.data || [];
        setFilms(Array.isArray(allFilms) ? allFilms : []);
        const allSeries = seriesRes.data?.series || seriesRes.data || [];
        setSeries(allSeries.filter(s => s.type === 'tv_series'));
        setAnime(allSeries.filter(s => s.type === 'anime'));
      }
    } catch { /* */ }
    setLoading(false);
  }, [api, targetId, isOwner]);

  useEffect(() => { loadData(); }, [loadData]);

  // Filtered items
  const currentItems = activeTab === 'film'
    ? films.filter(f => !f.is_sequel)
    : activeTab === 'saghe'
    ? films.filter(f => f.is_sequel)
    : activeTab === 'serie'
    ? series
    : anime;

  const setTab = (tab) => setSearchParams({ tab });

  // ─── Actions ───
  const handleWithdraw = async (item) => {
    setActionLoading('withdraw');
    try {
      if (item._contentType === 'film') {
        await api.delete(`/films/${item.id}`);
        toast.success('Film ritirato dalle sale');
      }
      setActionPopup(null);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const handleDelete = async (item) => {
    setActionLoading('delete');
    try {
      if (item._contentType === 'film') {
        await api.delete(`/films/${item.id}/permanent`);
      } else {
        await api.delete(`/series/${item.id}/permanent`);
      }
      toast.success('Eliminato definitivamente');
      setConfirmDelete(null);
      setActionPopup(null);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const handleSell = async (item) => {
    setActionLoading('sell');
    try {
      // Use discard/marketplace endpoint
      if (item._contentType === 'film') {
        await api.post(`/pipeline-v3/films/${item.source_project_id || item.id}/discard-to-market`);
      }
      toast.success('Film messo in vendita!');
      setConfirmSell(null);
      setActionPopup(null);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore vendita'); }
    setActionLoading(null);
  };

  const handleRegen = async (item) => {
    setRegenLoading(item.id);
    setActionPopup(null);
    try {
      const startRes = await api.post(`/films/${item.id}/regenerate-poster`, {});
      const taskId = startRes.data.task_id;
      if (!taskId) { toast.error('Errore avvio rigenerazione'); setRegenLoading(null); return; }
      toast.info('Generazione locandina AI in corso...');
      for (let i = 0; i < 40; i++) {
        await new Promise(r => setTimeout(r, 3000));
        try {
          const statusRes = await api.get(`/ai/poster/status/${taskId}`);
          if (statusRes.data.status === 'done' && statusRes.data.poster_url) {
            toast.success('Locandina rigenerata!');
            loadData();
            setRegenLoading(null);
            return;
          }
          if (statusRes.data.status === 'error') {
            toast.error(statusRes.data.error || 'Errore generazione');
            setRegenLoading(null);
            return;
          }
        } catch { /* continue polling */ }
      }
      toast.error('Timeout generazione');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore rigenerazione'); }
    setRegenLoading(null);
  };

  const handleAdv = (item) => {
    setActionPopup(null);
    // Navigate to the film detail with ADV panel
    navigate(`/films/${item.id}`);
  };

  const handleView = (item) => {
    setActionPopup(null);
    if (item._contentType === 'film') {
      navigate(`/films/${item.id}`);
    } else {
      navigate(`/series/${item.id}`);
    }
  };

  const title = isPublicView ? `I Suoi di ${playerName || 'Player'}` : 'I Miei Contenuti';

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pt-14 pb-20" data-testid="my-content-page">
      {/* Header */}
      <div className="sticky top-14 z-20 bg-[#0A0A0B]/95 backdrop-blur-sm px-2 py-2">
        <h1 className="font-['Bebas_Neue'] text-xl text-center mb-2 tracking-wide">{title}</h1>
        {/* Tabs */}
        <div className="flex gap-1">
          {TABS.map(tab => {
            const count = tab.id === 'film' ? films.filter(f => !f.is_sequel).length
              : tab.id === 'saghe' ? films.filter(f => f.is_sequel).length
              : tab.id === 'serie' ? series.length
              : anime.length;
            return (
              <button key={tab.id}
                onClick={() => setTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-[10px] font-semibold transition-all
                  ${activeTab === tab.id ? `${tab.bg} ${tab.color} border border-current/20` : 'text-gray-500 bg-[#111113] border border-transparent'}`}
                data-testid={`tab-${tab.id}`}
              >
                <tab.icon className="w-3 h-3" />
                <span className="hidden xs:inline">{tab.label}</span>
                {count > 0 && <span className="text-[8px] opacity-60">{count}</span>}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content Grid */}
      <div className="px-1.5 pt-2">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
          </div>
        ) : currentItems.length === 0 ? (
          <EmptyState tab={activeTab} isOwner={isOwner} navigate={navigate} />
        ) : (
          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-1" data-testid="content-grid">
            {currentItems.map((item) => {
              const contentType = (activeTab === 'film' || activeTab === 'saghe') ? 'film' : (activeTab === 'serie' ? 'tv_series' : 'anime');
              const enriched = { ...item, _contentType: contentType };
              return (
                <PosterCard
                  key={item.id}
                  item={enriched}
                  isOwner={isOwner}
                  regenLoading={regenLoading}
                  onClick={() => {
                    if (isOwner) {
                      setActionPopup(enriched);
                    } else {
                      handleView(enriched);
                    }
                  }}
                />
              );
            })}
          </div>
        )}
      </div>

      {/* ─── Action Popup (6 options) ─── */}
      <Dialog open={!!actionPopup} onOpenChange={(o) => { if (!o) setActionPopup(null); }}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-[320px] p-0 [&>button]:hidden" data-testid="content-action-popup">
          {actionPopup && (
            <>
              {/* Mini header with poster + title */}
              <div className="flex items-center gap-3 p-3 border-b border-white/5">
                <div className="w-10 h-14 rounded overflow-hidden flex-shrink-0 bg-gray-800">
                  {posterSrc(actionPopup.poster_url) ? (
                    <img src={posterSrc(actionPopup.poster_url)} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center"><Film className="w-4 h-4 text-gray-600" /></div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-bold truncate">{actionPopup.title}</h3>
                  <p className="text-[9px] text-gray-500">{actionPopup.genre_name || actionPopup.genre || ''}</p>
                </div>
                <button onClick={() => setActionPopup(null)} className="text-gray-500 p-1"><X className="w-4 h-4" /></button>
              </div>
              {/* 6 Action buttons */}
              <div className="p-2 space-y-1">
                {/* 1. Visualizza */}
                <ActionBtn icon={<Eye className="w-4 h-4" />} label="Visualizza dettaglio" color="text-cyan-400" onClick={() => handleView(actionPopup)} testId="action-view" />
                {/* 2. ADV */}
                {actionPopup._contentType === 'film' && actionPopup.status === 'in_theaters' && (
                  <ActionBtn icon={<Megaphone className="w-4 h-4" />} label="Campagna ADV" color="text-yellow-400" onClick={() => handleAdv(actionPopup)} testId="action-adv" />
                )}
                {/* 3. Rigenera locandina */}
                {actionPopup._contentType === 'film' && (
                  <ActionBtn icon={<Wand2 className="w-4 h-4" />} label={actionPopup.poster_url ? "Rigenera locandina (1x/mese)" : "Genera locandina"} color="text-purple-400"
                    onClick={() => handleRegen(actionPopup)} loading={regenLoading === actionPopup.id} testId="action-regen" />
                )}
                {/* 4. Togli da cinema / TV */}
                {actionPopup._contentType === 'film' && actionPopup.status === 'in_theaters' && (
                  <ActionBtn icon={<ChevronDown className="w-4 h-4" />} label="Ritira dal cinema" color="text-orange-400"
                    onClick={() => handleWithdraw(actionPopup)} loading={actionLoading === 'withdraw'} testId="action-withdraw" />
                )}
                {/* 5. Vendi film */}
                {actionPopup._contentType === 'film' && (
                  <ActionBtn icon={<Store className="w-4 h-4" />} label="Vendi al mercato" color="text-emerald-400"
                    onClick={() => setConfirmSell(actionPopup)} testId="action-sell" />
                )}
                {/* 6. Elimina */}
                <ActionBtn icon={<Trash2 className="w-4 h-4" />} label="Elimina per sempre" color="text-red-400"
                  onClick={() => setConfirmDelete(actionPopup)} testId="action-delete" />
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* ─── Confirm Delete (non-standard) ─── */}
      <Dialog open={!!confirmDelete} onOpenChange={(o) => { if (!o) setConfirmDelete(null); }}>
        <DialogContent className="bg-[#0F0F10] border-red-500/20 max-w-[320px]" data-testid="confirm-delete-dialog">
          <DialogHeader>
            <DialogTitle className="text-sm flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-4 h-4" /> Eliminazione Permanente
            </DialogTitle>
            <DialogDescription className="text-[11px] text-gray-400">
              "{confirmDelete?.title}" verrà eliminato per sempre. Questa azione NON può essere annullata.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 mt-2">
            <Button variant="outline" size="sm" className="text-xs border-white/10" onClick={() => setConfirmDelete(null)}>Annulla</Button>
            <Button size="sm" className="bg-red-600 hover:bg-red-700 text-xs" onClick={() => handleDelete(confirmDelete)} disabled={actionLoading === 'delete'} data-testid="confirm-delete-btn">
              {actionLoading === 'delete' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Trash2 className="w-3 h-3 mr-1" />}
              Elimina per sempre
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ─── Confirm Sell (black button) ─── */}
      <Dialog open={!!confirmSell} onOpenChange={(o) => { if (!o) setConfirmSell(null); }}>
        <DialogContent className="bg-[#0F0F10] border-emerald-500/20 max-w-[320px]" data-testid="confirm-sell-dialog">
          <DialogHeader>
            <DialogTitle className="text-sm flex items-center gap-2 text-emerald-400">
              <Store className="w-4 h-4" /> Vendi al Mercato
            </DialogTitle>
            <DialogDescription className="text-[11px] text-gray-400">
              "{confirmSell?.title}" verrà messo in vendita. Confermi?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 mt-2">
            <Button variant="outline" size="sm" className="text-xs border-white/10" onClick={() => setConfirmSell(null)}>Annulla</Button>
            <Button size="sm" className="bg-black hover:bg-gray-900 text-white text-xs border border-white/20" onClick={() => handleSell(confirmSell)} disabled={actionLoading === 'sell'} data-testid="confirm-sell-btn">
              {actionLoading === 'sell' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Store className="w-3 h-3 mr-1" />}
              Conferma Vendita
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/* ─── Poster Card ─── */
function PosterCard({ item, isOwner, regenLoading, onClick }) {
  const isLive = item.status === 'in_theaters' || item.status === 'in_tv';
  const url = posterSrc(item.poster_url);
  const isRegen = regenLoading === item.id;

  return (
    <div className="relative cursor-pointer active:scale-95 transition-transform" onClick={onClick} data-testid={`poster-${item.id}`}>
      <div className="aspect-[2/3] rounded-md overflow-hidden bg-[#111113] border border-white/5">
        {url ? (
          <img src={url} alt={item.title} className="w-full h-full object-cover" loading="lazy"
            onError={(e) => { e.target.style.display = 'none'; }} />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Film className="w-5 h-5 text-gray-700" />
          </div>
        )}
        {isRegen && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
            <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
          </div>
        )}
      </div>
      {/* Status badge */}
      {isLive && (
        <div className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-green-400 shadow-sm shadow-green-400/50" />
      )}
      {/* Title below poster */}
      <p className="text-[7px] text-gray-400 truncate mt-0.5 px-0.5 leading-tight">{item.title}</p>
    </div>
  );
}

/* ─── Action Button ─── */
function ActionBtn({ icon, label, color, onClick, loading, testId }) {
  return (
    <button onClick={onClick} disabled={loading}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all hover:bg-white/5 active:bg-white/10 ${color}`}
      data-testid={testId}>
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : icon}
      <span className="text-[11px] font-medium">{label}</span>
    </button>
  );
}

/* ─── Empty State ─── */
function EmptyState({ tab, isOwner, navigate }) {
  const msgs = {
    film: { icon: Film, text: 'Nessun film', btn: isOwner ? 'Crea Film' : null, route: '/create-film', color: 'bg-yellow-500 text-black' },
    saghe: { icon: BookOpen, text: 'Nessun sequel', btn: isOwner ? 'Crea Sequel' : null, route: '/sagas', color: 'bg-purple-600 text-white' },
    serie: { icon: Tv, text: 'Nessuna serie TV', btn: isOwner ? 'Crea Serie TV' : null, route: '/create-series', color: 'bg-blue-600 text-white' },
    anime: { icon: Sparkles, text: 'Nessun anime', btn: isOwner ? 'Crea Anime' : null, route: '/create-anime', color: 'bg-orange-600 text-white' },
  };
  const m = msgs[tab] || msgs.film;
  return (
    <div className="text-center py-16" data-testid={`empty-${tab}`}>
      <m.icon className="w-10 h-10 text-gray-700 mx-auto mb-3" />
      <p className="text-gray-400 text-sm mb-4">{m.text}</p>
      {m.btn && (
        <Button size="sm" className={`text-xs ${m.color}`} onClick={() => navigate(m.route)}>{m.btn}</Button>
      )}
    </div>
  );
}
