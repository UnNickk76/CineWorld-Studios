import React, { useState, useRef, useEffect } from 'react';
import { ArrowDownUp, Check } from 'lucide-react';

/**
 * SectionSortMenu — piccola icona ordinamento nel banner di una sezione dashboard.
 * Dropdown con opzioni (etichetta + valore). Emette `onChange(value)` al click.
 * 
 * Props:
 *   value: string — chiave opzione attiva
 *   onChange: (value:string) => void
 *   options: Array<{ value: string, label: string }>
 *   className: optional extra class
 *   testId: optional data-testid for the trigger (default 'section-sort-menu')
 */
export function SectionSortMenu({ value, onChange, options, className = '', testId = 'section-sort-menu' }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onClickOutside);
    document.addEventListener('touchstart', onClickOutside);
    return () => {
      document.removeEventListener('mousedown', onClickOutside);
      document.removeEventListener('touchstart', onClickOutside);
    };
  }, [open]);

  const active = options.find(o => o.value === value) || options[0];

  return (
    <div ref={ref} className={`relative inline-flex items-center ${className}`}>
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); setOpen(v => !v); }}
        className="flex items-center gap-1 px-1.5 h-5 rounded-md border border-white/10 bg-white/5 hover:bg-white/10 active:scale-95 transition-all text-[8px] uppercase tracking-wider text-white/70 hover:text-white"
        data-testid={testId}
        aria-label={`Ordina: ${active?.label || ''}`}
      >
        <ArrowDownUp className="w-2.5 h-2.5" />
        <span className="hidden sm:inline truncate max-w-[70px]">{active?.label}</span>
      </button>
      {open && (
        <div
          className="absolute right-0 top-full mt-1 z-50 min-w-[140px] rounded-lg border border-white/15 bg-black/95 backdrop-blur-xl shadow-2xl overflow-hidden"
          data-testid={`${testId}-dropdown`}
        >
          {options.map(opt => (
            <button
              key={opt.value}
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onChange?.(opt.value);
                setOpen(false);
              }}
              className={`w-full flex items-center justify-between gap-2 px-2.5 py-1.5 text-left text-[9px] transition-colors ${
                opt.value === value
                  ? 'bg-white/10 text-white font-semibold'
                  : 'text-white/70 hover:bg-white/5 hover:text-white'
              }`}
              data-testid={`${testId}-option-${opt.value}`}
            >
              <span className="truncate">{opt.label}</span>
              {opt.value === value && <Check className="w-2.5 h-2.5 flex-shrink-0" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Helper puro — applica un ordinamento client-side a un array.
 * Supporta chiavi: newest, oldest, top_rated, most_viewed, most_liked, alpha_asc, alpha_desc.
 */
export function sortItems(items, sortKey) {
  if (!Array.isArray(items)) return [];
  const arr = [...items];
  const num = (v) => (typeof v === 'number' && isFinite(v) ? v : 0);
  switch (sortKey) {
    case 'newest':
      return arr.sort((a, b) => new Date(b.created_at || b.released_at || 0) - new Date(a.created_at || a.released_at || 0));
    case 'oldest':
      return arr.sort((a, b) => new Date(a.created_at || a.released_at || 0) - new Date(b.created_at || b.released_at || 0));
    case 'top_rated':
      return arr.sort((a, b) => num(b.quality_score) - num(a.quality_score));
    case 'most_viewed':
      return arr.sort((a, b) => num(b.total_spectators || b.total_revenue) - num(a.total_spectators || a.total_revenue));
    case 'most_liked':
      return arr.sort((a, b) => num(b.virtual_likes || b.likes_count) - num(a.virtual_likes || a.likes_count));
    case 'alpha_asc':
      return arr.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
    case 'alpha_desc':
      return arr.sort((a, b) => (b.title || '').localeCompare(a.title || ''));
    default:
      return arr;
  }
}

// Preset pool più comune per le sezioni dashboard
export const DEFAULT_SORT_OPTIONS = [
  { value: 'newest', label: 'Più Recenti' },
  { value: 'top_rated', label: 'Top Voto' },
  { value: 'most_viewed', label: 'Più Visti' },
  { value: 'most_liked', label: 'Più Amati' },
  { value: 'alpha_asc', label: 'A-Z' },
];

export default SectionSortMenu;
