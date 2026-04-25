/**
 * Procedural ambient sound FX for trailer genres — generated via WebAudio API.
 * Zero file assets. Starts muted by default (iOS-friendly), must be toggled on by user.
 *
 * Usage:
 *   const fx = createTrailerAudio(genre);
 *   fx.start();    // enable sound
 *   fx.stop();     // disable
 */
export function createTrailerAudio(genre = '') {
  const g = (genre || '').toLowerCase();
  const ctxRef = { ctx: null, nodes: [], running: false };

  const start = () => {
    if (ctxRef.running) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      const ctx = new AC();
      ctxRef.ctx = ctx;
      ctxRef.running = true;

      const master = ctx.createGain();
      master.gain.value = 0;
      master.gain.linearRampToValueAtTime(0.12, ctx.currentTime + 0.8);
      master.connect(ctx.destination);
      ctxRef.nodes.push(master);

      if (g.includes('horror') || g.includes('thriller')) {
        // Low drone + subtle pulse
        const o1 = ctx.createOscillator(); o1.type = 'sawtooth'; o1.frequency.value = 55;
        const o2 = ctx.createOscillator(); o2.type = 'sine'; o2.frequency.value = 82.4;
        const o3 = ctx.createOscillator(); o3.type = 'sine'; o3.frequency.value = 41.2;
        const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 220; lp.Q.value = 3;
        const tremolo = ctx.createGain(); tremolo.gain.value = 0.8;
        const lfo = ctx.createOscillator(); lfo.frequency.value = 0.3; lfo.type = 'sine';
        const lfoGain = ctx.createGain(); lfoGain.gain.value = 0.3;
        lfo.connect(lfoGain); lfoGain.connect(tremolo.gain);
        o1.connect(lp); o2.connect(lp); o3.connect(lp);
        lp.connect(tremolo); tremolo.connect(master);
        [o1, o2, o3, lfo].forEach(n => n.start());
        ctxRef.nodes.push(o1, o2, o3, lfo, lp, tremolo, lfoGain);
      } else if (g.includes('commedia') || g.includes('comedy')) {
        // Warm pad with subtle arpeggio
        const o1 = ctx.createOscillator(); o1.type = 'triangle'; o1.frequency.value = 261.6;
        const o2 = ctx.createOscillator(); o2.type = 'sine'; o2.frequency.value = 329.6;
        const o3 = ctx.createOscillator(); o3.type = 'triangle'; o3.frequency.value = 523.2;
        const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 1800;
        const g1 = ctx.createGain(); g1.gain.value = 0.35;
        const g2 = ctx.createGain(); g2.gain.value = 0.25;
        const g3 = ctx.createGain(); g3.gain.value = 0.15;
        o1.connect(g1); o2.connect(g2); o3.connect(g3);
        g1.connect(lp); g2.connect(lp); g3.connect(lp);
        lp.connect(master);
        [o1, o2, o3].forEach(n => n.start());
        ctxRef.nodes.push(o1, o2, o3, lp, g1, g2, g3);
      } else if (g.includes('sci-fi') || g.includes('fantascienza') || g.includes('fantasy')) {
        // Cosmic pad
        const o1 = ctx.createOscillator(); o1.type = 'sawtooth'; o1.frequency.value = 110;
        const o2 = ctx.createOscillator(); o2.type = 'sine'; o2.frequency.value = 165;
        const o3 = ctx.createOscillator(); o3.type = 'sine'; o3.frequency.value = 246.9;
        const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 800; lp.Q.value = 6;
        const lfo = ctx.createOscillator(); lfo.frequency.value = 0.15; lfo.type = 'sine';
        const lfoG = ctx.createGain(); lfoG.gain.value = 300;
        lfo.connect(lfoG); lfoG.connect(lp.frequency);
        o1.connect(lp); o2.connect(lp); o3.connect(lp);
        lp.connect(master);
        [o1, o2, o3, lfo].forEach(n => n.start());
        ctxRef.nodes.push(o1, o2, o3, lfo, lp, lfoG);
      } else if (g.includes('azione') || g.includes('action')) {
        // Tense pulse
        const o1 = ctx.createOscillator(); o1.type = 'square'; o1.frequency.value = 73.4;
        const o2 = ctx.createOscillator(); o2.type = 'sawtooth'; o2.frequency.value = 55;
        const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 300;
        const pulse = ctx.createGain(); pulse.gain.value = 0.4;
        const lfo = ctx.createOscillator(); lfo.frequency.value = 2; lfo.type = 'square';
        const lfoG = ctx.createGain(); lfoG.gain.value = 0.3;
        lfo.connect(lfoG); lfoG.connect(pulse.gain);
        o1.connect(lp); o2.connect(lp);
        lp.connect(pulse); pulse.connect(master);
        [o1, o2, lfo].forEach(n => n.start());
        ctxRef.nodes.push(o1, o2, lfo, lp, pulse, lfoG);
      } else {
        // Default: warm cinematic pad
        const o1 = ctx.createOscillator(); o1.type = 'triangle'; o1.frequency.value = 130.8;
        const o2 = ctx.createOscillator(); o2.type = 'sine'; o2.frequency.value = 196;
        const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 900;
        o1.connect(lp); o2.connect(lp); lp.connect(master);
        [o1, o2].forEach(n => n.start());
        ctxRef.nodes.push(o1, o2, lp);
      }
    } catch (_) { /* ignore audio errors */ }
  };

  const stop = () => {
    if (!ctxRef.running) return;
    try {
      const { ctx, nodes } = ctxRef;
      const master = nodes[0];
      if (master?.gain) {
        master.gain.cancelScheduledValues(ctx.currentTime);
        master.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.3);
      }
      setTimeout(() => {
        try { nodes.forEach(n => { try { n.stop?.(); } catch (_) {} try { n.disconnect?.(); } catch (_) {} }); } catch (_) {}
        try { ctx.close?.(); } catch (_) {}
      }, 400);
    } catch (_) {}
    ctxRef.ctx = null; ctxRef.nodes = []; ctxRef.running = false;
  };

  return { start, stop, isRunning: () => ctxRef.running };
}
