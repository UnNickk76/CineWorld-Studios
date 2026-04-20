// CineWorld — Pipeline WOW Animations
// 4 momenti: post-Idea (film roll), pre-Cast (folla), montaggio (rolling vintage), La Prima (mega event)

import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  const [flashes, setFlashes] = useState([]);
  const posterUrl = film?.poster_url;
  const premiereCity = film?.premiere?.city?.toUpperCase() || 'CITTA';

  // Bug fix: ref-pattern so useEffect dep is [] — prevents timer resets on
  // parent re-renders (inline arrow onComplete used to cancel all timers).
  const onCompleteRef = useRef(onComplete);
  const calledRef = useRef(false);
  onCompleteRef.current = onComplete;

  const doComplete = useCallback(() => {
    if (calledRef.current) return;
    calledRef.current = true;
    onCompleteRef.current?.();
  }, []);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 400),    // Spotlight + carpet reveal
      setTimeout(() => setPhase(2), 1800),   // Title drop + city reveal
      setTimeout(() => setPhase(3), 3300),   // Cities storm + flash burst
      setTimeout(() => setPhase(4), 5200),   // 5 stars reveal
      setTimeout(() => setPhase(5), 6800),   // Final glow + LIVE badge
      setTimeout(doComplete, 8600),
      // Safety: force-close after 15s no matter what
      setTimeout(doComplete, 15000),
    ];
    return () => timers.forEach(clearTimeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Cities bubble up
  useEffect(() => {
    if (phase < 2) return;
    let idx = 0;
    const interval = setInterval(() => {
      const city = CITIES[idx % CITIES.length];
      const pos = { x: 5 + Math.random() * 85, y: 10 + Math.random() * 75 };
      setVisibleCities(prev => [...prev.slice(-8), { city, pos, id: Date.now() + idx }]);
      idx++;
    }, 260);
    return () => clearInterval(interval);
  }, [phase]);

  // Camera flash burst during phase 3
  useEffect(() => {
    if (phase !== 3) return;
    const id = setInterval(() => {
      setFlashes(prev => [...prev.slice(-4), { id: Date.now(), x: Math.random() * 100, y: Math.random() * 100 }]);
    }, 120);
    return () => clearInterval(id);
  }, [phase]);

  return (
    <div className="fixed inset-0 z-[99999] overflow-hidden" data-testid="la-prima-animation">
      {/* Skip / close button (always tappable, even during animation) */}
      <button
        type="button"
        onClick={doComplete}
        aria-label="Chiudi animazione"
        data-testid="la-prima-skip-btn"
        className="absolute top-4 right-4 z-[100000] w-9 h-9 rounded-full bg-black/60 border border-white/25 text-white/90 flex items-center justify-center hover:bg-black/80 active:scale-95 transition"
      >
        <span className="text-xl leading-none font-bold">×</span>
      </button>

      {/* Deep red-black premiere background */}
      <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at 50% 30%, #3a0a18 0%, #1a0508 40%, #050003 100%)' }} />

      {/* Vertical spotlight beams sweeping */}
      {phase >= 1 && [0, 1, 2, 3].map(i => (
        <motion.div key={`beam-${i}`} className="absolute top-0 w-[30%] h-full origin-top"
          style={{ left: `${-10 + i * 30}%`, background: 'linear-gradient(180deg, rgba(250,204,21,0.18) 0%, transparent 80%)', transform: 'skewX(-8deg)' }}
          initial={{ opacity: 0, scaleY: 0 }}
          animate={{ opacity: [0, 0.9, 0.35, 0.7, 0.3], scaleY: 1, rotate: [0, 6, -6, 0] }}
          transition={{ duration: 4, delay: i * 0.15, repeat: Infinity, repeatType: 'mirror' }} />
      ))}

      {/* Red carpet with perspective */}
      <motion.div className="absolute bottom-0 left-1/2 -translate-x-1/2 h-[60%]"
        style={{ width: '60%', background: 'linear-gradient(180deg, transparent 0%, rgba(220,38,38,0.15) 30%, rgba(220,38,38,0.55) 100%)',
          clipPath: 'polygon(40% 0%, 60% 0%, 100% 100%, 0% 100%)' }}
        initial={{ scaleY: 0, opacity: 0 }} animate={{ scaleY: 1, opacity: 1 }} transition={{ duration: 1.2, ease: 'easeOut' }} />

      {/* Golden sparkles - increased density */}
      {phase >= 1 && [...Array(35)].map((_, i) => (
        <motion.div key={`spark-${i}`} className="absolute rounded-full"
          style={{ width: 2 + Math.random() * 3, height: 2 + Math.random() * 3,
            left: `${Math.random() * 100}%`, top: `${Math.random() * 100}%`,
            background: '#facc15', boxShadow: '0 0 8px #facc15' }}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: [0, 1, 0.2, 1, 0], scale: [0, 1.8, 0.8, 1.5, 0], y: [0, -30] }}
          transition={{ duration: 2 + Math.random() * 2, delay: i * 0.08, repeat: Infinity, repeatDelay: Math.random() * 3 }} />
      ))}

      {/* Huge initial flash */}
      {phase === 1 && (
        <motion.div className="absolute inset-0"
          style={{ background: 'radial-gradient(circle at 50% 35%, rgba(255,255,255,0.85) 0%, rgba(250,204,21,0.4) 20%, transparent 55%)' }}
          initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 0.3] }} transition={{ duration: 1.2 }} />
      )}

      {/* Poster reveal with 3D flip */}
      {phase >= 1 && posterUrl && (
        <motion.div className="absolute left-1/2 top-[12%] z-10"
          initial={{ x: '-50%', scale: 0, rotateY: 180, rotateZ: -15 }}
          animate={{ x: '-50%', scale: 1, rotateY: 0, rotateZ: 0 }}
          transition={{ delay: 0.3, type: 'spring', damping: 11, stiffness: 80 }}>
          <div className="relative">
            <img src={posterUrl.startsWith('http') ? posterUrl : `${API}${posterUrl}`} alt=""
              className="w-36 h-52 object-cover rounded-xl"
              style={{ border: '3px solid rgba(250,204,21,0.6)',
                boxShadow: '0 0 60px rgba(250,204,21,0.5), 0 0 120px rgba(220,38,38,0.3), inset 0 0 20px rgba(0,0,0,0.4)' }} />
            {/* Pulsing golden ring */}
            <motion.div className="absolute -inset-3 rounded-2xl"
              style={{ border: '2px solid rgba(250,204,21,0.5)' }}
              animate={{ scale: [1, 1.08, 1], opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.8, repeat: Infinity }} />
            <motion.div className="absolute -inset-6 rounded-3xl"
              style={{ border: '1px solid rgba(220,38,38,0.4)' }}
              animate={{ scale: [1, 1.15, 1], opacity: [0.2, 0.7, 0.2] }}
              transition={{ duration: 2.4, repeat: Infinity, delay: 0.4 }} />
          </div>
        </motion.div>
      )}

      {/* Film title */}
      {phase >= 2 && (
        <motion.div className="absolute left-0 right-0 top-[60%] text-center z-10"
          initial={{ y: 50, opacity: 0, scale: 0.6 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          transition={{ type: 'spring', damping: 10 }}>
          <div className="text-4xl font-black text-yellow-400 px-4"
            style={{ fontFamily: "'Bebas Neue', sans-serif",
              textShadow: '0 0 28px rgba(250,204,21,0.7), 0 0 56px rgba(220,38,38,0.4)',
              letterSpacing: '4px' }}>
            {film?.title || 'LA PRIMA'}
          </div>
          <motion.div className="text-[11px] text-red-300/80 mt-1.5 tracking-[6px]"
            initial={{ letterSpacing: '0px', opacity: 0 }}
            animate={{ letterSpacing: '6px', opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}>
            LA PRIMA MONDIALE · {premiereCity}
          </motion.div>
        </motion.div>
      )}

      {/* Floating city names */}
      <AnimatePresence>
        {visibleCities.map(({ city, pos, id }) => (
          <motion.div key={id} className="absolute z-5 pointer-events-none"
            style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
            initial={{ opacity: 0, scale: 0.4, y: 20 }}
            animate={{ opacity: 0.8, scale: 1, y: -15 }}
            exit={{ opacity: 0, scale: 0.2, y: -40 }}
            transition={{ duration: 1.6 }}>
            <span className="text-[11px] font-bold tracking-[3px]"
              style={{ color: city === premiereCity ? '#facc15' : 'rgba(250,204,21,0.55)',
                fontFamily: "'Bebas Neue', sans-serif",
                textShadow: city === premiereCity ? '0 0 10px #facc15' : 'none' }}>
              {city}
            </span>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Camera flashes */}
      <AnimatePresence>
        {flashes.map(f => (
          <motion.div key={f.id} className="absolute rounded-full pointer-events-none"
            style={{ width: 120, height: 120, left: `${f.x}%`, top: `${f.y}%`,
              background: 'radial-gradient(circle, rgba(255,255,255,0.95) 0%, rgba(250,204,21,0.3) 30%, transparent 70%)' }}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: [0, 1, 0], scale: [0, 1.2, 0] }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.45 }} />
        ))}
      </AnimatePresence>

      {/* Star rating reveal */}
      {phase >= 4 && (
        <motion.div className="absolute bottom-24 left-0 right-0 text-center z-10"
          initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200 }}>
          <div className="flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map(i => (
              <motion.span key={i} className="text-4xl"
                initial={{ y: 40, opacity: 0, rotate: -180, scale: 0 }}
                animate={{ y: 0, opacity: 1, rotate: 0, scale: 1 }}
                transition={{ delay: i * 0.12, type: 'spring', stiffness: 180 }}
                style={{ color: '#facc15', textShadow: '0 0 16px rgba(250,204,21,0.7)' }}>
                &#9733;
              </motion.span>
            ))}
          </div>
        </motion.div>
      )}

      {/* LIVE badge with pulsing */}
      {phase >= 5 && (
        <motion.div className="absolute bottom-10 left-0 right-0 text-center z-10"
          initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }}
          transition={{ type: 'spring', stiffness: 150 }}>
          <motion.div className="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-red-600/90 border-2 border-red-300"
            animate={{ boxShadow: ['0 0 20px rgba(220,38,38,0.5)', '0 0 40px rgba(220,38,38,0.9)', '0 0 20px rgba(220,38,38,0.5)'] }}
            transition={{ duration: 1.2, repeat: Infinity }}>
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            <span className="text-sm font-black text-white tracking-[4px]" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
              LIVE ORA
            </span>
          </motion.div>
          <p className="text-[10px] text-yellow-400/80 mt-2 tracking-[5px]" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
            24 ORE DI EVENTO ESCLUSIVO
          </p>
        </motion.div>
      )}
    </div>
  );
}
