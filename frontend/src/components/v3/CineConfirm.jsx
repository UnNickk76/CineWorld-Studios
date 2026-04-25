// CineWorld — CineConfirm (Cineox + Velion) — cross-pipeline reusable
// Single-source confirm modal with the two mascots, cinematic framing, pulse glow.

import React from 'react';

export default function CineConfirm({ open, title, subtitle, confirmLabel = 'Conferma', confirmTone = 'amber', onConfirm, onCancel }) {
  if (!open) return null;
  const tonePalette = {
    amber:  { border: 'border-amber-500/25', glowRGB: '255,180,50',  btnBg: 'bg-amber-500/15 border-amber-500/35 text-amber-400 hover:bg-amber-500/25',   titleColor: 'text-amber-300' },
    rose:   { border: 'border-rose-500/30',  glowRGB: '255,80,110',  btnBg: 'bg-rose-500/15 border-rose-500/40 text-rose-300 hover:bg-rose-500/25',      titleColor: 'text-rose-200' },
    violet: { border: 'border-violet-500/30',glowRGB: '160,100,255', btnBg: 'bg-violet-500/15 border-violet-500/40 text-violet-300 hover:bg-violet-500/25', titleColor: 'text-violet-200' },
  };
  const t = tonePalette[confirmTone] || tonePalette.amber;
  return (
    <>
      <style>{`
        @keyframes cineBackdropIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes cineModalIn { from { opacity: 0; transform: scale(0.88) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
        @keyframes cineGlowPulse-${confirmTone} {
          0%, 100% { box-shadow: 0 0 20px rgba(${t.glowRGB},0.1), inset 0 0 30px rgba(${t.glowRGB},0.02); }
          50% { box-shadow: 0 0 45px rgba(${t.glowRGB},0.25), inset 0 0 40px rgba(${t.glowRGB},0.04); }
        }
        @keyframes cineFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
        @keyframes cineFloatAlt { 0%, 100% { transform: translateY(-2px); } 50% { transform: translateY(4px); } }
      `}</style>
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-sm z-[70] flex items-center justify-center p-4"
        style={{ animation: 'cineBackdropIn 0.25s ease-out' }}
        onClick={onCancel}
        data-testid="cine-confirm-modal"
      >
        <div
          className={`relative bg-[#0d0d0f] border ${t.border} rounded-2xl p-5 max-w-sm w-full space-y-4 overflow-hidden`}
          style={{ animation: `cineModalIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), cineGlowPulse-${confirmTone} 3s ease-in-out infinite` }}
          onClick={e => e.stopPropagation()}
        >
          {/* Characters */}
          <div className="relative z-10 flex items-end justify-center gap-2">
            <div style={{ animation: 'cineFloatAlt 3.5s ease-in-out infinite' }}>
              <img src="/assets/characters/cineox.png" alt="Cineox" className="w-16 h-16 object-contain drop-shadow-lg"
                onError={(e) => { e.target.style.display = 'none'; }} />
            </div>
            <div className="flex-1 text-center px-1">
              <p className={`font-bold leading-tight ${t.titleColor}`} style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: '15px', letterSpacing: '0.5px' }}>{title}</p>
              {subtitle && <p className="text-[8px] text-gray-400 mt-1 leading-relaxed">{subtitle}</p>}
            </div>
            <div style={{ animation: 'cineFloat 3s ease-in-out infinite', filter: 'drop-shadow(0 0 8px rgba(0,180,255,0.3))' }}>
              <img src="/assets/characters/velion.png" alt="Velion" className="w-16 h-16 object-contain"
                onError={(e) => { e.target.style.display = 'none'; }} />
            </div>
          </div>

          {/* Buttons */}
          <div className="relative z-10 flex gap-2.5">
            <button
              onClick={onCancel}
              className="flex-1 py-2.5 rounded-xl bg-gray-800/80 border border-gray-700/50 text-gray-400 text-[10px] font-bold hover:bg-gray-700 active:scale-[0.96] transition-all"
              data-testid="cine-cancel-btn"
            >
              Annulla
            </button>
            <button
              onClick={onConfirm}
              className={`flex-1 py-2.5 rounded-xl border text-[10px] font-bold active:scale-[0.96] transition-all ${t.btnBg}`}
              data-testid="cine-confirm-btn"
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
