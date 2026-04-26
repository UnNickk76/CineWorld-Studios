// CineWorld — Mercato Unificato v2
// 5 sezioni: Film, Serie TV, Anime, Infrastrutture, Diritti TV
// Supporta: prezzo fisso, asta, offerta libera

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import {
  Store, Film, Tv, Sparkles, Building2, Radio, Gavel, Tag, Send,
  Loader2, Clock, Star, TrendingUp, Search, Filter, ChevronRight,
  Trash2, DollarSign, Crown, Zap, X, Users
} from 'lucide-react';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import TalentMarketModal from '../components/TalentMarketModal';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};
function fmtPrice(n) { if (n >= 1e9) return `$${(n/1e9).toFixed(1)}B`; if (n >= 1e6) return `$${(n/1e6).toFixed(1)}M`; if (n >= 1e3) return `$${(n/1e3).toFixed(0)}K`; return `$${n}`; }

const SECTIONS = [
  { id: 'all', label: 'Tutto', icon: Store, color: 'text-white' },
  { id: 'film', label: 'Film', icon: Film, color: 'text-yellow-400' },
  { id: 'series', label: 'Serie', icon: Tv, color: 'text-blue-400' },
  { id: 'anime', label: 'Anime', icon: Sparkles, color: 'text-orange-400' },
  { id: 'infrastructure', label: 'Infra', icon: Building2, color: 'text-emerald-400' },
  { id: 'tv_rights', label: 'Dir.TV', icon: Radio, color: 'text-purple-400' },
  { id: 'npc', label: 'NPC', icon: Users, color: 'text-pink-400' },
];

const SALE_ICONS = { fixed: Tag, auction: Gavel, offer: Send };

export default function MarketV2Page() {
  const { api, user } = useContext(AuthContext);
  const [section, setSection] = useState('all');
  const [listings, setListings] = useState([]);
  const [counts, setCounts] = useState({});
  const [deal, setDeal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedListing, setSelectedListing] = useState(null);
  const [tab, setTab] = useState('browse'); // browse, my, stats
  const [myData, setMyData] = useState(null);
  const [stats, setStats] = useState(null);
  const [bidAmount, setBidAmount] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [showFilters, setShowFilters] = useState(false);
  const [showTalentMarketModal, setShowTalentMarketModal] = useState(false);

  // Sell modal
  const [showSellModal, setShowSellModal] = useState(false);
  const [sellForm, setSellForm] = useState({ item_type: 'film', item_id: '', sale_type: 'fixed', price: '', auction_hours: 48, description: '' });
  const [myItems, setMyItems] = useState({ films: [], series: [], infrastructure: [] });

  const filteredListings = searchQuery
    ? listings.filter(l => l.title?.toLowerCase().includes(searchQuery.toLowerCase()))
    : listings;
  const loadMarket = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (section !== 'all') params.set('section', section);
      if (sortBy !== 'newest') params.set('sort_by', sortBy);
      const qs = params.toString() ? `?${params.toString()}` : '';
      const res = await api.get(`/market/browse${qs}`);
      setListings(res.data.listings || []);
      setCounts(res.data.counts || {});
      setDeal(res.data.deal_of_day);
    } catch { toast.error('Errore caricamento mercato'); }
    setLoading(false);
  }, [api, section, sortBy]);

  const loadMyData = useCallback(async () => {
    try {
      const res = await api.get('/market/my-listings');
      setMyData(res.data);
    } catch { /* */ }
  }, [api]);

  const loadStats = useCallback(async () => {
    try {
      const res = await api.get('/market/stats');
      setStats(res.data);
    } catch { /* */ }
  }, [api]);

  useEffect(() => { loadMarket(); }, [loadMarket]);
  useEffect(() => { if (tab === 'my') loadMyData(); }, [tab, loadMyData]);
  useEffect(() => { if (tab === 'stats') loadStats(); }, [tab, loadStats]);

  // Load sellable items
  const loadMyItems = async () => {
    try {
      const [films, series, infra] = await Promise.all([
        api.get('/films/my').catch(() => ({ data: [] })),
        api.get('/series-pipeline/my?series_type=all').catch(() => ({ data: { series: [] } })),
        api.get('/infrastructure/my').catch(() => ({ data: [] })),
      ]);
      setMyItems({
        films: Array.isArray(films.data) ? films.data : [],
        series: series.data?.series || [],
        infrastructure: Array.isArray(infra.data) ? infra.data : infra.data?.infrastructure || [],
      });
    } catch { /* */ }
  };

  const handleBuy = async (listing) => {
    setActionLoading(true);
    try {
      if (listing.item_type === 'tv_rights') {
        const res = await api.post(`/market/tv-rights/buy/${listing.id}`);
        toast.success(res.data.message);
      } else {
        const res = await api.post('/market/buy', { listing_id: listing.id });
        toast.success(res.data.message);
      }
      setSelectedListing(null);
      loadMarket();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore acquisto'); }
    setActionLoading(false);
  };

  const handleBid = async (listing) => {
    const amount = parseInt(bidAmount);
    if (!amount || amount <= 0) { toast.error('Importo non valido'); return; }
    setActionLoading(true);
    try {
      const res = await api.post('/market/bid', { listing_id: listing.id, amount });
      toast.success(res.data.message);
      setBidAmount('');
      setSelectedListing(null);
      loadMarket();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore offerta'); }
    setActionLoading(false);
  };

  const handleOffer = async (listing) => {
    const amount = parseInt(bidAmount);
    if (!amount || amount <= 0) { toast.error('Importo non valido'); return; }
    setActionLoading(true);
    try {
      const res = await api.post('/market/offer', { listing_id: listing.id, amount });
      toast.success(res.data.message);
      setBidAmount('');
      setSelectedListing(null);
      loadMarket();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore offerta'); }
    setActionLoading(false);
  };

  const handleSell = async () => {
    if (!sellForm.item_id || !sellForm.price) { toast.error('Compila tutti i campi'); return; }
    setActionLoading(true);
    try {
      const res = await api.post('/market/list', {
        item_type: sellForm.item_type,
        item_id: sellForm.item_id,
        sale_type: sellForm.sale_type,
        price: parseInt(sellForm.price),
        auction_hours: sellForm.auction_hours,
        description: sellForm.description,
      });
      toast.success(res.data.message);
      setShowSellModal(false);
      setSellForm({ item_type: 'film', item_id: '', sale_type: 'fixed', price: '', auction_hours: 48, description: '' });
      loadMarket();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore creazione listing'); }
    setActionLoading(false);
  };

  const handleCancel = async (listingId) => {
    try {
      await api.delete(`/market/listing/${listingId}`);
      toast.success('Listing cancellato');
      loadMyData();
      loadMarket();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const handleAcceptOffer = async (listingId, offerId) => {
    setActionLoading(true);
    try {
      const res = await api.post(`/market/offer/${listingId}/accept/${offerId}`);
      toast.success(res.data.message);
      loadMyData();
      loadMarket();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const totalCount = Object.values(counts).reduce((a, b) => a + b, 0);

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pt-14 pb-20" data-testid="market-page">
      {/* Header */}
      <div className="px-3 pt-3 pb-2">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <Store className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold">Mercato</h1>
              <p className="text-[9px] text-gray-500">{totalCount} listing attivi</p>
            </div>
          </div>
          <Button size="sm" className="h-7 text-[10px] bg-emerald-600 hover:bg-emerald-700"
            onClick={() => { setShowSellModal(true); loadMyItems(); }} data-testid="sell-btn">
            <DollarSign className="w-3 h-3 mr-1" /> Vendi
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-2">
          {['browse', 'my', 'stats'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`flex-1 py-1.5 text-[10px] font-medium rounded-md ${tab === t ? 'bg-emerald-500/15 text-emerald-400' : 'bg-white/5 text-gray-500'}`}
              data-testid={`market-tab-${t}`}>
              {t === 'browse' ? 'Sfoglia' : t === 'my' ? 'I Miei' : 'Statistiche'}
            </button>
          ))}
        </div>

        {/* Section filter (browse only) */}
        {tab === 'browse' && (
          <>
          <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
            {SECTIONS.map(s => (
              <button key={s.id} onClick={() => {
                if (s.id === 'npc') {
                  setShowTalentMarketModal(true);
                } else {
                  setSection(s.id);
                }
              }}
                className={`flex items-center gap-1 px-2 py-1 rounded-md text-[9px] font-medium whitespace-nowrap transition
                  ${s.id === 'npc' ? 'bg-pink-500/15 text-pink-200 border border-pink-500/30' :
                    section === s.id ? 'bg-white/10 text-white' : 'bg-white/[0.03] text-gray-500'}`}
                data-testid={`market-section-${s.id}`}>
                <s.icon className={`w-3 h-3 ${s.id === 'npc' ? 'text-pink-300' : (section === s.id ? s.color : '')}`} />
                {s.label}
                {s.id !== 'all' && s.id !== 'npc' && counts[s.id] > 0 && <span className="text-[8px] opacity-50">{counts[s.id]}</span>}
              </button>
            ))}
          </div>
          <div className="flex gap-1.5 mt-1.5">
            <div className="flex-1 relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-500" />
              <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Cerca titolo..."
                className="w-full h-7 pl-6 pr-2 bg-white/5 border border-white/10 rounded-md text-[10px] text-white" data-testid="market-search" />
            </div>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)}
              className="h-7 bg-white/5 border border-white/10 rounded-md text-[9px] text-gray-400 px-1.5" data-testid="market-sort">
              <option value="newest">Recenti</option>
              <option value="price_asc">Prezzo basso</option>
              <option value="price_desc">Prezzo alto</option>
              <option value="ending_soon">Scadenza</option>
            </select>
          </div>
          </>
        )}
      </div>

      <div className="px-3">
        {/* BROWSE TAB */}
        {tab === 'browse' && (
          loading ? (
            <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 text-emerald-400 animate-spin" /></div>
          ) : filteredListings.length === 0 ? (
            <div className="text-center py-16">
              <Store className="w-10 h-10 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">Nessun listing trovato</p>
            </div>
          ) : (
            <div className="space-y-2">
              {deal && (
                <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }}
                  className="p-2.5 rounded-xl bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20 cursor-pointer"
                  onClick={() => setSelectedListing(deal)} data-testid="deal-of-day">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Zap className="w-3 h-3 text-amber-400" />
                    <span className="text-[9px] font-bold text-amber-400">AFFARE DEL GIORNO</span>
                  </div>
                  <p className="text-xs font-bold truncate">{deal.title}</p>
                  <p className="text-[10px] text-amber-400 font-bold">{fmtPrice(deal.price)}</p>
                </motion.div>
              )}
              {filteredListings.map(l => (
                <ListingCard key={l.id} listing={l} onClick={() => { setSelectedListing(l); setBidAmount(''); }} />
              ))}
            </div>
          )
        )}

        {/* MY TAB */}
        {tab === 'my' && myData && (
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-bold text-emerald-400 mb-2">In Vendita ({myData.active?.length || 0})</h3>
              {myData.active?.length === 0 ? (
                <p className="text-[10px] text-gray-500 py-4 text-center">Nessun listing attivo</p>
              ) : myData.active?.map(l => (
                <div key={l.id} className="p-2 bg-white/[0.03] rounded-lg border border-white/5 mb-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold truncate">{l.title}</p>
                      <p className="text-[9px] text-gray-500">{l.sale_type === 'auction' ? 'Asta' : l.sale_type === 'offer' ? 'Offerta' : 'Fisso'} — {fmtPrice(l.price)}</p>
                      {l.offers?.length > 0 && (
                        <div className="mt-1 space-y-0.5">
                          {l.offers.filter(o => o.status === 'pending').map(o => (
                            <div key={o.id} className="flex items-center gap-2 text-[9px]">
                              <span className="text-amber-400">{o.bidder_name}: {fmtPrice(o.amount)}</span>
                              <button onClick={() => handleAcceptOffer(l.id, o.id)} className="text-green-400 font-bold hover:underline" data-testid={`accept-offer-${o.id}`}>Accetta</button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <button onClick={() => handleCancel(l.id)} className="text-red-400 p-1" data-testid={`cancel-listing-${l.id}`}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div>
              <h3 className="text-xs font-bold text-cyan-400 mb-2">Storico Transazioni</h3>
              {myData.transactions?.length === 0 ? (
                <p className="text-[10px] text-gray-500 py-4 text-center">Nessuna transazione</p>
              ) : myData.transactions?.map(t => (
                <div key={t.id} className="flex items-center justify-between p-1.5 border-b border-white/5 text-[10px]">
                  <div className="flex-1 min-w-0">
                    <span className={`font-bold ${t.i_am_seller ? 'text-green-400' : 'text-red-400'}`}>
                      {t.i_am_seller ? '+' : '-'}{fmtPrice(t.i_am_seller ? t.seller_received : t.price)}
                    </span>
                    <span className="text-gray-400 ml-1.5 truncate">{t.title}</span>
                  </div>
                  <span className="text-gray-600 text-[8px]">{t.other_name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STATS TAB */}
        {tab === 'stats' && stats && (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-2">
              <StatBox label="Listing" value={stats.total_active_listings} />
              <StatBox label="Transazioni" value={stats.total_transactions} />
              <StatBox label="Mie Vendite" value={stats.my_stats?.sales || 0} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <StatBox label="Acquisti" value={stats.my_stats?.purchases || 0} />
              <StatBox label="Revenue" value={fmtPrice(stats.my_stats?.total_revenue || 0)} />
            </div>
            {Object.keys(stats.avg_prices || {}).length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-gray-400 mb-2">Prezzi Medi</h3>
                {Object.entries(stats.avg_prices).map(([type, d]) => (
                  <div key={type} className="flex justify-between text-[10px] py-1 border-b border-white/5">
                    <span className="text-gray-400 capitalize">{type}</span>
                    <span className="text-emerald-400 font-bold">{fmtPrice(d.avg_price)} ({d.count} venduti)</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ─── Listing Detail Modal ─── */}
      <Dialog open={!!selectedListing} onOpenChange={(o) => { if (!o) setSelectedListing(null); }}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-[360px] p-0 [&>button]:hidden" data-testid="listing-detail-modal">
          {selectedListing && (
            <>
              <div className="p-3 border-b border-white/5">
                <div className="flex items-center gap-3">
                  {posterSrc(selectedListing.poster_url) ? (
                    <img src={posterSrc(selectedListing.poster_url)} alt="" className="w-14 h-20 rounded-md object-cover" />
                  ) : (
                    <div className="w-14 h-20 rounded-md bg-gray-800 flex items-center justify-center"><Film className="w-5 h-5 text-gray-600" /></div>
                  )}
                  <div className="flex-1 min-w-0">
                    <Badge className={`text-[8px] mb-1 border-0 ${selectedListing.item_type === 'tv_rights' ? 'bg-purple-500/15 text-purple-400' : selectedListing.item_type === 'infrastructure' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-yellow-500/15 text-yellow-400'}`}>
                      {selectedListing.item_type === 'tv_rights' ? 'Diritti TV' : selectedListing.item_type.toUpperCase()}
                    </Badge>
                    <h3 className="text-sm font-bold truncate">{selectedListing.title}</h3>
                    <p className="text-[9px] text-gray-500">da {selectedListing.seller_name}</p>
                    {selectedListing.genre && <p className="text-[9px] text-gray-600">{selectedListing.genre}</p>}
                    {selectedListing.quality_score > 0 && (
                      <div className="flex items-center gap-1 mt-0.5">
                        <Star className="w-2.5 h-2.5 text-amber-400" />
                        <span className="text-[9px] text-amber-400">{(selectedListing.quality_score / 10).toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                  <button onClick={() => setSelectedListing(null)} className="text-gray-500 self-start"><X className="w-4 h-4" /></button>
                </div>
              </div>

              <div className="p-3 space-y-3">
                {/* Extra info */}
                {selectedListing.extra_info?.royalty_pct && (
                  <div className="flex items-center gap-2 p-2 bg-purple-500/5 rounded-lg border border-purple-500/10">
                    <Crown className="w-3.5 h-3.5 text-purple-400" />
                    <span className="text-[10px] text-purple-300">Royalty: {selectedListing.extra_info.royalty_pct}% al creatore originale</span>
                  </div>
                )}

                {/* Price */}
                <div className="text-center py-2">
                  <p className="text-[9px] text-gray-500 uppercase">
                    {selectedListing.sale_type === 'auction' ? 'Offerta attuale' : selectedListing.sale_type === 'offer' ? 'Prezzo richiesto' : 'Prezzo'}
                  </p>
                  <p className="text-2xl font-bold text-emerald-400 font-['Bebas_Neue'] tracking-wide">
                    {fmtPrice(selectedListing.current_bid || selectedListing.price)}
                  </p>
                  {selectedListing.time_remaining && (
                    <div className="flex items-center justify-center gap-1 mt-1">
                      <Clock className="w-3 h-3 text-amber-400" />
                      <span className="text-[10px] text-amber-400">{selectedListing.time_remaining}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                {!selectedListing.is_mine && (
                  <>
                    {selectedListing.sale_type === 'fixed' && (
                      <Button className="w-full bg-emerald-600 hover:bg-emerald-700 text-sm" onClick={() => handleBuy(selectedListing)}
                        disabled={actionLoading} data-testid="buy-now-btn">
                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Tag className="w-4 h-4 mr-1" />}
                        Compra Ora — {fmtPrice(selectedListing.price)}
                      </Button>
                    )}
                    {(selectedListing.sale_type === 'auction' || selectedListing.sale_type === 'offer') && (
                      <div className="flex gap-2">
                        <input type="number" value={bidAmount} onChange={e => setBidAmount(e.target.value)}
                          className="flex-1 h-9 px-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white"
                          placeholder={`Min ${fmtPrice((selectedListing.current_bid || selectedListing.price) * 1.05 + 1000)}`}
                          data-testid="bid-input" />
                        <Button className="bg-amber-600 hover:bg-amber-700 text-xs h-9 px-3"
                          onClick={() => selectedListing.sale_type === 'auction' ? handleBid(selectedListing) : handleOffer(selectedListing)}
                          disabled={actionLoading} data-testid="place-bid-btn">
                          {actionLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Gavel className="w-3 h-3 mr-1" />}
                          {selectedListing.sale_type === 'auction' ? 'Offri' : 'Proponi'}
                        </Button>
                      </div>
                    )}
                  </>
                )}
                {selectedListing.description && (
                  <p className="text-[10px] text-gray-400 italic">"{selectedListing.description}"</p>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* ─── Sell Modal ─── */}
      <Dialog open={showSellModal} onOpenChange={(o) => { if (!o) setShowSellModal(false); }}>
        <DialogContent className="bg-[#0F0F10] border-white/10 max-w-[360px] [&>button]:hidden" data-testid="sell-modal">
          <DialogHeader>
            <DialogTitle className="text-sm flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-400" /> Metti in Vendita
            </DialogTitle>
            <DialogDescription className="text-[10px] text-gray-400">Scegli cosa vendere e il tipo di vendita</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            {/* Type */}
            <div>
              <label className="text-[9px] text-gray-500 mb-1 block">Tipo</label>
              <div className="grid grid-cols-3 gap-1">
                {[['film', 'Film'], ['series', 'Serie/Anime'], ['infrastructure', 'Infrastruttura']].map(([v, l]) => (
                  <button key={v} onClick={() => setSellForm({ ...sellForm, item_type: v, item_id: '' })}
                    className={`py-1.5 text-[10px] rounded-md ${sellForm.item_type === v ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20' : 'bg-white/5 text-gray-500 border border-transparent'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            {/* Item select */}
            <div>
              <label className="text-[9px] text-gray-500 mb-1 block">Oggetto</label>
              <select value={sellForm.item_id} onChange={e => setSellForm({ ...sellForm, item_id: e.target.value })}
                className="w-full h-8 bg-white/5 border border-white/10 rounded-md text-[10px] text-white px-2" data-testid="sell-item-select">
                <option value="">Seleziona...</option>
                {sellForm.item_type === 'film' && myItems.films.map(f => (
                  <option key={f.id} value={f.id}>{f.title}</option>
                ))}
                {sellForm.item_type === 'series' && myItems.series.map(s => (
                  <option key={s.id} value={s.id}>{s.title} ({s.type === 'anime' ? 'Anime' : 'Serie'})</option>
                ))}
                {sellForm.item_type === 'infrastructure' && myItems.infrastructure.map(i => (
                  <option key={i.id} value={i.id}>{i.custom_name || i.type} (Lv.{i.level})</option>
                ))}
              </select>
            </div>
            {/* Sale type */}
            <div>
              <label className="text-[9px] text-gray-500 mb-1 block">Tipo Vendita</label>
              <div className="grid grid-cols-3 gap-1">
                {[['fixed', 'Fisso'], ['auction', 'Asta'], ['offer', 'Offerta']].map(([v, l]) => (
                  <button key={v} onClick={() => setSellForm({ ...sellForm, sale_type: v })}
                    className={`py-1.5 text-[10px] rounded-md ${sellForm.sale_type === v ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' : 'bg-white/5 text-gray-500 border border-transparent'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            {/* Price */}
            <div>
              <label className="text-[9px] text-gray-500 mb-1 block">{sellForm.sale_type === 'auction' ? 'Prezzo Base' : 'Prezzo'}</label>
              <input type="number" value={sellForm.price} onChange={e => setSellForm({ ...sellForm, price: e.target.value })}
                className="w-full h-8 bg-white/5 border border-white/10 rounded-md text-sm text-white px-2" placeholder="$100,000" data-testid="sell-price-input" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" size="sm" className="text-xs border-white/10" onClick={() => setShowSellModal(false)}>Annulla</Button>
            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-xs" onClick={handleSell} disabled={actionLoading} data-testid="confirm-sell-btn">
              {actionLoading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <DollarSign className="w-3 h-3 mr-1" />}
              Metti in Vendita
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* NPC Talent Market modal — Sistema Talenti Vivente */}
      <TalentMarketModal
        open={showTalentMarketModal}
        onClose={() => setShowTalentMarketModal(false)}
      />
    </div>
  );
}

function ListingCard({ listing, onClick }) {
  const SaleIcon = SALE_ICONS[listing.sale_type] || Tag;
  return (
    <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}
      className="flex gap-2.5 p-2 bg-white/[0.02] rounded-lg border border-white/5 cursor-pointer active:scale-[0.98] transition-transform"
      onClick={onClick} data-testid={`listing-${listing.id}`}>
      {posterSrc(listing.poster_url) ? (
        <img src={posterSrc(listing.poster_url)} alt="" className="w-11 h-16 rounded-md object-cover flex-shrink-0" />
      ) : (
        <div className="w-11 h-16 rounded-md bg-gray-800 flex items-center justify-center flex-shrink-0"><Film className="w-4 h-4 text-gray-700" /></div>
      )}
      <div className="flex-1 min-w-0 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <p className="text-[11px] font-bold truncate">{listing.title}</p>
            <Badge className="text-[7px] border-0 bg-white/5 text-gray-400 flex-shrink-0">{listing.item_type === 'tv_rights' ? 'DIR.TV' : listing.item_type.toUpperCase()}</Badge>
          </div>
          <p className="text-[9px] text-gray-500">{listing.seller_name} {listing.genre ? `- ${listing.genre}` : ''}</p>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <SaleIcon className="w-3 h-3 text-emerald-400" />
            <span className="text-xs font-bold text-emerald-400">{fmtPrice(listing.current_bid || listing.price)}</span>
          </div>
          {listing.time_remaining && <span className="text-[8px] text-amber-400 flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" />{listing.time_remaining}</span>}
          {listing.bids?.length > 0 && <span className="text-[8px] text-gray-500">{listing.bids.length} offerte</span>}
        </div>
      </div>
      <ChevronRight className="w-4 h-4 text-gray-600 self-center flex-shrink-0" />
    </motion.div>
  );
}

function StatBox({ label, value }) {
  return (
    <div className="bg-white/[0.03] rounded-lg border border-white/5 p-2.5 text-center">
      <div className="text-lg font-bold text-white">{value}</div>
      <div className="text-[8px] text-gray-500">{label}</div>
    </div>
  );
}
