import React, { useState, useEffect, useMemo } from 'react';

/**
 * LampoReleaseOverlay
 * Wow event mostrato dopo che il giocatore conferma il rilascio LAMPO.
 *  • Schermo nero con grain
 *  • 3 lampi SVG che attraversano lo schermo
 *  • "LAMPO!" gigante che esplode al centro con shockwave
 *  • Sottotitolo dinamico (AL CINEMA / IN TV / PROGRAMMATO PER …)
 *  • Particelle dorate
 *  • ~3.5s di durata
 *
 * Props:
 *  - mode: 'immediate' | 'scheduled'
 *  - contentType: 'film' | 'tv_series' | 'anime'
 *  - releaseAt: ISO date string (solo per scheduled)
 *  - onComplete: callback alla fine
 */
export default function LampoReleaseOverlay({ mode = 'immediate', contentType = 'film', releaseAt, onComplete }) {
  const [phase, setPhase] = useState(0); // 0=dark, 1=bolts, 2=boom, 3=tagline, 4=fade
  const [done, setDone] = useState(false);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    const t1 = setTimeout(() => setPhase(1), 200);
    const t2 = setTimeout(() => setPhase(2), 900);
    const t3 = setTimeout(() => setPhase(3), 1700);
    const t4 = setTimeout(() => setPhase(4), 3000);
    const t5 = setTimeout(() => { setDone(true); document.body.style.overflow = ''; onComplete?.(); }, 3600);
    return () => { [t1, t2, t3, t4, t5].forEach(clearTimeout); document.body.style.overflow = ''; };
  }, [onComplete]);

  // Sottotitolo dinamico
  const tagline = useMemo(() => {
    if (mode === 'scheduled' && releaseAt) {
      try {
        const d = new Date(releaseAt);
        const date = d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric' });
        const time = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
        return contentType === 'film' ? `IN TUTTI I CINEMA DAL ${date} · ${time}` : `IN TUTTE LE TV DAL ${date} · ${time}`;
      } catch {
        return contentType === 'film' ? 'IN ARRIVO AL CINEMA' : 'IN ARRIVO IN TV';
      }
    }
    return contentType === 'film' ? 'AL CINEMA!' : (contentType === 'anime' ? 'IN TV!' : 'IN TV!');
  }, [mode, contentType, releaseAt]);

  // Pre-genera particelle dorate (staticamente sparse)
  const sparks = useMemo(() => Array.from({ length: 28 }).map((_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 0.8,
    duration: 1.5 + Math.random() * 1.2,
    size: 2 + Math.random() * 4,
    drift: (Math.random() - 0.5) * 30,
  })), []);

  if (done) return null;

  return (
    <div className="fixed inset-0 z-[9999]" style={{ background: '#000' }} data-testid="lampo-release-overlay">
      {/* Film grain */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.1'/%3E%3C/svg%3E")`,
        opacity: 0.45,
      }} />

      {/* Vignette */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.85) 100%)',
      }} />

      {/* ⚡ Lightning bolts SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none"
        style={{ opacity: phase >= 1 ? 1 : 0, transition: 'opacity 0.2s', filter: 'drop-shadow(0 0 4px #fbbf24) drop-shadow(0 0 12px #f97316)' }}>
        <defs>
          <linearGradient id="boltGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fff8c4" />
            <stop offset="50%" stopColor="#fbbf24" />
            <stop offset="100%" stopColor="#f97316" />
          </linearGradient>
        </defs>
        {/* Bolt 1: top-left → center */}
        <polyline points="10,5 25,28 18,40 35,55 28,68 45,80"
          fill="none" stroke="url(#boltGrad)" strokeWidth="0.6" strokeLinecap="round" strokeLinejoin="round"
          style={{
            strokeDasharray: 200, strokeDashoffset: phase >= 1 ? 0 : 200,
            transition: 'stroke-dashoffset 0.45s cubic-bezier(0.6, 0, 0.4, 1)',
            opacity: phase < 4 ? 1 : 0,
          }} />
        {/* Bolt 2: top-right → bottom-left */}
        <polyline points="92,8 78,22 86,35 70,48 78,62 60,75 68,90"
          fill="none" stroke="url(#boltGrad)" strokeWidth="0.55" strokeLinecap="round" strokeLinejoin="round"
          style={{
            strokeDasharray: 220, strokeDashoffset: phase >= 1 ? 0 : 220,
            transition: 'stroke-dashoffset 0.55s cubic-bezier(0.6, 0, 0.4, 1) 0.15s',
            opacity: phase < 4 ? 1 : 0,
          }} />
        {/* Bolt 3: bottom-center → top */}
        <polyline points="50,95 42,80 56,68 48,52 60,38 50,22 58,5"
          fill="none" stroke="url(#boltGrad)" strokeWidth="0.5" strokeLinecap="round" strokeLinejoin="round"
          style={{
            strokeDasharray: 200, strokeDashoffset: phase >= 1 ? 0 : 200,
            transition: 'stroke-dashoffset 0.5s cubic-bezier(0.6, 0, 0.4, 1) 0.3s',
            opacity: phase < 4 ? 1 : 0,
          }} />
      </svg>

      {/* ⚡ Flash bianco al phase 2 (boom) */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(circle at center, rgba(255,240,180,0.85) 0%, rgba(255,160,40,0.3) 30%, transparent 60%)',
        opacity: phase === 2 ? 1 : 0,
        transition: phase === 2 ? 'opacity 0.15s' : 'opacity 0.6s',
      }} />

      {/* Shockwave ring */}
      {phase >= 2 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div style={{
            width: '20px', height: '20px', borderRadius: '50%',
            border: '3px solid rgba(251,191,36,0.7)',
            animation: 'lampoShockwave 1.4s ease-out forwards',
          }} />
        </div>
      )}

      {/* Center boom */}
      <div className="absolute inset-0 flex flex-col items-center justify-center px-4 text-center"
        style={{ animation: phase >= 2 ? 'lampoCameraShake 0.5s ease-out' : 'none' }}>
        {/* LAMPO! gigante */}
        <div style={{
          fontFamily: "'Bebas Neue', system-ui, sans-serif",
          fontSize: 'clamp(4rem, 18vw, 9rem)',
          fontWeight: 900,
          letterSpacing: '0.05em',
          background: 'linear-gradient(180deg, #fff8c4 0%, #fbbf24 45%, #f97316 100%)',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          color: 'transparent',
          textShadow: '0 0 40px rgba(251,191,36,0.7)',
          filter: 'drop-shadow(0 4px 12px rgba(249,115,22,0.6))',
          opacity: phase >= 2 ? 1 : 0,
          transform: phase >= 2 ? 'scale(1)' : 'scale(0.3)',
          transition: 'all 0.45s cubic-bezier(0.16, 1, 0.3, 1)',
          lineHeight: 1,
        }}>
          LAMPO!
        </div>

        {/* Tagline */}
        <div style={{
          marginTop: '24px',
          fontFamily: "'Bebas Neue', system-ui, sans-serif",
          fontSize: 'clamp(1.1rem, 4vw, 1.8rem)',
          fontWeight: 700,
          letterSpacing: '0.18em',
          color: '#fff8e7',
          textShadow: '0 0 18px rgba(251,191,36,0.55)',
          opacity: phase >= 3 ? 1 : 0,
          transform: phase >= 3 ? 'translateY(0)' : 'translateY(12px)',
          transition: 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        }}>
          {tagline}
        </div>

        {/* Mini hint scheduled */}
        {mode === 'scheduled' && phase >= 3 && (
          <div style={{
            marginTop: '12px',
            fontSize: '0.75rem',
            color: 'rgba(251,191,36,0.7)',
            fontStyle: 'italic',
            letterSpacing: '0.05em',
            opacity: phase >= 3 ? 1 : 0,
            transition: 'opacity 0.4s 0.2s',
          }}>
            ✨ L'attesa creerà hype: spettatori extra ti aspettano.
          </div>
        )}
      </div>

      {/* Sparks (particles) */}
      {phase >= 2 && phase < 4 && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {sparks.map(s => (
            <div key={s.id} style={{
              position: 'absolute',
              left: `${s.left}%`,
              bottom: '-10px',
              width: `${s.size}px`,
              height: `${s.size}px`,
              borderRadius: '50%',
              background: 'radial-gradient(circle, #fff8c4 0%, #fbbf24 50%, transparent 100%)',
              boxShadow: '0 0 8px #fbbf24',
              animation: `lampoSparkRise ${s.duration}s ease-out ${s.delay}s forwards`,
              ['--drift']: `${s.drift}px`,
            }} />
          ))}
        </div>
      )}

      {/* Final fade */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: '#000',
        opacity: phase >= 4 ? 1 : 0,
        transition: 'opacity 0.5s',
      }} />

      <style>{`
        @keyframes lampoShockwave {
          0% { width: 20px; height: 20px; opacity: 0.8; border-width: 4px; }
          100% { width: 1200px; height: 1200px; opacity: 0; border-width: 1px; }
        }
        @keyframes lampoCameraShake {
          0%   { transform: translate(0, 0); }
          15%  { transform: translate(-4px, 2px); }
          30%  { transform: translate(4px, -3px); }
          45%  { transform: translate(-3px, 3px); }
          60%  { transform: translate(2px, -2px); }
          75%  { transform: translate(-1px, 1px); }
          100% { transform: translate(0, 0); }
        }
        @keyframes lampoSparkRise {
          0%   { transform: translateY(0) translateX(0); opacity: 0; }
          15%  { opacity: 1; }
          100% { transform: translateY(-110vh) translateX(var(--drift)); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
