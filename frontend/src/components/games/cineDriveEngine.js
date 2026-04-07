/* ===================================================================
   CINE DRIVE ENGINE — Shared logic for Auto Cinematografica
   Canvas rendering, perspective road, neon/synthwave style
   =================================================================== */

// --- Constants ---
export const CAR_W = 30, CAR_H = 52, HB_W = 22, HB_H = 40;
export const VY = 0.10, RTW = 0.15, RBW = 0.84;
export const CT = 45, MXT = 120, MHP = 3, INV = 1.0;
export const NMD = 14, NMCD = 0.4;
export const OBS_HB = { ciak:[12,10], reel:[11,11], camera:[14,8], spotlight:[10,10], trophy:[8,10], barrier:[16,6] };
export const OBS_IDS = Object.keys(OBS_HB);
export const BON_IDS = ['star','ticket','lightning','crown'];
export const BON_D = { star:{s:20}, ticket:{s:15}, lightning:{s:5,fx:'slow'}, crown:{s:5,fx:'shield'} };

export const PAL = {
  neon:  { road:'#0a0a1a', line:'#ff00ff', glow:'#ff00ff', acc:'#00ffff', sky:'#05051a', cg:'#ff00ff' },
  rain:  { road:'#0a0a15', line:'#4488ff', glow:'#4488ff', acc:'#88bbff', sky:'#0a0a20', cg:'#4488ff' },
  tunnel:{ road:'#050510', line:'#ff6600', glow:'#ff6600', acc:'#ffaa00', sky:'#020205', cg:'#ff6600' },
  synth: { road:'#0d001a', line:'#ff00aa', glow:'#ff00aa', acc:'#aa00ff', sky:'#0a0020', cg:'#ff00aa' },
  stunt: { road:'#0a0a0a', line:'#ff3300', glow:'#ff3300', acc:'#ffaa00', sky:'#0a0505', cg:'#ff3300' },
  emer:  { road:'#0a0a1a', line:'#0066ff', glow:'#ff0044', acc:'#0066ff', sky:'#050510', cg:'#ff0044' },
};

// --- Helpers ---
export const lerp = (a, b, t) => a + (b - a) * Math.min(1, t);
export const rand = (a, b) => Math.random() * (b - a) + a;
export const pick = a => a[Math.floor(Math.random() * a.length)];
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// --- Perspective ---
export function roadAt(y, w, h) {
  const vy = h * VY, t = clamp((y - vy) / (h - vy), 0, 1);
  const rw = lerp(w * RTW, w * RBW, t), l = (w - rw) / 2;
  return { l, r: l + rw, w: rw, t };
}
export function lnX(lane, y, w, h) { const r = roadAt(y, w, h); return r.l + (lane + 0.5) * r.w / 3; }
export function scAt(y, h) { return clamp((y - h * VY) / (h - h * VY), 0.3, 1.2); }

// --- Init Skyline ---
export function initSky(w) {
  const b = []; let x = 0;
  while (x < w + 40) {
    const bw = rand(12, 35), bh = rand(25, 90), wins = [];
    for (let wy = 5; wy < bh - 3; wy += 6)
      for (let wx = 3; wx < bw - 3; wx += 5)
        if (Math.random() > 0.5) wins.push({ x: wx, y: wy, c: `rgba(255,${~~rand(150,220)},${~~rand(50,120)},${rand(0.12,0.35).toFixed(2)})` });
    b.push({ x, w: bw, h: bh, wins }); x += bw + rand(2, 8);
  }
  return b;
}

// --- Draw Skyline ---
export function drawSky(ctx, sky, w, h, p) {
  const by = h * VY;
  const g = ctx.createLinearGradient(0, 0, 0, by);
  g.addColorStop(0, p.sky); g.addColorStop(1, p.road);
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, by);
  for (const b of sky) {
    ctx.fillStyle = '#0a0a18'; ctx.fillRect(b.x, by - b.h, b.w, b.h);
    for (const wi of b.wins) { ctx.fillStyle = wi.c; ctx.fillRect(b.x + wi.x, by - b.h + wi.y, 2, 3); }
  }
}

// --- Draw Road ---
export function drawRoad(ctx, w, h, scroll, p) {
  const vy = h * VY;
  const { l: tl, r: tr } = roadAt(vy, w, h), { l: bl, r: br } = roadAt(h, w, h);
  ctx.beginPath(); ctx.moveTo(tl, vy); ctx.lineTo(tr, vy); ctx.lineTo(br, h); ctx.lineTo(bl, h);
  ctx.closePath(); ctx.fillStyle = p.road; ctx.fill();
  // Edges
  ctx.save(); ctx.shadowBlur = 4; ctx.shadowColor = p.glow;
  ctx.beginPath(); ctx.moveTo(tl, vy); ctx.lineTo(bl, h); ctx.moveTo(tr, vy); ctx.lineTo(br, h);
  ctx.strokeStyle = p.glow + '50'; ctx.lineWidth = 1.5; ctx.stroke(); ctx.restore();
  // Center dashes
  for (let i = 0; i < 10; i++) {
    const t = ((i / 10 + scroll * 0.12) % 1), py = vy + t * t * (h - vy);
    const dl = 6 + t * 12, rd = roadAt(py, w, h), cx = rd.l + rd.w / 2;
    if (py + dl > h || py < vy) continue;
    ctx.beginPath(); ctx.moveTo(cx, py); ctx.lineTo(cx, py + dl);
    ctx.strokeStyle = p.line; ctx.globalAlpha = 0.15 + t * 0.4; ctx.lineWidth = 1 + t; ctx.stroke();
  }
  ctx.globalAlpha = 1;
  // Speed streaks
  for (let i = 0; i < 6; i++) {
    const t = ((i / 6 + scroll * 0.15) % 1), py = vy + t * t * (h - vy), s = t;
    const rd = roadAt(py, w, h);
    ctx.globalAlpha = s * 0.15; ctx.strokeStyle = p.glow; ctx.lineWidth = 0.5 + s * 0.5;
    ctx.beginPath(); ctx.moveTo(rd.l + 2, py); ctx.lineTo(rd.l + 2, py + 4 + s * 6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(rd.r - 2, py); ctx.lineTo(rd.r - 2, py + 4 + s * 6); ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

// --- Draw Car ---
export function drawCar(ctx, x, y, tilt, shield, turbo, p) {
  ctx.save(); ctx.translate(x, y); if (tilt) ctx.rotate(tilt);
  const cw = CAR_W, ch = CAR_H;
  // Underglow
  ctx.shadowBlur = turbo ? 22 : 14; ctx.shadowColor = p.cg;
  // Exhaust trail
  const tg = ctx.createLinearGradient(0, ch / 2, 0, ch / 2 + (turbo ? 30 : 18));
  tg.addColorStop(0, p.cg + '50'); tg.addColorStop(1, 'transparent');
  ctx.fillStyle = tg; ctx.fillRect(turbo ? -8 : -5, ch / 2, turbo ? 16 : 10, turbo ? 30 : 18);
  // Body
  ctx.beginPath();
  ctx.moveTo(-cw / 2 + 5, -ch / 2); ctx.lineTo(cw / 2 - 5, -ch / 2);
  ctx.quadraticCurveTo(cw / 2, -ch / 2, cw / 2, -ch / 2 + 5);
  ctx.lineTo(cw / 2, ch / 2 - 3); ctx.quadraticCurveTo(cw / 2, ch / 2, cw / 2 - 3, ch / 2);
  ctx.lineTo(-cw / 2 + 3, ch / 2); ctx.quadraticCurveTo(-cw / 2, ch / 2, -cw / 2, ch / 2 - 3);
  ctx.lineTo(-cw / 2, -ch / 2 + 5); ctx.quadraticCurveTo(-cw / 2, -ch / 2, -cw / 2 + 5, -ch / 2);
  ctx.closePath(); ctx.fillStyle = '#1a1a2e'; ctx.fill();
  ctx.strokeStyle = p.cg; ctx.lineWidth = 1.3; ctx.stroke();
  // Hood
  ctx.shadowBlur = 0; ctx.fillStyle = '#141428';
  ctx.beginPath(); ctx.moveTo(-cw / 2 + 5, -ch / 2); ctx.lineTo(cw / 2 - 5, -ch / 2);
  ctx.lineTo(cw / 2 - 3, -ch / 2 + 12); ctx.lineTo(-cw / 2 + 3, -ch / 2 + 12); ctx.closePath(); ctx.fill();
  // Windshield
  ctx.beginPath(); ctx.moveTo(-cw / 2 + 5, -ch / 2 + 13); ctx.lineTo(cw / 2 - 5, -ch / 2 + 13);
  ctx.lineTo(cw / 2 - 6, -ch / 2 + 20); ctx.lineTo(-cw / 2 + 6, -ch / 2 + 20); ctx.closePath();
  ctx.fillStyle = 'rgba(100,160,255,0.25)'; ctx.fill();
  ctx.strokeStyle = 'rgba(100,160,255,0.4)'; ctx.lineWidth = 0.6; ctx.stroke();
  // Roof
  ctx.fillStyle = '#161630'; ctx.fillRect(-cw / 2 + 6, -ch / 2 + 20, cw - 12, 12);
  // Rear window
  ctx.beginPath(); ctx.moveTo(-cw / 2 + 6, -ch / 2 + 32); ctx.lineTo(cw / 2 - 6, -ch / 2 + 32);
  ctx.lineTo(cw / 2 - 5, -ch / 2 + 38); ctx.lineTo(-cw / 2 + 5, -ch / 2 + 38); ctx.closePath();
  ctx.fillStyle = 'rgba(100,160,255,0.15)'; ctx.fill();
  // Headlights
  ctx.shadowBlur = 8; ctx.shadowColor = '#fff'; ctx.fillStyle = '#fff';
  ctx.fillRect(-cw / 2 + 2, -ch / 2 + 1, 5, 3); ctx.fillRect(cw / 2 - 7, -ch / 2 + 1, 5, 3);
  // Beams
  ctx.shadowBlur = 0;
  const bm = ctx.createLinearGradient(0, -ch / 2, 0, -ch / 2 - 25);
  bm.addColorStop(0, 'rgba(255,255,200,0.12)'); bm.addColorStop(1, 'transparent');
  ctx.fillStyle = bm; ctx.beginPath();
  ctx.moveTo(-cw / 2 + 1, -ch / 2); ctx.lineTo(-cw / 2 - 4, -ch / 2 - 25);
  ctx.lineTo(cw / 2 + 4, -ch / 2 - 25); ctx.lineTo(cw / 2 - 1, -ch / 2); ctx.closePath(); ctx.fill();
  // Taillights
  ctx.shadowBlur = 5; ctx.shadowColor = '#ff0033'; ctx.fillStyle = '#ff0033';
  ctx.fillRect(-cw / 2 + 3, ch / 2 - 4, 6, 2); ctx.fillRect(cw / 2 - 9, ch / 2 - 4, 6, 2);
  // Wheels
  ctx.shadowBlur = 0; ctx.fillStyle = '#0a0a0a';
  ctx.fillRect(-cw / 2 - 2, -ch / 2 + 4, 3, 8); ctx.fillRect(cw / 2 - 1, -ch / 2 + 4, 3, 8);
  ctx.fillRect(-cw / 2 - 2, ch / 2 - 12, 3, 8); ctx.fillRect(cw / 2 - 1, ch / 2 - 12, 3, 8);
  // Shield
  if (shield) {
    ctx.beginPath(); ctx.ellipse(0, 0, cw / 2 + 8, ch / 2 + 8, 0, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255,215,0,0.4)'; ctx.lineWidth = 2;
    ctx.shadowBlur = 8; ctx.shadowColor = '#ffd700'; ctx.stroke();
  }
  ctx.restore();
}

// --- Draw Obstacle ---
export function drawObs(ctx, type, x, y, s, p) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.shadowBlur = 3; ctx.shadowColor = p.acc;
  switch (type) {
    case 'ciak':
      ctx.fillStyle = '#1a1a1a'; ctx.fillRect(-12, -8, 24, 16);
      ctx.fillStyle = '#333'; ctx.fillRect(-12, -12, 24, 4);
      ctx.fillStyle = '#fff'; for (let i = 0; i < 4; i++) ctx.fillRect(-10 + i * 6, -12, 3, 4);
      ctx.strokeStyle = p.acc; ctx.lineWidth = 0.8; ctx.strokeRect(-12, -12, 24, 20); break;
    case 'reel':
      ctx.beginPath(); ctx.arc(0, 0, 11, 0, Math.PI * 2); ctx.fillStyle = '#111'; ctx.fill();
      ctx.strokeStyle = p.acc; ctx.lineWidth = 1; ctx.stroke();
      ctx.beginPath(); ctx.arc(0, 0, 4, 0, Math.PI * 2); ctx.stroke();
      for (let a = 0; a < 6; a++) { ctx.beginPath(); const an = a * Math.PI / 3; ctx.moveTo(0, 0); ctx.lineTo(Math.cos(an) * 9, Math.sin(an) * 9); ctx.stroke(); } break;
    case 'camera':
      ctx.fillStyle = '#1a1a1a'; ctx.fillRect(-10, -7, 20, 14);
      ctx.beginPath(); ctx.arc(13, 0, 5, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = p.acc; ctx.lineWidth = 0.8; ctx.strokeRect(-10, -7, 20, 14);
      ctx.beginPath(); ctx.arc(13, 0, 5, 0, Math.PI * 2); ctx.stroke(); break;
    case 'spotlight':
      ctx.beginPath(); ctx.moveTo(0, -10); ctx.lineTo(-9, 8); ctx.lineTo(9, 8); ctx.closePath();
      ctx.fillStyle = '#1a1a1a'; ctx.fill(); ctx.strokeStyle = '#ffaa00'; ctx.lineWidth = 1; ctx.stroke();
      ctx.beginPath(); ctx.arc(0, -10, 3, 0, Math.PI * 2); ctx.fillStyle = '#ffdd00'; ctx.fill(); break;
    case 'trophy':
      ctx.beginPath(); ctx.moveTo(-7, -9); ctx.lineTo(7, -9); ctx.lineTo(5, 0); ctx.lineTo(2, 3);
      ctx.lineTo(2, 7); ctx.lineTo(6, 9); ctx.lineTo(-6, 9); ctx.lineTo(-2, 7);
      ctx.lineTo(-2, 3); ctx.lineTo(-5, 0); ctx.closePath();
      ctx.fillStyle = '#332200'; ctx.fill(); ctx.strokeStyle = '#ffd700'; ctx.lineWidth = 1; ctx.stroke(); break;
    case 'barrier':
      ctx.fillStyle = '#222'; ctx.fillRect(-15, -5, 30, 10);
      ctx.fillStyle = '#ff3300'; for (let i = 0; i < 3; i++) ctx.fillRect(-13 + i * 10, -3, 6, 6);
      ctx.strokeStyle = p.acc; ctx.lineWidth = 0.8; ctx.strokeRect(-15, -5, 30, 10); break;
  }
  ctx.restore();
}

// --- Draw Bonus ---
export function drawBon(ctx, type, x, y, s, time) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  const pu = 1 + Math.sin(time * 5) * 0.1; ctx.scale(pu, pu);
  switch (type) {
    case 'star':
      ctx.shadowBlur = 8; ctx.shadowColor = '#ffd700'; ctx.fillStyle = '#ffd700';
      ctx.beginPath(); for (let i = 0; i < 10; i++) { const a = (i * Math.PI / 5) - Math.PI / 2, r = i % 2 === 0 ? 8 : 3.5; i === 0 ? ctx.moveTo(Math.cos(a) * r, Math.sin(a) * r) : ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
      ctx.closePath(); ctx.fill(); break;
    case 'ticket':
      ctx.shadowBlur = 6; ctx.shadowColor = '#ff3344'; ctx.fillStyle = '#ff3344';
      ctx.fillRect(-7, -4, 14, 8); ctx.fillStyle = '#fff'; ctx.fillRect(-7, -4, 3, 8); break;
    case 'lightning':
      ctx.shadowBlur = 8; ctx.shadowColor = '#00ffff'; ctx.fillStyle = '#00ffff';
      ctx.beginPath(); ctx.moveTo(-3, -8); ctx.lineTo(3, -2); ctx.lineTo(0, -2);
      ctx.lineTo(4, 8); ctx.lineTo(-3, 2); ctx.lineTo(0, 2); ctx.closePath(); ctx.fill(); break;
    case 'crown':
      ctx.shadowBlur = 8; ctx.shadowColor = '#ffd700'; ctx.fillStyle = '#ffd700';
      ctx.beginPath(); ctx.moveTo(-8, 3); ctx.lineTo(-8, -3); ctx.lineTo(-4, 0);
      ctx.lineTo(0, -6); ctx.lineTo(4, 0); ctx.lineTo(8, -3); ctx.lineTo(8, 3); ctx.closePath(); ctx.fill(); break;
  }
  ctx.restore();
}

// --- Draw Particles ---
export function drawParts(ctx, parts) {
  for (const p of parts) {
    ctx.globalAlpha = p.life / p.ml; ctx.fillStyle = p.c;
    ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

// --- Collision AABB ---
export function aabb(ax, ay, aw, ah, bx, by, bw, bh) {
  return ax - aw / 2 < bx + bw / 2 && ax + aw / 2 > bx - bw / 2 && ay - ah / 2 < by + bh / 2 && ay + ah / 2 > by - bh / 2;
}

// --- Score ---
export function calcSc(g, extra) { return Math.min(999, Math.max(0, Math.round(g.score + g.maxCombo * 5 + (g.hitsTaken === 0 ? 60 : 0) + (extra || 0)))); }
