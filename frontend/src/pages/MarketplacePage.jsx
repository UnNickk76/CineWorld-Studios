// CineWorld Studio's - MarketplacePage
// Extracted from App.js for modularity

import React, { useState, useEffect, useRef, useCallback, useMemo, useContext } from 'react';
import { useNavigate, useLocation, useSearchParams, useParams } from 'react-router-dom';
import { AuthContext, LanguageContext, PlayerPopupContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ScrollArea } from '../components/ui/scroll-area';
import { Slider } from '../components/ui/slider';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '../components/ui/alert-dialog';
import { Checkbox } from '../components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import {
  Film, Star, Award, TrendingUp, Clock, Play, Pause, Volume2, Users, Clapperboard,
  Send, Image, ChevronRight, ChevronDown, ChevronLeft, Menu, X, Settings,
  Zap, Globe, Trophy, Shield, Swords, Heart, MessageSquare, Bell, Home,
  Plus, Minus, Search, Filter, Trash2, Edit, Save, Copy, ExternalLink,
  Check, AlertCircle, Info, HelpCircle, Loader2, RefreshCw, Download,
  Eye, EyeOff, Lock, Unlock, Mail, Phone, Calendar, MapPin, Building,
  Sparkles, Flame, Target, Gamepad2, Music, Palette, Camera, Video,
  BookOpen, Newspaper, Gift, Crown, Medal, Gem, Coins, Wallet,
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, MoreHorizontal, MoreVertical,
  ChevronUp, ChevronsUpDown, Lightbulb, Megaphone, Share2, ThumbsUp,
  ThumbsDown, Bookmark, Flag, AlertTriangle, XCircle, CheckCircle,
  BarChart3, PieChart, Activity, Percent, DollarSign, Hash, AtSign,
  Scissors, Wand2, Brush, Layers, Grid, List, LayoutGrid, Table,
  CircleDollarSign, Store, Package, ShoppingCart, Tag, Receipt,
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';

// useTranslations imported from contexts

const MarketplacePage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [listings, setListings] = useState([]);
  const [myListings, setMyListings] = useState([]);
  const [myOffers, setMyOffers] = useState([]);
  const [myInfra, setMyInfra] = useState([]);
  const [canTrade, setCanTrade] = useState(false);
  const [requiredLevel, setRequiredLevel] = useState(15);
  const [currentLevel, setCurrentLevel] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('browse');
  
  // Sell dialog state
  const [showSellDialog, setShowSellDialog] = useState(false);
  const [selectedInfra, setSelectedInfra] = useState(null);
  const [valuation, setValuation] = useState(null);
  const [askingPrice, setAskingPrice] = useState(0);
  const [listing, setListing] = useState(false);
  
  // Offer dialog state
  const [showOfferDialog, setShowOfferDialog] = useState(false);
  const [selectedListing, setSelectedListing] = useState(null);
  const [offerPrice, setOfferPrice] = useState(0);
  const [making, setMaking] = useState(false);

  useEffect(() => {
    loadData();
  }, [api]);

  const loadData = async () => {
    try {
      const [marketRes, myRes, infraRes] = await Promise.all([
        api.get('/marketplace'),
        api.get('/marketplace/my-listings'),
        api.get('/infrastructure/my')
      ]);
      setListings(marketRes.data.listings);
      setCanTrade(marketRes.data.can_trade);
      setRequiredLevel(marketRes.data.required_level);
      setCurrentLevel(marketRes.data.current_level);
      setMyListings(myRes.data.my_listings);
      setMyOffers(myRes.data.my_offers);
      setMyInfra(infraRes.data.infrastructure);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const openSellDialog = async (infra) => {
    setSelectedInfra(infra);
    try {
      const res = await api.get(`/infrastructure/${infra.id}/valuation`);
      setValuation(res.data);
      setAskingPrice(res.data.suggested_price);
      setShowSellDialog(true);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella valutazione');
    }
  };

  const createListing = async () => {
    setListing(true);
    try {
      await api.post('/marketplace/list', {
        infrastructure_id: selectedInfra.id,
        asking_price: askingPrice
      });
      toast.success('Infrastruttura messa in vendita!');
      setShowSellDialog(false);
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setListing(false);
    }
  };

  const cancelListing = async (listingId) => {
    try {
      await api.delete(`/marketplace/listing/${listingId}`);
      toast.success('Annuncio cancellato');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const openOfferDialog = (listing) => {
    setSelectedListing(listing);
    setOfferPrice(listing.asking_price);
    setShowOfferDialog(true);
  };

  const makeOffer = async () => {
    setMaking(true);
    try {
      await api.post('/marketplace/offer', {
        listing_id: selectedListing.id,
        offer_price: offerPrice
      });
      toast.success('Offerta inviata!');
      setShowOfferDialog(false);
      loadData();
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setMaking(false);
    }
  };

  const acceptOffer = async (listingId, offerId) => {
    try {
      const res = await api.post(`/marketplace/offer/${listingId}/accept/${offerId}`);
      toast.success(`Vendita completata! Hai ricevuto $${res.data.sold_price.toLocaleString()}`);
      loadData();
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const rejectOffer = async (listingId, offerId) => {
    try {
      await api.post(`/marketplace/offer/${listingId}/reject/${offerId}`);
      toast.success('Offerta rifiutata');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  if (loading) return <div className="pt-20 text-center">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="marketplace-page">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
          <ShoppingBag className="w-7 h-7 text-yellow-500" /> Marketplace Infrastrutture
        </h1>
        {!canTrade && (
          <Badge className="bg-red-500/20 text-red-400 flex items-center gap-1">
            <Lock className="w-3 h-3" /> Richiesto Lv.{requiredLevel} (Attuale: Lv.{currentLevel})
          </Badge>
        )}
      </div>

      {!canTrade && (
        <Card className="bg-yellow-500/10 border-yellow-500/30 mb-4">
          <CardContent className="p-4 flex items-center gap-3">
            <Lock className="w-8 h-8 text-yellow-500" />
            <div>
              <h3 className="font-semibold">Marketplace Bloccato</h3>
              <p className="text-sm text-gray-400">
                Devi raggiungere il livello {requiredLevel} per comprare e vendere infrastrutture con altri giocatori. 
                Attualmente sei al livello {currentLevel}.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="browse">Sfoglia ({listings.length})</TabsTrigger>
          <TabsTrigger value="my-listings">I Miei Annunci ({myListings.filter(l => l.status === 'active').length})</TabsTrigger>
          <TabsTrigger value="sell">Vendi</TabsTrigger>
        </TabsList>

        <TabsContent value="browse">
          {listings.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
              <Building className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <h3 className="text-lg mb-2">Nessun annuncio attivo</h3>
              <p className="text-gray-400">Al momento non ci sono infrastrutture in vendita.</p>
            </Card>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {listings.map(listing => (
                <Card key={listing.id} className="bg-[#1A1A1A] border-white/10">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-12 h-12 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                        <Building className="w-6 h-6 text-yellow-500" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold">{listing.infrastructure.custom_name}</h3>
                        <p className="text-xs text-gray-400">{listing.infrastructure.city?.name}, {listing.infrastructure.country}</p>
                      </div>
                    </div>
                    <div className="space-y-1 text-sm mb-3">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Tipo:</span>
                        <span>{listing.infrastructure.type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Ricavi totali:</span>
                        <span className="text-green-400">${listing.infrastructure.total_revenue?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Film in programmazione:</span>
                        <span>{listing.infrastructure.films_showing}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Venditore:</span>
                        <span>{listing.seller?.nickname}</span>
                      </div>
                    </div>
                    <div className="p-2 bg-yellow-500/10 rounded border border-yellow-500/20 mb-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Prezzo richiesto:</span>
                        <span className="text-yellow-500 font-bold text-lg">${listing.asking_price?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-400">
                        <span>Valore stimato:</span>
                        <span>${listing.calculated_value?.toLocaleString()}</span>
                      </div>
                    </div>
                    <Button 
                      className="w-full bg-yellow-500 text-black hover:bg-yellow-400" 
                      disabled={!canTrade || listing.seller_id === user?.id}
                      onClick={() => openOfferDialog(listing)}
                    >
                      {listing.seller_id === user?.id ? 'Il tuo annuncio' : 'Fai un\'offerta'}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="my-listings">
          {myListings.filter(l => l.status === 'active').length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
              <Ticket className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <h3 className="text-lg mb-2">Nessun annuncio attivo</h3>
              <p className="text-gray-400">Non hai infrastrutture in vendita.</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {myListings.filter(l => l.status === 'active').map(listing => (
                <Card key={listing.id} className="bg-[#1A1A1A] border-white/10">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Building className="w-8 h-8 text-yellow-500" />
                        <div>
                          <h3 className="font-semibold">{listing.infrastructure.custom_name}</h3>
                          <p className="text-xs text-gray-400">Prezzo: ${listing.asking_price?.toLocaleString()}</p>
                        </div>
                      </div>
                      <Button variant="destructive" size="sm" onClick={() => cancelListing(listing.id)}>
                        <X className="w-4 h-4" /> Annulla
                      </Button>
                    </div>
                    {listing.offers?.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-semibold text-sm">Offerte ricevute ({listing.offers.filter(o => o.status === 'pending').length})</h4>
                        {listing.offers.filter(o => o.status === 'pending').map(offer => (
                          <div key={offer.id} className="flex items-center justify-between p-2 bg-white/5 rounded">
                            <div>
                              <p className="font-semibold">{offer.buyer_nickname}</p>
                              <p className="text-yellow-500">${offer.offer_price?.toLocaleString()}</p>
                            </div>
                            <div className="flex gap-2">
                              <Button size="sm" className="bg-green-500 hover:bg-green-400" onClick={() => acceptOffer(listing.id, offer.id)}>
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button size="sm" variant="destructive" onClick={() => rejectOffer(listing.id, offer.id)}>
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="sell">
          {myInfra.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
              <Building className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <h3 className="text-lg mb-2">Nessuna infrastruttura</h3>
              <p className="text-gray-400 mb-4">Non hai infrastrutture da vendere.</p>
              <Button onClick={() => navigate('/infrastructure')} className="bg-yellow-500 text-black">
                Acquista Infrastrutture
              </Button>
            </Card>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {myInfra.map(infra => {
                const isListed = myListings.some(l => l.infrastructure_id === infra.id && l.status === 'active');
                return (
                  <Card key={infra.id} className={`bg-[#1A1A1A] border-white/10 ${isListed ? 'opacity-60' : ''}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                          <Building className="w-5 h-5 text-yellow-500" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm">{infra.custom_name}</h3>
                          <p className="text-xs text-gray-400">{infra.city?.name}, {infra.country}</p>
                        </div>
                      </div>
                      <div className="text-xs text-gray-400 mb-3">
                        Tipo: {infra.type} • Ricavi: ${infra.total_revenue?.toLocaleString()}
                      </div>
                      <Button 
                        className="w-full" 
                        disabled={!canTrade || isListed}
                        onClick={() => openSellDialog(infra)}
                      >
                        {isListed ? 'Già in vendita' : 'Metti in vendita'}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Sell Dialog */}
      <Dialog open={showSellDialog} onOpenChange={setShowSellDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl">Vendi Infrastruttura</DialogTitle>
            <DialogDescription>Imposta il prezzo per {selectedInfra?.custom_name}</DialogDescription>
          </DialogHeader>
          {valuation && (
            <div className="space-y-4">
              <div className="p-3 bg-white/5 rounded border border-white/10">
                <h4 className="font-semibold mb-2">Valutazione</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-gray-400">Valore base:</span> <span>${valuation.factors?.base_value?.toLocaleString()}</span></div>
                  <div><span className="text-gray-400">Moltiplicatore livello:</span> <span>x{valuation.factors?.level_multiplier}</span></div>
                  <div><span className="text-gray-400">Moltiplicatore fama:</span> <span>x{valuation.factors?.fame_multiplier}</span></div>
                  <div><span className="text-gray-400">Bonus ricavi:</span> <span>+${valuation.factors?.revenue_bonus?.toLocaleString()}</span></div>
                </div>
              </div>
              <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
                <div className="flex justify-between mb-1">
                  <span>Valore stimato:</span>
                  <span className="text-yellow-500 font-bold">${valuation.calculated_value?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Range prezzo:</span>
                  <span>${valuation.min_price?.toLocaleString()} - ${valuation.max_price?.toLocaleString()}</span>
                </div>
              </div>
              <div>
                <Label className="text-xs">Prezzo richiesto</Label>
                <Input 
                  type="number" 
                  value={askingPrice} 
                  onChange={e => setAskingPrice(parseInt(e.target.value) || 0)}
                  min={valuation.min_price}
                  max={valuation.max_price}
                  className="h-10 bg-black/20 border-white/10"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Min: ${valuation.min_price?.toLocaleString()} • Max: ${valuation.max_price?.toLocaleString()}
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSellDialog(false)}>Annulla</Button>
            <Button 
              onClick={createListing} 
              disabled={listing || askingPrice < valuation?.min_price || askingPrice > valuation?.max_price}
              className="bg-yellow-500 text-black"
            >
              {listing ? 'Pubblicando...' : 'Pubblica Annuncio'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Offer Dialog */}
      <Dialog open={showOfferDialog} onOpenChange={setShowOfferDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl">Fai un'offerta</DialogTitle>
            <DialogDescription>{selectedListing?.infrastructure?.custom_name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-3 bg-white/5 rounded border border-white/10">
              <div className="flex justify-between mb-1">
                <span className="text-gray-400">Prezzo richiesto:</span>
                <span className="text-yellow-500">${selectedListing?.asking_price?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>Valore stimato:</span>
                <span>${selectedListing?.calculated_value?.toLocaleString()}</span>
              </div>
            </div>
            <div>
              <Label className="text-xs">La tua offerta</Label>
              <Input 
                type="number" 
                value={offerPrice} 
                onChange={e => setOfferPrice(parseInt(e.target.value) || 0)}
                min={1}
                className="h-10 bg-black/20 border-white/10"
              />
            </div>
            <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
              <div className="flex justify-between">
                <span>I tuoi fondi:</span>
                <span className={user?.funds >= offerPrice ? 'text-green-400' : 'text-red-400'}>
                  ${user?.funds?.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowOfferDialog(false)}>Annulla</Button>
            <Button 
              onClick={makeOffer} 
              disabled={making || offerPrice < 1 || user?.funds < offerPrice}
              className="bg-yellow-500 text-black"
            >
              {making ? 'Inviando...' : 'Invia Offerta'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Festivals Page

export default MarketplacePage;
