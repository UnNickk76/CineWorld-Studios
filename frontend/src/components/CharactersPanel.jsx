/**
 * CharactersPanel — lista personaggi generati dall'AI con:
 *   - Pulsante "Genera personaggi" (o "Rigenera")
 *   - Lista di slot con nome/età/ruolo/descrizione
 *   - Menu a tendina per abbinare un attore (solo quando `actors` è fornita)
 *     → gli attori fuori forbice d'età sono disabilitati (freezed)
 *
 * Props:
 *   kind:            'film_v3' | 'series_v3' | 'lampo'
 *   projectId:       string
 *   actors:          array | null   (null → modalità "sola lettura" per anime/animation)
 *   onToast:         fn(msg, type)
 *   onChange:        fn(chars)  → notificato quando il cast (assegnazioni) cambia
 *   readOnly:        bool (disabilita generazione/assegnazioni)
 *
 * Logica età: importata da `characterAgeUtils.js`.
 */
import React, { useEffect, useState, useMemo } from 'react';
import { Users, Sparkles, RefreshCw, Loader2, CheckCircle2, Wand2, Zap, X, Award } from 'lucide-react';
import { isActorCompatible, roleLabel, roleColor } from '../utils/characterAgeUtils';
import { useActorMatchScores, ActorMatchBadge, ActorPulseWrapper } from './saga/SagaActorMatch';

const API = process.env.REACT_APP_BACKEND_URL;

async function apiCall(path, method = 'GET', body = null) {
  const token = localStorage.getItem('cineworld_token');
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
  if (!res.ok) {
    const msg = typeof data.detail === 'string' ? data.detail : `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

export default function CharactersPanel({ kind, projectId, actors = null, onToast, onChange, readOnly = false, sagaId = null }) {
  const [chars, setChars] = useState([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [assigningId, setAssigningId] = useState(null);

  // carica personaggi all'avvio
  useEffect(() => {
    if (!projectId) return;
    let abort = false;
    setLoading(true);
    apiCall(`/api/characters/${kind}/${projectId}`)
      .then(d => { if (!abort) setChars(d.characters || []); })
      .catch(() => { if (!abort) setChars([]); })
      .finally(() => { if (!abort) setLoading(false); });
    return () => { abort = true; };
  }, [kind, projectId]);

  const generate = async (force = false) => {
    if (readOnly || busy) return;
    setBusy(true);
    try {
      const d = await apiCall(`/api/characters/${kind}/${projectId}/generate${force ? '?force=true' : ''}`, 'POST');
      setChars(d.characters || []);
      onChange && onChange(d.characters || []);
      onToast && onToast(d.cached ? 'Personaggi caricati' : `✨ ${d.characters.length} personaggi generati`);
    } catch (e) {
      onToast && onToast(e.message || 'Errore generazione personaggi', 'error');
    }
    setBusy(false);
  };

  const assignActor = async (char, actorId, actorName) => {
    if (readOnly) return;
    setAssigningId(char.id);
    try {
      const d = await apiCall(`/api/characters/${kind}/${projectId}/assign`, 'POST', {
        character_id: char.id, actor_id: actorId, actor_name: actorName,
      });
      setChars(d.characters || []);
      onChange && onChange(d.characters || []);
    } catch (e) {
      onToast && onToast(e.message || 'Errore assegnazione', 'error');
    }
    setAssigningId(null);
  };

  // ── Cast Suggerito (preview) ──
  const [suggestModal, setSuggestModal] = useState(null); // { suggestions:[], pool_size }
  const [suggestBusy, setSuggestBusy] = useState(false);

  const openSuggest = async () => {
    if (readOnly || actors === null || suggestBusy) return;
    setSuggestBusy(true);
    try {
      const payload = { actors: (actors || []).map(a => ({
        id: a.id, name: a.name, age: a.age, gender: a.gender,
        skill: a.skill, popularity: a.popularity, stars: a.stars,
        strong_genres: a.strong_genres,
      })), overwrite: false };
      const d = await apiCall(`/api/characters/${kind}/${projectId}/suggest-cast`, 'POST', payload);
      setSuggestModal(d);
    } catch (e) {
      onToast && onToast(e.message || 'Errore generazione suggerimenti', 'error');
    }
    setSuggestBusy(false);
  };

  const applySuggestions = async () => {
    if (!suggestModal) return;
    setSuggestBusy(true);
    try {
      const payload = { actors: (actors || []).map(a => ({
        id: a.id, name: a.name, age: a.age, gender: a.gender,
        skill: a.skill, popularity: a.popularity, stars: a.stars,
        strong_genres: a.strong_genres,
      })), overwrite: false };
      const d = await apiCall(`/api/characters/${kind}/${projectId}/auto-complete-cast`, 'POST', payload);
      setChars(d.characters || []);
      onChange && onChange(d.characters || []);
      setSuggestModal(null);
      onToast && onToast(`✨ Cast applicato: ${d.assigned}/${d.total} personaggi`);
    } catch (e) {
      onToast && onToast(e.message || 'Errore applicazione cast', 'error');
    }
    setSuggestBusy(false);
  };

  const autoCompleteAll = async () => {
    if (readOnly || actors === null || suggestBusy) return;
    setSuggestBusy(true);
    try {
      const payload = { actors: (actors || []).map(a => ({
        id: a.id, name: a.name, age: a.age, gender: a.gender,
        skill: a.skill, popularity: a.popularity, stars: a.stars,
        strong_genres: a.strong_genres,
      })), overwrite: true };
      const d = await apiCall(`/api/characters/${kind}/${projectId}/auto-complete-cast`, 'POST', payload);
      setChars(d.characters || []);
      onChange && onChange(d.characters || []);
      onToast && onToast(`⚡ Cast completato: ${d.assigned}/${d.total} (${d.no_match || 0} senza match età)`);
    } catch (e) {
      onToast && onToast(e.message || 'Errore auto-completa', 'error');
    }
    setSuggestBusy(false);
  };

  // Statistiche slot
  const stats = useMemo(() => {
    const total = chars.length;
    const assigned = chars.filter(c => c.assigned_actor_id).length;
    const hasProtagonist = chars.some(c => c.role_type === 'protagonist' && c.assigned_actor_id);
    return { total, assigned, hasProtagonist };
  }, [chars]);

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500 text-xs flex items-center justify-center gap-2">
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Caricamento personaggi…
      </div>
    );
  }

  // Empty state
  if (!chars.length) {
    return (
      <div className="p-4 rounded-xl border border-dashed border-purple-500/30 bg-purple-500/5" data-testid="characters-panel-empty">
        <div className="flex items-center gap-2 mb-2">
          <Users className="w-4 h-4 text-purple-400" />
          <h3 className="text-xs font-bold text-purple-200">Personaggi dell'opera</h3>
        </div>
        <p className="text-[10px] text-gray-400 mb-3">
          L'AI creerà da 5 a 20 personaggi coerenti con la trama: nomi, età, ruolo di importanza e descrizione.
          {actors !== null && ' Poi potrai assegnare gli attori.'}
        </p>
        <button
          onClick={() => generate(false)}
          disabled={busy || readOnly}
          className="w-full px-3 py-2 rounded-lg bg-purple-500/20 border border-purple-500/50 text-purple-200 text-xs font-bold disabled:opacity-50 active:scale-95 transition-all flex items-center justify-center gap-2"
          data-testid="generate-characters-btn"
        >
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          {busy ? 'Generazione in corso…' : 'Genera personaggi (AI)'}
        </button>
      </div>
    );
  }

  // Lista personaggi
  return (
    <div className="rounded-xl border border-purple-500/20 bg-gradient-to-br from-purple-950/20 to-gray-900/50 overflow-hidden" data-testid="characters-panel">
      <div className="px-3 py-2 border-b border-purple-500/10 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Users className="w-3.5 h-3.5 text-purple-400" />
          <h3 className="text-[11px] font-bold text-purple-200 uppercase tracking-wider">
            Personaggi ({chars.length})
          </h3>
          {actors !== null && (
            <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
              stats.hasProtagonist && stats.assigned >= 5
                ? 'bg-emerald-500/20 text-emerald-300'
                : 'bg-amber-500/20 text-amber-300'
            }`}>
              {stats.assigned}/{stats.total} assegnati
            </span>
          )}
        </div>
        {!readOnly && (
          <button
            onClick={() => generate(true)}
            disabled={busy}
            className="text-[10px] text-gray-400 hover:text-purple-300 flex items-center gap-1 disabled:opacity-50"
            data-testid="regenerate-characters-btn"
            title="Rigenera personaggi"
          >
            {busy ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
            Rigenera
          </button>
        )}
      </div>

      {/* Pulsanti AI Cast (solo se attori disponibili) */}
      {actors !== null && !readOnly && (
        <div className="px-3 py-2 grid grid-cols-2 gap-2 border-b border-purple-500/10 bg-black/20">
          <button
            onClick={openSuggest}
            disabled={suggestBusy || !chars.length}
            className="px-2 py-1.5 rounded-lg bg-cyan-500/15 border border-cyan-500/40 text-cyan-200 text-[10px] font-bold disabled:opacity-50 active:scale-95 transition-all flex items-center justify-center gap-1"
            data-testid="suggest-cast-btn"
            title="L'AI propone gli attori migliori, tu confermi"
          >
            {suggestBusy ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wand2 className="w-3 h-3" />}
            Suggerisci Cast AI
          </button>
          <button
            onClick={autoCompleteAll}
            disabled={suggestBusy || !chars.length}
            className="px-2 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/40 text-amber-200 text-[10px] font-bold disabled:opacity-50 active:scale-95 transition-all flex items-center justify-center gap-1"
            data-testid="auto-complete-cast-btn"
            title={`Assegna automaticamente tutti i ${chars.length} personaggi`}
          >
            {suggestBusy ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
            Completa Cast Auto
          </button>
        </div>
      )}

      <ul className="divide-y divide-purple-500/10">
        {chars.map(c => (
          <CharacterRow
            key={c.id}
            char={c}
            actors={actors}
            readOnly={readOnly}
            assigning={assigningId === c.id}
            onAssign={(actorId, actorName) => assignActor(c, actorId, actorName)}
            sagaId={sagaId}
            projectId={projectId}
          />
        ))}
      </ul>

      {actors !== null && !stats.hasProtagonist && stats.total > 0 && (
        <div className="px-3 py-2 bg-amber-500/10 border-t border-amber-500/30 text-[10px] text-amber-300">
          ⚠️ Assegna un attore al personaggio protagonista per avanzare.
        </div>
      )}

      {/* Modale preview suggerimenti */}
      {suggestModal && (
        <div className="fixed inset-0 z-[70] bg-black/85 backdrop-blur-sm flex items-end sm:items-center justify-center p-3" onClick={() => !suggestBusy && setSuggestModal(null)}>
          <div className="w-full max-w-md max-h-[85vh] rounded-2xl border border-cyan-500/40 bg-gradient-to-br from-cyan-950/70 to-gray-900/95 flex flex-col overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="px-4 py-3 flex items-center justify-between border-b border-cyan-500/20 shrink-0">
              <div className="flex items-center gap-2">
                <Wand2 className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-cyan-200">Cast Suggerito AI</h3>
              </div>
              <button onClick={() => !suggestBusy && setSuggestModal(null)} disabled={suggestBusy} className="text-gray-400 hover:text-white" data-testid="suggest-close">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="px-4 py-2 text-[10px] text-gray-400 border-b border-cyan-500/10 shrink-0">
              Pool di {suggestModal.actors_pool_size} attori. I personaggi senza match d'età non vengono assegnati.
            </div>
            <ul className="flex-1 overflow-y-auto divide-y divide-cyan-500/10">
              {suggestModal.suggestions.map(s => (
                <li key={s.character_id} className="px-4 py-2 flex items-center gap-2" data-testid={`suggest-row-${s.character_id}`}>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-bold text-white truncate">{s.character_name}</p>
                    {s.actor_name ? (
                      <p className="text-[10px] text-cyan-300 truncate">→ {s.actor_name} {s.kept ? '(già assegnato)' : ''}</p>
                    ) : (
                      <p className="text-[10px] text-red-400">— Nessun attore compatibile</p>
                    )}
                  </div>
                  {s.score !== null && s.score !== undefined && (
                    <span className="text-[9px] text-gray-500 shrink-0">score {s.score}</span>
                  )}
                </li>
              ))}
            </ul>
            <div className="grid grid-cols-2 gap-2 p-3 border-t border-cyan-500/20 shrink-0">
              <button onClick={() => setSuggestModal(null)} disabled={suggestBusy}
                className="px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-gray-200 text-xs font-bold disabled:opacity-50"
                data-testid="suggest-cancel">
                Annulla
              </button>
              <button onClick={applySuggestions} disabled={suggestBusy}
                className="px-3 py-2 rounded-lg bg-cyan-500/30 border border-cyan-500/60 text-cyan-100 text-xs font-bold disabled:opacity-50 flex items-center justify-center gap-1"
                data-testid="suggest-apply">
                {suggestBusy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                Applica
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function CharacterRow({ char, actors, readOnly, assigning, onAssign, sagaId, projectId }) {
  const [open, setOpen] = useState(false);
  const assigned = char.assigned_actor_id;
  const color = roleColor(char.role_type);
  const matchData = useActorMatchScores({ sagaId, characterId: char.id, projectId });
  const top3 = (matchData.matches || []).slice(0, 3);

  // Filtra attori compatibili per età; incompatibili compaiono DISABILITATI
  const actorOptions = useMemo(() => {
    if (!actors) return [];
    return actors.map(a => ({
      ...a,
      compatible: isActorCompatible(char.age, a.age),
    })).sort((a, b) => {
      // Compatibili prima, poi per nome
      if (a.compatible !== b.compatible) return a.compatible ? -1 : 1;
      return (a.name || '').localeCompare(b.name || '');
    });
  }, [actors, char.age]);

  return (
    <li className="px-3 py-2 flex items-center gap-2" data-testid={`character-row-${char.id}`}>
      <div className={`w-1 h-10 rounded-full ${color.bar}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-bold text-white truncate">{char.name}</span>
          <span className={`text-[8px] font-bold uppercase px-1.5 py-0.5 rounded-full ${color.chip}`}>
            {roleLabel(char.role_type)}
          </span>
          <span className="text-[9px] text-gray-500">
            {char.gender === 'F' ? '♀' : char.gender === 'M' ? '♂' : '◯'} {char.age}a
          </span>
        </div>
        {char.description && (
          <p className="text-[9px] text-gray-400 mt-0.5 leading-tight line-clamp-2">{char.description}</p>
        )}
        {/* Top 3 chip suggerimenti attori (saga capitoli successivi) */}
        {!assigned && !readOnly && actors !== null && top3.length > 0 && (
          <div className="mt-1.5 flex items-center gap-1 flex-wrap" data-testid={`saga-top3-${char.id}`}>
            <span className="text-[8px] uppercase tracking-wider text-amber-400 font-bold">✨ Top match:</span>
            {top3.map((m, i) => {
              const a = (actors || []).find(x => x.id === m.actor_id);
              if (!a) return null;
              const compat = isActorCompatible(char.age, a.age);
              return (
                <ActorPulseWrapper key={m.actor_id} active={i === 0}>
                  <button
                    onClick={() => compat && onAssign(a.id, a.name)}
                    disabled={!compat}
                    title={m.reason}
                    data-testid={`saga-top-${char.id}-${m.actor_id}`}
                    className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold whitespace-nowrap border ${i === 0 ? 'bg-amber-500/20 border-amber-400/60 text-amber-200' : 'bg-zinc-800 border-zinc-700 text-zinc-200'} ${!compat ? 'opacity-40 cursor-not-allowed' : 'hover:scale-105'} transition-transform`}
                  >
                    {m.actor_name} <span className="opacity-60">{m.match_score}%</span>
                    {m.is_saga_vet && <Award className="w-2.5 h-2.5 inline ml-0.5" />}
                  </button>
                </ActorPulseWrapper>
              );
            })}
          </div>
        )}
        {/* Menu a tendina attore (solo se actors presente) */}
        {actors !== null && (
          <div className="mt-1.5">
            {assigned ? (
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                <span className="text-[10px] text-emerald-300 font-semibold truncate">
                  {char.assigned_actor_name || 'Attore assegnato'}
                </span>
                {!readOnly && (
                  <button
                    onClick={() => onAssign(null, null)}
                    className="text-[9px] text-gray-500 hover:text-red-400 ml-auto"
                    data-testid={`unassign-${char.id}`}
                  >
                    rimuovi
                  </button>
                )}
              </div>
            ) : (
              <select
                value=""
                disabled={readOnly || assigning}
                onChange={(e) => {
                  const v = e.target.value;
                  if (!v) return;
                  const act = actorOptions.find(a => a.id === v);
                  if (act && act.compatible) onAssign(act.id, act.name);
                }}
                className="w-full text-[10px] px-2 py-1 rounded bg-black/40 border border-gray-700 text-gray-200 disabled:opacity-50"
                data-testid={`assign-select-${char.id}`}
              >
                <option value="">
                  {assigning ? 'Assegnazione…' : 'Scegli attore per questo personaggio…'}
                </option>
                {actorOptions.map(a => (
                  <option
                    key={a.id}
                    value={a.id}
                    disabled={!a.compatible}
                    style={!a.compatible ? { color: '#666' } : {}}
                  >
                    {a.compatible ? '' : '🔒 '}
                    {a.name} ({a.age}a) {a.compatible ? '' : '— fuori età'}
                  </option>
                ))}
              </select>
            )}
          </div>
        )}
      </div>
    </li>
  );
}
