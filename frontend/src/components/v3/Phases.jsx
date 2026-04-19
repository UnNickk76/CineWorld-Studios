import React, { useState, useEffect, useRef } from 'react';
import { TrendingUp, Camera, Clapperboard, Scissors, Megaphone, Globe, Ticket, Film, Award, Zap, Clock, Check, Coins, Trash2, AlertTriangle, Handshake } from 'lucide-react';
import { PhaseWrapper, ProgressCircle, v3api } from './V3Shared';

const SPEEDUP_COSTS = { 25: 10, 50: 15, 75: 20, 100: 25 };

// Cost decreases exponentially inverse based on current progress
function getSpeedupCost(baseCost, currentProgress) {
  const remaining = (100 - currentProgress) / 100;
  return Math.max(1, Math.ceil(baseCost * remaining));
}

/* ═══════ HYPE ═══════ */
export const HypePhase = ({ film, onRefresh, toast }) => {
  const [strategy, setStrategy] = useState(film.hype_strategy || film.hype_notes || 'balanced');
  const [duration, setDuration] = useState(film.hype_duration || film.hype_budget || 12);
  const [loading, setLoading] = useState(false);
  const [configured, setConfigured] = useState(!!(film.hype_started_at || film.hype_notes || film.hype_budget > 0));
  const [now, setNow] = useState(Date.now());
  const progressRef = useRef(null);

  // Update configured from backend on film change
  useEffect(() => {
    setConfigured(!!(film.hype_started_at || film.hype_notes || film.hype_budget > 0));
  }, [film.hype_started_at, film.hype_notes, film.hype_budget]);

  // Real-time tick every second for live countdown and smooth progress
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Calculate progress & ETA from backend timestamps (fallback to film.hype_progress)
  const hasTimestamps = !!(film.hype_started_at && film.hype_complete_at);
  const startedAt = hasTimestamps ? new Date(film.hype_started_at).getTime() : now;
  const completeAt = hasTimestamps ? new Date(film.hype_complete_at).getTime() : startedAt;
  const totalMs = Math.max(1, completeAt - startedAt);
  const elapsedMs = now - startedAt;
  const remainingMs = hasTimestamps ? Math.max(0, completeAt - now) : 0;
  const hypeProgress = hasTimestamps
    ? Math.min(100, Math.max(0, (elapsedMs / totalMs) * 100))
    : (film.hype_progress || 0);
  const isComplete = hasTimestamps ? remainingMs <= 0 : hypeProgress >= 100;

  // Format ETA: "Mancano: 1h 23m 45s"
  const remH = Math.floor(remainingMs / 3600000);
  const remM = Math.floor((remainingMs % 3600000) / 60000);
  const remS = Math.floor((remainingMs % 60000) / 1000);
  const etaLabel = isComplete
    ? 'Completato!'
    : remH > 0
      ? `Mancano: ${remH}h ${remM}m ${remS}s`
      : remM > 0
        ? `Mancano: ${remM}m ${remS}s`
        : `Mancano: ${remS}s`;

  // Poll backend for live progress (every 10s when configured and not done) to stay in sync
  useEffect(() => {
    if (configured && !isComplete) {
      progressRef.current = setInterval(async () => {
        try {
          await onRefresh();
        } catch { /* */ }
      }, 10000);
      return () => { if (progressRef.current) clearInterval(progressRef.current); };
    }
  }, [configured, isComplete, onRefresh]);

  const save = async () => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/save-hype`, 'POST', { hype_notes: strategy, budget: duration });
      await onRefresh();
      setConfigured(true);
      toast?.('Hype configurato!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const speedup = async (pct) => {
    if (hypeProgress >= 100) { toast?.('Già al 100%!', 'error'); return; }
    setLoading(true);
    try {
      const res = await v3api(`/films/${film.id}/speedup`, 'POST', { stage: 'hype', percentage: pct });
      await onRefresh();
      toast?.(`Velocizzato! (-${res.cost} CP)`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Hype Machine" subtitle="Costruisci aspettativa strategica" icon={TrendingUp} color="orange">
      <div className="space-y-3">

        {/* Hype Progress Bar — always visible when configured */}
        {configured && (
          <div className="p-3 rounded-xl bg-orange-500/5 border border-orange-500/15 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[8px] text-gray-500 uppercase font-bold">Avanzamento Hype</span>
              <span className="text-[10px] font-black text-orange-400">{Math.floor(hypeProgress)}%</span>
            </div>
            <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-orange-600 to-amber-400 transition-all duration-1000 ease-out"
                style={{ width: `${Math.min(100, hypeProgress)}%` }}
              />
            </div>
            {hasTimestamps && (
              <div className="flex items-center justify-center gap-2" data-testid="hype-eta-countdown">
                <Clock className="w-3 h-3 text-orange-400" />
                <span className={`text-[10px] font-bold ${isComplete ? 'text-emerald-400' : 'text-orange-300'}`}>
                  {etaLabel}
                </span>
              </div>
            )}
            <p className="text-[7px] text-gray-600 text-center">
              {hypeProgress >= 100 ? 'Hype al massimo! Avanza al prossimo step.' :
               hypeProgress >= 50 ? 'L\'hype cresce... velocizza per completare!' :
               'Campagna in corso. L\'hype si costruisce nel tempo.'}
            </p>
          </div>
        )}

        <p className="text-[8px] text-gray-500 uppercase font-bold">Strategia</p>
        <div className="grid grid-cols-3 gap-1.5">
          {['sprint','balanced','slow_build'].map(s => (
            <button key={s} onClick={() => setStrategy(s)} disabled={configured}
              className={`p-2 rounded-lg text-center border text-[9px] font-bold transition-all ${
                strategy === s ? 'bg-orange-500/10 border-orange-500/30 text-orange-400' : 'border-gray-800 text-gray-500'
              } disabled:opacity-60`}>{s === 'sprint' ? 'Sprint' : s === 'balanced' ? 'Bilanciata' : 'Costruzione'}</button>
          ))}
        </div>
        <div>
          <div className="flex justify-between text-[8px] mb-1">
            <span className="text-gray-500">Durata campagna</span>
            <span className="text-orange-400 font-bold">{duration}h</span>
          </div>
          <input type="range" min={2} max={24} value={duration} onChange={e => setDuration(+e.target.value)}
            disabled={configured}
            className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orange-500 disabled:opacity-50" />
        </div>

        {!configured && (
          <button onClick={save} disabled={loading} className="w-full text-[9px] py-2 rounded-xl bg-orange-500/15 border border-orange-500/30 text-orange-400 disabled:opacity-30 font-bold" data-testid="save-hype-btn">
            {loading ? '...' : 'Configura Hype'}
          </button>
        )}

        {configured && (
          <>
            <p className="text-[8px] text-gray-500 uppercase font-bold">Velocizza (a pagamento)</p>
            <div className="grid grid-cols-2 gap-1.5">
              {[25,50,75,100].map(p => {
                const cost = getSpeedupCost(SPEEDUP_COSTS[p], hypeProgress);
                const remaining = 100 - hypeProgress;
                const gain = Math.ceil(remaining * (p / 100));
                return (
                  <button key={p} onClick={() => speedup(p)} disabled={loading || hypeProgress >= 100}
                    className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg bg-yellow-500/5 border border-yellow-500/15 text-yellow-400 text-[8px] font-bold disabled:opacity-30 hover:bg-yellow-500/10 transition-all"
                    data-testid={`speedup-${p}`}>
                    <Zap className="w-3 h-3" />
                    <span>+{gain}%</span>
                    <span className="flex items-center gap-0.5 text-[7px] text-cyan-400 ml-1">
                      <Coins className="w-2.5 h-2.5" />{cost}
                    </span>
                  </button>
                );
              })}
            </div>
          </>
        )}

      </div>
    </PhaseWrapper>
  );
};

const FILM_FORMATS = [
  { id: 'cortometraggio', label: 'Cortometraggio', range: '25-40 min' },
  { id: 'medio', label: 'Medio', range: '50-80 min' },
  { id: 'standard', label: 'Standard', range: '90-120 min' },
  { id: 'epico', label: 'Epico', range: '130-180 min' },
  { id: 'kolossal', label: 'Kolossal', range: '2h10-4h' },
];

/* ═══════ PREP ═══════ */
export const PrepPhase = ({ film, onRefresh, toast }) => {
  const [equipment, setEquipment] = useState(film.prep_equipment || []);
  const [cgi, setCgi] = useState(film.prep_cgi || []);
  const [vfx, setVfx] = useState(film.prep_vfx || []);
  const [extras, setExtras] = useState(film.prep_extras || 0);
  const [filmFormat, setFilmFormat] = useState(film.film_format || 'standard');
  const [options, setOptions] = useState({ equipment: [], cgi: [], vfx: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => { v3api(`/films/${film.id}/prep-options`).then(setOptions).catch(() => {}); }, [film.id]);

  const toggle = (list, set, id) => set(v => v.includes(id) ? v.filter(x => x !== id) : [...v, id]);

  const save = async () => {
    setLoading(true);
    try {
      const res = await v3api(`/films/${film.id}/save-prep-full`, 'POST', { equipment, cgi, vfx, extras_count: extras, film_format: filmFormat });
      await onRefresh();
      const days = res.shooting_days;
      toast?.(days ? `Pre-produzione confermata! Riprese stimate: ${days} giorni` : 'Pre-produzione confermata!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const renderTags = (label, items, selected, set) => (
    <div>
      <p className="text-[8px] text-gray-500 uppercase font-bold mb-1">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map(it => (
          <button key={it.id} onClick={() => toggle(selected, set, it.id)}
            className={`px-2 py-1 rounded-lg text-[8px] font-bold border ${
              selected.includes(it.id) ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : 'border-gray-800 text-gray-500'
            }`}>{it.name} <span className="text-[6px] opacity-60">${(it.cost/1000).toFixed(0)}K</span></button>
        ))}
      </div>
    </div>
  );

  return (
    <PhaseWrapper title="Pre-Produzione" subtitle="Attrezzature, effetti speciali e formato" icon={Camera} color="blue">
      <div className="space-y-3">
        {/* Film Format */}
        <div>
          <p className="text-[8px] text-gray-500 uppercase font-bold mb-1">Formato Film</p>
          <div className="grid grid-cols-2 gap-1.5">
            {FILM_FORMATS.map(f => (
              <button key={f.id} onClick={() => setFilmFormat(f.id)}
                className={`p-2 rounded-lg border text-left transition-all ${
                  filmFormat === f.id ? 'bg-blue-500/10 border-blue-500/30' : 'border-gray-800 hover:border-gray-600'
                }`}>
                <p className={`text-[9px] font-bold ${filmFormat === f.id ? 'text-blue-400' : 'text-gray-400'}`}>{f.label}</p>
                <p className="text-[7px] text-gray-600">{f.range}</p>
              </button>
            ))}
          </div>
        </div>

        {renderTags('Attrezzature', options.equipment || [], equipment, setEquipment)}
        {renderTags('CGI', options.cgi || [], cgi, setCgi)}
        {renderTags('VFX', options.vfx || [], vfx, setVfx)}
        <div>
          <div className="flex justify-between text-[8px] mb-1">
            <span className="text-gray-500">Comparse</span><span className="text-blue-400 font-bold">{extras}</span>
          </div>
          <input type="range" min={0} max={1000} step={50} value={extras} onChange={e => setExtras(+e.target.value)}
            className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500" />
        </div>

        {/* Shooting estimate */}
        {film.shooting_days > 0 && (
          <div className="p-2 rounded-lg bg-blue-500/5 border border-blue-500/15 flex items-center justify-between">
            <span className="text-[8px] text-gray-400">Riprese stimate</span>
            <span className="text-[10px] font-bold text-blue-400">{film.shooting_days} giorni</span>
          </div>
        )}

        <button onClick={save} disabled={loading} className="w-full text-[9px] py-2 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-400 disabled:opacity-30 font-bold">
          {loading ? '...' : 'Conferma Pre-Produzione'}
        </button>
      </div>
    </PhaseWrapper>
  );
};

/* ═══════ CIAK ═══════ */
export const CiakPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState(false);
  const [now, setNow] = useState(Date.now());
  const shootDays = film.shooting_days || 14;

  // Real-time countdown tick every second
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Auto-start timer if missing (film was in CIAK before timer code deployed)
  useEffect(() => {
    if (!film.ciak_started_at && film.pipeline_state === 'ciak') {
      v3api(`/films/${film.id}/start-ciak`, 'POST').then(() => onRefresh?.()).catch(() => {});
    }
  }, [film.id, film.ciak_started_at, film.pipeline_state, onRefresh]);

  // Calculate real progress from timestamps
  const startedAt = film.ciak_started_at ? new Date(film.ciak_started_at).getTime() : now;
  const completeAt = film.ciak_complete_at ? new Date(film.ciak_complete_at).getTime() : startedAt + shootDays * 3600000;
  const totalMs = Math.max(1, completeAt - startedAt);
  const elapsedMs = now - startedAt;
  const remainingMs = Math.max(0, completeAt - now);
  const progress = Math.min(100, Math.max(0, (elapsedMs / totalMs) * 100));
  const isComplete = remainingMs <= 0;

  // Format remaining time
  const remainH = Math.floor(remainingMs / 3600000);
  const remainM = Math.floor((remainingMs % 3600000) / 60000);
  const remainS = Math.floor((remainingMs % 60000) / 1000);
  const remainLabel = isComplete ? 'Completato!' : remainH > 0 ? `${remainH}h ${remainM}m` : `${remainM}m ${remainS}s`;

  const daysDone = Math.min(shootDays, Math.floor((progress / 100) * shootDays));

  const speedup = async (pct) => {
    const cost = getSpeedupCost(SPEEDUP_COSTS[pct], progress);
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/speedup`, 'POST', { stage: 'ciak', percentage: pct });
      await onRefresh();
      toast?.(`Velocizzato (-${cost} CP)`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="CIAK! Riprese" subtitle="Le riprese del film" icon={Clapperboard} color="red">
      <div className="space-y-3">
        {/* Shooting info */}
        <div className="flex items-center justify-between px-2">
          <div className="text-center">
            <p className="text-[7px] text-gray-500 uppercase">Durata riprese</p>
            <p className="text-sm font-black text-red-400">{shootDays} giorni</p>
          </div>
          <div className="text-center">
            <p className="text-[7px] text-gray-500 uppercase">Giorno</p>
            <p className="text-sm font-black text-white">{daysDone}/{shootDays}</p>
          </div>
          <div className="text-center">
            <p className="text-[7px] text-gray-500 uppercase">Formato</p>
            <p className="text-[9px] font-bold text-blue-400 capitalize">{(film.film_format || 'standard').replace(/_/g, ' ')}</p>
          </div>
        </div>

        {/* Real countdown + progress */}
        <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/15 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[8px] text-gray-500 uppercase font-bold">Avanzamento Riprese</span>
            <span className="text-[10px] font-black text-red-400">{Math.floor(progress)}%</span>
          </div>
          <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-red-600 to-orange-400 transition-all duration-1000 ease-out"
              style={{ width: `${Math.min(100, progress)}%` }} />
          </div>
          <div className="flex items-center justify-center gap-2">
            <Clock className="w-3 h-3 text-red-400" />
            <span className={`text-[10px] font-bold ${isComplete ? 'text-emerald-400' : 'text-red-300'}`}>
              {isComplete ? 'Riprese completate!' : remainLabel + ' rimanenti'}
            </span>
          </div>
        </div>

        {/* Speedup buttons */}
        {!isComplete && (
          <>
            <p className="text-[8px] text-gray-500 uppercase font-bold">Velocizza Riprese (a pagamento)</p>
            <div className="grid grid-cols-2 gap-1.5">
              {[25,50,75,100].map(p => {
                const cost = getSpeedupCost(SPEEDUP_COSTS[p], progress);
                const remH = Math.floor((remainingMs * (p / 100)) / 3600000);
                const remM = Math.floor(((remainingMs * (p / 100)) % 3600000) / 60000);
                const saved = remH > 0 ? `-${remH}h${remM}m` : `-${remM}m`;
                return (
                  <button key={p} onClick={() => speedup(p)} disabled={loading}
                    className="flex flex-col items-center gap-0.5 px-2 py-2 rounded-lg bg-yellow-500/5 border border-yellow-500/15 text-yellow-400 text-[8px] font-bold disabled:opacity-30 hover:bg-yellow-500/10 transition-all"
                    data-testid={`ciak-speedup-${p}`}>
                    <div className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      <span>{p}%</span>
                      <span className="flex items-center gap-0.5 text-[7px] text-cyan-400">
                        <Coins className="w-2.5 h-2.5" />{cost}
                      </span>
                    </div>
                    <span className="text-[6px] text-gray-500">{saved}</span>
                  </button>
                );
              })}
            </div>
          </>
        )}

        {isComplete && (
          <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/15 text-center">
            <p className="text-[9px] text-emerald-400 font-bold">Riprese completate! Premi Avanti per il prossimo step.</p>
          </div>
        )}
      </div>
    </PhaseWrapper>
  );
};

/* ═══════ FINAL CUT MESSAGES ═══════ */
const FC_MESSAGES = [
  "Sincronizzazione audio e video in corso...",
  "Il montatore sta analizzando le scene migliori...",
  "Correzione colore della scena d'apertura...",
  "Taglio delle scene superflue...",
  "Aggiunta delle transizioni tra le sequenze...",
  "Mixaggio della colonna sonora...",
  "Bilanciamento dei livelli audio...",
  "Revisione del ritmo narrativo...",
  "Inserimento degli effetti sonori ambientali...",
  "Ottimizzazione della fotografia...",
  "Il regista sta rivedendo il primo montaggio...",
  "Rifinitura dei dialoghi in post-produzione...",
  "Stabilizzazione delle riprese in movimento...",
  "Aggiunta dei titoli di testa...",
  "Rendering delle scene in CGI...",
  "Compositing degli effetti visivi...",
  "Correzione delle imperfezioni visive...",
  "Il colorist sta lavorando alla palette cromatica...",
  "Inserimento della musica di sottofondo...",
  "Taglio e cucitura delle scene d'azione...",
  "Revisione della continuita tra le scene...",
  "Aggiunta degli effetti di transizione...",
  "Sincronizzazione del labiale...",
  "Ottimizzazione della scena climax...",
  "Rifinitura del finale del film...",
  "Mixaggio finale in Dolby Surround...",
  "Il sound designer crea atmosfere uniche...",
  "Inserimento dei sottotitoli...",
  "Revisione del montaggio alternato...",
  "Correzione della grana dell'immagine...",
  "Aggiunta del logo della casa di produzione...",
  "Il regista approva la scena del confronto...",
  "Rifinitura delle scene romantiche...",
  "Ottimizzazione dei tempi comici...",
  "Bilanciamento delle scene di tensione...",
  "Aggiunta della dissolvenza in chiusura...",
  "Rendering finale delle scene notturne...",
  "Revisione del flashback centrale...",
  "Aggiunta degli effetti di pioggia digitale...",
  "Il montatore taglia 15 minuti superflui...",
  "Inserimento del tema musicale principale...",
  "Correzione dell'esposizione nelle scene esterne...",
  "Aggiunta dei crediti finali...",
  "Revisione dell'arco narrativo del protagonista...",
  "Ottimizzazione della scena d'inseguimento...",
  "Il colorist aggiunge toni caldi al tramonto...",
  "Sincronizzazione dei movimenti di camera...",
  "Rifinitura della scena del colpo di scena...",
  "Aggiunta del sonoro ambientale della citta...",
  "Rendering degli effetti particellari...",
  "Revisione del montaggio parallelo...",
  "Il regista vuole rifare il finale...",
  "Aggiunta delle scritte in sovrimpressione...",
  "Correzione del bilanciamento del bianco...",
  "Ottimizzazione della scena onirica...",
  "Mixaggio della voce narrante...",
  "Inserimento degli effetti di slow-motion...",
  "Il montatore riordina le sequenze temporali...",
  "Aggiunta della colonna sonora orchestrale...",
  "Rifinitura delle scene di massa...",
  "Correzione delle ombre nelle scene interne...",
  "Rendering delle esplosioni in CGI...",
  "Revisione del pacing del secondo atto...",
  "Il sound designer aggiunge il battito cardiaco...",
  "Aggiunta del filtro vintage alle scene retro...",
  "Ottimizzazione della scena subacquea...",
  "Inserimento dei rumori di fondo realistici...",
  "Correzione del contrasto nelle scene buie...",
  "Il regista e soddisfatto della scena madre...",
  "Aggiunta delle particelle di polvere atmosferica...",
  "Rifinitura della scena di apertura...",
  "Rendering delle creature digitali...",
  "Mixaggio dei livelli di dialogo e musica...",
  "Revisione dell'epilogo...",
  "Aggiunta degli easter egg nascosti...",
  "Il colorist crea il look definitivo del film...",
  "Ottimizzazione delle scene di volo...",
  "Inserimento del tema dell'antagonista...",
  "Correzione dei riflessi nelle scene con vetro...",
  "Aggiunta delle dissolvenze incrociate...",
  "Rifinitura della colonna sonora emotiva...",
  "Il montatore lavora alla versione Director's Cut...",
  "Rendering finale a risoluzione 4K...",
  "Revisione complessiva del montaggio...",
  "Aggiunta dei suoni foley personalizzati...",
  "Ottimizzazione della compressione dinamica...",
  "Il regista firma l'approvazione del montaggio...",
  "Inserimento del teaser per i titoli di coda...",
  "Correzione finale della timeline...",
  "Esportazione del master in formato DCP...",
  "Controllo qualita dell'output finale...",
  "Verifica della sincronizzazione su tutti i canali...",
  "Il film sta prendendo la sua forma definitiva...",
  "Preparazione del pacchetto per la distribuzione...",
  "Ultimi ritocchi al mix audio 7.1...",
  "Generazione della versione per il cinema...",
  "Il montaggio e quasi pronto...",
  "Revisione finale prima dell'approvazione...",
  "Il team di post-produzione da gli ultimi tocchi...",
  "Encoding del master file definitivo...",
];

/* ═══════ FINAL CUT ═══════ */
export const FinalCutPhase = ({ film, onRefresh, toast }) => {
  const [notes, setNotes] = useState(film.finalcut_notes || '');
  const [loading, setLoading] = useState(false);
  const [now, setNow] = useState(Date.now());
  const [msgIdx, setMsgIdx] = useState(0);
  const [filmDuration, setFilmDuration] = useState(null);
  const started = !!film.finalcut_started_at;

  // Tick every second for countdown
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Rotate messages every 4 seconds
  useEffect(() => {
    if (started) {
      const msgTimer = setInterval(() => setMsgIdx(prev => (prev + 1) % FC_MESSAGES.length), 4000);
      return () => clearInterval(msgTimer);
    }
  }, [started]);

  // Auto-start timer if in finalcut but no timestamps
  useEffect(() => {
    if (!film.finalcut_started_at && film.pipeline_state === 'finalcut') {
      v3api(`/films/${film.id}/start-finalcut`, 'POST').then(() => onRefresh?.()).catch(() => {});
    }
  }, [film.id, film.finalcut_started_at, film.pipeline_state, onRefresh]);

  // Calculate progress from timestamps
  const startedAt = film.finalcut_started_at ? new Date(film.finalcut_started_at).getTime() : now;
  const completeAt = film.finalcut_complete_at ? new Date(film.finalcut_complete_at).getTime() : startedAt + 12 * 3600000;
  const totalMs = Math.max(1, completeAt - startedAt);
  const elapsedMs = now - startedAt;
  const remainingMs = Math.max(0, completeAt - now);
  const progress = Math.min(100, Math.max(0, (elapsedMs / totalMs) * 100));
  const isComplete = remainingMs <= 0;

  const remainH = Math.floor(remainingMs / 3600000);
  const remainM = Math.floor((remainingMs % 3600000) / 60000);
  const remainS = Math.floor((remainingMs % 60000) / 1000);
  const remainLabel = isComplete ? 'Completato!' : remainH > 0 ? `${remainH}h ${remainM}m` : `${remainM}m ${remainS}s`;
  const fcHours = film.finalcut_hours || Math.round(totalMs / 3600000);

  // Load film duration after complete
  useEffect(() => {
    if (isComplete && !filmDuration) {
      v3api(`/films/${film.id}/film-duration`).then(d => {
        setFilmDuration(d);
        // Save to project for header display
        v3api(`/films/${film.id}/save-idea`, 'POST', {
          title: film.title || '', genre: film.genre || 'drama',
          preplot: film.preplot || '',
          subgenres: film.subgenres || [], locations: film.locations || [],
        }).catch(() => {});
      }).catch(() => {});
    }
  }, [isComplete, film.id, filmDuration]);

  const save = async () => {
    setLoading(true);
    try {
      const res = await v3api(`/films/${film.id}/save-finalcut`, 'POST', { finalcut_notes: notes });
      await onRefresh();
      toast?.(`Montaggio avviato! Durata: ${res.finalcut_hours}h`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const speedup = async (pct) => {
    const cost = getSpeedupCost(SPEEDUP_COSTS[pct], progress);
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/speedup`, 'POST', { stage: 'finalcut', percentage: pct });
      await onRefresh();
      toast?.(`Velocizzato (-${cost} CP)`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Final Cut" subtitle="Post-produzione e montaggio" icon={Scissors} color="purple">
      <div className="space-y-3">
        {/* Not started: show notes form */}
        {!started && (
          <>
            <textarea value={notes} onChange={e => setNotes(e.target.value)}
              rows={3} placeholder="Note per il montaggio..."
              className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px] text-white placeholder-gray-600" />
            <button onClick={save} disabled={loading}
              className="w-full text-[9px] py-2 rounded-xl bg-purple-500/15 border border-purple-500/30 text-purple-400 disabled:opacity-30 font-bold">
              {loading ? '...' : 'Avvia Montaggio'}
            </button>
          </>
        )}

        {/* Timer active */}
        {started && (
          <>
            {/* Progress + countdown */}
            <div className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/15 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[8px] text-gray-500 uppercase font-bold">Montaggio ({fcHours}h totali)</span>
                <span className="text-[10px] font-black text-purple-400">{Math.floor(progress)}%</span>
              </div>
              <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-purple-600 to-pink-400 transition-all duration-1000 ease-out"
                  style={{ width: `${Math.min(100, progress)}%` }} />
              </div>
              <div className="flex items-center justify-center gap-2">
                <Clock className="w-3 h-3 text-purple-400" />
                <span className={`text-[10px] font-bold ${isComplete ? 'text-emerald-400' : 'text-purple-300'}`}>
                  {isComplete ? 'Montaggio completato!' : remainLabel + ' rimanenti'}
                </span>
              </div>
            </div>

            {/* Rotating message in italic */}
            {!isComplete && (
              <div className="px-3 py-2 rounded-lg bg-purple-500/3 border border-purple-500/10 min-h-[32px] flex items-center justify-center">
                <p className="text-[9px] text-purple-300/80 italic text-center transition-opacity duration-500" key={msgIdx}>
                  {FC_MESSAGES[msgIdx]}
                </p>
              </div>
            )}

            {/* Speedup buttons */}
            {!isComplete && (
              <>
                <p className="text-[8px] text-gray-500 uppercase font-bold">Velocizza (a pagamento)</p>
                <div className="grid grid-cols-2 gap-1.5">
                  {[25,50,75,100].map(p => {
                    const cost = getSpeedupCost(SPEEDUP_COSTS[p], progress);
                    const remH = Math.floor((remainingMs * (p / 100)) / 3600000);
                    const remM = Math.floor(((remainingMs * (p / 100)) % 3600000) / 60000);
                    const saved = remH > 0 ? `-${remH}h${remM}m` : `-${remM}m`;
                    return (
                      <button key={p} onClick={() => speedup(p)} disabled={loading}
                        className="flex flex-col items-center gap-0.5 px-2 py-2 rounded-lg bg-yellow-500/5 border border-yellow-500/15 text-yellow-400 text-[8px] font-bold disabled:opacity-30 hover:bg-yellow-500/10 transition-all">
                        <div className="flex items-center gap-1">
                          <Zap className="w-3 h-3" />
                          <span>{p}%</span>
                          <span className="flex items-center gap-0.5 text-[7px] text-cyan-400">
                            <Coins className="w-2.5 h-2.5" />{cost}
                          </span>
                        </div>
                        <span className="text-[6px] text-gray-500">{saved}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* Film Duration — shown after completion */}
            {isComplete && filmDuration && (
              <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-center space-y-1">
                <p className="text-[7px] text-gray-500 uppercase font-bold tracking-wider">Durata Effettiva del Film</p>
                <p className="text-2xl font-black text-emerald-400">{filmDuration.duration_label}</p>
                <p className="text-[8px] text-gray-500">({filmDuration.duration_minutes} minuti)</p>
              </div>
            )}

            {isComplete && (
              <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/15 text-center">
                <p className="text-[9px] text-emerald-400 font-bold">Montaggio completato! Premi Avanti per il prossimo step.</p>
              </div>
            )}
          </>
        )}
      </div>
    </PhaseWrapper>
  );
};

/* ═══════ SCARTA FILM DIALOG ═══════ */
export const DiscardFilmButton = ({ filmId, onDiscard }) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

  const doDiscard = async () => {
    setLoading(true);
    try {
      await v3api(`/films/${filmId}/discard`, 'POST');
      onDiscard?.();
    } catch (e) { /* handled by parent */ }
    setLoading(false);
  };

  return (
    <>
      <button onClick={() => setShowConfirm(true)}
        className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-red-500/5 border border-red-500/15 text-red-400/60 text-[8px] font-bold hover:bg-red-500/10 hover:text-red-400 transition-all mt-4"
        data-testid="discard-film-btn">
        <Trash2 className="w-3 h-3" /> Scarta Film
      </button>
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={() => setShowConfirm(false)}>
          <div className="bg-gray-900 border border-red-500/30 rounded-xl p-5 mx-6 max-w-sm w-full space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h4 className="text-sm font-bold text-white">Conferma Scarto</h4>
            </div>
            <p className="text-[10px] text-gray-400">Sei sicuro di voler scartare questo film? Il progetto verra inviato al mercato e non potrai piu modificarlo.</p>
            <div className="flex gap-2">
              <button onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 rounded-lg border border-gray-700 text-gray-400 text-[9px] font-bold">Annulla</button>
              <button onClick={doDiscard} disabled={loading}
                className="flex-1 py-2 rounded-lg bg-red-500/20 border border-red-500/40 text-red-400 text-[9px] font-bold disabled:opacity-50">
                {loading ? '...' : 'Conferma Scarto'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

/* ═══════ MARKETING ═══════ */
const MKT_PACKAGES = [
  { name: 'Teaser Digitale', cost: 20000, hype: 5 },
  { name: 'Campagna Social', cost: 40000, hype: 12 },
  { name: 'Stampa e TV', cost: 60000, hype: 18 },
  { name: 'Tour Cast', cost: 80000, hype: 25 },
  { name: 'Mega Globale', cost: 150000, hype: 40 },
];

export const MarketingPhase = ({ film, onRefresh, toast, onDirty }) => {
  const [proposals, setProposals] = useState([]);
  const [selectedSponsors, setSelectedSponsors] = useState(film.selected_sponsors?.map(s => s.sponsor_id) || []);
  const [sponsorsConfirmed, setSponsorsConfirmed] = useState(!!film.sponsors_confirmed);
  const [pkgs, setPkgs] = useState(film.marketing_packages || []);
  const [loading, setLoading] = useState(false);
  const done = film.marketing_completed;

  useEffect(() => {
    if (!sponsorsConfirmed) {
      v3api(`/films/${film.id}/sponsor-proposals`).then(d => setProposals(d.proposals || [])).catch(() => {});
    }
  }, [film.id, sponsorsConfirmed]);

  const toggleSponsor = (id) => {
    setSelectedSponsors(prev => {
      if (prev.includes(id)) return prev.filter(x => x !== id);
      if (prev.length >= 6) return prev;
      return [...prev, id];
    });
    onDirty?.();
  };

  const confirmSponsors = async () => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/save-sponsors`, 'POST', { sponsor_ids: selectedSponsors });
      await onRefresh();
      setSponsorsConfirmed(true);
      toast?.(`${selectedSponsors.length} sponsor confermati!`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const saveMarketing = async () => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/save-marketing`, 'POST', { packages: pkgs });
      await onRefresh(); toast?.('Marketing confermato!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const tierColors = { A: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20', B: 'text-blue-400 bg-blue-500/10 border-blue-500/20', C: 'text-gray-400 bg-gray-500/10 border-gray-500/20' };
  const tierLabels = { A: 'Premium', B: 'Standard', C: 'Emergente' };

  return (
    <PhaseWrapper title="Sponsor & Marketing" subtitle="Trova sponsor e promuovi il film" icon={Megaphone} color="green">
      <div className="space-y-3">

        {/* ═══ STEP 1: SPONSORS ═══ */}
        {!sponsorsConfirmed ? (
          <>
            <div className="flex items-center gap-2 mb-1">
              <Handshake className="w-3.5 h-3.5 text-green-400" />
              <p className="text-[8px] text-gray-500 uppercase font-bold">Sponsor disponibili ({proposals.length})</p>
              <span className="text-[7px] text-cyan-400 font-bold ml-auto">{selectedSponsors.length}/6</span>
            </div>

            {proposals.length === 0 && (
              <p className="text-[9px] text-gray-600 text-center py-2">Nessuno sponsor interessato al momento</p>
            )}

            <div className="space-y-1.5 max-h-72 overflow-y-auto">
              {proposals.map(s => {
                const sel = selectedSponsors.includes(s.sponsor_id);
                return (
                  <button key={s.sponsor_id} onClick={() => toggleSponsor(s.sponsor_id)}
                    className={`w-full flex items-center gap-2 p-2.5 rounded-lg border text-left transition-all ${
                      sel ? 'bg-green-500/10 border-green-500/40' : 'bg-gray-800/30 border-gray-700'
                    }`}>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className={`text-[9px] font-bold ${sel ? 'text-green-400' : 'text-white'}`}>{s.sponsor_name}</span>
                        <span className={`text-[6px] px-1 py-0.5 rounded border font-bold ${tierColors[s.tier] || tierColors.C}`}>{tierLabels[s.tier] || s.tier}</span>
                        {s.genre_match && <span className="text-[6px] px-1 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">Match</span>}
                      </div>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span className="text-[7px] text-yellow-400">${(s.offer_amount || 0).toLocaleString()}</span>
                        <span className="text-[7px] text-orange-400">{s.daily_share_pct}% giornaliero</span>
                      </div>
                    </div>
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 ${
                      sel ? 'border-green-400 bg-green-500/20' : 'border-gray-700'
                    }`}>
                      {sel && <Check className="w-3 h-3 text-green-400" />}
                    </div>
                  </button>
                );
              })}
            </div>

            <button onClick={confirmSponsors} disabled={loading}
              className="w-full text-[9px] py-2 rounded-xl bg-green-500/15 border border-green-500/30 text-green-400 disabled:opacity-30 font-bold">
              {loading ? '...' : selectedSponsors.length > 0 ? `Conferma ${selectedSponsors.length} Sponsor` : 'Prosegui senza Sponsor'}
            </button>
          </>
        ) : (
          <div className="p-2 rounded-lg bg-green-500/5 border border-green-500/15 flex items-center gap-2">
            <Handshake className="w-3.5 h-3.5 text-green-400" />
            <p className="text-[9px] text-green-400 font-bold">
              {(film.selected_sponsors || []).length > 0
                ? `${(film.selected_sponsors || []).length} sponsor confermati — $${(film.sponsors_total_offer || 0).toLocaleString()} al rilascio`
                : 'Nessuno sponsor selezionato'}
            </p>
          </div>
        )}

        {/* ═══ STEP 2: MARKETING (after sponsors confirmed) ═══ */}
        {sponsorsConfirmed && (
          <>
            {!done && (
              <>
                <p className="text-[8px] text-gray-500 uppercase font-bold">Pacchetti Marketing</p>
                {MKT_PACKAGES.map(pkg => {
                  const sel = pkgs.includes(pkg.name);
                  return (
                    <button key={pkg.name} onClick={() => { setPkgs(v => sel ? v.filter(x => x !== pkg.name) : [...v, pkg.name]); onDirty?.(); }}
                      className={`w-full flex items-center gap-2 p-2.5 rounded-lg border text-left transition-all ${
                        sel ? 'bg-green-500/10 border-green-500/40' : 'bg-gray-800/30 border-gray-700'
                      }`}>
                      <Megaphone className={`w-3.5 h-3.5 shrink-0 ${sel ? 'text-green-400' : 'text-gray-600'}`} />
                      <div className="flex-1">
                        <p className={`text-[9px] font-bold ${sel ? 'text-green-400' : 'text-gray-300'}`}>{pkg.name}</p>
                        <p className="text-[7px] text-gray-500">${pkg.cost.toLocaleString()} | +{pkg.hype} hype</p>
                      </div>
                    </button>
                  );
                })}
              </>
            )}
            {done && (
              <div className="p-2 rounded-lg bg-green-500/5 border border-green-500/15 flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                <p className="text-[9px] text-green-400 font-bold">Marketing confermato</p>
              </div>
            )}
            {!done && (
              <button onClick={saveMarketing} disabled={loading} className="w-full text-[9px] py-2 rounded-xl bg-green-500/15 border border-green-500/30 text-green-400 disabled:opacity-30 font-bold">
                {loading ? '...' : 'Conferma Marketing'}
              </button>
            )}
          </>
        )}
      </div>
    </PhaseWrapper>
  );
};

/* ═══════ LA PRIMA ═══════ */
export const LaPrimaPhase = ({ film, onRefresh, toast, onDirty, onTriggerAnimation }) => {
  const [loading, setLoading] = useState(false);
  const releaseTypeSet = film.release_type === 'premiere' || film.release_type === 'direct';
  const isPremiere = film.release_type === 'premiere';
  const premiere = film.premiere || {};
  const isConfigured = !!premiere.city && !!premiere.datetime;

  // Wizard state for configuring premiere
  const [citiesByRegion, setCitiesByRegion] = useState({});
  const [selectedCity, setSelectedCity] = useState('');
  const [datetime, setDatetime] = useState('');
  const [delayDays, setDelayDays] = useState(3);
  const [wizardStep, setWizardStep] = useState(1); // 1=city, 2=datetime, 3=delay, 4=confirm

  // Countdown ticker
  const [nowTick, setNowTick] = useState(Date.now());
  useEffect(() => { if (!isConfigured) return; const i = setInterval(() => setNowTick(Date.now()), 30000); return () => clearInterval(i); }, [isConfigured]);

  // Trigger WOW animation on first transition waiting → live
  const prevWindowState = useRef(null);

  const chooseReleaseType = async (type) => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/set-release-type`, 'POST', { release_type: type });
      await onRefresh();
      onDirty?.();
      toast?.(type === 'premiere' ? 'La Prima selezionata!' : 'Rilascio Diretto selezionato');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  // Helper: call non-pipeline-v3 endpoints (la-prima router)
  const apiCall = async (path, method = 'GET', body) => {
    const API = process.env.REACT_APP_BACKEND_URL;
    const token = localStorage.getItem('cineworld_token');
    const res = await fetch(`${API}/api${path}`, {
      method, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || data.error || 'Errore API');
    return data;
  };

  useEffect(() => {
    if (isPremiere && !isConfigured && wizardStep === 1) {
      apiCall('/la-prima/cities').then(d => setCitiesByRegion(d.by_region || {})).catch(() => {});
    }
  }, [isPremiere, isConfigured, wizardStep]);

  // Datetime boundaries: from tomorrow 00:00 to +3 days 23:59 (local)
  const dtMin = (() => { const d = new Date(); d.setDate(d.getDate() + 1); d.setHours(0, 0, 0, 0); return d.toISOString().slice(0, 16); })();
  const dtMax = (() => { const d = new Date(); d.setDate(d.getDate() + 3); d.setHours(23, 59, 0, 0); return d.toISOString().slice(0, 16); })();

  const confirmSetup = async () => {
    if (!selectedCity || !datetime) { toast?.('Seleziona citta e data', 'error'); return; }
    setLoading(true);
    try {
      const iso = new Date(datetime).toISOString();
      await apiCall(`/la-prima/setup/${film.id}`, 'POST', {
        city: selectedCity, datetime: iso, release_delay_days: delayDays,
      });
      await onRefresh();
      onDirty?.();
      toast?.(`La Prima confermata a ${selectedCity}!`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  // Format countdown to event / end of event
  const computeWindow = () => {
    if (!premiere.datetime) return null;
    const pdt = new Date(premiere.datetime).getTime();
    const end = pdt + 24 * 3600 * 1000;
    const now = nowTick;
    if (now < pdt) {
      const delta = pdt - now;
      return { state: 'waiting', delta };
    }
    if (now < end) {
      const delta = end - now;
      return { state: 'live', delta };
    }
    return { state: 'done', delta: 0 };
  };
  const window = computeWindow();
  useEffect(() => {
    if (!window) return;
    if (prevWindowState.current === 'waiting' && window.state === 'live') {
      // Transition to LIVE! Trigger super animation.
      onTriggerAnimation?.();
    }
    prevWindowState.current = window.state;
  }, [window, onTriggerAnimation]);
  const fmtDelta = (ms) => {
    const h = Math.floor(ms / 3600000);
    const m = Math.floor((ms % 3600000) / 60000);
    if (h >= 24) return `${Math.floor(h / 24)}g ${h % 24}h`;
    return `${h}h ${m}m`;
  };

  return (
    <PhaseWrapper title="La Prima" subtitle="L'evento esclusivo di anteprima" icon={Award} color="yellow">
      <div className="space-y-3">
        {!releaseTypeSet ? (
          <div className="space-y-2">
            <p className="text-[8px] text-gray-500 uppercase font-bold text-center">Come vuoi rilasciare il film?</p>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => chooseReleaseType('premiere')} disabled={loading}
                data-testid="choose-la-prima-btn"
                className="p-3 rounded-xl border text-center bg-yellow-500/10 border-yellow-500/30 hover:bg-yellow-500/20 active:scale-95 transition-all disabled:opacity-50">
                <Award className="w-5 h-5 mx-auto mb-1 text-yellow-400" />
                <p className="text-[9px] font-bold text-yellow-400">La Prima</p>
                <p className="text-[7px] text-gray-500 mt-0.5">Evento esclusivo</p>
              </button>
              <button onClick={() => chooseReleaseType('direct')} disabled={loading}
                data-testid="choose-direct-btn"
                className="p-3 rounded-xl border text-center bg-emerald-500/10 border-emerald-500/30 hover:bg-emerald-500/20 active:scale-95 transition-all disabled:opacity-50">
                <Ticket className="w-5 h-5 mx-auto mb-1 text-emerald-400" />
                <p className="text-[9px] font-bold text-emerald-400">Diretto</p>
                <p className="text-[7px] text-gray-500 mt-0.5">Salta La Prima</p>
              </button>
            </div>
            <p className="text-[7px] text-gray-600 text-center mt-1">La scelta non potra' essere modificata</p>
          </div>
        ) : isPremiere && !isConfigured ? (
          <div className="space-y-3" data-testid="la-prima-wizard">
            {/* Stepper indicator */}
            <div className="flex items-center justify-center gap-2">
              {[1,2,3].map(n => (
                <div key={n} className={`w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold ${wizardStep >= n ? 'bg-yellow-500 text-black' : 'bg-gray-800 text-gray-600'}`}>{n}</div>
              ))}
            </div>

            {/* STEP 1: City */}
            {wizardStep === 1 && (
              <>
                <p className="text-[8px] text-gray-500 uppercase font-bold text-center">1. Scegli la citta'</p>
                <div className="max-h-[360px] overflow-y-auto pr-1 space-y-2" data-testid="city-picker">
                  {Object.entries(citiesByRegion).map(([region, cities]) => (
                    <div key={region}>
                      <p className="text-[7px] text-yellow-500/70 uppercase tracking-wider font-bold mb-1">{region}</p>
                      <div className="grid grid-cols-2 gap-1.5">
                        {cities.map(c => (
                          <button key={c.name}
                            onClick={() => setSelectedCity(c.name)}
                            data-testid={`city-btn-${c.name}`}
                            className={`p-2 rounded-lg border text-left transition-all ${
                              selectedCity === c.name ? 'bg-yellow-500/15 border-yellow-500/50' : 'bg-gray-800/30 border-gray-700 hover:border-yellow-500/20'
                            }`}>
                            <p className={`text-[9px] font-bold ${selectedCity === c.name ? 'text-yellow-400' : 'text-white'}`}>{c.name}</p>
                            <p className="text-[7px] text-gray-500 italic">{c.vibe}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <button onClick={() => setWizardStep(2)} disabled={!selectedCity}
                  className="w-full py-2 rounded-xl bg-yellow-500/15 border border-yellow-500/30 text-yellow-400 text-[9px] font-bold disabled:opacity-30"
                  data-testid="wizard-next-city">
                  Avanti ({selectedCity || '—'})
                </button>
              </>
            )}

            {/* STEP 2: Datetime */}
            {wizardStep === 2 && (
              <>
                <p className="text-[8px] text-gray-500 uppercase font-bold text-center">2. Quando avverra' La Prima?</p>
                <div className="p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/15 space-y-2">
                  <input type="datetime-local"
                    value={datetime}
                    min={dtMin} max={dtMax}
                    onChange={e => setDatetime(e.target.value)}
                    data-testid="datetime-picker"
                    className="w-full bg-black/40 border border-yellow-500/20 rounded-lg px-2 py-2 text-[11px] text-yellow-300 [color-scheme:dark]" />
                  <p className="text-[7px] text-gray-500 text-center leading-tight">
                    Minimo: domani ore 00:00 · Massimo: tra 3 giorni<br/>
                    Orario consigliato: 19:00-21:00 locali ({selectedCity})
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => setWizardStep(1)}
                    className="py-2 rounded-xl bg-gray-800/30 border border-gray-700 text-gray-400 text-[9px] font-bold">
                    Indietro
                  </button>
                  <button onClick={() => setWizardStep(3)} disabled={!datetime}
                    className="py-2 rounded-xl bg-yellow-500/15 border border-yellow-500/30 text-yellow-400 text-[9px] font-bold disabled:opacity-30"
                    data-testid="wizard-next-datetime">
                    Avanti
                  </button>
                </div>
              </>
            )}

            {/* STEP 3: Delay days */}
            {wizardStep === 3 && (
              <>
                <p className="text-[8px] text-gray-500 uppercase font-bold text-center">3. Uscita al cinema dopo la La Prima</p>
                <div className="p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/15 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-gray-400">Giorni dopo La Prima</span>
                    <span className="text-2xl font-black text-yellow-400">{delayDays}</span>
                  </div>
                  <input type="range" min="1" max="6" step="1" value={delayDays}
                    onChange={e => setDelayDays(parseInt(e.target.value))}
                    data-testid="delay-slider"
                    className="w-full accent-yellow-400" />
                  <div className="flex justify-between text-[7px] text-gray-500">
                    {[1,2,3,4,5,6].map(n => <span key={n} className={n === delayDays ? 'text-yellow-400 font-bold' : ''}>{n}g</span>)}
                  </div>
                  <p className="text-[7px] text-center text-gray-500 italic">
                    {delayDays === 3 ? 'Ideale: massimo buzz' : delayDays < 3 ? 'Troppo veloce, meno tempo per il passaparola' : 'Hype rischia di raffreddarsi'}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => setWizardStep(2)}
                    className="py-2 rounded-xl bg-gray-800/30 border border-gray-700 text-gray-400 text-[9px] font-bold">
                    Indietro
                  </button>
                  <button onClick={confirmSetup} disabled={loading}
                    className="py-2 rounded-xl bg-yellow-500 text-black text-[9px] font-black disabled:opacity-50"
                    data-testid="confirm-setup-btn">
                    {loading ? '...' : 'Conferma La Prima'}
                  </button>
                </div>
                <p className="text-[7px] text-gray-600 text-center">Citta: <span className="text-yellow-400">{selectedCity}</span> · Data: <span className="text-yellow-400">{datetime ? new Date(datetime).toLocaleString('it-IT', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}</span></p>
              </>
            )}
          </div>
        ) : isPremiere && isConfigured ? (
          <div className="space-y-3" data-testid="la-prima-configured">
            <div className="p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/30 space-y-2">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-yellow-400" />
                <span className="text-[10px] font-bold text-yellow-400 uppercase tracking-wider">La Prima configurata</span>
              </div>
              <p className="text-[9px] text-gray-300">Citta: <span className="font-bold text-yellow-300">{premiere.city}</span></p>
              <p className="text-[9px] text-gray-300">Data: <span className="font-bold text-yellow-300">{new Date(premiere.datetime).toLocaleString('it-IT', { day: '2-digit', month: 'long', hour: '2-digit', minute: '2-digit' })}</span></p>
              <p className="text-[9px] text-gray-300">Cinema dopo: <span className="font-bold text-yellow-300">{premiere.release_delay_days}g dalla Prima</span></p>
            </div>
            {window && window.state === 'waiting' && (
              <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-center">
                <p className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider mb-1">In attesa</p>
                <p className="text-2xl font-black text-cyan-300">{fmtDelta(window.delta)}</p>
                <p className="text-[8px] text-gray-500 mt-1">L'hype cresce. Il film resta in Prossimamente.</p>
              </div>
            )}
            {window && window.state === 'live' && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/40 text-center animate-pulse">
                <p className="text-[10px] text-red-400 font-bold uppercase tracking-wider mb-1">LIVE ORA</p>
                <p className="text-2xl font-black text-red-300">{fmtDelta(window.delta)}</p>
                <p className="text-[8px] text-gray-500 mt-1">Fine evento. Poi sblocca distribuzione.</p>
              </div>
            )}
            {window && window.state === 'done' && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center">
                <p className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider mb-1">La Prima conclusa</p>
                <p className="text-[9px] text-gray-400">Premi Avanti per procedere alla distribuzione.</p>
              </div>
            )}
          </div>
        ) : (
          <div className="p-3 rounded-xl bg-gray-800/20 border border-gray-700/30 text-center">
            <p className="text-[10px] text-gray-400">Nessuna premiere selezionata (rilascio diretto)</p>
            <p className="text-[8px] text-gray-500 mt-1">Premi Avanti per continuare alla distribuzione</p>
          </div>
        )}
      </div>
    </PhaseWrapper>
  );
};

/* ═══════ DISTRIBUTION ═══════ */
import { ChevronDown, ChevronRight, MapPin } from 'lucide-react';

const DATES = ['Immediato','6 ore','12 ore','24 ore','2 giorni','3 giorni'];

const ZoneTree = ({ zones, mondiale, setMondiale, selConts, setSelConts, selNations, setSelNations, selCities, setSelCities }) => {
  const [expanded, setExpanded] = useState({});
  const [expandedNations, setExpandedNations] = useState({});

  const toggleExpand = (id) => setExpanded(p => ({ ...p, [id]: !p[id] }));
  const toggleExpandNation = (id) => setExpandedNations(p => ({ ...p, [id]: !p[id] }));

  const toggleContinent = (cid) => {
    if (mondiale) return;
    setSelConts(p => p.includes(cid) ? p.filter(x => x !== cid) : [...p, cid]);
  };

  const toggleNation = (cid, nid) => {
    if (mondiale || selConts.includes(cid)) return;
    setSelNations(p => {
      const curr = p[cid] || [];
      const next = curr.includes(nid) ? curr.filter(x => x !== nid) : [...curr, nid];
      return { ...p, [cid]: next };
    });
  };

  const toggleCity = (cid, nid, city) => {
    if (mondiale || selConts.includes(cid) || (selNations[cid] || []).includes(nid)) return;
    setSelCities(p => {
      const contMap = p[cid] || {};
      const curr = contMap[nid] || [];
      const next = curr.includes(city) ? curr.filter(x => x !== city) : [...curr, city];
      return { ...p, [cid]: { ...contMap, [nid]: next } };
    });
  };

  const toggleAllCities = (cid, nid, allCities) => {
    if (mondiale || selConts.includes(cid) || (selNations[cid] || []).includes(nid)) return;
    setSelCities(p => {
      const contMap = p[cid] || {};
      const curr = contMap[nid] || [];
      const allSelected = allCities.every(c => curr.includes(c));
      return { ...p, [cid]: { ...contMap, [nid]: allSelected ? [] : [...allCities] } };
    });
  };

  return (
    <div className="space-y-1.5">
      {/* Mondiale */}
      <button onClick={() => setMondiale(!mondiale)}
        className={`w-full flex items-center justify-between p-2.5 rounded-lg border transition-all ${
          mondiale ? 'bg-blue-500/10 border-blue-500/40' : 'border-gray-800 hover:border-gray-600'
        }`}>
        <div className="flex items-center gap-2">
          <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${mondiale ? 'border-blue-400 bg-blue-500/20' : 'border-gray-700'}`}>
            {mondiale && <Check className="w-2.5 h-2.5 text-blue-400" />}
          </div>
          <span className={`text-[9px] font-bold ${mondiale ? 'text-blue-400' : 'text-white'}`}>Mondiale</span>
          <span className="text-[7px] text-gray-500">Tutti i continenti</span>
        </div>
        <span className="text-[7px] text-yellow-400 font-bold">$200K 20CP</span>
      </button>

      {!mondiale && (
        <p className="text-[7px] text-gray-600 text-center">— oppure seleziona zone —</p>
      )}

      {/* Continents */}
      {Object.entries(zones).map(([cid, cont]) => {
        const isFullCont = mondiale || selConts.includes(cid);
        const isExpanded = expanded[cid];
        const nationCount = Object.keys(cont.nations || {}).length;
        const selNationCount = (selNations[cid] || []).length;
        const selCityCount = Object.values(selCities[cid] || {}).reduce((s, arr) => s + arr.length, 0);

        return (
          <div key={cid} className={`rounded-lg border overflow-hidden ${isFullCont ? 'border-blue-500/30 bg-blue-500/5' : 'border-gray-800'}`}>
            <div className="flex items-center">
              <button onClick={() => toggleContinent(cid)} disabled={mondiale}
                className="flex items-center gap-2 flex-1 p-2 text-left disabled:opacity-60">
                <div className={`w-3.5 h-3.5 rounded border-2 flex items-center justify-center shrink-0 ${isFullCont ? 'border-blue-400 bg-blue-500/20' : 'border-gray-700'}`}>
                  {isFullCont && <Check className="w-2 h-2 text-blue-400" />}
                </div>
                <span className={`text-[9px] font-bold ${isFullCont ? 'text-blue-400' : 'text-white'}`}>{cont.label}</span>
                {(selNationCount > 0 || selCityCount > 0) && !isFullCont && (
                  <span className="text-[6px] text-cyan-400">{selNationCount > 0 ? `${selNationCount}N` : ''}{selCityCount > 0 ? ` ${selCityCount}C` : ''}</span>
                )}
              </button>
              <button onClick={() => toggleExpand(cid)} className="p-2 text-gray-500">
                {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>
            </div>

            {/* Nations */}
            {isExpanded && (
              <div className="border-t border-gray-800/50 pl-4 py-1 space-y-0.5">
                {Object.entries(cont.nations || {}).map(([nid, nat]) => {
                  const isFullNation = isFullCont || (selNations[cid] || []).includes(nid);
                  const isNatExpanded = expandedNations[`${cid}/${nid}`];
                  const cities = nat.cities || [];
                  const selCitiesHere = (selCities[cid] || {})[nid] || [];

                  return (
                    <div key={nid}>
                      <div className="flex items-center">
                        <button onClick={() => toggleNation(cid, nid)} disabled={mondiale || isFullCont}
                          className="flex items-center gap-1.5 flex-1 py-1 text-left disabled:opacity-50">
                          <div className={`w-3 h-3 rounded border flex items-center justify-center shrink-0 ${isFullNation ? 'border-cyan-400 bg-cyan-500/20' : 'border-gray-700'}`}>
                            {isFullNation && <Check className="w-2 h-2 text-cyan-400" />}
                          </div>
                          <span className={`text-[8px] font-medium ${isFullNation ? 'text-cyan-400' : 'text-gray-300'}`}>{nat.label}</span>
                          {selCitiesHere.length > 0 && !isFullNation && (
                            <span className="text-[6px] text-emerald-400">{selCitiesHere.length}/{cities.length}</span>
                          )}
                        </button>
                        <button onClick={() => toggleExpandNation(`${cid}/${nid}`)} className="p-1 text-gray-600">
                          {isNatExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        </button>
                      </div>

                      {/* Cities */}
                      {isNatExpanded && (
                        <div className="pl-4 py-1 space-y-0.5">
                          <button onClick={() => toggleAllCities(cid, nid, cities)} disabled={mondiale || isFullCont || isFullNation}
                            className="text-[7px] text-blue-400 underline mb-1 disabled:opacity-30">
                            {cities.every(c => selCitiesHere.includes(c)) ? 'Deseleziona tutte' : 'Seleziona tutte'}
                          </button>
                          <div className="flex flex-wrap gap-1">
                            {cities.map(city => {
                              const sel = isFullNation || isFullCont || mondiale || selCitiesHere.includes(city);
                              return (
                                <button key={city} onClick={() => toggleCity(cid, nid, city)}
                                  disabled={mondiale || isFullCont || isFullNation}
                                  className={`px-1.5 py-0.5 rounded text-[7px] font-medium border transition-all disabled:opacity-50 ${
                                    sel ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'border-gray-800 text-gray-500 hover:border-gray-600'
                                  }`}>
                                  {city}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export const DistributionPhase = ({ film, onRefresh, toast, onDirty }) => {
  const [zones, setZones] = useState({});
  const [loading, setLoading] = useState(false);
  const isPremiere = film.release_type === 'premiere';
  // If premiere: force a non-immediato default (24h), block "Immediato"
  const defaultDate = film.distribution_release_delay || (isPremiere ? '24_ore' : 'immediato');
  const [date, setDate] = useState(defaultDate);
  const [theaterDays, setTheaterDays] = useState(film.distribution_theater_days || 21);
  const [mondiale, setMondiale] = useState(!!film.distribution_mondiale);
  const [selConts, setSelConts] = useState(film.distribution_continents || []);
  const [selNations, setSelNations] = useState(film.distribution_nations || {});
  const [selCities, setSelCities] = useState(film.distribution_cities || {});
  const [costPreview, setCostPreview] = useState(null);
  const done = !!film.distribution_confirmed;

  useEffect(() => { v3api(`/films/${film.id}/distribution-zones`).then(d => setZones(d.zones || {})).catch(() => {}); }, [film.id]);

  // Live cost preview
  useEffect(() => {
    const hasSelections = mondiale || selConts.length > 0 || Object.values(selNations).some(a => a.length > 0) || Object.values(selCities).some(o => Object.values(o).some(a => a.length > 0));
    if (!hasSelections) { setCostPreview(null); return; }
    const body = { mondiale, continents: selConts, nations: selNations, cities: selCities, release_delay: date, theater_days: theaterDays };
    v3api(`/films/${film.id}/calc-distribution-cost`, 'POST', body).then(setCostPreview).catch(() => {});
  }, [mondiale, selConts, selNations, selCities, film.id, date, theaterDays]);

  const save = async () => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/save-distribution`, 'POST', { mondiale, continents: selConts, nations: selNations, cities: selCities, release_delay: date, theater_days: theaterDays });
      await onRefresh(); toast?.('Distribuzione confermata!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Distribuzione" subtitle="Zone e data di uscita" icon={Globe} color="blue">
      <div className="space-y-3">
        {done ? (
          <div className="p-2 rounded-lg bg-blue-500/5 border border-blue-500/15 flex items-center gap-2">
            <Check className="w-4 h-4 text-blue-400" />
            <p className="text-[9px] text-blue-400 font-bold">Distribuzione confermata</p>
          </div>
        ) : (
          <>
            <p className="text-[8px] text-gray-500 uppercase font-bold">Data uscita{isPremiere ? ' (post La Prima)' : ''}</p>
            {isPremiere && (
              <p className="text-[7px] text-yellow-500/70 text-center -mt-1">Il rilascio Immediato non e' disponibile con La Prima</p>
            )}
            <div className="grid grid-cols-3 gap-1.5">
              {DATES.map(label => {
                const val = label.toLowerCase().replace(/ /g, '_');
                const isImmediato = val === 'immediato';
                const blocked = isPremiere && isImmediato;
                return (
                  <button key={label} onClick={() => { if (blocked) return; setDate(val); onDirty?.(); }}
                    disabled={blocked}
                    className={`py-2 rounded-lg text-[8px] font-bold border transition-all ${
                      blocked ? 'border-gray-900 bg-gray-900/50 text-gray-700 line-through cursor-not-allowed' :
                      date === val ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' : 'border-gray-800 text-gray-400 hover:border-gray-600'
                    }`}>{label}</button>
                );
              })}
            </div>

            <p className="text-[8px] text-gray-500 uppercase font-bold">Zone di distribuzione</p>
            <ZoneTree zones={zones} mondiale={mondiale} setMondiale={(v) => { setMondiale(v); onDirty?.(); }}
              selConts={selConts} setSelConts={(v) => { setSelConts(v); onDirty?.(); }}
              selNations={selNations} setSelNations={(v) => { setSelNations(v); onDirty?.(); }}
              selCities={selCities} setSelCities={(v) => { setSelCities(v); onDirty?.(); }} />

            {/* Velion Intelligence */}
            <div className="p-3 rounded-xl bg-teal-500/5 border border-teal-500/15 space-y-1.5">
              <p className="text-[8px] text-teal-400 font-bold">Velion — Intelligence Distribuzione</p>
              <p className="text-[7px] text-gray-400 italic">
                Per il tuo film '{film.title}', considera che: le zone con maggiore affinita al genere '{film.genre}' porteranno incassi migliori.
                Singole citta strategiche possono avere piu valore di interi continenti se scelte bene.
              </p>
            </div>

            {/* Theater days */}
            <div>
              <div className="flex justify-between text-[8px] mb-1">
                <span className="text-gray-500">Durata programmazione in sala</span>
                <span className="text-blue-400 font-bold">{theaterDays} giorni</span>
              </div>
              <input type="range" min={7} max={60} value={theaterDays} onChange={e => { setTheaterDays(+e.target.value); onDirty?.(); }}
                className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500" />
            </div>

            {/* Cost preview */}
            {costPreview && (
              <div className="p-2.5 rounded-xl bg-yellow-500/5 border border-yellow-500/20 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[8px] text-gray-400">Costo distribuzione</span>
                  <span className="text-[10px] font-bold text-yellow-400">
                    ${(costPreview.total_funds || 0).toLocaleString()} + {costPreview.total_cp || 0} CP
                  </span>
                </div>
                {(costPreview.breakdown || []).map((b, i) => (
                  <div key={i} className="flex items-center justify-between text-[7px]">
                    <span className="text-gray-500 truncate flex-1">{b.label}</span>
                    <span className="text-gray-400 ml-2 shrink-0">${(b.funds || 0).toLocaleString()} {b.cp}CP</span>
                  </div>
                ))}
              </div>
            )}

            <button onClick={save} disabled={loading || (!mondiale && selConts.length === 0 && Object.values(selNations).every(a => a.length === 0) && Object.values(selCities).every(o => Object.values(o).every(a => a.length === 0)))}
              className="w-full text-[9px] py-2 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-400 disabled:opacity-30 font-bold">
              {loading ? '...' : 'Conferma Distribuzione'}
            </button>
          </>
        )}
      </div>
    </PhaseWrapper>
  );
};

/* ═══════ STEP FINALE ═══════ */
export const StepFinale = ({ film, onConfirm, onDiscard, loading, releaseType }) => {
  const [cost, setCost] = useState(null);
  const [savingsOptions, setSavingsOptions] = useState([]);
  const [showReview, setShowReview] = useState(false);
  const [velionResult, setVelionResult] = useState(null);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    v3api(`/films/${film.id}/production-cost`).then(setCost).catch(() => {});
    v3api(`/films/${film.id}/savings-options`).then(d => setSavingsOptions(d.options || [])).catch(() => {});
  }, [film.id]);

  const refreshCost = async () => {
    const c = await v3api(`/films/${film.id}/production-cost`);
    setCost(c);
    const s = await v3api(`/films/${film.id}/savings-options`);
    setSavingsOptions(s.options || []);
  };

  const applySaving = async (savingId) => {
    setApplying(true);
    try {
      await v3api(`/films/${film.id}/apply-saving-option`, 'POST', { saving_id: savingId });
      await refreshCost();
    } catch (e) { /* */ }
    setApplying(false);
  };

  const velionOptimize = async () => {
    setApplying(true);
    try {
      const res = await v3api(`/films/${film.id}/velion-optimize`, 'POST');
      setVelionResult(res.velion_savings);
      await refreshCost();
    } catch (e) { /* */ }
    setApplying(false);
  };

  const totalFunds = cost?.total_funds || 0;
  const totalCp = cost?.total_cp || 0;

  // Compute La Prima 24h blocker
  const premiere = film.premiere || {};
  const [nowTick, setNowTick] = useState(Date.now());
  useEffect(() => {
    if (releaseType !== 'premiere' || !premiere.datetime) return;
    const i = setInterval(() => setNowTick(Date.now()), 30000);
    return () => clearInterval(i);
  }, [releaseType, premiere.datetime]);
  const laPrimaBlock = (() => {
    if (releaseType !== 'premiere' || !premiere.datetime) return null;
    try {
      const pdt = new Date(premiere.datetime).getTime();
      const end = pdt + 24 * 3600 * 1000;
      if (nowTick < pdt) return { state: 'waiting', delta: pdt - nowTick };
      if (nowTick < end) return { state: 'live', delta: end - nowTick };
      return null;
    } catch { return null; }
  })();
  const fmtDelta = (ms) => {
    const h = Math.floor(ms / 3600000);
    const m = Math.floor((ms % 3600000) / 60000);
    return h >= 24 ? `${Math.floor(h / 24)}g ${h % 24}h ${m}m` : `${h}h ${m}m`;
  };
  const releaseBlocked = !!laPrimaBlock;

  return (
    <PhaseWrapper title="STEP FINALE" subtitle="Riepilogo e conferma uscita" icon={Ticket} color="emerald">
      <div className="space-y-3">
        {/* Poster */}
        <div className="flex justify-center">
          {film.poster_url ? <img src={film.poster_url} alt="" className="w-24 h-36 rounded-lg border border-gray-700 object-cover shadow-lg" /> :
            <div className="w-24 h-36 rounded-lg border border-gray-700 bg-gray-800/50 flex items-center justify-center"><Film className="w-6 h-6 text-gray-600" /></div>}
        </div>
        <div className="p-3 rounded-xl bg-gray-800/30 border border-gray-700/50 text-center space-y-1">
          <p className="text-lg font-black text-white">{film.title}</p>
          <p className="text-[9px] text-gray-400">{releaseType === 'premiere' ? 'La Prima' : 'Rilascio Diretto'}</p>
          {film.film_duration_label && <p className="text-[8px] text-emerald-400">{film.film_duration_label}</p>}
        </div>

        {/* Cost Breakdown */}
        {cost && (
          <div className="p-3 rounded-xl bg-gray-800/20 border border-gray-700/40 space-y-1.5">
            <p className="text-[8px] text-gray-500 uppercase font-bold">Riepilogo Costi Produzione</p>
            {(cost.breakdown || []).map((b, i) => (
              <div key={i} className={`flex items-center justify-between text-[8px] ${b.funds < 0 ? 'text-emerald-400' : 'text-gray-300'}`}>
                <span className="truncate flex-1">{b.label}</span>
                <span className="font-bold ml-2 shrink-0">
                  {b.funds < 0 ? `-$${Math.abs(b.funds).toLocaleString()}` : `$${b.funds.toLocaleString()}`}
                </span>
              </div>
            ))}
            <div className="border-t border-gray-700 pt-1.5 mt-1.5 flex items-center justify-between">
              <span className="text-[9px] font-bold text-white">TOTALE</span>
              <span className="text-[10px] font-black text-yellow-400">${totalFunds.toLocaleString()} + {totalCp} CP</span>
            </div>
          </div>
        )}

        {/* Review options */}
        {!showReview ? (
          <button onClick={() => setShowReview(true)}
            className="w-full text-[8px] py-2 rounded-lg bg-blue-500/5 border border-blue-500/15 text-blue-400 font-bold hover:bg-blue-500/10 transition-all">
            Vuoi rivedere qualcosa?
          </button>
        ) : (
          <div className="p-3 rounded-xl bg-blue-500/5 border border-blue-500/20 space-y-2">
            <p className="text-[8px] text-blue-400 uppercase font-bold">Opzioni Risparmio</p>
            {savingsOptions.length === 0 && <p className="text-[8px] text-gray-500">Nessuna opzione disponibile</p>}
            {savingsOptions.map(opt => (
              <button key={opt.id} onClick={() => applySaving(opt.id)} disabled={applying}
                className="w-full flex items-center justify-between p-2 rounded-lg bg-gray-800/30 border border-gray-700 hover:border-blue-500/30 transition-all text-left disabled:opacity-50">
                <div>
                  <p className="text-[8px] font-bold text-gray-300">{opt.label}</p>
                  <p className="text-[7px] text-gray-500">{opt.description}</p>
                </div>
                <span className="text-[8px] text-emerald-400 font-bold shrink-0 ml-2">
                  -${opt.savings_funds.toLocaleString()}{opt.savings_cp > 0 ? ` -${opt.savings_cp}CP` : ''}
                </span>
              </button>
            ))}
            {/* Velion auto */}
            <button onClick={velionOptimize} disabled={applying}
              className="w-full flex items-center justify-between p-2.5 rounded-lg bg-teal-500/5 border border-teal-500/20 hover:bg-teal-500/10 transition-all disabled:opacity-50">
              <div>
                <p className="text-[8px] font-bold text-teal-400">Ci pensa Velion</p>
                <p className="text-[7px] text-gray-500">Auto-ottimizzazione intelligente</p>
              </div>
              {velionResult ? (
                <span className="text-[8px] text-emerald-400 font-bold">-{velionResult.savings_pct}%</span>
              ) : (
                <span className="text-[8px] text-teal-400 font-bold">8-15%</span>
              )}
            </button>
            <button onClick={() => setShowReview(false)} className="text-[7px] text-gray-500 underline w-full text-center">Chiudi</button>
          </div>
        )}

        {/* La Prima 24h blocker banner */}
        {laPrimaBlock && (
          <div className={`p-3 rounded-xl border text-center ${
            laPrimaBlock.state === 'live' ? 'bg-red-500/10 border-red-500/40' : 'bg-yellow-500/10 border-yellow-500/40'
          }`} data-testid="la-prima-blocker">
            <p className={`text-[10px] font-bold uppercase tracking-wider ${laPrimaBlock.state === 'live' ? 'text-red-400' : 'text-yellow-400'}`}>
              {laPrimaBlock.state === 'live' ? 'La Prima in corso' : 'La Prima in attesa'}
            </p>
            <p className={`text-2xl font-black mt-1 ${laPrimaBlock.state === 'live' ? 'text-red-300' : 'text-yellow-300'}`}>
              {fmtDelta(laPrimaBlock.delta)}
            </p>
            <p className="text-[8px] text-gray-500 mt-1">
              Il rilascio e' bloccato fino alla fine della La Prima a {premiere.city}
            </p>
          </div>
        )}

        {/* Confirm Button with cost */}
        <button onClick={onConfirm} disabled={loading || releaseBlocked}
          className="w-full text-sm py-3 rounded-xl bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30 text-emerald-300 font-bold disabled:opacity-30 disabled:cursor-not-allowed" data-testid="confirm-release-btn">
          {loading ? '...' : releaseBlocked ? `Bloccato: La Prima ${laPrimaBlock.state === 'live' ? 'in corso' : 'in attesa'}` : `Confermi spendendo $${totalFunds.toLocaleString()} e ${totalCp}CP?`}
        </button>
        <button onClick={onDiscard} disabled={loading}
          className="w-full text-[9px] py-2 rounded-xl bg-red-500/5 border border-red-500/20 text-red-400/70 disabled:opacity-50">
          SCARTA FILM
        </button>
      </div>
    </PhaseWrapper>
  );
};
