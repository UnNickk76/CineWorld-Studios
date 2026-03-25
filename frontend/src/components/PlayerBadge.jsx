// PlayerBadge - Shows badge icons before player name
// Supports: cineadmin (permanent), cinemod (permanent), cinestar (timed), cinevip (timed)
// Usage: <PlayerBadge badge={user.badge} badgeExpiry={user.badge_expiry} badges={user.badges} />

import React from 'react';
import { Crown, Star, Shield, ShieldCheck } from 'lucide-react';

// Priority order: cineadmin > cinemod > cinestar > cinevip
const BADGE_CONFIG = {
  cineadmin: { icon: Shield, color: 'text-red-400', glow: 'drop-shadow-[0_0_5px_rgba(248,113,113,0.7)]', label: 'CineADMIN', permanent: true },
  cinemod:   { icon: ShieldCheck, color: 'text-blue-400', glow: 'drop-shadow-[0_0_5px_rgba(96,165,250,0.7)]', label: 'CineMOD', permanent: true },
  cinestar:  { icon: Star, color: 'text-amber-300', glow: 'drop-shadow-[0_0_5px_rgba(252,211,77,0.7)]', label: 'CineSTAR', permanent: false },
  cinevip:   { icon: Crown, color: 'text-yellow-400', glow: 'drop-shadow-[0_0_4px_rgba(250,204,21,0.6)]', label: 'CineVIP', permanent: false },
};
const BADGE_ORDER = ['cineadmin', 'cinemod', 'cinestar', 'cinevip'];

function getActiveBadges(badge, badgeExpiry, badges) {
  const active = [];
  // Check permanent badges from 'badges' field
  if (badges) {
    if (badges.cineadmin) active.push('cineadmin');
    if (badges.cinemod) active.push('cinemod');
  }
  // Check timed badge (legacy field)
  if (badge && badge !== 'none' && badgeExpiry && new Date(badgeExpiry) > new Date()) {
    if (!active.includes(badge)) active.push(badge);
  }
  // Sort by priority
  return active.sort((a, b) => BADGE_ORDER.indexOf(a) - BADGE_ORDER.indexOf(b));
}

export function PlayerBadge({ badge, badgeExpiry, badges, size = 'sm', inline = false, maxBadges = 2 }) {
  const active = getActiveBadges(badge, badgeExpiry, badges);
  if (active.length === 0) return null;

  const sizes = { xs: 'w-3 h-3', sm: 'w-3.5 h-3.5', md: 'w-4 h-4', lg: 'w-5 h-5' };
  const iconClass = sizes[size] || sizes.sm;
  const gap = inline ? 'mr-1' : 'mr-0.5';

  return (
    <span className={`inline-flex items-center ${gap}`}>
      {active.slice(0, maxBadges).map(key => {
        const cfg = BADGE_CONFIG[key];
        if (!cfg) return null;
        const Icon = cfg.icon;
        return (
          <span key={key} className="inline-flex items-center mr-0.5" title={cfg.label} data-testid={`badge-${key}`}>
            <Icon className={`${iconClass} ${cfg.color} ${cfg.glow}`} fill="currentColor" />
          </span>
        );
      })}
    </span>
  );
}

// Masterpiece badge for film posters
export function MasterpieceBadge({ isMasterpiece, size = 'sm' }) {
  if (!isMasterpiece) return null;

  const sizes = { xs: 'text-[7px] px-1 py-0', sm: 'text-[8px] px-1.5 py-0.5', md: 'text-[9px] px-2 py-0.5' };
  const cls = sizes[size] || sizes.sm;

  return (
    <div className={`absolute top-1 left-1 z-10 ${cls} bg-yellow-500/90 text-black font-black rounded shadow-[0_0_8px_rgba(234,179,8,0.5)] flex items-center gap-0.5`}
      title="CineWORLD Masterpiece" data-testid="badge-masterpiece">
      <Crown className="w-2.5 h-2.5" fill="currentColor" />
      <span>CineWORLD</span>
    </div>
  );
}

// Helper: wrap player name with badge
export function PlayerNameWithBadge({ nickname, badge, badgeExpiry, badges, className = '' }) {
  return (
    <span className={`inline-flex items-center ${className}`}>
      <PlayerBadge badge={badge} badgeExpiry={badgeExpiry} badges={badges} inline />
      <span>{nickname}</span>
    </span>
  );
}
