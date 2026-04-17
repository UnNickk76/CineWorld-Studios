// CineWorld — Pipeline WOW Animations
// 4 momenti: post-Idea (film roll), pre-Cast (folla), montaggio (rolling vintage), La Prima (mega event)

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API = process.env.REACT_APP_BACKEND_URL;

// ═══════════════════════════════════════
// 1. FILM ROLL — After Idea (pellicola che scorre)
// ═══════════════════════════════════════
export function FilmRollAnimation({ onComplete }) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 300),
      setTimeout(() => setPhase(2), 1500),
      setTimeout(() => setPhase(3), 3500),
      setTimeout(() => onComplete(), 4500),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 z-[99999] bg-black flex items-center justify-center overflow-hidden" data-testid="film-roll-animation">
      {/* Film strips scrolling */}
      <div className="absolute left-2 top-0 bottom-0 w-8 opacity-60" style={{ background: 'repeating-linear-gradient(180deg, #111 0px, #111 18px, #333 18px, #333 20px, #111 20px, #111 24px)', animation: 'filmScroll 1.5s linear infinite' }} />
      <div className="absolute right-2 top-0 bottom-0 w-8 opacity-60" style={{ background: 'repeating-linear-gradient(180deg, #111 0px, #111 18px, #333 18px, #333 20px, #111 20px, #111 24px)', animation: 'filmScrollReverse 2s linear infinite' }} />

      {/* Sprocket holes */}
      <div className="absolute left-0 top-0 bottom-0 w-3" style={{ background: 'repeating-linear-gradient(180deg, transparent 0px, transparent 14px, rgba(255,255,255,0.1) 14px, rgba(255,255,255,0.1) 18px, transparent 18px, transparent 24px)', animation: 'filmScroll 1.5s linear infinite' }} />
      <div className="absolute right-0 top-0 bottom-0 w-3" style={{ background: 'repeating-linear-gradient(180deg, transparent 0px, transparent 14px, rgba(255,255,255,0.1) 14px, rgba(255,255,255,0.1) 18px, transparent 18px, transparent 24px)', animation: 'filmScrollReverse 2s linear infinite' }} />

      {/* Center content */}
      <AnimatePresence mode="wait">
        {phase >= 1 && phase < 3 && (
          <motion.div key="countdown" className="text-center" initial={{ scale: 0.3, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 2, opacity: 0 }}>
            <div className="text-6xl font-black text-white" style={{ fontFamily: "'Bebas Neue', sans-serif", textShadow: '0 0 40px rgba(255,255,255,0.3)' }}>
              {phase === 1 ? '3... 2... 1...' : ''}
            </div>
          </motion.div>
        )}
        {phase === 2 && (
          <motion.div key="action" className="text-center" initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="text-4xl font-black text-yellow-400" style={{ fontFamily: "'Bebas Neue', sans-serif", textShadow: '0 0 30px rgba(250,204,21,0.5)' }}>
              AZIONE!
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Film grain */}
      <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ background: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")` }} />

      <style>{`
        @keyframes filmScroll { from { background-position-y: 0; } to { background-position-y: 24px; } }
        @keyframes filmScrollReverse { from { background-position-y: 0; } to { background-position-y: -24px; } }
      `}</style>
    </div>
  );
}


// ═══════════════════════════════════════
// 2. CROWD RUSH — Pre-Casting (folla agli studio)
// ═══════════════════════════════════════
export function CrowdRushAnimation({ onComplete, studioName }) {
  const [phase, setPhase] = useState(0);
  const canvasRef = useRef(null);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 2000),
      setTimeout(() => setPhase(3), 4000),
      setTimeout(() => onComplete(), 5500),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  // Animated crowd using canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width = 390;
    const H = canvas.height = 500;

    const COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#a855f7', '#ec4899', '#06b6d4', '#f97316'];
    const people = Array.from({ length: 40 }, () => ({
      x: Math.random() * W, y: H + Math.random() * 100,
      speed: 1 + Math.random() * 2, size: 6 + Math.random() * 4,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      sway: Math.random() * 2 - 1, phase: Math.random() * Math.PI * 2,
    }));

    let frame = 0;
    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      // Studio gate at top
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(W * 0.25, 40, W * 0.5, 80);
      ctx.fillStyle = '#facc15';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(studioName || "STUDIO'S", W / 2, 85);
      // Gate lights
      for (let i = 0; i < 6; i++) {
        const flash = Math.sin(frame * 0.1 + i) > 0.3;
        ctx.beginPath();
        ctx.arc(W * 0.28 + i * (W * 0.44 / 5), 50, flash ? 4 : 2, 0, Math.PI * 2);
        ctx.fillStyle = flash ? '#facc15' : '#666';
        ctx.fill();
      }

      // Draw people
      people.forEach(p => {
        p.y -= p.speed;
        p.x += Math.sin(frame * 0.05 + p.phase) * p.sway;

        if (p.y < 120) { p.y = H + 20; p.x = Math.random() * W; }

        // Head
        ctx.beginPath();
        ctx.arc(p.x, p.y - p.size, p.size * 0.4, 0, Math.PI * 2);
        ctx.fillStyle = '#d4a574';
        ctx.fill();
        // Body
        ctx.beginPath();
        ctx.ellipse(p.x, p.y, p.size * 0.35, p.size * 0.6, 0, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.fill();
        // Legs movement
        const legSwing = Math.sin(frame * 0.15 + p.phase) * 3;
        ctx.beginPath();
        ctx.moveTo(p.x - 2, p.y + p.size * 0.5);
        ctx.lineTo(p.x - 2 + legSwing, p.y + p.size);
        ctx.moveTo(p.x + 2, p.y + p.size * 0.5);
        ctx.lineTo(p.x + 2 - legSwing, p.y + p.size);
        ctx.strokeStyle = p.color;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });

      // Camera flashes
      if (frame % 15 === 0) {
        const fx = W * 0.15 + Math.random() * W * 0.7;
        const fy = 100 + Math.random() * 200;
        ctx.beginPath();
        ctx.arc(fx, fy, 15, 0, Math.PI * 2);
        const g = ctx.createRadialGradient(fx, fy, 0, fx, fy, 15);
        g.addColorStop(0, 'rgba(255,255,255,0.8)');
        g.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = g;
        ctx.fill();
      }

      frame++;
      requestAnimationFrame(draw);
    };
    const id = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(id);
  }, [studioName]);

  return (
    <div className="fixed inset-0 z-[99999] bg-[#0a0a0b] flex flex-col items-center justify-center overflow-hidden" data-testid="crowd-rush-animation">
      <canvas ref={canvasRef} className="w-full max-w-[390px]" style={{ height: '500px' }} />

      <AnimatePresence>
        {phase >= 1 && (
          <motion.div className="absolute bottom-20 text-center" initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
            <p className="text-2xl font-black text-yellow-400" style={{ fontFamily: "'Bebas Neue', sans-serif", textShadow: '0 0 20px rgba(250,204,21,0.4)' }}>
              {phase === 1 ? 'CASTING CALL!' : phase === 2 ? 'TUTTI VOGLIONO ENTRARE!' : 'IL CAST E PRONTO!'}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


// ═══════════════════════════════════════
// 3. MONTAGE ROLL — Final Cut (pellicola vintage + editing)
// ═══════════════════════════════════════
export function MontageRollAnimation({ onComplete }) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 400),
      setTimeout(() => setPhase(2), 2000),
      setTimeout(() => setPhase(3), 3500),
      setTimeout(() => onComplete(), 4800),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 z-[99999] bg-black flex items-center justify-center overflow-hidden" data-testid="montage-roll-animation">
      {/* Film frame borders */}
      <div className="absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-[#1a1a0e] to-transparent" />
      <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#1a1a0e] to-transparent" />

      {/* Scrolling film frames */}
      {[...Array(8)].map((_, i) => (
        <motion.div key={i} className="absolute w-[60vw] h-20 border-2 border-amber-900/40 rounded"
          style={{ left: '20vw' }}
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: [i * 100 - 100, i * 100, i * 100 + 800], opacity: [0, 0.6, 0] }}
          transition={{ duration: 3, delay: i * 0.3, repeat: Infinity, ease: 'linear' }}>
          <div className="w-full h-full bg-gradient-to-r from-amber-900/20 via-amber-800/10 to-amber-900/20" />
        </motion.div>
      ))}

      {/* Vintage grain */}
      <div className="absolute inset-0 opacity-20 pointer-events-none mix-blend-overlay"
        style={{ background: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")` }} />

      {/* Sepia vignette */}
      <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at center, transparent 40%, rgba(20,15,5,0.7) 100%)' }} />

      {/* Center text */}
      <AnimatePresence mode="wait">
        {phase === 1 && (
          <motion.div key="cut" className="text-center z-10" initial={{ scale: 3, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.5, opacity: 0 }} transition={{ type: 'spring', damping: 10 }}>
            <div className="text-5xl font-black text-amber-400" style={{ fontFamily: "'Bebas Neue', sans-serif", textShadow: '0 0 30px rgba(245,158,11,0.5)' }}>FINAL CUT</div>
          </motion.div>
        )}
        {phase === 2 && (
          <motion.div key="edit" className="text-center z-10" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <div className="text-3xl font-black text-white" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>MONTAGGIO IN CORSO...</div>
            {/* Editing bars */}
            <div className="flex gap-1 mt-4 justify-center">
              {[...Array(12)].map((_, i) => (
                <motion.div key={i} className="w-3 rounded-sm" style={{ backgroundColor: i % 3 === 0 ? '#f59e0b' : i % 3 === 1 ? '#ef4444' : '#3b82f6' }}
                  initial={{ height: 10 }}
                  animate={{ height: [10, 30 + Math.random() * 30, 10] }}
                  transition={{ duration: 0.5, delay: i * 0.08, repeat: Infinity, repeatType: 'reverse' }} />
              ))}
            </div>
          </motion.div>
        )}
        {phase === 3 && (
          <motion.div key="done" className="text-center z-10" initial={{ scale: 0.3, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring' }}>
            <div className="text-4xl font-black text-emerald-400" style={{ fontFamily: "'Bebas Neue', sans-serif", textShadow: '0 0 30px rgba(52,211,153,0.5)' }}>PRONTO!</div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Countdown marks at bottom */}
      <div className="absolute bottom-8 flex gap-3">
        {[5, 4, 3, 2, 1].map(n => (
          <motion.span key={n} className="text-2xl font-black text-amber-900/40"
            style={{ fontFamily: "'Bebas Neue', sans-serif" }}
            initial={{ opacity: 0 }} animate={{ opacity: [0, 0.8, 0] }}
            transition={{ delay: n * 0.5, duration: 0.5 }}>
            {n}
          </motion.span>
        ))}
      </div>
    </div>
  );
}


// ═══════════════════════════════════════
// 4. LA PRIMA — Mega Premiere Event
// ═══════════════════════════════════════
const CITIES = ['ROMA', 'MILANO', 'NEW YORK', 'LOS ANGELES', 'TOKYO', 'PARIGI', 'LONDRA', 'BERLINO', 'SEOUL', 'SYDNEY', 'MUMBAI', 'RIO', 'DUBAI', 'TORONTO', 'CANNES'];

export function LaPrimaAnimation({ onComplete, film }) {
  const [phase, setPhase] = useState(0);
  const [visibleCities, setVisibleCities] = useState([]);
  const posterUrl = film?.poster_url;

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 2500),
      setTimeout(() => setPhase(3), 4500),
      setTimeout(() => setPhase(4), 6500),
      setTimeout(() => onComplete(), 8000),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  // Cities appear/disappear
  useEffect(() => {
    if (phase < 2) return;
    let idx = 0;
    const interval = setInterval(() => {
      const city = CITIES[idx % CITIES.length];
      const pos = { x: 10 + Math.random() * 75, y: 15 + Math.random() * 65 };
      setVisibleCities(prev => [...prev.slice(-6), { city, pos, id: Date.now() }]);
      idx++;
    }, 400);
    return () => clearInterval(interval);
  }, [phase]);

  return (
    <div className="fixed inset-0 z-[99999] overflow-hidden" data-testid="la-prima-animation">
      {/* Background: dark red carpet gradient */}
      <div className="absolute inset-0" style={{ background: 'linear-gradient(180deg, #0a0005 0%, #1a0510 30%, #2a0a15 60%, #0a0005 100%)' }} />

      {/* Red carpet strips */}
      <motion.div className="absolute bottom-0 left-[35%] w-[30%] h-full"
        style={{ background: 'linear-gradient(180deg, transparent 0%, rgba(220,38,38,0.15) 50%, rgba(220,38,38,0.3) 100%)' }}
        initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ duration: 1, ease: 'easeOut' }} />

      {/* Golden sparkles */}
      {phase >= 1 && [...Array(20)].map((_, i) => (
        <motion.div key={`spark-${i}`} className="absolute w-1 h-1 rounded-full bg-yellow-400"
          style={{ left: `${Math.random() * 100}%`, top: `${Math.random() * 100}%` }}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: [0, 1, 0], scale: [0, 1.5, 0] }}
          transition={{ duration: 1.5, delay: i * 0.15, repeat: Infinity, repeatDelay: Math.random() * 2 }} />
      ))}

      {/* Golden flash burst */}
      {phase === 1 && (
        <motion.div className="absolute inset-0"
          style={{ background: 'radial-gradient(circle at 50% 40%, rgba(250,204,21,0.3) 0%, transparent 50%)' }}
          initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 0] }} transition={{ duration: 1.5 }} />
      )}

      {/* Poster reveal */}
      {phase >= 1 && posterUrl && (
        <motion.div className="absolute left-1/2 top-[15%] z-10"
          initial={{ x: '-50%', scale: 0, rotateY: 90 }}
          animate={{ x: '-50%', scale: 1, rotateY: 0 }}
          transition={{ delay: 0.3, type: 'spring', damping: 12 }}>
          <div className="relative">
            <img src={posterUrl.startsWith('http') ? posterUrl : `${API}${posterUrl}`} alt=""
              className="w-32 h-48 object-cover rounded-xl shadow-2xl"
              style={{ border: '3px solid rgba(250,204,21,0.5)', boxShadow: '0 0 40px rgba(250,204,21,0.3), 0 0 80px rgba(250,204,21,0.1)' }} />
            {/* Glow ring around poster */}
            <motion.div className="absolute -inset-2 rounded-2xl"
              style={{ border: '2px solid rgba(250,204,21,0.3)' }}
              animate={{ scale: [1, 1.05, 1], opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }} />
          </div>
        </motion.div>
      )}

      {/* Film title */}
      {phase >= 2 && (
        <motion.div className="absolute left-0 right-0 top-[58%] text-center z-10"
          initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ type: 'spring' }}>
          <div className="text-3xl font-black text-yellow-400 px-4" style={{ fontFamily: "'Bebas Neue', sans-serif", textShadow: '0 0 20px rgba(250,204,21,0.4)', letterSpacing: '3px' }}>
            {film?.title || 'LA PRIMA'}
          </div>
          <div className="text-xs text-red-300/60 mt-1 tracking-[4px]">PREMIERE MONDIALE</div>
        </motion.div>
      )}

      {/* Floating city names */}
      <AnimatePresence>
        {visibleCities.map(({ city, pos, id }) => (
          <motion.div key={id} className="absolute z-5 pointer-events-none"
            style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
            initial={{ opacity: 0, scale: 0.5, y: 10 }}
            animate={{ opacity: 0.7, scale: 1, y: -10 }}
            exit={{ opacity: 0, scale: 0.3, y: -30 }}
            transition={{ duration: 1.5 }}>
            <span className="text-[10px] font-bold tracking-[3px]" style={{ color: 'rgba(250,204,21,0.5)', fontFamily: "'Bebas Neue', sans-serif" }}>
              {city}
            </span>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Camera flashes */}
      {phase >= 3 && [...Array(8)].map((_, i) => (
        <motion.div key={`flash-${i}`} className="absolute rounded-full pointer-events-none"
          style={{ width: 60, height: 60, left: `${10 + Math.random() * 80}%`, top: `${20 + Math.random() * 60}%`,
            background: 'radial-gradient(circle, rgba(255,255,255,0.9) 0%, transparent 70%)' }}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: [0, 1, 0], scale: [0, 1, 0] }}
          transition={{ duration: 0.3, delay: i * 0.4, repeat: 3 }} />
      ))}

      {/* Star rating reveal */}
      {phase >= 4 && (
        <motion.div className="absolute bottom-16 left-0 right-0 text-center z-10"
          initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 200 }}>
          <div className="flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map(i => (
              <motion.span key={i} className="text-3xl"
                initial={{ y: 20, opacity: 0, rotate: -180 }}
                animate={{ y: 0, opacity: 1, rotate: 0 }}
                transition={{ delay: i * 0.15, type: 'spring' }}
                style={{ color: '#facc15', textShadow: '0 0 10px rgba(250,204,21,0.5)' }}>
                &#9733;
              </motion.span>
            ))}
          </div>
          <motion.p className="text-sm text-yellow-400/80 mt-2 tracking-[5px]"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2 }}
            style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
            IN USCITA!
          </motion.p>
        </motion.div>
      )}
    </div>
  );
}
