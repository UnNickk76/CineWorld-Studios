import React, { useCallback, useEffect, useRef, useState, useMemo, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Film, ChevronLeft, Save, X, Tv, Sparkles, Star } from 'lucide-react';
import { StepperBar as FilmStepperBar, PhaseWrapper, ProgressCircle, STEP_STYLES, GENRE_LABELS, SUBGENRE_MAP, LOCATION_TAGS } from './V3Shared';
import { Check, TrendingUp, Users, Camera, Clapperboard, Scissors, Megaphone, Globe, Ticket } from 'lucide-react';
import { AuthContext } from '../../contexts';
import TrailerGeneratorCard from '../TrailerGeneratorCard';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

/* ─── Inline Progress Circle (small, for inside buttons) ─── */
const InlineProgressCircle = ({ value = 0, color = '#fff' }) => {
  const r = 7;
  const c = 2 * Math.PI * r;
  const off = c - (value / 100) * c;
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" className="inline-block flex-shrink-0">
      <circle cx="10" cy="10" r={r} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />
      <circle
        cx="10" cy="10" r={r} fill="none" stroke={color} strokeWidth="2"
        strokeDasharray={c}
        strokeDashoffset={off}
        strokeLinecap="round"
        transform="rotate(-90 10 10)"
        style={{ transition: 'stroke-dashoffset 0.3s ease' }}
      />
    </svg>
  );
};

/* ─── API helper (uses series-v3 prefix) ─── */
async function sapi(path, method = 'GET', body) {
  const token = localStorage.getItem('cineworld_token');
  const res = await fetch(`${API}/api/pipeline-series-v3${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || 'Errore API');
  return data;
}

/* ─── Steps (same as film but no LaPrima) ─── */
const SERIES_STEPS = [
  { id: 'idea', label: 'IDEA', icon: Sparkles, color: 'amber' },
  { id: 'hype', label: 'HYPE', icon: TrendingUp, color: 'orange' },
  { id: 'cast', label: 'CAST', icon: Users, color: 'cyan' },
  { id: 'prep', label: 'PREP', icon: Camera, color: 'blue' },
  { id: 'ciak', label: 'CIAK', icon: Clapperboard, color: 'red' },
  { id: 'finalcut', label: 'FINAL CUT', icon: Scissors, color: 'purple' },
  { id: 'marketing', label: 'MARKETING', icon: Megaphone, color: 'green' },
  { id: 'distribution', label: 'TV', icon: Globe, color: 'blue' },
  { id: 'release_pending', label: 'USCITA', icon: Ticket, color: 'emerald' },
];

const ANIME_GENRE_LABELS = {
  shonen: 'Shonen', shojo: 'Shojo', seinen: 'Seinen', mecha: 'Mecha', isekai: 'Isekai',
  slice_of_life: 'Slice of Life', sports: 'Sport', action: 'Azione', fantasy: 'Fantasy',
  sci_fi: 'Fantascienza', horror: 'Horror', comedy: 'Commedia', drama: 'Dramma',
  romance: 'Romance', mystery: 'Mistero', thriller: 'Thriller', adventure: 'Avventura', musical: 'Musical',
};

const ALL_LABELS = { ...GENRE_LABELS, ...ANIME_GENRE_LABELS };

/* ─── Stepper Bar ─── */
const StepperBar = ({ current }) => {
  const ci = SERIES_STEPS.findIndex(s => s.id === current);
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) {
      const el = ref.current.querySelector(`[data-sid="${current}"]`);
      if (el) {
        const container = ref.current;
        container.scrollTo({ left: Math.max(0, el.offsetLeft - container.offsetWidth / 2 + el.offsetWidth / 2), behavior: 'smooth' });
      }
    }
  }, [current]);
  return (
    <div ref={ref} className="flex items-center gap-0 overflow-x-auto py-2 px-1 scrollbar-hide" data-testid="series-stepper">
      {SERIES_STEPS.map((s, i) => {
        const Icon = s.icon;
        const style = STEP_STYLES[s.color];
        const done = i < ci; const active = i === ci;
        return (
          <React.Fragment key={s.id}>
            {i > 0 && <div className={`w-2 sm:w-4 h-0.5 shrink-0 ${done || active ? style.line : 'bg-gray-800'}`} />}
            <div className="flex flex-col items-center shrink-0 gap-0.5" data-sid={s.id}>
              <div className={`w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center border-2 transition-all ${
                active ? `${style.active} shadow-lg scale-110` : done ? 'border-emerald-600 bg-emerald-500/10 text-emerald-400' : 'border-gray-800 bg-gray-900/50 text-gray-700 opacity-40'
              }`}>{done ? <Check className="w-2.5 h-2.5" /> : <Icon className="w-2.5 h-2.5" />}</div>
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

/* ═══════════════ PHASES ═══════════════ */

/* ─── IDEA PHASE ─── */
const IdeaPhase = ({ project, onRefresh, seriesType }) => {
  const [title, setTitle] = useState(project.title || '');
  const [genre, setGenre] = useState(project.genre || '');
  const [subgenres, setSubgenres] = useState(project.subgenres || []);
  const [preplot, setPreplot] = useState(project.preplot || '');
  const [numEp, setNumEp] = useState(project.num_episodes || 10);
  const [locations, setLocations] = useState(project.locations || []);
  const [genres, setGenres] = useState({});
  const [saving, setSaving] = useState(false);
  const [genTitles, setGenTitles] = useState(false);
  const [genPoster, setGenPoster] = useState(false);
  const [genScreen, setGenScreen] = useState(false);
  const [posterProgress, setPosterProgress] = useState(0);
  const [screenProgress, setScreenProgress] = useState(0);
  const [selectedEp, setSelectedEp] = useState(null);  // episode clicked → show mini_plot
  const posterIntRef = useRef(null);
  const screenIntRef = useRef(null);

  useEffect(() => {
    sapi(`/genres?series_type=${seriesType}`).then(d => setGenres(d.genres || {})).catch(() => {});
  }, [seriesType]);

  const genreInfo = genres[genre] || {};
  const epRange = genreInfo.ep_range || [4, 26];
  const subOpts = SUBGENRE_MAP[genre] || [];
  const valid = title.trim().length >= 2 && genre && preplot.trim().length >= 30;

  const save = async () => {
    setSaving(true);
    try {
      await sapi(`/projects/${project.id}/save-idea`, 'POST', { title, genre, subgenres, preplot, num_episodes: numEp, locations });
      toast.success('Idea salvata!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setSaving(false);
  };

  const generateTitles = async () => {
    setGenTitles(true);
    try {
      const r = await sapi(`/projects/${project.id}/generate-episode-titles`, 'POST');
      toast.success(`${r.episodes?.length || 0} titoli generati!`);
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setGenTitles(false);
  };

  const generatePoster = async () => {
    setGenPoster(true);
    setPosterProgress(0);
    // Simulate progress 0→95 over ~18s until the real response arrives
    if (posterIntRef.current) clearInterval(posterIntRef.current);
    const start = Date.now();
    posterIntRef.current = setInterval(() => {
      const elapsed = (Date.now() - start) / 1000;
      setPosterProgress(Math.min(95, Math.round(elapsed * 5.3)));
    }, 400);
    try {
      const r = await sapi(`/projects/${project.id}/generate-poster`, 'POST');
      setPosterProgress(100);
      toast.success(r.message || 'Locandina generata!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    if (posterIntRef.current) { clearInterval(posterIntRef.current); posterIntRef.current = null; }
    setTimeout(() => { setGenPoster(false); setPosterProgress(0); }, 600);
  };

  const generateScreenplay = async () => {
    setGenScreen(true);
    setScreenProgress(0);
    if (screenIntRef.current) clearInterval(screenIntRef.current);
    const start = Date.now();
    screenIntRef.current = setInterval(() => {
      const elapsed = (Date.now() - start) / 1000;
      // Longer because 2 LLM calls (script + mini-plots), ~25s
      setScreenProgress(Math.min(95, Math.round(elapsed * 3.8)));
    }, 400);
    try {
      const r = await sapi(`/projects/${project.id}/generate-screenplay`, 'POST');
      setScreenProgress(100);
      toast.success(r.message || 'Sceneggiatura generata!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    if (screenIntRef.current) { clearInterval(screenIntRef.current); screenIntRef.current = null; }
    setTimeout(() => { setGenScreen(false); setScreenProgress(0); }, 600);
  };

  // Cleanup intervals on unmount
  useEffect(() => () => {
    if (posterIntRef.current) clearInterval(posterIntRef.current);
    if (screenIntRef.current) clearInterval(screenIntRef.current);
  }, []);

  return (
    <div className="p-3 space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
          {seriesType === 'anime' ? <Sparkles className="w-3.5 h-3.5 text-amber-400" /> : <Tv className="w-3.5 h-3.5 text-amber-400" />}
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">Concept {seriesType === 'anime' ? 'Anime' : 'Serie TV'}</h3>
          <p className="text-[8px] text-gray-500">Titolo, genere, episodi, sinossi</p>
        </div>
      </div>

      {/* Title */}
      <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Titolo della serie..."
        className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-800 text-white text-xs focus:border-amber-500/40 focus:outline-none" data-testid="series-title-input" />

      {/* Genre */}
      <div className="flex flex-wrap gap-1">
        {Object.entries(genres).map(([id, info]) => (
          <button key={id} onClick={() => { setGenre(id); setSubgenres([]); }}
            className={`px-2 py-1 rounded-full text-[8px] font-bold border transition-all ${genre === id ? 'border-amber-500 bg-amber-500/15 text-amber-400' : 'border-gray-800 text-gray-500 hover:border-gray-600'}`}>
            {info.name_it || ALL_LABELS[id] || id}
          </button>
        ))}
      </div>

      {/* Subgenres */}
      {subOpts.length > 0 && (
        <div>
          <p className="text-[8px] text-gray-500 mb-1">Sottogeneri (opzionali)</p>
          <div className="flex flex-wrap gap-1">
            {subOpts.slice(0, 12).map(s => (
              <button key={s} onClick={() => setSubgenres(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s].slice(0, 3))}
                className={`px-1.5 py-0.5 rounded text-[7px] border ${subgenres.includes(s) ? 'border-purple-500/40 bg-purple-500/15 text-purple-400' : 'border-gray-800 text-gray-600'}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Num Episodes */}
      <div>
        <p className="text-[8px] text-gray-500 mb-1">Numero Episodi ({epRange[0]}-{epRange[1]})</p>
        <div className="flex items-center gap-2">
          <input type="range" min={epRange[0]} max={epRange[1]} value={numEp} onChange={e => setNumEp(+e.target.value)}
            className="flex-1 accent-amber-500" data-testid="num-episodes-slider" />
          <span className="text-sm font-bold text-amber-400 w-8 text-center">{numEp}</span>
        </div>
      </div>

      {/* Synopsis */}
      <textarea value={preplot} onChange={e => setPreplot(e.target.value)} rows={3}
        placeholder="Sinossi della stagione (min 30 caratteri)..."
        className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-800 text-white text-[10px] focus:border-amber-500/40 focus:outline-none resize-none" data-testid="series-preplot" />
      <p className="text-[7px] text-gray-600 text-right">{preplot.length}/30 min</p>

      {/* Locations */}
      <div>
        <p className="text-[8px] text-gray-500 mb-1">Ambientazione</p>
        <div className="flex flex-wrap gap-1">
          {LOCATION_TAGS.map(l => (
            <button key={l} onClick={() => setLocations(prev => prev.includes(l) ? prev.filter(x => x !== l) : [...prev, l])}
              className={`px-1.5 py-0.5 rounded text-[7px] border ${locations.includes(l) ? 'border-blue-500/40 bg-blue-500/15 text-blue-400' : 'border-gray-800 text-gray-600'}`}>
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Save + Generate Titles */}
      <div className="flex gap-2">
        <button onClick={save} disabled={!valid || saving}
          className="flex-1 py-2 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[10px] font-bold disabled:opacity-30" data-testid="save-idea-btn">
          {saving ? '...' : 'Salva Idea'}
        </button>
        {valid && (
          <button onClick={generateTitles} disabled={genTitles}
            className="px-3 py-2 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 text-[10px] font-bold disabled:opacity-30" data-testid="gen-titles-btn">
            {genTitles ? '...' : 'Titoli EP'}
          </button>
        )}
      </div>

      {/* AI Poster + Screenplay (like film V3) */}
      {valid && project.id && (
        <div className="grid grid-cols-2 gap-2" data-testid="series-ai-tools">
          <button onClick={generatePoster} disabled={genPoster}
            className="py-2 rounded-lg bg-purple-500/15 border border-purple-500/30 text-purple-300 text-[10px] font-bold active:scale-95 transition-transform disabled:opacity-70 flex items-center justify-center gap-1.5 relative" data-testid="gen-series-poster-btn">
            {genPoster && (
              <InlineProgressCircle value={posterProgress} color="#c084fc" />
            )}
            <span>{genPoster
              ? `${posterProgress}%`
              : (project.poster_url ? 'Rigenera Locandina' : 'Locandina AI')}</span>
          </button>
          <button onClick={generateScreenplay} disabled={genScreen}
            className="py-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold active:scale-95 transition-transform disabled:opacity-70 flex items-center justify-center gap-1.5 relative" data-testid="gen-series-screenplay-btn">
            {genScreen && (
              <InlineProgressCircle value={screenProgress} color="#34d399" />
            )}
            <span>{genScreen
              ? `${screenProgress}%`
              : (project.screenplay_text ? 'Rigenera Sceneggiatura' : 'Sceneggiatura AI')}</span>
          </button>
        </div>
      )}

      {project.poster_url && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-purple-500/5 border border-purple-500/20">
          <img src={(project.poster_url.startsWith('http') ? project.poster_url : `${API}${project.poster_url}`)} alt="" className="w-10 h-14 rounded object-cover border border-purple-400/30" />
          <p className="text-[9px] text-purple-200">Locandina pronta</p>
        </div>
      )}
      {project.screenplay_text && (
        <details className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
          <summary className="text-[10px] font-bold text-emerald-300 cursor-pointer">📝 Sceneggiatura (click per leggere)</summary>
          <p className="text-[9px] text-gray-300 mt-2 whitespace-pre-wrap leading-relaxed">{project.screenplay_text}</p>
        </details>
      )}

      {/* Episode titles grid — 12 per column, click to show mini-plot */}
      {project.episodes?.length > 0 && (
        <div className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
          <p className="text-[8px] text-gray-500 mb-1.5 font-bold uppercase">Titoli Episodi ({project.episodes.length})</p>
          <div
            className="grid gap-x-3 gap-y-0.5 overflow-x-auto"
            style={{ gridAutoFlow: 'column', gridTemplateRows: 'repeat(12, auto)', gridAutoColumns: 'minmax(130px, 1fr)' }}
            data-testid="series-episodes-grid"
          >
            {project.episodes.map((ep, i) => (
              <button
                key={i}
                onClick={() => setSelectedEp(ep)}
                className="text-left text-[8.5px] text-gray-400 hover:text-amber-300 active:text-amber-400 transition-colors truncate leading-tight py-0.5"
                title={ep.title}
                data-testid={`ep-title-${ep.number}`}
              >
                <span className="text-gray-600 mr-1">{ep.number}.</span>{ep.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Episode mini-plot modal */}
      {selectedEp && (
        <div className="fixed inset-0 z-[70] bg-black/70 flex items-center justify-center p-4" onClick={() => setSelectedEp(null)}>
          <div className="bg-[#111113] border border-amber-500/30 rounded-xl max-w-sm w-full p-4 space-y-3" onClick={(e) => e.stopPropagation()}>
            <div>
              <p className="text-[8px] text-amber-400/80 uppercase font-bold">Episodio {selectedEp.number}</p>
              <h4 className="text-base font-bold text-white mt-0.5">{selectedEp.title}</h4>
            </div>
            <div className="text-[11px] text-gray-300 leading-relaxed whitespace-pre-wrap min-h-[72px]">
              {selectedEp.mini_plot
                ? selectedEp.mini_plot
                : <span className="italic text-gray-500">Mini-trama non ancora disponibile. Genera la sceneggiatura per creare le trame di tutti gli episodi.</span>}
            </div>
            <button
              onClick={() => setSelectedEp(null)}
              className="w-full py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[10px] font-bold"
              data-testid="close-ep-modal">
              Chiudi
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

/* ─── HYPE PHASE (reuse film logic) ─── */
const HypePhase = ({ project, onRefresh }) => {
  const [progress, setProgress] = useState(project.hype_progress || 0);
  useEffect(() => { setProgress(project.hype_progress || 0); }, [project]);
  return (
    <PhaseWrapper title="Hype" subtitle="Costruisci aspettative" icon={TrendingUp} color="orange">
      <div className="flex flex-col items-center py-4">
        <ProgressCircle value={progress} size={80} color="#f97316" />
        <p className="text-[9px] text-gray-500 mt-2">L'hype si accumula automaticamente. Avanza quando pronto.</p>
      </div>
    </PhaseWrapper>
  );
};

/* ─── CAST PHASE (simplified for series) ─── */
const CastPhase = ({ project, onRefresh, seriesType }) => {
  const cast = project.cast || {};
  const maxActors = seriesType === 'anime' ? 8 : 8;
  return (
    <PhaseWrapper title="Cast & Crew" subtitle={`Seleziona il cast (max ${maxActors} attori)`} icon={Users} color="cyan">
      <div className="space-y-2">
        <div className="p-2 bg-cyan-500/5 border border-cyan-500/15 rounded-lg">
          <p className="text-[9px] text-gray-400">Showrunner: <span className="text-white font-bold">{cast.director?.name || 'Da selezionare'}</span></p>
          <p className="text-[9px] text-gray-400">Attori: <span className="text-white font-bold">{(cast.actors || []).length}/{maxActors}</span></p>
          <p className="text-[9px] text-gray-400">Compositore: <span className="text-white font-bold">{cast.composer?.name || 'Da selezionare'}</span></p>
          {seriesType === 'anime' && <p className="text-[8px] text-yellow-400 mt-1">Il compositore influenza la Opening/Ending</p>}
        </div>
        <p className="text-[8px] text-gray-500 text-center">Il casting utilizza lo stesso sistema del film V3. Avanza per ora.</p>
      </div>
    </PhaseWrapper>
  );
};

/* ─── PREP PHASE ─── */
const PrepPhase = ({ project, onRefresh, seriesType }) => {
  const formats = [
    { id: 'miniserie', label: 'Miniserie', desc: '4-6 episodi' },
    { id: 'stagionale', label: 'Stagionale', desc: '8-13 episodi' },
    { id: 'lunga', label: 'Lunga', desc: '20-26 episodi' },
    { id: 'maratona', label: 'Maratona', desc: '40+ episodi' },
  ];
  const durations = [22, 30, 45, 60];
  return (
    <PhaseWrapper title="Pre-Produzione" subtitle="Formato, durata episodi, effetti" icon={Camera} color="blue">
      <div className="space-y-3">
        <p className="text-[8px] text-gray-500">Formato Serie</p>
        <div className="grid grid-cols-2 gap-1.5">
          {formats.map(f => (
            <button key={f.id} className={`p-2 rounded-lg border text-left ${project.series_format === f.id ? 'border-blue-500/40 bg-blue-500/10' : 'border-gray-800'}`}>
              <p className="text-[9px] font-bold text-white">{f.label}</p>
              <p className="text-[7px] text-gray-500">{f.desc}</p>
            </button>
          ))}
        </div>
        <p className="text-[8px] text-gray-500">Durata Episodio</p>
        <div className="flex gap-1.5">
          {durations.map(d => (
            <button key={d} className={`flex-1 py-1.5 rounded-lg border text-[9px] font-bold ${project.episode_duration_min === d ? 'border-blue-500/40 bg-blue-500/10 text-blue-400' : 'border-gray-800 text-gray-500'}`}>
              {d} min
            </button>
          ))}
        </div>
      </div>
    </PhaseWrapper>
  );
};

/* ─── CIAK PHASE ─── */
const CiakPhase = ({ project, seriesType }) => {
  const minPerEp = seriesType === 'anime' ? 20 : 30;
  const totalMin = (project.num_episodes || 10) * minPerEp;
  return (
    <PhaseWrapper title="Riprese" subtitle={`${minPerEp} min reali per episodio`} icon={Clapperboard} color="red">
      <div className="flex flex-col items-center py-4">
        <ProgressCircle value={0} size={80} color="#ef4444" />
        <p className="text-[9px] text-gray-500 mt-2">{project.num_episodes} episodi × {minPerEp} min = <span className="text-white font-bold">{totalMin} min</span> totali</p>
        <p className="text-[8px] text-gray-600">Avanza per avviare le riprese</p>
      </div>
    </PhaseWrapper>
  );
};

/* ─── FINALCUT PHASE ─── */
const FinalCutPhase = ({ project }) => (
  <PhaseWrapper title="Post-Produzione" subtitle="Montaggio e mix finale" icon={Scissors} color="purple">
    <div className="flex flex-col items-center py-4">
      <ProgressCircle value={0} size={80} color="#a855f7" />
      <p className="text-[9px] text-gray-500 mt-2">Il montaggio finale e il mix audio avvengono qui. I voti CWSv per episodio vengono calcolati.</p>
    </div>
  </PhaseWrapper>
);

/* ─── MARKETING PHASE ─── */
const MarketingPhase = ({ project, onRefresh }) => {
  const [prossimamente, setProssimamente] = useState(project.prossimamente_tv || false);
  const save = async () => {
    try {
      await sapi(`/projects/${project.id}/save-marketing-data`, 'POST', { prossimamente_tv: prossimamente, selected_sponsors: [], marketing_packages: [] });
      toast.success('Marketing salvato!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
  };
  return (
    <PhaseWrapper title="Marketing & TV" subtitle="Sponsor, promozione, prossimamente" icon={Megaphone} color="green">
      <div className="space-y-3">
        {/* Prossimamente TV Toggle */}
        <div className="p-3 rounded-lg bg-green-500/5 border border-green-500/15">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] font-bold text-white">Prossimamente in TV</p>
              <p className="text-[8px] text-gray-500">Mostra nella sezione "Prossimamente" della Dashboard</p>
            </div>
            <button onClick={() => setProssimamente(!prossimamente)}
              className={`w-12 h-6 rounded-full transition-colors relative ${prossimamente ? 'bg-green-600' : 'bg-gray-700'}`} data-testid="prossimamente-toggle">
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${prossimamente ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
          </div>
          {prossimamente && (
            <p className="text-[8px] text-green-400 mt-2">La serie apparirà nella sezione "Prossimamente" appena creata. Al completamento pipeline deciderai quando trasmetterla.</p>
          )}
          {!prossimamente && (
            <p className="text-[8px] text-gray-500 mt-2">La serie andrà direttamente in "I Miei" → Serie TV/Anime dopo il rilascio.</p>
          )}
        </div>
        <button onClick={save} className="w-full py-2 rounded-lg bg-green-500/15 border border-green-500/30 text-green-400 text-[10px] font-bold" data-testid="save-marketing-btn">
          Conferma Marketing
        </button>
      </div>
    </PhaseWrapper>
  );
};

/* ─── DISTRIBUTION PHASE ─── */
const DistributionPhase = ({ project, onRefresh }) => {
  const [policy, setPolicy] = useState(project.release_policy || 'daily_1');
  const [epsBatch, setEpsBatch] = useState(project.tv_eps_per_batch || 1);
  const [interval, setInterval_] = useState(project.tv_interval_days || 1);
  const [split, setSplit] = useState(project.tv_split_season || false);
  const [pause, setPause] = useState(project.tv_split_pause_days || 14);
  const [delay, setDelay] = useState(project.distribution_delay_hours || 0);

  const policies = [
    { id: 'daily_1', label: '1 al giorno', desc: 'La TV trasmette 1 episodio al giorno. Nessuna scelta per la TV.', tvFree: false },
    { id: 'daily_3', label: '3 al giorno', desc: 'La TV puo scegliere 1, 2 o 3 episodi al giorno.', tvFree: true },
    { id: 'half_seasons', label: 'Due mezze stagioni', desc: 'La TV puo confermare 2 blocchi o scegliere quanti ep al giorno.', tvFree: true },
    { id: 'all_at_once', label: 'Tutta insieme', desc: 'La TV ha piena liberta: binge, 2 blocchi, o programmazione personalizzata.', tvFree: true },
  ];
  const canChooseEps = policy !== 'daily_1';
  const canChooseInterval = policy === 'half_seasons' || policy === 'all_at_once';
  const canSplit = policy === 'half_seasons' || policy === 'all_at_once';
  const halfEps = Math.ceil((project.num_episodes || 10) / 2);

  const save = async () => {
    try {
      await sapi(`/projects/${project.id}/save-distribution`, 'POST', {
        release_policy: policy, tv_eps_per_batch: epsBatch, tv_interval_days: interval,
        tv_split_season: split, tv_split_pause_days: pause, distribution_delay_hours: delay,
      });
      toast.success('Distribuzione salvata!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
  };

  return (
    <PhaseWrapper title="Distribuzione TV" subtitle="Scheduling e programmazione" icon={Globe} color="blue">
      <div className="space-y-3">
        {/* Release Policy (Producer choice) */}
        <p className="text-[9px] text-gray-400 font-bold uppercase">Politica di rilascio</p>
        <div className="space-y-1.5">
          {policies.map(p => (
            <button key={p.id} onClick={() => { setPolicy(p.id); if (p.id === 'daily_1') { setEpsBatch(1); setInterval_(1); setSplit(false); } }}
              className={`w-full p-2.5 rounded-lg border text-left transition-all ${policy === p.id ? 'border-blue-500/40 bg-blue-500/10' : 'border-gray-800 hover:border-gray-700'}`}
              data-testid={`policy-${p.id}`}>
              <p className="text-[10px] font-bold text-white">{p.label}</p>
              <p className="text-[7px] text-gray-500">{p.desc}</p>
            </button>
          ))}
        </div>

        {/* TV Scheduling Options */}
        {canChooseEps && (
          <div>
            <p className="text-[9px] text-gray-400 font-bold uppercase mb-1">Episodi per trasmissione</p>
            <div className="flex gap-1.5">
              {[1, 2, 3].map(n => (
                <button key={n} onClick={() => setEpsBatch(n)}
                  className={`flex-1 py-2 rounded-lg border text-[10px] font-bold ${epsBatch === n ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-400' : 'border-gray-800 text-gray-500'}`}>
                  {n} ep
                </button>
              ))}
            </div>
          </div>
        )}

        {canChooseInterval && (
          <div>
            <p className="text-[9px] text-gray-400 font-bold uppercase mb-1">Ogni quanti giorni</p>
            <div className="flex gap-1.5">
              {[1, 2, 3].map(n => (
                <button key={n} onClick={() => setInterval_(n)}
                  className={`flex-1 py-2 rounded-lg border text-[10px] font-bold ${interval === n ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-400' : 'border-gray-800 text-gray-500'}`}>
                  {n === 1 ? 'Ogni giorno' : `Ogni ${n} giorni`}
                </button>
              ))}
            </div>
          </div>
        )}

        {canSplit && (
          <div className="p-2.5 rounded-lg bg-indigo-500/5 border border-indigo-500/15">
            <div className="flex items-center justify-between mb-1">
              <p className="text-[10px] font-bold text-white">Dividi in 2 mezze stagioni</p>
              <button onClick={() => setSplit(!split)}
                className={`w-10 h-5 rounded-full transition-colors relative ${split ? 'bg-indigo-600' : 'bg-gray-700'}`}>
                <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${split ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </button>
            </div>
            {split && (
              <div>
                <p className="text-[8px] text-gray-500 mb-1">Prima meta: {halfEps} ep — Pausa — Seconda meta: {(project.num_episodes || 10) - halfEps} ep</p>
                <p className="text-[8px] text-gray-500 mb-1">Pausa tra le due meta:</p>
                <div className="flex gap-1">
                  {[7, 14, 21, 30].map(d => (
                    <button key={d} onClick={() => setPause(d)}
                      className={`px-2 py-1 rounded text-[8px] font-bold border ${pause === d ? 'border-indigo-500 bg-indigo-500/15 text-indigo-400' : 'border-gray-700 text-gray-500'}`}>
                      {d}g
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {project.prossimamente_tv && (
          <div>
            <p className="text-[9px] text-gray-400 font-bold uppercase mb-1">Inizio trasmissione</p>
            <div className="flex flex-wrap gap-1.5">
              {[0, 6, 12, 24, 48, 72].map(h => (
                <button key={h} onClick={() => setDelay(h)}
                  className={`px-3 py-1.5 rounded-lg border text-[9px] font-bold ${delay === h ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-400' : 'border-gray-800 text-gray-500'}`}>
                  {h === 0 ? 'Immediato' : `Dopo ${h}h`}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
          <p className="text-[8px] text-gray-500 font-bold uppercase mb-1">Riepilogo programmazione</p>
          <p className="text-[9px] text-gray-400">
            {policy === 'daily_1' && `1 episodio al giorno per ${project.num_episodes || 10} giorni`}
            {policy === 'daily_3' && `${epsBatch} ep al giorno per ${Math.ceil((project.num_episodes || 10) / epsBatch)} giorni`}
            {policy === 'half_seasons' && split && `${halfEps} ep (${epsBatch} ogni ${interval}g) — pausa ${pause}g — poi ${(project.num_episodes || 10) - halfEps} ep`}
            {policy === 'half_seasons' && !split && `${epsBatch} ep ogni ${interval} giorno/i`}
            {policy === 'all_at_once' && !split && epsBatch >= 3 && interval === 1 && 'Tutti gli episodi subito (binge)'}
            {policy === 'all_at_once' && !split && (epsBatch < 3 || interval > 1) && `${epsBatch} ep ogni ${interval} giorno/i`}
            {policy === 'all_at_once' && split && `2 blocchi con pausa ${pause}g`}
          </p>
        </div>

        <button onClick={save} className="w-full py-2 rounded-lg bg-blue-500/15 border border-blue-500/30 text-blue-400 text-[10px] font-bold" data-testid="save-distribution-btn">
          Conferma Distribuzione
        </button>
      </div>
    </PhaseWrapper>
  );
};

/* ─── STEP FINALE ─── */
const StepFinale = ({ project, onConfirm, loading, seriesType }) => {
  const isAnime = seriesType === 'anime';
  return (
    <PhaseWrapper title="Uscita" subtitle="Riepilogo e conferma" icon={Ticket} color="emerald">
      <div className="space-y-3">
        <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 text-center">
          {project.poster_url ? <img src={project.poster_url} alt="" className="w-20 h-28 object-cover rounded mx-auto mb-2" /> :
            <div className="w-20 h-28 bg-gray-800 rounded mx-auto mb-2 flex items-center justify-center">{isAnime ? <Sparkles className="w-5 h-5 text-gray-700" /> : <Tv className="w-5 h-5 text-gray-700" />}</div>}
          <h3 className="text-sm font-bold text-white">{project.title}</h3>
          <p className="text-[8px] text-gray-500">{ALL_LABELS[project.genre] || project.genre} — {project.num_episodes} episodi</p>
          <p className="text-[8px] text-gray-500">{project.distribution_schedule === 'binge' ? 'Binge' : 'Settimanale'} — {project.prossimamente_tv ? 'In TV' : 'Solo Catalogo'}</p>
        </div>

        {/* Episodes preview */}
        {project.episodes?.length > 0 && (
          <div className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
            <p className="text-[8px] text-gray-500 font-bold uppercase mb-1">Episodi</p>
            {project.episodes.map((ep, i) => (
              <div key={i} className="flex items-center gap-2 py-0.5">
                <span className="text-[7px] text-gray-600 w-4">{ep.number}.</span>
                <span className="text-[8px] text-gray-300 flex-1">{ep.title}</span>
                <span className="text-[7px] text-gray-700">CWSv nascosto</span>
              </div>
            ))}
          </div>
        )}

        <button onClick={onConfirm} disabled={loading}
          className="w-full py-3 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[11px] font-bold disabled:opacity-30" data-testid="confirm-release-btn">
          {loading ? 'Rilascio in corso...' : `Rilascia ${isAnime ? 'Anime' : 'Serie TV'}`}
        </button>
      </div>
    </PhaseWrapper>
  );
};


/* ═══════════════════════════════════════════════════
   MAIN COMPONENT — PipelineSeriesV3
   ═══════════════════════════════════════════════════ */
export default function PipelineSeriesV3({ seriesType = 'tv_series' }) {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [prevoto, setPrevoto] = useState(null);

  const isAnime = seriesType === 'anime';
  const typeLabel = isAnime ? 'Anime' : 'Serie TV';

  const loadProjects = useCallback(async () => {
    try {
      const data = await sapi(`/projects?series_type=${seriesType}`);
      setProjects(Array.isArray(data) ? data : []);
    } catch { /* */ }
  }, [seriesType]);

  const selectProject = useCallback(async (p) => {
    try { const d = await sapi(`/projects/${p.id}`); setSelected(d); setDirty(false); } catch (e) { toast.error(e.message); }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  const currentStep = selected?.pipeline_state || 'idea';
  const stepIndex = SERIES_STEPS.findIndex(s => s.id === currentStep);

  // Fetch prevoto
  useEffect(() => {
    if (!selected?.id) { setPrevoto(null); return; }
    if (currentStep === 'idea' && !selected?.preplot) { setPrevoto(null); return; }
    sapi(`/projects/${selected.id}/prevoto`).then(r => setPrevoto(r)).catch(() => setPrevoto(null));
  }, [selected?.id, currentStep, selected?.updated_at]);

  const createProject = async () => {
    setLoading(true);
    try {
      const res = await sapi('/create', 'POST', { title: isAnime ? 'Nuovo Anime' : 'Nuova Serie', genre: isAnime ? 'shonen' : 'drama', series_type: seriesType, num_episodes: 10, preplot: '' });
      setSelected(res.project); setDirty(false); await loadProjects(); toast.success(`${typeLabel} creata!`);
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };

  const refreshSelected = useCallback(async () => {
    if (!selected?.id) return;
    try { const d = await sapi(`/projects/${selected.id}`); setSelected(d); } catch { /* */ }
  }, [selected?.id]);

  const advance = async (nextState) => {
    if (!selected?.id) return;
    setLoading(true);
    try {
      const d = await sapi(`/projects/${selected.id}/advance`, 'POST', { next_state: nextState });
      setSelected(d); setDirty(false);
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };

  const confirmRelease = async () => {
    if (!selected?.id) return;
    setLoading(true);
    try {
      const r = await sapi(`/projects/${selected.id}/confirm-release`, 'POST');
      toast.success(`${typeLabel} rilasciata! CWSv: ${r.cwsv_display}`);
      setSelected(null);
      navigate('/dashboard');
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };

  const nextStep = SERIES_STEPS[stepIndex + 1]?.id;
  const prevStep = stepIndex > 0 ? SERIES_STEPS[stepIndex - 1]?.id : null;

  const active = projects.filter(p => !['released', 'completed', 'discarded'].includes(p.pipeline_state));

  /* ─── BOARD VIEW ─── */
  if (!selected) {
    return (
      <div className="min-h-screen bg-black text-white pb-28" data-testid="series-board">
        <div className="px-3 pt-24">
          <h2 className="text-lg font-black text-white mb-1">{isAnime ? 'Produzione Anime' : 'Produzione Serie TV'}</h2>
          <p className="text-[10px] text-gray-500 mb-3">Crea o continua una {typeLabel.toLowerCase()}</p>
          <div className="grid grid-cols-3 gap-2">
            <button onClick={createProject} disabled={loading}
              className="aspect-[2/3] rounded-xl border-2 border-dashed border-gray-700 hover:border-amber-500/50 bg-gray-900/30 flex flex-col items-center justify-center gap-1.5 transition-all active:scale-95 disabled:opacity-50"
              data-testid="new-series-btn">
              <div className="w-8 h-8 rounded-full border-2 border-dashed border-gray-600 flex items-center justify-center">
                <Plus className="w-4 h-4 text-gray-500" />
              </div>
              <p className="text-[9px] font-bold text-gray-400">Nuova {typeLabel}</p>
            </button>
            {active.map(p => (
              <button key={p.id} onClick={() => selectProject(p)}
                className="aspect-[2/3] rounded-xl border border-gray-800 bg-gray-900/60 hover:border-amber-500/30 flex flex-col overflow-hidden transition-all active:scale-95"
                data-testid={`series-card-${p.id}`}>
                <div className="flex-1 w-full bg-gray-800 relative">
                  {p.poster_url ? <img src={p.poster_url} alt="" className="w-full h-full object-cover" /> :
                    <div className="w-full h-full flex items-center justify-center">{isAnime ? <Sparkles className="w-5 h-5 text-gray-700" /> : <Tv className="w-5 h-5 text-gray-700" />}</div>}
                  <div className="absolute top-1 right-1 px-1 py-0.5 rounded-full bg-black/70 text-[5px] font-bold text-amber-400 uppercase">{p.pipeline_state || 'idea'}</div>
                </div>
                <div className="p-1.5">
                  <p className="text-[8px] font-bold text-white truncate">{p.title || 'Senza titolo'}</p>
                  <p className="text-[6px] text-gray-500">{ALL_LABELS[p.genre] || p.genre || ''} — {p.num_episodes} ep</p>
                </div>
              </button>
            ))}
          </div>
          {active.length === 0 && <p className="text-center text-gray-600 text-[10px] mt-4">Nessun progetto. Crea la tua prima {typeLabel.toLowerCase()}!</p>}
        </div>
      </div>
    );
  }

  /* ─── PHASE CONTENT ─── */
  const phaseProps = { project: selected, onRefresh: refreshSelected, seriesType };
  const renderPhase = () => {
    switch (currentStep) {
      case 'idea': return <IdeaPhase {...phaseProps} />;
      case 'hype': return <HypePhase {...phaseProps} />;
      case 'cast': return <CastPhase {...phaseProps} />;
      case 'prep': return <PrepPhase {...phaseProps} />;
      case 'ciak': return <CiakPhase {...phaseProps} />;
      case 'finalcut': return <FinalCutPhase {...phaseProps} />;
      case 'marketing': return <MarketingPhase {...phaseProps} />;
      case 'distribution': return <DistributionPhase {...phaseProps} />;
      case 'release_pending': return <StepFinale project={selected} onConfirm={confirmRelease} loading={loading} seriesType={seriesType} />;
      default: return <p className="text-gray-500 text-sm p-4">Stato: {currentStep}</p>;
    }
  };

  return (
    <div className="min-h-screen bg-black text-white pb-28" style={{ overscrollBehavior: 'none' }}>
      <div className="pt-20">
        {/* Header */}
        <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-800/50">
          <button onClick={() => { setSelected(null); loadProjects(); }} className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center shrink-0" data-testid="back-btn">
            <ChevronLeft className="w-3.5 h-3.5 text-gray-400" />
          </button>
          {selected.poster_url ? <img src={selected.poster_url} alt="" className="w-9 h-12 rounded object-cover border border-gray-700 shrink-0" /> :
            <div className="w-9 h-12 rounded bg-gray-800 border border-gray-700 flex items-center justify-center shrink-0">{isAnime ? <Sparkles className="w-3.5 h-3.5 text-gray-600" /> : <Tv className="w-3.5 h-3.5 text-gray-600" />}</div>}
          <div className="flex-1 min-w-0">
            <h2 className="text-xs font-bold text-white truncate">{selected.title || `Nuova ${typeLabel}`}</h2>
            <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
              <span className="text-[7px] px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium uppercase">{ALL_LABELS[selected.genre] || selected.genre}</span>
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
              <span className="text-[6px] px-1 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700 font-bold">{selected.num_episodes} ep</span>
            </div>
          </div>
        </div>

        {/* Advance Button */}
        {currentStep !== 'release_pending' && nextStep && (
          <div className="sticky top-[88px] z-30 px-3 py-1.5 bg-black/90 backdrop-blur-sm border-b border-gray-800/30 flex gap-2">
            {prevStep && (
              <button onClick={() => advance(prevStep)} disabled={loading}
                className="px-3 py-1.5 rounded-lg border border-gray-800 text-gray-500 text-[8px] font-bold disabled:opacity-30">Indietro</button>
            )}
            <button onClick={() => advance(nextStep)} disabled={loading}
              className="flex-1 py-1.5 rounded-lg text-[9px] font-bold bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 disabled:opacity-30"
              data-testid="advance-btn">
              {loading ? '...' : `Avanti → ${SERIES_STEPS[stepIndex + 1]?.label}`}
            </button>
          </div>
        )}

        <StepperBar current={currentStep} />
        {renderPhase()}
        <SeriesTrailerSection project={selected} onRefresh={refreshSelected} />
      </div>
    </div>
  );
}

/* ─── Trailer AI section for series/anime ─── */
function SeriesTrailerSection({ project, onRefresh }) {
  const auth = useContext(AuthContext) || {};
  const { api, user } = auth;
  if (!project?.id || !api || user?.id !== project.user_id) return null;
  return (
    <div className="px-3 mt-3">
      <TrailerGeneratorCard
        contentId={project.id}
        contentTitle={project.title}
        contentGenre={project.genre || ''}
        contentStatus={project.status || project.pipeline_state || ''}
        api={api}
        userCredits={user?.cinepass ?? user?.cinecrediti ?? user?.cinecredits ?? 0}
        canGenerate={true}
        isGuest={!!user?.is_guest}
        onGenerated={onRefresh}
      />
    </div>
  );
}
