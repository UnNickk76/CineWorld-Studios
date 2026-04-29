import React from 'react';
import { Award } from 'lucide-react';

/**
 * VeteranBadge — calcola il tier di anzianità dal `created_at`.
 * Tier:
 *   >= 365gg → Gold (Veterano Leggendario)
 *   >= 180gg → Silver (Veterano)
 *   >=  90gg → Bronze (Veterano in Erba)
 *   <   90gg → nessun badge
 */
export function getVeteranTier(createdAt) {
  if (!createdAt) return null;
  try {
    const dt = new Date(createdAt);
    if (Number.isNaN(dt.getTime())) return null;
    const days = Math.floor((Date.now() - dt.getTime()) / 86400000);
    if (days >= 365) return { tier: 'gold', label: 'Veterano Leggendario', days, color: '#facc15', bg: 'rgba(250,204,21,0.15)', border: 'rgba(250,204,21,0.45)', glow: '0 0 14px rgba(250,204,21,0.35)' };
    if (days >= 180) return { tier: 'silver', label: 'Veterano', days, color: '#cbd5e1', bg: 'rgba(203,213,225,0.12)', border: 'rgba(203,213,225,0.4)', glow: '0 0 10px rgba(203,213,225,0.25)' };
    if (days >= 90) return { tier: 'bronze', label: 'Veterano in Erba', days, color: '#fb923c', bg: 'rgba(251,146,60,0.12)', border: 'rgba(251,146,60,0.4)', glow: '0 0 10px rgba(251,146,60,0.25)' };
    return null;
  } catch { return null; }
}

export default function VeteranBadge({ createdAt, size = 'md', showLabel = true }) {
  const t = getVeteranTier(createdAt);
  if (!t) return null;
  const px = size === 'sm' ? 'px-1.5 py-0.5 text-[8px]' : size === 'lg' ? 'px-2.5 py-1 text-xs' : 'px-2 py-0.5 text-[10px]';
  const iconSize = size === 'sm' ? 9 : size === 'lg' ? 14 : 11;
  return (
    <span
      data-testid={`veteran-badge-${t.tier}`}
      title={`${t.label} · iscritto da ${t.days} giorni`}
      className={`inline-flex items-center gap-1 rounded-full font-bold uppercase tracking-wider whitespace-nowrap ${px}`}
      style={{
        color: t.color,
        backgroundColor: t.bg,
        borderColor: t.border,
        borderWidth: 1,
        borderStyle: 'solid',
        boxShadow: t.glow,
      }}
    >
      <Award size={iconSize} strokeWidth={2.5} />
      {showLabel && <span>{t.label}</span>}
    </span>
  );
}
