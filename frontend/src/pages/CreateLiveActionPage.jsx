/**
 * CreateLiveActionPage — sblocca/elenca le origini eligibili e permette di
 * creare un live-action (V3 classico o LAMPO) da un film d'animazione o anime.
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Camera, Lock, Sparkles, Loader2, Star, Zap, Film } from 'lucide-react';

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

export default function CreateLiveActionPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [unlocked, setUnlocked] = useState(false);
  const [requirements, setRequirements] = useState(null);
  const [origins, setOrigins] = useState([]);
  const [selected, setSelected] = useState(null);
  const [creating, setCreating] = useState(false);
  const [titleOverride, setTitleOverride] = useState('');
  const [subgenreOverride, setSubgenreOverride] = useState('');
  const [mode, setMode] = useState('classic');
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const d = await apiCall('/api/live-action/eligible-origins');
        setUnlocked(d.unlocked);
        setRequirements(d.requirements);
        setOrigins(d.origins || []);
      } catch (e) {
        setError(e.message || 'Errore caricamento');
      }
      setLoading(false);
    };
    load();
  }, []);

  const startCreation = async () => {
    if (!selected) return;
    setCreating(true);
    setError(null);
    try {
      const body = {
        origin_id: selected.id,
        origin_kind: selected.kind,
        mode,
      };
      if (titleOverride.trim()) body.title = titleOverride.trim();
      if (!selected.subgenre && subgenreOverride.trim()) body.subgenre = subgenreOverride.trim();
      const d = await apiCall('/api/live-action/create', 'POST', body);
      // naviga alla pipeline col nuovo progetto
      navigate(`/pipeline-v3?p=${d.project.id}`);
    } catch (e) {
      setError(e.message || 'Errore creazione');
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-pink-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white pb-28" data-testid="create-live-action-page">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-black/95 backdrop-blur-sm border-b border-pink-500/20">
        <div className="flex items-center gap-2 px-3 py-3 pt-safe">
          <button onClick={() => navigate(-1)} className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center" data-testid="back-btn">
            <ChevronLeft className="w-4 h-4 text-gray-400" />
          </button>
          <div className="flex items-center gap-2">
            <Camera className="w-4 h-4 text-pink-400" />
            <h1 className="text-sm font-bold text-pink-200 uppercase tracking-wider">Live Action</h1>
          </div>
        </div>
      </div>

      <div className="px-4 pt-20">
        <p className="text-xs text-gray-400 mb-4 leading-relaxed">
          Trasforma i tuoi <strong className="text-amber-300">film d'animazione</strong> e <strong className="text-purple-300">anime</strong> in un
          <strong className="text-pink-300"> live-action cinematografico</strong>. I personaggi originali saranno pre-popolati e dovrai assegnare gli attori.
        </p>

        {/* Stato sblocco */}
        {!unlocked && requirements && (
          <RequirementsBox req={requirements} />
        )}

        {unlocked && origins.length === 0 && (
          <div className="p-4 rounded-xl border border-dashed border-gray-700 bg-gray-900/30 text-center">
            <Film className="w-8 h-8 text-gray-600 mx-auto mb-2" />
            <p className="text-xs text-gray-400">
              Nessuna opera eligibile al momento.
            </p>
            <p className="text-[10px] text-gray-500 mt-1">
              Servono film d'animazione o anime di tua proprietà usciti da almeno <strong>15 giorni reali</strong>, senza un live-action già prodotto.
            </p>
          </div>
        )}

        {unlocked && origins.length > 0 && (
          <>
            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-2">
              Opere eligibili ({origins.length})
            </p>
            <div className="grid grid-cols-2 gap-3">
              {origins.map(o => (
                <button key={o.id}
                  onClick={() => { setSelected(o); setTitleOverride(`${o.title} — Live Action`); setSubgenreOverride(o.subgenre || ''); }}
                  className={`text-left rounded-xl border-2 p-2 transition-all active:scale-95 ${
                    selected?.id === o.id ? 'border-pink-500 bg-pink-500/10' : 'border-gray-800 bg-gray-900/40 hover:border-pink-500/40'
                  }`}
                  data-testid={`origin-card-${o.id}`}
                >
                  <div className="aspect-[2/3] rounded-lg bg-gray-800 overflow-hidden mb-2 relative">
                    {o.poster_url ? (
                      <img src={o.poster_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Film className="w-8 h-8 text-gray-700" />
                      </div>
                    )}
                    <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded-full bg-black/80 text-[8px] font-bold uppercase">
                      {o.kind === 'anime' ? <span className="text-purple-300">Anime</span> : <span className="text-amber-300">Animaz.</span>}
                    </div>
                    {o.is_lampo && (
                      <div className="absolute top-1 right-1 px-1 py-0.5 rounded-full bg-amber-500/90 text-black text-[7px] font-black">⚡</div>
                    )}
                  </div>
                  <p className="text-[10px] font-bold text-white truncate">{o.title}</p>
                  <div className="flex items-center gap-2 mt-1 text-[8px] text-gray-400">
                    <span className="flex items-center gap-0.5"><Star className="w-2.5 h-2.5 text-yellow-400" />{o.cwsv.toFixed(1)}</span>
                    <span>•</span>
                    <span>{o.days_since_release}gg</span>
                    {o.spectators > 0 && (<><span>•</span><span>{(o.spectators / 1000).toFixed(0)}k</span></>)}
                  </div>
                </button>
              ))}
            </div>
          </>
        )}

        {/* Modale di conferma */}
        {selected && (
          <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-end sm:items-center justify-center p-4" onClick={() => !creating && setSelected(null)}>
            <div className="w-full max-w-md rounded-2xl border border-pink-500/40 bg-gradient-to-br from-pink-950/70 to-gray-900/95 p-5" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center gap-2 mb-3">
                <Camera className="w-5 h-5 text-pink-400" />
                <h2 className="text-sm font-bold text-pink-200">Crea Live Action</h2>
              </div>
              <p className="text-[11px] text-gray-300 mb-3">
                Da <strong>{selected.title}</strong> ({selected.kind === 'anime' ? 'anime' : 'animazione'})
              </p>

              <label className="text-[10px] text-gray-400 font-bold uppercase">Titolo</label>
              <input
                type="text"
                value={titleOverride}
                onChange={(e) => setTitleOverride(e.target.value)}
                disabled={creating}
                maxLength={120}
                className="w-full text-xs px-3 py-2 rounded-lg bg-black/40 border border-gray-700 text-white mt-1 mb-3"
                data-testid="la-title-input"
              />

              {!selected.subgenre && (
                <>
                  <label className="text-[10px] text-gray-400 font-bold uppercase">Sotto-genere (opzionale)</label>
                  <input
                    type="text"
                    value={subgenreOverride}
                    onChange={(e) => setSubgenreOverride(e.target.value)}
                    disabled={creating}
                    placeholder="L'origine non aveva sottogenere — opzionale"
                    className="w-full text-xs px-3 py-2 rounded-lg bg-black/40 border border-gray-700 text-white mt-1 mb-3"
                    data-testid="la-subgenre-input"
                  />
                </>
              )}

              <label className="text-[10px] text-gray-400 font-bold uppercase">Modalità di produzione</label>
              <div className="grid grid-cols-2 gap-2 mt-1 mb-3">
                <button
                  onClick={() => setMode('classic')}
                  disabled={creating}
                  className={`px-3 py-2 rounded-lg border text-xs font-bold ${mode === 'classic' ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-200' : 'bg-gray-900 border-gray-700 text-gray-400'}`}
                  data-testid="mode-classic"
                >
                  Pipeline V3
                </button>
                <button
                  onClick={() => setMode('lampo')}
                  disabled={creating}
                  className={`px-3 py-2 rounded-lg border text-xs font-bold flex items-center justify-center gap-1 ${mode === 'lampo' ? 'bg-amber-500/20 border-amber-500/50 text-amber-200' : 'bg-gray-900 border-gray-700 text-gray-400'}`}
                  data-testid="mode-lampo"
                >
                  <Zap className="w-3 h-3" /> LAMPO
                </button>
              </div>

              <div className="rounded-lg bg-black/40 border border-pink-500/20 p-3 text-[10px] text-gray-400 mb-3">
                <p>📺 Genere ereditato: <strong className="text-white">{selected.genre}</strong></p>
                <p>👥 Personaggi pre-popolati dall'opera origine</p>
                <p>⚡ Bonus hype iniziale: + (CWSv × 8) + (spettatori / 100k)</p>
              </div>

              {error && (
                <div className="text-[11px] text-red-300 bg-red-500/10 border border-red-500/30 p-2 rounded-lg mb-3" data-testid="la-error">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => { setSelected(null); setError(null); }}
                  disabled={creating}
                  className="px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-gray-200 text-xs font-bold disabled:opacity-50"
                  data-testid="la-cancel"
                >
                  Annulla
                </button>
                <button
                  onClick={startCreation}
                  disabled={creating || !titleOverride.trim()}
                  className="px-3 py-2 rounded-lg bg-pink-500/30 border border-pink-500/60 text-pink-100 text-xs font-bold disabled:opacity-50 flex items-center justify-center gap-1"
                  data-testid="la-confirm"
                >
                  {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                  {creating ? 'Creazione…' : 'Crea Live Action'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function RequirementsBox({ req }) {
  const items = [
    { label: `Livello Player ≥ ${req.req_player_level}`, ok: req.player_level >= req.req_player_level, current: req.player_level },
    { label: `Fama ≥ ${req.req_fame}`, ok: req.fame >= req.req_fame, current: req.fame },
    { label: `Studio Anime o Production Studio Lv ${req.req_studio_level}`, ok: req.studio_anime_level >= req.req_studio_level || req.production_studio_level >= req.req_studio_level, current: `Anime ${req.studio_anime_level} / Prod ${req.production_studio_level}` },
  ];
  return (
    <div className="rounded-xl border border-pink-500/30 bg-pink-500/5 p-4 mb-4" data-testid="la-requirements">
      <div className="flex items-center gap-2 mb-3">
        <Lock className="w-4 h-4 text-pink-400" />
        <h3 className="text-xs font-bold text-pink-200">Requisiti per sbloccare il Live Action</h3>
      </div>
      <ul className="space-y-2">
        {items.map((it, i) => (
          <li key={i} className="flex items-start gap-2 text-[11px]">
            <span className={`w-4 h-4 shrink-0 rounded-full flex items-center justify-center font-bold text-[9px] ${it.ok ? 'bg-emerald-500/30 text-emerald-200' : 'bg-gray-700 text-gray-400'}`}>
              {it.ok ? '✓' : '✗'}
            </span>
            <div className="flex-1">
              <p className={it.ok ? 'text-emerald-300' : 'text-gray-300'}>{it.label}</p>
              <p className="text-[9px] text-gray-500">Attuale: {it.current}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
