// CineWorld Studio's — LaPrimaBanner
// Banner fisso visualizzato PRIMA del grafico G1/G2/... per i film
// che hanno avuto una "La Prima" (premiere event) prima dell'uscita al cinema.
// Cliccabile → apre stats dedicate della serata.

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Crown, MapPin, Clock, Star, X, Users, TrendingUp, Camera, Award } from 'lucide-react';

const fmtNum = (v) => Number(v || 0).toLocaleString('it-IT');
const fmtMoney = (v) => `$${Math.round(Number(v || 0)).toLocaleString('it-IT')}`;

const SCORE_COLORS = {
  Trionfo: { ring: 'ring-amber-400/60', bg: 'from-amber-500/30 to-yellow-600/15', text: 'text-amber-200' },
  Successo: { ring: 'ring-emerald-500/50', bg: 'from-emerald-500/25 to-emerald-700/10', text: 'text-emerald-200' },
  Discreta: { ring: 'ring-cyan-500/40', bg: 'from-cyan-500/20 to-cyan-700/10', text: 'text-cyan-200' },
  Tiepida: { ring: 'ring-orange-500/40', bg: 'from-orange-500/20 to-orange-700/10', text: 'text-orange-200' },
  Flop: { ring: 'ring-rose-600/50', bg: 'from-rose-600/25 to-rose-800/10', text: 'text-rose-200' },
};

export const LaPrimaBanner = ({ laprima }) => {
  const [showDetail, setShowDetail] = useState(false);
  if (!laprima) return null;

  const style = SCORE_COLORS[laprima.outcome_label] || SCORE_COLORS.Discreta;
  const dateLabel = laprima.date ? new Date(laprima.date).toLocaleDateString('it-IT', { day: '2-digit', month: 'short' }) : '—';
  const boost = laprima.boost_applied_to_g1 || 0;

  return (
    <>
      <button
        onClick={() => setShowDetail(true)}
        className={`w-full text-left rounded-xl bg-gradient-to-r ${style.bg} ring-1 ${style.ring} p-2.5 hover:scale-[1.01] active:scale-[0.99] transition-all`}
        data-testid="laprima-banner"
      >
        <div className="flex items-center gap-2.5">
          <div className={`w-9 h-9 rounded-full bg-zinc-950/40 flex items-center justify-center flex-shrink-0 ${style.text}`}>
            <Crown className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className={`text-[9px] font-black uppercase tracking-wider ${style.text}`}>🥇 La Prima</span>
              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-zinc-950/40 ${style.text}`}>
                {laprima.outcome_label}
              </span>
            </div>
            <div className={`text-xs font-bold ${style.text} truncate flex items-center gap-1.5 mt-0.5`}>
              <MapPin className="w-3 h-3" /> {laprima.city}
              <span className="text-zinc-500">·</span>
              <Clock className="w-3 h-3" /> {dateLabel} {laprima.time}
            </div>
            <div className="flex items-center gap-2 text-[10px] text-zinc-400 mt-0.5">
              <span className="flex items-center gap-0.5"><Star className="w-2.5 h-2.5 text-amber-400" />{laprima.score}/10</span>
              <span>·</span>
              <span>{fmtNum(laprima.attendance)} VIP</span>
              {boost !== 0 && (
                <>
                  <span>·</span>
                  <span className={boost > 0 ? 'text-emerald-400' : 'text-rose-400'}>
                    {boost > 0 ? '+' : ''}{Math.round(boost * 100)}% G1
                  </span>
                </>
              )}
            </div>
          </div>
          <div className={`text-[9px] font-bold ${style.text} opacity-70`}>Tap per dettagli</div>
        </div>
      </button>

      <AnimatePresence>
        {showDetail && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowDetail(false)}
            className="fixed inset-0 z-[10001] bg-black/85 backdrop-blur-sm flex items-center justify-center p-3"
          >
            <motion.div
              initial={{ scale: 0.92, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              onClick={(e) => e.stopPropagation()}
              className={`w-full max-w-md rounded-2xl bg-gradient-to-br ${style.bg} bg-zinc-950 ring-1 ${style.ring} shadow-2xl`}
              data-testid="laprima-detail-modal"
            >
              <div className="flex items-center justify-between p-4 border-b border-zinc-800/60">
                <div className="flex items-center gap-2">
                  <Crown className={`w-5 h-5 ${style.text}`} />
                  <div>
                    <div className={`text-[10px] uppercase tracking-wider font-bold ${style.text}`}>La Prima</div>
                    <div className="text-sm font-bold text-zinc-100">{laprima.outcome_label}</div>
                  </div>
                </div>
                <button onClick={() => setShowDetail(false)} className="p-1 rounded-md hover:bg-zinc-800/60">
                  <X className="w-4 h-4 text-zinc-400" />
                </button>
              </div>

              <div className="p-4 space-y-3">
                {/* Top row */}
                <div className="grid grid-cols-2 gap-2">
                  <DetailCard icon={<MapPin className="w-3 h-3" />} label="Città" value={laprima.city} />
                  <DetailCard icon={<Clock className="w-3 h-3" />} label="Data & ora" value={`${dateLabel} ${laprima.time}`} />
                </div>

                {/* Score big */}
                <div className={`rounded-xl bg-zinc-950/40 ring-1 ${style.ring} p-3 text-center`}>
                  <div className="text-[10px] uppercase tracking-wider text-zinc-400">Valutazione serata</div>
                  <div className={`text-4xl font-black ${style.text} mt-1`}>{laprima.score}/10</div>
                  <div className="flex items-center justify-center gap-0.5 mt-1">
                    {[...Array(10)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-2.5 h-2.5 ${i < Math.round(laprima.score) ? 'text-amber-400 fill-amber-400' : 'text-zinc-700'}`}
                      />
                    ))}
                  </div>
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-2 gap-2">
                  <DetailCard icon={<Users className="w-3 h-3" />} label="Spettatori" value={fmtNum(laprima.attendance)} />
                  <DetailCard icon={<Award className="w-3 h-3" />} label="VIP/Ospiti" value={fmtNum(laprima.vip_attendance)} />
                  <DetailCard icon={<TrendingUp className="w-3 h-3" />} label="Incassi serata" value={fmtMoney(laprima.revenue)} />
                  <DetailCard icon={<Camera className="w-3 h-3" />} label="Copertura media" value={laprima.media_coverage?.toUpperCase()} />
                </div>

                {/* Critic + boost */}
                <div className="rounded-xl bg-zinc-950/40 ring-1 ring-zinc-800 p-3 space-y-2">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-zinc-400">Approvazione critica</span>
                      <span className={`text-xs font-bold ${style.text}`}>{laprima.critic_approval_pct}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-zinc-900 overflow-hidden">
                      <div className={`h-full bg-gradient-to-r from-amber-500 to-amber-300 transition-all`}
                        style={{ width: `${laprima.critic_approval_pct}%` }} />
                    </div>
                  </div>
                  {boost !== 0 && (
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-zinc-400">Bonus al G1 (primo giorno cinema)</span>
                      <span className={`font-bold ${boost > 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                        {boost > 0 ? '+' : ''}{Math.round(boost * 100)}%
                      </span>
                    </div>
                  )}
                </div>

                <div className="text-[9px] text-zinc-600 text-center italic pt-1">
                  La serata di La Prima ha influenzato l'opening day del cinema.
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

const DetailCard = ({ icon, label, value }) => (
  <div className="rounded-lg bg-zinc-950/50 ring-1 ring-zinc-800/60 p-2">
    <div className="text-[9px] text-zinc-500 flex items-center gap-1">{icon} {label}</div>
    <div className="text-xs font-bold text-zinc-200 truncate mt-0.5">{value}</div>
  </div>
);

export default LaPrimaBanner;
