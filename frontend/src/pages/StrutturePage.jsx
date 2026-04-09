import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Film, Star, TrendingUp, Plus, X, DollarSign, Building, Ticket,
  Store, Crown, ShoppingBag, Eye, Zap, Shield, ArrowUpCircle, Wallet,
  ChevronDown, ChevronUp, Users
} from 'lucide-react';

const STRUTTURE_CATEGORIES = [
  { id: 'cinema', label: 'Cinema', icon: Ticket, color: 'amber', types: ['cinema', 'drive_in', 'vip_cinema'] },
  { id: 'commerciale', label: 'Commerciale', icon: Store, color: 'green', types: ['multiplex_small', 'multiplex_medium', 'multiplex_large'] },
  { id: 'speciale', label: 'Speciale', icon: Crown, color: 'yellow', types: ['cinema_museum', 'film_festival_venue', 'theme_park'] },
];

const ALL_STRUTTURE_TYPES = STRUTTURE_CATEGORIES.flatMap(c => c.types);

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
  // Film management
  const [showAddFilm, setShowAddFilm] = useState(false);
  const [showRentFilm, setShowRentFilm] = useState(false);
  const [myFilms, setMyFilms] = useState([]);
  const [rentalFilms, setRentalFilms] = useState([]);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [rentalWeeks, setRentalWeeks] = useState(1);
  const [actionLoading, setActionLoading] = useState(false);
  const [removingFilm, setRemovingFilm] = useState(null);
  // Prices
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
      toast.success(`"${selectedFilm.title}" aggiunto!`);
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
      toast.success(`"${selectedFilm.title}" affittato per ${rentalWeeks} settimane!`);
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
      toast.success('Film rimosso');
      await refreshStructures();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setRemovingFilm(null); }
  };

  const savePricesFn = async () => {
    if (!expanded) return;
    setSavingPrices(true);
    try {
      await api.put(`/infrastructure/${expanded}/prices`, { prices });
      toast.success('Prezzi aggiornati!');
      await refreshStructures();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setSavingPrices(false); setShowPrices(false); }
  };

  const activeCat = STRUTTURE_CATEGORIES.find(c => c.id === activeTab) || STRUTTURE_CATEGORIES[0];
  const filtered = structures.filter(s => activeCat.types.includes(s.type));

  const getPerformanceColor = (val) => val >= 70 ? 'text-green-400' : val >= 40 ? 'text-yellow-400' : 'text-red-400';
  const getPerformanceBg = (val) => val >= 70 ? 'bg-green-500/15 border-green-500/25' : val >= 40 ? 'bg-yellow-500/15 border-yellow-500/25' : 'bg-red-500/15 border-red-500/25';

  if (loading) return <div className="pt-20 text-center text-gray-500">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 max-w-2xl mx-auto px-3" data-testid="strutture-page">
      {/* Header */}
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
            <button
              key={cat.id}
              onClick={() => { setActiveTab(cat.id); setExpanded(null); setDetail(null); }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-xs font-medium border transition-all ${
                isActive
                  ? `bg-${cat.color}-500/15 border-${cat.color}-500/30 text-${cat.color}-400 shadow-[0_0_12px_rgba(251,191,36,0.08)]`
                  : 'bg-white/3 border-white/5 text-gray-500 hover:text-gray-300'
              }`}
              data-testid={`strutture-tab-${cat.id}`}
            >
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
            return (
              <div key={infra.id} className="rounded-xl border border-white/8 bg-white/3 overflow-hidden transition-all">
                {/* Card header */}
                <button
                  className="w-full flex items-center gap-3 p-3 text-left active:scale-[0.99] transition-transform"
                  onClick={() => isOpen ? (setExpanded(null), setDetail(null)) : openDetail(infra)}
                  data-testid={`struttura-card-${infra.id}`}
                >
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
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                      className="overflow-hidden"
                    >
                      <div className="px-3 pb-3 space-y-3 border-t border-white/5 pt-3">
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
                            <div className={`p-2 rounded-lg border text-center ${getPerformanceBg(detail.stats.satisfaction_index)}`}>
                              <p className="text-[9px] text-gray-400">Gradimento</p>
                              <p className={`text-sm font-bold ${getPerformanceColor(detail.stats.satisfaction_index)}`}>{detail.stats.satisfaction_index}/100</p>
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
                            <p>{detail.stats?.screens || 0} schermi</p>
                            <p>{detail.stats?.total_capacity?.toLocaleString() || 0} posti</p>
                          </div>
                        </div>

                        {/* Film Programming */}
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
                                const perf = film.imdb_rating >= 7 ? 'green' : film.imdb_rating >= 5 ? 'yellow' : 'red';
                                return (
                                  <div key={film.film_id} className={`flex items-center gap-2 p-2 rounded-lg border bg-${perf}-500/5 border-${perf}-500/15`}>
                                    {film.poster_url && <img src={film.poster_url} alt="" className="w-8 h-12 object-cover rounded" />}
                                    <div className="flex-1 min-w-0">
                                      <p className="text-xs font-semibold truncate">{film.title}</p>
                                      <div className="flex items-center gap-1.5 text-[10px] text-gray-400">
                                        <span className={`text-${perf}-400 font-bold`}>IMDb {film.imdb_rating || '?'}</span>
                                        <Badge className={`text-[8px] h-3.5 ${film.is_owned ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                          {film.is_owned ? '100%' : `${film.revenue_share_renter || 70}%`}
                                        </Badge>
                                      </div>
                                    </div>
                                    <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10" disabled={removingFilm === film.film_id} onClick={() => removeFilm(film.film_id)}>
                                      <X className="w-3.5 h-3.5" />
                                    </Button>
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
                              }}>
                                <Plus className="w-3 h-3 mr-1" /> I Miei Film
                              </Button>
                              <Button className="h-8 text-[11px] bg-blue-600 hover:bg-blue-500" onClick={async () => {
                                const r = await api.get('/films/available-for-rental'); setRentalFilms(r.data); setShowRentFilm(true);
                              }}>
                                <ShoppingBag className="w-3 h-3 mr-1" /> Affitta
                              </Button>
                            </div>
                          )}
                        </div>

                        {/* Actions row */}
                        <div className="grid grid-cols-2 gap-2">
                          <Button variant="outline" className="h-8 text-[11px] border-yellow-500/20 text-yellow-400 hover:bg-yellow-500/10" onClick={() => setShowPrices(true)}>
                            <DollarSign className="w-3 h-3 mr-1" /> Prezzi
                          </Button>
                          {upgradeInfo && upgradeInfo.current_level < upgradeInfo.max_level && (
                            <Button
                              className={`h-8 text-[11px] ${upgradeInfo.can_upgrade ? 'bg-gradient-to-r from-purple-600 to-cyan-600 text-white' : 'bg-gray-700 text-gray-400'}`}
                              disabled={!upgradeInfo.can_upgrade || upgrading}
                              onClick={() => handleUpgrade(infra.id)}
                              data-testid={`upgrade-struttura-${infra.id}`}
                            >
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
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowPrices(false)}>Annulla</Button>
            <Button size="sm" onClick={savePricesFn} disabled={savingPrices} className="bg-yellow-500 text-black">{savingPrices ? '...' : 'Salva'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
