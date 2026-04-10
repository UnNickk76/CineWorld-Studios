import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Lock, Loader2, Building, Film, Tv, Sparkles, Camera, Radio, GraduationCap, Shield, ChevronRight } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SLOTS = [
  { id: 'studios', label: 'Studi Produzione', types: ['production_studio', 'studio_serie_tv', 'studio_anime'], icon: Camera, route: '/create-film', x: 33, y: 2, w: 34, h: 16, color: '#e8a040' },
  { id: 'cinema', label: 'Cinema & Sale', types: ['cinema', 'drive_in', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema'], icon: Film, route: '/infrastructure', x: 2, y: 22, w: 30, h: 24, color: '#60a0e0' },
  { id: 'talent', label: 'Agenzia & Talenti', types: ['talent_scout_actors', 'talent_scout_screenwriters', 'cinema_school'], icon: GraduationCap, route: '/acting-school', x: 68, y: 22, w: 30, h: 24, color: '#a070d0' },
  { id: 'events', label: 'Eventi & Esperienza', types: ['film_festival_venue', 'cinema_museum', 'theme_park'], icon: Sparkles, route: '/festivals', x: 2, y: 54, w: 30, h: 24, color: '#50c878' },
  { id: 'broadcast', label: 'Broadcast TV', types: ['emittente_tv'], icon: Radio, route: '/my-tv', x: 68, y: 54, w: 30, h: 24, color: '#e06060' },
  { id: 'strategic', label: 'Div. Strategiche', types: ['pvp_operative', 'pvp_investigative', 'pvp_legal'], icon: Shield, route: '/pvp-arena', x: 28, y: 82, w: 44, h: 16, color: '#c0c0c0' },
];

export default function ParcoStudioPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [backgrounds, setBackgrounds] = useState({});
  const [baseMap, setBaseMap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const scrollRef = useRef(null);
  const generatedRef = useRef(false);

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('/infrastructure/parco-studio/backgrounds');
      setBackgrounds(res.data.backgrounds || {});
      setBaseMap(res.data.base_map_url || null);
      return res.data.base_map_url;
    } catch { return null; }
    finally { setLoading(false); }
  }, [api]);

  // Load data + auto-generate if needed
  useEffect(() => {
    const init = async () => {
      const mapUrl = await loadData();
      // Auto-generate if no map exists (once)
      if (!mapUrl && !generatedRef.current) {
        generatedRef.current = true;
        setGenerating(true);
        try {
          const res = await api.post('/infrastructure/parco-studio/generate-base-map');
          setBaseMap(res.data.image_url);
        } catch { /* silent - will show fallback */ }
        finally { setGenerating(false); }
      }
    };
    init();
  }, [loadData, api]);

  // Auto-center on studio
  useEffect(() => {
    if (!loading && !generating && scrollRef.current) {
      const el = scrollRef.current;
      el.scrollLeft = (el.scrollWidth - el.clientWidth) / 2;
      el.scrollTop = (el.scrollHeight * 0.28) - (el.clientHeight / 3);
    }
  }, [loading, generating, baseMap]);

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
    if (ss.state === 'empty') { navigate('/infrastructure'); return; }
    if (ss.infraId) navigate(`/infrastructure/${ss.infraId}`);
    else navigate(slot.route);
  };

  // Loading / Generating screen
  if (loading || generating) {
    return (
      <div className="fixed inset-0 bg-[#080604] flex flex-col items-center justify-center z-40 gap-3" style={{ top: 48, bottom: 52 }}>
        <Loader2 className="w-8 h-8 text-yellow-500 animate-spin" />
        <p className="text-gray-500 text-xs">{generating ? 'Costruzione Parco Studio in corso...' : 'Caricamento...'}</p>
      </div>
    );
  }

  const mapSize = 1200;
  const mapBg = baseMap ? (baseMap.startsWith('/') ? `${BACKEND_URL}${baseMap}` : baseMap) : null;

  return (
    <div className="fixed inset-0 bg-[#060503] z-30" style={{ top: 48, bottom: 52 }} data-testid="parco-studio-page">
      <div ref={scrollRef} className="w-full h-full overflow-auto" style={{ WebkitOverflowScrolling: 'touch' }}>
        <div className="relative" style={{ width: mapSize, height: mapSize }}>
          {/* Background map */}
          {mapBg ? (
            <img src={mapBg} alt="" className="absolute inset-0 w-full h-full object-cover" draggable={false} loading="lazy" />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-br from-[#1a1508] via-[#0d0a04] to-[#080604]" />
          )}
          <div className="absolute inset-0 bg-black/15 pointer-events-none" />

          {/* Central Studio Label */}
          <div className="absolute flex flex-col items-center pointer-events-none" style={{ left: '30%', top: '38%', width: '40%' }}>
            <div className="bg-black/60 backdrop-blur-sm rounded-lg px-4 py-2 border border-yellow-500/30">
              <p className="font-['Bebas_Neue'] text-xl text-yellow-500 tracking-widest text-center">CineWorld Studio's</p>
            </div>
          </div>

          {/* 6 Slots */}
          {SLOTS.map(slot => {
            const ss = getSlotState(slot);
            const Icon = slot.icon;
            const isEmpty = ss.state === 'empty';

            return (
              <div key={slot.id} className="absolute cursor-pointer group" style={{ left: `${slot.x}%`, top: `${slot.y}%`, width: `${slot.w}%`, height: `${slot.h}%` }}
                onClick={() => handleSlotClick(slot, ss)} data-testid={`slot-${slot.id}`}>
                <div className={`absolute inset-0 rounded-lg border transition-all flex flex-col items-center justify-center gap-1
                  ${isEmpty ? 'bg-black/50 border-white/10' : 'bg-black/25 border-opacity-40'}`}
                  style={{ borderColor: isEmpty ? undefined : slot.color }}>

                  {isEmpty ? (
                    <Lock className="w-6 h-6 text-white/20" />
                  ) : (
                    <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: `${slot.color}25`, border: `1.5px solid ${slot.color}70` }}>
                      <Icon className="w-5 h-5" style={{ color: slot.color }} />
                    </div>
                  )}

                  <div className="bg-black/70 backdrop-blur-sm rounded px-2 py-1 max-w-[95%]">
                    <p className="text-white font-bold text-[10px] text-center leading-tight">{slot.label}</p>
                    <p className="text-center text-[8px]" style={{ color: isEmpty ? '#666' : slot.color }}>
                      {isEmpty ? 'Terreno' : `${ss.owned}/${ss.total}`}
                    </p>
                    {!isEmpty && (
                      <div className="mt-0.5 h-1 rounded-full bg-white/10 overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${(ss.owned / ss.total) * 100}%`, background: slot.color }} />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* UI overlays */}
      <div className="absolute top-1.5 right-1.5 bg-black/60 backdrop-blur-sm rounded px-2 py-0.5 border border-white/10">
        <p className="text-[7px] text-yellow-500/70 font-bold tracking-wider">VISTA PARCO STUDIO</p>
      </div>
      <button className="absolute top-1.5 left-1.5 bg-black/60 backdrop-blur-sm rounded px-2 py-1 border border-white/10 text-gray-300 text-[10px] flex items-center gap-1"
        onClick={() => navigate('/infrastructure')} data-testid="parco-back">
        <Building className="w-3 h-3" /> Classica
      </button>
    </div>
  );
}
