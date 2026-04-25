/**
 * AdminStatusEditor — Selettore di stato cliccabile per il pannello admin.
 *
 * Mostra TUTTI gli stati possibili divisi per collection, con descrizione di
 * dove appare ogni stato nelle dashboard (così l'admin sa cosa sta cambiando).
 * Per le serie TV ha anche un toggle `prossimamente_tv` per la sezione "IN ARRIVO SU TV".
 *
 * Mobile-first: bottom-sheet su mobile, dialog centrato su desktop.
 * Il bottone Conferma è STICKY in alto e visibile sopra l'overlay.
 */
import React, { useMemo, useState, useEffect } from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { Check, X, AlertTriangle, Save } from 'lucide-react';

// ── Cataloghi stati per collection ─────────────────────────────────────
// Ogni stato è un oggetto { value, label, desc, color, sections }
// `sections` indica DOVE viene mostrato l'item con quello stato in dashboard.

const STATUSES_FILMS = [
  { value: 'in_theaters',     label: 'In Sala',           color: 'amber',  sections: ['Ultimi Al Cinema', 'Box Office', 'La Premiere'],  desc: 'Film attivamente in sala. Genera incassi giornalieri, conta nelle classifiche box office.' },
  { value: 'lampo_ready',     label: 'LAMPO · Bozza',     color: 'amber',  sections: ['Prossimamente Film', 'I Miei (bozza)'], desc: '⚡ Bozza LAMPO pronta da rilasciare. Visibile come "A breve al cinema" a tutti i player.' },
  { value: 'lampo_scheduled', label: 'LAMPO · Programmato', color: 'amber', sections: ['Prossimamente Film', 'In Arrivo'], desc: '⚡ LAMPO con uscita programmata futura. Mostra countdown.' },
  { value: 'completed',       label: 'Completato',        color: 'slate',  sections: ['Catalogo storico'], desc: 'Film terminato la corsa al cinema. Esce dalla rotation, resta nei profili e classifiche.' },
  { value: 'archived',        label: 'Archiviato',        color: 'slate',  sections: ['Catalogo storico'], desc: 'Film archiviato dopo molti giorni di catalogo. Solo storico.' },
  { value: 'released',        label: 'Rilasciato (legacy)', color: 'slate', sections: ['Catalogo'], desc: 'Stato generico legacy. Equivale a "completato".' },
  { value: 'pending_release', label: 'In Attesa Rilascio', color: 'cyan',  sections: ['I Miei'], desc: 'Pre-uscita, in attesa di scheduling. Solo lato produttore.' },
  { value: 'discarded',       label: 'Scartato',          color: 'rose',   sections: ['(nessuna)'], desc: 'Item scartato dall\'utente. Non visibile in dashboard pubbliche.' },
  { value: 'deleted',         label: 'Eliminato',         color: 'rose',   sections: ['(nessuna)'], desc: 'Eliminato. Nasconde dappertutto.' },
];

const STATUSES_FILM_PROJECTS = [
  { value: 'idea',           label: 'Idea',           color: 'gray',  sections: ['Pipeline V3 (Idea)'], desc: 'Step iniziale: idea, hype non ancora generato.' },
  { value: 'casting',        label: 'Casting',        color: 'cyan',  sections: ['Pipeline V3'], desc: 'Step casting: scelta attori e regista.' },
  { value: 'screenplay',     label: 'Sceneggiatura',  color: 'cyan',  sections: ['Pipeline V3'], desc: 'Step sceneggiatura: definizione script e PreVoto.' },
  { value: 'pre_production', label: 'Pre-produzione', color: 'cyan',  sections: ['Pipeline V3'], desc: 'Step preparativi: budget, sponsor, locandina.' },
  { value: 'shooting',       label: 'Riprese',        color: 'amber', sections: ['Pipeline V3', 'Prossimamente'], desc: 'Step ciak, riprese in corso (tempo reale).' },
  { value: 'pending_release',label: 'In Attesa Rilascio', color: 'amber', sections: ['Pipeline V3', 'Prossimamente'], desc: 'Pronto per il rilascio finale (Premiere/Distribution).' },
  { value: 'coming_soon',    label: 'Coming Soon',    color: 'amber', sections: ['Prossimamente'], desc: 'Visibile a tutti come "prossimamente al cinema".' },
  { value: 'discarded',      label: 'Scartato',       color: 'rose',  sections: ['(nessuna)'], desc: 'Progetto scartato dall\'utente. Nascosto.' },
  { value: 'released',       label: 'Rilasciato',     color: 'slate', sections: ['(in films)'], desc: 'Stato finale: il film è ora in collection films. Non dovrebbe servire più.' },
];

const STATUSES_TV_SERIES = [
  { value: 'in_tv',           label: 'In TV',             color: 'cyan',   sections: ['In Arrivo Su TV', 'Ultimi Aggiornamenti', 'Le Mie TV'], desc: 'Serie in onda su una stazione TV. Visibile a tutti, episodi rilasciati progressivamente. Richiede `prossimamente_tv: true`.' },
  { value: 'catalog',         label: 'Catalogo',          color: 'slate',  sections: ['Catalogo (proprietario)'], desc: 'Solo nel catalogo del produttore (no broadcast TV). Visibile solo a lui.' },
  { value: 'completed',       label: 'Completata',        color: 'emerald', sections: ['Ultimi Aggiornamenti', 'Catalogo storico'], desc: 'Tutti gli episodi sono andati in onda. Termina la rotation TV.' },
  { value: 'released',        label: 'Rilasciata (legacy)', color: 'slate', sections: ['Catalogo'], desc: 'Stato generico legacy.' },
  { value: 'lampo_ready',     label: 'LAMPO · Bozza',     color: 'amber',  sections: ['Prossimamente Serie/Anime', 'In Arrivo Su TV', 'Ultimi Aggiornamenti'], desc: '⚡ Bozza LAMPO pronta da rilasciare. Visibile come "A breve" a tutti.' },
  { value: 'lampo_scheduled', label: 'LAMPO · Programmata', color: 'amber', sections: ['Prossimamente Serie/Anime', 'In Arrivo Su TV'], desc: '⚡ LAMPO programmata. Mostra countdown.' },
  { value: 'coming_soon',     label: 'Coming Soon',       color: 'cyan',   sections: ['Prossimamente'], desc: 'In coming-soon (pre-rilascio).' },
  { value: 'production',      label: 'In Produzione',     color: 'cyan',   sections: ['Prossimamente (in lavorazione)'], desc: 'Serie in fase di produzione attiva.' },
  { value: 'ready_to_release',label: 'Pronta al Rilascio',color: 'amber',  sections: ['Prossimamente'], desc: 'Serie completata, in attesa del rilascio.' },
  { value: 'discarded',       label: 'Scartata',          color: 'rose',   sections: ['(nessuna)'], desc: 'Scartata. Nascosta.' },
];

const STATUSES_SERIES_PROJECTS_V3 = [
  { value: 'idea',     label: 'Idea',          color: 'gray',  sections: ['Pipeline V3 (Idea)'], desc: 'Step iniziale.' },
  { value: 'hype',     label: 'Hype',          color: 'cyan',  sections: ['Pipeline V3'], desc: 'Step hype.' },
  { value: 'cast',     label: 'Cast',          color: 'cyan',  sections: ['Pipeline V3'], desc: 'Step cast.' },
  { value: 'prep',     label: 'Pre-produzione', color: 'cyan', sections: ['Pipeline V3'], desc: 'Step preparativi.' },
  { value: 'ciak',     label: 'Riprese',       color: 'amber', sections: ['Pipeline V3'], desc: 'Step ciak (riprese).' },
  { value: 'finalcut', label: 'Final Cut',     color: 'amber', sections: ['Pipeline V3'], desc: 'Step finalizzazione.' },
  { value: 'marketing',label: 'Marketing',     color: 'amber', sections: ['Pipeline V3'], desc: 'Step marketing pre-rilascio.' },
  { value: 'distribution', label: 'Distribuzione TV', color: 'amber', sections: ['Pipeline V3', 'Prossimamente'], desc: 'Scelta stazione TV / catalogo.' },
  { value: 'release_pending', label: 'Pronta al Rilascio', color: 'amber', sections: ['Pipeline V3'], desc: 'Pronta al rilascio finale.' },
  { value: 'discarded',label: 'Scartata',      color: 'rose',  sections: ['(nessuna)'], desc: 'Scartata.' },
];

const STATUSES_BY_COLLECTION = {
  films: STATUSES_FILMS,
  film_projects: STATUSES_FILM_PROJECTS,
  tv_series: STATUSES_TV_SERIES,
  series_projects_v3: STATUSES_SERIES_PROJECTS_V3,
};

const COLLECTION_LABELS = {
  films: 'Film (rilasciati)',
  film_projects: 'Film Projects (V3 in lavorazione)',
  tv_series: 'Serie TV / Anime (rilasciati)',
  series_projects_v3: 'Series Projects V3 (in lavorazione)',
};

const COLOR_MAP = {
  amber:   { bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   text: 'text-amber-200',   dot: 'bg-amber-400' },
  cyan:    { bg: 'bg-cyan-500/10',    border: 'border-cyan-500/30',    text: 'text-cyan-200',    dot: 'bg-cyan-400' },
  emerald: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-200', dot: 'bg-emerald-400' },
  slate:   { bg: 'bg-slate-500/10',   border: 'border-slate-500/30',   text: 'text-slate-200',   dot: 'bg-slate-400' },
  gray:    { bg: 'bg-gray-500/10',    border: 'border-gray-500/30',    text: 'text-gray-200',    dot: 'bg-gray-400' },
  rose:    { bg: 'bg-rose-500/10',    border: 'border-rose-500/30',    text: 'text-rose-200',    dot: 'bg-rose-400' },
};

// ── Componente ─────────────────────────────────────────────────────────
export default function AdminStatusEditor({ open, onClose, item, api, onUpdated }) {
  const collection = item?.collection || 'films';
  const currentStatus = item?.stage || item?.status;
  const isSeries = collection === 'tv_series';

  const statuses = useMemo(() => STATUSES_BY_COLLECTION[collection] || [], [collection]);

  const [selectedStatus, setSelectedStatus] = useState(currentStatus);
  const [prossimamenteTv, setProssimamenteTv] = useState(!!item?.prossimamente_tv);
  const [syncPipeline, setSyncPipeline] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open) {
      setSelectedStatus(currentStatus);
      setProssimamenteTv(!!item?.prossimamente_tv);
      setSyncPipeline(true);
      setError(null);
    }
  }, [open, currentStatus, item?.prossimamente_tv]);

  const isDirty = selectedStatus !== currentStatus
    || (isSeries && prossimamenteTv !== !!item?.prossimamente_tv);

  const isProjectCollection = collection === 'film_projects' || collection === 'series_projects_v3';

  const handleSave = async () => {
    if (!item || !isDirty) { onClose?.(); return; }
    setSaving(true);
    setError(null);
    try {
      const payload = {
        item_id: item.id,
        collection,
        status: selectedStatus,
      };
      if (isSeries) payload.prossimamente_tv = prossimamenteTv;
      if (isProjectCollection) payload.sync_pipeline_state = syncPipeline;
      const res = await api.post('/admin/set-content-status', payload);
      if (res.data?.success) {
        onUpdated?.(res.data.item);
        onClose?.();
      } else {
        setError('Risposta inattesa dal server.');
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Errore salvataggio stato.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent
        className="max-w-md p-0 bg-[#0a0a0c] border border-white/10 max-h-[90vh] overflow-hidden flex flex-col"
        style={{ zIndex: 200 }}  /* ensure on top of underlying admin popup */
        data-testid="admin-status-editor"
      >
        {/* STICKY HEADER + CONFIRM (sopra l'overlay, sempre visibile) */}
        <div className="px-4 pt-3 pb-3 border-b border-white/10 bg-[#0a0a0c] flex-shrink-0 sticky top-0 z-10">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-white truncate font-['Bebas_Neue'] tracking-wide text-base">
                Cambia Stato
              </h2>
              <p className="text-[10px] text-white/50 truncate">"{item?.title || '—'}"</p>
              <p className="text-[9px] text-white/40 mt-0.5">
                Collection: <span className="font-mono text-amber-300">{collection}</span>
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white/40 hover:text-white p-1 -mr-1 flex-shrink-0"
              data-testid="admin-status-editor-close"
              aria-label="Chiudi"
            >
              <X size={16} />
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving || !isDirty}
              data-testid="admin-status-confirm-btn"
              className={`flex-1 py-2.5 rounded-lg text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all touch-manipulation ${
                isDirty && !saving
                  ? 'bg-emerald-500 text-black hover:bg-emerald-400 active:scale-95'
                  : 'bg-white/5 text-white/30 cursor-not-allowed'
              }`}
            >
              <Save size={14} />
              {saving ? 'Salvataggio…' : isDirty ? 'CONFERMA MODIFICHE' : 'Nessuna modifica'}
            </button>
            <button
              onClick={onClose}
              disabled={saving}
              data-testid="admin-status-cancel-btn"
              className="px-3 py-2.5 rounded-lg text-[11px] font-bold border border-white/10 text-white/70 hover:bg-white/5 active:scale-95 transition-all touch-manipulation"
            >
              Annulla
            </button>
          </div>
          {error && (
            <div className="mt-2 px-2 py-1.5 rounded bg-rose-500/10 border border-rose-500/30 text-[10px] text-rose-300 flex items-center gap-1.5">
              <AlertTriangle size={12} /> {error}
            </div>
          )}
        </div>

        {/* SCROLLABLE BODY */}
        <div className="flex-1 overflow-y-auto px-4 py-3" data-testid="admin-status-editor-body">
          {/* Currently selected indicator */}
          <div className="mb-3 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
            <div className="text-[9px] uppercase tracking-widest text-white/50 font-semibold">Stato attuale</div>
            <div className="font-mono text-amber-300 text-sm font-bold">{currentStatus || '—'}</div>
          </div>

          {/* Toggle prossimamente_tv (solo tv_series) */}
          {isSeries && (
            <div className="mb-3 px-3 py-2.5 rounded-lg bg-cyan-500/5 border border-cyan-500/20">
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="text-[10px] font-bold text-cyan-200 uppercase tracking-wider">Prossimamente TV</div>
                  <div className="text-[9px] text-white/60 leading-snug">Se ON, la serie compare in "IN ARRIVO SU TV" e "Prossimamente Serie/Anime" globali.</div>
                </div>
                <button
                  onClick={() => setProssimamenteTv(v => !v)}
                  data-testid="admin-status-prossimamente-toggle"
                  className={`flex-shrink-0 w-12 h-6 rounded-full relative transition-colors ${prossimamenteTv ? 'bg-cyan-500' : 'bg-white/10'}`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${prossimamenteTv ? 'translate-x-6' : 'translate-x-0.5'}`} />
                </button>
              </div>
            </div>
          )}

          {/* Sync pipeline_state checkbox (project collections) */}
          {isProjectCollection && (
            <div className="mb-3 px-3 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20">
              <label className="flex items-start gap-2 cursor-pointer touch-manipulation">
                <input
                  type="checkbox"
                  checked={syncPipeline}
                  onChange={e => setSyncPipeline(e.target.checked)}
                  data-testid="admin-status-sync-pipeline-checkbox"
                  className="mt-0.5 w-4 h-4 accent-amber-500"
                />
                <div className="min-w-0 flex-1">
                  <div className="text-[10px] font-bold text-amber-200">Sincronizza anche `pipeline_state`</div>
                  <div className="text-[9px] text-white/60 leading-snug">Per i progetti V3, copia lo status anche in `pipeline_state` (consigliato).</div>
                </div>
              </label>
            </div>
          )}

          <div className="text-[10px] uppercase tracking-wider text-white/50 font-semibold mb-2 px-1">
            Stati disponibili — {COLLECTION_LABELS[collection]}
          </div>

          {/* Status options */}
          <div className="space-y-1.5">
            {statuses.map(s => {
              const isSelected = selectedStatus === s.value;
              const c = COLOR_MAP[s.color] || COLOR_MAP.gray;
              return (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setSelectedStatus(s.value)}
                  data-testid={`admin-status-option-${s.value}`}
                  className={`w-full text-left rounded-lg px-3 py-2.5 transition-all touch-manipulation ${
                    isSelected
                      ? `${c.bg} ${c.border} border-2 shadow-[0_0_10px_rgba(251,191,36,0.15)]`
                      : 'bg-white/[0.02] border border-white/5 hover:bg-white/5 active:bg-white/10'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${c.dot} flex-shrink-0`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`font-mono text-[11px] font-bold ${isSelected ? c.text : 'text-white/80'}`}>
                          {s.value}
                        </span>
                        <span className="text-[10px] text-white/50">— {s.label}</span>
                      </div>
                      <div className="text-[9px] text-white/55 leading-snug mt-0.5">{s.desc}</div>
                      {s.sections?.length > 0 && (
                        <div className="flex gap-1 flex-wrap mt-1">
                          {s.sections.map((sec, i) => (
                            <span key={i} className="px-1.5 py-0.5 text-[8px] rounded-full bg-white/5 border border-white/10 text-white/60">
                              📍 {sec}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    {isSelected && <Check size={16} className="text-emerald-400 flex-shrink-0" />}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Footer hint */}
          <div className="mt-4 px-3 py-2 rounded bg-rose-500/5 border border-rose-500/20">
            <p className="text-[9px] text-rose-200/80 italic leading-snug">
              ⚠ La modifica è REALE e immediata in DB. Usa con cautela: alcuni stati attivano logica
              automatica (es. il scheduler promuove `lampo_scheduled` → `in_theaters` allo scadere).
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
