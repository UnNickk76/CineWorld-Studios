import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Film, Star, Zap, Clock, ChevronLeft, ChevronRight, ChevronDown, Check, Eye, X,
  Plus, Sparkles, Camera, Clapperboard, Megaphone, Award, Ticket,
  MapPin, Palette, FileText, Lock, Users, Music, Wand2, Play,
  Timer, TrendingUp, DollarSign, Building2, Globe, Heart, Send,
  Pencil, Tv, BarChart3, PlayCircle, RefreshCw
} from 'lucide-react';
import { Badge } from '../components/ui/badge';
import { useToast } from '../hooks/use-toast';
import CiakIntroOverlay from '../components/CiakIntroOverlay';
import CinematicReleaseOverlay from '../components/CinematicReleaseOverlay';

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
    const token = localStorage.getItem('cineworld_token');
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
      const token = localStorage.getItem('cineworld_token');
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

// Steps that CANNOT be edited (timer-based)
const EDIT_BLOCKED_STEPS = new Set([4, 5, 8]);

const StepperBar = ({ uiStep, onViewStep, allowScheduleStep }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      const active = ref.current.querySelector(`[data-step="${uiStep}"]`);
      if (active) active.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
  }, [uiStep]);

  return (
    <div className="px-1 py-2">
      <div ref={ref} className="flex items-center gap-0 px-1 pr-6 overflow-x-auto scrollbar-hide" data-testid="v2-stepper">
        {V2_STEPS.map((step, i) => {
          const Icon = step.icon;
          const style = STEP_STYLES[step.color];
          const isCurrent = i === uiStep;
          const isCompleted = i < uiStep;
          const isSchedulable = allowScheduleStep && i === uiStep + 1;
          return (
            <React.Fragment key={step.id}>
              {i > 0 && <div className={`w-3 sm:w-5 h-0.5 flex-shrink-0 ${isCompleted || isCurrent ? style.line : 'bg-gray-800'}`} />}
              <div className="flex flex-col items-center gap-0.5 flex-shrink-0 relative" data-step={i}>
                <div
                  onClick={isCompleted ? () => onViewStep(i) : isSchedulable ? () => onViewStep(i) : undefined}
                  className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                    isCurrent ? `${style.active} shadow-lg shadow-${step.color}-500/20 scale-110` :
                    isCompleted ? 'border-emerald-600 bg-emerald-500/10 text-emerald-400 cursor-pointer hover:border-cyan-400 hover:bg-cyan-500/10 active:scale-95' :
                    isSchedulable ? `${STEP_STYLES[step.color].active} opacity-70 cursor-pointer animate-pulse` :
                    'border-gray-800 bg-gray-900/50 text-gray-700'
                  }`}
                  data-testid={isCompleted ? `view-step-${i}` : isSchedulable ? `schedule-step-${i}` : undefined}
                >
                  {isCompleted ? <Check className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
                </div>
                {isCompleted && (
                  <div className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-cyan-500 flex items-center justify-center shadow-sm">
                    <Eye className="w-2 h-2 text-black" />
                  </div>
                )}
                <span className={`text-[6px] sm:text-[7px] font-bold tracking-wider uppercase whitespace-nowrap ${
                  isCurrent ? style.text : isCompleted ? 'text-emerald-500/60' : isSchedulable ? STEP_STYLES[step.color].text + ' opacity-70' : 'text-gray-700'
                }`}>{step.label}</span>
              </div>
            </React.Fragment>
          );
        })}
      </div>
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
      <h2 className="text-sm font-bold text-white truncate">{film.title || 'Nuovo Progetto'}</h2>
      <div className="flex items-center gap-2 mt-0.5">
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium uppercase">{film.genre || '—'}</span>
        {film.content_type && film.content_type !== 'film' && (
          <span className={`text-[8px] px-1 py-0.5 rounded font-bold ${
            film.content_type === 'serie_tv' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/15' :
            'bg-pink-500/10 text-pink-400 border border-pink-500/15'
          }`}>{film.content_type === 'serie_tv' ? 'Serie TV' : 'Anime'}{film.season_number > 1 ? ` S${film.season_number}` : ''}</span>
        )}
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
//  CINE CONFIRM MODAL (Cineox + Velion — used everywhere)
// ═══════════════════════════════════════════════════════════════

const CineConfirm = ({ open, title, subtitle, confirmLabel = 'Conferma', onConfirm, onCancel }) => {
  if (!open) return null;
  return (
    <>
      <style>{`
        @keyframes cineBackdropIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes cineModalIn { from { opacity: 0; transform: scale(0.88) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
        @keyframes cineGlowPulse {
          0%, 100% { box-shadow: 0 0 20px rgba(255,180,50,0.1), inset 0 0 30px rgba(255,180,50,0.02); }
          50% { box-shadow: 0 0 45px rgba(255,180,50,0.25), inset 0 0 40px rgba(255,180,50,0.04); }
        }
        @keyframes cineFloat {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
        @keyframes cineFloatAlt {
          0%, 100% { transform: translateY(-2px); }
          50% { transform: translateY(4px); }
        }
        @keyframes cineGrain {
          0%, 100% { transform: translate(0, 0); }
          10% { transform: translate(-1%, -1%); }
          30% { transform: translate(1%, 2%); }
          50% { transform: translate(-2%, 1%); }
          70% { transform: translate(2%, -1%); }
          90% { transform: translate(-1%, 2%); }
        }
      `}</style>
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        style={{ animation: 'cineBackdropIn 0.25s ease-out' }}
        onClick={onCancel}
        data-testid="cine-confirm-modal"
      >
        <div
          className="relative bg-[#0d0d0f] border border-amber-500/25 rounded-2xl p-5 max-w-sm w-full space-y-4 overflow-hidden"
          style={{ animation: 'cineModalIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), cineGlowPulse 3s ease-in-out infinite' }}
          onClick={e => e.stopPropagation()}
        >
          {/* Film grain overlay */}
          <div className="absolute inset-0 pointer-events-none opacity-[0.04] rounded-2xl overflow-hidden">
            <div className="absolute inset-0" style={{
              backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\' opacity=\'0.5\'/%3E%3C/svg%3E")',
              animation: 'cineGrain 0.3s steps(4) infinite',
            }} />
          </div>

          {/* Characters */}
          <div className="relative z-10 flex items-end justify-center gap-2">
            <div style={{ animation: 'cineFloatAlt 3.5s ease-in-out infinite' }}>
              <img src="/assets/characters/cineox.png" alt="Cineox" className="w-16 h-16 object-contain drop-shadow-lg" />
            </div>
            <div className="flex-1 text-center px-1">
              <p className="text-xs text-amber-300 font-bold leading-tight" style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: '15px', letterSpacing: '0.5px' }}>{title}</p>
              {subtitle && <p className="text-[8px] text-gray-400 mt-1 leading-relaxed">{subtitle}</p>}
            </div>
            <div style={{ animation: 'cineFloat 3s ease-in-out infinite', filter: 'drop-shadow(0 0 8px rgba(0,180,255,0.3))' }}>
              <img src="/assets/characters/velion.png" alt="Velion" className="w-16 h-16 object-contain" />
            </div>
          </div>

          {/* Buttons */}
          <div className="relative z-10 flex gap-2.5">
            <button
              onClick={onCancel}
              className="flex-1 py-2.5 rounded-xl bg-gray-800/80 border border-gray-700/50 text-gray-400 text-[10px] font-bold hover:bg-gray-700 active:scale-[0.96] transition-all"
              data-testid="cine-cancel-btn"
            >
              Annulla
            </button>
            <button
              onClick={onConfirm}
              className="flex-1 py-2.5 rounded-xl bg-amber-500/15 border border-amber-500/35 text-amber-400 text-[10px] font-bold hover:bg-amber-500/25 hover:shadow-[0_0_15px_rgba(255,180,50,0.2)] active:scale-[0.96] transition-all"
              data-testid="cine-confirm-btn"
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

// ═══════════════════════════════════════════════════════════════
//  SPEEDUP PANEL (4 tiers — used by all timer phases)
// ═══════════════════════════════════════════════════════════════

const SPEEDUP_TIERS = [
  { pct: 25,  label: '25%',  color: 'green' },
  { pct: 50,  label: '50%',  color: 'yellow' },
  { pct: 75,  label: '75%',  color: 'orange' },
  { pct: 100, label: 'MAX',  color: 'red' },
];


// ═══ THEATER STATS PANEL — expandable stats, Withdraw & Send to TV ═══
const TheaterStatsPanel = ({ film, api, onRefresh, toast }) => {
  const [expanded, setExpanded] = useState(false);
  const [stats, setStats] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [loading, setLoading] = useState('');
  const isOwner = true; // shown only to owner
  const ts = film.theater_stats || {};
  const isReleased = film.pipeline_state === 'released';

  // Fetch full stats on expand
  useEffect(() => {
    if (expanded && !stats) {
      api.get(`/films/${film.id}/theater-stats`).then(d => setStats(d?.theater_stats || d)).catch(() => {});
    }
  }, [expanded, film.id, api, stats]);

  const doWithdraw = async () => {
    setConfirmAction(null); setLoading('withdraw');
    try {
      await api.post(`/films/${film.id}/withdraw-theater`);
      toast({ title: 'Film ritirato dalle sale' }); onRefresh();
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };
  const doSendTV = async () => {
    setConfirmAction(null); setLoading('tv');
    try {
      await api.post(`/films/${film.id}/send-to-tv`);
      // Also withdraw from theater
      if (isReleased) await api.post(`/films/${film.id}/withdraw-theater`).catch(() => {});
      toast({ title: 'Film inviato in TV e ritirato dalle sale!' }); onRefresh();
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const perfColors = { great:'text-green-400', good:'text-emerald-400', ok:'text-yellow-400', declining:'text-orange-400', bad:'text-red-400', flop:'text-red-500' };
  const perfLabels = { great:'Straordinario', good:'Ottimo', ok:'Discreto', declining:'In calo', bad:'Scarso', flop:'Flop' };
  const trendIcon = (t) => t === 'up' ? '▲' : t === 'down' ? '▼' : '●';
  const trendColor = (t) => t === 'up' ? 'text-green-400' : t === 'down' ? 'text-red-400' : 'text-gray-400';

  const fullStats = stats?.theater_stats || ts;

  return (
    <div className="rounded-lg border border-yellow-500/20 overflow-hidden">
      {/* Compact bar — always visible */}
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-center justify-between px-3 py-2 bg-yellow-500/5 hover:bg-yellow-500/10 transition-colors" data-testid="theater-stats-toggle">
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-bold text-yellow-400">{isReleased ? 'IN SALA' : 'FUORI SALA'}</span>
          <span className={`text-[8px] font-bold ${perfColors[ts.performance] || 'text-gray-400'}`}>{perfLabels[ts.performance] || '—'}</span>
        </div>
        <div className="flex items-center gap-3 text-[8px]">
          <span className="text-gray-400">{ts.days_in_theater || 0}gg in sala</span>
          {isReleased && <span className="text-yellow-400/70">{ts.days_remaining || 0}gg rimasti</span>}
          {(ts.days_extended || 0) > 0 && <span className="text-green-400">+{ts.days_extended}gg</span>}
          {(ts.days_reduced || 0) > 0 && <span className="text-red-400">-{ts.days_reduced}gg</span>}
          <span className="text-gray-600">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* Expanded stats */}
      {expanded && (
        <div className="p-3 space-y-2 bg-gray-900/50">
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
              <p className="text-[7px] text-gray-500">Cinema</p>
              <p className="text-[11px] font-bold text-white">{fullStats.current_cinemas || 0}</p>
            </div>
            <div className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
              <p className="text-[7px] text-gray-500">Spettatori oggi</p>
              <p className="text-[11px] font-bold text-cyan-400">{(fullStats.daily_spectators || 0).toLocaleString()}</p>
            </div>
            <div className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
              <p className="text-[7px] text-gray-500">Spettatori totali</p>
              <p className="text-[11px] font-bold text-yellow-400">{(fullStats.total_spectators || 0).toLocaleString()}</p>
            </div>
          </div>

          {/* Last 3 days trend */}
          {fullStats.daily_history?.length > 0 && (
            <div>
              <p className="text-[7px] text-gray-500 uppercase font-bold mb-1">Andamento ultimi 3 giorni</p>
              <div className="flex gap-1">
                {fullStats.daily_history.slice(-3).map((d, i) => (
                  <div key={i} className="flex-1 p-1.5 rounded bg-white/[0.02] border border-white/5 text-center">
                    <p className="text-[7px] text-gray-600">Giorno {d.day}</p>
                    <p className={`text-[9px] font-bold ${trendColor(d.trend)}`}>{trendIcon(d.trend)} {d.spectators?.toLocaleString()}</p>
                    <p className="text-[6px] text-gray-600">{d.cinemas} cinema</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Revenue */}
          <div className="flex justify-between items-center px-1">
            <span className="text-[8px] text-gray-500">Incassi sala totali</span>
            <span className="text-[10px] font-bold text-green-400">${(fullStats.total_revenue || 0).toLocaleString()}</span>
          </div>

          {/* Owner action buttons */}
          {isOwner && isReleased && (
            <div className="flex gap-2 pt-1">
              <button onClick={() => setConfirmAction('withdraw')} disabled={!!loading}
                className="flex-1 text-[9px] py-2 rounded-lg bg-red-500/10 border border-red-500/25 text-red-400 hover:bg-red-500/20 font-bold disabled:opacity-40" data-testid="withdraw-theater-btn">
                {loading === 'withdraw' ? '...' : 'Ritira dalle sale'}
              </button>
              <button onClick={() => setConfirmAction('tv')} disabled={!!loading}
                className="flex-1 text-[9px] py-2 rounded-lg bg-blue-500/10 border border-blue-500/25 text-blue-400 hover:bg-blue-500/20 font-bold disabled:opacity-40" data-testid="send-to-tv-btn">
                {loading === 'tv' ? '...' : 'Manda in TV'}
              </button>
            </div>
          )}
        </div>
      )}
      <CineConfirm open={confirmAction === 'withdraw'} title="Ritirare il film dalle sale?" confirmLabel="Ritira" onConfirm={doWithdraw} onCancel={() => setConfirmAction(null)} />
      <CineConfirm open={confirmAction === 'tv'} title="Inviare in TV e ritirare dalle sale?" confirmLabel="Conferma" onConfirm={doSendTV} onCancel={() => setConfirmAction(null)} />
    </div>
  );
};


const SpeedupPanel = ({ film, onRefresh, toast }) => {
  const [costs, setCosts] = useState(null);
  const [loading, setLoading] = useState('');
  const [confirmPct, setConfirmPct] = useState(null);
  const isGuest = JSON.parse(localStorage.getItem('cineworld_user') || '{}').is_guest;

  useEffect(() => {
    api.get(`/films/${film.id}/speedup-costs`).then(d => setCosts(d.costs || {})).catch(() => {});
  }, [film.id, film.pipeline_metrics?.last_speedup]);

  const doSpeedup = async (pct) => {
    setConfirmPct(null);
    setLoading(String(pct));
    try {
      const res = await api.post(`/films/${film.id}/speedup`, { percentage: pct });
      onRefresh();
      toast({ title: `Accelerato del ${pct}%!${isGuest ? '' : ` (-${res.credits_spent} crediti)`}` });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  if (!costs) return null;

  return (
    <div className="space-y-1.5" data-testid="speedup-panel">
      <p className="text-[8px] text-gray-500 uppercase font-bold tracking-wider">Accelera (crediti)</p>
      <div className="grid grid-cols-4 gap-1.5">
        {SPEEDUP_TIERS.map(t => {
          const cost = costs[String(t.pct)] || '?';
          const isLoading = loading === String(t.pct);
          const colors = {
            green: 'bg-emerald-500/10 border-emerald-500/25 text-emerald-400 hover:bg-emerald-500/20',
            yellow: 'bg-yellow-500/10 border-yellow-500/25 text-yellow-400 hover:bg-yellow-500/20',
            orange: 'bg-orange-500/10 border-orange-500/25 text-orange-400 hover:bg-orange-500/20',
            red: 'bg-red-500/10 border-red-500/25 text-red-400 hover:bg-red-500/20',
          };
          return (
            <button
              key={t.pct}
              onClick={() => isGuest ? doSpeedup(t.pct) : setConfirmPct(t.pct)}
              disabled={!!loading}
              className={`flex flex-col items-center py-2 px-1 rounded-lg border transition-colors disabled:opacity-40 ${colors[t.color]}`}
              data-testid={`speedup-${t.pct}`}
            >
              <span className="text-[10px] font-bold">{isLoading ? '...' : t.label}</span>
              {isGuest
                ? <span className="text-[7px] mt-0.5"><s className="opacity-40">{cost} cr</s> <span className="text-green-400 font-bold">GRATIS</span></span>
                : <span className="text-[7px] opacity-70 mt-0.5">{cost} cr</span>
              }
            </button>
          );
        })}
      </div>
      <CineConfirm
        open={confirmPct !== null}
        title={`Accelera del ${confirmPct}% per ${costs?.[String(confirmPct)] || '?'} crediti?`}
        confirmLabel="Accelera!"
        onConfirm={() => doSpeedup(confirmPct)}
        onCancel={() => setConfirmPct(null)}
      />
    </div>
  );
};

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
          <div className="w-full bg-gray-800/30 border border-gray-700/50 rounded-lg px-3 py-2 text-xs text-amber-400 font-medium capitalize" data-testid="idea-genre">
            {(genre || film.genre || '').replace('_', ' ') || '—'}
          </div>
        </div>
        <div>
          <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold">Sottogeneri</label>
          <div className="w-full bg-gray-800/30 border border-gray-700/50 rounded-lg px-3 py-2 text-xs text-gray-300 min-h-[32px] flex flex-wrap gap-1" data-testid="idea-subgenre">
            {(film.subgenres || []).length > 0
              ? film.subgenres.map(sg => <span key={sg} className="px-1.5 py-0 rounded bg-amber-500/10 text-amber-400/80 text-[9px] border border-amber-500/15">{sg}</span>)
              : <span className="text-gray-600">—</span>
            }
          </div>
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
        <label className="text-[9px] text-gray-500 uppercase tracking-wider font-bold flex items-center gap-1"><MapPin className="w-3 h-3" /> Location ({locations.length})</label>
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
                      else setLocations([...locations, l]);
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
        {/* Poster display with async regen */}
        {film.poster_url ? (
          <div className="relative group">
            <img src={film.poster_url} alt="" className={`w-full max-w-[160px] mx-auto rounded-lg border border-gray-700 transition-opacity ${loading === 'regen-poster' ? 'opacity-30' : ''}`} />
            {loading === 'regen-poster' && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-1">
                <div className="w-6 h-6 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-[8px] text-yellow-400">Generazione in corso...</span>
              </div>
            )}
            {(film.poster_regen_count || 0) < 3 ? (
              <button
                onClick={async () => {
                  setLoading('regen-poster');
                  try {
                    const res = await api.post(`/films/${film.id}/regenerate-poster`);
                    const jobId = res.data.job_id;
                    // Poll for completion
                    const poll = setInterval(async () => {
                      try {
                        const st = await api.get(`/poster-status/${jobId}`);
                        if (st.data.status === 'completed') {
                          clearInterval(poll);
                          setFilm(prev => ({ ...prev, poster_url: st.data.poster_url + '?t=' + Date.now(), poster_regen_count: (prev.poster_regen_count || 0) + 1 }));
                          toast({ title: 'Locandina rigenerata!' });
                          setLoading(null);
                        } else if (st.data.status === 'failed') {
                          clearInterval(poll);
                          toast({ title: st.data.error || 'Errore, riprova', variant: 'destructive' });
                          setLoading(null);
                        }
                      } catch { /* continue polling */ }
                    }, 2000);
                    // Failsafe: stop after 40s
                    setTimeout(() => { clearInterval(poll); setLoading(null); }, 40000);
                  } catch (e) { toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' }); setLoading(null); }
                }}
                disabled={loading === 'regen-poster'}
                className="absolute top-1 right-1 px-1.5 py-0.5 rounded bg-black/60 border border-yellow-500/30 text-yellow-400 text-[8px] flex items-center gap-0.5 opacity-0 group-hover:opacity-100 hover:bg-black/80 transition-all disabled:opacity-30"
                data-testid="regen-poster-btn"
              >
                <RefreshCw className="w-2.5 h-2.5" /> Rigenera
              </button>
            ) : (
              <span className="absolute top-1 right-1 px-1.5 py-0.5 rounded bg-black/60 text-gray-500 text-[7px]">Max 3 rigenerate</span>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-4">
            <Film className="w-8 h-8 text-gray-600" />
            <p className="text-[9px] text-gray-500">Locandina non disponibile</p>
            <button
              onClick={async () => {
                setLoading('regen-poster');
                try {
                  const res = await api.post(`/films/${film.id}/regenerate-poster`);
                  const jobId = res.data.job_id;
                  const poll = setInterval(async () => {
                    try {
                      const st = await api.get(`/poster-status/${jobId}`);
                      if (st.data.status === 'completed') {
                        clearInterval(poll);
                        setFilm(prev => ({ ...prev, poster_url: st.data.poster_url, poster_regen_count: 1, pipeline_flags: { ...prev.pipeline_flags, has_poster: true } }));
                        toast({ title: 'Locandina generata!' });
                        setLoading(null);
                      } else if (st.data.status === 'failed') {
                        clearInterval(poll);
                        toast({ title: st.data.error || 'Errore', variant: 'destructive' });
                        setLoading(null);
                      }
                    } catch { /* continue */ }
                  }, 2000);
                  setTimeout(() => { clearInterval(poll); setLoading(null); }, 40000);
                } catch (e) { toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' }); setLoading(null); }
              }}
              disabled={loading === 'regen-poster'}
              className="px-3 py-1.5 rounded-lg bg-yellow-500/15 border border-yellow-500/30 text-yellow-400 text-[10px] flex items-center gap-1 hover:bg-yellow-500/25 transition-colors disabled:opacity-50"
              data-testid="gen-poster-btn"
            >
              {loading === 'regen-poster' ? <><div className="w-3 h-3 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" /> Generazione...</> : <><Sparkles className="w-3 h-3" /> Genera Locandina</>}
            </button>
          </div>
        )}
        {!hasPoster && !film.poster_url && (
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
                  data-testid={`screenplay-${m.replace('_','-')}`}
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

  // Matrix effect colors by genre
  const genreColors = {
    horror: '#ff0033', sci_fi: '#00e5ff', comedy: '#00ff88', drama: '#ffaa00',
    action: '#ff6600', thriller: '#cc00ff', romance: '#ff69b4', fantasy: '#9966ff',
    historical: '#daa520', documentary: '#44ff44', musical: '#ff44ff',
  };
  const matrixColor = genreColors[film.genre] || '#00ff88';
  const canvasRef = useRef(null);
  const isHypeLive = state === 'hype_live';

  useEffect(() => {
    if (!isHypeLive) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const resize = () => { canvas.width = canvas.parentElement.offsetWidth; canvas.height = canvas.parentElement.offsetHeight; };
    resize();
    window.addEventListener('resize', resize);
    const letters = '01CINEWORLDSTUDIO';
    const fontSize = 14;
    const columns = Math.floor(canvas.width / fontSize);
    const drops = Array(columns).fill(1);
    const draw = () => {
      ctx.fillStyle = 'rgba(0,0,0,0.04)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.shadowColor = matrixColor;
      ctx.shadowBlur = 6;
      ctx.fillStyle = matrixColor;
      ctx.font = `bold ${fontSize}px monospace`;
      for (let i = 0; i < drops.length; i++) {
        const text = letters[Math.floor(Math.random() * letters.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    };
    const interval = setInterval(draw, 33);
    return () => { clearInterval(interval); window.removeEventListener('resize', resize); };
  }, [isHypeLive, matrixColor]);

  return (
    <div className="relative overflow-hidden">
      {/* Matrix canvas — behind everything */}
      {isHypeLive && (
        <canvas ref={canvasRef} className="absolute inset-0 z-0 opacity-[0.25] pointer-events-none" data-testid="matrix-canvas" />
      )}
      <div className="relative z-10">
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
      {state === 'hype_live' && <HypeLivePanel film={film} remaining={remaining} done={done} onRefresh={onRefresh} toast={toast} loading={loading} completeHype={completeHype} />}
    </PhaseWrapper>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  HYPE LIVE PANEL (dynamic bar + polling)
// ═══════════════════════════════════════════════════════════════

const HypeLivePanel = ({ film, remaining, done, onRefresh, toast, loading, completeHype }) => {
  const [live, setLive] = useState(null);
  const [prevHype, setPrevHype] = useState(null);
  const [prevAgencies, setPrevAgencies] = useState(null);
  const [hypeDelta, setHypeDelta] = useState(null);
  const [agDelta, setAgDelta] = useState(null);

  const fetchLive = useCallback(async () => {
    try {
      const d = await api.get(`/films/${film.id}/hype-live`);
      setLive(prev => {
        if (prev) {
          const hd = d.hype - prev.hype;
          const ad = d.agencies - prev.agencies;
          if (hd !== 0) setHypeDelta(hd);
          if (ad !== 0) setAgDelta(ad);
          setTimeout(() => setHypeDelta(null), 2500);
          setTimeout(() => setAgDelta(null), 2500);
        }
        return d;
      });
    } catch {}
  }, [film.id]);

  useEffect(() => {
    fetchLive();
    const interval = setInterval(fetchLive, 8000);
    return () => clearInterval(interval);
  }, [fetchLive]);

  const hype = live?.hype ?? film.pipeline_metrics?.hype_score ?? 0;
  const hypeTarget = live?.hype_target ?? hype;
  const agencies = live?.agencies ?? 0;
  const agTarget = live?.agencies_target ?? agencies;
  const ratio = live?.ratio ?? 0;
  const hypePct = hypeTarget > 0 ? Math.min(100, Math.round((hype / hypeTarget) * 100)) : 0;
  const agPct = agTarget > 0 ? Math.min(100, Math.round((agencies / agTarget) * 100)) : 0;

  return (
    <div className="space-y-3" data-testid="hype-live-panel">
      {/* Timer */}
      <div className="p-3 rounded-lg bg-orange-500/5 border border-orange-500/20 text-center">
        <p className="text-[9px] text-gray-500 uppercase">Hype in corso</p>
        <p className="text-lg font-bold text-orange-400 font-mono">{remaining}</p>
      </div>

      {/* Hype bar */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-[9px] text-gray-500 uppercase font-bold">Hype</span>
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-orange-400">{hype}</span>
            <span className="text-[8px] text-gray-600">/ {hypeTarget}</span>
            {hypeDelta !== null && (
              <span className={`text-[9px] font-bold animate-pulse ${hypeDelta > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {hypeDelta > 0 ? '+' : ''}{hypeDelta}
              </span>
            )}
          </div>
        </div>
        <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
          <div className="h-full rounded-full bg-gradient-to-r from-orange-600 to-amber-400 transition-all duration-1000 ease-out"
            style={{ width: `${hypePct}%` }} />
        </div>
      </div>

      {/* Agencies bar */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-[9px] text-gray-500 uppercase font-bold">Agenzie</span>
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-cyan-400">{agencies}</span>
            <span className="text-[8px] text-gray-600">/ {agTarget}</span>
            {agDelta !== null && (
              <span className={`text-[9px] font-bold animate-pulse ${agDelta > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {agDelta > 0 ? '+' : ''}{agDelta}
              </span>
            )}
          </div>
        </div>
        <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
          <div className="h-full rounded-full bg-gradient-to-r from-cyan-600 to-cyan-400 transition-all duration-1000 ease-out"
            style={{ width: `${agPct}%` }} />
        </div>
      </div>

      {!done && <SpeedupPanel film={film} onRefresh={() => { onRefresh(); fetchLive(); }} toast={toast} />}
      {done && (
        <button onClick={completeHype} disabled={loading === 'complete'}
          className="w-full text-[10px] py-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="complete-hype-btn">
          {loading === 'complete' ? '...' : 'Vai al Cast'}
        </button>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 3 — CAST
// ═══════════════════════════════════════════════════════════════

const CAST_TABS = [
  { key: 'director', label: 'Registi', icon: Camera, max: 1 },
  { key: 'writer', label: 'Sceneggiatori', icon: FileText, max: 3 },
  { key: 'actor', label: 'Attori', icon: Star, max: 99 },
  { key: 'composer', label: 'Compositori', icon: Music, max: 1 },
];

const FAME_COLORS = {
  sconosciuto: 'text-gray-500 bg-gray-500/10',
  emergente: 'text-teal-400 bg-teal-500/10',
  conosciuto: 'text-blue-400 bg-blue-500/10',
  famoso: 'text-orange-400 bg-orange-500/10',
  star: 'text-yellow-400 bg-yellow-500/10',
};

const SkillBar = ({ name, value }) => {
  const color = value >= 80 ? 'bg-emerald-500' : value >= 60 ? 'bg-yellow-500' : value >= 40 ? 'bg-orange-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[7px] text-gray-500 w-16 truncate">{name}</span>
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-[7px] text-gray-400 w-5 text-right">{value}</span>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  CHEMISTRY PANEL — Indicatori chimica cast (no numeri, solo colori)
// ═══════════════════════════════════════════════════════════════

const CHEM_ICONS = {
  good: { dot: 'bg-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-500/5', text: 'text-emerald-400', label: 'Buona intesa' },
  neutral: { dot: 'bg-amber-400', border: 'border-amber-500/30', bg: 'bg-amber-500/5', text: 'text-amber-400', label: 'Neutrale' },
  tension: { dot: 'bg-red-400', border: 'border-red-500/30', bg: 'bg-red-500/5', text: 'text-red-400', label: 'Tensione' },
};

const ChemistryPanel = ({ film, loading, setLoading, toast }) => {
  const [chemData, setChemData] = useState(null);
  const [showPairs, setShowPairs] = useState(false);

  const castActors = film.cast?.actors || [];
  const hasDirector = !!film.cast?.director;
  const enoughCast = castActors.length >= 2 || (castActors.length >= 1 && hasDirector);

  // Use pipeline_metrics indicator as default
  const savedIndicator = film.pipeline_metrics?.cast_chemistry_indicator;
  const savedPairs = film.cast_chemistry_pairs || [];

  const fetchChemistry = async () => {
    setLoading('chem');
    try {
      const res = await api.get(`/films/${film.id}/cast-chemistry`);
      setChemData(res);
      toast({ title: `Chimica analizzata!` });
    } catch (e) {
      toast({ title: 'Errore', description: e.message, variant: 'destructive' });
    }
    setLoading('');
  };

  const displayData = chemData || (savedIndicator ? { indicator: savedIndicator, pairs: savedPairs.map(p => ({ a_name: p.a_name, b_name: p.b_name, indicator: p.indicator })), best_pair: film.cast_chemistry_best ? { a_name: film.cast_chemistry_best.a_name, b_name: film.cast_chemistry_best.b_name, indicator: film.cast_chemistry_best.indicator } : null, worst_pair: film.cast_chemistry_worst ? { a_name: film.cast_chemistry_worst.a_name, b_name: film.cast_chemistry_worst.b_name, indicator: film.cast_chemistry_worst.indicator } : null } : null);

  if (!enoughCast) return null;

  const style = CHEM_ICONS[displayData?.indicator || 'neutral'];

  return (
    <div className={`p-2 rounded-lg ${style.bg} border ${style.border} space-y-1.5`} data-testid="chemistry-panel">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Heart className="w-3.5 h-3.5 text-pink-400" />
          <span className="text-[9px] text-gray-400 font-bold uppercase">Chimica Cast</span>
          {displayData && (
            <span className="flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full ${style.dot}`} />
              <span className={`text-[9px] font-bold ${style.text}`}>{style.label}</span>
            </span>
          )}
        </div>
        <button onClick={fetchChemistry} disabled={loading === 'chem'}
          className="text-[7px] px-2 py-1 rounded bg-pink-500/10 border border-pink-500/20 text-pink-400 hover:bg-pink-500/20 transition-colors disabled:opacity-40 font-bold"
          data-testid="analyze-chemistry-btn">
          {loading === 'chem' ? '...' : displayData ? 'Rianalizza' : 'Analizza'}
        </button>
      </div>

      {/* Pairs preview */}
      {displayData?.pairs?.length > 0 && (
        <>
          <button onClick={() => setShowPairs(!showPairs)} className="text-[7px] text-gray-500 hover:text-gray-300 transition-colors">
            {showPairs ? 'Nascondi coppie' : `Mostra ${displayData.pairs.length} coppie`}
          </button>
          {showPairs && (
            <div className="grid grid-cols-2 gap-1 max-h-32 overflow-y-auto" data-testid="chemistry-pairs">
              {displayData.pairs.map((p, i) => {
                const ps = CHEM_ICONS[p.indicator || 'neutral'];
                return (
                  <div key={i} className={`flex items-center gap-1 px-1.5 py-1 rounded ${ps.bg} border ${ps.border}`}>
                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${ps.dot}`} />
                    <span className="text-[7px] text-gray-300 truncate">{p.a_name?.split(' ')[0]} + {p.b_name?.split(' ')[0]}</span>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Best / Worst highlights */}
      {displayData?.best_pair && displayData?.worst_pair && displayData.best_pair.indicator !== displayData.worst_pair.indicator && (
        <div className="flex gap-1.5 text-[7px]">
          {displayData.best_pair.indicator === 'good' && (
            <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              Migliore: {displayData.best_pair.a_name?.split(' ')[0]} + {displayData.best_pair.b_name?.split(' ')[0]}
            </span>
          )}
          {displayData.worst_pair.indicator === 'tension' && (
            <span className="px-1.5 py-0.5 rounded bg-red-500/10 border border-red-500/20 text-red-400">
              Rischio: {displayData.worst_pair.a_name?.split(' ')[0]} + {displayData.worst_pair.b_name?.split(' ')[0]}
            </span>
          )}
        </div>
      )}
    </div>
  );
};


const CastPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState('');
  const isGuest = JSON.parse(localStorage.getItem('cineworld_user') || '{}').is_guest;
  const [activeTab, setActiveTab] = useState('director');
  const [expandedProposal, setExpandedProposal] = useState(null);
  const [rejectInfo, setRejectInfo] = useState(null);
  const [selectedRole, setSelectedRole] = useState({});
  const cast = film.cast || {};
  const proposals = film.cast_proposals || [];
  const isAnime = film.content_type === 'anime';
  const directors = cast.director ? 1 : 0;
  const screenwriters = (cast.screenwriters || (cast.screenwriter ? [cast.screenwriter] : [])).length;
  const actors = (cast.actors || []).length;
  const composers = cast.composer ? 1 : 0;
  const animators = (cast.animators || []).length;
  const voiceActors = (cast.voice_actors || []).length;
  const canLock = directors >= 1 && (isAnime ? animators >= 1 : actors >= 2);

  // Dynamic tabs based on content_type
  const castTabs = [
    { key: 'director', label: 'Registi', icon: Camera, max: 1 },
    { key: 'writer', label: 'Sceneggiatori', icon: FileText, max: 3 },
    ...(isAnime ? [
      { key: 'animator', label: 'Disegnatori', icon: Palette, max: 3 },
      { key: 'voice_actor', label: 'Doppiatori', icon: Megaphone, max: 5 },
    ] : []),
    { key: 'actor', label: isAnime ? 'Attori (opz.)' : 'Attori', icon: Star, max: 99 },
    { key: 'composer', label: 'Compositori', icon: Music, max: 1 },
  ];

  // IDs of already selected cast — hide them from proposal list
  const selectedIds = new Set();
  if (cast.director?.id) selectedIds.add(cast.director.id);
  for (const sw of (cast.screenwriters || [])) { if (sw?.id) selectedIds.add(sw.id); }
  for (const a of (cast.actors || [])) { if (a?.id) selectedIds.add(a.id); }
  if (cast.composer?.id) selectedIds.add(cast.composer.id);
  for (const anim of (cast.animators || [])) { if (anim?.id) selectedIds.add(anim.id); }
  for (const va of (cast.voice_actors || [])) { if (va?.id) selectedIds.add(va.id); }

  // Filter proposals by active tab role_type, hide rejected AND already selected
  const tabProposals = proposals.map((p, i) => ({...p, _idx: i})).filter(p => p.role_type === activeTab && p.status !== 'rejected' && !selectedIds.has(p.id));
  const tabInfo = castTabs.find(t => t.key === activeTab);
  const currentCount = activeTab === 'director' ? directors : activeTab === 'writer' ? screenwriters : activeTab === 'actor' ? actors : activeTab === 'composer' ? composers : activeTab === 'animator' ? animators : activeTab === 'voice_actor' ? voiceActors : 0;
  const tabFull = currentCount >= (tabInfo?.max || 99);

  const ACTOR_ROLES = [
    { key: 'protagonista', label: 'Protagonista' },
    { key: 'co_protagonista', label: 'Co-Protagonista' },
    { key: 'antagonista', label: 'Antagonista' },
    { key: 'supporto', label: 'Supporto' },
    { key: 'cameo', label: 'Cameo' },
    { key: 'generico', label: 'Generico' },
  ];

  const selectCast = async (index) => {
    const castRole = activeTab === 'actor' ? (selectedRole[index] || 'protagonista') : undefined;
    setLoading(`s_${index}`);
    try {
      const res = await api.post(`/films/${film.id}/select-cast`, { proposal_index: index, role: activeTab, cast_role: castRole });
      if (res.rejected) {
        setRejectInfo({ index, role: activeTab, name: res.name, reason: res.reason, cost: res.renegotiate_cost });
      } else {
        toast({ title: `${res.selected} ingaggiato/a${castRole ? ' come ' + castRole.replace('_', '-') : ''}! (-$${(res.cost_paid||0).toLocaleString()})` });
        setExpandedProposal(null);
      }
      onRefresh();
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const renegotiate = async () => {
    if (!rejectInfo) return;
    setLoading('renego');
    try {
      const res = await api.post(`/films/${film.id}/renegotiate-cast`, { proposal_index: rejectInfo.index, role: rejectInfo.role });
      toast({ title: `${res.selected} ha accettato! (-$${(res.cost_paid||0).toLocaleString()})` });
      setRejectInfo(null);
      onRefresh();
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const lockCast = async () => {
    setLoading('lock');
    try {
      await api.post(`/films/${film.id}/lock-cast`);
      onRefresh();
      toast({ title: 'Cast confermato! Avanti con la PREP.' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setLoading('');
  };

  const starsStr = (n) => '★'.repeat(n || 0) + '☆'.repeat(Math.max(0, 5 - (n || 0)));
  const genderIcon = (g) => {
    const gl = (g || '').toLowerCase();
    if (gl === 'm' || gl === 'male') return '♂';
    if (gl === 'f' || gl === 'female') return '♀';
    return '⚧';
  };

  // Chemistry lookup for individual cast members
  const chemPairs = film.cast_chemistry_pairs || [];
  const getPersonChem = (personId) => {
    if (!personId || chemPairs.length === 0) return null;
    const relevant = chemPairs.filter(p => p.a_id === personId || p.b_id === personId);
    if (relevant.length === 0) return null;
    const good = relevant.filter(p => p.indicator === 'good').length;
    const tension = relevant.filter(p => p.indicator === 'tension').length;
    if (tension > good) return 'tension';
    if (good > tension) return 'good';
    return 'neutral';
  };

  // Current selected cast slot
  const CastSlot = ({ label, person, icon: Icon }) => {
    const personChem = person ? getPersonChem(person.id) : null;
    const chemStyle = personChem ? CHEM_ICONS[personChem] : null;
    return (
      <div className={`p-2 rounded-lg border ${person ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-gray-800/30 border-gray-700/50'}`}>
        <div className="flex justify-between items-center">
          <p className="text-[8px] text-gray-500 uppercase font-bold flex items-center gap-1"><Icon className="w-2.5 h-2.5" /> {label}</p>
          <div className="flex items-center gap-1">
            {person?.cast_role && <span className="text-[6px] px-1 py-0.5 rounded bg-violet-500/15 text-violet-400 font-bold">{person.cast_role.replace('_', '-')}</span>}
            {chemStyle && <span className={`w-1.5 h-1.5 rounded-full ${chemStyle.dot}`} title={chemStyle.label} />}
            {person && <span className="text-[7px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold">Scelto</span>}
          </div>
        </div>
        {person ? (
          <div className="flex items-center gap-2 mt-1">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[8px] font-bold ${person.is_star ? 'bg-yellow-500/20 border border-yellow-500/40 text-yellow-400' : 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-400'}`}>
              {(person.name || '?')[0]}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-medium text-white truncate">{person.name}</p>
              <p className="text-[7px] text-gray-500"><span className={`${(person.gender||'').toLowerCase() === 'male' || person.gender === 'M' ? 'text-blue-400' : (person.gender||'').toLowerCase() === 'female' || person.gender === 'F' ? 'text-pink-400' : 'text-gray-400'}`}>{genderIcon(person.gender)}</span> {person.age}a • {person.nationality}{person.imdb_rating ? ` • IMDb ${(person.imdb_rating/10).toFixed(1)}` : ''} • ${(person.cost||0).toLocaleString()}</p>
            </div>
          </div>
        ) : <p className="text-[9px] text-gray-600 italic mt-1">—</p>}
      </div>
    );
  };

  const breakdown = film.pipeline_metrics?.cast_breakdown || [];

  return (
    <PhaseWrapper title="Il Cast" subtitle="Assembla la squadra perfetta" icon={Users} color="cyan">
      {/* Selected Cast Summary */}
      <div className="grid grid-cols-2 gap-1.5">
        <CastSlot label="Regista" person={cast.director} icon={Camera} />
        <CastSlot label="Sceneggiatore" person={(cast.screenwriters || [])[0] || cast.screenwriter} icon={FileText} />
      </div>
      {actors > 0 && (
        <div className="grid grid-cols-2 gap-1.5">
          {(cast.actors || []).map((a, i) => <CastSlot key={i} label={`Attore ${i+1}`} person={a} icon={Star} />)}
        </div>
      )}
      {cast.composer && <CastSlot label="Compositore" person={cast.composer} icon={Music} />}
      {/* Anime-specific roles */}
      {(cast.animators || []).length > 0 && (
        <div className="grid grid-cols-2 gap-1.5">
          {cast.animators.map((a, i) => <CastSlot key={`anim-${i}`} label={`Disegnatore ${i+1}`} person={a} icon={Palette} />)}
        </div>
      )}
      {(cast.voice_actors || []).length > 0 && (
        <div className="grid grid-cols-2 gap-1.5">
          {cast.voice_actors.map((a, i) => <CastSlot key={`va-${i}`} label={`Doppiatore ${i+1}`} person={a} icon={Megaphone} />)}
        </div>
      )}

      {/* Quality + Breakdown */}
      <div className="p-2 rounded-lg bg-cyan-500/5 border border-cyan-500/15 space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-[9px] text-gray-500">Qualita Cast:</span>
          <span className={`text-[11px] font-bold ${(film.pipeline_metrics?.cast_quality || 0) > 50 ? 'text-emerald-400' : 'text-orange-400'}`}>
            {film.pipeline_metrics?.cast_quality || 0}%
          </span>
        </div>
        {breakdown.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {breakdown.slice(0, 6).map((b, i) => (
              <span key={i} className={`text-[7px] px-1 py-0.5 rounded ${b.startsWith('+') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{b}</span>
            ))}
          </div>
        )}
      </div>

      {/* Chemistry Indicator Panel */}
      <ChemistryPanel film={film} loading={loading} setLoading={setLoading} toast={toast} />

      {/* Rejection modal */}
      {rejectInfo && (
        <CineConfirm open={true} title={rejectInfo.reason}
          subtitle={`Offri $${rejectInfo.cost?.toLocaleString()} per convincerlo/a?`}
          confirmLabel="Rinegozia" onConfirm={renegotiate} onCancel={() => setRejectInfo(null)} />
      )}

      {/* TABS */}
      <div className="flex gap-1 overflow-x-auto scrollbar-hide" data-testid="cast-tabs">
        {castTabs.map(tab => {
          const cnt = tab.key === 'director' ? directors : tab.key === 'writer' ? screenwriters : tab.key === 'actor' ? actors : tab.key === 'composer' ? composers : tab.key === 'animator' ? animators : tab.key === 'voice_actor' ? voiceActors : 0;
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          const available = proposals.filter(p => p.role_type === tab.key && p.status !== 'rejected').length;
          return (
            <button key={tab.key} onClick={() => { setActiveTab(tab.key); setExpandedProposal(null); }}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[9px] font-bold whitespace-nowrap transition-colors border ${
                isActive ? 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400' : 'bg-gray-800/30 border-gray-700/50 text-gray-500 hover:text-gray-300'
              }`} data-testid={`tab-${tab.key}`}>
              <Icon className="w-3 h-3" />
              {tab.label}
              <span className={`text-[7px] px-1 rounded ${cnt > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-gray-700 text-gray-500'}`}>
                {cnt}/{tab.max === 99 ? '∞' : tab.max}
              </span>
              <span className="text-[7px] text-gray-600">{available}</span>
            </button>
          );
        })}
      </div>

      {/* Refresh for old proposals */}
      {proposals.length > 0 && !proposals[0]?.fame_tier && (
        <button onClick={async () => {
          setLoading('refresh');
          try { await api.post(`/films/${film.id}/refresh-proposals`); onRefresh(); toast({ title: 'Proposte aggiornate!' }); } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
          setLoading('');
        }} disabled={loading === 'refresh'}
          className="w-full text-[8px] py-1.5 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500/20 transition-colors" data-testid="refresh-proposals-btn">
          {loading === 'refresh' ? '...' : 'Aggiorna Proposte (formato nuovo)'}
        </button>
      )}

      {/* Tab Proposals */}
      <div className="space-y-1.5 max-h-80 overflow-y-auto" data-testid="proposals-list">
        {tabFull && <p className="text-[9px] text-amber-400 text-center py-2 bg-amber-500/5 rounded-lg border border-amber-500/15">Slot pieno! Max raggiunto per {tabInfo?.label}</p>}
        {tabProposals.map((p) => {
          const isExpanded = expandedProposal === p._idx;
          const fameStyle = FAME_COLORS[p.fame_tier] || FAME_COLORS.sconosciuto;
          return (
            <div key={p._idx} className={`rounded-lg border transition-colors ${p.is_star ? 'bg-yellow-500/5 border-yellow-500/15' : 'bg-gray-800/30 border-gray-700/50'}`}>
              {/* Header row */}
              <div className="flex items-center gap-2 p-2 cursor-pointer" onClick={() => setExpandedProposal(isExpanded ? null : p._idx)}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${
                  p.is_star ? 'bg-yellow-500/20 border-2 border-yellow-500/40 text-yellow-400' :
                  p.stars >= 4 ? 'bg-purple-500/15 border border-purple-500/30 text-purple-400' :
                  'bg-gray-700 border border-gray-600 text-gray-300'}`}>
                  {(p.name || '?')[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <p className="text-[10px] font-medium text-white truncate">{p.name}</p>
                    <span className={`text-[6px] px-1 py-0.5 rounded font-bold ${fameStyle}`}>{p.fame_tier || '?'}</span>
                  </div>
                  <p className="text-[7px] text-gray-500">
                    <span className={`${(p.gender||'').toLowerCase() === 'male' || p.gender === 'M' ? 'text-blue-400' : (p.gender||'').toLowerCase() === 'female' || p.gender === 'F' ? 'text-pink-400' : 'text-gray-400'}`}>{genderIcon(p.gender)}</span> {p.age}a • {p.nationality} • <span className="text-yellow-400">{starsStr(p.stars)}</span>{p.imdb_rating ? ` • IMDb ${(p.imdb_rating/10).toFixed(1)}` : ''} • ${(p.cost||0).toLocaleString()}
                  </p>
                </div>
                <ChevronRight className={`w-3 h-3 text-gray-600 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </div>

              {/* Expanded: 8 skill bars + select button */}
              {isExpanded && (
                <div className="px-2 pb-2 space-y-1.5 border-t border-gray-700/30 pt-1.5">
                  {/* Strengths / Weaknesses */}
                  <div className="flex flex-wrap gap-1">
                    {p.strengths?.map((s, j) => <span key={j} className="text-[7px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{s}</span>)}
                    {p.weaknesses?.map((w, j) => <span key={j} className="text-[7px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">{w}</span>)}
                  </div>
                  {p.role_affinity && <p className="text-[8px] text-violet-400">Tipo: {p.role_affinity}</p>}
                  {p.genre_affinity?.length > 0 && <p className="text-[8px] text-cyan-400">Affinita genere: {p.genre_affinity.join(', ')}</p>}
                  {p.worked_with_us && <p className="text-[8px] text-green-400">Ha gia lavorato con noi</p>}

                  {/* 8 Skill bars */}
                  <div className="space-y-0.5">
                    {Object.entries(p.skills || {}).map(([k, v]) => <SkillBar key={k} name={k} value={v} />)}
                  </div>

                  {/* Role selection for actors */}
                  {activeTab === 'actor' && !tabFull && (
                    <div className="flex items-center gap-2 mt-1" data-testid={`role-select-${p._idx}`}>
                      <span className="text-[8px] text-gray-400 flex-shrink-0">Ruolo:</span>
                      <select
                        value={selectedRole[p._idx] || 'protagonista'}
                        onChange={(e) => { e.stopPropagation(); setSelectedRole(prev => ({...prev, [p._idx]: e.target.value})); }}
                        onClick={(e) => e.stopPropagation()}
                        className="flex-1 text-[9px] py-1.5 px-2 rounded-lg bg-gray-800 border border-violet-500/30 text-violet-300 font-bold appearance-none"
                      >
                        {ACTOR_ROLES.map(r => <option key={r.key} value={r.key}>{r.label}</option>)}
                      </select>
                    </div>
                  )}

                  {/* Select button */}
                  {!tabFull && (
                    <button onClick={(e) => { e.stopPropagation(); selectCast(p._idx); }}
                      disabled={loading.startsWith('s_')}
                      className="w-full text-[9px] py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/25 text-cyan-400 hover:bg-cyan-500/20 transition-colors disabled:opacity-40 font-bold mt-1"
                      data-testid={`select-${p._idx}`}>
                      {activeTab === 'actor' ? `Ingaggia come ${(selectedRole[p._idx] || 'protagonista').replace('_', '-')}` : `Ingaggia come ${tabInfo?.label?.replace(/i$/, 'a').replace(/ori$/, 'ore')}`}
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
        {tabProposals.length === 0 && <p className="text-[9px] text-gray-600 italic text-center py-4">Nessuna proposta {tabInfo?.label?.toLowerCase()}</p>}
      </div>

      {/* Auto-Complete Cast */}
      <button onClick={async () => {
        setLoading('autocast');
        try {
          const r = await api.post(`/films/${film.id}/auto-cast`);
          toast({ title: 'Cast completato automaticamente!' });
          onRefresh();
        } catch (e) { toast({ title: e.message || 'Errore', variant: 'destructive' }); }
        setLoading('');
      }} disabled={loading === 'autocast' || canLock}
        className="w-full text-[10px] py-2.5 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-400 hover:bg-amber-500/20 transition-colors disabled:opacity-30 font-bold mb-1.5" data-testid="auto-cast-btn">
        {loading === 'autocast' ? 'Completamento...' : (<>Completa Cast Auto — {isGuest ? <><s className="opacity-50">$2M + 10cr</s> GRATIS</> : '$2M + 10cr'}</>)}
      </button>

      {/* Lock */}
      <button onClick={lockCast} disabled={!canLock || loading === 'lock'}
        className="w-full text-[10px] py-2.5 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/25 transition-colors disabled:opacity-30 font-bold" data-testid="lock-cast-btn">
        {loading === 'lock' ? '...' : 'Conferma Cast e Procedi'}
      </button>
      {!canLock && <p className="text-[8px] text-gray-600 text-center">{isAnime ? 'Serve: 1 regista + 1 disegnatore minimo' : 'Serve: 1 regista + 2 attori minimo'}</p>}
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
  const [showCiakIntro, setShowCiakIntro] = useState(false);

  useEffect(() => {
    api.get(`/films/${film.id}/prep-options`).then(setOptions).catch(() => {});
  }, [film.id]);

  const saveAndProceed = async () => {
    setLoading('save');
    try {
      await api.post(`/films/${film.id}/save-prep`, { equipment, cgi_packages: cgi, vfx_packages: vfx, extras_count: extras });
      setLoading('');
      // Show cinematic intro, then start CIAK at the end
      setShowCiakIntro(true);
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); setLoading(''); }
  };

  const onIntroComplete = async () => {
    setShowCiakIntro(false);
    try {
      await api.post(`/films/${film.id}/start-ciak`);
      onRefresh();
      toast({ title: 'CIAK! Riprese avviate!' });
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
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

      <button onClick={saveAndProceed} disabled={loading === 'save' || showCiakIntro}
        className="w-full text-[10px] py-2.5 rounded-lg bg-blue-500/15 border border-blue-500/30 text-blue-400 hover:bg-blue-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="start-ciak-btn">
        {loading === 'save' ? 'Salvataggio...' : showCiakIntro ? 'Avvio riprese...' : 'Salva e Avvia Riprese'}
      </button>
      {showCiakIntro && <CiakIntroOverlay onComplete={onIntroComplete} />}
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

  // Matrix orange effect for CIAK
  const ciakCanvasRef = useRef(null);
  const isShooting = !done;

  useEffect(() => {
    if (!isShooting) return;
    const canvas = ciakCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const resize = () => { canvas.width = canvas.parentElement.offsetWidth; canvas.height = canvas.parentElement.offsetHeight; };
    resize();
    window.addEventListener('resize', resize);
    const letters = 'CIAKACTIONRIPRESE!';
    const fontSize = 12;
    const columns = Math.floor(canvas.width / fontSize);
    const drops = Array(columns).fill(1);
    const draw = () => {
      ctx.fillStyle = 'rgba(0,0,0,0.05)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.shadowColor = '#ff8c00';
      ctx.shadowBlur = 4;
      ctx.fillStyle = '#ff8c00';
      ctx.font = `bold ${fontSize}px monospace`;
      for (let i = 0; i < drops.length; i++) {
        const text = letters[Math.floor(Math.random() * letters.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    };
    const interval = setInterval(draw, 40);
    return () => { clearInterval(interval); window.removeEventListener('resize', resize); };
  }, [isShooting]);

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
      <div className="relative p-4 rounded-lg bg-red-500/5 border border-red-500/20 text-center space-y-2 overflow-hidden">
        {isShooting && (
          <canvas ref={ciakCanvasRef} className="absolute inset-0 z-0 opacity-[0.18] pointer-events-none" data-testid="ciak-matrix-canvas" />
        )}
        <Clapperboard className="relative z-10 w-8 h-8 text-red-400 mx-auto" />
        <p className="relative z-10 text-[9px] text-gray-500 uppercase">Riprese in corso</p>
        <p className="relative z-10 text-xl font-bold text-red-400 font-mono">{remaining}</p>
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

      {!done && <SpeedupPanel film={film} onRefresh={onRefresh} toast={toast} />}
      {done && (
        <button onClick={completeCiak} disabled={loading === 'complete'}
          className="w-full text-[10px] py-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="complete-ciak-btn">
          {loading === 'complete' ? '...' : 'Completa Riprese'}
        </button>
      )}
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
      {!done && <SpeedupPanel film={film} onRefresh={onRefresh} toast={toast} />}
      {done && (
        <button onClick={complete} disabled={loading === 'complete'}
          className="w-full text-[10px] py-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="complete-finalcut-btn">
          {loading === 'complete' ? '...' : 'Completa Final Cut'}
        </button>
      )}
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
  const [showReleaseOverlay, setShowReleaseOverlay] = useState(false);
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState('');
  const [duration, setDuration] = useState(24);
  const [cityTips, setCityTips] = useState(null);
  const state = film.pipeline_state;
  const timers = film.pipeline_timers || {};
  const { remaining, done } = useCountdown(timers.premiere_end);

  useEffect(() => {
    if (state === 'premiere_setup') {
      api.get(`/films/${film.id}/premiere-cities`).then(d => setCities(d.cities || [])).catch(() => {});
      // Fetch Velion city tips for LaPrima
      const BACKEND = process.env.REACT_APP_BACKEND_URL || '';
      const token = localStorage.getItem('cineworld_token');
      fetch(`${BACKEND}/api/city-tastes/la-prima-tips/${film.id}`, { headers: { 'Authorization': `Bearer ${token}` } })
        .then(r => r.json()).then(d => setCityTips(d)).catch(() => {});
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
      await api.post(`/films/${film.id}/complete-premiere`);
      setShowReleaseOverlay(true);
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); setLoading(''); }
  };

  const onPremiereOverlayDone = () => {
    setShowReleaseOverlay(false);
    setLoading('');
    api.post(`/films/${film.id}/mark-release-played`).catch(() => {});
    onRefresh();
    toast({ title: `Premiere completata!` });
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
          {/* Velion City Intelligence for LaPrima */}
          {cityTips?.tips?.length > 0 && selectedCity && (
            <div className="p-2 bg-gradient-to-br from-yellow-500/5 to-cyan-500/5 border border-yellow-500/15 rounded-lg">
              <p className="text-[9px] text-yellow-400 font-bold mb-1">Velion — Consigli Premiere</p>
              {cityTips.intro && <p className="text-[8px] text-gray-400 mb-1.5">{cityTips.intro}</p>}
              {cityTips.tips.filter(t => t.name === selectedCity).map(tip => {
                const colors = { fermento: 'text-green-400', forte: 'text-emerald-400', discreto: 'text-yellow-400', tiepido: 'text-orange-400', freddo: 'text-red-400' };
                return (
                  <div key={tip.city_id} className="flex items-start gap-2">
                    <span className={`text-[9px] font-bold ${colors[tip.level] || 'text-gray-400'}`}>{tip.name}:</span>
                    <p className="text-[8px] text-gray-400">{tip.phrase}</p>
                  </div>
                );
              })}
            </div>
          )}
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
          {done && (
            <button onClick={completePremiere} disabled={loading === 'complete'}
              className="w-full text-[10px] py-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 font-bold" data-testid="complete-premiere-btn">
              {loading === 'complete' ? '...' : 'Completa Premiere'}
            </button>
          )}
        </div>
      )}
      {showReleaseOverlay && (
        <CinematicReleaseOverlay
          film={film} releaseType="premiere"
          onComplete={onPremiereOverlayDone}
        />
      )}
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FASE 9 — USCITA
// ═══════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════
//  FASE 9 — USCITA (Release Scheduling + Zones)
// ═══════════════════════════════════════════════════════════════


// ═══════════════════════════════════════════════════════════════
//  SERIE/ANIME — Episode Manager (Board, post-release) — Netflix-Style
// ═══════════════════════════════════════════════════════════════

const EP_TYPE_STYLES = {
  normal:        { accent: 'cyan',   accentBg: 'bg-cyan-500/15', accentBorder: 'border-cyan-500/50', accentRing: 'ring-cyan-500/20', accentText: 'text-cyan-400', accentBtnBg: 'bg-cyan-500/20', accentBtnHover: 'hover:bg-cyan-500/30', accentBar: 'bg-cyan-500', icon: Play,       label: 'Episodio' },
  peak:          { accent: 'amber',  accentBg: 'bg-amber-500/15', accentBorder: 'border-amber-500/50', accentRing: 'ring-amber-500/20', accentText: 'text-amber-400', accentBtnBg: 'bg-amber-500/20', accentBtnHover: 'hover:bg-amber-500/30', accentBar: 'bg-amber-500', icon: Zap,        label: 'Episodio Esplosivo' },
  filler:        { accent: 'gray',   accentBg: 'bg-gray-500/15', accentBorder: 'border-gray-500/50', accentRing: 'ring-gray-500/20', accentText: 'text-gray-400', accentBtnBg: 'bg-gray-500/20', accentBtnHover: 'hover:bg-gray-500/30', accentBar: 'bg-gray-500', icon: Clock,      label: 'Intermezzo' },
  plot_twist:    { accent: 'purple', accentBg: 'bg-purple-500/15', accentBorder: 'border-purple-500/50', accentRing: 'ring-purple-500/20', accentText: 'text-purple-400', accentBtnBg: 'bg-purple-500/20', accentBtnHover: 'hover:bg-purple-500/30', accentBar: 'bg-purple-500', icon: Sparkles,   label: 'Colpo di Scena' },
  season_finale: { accent: 'red',    accentBg: 'bg-red-500/15', accentBorder: 'border-red-500/50', accentRing: 'ring-red-500/20', accentText: 'text-red-400', accentBtnBg: 'bg-red-500/20', accentBtnHover: 'hover:bg-red-500/30', accentBar: 'bg-red-500', icon: Award,      label: 'Finale di Stagione' },
};

const EpisodeCard = ({ ep, isCurrent, onWatch }) => {
  const isReleased = ep.status === 'released';
  const isWatched = ep.watched;
  const typeStyle = EP_TYPE_STYLES[ep.episode_type] || EP_TYPE_STYLES.normal;
  const TypeIcon = typeStyle.icon;

  return (
    <div
      className={`relative rounded-lg border transition-all duration-300 overflow-hidden ${
        isCurrent && isReleased && !isWatched
          ? `${typeStyle.accentBorder} ${typeStyle.accentBg} ring-1 ${typeStyle.accentRing}`
          : isWatched
            ? 'border-emerald-500/20 bg-emerald-500/5'
            : isReleased
              ? 'border-white/10 bg-white/[0.02] hover:border-white/20'
              : 'border-white/5 bg-black/20 opacity-50'
      }`}
      data-testid={`ep-card-${ep.number}`}
    >
      <div className="p-3">
        <div className="flex items-start gap-3">
          {/* Episode Number */}
          <div className={`flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center text-xs font-black ${
            isWatched ? 'bg-emerald-500/20 text-emerald-400'
              : isReleased ? `${typeStyle.accentBg} ${typeStyle.accentText}`
              : 'bg-gray-800 text-gray-600'
          }`}>
            {isWatched ? <Check className="w-3.5 h-3.5" /> : ep.number}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-0.5">
              <span className="text-[10px] font-bold text-white truncate">{ep.title || `Episodio ${ep.number}`}</span>
              {ep.episode_type && ep.episode_type !== 'normal' && (
                <TypeIcon className={`w-3 h-3 flex-shrink-0 ${typeStyle.accentText}`} />
              )}
            </div>
            <p className="text-[9px] text-gray-500 leading-relaxed line-clamp-2">
              {ep.plot || 'Trama non disponibile.'}
            </p>
            {/* Stats row */}
            <div className="flex items-center gap-3 mt-1.5">
              {isReleased && (
                <span className="text-[8px] text-gray-600">
                  {new Date(ep.release_at || ep.released_at).toLocaleDateString('it-IT', { day: '2-digit', month: 'short' })}
                </span>
              )}
              {!isReleased && ep.release_at && (
                <span className="text-[8px] text-gray-600 flex items-center gap-0.5">
                  <Lock className="w-2.5 h-2.5" />
                  {new Date(ep.release_at).toLocaleDateString('it-IT', { day: '2-digit', month: 'short' })}
                </span>
              )}
              {isWatched && ep.rating && (
                <span className={`text-[8px] font-bold ${
                  ep.rating >= 70 ? 'text-emerald-400' : ep.rating >= 45 ? 'text-amber-400' : 'text-red-400'
                }`}>
                  {ep.rating}/100
                </span>
              )}
              {isWatched && ep.audience_count && (
                <span className="text-[8px] text-gray-500">
                  {ep.audience_count >= 1000 ? `${(ep.audience_count / 1000).toFixed(1)}k` : ep.audience_count} spettatori
                </span>
              )}
            </div>
          </div>

          {/* Action */}
          <div className="flex-shrink-0">
            {isReleased && !isWatched && (
              <button onClick={() => onWatch(ep.number)}
                className={`w-8 h-8 rounded-full flex items-center justify-center ${typeStyle.accentBtnBg} ${typeStyle.accentText} ${typeStyle.accentBtnHover} transition-colors`}
                data-testid={`watch-ep-${ep.number}`}
                title="Guarda episodio">
                <PlayCircle className="w-4 h-4" />
              </button>
            )}
            {isWatched && (
              <div className="w-8 h-8 rounded-full flex items-center justify-center bg-emerald-500/10">
                <Eye className="w-3.5 h-3.5 text-emerald-500/50" />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Current episode indicator bar */}
      {isCurrent && isReleased && !isWatched && (
        <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${typeStyle.accentBar}`} />
      )}
    </div>
  );
};

const EpisodeManager = ({ film, onRefresh, toast }) => {
  const [mode, setMode] = useState(film.episode_release_mode || null);
  const [episodes, setEpisodes] = useState([]);
  const [total, setTotal] = useState(0);
  const [released, setReleased] = useState(0);
  const [allReleased, setAllReleased] = useState(false);
  const [currentEp, setCurrentEp] = useState(1);
  const [stats, setStats] = useState(null);
  const [generated, setGenerated] = useState(false);
  const [choosing, setChoosing] = useState(false);
  const [loading, setLoading] = useState('');
  const [watchLoading, setWatchLoading] = useState(null);
  const [seasonLoading, setSeasonLoading] = useState(false);
  const [newSeasonEp, setNewSeasonEp] = useState(12);
  const [enrichLoading, setEnrichLoading] = useState(false);

  const loadEpisodes = useCallback(async () => {
    try {
      const res = await api.get(`/films/${film.id}/episodes`);
      setEpisodes(res.episodes || []);
      setTotal(res.total || 0);
      setReleased(res.released || 0);
      setAllReleased(res.all_released || false);
      setCurrentEp(res.current_episode || 1);
      setMode(res.mode || null);
      setStats(res.stats || null);
      setGenerated(res.episodes_generated || false);
    } catch (e) {}
  }, [film.id]);

  useEffect(() => { loadEpisodes(); }, [loadEpisodes]);

  const chooseMode = async (m) => {
    setLoading(m);
    try {
      await api.post(`/films/${film.id}/set-release-mode`, { mode: m });
      toast({ title: `Modalita ${m === 'binge' ? 'Binge' : m === 'daily' ? 'Giornaliero' : 'Settimanale'} attivata!` });
      await loadEpisodes();
      setChoosing(false);
    } catch (e) {
      toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' });
    }
    setLoading('');
  };

  const watchEpisode = async (epNum) => {
    setWatchLoading(epNum);
    try {
      const res = await api.post(`/films/${film.id}/episodes/${epNum}/watch`);
      const ep = res.episode;
      const ratingMsg = res.rating >= 70 ? 'Ottimo!' : res.rating >= 45 ? 'Discreto' : 'Deludente';
      toast({
        title: `Ep${epNum}: "${ep.title}" — ${ratingMsg} (${res.rating}/100)`,
        description: `Audience: ${(res.audience || 0).toLocaleString()} | Hype: ${res.hype_change >= 0 ? '+' : ''}${res.hype_change}${
          res.all_watched ? ' | Serie completata!' : ''
        }`,
      });
      if (res.series_final_score) {
        setTimeout(() => {
          toast({ title: `Valutazione Finale Serie: ${res.series_final_score}/100` });
        }, 1500);
      }
      await loadEpisodes();
    } catch (e) {
      toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' });
    }
    setWatchLoading(null);
  };

  const enrichEpisodes = async () => {
    setEnrichLoading(true);
    try {
      await api.post(`/films/${film.id}/episodes/enrich`);
      toast({ title: 'Episodi arricchiti con titoli e trame!' });
      await loadEpisodes();
    } catch (e) {
      toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' });
    }
    setEnrichLoading(false);
  };

  const createSeason = async () => {
    setSeasonLoading(true);
    try {
      const res = await api.post(`/films/${film.id}/new-season`, { episode_count: newSeasonEp });
      toast({
        title: `Stagione ${res.season} creata!`,
        description: res.departed_actors?.length > 0
          ? `${res.departed_actors.length} membri hanno lasciato il progetto`
          : `Cast confermato. Bonus: ${res.season_bonus > 0 ? '+' : ''}${res.season_bonus}`,
      });
      onRefresh();
    } catch (e) {
      toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' });
    }
    setSeasonLoading(false);
  };

  const modeLabels = { binge: 'Binge', daily: 'Giornaliero', weekly: 'Settimanale' };
  const modeIcons = { binge: Zap, daily: Clock, weekly: Timer };

  // ─── No mode chosen → show selector ───
  if (!mode) {
    return (
      <div className="mt-3 p-3 rounded-lg bg-[#0a0a0f] border border-cyan-500/15 space-y-2" data-testid="episode-mode-selector">
        <div className="flex items-center gap-2 mb-1">
          <Tv className="w-3.5 h-3.5 text-cyan-400" />
          <p className="text-[9px] text-cyan-400 font-bold uppercase tracking-wider">Distribuzione Episodi</p>
        </div>
        <p className="text-[8px] text-gray-400">
          {film.episode_count || '?'} episodi — scegli come distribuirli. La scelta e definitiva.
        </p>
        {!choosing ? (
          <button onClick={() => setChoosing(true)}
            className="w-full py-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/25 text-cyan-400 text-[10px] font-bold hover:bg-cyan-500/20 transition-colors"
            data-testid="choose-mode-btn">
            Scegli Modalita di Rilascio
          </button>
        ) : (
          <div className="space-y-1.5">
            {[
              { id: 'binge', label: 'Binge', desc: 'Tutti gli episodi subito — ideale per maratone', icon: Zap },
              { id: 'daily', label: 'Giornaliero', desc: '1 episodio al giorno — hype costante', icon: Clock },
              { id: 'weekly', label: 'Settimanale', desc: '1 episodio ogni 7 giorni — suspense massima', icon: Timer },
            ].map(m => (
              <button key={m.id} onClick={() => chooseMode(m.id)}
                disabled={loading !== ''}
                className="w-full p-2.5 rounded-lg border border-gray-800 hover:border-cyan-500/30 text-left flex items-center gap-3 transition-all active:scale-[0.98]"
                data-testid={`mode-${m.id}`}>
                <m.icon className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-[10px] font-bold text-white">{m.label}</p>
                  <p className="text-[8px] text-gray-500">{m.desc}</p>
                </div>
                {loading === m.id && <span className="text-[8px] text-cyan-400 animate-pulse">...</span>}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─── Mode chosen → Netflix-style episode list ───
  const ModeIcon = modeIcons[mode] || Clock;
  const pct = total > 0 ? Math.round((released / total) * 100) : 0;
  const watchedCount = episodes.filter(e => e.watched).length;
  const watchPct = total > 0 ? Math.round((watchedCount / total) * 100) : 0;
  const needsEnrich = episodes.length > 0 && !episodes[0].title && !generated;

  return (
    <div className="mt-3 space-y-2" data-testid="episode-manager">
      {/* Header card with progress */}
      <div className="p-3 rounded-lg bg-[#0a0a0f] border border-white/10">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ModeIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[9px] text-cyan-400 font-bold uppercase tracking-wider">
              S{film.season_number || 1} — {modeLabels[mode]}
            </span>
          </div>
          <span className="text-[9px] text-gray-400 font-mono">{released}/{total} usciti</span>
        </div>

        {/* Release progress bar */}
        <div className="space-y-1">
          <div className="w-full h-1.5 bg-gray-800/80 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${pct}%` }} />
          </div>
          {/* Watch progress bar */}
          <div className="w-full h-1 bg-gray-800/50 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${watchPct}%` }} />
          </div>
          <div className="flex justify-between text-[7px] text-gray-600">
            <span>{pct}% rilasciati</span>
            <span>{watchPct}% visti</span>
          </div>
        </div>

        {/* Stats row */}
        {stats && (stats.avg_rating || stats.total_audience > 0) && (
          <div className="flex gap-3 mt-2 pt-2 border-t border-white/5">
            {stats.avg_rating && (
              <div className="text-center">
                <div className={`text-xs font-black ${stats.avg_rating >= 70 ? 'text-emerald-400' : stats.avg_rating >= 45 ? 'text-amber-400' : 'text-red-400'}`}>
                  {stats.avg_rating}
                </div>
                <div className="text-[7px] text-gray-600">Rating Medio</div>
              </div>
            )}
            {stats.total_audience > 0 && (
              <div className="text-center">
                <div className="text-xs font-black text-white">
                  {stats.total_audience >= 1000000 ? `${(stats.total_audience / 1000000).toFixed(1)}M` :
                   stats.total_audience >= 1000 ? `${(stats.total_audience / 1000).toFixed(1)}k` : stats.total_audience}
                </div>
                <div className="text-[7px] text-gray-600">Audience Tot.</div>
              </div>
            )}
            {stats.total_hype !== 0 && (
              <div className="text-center">
                <div className={`text-xs font-black ${stats.total_hype >= 0 ? 'text-cyan-400' : 'text-red-400'}`}>
                  {stats.total_hype >= 0 ? '+' : ''}{stats.total_hype}
                </div>
                <div className="text-[7px] text-gray-600">Hype</div>
              </div>
            )}
            <div className="text-center">
              <div className="text-xs font-black text-white">{stats.watched}/{total}</div>
              <div className="text-[7px] text-gray-600">Visti</div>
            </div>
          </div>
        )}
      </div>

      {/* Enrich button for old-format episodes */}
      {needsEnrich && (
        <button onClick={enrichEpisodes} disabled={enrichLoading}
          className="w-full py-2 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-400 text-[9px] font-bold hover:bg-amber-500/20 transition-colors disabled:opacity-30"
          data-testid="enrich-episodes-btn">
          {enrichLoading ? 'Generazione titoli...' : 'Genera Titoli & Trame Episodi'}
        </button>
      )}

      {/* Episode list */}
      <div className="space-y-1.5" data-testid="episode-list">
        {episodes.map(ep => (
          <EpisodeCard key={ep.number} ep={ep} isCurrent={ep.number === currentEp}
            onWatch={watchEpisode} />
        ))}
      </div>

      {/* New Season */}
      {allReleased && (
        <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/15 space-y-2" data-testid="new-season-section">
          <p className="text-[9px] text-amber-400 font-bold uppercase tracking-wider">Nuova Stagione</p>
          <p className="text-[8px] text-gray-400">
            Tutti gli episodi rilasciati! Crea la Stagione {(film.season_number || 1) + 1}.
          </p>
          <div>
            <label className="text-[7px] text-gray-500 uppercase">Episodi nuova stagione ({newSeasonEp})</label>
            <input type="range" min={8} max={24} value={newSeasonEp}
              onChange={e => setNewSeasonEp(parseInt(e.target.value))}
              className="w-full h-1 bg-gray-800 rounded-full appearance-none cursor-pointer accent-amber-500"
              data-testid="new-season-ep-slider"
            />
          </div>
          <button onClick={createSeason} disabled={seasonLoading}
            className="w-full py-2 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[10px] font-bold hover:bg-amber-500/25 transition-colors disabled:opacity-30"
            data-testid="create-season-btn">
            {seasonLoading ? 'Creazione...' : `Crea Stagione ${(film.season_number || 1) + 1}`}
          </button>
        </div>
      )}
    </div>
  );
};


const UscitaPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState('');
  const [result, setResult] = useState(null);
  const [showReleaseOverlay, setShowReleaseOverlay] = useState(false);
  const [zones, setZones] = useState([]);
  const [dateOptions, setDateOptions] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedZones, setSelectedZones] = useState([]);
  const [expandedContinent, setExpandedContinent] = useState(null);
  const [scheduled, setScheduled] = useState(film.release_schedule || null);
  const [epCount, setEpCount] = useState(film.episode_count || 12);
  const [epSaved, setEpSaved] = useState(!!film.episode_count);
  const [cityTips, setCityTips] = useState(null);
  const [theaterWeeks, setTheaterWeeks] = useState(film.theater_weeks || 3);
  const state = film.pipeline_state;
  const canRelease = state === 'release_pending';
  const canSchedule = state === 'premiere_live' || state === 'release_pending';
  const isSeries = film.content_type === 'serie_tv' || film.content_type === 'anime';

  useEffect(() => {
    api.get('/release-zones').then(r => {
      setZones(r?.zones || []);
      setDateOptions(r?.dates || []);
    }).catch(() => {});
    // Fetch Velion city tips
    const BACKEND = process.env.REACT_APP_BACKEND_URL || '';
    const token = localStorage.getItem('cineworld_token');
    fetch(`${BACKEND}/api/city-tastes/tips/${film.id}`, { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json()).then(d => setCityTips(d)).catch(() => {});
  }, [film.id]);

  useEffect(() => {
    if (film.release_schedule) {
      setScheduled(film.release_schedule);
      setSelectedDate(film.release_schedule.date_option);
      setSelectedZones(film.release_schedule.zones || []);
    }
  }, [film.release_schedule]);

  const hasWorld = selectedZones.includes('world');
  const activeZones = hasWorld ? ['world'] : selectedZones;
  const totalFunds = activeZones.reduce((s, z) => s + (zones.find(x => x.id === z)?.funds || 0), 0);
  const totalCp = activeZones.reduce((s, z) => s + (zones.find(x => x.id === z)?.cp || 0), 0);
  const dateInfo = dateOptions.find(d => d.id === selectedDate);

  const toggleZone = (zid) => {
    if (zid === 'world') {
      setSelectedZones(prev => prev.includes('world') ? [] : ['world']);
    } else {
      setSelectedZones(prev => {
        const without = prev.filter(z => z !== 'world' && z !== zid);
        return prev.includes(zid) ? without : [...without, zid];
      });
    }
    if (!velionZoneTip) setVelionZoneTip(true);
  };

  const continents = {};
  zones.filter(z => z.id !== 'world').forEach(z => {
    if (!continents[z.continent]) continents[z.continent] = [];
    continents[z.continent].push(z);
  });
  const worldZone = zones.find(z => z.id === 'world');

  const [velionDateTip, setVelionDateTip] = useState(false);
  const [velionZoneTip, setVelionZoneTip] = useState(false);

  // Show Velion tips on first date selection
  const handleDateSelect = (dateId) => {
    setSelectedDate(dateId);
    if (!velionDateTip) setVelionDateTip(true);
  };

  const scheduleRelease = async () => {
    if (!selectedDate || activeZones.length === 0) {
      toast({ title: 'Seleziona data e almeno una zona', variant: 'destructive' }); return;
    }
    setLoading('schedule');
    try {
      const res = await api.post(`/films/${film.id}/schedule-release`, {
        date_option: selectedDate, zones: activeZones, theater_weeks: theaterWeeks,
      });
      setScheduled(res.data?.schedule || res.data);
      toast({ title: `Distribuzione programmata!` });
      onRefresh();
    } catch (e) { toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' }); }
    finally { setLoading(''); }
  };

  const release = async () => {
    setLoading('release');
    try {
      const res = await api.post(`/films/${film.id}/release`);
      if (res.data?.scheduled) {
        toast({ title: `Film programmato per uscita` });
        onRefresh(); setLoading('');
      } else {
        setResult(res.data);
        if (!film.release_sequence_played) {
          setShowReleaseOverlay(true);
        } else {
          setLoading('');
          onRefresh();
          toast({ title: `${film.title} rilasciato! Quality: ${res.data?.quality_score || '?'}` });
        }
      }
    } catch (e) { toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' }); setLoading(''); }
  };

  const onCinemaOverlayDone = () => {
    setShowReleaseOverlay(false);
    setLoading('');
    api.post(`/films/${film.id}/mark-release-played`).catch(() => {});
    onRefresh();
    toast({ title: `${film.title} rilasciato! Quality: ${result?.quality_score || '?'}` });
  };

  const tierColors = { masterpiece: 'text-yellow-400', excellent: 'text-emerald-400', good: 'text-blue-400', mediocre: 'text-orange-400', bad: 'text-red-400' };

  // If already released/completed, show results
  if (result || state === 'completed' || state === 'released') {
    return (
      <PhaseWrapper title="Uscita al Cinema" subtitle="Il momento della verita" icon={Ticket} color="emerald">
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

          {/* ═══ THEATER STATS — In Sala ═══ */}
          {/* Theater stats temporarily disabled */}

          {/* ═══ SERIE/ANIME — Episodi + Stagioni ═══ */}
          {(film.content_type === 'serie_tv' || film.content_type === 'anime') && (
            <EpisodeManager film={film} onRefresh={onRefresh} toast={toast} />
          )}
        </div>
        {showReleaseOverlay && (
          <CinematicReleaseOverlay
            film={film} releaseType="cinema"
            onComplete={onCinemaOverlayDone}
          />
        )}
      </PhaseWrapper>
    );
  }

  // If coming_soon_scheduled, show waiting state
  if (state === 'coming_soon_scheduled') {
    return (
      <PhaseWrapper title="Uscita Programmata" subtitle="In attesa del giorno di uscita" icon={Ticket} color="emerald">
        <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-center space-y-2">
          <Clock className="w-8 h-8 text-emerald-400 mx-auto" />
          <p className="text-sm font-bold text-white">Film in Prossimamente</p>
          <p className="text-[10px] text-gray-400">Uscira tra {scheduled?.days || '?'} giorni</p>
          {scheduled?.zone_names && (
            <p className="text-[9px] text-emerald-400">Zone: {scheduled.zone_names.join(', ')}</p>
          )}
        </div>
      </PhaseWrapper>
    );
  }

  return (
    <PhaseWrapper title="Distribuzione" subtitle={state === 'premiere_live' ? 'Programma durante La Prima' : 'Scegli come distribuire'} icon={Ticket} color="emerald">
      <div className="space-y-3">
        {state === 'premiere_live' && (
          <div className="p-2 rounded-lg bg-yellow-500/5 border border-yellow-500/15 text-center">
            <p className="text-[8px] text-yellow-400">La Prima in corso — programma la distribuzione, il rilascio partira al termine</p>
          </div>
        )}

        {/* Episode count — solo per Serie/Anime, prima del rilascio */}
        {isSeries && !epSaved && (
          <div className="p-3 rounded-lg bg-cyan-500/5 border border-cyan-500/15 space-y-2">
            <p className="text-[9px] text-cyan-400 font-bold uppercase">Episodi ({epCount})</p>
            <input type="range" min={8} max={24} value={epCount}
              onChange={e => setEpCount(parseInt(e.target.value))}
              className="w-full h-1.5 bg-gray-800 rounded-full appearance-none cursor-pointer accent-cyan-500"
              data-testid="ep-count-slider" />
            <div className="flex justify-between text-[7px]">
              <span className="text-gray-600">8</span>
              <span className="text-cyan-400/60">Qualita: {Math.round((1 - ((epCount - 8) * 0.02)) * 100)}%</span>
              <span className="text-gray-600">24</span>
            </div>
            <button onClick={async () => {
              try {
                await api.post(`/films/${film.id}/set-episodes`, { episode_count: epCount });
                setEpSaved(true);
                toast({ title: `${epCount} episodi confermati!` });
                onRefresh();
              } catch (e) { toast({ title: e.response?.data?.detail || 'Errore', variant: 'destructive' }); }
            }}
              className="w-full py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/25 text-cyan-400 text-[9px] font-bold hover:bg-cyan-500/20 transition-colors"
              data-testid="confirm-episodes-btn">
              Conferma {epCount} Episodi
            </button>
          </div>
        )}
        {isSeries && epSaved && (
          <div className="flex items-center gap-2 px-2 py-1 rounded bg-cyan-500/5 border border-cyan-500/10">
            <span className="text-[8px] text-cyan-400 font-bold">{film.episode_count || epCount} Episodi</span>
            <span className="text-[7px] text-gray-500">Qualita: {Math.round((1 - (((film.episode_count || epCount) - 8) * 0.02)) * 100)}%</span>
          </div>
        )}
        {/* Date Selection */}
        <div>
          <p className="text-[9px] text-gray-500 uppercase font-bold mb-1.5">Data di uscita</p>
          <div className="grid grid-cols-4 gap-1">
            {dateOptions.map(d => {
              const disabled = d.direct_only && isPremiere;
              const selected = selectedDate === d.id;
              return (
                <button key={d.id} disabled={disabled}
                  onClick={() => !disabled && handleDateSelect(d.id)}
                  className={`py-1.5 px-1 rounded-md text-[9px] font-bold border transition-all ${
                    disabled ? 'opacity-20 cursor-not-allowed border-gray-800 text-gray-600' :
                    selected ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' :
                    'border-gray-800 text-gray-400 hover:border-gray-600'
                  }`}
                  data-testid={`date-opt-${d.id}`}
                >
                  {d.label}
                </button>
              );
            })}
          </div>
          {/* Hype multiplier hidden from player */}
          {velionDateTip && (
            <div className="mt-1.5 px-2.5 py-2 bg-cyan-500/5 border border-cyan-500/15 rounded-lg">
              <p className="text-[9px] text-cyan-400 font-bold mb-0.5">Consiglio di Velion:</p>
              <p className="text-[8px] text-gray-400">Ogni data genera un diverso livello di aspettativa. Attesa pi\u00f9 lunga = pi\u00f9 hype ma anche pi\u00f9 rischio! "Immediato" \u00e8 sicuro ma senza bonus. Sperimenta!</p>
            </div>
          )}
        </div>

        {/* Zone Selection */}
        <div>
          <p className="text-[9px] text-gray-500 uppercase font-bold mb-1.5">Zone di distribuzione</p>

          {/* WORLD option */}
          {worldZone && (
            <button onClick={() => toggleZone('world')}
              className={`w-full mb-1.5 p-2 rounded-lg border text-left flex items-center justify-between transition-all ${
                hasWorld ? 'bg-emerald-500/10 border-emerald-500/30' : 'border-gray-800 hover:border-gray-600'
              }`} data-testid="zone-world">
              <div>
                <span className="text-[10px] font-bold text-white">Mondiale</span>
                <span className="text-[8px] text-gray-500 ml-2">Tutti i continenti</span>
              </div>
              <div className="text-right">
                <span className="text-[9px] text-green-400">${(worldZone.funds / 1000).toFixed(0)}K</span>
                <span className="text-[9px] text-cyan-400 ml-1">{worldZone.cp}CP</span>
              </div>
            </button>
          )}

          <div className="text-center text-[8px] text-gray-600 mb-1.5">— oppure seleziona zone —</div>

          {/* Continent groups */}
          <div className="space-y-1">
            {Object.entries(continents).map(([cont, czones]) => (
              <div key={cont} className={`rounded-lg border transition-all ${hasWorld ? 'opacity-30 pointer-events-none' : 'border-gray-800'}`}>
                <button onClick={() => setExpandedContinent(expandedContinent === cont ? null : cont)}
                  className="w-full p-2 flex items-center justify-between text-[10px]" data-testid={`continent-${cont}`}>
                  <span className="font-bold text-gray-300">{cont}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[8px] text-gray-500">{czones.filter(z => selectedZones.includes(z.id)).length}/{czones.length}</span>
                    <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform ${expandedContinent === cont ? 'rotate-180' : ''}`} />
                  </div>
                </button>
                {expandedContinent === cont && (
                  <div className="px-2 pb-2 space-y-1">
                    {czones.map(z => (
                      <button key={z.id} onClick={() => toggleZone(z.id)}
                        className={`w-full p-1.5 rounded-md flex items-center justify-between transition-all ${
                          selectedZones.includes(z.id) ? 'bg-emerald-500/10 border border-emerald-500/25' : 'border border-transparent hover:bg-white/5'
                        }`} data-testid={`zone-${z.id}`}>
                        <div>
                          <span className="text-[9px] font-semibold text-white">{z.name}</span>
                          <p className="text-[7px] text-gray-600">{z.countries}</p>
                        </div>
                        <div className="text-right shrink-0 ml-2">
                          <span className="text-[8px] text-green-400">${(z.funds / 1000).toFixed(0)}K</span>
                          <span className="text-[8px] text-cyan-400 ml-1">{z.cp}CP</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {velionZoneTip && (
          <div className="px-2.5 py-2 bg-cyan-500/5 border border-cyan-500/15 rounded-lg">
            <p className="text-[9px] text-cyan-400 font-bold mb-0.5">Consiglio di Velion:</p>
            <p className="text-[8px] text-gray-400">"Mondiale" raggiunge tutti ma costa di pi\u00f9. Seleziona zone specifiche per risparmiare e concentrare gli incassi dove il genere funziona meglio!</p>
          </div>
        )}

        {/* Velion City Intelligence */}
        {cityTips?.city_tips?.length > 0 && (selectedDate || selectedZones.length > 0) && (
          <div className="p-2.5 bg-gradient-to-br from-cyan-500/5 to-purple-500/5 border border-cyan-500/15 rounded-lg space-y-2">
            <p className="text-[9px] text-cyan-400 font-bold flex items-center gap-1">Velion — Intelligence Citt\u00e0</p>
            {cityTips.date_tips && (
              <div className="space-y-0.5">
                {cityTips.date_tips.map((t, i) => (
                  <p key={i} className="text-[8px] text-gray-400">{t}</p>
                ))}
              </div>
            )}
            <div className="space-y-1 mt-1">
              {cityTips.city_tips.slice(0, 5).map(tip => {
                const colors = { fermento: 'text-green-400', forte: 'text-emerald-400', discreto: 'text-yellow-400', tiepido: 'text-orange-400', freddo: 'text-red-400' };
                return (
                  <div key={tip.city_id} className="flex items-start gap-2">
                    <span className={`text-[8px] font-bold ${colors[tip.level] || 'text-gray-400'} flex-shrink-0 w-16`}>{tip.name}</span>
                    <p className="text-[7px] text-gray-500 leading-relaxed">{tip.phrase}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Cost Summary */}
        {(selectedDate && activeZones.length > 0) && (
          <div className="p-2 rounded-lg bg-gray-800/50 border border-gray-700/30 flex items-center justify-between">
            <span className="text-[9px] text-gray-400">Costo distribuzione:</span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-green-400">${totalFunds.toLocaleString()}</span>
              <span className="text-[10px] font-bold text-cyan-400">{totalCp} CP</span>
            </div>
          </div>
        )}

        {/* Already scheduled info */}
        {scheduled && (
          <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/15 text-center">
            <p className="text-[8px] text-emerald-400 font-bold">Distribuzione programmata</p>
            <p className="text-[8px] text-gray-400">{scheduled.date_label} — {scheduled.zone_names?.join(', ')}</p>
          </div>
        )}

        {/* Theater Duration Slider */}
        {canSchedule && !scheduled && (
          <div className="p-2 rounded-lg bg-gray-800/50 border border-gray-700/30">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] text-gray-400">Durata programmazione in sala</span>
              <span className="text-[11px] font-bold text-yellow-400">{theaterWeeks * 7} giorni</span>
            </div>
            <input type="range" min={1} max={4} step={1} value={theaterWeeks} onChange={e => setTheaterWeeks(+e.target.value)}
              className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-yellow-500" data-testid="theater-weeks-slider" />
            <div className="flex justify-between text-[7px] text-gray-600 mt-0.5">
              <span>7gg</span><span>14gg</span><span>21gg</span><span>28gg</span>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {canSchedule && !scheduled && (
          <button onClick={scheduleRelease} disabled={!selectedDate || activeZones.length === 0 || loading === 'schedule'}
            className="w-full text-[10px] py-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-30 font-bold"
            data-testid="schedule-release-btn">
            {loading === 'schedule' ? '...' : state === 'premiere_live' ? 'Programma Uscita' : 'Conferma Distribuzione'}
          </button>
        )}

        {canRelease && scheduled && (
          <button onClick={release} disabled={loading === 'release'}
            className="w-full text-sm py-3 rounded-lg bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30 text-emerald-300 hover:from-emerald-500/30 hover:to-green-500/30 transition-all disabled:opacity-50 font-bold"
            data-testid="release-btn">
            {loading === 'release' ? 'Calcolo qualita...' : 'RILASCIA NEI CINEMA'}
          </button>
        )}

        {state === 'premiere_live' && scheduled && (
          <p className="text-[8px] text-yellow-400/70 text-center">
            Il rilascio avverra automaticamente al termine de La Prima
          </p>
        )}
      </div>

      {showReleaseOverlay && (
        <CinematicReleaseOverlay
          film={film} releaseType="cinema"
          onComplete={onCinemaOverlayDone}
        />
      )}
    </PhaseWrapper>
  );
};

// ═══════════════════════════════════════════════════════════════
//  BOARD — card tratteggiata "Nuovo Film" + film in pipeline
// ═══════════════════════════════════════════════════════════════

const BOARD_HIDDEN = new Set(['released', 'completed', 'discarded']);

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
            <span className="text-[9px] font-bold text-gray-500 group-hover:text-amber-400 transition-colors block">Nuovo Progetto</span>
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
                  {f.content_type && f.content_type !== 'film' && (
                    <span className={`text-[6px] px-1 py-0 rounded font-bold ${
                      f.content_type === 'serie_tv' ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20' :
                      'bg-pink-500/15 text-pink-400 border border-pink-500/20'
                    }`}>{f.content_type === 'serie_tv' ? 'SERIE' : 'ANIME'}{f.season_number > 1 ? ` S${f.season_number}` : ''}</span>
                  )}
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
  const [viewingStep, setViewingStep] = useState(null);
  const [forceUscita, setForceUscita] = useState(false);
  const [showEditConfirm, setShowEditConfirm] = useState(null);
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
  const backToBoard = () => { setSelected(null); setView('board'); setForceUscita(false); loadFilms(); };

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

    // Allow USCITA scheduling during premiere_live
    if (forceUscita && st === 'premiere_live') return <UscitaPhase {...props} />;

    if (ui === 0 || st === 'draft' || st === 'idea') return <IdeaPhase {...props} />;
    if (ui === 1 || st === 'proposed' || st === 'hype_setup' || st === 'hype_live') return <HypePhase {...props} />;
    if (ui === 2 || st === 'casting_live') return <CastPhase {...props} />;
    if (ui === 3 || st === 'prep') return <PrepPhase {...props} />;
    if (ui === 4 || st === 'shooting') return <CiakPhase {...props} />;
    if (ui === 5 || st === 'postproduction') return <FinalCutPhase {...props} />;
    if (ui === 6 || st === 'sponsorship' || st === 'marketing') return <MarketingPhase {...props} />;
    if (ui === 7 || st === 'premiere_setup' || st === 'premiere_live') return <LaPrimaPhase {...props} />;
    if (ui === 8 || st === 'release_pending' || st === 'released' || st === 'completed' || st === 'coming_soon_scheduled') return <UscitaPhase {...props} />;
    return <div className="p-4 text-center text-gray-500 text-xs">Stato sconosciuto: {st}</div>;
  };

  // ─── renderPhaseReadOnly: renders a step's content in FROZEN mode ───
  const renderPhaseReadOnly = (stepIdx) => {
    if (!selected) return null;
    const f = selected;
    const data = (key, fallback = '—') => f[key] || f.pipeline_metrics?.[key] || fallback;

    // Step 0: IDEA
    if (stepIdx === 0) return (
      <div className="p-3 space-y-2" data-testid="readonly-step-0">
        <div className="text-[10px] space-y-1 text-gray-300">
          <p><span className="text-gray-500 font-bold">Titolo:</span> {f.title}</p>
          <p><span className="text-gray-500 font-bold">Genere:</span> {f.genre} {f.subgenres?.length > 0 && `(${f.subgenres.join(', ')})`}</p>
          <p><span className="text-gray-500 font-bold">Pre-Trama:</span> {f.pre_screenplay || f.pre_trama || '—'}</p>
          <p><span className="text-gray-500 font-bold">Location:</span> {(f.locations || []).join(', ') || '—'}</p>
          {f.pre_imdb_score > 0 && <p><span className="text-gray-500 font-bold">Pre-IMDb:</span> {f.pre_imdb_score?.toFixed?.(1)}</p>}
        </div>
      </div>
    );

    // Step 1: HYPE
    if (stepIdx === 1) return (
      <div className="p-3 space-y-2" data-testid="readonly-step-1">
        <div className="text-[10px] space-y-1 text-gray-300">
          <p><span className="text-gray-500 font-bold">Strategia Hype:</span> {data('hype_strategy')}</p>
          <p><span className="text-gray-500 font-bold">Hype Score:</span> {f.pipeline_metrics?.hype_score || f.hype_score || 0}</p>
          <p><span className="text-gray-500 font-bold">Agenzie Interessate:</span> {(f.interested_agencies || []).length}</p>
        </div>
      </div>
    );

    // Step 2: CAST
    if (stepIdx === 2) return (
      <div className="p-3 space-y-2" data-testid="readonly-step-2">
        <div className="text-[10px] space-y-1 text-gray-300">
          <p className="text-gray-500 font-bold">Cast Selezionato:</p>
          {(f.cast || []).map((c, i) => (
            <p key={i} className="pl-2">{c.name || c.actor_name} — {c.role || c.character}</p>
          ))}
          {(!f.cast || f.cast.length === 0) && <p className="text-gray-600">Nessun cast salvato</p>}
        </div>
      </div>
    );

    // Step 3: PREP
    if (stepIdx === 3) return (
      <div className="p-3 space-y-2" data-testid="readonly-step-3">
        <div className="text-[10px] space-y-1 text-gray-300">
          <p><span className="text-gray-500 font-bold">Budget Produzione:</span> ${(f.production_budget || 0).toLocaleString()}</p>
          <p><span className="text-gray-500 font-bold">CGI:</span> {f.cgi_level || data('cgi_level')}</p>
          <p><span className="text-gray-500 font-bold">VFX:</span> {f.vfx_level || data('vfx_level')}</p>
          <p><span className="text-gray-500 font-bold">Extra:</span> {f.extras_count || data('extras')}</p>
        </div>
      </div>
    );

    // Step 4: CIAK
    if (stepIdx === 4) return (
      <div className="p-3 space-y-2" data-testid="readonly-step-4">
        <div className="text-[10px] text-gray-300">
          <p><span className="text-gray-500 font-bold">Stato:</span> Riprese completate</p>
          <p><span className="text-gray-500 font-bold">Eventi:</span> {(f.pipeline_metrics?.shooting_events || []).length || 0} eventi durante le riprese</p>
        </div>
      </div>
    );

    // Step 5: FINAL CUT
    if (stepIdx === 5) return (
      <div className="p-3 space-y-2" data-testid="readonly-step-5">
        <div className="text-[10px] text-gray-300">
          <p><span className="text-gray-500 font-bold">Stato:</span> Post-produzione completata</p>
          <p><span className="text-gray-500 font-bold">Quality:</span> {f.pipeline_metrics?.quality_score?.toFixed?.(1) || '—'}</p>
        </div>
      </div>
    );

    // Step 6: MARKETING
    if (stepIdx === 6) return (
      <div className="p-3 space-y-2" data-testid="readonly-step-6">
        <div className="text-[10px] space-y-1 text-gray-300">
          <p><span className="text-gray-500 font-bold">Sponsor:</span> {(f.sponsors || []).map(s => s.name || s).join(', ') || '—'}</p>
          <p><span className="text-gray-500 font-bold">Marketing Score:</span> {f.pipeline_metrics?.marketing_score?.toFixed?.(1) || '—'}</p>
        </div>
      </div>
    );

    // Step 7: LA PRIMA
    if (stepIdx === 7) return (
      <div className="p-3 space-y-2" data-testid="readonly-step-7">
        <div className="text-[10px] text-gray-300">
          <p><span className="text-gray-500 font-bold">Premiere:</span> In corso o completata</p>
        </div>
      </div>
    );

    return <div className="p-3 text-[10px] text-gray-500">Dati non disponibili</div>;
  };

  // ─── CREATE VIEW: title + genre then enter detail ───
  if (view === 'create') {
    return <CreateFilmView onBack={backToBoard} onCreated={(film) => { setSelected(film); setView('detail'); loadFilms(); }} toast={toast} />;
  }

  // ─── DETAIL VIEW ───
  if (view === 'detail' && selected) {

    const editCount = selected.edit_count || 0;
    const canEdit = editCount < 3 && !['released', 'completed', 'discarded', 'release_pending'].includes(selected.pipeline_state);

    const handleViewStep = (stepIdx) => {
      // Allow viewing USCITA (step 8) during premiere_live
      if (stepIdx === 8 && selected?.pipeline_state === 'premiere_live') {
        setViewingStep(null); // Not read-only view, just navigate there
        setForceUscita(true);
        return;
      }
      setForceUscita(false);
      setViewingStep(stepIdx);
    };
    const handleCloseView = () => { setViewingStep(null); setShowEditConfirm(null); setForceUscita(false); };

    const handleConfirmEdit = async () => {
      const targetStep = showEditConfirm;
      setShowEditConfirm(null);
      try {
        const res = await api.post(`/films/${selected.id}/edit-step`, { target_ui_step: targetStep });
        setSelected(res.film);
        setViewingStep(null);
        loadFilms();
        toast({ title: res.message || 'Step sbloccato!' });
      } catch (e) {
        toast({ title: 'Errore', description: e.message, variant: 'destructive' });
      }
    };

    // If viewing a past step in read-only mode
    if (viewingStep !== null) {
      const stepInfo = V2_STEPS[viewingStep];
      const Icon = stepInfo.icon;
      const isEditable = canEdit && !EDIT_BLOCKED_STEPS.has(viewingStep);

      return (
        <div className="min-h-screen bg-black text-white pt-14 pb-40" data-testid="pipeline-v2-readonly">
          {/* Header */}
          <div className="flex items-center gap-3 p-3 border-b border-gray-800/50">
            <button onClick={handleCloseView} className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center hover:bg-gray-700 transition-colors" data-testid="readonly-back-btn">
              <ChevronLeft className="w-4 h-4 text-gray-400" />
            </button>
            <Icon className="w-5 h-5 text-gray-400" />
            <div className="flex-1">
              <h2 className="text-sm font-bold text-white">{stepInfo.label}</h2>
              <p className="text-[8px] text-gray-500">Dati salvati — Sola lettura</p>
            </div>
            <Lock className="w-4 h-4 text-gray-600" />
          </div>

          {/* Read-only content */}
          <div className="border-b border-gray-800/30">
            {renderPhaseReadOnly(viewingStep)}
          </div>

          {/* Edit button + counter */}
          {isEditable && (
            <div className="p-3 space-y-2">
              <div className="flex justify-end">
                <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 font-bold" data-testid="edit-counter">
                  {3 - editCount}/3 modifiche
                </span>
              </div>
              <button
                onClick={() => setShowEditConfirm(viewingStep)}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-400 hover:bg-amber-500/20 transition-colors font-bold text-[10px]"
                data-testid="edit-step-btn"
              >
                <Pencil className="w-3.5 h-3.5" /> Modifica questo step
              </button>
            </div>
          )}

          {!isEditable && EDIT_BLOCKED_STEPS.has(viewingStep) && (
            <div className="p-3">
              <p className="text-[8px] text-gray-600 text-center">Questo step (basato su timer) non puo essere modificato</p>
            </div>
          )}

          <CineConfirm
            open={showEditConfirm !== null}
            title="Vuoi riscrivere questa scena?"
            subtitle={`Userai 1 delle tue ${3 - editCount} revisioni disponibili.${editCount >= 2 ? " Ultima revisione!" : ''}`}
            confirmLabel="Riscrivi"
            onConfirm={handleConfirmEdit}
            onCancel={() => setShowEditConfirm(null)}
          />
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-black text-white pt-14 pb-40" data-testid="pipeline-v2-detail">
        <FilmHeader film={selected} onBack={backToBoard} />
        <StepperBar
          uiStep={forceUscita ? 8 : (selected.pipeline_ui_step ?? 0)}
          onViewStep={handleViewStep}
          allowScheduleStep={selected.pipeline_state === 'premiere_live'}
        />
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

const GENRE_LABELS = {
  action: 'Action', comedy: 'Comedy', drama: 'Drama', horror: 'Horror', sci_fi: 'Sci-Fi',
  romance: 'Romance', thriller: 'Thriller', animation: 'Animation', documentary: 'Documentary',
  fantasy: 'Fantasy', musical: 'Musical', western: 'Western', biographical: 'Biographical',
  mystery: 'Mystery', adventure: 'Adventure', war: 'War', crime: 'Crime', noir: 'Noir', historical: 'Storico',
};

const GENRE_TAGLINES = {
  comedy: 'Il pubblico vuole ridere. Parti dal titolo giusto.',
  thriller: 'La tensione comincia dal concept.',
  drama: 'Ogni storia ha bisogno della giusta profondita.',
  historical: 'Ogni epoca ha bisogno della sua visione.',
  action: "L'adrenalina nasce dalle idee.",
  horror: 'Il terrore si costruisce frame per frame.',
  sci_fi: 'Il futuro prende forma dalla tua immaginazione.',
  romance: "L'amore sullo schermo inizia dalla sceneggiatura.",
  war: 'Le grandi battaglie nascono da grandi storie.',
  crime: 'Ogni crimine perfetto inizia con un piano.',
  noir: "L'ombra e la luce, il bene e il male.",
  fantasy: 'Mondi interi nascono dalla tua visione.',
  mystery: 'Ogni indizio conta. Ogni dettaglio e fondamentale.',
  adventure: "L'avventura chiama. Rispondi con una storia.",
  animation: 'Dai colore ai tuoi sogni.',
  documentary: 'La realta e la migliore sceneggiatura.',
  musical: 'Quando le parole non bastano, si canta.',
  western: 'Il sole tramonta, la leggenda inizia.',
  biographical: 'Vite straordinarie meritano il grande schermo.',
};

const MINI_STEPS = ['IDEA', 'HYPE', 'CAST', 'PREP', 'CIAK', 'FINAL CUT', 'LANCIO'];

const CONTENT_TYPES = [
  { id: 'film', label: 'Film', icon: 'Film', desc: 'Lungometraggio classico' },
  { id: 'serie_tv', label: 'Serie TV', icon: 'Tv', desc: 'Serie a episodi' },
  { id: 'anime', label: 'Anime', icon: 'Sparkles', desc: 'Animazione giapponese' },
];

const CreateFilmView = ({ onBack, onCreated, toast }) => {
  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('drama');
  const [subgenres, setSubgenres] = useState([]);
  const [contentType, setContentType] = useState('film');
  const [durationCat, setDurationCat] = useState('standard');
  const [episodeCount, setEpisodeCount] = useState(12);
  const [creating, setCreating] = useState(false);
  const [showCinematic, setShowCinematic] = useState(false);
  const [count, setCount] = useState(3);
  const pendingFilmRef = useRef(null);
  const isSeries = contentType === 'serie_tv' || contentType === 'anime';

  const availableSubs = SUBGENRE_MAP[genre] || [];

  const toggleSub = (sg) => {
    setSubgenres(prev => {
      if (prev.includes(sg)) return prev.filter(s => s !== sg);
      if (prev.length >= 3) return [...prev.slice(1), sg];
      return [...prev, sg];
    });
  };

  const changeGenre = (g) => { setGenre(g); setSubgenres([]); };

  // Cinematic countdown
  useEffect(() => {
    if (!showCinematic) return;
    let current = 3;
    setCount(3);
    const iv = setInterval(() => {
      current--;
      if (current <= 0) {
        clearInterval(iv);
        setTimeout(() => {
          setShowCinematic(false);
          if (pendingFilmRef.current) onCreated(pendingFilmRef.current);
        }, 500);
      } else {
        setCount(current);
      }
    }, 900);
    return () => clearInterval(iv);
  }, [showCinematic, onCreated]);

  const create = async () => {
    if (!title.trim()) return;
    setCreating(true);
    try {
      const payload = { title: title.trim(), genre, subgenres, content_type: contentType };
      const res = await api.post('/films', payload);
      // Set duration category for films
      if (!isSeries && durationCat) {
        await api.post(`/films/${res.film.id}/set-duration`, { category: durationCat }).catch(() => {});
      }
      if (isSeries && episodeCount >= 8 && episodeCount <= 24) {
        await api.post(`/films/${res.film.id}/set-episodes`, { episode_count: episodeCount }).catch(() => {});
      }
      const typeLabel = contentType === 'serie_tv' ? 'Serie TV' : contentType === 'anime' ? 'Anime' : 'Film';
      toast({ title: `${typeLabel} creato!` });
      pendingFilmRef.current = res.film;
      setShowCinematic(true);
    } catch (e) { toast({ title: 'Errore', description: e.message, variant: 'destructive' }); }
    setCreating(false);
  };

  return (
    <>
    {/* ═══ CINEMATIC INTRO OVERLAY ═══ */}
    {showCinematic && (
      <div className="fixed inset-0 z-[9999] bg-black overflow-hidden" data-testid="cinematic-intro">
        {/* Film grain */}
        <div className="absolute inset-0 pointer-events-none opacity-30" style={{
          background: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.03), rgba(255,255,255,0.03) 1px, transparent 1px, transparent 3px)',
        }} />

        {/* Scratch lines */}
        <div className="absolute inset-0 pointer-events-none opacity-15" style={{
          background: `linear-gradient(90deg, transparent 49.5%, rgba(255,255,255,0.15) 49.5%, rgba(255,255,255,0.15) 50.5%, transparent 50.5%),
                       linear-gradient(90deg, transparent 30%, rgba(255,255,255,0.08) 30%, rgba(255,255,255,0.08) 30.3%, transparent 30.3%)`,
          animation: 'scratchMove 0.3s steps(3) infinite',
        }} />

        {/* Real projector PNG */}
        <img src="/assets/projector.png" alt="" className="absolute bottom-3 left-2 w-24 z-10" style={{ filter: 'brightness(0.85) contrast(1.2)' }} />

        {/* Light beam — from projector lens toward screen (bottom-left → top-right) */}
        <div className="absolute z-[2]" style={{
          bottom: '60px', left: '90px',
          width: '70vw', maxWidth: '380px', height: '220px',
          background: 'linear-gradient(28deg, rgba(255,255,230,0.35) 0%, rgba(255,255,230,0.15) 25%, rgba(255,255,230,0.04) 55%, transparent 100%)',
          filter: 'blur(7px)',
          transformOrigin: 'bottom left',
          transform: 'skewX(-8deg)',
          animation: 'beamFlicker 0.25s infinite alternate',
        }} />
        <div className="absolute z-[1]" style={{
          bottom: '50px', left: '80px',
          width: '75vw', maxWidth: '400px', height: '250px',
          background: 'linear-gradient(25deg, rgba(255,255,200,0.12) 0%, rgba(255,255,200,0.04) 40%, transparent 70%)',
          filter: 'blur(16px)',
          transformOrigin: 'bottom left',
          transform: 'skewX(-5deg)',
          animation: 'beamFlicker 0.3s infinite alternate-reverse',
        }} />

        {/* Screen */}
        <div className="absolute z-[3]" style={{ top: '16%', right: '6%', width: '58%', maxWidth: '250px', aspectRatio: '16/10' }}>
          <div className="w-full h-full rounded-md flex flex-col items-center justify-center relative" style={{
            background: '#f0ece0',
            boxShadow: '0 0 80px rgba(255,255,220,0.2), 0 0 160px rgba(255,255,200,0.06)',
          }}>
            <div className="absolute inset-0 rounded-md" style={{ background: 'radial-gradient(ellipse, transparent 45%, rgba(0,0,0,0.35) 100%)' }} />
            <span className="relative text-6xl font-bold text-black font-mono" style={{ animation: 'countFlicker 0.12s infinite', textShadow: '0 0 2px rgba(0,0,0,0.3)' }} data-testid="cinematic-count">{count}</span>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
              <div className="w-[1px] h-full bg-black/30 absolute" />
              <div className="h-[1px] w-full bg-black/30 absolute" />
              <div className="w-16 h-16 rounded-full border border-black/20 absolute" />
            </div>
          </div>
        </div>

        {/* Flash fotografici realistici (paparazzi) */}
        <div className="absolute inset-0 pointer-events-none z-[4]">
          <div className="absolute w-28 h-28 rounded-full" style={{ top: '18%', left: '8%', background: 'radial-gradient(circle, white 0%, rgba(255,255,255,0.3) 35%, transparent 65%)', opacity: 0, animation: 'paparazzi 2.8s 0.2s infinite' }} />
          <div className="absolute w-24 h-24 rounded-full" style={{ bottom: '28%', right: '12%', background: 'radial-gradient(circle, white 0%, rgba(255,255,255,0.3) 35%, transparent 65%)', opacity: 0, animation: 'paparazzi 3.2s 1.4s infinite' }} />
          <div className="absolute w-20 h-20 rounded-full" style={{ top: '55%', left: '45%', background: 'radial-gradient(circle, white 0%, rgba(255,255,255,0.25) 35%, transparent 65%)', opacity: 0, animation: 'paparazzi 2.5s 2.3s infinite' }} />
        </div>

        {/* Titoli cinematografici */}
        <div className="absolute bottom-16 left-0 right-0 text-center z-[5]" style={{ animation: 'fadeInSlow 1.5s ease-out' }}>
          <p className="text-[9px] text-gray-500 uppercase tracking-[0.3em] font-mono">una produzione di</p>
          <p className="text-2xl font-bold text-[#f5c518] mt-1.5 tracking-wide">{title || 'Il Tuo Film'}</p>
          <p className="text-sm text-blue-400 mt-1 font-medium">CineWorld Studios</p>
        </div>

        <style>{`
          @keyframes beamFlicker { from { opacity: 0.65; } to { opacity: 1; } }
          @keyframes countFlicker { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }
          @keyframes scratchMove { 0% { transform: translateX(0); } 100% { transform: translateX(3px); } }
          @keyframes paparazzi {
            0%, 90%, 100% { opacity: 0; transform: scale(0.6); }
            93% { opacity: 1; transform: scale(1.1); }
            96% { opacity: 0; transform: scale(0.8); }
          }
          @keyframes fadeInSlow { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        `}</style>
      </div>
    )}

    <div className="min-h-screen bg-gradient-to-b from-black via-[#080c18] to-black text-white" data-testid="pipeline-v2-create">
      {/* Vignette glow */}
      <div className="fixed inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse at 50% 30%, rgba(180,130,40,0.06) 0%, transparent 60%)' }} />

      {/* Flash fotografici */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {[
          { top: '12%', left: '8%', delay: '0s' },
          { top: '35%', right: '5%', delay: '2s' },
          { bottom: '25%', left: '15%', delay: '4s' },
        ].map((pos, i) => (
          <div key={i} className="absolute w-16 h-16 opacity-0" style={{
            ...pos,
            background: 'radial-gradient(circle, rgba(255,255,255,0.7) 0%, transparent 70%)',
            animation: `flashPop 7s ${pos.delay} infinite`,
          }} />
        ))}
      </div>

      {/* Keyframes */}
      <style>{`
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.35; transform: scale(0.97); }
          50% { opacity: 0.75; transform: scale(1.03); }
        }
        @keyframes flashPop {
          0%, 10%, 100% { opacity: 0; transform: scale(0.5); }
          4% { opacity: 0.8; transform: scale(1.1); }
          7% { opacity: 0; transform: scale(0.7); }
        }
      `}</style>

      <div className="relative z-10 px-4 pt-12 pb-16">
        {/* Back */}
        <button onClick={onBack} className="flex items-center gap-1 mb-2 text-gray-500 hover:text-gray-300 transition-colors" data-testid="create-back-btn">
          <ChevronLeft className="w-3.5 h-3.5" />
          <span className="text-[10px]">Indietro</span>
        </button>

        {/* Header */}
        <h1 className="text-lg font-bold text-amber-400 tracking-tight">
          {contentType === 'serie_tv' ? 'Crea la tua Serie TV' : contentType === 'anime' ? 'Crea il tuo Anime' : 'Dai vita al tuo prossimo film'}
        </h1>
        <p className="text-xs text-gray-400 mt-0.5 mb-2">Scegli titolo e genere. Il resto prendera forma lungo la produzione.</p>

        {/* Content Type Selector */}
        <div className="flex gap-1.5 mb-3">
          {CONTENT_TYPES.map(ct => (
            <button key={ct.id} onClick={() => setContentType(ct.id)}
              className={`flex-1 py-1.5 px-2 rounded-lg border text-center transition-all ${
                contentType === ct.id
                  ? 'bg-amber-500/15 border-amber-500/40 text-amber-400'
                  : 'border-gray-800 text-gray-500 hover:border-gray-600'
              }`} data-testid={`content-type-${ct.id}`}>
              <p className="text-[10px] font-bold">{ct.label}</p>
              <p className="text-[7px] text-gray-500">{ct.desc}</p>
            </button>
          ))}
        </div>

        {/* Mini step bar */}
        <div className="flex gap-1 overflow-x-auto no-scrollbar mb-3">
          {MINI_STEPS.map((s, i) => (
            <span key={s} className={`flex-shrink-0 px-1.5 py-0.5 rounded-full text-[6px] font-bold uppercase tracking-wider border ${
              i === 0 ? 'bg-amber-500/15 border-amber-500/40 text-amber-400' : 'bg-gray-800/30 border-gray-800 text-gray-600'
            }`}>{s}</span>
          ))}
        </div>

        {/* Main card */}
        <div className="rounded-2xl border border-gray-800/60 bg-gradient-to-b from-gray-900/60 to-gray-900/30 backdrop-blur-sm p-3 space-y-3" style={{ boxShadow: '0 0 40px rgba(180,130,40,0.04)' }}>

          {/* Poster preview — compact with aura */}
          <div className="flex gap-3 items-center">
            <div className="relative flex-shrink-0">
              {/* Aura glow */}
              <div className="absolute -inset-2 rounded-xl opacity-50" style={{
                background: 'radial-gradient(circle, rgba(0,180,255,0.3) 0%, transparent 70%)',
                filter: 'blur(10px)',
                animation: 'pulseGlow 3s infinite ease-in-out',
              }} />
              <div className="relative w-16 rounded-lg overflow-hidden border border-cyan-500/20 bg-gradient-to-b from-gray-800/80 to-gray-900" style={{ aspectRatio: '2/3' }}>
                <div className="w-full h-full flex flex-col items-center justify-center p-1.5 relative">
                  <Film className="w-5 h-5 text-gray-700/30 absolute" />
                  <div className="relative z-10 text-center">
                    <span className="text-[5px] px-1 py-0 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400 font-bold uppercase">In sviluppo</span>
                    <p className="text-[8px] font-bold text-white leading-tight mt-1 line-clamp-2">{title || 'Titolo'}</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <label className="text-[8px] text-gray-500 uppercase tracking-wider font-bold block mb-1">Titolo del Film</label>
              <input
                value={title} onChange={e => setTitle(e.target.value)}
                placeholder="Il tuo prossimo capolavoro..."
                autoFocus
                className="w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:border-amber-500/40 focus:outline-none transition-colors"
                data-testid="create-title"
              />
            </div>
          </div>

          {/* Genre dropdown */}
          <div>
            <label className="text-[8px] text-gray-500 uppercase tracking-wider font-bold block mb-1">Genere</label>
            <select
              value={genre} onChange={e => changeGenre(e.target.value)}
              className="w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-amber-500/40 focus:outline-none"
              data-testid="create-genre"
            >
              {GENRES.map(g => <option key={g} value={g}>{GENRE_LABELS[g] || g}</option>)}
            </select>
            <p className="text-[8px] text-amber-400/50 mt-1 italic min-h-[12px]">{GENRE_TAGLINES[genre] || 'Ogni grande film inizia da un\'idea.'}</p>
          </div>

          {/* Subgenres chips */}
          <div>
            <label className="text-[8px] text-gray-500 uppercase tracking-wider font-bold block mb-1">
              Sottogeneri <span className="text-gray-600">(max 3)</span>
            </label>
            <div className="flex flex-wrap gap-1" data-testid="subgenre-chips">
              {availableSubs.map(sg => {
                const active = subgenres.includes(sg);
                return (
                  <button
                    key={sg} onClick={() => toggleSub(sg)}
                    className={`px-2 py-0.5 rounded-full text-[9px] font-medium border transition-all ${
                      active
                        ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                        : 'bg-gray-800/40 border-gray-700 text-gray-400 hover:border-gray-500'
                    }`}
                    data-testid={`subgenre-${sg}`}
                  >
                    {sg}
                  </button>
                );
              })}
            </div>
          </div>


          {/* Duration category — solo per Film */}
          {!isSeries && (
            <div>
              <label className="text-[8px] text-gray-500 uppercase tracking-wider font-bold block mb-1">Durata Film</label>
              <div className="grid grid-cols-5 gap-1">
                {[
                  { id: 'cortometraggio', label: 'Corto', sub: '20-45min', rev: '0.45x' },
                  { id: 'feature_breve', label: 'Breve', sub: '46-70min', rev: '0.7x' },
                  { id: 'standard', label: 'Standard', sub: '71-140min', rev: '1x' },
                  { id: 'extended', label: 'Extended', sub: '141-210min', rev: '1.3x' },
                  { id: 'kolossal', label: 'Kolossal', sub: '211-280min', rev: '1.6x' },
                ].map(d => (
                  <button key={d.id} onClick={() => setDurationCat(d.id)} data-testid={`duration-${d.id}`}
                    className={`text-center py-1.5 px-1 rounded-lg border text-[8px] transition-colors ${durationCat === d.id ? 'bg-amber-500/15 border-amber-500/40 text-amber-400' : 'bg-gray-800/40 border-gray-700 text-gray-500 hover:border-gray-500'}`}>
                    <div className="font-bold">{d.label}</div>
                    <div className="text-[6px] opacity-60">{d.sub}</div>
                    <div className="text-[6px] text-yellow-500/50">{d.rev}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Episode count — solo per Serie/Anime */}
          {isSeries && (
            <div>
              <label className="text-[8px] text-gray-500 uppercase tracking-wider font-bold block mb-1">
                Episodi <span className="text-gray-600">({episodeCount})</span>
              </label>
              <input type="range" min={8} max={24} value={episodeCount}
                onChange={e => setEpisodeCount(parseInt(e.target.value))}
                className="w-full h-1.5 bg-gray-800 rounded-full appearance-none cursor-pointer accent-amber-500"
                data-testid="episode-slider"
              />
              <div className="flex justify-between text-[7px] text-gray-600 mt-0.5">
                <span>8 ep</span>
                <span className="text-amber-400/60">
                  Qualita: {episodeCount === 8 ? '100%' : `${Math.round((1 - ((episodeCount - 8) * 0.02)) * 100)}%`}
                </span>
                <span>24 ep</span>
              </div>
            </div>
          )}

          {/* CTA Button */}
          <button
            onClick={create}
            disabled={creating || !title.trim()}
            className="w-full text-sm py-3 rounded-xl bg-amber-500 text-black font-bold hover:bg-amber-400 active:scale-[0.97] transition-all disabled:opacity-25 flex items-center justify-center gap-2"
            style={{ boxShadow: title.trim() ? '0 0 20px rgba(245,158,11,0.2)' : 'none' }}
            data-testid="create-confirm-btn"
          >
            <Plus className="w-4 h-4" />
            {creating ? 'Creazione...' : 'Crea e Inizia'}
          </button>
        </div>
      </div>
    </div>
    </>
  );
};

export default PipelineV2;
