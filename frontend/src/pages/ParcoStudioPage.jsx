import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Lock, Loader2, Building, Film, Sparkles, Camera, Radio, GraduationCap, Shield, X, ChevronRight, Plus, Minus, Gamepad2 } from 'lucide-react';

const GLOW_COLORS = ['#d4af37','#e04040','#4080e0','#40c060','#9050d0','#40c8d8','#e08030'];

const SLOTS = [
  { id: 'studios', label: 'Studi di Produzione', cx: 50.2, cy: 53, color: '#e8a040', icon: Camera,
    infras: [
      { type: 'production_studio', name: 'Studio Produzione Film', route: '/create-film' },
      { type: 'studio_serie_tv', name: 'Studio Serie TV', route: '/create-series' },
      { type: 'studio_anime', name: 'Studio Anime', route: '/create-anime' },
    ],
  },
  { id: 'arcade', label: 'Sala Giochi', cx: 22.1, cy: 17.8, color: '#e840c0', icon: Gamepad2,
    infras: [{ type: '_minigiochi', name: 'Minigiochi', route: '/minigiochi' }],
  },
  { id: 'talent', label: 'Agenzia & Talenti', cx: 17.5, cy: 45.7, color: '#a070d0', icon: GraduationCap,
    infras: [
      { type: 'talent_scout_actors', name: 'Scout Attori', route: '/infrastructure' },
      { type: 'talent_scout_screenwriters', name: 'Scout Sceneggiatori', route: '/infrastructure' },
      { type: 'cinema_school', name: 'Scuola di Recitazione', route: '/acting-school' },
    ],
  },
  { id: 'broadcast', label: 'Broadcast TV', cx: 17.5, cy: 77, color: '#e06060', icon: Radio,
    infras: [
      { type: 'emittente_tv', name: 'Emittente TV', route: '/my-tv' },
    ],
  },
  { id: 'events', label: 'Eventi & Esperienza', cx: 71.7, cy: 75.5, color: '#50c878', icon: Sparkles,
    infras: [
      { type: 'film_festival_venue', name: 'Festival del Cinema', route: '/festivals' },
      { type: 'cinema_museum', name: 'Museo del Cinema', route: '/infrastructure' },
      { type: 'theme_park', name: 'Parco Tematico', route: '/infrastructure' },
    ],
  },
  { id: 'strategic', label: 'Strategico', cx: 83.8, cy: 55, color: '#c0c0c0', icon: Shield,
    infras: [
      { type: 'pvp_operative', name: 'Divisione Operativa', route: '/pvp-arena' },
      { type: 'pvp_investigative', name: 'Divisione Investigativa', route: '/pvp-arena' },
      { type: 'pvp_legal', name: 'Divisione Legale', route: '/pvp-arena' },
    ],
  },
  { id: 'cinema', label: 'Cinema & Sale', cx: 83.8, cy: 23, color: '#60a0e0', icon: Film,
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
            <img src="/parco-studio-map.png?v=2" alt="" style={{ width: mw, height: mh, display: 'block' }} draggable={false} />

            {/* Insegna — solo nome casa di produzione del player */}
            {user?.production_house_name && (
              <div className="absolute pointer-events-none" style={{ left: '38%', top: '44%', width: '24%' }}>
                <div className="flex justify-center">
                  <div style={{
                    padding: `${mw * 0.002}px ${mw * 0.006}px`,
                    background: 'rgba(10,5,0,0.6)', backdropFilter: 'blur(3px)',
                    borderRadius: mw * 0.001,
                    border: `${Math.max(1, mw * 0.0004)}px solid ${glowColor}50`,
                    boxShadow: `0 0 ${mw * 0.004}px ${glowColor}35, 0 0 ${mw * 0.008}px ${glowColor}15`,
                    animation: 'glowPulse 2.5s ease-in-out infinite',
                  }}>
                    <p className="font-['Bebas_Neue'] text-center text-white tracking-[0.12em] whitespace-nowrap" style={{ fontSize: mw * 0.005, lineHeight: 1.1 }}>
                      {user.production_house_name}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Invisible tap areas on buildings — 150% larger, fully transparent */}
            {SLOTS.map(slot => {
              const tapSize = mw * 0.032;
              return (
                <div key={slot.id} className="absolute cursor-pointer" data-testid={`slot-${slot.id}`}
                  style={{ left: `${slot.cx}%`, top: `${slot.cy}%`, width: tapSize, height: tapSize, transform: 'translate(-50%,-50%)' }}
                  onClick={() => slot.id === 'arcade' ? navigate('/minigiochi') : setOpenSlot(slot.id)}
                />
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

      {/* Glow animation */}
      <style>{`@keyframes glowPulse { 0%,100% { opacity: 0.85; } 50% { opacity: 1; } }`}</style>
    </div>
  );
}
