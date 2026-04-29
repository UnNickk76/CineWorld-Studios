import React, { useState, useMemo, useRef, useEffect, useContext } from 'react';
import { Sparkles, Film, RefreshCw, Building2, MapPin, Trees, Landmark, Home, Trash2, RotateCcw } from 'lucide-react';
import { PhaseWrapper, GENRES, GENRE_LABELS, SUBGENRE_MAP, ProgressCircle, v3api } from './V3Shared';
import { AuthContext } from '../../contexts';
import TrailerGeneratorCard from '../TrailerGeneratorCard';
import CineConfirm from './CineConfirm';
import { LocationCoherenceBar } from './LocationCoherenceBar';

/*
  Flusso sequenziale:
  FASE 1: Titolo + Genere + Sottogeneri + Pretrama + Ambientazione → OK (freeze se <1 sottogenere)
  FASE 2: Locandina AI (pretrama default, prompt opzionale) → OK (freeze se no locandina)
  FASE 3: Sceneggiatura (AI da pretrama / manuale 100+ chars) → OK (freeze se vuota)
  Dopo fase 3 → bottone Avanti HYPE in alto si sfreeza
*/

const LOC_CAT_META = {
  my_studio: { label: 'Il Mio Studio', icon: Home, color: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-500/10' },
  studios:   { label: 'Studios',       icon: Building2, color: 'text-cyan-400',    border: 'border-cyan-500/30',    bg: 'bg-cyan-500/10' },
  cities:    { label: 'Citt\u00E0',    icon: MapPin,    color: 'text-amber-400',   border: 'border-amber-500/30',   bg: 'bg-amber-500/10' },
  nature:    { label: 'Natura',        icon: Trees,     color: 'text-green-400',   border: 'border-green-500/30',   bg: 'bg-green-500/10' },
  historical:{ label: 'Storici',       icon: Landmark,  color: 'text-purple-400',  border: 'border-purple-500/30',  bg: 'bg-purple-500/10' },
};

const MAX_LOCATIONS = 999; // No hard limit — coerenza valutata da AI/sweet spot

export const IdeaPhase = ({ film, onRefresh, toast, onDirty, readOnly = false }) => {
  const { user, api } = useContext(AuthContext) || {};
  const isGuest = !!user?.is_guest;
  // Determine which sub-phase we're in based on saved data.
  // NOTE: il film e' "idea-saved" SOLO quando ha tutti i campi base + locations + budget_tier
  // (altrimenti l'utente non puo' modificare location/budget se sono ancora vuoti).
  const hasSavedIdea = !!(
    film.genre && film.preplot && film.preplot.length >= 50 &&
    (film.subgenres?.length > 0 || film.subgenre) &&
    (film.locations?.length > 0) &&
    film.budget_tier
  );
  const hasPoster = !!film.poster_url;
  const hasScreenplay = !!(film.screenplay_text && film.screenplay_text.length > 50);

  // If poster missing (e.g. purchased screenplay pre-filled screenplay but no poster yet),
  // force subPhase 1 regardless of screenplay state — the player must create the poster.
  const initialPhase = hasScreenplay && hasPoster ? 3 : hasPoster ? 2 : hasSavedIdea ? 1 : 0;
  const [subPhase, setSubPhase] = useState(initialPhase);

  // Form state
  const [title, setTitle] = useState(film.title || '');
  const [genre, setGenre] = useState(film.genre || 'action');
  const [subgenres, setSubgenres] = useState(film.subgenres || (film.subgenre ? [film.subgenre] : []));
  const [preplot, setPreplot] = useState(film.preplot || '');
  const [locations, setLocations] = useState(film.locations || []);
  const [budgetTier, setBudgetTier] = useState(film.budget_tier || 'mid');
  const [vmRating, setVmRating] = useState(film.vm_rating || (
    (film.genre || '').toLowerCase() === 'erotic' ? 'vm16' :
    (film.genre || '').toLowerCase() === 'horror' ? 'vm14' : null
  ));
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

  // Real locations picker
  const [allLocations, setAllLocations] = useState([]);
  const [ownStudio, setOwnStudio] = useState(null);
  const [activeCat, setActiveCat] = useState('studios');
  const [locQuery, setLocQuery] = useState('');

  useEffect(() => {
    // Fetch real locations list (studios, cities, nature, historical)
    (async () => {
      try {
        const res = await api.get('/locations');
        const list = Array.isArray(res.data) ? res.data : (res.data?.locations || []);
        setAllLocations(list);
      } catch {}
      // Detect own production studio from infrastructure
      try {
        const res = await api.get('/infrastructure/my');
        const items = res.data?.infrastructure || res.data || [];
        const studio = (items || []).find(i => i?.type === 'production_studio');
        if (studio) setOwnStudio({
          name: studio.custom_name || studio.name || user?.production_house_name || 'Il Mio Studio',
          cost_per_day: 0,
          category: 'my_studio',
          is_own: true,
        });
      } catch {}
    })();
  }, [api, user?.production_house_name]);

  // Auto-close zoom after 20s
  useEffect(() => {
    if (posterZoomed) {
      zoomTimerRef.current = setTimeout(() => setPosterZoomed(false), 20000);
      return () => clearTimeout(zoomTimerRef.current);
    }
  }, [posterZoomed]);

  const subgenreOptions = useMemo(() => SUBGENRE_MAP[genre] || [], [genre]);
  const mark = () => onDirty?.();

  // Auto VM rating quando il genere cambia (override possibile manuale)
  useEffect(() => {
    if (vmRating) return;  // gia' impostato dal player
    const g = (genre || '').toLowerCase();
    if (g === 'erotic') setVmRating('vm16');
    else if (g === 'horror') setVmRating('vm14');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [genre]);

  // Phase 0 validation
  const phase0Valid = title.trim().length >= 2 && genre && subgenres.length >= 1 && preplot.trim().length >= 50;

  // ═══ FASE 0: OK → save idea ═══
  const confirmPhase0 = async () => {
    setLoading('phase0');
    try {
      await v3api(`/films/${film.id}/save-idea`, 'POST', { title, genre, subgenre: subgenres.join(', '), preplot, subgenres, locations, budget_tier: budgetTier, vm_rating: vmRating });
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
    } catch (e) {
      clearInterval(posterInt.current); setPosterProgress(0);
      // Provider-failed → show friendly retry toast
      const isProviderFail = e?.status === 503 || /image_provider_failed|provider/i.test(e?.message || '');
      if (isProviderFail && typeof window !== 'undefined' && window.sonner) {
        // fallback path handled below via toast API
      }
      try {
        // Try sonner-style toast with action if available
        const { toast: sonnerToast } = await import('sonner');
        sonnerToast.error(isProviderFail ? 'Generazione immagine non riuscita' : (e.message || 'Errore'), {
          description: isProviderFail ? 'Il provider AI non ha risposto. Puoi riprovare o tornare indietro.' : undefined,
          action: isProviderFail ? { label: 'Riprova', onClick: () => generatePoster() } : undefined,
          cancel: isProviderFail ? { label: 'Indietro', onClick: () => {} } : undefined,
        });
      } catch {
        toast?.(e.message || 'Errore locandina', 'error');
      }
    }
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

  // Sub-phase 3 → 4: user either generates trailer or skips
  const skipTrailer = () => setSubPhase(4);
  const confirmTrailerAndProceed = () => setSubPhase(4);

  const toggleLoc = (l) => { setLocations(v => v.includes(l) ? v.filter(x => x !== l) : [...v, l]); mark(); };
  const toggleSubgenre = (s) => { setSubgenres(v => v.includes(s) ? v.filter(x => x !== s) : v.length < 3 ? [...v, s] : v); mark(); };

  // OK button component
  const OkButton = ({ enabled, onClick, loading: btnLoading, testid }) => (
    <button onClick={onClick} disabled={!enabled || !!btnLoading}
      className={`px-5 py-1.5 rounded-lg text-xs font-black transition-all ${
        enabled ? 'bg-amber-400 text-black hover:bg-amber-300 active:scale-95' : 'bg-gray-800 text-gray-600 cursor-not-allowed'
      } disabled:opacity-50`}
      data-testid={testid}>
      {btnLoading ? '...' : 'OK'}
    </button>
  );

  return (
    <PhaseWrapper title="L'Idea" subtitle="Dai forma al tuo progetto cinematografico" icon={Sparkles} color="amber">
      <div className="space-y-3">

        {/* ═══ SAGA HEADER — mini-timeline + fan base bonus + cliffhanger reminder ═══ */}
        {film.saga_id && (film.saga_chapter_number || 0) >= 1 && (
          <SagaPipelineHeader film={film} api={api} />
        )}

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
          <p className="text-[7px] text-amber-500/70 mt-1">⚠ Parolacce e linguaggio esplicito vengono automaticamente censurati. Le bestemmie sono vietate.</p>
        </div>

        {/* VM Rating selector */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[8px] text-gray-500 uppercase font-bold">Classificazione (Visione)</span>
            {vmRating && <span className="text-[8px] font-bold text-red-400">{vmRating.toUpperCase()}</span>}
          </div>
          <div className="grid grid-cols-4 gap-1" data-testid="vm-rating-selector">
            {[
              { v: null,   label: 'Tutti', color: 'border-gray-700 text-gray-400' },
              { v: 'vm14', label: 'VM 14', color: 'border-yellow-600/50 text-yellow-300' },
              { v: 'vm16', label: 'VM 16', color: 'border-orange-600/60 text-orange-300' },
              { v: 'vm18', label: 'VM 18', color: 'border-red-600/70 text-red-300' },
            ].map(opt => (
              <button key={String(opt.v)}
                onClick={() => { setVmRating(opt.v); mark(); }}
                disabled={subPhase > 0}
                data-testid={`vm-rating-${opt.v || 'free'}`}
                className={`text-[8px] py-1.5 rounded-lg border font-bold transition disabled:opacity-50 ${vmRating === opt.v ? `${opt.color} bg-white/5` : 'border-gray-800 text-gray-600'}`}>
                {opt.label}
              </button>
            ))}
          </div>
          <p className="text-[7px] text-gray-500 mt-1">
            {(genre || '').toLowerCase() === 'erotic' && 'Genere erotico → minimo VM16. '}
            {(genre || '').toLowerCase() === 'horror' && 'Genere horror → consigliato VM14+. '}
            La classificazione influenza pubblico, distribuzione TV e fasce orarie.
          </p>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[8px] text-gray-500 uppercase font-bold">Location di Ripresa</span>
            <span className={`text-[8px] ${locations.length > 0 ? 'text-cyan-400' : 'text-gray-600'}`}>
              {locations.length} selezionate
            </span>
          </div>

          {/* Category tabs */}
          <div className="flex gap-1 mb-2 overflow-x-auto pb-1" data-testid="location-categories">
            {Object.entries(LOC_CAT_META)
              .filter(([k]) => k !== 'my_studio' || !!ownStudio)
              .map(([key, meta]) => {
                const Icon = meta.icon;
                const count = key === 'my_studio'
                  ? (ownStudio && locations.includes(ownStudio.name) ? 1 : 0)
                  : allLocations.filter(l => l.category === key && locations.includes(l.name)).length;
                return (
                  <button key={key} onClick={() => subPhase === 0 && setActiveCat(key)} disabled={subPhase > 0}
                    className={`shrink-0 flex items-center gap-1 px-2 py-1 rounded-lg text-[8px] font-bold border transition-all disabled:opacity-50 ${
                      activeCat === key ? `${meta.bg} ${meta.border} ${meta.color}` : 'border-gray-800 text-gray-500 hover:border-gray-600'
                    }`}
                    data-testid={`location-cat-${key}`}>
                    <Icon className="w-3 h-3" />
                    <span>{meta.label}</span>
                    {count > 0 && <span className={`${meta.color} font-black`}>{count}</span>}
                  </button>
                );
              })}
          </div>

          {/* Search (not on my_studio) */}
          {activeCat !== 'my_studio' && subPhase === 0 && (
            <input value={locQuery} onChange={e => setLocQuery(e.target.value)}
              placeholder="Cerca location..."
              className="w-full rounded-lg border border-gray-800 bg-gray-950 px-2.5 py-1.5 text-[9px] text-white placeholder-gray-600 mb-1.5" />
          )}

          {/* Location list */}
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1" data-testid="location-list">
            {activeCat === 'my_studio' && ownStudio && (() => {
              const selected = locations.includes(ownStudio.name);
              const meta = LOC_CAT_META.my_studio;
              const Icon = meta.icon;
              return (
                <button onClick={() => subPhase === 0 && toggleLoc(ownStudio.name)} disabled={subPhase > 0}
                  className={`w-full flex items-center justify-between p-1.5 rounded-lg border transition-all disabled:opacity-50 ${
                    selected ? `${meta.bg} ${meta.border}` : 'border-gray-800 hover:border-gray-700 bg-gray-900/30'
                  }`}
                  data-testid={`location-option-${ownStudio.name}`}>
                  <span className="flex items-center gap-1.5">
                    <Icon className={`w-3 h-3 ${meta.color}`} />
                    <span className={`text-[9px] font-bold ${selected ? meta.color : 'text-gray-300'}`}>{ownStudio.name}</span>
                  </span>
                  <span className="text-[8px] text-emerald-400 font-black">GRATIS</span>
                </button>
              );
            })()}
            {activeCat !== 'my_studio' && allLocations
              .filter(l => l.category === activeCat)
              .filter(l => !locQuery || l.name.toLowerCase().includes(locQuery.toLowerCase()))
              .map(l => {
                const selected = locations.includes(l.name);
                const meta = LOC_CAT_META[l.category] || LOC_CAT_META.studios;
                // Costo crescente: 6+ → +60%, 11+ → +140%, 16+ → +250%
                const idxIfSelected = selected ? locations.indexOf(l.name) : locations.length;
                const costMult = idxIfSelected < 5 ? 1.0 : idxIfSelected < 10 ? 1.6 : idxIfSelected < 15 ? 2.4 : 3.5;
                const adjCost = Math.round((l.cost_per_day * costMult) / 1000);
                return (
                  <button key={l.name} onClick={() => subPhase === 0 && toggleLoc(l.name)}
                    disabled={subPhase > 0}
                    className={`w-full flex items-center justify-between p-1.5 rounded-lg border transition-all disabled:opacity-40 ${
                      selected ? `${meta.bg} ${meta.border}` : 'border-gray-800 hover:border-gray-700 bg-gray-900/20'
                    }`}
                    data-testid={`location-option-${l.name}`}>
                    <span className={`text-[9px] font-bold truncate ${selected ? meta.color : 'text-gray-300'}`}>{l.name}</span>
                    {isGuest ? (
                      <span className="shrink-0 ml-2 flex items-center gap-1">
                        <s className="text-[7px] text-gray-500">${(l.cost_per_day / 1000).toFixed(0)}K/g</s>
                        <span className="text-[8px] text-emerald-400 font-black">GRATIS</span>
                      </span>
                    ) : (
                      <span className="shrink-0 ml-2 text-[8px] text-gray-400">
                        ${adjCost}K
                        <span className="text-gray-600">/g</span>
                        {costMult > 1 && <span className="text-amber-400 ml-0.5">×{costMult}</span>}
                      </span>
                    )}
                  </button>
                );
              })}
            {activeCat !== 'my_studio' && allLocations.filter(l => l.category === activeCat).length === 0 && (
              <p className="text-[8px] text-gray-600 text-center py-2">Caricamento location...</p>
            )}
          </div>

          {/* Selected chips */}
          {locations.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-gray-800/50" data-testid="selected-locations">
              {locations.map(name => (
                <span key={name} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-[8px] text-cyan-300 font-bold">
                  {name}
                  {subPhase === 0 && (
                    <button onClick={() => toggleLoc(name)} className="hover:text-red-400">{'\u00D7'}</button>
                  )}
                </span>
              ))}
            </div>
          )}

          {/* Coherence Bar — sweet spot + AI advice */}
          {(genre || locations.length > 0) && (
            <div className="mt-2">
              <LocationCoherenceBar
                genre={genre}
                preplot={preplot}
                locations={locations}
              />
            </div>
          )}
        </div>

        {/* ═══ BUDGET TIER ═══ */}
        <div className="space-y-1.5">
          <span className="text-[8px] text-gray-500 uppercase font-bold">Budget Produzione</span>
          <div className="grid grid-cols-3 gap-1">
            {[
              { id: 'micro', label: 'Micro', range: '$200K-800K', color: 'text-gray-400 border-gray-700', risk: 'Rischio basso' },
              { id: 'low', label: 'Low', range: '$800K-3M', color: 'text-blue-400 border-blue-500/30', risk: 'Rischio basso' },
              { id: 'mid', label: 'Mid', range: '$3M-12M', color: 'text-cyan-400 border-cyan-500/30', risk: 'Bilanciato' },
              { id: 'big', label: 'Big', range: '$12M-40M', color: 'text-amber-400 border-amber-500/30', risk: 'Rischio medio' },
              { id: 'blockbuster', label: 'Blockbuster', range: '$40M-100M', color: 'text-orange-400 border-orange-500/30', risk: 'Rischio alto' },
              { id: 'mega', label: 'Mega', range: '$100M-250M', color: 'text-red-400 border-red-500/30', risk: 'Rischio estremo' },
            ].map(b => (
              <button key={b.id} onClick={() => { if (subPhase === 0) { setBudgetTier(b.id); mark(); } }} disabled={subPhase > 0}
                className={`p-1.5 rounded-lg border text-center transition-all disabled:opacity-50 ${
                  budgetTier === b.id ? `${b.color} bg-white/5` : 'border-gray-800 text-gray-600 hover:border-gray-700'
                }`}>
                <p className="text-[9px] font-bold">{b.label}</p>
                <p className="text-[7px] opacity-70">{b.range}</p>
                {budgetTier === b.id && <p className="text-[6px] opacity-50 mt-0.5">{b.risk}</p>}
              </button>
            ))}
          </div>
          <p className="text-[7px] text-gray-600">Budget alto = hype maggiore ma rischio flop se qualita bassa</p>
        </div>

        {/* OK Fase 0 */}
        {subPhase === 0 && (
          <div className="flex justify-end">
            <OkButton enabled={phase0Valid} onClick={confirmPhase0} loading={loading === 'phase0'} testid="idea-ok-phase0" />
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
                          className="flex-1 text-[8px] py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 disabled:opacity-30 font-bold"
                          data-testid="poster-ai-auto">Genera da pretrama</button>
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
                        className="w-full text-[8px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20 disabled:opacity-30 font-bold"
                        data-testid="screenplay-ai-auto">
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
                <OkButton enabled={!!(film.screenplay_text && film.screenplay_text.length > 50) || manualScreenplay.length >= 100} onClick={confirmPhase2} loading={loading === 'screenplay'} testid="idea-ok-screenplay" />
              </div>
            )}
          </div>
        )}

        {/* ═══ FASE 3: TRAILER AI (opzionale, dopo sceneggiatura) — solo edit mode ═══ */}
        {subPhase >= 3 && !readOnly && (
          <div className={`p-3 rounded-xl border space-y-2 ${subPhase === 3 ? 'bg-gray-800/20 border-sky-500/30' : 'bg-gray-900/20 border-gray-800/20 opacity-60'}`}>
            <div className="flex items-center justify-between">
              <span className="text-[8px] text-gray-500 uppercase font-bold">Trailer AI (opzionale)</span>
              {subPhase > 3 && <span className="text-[8px] text-emerald-400 font-bold">✓ Confermato</span>}
            </div>
            {subPhase === 3 && (
              <>
                <p className="text-[9px] text-gray-400">
                  Crea un trailer cinematografico basato su pretrama e sceneggiatura. Aumenta l'hype del film.
                  Puoi anche saltarlo — la pipeline continua comunque.
                </p>
                <TrailerGeneratorCard
                  contentId={film.id}
                  contentTitle={film.title}
                  contentGenre={film.genre || ''}
                  contentStatus={film.pipeline_state || film.status || ''}
                  api={api}
                  userCredits={user?.cinepass ?? user?.cinecrediti ?? user?.cinecredits ?? 0}
                  canGenerate={true}
                  isGuest={isGuest}
                  onGenerated={onRefresh}
                  onSkip={skipTrailer}
                  onConfirm={confirmTrailerAndProceed}
                  sagaInheritance={(film.saga_id && (film.saga_chapter_number || 0) > 1) ? { active: true, sagaId: film.saga_id, chapterNumber: film.saga_chapter_number } : null}
                />
              </>
            )}
          </div>
        )}

        {/* DONE message */}
        {subPhase >= 4 && (
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

      {/* Danger zone: Scarta / Ricomincia (mobile-first) */}
      {!readOnly && (
        <DangerZoneFilm film={film} onRefresh={onRefresh} toast={toast} api={api} />
      )}
    </PhaseWrapper>
  );
};

// Danger Zone — film V3 ideaPhase
const DangerZoneFilm = ({ film, onRefresh, toast, api }) => {
  const [showDiscard, setShowDiscard] = useState(false);
  const [showRestart, setShowRestart] = useState(false);
  const [busy, setBusy] = useState(false);

  const onDiscard = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await api.post(`/pipeline-v3/films/${film.id}/hard-delete`);
      toast?.success?.('Progetto eliminato');
      setShowDiscard(false);
      window.location.href = '/produci';
    } catch (e) {
      toast?.error?.(e?.response?.data?.detail || 'Errore eliminazione');
    } finally { setBusy(false); }
  };
  const onRestart = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await api.post(`/pipeline-v3/films/${film.id}/restart`);
      toast?.success?.('Progetto ricominciato da zero');
      setShowRestart(false);
      onRefresh?.();
    } catch (e) {
      toast?.error?.(e?.response?.data?.detail || 'Errore reset');
    } finally { setBusy(false); }
  };

  return (
    <div className="mt-4 pt-4 border-t border-white/5">
      <p className="text-[8px] text-gray-600 uppercase font-bold tracking-wider mb-2 text-center">Zona pericolosa</p>
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => setShowRestart(true)}
          data-testid="idea-restart-btn"
          className="py-2.5 rounded-xl border border-amber-500/25 bg-amber-500/5 text-amber-400 text-[10px] font-bold flex items-center justify-center gap-1.5 hover:bg-amber-500/10 active:scale-[0.97] transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Ricomincia
        </button>
        <button
          onClick={() => setShowDiscard(true)}
          data-testid="idea-discard-btn"
          className="py-2.5 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-[10px] font-bold flex items-center justify-center gap-1.5 hover:bg-rose-500/10 active:scale-[0.97] transition-all"
        >
          <Trash2 className="w-3.5 h-3.5" /> Scarta
        </button>
      </div>
      <CineConfirm
        open={showDiscard}
        title="Scartare il progetto?"
        subtitle="Verra' eliminato completamente. Non finira' al mercato."
        confirmLabel={busy ? '...' : 'Scarta per sempre'}
        confirmTone="rose"
        onConfirm={onDiscard}
        onCancel={() => !busy && setShowDiscard(false)}
      />
      <CineConfirm
        open={showRestart}
        title="Ricominciare da capo?"
        subtitle="Tutti i dati (titolo, locandina, sceneggiatura, cast, ecc.) saranno cancellati."
        confirmLabel={busy ? '...' : 'Ricomincia'}
        confirmTone="amber"
        onConfirm={onRestart}
        onCancel={() => !busy && setShowRestart(false)}
      />
    </div>
  );
};


/**
 * SagaPipelineHeader — mini-timeline + fan base bonus + cliffhanger reminder
 * Visibile in cima alla pipeline V3 quando il film è parte di una saga.
 */
const SagaPipelineHeader = ({ film, api }) => {
  const [saga, setSaga] = useState(null);

  useEffect(() => {
    if (!film?.saga_id || !api) return;
    api.get(`/sagas/${film.saga_id}`).then(r => setSaga(r.data || null)).catch(() => setSaga(null));
  }, [film?.saga_id, api]);

  if (!saga) return null;

  const total = saga.saga?.total_planned_chapters || 0;
  const released = saga.chapters?.length || 0;
  const currentN = film.saga_chapter_number || 1;
  const prevChapter = (saga.chapters || []).find(c => (c.chapter_number || 0) === currentN - 1);
  const prevCwsv = prevChapter?.cwsv || 0;
  const prevCliff = !!prevChapter?.saga_cliffhanger;

  // Calcolo fan base bonus modifier (replica logica backend)
  const fanBaseBonusPct = currentN >= 2 ? Math.round(((prevCwsv >= 8 ? 1.25 : prevCwsv >= 6.5 ? 1.15 : prevCwsv >= 5 ? 1.05 : 0.95) - 1) * 100) : 0;
  const earlyOffset = prevCwsv >= 8 ? 6 : prevCwsv >= 6.5 ? 5 : prevCwsv >= 5 ? 4 : prevCwsv >= 3.5 ? 3 : 2;

  return (
    <div className="rounded-xl border border-violet-500/30 bg-gradient-to-br from-violet-950/40 via-fuchsia-950/30 to-zinc-900/40 p-3 space-y-2.5" data-testid="saga-pipeline-header">
      {/* Title + chapter info */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-[10px] uppercase tracking-wider text-violet-300 font-bold">SAGA</span>
          <span className="text-[11px] font-bold text-white truncate">{saga.saga?.title || 'Saga'}</span>
        </div>
        <span className="text-[9px] text-violet-200 font-bold whitespace-nowrap">Cap. {currentN}/{total}</span>
      </div>

      {/* Mini-timeline */}
      {total > 0 && (
        <div className="flex items-center gap-1" data-testid="saga-timeline">
          {Array.from({ length: total }, (_, i) => {
            const n = i + 1;
            const isReleased = n <= released;
            const isCurrent = n === currentN;
            return (
              <div key={n} className="flex-1 flex flex-col items-center">
                <div className={`w-full h-1.5 rounded-full ${isCurrent ? 'bg-violet-400' : isReleased ? 'bg-emerald-500' : 'bg-zinc-700'}`} />
                <span className={`text-[7px] mt-0.5 font-bold ${isCurrent ? 'text-violet-300' : isReleased ? 'text-emerald-300' : 'text-zinc-500'}`}>
                  {isCurrent ? '◉' : isReleased ? '✓' : n}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* (d) Fan Base Bonus + (e) Cliffhanger reminder */}
      {currentN >= 2 && (
        <div className="grid grid-cols-2 gap-2">
          {fanBaseBonusPct !== 0 && (
            <div className={`px-2 py-1.5 rounded-lg border text-[9px] font-bold ${fanBaseBonusPct > 0 ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300' : 'border-rose-500/40 bg-rose-500/10 text-rose-300'}`} data-testid="saga-fanbase-badge">
              Fan Base {fanBaseBonusPct > 0 ? `+${fanBaseBonusPct}%` : `${fanBaseBonusPct}%`}
              <div className="text-[7px] opacity-80 font-normal">CWSv prec. {prevCwsv.toFixed(1)}</div>
            </div>
          )}
          {prevCliff && (
            <div className="px-2 py-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 text-amber-300 text-[9px] font-bold" data-testid="saga-cliffhanger-reminder">
              💥 Cliffhanger attivo
              <div className="text-[7px] opacity-80 font-normal">+5% hype iniziale</div>
            </div>
          )}
          <div className="px-2 py-1.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 text-[9px] font-bold col-span-2 sm:col-span-1">
            ⏱ Hype anticipato {earlyOffset}gg
            <div className="text-[7px] opacity-80 font-normal">prima della fine cinema cap. precedente</div>
          </div>
        </div>
      )}
    </div>
  );
};
