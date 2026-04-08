/* ===================================================================
   FLIPPER PRO — Minigiochi Pro Flipper Cinematografico
   Canvas physics + PNG overlay per leve e pallina
   =================================================================== */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import './flipperPro.css';

const W = 360, H = 600, BALL_R = 10, GRAV = 0.32;
const FLIPPER_LEN = 72, FLIPPER_W = 14, FLIPPER_REST = 0.35, FLIPPER_UP = -0.55;
const LF_X = 105, RF_X = 255, F_Y = H - 85;

function initTargets() {
  return [
    { x: 100, y: 180, r: 14, pts: 100, hit: 0 },
    { x: 180, y: 130, r: 16, pts: 200, hit: 0 },
    { x: 260, y: 180, r: 14, pts: 100, hit: 0 },
    { x: 140, y: 280, r: 12, pts: 150, hit: 0 },
    { x: 220, y: 280, r: 12, pts: 150, hit: 0 },
    { x: 180, y: 230, r: 18, pts: 500, hit: 0 },
    // Bumpers laterali
    { x: 50, y: 350, r: 10, pts: 50, hit: 0 },
    { x: 310, y: 350, r: 10, pts: 50, hit: 0 },
  ];
}

function initWalls() {
  return [
    // Left wall
    { x1: 15, y1: 80, x2: 15, y2: H - 40 },
    { x1: W - 15, y1: 80, x2: W - 15, y2: H - 40 },
    // Top arc approx
    { x1: 15, y1: 80, x2: 80, y2: 20 },
    { x1: W - 15, y1: 80, x2: W - 80, y2: 20 },
    { x1: 80, y1: 20, x2: W - 80, y2: 20 },
    // Drain guards
    { x1: 15, y1: H - 40, x2: LF_X - 15, y2: F_Y + 10 },
    { x1: W - 15, y1: H - 40, x2: RF_X + 15, y2: F_Y + 10 },
  ];
}

export function FlipperProGame({ mode = 'contest', onComplete }) {
  const canvasRef = useRef(null), contRef = useRef(null);
  const gRef = useRef(null), rafRef = useRef(null), uiRef = useRef(null);
  const cbRef = useRef(onComplete); cbRef.current = onComplete;
  const doneRef = useRef(false);
  const imgRef = useRef({ bg: null, ball: null, lsx: null, ldx: null, loaded: 0 });

  const [ui, setUi] = useState({ phase: 'intro', score: 0, multi: 1, balls: 3, level: 1, ballX: W / 2, ballY: H - 120, lfAng: FLIPPER_REST, rfAng: FLIPPER_REST });

  // Preload images
  useEffect(() => {
    const imgs = imgRef.current;
    const srcs = { bg: '/assets/flipper/bg.png', ball: '/assets/flipper/ball.png', lsx: '/assets/flipper/leva_sx.png', ldx: '/assets/flipper/leva_dx.png' };
    Object.entries(srcs).forEach(([k, src]) => {
      const img = new Image(); img.src = src;
      img.onload = () => { imgs[k] = img; imgs.loaded++; };
      img.onerror = () => console.error('Flipper img missing:', src);
    });
  }, []);

  const initGame = useCallback(() => {
    return {
      ball: { x: W / 2, y: H - 120, vx: 0, vy: 0, active: false },
      lf: FLIPPER_REST, rf: FLIPPER_REST, lfTarget: FLIPPER_REST, rfTarget: FLIPPER_REST,
      score: 0, multi: 1, balls: 3, level: 1,
      targets: initTargets(), walls: initWalls(),
      particles: [], phase: 'play', time: mode === 'contest' ? 90 : 120,
      shakeT: 0,
    };
  }, [mode]);

  const startGame = useCallback(() => {
    gRef.current = initGame();
    gRef.current.phase = 'play';
    doneRef.current = false;
    setUi(u => ({ ...u, phase: 'play', score: 0, multi: 1, balls: 3, level: 1 }));
  }, [initGame]);

  const launchBall = useCallback(() => {
    const g = gRef.current; if (!g || g.ball.active) return;
    g.ball = { x: W - 30, y: H - 100, vx: (Math.random() - 0.5) * 3, vy: -13 - Math.random() * 3, active: true };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);

    const g = initGame(); gRef.current = g;
    let lt = performance.now();

    // Keyboard
    const kd = (e) => {
      const g = gRef.current; if (!g) return;
      if (e.key === 'ArrowLeft' || e.key === 'a') g.lfTarget = FLIPPER_UP;
      if (e.key === 'ArrowRight' || e.key === 'd') g.rfTarget = FLIPPER_UP;
      if (e.key === ' ') { e.preventDefault(); launchBall(); }
    };
    const ku = (e) => {
      const g = gRef.current; if (!g) return;
      if (e.key === 'ArrowLeft' || e.key === 'a') g.lfTarget = FLIPPER_REST;
      if (e.key === 'ArrowRight' || e.key === 'd') g.rfTarget = FLIPPER_REST;
    };
    window.addEventListener('keydown', kd); window.addEventListener('keyup', ku);

    function update(dt) {
      const g = gRef.current; if (!g || g.phase !== 'play') return;
      dt = Math.min(dt, 0.033);
      g.time -= dt; if (g.time <= 0) { g.time = 0; g.phase = 'over'; return; }
      if (g.shakeT > 0) g.shakeT -= dt;

      // Flipper lerp
      g.lf += (g.lfTarget - g.lf) * 0.3;
      g.rf += (g.rfTarget - g.rf) * 0.3;

      const b = g.ball;
      if (!b.active) return;

      // Physics
      b.vy += GRAV + g.level * 0.03;
      b.x += b.vx; b.y += b.vy;
      b.vx *= 0.999; // tiny friction

      // Walls
      if (b.x < 20 + BALL_R) { b.x = 20 + BALL_R; b.vx = Math.abs(b.vx) * 0.8; }
      if (b.x > W - 20 - BALL_R) { b.x = W - 20 - BALL_R; b.vx = -Math.abs(b.vx) * 0.8; }
      if (b.y < 25 + BALL_R) { b.y = 25 + BALL_R; b.vy = Math.abs(b.vy) * 0.7; }

      // Drain
      if (b.y > H + 20) {
        b.active = false; g.balls--; g.multi = 1; g.shakeT = 0.3;
        if (g.balls <= 0) { g.phase = 'over'; }
        else { b.x = W / 2; b.y = H - 120; b.vx = 0; b.vy = 0; }
      }

      // Left flipper collision
      flipperCollide(b, LF_X, F_Y, g.lf, true);
      // Right flipper collision
      flipperCollide(b, RF_X, F_Y, g.rf, false);

      // Targets
      for (const t of g.targets) {
        const dx = b.x - t.x, dy = b.y - t.y, dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < t.r + BALL_R) {
          const nx = dx / dist, ny = dy / dist;
          b.vx = nx * 6; b.vy = ny * 6;
          b.x = t.x + nx * (t.r + BALL_R + 1);
          b.y = t.y + ny * (t.r + BALL_R + 1);
          g.score += t.pts * g.multi;
          g.multi = Math.min(g.multi + 1, 8);
          t.hit = 8;
          g.shakeT = 0.1;
          spawnP(g, t.x, t.y, 8, '#ffd700');
        }
        if (t.hit > 0) t.hit -= dt * 15;
      }

      // Level up
      if (g.score > g.level * 2000) {
        g.level++; spawnP(g, W / 2, H / 2, 15, '#00ffcc');
        // Reset targets
        g.targets = initTargets();
      }

      // Particles
      for (const p of g.particles) { p.x += p.vx * dt * 60; p.y += p.vy * dt * 60; p.life -= dt; }
      g.particles = g.particles.filter(p => p.life > 0);

      // Drain guards — angled walls
      wallCollide(b, 15, H - 40, LF_X - 15, F_Y + 10);
      wallCollide(b, W - 15, H - 40, RF_X + 15, F_Y + 10);
    }

    function flipperCollide(b, fx, fy, ang, isLeft) {
      const a = isLeft ? -ang : ang;
      const ex = fx + Math.cos(a) * FLIPPER_LEN * (isLeft ? 1 : -1);
      const ey = fy + Math.sin(a) * FLIPPER_LEN;
      wallCollide(b, fx, fy, ex, ey, true, isLeft ? g.lf < FLIPPER_REST - 0.1 : g.rf < FLIPPER_REST - 0.1);
    }

    function wallCollide(b, x1, y1, x2, y2, isFlipper = false, flipping = false) {
      const dx = x2 - x1, dy = y2 - y1, len = Math.sqrt(dx * dx + dy * dy);
      if (len === 0) return;
      const nx = -dy / len, ny = dx / len;
      const dist = (b.x - x1) * nx + (b.y - y1) * ny;
      if (Math.abs(dist) < BALL_R + (isFlipper ? FLIPPER_W / 2 : 3)) {
        const t = ((b.x - x1) * dx + (b.y - y1) * dy) / (len * len);
        if (t >= -0.1 && t <= 1.1) {
          const dot = b.vx * nx + b.vy * ny;
          if (dot < 0) {
            const boost = isFlipper && flipping ? 8 : 0;
            b.vx -= 2 * dot * nx; b.vy -= 2 * dot * ny;
            if (boost) { b.vy -= boost; b.vx += (b.x < W / 2 ? -2 : 2); }
            b.vx *= 0.85; b.vy *= 0.85;
          }
        }
      }
    }

    function spawnP(g, x, y, n, c) {
      for (let i = 0; i < n; i++) {
        const a = Math.random() * Math.PI * 2;
        g.particles.push({ x, y, vx: Math.cos(a) * (1 + Math.random() * 2), vy: Math.sin(a) * (1 + Math.random() * 2), life: 0.4 + Math.random() * 0.3, c });
      }
    }

    function draw() {
      const g = gRef.current; if (!g) return;
      const imgs = imgRef.current;
      let sx = 0, sy = 0;
      if (g.shakeT > 0) { sx = (Math.random() - 0.5) * 4; sy = (Math.random() - 0.5) * 4; }
      ctx.save(); ctx.translate(sx, sy);

      // BG
      if (imgs.bg) { ctx.drawImage(imgs.bg, 0, 0, W, H); }
      else { ctx.fillStyle = '#0a0a1a'; ctx.fillRect(0, 0, W, H); }

      // Targets
      for (const t of g.targets) {
        const glow = t.hit > 0 ? t.hit / 8 : 0;
        ctx.save(); ctx.translate(t.x, t.y);
        ctx.shadowBlur = 6 + glow * 10; ctx.shadowColor = glow > 0 ? '#ffd700' : '#ff4444';
        ctx.fillStyle = glow > 0 ? `rgb(255,${200 + glow * 55},${50 + glow * 200})` : '#cc2222';
        ctx.beginPath(); ctx.arc(0, 0, t.r, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.3)'; ctx.beginPath(); ctx.arc(-t.r * 0.2, -t.r * 0.2, t.r * 0.4, 0, Math.PI * 2); ctx.fill();
        ctx.shadowBlur = 0; ctx.restore();
      }

      // Walls (subtle glow lines)
      ctx.strokeStyle = 'rgba(255,200,0,0.15)'; ctx.lineWidth = 2;
      for (const w of g.walls) { ctx.beginPath(); ctx.moveTo(w.x1, w.y1); ctx.lineTo(w.x2, w.y2); ctx.stroke(); }

      // Particles
      for (const p of g.particles) {
        ctx.globalAlpha = p.life / 0.7; ctx.fillStyle = p.c;
        ctx.beginPath(); ctx.arc(p.x, p.y, 2, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;

      // Flippers (canvas fallback, PNG overlay is on top)
      drawFlipperCanvas(ctx, LF_X, F_Y, g.lf, true);
      drawFlipperCanvas(ctx, RF_X, F_Y, g.rf, false);

      // Ball (canvas fallback)
      if (g.ball.active) {
        ctx.shadowBlur = 8; ctx.shadowColor = '#ffd700';
        ctx.fillStyle = '#ddd'; ctx.beginPath(); ctx.arc(g.ball.x, g.ball.y, BALL_R, 0, Math.PI * 2); ctx.fill();
        ctx.shadowBlur = 0;
      }

      ctx.restore();
    }

    function drawFlipperCanvas(ctx, fx, fy, ang, isLeft) {
      ctx.save(); ctx.translate(fx, fy);
      ctx.rotate(isLeft ? -ang : ang);
      ctx.fillStyle = '#cc9900'; ctx.shadowBlur = 4; ctx.shadowColor = '#ffd700';
      const dir = isLeft ? 1 : -1;
      ctx.beginPath();
      ctx.moveTo(0, -FLIPPER_W / 2);
      ctx.lineTo(FLIPPER_LEN * dir, -4);
      ctx.lineTo(FLIPPER_LEN * dir, 4);
      ctx.lineTo(0, FLIPPER_W / 2);
      ctx.closePath(); ctx.fill();
      ctx.shadowBlur = 0; ctx.restore();
    }

    const loop = () => {
      const now = performance.now(), dt = (now - lt) / 1000; lt = now;
      if (gRef.current?.phase === 'play') update(dt);
      draw();

      const g = gRef.current;
      if (g?.phase === 'over' && !doneRef.current) {
        doneRef.current = true;
        const fs = Math.min(999, g.score);
        setUi(u => ({ ...u, phase: 'over', score: fs }));
        setTimeout(() => cbRef.current(fs), 3000);
      }

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    uiRef.current = setInterval(() => {
      const g = gRef.current; if (!g) return;
      setUi(u => ({
        ...u, score: g.score, multi: g.multi, balls: g.balls, level: g.level,
        time: Math.ceil(g.time),
        ballX: g.ball.x, ballY: g.ball.y,
        lfAng: g.lf, rfAng: g.rf,
        phase: g.phase,
      }));
    }, 80);

    return () => {
      cancelAnimationFrame(rafRef.current); clearInterval(uiRef.current);
      window.removeEventListener('keydown', kd); window.removeEventListener('keyup', ku);
    };
  }, [initGame, launchBall, mode]);

  // Touch controls
  const onFlip = useCallback((side, down) => {
    const g = gRef.current; if (!g) return;
    if (side === 'left') g.lfTarget = down ? FLIPPER_UP : FLIPPER_REST;
    if (side === 'right') g.rfTarget = down ? FLIPPER_UP : FLIPPER_REST;
  }, []);

  return (
    <div ref={contRef} className="fp-container" style={{ width: W, maxWidth: '100%' }} data-testid="minigame-flipper-pro">
      <canvas ref={canvasRef} className="fp-canvas" />

      {/* PNG Ball overlay */}
      {ui.phase === 'play' && (
        <img src="/assets/flipper/ball.png" alt="" className="fp-ball-img"
          style={{ left: ui.ballX, top: ui.ballY, width: BALL_R * 2.4, height: BALL_R * 2.4, transform: 'translate(-50%,-50%)' }} />
      )}

      {/* PNG Flipper overlays */}
      {ui.phase === 'play' && <>
        <img src="/assets/flipper/leva_sx.png" alt="" className="fp-leva-img"
          style={{ left: LF_X, top: F_Y, width: FLIPPER_LEN + 10, transform: `translate(-10%,-50%) rotate(${ui.lfAng}rad)`, transformOrigin: '10% 50%' }} />
        <img src="/assets/flipper/leva_dx.png" alt="" className="fp-leva-img"
          style={{ left: RF_X, top: F_Y, width: FLIPPER_LEN + 10, transform: `translate(-90%,-50%) rotate(${-ui.rfAng}rad)`, transformOrigin: '90% 50%' }} />
      </>}

      {/* HUD */}
      {ui.phase === 'play' && (
        <div className="fp-hud">
          <span className="fp-hud-score">{ui.score}</span>
          <span className="fp-hud-multi">x{ui.multi}</span>
          <span className="fp-hud-info">Lv{ui.level} | {ui.time}s | Palle:{ui.balls}</span>
        </div>
      )}

      {/* Controls */}
      {ui.phase === 'play' && (
        <div className="fp-controls">
          <button className="fp-btn fp-btn-flip"
            onPointerDown={() => onFlip('left', true)} onPointerUp={() => onFlip('left', false)} onPointerLeave={() => onFlip('left', false)}
            onTouchStart={(e) => { e.preventDefault(); onFlip('left', true); }} onTouchEnd={() => onFlip('left', false)}
            data-testid="fp-left">SX</button>
          <button className="fp-btn fp-btn-launch" onPointerDown={launchBall} data-testid="fp-launch">LANCIA</button>
          <button className="fp-btn fp-btn-flip"
            onPointerDown={() => onFlip('right', true)} onPointerUp={() => onFlip('right', false)} onPointerLeave={() => onFlip('right', false)}
            onTouchStart={(e) => { e.preventDefault(); onFlip('right', true); }} onTouchEnd={() => onFlip('right', false)}
            data-testid="fp-right">DX</button>
        </div>
      )}

      {/* Intro */}
      {ui.phase === 'intro' && (
        <div className="fp-overlay" data-testid="fp-intro">
          <div className="fp-intro-box">
            <p className="fp-title">FLIPPER PRO</p>
            <p className="fp-sub">MINIGIOCHI CINEMATOGRAFICI</p>
            <p className="fp-rules">Lancia la pallina, colpisci i target, accumula multiplier!</p>
            <button className="fp-start-btn" onPointerDown={startGame} data-testid="fp-start">INSERISCI MONETA</button>
            <p className="fp-hint">Mobile: SX/DX per le leve | Desktop: A/D + Spazio</p>
          </div>
        </div>
      )}

      {/* Game Over */}
      {ui.phase === 'over' && (
        <div className="fp-overlay fp-over-bg" data-testid="fp-gameover">
          <div className="fp-result-box">
            <p className="fp-over-title">GAME OVER</p>
            <p className="fp-score-big">{Math.min(999, ui.score)}</p>
            <p className="fp-result-info">Level {ui.level} | Multiplier max x{ui.multi}</p>
          </div>
        </div>
      )}
    </div>
  );
}
