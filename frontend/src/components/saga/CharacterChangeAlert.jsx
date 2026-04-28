// CineWorld Studio's — CharacterChangeAlert
// Alert mostrato quando l'AI introduce nuovi personaggi o ne rimuove
// rispetto al capitolo precedente di una saga.
// Attivato durante la fase Casting di un capitolo > 1.

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserPlus, UserMinus, Users, AlertTriangle } from 'lucide-react';

export const CharacterChangeAlert = ({ added = [], removed = [], onDismiss }) => {
  const hasChanges = (added && added.length > 0) || (removed && removed.length > 0);
  if (!hasChanges) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        className="rounded-xl border border-cyan-700/50 bg-cyan-950/40 p-3.5 mb-3"
        data-testid="character-change-alert"
      >
        <div className="flex items-center gap-2 mb-2">
          <Users className="w-4 h-4 text-cyan-300" />
          <span className="text-sm font-bold text-cyan-200">
            Cast evoluto per il nuovo capitolo
          </span>
        </div>

        {added && added.length > 0 && (
          <div className="mb-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-300 mb-1">
              <UserPlus className="w-3.5 h-3.5" />
              Nuovi personaggi ({added.length}) — Devi assegnare un attore
            </div>
            <ul className="space-y-1 pl-5">
              {added.map((c, i) => (
                <li key={c.id || c.name || i} className="text-[11px] text-zinc-300 leading-tight" data-testid={`saga-char-added-${i}`}>
                  <span className="font-bold text-emerald-200">{c.name}</span>{' '}
                  <span className="text-zinc-500">({c.role_type}, {c.age}{c.gender})</span>
                  {c.description && <span className="text-zinc-400"> — {c.description}</span>}
                </li>
              ))}
            </ul>
          </div>
        )}

        {removed && removed.length > 0 && (
          <div className="mb-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-300 mb-1">
              <UserMinus className="w-3.5 h-3.5" />
              Personaggi usciti di scena ({removed.length}) — Attori rimossi automaticamente
            </div>
            <ul className="space-y-0.5 pl-5">
              {removed.map((name, i) => (
                <li key={name || i} className="text-[11px] text-rose-200/80 line-through" data-testid={`saga-char-removed-${i}`}>
                  {name}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex items-start gap-1.5 mt-2 text-[10px] text-amber-300/80">
          <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
          <span>
            I personaggi principali (protagonist/antagonist/coprotagonist) sono mantenuti.
            Le modifiche derivano dalla nuova pretrama AI coerente con i capitoli precedenti.
          </span>
        </div>

        {onDismiss && (
          <button
            onClick={onDismiss}
            className="mt-2 text-[11px] text-cyan-400 hover:text-cyan-300 underline"
            data-testid="saga-char-alert-dismiss"
          >
            Ho capito, procedi al casting
          </button>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default CharacterChangeAlert;
