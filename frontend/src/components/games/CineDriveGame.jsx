/* ===================================================================
   AUTO CINEMATOGRAFICA — Base
   Neon arcade car dodge, cinema-themed, perspective road, mobile-first
   =================================================================== */
import React, { useState, useEffect, useRef } from 'react';
import {
  CAR_W, CAR_H, HB_W, HB_H, VY, CT, MXT, MHP, INV, NMD, NMCD,
  OBS_HB, OBS_IDS, BON_IDS, BON_D, PAL,
  lerp, rand, pick, clamp,
  roadAt, lnX, scAt, initSky,
  drawSky, drawRoad, drawCar, drawObs, drawBon, drawParts, aabb, calcSc,
} from './cineDriveEngine';
import './cineDrive.css';

export function CineDriveGame({ mode = 'contest', onComplete }) {
  const canvasRef = useRef(null), contRef = useRef(null), gRef = useRef(null);
  const rafRef = useRef(null), uiRef = useRef(null), doneRef = useRef(false);
  const touchRef = useRef({ down: false, x: 0 });
  const cbRef = useRef(onComplete); cbRef.current = onComplete;

  const [ui, setUi] = useState({ score: 0, combo: 0, hp: 3, shield: false, time: 0, nm: 0, phase: 'count', countVal: 3 });
  const [shake, setShake] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current, cont = contRef.current;
    if (!canvas || !cont) return;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.floor(cont.getBoundingClientRect().width), h = 380;
    canvas.width = w * dpr; canvas.height = h * dpr;
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
    const pal = PAL.neon;
    const carY = h * 0.76;

    const g = {
      w, h, mode, pal,
      car: { x: w / 2, targetX: w / 2 }, carY,
      hp: MHP, invuln: 0, shield: false, shieldT: 0,
      slowmo: false, slowT: 0,
      obs: [], bons: [], parts: [],
      score: 0, combo: 0, maxCombo: 0, nearMisses: 0,
      hitsTaken: 0, bonusCount: 0,
      speed: 150, scroll: 0,
      surviveTime: 0, difficulty: 1, spawnT: 0, diffT: 0, bonSpawnT: rand(2, 4), nmCd: 0,
      phase: 'count', countVal: 3, countT: 0,
      contestTime: CT, tilt: 0, prevX: w / 2,
      sky: initSky(w), hitFlash: 0,
    };
    gRef.current = g;
    let lt = performance.now();

    const gx = e => (e.clientX ?? e.touches?.[0]?.clientX ?? 0) - cont.getBoundingClientRect().left;
    const pd = e => { e.preventDefault(); touchRef.current = { down: true, x: gx(e) }; };
    const pm = e => { e.preventDefault(); if (touchRef.current.down) touchRef.current.x = gx(e); };
    const pu = () => { touchRef.current.down = false; };
    cont.addEventListener('pointerdown', pd, { passive: false });
    cont.addEventListener('pointermove', pm, { passive: false });
    cont.addEventListener('pointerup', pu); cont.addEventListener('pointerleave', pu);
    cont.addEventListener('touchstart', e => e.preventDefault(), { passive: false });

    const end = () => {
      g.phase = 'over'; if (doneRef.current) return; doneRef.current = true;
      const fs = calcSc(g);
      setUi(p => ({ ...p, phase: 'over', score: fs }));
      setTimeout(() => cbRef.current(fs), 1500);
    };

    const loop = () => {
      const now = performance.now(), dt = Math.min((now - lt) / 1000, 0.05); lt = now;

      // --- COUNTDOWN ---
      if (g.phase === 'count') {
        g.countT += dt; g.scroll += dt * 0.5;
        if (g.countVal > 0 && g.countT >= 0.7) { g.countT = 0; g.countVal--; }
        else if (g.countVal === 0 && g.countT >= 0.5) { g.phase = 'play'; }
        // Render during countdown — canvas transparent, PNG layers handle visuals
        ctx.clearRect(0, 0, w, h);
        setUi(p => ({ ...p, countVal: g.countVal, phase: 'count' }));
        rafRef.current = requestAnimationFrame(loop); return;
      }
      if (g.phase === 'over') { rafRef.current = requestAnimationFrame(loop); return; }

      // --- PLAY ---
      const sm = g.slowmo ? 0.4 : 1, gdt = dt * sm;
      g.surviveTime += dt; g.score += dt * 2; g.scroll += g.speed * dt * 0.003;

      if (g.mode === 'contest') { g.contestTime -= dt; if (g.contestTime <= 0) { end(); return; } }
      else if (g.surviveTime >= MXT) { end(); return; }

      g.diffT += dt;
      if (g.diffT >= 5) { g.diffT -= 5; g.difficulty = Math.min(5, g.difficulty + 0.2); g.speed = Math.min(350, 150 + (g.difficulty - 1) * 45); }

      // Car
      const rb = roadAt(carY, w, h);
      const minX = rb.l + CAR_W / 2 + 4, maxX = rb.r - CAR_W / 2 - 4;
      if (touchRef.current.down) g.car.targetX = clamp(touchRef.current.x, minX, maxX);
      g.car.x = lerp(g.car.x, g.car.targetX, dt * 10);
      if (g.invuln > 0) g.invuln -= dt;
      if (g.hitFlash > 0) g.hitFlash -= dt;
      if (g.shieldT > 0) { g.shieldT -= dt; if (g.shieldT <= 0) g.shield = false; }
      if (g.slowT > 0) { g.slowT -= dt; if (g.slowT <= 0) g.slowmo = false; }
      // Tilt
      const vel = (g.car.x - g.prevX) / Math.max(dt, 0.001); g.prevX = g.car.x;
      g.tilt = lerp(g.tilt, clamp(vel * 0.05, -0.15, 0.15), dt * 8);
      if (g.nmCd > 0) g.nmCd -= dt;

      // Spawn obstacles
      g.spawnT -= gdt;
      if (g.spawnT <= 0) {
        g.spawnT = Math.max(0.35, 0.9 - (g.difficulty - 1) * 0.12);
        g.obs.push({ type: pick(OBS_IDS), lane: ~~rand(0, 3), y: h * VY - 5, passed: false, nmd: false });
      }
      // Spawn bonuses
      g.bonSpawnT -= gdt;
      if (g.bonSpawnT <= 0) { g.bonSpawnT = rand(3, 6); g.bons.push({ type: pick(BON_IDS), lane: ~~rand(0, 3), y: h * VY - 5, col: false }); }

      // Update obstacles
      for (const o of g.obs) {
        const s = scAt(o.y, h); o.y += g.speed * s * gdt;
        o.sx = lnX(o.lane, o.y, w, h); o.sc = s;
        const hbw = OBS_HB[o.type][0] * s, hbh = OBS_HB[o.type][1] * s;
        // Collision
        if (!o.passed && g.invuln <= 0 && !g.shield && aabb(o.sx, o.y, hbw, hbh, g.car.x, carY, HB_W, HB_H)) {
          o.passed = true; g.hp--; g.invuln = INV; g.hitsTaken++; g.combo = 0; g.hitFlash = 0.2;
          setShake(true); setTimeout(() => setShake(false), 200);
          try { navigator.vibrate?.([30, 20, 30]); } catch {}
          for (let i = 0; i < 6; i++) g.parts.push({ x: o.sx + rand(-10, 10), y: o.y + rand(-10, 10), vx: rand(-40, 40), vy: rand(-40, 10), r: rand(1, 3), c: '#ff4444', life: 0.5, ml: 0.5 });
          if (g.hp <= 0 && g.mode !== 'contest') { end(); return; }
        }
        // Shield absorb
        if (!o.passed && g.shield && aabb(o.sx, o.y, hbw, hbh, g.car.x, carY, HB_W, HB_H)) {
          o.passed = true; g.shield = false; g.shieldT = 0;
          for (let i = 0; i < 5; i++) g.parts.push({ x: g.car.x + rand(-15, 15), y: carY + rand(-15, 15), vx: rand(-30, 30), vy: rand(-30, 30), r: rand(1, 2), c: '#ffd700', life: 0.4, ml: 0.4 });
        }
        // Near miss
        if (!o.passed && !o.nmd && g.nmCd <= 0 && o.y > carY - HB_H / 2 - 5 && o.y < carY + HB_H / 2 + 5) {
          const dx = Math.abs(o.sx - g.car.x);
          if (dx > HB_W / 2 + hbw / 2 - 2 && dx < HB_W / 2 + hbw / 2 + NMD) {
            o.nmd = true; g.nearMisses++; g.nmCd = NMCD; g.combo++; g.maxCombo = Math.max(g.maxCombo, g.combo); g.score += 10;
            g.parts.push({ x: o.sx, y: o.y, vx: 0, vy: -20, r: 0, c: '#00ffff', life: 0.6, ml: 0.6, txt: 'NEAR MISS' });
            try { navigator.vibrate?.(12); } catch {}
          }
        }
        // Dodged
        if (!o.passed && o.y > carY + HB_H) { o.passed = true; g.combo++; g.maxCombo = Math.max(g.maxCombo, g.combo); g.score += 5; }
      }
      g.obs = g.obs.filter(o => o.y < h + 20);

      // Update bonuses
      for (const b of g.bons) {
        const s = scAt(b.y, h); b.y += g.speed * s * gdt; b.sx = lnX(b.lane, b.y, w, h); b.sc = s;
        if (!b.col && aabb(b.sx, b.y, 12 * s, 12 * s, g.car.x, carY, HB_W + 8, HB_H + 8)) {
          b.col = true; const d = BON_D[b.type]; g.score += d.s; g.bonusCount++;
          if (d.fx === 'slow') { g.slowmo = true; g.slowT = 2; }
          if (d.fx === 'shield') { g.shield = true; g.shieldT = 8; }
          for (let i = 0; i < 5; i++) g.parts.push({ x: b.sx + rand(-8, 8), y: b.y + rand(-8, 8), vx: rand(-30, 30), vy: rand(-40, -10), r: rand(1, 2.5), c: b.type === 'star' ? '#ffd700' : b.type === 'lightning' ? '#00ffff' : '#ff3344', life: 0.4, ml: 0.4 });
          try { navigator.vibrate?.(8); } catch {}
        }
      }
      g.bons = g.bons.filter(b => !b.col && b.y < h + 20);

      // Particles
      for (const p of g.parts) { p.x += (p.vx || 0) * dt; p.y += (p.vy || 0) * dt; p.life -= dt; }
      g.parts = g.parts.filter(p => p.life > 0);

      // === RENDER === (canvas transparent — PNG bg behind, PNG car overlay)
      ctx.clearRect(0, 0, w, h);
      if (g.hitFlash > 0) { ctx.fillStyle = `rgba(255,0,0,${0.15 * (g.hitFlash / 0.2)})`; ctx.fillRect(0, 0, w, h); }
      if (g.slowmo) { ctx.fillStyle = 'rgba(0,255,255,0.03)'; ctx.fillRect(0, 0, w, h); }
      // Obstacles (rendered on canvas above PNG bg)
      for (const o of g.obs) { if (!o.passed) drawObs(ctx, o.type, o.sx, o.y, o.sc, pal); }
      // Bonuses
      for (const b of g.bons) { if (!b.col) drawBon(ctx, b.type, b.sx, b.y, b.sc, g.surviveTime); }
      // Car drawn as PNG overlay — skip canvas car
      // Particles
      drawParts(ctx, g.parts);
      // NM text particles
      for (const p of g.parts) {
        if (!p.txt) continue;
        ctx.globalAlpha = p.life / p.ml; ctx.font = 'bold 9px monospace'; ctx.fillStyle = p.c;
        ctx.textAlign = 'center'; ctx.fillText(p.txt, p.x, p.y);
      }
      ctx.globalAlpha = 1;

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    uiRef.current = setInterval(() => {
      const gg = gRef.current; if (!gg) return;
      setUi({
        score: calcSc(gg), combo: gg.combo, hp: gg.hp, shield: gg.shield,
        time: gg.mode === 'contest' ? Math.ceil(gg.contestTime) : Math.floor(gg.surviveTime),
        nm: gg.nearMisses, phase: gg.phase, countVal: gg.countVal,
        carX: gg.car.x, tilt: gg.tilt || 0, invuln: gg.invuln > 0,
      });
    }, 100);

    return () => { g.phase = 'over'; cancelAnimationFrame(rafRef.current); clearInterval(uiRef.current); cont.removeEventListener('pointerdown', pd); cont.removeEventListener('pointermove', pm); cont.removeEventListener('pointerup', pu); cont.removeEventListener('pointerleave', pu); };
  }, []); // eslint-disable-line

  return (
    <div ref={contRef} className={`cd-container ${shake ? 'cd-shake' : ''}`} style={{ height: 380 }} data-testid="minigame-cine-drive">
      {/* LAYER 2: PNG Background */}
      <img src="/assets/cinedrive/bg_city.png" alt="" className="cd-bg-img" />
      {/* LAYER 4: Canvas (obstacles, bonuses, particles, effects) */}
      <canvas ref={canvasRef} className="cd-canvas" />
      {/* LAYER 5: PNG Car */}
      <img
        src="/assets/cinedrive/car.png"
        alt=""
        className={`cd-car-img ${ui.invuln ? 'cd-car-invuln' : ''}`}
        style={{
          left: ui.carX,
          top: '76%',
          transform: `translateX(-50%) translateY(-50%) rotate(${ui.tilt}rad)`,
        }}
      />
      {/* HUD */}
      <div className="cd-ui-top">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-[10px] font-mono text-fuchsia-400/70 leading-none">SCORE</p>
            <p className="text-lg font-black font-mono text-fuchsia-300 cd-glow leading-tight">{ui.score}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-mono text-fuchsia-400/70 leading-none">{mode === 'contest' ? 'TIME' : 'SURVIVE'}</p>
            <p className="text-base font-bold font-mono text-white leading-tight">{ui.time}s</p>
          </div>
        </div>
        <div className="flex items-center justify-between mt-1">
          <div className="flex gap-1">{[0, 1, 2].map(i => <div key={i} className="w-2 h-2 rounded-full transition-all" style={{ background: i < ui.hp ? '#ff00ff' : '#222', boxShadow: i < ui.hp ? '0 0 6px #ff00ff' : 'none' }} />)}</div>
          {ui.combo >= 3 && <span className="text-[10px] font-bold font-mono text-fuchsia-400 cd-glow">x{ui.combo}</span>}
          {ui.shield && <span className="text-[9px] font-bold font-mono text-yellow-400 animate-pulse">SCUDO</span>}
          {ui.nm > 0 && <span className="text-[9px] font-mono text-cyan-400/60">NM:{ui.nm}</span>}
        </div>
      </div>
      {/* Countdown */}
      {ui.phase === 'count' && (
        <div className="cd-count" key={ui.countVal}>
          <p className="cd-count-num">{ui.countVal > 0 ? ui.countVal : 'VIA!'}</p>
        </div>
      )}
      {/* Game Over */}
      {ui.phase === 'over' && (
        <div className="cd-over" data-testid="cine-drive-gameover">
          <p className="text-sm font-mono text-fuchsia-500/60 mb-1">CIAK!</p>
          <p className="text-xl font-black font-mono text-fuchsia-300 cd-glow">CORSA INTERROTTA</p>
          <p className="text-3xl font-black font-mono text-cyan-300 mt-3 cd-glow-cy">{ui.score}</p>
        </div>
      )}
    </div>
  );
}
