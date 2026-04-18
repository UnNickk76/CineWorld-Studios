import React from 'react';

/**
 * AvatarWithLogo — Avatar con logo sovrapposto in basso a destra.
 */
export function AvatarWithLogo({ avatarUrl, logoUrl, nickname, size = 'sm', className = '' }) {
  const sizes = {
    xs: { outer: 'w-6 h-6', logo: 'w-3 h-3 -bottom-0.5 -right-0.5', text: 'text-[8px]' },
    sm: { outer: 'w-10 h-10', logo: 'w-5 h-5 -bottom-0.5 -right-0.5', text: 'text-sm' },
    md: { outer: 'w-14 h-14', logo: 'w-7 h-7 -bottom-1 -right-1 border-2', text: 'text-lg' },
    lg: { outer: 'w-20 h-20', logo: 'w-9 h-9 -bottom-1 -right-1 border-2', text: 'text-2xl' },
  };
  const s = sizes[size] || sizes.sm;
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
  const imgSrc = avatarUrl?.startsWith('/') ? `${BACKEND_URL}${avatarUrl}` : avatarUrl;

  return (
    <div className={`relative shrink-0 ${className}`} data-testid="avatar-with-logo">
      <div className={`${s.outer} rounded-full border-2 border-yellow-500/40 overflow-hidden bg-gray-800`}>
        {avatarUrl ? (
          <img src={imgSrc} alt={nickname} className="w-full h-full object-cover"
            onError={(e) => { e.target.onerror=null; e.target.style.display='none'; }} />
        ) : (
          <div className={`w-full h-full flex items-center justify-center text-yellow-400 font-bold ${s.text}`}>{(nickname || '?')[0]}</div>
        )}
      </div>
      {logoUrl && (
        <img src={logoUrl} alt="" className={`absolute ${s.logo} rounded-full border-gray-900 object-contain bg-gray-900/90`} />
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
