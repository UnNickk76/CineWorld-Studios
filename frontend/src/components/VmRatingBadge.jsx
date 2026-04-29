import React from 'react';

/**
 * Badge classificazione minori (VM14/VM16/VM18).
 * Mostra un piccolo bollino rosso/arancio sulla locandina o card.
 *
 * Props:
 *  - rating: 'vm14' | 'vm16' | 'vm18' | null/undefined
 *  - size: 'xs' | 'sm' | 'md' (default 'sm')
 *  - className: extra classes
 */
const COLORS = {
  vm14: { bg: 'bg-yellow-500', text: 'text-black', label: 'VM 14' },
  vm16: { bg: 'bg-orange-500', text: 'text-black', label: 'VM 16' },
  vm18: { bg: 'bg-red-600',    text: 'text-white', label: 'VM 18' },
};

const SIZES = {
  xs: 'text-[6px] px-1 py-0.5',
  sm: 'text-[8px] px-1.5 py-0.5',
  md: 'text-[10px] px-2 py-1',
};

export const VmRatingBadge = ({ rating, size = 'sm', className = '' }) => {
  if (!rating || !COLORS[rating]) return null;
  const c = COLORS[rating];
  const s = SIZES[size] || SIZES.sm;
  return (
    <span
      className={`inline-flex items-center justify-center rounded font-black uppercase tracking-wider border border-black/30 shadow-sm ${c.bg} ${c.text} ${s} ${className}`}
      data-testid={`vm-badge-${rating}`}
      title={`Classificazione: ${c.label}`}
    >
      {c.label}
    </span>
  );
};

export default VmRatingBadge;
