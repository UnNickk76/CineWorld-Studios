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
import ProductionStudioPanel from '../components/ProductionStudioPanel';
import { InfraInfoButton } from '../components/InfraInfoButton';
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
  Car, Building2, GraduationCap, ArrowUpCircle, ShoppingBag, Landmark, Ticket
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { useRadio } from '../contexts/RadioContext';

const INFRA_CINEPASS = {
  cinema: 10, drive_in: 8, multiplex: 15, cinema_school: 12,
  vip_cinema: 15, production_studio: 20,
  multiplex_small: 10, multiplex_medium: 14, multiplex_large: 18,
  pvp_investigative: 5, pvp_operative: 3, pvp_legal: 10,
  studio_serie_tv: 15, studio_anime: 15, emittente_tv: 20,
  talent_scout_actors: 8, talent_scout_screenwriters: 8,
  cinema_museum: 25, film_festival_venue: 30, theme_park: 35
};
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const InfrastructurePage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isRadioPromo = searchParams.get('promo') === 'radio';
  const { refreshBanner } = useRadio();
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
  const [lockedInfoInfra, setLockedInfoInfra] = useState(null);
  
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
  
  // Detail tabs state (Panoramica, Eventi, Sicurezza, Influenza)
  const [detailTab, setDetailTab] = useState('panoramica');
  const [infraEvents, setInfraEvents] = useState(null);
  const [infraSecurity, setInfraSecurity] = useState(null);
  const [infraInfluence, setInfraInfluence] = useState(null);
  
  // Film management state - REMOVED (moved to StrutturePage)
  // Acting School state - REMOVED (moved to AgenziaPage)

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
      // If redirected from Radio Promo banner, auto-scroll to Emittente TV card
      if (isRadioPromo) {
        toast.success('📻 PROMO RADIO attiva: 80% di sconto sull\'Emittente TV!', { duration: 6000 });
        setTimeout(() => {
          const el = document.querySelector('[data-infra-type="emittente_tv"]');
          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 400);
      }
    });
  }, [api, isRadioPromo]);

  const getIcon = (iconName) => {
    const icons = { film: Film, car: Car, 'shopping-bag': ShoppingBag, building: Building, 'building-2': Building2, 'graduation-cap': GraduationCap, landmark: Landmark, crown: Crown, award: Award, 'ferris-wheel': Star, clapperboard: Clapperboard, radio: Video, sparkles: Sparkles, video: Video, tv: Film, target: Target, shield: Shield, swords: Swords, users: Users, search: Search };
    return icons[iconName] || Building;
  };

  const handlePurchase = async () => {
    if (!selectedType) return;
    const isPvp = selectedType.is_pvp;
    if (!isPvp && (!selectedCountry || !selectedCity)) return;
    setPurchasing(true);
    try {
      const payload = {
        type: selectedType.id,
        city_name: isPvp ? 'HQ' : selectedCity,
        country: isPvp ? 'Strategico' : selectedCountry,
        custom_name: customName || null
      };
      const res = await api.post('/infrastructure/purchase', payload);
      if (res.data.radio_promo_applied) {
        toast.success(`📻 PROMO RADIO APPLICATA! Hai speso solo $${res.data.cost.toLocaleString()} (80% di sconto)`);
        refreshBanner?.();
      } else {
        toast.success(`Acquistato! Hai speso $${res.data.cost.toLocaleString()}`);
      }
      setShowPurchaseDialog(false);
      if (refreshUser) refreshUser();
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
        setMyInfra(myRes.data);
      } catch {}
      // Refresh user funds in header
      try { await refreshUser?.(); } catch {}
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

  const [pendingRevenue, setPendingRevenue] = useState(null);
  const [collectingRevenue, setCollectingRevenue] = useState(false);
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [renaming, setRenaming] = useState(false);

  const handleRename = async () => {
    if (!selectedInfra) return;
    const name = (renameValue || '').trim();
    if (name.length < 2 || name.length > 60) {
      toast.error('Il nome deve essere tra 2 e 60 caratteri');
      return;
    }
    setRenaming(true);
    try {
      await api.put(`/infrastructure/${selectedInfra.id}/rename`, { custom_name: name });
      toast.success('Nome aggiornato!');
      setSelectedInfra({ ...selectedInfra, custom_name: name });
      setInfraDetail({ ...(infraDetail || {}), custom_name: name });
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
      setRenameOpen(false);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nel rinominare');
    } finally {
      setRenaming(false);
    }
  };

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

  // Category definitions for navbar
  const CATEGORIES = [
    { id: 'cinema', label: 'CINEMA', icon: Ticket, color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/30',
      types: ['cinema', 'drive_in', 'vip_cinema'] },
    { id: 'commerciale', label: 'COMMERCIALE', icon: Store, color: 'text-green-400', bg: 'bg-green-500/15', border: 'border-green-500/30',
      types: ['multiplex_small', 'multiplex_medium', 'multiplex_large'] },
    { id: 'studi', label: 'STUDI', icon: Video, color: 'text-purple-400', bg: 'bg-purple-500/15', border: 'border-purple-500/30',
      types: ['production_studio', 'studio_serie_tv', 'studio_anime', 'emittente_tv'] },
    { id: 'agenzie', label: 'AGENZIE', icon: Users, color: 'text-cyan-400', bg: 'bg-cyan-500/15', border: 'border-cyan-500/30',
      types: ['cinema_school', 'talent_scout_actors', 'talent_scout_screenwriters'] },
    { id: 'strategico', label: 'STRATEGICO', icon: Shield, color: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/30',
      types: ['pvp_operative', 'pvp_investigative', 'pvp_legal'] },
    { id: 'speciale', label: 'SPECIALE', icon: Crown, color: 'text-yellow-400', bg: 'bg-yellow-500/15', border: 'border-yellow-500/30',
      types: ['cinema_museum', 'film_festival_venue', 'theme_park'] },
  ];

  const [activeCategory, setActiveCategory] = useState('cinema');
  const [activeSubTab, setActiveSubTab] = useState('disponibili');

  const activeCat = CATEGORIES.find(c => c.id === activeCategory) || CATEGORIES[0];
  const filteredTypes = infraTypes.filter(it => activeCat.types.includes(it.id));
  const filteredOwned = myInfra.infrastructure?.filter(inf => activeCat.types.includes(inf.type)) || [];

  return (
    <div className="pt-16 pb-20 max-w-7xl mx-auto" data-testid="infrastructure-page">
      {/* Level Progress */}
      {levelInfo && (
        <div className="px-3 mb-2">
          <Card className="bg-gradient-to-r from-purple-500/20 to-yellow-500/20 border-purple-500/30">
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-purple-400" />
                  <span className="font-['Bebas_Neue'] text-xl">Level {levelInfo.level}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Award className="w-4 h-4 text-yellow-400" />
                  <span className="text-yellow-400 font-semibold text-sm">Fame: {levelInfo.fame?.toFixed(0) || 50}</span>
                </div>
              </div>
              <Progress value={levelInfo.progress_percent} className="h-1.5 mb-0.5" />
              <p className="text-[10px] text-gray-400">{levelInfo.current_xp} / {levelInfo.xp_for_next_level} XP</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Category Navbar — sticky, 2 rows: 3 top + 2 bottom */}
      <nav className="sticky top-[52px] z-30 bg-[#0a0a0a]/95 backdrop-blur-sm border-b border-white/5 mb-1 px-2 py-1.5" data-testid="infra-category-nav">
        <div className="grid grid-cols-3 gap-1 mb-1">
          {CATEGORIES.slice(0, 3).map(cat => {
            const CatIcon = cat.icon;
            const isActive = activeCategory === cat.id;
            const ownedCount = myInfra.infrastructure?.filter(inf => cat.types.includes(inf.type)).length || 0;
            return (
              <button
                key={cat.id}
                onClick={() => { setActiveCategory(cat.id); setActiveSubTab('disponibili'); }}
                className={`flex items-center justify-center gap-1 px-1 py-2 text-[11px] font-medium rounded-lg border transition-colors ${
                  isActive ? `${cat.bg} ${cat.border} ${cat.color}` : 'border-white/5 text-gray-500 hover:text-gray-300'
                }`}
                data-testid={`infra-tab-${cat.id}`}
              >
                <CatIcon className="w-3.5 h-3.5" />
                {cat.label}
                {ownedCount > 0 && <span className="text-[9px] bg-white/10 px-1 rounded-full">{ownedCount}</span>}
              </button>
            );
          })}
        </div>
        <div className="grid grid-cols-2 gap-1">
          {CATEGORIES.slice(3).map(cat => {
            const CatIcon = cat.icon;
            const isActive = activeCategory === cat.id;
            const ownedCount = myInfra.infrastructure?.filter(inf => cat.types.includes(inf.type)).length || 0;
            return (
              <button
                key={cat.id}
                onClick={() => { setActiveCategory(cat.id); setActiveSubTab('disponibili'); }}
                className={`flex items-center justify-center gap-1 px-1 py-2 text-[11px] font-medium rounded-lg border transition-colors ${
                  isActive ? `${cat.bg} ${cat.border} ${cat.color}` : 'border-white/5 text-gray-500 hover:text-gray-300'
                }`}
                data-testid={`infra-tab-${cat.id}`}
              >
                <CatIcon className="w-3.5 h-3.5" />
                {cat.label}
                {ownedCount > 0 && <span className="text-[9px] bg-white/10 px-1 rounded-full">{ownedCount}</span>}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Sub-tabs: Disponibili / Possedute */}
      <div className="px-3 mb-3">
        <div className="flex gap-2">
          {['disponibili', 'possedute'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveSubTab(tab)}
              className={`flex-1 py-2 text-xs font-medium text-center rounded-lg border transition-colors ${
                activeSubTab === tab
                  ? `${activeCat.bg} ${activeCat.border} ${activeCat.color}`
                  : 'bg-transparent border-white/5 text-gray-500 hover:text-gray-300'
              }`}
              data-testid={`infra-subtab-${tab}`}
            >
              {tab === 'disponibili' ? 'Disponibili' : `Possedute (${filteredOwned.length})`}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="px-3">
        {activeSubTab === 'disponibili' ? (
          /* DISPONIBILI */
          filteredTypes.length === 0 ? (
            <p className="text-gray-500 text-center py-8 text-sm">Nessuna infrastruttura in questa categoria</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {filteredTypes.map(infra => {
                const Icon = getIcon(infra.icon);
                const canBuy = infra.can_purchase;
                const isPromoEligible = isRadioPromo && infra.id === 'emittente_tv';
                const promoPrice = isPromoEligible ? Math.round((infra.base_cost || 0) * 0.2) : null;
                return (
                  <Card
                    key={infra.id}
                    data-infra-type={infra.id}
                    className={`border transition-all cursor-pointer relative ${canBuy ? `bg-white/5 ${activeCat.border} hover:bg-white/10` : 'bg-white/3 border-white/5 opacity-60 hover:opacity-85 active:scale-[0.98]'} ${isPromoEligible ? 'ring-2 ring-red-400/70 shadow-lg shadow-red-900/40' : ''}`}
                    onClick={() => {
                      if (canBuy) { setSelectedType(infra); setShowPurchaseDialog(true); }
                      else { setLockedInfoInfra(infra); }
                    }}
                  >
                    {isPromoEligible && (
                      <div className="absolute -top-2 -right-2 z-10 bg-gradient-to-br from-red-500 to-amber-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full shadow-md animate-pulse">-80%</div>
                    )}
                    <div onClick={(e) => e.stopPropagation()}><InfraInfoButton infraType={infra.id} variant="corner" /></div>
                    <CardContent className="p-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-2 ${activeCat.bg}`}>
                        {canBuy ? <Icon className={`w-5 h-5 ${activeCat.color}`} /> : <Lock className="w-5 h-5 text-gray-500" />}
                      </div>
                      <h3 className="font-semibold text-xs leading-tight mb-1 line-clamp-2">{language === 'it' ? infra.name_it : infra.name}</h3>
                      <div className="flex gap-1 mb-1.5 flex-wrap">
                        <Badge className={`text-[8px] h-3.5 px-1 ${infra.meets_level ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                          Lv.{infra.level_required}
                        </Badge>
                        <Badge className={`text-[8px] h-3.5 px-1 ${infra.meets_fame ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                          F.{infra.fame_required}
                        </Badge>
                      </div>
                      <p className="text-[9px] text-gray-500 line-clamp-2 mb-2">{language === 'it' ? infra.description_it : infra.description}</p>
                      <div className="flex items-center justify-between">
                        {isPromoEligible ? (
                          <div className="flex flex-col">
                            <span className="text-[9px] text-gray-500 line-through">${infra.base_cost?.toLocaleString()}</span>
                            <span className="font-bold text-xs text-red-400">${promoPrice?.toLocaleString()}</span>
                          </div>
                        ) : (
                          <span className={`font-bold text-xs ${activeCat.color}`}>${infra.base_cost?.toLocaleString()}</span>
                        )}
                        {infra.already_owned && <Badge className="bg-blue-500/20 text-blue-400 text-[8px] h-3.5">Posseduto</Badge>}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )
        ) : (
          /* POSSEDUTE */
          filteredOwned.length === 0 ? (
            <p className="text-gray-500 text-center py-8 text-sm">Nessuna infrastruttura {activeCat.label.toLowerCase()} posseduta</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {filteredOwned.map(infra => {
                const Icon = getIcon(INFRASTRUCTURE_TYPES?.[infra.type]?.icon || 'building');
                return (
                  <Card
                    key={infra.id}
                    className={`${activeCat.border} bg-white/5 cursor-pointer hover:bg-white/10 transition-all relative`}
                    onClick={() => openInfraDetail(infra)}
                  >
                    <div onClick={(e) => e.stopPropagation()}><InfraInfoButton infraType={infra.type} variant="corner" /></div>
                    <CardContent className="p-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-2 ${activeCat.bg}`}>
                        <Icon className={`w-5 h-5 ${activeCat.color}`} />
                      </div>
                      <h3 className="font-semibold text-xs leading-tight mb-0.5 line-clamp-2">{infra.custom_name}</h3>
                      <p className="text-[9px] text-gray-500 mb-1.5">{infra.city?.name}, {infra.country}</p>
                      <div className="flex justify-between text-[10px]">
                        <span className="text-gray-400">Ricavi:</span>
                        <span className="text-green-400 font-semibold">${(infra.total_revenue || 0).toLocaleString()}</span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )
        )}
      </div>

      {/* Locked Infrastructure Info Dialog */}
      <Dialog open={!!lockedInfoInfra} onOpenChange={(o) => !o && setLockedInfoInfra(null)}>
        <DialogContent className="bg-[#14110d] border-amber-500/20 max-w-sm max-h-[85vh] overflow-y-auto" data-testid="locked-infra-dialog">
          {lockedInfoInfra && (() => {
            const LockedIcon = getIcon(lockedInfoInfra.icon);
            const userLvl = levelInfo?.level ?? user?.level ?? 0;
            const userFame = user?.fame ?? 0;
            const meetsLv = userLvl >= (lockedInfoInfra.level_required || 0);
            const meetsFame = userFame >= (lockedInfoInfra.fame_required || 0);
            const perks = [];
            if (lockedInfoInfra.screens > 0) perks.push(`${lockedInfoInfra.screens} sale x ${lockedInfoInfra.seats_per_screen} posti`);
            if (lockedInfoInfra.revenue_multiplier && lockedInfoInfra.revenue_multiplier !== 1) perks.push(`Ricavi x${lockedInfoInfra.revenue_multiplier}`);
            if (lockedInfoInfra.can_show_3d) perks.push('Supporta film 3D');
            if (lockedInfoInfra.has_food_court) perks.push('Food court integrato');
            if (lockedInfoInfra.production_bonus) perks.push(`-${lockedInfoInfra.production_bonus}% costi produzione`);
            if (lockedInfoInfra.quality_bonus) perks.push(`+${lockedInfoInfra.quality_bonus}% qualità film`);
            if (lockedInfoInfra.daily_maintenance) perks.push(`Manutenzione $${lockedInfoInfra.daily_maintenance.toLocaleString()}/g`);
            return (
              <>
                <DialogHeader>
                  <div className="flex items-center gap-3 mb-1">
                    <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
                      <LockedIcon className="w-6 h-6 text-amber-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <DialogTitle className="font-['Bebas_Neue'] text-xl leading-tight">
                        {language === 'it' ? lockedInfoInfra.name_it : lockedInfoInfra.name}
                      </DialogTitle>
                      <div className="flex items-center gap-1 mt-0.5">
                        <Lock className="w-3 h-3 text-amber-400" />
                        <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Bloccata</span>
                      </div>
                    </div>
                  </div>
                </DialogHeader>
                <div className="space-y-3">
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {language === 'it' ? lockedInfoInfra.description_it : lockedInfoInfra.description}
                  </p>
                  {perks.length > 0 && (
                    <div className="p-2.5 rounded-lg bg-black/40 border border-white/5" data-testid="locked-infra-benefits">
                      <p className="text-[9px] uppercase tracking-wider text-amber-400/70 font-bold mb-1.5">A cosa serve</p>
                      <ul className="space-y-1">
                        {perks.map((p, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-[11px] text-gray-200">
                            <span className="text-emerald-400 mt-0.5">●</span>
                            <span>{p}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="p-2.5 rounded-lg bg-rose-500/5 border border-rose-500/20" data-testid="locked-infra-requirements">
                    <p className="text-[9px] uppercase tracking-wider text-rose-300/70 font-bold mb-1.5">Requisiti per sbloccarla</p>
                    <div className="grid grid-cols-2 gap-2">
                      <div className={`p-2 rounded border ${meetsLv ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-rose-500/10 border-rose-500/30'}`}>
                        <p className="text-[9px] text-gray-400 uppercase">Livello</p>
                        <p className={`text-sm font-bold ${meetsLv ? 'text-emerald-300' : 'text-rose-300'}`}>
                          Lv.{userLvl} / Lv.{lockedInfoInfra.level_required}
                        </p>
                      </div>
                      <div className={`p-2 rounded border ${meetsFame ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-rose-500/10 border-rose-500/30'}`}>
                        <p className="text-[9px] text-gray-400 uppercase">Fama</p>
                        <p className={`text-sm font-bold ${meetsFame ? 'text-emerald-300' : 'text-rose-300'}`}>
                          {userFame} / {lockedInfoInfra.fame_required}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-amber-500/5 border border-amber-500/15">
                    <span className="text-[10px] text-gray-400 uppercase tracking-wider">Costo acquisto</span>
                    <span className="text-sm font-bold text-amber-300">${lockedInfoInfra.base_cost?.toLocaleString()}</span>
                  </div>
                  <Button
                    onClick={() => setLockedInfoInfra(null)}
                    className="w-full bg-amber-500 hover:bg-amber-400 text-black font-bold"
                    data-testid="locked-infra-close-btn"
                  >
                    Ho capito
                  </Button>
                </div>
              </>
            );
          })()}
        </DialogContent>
      </Dialog>

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
            {selectedType?.is_pvp ? (
              /* PvP infrastructure: no city needed */
              <div className="p-3 bg-red-500/10 rounded border border-red-500/20">
                <p className="text-xs text-gray-400 mb-2">Struttura strategica (PvP) - non richiede posizione</p>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Costo:</span>
                  <span className="text-yellow-500 font-bold">${selectedType?.base_cost?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>I tuoi fondi:</span>
                  <span className={user?.funds >= (selectedType?.base_cost || 0) ? 'text-green-400' : 'text-red-400'}>${user?.funds?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span className="flex items-center gap-1"><Ticket className="w-3 h-3 text-cyan-400" /> CinePass:</span>
                  <span className={user?.cinepass >= (INFRA_CINEPASS[selectedType?.id] || 5) ? 'text-green-400' : 'text-red-400'}>
                    {INFRA_CINEPASS[selectedType?.id] || 5} richiesti ({user?.cinepass ?? 100} disponibili)
                  </span>
                </div>
              </div>
            ) : (
            <>
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
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span className="flex items-center gap-1"><Ticket className="w-3 h-3 text-cyan-400" /> CinePass:</span>
                  <span className={user?.cinepass >= (INFRA_CINEPASS[selectedType?.id] || 10) ? 'text-green-400' : 'text-red-400'}>
                    {INFRA_CINEPASS[selectedType?.id] || 10} richiesti ({user?.cinepass ?? 100} disponibili)
                  </span>
                </div>
              </div>
            )}
            </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPurchaseDialog(false)}>Annulla</Button>
            <Button onClick={handlePurchase} disabled={purchasing || (!selectedType?.is_pvp && (!selectedCity || user?.funds < getCityPrice())) || (selectedType?.is_pvp && user?.funds < (selectedType?.base_cost || 0))} className="bg-yellow-500 text-black">
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
              <button
                type="button"
                onClick={() => { setRenameValue(selectedInfra?.custom_name || ''); setRenameOpen(true); }}
                className="ml-auto p-1.5 rounded-md hover:bg-white/10 active:scale-95 transition-all"
                data-testid="rename-infra-btn"
                aria-label="Rinomina"
                title="Rinomina"
              >
                <Edit className="w-4 h-4 text-cyan-300" />
              </button>
            </DialogTitle>
            <DialogDescription>
              {selectedInfra?.city?.name}, {selectedInfra?.country} • {selectedInfra?.type}
            </DialogDescription>
          </DialogHeader>
          
          {loadingDetail ? (
            <div className="text-center py-8">Caricamento...</div>
          ) : infraDetail && (
            <div className="space-y-3">
              {/* Basic info */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-white/5 rounded border border-white/10">
                  <p className="text-xs text-gray-400">Livello</p>
                  <p className="text-lg font-bold text-yellow-400">Lv.{infraDetail.level || 1}</p>
                </div>
                <div className="p-3 bg-white/5 rounded border border-white/10">
                  <p className="text-xs text-gray-400">Ricavi totali</p>
                  <p className="text-lg font-bold text-green-400">${(infraDetail.total_revenue || 0).toLocaleString()}</p>
                </div>
              </div>

              {/* Navigate to management */}
              {['cinema','drive_in','vip_cinema','multiplex_small','multiplex_medium','multiplex_large','cinema_museum','film_festival_venue','theme_park'].includes(selectedInfra?.type) && (
                <Button variant="outline" className="w-full h-10 border-amber-500/30 text-amber-400 hover:bg-amber-500/10" onClick={() => { setShowDetailDialog(false); navigate('/strutture'); }} data-testid="go-strutture-btn">
                  Gestisci in Strutture
                </Button>
              )}
              {selectedInfra?.type === 'cinema_school' && (
                <Button variant="outline" className="w-full h-10 border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10" onClick={() => { setShowDetailDialog(false); navigate('/agenzia'); }} data-testid="go-agenzia-btn">
                  Gestisci in Agenzia
                </Button>
              )}
              {['pvp_operative','pvp_investigative','pvp_legal'].includes(selectedInfra?.type) && (
                <Button variant="outline" className="w-full h-10 border-red-500/30 text-red-400 hover:bg-red-500/10" onClick={() => { setShowDetailDialog(false); navigate('/strategico'); }} data-testid="go-strategico-btn">
                  Gestisci in Strategico
                </Button>
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
                      {upgradeInfo.cinepass_cost > 0 && (
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-400">CinePass: <span className={`font-bold ${(upgradeInfo.user_cinepass || 0) >= upgradeInfo.cinepass_cost ? 'text-green-400' : 'text-red-400'}`}>{upgradeInfo.cinepass_cost}</span></span>
                          <span className="text-gray-500 text-[10px]">Hai: {upgradeInfo.user_cinepass || 0}</span>
                        </div>
                      )}
                      
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

            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>Chiudi</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Rename Dialog */}
      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent className="bg-[#14110d] border-cyan-500/20 max-w-sm" data-testid="rename-infra-dialog">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
              <Edit className="w-4 h-4 text-cyan-300" /> Rinomina infrastruttura
            </DialogTitle>
            <DialogDescription className="text-xs text-gray-400">
              Dai un nome unico al tuo {selectedInfra?.type === 'production_studio' ? 'Studio di Produzione' : 'studio'} (2-60 caratteri).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Input
              value={renameValue}
              onChange={e => setRenameValue(e.target.value)}
              placeholder="Es. Anacapito Studios"
              maxLength={60}
              className="h-10 bg-black/30 border-cyan-500/20 focus:border-cyan-400/50"
              data-testid="rename-infra-input"
              autoFocus
            />
            <div className="text-[10px] text-gray-500 text-right">{(renameValue || '').length}/60</div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameOpen(false)} disabled={renaming}>Annulla</Button>
            <Button
              onClick={handleRename}
              disabled={renaming || (renameValue || '').trim().length < 2}
              className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold"
              data-testid="rename-infra-confirm-btn"
            >
              {renaming ? 'Salvo…' : 'Salva'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const INFRASTRUCTURE_TYPES = {};

export default InfrastructurePage;
