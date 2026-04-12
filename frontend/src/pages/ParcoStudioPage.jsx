import React, { useState, useEffect, useContext, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Lock, Loader2, Building, Film, Sparkles, Camera, Radio, GraduationCap, Shield, X, ChevronRight, Plus, Minus, Gamepad2 } from 'lucide-react';

// ═══ LED SIGN — 15+ animated effects for production house name ═══
const SignLED = ({ name, mw }) => {
  const [effectIdx, setEffectIdx] = useState(0);
  const [frame, setFrame] = useState(0);
  const letters = useMemo(() => name.split(''), [name]);
  const EFFECTS_COUNT = 15;
  const EFFECT_DURATION = 5000; // 5 seconds per effect

  // Rotate through effects slowly
  useEffect(() => {
    const iv = setInterval(() => setEffectIdx(i => (i + 1) % EFFECTS_COUNT), EFFECT_DURATION);
    return () => clearInterval(iv);
  }, []);

  // Frame ticker for animations (60ms per frame)
  useEffect(() => {
    const iv = setInterval(() => setFrame(f => f + 1), 60);
    return () => clearInterval(iv);
  }, []);

  // Reset frame on effect change
  useEffect(() => { setFrame(0); }, [effectIdx]);

  const fs = mw * 0.009;
  const maxFrames = Math.ceil(EFFECT_DURATION / 60);

  const renderEffect = () => {
    switch (effectIdx) {
      case 0: { // Typewriter — one letter at a time from left
        const show = Math.min(letters.length, Math.floor(frame / 3) + 1);
        return letters.map((l, i) => (
          <span key={i} style={{ opacity: i < show ? 1 : 0, transition: 'opacity 0.1s' }}>{l}</span>
        ));
      }
      case 1: { // Blink — full name appears/disappears irregularly
        const pattern = [1,1,1,0,1,0,0,1,1,1,1,0,1,1,0,0,0,1,1,1,1,1,0,1];
        const idx = Math.floor(frame / 8) % pattern.length;
        return <span style={{ opacity: pattern[idx] }}>{name}</span>;
      }
      case 2: { // Zoom from dot — starts tiny, grows to full
        const progress = Math.min(1, frame / 50);
        const scale = 0.05 + progress * 0.95;
        return <span style={{ display: 'inline-block', transform: `scale(${scale})`, opacity: 0.3 + progress * 0.7 }}>{name}</span>;
      }
      case 3: { // Reverse typewriter — last letter to first
        const show = Math.min(letters.length, Math.floor(frame / 3) + 1);
        return letters.map((l, i) => (
          <span key={i} style={{ opacity: (letters.length - 1 - i) < show ? 1 : 0, transition: 'opacity 0.1s' }}>{l}</span>
        ));
      }
      case 4: { // Wave — letters bounce up and down
        return letters.map((l, i) => {
          const offset = Math.sin((frame * 0.08) + i * 0.5) * fs * 0.3;
          return <span key={i} style={{ display: 'inline-block', transform: `translateY(${offset}px)` }}>{l}</span>;
        });
      }
      case 5: { // Color sweep — blue glow moves through letters
        return letters.map((l, i) => {
          const pos = (frame * 0.15) % (letters.length + 4) - 2;
          const dist = Math.abs(i - pos);
          const bright = dist < 2 ? 1 : 0.5;
          const color = dist < 1.5 ? '#60c0ff' : dist < 3 ? '#4090dd' : '#2060aa';
          return <span key={i} style={{ color, opacity: bright, transition: 'color 0.15s' }}>{l}</span>;
        });
      }
      case 6: { // Fade in one by one from center outward
        const center = Math.floor(letters.length / 2);
        return letters.map((l, i) => {
          const dist = Math.abs(i - center);
          const show = frame > dist * 4;
          return <span key={i} style={{ opacity: show ? 1 : 0, transition: 'opacity 0.2s' }}>{l}</span>;
        });
      }
      case 7: { // Glitch — random letters flash different chars
        return letters.map((l, i) => {
          const glitching = Math.random() < 0.08 && frame % 4 === 0;
          const char = glitching ? String.fromCharCode(33 + Math.floor(Math.random() * 90)) : l;
          return <span key={i} style={{ color: glitching ? '#ff4040' : undefined }}>{char}</span>;
        });
      }
      case 8: { // Slide in from right
        const progress = Math.min(1, frame / 40);
        const x = (1 - progress) * 100;
        return <span style={{ display: 'inline-block', transform: `translateX(${x}%)`, opacity: progress }}>{name}</span>;
      }
      case 9: { // Flicker neon — simulates neon sign turning on
        const steps = [0,0,0.3,0,0.5,0.3,0,0.8,0.5,1,0.8,1,1,1,1,1,0.9,1,1,1];
        const idx = Math.min(steps.length - 1, Math.floor(frame / 4));
        return <span style={{ opacity: steps[idx], textShadow: steps[idx] > 0.8 ? `0 0 ${fs*0.5}px #4080ff, 0 0 ${fs}px #2060cc` : 'none' }}>{name}</span>;
      }
      case 10: { // Scramble reveal — random chars settle into correct letters
        return letters.map((l, i) => {
          const settled = frame > (i * 3 + 10);
          const char = settled ? l : String.fromCharCode(65 + Math.floor(Math.random() * 26));
          return <span key={i} style={{ color: settled ? undefined : '#4080aa' }}>{char}</span>;
        });
      }
      case 11: { // Bounce drop — letters drop in from top with bounce
        return letters.map((l, i) => {
          const delay = i * 3;
          const t = Math.max(0, frame - delay);
          const y = t < 10 ? -fs * 2 * (1 - t/10) : t < 15 ? fs * 0.3 * Math.sin((t-10) * 0.6) : 0;
          const opacity = t > 0 ? 1 : 0;
          return <span key={i} style={{ display: 'inline-block', transform: `translateY(${y}px)`, opacity }}>{l}</span>;
        });
      }
      case 12: { // Pulse glow — entire name pulses with bright blue glow
        const pulse = 0.5 + 0.5 * Math.sin(frame * 0.06);
        return <span style={{ textShadow: `0 0 ${pulse * fs}px #3090ff, 0 0 ${pulse * fs * 2}px #2060cc40` }}>{name}</span>;
      }
      case 13: { // Matrix rain reveal — letters appear as if falling into place
        return letters.map((l, i) => {
          const delay = i * 2 + Math.floor(Math.sin(i * 2.5) * 5);
          const t = Math.max(0, frame - delay);
          const falling = t < 8;
          const y = falling ? -fs * (1 - t/8) : 0;
          return <span key={i} style={{ display: 'inline-block', transform: `translateY(${y}px)`, opacity: t > 0 ? 1 : 0, color: falling ? '#40ff80' : undefined }}>{l}</span>;
        });
      }
      case 14: { // Split reveal — name splits from center
        const progress = Math.min(1, frame / 40);
        return letters.map((l, i) => {
          const center = letters.length / 2;
          const side = i < center ? -1 : 1;
          const dist = Math.abs(i - center);
          const x = (1 - progress) * side * dist * fs * 0.3;
          return <span key={i} style={{ display: 'inline-block', transform: `translateX(${x}px)`, opacity: 0.2 + progress * 0.8 }}>{l}</span>;
        });
      }
      default:
        return <span>{name}</span>;
    }
  };

  return (
    <div className="absolute pointer-events-none" style={{ left: '35%', top: '38.5%', width: '30%' }}>
      <div className="flex justify-center">
        <div style={{
          padding: `${mw * 0.003}px ${mw * 0.01}px`,
          background: 'rgba(0,5,20,0.75)', backdropFilter: 'blur(3px)',
          borderRadius: mw * 0.0015,
          border: `${Math.max(1, mw * 0.0004)}px solid rgba(60,120,255,0.35)`,
          boxShadow: '0 0 8px rgba(40,80,200,0.3), inset 0 0 6px rgba(40,80,200,0.15)',
          overflow: 'hidden',
        }}>
          <p className="font-['Bebas_Neue'] font-bold text-center whitespace-nowrap" style={{
            fontSize: fs, lineHeight: 1.2, color: '#4090ee',
            letterSpacing: '0.15em',
            textShadow: '0 0 4px rgba(60,140,255,0.6)',
          }}>
            {renderEffect()}
          </p>
        </div>
      </div>
    </div>
  );
};

const GLOW_COLORS = ['#d4af37','#e04040','#4080e0','#40c060','#9050d0','#40c8d8','#e08030'];

const SLOTS = [
  { id: 'studios', label: 'Studi di Produzione', cx: 50, cy: 33, color: '#e8a040', icon: Camera,
    w: 28, h: 22,
    infras: [
      { type: 'production_studio', name: 'Studio Produzione Film', route: '/create-film' },
      { type: 'studio_serie_tv', name: 'Studio Serie TV', route: '/create-series' },
      { type: 'studio_anime', name: 'Studio Anime', route: '/create-anime' },
    ],
  },
  { id: 'arcade', label: 'Sala Giochi', cx: 14, cy: 14, color: '#e840c0', icon: Gamepad2,
    w: 16, h: 18,
    infras: [{ type: '_minigiochi', name: 'Minigiochi', route: '/minigiochi' }],
  },
  { id: 'talent', label: 'Agenzia & Talenti', cx: 16, cy: 37, color: '#a070d0', icon: GraduationCap,
    w: 14, h: 14,
    infras: [
      { type: 'talent_scout_actors', name: 'Scout Attori', route: '/infrastructure' },
      { type: 'talent_scout_screenwriters', name: 'Scout Sceneggiatori', route: '/infrastructure' },
      { type: 'cinema_school', name: 'Scuola di Recitazione', route: '/acting-school' },
    ],
  },
  { id: 'broadcast', label: 'Broadcast TV', cx: 18, cy: 57, color: '#e06060', icon: Radio,
    w: 14, h: 16,
    infras: [
      { type: 'emittente_tv', name: 'Emittente TV', route: '/my-tv' },
    ],
  },
  { id: 'events', label: 'Eventi & Esperienza', cx: 72, cy: 56, color: '#50c878', icon: Sparkles,
    w: 20, h: 18,
    infras: [
      { type: 'film_festival_venue', name: 'Festival del Cinema', route: '/festivals' },
      { type: 'cinema_museum', name: 'Museo del Cinema', route: '/infrastructure' },
      { type: 'theme_park', name: 'Parco Tematico', route: '/infrastructure' },
    ],
  },
  { id: 'strategic', label: 'Strategico', cx: 86, cy: 40, color: '#c0c0c0', icon: Shield,
    w: 14, h: 18,
    infras: [
      { type: 'pvp_operative', name: 'Divisione Operativa', route: '/pvp-arena' },
      { type: 'pvp_investigative', name: 'Divisione Investigativa', route: '/pvp-arena' },
      { type: 'pvp_legal', name: 'Divisione Legale', route: '/pvp-arena' },
    ],
  },
  { id: 'cinema', label: 'Cinema & Sale', cx: 82, cy: 16, color: '#60a0e0', icon: Film,
    w: 20, h: 18,
    infras: [
      { type: 'cinema', name: 'Cinema', route: '/infrastructure' },
      { type: 'drive_in', name: 'Drive-In', route: '/infrastructure' },
      { type: 'multiplex_small', name: 'Multiplex Piccolo', route: '/infrastructure' },
      { type: 'multiplex_medium', name: 'Multiplex Medio', route: '/infrastructure' },
      { type: 'multiplex_large', name: 'Multiplex Grande', route: '/infrastructure' },
      { type: 'vip_cinema', name: 'VIP Cinema', route: '/infrastructure' },
    ],
  },
];

export default function ParcoStudioPage() {
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [backgrounds, setBackgrounds] = useState({});
  const [loading, setLoading] = useState(true);
  const [openSlot, setOpenSlot] = useState(null);
  const [zoom, setZoom] = useState(0.3);
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const touchRef = useRef({ dist: 0, zoom: 0.3 });

  // Glow color per player (deterministic from nickname)
  const glowColor = GLOW_COLORS[(user?.nickname || '').split('').reduce((a, c) => a + c.charCodeAt(0), 0) % GLOW_COLORS.length];

  const loadData = useCallback(async () => {
    try { const res = await api.get('/infrastructure/parco-studio/backgrounds'); setBackgrounds(res.data.backgrounds || {}); }
    catch {} finally { setLoading(false); }
  }, [api]);
  useEffect(() => { loadData(); }, [loadData]);

  // Map dimensions: wider, less tall
  const MAP_W = 4000;
  const MAP_H = 2400;

  // Center on studio
  const centerMap = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const mw = MAP_W * zoom, mh = MAP_H * zoom;
    const cw = el.clientWidth, ch = el.clientHeight;
    if (mw <= cw) { el.scrollLeft = 0; } else { el.scrollLeft = (mw * 0.5) - cw / 2; }
    if (mh <= ch) { el.scrollTop = 0; } else { el.scrollTop = (mh * 0.42) - ch / 2; }
  }, [zoom]);

  useEffect(() => { if (!loading) setTimeout(centerMap, 50); }, [loading, zoom, centerMap]);

  // Pinch zoom
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const getTouchDist = (e) => {
      const [a, b] = [e.touches[0], e.touches[1]];
      return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
    };
    const onStart = (e) => { if (e.touches.length === 2) { touchRef.current = { dist: getTouchDist(e), zoom }; } };
    const onMove = (e) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const d = getTouchDist(e);
        const scale = d / touchRef.current.dist;
        const nz = Math.max(0.2, Math.min(1.0, +(touchRef.current.zoom * scale).toFixed(2)));
        setZoom(nz);
      }
    };
    el.addEventListener('touchstart', onStart, { passive: true });
    el.addEventListener('touchmove', onMove, { passive: false });
    return () => { el.removeEventListener('touchstart', onStart); el.removeEventListener('touchmove', onMove); };
  }, [zoom, loading]);

  const isOwned = (t) => t === '_minigiochi' ? true : (backgrounds[t]?.owned || false);
  const getInfraId = (t) => backgrounds[t]?.infra_id;
  const slotOwned = (s) => s.infras.filter(i => isOwned(i.type)).length;

  const handleInfra = (infra) => {
    if (isOwned(infra.type)) {
      const iid = getInfraId(infra.type);
      if (iid) navigate(`/infrastructure/${iid}`); else navigate(infra.route);
    } else navigate('/infrastructure');
    setOpenSlot(null);
  };

  if (loading) return <div className="fixed inset-0 bg-[#080604] flex items-center justify-center z-40" style={{ top: 44, bottom: 52 }}><Loader2 className="w-8 h-8 text-yellow-500 animate-spin" /></div>;

  const mw = MAP_W * zoom, mh = MAP_H * zoom;
  const vw = containerRef.current?.clientWidth || 390;
  const vh = containerRef.current?.clientHeight || 700;
  const padX = mw < vw ? (vw - mw) / 2 : 0;
  const padY = mh < vh ? (vh - mh) / 2 : 0;

  return (
    <div className="fixed inset-0 bg-[#0a0906] z-30" style={{ top: 44, bottom: 52 }} data-testid="parco-studio-page">
      <div ref={containerRef} className="w-full h-full overflow-auto" style={{ WebkitOverflowScrolling: 'touch' }}>
        <div style={{ paddingLeft: padX, paddingTop: padY, paddingRight: padX, paddingBottom: padY }}>
          <div ref={mapRef} className="relative" style={{ width: mw, height: mh }}>
            <img src="/parco-studio-map.png?v=3" alt="" style={{ width: mw, height: mh, display: 'block' }} draggable={false} />

            {/* LED Screen Sign — animated production house name */}
            {user?.production_house_name && (
              <SignLED name={user.production_house_name} mw={mw} />
            )}

            {/* Building tap areas — full building size, lock for unowned */}
            {SLOTS.map(slot => {
              const owned = slotOwned(slot);
              const empty = owned === 0;
              const bw = mw * slot.w / 100;
              const bh = mh * slot.h / 100;
              const lockSize = Math.min(bw, bh) * 0.35;

              return (
                <div key={slot.id} className="absolute cursor-pointer" data-testid={`slot-${slot.id}`}
                  style={{ left: `${slot.cx}%`, top: `${slot.cy}%`, width: bw, height: bh, transform: 'translate(-50%,-50%)' }}
                  onClick={() => slot.id === 'arcade' ? navigate('/minigiochi') : (empty ? navigate('/infrastructure') : setOpenSlot(slot.id))}>
                  {empty && slot.id !== 'arcade' && (
                    <div className="w-full h-full flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.2)', borderRadius: mw * 0.002 }}>
                      <Lock style={{ width: lockSize, height: lockSize, color: 'rgba(212,175,55,0.55)' }} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Zoom — left side */}
      <div className="absolute bottom-3 left-3 flex flex-col gap-1.5 z-10">
        <button onClick={() => setZoom(z => Math.min(1.0, +(z + 0.1).toFixed(2)))}
          className="w-8 h-8 rounded-full bg-black/70 border border-yellow-500/40 text-yellow-500 flex items-center justify-center active:scale-90 transition-transform" data-testid="zoom-in">
          <Plus className="w-3.5 h-3.5" />
        </button>
        <div className="text-center text-[7px] text-yellow-500/50 font-bold">{Math.round(zoom * 100)}%</div>
        <button onClick={() => setZoom(z => Math.max(0.2, +(z - 0.1).toFixed(2)))}
          className="w-8 h-8 rounded-full bg-black/70 border border-yellow-500/40 text-yellow-500 flex items-center justify-center active:scale-90 transition-transform" data-testid="zoom-out">
          <Minus className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Building popup */}
      {openSlot && (() => {
        const slot = SLOTS.find(s => s.id === openSlot);
        if (!slot) return null;
        const Icon = slot.icon;
        return (
          <div className="fixed inset-0 z-[60] flex items-center justify-center px-4" onClick={() => setOpenSlot(null)}>
            <div className="absolute inset-0 bg-black/60" />
            <div className="relative w-full max-w-sm bg-[#111113] rounded-2xl overflow-hidden border" style={{ borderColor: `${slot.color}30`, maxHeight: 'calc(100vh - 120px)' }} onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 flex-shrink-0">
                <div className="flex items-center gap-2"><Icon className="w-5 h-5" style={{ color: slot.color }} /><span className="font-bold text-sm text-white">{slot.label}</span></div>
                <button onClick={() => setOpenSlot(null)} className="text-gray-400"><X className="w-4 h-4" /></button>
              </div>
              <div className="p-3 space-y-1.5 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
                {slot.infras.map(infra => {
                  const own = isOwned(infra.type);
                  return (
                    <button key={infra.type} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all active:scale-[0.98] ${own ? 'bg-white/5 border-white/10' : 'bg-black/30 border-white/5'}`}
                      onClick={() => handleInfra(infra)} data-testid={`infra-${infra.type}`}>
                      {own ? <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: `${slot.color}20`, border: `1.5px solid ${slot.color}50` }}><Icon className="w-4 h-4" style={{ color: slot.color }} /></div>
                        : <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-yellow-500/10 border border-yellow-500/30"><Lock className="w-4 h-4 text-yellow-500/70" /></div>}
                      <div className="flex-1 text-left">
                        <p className={`text-[11px] font-bold ${own ? 'text-white' : 'text-gray-500'}`}>{infra.name}</p>
                        <p className="text-[8px]" style={{ color: own ? slot.color : '#666' }}>{own ? 'Attiva' : 'Non acquistata'}</p>
                      </div>
                      <ChevronRight className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })()}

      {/* Top UI */}
      <div className="absolute top-1.5 right-1.5 bg-black/60 backdrop-blur-sm rounded px-2 py-0.5 border border-white/10">
        <p className="text-[7px] text-yellow-500/70 font-bold tracking-wider">PARCO STUDIO</p>
      </div>
      <button className="absolute top-1.5 left-1.5 bg-black/60 backdrop-blur-sm rounded px-2 py-1 border border-white/10 text-gray-300 text-[10px] flex items-center gap-1"
        onClick={() => navigate('/infrastructure')} data-testid="parco-back">
        <Building className="w-3 h-3" /> Classica
      </button>

      {/* Glow animations */}
      <style>{`@keyframes glowPulse { 0%,100% { opacity: 0.85; } 50% { opacity: 1; } }`}</style>
    </div>
  );
}
