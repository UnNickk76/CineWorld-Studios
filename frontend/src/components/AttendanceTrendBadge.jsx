import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * Compact attendance trend badge — shown over film posters or next to
 * the "AL CINEMA" label. Only renders when the film is in_theaters.
 * Props:
 *   - trend: 'up' | 'down' | 'flat' | null
 *   - status: film.status (will render only for 'in_theaters')
 *   - size: 'xs' | 'sm' (default 'xs')
 */
export const AttendanceTrendBadge = ({ trend, status, size = 'xs', className = '' }) => {
  if (status !== 'in_theaters') return null;
  const t = trend || 'flat';
  const px = size === 'sm' ? 'w-5 h-5' : 'w-4 h-4';
  const ic = size === 'sm' ? 'w-3 h-3' : 'w-2.5 h-2.5';
  let Icon = Minus;
  let bg = 'bg-gray-500/80';
  let ring = 'ring-gray-400/40';
  let pulse = '';
  if (t === 'up') {
    Icon = TrendingUp;
    bg = 'bg-emerald-500';
    ring = 'ring-emerald-300/60 shadow-[0_0_8px_rgba(16,185,129,0.75)]';
    pulse = 'animate-pulse';
  } else if (t === 'down') {
    Icon = TrendingDown;
    bg = 'bg-rose-500';
    ring = 'ring-rose-300/60 shadow-[0_0_8px_rgba(244,63,94,0.75)]';
    pulse = 'animate-pulse';
  }
  return (
    <span
      className={`inline-flex items-center justify-center rounded ${px} ${bg} ${ring} ${pulse} ring-1 ${className}`}
      data-testid={`attendance-trend-${t}`}
      title={t === 'up' ? 'Affluenza in crescita' : t === 'down' ? 'Affluenza in calo' : 'Affluenza stabile'}
    >
      <Icon className={`${ic} text-white`} strokeWidth={3} />
    </span>
  );
};

export default AttendanceTrendBadge;
