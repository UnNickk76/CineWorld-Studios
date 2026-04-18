import React from 'react';

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
