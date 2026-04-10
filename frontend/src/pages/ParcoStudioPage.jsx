import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { toast } from 'sonner';
import { Lock, Loader2, Building, Film, Tv, Sparkles, Camera, Radio, GraduationCap, Search, Shield, Swords, Scale, ChevronRight } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const MAP_BG = 'https://static.prod-images.emergentagent.com/jobs/47886dbc-bc84-42e0-b9d1-56428c76a4e6/images/e7055672c77e0661bec65b95bce6435e0652309f8cc48e46271fd4415a6f884d.png';

// 6 slots grouped visually — each maps to real infrastructure types
const SLOTS = [
  {
    id: 'studios',
    label: 'Studi di Produzione',
    types: ['production_studio', 'studio_serie_tv', 'studio_anime'],
    icon: Camera,
    route: '/create-film',
    // Position on 2000x2000 map (% from top-left)
    x: 38, y: 10, w: 24, h: 18,
    color: '#e8a040',
  },
  {
    id: 'cinema',
    label: 'Cinema & Distribuzione',
    types: ['cinema', 'drive_in', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema'],
    icon: Film,
    route: '/infrastructure',
    x: 5, y: 30, w: 26, h: 22,
    color: '#60a0e0',
  },
  {
    id: 'talent',
    label: 'Agenzia & Talenti',
    types: ['talent_scout_actors', 'talent_scout_screenwriters', 'cinema_school'],
    icon: GraduationCap,
    route: '/acting-school',
    x: 69, y: 30, w: 26, h: 22,
    color: '#a070d0',
  },
  {
    id: 'events',
    label: 'Eventi & Esperienza',
    types: ['film_festival_venue', 'cinema_museum', 'theme_park'],
    icon: Sparkles,
    route: '/festivals',
    x: 5, y: 60, w: 26, h: 22,
    color: '#50c878',
  },
  {
    id: 'broadcast',
    label: 'Broadcast TV',
    types: ['emittente_tv'],
    icon: Radio,
    route: '/my-tv',
    x: 69, y: 60, w: 26, h: 22,
    color: '#e06060',
  },
  {
    id: 'strategic',
    label: 'Divisioni Strategiche',
    types: ['pvp_operative', 'pvp_investigative', 'pvp_legal'],
    icon: Shield,
    route: '/pvp-arena',
    x: 35, y: 76, w: 30, h: 18,
    color: '#c0c0c0',
  },
];

export default function ParcoStudioPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [backgrounds, setBackgrounds] = useState({});
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef(null);

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('/infrastructure/parco-studio/backgrounds');
      setBackgrounds(res.data.backgrounds || {});
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  // Auto-center on studio on load
  useEffect(() => {
    if (!loading && scrollRef.current) {
      const el = scrollRef.current;
      const mapW = el.scrollWidth;
      const mapH = el.scrollHeight;
      // Center of the map (where the studio is)
      el.scrollLeft = (mapW - el.clientWidth) / 2;
      el.scrollTop = (mapH * 0.28) - (el.clientHeight / 3);
    }
  }, [loading]);

  // Calculate slot state from owned infras
  const getSlotState = (slot) => {
    let ownedCount = 0;
    let totalCount = slot.types.length;
    let firstOwnedId = null;

    for (const t of slot.types) {
      const info = backgrounds[t];
      if (info?.owned) {
        ownedCount++;
        if (!firstOwnedId) firstOwnedId = info.infra_id;
      }
    }

    if (ownedCount === 0) return { state: 'empty', owned: 0, total: totalCount, infraId: null };
    if (ownedCount < totalCount) return { state: 'partial', owned: ownedCount, total: totalCount, infraId: firstOwnedId };
    return { state: 'complete', owned: ownedCount, total: totalCount, infraId: firstOwnedId };
  };

  const handleSlotClick = (slot, slotState) => {
    if (slotState.state === 'empty') {
      navigate('/infrastructure');
      toast.info(`Acquista un'infrastruttura ${slot.label} per sbloccare!`);
      return;
    }
    if (slotState.infraId) {
      navigate(`/infrastructure/${slotState.infraId}`);
    } else {
      navigate(slot.route);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-[#080604] flex items-center justify-center z-40">
        <Loader2 className="w-8 h-8 text-yellow-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-[#060503] z-30" style={{ top: 48, bottom: 52 }} data-testid="parco-studio-page">
      {/* Scrollable map container */}
      <div
        ref={scrollRef}
        className="w-full h-full overflow-auto"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >
        {/* Map canvas - 2000x2000 virtual pixels */}
        <div className="relative" style={{ width: 2000, height: 2000 }}>
          {/* Background image */}
          <img
            src={MAP_BG}
            alt="Parco Studio"
            className="absolute inset-0 w-full h-full object-cover"
            draggable={false}
          />
          {/* Dark overlay for readability */}
          <div className="absolute inset-0 bg-black/20 pointer-events-none" />

          {/* Central Studio Label */}
          <div className="absolute flex flex-col items-center pointer-events-none"
            style={{ left: '35%', top: '33%', width: '30%' }}>
            <div className="bg-black/60 backdrop-blur-sm rounded-lg px-4 py-2 border border-yellow-500/30">
              <p className="font-['Bebas_Neue'] text-2xl text-yellow-500 tracking-widest text-center leading-none">CineWorld</p>
              <p className="font-['Bebas_Neue'] text-sm text-yellow-500/60 tracking-widest text-center">Studio's</p>
            </div>
          </div>

          {/* 6 Slot hotspots */}
          {SLOTS.map(slot => {
            const slotState = getSlotState(slot);
            const Icon = slot.icon;
            const isEmpty = slotState.state === 'empty';
            const isPartial = slotState.state === 'partial';
            const isComplete = slotState.state === 'complete';

            return (
              <div
                key={slot.id}
                className="absolute cursor-pointer group"
                style={{
                  left: `${slot.x}%`,
                  top: `${slot.y}%`,
                  width: `${slot.w}%`,
                  height: `${slot.h}%`,
                }}
                onClick={() => handleSlotClick(slot, slotState)}
                data-testid={`slot-${slot.id}`}
              >
                {/* Slot overlay */}
                <div className={`absolute inset-0 rounded-xl border-2 transition-all duration-300 flex flex-col items-center justify-center gap-2
                  ${isEmpty
                    ? 'bg-black/50 border-white/10 group-hover:bg-black/40 group-hover:border-white/20'
                    : isPartial
                    ? 'bg-black/30 border-dashed group-hover:bg-black/20'
                    : 'bg-black/15 group-hover:bg-black/10'
                  }`}
                  style={{ borderColor: isEmpty ? undefined : `${slot.color}50` }}
                >
                  {/* Lock icon for empty */}
                  {isEmpty && <Lock className="w-10 h-10 text-white/25" />}

                  {/* Building icon for owned */}
                  {!isEmpty && (
                    <div className="w-16 h-16 rounded-full flex items-center justify-center"
                      style={{ background: `${slot.color}20`, border: `2px solid ${slot.color}60` }}>
                      <Icon className="w-8 h-8" style={{ color: slot.color }} />
                    </div>
                  )}

                  {/* Label */}
                  <div className="bg-black/70 backdrop-blur-sm rounded-lg px-3 py-1.5 max-w-[90%]">
                    <p className="text-white font-bold text-sm text-center leading-tight">{slot.label}</p>
                    {/* Progress */}
                    <p className="text-center mt-0.5" style={{ color: isEmpty ? '#888' : slot.color, fontSize: 11 }}>
                      {isEmpty ? 'Terreno disponibile' : `${slotState.owned}/${slotState.total} costruiti`}
                    </p>
                    {/* Progress bar */}
                    {!isEmpty && (
                      <div className="mt-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
                        <div className="h-full rounded-full transition-all" style={{
                          width: `${(slotState.owned / slotState.total) * 100}%`,
                          background: slot.color,
                        }} />
                      </div>
                    )}
                  </div>

                  {/* Click indicator */}
                  <div className="flex items-center gap-1 text-white/40 text-xs">
                    <span>{isEmpty ? 'Acquista' : 'Entra'}</span>
                    <ChevronRight className="w-3 h-3" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mini-map indicator (top-right) */}
      <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm rounded-lg px-2 py-1 border border-white/10">
        <p className="text-[8px] text-yellow-500/70 font-bold tracking-wider">VISTA PARCO STUDIO</p>
      </div>

      {/* Back button */}
      <button
        className="absolute top-2 left-2 bg-black/60 backdrop-blur-sm rounded-lg px-3 py-1.5 border border-white/10 text-gray-300 text-xs flex items-center gap-1"
        onClick={() => navigate('/infrastructure')}
        data-testid="parco-back"
      >
        <Building className="w-3 h-3" /> Classica
      </button>
    </div>
  );
}
