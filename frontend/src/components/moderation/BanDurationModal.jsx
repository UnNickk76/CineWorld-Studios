import React, { useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';

/**
 * BanDurationModal — popup admin per scegliere la durata di un ban.
 * Accetta input free-form: "3 ore", "1 giorno", "permanente", "30 minuti", ecc.
 */
const PRESETS = ['3 ore', '7 ore', '1 giorno', '3 giorni', '7 giorni', '10 giorni', '30 giorni', 'permanente'];

export default function BanDurationModal({ open, target, onCancel, onConfirm, busy }) {
  const [duration, setDuration] = useState('1 giorno');
  const [reason, setReason] = useState('');
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[150] bg-black/85 backdrop-blur-sm flex items-center justify-center p-3" onClick={() => !busy && onCancel?.()} data-testid="ban-duration-modal">
      <div className="w-full max-w-sm rounded-2xl bg-gradient-to-br from-zinc-900 to-zinc-950 border border-rose-500/40 p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-rose-400 font-bold flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" /> Ban Utente
            </p>
            <p className="text-sm font-bold text-white truncate max-w-[14rem]">@{target?.nickname}</p>
          </div>
          <button onClick={() => !busy && onCancel?.()} className="text-zinc-400 hover:text-white"><X className="w-4 h-4" /></button>
        </div>

        <p className="text-[10px] text-zinc-400 mb-1 uppercase font-bold">Durata</p>
        <input
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
          placeholder="Es. 3 ore, 1 giorno, permanente"
          data-testid="ban-duration-input"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2.5 py-2 text-sm text-white focus:border-rose-500/50 outline-none"
        />
        <div className="flex flex-wrap gap-1.5 mt-2">
          {PRESETS.map(p => (
            <button
              key={p}
              type="button"
              onClick={() => setDuration(p)}
              data-testid={`ban-preset-${p}`}
              className={`px-2 py-1 rounded text-[9px] font-bold border ${duration === p ? 'border-rose-500/50 bg-rose-500/15 text-rose-200' : 'border-zinc-700 bg-zinc-900/40 text-zinc-400 hover:border-zinc-600'}`}
            >
              {p}
            </button>
          ))}
        </div>

        <p className="text-[10px] text-zinc-400 mb-1 mt-3 uppercase font-bold">Motivo <span className="text-zinc-600 normal-case">(opzionale)</span></p>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value.slice(0, 300))}
          rows={2}
          data-testid="ban-reason-input"
          placeholder="Spiega brevemente il motivo del ban…"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2.5 py-2 text-xs text-white focus:border-rose-500/50 outline-none resize-none"
        />

        <div className="flex items-center gap-2 mt-3">
          <button onClick={() => !busy && onCancel?.()} disabled={busy} className="flex-1 py-2.5 rounded-lg border border-zinc-700 bg-zinc-900/40 text-zinc-300 text-[11px] font-bold hover:bg-zinc-800">
            Annulla
          </button>
          <button
            onClick={() => onConfirm?.({ duration, reason })}
            disabled={busy || !duration.trim()}
            data-testid="ban-confirm-btn"
            className="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-rose-500 to-red-600 text-white text-[11px] font-bold hover:scale-[1.02] transition-transform disabled:opacity-50"
          >
            {busy ? 'Banno…' : 'Conferma Ban'}
          </button>
        </div>
        <p className="text-[8px] text-zinc-500 mt-3 text-center">Il counter dei ban non viene resettato dallo sblocco.</p>
      </div>
    </div>
  );
}
