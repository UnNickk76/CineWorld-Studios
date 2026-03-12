// CineWorld Studio's - FilmWizard
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
import { Calendar as CalendarComponent } from '../components/ui/calendar';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import {
  Film, Star, Award, TrendingUp, TrendingDown, Clock, Play, Pause, Volume2, Users, Clapperboard,
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

const FilmWizard = () => {
  const { api, user, updateFunds } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();

  const SkillBadge = ({ name, value, change, language: lang = 'it' }) => {
    const getBgColor = () => {
      if (change > 0) return 'bg-green-500/20 border-green-500/30';
      if (change < 0) return 'bg-red-500/20 border-red-500/30';
      return 'bg-white/5 border-white/10';
    };
    const translatedName = SKILL_TRANSLATIONS[name]?.[lang] || SKILL_TRANSLATIONS[name]?.['en'] || name;
    return (
      <div className={`flex items-center justify-between px-1.5 py-0.5 rounded border ${getBgColor()}`}>
        <span className="text-xs truncate mr-1">{translatedName}</span>
        <div className="flex items-center gap-0.5">
          <span className={`font-bold text-xs ${change > 0 ? 'text-green-500' : change < 0 ? 'text-red-500' : ''}`}>{value}</span>
          {change > 0 && <TrendingUp className="w-2.5 h-2.5 text-green-500" />}
          {change < 0 && <TrendingDown className="w-2.5 h-2.5 text-red-500" />}
        </div>
      </div>
    );
  };

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [sponsors, setSponsors] = useState([]);
  const [locations, setLocations] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [screenwriters, setScreenwriters] = useState([]);
  const [directors, setDirectors] = useState([]);
  const [actors, setActors] = useState([]);
  const [composers, setComposers] = useState([]);
  const [genres, setGenres] = useState({});
  const [actorRoles, setActorRoles] = useState([]);
  const [resumedDraftId, setResumedDraftId] = useState(null);
  
  // New states for cast filtering
  const [castCategories, setCastCategories] = useState([]);
  const [availableSkills, setAvailableSkills] = useState({
    screenwriters: [], directors: [], actors: [], composers: []
  });
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSkill, setSelectedSkill] = useState('all');
  const [skillSearchQuery, setSkillSearchQuery] = useState('');
  
  // Rejection system states
  const [refusedIds, setRefusedIds] = useState(new Set());
  const [rejectionModal, setRejectionModal] = useState(null);
  const [renegotiateOffer, setRenegotiateOffer] = useState(0);
  const [renegotiating, setRenegotiating] = useState(false);
  const [checkingOffer, setCheckingOffer] = useState(null);
  
  // Pre-engagement states
  const [preEngagedCast, setPreEngagedCast] = useState(null);
  const [preFilmId, setPreFilmId] = useState(null);
  const [dismissModal, setDismissModal] = useState(null);

  const [filmData, setFilmData] = useState({
    title: '', subtitle: '', genre: 'action', subgenres: [], release_date: new Date().toISOString().split('T')[0],
    weeks_in_theater: 4, sponsor_id: null, equipment_package: 'Standard', locations: [], location_days: {},
    screenwriter_id: '', director_id: '', composer_id: '', actors: [], extras_count: 50, extras_cost: 50000,
    screenplay: '', screenplay_source: 'manual', screenplay_prompt: '', 
    soundtrack_prompt: '', soundtrack_description: '',
    poster_url: '', poster_prompt: '', ad_duration_seconds: 0, ad_revenue: 0,
    is_sequel: false, sequel_parent_id: null
  });
  const [myFilmsForSequel, setMyFilmsForSequel] = useState([]);
  const [releaseDate, setReleaseDate] = useState(new Date());
  const steps = [{num:1,title:'Title'},{num:2,title:'Sponsor'},{num:3,title:'Equipment'},{num:4,title:'Writer'},{num:5,title:'Director'},{num:6,title:'Composer'},{num:7,title:'Cast'},{num:8,title:'Script'},{num:9,title:'Soundtrack'},{num:10,title:'Poster'},{num:11,title:'Ads'},{num:12,title:'Review'}];

  // Function to save draft (pause)
  const saveDraft = async (reason = 'paused') => {
    setSavingDraft(true);
    try {
      const draftData = {
        ...filmData,
        current_step: step,
        paused_reason: reason
      };
      const res = await api.post('/films/drafts', draftData);
      toast.success(language === 'it' ? 'Bozza salvata! Puoi riprendere dalla pagina "Film Incompleti"' : 'Draft saved! You can resume from "Incomplete Films"');
      if (reason === 'paused') {
        navigate('/drafts');
      }
    } catch (e) {
      toast.error(language === 'it' ? 'Errore nel salvataggio della bozza' : 'Error saving draft');
    } finally {
      setSavingDraft(false);
    }
  };
  
  // Load draft from URL params or localStorage
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const draftId = params.get('draft');
    if (draftId) {
      loadDraft(draftId);
    }
  }, []);
  
  const loadDraft = async (draftId) => {
    try {
      const res = await api.get(`/films/drafts/${draftId}`);
      const draft = res.data;
      setFilmData({
        title: draft.title || '',
        genre: draft.genre || 'action',
        subgenres: draft.subgenres || [],
        release_date: draft.release_date || new Date().toISOString().split('T')[0],
        weeks_in_theater: draft.weeks_in_theater || 4,
        sponsor_id: draft.sponsor_id,
        equipment_package: draft.equipment_package || 'Standard',
        locations: draft.locations || [],
        location_days: draft.location_days || {},
        screenwriter_id: draft.screenwriter_id || '',
        director_id: draft.director_id || '',
        composer_id: draft.composer_id || '',
        actors: draft.actors || [],
        extras_count: draft.extras_count || 50,
        extras_cost: draft.extras_cost || 50000,
        screenplay: draft.screenplay || '',
        screenplay_source: draft.screenplay_source || 'manual',
        screenplay_prompt: draft.screenplay_prompt || '',
        soundtrack_prompt: draft.soundtrack_prompt || '',
        soundtrack_description: draft.soundtrack_description || '',
        poster_url: draft.poster_url || '',
        poster_prompt: draft.poster_prompt || '',
        ad_duration_seconds: draft.ad_duration_seconds || 0,
        ad_revenue: draft.ad_revenue || 0
      });
      setStep(draft.current_step || 1);
      setResumedDraftId(draftId);
      
      // Check if this draft comes from a pre-film
      if (draft.from_pre_film && draft.pre_film_id) {
        setPreFilmId(draft.pre_film_id);
        setPreEngagedCast(draft.pre_engaged_cast || null);
        
        // Pre-fill cast IDs from pre-engaged cast
        const preCast = draft.pre_engaged_cast || {};
        if (preCast.screenwriter?.id) {
          setFilmData(prev => ({...prev, screenwriter_id: preCast.screenwriter.id}));
        }
        if (preCast.director?.id) {
          setFilmData(prev => ({...prev, director_id: preCast.director.id}));
        }
        if (preCast.composer?.id) {
          setFilmData(prev => ({...prev, composer_id: preCast.composer.id}));
        }
        if (preCast.actors?.length > 0) {
          setFilmData(prev => ({
            ...prev, 
            actors: preCast.actors.map(a => ({
              id: a.id,
              role: 'Lead',
              fee: a.offered_fee
            }))
          }));
        }
        
        toast.info(language === 'it' 
          ? 'Cast pre-ingaggiato caricato. Puoi mantenerlo o congedarlo (con penale).'
          : 'Pre-engaged cast loaded. You can keep or dismiss them (with penalty).');
      }
      
      toast.success(language === 'it' ? 'Bozza caricata!' : 'Draft loaded!');
    } catch (e) {
      toast.error(language === 'it' ? 'Errore nel caricamento della bozza' : 'Error loading draft');
    }
  };

  // Auto-save every 30 seconds
  const [lastAutoSave, setLastAutoSave] = useState(null);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  
  useEffect(() => {
    if (!autoSaveEnabled || !filmData.title) return;
    
    const autoSaveInterval = setInterval(async () => {
      // Only auto-save if there's meaningful data
      if (filmData.title || filmData.genre !== 'action' || filmData.screenplay || filmData.actors.length > 0) {
        try {
          const draftData = {
            ...filmData,
            current_step: step,
            paused_reason: 'autosave'
          };
          await api.post('/films/drafts', draftData);
          setLastAutoSave(new Date());
          // Silent save - no toast to avoid spam
        } catch (e) {
          // Silent fail for auto-save - no action needed
        }
      }
    }, 30000); // 30 seconds
    
    return () => clearInterval(autoSaveInterval);
  }, [filmData, step, autoSaveEnabled, api]);

  // Save before page unload
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (filmData.title || filmData.screenplay || filmData.actors.length > 0) {
        // Try to save draft synchronously (best effort)
        const draftData = {
          ...filmData,
          current_step: step,
          paused_reason: 'browser_close'
        };
        // Use sendBeacon for reliable save on page close
        const blob = new Blob([JSON.stringify(draftData)], { type: 'application/json' });
        navigator.sendBeacon?.(`${api.defaults.baseURL}/films/drafts`, blob);
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [filmData, step, api]);

  useEffect(() => { 
    api.get('/sponsors').then(r=>setSponsors(r.data)); 
    api.get('/locations').then(r=>setLocations(r.data)); 
    api.get('/equipment').then(r=>setEquipment(r.data));
    api.get('/genres').then(r=>setGenres(r.data));
    api.get('/actor-roles').then(r=>setActorRoles(r.data));
    api.get('/films/my/for-sequel').then(r=>setMyFilmsForSequel(r.data.films || [])).catch(()=>{});
  }, [api]);
  
  const fetchPeople = async (type, category = '', skill = '') => {
    try {
      let url = `/${type}?limit=200`;
      if (category && category !== 'all') url += `&category=${category}`;
      if (skill && skill !== 'all') url += `&skill=${skill}`;
      
      const res = await api.get(url);
      if(type==='screenwriters') {
        setScreenwriters(res.data.screenwriters || []);
        setAvailableSkills(prev => ({...prev, screenwriters: res.data.available_skills || []}));
      }
      else if(type==='directors') {
        setDirectors(res.data.directors || []);
        setAvailableSkills(prev => ({...prev, directors: res.data.available_skills || []}));
      }
      else if(type==='actors') {
        setActors(res.data.actors || []);
        setAvailableSkills(prev => ({...prev, actors: res.data.available_skills || []}));
      }
      else if(type==='composers') {
        setComposers(res.data.composers || []);
        setAvailableSkills(prev => ({...prev, composers: res.data.available_skills || []}));
      }
      if (res.data.categories) setCastCategories(res.data.categories);
    } catch(err) {
      // Retry once after 1 second on failure
      setTimeout(async () => {
        try {
          let url = `/${type}?limit=200`;
          const retryRes = await api.get(url);
          if(type==='actors') setActors(retryRes.data.actors || []);
          else if(type==='screenwriters') setScreenwriters(retryRes.data.screenwriters || []);
          else if(type==='directors') setDirectors(retryRes.data.directors || []);
          else if(type==='composers') setComposers(retryRes.data.composers || []);
          if (retryRes.data.categories) setCastCategories(retryRes.data.categories);
        } catch(e) { /* Silent retry fail */ }
      }, 1000);
    }
  };
  
  useEffect(() => { 
    if(step===4) { fetchPeople('screenwriters', selectedCategory, selectedSkill); }
    if(step===5) { fetchPeople('directors', selectedCategory, selectedSkill); }
    if(step===6) { fetchPeople('composers', selectedCategory, selectedSkill); }
    if(step===7) { fetchPeople('actors', selectedCategory, selectedSkill); }
  }, [step, selectedCategory, selectedSkill]);
  
  // Reset filters when changing steps
  useEffect(() => {
    setSelectedCategory('all');
    setSelectedSkill('all');
    setSkillSearchQuery('');
  }, [step]);

  const generateScreenplay = async () => { 
    setGenerating(true); 
    try { 
      const res = await api.post('/ai/screenplay', { genre: filmData.genre, title: filmData.title, language, tone: 'dramatic', length: 'medium', custom_prompt: filmData.screenplay_prompt }); 
      setFilmData({...filmData, screenplay: res.data.screenplay, screenplay_source: 'ai'}); 
      toast.success(language === 'it' ? 'Sceneggiatura generata!' : 'Screenplay generated!'); 
    } catch(e) { 
      toast.error(language === 'it' ? 'Errore generazione sceneggiatura. Riprova.' : 'Screenplay generation error. Try again.'); 
    } finally { 
      setGenerating(false); 
    }
  };
  const generatePoster = async () => { 
    setGenerating(true); 
    try { 
      const res = await api.post('/ai/poster', { title: filmData.title, genre: filmData.genre, description: filmData.poster_prompt || filmData.title, style: 'cinematic' }); 
      if (res.data.poster_url && res.data.poster_url.startsWith('data:')) {
        setFilmData({...filmData, poster_url: res.data.poster_url}); 
        toast.success(language === 'it' ? 'Locandina AI generata!' : 'AI Poster generated!'); 
      } else {
        toast.error(res.data.error || (language === 'it' ? 'Generazione fallita, riprova' : 'Generation failed, try again'));
      }
    } catch(e) { 
      toast.error(e.response?.data?.error || (language === 'it' ? 'Errore generazione locandina. Riprova.' : 'Poster generation error. Try again.')); 
    } finally { 
      setGenerating(false); 
    }
  };
  const generateSoundtrack = async () => { 
    setGenerating(true); 
    try { 
      const res = await api.post('/ai/soundtrack-description', { title: filmData.title, genre: filmData.genre, mood: 'epic', custom_prompt: filmData.soundtrack_prompt, language }); 
      setFilmData({...filmData, soundtrack_description: res.data.description}); 
      toast.success(language === 'it' ? 'Descrizione colonna sonora generata!' : 'Soundtrack description generated!'); 
    } catch(e) { 
      toast.error(language === 'it' ? 'Errore generazione. Riprova.' : 'Generation error. Try again.'); 
    } finally { 
      setGenerating(false); 
    }
  };
  
  // Load rejections on mount
  useEffect(() => {
    api.get('/cast/rejections').then(r => {
      setRefusedIds(new Set(r.data.refused_ids || []));
    }).catch(() => {});
  }, [api]);
  
  // Function to make an offer to a cast member
  const makeOffer = async (person, personType, onAccept) => {
    // If already refused, don't allow clicking
    if (refusedIds.has(person.id)) {
      return;
    }
    
    setCheckingOffer(person.id);
    
    try {
      const res = await api.post('/cast/offer', {
        person_id: person.id,
        person_type: personType,
        film_genre: filmData.genre
      });
      
      if (res.data.accepted) {
        // Accepted! Proceed with selection
        onAccept();
        toast.success(res.data.message);
      } else {
        // Refused!
        setRefusedIds(prev => new Set([...prev, person.id]));
        setRenegotiateOffer(Math.round(res.data.requested_fee || person.fee * 1.2 || 60000));
        setRejectionModal({
          name: res.data.person_name,
          type: res.data.person_type,
          reason: res.data.reason,
          stars: res.data.stars,
          fame: res.data.fame,
          alreadyRefused: res.data.already_refused,
          negotiation_id: res.data.negotiation_id,
          can_renegotiate: res.data.can_renegotiate,
          requested_fee: res.data.requested_fee,
          person_id: person.id,
          onAccept: onAccept
        });
      }
    } catch (e) {
      toast.error('Errore nella comunicazione');
      // On error, allow selection anyway
      onAccept();
    } finally {
      setCheckingOffer(null);
    }
  };
  
  const calculateBudget = () => { const eq = equipment.find(e=>e.name===filmData.equipment_package)||{cost:0}; let loc=0; filmData.locations.forEach(l=>{const lo=locations.find(x=>x.name===l); if(lo)loc+=lo.cost_per_day*(filmData.location_days[l]||7);}); return eq.cost+loc+filmData.extras_cost; };
  const getSponsorBudget = () => { if(!filmData.sponsor_id)return 0; const s=sponsors.find(x=>x.name===filmData.sponsor_id); return s?.budget_offer||0; };
  
  // Tier popup state
  const [tierPopup, setTierPopup] = useState(null);
  const [criticReviewsPopup, setCriticReviewsPopup] = useState(null);
  
  const TIER_STYLES = {
    masterpiece: { bg: 'from-yellow-500/30 to-amber-500/30', border: 'border-yellow-500', text: 'text-yellow-400', emoji: '🏆' },
    epic: { bg: 'from-purple-500/30 to-pink-500/30', border: 'border-purple-500', text: 'text-purple-400', emoji: '⭐' },
    excellent: { bg: 'from-blue-500/30 to-cyan-500/30', border: 'border-blue-500', text: 'text-blue-400', emoji: '✨' },
    promising: { bg: 'from-green-500/30 to-emerald-500/30', border: 'border-green-500', text: 'text-green-400', emoji: '🌟' },
    flop: { bg: 'from-red-500/30 to-orange-500/30', border: 'border-red-500', text: 'text-red-400', emoji: '💔' },
    normal: { bg: 'from-gray-500/30 to-slate-500/30', border: 'border-gray-500', text: 'text-gray-400', emoji: '🎬' }
  };
  
  const handleSubmit = async () => { 
    setLoading(true); 
    try { 
      const res = await api.post('/films', {...filmData, release_date: releaseDate.toISOString()}); 
      
      // Check if film got a special tier
      const tier = res.data.film_tier || 'normal';
      const tierStyle = TIER_STYLES[tier] || TIER_STYLES.normal;
      
      // Always show the critic reviews popup on film release
      setCriticReviewsPopup({
        filmId: res.data.id,
        filmTitle: res.data.title,
        tier: tier,
        tierStyle: tierStyle,
        tierName: tier === 'masterpiece' ? 'Capolavoro' : 
                 tier === 'epic' ? 'Epico' : 
                 tier === 'excellent' ? 'Eccellente' : 
                 tier === 'promising' ? 'Promettente' : 
                 tier === 'flop' ? 'Possibile Flop' :
                 tier === 'mediocre' ? 'Mediocre' :
                 tier === 'poor' ? 'Scarso' : 'Standard',
        opening: res.data.opening_day_revenue,
        qualityScore: res.data.quality_score,
        reviews: res.data.critic_reviews || [],
        effects: res.data.critic_effects || {},
      });
      
      updateFunds(user.funds - calculateBudget() + getSponsorBudget() + filmData.ad_revenue + res.data.opening_day_revenue); 
    } catch(e) { 
      toast.error(e.response?.data?.detail||'Failed'); 
    } finally { 
      setLoading(false); 
    }
  };

  const getRoleName = (roleId) => {
    const role = actorRoles.find(r => r.id === roleId);
    if (!role) return roleId;
    const langKey = `name_${language}`;
    return role[langKey] || role.name;
  };

  // Check if a cast member is pre-engaged
  const isPreEngaged = (castType, castId) => {
    if (!preEngagedCast) return false;
    if (castType === 'actor') {
      return preEngagedCast.actors?.some(a => a.id === castId);
    }
    return preEngagedCast[castType]?.id === castId;
  };

  // Get pre-engaged cast info
  const getPreEngagedInfo = (castType, castId) => {
    if (!preEngagedCast) return null;
    if (castType === 'actor') {
      return preEngagedCast.actors?.find(a => a.id === castId);
    }
    return preEngagedCast[castType];
  };

  // Handle dismissing pre-engaged cast
  const handleDismissCast = async (castType, castId) => {
    if (!preFilmId) return;
    
    try {
      const res = await api.post(`/pre-films/${preFilmId}/dismiss-cast?cast_type=${castType}&cast_id=${castId}`);
      setDismissModal({
        castType,
        castId,
        ...res.data
      });
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  // Confirm dismissal
  const confirmDismissal = async () => {
    if (!dismissModal || !preFilmId) return;
    
    try {
      // Actually release the cast
      await api.post(`/pre-films/${preFilmId}/release`, {
        pre_film_id: preFilmId,
        cast_type: dismissModal.castType,
        cast_id: dismissModal.castId
      });
      
      toast.success(`${dismissModal.cast_name} ${language === 'it' ? 'congedato' : 'dismissed'}`);
      
      // Update local state
      if (dismissModal.castType === 'screenwriter') {
        setFilmData(prev => ({...prev, screenwriter_id: ''}));
      } else if (dismissModal.castType === 'director') {
        setFilmData(prev => ({...prev, director_id: ''}));
      } else if (dismissModal.castType === 'composer') {
        setFilmData(prev => ({...prev, composer_id: ''}));
      } else if (dismissModal.castType === 'actor') {
        setFilmData(prev => ({
          ...prev,
          actors: prev.actors.filter(a => a.id !== dismissModal.castId)
        }));
      }
      
      // Update pre-engaged cast state
      setPreEngagedCast(prev => {
        if (!prev) return prev;
        if (dismissModal.castType === 'actor') {
          return {...prev, actors: prev.actors.filter(a => a.id !== dismissModal.castId)};
        }
        return {...prev, [dismissModal.castType]: null};
      });
      
      setDismissModal(null);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const PersonCard = ({ person, isSelected, onSelect, showRoleSelect = false, currentRole = null, onRoleChange = null, roleType = 'actor' }) => {
    const isRefused = refusedIds.has(person.id);
    const isChecking = checkingOffer === person.id;
    
    // Generate star display
    const renderStars = (count) => {
      return Array(5).fill(0).map((_, i) => (
        <Star key={i} className={`w-2.5 h-2.5 ${i < count ? 'fill-yellow-500 text-yellow-500' : 'text-gray-600'}`} />
      ));
    };
    
    const getFameColor = (category) => {
      switch(category) {
        case 'superstar': return 'text-purple-400 bg-purple-500/20';
        case 'famous': return 'text-yellow-400 bg-yellow-500/20';
        case 'rising': return 'text-blue-400 bg-blue-500/20';
        case 'known': return 'text-green-400 bg-green-500/20';
        default: return 'text-gray-400 bg-gray-500/20';
      }
    };
    
    const getCategoryColor = (category) => {
      switch(category) {
        case 'recommended': return 'text-emerald-400 bg-emerald-500/20';
        case 'star': return 'text-purple-400 bg-purple-500/20';
        case 'known': return 'text-blue-400 bg-blue-500/20';
        case 'emerging': return 'text-orange-400 bg-orange-500/20';
        case 'unknown': return 'text-gray-400 bg-gray-500/20';
        default: return 'text-gray-400 bg-gray-500/20';
      }
    };
    
    const getCategoryName = (category) => {
      const names = {
        recommended: language === 'it' ? 'Consigliato' : 'Recommended',
        star: 'Star',
        known: language === 'it' ? 'Conosciuto' : 'Known',
        emerging: language === 'it' ? 'Emergente' : 'Emerging',
        unknown: language === 'it' ? 'Sconosciuto' : 'Unknown'
      };
      return names[category] || category;
    };
    
    // Get primary skills display
    const primarySkillsDisplay = person.primary_skills_translated || person.primary_skills || [];
    const secondarySkillDisplay = person.secondary_skill_translated || person.secondary_skill;
    
    // Handle click with offer system
    const handleClick = () => {
      if (isRefused || isChecking) return;
      makeOffer(person, roleType, onSelect);
    };
    
    return (
      <Card 
        className={`border-2 transition-all ${
          isRefused 
            ? 'bg-red-950/30 border-red-500/30 cursor-not-allowed opacity-60' 
            : isChecking
              ? 'bg-[#1A1A1A] border-yellow-500/50 animate-pulse cursor-wait'
              : isSelected 
                ? 'bg-[#1A1A1A] border-yellow-500 ring-1 ring-yellow-500/50 cursor-pointer' 
                : 'bg-[#1A1A1A] border-white/10 hover:border-white/20 cursor-pointer'
        }`} 
        onClick={handleClick}
      >
        <CardContent className="p-2 relative">
          {/* Refused overlay */}
          {isRefused && (
            <div className="absolute top-1 right-1 z-10">
              <Badge className="bg-red-500/80 text-white text-[8px] flex items-center gap-1">
                <XCircle className="w-2.5 h-2.5" />
                {language === 'it' ? 'Ha rifiutato' : 'Refused'}
              </Badge>
            </div>
          )}
          
          {/* Loading overlay */}
          {isChecking && (
            <div className="absolute inset-0 bg-black/30 flex items-center justify-center z-10 rounded-lg">
              <div className="text-xs text-yellow-400 animate-pulse">
                {language === 'it' ? 'Contattando...' : 'Contacting...'}
              </div>
            </div>
          )}
          
          {/* Header: Avatar, Name, Cost */}
          <div className="flex items-start gap-2 mb-1.5">
            <Avatar className="w-10 h-10 flex-shrink-0"><AvatarImage src={person.avatar_url} /><AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xs">{person.name[0]}</AvatarFallback></Avatar>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1 flex-wrap">
                <h4 className="font-semibold text-xs truncate max-w-[100px]">{person.name}</h4>
                <span className="text-[10px] text-gray-400">{person.gender === 'female' ? '♀' : '♂'}</span>
                {person.is_hidden_gem && <Sparkles className="w-2.5 h-2.5 text-green-500" title="Hidden Gem!" />}
                {person.has_worked_with_us && (
                  <Badge className="text-[8px] h-3.5 px-1 bg-cyan-500/20 text-cyan-400 whitespace-nowrap">
                    {language === 'it' ? 'Ha lavorato con noi' : 'Worked with us'}
                  </Badge>
                )}
              </div>
              {/* Primary & Secondary Skills inline */}
              <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                {primarySkillsDisplay.slice(0, 2).map((skill, idx) => (
                  <span key={idx} className="text-[9px] text-yellow-400 bg-yellow-500/10 px-1 py-0.5 rounded">
                    {skill}
                  </span>
                ))}
                {secondarySkillDisplay && (
                  <span className="text-[9px] text-gray-400 bg-white/5 px-1 py-0.5 rounded">
                    {secondarySkillDisplay}
                  </span>
                )}
              </div>
              <p className="text-[10px] text-gray-400 mt-0.5">{person.nationality} • {person.age}yo • {person.years_active}y exp</p>
            </div>
            <p className="text-yellow-500 font-bold text-xs whitespace-nowrap">${((person.cost_per_film || 0)/1000).toFixed(0)}K</p>
          </div>
          
          {/* Stars, Category row */}
          <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
            {person.stars && (
              <div className="flex items-center gap-0.5" title={`${person.stars} stelle`}>
                {renderStars(person.stars)}
              </div>
            )}
            {person.category && (
              <Badge className={`text-[8px] h-4 px-1 ${getCategoryColor(person.category)}`}>
                {person.category_translated || getCategoryName(person.category)}
              </Badge>
            )}
            {person.fame_category && (
              <Badge className={`text-[8px] h-4 px-1 ${getFameColor(person.fame_category)}`}>
                {person.fame_category === 'superstar' ? 'Superstar' : 
                 person.fame_category === 'famous' ? (language === 'it' ? 'Famoso' : 'Famous') : 
                 person.fame_category === 'rising' ? (language === 'it' ? 'In Ascesa' : 'Rising') : 
                 person.fame_category === 'known' ? (language === 'it' ? 'Noto' : 'Known') : 
                 (language === 'it' ? 'Sconosciuto' : 'Unknown')}
              </Badge>
            )}
          </div>
          
          {/* Skills grid - show only 4 */}
          <div className="grid grid-cols-2 gap-0.5">
            {Object.entries(person.skills||{}).slice(0,4).map(([s,v])=><SkillBadge key={s} name={s} value={v} change={person.skill_changes?.[s]||0} language={language} />)}
          </div>
          
          {showRoleSelect && isSelected && (
            <div className="mt-2 pt-2 border-t border-white/10" onClick={e => e.stopPropagation()}>
              <Select value={currentRole} onValueChange={onRoleChange}>
                <SelectTrigger className="h-7 text-xs bg-black/20 border-white/10">
                  <SelectValue placeholder="Select role..." />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A]">
                  {actorRoles.map(r => (
                    <SelectItem key={r.id} value={r.id} className="text-xs">{getRoleName(r.id)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const toggleSubgenre = (subgenre) => {
    if (filmData.subgenres.includes(subgenre)) {
      setFilmData({...filmData, subgenres: filmData.subgenres.filter(s => s !== subgenre)});
    } else if (filmData.subgenres.length < 3) {
      setFilmData({...filmData, subgenres: [...filmData.subgenres, subgenre]});
    } else {
      toast.error('Max 3 sub-genres allowed');
    }
  };

  const renderStep = () => {
    switch(step) {
      case 1: return (<div className="space-y-3">
        <div><Label className="text-xs">{language === 'it' ? 'Titolo' : 'Title'} *</Label><Input value={filmData.title} onChange={e=>setFilmData({...filmData,title:e.target.value})} placeholder={language === 'it' ? 'Titolo del film...' : 'Film title...'} className="h-10 bg-black/20 border-white/10" data-testid="film-title-input" /></div>
        
        {/* Subtitle - optional, required for sequels */}
        <div>
          <Label className="text-xs">{language === 'it' ? 'Sottotitolo' : 'Subtitle'} {filmData.is_sequel && <span className="text-red-400">*</span>}</Label>
          <Input 
            value={filmData.subtitle} 
            onChange={e=>setFilmData({...filmData,subtitle:e.target.value})} 
            placeholder={language === 'it' ? 'es. "La Vendetta", "Il Ritorno"...' : 'e.g. "The Revenge", "The Return"...'} 
            className="h-9 bg-black/20 border-white/10" 
            data-testid="film-subtitle-input" 
          />
          <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Opzionale. Obbligatorio per i sequel.' : 'Optional. Required for sequels.'}</p>
        </div>
        
        {/* Sequel checkbox and parent selection */}
        <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Checkbox 
              id="is-sequel" 
              checked={filmData.is_sequel}
              onCheckedChange={(checked) => setFilmData({...filmData, is_sequel: checked, sequel_parent_id: checked ? filmData.sequel_parent_id : null})}
            />
            <Label htmlFor="is-sequel" className="text-sm cursor-pointer">
              {language === 'it' ? 'Questo è un sequel' : 'This is a sequel'}
            </Label>
          </div>
          
          {filmData.is_sequel && (
            <div className="pl-6 space-y-2">
              <Label className="text-xs">{language === 'it' ? 'Seleziona il film originale' : 'Select original film'} *</Label>
              {myFilmsForSequel.length > 0 ? (
                <Select value={filmData.sequel_parent_id || ''} onValueChange={v => {
                  const parent = myFilmsForSequel.find(f => f.id === v);
                  setFilmData({...filmData, sequel_parent_id: v, genre: parent?.genre || filmData.genre});
                }}>
                  <SelectTrigger className="h-9 bg-black/30 border-white/10">
                    <SelectValue placeholder={language === 'it' ? 'Seleziona...' : 'Select...'} />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1A1A1A] max-h-[200px]">
                    {myFilmsForSequel.map(f => (
                      <SelectItem key={f.id} value={f.id} className="text-xs">
                        <div className="flex items-center gap-2">
                          <span>{f.full_title}</span>
                          <Badge className={`text-[8px] ${f.film_tier === 'masterpiece' ? 'bg-yellow-500/20 text-yellow-400' : f.film_tier === 'possible_flop' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20'}`}>
                            Q:{f.quality_score}
                          </Badge>
                          {f.sequel_count > 0 && <span className="text-[9px] text-gray-400">({f.sequel_count} sequel)</span>}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-xs text-gray-400">{language === 'it' ? 'Nessun film disponibile. Crea prima un film.' : 'No films available. Create a film first.'}</p>
              )}
              
              {filmData.sequel_parent_id && (
                <div className="text-xs bg-black/30 rounded p-2">
                  {(() => {
                    const parent = myFilmsForSequel.find(f => f.id === filmData.sequel_parent_id);
                    if (!parent) return null;
                    const bonus = parent.quality_score >= 70 ? '+' : parent.quality_score < 40 ? '-' : '±';
                    const bonusColor = parent.quality_score >= 70 ? 'text-green-400' : parent.quality_score < 40 ? 'text-red-400' : 'text-yellow-400';
                    return (
                      <div className="flex items-center gap-2">
                        <TrendingUp className={`w-3 h-3 ${bonusColor}`} />
                        <span className={bonusColor}>
                          {language === 'it' 
                            ? `Bonus sequel: ${bonus} (basato su qualità ${parent.quality_score})`
                            : `Sequel bonus: ${bonus} (based on quality ${parent.quality_score})`}
                        </span>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div>
          <Label className="text-xs">{t('genre')} *</Label>
          <Select value={filmData.genre} onValueChange={v=>setFilmData({...filmData, genre:v, subgenres: []})} disabled={filmData.is_sequel && filmData.sequel_parent_id}>
            <SelectTrigger className="h-9 bg-black/20 border-white/10"><SelectValue /></SelectTrigger>
            <SelectContent className="bg-[#1A1A1A] max-h-[200px]">
              {Object.entries(genres).map(([key, g])=><SelectItem key={key} value={key}>{g.name}</SelectItem>)}
            </SelectContent>
          </Select>
          {filmData.is_sequel && filmData.sequel_parent_id && (
            <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Il genere è ereditato dal film originale' : 'Genre inherited from original film'}</p>
          )}
        </div>
        {genres[filmData.genre] && (
          <div>
            <Label className="text-xs">Sub-genres (max 3)</Label>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {genres[filmData.genre].subgenres.map(sg => (
                <Badge 
                  key={sg}
                  variant={filmData.subgenres.includes(sg) ? "default" : "outline"}
                  className={`cursor-pointer text-xs ${filmData.subgenres.includes(sg) ? 'bg-yellow-500 text-black hover:bg-yellow-600' : 'hover:bg-white/10'}`}
                  onClick={() => toggleSubgenre(sg)}
                >
                  {sg} {filmData.subgenres.includes(sg) && <X className="w-2.5 h-2.5 ml-1" />}
                </Badge>
              ))}
            </div>
            {filmData.subgenres.length > 0 && (
              <p className="text-xs text-gray-400 mt-1">Selected: {filmData.subgenres.join(', ')}</p>
            )}
          </div>
        )}
        <div><Label className="text-xs">{t('release_date')}</Label><Popover><PopoverTrigger asChild><Button variant="outline" className="w-full h-9 justify-start bg-black/20 border-white/10"><Calendar className="w-3 h-3 mr-2" />{format(releaseDate,'PPP')}</Button></PopoverTrigger><PopoverContent className="w-auto p-0 bg-[#1A1A1A] border-white/10"><CalendarComponent mode="single" selected={releaseDate} onSelect={setReleaseDate} disabled={d=>d<new Date(new Date().setHours(0,0,0,0))} /></PopoverContent></Popover></div>
        <div><Label className="text-xs">Weeks: {filmData.weeks_in_theater}</Label><Slider value={[filmData.weeks_in_theater]} onValueChange={([v])=>setFilmData({...filmData,weeks_in_theater:v})} min={1} max={12} /></div>
      </div>);
      case 2: return (<div className="space-y-2">
        <Card className={`border-2 cursor-pointer ${!filmData.sponsor_id?'border-yellow-500':'border-white/10'}`} onClick={()=>setFilmData({...filmData,sponsor_id:null})}><CardContent className="p-2 flex items-center gap-2"><X className="w-4 h-4" /><span className="text-sm">No Sponsor</span></CardContent></Card>
        {sponsors.map(s=><Card key={s.name} className={`border-2 cursor-pointer ${filmData.sponsor_id===s.name?'border-yellow-500':'border-white/10'}`} onClick={()=>setFilmData({...filmData,sponsor_id:s.name})}><CardContent className="p-2 flex justify-between items-center"><span className="text-sm">{s.name}</span><div className="text-right"><span className="text-green-400 text-sm">+${s.budget_offer.toLocaleString()}</span><span className="text-red-400 text-xs ml-2">-{s.revenue_share}%</span></div></CardContent></Card>)}
      </div>);
      case 3: return (<div className="space-y-3">
        <div><Label className="text-xs">Equipment</Label><div className="space-y-1">{equipment.map(e=><Card key={e.name} className={`border-2 cursor-pointer ${filmData.equipment_package===e.name?'border-yellow-500':'border-white/10'}`} onClick={()=>setFilmData({...filmData,equipment_package:e.name})}><CardContent className="p-2 flex justify-between"><span className="text-sm">{e.name} <span className="text-gray-400">(+{e.quality_bonus}%)</span></span><span className="text-yellow-500 text-sm">${e.cost.toLocaleString()}</span></CardContent></Card>)}</div></div>
        <div><Label className="text-xs">Locations</Label><div className="grid grid-cols-2 gap-1">{locations.map(l=>{const sel=filmData.locations.includes(l.name);return<Card key={l.name} className={`border-2 cursor-pointer ${sel?'border-yellow-500':'border-white/10'}`} onClick={()=>{if(sel)setFilmData({...filmData,locations:filmData.locations.filter(x=>x!==l.name)});else setFilmData({...filmData,locations:[...filmData.locations,l.name],location_days:{...filmData.location_days,[l.name]:7}});}}><CardContent className="p-1.5 text-xs"><span>{l.name}</span><span className="text-yellow-500 block">${l.cost_per_day.toLocaleString()}/day</span></CardContent></Card>;})}</div></div>
      </div>);
      case 4: case 5:
        const people45 = step===4?screenwriters:directors;
        const selId = step===4?filmData.screenwriter_id:filmData.director_id;
        const roleType45 = step===4?'screenwriters':'directors';
        const skills45 = step===4?availableSkills.screenwriters:availableSkills.directors;
        return (<div className="space-y-2">
          {/* Filters Row */}
          <div className="flex flex-wrap gap-2 p-2 bg-black/20 rounded border border-white/10">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="h-7 w-[140px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Categoria...' : 'Category...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte' : 'All'}</SelectItem>
                <SelectItem value="recommended" className="text-xs">{language === 'it' ? 'Consigliati' : 'Recommended'}</SelectItem>
                <SelectItem value="star" className="text-xs">Star</SelectItem>
                <SelectItem value="known" className="text-xs">{language === 'it' ? 'Conosciuti' : 'Known'}</SelectItem>
                <SelectItem value="emerging" className="text-xs">{language === 'it' ? 'Emergenti' : 'Emerging'}</SelectItem>
                <SelectItem value="unknown" className="text-xs">{language === 'it' ? 'Sconosciuti' : 'Unknown'}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSkill} onValueChange={setSelectedSkill}>
              <SelectTrigger className="h-7 w-[150px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Filtra skill...' : 'Filter skill...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte le skill' : 'All skills'}</SelectItem>
                {skills45.map(sk => (
                  <SelectItem key={sk} value={sk} className="text-xs">{sk}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="h-7" onClick={()=>fetchPeople(roleType45, selectedCategory, selectedSkill)}><RefreshCw className="w-3 h-3 mr-1" />Refresh</Button>
          </div>
          <p className="text-xs text-gray-400">{people45.length} {step===4?(language==='it'?'sceneggiatori':'screenwriters'):(language==='it'?'registi':'directors')} {language==='it'?'trovati':'found'}</p>
          <ScrollArea className="h-[380px] sm:h-[420px]"><div className="space-y-1.5 pr-2">{people45.map(p=>{const isSel=selId===p.id;return<PersonCard key={p.id} person={p} isSelected={isSel} roleType={step===4?'screenwriter':'director'} onSelect={()=>{if(step===4)setFilmData({...filmData,screenwriter_id:p.id});else setFilmData({...filmData,director_id:p.id});}} />;})}</div></ScrollArea>
        </div>);
      case 6:
        return (<div className="space-y-2">
          {/* Filters Row */}
          <div className="flex flex-wrap gap-2 p-2 bg-black/20 rounded border border-white/10">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="h-7 w-[140px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Categoria...' : 'Category...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte' : 'All'}</SelectItem>
                <SelectItem value="recommended" className="text-xs">{language === 'it' ? 'Consigliati' : 'Recommended'}</SelectItem>
                <SelectItem value="star" className="text-xs">Star</SelectItem>
                <SelectItem value="known" className="text-xs">{language === 'it' ? 'Conosciuti' : 'Known'}</SelectItem>
                <SelectItem value="emerging" className="text-xs">{language === 'it' ? 'Emergenti' : 'Emerging'}</SelectItem>
                <SelectItem value="unknown" className="text-xs">{language === 'it' ? 'Sconosciuti' : 'Unknown'}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSkill} onValueChange={setSelectedSkill}>
              <SelectTrigger className="h-7 w-[150px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Filtra skill...' : 'Filter skill...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte le skill' : 'All skills'}</SelectItem>
                {availableSkills.composers.map(sk => (
                  <SelectItem key={sk} value={sk} className="text-xs">{sk}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="h-7" onClick={()=>fetchPeople('composers', selectedCategory, selectedSkill)}><RefreshCw className="w-3 h-3 mr-1" />Refresh</Button>
          </div>
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-400"><Music className="w-3 h-3 inline mr-1" />{composers.length} {language==='it'?'compositori trovati':'composers found'}</p>
          </div>
          <ScrollArea className="h-[380px] sm:h-[420px]">
            <div className="space-y-1.5 pr-2">
              {composers.map(p => {
                const isSel = filmData.composer_id === p.id;
                return <PersonCard key={p.id} person={p} isSelected={isSel} roleType="composer" onSelect={() => setFilmData({...filmData, composer_id: p.id})} />;
              })}
            </div>
          </ScrollArea>
        </div>);
      case 7:
        return (<div className="space-y-2">
          {/* Filters Row */}
          <div className="flex flex-wrap gap-2 p-2 bg-black/20 rounded border border-white/10">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="h-7 w-[140px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Categoria...' : 'Category...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte' : 'All'}</SelectItem>
                <SelectItem value="recommended" className="text-xs">{language === 'it' ? 'Consigliati' : 'Recommended'}</SelectItem>
                <SelectItem value="star" className="text-xs">Star</SelectItem>
                <SelectItem value="known" className="text-xs">{language === 'it' ? 'Conosciuti' : 'Known'}</SelectItem>
                <SelectItem value="emerging" className="text-xs">{language === 'it' ? 'Emergenti' : 'Emerging'}</SelectItem>
                <SelectItem value="unknown" className="text-xs">{language === 'it' ? 'Sconosciuti' : 'Unknown'}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSkill} onValueChange={setSelectedSkill}>
              <SelectTrigger className="h-7 w-[150px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Filtra skill...' : 'Filter skill...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte le skill' : 'All skills'}</SelectItem>
                {availableSkills.actors.map(sk => (
                  <SelectItem key={sk} value={sk} className="text-xs">{sk}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="h-7" onClick={()=>fetchPeople('actors', selectedCategory, selectedSkill)}><RefreshCw className="w-3 h-3 mr-1" />Refresh</Button>
          </div>
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-400">{language === 'it' ? 'Selezionati' : 'Selected'}: {filmData.actors.length} {language === 'it' ? 'attori' : 'actors'} • {actors.length} {language === 'it' ? 'disponibili' : 'available'}</p>
          </div>
          {filmData.actors.length > 0 && (
            <div className="flex flex-wrap gap-1 p-2 bg-black/20 rounded border border-white/10">
              {filmData.actors.map(a => {
                const actor = actors.find(ac => ac.id === a.actor_id);
                return actor ? (
                  <Badge key={a.actor_id} className="bg-yellow-500/20 text-yellow-500 text-xs">
                    {actor.name} ({getRoleName(a.role)})
                    <X className="w-2.5 h-2.5 ml-1 cursor-pointer" onClick={() => setFilmData({...filmData, actors: filmData.actors.filter(x => x.actor_id !== a.actor_id)})} />
                  </Badge>
                ) : null;
              })}
            </div>
          )}
          <ScrollArea className="h-[320px] sm:h-[360px]">
            <div className="space-y-1.5 pr-2">
              {actors.map(p => {
                const selectedActor = filmData.actors.find(a => a.actor_id === p.id);
                const isSel = !!selectedActor;
                return (
                  <PersonCard 
                    key={p.id} 
                    person={p} 
                    isSelected={isSel}
                    roleType="actor"
                    showRoleSelect={true}
                    currentRole={selectedActor?.role || 'protagonist'}
                    onRoleChange={(newRole) => {
                      setFilmData({
                        ...filmData, 
                        actors: filmData.actors.map(a => a.actor_id === p.id ? {...a, role: newRole} : a)
                      });
                    }}
                    onSelect={() => {
                      if (isSel) {
                        setFilmData({...filmData, actors: filmData.actors.filter(a => a.actor_id !== p.id)});
                      } else {
                        setFilmData({...filmData, actors: [...filmData.actors, {actor_id: p.id, role: 'protagonist'}]});
                      }
                    }} 
                  />
                );
              })}
            </div>
          </ScrollArea>
          <div><Label className="text-xs">Extras: {filmData.extras_count} (${filmData.extras_cost.toLocaleString()})</Label><Slider value={[filmData.extras_count]} onValueChange={([v])=>setFilmData({...filmData,extras_count:v,extras_cost:v*1000})} min={0} max={500} step={10} /></div>
        </div>);
      case 8: return (<div className="space-y-3">
        <div className="flex gap-2"><Button variant={filmData.screenplay_source==='manual'?'default':'outline'} size="sm" onClick={()=>setFilmData({...filmData,screenplay_source:'manual'})} className={filmData.screenplay_source==='manual'?'bg-yellow-500 text-black':''}>Manuale</Button><Button variant="outline" size="sm" onClick={generateScreenplay} disabled={generating||!filmData.title}><Sparkles className="w-3 h-3 mr-1" />{generating?'...':'Genera con AI'}</Button></div>
        <Input value={filmData.screenplay_prompt} onChange={e=>setFilmData({...filmData,screenplay_prompt:e.target.value})} placeholder="La tua idea per la sceneggiatura... (opzionale per AI)" className="bg-black/20 border-white/10 text-sm" />
        <Textarea value={filmData.screenplay} onChange={e=>setFilmData({...filmData,screenplay:e.target.value})} placeholder="Sceneggiatura..." className="min-h-[200px] bg-black/20 border-white/10" />
      </div>);
      case 9: return (<div className="space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Music className="w-5 h-5 text-purple-400" />
          <p className="text-sm">Genera una descrizione per la colonna sonora AI</p>
        </div>
        <Input value={filmData.soundtrack_prompt} onChange={e=>setFilmData({...filmData,soundtrack_prompt:e.target.value})} placeholder="Il tuo concept per la colonna sonora... (es: epica orchestrale con cori)" className="bg-black/20 border-white/10 text-sm" />
        <Button variant="outline" onClick={generateSoundtrack} disabled={generating||!filmData.title} className="border-purple-500/30 text-purple-400">
          <Sparkles className="w-3 h-3 mr-1" />{generating?'Generazione...':'Genera Descrizione AI'}
        </Button>
        {filmData.soundtrack_description && (
          <Card className="bg-purple-500/10 border-purple-500/30">
            <CardContent className="p-3">
              <p className="text-sm text-purple-200">{filmData.soundtrack_description}</p>
            </CardContent>
          </Card>
        )}
        <p className="text-xs text-gray-500">La descrizione verrà usata per generare la colonna sonora nel trailer del film.</p>
      </div>);
      case 10: return (<div className="grid md:grid-cols-2 gap-3">
        <div className="space-y-2">
          <Textarea value={filmData.poster_prompt} onChange={e=>setFilmData({...filmData,poster_prompt:e.target.value})} placeholder="Describe poster..." className="min-h-[100px] bg-black/20 border-white/10" />
          <Button onClick={generatePoster} disabled={generating} className="w-full bg-yellow-500 text-black"><Sparkles className="w-3 h-3 mr-1" />{generating?'...':'Generate AI Poster'}</Button>
          <Input value={filmData.poster_url} onChange={e=>setFilmData({...filmData,poster_url:e.target.value})} placeholder="Or paste URL..." className="bg-black/20 border-white/10" />
        </div>
        <div className="aspect-[2/3] bg-[#1A1A1A] rounded border border-white/10 overflow-hidden">{filmData.poster_url?<img src={filmData.poster_url} alt="Poster" className="w-full h-full object-cover" />:<div className="w-full h-full flex items-center justify-center text-gray-500"><Image className="w-10 h-10 opacity-50" /></div>}</div>
      </div>);
      case 11: return (<div className="space-y-3">
        <p className="text-xs text-gray-400">Ads give immediate revenue but may reduce satisfaction.</p>
        <div><Label className="text-xs">Duration: {filmData.ad_duration_seconds}s</Label><Slider value={[filmData.ad_duration_seconds]} onValueChange={([v])=>setFilmData({...filmData,ad_duration_seconds:v,ad_revenue:v*5000})} min={0} max={180} step={15} /></div>
        <Card className="bg-[#1A1A1A] border-white/10"><CardContent className="p-3"><div className="flex justify-between"><span>Immediate Revenue</span><span className="text-green-400 text-lg">+${filmData.ad_revenue.toLocaleString()}</span></div>{filmData.ad_duration_seconds>60&&<p className="text-xs text-yellow-500 mt-1">⚠️ High ads may reduce satisfaction</p>}</CardContent></Card>
      </div>);
      case 12:
        const budget=calculateBudget(), sponsor=getSponsorBudget(), net=budget-sponsor-filmData.ad_revenue;
        return (<Card className="bg-[#1A1A1A] border-white/10"><CardHeader className="pb-2"><CardTitle className="font-['Bebas_Neue'] text-xl">{filmData.title}</CardTitle><CardDescription>{t(filmData.genre)} • {filmData.weeks_in_theater}w</CardDescription></CardHeader><CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs"><div><span className="text-gray-400">Release</span><p>{format(releaseDate,'PPP')}</p></div><div><span className="text-gray-400">Sponsor</span><p>{filmData.sponsor_id||'None'}</p></div><div><span className="text-gray-400">Equipment</span><p>{filmData.equipment_package}</p></div><div><span className="text-gray-400">Cast</span><p>{filmData.actors.length}+{filmData.extras_count}</p></div><div><span className="text-gray-400">Composer</span><p>{composers.find(c=>c.id===filmData.composer_id)?.name||'None'}</p></div></div>
          <div className="pt-2 border-t border-white/10 space-y-1 text-sm"><div className="flex justify-between"><span>Budget</span><span className="text-red-400">-${budget.toLocaleString()}</span></div>{sponsor>0&&<div className="flex justify-between"><span>Sponsor</span><span className="text-green-400">+${sponsor.toLocaleString()}</span></div>}{filmData.ad_revenue>0&&<div className="flex justify-between"><span>Ads</span><span className="text-green-400">+${filmData.ad_revenue.toLocaleString()}</span></div>}<div className="flex justify-between font-bold pt-1 border-t border-white/10"><span>Net</span><span className={net>0?'text-red-400':'text-green-400'}>${Math.abs(net).toLocaleString()}</span></div></div>
        </CardContent></Card>);
      default: return null;
    }
  };

  const canProceed = () => { switch(step){ case 1:return filmData.title&&filmData.genre; case 3:return filmData.locations.length>0; case 4:return filmData.screenwriter_id; case 5:return filmData.director_id; case 6:return filmData.composer_id; case 7:return filmData.actors.length>0; case 8:return filmData.screenplay; default:return true; }};

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="film-wizard">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2 overflow-x-auto pb-1">{steps.map((s,i)=>(<div key={s.num} className="flex items-center"><div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step===s.num?'bg-yellow-500 text-black':step>s.num?'bg-green-500 text-white':'bg-gray-700 text-gray-400'}`}>{step>s.num?'✓':s.num}</div>{i<steps.length-1&&<div className={`w-3 h-0.5 mx-0.5 ${step>s.num?'bg-green-500':'bg-gray-700'}`} />}</div>))}</div>
        <h2 className="font-['Bebas_Neue'] text-xl">{steps[step-1].title}</h2>
      </div>
      <Card className="bg-[#1A1A1A] border-white/10"><CardContent className="p-3"><AnimatePresence mode="wait"><motion.div key={step} initial={{opacity:0,x:20}} animate={{opacity:1,x:0}} exit={{opacity:0,x:-20}}>{renderStep()}</motion.div></AnimatePresence></CardContent></Card>
      <div className="flex justify-between items-center mt-3">
        <div className="flex gap-2 items-center">
          <Button variant="outline" size="sm" onClick={()=>setStep(step-1)} disabled={step===1}>Previous</Button>
          <Button variant="outline" size="sm" onClick={()=>saveDraft('paused')} disabled={savingDraft} className="text-orange-400 border-orange-400/50 hover:bg-orange-500/10">
            {savingDraft ? '...' : (language === 'it' ? 'Metti in Pausa' : 'Pause')}
          </Button>
          {lastAutoSave && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <CheckCircle className="w-3 h-3 text-green-500" />
              {language === 'it' ? 'Salvato' : 'Saved'} {lastAutoSave.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
            </span>
          )}
        </div>
        {step<12?<Button size="sm" onClick={()=>setStep(step+1)} disabled={!canProceed()} className="bg-yellow-500 text-black">Next <ChevronRight className="w-3 h-3 ml-1" /></Button>:<Button size="sm" onClick={handleSubmit} disabled={loading||calculateBudget()-getSponsorBudget()-filmData.ad_revenue>user.funds} className="bg-yellow-500 text-black">{loading?'...':'Create Film'}</Button>}
      </div>

      {/* Rejection Modal */}
      {rejectionModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setRejectionModal(null)}>
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] border border-red-500/50 rounded-lg p-6 max-w-sm w-full"
            onClick={e => e.stopPropagation()}
            data-testid="rejection-modal"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                <XCircle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h3 className="font-bold text-lg text-red-400">
                  {language === 'it' ? 'Offerta Rifiutata' : 'Offer Rejected'}
                </h3>
                <p className="text-sm text-gray-400">{rejectionModal.name}</p>
              </div>
            </div>
            
            <div className="bg-black/30 rounded-lg p-4 mb-4">
              <p className="text-sm text-gray-300 italic">"{rejectionModal.reason}"</p>
            </div>
            
            {rejectionModal.alreadyRefused && (
              <p className="text-xs text-yellow-500 mb-3">
                {language === 'it' 
                  ? '⚠️ Questa persona ha già rifiutato la tua offerta oggi.' 
                  : '⚠️ This person already refused your offer today.'}
              </p>
            )}
            
            <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
              {rejectionModal.stars && (
                <div className="flex items-center gap-1">
                  {Array(5).fill(0).map((_, i) => (
                    <Star key={i} className={`w-3 h-3 ${i < rejectionModal.stars ? 'fill-yellow-500 text-yellow-500' : 'text-gray-600'}`} />
                  ))}
                </div>
              )}
              {rejectionModal.fame && (
                <span>{language === 'it' ? 'Fama' : 'Fame'}: {rejectionModal.fame}</span>
              )}
            </div>
            
            <Button 
              className="w-full bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30"
              onClick={() => setRejectionModal(null)}
              data-testid="rejection-modal-close"
            >
              {language === 'it' ? 'Ho capito' : 'I understand'}
            </Button>
            
            {rejectionModal.can_renegotiate && rejectionModal.negotiation_id && !rejectionModal.alreadyRefused && (
              <div className="mt-3 p-3 rounded bg-yellow-500/10 border border-yellow-500/30">
                <p className="text-xs text-yellow-400 font-semibold mb-2">
                  {language === 'it' ? 'Vuoi rinegoziare? Offri di più!' : 'Want to renegotiate? Offer more!'}
                </p>
                <p className="text-[10px] text-gray-400 mb-2">
                  {language === 'it' ? 'Richiesta minima' : 'Min. request'}: ${Math.round(rejectionModal.requested_fee || 0).toLocaleString()}
                </p>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    value={renegotiateOffer}
                    onChange={e => setRenegotiateOffer(Number(e.target.value))}
                    className="h-8 text-sm bg-black/30 border-yellow-500/30"
                    data-testid="renegotiate-offer-input"
                  />
                  <Button
                    size="sm"
                    disabled={renegotiating || renegotiateOffer <= 0}
                    className="bg-yellow-500 hover:bg-yellow-400 text-black font-bold whitespace-nowrap"
                    data-testid="renegotiate-btn"
                    onClick={async () => {
                      setRenegotiating(true);
                      try {
                        const res = await api.post(`/cast/renegotiate/${rejectionModal.negotiation_id}`, { new_offer: renegotiateOffer });
                        if (res.data.accepted) {
                          toast.success(res.data.message);
                          setRefusedIds(prev => { const n = new Set(prev); n.delete(rejectionModal.person_id); return n; });
                          if (rejectionModal.onAccept) rejectionModal.onAccept();
                          setRejectionModal(null);
                        } else {
                          setRenegotiateOffer(Math.round(res.data.requested_fee || renegotiateOffer * 1.2));
                          setRejectionModal(prev => ({
                            ...prev,
                            reason: res.data.reason,
                            requested_fee: res.data.requested_fee,
                            can_renegotiate: res.data.can_renegotiate,
                            negotiation_id: res.data.negotiation_id
                          }));
                          toast.error(`${res.data.person_name}: "${res.data.reason}" (${res.data.attempts_left || 0} ${language === 'it' ? 'tentativi rimasti' : 'attempts left'})`);
                        }
                      } catch (e) {
                        toast.error(e.response?.data?.detail || 'Errore rinegoziazione');
                      } finally {
                        setRenegotiating(false);
                      }
                    }}
                  >
                    {renegotiating ? '...' : (language === 'it' ? 'Rinegozia' : 'Renegotiate')}
                  </Button>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      )}

      {/* Film Tier Celebration Popup */}
      {/* Critic Reviews Popup - Shown on film release */}
      {criticReviewsPopup && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4" onClick={() => { setCriticReviewsPopup(null); navigate(`/films/${criticReviewsPopup.filmId}`); }}>
          <motion.div 
            initial={{ scale: 0.5, opacity: 0, y: 50 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            transition={{ type: "spring", damping: 12 }}
            className="bg-[#111] border border-gray-700 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto relative"
            onClick={e => e.stopPropagation()}
            data-testid="critic-reviews-popup"
          >
            {/* Header with tier */}
            <div className={`bg-gradient-to-br ${criticReviewsPopup.tierStyle.bg} p-6 text-center rounded-t-2xl border-b ${criticReviewsPopup.tierStyle.border}`}>
              <motion.div animate={{ scale: [1, 1.15, 1] }} transition={{ duration: 0.6, repeat: 2 }} className="text-5xl mb-2">
                {criticReviewsPopup.tierStyle.emoji}
              </motion.div>
              <h2 className="font-['Bebas_Neue'] text-3xl text-white">{criticReviewsPopup.filmTitle}</h2>
              <p className={`font-['Bebas_Neue'] text-2xl ${criticReviewsPopup.tierStyle.text} mt-1`}>{criticReviewsPopup.tierName}</p>
              <p className="text-green-400 text-lg font-bold mt-2">
                {language === 'it' ? 'Incasso' : 'Opening'}: ${criticReviewsPopup.opening?.toLocaleString()}
              </p>
            </div>
            
            {/* Critic Reviews Section */}
            <div className="p-4">
              <h3 className="font-['Bebas_Neue'] text-xl text-amber-400 mb-3 flex items-center gap-2">
                <Newspaper className="w-5 h-5" /> {language === 'it' ? 'LA CRITICA' : 'CRITICS'}
              </h3>
              
              <div className="space-y-3">
                {criticReviewsPopup.reviews.map((review, idx) => (
                  <motion.div 
                    key={review.id || idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + idx * 0.2 }}
                    className={`rounded-lg p-3 border ${
                      review.sentiment === 'positive' ? 'bg-green-500/10 border-green-500/30' :
                      review.sentiment === 'negative' ? 'bg-red-500/10 border-red-500/30' :
                      'bg-gray-500/10 border-gray-500/30'
                    }`}
                    data-testid={`critic-review-${idx}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white">{review.newspaper}</span>
                        <div className="flex">
                          {[...Array(review.newspaper_prestige || 3)].map((_, i) => (
                            <Star key={i} className="w-2.5 h-2.5 fill-yellow-500 text-yellow-500" />
                          ))}
                        </div>
                      </div>
                      <Badge className={`text-xs ${
                        review.sentiment === 'positive' ? 'bg-green-500/30 text-green-400' :
                        review.sentiment === 'negative' ? 'bg-red-500/30 text-red-400' :
                        'bg-gray-500/30 text-gray-400'
                      }`}>
                        {review.score}/10
                      </Badge>
                    </div>
                    <p className="text-gray-300 text-xs italic">"{review.review}"</p>
                    <p className="text-gray-500 text-[10px] mt-1">- {review.critic_name}</p>
                    
                    {/* Effect indicator */}
                    <div className="flex gap-2 mt-2 text-[10px]">
                      {review.attendance_effect !== 0 && (
                        <span className={review.attendance_effect > 0 ? 'text-green-400' : 'text-red-400'}>
                          {review.attendance_effect > 0 ? '+' : ''}{review.attendance_effect} {language === 'it' ? 'spettatori' : 'viewers'}
                        </span>
                      )}
                      {review.revenue_effect_pct !== 0 && (
                        <span className={review.revenue_effect_pct > 0 ? 'text-green-400' : 'text-red-400'}>
                          {review.revenue_effect_pct > 0 ? '+' : ''}{review.revenue_effect_pct}% {language === 'it' ? 'incassi' : 'revenue'}
                        </span>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
              
              {/* Total Effects Summary */}
              {criticReviewsPopup.effects && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + criticReviewsPopup.reviews.length * 0.2 }}
                  className="mt-4 bg-white/5 rounded-lg p-3 border border-white/10"
                >
                  <p className="text-xs text-gray-400 mb-2 font-semibold">{language === 'it' ? 'Effetto critica totale:' : 'Total critic effect:'}</p>
                  <div className="flex gap-4 text-sm">
                    <span className={`${criticReviewsPopup.effects.attendance_bonus > 0 ? 'text-green-400' : criticReviewsPopup.effects.attendance_bonus < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                      {criticReviewsPopup.effects.attendance_bonus > 0 ? '+' : ''}{criticReviewsPopup.effects.attendance_bonus || 0} {language === 'it' ? 'spettatori' : 'viewers'}
                    </span>
                    <span className={`${criticReviewsPopup.effects.revenue_bonus_pct > 0 ? 'text-green-400' : criticReviewsPopup.effects.revenue_bonus_pct < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                      {criticReviewsPopup.effects.revenue_bonus_pct > 0 ? '+' : ''}{criticReviewsPopup.effects.revenue_bonus_pct || 0}% {language === 'it' ? 'incassi' : 'revenue'}
                    </span>
                  </div>
                </motion.div>
              )}
            </div>
            
            {/* Action Button */}
            <div className="p-4 pt-0">
              <Button 
                className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold text-lg py-5"
                onClick={() => { setCriticReviewsPopup(null); navigate(`/films/${criticReviewsPopup.filmId}`); }}
                data-testid="critic-reviews-go-btn"
              >
                {language === 'it' ? 'Vai al Film' : 'Go to Film'} <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </motion.div>
        </div>
      )}
      
      {/* Dismiss Pre-Engaged Cast Modal */}
      {dismissModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setDismissModal(null)}>
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }} 
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] rounded-xl p-6 max-w-md w-full border border-red-500/30"
            onClick={e => e.stopPropagation()}
          >
            <div className="text-center mb-4">
              <div className="w-16 h-16 mx-auto bg-red-500/20 rounded-full flex items-center justify-center mb-3">
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>
              <h2 className="font-['Bebas_Neue'] text-2xl text-red-400">
                {language === 'it' ? 'Congedare Cast' : 'Dismiss Cast'}
              </h2>
              <p className="text-lg font-semibold mt-2">{dismissModal.cast_name}</p>
            </div>
            
            <div className="bg-black/30 rounded-lg p-4 mb-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">{language === 'it' ? 'Anticipo perso' : 'Lost advance'}:</span>
                <span className="text-red-400 font-bold">${dismissModal.advance_lost?.toLocaleString()}</span>
              </div>
              {dismissModal.additional_penalty > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">{language === 'it' ? 'Penale aggiuntiva' : 'Additional penalty'}:</span>
                  <span className="text-red-400 font-bold">${dismissModal.additional_penalty?.toLocaleString()}</span>
                </div>
              )}
              <div className="border-t border-white/10 pt-2 flex justify-between">
                <span className="text-gray-300 font-semibold">{language === 'it' ? 'Costo totale' : 'Total cost'}:</span>
                <span className="text-red-400 font-bold text-lg">${dismissModal.total_cost?.toLocaleString()}</span>
              </div>
              <p className="text-xs text-gray-500 text-center mt-2">
                {language === 'it' ? `Penale: ${dismissModal.penalty_percent?.toFixed(0)}%` : `Penalty: ${dismissModal.penalty_percent?.toFixed(0)}%`}
              </p>
            </div>
            
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setDismissModal(null)} className="flex-1">
                {language === 'it' ? 'Annulla' : 'Cancel'}
              </Button>
              <Button onClick={confirmDismissal} className="flex-1 bg-red-600 hover:bg-red-700">
                {language === 'it' ? 'Congeda' : 'Dismiss'}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

// ==================== PRE-ENGAGEMENT PAGE ====================

const GENRES_LIST = [
  { id: 'action', name: 'Action', nameIt: 'Azione' },
  { id: 'comedy', name: 'Comedy', nameIt: 'Commedia' },
  { id: 'drama', name: 'Drama', nameIt: 'Drammatico' },
  { id: 'horror', name: 'Horror', nameIt: 'Horror' },
  { id: 'scifi', name: 'Sci-Fi', nameIt: 'Fantascienza' },
  { id: 'thriller', name: 'Thriller', nameIt: 'Thriller' },
  { id: 'romance', name: 'Romance', nameIt: 'Romantico' },
  { id: 'animation', name: 'Animation', nameIt: 'Animazione' },
  { id: 'documentary', name: 'Documentary', nameIt: 'Documentario' },
  { id: 'fantasy', name: 'Fantasy', nameIt: 'Fantasy' },
];


export default FilmWizard;
