import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Film, ChevronLeft, Save, X } from 'lucide-react';
import CinematicReleaseOverlay from '../components/CinematicReleaseOverlay';
import { V3_STEPS, StepperBar, GENRE_LABELS, v3api } from '../components/v3/V3Shared';
import { IdeaPhase } from '../components/v3/IdeaPhase';
import { CastPhase } from '../components/v3/CastPhase';
import { HypePhase, PrepPhase, CiakPhase, FinalCutPhase, MarketingPhase, LaPrimaPhase, DistributionPhase, StepFinale, DiscardFilmButton } from '../components/v3/Phases';

export default function PipelineV3() {
  const navigate = useNavigate();
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
    try { const d = await v3api(`/films/${p.id}`); setSelected(d); setDirty(false); } catch (e) { showToast(e.message, 'error'); }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);
  useEffect(() => { if (toast) { const t = setTimeout(() => setToast(null), 3000); return () => clearTimeout(t); } }, [toast]);
  useEffect(() => { return () => { if (progressRef.current) clearInterval(progressRef.current); }; }, []);

  const currentStep = selected?.pipeline_state || 'idea';
  const stepIndex = V3_STEPS.findIndex(s => s.id === currentStep);

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
    setLoading(true);
    try {
      await v3api(`/films/${selected.id}/advance`, 'POST', { next_state: nextState });
      await refreshSelected(); setDirty(false);
    } catch (e) { showToast(e.message, 'error'); }
    setLoading(false);
  };

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

    // API succeeded — NOW show the cinema animation
    setReleasePhase('wow');
  };

  const onWowDone = useCallback(() => {
    setReleasePhase('done');
    setSelected(null);
    // Navigate to dashboard
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
        if (selected.release_type === 'premiere') {
          const pp = selected.prima_progress || 0;
          return pp >= 100;
        }
        return true;
      }
      case 'distribution':
        return true;
      default:
        return true;
    }
  })();

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
  const phaseProps = { film: selected, onRefresh: refreshSelected, toast: showToast, onDirty: markDirty };
  const renderPhase = () => {
    switch (currentStep) {
      case 'idea': return <IdeaPhase {...phaseProps} />;
      case 'hype': return <HypePhase {...phaseProps} />;
      case 'cast': return <CastPhase {...phaseProps} />;
      case 'prep': return <PrepPhase {...phaseProps} />;
      case 'ciak': return <CiakPhase {...phaseProps} />;
      case 'finalcut': return <FinalCutPhase {...phaseProps} />;
      case 'marketing': return <MarketingPhase {...phaseProps} />;
      case 'la_prima': return <LaPrimaPhase {...phaseProps} />;
      case 'distribution': return <DistributionPhase {...phaseProps} />;
      case 'release_pending': return <StepFinale film={selected} onConfirm={confirmRelease} onDiscard={discard} loading={loading || releasePhase !== 'idle'} releaseType={selected.release_type || 'direct'} />;
      default: return <p className="text-gray-500 text-sm p-4">Stato: {currentStep}</p>;
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
            </div>
          </div>
          <button onClick={saveDraft} disabled={loading || !dirty}
            className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[7px] font-bold border shrink-0 ${
              dirty ? 'border-amber-500/30 bg-amber-500/10 text-amber-400' : 'border-gray-800 bg-gray-900 text-gray-600'
            } disabled:opacity-30`} data-testid="save-draft-btn">
            <Save className="w-2.5 h-2.5" /> {dirty ? 'Salva' : 'OK'}
          </button>
        </div>

        {/* Sticky Advance Button */}
        {currentStep !== 'release_pending' && nextStep && (
          <div className="sticky top-[88px] z-30 px-3 py-1.5 bg-black/90 backdrop-blur-sm border-b border-gray-800/30 flex gap-2">
            {prevStep && (
              <button onClick={() => advance(prevStep)} disabled={loading}
                className="px-3 py-1.5 rounded-lg border border-gray-800 text-gray-500 text-[8px] font-bold disabled:opacity-30">Indietro</button>
            )}
            <button onClick={() => advance(nextStep)} disabled={loading || !canAdvance}
              className={`flex-1 py-1.5 rounded-lg text-[9px] font-bold disabled:opacity-30 ${
                canAdvance ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400' : 'bg-gray-800/50 border border-gray-700/30 text-gray-600 cursor-not-allowed'
              }`} data-testid="advance-btn">
              {loading ? '...' : !canAdvance ? `Completa ${V3_STEPS[stepIndex]?.label} prima` : `Avanti ${V3_STEPS[stepIndex + 1]?.label}`}
            </button>
          </div>
        )}

        <StepperBar current={currentStep} />
        {renderPhase()}

        {/* Scarta Film — in every step except idea */}
        {currentStep !== 'idea' && currentStep !== 'release_pending' && (
          <div className="px-3 pb-4">
            <DiscardFilmButton filmId={selected.id} onDiscard={() => { setSelected(null); refreshProjects(); showToast('Film scartato'); }} />
          </div>
        )}
      </div>
    </div>
  );
}
