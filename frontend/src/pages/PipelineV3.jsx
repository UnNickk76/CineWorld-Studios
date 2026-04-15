import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Film, ChevronLeft, Save, Sparkles, TrendingUp, Users, Camera, Clapperboard,
  Scissors, Megaphone, Globe, Ticket, Check, Award, X, Star, Clock, Zap } from 'lucide-react';
import CinematicReleaseOverlay from '../components/CinematicReleaseOverlay';

const API = process.env.REACT_APP_BACKEND_URL;

/* ═══════ CONSTANTS ═══════ */
const V3_STEPS = [
  { id: 'idea', label: 'IDEA', icon: Sparkles, color: 'amber' },
  { id: 'hype', label: 'HYPE', icon: TrendingUp, color: 'orange' },
  { id: 'cast', label: 'CAST', icon: Users, color: 'cyan' },
  { id: 'prep', label: 'PREP', icon: Camera, color: 'blue' },
  { id: 'ciak', label: 'CIAK', icon: Clapperboard, color: 'red' },
  { id: 'finalcut', label: 'FINAL CUT', icon: Scissors, color: 'purple' },
  { id: 'marketing', label: 'MARKETING', icon: Megaphone, color: 'green' },
  { id: 'distribution', label: 'DISTRIB.', icon: Globe, color: 'blue' },
  { id: 'release_pending', label: 'USCITA', icon: Ticket, color: 'emerald' },
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

const GENRES = ['action','comedy','drama','horror','sci_fi','romance','thriller','animation','documentary','fantasy','adventure','musical','western','biographical','mystery','war','crime','noir','historical'];
const GENRE_LABELS = { action:'Azione', comedy:'Commedia', drama:'Dramma', horror:'Horror', sci_fi:'Fantascienza', romance:'Romantico', thriller:'Thriller', animation:'Animazione', documentary:'Documentario', fantasy:'Fantasy', adventure:'Avventura', musical:'Musical', western:'Western', biographical:'Biografico', mystery:'Giallo', war:'Guerra', crime:'Crime', noir:'Noir', historical:'Storico' };
const SUBGENRE_MAP = {
  action:['militare','spy','vendetta','arti marziali','heist','survival'], comedy:['slapstick','romantica','nera','satirica','demenziale','teen','familiare'],
  drama:['romantico','psicologico','familiare','sociale','biografico','legale'], horror:['slasher','psicologico','soprannaturale','body horror','gotico','zombie'],
  sci_fi:['cyberpunk','space opera','distopia','alieni','mecha','viaggi nel tempo'], romance:['tragico','commedia romantica','teen romance','proibito','period'],
  thriller:['psicologico','crime','paranoia','politico','suspense','serial killer'], animation:['CGI','stop motion','2D classico','anime','mixed media'],
  documentary:['true crime','storico','sociale','natura','sportivo'], fantasy:['epico','dark fantasy','urban fantasy','mitologico','fiabesco'],
  adventure:['giungla','oceano','tesoro','survival','esplorazione'], musical:['broadway','dance','rock opera','biografico'], western:['classico','spaghetti','neo-western'],
  biographical:['musicale','politico','sportivo','criminale'], mystery:['whodunit','noir','giallo','poliziesco'], war:['WWII','moderna','medievale'],
  crime:['gangster','heist','detective','mafioso'], noir:['classico','neo-noir','tech-noir'], historical:['guerra','imperi','medioevo','rinascimento'],
};
const MARKETING_PACKAGES = [
  { name: 'Teaser Digitale', cost: 20000, hype: 5 },
  { name: 'Campagna Social', cost: 40000, hype: 12 },
  { name: 'Stampa e TV', cost: 60000, hype: 18 },
  { name: 'Tour Cast', cost: 80000, hype: 25 },
  { name: 'Mega Globale', cost: 150000, hype: 40 },
];
const RELEASE_DATES = ['Immediato','6 ore','12 ore','24 ore','2 giorni','3 giorni'];

/* ═══════ API HELPER ═══════ */
async function api(path, method = 'GET', body) {
  const token = localStorage.getItem('cineworld_token');
  const res = await fetch(`${API}/api/pipeline-v3${path}`, {
    method, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || 'Errore API');
  return data;
}

/* ═══════ PROGRESS CIRCLE ═══════ */
const ProgressCircle = ({ value, size = 48, color = '#00FFD0' }) => {
  const r = (size / 2) - 4;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(100, Math.max(0, value)) / 100) * circ;
  return (
    <svg width={size} height={size} className="block">
      <circle cx={size/2} cy={size/2} r={r} stroke="#333" strokeWidth="3" fill="none" />
      <circle cx={size/2} cy={size/2} r={r} stroke={color} strokeWidth="3" fill="none"
        strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.5s ease', transform: 'rotate(-90deg)', transformOrigin: 'center' }} />
      <text x={size/2} y={size/2} textAnchor="middle" dominantBaseline="central"
        fill={color} fontSize={size * 0.22} fontWeight="bold">{Math.floor(value)}%</text>
    </svg>
  );
};

/* ═══════ STEPPER ═══════ */
const StepperBar = ({ current }) => {
  const ci = V3_STEPS.findIndex(s => s.id === current);
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) {
      const el = ref.current.querySelector(`[data-sid="${current}"]`);
      if (el) el.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
  }, [current]);
  return (
    <div ref={ref} className="flex items-center gap-0 overflow-x-auto py-2 px-1 scrollbar-hide" data-testid="v3-stepper">
      {V3_STEPS.map((s, i) => {
        const Icon = s.icon;
        const style = STEP_STYLES[s.color];
        const done = i < ci;
        const active = i === ci;
        return (
          <React.Fragment key={s.id}>
            {i > 0 && <div className={`w-2 sm:w-4 h-0.5 shrink-0 ${done || active ? style.line : 'bg-gray-800'}`} />}
            <div className="flex flex-col items-center shrink-0 gap-0.5" data-sid={s.id}>
              <div className={`w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                active ? `${style.active} shadow-lg scale-110` :
                done ? 'border-emerald-600 bg-emerald-500/10 text-emerald-400' :
                'border-gray-800 bg-gray-900/50 text-gray-700 opacity-40'
              }`}>
                {done ? <Check className="w-2.5 h-2.5" /> : <Icon className="w-2.5 h-2.5" />}
              </div>
              <span className={`text-[5px] sm:text-[6px] font-bold uppercase tracking-wider whitespace-nowrap ${
                active ? style.text : done ? 'text-emerald-500/60' : 'text-gray-700'
              }`}>{s.label}</span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

/* ═══════ PHASE WRAPPER ═══════ */
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

/* ═══════ FILM HEADER ═══════ */
const FilmHeader = ({ film, onBack, onSaveDraft, dirty, loading }) => (
  <div className="flex items-center gap-3 p-3 border-b border-gray-800/50">
    <button onClick={onBack} className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center" data-testid="back-btn">
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
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium uppercase">{GENRE_LABELS[film.genre] || film.genre || '—'}</span>
        <span className="text-[7px] px-1 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/15 font-bold">V3</span>
      </div>
    </div>
    <button onClick={onSaveDraft} disabled={loading || !dirty}
      className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[8px] font-bold border ${
        dirty ? 'border-amber-500/30 bg-amber-500/10 text-amber-400' : 'border-gray-800 bg-gray-900 text-gray-600'
      } disabled:opacity-30`} data-testid="save-draft-btn">
      <Save className="w-3 h-3" /> {dirty ? 'Salva' : 'OK'}
    </button>
  </div>
);

/* ═══════ SPEEDUP BUTTONS ═══════ */
const SpeedupButtons = ({ stage, onSpeedup, loading }) => (
  <div className="flex gap-1.5 flex-wrap">
    {[25,50,75,100].map(p => (
      <button key={p} onClick={() => onSpeedup(stage, p)} disabled={loading}
        className="flex items-center gap-1 px-2 py-1.5 rounded-lg bg-yellow-500/5 border border-yellow-500/15 text-yellow-400 text-[9px] font-bold hover:bg-yellow-500/10 transition-colors disabled:opacity-30">
        <Zap className="w-3 h-3" /> {p}%
      </button>
    ))}
  </div>
);

/* ═══════ MAIN COMPONENT ═══════ */
export default function PipelineV3() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [dirty, setDirty] = useState(false);
  const [posterProgress, setPosterProgress] = useState(0);
  const [scriptProgress, setScriptProgress] = useState(0);
  const posterIntRef = useRef(null);
  const scriptIntRef = useRef(null);
  const autosaveRef = useRef(null);

  // Release flow
  const [releasePhase, setReleasePhase] = useState('idle');
  const [releaseProgress, setReleaseProgress] = useState(0);
  const [releaseResult, setReleaseResult] = useState(null);
  const progressRef = useRef(null);

  // Form
  const [idea, setIdea] = useState({ title: '', genre: 'action', subgenre: '', preplot: '' });
  const [posterSource, setPosterSource] = useState('preplot');
  const [posterPrompt, setPosterPrompt] = useState('');
  const [screenplaySource, setScreenplaySource] = useState('preplot');
  const [screenplayPrompt, setScreenplayPrompt] = useState('');
  const [hypeNotes, setHypeNotes] = useState('');
  const [hypeBudget, setHypeBudget] = useState(0);
  const [castNotes, setCastNotes] = useState('');
  const [chemistryMode, setChemistryMode] = useState('auto');
  const [prepNotes, setPrepNotes] = useState('');
  const [finalcutNotes, setFinalcutNotes] = useState('');
  const [marketingPkgs, setMarketingPkgs] = useState([]);
  const [releaseType, setReleaseType] = useState('direct');
  const [releaseDate, setReleaseDate] = useState('Immediato');
  const [world, setWorld] = useState(true);

  const showToast = (msg, type = 'ok') => setToast({ msg, type });
  const markDirty = () => setDirty(true);

  const loadProjects = useCallback(async () => {
    try { const d = await api('/films'); setProjects(d.items || []); } catch {}
  }, []);

  const syncForm = useCallback((p) => {
    if (!p) return;
    setIdea({ title: p.title || '', genre: p.genre || 'action', subgenre: p.subgenre || '', preplot: p.preplot || '' });
    setHypeNotes(p.hype_notes || ''); setHypeBudget(p.hype_budget || 0);
    setCastNotes(p.cast_notes || ''); setChemistryMode(p.chemistry_mode || 'auto');
    setPrepNotes(p.prep_notes || ''); setFinalcutNotes(p.finalcut_notes || '');
    setMarketingPkgs(p.marketing_packages || []); setReleaseType(p.release_type || 'direct');
    setReleaseDate(p.release_date_label || 'Immediato'); setWorld(p.distribution_world ?? true);
    setPosterSource(p.poster_source || 'preplot'); setPosterPrompt(p.poster_prompt || '');
    setScreenplaySource(p.screenplay_source || 'preplot'); setScreenplayPrompt(p.screenplay_prompt || '');
    setDirty(false);
  }, []);

  const selectProject = useCallback(async (p) => {
    try { const d = await api(`/films/${p.id}`); setSelected(d); syncForm(d); } catch (e) { showToast(e.message, 'error'); }
  }, [syncForm]);

  const refreshSelected = useCallback(async () => {
    if (!selected?.id) return null;
    try { const d = await api(`/films/${selected.id}`); setSelected(d); syncForm(d); return d; } catch { return null; }
  }, [selected?.id, syncForm]);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  const currentStep = selected?.pipeline_state || 'idea';
  const stepIndex = V3_STEPS.findIndex(s => s.id === currentStep);
  const subgenreOptions = useMemo(() => SUBGENRE_MAP[idea.genre] || [], [idea.genre]);

  // Autosave
  useEffect(() => {
    if (!selected || !dirty) return;
    autosaveRef.current = setTimeout(async () => {
      try { await api(`/films/${selected.id}/save-idea`, 'POST', idea); setDirty(false); } catch {}
    }, 10000);
    return () => clearTimeout(autosaveRef.current);
  }, [dirty, selected, idea]);

  // API runner
  const run = async (fn, msg) => {
    setLoading(true);
    try { await fn(); if (msg) showToast(msg); await loadProjects(); } catch (e) { showToast(e.message, 'error'); }
    setLoading(false);
  };

  const createProject = () => run(async () => {
    const res = await api('/films/create', 'POST', { title: 'Nuovo Film', genre: 'comedy', preplot: '' });
    setSelected(res.project); syncForm(res.project);
  }, 'Progetto V3 creato!');

  const saveDraft = () => run(async () => {
    await api(`/films/${selected.id}/save-idea`, 'POST', idea); setDirty(false);
  }, 'Bozza salvata');

  const saveStepAndAdvance = async (nextState) => {
    setLoading(true);
    try {
      const st = currentStep;
      if (st === 'idea') await api(`/films/${selected.id}/save-idea`, 'POST', idea);
      else if (st === 'hype') await api(`/films/${selected.id}/save-hype`, 'POST', { hype_notes: hypeNotes, budget: Number(hypeBudget || 0) });
      else if (st === 'cast') await api(`/films/${selected.id}/save-cast`, 'POST', { cast_notes: castNotes, chemistry_mode: chemistryMode });
      else if (st === 'prep') await api(`/films/${selected.id}/save-prep`, 'POST', { prep_notes: prepNotes });
      else if (st === 'ciak') await api(`/films/${selected.id}/start-ciak`, 'POST');
      else if (st === 'finalcut') await api(`/films/${selected.id}/save-finalcut`, 'POST', { finalcut_notes: finalcutNotes });
      else if (st === 'marketing') {
        await api(`/films/${selected.id}/save-marketing`, 'POST', { packages: marketingPkgs });
        await api(`/films/${selected.id}/set-release-type`, 'POST', { release_type: releaseType });
      }
      else if (st === 'distribution') await api(`/films/${selected.id}/schedule-release`, 'POST', { release_date_label: releaseDate, world, zones: [] });
      if (nextState) await api(`/films/${selected.id}/advance`, 'POST', { next_state: nextState });
      await refreshSelected(); setDirty(false);
    } catch (e) { showToast(e.message, 'error'); }
    setLoading(false);
  };

  const speedup = async (stage, pct) => {
    setLoading(true);
    try {
      await api(`/films/${selected.id}/speedup`, 'POST', { stage, percentage: pct });
      await refreshSelected(); showToast(`Velocizzazione ${pct}% applicata!`);
    } catch (e) { showToast(e.message, 'error'); }
    setLoading(false);
  };

  const generatePoster = async (mode) => {
    setLoading(true); setPosterProgress(5);
    posterIntRef.current = setInterval(() => setPosterProgress(p => p >= 90 ? p : p + Math.random() * 10), 800);
    try {
      await api(`/films/${selected.id}/generate-poster`, 'POST', {
        source: mode === 'custom' ? 'custom_prompt' : 'preplot',
        custom_prompt: mode === 'custom' ? posterPrompt : '',
      });
      setPosterProgress(100); clearInterval(posterIntRef.current);
      await refreshSelected(); showToast('Locandina salvata!');
    } catch (e) { clearInterval(posterIntRef.current); setPosterProgress(0); showToast(e.message, 'error'); }
    setLoading(false);
  };

  const generateScreenplay = async () => {
    setLoading(true); setScriptProgress(5);
    scriptIntRef.current = setInterval(() => setScriptProgress(p => p >= 90 ? p : p + Math.random() * 8), 1000);
    try {
      await api(`/films/${selected.id}/generate-screenplay`, 'POST', {
        source: screenplaySource === 'custom_prompt' ? 'custom_prompt' : 'preplot',
        custom_prompt: screenplaySource === 'custom_prompt' ? screenplayPrompt : '',
      });
      setScriptProgress(100); clearInterval(scriptIntRef.current);
      await refreshSelected(); showToast('Sceneggiatura generata!');
    } catch (e) { clearInterval(scriptIntRef.current); setScriptProgress(0); showToast(e.message, 'error'); }
    setLoading(false);
  };

  // ═══════ CONFIRM RELEASE ═══════
  const confirmRelease = async () => {
    if (releasePhase !== 'idle' || !selected?.id) return;
    setReleasePhase('progress'); setReleaseProgress(0);
    let p = 0;
    progressRef.current = setInterval(() => { p += Math.random() * 6 + 2; if (p >= 100) { p = 100; clearInterval(progressRef.current); } setReleaseProgress(Math.min(100, p)); }, 400);
    await new Promise(r => { const c = setInterval(() => { if (p >= 100) { clearInterval(c); r(); } }, 200); });
    await new Promise(r => setTimeout(r, 800));
    setReleasePhase('calling');
    try {
      const res = await api(`/films/${selected.id}/confirm-release`, 'POST');
      setReleaseResult(res);
      await refreshSelected();
      setReleasePhase('wow');
    } catch (e) {
      showToast(e.message, 'error');
      setReleasePhase('idle'); setReleaseProgress(0);
    }
  };

  const onWowDone = () => { setReleasePhase('idle'); loadProjects(); navigate('/'); };
  const discard = () => run(async () => { await api(`/films/${selected.id}/discard`, 'POST'); setSelected(null); }, 'Film scartato');

  useEffect(() => { return () => { if (progressRef.current) clearInterval(progressRef.current); }; }, []);

  const active = projects.filter(p => !['released','completed','discarded'].includes(p.pipeline_state));

  /* ═══════ RELEASE OVERLAY ═══════ */
  if (releasePhase === 'progress' || releasePhase === 'calling') {
    return (
      <div className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center">
        <svg width="120" height="120"><circle cx="60" cy="60" r="50" stroke="#1f2937" strokeWidth="6" fill="none" />
          <circle cx="60" cy="60" r="50" stroke="#10b981" strokeWidth="6" fill="none"
            strokeDasharray={314} strokeDashoffset={314 - (releaseProgress / 100) * 314} strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.4s ease', transform: 'rotate(-90deg)', transformOrigin: 'center' }} />
        </svg>
        <div className="absolute text-3xl font-bold text-emerald-400">{Math.floor(releaseProgress)}%</div>
        <p className="text-gray-400 text-sm mt-6">{releasePhase === 'calling' ? 'Invio al sistema...' : 'Analisi in corso...'}</p>
      </div>
    );
  }
  if (releasePhase === 'wow' && selected) {
    return <CinematicReleaseOverlay film={selected} releaseType="cinema" onComplete={onWowDone} />;
  }

  /* ═══════ TOAST ═══════ */
  const toastEl = toast ? (
    <div className={`fixed top-16 left-3 right-3 z-40 px-4 py-2.5 rounded-xl text-[10px] font-bold ${
      toast.type === 'error' ? 'bg-red-500/15 border border-red-500/30 text-red-300' : 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
    }`} onClick={() => setToast(null)}>{toast.msg}
      <button className="absolute top-1.5 right-2 text-gray-500"><X className="w-3 h-3" /></button>
    </div>
  ) : null;
  useEffect(() => { if (toast) { const t = setTimeout(() => setToast(null), 3000); return () => clearTimeout(t); } }, [toast]);

  /* ═══════ BOARD VIEW ═══════ */
  if (!selected) {
    return (
      <div className="min-h-screen bg-black text-white pb-28" data-testid="v3-board">
        {toastEl}
        <div className="px-3 pt-24">
          <p className="text-[10px] text-gray-500 mb-3">Inizia un nuovo film o continua quelli in lavorazione</p>
          <div className="grid grid-cols-3 gap-2">
            <button onClick={createProject} disabled={loading}
              className="aspect-[2/3] rounded-xl border-2 border-dashed border-gray-700 hover:border-emerald-500/50 bg-gray-900/30 flex flex-col items-center justify-center gap-1.5 transition-all active:scale-95 disabled:opacity-50"
              data-testid="new-project-btn">
              <div className="w-8 h-8 rounded-full border-2 border-dashed border-gray-600 flex items-center justify-center">
                <Plus className="w-4 h-4 text-gray-500" />
              </div>
              <p className="text-[9px] font-bold text-gray-400">Nuovo Film</p>
              <p className="text-[6px] text-gray-600">Crea da zero</p>
            </button>
            {active.map(p => (
              <button key={p.id} onClick={() => selectProject(p)}
                className="aspect-[2/3] rounded-xl border border-gray-800 bg-gray-900/60 hover:border-emerald-500/30 flex flex-col overflow-hidden transition-all active:scale-95"
                data-testid={`project-card-${p.id}`}>
                <div className="flex-1 w-full bg-gray-800 relative">
                  {p.poster_url ? <img src={p.poster_url} alt="" className="w-full h-full object-cover" /> :
                    <div className="w-full h-full flex items-center justify-center"><Film className="w-5 h-5 text-gray-700" /></div>}
                  <div className="absolute top-1 right-1 px-1 py-0.5 rounded-full bg-black/70 text-[5px] font-bold text-emerald-400 uppercase">{p.pipeline_state || 'idea'}</div>
                </div>
                <div className="p-1.5">
                  <p className="text-[8px] font-bold text-white truncate">{p.title || 'Senza titolo'}</p>
                  <p className="text-[6px] text-gray-500">{GENRE_LABELS[p.genre] || p.genre || '—'}</p>
                </div>
              </button>
            ))}
          </div>
          {active.length === 0 && <p className="text-center text-gray-600 text-[10px] mt-4">Nessun film in lavorazione. Crea il tuo primo!</p>}
        </div>
      </div>
    );
  }

  /* ═══════ STEP RENDER ═══════ */
  const nextStep = V3_STEPS[stepIndex + 1]?.id;
  const prevStep = stepIndex > 0 ? V3_STEPS[stepIndex - 1]?.id : null;

  const renderPhase = () => {
    switch (currentStep) {
      case 'idea': return (
        <PhaseWrapper title="L'Idea" subtitle="Dai forma al tuo film" icon={Sparkles} color="amber">
          <div className="space-y-3">
            <input value={idea.title} onChange={e => { setIdea(v => ({ ...v, title: e.target.value })); markDirty(); }}
              placeholder="Titolo del film" className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm" data-testid="title-input" />
            <div className="grid grid-cols-2 gap-2">
              <select value={idea.genre} onChange={e => { setIdea(v => ({ ...v, genre: e.target.value, subgenre: '' })); markDirty(); }}
                className="rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]">
                {GENRES.map(g => <option key={g} value={g}>{GENRE_LABELS[g] || g}</option>)}
              </select>
              <select value={idea.subgenre} onChange={e => { setIdea(v => ({ ...v, subgenre: e.target.value })); markDirty(); }}
                className="rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]">
                <option value="">Sottogenere</option>
                {subgenreOptions.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <textarea value={idea.preplot} onChange={e => { setIdea(v => ({ ...v, preplot: e.target.value })); markDirty(); }}
              rows={4} placeholder="Pretrama del film..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]" data-testid="preplot-input" />

            {/* LOCANDINA */}
            <div className="p-3 rounded-xl bg-gray-800/20 border border-gray-700/30 space-y-2">
              <p className="text-[9px] text-gray-500 uppercase font-bold">Locandina AI</p>
              {selected.poster_url && <img src={selected.poster_url} alt="" className="w-20 h-28 rounded-lg border border-gray-700 object-cover mx-auto" />}
              {posterProgress > 0 && posterProgress < 100 ? (
                <div className="flex justify-center py-2"><ProgressCircle value={posterProgress} size={56} color="#F59E0B" /></div>
              ) : (
                <div className="space-y-2">
                  <div className="flex gap-1.5">
                    <button onClick={() => generatePoster('auto')} disabled={loading}
                      className="flex-1 text-[9px] py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 disabled:opacity-50" data-testid="poster-ai-auto">AI Auto</button>
                    <button onClick={() => generatePoster('custom')} disabled={loading || !posterPrompt.trim()}
                      className="flex-1 text-[9px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 hover:bg-purple-500/20 disabled:opacity-50" data-testid="poster-ai-custom">AI Custom</button>
                  </div>
                  <input value={posterPrompt} onChange={e => setPosterPrompt(e.target.value)}
                    placeholder="Prompt personalizzato locandina..." className="w-full rounded-lg border border-gray-800 bg-gray-950 px-2.5 py-2 text-[9px]" />
                </div>
              )}
            </div>

            {/* SCENEGGIATURA */}
            <div className="p-3 rounded-xl bg-gray-800/20 border border-gray-700/30 space-y-2">
              <p className="text-[9px] text-gray-500 uppercase font-bold">Sceneggiatura</p>
              {scriptProgress > 0 && scriptProgress < 100 ? (
                <div className="flex justify-center py-2"><ProgressCircle value={scriptProgress} size={56} color="#A855F7" /></div>
              ) : (
                <div className="space-y-2">
                  <div className="flex gap-1.5">
                    <button onClick={() => { setScreenplaySource('preplot'); }} className={`flex-1 text-[8px] py-1.5 rounded-lg border ${screenplaySource === 'preplot' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'border-gray-800 text-gray-500'}`}>Da pretrama</button>
                    <button onClick={() => { setScreenplaySource('custom_prompt'); }} className={`flex-1 text-[8px] py-1.5 rounded-lg border ${screenplaySource === 'custom_prompt' ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' : 'border-gray-800 text-gray-500'}`}>Prompt custom</button>
                  </div>
                  {screenplaySource === 'custom_prompt' && (
                    <textarea value={screenplayPrompt} onChange={e => setScreenplayPrompt(e.target.value)}
                      rows={3} placeholder="Prompt sceneggiatura..." className="w-full rounded-lg border border-gray-800 bg-gray-950 px-2.5 py-2 text-[9px]" />
                  )}
                  <button onClick={generateScreenplay} disabled={loading}
                    className="w-full text-[9px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20 disabled:opacity-50 font-bold" data-testid="gen-screenplay-btn">Genera Sceneggiatura</button>
                </div>
              )}
              {selected.screenplay_text && <pre className="whitespace-pre-wrap text-[8px] text-gray-400 mt-2 max-h-32 overflow-y-auto bg-gray-900/50 p-2 rounded-lg">{selected.screenplay_text}</pre>}
            </div>
          </div>
        </PhaseWrapper>
      );
      case 'hype': return (
        <PhaseWrapper title="Hype Machine" subtitle="Crea aspettativa strategica" icon={TrendingUp} color="orange">
          <div className="space-y-3">
            <textarea value={hypeNotes} onChange={e => { setHypeNotes(e.target.value); markDirty(); }}
              rows={3} placeholder="Strategia hype..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]" />
            <input type="number" value={hypeBudget} onChange={e => { setHypeBudget(e.target.value); markDirty(); }}
              placeholder="Budget hype ($)" className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]" />
            <SpeedupButtons stage="hype" onSpeedup={speedup} loading={loading} />
          </div>
        </PhaseWrapper>
      );
      case 'cast': return (
        <PhaseWrapper title="Il Cast" subtitle="Assembla la squadra" icon={Users} color="cyan">
          <div className="space-y-3">
            <textarea value={castNotes} onChange={e => { setCastNotes(e.target.value); markDirty(); }}
              rows={3} placeholder="Note cast..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]" />
            <select value={chemistryMode} onChange={e => { setChemistryMode(e.target.value); markDirty(); }}
              className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]">
              <option value="auto">Chimica auto</option><option value="manual">Chimica manuale</option><option value="off">Nessuna</option>
            </select>
          </div>
        </PhaseWrapper>
      );
      case 'prep': return (
        <PhaseWrapper title="Pre-Produzione" subtitle="Attrezzature e preparativi" icon={Camera} color="blue">
          <textarea value={prepNotes} onChange={e => { setPrepNotes(e.target.value); markDirty(); }}
            rows={3} placeholder="Note preparazione..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]" />
        </PhaseWrapper>
      );
      case 'ciak': return (
        <PhaseWrapper title="CIAK! Riprese" subtitle="Le riprese del film" icon={Clapperboard} color="red">
          <div className="space-y-3">
            <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/15 text-center">
              <Clock className="w-5 h-5 text-red-400 mx-auto mb-1" />
              <p className="text-[10px] text-gray-400">Avvia le riprese e passa al montaggio</p>
            </div>
            <SpeedupButtons stage="ciak" onSpeedup={speedup} loading={loading} />
          </div>
        </PhaseWrapper>
      );
      case 'finalcut': return (
        <PhaseWrapper title="Final Cut" subtitle="Post-produzione e montaggio" icon={Scissors} color="purple">
          <div className="space-y-3">
            <textarea value={finalcutNotes} onChange={e => { setFinalcutNotes(e.target.value); markDirty(); }}
              rows={3} placeholder="Note final cut..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px]" />
            <SpeedupButtons stage="finalcut" onSpeedup={speedup} loading={loading} />
          </div>
        </PhaseWrapper>
      );
      case 'marketing': return (
        <PhaseWrapper title="Sponsor & Marketing" subtitle="Finanzia e promuovi" icon={Megaphone} color="green">
          <div className="space-y-3">
            <p className="text-[9px] text-gray-500 uppercase font-bold">Pacchetti Marketing</p>
            {MARKETING_PACKAGES.map(pkg => {
              const sel = marketingPkgs.includes(pkg.name);
              return (
                <button key={pkg.name} onClick={() => { setMarketingPkgs(v => sel ? v.filter(x => x !== pkg.name) : [...v, pkg.name]); markDirty(); }}
                  className={`w-full flex items-center gap-2 p-2.5 rounded-lg border text-left transition-colors ${sel ? 'bg-green-500/10 border-green-500/40' : 'bg-gray-800/30 border-gray-700'}`}>
                  <Megaphone className={`w-4 h-4 shrink-0 ${sel ? 'text-green-400' : 'text-gray-600'}`} />
                  <div className="flex-1">
                    <p className={`text-[10px] font-bold ${sel ? 'text-green-400' : 'text-gray-300'}`}>{pkg.name}</p>
                    <p className="text-[8px] text-gray-500">${pkg.cost.toLocaleString()} | +{pkg.hype} hype</p>
                  </div>
                </button>
              );
            })}
            <div className="border-t border-gray-800 pt-3 space-y-2">
              <p className="text-[9px] text-gray-500 uppercase font-bold text-center">Come vuoi rilasciare il film?</p>
              <div className="grid grid-cols-2 gap-2">
                <button onClick={() => { setReleaseType('premiere'); markDirty(); }}
                  className={`p-3 rounded-xl border text-center ${releaseType === 'premiere' ? 'bg-yellow-500/15 border-yellow-500/50' : 'bg-gray-800/30 border-gray-700'}`}>
                  <Award className={`w-5 h-5 mx-auto mb-1 ${releaseType === 'premiere' ? 'text-yellow-400' : 'text-gray-600'}`} />
                  <p className={`text-[10px] font-bold ${releaseType === 'premiere' ? 'text-yellow-400' : 'text-gray-500'}`}>La Prima</p>
                </button>
                <button onClick={() => { setReleaseType('direct'); markDirty(); }}
                  className={`p-3 rounded-xl border text-center ${releaseType === 'direct' ? 'bg-emerald-500/15 border-emerald-500/50' : 'bg-gray-800/30 border-gray-700'}`}>
                  <Ticket className={`w-5 h-5 mx-auto mb-1 ${releaseType === 'direct' ? 'text-emerald-400' : 'text-gray-600'}`} />
                  <p className={`text-[10px] font-bold ${releaseType === 'direct' ? 'text-emerald-400' : 'text-gray-500'}`}>Diretto</p>
                </button>
              </div>
            </div>
          </div>
        </PhaseWrapper>
      );
      case 'distribution': return (
        <PhaseWrapper title="Distribuzione" subtitle="Zone e data di uscita" icon={Globe} color="blue">
          <div className="space-y-3">
            <p className="text-[9px] text-gray-500 uppercase font-bold">Data uscita</p>
            <div className="grid grid-cols-3 gap-1.5">
              {RELEASE_DATES.map(label => (
                <button key={label} onClick={() => { setReleaseDate(label); markDirty(); }}
                  className={`rounded-lg py-2 text-[9px] font-bold border ${releaseDate === label ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' : 'border-gray-800 text-gray-400'}`}>{label}</button>
              ))}
            </div>
            <label className="flex items-center gap-2 text-[10px] text-gray-400">
              <input type="checkbox" checked={world} onChange={e => { setWorld(e.target.checked); markDirty(); }} /> Distribuzione Mondiale
            </label>
          </div>
        </PhaseWrapper>
      );
      case 'release_pending': return (
        <PhaseWrapper title="STEP FINALE" subtitle="Riepilogo e conferma uscita" icon={Ticket} color="emerald">
          <div className="space-y-3">
            <div className="flex justify-center">
              {selected.poster_url ? <img src={selected.poster_url} alt="" className="w-24 h-36 rounded-lg border border-gray-700 object-cover shadow-lg" /> :
                <div className="w-24 h-36 rounded-lg border border-gray-700 bg-gray-800/50 flex items-center justify-center"><Film className="w-6 h-6 text-gray-600" /></div>}
            </div>
            <div className="p-3 rounded-xl bg-gray-800/30 border border-gray-700/50 text-center space-y-1">
              <p className="text-lg font-black text-white">{selected.title}</p>
              <p className="text-[10px] text-gray-400">{GENRE_LABELS[selected.genre] || selected.genre} | {releaseType === 'premiere' ? 'La Prima' : 'Diretto'} | {releaseDate}</p>
              <p className="text-[9px] text-gray-600">Qualita: n.d. (sara calcolata al rilascio)</p>
            </div>
            <button onClick={confirmRelease} disabled={loading || releasePhase !== 'idle'}
              className="w-full text-sm py-3 rounded-xl bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30 text-emerald-300 font-bold disabled:opacity-50"
              data-testid="confirm-release-btn">CONFERMA USCITA</button>
            <button onClick={discard} disabled={loading}
              className="w-full text-[10px] py-2 rounded-xl bg-red-500/5 border border-red-500/20 text-red-400/70 disabled:opacity-50">SCARTA FILM</button>
          </div>
        </PhaseWrapper>
      );
      default: return <p className="text-gray-500 text-sm p-4">Stato: {currentStep}</p>;
    }
  };

  /* ═══════ PROJECT VIEW ═══════ */
  return (
    <div className="min-h-screen bg-black text-white pb-28">
      {toastEl}
      <div className="pt-20">
        <FilmHeader film={selected} onBack={() => { setSelected(null); loadProjects(); }} onSaveDraft={saveDraft} dirty={dirty} loading={loading} />
        <StepperBar current={currentStep} />
        {renderPhase()}
        {currentStep !== 'release_pending' && (
          <div className="px-3 mt-2 flex gap-2">
            {prevStep && (
              <button onClick={() => saveStepAndAdvance(prevStep)} disabled={loading}
                className="flex-1 py-2.5 rounded-xl border border-gray-800 text-gray-400 text-[10px] font-bold disabled:opacity-30">Indietro</button>
            )}
            {nextStep && (
              <button onClick={() => saveStepAndAdvance(nextStep)} disabled={loading}
                className="flex-1 py-2.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold disabled:opacity-30"
                data-testid="advance-btn">{loading ? '...' : `Avanti → ${V3_STEPS[stepIndex + 1]?.label}`}</button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
