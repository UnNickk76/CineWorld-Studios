import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { toast } from 'sonner';
import { Lock, Loader2, Building, Film, Tv, Sparkles, Camera, Radio, GraduationCap, Search, Shield, Swords, Scale, Eye, Ticket, Trophy, MapPin, RefreshCw } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const INFRA_ICONS = {
  cinema: Film, drive_in: Camera, multiplex_small: Building, multiplex_medium: Building,
  multiplex_large: Building, vip_cinema: Ticket, cinema_museum: Eye, film_festival_venue: Trophy,
  theme_park: MapPin, production_studio: Camera, studio_serie_tv: Tv, studio_anime: Sparkles,
  emittente_tv: Radio, cinema_school: GraduationCap, talent_scout_actors: Search,
  talent_scout_screenwriters: Search, pvp_operative: Swords, pvp_investigative: Shield, pvp_legal: Scale,
};

const INFRA_ROUTES = {
  cinema: '/infrastructure', drive_in: '/infrastructure', multiplex_small: '/infrastructure',
  multiplex_medium: '/infrastructure', multiplex_large: '/infrastructure', vip_cinema: '/infrastructure',
  cinema_museum: '/infrastructure', film_festival_venue: '/festivals', theme_park: '/infrastructure',
  production_studio: '/create-film', studio_serie_tv: '/create-series', studio_anime: '/create-anime',
  emittente_tv: '/my-tv', cinema_school: '/acting-school',
  talent_scout_actors: '/infrastructure', talent_scout_screenwriters: '/infrastructure',
  pvp_operative: '/pvp-arena', pvp_investigative: '/pvp-arena', pvp_legal: '/pvp-arena',
};

const CATEGORIES = [
  { key: 'cinema', label: 'Cinema & Sale', types: ['cinema', 'drive_in', 'multiplex_small', 'multiplex_medium', 'multiplex_large', 'vip_cinema', 'cinema_museum', 'film_festival_venue', 'theme_park'] },
  { key: 'studios', label: 'Studi', types: ['production_studio', 'studio_serie_tv', 'studio_anime', 'emittente_tv'] },
  { key: 'talent', label: 'Talento', types: ['cinema_school', 'talent_scout_actors', 'talent_scout_screenwriters'] },
  { key: 'pvp', label: 'Divisioni', types: ['pvp_operative', 'pvp_investigative', 'pvp_legal'] },
];

export default function ParcoStudioPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [backgrounds, setBackgrounds] = useState({});
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(null);

  const loadBackgrounds = useCallback(async () => {
    try {
      const res = await api.get('/infrastructure/parco-studio/backgrounds');
      setBackgrounds(res.data.backgrounds || {});
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadBackgrounds(); }, [loadBackgrounds]);

  const generateBg = async (infraType) => {
    setGenerating(infraType);
    try {
      const res = await api.post('/infrastructure/parco-studio/generate-background', { infra_type: infraType });
      setBackgrounds(prev => ({
        ...prev,
        [infraType]: { ...prev[infraType], image_url: res.data.image_url },
      }));
      if (!res.data.cached) toast.success('Background generato!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore generazione');
    } finally { setGenerating(null); }
  };

  const handleClick = (infraType, info) => {
    if (!info.owned) {
      navigate('/infrastructure');
      toast.info('Acquista questa infrastruttura per sbloccarla!');
      return;
    }
    if (info.infra_id) {
      navigate(`/infrastructure/${info.infra_id}`);
    } else {
      navigate(INFRA_ROUTES[infraType] || '/infrastructure');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#080604] flex items-center justify-center pt-14 pb-20">
        <Loader2 className="w-6 h-6 text-yellow-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#080604] pt-14 pb-20 px-2" data-testid="parco-studio-page">
      {/* Header */}
      <div className="text-center py-4">
        <h1 className="font-['Bebas_Neue'] text-2xl tracking-widest text-yellow-500/90">Vista Parco Studio</h1>
        <p className="text-[10px] text-gray-500 mt-0.5">Esplora le tue infrastrutture in modalita cinematografica</p>
      </div>

      {CATEGORIES.map(cat => (
        <div key={cat.key} className="mb-4">
          <h2 className="font-['Bebas_Neue'] text-xs tracking-widest text-gray-500 uppercase px-1 mb-2">{cat.label}</h2>
          <div className="grid grid-cols-2 gap-2">
            {cat.types.map(infraType => {
              const info = backgrounds[infraType] || {};
              const Icon = INFRA_ICONS[infraType] || Building;
              const hasImage = !!info.image_url;
              const isGenerating = generating === infraType;
              const isOwned = info.owned;

              return (
                <div key={infraType} className="relative rounded-lg overflow-hidden border border-white/8 group" style={{ minHeight: 120 }}
                  data-testid={`parco-${infraType}`}>

                  {/* Background image or placeholder */}
                  {hasImage ? (
                    <div className="absolute inset-0">
                      <img src={`${BACKEND_URL}${info.image_url}`} alt="" className="w-full h-full object-cover"
                        loading="lazy" onError={(e) => { e.target.style.display = 'none'; }} />
                      <div className="absolute inset-0 bg-black/40" />
                    </div>
                  ) : (
                    <div className="absolute inset-0 bg-gradient-to-br from-[#12100a] to-[#0a0806]" />
                  )}

                  {/* Locked overlay */}
                  {!isOwned && (
                    <div className="absolute inset-0 bg-black/70 z-10 flex flex-col items-center justify-center cursor-pointer"
                      onClick={() => handleClick(infraType, info)}>
                      <Lock className="w-5 h-5 text-gray-500 mb-1" />
                      <span className="text-[8px] text-gray-500 text-center px-2">Acquista infrastruttura</span>
                    </div>
                  )}

                  {/* Content */}
                  <div className={`relative z-[5] flex flex-col items-center justify-center h-full min-h-[120px] p-2 ${isOwned ? 'cursor-pointer' : ''}`}
                    onClick={() => isOwned && handleClick(infraType, info)}>
                    <Icon className="w-6 h-6 text-yellow-500/80 mb-1 drop-shadow-lg" />
                    <span className="text-[10px] font-bold text-white text-center drop-shadow-lg leading-tight">{info.name || infraType}</span>

                    {/* Generate button */}
                    {isOwned && !hasImage && !isGenerating && (
                      <button className="mt-1.5 flex items-center gap-1 px-2 py-0.5 rounded bg-yellow-500/20 border border-yellow-500/30 text-yellow-400 text-[8px]"
                        onClick={(e) => { e.stopPropagation(); generateBg(infraType); }}
                        data-testid={`gen-bg-${infraType}`}>
                        <Sparkles className="w-2.5 h-2.5" /> Genera sfondo
                      </button>
                    )}

                    {/* Loading spinner */}
                    {isGenerating && (
                      <div className="mt-1.5 flex items-center gap-1 text-yellow-400 text-[8px]">
                        <Loader2 className="w-3 h-3 animate-spin" /> Generazione...
                      </div>
                    )}

                    {/* Regenerate button (small, on owned + has image) */}
                    {isOwned && hasImage && !isGenerating && (
                      <button className="absolute top-1.5 right-1.5 w-5 h-5 flex items-center justify-center rounded-full bg-black/50 text-gray-400 hover:text-yellow-400 transition-colors opacity-0 group-hover:opacity-100"
                        onClick={(e) => { e.stopPropagation(); generateBg(infraType); }}
                        title="Rigenera sfondo">
                        <RefreshCw className="w-2.5 h-2.5" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
