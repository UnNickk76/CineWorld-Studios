// CineWorld Studio's — AttendanceChart
// Grafico bar/line ibrido per affluenze giornaliere con heatmap colors
// Verde (hold>90%) → Giallo → Rosso (<50%)
// Mostra anche la linea di forecast per i 3 giorni futuri (tratteggiata).

import React from 'react';
import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell, CartesianGrid } from 'recharts';

const fmtMoney = (v) => v >= 1000 ? `$${(v / 1000).toFixed(1)}K` : `$${v}`;
const fmtNum = (v) => Number(v).toLocaleString('it-IT');

const heatColor = (hold) => {
  if (hold == null) return '#06b6d4'; // cyan = giorno 1
  if (hold >= 1.0) return '#10b981';   // emerald: crescita
  if (hold >= 0.85) return '#22c55e';  // green
  if (hold >= 0.65) return '#84cc16';  // lime
  if (hold >= 0.50) return '#eab308';  // yellow
  if (hold >= 0.30) return '#f97316';  // orange
  return '#ef4444';                    // red
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div className="rounded-lg border border-cyan-700/50 bg-zinc-950/95 p-2.5 text-xs shadow-2xl">
      <div className="font-bold text-cyan-300">{d.day_label} • {d.date}</div>
      {d.is_forecast ? (
        <>
          <div className="text-amber-300 mt-1">📊 Stima</div>
          <div className="text-zinc-300">{fmtMoney(d.revenue)} previsti</div>
          <div className="text-zinc-500 text-[10px]">{fmtNum(d.spectators)} spettatori stimati</div>
        </>
      ) : (
        <>
          <div className="text-emerald-300 mt-1">{fmtMoney(d.revenue)}</div>
          <div className="text-zinc-300">{fmtNum(d.spectators)} spettatori</div>
          {d.hold_ratio != null && (
            <div className={`text-[10px] mt-1 ${d.hold_ratio >= 0.85 ? 'text-emerald-400' : d.hold_ratio >= 0.55 ? 'text-yellow-400' : 'text-rose-400'}`}>
              Hold: {Math.round(d.hold_ratio * 100)}%
            </div>
          )}
          {d.is_weekend && <div className="text-violet-400 text-[10px]">🎉 Weekend</div>}
          {d.is_today && <div className="text-cyan-400 text-[10px] font-bold">⚡ Oggi (live)</div>}
        </>
      )}
    </div>
  );
};

export const AttendanceChart = ({ daily = [], forecast = [], totalDays = 0, mode = 'live', height = 220 }) => {
  // mode 'live' = solo passati+oggi (mobile-friendly)
  // mode 'full' = tutti i giorni programmati con vuoti per i futuri
  let combined;
  if (mode === 'full' && totalDays > 0) {
    // Costruisci array completo da G1 a G{totalDays}
    const dayMap = {};
    daily.forEach(d => { dayMap[d.day_index] = { ...d, _color: heatColor(d.hold_ratio) }; });
    forecast.forEach(f => { dayMap[f.day_index] = { ...f, revenue: f.projected_revenue, spectators: f.projected_spectators, _color: '#fbbf2440' }; });
    combined = [];
    for (let i = 0; i < totalDays; i++) {
      if (dayMap[i]) {
        combined.push(dayMap[i]);
      } else {
        combined.push({
          day_index: i,
          day_label: `G${i + 1}`,
          revenue: 0,
          spectators: 0,
          hold_ratio: null,
          is_today: false,
          is_future: true,
          _color: '#27272a',
        });
      }
    }
  } else {
    combined = [
      ...daily.map(d => ({ ...d, _color: heatColor(d.hold_ratio) })),
      ...forecast.map(f => ({
        ...f,
        revenue: f.projected_revenue,
        spectators: f.projected_spectators,
        _color: '#fbbf2440',
      })),
    ];
  }

  if (combined.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-xs text-zinc-500 italic">
        Dati affluenze in arrivo (aggiornati ogni ora)…
      </div>
    );
  }

  return (
    <div className="w-full" data-testid="attendance-chart">
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={combined} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis dataKey="day_label" tick={{ fill: '#a1a1aa', fontSize: 9 }} axisLine={{ stroke: '#3f3f46' }} />
          <YAxis tick={{ fill: '#a1a1aa', fontSize: 9 }} axisLine={{ stroke: '#3f3f46' }} tickFormatter={fmtMoney} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(6, 182, 212, 0.05)' }} />
          {/* Bar per daily */}
          <Bar dataKey="revenue" radius={[3, 3, 0, 0]}>
            {combined.map((entry, i) => (
              <Cell
                key={`c-${i}`}
                fill={entry.is_forecast ? '#fbbf24' : entry._color}
                fillOpacity={entry.is_forecast ? 0.35 : 0.95}
                stroke={entry.is_today ? '#06b6d4' : 'none'}
                strokeWidth={entry.is_today ? 2 : 0}
              />
            ))}
          </Bar>
          {/* Linea di tendenza */}
          <Line
            type="monotone"
            dataKey="revenue"
            stroke="#06b6d4"
            strokeWidth={1.4}
            dot={false}
            strokeOpacity={0.6}
            activeDot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
      {/* Legend */}
      <div className="flex items-center justify-center gap-3 mt-1 text-[9px] text-zinc-500">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded bg-emerald-500" /> Hold &gt; 85%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded bg-yellow-500" /> 50-85%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded bg-rose-500" /> &lt; 50%
        </span>
        {forecast.length > 0 && (
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded bg-amber-400/40 border border-amber-400" /> Forecast
          </span>
        )}
      </div>
    </div>
  );
};

export default AttendanceChart;
