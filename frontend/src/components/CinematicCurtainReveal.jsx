import React, { useEffect, useState } from 'react';

/**
 * Cinematic curtain animation shown after purchasing a ready-made screenplay.
 * Two red velvet curtains slide apart revealing the film title.
 * Fires on window event 'cineworld:curtain-reveal' with detail { title, subtitle? }.
 * Auto-dismisses after ~2.4s.
 */
export const CinematicCurtainReveal = () => {
  const [state, setState] = useState(null);   // {title, subtitle, phase: 'closed'|'opening'|'revealed'|'closing'}

  useEffect(() => {
    const onReveal = (e) => {
      const { title = '', subtitle = '' } = e.detail || {};
      setState({ title, subtitle, phase: 'closed' });
      // Kick off the animation timeline
      requestAnimationFrame(() => setState(s => s ? { ...s, phase: 'opening' } : s));
      setTimeout(() => setState(s => s ? { ...s, phase: 'revealed' } : s), 900);
      setTimeout(() => setState(s => s ? { ...s, phase: 'closing' } : s), 2200);
      setTimeout(() => setState(null), 3000);
    };
    window.addEventListener('cineworld:curtain-reveal', onReveal);
    return () => window.removeEventListener('cineworld:curtain-reveal', onReveal);
  }, []);

  if (!state) return null;
  const { title, subtitle, phase } = state;
  const open = phase === 'opening' || phase === 'revealed';

  return (
    <div
      className="fixed inset-0 z-[100] pointer-events-none overflow-hidden"
      data-testid="cinematic-curtain-reveal"
    >
      {/* Backdrop — dim */}
      <div
        className="absolute inset-0 transition-opacity duration-700"
        style={{ background: 'radial-gradient(ellipse at center, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.95) 100%)',
                 opacity: phase === 'closing' ? 0 : 1 }}
      />
      {/* Left curtain */}
      <div
        className="absolute top-0 bottom-0 left-0 transition-transform duration-[900ms] ease-[cubic-bezier(0.7,0,0.3,1)]"
        style={{
          width: '52%',
          backgroundImage: 'repeating-linear-gradient(90deg, #7f0a0a 0px, #5a0606 14px, #8b0d0d 28px)',
          boxShadow: 'inset -20px 0 40px rgba(0,0,0,0.6)',
          transform: open ? 'translateX(-100%)' : 'translateX(0)',
        }}
      />
      {/* Right curtain */}
      <div
        className="absolute top-0 bottom-0 right-0 transition-transform duration-[900ms] ease-[cubic-bezier(0.7,0,0.3,1)]"
        style={{
          width: '52%',
          backgroundImage: 'repeating-linear-gradient(90deg, #8b0d0d 0px, #5a0606 14px, #7f0a0a 28px)',
          boxShadow: 'inset 20px 0 40px rgba(0,0,0,0.6)',
          transform: open ? 'translateX(100%)' : 'translateX(0)',
        }}
      />
      {/* Title centered */}
      <div
        className="absolute inset-0 flex flex-col items-center justify-center text-center px-6 transition-all duration-700"
        style={{
          opacity: phase === 'revealed' ? 1 : 0,
          transform: phase === 'revealed' ? 'scale(1)' : 'scale(0.9)',
        }}
      >
        <p className="text-xs text-amber-400/80 uppercase tracking-[0.3em] font-bold mb-2">
          Sceneggiatura pronta
        </p>
        <h1
          className="font-['Bebas_Neue'] text-4xl sm:text-6xl text-white drop-shadow-[0_0_20px_rgba(255,200,80,0.4)] tracking-wide"
          data-testid="curtain-film-title"
        >
          {title}
        </h1>
        {subtitle && (
          <p className="mt-3 text-sm text-gray-300 italic">{subtitle}</p>
        )}
      </div>
    </div>
  );
};

export default CinematicCurtainReveal;
