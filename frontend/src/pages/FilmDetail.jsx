// CineWorld Studio's - FilmDetail
// Extracted from App.js for modularity

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, MessageCircle
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const FilmDetail = () => {
  const { api, user } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [film, setFilm] = useState(null);
  const [expandedCountry, setExpandedCountry] = useState(null);
  const [actorRoles, setActorRoles] = useState([]);
  const [hourlyRevenue, setHourlyRevenue] = useState(null);
  const [durationStatus, setDurationStatus] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [generatingTrailer, setGeneratingTrailer] = useState(false);
  const [rereleaseStatus, setRereleaseStatus] = useState(null);
  const [rereleasing, setRereleasing] = useState(false);
  const [distribution, setDistribution] = useState(null);
  const [showLikersPopup, setShowLikersPopup] = useState(false);
  const [likers, setLikers] = useState([]);
  const [loadingLikers, setLoadingLikers] = useState(false);
  const [showEndRunPopup, setShowEndRunPopup] = useState(false);
  const [endRunData, setEndRunData] = useState(null);
  // Virtual Audience System
  const [virtualAudience, setVirtualAudience] = useState(null);
  const [showImdbDetail, setShowImdbDetail] = useState(false);
  const navigate = useNavigate();
  
  // One-time actions state
  const [filmActions, setFilmActions] = useState(null);
  const [performingAction, setPerformingAction] = useState(null);

  const [loadError, setLoadError] = useState(null);
  
  const loadFilm = async () => {
    const id = window.location.pathname.split('/').pop(); 
    try {
      const [filmRes, rolesRes, actionsRes, distRes, virtualRes] = await Promise.all([
        api.get(`/films/${id}`),
        api.get('/actor-roles').catch(() => ({ data: [] })),
        api.get(`/films/${id}/actions`).catch(() => ({ data: null })),
        api.get(`/films/${id}/distribution`).catch(() => ({ data: null })),
        api.get(`/films/${id}/virtual-audience`).catch(() => ({ data: null }))
      ]);
      
      // Verify the response is a valid film (not an error object)
      if (!filmRes.data || filmRes.data.detail || !filmRes.data.title) {
        setLoadError(filmRes.data?.detail || 'Film non trovato');
        return;
      }
      
      setFilm(filmRes.data);
    setActorRoles(rolesRes.data);
    if (filmRes.data) setFilmActions(actionsRes.data);
    if (distRes.data) setDistribution(distRes.data);
    if (virtualRes.data) setVirtualAudience(virtualRes.data);
    
    // Load hourly revenue and duration status for in-theater films
    if (filmRes.data.status === 'in_theaters') {
      const [hourlyRes, durationRes] = await Promise.all([
        api.get(`/films/${id}/hourly-revenue`).catch(() => null),
        api.get(`/films/${id}/duration-status`).catch(() => null)
      ]);
      if (hourlyRes) setHourlyRevenue(hourlyRes.data);
      if (durationRes) setDurationStatus(durationRes.data);
    }
    
    // Load re-release status for withdrawn/completed films
    if (filmRes.data.status === 'withdrawn' || filmRes.data.status === 'completed') {
      const rereleaseRes = await api.get(`/films/${id}/rerelease-status`).catch(() => null);
      if (rereleaseRes) setRereleaseStatus(rereleaseRes.data);
      
      // Check if we should show end-of-run expectations popup (only for owner, only once per session)
      const shownKey = `endrun_shown_${id}`;
      if (filmRes.data.user_id === user?.id && !sessionStorage.getItem(shownKey) && filmRes.data.film_tier) {
        try {
          const expectationsRes = await api.get(`/films/${id}/tier-expectations`);
          if (expectationsRes.data) {
            setEndRunData(expectationsRes.data);
            setShowEndRunPopup(true);
            sessionStorage.setItem(shownKey, 'true');
          }
        } catch (e) {
          // Silently fail
        }
      }
    }
    } catch (err) {
      console.error('Film load error:', err);
      setLoadError(err.response?.data?.detail || 'Errore nel caricamento del film');
    }
  };
  
  const handleRerelease = async () => {
    if (!rereleaseStatus?.can_rerelease) return;
    
    setRereleasing(true);
    try {
      const res = await api.post(`/films/${film.id}/rerelease`);
      toast.success(res.data.message);
      toast.info(`Incasso apertura: $${res.data.opening_revenue.toLocaleString()}`);
      loadFilm();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setRereleasing(false);
    }
  };

  useEffect(() => { loadFilm(); }, [api]);
  
  // Load likers when popup opens - must be before early return
  useEffect(() => {
    if (showLikersPopup && film) {
      const loadLikersData = async () => {
        setLoadingLikers(true);
        try {
          const res = await api.get(`/films/${film.id}/likes`);
          setLikers(res.data.likers || []);
        } catch (e) {
          toast.error('Errore nel caricamento');
        } finally {
          setLoadingLikers(false);
        }
      };
      loadLikersData();
    }
  }, [showLikersPopup, film?.id, api]);
  
  if (loadError) return (
    <div className="pt-16 p-4 text-center space-y-4">
      <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto">
        <Film className="w-8 h-8 text-red-400" />
      </div>
      <h2 className="text-lg font-bold text-white">{typeof loadError === 'string' ? loadError : 'Film non trovato'}</h2>
      <p className="text-sm text-gray-400">Questo film potrebbe non essere disponibile o è stato rimosso.</p>
      <Button onClick={() => navigate(-1)} variant="outline" className="border-white/20">
        <ChevronLeft className="w-4 h-4 mr-1" /> Torna indietro
      </Button>
    </div>
  );
  
  if (!film) return <div className="pt-16 p-4 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;
  
  // Check if current user is the owner
  const isOwner = filmActions?.is_owner || film.user_id === user?.id;
  
  // Check if action is available
  const isActionAvailable = (actionName) => {
    if (!isOwner) return false;
    if (!filmActions) return true; // Default to available if not loaded
    return filmActions.actions?.[actionName]?.available;
  };
  
  // Perform create star action
  const performCreateStar = async (actorId) => {
    if (!isActionAvailable('create_star')) {
      toast.error(language === 'it' ? 'Azione già utilizzata' : 'Action already used');
      return;
    }
    setPerformingAction('create_star');
    try {
      const res = await api.post(`/films/${film.id}/action/create-star?actor_id=${actorId}`);
      toast.success(res.data.message);
      loadFilm(); // Reload to update actions state
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
    setPerformingAction(null);
  };
  
  // Perform skill boost action
  const performSkillBoost = async () => {
    if (!isActionAvailable('skill_boost')) {
      toast.error(language === 'it' ? 'Azione già utilizzata' : 'Action already used');
      return;
    }
    setPerformingAction('skill_boost');
    try {
      const res = await api.post(`/films/${film.id}/action/skill-boost`);
      toast.success(res.data.message);
      // Show individual boosts
      res.data.boosted_cast?.forEach(b => {
        toast.info(`${b.name}: ${b.skill} +${b.boost}`);
      });
      loadFilm();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
    setPerformingAction(null);
  };

  const processHourlyRevenue = async () => {
    setProcessing(true);
    try {
      const res = await api.post(`/films/${film.id}/process-hourly-revenue`);
      if (res.data.processed) {
        toast.success(`Incasso orario: $${res.data.revenue.toLocaleString()}!`);
        if (res.data.special_event) {
          toast.success(`Evento speciale: ${res.data.special_event}!`);
        }
        loadFilm();
      } else {
        toast.info(`Attendi ${Math.ceil(res.data.wait_seconds / 60)} minuti per il prossimo incasso.`);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
    setProcessing(false);
  };

  const extendFilm = async () => {
    try {
      const res = await api.post(`/films/${film.id}/extend?extra_days=3`);
      toast.success(`Film esteso di ${res.data.extra_days} giorni! Fame +${res.data.fame_bonus}. Estensioni rimaste: ${res.data.extensions_remaining}`);
      loadFilm();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Impossibile estendere');
    }
  };

  const checkStarDiscoveries = async () => {
    try {
      const res = await api.post(`/films/${film.id}/check-star-discoveries`);
      if (res.data.total_found > 0) {
        res.data.discoveries.forEach(d => toast.success(d.announcement));
      } else {
        toast.info('Nessuna nuova stella scoperta questa volta.');
      }
    } catch (e) {
      toast.error('Errore nel controllo scoperte');
    }
  };

  const evolveSkills = async () => {
    try {
      const res = await api.post(`/films/${film.id}/evolve-cast-skills`);
      if (res.data.total_evolved > 0) {
        toast.success(`${res.data.total_evolved} membri del cast hanno evoluto le loro skill!`);
      } else {
        toast.info('Nessun cambiamento nelle skill del cast.');
      }
    } catch (e) {
      toast.error('Errore nell\'evoluzione skill');
    }
  };

  const generateTrailer = async () => {
    setGeneratingTrailer(true);
    try {
      const res = await api.post(`/films/${film.id}/generate-trailer`);
      if (res.data.status === 'exists') {
        toast.info('Il trailer esiste già!');
      } else {
        toast.success('Trailer generato con successo!');
      }
      setFilm(prev => ({ ...prev, trailer_url: res.data.trailer_url }));
      setGeneratingTrailer(false);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella generazione del trailer');
      setGeneratingTrailer(false);
    }
  };

  const getRoleName = (roleId) => {
    const role = actorRoles.find(r => r.id === roleId);
    if (!role) return roleId;
    const langKey = `name_${language}`;
    return role[langKey] || role.name;
  };

  const getRoleBadge = (role) => {
    const badges = {
      protagonist: { color: 'bg-yellow-500/20 text-yellow-500', label: getRoleName('protagonist') },
      co_protagonist: { color: 'bg-blue-500/20 text-blue-400', label: getRoleName('co_protagonist') },
      antagonist: { color: 'bg-red-500/20 text-red-400', label: getRoleName('antagonist') },
      supporting: { color: 'bg-gray-500/20 text-gray-400', label: getRoleName('supporting') },
      cameo: { color: 'bg-purple-500/20 text-purple-400', label: getRoleName('cameo') }
    };
    const badge = badges[role] || badges.supporting;
    return <Badge className={`${badge.color} text-[10px] h-4`}>{badge.label}</Badge>;
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="film-detail-page">
      <div className="grid lg:grid-cols-3 gap-4">
        <Card className="bg-[#1A1A1A] border-white/10 overflow-hidden">
          <div className="aspect-[2/3] relative">
            <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'} alt={film.title} className="w-full h-full object-cover" />
            {film.is_sequel && (
              <div className="absolute top-2 right-2 bg-purple-600 text-white text-xs px-2 py-1 rounded-lg font-bold shadow-lg">
                SEQUEL #{film.sequel_number || 2}
              </div>
            )}
          </div>
          <CardContent className="p-3">
            <h1 className="font-['Bebas_Neue'] text-xl mb-1">{film.title}</h1>
            {film.subtitle && (
              <h2 className="text-gray-400 text-sm mb-2">{film.subtitle}</h2>
            )}
            {/* Sequel bonus info */}
            {film.sequel_bonus_applied && typeof film.sequel_bonus_applied === 'object' && (
              <div className={`text-xs p-2 rounded mb-2 ${(film.sequel_bonus_applied?.multiplier || 0) >= 1 ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                <div className="flex items-center gap-1">
                  <TrendingUp className={`w-3 h-3 ${(film.sequel_bonus_applied?.multiplier || 0) >= 1 ? 'text-green-400' : 'text-red-400'}`} />
                  <span className={(film.sequel_bonus_applied?.multiplier || 0) >= 1 ? 'text-green-400' : 'text-red-400'}>
                    {film.sequel_bonus_applied?.reason}
                  </span>
                </div>
                <p className="text-gray-400 text-[10px] mt-1">
                  Sequel di "{film.sequel_bonus_applied?.parent_title}" • Bonus: {(film.sequel_bonus_applied?.multiplier || 0) >= 1 ? '+' : ''}{(((film.sequel_bonus_applied?.multiplier || 1) - 1) * 100).toFixed(0)}%
                </p>
              </div>
            )}
            <div className="flex flex-wrap gap-1.5 mb-2">
              <Badge className="bg-yellow-500/20 text-yellow-500 text-xs">{t(film.genre)}</Badge>
              {film.subgenres?.map(sg => <Badge key={sg} variant="outline" className="text-[10px] h-4 border-gray-600">{sg}</Badge>)}
              <Badge className={`text-xs ${film.status==='in_theaters'?'bg-green-500':film.status==='withdrawn'?'bg-orange-500':'bg-gray-500'}`}>{film.status}</Badge>
            </div>
            
            {/* IMDb-style Rating */}
            <div 
              className="flex items-center gap-3 mb-3 p-2 rounded bg-yellow-500/10 border border-yellow-500/20 cursor-pointer hover:bg-yellow-500/15 transition-colors"
              onClick={() => setShowImdbDetail && setShowImdbDetail(true)}
              data-testid="imdb-rating-card"
            >
              <div className="text-center">
                <div className="flex items-center gap-1">
                  <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                  <span className="text-2xl font-bold text-yellow-500">{film.imdb_rating?.toFixed(1) || '0.0'}</span>
                </div>
                <p className="text-[10px] text-gray-400">IMDb Rating</p>
              </div>
              {film.user_avg_rating > 0 && (
                <div className="text-center border-l border-white/10 pl-3">
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-blue-400" />
                    <span className="text-lg font-bold text-blue-400">{film.user_avg_rating?.toFixed(1)}</span>
                  </div>
                  <p className="text-[10px] text-gray-400">{film.rating_count || 0} {language === 'it' ? 'voti' : 'votes'}</p>
                </div>
              )}
              {film.cineboard_score && (
                <div className="text-center border-l border-white/10 pl-3">
                  <span className="text-lg font-bold text-purple-400">{film.cineboard_score?.toFixed(0)}</span>
                  <p className="text-[10px] text-gray-400">CineScore</p>
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              <div 
                className="text-center p-2 rounded bg-white/5 cursor-pointer hover:bg-white/10 transition-colors"
                onClick={() => setShowLikersPopup(true)}
                data-testid="likes-count-btn"
              >
                <Heart className="w-4 h-4 mx-auto mb-0.5 text-pink-400" />
                <p className="font-bold text-sm">{film.likes_count}</p>
                <p className="text-[9px] text-gray-500">{language === 'it' ? 'Like Giocatori' : 'Player Likes'}</p>
              </div>
              <div className="text-center p-2 rounded bg-white/5">
                <Heart className="w-4 h-4 mx-auto mb-0.5 text-red-500 fill-red-500" />
                <p className="font-bold text-sm">{virtualAudience?.virtual_likes?.toLocaleString() || 0}</p>
                <p className="text-[9px] text-gray-500">{language === 'it' ? 'Like Pubblico' : 'Audience Likes'}</p>
              </div>
            </div>
            
            {/* Virtual Audience Bonus Display */}
            {virtualAudience?.bonuses && virtualAudience.bonuses.money_bonus_percent > 0 && (
              <div className="mt-2 p-2 rounded bg-gradient-to-r from-red-500/10 to-pink-500/10 border border-red-500/20">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">{language === 'it' ? 'Bonus Pubblico' : 'Audience Bonus'}</span>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-green-500/20 text-green-400 text-[10px]">
                      +{virtualAudience.bonuses.money_bonus_percent}% {language === 'it' ? 'ricavi' : 'revenue'}
                    </Badge>
                    <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">
                      +{virtualAudience.bonuses.rating_bonus} rating
                    </Badge>
                  </div>
                </div>
              </div>
            )}
            
            {/* Virtual Reviews Section */}
            {virtualAudience?.reviews && virtualAudience.reviews.length > 0 && (
              <div className="mt-2 pt-2 border-t border-white/10">
                <h4 className="text-[10px] font-semibold text-gray-400 mb-1.5 uppercase flex items-center gap-1">
                  <MessageCircle className="w-3 h-3" />
                  {language === 'it' ? 'Recensioni Pubblico' : 'Audience Reviews'}
                </h4>
                <div className="space-y-1.5 max-h-32 overflow-y-auto">
                  {virtualAudience.reviews.slice(0, 3).map((review, idx) => (
                    <div key={idx} className={`p-1.5 rounded text-xs ${review.sentiment === 'positive' ? 'bg-green-500/10 border-l-2 border-green-500' : review.sentiment === 'negative' ? 'bg-red-500/10 border-l-2 border-red-500' : 'bg-white/5 border-l-2 border-gray-500'}`}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="font-medium text-[10px]">{review.reviewer?.display || 'Anonymous'}</span>
                        <span className={`font-bold ${review.rating >= 7 ? 'text-green-400' : review.rating <= 4 ? 'text-red-400' : 'text-yellow-400'}`}>
                          ⭐ {review.rating}
                        </span>
                      </div>
                      <p className="text-gray-300 italic text-[10px] leading-tight">"{review.text}"</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-2 mt-2">
              <div className="text-center p-2 rounded bg-white/5"><DollarSign className="w-4 h-4 mx-auto mb-0.5 text-green-400" /><p className="font-bold text-sm">${(film.total_revenue||0).toLocaleString()}</p><p className="text-[9px] text-gray-500">{language === 'it' ? 'Incasso Totale' : 'Total Revenue'}</p></div>
              <div className="text-center p-2 rounded bg-white/5"><BarChart3 className="w-4 h-4 mx-auto mb-0.5 text-blue-400" /><p className="font-bold text-sm">{film.actual_weeks_in_theater || 0}</p><p className="text-[9px] text-gray-500">{language === 'it' ? 'Settimane' : 'Weeks'}</p></div>
            </div>
            <div className="mt-2 pt-2 border-t border-white/10 space-y-1">
              <div className="flex justify-between text-xs"><span className="text-gray-400">Qualità</span><span>{film.quality_score?.toFixed(0)}%</span></div><Progress value={film.quality_score} className="h-1.5" />
              <div className="flex justify-between text-xs"><span className="text-gray-400">Soddisfazione</span><span>{(film.audience_satisfaction||50).toFixed(0)}%</span></div><Progress value={film.audience_satisfaction||50} className="h-1.5" />
              {film.soundtrack_rating > 0 && (
                <><div className="flex justify-between text-xs"><span className="text-gray-400">Colonna Sonora</span><span className="text-emerald-400">{film.soundtrack_rating}/100</span></div><Progress value={film.soundtrack_rating} className="h-1.5" /></>
              )}
            </div>
            
            {/* Synopsis */}
            {film.synopsis && (
              <div className="mt-3 pt-3 border-t border-white/10">
                <h4 className="text-xs font-semibold text-gray-400 mb-1 uppercase">{language === 'it' ? 'Trama' : 'Synopsis'}</h4>
                <p className="text-sm text-gray-300 leading-relaxed">{film.synopsis}</p>
              </div>
            )}
          </CardContent>
        </Card>
        <div className="lg:col-span-2 space-y-4">
          {/* Hourly Revenue Section - Only for films in theaters */}
          {film.status === 'in_theaters' && (
            <Card className="bg-gradient-to-r from-green-500/10 to-yellow-500/10 border-green-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-400" /> Incassi Orari
                </CardTitle>
              </CardHeader>
              <CardContent>
                {hourlyRevenue && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                    <div className="p-2 rounded bg-black/20 text-center">
                      <p className="text-[10px] text-gray-400">Stima Oraria</p>
                      <p className="text-lg font-bold text-green-400">${hourlyRevenue.revenue?.toLocaleString()}</p>
                    </div>
                    <div className="p-2 rounded bg-black/20 text-center">
                      <p className="text-[10px] text-gray-400">Giorni in Sala</p>
                      <p className="text-lg font-bold">{hourlyRevenue.days_in_theater || durationStatus?.current_days || 1}</p>
                    </div>
                    <div className="p-2 rounded bg-black/20 text-center">
                      <p className="text-[10px] text-gray-400">Moltiplicatore</p>
                      <p className="text-lg font-bold text-yellow-400">x{((hourlyRevenue.factors?.quality_mult || 1) * (hourlyRevenue.factors?.genre_mult || 1)).toFixed(2)}</p>
                    </div>
                    <div className="p-2 rounded bg-black/20 text-center">
                      <p className="text-[10px] text-gray-400">Imprevedibilità</p>
                      <p className="text-lg font-bold">{((hourlyRevenue.factors?.unpredictability || 1) * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  {/* Hourly revenue - always available for owner */}
                  {isOwner && (
                    <Button onClick={processHourlyRevenue} disabled={processing} className="bg-green-600 hover:bg-green-500">
                      {processing ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : <DollarSign className="w-4 h-4 mr-1" />}
                      {language === 'it' ? 'Incassa Ora' : 'Collect Now'}
                    </Button>
                  )}
                  {/* Create Star - ONE TIME */}
                  {isOwner && (
                    <Button 
                      variant="outline" 
                      onClick={checkStarDiscoveries} 
                      disabled={!isActionAvailable('create_star') || performingAction === 'create_star'}
                      className={`border-yellow-500/30 ${!isActionAvailable('create_star') ? 'opacity-50 cursor-not-allowed' : 'text-yellow-400'}`}
                      title={!isActionAvailable('create_star') ? (language === 'it' ? 'Già utilizzato' : 'Already used') : ''}
                    >
                      <Star className="w-4 h-4 mr-1" /> {language === 'it' ? 'Crea Stella' : 'Create Star'}
                      {!isActionAvailable('create_star') && <Lock className="w-3 h-3 ml-1" />}
                    </Button>
                  )}
                  {/* Skill Boost - ONE TIME */}
                  {isOwner && (
                    <Button 
                      variant="outline" 
                      onClick={performSkillBoost} 
                      disabled={!isActionAvailable('skill_boost') || performingAction === 'skill_boost'}
                      className={`border-blue-500/30 ${!isActionAvailable('skill_boost') ? 'opacity-50 cursor-not-allowed' : 'text-blue-400'}`}
                      title={!isActionAvailable('skill_boost') ? (language === 'it' ? 'Già utilizzato' : 'Already used') : ''}
                    >
                      {performingAction === 'skill_boost' ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : <TrendingUp className="w-4 h-4 mr-1" />}
                      {language === 'it' ? 'Boost Skill Cast' : 'Boost Cast Skills'}
                      {!isActionAvailable('skill_boost') && <Lock className="w-3 h-3 ml-1" />}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Duration Status */}
          {film.status === 'in_theaters' && durationStatus && (
            <Card className={`border ${durationStatus.status === 'extend' ? 'bg-green-500/10 border-green-500/30' : durationStatus.status === 'withdraw_early' ? 'bg-red-500/10 border-red-500/30' : 'bg-[#1A1A1A] border-white/10'}`}>
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-yellow-500" /> Stato Programmazione
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{durationStatus.current_days}</p>
                    <p className="text-[10px] text-gray-400">Giorni trascorsi</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">{durationStatus.planned_days}</p>
                    <p className="text-[10px] text-gray-400">Giorni pianificati</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-yellow-400">{durationStatus.days_remaining}</p>
                    <p className="text-[10px] text-gray-400">Giorni rimanenti</p>
                  </div>
                </div>
                <div className="p-2 rounded bg-black/20 mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">{language === 'it' ? 'Punteggio Performance:' : 'Performance Score:'}</span>
                    <span className={`font-bold ${durationStatus.score > 0 ? 'text-green-400' : durationStatus.score < 0 ? 'text-red-400' : 'text-gray-400'}`}>{durationStatus.score > 0 ? '+' : ''}{durationStatus.score}</span>
                  </div>
                  <div className="text-[10px] text-gray-400">
                    {durationStatus.reasons?.slice(0, 3).map((r, i) => <div key={i}>{r}</div>)}
                  </div>
                </div>
                {durationStatus.status === 'extend' && durationStatus.can_extend && (
                  <div className="p-3 rounded bg-green-500/20 border border-green-500/30 mb-3">
                    <p className="text-green-400 font-semibold flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Film idoneo per estensione!</p>
                    <p className="text-xs text-gray-300">Puoi estendere fino a {durationStatus.max_days_per_extension || 3} giorni extra.</p>
                    <p className="text-xs text-green-300">Fame bonus: +{durationStatus.fame_change}</p>
                    <p className="text-[10px] text-gray-400 mt-1">Estensioni: {durationStatus.extension_count || 0}/{durationStatus.max_extensions || 1}</p>
                    <Button onClick={extendFilm} size="sm" className="mt-2 bg-green-600">Estendi di 3 giorni</Button>
                  </div>
                )}
                {durationStatus.status === 'extend' && !durationStatus.can_extend && durationStatus.extension_count < 1 && (
                  <div className="p-3 rounded bg-yellow-500/20 border border-yellow-500/30 mb-3">
                    <p className="text-yellow-400 font-semibold flex items-center gap-2"><Clock className="w-4 h-4" /> Estensione in cooldown</p>
                    <p className="text-xs text-gray-300">Attendi {durationStatus.days_until_next_extension} giorni prima di estendere.</p>
                    <p className="text-[10px] text-gray-400">Estensioni: {durationStatus.extension_count || 0}/{durationStatus.max_extensions || 1}</p>
                  </div>
                )}
                {durationStatus.extension_count >= 1 && (
                  <div className="p-3 rounded bg-gray-500/20 border border-gray-500/30 mb-3">
                    <p className="text-gray-400 font-semibold flex items-center gap-2"><Check className="w-4 h-4" /> Estensione esaurita</p>
                    <p className="text-xs text-gray-400">Hai usato l'unica estensione disponibile.</p>
                    <p className="text-[10px] text-gray-500">Giorni totali aggiunti: +{durationStatus.total_extension_days || 0}</p>
                  </div>
                )}
                {durationStatus.status === 'withdraw_early' && (
                  <div className="p-3 rounded bg-red-500/20 border border-red-500/30">
                    <p className="text-red-400 font-semibold flex items-center gap-2"><TrendingDown className="w-4 h-4" /> Performance scarsa</p>
                    <p className="text-xs text-gray-300">Il film potrebbe essere ritirato anticipatamente.</p>
                    <p className="text-xs text-red-300">Fame penalty: {durationStatus.fame_change}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
          
          {/* Re-release Section - For withdrawn/completed films owned by user */}
          {isOwner && (film.status === 'withdrawn' || film.status === 'completed') && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-purple-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  <RotateCcw className="w-5 h-5 text-purple-400" /> 
                  {language === 'it' ? 'Rimetti in Sala' : 'Re-release'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {rereleaseStatus?.can_rerelease ? (
                  <div className="space-y-3">
                    <p className="text-sm text-gray-300">
                      {language === 'it' 
                        ? 'Puoi rimettere questo film nelle sale cinematografiche!'
                        : 'You can bring this film back to theaters!'}
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-2 rounded bg-black/20 text-center">
                        <p className="text-[10px] text-gray-400">{language === 'it' ? 'Costo' : 'Cost'}</p>
                        <p className="text-lg font-bold text-yellow-400">${rereleaseStatus.cost?.toLocaleString()}</p>
                      </div>
                      <div className="p-2 rounded bg-black/20 text-center">
                        <p className="text-[10px] text-gray-400">{language === 'it' ? 'Uscite precedenti' : 'Previous releases'}</p>
                        <p className="text-lg font-bold">{rereleaseStatus.times_released || 1}</p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500">
                      {language === 'it' 
                        ? `Costo: 30% del budget originale ($${rereleaseStatus.original_budget?.toLocaleString()})`
                        : `Cost: 30% of original budget ($${rereleaseStatus.original_budget?.toLocaleString()})`}
                    </p>
                    <Button 
                      onClick={handleRerelease} 
                      disabled={rereleasing || (user?.funds || 0) < rereleaseStatus.cost}
                      className="w-full bg-purple-600 hover:bg-purple-500"
                    >
                      {rereleasing ? (
                        <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> {language === 'it' ? 'Rilancio...' : 'Releasing...'}</>
                      ) : (
                        <><RotateCcw className="w-4 h-4 mr-2" /> {language === 'it' ? 'Rimetti in Sala' : 'Re-release'} - ${rereleaseStatus.cost?.toLocaleString()}</>
                      )}
                    </Button>
                  </div>
                ) : rereleaseStatus?.days_remaining > 0 ? (
                  <div className="space-y-3">
                    <p className="text-sm text-gray-300">
                      {language === 'it' 
                        ? 'Questo film non può essere ancora rimesso in sala.'
                        : 'This film cannot be re-released yet.'}
                    </p>
                    <div className="p-3 rounded bg-black/20 text-center">
                      <Clock className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
                      <p className="text-2xl font-bold text-yellow-400">{rereleaseStatus.days_remaining}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'giorni rimanenti' : 'days remaining'}</p>
                    </div>
                    <p className="text-xs text-gray-500 text-center">
                      {language === 'it' 
                        ? 'Devi aspettare 7 giorni dalla rimozione prima di poter rimettere il film in sala.'
                        : 'You must wait 7 days after withdrawal before re-releasing.'}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">
                    {rereleaseStatus?.reason || (language === 'it' ? 'Verifica stato in corso...' : 'Checking status...')}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Cinema Distribution Section - Where the film is showing */}
          {distribution && distribution.current_cinemas > 0 && (
            <Card className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-blue-400" /> 
                  {language === 'it' ? 'In Programmazione' : 'Now Showing In'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                  <Dialog>
                    <DialogTrigger asChild>
                      <div className="p-2 rounded bg-black/20 text-center cursor-pointer hover:bg-black/40 transition-colors ring-1 ring-blue-500/30" data-testid="cinema-distribution-trigger">
                        <p className="text-[10px] text-gray-400">{language === 'it' ? 'Cinema' : 'Cinemas'}</p>
                        <p className="text-xl font-bold text-blue-400">{distribution.current_cinemas}</p>
                        <p className="text-[8px] text-blue-400/60 mt-0.5">{language === 'it' ? 'Dettagli' : 'Details'}</p>
                      </div>
                    </DialogTrigger>
                    <DialogContent className="bg-[#1a1a2e] border-blue-500/30 max-w-md max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                          <MapPin className="w-5 h-5 text-blue-400" />
                          {language === 'it' ? 'Distribuzione per Paese' : 'Distribution by Country'}
                        </DialogTitle>
                      </DialogHeader>
                      <div className="space-y-1.5">
                        {distribution.distribution?.map((country, idx) => (
                          <div key={idx} className="flex items-center justify-between p-2 rounded bg-black/20">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{
                                country.country_code === 'US' ? '🇺🇸' :
                                country.country_code === 'IT' ? '🇮🇹' :
                                country.country_code === 'FR' ? '🇫🇷' :
                                country.country_code === 'DE' ? '🇩🇪' :
                                country.country_code === 'UK' ? '🇬🇧' :
                                country.country_code === 'ES' ? '🇪🇸' :
                                country.country_code === 'JP' ? '🇯🇵' :
                                country.country_code === 'CN' ? '🇨🇳' :
                                country.country_code === 'BR' ? '🇧🇷' :
                                country.country_code === 'MX' ? '🇲🇽' : '🌍'
                              }</span>
                              <span className="font-medium">{country.country_name}</span>
                            </div>
                            <div className="flex items-center gap-3 text-sm">
                              <span className="text-blue-400">{country.cinemas} {language === 'it' ? 'cinema' : 'cinemas'}</span>
                              <span className="text-green-400">{country.total_attendance?.toLocaleString()} {language === 'it' ? 'spett.' : 'viewers'}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </DialogContent>
                  </Dialog>
                  <div className="p-2 rounded bg-black/20 text-center">
                    <p className="text-[10px] text-gray-400">{language === 'it' ? 'Spettatori' : 'Viewers'}</p>
                    <p className="text-xl font-bold text-green-400">{distribution.current_attendance?.toLocaleString()}</p>
                  </div>
                  <div className="p-2 rounded bg-black/20 text-center">
                    <p className="text-[10px] text-gray-400">{language === 'it' ? 'Media/Cinema' : 'Avg/Cinema'}</p>
                    <p className="text-xl font-bold">{distribution.avg_attendance_per_cinema}</p>
                  </div>
                  <div className="p-2 rounded bg-black/20 text-center">
                    <p className="text-[10px] text-gray-400">{language === 'it' ? 'Totale Storico' : 'Total All-Time'}</p>
                    <p className="text-xl font-bold text-purple-400">{(distribution.cumulative_attendance || 0).toLocaleString()}</p>
                  </div>
                </div>
                
                {/* Trend indicator */}
                <div className="mt-3 pt-3 border-t border-white/10 flex items-center justify-between">
                  <span className="text-xs text-gray-400">{language === 'it' ? 'Tendenza' : 'Trend'}</span>
                  <span className={`flex items-center gap-1 text-sm font-semibold ${
                    distribution.trend === 'growing' ? 'text-green-400' :
                    distribution.trend === 'declining' ? 'text-red-400' :
                    distribution.trend === 'stable' ? 'text-yellow-400' : 'text-gray-400'
                  }`}>
                    {distribution.trend === 'growing' && <><TrendingUp className="w-4 h-4" /> {language === 'it' ? 'In Crescita' : 'Growing'}</>}
                    {distribution.trend === 'declining' && <><TrendingDown className="w-4 h-4" /> {language === 'it' ? 'In Calo' : 'Declining'}</>}
                    {distribution.trend === 'stable' && <><span>→</span> {language === 'it' ? 'Stabile' : 'Stable'}</>}
                    {distribution.trend === 'new' && <><Sparkles className="w-4 h-4" /> {language === 'it' ? 'Nuovo' : 'New'}</>}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Cast Section */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2"><CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><Users className="w-4 h-4 text-yellow-500" /> Cast & Crew</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {/* Director & Screenwriter */}
              <div className="grid grid-cols-2 gap-2">
                {film.director && typeof film.director === 'object' && (
                  <div className="p-2 rounded bg-white/5">
                    <p className="text-[10px] text-gray-500 uppercase mb-1">Director</p>
                    <div className="flex items-center gap-2">
                      <Avatar className="w-8 h-8"><AvatarImage src={film.director?.avatar_url} /><AvatarFallback className="text-[10px] bg-yellow-500/20">{film.director?.name?.[0]}</AvatarFallback></Avatar>
                      <div>
                        <p className="text-sm font-semibold">{film.director?.name} <span className={`${film.director?.gender === 'female' ? 'text-pink-400' : 'text-blue-400'}`}>{film.director?.gender === 'female' ? '♀' : '♂'}</span></p>
                        <p className="text-[10px] text-gray-400">{film.director?.nationality}</p>
                      </div>
                    </div>
                  </div>
                )}
                {film.screenwriter && typeof film.screenwriter === 'object' && (
                  <div className="p-2 rounded bg-white/5">
                    <p className="text-[10px] text-gray-500 uppercase mb-1">Screenwriter</p>
                    <div className="flex items-center gap-2">
                      <Avatar className="w-8 h-8"><AvatarImage src={film.screenwriter?.avatar_url} /><AvatarFallback className="text-[10px] bg-yellow-500/20">{film.screenwriter?.name?.[0]}</AvatarFallback></Avatar>
                      <div>
                        <p className="text-sm font-semibold">{film.screenwriter?.name} <span className={`${film.screenwriter?.gender === 'female' ? 'text-pink-400' : 'text-blue-400'}`}>{film.screenwriter?.gender === 'female' ? '♀' : '♂'}</span></p>
                        <p className="text-[10px] text-gray-400">{film.screenwriter?.nationality}</p>
                      </div>
                    </div>
                  </div>
                )}
                {film.composer && typeof film.composer === 'object' && (
                  <div className="p-2 rounded bg-white/5">
                    <p className="text-[10px] text-gray-500 uppercase mb-1">Colonna Sonora</p>
                    <div className="flex items-center gap-2">
                      <Avatar className="w-8 h-8"><AvatarFallback className="text-[10px] bg-emerald-500/20 text-emerald-400">{film.composer?.name?.[0]}</AvatarFallback></Avatar>
                      <div className="flex-1">
                        <p className="text-sm font-semibold">{film.composer?.name}</p>
                        {film.composer?.imdb_rating > 0 && (
                          <div className="flex items-center gap-1 mt-0.5">
                            <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                            <span className="text-xs text-yellow-400 font-bold">{film.composer?.imdb_rating}/100</span>
                            <span className="text-[10px] text-gray-500 ml-1">Rating Colonna Sonora</span>
                          </div>
                        )}
                      </div>
                    </div>
                    {film.soundtrack_boost && typeof film.soundtrack_boost === 'object' && (
                      <div className="mt-1.5 flex gap-1">
                        <span className="text-[9px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded">G1: +{Math.round(((film.soundtrack_boost?.day_1_multiplier || 1) - 1) * 100)}%</span>
                        <span className="text-[9px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded">G2: +{Math.round(((film.soundtrack_boost?.day_2_multiplier || 1) - 1) * 100)}%</span>
                        <span className="text-[9px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded">G3: +{Math.round(((film.soundtrack_boost?.day_3_multiplier || 1) - 1) * 100)}%</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
              {/* Actors */}
              {Array.isArray(film.cast) && film.cast.length > 0 && (
                <div>
                  <p className="text-[10px] text-gray-500 uppercase mb-2">Cast ({film.cast.length} actors)</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {film.cast.map(actor => (
                      <div key={actor?.id || actor?.actor_id || Math.random()} className="flex items-center gap-2 p-2 rounded bg-white/5">
                        <Avatar className="w-8 h-8"><AvatarImage src={actor?.avatar_url} /><AvatarFallback className="text-[10px] bg-yellow-500/20">{actor?.name?.[0]}</AvatarFallback></Avatar>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            <p className="text-sm font-semibold truncate">{actor?.name}</p>
                            <span className={`text-xs ${actor?.gender === 'female' ? 'text-pink-400' : 'text-blue-400'}`}>{actor?.gender === 'female' ? '♀' : '♂'}</span>
                          </div>
                          <p className="text-[10px] text-gray-400">{actor.nationality}</p>
                        </div>
                        {actor.role && getRoleBadge(actor.role)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
          {/* Trailer Section */}
          <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30" data-testid="trailer-section">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <Film className="w-5 h-5 text-purple-400" /> Trailer
                {film.trailer_url && <Badge className="bg-green-500/20 text-green-400 text-xs ml-2">Generato</Badge>}
              </CardTitle>
              <CardDescription className="text-xs">{language === 'it' ? 'Genera un trailer promozionale gratuito' : 'Generate a free promotional trailer'}</CardDescription>
            </CardHeader>
            <CardContent>
              {film.trailer_url ? (
                <div className="space-y-3">
                  <div className="aspect-[9/16] max-h-[400px] mx-auto bg-black rounded-lg overflow-hidden">
                    <video 
                      src={`${BACKEND_URL}${film.trailer_url}`} 
                      controls 
                      className="w-full h-full"
                      poster={film.poster_url}
                    >
                      Il tuo browser non supporta i video.
                    </video>
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-green-400">{language === 'it' ? 'Trailer pronto!' : 'Trailer ready!'}</p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-purple-500/50 text-purple-400 hover:bg-purple-500/20"
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = `${BACKEND_URL}${film.trailer_url}`;
                        link.download = `trailer_${film.title || 'film'}.mp4`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        toast.success('Download trailer avviato!');
                      }}
                      data-testid="download-trailer-btn"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Scarica
                    </Button>
                  </div>
                </div>
              ) : generatingTrailer ? (
                <div className="text-center py-8 space-y-3">
                  <RefreshCw className="w-10 h-10 mx-auto text-purple-400 animate-spin" />
                  <p className="text-purple-300">{language === 'it' ? 'Generazione trailer in corso...' : 'Generating trailer...'}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Attendere qualche secondo' : 'Please wait a few seconds'}</p>
                </div>
              ) : (
                <div className="text-center py-6 space-y-3">
                  <Film className="w-12 h-12 mx-auto text-purple-400/50" />
                  {isOwner ? (
                    <Button 
                      onClick={() => generateTrailer()} 
                      size="sm" 
                      className="bg-purple-600 hover:bg-purple-500"
                      data-testid="generate-trailer-btn"
                    >
                      <Video className="w-4 h-4 mr-1" />
                      {language === 'it' ? 'Genera Trailer Gratuito' : 'Generate Free Trailer'}
                    </Button>
                  ) : (
                    <p className="text-xs text-gray-500">
                      {language === 'it' ? 'Solo il proprietario può generare il trailer' : 'Only the owner can generate the trailer'}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Likers Popup */}
      {showLikersPopup && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowLikersPopup(false)}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] border border-white/10 rounded-xl p-4 max-w-md w-full max-h-[70vh] overflow-hidden"
            onClick={e => e.stopPropagation()}
            data-testid="likers-popup"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
                <Heart className="w-5 h-5 text-red-400 fill-red-400" />
                {language === 'it' ? `Chi ha messo Like (${film.likes_count || 0})` : `Who Liked (${film.likes_count || 0})`}
              </h3>
              <button onClick={() => setShowLikersPopup(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <ScrollArea className="h-[50vh]">
              {loadingLikers ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto text-yellow-500" />
                </div>
              ) : likers.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Heart className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p>{language === 'it' ? 'Nessun like ancora' : 'No likes yet'}</p>
                </div>
              ) : (
                <div className="space-y-2 pr-2">
                  {likers.map((liker, idx) => (
                    <div 
                      key={idx} 
                      className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors"
                      onClick={() => { setShowLikersPopup(false); navigate(`/player/${liker.user_id}`); }}
                    >
                      <img 
                        src={liker.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${liker.nickname}`} 
                        alt={liker.nickname}
                        className="w-10 h-10 rounded-full"
                      />
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{liker.nickname}</p>
                        <p className="text-xs text-gray-400">{liker.production_house}</p>
                      </div>
                      <div className="text-[10px] text-gray-500">
                        {new Date(liker.liked_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </motion.div>
        </div>
      )}
      
      {/* End of Run Expectations Popup */}
      {showEndRunPopup && endRunData && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4" onClick={() => setShowEndRunPopup(false)}>
          <motion.div
            initial={{ scale: 0.8, opacity: 0, y: 50 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            transition={{ type: 'spring', duration: 0.6 }}
            className={`bg-gradient-to-br ${
              endRunData.exceeded ? 'from-yellow-500/30 to-amber-500/30 border-yellow-500' :
              endRunData.met_expectations ? 'from-green-500/30 to-emerald-500/30 border-green-500' :
              'from-red-500/30 to-orange-500/30 border-red-500'
            } border-2 rounded-2xl p-6 max-w-md w-full text-center relative overflow-hidden`}
            onClick={e => e.stopPropagation()}
            data-testid="end-run-popup"
          >
            {/* Background decoration */}
            {endRunData.exceeded && (
              <div className="absolute inset-0 overflow-hidden pointer-events-none">
                {[...Array(20)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="absolute text-2xl"
                    initial={{ y: -20, x: Math.random() * 300, opacity: 0 }}
                    animate={{ y: 400, opacity: [0, 1, 1, 0], rotate: 360 }}
                    transition={{ duration: 3, delay: i * 0.15, repeat: Infinity }}
                  >
                    {['🎉', '⭐', '🏆', '✨'][i % 4]}
                  </motion.div>
                ))}
              </div>
            )}
            
            {/* Main icon */}
            <motion.div 
              className="text-6xl mb-4"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              {endRunData.exceeded ? '🏆' : endRunData.met_expectations ? '✅' : '📊'}
            </motion.div>
            
            {/* Title */}
            <h2 className={`font-['Bebas_Neue'] text-3xl mb-2 ${
              endRunData.exceeded ? 'text-yellow-400' :
              endRunData.met_expectations ? 'text-green-400' : 'text-orange-400'
            }`}>
              {language === 'it' ? 'Programmazione Terminata!' : 'Theater Run Complete!'}
            </h2>
            
            {/* Film title */}
            <p className="text-lg text-gray-300 mb-4">"{endRunData.film_title}"</p>
            
            {/* Tier Badge */}
            {endRunData.tier && endRunData.tier !== 'normal' && (
              <div className={`inline-block px-4 py-1 rounded-full mb-4 ${
                endRunData.tier === 'masterpiece' ? 'bg-yellow-500/30 text-yellow-400' :
                endRunData.tier === 'epic' ? 'bg-purple-500/30 text-purple-400' :
                endRunData.tier === 'excellent' ? 'bg-blue-500/30 text-blue-400' :
                endRunData.tier === 'promising' ? 'bg-green-500/30 text-green-400' :
                endRunData.tier === 'flop' ? 'bg-red-500/30 text-red-400' : 'bg-gray-500/30 text-gray-400'
              }`}>
                {endRunData.film_tier_info?.emoji} {endRunData.film_tier_info?.name || endRunData.tier}
              </div>
            )}
            
            {/* Stats comparison */}
            <div className="bg-black/30 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">{language === 'it' ? 'Previsto' : 'Expected'}</p>
                  <p className="text-xl font-bold text-gray-300">${endRunData.expected_revenue?.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">{language === 'it' ? 'Effettivo' : 'Actual'}</p>
                  <p className={`text-xl font-bold ${
                    endRunData.ratio >= 1 ? 'text-green-400' : 'text-red-400'
                  }`}>${endRunData.actual_revenue?.toLocaleString()}</p>
                </div>
              </div>
              
              {/* Performance ratio bar */}
              <div className="relative h-4 bg-black/40 rounded-full overflow-hidden mb-2">
                <motion.div 
                  className={`absolute h-full rounded-full ${
                    endRunData.ratio >= 1.2 ? 'bg-yellow-500' :
                    endRunData.ratio >= 1 ? 'bg-green-500' :
                    endRunData.ratio >= 0.8 ? 'bg-orange-500' : 'bg-red-500'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, (endRunData.ratio || 0) * 100)}%` }}
                  transition={{ duration: 1, delay: 0.3 }}
                />
                <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-white/30"></div>
              </div>
              <p className={`text-sm font-bold ${
                endRunData.ratio >= 1.2 ? 'text-yellow-400' :
                endRunData.ratio >= 1 ? 'text-green-400' :
                endRunData.ratio >= 0.8 ? 'text-orange-400' : 'text-red-400'
              }`}>
                {((endRunData.ratio || 0) * 100).toFixed(0)}% {language === 'it' ? 'delle aspettative' : 'of expectations'}
              </p>
            </div>
            
            {/* Message */}
            <p className={`text-lg mb-4 ${
              endRunData.message_type === 'success' ? 'text-green-400' :
              endRunData.message_type === 'positive' ? 'text-blue-400' :
              endRunData.message_type === 'negative' ? 'text-red-400' : 'text-gray-300'
            }`}>
              {endRunData.message}
            </p>
            
            {/* Special messages for surprises */}
            {endRunData.exceeded && endRunData.tier === 'flop' && (
              <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3 mb-4">
                <p className="text-yellow-400 font-bold text-sm">
                  {language === 'it' 
                    ? '🎭 Il film che era un "Possibile Flop" è diventato un successo inaspettato!'
                    : '🎭 The "Potential Flop" turned into an unexpected hit!'}
                </p>
              </div>
            )}
            
            {!endRunData.met_expectations && endRunData.tier !== 'flop' && (
              <div className="bg-orange-500/20 border border-orange-500/50 rounded-lg p-3 mb-4">
                <p className="text-orange-400 font-bold text-sm">
                  {language === 'it' 
                    ? '📉 Nonostante le aspettative, il film non ha performato come previsto.'
                    : '📉 Despite expectations, the film underperformed.'}
                </p>
              </div>
            )}
            
            <Button 
              className={`w-full font-bold text-lg py-6 ${
                endRunData.exceeded ? 'bg-yellow-500 hover:bg-yellow-600 text-black' :
                endRunData.met_expectations ? 'bg-green-600 hover:bg-green-700' : 'bg-orange-600 hover:bg-orange-700'
              }`}
              onClick={() => setShowEndRunPopup(false)}
            >
              {language === 'it' ? 'Continua' : 'Continue'}
            </Button>
          </motion.div>
        </div>
      )}

      {/* IMDb Detail Popup */}
      <Dialog open={showImdbDetail} onOpenChange={setShowImdbDetail}>
        <DialogContent className="bg-[#1A1A1A] border-yellow-500/20 max-w-sm max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" /> IMDb Rating Breakdown
            </DialogTitle>
          </DialogHeader>
          {film && (() => {
            const quality = film.quality_score || 0;
            const qualityRating = (quality / 100) * 4;
            const likes = film.likes_count || 0;
            const engagementRating = Math.min(Math.log10(likes + 1) / 2.5, 1.0) * 3;
            const awards = (film.awards || []).length;
            const nominations = (film.nominations || []).length;
            const criticalRating = Math.min((awards * 0.5 + nominations * 0.2) / 2, 1.0) * 2;
            const budget = film.total_budget || 1000000;
            const revenue = film.total_revenue || 0;
            const roi = budget > 0 ? revenue / budget : 0;
            const revenueRating = Math.min(roi / 5, 1.0) * 1;
            const total = qualityRating + engagementRating + criticalRating + revenueRating;
            const imdb = Math.min(4 + (total / 10) * 6, 10.0);
            
            const factors = [
              { name: language === 'it' ? 'Qualità Produzione' : 'Production Quality', weight: '40%', score: qualityRating, max: 4, detail: `${quality.toFixed(0)}%`, icon: Film },
              { name: language === 'it' ? 'Engagement Pubblico' : 'Audience Engagement', weight: '30%', score: engagementRating, max: 3, detail: `${likes} likes`, icon: Heart },
              { name: language === 'it' ? 'Ricezione Critica' : 'Critical Reception', weight: '20%', score: criticalRating, max: 2, detail: `${awards} premi, ${nominations} nomine`, icon: Award },
              { name: language === 'it' ? 'Successo Commerciale' : 'Commercial Success', weight: '10%', score: revenueRating, max: 1, detail: `ROI: ${(roi * 100).toFixed(0)}%`, icon: DollarSign },
              { name: language === 'it' ? 'Punteggio Audience' : 'Audience Score', weight: 'bonus', score: (film.audience_satisfaction || 50) / 100, max: 1, detail: `${(film.audience_satisfaction || 50).toFixed(0)}%`, icon: Users },
              { name: language === 'it' ? 'Popolarità' : 'Popularity', weight: 'bonus', score: Math.min((film.popularity_score || 0) / 100, 1), max: 1, detail: `${(film.popularity_score || 0).toFixed(0)}`, icon: TrendingUp }
            ].sort((a, b) => b.score - a.score).slice(0, 6);
            
            return (
              <div className="space-y-3">
                <div className="text-center py-3">
                  <div className="text-5xl font-bold text-yellow-500">{imdb.toFixed(1)}</div>
                  <p className="text-xs text-gray-400 mt-1">{language === 'it' ? 'su 10' : 'out of 10'}</p>
                </div>
                <div className="space-y-2">
                  {factors.map((f, i) => (
                    <div key={i} className="p-2 rounded bg-white/5 border border-white/10">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <f.icon className="w-3.5 h-3.5 text-yellow-500" />
                          <span className="text-sm font-semibold">{f.name}</span>
                        </div>
                        <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">{f.weight}</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Progress value={(f.score / f.max) * 100} className="flex-1 h-1.5" />
                        <span className="text-xs text-gray-400 w-16 text-right">{f.detail}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FilmDetail;
