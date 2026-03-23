import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { Button } from './ui/button';

const LS_KEY = 'velion_login_bubble_seen';

export function VelionLoginBubble({ onStart }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (localStorage.getItem(LS_KEY)) return;
    const timer = setTimeout(() => setShow(true), 1200);
    return () => clearTimeout(timer);
  }, []);

  const handleClose = () => {
    setShow(false);
    localStorage.setItem(LS_KEY, 'true');
  };

  const handleStart = () => {
    handleClose();
    onStart?.();
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ type: 'spring', damping: 22, stiffness: 280 }}
          className="fixed bottom-4 right-4 left-4 sm:left-auto sm:right-6 sm:bottom-6 sm:w-[360px] z-50"
          data-testid="velion-login-bubble"
        >
          <div
            className="rounded-2xl border border-cyan-500/20 overflow-hidden"
            style={{ background: 'linear-gradient(180deg, #0d0d10 0%, #111115 100%)', boxShadow: '0 0 50px rgba(0,200,255,0.06)' }}
          >
            {/* Close button */}
            <button
              onClick={handleClose}
              className="absolute top-3 right-3 z-10 p-1 rounded-lg hover:bg-white/10 transition-colors"
              data-testid="velion-login-bubble-close"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>

            {/* Header with Velion avatar */}
            <div className="flex items-center gap-3 px-4 pt-4 pb-2">
              <div className="w-12 h-12 rounded-full relative flex-shrink-0">
                <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, transparent 100%)' }} />
                <motion.div
                  className="absolute inset-[-2px] rounded-full"
                  style={{ background: 'conic-gradient(from 0deg, rgba(0,180,255,0.4), rgba(0,100,255,0.1), rgba(0,180,255,0.4))', filter: 'blur(3px)' }}
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 6, ease: 'linear' }}
                />
                <img
                  src="/velion.png"
                  alt="Velion"
                  className="w-full h-full object-contain rounded-full relative z-10"
                  style={{ mixBlendMode: 'screen', filter: 'brightness(1.4) contrast(1.3) saturate(1.2)' }}
                />
              </div>
              <div>
                <span className="text-[10px] text-cyan-400 font-['Bebas_Neue'] tracking-widest">VELION</span>
                <p className="text-[10px] text-gray-600">Il tuo assistente</p>
              </div>
            </div>

            {/* Message content */}
            <div className="px-4 pb-3">
              <div className="bg-white/[0.03] border border-white/5 rounded-xl px-3.5 py-3 relative">
                <div className="absolute -top-1.5 left-8 w-3 h-3 bg-white/[0.03] border-l border-t border-white/5 rotate-45" />
                <p className="text-[13px] text-gray-300 leading-relaxed">
                  <span className="text-white font-semibold">Benvenuto in CineWorld Studio's.</span>
                  <br />Qui non crei solo film… costruisci un impero.
                </p>
                <p className="text-[13px] text-gray-300 leading-relaxed mt-2">
                  È il primo browser game sul cinema con PvP: puoi competere contro altri produttori e diventare il migliore.
                </p>
                <p className="text-[12px] text-gray-500 leading-relaxed mt-2 italic">
                  Siamo ancora in sviluppo: potrebbero esserci bug o sistemi da perfezionare.
                  <br />Ed è proprio qui che entri in gioco tu.
                </p>
                <p className="text-[13px] text-cyan-400/80 leading-relaxed mt-2 font-medium">
                  Aiutaci a migliorare… divertendoti.
                </p>
              </div>
            </div>

            {/* CTA */}
            <div className="px-4 pb-4">
              <Button
                onClick={handleStart}
                className="w-full bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-400 border border-cyan-500/30 rounded-xl h-10 text-sm font-medium"
                data-testid="velion-login-start-btn"
              >
                Inizia ora
              </Button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
