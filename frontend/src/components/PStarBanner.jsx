import React, { useEffect, useState, useContext } from 'react';
import { Star, Award, MapPin, Users, Trophy, X, Clapperboard, MessageSquare, Clock, AlertCircle } from 'lucide-react';
import { Dialog, DialogContent } from './ui/dialog';
import { AuthContext } from '../contexts';
import { PStarScoreCard } from '../pages/LaPrimaEvents';
import { useNavigate } from 'react-router-dom';

/**
 * PStarBanner — shown on film popup for films that had a La Prima.
 * Clicking opens a scrollable modal with:
 *   - Dettagli evento (fixed top)
 *   - Partecipazione cinema (38/42) based on hype+quality+city
 *   - PStar score (if ended)
 *   - Rejection reports (cinemas that didn't join — progressively revealed)
 *   - Audience comments (dynamic, hourly)
 */
export default function PStarBanner({ film }) {
  const { api } = useContext(AuthContext);
  const [entry, setEntry] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [openDetail, setOpenDetail] = useState(false);
  const navigate = useNavigate();

  const isPremiere = film?.release_type === 'premiere';
  const premiere = film?.premiere || {};
  const hasPremiereSetup = isPremiere && premiere.city && premiere.datetime;

  useEffect(() => {
    if (!hasPremiereSetup || !film?.id || !api) return;
    setLoading(true);
    Promise.all([
      api.get(`/events/la-prima/film/${film.id}/pstar`).then(r => r.data?.entry || null).catch(() => null),
      api.get(`/events/la-prima/film/${film.id}/report`).then(r => r.data || null).catch(() => null),
    ]).then(([e, r]) => { setEntry(e); setReport(r); })
      .finally(() => setLoading(false));
  }, [hasPremiereSetup, film?.id, api, openDetail]);

  if (!hasPremiereSetup) return null;

  const spectators = report?.spectators_total ?? premiere.spectators_total ?? 0;
  const participating = report?.participating_cinemas ?? premiere.cinemas_count ?? premiere.num_cinemas ?? 1;
  const totalCinemas = report?.total_cinemas ?? premiere.total_cinemas_in_city ?? null;
  const openingShow = report?.opening_showtime ?? premiere.opening_showtime ?? null;

  const now = Date.now();
  const pdt = premiere.datetime ? new Date(premiere.datetime).getTime() : null;
  const end = pdt ? pdt + 24 * 3600 * 1000 : null;
  let state = 'waiting';
  if (pdt && now >= pdt && now < end) state = 'live';
  else if (end && now >= end) state = 'ended';

  const scoreColor = entry ? ({
    legendary: '#facc15', brilliant: '#e5e7eb', great: '#fb923c',
    good: '#a3a3a3', ok: '#6b7280', weak: '#4b5563',
  }[entry.tier] || '#fbbf24') : '#fbbf24';

  return (
    <>
      <div
        className="ct2-pstar-banner"
        onClick={() => setOpenDetail(true)}
        data-testid="pstar-banner"
        style={{
          cursor: 'pointer', margin: '8px 10px 0', padding: '8px 14px', borderRadius: '6px',
          background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.12) 0%, rgba(180, 140, 30, 0.06) 100%)',
          border: `1px solid ${scoreColor}55`,
          boxShadow: `inset 0 0 12px ${scoreColor}22, 0 0 8px ${scoreColor}33`,
          position: 'relative', overflow: 'hidden',
        }}
      >
        <div className="ct2-pstar-shine" />
        <div className="flex items-center gap-2" style={{ position: 'relative' }}>
          <Award className="w-4 h-4" style={{ color: scoreColor, flexShrink: 0 }} />
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-black uppercase tracking-[2px]" style={{ color: scoreColor, fontFamily: "'Bebas Neue', sans-serif" }}>
              {state === 'live' ? 'LA PRIMA LIVE' : state === 'ended' ? 'LA PRIMA CONCLUSA' : 'LA PRIMA A BREVE'} · {premiere.city}
            </p>
            {report?.official_cinema && (
              <p className="text-[8px] text-yellow-200/70 truncate italic -mt-0.5" data-testid="pstar-banner-cinema">🎬 {report.official_cinema}</p>
            )}
            <div className="flex items-center gap-2 mt-0.5 text-[9px] text-yellow-200/80 flex-wrap">
              <span className="inline-flex items-center gap-0.5">
                <MapPin className="w-2 h-2" />
                {totalCinemas ? `${participating}/${totalCinemas} cinema` : `${participating} cinema`}
              </span>
              {spectators > 0 && (
                <span className="inline-flex items-center gap-0.5"><Users className="w-2 h-2" />{spectators.toLocaleString()} spettatori</span>
              )}
            </div>
          </div>
          {entry && entry.score !== undefined && (
            <div className="flex items-center gap-1 px-2 py-1 rounded-full" style={{ background: `${scoreColor}30`, border: `1px solid ${scoreColor}66`, flexShrink: 0 }}>
              <Star className="w-3 h-3 fill-current" style={{ color: scoreColor }} />
              <span className="text-[11px] font-black" style={{ color: scoreColor }}>{entry.score.toFixed(1)}</span>
            </div>
          )}
        </div>
        <style>{`
          @keyframes pstar-shine { 0% { transform: translateX(-100%); } 100% { transform: translateX(200%); } }
          .ct2-pstar-shine {
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.14) 50%, transparent 100%);
            animation: pstar-shine 3.8s ease-in-out infinite; pointer-events: none;
          }
        `}</style>
      </div>

      <Dialog open={openDetail} onOpenChange={(v) => !v && setOpenDetail(false)}>
        <DialogContent
          className="bg-[#0a0606] border-yellow-500/30 text-white w-[95vw] max-w-md p-0 max-h-[90vh] overflow-hidden flex flex-col"
          data-testid="pstar-detail-dialog"
        >
          {/* Fixed header */}
          <div className="flex items-center justify-between p-4 pb-3 border-b border-yellow-500/20 bg-[#0a0606] sticky top-0 z-10 shrink-0">
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-yellow-400" />
              <h3 className="text-sm font-bold text-yellow-400 uppercase tracking-wider">Resoconto La Prima</h3>
            </div>
            <button
              onClick={() => setOpenDetail(false)}
              className="text-gray-500 hover:text-white p-1"
              data-testid="pstar-detail-close" aria-label="Chiudi">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Scrollable body */}
          <div className="flex-1 overflow-y-auto px-4 pb-4 pt-3 space-y-3" data-testid="pstar-detail-scroll">
            {/* FIXED-TOP Premiere summary */}
            <div className="p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/20">
              <p className="text-[10px] font-bold text-yellow-400 uppercase tracking-wider mb-2">Dettagli Evento</p>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div><span className="text-gray-500">Città</span>: <span className="text-yellow-300 font-bold">{premiere.city}</span></div>
                <div>
                  <span className="text-gray-500">Cinema</span>:{' '}
                  <span className="text-yellow-300 font-bold">
                    {totalCinemas ? `${participating}/${totalCinemas}` : participating}
                  </span>
                </div>
                <div><span className="text-gray-500">Spettatori</span>: <span className="text-yellow-300 font-bold">{spectators.toLocaleString()}</span></div>
                <div>
                  <span className="text-gray-500">Data</span>:{' '}
                  <span className="text-yellow-300 font-bold">
                    {premiere.datetime ? new Date(premiere.datetime).toLocaleString('it-IT', {day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit'}) : '—'}
                  </span>
                </div>
              </div>
              {openingShow && (
                <div className="mt-2 pt-2 border-t border-yellow-500/10 text-[10px]">
                  <div className="flex items-center gap-1.5">
                    <Clapperboard className="w-3 h-3 text-yellow-400 shrink-0" />
                    <span className="text-gray-400 shrink-0">Prima proiezione ore</span>
                    <span className="text-yellow-300 font-bold">{openingShow}</span>
                  </div>
                  {report?.official_cinema && (
                    <div className="mt-1 pl-4 text-yellow-200/90 italic" data-testid="pstar-official-cinema">
                      al <span className="font-bold not-italic">{report.official_cinema}</span>
                      <span className="text-gray-500"> — 1 cinema per il debutto ufficiale</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* PStar / status */}
            {loading ? (
              <p className="text-[10px] text-gray-500 text-center py-2">Caricamento...</p>
            ) : entry ? (
              <PStarScoreCard entry={entry} />
            ) : state === 'ended' ? (
              <div className="p-3 rounded-xl bg-gray-800/30 border border-gray-700/30 text-center">
                <p className="text-[10px] text-gray-400">PStar in calcolo (ogni 15 minuti)</p>
              </div>
            ) : (
              <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-center">
                <p className="text-[10px] text-cyan-300 font-bold">La Prima {state === 'live' ? 'IN CORSO' : 'IN ATTESA'}</p>
                <p className="text-[9px] text-gray-400 mt-1">Il PStar sarà calcolato al termine delle 24 ore.</p>
              </div>
            )}

            {/* Rejection reports */}
            {report?.rejection_reports?.length > 0 && (
              <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/20">
                <div className="flex items-center gap-1.5 mb-2">
                  <AlertCircle className="w-3 h-3 text-red-400" />
                  <p className="text-[10px] font-bold text-red-400 uppercase tracking-wider">
                    Cinema non partecipanti ({report.total_cinemas - report.participating_cinemas})
                  </p>
                </div>
                <div className="space-y-1.5" data-testid="rejection-reports-list">
                  {report.rejection_reports.map((r, idx) => (
                    <div key={idx} className="flex gap-2 text-[10px] border-l-2 border-red-500/30 pl-2">
                      <span className="text-red-300 font-bold shrink-0">{r.cinema_name}</span>
                      <span className="text-gray-400 italic">{r.reason}</span>
                    </div>
                  ))}
                  {report.total_cinemas - report.participating_cinemas > report.rejection_reports.length && (
                    <p className="text-[9px] text-gray-500 italic mt-1">
                      …altri {report.total_cinemas - report.participating_cinemas - report.rejection_reports.length} resoconti in arrivo
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Audience comments — dynamic hourly */}
            {report?.audience_comments?.length > 0 && (
              <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                <div className="flex items-center gap-1.5 mb-2">
                  <MessageSquare className="w-3 h-3 text-emerald-400" />
                  <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                    Commenti dalla sala
                  </p>
                </div>
                <div className="space-y-2" data-testid="audience-comments-list">
                  {report.audience_comments.map((c, idx) => (
                    <div key={idx} className="text-[10px] border-l-2 border-emerald-500/30 pl-2">
                      <p className="text-gray-200 italic">"{c.text}"</p>
                      <div className="flex items-center gap-1 mt-0.5 text-[9px] text-gray-500">
                        <Clock className="w-2 h-2" /> {c.posted_ago}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Link to events page */}
            <button
              onClick={() => { setOpenDetail(false); navigate('/events/la-prima'); }}
              className="w-full py-2.5 rounded-xl bg-yellow-500/15 border border-yellow-500/30 text-yellow-300 text-[11px] font-bold hover:bg-yellow-500/25 active:scale-95 transition"
              data-testid="go-to-events-btn">
              <Trophy className="w-3 h-3 inline mr-1" /> Vedi classifica eventi La Prima
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
