/* ===================================================================
   MATRIX DODGE — Base
   Dodge projectiles Matrix-style. Near-miss, combo, auto bullet-time.
   Canvas rendering. Mobile-first. No external images.
   =================================================================== */
import React, { useState, useEffect, useRef } from 'react';
import {
  PW, PH, HBW, HBH, NM_DIST, NM_CD, BT_FILL, BT_MAX, BT_DURATION, BT_SLOW,
  BASE_SPAWN, MIN_SPAWN, DIFF_INTERVAL, DIFF_STEP, MAX_DIFF, INVULN,
  CONTEST_SECS, MAX_SURVIVE,
  lerp, clamp,
  initGame, spawnPattern,
  renderBg, renderRain, renderPlayer, renderPlayerTrail, renderProjectiles, renderTextFx, renderVignette,
  updateRain, circleRect, calcScore,
} from './matrixDodgeEngine';
import './matrixDodge.css';

export function MatrixDodgeGame({ mode = 'contest', onComplete }) {
  const canvasRef = useRef(null);
  const contRef = useRef(null);
  const gRef = useRef(null);
  const rafRef = useRef(null);
  const uiIvRef = useRef(null);
  const doneRef = useRef(false);
  const touchRef = useRef({ down: false, x: 0 });
  const cbRef = useRef(onComplete);
  cbRef.current = onComplete;

  const [ui, setUi] = useState({ score: 0, combo: 0, hp: 3, btBar: 0, btActive: false, time: 0, nm: 0, phase: 'playing', playerX: 0, direction: 'idle' });
  const [shake, setShake] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    const cont = contRef.current;
    if (!canvas || !cont) return;

    const dpr = window.devicePixelRatio || 1;
    const w = Math.floor(cont.getBoundingClientRect().width);
    const h = 360;
    canvas.width = w * dpr; canvas.height = h * dpr;
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const g = initGame(w, h, mode);
    gRef.current = g;
    let lt = performance.now();

    /* --- Touch --- */
    const gx = (e) => (e.clientX ?? e.touches?.[0]?.clientX ?? 0) - cont.getBoundingClientRect().left;
    const pd = (e) => { e.preventDefault(); touchRef.current = { down: true, x: gx(e) }; };
    const pm = (e) => { e.preventDefault(); if (touchRef.current.down) touchRef.current.x = gx(e); };
    const pu = () => { touchRef.current.down = false; };
    cont.addEventListener('pointerdown', pd, { passive: false });
    cont.addEventListener('pointermove', pm, { passive: false });
    cont.addEventListener('pointerup', pu);
    cont.addEventListener('pointerleave', pu);
    cont.addEventListener('touchstart', e => e.preventDefault(), { passive: false });

    /* --- End --- */
    const end = () => {
      g.running = false;
      if (doneRef.current) return; doneRef.current = true;
      const fs = calcScore(g);
      setUi(p => ({ ...p, phase: 'over', score: fs }));
      setTimeout(() => cbRef.current(fs), 1200);
    };

    /* --- Loop --- */
    const loop = () => {
      if (!g.running) return;
      const now = performance.now();
      const dt = Math.min((now - lt) / 1000, 0.05);
      lt = now;
      const gs = g.btActive ? BT_SLOW : 1;
      const gdt = dt * gs;

      g.surviveTime += dt; g.score += dt * 2;
      if (g.mode === 'contest') { g.contestTime -= dt; if (g.contestTime <= 0) { end(); return; } }
      else if (g.surviveTime >= MAX_SURVIVE) { end(); return; }

      g.diffTimer += dt;
      if (g.diffTimer >= DIFF_INTERVAL) { g.diffTimer -= DIFF_INTERVAL; g.difficulty = Math.min(MAX_DIFF, g.difficulty + DIFF_STEP); }

      const p = g.player;
      if (touchRef.current.down) p.targetX = clamp(touchRef.current.x - PW / 2, 0, w - PW);
      p.x = lerp(p.x, p.targetX, dt * 12);
      if (g.invuln > 0) g.invuln -= dt;
      if (g.hitFlash > 0) g.hitFlash -= dt;
      // Trail
      g.trailT = (g.trailT || 0) - dt;
      if (g.trailT <= 0) { g.trailT = 0.05; if (!g.trail) g.trail = []; g.trail.unshift({ x: p.x, y: p.y }); if (g.trail.length > 3) g.trail.pop(); }
      // Tilt from velocity
      const vel = (p.x - (g.pxPrev ?? p.x)) / Math.max(dt, 0.001); g.pxPrev = p.x;
      g.tilt = lerp(g.tilt || 0, clamp(vel * 0.06, -0.18, 0.18), dt * 8);

      g.spawnTimer -= gdt;
      if (g.spawnTimer <= 0) { g.spawnTimer = Math.max(MIN_SPAWN, BASE_SPAWN - (g.difficulty - 1) * 0.15); g.projectiles.push(...spawnPattern(w, g.difficulty)); }
      if (g.nmCooldown > 0) g.nmCooldown -= dt;

      const pcx = p.x + PW / 2, pcy = p.y + PH / 2;
      const hbx = p.x + (PW - HBW) / 2, hby = p.y + (PH - HBH) / 2;

      for (const pr of g.projectiles) {
        if (pr.ghost && pr.ghostTimer > 0) pr.ghostTimer -= gdt;
        pr.trail.unshift({ x: pr.x, y: pr.y }); if (pr.trail.length > 6) pr.trail.pop();
        pr.x += pr.vx * gdt; pr.y += pr.vy * gdt;
        if (pr.ghost && pr.ghostTimer > 0) continue;

        if (!pr.nearMissed && !pr.passed && g.nmCooldown <= 0) {
          const dx = pr.x - pcx, dy = pr.y - pcy, d = Math.sqrt(dx * dx + dy * dy);
          if (d < NM_DIST && d > HBW / 2) {
            pr.nearMissed = true; g.nearMisses++; g.nmCooldown = NM_CD;
            g.btBar = Math.min(BT_MAX, g.btBar + BT_FILL);
            g.combo++; g.maxCombo = Math.max(g.maxCombo, g.combo); g.score += 8;
            g.fx.push({ type: 'text', x: pr.x, y: pr.y, text: 'NEAR MISS', color: '#00ffff', life: 0.8, maxLife: 0.8 });
            try { navigator.vibrate?.(15); } catch {}
          }
        }

        if (!pr.passed && g.invuln <= 0 && circleRect(pr.x, pr.y, pr.r, hbx, hby, HBW, HBH)) {
          pr.passed = true; g.hp--; g.invuln = INVULN; g.hitsTaken++; g.combo = 0; g.hitFlash = 0.15;
          setShake(true); setTimeout(() => setShake(false), 150);
          try { navigator.vibrate?.([30, 20, 30]); } catch {}
          g.fx.push({ type: 'hit', life: 0.3, maxLife: 0.3 });
          if (g.hp <= 0 && g.mode !== 'contest') { end(); return; }
        }

        if (!pr.passed && pr.y > p.y + PH) { pr.passed = true; g.dodges++; g.score += 3; }
      }
      g.projectiles = g.projectiles.filter(q => q.y < h + 30 && q.x > -30 && q.x < w + 30);

      if (!g.btActive && g.btBar >= BT_MAX) {
        g.btActive = true; g.btTimer = BT_DURATION; g.btUses++; g.btBar = 0; g.score += 15;
        g.fx.push({ type: 'text', x: w / 2, y: h / 2, text: 'BULLET TIME', color: '#00ff41', life: 1.2, maxLife: 1.2, big: true });
      }
      if (g.btActive) { g.btTimer -= dt; if (g.btTimer <= 0) g.btActive = false; }

      g.fx = g.fx.filter(f => { f.life -= dt; return f.life > 0; });
      updateRain(g.rain, w, h, gdt);

      /* --- RENDER --- */
      renderBg(ctx, w, h);
      const hitFx = g.fx.find(f => f.type === 'hit');
      if (hitFx) { ctx.fillStyle = `rgba(255,0,0,${0.2 * (hitFx.life / hitFx.maxLife)})`; ctx.fillRect(0, 0, w, h); }
      renderRain(ctx, g.rain, w, h, g.btActive ? 1.5 : 1);
      renderProjectiles(ctx, g.projectiles, g.btActive);
      // Player canvas rendering hidden — Neo PNG overlay used instead
      // renderPlayerTrail(ctx, g.trail, g.btActive, g.combo);
      // renderPlayer(ctx, p.x, p.y, g.invuln, g.btActive, g.combo, 1, g.tilt, g.surviveTime, g.hitFlash > 0);
      renderTextFx(ctx, g.fx);
      renderVignette(ctx, w, h, g.btActive);

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    uiIvRef.current = setInterval(() => {
      const gg = gRef.current; if (!gg) return;
      const vel = gg.player.x - (gg._prevUiX ?? gg.player.x);
      gg._prevUiX = gg.player.x;
      const dir = vel < -1.5 ? 'left' : vel > 1.5 ? 'right' : 'idle';
      setUi({
        score: calcScore(gg), combo: gg.combo, hp: gg.hp,
        btBar: gg.btBar, btActive: gg.btActive,
        time: gg.mode === 'contest' ? Math.ceil(gg.contestTime) : Math.floor(gg.surviveTime),
        nm: gg.nearMisses, phase: gg.running ? 'playing' : 'over',
        playerX: gg.player.x + PW / 2, direction: dir,
      });
    }, 100);

    return () => { g.running = false; cancelAnimationFrame(rafRef.current); clearInterval(uiIvRef.current); cont.removeEventListener('pointerdown', pd); cont.removeEventListener('pointermove', pm); cont.removeEventListener('pointerup', pu); cont.removeEventListener('pointerleave', pu); };
  }, []); // eslint-disable-line

  return (
    <div ref={contRef} className={`md-container ${shake ? 'md-shake' : ''}`} style={{ height: 360 }} data-testid="minigame-matrix-dodge">
      <canvas ref={canvasRef} className="md-canvas" />
      {/* Neo PNG overlay — inside game container */}
      <div
        style={{
          position: 'absolute',
          left: ui.playerX,
          bottom: 38,
          width: 72,
          height: 72,
          transform: 'translateX(-50%)',
          pointerEvents: 'none',
          zIndex: 999,
        }}
      >
        <img
          src={
            ui.direction === 'left'
              ? '/assets/matrix/neo_sx.png'
              : ui.direction === 'right'
              ? '/assets/matrix/neo_dx.png'
              : '/assets/matrix/neo_idle.png'
          }
          alt="Neo"
          style={{
            position: 'absolute',
            left: '50%',
            bottom: 0,
            width: 72,
            height: 72,
            objectFit: 'contain',
            transform:
              ui.direction === 'left'
                ? 'translateX(-50%) rotate(-6deg)'
                : ui.direction === 'right'
                ? 'translateX(-50%) rotate(6deg)'
                : 'translateX(-50%)',
            pointerEvents: 'none',
            zIndex: 1000,
            filter: 'drop-shadow(0 0 10px #00ff66) drop-shadow(0 0 18px #00ff66)',
            opacity: ui.phase === 'over' ? 0.3 : 1,
            transition: 'opacity 0.3s',
          }}
          onError={(e) => {
            console.error('Neo image missing:', e.currentTarget.src);
            e.currentTarget.style.display = 'none';
          }}
        />
      </div>
      <div className="md-ui-top">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-[10px] font-mono text-green-400/70 leading-none">SCORE</p>
            <p className="text-lg font-black font-mono text-green-300 md-glow leading-tight">{ui.score}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-mono text-green-400/70 leading-none">{mode === 'contest' ? 'TIME' : 'SURVIVE'}</p>
            <p className="text-base font-bold font-mono text-white leading-tight">{ui.time}s</p>
          </div>
        </div>
        <div className="flex items-center justify-between mt-1">
          <div className="flex gap-1">{[0, 1, 2].map(i => <div key={i} className={`md-hp ${i < ui.hp ? 'on' : ''}`} />)}</div>
          {ui.combo >= 3 && <span className="text-[10px] font-bold font-mono text-green-400 md-glow">x{ui.combo} COMBO</span>}
          {ui.nm > 0 && <span className="text-[9px] font-mono text-cyan-400/60">NM:{ui.nm}</span>}
        </div>
      </div>
      <div className="md-ui-bottom">
        <div className="md-bt-bar"><div className={`md-bt-fill ${ui.btActive ? 'active' : ''}`} style={{ width: `${ui.btActive ? 100 : ui.btBar}%` }} /></div>
        <p className="text-[8px] font-mono text-green-500/40 text-center mt-0.5">{ui.btActive ? 'BULLET TIME' : ui.btBar >= 80 ? 'QUASI...' : 'BULLET TIME'}</p>
      </div>
      {ui.phase === 'over' && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-black/70" data-testid="matrix-dodge-gameover">
          <div className="text-center">
            <p className="text-2xl font-black font-mono text-green-400 md-glow">{mode === 'contest' ? "TIME'S UP" : 'GAME OVER'}</p>
            <p className="text-3xl font-black font-mono text-cyan-300 mt-2">{ui.score}</p>
          </div>
        </div>
      )}
    </div>
  );
}
