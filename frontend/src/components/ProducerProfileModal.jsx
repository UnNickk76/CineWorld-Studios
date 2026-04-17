import React, { useState, useEffect, useContext } from 'react';
import { X, Star, Film, Tv, Sparkles, TrendingUp, Award, MessageCircle, Swords, Crown, UserPlus, UserCheck, BarChart3 } from 'lucide-react';
import { AuthContext } from '../contexts';
import { toast } from 'sonner';

const LEVEL_BADGES = [
  { min: 0, label: 'Esordiente', color: '#6b7280', bg: 'rgba(107,114,128,0.12)', border: 'rgba(107,114,128,0.2)', glow: '' },
  { min: 3, label: 'Promettente', color: '#60a5fa', bg: 'rgba(96,165,250,0.12)', border: 'rgba(96,165,250,0.2)', glow: '' },
  { min: 8, label: 'Affermato', color: '#34d399', bg: 'rgba(52,211,153,0.12)', border: 'rgba(52,211,153,0.2)', glow: '0 0 12px rgba(52,211,153,0.15)' },
  { min: 15, label: 'Maestro', color: '#a78bfa', bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.25)', glow: '0 0 16px rgba(167,139,250,0.15)' },
  { min: 30, label: 'Leggenda', color: '#facc15', bg: 'rgba(250,204,21,0.12)', border: 'rgba(250,204,21,0.25)', glow: '0 0 20px rgba(250,204,21,0.2)' },
];

function getBadge(n) { let b = LEVEL_BADGES[0]; for (const x of LEVEL_BADGES) if (n >= x.min) b = x; return b; }
function fmtRev(n) { if (n >= 1e9) return (n/1e9).toFixed(1)+'B'; if (n >= 1e6) return (n/1e6).toFixed(1)+'M'; if (n >= 1e3) return (n/1e3).toFixed(0)+'K'; return n.toString(); }

export default function ProducerProfileModal({ producerId, producerData, isOpen, onClose, onCompare }) {
  const { api, user } = useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const isSelf = user?.id === producerId;

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    if (producerId) {
      Promise.all([
        api.get(`/players/${producerId}/profile`).catch(() => null),
        !isSelf ? api.get(`/players/${producerId}/is-following`).catch(() => null) : Promise.resolve(null),
      ]).then(([profileRes, followRes]) => {
        if (profileRes?.data) setStats(profileRes.data);
        else if (producerData) setStats(buildLocal(producerData));
        if (followRes?.data) setIsFollowing(followRes.data.is_following);
        setLoading(false);
      });
    } else if (producerData) { setStats(buildLocal(producerData)); setLoading(false); }
    else setLoading(false);
  }, [isOpen, producerId, producerData, api, isSelf]);

  const sendChallenge = async () => {
    try {
      await api.post(`/challenges/send`, { opponent_id: producerId, game_id: 'box_office_quiz', bet_amount: 0 });
      toast.success('Sfida inviata! Il giocatore ha 10 minuti per accettare.');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore invio sfida'); }
  };

  const openChat = () => {
    window.location.href = `/chat?player=${producerId}`;
  };

  const toggleFollow = async () => {
    setFollowLoading(true);
    try {
      if (isFollowing) {
        await api.delete(`/social/follow/${producerId}`);
        setIsFollowing(false);
        toast.success('Non segui più questo produttore');
      } else {
        await api.post(`/social/follow/${producerId}`);
        setIsFollowing(true);
        toast.success('Ora segui questo produttore!');
      }
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setFollowLoading(false); }
  };

  if (!isOpen) return null;
  const s = stats || {};
  const total = (s.total_films || 0) + (s.total_series || 0) + (s.total_anime || 0);
  const badge = getBadge(total);
  const avg = s.avg_cwsv || 0;

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '12px' }}
      onClick={onClose} data-testid="producer-profile-modal">
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.85)' }} />
      <div style={{ position: 'relative', width: '100%', maxWidth: '380px', background: 'linear-gradient(180deg, #0d1117 0%, #0a0c10 100%)', borderRadius: '16px',
        border: `1px solid ${badge.border}`, overflow: 'hidden', maxHeight: '88vh', overflowY: 'auto', boxShadow: badge.glow || '0 0 30px rgba(167,139,250,0.08)' }}
        onClick={e => e.stopPropagation()}>

        {/* Header gradient */}
        <div style={{ height: '60px', background: `linear-gradient(135deg, ${badge.bg}, rgba(0,0,0,0))`, position: 'relative' }}>
          <button onClick={onClose} style={{ position: 'absolute', top: '12px', right: '12px', width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)', color: '#666', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><X size={14} /></button>
        </div>

        {loading ? (
          <div style={{ padding: '60px 0', textAlign: 'center' }}>
            <div style={{ width: '28px', height: '28px', border: '2px solid rgba(167,139,250,0.2)', borderTopColor: '#a78bfa', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }} />
          </div>
        ) : !s.nickname ? (
          <div style={{ padding: '60px 0', textAlign: 'center', color: '#555', fontSize: '12px' }}>Profilo non disponibile</div>
        ) : (
          <div style={{ padding: '0 16px 16px', marginTop: '-30px' }}>
            {/* Avatar + Name */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', marginBottom: '14px' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: `linear-gradient(135deg, ${badge.color}30, ${badge.color}10)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px', fontWeight: '900', color: badge.color, border: `2px solid ${badge.border}`, flexShrink: 0 }}>
                {(s.nickname || '?')[0]}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ fontSize: '16px', fontWeight: '900', color: '#fff', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '0.5px' }}>{s.nickname}</div>
                  {/* Follow button */}
                  {!isSelf && (
                    <button onClick={toggleFollow} disabled={followLoading} data-testid="follow-producer-btn"
                      style={{ display: 'flex', alignItems: 'center', gap: '3px', padding: '2px 8px', borderRadius: '10px',
                        background: isFollowing ? 'rgba(74,222,128,0.1)' : 'rgba(96,165,250,0.1)',
                        border: `1px solid ${isFollowing ? 'rgba(74,222,128,0.3)' : 'rgba(96,165,250,0.3)'}`,
                        color: isFollowing ? '#4ade80' : '#60a5fa', fontSize: '8px', fontWeight: 'bold', cursor: 'pointer', flexShrink: 0 }}>
                      {isFollowing ? <UserCheck size={9} /> : <UserPlus size={9} />}
                      {isFollowing ? 'Segui' : 'Segui'}
                    </button>
                  )}
                </div>
                <div style={{ fontSize: '10px', color: '#555' }}>{s.production_house_name || 'Studio indipendente'}</div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '3px', padding: '2px 10px', borderRadius: '12px',
                  background: badge.bg, border: `1px solid ${badge.border}`, fontSize: '9px', fontWeight: 'bold', color: badge.color }}>
                  <Crown size={9} /> {badge.label}
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', marginBottom: '10px' }}>
              <StatCell icon={<Film size={11} />} label="Film" value={s.total_films || 0} color="#facc15" />
              <StatCell icon={<Tv size={11} />} label="Serie TV" value={s.total_series || 0} color="#60a5fa" />
              <StatCell icon={<Sparkles size={11} />} label="Anime" value={s.total_anime || 0} color="#f472b6" />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '12px' }}>
              <StatCell icon={<Star size={11} />} label="CWSv Medio" value={avg > 0 ? (avg % 1 === 0 ? avg : avg.toFixed(1)) : '---'} color="#f0c040" />
              <StatCell icon={<TrendingUp size={11} />} label="Revenue" value={`$${fmtRev(s.total_revenue || 0)}`} color="#4ade80" />
            </div>

            {/* Best Film */}
            {s.best_film && (
              <div style={{ padding: '10px', borderRadius: '10px', background: 'linear-gradient(135deg, rgba(250,204,21,0.06), rgba(250,204,21,0.02))', border: '1px solid rgba(250,204,21,0.12)', marginBottom: '12px' }}>
                <div style={{ fontSize: '8px', color: '#4a5568', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>Miglior Produzione</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Star size={14} fill="#facc15" color="#facc15" />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#fff' }}>{s.best_film.title}</div>
                    <div style={{ fontSize: '9px', color: '#666' }}>CWSv {s.best_film.cwsv_display || '?'}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Filmography */}
            {s.filmography?.length > 0 && (
              <div style={{ marginBottom: '14px' }}>
                <div style={{ fontSize: '9px', color: '#4a5568', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px', marginBottom: '6px' }}>Filmografia</div>
                {s.filmography.slice(0, 5).map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '5px 0', borderBottom: i < 4 ? '1px solid rgba(255,255,255,0.03)' : 'none' }}>
                    <span style={{ fontSize: '9px', color: '#333', width: '14px' }}>{i + 1}.</span>
                    <span style={{ width: '14px', display: 'flex', alignItems: 'center' }}>
                      {f.type === 'anime' ? <Sparkles size={9} style={{ color: '#f472b6' }} /> : f.type === 'tv_series' ? <Tv size={9} style={{ color: '#60a5fa' }} /> : <Film size={9} style={{ color: '#facc15' }} />}
                    </span>
                    <span style={{ fontSize: '10px', color: '#ccc', flex: 1 }}>{f.title}</span>
                    <span style={{ fontSize: '10px', fontWeight: 'bold', color: (f.quality_score || 0) >= 8 ? '#facc15' : (f.quality_score || 0) >= 6 ? '#4ade80' : '#fb923c' }}>
                      {f.cwsv_display || '---'}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Action Buttons (only for OTHER players) */}
            {!isSelf && (
              <div style={{ display: 'flex', gap: '6px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px', flexWrap: 'wrap' }}>
                <button onClick={() => { onClose(); window.location.href = `/player/${producerId}/content`; }} data-testid="view-productions-btn"
                  style={{ flex: '1 1 100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px', padding: '10px', borderRadius: '10px', border: '1px solid rgba(52,211,153,0.2)', background: 'linear-gradient(135deg, rgba(52,211,153,0.08), rgba(52,211,153,0.03))', color: '#34d399', fontWeight: 'bold', fontSize: '10px', cursor: 'pointer', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px', marginBottom: '2px' }}>
                  <Film size={13} /> I Suoi Contenuti
                </button>
                <button onClick={openChat} data-testid="chat-producer-btn"
                  style={{ flex: '1 1 45%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px', padding: '10px', borderRadius: '10px', border: '1px solid rgba(96,165,250,0.2)', background: 'linear-gradient(135deg, rgba(96,165,250,0.08), rgba(96,165,250,0.03))', color: '#60a5fa', fontWeight: 'bold', fontSize: '10px', cursor: 'pointer', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px' }}>
                  <MessageCircle size={13} /> Chat
                </button>
                <button onClick={sendChallenge} data-testid="challenge-producer-btn"
                  style={{ flex: '1 1 45%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px', padding: '10px', borderRadius: '10px', border: '1px solid rgba(250,204,21,0.2)', background: 'linear-gradient(135deg, rgba(250,204,21,0.08), rgba(250,204,21,0.03))', color: '#facc15', fontWeight: 'bold', fontSize: '10px', cursor: 'pointer', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px' }}>
                  <Swords size={13} /> Sfida
                </button>
                {onCompare && (
                  <button onClick={() => { onClose(); onCompare(producerId); }} data-testid="compare-producer-btn"
                    style={{ flex: '1 1 100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px', padding: '8px', borderRadius: '10px', border: '1px solid rgba(167,139,250,0.2)', background: 'linear-gradient(135deg, rgba(167,139,250,0.06), rgba(167,139,250,0.02))', color: '#a78bfa', fontWeight: 'bold', fontSize: '10px', cursor: 'pointer', fontFamily: "'Bebas Neue', sans-serif", letterSpacing: '1px' }}>
                    <BarChart3 size={13} /> Confronta con me
                  </button>
                )}
              </div>
            )}
            {isSelf && (
              <div style={{ textAlign: 'center', padding: '8px 0', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '9px', color: '#333', fontStyle: 'italic' }}>Questo sei tu</span>
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
    <div style={{ textAlign: 'center', padding: '8px 4px', borderRadius: '10px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
      <div style={{ fontSize: '8px', color: '#4a5568', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>{icon} {label}</div>
      <div style={{ fontSize: '17px', fontWeight: '900', color, marginTop: '2px', fontFamily: "'Bebas Neue', sans-serif" }}>{value}</div>
    </div>
  );
}

function buildLocal(data) {
  return { nickname: data.nickname || '?', production_house_name: data.production_house_name || '', total_films: data.total_films_released || 0, total_series: 0, total_anime: 0, total_revenue: data.total_revenue || 0, avg_cwsv: 0, filmography: [], best_film: null };
}
