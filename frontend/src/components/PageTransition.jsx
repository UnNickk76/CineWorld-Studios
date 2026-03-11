import React from 'react';
import { motion } from 'framer-motion';

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  enter: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 }
};

const pageTransition = {
  type: 'tween',
  ease: 'easeOut',
  duration: 0.2
};

export const PageTransition = ({ children, className = '' }) => (
  <motion.div
    initial="initial"
    animate="enter"
    exit="exit"
    variants={pageVariants}
    transition={pageTransition}
    className={className}
  >
    {children}
  </motion.div>
);

export const PageSkeleton = ({ rows = 6, cards = false }) => (
  <div className="animate-pulse space-y-4 p-4 max-w-4xl mx-auto">
    {/* Header skeleton */}
    <div className="h-8 bg-white/5 rounded-lg w-48" />
    <div className="h-4 bg-white/5 rounded w-32" />
    
    {cards ? (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-32 bg-white/5 rounded-lg" />
        ))}
      </div>
    ) : (
      <div className="space-y-3 mt-4">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-3 items-center">
            <div className="w-10 h-10 rounded-full bg-white/5 flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-white/5 rounded w-3/4" />
              <div className="h-3 bg-white/5 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);

export default PageTransition;
