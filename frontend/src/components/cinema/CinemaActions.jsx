// CineWorld Studio's — CinemaActions
// Bottoni Ritira / Prolunga visibili solo per il proprietario.
// Apre i modali di conferma Cineox/Velion-style.

import React, { useState } from 'react';
import { Pause, Plus, Lock } from 'lucide-react';
import { Button } from '../ui/button';
import { ExtendConfirmModal } from './ExtendConfirmModal';
import { WithdrawConfirmModal } from './WithdrawConfirmModal';

export const CinemaActions = ({ stats, onActionDone, isOwner }) => {
  const [showExtend, setShowExtend] = useState(false);
  const [showWithdraw, setShowWithdraw] = useState(false);

  if (!isOwner) {
    return (
      <div className="text-center text-[10px] text-zinc-600 italic flex items-center justify-center gap-1 mt-1">
        <Lock className="w-3 h-3" /> Le azioni cinema sono disponibili solo al proprietario
      </div>
    );
  }

  const ext = stats?.actions?.extend;
  const wit = stats?.actions?.withdraw;

  return (
    <div className="space-y-2" data-testid="cinema-actions">
      <div className="grid grid-cols-2 gap-2">
        <Button
          onClick={() => setShowExtend(true)}
          disabled={!ext?.available}
          variant="outline"
          className={`h-10 text-xs font-bold ${
            ext?.available
              ? 'border-emerald-700/50 bg-emerald-950/30 text-emerald-200 hover:bg-emerald-900/40'
              : 'border-zinc-800 text-zinc-600'
          }`}
          data-testid="cinema-extend-btn"
        >
          <Plus className="w-3.5 h-3.5 mr-1" />
          Prolunga
        </Button>
        <Button
          onClick={() => setShowWithdraw(true)}
          disabled={!wit?.available}
          variant="outline"
          className={`h-10 text-xs font-bold ${
            wit?.available
              ? 'border-rose-700/50 bg-rose-950/30 text-rose-200 hover:bg-rose-900/40'
              : 'border-zinc-800 text-zinc-600'
          }`}
          data-testid="cinema-withdraw-btn"
        >
          <Pause className="w-3.5 h-3.5 mr-1" />
          Ritira
        </Button>
      </div>

      {/* Tooltip-style explanation */}
      {!ext?.available && ext?.reason && (
        <div className="text-[10px] text-zinc-500 italic">
          ⓘ {ext.reason}
        </div>
      )}

      {showExtend && ext?.available && (
        <ExtendConfirmModal
          stats={stats}
          onClose={() => setShowExtend(false)}
          onSuccess={() => {
            setShowExtend(false);
            onActionDone?.('extend');
          }}
        />
      )}
      {showWithdraw && wit?.available && (
        <WithdrawConfirmModal
          stats={stats}
          onClose={() => setShowWithdraw(false)}
          onSuccess={() => {
            setShowWithdraw(false);
            onActionDone?.('withdraw');
          }}
        />
      )}
    </div>
  );
};

export default CinemaActions;
