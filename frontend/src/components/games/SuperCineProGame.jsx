/* ===================================================================
   SUPERCINE — PRO ASSURDA
   Platformer cinematografico epico. Mobile-first, canvas.
   =================================================================== */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  PW, PH, ZONE_NAMES,
  initGame, updateGame, render, calcFinalScore, calcRank, rankColor,
} from './superCineProEngine';
import './superCinePro.css';

export function SuperCineProGame({ mode = 'contest', onComplete }) {
  const canvasRef = useRef(null), contRef = useRef(null), gRef = useRef(null);
  const rafRef = useRef(null), uiRef = useRef(null), doneRef = useRef(false);
  const inputRef = useRef({ left: false, right: false, jump: false, jumpPressed: false });
  const cbRef = useRef(onComplete); cbRef.current = onComplete;

  const [ui, setUi] = useState({ phase: 'intro', score: 0, stars: 0, totalStars: 0, hp: 3, time: 0, zone: '', powerup: null, completed: false, damage: 0, secrets: 0, totalSecrets: 0, runTime: 0, rank: 'D', rankC: '#888', screenX: 0, screenY: 0, facing: 1, invuln: false });

  const startGame = useCallback(() => {
    const g = gRef.current; if (!g) return;
    g.phase = 'play';
    setUi(u => ({ ...u, phase: 'play' }));
  }, []);

  const pauseGame = useCallback(() => {
    const g = gRef.current; if (!g) return;
    if (g.phase === 'play') { g.phase = 'paused'; setUi(u => ({ ...u, phase: 'paused' })); }
    else if (g.phase === 'paused') { g.phase = 'play'; setUi(u => ({ ...u, phase: 'play' })); }
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current, cont = contRef.current;
    if (!canvas || !cont) return;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.floor(cont.getBoundingClientRect().width), h = 400;
    canvas.width = w * dpr; canvas.height = h * dpr;
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);

    const g = initGame(w, h, mode);
    gRef.current = g;
    let lt = performance.now();

    // Keyboard
    const kd = (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'a') inputRef.current.left = true;
      if (e.key === 'ArrowRight' || e.key === 'd') inputRef.current.right = true;
      if (e.key === ' ' || e.key === 'ArrowUp' || e.key === 'w') { inputRef.current.jump = true; inputRef.current.jumpPressed = true; e.preventDefault(); }
      if (e.key === 'Escape' || e.key === 'p') pauseGame();
    };
    const ku = (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'a') inputRef.current.left = false;
      if (e.key === 'ArrowRight' || e.key === 'd') inputRef.current.right = false;
      if (e.key === ' ' || e.key === 'ArrowUp' || e.key === 'w') inputRef.current.jump = false;
    };
    window.addEventListener('keydown', kd); window.addEventListener('keyup', ku);

    // ===== SUPERCINE – CONTROLLI TOUCH CINEMATOGRAFICI =====
    const SWIPE_MOVE_THRESHOLD = 30;
    let touchStartX = 0, touchStartY = 0, isTouching = false, jumpTriggered = false;

    const onTS = (e) => {
      const t = e.touches[0];
      touchStartX = t.clientX; touchStartY = t.clientY;
      isTouching = true; jumpTriggered = false;
    };
    const onTM = (e) => {
      if (!isTouching) return;
      const t = e.touches[0];
      const dx = t.clientX - touchStartX, dy = t.clientY - touchStartY;
      // Movimento orizzontale
      if (Math.abs(dx) > SWIPE_MOVE_THRESHOLD) {
        inputRef.current.left = dx < 0; inputRef.current.right = dx > 0;
      }
      // Salto (swipe up)
      if (!jumpTriggered && dy < -40) {
        inputRef.current.jump = true; inputRef.current.jumpPressed = true;
        jumpTriggered = true;
      }
    };
    const onTE = () => {
      if (!isTouching) return;
      setTimeout(() => { inputRef.current.left = false; inputRef.current.right = false; inputRef.current.jump = false; }, 120);
      isTouching = false; jumpTriggered = false;
    };
    cont.addEventListener('touchstart', onTS, { passive: true });
    cont.addEventListener('touchmove', onTM, { passive: true });
    cont.addEventListener('touchend', onTE, { passive: true });

    const loop = () => {
      const now = performance.now(), dt = (now - lt) / 1000; lt = now;
      g.input = { ...inputRef.current };
      if (inputRef.current.jumpPressed) inputRef.current.jumpPressed = false;

      updateGame(g, dt);
      render(ctx, g);

      // End conditions
      if (g.phase === 'over' && !doneRef.current) {
        doneRef.current = true;
        const fs = calcFinalScore(g);
        setUi(u => ({ ...u, phase: 'over', score: fs, rank: calcRank(fs), rankC: rankColor(calcRank(fs)) }));
        setTimeout(() => cbRef.current(fs), 3000);
      }
      if (g.phase === 'results' && !doneRef.current) {
        doneRef.current = true;
        const fs = calcFinalScore(g);
        const rk = calcRank(fs);
        setUi(u => ({ ...u, phase: 'results', score: fs, rank: rk, rankC: rankColor(rk), completed: true }));
        setTimeout(() => cbRef.current(fs), 4000);
      }

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    uiRef.current = setInterval(() => {
      const gg = gRef.current; if (!gg) return;
      const sx = gg.player.x + PW / 2 - gg.cam.x;
      const sy = gg.player.y + PH / 2 - gg.cam.y;
      setUi(u => ({
        ...u,
        stars: gg.stars, totalStars: gg.level.totalStars, hp: gg.player.hp,
        time: Math.ceil(gg.time), zone: ZONE_NAMES[gg.zone] || '',
        powerup: gg.activePowerup, damage: gg.damage, secrets: gg.secretsFound,
        totalSecrets: gg.level.totalSecrets, runTime: gg.runTime,
        screenX: sx, screenY: sy, facing: gg.player.facing, invuln: gg.player.invuln > 0,
      }));
    }, 60);

    return () => {
      cancelAnimationFrame(rafRef.current); clearInterval(uiRef.current);
      window.removeEventListener('keydown', kd); window.removeEventListener('keyup', ku);
      cont.removeEventListener('touchstart', onTS); cont.removeEventListener('touchmove', onTM); cont.removeEventListener('touchend', onTE);
    };
  }, [mode, pauseGame]);

  // Touch controls
  const onBtn = useCallback((btn, down) => {
    if (btn === 'left') inputRef.current.left = down;
    if (btn === 'right') inputRef.current.right = down;
    if (btn === 'jump') { inputRef.current.jump = down; if (down) inputRef.current.jumpPressed = true; }
  }, []);

  return (
    <div ref={contRef} className="scp-container" style={{ height: 400 }} data-testid="minigame-supercine-pro">
      <canvas ref={canvasRef} className="scp-canvas" />
      {/* SuperCine character PNG overlay */}
      {(ui.phase === 'play' || ui.phase === 'paused' || ui.phase === 'results' || ui.phase === 'over') && (
        <img
          src="/assets/supercine/character.png"
          alt="SuperCine"
          className={ui.invuln ? 'scp-char-invuln' : ''}
          style={{
            position: 'absolute',
            left: ui.screenX,
            top: ui.screenY,
            width: 42,
            height: 42,
            transform: `translate(-50%, -50%) scaleX(${ui.facing})`,
            pointerEvents: 'none',
            zIndex: 5,
            imageRendering: 'auto',
            filter: ui.powerup ? 'drop-shadow(0 0 6px #ffd700)' : 'drop-shadow(0 0 3px rgba(0,0,0,0.5))',
            opacity: ui.phase === 'over' ? 0.4 : 1,
            transition: 'filter 0.3s, opacity 0.3s',
          }}
          onError={(e) => { console.error('SuperCine character missing:', e.currentTarget.src); e.currentTarget.style.display = 'none'; }}
        />
      )}

      {/* HUD */}
      {ui.phase === 'play' && (
        <div className="scp-hud">
          <div className="scp-hud-row">
            <div>
              <span className="scp-hud-label">STELLE</span>
              <span className="scp-hud-val scp-gold">{ui.stars}/{ui.totalStars}</span>
            </div>
            <div>
              <span className="scp-hud-label">{mode === 'contest' ? 'TEMPO' : 'TEMPO'}</span>
              <span className={`scp-hud-val ${ui.time <= 15 ? 'scp-red scp-blink' : ''}`}>{ui.time}s</span>
            </div>
            <div className="scp-hud-hp">
              {[0, 1, 2].map(i => <div key={i} className={`scp-hp-dot ${i < ui.hp ? 'on' : ''}`} />)}
            </div>
            <button className="scp-pause-btn" onPointerDown={pauseGame} data-testid="scp-pause">||</button>
          </div>
          {ui.powerup && <div className="scp-powerup-badge">{ui.powerup === 'sprint' ? 'SPRINT' : ui.powerup === 'megaciak' ? 'MEGACIAK' : 'STELLA'}</div>}
        </div>
      )}

      {/* Mobile Controls */}
      {(ui.phase === 'play') && (
        <div className="scp-controls" data-testid="scp-controls">
          <div className="scp-ctrl-left">
            <button className="scp-btn scp-btn-dir"
              onPointerDown={() => onBtn('left', true)} onPointerUp={() => onBtn('left', false)} onPointerLeave={() => onBtn('left', false)}
              onTouchStart={(e) => { e.preventDefault(); onBtn('left', true); }} onTouchEnd={() => onBtn('left', false)}
              data-testid="scp-left">&#9664;</button>
            <button className="scp-btn scp-btn-dir"
              onPointerDown={() => onBtn('right', true)} onPointerUp={() => onBtn('right', false)} onPointerLeave={() => onBtn('right', false)}
              onTouchStart={(e) => { e.preventDefault(); onBtn('right', true); }} onTouchEnd={() => onBtn('right', false)}
              data-testid="scp-right">&#9654;</button>
          </div>
          <button className="scp-btn scp-btn-jump"
            onPointerDown={() => onBtn('jump', true)} onPointerUp={() => onBtn('jump', false)} onPointerLeave={() => onBtn('jump', false)}
            onTouchStart={(e) => { e.preventDefault(); onBtn('jump', true); }} onTouchEnd={() => onBtn('jump', false)}
            data-testid="scp-jump">JUMP</button>
        </div>
      )}

      {/* INTRO */}
      {ui.phase === 'intro' && (
        <div className="scp-overlay" data-testid="scp-intro">
          <div className="scp-intro-box">
            <p className="scp-title">SUPERCINE</p>
            <p className="scp-subtitle">AIUTA IL NOSTRO AMICO REGISTA CINEOX!</p>
            <div className="scp-rules">
              <p>Completa il livello, raccogli stelle, evita ostacoli!</p>
              <p>7 zone cinematografiche, segreti nascosti, powerup</p>
              <p>Rank finale basato su tempo, stelle, danni, segreti</p>
            </div>
            <button className="scp-start-btn" onPointerDown={startGame} data-testid="scp-start">AZIONE!</button>
            <p className="scp-hint">Mobile: tasti su schermo | Desktop: Frecce + Spazio</p>
          </div>
        </div>
      )}

      {/* PAUSED */}
      {ui.phase === 'paused' && (
        <div className="scp-overlay" data-testid="scp-paused">
          <div className="scp-pause-box">
            <p className="scp-pause-title">PAUSA</p>
            <p className="scp-pause-stats">Stelle: {ui.stars}/{ui.totalStars} | Tempo: {ui.time}s | Danni: {ui.damage}</p>
            <button className="scp-start-btn" onPointerDown={pauseGame}>RIPRENDI</button>
          </div>
        </div>
      )}

      {/* GAME OVER */}
      {ui.phase === 'over' && (
        <div className="scp-overlay scp-over-bg" data-testid="scp-gameover">
          <div className="scp-result-box">
            <p className="scp-over-title">TEMPO SCADUTO</p>
            <p className="scp-score-big">{ui.score}</p>
            <p className="scp-rank" style={{ color: ui.rankC }}>{ui.rank}</p>
            <div className="scp-stats-grid">
              <span>Stelle: {ui.stars}/{ui.totalStars}</span>
              <span>Danni: {ui.damage}</span>
              <span>Segreti: {ui.secrets}/{ui.totalSecrets}</span>
              <span>Tempo: {Math.floor(ui.runTime)}s</span>
            </div>
          </div>
        </div>
      )}

      {/* RESULTS (completed) */}
      {ui.phase === 'results' && (
        <div className="scp-overlay scp-result-bg" data-testid="scp-results">
          <div className="scp-result-box scp-result-win">
            <p className="scp-win-title">PREMIERE COMPLETATA!</p>
            <p className="scp-score-big scp-glow-gold">{ui.score}</p>
            <p className="scp-rank scp-rank-big" style={{ color: ui.rankC }}>{ui.rank}</p>
            <div className="scp-stats-grid">
              <span>Stelle: {ui.stars}/{ui.totalStars}</span>
              <span>Danni: {ui.damage}</span>
              <span>Segreti: {ui.secrets}/{ui.totalSecrets}</span>
              <span>Tempo: {Math.floor(ui.runTime)}s</span>
            </div>
            <p className="scp-congrats">{ui.rank === 'LEGENDARY DIRECTOR' ? 'SEI UNA LEGGENDA!' : ui.rank === 'S+' ? 'INCREDIBILE!' : ui.rank === 'S' ? 'SPETTACOLARE!' : 'BEN FATTO!'}</p>
          </div>
        </div>
      )}
    </div>
  );
}
