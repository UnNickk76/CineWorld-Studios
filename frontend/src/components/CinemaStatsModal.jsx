import React, { useState, useEffect } from 'react';
import { X, TrendingUp } from 'lucide-react';

const BACKEND = process.env.REACT_APP_BACKEND_URL || '';

const CinemaStatsModal = ({ film, isOpen, onClose }) => {
  const [stats, setStats] = useState(null);
  const [trendHistory, setTrendHistory] = useState([]);
  const [tvStations, setTvStations] = useState([]);
  const [selectedTv, setSelectedTv] = useState('');
  const [loading, setLoading] = useState('');
  const token = typeof window !== 'undefined' ? localStorage.getItem('cineworld_token') : '';
  const user = JSON.parse(typeof window !== 'undefined' ? localStorage.getItem('cineworld_user') || '{}' : '{}');
  const isOwner = user.id === film?.user_id;

  useEffect(() => {
    if (!isOpen || !film?.id) return;
    const h = { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' };
    fetch(BACKEND + '/api/pipeline-v2/films/' + film.id + '/theater-stats', { headers: h })
      .then(r => r.ok ? r.json() : null).then(d => {
        if (d) {
          setStats(d);
          setTrendHistory(d.cwtrend_history || []);
        }
      }).catch(() => {});
    if (isOwner) {
      fetch(BACKEND + '/api/my-tv/stations', { headers: h })
        .then(r => r.ok ? r.json() : []).then(d => setTvStations(Array.isArray(d) ? d : d?.stations || [])).catch(() => {});
    }
  }, [isOpen, film?.id, isOwner, token]);

  if (!isOpen) return null;

  const ts = stats?.theater_stats || (typeof film?.theater_stats === 'object' ? film.theater_stats : null) || {};
  const days = parseInt(ts.days_in_theater) || 0;
  const remain = parseInt(ts.days_remaining) || 0;
  const ext = parseInt(ts.days_extended) || 0;
  const red = parseInt(ts.days_reduced) || 0;
  const cinemas = parseInt(ts.current_cinemas) || 0;
  const specDay = parseInt(ts.daily_spectators) || 0;
  const specTot = parseInt(ts.total_spectators) || 0;
  const rev = parseInt(ts.total_revenue) || 0;
  const perf = typeof ts.performance === 'string' ? ts.performance : '';
  const perfLabel = { great: 'Straordinario', good: 'Ottimo', ok: 'Discreto', declining: 'In calo', bad: 'Scarso', flop: 'Flop' }[perf] || '';
  const perfColor = { great: '#4ade80', good: '#34d399', ok: '#facc15', declining: '#fb923c', bad: '#f87171', flop: '#ef4444' }[perf] || '#9ca3af';

  const doAction = (endpoint) => {
    if (!window.confirm('Confermi?')) return;
    setLoading(endpoint);
    const h = { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' };
    const body = selectedTv ? JSON.stringify({ station_id: selectedTv }) : '{}';
    fetch(BACKEND + '/api/pipeline-v2/films/' + film.id + '/' + endpoint, { method: 'POST', headers: h, body })
      .then(() => { onClose(); window.location.reload(); }).catch(() => setLoading(''));
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }} onClick={onClose}>
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.6)' }} />
      <div style={{ position: 'relative', width: '100%', maxWidth: 380, background: '#111113', borderRadius: 16, border: '1px solid rgba(56,189,248,0.2)', overflow: 'hidden' }} onClick={e => e.stopPropagation()} data-testid="cinema-stats-modal">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <div>
            <span style={{ fontSize: 13, fontWeight: 'bold', color: '#38bdf8' }}>{film?.pipeline_state === 'released' ? 'AL CINEMA' : 'FUORI SALA'}</span>
            {perfLabel && <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 'bold', color: perfColor }}>{perfLabel}</span>}
          </div>
          <button onClick={onClose} style={{ color: '#6b7280' }} data-testid="cinema-stats-close"><X size={18} /></button>
        </div>
        <div style={{ padding: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 12 }}>
            {[
              { label: 'Cinema', value: '' + cinemas, color: '#fff' },
              { label: 'Spett. oggi', value: '' + specDay, color: '#22d3ee' },
              { label: 'Spett. totali', value: '' + specTot, color: '#facc15' },
            ].map(s => (
              <div key={s.label} style={{ textAlign: 'center', padding: 8, borderRadius: 8, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ fontSize: 9, color: '#6b7280' }}>{s.label}</div>
                <div style={{ fontSize: 14, fontWeight: 'bold', color: s.color }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* CWTrend Sparkline */}
          {trendHistory.length > 0 && <Sparkline data={trendHistory} />}

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 8 }}>
            <span style={{ color: '#6b7280' }}>Giorni in sala</span>
            <span style={{ fontWeight: 'bold', color: '#facc15' }}>{'' + days}gg{remain > 0 ? ' / ' + remain + ' rimasti' : ''}</span>
          </div>
          {(ext > 0 || red > 0) && (
            <div style={{ display: 'flex', gap: 8, fontSize: 10, marginBottom: 8 }}>
              {ext > 0 && <span style={{ color: '#4ade80', fontWeight: 'bold' }}>+{ext} giorni estesi</span>}
              {red > 0 && <span style={{ color: '#f87171', fontWeight: 'bold' }}>-{red} giorni ridotti</span>}
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 12 }}>
            <span style={{ color: '#6b7280' }}>Incassi sala</span>
            <span style={{ fontWeight: 'bold', color: '#4ade80' }}>{'$' + rev.toLocaleString()}</span>
          </div>
          {isOwner && (
            <div>
              {tvStations.length > 0 && (
                <select value={selectedTv} onChange={e => setSelectedTv(e.target.value)}
                  style={{ width: '100%', background: '#1f2937', color: '#fff', border: '1px solid #374151', borderRadius: 8, padding: '6px 8px', fontSize: 11, marginBottom: 8 }}>
                  <option value="">Scegli emittente TV...</option>
                  {tvStations.map(s => <option key={s.id || s.name} value={s.id || s.name}>{s.name || s.channel_name}</option>)}
                </select>
              )}
              <div style={{ display: 'flex', gap: 8 }}>
                {film?.pipeline_state === 'released' && (
                  <button onClick={() => doAction('withdraw-theater')} disabled={!!loading} data-testid="withdraw-theater-btn"
                    style={{ flex: 1, fontSize: 10, padding: '8px 0', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171', fontWeight: 'bold', cursor: 'pointer' }}>
                    {loading === 'withdraw-theater' ? '...' : 'Ritira dal cinema'}
                  </button>
                )}
                {selectedTv && (
                  <button onClick={() => doAction('send-to-tv')} disabled={!!loading}
                    style={{ flex: 1, fontSize: 10, padding: '8px 0', borderRadius: 8, background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', color: '#60a5fa', fontWeight: 'bold', cursor: 'pointer' }}>
                    {loading === 'send-to-tv' ? '...' : 'Manda in TV'}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ─── SVG Sparkline Component ─── */
function Sparkline({ data }) {
  if (!data || data.length < 2) return null;

  const values = data.map(d => d.cwtrend);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const current = values[values.length - 1];
  const prev = values[values.length - 2];
  const trending = current >= prev;

  const W = 220;
  const H = 40;
  const PAD = 4;
  const points = values.map((v, i) => {
    const x = PAD + (i / (values.length - 1)) * (W - PAD * 2);
    const y = H - PAD - ((v - min) / range) * (H - PAD * 2);
    return { x, y };
  });

  const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  const area = line + ` L ${points[points.length - 1].x.toFixed(1)} ${H} L ${points[0].x.toFixed(1)} ${H} Z`;
  const lineColor = trending ? '#4ade80' : '#f87171';
  const fillColor = trending ? 'rgba(74,222,128,0.1)' : 'rgba(248,113,113,0.1)';

  return (
    <div style={{ marginBottom: 12, padding: '8px 0', borderRadius: 10, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }} data-testid="cwtrend-sparkline">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 12px', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <TrendingUp size={12} color={lineColor} />
          <span style={{ fontSize: 10, color: '#9ca3af', fontWeight: '600' }}>CWTrend (7gg)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: 14, fontWeight: 'bold', color: lineColor }}>{current?.toFixed(1)}</span>
          <span style={{ fontSize: 9, color: trending ? '#4ade80' : '#f87171' }}>
            {trending ? '+' : ''}{(current - prev).toFixed(1)}
          </span>
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
          <defs>
            <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={lineColor} stopOpacity="0.3" />
              <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={area} fill="url(#sparkGrad)" />
          <path d={line} fill="none" stroke={lineColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          {/* Current value dot */}
          <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="3" fill={lineColor} stroke="#111113" strokeWidth="1.5" />
        </svg>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0 12px', marginTop: 2 }}>
        {data.map((d, i) => (
          <span key={i} style={{ fontSize: 7, color: '#4b5563' }}>
            {d.day >= 0 ? `G${d.day}` : ''}
          </span>
        ))}
      </div>
    </div>
  );
}

export default CinemaStatsModal;
