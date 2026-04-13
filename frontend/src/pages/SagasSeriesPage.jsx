// CineWorld Studio's - SagasSeriesPage
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

const SagasSeriesPage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const [searchParams] = useSearchParams();
  const typeParam = searchParams.get('type');
  const [activeTab, setActiveTab] = useState(typeParam === 'tv_series' ? 'series' : typeParam === 'anime' ? 'anime' : 'sagas');
  const [myFilms, setMyFilms] = useState([]);
  const [mySagas, setMySagas] = useState([]);
  const [mySeries, setMySeries] = useState([]);
  const [canCreateSequel, setCanCreateSequel] = useState(null);
  const [canCreateSeries, setCanCreateSeries] = useState(null);
  const [canCreateAnime, setCanCreateAnime] = useState(null);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [showCreateSeriesDialog, setShowCreateSeriesDialog] = useState(false);
  const [seriesType, setSeriesType] = useState('tv_series');
  const [creating, setCreating] = useState(false);
  const [posterLoading, setPosterLoading] = useState(null);
  const [newSeries, setNewSeries] = useState({ title: '', genre: 'drama', episodes_count: 10, episode_length: 45, synopsis: '' });

  const labels = {
    sagas: language === 'it' ? 'Saghe & Sequel' : 'Sagas & Sequels',
    series: language === 'it' ? 'Serie TV' : 'TV Series',
    anime: language === 'it' ? 'Anime' : 'Anime',
    create_sequel: language === 'it' ? 'Crea Sequel' : 'Create Sequel',
    create_series: language === 'it' ? 'Crea Serie TV' : 'Create TV Series',
    create_anime: language === 'it' ? 'Crea Anime' : 'Create Anime',
    required_level: language === 'it' ? 'Livello richiesto' : 'Required level',
    required_fame: language === 'it' ? 'Fama richiesta' : 'Required fame',
    no_films: language === 'it' ? 'Non hai film idonei per creare sequel' : 'No eligible films for sequel',
    select_film: language === 'it' ? 'Seleziona un film per creare un sequel' : 'Select a film to create a sequel',
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [filmsRes, seriesRes, sequelCheck, tvCheck, animeCheck] = await Promise.all([
        api.get('/films/my'),
        api.get('/series/my').catch(() => ({ data: { series: [] } })),
        api.get('/saga/can-create').catch(() => ({ data: { can_create: false } })),
        api.get('/series/can-create?series_type=tv_series').catch(() => ({ data: { can_create: false } })),
        api.get('/series/can-create?series_type=anime').catch(() => ({ data: { can_create: false } })),
      ]);
      setMyFilms(filmsRes.data || []);
      setMySeries(seriesRes.data?.series || []);
      setCanCreateSequel(sequelCheck.data);
      setCanCreateSeries(tvCheck.data);
      setCanCreateAnime(animeCheck.data);
      
      // Group films into sagas
      const sagas = {};
      (filmsRes.data || []).forEach(film => {
        if (film.saga_id) {
          if (!sagas[film.saga_id]) sagas[film.saga_id] = [];
          sagas[film.saga_id].push(film);
        }
      });
      setMySagas(Object.values(sagas));
    } catch (e) {
      console.error(e);
    }
  };

  const createSequel = async (filmId) => {
    setCreating(true);
    try {
      const res = await api.post(`/films/${filmId}/create-sequel`);
      toast.success(res.data.message || 'Sequel creato!');
      loadData();
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore creazione sequel');
    } finally {
      setCreating(false);
    }
  };

  const createSeries = async () => {
    if (!newSeries.title.trim()) { toast.error('Inserisci un titolo'); return; }
    setCreating(true);
    try {
      const res = await api.post('/series/create', { ...newSeries, series_type: seriesType });
      toast.success(`${seriesType === 'anime' ? 'Anime' : 'Serie TV'} creata! +200 XP`);
      setShowCreateSeriesDialog(false);
      setNewSeries({ title: '', genre: 'drama', episodes_count: 10, episode_length: 45, synopsis: '' });
      loadData();
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore creazione');
    } finally {
      setCreating(false);
    }
  };

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const posterSrc = (url) => {
    if (!url) return null;
    if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
    return url;
  };

  const regeneratePoster = async (seriesId, isAnime) => {
    setPosterLoading(seriesId);
    try {
      const endpoint = isAnime ? `/anime/${seriesId}/generate-poster` : `/series/${seriesId}/generate-poster`;
      const res = await api.post(endpoint, {}, { timeout: 120000 });
      if (res.data.poster_url) {
        setMySeries(prev => prev.map(s => s.id === seriesId ? { ...s, poster_url: res.data.poster_url } : s));
        toast.success(res.data.message || 'Locandina generata!');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore generazione locandina');
    } finally {
      setPosterLoading(null);
    }
  };

  const genres = ['action', 'comedy', 'drama', 'horror', 'sci-fi', 'romance', 'thriller', 'fantasy', 'animation'];

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="sagas-series-page">
      <div className="text-center mb-6">
        <BookOpen className="w-12 h-12 text-purple-500 mx-auto mb-2" />
        <h1 className="font-['Bebas_Neue'] text-3xl">{language === 'it' ? 'Saghe e Serie' : 'Sagas & Series'}</h1>
        <p className="text-gray-400 text-sm">{language === 'it' ? 'Espandi il tuo universo cinematografico' : 'Expand your cinematic universe'}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 justify-center flex-wrap">
        <Button variant={activeTab === 'sagas' ? 'default' : 'outline'} onClick={() => setActiveTab('sagas')} className={activeTab === 'sagas' ? 'bg-purple-500' : ''}>
          <Film className="w-4 h-4 mr-2" />{labels.sagas}
        </Button>
        <Button variant={activeTab === 'series' ? 'default' : 'outline'} onClick={() => setActiveTab('series')} className={activeTab === 'series' ? 'bg-blue-500' : ''}>
          <Clapperboard className="w-4 h-4 mr-2" />{labels.series}
        </Button>
        <Button variant={activeTab === 'anime' ? 'default' : 'outline'} onClick={() => setActiveTab('anime')} className={activeTab === 'anime' ? 'bg-pink-500' : ''}>
          <Star className="w-4 h-4 mr-2" />{labels.anime}
        </Button>
      </div>

      {/* Sagas Tab */}
      {activeTab === 'sagas' && (
        <div className="space-y-4">
          {/* Requirements Card */}
          <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30">
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="font-['Bebas_Neue'] text-lg text-purple-400">{labels.create_sequel}</h3>
                  <p className="text-xs text-gray-400">
                    {canCreateSequel?.can_create 
                      ? `${language === 'it' ? 'Puoi creare sequel!' : 'You can create sequels!'}`
                      : `${labels.required_level}: ${canCreateSequel?.required_level || 15} (${language === 'it' ? 'sei' : "you're"} ${canCreateSequel?.current_level || 1}) • ${labels.required_fame}: ${canCreateSequel?.required_fame || 100} (${language === 'it' ? 'hai' : "you have"} ${canCreateSequel?.current_fame || 50})`}
                  </p>
                </div>
                {canCreateSequel?.can_create && (
                  <Badge className="bg-green-500/20 text-green-400">{language === 'it' ? 'Sbloccato!' : 'Unlocked!'}</Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Eligible Films for Sequel */}
          {canCreateSequel?.can_create && (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg">{labels.select_film}</CardTitle>
              </CardHeader>
              <CardContent>
                {myFilms.filter(f => f.status !== 'in_production' && !f.is_sequel).length === 0 ? (
                  <p className="text-gray-400 text-center py-4">{labels.no_films}</p>
                ) : (
                  <ScrollArea className="h-[300px]">
                    <div className="grid sm:grid-cols-2 gap-3">
                      {myFilms.filter(f => f.status !== 'in_production' && !f.is_sequel).map(film => (
                        <Card key={film.id} className="bg-white/5 border-white/10">
                          <CardContent className="p-3">
                            <div className="flex items-center gap-3">
                              {film.poster_url && !film.poster_url.startsWith('data:') ? (
                                <img src={film.poster_url} alt="" className="w-12 h-16 object-cover rounded" />
                              ) : (
                                <div className="w-12 h-16 bg-white/10 rounded flex items-center justify-center"><Film className="w-6 h-6 text-gray-500" /></div>
                              )}
                              <div className="flex-1 min-w-0">
                                <p className="font-semibold truncate">{film.title}</p>
                                <p className="text-xs text-gray-400">{film.genre} • {film.sequel_count || 0} sequel</p>
                              </div>
                              <Button size="sm" onClick={() => createSequel(film.id)} disabled={creating || (film.sequel_count || 0) >= 5} className="bg-purple-500 hover:bg-purple-400">
                                <Plus className="w-4 h-4" />
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          )}

          {/* Existing Sagas */}
          {mySagas.length > 0 && (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Le Tue Saghe' : 'Your Sagas'}</CardTitle>
              </CardHeader>
              <CardContent>
                {mySagas.map((saga, i) => (
                  <div key={i} className="p-3 bg-white/5 rounded mb-2">
                    <p className="font-semibold mb-2">{saga[0]?.saga_name || `Saga ${i+1}`}</p>
                    <div className="flex gap-2 overflow-x-auto pb-2">
                      {saga.map((film, j) => (
                        <div key={film.id} className="flex-shrink-0 w-20 text-center">
                          <div className="w-20 h-28 bg-white/10 rounded mb-1 flex items-center justify-center text-xs">#{j+1}</div>
                          <p className="text-xs truncate">{film.title}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Series Tab */}
      {activeTab === 'series' && (
        <div className="space-y-4">
          <Card className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/30">
            <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="font-['Bebas_Neue'] text-lg text-blue-400">{labels.create_series}</h3>
                <p className="text-xs text-gray-400">
                  {canCreateSeries?.can_create 
                    ? `${language === 'it' ? 'Puoi creare serie TV!' : 'You can create TV series!'}`
                    : `${labels.required_level}: ${canCreateSeries?.required_level || 20} • ${labels.required_fame}: ${canCreateSeries?.required_fame || 200}`}
                </p>
              </div>
              <Button onClick={() => { setSeriesType('tv_series'); setShowCreateSeriesDialog(true); }} disabled={!canCreateSeries?.can_create} className="bg-blue-500 hover:bg-blue-400">
                <Plus className="w-4 h-4 mr-2" />{labels.create_series}
              </Button>
            </CardContent>
          </Card>

          {/* My Series */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Le Tue Serie TV' : 'Your TV Series'}</CardTitle>
            </CardHeader>
            <CardContent>
              {mySeries.filter(s => (s.series_type || s.type) === 'tv_series').length === 0 ? (
                <p className="text-gray-400 text-center py-8">{language === 'it' ? 'Non hai ancora serie TV' : 'No TV series yet'}</p>
              ) : (
                <div className="grid sm:grid-cols-2 gap-3">
                  {mySeries.filter(s => (s.series_type || s.type) === 'tv_series').map(series => (
                    <Card key={series.id} className="bg-white/5 border-white/10">
                      <CardContent className="p-3">
                        <div className="flex items-start gap-3">
                          {posterSrc(series.poster_url) ? (
                            <img src={posterSrc(series.poster_url)} alt={series.title} className="w-16 h-24 object-cover rounded flex-shrink-0" />
                          ) : (
                            <div className="w-16 h-24 bg-white/10 rounded flex items-center justify-center flex-shrink-0"><Clapperboard className="w-6 h-6 text-gray-500" /></div>
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold truncate">{series.title}</p>
                            <p className="text-xs text-gray-400">{series.episodes_count} episodi &bull; {series.genre}</p>
                            <Badge className={series.status === 'in_production' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'} variant="outline">
                              {series.status === 'in_production' ? 'In Produzione' : series.status}
                            </Badge>
                            <Button
                              size="sm"
                              variant="ghost"
                              disabled={posterLoading === series.id}
                              onClick={(e) => { e.stopPropagation(); regeneratePoster(series.id, false); }}
                              className="mt-1 h-7 text-[10px] text-blue-400 hover:text-blue-300 px-2"
                              data-testid={`regen-poster-series-${series.id}`}
                            >
                              {posterLoading === series.id ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <RefreshCw className="w-3 h-3 mr-1" />}
                              {posterLoading === series.id ? 'Generazione...' : (series.poster_url ? 'Rigenera Locandina' : 'Crea Locandina')}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Anime Tab */}
      {activeTab === 'anime' && (
        <div className="space-y-4">
          <Card className="bg-gradient-to-r from-pink-500/10 to-purple-500/10 border-pink-500/30">
            <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="font-['Bebas_Neue'] text-lg text-pink-400">{labels.create_anime}</h3>
                <p className="text-xs text-gray-400">
                  {canCreateAnime?.can_create 
                    ? `${language === 'it' ? 'Puoi creare anime!' : 'You can create anime!'}`
                    : `${labels.required_level}: ${canCreateAnime?.required_level || 25} • ${labels.required_fame}: ${canCreateAnime?.required_fame || 300}`}
                </p>
              </div>
              <Button onClick={() => { setSeriesType('anime'); setShowCreateSeriesDialog(true); }} disabled={!canCreateAnime?.can_create} className="bg-pink-500 hover:bg-pink-400">
                <Plus className="w-4 h-4 mr-2" />{labels.create_anime}
              </Button>
            </CardContent>
          </Card>

          {/* My Anime */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'I Tuoi Anime' : 'Your Anime'}</CardTitle>
            </CardHeader>
            <CardContent>
              {mySeries.filter(s => (s.series_type || s.type) === 'anime').length === 0 ? (
                <p className="text-gray-400 text-center py-8">{language === 'it' ? 'Non hai ancora anime' : 'No anime yet'}</p>
              ) : (
                <div className="grid sm:grid-cols-2 gap-3">
                  {mySeries.filter(s => (s.series_type || s.type) === 'anime').map(series => (
                    <Card key={series.id} className="bg-white/5 border-white/10">
                      <CardContent className="p-3">
                        <div className="flex items-start gap-3">
                          {posterSrc(series.poster_url) ? (
                            <img src={posterSrc(series.poster_url)} alt={series.title} className="w-16 h-24 object-cover rounded flex-shrink-0" />
                          ) : (
                            <div className="w-16 h-24 bg-white/10 rounded flex items-center justify-center flex-shrink-0"><Star className="w-6 h-6 text-gray-500" /></div>
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold truncate">{series.title}</p>
                            <p className="text-xs text-gray-400">{series.episodes_count} episodi &bull; {series.genre}</p>
                            <Badge className={series.status === 'in_production' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'} variant="outline">
                              {series.status === 'in_production' ? 'In Produzione' : series.status}
                            </Badge>
                            <Button
                              size="sm"
                              variant="ghost"
                              disabled={posterLoading === series.id}
                              onClick={(e) => { e.stopPropagation(); regeneratePoster(series.id, true); }}
                              className="mt-1 h-7 text-[10px] text-pink-400 hover:text-pink-300 px-2"
                              data-testid={`regen-poster-anime-${series.id}`}
                            >
                              {posterLoading === series.id ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <RefreshCw className="w-3 h-3 mr-1" />}
                              {posterLoading === series.id ? 'Generazione...' : (series.poster_url ? 'Rigenera Locandina' : 'Crea Locandina')}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Series/Anime Dialog */}
      <Dialog open={showCreateSeriesDialog} onOpenChange={setShowCreateSeriesDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              {seriesType === 'anime' ? <Star className="w-5 h-5 text-pink-400" /> : <Clapperboard className="w-5 h-5 text-blue-400" />}
              {seriesType === 'anime' ? labels.create_anime : labels.create_series}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs">{language === 'it' ? 'Titolo' : 'Title'}</Label>
              <Input value={newSeries.title} onChange={e => setNewSeries({...newSeries, title: e.target.value})} placeholder={seriesType === 'anime' ? 'Il mio anime...' : 'La mia serie...'} className="bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Genere' : 'Genre'}</Label>
              <select value={newSeries.genre} onChange={e => setNewSeries({...newSeries, genre: e.target.value})} className="w-full h-9 rounded bg-black/20 border border-white/10 text-sm px-2">
                {genres.map(g => <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs">{language === 'it' ? 'Episodi' : 'Episodes'}</Label>
                <Input type="number" value={newSeries.episodes_count} onChange={e => setNewSeries({...newSeries, episodes_count: parseInt(e.target.value) || 10})} min={1} max={100} className="bg-black/20 border-white/10" />
              </div>
              <div>
                <Label className="text-xs">{language === 'it' ? 'Durata (min)' : 'Length (min)'}</Label>
                <Input type="number" value={newSeries.episode_length} onChange={e => setNewSeries({...newSeries, episode_length: parseInt(e.target.value) || 45})} min={10} max={120} className="bg-black/20 border-white/10" />
              </div>
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Sinossi' : 'Synopsis'}</Label>
              <Textarea value={newSeries.synopsis} onChange={e => setNewSeries({...newSeries, synopsis: e.target.value})} placeholder={language === 'it' ? 'La trama della serie...' : 'Series plot...'} className="bg-black/20 border-white/10 h-20" />
            </div>
            <Card className="bg-white/5 border-white/10">
              <CardContent className="p-3">
                <div className="flex justify-between items-center">
                  <span>{language === 'it' ? 'Budget totale' : 'Total budget'}</span>
                  <span className="text-yellow-400 font-bold">${((seriesType === 'anime' ? 30000 : 50000) * newSeries.episodes_count).toLocaleString()}</span>
                </div>
              </CardContent>
            </Card>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateSeriesDialog(false)}>{language === 'it' ? 'Annulla' : 'Cancel'}</Button>
            <Button onClick={createSeries} disabled={creating || !newSeries.title} className={seriesType === 'anime' ? 'bg-pink-500' : 'bg-blue-500'}>
              {creating ? '...' : language === 'it' ? 'Crea' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Leaderboard Page

export default SagasSeriesPage;
