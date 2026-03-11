// CineWorld Studio's - InfrastructurePage
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding,
  Car, Building2, GraduationCap, ArrowUpCircle, ShoppingBag, Landmark
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';

// useTranslations imported from contexts

const InfrastructurePage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [infraTypes, setInfraTypes] = useState([]);
  const [myInfra, setMyInfra] = useState({ infrastructure: [], grouped: {} });
  const [cities, setCities] = useState({});
  const [selectedType, setSelectedType] = useState(null);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [customName, setCustomName] = useState('');
  const [purchasing, setPurchasing] = useState(false);
  const [showPurchaseDialog, setShowPurchaseDialog] = useState(false);
  const [levelInfo, setLevelInfo] = useState(null);
  
  // Infrastructure detail dialog state
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedInfra, setSelectedInfra] = useState(null);
  const [infraDetail, setInfraDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [prices, setPrices] = useState({});
  const [showPricesDialog, setShowPricesDialog] = useState(false);
  const [savingPrices, setSavingPrices] = useState(false);
  const [upgradeInfo, setUpgradeInfo] = useState(null);
  const [upgrading, setUpgrading] = useState(false);
  
  // Film management state
  const [showAddFilmDialog, setShowAddFilmDialog] = useState(false);
  const [showRentFilmDialog, setShowRentFilmDialog] = useState(false);
  const [myFilms, setMyFilms] = useState([]);
  const [rentalFilms, setRentalFilms] = useState([]);
  const [selectedFilmToAdd, setSelectedFilmToAdd] = useState(null);
  const [selectedFilmToRent, setSelectedFilmToRent] = useState(null);
  const [rentalWeeks, setRentalWeeks] = useState(1);
  const [addingFilm, setAddingFilm] = useState(false);
  const [rentingFilm, setRentingFilm] = useState(false);
  const [removingFilm, setRemovingFilm] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get('/infrastructure/types'),
      api.get('/infrastructure/my'),
      api.get('/infrastructure/cities'),
      api.get('/player/level-info')
    ]).then(([types, my, citiesData, level]) => {
      setInfraTypes(types.data);
      setMyInfra(my.data);
      setCities(citiesData.data);
      setLevelInfo(level.data);
    });
  }, [api]);

  const getIcon = (iconName) => {
    const icons = { film: Film, car: Car, 'shopping-bag': ShoppingBag, building: Building, 'building-2': Building2, 'graduation-cap': GraduationCap, landmark: Landmark, crown: Crown, award: Award, 'ferris-wheel': Star, clapperboard: Clapperboard };
    return icons[iconName] || Building;
  };

  const handlePurchase = async () => {
    if (!selectedType || !selectedCountry || !selectedCity) return;
    setPurchasing(true);
    try {
      const res = await api.post('/infrastructure/purchase', {
        type: selectedType.id,
        city_name: selectedCity,
        country: selectedCountry,
        custom_name: customName || null
      });
      toast.success(`Acquistato! Hai speso $${res.data.cost.toLocaleString()}`);
      setShowPurchaseDialog(false);
      // Refresh
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Acquisto fallito');
    } finally {
      setPurchasing(false);
    }
  };

  const getCityPrice = () => {
    if (!selectedType || !selectedCountry || !selectedCity) return 0;
    const city = cities[selectedCountry]?.find(c => c.name === selectedCity);
    if (!city) return selectedType.base_cost;
    return Math.round(selectedType.base_cost * city.cost_multiplier);
  };

  const openInfraDetail = async (infra) => {
    setSelectedInfra(infra);
    setLoadingDetail(true);
    setShowDetailDialog(true);
    setUpgradeInfo(null);
    try {
      const [detailRes, upgradeRes] = await Promise.all([
        api.get(`/infrastructure/${infra.id}`),
        api.get(`/infrastructure/${infra.id}/upgrade-info`)
      ]);
      setInfraDetail(detailRes.data);
      setPrices(detailRes.data.prices || { ticket: 12, popcorn: 8, drinks: 5, combo: 18 });
      setUpgradeInfo(upgradeRes.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nel caricamento');
      setShowDetailDialog(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleUpgrade = async () => {
    if (!selectedInfra || upgrading) return;
    setUpgrading(true);
    try {
      const res = await api.post(`/infrastructure/${selectedInfra.id}/upgrade`);
      toast.success(`Upgrade al Livello ${res.data.new_level} completato!`);
      // Refresh detail and upgrade info
      const [detailRes, upgradeRes] = await Promise.all([
        api.get(`/infrastructure/${selectedInfra.id}`),
        api.get(`/infrastructure/${selectedInfra.id}/upgrade-info`)
      ]);
      setInfraDetail(detailRes.data);
      setUpgradeInfo(upgradeRes.data);
      // Refresh infrastructure list
      try {
        const myRes = await api.get('/infrastructure/my');
        setMyInfrastructure(myRes.data);
      } catch {}
      // Refresh user funds in header
      try {
        const userRes = await api.get('/auth/me');
        if (userRes.data) setUser(prev => ({ ...prev, funds: userRes.data.funds }));
      } catch {}
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nell\'upgrade');
    } finally {
      setUpgrading(false);
    }
  };

  const savePrices = async () => {
    if (!selectedInfra) return;
    setSavingPrices(true);
    try {
      await api.put(`/infrastructure/${selectedInfra.id}/prices`, { prices });
      toast.success('Prezzi aggiornati!');
      // Refresh infrastructure list
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setSavingPrices(false);
    }
  };

  const openAddFilmDialog = async () => {
    try {
      const res = await api.get('/films/my-available');
      setMyFilms(res.data);
      setShowAddFilmDialog(true);
    } catch (e) {
      toast.error('Errore nel caricamento dei film');
    }
  };

  const openRentFilmDialog = async () => {
    try {
      const res = await api.get('/films/available-for-rental');
      setRentalFilms(res.data);
      setShowRentFilmDialog(true);
    } catch (e) {
      toast.error('Errore nel caricamento dei film');
    }
  };

  const addFilmToCinema = async () => {
    if (!selectedFilmToAdd || !selectedInfra) return;
    setAddingFilm(true);
    try {
      const res = await api.post(`/infrastructure/${selectedInfra.id}/add-film`, {
        film_id: selectedFilmToAdd.id
      });
      toast.success(`"${selectedFilmToAdd.title}" aggiunto alla programmazione!`);
      setInfraDetail({...infraDetail, films_showing: res.data.films_showing});
      setShowAddFilmDialog(false);
      setSelectedFilmToAdd(null);
      // Refresh my infra
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setAddingFilm(false);
    }
  };

  const rentFilmForCinema = async () => {
    if (!selectedFilmToRent || !selectedInfra) return;
    setRentingFilm(true);
    try {
      const res = await api.post(`/infrastructure/${selectedInfra.id}/rent-film`, {
        film_id: selectedFilmToRent.id,
        weeks: rentalWeeks
      });
      toast.success(`"${selectedFilmToRent.title}" affittato per ${rentalWeeks} settimane! ${res.data.owner_name} ha ricevuto $${res.data.owner_received.toLocaleString()}`);
      setInfraDetail({...infraDetail, films_showing: res.data.films_showing});
      setShowRentFilmDialog(false);
      setSelectedFilmToRent(null);
      setRentalWeeks(1);
      // Refresh my infra and user
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setRentingFilm(false);
    }
  };

  const removeFilmFromCinema = async (filmId) => {
    if (!selectedInfra) return;
    setRemovingFilm(filmId);
    try {
      const res = await api.delete(`/infrastructure/${selectedInfra.id}/films/${filmId}`);
      toast.success('Film rimosso dalla programmazione');
      setInfraDetail({...infraDetail, films_showing: res.data.films_showing});
      // Refresh
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setRemovingFilm(null);
    }
  };

  const [pendingRevenue, setPendingRevenue] = useState(null);
  const [collectingRevenue, setCollectingRevenue] = useState(false);

  const loadPendingRevenue = async (infraId) => {
    try {
      const res = await api.get(`/infrastructure/${infraId}/pending-revenue`);
      setPendingRevenue(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const collectRevenue = async () => {
    if (!selectedInfra) return;
    setCollectingRevenue(true);
    try {
      const res = await api.post(`/infrastructure/${selectedInfra.id}/collect-revenue`);
      toast.success(`Riscossi $${res.data.collected.toLocaleString()}! (${res.data.hours_accumulated}h accumulate)`);
      setPendingRevenue({...pendingRevenue, pending: 0, hours_accumulated: 0});
      // Refresh
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setCollectingRevenue(false);
    }
  };

  // Load pending revenue when opening detail dialog
  useEffect(() => {
    if (showDetailDialog && selectedInfra) {
      loadPendingRevenue(selectedInfra.id);
    }
  }, [showDetailDialog, selectedInfra]);

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="infrastructure-page">
      {/* Level Progress */}
      {levelInfo && (
        <Card className="bg-gradient-to-r from-purple-500/20 to-yellow-500/20 border-purple-500/30 mb-4">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Star className="w-6 h-6 text-purple-400" />
                <span className="font-['Bebas_Neue'] text-2xl">Level {levelInfo.level}</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-yellow-400" />
                <span className="text-yellow-400 font-semibold">Fame: {levelInfo.fame?.toFixed(0) || 50}</span>
              </div>
            </div>
            <Progress value={levelInfo.progress_percent} className="h-2 mb-1" />
            <p className="text-xs text-gray-400">{levelInfo.current_xp} / {levelInfo.xp_for_next_level} XP per il prossimo livello</p>
          </CardContent>
        </Card>
      )}

      {/* My Infrastructure */}
      <Card className="bg-[#1A1A1A] border-white/10 mb-4">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
            <Building className="w-5 h-5 text-yellow-500" /> Le Mie Infrastrutture ({myInfra.total_count || 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {myInfra.infrastructure.length === 0 ? (
            <p className="text-gray-400 text-center py-6">Non hai ancora infrastrutture. Raggiungi il livello 5 per acquistare il tuo primo cinema!</p>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {myInfra.infrastructure.map(infra => {
                const Icon = getIcon(INFRASTRUCTURE_TYPES?.[infra.type]?.icon || 'building');
                return (
                  <Card key={infra.id} className="bg-white/5 border-white/10 cursor-pointer hover:border-yellow-500/50 transition-colors" onClick={() => openInfraDetail(infra)}>
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                          <Icon className="w-5 h-5 text-yellow-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-sm truncate">{infra.custom_name}</h3>
                          <p className="text-[10px] text-gray-400">{infra.city?.name}, {infra.country}</p>
                        </div>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">Ricavi totali:</span>
                        <span className="text-green-400">${(infra.total_revenue || 0).toLocaleString()}</span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Available Infrastructure Types */}
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-yellow-500" /> Infrastrutture Disponibili
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {infraTypes.map(infra => {
              const Icon = getIcon(infra.icon);
              const canBuy = infra.can_purchase;
              return (
                <Card key={infra.id} className={`border transition-all ${canBuy ? 'bg-white/5 border-green-500/30 hover:border-green-500' : 'bg-white/5 border-white/10 opacity-60'}`}>
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${canBuy ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
                        {canBuy ? <Icon className="w-5 h-5 text-green-500" /> : <Lock className="w-5 h-5 text-gray-500" />}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-sm">{language === 'it' ? infra.name_it : infra.name}</h3>
                        <div className="flex gap-1">
                          <Badge className={`text-[10px] h-4 ${infra.meets_level ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                            Lv.{infra.level_required}
                          </Badge>
                          <Badge className={`text-[10px] h-4 ${infra.meets_fame ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                            Fame {infra.fame_required}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <p className="text-[10px] text-gray-400 mb-2 line-clamp-2">{language === 'it' ? infra.description_it : infra.description}</p>
                    <div className="flex justify-between items-center">
                      <span className="text-yellow-500 font-semibold text-sm">${infra.base_cost?.toLocaleString()}</span>
                      <Button size="sm" className="h-7 text-xs" disabled={!canBuy} onClick={() => { setSelectedType(infra); setShowPurchaseDialog(true); }}>
                        {canBuy ? 'Acquista' : 'Bloccato'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Purchase Dialog */}
      <Dialog open={showPurchaseDialog} onOpenChange={setShowPurchaseDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl">Acquista {selectedType?.name_it || selectedType?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs">Nome personalizzato</Label>
              <Input value={customName} onChange={e => setCustomName(e.target.value)} placeholder={`${user?.nickname}'s ${selectedType?.name}`} className="h-9 bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">Paese</Label>
              <Select value={selectedCountry} onValueChange={v => { setSelectedCountry(v); setSelectedCity(''); }}>
                <SelectTrigger className="h-9 bg-black/20 border-white/10"><SelectValue placeholder="Seleziona paese" /></SelectTrigger>
                <SelectContent>
                  {Object.keys(cities).map(country => (
                    <SelectItem key={country} value={country}>{country}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedCountry && (
              <div>
                <Label className="text-xs">Città</Label>
                <Select value={selectedCity} onValueChange={setSelectedCity}>
                  <SelectTrigger className="h-9 bg-black/20 border-white/10"><SelectValue placeholder="Seleziona città" /></SelectTrigger>
                  <SelectContent>
                    {cities[selectedCountry]?.map(city => (
                      <SelectItem key={city.name} value={city.name}>
                        {city.name} (x{city.cost_multiplier})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {selectedCity && (
              <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Costo totale:</span>
                  <span className="text-yellow-500 font-bold">${getCityPrice().toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>I tuoi fondi:</span>
                  <span className={user?.funds >= getCityPrice() ? 'text-green-400' : 'text-red-400'}>${user?.funds?.toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPurchaseDialog(false)}>Annulla</Button>
            <Button onClick={handlePurchase} disabled={purchasing || !selectedCity || user?.funds < getCityPrice()} className="bg-yellow-500 text-black">
              {purchasing ? 'Acquistando...' : 'Conferma Acquisto'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Infrastructure Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Building className="w-5 h-5 text-yellow-500" /> {selectedInfra?.custom_name || 'Dettaglio Infrastruttura'}
            </DialogTitle>
            <DialogDescription>
              {selectedInfra?.city?.name}, {selectedInfra?.country} • {selectedInfra?.type}
            </DialogDescription>
          </DialogHeader>
          
          {loadingDetail ? (
            <div className="text-center py-8">Caricamento...</div>
          ) : infraDetail && (
            <div className="space-y-4">
              {/* Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-white/5 rounded border border-white/10">
                  <p className="text-xs text-gray-400">Ricavi totali</p>
                  <p className="text-lg font-bold text-green-400">${(infraDetail.total_revenue || 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-white/5 rounded border border-white/10">
                  <p className="text-xs text-gray-400">Film in programmazione</p>
                  <p className="text-lg font-bold text-yellow-500">{infraDetail.films_showing?.length || 0}</p>
                </div>
              </div>

              {/* Revenue Collection */}
              {pendingRevenue && (
                <div className="p-3 bg-gradient-to-r from-green-500/10 to-yellow-500/10 rounded border border-green-500/30">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-sm flex items-center gap-2">
                      <Wallet className="w-4 h-4 text-green-500" /> Incassi da Riscuotere
                    </h4>
                    <Badge className={pendingRevenue.is_maxed ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}>
                      {pendingRevenue.hours_accumulated?.toFixed(1)}h / 4h
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-2xl font-bold text-green-400">${pendingRevenue.pending?.toLocaleString()}</p>
                      <p className="text-xs text-gray-400">${pendingRevenue.hourly_rate?.toLocaleString()}/ora</p>
                    </div>
                    <Button 
                      onClick={collectRevenue}
                      disabled={collectingRevenue || pendingRevenue.pending < 1}
                      className="bg-green-500 hover:bg-green-400 text-black font-bold"
                    >
                      {collectingRevenue ? 'Riscuotendo...' : 'Riscuoti Ora'}
                    </Button>
                  </div>
                  {pendingRevenue.is_maxed && (
                    <p className="text-xs text-red-400 mt-2">⚠️ Incassi al massimo! Riscuoti per continuare ad accumulare.</p>
                  )}
                </div>
              )}

              {/* Attendance & Satisfaction Stats */}
              {infraDetail?.stats && (
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-cyan-400" /> Statistiche Cinema
                  </h4>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="p-2.5 bg-cyan-500/10 rounded border border-cyan-500/20 text-center">
                      <p className="text-[10px] text-gray-400">Affluenza/giorno</p>
                      <p className="text-base font-bold text-cyan-400">{infraDetail.stats.daily_attendance?.toLocaleString()}</p>
                    </div>
                    <div className="p-2.5 bg-green-500/10 rounded border border-green-500/20 text-center">
                      <p className="text-[10px] text-gray-400">Occupazione</p>
                      <p className="text-base font-bold text-green-400">{infraDetail.stats.occupancy_rate}%</p>
                    </div>
                    <div className="p-2.5 bg-yellow-500/10 rounded border border-yellow-500/20 text-center">
                      <p className="text-[10px] text-gray-400">Gradimento</p>
                      <p className={`text-base font-bold ${infraDetail.stats.satisfaction_index >= 70 ? 'text-green-400' : infraDetail.stats.satisfaction_index >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {infraDetail.stats.satisfaction_index}/100
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="p-2.5 bg-white/5 rounded border border-white/10 text-center">
                      <p className="text-[10px] text-gray-400">Ricavi Biglietti</p>
                      <p className="text-sm font-bold text-green-400">${(infraDetail.stats.ticket_revenue || 0).toLocaleString()}</p>
                    </div>
                    <div className="p-2.5 bg-white/5 rounded border border-white/10 text-center">
                      <p className="text-[10px] text-gray-400">Ricavi Food</p>
                      <p className="text-sm font-bold text-orange-400">${(infraDetail.stats.food_revenue || 0).toLocaleString()}</p>
                    </div>
                    <div className="p-2.5 bg-white/5 rounded border border-white/10 text-center">
                      <p className="text-[10px] text-gray-400">Qualità Film</p>
                      <p className="text-sm font-bold text-purple-400">{infraDetail.stats.film_quality_avg}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-white/5 rounded border border-white/10">
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <span>{infraDetail.stats.screens} schermi</span>
                      <span>|</span>
                      <span>{infraDetail.stats.seats_per_screen} posti/schermo</span>
                      <span>|</span>
                      <span>Capienza: {infraDetail.stats.total_capacity?.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Upgrade Section */}
              {upgradeInfo && (
                <div className="space-y-2 p-3 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 rounded-lg border border-purple-500/20">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-sm flex items-center gap-2">
                      <ArrowUpCircle className="w-4 h-4 text-purple-400" />
                      {upgradeInfo.current_level >= upgradeInfo.max_level 
                        ? 'Livello Massimo!' 
                        : `Upgrade Lv.${upgradeInfo.current_level} → Lv.${upgradeInfo.next_level}`}
                    </h4>
                    <Badge className="bg-purple-500/20 text-purple-400 text-xs">
                      Lv.{upgradeInfo.current_level}/{upgradeInfo.max_level}
                    </Badge>
                  </div>
                  
                  {upgradeInfo.current_level < upgradeInfo.max_level && (
                    <>
                      {/* Benefits preview */}
                      <div className="grid grid-cols-3 gap-1.5 text-center text-[10px]">
                        {upgradeInfo.benefits?.screens_added > 0 && (
                          <div className="p-1.5 bg-cyan-500/10 rounded border border-cyan-500/20">
                            <p className="text-gray-400">Sale</p>
                            <p className="text-cyan-400 font-bold">+{upgradeInfo.benefits.screens_added}</p>
                          </div>
                        )}
                        {upgradeInfo.benefits?.seats_added > 0 && (
                          <div className="p-1.5 bg-green-500/10 rounded border border-green-500/20">
                            <p className="text-gray-400">Posti/Sala</p>
                            <p className="text-green-400 font-bold">+{upgradeInfo.benefits.seats_added}</p>
                          </div>
                        )}
                        <div className="p-1.5 bg-yellow-500/10 rounded border border-yellow-500/20">
                          <p className="text-gray-400">Revenue</p>
                          <p className="text-yellow-400 font-bold">x{upgradeInfo.benefits?.next?.revenue_multiplier}</p>
                        </div>
                      </div>
                      
                      {/* New products */}
                      {upgradeInfo.benefits?.new_products?.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap">
                          <span className="text-[10px] text-gray-400">Nuovi prodotti:</span>
                          {upgradeInfo.benefits.new_products.map(p => (
                            <Badge key={p.id} className="bg-green-500/20 text-green-400 text-[10px]">
                              {p.name} (${p.base_price})
                            </Badge>
                          ))}
                        </div>
                      )}
                      
                      {/* Cost and requirements */}
                      <div className="flex items-center justify-between text-xs pt-1">
                        <span className="text-gray-400">
                          Costo: <span className={`font-bold ${(upgradeInfo.user_funds || 0) >= upgradeInfo.upgrade_cost ? 'text-green-400' : 'text-red-400'}`}>
                            ${upgradeInfo.upgrade_cost?.toLocaleString()}
                          </span>
                        </span>
                        <span className="text-gray-400">
                          Lv. giocatore: <span className={`font-bold ${upgradeInfo.player_level >= upgradeInfo.player_level_required ? 'text-green-400' : 'text-red-400'}`}>
                            {upgradeInfo.player_level}/{upgradeInfo.player_level_required}
                          </span>
                        </span>
                      </div>
                      
                      <Button
                        onClick={handleUpgrade}
                        disabled={!upgradeInfo.can_upgrade || upgrading}
                        className={`w-full h-9 font-bold ${upgradeInfo.can_upgrade ? 'bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white' : 'bg-gray-700 text-gray-400 cursor-not-allowed'}`}
                        data-testid="upgrade-infra-btn"
                      >
                        {upgrading ? 'Miglioramento in corso...' : upgradeInfo.can_upgrade ? `Migliora a Lv.${upgradeInfo.next_level}` : upgradeInfo.reason}
                      </Button>
                    </>
                  )}
                </div>
              )}

              {/* Prices Button - opens separate dialog */}
              {['cinema', 'megaplex', 'drive_in', 'mall', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema'].includes(selectedInfra?.type) && (
                <Button 
                  variant="outline" 
                  className="w-full h-10 border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10"
                  onClick={() => setShowPricesDialog(true)}
                  data-testid="open-prices-btn"
                >
                  <DollarSign className="w-4 h-4 mr-2" /> Modifica Prezzi
                </Button>
              )}

              {/* Film Management Section */}
              {['cinema', 'megaplex', 'drive_in', 'mall', 'multiplex_small', 'multiplex_medium', 'multiplex_large'].includes(selectedInfra?.type) && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-sm flex items-center gap-2">
                      <Film className="w-4 h-4 text-yellow-500" /> Programmazione Film
                    </h4>
                    <span className="text-xs text-gray-400">
                      {infraDetail?.films_showing?.length || 0} / {infraDetail?.type_info?.screens || 4} schermi
                    </span>
                  </div>
                  
                  {/* Films showing */}
                  {infraDetail?.films_showing?.length > 0 ? (
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {infraDetail.films_showing.map(film => (
                        <div key={film.film_id} className="flex items-center gap-2 p-2 bg-white/5 rounded border border-white/10">
                          {film.poster_url && (
                            <img src={film.poster_url} alt="" className="w-10 h-14 object-cover rounded" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold truncate">{film.title}</p>
                            <div className="flex items-center gap-2 text-xs text-gray-400">
                              <span>⭐ {film.imdb_rating || '?'}</span>
                              <Badge className={`text-[9px] h-4 ${film.is_owned ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                {film.is_owned ? '100% ricavi' : `${film.revenue_share_renter || 70}% ricavi`}
                              </Badge>
                              {film.is_rented && film.rental_end && (
                                <span className="text-yellow-400">
                                  Scade: {new Date(film.rental_end).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                          <Button 
                            size="sm" 
                            variant="destructive" 
                            className="h-7 w-7 p-0"
                            disabled={removingFilm === film.film_id}
                            onClick={() => removeFilmFromCinema(film.film_id)}
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-gray-500 text-sm py-3">Nessun film in programmazione</p>
                  )}
                  
                  {/* Add Film Buttons */}
                  {(infraDetail?.films_showing?.length || 0) < (infraDetail?.type_info?.screens || 4) && (
                    <div className="grid grid-cols-2 gap-2">
                      <Button 
                        variant="outline" 
                        className="h-9 text-xs"
                        onClick={openAddFilmDialog}
                      >
                        <Plus className="w-3 h-3 mr-1" /> I Miei Film
                      </Button>
                      <Button 
                        className="h-9 text-xs bg-blue-500 hover:bg-blue-400"
                        onClick={openRentFilmDialog}
                      >
                        <ShoppingBag className="w-3 h-3 mr-1" /> Affitta Film
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>Chiudi</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Prices Dialog (separate popup) */}
      <Dialog open={showPricesDialog} onOpenChange={setShowPricesDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-sm max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-yellow-500" /> Gestione Prezzi
            </DialogTitle>
            <DialogDescription>{selectedInfra?.custom_name}</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs">Biglietto ($)</Label>
              <Input type="number" value={prices.ticket || 12} onChange={e => setPrices({...prices, ticket: parseInt(e.target.value) || 0})} className="h-9 bg-black/20 border-white/10" min={1} max={50} />
            </div>
            <div>
              <Label className="text-xs">Popcorn ($)</Label>
              <Input type="number" value={prices.popcorn || 8} onChange={e => setPrices({...prices, popcorn: parseInt(e.target.value) || 0})} className="h-9 bg-black/20 border-white/10" min={1} max={30} />
            </div>
            <div>
              <Label className="text-xs">Bevande ($)</Label>
              <Input type="number" value={prices.drinks || 5} onChange={e => setPrices({...prices, drinks: parseInt(e.target.value) || 0})} className="h-9 bg-black/20 border-white/10" min={1} max={20} />
            </div>
            <div>
              <Label className="text-xs">Combo ($)</Label>
              <Input type="number" value={prices.combo || 18} onChange={e => setPrices({...prices, combo: parseInt(e.target.value) || 0})} className="h-9 bg-black/20 border-white/10" min={1} max={60} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowPricesDialog(false)}>Annulla</Button>
            <Button onClick={savePrices} disabled={savingPrices} className="bg-yellow-500 text-black hover:bg-yellow-400" data-testid="save-prices-btn">
              {savingPrices ? 'Salvando...' : 'Salva Prezzi'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Own Film Dialog */}
      <Dialog open={showAddFilmDialog} onOpenChange={setShowAddFilmDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Film className="w-5 h-5 text-yellow-500" /> Aggiungi i Tuoi Film
            </DialogTitle>
            <DialogDescription>Seleziona un tuo film da proiettare. Riceverai il 100% dei ricavi.</DialogDescription>
          </DialogHeader>
          
          {myFilms.length === 0 ? (
            <div className="text-center py-6">
              <Film className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <p className="text-gray-400">Non hai ancora creato nessun film.</p>
              <Button className="mt-3" onClick={() => { setShowAddFilmDialog(false); setShowDetailDialog(false); navigate('/create'); }}>
                Crea un Film
              </Button>
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {myFilms.map(film => (
                <div 
                  key={film.id} 
                  className={`flex items-center gap-3 p-2 rounded border cursor-pointer transition-colors ${
                    selectedFilmToAdd?.id === film.id 
                      ? 'bg-yellow-500/20 border-yellow-500' 
                      : 'bg-white/5 border-white/10 hover:border-yellow-500/50'
                  }`}
                  onClick={() => setSelectedFilmToAdd(film)}
                >
                  {film.poster_url && (
                    <img src={film.poster_url} alt="" className="w-12 h-16 object-cover rounded" />
                  )}
                  <div className="flex-1">
                    <p className="font-semibold text-sm">{film.title}</p>
                    <p className="text-xs text-gray-400">{film.genre} • ⭐ {film.imdb_rating}</p>
                    <p className="text-xs text-green-400">Ricavi: ${(film.total_revenue || 0).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddFilmDialog(false)}>Annulla</Button>
            <Button 
              onClick={addFilmToCinema} 
              disabled={!selectedFilmToAdd || addingFilm}
              className="bg-yellow-500 text-black"
            >
              {addingFilm ? 'Aggiungendo...' : 'Aggiungi'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rent Film Dialog */}
      <Dialog open={showRentFilmDialog} onOpenChange={setShowRentFilmDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-blue-500" /> Affitta Film di Altri Giocatori
            </DialogTitle>
            <DialogDescription>Affitta film popolari. Paghi l'affitto e ricevi il 70% dei ricavi.</DialogDescription>
          </DialogHeader>
          
          {rentalFilms.length === 0 ? (
            <div className="text-center py-6">
              <Film className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <p className="text-gray-400">Nessun film disponibile per l'affitto al momento.</p>
            </div>
          ) : (
            <>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {rentalFilms.map(film => (
                  <div 
                    key={film.id} 
                    className={`flex items-center gap-3 p-2 rounded border cursor-pointer transition-colors ${
                      selectedFilmToRent?.id === film.id 
                        ? 'bg-blue-500/20 border-blue-500' 
                        : 'bg-white/5 border-white/10 hover:border-blue-500/50'
                    }`}
                    onClick={() => setSelectedFilmToRent(film)}
                  >
                    {film.poster_url && (
                      <img src={film.poster_url} alt="" className="w-12 h-16 object-cover rounded" />
                    )}
                    <div className="flex-1">
                      <p className="font-semibold text-sm">{film.title}</p>
                      <p className="text-xs text-gray-400">{film.genre} • ⭐ {film.imdb_rating} • ❤️ {film.likes_count}</p>
                      <p className="text-xs text-gray-500">di {film.owner?.nickname || 'Unknown'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-yellow-500 font-bold text-sm">${film.weekly_rental?.toLocaleString()}</p>
                      <p className="text-[10px] text-gray-400">/settimana</p>
                    </div>
                  </div>
                ))}
              </div>
              
              {selectedFilmToRent && (
                <div className="p-3 bg-blue-500/10 rounded border border-blue-500/20 mt-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Durata affitto:</span>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" className="h-7 w-7 p-0" onClick={() => setRentalWeeks(Math.max(1, rentalWeeks - 1))}>-</Button>
                      <span className="w-8 text-center font-bold">{rentalWeeks}</span>
                      <Button size="sm" variant="outline" className="h-7 w-7 p-0" onClick={() => setRentalWeeks(Math.min(12, rentalWeeks + 1))}>+</Button>
                      <span className="text-sm">settimane</span>
                    </div>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Costo totale:</span>
                    <span className="text-yellow-500 font-bold">${(selectedFilmToRent.weekly_rental * rentalWeeks).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>Al proprietario (30%):</span>
                    <span>${(selectedFilmToRent.weekly_rental * rentalWeeks * 0.3).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xs text-green-400 mt-1">
                    <span>Tuoi ricavi futuri:</span>
                    <span>70% degli incassi</span>
                  </div>
                </div>
              )}
            </>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowRentFilmDialog(false); setSelectedFilmToRent(null); }}>Annulla</Button>
            <Button 
              onClick={rentFilmForCinema} 
              disabled={!selectedFilmToRent || rentingFilm || (user?.funds < (selectedFilmToRent?.weekly_rental * rentalWeeks))}
              className="bg-blue-500 hover:bg-blue-400"
            >
              {rentingFilm ? 'Affittando...' : `Affitta per $${selectedFilmToRent ? (selectedFilmToRent.weekly_rental * rentalWeeks).toLocaleString() : 0}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Placeholder for infrastructure detail route
const INFRASTRUCTURE_TYPES = {};

// Infrastructure Marketplace Page

export default InfrastructurePage;
