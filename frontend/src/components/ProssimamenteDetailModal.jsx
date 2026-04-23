// CineWorld - Prossimamente (Serie TV / Anime) Detail Modal
// Used by Dashboard "IN ARRIVO SU TV" and "Ultimi Aggiornamenti" rows.
// Shows poster, producer, genre, CWSv, airing countdown, and a clickable episode list
// where each episode expands to reveal its AI-generated mini_plot.

import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { Tv, Sparkles, Star, Film as FilmIcon, Clock, X, ChevronDown, ChevronUp, Play } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300';
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};

function humanCountdown(targetIso) {
  if (!targetIso) return null;
  try {
    const t = new Date(targetIso).getTime();
    const d = t - Date.now();
    if (d <= 0) return 'in onda';
    const h = Math.floor(d / 3600000);
    const m = Math.floor((d % 3600000) / 60000);
    if (h >= 24) return `${Math.floor(h / 24)}g ${h % 24}h`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  } catch { return null; }
}

export default function ProssimamenteDetailModal({ open, onClose, seriesId }) {
  const { api, user } = useContext(AuthContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedEp, setExpandedEp] = useState(null);
  const [myStations, setMyStations] = useState([]);
  const [stationsLoaded, setStationsLoaded] = useState(false);
  const [showStationPicker, setShowStationPicker] = useState(false);
  const [assigning, setAssigning] = useState(false);

  useEffect(() => {
    if (!open || !seriesId) return;
    setLoading(true);
    setData(null);
    setExpandedEp(null);
    setShowStationPicker(false);
    api.get(`/series/${seriesId}`)
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [open, seriesId, api]);

  const isOwner = !!(user && data && data.user_id === user.id);
  const noStationAssigned = isOwner && data && !data.scheduled_for_tv_station;

  useEffect(() => {
    if (!showStationPicker || stationsLoaded) return;
    const token = localStorage.getItem('cineworld_token');
    fetch(`${process.env.REACT_APP_BACKEND_URL}/api/my-owned-tv-stations`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(d => setMyStations(d?.stations || []))
      .catch(() => setMyStations([]))
      .finally(() => setStationsLoaded(true));
  }, [showStationPicker, stationsLoaded]);

  const assignToStation = async (stationId) => {
    setAssigning(true);
    try {
      await api.post(`/tv-stations/${stationId}/assign-series/${seriesId}`);
      const { toast } = await import('sonner');
      toast.success('Serie inviata alla tua emittente TV');
      onClose();
    } catch (e) {
      const { toast } = await import('sonner');
      toast.error(e?.response?.data?.detail || 'Errore invio a TV');
    } finally { setAssigning(false); }
  };

  if (!open) return null;
  const isAnime = data?.type === 'anime';
  const episodes = Array.isArray(data?.episodes) ? data.episodes : [];
  const producerName = data?.owner?.nickname || data?.producer?.nickname || '';
  const quality = data?.quality_score || 0;
  const cwsvDisplay = data?.cwsv_display;
  const airingCountdown = humanCountdown(data?.tv_airing_start);

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="bg-[#0D0D0F] border-white/10 max-w-[420px] p-0 [&>button]:hidden overflow-hidden" data-testid="prossimamente-detail-modal">
        {/* Hero */}
        <div className="relative h-[220px] overflow-hidden">
          {data?.poster_url ? (
            <img src={posterSrc(data.poster_url)} alt={data.title} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-indigo-900/60 to-black flex items-center justify-center">
              {isAnime ? <Sparkles className="w-10 h-10 text-orange-400/60" /> : <Tv className="w-10 h-10 text-indigo-400/60" />}
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-[#0D0D0F] via-[#0D0D0F]/40 to-transparent" />
          <button onClick={onClose} data-testid="prossimamente-modal-close"
            className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/60 hover:bg-black/80 flex items-center justify-center">
            <X className="w-4 h-4 text-white" />
          </button>
          <div className="absolute bottom-3 left-3 right-3">
            <div className="flex items-center gap-2 mb-1">
              {isAnime ? <Sparkles className="w-4 h-4 text-orange-400" /> : <Tv className="w-4 h-4 text-indigo-400" />}
              <h2 className="text-lg font-bold text-white truncate">{data?.title || 'Caricamento...'}</h2>
            </div>
            {producerName && <p className="text-[11px] text-gray-400">di {producerName}</p>}
          </div>
        </div>

        {/* Stats */}
        {data && (
          <div className="px-4 py-3 space-y-3 max-h-[55vh] overflow-y-auto scrollbar-hide">
            <div className="grid grid-cols-4 gap-2">
              <StatBox label="Tipo" value={isAnime ? 'Anime' : 'Serie'} color="text-indigo-400" />
              <StatBox label="Ep." value={data?.num_episodes || episodes.length || 0} color="text-cyan-400" icon={<FilmIcon className="w-3 h-3" />} />
              {quality > 0 && <StatBox label="CWSv" value={cwsvDisplay || quality} color="text-yellow-400" icon={<Star className="w-3 h-3" />} />}
              {data?.genre_name && <StatBox label="Genere" value={data.genre_name} color="text-pink-400" />}
            </div>

            {/* Airing countdown */}
            {airingCountdown && (
              <div className="flex items-center gap-2 p-2 rounded-lg bg-indigo-500/8 border border-indigo-500/20">
                <Clock className="w-4 h-4 text-indigo-400" />
                <p className="text-[11px] text-indigo-300">
                  {airingCountdown === 'in onda' ? 'Trasmissione in corso' : `Inizio trasmissione tra ${airingCountdown}`}
                </p>
              </div>
            )}

            {/* Preplot */}
            {(data?.preplot || data?.short_plot) && (
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                <p className="text-[8px] text-gray-500 font-bold uppercase mb-1">Trama</p>
                <p className="text-[11px] text-gray-300 leading-snug">{data.preplot || data.short_plot}</p>
              </div>
            )}

            {/* Episodes */}
            {episodes.length > 0 ? (
              <div>
                <p className="text-[8px] text-gray-500 font-bold uppercase mb-2">Episodi ({episodes.length})</p>
                <div className="space-y-1">
                  {episodes.map((ep, i) => {
                    const epNum = ep.number || (i + 1);
                    const isOpen = expandedEp === epNum;
                    const hasPlot = !!ep.mini_plot;
                    return (
                      <div key={epNum} className="rounded-lg bg-white/[0.03] border border-white/5 overflow-hidden">
                        <button
                          onClick={() => setExpandedEp(isOpen ? null : epNum)}
                          className="w-full px-2.5 py-2 flex items-center gap-2 hover:bg-white/[0.04] active:bg-white/[0.06] transition-colors text-left"
                          data-testid={`prossimamente-ep-${epNum}`}
                        >
                          <div className="w-7 h-7 rounded-full bg-indigo-500/15 text-indigo-400 flex items-center justify-center text-[10px] font-black flex-shrink-0">
                            {epNum}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-[11px] font-bold text-white truncate">{ep.title || `Episodio ${epNum}`}</p>
                            {ep.is_finale ? <p className="text-[8px] text-amber-400 font-bold">FINALE STAGIONE</p> : ep.duration_min ? <p className="text-[8px] text-gray-500">{ep.duration_min}m</p> : null}
                          </div>
                          {ep.cwsv_display && <span className="text-[9px] text-yellow-400 font-bold">{ep.cwsv_display}</span>}
                          {hasPlot && (isOpen ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />)}
                        </button>
                        {isOpen && hasPlot && (
                          <div className="px-3 pb-2.5 pt-0.5 border-t border-white/5">
                            <p className="text-[10px] text-gray-300 leading-relaxed italic">{ep.mini_plot}</p>
                          </div>
                        )}
                        {isOpen && !hasPlot && (
                          <div className="px-3 pb-2.5 pt-0.5 border-t border-white/5">
                            <p className="text-[9px] text-gray-600">Mini-trama disponibile al rilascio</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : data?.num_episodes > 0 ? (
              <div className="p-3 rounded-lg border border-white/5 text-center">
                <Play className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                <p className="text-[10px] text-gray-500">{data.num_episodes} episodi — mini-trame disponibili al rilascio</p>
              </div>
            ) : null}

            {/* Owner actions: if no TV station assigned, offer send-to-TV or sell */}
            {isOwner && noStationAssigned && (
              <div className="pt-1">
                <p className="text-[8px] text-gray-500 font-bold uppercase mb-2">Azioni</p>
                {!showStationPicker ? (
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setShowStationPicker(true)}
                      data-testid="owner-send-to-tv-btn"
                      className="p-2.5 rounded-lg bg-gradient-to-br from-blue-500/15 to-indigo-500/10 border border-blue-500/30 hover:from-blue-500/25 hover:to-indigo-500/20 active:scale-[0.98] transition-all text-left"
                    >
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <Tv className="w-3.5 h-3.5 text-blue-400" />
                        <p className="text-[10px] font-bold text-white">Invia a TV</p>
                      </div>
                      <p className="text-[8px] text-gray-400 leading-snug">Scegli una delle tue emittenti</p>
                    </button>
                    <button
                      onClick={() => {
                        onClose();
                        window.location.href = `/marketplace?sell=series&id=${seriesId}`;
                      }}
                      data-testid="owner-sell-market-btn"
                      className="p-2.5 rounded-lg bg-gradient-to-br from-amber-500/15 to-yellow-500/10 border border-amber-500/30 hover:from-amber-500/25 hover:to-yellow-500/20 active:scale-[0.98] transition-all text-left"
                    >
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className="text-[13px]">$</span>
                        <p className="text-[10px] font-bold text-white">Vendi al Mercato</p>
                      </div>
                      <p className="text-[8px] text-gray-400 leading-snug">Gestisci prezzi di licenza</p>
                    </button>
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <button onClick={() => setShowStationPicker(false)} className="text-[9px] text-gray-400 hover:text-white">&larr; Torna</button>
                    {!stationsLoaded ? (
                      <p className="text-[9px] text-gray-500 text-center py-3">Caricamento...</p>
                    ) : myStations.length === 0 ? (
                      <div className="p-3 rounded-lg border border-amber-500/25 bg-amber-500/5 text-center">
                        <p className="text-[10px] text-amber-300 font-bold">Nessuna emittente TV posseduta</p>
                        <p className="text-[8px] text-gray-500 mt-1">Acquista un'infrastruttura TV per trasmettere questa serie.</p>
                      </div>
                    ) : (
                      myStations.map(st => (
                        <button key={st.id} onClick={() => assignToStation(st.id)} disabled={assigning}
                          data-testid={`owner-assign-station-${st.id}`}
                          className="w-full p-2 rounded-lg border border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/10 active:scale-[0.98] text-left disabled:opacity-50 transition-all">
                          <p className="text-[10px] font-bold text-white flex items-center gap-1.5">
                            <Tv className="w-3 h-3 text-blue-400" /> {st.station_name || 'Emittente'}
                          </p>
                          <p className="text-[7px] text-gray-500">Lv.{st.infra_level || 1} · {st.nation || 'Italia'}</p>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {loading && !data && (
          <div className="py-10 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function StatBox({ label, value, icon, color }) {
  return (
    <div className="bg-white/[0.03] rounded-lg p-2 text-center">
      {icon && <div className={`flex items-center justify-center mb-1 ${color}`}>{icon}</div>}
      <p className="text-[11px] font-bold truncate">{value}</p>
      <p className="text-[7px] text-gray-500 uppercase">{label}</p>
    </div>
  );
}
