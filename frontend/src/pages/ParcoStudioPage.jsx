import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Lock, Loader2, Building, Film, Tv, Sparkles, Camera, Radio, GraduationCap, Shield } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// 6 slots with positions mapped to the actual image landmarks (% of 1400x1400)
const SLOTS = [
  {
    id: 'studios', label: 'Studi di Produzione',
    types: ['production_studio', 'studio_serie_tv', 'studio_anime'],
    icon: Camera, color: '#e8a040',
    // Center building area
    x: 34, y: 28, w: 32, h: 18,
  },
  {
    id: 'cinema', label: 'Cinema & Sale',
    types: ['cinema', 'drive_in', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema'],
    icon: Film, color: '#60a0e0',
    // Bottom-left lots
    x: 4, y: 55, w: 28, h: 20,
  },
  {
    id: 'talent', label: 'Agenzia & Talenti',
    types: ['talent_scout_actors', 'talent_scout_screenwriters', 'cinema_school'],
    icon: GraduationCap, color: '#a070d0',
    // Right lots (top-right area)
    x: 65, y: 22, w: 28, h: 20,
  },
  {
    id: 'events', label: 'Eventi & Esperienza',
    types: ['film_festival_venue', 'cinema_museum', 'theme_park'],
    icon: Sparkles, color: '#50c878',
    // Top-left lots
    x: 4, y: 22, w: 28, h: 20,
  },
  {
    id: 'broadcast', label: 'Broadcast TV',
    types: ['emittente_tv'],
    icon: Radio, color: '#e06060',
    // Bottom-right lots
    x: 65, y: 55, w: 28, h: 20,
  },
  {
    id: 'strategic', label: 'Divisioni Strategiche',
    types: ['pvp_operative', 'pvp_investigative', 'pvp_legal'],
    icon: Shield, color: '#c0c0c0',
    // Bottom center lots
    x: 28, y: 78, w: 44, h: 14,
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
    } catch {}
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  // Auto-center on studio building
  useEffect(() => {
    if (!loading && scrollRef.current) {
      const el = scrollRef.current;
      // Center on the studio (roughly 50%,40% of the map)
      el.scrollLeft = (el.scrollWidth * 0.5) - (el.clientWidth / 2);
      el.scrollTop = (el.scrollHeight * 0.38) - (el.clientHeight / 2);
    }
  }, [loading]);

  const getSlotState = (slot) => {
    let ownedCount = 0, firstId = null;
    for (const t of slot.types) {
      const info = backgrounds[t];
      if (info?.owned) { ownedCount++; if (!firstId) firstId = info.infra_id; }
    }
    if (ownedCount === 0) return { state: 'empty', owned: 0, total: slot.types.length, infraId: null };
    if (ownedCount < slot.types.length) return { state: 'partial', owned: ownedCount, total: slot.types.length, infraId: firstId };
    return { state: 'complete', owned: ownedCount, total: slot.types.length, infraId: firstId };
  };

  const handleSlotClick = (slot, ss) => {
    if (ss.state === 'empty') {
      navigate('/infrastructure');
      return;
    }
    if (ss.infraId) navigate(`/infrastructure/${ss.infraId}`);
    else navigate('/infrastructure');
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
      {/* Scrollable map */}
      <div ref={scrollRef} className="w-full h-full overflow-auto" style={{ WebkitOverflowScrolling: 'touch' }}>
        <div className="relative" style={{ width: 1400, height: 1400 }}>
          {/* Static background image */}
          <img
            src="/parco-studio-map.png"
            alt="CineWorld Studios"
            className="absolute inset-0 w-full h-full object-cover"
            draggable={false}
          />

          {/* 6 Slot overlays */}
          {SLOTS.map(slot => {
            const ss = getSlotState(slot);
            const Icon = slot.icon;
            const isEmpty = ss.state === 'empty';

            return (
              <div
                key={slot.id}
                className="absolute cursor-pointer"
                style={{ left: `${slot.x}%`, top: `${slot.y}%`, width: `${slot.w}%`, height: `${slot.h}%` }}
                onClick={() => handleSlotClick(slot, ss)}
                data-testid={`slot-${slot.id}`}
              >
                {isEmpty ? (
                  /* LOCKED — pulsating lock */
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <div className="animate-pulse flex flex-col items-center" style={{ animationDuration: '2s' }}>
                      <div className="w-12 h-12 rounded-full flex items-center justify-center mb-1"
                        style={{ background: 'rgba(0,0,0,0.5)', border: '2px solid rgba(212,175,55,0.5)', boxShadow: '0 0 15px rgba(212,175,55,0.3)' }}>
                        <Lock className="w-6 h-6 text-yellow-500" />
                      </div>
                      <div className="bg-black/70 backdrop-blur-sm rounded px-2 py-1">
                        <p className="text-[9px] font-bold text-yellow-500/80 text-center">{slot.label}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* OWNED — name + progress */
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <div className="bg-black/60 backdrop-blur-sm rounded-lg px-3 py-2 border"
                      style={{ borderColor: `${slot.color}50`, boxShadow: `0 0 12px ${slot.color}20` }}>
                      <div className="flex items-center gap-1.5 justify-center">
                        <Icon className="w-4 h-4" style={{ color: slot.color }} />
                        <p className="text-[10px] font-bold text-white text-center">{slot.label}</p>
                      </div>
                      <p className="text-[8px] text-center mt-0.5" style={{ color: slot.color }}>
                        {ss.owned}/{ss.total} attivi
                      </p>
                      <div className="mt-1 h-1 rounded-full bg-white/10 overflow-hidden w-full">
                        <div className="h-full rounded-full transition-all" style={{
                          width: `${(ss.owned / ss.total) * 100}%`,
                          background: slot.color,
                        }} />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

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
