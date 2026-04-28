// CineWorld Studio's — WithdrawConfirmModal
// Modale conferma ritiro anticipato (stile Cineox/Velion).
// Mostra le penalty: -1 fama (se hold buono) + -5% incassi previsti del prossimo mese.

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Pause, Loader2, X, AlertTriangle, TrendingDown, Award } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { Button } from '../ui/button';

const API = process.env.REACT_APP_BACKEND_URL;

export const WithdrawConfirmModal = ({ stats, onClose, onSuccess }) => {
  const [submitting, setSubmitting] = useState(false);
  const wit = stats.actions.withdraw;
  const penalty = wit?.penalty || {};

  const handleConfirm = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('cineworld_token');
      await axios.post(
        `${API}/api/cinema-stats/${stats.content.id}/withdraw`,
        { confirm: true },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      toast.success(`Film ritirato dalle sale${penalty.fame_penalty > 0 ? ` (-${penalty.fame_penalty} fama)` : ''}`);
      onSuccess?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore ritiro');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-[10000] bg-black/80 backdrop-blur-sm flex items-center justify-center p-3"
      data-testid="withdraw-confirm-modal"
    >
      <motion.div
        initial={{ scale: 0.92, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-gradient-to-br from-rose-950/90 via-zinc-950 to-zinc-950 ring-1 ring-rose-700/40 shadow-2xl"
      >
        <div className="flex items-center justify-between p-4 border-b border-rose-900/40">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-rose-500/20 flex items-center justify-center">
              <Pause className="w-4 h-4 text-rose-300" />
            </div>
            <div>
              <div className="text-sm font-bold text-rose-200">Ritira dalle sale</div>
              <div className="text-[10px] text-zinc-500">Cineox/Velion · Conferma azione</div>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-md hover:bg-zinc-800/60 text-zinc-400" data-testid="withdraw-close">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 space-y-3">
          <div className="text-xs text-zinc-300 leading-relaxed">
            Stai per ritirare anticipatamente <strong className="text-rose-200">"{stats.content.title}"</strong> dalle sale.
            Il film verrà spostato nello stato <em>«Completato»</em> e non genererà più incassi.
          </div>

          {/* Penalty rosse */}
          <div className="space-y-2">
            <div className="flex items-start gap-2 rounded-lg bg-zinc-900/60 ring-1 ring-zinc-800 p-2.5">
              <Award className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-[10px] text-zinc-400 uppercase tracking-wider">Penalità Fama</div>
                {penalty.fame_penalty > 0 ? (
                  <div className="text-sm font-bold text-rose-300" data-testid="withdraw-fame-penalty">
                    -{penalty.fame_penalty} fama
                  </div>
                ) : (
                  <div className="text-sm font-bold text-emerald-400">Nessuna</div>
                )}
                {penalty.is_impulsive && (
                  <div className="text-[10px] text-rose-300/80 mt-0.5">
                    Hold ratio recente: {Math.round((penalty.recent_hold_ratio || 0) * 100)}%. Ritirare con buoni incassi sembra impulsivo.
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-start gap-2 rounded-lg bg-zinc-900/60 ring-1 ring-zinc-800 p-2.5">
              <TrendingDown className="w-4 h-4 text-orange-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-[10px] text-zinc-400 uppercase tracking-wider">Effetto sul mercato</div>
                <div className="text-sm font-bold text-orange-300" data-testid="withdraw-rev-penalty">
                  -{Math.round((penalty.future_revenue_penalty_pct || 0) * 100)}% incassi prossimi 30 giorni
                </div>
                <div className="text-[10px] text-zinc-500 mt-0.5">
                  Gli esercenti perderanno fiducia: i tuoi prossimi film del mese soffriranno questa scelta.
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-rose-950/40 ring-1 ring-rose-700/30 p-2.5 text-[11px] text-rose-200 leading-snug flex items-start gap-2">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>Azione irreversibile. Il film passerà subito allo stato «Completato».</span>
          </div>
        </div>

        <div className="flex gap-2 p-4 pt-0">
          <Button variant="ghost" onClick={onClose} disabled={submitting} className="flex-1" data-testid="withdraw-cancel">
            Annulla
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={submitting}
            className="flex-1 bg-rose-700 hover:bg-rose-600 font-bold"
            data-testid="withdraw-confirm"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Conferma ritiro'}
          </Button>
        </div>
      </motion.div>
    </div>
  );
};

export default WithdrawConfirmModal;
