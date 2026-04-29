import React, { useState, useContext } from 'react';
import { AlertTriangle, X, Send, Loader2 } from 'lucide-react';
import { AuthContext } from '../../contexts';
import { toast } from 'sonner';

const CATEGORIES = [
  { id: 'inappropriato', label: 'Contenuto inappropriato', color: 'rose' },
  { id: 'spam', label: 'Spam', color: 'amber' },
  { id: 'plagio', label: 'Plagio', color: 'violet' },
  { id: 'offensivo', label: 'Offensivo', color: 'red' },
  { id: 'altro', label: 'Altro', color: 'gray' },
];

export default function ReportContentButton({ contentType = 'film', contentId, contentTitle, ownerUserId }) {
  const { api, user } = useContext(AuthContext);
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState('inappropriato');
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);

  const isOwn = ownerUserId && user?.id === ownerUserId;
  if (isOwn) return null;

  const submit = async () => {
    setBusy(true);
    try {
      const res = await api.post('/reports', { content_type: contentType, content_id: contentId, category, notes: notes.trim() || undefined });
      if (res.data?.target_is_admin) {
        toast.info(res.data.message || 'Segnalazione registrata.');
      } else {
        toast.success('Segnalazione inviata. Grazie!');
      }
      setOpen(false);
      setNotes('');
    } catch (e) {
      const detail = e?.response?.data?.detail || 'Errore invio segnalazione';
      toast.error(detail);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        data-testid="report-content-btn"
        className="w-full mt-4 py-2.5 rounded-lg border border-rose-500/30 bg-rose-500/5 text-rose-300 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-2 hover:bg-rose-500/10 transition-colors"
      >
        <AlertTriangle className="w-3.5 h-3.5" /> Segnala questo contenuto
      </button>
      {open && (
        <div className="fixed inset-0 z-[120] bg-black/80 backdrop-blur-sm flex items-center justify-center p-3" onClick={() => !busy && setOpen(false)} data-testid="report-modal">
          <div className="w-full max-w-md rounded-2xl bg-gradient-to-br from-zinc-900 to-zinc-950 border border-rose-500/30 p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-rose-400 font-bold">Segnalazione</p>
                <p className="text-sm font-bold text-white truncate max-w-[20rem]">{contentTitle || 'Contenuto'}</p>
              </div>
              <button onClick={() => !busy && setOpen(false)} className="text-zinc-400 hover:text-white" data-testid="report-modal-close">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-[10px] text-zinc-400 mb-2 uppercase font-bold">Categoria</p>
            <div className="grid grid-cols-2 gap-1.5 mb-3">
              {CATEGORIES.map(c => (
                <button
                  key={c.id}
                  onClick={() => setCategory(c.id)}
                  data-testid={`report-cat-${c.id}`}
                  className={`px-2 py-2 rounded-lg text-[10px] font-bold border transition-all ${
                    category === c.id
                      ? 'border-rose-500/60 bg-rose-500/15 text-rose-200'
                      : 'border-zinc-700 bg-zinc-900/40 text-zinc-400 hover:border-zinc-600'
                  }`}
                >
                  {c.label}
                </button>
              ))}
            </div>

            <p className="text-[10px] text-zinc-400 mb-1 uppercase font-bold">Note <span className="text-zinc-600 normal-case">(opzionale, max 500)</span></p>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value.slice(0, 500))}
              rows={3}
              placeholder="Spiega brevemente perché segnali questo contenuto…"
              data-testid="report-notes"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2.5 py-2 text-xs text-white placeholder-zinc-600 focus:border-rose-500/50 outline-none resize-none"
            />

            <div className="flex items-center gap-2 mt-3">
              <button
                onClick={() => !busy && setOpen(false)}
                disabled={busy}
                className="flex-1 py-2.5 rounded-lg border border-zinc-700 bg-zinc-900/40 text-zinc-300 text-[11px] font-bold hover:bg-zinc-800"
              >
                Annulla
              </button>
              <button
                onClick={submit}
                disabled={busy}
                data-testid="report-submit-btn"
                className="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-rose-500 to-red-600 text-white text-[11px] font-bold flex items-center justify-center gap-1.5 hover:scale-[1.02] transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                {busy ? 'Invio…' : 'Invia segnalazione'}
              </button>
            </div>

            <p className="text-[8px] text-zinc-500 mt-3 text-center">
              Le segnalazioni false o ripetute possono comportare provvedimenti.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
