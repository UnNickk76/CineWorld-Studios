import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Film, ChevronLeft, Save, Sparkles, TrendingUp, Users, Camera, Clapperboard, Scissors, Megaphone, Globe, Ticket, Check, Award, X } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const STEPS = [
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

const GENRES = ['action','comedy','drama','horror','sci_fi','romance','thriller','animation','documentary','fantasy','adventure'];
const GENRE_LABELS = { action:'Azione', comedy:'Commedia', drama:'Dramma', horror:'Horror', sci_fi:'Fantascienza', romance:'Romantico', thriller:'Thriller', animation:'Animazione', documentary:'Documentario', fantasy:'Fantasy', adventure:'Avventura' };
const SUBGENRES = {
  action:['militare','spy','vendetta','arti marziali'], comedy:['demenziale','surreale','familiare','satirica'],
  drama:['romantico','psicologico','sociale','familiare'], horror:['slasher','soprannaturale','psicologico','zombie'],
  sci_fi:['cyberpunk','distopia','alieni','mecha'], romance:['tragico','proibito','teen romance','commedia romantica'],
  thriller:['crime','mistero','suspense','paranoia'], animation:['anime','CGI','2D classico','stop motion'],
  documentary:['true crime','storico','sociale','natura'], fantasy:['epico','dark fantasy','urban fantasy','mitologico'],
  adventure:['giungla','tesoro','survival','oceano'],
};
const RELEASE_OPTIONS = ['Immediato','6 ore','12 ore','24 ore','2 giorni','3 giorni'];
const MARKETING_PACKAGES = ['Teaser Digitale','Campagna Social','Stampa e TV','Tour Cast','Mega Globale'];

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

/* ═══════ STEPPER ═══════ */
const Stepper = ({ current }) => {
  const ci = STEPS.findIndex(s => s.id === current);
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) {
      const el = ref.current.querySelector(`[data-sid="${current}"]`);
      if (el) el.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
  }, [current]);
  return (
    <div ref={ref} className="flex items-center gap-0 overflow-x-auto py-2 px-1 scrollbar-hide" data-testid="v3-stepper">
      {STEPS.map((s, i) => {
        const Icon = s.icon;
        const done = i < ci;
        const active = i === ci;
        return (
          <React.Fragment key={s.id}>
            {i > 0 && <div className={`w-3 h-[2px] shrink-0 ${done || active ? 'bg-emerald-500' : 'bg-gray-800'}`} />}
            <div className="flex flex-col items-center shrink-0 gap-0.5" data-sid={s.id}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center border-2 transition-all ${
                active ? 'border-emerald-400 bg-emerald-500/15 text-emerald-400 scale-110' :
                done ? 'border-emerald-600 bg-emerald-500/10 text-emerald-400' :
                'border-gray-800 bg-gray-900/50 text-gray-600 opacity-40'
              }`}>
                {done ? <Check className="w-2.5 h-2.5" /> : <Icon className="w-2.5 h-2.5" />}
              </div>
              <span className={`text-[5px] font-bold uppercase tracking-wider ${
                active ? 'text-emerald-300' : done ? 'text-emerald-500/60' : 'text-gray-700'
              }`}>{s.label}</span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

/* ═══════ PROGRESS OVERLAY ═══════ */
const ProgressOverlay = ({ value }) => (
  <div className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center">
    <svg width="120" height="120">
      <circle cx="60" cy="60" r="50" stroke="#1f2937" strokeWidth="6" fill="none" />
      <circle cx="60" cy="60" r="50" stroke="#10b981" strokeWidth="6" fill="none"
        strokeDasharray={314} strokeDashoffset={314 - (value / 100) * 314}
        strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.4s ease', transform: 'rotate(-90deg)', transformOrigin: 'center' }} />
    </svg>
    <div className="absolute text-3xl font-bold text-emerald-400">{Math.floor(value)}%</div>
    <p className="text-gray-400 text-sm mt-6">Rilascio in corso...</p>
  </div>
);

/* ═══════ TOAST ═══════ */
const Toast = ({ msg, type, onClose }) => {
  useEffect(() => { const t = setTimeout(onClose, 3000); return () => clearTimeout(t); }, [onClose]);
  return (
    <div className={`fixed top-4 left-4 right-4 z-40 px-4 py-3 rounded-xl text-sm font-bold ${
      type === 'error' ? 'bg-red-500/15 border border-red-500/30 text-red-300' : 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
    }`}>
      {msg}
      <button onClick={onClose} className="absolute top-2 right-3 text-gray-500"><X className="w-4 h-4" /></button>
    </div>
  );
};

/* ═══════ MAIN ═══════ */
export default function PipelineV3() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showProgress, setShowProgress] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dirty, setDirty] = useState(false);
  const autosaveRef = useRef(null);

  // Form state
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
  const [marketingPackages, setMarketingPackages] = useState([]);
  const [releaseType, setReleaseType] = useState('direct');
  const [releaseDate, setReleaseDate] = useState('Immediato');
  const [world, setWorld] = useState(true);

  const showToast = (msg, type = 'ok') => setToast({ msg, type });

  // Load projects
  const loadProjects = useCallback(async () => {
    try {
      const data = await api('/films');
      setProjects(data.items || []);
    } catch (e) { showToast(e.message, 'error'); }
  }, []);

  // Sync form from project
  const syncForm = useCallback((p) => {
    if (!p) return;
    setIdea({ title: p.title || '', genre: p.genre || 'action', subgenre: p.subgenre || '', preplot: p.preplot || '' });
    setHypeNotes(p.hype_notes || ''); setHypeBudget(p.hype_budget || 0);
    setCastNotes(p.cast_notes || ''); setChemistryMode(p.chemistry_mode || 'auto');
    setPrepNotes(p.prep_notes || ''); setFinalcutNotes(p.finalcut_notes || '');
    setMarketingPackages(p.marketing_packages || []); setReleaseType(p.release_type || 'direct');
    setReleaseDate(p.release_date_label || 'Immediato'); setWorld(p.distribution_world ?? true);
    setPosterSource(p.poster_source || 'preplot'); setPosterPrompt(p.poster_prompt || '');
    setScreenplaySource(p.screenplay_source || 'preplot'); setScreenplayPrompt(p.screenplay_prompt || '');
    setDirty(false);
  }, []);

  const selectProject = useCallback(async (p) => {
    try {
      const data = await api(`/films/${p.id}`);
      setSelected(data);
      syncForm(data);
    } catch (e) { showToast(e.message, 'error'); }
  }, [syncForm]);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  const currentStep = selected?.pipeline_state || 'idea';
  const stepIndex = STEPS.findIndex(s => s.id === currentStep);
  const subgenreOptions = useMemo(() => SUBGENRES[idea.genre] || [], [idea.genre]);

  // Mark dirty on form changes
  const markDirty = () => setDirty(true);

  // Autosave every 10s if dirty
  useEffect(() => {
    if (!selected || !dirty) return;
    autosaveRef.current = setTimeout(async () => {
      try {
        await api(`/films/${selected.id}/save-idea`, 'POST', idea);
        setDirty(false);
      } catch {}
    }, 10000);
    return () => clearTimeout(autosaveRef.current);
  }, [dirty, selected, idea]);

  // API helpers
  const run = async (fn, msg) => {
    setLoading(true);
    try {
      await fn();
      if (msg) showToast(msg);
      await loadProjects();
    } catch (e) { showToast(e.message, 'error'); }
    setLoading(false);
  };

  const createProject = () => run(async () => {
    console.log('[V3] Creating new project...');
    const defaultIdea = { title: 'Nuovo Film', genre: 'comedy', subgenre: '', preplot: '' };
    const res = await api('/films/create', 'POST', defaultIdea);
    console.log('[V3] Created:', res.project?.id);
    setSelected(res.project);
    syncForm(res.project);
  }, 'Progetto creato!');

  const saveDraft = () => run(async () => {
    await api(`/films/${selected.id}/save-idea`, 'POST', idea);
    setDirty(false);
  }, 'Bozza salvata');

  const advance = (nextState) => run(async () => {
    // Save current step data first
    const st = currentStep;
    if (st === 'idea') await api(`/films/${selected.id}/save-idea`, 'POST', idea);
    if (st === 'hype') await api(`/films/${selected.id}/save-hype`, 'POST', { hype_notes: hypeNotes, budget: Number(hypeBudget || 0) });
    if (st === 'cast') await api(`/films/${selected.id}/save-cast`, 'POST', { cast_notes: castNotes, chemistry_mode: chemistryMode });
    if (st === 'prep') await api(`/films/${selected.id}/save-prep`, 'POST', { prep_notes: prepNotes });
    if (st === 'ciak') await api(`/films/${selected.id}/start-ciak`, 'POST');
    if (st === 'finalcut') await api(`/films/${selected.id}/save-finalcut`, 'POST', { finalcut_notes: finalcutNotes });
    if (st === 'marketing') {
      await api(`/films/${selected.id}/save-marketing`, 'POST', { packages: marketingPackages });
      await api(`/films/${selected.id}/set-release-type`, 'POST', { release_type: releaseType });
    }
    if (st === 'distribution') await api(`/films/${selected.id}/schedule-release`, 'POST', { release_date_label: releaseDate, world, zones: [] });
    // Advance
    await api(`/films/${selected.id}/advance`, 'POST', { next_state: nextState });
    const fresh = await api(`/films/${selected.id}`);
    setSelected(fresh);
    syncForm(fresh);
    setDirty(false);
  }, `Avanzato a ${nextState}`);

  const confirmRelease = async () => {
    if (loading || !selected?.id) return;
    setLoading(true); setShowProgress(true); setProgress(0);
    let p = 0;
    const timer = setInterval(() => { p += Math.random() * 6 + 2; setProgress(Math.min(100, p)); if (p >= 100) clearInterval(timer); }, 400);
    await new Promise(r => setTimeout(r, 2500));
    try {
      await api(`/films/${selected.id}/confirm-release`, 'POST');
      setProgress(100);
      await new Promise(r => setTimeout(r, 800));
      setShowProgress(false);
      showToast('Film rilasciato!');
      setTimeout(() => navigate('/'), 800);
    } catch (e) {
      setShowProgress(false);
      showToast(e.message, 'error');
    }
    setLoading(false);
  };

  const discard = () => run(async () => {
    await api(`/films/${selected.id}/discard`, 'POST');
    setSelected(null);
  }, 'Film scartato');

  // Active projects (not released/discarded)
  const active = projects.filter(p => !['released','completed','discarded'].includes(p.pipeline_state));

  /* ═══════ BOARD VIEW (no project selected) ═══════ */
  if (!selected) {
    return (
      <div className="min-h-screen bg-black text-white pb-28">
        {showProgress && <ProgressOverlay value={progress} />}
        {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
        <div className="px-4 pt-24">
          <p className="text-[10px] text-gray-500 mb-4">Inizia un nuovo film o continua quelli in lavorazione</p>

          <div className="grid grid-cols-3 gap-2">
            {/* NEW PROJECT CARD */}
            <button onClick={createProject} disabled={loading}
              className="aspect-[2/3] rounded-xl border-2 border-dashed border-gray-700 hover:border-emerald-500/50 bg-gray-900/30 flex flex-col items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50"
              data-testid="new-project-btn">
              <div className="w-10 h-10 rounded-full border-2 border-dashed border-gray-600 flex items-center justify-center">
                <Plus className="w-5 h-5 text-gray-500" />
              </div>
              <p className="text-[10px] font-bold text-gray-400">Nuovo Film</p>
              <p className="text-[7px] text-gray-600">Crea da zero</p>
            </button>

            {/* EXISTING PROJECT CARDS */}
            {active.map(p => (
              <button key={p.id} onClick={() => selectProject(p)}
                className="aspect-[2/3] rounded-xl border border-gray-800 bg-gray-900/60 hover:border-emerald-500/30 flex flex-col overflow-hidden transition-all active:scale-95"
                data-testid={`project-card-${p.id}`}>
                <div className="flex-1 w-full bg-gray-800 relative">
                  {p.poster_url ? (
                    <img src={p.poster_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Film className="w-6 h-6 text-gray-700" />
                    </div>
                  )}
                  <div className="absolute top-1 right-1 px-1.5 py-0.5 rounded-full bg-black/70 text-[6px] font-bold text-emerald-400 uppercase">
                    {p.pipeline_state || 'idea'}
                  </div>
                </div>
                <div className="p-1.5">
                  <p className="text-[9px] font-bold text-white truncate">{p.title || 'Senza titolo'}</p>
                  <p className="text-[7px] text-gray-500">{GENRE_LABELS[p.genre] || p.genre || '—'}</p>
                </div>
              </button>
            ))}
          </div>

          {active.length === 0 && (
            <p className="text-center text-gray-600 text-xs mt-6">Nessun film in lavorazione. Crea il tuo primo!</p>
          )}
        </div>
      </div>
    );
  }

  /* ═══════ STEP VIEWS ═══════ */
  const nextStep = STEPS[stepIndex + 1]?.id;

  const renderStep = () => {
    switch (currentStep) {
      case 'idea': return (
        <div className="space-y-3">
          <input value={idea.title} onChange={e => { setIdea(v => ({ ...v, title: e.target.value })); markDirty(); }}
            placeholder="Titolo del film" className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm" />
          <select value={idea.genre} onChange={e => { setIdea(v => ({ ...v, genre: e.target.value, subgenre: '' })); markDirty(); }}
            className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm">
            {GENRES.map(g => <option key={g} value={g}>{GENRE_LABELS[g] || g}</option>)}
          </select>
          {subgenreOptions.length > 0 && (
            <select value={idea.subgenre} onChange={e => { setIdea(v => ({ ...v, subgenre: e.target.value })); markDirty(); }}
              className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm">
              <option value="">Sottogenere</option>
              {subgenreOptions.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          )}
          <textarea value={idea.preplot} onChange={e => { setIdea(v => ({ ...v, preplot: e.target.value })); markDirty(); }}
            rows={4} placeholder="Pretrama del film..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm" />
        </div>
      );
      case 'hype': return (
        <div className="space-y-3">
          <textarea value={hypeNotes} onChange={e => { setHypeNotes(e.target.value); markDirty(); }}
            rows={3} placeholder="Strategia hype..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm" />
          <input type="number" value={hypeBudget} onChange={e => { setHypeBudget(e.target.value); markDirty(); }}
            placeholder="Budget hype ($)" className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm" />
        </div>
      );
      case 'cast': return (
        <div className="space-y-3">
          <textarea value={castNotes} onChange={e => { setCastNotes(e.target.value); markDirty(); }}
            rows={3} placeholder="Note cast..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm" />
          <select value={chemistryMode} onChange={e => { setChemistryMode(e.target.value); markDirty(); }}
            className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm">
            <option value="auto">Chimica auto</option>
            <option value="manual">Chimica manuale</option>
            <option value="off">Nessuna chimica</option>
          </select>
        </div>
      );
      case 'prep': return (
        <div className="space-y-3">
          <textarea value={prepNotes} onChange={e => { setPrepNotes(e.target.value); markDirty(); }}
            rows={3} placeholder="Note preparazione..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm" />
        </div>
      );
      case 'ciak': return (
        <div className="space-y-3">
          <p className="text-[10px] text-gray-400">Avvia le riprese. Il ciak completa e avanza al final cut.</p>
        </div>
      );
      case 'finalcut': return (
        <div className="space-y-3">
          <textarea value={finalcutNotes} onChange={e => { setFinalcutNotes(e.target.value); markDirty(); }}
            rows={3} placeholder="Note final cut..." className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm" />
        </div>
      );
      case 'marketing': return (
        <div className="space-y-3">
          <p className="text-[9px] text-gray-500 uppercase font-bold">Pacchetti Marketing</p>
          <div className="grid grid-cols-2 gap-2">
            {MARKETING_PACKAGES.map(name => (
              <button key={name} onClick={() => { setMarketingPackages(v => v.includes(name) ? v.filter(x => x !== name) : [...v, name]); markDirty(); }}
                className={`rounded-xl border p-2.5 text-[10px] text-left font-bold transition-all ${
                  marketingPackages.includes(name) ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300' : 'border-gray-800 bg-gray-900/50 text-gray-400'
                }`}>{name}</button>
            ))}
          </div>
          <p className="text-[9px] text-gray-500 uppercase font-bold mt-3">Tipo rilascio</p>
          <div className="grid grid-cols-2 gap-2">
            <button onClick={() => { setReleaseType('premiere'); markDirty(); }}
              className={`p-3 rounded-xl border text-center ${releaseType === 'premiere' ? 'border-yellow-500/50 bg-yellow-500/10' : 'border-gray-800'}`}>
              <Award className={`w-5 h-5 mx-auto mb-1 ${releaseType === 'premiere' ? 'text-yellow-400' : 'text-gray-600'}`} />
              <p className={`text-[10px] font-bold ${releaseType === 'premiere' ? 'text-yellow-400' : 'text-gray-500'}`}>La Prima</p>
            </button>
            <button onClick={() => { setReleaseType('direct'); markDirty(); }}
              className={`p-3 rounded-xl border text-center ${releaseType === 'direct' ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-gray-800'}`}>
              <Ticket className={`w-5 h-5 mx-auto mb-1 ${releaseType === 'direct' ? 'text-emerald-400' : 'text-gray-600'}`} />
              <p className={`text-[10px] font-bold ${releaseType === 'direct' ? 'text-emerald-400' : 'text-gray-500'}`}>Diretto</p>
            </button>
          </div>
        </div>
      );
      case 'distribution': return (
        <div className="space-y-3">
          <p className="text-[9px] text-gray-500 uppercase font-bold">Data uscita</p>
          <div className="grid grid-cols-3 gap-1.5">
            {RELEASE_OPTIONS.map(label => (
              <button key={label} onClick={() => { setReleaseDate(label); markDirty(); }}
                className={`rounded-lg py-2 text-[9px] font-bold border ${
                  releaseDate === label ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' : 'border-gray-800 text-gray-400'
                }`}>{label}</button>
            ))}
          </div>
          <label className="flex items-center gap-2 text-[10px] text-gray-400 mt-2">
            <input type="checkbox" checked={world} onChange={e => { setWorld(e.target.checked); markDirty(); }} className="rounded" />
            Distribuzione Mondiale
          </label>
        </div>
      );
      case 'release_pending': return (
        <div className="space-y-3">
          <div className="p-3 rounded-xl bg-gray-800/30 border border-gray-700/50 text-center space-y-1">
            <p className="text-[9px] text-gray-500 uppercase font-bold">Riepilogo</p>
            <p className="text-lg font-black text-white">{selected.title}</p>
            <p className="text-[10px] text-gray-400">{GENRE_LABELS[selected.genre] || selected.genre} | {releaseType === 'premiere' ? 'La Prima' : 'Diretto'} | {releaseDate}</p>
            <p className="text-[9px] text-gray-600">Qualita: n.d.</p>
          </div>
          <button onClick={confirmRelease} disabled={loading}
            className="w-full text-sm py-3 rounded-xl bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30 text-emerald-300 font-bold disabled:opacity-50"
            data-testid="confirm-release-btn">
            CONFERMA USCITA
          </button>
          <button onClick={discard} disabled={loading}
            className="w-full text-[10px] py-2 rounded-xl bg-red-500/5 border border-red-500/20 text-red-400/70 disabled:opacity-50"
            data-testid="discard-btn">
            SCARTA FILM
          </button>
        </div>
      );
      default: return <p className="text-gray-500 text-sm">Stato sconosciuto: {currentStep}</p>;
    }
  };

  /* ═══════ PROJECT VIEW ═══════ */
  return (
    <div className="min-h-screen bg-black text-white pb-28">
      {showProgress && <ProgressOverlay value={progress} />}
      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
      <div className="px-4 pt-24">
        {/* Header */}
        <div className="flex items-center gap-3 mb-3">
          <button onClick={() => { setSelected(null); loadProjects(); }} className="w-8 h-8 rounded-full bg-gray-900 border border-gray-800 flex items-center justify-center">
            <ChevronLeft className="w-4 h-4 text-gray-400" />
          </button>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-black truncate">{selected.title || 'Nuovo film'}</p>
            <p className="text-[9px] text-gray-500">{GENRE_LABELS[selected.genre] || selected.genre}</p>
          </div>
          <button onClick={saveDraft} disabled={loading || !dirty}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[9px] font-bold border transition-all ${
              dirty ? 'border-amber-500/30 bg-amber-500/10 text-amber-400' : 'border-gray-800 bg-gray-900 text-gray-600'
            } disabled:opacity-30`} data-testid="save-draft-btn">
            <Save className="w-3 h-3" />
            {dirty ? 'Salva bozza' : 'Salvato'}
          </button>
        </div>

        <Stepper current={currentStep} />

        {/* Step content */}
        <div className="mt-3 rounded-2xl border border-gray-800 bg-gray-950/50 p-4">
          <p className="text-[9px] text-gray-500 uppercase font-bold mb-3">
            {STEPS[stepIndex]?.label || currentStep}
          </p>
          {renderStep()}
        </div>

        {/* Navigation */}
        {currentStep !== 'release_pending' && (
          <div className="mt-3 flex gap-2">
            {stepIndex > 0 && (
              <button onClick={() => { const prev = STEPS[stepIndex - 1]?.id; if (prev) advance(prev); }}
                disabled={loading}
                className="flex-1 py-2.5 rounded-xl border border-gray-800 text-gray-400 text-[10px] font-bold disabled:opacity-30">
                Indietro
              </button>
            )}
            {nextStep && (
              <button onClick={() => advance(nextStep)} disabled={loading}
                className="flex-1 py-2.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold disabled:opacity-30"
                data-testid="advance-btn">
                {loading ? '...' : `Avanti → ${STEPS[stepIndex + 1]?.label}`}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
