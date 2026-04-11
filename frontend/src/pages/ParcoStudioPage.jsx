import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Lock, Loader2, Building, Film, Tv, Sparkles, Camera, Radio, GraduationCap, Shield, X, ChevronRight, Plus, Minus } from 'lucide-react';

const SLOTS = [
  { id: 'studios', label: 'Studi di Produzione', cx: 1500, cy: 1500, color: '#e8a040', icon: Camera,
    infras: [
      { type: 'production_studio', name: 'Studio Produzione Film', route: '/create-film' },
      { type: 'studio_serie_tv', name: 'Studio Serie TV', route: '/create-series' },
      { type: 'studio_anime', name: 'Studio Anime', route: '/create-anime' },
    ],
  },
  { id: 'talent', label: 'Agenzia & Talenti', cx: 900, cy: 900, color: '#a070d0', icon: GraduationCap,
    infras: [
      { type: 'talent_scout_actors', name: 'Scout Attori', route: '/infrastructure' },
      { type: 'talent_scout_screenwriters', name: 'Scout Sceneggiatori', route: '/infrastructure' },
      { type: 'cinema_school', name: 'Scuola di Recitazione', route: '/acting-school' },
    ],
  },
  { id: 'cinema', label: 'Cinema & Sale', cx: 2100, cy: 900, color: '#60a0e0', icon: Film,
    infras: [
      { type: 'cinema', name: 'Cinema', route: '/infrastructure' },
      { type: 'drive_in', name: 'Drive-In', route: '/infrastructure' },
      { type: 'multiplex_small', name: 'Multiplex Piccolo', route: '/infrastructure' },
      { type: 'multiplex_medium', name: 'Multiplex Medio', route: '/infrastructure' },
      { type: 'multiplex_large', name: 'Multiplex Grande', route: '/infrastructure' },
      { type: 'vip_cinema', name: 'VIP Cinema', route: '/infrastructure' },
    ],
  },
  { id: 'events', label: 'Eventi & Esperienza', cx: 2100, cy: 2100, color: '#50c878', icon: Sparkles,
    infras: [
      { type: 'film_festival_venue', name: 'Festival del Cinema', route: '/festivals' },
      { type: 'cinema_museum', name: 'Museo del Cinema', route: '/infrastructure' },
      { type: 'theme_park', name: 'Parco Tematico', route: '/infrastructure' },
    ],
  },
  { id: 'broadcast', label: 'Broadcast TV', cx: 900, cy: 2100, color: '#e06060', icon: Radio,
    infras: [
      { type: 'emittente_tv', name: 'Emittente TV', route: '/my-tv' },
    ],
  },
  { id: 'strategic', label: 'Divisioni Strategiche', cx: 1500, cy: 2500, color: '#c0c0c0', icon: Shield,
    infras: [
      { type: 'pvp_operative', name: 'Divisione Operativa', route: '/pvp-arena' },
      { type: 'pvp_investigative', name: 'Divisione Investigativa', route: '/pvp-arena' },
      { type: 'pvp_legal', name: 'Divisione Legale', route: '/pvp-arena' },
    ],
  },
];

const MAP_NATIVE = 3000;
const ZOOM_MIN = 0.2;
const ZOOM_MAX = 1.0;
const ZOOM_INIT = 0.5;
const ZOOM_STEP = 0.1;

export default function ParcoStudioPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [backgrounds, setBackgrounds] = useState({});
  const [loading, setLoading] = useState(true);
  const [openSlot, setOpenSlot] = useState(null);
  const [zoom, setZoom] = useState(ZOOM_INIT);
  const scrollRef = useRef(null);
  const centeredRef = useRef(false);

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('/infrastructure/parco-studio/backgrounds');
      setBackgrounds(res.data.backgrounds || {});
    } catch {}
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  // Center on studio after load and whenever zoom changes
  useEffect(() => {
    if (!loading && scrollRef.current) {
      const el = scrollRef.current;
      const mapPx = MAP_NATIVE * zoom;
      const cx = 1500 * zoom;
      const cy = 1500 * zoom;
      el.scrollLeft = cx - (el.clientWidth / 2);
      el.scrollTop = cy - (el.clientHeight / 2);
      centeredRef.current = true;
    }
  }, [loading, zoom]);

  const zoomIn = () => setZoom(z => Math.min(ZOOM_MAX, +(z + ZOOM_STEP).toFixed(2)));
  const zoomOut = () => setZoom(z => Math.max(ZOOM_MIN, +(z - ZOOM_STEP).toFixed(2)));

  const isOwned = (type) => backgrounds[type]?.owned || false;
  const getInfraId = (type) => backgrounds[type]?.infra_id;
  const slotOwnedCount = (slot) => slot.infras.filter(i => isOwned(i.type)).length;

  const handleInfraClick = (infra) => {
    if (isOwned(infra.type)) {
      const iid = getInfraId(infra.type);
      if (iid) navigate(`/infrastructure/${iid}`);
      else navigate(infra.route);
    } else {
      navigate('/infrastructure');
    }
    setOpenSlot(null);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-[#080604] flex items-center justify-center z-40" style={{ top: 44, bottom: 52 }}>
        <Loader2 className="w-8 h-8 text-yellow-500 animate-spin" />
      </div>
    );
  }

  const mapPx = MAP_NATIVE * zoom;
  const hitSize = 200 * zoom;

  return (
    <div className="fixed inset-0 bg-[#040302] z-30" style={{ top: 44, bottom: 52 }} data-testid="parco-studio-page">
      <div ref={scrollRef} className="w-full h-full overflow-auto" style={{ WebkitOverflowScrolling: 'touch' }}>
        <div className="relative" style={{ width: mapPx, height: mapPx }}>
          <img src="/parco-studio-map.png" alt="" style={{ width: mapPx, height: mapPx, display: 'block' }} draggable={false} />

          {SLOTS.map(slot => {
            const owned = slotOwnedCount(slot);
            const Icon = slot.icon;
            const isEmpty = owned === 0;
            const sx = slot.cx * zoom - hitSize / 2;
            const sy = slot.cy * zoom - hitSize / 2;
            const fontSize = Math.max(8, 11 * zoom / ZOOM_INIT);

            return (
              <div key={slot.id} className="absolute cursor-pointer" data-testid={`slot-${slot.id}`}
                style={{ left: sx, top: sy, width: hitSize, height: hitSize }}
                onClick={() => setOpenSlot(slot.id)}>
                <div className="w-full h-full flex flex-col items-center justify-center">
                  {isEmpty ? (
                    <div className="animate-pulse flex flex-col items-center" style={{ animationDuration: '2s' }}>
                      <div className="rounded-full flex items-center justify-center"
                        style={{ width: hitSize * 0.4, height: hitSize * 0.4, background: 'rgba(0,0,0,0.6)', border: '2px solid rgba(212,175,55,0.6)', boxShadow: '0 0 15px rgba(212,175,55,0.35)' }}>
                        <Lock style={{ width: hitSize * 0.2, height: hitSize * 0.2 }} className="text-yellow-500" />
                      </div>
                      <div className="bg-black/70 backdrop-blur-sm rounded mt-1 px-2 py-0.5">
                        <p className="font-bold text-yellow-500/80 text-center whitespace-nowrap" style={{ fontSize }}>{slot.label}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center">
                      <div className="rounded-full flex items-center justify-center"
                        style={{ width: hitSize * 0.4, height: hitSize * 0.4, background: 'rgba(0,0,0,0.5)', border: `2px solid ${slot.color}80`, boxShadow: `0 0 14px ${slot.color}30` }}>
                        <Icon style={{ width: hitSize * 0.2, height: hitSize * 0.2, color: slot.color }} />
                      </div>
                      <div className="bg-black/70 backdrop-blur-sm rounded mt-1 px-2 py-1" style={{ borderLeft: `2px solid ${slot.color}60` }}>
                        <p className="font-bold text-white text-center whitespace-nowrap" style={{ fontSize }}>{slot.label}</p>
                        <p className="text-center" style={{ color: slot.color, fontSize: fontSize * 0.8 }}>{owned}/{slot.infras.length} attivi</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Zoom controls */}
      <div className="absolute bottom-3 right-3 flex flex-col gap-1.5 z-10">
        <button onClick={zoomIn} disabled={zoom >= ZOOM_MAX}
          className="w-9 h-9 rounded-full bg-black/70 border border-yellow-500/40 text-yellow-500 flex items-center justify-center disabled:opacity-30 active:scale-90 transition-transform"
          data-testid="zoom-in">
          <Plus className="w-4 h-4" />
        </button>
        <div className="text-center text-[8px] text-yellow-500/60 font-bold">{Math.round(zoom * 100)}%</div>
        <button onClick={zoomOut} disabled={zoom <= ZOOM_MIN}
          className="w-9 h-9 rounded-full bg-black/70 border border-yellow-500/40 text-yellow-500 flex items-center justify-center disabled:opacity-30 active:scale-90 transition-transform"
          data-testid="zoom-out">
          <Minus className="w-4 h-4" />
        </button>
      </div>

      {/* Building popup */}
      {openSlot && (() => {
        const slot = SLOTS.find(s => s.id === openSlot);
        if (!slot) return null;
        const Icon = slot.icon;
        return (
          <div className="fixed inset-0 z-[60] flex items-end justify-center" onClick={() => setOpenSlot(null)}>
            <div className="absolute inset-0 bg-black/50" />
            <div className="relative w-full max-w-sm bg-[#111113] border-t rounded-t-2xl overflow-hidden"
              style={{ borderColor: `${slot.color}30` }} onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <Icon className="w-5 h-5" style={{ color: slot.color }} />
                  <span className="font-bold text-sm text-white">{slot.label}</span>
                </div>
                <button onClick={() => setOpenSlot(null)} className="text-gray-400"><X className="w-4 h-4" /></button>
              </div>
              <div className="p-3 space-y-1.5" style={{ paddingBottom: 'calc(12px + env(safe-area-inset-bottom, 0px))' }}>
                {slot.infras.map(infra => {
                  const own = isOwned(infra.type);
                  return (
                    <button key={infra.type}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all active:scale-[0.98] ${own ? 'bg-white/5 border-white/10 hover:bg-white/10' : 'bg-black/30 border-white/5'}`}
                      onClick={() => handleInfraClick(infra)} data-testid={`infra-${infra.type}`}>
                      {own ? (
                        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: `${slot.color}20`, border: `1.5px solid ${slot.color}50` }}>
                          <Icon className="w-4 h-4" style={{ color: slot.color }} />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-yellow-500/10 border border-yellow-500/30">
                          <Lock className="w-4 h-4 text-yellow-500/70" />
                        </div>
                      )}
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

      {/* UI overlays */}
      <div className="absolute top-1.5 right-1.5 bg-black/60 backdrop-blur-sm rounded px-2 py-0.5 border border-white/10">
        <p className="text-[7px] text-yellow-500/70 font-bold tracking-wider">PARCO STUDIO</p>
      </div>
      <button className="absolute top-1.5 left-1.5 bg-black/60 backdrop-blur-sm rounded px-2 py-1 border border-white/10 text-gray-300 text-[10px] flex items-center gap-1"
        onClick={() => navigate('/infrastructure')} data-testid="parco-back">
        <Building className="w-3 h-3" /> Classica
      </button>
    </div>
  );
}
