import React, { useState, useEffect } from 'react';
import { Users, Star, Zap } from 'lucide-react';
import { PhaseWrapper, v3api } from './V3Shared';

const CAST_TABS = [
  { id: 'directors', label: 'Registi', max: 1 },
  { id: 'screenwriters', label: 'Scenegg.', max: 3 },
  { id: 'actors', label: 'Attori', max: 5 },
  { id: 'composers', label: 'Compositori', max: 1 },
];

const ACTOR_ROLES = ['protagonista','antagonista','co_protagonista','supporto','generico'];

const NpcCard = ({ npc, selected, onSelect, castRole, onRoleChange }) => {
  const colors = ['#F59E0B','#3B82F6','#EF4444','#10B981','#A855F7','#F97316','#06B6D4'];
  const bgColor = colors[((npc.name || '').charCodeAt(0) + (npc.name || '').length) % colors.length];
  return (
    <button onClick={onSelect}
      className={`w-full flex items-center gap-2 p-2 rounded-lg border text-left transition-all ${
        selected ? 'bg-cyan-500/10 border-cyan-500/40' : 'bg-gray-800/30 border-gray-700 hover:border-gray-600'
      }`}>
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-black shrink-0" style={{ background: bgColor }}>
        {(npc.name || '?')[0]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1">
          <span className="text-[9px] font-bold text-white truncate">{npc.name}</span>
          {npc.fame_category && <span className="text-[6px] px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 font-bold">{npc.fame_category}</span>}
        </div>
        <p className="text-[7px] text-gray-500">{npc.nationality} | {npc.age || '?'} anni | ${(npc.cost || 0).toLocaleString()}</p>
        <div className="flex items-center gap-0.5 mt-0.5">
          {Array.from({ length: npc.stars || 1 }).map((_, i) => <Star key={i} className="w-2 h-2 text-yellow-400 fill-yellow-400" />)}
        </div>
      </div>
      {castRole !== undefined && (
        <select value={castRole} onClick={e => e.stopPropagation()} onChange={e => onRoleChange?.(e.target.value)}
          className="text-[7px] rounded bg-gray-900 border border-gray-700 px-1 py-0.5 text-gray-300">
          {ACTOR_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
      )}
    </button>
  );
};

export const CastPhase = ({ film, onRefresh, toast }) => {
  const [tab, setTab] = useState('directors');
  const [proposals, setProposals] = useState({});
  const [loading, setLoading] = useState(false);
  const cast = film.cast || { director: null, screenwriters: [], actors: [], composer: null };

  useEffect(() => {
    v3api(`/films/${film.id}/cast-proposals`).then(setProposals).catch(() => {});
  }, [film.id]);

  const selectMember = async (npc, role, castRole) => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/select-cast-member`, 'POST', { npc_id: npc.id, role, cast_role: castRole || 'generico' });
      await onRefresh(); toast?.(`${npc.name} aggiunto al cast!`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const autoCast = async () => {
    setLoading(true);
    try { await v3api(`/films/${film.id}/auto-cast`, 'POST'); await onRefresh(); toast?.('Cast auto completato!'); }
    catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const selectedIds = new Set([
    cast.director?.id, cast.composer?.id,
    ...(cast.screenwriters || []).map(s => s.id),
    ...(cast.actors || []).map(a => a.id),
  ].filter(Boolean));

  const currentTab = CAST_TABS.find(t => t.id === tab);
  const tabItems = proposals[tab] || [];
  const currentCount = tab === 'directors' ? (cast.director ? 1 : 0) :
    tab === 'composers' ? (cast.composer ? 1 : 0) :
    tab === 'screenwriters' ? (cast.screenwriters || []).length :
    (cast.actors || []).length;
  const maxCount = currentTab?.max || 5;
  const isFull = currentCount >= maxCount;

  return (
    <PhaseWrapper title="Il Cast" subtitle="Assembla la tua squadra" icon={Users} color="cyan">
      <div className="space-y-3">
        {/* Auto Cast */}
        <button onClick={autoCast} disabled={loading}
          className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[9px] font-bold hover:bg-cyan-500/15 disabled:opacity-30" data-testid="auto-cast-btn">
          <Zap className="w-3 h-3" /> Completa Cast Auto
        </button>

        {/* Current Cast Summary */}
        <div className="grid grid-cols-4 gap-1.5">
          <div className="p-1.5 rounded-lg bg-gray-800/30 border border-gray-700/30 text-center">
            <p className="text-[7px] text-gray-500">Regista</p>
            <p className="text-[8px] font-bold text-white truncate">{cast.director?.name || '—'}</p>
          </div>
          <div className="p-1.5 rounded-lg bg-gray-800/30 border border-gray-700/30 text-center">
            <p className="text-[7px] text-gray-500">Scenegg.</p>
            <p className="text-[8px] font-bold text-white">{(cast.screenwriters || []).length}/1</p>
          </div>
          <div className="p-1.5 rounded-lg bg-gray-800/30 border border-gray-700/30 text-center">
            <p className="text-[7px] text-gray-500">Attori</p>
            <p className="text-[8px] font-bold text-white">{(cast.actors || []).length}/5</p>
          </div>
          <div className="p-1.5 rounded-lg bg-gray-800/30 border border-gray-700/30 text-center">
            <p className="text-[7px] text-gray-500">Compos.</p>
            <p className="text-[8px] font-bold text-white truncate">{cast.composer?.name || '—'}</p>
          </div>
        </div>

        {/* Selected Actors */}
        {(cast.actors || []).length > 0 && (
          <div className="space-y-1">
            <p className="text-[7px] text-gray-500 uppercase font-bold">Cast selezionato</p>
            {(cast.actors || []).map((a, i) => (
              <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-cyan-500/5 border border-cyan-500/15">
                <span className="text-[8px] font-bold text-cyan-400">{a.name}</span>
                <span className="text-[7px] text-gray-500">({a.cast_role || 'generico'})</span>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1">
          {CAST_TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex-1 py-1.5 rounded-lg text-[8px] font-bold border ${
                tab === t.id ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'border-gray-800 text-gray-500'
              }`}>{t.label}</button>
          ))}
        </div>

        {/* NPC List */}
        <p className="text-[7px] text-gray-500">{currentTab?.label} disponibili ({tabItems.length}) {isFull && <span className="text-amber-400">— Slot pieno</span>}</p>
        <div className="space-y-1.5 max-h-64 overflow-y-auto">
          {tabItems.map(npc => {
            const sel = selectedIds.has(npc.id);
            return (
              <NpcCard key={npc.id} npc={npc} selected={sel}
                castRole={tab === 'actors' ? 'protagonista' : undefined}
                onSelect={() => !sel && !isFull && selectMember(npc, tab === 'directors' ? 'director' : tab === 'screenwriters' ? 'screenwriter' : tab === 'composers' ? 'composer' : 'actor', tab === 'actors' ? 'protagonista' : undefined)} />
            );
          })}
        </div>
      </div>
    </PhaseWrapper>
  );
};
