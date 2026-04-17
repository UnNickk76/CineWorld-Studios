import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Sparkles, Film, RefreshCw } from 'lucide-react';
import { PhaseWrapper, GENRES, GENRE_LABELS, SUBGENRE_MAP, LOCATION_TAGS, ProgressCircle, v3api } from './V3Shared';

/*
  Flusso sequenziale:
  FASE 1: Titolo + Genere + Sottogeneri + Pretrama + Ambientazione → OK (freeze se <1 sottogenere)
  FASE 2: Locandina AI (pretrama default, prompt opzionale) → OK (freeze se no locandina)
  FASE 3: Sceneggiatura (AI da pretrama / manuale 100+ chars) → OK (freeze se vuota)
  Dopo fase 3 → bottone Avanti HYPE in alto si sfreeza
*/

export const IdeaPhase = ({ film, onRefresh, toast, onDirty }) => {
  // Determine which sub-phase we're in based on saved data
  const hasSavedIdea = !!(film.genre && film.preplot && film.preplot.length >= 50 && (film.subgenres?.length > 0 || film.subgenre));
  const hasPoster = !!film.poster_url;
  const hasScreenplay = !!(film.screenplay_text && film.screenplay_text.length > 50);

  const initialPhase = hasScreenplay ? 3 : hasPoster ? 2 : hasSavedIdea ? 1 : 0;
  const [subPhase, setSubPhase] = useState(initialPhase);

  // Form state
  const [title, setTitle] = useState(film.title || '');
  const [genre, setGenre] = useState(film.genre || 'action');
  const [subgenres, setSubgenres] = useState(film.subgenres || (film.subgenre ? [film.subgenre] : []));
  const [preplot, setPreplot] = useState(film.preplot || '');
  const [locations, setLocations] = useState(film.locations || []);
  const [posterPrompt, setPosterPrompt] = useState('');
  const [showPromptInput, setShowPromptInput] = useState(false);
  const [manualScreenplay, setManualScreenplay] = useState('');
  const [screenplayMode, setScreenplayMode] = useState('ai'); // ai | manual
  const [loading, setLoading] = useState('');
  const [posterProgress, setPosterProgress] = useState(0);
  const [scriptProgress, setScriptProgress] = useState(0);
  const [posterZoomed, setPosterZoomed] = useState(false);
  const zoomTimerRef = useRef(null);
  const posterInt = useRef(null);
  const scriptInt = useRef(null);

  // Auto-close zoom after 20s
  useEffect(() => {
    if (posterZoomed) {
      zoomTimerRef.current = setTimeout(() => setPosterZoomed(false), 20000);
      return () => clearTimeout(zoomTimerRef.current);
    }
  }, [posterZoomed]);

  const subgenreOptions = useMemo(() => SUBGENRE_MAP[genre] || [], [genre]);
  const mark = () => onDirty?.();

  // Phase 0 validation
  const phase0Valid = title.trim().length >= 2 && genre && subgenres.length >= 1 && preplot.trim().length >= 50;

  // ═══ FASE 0: OK → save idea ═══
  const confirmPhase0 = async () => {
    setLoading('phase0');
    try {
      await v3api(`/films/${film.id}/save-idea`, 'POST', { title, genre, subgenre: subgenres.join(', '), preplot, subgenres, locations });
      await onRefresh();
      setSubPhase(1);
      toast?.('Idea salvata!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading('');
  };

  // ═══ FASE 1: Locandina ═══
  const generatePoster = async () => {
    setLoading('poster'); setPosterProgress(5);
    posterInt.current = setInterval(() => setPosterProgress(p => p >= 90 ? p : p + Math.random() * 10), 800);
    try {
      const source = showPromptInput && posterPrompt.trim() ? 'custom_prompt' : 'preplot';
      const custom = showPromptInput ? posterPrompt.trim() : '';
      await v3api(`/films/${film.id}/generate-poster`, 'POST', { source, custom_prompt: custom });
      setPosterProgress(100); clearInterval(posterInt.current);
      await onRefresh();
      toast?.('Locandina creata!');
    } catch (e) { clearInterval(posterInt.current); setPosterProgress(0); toast?.(e.message, 'error'); }
    setLoading('');
  };

  const confirmPhase1 = () => { if (film.poster_url) setSubPhase(2); };

  // ═══ FASE 2: Sceneggiatura ═══
  const generateScreenplay = async () => {
    setLoading('screenplay'); setScriptProgress(5);
    scriptInt.current = setInterval(() => setScriptProgress(p => p >= 90 ? p : p + Math.random() * 8), 1000);
    try {
      await v3api(`/films/${film.id}/generate-screenplay`, 'POST', { source: 'preplot', custom_prompt: '' });
      setScriptProgress(100); clearInterval(scriptInt.current);
      await onRefresh();
      toast?.('Sceneggiatura generata!');
    } catch (e) { clearInterval(scriptInt.current); setScriptProgress(0); toast?.(e.message, 'error'); }
    setLoading('');
  };

  const saveManualScreenplay = async () => {
    setLoading('screenplay');
    try {
      await v3api(`/films/${film.id}/generate-screenplay`, 'POST', { source: 'custom_prompt', custom_prompt: manualScreenplay });
      await onRefresh();
      toast?.('Sceneggiatura salvata!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading('');
  };

  const screenplayReady = !!(film.screenplay_text && film.screenplay_text.length > 50) || manualScreenplay.length >= 100;
  const confirmPhase2 = async () => {
    if (screenplayMode === 'manual' && manualScreenplay.length >= 100 && !film.screenplay_text) {
      await saveManualScreenplay();
    }
    setSubPhase(3);
  };

  const toggleLoc = (l) => { setLocations(v => v.includes(l) ? v.filter(x => x !== l) : [...v, l]); mark(); };
  const toggleSubgenre = (s) => { setSubgenres(v => v.includes(s) ? v.filter(x => x !== s) : v.length < 3 ? [...v, s] : v); mark(); };

  // OK button component
  const OkButton = ({ enabled, onClick, loading: btnLoading }) => (
    <button onClick={onClick} disabled={!enabled || !!btnLoading}
      className={`px-5 py-1.5 rounded-lg text-xs font-black transition-all ${
        enabled ? 'bg-amber-400 text-black hover:bg-amber-300 active:scale-95' : 'bg-gray-800 text-gray-600 cursor-not-allowed'
      } disabled:opacity-50`}>
      {btnLoading ? '...' : 'OK'}
    </button>
  );

  return (
    <PhaseWrapper title="L'Idea" subtitle="Dai forma al tuo progetto cinematografico" icon={Sparkles} color="amber">
      <div className="space-y-3">

        {/* ═══ SEMPRE VISIBILE: Titolo + Genere + Sottogeneri + Pretrama + Ambientazione ═══ */}
        <input value={title} onChange={e => { setTitle(e.target.value); mark(); }}
          placeholder="Titolo del film" className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm text-white placeholder-gray-600"
          disabled={subPhase > 0} data-testid="title-input" />

        <select value={genre} onChange={e => { setGenre(e.target.value); setSubgenres([]); mark(); }}
          disabled={subPhase > 0}
          className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px] text-white disabled:opacity-50">
          {GENRES.map(g => <option key={g} value={g}>{GENRE_LABELS[g]}</option>)}
        </select>

        {subgenreOptions.length > 0 && (
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-[8px] text-gray-500 uppercase font-bold">Sottogeneri</span>
              <span className={`text-[8px] ${subgenres.length > 0 ? 'text-cyan-400' : 'text-gray-600'}`}>{subgenres.length}/3</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {subgenreOptions.map(s => (
                <button key={s} onClick={() => subPhase === 0 && toggleSubgenre(s)} disabled={subPhase > 0}
                  className={`px-2 py-1 rounded-lg text-[8px] font-bold border transition-all ${
                    subgenres.includes(s) ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'border-gray-800 text-gray-500 hover:border-gray-600'
                  } disabled:opacity-50`}>{s}</button>
              ))}
            </div>
          </div>
        )}

        <div>
          <div className="flex justify-between mb-1">
            <span className="text-[8px] text-gray-500 uppercase font-bold">Pretrama</span>
            <span className={`text-[8px] ${preplot.length >= 50 ? 'text-emerald-400' : 'text-gray-600'}`}>{preplot.length}/50 min</span>
          </div>
          <textarea value={preplot} onChange={e => { setPreplot(e.target.value); mark(); }}
            rows={4} placeholder="Descrivi la trama del tuo film (min 50 caratteri)..."
            disabled={subPhase > 0}
            className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px] text-white placeholder-gray-600 disabled:opacity-50" data-testid="preplot-input" />
        </div>

        <div>
          <span className="text-[8px] text-gray-500 uppercase font-bold">Ambientazione</span>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {LOCATION_TAGS.map(l => (
              <button key={l} onClick={() => subPhase === 0 && toggleLoc(l)} disabled={subPhase > 0}
                className={`px-2 py-1 rounded-lg text-[8px] font-bold border transition-all ${
                  locations.includes(l) ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' : 'border-gray-800 text-gray-500 hover:border-gray-600'
                } disabled:opacity-50`}>{l}</button>
            ))}
          </div>
        </div>

        {/* OK Fase 0 */}
        {subPhase === 0 && (
          <div className="flex justify-end">
            <OkButton enabled={phase0Valid} onClick={confirmPhase0} loading={loading === 'phase0'} />
          </div>
        )}

        {/* ═══ FASE 1: LOCANDINA (solo dopo OK fase 0) ═══ */}
        {subPhase >= 1 && (
          <div className={`p-3 rounded-xl border space-y-2 ${subPhase === 1 ? 'bg-gray-800/20 border-gray-700/30' : 'bg-gray-900/20 border-gray-800/20 opacity-60'}`}>
            <div className="flex justify-between items-center">
              <span className="text-[8px] text-gray-500 uppercase font-bold">Locandina AI</span>
              {film.poster_url && subPhase === 1 && (
                <button onClick={generatePoster} disabled={!!loading}
                  className="flex items-center gap-1 text-[7px] text-amber-400 font-bold">
                  <RefreshCw className="w-3 h-3" /> Ricrea
                </button>
              )}
            </div>

            {film.poster_url && (
              <img src={film.poster_url} alt="" className="w-24 h-36 rounded-lg border border-gray-700 object-cover mx-auto shadow-lg cursor-pointer hover:brightness-110 transition"
                onClick={() => setPosterZoomed(true)} data-testid="poster-zoom-trigger" />
            )}

            {subPhase === 1 && !film.poster_url && (
              <>
                {posterProgress > 0 && posterProgress < 100 ? (
                  <div className="flex flex-col items-center py-3 gap-2">
                    <ProgressCircle value={posterProgress} size={56} color="#F59E0B" />
                    <p className="text-[8px] text-amber-400/70 text-center">La locandina sta prendendo vita... attendi la sua comparsa!</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-[8px] text-gray-400">La locandina viene generata dalla tua pretrama. Vuoi aggiungere indicazioni?</p>
                    {!showPromptInput ? (
                      <div className="flex gap-1.5">
                        <button onClick={generatePoster} disabled={!!loading}
                          className="flex-1 text-[8px] py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 disabled:opacity-30 font-bold">Genera da pretrama</button>
                        <button onClick={() => setShowPromptInput(true)}
                          className="flex-1 text-[8px] py-2 rounded-lg border border-gray-700 text-gray-400 hover:border-gray-600 font-bold">+ Prompt</button>
                      </div>
                    ) : (
                      <div className="space-y-1.5">
                        <input value={posterPrompt} onChange={e => setPosterPrompt(e.target.value)}
                          placeholder="Descrivi la locandina che immagini..."
                          className="w-full rounded-lg border border-gray-800 bg-gray-950 px-2.5 py-1.5 text-[8px] text-white placeholder-gray-600" />
                        <div className="flex gap-1.5">
                          <button onClick={generatePoster} disabled={!!loading}
                            className="flex-1 text-[8px] py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 disabled:opacity-30 font-bold">Genera con prompt</button>
                          <button onClick={() => { setShowPromptInput(false); setPosterPrompt(''); }}
                            className="text-[8px] py-2 px-3 rounded-lg border border-gray-700 text-gray-500">Annulla</button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {/* OK Fase 1 */}
            {subPhase === 1 && (
              <div className="flex justify-end pt-1">
                <OkButton enabled={!!film.poster_url} onClick={confirmPhase1} />
              </div>
            )}
          </div>
        )}

        {/* ═══ FASE 2: SCENEGGIATURA (solo dopo OK locandina) ═══ */}
        {subPhase >= 2 && (
          <div className={`p-3 rounded-xl border space-y-2 ${subPhase === 2 ? 'bg-gray-800/20 border-gray-700/30' : 'bg-gray-900/20 border-gray-800/20 opacity-60'}`}>
            <span className="text-[8px] text-gray-500 uppercase font-bold">Sceneggiatura</span>

            {/* Show existing screenplay */}
            {film.screenplay_text && (
              <div className="max-h-48 overflow-y-auto rounded-lg bg-gray-900/50 p-3 border border-gray-800">
                <pre className="whitespace-pre-wrap text-[9px] text-gray-300 leading-relaxed font-sans">{film.screenplay_text}</pre>
              </div>
            )}

            {subPhase === 2 && !film.screenplay_text && (
              <>
                {scriptProgress > 0 && scriptProgress < 100 ? (
                  <div className="flex flex-col items-center py-3 gap-2">
                    <ProgressCircle value={scriptProgress} size={56} color="#A855F7" />
                    <p className="text-[8px] text-purple-400/70 text-center">La storia prende forma...</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex gap-1.5">
                      <button onClick={() => setScreenplayMode('ai')}
                        className={`flex-1 text-[7px] py-1.5 rounded-lg border font-bold ${
                          screenplayMode === 'ai' ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' : 'border-gray-800 text-gray-500'
                        }`}>AI da pretrama</button>
                      <button onClick={() => setScreenplayMode('manual')}
                        className={`flex-1 text-[7px] py-1.5 rounded-lg border font-bold ${
                          screenplayMode === 'manual' ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' : 'border-gray-800 text-gray-500'
                        }`}>Scrivi manualmente</button>
                    </div>

                    {screenplayMode === 'ai' && (
                      <button onClick={generateScreenplay} disabled={!!loading}
                        className="w-full text-[8px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20 disabled:opacity-30 font-bold">
                        Genera Sceneggiatura AI
                      </button>
                    )}

                    {screenplayMode === 'manual' && (
                      <div className="space-y-1.5">
                        <div className="flex justify-between">
                          <span className="text-[7px] text-gray-500">Scrivi la tua sceneggiatura</span>
                          <span className={`text-[7px] ${manualScreenplay.length >= 100 ? 'text-emerald-400' : 'text-gray-600'}`}>{manualScreenplay.length}/100 min</span>
                        </div>
                        <textarea value={manualScreenplay} onChange={e => setManualScreenplay(e.target.value)}
                          rows={6} placeholder="Scrivi qui la sceneggiatura del film..."
                          className="w-full rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-[9px] text-white placeholder-gray-600 leading-relaxed" />
                        <button onClick={saveManualScreenplay} disabled={manualScreenplay.length < 100 || !!loading}
                          className="w-full text-[8px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 disabled:opacity-30 font-bold">
                          {loading === 'screenplay' ? '...' : 'Salva Sceneggiatura'}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {/* OK Fase 2 */}
            {subPhase === 2 && (
              <div className="flex justify-end pt-1">
                <OkButton enabled={!!(film.screenplay_text && film.screenplay_text.length > 50) || manualScreenplay.length >= 100} onClick={confirmPhase2} loading={loading === 'screenplay'} />
              </div>
            )}
          </div>
        )}

        {/* DONE message */}
        {subPhase >= 3 && (
          <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/15 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <p className="text-[9px] text-emerald-400 font-bold">Idea completa! Premi Avanti HYPE in alto.</p>
          </div>
        )}
      </div>

      {/* Poster Zoom Overlay */}
      {posterZoomed && film.poster_url && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/85 backdrop-blur-sm"
          onClick={() => { setPosterZoomed(false); clearTimeout(zoomTimerRef.current); }}
          data-testid="poster-zoom-overlay">
          <img src={film.poster_url} alt={film.title || ''} className="max-w-[85vw] max-h-[85vh] rounded-2xl shadow-2xl object-contain border-2 border-white/10"
            style={{ animation: 'zoomIn 0.3s ease-out' }} />
          <div className="absolute bottom-6 left-0 right-0 text-center">
            <p className="text-[10px] text-gray-400">Tocca per chiudere</p>
          </div>
        </div>
      )}
    </PhaseWrapper>
  );
};
