import React, { useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';

const CINEMA_WORDS = [
  'HYPE', 'VIRAL', 'FLOP', 'STAR', 'OSCAR', 'BOX OFFICE', 'PREMIERE',
  'BLOCKBUSTER', 'SEQUEL', 'CULT', 'HIT', 'BOOM', 'LEGEND', 'FAME',
  'ACTION', 'DRAMA', 'THRILLER', 'EPIC', 'CINEMA', 'STUDIO', 'MAJOR',
  'CUT', 'CIAK', 'REGIA', 'CAST', 'CREW', 'SET', 'TAKE',
];

export default function MatrixOverlay({ filmTitles = [], actorNames = [], onReveal, duration = 2500 }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const revealedRef = useRef(false);
  // Enforce minimum duration of 8s
  const safeDuration = Math.max(8000, duration);

  const allWords = useCallback(() => {
    const w = [...CINEMA_WORDS, ...filmTitles.slice(0, 10), ...actorNames.slice(0, 10)];
    return w;
  }, [filmTitles, actorNames]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = window.innerWidth;
    const H = window.innerHeight;
    canvas.width = W;
    canvas.height = H;

    const isMobile = W < 600;
    const fontSize = isMobile ? 12 : 14;
    const cols = Math.floor(W / (fontSize * 0.8));
    const drops = new Array(cols).fill(0).map(() => Math.random() * -50);
    const speeds = new Array(cols).fill(0).map(() => 0.3 + Math.random() * 0.7);
    const words = allWords();
    const startTime = Date.now();

    const draw = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(1, elapsed / safeDuration);

      // Fade trail
      ctx.fillStyle = 'rgba(0, 0, 0, 0.06)';
      ctx.fillRect(0, 0, W, H);

      ctx.font = `${fontSize}px 'Courier New', monospace`;

      for (let i = 0; i < cols; i++) {
        const x = i * fontSize * 0.8;
        const y = drops[i] * fontSize;

        // Pick random character or word fragment
        let char;
        if (Math.random() < 0.08) {
          const word = words[Math.floor(Math.random() * words.length)];
          char = word[Math.floor(Math.random() * word.length)];
        } else {
          char = String.fromCharCode(0x30A0 + Math.random() * 96);
        }

        // Color: bright green head, darker trail
        const brightness = Math.max(0.2, 1 - (y / H) * 0.5);
        const g = Math.floor(200 * brightness + 55);
        ctx.fillStyle = `rgba(0, ${g}, 0, ${0.8 * brightness})`;
        
        // Glow effect for head
        if (Math.random() < 0.02) {
          ctx.shadowColor = '#00ff00';
          ctx.shadowBlur = 12;
        } else {
          ctx.shadowBlur = 0;
        }

        ctx.fillText(char, x, y);

        drops[i] += speeds[i];
        if (drops[i] * fontSize > H && Math.random() > 0.97) {
          drops[i] = 0;
          speeds[i] = 0.3 + Math.random() * 0.7;
        }
      }

      // Slowdown + central opening for reveal (last 30% of duration)
      if (progress > 0.7 && !revealedRef.current) {
        const revealProgress = (progress - 0.7) / 0.3;
        const radius = revealProgress * Math.max(W, H) * 0.55;
        const cx = W / 2;
        const cy = H / 2;

        // Slow down column speed
        for (let j = 0; j < cols; j++) {
          speeds[j] *= 0.97;
        }

        // Clear circle from center with soft edge
        ctx.save();
        const gradient = ctx.createRadialGradient(cx, cy, radius * 0.5, cx, cy, radius);
        gradient.addColorStop(0, 'rgba(0, 0, 0, 0.8)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();
        ctx.restore();
      }

      if (progress >= 1 && !revealedRef.current) {
        revealedRef.current = true;
        if (onReveal) onReveal();
        return;
      }

      animRef.current = requestAnimationFrame(draw);
    };

    // Initial black fill
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);
    animRef.current = requestAnimationFrame(draw);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [allWords, duration, onReveal]);

  return (
    <motion.canvas
      ref={canvasRef}
      className="fixed inset-0 z-[400]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      data-testid="matrix-overlay"
    />
  );
}
