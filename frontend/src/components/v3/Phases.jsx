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
  const [configured, setConfigured] = useState(!!(film.hype_notes || film.hype_budget > 0));
  const [hypeProgress, setHypeProgress] = useState(film.hype_progress || 0);
  const progressRef = useRef(null);

  // Simulate hype progress after configuration
  useEffect(() => {
    if (configured && hypeProgress < 100) {
      progressRef.current = setInterval(() => {
        setHypeProgress(prev => {
          const next = prev + Math.random() * 0.5 + 0.1;
          if (next >= 100) { clearInterval(progressRef.current); return 100; }
          return next;
        });
      }, 3000);
      return () => { if (progressRef.current) clearInterval(progressRef.current); };
    }
  }, [configured, hypeProgress]);

  const save = async () => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/save-hype`, 'POST', { hype_notes: strategy, budget: duration });
      await onRefresh();
      setConfigured(true);
      setHypeProgress(prev => Math.max(prev, 5));
      toast?.('Hype configurato!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const speedup = async (pct) => {
    const cost = getSpeedupCost(SPEEDUP_COSTS[pct], hypeProgress);
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/speedup`, 'POST', { stage: 'hype', percentage: pct });
      // Add percentage of REMAINING progress (so 100% always reaches 100%)
      const remaining = 100 - hypeProgress;
      const gain = remaining * (pct / 100);
      setHypeProgress(prev => Math.min(100, prev + gain));
      await onRefresh();
      toast?.(`Velocizzato +${Math.ceil(gain)}% (-${cost} CP)`);
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
  const [releaseType, setReleaseType] = useState(film.release_type || 'direct');
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
      await v3api(`/films/${film.id}/set-release-type`, 'POST', { release_type: releaseType });
      await onRefresh(); toast?.('Marketing + rilascio confermati!');
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
            {/* Release type */}
            <div className="border-t border-gray-800 pt-3 space-y-2">
              <p className="text-[8px] text-gray-500 uppercase font-bold text-center">Come vuoi rilasciare il film?</p>
              <div className="grid grid-cols-2 gap-2">
                <button onClick={() => { setReleaseType('premiere'); onDirty?.(); }}
                  className={`p-3 rounded-xl border text-center ${releaseType === 'premiere' ? 'bg-yellow-500/15 border-yellow-500/50' : 'bg-gray-800/30 border-gray-700'}`}>
                  <Award className={`w-5 h-5 mx-auto mb-1 ${releaseType === 'premiere' ? 'text-yellow-400' : 'text-gray-600'}`} />
                  <p className={`text-[9px] font-bold ${releaseType === 'premiere' ? 'text-yellow-400' : 'text-gray-500'}`}>La Prima</p>
                </button>
                <button onClick={() => { setReleaseType('direct'); onDirty?.(); }}
                  className={`p-3 rounded-xl border text-center ${releaseType === 'direct' ? 'bg-emerald-500/15 border-emerald-500/50' : 'bg-gray-800/30 border-gray-700'}`}>
                  <Ticket className={`w-5 h-5 mx-auto mb-1 ${releaseType === 'direct' ? 'text-emerald-400' : 'text-gray-600'}`} />
                  <p className={`text-[9px] font-bold ${releaseType === 'direct' ? 'text-emerald-400' : 'text-gray-500'}`}>Diretto</p>
                </button>
              </div>
            </div>
            {!done && (
              <button onClick={saveMarketing} disabled={loading} className="w-full text-[9px] py-2 rounded-xl bg-green-500/15 border border-green-500/30 text-green-400 disabled:opacity-30 font-bold">
                {loading ? '...' : 'Conferma Marketing e Rilascio'}
              </button>
            )}
          </>
        )}
      </div>
    </PhaseWrapper>
  );
};

/* ═══════ LA PRIMA ═══════ */
export const LaPrimaPhase = ({ film, onRefresh, toast }) => {
  const [loading, setLoading] = useState(false);
  const [primaProgress, setPrimaProgress] = useState(film.prima_progress || 0);
  const progressRef = useRef(null);
  const isPremiere = film.release_type === 'premiere';

  useEffect(() => {
    if (isPremiere && primaProgress < 100) {
      progressRef.current = setInterval(() => {
        setPrimaProgress(prev => {
          const next = prev + Math.random() * 0.3 + 0.05;
          if (next >= 100) { clearInterval(progressRef.current); return 100; }
          return next;
        });
      }, 4000);
      return () => { if (progressRef.current) clearInterval(progressRef.current); };
    }
  }, [isPremiere, primaProgress]);

  const speedup = async (pct) => {
    const cost = getSpeedupCost(SPEEDUP_COSTS[pct], primaProgress);
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/speedup`, 'POST', { stage: 'premiere', percentage: pct });
      const remaining = 100 - primaProgress;
      const gain = remaining * (pct / 100);
      setPrimaProgress(prev => Math.min(100, prev + gain));
      await onRefresh();
      toast?.(`Velocizzato +${Math.ceil(gain)}% (-${cost} CP)`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="La Prima" subtitle="L'evento esclusivo di anteprima" icon={Award} color="yellow">
      <div className="space-y-3">
        {isPremiere ? (
          <>
            <div className="p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/15 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[8px] text-gray-500 uppercase font-bold">Preparazione Premiere</span>
                <span className="text-[10px] font-black text-yellow-400">{Math.floor(primaProgress)}%</span>
              </div>
              <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-yellow-600 to-amber-300 transition-all duration-1000 ease-out"
                  style={{ width: `${Math.min(100, primaProgress)}%` }} />
              </div>
              <p className="text-[7px] text-gray-600 text-center">
                {primaProgress >= 100 ? 'Premiere pronta! Avanza alla distribuzione.' :
                 'L\'anteprima esclusiva sta prendendo forma...'}
              </p>
            </div>
            <p className="text-[8px] text-gray-500 uppercase font-bold">Velocizza Premiere (a pagamento)</p>
            <div className="grid grid-cols-2 gap-1.5">
              {[25,50,75,100].map(p => {
                const cost = getSpeedupCost(SPEEDUP_COSTS[p], primaProgress);
                const remaining = 100 - primaProgress;
                const gain = Math.ceil(remaining * (p / 100));
                return (
                  <button key={p} onClick={() => speedup(p)} disabled={loading || primaProgress >= 100}
                    className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg bg-yellow-500/5 border border-yellow-500/15 text-yellow-400 text-[8px] font-bold disabled:opacity-30 hover:bg-yellow-500/10 transition-all">
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
const DATES = ['Immediato','6 ore','12 ore','24 ore','2 giorni','3 giorni'];

export const DistributionPhase = ({ film, onRefresh, toast, onDirty }) => {
  const [date, setDate] = useState(film.release_date_label || 'Immediato');
  const [world, setWorld] = useState(film.distribution_world ?? true);
  const [loading, setLoading] = useState(false);
  const isPremiere = film.release_type === 'premiere';

  const save = async () => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/schedule-release`, 'POST', { release_date_label: date, world, zones: [] });
      await onRefresh(); toast?.('Distribuzione confermata!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  return (
    <PhaseWrapper title="Distribuzione" subtitle="Zone e data di uscita" icon={Globe} color="blue">
      <div className="space-y-3">
        <p className="text-[8px] text-gray-500 uppercase font-bold">Data uscita</p>
        <div className="grid grid-cols-3 gap-1.5">
          {DATES.map(label => {
            const disabled = isPremiere && label === 'Immediato';
            return (
              <button key={label} onClick={() => !disabled && setDate(label)} disabled={disabled}
                title={disabled ? 'La Prima richiede attesa' : ''}
                className={`py-2 rounded-lg text-[8px] font-bold border ${
                  disabled ? 'opacity-20 cursor-not-allowed border-gray-800 text-gray-600' :
                  date === label ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' :
                  'border-gray-800 text-gray-400 hover:border-gray-600'
                }`}>{label}</button>
            );
          })}
        </div>
        <label className="flex items-center gap-2 text-[9px] text-gray-400">
          <input type="checkbox" checked={world} onChange={e => { setWorld(e.target.checked); onDirty?.(); }} className="rounded" />
          Distribuzione Mondiale
        </label>
        <button onClick={save} disabled={loading} className="w-full text-[9px] py-2 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-400 disabled:opacity-30 font-bold">
          {loading ? '...' : 'Conferma Distribuzione'}
        </button>
      </div>
    </PhaseWrapper>
  );
};

/* ═══════ STEP FINALE ═══════ */
export const StepFinale = ({ film, onConfirm, onDiscard, loading, releaseType }) => (
  <PhaseWrapper title="STEP FINALE" subtitle="Riepilogo e conferma uscita" icon={Ticket} color="emerald">
    <div className="space-y-3">
      <div className="flex justify-center">
        {film.poster_url ? <img src={film.poster_url} alt="" className="w-24 h-36 rounded-lg border border-gray-700 object-cover shadow-lg" /> :
          <div className="w-24 h-36 rounded-lg border border-gray-700 bg-gray-800/50 flex items-center justify-center"><Film className="w-6 h-6 text-gray-600" /></div>}
      </div>
      <div className="p-3 rounded-xl bg-gray-800/30 border border-gray-700/50 text-center space-y-1">
        <p className="text-lg font-black text-white">{film.title}</p>
        <p className="text-[9px] text-gray-400">{releaseType === 'premiere' ? 'La Prima' : 'Rilascio Diretto'}</p>
        <p className="text-[8px] text-gray-600">Qualita: n.d. (calcolata dopo uscita)</p>
      </div>
      <button onClick={onConfirm} disabled={loading}
        className="w-full text-sm py-3 rounded-xl bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30 text-emerald-300 font-bold disabled:opacity-50" data-testid="confirm-release-btn">
        CONFERMA USCITA
      </button>
      <button onClick={onDiscard} disabled={loading}
        className="w-full text-[9px] py-2 rounded-xl bg-red-500/5 border border-red-500/20 text-red-400/70 disabled:opacity-50">
        SCARTA FILM
      </button>
    </div>
  </PhaseWrapper>
);
