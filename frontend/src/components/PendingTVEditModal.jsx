// CineWorld - Pending TV Edit Modal
// Appears when the station owner taps ✏️ on a pipeline-scheduled V3 series tile.
// Lets them override eps-per-batch, interval days, delay, and split-season settings.

import React, { useContext, useState } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { Tv, Sparkles, X, Save } from 'lucide-react';
import { toast } from 'sonner';

export default function PendingTVEditModal({ open, onClose, item, stationId, onSaved }) {
  const { api } = useContext(AuthContext);
  const isAnime = item?.type === 'anime' || item?.content_type === 'anime';
  const [epsBatch, setEpsBatch] = useState(item?.tv_eps_per_batch || 1);
  const [interval, setIntervalD] = useState(item?.tv_interval_days || 1);
  const [split, setSplit] = useState(item?.tv_split_season || false);
  const [pause, setPause] = useState(item?.tv_split_pause_days || 14);
  const [delay, setDelay] = useState(item?.distribution_delay_hours || 0);
  const [saving, setSaving] = useState(false);
  const policy = item?.release_policy || 'daily_1';

  const canChooseEps = policy !== 'daily_1';
  const canChooseInterval = policy === 'half_seasons' || policy === 'all_at_once';
  const canSplit = policy === 'half_seasons' || policy === 'all_at_once';

  const save = async () => {
    setSaving(true);
    try {
      await api.post(`/tv-stations/${stationId}/edit-pending/${item.id}`, {
        tv_eps_per_batch: epsBatch,
        tv_interval_days: interval,
        tv_split_season: split,
        tv_split_pause_days: pause,
        distribution_delay_hours: delay,
      });
      toast.success('Impostazioni aggiornate');
      onSaved?.();
      onClose();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore salvataggio');
    } finally { setSaving(false); }
  };

  if (!item) return null;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="bg-[#0F0F10] border-white/10 max-w-[400px] p-0 [&>button]:hidden" data-testid="pending-tv-edit-modal">
        {/* Header */}
        <div className="p-3 border-b border-white/5 flex items-center gap-2">
          {isAnime ? <Sparkles className="w-4 h-4 text-orange-400" /> : <Tv className="w-4 h-4 text-indigo-400" />}
          <div className="flex-1 min-w-0">
            <h2 className="text-sm font-bold text-white truncate">{item.title}</h2>
            <p className="text-[9px] text-gray-500">Modifica impostazioni trasmissione</p>
          </div>
          <button onClick={onClose} className="w-7 h-7 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center">
            <X className="w-3.5 h-3.5 text-gray-400" />
          </button>
        </div>

        <div className="p-3 space-y-3 max-h-[65vh] overflow-y-auto">
          <div className="p-2 rounded-lg bg-amber-500/5 border border-amber-500/15">
            <p className="text-[9px] text-amber-300">Politica rilascio: <span className="font-bold">{policy.replace('_', ' ')}</span></p>
            <p className="text-[8px] text-gray-500">Questa e' stata scelta dal produttore e non puoi cambiarla.</p>
          </div>

          {canChooseEps && (
            <div>
              <p className="text-[9px] text-gray-400 font-bold uppercase mb-1">Episodi per trasmissione</p>
              <div className="flex gap-1.5">
                {[1, 2, 3].map(n => (
                  <button key={n} onClick={() => setEpsBatch(n)} data-testid={`edit-eps-${n}`}
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
                  <button key={n} onClick={() => setIntervalD(n)} data-testid={`edit-interval-${n}`}
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
                  <p className="text-[8px] text-gray-500 mb-1">Pausa tra le due meta:</p>
                  <div className="flex gap-1 flex-wrap">
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

          <div>
            <p className="text-[9px] text-gray-400 font-bold uppercase mb-1">Inizio trasmissione (dal rilascio)</p>
            <div className="flex flex-wrap gap-1.5">
              {[0, 6, 12, 24, 48, 72].map(h => (
                <button key={h} onClick={() => setDelay(h)} data-testid={`edit-delay-${h}`}
                  className={`px-3 py-1.5 rounded-lg border text-[9px] font-bold ${delay === h ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-400' : 'border-gray-800 text-gray-500'}`}>
                  {h === 0 ? 'Immediato' : `Dopo ${h}h`}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="p-3 border-t border-white/5 flex gap-2">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-lg border border-white/10 text-[11px] font-bold text-gray-400 hover:bg-white/5">
            Annulla
          </button>
          <button onClick={save} disabled={saving} data-testid="pending-edit-save-btn"
            className="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 text-black text-[11px] font-black disabled:opacity-50 flex items-center justify-center gap-1">
            <Save className="w-3.5 h-3.5" /> {saving ? '...' : 'Salva e Conferma'}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
