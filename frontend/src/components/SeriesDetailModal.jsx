// CineWorld - Series/Anime Detail Modal
// Shows poster, title, genre, episodes, quality, views, broadcast status
// "Gestisci Palinsesto" button for owners

import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { Tv, Sparkles, Eye, Star, Film, Clock, Users, Calendar, ChevronRight, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300';
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};

export function SeriesDetailModal({ open, onClose, series, stationId, isOwner, onManagePalinsesto }) {
  const { api } = useContext(AuthContext);
  const [broadcastInfo, setBroadcastInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !series || !stationId) return;
    setLoading(true);
    api.get(`/tv-stations/${stationId}/broadcast/${series.id}`)
      .then(r => setBroadcastInfo(r.data))
      .catch(() => setBroadcastInfo(null))
      .finally(() => setLoading(false));
  }, [open, series, stationId, api]);

  if (!series) return null;

  const bstate = broadcastInfo?.broadcast_state || series.broadcast_state || 'idle';
  const stateLabel = { idle: 'Non trasmessa', scheduled: 'Programmata', airing: 'In onda', completed: 'Completata', reruns: 'In replica', retired: 'Ritirata' };
  const stateColor = { idle: 'bg-gray-500/20 text-gray-400', scheduled: 'bg-blue-500/20 text-blue-400', airing: 'bg-green-500/20 text-green-400', completed: 'bg-cyan-500/20 text-cyan-400', reruns: 'bg-amber-500/20 text-amber-400', retired: 'bg-red-500/20 text-red-400' };
  const isAnime = series.type === 'anime' || series.content_type === 'anime';
  const totalEps = broadcastInfo?.total_episodes || series.total_episodes || series.num_episodes || 0;
  const viewers = broadcastInfo?.total_viewers || series.broadcast_viewers || 0;
  const quality = series.quality_score || 0;

  // Episodes aired info
  const airedCount = broadcastInfo?.current_episode || series.episodes_aired || 0;
  const nextAir = broadcastInfo?.next_air_at || series.next_air_at;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="bg-[#0F0F10] border-white/10 max-w-[400px] p-0 [&>button]:hidden" data-testid="series-detail-modal">
        {/* Hero poster */}
        <div className="relative h-[200px] overflow-hidden rounded-t-lg">
          <img src={posterSrc(series.poster_url)} alt={series.title} className="w-full h-full object-cover" onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'; }} />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0F0F10] via-transparent to-transparent" />
          <button onClick={onClose} className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white hover:bg-black/70">✕</button>
          <div className="absolute bottom-3 left-3 right-3">
            <div className="flex items-center gap-2 mb-1">
              {isAnime ? <Sparkles className="w-4 h-4 text-orange-400" /> : <Tv className="w-4 h-4 text-blue-400" />}
              <h2 className="text-lg font-bold truncate">{series.title}</h2>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={`text-[9px] border-0 ${stateColor[bstate] || stateColor.idle}`}>
                {stateLabel[bstate] || bstate}
              </Badge>
              {series.genre_name && <span className="text-[10px] text-gray-400">{series.genre_name}</span>}
            </div>
          </div>
        </div>

        {/* Stats grid */}
        {loading ? (
          <div className="flex items-center justify-center py-8"><Loader2 className="w-5 h-5 text-gray-500 animate-spin" /></div>
        ) : (
          <div className="px-4 pb-4 space-y-3">
            <div className="grid grid-cols-4 gap-2">
              <StatBox label="Episodi" value={totalEps} icon={<Film className="w-3 h-3" />} color="text-blue-400" />
              <StatBox label="Valore" value={`${quality}/100`} icon={<Star className="w-3 h-3" />} color="text-yellow-400" />
              <StatBox label="Views" value={viewers > 1000 ? `${(viewers/1000).toFixed(1)}K` : viewers} icon={<Eye className="w-3 h-3" />} color="text-cyan-400" />
              <StatBox label="Trasmessi" value={`${airedCount}/${totalEps}`} icon={<Users className="w-3 h-3" />} color="text-green-400" />
            </div>

            {/* Schedule info */}
            {bstate === 'scheduled' && nextAir && (
              <Card className="bg-blue-500/5 border-blue-500/20">
                <CardContent className="p-3 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-blue-400" />
                  <div>
                    <p className="text-[10px] text-blue-400 font-medium">Programmata</p>
                    <p className="text-[11px] text-gray-400">Primo ep: {new Date(nextAir).toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {bstate === 'airing' && (
              <Card className="bg-green-500/5 border-green-500/20">
                <CardContent className="p-3 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  <div>
                    <p className="text-[10px] text-green-400 font-medium">In onda - Ep. {airedCount + 1}/{totalEps}</p>
                    {nextAir && <p className="text-[10px] text-gray-500">Prossimo: {new Date(nextAir).toLocaleDateString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</p>}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Episode list — scrollable, all clickable, plot only if aired */}
            {broadcastInfo?.episodes && broadcastInfo.episodes.length > 0 && (
              <div>
                <p className="text-[10px] text-gray-500 mb-1.5 uppercase tracking-wider">Episodi ({broadcastInfo.episodes.length})</p>
                <EpisodeList episodes={broadcastInfo.episodes} />
              </div>
            )}

            {/* Manage button (owner only) */}
            {isOwner && (
              <Button
                className="w-full h-11 bg-gradient-to-r from-yellow-500 to-amber-500 hover:from-yellow-400 hover:to-amber-400 text-black font-bold text-sm rounded-xl"
                onClick={() => { onClose(); onManagePalinsesto(series); }}
                data-testid="manage-palinsesto-btn"
              >
                <ChevronRight className="w-4 h-4 mr-2" /> Gestisci Palinsesto
              </Button>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function StatBox({ label, value, icon, color }) {
  return (
    <div className="bg-white/[0.03] rounded-lg p-2 text-center">
      <div className={`flex items-center justify-center mb-1 ${color}`}>{icon}</div>
      <p className="text-xs font-bold">{value}</p>
      <p className="text-[8px] text-gray-500">{label}</p>
    </div>
  );
}

function EpisodeList({ episodes }) {
  const [expanded, setExpanded] = useState(null);
  const typeLabels = { peak: 'PEAK', filler: 'FILLER', plot_twist: 'TWIST', season_finale: 'FINALE' };
  const typeColors = { peak: 'text-amber-400', filler: 'text-gray-500', plot_twist: 'text-purple-400', season_finale: 'text-red-400' };
  return (
    <div
      className="space-y-1 max-h-[260px] overflow-y-auto pr-1"
      style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.15) transparent' }}
      data-testid="series-detail-episode-list"
    >
      {episodes.map((ep) => {
        const isAired = ep.broadcast_state === 'aired';
        const isOnAir = ep.broadcast_state === 'on_air';
        const isExpanded = expanded === ep.number;
        return (
          <div key={ep.number}>
            <div
              onClick={() => setExpanded(isExpanded ? null : ep.number)}
              className={`flex items-center gap-2 rounded-lg p-2 cursor-pointer transition-all touch-manipulation ${
                isAired ? 'bg-white/[0.03] border border-green-500/10 hover:bg-white/[0.06]'
                : isOnAir ? 'bg-green-500/5 border border-green-500/20 hover:bg-green-500/10'
                : 'bg-black/20 border border-white/5 hover:bg-white/[0.04]'
              }`}
              data-testid={`series-detail-ep-${ep.number}`}
            >
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold flex-shrink-0 ${
                isAired ? 'bg-green-500/20 text-green-400'
                : isOnAir ? 'bg-green-500 text-white'
                : 'bg-white/5 text-gray-500'
              }`}>{ep.number}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className={`text-[11px] font-medium truncate ${isAired || isOnAir ? '' : 'text-gray-400'}`}>{ep.title || `Episodio ${ep.number}`}</p>
                  {typeLabels[ep.episode_type] && (isAired || isOnAir) && (
                    <span className={`text-[7px] font-bold ${typeColors[ep.episode_type]}`}>{typeLabels[ep.episode_type]}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                {isAired && ep.consensus_pct > 0 && (
                  <span className={`text-[9px] font-bold ${ep.consensus_pct >= 70 ? 'text-green-400' : ep.consensus_pct >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>{ep.consensus_pct}%</span>
                )}
                {isOnAir && (
                  <>
                    <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-[8px] text-green-400 font-bold">LIVE</span>
                  </>
                )}
                {!isAired && !isOnAir && ep.release_datetime && (
                  <span className="text-[8px] text-gray-500">
                    <Clock className="w-2.5 h-2.5 inline mr-0.5" />
                    {new Date(ep.release_datetime).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })}
                  </span>
                )}
                <ChevronRight className={`w-3 h-3 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </div>
            </div>
            {isExpanded && (
              <div className="ml-8 mt-1 mb-1 p-2 rounded-lg bg-white/[0.02] border border-white/5">
                {(isAired || isOnAir) ? (
                  (ep.plot || ep.mini_plot)
                    ? <p className="text-[10px] text-gray-300 italic leading-relaxed">{ep.plot || ep.mini_plot}</p>
                    : <p className="text-[10px] text-gray-500 italic">Trama non disponibile.</p>
                ) : (
                  <p className="text-[10px] text-gray-500 italic">
                    Trama non ancora disponibile — sarà visibile quando l'episodio verrà trasmesso.
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
