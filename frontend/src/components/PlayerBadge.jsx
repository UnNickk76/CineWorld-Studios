// PlayerBadge - Shows CineVIP/CineSTAR badge before player name
// Usage: <PlayerBadge badge={user.badge} badgeExpiry={user.badge_expiry} />
// Or inline: <PlayerBadge badge={user.badge} badgeExpiry={user.badge_expiry} inline />

import React from 'react';
import { Crown, Star } from 'lucide-react';

function isBadgeActive(badge, expiry) {
  if (!badge || badge === 'none') return false;
  if (!expiry) return false;
  return new Date(expiry) > new Date();
}

export function PlayerBadge({ badge, badgeExpiry, size = 'sm', inline = false }) {
  if (!isBadgeActive(badge, badgeExpiry)) return null;

  const sizes = { xs: 'w-3 h-3', sm: 'w-3.5 h-3.5', md: 'w-4 h-4', lg: 'w-5 h-5' };
  const iconClass = sizes[size] || sizes.sm;

  if (badge === 'cinevip') {
    return (
      <span className={`inline-flex items-center ${inline ? 'mr-1' : 'mr-0.5'}`} title="CineVIP" data-testid="badge-cinevip">
        <Crown className={`${iconClass} text-yellow-400 drop-shadow-[0_0_4px_rgba(250,204,21,0.6)]`} fill="currentColor" />
      </span>
    );
  }

  if (badge === 'cinestar') {
    return (
      <span className={`inline-flex items-center ${inline ? 'mr-1' : 'mr-0.5'}`} title="CineSTAR" data-testid="badge-cinestar">
        <Star className={`${iconClass} text-amber-300 drop-shadow-[0_0_5px_rgba(252,211,77,0.7)]`} fill="currentColor" />
      </span>
    );
  }

  return null;
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
export function PlayerNameWithBadge({ nickname, badge, badgeExpiry, className = '' }) {
  return (
    <span className={`inline-flex items-center ${className}`}>
      <PlayerBadge badge={badge} badgeExpiry={badgeExpiry} inline />
      <span>{nickname}</span>
    </span>
  );
}
