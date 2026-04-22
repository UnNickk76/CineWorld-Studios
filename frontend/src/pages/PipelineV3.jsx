import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Plus, Film, ChevronLeft, Save, X, Eye } from 'lucide-react';
import CinematicReleaseOverlay from '../components/CinematicReleaseOverlay';
import { FilmRollAnimation, CrowdRushAnimation, MontageRollAnimation, LaPrimaAnimation } from '../components/v3/PipelineAnimations';
import { V3_STEPS, StepperBar, GENRE_LABELS, v3api } from '../components/v3/V3Shared';
import { IdeaPhase } from '../components/v3/IdeaPhase';
import { CastPhase } from '../components/v3/CastPhase';
import { HypePhase, PrepPhase, CiakPhase, FinalCutPhase, MarketingPhase, LaPrimaPhase, DistributionPhase, StepFinale, DiscardFilmButton } from '../components/v3/Phases';
import TrailerGeneratorCard from '../components/TrailerGeneratorCard';
import { AuthContext } from '../contexts';

export default function PipelineV3() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { api, user } = useContext(AuthContext) || {};
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [dirty, setDirty] = useState(false);
  const autosaveRef = useRef(null);

  // Release flow
  const [releasePhase, setReleasePhase] = useState('idle');
  const [releaseProgress, setReleaseProgress] = useState(0);
  const progressRef = useRef(null);
  const releaseCompletedRef = useRef(false); // ANTI-LOOP: once true, never show overlay again
  const [clockTick, setClockTick] = useState(0);
  const [prevoto, setPrevoto] = useState(null);
  const [wowAnimation, setWowAnimation] = useState(null); // 'film_roll' | 'crowd_rush' | 'montage_roll' | 'la_prima' | null
  const pendingAdvanceRef = useRef(null);

  // Tick every 5s for real-time checks (CIAK timer)
  useEffect(() => {
    const t = setInterval(() => setClockTick(c => c + 1), 5000);
    return () => clearInterval(t);
  }, []);

  const showToast = (msg, type = 'ok') => setToast({ msg: String(msg || ''), type });
  const markDirty = () => setDirty(true);

  const loadProjects = useCallback(async () => {
    try { const d = await v3api('/films'); setProjects(d.items || []); } catch {}
  }, []);

  const refreshSelected = useCallback(async () => {
    if (!selected?.id) return null;
    try { const d = await v3api(`/films/${selected.id}`); setSelected(d); setDirty(false); return d; } catch { return null; }
  }, [selected?.id]);

  const selectProject = useCallback(async (p) => {
    try {
      // Reset release state when selecting a new project
      setReleasePhase('idle');
      releaseCompletedRef.current = false;
      const d = await v3api(`/films/${p.id}`);
      setSelected(d); setDirty(false);
    } catch (e) { showToast(e.message, 'error'); }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);
  useEffect(() => { if (toast) { const t = setTimeout(() => setToast(null), 3000); return () => clearTimeout(t); } }, [toast]);
  useEffect(() => { return () => { if (progressRef.current) clearInterval(progressRef.current); }; }, []);

  // Auto-select a project when ?p=<project_id> is passed in URL (used by "Genera Trailer"
  // action from FilmActionsSheet to jump directly to the trailer step in read-only mode).
  const autoSelectRef = useRef(false);
  useEffect(() => {
    const pid = searchParams.get('p');
    if (!pid || autoSelectRef.current || selected) return;
    autoSelectRef.current = true;
    (async () => {
      try {
        const d = await v3api(`/films/${pid}`);
        if (d) {
          setReleasePhase('idle');
          releaseCompletedRef.current = false;
          setSelected(d);
          // Clear the query param so refreshing doesn't re-trigger
          setSearchParams({}, { replace: true });
        }
      } catch (_) { /* ignore */ }
    })();
  }, [searchParams, selected, setSearchParams]);

  const currentStep = selected?.pipeline_state || 'idea';
  const stepIndex = V3_STEPS.findIndex(s => s.id === currentStep);

  // Read-only navigation: player can click any step to preview it.
  // null = follow currentStep; otherwise override the rendered phase with this id.
  const [viewStepOverride, setViewStepOverride] = useState(null);
  // Reset override whenever the selected film or its currentStep changes
  useEffect(() => { setViewStepOverride(null); }, [selected?.id, currentStep]);
  const viewStep = viewStepOverride || currentStep;
  const viewIndex = V3_STEPS.findIndex(s => s.id === viewStep);
  const isReadOnly = viewStep !== currentStep;

  // Fetch pre-voto CWSv when film or step changes
  useEffect(() => {
    if (!selected?.id) { setPrevoto(null); return; }
    // Don't fetch for the very first state without data
    if (currentStep === 'idea' && !selected?.preplot) { setPrevoto(null); return; }
    v3api(`/films/${selected.id}/prevoto`).then(r => setPrevoto(r)).catch(() => setPrevoto(null));
  }, [selected?.id, currentStep, selected?.updated_at]);


  const createProject = async () => {
    setLoading(true);
    try {
      const res = await v3api('/films/create', 'POST', { title: 'Nuovo Film', genre: 'comedy', preplot: '' });
      setSelected(res.project); setDirty(false); await loadProjects(); showToast('Progetto V3 creato!');
    } catch (e) { showToast(e.message, 'error'); }
    setLoading(false);
  };

  const saveDraft = async () => {
    if (!selected?.id) return;
    setLoading(true);
    try { await v3api(`/films/${selected.id}/save-idea`, 'POST', { title: selected.title || '', genre: selected.genre || 'comedy', subgenre: '', preplot: selected.preplot || '' }); setDirty(false); showToast('Bozza salvata'); }
    catch (e) { showToast(e.message, 'error'); }
    setLoading(false);
  };

  const advance = async (nextState) => {
    if (!selected?.id) return;

    // Trigger WOW animations for specific transitions
    const WOW_TRANSITIONS = {
      'hype': 'film_roll',      // idea → hype: film rolling
      'cast': 'crowd_rush',     // hype → cast: folla agli studi
      'finalcut': 'montage_roll', // ciak → finalcut: montaggio
    };

    const animationType = WOW_TRANSITIONS[nextState];
    if (animationType) {
      // Store both nextState AND pid to avoid stale closure issues
      pendingAdvanceRef.current = { nextState, pid: selected.id };
      setWowAnimation(animationType);
      return; // Animation will call onWowAnimationComplete when done
    }

    await completeAdvance(nextState, selected.id);
  };

  const completeAdvance = async (nextState, pid) => {
    if (!pid) pid = selected?.id;
    if (!pid) return;
    setLoading(true);
    try {
      await v3api(`/films/${pid}/advance`, 'POST', { next_state: nextState });
      // Refresh using pid directly (avoids stale closure)
      const d = await v3api(`/films/${pid}`);
      setSelected(d); setDirty(false);
    } catch (e) { showToast(String(e?.message || 'Errore avanzamento'), 'error'); }
    setLoading(false);
  };

  const onWowAnimationComplete = useCallback(async () => {
    const pending = pendingAdvanceRef.current;
    setWowAnimation(null);
    pendingAdvanceRef.current = null;
    if (!pending) return;
    const { nextState, pid } = pending;
    if (!nextState || !pid) return;
    // Inline advance call — no stale closure dependency
    setLoading(true);
    try {
      await v3api(`/films/${pid}/advance`, 'POST', { next_state: nextState });
      const d = await v3api(`/films/${pid}`);
      setSelected(d); setDirty(false);
    } catch (e) { setToast({ msg: String(e?.message || 'Errore'), type: 'error' }); }
    setLoading(false);
  }, []);

  const confirmRelease = async () => {
    if (releasePhase !== 'idle' || !selected?.id || releaseCompletedRef.current) return;
    releaseCompletedRef.current = true; // Lock immediately — prevents any re-trigger

    // Call API first (no animation until success confirmed)
    setReleasePhase('calling');
    try {
      const res = await v3api(`/films/${selected.id}/confirm-release`, 'POST');
      if (!res?.success) {
        showToast(String(res?.detail || 'Errore nel rilascio'), 'error');
        setReleasePhase('idle');
        releaseCompletedRef.current = false;
        return;
      }
    } catch (e) {
      showToast(String(e.message || 'Errore nel rilascio'), 'error');
      setReleasePhase('idle');
      releaseCompletedRef.current = false;
      return;
    }

    // API succeeded — NOW show La Prima animation then cinema animation
    setWowAnimation('la_prima');
  };

  const onWowDone = useCallback(() => {
    setReleasePhase('idle');
    releaseCompletedRef.current = false;
    setSelected(null);
    setTimeout(() => navigate('/dashboard'), 100);
  }, [navigate]);

  const discard = async () => {
    if (!selected?.id) return;
    setLoading(true);
    try { await v3api(`/films/${selected.id}/discard`, 'POST'); setSelected(null); await loadProjects(); showToast('Film scartato'); }
    catch (e) { showToast(e.message, 'error'); }
    setLoading(false);
  };

  const active = projects.filter(p => !['released','completed','discarded'].includes(p.pipeline_state));
  const nextStep = V3_STEPS[stepIndex + 1]?.id;
  const prevStep = stepIndex > 0 ? V3_STEPS[stepIndex - 1]?.id : null;

  // eslint-disable-next-line
  const canAdvance = (() => {
    void clockTick; // trigger re-eval on tick
    if (!selected) return false;
    switch (currentStep) {
      case 'idea':
        return !!(selected.screenplay_text && selected.screenplay_text.length > 50 && selected.poster_url);
      case 'hype': {
        const hp = selected.hype_progress || 0;
        return hp >= 100;
      }
      case 'cast':
        return !!(selected.cast?.director || selected.cast?.actors?.length > 0);
      case 'prep':
        return !!(selected.film_format && selected.shooting_days > 0);
      case 'ciak': {
        if (!selected.ciak_complete_at) return false;
        return new Date(selected.ciak_complete_at) <= new Date();
      }
      case 'finalcut': {
        if (!selected.finalcut_complete_at) return false;
        return new Date(selected.finalcut_complete_at) <= new Date();
      }
      case 'marketing':
        return !!(selected.marketing_completed);
      case 'la_prima': {
        if (!selected.release_type) return false; // must choose La Prima vs Diretto
        if (selected.release_type === 'premiere') {
          const prem = selected.premiere || {};
          if (!prem.city || !prem.datetime) return false;
          // NOTE: advance to distribution no longer waits for 24h. Only the final
          // release (step 'uscita') is blocked until premiere.datetime + 24h.
        }
        return true;
      }
      case 'distribution':
        return true;
      default:
        return true;
    }
  })();

  // ═══ WOW ANIMATIONS ═══
  if (wowAnimation === 'film_roll') {
    return <FilmRollAnimation onComplete={onWowAnimationComplete} />;
  }
  if (wowAnimation === 'crowd_rush') {
    return <CrowdRushAnimation onComplete={onWowAnimationComplete} studioName={selected?.production_house_name || "STUDIO'S"} />;
  }
  if (wowAnimation === 'montage_roll') {
    return <MontageRollAnimation onComplete={onWowAnimationComplete} />;
  }
  if (wowAnimation === 'la_prima') {
    return <LaPrimaAnimation film={selected} onComplete={() => { setWowAnimation(null); setReleasePhase('wow'); }} />;
  }
  if (wowAnimation === 'la_prima_live') {
    // Triggered when film enters LIVE window (premiere.datetime reached).
    // No release side-effect: just show the wow then return to normal.
    return <LaPrimaAnimation film={selected} onComplete={() => setWowAnimation(null)} />;
  }

  // ═══ OVERLAY STATES ═══
  if (releasePhase === 'calling') {
    return (
      <div className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center">
        <div className="w-10 h-10 border-4 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" />
        <p className="text-gray-400 text-sm mt-6">Invio al sistema...</p>
      </div>
    );
  }
  if (releasePhase === 'wow' && selected) {
    return <CinematicReleaseOverlay film={selected} releaseType="cinema" onComplete={onWowDone} />;
  }
  // Safety: if releasePhase got stuck, reset it
  if (releasePhase !== 'idle' && releasePhase !== 'calling' && !selected) {
    setReleasePhase('idle');
    releaseCompletedRef.current = false;
  }

  // ═══ TOAST ═══
  const toastEl = toast ? (
    <div className={`fixed top-28 left-3 right-3 z-40 px-4 py-2.5 rounded-xl text-[10px] font-bold ${
      toast.type === 'error' ? 'bg-red-500/15 border border-red-500/30 text-red-300' : 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
    }`} onClick={() => setToast(null)}>{toast.msg}<button className="absolute top-1.5 right-2"><X className="w-3 h-3 text-gray-500" /></button></div>
  ) : null;

  // ═══ BOARD VIEW ═══
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
                  <p className="text-[6px] text-gray-500">{GENRE_LABELS[p.genre] || p.genre || ''}</p>
                </div>
              </button>
            ))}
          </div>
          {active.length === 0 && <p className="text-center text-gray-600 text-[10px] mt-4">Nessun film. Crea il tuo primo!</p>}
        </div>
      </div>
    );
  }

  // ═══ PHASE CONTENT ═══
  const phaseProps = { film: selected, onRefresh: refreshSelected, toast: showToast, onDirty: markDirty, readOnly: isReadOnly };
  const renderPhase = () => {
    switch (viewStep) {
      case 'idea': return <IdeaPhase {...phaseProps} />;
      case 'hype': return <HypePhase {...phaseProps} />;
      case 'cast': return <CastPhase {...phaseProps} />;
      case 'prep': return <PrepPhase {...phaseProps} />;
      case 'ciak': return <CiakPhase {...phaseProps} />;
      case 'finalcut': return <FinalCutPhase {...phaseProps} />;
      case 'marketing': return <MarketingPhase {...phaseProps} />;
      case 'la_prima': return <LaPrimaPhase {...phaseProps} onTriggerAnimation={() => setWowAnimation('la_prima_live')} />;
      case 'distribution': return <DistributionPhase {...phaseProps} />;
      case 'release_pending': return <StepFinale film={selected} onConfirm={confirmRelease} onDiscard={discard} loading={loading || releasePhase !== 'idle'} releaseType={selected.release_type || 'direct'} readOnly={isReadOnly} />;
      default: return <p className="text-gray-500 text-sm p-4">Stato: {viewStep}</p>;
    }
  };

  // ═══ PROJECT VIEW ═══
  return (
    <div className="min-h-screen bg-black text-white pb-28" style={{ overscrollBehavior: 'none' }}>
      {toastEl}
      <div className="pt-20">
        {/* Header */}
        <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-800/50">
          <button onClick={() => { setSelected(null); loadProjects(); }} className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center shrink-0" data-testid="back-btn">
            <ChevronLeft className="w-3.5 h-3.5 text-gray-400" />
          </button>
          {selected.poster_url ? <img src={selected.poster_url} alt="" className="w-9 h-12 rounded object-cover border border-gray-700 shrink-0" /> :
            <div className="w-9 h-12 rounded bg-gray-800 border border-gray-700 flex items-center justify-center shrink-0"><Film className="w-3.5 h-3.5 text-gray-600" /></div>}
          <div className="flex-1 min-w-0">
            <h2 className="text-xs font-bold text-white truncate">{selected.title || 'Nuovo Progetto'}</h2>
            <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
              <span className="text-[7px] px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium uppercase">{GENRE_LABELS[selected.genre] || selected.genre}</span>
              {prevoto?.prevoto ? (
                <span className={`text-[7px] px-1.5 py-0.5 rounded font-black border ${
                  prevoto.prevoto >= 8 ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25' :
                  prevoto.prevoto >= 6 ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25' :
                  prevoto.prevoto >= 4 ? 'bg-amber-500/15 text-amber-400 border-amber-500/25' :
                  'bg-red-500/15 text-red-400 border-red-500/25'
                }`} data-testid="prevoto-badge">CWSv {prevoto.display || prevoto.prevoto}</span>
              ) : (
                <span className="text-[6px] px-1 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/15 font-bold">V3</span>
              )}
              {selected.film_duration_label && (
                <span className="text-[6px] px-1 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">{selected.film_duration_label}</span>
              )}
              {selected.budget_tier && (
                <span className={`text-[6px] px-1 py-0.5 rounded font-bold border ${
                  selected.budget_tier === 'mega' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                  selected.budget_tier === 'blockbuster' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                  selected.budget_tier === 'big' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                  'bg-gray-800 text-gray-400 border-gray-700'
                }`}>{selected.budget_tier.toUpperCase()}</span>
              )}
              {selected.from_purchased_screenplay && (
                <span className={`text-[6px] px-1 py-0.5 rounded font-bold border inline-flex items-center gap-0.5 ${
                  selected.purchased_screenplay_mode === 'veloce'
                    ? 'bg-orange-500/15 text-orange-300 border-orange-500/30'
                    : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                }`} title={`Da Sceneggiatura Pronta (${selected.purchased_screenplay_source || '?'})`}>
                  📖 {(selected.purchased_screenplay_mode || 'PRONTA').toUpperCase()}
                </span>
              )}
            </div>
          </div>
          <button onClick={saveDraft} disabled={loading || !dirty}
            className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[7px] font-bold border shrink-0 ${
              dirty ? 'border-amber-500/30 bg-amber-500/10 text-amber-400' : 'border-gray-800 bg-gray-900 text-gray-600'
            } disabled:opacity-30`} data-testid="save-draft-btn">
            <Save className="w-2.5 h-2.5" /> {dirty ? 'Salva' : 'OK'}
          </button>
        </div>

        {/* Sticky Advance Button — only when viewing the current step */}
        {!isReadOnly && currentStep !== 'release_pending' && nextStep && (
          <div className="sticky top-[88px] z-30 px-3 py-1.5 bg-black/90 backdrop-blur-sm border-b border-gray-800/30 flex gap-2">
            {prevStep && (
              <button onClick={() => advance(prevStep)} disabled={loading}
                className="px-3 py-1.5 rounded-lg border border-gray-800 text-gray-500 text-[8px] font-bold disabled:opacity-30">Indietro</button>
            )}
            {/* Veloce Fast Track: at hype state, jump directly to distribution */}
            {selected.auto_advance_veloce && currentStep === 'hype' ? (
              <button
                onClick={async () => {
                  if (!selected.poster_url) {
                    showToast('Crea prima la locandina', 'error');
                    return;
                  }
                  setLoading(true);
                  try {
                    const API = process.env.REACT_APP_BACKEND_URL;
                    const token = localStorage.getItem('cineworld_token');
                    const resp = await fetch(`${API}/api/purchased-screenplays/veloce-fast-track/${selected.id}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    });
                    const r = await resp.json();
                    if (!resp.ok) throw new Error(r.detail || 'Errore');
                    if (r?.project) { setSelected(r.project); showToast(r.message || 'Fast-track completato'); }
                    else { await refreshSelected(); showToast('Fast-track completato'); }
                  } catch (e) {
                    showToast(String(e?.message || 'Errore fast-track'), 'error');
                  }
                  setLoading(false);
                }}
                disabled={loading || !selected.poster_url}
                className="flex-1 py-1.5 rounded-lg text-[9px] font-bold bg-orange-500/20 border border-orange-500/40 text-orange-300 disabled:opacity-30"
                data-testid="veloce-fast-track-btn">
                {loading ? '...' : !selected.poster_url ? 'Crea prima la locandina' : '⚡ Fast-Track → Distribuzione'}
              </button>
            ) : (
              <button onClick={() => advance(nextStep)} disabled={loading || !canAdvance}
                className={`flex-1 py-1.5 rounded-lg text-[9px] font-bold disabled:opacity-30 ${
                  canAdvance ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400' : 'bg-gray-800/50 border border-gray-700/30 text-gray-600 cursor-not-allowed'
                }`} data-testid="advance-btn">
                {loading ? '...' : !canAdvance ? `Completa ${V3_STEPS[stepIndex]?.label} prima` : `Avanti ${V3_STEPS[stepIndex + 1]?.label}`}
              </button>
            )}
          </div>
        )}

        {/* Read-only view banner — shown when previewing a non-current step */}
        {isReadOnly && (
          <div className="sticky top-[88px] z-30 px-3 py-2 bg-blue-500/10 backdrop-blur-sm border-b border-blue-500/20 flex items-center gap-2" data-testid="readonly-banner">
            <Eye className="w-3.5 h-3.5 text-blue-400 shrink-0" />
            <p className="text-[9px] text-blue-300 flex-1 leading-tight">
              Anteprima: <span className="font-bold">{V3_STEPS[viewIndex]?.label}</span>
              {viewIndex < stepIndex ? ' (gia completato)' : viewIndex > stepIndex ? ' (da fare)' : ''}
            </p>
            <button onClick={() => setViewStepOverride(null)}
              className="px-2.5 py-1 rounded-full bg-blue-500/20 border border-blue-500/40 text-[8px] font-bold text-blue-300"
              data-testid="return-current-step-btn">
              Torna al tuo step
            </button>
          </div>
        )}

        <StepperBar current={viewStep} onSelect={(sid, idx) => {
          // Allow clicking to preview any step; if user picks current step → clear override
          if (sid === currentStep) setViewStepOverride(null);
          else setViewStepOverride(sid);
        }} />
        <div className={isReadOnly ? 'pointer-events-none opacity-80 select-none relative' : ''} data-testid={isReadOnly ? 'phase-readonly-wrapper' : 'phase-active-wrapper'}>
          {isReadOnly && (
            <div className="absolute inset-0 bg-transparent z-10 pointer-events-auto" onClick={(e) => e.preventDefault()} />
          )}
          {renderPhase()}
        </div>

        {/* ═══ TRAILER AI ALWAYS-AVAILABLE in read-only navigation ═══ */}
        {isReadOnly && selected?.user_id === user?.id && api && (
          <div className="px-3 mt-3" data-testid="trailer-always-available">
            <div className="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-wider text-sky-400 font-black">
              <span className="w-1 h-3 bg-sky-400 rounded-full" />
              Trailer AI · disponibile in qualsiasi momento
            </div>
            <TrailerGeneratorCard
              contentId={selected.id}
              contentTitle={selected.title}
              contentGenre={selected.genre || ''}
              contentStatus={selected.status || selected.pipeline_state || ''}
              api={api}
              userCredits={user?.cinecrediti ?? user?.cinecredits ?? 0}
              canGenerate={true}
              isGuest={!!user?.is_guest}
              onGenerated={refreshSelected}
            />
          </div>
        )}

        {/* Pipeline Events Log */}
        {selected.pipeline_events && selected.pipeline_events.length > 0 && (
          <div className="px-3 py-2 space-y-1">
            <p className="text-[7px] text-gray-500 uppercase font-bold">Eventi di Produzione ({selected.pipeline_events.length})</p>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {[...selected.pipeline_events].reverse().map((ev, i) => (
                <div key={i} className={`flex items-start gap-1.5 px-2 py-1 rounded text-[8px] border ${
                  ev.type === 'positive' ? 'bg-emerald-500/5 border-emerald-500/15 text-emerald-400' :
                  ev.type === 'negative' ? 'bg-red-500/5 border-red-500/15 text-red-400' :
                  'bg-amber-500/5 border-amber-500/15 text-amber-400'
                }`}>
                  <span>{ev.type === 'positive' ? '+' : ev.type === 'negative' ? '-' : '~'}</span>
                  <span className="flex-1">{ev.text}</span>
                  <span className="text-[6px] text-gray-600 shrink-0">{ev.phase}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Scarta Film — in every step except idea */}
        {currentStep !== 'idea' && currentStep !== 'release_pending' && (
          <div className="px-3 pb-4">
            <DiscardFilmButton filmId={selected.id} onDiscard={() => { setSelected(null); loadProjects(); showToast('Film scartato'); }} />
          </div>
        )}
      </div>
    </div>
  );
}
