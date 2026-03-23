import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const VELION_SIZE = 80;

export const VelionOverlay = ({ onClick }) => {
  const [hovered, setHovered] = useState(false);

  return (
    <motion.button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="fixed bottom-20 right-2 z-50 sm:bottom-6 sm:right-5 cursor-pointer"
      style={{ width: VELION_SIZE, height: VELION_SIZE }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 260, damping: 20, delay: 1.5 }}
      whileHover={{ scale: 1.15 }}
      whileTap={{ scale: 0.9 }}
      data-testid="velion-overlay"
      title="Tutorial"
    >
      {/* Background circle for visibility */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(0,30,60,0.85) 40%, rgba(0,20,50,0.5) 70%, transparent 100%)',
        }}
      />
      {/* Animated glow ring */}
      <motion.div
        className="absolute inset-[-4px] rounded-full"
        style={{
          background: 'conic-gradient(from 0deg, rgba(0,180,255,0.4), rgba(0,100,255,0.1), rgba(0,180,255,0.4))',
          filter: 'blur(3px)',
        }}
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 6, ease: 'linear' }}
      />
      {/* Character image */}
      <img
        src="/velion.png"
        alt="Velion"
        className="w-full h-full object-contain rounded-full relative z-10 pointer-events-none"
        style={{
          mixBlendMode: 'screen',
          filter: 'brightness(1.4) contrast(1.3) saturate(1.2)',
        }}
      />
      {/* Pulsing notification dot */}
      <AnimatePresence>
        {!hovered && (
          <motion.div
            className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full z-20 border-2 border-[#0a0a0b]"
            style={{ background: 'linear-gradient(135deg, #00ddff, #0088ff)' }}
            animate={{ scale: [1, 1.25, 1], opacity: [1, 0.8, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            exit={{ scale: 0, opacity: 0 }}
          />
        )}
      </AnimatePresence>
      {/* Tooltip on hover */}
      <AnimatePresence>
        {hovered && (
          <motion.div
            initial={{ opacity: 0, x: 8, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 8, scale: 0.9 }}
            transition={{ duration: 0.15 }}
            className="absolute right-full mr-2 top-1/2 -translate-y-1/2 whitespace-nowrap bg-[#0d1117]/95 border border-cyan-500/40 text-cyan-300 text-[11px] px-2.5 py-1.5 rounded-lg font-['Bebas_Neue'] tracking-widest shadow-lg shadow-cyan-500/10"
          >
            Chiedi a Velion
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
};
