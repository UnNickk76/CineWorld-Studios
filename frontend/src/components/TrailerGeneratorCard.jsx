import React, { useEffect, useRef, useState } from 'react';
import { Film, Sparkles, Crown, Play, Lock, TrendingUp, Trophy, X, Check, SkipForward } from 'lucide-react';
import { toast } from 'sonner';
import TrailerPlayerModal from './TrailerPlayerModal';

const TIERS = [
  { key: 'base', label: 'Base', duration: 10, cost: 0, hype: 3, frames: 3, icon: Film, color: 'from-sky-600 to-blue-500', border: 'border-sky-500/40' },
  { key: 'cinematic', label: 'Cinematico', duration: 20, cost: 10, hype: 8, frames: 6, icon: Sparkles, color: 'from-purple-600 to-fuchsia-500', border: 'border-purple-500/40' },
  { key: 'pro', label: 'PRO', duration: 30, cost: 20, hype: 15, frames: 10, icon: Crown, color: 'from-amber-500 to-orange-500', border: 'border-amber-500/40' },
];

const tierOrder = { base: 0, cinematic: 1, pro: 2 };

// Detect if content is in post-release phase (highlights mode).
function isReleasedContent(contentStatus) {
  const s = (contentStatus || '').toLowerCase();
  return ['released', 'in_theaters', 'in_tv', 'catalog', 'completed', 'withdrawn'].includes(s);
}

/**
 * TrailerGeneratorCard — pipeline block for trailer generation.
 * Auto-switches between two modes based on content status:
 *   - pre_launch (default): blue/orange CTA, +hype boost, full price
 *   - highlights (post-release): gold/trophy CTA, no hype boost, 50% discount
 */
export default function TrailerGeneratorCard({ contentId, contentTitle, contentGenre = '', contentStatus = '', api, userCredits = 0, canGenerate = true, onGenerated, isGuest = false, onSkip, onConfirm }) {
  const [trailer, setTrailer] = useState(null);
  const [job, setJob] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const pollRef = useRef(null);
  const jobStartRef = useRef(null);

  const isReleased = isReleasedContent(contentStatus);
  const mode = isReleased ? 'highlights' : 'pre_launch';
  const modeMeta = isReleased
    ? { label: 'Trailer Highlights', subtitle: 'Best-of per social & archivio · sconto 50%', icon: Trophy, accent: 'from-amber-400 to-yellow-500', accentText: 'text-amber-400', border: 'border-amber-500/30', bg: 'from-[#1a1510] to-[#0d0d10]' }
    : { label: 'Trailer Pre-Lancio', subtitle: 'Concede +hype durante la fase di attesa', icon: TrendingUp, accent: 'from-sky-500 to-blue-500', accentText: 'text-sky-400', border: 'border-sky-500/30', bg: 'from-[#101620] to-[#0d0d10]' };

  // Initial load
  useEffect(() => {
    if (!contentId) return;
    refreshTrailer();
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
    if (!jobStartRef.current) jobStartRef.current = Date.now();
    pollRef.current = setInterval(async () => {
      try {
        const r = await api.get(`/trailers/${contentId}/status`);
        setJob(r.data);
        setElapsed(Math.floor((Date.now() - (jobStartRef.current || Date.now())) / 1000));
        if (r.data?.status === 'completed') {
          clearInterval(pollRef.current);
          jobStartRef.current = null;
          setJob(null);
          await refreshTrailer();
          toast.success(isReleased ? '🏆 Trailer highlights pronto!' : '🎬 Trailer pronto!');
          onGenerated?.();
        } else if (r.data?.status === 'failed') {
          clearInterval(pollRef.current);
          jobStartRef.current = null;
          setJob(null);
          toast.error('Generazione trailer fallita. Riprova.');
        } else if (r.data?.status === 'aborted') {
          clearInterval(pollRef.current);
          jobStartRef.current = null;
          setJob(null);
          toast.info('Generazione trailer annullata.');
        }
      } catch { /* */ }
    }, 2500);
  };

  const handleAbort = async () => {
    if (!window.confirm('Sicuro di voler annullare la generazione? La pipeline può proseguire senza trailer.')) return;
    try {
      await api.post(`/trailers/${contentId}/abort`);
      clearInterval(pollRef.current);
      jobStartRef.current = null;
      setJob(null);
      toast.info('Generazione annullata. Puoi proseguire senza trailer.');
    } catch (e) {
      toast.error('Impossibile annullare');
    }
  };

  const effectiveCost = (baseCost) => {
    if (isGuest) return 0;
    return isReleased ? Math.round(baseCost * 0.5) : baseCost;
  };

  const handleGenerate = async (tierKey) => {
    const tier = TIERS.find(t => t.key === tierKey);
    const currentTierKey = trailer?.tier;
    const sameMode = trailer?.mode === mode;
    const currentCost = (sameMode && currentTierKey) ? effectiveCost(TIERS.find(t => t.key === currentTierKey)?.cost || 0) : 0;
    const targetCost = effectiveCost(tier.cost);
    const delta = Math.max(0, targetCost - currentCost);
    if (delta > 0 && userCredits < delta && !isGuest) {
      toast.error(`Servono ${delta} cinecrediti (ne hai ${userCredits})`);
      return;
    }
    try {
      const r = await api.post(`/trailers/${contentId}/generate?tier=${tierKey}&mode=${mode}`);
      setJob({ ...r.data, tier: tierKey });
      jobStartRef.current = Date.now();
      setElapsed(0);
      toast.success(`Generazione ${tier.label} ${isReleased ? 'highlights' : 'pre-lancio'} avviata (~${r.data.estimated_seconds}s)`);
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
    const estimated = job.estimated_seconds || 20;
    const remaining = Math.max(0, estimated - elapsed);
    return (
      <div className={`relative rounded-2xl border ${modeMeta.border} bg-gradient-to-br ${modeMeta.bg} p-5 text-center`} data-testid="trailer-generator-card">
        <button onClick={handleAbort}
          className="absolute top-2 right-2 w-7 h-7 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 flex items-center justify-center transition-colors"
          data-testid="trailer-abort-btn" title="Annulla generazione">
          <X className="w-4 h-4" />
        </button>
        <div className="relative w-24 h-24 mx-auto mb-3">
          <svg className="w-24 h-24 -rotate-90" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
            <circle cx="40" cy="40" r="34" fill="none" stroke="url(#gg)" strokeWidth="6" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={dashOffset} style={{ transition: 'stroke-dashoffset 0.5s' }} />
            <defs><linearGradient id="gg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#f5a623" /><stop offset="100%" stopColor="#e94e77" /></linearGradient></defs>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-xl font-black ${modeMeta.accentText}`}>{progress}%</span>
            <span className="text-[8px] text-gray-500 font-bold">{remaining}s</span>
          </div>
        </div>
        <p className={`text-[13px] font-bold ${modeMeta.accentText} mb-1`}>Creazione {tier.label} in corso…</p>
        <p className="text-[10px] text-gray-400 mb-1">Attendi il completamento, non chiudere ancora.</p>
        <p className="text-[9px] text-gray-500">Stage: {job.stage || 'queued'} · trascorsi {elapsed}s / ~{estimated}s</p>
        <p className="text-[8px] text-gray-600 mt-2">Tocca la ✕ in alto a destra per annullare e proseguire senza trailer.</p>
      </div>
    );
  }

  // RENDER: trailer esistente
  if (trailer) {
    const tier = TIERS.find(t => t.key === trailer.tier) || TIERS[0];
    const Icon = tier.icon;
    // Can upgrade if current tier isn't maxed AND mode matches
    const sameMode = (trailer.mode || 'pre_launch') === mode;
    const canUpgrade = sameMode && tierOrder[trailer.tier] < 2;
    const trailerIsHighlights = (trailer.mode || 'pre_launch') === 'highlights';
    return (
      <>
        <div className={`rounded-2xl border ${modeMeta.border} bg-gradient-to-br ${modeMeta.bg} p-4`} data-testid="trailer-generator-card">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${tier.color} flex items-center justify-center`}>
                <Icon className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-[11px] font-bold text-white flex items-center gap-1.5">
                  Trailer {tier.label}
                  {trailerIsHighlights && <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-bold tracking-wider">HIGHLIGHTS</span>}
                </p>
                <p className="text-[8px] text-gray-500 uppercase tracking-wide">{trailer.duration_seconds}s · {trailer.frames?.length || 0} frame · {trailer.views_count || 0} viste</p>
              </div>
            </div>
            {trailer.trending && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-400 font-bold">🔥 TRENDING</span>}
          </div>
          <button
            onClick={() => setShowPlayer(true)}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold flex items-center justify-center gap-2 hover:scale-[1.02] transition-transform"
            data-testid="trailer-watch-btn">
            <Play className="w-4 h-4 fill-black" /> Guarda Preview
          </button>
          {onConfirm && (
            <button
              onClick={onConfirm}
              className="mt-2 w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/40 text-emerald-300 font-bold flex items-center justify-center gap-2 hover:bg-emerald-500/30 transition-colors"
              data-testid="trailer-confirm-btn">
              <Check className="w-4 h-4" /> Conferma e prosegui
            </button>
          )}
          {canUpgrade && canGenerate && (
            <div className="mt-2 flex gap-1.5">
              {TIERS.filter(t => tierOrder[t.key] > tierOrder[trailer.tier]).map(t => {
                const delta = effectiveCost(t.cost) - effectiveCost(tier.cost);
                return (
                  <button key={t.key} onClick={() => handleGenerate(t.key)} className={`flex-1 py-1.5 rounded-lg border ${t.border} bg-white/[0.02] text-[9px] font-bold text-white hover:bg-white/[0.05]`} data-testid={`trailer-upgrade-${t.key}`}>
                    Upgrade → {t.label}<br/><span className="text-yellow-400">{delta > 0 ? `+${delta} cc` : 'GRATIS'}</span>
                  </button>
                );
              })}
            </div>
          )}
          {/* Offer a different-mode trailer below if available and not already created */}
          {canGenerate && !sameMode && (
            <div className={`mt-3 p-2 rounded-lg bg-black/30 border ${modeMeta.border}`}>
              <p className={`text-[9px] font-bold uppercase tracking-wider ${modeMeta.accentText} mb-1`}>
                Crea anche un {modeMeta.label}
              </p>
              <p className="text-[8px] text-gray-500">{modeMeta.subtitle}</p>
              <div className="grid grid-cols-3 gap-1.5 mt-1.5">
                {TIERS.map(t => {
                  const cost = effectiveCost(t.cost);
                  return (
                    <button key={t.key} onClick={() => handleGenerate(t.key)} className={`py-1.5 rounded-lg border ${t.border} bg-gradient-to-br ${t.color} text-[8px] font-bold text-white`}>
                      {t.label}<br/><span className="opacity-90">{cost === 0 ? 'GRATIS' : `${cost} cc`}</span>
                    </button>
                  );
                })}
              </div>
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

  const ModeIcon = modeMeta.icon;
  return (
    <div className={`rounded-2xl border ${modeMeta.border} bg-gradient-to-br ${modeMeta.bg} p-4`} data-testid="trailer-generator-card">
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${modeMeta.accent} flex items-center justify-center`}>
          <ModeIcon className="w-3.5 h-3.5 text-white" />
        </div>
        <div>
          <p className={`text-[12px] font-bold ${modeMeta.accentText} uppercase tracking-wider`}>{modeMeta.label}</p>
          <p className="text-[8px] text-gray-500">{modeMeta.subtitle}</p>
        </div>
      </div>
      <p className="text-[10px] text-gray-500 mb-3">
        {isReleased
          ? 'Il film è già uscito: non concede hype, ma è perfetto per social e archivio. Costo ridotto del 50%.'
          : 'Crea un trailer cinematografico con immagini AI coerenti. Non blocca la pipeline.'}
      </p>
      <div className="grid grid-cols-3 gap-2">
        {TIERS.map(t => {
          const Icon = t.icon;
          const cost = effectiveCost(t.cost);
          const canAfford = cost === 0 || userCredits >= cost;
          return (
            <button
              key={t.key}
              onClick={() => handleGenerate(t.key)}
              disabled={!canAfford}
              className={`p-2 rounded-xl border ${t.border} bg-gradient-to-br ${t.color} ${canAfford ? 'opacity-100' : 'opacity-40'} text-white flex flex-col items-center gap-1 hover:scale-[1.02] transition-transform disabled:cursor-not-allowed`}
              data-testid={`trailer-tier-${t.key}`}>
              <Icon className="w-4 h-4" />
              <span className="text-[10px] font-black uppercase">{t.label}</span>
              <span className="text-[8px] opacity-80">{t.duration}s · {t.frames} frame</span>
              <span className="text-[9px] font-bold bg-black/30 rounded-full px-2 py-0.5 mt-0.5">
                {isGuest && t.cost > 0 ? <><span className="line-through opacity-50 mr-1">{t.cost}</span><span className="text-emerald-300">GRATIS</span></> :
                 cost === 0 ? 'GRATIS' :
                 isReleased && t.cost > 0 ? <><span className="line-through opacity-50 mr-1">{t.cost}</span>{cost} cc</> : `${cost} cc`}
              </span>
              <span className="text-[7px] opacity-70">{isReleased ? 'post-lancio' : `+${t.hype}% hype`}</span>
            </button>
          );
        })}
      </div>
      <p className="text-[8px] text-gray-600 mt-2 text-center">
        {isReleased
          ? 'I trailer highlights non influenzano il gameplay: sono solo contenuto cosmetico.'
          : 'Hype bonus applicato solo se il contenuto è ancora in fase Hype/Pre-Rilascio.'}
      </p>
      {onSkip && (
        <button
          onClick={onSkip}
          className="mt-3 w-full py-2 rounded-xl border border-gray-700 bg-gray-900/50 text-gray-300 text-[11px] font-bold hover:bg-gray-800 flex items-center justify-center gap-2"
          data-testid="trailer-skip-btn">
          <SkipForward className="w-3.5 h-3.5" /> Salta trailer, prosegui
        </button>
      )}
    </div>
  );
}
