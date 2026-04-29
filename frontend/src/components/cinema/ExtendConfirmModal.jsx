// CineWorld Studio's — ExtendConfirmModal
// Modale conferma prolungamento sale (stile Cineox/Velion).

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Loader2, X, Coins, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { Button } from '../ui/button';
import { Slider } from '../ui/slider';

const API = process.env.REACT_APP_BACKEND_URL;

const fmtMoney = (v) => `$${Math.round(Number(v || 0)).toLocaleString('it-IT')}`;

export const ExtendConfirmModal = ({ stats, onClose, onSuccess }) => {
  const ext = stats.actions.extend;
  const [days, setDays] = useState(ext?.default_days || 7);
  const [submitting, setSubmitting] = useState(false);

  // Calcolo costo lato client (preview)
  const costPerDay = ext?.preview_cost_per_day || { money_cost: 0, cp_cost: 0 };
  const moneyTotal = (costPerDay.money_cost || 0) * days;
  const cpTotal = (costPerDay.cp_cost || 0) * days;

  const handleConfirm = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.post(
        `${API}/api/cinema-stats/${stats.content.id}/extend`,
        { extra_days: days, confirm: true },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      toast.success(`✅ Programmazione prolungata di ${res.data.extra_days} giorni!`);
      onSuccess?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore prolungamento');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-[10000] bg-black/80 backdrop-blur-sm flex items-center justify-center p-3"
      data-testid="extend-confirm-modal"
    >
      <motion.div
        initial={{ scale: 0.92, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-gradient-to-br from-emerald-950/90 via-zinc-950 to-zinc-950 ring-1 ring-emerald-700/40 shadow-2xl"
      >
        <div className="flex items-center justify-between p-4 border-b border-emerald-900/40">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <Plus className="w-4 h-4 text-emerald-300" />
            </div>
            <div>
              <div className="text-sm font-bold text-emerald-200">Prolunga programmazione</div>
              <div className="text-[10px] text-zinc-500">Cineox/Velion · Conferma azione</div>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-md hover:bg-zinc-800/60 text-zinc-400" data-testid="extend-close">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div className="text-xs text-zinc-300 leading-relaxed">
            Stai per prolungare <strong className="text-emerald-200">"{stats.content.title}"</strong> nelle sale.
            I costi crescono in base alla media incassi degli ultimi 3 giorni.
          </div>

          {/* Slider giorni */}
          <div>
            <div className="flex items-baseline justify-between mb-2">
              <span className="text-xs text-zinc-400">Giorni extra</span>
              <span className="text-xl font-black text-emerald-300" data-testid="extend-days-value">
                +{days} <span className="text-xs font-normal text-zinc-400">giorni</span>
              </span>
            </div>
            <Slider
              value={[days]}
              min={ext.min_days}
              max={ext.max_days}
              step={1}
              onValueChange={(v) => setDays(v[0])}
              data-testid="extend-days-slider"
            />
            <div className="flex justify-between text-[9px] text-zinc-600 mt-1">
              <span>{ext.min_days}</span>
              <span>7</span>
              <span>{ext.max_days}</span>
            </div>
          </div>

          {/* Cost preview */}
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg bg-zinc-900/60 ring-1 ring-zinc-800 p-3">
              <div className="text-[10px] text-zinc-500 flex items-center gap-1 mb-0.5">
                <Coins className="w-3 h-3" /> Costo
              </div>
              <div className="text-base font-bold text-amber-300" data-testid="extend-money-cost">
                {fmtMoney(moneyTotal)}
              </div>
            </div>
            <div className="rounded-lg bg-zinc-900/60 ring-1 ring-zinc-800 p-3">
              <div className="text-[10px] text-zinc-500 flex items-center gap-1 mb-0.5">
                <Sparkles className="w-3 h-3" /> CP richiesti
              </div>
              <div className="text-base font-bold text-violet-300" data-testid="extend-cp-cost">
                {cpTotal} CP
              </div>
            </div>
          </div>

          {/* Bonus info */}
          <div className="rounded-lg bg-emerald-950/40 ring-1 ring-emerald-700/30 p-2.5 text-[10px] text-emerald-200/90 leading-snug">
            🌟 <strong>Bonus prolungamento</strong>: se mantieni un hold ratio &gt;70% durante l'estensione, riceverai +0.2 al CWSv display finale.
          </div>
        </div>

        <div className="flex gap-2 p-4 pt-0">
          <Button variant="ghost" onClick={onClose} disabled={submitting} className="flex-1" data-testid="extend-cancel">
            Annulla
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={submitting}
            className="flex-1 bg-emerald-600 hover:bg-emerald-500 font-bold"
            data-testid="extend-confirm"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : `Prolunga +${days}gg`}
          </Button>
        </div>
      </motion.div>
    </div>
  );
};

export default ExtendConfirmModal;
