import React, { useState, useEffect, useContext } from 'react';
import { X, Star, Film, Tv, Sparkles, TrendingUp, Award } from 'lucide-react';
import { AuthContext } from '../contexts';

const BACKEND = process.env.REACT_APP_BACKEND_URL || '';

const LEVEL_BADGES = [
  { min: 0, label: 'Esordiente', color: '#6b7280', bg: 'rgba(107,114,128,0.15)' },
  { min: 3, label: 'Promettente', color: '#60a5fa', bg: 'rgba(96,165,250,0.15)' },
  { min: 8, label: 'Affermato', color: '#34d399', bg: 'rgba(52,211,153,0.15)' },
  { min: 15, label: 'Maestro', color: '#a78bfa', bg: 'rgba(167,139,250,0.15)' },
  { min: 30, label: 'Leggenda', color: '#facc15', bg: 'rgba(250,204,21,0.15)' },
];

function getBadge(totalFilms) {
  let badge = LEVEL_BADGES[0];
  for (const b of LEVEL_BADGES) {
    if (totalFilms >= b.min) badge = b;
  }
  return badge;
}

export default function ProducerProfileModal({ producerId, producerData, isOpen, onClose }) {
  const { api } = useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);

    // If we have a producerId, fetch from backend; otherwise use producerData
    if (producerId) {
      api.get(`/players/${producerId}/profile`).then(r => {
        setStats(r.data);
        setLoading(false);
      }).catch(() => {
        // Fallback: build from producerData
        if (producerData) setStats(buildLocalStats(producerData));
        setLoading(false);
      });
    } else if (producerData) {
      setStats(buildLocalStats(producerData));
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, [isOpen, producerId, producerData, api]);

  if (!isOpen) return null;

  const s = stats || {};
  const totalContent = (s.total_films || 0) + (s.total_series || 0) + (s.total_anime || 0);
  const badge = getBadge(totalContent);
  const avgCwsv = s.avg_cwsv || 0;

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}
      onClick={onClose} data-testid="producer-profile-modal">
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.8)' }} />
      <div style={{ position: 'relative', width: '100%', maxWidth: '380px', background: '#111113', borderRadius: '12px',
        border: '1px solid rgba(167,139,250,0.2)', overflow: 'hidden', maxHeight: '85vh', overflowY: 'auto' }}
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <span style={{ color: '#a78bfa', fontSize: '14px', fontWeight: 'bold', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1.5px' }}>Profilo Produttore</span>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#666', cursor: 'pointer' }}><X size={18} /></button>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <div style={{ width: '24px', height: '24px', border: '2px solid rgba(167,139,250,0.3)', borderTopColor: '#a78bfa', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }} />
          </div>
        ) : !s.nickname ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666', fontSize: '12px' }}>Profilo non disponibile</div>
        ) : (
          <div style={{ padding: '16px' }}>
            {/* Avatar + Name */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'linear-gradient(135deg, rgba(167,139,250,0.3), rgba(56,189,248,0.3))',
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px', fontWeight: 'bold', color: '#fff', border: '2px solid rgba(167,139,250,0.3)' }}>
                {(s.nickname || '?')[0]}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#fff' }}>{s.nickname}</div>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.production_house_name || 'Studio indipendente'}</div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '4px', padding: '2px 8px', borderRadius: '10px',
                  background: badge.bg, border: `1px solid ${badge.color}30`, fontSize: '9px', fontWeight: 'bold', color: badge.color }}>
                  <Award size={10} /> {badge.label}
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', marginBottom: '14px' }}>
              <StatCell icon={<Film size={12} />} label="Film" value={s.total_films || 0} color="#facc15" />
              <StatCell icon={<Tv size={12} />} label="Serie TV" value={s.total_series || 0} color="#60a5fa" />
              <StatCell icon={<Sparkles size={12} />} label="Anime" value={s.total_anime || 0} color="#f472b6" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '14px' }}>
              <StatCell icon={<Star size={12} />} label="CWSv Medio" value={avgCwsv > 0 ? (avgCwsv % 1 === 0 ? avgCwsv : avgCwsv.toFixed(1)) : '—'} color="#f0c040" />
              <StatCell icon={<TrendingUp size={12} />} label="Revenue" value={`$${formatRev(s.total_revenue || 0)}`} color="#4ade80" />
            </div>

            {/* Best film */}
            {s.best_film && (
              <div style={{ padding: '10px', borderRadius: '8px', background: 'rgba(250,204,21,0.05)', border: '1px solid rgba(250,204,21,0.15)', marginBottom: '14px' }}>
                <div style={{ fontSize: '8px', color: '#6b7280', textTransform: 'uppercase', marginBottom: '4px' }}>Film migliore</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Star size={14} fill="#facc15" color="#facc15" />
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#fff' }}>{s.best_film.title}</div>
                    <div style={{ fontSize: '9px', color: '#888' }}>CWSv {s.best_film.cwsv_display || s.best_film.quality_score || '?'}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Recent filmography */}
            {s.filmography?.length > 0 && (
              <div>
                <div style={{ fontSize: '9px', color: '#6b7280', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '6px' }}>Filmografia recente</div>
                {s.filmography.slice(0, 5).map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: i < 4 ? '1px solid rgba(255,255,255,0.03)' : 'none' }}>
                    <span style={{ fontSize: '9px', color: '#555', width: '16px' }}>{i + 1}.</span>
                    <span style={{ fontSize: '10px', color: '#ddd', flex: 1 }}>{f.title}</span>
                    <span style={{ fontSize: '9px', fontWeight: 'bold', color: (f.quality_score || 0) >= 8 ? '#facc15' : (f.quality_score || 0) >= 6 ? '#4ade80' : '#fb923c' }}>
                      {f.cwsv_display || (f.quality_score ? f.quality_score.toFixed(1) : '—')}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCell({ icon, label, value, color }) {
  return (
    <div style={{ textAlign: 'center', padding: '8px 4px', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
      <div style={{ fontSize: '8px', color: '#6b7280', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>{icon} {label}</div>
      <div style={{ fontSize: '16px', fontWeight: 'bold', color, marginTop: '2px' }}>{value}</div>
    </div>
  );
}

function formatRev(n) {
  if (n >= 1000000000) return (n / 1000000000).toFixed(1) + 'B';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
  return n.toString();
}

function buildLocalStats(data) {
  return {
    nickname: data.nickname || data.name || '?',
    production_house_name: data.production_house_name || data.studio || '',
    total_films: data.total_films_released || 0,
    total_series: 0,
    total_anime: 0,
    total_revenue: data.total_revenue || 0,
    avg_cwsv: 0,
    filmography: [],
    best_film: null,
  };
}
