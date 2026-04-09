import React, { useState, useEffect, useCallback } from 'react';

const GENRE_COLORS = {
  horror: '#8b0000', comedy: '#d4a017', drama: '#1e3a8a', thriller: '#115e59',
  action: '#c2410c', sci_fi: '#0284c7', fantasy: '#7c3aed', historical: '#b45309',
  romance: '#db2777', animation: '#0891b2', anime: '#0891b2', documentary: '#94a3b8',
  default: '#d4a017',
};

export default function CinematicReleaseOverlay({ filmTitle, productionHouseName, posterUrl, genre, releaseType, onComplete }) {
  const [phase, setPhase] = useState(0);
  const color = GENRE_COLORS[genre] || GENRE_COLORS.default;

  const done = useCallback(() => {
    document.body.style.overflow = '';
    onComplete();
  }, [onComplete]);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    const timers = [
      setTimeout(() => setPhase(1), 300),    // projector on
      setTimeout(() => setPhase(2), 1000),   // beam + countdown 3
      setTimeout(() => setPhase(3), 1700),   // countdown 2
      setTimeout(() => setPhase(4), 2400),   // countdown 1
      setTimeout(() => setPhase(5), 3100),   // poster appears
      setTimeout(() => setPhase(6), 4200),   // titles
      setTimeout(() => setPhase(7), 5200),   // flash climax
      setTimeout(() => done(), 5800),        // exit
    ];
    return () => { timers.forEach(clearTimeout); document.body.style.overflow = ''; };
  }, [done]);

  const isLaPrima = releaseType === 'premiere';

  return (
    <div className="fixed inset-0 z-[9999]" style={{ background: '#000' }}>
      {/* Film grain overlay */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='g'%3E%3CfeTurbulence baseFrequency='0.8' numOctaves='4' type='fractalNoise'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)' opacity='0.06'/%3E%3C/svg%3E")`,
        opacity: phase >= 1 ? 0.5 : 0, transition: 'opacity 0.5s',
      }} />

      {/* Vertical scan lines */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 1px, rgba(255,255,255,0.01) 1px, rgba(255,255,255,0.01) 3px)',
        opacity: phase >= 2 ? 1 : 0,
      }} />

      {/* Projector (bottom-left) */}
      <div style={{
        position: 'absolute', bottom: '-10px', left: '10px', width: '100px', height: '100px',
        opacity: phase >= 1 ? 1 : 0,
        transform: phase >= 1 ? 'translateY(0)' : 'translateY(30px)',
        transition: 'all 0.8s cubic-bezier(0.16,1,0.3,1)',
        filter: `drop-shadow(0 0 20px ${color}) drop-shadow(0 0 40px ${color}50)`,
        animation: phase >= 1 && phase < 7 ? 'projectorVibrate 0.08s infinite alternate' : 'none',
      }}>
        <img src="/assets/projector.png" alt="" style={{ width: '100%', height: '100%', objectFit: 'contain' }}
          onError={(e) => { e.target.style.display = 'none'; }} />
        {/* Genre color glow */}
        <div style={{
          position: 'absolute', inset: '-20px', borderRadius: '50%',
          background: `radial-gradient(circle, ${color}40 0%, transparent 70%)`,
          animation: 'projectorPulse 1.5s ease-in-out infinite',
        }} />
      </div>

      {/* Light beam from projector to screen */}
      <div style={{
        position: 'absolute', bottom: '60px', left: '60px',
        width: '200%', height: '200%',
        opacity: phase >= 2 ? 0.3 : 0,
        transition: 'opacity 0.8s',
        background: `linear-gradient(315deg, transparent 30%, ${color}15 45%, ${color}08 55%, transparent 70%)`,
        pointerEvents: 'none',
      }} />

      {/* Beam particles */}
      {phase >= 2 && phase < 7 && (
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
          {Array.from({length: 8}).map((_, i) => (
            <div key={i} style={{
              position: 'absolute',
              width: '2px', height: '2px', borderRadius: '50%',
              background: `${color}`,
              left: `${15 + i * 10}%`, top: `${70 - i * 8}%`,
              opacity: 0.4,
              animation: `particleFloat ${1.5 + i * 0.3}s ease-in-out infinite alternate`,
              animationDelay: `${i * 0.2}s`,
            }} />
          ))}
        </div>
      )}

      {/* Screen area (center-top) */}
      <div style={{
        position: 'absolute', top: '8%', left: '50%', transform: 'translateX(-50%)',
        width: '80%', maxWidth: '320px',
        aspectRatio: '3/4',
        background: phase >= 2 ? '#f5f0e8' : '#111',
        borderRadius: '4px',
        boxShadow: phase >= 2 ? `0 0 60px ${color}30, inset 0 0 30px rgba(0,0,0,0.3)` : 'none',
        transition: 'all 0.6s',
        overflow: 'hidden',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {/* Screen grain */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='s'%3E%3CfeTurbulence baseFrequency='1.2' numOctaves='3' type='fractalNoise'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23s)' opacity='0.04'/%3E%3C/svg%3E")`,
          pointerEvents: 'none', zIndex: 5,
          animation: 'screenFlicker 0.1s infinite alternate',
        }} />

        {/* Countdown numbers */}
        {phase >= 2 && phase <= 4 && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 3,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
          }}>
            {/* Circle */}
            <div style={{
              width: '120px', height: '120px', borderRadius: '50%',
              border: '3px solid #555', display: 'flex', alignItems: 'center', justifyContent: 'center',
              position: 'relative',
            }}>
              {/* Cross lines */}
              <div style={{ position: 'absolute', width: '1px', height: '100%', background: '#555' }} />
              <div style={{ position: 'absolute', width: '100%', height: '1px', background: '#555' }} />
              {/* Number */}
              <span style={{
                fontSize: '4rem', fontWeight: 900, color: '#333', fontFamily: 'monospace',
                animation: 'countPop 0.3s ease-out',
              }}>
                {phase === 2 ? '3' : phase === 3 ? '2' : '1'}
              </span>
            </div>
            {/* Scratches */}
            <div style={{ position: 'absolute', top: '20%', left: '10%', width: '1px', height: '60%', background: '#00000015', transform: 'rotate(2deg)' }} />
            <div style={{ position: 'absolute', top: '10%', right: '20%', width: '1px', height: '40%', background: '#00000010', transform: 'rotate(-1deg)' }} />
          </div>
        )}

        {/* Poster projection */}
        {phase >= 5 && (
          <div style={{
            position: 'absolute', inset: '4%', zIndex: 4,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            opacity: phase >= 5 ? 1 : 0,
            transform: phase >= 5 ? 'scale(1)' : 'scale(0.9)',
            transition: 'all 0.6s cubic-bezier(0.16,1,0.3,1)',
          }}>
            {posterUrl ? (
              <img src={posterUrl} alt={filmTitle} style={{
                width: '100%', height: '100%', objectFit: 'cover', borderRadius: '2px',
                filter: 'contrast(1.05) saturate(1.1)',
              }} />
            ) : (
              <div style={{
                width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: `linear-gradient(135deg, ${color}30, #1a1a1a)`,
                borderRadius: '2px',
              }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 900, color: '#ffd700', textAlign: 'center', padding: '20px', fontFamily: 'serif' }}>
                  {filmTitle}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Titles below screen */}
      <div style={{
        position: 'absolute', bottom: '18%', left: 0, right: 0,
        textAlign: 'center',
        opacity: phase >= 6 ? 1 : 0,
        transform: phase >= 6 ? 'translateY(0)' : 'translateY(20px)',
        transition: 'all 0.6s cubic-bezier(0.16,1,0.3,1)',
      }}>
        {isLaPrima && (
          <p style={{
            fontSize: '0.6rem', letterSpacing: '0.3em', color: '#d4a017',
            fontWeight: 700, marginBottom: '8px', textTransform: 'uppercase',
          }}>
            LA PRIMA
          </p>
        )}
        <p style={{
          fontSize: '0.55rem', letterSpacing: '0.2em', color: '#999',
          fontWeight: 400, marginBottom: '4px',
        }}>
          UNA PRODUZIONE DI
        </p>
        <p style={{
          fontSize: '1.4rem', fontWeight: 900, color: '#ffd700',
          letterSpacing: '0.08em', fontFamily: 'serif',
          textShadow: `0 0 20px ${color}60`,
          marginBottom: '6px',
        }}>
          {filmTitle}
        </p>
        <p style={{
          fontSize: '0.65rem', fontWeight: 600, color: '#4a90d9',
          letterSpacing: '0.15em',
        }}>
          {productionHouseName || 'STUDIO INDIPENDENTE'}
        </p>
      </div>

      {/* Flash on climax */}
      {phase === 7 && (
        <>
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            background: 'rgba(255,240,200,0.4)',
            animation: 'flashBurst 0.6s ease-out forwards',
          }} />
          {isLaPrima && (
            <div style={{
              position: 'absolute', inset: 0, pointerEvents: 'none',
              background: 'rgba(255,255,255,0.15)',
              animation: 'flashBurst 0.4s ease-out 0.2s forwards',
            }} />
          )}
        </>
      )}

      <style>{`
        @keyframes projectorVibrate {
          0% { transform: translateY(0) rotate(0deg); }
          100% { transform: translateY(-0.5px) rotate(0.3deg); }
        }
        @keyframes projectorPulse {
          0%, 100% { opacity: 0.5; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.05); }
        }
        @keyframes particleFloat {
          0% { transform: translate(0, 0); opacity: 0.2; }
          100% { transform: translate(5px, -8px); opacity: 0.5; }
        }
        @keyframes screenFlicker {
          0% { opacity: 0.03; }
          100% { opacity: 0.06; }
        }
        @keyframes countPop {
          0% { transform: scale(1.3); opacity: 0.5; }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes flashBurst {
          0% { opacity: 1; }
          100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
