// PlayerBadge - Shows badge PNG icons before player name
// CineADMIN/CineMOD = permanent, CineSTAR/CineVIP = timed
// CineWORLD = film badge (not user badge), shown on masterpiece posters
//
// Usage: <PlayerBadge badge={user.badge} badgeExpiry={user.badge_expiry} badges={user.badges} />

import React from 'react';

const BADGE_ASSETS = {
  cineadmin: '/assets/badges/cineadmin.png',
  cinemod: '/assets/badges/cinemod.png',
  cinestar: '/assets/badges/cinestar.png',
  cinevip: '/assets/badges/cinevip.png',
};
const BADGE_ORDER = ['cineadmin', 'cinemod', 'cinestar', 'cinevip'];
const BADGE_LABELS = { cineadmin: 'CineADMIN', cinemod: 'CineMOD', cinestar: 'CineSTAR', cinevip: 'CineVIP' };

function getActiveBadges(badge, badgeExpiry, badges) {
  const active = [];
  if (badges) {
    if (badges.cineadmin) active.push('cineadmin');
    if (badges.cinemod) active.push('cinemod');
  }
  if (badge && badge !== 'none' && badgeExpiry && new Date(badgeExpiry) > new Date()) {
    if (!active.includes(badge)) active.push(badge);
  }
  return active.sort((a, b) => BADGE_ORDER.indexOf(a) - BADGE_ORDER.indexOf(b));
}

export function PlayerBadge({ badge, badgeExpiry, badges, size = 'sm', maxBadges = 2 }) {
  const active = getActiveBadges(badge, badgeExpiry, badges);
  if (active.length === 0) return null;

  const sizes = { xs: 12, sm: 14, md: 18, lg: 22 };
  const px = sizes[size] || sizes.sm;

  return (
    <span className="inline-flex items-center mr-0.5 align-middle" style={{ gap: '1px' }}>
      {active.slice(0, maxBadges).map(key => (
        <img key={key} src={BADGE_ASSETS[key]} alt={BADGE_LABELS[key]} title={BADGE_LABELS[key]}
          className="inline-block align-middle object-contain" draggable={false}
          style={{ width: px, height: px }}
          data-testid={`badge-${key}`} />
      ))}
    </span>
  );
}

// CineWORLD badge for masterpiece film posters (NOT a user badge)
export function MasterpieceBadge({ isMasterpiece, size = 'sm' }) {
  if (!isMasterpiece) return null;
  const sizes = { xs: 20, sm: 24, md: 30 };
  const px = sizes[size] || sizes.sm;

  return (
    <div className="absolute top-1 left-1 z-10" title="CineWORLD Masterpiece" data-testid="badge-masterpiece">
      <img src="/assets/badges/cineworld.png" alt="CineWORLD" className="object-contain drop-shadow-[0_0_4px_rgba(234,179,8,0.6)]"
        style={{ width: px, height: px }} draggable={false} />
    </div>
  );
}

// Convenience wrapper: [badges] Nickname
export function PlayerNameWithBadge({ nickname, badge, badgeExpiry, badges, className = '' }) {
  return (
    <span className={`inline-flex items-center ${className}`}>
      <PlayerBadge badge={badge} badgeExpiry={badgeExpiry} badges={badges} />
      <span>{nickname}</span>
    </span>
  );
}
