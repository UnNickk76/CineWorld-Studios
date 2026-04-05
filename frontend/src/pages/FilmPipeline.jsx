import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { useSWR, useGameStore } from '../contexts/GameStore';
import { TabErrorBoundary, MiniStepBar } from '../components/ErrorBoundary';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  Pencil, ClipboardList, Users, BookOpen, Clapperboard, Play,
  HelpCircle, Star, MapPin, Clock, Check, X, DollarSign,
  Zap, ChevronRight, ChevronDown, ChevronUp, RefreshCw, ThumbsDown, ShoppingCart, Film, TrendingUp, TrendingDown,
  Settings, Sparkles, Wand2, Globe, UserCheck, Minus, Target, Flame,
  Lock, Rocket, Palette, Lightbulb, FileText, Save, ChevronLeft
} from 'lucide-react';

import { ReleaseModeSelector } from '../components/ReleaseModeSelector';
import { FilmProductionCard } from '../components/FilmProductionCard';
import FilmPopup, { FilmInlineView } from '../components/FilmPopup';
import { DraftsSection } from '../components/DraftsSection';
import LaPremiereSection from '../components/LaPremiereSection';
import '../styles/cinematic-pipeline.css';

// Haptic feedback utility
const haptic = (pattern = [10]) => { try { navigator?.vibrate?.(pattern); } catch {} };

const TABS = [
  { id: 'creation', icon: Pencil, label: 'Creazione', desc: 'Crea una nuova proposta: titolo, genere, sinossi e location' },
  { id: 'proposals', icon: ClipboardList, label: 'Proposte', desc: 'Film proposti con pre-valutazione IMDb. Scarta o prosegui al casting' },
  { id: 'casting', icon: Users, label: 'Casting', desc: 'Gli agenti propongono candidati per il cast del tuo film' },
  { id: 'screenplay', icon: BookOpen, label: 'Sceneggiatura', desc: 'Sceneggiatura completa e creazione della locandina (Fase 2)' },
  { id: 'pre_production', icon: Clapperboard, label: 'Pre-Produzione', desc: 'Film pronti per le riprese. Rimasterizza o lancia il Ciak! (Fase 2)' },
  { id: 'shooting', icon: Play, label: 'Ciak! Si Gira!', desc: 'Film in fase di ripresa. Velocizza o attendi il completamento (Fase 2)' },
];

const PIPELINE_STEPS = [
  { id: 'idea', label: 'Idea', icon: Lightbulb, tab: 'creation', color: 'yellow' },
  { id: 'trama', label: 'Trama', icon: FileText, tab: 'creation', color: 'yellow' },
  { id: 'location', label: 'Location', icon: MapPin, tab: 'creation', color: 'yellow' },
  { id: 'poster', label: 'Poster', icon: Palette, tab: 'proposals', color: 'purple' },
  { id: 'coming_soon', label: 'Hype', icon: Flame, tab: 'proposals', color: 'orange' },
  { id: 'casting', label: 'Casting', icon: Users, tab: 'casting', color: 'cyan' },
  { id: 'script', label: 'Script', icon: BookOpen, tab: 'screenplay', color: 'green' },
  { id: 'production', label: 'Produzione', icon: Clapperboard, tab: 'pre_production', color: 'blue' },
  { id: 'release', label: 'Uscita', icon: Rocket, tab: 'shooting', color: 'emerald' },
];

// ─── Pipeline Step Bar Component (Animated) ───
const PipelineStepBar = ({ activeTab, counts, onTabChange }) => {
  const scrollRef = React.useRef(null);
  const hasComingSoon = (counts.coming_soon || 0) > 0;
  
  const getStepState = (step) => {
    const tabOrder = ['creation', 'proposals', 'casting', 'screenplay', 'pre_production', 'shooting'];
    const activeIdx = tabOrder.indexOf(activeTab);
    const stepIdx = tabOrder.indexOf(step.tab);
    
    if (step.tab === activeTab) return 'current';
    if (stepIdx < activeIdx) return 'completed';
    
    if (hasComingSoon && ['casting', 'script', 'production', 'release'].includes(step.id)) {
      const tabCountMap = { casting: counts.casting, script: counts.screenplay, production: counts.pre_production, release: counts.shooting };
      if (!tabCountMap[step.id]) return 'locked';
    }
    
    return 'future';
  };

  React.useEffect(() => {
    if (scrollRef.current) {
      const el = scrollRef.current.querySelector('[data-step-active="true"]');
      if (el) el.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
  }, [activeTab]);

  const glowColors = {
    yellow: 'rgba(234,179,8,0.5)',
    purple: 'rgba(168,85,247,0.5)',
    orange: 'rgba(249,115,22,0.5)',
    cyan: 'rgba(6,182,212,0.5)',
    green: 'rgba(34,197,94,0.5)',
    blue: 'rgba(59,130,246,0.5)',
    emerald: 'rgba(16,185,129,0.5)',
  };

  const colorStyles = {
    yellow: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', text: 'text-yellow-400', iconBg: 'bg-yellow-500/30' },
    purple: { bg: 'bg-purple-500/20', border: 'border-purple-500/50', text: 'text-purple-400', iconBg: 'bg-purple-500/30' },
    orange: { bg: 'bg-orange-500/20', border: 'border-orange-500/50', text: 'text-orange-400', iconBg: 'bg-orange-500/30' },
    cyan: { bg: 'bg-cyan-500/20', border: 'border-cyan-500/50', text: 'text-cyan-400', iconBg: 'bg-cyan-500/30' },
    green: { bg: 'bg-green-500/20', border: 'border-green-500/50', text: 'text-green-400', iconBg: 'bg-green-500/30' },
    blue: { bg: 'bg-blue-500/20', border: 'border-blue-500/50', text: 'text-blue-400', iconBg: 'bg-blue-500/30' },
    emerald: { bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', text: 'text-emerald-400', iconBg: 'bg-emerald-500/30' },
  };

  return (
    <div className="mb-3 relative" data-testid="pipeline-step-bar">
      <div ref={scrollRef} className="flex items-center gap-0 overflow-x-auto pb-1.5 px-0.5 no-scrollbar">
        {PIPELINE_STEPS.map((step, i) => {
          const state = getStepState(step);
          const Icon = step.icon;
          const cs = colorStyles[step.color];
          const isLocked = state === 'locked';
          const isCurrent = state === 'current';
          const isCompleted = state === 'completed';
          const isFuture = state === 'future';
          const isComingSoonActive = step.id === 'coming_soon' && hasComingSoon;

          return (
            <React.Fragment key={step.id}>
              {/* Connector line */}
              {i > 0 && (
                <div className={`flex-shrink-0 w-4 h-[2px] rounded-full ${
                  isCompleted || isCurrent
                    ? 'connector-active'
                    : 'bg-gray-800'
                }`} />
              )}
              
              {/* Step button */}
              <button
                onClick={() => { if (!isLocked) { haptic([15]); onTabChange(step.tab); } }}
                data-step-active={isCurrent ? 'true' : 'false'}
                data-testid={`step-${step.id}`}
                disabled={isLocked}
                style={isCurrent ? { '--step-glow-color': glowColors[step.color] } : {}}
                className={`flex-shrink-0 flex flex-col items-center gap-0.5 p-1 rounded-xl transition-all min-w-[44px] relative ${
                  isCurrent
                    ? `${cs.bg} border ${cs.border} step-current`
                    : isCompleted
                      ? 'step-completed'
                      : isLocked
                        ? 'step-locked cursor-not-allowed'
                        : isFuture
                          ? 'opacity-40'
                          : ''
                }`}
              >
                {/* Icon container */}
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
                  isCurrent
                    ? `${cs.iconBg}`
                    : isCompleted
                      ? 'bg-green-500/20'
                      : isLocked
                        ? 'bg-gray-900'
                        : 'bg-gray-800/50'
                }`}>
                  {isLocked ? (
                    <Lock className="w-3 h-3 text-gray-700" />
                  ) : isCompleted ? (
                    <Check className="w-3.5 h-3.5 text-green-400 step-check-icon" />
                  ) : isComingSoonActive ? (
                    <Icon className={`w-3.5 h-3.5 ${cs.text} cs-icon-spin`} />
                  ) : (
                    <Icon className={`w-3.5 h-3.5 ${isCurrent ? cs.text : 'text-gray-600'}`} />
                  )}
                </div>
                
                {/* Label */}
                <span className={`text-[7px] font-semibold leading-none tracking-wide ${
                  isCurrent ? cs.text
                  : isCompleted ? 'text-green-400/80'
                  : isLocked ? 'text-gray-800'
                  : 'text-gray-600'
                }`}>
                  {step.label}
                </span>

                {/* Coming Soon countdown indicator */}
                {isComingSoonActive && (
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-full">
                    <div className="h-[2px] rounded-full cs-progress-bar mx-1" />
                  </div>
                )}
              </button>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

// ============ CREATION TAB with AUTOSAVE ============
const CreationTab = ({ api, refreshUser, refreshCounts, cachedGet }) => {
  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('');
  const [selectedSubgenres, setSelectedSubgenres] = useState([]);
  const [preScreenplay, setPreScreenplay] = useState('');
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [locFilter, setLocFilter] = useState('all');
  const [genres, setGenres] = useState({});
  const [locations, setLocations] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState(0); // 0=release mode, 1=title/genre, 2=screenplay, 3=location
  const [releaseType, setReleaseType] = useState(null);
  const [myScreenplays, setMyScreenplays] = useState([]);
  const [selectedScreenplay, setSelectedScreenplay] = useState(null);
  const [draftId, setDraftId] = useState(null);
  const [showDraftRecovery, setShowDraftRecovery] = useState(false);
  const [recoveredDraft, setRecoveredDraft] = useState(null);
  const [autoSaving, setAutoSaving] = useState(false);
  const autoSaveTimerRef = useRef(null);

  useEffect(() => {
    cachedGet('/genres').then(r => setGenres(r.data || {})).catch(() => {});
    cachedGet('/locations').then(r => setLocations(r.data || [])).catch(() => {});
    api.get('/agency/my-screenplays').then(r => setMyScreenplays(r.data.screenplays || [])).catch(() => {});
    // Check for existing draft
    api.get('/film-pipeline/draft').then(r => {
      if (r.data.has_draft && r.data.draft) {
        setRecoveredDraft(r.data.draft);
        setShowDraftRecovery(true);
      }
    }).catch(() => {});
  }, [cachedGet, api]);

  // Autosave every 4 seconds when user is actively editing (step >= 1)
  useEffect(() => {
    if (step < 1) return;
    if (autoSaveTimerRef.current) clearInterval(autoSaveTimerRef.current);
    autoSaveTimerRef.current = setInterval(() => {
      if (title.trim() || genre || preScreenplay.trim()) {
        setAutoSaving(true);
        api.post('/film-pipeline/draft', {
          draft_id: draftId || undefined,
          step, release_type: releaseType, title, genre,
          subgenres: selectedSubgenres, pre_screenplay: preScreenplay,
          locations: selectedLocations,
          purchased_screenplay_id: selectedScreenplay?.id
        }).then(r => {
          if (r.data.draft_id && !draftId) setDraftId(r.data.draft_id);
          setTimeout(() => setAutoSaving(false), 500);
        }).catch(() => setAutoSaving(false));
      }
    }, 4000);
    return () => { if (autoSaveTimerRef.current) clearInterval(autoSaveTimerRef.current); };
  }, [step, title, genre, selectedSubgenres, preScreenplay, selectedLocations, releaseType, draftId, api, selectedScreenplay]);

  // Save draft immediately on step change
  const saveDraftNow = useCallback(async (nextStep) => {
    if (!title.trim() && !genre && !preScreenplay.trim()) return;
    try {
      const r = await api.post('/film-pipeline/draft', {
        draft_id: draftId || undefined,
        step: nextStep, release_type: releaseType, title, genre,
        subgenres: selectedSubgenres, pre_screenplay: preScreenplay,
        locations: selectedLocations,
        purchased_screenplay_id: selectedScreenplay?.id
      });
      if (r.data.draft_id && !draftId) setDraftId(r.data.draft_id);
    } catch {}
  }, [api, draftId, title, genre, selectedSubgenres, preScreenplay, selectedLocations, releaseType, selectedScreenplay]);

  const recoverDraft = () => {
    if (!recoveredDraft) return;
    setDraftId(recoveredDraft.id);
    setStep(recoveredDraft.step || 1);
    setReleaseType(recoveredDraft.release_type);
    setTitle(recoveredDraft.title || '');
    setGenre(recoveredDraft.genre || '');
    setSelectedSubgenres(recoveredDraft.subgenres || []);
    setPreScreenplay(recoveredDraft.pre_screenplay || '');
    setSelectedLocations(recoveredDraft.locations || []);
    setShowDraftRecovery(false);
    toast.success('Bozza recuperata!');
  };

  const discardDraft = () => {
    if (recoveredDraft?.id) {
      api.delete(`/film-pipeline/draft/${recoveredDraft.id}`).catch(() => {});
    }
    setShowDraftRecovery(false);
    setRecoveredDraft(null);
  };

  const goToStep = (nextStep) => {
    saveDraftNow(nextStep);
    setStep(nextStep);
  };

  const toggleSubgenre = (sg) => {
    if (selectedSubgenres.includes(sg)) {
      setSelectedSubgenres(selectedSubgenres.filter(s => s !== sg));
    } else if (selectedSubgenres.length < 3) {
      setSelectedSubgenres([...selectedSubgenres, sg]);
    }
  };

  const toggleLocation = (name) => {
    if (selectedLocations.includes(name)) {
      setSelectedLocations(selectedLocations.filter(l => l !== name));
    } else {
      setSelectedLocations([...selectedLocations, name]);
    }
  };

  const handleSubmit = async () => {
    if (!title.trim() || !genre || selectedSubgenres.length === 0 || preScreenplay.length < 100 || selectedLocations.length === 0) {
      toast.error('Compila tutti i campi. Seleziona almeno 1 sottogenere e 1 location.');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        title, genre, subgenres: selectedSubgenres, pre_screenplay: preScreenplay, locations: selectedLocations,
        release_type: releaseType || 'immediate'
      };
      if (selectedScreenplay) payload.purchased_screenplay_id = selectedScreenplay.id;
      const res = await api.post('/film-pipeline/create', payload);
      toast.success(res.data.message);
      setTitle(''); setGenre(''); setSelectedSubgenres([]); setPreScreenplay(''); setSelectedLocations([]); setStep(0);
      setReleaseType(null);
      setSelectedScreenplay(null);
      setDraftId(null);
      setMyScreenplays(prev => prev.filter(s => s.id !== selectedScreenplay?.id));
      refreshUser(); refreshCounts();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setSubmitting(false);
    }
  };

  const subgenresList = genres[genre]?.subgenres || [];

  const CATEGORY_LABELS = { studios: 'Studi', cities: 'Citta', nature: 'Natura', historical: 'Storici' };
  const categories = ['all', ...new Set(locations.map(l => l.category))];
  const filteredLocations = locFilter === 'all' ? locations : locations.filter(l => l.category === locFilter);

  return (
    <div className="space-y-4">
      {/* Draft Recovery Popup */}
      {showDraftRecovery && recoveredDraft && (
        <Card className="bg-[#1A1A1B] border-purple-500/30 border-2" data-testid="draft-recovery-popup">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-2">
              <Save className="w-4 h-4 text-purple-400" />
              <p className="text-xs font-bold text-purple-300">Bozza trovata!</p>
            </div>
            <p className="text-[10px] text-gray-400 mb-2">
              Hai un film in bozza: <span className="text-white font-medium">&quot;{recoveredDraft.title || 'Senza Titolo'}&quot;</span>
              {recoveredDraft.genre && <> ({recoveredDraft.genre})</>}
            </p>
            <div className="flex gap-2">
              <Button className="flex-1 bg-purple-700 hover:bg-purple-600 text-xs" onClick={recoverDraft} data-testid="draft-recover-btn">
                Continua il film
              </Button>
              <Button variant="outline" className="border-gray-700 text-xs text-gray-400" onClick={discardDraft} data-testid="draft-discard-btn">
                Scarta
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Autosave indicator */}
      {autoSaving && step >= 1 && (
        <div className="flex items-center justify-center gap-1 text-[9px] text-gray-500">
          <Save className="w-2.5 h-2.5 animate-pulse" /> Salvataggio automatico...
        </div>
      )}

      {/* Step indicator */}
      <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
        {['Titolo & Genere', 'Pre-Sceneggiatura', 'Location'].map((s, i) => (
          <React.Fragment key={i}>
            {i > 0 && <ChevronRight className="w-3 h-3" />}
            <span className={`px-2 py-0.5 rounded ${step === i + 1 ? 'bg-yellow-500/20 text-yellow-400 font-medium' : 'text-gray-600'}`}>{s}</span>
          </React.Fragment>
        ))}
      </div>

      {step === 0 && (
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardContent className="p-4">
            <ReleaseModeSelector
              selected={releaseType}
              onSelect={(mode) => { setReleaseType(mode); goToStep(1); }}
              onContinue={() => { if (releaseType) goToStep(1); }}
            />
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2"><Film className="w-4 h-4 text-yellow-400" />Titolo & Genere</CardTitle>
              {releaseType && (
                <button onClick={() => setStep(0)} className="flex items-center gap-1 text-[9px] text-gray-500 hover:text-yellow-400 transition-colors" data-testid="film-change-release-mode">
                  {releaseType === 'coming_soon' ? <Clock className="w-3 h-3 text-cyan-400" /> : <Zap className="w-3 h-3 text-yellow-400" />}
                  {releaseType === 'coming_soon' ? 'Coming Soon' : 'Immediato'}
                </button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Purchased screenplay selector */}
            {myScreenplays.length > 0 && (
              <div className="p-2.5 rounded border border-emerald-800/30 bg-emerald-500/5">
                <p className="text-[10px] text-emerald-400 font-semibold mb-1.5 flex items-center gap-1">
                  <BookOpen className="w-3 h-3" /> Hai {myScreenplays.length} sceneggiatura/e pronta/e
                </p>
                <div className="space-y-1.5">
                  {myScreenplays.map(sp => (
                    <button key={sp.id} onClick={() => {
                      if (selectedScreenplay?.id === sp.id) {
                        setSelectedScreenplay(null);
                        setTitle(''); setGenre(''); setSelectedSubgenres([]); setPreScreenplay('');
                      } else {
                        setSelectedScreenplay(sp);
                        setTitle(sp.title);
                        setGenre(sp.genre);
                        setSelectedSubgenres([]);
                        setPreScreenplay(sp.synopsis || '');
                      }
                    }}
                      className={`w-full text-left p-2 rounded text-xs transition-all ${selectedScreenplay?.id === sp.id ? 'bg-emerald-500/20 border border-emerald-500/50' : 'bg-black/20 border border-gray-800 hover:border-emerald-800/50'}`}
                      data-testid={`use-screenplay-${sp.id}`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-semibold text-white">{sp.title}</span>
                          <span className="text-gray-500 ml-1.5">di {sp.writer_name}</span>
                        </div>
                        <Badge className={`text-[7px] h-3.5 ${sp.quality >= 70 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>Q{sp.quality}</Badge>
                      </div>
                      <p className="text-[9px] text-gray-500 mt-0.5">{sp.genre_name} {selectedScreenplay?.id === sp.id ? '- Selezionata' : '- Clicca per usare'}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Titolo del Film</label>
              <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Il titolo del tuo capolavoro..."
                className="bg-black/30 border-gray-700 text-white" maxLength={80} data-testid="film-title-input" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Genere</label>
              <Select value={genre} onValueChange={v => { setGenre(v); setSelectedSubgenres([]); }}>
                <SelectTrigger className="bg-black/30 border-gray-700 text-white" data-testid="genre-select">
                  <SelectValue placeholder="Seleziona un genere..." />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(genres).map(([key, val]) => (
                    <SelectItem key={key} value={key} data-testid={`genre-${key}`}>{val.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {genre && subgenresList.length > 0 && (
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Sottogenere (max 3)</label>
                <div className="flex flex-wrap gap-1.5">
                  {subgenresList.map(sg => (
                    <Badge key={sg} variant={selectedSubgenres.includes(sg) ? "default" : "outline"}
                      className={`cursor-pointer text-[10px] px-2 py-1 transition-all ${selectedSubgenres.includes(sg) ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50 hover:bg-cyan-500/30' : 'border-gray-700 text-gray-400 hover:border-gray-500'}`}
                      onClick={() => toggleSubgenre(sg)}
                      data-testid={`subgenre-${sg}`}>{sg}</Badge>
                  ))}
                </div>
                {selectedSubgenres.length > 0 && (
                  <p className="text-[10px] text-cyan-400 mt-1">{selectedSubgenres.length}/3 selezionati</p>
                )}
              </div>
            )}
            <Button disabled={!title.trim() || !genre || selectedSubgenres.length === 0} onClick={() => goToStep(2)}
              className="w-full bg-yellow-600 hover:bg-yellow-700" data-testid="step1-next">
              Avanti <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><BookOpen className="w-4 h-4 text-cyan-400" />Pre-Sceneggiatura</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="p-2 bg-black/30 rounded border border-gray-800 text-[10px] text-gray-500">
              <span className="text-yellow-400">{title}</span> &bull; {genres[genre]?.name} &bull; {selectedSubgenres.join(', ')}
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Scrivi la sinossi del tuo film (100-500 caratteri)</label>
              <Textarea value={preScreenplay} onChange={e => setPreScreenplay(e.target.value.slice(0, 500))}
                placeholder="Racconta brevemente la trama del tuo film... La tua creativita' influenzera' la valutazione!"
                className="bg-black/30 border-gray-700 text-white min-h-[120px]" data-testid="pre-screenplay-input" />
              <div className="flex justify-between mt-1">
                <span className={`text-[10px] ${preScreenplay.length < 100 ? 'text-red-400' : preScreenplay.length >= 400 ? 'text-green-400' : 'text-yellow-400'}`}>
                  {preScreenplay.length}/500 {preScreenplay.length < 100 ? '(minimo 100)' : preScreenplay.length >= 400 ? 'Eccellente!' : ''}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => goToStep(1)} className="border-gray-700 text-gray-400">Indietro</Button>
              <Button disabled={preScreenplay.length < 100} onClick={() => goToStep(3)}
                className="flex-1 bg-cyan-600 hover:bg-cyan-700" data-testid="step2-next">
                Avanti <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><MapPin className="w-4 h-4 text-green-400" />Location</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="p-2 bg-black/30 rounded border border-gray-800 text-[10px] text-gray-500">
              <span className="text-yellow-400">{title}</span> &bull; {genres[genre]?.name} &bull; {selectedSubgenres.join(', ')}
            </div>
            {/* Category filter */}
            <div className="flex flex-wrap gap-1">
              {categories.map(cat => (
                <button key={cat} onClick={() => setLocFilter(cat)}
                  className={`px-2 py-1 rounded text-[10px] border transition-all ${locFilter === cat ? 'border-green-500 bg-green-500/10 text-green-400' : 'border-gray-700 text-gray-500 hover:border-gray-600'}`}
                  data-testid={`loc-filter-${cat}`}>
                  {cat === 'all' ? 'Tutti' : CATEGORY_LABELS[cat] || cat}
                </button>
              ))}
            </div>
            {selectedLocations.length > 0 && (
              <p className="text-[10px] text-green-400">{selectedLocations.length} location selezionate</p>
            )}
            <div className="grid grid-cols-2 gap-1.5 max-h-[300px] overflow-y-auto pr-1">
              {filteredLocations.map(loc => (
                <button key={loc.name} onClick={() => toggleLocation(loc.name)}
                  className={`p-2 rounded text-left border transition-all ${selectedLocations.includes(loc.name) ? 'border-green-500 bg-green-500/10' : 'border-gray-700 hover:border-gray-600'}`}
                  data-testid={`loc-${loc.name.replace(/\s/g, '-')}`}>
                  <p className="text-xs font-medium text-gray-200 truncate">{loc.name}</p>
                  <p className="text-[9px] text-gray-500">${loc.cost_per_day?.toLocaleString()}/giorno &bull; {CATEGORY_LABELS[loc.category] || loc.category}</p>
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => goToStep(2)} className="border-gray-700 text-gray-400">Indietro</Button>
              <Button disabled={selectedLocations.length === 0 || submitting} onClick={handleSubmit}
                className="flex-1 bg-green-600 hover:bg-green-700" data-testid="submit-proposal">
                {submitting ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : <Star className="w-4 h-4 mr-1" />}
                Proponi Film (1 CP)
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// ============ PROPOSALS TAB ============
const ProposalsTab = ({ api, refreshUser, refreshCounts }) => {
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [posterLoading, setPosterLoading] = useState(null);
  const [posterMode, setPosterMode] = useState({});
  const [posterPrompt, setPosterPrompt] = useState({});
  const [posterStyle, setPosterStyle] = useState({});
  const [actionLoading, setActionLoading] = useState(null);
  const [countdowns, setCountdowns] = useState({});
  const [csTier, setCsTier] = useState({});
  const [csHours, setCsHours] = useState({});

  const fetch = useCallback(async () => {
    try {
      const res = await api.get('/film-pipeline/proposals');
      const safe = (res.data.proposals || []).filter(p => p && p.id && p.title);
      setProposals(safe);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); }, [fetch]);

  // Countdown updater - also calculate immediately on proposals change
  useEffect(() => {
    const calcCountdowns = () => {
      const now = new Date();
      const cd = {};
      proposals.forEach(p => {
        if (p.status === 'coming_soon' && p.scheduled_release_at) {
          const diff = new Date(p.scheduled_release_at) - now;
          if (diff > 0) {
            const h = Math.floor(diff / 3600000);
            const m = Math.floor((diff % 3600000) / 60000);
            cd[p.id] = `${h}h ${m}m`;
          } else {
            cd[p.id] = null; // Timer expired
          }
        }
      });
      setCountdowns(cd);
    };
    calcCountdowns(); // Calculate immediately
    const interval = setInterval(calcCountdowns, 10000);
    return () => clearInterval(interval);
  }, [proposals]);

  const discard = async (id) => {
    try {
      const res = await api.post(`/film-pipeline/${id}/discard`);
      toast.success(res.data.message);
      fetch(); refreshCounts();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const generatePoster = async (filmId) => {
    setPosterLoading(filmId);
    try {
      const pMode = posterMode[filmId] || 'ai_auto';
      const body = { mode: pMode };
      if (pMode === 'ai_custom') body.custom_prompt = posterPrompt[filmId] || '';
      if (pMode === 'classic') body.classic_style = posterStyle[filmId] || 'drama';
      const res = await api.post(`/film-pipeline/${filmId}/generate-poster`, body, { timeout: 120000 });
      toast.success(res.data.message || 'Locandina generata!');
      fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore generazione locandina'); }
    finally { setPosterLoading(null); }
  };

  const launchComingSoon = async (id) => {
    const tier = csTier[id] || 'short';
    const hours = csHours[id] || (tier === 'short' ? 4 : tier === 'medium' ? 12 : 30);
    setActionLoading(`cs-${id}`);
    try {
      const res = await api.post(`/film-pipeline/${id}/launch-coming-soon`, { tier, hours });
      const d = res.data;
      toast.success(`${d.message} (${d.final_hours.toFixed(1)}h)`);
      fetch(); refreshCounts();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const advance = async (id) => {
    setActionLoading(`adv-${id}`);
    try {
      const res = await api.post(`/film-pipeline/${id}/advance-to-casting`);
      toast.success(res.data.message);
      fetch(); refreshUser(); refreshCounts();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const POSTER_MODES = [
    { id: 'ai_auto', label: 'AI Auto' },
    { id: 'ai_custom', label: 'AI + Prompt' },
    { id: 'classic', label: 'Stile Classico' }
  ];
  const CLASSIC_STYLES = [
    { id: 'noir', label: 'Noir' }, { id: 'vintage', label: 'Vintage' },
    { id: 'action', label: 'Action' }, { id: 'romance', label: 'Romance' },
    { id: 'horror', label: 'Horror' }, { id: 'scifi', label: 'Sci-Fi' },
    { id: 'comedy', label: 'Commedia' }, { id: 'drama', label: 'Dramma' }
  ];

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;
  if (!proposals.length) return <div className="text-center py-12 text-gray-500"><ClipboardList className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessuna proposta. Crea un film nella sezione Creazione!</p></div>;

  // Determine step for each proposal
  const getStep = (p) => {
    if (p.status === 'ready_for_casting') return 'casting_ready';
    if (p.status === 'coming_soon') {
      // Check actual time, not countdown state (which may be empty on first render)
      if (p.scheduled_release_at) {
        const diff = new Date(p.scheduled_release_at) - new Date();
        return diff > 0 ? 'coming_soon_active' : 'casting_ready';
      }
      return 'coming_soon_active'; // Default to active if no release date yet
    }
    if (!p.poster_url) return 'needs_poster';
    return 'needs_coming_soon';
  };

  return (
    <div className="space-y-3">
      {proposals.map(p => {
        const step = getStep(p);
        return (
        <Card key={p.id} className="bg-[#1A1A1B] border-gray-800 film-card-hover" data-testid={`proposal-${p.id}`}>
          <CardContent className="p-3">
            {/* Mini Step Bar */}
            <MiniStepBar status={p.status} />
            {/* Header */}
            <div className="flex items-start gap-3 mb-2 mt-2">
              {p.poster_url ? (
                <img src={p.poster_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${p.poster_url}` : p.poster_url}
                  alt="" className="w-14 h-20 object-cover rounded flex-shrink-0" />
              ) : (
                <div className="w-14 h-20 rounded bg-gray-800/50 flex items-center justify-center flex-shrink-0">
                  <Film className="w-5 h-5 text-gray-600" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-sm truncate">{p.title}</h3>
                <p className="text-[9px] text-gray-500">{p.genre} &bull; {p.subgenre} &bull; {p.location?.name}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <Star className="w-3 h-3 text-yellow-400" />
                  <span className={`text-sm font-bold ${p.pre_imdb_score >= 7 ? 'text-green-400' : p.pre_imdb_score >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {p.pre_imdb_score}
                  </span>
                  <span className="text-[8px] text-gray-600 ml-0.5">Pre-IMDb</span>
                </div>
                <p className="text-[9px] text-gray-500 mt-0.5 line-clamp-1 italic">"{p.pre_screenplay}"</p>
              </div>
            </div>

            {/* Step indicator */}
            <div className="flex items-center gap-1 mb-2">
              <div className={`h-1 flex-1 rounded-full ${step === 'needs_poster' ? 'bg-purple-500' : 'bg-purple-500/30'}`} />
              <div className={`h-1 flex-1 rounded-full ${step === 'needs_coming_soon' ? 'bg-cyan-500' : step === 'coming_soon_active' || step === 'casting_ready' ? 'bg-cyan-500/30' : 'bg-gray-700'}`} />
              <div className={`h-1 flex-1 rounded-full ${step === 'coming_soon_active' ? 'bg-orange-500 animate-pulse' : step === 'casting_ready' ? 'bg-green-500' : 'bg-gray-700'}`} />
            </div>

            {/* Step: needs poster */}
            {step === 'needs_poster' && (
              <div className="space-y-2 p-2 rounded-lg border border-purple-500/20 bg-purple-500/5" data-testid={`poster-step-${p.id}`}>
                <p className="text-[10px] font-bold text-purple-400">Step 1: Genera Locandina</p>
                <div className="flex gap-1">
                  {POSTER_MODES.map(opt => (
                    <button key={opt.id} onClick={() => setPosterMode(m => ({...m, [p.id]: opt.id}))}
                      className={`flex-1 p-1.5 rounded text-[9px] text-center border transition-all ${(posterMode[p.id] || 'ai_auto') === opt.id ? 'border-purple-500 bg-purple-500/10 text-purple-300' : 'border-gray-700 text-gray-500'}`}>
                      {opt.label}
                    </button>
                  ))}
                </div>
                {(posterMode[p.id] || 'ai_auto') === 'ai_custom' && (
                  <input type="text" placeholder="Descrivi la locandina..."
                    value={posterPrompt[p.id] || ''} onChange={e => setPosterPrompt(v => ({...v, [p.id]: e.target.value}))}
                    className="w-full p-1.5 bg-black/30 border border-gray-700 rounded text-[10px] text-white" />
                )}
                {(posterMode[p.id] || 'ai_auto') === 'classic' && (
                  <div className="grid grid-cols-4 gap-1">
                    {CLASSIC_STYLES.map(s => (
                      <button key={s.id} onClick={() => setPosterStyle(v => ({...v, [p.id]: s.id}))}
                        className={`p-1 rounded text-[8px] text-center border transition-all ${(posterStyle[p.id] || 'drama') === s.id ? 'border-purple-500 bg-purple-500/10' : 'border-gray-700'}`}>
                        {s.label}
                      </button>
                    ))}
                  </div>
                )}
                <Button size="sm" className="w-full bg-purple-700 hover:bg-purple-600 text-[10px]"
                  onClick={() => generatePoster(p.id)} disabled={posterLoading === p.id}
                  data-testid={`gen-poster-${p.id}`}>
                  {posterLoading === p.id ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Sparkles className="w-3 h-3 mr-1" />}
                  Genera Locandina
                </Button>
              </div>
            )}

            {/* Step: needs coming soon - DURATION SELECTOR */}
            {step === 'needs_coming_soon' && (() => {
              const tier = csTier[p.id] || 'short';
              const TIERS = [
                { id: 'short', label: 'Breve', range: '2-6h', min: 2, max: 6, icon: Zap, color: 'yellow', desc: 'Meno rischi, meno hype', steps: [2, 3, 4, 5, 6] },
                { id: 'medium', label: 'Medio', range: '6-18h', min: 6, max: 18, icon: Film, color: 'cyan', desc: 'Equilibrio rischio/hype', steps: [6, 8, 10, 12, 15, 18] },
                { id: 'long', label: 'Lungo', range: '18-48h', min: 18, max: 48, icon: Flame, color: 'orange', desc: 'Massimo hype, massimo rischio', steps: [18, 24, 30, 36, 42, 48] },
              ];
              const activeTier = TIERS.find(t => t.id === tier);
              const hours = csHours[p.id] || activeTier.steps[Math.floor(activeTier.steps.length / 2)];
              return (
              <div className="space-y-2.5" data-testid={`cs-step-${p.id}`}>
                <p className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Durata Coming Soon</p>
                <div className="grid grid-cols-3 gap-1.5">
                  {TIERS.map(t => {
                    const TIcon = t.icon;
                    const active = tier === t.id;
                    return (
                    <button key={t.id} onClick={() => { setCsTier(s => ({...s, [p.id]: t.id})); setCsHours(s => ({...s, [p.id]: t.steps[Math.floor(t.steps.length / 2)]})); }}
                      className={`p-2 rounded-lg border text-center transition-all ${active ? `border-${t.color}-500/60 bg-${t.color}-500/10` : 'border-gray-700/60 hover:border-gray-600'}`}
                      data-testid={`tier-${t.id}-${p.id}`}>
                      <TIcon className={`w-4 h-4 mx-auto mb-0.5 ${active ? `text-${t.color}-400` : 'text-gray-600'}`} />
                      <p className={`text-[10px] font-bold ${active ? 'text-white' : 'text-gray-500'}`}>{t.label}</p>
                      <p className="text-[8px] text-gray-600">{t.range}</p>
                    </button>
                    );
                  })}
                </div>
                {/* Steps selector */}
                <div className="flex gap-1 items-center">
                  {activeTier.steps.map(h => (
                    <button key={h} onClick={() => setCsHours(s => ({...s, [p.id]: h}))}
                      className={`flex-1 py-1 rounded text-[9px] font-medium border transition-all ${hours === h ? 'border-cyan-500 bg-cyan-500/15 text-cyan-400' : 'border-gray-700 text-gray-500'}`}
                      data-testid={`hours-${h}-${p.id}`}>
                      {h}h
                    </button>
                  ))}
                </div>
                <div className="text-[8px] text-gray-600 space-y-0.5">
                  <p>{tier === 'short' ? 'Meno tempo = meno eventi e meno rischi' : tier === 'medium' ? 'Equilibrio tra hype e rischio eventi' : 'Massimo hype possibile ma piu\' eventi negativi'}</p>
                  <p className="text-gray-700">Velocizzazione max: {tier === 'short' ? '20%' : tier === 'medium' ? '40%' : '60%'}</p>
                </div>
                <Button size="sm" className="w-full bg-cyan-700 hover:bg-cyan-600 text-[10px]"
                  onClick={() => launchComingSoon(p.id)} disabled={actionLoading === `cs-${p.id}`}
                  data-testid={`launch-cs-${p.id}`}>
                  {actionLoading === `cs-${p.id}` ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
                  Lancia Coming Soon ({hours}h)
                </Button>
              </div>
              );
            })()}

            {/* Step: coming soon active */}
            {step === 'coming_soon_active' && (
              <div className="p-2 rounded-lg border border-orange-500/20 bg-orange-500/5 space-y-2" data-testid={`cs-active-${p.id}`}>
                <div className="flex items-center justify-center gap-1.5">
                  <Flame className="w-3.5 h-3.5 text-orange-400 animate-pulse" />
                  <span className="text-[10px] font-bold text-orange-400">Coming Soon attivo</span>
                </div>
                <div className="flex items-center justify-center gap-1">
                  <Clock className="w-3 h-3 text-cyan-400" />
                  <span className="text-xs font-bold text-cyan-400">{countdowns[p.id] || '...'}</span>
                </div>
                {p.hype_score > 0 && (
                  <div className="flex items-center justify-center gap-1">
                    <Flame className="w-3 h-3 text-orange-400" />
                    <span className="text-[10px] text-orange-400">Hype: {p.hype_score}</span>
                  </div>
                )}
                {/* Speedup Tier Buttons */}
                <div className="pt-1 border-t border-orange-500/10">
                  <p className="text-[8px] text-gray-500 text-center mb-1.5">Velocizza il timer</p>
                  <div className="grid grid-cols-3 gap-1">
                    {[
                      { pct: 25, cost: 10, label: '-25%', color: 'yellow' },
                      { pct: 75, cost: 20, label: '-75%', color: 'orange' },
                      { pct: 100, cost: 30, label: 'ISTANTANEO', color: 'red' },
                    ].map(tier => {
                      const isFree = (p.free_speedups || 0) > 0;
                      return (
                        <button
                          key={tier.pct}
                          className={`p-1.5 rounded-lg border text-center transition-all hover:scale-[1.02] active:scale-95 ${
                            tier.color === 'yellow' ? 'border-yellow-500/30 bg-yellow-500/5 hover:bg-yellow-500/15' :
                            tier.color === 'orange' ? 'border-orange-500/30 bg-orange-500/5 hover:bg-orange-500/15' :
                            'border-red-500/30 bg-red-500/5 hover:bg-red-500/15'
                          }`}
                          disabled={actionLoading === `speedup-${p.id}-${tier.pct}`}
                          onClick={async () => {
                            setActionLoading(`speedup-${p.id}-${tier.pct}`);
                            try {
                              const res = await api.post(`/projects/${p.id}/speedup`, { percent: tier.pct });
                              toast.success(res.data.message || `Velocizzato del ${tier.pct}%!`);
                              fetch();
                              refreshUser();
                            } catch (err) {
                              toast.error(err.response?.data?.detail || 'Errore speedup');
                            } finally {
                              setActionLoading(null);
                            }
                          }}
                          data-testid={`speedup-${tier.pct}-${p.id}`}
                        >
                          <Zap className={`w-3 h-3 mx-auto mb-0.5 ${
                            tier.color === 'yellow' ? 'text-yellow-400' : tier.color === 'orange' ? 'text-orange-400' : 'text-red-400'
                          }`} />
                          <span className={`text-[9px] font-bold block ${
                            tier.color === 'yellow' ? 'text-yellow-300' : tier.color === 'orange' ? 'text-orange-300' : 'text-red-300'
                          }`}>{tier.label}</span>
                          <span className="text-[7px] text-gray-500">
                            {isFree ? 'GRATIS' : `${tier.cost} CP`}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                  {(p.free_speedups || 0) > 0 && (
                    <p className="text-[8px] text-green-400 text-center mt-1">{p.free_speedups} velocizzazioni gratuite rimaste</p>
                  )}
                </div>
              </div>
            )}

            {/* Step: casting ready */}
            {step === 'casting_ready' && (
              <div className="space-y-2" data-testid={`casting-ready-${p.id}`}>
                <div className="p-2 rounded-lg border border-green-500/20 bg-green-500/5 text-center">
                  <p className="text-[10px] font-bold text-green-400">Coming Soon completato!</p>
                  {p.hype_score > 0 && <p className="text-[9px] text-orange-400">Hype accumulato: {p.hype_score}</p>}
                </div>
                <Button size="sm" className="w-full bg-green-700 hover:bg-green-600 text-xs"
                  onClick={() => advance(p.id)} disabled={actionLoading === `adv-${p.id}`}
                  data-testid={`advance-${p.id}`}>
                  {actionLoading === `adv-${p.id}` ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Users className="w-3 h-3 mr-1" />}
                  Prosegui al Casting (2 CP)
                </Button>
              </div>
            )}

            {/* Discard button always available */}
            {step !== 'coming_soon_active' && (
              <div className="mt-2">
                <Button size="sm" variant="outline" className="text-[9px] border-red-800/50 text-red-400/60 hover:bg-red-500/10 h-6 w-full"
                  onClick={() => discard(p.id)} data-testid={`discard-${p.id}`}>
                  <ThumbsDown className="w-2.5 h-2.5 mr-1" /> Scarta
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )})}
    </div>
  );
};

// ============ CASTING TAB ============
const CastingTab = ({ api, refreshUser, refreshCounts }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [expandedRoles, setExpandedRoles] = useState({});
  const [actorRoles, setActorRoles] = useState({});
  const [equipmentOpen, setEquipmentOpen] = useState(null);
  const [equipmentOptions, setEquipmentOptions] = useState([]);
  const [selectedEquipment, setSelectedEquipment] = useState({});
  const [equipLoading, setEquipLoading] = useState(false);
  const [rejectedProposal, setRejectedProposal] = useState(null);
  const [castingMode, setCastingMode] = useState({}); // {filmId: 'agency'|'market'|null}
  const [agencyActors, setAgencyActors] = useState({ effective: [], school: [] });
  const [agencyInfo, setAgencyInfo] = useState(null);
  const [selectedAgencyActors, setSelectedAgencyActors] = useState({});
  const [agencyRoles, setAgencyRoles] = useState({});
  const [expandedSkills, setExpandedSkills] = useState({});
  const [expandedScreenplay, setExpandedScreenplay] = useState({});

  const ACTOR_ROLES = ['Protagonista', 'Co-Protagonista', 'Antagonista', 'Supporto', 'Cameo'];

  const SkillBar = ({ label, value, max = 100 }) => (
    <div className="flex items-center gap-1.5">
      <span className="text-[8px] text-gray-500 w-14 truncate">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{
          width: `${(value / max) * 100}%`,
          backgroundColor: value >= 80 ? '#22c55e' : value >= 50 ? '#eab308' : '#ef4444'
        }} />
      </div>
      <span className="text-[8px] text-gray-400 w-5 text-right">{value}</span>
    </div>
  );

  const GenderIcon = ({ gender }) => {
    if (gender === 'female') return <span className="text-[10px] text-pink-400" title="Donna">&#9792;</span>;
    if (gender === 'male') return <span className="text-[10px] text-sky-400" title="Uomo">&#9794;</span>;
    return null;
  };

  const FameLabel = ({ fameCategory, fameLabel }) => {
    const colors = {
      'unknown': 'bg-gray-600/30 text-gray-400',
      'rising': 'bg-emerald-500/20 text-emerald-400',
      'famous': 'bg-amber-500/20 text-amber-400',
      'superstar': 'bg-purple-500/20 text-purple-400'
    };
    return <Badge className={`text-[8px] h-4 ${colors[fameCategory] || colors.unknown}`}>{fameLabel || 'Sconosciuto'}</Badge>;
  };

  const GrowthTrend = ({ trend }) => {
    if (trend === 'rising') return <TrendingUp className="w-3 h-3 text-green-400" title="In crescita" />;
    if (trend === 'declining') return <TrendingDown className="w-3 h-3 text-red-400" title="In calo" />;
    return <Minus className="w-3 h-3 text-gray-600" title="Stabile" />;
  };

  const PersonMeta = ({ person }) => (
    <div className="flex items-center gap-1 flex-wrap mt-0.5">
      {person?.gender && <GenderIcon gender={person.gender} />}
      {person?.age && <span className="text-[9px] text-gray-500">{person.age}a</span>}
      {person?.nationality && (
        <span className="text-[9px] text-gray-500 flex items-center gap-0.5">
          <Globe className="w-2.5 h-2.5" />{person.nationality}
        </span>
      )}
      {person?.imdb_rating != null && (
        <Badge className="text-[8px] h-4 bg-yellow-500/20 text-yellow-400 font-bold">
          <Star className="w-2.5 h-2.5 mr-0.5 fill-yellow-400" />{person.imdb_rating.toFixed(1)}
        </Badge>
      )}
      {person?.fame_category && <FameLabel fameCategory={person.fame_category} fameLabel={person.fame_label} />}
      {person?.growth_trend && <GrowthTrend trend={person.growth_trend} />}
      {person?.has_worked_with_player && (
        <Badge className="text-[8px] h-4 bg-cyan-500/20 text-cyan-400">
          <UserCheck className="w-2.5 h-2.5 mr-0.5" />Collaboratore
        </Badge>
      )}
      {(person?.strong_genres_names || []).map((g, i) => (
        <Badge key={`sg-${i}`} className="bg-emerald-500/15 text-emerald-400 text-[7px] h-3">{g}</Badge>
      ))}
      {person?.adaptable_genre_name && (
        <Badge className="bg-amber-500/15 text-amber-400 text-[7px] h-3">~ {person.adaptable_genre_name}</Badge>
      )}
    </div>
  );

  const SelectedCastDetail = ({ person, roleName }) => (
    <div className="mt-2 p-2 bg-black/30 rounded border border-gray-700">
      <div className="flex items-center gap-2 mb-1.5">
        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-[10px] font-bold text-yellow-400">
          {person?.name?.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold">{person?.name}</p>
          <p className="text-[9px] text-gray-500">{roleName} &bull; ${(person?.cost_per_film || person?.cost || 0).toLocaleString()}</p>
          <PersonMeta person={person} />
        </div>
      </div>
      {person?.skills && Object.entries(person.skills).map(([skill, val]) => (
        <SkillBar key={skill} label={skill} value={val} />
      ))}
      {person?.role_in_film && (
        <Badge className="mt-1.5 bg-purple-500/20 text-purple-400 text-[9px]">{person.role_in_film}</Badge>
      )}
    </div>
  );

  const fetch = useCallback(async () => {
    try {
      const res = await api.get('/film-pipeline/casting');
      // Filter out corrupted films that could crash rendering
      const safeFilms = (res.data.casting_films || []).filter(f => f && f.id && f.title);
      setFilms(safeFilms);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [api]);

  const loadAgencyActors = useCallback(async () => {
    try {
      const res = await api.get('/agency/actors-for-casting');
      setAgencyActors({ effective: res.data.effective_actors || [], school: res.data.school_students || [] });
      setAgencyInfo(res.data);
    } catch (e) { console.error(e); }
  }, [api]);

  useEffect(() => { fetch(); loadAgencyActors(); const i = setInterval(fetch, 60000); return () => clearInterval(i); }, [fetch, loadAgencyActors]);

  const speedUp = async (filmId, roleType) => {
    setActionLoading(`speed-${filmId}-${roleType}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/speed-up-casting`, { role_type: roleType });
      toast.success(res.data.message);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const selectCast = async (filmId, roleType, proposalId) => {
    if (roleType === 'actors' && !actorRoles[proposalId]) {
      toast.error('Seleziona il ruolo per questo attore (Protagonista, Antagonista, etc.)');
      return;
    }
    setActionLoading(`select-${proposalId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/select-cast`, {
        role_type: roleType, proposal_id: proposalId,
        actor_role: roleType === 'actors' ? (actorRoles[proposalId] || 'Supporto') : null
      });
      if (res.data.accepted) {
        toast.success(res.data.message);
        if (res.data.casting_complete) toast.success('Casting completo! Puoi procedere alla sceneggiatura.');
      } else {
        // Rejected - show renegotiate option
        setRejectedProposal({ filmId, roleType, proposalId, name: res.data.message });
        toast.error(res.data.message);
      }
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const renegotiate = async (filmId, roleType, proposalId) => {
    setActionLoading(`renego-${proposalId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/renegotiate`, {
        role_type: roleType, proposal_id: proposalId,
        actor_role: roleType === 'actors' ? (actorRoles[proposalId] || 'Supporto') : null
      });
      if (res.data.accepted) {
        toast.success(res.data.message);
        setRejectedProposal(null);
        if (res.data.casting_complete) toast.success('Casting completo!');
      } else {
        toast.error(res.data.message);
      }
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const advanceToScreenplay = async (filmId) => {
    setActionLoading(`adv-${filmId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/advance-to-screenplay`);
      toast.success(res.data.message);
      refreshUser(); refreshCounts(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const submitAgencyCast = async (filmId) => {
    const selected = Object.entries(selectedAgencyActors)
      .filter(([_, v]) => v)
      .map(([actorId]) => {
        const eff = agencyActors.effective.find(a => a.id === actorId);
        const sch = agencyActors.school.find(a => a.id === actorId);
        return {
          actor_id: actorId,
          role: agencyRoles[actorId] || 'Supporto',
          source: eff ? 'effective' : sch ? 'school' : 'effective'
        };
      });
    if (selected.length === 0) { toast.error('Seleziona almeno un attore'); return; }
    setActionLoading(`agency-cast-${filmId}`);
    try {
      const res = await api.post(`/agency/cast-for-film/${filmId}`, { actor_ids: selected });
      toast.success(res.data.message);
      setSelectedAgencyActors({});
      setAgencyRoles({});
      refreshUser(); fetch(); loadAgencyActors();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const toggleAgencyActor = (actorId) => {
    setSelectedAgencyActors(prev => ({ ...prev, [actorId]: !prev[actorId] }));
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;
  if (!films.length) return <div className="text-center py-12 text-gray-500"><Users className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessun film in casting.</p></div>;

  const roleLabels = { directors: 'Regista', screenwriters: 'Sceneggiatore', actors: 'Attori', composers: 'Compositore' };
  const roleIcons = { directors: '🎬', screenwriters: '📝', actors: '🎭', composers: '🎵' };

  const openEquipment = async (filmId) => {
    setEquipmentOpen(filmId);
    try {
      const res = await api.get(`/film-pipeline/${filmId}/equipment-options`);
      setEquipmentOptions(res.data.options);
      const sel = {};
      (res.data.selected || []).forEach(e => { sel[e.id] = true; });
      setSelectedEquipment(sel);
    } catch (e) { toast.error('Errore caricamento attrezzature'); }
  };

  const saveEquipment = async (filmId) => {
    setEquipLoading(true);
    try {
      const ids = Object.keys(selectedEquipment).filter(k => selectedEquipment[k]);
      const res = await api.post(`/film-pipeline/${filmId}/select-equipment`, { equipment_ids: ids });
      toast.success(res.data.message);
      setEquipmentOpen(null);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setEquipLoading(false); }
  };

  return (
    <div className="space-y-3">
      {films.map(f => {
        const cast = f.cast || {};
        const castComplete = cast.director && cast.screenwriter && cast.composer && cast.actors?.length > 0;
        const isLocked = f.cast_locked === true || (f.from_emerging_screenplay && f.emerging_option === 'full_package');
        return (
          <Card key={f.id} className="bg-[#1A1A1B] border-gray-800 film-card-hover" data-testid={`casting-film-${f.id}`}>
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-sm">{f.title}</h3>
                  <p className="text-[10px] text-gray-500">{f.genre} &bull; {f.subgenre} &bull; Pre-IMDb: <span className="text-yellow-400">{f.pre_imdb_score}</span></p>
                  {isLocked && <Badge className="bg-emerald-500/20 text-emerald-400 text-[9px] mt-1">Pacchetto Completo - Cast incluso</Badge>}
                </div>
                {(castComplete || isLocked) && (
                  <Button size="sm" className="bg-green-700 hover:bg-green-800 text-xs" onClick={() => advanceToScreenplay(f.id)}
                    disabled={actionLoading === `adv-${f.id}`} data-testid={`advance-screenplay-${f.id}`}>
                    {actionLoading === `adv-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3 mr-1" />}
                    Prosegui (2 CP)
                  </Button>
                )}
              </div>

              {/* Locked cast: read-only view always visible */}
              {isLocked ? (
                <div className="space-y-2 mt-2">
                  <div className="space-y-2">
                    {cast.director && (
                      <div className="rounded border border-green-800 bg-green-500/5 p-2">
                        <span className="text-[10px] font-semibold text-gray-400">🎬 Regista</span>
                        <SelectedCastDetail person={cast.director} roleName="Regista" />
                      </div>
                    )}
                    {cast.screenwriter && (
                      <div className="rounded border border-green-800 bg-green-500/5 p-2">
                        <span className="text-[10px] font-semibold text-gray-400">📝 Sceneggiatore</span>
                        <SelectedCastDetail person={cast.screenwriter} roleName="Sceneggiatore" />
                      </div>
                    )}
                    {cast.actors?.length > 0 && (
                      <div className="rounded border border-green-800 bg-green-500/5 p-2">
                        <span className="text-[10px] font-semibold text-gray-400">🎭 Attori ({cast.actors.length})</span>
                        {cast.actors.map((a, idx) => (
                          <SelectedCastDetail key={idx} person={a} roleName={a.role || a.role_in_film || 'Attore'} />
                        ))}
                      </div>
                    )}
                    {cast.composer && (
                      <div className="rounded border border-green-800 bg-green-500/5 p-2">
                        <span className="text-[10px] font-semibold text-gray-400">🎵 Compositore</span>
                        <SelectedCastDetail person={cast.composer} roleName="Compositore" />
                      </div>
                    )}
                  </div>
                </div>
              ) : (
              <>
              <div className="flex gap-2 mb-2">
                <Button variant="outline" size="sm" className="flex-1 text-xs border-gray-700"
                  onClick={() => setSelectedFilm(selectedFilm === f.id ? null : f.id)}>
                  {selectedFilm === f.id ? 'Chiudi Casting' : 'Gestisci Casting'}
                </Button>
                <Button variant="outline" size="sm" className="text-xs border-amber-700 text-amber-400 hover:bg-amber-500/10"
                  onClick={() => openEquipment(f.id)} data-testid={`equipment-btn-${f.id}`}>
                  <Settings className="w-3 h-3 mr-0.5" /> Attrezzature
                  {f.equipment?.length > 0 && <Badge className="ml-1 bg-green-500/20 text-green-400 text-[8px] h-4">{f.equipment.length}</Badge>}
                </Button>
                <Button variant="outline" size="sm" className="text-xs border-red-800/50 text-red-400 hover:bg-red-500/10"
                  disabled={actionLoading === `discard-${f.id}`}
                  onClick={async () => {
                    setActionLoading(`discard-${f.id}`);
                    try {
                      const res = await api.post(`/film-pipeline/${f.id}/discard`);
                      toast.success(res.data.message);
                      refreshUser(); refreshCounts(); fetch();
                    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
                    finally { setActionLoading(null); }
                  }}
                  data-testid={`discard-casting-${f.id}`}>
                  {actionLoading === `discard-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ThumbsDown className="w-3 h-3 mr-0.5" />}
                  Scarta
                </Button>
              </div>

              {/* Equipment Popup */}
              {equipmentOpen === f.id && (
                <div className="p-2 mb-2 rounded border border-amber-500/30 bg-amber-500/5 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-amber-400">Attrezzature Disponibili</p>
                    <Button size="sm" variant="ghost" className="h-5 w-5 p-0" onClick={() => setEquipmentOpen(null)}><X className="w-3 h-3" /></Button>
                  </div>
                  <div className="grid grid-cols-1 gap-1">
                    {equipmentOptions.map(eq => (
                      <label key={eq.id} className={`flex items-center gap-2 p-1.5 rounded border cursor-pointer transition-all ${selectedEquipment[eq.id] ? 'border-amber-500 bg-amber-500/10' : 'border-gray-700 hover:border-gray-600'}`}>
                        <input type="checkbox" checked={!!selectedEquipment[eq.id]}
                          onChange={e => setSelectedEquipment(p => ({...p, [eq.id]: e.target.checked}))}
                          className="accent-amber-500 w-3 h-3" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            <span className="text-[10px] font-medium">{eq.name}</span>
                            <Badge className={`text-[7px] h-3 ${eq.tier === 'premium' ? 'bg-purple-500/20 text-purple-400' : eq.tier === 'pro' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-600/20 text-gray-400'}`}>{eq.tier}</Badge>
                          </div>
                          <p className="text-[8px] text-gray-500 truncate">{eq.desc}</p>
                        </div>
                        <span className="text-[9px] text-yellow-400 font-medium whitespace-nowrap">${(eq.cost/1000).toFixed(0)}K</span>
                      </label>
                    ))}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-gray-400">
                      Totale: <span className="text-yellow-400">${(equipmentOptions.filter(e => selectedEquipment[e.id]).reduce((s, e) => s + e.cost, 0) / 1000).toFixed(0)}K</span>
                    </span>
                    <Button size="sm" className="bg-amber-700 hover:bg-amber-800 text-[10px] h-6" onClick={() => saveEquipment(f.id)} disabled={equipLoading}
                      data-testid={`save-equipment-${f.id}`}>
                      {equipLoading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 mr-0.5" />} Conferma
                    </Button>
                  </div>
                </div>
              )}

              {selectedFilm === f.id && (
                <div className="space-y-3 mt-2">
                  {/* Agency/Market choice for actors */}
                  {!castingMode[f.id] && (agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                    <div className="p-3 rounded border border-purple-800/40 bg-purple-500/5 space-y-2" data-testid="casting-mode-choice">
                      <p className="text-xs font-semibold text-purple-300">Come vuoi ingaggiare gli attori?</p>
                      <div className="grid grid-cols-2 gap-2">
                        <Button size="sm" className="h-auto py-2 bg-purple-700/80 hover:bg-purple-700 text-left flex-col items-start"
                          onClick={() => setCastingMode(p => ({...p, [f.id]: 'agency'}))} data-testid="cast-mode-agency">
                          <span className="text-xs font-semibold flex items-center gap-1"><Users className="w-3.5 h-3.5" /> Dalla tua Agenzia</span>
                          <span className="text-[9px] text-purple-200/70 mt-0.5">
                            {agencyActors.effective.length} attori + {agencyActors.school.length} studenti
                          </span>
                        </Button>
                        <Button size="sm" className="h-auto py-2 bg-cyan-700/80 hover:bg-cyan-700 text-left flex-col items-start"
                          onClick={() => setCastingMode(p => ({...p, [f.id]: 'market'}))} data-testid="cast-mode-market">
                          <span className="text-xs font-semibold flex items-center gap-1"><Globe className="w-3.5 h-3.5" /> Dal Mercato</span>
                          <span className="text-[9px] text-cyan-200/70 mt-0.5">Attori proposti dagli agenti</span>
                        </Button>
                      </div>
                      <p className="text-[9px] text-gray-500">Puoi usare entrambi i metodi. Regista, sceneggiatore e compositore sono dal mercato.</p>
                    </div>
                  )}
                  {/* If no agency actors, auto-set to market */}
                  {!castingMode[f.id] && agencyActors.effective.length === 0 && agencyActors.school.length === 0 && (() => { if (!castingMode[f.id]) setCastingMode(p => ({...p, [f.id]: 'market'})); return null; })()}

                  {/* Agency casting mode */}
                  {castingMode[f.id] === 'agency' && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-semibold text-purple-300">Attori dalla tua Agenzia</p>
                        <Button size="sm" variant="ghost" className="h-6 text-[9px] text-gray-400"
                          onClick={() => setCastingMode(p => ({...p, [f.id]: 'market'}))}>
                          Passa al Mercato
                        </Button>
                      </div>
                      {/* Already cast agency actors */}
                      {cast.actors?.filter(a => a.is_agency_actor).length > 0 && (
                        <div className="p-2 rounded border border-green-800 bg-green-500/5">
                          <p className="text-[10px] font-medium text-green-400 mb-1">Attori agenzia nel cast:</p>
                          {cast.actors.filter(a => a.is_agency_actor).map((a, i) => (
                            <SelectedCastDetail key={i} person={a} roleName={a.role_in_film || 'Attore'} />
                          ))}
                        </div>
                      )}
                      {/* Effective actors */}
                      {agencyActors.effective.length > 0 && (
                        <div>
                          <p className="text-[10px] font-medium text-gray-400 mb-1">Attori Effettivi ({agencyInfo?.agency_name})</p>
                          {agencyActors.effective.map(actor => {
                            const alreadyCast = cast.actors?.some(a => a.id === actor.id);
                            const isSelected = selectedAgencyActors[actor.id];
                            const avgSkill = Object.values(actor.skills || {}).length > 0
                              ? Math.round(Object.values(actor.skills).reduce((a, b) => a + b, 0) / Object.values(actor.skills).length) : 0;
                            return (
                              <div key={actor.id} className={`p-2 mb-1 rounded border cursor-pointer transition-all ${alreadyCast ? 'border-green-800 bg-green-500/5 opacity-60' : isSelected ? 'border-purple-500 bg-purple-500/10' : 'border-gray-700 hover:border-purple-800/60'}`}
                                onClick={() => !alreadyCast && toggleAgencyActor(actor.id)} data-testid={`agency-actor-pick-${actor.id}`}>
                                <div className="flex items-center gap-2">
                                  <img src={actor.avatar_url} alt="" className="w-7 h-7 rounded-full bg-gray-800" />
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-1 flex-wrap">
                                      <span className="text-[11px] font-medium">{actor.name}</span>
                                      <span className={`text-[10px] font-bold ${actor.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>
                                        {actor.gender === 'female' ? '♀' : '♂'}
                                      </span>
                                      {actor.is_legendary && <Badge className="bg-yellow-500/20 text-yellow-400 text-[7px] h-3.5">Leggenda</Badge>}
                                      {[...Array(actor.stars || 2)].map((_, i) => <Star key={i} className="w-2 h-2 text-yellow-500 fill-yellow-500" />)}
                                    </div>
                                    <p className="text-[9px] text-gray-500">
                                      {actor.nationality} &bull; {actor.age}a &bull; Skill: <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>
                                      &bull; {actor.films_count || 0} film
                                    </p>
                                    <div className="flex flex-wrap gap-0.5 mt-0.5">
                                      {(actor.strong_genres_names || []).map((g, i) => <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[7px] h-3">{g}</Badge>)}
                                      {actor.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[7px] h-3">~ {actor.adaptable_genre_name}</Badge>}
                                    </div>
                                  </div>
                                  {!alreadyCast && isSelected && (
                                    <select value={agencyRoles[actor.id] || ''} onClick={e => e.stopPropagation()}
                                      onChange={e => setAgencyRoles(p => ({...p, [actor.id]: e.target.value}))}
                                      className="h-6 text-[9px] bg-gray-800 border border-gray-700 rounded px-1 text-white">
                                      <option value="">Ruolo...</option>
                                      {ACTOR_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                                    </select>
                                  )}
                                  {alreadyCast && <Badge className="bg-green-500/20 text-green-400 text-[8px]">Nel cast</Badge>}
                                  {!alreadyCast && isSelected && <Check className="w-4 h-4 text-purple-400" />}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                      {/* School students */}
                      {agencyActors.school.length > 0 && (
                        <div>
                          <p className="text-[10px] font-medium text-gray-400 mb-1">Studenti Scuola Recitazione (continuano la formazione + bonus crescita)</p>
                          {agencyActors.school.map(actor => {
                            const alreadyCast = cast.actors?.some(a => a.id === actor.id);
                            const isSelected = selectedAgencyActors[actor.id];
                            const skills = actor.skills || {};
                            const avgSkill = Object.values(skills).length > 0
                              ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;
                            return (
                              <div key={actor.id} className={`p-2 mb-1 rounded border cursor-pointer transition-all ${alreadyCast ? 'border-green-800 bg-green-500/5 opacity-60' : isSelected ? 'border-cyan-500 bg-cyan-500/10' : 'border-gray-700 hover:border-cyan-800/60'}`}
                                onClick={() => !alreadyCast && toggleAgencyActor(actor.id)} data-testid={`school-actor-pick-${actor.id}`}>
                                <div className="flex items-center gap-2">
                                  <div className="w-7 h-7 rounded-full bg-cyan-900/30 flex items-center justify-center text-[10px] font-bold text-cyan-400">
                                    {actor.name?.charAt(0)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-1">
                                      <span className="text-[11px] font-medium">{actor.name}</span>
                                      <Badge className="bg-cyan-500/15 text-cyan-400 text-[7px] h-3">Studente</Badge>
                                      <span className="text-[9px] text-gray-500">Skill: {avgSkill}</span>
                                    </div>
                                  </div>
                                  {!alreadyCast && isSelected && (
                                    <select value={agencyRoles[actor.id] || ''} onClick={e => e.stopPropagation()}
                                      onChange={e => setAgencyRoles(p => ({...p, [actor.id]: e.target.value}))}
                                      className="h-6 text-[9px] bg-gray-800 border border-gray-700 rounded px-1 text-white">
                                      <option value="">Ruolo...</option>
                                      {ACTOR_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                                    </select>
                                  )}
                                  {alreadyCast && <Badge className="bg-green-500/20 text-green-400 text-[8px]">Nel cast</Badge>}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                      {/* Confirm button */}
                      {Object.values(selectedAgencyActors).some(v => v) && (
                        <Button size="sm" className="w-full bg-purple-700 hover:bg-purple-800 text-xs"
                          onClick={() => submitAgencyCast(f.id)}
                          disabled={actionLoading === `agency-cast-${f.id}`} data-testid="confirm-agency-cast">
                          {actionLoading === `agency-cast-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Check className="w-3 h-3 mr-1" />}
                          Aggiungi {Object.values(selectedAgencyActors).filter(v => v).length} attore/i al cast
                        </Button>
                      )}
                      <p className="text-[9px] text-amber-400">Bonus: +20-70% XP e Fama player per ogni film con i tuoi attori!</p>
                    </div>
                  )}

                  {/* Market casting mode - the existing proposal system */}
                  {(castingMode[f.id] === 'market' || (!castingMode[f.id] && agencyActors.effective.length === 0 && agencyActors.school.length === 0)) && (
                    <div className="space-y-3">
                      {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold text-cyan-300">Casting dal Mercato</p>
                          <Button size="sm" variant="ghost" className="h-6 text-[9px] text-gray-400"
                            onClick={() => setCastingMode(p => ({...p, [f.id]: 'agency'}))}>
                            Gestisci Agenzia
                          </Button>
                        </div>
                      )}

                      {/* Agency actors in primo piano nel mercato */}
                      {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                        <div className="p-2 rounded-lg border border-purple-500/15 bg-purple-500/5 space-y-1.5" data-testid="film-market-agency-section">
                          <p className="text-[10px] font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-1">
                            <Users className="w-3 h-3" /> I tuoi Attori
                            <Badge className="text-[7px] bg-amber-500/15 text-amber-400 h-3 ml-1">Bonus XP/Fama</Badge>
                          </p>
                          <div className="space-y-1.5 max-h-48 overflow-y-auto">
                            {[...agencyActors.effective, ...agencyActors.school].map(actor => {
                              const isSelected = selectedAgencyActors[actor.id];
                              const skills = actor.skills || {};
                              const avgSkill = Object.values(skills).length > 0
                                ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;
                              return (
                                <div key={actor.id} className={`p-1.5 rounded-lg transition-all cursor-pointer border ${
                                  isSelected ? 'bg-purple-500/15 border-purple-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-purple-500/10'
                                }`} onClick={() => toggleAgencyActor(actor.id)} data-testid={`film-market-agency-actor-${actor.id}`}>
                                  <div className="flex items-center gap-2">
                                    <div className="w-7 h-7 rounded-full bg-purple-500/20 flex items-center justify-center text-[10px] font-bold text-purple-400 flex-shrink-0">
                                      {actor.name?.charAt(0)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-1 flex-wrap">
                                        <p className="text-[11px] font-medium truncate">{actor.name}</p>
                                        <span className={`text-[10px] font-bold ${actor.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>
                                          {actor.gender === 'female' ? '♀' : '♂'}
                                        </span>
                                        {[...Array(actor.stars || 2)].map((_, i) => <Star key={i} className="w-2 h-2 text-yellow-500 fill-yellow-500" />)}
                                      </div>
                                      <p className="text-[9px] text-gray-500">
                                        {actor.nationality} &bull; {actor.age}a &bull; Skill: <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>
                                        &bull; {actor.films_count || 0} film
                                      </p>
                                      <div className="flex items-center gap-0.5 flex-wrap">
                                        {(actor.strong_genres_names || []).map((g, i) => <Badge key={`sg-${i}`} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                                        {actor.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[6px] h-3">~ {actor.adaptable_genre_name}</Badge>}
                                      </div>
                                    </div>
                                  {isSelected && (
                                    <select className="bg-[#1a1a1a] text-[9px] rounded px-1 py-0.5 border border-white/10 text-white"
                                      value={agencyRoles[actor.id] || 'Supporto'} onClick={e => e.stopPropagation()}
                                      onChange={e => setAgencyRoles(p => ({...p, [actor.id]: e.target.value}))}>
                                      <option value="Protagonista">Protagonista</option>
                                      <option value="Co-Protagonista">Co-Protagonista</option>
                                      <option value="Antagonista">Antagonista</option>
                                      <option value="Supporto">Supporto</option>
                                    </select>
                                  )}
                                  {isSelected && <Check className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                          {Object.values(selectedAgencyActors).some(Boolean) && (
                            <Button size="sm" className="w-full bg-purple-500 hover:bg-purple-600 text-white text-xs" onClick={() => submitAgencyCast(f.id)} disabled={actionLoading === `agency-cast-${f.id}`} data-testid="film-market-confirm-agency-cast">
                              {actionLoading === `agency-cast-${f.id}` ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Users className="w-3.5 h-3.5 mr-1" />}
                              Aggiungi dall'Agenzia ({Object.values(selectedAgencyActors).filter(Boolean).length})
                            </Button>
                          )}
                        </div>
                      )}

                      {/* Divider before market proposals */}
                      {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                        <div className="border-t border-white/5 pt-2">
                          <p className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1">
                            <Star className="w-3 h-3" /> Proposte dal Mercato
                          </p>
                        </div>
                      )}
                  {Object.entries(f.cast_proposals || {}).map(([role, proposals]) => {
                    const hasSelection = role === 'actors' ? cast.actors?.length > 0 : cast[role === 'directors' ? 'director' : role === 'screenwriters' ? 'screenwriter' : 'composer'];
                    const selected = role === 'actors' ? false : hasSelection; // Actors: never block, always allow more
                    const selectedPerson = role === 'actors' ? null : cast[role === 'directors' ? 'director' : role === 'screenwriters' ? 'screenwriter' : 'composer'];
                    const available = proposals.filter(p => p.status === 'available');
                    const pending = proposals.filter(p => p.status === 'pending');
                    const roleKey = `${f.id}-${role}`;
                    const isExpanded = expandedRoles[roleKey];
                    const actorCount = role === 'actors' ? (cast.actors?.length || 0) : 0;

                    return (
                      <div key={role} className={`rounded border transition-all ${selected ? 'border-green-800 bg-green-500/5' : hasSelection && role === 'actors' ? 'border-cyan-800 bg-cyan-500/5' : 'border-gray-700'}`}>
                        <div className="flex items-center justify-between p-2 cursor-pointer hover:bg-white/5"
                          onClick={() => setExpandedRoles(prev => ({ ...prev, [roleKey]: !prev[roleKey] }))}
                          data-testid={`role-header-${role}`}>
                          <span className="text-xs font-medium">{roleIcons[role]} {roleLabels[role]}</span>
                          <div className="flex items-center gap-1">
                            {role === 'actors' && actorCount > 0 && (
                              <Badge className="bg-cyan-500/20 text-cyan-400 text-[9px]">
                                {actorCount} scelti
                              </Badge>
                            )}
                            {selected ? (
                              <Badge className="bg-green-500/20 text-green-400 text-[9px]">
                                <Check className="w-3 h-3 mr-0.5" />
                                Scelto
                              </Badge>
                            ) : (
                              <>
                                <Badge className="bg-cyan-500/20 text-cyan-400 text-[9px]">{available.length} disponibili</Badge>
                                {pending.length > 0 && (
                                  <Button size="sm" className="h-5 px-1.5 text-[9px] bg-yellow-600 hover:bg-yellow-700"
                                    disabled={actionLoading === `speed-${f.id}-${role}`}
                                    onClick={(e) => { e.stopPropagation(); speedUp(f.id, role); }}>
                                    <Zap className="w-2.5 h-2.5 mr-0.5" /> Sblocca (${(pending.length * 5000).toLocaleString()})
                                  </Button>
                                )}
                              </>
                            )}
                            <ChevronRight className={`w-3.5 h-3.5 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="px-2 pb-2">
                            {/* Show selected actors (always visible for actors) */}
                            {role === 'actors' && cast.actors?.length > 0 && cast.actors.map((actor, idx) => (
                              <SelectedCastDetail key={idx} person={actor} roleName={actor.role_in_film || 'Attore'} />
                            ))}
                            {/* Show selected person for non-actor roles */}
                            {selected && role !== 'actors' && selectedPerson && (
                              <SelectedCastDetail person={selectedPerson} roleName={roleLabels[role]} />
                            )}

                            {/* Show available proposals — unified card format */}
                            {!selected && available.map(prop => {
                              const person = prop.person || {};
                              const skills = person.skills || {};
                              const avgSkill = Object.values(skills).length > 0
                                ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;
                              const skillsOpen = expandedSkills[prop.id];
                              return (
                              <div key={prop.id} 
                                className={`p-2 mb-1.5 rounded-lg border transition-all ${role === 'actors' ? 'border-cyan-800/30 cursor-pointer hover:border-cyan-500/50 hover:bg-cyan-500/5' : 'border-gray-800/50 hover:border-gray-700'} bg-white/[0.02]`}
                                onClick={role === 'actors' ? () => selectCast(f.id, role, prop.id) : undefined}
                                data-testid={`proposal-card-${prop.id}`}>
                                <div className="flex items-center gap-2">
                                  {person.avatar_url ? (
                                    <img src={person.avatar_url} alt="" className="w-9 h-9 rounded-full bg-gray-800" />
                                  ) : (
                                    <div className="w-9 h-9 rounded-full bg-cyan-500/20 flex items-center justify-center text-xs font-bold text-cyan-400">
                                      {person.name?.charAt(0)}
                                    </div>
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-1">
                                      <p className="text-xs font-semibold truncate">{person.name}</p>
                                      {person.gender && <span className={`text-[10px] font-bold ${person.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>{person.gender === 'female' ? '\u2640' : '\u2642'}</span>}
                                      {[...Array(person.stars || 2)].map((_, i) => <Star key={i} className="w-2.5 h-2.5 text-yellow-500 fill-yellow-500" />)}
                                      {person.fame_category && <Badge className={`text-[6px] h-3 ${person.fame_category === 'superstar' ? 'bg-yellow-500/20 text-yellow-400' : person.fame_category === 'famous' ? 'bg-orange-500/20 text-orange-400' : person.fame_category === 'rising' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-gray-500/20 text-gray-400'}`}>{person.fame_label || person.fame_category}</Badge>}
                                    </div>
                                    <p className="text-[9px] text-gray-500">
                                      {person.nationality}{person.age ? <>{' \u2022 '}{person.age}a</> : ''}{' \u2022 '}Skill: <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>{person.films_count ? <>{' \u2022 '}{person.films_count} film</> : ''}
                                    </p>
                                    <div className="flex flex-wrap gap-0.5 mt-0.5">
                                      {(person.strong_genres_names || []).map((g, i) => <Badge key={`sg-${i}`} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                                      {person.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[6px] h-3">~ {person.adaptable_genre_name}</Badge>}
                                    </div>
                                    {(person.agency_name || prop.agent_name) && (
                                      <p className="text-[8px] text-gray-600 mt-0.5">Agenzia: {person.agency_name || prop.agent_name}</p>
                                    )}
                                  </div>
                                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                                    <span className="text-[9px] text-yellow-400 font-bold">${prop.cost?.toLocaleString()}</span>
                                    {role === 'actors' && (
                                      <select value={actorRoles[prop.id] || ''} onChange={e => { e.stopPropagation(); setActorRoles(p => ({...p, [prop.id]: e.target.value})); }}
                                        onClick={e => e.stopPropagation()}
                                        className="h-5 text-[8px] bg-gray-800 border border-gray-700 rounded px-0.5 text-white"
                                        data-testid={`actor-role-${prop.id}`}>
                                        <option value="">Ruolo...</option>
                                        {ACTOR_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                                      </select>
                                    )}
                                    {role !== 'actors' && (
                                      <Button size="sm" className="h-6 px-2 text-[10px] bg-cyan-700 hover:bg-cyan-800"
                                        disabled={actionLoading === `select-${prop.id}`}
                                        onClick={(e) => { e.stopPropagation(); selectCast(f.id, role, prop.id); }}
                                        data-testid={`select-${prop.id}`}>
                                        {actionLoading === `select-${prop.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 mr-0.5" />}
                                        Scegli
                                      </Button>
                                    )}
                                    {role === 'actors' && <Badge className="bg-cyan-600/20 text-cyan-300 text-[7px]">Clicca</Badge>}
                                    {person.has_worked_with_player && <Badge className="text-[6px] bg-cyan-500/15 text-cyan-400 h-3">Collaboratore</Badge>}
                                  </div>
                                </div>
                                {/* Skill toggle */}
                                {Object.keys(skills).length > 0 && (
                                  <div className="mt-1">
                                    <button className="text-[8px] text-cyan-400 hover:text-cyan-300 flex items-center gap-0.5"
                                      onClick={e => { e.stopPropagation(); setExpandedSkills(p => ({...p, [prop.id]: !p[prop.id]})); }}
                                      data-testid={`toggle-skills-${prop.id}`}>
                                      {skillsOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                      {skillsOpen ? 'Nascondi Skill' : 'Mostra Skill'}
                                    </button>
                                    {skillsOpen && (
                                      <div className="grid grid-cols-3 gap-x-3 gap-y-0.5 mt-1 px-1">
                                        {Object.entries(skills).sort(([,a],[,b]) => b - a).map(([k, v]) => (
                                          <div key={k} className="flex items-center gap-1">
                                            <span className="text-[8px] text-gray-500 capitalize w-16 truncate">{k.replace(/_/g, ' ')}</span>
                                            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                              <div className={`h-full rounded-full ${v >= 80 ? 'bg-emerald-500' : v >= 60 ? 'bg-cyan-500' : v >= 40 ? 'bg-amber-500' : 'bg-red-500'}`} style={{width: `${v}%`}} />
                                            </div>
                                            <span className="text-[8px] text-gray-400 w-5 text-right">{v}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                              );
                            })}

                            {/* Show rejected proposals with renegotiate option */}
                            {proposals.filter(p => p.status === 'rejected').map(prop => (
                              <div key={prop.id} className="p-2 mb-1.5 bg-red-500/5 rounded border border-red-800/40" data-testid={`rejected-${prop.id}`}>
                                <div className="flex items-center justify-between">
                                  <div className="flex-1 min-w-0">
                                    <p className="text-xs font-medium text-red-300">{prop.person?.name}</p>
                                    <p className="text-[9px] text-red-400">Ha rifiutato &bull; Costo rinegoziazione: ${Math.round(prop.cost * 1.3).toLocaleString()}</p>
                                  </div>
                                  <Button size="sm" className="h-6 px-2 text-[10px] bg-amber-700 hover:bg-amber-800"
                                    disabled={actionLoading === `renego-${prop.id}`}
                                    onClick={(e) => { e.stopPropagation(); renegotiate(f.id, role, prop.id); }}
                                    data-testid={`renegotiate-${prop.id}`}>
                                    {actionLoading === `renego-${prop.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3 mr-0.5" />}
                                    Rinegozia
                                  </Button>
                                </div>
                              </div>
                            ))}

                            {/* Pending agents */}
                            {!selected && pending.length > 0 && available.length === 0 && (
                              <div className="flex items-center gap-1.5 p-2 text-[10px] text-gray-500">
                                <Clock className="w-3 h-3 animate-pulse text-yellow-500" />
                                {pending.length} {pending.length === 1 ? 'agente in arrivo' : 'agenti in arrivo'}...
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                    </div>
                  )}
                </div>
              )}
              </>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

// ============ CLASSIC POSTER STYLES ============
const CLASSIC_STYLES = [
  { id: 'noir', label: 'Film Noir', desc: 'Ombre drammatiche' },
  { id: 'vintage', label: 'Vintage', desc: 'Stile anni 60' },
  { id: 'action', label: 'Action', desc: 'Esplosioni e fuoco' },
  { id: 'romance', label: 'Romance', desc: 'Colori pastello' },
  { id: 'horror', label: 'Horror', desc: 'Dark e nebbia' },
  { id: 'scifi', label: 'Sci-Fi', desc: 'Neon futuristico' },
  { id: 'comedy', label: 'Commedia', desc: 'Colori vivaci' },
  { id: 'drama', label: 'Dramma', desc: 'Toni artistici' }
];

// ============ SCREENPLAY TAB ============
const ScreenplayTab = ({ api, refreshUser, refreshCounts }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState({});
  const [manualText, setManualText] = useState({});
  const [actionLoading, setActionLoading] = useState(null);
  // Poster states
  const [posterMode, setPosterMode] = useState({});
  const [posterPrompt, setPosterPrompt] = useState({});
  const [posterStyle, setPosterStyle] = useState({});
  const [posterLoading, setPosterLoading] = useState(null);
  const [expandedScreenplay, setExpandedScreenplay] = useState({});

  const fetch = useCallback(async () => {
    try { const res = await api.get('/film-pipeline/screenplay'); setFilms(res.data.films || []); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); }, [fetch]);

  const writeScreenplay = async (filmId) => {
    const m = mode[filmId] || 'ai';
    setActionLoading(filmId);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/write-screenplay`, {
        mode: m, manual_text: m === 'manual' ? manualText[filmId] || '' : undefined
      }, { timeout: 120000 });
      toast.success(res.data.message);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const advance = async (filmId) => {
    setActionLoading(`adv-${filmId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/advance-to-preproduction`);
      toast.success(res.data.message);
      refreshUser(); refreshCounts(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const generatePoster = async (filmId) => {
    const pMode = posterMode[filmId] || 'ai_auto';
    setPosterLoading(filmId);
    try {
      const body = { mode: pMode };
      if (pMode === 'ai_custom') body.custom_prompt = posterPrompt[filmId] || '';
      if (pMode === 'classic') body.classic_style = posterStyle[filmId] || 'drama';
      const res = await api.post(`/film-pipeline/${filmId}/generate-poster`, body, { timeout: 120000 });
      toast.success(res.data.message);
      fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore generazione poster'); }
    finally { setPosterLoading(null); }
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;
  if (!films.length) return <div className="text-center py-12 text-gray-500"><BookOpen className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessun film in fase sceneggiatura.</p></div>;

  return (
    <div className="space-y-3">
      {films.map(f => {
        // Defensive: ensure screenplay is always a string for rendering
        const screenplayText = typeof f.screenplay === 'string' ? f.screenplay 
          : (f.screenplay && typeof f.screenplay === 'object') ? (f.screenplay.text || JSON.stringify(f.screenplay))
          : '';
        const hasScreenplay = !!screenplayText;
        const isFullPackage = f.from_emerging_screenplay && f.emerging_option === 'full_package';
        
        // Wrap each film in try/catch so one bad film doesn't crash the entire list
        try {
        return (
        <Card key={f.id} className="bg-[#1A1A1B] border-gray-800 film-card-hover" data-testid={`screenplay-film-${f.id}`}>
          <CardContent className="p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-sm">{f.title || 'Senza titolo'}</h3>
                <p className="text-[10px] text-gray-500">{f.genre || '?'} &bull; {f.subgenre || ''} &bull; Pre-IMDb: <span className="text-yellow-400">{f.pre_imdb_score || '?'}</span></p>
                {isFullPackage && <Badge className="bg-emerald-500/20 text-emerald-400 text-[9px] mt-1">Pacchetto Completo - Sceneggiatura inclusa</Badge>}
              </div>
              <div className="flex items-center gap-1.5">
                {(hasScreenplay || isFullPackage) && (
                  <Button size="sm" className="bg-green-700 hover:bg-green-800 text-xs" onClick={() => advance(f.id)}
                    disabled={actionLoading === `adv-${f.id}`} data-testid={`advance-preprod-${f.id}`}>
                    <ChevronRight className="w-3 h-3 mr-1" /> Pre-Produzione (3 CP)
                  </Button>
                )}
                <Button size="sm" variant="outline" className="text-[10px] border-red-800/50 text-red-400 hover:bg-red-500/10 h-7 px-2"
                  disabled={actionLoading === `discard-${f.id}`}
                  onClick={async () => {
                    if (!window.confirm(`Scartare "${f.title}"?`)) return;
                    setActionLoading(`discard-${f.id}`);
                    try { const res = await api.post(`/film-pipeline/${f.id}/discard`); toast.success(res.data.message); refreshUser(); refreshCounts(); fetch(); }
                    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
                  }}
                  data-testid={`discard-screenplay-${f.id}`}>
                  {actionLoading === `discard-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ThumbsDown className="w-3 h-3" />}
                </Button>
              </div>
            </div>

            {/* Full package: screenplay is read-only, show pre_screenplay as final */}
            {isFullPackage ? (
              <>
                <div className="p-2 bg-green-500/5 rounded border border-green-500/20">
                  <p className="text-[9px] text-green-400 font-medium mb-0.5">Sceneggiatura (Pacchetto Completo)</p>
                  <p className="text-[10px] text-gray-300 line-clamp-6">{f.pre_screenplay || ''}</p>
                </div>

                {/* Poster section for full_package */}
                <div className="p-2 rounded border border-purple-500/30 bg-purple-500/5">
                  <p className="text-[10px] text-purple-400 font-semibold mb-1.5">Locandina del Film</p>
                  {f.poster_url ? (
                    <div className="flex items-start gap-2">
                      <img src={f.poster_url} alt="Locandina" className="w-20 h-28 object-cover rounded" />
                      <div className="flex-1">
                        <p className="text-[9px] text-green-400 mb-1">Locandina creata!</p>
                        <Button size="sm" variant="outline" className="text-[9px] border-purple-700 text-purple-400 h-6"
                          onClick={() => { setPosterMode(p => ({...p, [f.id]: 'ai_auto'})); generatePoster(f.id); }}
                          disabled={posterLoading === f.id}>
                          {posterLoading === f.id ? <RefreshCw className="w-2.5 h-2.5 animate-spin mr-0.5" /> : null}
                          Rigenera
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex gap-1 mb-1.5">
                        {[
                          { id: 'ai_auto', label: 'AI Automatica', desc: 'Dalla sceneggiatura' },
                          { id: 'ai_custom', label: 'AI + Prompt', desc: 'Scrivi tu il prompt' },
                          { id: 'classic', label: 'Stile Classico', desc: 'Scegli uno stile' }
                        ].map(opt => (
                          <button key={opt.id} onClick={() => setPosterMode(p => ({...p, [f.id]: opt.id}))}
                            className={`flex-1 p-1.5 rounded text-center border transition-all ${(posterMode[f.id] || 'ai_auto') === opt.id ? 'border-purple-500 bg-purple-500/10' : 'border-gray-700'}`}>
                            <p className="text-[9px] font-medium text-gray-200">{opt.label}</p>
                            <p className="text-[7px] text-gray-500">{opt.desc}</p>
                          </button>
                        ))}
                      </div>
                      {(posterMode[f.id] || 'ai_auto') === 'ai_custom' && (
                        <input type="text" placeholder="Descrivi la locandina che vuoi..."
                          value={posterPrompt[f.id] || ''} onChange={e => setPosterPrompt(p => ({...p, [f.id]: e.target.value}))}
                          className="w-full mb-1.5 text-[10px] bg-black/30 border border-gray-700 rounded p-1.5 text-white" />
                      )}
                      {(posterMode[f.id] || 'ai_auto') === 'classic' && (
                        <div className="grid grid-cols-4 gap-1 mb-1.5">
                          {CLASSIC_STYLES.map(s => (
                            <button key={s.id} onClick={() => setPosterStyle(p => ({...p, [f.id]: s.id}))}
                              className={`p-1 rounded text-center border transition-all ${(posterStyle[f.id] || 'drama') === s.id ? 'border-purple-500 bg-purple-500/10' : 'border-gray-700'}`}>
                              <p className="text-[8px] font-medium">{s.label}</p>
                              <p className="text-[7px] text-gray-500">{s.desc}</p>
                            </button>
                          ))}
                        </div>
                      )}
                      <Button size="sm" className="w-full bg-purple-700 hover:bg-purple-800 text-[10px] h-7"
                        onClick={() => generatePoster(f.id)} disabled={posterLoading === f.id}
                        data-testid={`generate-poster-${f.id}`}>
                        {posterLoading === f.id ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Sparkles className="w-3 h-3 mr-1" />}
                        Crea Locandina
                      </Button>
                    </>
                  )}
                </div>
              </>
            ) : (
            <>
            {/* Pre-screenplay (always visible, not editable) */}
            <div className="p-2 bg-yellow-500/5 rounded border border-yellow-500/20">
              <p className="text-[9px] text-yellow-400 font-medium mb-0.5">Pre-Sceneggiatura (originale)</p>
              <p className="text-[10px] text-gray-400 italic">"{f.pre_screenplay || ''}"</p>
            </div>

            {hasScreenplay ? (
              <>
                <div className="p-2 bg-green-500/5 rounded border border-green-500/20">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-[9px] text-green-400 font-medium">Sceneggiatura completata ({f.screenplay_mode === 'ai' ? 'AI' : f.screenplay_mode === 'manual' ? 'Manuale' : 'Solo Pre'})</p>
                    <button onClick={() => setExpandedScreenplay(p => ({...p, [f.id]: !p[f.id]}))}
                      className="text-[8px] text-green-400/70 hover:text-green-300 transition-colors flex items-center gap-0.5"
                      data-testid={`toggle-screenplay-${f.id}`}>
                      {expandedScreenplay[f.id] ? 'Riduci' : 'Espandi'}
                      <ChevronDown className={`w-2.5 h-2.5 transition-transform ${expandedScreenplay[f.id] ? 'rotate-180' : ''}`} />
                    </button>
                  </div>
                  <div className={`relative ${expandedScreenplay[f.id] ? '' : 'max-h-[180px] overflow-hidden'}`}>
                    <p className="text-[10px] text-gray-300 whitespace-pre-line leading-relaxed">{screenplayText}</p>
                    {!expandedScreenplay[f.id] && (
                      <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-[#111113] to-transparent pointer-events-none" />
                    )}
                  </div>
                  {!expandedScreenplay[f.id] && (
                    <button onClick={() => setExpandedScreenplay(p => ({...p, [f.id]: true}))}
                      className="w-full text-center text-[8px] text-green-400/60 hover:text-green-300 mt-1 transition-colors"
                      data-testid={`expand-screenplay-hint-${f.id}`}>
                      Scorri per leggere tutto...
                    </button>
                  )}
                </div>

                {/* ====== POSTER SECTION ====== */}
                <div className="p-2 rounded border border-purple-500/30 bg-purple-500/5">
                  <p className="text-[10px] text-purple-400 font-semibold mb-1.5">Locandina del Film</p>
                  {f.poster_url ? (
                    <div className="flex items-start gap-2">
                      <img src={f.poster_url} alt="Locandina" className="w-20 h-28 object-cover rounded" />
                      <div className="flex-1">
                        <p className="text-[9px] text-green-400 mb-1">Locandina creata!</p>
                        <Button size="sm" variant="outline" className="text-[9px] border-purple-700 text-purple-400 h-6"
                          onClick={() => { setPosterMode(p => ({...p, [f.id]: 'ai_auto'})); generatePoster(f.id); }}
                          disabled={posterLoading === f.id}>
                          {posterLoading === f.id ? <RefreshCw className="w-2.5 h-2.5 animate-spin mr-0.5" /> : null}
                          Rigenera
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex gap-1 mb-1.5">
                        {[
                          { id: 'ai_auto', label: 'AI Automatica', desc: 'Dalla sceneggiatura' },
                          { id: 'ai_custom', label: 'AI + Prompt', desc: 'Scrivi tu il prompt' },
                          { id: 'classic', label: 'Stile Classico', desc: 'Scegli uno stile' }
                        ].map(opt => (
                          <button key={opt.id} onClick={() => setPosterMode(p => ({...p, [f.id]: opt.id}))}
                            className={`flex-1 p-1.5 rounded text-center border transition-all ${(posterMode[f.id] || 'ai_auto') === opt.id ? 'border-purple-500 bg-purple-500/10' : 'border-gray-700'}`}
                            data-testid={`poster-mode-${opt.id}-${f.id}`}>
                            <p className="text-[9px] font-medium text-gray-200">{opt.label}</p>
                            <p className="text-[7px] text-gray-500">{opt.desc}</p>
                          </button>
                        ))}
                      </div>

                      {(posterMode[f.id] || 'ai_auto') === 'ai_custom' && (
                        <input type="text" placeholder="Descrivi la locandina che vuoi..."
                          value={posterPrompt[f.id] || ''} onChange={e => setPosterPrompt(p => ({...p, [f.id]: e.target.value}))}
                          className="w-full mb-1.5 text-[10px] bg-black/30 border border-gray-700 rounded p-1.5 text-white" />
                      )}

                      {(posterMode[f.id] || 'ai_auto') === 'classic' && (
                        <div className="grid grid-cols-4 gap-1 mb-1.5">
                          {CLASSIC_STYLES.map(s => (
                            <button key={s.id} onClick={() => setPosterStyle(p => ({...p, [f.id]: s.id}))}
                              className={`p-1 rounded text-center border transition-all ${(posterStyle[f.id] || 'drama') === s.id ? 'border-purple-500 bg-purple-500/10' : 'border-gray-700'}`}>
                              <p className="text-[8px] font-medium">{s.label}</p>
                              <p className="text-[7px] text-gray-500">{s.desc}</p>
                            </button>
                          ))}
                        </div>
                      )}

                      <Button size="sm" className="w-full bg-purple-700 hover:bg-purple-800 text-[10px] h-7"
                        onClick={() => generatePoster(f.id)} disabled={posterLoading === f.id}
                        data-testid={`generate-poster-${f.id}`}>
                        {posterLoading === f.id ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Sparkles className="w-3 h-3 mr-1" />}
                        Crea Locandina
                      </Button>
                    </>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="flex gap-1.5">
                  {[
                    { id: 'ai', label: 'AI ($80K)', desc: 'Sceneggiatura generata da AI' },
                    { id: 'pre_only', label: 'Solo Pre ($0)', desc: 'Malus -15% qualita' },
                    { id: 'manual', label: 'Scrivi ($20K)', desc: 'Scrivi tu la sceneggiatura' }
                  ].map(opt => (
                    <button key={opt.id} onClick={() => setMode(prev => ({ ...prev, [f.id]: opt.id }))}
                      className={`flex-1 p-2 rounded text-center border transition-all ${(mode[f.id] || 'ai') === opt.id ? 'border-cyan-500 bg-cyan-500/10' : 'border-gray-700'}`}>
                      <p className="text-[10px] font-medium text-gray-200">{opt.label}</p>
                      <p className="text-[8px] text-gray-500">{opt.desc}</p>
                    </button>
                  ))}
                </div>

                {(mode[f.id] || 'ai') === 'manual' && (
                  <Textarea value={manualText[f.id] || ''} onChange={e => setManualText(prev => ({ ...prev, [f.id]: e.target.value }))}
                    placeholder="Scrivi la sceneggiatura completa basandoti sulla pre-sceneggiatura sopra..."
                    className="bg-black/30 border-gray-700 text-white min-h-[100px] text-xs" />
                )}

                <Button onClick={() => writeScreenplay(f.id)} disabled={actionLoading === f.id}
                  className="w-full bg-cyan-700 hover:bg-cyan-800 text-xs" data-testid={`write-screenplay-${f.id}`}>
                  {actionLoading === f.id ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <BookOpen className="w-3 h-3 mr-1" />}
                  {(mode[f.id] || 'ai') === 'ai' ? 'Genera Sceneggiatura AI' : (mode[f.id] || 'ai') === 'manual' ? 'Salva Sceneggiatura' : 'Usa Solo Pre-Sceneggiatura'}
                </Button>
              </>
            )}
            </>
            )}
          </CardContent>
        </Card>
      );
        } catch (renderError) {
          // If ANY rendering error occurs for this film, show a safe fallback
          return (
            <Card key={f.id || Math.random()} className="bg-[#1A1A1B] border-red-800/30">
              <CardContent className="p-3 text-center">
                <p className="text-xs text-red-400">Errore nel rendering del film "{f.title || '?'}"</p>
                <p className="text-[9px] text-gray-500 mt-1">{String(renderError?.message || renderError)}</p>
                <Button size="sm" variant="outline" className="text-[10px] border-red-800/50 text-red-400 mt-2"
                  onClick={async () => {
                    setActionLoading(`discard-${f.id}`);
                    try { const res = await api.post(`/film-pipeline/${f.id}/discard`); toast.success(res.data.message); refreshUser(); refreshCounts(); fetch(); }
                    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
                  }}>
                  <ThumbsDown className="w-3 h-3 mr-1" /> Scarta questo progetto
                </Button>
              </CardContent>
            </Card>
          );
        }
      })}
    </div>
  );
};

// ============ PRE-PRODUCTION TAB ============
const PreProductionTab = ({ api, refreshUser, refreshCounts }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [setupFilm, setSetupFilm] = useState(null);
  const [prodOptions, setProdOptions] = useState(null);
  const [extrasCount, setExtrasCount] = useState(200);
  const [selectedCGI, setSelectedCGI] = useState([]);
  const [selectedVFX, setSelectedVFX] = useState([]);
  // Sponsor states
  const [sponsorOpen, setSponsorOpen] = useState(null);
  const [sponsorOffers, setSponsorOffers] = useState([]);
  const [selectedSponsors, setSelectedSponsors] = useState({});
  const [maxSponsors, setMaxSponsors] = useState(1);
  const [sponsorLoading, setSponsorLoading] = useState(false);

  const openSponsors = async (filmId) => {
    setSponsorOpen(filmId);
    try {
      const res = await api.get(`/film-pipeline/${filmId}/sponsor-offers`);
      setSponsorOffers(res.data.offers || []);
      setMaxSponsors(res.data.max_sponsors || 1);
      const sel = {};
      (res.data.selected || []).forEach(s => { sel[s.id] = true; });
      setSelectedSponsors(sel);
    } catch (e) { toast.error('Errore caricamento sponsor'); }
  };

  const saveSponsors = async (filmId) => {
    setSponsorLoading(true);
    try {
      const ids = Object.keys(selectedSponsors).filter(k => selectedSponsors[k]);
      const res = await api.post(`/film-pipeline/${filmId}/select-sponsors`, { sponsor_ids: ids });
      toast.success(res.data.message);
      setSponsorOpen(null);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setSponsorLoading(false); }
  };

  const fetch = useCallback(async () => {
    try { const res = await api.get('/film-pipeline/pre-production'); setFilms(res.data.films || []); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); const i = setInterval(fetch, 60000); return () => clearInterval(i); }, [fetch]);

  const openSetup = async (film) => {
    setSetupFilm(film);
    try {
      const res = await api.get(`/film-pipeline/production-options/${film.genre}`);
      setProdOptions(res.data);
      setExtrasCount(res.data.extras_optimal?.sweet || 200);
      setSelectedCGI([]);
      setSelectedVFX([]);
    } catch (e) { toast.error('Errore caricamento opzioni'); }
  };

  const submitSetup = async () => {
    if (!setupFilm) return;
    setActionLoading(`setup-${setupFilm.id}`);
    try {
      const res = await api.post(`/film-pipeline/${setupFilm.id}/production-setup`, {
        extras_count: extrasCount, cgi_packages: selectedCGI, vfx_packages: selectedVFX
      });
      toast.success(res.data.message);
      setSetupFilm(null);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const toggleCGI = (id) => setSelectedCGI(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  const toggleVFX = (id) => setSelectedVFX(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const remaster = async (filmId) => {
    setActionLoading(`rem-${filmId}`);
    try { const res = await api.post(`/film-pipeline/${filmId}/remaster`); toast.success(res.data.message); refreshUser(); fetch(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
  };

  const speedUpRemaster = async (filmId) => {
    setActionLoading(`speed-${filmId}`);
    try { const res = await api.post(`/film-pipeline/${filmId}/speed-up-remaster`); toast.success(res.data.message); refreshUser(); fetch(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
  };

  const startShooting = async (filmId) => {
    setActionLoading(`shoot-${filmId}`);
    try { const res = await api.post(`/film-pipeline/${filmId}/start-shooting`); toast.success(res.data.message); refreshUser(); refreshCounts(); fetch(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
  };

  const totalSetupCost = () => {
    if (!prodOptions) return 0;
    const extrasCost = extrasCount * (prodOptions.extras_cost_per_person || 500);
    const cgiCost = (prodOptions.cgi_packages || []).filter(p => selectedCGI.includes(p.id)).reduce((s, p) => s + p.cost, 0);
    const vfxCost = (prodOptions.vfx_packages || []).filter(p => selectedVFX.includes(p.id)).reduce((s, p) => s + p.cost, 0);
    return extrasCost + cgiCost + vfxCost;
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;
  if (!films.length) return <div className="text-center py-12 text-gray-500"><Clapperboard className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessun film in pre-produzione.</p></div>;

  return (
    <div className="space-y-3">
      {films.map(f => {
        const remasterInProgress = f.remaster_started_at && !f.remaster_completed;
        const remasterDone = f.remaster_completed;
        const hasSetup = f.production_setup?.setup_completed;
        return (
          <Card key={f.id} className="bg-[#1A1A1B] border-gray-800 film-card-hover" data-testid={`preprod-film-${f.id}`}>
            <CardContent className="p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-sm">{f.title}</h3>
                  <p className="text-[10px] text-gray-500">Pre-IMDb: <span className="text-yellow-400">{f.pre_imdb_score}</span>
                    {remasterDone && <span className="text-green-400 ml-1"> +{f.remaster_quality_boost}% remaster</span>}
                  </p>
                </div>
                {hasSetup && (
                  <Badge className="bg-green-500/20 text-green-400 text-[9px]">
                    <Check className="w-3 h-3 mr-0.5" />
                    Setup OK
                  </Badge>
                )}
              </div>

              {/* Production setup summary if completed */}
              {hasSetup && (
                <div className="p-2 bg-black/30 rounded border border-gray-700 text-[10px] text-gray-400 space-y-0.5">
                  <p>Comparse: {f.production_setup.extras_count} &bull; CGI: {f.production_setup.cgi_packages?.length || 0} pacchetti &bull; VFX: {f.production_setup.vfx_packages?.length || 0} effetti</p>
                  <p>Costo produzione: <span className="text-yellow-400">${f.production_setup.total_cost?.toLocaleString()}</span></p>
                </div>
              )}

              {remasterInProgress && (
                <div className="p-2 bg-yellow-500/10 rounded border border-yellow-500/20">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <RefreshCw className="w-3 h-3 animate-spin text-yellow-400" />
                      <span className="text-[10px] text-yellow-300">Rimasterizzazione... {Math.round(f.remaster_remaining_minutes || 0)} min</span>
                    </div>
                    <Button size="sm" className="h-5 px-2 text-[9px] bg-yellow-600 hover:bg-yellow-700"
                      disabled={actionLoading === `speed-${f.id}`} onClick={() => speedUpRemaster(f.id)}>
                      <Zap className="w-2.5 h-2.5 mr-0.5" /> $40K
                    </Button>
                  </div>
                </div>
              )}

              {/* Sponsor summary if selected */}
              {f.sponsors?.length > 0 && (
                <div className="p-2 bg-cyan-500/5 rounded border border-cyan-500/20 text-[10px] text-gray-400 space-y-0.5">
                  <p className="text-[9px] text-cyan-400 font-medium">Sponsor selezionati:</p>
                  <div className="flex flex-wrap gap-1">
                    {f.sponsors.map(sp => (
                      <Badge key={sp.id} className="text-[8px] h-4" style={{ backgroundColor: sp.logo_color + '20', color: sp.logo_color, borderColor: sp.logo_color + '40' }}>
                        {sp.name}
                      </Badge>
                    ))}
                  </div>
                  <p>Incasso sponsor: <span className="text-green-400">${(f.sponsor_money || 0).toLocaleString()}</span> | Rev. share: <span className="text-red-400">{f.sponsor_rev_share_pct || 0}%</span> | Affluenza: <span className="text-blue-400">+{f.sponsor_attendance_boost_pct || 0}%</span></p>
                </div>
              )}

              {/* Sponsor selection popup */}
              {sponsorOpen === f.id && (
                <div className="p-2 mb-2 rounded border border-cyan-500/30 bg-cyan-500/5 space-y-1.5" data-testid={`sponsor-popup-${f.id}`}>
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-cyan-400">Offerte Sponsor (max {maxSponsors})</p>
                    <Button size="sm" variant="ghost" className="h-5 w-5 p-0" onClick={() => setSponsorOpen(null)}><X className="w-3 h-3" /></Button>
                  </div>
                  <p className="text-[8px] text-gray-500">Gli sponsor ti offrono denaro in cambio di una % sugli incassi. La loro fama aumenta l'affluenza al cinema (non il punteggio IMDb).</p>
                  <div className="grid grid-cols-1 gap-1 max-h-[300px] overflow-y-auto pr-1">
                    {sponsorOffers.map(sp => {
                      const isSelected = !!selectedSponsors[sp.id];
                      const selectedCount = Object.values(selectedSponsors).filter(Boolean).length;
                      const canSelect = isSelected || selectedCount < maxSponsors;
                      return (
                        <label key={sp.id} className={`flex items-center gap-2 p-1.5 rounded border cursor-pointer transition-all ${isSelected ? 'border-cyan-500 bg-cyan-500/10' : canSelect ? 'border-gray-700 hover:border-gray-600' : 'border-gray-800 opacity-40'}`}>
                          <input type="checkbox" checked={isSelected} disabled={!canSelect}
                            onChange={e => setSelectedSponsors(p => ({...p, [sp.id]: e.target.checked}))}
                            className="accent-cyan-500 w-3 h-3" data-testid={`sponsor-check-${sp.id}`} />
                          <div className="w-5 h-5 rounded-full flex-shrink-0" style={{ backgroundColor: sp.logo_color }} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1">
                              <span className="text-[10px] font-medium">{sp.name}</span>
                              <Badge className="text-[7px] h-3 bg-gray-600/20 text-gray-400">{sp.category}</Badge>
                            </div>
                            <div className="flex items-center gap-2 text-[8px] text-gray-500">
                              <span>Fama: {sp.fame}</span>
                              <span className="text-red-400">Rev. share: {sp.revenue_share_pct}%</span>
                              <span className="text-blue-400">Affluenza: +{sp.attendance_boost_pct}%</span>
                            </div>
                          </div>
                          <span className="text-[9px] text-green-400 font-medium whitespace-nowrap">${(sp.offer_amount / 1000).toFixed(0)}K</span>
                        </label>
                      );
                    })}
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="text-[9px] text-gray-400">
                      <span>Selezionati: <span className="text-cyan-400">{Object.values(selectedSponsors).filter(Boolean).length}/{maxSponsors}</span></span>
                      <span className="ml-2">Incasso: <span className="text-green-400">${(sponsorOffers.filter(s => selectedSponsors[s.id]).reduce((sum, s) => sum + s.offer_amount, 0) / 1000).toFixed(0)}K</span></span>
                      <span className="ml-2">Rev. share tot: <span className="text-red-400">{sponsorOffers.filter(s => selectedSponsors[s.id]).reduce((sum, s) => sum + s.revenue_share_pct, 0).toFixed(1)}%</span></span>
                    </div>
                    <Button size="sm" className="bg-cyan-700 hover:bg-cyan-800 text-[10px] h-6"
                      onClick={() => saveSponsors(f.id)} disabled={sponsorLoading || Object.values(selectedSponsors).filter(Boolean).length === 0}
                      data-testid={`save-sponsors-${f.id}`}>
                      {sponsorLoading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 mr-0.5" />} Conferma
                    </Button>
                  </div>
                </div>
              )}

              <div className="flex gap-2 flex-wrap">
                {!hasSetup && (
                  <Button size="sm" variant="outline" className="text-xs border-orange-700 text-orange-400"
                    onClick={() => openSetup(f)} data-testid={`setup-${f.id}`}>
                    <Settings className="w-3 h-3 mr-1" /> Setup Produzione
                  </Button>
                )}
                <Button size="sm" variant="outline" className="text-xs border-cyan-700 text-cyan-400"
                  onClick={() => openSponsors(f.id)} data-testid={`sponsors-btn-${f.id}`}>
                  <DollarSign className="w-3 h-3 mr-0.5" /> Sponsor
                  {f.sponsors?.length > 0 && <Badge className="ml-1 bg-green-500/20 text-green-400 text-[8px] h-4">{f.sponsors.length}</Badge>}
                </Button>
                {!f.remaster_started_at && (
                  <Button size="sm" variant="outline" className="text-xs border-yellow-700 text-yellow-400"
                    disabled={actionLoading === `rem-${f.id}`} onClick={() => remaster(f.id)} data-testid={`remaster-${f.id}`}>
                    <Star className="w-3 h-3 mr-1" /> Rimasterizza
                  </Button>
                )}
                <Button size="sm" className="flex-1 bg-red-700 hover:bg-red-800 text-xs"
                  disabled={remasterInProgress || actionLoading === `shoot-${f.id}`}
                  onClick={() => startShooting(f.id)} data-testid={`ciak-${f.id}`}>
                  <Play className="w-3 h-3 mr-1" /> Ciak! (3 CP)
                </Button>
                <Button size="sm" variant="outline" className="text-[10px] border-red-800/50 text-red-400 hover:bg-red-500/10 h-8 px-2"
                  disabled={actionLoading === `discard-${f.id}`}
                  onClick={async () => {
                    setActionLoading(`discard-${f.id}`);
                    try { const res = await api.post(`/film-pipeline/${f.id}/discard`); toast.success(res.data.message); refreshUser(); refreshCounts(); fetch(); }
                    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
                  }}
                  data-testid={`discard-preprod-${f.id}`}>
                  {actionLoading === `discard-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ThumbsDown className="w-3 h-3 mr-0.5" />}
                  Scarta
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}

      {/* Production Setup Dialog */}
      <Dialog open={!!setupFilm} onOpenChange={() => setSetupFilm(null)}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-lg max-h-[80vh] overflow-y-auto">
          {setupFilm && prodOptions && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 text-base">
                  <Settings className="w-5 h-5 text-orange-400" />
                  Setup Produzione - {setupFilm.title}
                </DialogTitle>
                <DialogDescription>Configura comparse, CGI e effetti speciali. Solo denaro, niente crediti.</DialogDescription>
              </DialogHeader>

              <div className="space-y-4 mt-2">
                {/* EXTRAS SLIDER */}
                <div>
                  <label className="text-xs font-medium flex items-center gap-1 mb-2">
                    <Users className="w-3.5 h-3.5 text-blue-400" />
                    Comparse: <span className="text-yellow-400">{extrasCount}</span>
                    <span className="text-gray-500 text-[9px] ml-auto">
                      (Ottimale: {prodOptions.extras_optimal.min}-{prodOptions.extras_optimal.max})
                    </span>
                  </label>
                  <input type="range" min={50} max={1000} step={10} value={extrasCount}
                    onChange={e => setExtrasCount(parseInt(e.target.value))}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-500 bg-gray-700"
                    data-testid="extras-slider" />
                  <div className="flex justify-between text-[8px] text-gray-500 mt-0.5">
                    <span>50</span>
                    <span className="text-green-400">Sweet spot: {prodOptions.extras_optimal.sweet}</span>
                    <span>1000</span>
                  </div>
                  <p className="text-[9px] text-gray-500 mt-0.5">Costo: ${(extrasCount * prodOptions.extras_cost_per_person).toLocaleString()}</p>
                </div>

                {/* CGI PACKAGES */}
                <div>
                  <label className="text-xs font-medium flex items-center gap-1 mb-2">
                    <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                    Pacchetti CGI
                  </label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {(prodOptions.cgi_packages || []).map(pkg => (
                      <button key={pkg.id} onClick={() => toggleCGI(pkg.id)}
                        className={`p-2 rounded text-left border transition-all ${selectedCGI.includes(pkg.id) ? 'border-purple-500 bg-purple-500/10' : 'border-gray-700 hover:border-gray-600'}`}
                        data-testid={`cgi-${pkg.id}`}>
                        <p className="text-[10px] font-medium">{pkg.name}</p>
                        <p className="text-[8px] text-gray-500">{pkg.desc}</p>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-[9px] text-yellow-400">${(pkg.cost / 1000).toFixed(0)}K</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* VFX PACKAGES */}
                <div>
                  <label className="text-xs font-medium flex items-center gap-1 mb-2">
                    <Wand2 className="w-3.5 h-3.5 text-cyan-400" />
                    Effetti Speciali (VFX)
                  </label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {(prodOptions.vfx_packages || []).map(pkg => (
                      <button key={pkg.id} onClick={() => toggleVFX(pkg.id)}
                        className={`p-2 rounded text-left border transition-all ${selectedVFX.includes(pkg.id) ? 'border-cyan-500 bg-cyan-500/10' : 'border-gray-700 hover:border-gray-600'}`}
                        data-testid={`vfx-${pkg.id}`}>
                        <p className="text-[10px] font-medium">{pkg.name}</p>
                        <p className="text-[8px] text-gray-500">{pkg.desc}</p>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-[9px] text-yellow-400">${(pkg.cost / 1000).toFixed(0)}K</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* TOTAL COST */}
                <div className="flex items-center justify-between p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                  <div>
                    <p className="text-xs font-medium">Costo Totale</p>
                    <p className="text-[9px] text-gray-400">Solo denaro, niente crediti</p>
                  </div>
                  <p className="text-lg font-bold text-yellow-400">${totalSetupCost().toLocaleString()}</p>
                </div>

                <Button className="w-full bg-orange-600 hover:bg-orange-700" onClick={submitSetup}
                  disabled={actionLoading === `setup-${setupFilm.id}`} data-testid="confirm-setup">
                  {actionLoading === `setup-${setupFilm.id}` ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : <Check className="w-4 h-4 mr-1" />}
                  Conferma Setup Produzione
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ============ SHOOTING TAB ============
const ShootingTab = ({ api, refreshUser, refreshCounts }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [releaseResult, setReleaseResult] = useState(null);
  const [releasePhase, setReleasePhase] = useState(0);
  const [trailerSlide, setTrailerSlide] = useState(0);
  const [animatedQuality, setAnimatedQuality] = useState(0);
  const [animatedRevenue, setAnimatedRevenue] = useState(0);
  const [releaseStrategy, setReleaseStrategy] = useState({});
  const [manualHours, setManualHours] = useState({});

  const fetch = useCallback(async () => {
    try { const res = await api.get('/film-pipeline/shooting'); setFilms(res.data.films || []); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); const i = setInterval(fetch, 45000); return () => clearInterval(i); }, [fetch]);

  const speedUp = async (filmId, option) => {
    setActionLoading(`speed-${filmId}`);
    try { const res = await api.post(`/film-pipeline/${filmId}/speed-up-shooting`, { option }); toast.success(res.data.message); refreshUser(); fetch(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
  };

  const release = async (filmId) => {
    setActionLoading(`rel-${filmId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/release`, {}, { timeout: 60000 });
      const data = res.data;
      setReleaseResult(data);
      setTrailerSlide(0);
      setAnimatedQuality(0);
      setAnimatedRevenue(0);
      
      // 5-phase cinematic sequence
      const hasTrailer = data.screenplay_scenes && data.screenplay_scenes.length > 0;
      const hasEvent = data.release_event && data.release_event.id !== 'nothing_special';
      
      // Phase 1: Intro (cinema image + "il tuo film sta uscendo...")
      setReleasePhase(1);
      
      // Phase 2: Trailer slideshow (if available)
      const trailerDelay = 2000;
      if (hasTrailer) {
        setTimeout(() => {
          setReleasePhase(2);
          // Advance slides
          const scenes = data.screenplay_scenes;
          scenes.forEach((_, i) => {
            setTimeout(() => setTrailerSlide(i), i * 800);
          });
        }, trailerDelay);
      }
      
      // Phase 3: Event reveal
      const eventDelay = hasTrailer ? trailerDelay + (data.screenplay_scenes.length * 800) + 400 : trailerDelay;
      if (hasEvent) {
        setTimeout(() => setReleasePhase(3), eventDelay);
      }
      
      // Phase 4: Animated numbers
      const numbersDelay = hasEvent ? eventDelay + 2000 : eventDelay;
      setTimeout(() => {
        setReleasePhase(4);
        // Animate quality score counting up
        const targetQ = Math.round(data.quality_score);
        const targetR = Math.round(data.opening_day_revenue || 0);
        const steps = 30;
        for (let i = 1; i <= steps; i++) {
          setTimeout(() => {
            setAnimatedQuality(Math.round((targetQ / steps) * i));
            setAnimatedRevenue(Math.round((targetR / steps) * i));
          }, i * 40);
        }
      }, numbersDelay);
      
      // Phase 5: Final result
      setTimeout(() => setReleasePhase(5), numbersDelay + 1500);
      
      refreshUser(); refreshCounts(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore nel rilascio'); }
    finally { setActionLoading(null); }
  };

  const confirmStrategy = async (filmId) => {
    const strategy = releaseStrategy[filmId];
    if (!strategy) return;
    const hours = strategy === 'manual' ? (manualHours[filmId] || 24) : 24;
    setActionLoading(`strategy-${filmId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/choose-release-strategy`, { strategy, hours });
      const d = res.data;
      const bonusMsg = d.bonus_pct > 0 ? ` Bonus: +${d.bonus_pct}%` : '';
      const perfectMsg = d.perfect_timing ? ' Tempismo perfetto!' : '';
      toast.success(`Strategia confermata! Uscita tra ${d.hours_until_release}h.${bonusMsg}${perfectMsg}`);
      refreshUser(); refreshCounts(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;

  return (
    <div className="space-y-3">
      {films.length === 0 && !releaseResult && (
        <div className="text-center py-12 text-gray-500"><Play className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessun film in ripresa.</p></div>
      )}

      {films.map(f => {
        const progress = Math.min(100, ((f.shooting_day_current || 0) / Math.max(1, f.shooting_days || 5)) * 100);
        const completed = f.shooting_completed || progress >= 100;
        return (
          <Card key={f.id} className={`bg-[#1A1A1B] ${completed ? 'border-green-800' : 'border-gray-800'}`} data-testid={`shooting-film-${f.id}`}>
            <CardContent className="p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-sm">{f.title}</h3>
                  <p className="text-[10px] text-gray-500">
                    Giorno {f.shooting_day_current || 0}/{f.shooting_days || 5}
                    {!completed && f.shooting_hours_remaining != null && <span> &bull; ~{Math.round(f.shooting_hours_remaining * 60)}min rimanenti</span>}
                  </p>
                </div>
                {completed ? (
                  <Badge className="bg-green-500/20 text-green-400 text-[10px]">Completato!</Badge>
                ) : (
                  <Badge className="bg-blue-500/20 text-blue-400 text-[10px]">{Math.round(progress)}%</Badge>
                )}
              </div>

              {/* Progress bar */}
              <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all bg-gradient-to-r from-blue-500 to-green-500" style={{ width: `${progress}%` }} />
              </div>

              {completed ? (
                <div className="flex gap-1.5 flex-wrap">
                  {/* La Prima — solo per film pronti al rilascio */}
                  {(f.status === 'prima' || f.status === 'pending_release') && (
                    <div className="w-full mb-1">
                      <LaPremiereSection
                        filmId={f.id}
                        project={f}
                      />
                    </div>
                  )}
                  {f.release_type === 'coming_soon' ? (
                    <div className="w-full space-y-2" data-testid={`release-strategy-${f.id}`}>
                      <p className="text-xs font-bold text-white">Strategia di Uscita</p>

                      {/* Automatica */}
                      <div
                        className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                          releaseStrategy[f.id] === 'auto'
                            ? 'border-yellow-500/60 bg-yellow-500/10'
                            : 'border-gray-700/60 hover:border-gray-600'
                        }`}
                        onClick={() => setReleaseStrategy(s => ({...s, [f.id]: 'auto'}))}
                        data-testid={`strategy-auto-${f.id}`}>
                        <div className="flex items-start gap-2">
                          <Zap className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-[11px] font-bold text-white">Automatica</p>
                            <p className="text-[9px] text-gray-500">Il sistema decide il momento migliore</p>
                            <p className="text-[9px] text-emerald-400 mt-0.5">+3% incassi garantiti</p>
                          </div>
                        </div>
                      </div>

                      {/* Manuale */}
                      <div
                        className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                          releaseStrategy[f.id] === 'manual'
                            ? 'border-cyan-500/60 bg-cyan-500/10'
                            : 'border-gray-700/60 hover:border-gray-600'
                        }`}
                        onClick={() => setReleaseStrategy(s => ({...s, [f.id]: 'manual'}))}
                        data-testid={`strategy-manual-${f.id}`}>
                        <div className="flex items-start gap-2">
                          <Target className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                          <div className="flex-1">
                            <p className="text-[11px] font-bold text-white">Manuale</p>
                            <p className="text-[9px] text-gray-500">Scegli quando uscire</p>
                            <p className="text-[9px] text-amber-400 mt-0.5">Tempismo perfetto: +8% incassi!</p>
                          </div>
                        </div>
                        {releaseStrategy[f.id] === 'manual' && (
                          <div className="mt-2 grid grid-cols-4 gap-1.5 ml-6" data-testid={`manual-hours-${f.id}`}>
                            {[6, 12, 24, 48].map(h => (
                              <button key={h}
                                className={`py-1.5 rounded text-[10px] font-medium border transition-all ${
                                  manualHours[f.id] === h
                                    ? 'border-cyan-500 bg-cyan-500/15 text-cyan-400'
                                    : 'border-gray-700 text-gray-400 hover:border-gray-500'
                                }`}
                                onClick={(e) => { e.stopPropagation(); setManualHours(s => ({...s, [f.id]: h})); }}
                                data-testid={`manual-${h}h-${f.id}`}>
                                {h}h
                              </button>
                            ))}
                          </div>
                        )}
                      </div>

                      <Button
                        className="w-full bg-gradient-to-r from-yellow-600 to-amber-600 hover:from-yellow-500 hover:to-amber-500 text-white text-xs font-bold"
                        disabled={!releaseStrategy[f.id] || (releaseStrategy[f.id] === 'manual' && !manualHours[f.id]) || actionLoading === `strategy-${f.id}`}
                        onClick={() => confirmStrategy(f.id)}
                        data-testid={`confirm-strategy-${f.id}`}>
                        {actionLoading === `strategy-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
                        Conferma Strategia
                      </Button>
                    </div>
                  ) : (
                    <Button className="flex-1 bg-green-700 hover:bg-green-800 text-xs" disabled={actionLoading === `rel-${f.id}`}
                      onClick={() => release(f.id)} data-testid={`release-${f.id}`}>
                      {actionLoading === `rel-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Film className="w-3 h-3 mr-1" />}
                      Rilascia al Cinema!
                    </Button>
                  )}
                  <Button size="sm" variant="outline" className="text-[10px] border-red-800/50 text-red-400 hover:bg-red-500/10 px-2"
                    disabled={actionLoading === `discard-${f.id}`}
                    onClick={async () => {
                      if (!window.confirm(`Scartare "${f.title}"?`)) return;
                      setActionLoading(`discard-${f.id}`);
                      try { const res = await api.post(`/film-pipeline/${f.id}/discard`); toast.success(res.data.message); refreshUser(); refreshCounts(); fetch(); }
                      catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
                    }}
                    data-testid={`discard-shooting-${f.id}`}>
                    <ThumbsDown className="w-3 h-3 mr-0.5" /> Scarta
                  </Button>
                </div>
              ) : (
                <div className="space-y-1.5">
                  <div className="flex gap-1.5">
                    <Button size="sm" variant="outline" className="flex-1 text-[9px] border-gray-700" disabled={actionLoading === `speed-${f.id}`}
                      onClick={() => speedUp(f.id, 'fast')}>
                      <Zap className="w-2.5 h-2.5 mr-0.5" /> 50% ($50K)
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1 text-[9px] border-yellow-700 text-yellow-400" disabled={actionLoading === `speed-${f.id}`}
                      onClick={() => speedUp(f.id, 'faster')}>
                      <Zap className="w-2.5 h-2.5 mr-0.5" /> 80% ($90K)
                    </Button>
                    <Button size="sm" className="flex-1 text-[9px] bg-red-700 hover:bg-red-800" disabled={actionLoading === `speed-${f.id}`}
                      onClick={() => speedUp(f.id, 'instant')}>
                      <Zap className="w-2.5 h-2.5 mr-0.5" /> Subito! ($150K)
                    </Button>
                  </div>
                  <Button size="sm" variant="outline" className="w-full text-[10px] border-red-800/50 text-red-400 hover:bg-red-500/10"
                    disabled={actionLoading === `discard-${f.id}`}
                    onClick={async () => {
                      if (!window.confirm(`Scartare "${f.title}"?`)) return;
                      setActionLoading(`discard-${f.id}`);
                      try { const res = await api.post(`/film-pipeline/${f.id}/discard`); toast.success(res.data.message); refreshUser(); refreshCounts(); fetch(); }
                      catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
                    }}
                    data-testid={`discard-shooting-${f.id}`}>
                    {actionLoading === `discard-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ThumbsDown className="w-3 h-3 mr-0.5" />}
                    Scarta
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}

      {/* Cinematic Release Experience */}
      {releaseResult && releasePhase > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3" data-testid="release-result">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/95 backdrop-blur-lg" 
            style={{ animation: 'fadeIn 0.5s ease-out' }}
            onClick={() => { if (releasePhase >= 5) { setReleaseResult(null); setReleasePhase(0); } }} />

          <div className="relative w-full max-w-sm z-10 max-h-[92vh] overflow-y-auto rounded-xl" style={{ scrollbarWidth: 'none' }}>
            
            {/* ===== PHASE 1: INTRO - Cinema Image + "Il tuo film sta uscendo..." ===== */}
            <div className={`relative w-full overflow-hidden rounded-t-xl ${
              releaseResult.release_outcome === 'success' ? 'ring-2 ring-yellow-500/60' : ''
            }`} data-testid="release-intro">
              <div className="aspect-[16/10] relative overflow-hidden">
                <img 
                  src={releaseResult.release_image || '/assets/release/cinema_normal.jpg'}
                  alt="Cinema" 
                  className={`w-full h-full object-cover ${
                    releaseResult.release_outcome === 'flop' ? 'saturate-[0.4] brightness-75' : 
                    releaseResult.release_outcome === 'success' ? 'brightness-110' : ''
                  }`}
                  style={{ 
                    animation: releaseResult.release_outcome === 'success' 
                      ? 'successZoom 1.5s ease-out both' 
                      : releaseResult.release_outcome === 'flop'
                      ? 'flopFade 1.2s ease-out both'
                      : 'slowZoom 8s ease-out both'
                  }}
                  data-testid="release-image"
                />
                {/* Gradient overlay */}
                <div className={`absolute inset-0 ${
                  releaseResult.release_outcome === 'success' 
                    ? 'bg-gradient-to-t from-black via-black/30 to-transparent' 
                    : releaseResult.release_outcome === 'flop'
                    ? 'bg-gradient-to-t from-black via-black/50 to-blue-950/30'
                    : 'bg-gradient-to-t from-black via-black/40 to-transparent'
                }`} />
                {/* Glow for success */}
                {releaseResult.release_outcome === 'success' && (
                  <div className="absolute inset-0 pointer-events-none" 
                    style={{ animation: 'glowPulse 2s ease-in-out infinite' }} />
                )}
                {/* Intro text */}
                <div className="absolute bottom-0 left-0 right-0 p-4 text-center">
                  {releasePhase === 1 && (
                    <p className="text-sm text-white/80 italic" style={{ animation: 'fadeIn 0.8s ease-out 0.3s both' }}>
                      Il tuo film sta uscendo nelle sale...
                    </p>
                  )}
                  {releasePhase >= 2 && (
                    <>
                      <h1 className="text-xl font-black text-white tracking-tight leading-tight"
                        style={{ animation: 'scaleIn 0.5s ease-out both' }}>
                        {releaseResult.title}
                      </h1>
                      {releaseResult.director_name && (
                        <p className="text-[10px] text-yellow-400/70 mt-0.5 uppercase tracking-[0.2em]"
                          style={{ animation: 'fadeIn 0.4s ease-out 0.3s both' }}>
                          Un film di {releaseResult.director_name}
                        </p>
                      )}
                    </>
                  )}
                  {/* Hype indicator */}
                  {releaseResult.hype_level > 0 && releasePhase <= 2 && (
                    <div className="mt-2 flex items-center justify-center gap-1.5" style={{ animation: 'fadeIn 0.5s ease-out 0.6s both' }}>
                      <div className="h-1 bg-white/10 rounded-full w-24 overflow-hidden">
                        <div className={`h-full rounded-full ${
                          releaseResult.hype_level >= 60 ? 'bg-yellow-400' : releaseResult.hype_level >= 30 ? 'bg-amber-500' : 'bg-gray-400'
                        }`} style={{ width: `${releaseResult.hype_level}%`, transition: 'width 1s ease-out' }} />
                      </div>
                      <span className="text-[9px] text-white/40">Hype {releaseResult.hype_level}%</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ===== PHASE 2: VISUAL TRAILER - Screenplay Storyboard ===== */}
            {releasePhase >= 2 && releaseResult.screenplay_scenes?.length > 0 && (
              <div className="bg-black/80 px-4 py-3 border-x border-white/5" data-testid="release-trailer">
                <p className="text-[9px] text-white/30 uppercase tracking-[0.2em] text-center mb-2"
                  style={{ animation: 'fadeIn 0.4s ease-out both' }}>
                  Anteprima Sceneggiatura
                </p>
                <div className="relative h-12 overflow-hidden">
                  {releaseResult.screenplay_scenes.map((scene, i) => (
                    <p key={i} className={`absolute inset-0 flex items-center justify-center text-center text-[11px] leading-relaxed italic transition-all duration-500 ${
                      trailerSlide === i ? 'opacity-100 translate-y-0' : trailerSlide > i ? 'opacity-0 -translate-y-4' : 'opacity-0 translate-y-4'
                    } ${
                      releaseResult.release_outcome === 'success' ? 'text-yellow-200/80' :
                      releaseResult.release_outcome === 'flop' ? 'text-blue-200/60' : 'text-gray-300/70'
                    }`}>
                      "{scene.length > 80 ? scene.substring(0, 80) + '...' : scene}"
                    </p>
                  ))}
                </div>
                {/* Slide dots */}
                <div className="flex justify-center gap-1 mt-1.5">
                  {releaseResult.screenplay_scenes.map((_, i) => (
                    <div key={i} className={`w-1 h-1 rounded-full transition-all duration-300 ${
                      trailerSlide >= i ? 'bg-white/50 scale-110' : 'bg-white/15'
                    }`} />
                  ))}
                </div>
              </div>
            )}

            {/* ===== PHASE 3: EVENT REVEAL ===== */}
            {releasePhase >= 3 && releaseResult.release_event && releaseResult.release_event.id !== 'nothing_special' && (() => {
              const evt = releaseResult.release_event;
              const isRare = evt.rarity === 'rare';
              const borderColor = evt.type === 'positive' ? 'border-emerald-500' : evt.type === 'negative' ? 'border-red-500' : 'border-amber-500';
              const glowColor = evt.type === 'positive' ? 'shadow-emerald-500/40' : evt.type === 'negative' ? 'shadow-red-500/40' : 'shadow-amber-500/40';
              const bgGrad = evt.type === 'positive' ? 'from-emerald-950/80 to-[#0a0a0b]' : evt.type === 'negative' ? 'from-red-950/80 to-[#0a0a0b]' : 'from-amber-950/80 to-[#0a0a0b]';
              const accentColor = evt.type === 'positive' ? 'text-emerald-400' : evt.type === 'negative' ? 'text-red-400' : 'text-amber-400';
              return (
                <div className={`relative border-x-2 border-b ${borderColor} bg-gradient-to-b ${bgGrad} p-3 shadow-lg ${glowColor} ${isRare ? 'ring-1 ring-purple-500/50' : ''}`}
                  style={{ animation: isRare ? 'shakeIn 0.7s ease-out both' : 'eventReveal 0.8s ease-out both' }}
                  data-testid="release-event">
                  {isRare && <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/10 to-transparent" style={{ animation: 'shimmer 2s ease-in-out infinite' }} />
                  </div>}
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      evt.type === 'positive' ? 'bg-emerald-500/20' : evt.type === 'negative' ? 'bg-red-500/20' : 'bg-amber-500/20'
                    }`} style={{ animation: 'pulse 1.5s ease-in-out infinite' }}>
                      <span className="text-lg">{evt.type === 'positive' ? '⚡' : evt.type === 'negative' ? '💥' : '🔀'}</span>
                    </div>
                    <div className="text-center">
                      {isRare && <Badge className="bg-purple-500/30 text-purple-300 text-[7px] mb-0.5 border border-purple-500/40">EVENTO RARO</Badge>}
                      <h3 className={`text-xs font-black ${accentColor} uppercase tracking-wider`}>{evt.name}</h3>
                    </div>
                  </div>
                  <p className="text-[10px] text-gray-300 text-center leading-relaxed mb-2">{evt.description}</p>
                  <div className="flex justify-center gap-3 text-[10px] font-bold">
                    {evt.quality_modifier !== 0 && (
                      <div className={`px-2 py-0.5 rounded-full ${evt.quality_modifier > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                        Qualita {evt.quality_modifier > 0 ? '+' : ''}{evt.quality_modifier}
                      </div>
                    )}
                    {evt.revenue_modifier !== 0 && (
                      <div className={`px-2 py-0.5 rounded-full ${evt.revenue_modifier > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                        Incassi {evt.revenue_modifier > 0 ? '+' : ''}{evt.revenue_modifier}%
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}

            {/* ===== PHASE 4: ANIMATED NUMBERS ===== */}
            {releasePhase >= 4 && (
              <div className="bg-[#0d0d0e] px-4 py-3 border-x border-white/5" style={{ animation: 'slideUp 0.6s ease-out both' }}
                data-testid="release-numbers">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <div className={`text-2xl font-black tabular-nums ${
                      releaseResult.quality_score >= 70 ? 'text-green-400' : releaseResult.quality_score >= 50 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {animatedQuality}
                    </div>
                    <p className="text-[8px] text-gray-500 uppercase tracking-wide">Qualità</p>
                  </div>
                  <div>
                    <div className="text-2xl font-black tabular-nums text-yellow-400">
                      {releaseResult.imdb_rating?.toFixed?.(1) || '—'}
                    </div>
                    <p className="text-[8px] text-gray-500 uppercase tracking-wide">IMDb</p>
                  </div>
                  <div>
                    <div className="text-2xl font-black tabular-nums text-green-400">
                      ${animatedRevenue > 999999 ? (animatedRevenue / 1000000).toFixed(1) + 'M' : animatedRevenue > 999 ? (animatedRevenue / 1000).toFixed(0) + 'K' : animatedRevenue}
                    </div>
                    <p className="text-[8px] text-gray-500 uppercase tracking-wide">Apertura</p>
                  </div>
                </div>
                {/* Tier badge */}
                <div className="flex justify-center mt-2">
                  <Badge className={`text-[10px] px-3 py-0.5 ${
                    releaseResult.tier === 'masterpiece' ? 'bg-yellow-500 text-black' :
                    releaseResult.tier === 'epic' ? 'bg-purple-500/30 text-purple-300' :
                    releaseResult.tier === 'excellent' ? 'bg-green-500/30 text-green-300' :
                    releaseResult.tier === 'good' ? 'bg-blue-500/30 text-blue-300' :
                    releaseResult.tier === 'flop' ? 'bg-red-500/30 text-red-300' : 'bg-gray-600'
                  }`} style={{ animation: 'scaleIn 0.4s ease-out 0.8s both' }}>
                    {releaseResult.tier_label}
                  </Badge>
                </div>
              </div>
            )}

            {/* ===== PHASE 5: FINAL RESULT ===== */}
            {releasePhase >= 5 && (
              <div className={`rounded-b-xl overflow-hidden ${
                releaseResult.release_outcome === 'success' ? 'bg-gradient-to-b from-[#0d0d0e] to-yellow-950/20' :
                releaseResult.release_outcome === 'flop' ? 'bg-gradient-to-b from-[#0d0d0e] to-blue-950/20' :
                'bg-[#0d0d0e]'
              }`} style={{ animation: 'slideUp 0.5s ease-out both' }} data-testid="release-final">
                {/* Outcome message */}
                <div className={`text-center py-3 px-4 ${
                  releaseResult.release_outcome === 'success' ? 'border-t border-yellow-500/30' :
                  releaseResult.release_outcome === 'flop' ? 'border-t border-blue-500/20' :
                  'border-t border-white/10'
                }`}>
                  <p className={`text-sm font-bold ${
                    releaseResult.release_outcome === 'success' ? 'text-yellow-400' :
                    releaseResult.release_outcome === 'flop' ? 'text-blue-300/70' : 'text-gray-300'
                  }`} style={{ animation: 'scaleIn 0.4s ease-out both' }}>
                    {releaseResult.release_outcome === 'success' ? "Evento dell'anno!" :
                     releaseResult.release_outcome === 'flop' ? "Il pubblico non ha risposto..." : "Buona accoglienza"}
                  </p>
                  <p className="text-green-400 text-xs mt-0.5">+{releaseResult.xp_gained} XP</p>
                </div>

                {/* Compact details */}
                <div className="px-3 pb-2 space-y-1.5">
                  {/* Sponsors */}
                  {releaseResult.sponsors?.length > 0 && (
                    <div className="text-[9px] text-gray-400 p-1.5 bg-black/30 rounded border border-cyan-500/10">
                      <span className="text-[9px] font-medium text-cyan-300 mr-1">Sponsor:</span>
                      {releaseResult.sponsors.map(sp => (
                        <Badge key={sp.id || sp.name} className="text-[7px] h-3 mr-0.5" style={{ backgroundColor: (sp.logo_color || '#666') + '20', color: sp.logo_color || '#aaa' }}>
                          {sp.name}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {/* Modifiers */}
                  <div className="text-[8px] text-gray-500 p-1.5 bg-black/30 rounded flex flex-wrap gap-x-2.5 gap-y-0.5">
                    <span>Pre-IMDb: {releaseResult.modifiers?.pre_imdb}</span>
                    <span>Cast: {releaseResult.modifiers?.cast_quality}</span>
                    <span>Buzz: {releaseResult.modifiers?.buzz > 0 ? '+' : ''}{releaseResult.modifiers?.buzz}</span>
                    <span>Remaster: +{releaseResult.modifiers?.remaster || 0}</span>
                  </div>
                  {/* Cost */}
                  <div className="text-[8px] text-gray-500 p-1.5 bg-black/30 rounded">
                    Denaro: <span className="text-yellow-400/80">${releaseResult.cost_summary?.total_money?.toLocaleString()}</span> | CinePass: <span className="text-cyan-400/80">{releaseResult.cost_summary?.total_cinepass} CP</span>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 px-3 pb-3">
                  <Button onClick={() => { setReleaseResult(null); setReleasePhase(0); window.location.href = `/films/${releaseResult.film_id}`; }}
                    className={`flex-1 text-xs h-9 ${
                      releaseResult.release_outcome === 'success' ? 'bg-yellow-600 hover:bg-yellow-500 text-black' :
                      releaseResult.release_outcome === 'flop' ? 'bg-blue-700 hover:bg-blue-600 text-white' :
                      'bg-amber-600 hover:bg-amber-500 text-black'
                    }`} data-testid="release-go-film">
                    <Film className="w-3 h-3 mr-1" /> Vai al Film
                  </Button>
                  <Button onClick={() => { setReleaseResult(null); setReleasePhase(0); }} variant="outline" className="border-gray-700 text-xs h-9" data-testid="release-close">
                    Chiudi
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* CSS Animations */}
          <style>{`
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            @keyframes scaleIn { from { opacity: 0; transform: scale(0.85); } to { opacity: 1; transform: scale(1); } }
            @keyframes eventReveal { from { opacity: 0; transform: scale(0.9) translateY(15px); } to { opacity: 1; transform: scale(1) translateY(0); } }
            @keyframes shakeIn { 
              0% { opacity: 0; transform: scale(0.8); }
              40% { opacity: 1; transform: scale(1.04); }
              55% { transform: scale(1) rotate(-1deg); }
              70% { transform: scale(1.02) rotate(1deg); }
              85% { transform: scale(1) rotate(-0.5deg); }
              100% { transform: scale(1) rotate(0); }
            }
            @keyframes shimmer {
              0%, 100% { transform: translateX(-100%); }
              50% { transform: translateX(100%); }
            }
            @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.08); } }
            @keyframes successZoom { 
              0% { opacity: 0; transform: scale(1.15); }
              60% { opacity: 1; transform: scale(1.02); }
              100% { opacity: 1; transform: scale(1); }
            }
            @keyframes slowZoom {
              0% { transform: scale(1); }
              100% { transform: scale(1.06); }
            }
            @keyframes flopFade { 
              0% { opacity: 0; transform: scale(0.98); }
              100% { opacity: 1; transform: scale(1); }
            }
            @keyframes glowPulse {
              0%, 100% { box-shadow: inset 0 0 40px rgba(234, 179, 8, 0.1); }
              50% { box-shadow: inset 0 0 80px rgba(234, 179, 8, 0.2); }
            }
          `}</style>
        </div>
      )}
    </div>
  );
};

// ============ BUZZ SECTION ============
const BuzzSection = ({ api, refreshUser }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState(null);

  const fetch = useCallback(async () => {
    try { const res = await api.get('/film-pipeline/buzz'); setFilms(res.data.films || []); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); }, [fetch]);

  const vote = async (filmId, voteType) => {
    setVoting(filmId);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/buzz-vote`, { vote: voteType });
      toast.success(res.data.message);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setVoting(null); }
  };

  if (loading || !films.length) return null;

  return (
    <Card className="bg-[#1A1A1B] border-purple-900/50 mt-4" data-testid="buzz-section">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-purple-400" /> Film in Arrivo — Vota l'Hype!
        </CardTitle>
        <p className="text-[10px] text-gray-500">Vota i film di altri produttori e guadagna CinePass</p>
      </CardHeader>
      <CardContent className="space-y-2">
        {films.map(f => (
          <div key={f.id} className="p-2 bg-black/30 rounded border border-purple-900/20" data-testid={`buzz-film-${f.id}`}>
            <div className="flex items-center justify-between mb-1">
              <div>
                <p className="text-xs font-medium">{f.title}</p>
                <p className="text-[9px] text-gray-500">{f.genre} &bull; di {f.owner_nickname} &bull; Pre-IMDb: {f.pre_imdb_score}</p>
              </div>
              <div className="text-[9px] text-gray-600">{f.total_votes} voti</div>
            </div>
            <p className="text-[9px] text-gray-500 italic mb-1.5">"{f.pre_screenplay}"</p>
            <div className="flex gap-1.5">
              <Button size="sm" className="flex-1 h-6 text-[9px] bg-green-700 hover:bg-green-800" disabled={voting === f.id}
                onClick={() => vote(f.id, 'high')} data-testid={`buzz-high-${f.id}`}>
                Hype!
              </Button>
              <Button size="sm" variant="outline" className="flex-1 h-6 text-[9px] border-gray-600" disabled={voting === f.id}
                onClick={() => vote(f.id, 'medium')}>
                Interessante
              </Button>
              <Button size="sm" variant="outline" className="flex-1 h-6 text-[9px] border-red-800 text-red-400" disabled={voting === f.id}
                onClick={() => vote(f.id, 'low')}>
                Meh
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

// ============ PLACEHOLDER TAB (Phase 2) ============
const PlaceholderTab = ({ icon: Icon, name }) => (
  <div className="text-center py-16 text-gray-500">
    <Icon className="w-12 h-12 mx-auto mb-3 opacity-20" />
    <p className="text-sm font-medium mb-1">{name}</p>
    <p className="text-[10px]">In arrivo nella Fase 2</p>
  </div>
);

// ============ CINEMATIC STEP CONSTANTS ============
const CINEMATIC_STEPS = [
  { id: 'idea', label: 'IDEA', icon: Lightbulb, color: 'yellow', statuses: ['draft', 'proposed'] },
  { id: 'hype', label: 'HYPE', icon: Flame, color: 'orange', statuses: ['coming_soon', 'ready_for_casting'] },
  { id: 'cast', label: 'CAST', icon: Users, color: 'cyan', statuses: ['casting'] },
  { id: 'produzione', label: 'PRODUZIONE', icon: Clapperboard, color: 'blue', statuses: ['sponsor', 'screenplay', 'pre_production', 'ciak', 'shooting'] },
  { id: 'la-prima', label: 'LA PRIMA', icon: Sparkles, color: 'gold', statuses: ['prima'] },
  { id: 'uscita', label: 'USCITA', icon: Rocket, color: 'green', statuses: ['pending_release', 'uscita'] },
];

const getCinematicStepIndex = (status) => {
  for (let i = 0; i < CINEMATIC_STEPS.length; i++) {
    if (CINEMATIC_STEPS[i].statuses.includes(status)) return i;
  }
  return 0;
};

const STEP_BG_MAP = {
  idea: 'idea-bg',
  hype: 'hype-bg',
  cast: 'casting-bg',
  produzione: 'production-bg',
  'la-prima': 'premiere-bg',
  uscita: 'release-bg',
};

const STEP_COLORS = {
  yellow: { active: 'border-yellow-500 bg-yellow-500/15 text-yellow-400', dot: 'bg-yellow-500', line: 'bg-yellow-500/40', glow: 'shadow-yellow-500/20' },
  orange: { active: 'border-orange-500 bg-orange-500/15 text-orange-400', dot: 'bg-orange-500', line: 'bg-orange-500/40', glow: 'shadow-orange-500/20' },
  cyan: { active: 'border-cyan-500 bg-cyan-500/15 text-cyan-400', dot: 'bg-cyan-500', line: 'bg-cyan-500/40', glow: 'shadow-cyan-500/20' },
  blue: { active: 'border-blue-500 bg-blue-500/15 text-blue-400', dot: 'bg-blue-500', line: 'bg-blue-500/40', glow: 'shadow-blue-500/20' },
  gold: { active: 'border-[#C6A55C] bg-[#C6A55C]/15 text-[#C6A55C]', dot: 'bg-[#C6A55C]', line: 'bg-[#C6A55C]/40', glow: 'shadow-[#C6A55C]/20' },
  green: { active: 'border-emerald-500 bg-emerald-500/15 text-emerald-400', dot: 'bg-emerald-500', line: 'bg-emerald-500/40', glow: 'shadow-emerald-500/20' },
};

// Evocative preview texts for La Prima
const PREMIERE_VIBES = [
  { city: 'Cannes', text: '"Presentato al Festival di Cannes"', vibe: 'Sotto le stelle della Croisette' },
  { city: 'Venezia', text: '"Notte di gala a Venezia"', vibe: 'Il Lido trattiene il respiro' },
  { city: 'Roma', text: '"Anteprima al Cinema Barberini"', vibe: 'La Capitale si ferma per il tuo film' },
  { city: 'Berlino', text: '"Berlinale — World Premiere"', vibe: 'L\'Orso d\'Oro ti attende' },
  { city: 'Los Angeles', text: '"Hollywood — Red Carpet Night"', vibe: 'Le luci di Sunset Boulevard brillano per te' },
  { city: 'Tokyo', text: '"Premiere esclusiva a Shibuya"', vibe: 'Il cinema incontra la cultura pop' },
];

// ─── Cinematic Step Bar Component ───
const CinematicStepBar = ({ currentStepIndex }) => (
  <div className="flex items-center justify-center gap-0 px-2 py-3" data-testid="cinematic-step-bar">
    {CINEMATIC_STEPS.map((step, i) => {
      const Icon = step.icon;
      const colors = STEP_COLORS[step.color];
      const isCurrent = i === currentStepIndex;
      const isCompleted = i < currentStepIndex;
      const isLocked = i > currentStepIndex;

      return (
        <React.Fragment key={step.id}>
          {i > 0 && (
            <div className={`step-connector ${isCompleted ? colors.line : 'bg-gray-800'}`} />
          )}
          <div className={`flex flex-col items-center gap-0.5 ${isCurrent ? '' : ''}`}>
            <div className={`w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
              isCurrent ? `${colors.active} step-active-glow` :
              isCompleted ? 'border-emerald-600 bg-emerald-500/10 text-emerald-400' :
              'border-gray-800 bg-gray-900/50 text-gray-700'
            }`}>
              {isCompleted ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Icon className={`w-3.5 h-3.5 ${isCurrent ? '' : ''}`} />
              )}
            </div>
            <span className={`text-[7px] sm:text-[8px] font-bold tracking-widest uppercase ${
              isCurrent ? (step.color === 'gold' ? 'text-[#C6A55C]' : `text-${step.color}-400`) :
              isCompleted ? 'text-emerald-500/70' :
              'text-gray-700'
            }`}>
              {step.label}
            </span>
          </div>
        </React.Fragment>
      );
    })}
  </div>
);

// ─── Film Carousel Component ───
const FilmCarousel = ({ films, selectedId, onSelect, onNew, countdowns }) => (
  <div className="mb-3">
    <div className="film-carousel">
      {/* New Film Card */}
      <button
        onClick={onNew}
        className="carousel-film-card flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-yellow-600/30 bg-yellow-600/5 hover:border-yellow-500/50 hover:bg-yellow-500/10 min-h-[160px]"
        data-testid="carousel-new-film"
      >
        <div className="w-10 h-10 rounded-full bg-yellow-600/10 flex items-center justify-center mb-2">
          <Pencil className="w-4 h-4 text-yellow-500" />
        </div>
        <span className="text-[10px] font-bold text-yellow-500/80 tracking-wide">NUOVO</span>
        <span className="text-[8px] text-yellow-600/50">FILM</span>
      </button>

      {/* Film Cards */}
      {films.map(f => {
        const isSelected = f.id === selectedId;
        const stepIdx = getCinematicStepIndex(f.status);
        const step = CINEMATIC_STEPS[stepIdx];
        const colors = STEP_COLORS[step.color];
        return (
          <button
            key={f.id}
            onClick={() => onSelect(f)}
            className={`carousel-film-card rounded-lg border overflow-hidden ${
              isSelected ? `active border-[#C6A55C]/60` : 'border-gray-800 hover:border-gray-600'
            }`}
            data-testid={`carousel-film-${f.id}`}
          >
            {/* Poster area */}
            <div className="w-full h-[100px] bg-gray-900 relative overflow-hidden">
              {f.poster_url ? (
                <img
                  src={f.poster_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${f.poster_url}` : f.poster_url}
                  alt="" className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
                  <Film className="w-6 h-6 text-gray-700" />
                </div>
              )}
              {/* Status badge */}
              <div className={`absolute top-1 right-1 px-1.5 py-0.5 rounded text-[7px] font-bold uppercase tracking-wide ${colors.active}`}>
                {step.label}
              </div>
              {/* Countdown overlay */}
              {countdowns[f.id] && (
                <div className="absolute bottom-0 inset-x-0 bg-black/70 text-center py-0.5">
                  <span className="text-[8px] text-orange-400 font-mono">{countdowns[f.id]}</span>
                </div>
              )}
            </div>
            {/* Info */}
            <div className="p-1.5 bg-[#0D0D0F]">
              <p className="text-[10px] font-bold text-white truncate">{f.title}</p>
              <div className="flex items-center gap-1 mt-0.5">
                <Star className="w-2.5 h-2.5 text-yellow-400 fill-yellow-400" />
                <span className="text-[9px] text-yellow-400 font-bold">{f.pre_imdb_score}</span>
                <span className="text-[8px] text-gray-600 truncate">{f.genre}</span>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  </div>
);

// ─── Step Section Wrapper ───
const StepSection = ({ stepId, title, subtitle, children }) => (
  <div className="relative rounded-xl border border-gray-800/50 overflow-hidden mb-4 step-section-enter" data-testid={`step-section-${stepId}`}>
    {/* Cinematic background placeholder */}
    <div className={`cinematic-bg-placeholder ${STEP_BG_MAP[stepId] || ''}`}>
      {/* PRODUZIONE — Film strip + grain + light leak */}
      {stepId === 'produzione' && (
        <>
          <div className="film-strip-top" />
          <div className="film-strip-bottom" />
          <div className="film-grain" />
          <div className="reel-light-leak" />
        </>
      )}
      {/* LA PRIMA — Red carpet + flashes + spotlight + stars */}
      {stepId === 'la-prima' && (
        <>
          <div className="red-carpet-anim" />
          <div className="carpet-shine" />
          <div className="gold-spotlight" />
          <div className="flash-overlay">
            <div className="flash-burst flash-1" />
            <div className="flash-burst flash-2" />
            <div className="flash-burst flash-3" />
            <div className="flash-burst flash-4" />
            <div className="flash-burst flash-5" />
          </div>
          <div className="star-particles">
            <div className="star-particle sp-1" />
            <div className="star-particle sp-2" />
            <div className="star-particle sp-3" />
            <div className="star-particle sp-4" />
            <div className="star-particle sp-5" />
            <div className="star-particle sp-6" />
          </div>
        </>
      )}
      {/* USCITA — Projector + dust + screen glow + vignette */}
      {stepId === 'uscita' && (
        <>
          <div className="projector-cone" />
          <div className="screen-glow" />
          <div className="cinema-vignette" />
          <div className="dust-particles">
            <div className="dust d-1" />
            <div className="dust d-2" />
            <div className="dust d-3" />
            <div className="dust d-4" />
            <div className="dust d-5" />
          </div>
        </>
      )}
    </div>
    {/* Content */}
    <div className={`relative z-10 ${stepId === 'produzione' ? 'py-6 px-4' : 'p-4'}`}>
      {title && (
        <div className="mb-4">
          <h2 className={`font-['Bebas_Neue'] text-xl sm:text-2xl tracking-wide ${
            stepId === 'la-prima' ? 'gold-shimmer-text' : 'text-white'
          }`}>
            {title}
          </h2>
          {subtitle && <p className="text-[10px] text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  </div>
);

// ─── Film Header (Cinematic) ───
const CinematicFilmHeader = ({ film }) => (
  <div className="flex items-start gap-3 mb-3 p-3 rounded-xl bg-black/40 border border-gray-800/50" data-testid="cinematic-film-header">
    {/* Poster */}
    <div className="w-16 h-24 rounded-lg overflow-hidden flex-shrink-0 border border-gray-700/50 shadow-lg">
      {film.poster_url ? (
        <img
          src={film.poster_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${film.poster_url}` : film.poster_url}
          alt="" className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
          <Film className="w-5 h-5 text-gray-600" />
        </div>
      )}
    </div>
    {/* Info */}
    <div className="flex-1 min-w-0">
      <h2 className="font-['Bebas_Neue'] text-lg sm:text-xl text-white tracking-wide truncate">{film.title}</h2>
      <p className="text-[10px] text-gray-500">{film.genre} &bull; {film.subgenre || film.subgenres?.join(', ')}</p>
      <div className="flex items-center gap-2 mt-1">
        <div className="flex items-center gap-0.5">
          <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
          <span className={`text-sm font-bold ${film.pre_imdb_score >= 7 ? 'text-emerald-400' : film.pre_imdb_score >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
            {film.pre_imdb_score}
          </span>
        </div>
        {film.hype_score > 0 && (
          <div className="flex items-center gap-0.5">
            <Flame className="w-3 h-3 text-orange-400" />
            <span className="text-[10px] text-orange-400 font-bold">{film.hype_score}</span>
          </div>
        )}
        {film.release_type && (
          <Badge className={`text-[8px] h-4 ${film.release_type === 'coming_soon' ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30' : 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30'}`}>
            {film.release_type === 'coming_soon' ? 'Coming Soon' : 'Immediato'}
          </Badge>
        )}
      </div>
      {film.pre_screenplay && (
        <p className="text-[9px] text-gray-600 mt-1 line-clamp-2 italic">"{film.pre_screenplay}"</p>
      )}
    </div>
  </div>
);

// ─── La Prima Preview Section ───
const LaPrimaPreview = ({ film }) => {
  const vibe = PREMIERE_VIBES[Math.floor(Math.abs(film.title?.charCodeAt(0) || 0) % PREMIERE_VIBES.length)];
  const premiereCity = film.premiere?.city;
  const matchedVibe = premiereCity ? PREMIERE_VIBES.find(v => v.city === premiereCity) : null;
  const displayVibe = matchedVibe || vibe;

  return (
    <div className="text-center py-6">
      {/* Evocative text */}
      <p className="premiere-evocative text-lg sm:text-xl font-['Bebas_Neue'] tracking-widest text-[#C6A55C]">
        {displayVibe.text}
      </p>
      <p className="text-[10px] text-[#C6A55C]/50 mt-1 italic">
        {displayVibe.vibe}
      </p>
      {/* Placeholder cinema effects */}
      <div className="flex items-center justify-center gap-6 mt-4 opacity-30">
        <div className="text-center">
          <div className="w-8 h-8 mx-auto rounded-full border border-[#C6A55C]/30 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-[#C6A55C]" />
          </div>
          <p className="text-[7px] text-[#C6A55C]/60 mt-1">Tappeto Rosso</p>
        </div>
        <div className="text-center">
          <div className="w-8 h-8 mx-auto rounded-full border border-[#C6A55C]/30 flex items-center justify-center">
            <Zap className="w-4 h-4 text-[#C6A55C]" />
          </div>
          <p className="text-[7px] text-[#C6A55C]/60 mt-1">Luci</p>
        </div>
        <div className="text-center">
          <div className="w-8 h-8 mx-auto rounded-full border border-[#C6A55C]/30 flex items-center justify-center">
            <Play className="w-4 h-4 text-[#C6A55C]" />
          </div>
          <p className="text-[7px] text-[#C6A55C]/60 mt-1">Proiettore</p>
        </div>
      </div>
    </div>
  );
};

// ============ MAIN PAGE (CINEMATIC LAYOUT) ============
const FilmPipeline = () => {
  const { api, refreshUser, cachedGet } = useContext(AuthContext);
  const [searchParams, setSearchParams] = useSearchParams();
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [countdowns, setCountdowns] = useState({});
  const [counts, setCounts] = useState({});
  const [showCreation, setShowCreation] = useState(false);
  const [badges, setBadges] = useState({});

  const { data: pipelineData, mutate: refreshPipeline } = useSWR('/film-pipeline/all');
  const { data: badgesData } = useSWR('/film-pipeline/badges');

  useEffect(() => {
    if (badgesData?.badges) setBadges(badgesData.badges);
  }, [badgesData]);

  const loadFilms = useCallback(async () => {
    try {
      const data = pipelineData || (await api.get('/film-pipeline/all')).data;
      const safe = (data.projects || []).filter(p => p && p.id && p.title && !['completed', 'released'].includes(p.status) && !p.film_id);
      setFilms(safe);
      try {
        const rescueRes = await api.post('/film-pipeline/rescue-lost-films');
        if (rescueRes.data?.rescued_count > 0) {
          toast.success(`${rescueRes.data.rescued_count} film recuperati!`);
          refreshPipeline();
        }
      } catch (e) { /* best-effort */ }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [api, pipelineData, refreshPipeline]);

  const refreshCounts = useCallback(async () => {
    try {
      const res = await api.get('/film-pipeline/counts');
      setCounts(res.data);
    } catch (e) { console.error(e); }
  }, [api]);

  useEffect(() => {
    loadFilms();
    refreshCounts();
    const interval = setInterval(loadFilms, 30000);
    return () => clearInterval(interval);
  }, [loadFilms, refreshCounts]);

  // Handle ?film=xxx from notifications
  useEffect(() => {
    const filmId = searchParams.get('film');
    if (filmId && films.length > 0) {
      const f = films.find(p => p.id === filmId);
      if (f) { setSelectedFilm(f); setSearchParams({}, { replace: true }); }
    }
  }, [searchParams, films, setSearchParams]);

  // Countdown timer
  useEffect(() => {
    const update = () => {
      const now = new Date();
      const cd = {};
      films.forEach(f => {
        if (f.status === 'coming_soon' && f.scheduled_release_at) {
          const diff = new Date(f.scheduled_release_at) - now;
          if (diff > 0) {
            const h = Math.floor(diff / 3600000);
            const m = Math.floor((diff % 3600000) / 60000);
            cd[f.id] = `${h}h ${m}m`;
          } else {
            cd[f.id] = null;
            api.post(`/film-pipeline/${f.id}/check-coming-soon-status`).then(res => {
              if (res.data?.advanced) { loadFilms(); refreshCounts(); toast.success(`"${f.title}" - Coming Soon completato!`); }
            }).catch(() => {});
          }
        }
      });
      setCountdowns(cd);
    };
    update();
    const i = setInterval(update, 10000);
    return () => clearInterval(i);
  }, [films, api, loadFilms, refreshCounts]);

  const handleRefresh = async () => {
    refreshPipeline();
    const res = await api.get('/film-pipeline/all');
    const safe = (res.data.projects || []).filter(p => p && p.id && p.title && !['completed', 'released'].includes(p.status) && !p.film_id);
    setFilms(safe);
    if (selectedFilm) {
      const updated = safe.find(f => f.id === selectedFilm.id);
      if (updated) setSelectedFilm(updated);
      else setSelectedFilm(null);
    }
    refreshCounts();
  };

  const handleCreationDone = () => {
    handleRefresh();
    setShowCreation(false);
  };

  const currentStepIndex = selectedFilm ? getCinematicStepIndex(selectedFilm.status) : 0;
  const currentCinematicStep = selectedFilm ? CINEMATIC_STEPS[currentStepIndex] : null;

  // Determine step section title
  const getStepTitle = (stepId) => {
    switch (stepId) {
      case 'idea': return ['L\'Idea', 'Dai vita al tuo film'];
      case 'hype': return ['Hype Machine', 'Crea aspettativa nel pubblico'];
      case 'cast': return ['Il Cast', 'Assembla la squadra perfetta'];
      case 'produzione': return ['Produzione', 'Sceneggiatura, Sponsor & Riprese'];
      case 'la-prima': return ['La Prima', 'L\'anteprima esclusiva'];
      case 'uscita': return ['Uscita al Cinema', 'Il momento della verità'];
      default: return ['', ''];
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white p-3 pt-16 pb-20" data-testid="film-pipeline-page">
      <div className="max-w-lg mx-auto">
        {/* ─── Cinematic Header ─── */}
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="font-['Bebas_Neue'] text-3xl sm:text-4xl text-white tracking-wide">
              Produci<span className="text-[#C6A55C]">!</span>
            </h1>
            <p className="text-[10px] text-gray-600">
              Film attivi: <span className="text-gray-400">{counts.total_active || 0}/{counts.max_simultaneous || 2}</span>
            </p>
          </div>
          {selectedFilm && (
            <Button
              onClick={() => { setSelectedFilm(null); setShowCreation(false); }}
              variant="outline"
              className="h-8 px-3 text-[10px] border-gray-700 text-gray-400 hover:text-white"
              data-testid="back-to-carousel-btn"
            >
              <ChevronLeft className="w-3 h-3 mr-1" /> Tutti i Film
            </Button>
          )}
        </div>

        {/* ─── Film Carousel (always visible when there are films) ─── */}
        {!selectedFilm && (
          <>
            {loading ? (
              <div className="text-center py-16">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[#C6A55C]/50" />
                <p className="text-xs text-gray-600">Caricamento produzioni...</p>
              </div>
            ) : (
              <>
                {/* Smart Badges */}
                {Object.values(badges).some(v => v > 0) && (
                  <div className="flex flex-wrap gap-1.5 mb-2" data-testid="smart-badges">
                    {[
                      { key: 'film', label: 'Film', color: 'yellow' },
                      { key: 'sequel', label: 'Sequel', color: 'blue' },
                      { key: 'serie_tv', label: 'Serie TV', color: 'purple' },
                      { key: 'anime', label: 'Anime', color: 'pink' },
                      { key: 'agenzia', label: 'Agenzia', color: 'cyan' },
                    ].map(cat => badges[cat.key] > 0 && (
                      <div key={cat.key} className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-medium border
                        ${cat.color === 'yellow' ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400' :
                          cat.color === 'blue' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' :
                          cat.color === 'purple' ? 'bg-purple-500/10 border-purple-500/20 text-purple-400' :
                          cat.color === 'pink' ? 'bg-pink-500/10 border-pink-500/20 text-pink-400' :
                          'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'
                        }`}>
                        {cat.label}
                        <span className="flex items-center justify-center w-3.5 h-3.5 rounded-full bg-red-500 text-white text-[7px] font-bold">{badges[cat.key]}</span>
                      </div>
                    ))}
                  </div>
                )}

                <FilmCarousel
                  films={films}
                  selectedId={null}
                  onSelect={(f) => { setSelectedFilm(f); setShowCreation(false); haptic([15]); }}
                  onNew={() => { setSelectedFilm(null); setShowCreation(true); haptic([10]); }}
                  countdowns={countdowns}
                />

                {/* Drafts section */}
                <DraftsSection
                  api={api}
                  onResume={(film) => { setSelectedFilm(film); haptic([15]); }}
                  onRefresh={handleRefresh}
                />

                {/* Empty state */}
                {films.length === 0 && !showCreation && (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[#C6A55C]/10 flex items-center justify-center">
                      <Film className="w-7 h-7 text-[#C6A55C]/50" />
                    </div>
                    <p className="text-sm text-gray-400 mb-1 font-medium">Il tuo studio è vuoto</p>
                    <p className="text-[10px] text-gray-600 mb-4">Crea il tuo primo capolavoro cinematografico</p>
                    <Button onClick={() => setShowCreation(true)} className="bg-[#C6A55C] hover:bg-[#b8953f] text-black text-xs font-bold px-6"
                      data-testid="create-first-film-btn">
                      <Pencil className="w-3.5 h-3.5 mr-1.5" /> Crea il tuo primo film
                    </Button>
                  </div>
                )}

                {/* Creation Flow (IDEA Step) */}
                {showCreation && (
                  <StepSection stepId="idea" title="L'Idea" subtitle="Dai vita al tuo film">
                    <TabErrorBoundary name="creation">
                      <CreationTab api={api} refreshUser={refreshUser} refreshCounts={handleCreationDone} cachedGet={cachedGet} />
                    </TabErrorBoundary>
                  </StepSection>
                )}

                {/* Buzz Section */}
                <BuzzSection api={api} refreshUser={refreshUser} />
              </>
            )}
          </>
        )}

        {/* ─── Selected Film: Full-Page Cinematic View ─── */}
        {selectedFilm && (
          <div className="space-y-0">
            {/* Film Header */}
            <CinematicFilmHeader film={selectedFilm} />

            {/* 6-Step Cinematic Bar */}
            <CinematicStepBar currentStepIndex={currentStepIndex} />

            {/* Step Content — full-page section */}
            {currentCinematicStep && (() => {
              const [title, subtitle] = getStepTitle(currentCinematicStep.id);
              return (
                <StepSection stepId={currentCinematicStep.id} title={title} subtitle={subtitle}>
                  {/* La Prima special preview */}
                  {currentCinematicStep.id === 'la-prima' && (
                    <LaPrimaPreview film={selectedFilm} />
                  )}

                  {/* La Prima section (for prima and pending_release) */}
                  {(selectedFilm.status === 'prima' || selectedFilm.status === 'pending_release') && currentCinematicStep.id !== 'uscita' && (
                    <div className="mb-4">
                      <LaPremiereSection filmId={selectedFilm.id} project={selectedFilm} />
                    </div>
                  )}

                  {/* Production speed-up placeholder */}
                  {currentCinematicStep.id === 'produzione' && selectedFilm.status === 'shooting' && (
                    <div className="mb-3 p-3 rounded-lg border border-blue-500/20 bg-blue-500/5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Zap className="w-4 h-4 text-blue-400" />
                          <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wide">Avanzamento Rapido</span>
                        </div>
                        <Badge className="bg-blue-500/15 text-blue-400 text-[8px] border-blue-500/20">Costo: CinePass</Badge>
                      </div>
                      <p className="text-[9px] text-gray-500 mt-1">Accelera le riprese del tuo film con CinePass</p>
                    </div>
                  )}

                  {/* Inline Film View (all step content from popup) */}
                  <FilmInlineView
                    film={selectedFilm}
                    onRefresh={handleRefresh}
                    countdown={countdowns[selectedFilm.id]}
                  />
                </StepSection>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
};

export default FilmPipeline;
