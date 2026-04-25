import React from 'react';

/**
 * ProducerBadge — piccola fascetta "DI [nickname]" mostrata sul poster
 * di un contenuto quando NON è del player corrente.
 * 
 * Props:
 *   producerNickname: string (es: "NeoMorpheus")
 *   producerId: string (user id del creatore)
 *   currentUserId: string (user id del player loggato)
 *   variant: 'top-left'|'top-right'|'bottom-left'|'bottom-right' (default: 'top-left')
 *   size: 'xs'|'sm' (default: 'xs')
 *   color: tailwind bg class (default auto-derivato dal nickname)
 */
const COLORS = [
  'bg-cyan-500/90',
  'bg-violet-500/90',
  'bg-rose-500/90',
  'bg-emerald-500/90',
  'bg-amber-500/90',
  'bg-fuchsia-500/90',
  'bg-sky-500/90',
  'bg-lime-500/90',
  'bg-orange-500/90',
];

function colorForName(name) {
  if (!name) return COLORS[0];
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) | 0;
  return COLORS[Math.abs(h) % COLORS.length];
}

const POS_MAP = {
  'top-left': 'top-0.5 left-0.5',
  'top-right': 'top-0.5 right-0.5',
  'bottom-left': 'bottom-0.5 left-0.5',
  'bottom-right': 'bottom-0.5 right-0.5',
};

const SIZE_MAP = {
  xs: 'text-[6px] px-1 py-[1px] leading-tight',
  sm: 'text-[8px] px-1.5 py-0.5 leading-tight',
};

export function ProducerBadge({
  producerNickname,
  producerId,
  currentUserId,
  variant = 'top-left',
  size = 'xs',
  color,
}) {
  // Mostra solo quando il contenuto NON è del player corrente
  if (!producerNickname) return null;
  if (producerId && currentUserId && producerId === currentUserId) return null;

  const bg = color || colorForName(producerNickname);
  const pos = POS_MAP[variant] || POS_MAP['top-left'];
  const sz = SIZE_MAP[size] || SIZE_MAP.xs;

  return (
    <div
      className={`absolute ${pos} ${bg} ${sz} rounded-sm text-white font-bold uppercase tracking-wider shadow-md backdrop-blur-sm pointer-events-none max-w-[80%] truncate`}
      data-testid={`producer-badge-${producerId || 'unknown'}`}
      title={`Di ${producerNickname}`}
    >
      DI {producerNickname}
    </div>
  );
}

export default ProducerBadge;
