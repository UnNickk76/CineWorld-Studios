import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

const VELION_SIZE = 72;
const LS_KEY = 'velion_visible';

export const VelionOverlay = ({ onClick, onDismiss }) => {
  const [hovered, setHovered] = useState(false);
  const [visible, setVisible] = useState(() => {
    const saved = localStorage.getItem(LS_KEY);
    return saved === null ? true : saved === 'true';
  });

  useEffect(() => {
    localStorage.setItem(LS_KEY, String(visible));
  }, [visible]);

  const handleDismiss = (e) => {
    e.stopPropagation();
    setVisible(false);
    onDismiss?.();
  };

  // Allow parent to show again
  useEffect(() => {
    const handler = () => setVisible(true);
    window.addEventListener('velion-show', handler);
    return () => window.removeEventListener('velion-show', handler);
  }, []);

  if (!visible) return null;

  return (
    <motion.div
      className="fixed bottom-20 right-2 z-50 sm:bottom-6 sm:right-5"
      style={{ width: VELION_SIZE, height: VELION_SIZE }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 20, delay: 1 }}
    >
      {/* Dismiss X */}
      <button
        onClick={handleDismiss}
        className="absolute -top-2 -left-2 z-30 w-5 h-5 rounded-full bg-gray-800 border border-gray-600 flex items-center justify-center hover:bg-red-600 hover:border-red-500 transition-colors"
        data-testid="velion-dismiss"
      >
        <X className="w-3 h-3 text-gray-300" />
      </button>

      {/* Clickable area */}
      <motion.button
        onClick={onClick}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        className="w-full h-full cursor-pointer relative"
        whileHover={{ scale: 1.12 }}
        whileTap={{ scale: 0.9 }}
        data-testid="velion-overlay"
        title="Tutorial"
      >
        <div
          className="absolute inset-0 rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, rgba(0,20,50,0.5) 70%, transparent 100%)' }}
        />
        <motion.div
          className="absolute inset-[-3px] rounded-full"
          style={{ background: 'conic-gradient(from 0deg, rgba(0,180,255,0.4), rgba(0,100,255,0.1), rgba(0,180,255,0.4))', filter: 'blur(3px)' }}
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 6, ease: 'linear' }}
        />
        <img
          src="/velion.png"
          alt="Velion"
          className="w-full h-full object-contain rounded-full relative z-10 pointer-events-none"
          style={{ mixBlendMode: 'screen', filter: 'brightness(1.4) contrast(1.3) saturate(1.2)' }}
        />
        <AnimatePresence>
          {!hovered && (
            <motion.div
              className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full z-20 border-2 border-[#0a0a0b]"
              style={{ background: 'linear-gradient(135deg, #00ddff, #0088ff)' }}
              animate={{ scale: [1, 1.25, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              exit={{ scale: 0, opacity: 0 }}
            />
          )}
        </AnimatePresence>
        <AnimatePresence>
          {hovered && (
            <motion.div
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 8 }}
              className="absolute right-full mr-2 top-1/2 -translate-y-1/2 whitespace-nowrap bg-[#0d1117]/95 border border-cyan-500/40 text-cyan-300 text-[11px] px-2.5 py-1.5 rounded-lg font-['Bebas_Neue'] tracking-widest"
            >
              Chiedi a Velion
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </motion.div>
  );
};
