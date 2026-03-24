import React, { useState, useEffect, useCallback, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Star, Film, Clock, Flame, Check, X, Lock, Rocket, Palette, Lightbulb,
  FileText, MapPin, Users, BookOpen, Clapperboard, Play, Sparkles, Zap,
  ChevronRight, ChevronDown, ChevronUp, RefreshCw, ThumbsDown, Settings,
  DollarSign, Target, Globe, UserCheck, Minus, TrendingUp, TrendingDown,
  HelpCircle, Wand2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ─── Haptic feedback ───
const haptic = (pattern = [10]) => { try { navigator?.vibrate?.(pattern); } catch {} };

// Sub-component for agency actor cards (uses useState for skill expansion)
const AgencyActorCardPopup = ({ actor, isSelected, onToggle, roleValue, onRoleChange, ACTOR_ROLES }) => {
  const [skillExpanded, setSkillExpanded] = React.useState(false);
  const skills = actor.skills || {};
  const avgSkill = Object.values(skills).length > 0
    ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;

  return (
    <div className={`p-2 rounded-lg transition-all border ${
      isSelected ? 'bg-purple-500/15 border-purple-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-purple-500/10'
    }`}>
      <div className="flex items-center gap-2 cursor-pointer" onClick={onToggle}>
        <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center text-[10px] font-bold text-purple-400 flex-shrink-0">
          {actor.name?.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 flex-wrap">
            <span className="text-[11px] font-medium truncate">{actor.name}</span>
            <span className={`text-[10px] font-bold ${actor.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>
              {actor.gender === 'female' ? '♀' : '♂'}
            </span>
            {[...Array(actor.stars || 2)].map((_, i) => <Star key={i} className="w-2 h-2 text-yellow-500 fill-yellow-500" />)}
          </div>
          <p className="text-[9px] text-gray-500">
            {actor.nationality} &bull; {actor.age}a &bull; Skill: <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>
            &bull; {actor.films_count || 0} film
          </p>
          <div className="flex flex-wrap gap-0.5 mt-0.5">
            {(actor.strong_genres_names || actor.strong_genres || []).map((g, i) => (
              <span key={i} className="text-[7px] px-1 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-800/40">{g}</span>
            ))}
            {(actor.adaptable_genre_name || actor.adaptable_genre) && (
              <span className="text-[7px] px-1 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-800/40">~ {actor.adaptable_genre_name || actor.adaptable_genre}</span>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <button className="text-[8px] text-gray-400 hover:text-white flex items-center gap-0.5"
            onClick={e => { e.stopPropagation(); setSkillExpanded(!skillExpanded); }}>
            {skillExpanded ? <ChevronUp className="w-2.5 h-2.5" /> : <ChevronDown className="w-2.5 h-2.5" />} Skill
          </button>
          {isSelected && (
            <select className="bg-[#1a1a1a] text-[9px] rounded px-1 py-0.5 border border-white/10 text-white"
              value={roleValue} onClick={e => e.stopPropagation()}
              onChange={e => onRoleChange(e.target.value)}>
              {ACTOR_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          )}
        </div>
        {isSelected && <Check className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />}
      </div>
      {skillExpanded && Object.keys(skills).length > 0 && (
        <div className="mt-1.5 pt-1.5 border-t border-white/5 space-y-0.5">
          {Object.entries(skills).map(([name, value]) => (
            <div key={name} className="flex items-center gap-1.5 text-[9px]">
              <span className="w-20 text-gray-500 truncate">{name}</span>
              <div className="flex-1 h-1 bg-gray-800 rounded-full">
                <div className={`h-full rounded-full ${value >= 80 ? 'bg-emerald-500' : value >= 60 ? 'bg-cyan-500' : value >= 40 ? 'bg-amber-500' : 'bg-red-500'}`}
                  style={{ width: `${Math.min(100, value)}%` }} />
              </div>
              <span className="w-5 text-right font-mono text-gray-400">{value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Pipeline Steps Config ───
const STEPS_IMMEDIATE = [
  { id: 'proposta', label: 'Proposta', icon: Lightbulb, color: 'yellow' },
  { id: 'casting', label: 'Casting', icon: Users, color: 'cyan' },
  { id: 'script', label: 'Script', icon: BookOpen, color: 'emerald' },
  { id: 'produzione', label: 'Produzione', icon: Clapperboard, color: 'blue' },
  { id: 'uscita', label: 'Uscita', icon: Rocket, color: 'purple' },
];

const STEPS_CS = [
  { id: 'proposta', label: 'Proposta', icon: Lightbulb, color: 'yellow' },
  { id: 'poster', label: 'Poster', icon: Palette, color: 'purple' },
  { id: 'hype', label: 'Hype', icon: Flame, color: 'orange' },
  { id: 'casting', label: 'Casting', icon: Users, color: 'cyan' },
  { id: 'script', label: 'Script', icon: BookOpen, color: 'emerald' },
  { id: 'produzione', label: 'Produzione', icon: Clapperboard, color: 'blue' },
  { id: 'uscita', label: 'Uscita', icon: Rocket, color: 'purple' },
];

// ─── Determine current step ID ───
function getCurrentStepId(film) {
  // Infer release_type from status if missing
  const isCS = film.release_type === 'coming_soon' || film.status === 'ready_for_casting' || (film.status === 'coming_soon');
  const s = film.status;
  if (isCS) {
    if (s === 'proposed' && !film.poster_url) return 'poster';
    if (s === 'proposed' && film.poster_url) return 'hype';
    if (s === 'coming_soon') return 'hype';
    if (s === 'ready_for_casting') return 'casting';
    if (s === 'casting') return 'casting';
    if (s === 'screenplay') return 'script';
    if (s === 'pre_production') return 'produzione';
    if (s === 'shooting') return 'uscita';
    return 'proposta';
  } else {
    if (s === 'proposed') return 'casting'; // proposta done, show advance UI
    if (s === 'ready_for_casting') return 'casting';
    if (s === 'casting') return 'casting';
    if (s === 'screenplay') return 'script';
    if (s === 'pre_production') return 'produzione';
    if (s === 'shooting') return 'uscita';
    return 'proposta';
  }
}

// ─── Color utility ───
const CS_MAP = {
  yellow: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', text: 'text-yellow-400', iconBg: 'bg-yellow-500/30', glow: 'rgba(234,179,8,0.4)' },
  purple: { bg: 'bg-purple-500/20', border: 'border-purple-500/50', text: 'text-purple-400', iconBg: 'bg-purple-500/30', glow: 'rgba(168,85,247,0.4)' },
  orange: { bg: 'bg-orange-500/20', border: 'border-orange-500/50', text: 'text-orange-400', iconBg: 'bg-orange-500/30', glow: 'rgba(249,115,22,0.4)' },
  cyan: { bg: 'bg-cyan-500/20', border: 'border-cyan-500/50', text: 'text-cyan-400', iconBg: 'bg-cyan-500/30', glow: 'rgba(6,182,212,0.4)' },
  emerald: { bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', text: 'text-emerald-400', iconBg: 'bg-emerald-500/30', glow: 'rgba(16,185,129,0.4)' },
  blue: { bg: 'bg-blue-500/20', border: 'border-blue-500/50', text: 'text-blue-400', iconBg: 'bg-blue-500/30', glow: 'rgba(59,130,246,0.4)' },
  green: { bg: 'bg-green-500/20', border: 'border-green-500/50', text: 'text-green-400', iconBg: 'bg-green-500/30', glow: 'rgba(34,197,94,0.4)' },
};

// ─── Per-Film Step Bar ───
function FilmStepBar({ film }) {
  const isCS = film.release_type === 'coming_soon' || film.status === 'ready_for_casting' || film.status === 'coming_soon';
  const steps = isCS ? STEPS_CS : STEPS_IMMEDIATE;
  const currentStepId = getCurrentStepId(film);
  const currentIdx = steps.findIndex(s => s.id === currentStepId);
  const scrollRef = React.useRef(null);

  React.useEffect(() => {
    if (scrollRef.current) {
      const el = scrollRef.current.querySelector('[data-step-active="true"]');
      if (el) el.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
  }, [currentStepId]);

  return (
    <div className="my-2" data-testid="film-popup-step-bar">
      <div ref={scrollRef} className="flex items-center gap-0 overflow-x-auto pb-1 px-0 no-scrollbar">
        {steps.map((step, i) => {
          const Icon = step.icon;
          const cs = CS_MAP[step.color] || CS_MAP.yellow;
          const isCompleted = i < currentIdx;
          const isCurrent = i === currentIdx;
          const isLocked = i > currentIdx;

          return (
            <React.Fragment key={step.id}>
              {i > 0 && (
                <div className={`flex-shrink-0 w-2 sm:w-4 h-[2px] rounded-full ${
                  isCompleted || isCurrent ? 'connector-active' : 'bg-gray-800'
                }`} />
              )}
              <div
                data-step-active={isCurrent ? 'true' : 'false'}
                style={isCurrent ? { '--step-glow-color': cs.glow } : {}}
                className={`flex-shrink-0 flex flex-col items-center gap-0.5 p-1 sm:p-1.5 rounded-lg sm:rounded-xl transition-all min-w-[38px] sm:min-w-[48px] relative ${
                  isCurrent ? `${cs.bg} border ${cs.border} step-current` :
                  isCompleted ? 'step-completed' :
                  isLocked ? 'step-locked opacity-40' : ''
                }`}
              >
                <div className={`w-6 h-6 sm:w-7 sm:h-7 rounded-md sm:rounded-lg flex items-center justify-center transition-all ${
                  isCurrent ? cs.iconBg :
                  isCompleted ? 'bg-green-500/20' :
                  'bg-gray-900'
                }`}>
                  {isLocked ? (
                    <Lock className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-gray-700" />
                  ) : isCompleted ? (
                    <Check className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-green-400 step-check-icon" />
                  ) : (
                    <Icon className={`w-3 h-3 sm:w-3.5 sm:h-3.5 ${isCurrent ? cs.text : 'text-gray-600'}`} />
                  )}
                </div>
                <span className={`text-[7px] sm:text-[8px] font-semibold leading-none tracking-wide ${
                  isCurrent ? cs.text :
                  isCompleted ? 'text-green-400/80' :
                  'text-gray-700'
                }`}>
                  {step.label}
                </span>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

// ─── Film Header (always visible) ───
function FilmHeader({ film }) {
  const posterSrc = film.poster_url
    ? (film.poster_url.startsWith('/') ? `${API_URL}${film.poster_url}` : film.poster_url)
    : null;

  return (
    <div className="flex items-start gap-2.5 pb-2.5 border-b border-white/5 pr-6">
      {posterSrc ? (
        <img src={posterSrc} alt="" className="w-12 h-[72px] sm:w-16 sm:h-24 object-cover rounded-lg flex-shrink-0 border border-white/10" />
      ) : (
        <div className="w-12 h-[72px] sm:w-16 sm:h-24 rounded-lg bg-gray-800/50 flex items-center justify-center flex-shrink-0 border border-white/10">
          <Film className="w-5 h-5 text-gray-600" />
        </div>
      )}
      <div className="flex-1 min-w-0 overflow-hidden">
        <h2 className="font-['Bebas_Neue'] text-lg sm:text-xl text-white truncate">{film.title}</h2>
        <p className="text-[10px] text-gray-500 truncate">
          {film.genre} {film.subgenre ? `\u2022 ${film.subgenre}` : ''} {film.location?.name ? `\u2022 ${film.location.name}` : ''}
        </p>
        <div className="flex items-center gap-1.5 mt-1">
          <Star className="w-3 h-3 text-yellow-400 flex-shrink-0" />
          <span className={`text-sm font-bold ${film.pre_imdb_score >= 7 ? 'text-green-400' : film.pre_imdb_score >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
            {film.pre_imdb_score}
          </span>
          <span className="text-[8px] text-gray-600">Pre-IMDb</span>
        </div>
        <p className="text-[9px] text-gray-500 mt-1 line-clamp-2 italic break-words">"{film.pre_screenplay}"</p>
      </div>
    </div>
  );
}

// ─── POSTER STEP ───
function PosterStep({ film, api, onRefresh }) {
  const [mode, setMode] = useState('ai_auto');
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('drama');
  const [loading, setLoading] = useState(false);

  const MODES = [
    { id: 'ai_auto', label: 'AI Auto' },
    { id: 'ai_custom', label: 'AI + Prompt' },
    { id: 'classic', label: 'Stile Classico' },
  ];
  const STYLES = [
    { id: 'noir', label: 'Noir' }, { id: 'vintage', label: 'Vintage' },
    { id: 'action', label: 'Action' }, { id: 'romance', label: 'Romance' },
    { id: 'horror', label: 'Horror' }, { id: 'scifi', label: 'Sci-Fi' },
    { id: 'comedy', label: 'Commedia' }, { id: 'drama', label: 'Dramma' },
  ];

  const generate = async () => {
    setLoading(true);
    try {
      const body = { mode };
      if (mode === 'ai_custom') body.custom_prompt = prompt;
      if (mode === 'classic') body.classic_style = style;
      const res = await api.post(`/film-pipeline/${film.id}/generate-poster`, body, { timeout: 120000 });
      toast.success(res.data.message || 'Locandina generata!');
      onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore generazione locandina'); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-2.5" data-testid={`popup-poster-step-${film.id}`}>
      <p className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">Genera la Locandina</p>
      <div className="flex gap-1">
        {MODES.map(opt => (
          <button key={opt.id} onClick={() => setMode(opt.id)}
            className={`flex-1 p-1.5 rounded text-[9px] text-center border transition-all ${
              mode === opt.id ? 'border-purple-500 bg-purple-500/10 text-purple-300' : 'border-gray-700 text-gray-500'
            }`}>{opt.label}</button>
        ))}
      </div>
      {mode === 'ai_custom' && (
        <input type="text" placeholder="Descrivi la locandina..." value={prompt}
          onChange={e => setPrompt(e.target.value)}
          className="w-full p-1.5 bg-black/30 border border-gray-700 rounded text-[10px] text-white" />
      )}
      {mode === 'classic' && (
        <div className="grid grid-cols-4 gap-1">
          {STYLES.map(s => (
            <button key={s.id} onClick={() => setStyle(s.id)}
              className={`p-1 rounded text-[8px] text-center border transition-all ${
                style === s.id ? 'border-purple-500 bg-purple-500/10' : 'border-gray-700'
              }`}>{s.label}</button>
          ))}
        </div>
      )}
      <Button size="sm" className="w-full bg-purple-700 hover:bg-purple-600 text-[10px]"
        onClick={generate} disabled={loading} data-testid={`popup-gen-poster-${film.id}`}>
        {loading ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Sparkles className="w-3 h-3 mr-1" />}
        Genera Locandina
      </Button>
    </div>
  );
}

// ─── COMING SOON / HYPE STEP ───
function HypeStep({ film, api, onRefresh, refreshUser, countdown }) {
  const [tier, setTier] = useState('short');
  const [hours, setHours] = useState(4);
  const [loading, setLoading] = useState(false);
  const [advLoading, setAdvLoading] = useState(false);

  const TIERS = [
    { id: 'short', label: 'Breve', range: '2-6h', icon: Zap, color: 'yellow', steps: [2, 3, 4, 5, 6] },
    { id: 'medium', label: 'Medio', range: '6-18h', icon: Film, color: 'cyan', steps: [6, 8, 10, 12, 15, 18] },
    { id: 'long', label: 'Lungo', range: '18-48h', icon: Flame, color: 'orange', steps: [18, 24, 30, 36, 42, 48] },
  ];

  const isActive = film.status === 'coming_soon';
  const isReady = film.status === 'ready_for_casting' || (film.status === 'coming_soon' && film.scheduled_release_at && new Date(film.scheduled_release_at) <= new Date());
  const needsLaunch = film.status === 'proposed' && film.poster_url;

  const launchCS = async () => {
    setLoading(true);
    try {
      const res = await api.post(`/film-pipeline/${film.id}/launch-coming-soon`, { tier, hours });
      toast.success(`${res.data.message} (${res.data.final_hours.toFixed(1)}h)`);
      onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setLoading(false); }
  };

  const advance = async () => {
    setAdvLoading(true);
    try {
      const res = await api.post(`/film-pipeline/${film.id}/advance-to-casting`);
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setAdvLoading(false); }
  };

  if (isReady) {
    return (
      <div className="space-y-2" data-testid={`popup-hype-ready-${film.id}`}>
        <div className="p-3 rounded-lg border border-green-500/20 bg-green-500/5 text-center">
          <p className="text-xs font-bold text-green-400">Coming Soon completato!</p>
          {film.hype_score > 0 && <p className="text-[9px] text-orange-400 mt-1">Hype accumulato: {film.hype_score}</p>}
        </div>
        <Button className="w-full bg-green-700 hover:bg-green-600 text-xs"
          onClick={advance} disabled={advLoading} data-testid={`popup-advance-casting-${film.id}`}>
          {advLoading ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Users className="w-3 h-3 mr-1" />}
          Prosegui al Casting (2 CP)
        </Button>
      </div>
    );
  }

  if (isActive) {
    return (
      <div className="p-3 rounded-lg border border-orange-500/20 bg-orange-500/5 text-center space-y-1.5" data-testid={`popup-hype-active-${film.id}`}>
        <div className="flex items-center justify-center gap-1.5">
          <Flame className="w-4 h-4 text-orange-400 animate-pulse" />
          <span className="text-xs font-bold text-orange-400">Coming Soon attivo</span>
        </div>
        <div className="flex items-center justify-center gap-1">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-base font-bold text-cyan-400">{countdown || '...'}</span>
        </div>
        {film.hype_score > 0 && (
          <div className="flex items-center justify-center gap-1">
            <Flame className="w-3 h-3 text-orange-400" />
            <span className="text-[10px] text-orange-400">Hype: {film.hype_score}</span>
          </div>
        )}
        <p className="text-[8px] text-gray-600">In attesa... il casting iniziera' dopo il Coming Soon</p>
      </div>
    );
  }

  if (needsLaunch) {
    const activeTier = TIERS.find(t => t.id === tier);
    return (
      <div className="space-y-2.5" data-testid={`popup-hype-launch-${film.id}`}>
        <p className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Durata Coming Soon</p>
        <div className="grid grid-cols-3 gap-1.5">
          {TIERS.map(t => {
            const TIcon = t.icon;
            const active = tier === t.id;
            return (
              <button key={t.id} onClick={() => { setTier(t.id); setHours(t.steps[Math.floor(t.steps.length / 2)]); }}
                className={`p-2 rounded-lg border text-center transition-all ${active ? `border-${t.color}-500/60 bg-${t.color}-500/10` : 'border-gray-700/60 hover:border-gray-600'}`}>
                <TIcon className={`w-4 h-4 mx-auto mb-0.5 ${active ? `text-${t.color}-400` : 'text-gray-600'}`} />
                <p className={`text-[10px] font-bold ${active ? 'text-white' : 'text-gray-500'}`}>{t.label}</p>
                <p className="text-[8px] text-gray-600">{t.range}</p>
              </button>
            );
          })}
        </div>
        <div className="flex gap-1 items-center">
          {activeTier.steps.map(h => (
            <button key={h} onClick={() => setHours(h)}
              className={`flex-1 py-1 rounded text-[9px] font-medium border transition-all ${
                hours === h ? 'border-cyan-500 bg-cyan-500/15 text-cyan-400' : 'border-gray-700 text-gray-500'
              }`}>{h}h</button>
          ))}
        </div>
        <Button size="sm" className="w-full bg-cyan-700 hover:bg-cyan-600 text-[10px]"
          onClick={launchCS} disabled={loading} data-testid={`popup-launch-cs-${film.id}`}>
          {loading ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
          Lancia Coming Soon ({hours}h)
        </Button>
      </div>
    );
  }

  return null;
}

// ─── CASTING STEP (for proposed/immediate films that need to advance) ───
function ProposedAdvanceStep({ film, api, onRefresh, refreshUser }) {
  const [loading, setLoading] = useState(false);

  const advance = async () => {
    setLoading(true);
    try {
      const res = await api.post(`/film-pipeline/${film.id}/advance-to-casting`);
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-2" data-testid={`popup-advance-step-${film.id}`}>
      <div className="p-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5 text-center">
        <p className="text-xs font-bold text-yellow-400">Proposta Completata!</p>
        <p className="text-[9px] text-gray-500 mt-1">Pre-IMDb: {film.pre_imdb_score} - Il tuo film e' pronto per il casting</p>
      </div>
      <Button className="w-full bg-cyan-700 hover:bg-cyan-600 text-xs"
        onClick={advance} disabled={loading} data-testid={`popup-go-casting-${film.id}`}>
        {loading ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Users className="w-3 h-3 mr-1" />}
        Prosegui al Casting (2 CP)
      </Button>
    </div>
  );
}

// ─── CASTING STEP (full casting UI) ───
function CastingStepContent({ film, api, onRefresh, refreshUser }) {
  const [actionLoading, setActionLoading] = useState(null);
  const [expandedRoles, setExpandedRoles] = useState({});
  const [actorRoles, setActorRoles] = useState({});
  const [expandedSkills, setExpandedSkills] = useState({});
  const [agencyActors, setAgencyActors] = useState({ effective: [], school: [] });
  const [selectedAgencyActors, setSelectedAgencyActors] = useState({});
  const [agencyRoles, setAgencyRoles] = useState({});
  const [showAutoComplete, setShowAutoComplete] = useState(false);
  const [velionMessage, setVelionMessage] = useState(null);
  const ACTOR_ROLES = ['Protagonista', 'Co-Protagonista', 'Antagonista', 'Supporto', 'Cameo'];
  const roleLabels = { directors: 'Regista', screenwriters: 'Sceneggiatore', actors: 'Attori', composers: 'Compositore' };

  useEffect(() => {
    api.get('/agency/actors-for-casting').then(r => {
      setAgencyActors({ effective: r.data.effective_actors || [], school: r.data.school_students || [] });
    }).catch(() => {});
  }, [api]);

  // Show auto-complete button after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => setShowAutoComplete(true), 5000);
    return () => clearTimeout(timer);
  }, []);

  const cast = film.cast || {};
  const castComplete = cast.director && cast.screenwriter && cast.composer && (cast.actors?.length || 0) >= 2;
  const isLocked = film.cast_locked === true || (film.from_emerging_screenplay && film.emerging_option === 'full_package');

  const speedUp = async (roleType) => {
    setActionLoading(`speed-${roleType}`);
    try {
      const res = await api.post(`/film-pipeline/${film.id}/speed-up-casting`, { role_type: roleType });
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  // FAIL-SAFE: selectCast with retry and fallback
  const selectCast = async (roleType, proposalId, retryCount = 0) => {
    if (roleType === 'actors' && !actorRoles[proposalId]) {
      setActorRoles(p => ({...p, [proposalId]: 'Supporto'}));
    }
    const finalRole = roleType === 'actors' ? (actorRoles[proposalId] || 'Supporto') : null;
    setActionLoading(`select-${proposalId}`);
    try {
      const res = await api.post(`/film-pipeline/${film.id}/select-cast`, {
        role_type: roleType, proposal_id: proposalId,
        actor_role: finalRole
      });
      if (res.data.accepted) {
        toast.success(res.data.message);
        haptic([10, 50, 10]);
        if (res.data.casting_complete) toast.success('Casting completo! Puoi proseguire.');
      } else {
        toast.error(res.data.message || 'Attore non disponibile');
      }
      refreshUser(); onRefresh();
    } catch (e) {
      // FAIL-SAFE: retry once, then fallback to auto-complete
      if (retryCount < 1) {
        await selectCast(roleType, proposalId, retryCount + 1);
        return;
      }
      toast.error('Errore selezione. Usa "Completa Cast" per proseguire.');
    }
    finally { setActionLoading(null); }
  };

  // FAIL-SAFE: Auto-complete cast
  const autoCompleteCast = async () => {
    setActionLoading('auto-complete');
    try {
      const res = await api.post(`/film-pipeline/${film.id}/auto-complete-cast`);
      if (res.data.success) {
        if (res.data.already_complete) {
          toast.success('Il cast è già completo!');
        } else {
          toast.success(res.data.velion_message || res.data.message);
          setVelionMessage(res.data.velion_message || 'Velion ha completato il casting!');
          setTimeout(() => setVelionMessage(null), 6000);
        }
        refreshUser(); onRefresh();
      } else {
        toast.error(res.data.message || 'Errore');
      }
    } catch (e) {
      toast.error('Errore nel completamento automatico');
    }
    finally { setActionLoading(null); }
  };

  // FAIL-SAFE: advanceToScreenplay with auto-complete fallback
  const advanceToScreenplay = async () => {
    setActionLoading('adv-screenplay');
    try {
      const res = await api.post(`/film-pipeline/${film.id}/advance-to-screenplay`);
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) {
      // FAIL-SAFE: if advance fails, try auto-complete then retry
      try {
        const autoRes = await api.post(`/film-pipeline/${film.id}/auto-complete-cast`);
        if (autoRes.data.success) {
          setVelionMessage(autoRes.data.velion_message || 'Velion ha completato il casting!');
          setTimeout(() => setVelionMessage(null), 6000);
          const retryRes = await api.post(`/film-pipeline/${film.id}/advance-to-screenplay`);
          toast.success(retryRes.data.message);
          refreshUser(); onRefresh();
        } else {
          toast.error('Impossibile completare il cast automaticamente');
        }
      } catch (e2) {
        toast.error('Errore avanzamento. Riprova tra poco.');
      }
    }
    finally { setActionLoading(null); }
  };

  const renegotiate = async (roleType, proposalId) => {
    setActionLoading(`renego-${proposalId}`);
    try {
      const res = await api.post(`/film-pipeline/${film.id}/renegotiate`, {
        role_type: roleType, proposal_id: proposalId,
        actor_role: roleType === 'actors' ? (actorRoles[proposalId] || 'Supporto') : null
      });
      if (res.data.accepted) { toast.success(res.data.message); }
      else { toast.error(res.data.message); }
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const submitAgencyCast = async () => {
    const selected = Object.entries(selectedAgencyActors)
      .filter(([_, v]) => v)
      .map(([actorId]) => ({
        actor_id: actorId,
        role: agencyRoles[actorId] || 'Supporto',
        source: agencyActors.effective.find(a => a.id === actorId) ? 'effective' : 'school'
      }));
    if (selected.length === 0) { toast.error('Seleziona almeno un attore'); return; }
    setActionLoading('agency-cast');
    try {
      const res = await api.post(`/agency/cast-for-film/${film.id}`, { actor_ids: selected });
      toast.success(res.data.message);
      setSelectedAgencyActors({}); setAgencyRoles({});
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  return (
    <div className="space-y-2" data-testid={`popup-casting-${film.id}`}>
      {/* Velion auto-complete message */}
      {velionMessage && (
        <motion.div
          initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
          className="flex items-center gap-2 p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20"
          data-testid="velion-cast-message">
          <Wand2 className="w-4 h-4 text-purple-400 flex-shrink-0" />
          <p className="text-[11px] text-purple-300">{velionMessage}</p>
        </motion.div>
      )}

      {/* Advance button - always visible, fail-safe handles incomplete cast */}
      {(castComplete || isLocked) && (
        <Button className="w-full bg-green-700 hover:bg-green-800 text-xs mb-2"
          onClick={advanceToScreenplay} disabled={actionLoading === 'adv-screenplay'}
          data-testid={`popup-advance-screenplay-${film.id}`}>
          {actionLoading === 'adv-screenplay' ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <ChevronRight className="w-3 h-3 mr-1" />}
          Prosegui alla Sceneggiatura (2 CP)
        </Button>
      )}

      {/* FAIL-SAFE: Auto-complete cast button */}
      {showAutoComplete && !castComplete && !isLocked && (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <Button
            className="w-full bg-purple-700/80 hover:bg-purple-700 text-xs mb-2 border border-purple-500/30"
            onClick={autoCompleteCast}
            disabled={actionLoading === 'auto-complete'}
            data-testid={`popup-auto-complete-cast-${film.id}`}>
            {actionLoading === 'auto-complete'
              ? <RefreshCw className="w-3 h-3 animate-spin mr-1" />
              : <Wand2 className="w-3 h-3 mr-1" />}
            Completa Cast Automaticamente (50% costo)
          </Button>
          <p className="text-[9px] text-gray-500 text-center -mt-1 mb-1">Velion assegnerà i ruoli mancanti con attori adatti al genere</p>
        </motion.div>
      )}

      {/* Cast proposals per role */}
      {Object.entries(film.cast_proposals || {}).map(([role, proposals]) => {
        const hasSelection = role === 'actors' ? cast.actors?.length > 0 : cast[role === 'directors' ? 'director' : role === 'screenwriters' ? 'screenwriter' : 'composer'];
        const selected = role === 'actors' ? false : hasSelection;
        const available = proposals.filter(p => p.status === 'available');
        const pending = proposals.filter(p => p.status === 'pending');
        const roleKey = role;
        const isExpanded = expandedRoles[roleKey];

        return (
          <div key={role} className={`rounded border transition-all ${selected ? 'border-green-800 bg-green-500/5' : 'border-gray-700'}`}>
            <div className="flex items-center justify-between p-2 cursor-pointer hover:bg-white/5"
              onClick={() => setExpandedRoles(prev => ({ ...prev, [roleKey]: !prev[roleKey] }))}
              data-testid={`popup-role-${role}`}>
              <span className="text-xs font-medium">{roleLabels[role]}</span>
              <div className="flex items-center gap-1">
                {selected && <Badge className="bg-green-500/20 text-green-400 text-[9px]"><Check className="w-3 h-3 mr-0.5" />Scelto</Badge>}
                {!selected && <Badge className="bg-cyan-500/20 text-cyan-400 text-[9px]">{available.length} disp.</Badge>}
                {!selected && pending.length > 0 && (
                  <Button size="sm" className="h-5 px-1.5 text-[9px] bg-yellow-600 hover:bg-yellow-700"
                    disabled={actionLoading === `speed-${role}`}
                    onClick={(e) => { e.stopPropagation(); speedUp(role); }}>
                    <Zap className="w-2.5 h-2.5 mr-0.5" /> Sblocca
                  </Button>
                )}
                <ChevronRight className={`w-3.5 h-3.5 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </div>
            </div>

            {isExpanded && (
              <div className="px-2 pb-2 space-y-1">
                {/* Available proposals */}
                {!selected && available.map(prop => {
                  const person = prop.person || {};
                  const skills = person.skills || {};
                  const avgSkill = Object.values(skills).length > 0
                    ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;
                  const stars = person.stars || Math.ceil(avgSkill / 20);
                  const fameCat = person.fame_category || person.fame_badge || '';
                  const fameLabel = fameCat === 'superstar' ? 'Superstar' : fameCat === 'famous' ? 'Famoso' : fameCat === 'rising' ? 'Emergente' : fameCat === 'unknown' ? 'Sconosciuto' : '';
                  const isSkillExpanded = expandedSkills[prop.id];
                  return (
                    <div key={prop.id} className="rounded-lg border border-gray-800/50 hover:border-gray-700 bg-white/[0.02] overflow-hidden"
                      data-testid={`popup-proposal-${prop.id}`}>
                      <div className="p-2">
                        <div className="flex items-start gap-2">
                          {/* Avatar */}
                          <div className="w-9 h-9 rounded-full bg-cyan-500/20 flex items-center justify-center text-[11px] font-bold text-cyan-400 flex-shrink-0">
                            {person.name?.charAt(0)}
                          </div>
                          {/* Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <p className="text-xs font-semibold truncate">{person.name}</p>
                              {person.gender && (
                                <span className={`text-[10px] font-bold ${person.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>
                                  {person.gender === 'female' ? '♀' : '♂'}
                                </span>
                              )}
                              {[...Array(stars)].map((_, i) => <Star key={i} className="w-2.5 h-2.5 text-yellow-500 fill-yellow-500" />)}
                              {fameLabel && <Badge className="text-[7px] h-3.5 bg-yellow-500/10 text-yellow-400 border-yellow-500/20 px-1">{fameLabel}</Badge>}
                            </div>
                            <p className="text-[8px] text-gray-500 mt-0.5">
                              {person.nationality || ''}{person.age ? ` \u2022 ${person.age}a` : ''}{' \u2022 '}Skill: <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>
                              {person.films_count != null ? ` \u2022 ${person.films_count} film` : ''}
                            </p>
                            <div className="flex flex-wrap gap-0.5 mt-0.5">
                              {(person.strong_genres_names || []).map((g, i) => (
                                <span key={i} className="text-[7px] px-1 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-800/40">{g}</span>
                              ))}
                              {person.adaptable_genre_name && (
                                <span className="text-[7px] px-1 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-800/40">~ {person.adaptable_genre_name}</span>
                              )}
                            </div>
                            {person.agency_name && <p className="text-[7px] text-gray-600 mt-0.5">Agenzia: {person.agency_name}</p>}
                          </div>
                          {/* Cost + Actions */}
                          <div className="flex flex-col items-end gap-1 flex-shrink-0">
                            <span className="text-[9px] text-yellow-400 font-bold">${prop.cost?.toLocaleString()}</span>
                            {role === 'actors' && (
                              <select value={actorRoles[prop.id] || ''} onChange={e => setActorRoles(p => ({...p, [prop.id]: e.target.value}))}
                                onClick={e => e.stopPropagation()}
                                className="h-5 text-[8px] bg-gray-800 border border-gray-700 rounded px-0.5 text-white">
                                <option value="">Ruolo...</option>
                                {ACTOR_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                              </select>
                            )}
                            <Button size="sm" className="h-5 px-2 text-[9px] bg-cyan-700 hover:bg-cyan-800"
                              disabled={actionLoading === `select-${prop.id}`}
                              onClick={() => selectCast(role, prop.id)}>
                              <Check className="w-2.5 h-2.5 mr-0.5" /> Scegli
                            </Button>
                          </div>
                        </div>
                      </div>
                      {/* Mostra Skill toggle */}
                      {Object.keys(skills).length > 0 && (
                        <>
                          <button
                            className="w-full flex items-center gap-1 px-2 py-1 text-[9px] text-cyan-400 hover:bg-white/5 border-t border-gray-800/30"
                            onClick={(e) => { e.stopPropagation(); setExpandedSkills(p => ({...p, [prop.id]: !p[prop.id]})); }}
                            data-testid={`toggle-skills-${prop.id}`}>
                            {isSkillExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            Mostra Skill
                          </button>
                          {isSkillExpanded && (
                            <div className="px-2 pb-2 grid grid-cols-2 gap-1">
                              {Object.entries(skills).map(([skillName, skillVal]) => (
                                <div key={skillName} className="flex items-center justify-between bg-white/[0.03] rounded px-1.5 py-0.5">
                                  <span className="text-[8px] text-gray-400 capitalize truncate">{skillName.replace(/_/g, ' ')}</span>
                                  <span className={`text-[8px] font-bold ${skillVal >= 70 ? 'text-green-400' : skillVal >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>{skillVal}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  );
                })}
                {/* Pending */}
                {!selected && pending.length > 0 && available.length === 0 && (
                  <div className="flex items-center gap-1.5 p-2 text-[10px] text-gray-500">
                    <Clock className="w-3 h-3 animate-pulse text-yellow-500" />
                    {pending.length} agenti in arrivo...
                  </div>
                )}
                {/* Rejected */}
                {proposals.filter(p => p.status === 'rejected').map(prop => (
                  <div key={prop.id} className="p-2 bg-red-500/5 rounded border border-red-800/40">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-red-300">{prop.person?.name}</p>
                        <p className="text-[9px] text-red-400">Ha rifiutato</p>
                      </div>
                      <Button size="sm" className="h-5 px-2 text-[9px] bg-amber-700 hover:bg-amber-800"
                        disabled={actionLoading === `renego-${prop.id}`}
                        onClick={() => renegotiate(role, prop.id)}>
                        <RefreshCw className="w-2.5 h-2.5 mr-0.5" /> Rinegozia
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}

      {/* Agency actors section */}
      {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
        <div className="p-2 rounded-lg border border-purple-500/15 bg-purple-500/5 space-y-1.5">
          <p className="text-[10px] font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-1">
            <Users className="w-3 h-3" /> I tuoi Attori (Agenzia)
          </p>
          <div className="space-y-1.5 max-h-60 overflow-y-auto">
            {[...agencyActors.effective, ...agencyActors.school].map(actor => (
              <AgencyActorCardPopup key={actor.id} actor={actor}
                isSelected={!!selectedAgencyActors[actor.id]}
                onToggle={() => setSelectedAgencyActors(p => ({ ...p, [actor.id]: !p[actor.id] }))}
                roleValue={agencyRoles[actor.id] || 'Supporto'}
                onRoleChange={val => setAgencyRoles(p => ({...p, [actor.id]: val}))}
                ACTOR_ROLES={ACTOR_ROLES} />
            ))}
          </div>
          {Object.values(selectedAgencyActors).some(Boolean) && (
            <Button size="sm" className="w-full bg-purple-500 hover:bg-purple-600 text-white text-xs"
              onClick={submitAgencyCast} disabled={actionLoading === 'agency-cast'}>
              {actionLoading === 'agency-cast' ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Users className="w-3 h-3 mr-1" />}
              Aggiungi dall'Agenzia ({Object.values(selectedAgencyActors).filter(Boolean).length})
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// ─── SCREENPLAY STEP ───
function ScreenplayStepContent({ film, api, onRefresh, refreshUser }) {
  const [mode, setMode] = useState('ai');
  const [manualText, setManualText] = useState('');
  const [loading, setLoading] = useState(null);
  const [expandedScreenplay, setExpandedScreenplay] = useState(false);

  const screenplayText = typeof film.screenplay === 'string' ? film.screenplay
    : (film.screenplay && typeof film.screenplay === 'object') ? (film.screenplay.text || '') : '';
  const hasScreenplay = !!screenplayText;
  const isFullPackage = film.from_emerging_screenplay && film.emerging_option === 'full_package';

  const writeScreenplay = async () => {
    setLoading('write');
    try {
      const res = await api.post(`/film-pipeline/${film.id}/write-screenplay`, {
        mode, manual_text: mode === 'manual' ? manualText : undefined
      }, { timeout: 120000 });
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setLoading(null); }
  };

  const advance = async () => {
    setLoading('advance');
    try {
      const res = await api.post(`/film-pipeline/${film.id}/advance-to-preproduction`);
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setLoading(null); }
  };

  return (
    <div className="space-y-2" data-testid={`popup-screenplay-${film.id}`}>
      {(hasScreenplay || isFullPackage) && (
        <Button className="w-full bg-green-700 hover:bg-green-800 text-xs mb-1"
          onClick={advance} disabled={loading === 'advance'}
          data-testid={`popup-advance-preprod-${film.id}`}>
          {loading === 'advance' ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <ChevronRight className="w-3 h-3 mr-1" />}
          Pre-Produzione (3 CP)
        </Button>
      )}

      {/* Show screenplay if exists */}
      {hasScreenplay && (
        <div className="p-2 bg-green-500/5 rounded border border-green-500/20">
          <div className="flex items-center justify-between mb-0.5">
            <p className="text-[9px] text-green-400 font-medium">Sceneggiatura completata</p>
            <button onClick={() => setExpandedScreenplay(!expandedScreenplay)}
              className="text-[8px] text-green-400/70 hover:text-green-300 flex items-center gap-0.5">
              {expandedScreenplay ? 'Riduci' : 'Espandi'}
              <ChevronDown className={`w-2.5 h-2.5 transition-transform ${expandedScreenplay ? 'rotate-180' : ''}`} />
            </button>
          </div>
          <div className={expandedScreenplay ? '' : 'max-h-[120px] overflow-hidden relative'}>
            <p className="text-[10px] text-gray-300 whitespace-pre-line leading-relaxed">{screenplayText}</p>
            {!expandedScreenplay && <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-[#111113] to-transparent" />}
          </div>
        </div>
      )}

      {/* Write screenplay */}
      {!hasScreenplay && !isFullPackage && (
        <>
          <div className="p-2 bg-yellow-500/5 rounded border border-yellow-500/20">
            <p className="text-[9px] text-yellow-400 font-medium mb-0.5">Pre-Sceneggiatura</p>
            <p className="text-[10px] text-gray-400 italic">"{film.pre_screenplay}"</p>
          </div>
          <div className="flex gap-1.5">
            {[
              { id: 'ai', label: 'AI ($80K)' },
              { id: 'pre_only', label: 'Solo Pre ($0)' },
              { id: 'manual', label: 'Scrivi ($20K)' }
            ].map(opt => (
              <button key={opt.id} onClick={() => setMode(opt.id)}
                className={`flex-1 p-2 rounded text-center border transition-all ${
                  mode === opt.id ? 'border-cyan-500 bg-cyan-500/10' : 'border-gray-700'
                }`}>
                <p className="text-[10px] font-medium text-gray-200">{opt.label}</p>
              </button>
            ))}
          </div>
          {mode === 'manual' && (
            <Textarea value={manualText} onChange={e => setManualText(e.target.value)}
              placeholder="Scrivi la sceneggiatura..." className="bg-black/30 border-gray-700 text-white min-h-[80px] text-xs" />
          )}
          <Button onClick={writeScreenplay} disabled={loading === 'write'}
            className="w-full bg-cyan-700 hover:bg-cyan-800 text-xs">
            {loading === 'write' ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <BookOpen className="w-3 h-3 mr-1" />}
            {mode === 'ai' ? 'Genera Sceneggiatura AI' : mode === 'manual' ? 'Salva' : 'Usa Solo Pre'}
          </Button>
        </>
      )}
    </div>
  );
}

// ─── PRE-PRODUCTION STEP ───
function ProductionStepContent({ film, api, onRefresh, refreshUser }) {
  const [actionLoading, setActionLoading] = useState(null);

  const hasSetup = film.production_setup?.setup_completed;
  const remasterInProgress = film.remaster_started_at && !film.remaster_completed;

  const startShooting = async () => {
    setActionLoading('shoot');
    try {
      const res = await api.post(`/film-pipeline/${film.id}/start-shooting`);
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const remaster = async () => {
    setActionLoading('remaster');
    try {
      const res = await api.post(`/film-pipeline/${film.id}/remaster`);
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  return (
    <div className="space-y-2" data-testid={`popup-production-${film.id}`}>
      {hasSetup && (
        <div className="p-2 bg-black/30 rounded border border-gray-700 text-[10px] text-gray-400">
          <p>Comparse: {film.production_setup.extras_count} | CGI: {film.production_setup.cgi_packages?.length || 0} | VFX: {film.production_setup.vfx_packages?.length || 0}</p>
          <p>Costo: <span className="text-yellow-400">${film.production_setup.total_cost?.toLocaleString()}</span></p>
        </div>
      )}

      {remasterInProgress && (
        <div className="p-2 bg-yellow-500/10 rounded border border-yellow-500/20">
          <div className="flex items-center gap-1.5">
            <RefreshCw className="w-3 h-3 animate-spin text-yellow-400" />
            <span className="text-[10px] text-yellow-300">Rimasterizzazione... {Math.round(film.remaster_remaining_minutes || 0)} min</span>
          </div>
        </div>
      )}

      {film.sponsors?.length > 0 && (
        <div className="p-2 bg-cyan-500/5 rounded border border-cyan-500/20 text-[10px] text-gray-400">
          <p className="text-[9px] text-cyan-400 font-medium">Sponsor:</p>
          <div className="flex flex-wrap gap-1">
            {film.sponsors.map(sp => (
              <Badge key={sp.id} className="text-[8px] h-4" style={{ backgroundColor: sp.logo_color + '20', color: sp.logo_color }}>
                {sp.name}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        {!film.remaster_started_at && (
          <Button size="sm" variant="outline" className="text-xs border-yellow-700 text-yellow-400"
            disabled={actionLoading === 'remaster'} onClick={remaster}>
            <Star className="w-3 h-3 mr-1" /> Rimasterizza
          </Button>
        )}
        <Button size="sm" className="flex-1 bg-red-700 hover:bg-red-800 text-xs"
          disabled={remasterInProgress || actionLoading === 'shoot'} onClick={startShooting}
          data-testid={`popup-ciak-${film.id}`}>
          <Play className="w-3 h-3 mr-1" /> Ciak! (3 CP)
        </Button>
      </div>
    </div>
  );
}

// ─── SHOOTING/RELEASE STEP with Cinematic Animation ───
function ReleaseStepContent({ film, api, onRefresh, refreshUser }) {
  const [actionLoading, setActionLoading] = useState(null);
  const [releaseStrategy, setReleaseStrategy] = useState(null);
  const [manualHours, setManualHours] = useState(null);
  const [releaseResult, setReleaseResult] = useState(null);
  const [releasePhase, setReleasePhase] = useState(0);
  const [trailerSlide, setTrailerSlide] = useState(0);
  const [animatedQuality, setAnimatedQuality] = useState(0);
  const [animatedRevenue, setAnimatedRevenue] = useState(0);

  const progress = Math.min(100, ((film.shooting_day_current || 0) / Math.max(1, film.shooting_days || 5)) * 100);
  const completed = film.shooting_completed || progress >= 100;

  const speedUp = async (option) => {
    setActionLoading('speed');
    try {
      const res = await api.post(`/film-pipeline/${film.id}/speed-up-shooting`, { option });
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const release = async () => {
    setActionLoading('release');
    // Immediately show loading state
    setReleasePhase(0);
    try {
      const res = await api.post(`/film-pipeline/${film.id}/release`, {}, { timeout: 60000 });
      const data = res.data;
      setReleaseResult(data);
      setTrailerSlide(0);
      setAnimatedQuality(0);
      setAnimatedRevenue(0);

      // 5-phase cinematic sequence
      const hasTrailer = data.screenplay_scenes && data.screenplay_scenes.length > 0;
      const hasEvent = data.release_event && data.release_event.id !== 'nothing_special';

      // Phase 1: Intro (cinema image)
      setReleasePhase(1);

      // Phase 2: Trailer slideshow
      const trailerDelay = 2000;
      if (hasTrailer) {
        setTimeout(() => {
          setReleasePhase(2);
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

      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore nel rilascio'); setReleaseResult(null); }
    finally { setActionLoading(null); }
  };

  const confirmStrategy = async () => {
    if (!releaseStrategy) return;
    const hours = releaseStrategy === 'manual' ? (manualHours || 24) : 24;
    setActionLoading('strategy');
    try {
      const res = await api.post(`/film-pipeline/${film.id}/choose-release-strategy`, { strategy: releaseStrategy, hours });
      toast.success(`Strategia confermata! Uscita tra ${res.data.hours_until_release}h`);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  // Cinematic Release Overlay
  if (releaseResult && releasePhase > 0) {
    const fmtRev = (v) => v > 999999 ? (v / 1000000).toFixed(1) + 'M' : v > 999 ? (v / 1000).toFixed(0) + 'K' : v;
    return (
      <div className="space-y-0" data-testid="release-cinematic">
        <style>{`
          @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
          @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
          @keyframes scaleIn { from { opacity: 0; transform: scale(0.85); } to { opacity: 1; transform: scale(1); } }
          @keyframes eventReveal { from { opacity: 0; transform: scale(0.9) translateY(15px); } to { opacity: 1; transform: scale(1) translateY(0); } }
          @keyframes shakeIn { 0% { opacity: 0; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1.04); } 55% { transform: scale(1) rotate(-1deg); } 70% { transform: scale(1.02) rotate(1deg); } 85% { transform: scale(1) rotate(-0.5deg); } 100% { transform: scale(1) rotate(0); } }
          @keyframes shimmer { 0%, 100% { transform: translateX(-100%); } 50% { transform: translateX(100%); } }
          @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.08); } }
          @keyframes successZoom { 0% { opacity: 0; transform: scale(1.15); } 60% { opacity: 1; transform: scale(1.02); } 100% { opacity: 1; transform: scale(1); } }
          @keyframes slowZoom { 0% { transform: scale(1); } 100% { transform: scale(1.06); } }
          @keyframes flopFade { 0% { opacity: 0; transform: scale(0.98); } 100% { opacity: 1; transform: scale(1); } }
          @keyframes glowPulse { 0%, 100% { box-shadow: inset 0 0 40px rgba(234, 179, 8, 0.1); } 50% { box-shadow: inset 0 0 80px rgba(234, 179, 8, 0.2); } }
        `}</style>

        {/* PHASE 1: Cinema Image + Intro */}
        <div className={`relative w-full overflow-hidden rounded-t-lg ${
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
            <div className={`absolute inset-0 ${
              releaseResult.release_outcome === 'success'
                ? 'bg-gradient-to-t from-black via-black/30 to-transparent'
                : releaseResult.release_outcome === 'flop'
                ? 'bg-gradient-to-t from-black via-black/50 to-blue-950/30'
                : 'bg-gradient-to-t from-black via-black/40 to-transparent'
            }`} />
            {releaseResult.release_outcome === 'success' && (
              <div className="absolute inset-0 pointer-events-none" style={{ animation: 'glowPulse 2s ease-in-out infinite' }} />
            )}
            <div className="absolute bottom-0 left-0 right-0 p-3 text-center">
              {releasePhase === 1 && (
                <p className="text-xs text-white/80 italic" style={{ animation: 'fadeIn 0.8s ease-out 0.3s both' }}>
                  Il tuo film sta uscendo nelle sale...
                </p>
              )}
              {releasePhase >= 2 && (
                <>
                  <h1 className="text-lg font-black text-white tracking-tight" style={{ animation: 'scaleIn 0.5s ease-out both' }}>
                    {releaseResult.title}
                  </h1>
                  {releaseResult.modifiers?.cast_quality > 0 && (
                    <p className="text-[9px] text-yellow-400/70 mt-0.5 uppercase tracking-[0.2em]" style={{ animation: 'fadeIn 0.4s ease-out 0.3s both' }}>
                      Un film di {film.cast?.director?.name || 'il tuo regista'}
                    </p>
                  )}
                </>
              )}
              {releaseResult.hype_level > 0 && releasePhase <= 2 && (
                <div className="mt-1.5 flex items-center justify-center gap-1.5" style={{ animation: 'fadeIn 0.5s ease-out 0.6s both' }}>
                  <div className="h-1 bg-white/10 rounded-full w-20 overflow-hidden">
                    <div className={`h-full rounded-full ${
                      releaseResult.hype_level >= 60 ? 'bg-yellow-400' : releaseResult.hype_level >= 30 ? 'bg-amber-500' : 'bg-gray-400'
                    }`} style={{ width: `${releaseResult.hype_level}%`, transition: 'width 1s ease-out' }} />
                  </div>
                  <span className="text-[8px] text-white/40">Hype {releaseResult.hype_level}%</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* PHASE 2: Screenplay Trailer */}
        {releasePhase >= 2 && releaseResult.screenplay_scenes?.length > 0 && (
          <div className="bg-black/80 px-3 py-2 border-x border-white/5" data-testid="release-trailer">
            <p className="text-[8px] text-white/30 uppercase tracking-[0.2em] text-center mb-1.5" style={{ animation: 'fadeIn 0.4s ease-out both' }}>
              Anteprima Sceneggiatura
            </p>
            <div className="relative h-10 overflow-hidden">
              {releaseResult.screenplay_scenes.map((scene, i) => (
                <p key={i} className={`absolute inset-0 flex items-center justify-center text-center text-[10px] leading-relaxed italic transition-all duration-500 ${
                  trailerSlide === i ? 'opacity-100 translate-y-0' : trailerSlide > i ? 'opacity-0 -translate-y-4' : 'opacity-0 translate-y-4'
                } ${
                  releaseResult.release_outcome === 'success' ? 'text-yellow-200/80' :
                  releaseResult.release_outcome === 'flop' ? 'text-blue-200/60' : 'text-gray-300/70'
                }`}>
                  &quot;{scene.length > 60 ? scene.substring(0, 60) + '...' : scene}&quot;
                </p>
              ))}
            </div>
            <div className="flex justify-center gap-1 mt-1">
              {releaseResult.screenplay_scenes.map((_, i) => (
                <div key={i} className={`w-1 h-1 rounded-full transition-all duration-300 ${
                  trailerSlide >= i ? 'bg-white/50 scale-110' : 'bg-white/15'
                }`} />
              ))}
            </div>
          </div>
        )}

        {/* PHASE 3: Event Reveal */}
        {releasePhase >= 3 && releaseResult.release_event && releaseResult.release_event.id !== 'nothing_special' && (() => {
          const evt = releaseResult.release_event;
          const isRare = evt.rarity === 'rare';
          const borderColor = evt.type === 'positive' ? 'border-emerald-500' : evt.type === 'negative' ? 'border-red-500' : 'border-amber-500';
          const bgGrad = evt.type === 'positive' ? 'from-emerald-950/80 to-[#0a0a0b]' : evt.type === 'negative' ? 'from-red-950/80 to-[#0a0a0b]' : 'from-amber-950/80 to-[#0a0a0b]';
          const accentColor = evt.type === 'positive' ? 'text-emerald-400' : evt.type === 'negative' ? 'text-red-400' : 'text-amber-400';
          return (
            <div className={`relative border-x-2 border-b ${borderColor} bg-gradient-to-b ${bgGrad} p-2.5 ${isRare ? 'ring-1 ring-purple-500/50' : ''}`}
              style={{ animation: isRare ? 'shakeIn 0.7s ease-out both' : 'eventReveal 0.8s ease-out both' }}
              data-testid="release-event">
              {isRare && <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/10 to-transparent" style={{ animation: 'shimmer 2s ease-in-out infinite' }} />
              </div>}
              <div className="flex items-center justify-center gap-2 mb-1.5">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
                  evt.type === 'positive' ? 'bg-emerald-500/20' : evt.type === 'negative' ? 'bg-red-500/20' : 'bg-amber-500/20'
                }`} style={{ animation: 'pulse 1.5s ease-in-out infinite' }}>
                  <Sparkles className={`w-3.5 h-3.5 ${accentColor}`} />
                </div>
                <div className="text-center">
                  {isRare && <Badge className="bg-purple-500/30 text-purple-300 text-[7px] mb-0.5 border border-purple-500/40">EVENTO RARO</Badge>}
                  <h3 className={`text-[10px] font-black ${accentColor} uppercase tracking-wider`}>{evt.name}</h3>
                </div>
              </div>
              <p className="text-[9px] text-gray-300 text-center leading-relaxed mb-1.5">{evt.description}</p>
              <div className="flex justify-center gap-2 text-[9px] font-bold">
                {evt.quality_modifier !== 0 && (
                  <div className={`px-1.5 py-0.5 rounded-full ${evt.quality_modifier > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                    Qualita {evt.quality_modifier > 0 ? '+' : ''}{evt.quality_modifier}
                  </div>
                )}
                {evt.revenue_modifier !== 0 && (
                  <div className={`px-1.5 py-0.5 rounded-full ${evt.revenue_modifier > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                    Incassi {evt.revenue_modifier > 0 ? '+' : ''}{evt.revenue_modifier}%
                  </div>
                )}
              </div>
            </div>
          );
        })()}

        {/* PHASE 4: Animated Numbers */}
        {releasePhase >= 4 && (
          <div className="bg-[#0d0d0e] px-3 py-2.5 border-x border-white/5" style={{ animation: 'slideUp 0.6s ease-out both' }}
            data-testid="release-numbers">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className={`text-xl font-black tabular-nums ${
                  releaseResult.quality_score >= 70 ? 'text-green-400' : releaseResult.quality_score >= 50 ? 'text-yellow-400' : 'text-red-400'
                }`}>{animatedQuality}</div>
                <p className="text-[7px] text-gray-500 uppercase tracking-wide">Qualita</p>
              </div>
              <div>
                <div className="text-xl font-black tabular-nums text-yellow-400">
                  {releaseResult.imdb_rating?.toFixed?.(1) || '-'}
                </div>
                <p className="text-[7px] text-gray-500 uppercase tracking-wide">IMDb</p>
              </div>
              <div>
                <div className="text-xl font-black tabular-nums text-green-400">
                  ${fmtRev(animatedRevenue)}
                </div>
                <p className="text-[7px] text-gray-500 uppercase tracking-wide">Apertura</p>
              </div>
            </div>
            {/* Tier badge */}
            <div className="flex justify-center mt-1.5">
              <Badge className={`text-[9px] px-2.5 py-0.5 ${
                releaseResult.tier === 'masterpiece' ? 'bg-yellow-500 text-black' :
                releaseResult.tier === 'excellent' ? 'bg-green-500/30 text-green-300' :
                releaseResult.tier === 'good' ? 'bg-blue-500/30 text-blue-300' :
                releaseResult.tier === 'mediocre' ? 'bg-gray-500/30 text-gray-300' :
                'bg-red-500/30 text-red-300'
              }`} style={{ animation: 'scaleIn 0.4s ease-out 0.8s both' }}>
                {releaseResult.tier_label}
              </Badge>
            </div>
          </div>
        )}

        {/* PHASE 5: Final Result + Soundtrack + Modifiers */}
        {releasePhase >= 5 && (
          <div className={`rounded-b-lg overflow-hidden ${
            releaseResult.release_outcome === 'success' ? 'bg-gradient-to-b from-[#0d0d0e] to-yellow-950/20' :
            releaseResult.release_outcome === 'flop' ? 'bg-gradient-to-b from-[#0d0d0e] to-blue-950/20' :
            'bg-[#0d0d0e]'
          }`} style={{ animation: 'slideUp 0.5s ease-out both' }} data-testid="release-final">
            {/* Outcome message */}
            <div className={`text-center py-2 px-3 ${
              releaseResult.release_outcome === 'success' ? 'border-t border-yellow-500/30' :
              releaseResult.release_outcome === 'flop' ? 'border-t border-blue-500/20' :
              'border-t border-white/10'
            }`}>
              <p className={`text-xs font-bold ${
                releaseResult.release_outcome === 'success' ? 'text-yellow-400' :
                releaseResult.release_outcome === 'flop' ? 'text-blue-300/70' : 'text-gray-300'
              }`} style={{ animation: 'scaleIn 0.4s ease-out both' }}>
                {releaseResult.release_outcome === 'success' ? "Evento dell'anno!" :
                 releaseResult.release_outcome === 'flop' ? "Il pubblico non ha risposto..." : "Buona accoglienza"}
              </p>
              <p className="text-green-400 text-[10px] mt-0.5">+{releaseResult.xp_gained} XP</p>
            </div>

            {/* Compact details */}
            <div className="px-2.5 pb-2 space-y-1">
              {/* Soundtrack Score */}
              {releaseResult.modifiers?.soundtrack > 0 && (
                <div className="flex items-center gap-1.5 p-1.5 bg-purple-500/10 border border-purple-500/20 rounded text-[9px]">
                  <Sparkles className="w-3 h-3 text-purple-400" />
                  <span className="text-purple-300 font-medium">Colonna Sonora:</span>
                  <span className="text-purple-200">+{releaseResult.modifiers.soundtrack} qualita</span>
                  {releaseResult.modifiers?.soundtrack >= 3 && <Badge className="bg-purple-500/20 text-purple-300 text-[7px]">Eccellente</Badge>}
                </div>
              )}
              {/* Sponsors */}
              {releaseResult.sponsors?.length > 0 && (
                <div className="text-[8px] text-gray-400 p-1.5 bg-black/30 rounded border border-cyan-500/10">
                  <span className="font-medium text-cyan-300 mr-1">Sponsor:</span>
                  {releaseResult.sponsors.map(sp => (
                    <Badge key={sp.id || sp.name} className="text-[7px] h-3 mr-0.5" style={{ backgroundColor: (sp.logo_color || '#666') + '20', color: sp.logo_color || '#aaa' }}>
                      {sp.name}
                    </Badge>
                  ))}
                </div>
              )}
              {/* Modifiers breakdown */}
              <div className="text-[8px] text-gray-500 p-1.5 bg-black/30 rounded flex flex-wrap gap-x-2 gap-y-0.5">
                <span>Pre-IMDb: {releaseResult.modifiers?.pre_imdb}</span>
                <span>Cast: {releaseResult.modifiers?.cast_quality}</span>
                <span>Soundtrack: +{releaseResult.modifiers?.soundtrack || 0}</span>
                <span>Buzz: {releaseResult.modifiers?.buzz > 0 ? '+' : ''}{releaseResult.modifiers?.buzz}</span>
                <span>Remaster: +{releaseResult.modifiers?.remaster || 0}</span>
              </div>
              {/* Advanced factors */}
              {releaseResult.modifiers?.advanced_factors && Object.keys(releaseResult.modifiers.advanced_factors).length > 0 && (
                <div className="text-[8px] text-gray-500 p-1.5 bg-black/30 rounded flex flex-wrap gap-x-2 gap-y-0.5">
                  {Object.entries(releaseResult.modifiers.advanced_factors).map(([key, val]) => (
                    <span key={key} className={`${String(val).startsWith('+') || String(val).startsWith('-') ? (String(val).startsWith('+') ? 'text-green-400' : 'text-red-400') : ''}`}>
                      {key.replace(/_/g, ' ')}: {val}
                    </span>
                  ))}
                </div>
              )}
              {/* Cost */}
              <div className="text-[8px] text-gray-500 p-1.5 bg-black/30 rounded">
                Denaro: <span className="text-yellow-400/80">${releaseResult.cost_summary?.total_money?.toLocaleString()}</span> | CinePass: <span className="text-cyan-400/80">{releaseResult.cost_summary?.total_cinepass} CP</span>
              </div>
              {/* Critic Reviews */}
              {releaseResult.critic_reviews?.length > 0 && (
                <div className="space-y-1 mt-1">
                  <p className="text-[8px] text-gray-400 font-medium uppercase tracking-wider">Recensioni</p>
                  {releaseResult.critic_reviews.slice(0, 3).map((review, idx) => (
                    <div key={idx} className="text-[8px] p-1.5 bg-black/30 rounded border-l-2 border-gray-700" style={{ animation: `fadeIn 0.3s ease-out ${0.2 + idx * 0.15}s both` }}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-gray-300 font-medium">{review.source || review.critic_name || 'Critico'}</span>
                        <span className={`font-bold ${
                          (review.score || review.rating || 0) >= 7 ? 'text-green-400' :
                          (review.score || review.rating || 0) >= 5 ? 'text-yellow-400' : 'text-red-400'
                        }`}>{(review.score || review.rating || 0).toFixed?.(1) || review.score}/10</span>
                      </div>
                      <p className="text-gray-500 italic leading-relaxed">&quot;{review.text || review.comment || ''}&quot;</p>
                    </div>
                  ))}
                </div>
              )}
              {/* Audience Satisfaction */}
              {releaseResult.audience_satisfaction > 0 && (
                <div className="flex items-center gap-2 p-1.5 bg-black/30 rounded">
                  <Users className="w-3 h-3 text-blue-400" />
                  <div className="flex-1">
                    <div className="flex justify-between text-[8px]">
                      <span className="text-gray-400">Soddisfazione Pubblico</span>
                      <span className={`font-bold ${releaseResult.audience_satisfaction >= 70 ? 'text-green-400' : releaseResult.audience_satisfaction >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {releaseResult.audience_satisfaction}%
                      </span>
                    </div>
                    <div className="h-1 bg-gray-800 rounded-full mt-0.5">
                      <div className={`h-full rounded-full ${releaseResult.audience_satisfaction >= 70 ? 'bg-green-500' : releaseResult.audience_satisfaction >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${releaseResult.audience_satisfaction}%`, transition: 'width 1s ease-out' }} />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 px-2.5 pb-2.5">
              <Button onClick={() => { setReleaseResult(null); setReleasePhase(0); window.location.href = `/films/${releaseResult.film_id}`; }}
                className={`flex-1 text-[10px] h-8 ${
                  releaseResult.release_outcome === 'success' ? 'bg-yellow-600 hover:bg-yellow-500 text-black' :
                  releaseResult.release_outcome === 'flop' ? 'bg-blue-700 hover:bg-blue-600 text-white' :
                  'bg-amber-600 hover:bg-amber-500 text-black'
                }`} data-testid="release-go-film">
                <Film className="w-3 h-3 mr-1" /> Vai al Film
              </Button>
              <Button onClick={() => { setReleaseResult(null); setReleasePhase(0); onRefresh(); }} variant="outline" className="border-gray-700 text-[10px] h-8" data-testid="release-close">
                Chiudi
              </Button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2" data-testid={`popup-release-${film.id}`}>
      <div className="flex items-center justify-between">
        <p className="text-[10px] text-gray-500">Giorno {film.shooting_day_current || 0}/{film.shooting_days || 5}</p>
        {completed ? (
          <Badge className="bg-green-500/20 text-green-400 text-[10px]">Completato!</Badge>
        ) : (
          <Badge className="bg-blue-500/20 text-blue-400 text-[10px]">{Math.round(progress)}%</Badge>
        )}
      </div>
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all bg-gradient-to-r from-blue-500 to-green-500" style={{ width: `${progress}%` }} />
      </div>

      {completed ? (
        film.release_type === 'coming_soon' ? (
          <div className="space-y-2">
            <p className="text-xs font-bold text-white">Strategia di Uscita</p>
            <div className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
              releaseStrategy === 'auto' ? 'border-yellow-500/60 bg-yellow-500/10' : 'border-gray-700/60 hover:border-gray-600'
            }`} onClick={() => setReleaseStrategy('auto')}>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-400" />
                <div>
                  <p className="text-[11px] font-bold text-white">Automatica</p>
                  <p className="text-[9px] text-emerald-400">+3% incassi</p>
                </div>
              </div>
            </div>
            <div className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
              releaseStrategy === 'manual' ? 'border-cyan-500/60 bg-cyan-500/10' : 'border-gray-700/60 hover:border-gray-600'
            }`} onClick={() => setReleaseStrategy('manual')}>
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-cyan-400" />
                <div>
                  <p className="text-[11px] font-bold text-white">Manuale</p>
                  <p className="text-[9px] text-amber-400">Tempismo perfetto: +8%!</p>
                </div>
              </div>
              {releaseStrategy === 'manual' && (
                <div className="mt-2 grid grid-cols-4 gap-1.5 ml-6">
                  {[6, 12, 24, 48].map(h => (
                    <button key={h} className={`py-1 rounded text-[10px] font-medium border transition-all ${
                      manualHours === h ? 'border-cyan-500 bg-cyan-500/15 text-cyan-400' : 'border-gray-700 text-gray-400'
                    }`} onClick={(e) => { e.stopPropagation(); setManualHours(h); }}>{h}h</button>
                  ))}
                </div>
              )}
            </div>
            <Button className="w-full bg-gradient-to-r from-yellow-600 to-amber-600 hover:from-yellow-500 text-white text-xs font-bold"
              disabled={!releaseStrategy || (releaseStrategy === 'manual' && !manualHours) || actionLoading === 'strategy'}
              onClick={confirmStrategy}>
              {actionLoading === 'strategy' ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
              Conferma Strategia
            </Button>
          </div>
        ) : (
          <Button className="w-full bg-green-700 hover:bg-green-800 text-xs" disabled={actionLoading === 'release'}
            onClick={release} data-testid={`popup-release-btn-${film.id}`}>
            {actionLoading === 'release' ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Film className="w-3 h-3 mr-1" />}
            Rilascia al Cinema!
          </Button>
        )
      ) : (
        <div className="flex gap-1.5">
          <Button size="sm" variant="outline" className="flex-1 text-[9px] border-gray-700" disabled={actionLoading === 'speed'}
            onClick={() => speedUp('fast')}>
            <Zap className="w-2.5 h-2.5 mr-0.5" /> 50% ($50K)
          </Button>
          <Button size="sm" variant="outline" className="flex-1 text-[9px] border-yellow-700 text-yellow-400" disabled={actionLoading === 'speed'}
            onClick={() => speedUp('faster')}>
            <Zap className="w-2.5 h-2.5 mr-0.5" /> 80% ($90K)
          </Button>
          <Button size="sm" className="flex-1 text-[9px] bg-red-700 hover:bg-red-800" disabled={actionLoading === 'speed'}
            onClick={() => speedUp('instant')}>
            <Zap className="w-2.5 h-2.5 mr-0.5" /> Subito! ($150K)
          </Button>
        </div>
      )}
    </div>
  );
}

// ─── DISCARD BUTTON ───
function DiscardButton({ film, api, onRefresh, refreshUser }) {
  const [loading, setLoading] = useState(false);

  const discard = async () => {
    if (!window.confirm(`Scartare "${film.title}"?`)) return;
    setLoading(true);
    try {
      const res = await api.post(`/film-pipeline/${film.id}/discard`);
      toast.success(res.data.message);
      refreshUser(); onRefresh();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setLoading(false); }
  };

  if (film.status === 'coming_soon') return null;

  return (
    <Button size="sm" variant="outline" className="w-full text-[9px] border-red-800/50 text-red-400/60 hover:bg-red-500/10 h-7 mt-2"
      onClick={discard} disabled={loading} data-testid={`popup-discard-${film.id}`}>
      {loading ? <RefreshCw className="w-2.5 h-2.5 animate-spin mr-1" /> : <ThumbsDown className="w-2.5 h-2.5 mr-1" />}
      Scarta Progetto
    </Button>
  );
}

// ═══════════════════════════════════════════
// MAIN POPUP COMPONENT
// ═══════════════════════════════════════════
export default function FilmPopup({ film, open, onClose, onRefresh, countdown }) {
  const { api, refreshUser } = useContext(AuthContext);

  if (!film) return null;

  const currentStep = getCurrentStepId(film);
  const isCS = film.release_type === 'coming_soon' || film.status === 'ready_for_casting' || film.status === 'coming_soon';
  const isImmediate = !isCS;

  // Determine which step content to show
  const renderStepContent = () => {
    // For immediate mode: proposed films need to advance to casting
    if (isImmediate && film.status === 'proposed') {
      return <ProposedAdvanceStep film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} />;
    }

    // Poster step (CS mode only)
    if (currentStep === 'poster') {
      return <PosterStep film={film} api={api} onRefresh={onRefresh} />;
    }

    // Hype/Coming Soon step (CS mode)
    if (currentStep === 'hype') {
      return <HypeStep film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} countdown={countdown} />;
    }

    // Casting step
    if (currentStep === 'casting' && film.status === 'casting') {
      return <CastingStepContent film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} />;
    }
    if (currentStep === 'casting' && (film.status === 'ready_for_casting')) {
      return <ProposedAdvanceStep film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} />;
    }

    // Screenplay step
    if (currentStep === 'script') {
      return <ScreenplayStepContent film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} />;
    }

    // Production step
    if (currentStep === 'produzione') {
      return <ProductionStepContent film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} />;
    }

    // Shooting/Release step
    if (currentStep === 'uscita') {
      return <ReleaseStepContent film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} />;
    }

    // Fallback: ready_for_casting ALWAYS shows advance button
    if (film.status === 'ready_for_casting') {
      return <ProposedAdvanceStep film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} />;
    }

    return <p className="text-[10px] text-gray-500 text-center py-4">Stato: {film.status}</p>;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#0f0f10] border-gray-800/60 text-white w-[calc(100vw-1.5rem)] max-w-md max-h-[85vh] overflow-y-auto p-3 sm:p-4 rounded-xl" data-testid={`film-popup-${film.id}`}>
        <DialogTitle className="sr-only">{film.title}</DialogTitle>
        <DialogDescription className="sr-only">Dettagli produzione di {film.title}</DialogDescription>
        {/* Film header */}
        <FilmHeader film={film} />

        {/* Per-film step bar */}
        <FilmStepBar film={film} />

        {/* Step content */}
        <div className="mt-1">
          {renderStepContent()}
        </div>

        {/* Discard */}
        <DiscardButton film={film} api={api} onRefresh={onRefresh} refreshUser={refreshUser} />
      </DialogContent>
    </Dialog>
  );
}
