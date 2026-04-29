/**
 * TvRightsBadge — Badge che indica che un contenuto è trasmesso in TV
 * tramite contratto del mercato diritti.
 *
 * Renderizzato dentro la card della locandina (in basso a destra).
 * Cliccato → apre TvMarketModal in panoramica (per mostrare quale TV detiene i diritti).
 */
import React from 'react';
import { Tv } from 'lucide-react';

export default function TvRightsBadge({ item, onClick, position = 'bottom-right' }) {
  if (!item?.tv_rights_active_contract_id || !item?.tv_rights_station_name) return null;
  const isFull = item.tv_rights_mode === 'full';
  const positions = {
    'bottom-right': 'bottom-1 right-1',
    'top-right':    'top-1 right-1',
    'bottom-left':  'bottom-1 left-1',
  };
  const pos = positions[position] || positions['bottom-right'];
  return (
    <button
      onClick={(e) => { e.stopPropagation(); onClick?.(item); }}
      className={`absolute ${pos} z-10 flex items-center gap-0.5 px-1 py-0.5 rounded text-[7px] font-black uppercase tracking-wider shadow-lg backdrop-blur-sm transition-transform hover:scale-110 active:scale-95 touch-manipulation max-w-[80%] ${
        isFull
          ? 'bg-amber-400 text-black border border-amber-300/50'
          : 'bg-cyan-400 text-black border border-cyan-300/50'
      }`}
      data-testid={`tv-rights-badge-${item.id}`}
      title={`Su ${item.tv_rights_station_name} (${isFull ? '100%' : '50%'})`}
    >
      <Tv size={8} className="flex-shrink-0" />
      <span className="truncate">{item.tv_rights_station_name}</span>
    </button>
  );
}
