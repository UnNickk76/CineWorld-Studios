import React from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';

const OUTCOME_CONFIG = {
  support_success: {
    image: '/assets/outcomes/supporto_successo.png',
    title: 'Supporto riuscito!',
    color: 'text-green-400',
    borderColor: 'border-green-500/30',
  },
  support_fail: {
    image: '/assets/outcomes/supporto_fallito.png',
    title: 'Supporto fallito...',
    color: 'text-orange-400',
    borderColor: 'border-orange-500/30',
  },
  boycott_success: {
    image: '/assets/outcomes/boicotto_successo.png',
    title: 'Boicotto riuscito!',
    color: 'text-red-400',
    borderColor: 'border-red-500/30',
  },
  boycott_fail: {
    image: '/assets/outcomes/boicotto_fallito.png',
    title: 'Boicotto fallito!',
    color: 'text-gray-400',
    borderColor: 'border-gray-500/30',
  },
  boycott_backfire: {
    image: '/assets/outcomes/boicotto_ritorto.png',
    title: 'Boicotto ritorto!',
    color: 'text-purple-400',
    borderColor: 'border-purple-500/30',
  },
};

export function getOutcomeType(action, outcome) {
  if (action === 'support' || action === 'hype') {
    return outcome === 'success' ? 'support_success' : 'support_fail';
  }
  // boycott
  if (outcome === 'success') return 'boycott_success';
  if (outcome === 'backfire') return 'boycott_backfire';
  return 'boycott_fail';
}

export function OutcomePopup({ open, onClose, outcomeType, title, message }) {
  const config = OUTCOME_CONFIG[outcomeType] || OUTCOME_CONFIG.support_success;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className={`bg-[#0A0A0B] border ${config.borderColor} max-w-xs p-0 overflow-hidden`} data-testid="outcome-popup">
        <div className="relative">
          <img src={config.image} alt={config.title} className="w-full aspect-square object-cover" />
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-[#0A0A0B] via-[#0A0A0B]/80 to-transparent p-3 pt-12">
            <h2 className={`font-['Bebas_Neue'] text-xl ${config.color}`}>{config.title}</h2>
            {title && <p className="text-sm font-semibold text-white mt-0.5">{title}</p>}
          </div>
        </div>
        <div className="px-4 pb-4 pt-1">
          {message && <p className="text-xs text-gray-400 mb-3">{message}</p>}
          <Button className="w-full h-9 text-sm bg-white/10 hover:bg-white/15 border border-white/10" onClick={onClose} data-testid="outcome-ok-btn">
            OK
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
