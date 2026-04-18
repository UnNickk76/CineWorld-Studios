import React from 'react';

/**
 * AvatarWithLogo — Avatar con logo della casa di produzione sovrapposto.
 * Il logo copre circa il 55% dell'avatar in basso a destra ma l'avatar resta
 * visibile dietro (logo con leggera trasparenza + bordo ring).
 */
export function AvatarWithLogo({ avatarUrl, logoUrl, nickname, size = 'sm', className = '' }) {
  const sizes = {
    xs: { outer: 'w-7 h-7', logo: 'w-4 h-4 -bottom-0.5 -right-0.5 ring-1', text: 'text-[9px]' },
    sm: { outer: 'w-12 h-12', logo: 'w-7 h-7 -bottom-1 -right-1 ring-2', text: 'text-base' },
    md: { outer: 'w-16 h-16', logo: 'w-9 h-9 -bottom-1 -right-1 ring-2', text: 'text-lg' },
    lg: { outer: 'w-24 h-24', logo: 'w-14 h-14 -bottom-1 -right-1 ring-2', text: 'text-2xl' },
  };
  const s = sizes[size] || sizes.sm;
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
  const imgSrc = avatarUrl?.startsWith('/') ? `${BACKEND_URL}${avatarUrl}` : avatarUrl;

  return (
    <div className={`relative shrink-0 ${className}`} data-testid="avatar-with-logo">
      <div className={`${s.outer} rounded-full border-2 border-yellow-500/40 overflow-hidden bg-gray-800 shadow-lg shadow-black/30`}>
        {avatarUrl ? (
          <img src={imgSrc} alt={nickname} className="w-full h-full object-cover"
            onError={(e) => { e.target.onerror=null; e.target.style.display='none'; }} />
        ) : (
          <div className={`w-full h-full flex items-center justify-center text-yellow-400 font-bold ${s.text}`}>{(nickname || '?')[0]}</div>
        )}
      </div>
      {logoUrl && (
        <img
          src={logoUrl}
          alt=""
          className={`absolute ${s.logo} rounded-full ring-gray-900 object-contain bg-gradient-to-br from-gray-900/95 to-gray-800/95 shadow-md shadow-black/50`}
          style={{ opacity: 0.95 }}
        />
      )}
    </div>
  );
}

/**
 * StudioName — Displays production house logo + name inline.
 * Use everywhere production_house_name appears.
 * 
 * Props:
 *   name: string — production house name
 *   logoUrl: string — logo data URI or URL
 *   className: string — extra classes for the text
 *   size: 'xs' | 'sm' | 'md' — controls logo+text size
 */
export function StudioName({ name, logoUrl, className = '', size = 'xs' }) {
  if (!name) return null;
  const sizes = {
    xs: { img: 'w-3 h-3', text: 'text-[10px]' },
    sm: { img: 'w-3.5 h-3.5', text: 'text-xs' },
    md: { img: 'w-4 h-4', text: 'text-sm' },
  };
  const s = sizes[size] || sizes.xs;

  return (
    <span className={`inline-flex items-center gap-0.5 ${className}`} data-testid="studio-name">
      {logoUrl && <img src={logoUrl} alt="" className={`${s.img} rounded-sm object-contain shrink-0`} />}
      <span className={s.text}>{name}</span>
    </span>
  );
}
