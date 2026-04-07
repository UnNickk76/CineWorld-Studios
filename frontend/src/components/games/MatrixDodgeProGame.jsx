/* ===================================================================
   MATRIX DODGE — PRO ASSURDA
   Extended: Dash, Manual BT, Afterimages, Events, Elite Wave, WOW.
   Canvas rendering. Mobile-first. No external images.
   =================================================================== */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  PW, PH, HBW, HBH, NM_DIST, NM_CD, BT_FILL, BT_MAX, BT_DURATION, BT_SLOW,
  BASE_SPAWN, MIN_SPAWN, BASE_SPEED, DIFF_INTERVAL, DIFF_STEP, MAX_DIFF, INVULN, MAX_SURVIVE,
  lerp, rand, clamp, pick,
  initRain, spawnPattern,
  renderBg, renderRain, renderPlayer, renderPlayerTrail, renderProjectiles, renderTextFx, renderVignette,
  updateRain, circleRect, calcScore,
} from './matrixDodgeEngine';
import './matrixDodge.css';

const PRO_CONTEST = 60;
const DASH_DIST = 80, DASH_CD = 2.5, DASH_INV = 0.2, DASH_DUR = 0.15;
const BT_MANUAL_COST = 50;
const ELITE_SCORE = 400, ELITE_TIME = 50, ELITE_DUR = 15, ELITE_BONUS = 150;
const WOW_THRESH = 600;

const EVENTS = [
  { id: 'glitch_storm', name: 'GLITCH STORM', duration: 5, color: '#ff00ff' },
  { id: 'red_pill', name: 'RED PILL', duration: 5, color: '#ff0033' },
  { id: 'system_break', name: 'SYSTEM BREAK', duration: 3, color: '#00ff41' },
  { id: 'agent_rush', name: 'AGENT RUSH', duration: 3.5, color: '#ff6600' },
  { id: 'code_fracture', name: 'CODE FRACTURE', duration: 4, color: '#00ffff' },
];

function spawnElite(w, speed) {
  const projs = [];
  const mk = (x, vy, vx = 0, ghost = false) => ({ x, y: -10, vx, vy, r: 4, trail: [], passed: false, nearMissed: false, ghost, ghostTimer: ghost ? rand(0.2, 0.6) : 0 });
  const tp = pick(['circle', 'alt', 'delayed', 'synced']);
  switch (tp) {
    case 'circle': { const gap = rand(0, Math.PI * 2); for (let a = 0; a < Math.PI * 2; a += 0.4) { if (Math.abs(a - gap) < 0.6) continue; projs.push(mk(w / 2 + Math.cos(a) * 80, speed * 0.6, Math.cos(a) * 50)); } break; }
    case 'alt': { for (let i = 0; i < 8; i++) { const fl = i % 2 === 0; projs.push(mk(fl ? 10 : w - 10, speed, fl ? 40 : -40)); } break; }
    case 'delayed': { for (let i = 0; i < 6; i++) { const p = mk(rand(20, w - 20), speed); p.ghost = true; p.ghostTimer = i * 0.15; projs.push(p); } break; }
    default: { for (let i = -3; i <= 3; i++) projs.push(mk(w / 2 + i * 25, speed)); }
  }
  return projs;
}

export function MatrixDodgeProGame({ mode = 'contest', onComplete }) {
  const canvasRef = useRef(null);
  const contRef = useRef(null);
  const gRef = useRef(null);
  const rafRef = useRef(null);
  const uiIvRef = useRef(null);
  const doneRef = useRef(false);
  const touchRef = useRef({ down: false, x: 0 });
  const cbRef = useRef(onComplete);
  cbRef.current = onComplete;

  const [ui, setUi] = useState({
    score: 0, combo: 0, hp: 3, btBar: 0, btActive: false, time: 0, nm: 0,
    phase: 'playing', dashOk: true, event: null, elite: false,
  });
  const [shake, setShake] = useState(false);

  const triggerDash = useCallback(() => {
    const g = gRef.current;
    if (!g || !g.running || g.dashCd > 0) return;
    const dir = touchRef.current.x > g.player.x + PW / 2 ? 1 : -1;
    g.player.targetX = clamp(g.player.x + dir * DASH_DIST, 0, g.w - PW);
    g.dashCd = DASH_CD; g.dashAct = DASH_DUR;
    g.invuln = Math.max(g.invuln, DASH_INV); g.dashUses++;
    for (let i = 0; i < 3; i++) g.afterimages.push({ x: g.player.x - dir * i * 15, y: g.player.y, life: 0.3, ml: 0.3 });
    try { navigator.vibrate?.(10); } catch {}
  }, []);

  const triggerBt = useCallback(() => {
    const g = gRef.current;
    if (!g || !g.running || g.btActive || g.btBar < BT_MANUAL_COST) return;
    g.btBar -= BT_MANUAL_COST; g.btActive = true; g.btTimer = BT_DURATION; g.btUses++; g.score += 15;
    g.fx.push({ type: 'text', x: g.w / 2, y: g.h / 2, text: 'BULLET TIME', color: '#00ff41', life: 1.2, maxLife: 1.2, big: true });
    try { navigator.vibrate?.([15, 10, 15]); } catch {}
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current, cont = contRef.current;
    if (!canvas || !cont) return;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.floor(cont.getBoundingClientRect().width), h = 380;
    canvas.width = w * dpr; canvas.height = h * dpr;
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);

    const g = {
      w, h, mode,
      player: { x: w / 2 - PW / 2, y: h * 0.70, targetX: w / 2 - PW / 2 },
      hp: 3, invuln: 0, projectiles: [], rain: initRain(w, h), fx: [],
      score: 0, combo: 0, maxCombo: 0, nearMisses: 0, dodges: 0,
      hitsTaken: 0, btUses: 0, dashUses: 0,
      btBar: 0, btActive: false, btTimer: 0,
      surviveTime: 0, difficulty: 1, spawnTimer: 0, diffTimer: 0, nmCooldown: 0,
      running: true, contestTime: PRO_CONTEST,
      dashCd: 0, dashAct: 0, afterimages: [],
      evt: null, evtTimer: 0, nextEvt: rand(15, 22),
      eliteOn: false, eliteTimer: 0, eliteSp: 0,
    };
    gRef.current = g;
    let lt = performance.now();

    const gx = (e) => (e.clientX ?? e.touches?.[0]?.clientX ?? 0) - cont.getBoundingClientRect().left;
    const pd = (e) => { if (e.target.closest('.md-btn')) return; e.preventDefault(); touchRef.current = { down: true, x: gx(e) }; };
    const pm = (e) => { e.preventDefault(); if (touchRef.current.down) touchRef.current.x = gx(e); };
    const pu = () => { touchRef.current.down = false; };
    cont.addEventListener('pointerdown', pd, { passive: false });
    cont.addEventListener('pointermove', pm, { passive: false });
    cont.addEventListener('pointerup', pu); cont.addEventListener('pointerleave', pu);
    cont.addEventListener('touchstart', e => { if (!e.target.closest('.md-btn')) e.preventDefault(); }, { passive: false });

    const end = () => {
      g.running = false; if (doneRef.current) return; doneRef.current = true;
      const eb = g.eliteOn ? ELITE_BONUS : 0;
      const fs = calcScore(g, eb);
      if (fs >= WOW_THRESH) {
        setUi(p => ({ ...p, phase: 'wow', score: fs }));
        setTimeout(() => cbRef.current(fs), 3000);
      } else {
        setUi(p => ({ ...p, phase: 'over', score: fs }));
        setTimeout(() => cbRef.current(fs), 1200);
      }
    };

    const loop = () => {
      if (!g.running) return;
      const now = performance.now(), dt = Math.min((now - lt) / 1000, 0.05); lt = now;
      const gs = g.btActive ? BT_SLOW : 1, gdt = dt * gs;
      g.surviveTime += dt; g.score += dt * 2;

      if (g.mode === 'contest') { g.contestTime -= dt; if (g.contestTime <= 0) { end(); return; } }
      else if (g.surviveTime >= MAX_SURVIVE) { end(); return; }

      g.diffTimer += dt;
      if (g.diffTimer >= DIFF_INTERVAL) { g.diffTimer -= DIFF_INTERVAL; g.difficulty = Math.min(MAX_DIFF, g.difficulty + DIFF_STEP * 1.2); }
      if (g.dashCd > 0) g.dashCd -= dt;
      if (g.dashAct > 0) g.dashAct -= dt;

      const p = g.player;
      if (touchRef.current.down) p.targetX = clamp(touchRef.current.x - PW / 2, 0, w - PW);
      p.x = lerp(p.x, p.targetX, dt * (g.dashAct > 0 ? 30 : 12));
      if (g.invuln > 0) g.invuln -= dt;
      if (g.hitFlash > 0) g.hitFlash -= dt;
      // Trail
      g.trailT = (g.trailT || 0) - dt;
      if (g.trailT <= 0) { g.trailT = 0.05; if (!g.trail) g.trail = []; g.trail.unshift({ x: p.x, y: p.y }); if (g.trail.length > 3) g.trail.pop(); }
      // Tilt from velocity
      const vel = (p.x - (g.pxPrev ?? p.x)) / Math.max(dt, 0.001); g.pxPrev = p.x;
      g.tilt = lerp(g.tilt || 0, clamp(vel * 0.06, -0.18, 0.18), dt * 8);

      g.afterimages = g.afterimages.filter(a => { a.life -= dt; return a.life > 0; });
      if ((g.combo >= 8 || g.btActive) && g.surviveTime % 0.1 < dt) g.afterimages.push({ x: p.x, y: p.y, life: 0.25, ml: 0.25 });

      // Events
      if (!g.evt && !g.eliteOn) {
        g.nextEvt -= dt;
        if (g.nextEvt <= 0) {
          g.evt = pick(EVENTS); g.evtTimer = g.evt.duration; g.nextEvt = rand(15, 25);
          g.fx.push({ type: 'text', x: w / 2, y: h * 0.35, text: g.evt.name, color: g.evt.color, life: 1.5, maxLife: 1.5, big: true });
        }
      }
      if (g.evt) { g.evtTimer -= dt; if (g.evtTimer <= 0) g.evt = null; }

      // Elite
      if (!g.eliteOn && (g.score > ELITE_SCORE || g.surviveTime > ELITE_TIME)) {
        g.eliteOn = true; g.eliteTimer = ELITE_DUR; g.eliteSp = 0;
        g.fx.push({ type: 'text', x: w / 2, y: h * 0.35, text: 'ELITE WAVE', color: '#ff0033', life: 2, maxLife: 2, big: true });
      }
      if (g.eliteTimer > 0) {
        g.eliteTimer -= dt; g.eliteSp -= gdt;
        if (g.eliteSp <= 0) { g.eliteSp = 0.4; g.projectiles.push(...spawnElite(w, BASE_SPEED + MAX_DIFF * 35)); }
      }

      if (g.eliteTimer <= 0) {
        g.spawnTimer -= gdt;
        if (g.spawnTimer <= 0) { g.spawnTimer = Math.max(MIN_SPAWN, BASE_SPAWN - (g.difficulty - 1) * 0.15); g.projectiles.push(...spawnPattern(w, g.difficulty)); }
      }
      if (g.nmCooldown > 0) g.nmCooldown -= dt;

      const pcx = p.x + PW / 2, pcy = p.y + PH / 2;
      const hbx = p.x + (PW - HBW) / 2, hby = p.y + (PH - HBH) / 2;
      const nmMul = g.evt?.id === 'red_pill' ? 2 : 1;

      for (const pr of g.projectiles) {
        if (pr.ghost && pr.ghostTimer > 0) pr.ghostTimer -= gdt;
        pr.trail.unshift({ x: pr.x, y: pr.y }); if (pr.trail.length > (g.btActive ? 10 : 6)) pr.trail.pop();
        let evx = pr.vx;
        if (g.evt?.id === 'glitch_storm') evx += Math.sin(g.surviveTime * 10 + pr.x) * 40;
        pr.x += evx * gdt; pr.y += pr.vy * gdt;
        if (pr.ghost && pr.ghostTimer > 0) continue;

        // Near miss
        if (!pr.nearMissed && !pr.passed && g.nmCooldown <= 0) {
          const dx = pr.x - pcx, dy = pr.y - pcy, d = Math.sqrt(dx * dx + dy * dy);
          if (d < NM_DIST && d > HBW / 2) {
            pr.nearMissed = true; g.nearMisses++; g.nmCooldown = NM_CD;
            g.btBar = Math.min(BT_MAX, g.btBar + BT_FILL * nmMul);
            g.combo++; g.maxCombo = Math.max(g.maxCombo, g.combo); g.score += 8 * nmMul;
            g.fx.push({ type: 'text', x: pr.x, y: pr.y, text: nmMul > 1 ? 'NEAR MISS x2' : 'NEAR MISS', color: '#00ffff', life: 0.8, maxLife: 0.8 });
            try { navigator.vibrate?.(15); } catch {}
          }
        }
        // System break safe zone
        if (g.evt?.id === 'system_break' && pr.x > w * 0.35 && pr.x < w * 0.65 && pr.y > h * 0.5 && pr.y < h * 0.85) { pr.passed = true; continue; }
        // Collision
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

      // BT auto
      if (!g.btActive && g.btBar >= BT_MAX) {
        g.btActive = true; g.btTimer = BT_DURATION; g.btUses++; g.btBar = 0; g.score += 15;
        g.fx.push({ type: 'text', x: w / 2, y: h / 2, text: 'BULLET TIME', color: '#00ff41', life: 1.2, maxLife: 1.2, big: true });
      }
      if (g.btActive) { g.btTimer -= dt; if (g.btTimer <= 0) g.btActive = false; }
      g.fx = g.fx.filter(f => { f.life -= dt; return f.life > 0; });
      updateRain(g.rain, w, h, gdt);

      /* === RENDER === */
      renderBg(ctx, w, h);
      // Event visuals
      if (g.evt?.id === 'glitch_storm') { for (let y = 0; y < h; y += 3) { ctx.fillStyle = `rgba(255,0,255,${0.02 + Math.sin(y + g.surviveTime * 5) * 0.01})`; ctx.fillRect(0, y, w, 1); } }
      if (g.evt?.id === 'red_pill') { ctx.fillStyle = 'rgba(255,0,30,0.05)'; ctx.fillRect(0, 0, w, h); }
      if (g.evt?.id === 'code_fracture') { ctx.save(); ctx.strokeStyle = 'rgba(0,255,255,0.15)'; ctx.lineWidth = 1; for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(w * 0.3 + i * w * 0.1, 0); ctx.lineTo(w * 0.3 + i * w * 0.1 + Math.sin(g.surviveTime * 3 + i) * 20, h); ctx.stroke(); } ctx.restore(); }
      const hitFx = g.fx.find(f => f.type === 'hit');
      if (hitFx) { ctx.fillStyle = `rgba(255,0,0,${0.2 * (hitFx.life / hitFx.maxLife)})`; ctx.fillRect(0, 0, w, h); }
      renderRain(ctx, g.rain, w, h, g.btActive ? 1.6 : g.eliteTimer > 0 ? 1.3 : 1);
      if (g.evt?.id === 'system_break') { ctx.save(); ctx.strokeStyle = 'rgba(0,255,65,0.3)'; ctx.lineWidth = 2; ctx.setLineDash([4, 4]); ctx.strokeRect(w * 0.35, h * 0.5, w * 0.3, h * 0.35); ctx.fillStyle = 'rgba(0,255,65,0.03)'; ctx.fillRect(w * 0.35, h * 0.5, w * 0.3, h * 0.35); ctx.restore(); }
      renderProjectiles(ctx, g.projectiles, g.btActive);
      for (const ai of g.afterimages) renderPlayer(ctx, ai.x, ai.y, 0, g.btActive, 0, (ai.life / ai.ml) * 0.3);
      renderPlayer(ctx, p.x, p.y, g.invuln, g.btActive, g.combo);
      renderTextFx(ctx, g.fx);
      renderVignette(ctx, w, h, g.btActive);
      if (g.eliteTimer > 0) { ctx.save(); ctx.strokeStyle = `rgba(255,0,50,${0.3 + Math.sin(g.surviveTime * 5) * 0.15})`; ctx.lineWidth = 3; ctx.strokeRect(1, 1, w - 2, h - 2); ctx.restore(); }

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    uiIvRef.current = setInterval(() => {
      const gg = gRef.current; if (!gg) return;
      const eb = gg.eliteOn ? ELITE_BONUS : 0;
      setUi({
        score: calcScore(gg, eb), combo: gg.combo, hp: gg.hp, btBar: gg.btBar, btActive: gg.btActive,
        time: gg.mode === 'contest' ? Math.ceil(gg.contestTime) : Math.floor(gg.surviveTime),
        nm: gg.nearMisses, phase: gg.running ? 'playing' : 'over',
        dashOk: gg.dashCd <= 0, event: gg.evt, elite: gg.eliteTimer > 0,
      });
    }, 100);

    return () => { g.running = false; cancelAnimationFrame(rafRef.current); clearInterval(uiIvRef.current); cont.removeEventListener('pointerdown', pd); cont.removeEventListener('pointermove', pm); cont.removeEventListener('pointerup', pu); cont.removeEventListener('pointerleave', pu); };
  }, []); // eslint-disable-line

  return (
    <div ref={contRef} className={`md-container ${shake ? 'md-shake' : ''}`} style={{ height: 380 }} data-testid="minigame-matrix-dodge-pro">
      <canvas ref={canvasRef} className="md-canvas" />
      <div className="md-ui-top">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-[9px] font-mono text-green-400/60 leading-none">SCORE</p>
            <p className="text-lg font-black font-mono text-green-300 md-glow leading-tight">{ui.score}</p>
          </div>
          {ui.event && <span className="text-[9px] font-bold font-mono px-1.5 py-0.5 rounded" style={{ color: ui.event.color, background: `${ui.event.color}15`, border: `1px solid ${ui.event.color}30` }}>{ui.event.name}</span>}
          <div className="text-right">
            <p className="text-[9px] font-mono text-green-400/60 leading-none">{mode === 'contest' ? 'TIME' : 'SURVIVE'}</p>
            <p className="text-base font-bold font-mono text-white leading-tight">{ui.time}s</p>
          </div>
        </div>
        <div className="flex items-center justify-between mt-1">
          <div className="flex gap-1">{[0, 1, 2].map(i => <div key={i} className={`md-hp ${i < ui.hp ? 'on' : ''}`} />)}</div>
          {ui.combo >= 3 && <span className="text-[10px] font-bold font-mono text-green-400 md-glow">x{ui.combo}</span>}
          {ui.elite && <span className="text-[9px] font-bold font-mono text-red-400 animate-pulse">ELITE</span>}
          {ui.nm > 0 && <span className="text-[9px] font-mono text-cyan-400/60">NM:{ui.nm}</span>}
        </div>
      </div>
      <div className="md-ui-bottom">
        <div className="flex items-end justify-between mb-1">
          <button className={`md-btn md-btn-dash ${ui.dashOk ? '' : 'cd'}`} onPointerDown={e => { e.stopPropagation(); triggerDash(); }} data-testid="dash-btn">DASH</button>
          <button className={`md-btn md-btn-bt ${ui.btBar >= BT_MANUAL_COST && !ui.btActive ? '' : 'cd'}`} onPointerDown={e => { e.stopPropagation(); triggerBt(); }} data-testid="bt-btn">BT</button>
        </div>
        <div className="md-bt-bar"><div className={`md-bt-fill ${ui.btActive ? 'active' : ''}`} style={{ width: `${ui.btActive ? 100 : ui.btBar}%` }} /></div>
      </div>
      {ui.phase === 'over' && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-black/70" data-testid="matrix-pro-gameover">
          <div className="text-center">
            <p className="text-2xl font-black font-mono text-green-400 md-glow">{mode === 'contest' ? "TIME'S UP" : 'GAME OVER'}</p>
            <p className="text-3xl font-black font-mono text-cyan-300 mt-2">{ui.score}</p>
          </div>
        </div>
      )}
      {ui.phase === 'wow' && (
        <div className="md-wow" data-testid="matrix-pro-wow">
          <p className="md-wow-title">THE ONE?</p>
          <p className="md-wow-score">{ui.score}</p>
          <p className="text-xs font-mono text-green-400/50 mt-3 animate-pulse">MATRIX DODGE PRO</p>
        </div>
      )}
    </div>
  );
}
