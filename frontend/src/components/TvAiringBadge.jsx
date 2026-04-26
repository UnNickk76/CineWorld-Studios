import React, { useEffect, useState, useContext } from 'react';
import { Tv, Radio } from 'lucide-react';
import { AuthContext } from '../contexts';

/**
 * TvAiringBadge — mostra "In TV dal {data ora} su {emittente}" se il contenuto
 * è in palinsesto (scheduled, airing o completed).
 *
 * Glow animato e font/colore presi dal `style` della TV station (default: cyan).
 * Il colore della station è in `primary_color` o derivato dallo `style`.
 */

const STYLE_PRESETS = {
  netflix: { color: '#E50914', font: '"Bebas Neue", sans-serif', glowRgb: '229,9,20' },
  disney: { color: '#0066CC', font: '"Inter", sans-serif', glowRgb: '0,102,204' },
  paramount: { color: '#0064FF', font: '"Inter", sans-serif', glowRgb: '0,100,255' },
  prime: { color: '#00A8E1', font: '"Inter", sans-serif', glowRgb: '0,168,225' },
  apple: { color: '#FFFFFF', font: '"SF Pro Display", -apple-system, sans-serif', glowRgb: '200,200,200' },
  sky: { color: '#0072FF', font: '"Inter", sans-serif', glowRgb: '0,114,255' },
  rai: { color: '#0046AD', font: '"Inter", sans-serif', glowRgb: '0,70,173' },
  dazn: { color: '#F8FF13', font: '"Inter", sans-serif', glowRgb: '248,255,19' },
  tim: { color: '#0046AD', font: '"Inter", sans-serif', glowRgb: '0,70,173' },
  default: { color: '#06b6d4', font: '"Bebas Neue", sans-serif', glowRgb: '6,182,212' },
};

function formatItalianDateTime(iso) {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return null;
    const date = d.toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' });
    const time = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
    return `${date}, ${time}`;
  } catch {
    return null;
  }
}

export default function TvAiringBadge({ contentId, compact = false }) {
  const { api } = useContext(AuthContext);
  const [info, setInfo] = useState(null);

  useEffect(() => {
    if (!contentId) return;
    let cancel = false;
    api.get(`/content/${contentId}/tv-airing-info`)
      .then(r => { if (!cancel) setInfo(r.data?.info || null); })
      .catch(() => {});
    return () => { cancel = true; };
  }, [contentId, api]);

  if (!info || !info.is_in_palinsesto || !info.first_air_at) return null;

  const styleKey = (info.style || 'default').toLowerCase();
  const preset = STYLE_PRESETS[styleKey] || STYLE_PRESETS.default;
  const color = info.primary_color || preset.color;
  const glow = preset.glowRgb;
  const dt = formatItalianDateTime(info.first_air_at);
  if (!dt) return null;

  const isLive = info.broadcast_state === 'airing';

  return (
    <div
      data-testid="tv-airing-badge"
      className={`inline-flex items-center gap-2 ${compact ? 'px-2 py-1 text-[9px]' : 'px-3 py-1.5 text-[11px]'} rounded-full font-bold tv-airing-glow`}
      style={{
        color,
        border: `1px solid rgba(${glow},0.45)`,
        background: `linear-gradient(135deg, rgba(${glow},0.12), rgba(${glow},0.04))`,
        fontFamily: preset.font,
        letterSpacing: '0.04em',
        boxShadow: `0 0 10px rgba(${glow},0.35), inset 0 0 6px rgba(${glow},0.2)`,
      }}
    >
      {isLive
        ? <Radio className={`${compact ? 'w-3 h-3' : 'w-3.5 h-3.5'} animate-pulse`} />
        : <Tv className={`${compact ? 'w-3 h-3' : 'w-3.5 h-3.5'}`} />
      }
      <span className="whitespace-nowrap">
        {isLive ? 'IN ONDA su ' : 'In TV dal '}
        <span style={{ color, textShadow: `0 0 6px rgba(${glow},0.55)` }}>{dt}</span>
        {!isLive && ' su '}
        {!isLive && <span style={{ color, textShadow: `0 0 6px rgba(${glow},0.55)` }}>{info.station_name}</span>}
        {isLive && <> · <span style={{ color }}>{info.station_name}</span></>}
      </span>
      <style>{`
        @keyframes tvAiringPulse {
          0%, 100% { box-shadow: 0 0 10px rgba(${glow},0.35), inset 0 0 6px rgba(${glow},0.2); }
          50% { box-shadow: 0 0 18px rgba(${glow},0.65), inset 0 0 10px rgba(${glow},0.35); }
        }
        .tv-airing-glow { animation: tvAiringPulse 2.4s ease-in-out infinite; }
      `}</style>
    </div>
  );
}
