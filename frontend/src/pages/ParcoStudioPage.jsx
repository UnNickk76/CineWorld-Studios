import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Lock, Loader2, Building, Film, Tv, Sparkles, Camera, Radio, GraduationCap, Shield, X, ChevronRight } from 'lucide-react';

const SLOTS = [
  {
    id: 'studios', label: 'Studi di Produzione', cx: 1500, cy: 1500, color: '#e8a040', icon: Camera,
    infras: [
      { type: 'production_studio', name: 'Studio Produzione Film', route: '/create-film' },
      { type: 'studio_serie_tv', name: 'Studio Serie TV', route: '/create-series' },
      { type: 'studio_anime', name: 'Studio Anime', route: '/create-anime' },
    ],
  },
  {
    id: 'talent', label: 'Agenzia & Talenti', cx: 900, cy: 900, color: '#a070d0', icon: GraduationCap,
    infras: [
      { type: 'talent_scout_actors', name: 'Scout Attori', route: '/infrastructure' },
      { type: 'talent_scout_screenwriters', name: 'Scout Sceneggiatori', route: '/infrastructure' },
      { type: 'cinema_school', name: 'Scuola di Recitazione', route: '/acting-school' },
    ],
  },
  {
    id: 'cinema', label: 'Cinema & Sale', cx: 2100, cy: 900, color: '#60a0e0', icon: Film,
    infras: [
      { type: 'cinema', name: 'Cinema', route: '/infrastructure' },
      { type: 'drive_in', name: 'Drive-In', route: '/infrastructure' },
      { type: 'multiplex_small', name: 'Multiplex Piccolo', route: '/infrastructure' },
      { type: 'multiplex_medium', name: 'Multiplex Medio', route: '/infrastructure' },
      { type: 'multiplex_large', name: 'Multiplex Grande', route: '/infrastructure' },
      { type: 'vip_cinema', name: 'VIP Cinema', route: '/infrastructure' },
    ],
  },
  {
    id: 'events', label: 'Eventi & Esperienza', cx: 2100, cy: 2100, color: '#50c878', icon: Sparkles,
    infras: [
      { type: 'film_festival_venue', name: 'Festival del Cinema', route: '/festivals' },
      { type: 'cinema_museum', name: 'Museo del Cinema', route: '/infrastructure' },
      { type: 'theme_park', name: 'Parco Tematico', route: '/infrastructure' },
    ],
  },
  {
    id: 'broadcast', label: 'Broadcast TV', cx: 900, cy: 2100, color: '#e06060', icon: Radio,
    infras: [
      { type: 'emittente_tv', name: 'Emittente TV', route: '/my-tv' },
    ],
  },
  {
    id: 'strategic', label: 'Divisioni Strategiche', cx: 1500, cy: 2500, color: '#c0c0c0', icon: Shield,
    infras: [
      { type: 'pvp_operative', name: 'Divisione Operativa', route: '/pvp-arena' },
      { type: 'pvp_investigative', name: 'Divisione Investigativa', route: '/pvp-arena' },
      { type: 'pvp_legal', name: 'Divisione Legale', route: '/pvp-arena' },
    ],
  },
];

export default function ParcoStudioPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [backgrounds, setBackgrounds] = useState({});
  const [loading, setLoading] = useState(true);
  const [openSlot, setOpenSlot] = useState(null);
  const scrollRef = useRef(null);

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('/infrastructure/parco-studio/backgrounds');
      setBackgrounds(res.data.backgrounds || {});
    } catch {}
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  // Auto-center on studio (1500,1500)
  useEffect(() => {
    if (!loading && scrollRef.current) {
      const el = scrollRef.current;
      el.scrollLeft = 1500 - (el.clientWidth / 2);
      el.scrollTop = 1500 - (el.clientHeight / 2);
    }
  }, [loading]);

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

  return (
    <div className="fixed inset-0 bg-[#040302] z-30" style={{ top: 44, bottom: 52 }} data-testid="parco-studio-page">
      <div ref={scrollRef} className="w-full h-full overflow-auto" style={{ WebkitOverflowScrolling: 'touch' }}>
        <div className="relative" style={{ width: 3000, height: 3000 }}>
          <img src="/parco-studio-map.png" alt="" className="absolute inset-0 w-full h-full object-cover" draggable={false} />

          {/* 6 Slot hitboxes */}
          {SLOTS.map(slot => {
            const owned = slotOwnedCount(slot);
            const total = slot.infras.length;
            const Icon = slot.icon;
            const isEmpty = owned === 0;

            return (
              <div key={slot.id} className="absolute cursor-pointer" data-testid={`slot-${slot.id}`}
                style={{ left: slot.cx - 100, top: slot.cy - 100, width: 200, height: 200 }}
                onClick={() => setOpenSlot(slot.id)}>
                <div className="w-full h-full flex flex-col items-center justify-center">
                  {isEmpty ? (
                    <div className="animate-pulse flex flex-col items-center" style={{ animationDuration: '2s' }}>
                      <div className="w-16 h-16 rounded-full flex items-center justify-center"
                        style={{ background: 'rgba(0,0,0,0.6)', border: '2.5px solid rgba(212,175,55,0.6)', boxShadow: '0 0 20px rgba(212,175,55,0.35)' }}>
                        <Lock className="w-8 h-8 text-yellow-500" />
                      </div>
                      <div className="bg-black/70 backdrop-blur-sm rounded mt-1.5 px-3 py-1">
                        <p className="text-[11px] font-bold text-yellow-500/80 text-center whitespace-nowrap">{slot.label}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center">
                      <div className="w-16 h-16 rounded-full flex items-center justify-center"
                        style={{ background: 'rgba(0,0,0,0.5)', border: `2.5px solid ${slot.color}80`, boxShadow: `0 0 16px ${slot.color}30` }}>
                        <Icon className="w-8 h-8" style={{ color: slot.color }} />
                      </div>
                      <div className="bg-black/70 backdrop-blur-sm rounded mt-1.5 px-3 py-1.5" style={{ borderLeft: `2px solid ${slot.color}60` }}>
                        <p className="text-[11px] font-bold text-white text-center whitespace-nowrap">{slot.label}</p>
                        <p className="text-[9px] text-center" style={{ color: slot.color }}>{owned}/{total} attivi</p>
                        <div className="mt-1 h-1 rounded-full bg-white/10 overflow-hidden w-16 mx-auto">
                          <div className="h-full rounded-full" style={{ width: `${(owned / total) * 100}%`, background: slot.color }} />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
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
              style={{ borderColor: `${slot.color}30` }}
              onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <Icon className="w-5 h-5" style={{ color: slot.color }} />
                  <span className="font-bold text-sm text-white">{slot.label}</span>
                </div>
                <button onClick={() => setOpenSlot(null)} className="text-gray-400"><X className="w-4 h-4" /></button>
              </div>
              <div className="p-3 space-y-1.5" style={{ paddingBottom: 'calc(12px + env(safe-area-inset-bottom, 0px))' }}>
                {slot.infras.map(infra => {
                  const owned = isOwned(infra.type);
                  return (
                    <button key={infra.type}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all active:scale-[0.98] ${
                        owned ? 'bg-white/5 border-white/10 hover:bg-white/10' : 'bg-black/30 border-white/5'
                      }`}
                      onClick={() => handleInfraClick(infra)}
                      data-testid={`infra-${infra.type}`}>
                      {owned ? (
                        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: `${slot.color}20`, border: `1.5px solid ${slot.color}50` }}>
                          <Icon className="w-4 h-4" style={{ color: slot.color }} />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-yellow-500/10 border border-yellow-500/30">
                          <Lock className="w-4 h-4 text-yellow-500/70" />
                        </div>
                      )}
                      <div className="flex-1 text-left">
                        <p className={`text-[11px] font-bold ${owned ? 'text-white' : 'text-gray-500'}`}>{infra.name}</p>
                        <p className="text-[8px]" style={{ color: owned ? slot.color : '#666' }}>
                          {owned ? 'Attiva — Tocca per gestire' : 'Non acquistata'}
                        </p>
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
