import React, { useEffect, useRef, useState } from 'react';
import { Film, Sparkles, Crown, Play, Loader2, Lock } from 'lucide-react';
import { toast } from 'sonner';
import TrailerPlayerModal from './TrailerPlayerModal';

const TIERS = [
  { key: 'base', label: 'Trailer Base', duration: 10, cost: 0, hype: 3, frames: 3, icon: Film, color: 'from-sky-600 to-blue-500', border: 'border-sky-500/40' },
  { key: 'cinematic', label: 'Cinematico', duration: 20, cost: 10, hype: 8, frames: 6, icon: Sparkles, color: 'from-purple-600 to-fuchsia-500', border: 'border-purple-500/40' },
  { key: 'pro', label: 'Trailer PRO', duration: 30, cost: 20, hype: 15, frames: 10, icon: Crown, color: 'from-amber-500 to-orange-500', border: 'border-amber-500/40' },
];

const tierOrder = { base: 0, cinematic: 1, pro: 2 };

/**
 * TrailerGeneratorCard — pipeline block for trailer generation.
 * Props:
 *  - contentId: id del film/serie/anime
 *  - contentTitle: titolo per share
 *  - api: axios instance
 *  - userCredits: cinecrediti disponibili
 *  - canGenerate: bool (false se non owner o fase non valida)
 *  - onGenerated: callback dopo generazione
 */
export default function TrailerGeneratorCard({ contentId, contentTitle, contentGenre = '', api, userCredits = 0, canGenerate = true, onGenerated }) {
  const [trailer, setTrailer] = useState(null);
  const [job, setJob] = useState(null); // {status, progress, tier, estimated_seconds}
  const [showPlayer, setShowPlayer] = useState(false);
  const pollRef = useRef(null);

  // Initial load
  useEffect(() => {
    if (!contentId) return;
    refreshTrailer();
    // Also check if a job is in flight
    api.get(`/trailers/${contentId}/status`).then(r => {
      if (r.data?.status === 'running') {
        setJob(r.data);
        startPolling();
      }
    }).catch(() => {});
    return () => clearInterval(pollRef.current);
     
  }, [contentId]);

  const refreshTrailer = async () => {
    try {
      const r = await api.get(`/trailers/${contentId}`);
      setTrailer(r.data?.trailer || null);
    } catch { /* */ }
  };

  const startPolling = () => {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const r = await api.get(`/trailers/${contentId}/status`);
        setJob(r.data);
        if (r.data?.status === 'completed') {
          clearInterval(pollRef.current);
          setJob(null);
          await refreshTrailer();
          toast.success('🎬 Trailer pronto!');
          onGenerated?.();
        } else if (r.data?.status === 'failed') {
          clearInterval(pollRef.current);
          setJob(null);
          toast.error('Generazione trailer fallita. Riprova.');
        }
      } catch { /* */ }
    }, 2500);
  };

  const handleGenerate = async (tierKey) => {
    const tier = TIERS.find(t => t.key === tierKey);
    const currentTierKey = trailer?.tier;
    const delta = currentTierKey ? Math.max(0, tier.cost - (TIERS.find(t => t.key === currentTierKey)?.cost || 0)) : tier.cost;
    if (delta > 0 && userCredits < delta) {
      toast.error(`Servono ${delta} cinecrediti (ne hai ${userCredits})`);
      return;
    }
    try {
      const r = await api.post(`/trailers/${contentId}/generate?tier=${tierKey}`);
      setJob({ ...r.data, tier: tierKey });
      toast.success(`Generazione ${tier.label} avviata (~${r.data.estimated_seconds}s)`);
      startPolling();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore generazione');
    }
  };

  const progress = job?.progress || 0;
  const circumference = 2 * Math.PI * 34;
  const dashOffset = circumference - (progress / 100) * circumference;

  // RENDER: job in corso
  if (job && job.status === 'running') {
    const tier = TIERS.find(t => t.key === job.tier) || TIERS[0];
    return (
      <div className="rounded-2xl border border-yellow-500/20 bg-gradient-to-br from-[#161619] to-[#0d0d10] p-5 text-center" data-testid="trailer-generator-card">
        <div className="relative w-20 h-20 mx-auto mb-3">
          <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
            <circle cx="40" cy="40" r="34" fill="none" stroke="url(#gg)" strokeWidth="6" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={dashOffset} style={{ transition: 'stroke-dashoffset 0.5s' }} />
            <defs><linearGradient id="gg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#f5a623" /><stop offset="100%" stopColor="#e94e77" /></linearGradient></defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-black text-yellow-400">{progress}%</span>
          </div>
        </div>
        <p className="text-[13px] font-bold text-yellow-300 mb-1">Creazione {tier.label} in corso…</p>
        <p className="text-[10px] text-gray-500">Stage: {job.stage || 'queued'} · Stima ~{job.estimated_seconds}s</p>
        <p className="text-[9px] text-gray-600 mt-2">Puoi chiudere questa pagina, ti avviso io quando è pronto.</p>
      </div>
    );
  }

  // RENDER: trailer esistente
  if (trailer) {
    const tier = TIERS.find(t => t.key === trailer.tier) || TIERS[0];
    const Icon = tier.icon;
    const canUpgrade = tierOrder[trailer.tier] < 2;
    return (
      <>
        <div className="rounded-2xl border border-yellow-500/25 bg-gradient-to-br from-[#1a1515] to-[#0d0d10] p-4" data-testid="trailer-generator-card">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${tier.color} flex items-center justify-center`}>
                <Icon className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-[11px] font-bold text-white">Trailer {tier.label}</p>
                <p className="text-[8px] text-gray-500 uppercase tracking-wide">{trailer.duration_seconds}s · {trailer.frames?.length || 0} frame · {trailer.views_count || 0} viste</p>
              </div>
            </div>
            {trailer.trending && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-400 font-bold">🔥 TRENDING</span>}
          </div>
          <button
            onClick={() => setShowPlayer(true)}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold flex items-center justify-center gap-2 hover:scale-[1.02] transition-transform"
            data-testid="trailer-watch-btn">
            <Play className="w-4 h-4 fill-black" /> Guarda Trailer
          </button>
          {canUpgrade && canGenerate && (
            <div className="mt-2 flex gap-1.5">
              {TIERS.filter(t => tierOrder[t.key] > tierOrder[trailer.tier]).map(t => {
                const delta = t.cost - tier.cost;
                return (
                  <button key={t.key} onClick={() => handleGenerate(t.key)} className={`flex-1 py-1.5 rounded-lg border ${t.border} bg-white/[0.02] text-[9px] font-bold text-white hover:bg-white/[0.05]`} data-testid={`trailer-upgrade-${t.key}`}>
                    Upgrade → {t.label}<br/><span className="text-yellow-400">{delta > 0 ? `+${delta} cc` : 'GRATIS'}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
        {showPlayer && (
          <TrailerPlayerModal
            trailer={trailer}
            contentTitle={contentTitle}
            contentGenre={contentGenre}
            contentId={contentId}
            api={api}
            onClose={() => { setShowPlayer(false); refreshTrailer(); }}
          />
        )}
      </>
    );
  }

  // RENDER: nessun trailer, generatore
  if (!canGenerate) {
    return (
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 text-center text-[11px] text-gray-500" data-testid="trailer-generator-card">
        <Lock className="w-4 h-4 mx-auto mb-1 text-gray-600" />
        Il trailer sarà disponibile quando il contenuto raggiungerà la fase Pre-Rilascio.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-yellow-500/15 bg-gradient-to-br from-[#161619] to-[#0d0d10] p-4" data-testid="trailer-generator-card">
      <div className="flex items-center gap-2 mb-3">
        <Film className="w-4 h-4 text-yellow-400" />
        <p className="text-[12px] font-bold text-yellow-400 uppercase tracking-wider">Trailer AI (opzionale)</p>
      </div>
      <p className="text-[10px] text-gray-500 mb-3">Crea un trailer cinematografico con immagini AI coerenti. Non blocca la pipeline — puoi generarlo adesso o quando vuoi.</p>
      <div className="grid grid-cols-3 gap-2">
        {TIERS.map(t => {
          const Icon = t.icon;
          const canAfford = t.cost === 0 || userCredits >= t.cost;
          return (
            <button
              key={t.key}
              onClick={() => handleGenerate(t.key)}
              disabled={!canAfford}
              className={`p-2 rounded-xl border ${t.border} bg-gradient-to-br ${t.color} opacity-${canAfford ? '100' : '40'} text-white flex flex-col items-center gap-1 hover:scale-[1.02] transition-transform disabled:cursor-not-allowed`}
              data-testid={`trailer-tier-${t.key}`}>
              <Icon className="w-4 h-4" />
              <span className="text-[10px] font-black uppercase">{t.label.replace('Trailer ', '')}</span>
              <span className="text-[8px] opacity-80">{t.duration}s · {t.frames} frame</span>
              <span className="text-[9px] font-bold bg-black/30 rounded-full px-2 py-0.5 mt-0.5">{t.cost === 0 ? 'GRATIS' : `${t.cost} cc`}</span>
              <span className="text-[7px] opacity-70">+{t.hype}% hype</span>
            </button>
          );
        })}
      </div>
      <p className="text-[8px] text-gray-600 mt-2 text-center">Hype bonus applicato solo se il contenuto è ancora in fase Hype/Pre-Rilascio.</p>
    </div>
  );
}
