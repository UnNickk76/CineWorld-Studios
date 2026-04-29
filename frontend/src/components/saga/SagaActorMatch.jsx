import React, { useEffect, useState, useContext } from 'react';
import { AuthContext } from '../../contexts';
import { Sparkles, Award } from 'lucide-react';
import { toast } from 'sonner';

/**
 * Hook che ritorna la mappa actor_id → match info per un personaggio in un capitolo saga.
 * Usato per il pulse oro Top 3 + tooltip.
 */
export function useActorMatchScores({ sagaId, characterId, projectId }) {
  const { api } = useContext(AuthContext);
  const [data, setData] = useState({ matches: [], saga_actor_ids: [], topIds: new Set() });

  useEffect(() => {
    if (!sagaId || !characterId) return;
    let abort = false;
    api.get(`/sagas/${sagaId}/actor-matches`, { params: { character_id: characterId, project_id: projectId } })
      .then(r => {
        if (abort) return;
        const matches = r.data?.matches || [];
        const topIds = new Set(matches.slice(0, 3).map(m => m.actor_id));
        setData({ matches, saga_actor_ids: r.data?.saga_actor_ids || [], topIds });
      })
      .catch(() => { /* silent */ });
    return () => { abort = true; };
  }, [sagaId, characterId, projectId, api]);

  const getMatch = (actorId) => data.matches.find(m => m.actor_id === actorId);
  const isTop3 = (actorId) => data.topIds.has(actorId);
  const isSagaVet = (actorId) => data.saga_actor_ids.includes(actorId);
  return { ...data, getMatch, isTop3, isSagaVet };
}

/**
 * Badge match% + Saga Vet. — visibile sotto/accanto al nome attore.
 */
export function ActorMatchBadge({ matchScore, reason, isSagaVet, isTop3 }) {
  if (matchScore == null && !isSagaVet) return null;
  const color = matchScore >= 85 ? 'text-amber-300' : matchScore >= 70 ? 'text-cyan-300' : 'text-zinc-400';
  return (
    <div className="flex items-center gap-1 flex-wrap" title={reason}>
      {matchScore != null && (
        <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-wider ${color} bg-black/40 border ${isTop3 ? 'border-amber-400/60' : 'border-white/10'}`} data-testid="actor-match-badge">
          <Sparkles size={8} /> {matchScore}%
        </span>
      )}
      {isSagaVet && (
        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-wider bg-amber-500/15 border border-amber-500/40 text-amber-300" data-testid="saga-vet-badge" title="Già nel cast di un capitolo precedente della saga">
          <Award size={8} /> Saga Vet.
        </span>
      )}
    </div>
  );
}

/**
 * Wrapper CSS pulse oro per il Top 3 attori matchati.
 * Avvolge un attore card con animazione gold pulse.
 */
export function ActorPulseWrapper({ active, children }) {
  if (!active) return children;
  return (
    <>
      <style>{`
        @keyframes goldPulseRing { 0%, 100% { box-shadow: 0 0 0 0 rgba(250,204,21,0.55), 0 0 14px rgba(250,204,21,0.35); } 50% { box-shadow: 0 0 0 4px rgba(250,204,21,0.0), 0 0 22px rgba(250,204,21,0.55); } }
        .actor-gold-pulse { animation: goldPulseRing 1.8s ease-in-out infinite; border-radius: 12px; }
      `}</style>
      <div className="actor-gold-pulse" data-testid="actor-gold-pulse">{children}</div>
    </>
  );
}
