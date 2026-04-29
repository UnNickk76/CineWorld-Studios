/**
 * DistributionPopup — Mostra dove viene trasmesso un film (LAMPO o Classic V3).
 *
 * Supporta entrambi i formati:
 *  • LAMPO: release_continents, release_countries, release_cities, worldwide, distribution_scope
 *  • Classic V3: cinema_distribution[{country_code, country_name, cinemas, total_attendance}],
 *                distribution_zone, distribution_continents/zones
 *
 * Mobile-first: bottom-sheet su mobile, dialog centrato su desktop.
 */
import React from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { Zap, Globe, MapPin, Building2, X, Tv } from 'lucide-react';

// ── Helpers ─────────────────────────────────────────────
const normalize = (v) => Array.isArray(v) ? v.filter(Boolean) : [];
const ZONE_LABEL = {
  national:    'Nazionale',
  continental: 'Continentale',
  world:       'Mondiale',
  worldwide:   'Mondiale',
};

const buildLines = (film) => {
  if (!film) return null;
  const continents = normalize(film.release_continents || film.distribution_continents || film.distribution_zones);
  const countries  = normalize(film.release_countries);
  const cities     = normalize(film.release_cities);
  const worldwide  = !!(film.worldwide || film.distribution_zone === 'world' || film.distribution_zone === 'worldwide');
  const cinemaDist = normalize(film.cinema_distribution); // [{country_name, cinemas, ...}]

  // Derive label
  const label =
    film.distribution_scope ||
    (worldwide ? 'Mondiale' :
      ZONE_LABEL[film.distribution_zone] ||
      (cinemaDist.length > 0
        ? `${cinemaDist.length} ${cinemaDist.length === 1 ? 'Paese' : 'Paesi'}`
        : null));

  const hasAnyData =
    worldwide ||
    continents.length > 0 ||
    countries.length > 0 ||
    cities.length > 0 ||
    cinemaDist.length > 0;

  return { label, continents, countries, cities, worldwide, cinemaDist, hasAnyData };
};

export const hasDistributionData = (film) => {
  const r = buildLines(film);
  return !!(r && r.hasAnyData);
};

export const getDistributionLabel = (film) => {
  const r = buildLines(film);
  return r ? r.label : null;
};

// ── Section ─────────────────────────────────────────────
const Section = ({ icon: Icon, title, items, accent = 'amber', emptyText, isPills = false }) => {
  if (!items || items.length === 0) return null;
  const colorMap = {
    amber:   { bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   text: 'text-amber-200',   icon: 'text-amber-300' },
    cyan:    { bg: 'bg-cyan-500/10',    border: 'border-cyan-500/30',    text: 'text-cyan-200',    icon: 'text-cyan-300' },
    emerald: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-200', icon: 'text-emerald-300' },
    violet:  { bg: 'bg-violet-500/10',  border: 'border-violet-500/30',  text: 'text-violet-200',  icon: 'text-violet-300' },
  }[accent];
  return (
    <div className="mb-3">
      <div className="flex items-center gap-1.5 mb-1.5">
        <Icon size={13} className={colorMap.icon} />
        <span className="text-[10px] uppercase tracking-wider font-semibold text-white/80">
          {title} <span className="text-white/40">({items.length})</span>
        </span>
      </div>
      {isPills ? (
        <div className="flex gap-1.5 flex-wrap">
          {items.map((it, i) => (
            <span
              key={i}
              className={`px-2 py-1 text-[11px] rounded-full ${colorMap.bg} ${colorMap.border} border ${colorMap.text} font-medium`}
              data-testid={`dist-pill-${title.toLowerCase()}-${i}`}
            >
              {typeof it === 'string' ? it : (it.country_name || it.name || '—')}
            </span>
          ))}
        </div>
      ) : (
        <div className={`rounded-lg ${colorMap.bg} ${colorMap.border} border p-2 max-h-44 overflow-y-auto`}>
          <ul className="space-y-1">
            {items.map((it, i) => (
              <li key={i} className={`text-[11px] ${colorMap.text} leading-snug flex items-center justify-between gap-2`} data-testid={`dist-item-${title.toLowerCase()}-${i}`}>
                <span className="truncate">
                  {typeof it === 'string' ? it : (it.country_name || it.name || '—')}
                </span>
                {typeof it === 'object' && it.cinemas != null && (
                  <span className="text-[9px] uppercase tracking-wider text-white/50 flex-shrink-0">
                    {it.cinemas} {it.cinemas === 1 ? 'sala' : 'sale'}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      {emptyText && items.length === 0 && (
        <div className="text-[10px] text-white/40 italic">{emptyText}</div>
      )}
    </div>
  );
};

// ── Main popup ───────────────────────────────────────────
export default function DistributionPopup({ open, onClose, film }) {
  const data = buildLines(film);
  if (!data) return null;
  const { label, continents, countries, cities, worldwide, cinemaDist } = data;
  const isLampo = !!(film?.is_lampo || film?.mode === 'lampo');

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent
        className="max-w-md p-0 bg-gradient-to-b from-[#0c0a08] to-[#050302] border border-amber-500/20 max-h-[85vh] overflow-hidden flex flex-col"
        data-testid="distribution-popup"
      >
        {/* Header */}
        <div className="px-4 pt-4 pb-3 border-b border-white/5 flex-shrink-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              {isLampo ? (
                <Zap size={18} className="text-amber-400 flex-shrink-0 drop-shadow-[0_0_6px_rgba(251,191,36,0.7)]" />
              ) : (
                <Globe size={18} className="text-cyan-400 flex-shrink-0" />
              )}
              <div className="min-w-0">
                <h2 className="text-sm font-bold text-white truncate font-['Bebas_Neue'] tracking-wide text-base">
                  Dove viene trasmesso
                </h2>
                <p className="text-[10px] text-white/50 truncate">"{film?.title || '—'}"</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white/40 hover:text-white p-1 -mr-1 flex-shrink-0"
              data-testid="distribution-popup-close"
              aria-label="Chiudi"
            >
              <X size={16} />
            </button>
          </div>

          {/* Big label */}
          {label && (
            <div className="mt-3 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-center">
              <div className="text-[9px] uppercase tracking-widest text-amber-300/80 font-semibold mb-0.5">Distribuzione</div>
              <div className="text-amber-100 font-bold text-sm">
                {label}
                {worldwide && ' 🌍'}
              </div>
            </div>
          )}
        </div>

        {/* Body — scrollable */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          {worldwide && (
            <div className="mb-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-center">
              <Globe size={20} className="inline text-emerald-300 mb-1" />
              <div className="text-[12px] text-emerald-100 font-medium">In tutto il mondo 🌍</div>
              <div className="text-[10px] text-emerald-300/70 italic mt-1">Distribuzione globale: presente in tutti i continenti</div>
            </div>
          )}

          {/* LAMPO sections */}
          {continents.length > 0 && (
            <Section icon={Globe} title="Continenti" items={continents} accent="cyan" isPills />
          )}
          {countries.length > 0 && (
            <Section icon={MapPin} title="Nazioni" items={countries} accent="emerald" isPills />
          )}
          {cities.length > 0 && (
            <Section icon={Building2} title="Città" items={cities} accent="amber" />
          )}

          {/* Classic V3 cinema_distribution */}
          {cinemaDist.length > 0 && (
            <Section icon={Tv} title="Sale per nazione" items={cinemaDist} accent="violet" />
          )}

          {/* Empty fallback */}
          {!worldwide && continents.length === 0 && countries.length === 0 && cities.length === 0 && cinemaDist.length === 0 && (
            <div className="py-8 text-center">
              <Globe size={24} className="inline text-white/20 mb-2" />
              <div className="text-[12px] text-white/50">Nessun dato di distribuzione disponibile.</div>
            </div>
          )}
        </div>

        {/* Footer hint */}
        <div className="px-4 py-2 border-t border-white/5 flex-shrink-0">
          <p className="text-[9px] text-white/40 italic text-center">
            {isLampo ? '⚡ Distribuzione LAMPO: pre-calcolata al rilascio' : '🎬 Distribuzione classica: scelta dal produttore'}
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
