// CineWorld Studio's - SeriesDetail (reuses FilmDetail structure)
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600';
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

import React, { useState, useEffect, useContext } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  Film, Star, TrendingUp, Users, Sparkles, Crown, Loader2, ArrowLeft,
  BarChart3, Activity, TrendingDown, Newspaper, Image, RefreshCw, Tv, Play
} from 'lucide-react';

export default function SeriesDetail() {
  const { api, user } = useContext(AuthContext);
  const { id } = useParams();
  const navigate = useNavigate();
  const [series, setSeries] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generatingPoster, setGeneratingPoster] = useState(false);

  useEffect(() => {
    loadSeries();
  }, [id]);

  const loadSeries = async () => {
    try {
      const res = await api.get(`/series/${id}`);
      if (!res.data || res.data.detail) { setLoading(false); return; }
      setSeries(res.data);
    } catch (e) { toast.error('Serie non trovata'); }
    setLoading(false);
  };

  const generatePoster = async () => {
    setGeneratingPoster(true);
    try {
      const res = await api.post(`/series-pipeline/${id}/generate-poster`, { mode: 'ai' }, { timeout: 60000 });
      if (res.data.poster_url) {
        setSeries(prev => ({ ...prev, poster_url: res.data.poster_url }));
        toast.success('Locandina generata!');
      }
    } catch (e) { toast.error('Errore generazione locandina'); }
    setGeneratingPoster(false);
  };

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center pt-16">
      <Loader2 className="w-8 h-8 text-red-400 animate-spin" />
    </div>
  );

  if (!series) return (
    <div className="min-h-screen bg-[#0A0A0B] text-white flex items-center justify-center pt-16 pb-20">
      <div className="text-center">
        <Tv className="w-12 h-12 text-gray-700 mx-auto mb-3" />
        <p className="text-gray-400 text-sm mb-2">Serie non trovata</p>
        <Button variant="outline" onClick={() => navigate(-1)}>Torna indietro</Button>
      </div>
    </div>
  );

  const isOwner = series.user_id === user?.id;
  const isAnime = series.type === 'anime';
  const accentColor = isAnime ? 'purple' : 'red';

  // Tier calculation (same as films)
  const getTier = (q) => {
    if (q >= 90) return { name: 'Masterpiece', color: 'text-yellow-400', bg: 'bg-yellow-500/15 border-yellow-500/30' };
    if (q >= 80) return { name: 'Epic', color: 'text-purple-400', bg: 'bg-purple-500/15 border-purple-500/30' };
    if (q >= 70) return { name: 'Excellent', color: 'text-blue-400', bg: 'bg-blue-500/15 border-blue-500/30' };
    if (q >= 55) return { name: 'Good', color: 'text-green-400', bg: 'bg-green-500/15 border-green-500/30' };
    if (q >= 40) return { name: 'Promising', color: 'text-teal-400', bg: 'bg-teal-500/15 border-teal-500/30' };
    return { name: 'Flop', color: 'text-red-400', bg: 'bg-red-500/15 border-red-500/30' };
  };

  const tier = getTier(series.quality_score || 0);
  const re = series.release_event;

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pt-16 pb-20" data-testid="series-detail-page">
      {/* Header with poster */}
      <div className="relative">
        <div className="h-48 overflow-hidden">
          <img src={posterSrc(series.poster_url)} alt={series.title}
            className="w-full h-full object-cover blur-sm opacity-30 scale-110" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0A0A0B]/80 to-[#0A0A0B]" />
        </div>
        <div className="absolute top-4 left-3 z-10">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="text-white/70 h-7 text-xs">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Indietro
          </Button>
        </div>
        <div className="absolute bottom-0 left-0 right-0 px-4 pb-3 flex gap-3 items-end">
          <div className="w-24 h-36 rounded-lg overflow-hidden shadow-2xl flex-shrink-0 bg-gray-900 border border-white/10">
            <img src={posterSrc(series.poster_url)} alt={series.title}
              className="w-full h-full object-cover" data-testid="series-poster" />
          </div>
          <div className="flex-1 min-w-0 pb-1">
            <Badge className={`text-[8px] mb-1 ${isAnime ? 'bg-purple-500/30 text-purple-300' : 'bg-red-500/30 text-red-300'}`}>
              {isAnime ? 'Anime' : 'Serie TV'}
            </Badge>
            <h1 className="text-lg font-black leading-tight truncate" data-testid="series-title">{series.title}</h1>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-400">
              <span>{series.genre_name}</span>
              <span>S{series.season_number}</span>
              <span>{series.num_episodes} ep.</span>
            </div>
            {series.owner && (
              <p className="text-[10px] text-gray-500 mt-0.5">di {series.owner.nickname}</p>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-3 mt-3 space-y-3 max-w-lg mx-auto">

        {/* Poster actions */}
        {isOwner && (
          <div className="flex gap-2">
            {!series.poster_url ? (
              <Button onClick={generatePoster} disabled={generatingPoster}
                className={`flex-1 text-xs h-8 ${isAnime ? 'bg-purple-600 hover:bg-purple-500' : 'bg-red-600 hover:bg-red-500'}`}
                data-testid="generate-poster-btn">
                {generatingPoster ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Image className="w-3 h-3 mr-1" />}
                {generatingPoster ? 'Generazione...' : 'Genera Locandina'}
              </Button>
            ) : (
              <Button onClick={generatePoster} disabled={generatingPoster} variant="outline"
                className="text-xs h-8 border-gray-700" data-testid="regenerate-poster-btn">
                {generatingPoster ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <RefreshCw className="w-3 h-3 mr-1" />}
                Rigenera Locandina
              </Button>
            )}
          </div>
        )}

        {/* Stats grid */}
        {series.status === 'completed' && (
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-[#151517] rounded-lg p-2 text-center border border-white/5">
              <p className={`text-xl font-black ${(series.quality_score || 0) >= 70 ? 'text-green-400' : (series.quality_score || 0) >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                {Math.round(series.quality_score || 0)}
              </p>
              <p className="text-[8px] text-gray-500">Qualita</p>
            </div>
            <div className="bg-[#151517] rounded-lg p-2 text-center border border-white/5">
              <p className="text-xl font-black text-yellow-400">{(series.audience_rating || 0).toFixed?.(1) || '—'}</p>
              <p className="text-[8px] text-gray-500">Rating</p>
            </div>
            <div className="bg-[#151517] rounded-lg p-2 text-center border border-white/5">
              <p className="text-xl font-black text-green-400">${((series.total_revenue || 0) / 1000000).toFixed(1)}M</p>
              <p className="text-[8px] text-gray-500">Incasso</p>
            </div>
            <div className="bg-[#151517] rounded-lg p-2 text-center border border-white/5">
              <p className="text-xl font-black text-blue-400">{((series.audience || 0) / 1000).toFixed(0)}K</p>
              <p className="text-[8px] text-gray-500">Audience</p>
            </div>
          </div>
        )}

        {/* Tier badge */}
        {series.status === 'completed' && (
          <div className={`flex items-center justify-between p-2.5 rounded-lg border ${tier.bg}`} data-testid="series-tier-badge">
            <div className="flex items-center gap-2">
              <Crown className={`w-4 h-4 ${tier.color}`} />
              <div>
                <p className={`font-bold text-sm uppercase ${tier.color}`}>{tier.name}</p>
                <p className="text-[9px] text-gray-500">Tier della Serie</p>
              </div>
            </div>
            <span className="text-base font-bold text-white/80">{Math.round(series.quality_score || 0)}</span>
          </div>
        )}

        {/* Release Event */}
        {re && re.id !== 'nothing_special' && (
          <Card className={`border overflow-hidden ${
            re.type === 'positive' ? 'bg-gradient-to-br from-emerald-500/10 via-[#1A1A1A] to-green-500/5 border-emerald-500/30' :
            re.type === 'negative' ? 'bg-gradient-to-br from-red-500/10 via-[#1A1A1A] to-orange-500/5 border-red-500/30' :
            'bg-gradient-to-br from-amber-500/10 via-[#1A1A1A] to-yellow-500/5 border-amber-500/30'
          }`} data-testid="series-release-event">
            <CardHeader className="pb-1 pt-3 px-3">
              <CardTitle className="text-xs flex items-center gap-1.5">
                <Sparkles className={`w-3.5 h-3.5 ${re.type === 'positive' ? 'text-emerald-400' : re.type === 'negative' ? 'text-red-400' : 'text-amber-400'}`} />
                {re.name}
                <Badge className={`text-[7px] ml-auto ${
                  re.rarity === 'rare' ? 'bg-yellow-500/30 text-yellow-300' :
                  re.rarity === 'uncommon' ? 'bg-blue-500/30 text-blue-300' : 'bg-gray-500/30 text-gray-300'
                }`}>{re.rarity === 'rare' ? 'Raro' : re.rarity === 'uncommon' ? 'Non Comune' : 'Comune'}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3 pt-0">
              <p className="text-[10px] text-gray-300 italic mb-2">"{re.description}"</p>
              <div className="flex gap-2">
                {re.quality_modifier !== 0 && (
                  <Badge className={`text-[8px] ${re.quality_modifier > 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                    Qualita {re.quality_modifier > 0 ? '+' : ''}{re.quality_modifier}
                  </Badge>
                )}
                {re.revenue_modifier !== 0 && (
                  <Badge className={`text-[8px] ${re.revenue_modifier > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    Ricavi {re.revenue_modifier > 0 ? '+' : ''}{re.revenue_modifier}%
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Description */}
        {series.description && (
          <Card className="bg-[#151517] border-white/5">
            <CardContent className="p-3">
              <p className="text-xs text-gray-300 leading-relaxed">{series.description}</p>
            </CardContent>
          </Card>
        )}

        {/* Cast */}
        {series.cast?.length > 0 && (
          <Card className="bg-[#151517] border-white/5">
            <CardHeader className="pb-1 pt-3 px-3">
              <CardTitle className="text-xs flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-blue-400" /> Cast ({series.cast.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3 pt-1">
              <div className="space-y-1.5">
                {series.cast.map((actor, i) => (
                  <div key={actor.actor_id || i} className="flex items-center gap-2 p-1.5 rounded bg-black/20">
                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center text-[9px] font-bold text-white/60 flex-shrink-0">
                      {(actor.name || 'A')[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] font-medium truncate">{actor.name}</p>
                      <div className="flex items-center gap-2 text-[8px] text-gray-500">
                        {actor.role && <span>{actor.role}</span>}
                        <span>Skill: {actor.skill || '?'}</span>
                        {actor.popularity && <span>Pop: {actor.popularity}</span>}
                        {actor.is_guest_star && <Badge className="text-[7px] bg-yellow-500/20 text-yellow-300 h-3">Guest Star</Badge>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quality Breakdown */}
        {series.quality_breakdown && Object.keys(series.quality_breakdown).length > 0 && (
          <Card className="bg-[#151517] border-white/5">
            <CardHeader className="pb-1 pt-3 px-3">
              <CardTitle className="text-xs flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-amber-400" /> Modificatori Qualita
              </CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3 pt-1 space-y-1">
              {Object.entries(series.quality_breakdown).map(([key, val]) => {
                const numVal = typeof val === 'number' ? val : parseFloat(String(val));
                const isPos = numVal > 0;
                const isNeg = numVal < 0;
                return (
                  <div key={key} className="flex items-center justify-between py-1 px-2 rounded bg-black/20 text-[10px]">
                    <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className={`font-mono font-semibold ${isPos ? 'text-emerald-400' : isNeg ? 'text-red-400' : 'text-gray-300'}`}>
                      {isPos ? '+' : ''}{typeof val === 'number' ? val.toFixed(1) : val}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        {/* Audience Comments */}
        {series.audience_comments?.length > 0 && (
          <Card className="bg-[#151517] border-white/5">
            <CardHeader className="pb-1 pt-3 px-3">
              <CardTitle className="text-xs flex items-center gap-1.5">
                <Newspaper className="w-3.5 h-3.5 text-cyan-400" /> Commenti del Pubblico
              </CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3 pt-1 space-y-1">
              {series.audience_comments.slice(0, 5).map((c, i) => (
                <div key={i} className={`p-1.5 rounded text-[10px] border-l-2 ${
                  (c.rating || c.score || 5) >= 7 ? 'bg-emerald-500/10 border-emerald-500' :
                  (c.rating || c.score || 5) <= 4 ? 'bg-red-500/10 border-red-500' :
                  'bg-amber-500/10 border-amber-500'
                }`}>
                  <div className="flex justify-between mb-0.5">
                    <span className="text-gray-300 font-medium">{c.username || c.name || 'Utente'}</span>
                    <span className={`font-bold ${(c.rating || c.score || 5) >= 7 ? 'text-emerald-400' : (c.rating || c.score || 5) <= 4 ? 'text-red-400' : 'text-amber-400'}`}>
                      {c.rating || c.score || '—'}/10
                    </span>
                  </div>
                  {c.comment && <p className="text-gray-400 italic leading-tight">"{c.comment.substring(0, 120)}{c.comment.length > 120 ? '...' : ''}"</p>}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Production Info */}
        <Card className="bg-[#151517] border-white/5">
          <CardHeader className="pb-1 pt-3 px-3">
            <CardTitle className="text-xs flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-gray-400" /> Informazioni Produzione
            </CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-3 pt-1">
            <div className="grid grid-cols-2 gap-1.5 text-[10px]">
              <div className="p-1.5 rounded bg-black/20">
                <span className="text-gray-500">Tipo</span>
                <p className="font-medium">{isAnime ? 'Anime' : 'Serie TV'}</p>
              </div>
              <div className="p-1.5 rounded bg-black/20">
                <span className="text-gray-500">Stagione</span>
                <p className="font-medium">S{series.season_number}</p>
              </div>
              <div className="p-1.5 rounded bg-black/20">
                <span className="text-gray-500">Episodi</span>
                <p className="font-medium">{series.num_episodes}</p>
              </div>
              <div className="p-1.5 rounded bg-black/20">
                <span className="text-gray-500">Genere</span>
                <p className="font-medium">{series.genre_name}</p>
              </div>
              {series.production_cost > 0 && (
                <div className="p-1.5 rounded bg-black/20">
                  <span className="text-gray-500">Costo Produzione</span>
                  <p className="font-medium text-yellow-400">${(series.production_cost || 0).toLocaleString()}</p>
                </div>
              )}
              {series.cast_total_salary > 0 && (
                <div className="p-1.5 rounded bg-black/20">
                  <span className="text-gray-500">Salari Cast</span>
                  <p className="font-medium text-orange-400">${(series.cast_total_salary || 0).toLocaleString()}</p>
                </div>
              )}
              <div className="p-1.5 rounded bg-black/20">
                <span className="text-gray-500">Stato</span>
                <p className={`font-medium ${series.status === 'completed' ? 'text-green-400' : 'text-amber-400'}`}>
                  {series.status === 'completed' ? 'Completata' : series.status}
                </p>
              </div>
              {series.created_at && (
                <div className="p-1.5 rounded bg-black/20">
                  <span className="text-gray-500">Creata il</span>
                  <p className="font-medium">{new Date(series.created_at).toLocaleDateString('it-IT')}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
