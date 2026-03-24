// CineWorld Studio's - MyFilms
// Extracted from App.js for modularity

import React, { useState, useEffect, useRef, useCallback, useMemo, useContext } from 'react';
import { useNavigate, useLocation, useSearchParams, useParams } from 'react-router-dom';
import { AuthContext, LanguageContext, PlayerPopupContext, useTranslations } from '../contexts';
import { useSWR } from '../contexts/GameStore';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400';
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, Tv
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';

// useTranslations imported from contexts

const MyFilms = () => {
  const { api, user, cachedGet } = useContext(AuthContext);
  const { t } = useTranslations();
  const [searchParams] = useSearchParams();
  const currentView = searchParams.get('view') || 'film';
  const [films, setFilms] = useState([]);
  const [series, setSeries] = useState([]);
  const [showAdDialog, setShowAdDialog] = useState(null);
  const [adPlatforms, setAdPlatforms] = useState([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [adDays, setAdDays] = useState(7);
  const [adLoading, setAdLoading] = useState(false);
  const [regenLoading, setRegenLoading] = useState(null);
  const navigate = useNavigate();

  // SWR for films - instant load from cache
  const { data: filmsData, mutate: refreshFilms } = useSWR(currentView === 'film' ? '/films/my' : null);
  useEffect(() => { if (filmsData) setFilms(filmsData); }, [filmsData]);

  useEffect(() => { 
    if (currentView === 'film') {
      api.get('/advertising/platforms').then(r=>setAdPlatforms(r.data)).catch(()=>{});
    } else {
      const sType = currentView === 'anime' ? 'anime' : 'tv_series';
      api.get(`/series-pipeline/my?series_type=${sType}`).then(r=>setSeries(r.data.series || [])).catch(()=>{});
    }
  }, [api, currentView]);

  const withdrawFilm = async (filmId) => {
    try {
      await api.delete(`/films/${filmId}`);
      toast.success('Film ritirato dalle sale');
      setFilms(films.map(f => f.id === filmId ? { ...f, status: 'withdrawn' } : f));
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const launchAdCampaign = async (filmId) => {
    if (selectedPlatforms.length === 0) { toast.error('Seleziona almeno una piattaforma'); return; }
    setAdLoading(true);
    try {
      const res = await api.post(`/films/${filmId}/advertise`, { platforms: selectedPlatforms, days: adDays, budget: 0 });
      toast.success(`Campagna lanciata! +$${res.data.revenue_boost?.toLocaleString()} incassi!`);
      setShowAdDialog(null); setSelectedPlatforms([]);
      api.get('/films/my').then(r => setFilms(r.data));
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } 
    finally { setAdLoading(false); }
  };

  const calculateAdCost = () => selectedPlatforms.reduce((s, pId) => { const p = adPlatforms.find(x => x.id === pId); return s + (p ? p.cost_per_day * adDays : 0); }, 0);

  const regeneratePoster = async (filmId, e) => {
    e.stopPropagation();
    setRegenLoading(filmId);
    try {
      // Start async generation
      const startRes = await api.post(`/films/${filmId}/regenerate-poster`, {});
      const taskId = startRes.data.task_id;
      if (!taskId) { toast.error('Errore avvio rigenerazione'); setRegenLoading(null); return; }
      toast.info('Generazione locandina AI in corso...');
      
      // Poll for result
      const maxPolls = 40;
      for (let i = 0; i < maxPolls; i++) {
        await new Promise(r => setTimeout(r, 3000));
        try {
          const statusRes = await api.get(`/ai/poster/status/${taskId}`);
          const { status, poster_url, error } = statusRes.data;
          if (status === 'done' && poster_url) {
            setFilms(prev => prev.map(f => f.id === filmId ? { ...f, poster_url } : f));
            toast.success('Locandina rigenerata!');
            setRegenLoading(null);
            return;
          }
          if (status === 'error') {
            toast.error(error || 'Errore generazione locandina');
            setRegenLoading(null);
            return;
          }
        } catch { /* polling error, continue */ }
      }
      toast.error('Timeout generazione locandina');
    } catch (err) {
      const detail = err.response?.data?.detail || err.response?.data?.error || err.message || 'Errore rigenerazione locandina';
      toast.error(`Errore: ${detail}`);
      console.error('Regenerate poster error:', err.response?.data || err.message);
    } finally {
      setRegenLoading(null);
    }
  };

  // Series/Anime View
  if (currentView === 'series' || currentView === 'anime') {
    const isAnime = currentView === 'anime';
    const color = isAnime ? 'orange' : 'blue';
    const Icon = isAnime ? Sparkles : Tv;
    const label = isAnime ? 'I Miei Anime' : 'Le Mie Serie TV';
    const createRoute = isAnime ? '/create-anime' : '/create-series';
    const boardRoute = isAnime ? '/social?view=anime' : '/social?view=series';

    return (
      <div className="pt-16 pb-20 px-2 sm:px-3 max-w-7xl mx-auto" data-testid={`my-${currentView}-page`}>
        <div className="flex items-center justify-between mb-4 sticky top-16 z-10 bg-[#0F0F10]/95 backdrop-blur-sm py-2 -mx-2 sm:-mx-3 px-2 sm:px-3">
          <h1 className={`font-['Bebas_Neue'] text-2xl sm:text-3xl text-${color}-400`}>{label}</h1>
          <div className="flex gap-1.5">
            <Button size="sm" variant="outline" onClick={() => navigate(boardRoute)} className={`h-8 px-2 text-xs border-${color}-500/30 text-${color}-400`}><Trophy className="w-3 h-3 mr-1" />Classifica</Button>
            <Button size="sm" onClick={() => navigate(createRoute)} className={`bg-${color}-500 text-white h-8 px-2 text-xs`}><Plus className="w-3 h-3 mr-1" />Crea</Button>
          </div>
        </div>
        {series.length === 0 ? (
          <Card className="bg-[#1A1A1A] border-white/10 p-6 text-center">
            <Icon className="w-10 h-10 mx-auto mb-3 text-gray-600" />
            <h3 className="text-base mb-2">{isAnime ? 'Nessun anime ancora' : 'Nessuna serie TV ancora'}</h3>
            <Button onClick={() => navigate(createRoute)} className={`bg-${color}-500 text-white text-sm`}>{isAnime ? 'Crea il tuo primo Anime' : 'Crea la tua prima Serie TV'}</Button>
          </Card>
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-1 sm:gap-1.5">
            {series.map(s => (
              <Card key={s.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden hover:border-white/15 transition-colors">
                <div className="aspect-[2/3] relative cursor-pointer" onClick={() => navigate(boardRoute)}>
                  {s.poster_url ? (
                    <img src={posterSrc(s.poster_url)} alt={s.title} className="w-full h-full object-cover" loading="lazy" />
                  ) : (
                    <div className={`w-full h-full bg-${color}-500/10 flex items-center justify-center`}>
                      <Icon className={`w-8 h-8 text-${color}-400/30`} />
                    </div>
                  )}
                  <Badge className={`absolute top-0.5 right-0.5 text-[6px] px-0.5 py-0 leading-tight ${
                    s.status === 'completed' ? 'bg-green-500' : s.status === 'cancelled' ? 'bg-red-500' : `bg-${color}-500`
                  }`}>{s.status === 'completed' ? 'DONE' : s.status}</Badge>
                </div>
                <CardContent className="p-1">
                  <h3 className="font-semibold text-[8px] sm:text-[9px] truncate">{s.title}</h3>
                  <div className="flex justify-between mt-0.5 text-[7px] sm:text-[8px]">
                    <span className="text-gray-400">{s.genre_name}</span>
                    <span className={`text-${color}-400`}>{s.quality_score > 0 ? `${s.quality_score}/100` : `${s.num_episodes}ep`}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Default Film View
  return (
    <div className="pt-16 pb-20 px-2 sm:px-3 max-w-7xl mx-auto" data-testid="my-films-page">
      <div className="flex items-center justify-between mb-4 sticky top-16 z-10 bg-[#0F0F10]/95 backdrop-blur-sm py-2 -mx-2 sm:-mx-3 px-2 sm:px-3" data-testid="my-films-sticky-header-main">
        <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl">{t('my_films')}</h1>
        <Button size="sm" onClick={() => navigate('/create-film')} className="bg-yellow-500 text-black h-8 px-2 sm:px-3 text-xs sm:text-sm"><Plus className="w-3 h-3 mr-1" /> Crea</Button>
      </div>
      {films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-6 text-center"><Film className="w-10 h-10 mx-auto mb-3 text-gray-600" /><h3 className="text-base mb-2">Nessun film ancora</h3><Button onClick={() => navigate('/create-film')} className="bg-yellow-500 text-black text-sm">Crea il tuo primo Film</Button></Card>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-1 sm:gap-1.5">
          {films.map(film => (
            <Card key={film.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden hover:border-white/15 transition-colors">
              <div className="aspect-[2/3] relative cursor-pointer" onClick={() => navigate(`/films/${film.id}`)}>
                <img src={posterSrc(film.poster_url)} alt={film.title} className="w-full h-full object-cover" loading="lazy" />
                <Badge className={`absolute top-0.5 right-0.5 text-[6px] px-0.5 py-0 leading-tight ${film.status === 'in_theaters' ? 'bg-green-500' : 'bg-orange-500'}`}>{film.status === 'in_theaters' ? 'LIVE' : film.status}</Badge>
                {(film.virtual_likes > 0) && (
                  <div className="absolute top-0.5 left-0.5 bg-black/70 rounded px-0.5 py-0.5 flex items-center gap-0.5">
                    <Heart className="w-1.5 h-1.5 text-pink-400 fill-pink-400" />
                    <span className="text-[6px] text-pink-300">{film.virtual_likes}</span>
                  </div>
                )}
              </div>
              <CardContent className="p-1">
                <h3 className="font-semibold text-[8px] sm:text-[9px] truncate">{film.title}</h3>
                <div className="flex justify-between mt-0.5 text-[7px] sm:text-[8px]">
                  <span className="text-gray-400">{(film.likes_count || 0) + (film.virtual_likes || 0)} lk</span>
                  <span className="text-green-400">${((film.total_revenue||0)/1000).toFixed(0)}K</span>
                </div>
                <div className="flex gap-0.5 mt-0.5">
                  {film.status === 'in_theaters' && (
                    <Button variant="outline" size="sm" className="flex-1 h-5 sm:h-6 text-[7px] sm:text-[8px] border-yellow-500/30 text-yellow-400 px-1 py-0" onClick={() => setShowAdDialog(film)}>
                      Ads
                    </Button>
                  )}
                  <Button 
                    variant="outline" size="sm" 
                    className="h-5 sm:h-6 text-[7px] sm:text-[8px] border-cyan-500/30 text-cyan-400 px-1 py-0"
                    onClick={(e) => { e.stopPropagation(); regeneratePoster(film.id, e); }}
                    disabled={regenLoading === film.id}
                    data-testid={`regen-poster-${film.id}`}
                  >
                    {regenLoading === film.id ? <Loader2 className="w-2.5 h-2.5 animate-spin" /> : <Wand2 className="w-2.5 h-2.5" />}
                  </Button>
                  {film.status === 'in_theaters' && (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="outline" size="sm" className="h-5 sm:h-6 text-[7px] sm:text-[8px] border-orange-500/30 text-orange-400 px-1 py-0"><Trash2 className="w-2.5 h-2.5" /></Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent className="bg-[#1A1A1A] border-white/10 max-w-[90vw] sm:max-w-md">
                        <AlertDialogHeader><AlertDialogTitle className="text-base">Ritirare?</AlertDialogTitle></AlertDialogHeader>
                        <AlertDialogFooter><AlertDialogCancel className="h-8 text-sm">No</AlertDialogCancel><AlertDialogAction onClick={() => withdrawFilm(film.id)} className="bg-orange-500 h-8 text-sm">Si</AlertDialogAction></AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <Dialog open={!!showAdDialog} onOpenChange={() => { setShowAdDialog(null); setSelectedPlatforms([]); }}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-[95vw] sm:max-w-lg">
          <DialogHeader><DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><Sparkles className="w-4 h-4 text-yellow-500" /> Pubblicizza "{showAdDialog?.title}"</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">{adPlatforms.map(p => (
              <Card key={p.id} className={`cursor-pointer border-2 ${selectedPlatforms.includes(p.id) ? 'border-yellow-500 bg-yellow-500/10' : 'border-white/10'}`} onClick={() => setSelectedPlatforms(prev => prev.includes(p.id) ? prev.filter(x => x !== p.id) : [...prev, p.id])}>
                <CardContent className="p-2"><span className="font-semibold text-xs">{p.name}</span><p className="text-[10px] text-gray-400">${p.cost_per_day.toLocaleString()}/day • +{((p.reach_multiplier-1)*100).toFixed(0)}%</p></CardContent>
              </Card>
            ))}</div>
            <div><Label className="text-xs">Durata: {adDays} giorni</Label><Slider value={[adDays]} onValueChange={([v]) => setAdDays(v)} min={1} max={30} className="mt-1" /></div>
            <div className="p-2 bg-black/30 rounded flex justify-between items-center"><span className="text-xs text-gray-400">Totale:</span><span className="text-lg font-bold text-yellow-500">${calculateAdCost().toLocaleString()}</span></div>
            <Button onClick={() => launchAdCampaign(showAdDialog?.id)} disabled={adLoading || selectedPlatforms.length === 0 || calculateAdCost() > (user?.funds||0)} className="w-full bg-yellow-500 text-black h-9">{adLoading ? '...' : 'Lancia'}</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Film Detail

export default MyFilms;
