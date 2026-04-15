import React, { useState, useEffect } from 'react';
import { Users, Star, Zap, X, BarChart3 } from 'lucide-react';
import { PhaseWrapper, v3api } from './V3Shared';

const CAST_TABS = [
  { id: 'directors', label: 'Registi', max: 1 },
  { id: 'screenwriters', label: 'Scenegg.', max: 3 },
  { id: 'actors', label: 'Attori', max: 5 },
  { id: 'composers', label: 'Compositori', max: 1 },
];

const ACTOR_ROLES = ['generico','protagonista','antagonista','co protagonista','supporto'];
const ROLE_DISPLAY = { 'generico': 'generico', 'protagonista': 'protagonista', 'antagonista': 'antagonista', 'co protagonista': 'Co Protagonista', 'co_protagonista': 'Co Protagonista', 'supporto': 'supporto' };

function SkillsModal({ npc, onClose }) {
  if (!npc) return null;
  const skills = npc.skills || {};
  const primary = npc.primary_skills || [];
  const entries = Object.entries(skills).filter(([, v]) => v != null);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 mx-4 max-w-sm w-full space-y-3" onClick={e => e.stopPropagation()} data-testid="skills-modal">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold text-white">{npc.name}</h4>
          <button onClick={onClose} className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center"><X className="w-3 h-3 text-gray-400" /></button>
        </div>
        <div className="flex items-center gap-2 text-[8px] text-gray-500">
          <span>{npc.nationality}</span>
          <span>|</span>
          <span>{npc.age || '?'} anni</span>
          <span>|</span>
          <span className="text-amber-400">{npc.fame_category || ''}</span>
          <span>|</span>
          <div className="flex items-center gap-0.5">
            {Array.from({ length: npc.stars || 1 }).map((_, i) => <Star key={i} className="w-2 h-2 text-yellow-400 fill-yellow-400" />)}
          </div>
        </div>
        {primary.length > 0 && (
          <div>
            <p className="text-[7px] text-gray-500 uppercase font-bold mb-1">Specialita</p>
            <div className="flex flex-wrap gap-1">
              {primary.map(s => <span key={s} className="text-[8px] px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-bold">{s}</span>)}
            </div>
          </div>
        )}
        {entries.length > 0 ? (
          <div>
            <p className="text-[7px] text-gray-500 uppercase font-bold mb-1">Skills</p>
            <div className="space-y-1.5">
              {entries.map(([key, val]) => {
                const num = typeof val === 'number' ? val : (typeof val === 'object' ? val.level || val.value || 0 : 0);
                const pct = Math.min(100, Math.max(0, num));
                return (
                  <div key={key}>
                    <div className="flex justify-between text-[8px] mb-0.5">
                      <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="text-white font-bold">{num}</span>
                    </div>
                    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-gradient-to-r from-cyan-600 to-emerald-400" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <p className="text-[9px] text-gray-600 text-center py-2">Nessuna skill dettagliata disponibile</p>
        )}
      </div>
    </div>
  );
}

const NpcCard = ({ npc, selected, onSelect, castRole, onRoleChange, onNameClick }) => {
  const colors = ['#F59E0B','#3B82F6','#EF4444','#10B981','#A855F7','#F97316','#06B6D4'];
  const bgColor = colors[((npc.name || '').charCodeAt(0) + (npc.name || '').length) % colors.length];
  return (
    <div className={`w-full flex items-center gap-2 p-2 rounded-lg border text-left transition-all ${
      selected ? 'bg-cyan-500/10 border-cyan-500/40' : 'bg-gray-800/30 border-gray-700 hover:border-gray-600'
    }`}>
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-black shrink-0" style={{ background: bgColor }}>
        {(npc.name || '?')[0]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1">
          <button onClick={(e) => { e.stopPropagation(); onNameClick?.(npc); }} className="text-[9px] font-bold text-white truncate hover:text-cyan-400 transition-colors underline decoration-dotted decoration-gray-600 underline-offset-2">{npc.name}</button>
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
          {ACTOR_ROLES.map(r => <option key={r} value={r}>{ROLE_DISPLAY[r] || r}</option>)}
        </select>
      )}
      {castRole === undefined && (
        <button onClick={onSelect} disabled={selected}
          className={`text-[7px] px-2 py-1 rounded-lg font-bold shrink-0 ${
            selected ? 'bg-gray-800 text-gray-600' : 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20'
          }`}>{selected ? 'OK' : '+'}</button>
      )}
      {castRole !== undefined && !selected && (
        <button onClick={onSelect} disabled={selected}
          className="text-[7px] px-2 py-1 rounded-lg font-bold shrink-0 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20">+</button>
      )}
    </div>
  );
};

export const CastPhase = ({ film, onRefresh, toast }) => {
  const [tab, setTab] = useState('directors');
  const [proposals, setProposals] = useState({});
  const [loading, setLoading] = useState(false);
  const [actorRoles, setActorRoles] = useState({});
  const [skillNpc, setSkillNpc] = useState(null);
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

  const roleDisplay = (r) => ROLE_DISPLAY[r] || (r || 'generico').replace(/_/g, ' ');

  return (
    <PhaseWrapper title="Il Cast" subtitle="Assembla la tua squadra" icon={Users} color="cyan">
      <div className="space-y-3">
        {skillNpc && <SkillsModal npc={skillNpc} onClose={() => setSkillNpc(null)} />}

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
            <p className="text-[8px] font-bold text-white">{(cast.screenwriters || []).length}/3</p>
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

        {/* Selected Cast */}
        {(cast.actors || []).length > 0 && (
          <div className="space-y-1">
            <p className="text-[7px] text-gray-500 uppercase font-bold">Cast selezionato</p>
            {(cast.actors || []).map((a, i) => (
              <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-cyan-500/5 border border-cyan-500/15">
                <button onClick={() => setSkillNpc(a)} className="text-[8px] font-bold text-cyan-400 hover:text-cyan-300 underline decoration-dotted underline-offset-2">{a.name}</button>
                <span className="text-[7px] text-gray-500">({roleDisplay(a.cast_role)})</span>
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
            const role = actorRoles[npc.id] || 'generico';
            return (
              <NpcCard key={npc.id} npc={npc} selected={sel}
                castRole={tab === 'actors' ? role : undefined}
                onRoleChange={(r) => setActorRoles(prev => ({ ...prev, [npc.id]: r }))}
                onNameClick={(n) => setSkillNpc(n)}
                onSelect={() => !sel && !isFull && selectMember(npc, tab === 'directors' ? 'director' : tab === 'screenwriters' ? 'screenwriter' : tab === 'composers' ? 'composer' : 'actor', tab === 'actors' ? (actorRoles[npc.id] || 'generico') : undefined)} />
            );
          })}
        </div>
      </div>
    </PhaseWrapper>
  );
};
