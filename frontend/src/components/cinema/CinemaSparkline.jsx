// CineWorld Studio's — CinemaSparkline
// Mini-grafico (sparkline) ultimi 7 giorni per overlay sui poster.
// Mostra trend visuale immediato senza aprire il modale completo.

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export const CinemaSparkline = ({ contentId, className = '' }) => {
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!contentId) return;
    let cancelled = false;
    (async () => {
      try {
        const token = localStorage.getItem('cineworld_token');
        const res = await axios.get(`${API}/api/cinema-stats/${contentId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (cancelled) return;
        const daily = res.data?.daily_breakdown || [];
        const last7 = daily.slice(-7);
        if (last7.length >= 2) {
          setData(last7);
        }
      } catch { /* silent */ }
    })();
    return () => { cancelled = true; };
  }, [contentId]);

  if (!data || data.length < 2) return null;

  const values = data.map(d => d.revenue);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = Math.max(1, max - min);
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((d.revenue - min) / range) * 90 - 5;
    return `${x},${y}`;
  }).join(' ');

  // Color basato su trend (ultimi 2 punti)
  const trend = values[values.length - 1] - values[values.length - 2];
  const trendColor = trend > 0 ? '#10b981' : trend < 0 ? '#f87171' : '#06b6d4';

  return (
    <div className={`w-16 h-6 ${className}`} data-testid="cinema-sparkline">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
        <polyline
          points={points}
          fill="none"
          stroke={trendColor}
          strokeWidth="3"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {/* Last point dot */}
        {data.length > 0 && (() => {
          const last = data[data.length - 1];
          const lx = 100;
          const ly = 100 - ((last.revenue - min) / range) * 90 - 5;
          return <circle cx={lx} cy={ly} r="4" fill={trendColor} />;
        })()}
      </svg>
    </div>
  );
};

export default CinemaSparkline;
