import React from 'react';
import { motion } from 'framer-motion';

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  enter: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 }
};

const pageTransition = {
  type: 'tween',
  ease: [0.25, 0.46, 0.45, 0.94], // Custom easing for smoother feel
  duration: 0.25
};

export const PageTransition = ({ children, className = '' }) => (
  <motion.div
    initial="initial"
    animate="enter"
    exit="exit"
    variants={pageVariants}
    transition={pageTransition}
    className={className}
    style={{ willChange: 'transform, opacity' }} // GPU acceleration
  >
    {children}
  </motion.div>
);

// Shimmer skeleton component for better loading UX
const ShimmerBar = ({ className }) => (
  <div className={`skeleton-shimmer rounded ${className}`} />
);

export const PageSkeleton = ({ rows = 6, cards = false }) => (
  <div className="space-y-4 p-4 max-w-4xl mx-auto">
    {/* Header skeleton with shimmer */}
    <ShimmerBar className="h-8 w-48" />
    <ShimmerBar className="h-4 w-32" />
    
    {cards ? (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <ShimmerBar key={i} className="h-32" style={{ animationDelay: `${i * 0.1}s` }} />
        ))}
      </div>
    ) : (
      <div className="space-y-3 mt-4">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-3 items-center" style={{ animationDelay: `${i * 0.05}s` }}>
            <ShimmerBar className="w-10 h-10 rounded-full flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <ShimmerBar className="h-4 w-3/4" />
              <ShimmerBar className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);

export default PageTransition;
