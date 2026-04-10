import React, { useState, useEffect, useContext, useMemo } from 'react';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Film, TrendingUp, Plus, X, DollarSign, Building, Ticket,
  Store, Crown, ShoppingBag, ArrowUpCircle, Wallet,
  ChevronDown, ChevronUp, Clock, Info, Zap, ThumbsUp, ThumbsDown, Minus
} from 'lucide-react';

const STRUTTURE_CATEGORIES = [
  { id: 'cinema', label: 'Cinema', icon: Ticket, color: 'amber', types: ['cinema', 'drive_in', 'vip_cinema'] },
  { id: 'commerciale', label: 'Commerciale', icon: Store, color: 'green', types: ['multiplex_small', 'multiplex_medium', 'multiplex_large'] },
  { id: 'speciale', label: 'Speciale', icon: Crown, color: 'yellow', types: ['cinema_museum', 'film_festival_venue', 'theme_park'] },
];

const ALL_STRUTTURE_TYPES = STRUTTURE_CATEGORIES.flatMap(c => c.types);

const STRUCTURE_LABELS = {
  cinema: { label: 'Cinema Standard', bonus: null },
  drive_in: { label: 'Drive-In', bonus: 'Bonus Horror / Action +20%' },
  vip_cinema: { label: 'Cinema VIP di Lusso', bonus: 'Bonus Drama / Romance +25%' },
  multiplex_small: { label: 'Centro Comm. Piccolo', bonus: 'Bonus Action +15%' },
  multiplex_medium: { label: 'Centro Comm. Medio', bonus: 'Bonus Action +15%' },
  multiplex_large: { label: 'Centro Comm. Grande IMAX', bonus: 'Bonus Action / Sci-Fi +15%' },
  cinema_museum: { label: 'Museo del Cinema', bonus: 'Bonus Storico / Drama +25%' },
  film_festival_venue: { label: 'Sede Festival', bonus: 'Bonus Drama / Indie +25%' },
  theme_park: { label: 'Parco a Tema', bonus: 'Bonus Action / Adventure / Sci-Fi +25%' },
};

function getFilmPerformance(film, gradimento) {
  const q = film.quality_score || 50;
  const imdb = film.imdb_rating || 5;
  const g = gradimento || 70;
  const score = (q * 0.4) + (imdb * 6) + (g * 0.2);
  if (score >= 65) return { level: 'ottimo', color: 'green', label: 'Ottimo rendimento', icon: ThumbsUp };
  if (score >= 40) return { level: 'medio', color: 'yellow', label: 'Rendimento medio', icon: Minus };
  return { level: 'flop', color: 'red', label: 'Sta performando male', icon: ThumbsDown };
}

function getRentalDaysLeft(film) {
  if (!film.rental_end_date) return null;
  const end = new Date(film.rental_end_date);
  const now = new Date();
  const diff = Math.max(0, Math.ceil((end - now) / 86400000));
  return diff;
}

function getFilmAge(film) {
  if (!film.added_at) return null;
  const added = new Date(film.added_at);
  const now = new Date();
  return Math.floor((now - added) / 86400000);
}

function generateEarningsExplanation(detail, prices) {
  const factors = [];
  const films = detail?.films_showing || [];
  const gradimento = detail?.gradimento ?? detail?.stats?.satisfaction_index ?? 70;
  const ticketPrice = prices?.ticket || 12;
  const screens = detail?.type_info?.screens || 4;

  if (films.length === 0) {
    factors.push({ type: 'negative', text: 'Nessun film in programmazione' });
    return factors;
  }

  const avgQuality = films.reduce((s, f) => s + (f.quality_score || 50), 0) / films.length;
  const avgImdb = films.reduce((s, f) => s + (f.imdb_rating || 5), 0) / films.length;

  if (avgQuality >= 65) factors.push({ type: 'positive', text: 'Film di alta qualita in programmazione' });
  else if (avgQuality < 40) factors.push({ type: 'negative', text: 'Film di bassa qualita abbassano la resa' });

  if (avgImdb >= 7) factors.push({ type: 'positive', text: `Rating IMDb medio alto (${avgImdb.toFixed(1)})` });
  else if (avgImdb < 5) factors.push({ type: 'negative', text: `Rating IMDb medio basso (${avgImdb.toFixed(1)})` });

  if (ticketPrice >= 8 && ticketPrice <= 15) factors.push({ type: 'positive', text: 'Prezzi ben bilanciati' });
  else if (ticketPrice > 20) factors.push({ type: 'negative', text: 'Prezzo biglietto troppo alto, meno spettatori' });
  else if (ticketPrice < 5) factors.push({ type: 'neutral', text: 'Prezzo biglietto molto basso, alta affluenza ma bassi incassi' });

  if (gradimento >= 70) factors.push({ type: 'positive', text: 'Gradimento pubblico alto' });
  else if (gradimento < 40) factors.push({ type: 'negative', text: 'Gradimento pubblico basso' });

  if (films.length < screens) factors.push({ type: 'neutral', text: `${screens - films.length} scherm${screens - films.length > 1 ? 'i' : 'o'} vuot${screens - films.length > 1 ? 'i' : 'o'}` });
  if (films.length === screens) factors.push({ type: 'positive', text: 'Tutti gli schermi occupati' });

  const oldFilms = films.filter(f => getFilmAge(f) > 5).length;
  if (oldFilms > 0) factors.push({ type: 'negative', text: `${oldFilms} film in programmazione da troppo tempo` });

  return factors;
}

export default function StrutturePage() {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const [structures, setStructures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('cinema');
  const [expanded, setExpanded] = useState(null);
  const [detail, setDetail] = useState(null);
  const [upgradeInfo, setUpgradeInfo] = useState(null);
  const [upgrading, setUpgrading] = useState(false);
  const [pendingRevenue, setPendingRevenue] = useState(null);
  const [showAddFilm, setShowAddFilm] = useState(false);
  const [showRentFilm, setShowRentFilm] = useState(false);
  const [myFilms, setMyFilms] = useState([]);
  const [rentalFilms, setRentalFilms] = useState([]);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [rentalWeeks, setRentalWeeks] = useState(1);
  const [actionLoading, setActionLoading] = useState(false);
  const [removingFilm, setRemovingFilm] = useState(null);
  const [showPrices, setShowPrices] = useState(false);
  const [prices, setPrices] = useState({});
  const [savingPrices, setSavingPrices] = useState(false);

  useEffect(() => {
    api.get('/infrastructure/my').then(r => {
      setStructures((r.data.infrastructure || []).filter(i => ALL_STRUTTURE_TYPES.includes(i.type)));
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [api]);

  const refreshStructures = async () => {
    const r = await api.get('/infrastructure/my');
    setStructures((r.data.infrastructure || []).filter(i => ALL_STRUTTURE_TYPES.includes(i.type)));
  };

  const openDetail = async (infra) => {
    setExpanded(infra.id);
    try {
      const [d, u, rev] = await Promise.all([
        api.get(`/infrastructure/${infra.id}`),
        api.get(`/infrastructure/${infra.id}/upgrade-info`),
        api.get(`/infrastructure/${infra.id}/pending-revenue`).catch(() => ({ data: null })),
      ]);
      setDetail(d.data);
      setUpgradeInfo(u.data);
      setPendingRevenue(rev.data);
      setPrices(d.data.prices || { ticket: 12, popcorn: 8, drinks: 5, combo: 18 });
    } catch { toast.error('Errore caricamento'); setExpanded(null); }
  };

  const handleUpgrade = async (infraId) => {
    setUpgrading(true);
    try {
      const r = await api.post(`/infrastructure/${infraId}/upgrade`);
      toast.success(`Upgrade al Livello ${r.data.new_level}!`);
      await openDetail(structures.find(s => s.id === infraId));
      await refreshStructures();
      refreshUser();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore upgrade'); }
    finally { setUpgrading(false); }
  };

  const addFilm = async () => {
    if (!selectedFilm || !expanded) return;
    setActionLoading(true);
    try {
      const r = await api.post(`/infrastructure/${expanded}/add-film`, { film_id: selectedFilm.id });
      toast.success(`"${selectedFilm.title}" aggiunto! Affluenza prevista in aumento`);
      setDetail(prev => ({ ...prev, films_showing: r.data.films_showing }));
      setShowAddFilm(false); setSelectedFilm(null);
      await refreshStructures();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(false); }
  };

  const rentFilm = async () => {
    if (!selectedFilm || !expanded) return;
    setActionLoading(true);
    try {
      const r = await api.post(`/infrastructure/${expanded}/rent-film`, { film_id: selectedFilm.id, weeks: rentalWeeks });
      toast.success(`"${selectedFilm.title}" affittato! Il 70% dei ricavi sara tuo`);
      setDetail(prev => ({ ...prev, films_showing: r.data.films_showing }));
      setShowRentFilm(false); setSelectedFilm(null); setRentalWeeks(1);
      await refreshStructures(); refreshUser();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(false); }
  };

  const removeFilm = async (filmId) => {
    if (!expanded) return;
    setRemovingFilm(filmId);
    try {
      const r = await api.delete(`/infrastructure/${expanded}/films/${filmId}`);
      setDetail(prev => ({ ...prev, films_showing: r.data.films_showing }));
      toast('Film rimosso. Rischio calo spettatori se non sostituito', { icon: <Info className="w-4 h-4 text-yellow-400" /> });
      await refreshStructures();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setRemovingFilm(null); }
  };

  const savePricesFn = async () => {
    if (!expanded) return;
    setSavingPrices(true);
    try {
      await api.put(`/infrastructure/${expanded}/prices`, { prices });
      const p = prices.ticket || 12;
      if (p > 20) toast('Prezzi aggiornati. Attenzione: prezzo alto, rischio calo spettatori', { icon: <Info className="w-4 h-4 text-yellow-400" /> });
      else if (p < 5) toast('Prezzi aggiornati. Prezzo basso = tanta affluenza, pochi incassi per biglietto', { icon: <Info className="w-4 h-4 text-cyan-400" /> });
      else toast.success('Prezzi aggiornati! Buon bilanciamento');
      await openDetail(structures.find(s => s.id === expanded));
      await refreshStructures();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setSavingPrices(false); setShowPrices(false); }
  };

  const activeCat = STRUTTURE_CATEGORIES.find(c => c.id === activeTab) || STRUTTURE_CATEGORIES[0];
  const filtered = structures.filter(s => activeCat.types.includes(s.type));

  if (loading) return <div className="pt-20 text-center text-gray-500">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 max-w-2xl mx-auto px-3" data-testid="strutture-page">
      <div className="mb-4">
        <h1 className="font-['Bebas_Neue'] text-2xl tracking-wide">Le Tue Strutture</h1>
        <p className="text-xs text-gray-500">Gestisci cinema, programmazione film e incassi</p>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 mb-4">
        {STRUTTURE_CATEGORIES.map(cat => {
          const CatIcon = cat.icon;
          const count = structures.filter(s => cat.types.includes(s.type)).length;
          const isActive = activeTab === cat.id;
          return (
            <button key={cat.id} onClick={() => { setActiveTab(cat.id); setExpanded(null); setDetail(null); }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-xs font-medium border transition-all ${isActive ? `bg-${cat.color}-500/15 border-${cat.color}-500/30 text-${cat.color}-400 shadow-[0_0_12px_rgba(251,191,36,0.08)]` : 'bg-white/3 border-white/5 text-gray-500 hover:text-gray-300'}`}
              data-testid={`strutture-tab-${cat.id}`}>
              <CatIcon className="w-3.5 h-3.5" />
              {cat.label}
              {count > 0 && <span className="text-[9px] bg-white/10 px-1.5 rounded-full">{count}</span>}
            </button>
          );
        })}
      </div>

      {/* Structure cards */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <Building className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">Nessuna struttura {activeCat.label.toLowerCase()}</p>
          <p className="text-xs text-gray-600 mt-1">Acquistala dalla sezione Infrastrutture</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(infra => {
            const isOpen = expanded === infra.id;
            const structInfo = STRUCTURE_LABELS[infra.type] || { label: infra.type, bonus: null };
            const gradimento = detail?.gradimento ?? detail?.stats?.satisfaction_index ?? 70;
            const earningsFactors = isOpen && detail ? generateEarningsExplanation(detail, prices) : [];

            return (
              <div key={infra.id} className="rounded-xl border border-white/8 bg-white/3 overflow-hidden transition-all">
                {/* Card header */}
                <button className="w-full flex items-center gap-3 p-3 text-left active:scale-[0.99] transition-transform"
                  onClick={() => isOpen ? (setExpanded(null), setDetail(null)) : openDetail(infra)}
                  data-testid={`struttura-card-${infra.id}`}>
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-${activeCat.color}-500/15 flex-shrink-0`}>
                    <activeCat.icon className={`w-5 h-5 text-${activeCat.color}-400`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-sm truncate">{infra.custom_name}</h3>
                      <Badge className={`text-[8px] h-4 px-1 bg-${activeCat.color}-500/20 text-${activeCat.color}-400`}>Lv.{infra.level || 1}</Badge>
                    </div>
                    <p className="text-[10px] text-gray-500 truncate">{infra.city?.name}, {infra.country}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs font-bold text-green-400">${(infra.total_revenue || 0).toLocaleString()}</p>
                    <p className="text-[9px] text-gray-600">ricavi totali</p>
                  </div>
                  {isOpen ? <ChevronUp className="w-4 h-4 text-gray-500 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />}
                </button>

                {/* Expanded detail */}
                <AnimatePresence>
                  {isOpen && detail && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }} className="overflow-hidden">
                      <div className="px-3 pb-3 space-y-3 border-t border-white/5 pt-3">

                        {/* 3) STRUCTURE TYPE + BONUS */}
                        <div className="flex items-center gap-2 p-2 bg-white/3 rounded-lg border border-white/8">
                          <Zap className={`w-4 h-4 flex-shrink-0 text-${activeCat.color}-400`} />
                          <div className="flex-1 min-w-0">
                            <p className="text-[11px] font-semibold">{structInfo.label}</p>
                            {structInfo.bonus && <p className="text-[9px] text-cyan-400">{structInfo.bonus}</p>}
                          </div>
                        </div>

                        {/* 5) GRADIMENTO BAR (animated) */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] text-gray-400">Gradimento pubblico</span>
                            <span className={`text-xs font-bold ${gradimento >= 70 ? 'text-green-400' : gradimento >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>{gradimento}/100</span>
                          </div>
                          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                            <motion.div
                              className={`h-full rounded-full ${gradimento >= 70 ? 'bg-gradient-to-r from-green-500 to-green-400' : gradimento >= 40 ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' : 'bg-gradient-to-r from-red-600 to-red-400'}`}
                              initial={{ width: 0 }}
                              animate={{ width: `${gradimento}%` }}
                              transition={{ duration: 0.8, ease: 'easeOut' }}
                            />
                          </div>
                        </div>

                        {/* Stats grid */}
                        {detail.stats && (
                          <div className="grid grid-cols-3 gap-2">
                            <div className="p-2 bg-cyan-500/10 rounded-lg border border-cyan-500/20 text-center">
                              <p className="text-[9px] text-gray-400">Affluenza</p>
                              <p className="text-sm font-bold text-cyan-400">{detail.stats.daily_attendance?.toLocaleString()}</p>
                            </div>
                            <div className="p-2 bg-green-500/10 rounded-lg border border-green-500/20 text-center">
                              <p className="text-[9px] text-gray-400">Occupazione</p>
                              <p className="text-sm font-bold text-green-400">{detail.stats.occupancy_rate}%</p>
                            </div>
                            <div className="p-2 bg-white/5 rounded-lg border border-white/10 text-center">
                              <p className="text-[9px] text-gray-400">Schermi</p>
                              <p className="text-sm font-bold text-white">{detail.stats?.screens || 0}</p>
                            </div>
                          </div>
                        )}

                        {/* Revenue */}
                        <div className="flex items-center justify-between p-2.5 bg-gradient-to-r from-green-500/8 to-yellow-500/8 rounded-lg border border-green-500/15">
                          <div className="flex items-center gap-2">
                            <Wallet className="w-4 h-4 text-green-400" />
                            <div>
                              <p className="text-[10px] text-gray-400">Incassi automatici</p>
                              <p className="text-sm font-bold text-green-400">${(pendingRevenue?.pending || 0).toLocaleString()}</p>
                            </div>
                          </div>
                          <div className="text-right text-[10px] text-gray-500">
                            <p>{detail.stats?.total_capacity?.toLocaleString() || 0} posti</p>
                          </div>
                        </div>

                        {/* 2) SPIEGAZIONE GUADAGNI */}
                        {earningsFactors.length > 0 && (
                          <div className="p-2.5 bg-white/3 rounded-lg border border-white/8 space-y-1.5">
                            <p className="text-[10px] font-semibold text-gray-300 flex items-center gap-1"><Info className="w-3 h-3 text-gray-500" /> Perche stai guadagnando cosi?</p>
                            {earningsFactors.map((f, i) => (
                              <div key={i} className="flex items-start gap-1.5">
                                <span className={`text-[10px] font-bold mt-px ${f.type === 'positive' ? 'text-green-400' : f.type === 'negative' ? 'text-red-400' : 'text-yellow-400'}`}>
                                  {f.type === 'positive' ? '+' : f.type === 'negative' ? '-' : '~'}
                                </span>
                                <span className="text-[10px] text-gray-400">{f.text}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* 1) FILM PROGRAMMING with performance badges */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-semibold flex items-center gap-1.5">
                              <Film className="w-3.5 h-3.5 text-yellow-500" /> Programmazione
                            </h4>
                            <span className="text-[10px] text-gray-500">{detail.films_showing?.length || 0}/{detail.type_info?.screens || 4} schermi</span>
                          </div>

                          {detail.films_showing?.length > 0 ? (
                            <div className="space-y-1.5">
                              {detail.films_showing.map(film => {
                                const perf = getFilmPerformance(film, gradimento);
                                const PerfIcon = perf.icon;
                                const daysLeft = getRentalDaysLeft(film);
                                const age = getFilmAge(film);
                                const isRented = !film.is_owned;
                                return (
                                  <div key={film.film_id} className={`p-2 rounded-lg border bg-${perf.color}-500/5 border-${perf.color}-500/15`} data-testid={`film-card-${film.film_id}`}>
                                    <div className="flex items-center gap-2">
                                      {film.poster_url && <img src={film.poster_url} alt="" className="w-8 h-12 object-cover rounded flex-shrink-0" />}
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-1.5">
                                          <p className="text-xs font-semibold truncate">{film.title}</p>
                                          {/* Performance badge */}
                                          <Badge className={`text-[7px] h-3.5 px-1 bg-${perf.color}-500/25 text-${perf.color}-400 flex items-center gap-0.5 flex-shrink-0`}>
                                            <PerfIcon className="w-2 h-2" />
                                            {perf.level === 'ottimo' ? 'OTTIMO' : perf.level === 'medio' ? 'MEDIO' : 'FLOP'}
                                          </Badge>
                                        </div>
                                        <p className={`text-[9px] text-${perf.color}-400/80`}>{perf.label}</p>
                                        <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                                          <span className="text-[9px] text-gray-500">IMDb {film.imdb_rating || '?'}</span>
                                          {/* 4) RENTAL info */}
                                          {isRented ? (
                                            <>
                                              <Badge className="text-[7px] h-3 bg-blue-500/25 text-blue-400">Noleggiato {film.revenue_share_renter || 70}%</Badge>
                                              {daysLeft !== null && <span className="text-[9px] text-blue-300"><Clock className="w-2.5 h-2.5 inline mr-0.5" />{daysLeft}g</span>}
                                              {film.rental_cost && <span className="text-[9px] text-gray-600">Pagato ${film.rental_cost?.toLocaleString()}</span>}
                                            </>
                                          ) : (
                                            <Badge className="text-[7px] h-3 bg-green-500/20 text-green-400">Tuo 100%</Badge>
                                          )}
                                          {age !== null && age > 5 && <span className="text-[9px] text-orange-400">In prog. da {age}g</span>}
                                        </div>
                                      </div>
                                      <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10 flex-shrink-0" disabled={removingFilm === film.film_id} onClick={() => removeFilm(film.film_id)}>
                                        <X className="w-3.5 h-3.5" />
                                      </Button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <p className="text-center text-gray-600 text-[11px] py-3">Nessun film in programmazione</p>
                          )}

                          {(detail.films_showing?.length || 0) < (detail.type_info?.screens || 4) && (
                            <div className="grid grid-cols-2 gap-2">
                              <Button variant="outline" className="h-8 text-[11px] border-white/10" onClick={async () => {
                                const r = await api.get('/films/my-available'); setMyFilms(r.data); setShowAddFilm(true);
                              }}><Plus className="w-3 h-3 mr-1" /> I Miei Film</Button>
                              <Button className="h-8 text-[11px] bg-blue-600 hover:bg-blue-500" onClick={async () => {
                                const r = await api.get('/films/available-for-rental'); setRentalFilms(r.data); setShowRentFilm(true);
                              }}><ShoppingBag className="w-3 h-3 mr-1" /> Affitta</Button>
                            </div>
                          )}
                        </div>

                        {/* Actions row */}
                        <div className="grid grid-cols-2 gap-2">
                          <Button variant="outline" className="h-8 text-[11px] border-yellow-500/20 text-yellow-400 hover:bg-yellow-500/10" onClick={() => setShowPrices(true)}>
                            <DollarSign className="w-3 h-3 mr-1" /> Prezzi
                          </Button>
                          {upgradeInfo && upgradeInfo.current_level < upgradeInfo.max_level && (
                            <Button className={`h-8 text-[11px] ${upgradeInfo.can_upgrade ? 'bg-gradient-to-r from-purple-600 to-cyan-600 text-white' : 'bg-gray-700 text-gray-400'}`}
                              disabled={!upgradeInfo.can_upgrade || upgrading} onClick={() => handleUpgrade(infra.id)} data-testid={`upgrade-struttura-${infra.id}`}>
                              <ArrowUpCircle className="w-3 h-3 mr-1" />
                              {upgrading ? '...' : `Lv.${upgradeInfo.next_level} ($${upgradeInfo.upgrade_cost?.toLocaleString()})`}
                            </Button>
                          )}
                          {upgradeInfo && upgradeInfo.current_level >= upgradeInfo.max_level && (
                            <Badge className="h-8 flex items-center justify-center bg-purple-500/20 text-purple-400 text-[11px]">MAX Lv.{upgradeInfo.max_level}</Badge>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Own Film Dialog */}
      <Dialog open={showAddFilm} onOpenChange={setShowAddFilm}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-lg">Aggiungi Film</DialogTitle>
            <DialogDescription>Seleziona un tuo film (100% ricavi)</DialogDescription>
          </DialogHeader>
          {myFilms.length === 0 ? (
            <p className="text-center text-gray-500 py-6 text-sm">Nessun film disponibile</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {myFilms.map(f => (
                <div key={f.id} className={`flex items-center gap-3 p-2 rounded-lg border cursor-pointer transition-colors ${selectedFilm?.id === f.id ? 'bg-yellow-500/15 border-yellow-500/40' : 'bg-white/3 border-white/8 hover:border-yellow-500/30'}`} onClick={() => setSelectedFilm(f)}>
                  {f.poster_url && <img src={f.poster_url} alt="" className="w-10 h-14 object-cover rounded" />}
                  <div className="flex-1">
                    <p className="text-sm font-semibold">{f.title}</p>
                    <p className="text-[10px] text-gray-400">{f.genre} IMDb {f.imdb_rating}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowAddFilm(false)}>Annulla</Button>
            <Button size="sm" onClick={addFilm} disabled={!selectedFilm || actionLoading} className="bg-yellow-500 text-black">{actionLoading ? '...' : 'Aggiungi'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rent Film Dialog */}
      <Dialog open={showRentFilm} onOpenChange={setShowRentFilm}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-lg">Affitta Film</DialogTitle>
            <DialogDescription>Paga l'affitto, ricevi il 70% dei ricavi</DialogDescription>
          </DialogHeader>
          {rentalFilms.length === 0 ? (
            <p className="text-center text-gray-500 py-6 text-sm">Nessun film disponibile</p>
          ) : (
            <>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {rentalFilms.map(f => (
                  <div key={f.id} className={`flex items-center gap-3 p-2 rounded-lg border cursor-pointer transition-colors ${selectedFilm?.id === f.id ? 'bg-blue-500/15 border-blue-500/40' : 'bg-white/3 border-white/8 hover:border-blue-500/30'}`} onClick={() => setSelectedFilm(f)}>
                    {f.poster_url && <img src={f.poster_url} alt="" className="w-10 h-14 object-cover rounded" />}
                    <div className="flex-1">
                      <p className="text-sm font-semibold">{f.title}</p>
                      <p className="text-[10px] text-gray-400">{f.genre} IMDb {f.imdb_rating} di {f.owner?.nickname || '?'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-yellow-500 font-bold text-xs">${f.weekly_rental?.toLocaleString()}</p>
                      <p className="text-[9px] text-gray-500">/sett.</p>
                    </div>
                  </div>
                ))}
              </div>
              {selectedFilm && (
                <div className="p-3 bg-blue-500/8 rounded-lg border border-blue-500/20 mt-2">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs">Durata:</span>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" className="h-6 w-6 p-0" onClick={() => setRentalWeeks(Math.max(1, rentalWeeks - 1))}>-</Button>
                      <span className="w-6 text-center font-bold text-sm">{rentalWeeks}</span>
                      <Button size="sm" variant="outline" className="h-6 w-6 p-0" onClick={() => setRentalWeeks(Math.min(12, rentalWeeks + 1))}>+</Button>
                      <span className="text-xs">sett.</span>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Totale:</span>
                    <span className="text-yellow-500 font-bold">${(selectedFilm.weekly_rental * rentalWeeks).toLocaleString()}</span>
                  </div>
                </div>
              )}
            </>
          )}
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => { setShowRentFilm(false); setSelectedFilm(null); }}>Annulla</Button>
            <Button size="sm" onClick={rentFilm} disabled={!selectedFilm || actionLoading || (user?.funds < (selectedFilm?.weekly_rental * rentalWeeks))} className="bg-blue-500">{actionLoading ? '...' : 'Affitta'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Prices Dialog */}
      <Dialog open={showPrices} onOpenChange={setShowPrices}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-sm">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><DollarSign className="w-4 h-4 text-yellow-500" /> Prezzi</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            {[['ticket', 'Biglietto', 50], ['popcorn', 'Popcorn', 30], ['drinks', 'Bevande', 20], ['combo', 'Combo', 60]].map(([k, label, max]) => (
              <div key={k}>
                <Label className="text-[10px]">{label} ($)</Label>
                <Input type="number" value={prices[k] || 0} onChange={e => setPrices({ ...prices, [k]: parseInt(e.target.value) || 0 })} className="h-8 bg-black/20 border-white/10 text-sm" min={1} max={max} />
              </div>
            ))}
          </div>
          <p className="text-[9px] text-gray-500">Prezzi troppo alti riducono l'affluenza. Bilanciamento ideale: $8-$15 per biglietto.</p>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowPrices(false)}>Annulla</Button>
            <Button size="sm" onClick={savePricesFn} disabled={savingPrices} className="bg-yellow-500 text-black">{savingPrices ? '...' : 'Salva'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
