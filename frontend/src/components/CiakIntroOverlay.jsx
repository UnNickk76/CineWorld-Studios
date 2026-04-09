import React, { useState, useEffect } from 'react';

const SCENES = ['SCENA 1', 'MOTORE', 'SCENA 2', 'SI GIRA'];

export default function CiakIntroOverlay({ onComplete }) {
  const [phase, setPhase] = useState(0); // 0=dark, 1=rolling, 2=scene, 3=light, 4=ciak, 5=done

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    const t1 = setTimeout(() => setPhase(1), 400);
    const t2 = setTimeout(() => setPhase(2), 1600);
    const t3 = setTimeout(() => setPhase(3), 3200);
    const t4 = setTimeout(() => setPhase(4), 4400);
    const t5 = setTimeout(() => { setPhase(5); }, 5200);
    const t6 = setTimeout(() => { document.body.style.overflow = ''; onComplete(); }, 5800);
    return () => { [t1,t2,t3,t4,t5,t6].forEach(clearTimeout); document.body.style.overflow = ''; };
  }, [onComplete]);

  const sceneIdx = Math.min(phase, SCENES.length - 1);

  return (
    <div className="fixed inset-0 z-[9999]" style={{ background: '#000' }}>
      {/* Film grain */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E")`,
        opacity: phase >= 1 ? 0.4 : 0,
        transition: 'opacity 0.5s',
      }} />

      {/* Vertical scan lines */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(255,255,255,0.015) 2px, rgba(255,255,255,0.015) 4px)',
        opacity: phase >= 1 ? 1 : 0,
      }} />

      {/* Film strip TOP */}
      <div className="absolute top-0 left-0 right-0 h-12 overflow-hidden" style={{ opacity: phase >= 1 ? 1 : 0, transition: 'opacity 0.6s' }}>
        <div style={{
          display: 'flex', gap: '2px',
          animation: 'filmStripScroll 3s linear infinite',
          width: '200%',
        }}>
          {Array.from({length: 40}).map((_, i) => (
            <div key={i} style={{
              width: '28px', height: '48px', flexShrink: 0,
              background: '#1a1a1a',
              borderLeft: '3px solid #333', borderRight: '3px solid #333',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <div style={{ width: '8px', height: '6px', borderRadius: '1px', background: '#444' }} />
            </div>
          ))}
        </div>
      </div>

      {/* Film strip BOTTOM */}
      <div className="absolute bottom-0 left-0 right-0 h-12 overflow-hidden" style={{ opacity: phase >= 1 ? 1 : 0, transition: 'opacity 0.6s' }}>
        <div style={{
          display: 'flex', gap: '2px',
          animation: 'filmStripScrollReverse 4s linear infinite',
          width: '200%',
        }}>
          {Array.from({length: 40}).map((_, i) => (
            <div key={i} style={{
              width: '28px', height: '48px', flexShrink: 0,
              background: '#1a1a1a',
              borderLeft: '3px solid #333', borderRight: '3px solid #333',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <div style={{ width: '8px', height: '6px', borderRadius: '1px', background: '#444' }} />
            </div>
          ))}
        </div>
      </div>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">

        {/* ROLLING text */}
        <div style={{
          fontSize: '3rem', fontWeight: 900, letterSpacing: '0.3em',
          color: '#ffeedd',
          textShadow: '0 0 30px rgba(255,200,100,0.4), 0 0 60px rgba(255,150,50,0.2)',
          opacity: phase >= 1 && phase < 4 ? 1 : 0,
          transform: phase >= 1 ? 'scale(1)' : 'scale(0.7)',
          transition: 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
          animation: phase >= 1 && phase < 4 ? 'textFlicker 0.15s infinite alternate' : 'none',
          fontFamily: 'monospace',
        }}>
          ROLLING
        </div>

        {/* Scene text */}
        <div style={{
          fontSize: '1.1rem', fontWeight: 700, letterSpacing: '0.15em',
          color: '#cc9944',
          opacity: phase >= 2 && phase < 4 ? 1 : 0,
          transform: phase >= 2 ? 'translateY(0)' : 'translateY(15px)',
          transition: 'all 0.4s ease-out',
          marginTop: '16px',
          fontFamily: 'monospace',
        }}>
          {SCENES[sceneIdx]}
        </div>

        {/* CIAK! final */}
        <div style={{
          fontSize: '4.5rem', fontWeight: 900, letterSpacing: '0.2em',
          color: '#fff',
          textShadow: '0 0 40px rgba(255,220,150,0.8), 0 0 80px rgba(255,180,80,0.5)',
          opacity: phase >= 4 && phase < 5 ? 1 : 0,
          transform: phase >= 4 ? 'scale(1)' : 'scale(1.5)',
          transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
          animation: phase === 4 ? 'ciakShake 0.1s ease-in-out 3' : 'none',
          fontFamily: 'monospace',
          position: 'absolute',
        }}>
          CIAK!
        </div>
      </div>

      {/* Warm studio light */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse at center, rgba(255,180,80,0.15) 0%, transparent 70%)',
        opacity: phase >= 3 ? 1 : 0,
        transition: 'opacity 0.8s',
      }} />

      {/* Flash on CIAK */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'rgba(255,240,200,0.6)',
        opacity: phase === 4 ? 1 : 0,
        transition: phase === 4 ? 'opacity 0.08s' : 'opacity 0.4s',
      }} />

      {/* Final white-out */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: '#000',
        opacity: phase >= 5 ? 1 : 0,
        transition: 'opacity 0.5s',
      }} />

      <style>{`
        @keyframes filmStripScroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        @keyframes filmStripScrollReverse {
          0% { transform: translateX(-50%); }
          100% { transform: translateX(0); }
        }
        @keyframes textFlicker {
          0% { opacity: 1; }
          100% { opacity: 0.88; }
        }
        @keyframes ciakShake {
          0% { transform: scale(1) translateX(0); }
          25% { transform: scale(1) translateX(-3px); }
          50% { transform: scale(1) translateX(3px); }
          75% { transform: scale(1) translateX(-2px); }
          100% { transform: scale(1) translateX(0); }
        }
      `}</style>
    </div>
  );
}
