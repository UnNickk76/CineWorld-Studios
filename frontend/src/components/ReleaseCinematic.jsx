import React, { useState, useEffect, useRef } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Film, Sparkles, Users, X } from 'lucide-react';

const STYLES = `
  @keyframes rc-fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes rc-slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes rc-scaleIn { from { opacity: 0; transform: scale(0.85); } to { opacity: 1; transform: scale(1); } }
  @keyframes rc-eventReveal { from { opacity: 0; transform: scale(0.9) translateY(15px); } to { opacity: 1; transform: scale(1) translateY(0); } }
  @keyframes rc-shakeIn { 0% { opacity: 0; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1.04); } 55% { transform: scale(1) rotate(-1deg); } 70% { transform: scale(1.02) rotate(1deg); } 100% { transform: scale(1) rotate(0); } }
  @keyframes rc-shimmer { 0%, 100% { transform: translateX(-100%); } 50% { transform: translateX(100%); } }
  @keyframes rc-pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.08); } }
  @keyframes rc-successZoom { 0% { opacity: 0; transform: scale(1.15); } 60% { opacity: 1; transform: scale(1.02); } 100% { opacity: 1; transform: scale(1); } }
  @keyframes rc-slowZoom { 0% { transform: scale(1); } 100% { transform: scale(1.06); } }
  @keyframes rc-flopFade { 0% { opacity: 0; transform: scale(0.98); } 100% { opacity: 1; transform: scale(1); } }
  @keyframes rc-glowPulse { 0%, 100% { box-shadow: inset 0 0 40px rgba(234, 179, 8, 0.1); } 50% { box-shadow: inset 0 0 80px rgba(234, 179, 8, 0.2); } }
`;

const fmtRev = (v) => v > 999999 ? (v / 1000000).toFixed(1) + 'M' : v > 999 ? (v / 1000).toFixed(0) + 'K' : v;

// inline: renders without fixed overlay (for embedding in FilmPopup dialog)
// actions: custom JSX for bottom buttons (overrides default "Chiudi")
export function ReleaseCinematic({ data, onClose, directorName, inline, actions }) {
  const [phase, setPhase] = useState(0);
  const [trailerSlide, setTrailerSlide] = useState(0);
  const [animQ, setAnimQ] = useState(0);
  const [animR, setAnimR] = useState(0);
  const phaseRef = useRef(0);

  // Auto-advance phases
  useEffect(() => {
    const timers = [
      setTimeout(() => { setPhase(1); phaseRef.current = 1; }, 300),
      setTimeout(() => { setPhase(2); phaseRef.current = 2; }, 1800),
      setTimeout(() => { setPhase(3); phaseRef.current = 3; }, 3500),
      setTimeout(() => { setPhase(4); phaseRef.current = 4; }, 4500),
      setTimeout(() => { setPhase(5); phaseRef.current = 5; }, 6000),
    ];
    return () => timers.forEach(clearTimeout);
  }, []);

  // Trailer slides
  useEffect(() => {
    if (phase < 2 || !data.screenplay_scenes?.length) return;
    const iv = setInterval(() => setTrailerSlide(p => (p + 1) % data.screenplay_scenes.length), 2500);
    return () => clearInterval(iv);
  }, [phase, data.screenplay_scenes]);

  // Animated numbers
  useEffect(() => {
    if (phase < 4) return;
    const target_q = data.quality_score || 0;
    const target_r = data.opening_day_revenue || 0;
    let frame = 0;
    const total = 25;
    const iv = setInterval(() => {
      frame++;
      const p = Math.min(1, frame / total);
      const ease = 1 - Math.pow(1 - p, 3);
      setAnimQ(Math.round(target_q * ease));
      setAnimR(Math.round(target_r * ease));
      if (frame >= total) clearInterval(iv);
    }, 40);
    return () => clearInterval(iv);
  }, [phase, data.quality_score, data.opening_day_revenue]);

  const r = data;
  const outcome = r.release_outcome || 'normal';

  const content = (
    <div className={inline ? 'space-y-0' : 'max-w-md w-full max-h-[90vh] overflow-y-auto rounded-lg'} onClick={inline ? undefined : e => e.stopPropagation()} data-testid="release-cinematic">
      <style>{STYLES}</style>

      {/* Close button - only in overlay mode */}
      {!inline && (
        <div className="sticky top-0 z-10 flex justify-end p-1">
          <button onClick={onClose} className="bg-black/60 rounded-full p-1 text-white/60 hover:text-white" data-testid="replay-close">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

        {/* PHASE 1: Cinema Image */}
        <div className={`relative w-full overflow-hidden rounded-t-lg ${outcome === 'success' ? 'ring-2 ring-yellow-500/60' : ''}`}>
          <div className="aspect-[16/10] relative overflow-hidden">
            <img src={r.release_image || '/assets/release/cinema_normal.jpg'} alt="Cinema"
              className={`w-full h-full object-cover ${outcome === 'flop' ? 'saturate-[0.4] brightness-75' : outcome === 'success' ? 'brightness-110' : ''}`}
              style={{ animation: outcome === 'success' ? 'rc-successZoom 1.5s ease-out both' : outcome === 'flop' ? 'rc-flopFade 1.2s ease-out both' : 'rc-slowZoom 8s ease-out both' }}
            />
            <div className={`absolute inset-0 ${outcome === 'success' ? 'bg-gradient-to-t from-black via-black/30 to-transparent' : outcome === 'flop' ? 'bg-gradient-to-t from-black via-black/50 to-blue-950/30' : 'bg-gradient-to-t from-black via-black/40 to-transparent'}`} />
            {outcome === 'success' && <div className="absolute inset-0 pointer-events-none" style={{ animation: 'rc-glowPulse 2s ease-in-out infinite' }} />}
            <div className="absolute bottom-0 left-0 right-0 p-3 text-center">
              {phase === 1 && <p className="text-xs text-white/80 italic" style={{ animation: 'rc-fadeIn 0.8s ease-out 0.3s both' }}>Il tuo film sta uscendo nelle sale...</p>}
              {phase >= 2 && (
                <>
                  <h1 className="text-lg font-black text-white tracking-tight" style={{ animation: 'rc-scaleIn 0.5s ease-out both' }}>{r.title}</h1>
                  {directorName && <p className="text-[9px] text-yellow-400/70 mt-0.5 uppercase tracking-[0.2em]" style={{ animation: 'rc-fadeIn 0.4s ease-out 0.3s both' }}>Un film di {directorName}</p>}
                </>
              )}
              {r.hype_level > 0 && phase <= 2 && (
                <div className="mt-1.5 flex items-center justify-center gap-1.5" style={{ animation: 'rc-fadeIn 0.5s ease-out 0.6s both' }}>
                  <div className="h-1 bg-white/10 rounded-full w-20 overflow-hidden">
                    <div className={`h-full rounded-full ${r.hype_level >= 60 ? 'bg-yellow-400' : r.hype_level >= 30 ? 'bg-amber-500' : 'bg-gray-400'}`} style={{ width: `${r.hype_level}%` }} />
                  </div>
                  <span className="text-[8px] text-white/40">Hype {r.hype_level}%</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* PHASE 2: Screenplay */}
        {phase >= 2 && r.screenplay_scenes?.length > 0 && (
          <div className="bg-black/80 px-3 py-2 border-x border-white/5">
            <p className="text-[8px] text-white/30 uppercase tracking-[0.2em] text-center mb-1.5">Anteprima Sceneggiatura</p>
            <div className="relative h-10 overflow-hidden">
              {r.screenplay_scenes.map((scene, i) => (
                <p key={i} className={`absolute inset-0 flex items-center justify-center text-center text-[10px] leading-relaxed italic transition-all duration-500 ${trailerSlide === i ? 'opacity-100 translate-y-0' : trailerSlide > i ? 'opacity-0 -translate-y-4' : 'opacity-0 translate-y-4'} ${outcome === 'success' ? 'text-yellow-200/80' : outcome === 'flop' ? 'text-blue-200/60' : 'text-gray-300/70'}`}>
                  &quot;{scene.length > 60 ? scene.substring(0, 60) + '...' : scene}&quot;
                </p>
              ))}
            </div>
            <div className="flex justify-center gap-1 mt-1">
              {r.screenplay_scenes.map((_, i) => <div key={i} className={`w-1 h-1 rounded-full transition-all duration-300 ${trailerSlide >= i ? 'bg-white/50 scale-110' : 'bg-white/15'}`} />)}
            </div>
          </div>
        )}

        {/* PHASE 3: Event */}
        {phase >= 3 && r.release_event && r.release_event.id !== 'nothing_special' && (() => {
          const evt = r.release_event;
          const isRare = evt.rarity === 'rare';
          const borderColor = evt.type === 'positive' ? 'border-emerald-500' : evt.type === 'negative' ? 'border-red-500' : 'border-amber-500';
          const bgGrad = evt.type === 'positive' ? 'from-emerald-950/80 to-[#0a0a0b]' : evt.type === 'negative' ? 'from-red-950/80 to-[#0a0a0b]' : 'from-amber-950/80 to-[#0a0a0b]';
          const accentColor = evt.type === 'positive' ? 'text-emerald-400' : evt.type === 'negative' ? 'text-red-400' : 'text-amber-400';
          return (
            <div className={`relative border-x-2 border-b ${borderColor} bg-gradient-to-b ${bgGrad} p-2.5 ${isRare ? 'ring-1 ring-purple-500/50' : ''}`} style={{ animation: isRare ? 'rc-shakeIn 0.7s ease-out both' : 'rc-eventReveal 0.8s ease-out both' }}>
              {isRare && <div className="absolute inset-0 overflow-hidden pointer-events-none"><div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/10 to-transparent" style={{ animation: 'rc-shimmer 2s ease-in-out infinite' }} /></div>}
              <div className="flex items-center justify-center gap-2 mb-1.5">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center ${evt.type === 'positive' ? 'bg-emerald-500/20' : evt.type === 'negative' ? 'bg-red-500/20' : 'bg-amber-500/20'}`} style={{ animation: 'rc-pulse 1.5s ease-in-out infinite' }}>
                  <Sparkles className={`w-3.5 h-3.5 ${accentColor}`} />
                </div>
                <div className="text-center">
                  {isRare && <Badge className="bg-purple-500/30 text-purple-300 text-[7px] mb-0.5 border border-purple-500/40">EVENTO RARO</Badge>}
                  <h3 className={`text-[10px] font-black ${accentColor} uppercase tracking-wider`}>{evt.name}</h3>
                </div>
              </div>
              <p className="text-[9px] text-gray-300 text-center leading-relaxed mb-1.5">{evt.description}</p>
              <div className="flex justify-center gap-2 text-[9px] font-bold">
                {evt.quality_modifier !== 0 && <div className={`px-1.5 py-0.5 rounded-full ${evt.quality_modifier > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>Qualita {evt.quality_modifier > 0 ? '+' : ''}{evt.quality_modifier}</div>}
                {evt.revenue_modifier !== 0 && <div className={`px-1.5 py-0.5 rounded-full ${evt.revenue_modifier > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>Incassi {evt.revenue_modifier > 0 ? '+' : ''}{evt.revenue_modifier}%</div>}
              </div>
            </div>
          );
        })()}

        {/* PHASE 4: Numbers */}
        {phase >= 4 && (
          <div className="bg-[#0d0d0e] px-3 py-2.5 border-x border-white/5" style={{ animation: 'rc-slideUp 0.6s ease-out both' }}>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className={`text-xl font-black tabular-nums ${r.quality_score >= 70 ? 'text-green-400' : r.quality_score >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>{animQ}</div>
                <p className="text-[7px] text-gray-500 uppercase tracking-wide">Qualita</p>
              </div>
              <div>
                <div className="text-xl font-black tabular-nums text-yellow-400">{r.imdb_rating?.toFixed?.(1) || '-'}</div>
                <p className="text-[7px] text-gray-500 uppercase tracking-wide">IMDb</p>
              </div>
              <div>
                <div className="text-xl font-black tabular-nums text-green-400">${fmtRev(animR)}</div>
                <p className="text-[7px] text-gray-500 uppercase tracking-wide">Apertura</p>
              </div>
            </div>
            <div className="flex justify-center mt-1.5">
              <Badge className={`text-[9px] px-2.5 py-0.5 ${r.tier === 'masterpiece' ? 'bg-yellow-500 text-black' : r.tier === 'excellent' ? 'bg-green-500/30 text-green-300' : r.tier === 'good' ? 'bg-blue-500/30 text-blue-300' : r.tier === 'mediocre' ? 'bg-gray-500/30 text-gray-300' : 'bg-red-500/30 text-red-300'}`} style={{ animation: 'rc-scaleIn 0.4s ease-out 0.8s both' }}>
                {r.tier_label}
              </Badge>
            </div>
          </div>
        )}

        {/* PHASE 5: Final */}
        {phase >= 5 && (
          <div className={`rounded-b-lg overflow-hidden ${outcome === 'success' ? 'bg-gradient-to-b from-[#0d0d0e] to-yellow-950/20' : outcome === 'flop' ? 'bg-gradient-to-b from-[#0d0d0e] to-blue-950/20' : 'bg-[#0d0d0e]'}`} style={{ animation: 'rc-slideUp 0.5s ease-out both' }}>
            <div className={`text-center py-2 px-3 ${outcome === 'success' ? 'border-t border-yellow-500/30' : outcome === 'flop' ? 'border-t border-blue-500/20' : 'border-t border-white/10'}`}>
              <p className={`text-xs font-bold ${outcome === 'success' ? 'text-yellow-400' : outcome === 'flop' ? 'text-blue-300/70' : 'text-gray-300'}`} style={{ animation: 'rc-scaleIn 0.4s ease-out both' }}>
                {outcome === 'success' ? "Evento dell'anno!" : outcome === 'flop' ? "Il pubblico non ha risposto..." : "Buona accoglienza"}
              </p>
              {r.xp_gained > 0 && <p className="text-green-400 text-[10px] mt-0.5">+{r.xp_gained} XP</p>}
            </div>
            <div className="px-2.5 pb-2 space-y-1">
              {r.modifiers?.soundtrack > 0 && (
                <div className="flex items-center gap-1.5 p-1.5 bg-purple-500/10 border border-purple-500/20 rounded text-[9px]">
                  <Sparkles className="w-3 h-3 text-purple-400" />
                  <span className="text-purple-300 font-medium">Colonna Sonora:</span>
                  <span className="text-purple-200">+{r.modifiers.soundtrack} qualita</span>
                </div>
              )}
              {r.sponsors?.length > 0 && (
                <div className="text-[8px] text-gray-400 p-1.5 bg-black/30 rounded border border-cyan-500/10">
                  <span className="font-medium text-cyan-300 mr-1">Sponsor:</span>
                  {r.sponsors.map(sp => <Badge key={sp.id || sp.name} className="text-[7px] h-3 mr-0.5" style={{ backgroundColor: (sp.logo_color || '#666') + '20', color: sp.logo_color || '#aaa' }}>{sp.name}</Badge>)}
                </div>
              )}
              {r.modifiers && Object.keys(r.modifiers).length > 0 && (
                <div className="text-[8px] text-gray-500 p-1.5 bg-black/30 rounded flex flex-wrap gap-x-2 gap-y-0.5">
                  {r.modifiers.pre_imdb != null && <span>Pre-IMDb: {r.modifiers.pre_imdb}</span>}
                  {r.modifiers.cast_quality != null && <span>Cast: {r.modifiers.cast_quality}</span>}
                  {r.modifiers.soundtrack != null && <span>Soundtrack: +{r.modifiers.soundtrack}</span>}
                  {r.modifiers.buzz != null && <span>Buzz: {r.modifiers.buzz > 0 ? '+' : ''}{r.modifiers.buzz}</span>}
                  {r.modifiers.remaster != null && <span>Remaster: +{r.modifiers.remaster}</span>}
                </div>
              )}
              {r.cost_summary?.total_money != null && (
                <div className="text-[8px] text-gray-500 p-1.5 bg-black/30 rounded">
                  Denaro: <span className="text-yellow-400/80">${r.cost_summary.total_money?.toLocaleString()}</span> | CinePass: <span className="text-cyan-400/80">{r.cost_summary.total_cinepass} CP</span>
                </div>
              )}
              {r.critic_reviews?.length > 0 && (
                <div className="space-y-1 mt-1">
                  <p className="text-[8px] text-gray-400 font-medium uppercase tracking-wider">Recensioni</p>
                  {r.critic_reviews.slice(0, 3).map((review, idx) => (
                    <div key={idx} className="text-[8px] p-1.5 bg-black/30 rounded border-l-2 border-gray-700" style={{ animation: `rc-fadeIn 0.3s ease-out ${0.2 + idx * 0.15}s both` }}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-gray-300 font-medium">{review.source || review.critic_name || 'Critico'}</span>
                        <span className={`font-bold ${(review.score || review.rating || 0) >= 7 ? 'text-green-400' : (review.score || review.rating || 0) >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>{(review.score || review.rating || 0).toFixed?.(1) || review.score}/10</span>
                      </div>
                      <p className="text-gray-500 italic leading-relaxed">&quot;{review.text || review.comment || ''}&quot;</p>
                    </div>
                  ))}
                </div>
              )}
              {r.audience_satisfaction > 0 && (
                <div className="flex items-center gap-2 p-1.5 bg-black/30 rounded">
                  <Users className="w-3 h-3 text-blue-400" />
                  <div className="flex-1">
                    <div className="flex justify-between text-[8px]">
                      <span className="text-gray-400">Soddisfazione Pubblico</span>
                      <span className={`font-bold ${r.audience_satisfaction >= 70 ? 'text-green-400' : r.audience_satisfaction >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>{r.audience_satisfaction}%</span>
                    </div>
                    <div className="h-1 bg-gray-800 rounded-full mt-0.5">
                      <div className={`h-full rounded-full ${r.audience_satisfaction >= 70 ? 'bg-green-500' : r.audience_satisfaction >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${r.audience_satisfaction}%`, transition: 'width 1s ease-out' }} />
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="flex justify-center gap-2 px-2.5 pb-2.5">
              {actions || (
                <Button onClick={onClose} variant="outline" className="border-gray-700 text-[10px] h-8" data-testid="replay-close-btn">
                  Chiudi
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
  );

  if (inline) return content;

  return (
    <div className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-3" onClick={onClose} data-testid="replay-cinematic-overlay">
      {content}
    </div>
  );
}
