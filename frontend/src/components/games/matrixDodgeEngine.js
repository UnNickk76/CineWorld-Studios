/* ===================================================================
   MATRIX DODGE ENGINE — Shared logic for Base & Pro variants
   Pure JS — no React, no external images, no heavy deps
   =================================================================== */

// --- Characters & Constants ---
const MC = 'アイウエオカキクケコサシスセソタチツテト0123456789ABCDEF<>{}=';
export const PW = 28, PH = 42, HBW = 16, HBH = 26;
export const PROJ_R = 4;
export const NM_DIST = 30, NM_CD = 0.35, BT_FILL = 22;
export const BT_MAX = 100, BT_DURATION = 3, BT_SLOW = 0.25;
export const BASE_SPAWN = 0.95, MIN_SPAWN = 0.25;
export const BASE_SPEED = 140, SPEED_PER_DIFF = 35;
export const DIFF_INTERVAL = 5, DIFF_STEP = 0.18, MAX_DIFF = 5;
export const MAX_HP = 3, INVULN = 1.0;
export const CONTEST_SECS = 45, MAX_SURVIVE = 120;

// --- Helpers ---
export const lerp = (a, b, t) => a + (b - a) * Math.min(1, t);
export const rand = (a, b) => Math.random() * (b - a) + a;
export const pick = (a) => a[Math.floor(Math.random() * a.length)];
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const mchar = () => MC[Math.floor(Math.random() * MC.length)];

// --- Init ---
export function initRain(w, h) {
  const cols = [];
  for (let x = 0; x < w; x += 18) {
    const len = Math.floor(rand(6, 16));
    cols.push({ x, y: rand(-h, 0), speed: rand(40, 110), chars: Array.from({ length: len }, mchar), len });
  }
  return cols;
}

export function initGame(w, h, mode) {
  return {
    w, h, mode,
    player: { x: w / 2 - PW / 2, y: h * 0.72, targetX: w / 2 - PW / 2 },
    hp: MAX_HP, invuln: 0,
    projectiles: [], rain: initRain(w, h), fx: [],
    score: 0, combo: 0, maxCombo: 0, nearMisses: 0, dodges: 0,
    hitsTaken: 0, btUses: 0,
    btBar: 0, btActive: false, btTimer: 0,
    surviveTime: 0, difficulty: 1, spawnTimer: 0, diffTimer: 0, nmCooldown: 0,
    running: true, contestTime: CONTEST_SECS,
  };
}

// --- Spawn Patterns ---
export function spawnPattern(w, difficulty) {
  const speed = BASE_SPEED + (difficulty - 1) * SPEED_PER_DIFF;
  const pats = ['random'];
  if (difficulty > 1.5) pats.push('burst');
  if (difficulty > 2.5) pats.push('wall_gap');
  if (difficulty > 3) pats.push('diagonal');
  if (difficulty > 3.5) pats.push('fan');
  if (difficulty > 4) pats.push('ghost');
  const pat = pick(pats);
  const projs = [];
  const mk = (x, vy, vx = 0, ghost = false) => ({
    x, y: -10, vx, vy: vy || speed, r: PROJ_R,
    trail: [], passed: false, nearMissed: false, ghost, ghostTimer: ghost ? rand(0.3, 0.8) : 0,
  });
  switch (pat) {
    case 'burst': { const cx = rand(40, w - 40); for (let i = 0; i < 3; i++) projs.push(mk(cx + (i - 1) * 22, speed)); break; }
    case 'wall_gap': {
      const gx = rand(50, w - 50), gw = 50;
      for (let x = 10; x < w - 10; x += 28) if (Math.abs(x - gx) > gw / 2) projs.push(mk(x, speed * 0.8));
      break;
    }
    case 'diagonal': {
      const fl = Math.random() > 0.5;
      for (let i = 0; i < 5; i++) projs.push(mk(fl ? 10 + i * 30 : w - 10 - i * 30, speed, fl ? 30 : -30));
      break;
    }
    case 'fan': { for (let i = -2; i <= 2; i++) projs.push(mk(w / 2, speed, i * 35)); break; }
    case 'ghost': { projs.push(mk(rand(20, w - 20), speed, 0, true)); projs.push(mk(rand(20, w - 20), speed)); break; }
    default: {
      const cnt = Math.floor(rand(1, Math.min(4, 1 + difficulty)));
      for (let i = 0; i < cnt; i++) projs.push(mk(rand(15, w - 15), speed + rand(-20, 20)));
    }
  }
  return projs;
}

// --- Render: Background ---
export function renderBg(ctx, w, h) {
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, w, h);
}

// --- Render: Rain ---
export function renderRain(ctx, rain, w, h, intensity) {
  ctx.font = '12px monospace';
  for (const col of rain) {
    for (let i = 0; i < col.chars.length; i++) {
      const cy = col.y - i * 16;
      if (cy < -16 || cy > h + 16) continue;
      const a = i === 0 ? 0.9 : Math.max(0.03, (1 - i / col.chars.length) * 0.35);
      ctx.fillStyle = i === 0
        ? `rgba(180,255,180,${a * intensity})`
        : `rgba(0,255,65,${a * intensity})`;
      ctx.fillText(col.chars[i], col.x, cy);
    }
  }
}

// --- Render: Player Silhouette ---
export function renderPlayer(ctx, x, y, invuln, btActive, combo, alpha) {
  const invA = invuln > 0 ? (Math.sin(invuln * 20) > 0 ? 0.3 : 0.85) : 1;
  ctx.save();
  ctx.globalAlpha = invA * (alpha ?? 1);
  const glow = btActive || combo >= 5;
  if (glow) { ctx.shadowBlur = btActive ? 18 : 10; ctx.shadowColor = btActive ? '#00ffff' : '#00ff41'; }
  const cx = x + PW / 2;
  ctx.beginPath(); ctx.arc(cx, y + 7, 6, 0, Math.PI * 2);
  ctx.fillStyle = '#001a08'; ctx.fill();
  ctx.strokeStyle = '#00ff41'; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(cx - 9, y + 15); ctx.lineTo(cx + 9, y + 15);
  ctx.lineTo(cx + 11, y + PH - 4); ctx.lineTo(cx - 11, y + PH - 4);
  ctx.closePath(); ctx.fillStyle = '#001a08'; ctx.fill(); ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(cx - 11, y + PH - 4); ctx.lineTo(cx - 15, y + PH + 2);
  ctx.moveTo(cx + 11, y + PH - 4); ctx.lineTo(cx + 15, y + PH + 2);
  ctx.stroke();
  ctx.restore();
}

// --- Render: Projectiles ---
export function renderProjectiles(ctx, projs, btActive) {
  for (const p of projs) {
    if (p.passed || (p.ghost && p.ghostTimer > 0)) continue;
    for (let i = 0; i < p.trail.length; i++) {
      const a = (1 - i / p.trail.length) * (btActive ? 0.4 : 0.25);
      ctx.beginPath();
      ctx.arc(p.trail[i].x, p.trail[i].y, p.r * (1 - i * 0.1), 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0,255,65,${a})`;
      ctx.fill();
    }
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r * 2.5, 0, Math.PI * 2);
    ctx.fillStyle = btActive ? 'rgba(0,255,255,0.1)' : 'rgba(0,255,65,0.1)';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = '#00ff41';
    ctx.fill();
  }
}

// --- Render: Text Effects ---
export function renderTextFx(ctx, fx) {
  for (const f of fx) {
    if (f.type !== 'text') continue;
    const a = f.life / f.maxLife;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.font = f.big ? 'bold 16px monospace' : 'bold 10px monospace';
    ctx.fillStyle = f.color;
    ctx.textAlign = 'center';
    ctx.fillText(f.text, f.x, f.y - (f.maxLife - f.life) * 30);
    ctx.restore();
  }
}

// --- Render: Vignette (Bullet Time) ---
export function renderVignette(ctx, w, h, active) {
  if (!active) return;
  const g = ctx.createRadialGradient(w / 2, h / 2, h * 0.3, w / 2, h / 2, h * 0.7);
  g.addColorStop(0, 'transparent');
  g.addColorStop(1, 'rgba(0,20,0,0.4)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, w, h);
}

// --- Update: Rain ---
export function updateRain(rain, w, h, dt) {
  for (const col of rain) {
    col.y += col.speed * dt;
    if (col.y - col.len * 16 > h) {
      col.y = rand(-100, -20);
      col.chars = Array.from({ length: col.len }, mchar);
    }
  }
}

// --- Collision: Circle vs Rect ---
export function circleRect(cx, cy, cr, rx, ry, rw, rh) {
  const nx = clamp(cx, rx, rx + rw);
  const ny = clamp(cy, ry, ry + rh);
  const dx = cx - nx, dy = cy - ny;
  return dx * dx + dy * dy < cr * cr;
}

// --- Score helper ---
export function calcScore(g, extraBonus) {
  const combo = g.maxCombo * 6;
  const noHit = g.hitsTaken === 0 ? 80 : 0;
  return Math.min(999, Math.max(0, Math.round(g.score + combo + noHit + (extraBonus || 0))));
}
