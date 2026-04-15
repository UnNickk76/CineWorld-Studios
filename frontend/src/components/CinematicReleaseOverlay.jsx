import React, { useState, useEffect, useCallback, useRef } from 'react';

const GENRE_COLORS = {
  horror: '#8b0000', comedy: '#d4a017', drama: '#1e3a8a', thriller: '#115e59',
  action: '#c2410c', sci_fi: '#0284c7', fantasy: '#7c3aed', historical: '#b45309',
  romance: '#db2777', animation: '#0891b2', anime: '#0891b2', noir: '#374151',
  war: '#78350f', crime: '#7f1d1d', documentary: '#94a3b8', default: '#d4a017',
};

export default function CinematicReleaseOverlay({ film, releaseType, onComplete }) {
  const [phase, setPhase] = useState(0);
  const [exiting, setExiting] = useState(false);
  const overlayRef = useRef(null);
  const color = GENRE_COLORS[film?.genre] || GENRE_COLORS.default;
  const filmTitle = film?.title || 'Film';
  const posterUrl = film?.poster_url;
  const productionHouse = film?.production_house_name || 'STUDIO INDIPENDENTE';
  const isLaPrima = releaseType === 'premiere';

  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    const doExit = () => {
      setExiting(true);
      setTimeout(() => {
        document.body.style.overflow = '';
        onCompleteRef.current?.();
      }, 600);
    };
    const t = [
      setTimeout(() => setPhase(1), 300),
      setTimeout(() => setPhase(2), 1100),
      setTimeout(() => setPhase(3), 1900),
      setTimeout(() => setPhase(4), 2700),
      setTimeout(() => setPhase(5), 3500),
      setTimeout(() => setPhase(6), 4400),
      setTimeout(() => setPhase(7), 5300),
      setTimeout(() => setPhase(8), 5900),
      setTimeout(doExit, 6500),
    ];
    return () => { t.forEach(clearTimeout); document.body.style.overflow = ''; };
  }, []); // No dependencies — runs once on mount only

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[99999]"
      style={{
        background: '#000',
        opacity: exiting ? 0 : 1,
        transition: exiting ? 'opacity 0.6s ease-out' : 'none',
      }}
      data-testid="cinematic-release-overlay"
    >
      {/* GRAIN — subtle film texture */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 1,
        opacity: phase >= 1 ? 0.4 : 0, transition: 'opacity 0.5s',
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='0.9' numOctaves='4' type='fractalNoise'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E")`,
        animation: phase >= 1 ? 'grainShift 0.15s steps(3) infinite' : 'none',
      }} />

      {/* VERTICAL SCAN LINES */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 1,
        backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(255,255,255,0.008) 2px, rgba(255,255,255,0.008) 4px)',
        opacity: phase >= 2 ? 1 : 0,
      }} />

      {/* ═══ PHASE 1-2: PROJECTOR ═══ */}
      <div style={{
        position: 'absolute', bottom: '2%', left: '3%', width: '90px', height: '90px',
        zIndex: 10,
        opacity: phase >= 1 ? 1 : 0,
        transform: phase >= 1 ? 'translateY(0) scale(1)' : 'translateY(20px) scale(0.8)',
        transition: 'all 0.7s cubic-bezier(0.16,1,0.3,1)',
        animation: phase >= 2 && phase < 8 ? 'mechVibrate 0.06s infinite alternate' : 'none',
      }}>
        {/* Projector body */}
        <div style={{
          width: '100%', height: '100%', position: 'relative',
          filter: `drop-shadow(0 0 15px ${color}) drop-shadow(0 0 30px ${color}40)`,
        }}>
          <img src="/assets/projector.png" alt=""
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            onError={(e) => { e.target.style.display = 'none'; }}
          />
          {/* Lens glow */}
          <div style={{
            position: 'absolute', top: '25%', right: '-5%',
            width: '20px', height: '20px', borderRadius: '50%',
            background: phase >= 2 ? `radial-gradient(circle, ${color}, transparent)` : 'transparent',
            opacity: phase >= 2 ? 1 : 0,
            transition: 'all 0.3s',
            boxShadow: phase >= 2 ? `0 0 20px ${color}, 0 0 40px ${color}80` : 'none',
            animation: phase >= 2 ? 'lensFlicker 0.12s infinite alternate' : 'none',
          }} />
          {/* Reels rotation hint */}
          <div style={{
            position: 'absolute', top: '10%', left: '15%',
            width: '22px', height: '22px', borderRadius: '50%',
            border: `2px solid ${color}60`,
            animation: phase >= 1 ? 'reelSpin 2s linear infinite' : 'none',
          }}>
            <div style={{ position: 'absolute', top: '50%', left: '50%', width: '8px', height: '1px', background: `${color}80`, transform: 'translate(-50%,-50%)' }} />
          </div>
        </div>
        {/* Genre color aura */}
        <div style={{
          position: 'absolute', inset: '-30px', borderRadius: '50%',
          background: `radial-gradient(circle, ${color}25 0%, transparent 65%)`,
          animation: 'auraPulse 2s ease-in-out infinite',
          pointerEvents: 'none',
        }} />
      </div>

      {/* ═══ PHASE 2: LIGHT BEAM ═══ */}
      <div style={{
        position: 'absolute', bottom: '12%', left: '8%',
        width: '250%', height: '250%',
        opacity: phase >= 2 ? 1 : 0,
        transition: 'opacity 0.8s',
        background: `linear-gradient(315deg, transparent 25%, ${color}08 38%, ${color}12 42%, ${color}06 48%, transparent 60%)`,
        pointerEvents: 'none', zIndex: 2,
        animation: phase >= 2 && phase < 8 ? 'beamFlick 3s ease-in-out infinite' : 'none',
      }} />

      {/* Beam dust particles */}
      {phase >= 2 && phase < 8 && (
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden', zIndex: 3 }}>
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} style={{
              position: 'absolute',
              width: `${1 + (i % 3)}px`, height: `${1 + (i % 3)}px`, borderRadius: '50%',
              background: i % 2 === 0 ? `${color}90` : 'rgba(255,255,255,0.4)',
              left: `${10 + i * 7}%`, top: `${75 - i * 6}%`,
              animation: `dustDrift ${2 + (i % 4) * 0.5}s ease-in-out infinite alternate`,
              animationDelay: `${i * 0.15}s`,
            }} />
          ))}
        </div>
      )}

      {/* ═══ PHASE 3: CINEMA SCREEN ═══ */}
      <div style={{
        position: 'absolute',
        top: '6%', left: '50%', transform: 'translateX(-50%)',
        width: '82%', maxWidth: '310px',
        aspectRatio: '3/4',
        borderRadius: '3px',
        background: phase >= 2 ? '#ede8dc' : '#0a0a0a',
        boxShadow: phase >= 2
          ? `0 0 50px ${color}20, 0 0 100px ${color}10, inset 0 0 40px rgba(0,0,0,0.25)`
          : 'none',
        transition: 'all 0.7s cubic-bezier(0.16,1,0.3,1)',
        overflow: 'hidden',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 5,
      }}>
        {/* Screen grain overlay */}
        <div style={{
          position: 'absolute', inset: 0, zIndex: 6, pointerEvents: 'none',
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 128 128' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='g'%3E%3CfeTurbulence baseFrequency='1.5' numOctaves='3' type='fractalNoise'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)' opacity='0.03'/%3E%3C/svg%3E")`,
          animation: phase >= 2 ? 'scrFlicker 0.08s steps(2) infinite' : 'none',
        }} />

        {/* Film scratches */}
        {phase >= 3 && phase <= 5 && (
          <>
            <div style={{ position: 'absolute', left: '22%', top: 0, width: '1px', height: '100%', background: 'rgba(0,0,0,0.07)', zIndex: 7, animation: 'scratchDrift 0.5s linear infinite' }} />
            <div style={{ position: 'absolute', left: '67%', top: 0, width: '1px', height: '100%', background: 'rgba(0,0,0,0.05)', zIndex: 7, animation: 'scratchDrift 0.7s linear infinite reverse' }} />
          </>
        )}

        {/* ═══ COUNTDOWN 3-2-1 ═══ */}
        {phase >= 3 && phase <= 5 && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {/* Concentric circles */}
            <div style={{
              width: '130px', height: '130px', borderRadius: '50%',
              border: '2.5px solid #555', position: 'relative',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <div style={{ position: 'absolute', width: '100px', height: '100px', borderRadius: '50%', border: '1.5px solid #777' }} />
              <div style={{ position: 'absolute', width: '70px', height: '70px', borderRadius: '50%', border: '1px solid #999' }} />
              {/* Cross hairs */}
              <div style={{ position: 'absolute', width: '1px', height: '100%', background: '#555' }} />
              <div style={{ position: 'absolute', width: '100%', height: '1px', background: '#555' }} />
              {/* Number */}
              <span style={{
                fontSize: '3.5rem', fontWeight: 900, color: '#2a2a2a',
                fontFamily: '"Courier New", monospace',
                animation: 'countSlam 0.25s cubic-bezier(0.34,1.56,0.64,1)',
                textShadow: '0 2px 4px rgba(0,0,0,0.2)',
              }}
                key={phase}
              >
                {phase === 3 ? '3' : phase === 4 ? '2' : '1'}
              </span>
            </div>
          </div>
        )}

        {/* Flash at "1" */}
        {phase === 5 && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 9,
            background: 'rgba(255,255,240,0.6)',
            animation: 'projFlash 0.4s ease-out forwards',
          }} />
        )}

        {/* ═══ PHASE 6: POSTER PROJECTION ═══ */}
        {phase >= 6 && (
          <div style={{
            position: 'absolute', inset: '3%', zIndex: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            opacity: phase >= 6 ? 1 : 0,
            transform: phase >= 6 ? 'scale(1)' : 'scale(0.92)',
            transition: 'all 0.7s cubic-bezier(0.16,1,0.3,1)',
          }}>
            {posterUrl ? (
              <img src={posterUrl} alt={filmTitle} style={{
                width: '100%', height: '100%', objectFit: 'cover', borderRadius: '2px',
                filter: 'contrast(1.08) saturate(1.15)',
                boxShadow: `0 0 30px ${color}30`,
              }} />
            ) : (
              <div style={{
                width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: `linear-gradient(160deg, ${color}30, #111, ${color}15)`,
                borderRadius: '2px',
              }}>
                <span style={{
                  fontSize: '1.6rem', fontWeight: 900, color: '#ffd700',
                  textAlign: 'center', padding: '20px', fontFamily: 'Georgia, serif',
                  textShadow: `0 0 20px ${color}80`,
                  lineHeight: 1.2,
                }}>
                  {filmTitle}
                </span>
              </div>
            )}
            {/* Edge glow on poster */}
            <div style={{
              position: 'absolute', inset: '-2px', borderRadius: '3px',
              boxShadow: `inset 0 0 15px ${color}20, 0 0 25px ${color}15`,
              pointerEvents: 'none',
            }} />
          </div>
        )}
      </div>

      {/* ═══ PHASE 7: CINEMATIC TITLES ═══ */}
      <div style={{
        position: 'absolute', bottom: '14%', left: 0, right: 0,
        textAlign: 'center', zIndex: 15,
        opacity: phase >= 7 ? 1 : 0,
        transform: phase >= 7 ? 'translateY(0)' : 'translateY(15px)',
        transition: 'all 0.6s cubic-bezier(0.16,1,0.3,1)',
      }}>
        {isLaPrima && (
          <p style={{
            fontSize: '0.55rem', letterSpacing: '0.35em', color: '#d4a017',
            fontWeight: 700, marginBottom: '10px', textTransform: 'uppercase',
          }}>
            LA PRIMA
          </p>
        )}
        <p style={{
          fontSize: '0.5rem', letterSpacing: '0.25em', color: '#777',
          fontWeight: 400, marginBottom: '6px',
        }}>
          UNA PRODUZIONE DI
        </p>
        <p style={{
          fontSize: '1.3rem', fontWeight: 900, color: '#ffd700',
          letterSpacing: '0.06em', fontFamily: 'Georgia, serif',
          textShadow: `0 0 25px ${color}50, 0 2px 8px rgba(0,0,0,0.5)`,
          marginBottom: '8px', padding: '0 10px',
        }}>
          {filmTitle}
        </p>
        <p style={{
          fontSize: '0.6rem', fontWeight: 600, color: '#4a90d9',
          letterSpacing: '0.18em',
        }}>
          {productionHouse}
        </p>
      </div>

      {/* ═══ PHASE 8: PHOTOGRAPHER FLASHES ═══ */}
      {phase === 8 && (
        <>
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 20,
            background: `radial-gradient(circle at 30% 50%, rgba(255,245,210,${isLaPrima ? 0.45 : 0.3}), transparent 60%)`,
            animation: 'photoFlash 0.5s ease-out forwards',
          }} />
          {isLaPrima && (
            <div style={{
              position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 20,
              background: 'radial-gradient(circle at 70% 40%, rgba(255,255,255,0.25), transparent 55%)',
              animation: 'photoFlash 0.4s ease-out 0.15s forwards',
            }} />
          )}
        </>
      )}

      {/* ═══ CSS KEYFRAMES ═══ */}
      <style>{`
        @keyframes grainShift {
          0% { transform: translate(0,0); }
          33% { transform: translate(-1px,1px); }
          66% { transform: translate(1px,-1px); }
          100% { transform: translate(0,0); }
        }
        @keyframes mechVibrate {
          0% { transform: translateY(0) rotate(0deg); }
          100% { transform: translateY(-0.4px) rotate(0.25deg); }
        }
        @keyframes lensFlicker {
          0% { opacity: 0.85; }
          100% { opacity: 1; }
        }
        @keyframes reelSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes auraPulse {
          0%, 100% { opacity: 0.4; transform: scale(1); }
          50% { opacity: 0.7; transform: scale(1.08); }
        }
        @keyframes beamFlick {
          0%, 100% { opacity: 0.85; }
          25% { opacity: 1; }
          50% { opacity: 0.7; }
          75% { opacity: 0.95; }
        }
        @keyframes dustDrift {
          0% { transform: translate(0, 0); opacity: 0.15; }
          100% { transform: translate(4px, -6px); opacity: 0.45; }
        }
        @keyframes scrFlicker {
          0% { opacity: 0.025; }
          100% { opacity: 0.05; }
        }
        @keyframes scratchDrift {
          0% { transform: translateX(0); }
          100% { transform: translateX(2px); }
        }
        @keyframes countSlam {
          0% { transform: scale(1.4); opacity: 0.4; }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes projFlash {
          0% { opacity: 0.6; }
          100% { opacity: 0; }
        }
        @keyframes photoFlash {
          0% { opacity: 1; }
          100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
