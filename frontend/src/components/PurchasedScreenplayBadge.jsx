import React from 'react';
import { BookOpen } from 'lucide-react';

/**
 * Small overlay badge on film poster cards to indicate the film was
 * created from a purchased/ready-made screenplay (emerging or agency).
 *
 * Usage:
 *   {film?.from_purchased_screenplay && (
 *     <PurchasedScreenplayBadge mode={film.purchased_screenplay_mode}
 *                               source={film.purchased_screenplay_source} />
 *   )}
 */
export function PurchasedScreenplayBadge({ mode, source, size = 'md', className = '' }) {
  const sz = size === 'sm' ? 'w-5 h-5' : size === 'lg' ? 'w-7 h-7' : 'w-6 h-6';
  const icon = size === 'sm' ? 'w-2.5 h-2.5' : size === 'lg' ? 'w-4 h-4' : 'w-3 h-3';
  const color = mode === 'veloce' ? 'bg-orange-500/90 border-orange-300/50' : 'bg-emerald-500/90 border-emerald-300/50';
  const title = source === 'agency'
    ? `Da Scout Agenzia (${mode || 'pronta'})`
    : `Da Sceneggiatore Emergente (${mode || 'pronta'})`;
  return (
    <div
      className={`absolute top-1 left-1 ${sz} rounded-full ${color} border flex items-center justify-center shadow-md backdrop-blur-sm ${className}`}
      title={title}
      data-testid="purchased-screenplay-badge"
    >
      <BookOpen className={`${icon} text-white`} strokeWidth={2.5} />
    </div>
  );
}

export default PurchasedScreenplayBadge;
