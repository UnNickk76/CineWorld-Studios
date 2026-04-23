import React, { useCallback, useEffect, useRef, useState, useMemo, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Film, ChevronLeft, Save, X, Tv, Sparkles, Star, Trash2, RotateCcw } from 'lucide-react';
import { StepperBar as FilmStepperBar, PhaseWrapper, ProgressCircle, STEP_STYLES, GENRE_LABELS, SUBGENRE_MAP, LOCATION_TAGS } from './V3Shared';
import { Check, TrendingUp, Users, Camera, Clapperboard, Scissors, Megaphone, Globe, Ticket } from 'lucide-react';
import { AuthContext } from '../../contexts';
import TrailerGeneratorCard from '../TrailerGeneratorCard';
import CineConfirm from './CineConfirm';
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

/* ─── Episode duration estimator (based on type + genre) ─── */
const estimateEpisodeDuration = (type, genre) => {
  if (type === 'anime') return 22;
  const longGenres = ['drama', 'thriller', 'mystery', 'sci_fi', 'historical', 'fantasy'];
  if (longGenres.includes(genre)) return 55;
  return 45;
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

/* ─── Steps (prep merged into idea; flow: idea→hype→cast→ciak→finalcut→marketing→distribution→uscita) ─── */
const SERIES_STEPS = [
  { id: 'idea', label: 'IDEA', icon: Sparkles, color: 'amber' },
  { id: 'hype', label: 'HYPE', icon: TrendingUp, color: 'orange' },
  { id: 'cast', label: 'CAST', icon: Users, color: 'cyan' },
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
  // Prep fields merged into idea
  const [fmt, setFmt] = useState(project.series_format || 'stagionale');
  const [dur, setDur] = useState(project.episode_duration_min || (seriesType === 'anime' ? 22 : 45));
  const [equip, setEquip] = useState(project.equipment_level || 'medium');
  const [genres, setGenres] = useState({});
  const [saving, setSaving] = useState(false);
  const [genTitles, setGenTitles] = useState(false);
  const [genPoster, setGenPoster] = useState(false);
  const [genScreen, setGenScreen] = useState(false);
  const [posterProgress, setPosterProgress] = useState(0);
  const [screenProgress, setScreenProgress] = useState(0);
  const [selectedEp, setSelectedEp] = useState(null);
  const posterIntRef = useRef(null);
  const screenIntRef = useRef(null);

  useEffect(() => {
    sapi(`/genres?series_type=${seriesType}`).then(d => setGenres(d.genres || {})).catch(() => {});
  }, [seriesType]);

  // Episode ranges by format (applied ONLY after user picks a format)
  const FORMAT_RANGES = {
    miniserie: [4, 6], stagionale: [8, 13], lunga: [20, 26], maratona: [40, 52],
  };
  const genreInfo = genres[genre] || {};
  const baseRange = genreInfo.ep_range || [4, 52];
  const formatRange = FORMAT_RANGES[fmt] || baseRange;
  // Intersect format with genre's ep_range
  const epMin = Math.max(baseRange[0], formatRange[0]);
  const epMax = Math.min(baseRange[1], formatRange[1]);
  const subOpts = SUBGENRE_MAP[genre] || [];
  const validIdea = title.trim().length >= 2 && genre && preplot.trim().length >= 30;
  const hasPoster = !!project.poster_url;
  const hasTitles = (project.episodes || []).length > 0;

  // Clamp numEp into the allowed range whenever format changes
  useEffect(() => {
    if (numEp < epMin) setNumEp(epMin);
    else if (numEp > epMax) setNumEp(epMax);
  }, [fmt, epMin, epMax]);   // eslint-disable-line

  const durations = seriesType === 'anime' ? [22, 24, 30] : [30, 45, 60];
  const formats = [
    { id: 'miniserie', label: 'Miniserie', desc: '4-6 ep' },
    { id: 'stagionale', label: 'Stagionale', desc: '8-13 ep' },
    { id: 'lunga', label: 'Lunga', desc: '20-26 ep' },
    { id: 'maratona', label: 'Maratona', desc: '40+ ep' },
  ];
  const equipLevels = [
    { id: 'low', label: 'Economico', cost: '$' },
    { id: 'medium', label: 'Medio', cost: '$$' },
    { id: 'high', label: 'Premium', cost: '$$$' },
  ];

  const save = async () => {
    setSaving(true);
    try {
      await sapi(`/projects/${project.id}/save-idea`, 'POST', {
        title, genre, subgenres, preplot, num_episodes: numEp, locations,
        series_format: fmt, episode_duration_min: dur, equipment_level: equip,
      });
      toast.success('Idea & Pre-Produzione salvate!');
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
    setGenPoster(true); setPosterProgress(0);
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
    setGenScreen(true); setScreenProgress(0);
    if (screenIntRef.current) clearInterval(screenIntRef.current);
    const start = Date.now();
    screenIntRef.current = setInterval(() => {
      const elapsed = (Date.now() - start) / 1000;
      setScreenProgress(Math.min(95, Math.round(elapsed * 3.8)));
    }, 400);
    try {
      const r = await sapi(`/projects/${project.id}/generate-screenplay`, 'POST');
      setScreenProgress(100);
      toast.success(r.message || 'Sceneggiatura + mini trame generate!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    if (screenIntRef.current) { clearInterval(screenIntRef.current); screenIntRef.current = null; }
    setTimeout(() => { setGenScreen(false); setScreenProgress(0); }, 600);
  };

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
          <p className="text-[8px] text-gray-500">Titolo → Genere → Pre-Produzione → Episodi → Locandina → Titoli → Sceneggiatura</p>
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

      {/* ═══ PRE-PRODUZIONE integrata ═══ */}
      {genre && (
        <div className="p-2 rounded-lg bg-blue-500/5 border border-blue-500/20 space-y-2">
          <p className="text-[8px] text-blue-300 font-bold uppercase tracking-wider flex items-center gap-1">
            <Camera className="w-3 h-3" /> Pre-Produzione
          </p>
          <div className="grid grid-cols-2 gap-1" data-testid="idea-fmt-grid">
            {formats.map(f => (
              <button key={f.id} onClick={() => setFmt(f.id)}
                className={`p-1.5 rounded-lg border text-left ${fmt === f.id ? 'border-blue-500/40 bg-blue-500/10' : 'border-gray-800'}`}
                data-testid={`idea-fmt-${f.id}`}>
                <p className="text-[9px] font-bold text-white">{f.label}</p>
                <p className="text-[7px] text-gray-500">{f.desc}</p>
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            {durations.map(d => (
              <button key={d} onClick={() => setDur(d)}
                className={`flex-1 py-1 rounded text-[8px] font-bold border ${dur === d ? 'border-blue-500/40 bg-blue-500/10 text-blue-300' : 'border-gray-800 text-gray-500'}`}
                data-testid={`idea-dur-${d}`}>
                {d} min
              </button>
            ))}
          </div>
          <div className="grid grid-cols-3 gap-1">
            {equipLevels.map(e => (
              <button key={e.id} onClick={() => setEquip(e.id)}
                className={`py-1 rounded text-[8px] border ${equip === e.id ? 'border-blue-500/40 bg-blue-500/10 text-blue-300' : 'border-gray-800 text-gray-500'}`}
                data-testid={`idea-equip-${e.id}`}>
                <span className="font-bold">{e.label}</span> <span className="opacity-60">{e.cost}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Num Episodes (range derivato dal formato) */}
      {genre && (
        <div>
          <p className="text-[8px] text-gray-500 mb-1">Numero Episodi <span className="text-amber-400/70">({epMin}-{epMax}, formato: {fmt})</span></p>
          <div className="flex items-center gap-2">
            <input type="range" min={epMin} max={epMax} value={Math.max(epMin, Math.min(epMax, numEp))} onChange={e => setNumEp(+e.target.value)}
              className="flex-1 accent-amber-500" data-testid="num-episodes-slider" />
            <span className="text-sm font-bold text-amber-400 w-8 text-center">{numEp}</span>
          </div>
        </div>
      )}

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

      {/* Save Idea + Prep */}
      <button onClick={save} disabled={!validIdea || saving}
        className="w-full py-2 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[10px] font-bold disabled:opacity-30" data-testid="save-idea-btn">
        {saving ? '...' : 'Salva Idea + Pre-Produzione'}
      </button>

      {/* AI Tools — gated sequence: 1.Locandina → 2.Titoli EP → 3.Sceneggiatura AI */}
      {validIdea && project.id && project.prep_completed && (
        <div className="space-y-2">
          {/* Step 1: Poster */}
          <button onClick={generatePoster} disabled={genPoster}
            className="w-full py-2 rounded-lg bg-purple-500/15 border border-purple-500/30 text-purple-300 text-[10px] font-bold disabled:opacity-70 flex items-center justify-center gap-1.5" data-testid="gen-series-poster-btn">
            {genPoster && <InlineProgressCircle value={posterProgress} color="#c084fc" />}
            <span>{genPoster ? `${posterProgress}%` : (hasPoster ? '1. Rigenera Locandina' : '1. Genera Locandina AI')}</span>
          </button>

          {/* Step 2: Episode titles — gated on poster */}
          <button onClick={generateTitles} disabled={genTitles || !hasPoster}
            className="w-full py-2 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-[10px] font-bold disabled:opacity-30" data-testid="gen-titles-btn">
            {genTitles ? '...' : !hasPoster ? '2. Prima la locandina' : (hasTitles ? `2. Rigenera ${numEp} Titoli Episodi` : `2. Genera ${numEp} Titoli Episodi`)}
          </button>

          {/* Step 3: Screenplay — gated on titles */}
          <button onClick={generateScreenplay} disabled={genScreen || !hasTitles}
            className="w-full py-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold disabled:opacity-30 flex items-center justify-center gap-1.5" data-testid="gen-series-screenplay-btn">
            {genScreen && <InlineProgressCircle value={screenProgress} color="#34d399" />}
            <span>{genScreen ? `${screenProgress}%` : !hasTitles ? '3. Prima i titoli episodi' : (project.screenplay_text ? '3. Rigenera Sceneggiatura + Mini Trame' : '3. Genera Sceneggiatura + Mini Trame')}</span>
          </button>
        </div>
      )}

      {!project.prep_completed && validIdea && (
        <p className="text-[9px] text-amber-400/80 text-center font-bold">⚠️ Salva prima Idea + Pre-Produzione per sbloccare Locandina, Titoli e Sceneggiatura</p>
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
      {project.episodes?.length > 0 && (() => {
        const epDur = estimateEpisodeDuration(project.type, project.genre);
        const totalMin = project.episodes.length * epDur;
        const totalH = Math.floor(totalMin / 60);
        const totalR = totalMin % 60;
        return (
          <div className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
            <div className="flex items-baseline justify-between mb-1.5">
              <p className="text-[8px] text-gray-500 font-bold uppercase">Titoli Episodi ({project.episodes.length})</p>
              <p className="text-[8px] text-amber-400/70 font-bold" data-testid="series-total-duration">
                ~{epDur}m · tot {totalH > 0 ? `${totalH}h ${totalR}m` : `${totalR}m`}
              </p>
            </div>
            <div
              className="grid gap-x-3 gap-y-0.5 overflow-x-auto"
              style={{ gridAutoFlow: 'column', gridTemplateRows: 'repeat(12, auto)', gridAutoColumns: 'minmax(160px, 1fr)' }}
              data-testid="series-episodes-grid"
            >
              {project.episodes.map((ep, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedEp(ep)}
                  className="text-left text-[8.5px] text-gray-400 hover:text-amber-300 active:text-amber-400 transition-colors truncate leading-tight py-0.5 flex items-baseline gap-1"
                  title={ep.title}
                  data-testid={`ep-title-${ep.number}`}
                >
                  <span className="text-gray-600">{ep.number}.</span>
                  <span className="truncate flex-1">{ep.title}</span>
                  <span className="text-gray-600 text-[7px] flex-shrink-0">{epDur}m</span>
                </button>
              ))}
            </div>
          </div>
        );
      })()}

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

      {/* Danger zone: Scarta / Ricomincia */}
      <SeriesDangerZone project={project} onRefresh={onRefresh} />
    </div>
  );
};

/* ─── Danger zone for Series/Anime V3 ─── */
const SeriesDangerZone = ({ project, onRefresh }) => {
  const [showDiscard, setShowDiscard] = useState(false);
  const [showRestart, setShowRestart] = useState(false);
  const [busy, setBusy] = useState(false);
  const onDiscard = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await sapi(`/projects/${project.id}/hard-delete`, 'POST');
      toast.success('Progetto eliminato');
      setShowDiscard(false);
      window.location.href = '/produci';
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const onRestart = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await sapi(`/projects/${project.id}/restart`, 'POST');
      toast.success('Progetto ricominciato da zero');
      setShowRestart(false);
      onRefresh?.();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  return (
    <div className="mt-4 pt-4 border-t border-white/5">
      <p className="text-[8px] text-gray-600 uppercase font-bold tracking-wider mb-2 text-center">Zona pericolosa</p>
      <div className="grid grid-cols-2 gap-2">
        <button onClick={() => setShowRestart(true)} data-testid="series-idea-restart-btn"
          className="py-2.5 rounded-xl border border-amber-500/25 bg-amber-500/5 text-amber-400 text-[10px] font-bold flex items-center justify-center gap-1.5 hover:bg-amber-500/10 active:scale-[0.97] transition-all">
          <RotateCcw className="w-3.5 h-3.5" /> Ricomincia
        </button>
        <button onClick={() => setShowDiscard(true)} data-testid="series-idea-discard-btn"
          className="py-2.5 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-[10px] font-bold flex items-center justify-center gap-1.5 hover:bg-rose-500/10 active:scale-[0.97] transition-all">
          <Trash2 className="w-3.5 h-3.5" /> Scarta
        </button>
      </div>
      <CineConfirm open={showDiscard} title="Scartare il progetto?"
        subtitle="Verra' eliminato completamente. Non finira' al mercato."
        confirmLabel={busy ? '...' : 'Scarta per sempre'} confirmTone="rose"
        onConfirm={onDiscard} onCancel={() => !busy && setShowDiscard(false)} />
      <CineConfirm open={showRestart} title="Ricominciare da capo?"
        subtitle="Tutti i dati (titolo, locandina, sceneggiatura, cast, episodi, ecc.) saranno cancellati."
        confirmLabel={busy ? '...' : 'Ricomincia'} confirmTone="amber"
        onConfirm={onRestart} onCancel={() => !busy && setShowRestart(false)} />
    </div>
  );
};
const useTimerProgress = (startedAt, completeAt) => {
  const [pct, setPct] = useState(0);
  useEffect(() => {
    if (!startedAt || !completeAt) { setPct(0); return; }
    const tick = () => {
      const start = new Date(startedAt).getTime();
      const end = new Date(completeAt).getTime();
      const now = Date.now();
      if (end <= start) { setPct(100); return; }
      const p = Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100));
      setPct(p);
    };
    tick();
    const id = setInterval(tick, 4000);
    return () => clearInterval(id);
  }, [startedAt, completeAt]);
  return pct;
};

/* ─── Speedup button (CP cost cap 6) ─── */
const SpeedupButtons = ({ project, stage, onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const options = [
    { pct: 25, cp: 1 },
    { pct: 50, cp: 2 },
    { pct: 75, cp: 4 },
    { pct: 100, cp: 6 },
  ];
  const doSpeedup = async (percentage) => {
    setLoading(true);
    try {
      await sapi(`/projects/${project.id}/speedup`, 'POST', { stage, percentage });
      toast.success(`Avanzato al ${percentage}%`);
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };
  return (
    <div className="grid grid-cols-4 gap-1 mt-2" data-testid={`speedup-${stage}`}>
      {options.map(o => (
        <button key={o.pct} onClick={() => doSpeedup(o.pct)} disabled={loading}
          className="py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-[8px] font-bold hover:bg-cyan-500/20 disabled:opacity-40 flex flex-col items-center">
          <span>{o.pct}%</span>
          <span className="text-[7px] text-cyan-400/70">{o.cp} CP</span>
        </button>
      ))}
    </div>
  );
};

/* ─── HYPE PHASE ─── */
const HypePhase = ({ project, onRefresh }) => {
  const [budget, setBudget] = useState(0);
  const [loading, setLoading] = useState(false);
  const progress = useTimerProgress(project.hype_started_at, project.hype_complete_at);
  const started = !!project.hype_started_at;

  const startHype = async () => {
    setLoading(true);
    try {
      await sapi(`/projects/${project.id}/save-hype`, 'POST', { hype_budget: budget });
      toast.success(started ? 'Budget aggiunto!' : 'Hype avviato!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Hype" subtitle="Costruisci aspettative" icon={TrendingUp} color="orange">
      <div className="space-y-3">
        <div className="flex flex-col items-center py-2">
          <ProgressCircle value={progress} size={90} color="#f97316" />
          {started && <p className="text-[8px] text-gray-500 mt-1">Budget speso: ${(project.hype_budget || 0).toLocaleString()}</p>}
        </div>

        {!started && (
          <>
            <p className="text-[9px] text-gray-400">Budget marketing hype (riduce il timer)</p>
            <div className="grid grid-cols-3 gap-1.5">
              {[0, 50000, 200000].map(b => (
                <button key={b} onClick={() => setBudget(b)}
                  className={`py-2 rounded-lg border text-[9px] font-bold ${budget === b ? 'border-orange-500/40 bg-orange-500/10 text-orange-400' : 'border-gray-800 text-gray-500'}`}>
                  {b === 0 ? 'Gratis (24h)' : b === 50000 ? '$50K (12h)' : '$200K (6h)'}
                </button>
              ))}
            </div>
            <button onClick={startHype} disabled={loading}
              className="w-full py-2 rounded-lg bg-orange-500/15 border border-orange-500/30 text-orange-400 text-[10px] font-bold disabled:opacity-40" data-testid="start-hype-btn">
              {loading ? '...' : 'Avvia Hype'}
            </button>
          </>
        )}

        {started && progress < 100 && <SpeedupButtons project={project} stage="hype" onRefresh={onRefresh} />}
        {started && progress >= 100 && <p className="text-[9px] text-emerald-400 text-center font-bold">Hype completato! Avanza a Cast.</p>}
      </div>
    </PhaseWrapper>
  );
};

/* ─── CAST PHASE (compact but complete) ─── */
const CastPhase = ({ project, onRefresh, seriesType }) => {
  const [loading, setLoading] = useState(false);
  const cast = project.cast || {};
  const actors = cast.actors || [];
  const actorLabel = seriesType === 'anime' ? 'Doppiatori' : 'Attori';

  const autoCast = async () => {
    setLoading(true);
    try {
      await sapi(`/projects/${project.id}/auto-cast`, 'POST');
      toast.success('Cast generato automaticamente!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Cast & Crew" subtitle={`Regia, compositore, ${actorLabel.toLowerCase()}`} icon={Users} color="cyan">
      <div className="space-y-3">
        {/* Showrunner / Regista */}
        <div className="p-2 rounded-lg bg-cyan-500/5 border border-cyan-500/15">
          <p className="text-[7px] text-gray-500 uppercase font-bold">Showrunner / Regista</p>
          <p className="text-[10px] text-white font-bold mt-0.5">{cast.director?.name || <span className="text-gray-500 italic">Da assegnare</span>}</p>
          {cast.director?.stars && <p className="text-[8px] text-amber-400">{'★'.repeat(cast.director.stars)}</p>}
        </div>

        {/* Compositore */}
        <div className="p-2 rounded-lg bg-purple-500/5 border border-purple-500/15">
          <p className="text-[7px] text-gray-500 uppercase font-bold">
            {seriesType === 'anime' ? 'Compositore (OP/ED)' : 'Compositore'}
          </p>
          <p className="text-[10px] text-white font-bold mt-0.5">{cast.composer?.name || <span className="text-gray-500 italic">Da assegnare</span>}</p>
        </div>

        {/* Attori/Doppiatori */}
        <div className="p-2 rounded-lg bg-amber-500/5 border border-amber-500/15">
          <div className="flex items-center justify-between mb-1">
            <p className="text-[7px] text-gray-500 uppercase font-bold">{actorLabel} ({actors.length}/8)</p>
          </div>
          {actors.length > 0 ? (
            <div className="grid grid-cols-2 gap-1">
              {actors.slice(0, 8).map((a, i) => (
                <div key={i} className="text-[9px] text-white truncate flex items-center gap-1" title={a.name}>
                  <span className="text-gray-600 text-[7px]">#{i + 1}</span>
                  <span className="truncate">{a.name}</span>
                  {a.stars && <span className="text-amber-400 text-[7px] flex-shrink-0">{'★'.repeat(a.stars)}</span>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[9px] text-gray-500 italic">Nessuno selezionato</p>
          )}
        </div>

        {/* Auto-cast button */}
        <button onClick={autoCast} disabled={loading}
          className="w-full py-2 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 text-[10px] font-bold disabled:opacity-40" data-testid="series-auto-cast-btn">
          {loading ? '...' : actors.length > 0 ? 'Rigenera Cast Automatico' : 'Genera Cast Automatico (6-8)'}
        </button>
        <p className="text-[7px] text-gray-600 text-center">Preleva dai tuoi attori in agenzia, completa con NPC stelle medie</p>
      </div>
    </PhaseWrapper>
  );
};

/* ─── PREP PHASE (functional) ─── */
const PrepPhase = ({ project, onRefresh, seriesType }) => {
  const [fmt, setFmt] = useState(project.series_format || 'stagionale');
  const [dur, setDur] = useState(project.episode_duration_min || (seriesType === 'anime' ? 22 : 45));
  const [equip, setEquip] = useState(project.equipment_level || 'medium');
  const [loading, setLoading] = useState(false);

  const formats = [
    { id: 'miniserie', label: 'Miniserie', desc: '4-6 ep' },
    { id: 'stagionale', label: 'Stagionale', desc: '8-13 ep' },
    { id: 'lunga', label: 'Lunga', desc: '20-26 ep' },
    { id: 'maratona', label: 'Maratona', desc: '40+ ep' },
  ];
  const durations = seriesType === 'anime' ? [22, 24, 30] : [30, 45, 60];
  const equipLevels = [
    { id: 'low', label: 'Economico', cost: '$', color: 'gray' },
    { id: 'medium', label: 'Medio', cost: '$$', color: 'blue' },
    { id: 'high', label: 'Premium', cost: '$$$', color: 'amber' },
  ];

  const save = async () => {
    setLoading(true);
    try {
      await sapi(`/projects/${project.id}/save-prep`, 'POST', {
        series_format: fmt, episode_duration_min: dur, equipment_level: equip,
      });
      toast.success('Pre-produzione salvata!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Pre-Produzione" subtitle="Formato, durata episodi, equipaggiamento" icon={Camera} color="blue">
      <div className="space-y-3">
        <p className="text-[8px] text-gray-500 uppercase font-bold">Formato</p>
        <div className="grid grid-cols-2 gap-1.5">
          {formats.map(f => (
            <button key={f.id} onClick={() => setFmt(f.id)}
              className={`p-2 rounded-lg border text-left ${fmt === f.id ? 'border-blue-500/40 bg-blue-500/10' : 'border-gray-800'}`}
              data-testid={`prep-fmt-${f.id}`}>
              <p className="text-[9px] font-bold text-white">{f.label}</p>
              <p className="text-[7px] text-gray-500">{f.desc}</p>
            </button>
          ))}
        </div>

        <p className="text-[8px] text-gray-500 uppercase font-bold">Durata Episodio</p>
        <div className="flex gap-1.5">
          {durations.map(d => (
            <button key={d} onClick={() => setDur(d)}
              className={`flex-1 py-1.5 rounded-lg border text-[9px] font-bold ${dur === d ? 'border-blue-500/40 bg-blue-500/10 text-blue-400' : 'border-gray-800 text-gray-500'}`}
              data-testid={`prep-dur-${d}`}>
              {d} min
            </button>
          ))}
        </div>

        <p className="text-[8px] text-gray-500 uppercase font-bold">Equipaggiamento</p>
        <div className="grid grid-cols-3 gap-1.5">
          {equipLevels.map(e => (
            <button key={e.id} onClick={() => setEquip(e.id)}
              className={`p-2 rounded-lg border ${equip === e.id ? `border-${e.color}-500/40 bg-${e.color}-500/10` : 'border-gray-800'}`}
              data-testid={`prep-equip-${e.id}`}>
              <p className="text-[9px] font-bold text-white">{e.label}</p>
              <p className={`text-[8px] ${equip === e.id ? `text-${e.color}-400` : 'text-gray-500'}`}>{e.cost}</p>
            </button>
          ))}
        </div>

        <button onClick={save} disabled={loading}
          className="w-full py-2 rounded-lg bg-blue-500/15 border border-blue-500/30 text-blue-400 text-[10px] font-bold disabled:opacity-40" data-testid="save-prep-btn">
          {loading ? '...' : 'Salva Pre-Produzione'}
        </button>
      </div>
    </PhaseWrapper>
  );
};

/* ─── CIAK PHASE (real timer) ─── */
const CiakPhase = ({ project, onRefresh, seriesType }) => {
  const [loading, setLoading] = useState(false);
  const progress = useTimerProgress(project.ciak_started_at, project.ciak_complete_at);
  const started = !!project.ciak_started_at;
  const minPerEp = seriesType === 'anime' ? 20 : 30;
  const totalMin = (project.num_episodes || 10) * minPerEp;

  const startCiak = async () => {
    setLoading(true);
    try {
      await sapi(`/projects/${project.id}/start-ciak`, 'POST');
      toast.success('Riprese avviate!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Riprese" subtitle={`${minPerEp} min reali per episodio`} icon={Clapperboard} color="red">
      <div className="space-y-3">
        <div className="flex flex-col items-center py-2">
          <ProgressCircle value={progress} size={90} color="#ef4444" />
          <p className="text-[9px] text-gray-500 mt-2">{project.num_episodes} ep × {minPerEp} min = <span className="text-white font-bold">{totalMin} min</span></p>
          {started && project.ciak_hours && (
            <p className="text-[8px] text-gray-600 mt-0.5">Durata: {project.ciak_hours}h reali</p>
          )}
        </div>

        {!started && (
          <button onClick={startCiak} disabled={loading}
            className="w-full py-2 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-[10px] font-bold disabled:opacity-40" data-testid="start-ciak-btn">
            {loading ? '...' : '🎬 Avvia Riprese'}
          </button>
        )}

        {started && progress < 100 && <SpeedupButtons project={project} stage="ciak" onRefresh={onRefresh} />}
        {started && progress >= 100 && <p className="text-[9px] text-emerald-400 text-center font-bold">Riprese completate! Avanza a Final Cut.</p>}
      </div>
    </PhaseWrapper>
  );
};

/* ─── FINALCUT PHASE (real timer) ─── */
const FinalCutPhase = ({ project, onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const progress = useTimerProgress(project.finalcut_started_at, project.finalcut_complete_at);
  const started = !!project.finalcut_started_at;

  const startFC = async () => {
    setLoading(true);
    try {
      await sapi(`/projects/${project.id}/start-finalcut`, 'POST');
      toast.success('Post-produzione avviata!');
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Post-Produzione" subtitle="Montaggio e mix finale" icon={Scissors} color="purple">
      <div className="space-y-3">
        <div className="flex flex-col items-center py-2">
          <ProgressCircle value={progress} size={90} color="#a855f7" />
          {started && project.finalcut_hours && (
            <p className="text-[8px] text-gray-600 mt-0.5">Durata: {project.finalcut_hours}h reali</p>
          )}
        </div>

        {!started && (
          <button onClick={startFC} disabled={loading}
            className="w-full py-2 rounded-lg bg-purple-500/15 border border-purple-500/30 text-purple-400 text-[10px] font-bold disabled:opacity-40" data-testid="start-finalcut-btn">
            {loading ? '...' : '✂️ Avvia Post-Produzione'}
          </button>
        )}

        {started && progress < 100 && <SpeedupButtons project={project} stage="finalcut" onRefresh={onRefresh} />}
        {started && progress >= 100 && <p className="text-[9px] text-emerald-400 text-center font-bold">Post-produzione completata! Avanza a Marketing.</p>}
      </div>
    </PhaseWrapper>
  );
};

/* ─── MARKETING PHASE ─── */
const MarketingPhase = ({ project, onRefresh }) => {
  const [prossimamente, setProssimamente] = useState(project.prossimamente_tv || false);
  const [sponsors, setSponsors] = useState([]);
  const [selectedSponsors, setSelectedSponsors] = useState(project.marketing_config?.sponsor_ids || []);
  const [adBreaks, setAdBreaks] = useState(project.ad_breaks_per_episode ?? 0);
  const [campaignDays, setCampaignDays] = useState(project.marketing_config?.campaign_days || 7);
  const [preview, setPreview] = useState({ upfront_revenue: 0, revenue_cut_pct: 60, interest_penalty_pct: 0 });
  const [saving, setSaving] = useState(false);
  const completed = !!project.marketing_completed;

  // Fetch ad platforms once
  useEffect(() => {
    const load = async () => {
      try {
        const API = process.env.REACT_APP_BACKEND_URL;
        const token = localStorage.getItem('cineworld_token');
        const r = await fetch(`${API}/api/pipeline-v3/ad-platforms`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        const d = await r.json();
        setSponsors(d.platforms || []);
      } catch (_) { /* ignore */ }
    };
    load();
  }, []);

  // Fetch preview on changes (debounced)
  useEffect(() => {
    const t = setTimeout(async () => {
      try {
        const qs = `sponsor_ids=${selectedSponsors.join(',')}&ad_breaks_min=${adBreaks}&campaign_days=${campaignDays}`;
        const r = await sapi(`/projects/${project.id}/marketing-preview?${qs}`);
        setPreview(r);
      } catch (_) { /* ignore */ }
    }, 250);
    return () => clearTimeout(t);
  }, [selectedSponsors, adBreaks, campaignDays, project.id]);

  const toggleSponsor = (id) => {
    setSelectedSponsors(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const save = async () => {
    setSaving(true);
    try {
      const r = await sapi(`/projects/${project.id}/save-marketing-v3`, 'POST', {
        sponsor_ids: selectedSponsors,
        ad_breaks_min: adBreaks,
        campaign_days: campaignDays,
        prossimamente_tv: prossimamente,
      });
      toast.success(`Marketing salvato! +$${(r.upfront_credited || 0).toLocaleString()} accreditati`);
      onRefresh?.();
    } catch (e) { toast.error(e.message); }
    setSaving(false);
  };

  return (
    <PhaseWrapper title="Marketing & TV" subtitle="Sponsor, pubblicità episodi, promozione" icon={Megaphone} color="green">
      <div className="space-y-3">
        {/* Sponsor packages */}
        <div className="p-2 rounded-lg bg-green-500/5 border border-green-500/15">
          <p className="text-[8px] text-green-300 font-bold uppercase mb-1.5">Sponsor ({selectedSponsors.length}/{sponsors.length})</p>
          <div className="grid grid-cols-2 gap-1">
            {sponsors.map(s => (
              <button key={s.id} onClick={() => toggleSponsor(s.id)}
                className={`p-1.5 rounded-lg border text-left ${selectedSponsors.includes(s.id) ? 'border-green-500/50 bg-green-500/10' : 'border-gray-800'}`}
                data-testid={`sponsor-${s.id}`}>
                <p className="text-[9px] font-bold text-white truncate">{s.name_it || s.name}</p>
                <p className="text-[7px] text-gray-500">x{s.reach_multiplier} · ${(s.cost_per_day / 1000).toFixed(0)}K/g</p>
              </button>
            ))}
          </div>
        </div>

        {/* Campaign days */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <p className="text-[8px] text-gray-500 uppercase font-bold">Giorni campagna</p>
            <span className="text-[10px] font-bold text-amber-400">{campaignDays}g</span>
          </div>
          <input type="range" min={3} max={30} value={campaignDays} onChange={e => setCampaignDays(+e.target.value)}
            className="w-full accent-amber-500" data-testid="campaign-days-slider" />
        </div>

        {/* Ad breaks slider — the KEY tradeoff */}
        <div className="p-2 rounded-lg bg-amber-500/5 border border-amber-500/20 space-y-1.5">
          <div className="flex items-center justify-between">
            <p className="text-[8px] text-amber-300 font-bold uppercase">Pubblicità / Episodio</p>
            <span className="text-sm font-bold text-amber-400">{adBreaks} min</span>
          </div>
          <input type="range" min={0} max={8} step={1} value={adBreaks} onChange={e => setAdBreaks(+e.target.value)}
            className="w-full accent-amber-500" data-testid="ad-breaks-slider" />
          <div className="flex items-center justify-between text-[8px]">
            <span className="text-gray-500">0 min = no ads</span>
            <span className="text-gray-500">8 min max</span>
          </div>
          <div className={`p-1.5 rounded text-[9px] leading-snug ${adBreaks === 0 ? 'bg-red-500/5 border border-red-500/20 text-red-300' : 'bg-blue-500/5 border border-blue-500/20 text-blue-300'}`}>
            {adBreaks === 0 ? (
              <>⚠️ <b>-60% ricavi giornalieri</b> fino a ritrasmissione, ma sponsor pagano full upfront e <b>interesse pubblico max</b>.</>
            ) : (
              <>✅ Solo <b>-10% ricavi giornalieri</b> · Sponsor pagano {Math.round((adBreaks / 8) * 100)}% upfront · Interesse pubblico <b>-{preview.interest_penalty_pct}%</b> (rischio flop)</>
            )}
          </div>
        </div>

        {/* Live preview */}
        <div className="p-2 rounded-lg bg-white/[0.03] border border-white/5 grid grid-cols-3 gap-1 text-center">
          <div>
            <p className="text-[7px] text-gray-500 uppercase">Upfront</p>
            <p className="text-[11px] font-bold text-emerald-400" data-testid="preview-upfront">${(preview.upfront_revenue / 1000).toFixed(0)}K</p>
          </div>
          <div>
            <p className="text-[7px] text-gray-500 uppercase">Cut /giorno</p>
            <p className="text-[11px] font-bold text-orange-400">-{preview.revenue_cut_pct}%</p>
          </div>
          <div>
            <p className="text-[7px] text-gray-500 uppercase">Interesse</p>
            <p className="text-[11px] font-bold text-red-400">-{preview.interest_penalty_pct}%</p>
          </div>
        </div>

        {/* Prossimamente TV Toggle */}
        <div className="p-2 rounded-lg bg-green-500/5 border border-green-500/15 flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-white">Prossimamente in TV</p>
            <p className="text-[7px] text-gray-500">Mostra nella dashboard</p>
          </div>
          <button onClick={() => setProssimamente(!prossimamente)}
            className={`w-12 h-6 rounded-full transition-colors relative ${prossimamente ? 'bg-green-600' : 'bg-gray-700'}`} data-testid="prossimamente-toggle">
            <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${prossimamente ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        </div>

        <button onClick={save} disabled={saving}
          className="w-full py-2 rounded-lg bg-green-500/15 border border-green-500/30 text-green-400 text-[10px] font-bold disabled:opacity-40" data-testid="save-marketing-btn">
          {saving ? '...' : completed ? 'Aggiorna Marketing' : 'Conferma Marketing'}
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
  const [targetStation, setTargetStation] = useState(project.target_tv_station_id || null);
  const [myStations, setMyStations] = useState([]);
  const [stationsLoaded, setStationsLoaded] = useState(false);

  useEffect(() => {
    if (!project?.prossimamente_tv || stationsLoaded) return;
    const token = localStorage.getItem('cineworld_token');
    fetch(`${API}/api/my-owned-tv-stations`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => setMyStations(d?.stations || []))
      .catch(() => setMyStations([]))
      .finally(() => setStationsLoaded(true));
  }, [project?.prossimamente_tv, stationsLoaded]);

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
        target_tv_station_id: targetStation,
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

        {/* Target TV Station (owner's stations + "Nessuna emittente") */}
        {project.prossimamente_tv && (
          <div>
            <p className="text-[9px] text-gray-400 font-bold uppercase mb-1">Emittente di destinazione</p>
            <div className="space-y-1.5">
              <button onClick={() => setTargetStation(null)} data-testid="station-none"
                className={`w-full p-2 rounded-lg border text-left transition-all ${targetStation === null ? 'border-amber-500/40 bg-amber-500/10' : 'border-gray-800 hover:border-gray-700'}`}>
                <p className="text-[10px] font-bold text-white flex items-center gap-1.5">
                  <Globe className="w-3 h-3 text-amber-400" /> Nessuna emittente
                </p>
                <p className="text-[7px] text-gray-500">Scegli piu' tardi dal menu della serie, oppure vendi al mercato</p>
              </button>
              {myStations.length === 0 && stationsLoaded && (
                <p className="text-[8px] text-gray-600 italic px-1">Non possiedi emittenti TV. Puoi crearne una da Infrastrutture.</p>
              )}
              {myStations.map(st => (
                <button key={st.id} onClick={() => setTargetStation(st.id)} data-testid={`station-${st.id}`}
                  className={`w-full p-2 rounded-lg border text-left transition-all ${targetStation === st.id ? 'border-blue-500/40 bg-blue-500/10' : 'border-gray-800 hover:border-gray-700'}`}>
                  <p className="text-[10px] font-bold text-white flex items-center gap-1.5">
                    <Tv className="w-3 h-3 text-blue-400" /> {st.station_name || st.name || 'Emittente'}
                  </p>
                  <p className="text-[7px] text-gray-500">
                    Lv.{st.infra_level || 1} · {st.nation || 'Italia'} · {st.film_cap ? `${st.film_count || 0}/${st.film_cap} film` : 'capacita disponibile'}
                  </p>
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
  const [selectedEp, setSelectedEp] = useState(null);
  const epDur = (isAnime ? 22 : (project.episode_duration_min || 45));
  return (
    <PhaseWrapper title="Uscita" subtitle="Riepilogo e conferma" icon={Ticket} color="emerald">
      <div className="space-y-3">
        <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 text-center">
          {project.poster_url ? <img src={project.poster_url} alt="" className="w-20 h-28 object-cover rounded mx-auto mb-2" /> :
            <div className="w-20 h-28 bg-gray-800 rounded mx-auto mb-2 flex items-center justify-center">{isAnime ? <Sparkles className="w-5 h-5 text-gray-700" /> : <Tv className="w-5 h-5 text-gray-700" />}</div>}
          <h3 className="text-sm font-bold text-white">{project.title}</h3>
          <p className="text-[8px] text-gray-500">{ALL_LABELS[project.genre] || project.genre} — {project.num_episodes} episodi</p>
          <p className="text-[8px] text-gray-500">{project.distribution_schedule === 'binge' ? 'Binge' : 'Settimanale'} — {project.prossimamente_tv ? 'In TV' : 'Solo Catalogo'}</p>
          {project.marketing_upfront_revenue > 0 && (
            <p className="text-[8px] text-emerald-400 mt-1">Upfront sponsor: ${(project.marketing_upfront_revenue || 0).toLocaleString()}</p>
          )}
          {typeof project.ad_breaks_per_episode === 'number' && (
            <p className="text-[8px] text-amber-400">Pubblicità: {project.ad_breaks_per_episode} min/ep · Cut: -{project.revenue_cut_percentage || 60}%/g</p>
          )}
        </div>

        {/* Episodes — clickable to view mini_plot */}
        {project.episodes?.length > 0 && (
          <div className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
            <p className="text-[8px] text-gray-500 font-bold uppercase mb-1">Episodi ({project.episodes.length})</p>
            {project.episodes.map((ep, i) => (
              <button key={i} onClick={() => setSelectedEp(ep)}
                className="w-full flex items-center gap-2 py-0.5 text-left hover:bg-white/[0.03] active:bg-white/[0.05] rounded transition-colors"
                data-testid={`final-ep-${ep.number}`}>
                <span className="text-[7px] text-gray-600 w-4">{ep.number}.</span>
                <span className="text-[8px] text-gray-300 flex-1 truncate">{ep.title}</span>
                <span className="text-[7px] text-gray-700 flex-shrink-0">{epDur}m · CWSv nascosto</span>
              </button>
            ))}
          </div>
        )}

        <button onClick={onConfirm} disabled={loading}
          className="w-full py-3 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[11px] font-bold disabled:opacity-30" data-testid="confirm-release-btn">
          {loading ? 'Rilascio in corso...' : `Rilascia ${isAnime ? 'Anime' : 'Serie TV'}`}
        </button>
      </div>

      {/* Episode mini-plot modal */}
      {selectedEp && (
        <div className="fixed inset-0 z-[70] bg-black/70 flex items-center justify-center p-4" onClick={() => setSelectedEp(null)}>
          <div className="bg-[#111113] border border-amber-500/30 rounded-xl max-w-sm w-full p-4 space-y-3" onClick={(e) => e.stopPropagation()}>
            <div>
              <p className="text-[8px] text-amber-400/80 uppercase font-bold">Episodio {selectedEp.number}</p>
              <h4 className="text-base font-bold text-white mt-0.5">{selectedEp.title}</h4>
            </div>
            <div className="text-[11px] text-gray-300 leading-relaxed whitespace-pre-wrap min-h-[72px]">
              {selectedEp.mini_plot || <span className="italic text-gray-500">Mini-trama non ancora disponibile.</span>}
            </div>
            <button onClick={() => setSelectedEp(null)}
              className="w-full py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[10px] font-bold" data-testid="close-final-ep-modal">
              Chiudi
            </button>
          </div>
        </div>
      )}
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

        {/* Advance Button — with per-step gating */}
        {currentStep !== 'release_pending' && nextStep && (() => {
          const timerProgress = (startAt, endAt) => {
            if (!startAt || !endAt) return 0;
            const s = new Date(startAt).getTime(), e = new Date(endAt).getTime(), n = Date.now();
            if (e <= s) return 100;
            return Math.min(100, Math.max(0, ((n - s) / (e - s)) * 100));
          };
          const reason = (() => {
            if (currentStep === 'idea') {
              if (!selected.title || !selected.genre) return 'Completa Titolo e Genere';
              if (!selected.preplot || selected.preplot.length < 30) return 'Sinossi min 30 caratteri';
              if (!selected.prep_completed) return 'Salva Idea + Pre-Produzione';
              if (!selected.poster_url) return 'Genera la Locandina';
              if (!(selected.episodes && selected.episodes.length > 0)) return 'Genera i Titoli Episodi';
              if (!selected.screenplay_text) return 'Genera la Sceneggiatura';
              return null;
            }
            if (currentStep === 'hype') {
              if (!selected.hype_started_at) return 'Avvia prima la campagna Hype';
              const pct = timerProgress(selected.hype_started_at, selected.hype_complete_at);
              if (pct < 100) return `Hype al ${Math.round(pct)}%. Usa CP per velocizzare`;
              return null;
            }
            if (currentStep === 'cast') {
              const cast = selected.cast || {};
              if (!cast.actors || cast.actors.length < 1) return 'Genera prima il Cast';
              return null;
            }
            if (currentStep === 'ciak') {
              if (!selected.ciak_started_at) return 'Avvia prima le Riprese';
              const pct = timerProgress(selected.ciak_started_at, selected.ciak_complete_at);
              if (pct < 100) return `Riprese al ${Math.round(pct)}%`;
              return null;
            }
            if (currentStep === 'finalcut') {
              if (!selected.finalcut_started_at) return 'Avvia prima la Post-Produzione';
              const pct = timerProgress(selected.finalcut_started_at, selected.finalcut_complete_at);
              if (pct < 100) return `Post-produzione al ${Math.round(pct)}%`;
              return null;
            }
            if (currentStep === 'marketing') {
              if (!selected.marketing_completed) return 'Conferma prima il Marketing';
              return null;
            }
            return null;
          })();
          const blocked = !!reason;
          return (
            <div className="sticky top-[88px] z-30 px-3 py-1.5 bg-black/90 backdrop-blur-sm border-b border-gray-800/30 flex gap-2">
              {prevStep && (
                <button onClick={() => advance(prevStep)} disabled={loading}
                  className="px-3 py-1.5 rounded-lg border border-gray-800 text-gray-500 text-[8px] font-bold disabled:opacity-30">Indietro</button>
              )}
              <button
                onClick={() => { if (!blocked) advance(nextStep); else toast.error(reason); }}
                disabled={loading || blocked}
                className={`flex-1 py-1.5 rounded-lg text-[9px] font-bold disabled:opacity-40 ${
                  blocked
                    ? 'bg-gray-800/60 border border-gray-700/40 text-gray-500 cursor-not-allowed'
                    : 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400'
                }`}
                data-testid="advance-btn"
                title={reason || ''}
              >
                {loading ? '...' : blocked ? reason : `Avanti → ${SERIES_STEPS[stepIndex + 1]?.label}`}
              </button>
            </div>
          );
        })()}

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
