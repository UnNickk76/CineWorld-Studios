import React, { useState, useEffect } from 'react';
import { Users, Star, Zap, X, Lock, Unlock, GraduationCap, Briefcase } from 'lucide-react';
import { PhaseWrapper, v3api } from './V3Shared';

const CAST_TABS = [
  { id: 'directors', label: 'Registi', max: 1 },
  { id: 'screenwriters', label: 'Scenegg.', max: 3 },
  { id: 'actors', label: 'Attori', max: 999 },
  { id: 'composers', label: 'Compositori', max: 1 },
];

const ACTOR_ROLES = ['generico','protagonista','antagonista','co protagonista','supporto'];
const ROLE_DISPLAY = { 'generico': 'generico', 'protagonista': 'protagonista', 'antagonista': 'antagonista', 'co protagonista': 'Co Protagonista', 'co_protagonista': 'Co Protagonista', 'supporto': 'supporto' };

const GENDER_SYMBOL = { male: '♂', female: '♀', nonbinary: '⚧', other: '⚧' };
const GENDER_COLOR = { male: 'text-blue-400', female: 'text-pink-400', nonbinary: 'text-purple-400', other: 'text-purple-400' };

function SkillsModal({ npc, onClose }) {
  if (!npc) return null;
  const skills = npc.skills || {};
  const primary = npc.primary_skills || [];
  const entries = Object.entries(skills).filter(([, v]) => v != null).sort((a, b) => b[1] - a[1]);
  // Show exactly 8 (pad with empty if less, truncate if more)
  const displayEntries = entries.slice(0, 8);
  const lowestEntry = displayEntries.length > 0 ? displayEntries[displayEntries.length - 1] : null;
  const gender = npc.gender || '';
  const gSymbol = GENDER_SYMBOL[gender] || '';
  const gColor = GENDER_COLOR[gender] || 'text-gray-400';
  const crc = npc.crc ?? 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 mx-4 max-w-sm w-full space-y-3 max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()} data-testid="skills-modal">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-bold text-white">{npc.name}</h4>
            {gSymbol && <span className={`text-base ${gColor}`}>{gSymbol}</span>}
            <span className={`text-[8px] px-1.5 py-0.5 rounded font-black border ${
              crc >= 80 ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25' :
              crc >= 60 ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25' :
              crc >= 40 ? 'bg-amber-500/15 text-amber-400 border-amber-500/25' :
              'bg-red-500/15 text-red-400 border-red-500/25'
            }`} data-testid="crc-badge">CRc {crc}</span>
          </div>
          <button onClick={onClose} className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center"><X className="w-3 h-3 text-gray-400" /></button>
        </div>
        <div className="flex items-center gap-2 text-[8px] text-gray-500 flex-wrap">
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

        {/* Specialita (2 primary skills) */}
        {primary.length > 0 && (
          <div>
            <p className="text-[7px] text-gray-500 uppercase font-bold mb-1">Specialita</p>
            <div className="flex flex-wrap gap-1">
              {primary.map(s => <span key={s} className="text-[8px] px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-bold">{s.replace(/_/g, ' ')}</span>)}
            </div>
          </div>
        )}

        {/* Weakness (lowest skill) */}
        {lowestEntry && (
          <div>
            <p className="text-[7px] text-gray-500 uppercase font-bold mb-1">Debolezza</p>
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-red-500/10 border border-red-500/20 text-red-400 font-bold">{lowestEntry[0].replace(/_/g, ' ')} ({lowestEntry[1]})</span>
          </div>
        )}

        {/* All 8 Skills */}
        {displayEntries.length > 0 && (
          <div>
            <p className="text-[7px] text-gray-500 uppercase font-bold mb-1">Skills ({displayEntries.length})</p>
            <div className="space-y-1.5">
              {displayEntries.map(([key, val]) => {
                const num = typeof val === 'number' ? val : 0;
                const pct = Math.min(100, Math.max(0, num));
                const isPrimary = primary.includes(key);
                const isWeakness = lowestEntry && lowestEntry[0] === key;
                const barColor = isWeakness ? 'from-red-600 to-red-400' : isPrimary ? 'from-yellow-500 to-amber-300' : 'from-cyan-600 to-emerald-400';
                return (
                  <div key={key}>
                    <div className="flex justify-between text-[8px] mb-0.5">
                      <span className={`capitalize ${isWeakness ? 'text-red-400' : isPrimary ? 'text-yellow-400' : 'text-gray-400'}`}>
                        {key.replace(/_/g, ' ')} {isPrimary ? '\u2605' : ''}{isWeakness ? '\u25BC' : ''}
                      </span>
                      <span className="text-white font-bold">{num}</span>
                    </div>
                    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full bg-gradient-to-r ${barColor}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const NpcCard = ({ npc, selected, onSelect, castRole, onRoleChange, onNameClick }) => {
  const colors = ['#F59E0B','#3B82F6','#EF4444','#10B981','#A855F7','#F97316','#06B6D4'];
  const bgColor = colors[((npc.name || '').charCodeAt(0) + (npc.name || '').length) % colors.length];
  const gender = npc.gender || '';
  const gSymbol = GENDER_SYMBOL[gender] || '';
  const gColor = GENDER_COLOR[gender] || '';
  const crc = npc.crc ?? 0;
  return (
    <div className={`w-full flex items-center gap-2 p-2 rounded-lg border text-left transition-all ${
      selected ? 'bg-cyan-500/10 border-cyan-500/40' : 'bg-gray-800/30 border-gray-700 hover:border-gray-600'
    }`}>
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-black shrink-0" style={{ background: bgColor }}>
        {(npc.name || '?')[0]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1 flex-wrap">
          <button onClick={(e) => { e.stopPropagation(); onNameClick?.(npc); }} className="text-[9px] font-bold text-white truncate hover:text-cyan-400 transition-colors underline decoration-dotted decoration-gray-600 underline-offset-2">{npc.name}</button>
          {gSymbol && <span className={`text-[10px] ${gColor}`}>{gSymbol}</span>}
          {npc.fame_category && <span className="text-[6px] px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 font-bold">{npc.fame_category}</span>}
          <span className={`text-[6px] px-1 py-0.5 rounded font-black border ${
            crc >= 80 ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25' :
            crc >= 60 ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25' :
            crc >= 40 ? 'bg-amber-500/15 text-amber-400 border-amber-500/25' :
            'bg-red-500/15 text-red-400 border-red-500/25'
          }`}>CRc {crc}</span>
        </div>
        <p className="text-[7px] text-gray-500">{npc.nationality} | {npc.age || '?'} anni | ${(npc.cost || npc.cost_per_film || 0).toLocaleString()}</p>
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

function UnlockAgenciesPanel({ filmId, toast, onBack }) {
  const [agencies, setAgencies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [unlockCost, setUnlockCost] = useState(5);

  useEffect(() => {
    v3api('/preferred-agencies').then(d => {
      setAgencies(d.agencies || []);
      setUnlockCost(d.unlock_cost_cp || 5);
    }).catch(() => {});
  }, []);

  const unlock = async (agencyId) => {
    setLoading(true);
    try {
      const res = await v3api('/unlock-agency', 'POST', { agency_id: agencyId });
      toast?.(res.message || 'Sbloccata!');
      // Refresh
      const d = await v3api('/preferred-agencies');
      setAgencies(d.agencies || []);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-[9px] font-bold text-amber-400">Agenzie Partner</p>
        <button onClick={onBack} className="text-[7px] text-gray-500 hover:text-gray-300 underline">Torna alle proposte</button>
      </div>
      <p className="text-[7px] text-gray-500">Sblocca agenzie come partner per ricevere cast migliori (3+ stelle), pi&ugrave; proposte e -10% sui costi. Costa {unlockCost} CinePass.</p>
      <div className="space-y-1 max-h-64 overflow-y-auto">
        {agencies.map(ag => (
          <div key={ag.id} className={`flex items-center gap-2 p-2 rounded-lg border ${
            ag.is_preferred ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-gray-800/30 border-gray-700 hover:border-amber-500/30'
          }`}>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1">
                <span className="text-[9px] font-bold text-white">{ag.name}</span>
                {ag.is_preferred && <Unlock className="w-2.5 h-2.5 text-emerald-400" />}
              </div>
              <p className="text-[7px] text-gray-500">{ag.region} | Rep {ag.reputation} | {(ag.specialization || []).join(', ')}</p>
            </div>
            {ag.is_preferred ? (
              <span className="text-[7px] px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 font-bold">Partner</span>
            ) : (
              <button onClick={() => unlock(ag.id)} disabled={loading}
                className="text-[7px] px-2 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 font-bold hover:bg-amber-500/20 disabled:opacity-30">
                <Lock className="w-2.5 h-2.5 inline mr-0.5" /> {unlockCost} CP
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}



export const CastPhase = ({ film, onRefresh, toast }) => {
  const [tab, setTab] = useState('directors');
  const [proposals, setProposals] = useState({});
  const [agencyActors, setAgencyActors] = useState([]);
  const [agencyInfo, setAgencyInfo] = useState(null);
  const [npcAgencies, setNpcAgencies] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actorRoles, setActorRoles] = useState({});
  const [skillNpc, setSkillNpc] = useState(null);
  const [castSource, setCastSource] = useState('pool'); // 'pool' | 'agency' | 'npc_agencies'
  const cast = film.cast || { director: null, screenwriters: [], actors: [], composer: null };

  useEffect(() => {
    v3api(`/films/${film.id}/cast-proposals`).then(setProposals).catch(() => {});
    v3api(`/films/${film.id}/my-agency-actors`).then(d => {
      setAgencyActors(d.actors || []);
      setAgencyInfo(d);
    }).catch(() => {});
    v3api(`/films/${film.id}/npc-agency-proposals`).then(setNpcAgencies).catch(() => {});
  }, [film.id]);

  const selectMember = async (npc, role, castRole) => {
    setLoading(true);
    try {
      await v3api(`/films/${film.id}/select-cast-member`, 'POST', { npc_id: npc.id, role, cast_role: castRole || 'generico' });
      await onRefresh(); toast?.(`${npc.name} aggiunto al cast!`);
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading(false);
  };

  const castAgencyActor = async (actor, role, castRole) => {
    setLoading(true);
    try {
      const res = await v3api(`/films/${film.id}/cast-agency-actor`, 'POST', {
        actor_id: actor.id, role, cast_role: castRole || 'generico', source: actor.source || 'agency'
      });
      await onRefresh();
      toast?.(res.message || `${actor.name} aggiunto!`);
      // Refresh agency list
      v3api(`/films/${film.id}/my-agency-actors`).then(d => setAgencyActors(d.actors || [])).catch(() => {});
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

  // Filter agency actors that aren't already cast
  const availableAgency = agencyActors.filter(a => !a.already_cast && !selectedIds.has(a.id));
  const npcProposals = (npcAgencies?.proposals || []).filter(p => !selectedIds.has(p.id));

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
            <p className="text-[8px] font-bold text-white truncate">{cast.director?.name || '\u2014'}</p>
          </div>
          <div className="p-1.5 rounded-lg bg-gray-800/30 border border-gray-700/30 text-center">
            <p className="text-[7px] text-gray-500">Scenegg.</p>
            <p className="text-[8px] font-bold text-white">{(cast.screenwriters || []).length}/3</p>
          </div>
          <div className="p-1.5 rounded-lg bg-gray-800/30 border border-gray-700/30 text-center">
            <p className="text-[7px] text-gray-500">Attori</p>
            <p className="text-[8px] font-bold text-white">{(cast.actors || []).length}</p>
          </div>
          <div className="p-1.5 rounded-lg bg-gray-800/30 border border-gray-700/30 text-center">
            <p className="text-[7px] text-gray-500">Compos.</p>
            <p className="text-[8px] font-bold text-white truncate">{cast.composer?.name || '\u2014'}</p>
          </div>
        </div>

        {/* Selected Cast */}
        {(cast.actors || []).length > 0 && (
          <div className="space-y-1">
            <p className="text-[7px] text-gray-500 uppercase font-bold">Cast selezionato</p>
            {(cast.actors || []).map((a, i) => (
              <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-cyan-500/5 border border-cyan-500/15">
                <button onClick={() => setSkillNpc(a)} className="text-[8px] font-bold text-cyan-400 hover:text-cyan-300 underline decoration-dotted underline-offset-2">{a.name}</button>
                {a.gender && GENDER_SYMBOL[a.gender] && <span className={`text-[9px] ${GENDER_COLOR[a.gender] || ''}`}>{GENDER_SYMBOL[a.gender]}</span>}
                <span className="text-[7px] text-gray-500">({roleDisplay(a.cast_role)})</span>
                {a.is_own_roster && a.own_source === 'school' && <span className="text-[6px] px-1 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold flex items-center gap-0.5"><GraduationCap className="w-2 h-2" />Scuola</span>}
                {a.is_own_roster && a.own_source === 'agency' && <span className="text-[6px] px-1 py-0.5 rounded bg-purple-500/15 text-purple-300 border border-purple-500/30 font-bold flex items-center gap-0.5"><Briefcase className="w-2 h-2" />Mia Agenzia</span>}
                {a.is_agency_actor && !a.is_own_roster && <span className="text-[6px] px-1 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-bold">Agenzia</span>}
                {a.is_returning && <span className="text-[6px] px-1 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">Ritorno</span>}
              </div>
            ))}
          </div>
        )}

        {/* Chemistry Pairs */}
        {film.chemistry_pairs && film.chemistry_pairs.length > 0 && (
          <div className="px-2 py-1.5 rounded-lg bg-emerald-500/5 border border-emerald-500/15 space-y-1">
            <p className="text-[7px] text-emerald-400 uppercase font-bold">Chimica Cast (+CWSv)</p>
            {film.chemistry_pairs.map((pair, i) => (
              <div key={i} className="flex items-center gap-1 text-[7px]">
                <span className="text-emerald-300 font-bold">{pair.a}</span>
                <span className="text-gray-600">&</span>
                <span className="text-emerald-300 font-bold">{pair.b}</span>
                <span className="text-gray-600">({pair.count} film insieme)</span>
              </div>
            ))}
            <p className="text-[6px] text-emerald-500/60">+{Math.min(3, film.chemistry_pairs.length * 0.5).toFixed(1)}% bonus CWSv</p>
          </div>
        )}

        {/* Source Selector: Pool / La Mia Agenzia / Agenzie NPC */}
        <div className="flex gap-1">
          <button onClick={() => setCastSource('pool')}
            className={`flex-1 py-1.5 rounded-lg text-[8px] font-bold border ${
              castSource === 'pool' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'border-gray-800 text-gray-500'
            }`}>Mercato</button>
          <button onClick={() => setCastSource('agency')}
            className={`flex-1 py-1.5 rounded-lg text-[8px] font-bold border ${
              castSource === 'agency' ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' : 'border-gray-800 text-gray-500'
            }`}>La Mia Agenzia {availableAgency.length > 0 ? `(${availableAgency.length})` : ''}</button>
          <button onClick={() => setCastSource('npc_agencies')}
            className={`flex-1 py-1.5 rounded-lg text-[8px] font-bold border ${
              castSource === 'npc_agencies' ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' : 'border-gray-800 text-gray-500'
            }`}>Agenzie ({npcAgencies?.num_agencies || 0})</button>
        </div>

        {/* === SOURCE: POOL (original cast-proposals) === */}
        {castSource === 'pool' && (
          <>
            <div className="flex gap-1">
              {CAST_TABS.map(t => (
                <button key={t.id} onClick={() => setTab(t.id)}
                  className={`flex-1 py-1.5 rounded-lg text-[8px] font-bold border ${
                    tab === t.id ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'border-gray-800 text-gray-500'
                  }`}>{t.label}</button>
              ))}
            </div>
            <p className="text-[7px] text-gray-500">{currentTab?.label} disponibili ({tabItems.length}) {isFull && <span className="text-amber-400">\u2014 Slot pieno</span>}</p>
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
          </>
        )}

        {/* === SOURCE: MY AGENCY === */}
        {castSource === 'agency' && (
          <div className="space-y-3">
            {agencyInfo && (
              <div className="px-2 py-1.5 rounded-lg bg-purple-500/5 border border-purple-500/15">
                <p className="text-[9px] font-bold text-purple-300">{agencyInfo.agency_name}</p>
                <p className="text-[7px] text-gray-500">Lv.{agencyInfo.agency_level} • {agencyInfo.total} attori propri • <span className="text-emerald-400 font-bold">Costo $0</span></p>
                <p className="text-[6px] text-emerald-300/70 mt-0.5">+XP e bonus CWSv all'uscita del film (proporzionale a stelle/numero attori propri)</p>
              </div>
            )}
            {availableAgency.length === 0 ? (
              <p className="text-center text-[8px] text-gray-600 py-4">Nessun attore disponibile. Recluta dalla pagina Agenzia o forma in Scuola di Recitazione!</p>
            ) : (
              <>
                {/* Group by source: school vs agency */}
                {[
                  { key: 'school', label: 'Scuola di Recitazione', icon: GraduationCap, color: 'emerald', tint: 'bg-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/40', avatarBg: 'bg-emerald-500/20 text-emerald-300', btnCls: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20' },
                  { key: 'agency', label: 'La Mia Agenzia', icon: Briefcase, color: 'purple', tint: 'bg-purple-500/5 border-purple-500/20 hover:border-purple-500/40', avatarBg: 'bg-purple-500/20 text-purple-300', btnCls: 'bg-purple-500/10 border-purple-500/20 text-purple-400 hover:bg-purple-500/20' },
                ].map(group => {
                  const items = availableAgency.filter(a => (a.source || 'agency') === group.key);
                  if (items.length === 0) return null;
                  const Icon = group.icon;
                  return (
                    <div key={group.key} className="space-y-1.5">
                      <div className="flex items-center gap-1.5">
                        <Icon className={`w-3 h-3 text-${group.color}-400`} />
                        <p className={`text-[8px] font-bold text-${group.color}-300 uppercase tracking-wider`}>{group.label}</p>
                        <span className={`text-[7px] text-${group.color}-400/70`}>({items.length})</span>
                      </div>
                      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        {items.map(actor => (
                          <div key={actor.id} className={`w-full flex items-center gap-2 p-2 rounded-lg border text-left transition-all ${group.tint}`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${group.avatarBg}`}>
                              {(actor.name || '?')[0]}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1 flex-wrap">
                                <button onClick={() => setSkillNpc(actor)} className={`text-[9px] font-bold text-white truncate hover:text-${group.color}-400 underline decoration-dotted underline-offset-2`}>{actor.name}</button>
                                {actor.gender && GENDER_SYMBOL[actor.gender] && <span className={`text-[10px] ${GENDER_COLOR[actor.gender] || ''}`}>{GENDER_SYMBOL[actor.gender]}</span>}
                                <span className={`text-[6px] px-1 py-0.5 rounded font-black border ${
                                  actor.crc >= 80 ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25' :
                                  actor.crc >= 60 ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25' :
                                  'bg-amber-500/15 text-amber-400 border-amber-500/25'
                                }`}>CRc {actor.crc}</span>
                              </div>
                              <div className="flex items-center gap-1 mt-0.5 text-[7px]">
                                <span className="text-gray-500">{actor.nationality}</span>
                                <span className="text-gray-700">•</span>
                                <span className="text-emerald-400 font-bold">GRATIS</span>
                              </div>
                              <div className="flex items-center gap-0.5 mt-0.5">
                                {Array.from({ length: actor.stars || 1 }).map((_, i) => <Star key={i} className="w-2 h-2 text-yellow-400 fill-yellow-400" />)}
                              </div>
                            </div>
                            <button onClick={() => !isFull && castAgencyActor(actor, 'actor', actorRoles[actor.id] || 'generico')} disabled={loading || isFull}
                              className={`text-[7px] px-2 py-1 rounded-lg font-bold shrink-0 border ${group.btnCls} disabled:opacity-30`} data-testid={`cast-own-${actor.id}`}>+</button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </>
            )}
          </div>
        )}

        {/* === SOURCE: NPC AGENCIES === */}
        {castSource === 'npc_agencies' && (
          <div className="space-y-2">
            {/* Agency badges with lock/unlock */}
            {npcAgencies?.agencies && (
              <div className="flex flex-wrap gap-1">
                {npcAgencies.agencies.map((ag, i) => (
                  <span key={i} className={`text-[7px] px-1.5 py-0.5 rounded font-bold flex items-center gap-0.5 ${
                    ag.is_exclusive
                      ? 'bg-yellow-500/15 border border-yellow-500/25 text-yellow-400'
                      : ag.is_preferred
                      ? 'bg-emerald-500/15 border border-emerald-500/25 text-emerald-400'
                      : 'bg-amber-500/10 border border-amber-500/20 text-amber-400'
                  }`}>
                    {ag.is_exclusive ? <Unlock className="w-2 h-2" /> : ag.is_preferred ? <Unlock className="w-2 h-2" /> : <Lock className="w-2 h-2 opacity-50" />}
                    {ag.name} {ag.is_exclusive ? '\u2B50' : ag.is_preferred ? '\u2605' : ''} Rep {ag.reputation}
                  </span>
                ))}
              </div>
            )}
            {/* Unlock button */}
            <button onClick={() => setCastSource('unlock_agencies')}
              className="w-full text-[8px] py-1.5 rounded-lg border border-dashed border-amber-500/30 text-amber-400/70 hover:text-amber-400 hover:border-amber-500/50 font-bold">
              <Lock className="w-3 h-3 inline mr-1" /> Gestisci Agenzie Partner (CinePass)
            </button>
            {npcProposals.length === 0 ? (
              <p className="text-center text-[8px] text-gray-600 py-4">Nessuna proposta dalle agenzie.</p>
            ) : (
              <div className="space-y-1.5 max-h-64 overflow-y-auto">
                {npcProposals.map(npc => {
                  const sel = selectedIds.has(npc.id);
                  const isExcActor = npc.is_exclusive_actor;
                  return (
                    <div key={npc.id} className={`w-full flex items-center gap-2 p-2 rounded-lg border text-left transition-all ${
                      isExcActor ? 'bg-yellow-500/10 border-yellow-500/30 ring-1 ring-yellow-500/20' :
                      npc.is_exclusive ? 'bg-amber-500/8 border-amber-500/25' :
                      'bg-amber-500/5 border-amber-500/15 hover:border-amber-500/30'
                    }`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                        isExcActor ? 'bg-yellow-500/25 text-yellow-300' : 'bg-amber-500/15 text-amber-300'
                      }`}>
                        {(npc.name || '?')[0]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1 flex-wrap">
                          <button onClick={() => setSkillNpc(npc)} className="text-[9px] font-bold text-white truncate hover:text-amber-400 underline decoration-dotted underline-offset-2">{npc.name}</button>
                          {npc.gender && GENDER_SYMBOL[npc.gender] && <span className={`text-[10px] ${GENDER_COLOR[npc.gender] || ''}`}>{GENDER_SYMBOL[npc.gender]}</span>}
                          <span className={`text-[6px] px-1 py-0.5 rounded font-black border ${
                            npc.crc >= 80 ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25' :
                            npc.crc >= 60 ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25' :
                            'bg-amber-500/15 text-amber-400 border-amber-500/25'
                          }`}>CRc {npc.crc}</span>
                          <span className="text-[6px] px-1 py-0.5 rounded bg-gray-800 text-gray-400 font-bold">{npc.role_type}</span>
                          {isExcActor && <span className="text-[6px] px-1 py-0.5 rounded bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 font-black">ESCLUSIVO</span>}
                          {npc.is_exclusive && !isExcActor && <span className="text-[5px] px-1 py-0.5 rounded bg-yellow-500/10 text-yellow-500/70 font-bold">Contratto</span>}
                        </div>
                        <p className="text-[7px] text-gray-500">
                          {npc.nationality} | {npc.cost === 0 ? <span className="text-yellow-400 font-bold">GRATIS</span> : `$${(npc.cost || 0).toLocaleString()}`} | {npc.agency_name}
                        </p>
                        <div className="flex items-center gap-0.5 mt-0.5">
                          {Array.from({ length: npc.stars || 1 }).map((_, i) => <Star key={i} className="w-2 h-2 text-yellow-400 fill-yellow-400" />)}
                        </div>
                      </div>
                      <button onClick={() => !sel && !isFull && selectMember(npc, npc.role_type === 'director' ? 'director' : npc.role_type === 'screenwriter' ? 'screenwriter' : npc.role_type === 'composer' ? 'composer' : 'actor', npc.role_type === 'actor' ? 'generico' : undefined)}
                        disabled={sel || loading || isFull}
                        className={`text-[7px] px-2 py-1 rounded-lg font-bold shrink-0 ${sel ? 'bg-gray-800 text-gray-600' : 'bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20'} disabled:opacity-30`}>
                        {sel ? 'OK' : '+'}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* === SOURCE: UNLOCK AGENCIES === */}
        {castSource === 'unlock_agencies' && (
          <UnlockAgenciesPanel filmId={film.id} toast={toast} onBack={() => {
            setCastSource('npc_agencies');
            v3api(`/films/${film.id}/npc-agency-proposals`).then(setNpcAgencies).catch(() => {});
          }} />
        )}
      </div>
    </PhaseWrapper>
  );
};
