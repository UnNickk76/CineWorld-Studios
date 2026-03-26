import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

const OUTCOME_CONFIG = {
  support_success: {
    image: '/assets/outcomes/supporto_successo.png',
    title: 'Supporto riuscito!',
    color: 'text-green-400',
    borderColor: 'border-green-500/40',
    glow: 'shadow-green-500/20',
  },
  support_fail: {
    image: '/assets/outcomes/supporto_fallito.png',
    title: 'Supporto fallito...',
    color: 'text-orange-400',
    borderColor: 'border-orange-500/40',
    glow: 'shadow-orange-500/20',
  },
  boycott_success: {
    image: '/assets/outcomes/boicotto_successo.png',
    title: 'Boicotto riuscito!',
    color: 'text-red-400',
    borderColor: 'border-red-500/40',
    glow: 'shadow-red-500/20',
  },
  boycott_fail: {
    image: '/assets/outcomes/boicotto_fallito.png',
    title: 'Boicotto fallito!',
    color: 'text-gray-400',
    borderColor: 'border-gray-500/40',
    glow: 'shadow-gray-500/20',
  },
  boycott_backfire: {
    image: '/assets/outcomes/boicotto_ritorto.png',
    title: 'Boicotto ritorto!',
    color: 'text-purple-400',
    borderColor: 'border-purple-500/40',
    glow: 'shadow-purple-500/20',
  },
};

export function getOutcomeType(action, outcome) {
  if (action === 'support' || action === 'hype') {
    return outcome === 'success' ? 'support_success' : 'support_fail';
  }
  if (outcome === 'success') return 'boycott_success';
  if (outcome === 'backfire') return 'boycott_backfire';
  return 'boycott_fail';
}

/** Determine outcome string from API response + action category */
export function parseOutcome(category, data) {
  if (category === 'boycott' && data.boycott_success === false) return 'backfire';
  if (data.success || data.boycott_success) return 'success';
  return 'fail';
}

export function OutcomePopup({ open, onClose, outcomeType, title, message }) {
  const config = OUTCOME_CONFIG[outcomeType] || OUTCOME_CONFIG.support_success;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 flex items-center justify-center"
          style={{ zIndex: 9999 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          data-testid="outcome-popup-overlay"
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
          {/* Card */}
          <motion.div
            className={`relative w-[280px] max-w-[90vw] rounded-2xl overflow-hidden border ${config.borderColor} bg-[#0A0A0B] shadow-2xl ${config.glow}`}
            initial={{ scale: 0.7, opacity: 0, y: 30 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            data-testid="outcome-popup"
          >
            {/* Close btn */}
            <button
              onClick={onClose}
              className="absolute top-2 right-2 z-10 w-6 h-6 rounded-full bg-black/60 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
              data-testid="outcome-close-btn"
            >
              <X className="w-3.5 h-3.5" />
            </button>

            {/* Image */}
            <img src={config.image} alt={config.title} className="w-full aspect-square object-cover" />

            {/* Gradient text overlay */}
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-[#0A0A0B] via-[#0A0A0B]/80 to-transparent p-3 pt-16">
              <h2 className={`font-['Bebas_Neue'] text-xl ${config.color}`}>{config.title}</h2>
              {title && <p className="text-sm font-semibold text-white mt-0.5">{title}</p>}
            </div>

            {/* Bottom section */}
            <div className="px-4 pb-4 pt-1">
              {message && <p className="text-xs text-gray-400 mb-3">{message}</p>}
              <button
                className="w-full h-9 text-sm rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 text-white font-medium transition-colors"
                onClick={onClose}
                data-testid="outcome-ok-btn"
              >
                OK
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
