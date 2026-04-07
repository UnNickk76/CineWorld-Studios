/* ===================================================================
   AUTO CINEMATOGRAFICA — PRO ASSURDA
   Extended: Scenarios, Events, Turbo, Boss Events, Star Rating
   =================================================================== */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  CAR_W, CAR_H, HB_W, HB_H, VY, MXT, MHP, INV, NMD, NMCD,
  OBS_HB, OBS_IDS, BON_IDS, BON_D, PAL,
  lerp, rand, pick, clamp,
  roadAt, lnX, scAt, initSky,
  drawSky, drawRoad, drawCar, drawObs, drawBon, drawParts, aabb, calcSc,
} from './cineDriveEngine';
import './cineDrive.css';

const PRO_CT = 60;
const SCEN_KEYS = ['neon', 'rain', 'tunnel', 'synth', 'stunt', 'emer'];
const PRO_EVENTS = [
  { id: 'flash', name: 'RIFLETTORI!', dur: 2, c: '#ffdd00' },
  { id: 'limo', name: 'LIMOUSINE!', dur: 3, c: '#ff00ff' },
  { id: 'mega_ciak', name: 'MEGA CIAK!', dur: 2, c: '#00ffff' },
  { id: 'ticket_rain', name: 'PIOGGIA TICKET!', dur: 4, c: '#ff3344' },
  { id: 'drone', name: 'DRONE CAM!', dur: 3, c: '#aa00ff' },
];
const TURBO_MAX = 100, TURBO_DUR = 4, TURBO_BONUS = 100;
const BOSS_SCORE = 350, BOSS_DUR = 10;

function starRating(s) { return s >= 800 ? 5 : s >= 600 ? 4 : s >= 400 ? 3 : s >= 200 ? 2 : 1; }

export function CineDriveProGame({ mode = 'contest', onComplete }) {
  const canvasRef = useRef(null), contRef = useRef(null), gRef = useRef(null);
  const rafRef = useRef(null), uiRef = useRef(null), doneRef = useRef(false);
  const touchRef = useRef({ down: false, x: 0 });
  const cbRef = useRef(onComplete); cbRef.current = onComplete;

  const [ui, setUi] = useState({ score: 0, combo: 0, hp: 3, shield: false, time: 0, nm: 0, phase: 'count', countVal: 3, turboBar: 0, turbo: false, event: null, boss: false, stars: 0 });
  const [shake, setShake] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current, cont = contRef.current;
    if (!canvas || !cont) return;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.floor(cont.getBoundingClientRect().width), h = 400;
    canvas.width = w * dpr; canvas.height = h * dpr;
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
    const carY = h * 0.76;

    const g = {
      w, h, mode, pal: PAL.neon,
      car: { x: w / 2, targetX: w / 2 }, carY,
      hp: MHP, invuln: 0, shield: false, shieldT: 0, slowmo: false, slowT: 0,
      obs: [], bons: [], parts: [],
      score: 0, combo: 0, maxCombo: 0, nearMisses: 0, hitsTaken: 0, bonusCount: 0,
      speed: 160, scroll: 0,
      surviveTime: 0, difficulty: 1, spawnT: 0, diffT: 0, bonSpawnT: rand(2, 3.5), nmCd: 0,
      phase: 'count', countVal: 3, countT: 0, contestTime: PRO_CT,
      tilt: 0, prevX: w / 2, sky: initSky(w), hitFlash: 0,
      // Pro extras
      scenIdx: 0, scenT: 15,
      evt: null, evtT: 0, nextEvt: rand(10, 18),
      turboBar: 0, turbo: false, turboT: 0,
      bossOn: false, bossT: 0, bossSp: 0,
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
      const eb = g.bossOn ? TURBO_BONUS : 0;
      const fs = calcSc(g, eb);
      const stars = starRating(fs);
      setUi(p => ({ ...p, phase: 'over', score: fs, stars }));
      setTimeout(() => cbRef.current(fs), 2000);
    };

    const loop = () => {
      const now = performance.now(), dt = Math.min((now - lt) / 1000, 0.05); lt = now;

      if (g.phase === 'count') {
        g.countT += dt; g.scroll += dt * 0.5;
        if (g.countVal > 0 && g.countT >= 0.7) { g.countT = 0; g.countVal--; }
        else if (g.countVal === 0 && g.countT >= 0.5) { g.phase = 'play'; }
        drawSky(ctx, g.sky, w, h, g.pal); drawRoad(ctx, w, h, g.scroll, g.pal);
        drawCar(ctx, g.car.x, carY, 0, false, false, g.pal);
        setUi(p => ({ ...p, countVal: g.countVal, phase: 'count' }));
        rafRef.current = requestAnimationFrame(loop); return;
      }
      if (g.phase === 'over') { rafRef.current = requestAnimationFrame(loop); return; }

      const turboMul = g.turbo ? 1.5 : 1;
      const sm = g.slowmo ? 0.4 : turboMul;
      const gdt = dt * sm;
      g.surviveTime += dt; g.score += dt * 2 * (g.turbo ? 2 : 1); g.scroll += g.speed * dt * 0.003;

      if (g.mode === 'contest') { g.contestTime -= dt; if (g.contestTime <= 0) { end(); return; } }
      else if (g.surviveTime >= MXT) { end(); return; }

      g.diffT += dt;
      if (g.diffT >= 5) { g.diffT -= 5; g.difficulty = Math.min(5, g.difficulty + 0.22); g.speed = Math.min(380, 160 + (g.difficulty - 1) * 50); }

      // Scenarios
      g.scenT -= dt;
      if (g.scenT <= 0) { g.scenT = 15; g.scenIdx = (g.scenIdx + 1) % SCEN_KEYS.length; g.pal = PAL[SCEN_KEYS[g.scenIdx]]; }

      // Events
      if (!g.evt && !g.bossOn) {
        g.nextEvt -= dt;
        if (g.nextEvt <= 0) { g.evt = pick(PRO_EVENTS); g.evtT = g.evt.dur; g.nextEvt = rand(12, 20); }
      }
      if (g.evt) { g.evtT -= dt; if (g.evtT <= 0) g.evt = null; }

      // Boss
      if (!g.bossOn && g.score > BOSS_SCORE) {
        g.bossOn = true; g.bossT = BOSS_DUR; g.bossSp = 0;
      }
      if (g.bossT > 0) {
        g.bossT -= dt; g.bossSp -= gdt;
        if (g.bossSp <= 0) { g.bossSp = 0.25; for (let i = 0; i < 2; i++) g.obs.push({ type: pick(OBS_IDS), lane: ~~rand(0, 3), y: h * VY - 5, passed: false, nmd: false }); }
      }

      // Turbo
      if (g.turbo) { g.turboT -= dt; if (g.turboT <= 0) g.turbo = false; }
      if (!g.turbo && g.turboBar >= TURBO_MAX) {
        g.turbo = true; g.turboT = TURBO_DUR; g.turboBar = 0;
      }

      // Car
      const rb = roadAt(carY, w, h);
      const minX = rb.l + CAR_W / 2 + 4, maxX = rb.r - CAR_W / 2 - 4;
      if (touchRef.current.down) g.car.targetX = clamp(touchRef.current.x, minX, maxX);
      g.car.x = lerp(g.car.x, g.car.targetX, dt * 10);
      if (g.invuln > 0) g.invuln -= dt;
      if (g.hitFlash > 0) g.hitFlash -= dt;
      if (g.shieldT > 0) { g.shieldT -= dt; if (g.shieldT <= 0) g.shield = false; }
      if (g.slowT > 0) { g.slowT -= dt; if (g.slowT <= 0) g.slowmo = false; }
      const vel = (g.car.x - g.prevX) / Math.max(dt, 0.001); g.prevX = g.car.x;
      g.tilt = lerp(g.tilt, clamp(vel * 0.05, -0.15, 0.15), dt * 8);
      if (g.nmCd > 0) g.nmCd -= dt;

      // Spawn
      if (g.bossT <= 0) {
        g.spawnT -= gdt;
        if (g.spawnT <= 0) { g.spawnT = Math.max(0.3, 0.85 - (g.difficulty - 1) * 0.12); g.obs.push({ type: pick(OBS_IDS), lane: ~~rand(0, 3), y: h * VY - 5, passed: false, nmd: false }); }
      }
      // Event: ticket rain spawns bonuses
      if (g.evt?.id === 'ticket_rain') { g.bonSpawnT -= gdt * 3; } else { g.bonSpawnT -= gdt; }
      if (g.bonSpawnT <= 0) { g.bonSpawnT = rand(2.5, 5); g.bons.push({ type: pick(BON_IDS), lane: ~~rand(0, 3), y: h * VY - 5, col: false }); }

      // Event: limo crossing (extra obstacle in center)
      if (g.evt?.id === 'limo' && g.evtT > g.evt.dur - 0.1) {
        g.obs.push({ type: 'barrier', lane: 1, y: h * VY - 5, passed: false, nmd: false });
      }
      // Event: mega ciak
      if (g.evt?.id === 'mega_ciak' && g.evtT > g.evt.dur - 0.1) {
        for (let l = 0; l < 3; l++) g.obs.push({ type: 'ciak', lane: l, y: h * VY - 5 - l * 15, passed: false, nmd: false });
      }

      // Update obstacles
      for (const o of g.obs) {
        const s = scAt(o.y, h); o.y += g.speed * s * gdt; o.sx = lnX(o.lane, o.y, w, h); o.sc = s;
        const hbw = OBS_HB[o.type][0] * s, hbh = OBS_HB[o.type][1] * s;
        if (!o.passed && g.invuln <= 0 && !g.shield && !g.turbo && aabb(o.sx, o.y, hbw, hbh, g.car.x, carY, HB_W, HB_H)) {
          o.passed = true; g.hp--; g.invuln = INV; g.hitsTaken++; g.combo = 0; g.hitFlash = 0.2;
          setShake(true); setTimeout(() => setShake(false), 200);
          try { navigator.vibrate?.([30, 20, 30]); } catch {}
          for (let i = 0; i < 6; i++) g.parts.push({ x: o.sx + rand(-10, 10), y: o.y + rand(-10, 10), vx: rand(-40, 40), vy: rand(-40, 10), r: rand(1, 3), c: '#ff4444', life: 0.5, ml: 0.5 });
          if (g.hp <= 0 && g.mode !== 'contest') { end(); return; }
        }
        // Turbo destroys obstacles
        if (!o.passed && g.turbo && aabb(o.sx, o.y, hbw, hbh, g.car.x, carY, HB_W + 10, HB_H + 10)) {
          o.passed = true; g.score += 8;
          for (let i = 0; i < 4; i++) g.parts.push({ x: o.sx + rand(-8, 8), y: o.y + rand(-8, 8), vx: rand(-50, 50), vy: rand(-50, -10), r: rand(1.5, 3), c: g.pal.acc, life: 0.4, ml: 0.4 });
        }
        if (!o.passed && g.shield && aabb(o.sx, o.y, hbw, hbh, g.car.x, carY, HB_W, HB_H)) {
          o.passed = true; g.shield = false;
          for (let i = 0; i < 5; i++) g.parts.push({ x: g.car.x + rand(-15, 15), y: carY + rand(-15, 15), vx: rand(-30, 30), vy: rand(-30, 30), r: rand(1, 2), c: '#ffd700', life: 0.4, ml: 0.4 });
        }
        if (!o.passed && !o.nmd && g.nmCd <= 0 && o.y > carY - HB_H / 2 - 5 && o.y < carY + HB_H / 2 + 5) {
          const dx = Math.abs(o.sx - g.car.x);
          if (dx > HB_W / 2 + hbw / 2 - 2 && dx < HB_W / 2 + hbw / 2 + NMD) {
            o.nmd = true; g.nearMisses++; g.nmCd = NMCD; g.combo++; g.maxCombo = Math.max(g.maxCombo, g.combo); g.score += 10;
            g.turboBar = Math.min(TURBO_MAX, g.turboBar + 8);
            g.parts.push({ x: o.sx, y: o.y, vx: 0, vy: -20, r: 0, c: '#00ffff', life: 0.6, ml: 0.6, txt: 'NEAR MISS' });
            try { navigator.vibrate?.(12); } catch {}
          }
        }
        if (!o.passed && o.y > carY + HB_H) { o.passed = true; g.combo++; g.maxCombo = Math.max(g.maxCombo, g.combo); g.score += 5; }
      }
      g.obs = g.obs.filter(o => o.y < h + 20);

      // Bonuses
      for (const b of g.bons) {
        const s = scAt(b.y, h); b.y += g.speed * s * gdt; b.sx = lnX(b.lane, b.y, w, h); b.sc = s;
        if (!b.col && aabb(b.sx, b.y, 12 * s, 12 * s, g.car.x, carY, HB_W + 8, HB_H + 8)) {
          b.col = true; const d = BON_D[b.type]; g.score += d.s; g.bonusCount++;
          g.turboBar = Math.min(TURBO_MAX, g.turboBar + 6);
          if (d.fx === 'slow') { g.slowmo = true; g.slowT = 2; }
          if (d.fx === 'shield') { g.shield = true; g.shieldT = 8; }
          for (let i = 0; i < 5; i++) g.parts.push({ x: b.sx + rand(-8, 8), y: b.y + rand(-8, 8), vx: rand(-30, 30), vy: rand(-40, -10), r: rand(1, 2.5), c: b.type === 'star' ? '#ffd700' : b.type === 'lightning' ? '#00ffff' : '#ff3344', life: 0.4, ml: 0.4 });
          try { navigator.vibrate?.(8); } catch {}
        }
      }
      g.bons = g.bons.filter(b => !b.col && b.y < h + 20);

      for (const p of g.parts) { p.x += (p.vx || 0) * dt; p.y += (p.vy || 0) * dt; p.life -= dt; }
      g.parts = g.parts.filter(p => p.life > 0);

      // === RENDER ===
      drawSky(ctx, g.sky, w, h, g.pal);
      // Event flash
      if (g.evt?.id === 'flash') { const a = Math.sin(g.evtT * 4) * 0.15; ctx.fillStyle = `rgba(255,255,200,${Math.max(0, a)})`; ctx.fillRect(0, 0, w, h); }
      if (g.hitFlash > 0) { ctx.fillStyle = `rgba(255,0,0,${0.15 * (g.hitFlash / 0.2)})`; ctx.fillRect(0, 0, w, h); }
      if (g.slowmo) { ctx.fillStyle = 'rgba(0,255,255,0.03)'; ctx.fillRect(0, 0, w, h); }
      if (g.turbo) { ctx.fillStyle = 'rgba(255,0,255,0.04)'; ctx.fillRect(0, 0, w, h); }
      drawRoad(ctx, w, h, g.scroll, g.pal);
      if (g.bossT > 0) { ctx.save(); ctx.strokeStyle = `rgba(255,0,50,${0.3 + Math.sin(g.surviveTime * 5) * 0.15})`; ctx.lineWidth = 3; ctx.strokeRect(1, 1, w - 2, h - 2); ctx.restore(); }
      for (const o of g.obs) { if (!o.passed) drawObs(ctx, o.type, o.sx, o.y, o.sc, g.pal); }
      for (const b of g.bons) { if (!b.col) drawBon(ctx, b.type, b.sx, b.y, b.sc, g.surviveTime); }
      const carA = g.invuln > 0 ? (Math.sin(g.invuln * 20) > 0 ? 0.4 : 1) : 1;
      ctx.globalAlpha = carA;
      drawCar(ctx, g.car.x, carY, g.tilt, g.shield, g.turbo, g.pal);
      ctx.globalAlpha = 1;
      drawParts(ctx, g.parts);
      for (const p of g.parts) { if (!p.txt) continue; ctx.globalAlpha = p.life / p.ml; ctx.font = 'bold 9px monospace'; ctx.fillStyle = p.c; ctx.textAlign = 'center'; ctx.fillText(p.txt, p.x, p.y); }
      ctx.globalAlpha = 1;
      // Drone cam visual
      if (g.evt?.id === 'drone') { ctx.save(); ctx.strokeStyle = 'rgba(170,0,255,0.2)'; ctx.lineWidth = 1; ctx.setLineDash([3, 3]); ctx.strokeRect(20, 20, w - 40, h - 40); ctx.restore(); }

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    uiRef.current = setInterval(() => {
      const gg = gRef.current; if (!gg) return;
      const eb = gg.bossOn ? TURBO_BONUS : 0;
      setUi({
        score: calcSc(gg, eb), combo: gg.combo, hp: gg.hp, shield: gg.shield,
        time: gg.mode === 'contest' ? Math.ceil(gg.contestTime) : Math.floor(gg.surviveTime),
        nm: gg.nearMisses, phase: gg.phase, countVal: gg.countVal,
        turboBar: gg.turboBar, turbo: gg.turbo,
        event: gg.evt, boss: gg.bossT > 0, stars: 0,
      });
    }, 100);

    return () => { g.phase = 'over'; cancelAnimationFrame(rafRef.current); clearInterval(uiRef.current); cont.removeEventListener('pointerdown', pd); cont.removeEventListener('pointermove', pm); cont.removeEventListener('pointerup', pu); cont.removeEventListener('pointerleave', pu); };
  }, []); // eslint-disable-line

  return (
    <div ref={contRef} className={`cd-container ${shake ? 'cd-shake' : ''}`} style={{ height: 400 }} data-testid="minigame-cine-drive-pro">
      <canvas ref={canvasRef} className="cd-canvas" />
      <div className="cd-ui-top">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-[9px] font-mono text-fuchsia-400/60 leading-none">SCORE</p>
            <p className="text-lg font-black font-mono text-fuchsia-300 cd-glow leading-tight">{ui.score}</p>
          </div>
          {ui.event && <span className="text-[9px] font-bold font-mono px-1.5 py-0.5 rounded" style={{ color: ui.event.c, background: `${ui.event.c}15`, border: `1px solid ${ui.event.c}30` }}>{ui.event.name}</span>}
          <div className="text-right">
            <p className="text-[9px] font-mono text-fuchsia-400/60 leading-none">{mode === 'contest' ? 'TIME' : 'SURVIVE'}</p>
            <p className="text-base font-bold font-mono text-white leading-tight">{ui.time}s</p>
          </div>
        </div>
        <div className="flex items-center justify-between mt-1">
          <div className="flex gap-1">{[0, 1, 2].map(i => <div key={i} className="w-2 h-2 rounded-full transition-all" style={{ background: i < ui.hp ? '#ff00ff' : '#222', boxShadow: i < ui.hp ? '0 0 6px #ff00ff' : 'none' }} />)}</div>
          {ui.combo >= 3 && <span className="text-[10px] font-bold font-mono text-fuchsia-400 cd-glow">x{ui.combo}</span>}
          {ui.shield && <span className="text-[9px] font-bold font-mono text-yellow-400 animate-pulse">SCUDO</span>}
          {ui.turbo && <span className="text-[9px] font-bold font-mono text-cyan-400 animate-pulse">TURBO!</span>}
          {ui.boss && <span className="text-[9px] font-bold font-mono text-red-400 animate-pulse">BOSS</span>}
        </div>
      </div>
      <div className="cd-ui-bot">
        <div className="cd-turbo"><div className={`cd-turbo-f ${ui.turbo ? 'on' : ''}`} style={{ width: `${ui.turbo ? 100 : ui.turboBar}%` }} /></div>
        <p className="text-[8px] font-mono text-fuchsia-500/40 text-center mt-0.5">{ui.turbo ? 'TURBO PREMIERE!' : 'TURBO'}</p>
      </div>
      {ui.phase === 'count' && <div className="cd-count" key={ui.countVal}><p className="cd-count-num">{ui.countVal > 0 ? ui.countVal : 'VIA!'}</p></div>}
      {ui.phase === 'over' && (
        <div className="cd-over" data-testid="cine-pro-gameover">
          <p className="text-sm font-mono text-fuchsia-500/60 mb-1">CIAK!</p>
          <p className="text-xl font-black font-mono text-fuchsia-300 cd-glow">CORSA INTERROTTA</p>
          <p className="text-3xl font-black font-mono text-cyan-300 mt-3 cd-glow-cy">{ui.score}</p>
          <div className="cd-stars mt-2">
            {[1, 2, 3, 4, 5].map(i => (
              <svg key={i} className={`cd-star-i ${i <= ui.stars ? 'on' : ''}`} viewBox="0 0 24 24" fill={i <= ui.stars ? '#ffd700' : '#333'}>
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.27 5.82 22 7 14.14l-5-4.87 6.91-1.01z" />
              </svg>
            ))}
          </div>
          <p className="text-[10px] font-mono text-fuchsia-400/40 mt-1">{ui.stars >= 5 ? 'LEGGENDA DEL CINEMA' : ui.stars >= 4 ? 'BLOCKBUSTER' : ui.stars >= 3 ? 'SPETTACOLARE' : ui.stars >= 2 ? 'BUONA CORSA' : 'DISCRETA'}</p>
        </div>
      )}
    </div>
  );
}
