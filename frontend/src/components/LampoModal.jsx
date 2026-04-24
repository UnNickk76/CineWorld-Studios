/**
 * LampoModal — contiene:
 *  • ModeChooser: scelta iniziale "Completa" vs "LAMPO!"
 *  • LampoForm: titolo + genere + sotto-genere + pretrama + budget tier
 *  • LampoProgress: cerchio 0-100% con messaggi AI
 *  • LampoResult: schermata finale con locandina, CWSv, cast, bottone Rilascia
 *
 * Props:
 *   open, onClose
 *   contentType: 'film' | 'tv_series' | 'anime'
 *   onStartCompleta: () => void   (callback per pipeline normale)
 *   onReleased: (result) => void  (callback dopo rilascio)
 */
import React, { useState, useEffect, useContext, useMemo } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import {
  Zap, Film as FilmIcon, Sparkles, Tv, X, DollarSign, TrendingUp,
  TrendingDown, Check, Loader2, Trophy, ChevronRight
} from 'lucide-react';

const GENRES = {
  film: [
    { value: 'action', label: 'Azione' },
    { value: 'drama', label: 'Drammatico' },
    { value: 'comedy', label: 'Commedia' },
    { value: 'horror', label: 'Horror' },
    { value: 'thriller', label: 'Thriller' },
    { value: 'romance', label: 'Romantico' },
    { value: 'scifi', label: 'Fantascienza' },
    { value: 'fantasy', label: 'Fantasy' },
  ],
  tv_series: [
    { value: 'drama', label: 'Drammatica' },
    { value: 'comedy', label: 'Sitcom' },
    { value: 'crime', label: 'Crime' },
    { value: 'thriller', label: 'Thriller' },
    { value: 'fantasy', label: 'Fantasy' },
    { value: 'scifi', label: 'Fantascienza' },
  ],
  anime: [
    { value: 'shonen', label: 'Shonen' },
    { value: 'seinen', label: 'Seinen' },
    { value: 'shojo', label: 'Shojo' },
    { value: 'mecha', label: 'Mecha' },
    { value: 'isekai', label: 'Isekai' },
  ],
};

const CT_META = {
  film:      { title: 'Film',     icon: FilmIcon,  color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
  tv_series: { title: 'Serie TV', icon: Tv,        color: 'text-blue-400',    bg: 'bg-blue-500/10',    border: 'border-blue-500/30' },
  anime:     { title: 'Anime',    icon: Sparkles,  color: 'text-orange-400',  bg: 'bg-orange-500/10',  border: 'border-orange-500/30' },
};

const BUDGET_COSTS = {
  film:     { low: 50000,  mid: 150000, high: 400000 },
  tv_series:{ low: 80000,  mid: 250000, high: 700000 },
  anime:    { low: 100000, mid: 350000, high: 900000 },
};

const BUDGET_CP = {
  film:     { low: 0, mid: 3, high: 8 },
  tv_series:{ low: 0, mid: 5, high: 12 },
  anime:    { low: 0, mid: 6, high: 15 },
};

// ───── ModeChooser ─────
function ModeChooser({ contentType, onPickCompleta, onPickLampo, onClose }) {
  const meta = CT_META[contentType];
  const CtIcon = meta.icon;
  return (
    <div className="p-4" data-testid="mode-chooser">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <CtIcon className={`w-5 h-5 ${meta.color}`} />
          <h2 className="text-xl font-['Bebas_Neue'] text-white">Come vuoi produrre?</h2>
        </div>
        <button onClick={onClose} className="text-white/50 hover:text-white p-1"><X className="w-4 h-4" /></button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Completa */}
        <button
          onClick={onPickCompleta}
          data-testid="mode-completa-btn"
          className="group relative overflow-hidden p-4 rounded-xl border-2 border-cyan-500/30 bg-gradient-to-br from-cyan-500/10 to-blue-500/5 hover:border-cyan-400/60 hover:scale-[1.02] transition-all text-left"
        >
          <div className="flex items-center gap-2 mb-2">
            <Trophy className="w-5 h-5 text-cyan-400" />
            <h3 className="text-lg font-['Bebas_Neue'] text-cyan-200">Completa</h3>
          </div>
          <p className="text-[11px] text-cyan-100/80 leading-snug mb-3">
            Pipeline completa con decisioni creative su ogni fase. Massimo controllo, massima qualità.
          </p>
          <div className="text-[9px] uppercase tracking-wider text-cyan-400/80 font-bold">
            Idea → Hype → Cast → Riprese → Montaggio → Marketing → Distribuzione
          </div>
          <ChevronRight className="absolute bottom-3 right-3 w-4 h-4 text-cyan-400/50 group-hover:text-cyan-300 group-hover:translate-x-1 transition-all" />
        </button>

        {/* Lampo */}
        <button
          onClick={onPickLampo}
          data-testid="mode-lampo-btn"
          className="group relative overflow-hidden p-4 rounded-xl border-2 border-amber-500/40 bg-gradient-to-br from-amber-500/15 to-orange-500/10 hover:border-amber-300 hover:scale-[1.02] transition-all text-left"
        >
          <div className="absolute top-0 right-0 px-2 py-0.5 text-[8px] font-black uppercase bg-amber-400 text-black rounded-bl-lg">Rapido</div>
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-amber-400 drop-shadow-[0_0_6px_rgba(251,191,36,0.8)]" />
            <h3 className="text-lg font-['Bebas_Neue'] text-amber-200">LAMPO!</h3>
          </div>
          <p className="text-[11px] text-amber-100/90 leading-snug mb-3">
            L'AI fa tutto per te in ~2 minuti. Pretrama + budget e via. Qualità legata al livello del tuo studio.
          </p>
          <div className="text-[9px] uppercase tracking-wider text-amber-300/80 font-bold">
            Idea → 🤖 AI → Pronto al rilascio
          </div>
          <ChevronRight className="absolute bottom-3 right-3 w-4 h-4 text-amber-400 group-hover:text-amber-200 group-hover:translate-x-1 transition-all" />
        </button>
      </div>
    </div>
  );
}

// ───── LampoForm ─────
function LampoForm({ contentType, onStart, onBack, onClose }) {
  const { api } = useContext(AuthContext);
  const meta = CT_META[contentType];
  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState(GENRES[contentType][0].value);
  const [preplot, setPreplot] = useState('');
  const [budgetTier, setBudgetTier] = useState('mid');
  const [numEpisodes, setNumEpisodes] = useState(10);
  const [submitting, setSubmitting] = useState(false);

  const cost = BUDGET_COSTS[contentType][budgetTier];
  const cp = BUDGET_CP[contentType][budgetTier];

  const canSubmit = title.trim().length >= 2 && preplot.trim().length >= 10 && !submitting;

  const handleStart = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      const res = await api.post('/lampo/start', {
        content_type: contentType,
        title: title.trim(),
        genre,
        preplot: preplot.trim(),
        budget_tier: budgetTier,
        num_episodes: contentType !== 'film' ? numEpisodes : undefined,
      });
      toast.success(`Produzione LAMPO avviata! Costo: $${(res.data.scaled_cost || 0).toLocaleString()}`);
      onStart(res.data.project);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore nell\'avvio');
      setSubmitting(false);
    }
  };

  return (
    <div className="p-4" data-testid="lampo-form">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-400 drop-shadow-[0_0_6px_rgba(251,191,36,0.8)]" />
          <h2 className="text-xl font-['Bebas_Neue'] text-amber-200">Produzione LAMPO!</h2>
        </div>
        <button onClick={onClose} className="text-white/50 hover:text-white p-1"><X className="w-4 h-4" /></button>
      </div>

      <div className="space-y-3">
        <div>
          <label className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Titolo</label>
          <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Es. Ultimo Volo"
            className="bg-black/40 border-amber-500/20 text-sm mt-1" data-testid="lampo-title-input" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Genere</label>
            <select value={genre} onChange={e => setGenre(e.target.value)}
              className="w-full mt-1 h-9 rounded-md bg-black/40 border border-amber-500/20 text-sm px-2 text-white"
              data-testid="lampo-genre-select">
              {GENRES[contentType].map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
            </select>
          </div>
          {contentType !== 'film' && (
            <div>
              <label className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Episodi</label>
              <select value={numEpisodes} onChange={e => setNumEpisodes(parseInt(e.target.value))}
                className="w-full mt-1 h-9 rounded-md bg-black/40 border border-amber-500/20 text-sm px-2 text-white"
                data-testid="lampo-episodes-select">
                {[6, 8, 10, 12, 16, 24].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          )}
        </div>

        <div>
          <label className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Pretrama</label>
          <Textarea value={preplot} onChange={e => setPreplot(e.target.value)} rows={3} maxLength={500}
            placeholder="Descrivi brevemente la storia. L'AI la svilupperà in sceneggiatura + episodi."
            className="bg-black/40 border-amber-500/20 text-sm mt-1 resize-none" data-testid="lampo-preplot-input" />
          <div className="text-right text-[9px] text-slate-500 mt-0.5">{preplot.length}/500</div>
        </div>

        <div>
          <label className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Budget</label>
          <div className="grid grid-cols-3 gap-2 mt-1">
            {[
              { key: 'low',  label: 'Basso',  icon: TrendingDown, color: 'border-red-500/30 bg-red-500/5 text-red-300', mod: '-1.0 CWSv' },
              { key: 'mid',  label: 'Medio',  icon: DollarSign,   color: 'border-slate-500/40 bg-slate-500/5 text-slate-300', mod: 'Baseline' },
              { key: 'high', label: 'Alto',   icon: TrendingUp,   color: 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300', mod: '+0.8 CWSv' },
            ].map(b => {
              const Bicon = b.icon;
              const active = budgetTier === b.key;
              const amount = BUDGET_COSTS[contentType][b.key];
              const cpCost = BUDGET_CP[contentType][b.key];
              return (
                <button key={b.key} onClick={() => setBudgetTier(b.key)} data-testid={`lampo-budget-${b.key}`}
                  className={`p-2 rounded-lg border-2 text-left transition-all ${active ? b.color + ' scale-[1.03]' : 'border-white/5 bg-white/[0.02] text-white/50 hover:border-white/15'}`}>
                  <div className="flex items-center gap-1 mb-0.5">
                    <Bicon className="w-3 h-3" />
                    <span className="text-[10px] font-bold uppercase">{b.label}</span>
                  </div>
                  <div className="text-[9px] font-semibold">${amount.toLocaleString()}</div>
                  {cpCost > 0 && <div className="text-[8px] opacity-80">+{cpCost} CP</div>}
                  <div className="text-[8px] italic opacity-70 mt-0.5">{b.mod}</div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <Button variant="ghost" onClick={onBack} className="h-10 text-[11px] text-slate-400 hover:text-slate-200" data-testid="lampo-back-btn">Indietro</Button>
          <Button onClick={handleStart} disabled={!canSubmit}
            className="flex-1 h-10 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black font-bold text-sm"
            data-testid="lampo-start-btn">
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Zap className="w-4 h-4 mr-1" /> AVVIA LAMPO</>}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ───── LampoProgress ─────
function LampoProgress({ project, onDone, onClose }) {
  const { api } = useContext(AuthContext);
  const [state, setState] = useState(project);

  useEffect(() => {
    let cancel = false;
    const poll = async () => {
      while (!cancel) {
        try {
          const res = await api.get(`/lampo/${project.id}/progress`);
          if (cancel) return;
          setState(res.data);
          if (res.data.status === 'ready' || res.data.status === 'error') {
            onDone(res.data);
            return;
          }
        } catch {}
        await new Promise(r => setTimeout(r, 3000));
      }
    };
    poll();
    return () => { cancel = true; };
  }, [project.id]);

  const pct = state.progress_pct || 0;
  const msg = state.progress_message || 'In corso…';
  const circ = 2 * Math.PI * 70;
  const offset = circ - (pct / 100) * circ;

  return (
    <div className="p-4 flex flex-col items-center text-center" data-testid="lampo-progress">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-5 h-5 text-amber-400 animate-pulse drop-shadow-[0_0_8px_rgba(251,191,36,0.9)]" />
        <h2 className="text-xl font-['Bebas_Neue'] text-amber-200">In Produzione LAMPO</h2>
      </div>
      <p className="text-xs text-slate-300 mb-6">"{state.title}"</p>

      <div className="relative w-48 h-48 flex items-center justify-center my-4">
        <svg className="transform -rotate-90 w-full h-full" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r="70" stroke="rgba(251,191,36,0.1)" strokeWidth="6" fill="none" />
          <circle cx="80" cy="80" r="70" stroke="url(#lampo-grad)" strokeWidth="6" fill="none"
            strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease-out', filter: 'drop-shadow(0 0 8px rgba(251,191,36,0.6))' }} />
          <defs>
            <linearGradient id="lampo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#fbbf24" />
              <stop offset="100%" stopColor="#f97316" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-5xl font-['Bebas_Neue'] text-amber-100">{pct}</span>
          <span className="text-xs text-amber-300/70">%</span>
        </div>
      </div>

      <p className="text-sm text-amber-200/90 font-medium animate-pulse">{msg}</p>
      <p className="text-[10px] text-slate-500 mt-2 italic">Puoi chiudere: la produzione continua in background.</p>

      <Button variant="ghost" onClick={onClose} className="mt-4 h-8 text-[10px] text-slate-400" data-testid="lampo-minimize-btn">
        Riduci a icona
      </Button>
    </div>
  );
}

// ───── LampoResult ─────
function LampoResult({ project, onReleased, onClose, api }) {
  const [releasing, setReleasing] = useState(false);
  const CT = CT_META[project.content_type];
  const ContentIcon = CT.icon;

  const handleRelease = async () => {
    setReleasing(true);
    try {
      const res = await api.post(`/lampo/${project.id}/release`);
      toast.success(res.data.message || 'Rilasciato!');
      onReleased(res.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore nel rilascio');
      setReleasing(false);
    }
  };

  const scoreColor = project.cwsv >= 8 ? 'text-emerald-400' :
                     project.cwsv >= 6.5 ? 'text-amber-400' :
                     project.cwsv >= 5 ? 'text-orange-400' : 'text-red-400';

  return (
    <div className="p-4 max-h-[80vh] overflow-y-auto" data-testid="lampo-result">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Check className="w-5 h-5 text-emerald-400" />
          <h2 className="text-xl font-['Bebas_Neue'] text-white">Produzione Completa!</h2>
        </div>
        <button onClick={onClose} className="text-white/50 hover:text-white p-1"><X className="w-4 h-4" /></button>
      </div>

      {/* Poster placeholder + CWSv */}
      <div className="flex gap-3 mb-4">
        <div className={`w-24 h-36 rounded-lg overflow-hidden ${CT.bg} ${CT.border} border flex items-center justify-center flex-shrink-0`}>
          {project.poster_url ? <img src={project.poster_url} alt="" className="w-full h-full object-cover" /> :
            <ContentIcon className={`w-8 h-8 ${CT.color}/30`} />}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-bold text-white truncate">{project.title}</h3>
          <p className="text-[10px] text-slate-400 capitalize">{project.genre} · {CT.title}</p>
          <div className="mt-2 p-2 rounded-lg bg-black/40 border border-amber-500/20">
            <div className="text-[9px] uppercase text-slate-400 font-semibold">Valutazione CWSv</div>
            <div className={`text-3xl font-['Bebas_Neue'] ${scoreColor}`}>{project.cwsv?.toFixed(1) || '—'}</div>
          </div>
        </div>
      </div>

      {/* Pretrama */}
      <div className="mb-3 p-3 rounded-lg bg-black/40 border border-white/5">
        <div className="text-[9px] uppercase text-slate-400 font-semibold mb-1">Pretrama</div>
        <p className="text-[11px] text-slate-200 leading-snug">{project.preplot}</p>
      </div>

      {/* Cast */}
      {project.cast && (
        <div className="mb-3 p-3 rounded-lg bg-black/40 border border-white/5">
          <div className="text-[9px] uppercase text-slate-400 font-semibold mb-2">Cast</div>
          <div className="space-y-1">
            {project.cast.director && <div className="text-[10px]"><span className="text-slate-500">Regia:</span> <span className="text-white">{project.cast.director.name}</span></div>}
            {project.cast.actors?.length > 0 && (
              <div className="text-[10px]"><span className="text-slate-500">{project.content_type === 'anime' ? 'Disegnatori' : 'Attori'}:</span> <span className="text-white">{project.cast.actors.map(a => a.name).join(', ')}</span></div>
            )}
            {project.cast.composer && <div className="text-[10px]"><span className="text-slate-500">Musiche:</span> <span className="text-white">{project.cast.composer.name}</span></div>}
          </div>
        </div>
      )}

      {/* Episodes (serie/anime) */}
      {project.episodes?.length > 0 && (
        <div className="mb-3 p-3 rounded-lg bg-black/40 border border-white/5">
          <div className="text-[9px] uppercase text-slate-400 font-semibold mb-2">Episodi ({project.episodes.length})</div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {project.episodes.slice(0, 5).map((ep, i) => (
              <div key={i} className="text-[10px] leading-snug">
                <span className="text-amber-400 font-bold">Ep.{ep.episode_number || (i + 1)}</span> <span className="text-slate-300">— {ep.synopsis}</span>
              </div>
            ))}
            {project.episodes.length > 5 && <div className="text-[9px] text-slate-500 italic">…e altri {project.episodes.length - 5} episodi</div>}
          </div>
        </div>
      )}

      {/* Marketing + sponsor */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="p-2 rounded-lg bg-black/40 border border-white/5 text-center">
          <div className="text-[8px] uppercase text-slate-500">Marketing</div>
          <div className="text-[11px] font-bold text-cyan-300 capitalize">{project.marketing_tier || 'medio'}</div>
        </div>
        <div className="p-2 rounded-lg bg-black/40 border border-white/5 text-center">
          <div className="text-[8px] uppercase text-slate-500">Attrezzature</div>
          <div className="text-[11px] font-bold text-violet-300 capitalize">{project.equipment_tier || project.budget_tier}</div>
        </div>
      </div>

      {/* Action button */}
      <Button onClick={handleRelease} disabled={releasing}
        className="w-full h-11 bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 text-black font-bold text-sm"
        data-testid="lampo-release-btn">
        {releasing ? <Loader2 className="w-4 h-4 animate-spin" /> :
         project.content_type === 'film' ? '🎬 Rilascia al Cinema' : '📺 Manda alla mia TV'}
      </Button>
      <p className="text-[9px] text-slate-500 text-center mt-2 italic">
        Nota: i progetti LAMPO non hanno trailer (né ora né in futuro).
      </p>
    </div>
  );
}

// ───── Main Dialog ─────
export default function LampoModal({ open, contentType, onClose, onPickCompleta }) {
  const { api } = useContext(AuthContext);
  const [phase, setPhase] = useState('chooser'); // chooser|form|progress|result
  const [activeProject, setActiveProject] = useState(null);

  useEffect(() => {
    if (open) setPhase('chooser');
  }, [open]);

  const handleClose = () => {
    setPhase('chooser');
    setActiveProject(null);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="max-w-md p-0 bg-gradient-to-b from-[#0c0a08] to-[#050302] border border-amber-500/20" data-testid="lampo-modal">
        {phase === 'chooser' && (
          <ModeChooser
            contentType={contentType}
            onPickCompleta={() => { handleClose(); onPickCompleta?.(); }}
            onPickLampo={() => setPhase('form')}
            onClose={handleClose}
          />
        )}
        {phase === 'form' && (
          <LampoForm
            contentType={contentType}
            onStart={(p) => { setActiveProject(p); setPhase('progress'); }}
            onBack={() => setPhase('chooser')}
            onClose={handleClose}
          />
        )}
        {phase === 'progress' && activeProject && (
          <LampoProgress
            project={activeProject}
            onDone={(p) => { setActiveProject(p); setPhase('result'); }}
            onClose={handleClose}
          />
        )}
        {phase === 'result' && activeProject && (
          <LampoResult
            project={activeProject}
            api={api}
            onReleased={() => handleClose()}
            onClose={handleClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
