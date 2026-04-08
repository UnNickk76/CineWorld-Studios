import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Film, Star, Zap, Clock, ChevronLeft, ChevronRight, Check, Eye, X,
  Plus, Sparkles, Camera, Clapperboard, Megaphone, Award, Ticket,
  MapPin, Palette, FileText, Lock, Users, Music, Wand2, Play,
  Timer, TrendingUp, DollarSign, Building2, Globe, Heart, Send
} from 'lucide-react';
import { Badge } from '../components/ui/badge';
import { useToast } from '../hooks/use-toast';

const API = process.env.REACT_APP_BACKEND_URL;

// ═══════════════════════════════════════════════════════════════
//  CONSTANTS
// ═══════════════════════════════════════════════════════════════

const V2_STEPS = [
  { id: 'idea',      label: 'IDEA',      icon: Sparkles, color: 'amber'  },
  { id: 'hype',      label: 'HYPE',      icon: TrendingUp, color: 'orange' },
  { id: 'cast',      label: 'CAST',      icon: Users,    color: 'cyan'   },
  { id: 'prep',      label: 'PREP',      icon: Camera,   color: 'blue'   },
  { id: 'ciak',      label: 'CIAK',      icon: Clapperboard, color: 'red' },
  { id: 'finalcut',  label: 'FINAL CUT', icon: Film,     color: 'purple' },
  { id: 'marketing', label: 'MARKETING', icon: Megaphone, color: 'green'  },
  { id: 'laprima',   label: 'LA PRIMA',  icon: Award,    color: 'yellow' },
  { id: 'uscita',    label: 'USCITA',    icon: Ticket,   color: 'emerald'},
];

const STEP_STYLES = {
  amber:   { active: 'border-amber-500 bg-amber-500/15 text-amber-400', line: 'bg-amber-600', text: 'text-amber-400' },
  orange:  { active: 'border-orange-500 bg-orange-500/15 text-orange-400', line: 'bg-orange-600', text: 'text-orange-400' },
  cyan:    { active: 'border-cyan-500 bg-cyan-500/15 text-cyan-400', line: 'bg-cyan-600', text: 'text-cyan-400' },
  blue:    { active: 'border-blue-500 bg-blue-500/15 text-blue-400', line: 'bg-blue-600', text: 'text-blue-400' },
  red:     { active: 'border-red-500 bg-red-500/15 text-red-400', line: 'bg-red-600', text: 'text-red-400' },
  purple:  { active: 'border-purple-500 bg-purple-500/15 text-purple-400', line: 'bg-purple-600', text: 'text-purple-400' },
  green:   { active: 'border-green-500 bg-green-500/15 text-green-400', line: 'bg-green-600', text: 'text-green-400' },
  yellow:  { active: 'border-yellow-500 bg-yellow-500/15 text-yellow-400', line: 'bg-yellow-600', text: 'text-yellow-400' },
  emerald: { active: 'border-emerald-500 bg-emerald-500/15 text-emerald-400', line: 'bg-emerald-600', text: 'text-emerald-400' },
};

const SUBGENRE_MAP = {
  action: ['militare', 'spy', 'vendetta', 'arti marziali', 'heist', 'survival', 'guerra urbana', 'apocalittico', 'crime action', 'supereroi'],
  comedy: ['slapstick', 'romantica', 'nera', 'satirica', 'demenziale', 'teen', 'familiare', 'surreale', 'parodia', 'situazionale'],
  drama: ['romantico', 'psicologico', 'familiare', 'sociale', 'biografico', 'legale', 'medico', 'religioso', 'politico', 'tragico'],
  horror: ['slasher', 'psicologico', 'soprannaturale', 'body horror', 'folk horror', 'found footage', 'gotico', 'survival horror', 'cosmico', 'zombie'],
  sci_fi: ['cyberpunk', 'space opera', 'viaggi nel tempo', 'distopia', 'post-apocalittico', 'alieni', 'hard sci-fi', 'biopunk', 'mecha', 'utopia'],
  romance: ['period', 'tragico', 'commedia romantica', 'fantasy', 'teen romance', 'epistolare', 'drammatico', 'musicale', 'proibito', 'riconciliazione'],
  thriller: ['psicologico', 'investigativo', 'crime', 'paranoia', 'politico', 'survival', 'techno-thriller', 'mistero', 'serial killer', 'suspense'],
  animation: ['CGI', 'stop motion', '2D classico', 'anime', 'clay', 'rotoscope', 'mixed media', 'pixel art', 'puppetoon', 'silhouette'],
  documentary: ['natura', 'true crime', 'sociale', 'musicale', 'sportivo', 'storico', 'scientifico', 'biografico', 'politico', 'viaggio'],
  fantasy: ['epico', 'dark fantasy', 'urban fantasy', 'fiabesco', 'mitologico', 'sword & sorcery', 'low fantasy', 'portal fantasy', 'romantico', 'steampunk'],
  musical: ['broadway', 'biografico', 'dance', 'rock opera', 'jukebox', 'opera', 'hip hop', 'classico', 'bollywood', 'country'],
  western: ['classico', 'spaghetti', 'neo-western', 'revisionista', 'crepuscolare', 'acid western', 'space western', 'comedy western', 'outlaw', 'frontier'],
  biographical: ['icona musicale', 'politico', 'sportivo', 'criminale', 'scienziato', 'artista', 'esploratore', 'attivista', 'leader militare', 'inventore'],
  mystery: ['whodunit', 'noir', 'cozy', 'locked room', 'giallo', 'poliziesco', 'cospirazione', 'soprannaturale', 'storico', 'scientifico'],
  adventure: ['giungla', 'oceano', 'tesoro', 'survival', 'esplorazione', 'montagna', 'sotterraneo', 'artico', 'desertico', 'urbano'],
  war: ['WWII', 'vietnam', 'moderna', 'medievale', 'napoleonica', 'civile americana', 'prima guerra', 'guerra fredda', 'resistenza', 'mercenari'],
  crime: ['gangster', 'heist', 'detective', 'cartello', 'mafioso', 'corruzione', 'rapimento', 'frode', 'vendetta', 'undercover'],
  noir: ['classico', 'neo-noir', 'tech-noir', 'southern gothic', 'sunshine noir', 'artico', 'mediterraneo', 'tokyo noir', 'rural noir', 'tropical noir'],
  historical: ['guerra', 'imperi', 'medioevo', 'rinascimento', 'antico', 'biografico storico', 'politico storico', 'rivoluzioni', 'coloniale', 'mitologico'],
};

// ═══════════════════════════════════════════════════════════════
//  HELPERS
// ═══════════════════════════════════════════════════════════════

const _pendingRequests = new Set();

const api = {
  get: async (path) => {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API}/api/pipeline-v2${path}`, { headers: { 'Authorization': `Bearer ${token}` } });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || res.statusText); }
    return res.json();
  },
  post: async (path, body) => {
    // Anti double-click: block identical concurrent POST requests
    const key = `POST:${path}`;
    if (_pendingRequests.has(key)) {
      throw new Error('Operazione in corso, attendere...');
    }
    _pendingRequests.add(key);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/api/pipeline-v2${path}`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || res.statusText); }
      return res.json();
    } finally {
      _pendingRequests.delete(key);
    }
  }
};

function useCountdown(endTime) {
  const [remaining, setRemaining] = useState('');
  const [done, setDone] = useState(false);
  useEffect(() => {
    if (!endTime) { setRemaining(''); setDone(true); return; }
    const tick = () => {
      const end = new Date(endTime).getTime();
      const now = Date.now();
      const diff = end - now;
      if (diff <= 0) { setRemaining('Completato'); setDone(true); return; }
      setDone(false);
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setRemaining(`${h}h ${m}m ${s}s`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [endTime]);
  return { remaining, done };
}

// ═══════════════════════════════════════════════════════════════
//  STEPPER BAR (9 steps, horizontal scrollable on mobile)
// ═══════════════════════════════════════════════════════════════

const StepperBar = ({ uiStep }) => {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) {
      const active = ref.current.querySelector(`[data-step="${uiStep}"]`);
      if (active) active.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
  }, [uiStep]);

  return (
    <div ref={ref} className="flex items-center gap-0 px-1 py-2 overflow-x-auto scrollbar-hide" data-testid="v2-stepper">
      {V2_STEPS.map((step, i) => {
        const Icon = step.icon;
        const style = STEP_STYLES[step.color];
        const isCurrent = i === uiStep;
        const isCompleted = i < uiStep;
        return (
          <React.Fragment key={step.id}>
            {i > 0 && <div className={`w-3 sm:w-5 h-0.5 flex-shrink-0 ${isCompleted ? style.line : 'bg-gray-800'}`} />}
            <div className="flex flex-col items-center gap-0.5 flex-shrink-0" data-step={i}>
              <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                isCurrent ? `${style.active} shadow-lg shadow-${step.color}-500/20 scale-110` :
                isCompleted ? 'border-emerald-600 bg-emerald-500/10 text-emerald-400' :
                'border-gray-800 bg-gray-900/50 text-gray-700'
              }`}>
                {isCompleted ? <Check className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
              </div>
              <span className={`text-[6px] sm:text-[7px] font-bold tracking-wider uppercase whitespace-nowrap ${
                isCurrent ? style.text : isCompleted ? 'text-emerald-500/60' : 'text-gray-700'
              }`}>{step.label}</span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FILM HEADER (poster + title + genre + pre-imdb)
// ═══════════════════════════════════════════════════════════════

const FilmHeader = ({ film, onBack }) => (
  <div className="flex items-center gap-3 p-3 border-b border-gray-800/50">
    <button onClick={onBack} className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center hover:bg-gray-700 transition-colors" data-testid="back-btn">
      <ChevronLeft className="w-4 h-4 text-gray-400" />
    </button>
    {film.poster_url ? (
      <img src={film.poster_url} alt="" className="w-10 h-14 rounded object-cover border border-gray-700" />
    ) : (
      <div className="w-10 h-14 rounded bg-gray-800 border border-gray-700 flex items-center justify-center">
        <Film className="w-4 h-4 text-gray-600" />
      </div>
    )}
    <div className="flex-1 min-w-0">
      <h2 className="text-sm font-bold text-white truncate">{film.title || 'Nuovo Film'}</h2>
      <div className="flex items-center gap-2 mt-0.5">
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium uppercase">{film.genre || '—'}</span>
        {film.pre_imdb_score > 0 && (
          <span className="text-[9px] text-yellow-400 font-bold flex items-center gap-0.5">
            <Star className="w-2.5 h-2.5" /> {film.pre_imdb_score}
          </span>
        )}
      </div>
    </div>
  </div>
);

// ═══════════════════════════════════════════════════════════════
//  PHASE WRAPPER
// ═══════════════════════════════════════════════════════════════

const PhaseWrapper = ({ title, subtitle, icon: Icon, color, children }) => (
  <div className="p-3 space-y-3">
    <div className="flex items-center gap-2 mb-2">
      <div className={`w-8 h-8 rounded-lg bg-${color}-500/10 border border-${color}-500/20 flex items-center justify-center`}>
        <Icon className={`w-4 h-4 text-${color}-400`} />
      </div>
      <div>
        <h3 className="text-sm font-bold text-white">{title}</h3>
        <p className="text-[9px] text-gray-500">{subtitle}</p>
      </div>
    </div>
    {children}
  </div>
);

// ═══════════════════════════════════════════════════════════════
//  FASE 1 — IDEA
// ═══════════════════════════════════════════════════════════════

const IdeaPhase = ({ film, onRefresh, toast }) => {
  const [title, setTitle] = useState(film.title || '');
  const [genre, setGenre] = useState(film.genre || '');
  const [subgenre, setSubgenre] = useState(film.subgenre || '');
  const [preTrama, setPreTrama] = useState(film.pre_trama || '');
  const [locations, setLocations] = useState(film.locations || []);
  const [allLocations, setAllLocations] = useState([]);
  const [genres, setGenres] = useState([]);
  const [subgenres, setSubgenres] = useState({});
  const [loading, setLoading] = useState('');
  const [screenplayMode, setScreenplayMode] = useState('');
  const [screenplayPrompt, setScreenplayPrompt] = useState('');
  const [manualScreenplay, setManualScreenplay] = useState(film.screenplay || '');

  useEffect(() => {
    api.get('/locations').then(d => setAllLocations(d.locations || [])).catch(() => {});
    api.get('/genres').then(d => { setGenres(d.genres || []); setSubgenres(d.subgenres || {}); }).catch(() => {});
  }, []);

  const saveIdea = async (extra = {}) => {
    setLoading('save');
    try {
      const body = { title, genre, subgenre, subgenres: subgenre ? [subgenre] : [], pre_trama: preTrama, locations, ...extra };
      await api.post(`/films/${film.id}/save-idea`, body);
      onRefresh();
      toast({ title: 'Salvato' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const generatePoster = async (mode) => {
    setLoading('poster');
    try {
      await api.post(`/films/${film.id}/poster`, { mode, prompt: mode === 'ai_custom' ? screenplayPrompt : '' });
      onRefresh();
      toast({ title: 'Locandina generata!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const writeScreenplay = async () => {
    if (!screenplayMode) return;
    setLoading('screenplay');
    try {
      const body = { mode: screenplayMode, prompt: screenplayPrompt, text: manualScreenplay };
      const res = await api.post(`/films/${film.id}/screenplay`, body);
      onRefresh();
      toast({ title: `Sceneggiatura scritta! (+${res.quality_bonus} quality)` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const propose = async () => {
    setLoading('propose');
    try {
      await saveIdea();
      await api.post(`/films/${film.id}/propose`);
      onRefresh();
      toast({ title: 'Film proposto! Configura l\'Hype.' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const locsByCategory = allLocations.reduce((acc, l) => {
    const cat = l.category || 'altro';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(l);
    return acc;
  }, {});

  const hasPoster = film.pipeline_flags?.has_poster;
  const hasScreenplay = film.pipeline_flags?.has_screenplay;
  const canPropose = title.length > 2 && genre && preTrama.length >= 50;

  return (
    <PhaseWrapper title="L'Idea" subtitle="Dai forma al tuo film" icon={Sparkles} color="amber">
      {/* 1. Titolo e Genere */}
      <div className="space-y-2">
        <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold">Titolo</label>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Il titolo del tuo film..."
          className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:border-amber-500/50 focus:outline-none" data-testid="idea-title" />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold">Genere</label>
          <select value={genre} onChange={e => { setGenre(e.target.value); setSubgenre(''); }}
            className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-2 py-2 text-xs text-white focus:border-amber-500/50 focus:outline-none" data-testid="idea-genre">
            <option value="">Scegli...</option>
            {genres.map(g => <option key={g} value={g}>{g.replace('_', ' ')}</option>)}
          </select>
        </div>
        <div>
          <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold">Sottogenere</label>
          <select value={subgenre} onChange={e => setSubgenre(e.target.value)}
            className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-2 py-2 text-xs text-white focus:border-amber-500/50 focus:outline-none" data-testid="idea-subgenre">
            <option value="">Opzionale</option>
            {(subgenres[genre] || []).map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* 2. Pre-Trama */}
      <div>
        <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold">Pre-Trama <span className="text-gray-600">(min 50 caratteri)</span></label>
        <textarea value={preTrama} onChange={e => setPreTrama(e.target.value)} rows={3} placeholder="Racconta la trama del tuo film..."
          className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder:text-gray-600 focus:border-amber-500/50 focus:outline-none resize-none" data-testid="idea-pretrama" />
        <p className={`text-[8px] ${preTrama.length >= 50 ? 'text-emerald-500' : 'text-gray-600'}`}>{preTrama.length}/50+</p>
      </div>

      {/* 3. Location */}
      <div>
        <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold flex items-center gap-1"><MapPin className="w-3 h-3" /> Location ({locations.length}/3)</label>
        <div className="mt-1 space-y-2 max-h-40 overflow-y-auto">
          {Object.entries(locsByCategory).map(([cat, locs]) => (
            <div key={cat}>
              <p className="text-[8px] text-gray-500 uppercase font-bold mb-1">{cat}</p>
              <div className="flex flex-wrap gap-1">
                {locs.map(l => {
                  const sel = locations.some(lo => (typeof lo === 'string' ? lo : lo.name) === l.name);
                  return (
                    <button key={l.name} onClick={() => {
                      if (sel) setLocations(locations.filter(lo => (typeof lo === 'string' ? lo : lo.name) !== l.name));
                      else if (locations.length < 3) setLocations([...locations, l]);
                    }}
                    className={`text-[8px] px-1.5 py-0.5 rounded border transition-colors ${sel ? 'bg-amber-500/15 border-amber-500/40 text-amber-400' : 'bg-gray-800/50 border-gray-700 text-gray-500 hover:border-gray-600'}`}>
                      {l.name}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pre-IMDb */}
      {film.pre_imdb_score > 0 && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-yellow-500/5 border border-yellow-500/15">
          <Star className="w-4 h-4 text-yellow-400" />
          <div>
            <p className="text-[9px] text-gray-500 uppercase">Pre-IMDb Score</p>
            <p className="text-sm font-bold text-yellow-400">{film.pre_imdb_score}</p>
          </div>
        </div>
      )}

      {/* 4. Locandina */}
      <div className="p-3 rounded-lg bg-gray-800/30 border border-gray-700/50 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[9px] text-gray-400 uppercase font-bold flex items-center gap-1"><Palette className="w-3 h-3" /> Locandina</span>
          {hasPoster && <Badge className="bg-emerald-500/15 text-emerald-400 text-[7px] border-emerald-500/20">Creata</Badge>}
        </div>
        {film.poster_url && <img src={film.poster_url} alt="" className="w-full max-w-[160px] mx-auto rounded-lg border border-gray-700" />}
        {!hasPoster && (
          <div className="flex gap-1.5">
            <button onClick={() => generatePoster('ai_auto')} disabled={loading === 'poster'}
              className="flex-1 text-[9px] py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 transition-colors disabled:opacity-50" data-testid="poster-ai-auto">
              {loading === 'poster' ? '...' : 'AI Auto'}
            </button>
            <button onClick={() => generatePoster('ai_custom')} disabled={loading === 'poster'}
              className="flex-1 text-[9px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 hover:bg-purple-500/20 transition-colors disabled:opacity-50" data-testid="poster-ai-custom">
              AI Custom
            </button>
            <button onClick={() => generatePoster('classic')} disabled={loading === 'poster'}
              className="flex-1 text-[9px] py-2 rounded-lg bg-gray-700/50 border border-gray-600 text-gray-400 hover:bg-gray-700 transition-colors disabled:opacity-50" data-testid="poster-classic">
              Classic
            </button>
          </div>
        )}
        {!hasPoster && <p className="text-[8px] text-gray-600 italic text-center">Opzionale ma consigliata (+hype)</p>}
      </div>

      {/* 5. Sceneggiatura */}
      <div className="p-3 rounded-lg bg-gray-800/30 border border-gray-700/50 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[9px] text-gray-400 uppercase font-bold flex items-center gap-1"><FileText className="w-3 h-3" /> Sceneggiatura</span>
          {hasScreenplay && <Badge className="bg-emerald-500/15 text-emerald-400 text-[7px] border-emerald-500/20">Scritta ({film.screenplay_mode})</Badge>}
        </div>
        {hasScreenplay && film.screenplay && (
          <p className="text-[9px] text-gray-400 max-h-20 overflow-y-auto leading-relaxed">{film.screenplay.slice(0, 300)}{film.screenplay.length > 300 ? '...' : ''}</p>
        )}
        {!hasScreenplay && (
          <>
            <div className="flex gap-1.5">
              {['ai_auto', 'ai_custom', 'manual'].map(m => (
                <button key={m} onClick={() => setScreenplayMode(m)}
                  className={`flex-1 text-[9px] py-1.5 rounded-lg border transition-colors ${screenplayMode === m ? 'bg-purple-500/15 border-purple-500/40 text-purple-400' : 'bg-gray-800/50 border-gray-700 text-gray-500'}`}>
                  {m === 'ai_auto' ? 'AI Auto' : m === 'ai_custom' ? 'AI Custom' : 'Manuale'}
                </button>
              ))}
            </div>
            {screenplayMode === 'ai_custom' && (
              <input value={screenplayPrompt} onChange={e => setScreenplayPrompt(e.target.value)} placeholder="Indica il tono, lo stile..."
                className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-gray-600 focus:outline-none" />
            )}
            {screenplayMode === 'manual' && (
              <textarea value={manualScreenplay} onChange={e => setManualScreenplay(e.target.value)} rows={4} placeholder="Scrivi la tua sceneggiatura..."
                className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder:text-gray-600 focus:outline-none resize-none" />
            )}
            {screenplayMode && (
              <button onClick={writeScreenplay} disabled={loading === 'screenplay'}
                className="w-full text-[10px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20 transition-colors disabled:opacity-50 font-bold" data-testid="write-screenplay-btn">
                {loading === 'screenplay' ? 'Scrittura in corso...' : 'Scrivi Sceneggiatura'}
              </button>
            )}
          </>
        )}
      </div>

      {/* Save + Propose */}
      <div className="flex gap-2 pt-2">
        <button onClick={() => saveIdea()} disabled={loading === 'save'}
          className="flex-1 text-[10px] py-2.5 rounded-lg bg-gray-700/50 border border-gray-600 text-gray-300 hover:bg-gray-700 transition-colors disabled:opacity-50 font-bold" data-testid="save-idea-btn">
          Salva Bozza
        </button>
        <button onClick={propose} disabled={!canPropose || loading === 'propose'}
          className="flex-1 text-[10px] py-2.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 hover:bg-amber-500/25 transition-colors disabled:opacity-30 font-bold" data-testid="propose-film-btn">
          {loading === 'propose' ? '...' : 'Proponi Film'}
        </button>
      </div>
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 2 — HYPE
// ═══════════════════════════════════════════════════════════════

const HypePhase = ({ film, onRefresh, toast }) => {
  const [duration, setDuration] = useState(8);
  const [strategy, setStrategy] = useState('bilanciata');
  const [loading, setLoading] = useState('');
  const state = film.pipeline_state;
  const timers = film.pipeline_timers || {};
  const { remaining, done } = useCountdown(timers.hype_end);

  const strategies = [
    { id: 'sprint', name: 'Sprint', desc: 'Rapido accesso alle proposte, meno hype totale', icon: Zap },
    { id: 'bilanciata', name: 'Bilanciata', desc: 'Equilibrio tra hype e velocita', icon: TrendingUp },
    { id: 'costruzione_lenta', name: 'Costruzione Lenta', desc: 'Piu hype e interesse agenzie, piu tempo', icon: Timer },
  ];

  const setupHype = async () => {
    setLoading('setup');
    try {
      await api.post(`/films/${film.id}/setup-hype`, { duration_hours: duration, strategy });
      onRefresh();
      toast({ title: 'Hype configurato!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const launchHype = async () => {
    setLoading('launch');
    try {
      const res = await api.post(`/films/${film.id}/launch-hype`);
      onRefresh();
      toast({ title: `Hype lanciato! ${res.initial_proposals} proposte in arrivo` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const speedup = async () => {
    setLoading('speedup');
    try {
      await api.post(`/films/${film.id}/speedup-hype`);
      onRefresh();
      toast({ title: 'Hype accelerato!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const completeHype = async () => {
    setLoading('complete');
    try {
      const res = await api.post(`/films/${film.id}/complete-hype`);
      onRefresh();
      toast({ title: `Casting aperto! ${res.total_proposals} proposte totali` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  return (
    <PhaseWrapper title="Hype Machine" subtitle="Crea aspettativa strategica" icon={TrendingUp} color="orange">
      {/* SETUP */}
      {state === 'proposed' && (
        <div className="space-y-3">
          <div>
            <label className="text-[9px] text-gray-500 uppercase font-bold">Durata Hype: {duration}h</label>
            <input type="range" min={2} max={24} value={duration} onChange={e => setDuration(+e.target.value)}
              className="w-full accent-orange-500 mt-1" data-testid="hype-duration" />
            <div className="flex justify-between text-[7px] text-gray-600"><span>2h</span><span>12h</span><span>24h</span></div>
          </div>
          <div className="space-y-1.5">
            <label className="text-[9px] text-gray-500 uppercase font-bold">Strategia</label>
            {strategies.map(s => (
              <button key={s.id} onClick={() => setStrategy(s.id)}
                className={`w-full flex items-center gap-2 p-2.5 rounded-lg border text-left transition-colors ${strategy === s.id ? 'bg-orange-500/10 border-orange-500/40' : 'bg-gray-800/30 border-gray-700 hover:border-gray-600'}`} data-testid={`strategy-${s.id}`}>
                <s.icon className={`w-4 h-4 flex-shrink-0 ${strategy === s.id ? 'text-orange-400' : 'text-gray-600'}`} />
                <div>
                  <p className={`text-[10px] font-bold ${strategy === s.id ? 'text-orange-400' : 'text-gray-300'}`}>{s.name}</p>
                  <p className="text-[8px] text-gray-500">{s.desc}</p>
                </div>
              </button>
            ))}
          </div>
          <button onClick={setupHype} disabled={loading === 'setup'}
            className="w-full text-[10px] py-2.5 rounded-lg bg-orange-500/15 border border-orange-500/30 text-orange-400 hover:bg-orange-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="setup-hype-btn">
            {loading === 'setup' ? '...' : 'Configura Hype'}
          </button>
        </div>
      )}

      {/* READY TO LAUNCH */}
      {state === 'hype_setup' && (
        <div className="space-y-3 text-center">
          <div className="p-3 rounded-lg bg-orange-500/5 border border-orange-500/20">
            <p className="text-[10px] text-orange-400 font-bold">Strategia: {film.hype_strategy}</p>
            <p className="text-[9px] text-gray-400 mt-1">{film.hype_duration_hours}h di hype • {film.pipeline_metrics?.target_agencies || '?'} agenzie target</p>
          </div>
          <button onClick={launchHype} disabled={loading === 'launch'}
            className="w-full text-[11px] py-3 rounded-lg bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-500/30 text-orange-300 hover:from-orange-500/30 hover:to-red-500/30 transition-all disabled:opacity-50 font-bold" data-testid="launch-hype-btn">
            {loading === 'launch' ? '...' : 'LANCIA HYPE'}
          </button>
        </div>
      )}

      {/* LIVE */}
      {state === 'hype_live' && (
        <div className="space-y-3">
          <div className="p-3 rounded-lg bg-orange-500/5 border border-orange-500/20 text-center">
            <p className="text-[9px] text-gray-500 uppercase">Hype in corso</p>
            <p className="text-lg font-bold text-orange-400 font-mono">{remaining}</p>
            <p className="text-[9px] text-gray-500 mt-1">Hype: {film.pipeline_metrics?.hype_score || 0} • Agenzie: {(film.interested_agencies || []).length}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={speedup} disabled={loading === 'speedup'}
              className="flex-1 text-[9px] py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 hover:bg-yellow-500/20 transition-colors disabled:opacity-50 font-bold" data-testid="speedup-hype-btn">
              Accelera ($30K)
            </button>
            {done && (
              <button onClick={completeHype} disabled={loading === 'complete'}
                className="flex-1 text-[10px] py-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="complete-hype-btn">
                {loading === 'complete' ? '...' : 'Vai al Cast'}
              </button>
            )}
          </div>
        </div>
      )}
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 3 — CAST
// ═══════════════════════════════════════════════════════════════

const CastPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState('');
  const cast = film.cast || {};
  const proposals = film.cast_proposals || [];
  const hasDirector = !!cast.director;
  const hasActors = (cast.actors || []).length >= 2;
  const canLock = hasDirector && hasActors;

  const selectCast = async (index, role) => {
    setLoading(`select_${index}`);
    try {
      const res = await api.post(`/films/${film.id}/select-cast`, { proposal_index: index, role });
      onRefresh();
      toast({ title: `${res.selected} aggiunto come ${role}!` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const lockCast = async () => {
    setLoading('lock');
    try {
      await api.post(`/films/${film.id}/lock-cast`);
      onRefresh();
      toast({ title: 'Cast bloccato! Avanti con la PREP.' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const CastSlot = ({ label, person, icon: Icon }) => (
    <div className="p-2 rounded-lg bg-gray-800/30 border border-gray-700/50">
      <p className="text-[8px] text-gray-500 uppercase font-bold flex items-center gap-1"><Icon className="w-2.5 h-2.5" /> {label}</p>
      {person ? (
        <div className="flex items-center gap-2 mt-1">
          <div className="w-6 h-6 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-[8px] font-bold text-cyan-400">{(person.name || '?')[0]}</div>
          <div>
            <p className="text-[10px] font-medium text-white">{person.name}</p>
            <p className="text-[8px] text-gray-500">Skill {person.skill || '?'} {person.agency_name ? `• ${person.agency_name}` : ''}</p>
          </div>
        </div>
      ) : <p className="text-[9px] text-gray-600 italic mt-1">Nessuno selezionato</p>}
    </div>
  );

  return (
    <PhaseWrapper title="Il Cast" subtitle="Assembla la squadra perfetta" icon={Users} color="cyan">
      {/* Current Cast */}
      <div className="grid grid-cols-2 gap-2">
        <CastSlot label="Regista" person={cast.director} icon={Camera} />
        <CastSlot label="Sceneggiatore" person={cast.screenwriter} icon={FileText} />
      </div>
      <div className="grid grid-cols-2 gap-2">
        {[0, 1].map(i => (
          <CastSlot key={i} label={`Attore ${i+1}`} person={(cast.actors || [])[i]} icon={Star} />
        ))}
      </div>
      <CastSlot label="Compositore" person={cast.composer} icon={Music} />

      {/* Quality */}
      <div className="flex items-center gap-2 p-2 rounded-lg bg-cyan-500/5 border border-cyan-500/15">
        <span className="text-[9px] text-gray-500">Qualita Cast:</span>
        <span className="text-[10px] font-bold text-cyan-400">{film.pipeline_metrics?.cast_quality || 0}%</span>
      </div>

      {/* Proposals */}
      <div>
        <p className="text-[9px] text-gray-500 uppercase font-bold mb-1">Proposte ({proposals.length})</p>
        <div className="space-y-1.5 max-h-60 overflow-y-auto">
          {proposals.map((p, i) => (
            <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-gray-800/30 border border-gray-700/50">
              <div className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center text-[9px] font-bold text-gray-300">{(p.name || '?')[0]}</div>
              <div className="flex-1 min-w-0">
                <p className="text-[10px] font-medium text-white truncate">{p.name}</p>
                <p className="text-[8px] text-gray-500">Skill {p.skill || '?'} • {p.agency_name || '?'}</p>
              </div>
              <div className="flex gap-1">
                {['director', 'actor', 'screenwriter', 'composer'].map(role => (
                  <button key={role} onClick={() => selectCast(i, role)} disabled={loading.startsWith('select')}
                    className="text-[7px] px-1.5 py-1 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20 transition-colors">
                    {role === 'director' ? 'REG' : role === 'actor' ? 'ATT' : role === 'screenwriter' ? 'SCR' : 'MUS'}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {proposals.length === 0 && <p className="text-[9px] text-gray-600 italic text-center py-4">Nessuna proposta disponibile</p>}
        </div>
      </div>

      {/* Lock */}
      <button onClick={lockCast} disabled={!canLock || loading === 'lock'}
        className="w-full text-[10px] py-2.5 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/25 transition-colors disabled:opacity-30 font-bold" data-testid="lock-cast-btn">
        {loading === 'lock' ? '...' : `Blocca Cast e Procedi`}
      </button>
      {!canLock && <p className="text-[8px] text-gray-600 text-center">Serve: 1 regista + 2 attori minimo</p>}
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 4 — PREP
// ═══════════════════════════════════════════════════════════════

const PrepPhase = ({ film, onRefresh, toast }) => {
  const [options, setOptions] = useState(null);
  const [equipment, setEquipment] = useState(film.equipment || []);
  const [cgi, setCgi] = useState(film.production_setup?.cgi_packages || []);
  const [vfx, setVfx] = useState(film.production_setup?.vfx_packages || []);
  const [extras, setExtras] = useState(film.production_setup?.extras_count || 100);
  const [loading, setLoading] = useState('');

  useEffect(() => {
    api.get(`/films/${film.id}/prep-options`).then(setOptions).catch(() => {});
  }, [film.id]);

  const saveAndProceed = async () => {
    setLoading('save');
    try {
      await api.post(`/films/${film.id}/save-prep`, { equipment, cgi_packages: cgi, vfx_packages: vfx, extras_count: extras });
      await api.post(`/films/${film.id}/start-ciak`);
      onRefresh();
      toast({ title: 'CIAK! Riprese avviate!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const toggleItem = (item, list, setList, max = 10) => {
    const exists = list.some(l => l.name === item.name);
    if (exists) setList(list.filter(l => l.name !== item.name));
    else if (list.length < max) setList([...list, item]);
  };

  if (!options) return <div className="p-4 text-center text-gray-600 text-xs">Caricamento opzioni...</div>;

  return (
    <PhaseWrapper title="Pre-Produzione" subtitle="Attrezzature, effetti e comparse" icon={Camera} color="blue">
      {/* Equipment */}
      <div>
        <p className="text-[9px] text-gray-500 uppercase font-bold mb-1">Attrezzature ({equipment.length}/10)</p>
        <div className="flex flex-wrap gap-1">
          {(options.equipment || []).map((eq, i) => {
            const sel = equipment.some(e => e.name === eq.name);
            return (
              <button key={i} onClick={() => toggleItem(eq, equipment, setEquipment)}
                className={`text-[8px] px-2 py-1 rounded border transition-colors ${sel ? 'bg-blue-500/15 border-blue-500/40 text-blue-400' : 'bg-gray-800/50 border-gray-700 text-gray-500'}`}>
                {eq.name} {eq.cost ? `$${(eq.cost/1000).toFixed(0)}K` : ''}
              </button>
            );
          })}
        </div>
      </div>

      {/* CGI */}
      <div>
        <p className="text-[9px] text-gray-500 uppercase font-bold mb-1">CGI ({cgi.length}/10)</p>
        <div className="flex flex-wrap gap-1">
          {(options.cgi_packages || []).map((c, i) => {
            const sel = cgi.some(x => x.name === c.name);
            return (
              <button key={i} onClick={() => toggleItem(c, cgi, setCgi)}
                className={`text-[8px] px-2 py-1 rounded border transition-colors ${sel ? 'bg-indigo-500/15 border-indigo-500/40 text-indigo-400' : 'bg-gray-800/50 border-gray-700 text-gray-500'}`}>
                {c.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* VFX */}
      <div>
        <p className="text-[9px] text-gray-500 uppercase font-bold mb-1">VFX ({vfx.length}/10)</p>
        <div className="flex flex-wrap gap-1">
          {(options.vfx_packages || []).map((v, i) => {
            const sel = vfx.some(x => x.name === v.name);
            return (
              <button key={i} onClick={() => toggleItem(v, vfx, setVfx)}
                className={`text-[8px] px-2 py-1 rounded border transition-colors ${sel ? 'bg-purple-500/15 border-purple-500/40 text-purple-400' : 'bg-gray-800/50 border-gray-700 text-gray-500'}`}>
                {v.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Extras Slider */}
      <div>
        <p className="text-[9px] text-gray-500 uppercase font-bold">Comparse: {extras}</p>
        <input type="range" min={0} max={1000} step={10} value={extras} onChange={e => setExtras(+e.target.value)}
          className="w-full accent-blue-500 mt-1" data-testid="extras-slider" />
        <div className="flex justify-between text-[7px] text-gray-600"><span>0</span><span>500</span><span>1000</span></div>
        <p className="text-[8px] text-gray-500">Costo: ${(extras * (options.extras_cost_per_person || 500)).toLocaleString()}</p>
      </div>

      <button onClick={saveAndProceed} disabled={loading === 'save'}
        className="w-full text-[10px] py-2.5 rounded-lg bg-blue-500/15 border border-blue-500/30 text-blue-400 hover:bg-blue-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="start-ciak-btn">
        {loading === 'save' ? '...' : 'Salva e Avvia Riprese'}
      </button>
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 5 — CIAK (Riprese)
// ═══════════════════════════════════════════════════════════════

const CiakPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState('');
  const timers = film.pipeline_timers || {};
  const { remaining, done } = useCountdown(timers.shooting_end);

  const speedup = async () => {
    setLoading('speedup');
    try {
      await api.post(`/films/${film.id}/speedup-ciak`);
      onRefresh();
      toast({ title: 'Riprese accelerate!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const completeCiak = async () => {
    setLoading('complete');
    try {
      const res = await api.post(`/films/${film.id}/complete-ciak`);
      onRefresh();
      const events = res.events || [];
      toast({ title: `Riprese completate! ${events.length} eventi sul set.` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  return (
    <PhaseWrapper title="CIAK! Riprese" subtitle={`${film.shooting_days || '?'} giorni di riprese`} icon={Clapperboard} color="red">
      <div className="p-4 rounded-lg bg-red-500/5 border border-red-500/20 text-center space-y-2">
        <Clapperboard className="w-8 h-8 text-red-400 mx-auto" />
        <p className="text-[9px] text-gray-500 uppercase">Riprese in corso</p>
        <p className="text-xl font-bold text-red-400 font-mono">{remaining}</p>
      </div>

      {(film.shooting_events || []).length > 0 && (
        <div className="space-y-1">
          <p className="text-[9px] text-gray-500 uppercase font-bold">Eventi sul set</p>
          {film.shooting_events.map((ev, i) => (
            <div key={i} className={`p-2 rounded-lg text-[9px] ${ev.type === 'positive' ? 'bg-green-500/5 text-green-400 border border-green-500/20' : ev.type === 'negative' ? 'bg-red-500/5 text-red-400 border border-red-500/20' : 'bg-yellow-500/5 text-yellow-400 border border-yellow-500/20'}`}>
              {ev.text} ({ev.quality_impact > 0 ? '+' : ''}{ev.quality_impact})
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button onClick={speedup} disabled={loading === 'speedup' || done}
          className="flex-1 text-[9px] py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 hover:bg-yellow-500/20 transition-colors disabled:opacity-50 font-bold" data-testid="speedup-ciak-btn">
          Accelera ($50K)
        </button>
        {done && (
          <button onClick={completeCiak} disabled={loading === 'complete'}
            className="flex-1 text-[10px] py-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="complete-ciak-btn">
            {loading === 'complete' ? '...' : 'Completa Riprese'}
          </button>
        )}
      </div>
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 6 — FINAL CUT
// ═══════════════════════════════════════════════════════════════

const FinalCutPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState('');
  const timers = film.pipeline_timers || {};
  const { remaining, done } = useCountdown(timers.postprod_end);

  const speedup = async () => {
    setLoading('speedup');
    try {
      await api.post(`/films/${film.id}/speedup-finalcut`);
      onRefresh();
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const complete = async () => {
    setLoading('complete');
    try {
      await api.post(`/films/${film.id}/complete-finalcut`);
      onRefresh();
      toast({ title: 'Final Cut completato! Sponsor e marketing.' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  return (
    <PhaseWrapper title="Final Cut" subtitle="Post-produzione e montaggio" icon={Film} color="purple">
      <div className="p-4 rounded-lg bg-purple-500/5 border border-purple-500/20 text-center space-y-2">
        <Film className="w-8 h-8 text-purple-400 mx-auto" />
        <p className="text-[9px] text-gray-500 uppercase">Montaggio in corso</p>
        <p className="text-xl font-bold text-purple-400 font-mono">{remaining}</p>
      </div>
      <div className="flex gap-2">
        <button onClick={speedup} disabled={loading === 'speedup' || done}
          className="flex-1 text-[9px] py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 hover:bg-yellow-500/20 transition-colors disabled:opacity-50 font-bold" data-testid="speedup-finalcut-btn">
          Accelera ($40K)
        </button>
        {done && (
          <button onClick={complete} disabled={loading === 'complete'}
            className="flex-1 text-[10px] py-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="complete-finalcut-btn">
            {loading === 'complete' ? '...' : 'Completa Final Cut'}
          </button>
        )}
      </div>
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 7 — MARKETING (Sponsor + Marketing)
// ═══════════════════════════════════════════════════════════════

const MarketingPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState('');
  const [sponsors, setSponsors] = useState([]);
  const [selectedSponsors, setSelectedSponsors] = useState([]);
  const [marketingPkgs, setMarketingPkgs] = useState([]);
  const [selectedMarketing, setSelectedMarketing] = useState([]);
  const state = film.pipeline_state;

  useEffect(() => {
    if (state === 'sponsorship') {
      api.get(`/films/${film.id}/sponsor-offers`).then(d => setSponsors(d.sponsors || [])).catch(() => {});
    }
    if (state === 'marketing') {
      api.get(`/films/${film.id}/marketing-options`).then(d => setMarketingPkgs(d.packages || [])).catch(() => {});
    }
  }, [film.id, state]);

  const saveSponsors = async () => {
    setLoading('sponsors');
    try {
      const res = await api.post(`/films/${film.id}/save-sponsors`, { sponsors: selectedSponsors });
      onRefresh();
      toast({ title: `Sponsor selezionati! +$${(res.income || 0).toLocaleString()}` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const saveMarketing = async () => {
    setLoading('marketing');
    try {
      await api.post(`/films/${film.id}/save-marketing`, { packages: selectedMarketing });
      onRefresh();
      toast({ title: 'Marketing configurato!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const choosePremiere = async () => {
    setLoading('premiere');
    try {
      await api.post(`/films/${film.id}/choose-premiere`);
      onRefresh();
      toast({ title: 'La Prima!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const chooseDirectRelease = async () => {
    setLoading('direct');
    try {
      await api.post(`/films/${film.id}/choose-direct-release`);
      onRefresh();
      toast({ title: 'Rilascio diretto nei cinema!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const toggleSponsor = (sp) => {
    const exists = selectedSponsors.some(s => s.name === sp.name);
    if (exists) setSelectedSponsors(selectedSponsors.filter(s => s.name !== sp.name));
    else if (selectedSponsors.length < 6) setSelectedSponsors([...selectedSponsors, sp]);
  };

  const toggleMarketing = (pkg) => {
    const exists = selectedMarketing.some(m => m.id === pkg.id);
    if (exists) setSelectedMarketing(selectedMarketing.filter(m => m.id !== pkg.id));
    else setSelectedMarketing([...selectedMarketing, pkg]);
  };

  return (
    <PhaseWrapper title="Sponsor & Marketing" subtitle="Finanzia e promuovi" icon={Megaphone} color="green">
      {/* SPONSORS */}
      {state === 'sponsorship' && (
        <div className="space-y-2">
          <p className="text-[9px] text-gray-500 uppercase font-bold">Sponsor disponibili ({selectedSponsors.length}/6)</p>
          {sponsors.map((sp, i) => {
            const sel = selectedSponsors.some(s => s.name === sp.name);
            return (
              <button key={i} onClick={() => toggleSponsor(sp)}
                className={`w-full flex items-center gap-2 p-2.5 rounded-lg border text-left transition-colors ${sel ? 'bg-green-500/10 border-green-500/40' : 'bg-gray-800/30 border-gray-700'}`}>
                <div className="w-3 h-3 rounded-full" style={{ background: sp.logo_color || '#666' }} />
                <div className="flex-1">
                  <p className={`text-[10px] font-bold ${sel ? 'text-green-400' : 'text-gray-300'}`}>{sp.name}</p>
                  <p className="text-[8px] text-gray-500">${(sp.offer_amount || 0).toLocaleString()} • {((sp.rev_share || 0)*100).toFixed(0)}% rev share</p>
                </div>
              </button>
            );
          })}
          <button onClick={saveSponsors} disabled={loading === 'sponsors'}
            className="w-full text-[10px] py-2.5 rounded-lg bg-green-500/15 border border-green-500/30 text-green-400 hover:bg-green-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="save-sponsors-btn">
            {loading === 'sponsors' ? '...' : selectedSponsors.length > 0 ? `Conferma ${selectedSponsors.length} Sponsor` : 'Salta Sponsor'}
          </button>
        </div>
      )}

      {/* MARKETING */}
      {state === 'marketing' && (
        <div className="space-y-3">
          <p className="text-[9px] text-gray-500 uppercase font-bold">Pacchetti Marketing</p>
          {marketingPkgs.map((pkg, i) => {
            const sel = selectedMarketing.some(m => m.id === pkg.id);
            return (
              <button key={i} onClick={() => toggleMarketing(pkg)}
                className={`w-full flex items-center gap-2 p-2.5 rounded-lg border text-left transition-colors ${sel ? 'bg-green-500/10 border-green-500/40' : 'bg-gray-800/30 border-gray-700'}`}>
                <Megaphone className={`w-4 h-4 flex-shrink-0 ${sel ? 'text-green-400' : 'text-gray-600'}`} />
                <div className="flex-1">
                  <p className={`text-[10px] font-bold ${sel ? 'text-green-400' : 'text-gray-300'}`}>{pkg.name}</p>
                  <p className="text-[8px] text-gray-500">${(pkg.cost || 0).toLocaleString()} • +{pkg.hype_boost} hype</p>
                </div>
              </button>
            );
          })}

          {selectedMarketing.length > 0 && (
            <button onClick={saveMarketing} disabled={loading === 'marketing'}
              className="w-full text-[10px] py-2 rounded-lg bg-green-500/15 border border-green-500/30 text-green-400 hover:bg-green-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="save-marketing-btn">
              Attiva Marketing (${selectedMarketing.reduce((a, m) => a + (m.cost || 0), 0).toLocaleString()})
            </button>
          )}

          <div className="border-t border-gray-800 pt-3 space-y-2">
            <p className="text-[9px] text-gray-500 uppercase font-bold text-center">Come vuoi rilasciare il film?</p>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={choosePremiere} disabled={!!loading}
                className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-center hover:bg-yellow-500/15 transition-colors disabled:opacity-50" data-testid="choose-premiere-btn">
                <Award className="w-5 h-5 text-yellow-400 mx-auto mb-1" />
                <p className="text-[10px] font-bold text-yellow-400">La Prima</p>
                <p className="text-[7px] text-gray-500">Red carpet + premiere</p>
              </button>
              <button onClick={chooseDirectRelease} disabled={!!loading}
                className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center hover:bg-emerald-500/15 transition-colors disabled:opacity-50" data-testid="choose-direct-btn">
                <Ticket className="w-5 h-5 text-emerald-400 mx-auto mb-1" />
                <p className="text-[10px] font-bold text-emerald-400">Rilascio Diretto</p>
                <p className="text-[7px] text-gray-500">Subito nei cinema</p>
              </button>
            </div>
          </div>
        </div>
      )}
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 8 — LA PRIMA
// ═══════════════════════════════════════════════════════════════

const LaPrimaPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState('');
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState('');
  const [duration, setDuration] = useState(24);
  const state = film.pipeline_state;
  const timers = film.pipeline_timers || {};
  const { remaining, done } = useCountdown(timers.premiere_end);

  useEffect(() => {
    if (state === 'premiere_setup') {
      api.get(`/films/${film.id}/premiere-cities`).then(d => setCities(d.cities || [])).catch(() => {});
    }
  }, [film.id, state]);

  const setupPremiere = async () => {
    if (!selectedCity) return;
    setLoading('setup');
    try {
      await api.post(`/films/${film.id}/setup-premiere`, { city: selectedCity, duration_hours: duration });
      onRefresh();
      toast({ title: `Premiere a ${selectedCity}!` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const completePremiere = async () => {
    setLoading('complete');
    try {
      const res = await api.post(`/films/${film.id}/complete-premiere`);
      onRefresh();
      toast({ title: `Premiere completata! Impact: ${res.premiere_impact}` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const speedup = async () => {
    setLoading('speedup');
    try {
      await api.post(`/films/${film.id}/speedup-premiere`);
      onRefresh();
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  return (
    <PhaseWrapper title="La Prima" subtitle="L'anteprima esclusiva" icon={Award} color="yellow">
      {state === 'premiere_setup' && (
        <div className="space-y-3">
          <div>
            <p className="text-[9px] text-gray-500 uppercase font-bold mb-1">Scegli la citta</p>
            <div className="grid grid-cols-2 gap-1.5 max-h-48 overflow-y-auto">
              {cities.map(c => (
                <button key={c.name} onClick={() => setSelectedCity(c.name)}
                  className={`p-2 rounded-lg border text-left transition-colors ${selectedCity === c.name ? 'bg-yellow-500/10 border-yellow-500/40' : 'bg-gray-800/30 border-gray-700'}`}>
                  <p className={`text-[9px] font-bold ${selectedCity === c.name ? 'text-yellow-400' : 'text-gray-300'}`}>{c.name}</p>
                  <p className="text-[7px] text-gray-500">{c.region} • Prestigio: {c.prestige}</p>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-[9px] text-gray-500 uppercase font-bold">Durata: {duration}h</label>
            <input type="range" min={2} max={48} value={duration} onChange={e => setDuration(+e.target.value)}
              className="w-full accent-yellow-500 mt-1" />
          </div>
          <button onClick={setupPremiere} disabled={!selectedCity || loading === 'setup'}
            className="w-full text-[10px] py-2.5 rounded-lg bg-yellow-500/15 border border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/25 transition-colors disabled:opacity-30 font-bold" data-testid="setup-premiere-btn">
            {loading === 'setup' ? '...' : 'Avvia La Prima'}
          </button>
        </div>
      )}

      {state === 'premiere_live' && (
        <div className="space-y-3">
          <div className="p-4 rounded-lg bg-yellow-500/5 border border-yellow-500/20 text-center space-y-2">
            <Award className="w-8 h-8 text-yellow-400 mx-auto" />
            <p className="text-[9px] text-gray-500 uppercase">Premiere a {film.premiere?.city}</p>
            <p className="text-xl font-bold text-yellow-400 font-mono">{remaining}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={speedup} disabled={loading === 'speedup' || done}
              className="flex-1 text-[9px] py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 hover:bg-yellow-500/20 transition-colors disabled:opacity-50 font-bold">
              Accelera ($60K)
            </button>
            {done && (
              <button onClick={completePremiere} disabled={loading === 'complete'}
                className="flex-1 text-[10px] py-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="complete-premiere-btn">
                {loading === 'complete' ? '...' : 'Completa Premiere'}
              </button>
            )}
          </div>
        </div>
      )}
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 9 — USCITA
// ═══════════════════════════════════════════════════════════════

const UscitaPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState('');
  const [result, setResult] = useState(null);
  const state = film.pipeline_state;

  const release = async () => {
    setLoading('release');
    try {
      const res = await api.post(`/films/${film.id}/release`);
      setResult(res);
      onRefresh();
      toast({ title: `${film.title} rilasciato! Quality: ${res.quality_score}` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const tierColors = { masterpiece: 'text-yellow-400', excellent: 'text-emerald-400', good: 'text-blue-400', mediocre: 'text-orange-400', bad: 'text-red-400' };

  return (
    <PhaseWrapper title="Uscita al Cinema" subtitle="Il momento della verita" icon={Ticket} color="emerald">
      {state === 'release_pending' && !result && (
        <div className="space-y-3 text-center">
          <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
            <Ticket className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm font-bold text-white mb-1">Pronto per il rilascio!</p>
            <p className="text-[9px] text-gray-500">Il tuo film entrera nei cinema di tutto il mondo</p>
          </div>
          <button onClick={release} disabled={loading === 'release'}
            className="w-full text-sm py-3 rounded-lg bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30 text-emerald-300 hover:from-emerald-500/30 hover:to-green-500/30 transition-all disabled:opacity-50 font-bold" data-testid="release-btn">
            {loading === 'release' ? 'Calcolo qualita...' : 'RILASCIA NEI CINEMA'}
          </button>
        </div>
      )}

      {(result || state === 'completed' || state === 'released') && (
        <div className="space-y-3">
          <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700/50 text-center space-y-2">
            <p className="text-[9px] text-gray-500 uppercase">Quality Score</p>
            <p className="text-3xl font-bold text-white">{result?.quality_score || film.final_quality || '?'}</p>
            <p className={`text-sm font-bold uppercase ${tierColors[result?.tier || film.final_tier] || 'text-gray-400'}`}>
              {result?.tier || film.final_tier || '—'}
            </p>
          </div>
          {result && (
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded-lg bg-green-500/5 border border-green-500/15 text-center">
                <p className="text-[8px] text-gray-500">Incassi Apertura</p>
                <p className="text-[11px] font-bold text-green-400">${(result.opening_day_revenue || 0).toLocaleString()}</p>
              </div>
              <div className="p-2 rounded-lg bg-yellow-500/5 border border-yellow-500/15 text-center">
                <p className="text-[8px] text-gray-500">XP Guadagnati</p>
                <p className="text-[11px] font-bold text-yellow-400">{result.xp_reward || 0}</p>
              </div>
              <div className="p-2 rounded-lg bg-purple-500/5 border border-purple-500/15 text-center">
                <p className="text-[8px] text-gray-500">Fama</p>
                <p className="text-[11px] font-bold text-purple-400">{result.fame_change > 0 ? '+' : ''}{result.fame_change}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  BOARD — card tratteggiata "Nuovo Film" + film in pipeline
// ═══════════════════════════════════════════════════════════════

const BOARD_HIDDEN = new Set(['released', 'completed', 'discarded', 'premiere_live']);

const BoardView = ({ films, loading, onSelectFilm, onNewFilm }) => {
  const active = films.filter(f => !BOARD_HIDDEN.has(f.pipeline_state));

  return (
    <div className="min-h-screen bg-black text-white px-4 pt-14 pb-24" data-testid="pipeline-v2-board">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-xl font-bold text-amber-400 tracking-tight">Qui inizia la tua produzione!</h1>
        <p className="text-sm text-blue-400 mt-1">Inizia un nuovo film o continua quelli in lavorazione</p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-3 gap-2.5">
        {/* Card tratteggiata Nuovo Film */}
        <button
          onClick={onNewFilm}
          className="flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-700 hover:border-amber-500/50 bg-transparent hover:bg-amber-500/5 transition-all aspect-[2/3] group"
          data-testid="new-film-card"
        >
          <div className="w-9 h-9 rounded-full border-2 border-dashed border-gray-600 group-hover:border-amber-500/60 flex items-center justify-center transition-colors">
            <Plus className="w-4 h-4 text-gray-600 group-hover:text-amber-400 transition-colors" />
          </div>
          <div className="text-center">
            <span className="text-[9px] font-bold text-gray-500 group-hover:text-amber-400 transition-colors block">Nuovo Film</span>
            <span className="text-[7px] text-gray-600 group-hover:text-amber-400/60 transition-colors">Crea da zero</span>
          </div>
        </button>

        {/* Loading skeleton */}
        {loading && [0,1].map(i => (
          <div key={i} className="rounded-xl bg-gray-900/50 border border-gray-800 aspect-[2/3] animate-pulse p-2">
            <div className="w-full h-3/5 bg-gray-800 rounded mb-1.5" />
            <div className="w-2/3 h-2.5 bg-gray-800 rounded mb-1" />
            <div className="w-1/2 h-2 bg-gray-800/60 rounded" />
          </div>
        ))}

        {/* Film cards */}
        {active.map(f => {
          const step = V2_STEPS[Math.max(0, f.pipeline_ui_step ?? 0)] || V2_STEPS[0];
          const StIcon = step.icon;
          const style = STEP_STYLES[step.color];
          return (
            <button
              key={f.id}
              onClick={() => onSelectFilm(f)}
              className="flex flex-col rounded-xl bg-gray-900/60 border border-gray-800 hover:border-gray-600 transition-all overflow-hidden text-left aspect-[2/3]"
              data-testid={`film-card-${f.id}`}
            >
              <div className="w-full flex-1 bg-gray-800 relative min-h-0">
                {f.poster_url ? (
                  <img src={f.poster_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Film className="w-6 h-6 text-gray-700" />
                  </div>
                )}
                <div className={`absolute top-1 right-1 flex items-center gap-0.5 px-1 py-0.5 rounded-full text-[6px] font-bold uppercase ${style.active}`}>
                  <StIcon className="w-2 h-2" />
                  {step.label}
                </div>
              </div>
              <div className="p-1.5">
                <p className="text-[9px] font-bold text-white truncate leading-tight">{f.title}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="text-[7px] text-gray-400 capitalize truncate">{f.genre === 'historical' ? 'storico' : (f.genre || '').replace('_', ' ')}</span>
                  {f.pre_imdb_score > 0 && (
                    <span className="text-[7px] text-yellow-400 font-bold flex items-center gap-0.5">
                      <Star className="w-1.5 h-1.5" />{f.pre_imdb_score}
                    </span>
                  )}
                </div>
                {(f.subgenres || []).length > 0 && (
                  <div className="flex flex-wrap gap-0.5 mt-0.5">
                    {f.subgenres.slice(0, 3).map(sg => (
                      <span key={sg} className="text-[6px] px-1 py-0 rounded bg-amber-500/10 text-amber-400/70 border border-amber-500/15">{sg}</span>
                    ))}
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Empty state */}
      {!loading && active.length === 0 && (
        <div className="text-center py-6">
          <p className="text-[10px] text-gray-600">Nessun film in lavorazione. Crea il tuo primo!</p>
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  MAIN PIPELINE V2 PAGE
// ═══════════════════════════════════════════════════════════════

const GENRES = ['action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance', 'thriller', 'animation', 'documentary', 'fantasy', 'musical', 'western', 'biographical', 'mystery', 'adventure', 'war', 'crime', 'noir', 'historical'];

const PipelineV2 = () => {
  // view: 'board' | 'detail' | 'create'
  const [view, setView] = useState('board');
  const [films, setFilms] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const loadFilms = useCallback(async () => {
    try {
      const data = await api.get('/films');
      setFilms(data.films || []);
      if (selected) {
        const updated = (data.films || []).find(f => f.id === selected.id);
        if (updated) setSelected(updated);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [selected?.id]);

  useEffect(() => { loadFilms(); }, []);

  const openFilm = (f) => { setSelected(f); setView('detail'); };
  const openCreate = () => setView('create');
  const backToBoard = () => { setSelected(null); setView('board'); loadFilms(); };

  const refreshSelected = async () => {
    if (!selected) return;
    try {
      const data = await api.get(`/films/${selected.id}`);
      setSelected(data.film);
      loadFilms();
    } catch (e) { console.error(e); }
  };

  const discardFilm = async () => {
    if (!selected) return;
    try {
      await api.post(`/films/${selected.id}/discard`);
      backToBoard();
      toast({ title: 'Film scartato' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
  };

  const renderPhase = () => {
    if (!selected) return null;
    const st = selected.pipeline_state;
    const ui = selected.pipeline_ui_step;
    const props = { film: selected, onRefresh: refreshSelected, toast };

    if (ui === 0 || st === 'draft' || st === 'idea') return <IdeaPhase {...props} />;
    if (ui === 1 || st === 'proposed' || st === 'hype_setup' || st === 'hype_live') return <HypePhase {...props} />;
    if (ui === 2 || st === 'casting_live') return <CastPhase {...props} />;
    if (ui === 3 || st === 'prep') return <PrepPhase {...props} />;
    if (ui === 4 || st === 'shooting') return <CiakPhase {...props} />;
    if (ui === 5 || st === 'postproduction') return <FinalCutPhase {...props} />;
    if (ui === 6 || st === 'sponsorship' || st === 'marketing') return <MarketingPhase {...props} />;
    if (ui === 7 || st === 'premiere_setup' || st === 'premiere_live') return <LaPrimaPhase {...props} />;
    if (ui === 8 || st === 'release_pending' || st === 'released' || st === 'completed') return <UscitaPhase {...props} />;
    return <div className="p-4 text-center text-gray-500 text-xs">Stato sconosciuto: {st}</div>;
  };

  // ─── CREATE VIEW: title + genre then enter detail ───
  if (view === 'create') {
    return <CreateFilmView onBack={backToBoard} onCreated={(film) => { setSelected(film); setView('detail'); loadFilms(); }} toast={toast} />;
  }

  // ─── DETAIL VIEW ───
  if (view === 'detail' && selected) {
    return (
      <div className="min-h-screen bg-black text-white" data-testid="pipeline-v2-detail">
        <FilmHeader film={selected} onBack={backToBoard} />
        <StepperBar uiStep={selected.pipeline_ui_step ?? 0} />
        {renderPhase()}
        {!['released', 'completed', 'discarded'].includes(selected.pipeline_state) && (
          <div className="p-3 border-t border-gray-800/50">
            <button onClick={discardFilm} className="w-full text-[9px] py-2 rounded-lg bg-red-500/5 border border-red-500/15 text-red-400/60 hover:bg-red-500/10 hover:text-red-400 transition-colors" data-testid="discard-btn">
              Scarta Film
            </button>
          </div>
        )}
      </div>
    );
  }

  // ─── BOARD VIEW (default) ───
  return <BoardView films={films} loading={loading} onSelectFilm={openFilm} onNewFilm={openCreate} />;
};

// ═══════════════════════════════════════════════════════════════
//  CREATE FILM VIEW (step 1: title + genre)
// ═══════════════════════════════════════════════════════════════

const CreateFilmView = ({ onBack, onCreated, toast }) => {
  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('drama');
  const [subgenres, setSubgenres] = useState([]);
  const [creating, setCreating] = useState(false);

  const availableSubs = SUBGENRE_MAP[genre] || [];

  const toggleSub = (sg) => {
    setSubgenres(prev => {
      if (prev.includes(sg)) return prev.filter(s => s !== sg);
      if (prev.length >= 3) return [...prev.slice(1), sg]; // drop oldest
      return [...prev, sg];
    });
  };

  // Reset subgenres when genre changes
  const changeGenre = (g) => { setGenre(g); setSubgenres([]); };

  const create = async () => {
    if (!title.trim()) return;
    setCreating(true);
    try {
      const res = await api.post('/films', { title: title.trim(), genre, subgenres });
      toast({ title: 'Film creato!' });
      onCreated(res.film);
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setCreating(false);
  };

  return (
    <div className="min-h-screen bg-black text-white p-3" data-testid="pipeline-v2-create">
      <div className="flex items-center gap-3 mb-5">
        <button onClick={onBack} className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center hover:bg-gray-700 transition-colors" data-testid="create-back-btn">
          <ChevronLeft className="w-4 h-4 text-gray-400" />
        </button>
        <h2 className="text-base font-bold">Nuovo Film</h2>
      </div>

      <div className="space-y-4 max-w-md">
        <div>
          <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold block mb-1.5">Titolo del Film</label>
          <input
            value={title} onChange={e => setTitle(e.target.value)}
            placeholder="Il titolo del tuo capolavoro..."
            autoFocus
            className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-gray-600 focus:border-amber-500/50 focus:outline-none"
            data-testid="create-title"
          />
        </div>
        <div>
          <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold block mb-1.5">Genere</label>
          <select
            value={genre} onChange={e => changeGenre(e.target.value)}
            className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white focus:border-amber-500/50 focus:outline-none"
            data-testid="create-genre"
          >
            {GENRES.map(g => <option key={g} value={g}>{g === 'historical' ? 'storico' : g.replace('_', ' ')}</option>)}
          </select>
        </div>

        {/* Subgenres chips */}
        <div>
          <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold block mb-1.5">
            Sottogeneri <span className="text-gray-600">(max 3)</span>
          </label>
          <div className="flex flex-wrap gap-1.5" data-testid="subgenre-chips">
            {availableSubs.map(sg => {
              const active = subgenres.includes(sg);
              return (
                <button
                  key={sg} onClick={() => toggleSub(sg)}
                  className={`px-2.5 py-1 rounded-full text-[10px] font-medium border transition-all ${
                    active
                      ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                      : 'bg-gray-800/40 border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-300'
                  }`}
                  data-testid={`subgenre-${sg}`}
                >
                  {sg}
                </button>
              );
            })}
          </div>
          {subgenres.length > 0 && (
            <p className="text-[8px] text-amber-400/60 mt-1.5">{subgenres.length}/3 selezionati: {subgenres.join(', ')}</p>
          )}
        </div>

        <button
          onClick={create}
          disabled={creating || !title.trim()}
          className="w-full text-sm py-3 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 hover:bg-amber-500/25 transition-colors disabled:opacity-30 font-bold flex items-center justify-center gap-2"
          data-testid="create-confirm-btn"
        >
          <Plus className="w-4 h-4" />
          {creating ? 'Creazione...' : 'Crea e Inizia'}
        </button>
      </div>
    </div>
  );
};

export default PipelineV2;
