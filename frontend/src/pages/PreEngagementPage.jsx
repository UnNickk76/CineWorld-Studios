// CineWorld Studio's - PreEngagementPage
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
import { SKILL_TRANSLATIONS, GENRES_LIST } from '../constants';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const PreEngagementPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('my-prefilms');
  const [preFilms, setPreFilms] = useState([]);
  const [expiredIdeas, setExpiredIdeas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEngageModal, setShowEngageModal] = useState(false);
  const [selectedPreFilm, setSelectedPreFilm] = useState(null);
  const [castType, setCastType] = useState('screenwriter');
  const [availableCast, setAvailableCast] = useState([]);
  const [loadingCast, setLoadingCast] = useState(false);
  const [negotiation, setNegotiation] = useState(null);
  
  // Create pre-film form
  const [newPreFilm, setNewPreFilm] = useState({ title: '', subtitle: '', genre: '', screenplay_draft: '', is_sequel: false, sequel_parent_id: null });
  const [myFilmsForPreSequel, setMyFilmsForPreSequel] = useState([]);

  useEffect(() => {
    loadData();
    // Load films for sequel selection
    api.get('/films/my/for-sequel').then(r=>setMyFilmsForPreSequel(r.data.films || [])).catch(()=>{});
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [preFilmsRes, expiredRes] = await Promise.all([
        api.get('/pre-films'),
        api.get('/pre-films/public/expired')
      ]);
      setPreFilms(preFilmsRes.data.pre_films || []);
      setExpiredIdeas(expiredRes.data.expired_ideas || []);
      
      // Check for rescissions on each pre-film
      for (const pf of preFilmsRes.data.pre_films || []) {
        if (pf.status === 'active' && !pf.is_expired) {
          try {
            const rescRes = await api.get(`/pre-films/${pf.id}/check-rescissions`);
            if (rescRes.data.rescissions?.length > 0) {
              for (const resc of rescRes.data.rescissions) {
                // Process rescission and notify user
                const processRes = await api.post(`/pre-films/${pf.id}/process-rescission?cast_type=${resc.cast_type}&cast_id=${resc.cast_id}`);
                toast.warning(`${resc.cast_name} ha rescisso il contratto per "${pf.title}". Anticipo rimborsato: $${resc.advance_to_refund.toLocaleString()}`);
              }
              // Reload data after rescissions
              const updatedRes = await api.get('/pre-films');
              setPreFilms(updatedRes.data.pre_films || []);
            }
          } catch (e) {
            // Silently fail rescission checks
          }
        }
      }
    } catch (e) {
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const createPreFilm = async () => {
    if (!newPreFilm.title || !newPreFilm.genre || !newPreFilm.screenplay_draft) {
      toast.error(language === 'it' ? 'Compila tutti i campi' : 'Fill all fields');
      return;
    }
    // Sequel validation
    if (newPreFilm.is_sequel && !newPreFilm.subtitle) {
      toast.error(language === 'it' ? 'Sottotitolo obbligatorio per i sequel' : 'Subtitle required for sequels');
      return;
    }
    if (newPreFilm.is_sequel && !newPreFilm.sequel_parent_id) {
      toast.error(language === 'it' ? 'Seleziona il film originale' : 'Select original film');
      return;
    }
    try {
      const res = await api.post('/pre-films', newPreFilm);
      if (res.data.success) {
        toast.success(res.data.message);
        setShowCreateModal(false);
        setNewPreFilm({ title: '', subtitle: '', genre: '', screenplay_draft: '', is_sequel: false, sequel_parent_id: null });
        loadData();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const loadAvailableCast = async (type) => {
    setLoadingCast(true);
    setCastType(type);
    try {
      const typeMap = { screenwriter: 'screenwriters', director: 'directors', composer: 'composers', actor: 'actors' };
      const res = await api.get(`/cast/available?type=${typeMap[type]}`);
      setAvailableCast(res.data.cast || []);
    } catch (e) {
      toast.error('Errore nel caricamento cast');
    } finally {
      setLoadingCast(false);
    }
  };

  const openEngageModal = (preFilm, type) => {
    setSelectedPreFilm(preFilm);
    setCastType(type);
    setNegotiation(null);
    loadAvailableCast(type);
    setShowEngageModal(true);
  };

  const engageCast = async (castMember, offeredFee) => {
    try {
      const res = await api.post(`/pre-films/${selectedPreFilm.id}/engage`, {
        pre_film_id: selectedPreFilm.id,
        cast_type: castType,
        cast_id: castMember.id,
        offered_fee: offeredFee
      });
      
      if (res.data.accepted) {
        toast.success(res.data.message);
        setShowEngageModal(false);
        loadData();
      } else {
        // Show negotiation options
        setNegotiation({
          ...res.data,
          cast_member: castMember,
          offered_fee: offeredFee
        });
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const renegotiate = async (newOffer) => {
    try {
      const res = await api.post(`/negotiations/${negotiation.negotiation_id}/renegotiate`, {
        pre_film_id: selectedPreFilm.id,
        cast_type: castType,
        cast_id: negotiation.cast_member.id,
        new_offer: newOffer,
        negotiation_id: negotiation.negotiation_id
      });
      
      if (res.data.accepted) {
        toast.success(res.data.message);
        setShowEngageModal(false);
        setNegotiation(null);
        loadData();
      } else if (res.data.final_rejection) {
        toast.error(res.data.message);
        setNegotiation(null);
      } else {
        setNegotiation(prev => ({
          ...prev,
          requested_fee: res.data.requested_fee,
          rejection_count: res.data.rejection_count
        }));
        toast.warning(res.data.message);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const releaseCast = async (preFilmId, type, castId, castName) => {
    if (!confirm(language === 'it' 
      ? `Sei sicuro di voler congedare ${castName}? Perderai l'anticipo e potresti dover pagare una penale.`
      : `Are you sure you want to dismiss ${castName}? You'll lose the advance and may have to pay a penalty.`
    )) return;
    
    try {
      const res = await api.post(`/pre-films/${preFilmId}/release`, {
        pre_film_id: preFilmId,
        cast_type: type,
        cast_id: castId
      });
      
      if (res.data.success) {
        toast.success(`${castName} ${language === 'it' ? 'congedato' : 'dismissed'}. ${language === 'it' ? 'Penale' : 'Penalty'}: ${res.data.penalty_percent.toFixed(0)}% ($${res.data.total_cost.toLocaleString()})`);
        loadData();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const convertToFilm = async (preFilmId) => {
    try {
      const res = await api.post(`/pre-films/${preFilmId}/convert`);
      if (res.data.success) {
        toast.success(res.data.message);
        navigate('/create', { state: { draftId: res.data.draft_id, fromPreFilm: true } });
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const getCastTypeLabel = (type) => {
    const labels = {
      screenwriter: language === 'it' ? 'Sceneggiatori' : 'Screenwriters',
      director: language === 'it' ? 'Registi' : 'Directors',
      composer: language === 'it' ? 'Musicisti' : 'Composers',
      actor: language === 'it' ? 'Attori' : 'Actors'
    };
    return labels[type] || type;
  };

  if (loading) return <LoadingSpinner />;


  return (
    <div className="pt-20 pb-24 px-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-['Bebas_Neue'] text-3xl">{language === 'it' ? 'Pre-Ingaggio Cast' : 'Pre-Engagement'}</h1>
          <p className="text-sm text-gray-400">{language === 'it' ? 'Ingaggia il cast prima di creare il film' : 'Engage cast before creating your film'}</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="bg-orange-500 hover:bg-orange-600">
          <Plus className="w-4 h-4 mr-2" /> {language === 'it' ? 'Nuovo Pre-Film' : 'New Pre-Film'}
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="bg-black/20">
          <TabsTrigger value="my-prefilms">{language === 'it' ? 'I Miei Pre-Film' : 'My Pre-Films'} ({preFilms.length})</TabsTrigger>
          <TabsTrigger value="public-ideas">{language === 'it' ? 'Idee Pubbliche' : 'Public Ideas'} ({expiredIdeas.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="my-prefilms" className="mt-4">
          {preFilms.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-8 text-center">
                <Users className="w-12 h-12 mx-auto text-gray-500 mb-4" />
                <h3 className="text-lg font-bold mb-2">{language === 'it' ? 'Nessun Pre-Film' : 'No Pre-Films'}</h3>
                <p className="text-sm text-gray-400 mb-4">{language === 'it' ? 'Crea un pre-film per iniziare ad ingaggiare il cast in anticipo' : 'Create a pre-film to start engaging cast in advance'}</p>
                <Button onClick={() => setShowCreateModal(true)} className="bg-orange-500">
                  <Plus className="w-4 h-4 mr-2" /> {language === 'it' ? 'Crea Pre-Film' : 'Create Pre-Film'}
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {preFilms.map(pf => (
                <Card key={pf.id} className={`bg-[#1A1A1A] border-white/10 ${pf.is_expired ? 'opacity-60' : ''}`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-['Bebas_Neue'] text-xl">{pf.title}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge className="bg-purple-500/20 text-purple-400">{GENRES_LIST.find(g => g.id === pf.genre)?.[language === 'it' ? 'nameIt' : 'name'] || pf.genre}</Badge>
                          {pf.is_expired ? (
                            <Badge className="bg-red-500/20 text-red-400">{language === 'it' ? 'Scaduto' : 'Expired'}</Badge>
                          ) : (
                            <Badge className="bg-green-500/20 text-green-400">{pf.days_remaining} {language === 'it' ? 'giorni rimasti' : 'days left'}</Badge>
                          )}
                        </div>
                      </div>
                      {!pf.is_expired && (
                        <Button onClick={() => convertToFilm(pf.id)} className="bg-yellow-500 text-black hover:bg-yellow-400">
                          <Clapperboard className="w-4 h-4 mr-2" /> {language === 'it' ? 'Crea Film' : 'Create Film'}
                        </Button>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-400 mb-4 italic">"{pf.screenplay_draft}"</p>
                    
                    {/* Pre-engaged cast */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                      {['screenwriter', 'director', 'composer'].map(type => {
                        const engaged = pf.pre_engaged_cast?.[type];
                        return (
                          <div key={type} className="bg-black/30 rounded-lg p-3">
                            <p className="text-[10px] text-gray-500 uppercase mb-2">{getCastTypeLabel(type)}</p>
                            {engaged ? (
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-sm font-semibold">{engaged.name || 'Loading...'}</p>
                                  <p className="text-[10px] text-green-400">${engaged.offered_fee?.toLocaleString()}</p>
                                </div>
                                {!pf.is_expired && (
                                  <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-red-400 hover:bg-red-500/20"
                                    onClick={() => releaseCast(pf.id, type, engaged.id, engaged.name)}>
                                    <X className="w-3 h-3" />
                                  </Button>
                                )}
                              </div>
                            ) : (
                              <Button size="sm" variant="outline" className="w-full h-8 text-xs" onClick={() => openEngageModal(pf, type)} disabled={pf.is_expired}>
                                <Plus className="w-3 h-3 mr-1" /> {language === 'it' ? 'Ingaggia' : 'Engage'}
                              </Button>
                            )}
                          </div>
                        );
                      })}
                      
                      {/* Actors */}
                      <div className="bg-black/30 rounded-lg p-3">
                        <p className="text-[10px] text-gray-500 uppercase mb-2">{getCastTypeLabel('actor')} ({pf.pre_engaged_cast?.actors?.length || 0})</p>
                        {pf.pre_engaged_cast?.actors?.length > 0 && (
                          <div className="space-y-1 mb-2 max-h-20 overflow-y-auto">
                            {pf.pre_engaged_cast.actors.map(actor => (
                              <div key={actor.id} className="flex items-center justify-between text-xs bg-black/30 rounded px-2 py-1">
                                <span>{actor.name || 'Loading...'}</span>
                                {!pf.is_expired && (
                                  <button className="text-red-400 hover:text-red-300" onClick={() => releaseCast(pf.id, 'actor', actor.id, actor.name)}>
                                    <X className="w-3 h-3" />
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                        <Button size="sm" variant="outline" className="w-full h-8 text-xs" onClick={() => openEngageModal(pf, 'actor')} disabled={pf.is_expired}>
                          <Plus className="w-3 h-3 mr-1" /> {language === 'it' ? 'Aggiungi' : 'Add'}
                        </Button>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{language === 'it' ? 'Anticipi pagati' : 'Advances paid'}: ${pf.total_advance_paid?.toLocaleString() || 0}</span>
                      <span>{language === 'it' ? 'Creato' : 'Created'}: {new Date(pf.created_at).toLocaleDateString()}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="public-ideas" className="mt-4">
          {expiredIdeas.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-8 text-center">
                <Lightbulb className="w-12 h-12 mx-auto text-gray-500 mb-4" />
                <h3 className="text-lg font-bold mb-2">{language === 'it' ? 'Nessuna Idea Pubblica' : 'No Public Ideas'}</h3>
                <p className="text-sm text-gray-400">{language === 'it' ? 'Le idee scadute di altri produttori appariranno qui' : 'Expired ideas from other producers will appear here'}</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {expiredIdeas.map(idea => (
                <Card key={idea.id} className="bg-[#1A1A1A] border-white/10">
                  <CardContent className="p-4">
                    <h3 className="font-['Bebas_Neue'] text-lg">{idea.title}</h3>
                    <Badge className="bg-purple-500/20 text-purple-400 mt-1">{GENRES_LIST.find(g => g.id === idea.genre)?.[language === 'it' ? 'nameIt' : 'name'] || idea.genre}</Badge>
                    <p className="text-sm text-gray-400 mt-2 italic">"{idea.screenplay_draft}"</p>
                    <p className="text-[10px] text-gray-500 mt-3">{language === 'it' ? 'Idea di' : 'Idea by'}: {idea.creator_nickname} ({idea.creator_production_house})</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create Pre-Film Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowCreateModal(false)}>
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }} 
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] rounded-xl p-6 max-w-md w-full border border-white/10 max-h-[80vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <h2 className="font-['Bebas_Neue'] text-2xl mb-4">{language === 'it' ? 'Crea Pre-Film' : 'Create Pre-Film'}</h2>
            
            <div className="space-y-4">
              <div>
                <Label className="text-xs">{language === 'it' ? 'Titolo (provvisorio)' : 'Title (provisional)'}</Label>
                <Input 
                  value={newPreFilm.title} 
                  onChange={e => setNewPreFilm({...newPreFilm, title: e.target.value})}
                  placeholder={language === 'it' ? 'Il titolo del tuo film...' : 'Your film title...'}
                  className="bg-black/30 border-white/10"
                />
              </div>
              
              {/* Subtitle for sequels */}
              <div>
                <Label className="text-xs">{language === 'it' ? 'Sottotitolo' : 'Subtitle'} {newPreFilm.is_sequel && <span className="text-red-400">*</span>}</Label>
                <Input 
                  value={newPreFilm.subtitle} 
                  onChange={e => setNewPreFilm({...newPreFilm, subtitle: e.target.value})}
                  placeholder={language === 'it' ? 'es. "La Vendetta"...' : 'e.g. "The Revenge"...'}
                  className="bg-black/30 border-white/10"
                />
                <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Opzionale. Obbligatorio per i sequel.' : 'Optional. Required for sequels.'}</p>
              </div>
              
              {/* Sequel checkbox */}
              <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <Checkbox 
                    id="prefilm-is-sequel" 
                    checked={newPreFilm.is_sequel}
                    onCheckedChange={(checked) => setNewPreFilm({...newPreFilm, is_sequel: checked, sequel_parent_id: checked ? newPreFilm.sequel_parent_id : null})}
                  />
                  <Label htmlFor="prefilm-is-sequel" className="text-sm cursor-pointer">
                    {language === 'it' ? 'Questo è un sequel' : 'This is a sequel'}
                  </Label>
                </div>
                
                {newPreFilm.is_sequel && (
                  <div className="pl-6 space-y-2">
                    <Label className="text-xs">{language === 'it' ? 'Film originale' : 'Original film'} *</Label>
                    {myFilmsForPreSequel.length > 0 ? (
                      <select 
                        value={newPreFilm.sequel_parent_id || ''} 
                        onChange={e => {
                          const parent = myFilmsForPreSequel.find(f => f.id === e.target.value);
                          setNewPreFilm({...newPreFilm, sequel_parent_id: e.target.value, genre: parent?.genre || newPreFilm.genre});
                        }}
                        className="w-full h-9 rounded-md bg-black/30 border border-white/10 px-3 text-sm"
                      >
                        <option value="">{language === 'it' ? 'Seleziona...' : 'Select...'}</option>
                        {myFilmsForPreSequel.map(f => (
                          <option key={f.id} value={f.id}>{f.full_title} (Q:{f.quality_score})</option>
                        ))}
                      </select>
                    ) : (
                      <p className="text-xs text-gray-400">{language === 'it' ? 'Nessun film disponibile' : 'No films available'}</p>
                    )}
                  </div>
                )}
              </div>
              
              <div>
                <Label className="text-xs">{language === 'it' ? 'Genere' : 'Genre'}</Label>
                <select 
                  value={newPreFilm.genre} 
                  onChange={e => setNewPreFilm({...newPreFilm, genre: e.target.value})}
                  className="w-full h-10 rounded-md bg-black/30 border border-white/10 px-3 text-sm"
                  disabled={newPreFilm.is_sequel && newPreFilm.sequel_parent_id}
                >
                  <option value="">{language === 'it' ? 'Seleziona genere...' : 'Select genre...'}</option>
                  {GENRES_LIST.map(g => (
                    <option key={g.id} value={g.id}>{language === 'it' ? g.nameIt : g.name}</option>
                  ))}
                </select>
                {newPreFilm.is_sequel && newPreFilm.sequel_parent_id && (
                  <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Genere ereditato' : 'Genre inherited'}</p>
                )}
              </div>
              
              <div>
                <Label className="text-xs">{language === 'it' ? 'Bozza Sceneggiatura (20-200 caratteri)' : 'Screenplay Draft (20-200 chars)'}</Label>
                <textarea 
                  value={newPreFilm.screenplay_draft} 
                  onChange={e => setNewPreFilm({...newPreFilm, screenplay_draft: e.target.value.slice(0, 200)})}
                  placeholder={language === 'it' ? 'Una breve descrizione della trama...' : 'A brief plot description...'}
                  className="w-full h-24 rounded-md bg-black/30 border border-white/10 px-3 py-2 text-sm resize-none"
                  maxLength={200}
                />
                <p className="text-[10px] text-gray-500 text-right">{newPreFilm.screenplay_draft.length}/200</p>
              </div>
              
              <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-3">
                <p className="text-xs text-orange-400">
                  {language === 'it' 
                    ? `Hai 20 giorni per completare il film. Se non lo fai, l'idea diventerà pubblica.`
                    : `You have 20 days to complete the film. If you don't, the idea will become public.`}
                </p>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <Button variant="outline" onClick={() => setShowCreateModal(false)} className="flex-1">
                {language === 'it' ? 'Annulla' : 'Cancel'}
              </Button>
              <Button onClick={createPreFilm} className="flex-1 bg-orange-500 hover:bg-orange-600">
                {language === 'it' ? 'Crea' : 'Create'}
              </Button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Engage Cast Modal */}
      {showEngageModal && selectedPreFilm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => { setShowEngageModal(false); setNegotiation(null); }}>
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }} 
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] rounded-xl p-6 max-w-2xl w-full border border-white/10 max-h-[80vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <h2 className="font-['Bebas_Neue'] text-2xl mb-2">
              {language === 'it' ? 'Ingaggia' : 'Engage'} {getCastTypeLabel(castType)}
            </h2>
            <p className="text-sm text-gray-400 mb-4">{language === 'it' ? 'per' : 'for'} "{selectedPreFilm.title}"</p>
            
            {/* Negotiation View */}
            {negotiation && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-4">
                <h3 className="font-bold text-red-400 mb-2">{negotiation.cast_name} {language === 'it' ? 'ha rifiutato!' : 'rejected!'}</h3>
                <p className="text-sm text-gray-300 mb-3">{negotiation.message}</p>
                
                {negotiation.can_renegotiate && (
                  <div className="space-y-3">
                    <p className="text-sm">{language === 'it' ? 'Richiesta' : 'Requested'}: <span className="text-yellow-400 font-bold">${negotiation.requested_fee?.toLocaleString()}</span></p>
                    
                    <div className="flex gap-2">
                      <Input 
                        type="number" 
                        placeholder={language === 'it' ? 'Nuova offerta...' : 'New offer...'}
                        className="bg-black/30 border-white/10"
                        id="renegotiate-offer"
                      />
                      <Button onClick={() => {
                        const input = document.getElementById('renegotiate-offer');
                        const value = parseFloat(input.value);
                        if (value > 0) renegotiate(value);
                      }} className="bg-yellow-500 text-black">
                        {language === 'it' ? 'Offri' : 'Offer'}
                      </Button>
                      <Button variant="outline" onClick={() => {
                        renegotiate(negotiation.requested_fee);
                      }} className="border-green-500 text-green-400">
                        {language === 'it' ? 'Accetta Richiesta' : 'Accept Request'}
                      </Button>
                    </div>
                    
                    <Button variant="ghost" onClick={() => setNegotiation(null)} className="w-full text-gray-400">
                      {language === 'it' ? 'Cerca altro cast' : 'Find other cast'}
                    </Button>
                  </div>
                )}
              </div>
            )}
            
            {/* Cast Tabs */}
            {!negotiation && (
              <>
                <Tabs value={castType} onValueChange={(v) => { setCastType(v); loadAvailableCast(v); }} className="mb-4">
                  <TabsList className="bg-black/20">
                    <TabsTrigger value="screenwriter">{language === 'it' ? 'Sceneggiatori' : 'Screenwriters'}</TabsTrigger>
                    <TabsTrigger value="director">{language === 'it' ? 'Registi' : 'Directors'}</TabsTrigger>
                    <TabsTrigger value="composer">{language === 'it' ? 'Musicisti' : 'Composers'}</TabsTrigger>
                    <TabsTrigger value="actor">{language === 'it' ? 'Attori' : 'Actors'}</TabsTrigger>
                  </TabsList>
                </Tabs>
                
                {loadingCast ? (
                  <div className="flex justify-center py-8">
                    <RefreshCw className="w-6 h-6 animate-spin text-yellow-500" />
                  </div>
                ) : (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {availableCast.map(cast => (
                      <CastEngageRow key={cast.id} cast={cast} onEngage={engageCast} language={language} />
                    ))}
                    {availableCast.length === 0 && (
                      <p className="text-center text-gray-500 py-4">{language === 'it' ? 'Nessun cast disponibile' : 'No cast available'}</p>
                    )}
                  </div>
                )}
              </>
            )}
            
            <Button variant="outline" onClick={() => { setShowEngageModal(false); setNegotiation(null); }} className="w-full mt-4">
              {language === 'it' ? 'Chiudi' : 'Close'}
            </Button>
          </motion.div>
        </div>
      )}
    </div>
  );
};

// Cast Row for Engagement
const CastEngageRow = ({ cast, onEngage, language }) => {
  const [offer, setOffer] = useState(cast.fee || 50000);
  const [showOffer, setShowOffer] = useState(false);
  
  return (
    <div className="bg-black/30 rounded-lg p-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <img 
          src={cast.avatar_url || `https://api.dicebear.com/9.x/personas/svg?seed=${cast.id}`} 
          alt={cast.name} 
          className="w-10 h-10 rounded-full"
        />
        <div>
          <p className="font-semibold">{cast.name}</p>
          <div className="flex items-center gap-2">
            <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">Fame: {cast.fame || 50}</Badge>
            <span className="text-xs text-green-400">${cast.fee?.toLocaleString() || '50,000'}</span>
          </div>
        </div>
      </div>
      
      {showOffer ? (
        <div className="flex items-center gap-2">
          <Input 
            type="number" 
            value={offer} 
            onChange={e => setOffer(parseFloat(e.target.value) || 0)}
            className="w-28 h-8 text-sm bg-black/30"
          />
          <Button size="sm" onClick={() => onEngage(cast, offer)} className="bg-orange-500 hover:bg-orange-600 h-8">
            {language === 'it' ? 'Offri' : 'Offer'}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setShowOffer(false)} className="h-8">
            <X className="w-4 h-4" />
          </Button>
        </div>
      ) : (
        <Button size="sm" onClick={() => setShowOffer(true)} className="bg-orange-500/20 text-orange-400 hover:bg-orange-500/30">
          {language === 'it' ? 'Ingaggia' : 'Engage'}
        </Button>
      )}
    </div>
  );
};

// ==================== END PRE-ENGAGEMENT PAGE ====================

// Film Drafts (Incomplete Films) Board

export default PreEngagementPage;
