import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { X } from 'lucide-react';

const ConfirmContext = createContext(null);

export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error('useConfirm must be inside ConfirmProvider');
  return ctx.confirm;
}

export function ConfirmProvider({ children }) {
  const [state, setState] = useState(null);
  const resolveRef = useRef(null);

  const confirm = useCallback(({ title, subtitle, confirmLabel = 'Conferma', confirmIcon = null, cancelLabel = 'Annulla' }) => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setState({ title, subtitle, confirmLabel, confirmIcon, cancelLabel });
    });
  }, []);

  const handleConfirm = () => {
    resolveRef.current?.(true);
    setState(null);
  };

  const handleCancel = () => {
    resolveRef.current?.(false);
    setState(null);
  };

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      <Dialog open={!!state} onOpenChange={(open) => { if (!open) handleCancel(); }}>
        <DialogContent
          className="bg-transparent border-0 shadow-none p-0 max-w-[380px] mx-auto [&>button]:hidden"
          data-testid="game-confirm-dialog"
        >
          <div className="relative">
            {/* Glow border */}
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-yellow-500/20 via-amber-500/10 to-yellow-500/20 blur-sm" />
            
            {/* Main container */}
            <div className="relative bg-[#1A1A1C]/95 backdrop-blur-xl rounded-2xl border border-yellow-500/20 overflow-hidden">
              {/* Mascots + Text */}
              <div className="flex items-center gap-2 px-3 pt-4 pb-3">
                {/* Velion left */}
                <div className="w-14 h-14 flex-shrink-0">
                  <img
                    src="/assets/characters/velion.png"
                    alt=""
                    className="w-full h-full object-contain drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]"
                  />
                </div>

                {/* Text center */}
                <div className="flex-1 text-center min-w-0 px-1">
                  <h3 className="text-sm font-bold text-yellow-400 leading-tight">
                    {state?.title}
                  </h3>
                  {state?.subtitle && (
                    <p className="text-[11px] text-gray-400 mt-1 leading-snug">
                      {state.subtitle}
                    </p>
                  )}
                </div>

                {/* CineOx right */}
                <div className="w-14 h-14 flex-shrink-0">
                  <img
                    src="/assets/characters/cineox.png"
                    alt=""
                    className="w-full h-full object-contain drop-shadow-[0_0_8px_rgba(234,179,8,0.4)]"
                  />
                </div>
              </div>

              {/* Buttons */}
              <div className="flex gap-2.5 px-3 pb-4">
                <Button
                  variant="outline"
                  className="flex-1 h-10 rounded-xl bg-[#2A2A3C]/80 border-white/10 hover:bg-[#3A3A4C] text-gray-300 text-sm font-medium"
                  onClick={handleCancel}
                  data-testid="confirm-cancel-btn"
                >
                  {state?.cancelLabel || 'Annulla'}
                </Button>
                <Button
                  className="flex-1 h-10 rounded-xl bg-gradient-to-r from-yellow-500 to-amber-500 hover:from-yellow-400 hover:to-amber-400 text-black text-sm font-bold border-0"
                  onClick={handleConfirm}
                  data-testid="confirm-action-btn"
                >
                  {state?.confirmIcon && <span className="mr-1.5">{state.confirmIcon}</span>}
                  {state?.confirmLabel || 'Conferma'}
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </ConfirmContext.Provider>
  );
}
