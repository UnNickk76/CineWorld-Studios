import React, { useContext } from 'react';
import { LanguageContext } from '../contexts';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Ticket, AlertTriangle } from 'lucide-react';

const CinePassConfirmDialog = ({ open, onClose, onConfirm, cost, actionName, loading, userBalance }) => {
  const { language } = useContext(LanguageContext);
  const canAfford = (userBalance ?? 0) >= cost;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#141416] border-gray-800 text-white max-w-xs" data-testid="cinepass-confirm-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <Ticket className="w-5 h-5 text-cyan-400" />
            Conferma CinePass
          </DialogTitle>
          <DialogDescription className="text-gray-400 text-sm">
            {actionName}
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-between p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/20">
          <span className="text-sm text-gray-300">{language === 'it' ? 'Costo' : 'Cost'}</span>
          <span className="text-lg font-bold text-cyan-400 flex items-center gap-1">
            <Ticket className="w-4 h-4" /> {cost}
          </span>
        </div>

        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>{language === 'it' ? 'Il tuo saldo' : 'Your balance'}</span>
          <span className={canAfford ? 'text-green-400' : 'text-red-400'}>{userBalance ?? 0} CinePass</span>
        </div>

        {!canAfford && (
          <div className="flex items-center gap-2 p-2 bg-red-500/10 rounded border border-red-500/20">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span className="text-xs text-red-400">{language === 'it' ? 'CinePass insufficienti!' : 'Not enough CinePass!'}</span>
          </div>
        )}

        <div className="flex gap-2 mt-1">
          <Button variant="outline" onClick={() => onClose(false)} className="flex-1 border-gray-700 text-gray-300">
            {language === 'it' ? 'Annulla' : 'Cancel'}
          </Button>
          <Button
            disabled={!canAfford || loading}
            onClick={onConfirm}
            className="flex-1 bg-cyan-700 hover:bg-cyan-800 font-bold"
            data-testid="cinepass-confirm-btn"
          >
            {loading ? '...' : language === 'it' ? 'Conferma' : 'Confirm'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CinePassConfirmDialog;
