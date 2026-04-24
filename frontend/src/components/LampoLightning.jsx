import React from 'react';
import { Zap } from 'lucide-react';

/**
 * LampoLightning — icona ⚡ lampeggiante/glow per marcare i contenuti
 * prodotti in modalità LAMPO.
 *
 * Props:
 *   visible: boolean (default: checks item.is_lampo OR item.mode === 'lampo')
 *   item: content document (optional, to auto-detect)
 *   variant: 'top-left'|'top-right'|'bottom-left'|'bottom-right' (default 'top-right')
 *   size: 'xs'|'sm'|'md' (default 'sm')
 */
const POS = {
  'top-left': 'top-1 left-1',
  'top-right': 'top-1 right-1',
  'bottom-left': 'bottom-1 left-1',
  'bottom-right': 'bottom-1 right-1',
};

const SIZE = {
  xs: { wrap: 'w-3.5 h-3.5', icon: 'w-2 h-2' },
  sm: { wrap: 'w-5 h-5', icon: 'w-3 h-3' },
  md: { wrap: 'w-7 h-7', icon: 'w-4 h-4' },
};

export function LampoLightning({ visible, item, variant = 'top-right', size = 'sm' }) {
  const isLampo = visible != null ? !!visible : (item?.is_lampo === true || item?.mode === 'lampo');
  if (!isLampo) return null;
  const pos = POS[variant] || POS['top-right'];
  const sz = SIZE[size] || SIZE.sm;
  return (
    <div
      className={`absolute ${pos} z-30 ${sz.wrap} rounded-full flex items-center justify-center pointer-events-none lampo-bolt`}
      title="Prodotto LAMPO"
      data-testid="lampo-lightning-badge"
    >
      <div className="absolute inset-0 rounded-full bg-amber-400/30 animate-ping" />
      <div className="absolute inset-0 rounded-full bg-gradient-to-br from-amber-300 to-orange-500 shadow-[0_0_8px_rgba(251,191,36,0.8)]" />
      <Zap className={`relative ${sz.icon} text-yellow-900 fill-yellow-100`} strokeWidth={3} />
    </div>
  );
}

export default LampoLightning;
