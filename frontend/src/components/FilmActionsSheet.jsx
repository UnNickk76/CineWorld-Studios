// CineWorld Studio's — Film Actions Sheet
// Unified bottom-sheet menu for film actions. Opens via window event `open-film-actions`.
// Includes: View, ADV, Regen Poster, Ritira Cinema, Vendi, Elimina, and La Mia TV (Subito/Prossimamente).

import React, { useState, useEffect, useCallback, useContext } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthContext } from '../contexts';
import {
  Eye, Megaphone, Wand2, ChevronDown, Store, Trash2, X,
  Tv, Zap, Clock, Film as FilmIcon, Loader2, AlertTriangle,
  TrendingDown, TrendingUp, Minus, Info, Play, Lock, Building2
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API}${url}`;
};

/**
 * Global helper to open the sheet from anywhere:
 *   window.dispatchEvent(new CustomEvent('open-film-actions', { detail: { film } }))
 */
export function openFilmActions(film) {
  window.dispatchEvent(new CustomEvent('open-film-actions', { detail: { film } }));
}

export default function FilmActionsSheet() {
  const { api, user, refreshUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [film, setFilm] = useState(null);
  const [tvSection, setTvSection] = useState(false); // show La mia TV panel
  const [stations, setStations] = useState([]);
  const [stationsLoading, setStationsLoading] = useState(false);
  const [stationsLoaded, setStationsLoaded] = useState(false);
  const [pickStation, setPickStation] = useState(null); // station selected for scheduling
  const [delayHours, setDelayHours] = useState(24);
  const [actionLoading, setActionLoading] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmSell, setConfirmSell] = useState(false);
  const [confirmWithdraw, setConfirmWithdraw] = useState(false);
  const [trailer, setTrailer] = useState(null);
  const [trailerLoading, setTrailerLoading] = useState(false);

  // Listener
  useEffect(() => {
    const handler = (e) => {
      const f = e.detail?.film;
      if (!f) return;
      // Safety: only open for films owned by the user
      if (f.user_id && user?.id && f.user_id !== user.id) {
        // Not owned → navigate to detail instead
        navigate(`/films/${f.id}`);
        return;
      }
      setFilm(f);
      setTvSection(false);
      setPickStation(null);
      setDelayHours(24);
      setStationsLoaded(false);
      setStations([]);
      // fetch trailer status (non-blocking)
      setTrailer(null);
      setTrailerLoading(true);
      api.get(`/trailers/${f.id}`).then(r => setTrailer(r.data?.trailer || null)).catch(() => setTrailer(null)).finally(() => setTrailerLoading(false));
    };
    window.addEventListener('open-film-actions', handler);
    return () => window.removeEventListener('open-film-actions', handler);
  }, [user?.id, navigate]);

  const close = useCallback(() => {
    setFilm(null);
    setTvSection(false);
    setPickStation(null);
  }, []);

  // Load stations on demand
  const loadStations = useCallback(async () => {
    setStationsLoading(true);
    try {
      const r = await api.get('/my-owned-tv-stations');
      setStations(r.data?.stations || []);
    } catch {
      setStations([]);
    }
    setStationsLoaded(true);
    setStationsLoading(false);
  }, [api]);

  useEffect(() => {
    if (tvSection && !stationsLoaded && !stationsLoading) loadStations();
  }, [tvSection, stationsLoaded, stationsLoading, loadStations]);

  if (!film) return null;

  const isInTheaters = film.status === 'in_theaters';

  // ─── Actions ───
  const handleView = () => { navigate(`/films/${film.id}`); close(); };
  const handleAdv = () => { navigate(`/films/${film.id}?panel=adv`); close(); };

  const handleRegenPoster = async () => {
    setActionLoading('regen');
    try {
      const r = await api.post(`/films/${film.id}/regenerate-poster`, {});
      if (r.data?.task_id) {
        toast.info('Rigenerazione locandina avviata...');
      } else {
        toast.success('Richiesta inviata');
      }
      close();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const handleWithdraw = async () => {
    setActionLoading('withdraw');
    try {
      await api.delete(`/films/${film.id}`);
      toast.success('Film ritirato dalle sale');
      window.dispatchEvent(new Event('film-actions-updated'));
      close();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const handleSell = async () => {
    setActionLoading('sell');
    try {
      await api.post(`/pipeline-v3/films/${film.source_project_id || film.id}/discard-to-market`);
      toast.success('Film messo in vendita!');
      window.dispatchEvent(new Event('film-actions-updated'));
      close();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore vendita'); }
    setActionLoading(null);
  };

  const handleDelete = async () => {
    setActionLoading('delete');
    try {
      await api.delete(`/films/${film.id}/permanent`);
      toast.success('Film eliminato');
      window.dispatchEvent(new Event('film-actions-updated'));
      close();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const handleTransferNow = async (station) => {
    setActionLoading(`tv-now-${station.id}`);
    try {
      const r = await api.post('/tv-stations/transfer-from-cinema', {
        film_id: film.id,
        station_id: station.id,
        mode: 'subito',
      });
      const bonus = r.data?.hype_bonus || 0;
      toast.success(r.data?.message || 'Trasferito in TV!', {
        description: bonus > 0 ? `+${bonus} hype bonus per il calo al cinema` : undefined,
        duration: 5000,
      });
      if (refreshUser) refreshUser();
      window.dispatchEvent(new Event('film-actions-updated'));
      close();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore trasferimento'); }
    setActionLoading(null);
  };

  const handleTransferScheduled = async (station, hours) => {
    setActionLoading(`tv-sched-${station.id}`);
    try {
      const r = await api.post('/tv-stations/transfer-from-cinema', {
        film_id: film.id,
        station_id: station.id,
        mode: 'prossimamente',
        delay_hours: hours,
      });
      toast.success(r.data?.message || 'Programmato in TV!');
      if (refreshUser) refreshUser();
      window.dispatchEvent(new Event('film-actions-updated'));
      close();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  return createPortal(
    <AnimatePresence>
      {film && (
        <motion.div
          key="backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
          onClick={close}
          className="fixed inset-0 z-[140] flex items-end justify-center"
          style={{ background: 'radial-gradient(ellipse at bottom, rgba(0,0,0,0.82) 0%, rgba(0,0,0,0.92) 70%)' }}
          data-testid="film-actions-sheet-backdrop"
        >
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', stiffness: 320, damping: 32 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md bg-gradient-to-b from-[#15100c] via-[#0d0a08] to-[#0a0708] border-t border-amber-500/20 rounded-t-3xl shadow-[0_-8px_40px_rgba(212,175,55,0.18)] overflow-hidden"
            style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
            data-testid="film-actions-sheet"
          >
            {/* Grip bar */}
            <div className="flex justify-center pt-2 pb-1">
              <div className="w-10 h-1 rounded-full bg-amber-500/40" />
            </div>

            {/* Header */}
            <div className="px-4 pt-1 pb-3 flex items-center gap-3 border-b border-amber-500/10">
              <div className="w-12 h-16 rounded-md overflow-hidden flex-shrink-0 bg-black border border-amber-500/20 shadow-[0_0_14px_rgba(212,175,55,0.15)]">
                {posterSrc(film.poster_url) ? (
                  <img src={posterSrc(film.poster_url)} alt={film.title} className="w-full h-full object-cover" />
                ) : <div className="w-full h-full flex items-center justify-center"><FilmIcon className="w-5 h-5 text-amber-500/50" /></div>}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[9px] text-amber-400/70 tracking-[0.2em] font-semibold uppercase">Azioni Film</p>
                <h3 className="text-base font-bold text-white leading-tight truncate">{film.title}</h3>
                <p className="text-[10px] text-gray-400 truncate">
                  {film.genre ? `${film.genre}` : ''}{isInTheaters ? ' · AL CINEMA' : ''}
                </p>
              </div>
              <button onClick={close} className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-gray-400 active:scale-90 transition-transform" data-testid="film-actions-close">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Body: main menu or La Mia TV panel */}
            {!tvSection ? (
              <div className="p-3 space-y-1 max-h-[65vh] overflow-y-auto">
                {/* Trailer banner — nascosto per progetti LAMPO (no trailer) */}
                {!film.is_lampo && film.mode !== 'lampo' && (
                  <TrailerBanner film={film} trailer={trailer} trailerLoading={trailerLoading} onGo={() => {
                    const pid = film.source_project_id || film.id;
                    navigate(`/create-film?p=${pid}`);
                    close();
                  }} />
                )}
                <ActionRow icon={<Eye className="w-4 h-4" />} color="text-cyan-400" label="Dettaglio Film" hint="Pipeline, stats, locandina" onClick={handleView} testId="fa-view" />
                {isInTheaters && (
                  <ActionRow icon={<Megaphone className="w-4 h-4" />} color="text-yellow-400" label="Campagna ADV" hint="Promuovi il film al cinema" onClick={handleAdv} testId="fa-adv" />
                )}
                <ActionRow icon={<Wand2 className="w-4 h-4" />} color="text-purple-400" label={film.poster_url ? 'Rigenera Locandina' : 'Genera Locandina'} hint="1x al mese · AI"
                  onClick={handleRegenPoster} loading={actionLoading === 'regen'} testId="fa-regen" />

                {isInTheaters && (
                  <ActionRow icon={<ChevronDown className="w-4 h-4" />} color="text-orange-400" label="Ritira dal Cinema" hint="Chiudi la programmazione"
                    onClick={() => setConfirmWithdraw(true)} testId="fa-withdraw" />
                )}

                {/* La Mia TV — primary golden CTA */}
                <button
                  onClick={() => setTvSection(true)}
                  disabled={!isInTheaters}
                  className={`w-full group relative overflow-hidden rounded-xl px-3 py-3 text-left transition-all
                    ${isInTheaters
                      ? 'bg-gradient-to-r from-amber-500/20 via-amber-400/15 to-amber-500/5 border border-amber-500/40 hover:border-amber-400/70 hover:shadow-[0_0_20px_rgba(212,175,55,0.25)] active:scale-[0.98]'
                      : 'bg-white/5 border border-white/10 opacity-55 cursor-not-allowed'}`}
                  data-testid="fa-open-mia-tv"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center border ${isInTheaters ? 'bg-amber-500/15 border-amber-400/40 text-amber-300' : 'bg-white/5 border-white/10 text-gray-500'}`}>
                      <Tv className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-bold tracking-wide ${isInTheaters ? 'text-amber-100' : 'text-gray-400'}`}>La Mia TV</p>
                      <p className={`text-[10px] ${isInTheaters ? 'text-amber-300/70' : 'text-gray-500'}`}>
                        {isInTheaters ? 'Trasferisci su una tua emittente (gratis)' : 'Disponibile solo per film al cinema'}
                      </p>
                    </div>
                    {isInTheaters && <ChevronDown className="w-4 h-4 rotate-[-90deg] text-amber-400/70 group-hover:translate-x-0.5 transition-transform" />}
                  </div>
                </button>

                <div className="pt-2 mt-1 border-t border-white/5 space-y-1">
                  <ActionRow icon={<Store className="w-4 h-4" />} color="text-emerald-400" label="Vendi al Mercato" hint="Ricavi dall'asta" onClick={() => setConfirmSell(true)} testId="fa-sell" />
                  <ActionRow icon={<Trash2 className="w-4 h-4" />} color="text-red-400" label="Elimina per sempre" hint="Irreversibile" onClick={() => setConfirmDelete(true)} testId="fa-delete" />
                </div>
              </div>
            ) : (
              <LaMiaTVPanel
                film={film}
                stations={stations}
                loading={stationsLoading}
                loaded={stationsLoaded}
                pickStation={pickStation}
                setPickStation={setPickStation}
                delayHours={delayHours}
                setDelayHours={setDelayHours}
                onBack={() => { setTvSection(false); setPickStation(null); }}
                onTransferNow={handleTransferNow}
                onTransferScheduled={handleTransferScheduled}
                actionLoading={actionLoading}
                onGoInfra={() => { navigate('/infrastructure'); close(); }}
              />
            )}

            {/* Mini confirmations */}
            <MiniConfirm
              open={confirmWithdraw}
              title="Ritira dal Cinema"
              body={`"${film.title}" verra' ritirato dalla programmazione cinematografica. Potrai comunque trasferirlo in TV dopo.`}
              cta="Conferma ritiro"
              tone="orange"
              onCancel={() => setConfirmWithdraw(false)}
              onConfirm={() => { setConfirmWithdraw(false); handleWithdraw(); }}
              loading={actionLoading === 'withdraw'}
            />
            <MiniConfirm
              open={confirmSell}
              title="Vendi al Mercato"
              body={`"${film.title}" verra' messo in asta sul mercato. Confermi?`}
              cta="Metti in vendita"
              tone="emerald"
              onCancel={() => setConfirmSell(false)}
              onConfirm={() => { setConfirmSell(false); handleSell(); }}
              loading={actionLoading === 'sell'}
            />
            <MiniConfirm
              open={confirmDelete}
              title="Eliminazione Permanente"
              body={`"${film.title}" sara' cancellato per sempre. Questa azione non e' reversibile.`}
              cta="Elimina per sempre"
              tone="red"
              onCancel={() => setConfirmDelete(false)}
              onConfirm={() => { setConfirmDelete(false); handleDelete(); }}
              loading={actionLoading === 'delete'}
            />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}

/* ─── Trailer Banner ─── */
function TrailerBanner({ film, trailer, trailerLoading, onGo }) {
  const hasTrailer = Boolean(trailer);
  const frames = trailer?.frames?.length || 0;
  const thumb = trailer?.frames?.[0]?.image_url || trailer?.frames?.[0]?.storage_path || film.poster_url;
  const thumbSrc = thumb && thumb.startsWith('http') ? thumb : (thumb ? `${API}${thumb}` : null);
  return (
    <button
      onClick={onGo}
      className={`w-full relative overflow-hidden rounded-xl border transition-all active:scale-[0.98] mb-1
        ${hasTrailer
          ? 'bg-gradient-to-r from-[#1a0f08] via-[#140b06] to-[#0f0804] border-orange-500/40 shadow-[0_0_18px_rgba(245,166,35,0.22)] hover:border-orange-400/70'
          : 'bg-[#0b0a09] border-white/10 opacity-95'}`}
      data-testid="fa-trailer-banner"
    >
      <div className="flex items-center gap-2 p-2">
        {/* Thumb */}
        <div className={`relative w-14 h-10 rounded-md overflow-hidden flex-shrink-0 bg-black border
          ${hasTrailer ? 'border-orange-400/50' : 'border-white/10 grayscale'}`}>
          {thumbSrc ? (
            <img src={thumbSrc} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center"><FilmIcon className="w-4 h-4 text-gray-600" /></div>
          )}
          <div className="absolute inset-0 flex items-center justify-center bg-black/35">
            {trailerLoading ? <Loader2 className="w-4 h-4 text-white animate-spin" />
              : hasTrailer ? <Play className="w-4 h-4 text-white fill-current drop-shadow" />
              : <Lock className="w-4 h-4 text-gray-500" />}
          </div>
        </div>
        <div className="flex-1 min-w-0 text-left">
          <p className={`text-[11px] font-black tracking-[0.15em] uppercase ${hasTrailer ? 'text-orange-300' : 'text-gray-500'}`}>
            Trailer
          </p>
          <p className={`text-[9px] ${hasTrailer ? 'text-orange-100/80' : 'text-gray-500'}`}>
            {trailerLoading ? 'Carico stato...' : hasTrailer ? `${frames} fotogrammi · ${trailer.duration_seconds || '—'}s` : 'Non ancora generato — clicca per crearlo'}
          </p>
        </div>
        <ChevronDown className={`w-4 h-4 rotate-[-90deg] flex-shrink-0 ${hasTrailer ? 'text-orange-400' : 'text-gray-600'}`} />
      </div>
      {!hasTrailer && (
        <div className="h-[2px] w-full bg-gradient-to-r from-gray-700 via-gray-500 to-gray-700 opacity-30" />
      )}
    </button>
  );
}

/* ─── Action Row ─── */
function ActionRow({ icon, color, label, hint, onClick, loading, testId }) {
  return (
    <button onClick={onClick} disabled={loading}
      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all hover:bg-white/5 active:bg-white/10 active:scale-[0.98] disabled:opacity-50"
      data-testid={testId}>
      <div className={`w-9 h-9 rounded-full flex items-center justify-center bg-white/5 border border-white/10 ${color}`}>
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-[12px] font-semibold ${color}`}>{label}</p>
        {hint && <p className="text-[9px] text-gray-500">{hint}</p>}
      </div>
    </button>
  );
}

/* ─── La Mia TV Panel ─── */
function LaMiaTVPanel({ film, stations, loading, loaded, pickStation, setPickStation, delayHours, setDelayHours, onBack, onTransferNow, onTransferScheduled, actionLoading, onGoInfra }) {
  const trend = film.trend || film.cinema_trend;
  const delayOptions = [6, 12, 24, 48, 96];

  return (
    <div className="p-3 max-h-[65vh] overflow-y-auto" data-testid="la-mia-tv-panel">
      <button onClick={onBack} className="flex items-center gap-1 text-[10px] text-amber-400/70 mb-2 hover:text-amber-300 active:scale-95 transition-transform" data-testid="la-mia-tv-back">
        <ChevronDown className="w-3 h-3 rotate-90" /> Azioni Film
      </button>

      <div className="flex items-center gap-2 mb-3">
        <Tv className="w-4 h-4 text-amber-400" />
        <h4 className="text-sm font-bold text-amber-100 tracking-wide">La Mia TV</h4>
        <span className="ml-auto text-[9px] text-emerald-400/80 bg-emerald-500/10 border border-emerald-500/30 px-1.5 py-0.5 rounded font-semibold">GRATIS</span>
      </div>

      {trend && (
        <TrendHint trend={trend} />
      )}

      {loading && !loaded ? (
        <div className="flex flex-col items-center justify-center py-10 gap-2" data-testid="la-mia-tv-loading">
          <Loader2 className="w-5 h-5 text-amber-400 animate-spin" />
          <p className="text-[9px] text-gray-500">Caricamento emittenti…</p>
        </div>
      ) : stations.length === 0 ? (
        <div className="text-center py-6" data-testid="la-mia-tv-empty">
          <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
            <Tv className="w-7 h-7 text-amber-400/70" />
          </div>
          <p className="text-sm font-bold text-amber-100 mb-1">Emittente TV mancante</p>
          <p className="text-[10px] text-gray-400 leading-snug px-4 mb-4">
            Per trasmettere "{film.title}" sulla tua TV devi prima costruire un'emittente.
          </p>
          <button
            onClick={onGoInfra}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-yellow-400 text-black font-bold text-[11px] hover:brightness-110 active:scale-95 transition-all shadow-[0_2px_12px_rgba(212,175,55,0.35)]"
            data-testid="la-mia-tv-goto-infra"
          >
            <Building2 className="w-3.5 h-3.5" />
            Vai a Infrastrutture
          </button>
          <p className="text-[9px] text-gray-600 mt-3">Acquisti l'emittente → torni qui → trasmetti il film (gratis)</p>
        </div>
      ) : !pickStation ? (
        <div className="space-y-1.5">
          <p className="text-[10px] text-gray-500 mb-1.5">Seleziona dove trasmettere:</p>
          {stations.map(s => {
            const full = s.film_count >= s.film_cap;
            return (
              <button
                key={s.id}
                onClick={() => !full && setPickStation(s)}
                disabled={full}
                className={`w-full flex items-center gap-2 p-2 rounded-lg border text-left transition-all
                  ${full
                    ? 'bg-white/5 border-white/10 opacity-50 cursor-not-allowed'
                    : 'bg-gradient-to-r from-amber-500/10 to-transparent border-amber-500/20 hover:border-amber-400/60 active:scale-[0.98]'}`}
                data-testid={`la-mia-tv-station-${s.id}`}
              >
                <div className="w-8 h-8 rounded-md bg-amber-500/15 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
                  <Tv className="w-4 h-4 text-amber-300" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-bold text-white truncate">{s.station_name}</p>
                  <p className="text-[9px] text-gray-500">
                    {s.nation} · Lv {s.infra_level} · {s.film_count}/{s.film_cap} film
                    {s.upcoming_count > 0 && ` · ${s.upcoming_count} in prossimamente`}
                  </p>
                </div>
                {full ? (
                  <span className="text-[8px] text-red-400 font-bold">PIENO</span>
                ) : (
                  <ChevronDown className="w-4 h-4 rotate-[-90deg] text-amber-400/60" />
                )}
              </button>
            );
          })}
        </div>
      ) : (
        <StationTransferOptions
          station={pickStation}
          onBack={() => setPickStation(null)}
          delayHours={delayHours}
          setDelayHours={setDelayHours}
          onTransferNow={() => onTransferNow(pickStation)}
          onTransferScheduled={() => onTransferScheduled(pickStation, delayHours)}
          actionLoading={actionLoading}
          delayOptions={delayOptions}
        />
      )}
    </div>
  );
}

function TrendHint({ trend }) {
  const direction = typeof trend === 'string' ? trend : trend?.direction;
  if (!direction || direction === 'new') return null;
  const cfg = {
    declining: {
      icon: <TrendingDown className="w-3 h-3" />,
      label: 'In calo al cinema',
      sub: 'Trasferimento SUBITO = +6..+14 hype TV',
      cls: 'bg-rose-500/10 border-rose-500/30 text-rose-200',
    },
    growing: {
      icon: <TrendingUp className="w-3 h-3" />,
      label: 'In crescita al cinema',
      sub: 'Valuta di lasciarlo in sala ancora',
      cls: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200',
    },
    stable: {
      icon: <Minus className="w-3 h-3" />,
      label: 'Andamento stabile',
      sub: 'Scegli tu il momento migliore',
      cls: 'bg-sky-500/10 border-sky-500/30 text-sky-200',
    },
  }[direction];
  if (!cfg) return null;
  return (
    <div className={`flex items-start gap-2 p-2 rounded-lg border mb-3 ${cfg.cls}`} data-testid="la-mia-tv-trend">
      <div className="mt-0.5">{cfg.icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-bold">{cfg.label}</p>
        <p className="text-[9px] opacity-80 leading-tight">{cfg.sub}</p>
      </div>
    </div>
  );
}

function StationTransferOptions({ station, onBack, delayHours, setDelayHours, onTransferNow, onTransferScheduled, actionLoading, delayOptions }) {
  const loadingNow = actionLoading === `tv-now-${station.id}`;
  const loadingSched = actionLoading === `tv-sched-${station.id}`;
  return (
    <div className="space-y-3">
      <button onClick={onBack} className="flex items-center gap-1 text-[9px] text-amber-400/70 hover:text-amber-300 active:scale-95 transition-transform" data-testid="la-mia-tv-station-back">
        <ChevronDown className="w-3 h-3 rotate-90" /> Altra emittente
      </button>
      <div className="p-2 rounded-lg bg-amber-500/5 border border-amber-500/20">
        <p className="text-[11px] font-bold text-amber-100">{station.station_name}</p>
        <p className="text-[9px] text-amber-300/60">{station.nation} · Livello {station.infra_level}</p>
      </div>

      {/* Subito CTA — gold */}
      <button
        onClick={onTransferNow}
        disabled={loadingNow || loadingSched}
        className="w-full rounded-xl px-3 py-3 text-left bg-gradient-to-r from-amber-500 via-amber-400 to-yellow-300 text-black shadow-[0_0_24px_rgba(255,200,80,0.35)] hover:shadow-[0_0_32px_rgba(255,200,80,0.55)] active:scale-[0.98] transition-all disabled:opacity-60"
        data-testid="la-mia-tv-transfer-now"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-black/20 flex items-center justify-center">
            {loadingNow ? <Loader2 className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-black tracking-wide">SUBITO</p>
            <p className="text-[10px] font-semibold opacity-80">Ritiro dal cinema e messa in onda immediata</p>
          </div>
        </div>
      </button>

      {/* Prossimamente */}
      <div className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-3 space-y-2">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-sky-300" />
          <p className="text-[12px] font-bold text-sky-100">Prossimamente</p>
        </div>
        <p className="text-[9px] text-sky-200/70">Il film resta al cinema e va in onda tra:</p>
        <div className="grid grid-cols-5 gap-1">
          {delayOptions.map(h => (
            <button
              key={h}
              onClick={() => setDelayHours(h)}
              className={`py-1.5 rounded-md text-[10px] font-bold transition-all
                ${delayHours === h ? 'bg-sky-400 text-black shadow-[0_0_10px_rgba(120,200,255,0.5)]' : 'bg-white/5 text-sky-200 border border-white/10 hover:border-sky-400/50'}`}
              data-testid={`la-mia-tv-delay-${h}`}
            >
              {h < 48 ? `${h}h` : `${h / 24}g`}
            </button>
          ))}
        </div>
        <button
          onClick={onTransferScheduled}
          disabled={loadingNow || loadingSched}
          className="w-full py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-[11px] font-bold active:scale-[0.98] transition-all disabled:opacity-60"
          data-testid="la-mia-tv-transfer-scheduled"
        >
          {loadingSched ? <Loader2 className="w-4 h-4 animate-spin inline-block" /> : <>Programma tra {delayHours < 48 ? `${delayHours}h` : `${delayHours / 24}g`}</>}
        </button>
      </div>

      <div className="flex items-start gap-1.5 px-1">
        <Info className="w-3 h-3 text-gray-500 flex-shrink-0 mt-0.5" />
        <p className="text-[9px] text-gray-500 leading-tight">
          Entrambe le opzioni sono <b>gratuite</b> perche' la stazione e' tua.
          "Subito" da' un bonus hype TV se il film era in calo.
        </p>
      </div>
    </div>
  );
}

/* ─── Mini Confirm Dialog ─── */
function MiniConfirm({ open, title, body, cta, tone, onCancel, onConfirm, loading }) {
  if (!open) return null;
  const toneCls = {
    red: { ring: 'border-red-500/40', btn: 'bg-red-600 hover:bg-red-500', icon: 'text-red-400' },
    emerald: { ring: 'border-emerald-500/40', btn: 'bg-emerald-600 hover:bg-emerald-500', icon: 'text-emerald-400' },
    orange: { ring: 'border-orange-500/40', btn: 'bg-orange-600 hover:bg-orange-500', icon: 'text-orange-400' },
  }[tone] || { ring: 'border-white/20', btn: 'bg-white/10', icon: 'text-white' };
  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/80 backdrop-blur-sm" onClick={onCancel}>
      <div className={`bg-[#15100c] border ${toneCls.ring} rounded-xl max-w-[300px] w-[90%] p-4 shadow-xl`} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className={`w-4 h-4 ${toneCls.icon}`} />
          <h4 className="text-sm font-bold text-white">{title}</h4>
        </div>
        <p className="text-[11px] text-gray-400 leading-relaxed mb-3">{body}</p>
        <div className="flex gap-2">
          <button onClick={onCancel} className="flex-1 py-2 rounded-md bg-white/5 border border-white/10 text-[11px] text-gray-300 hover:bg-white/10 active:scale-95 transition-transform">Annulla</button>
          <button onClick={onConfirm} disabled={loading} className={`flex-1 py-2 rounded-md text-[11px] text-white font-semibold ${toneCls.btn} active:scale-95 transition-transform disabled:opacity-60`} data-testid="mini-confirm-btn">
            {loading ? <Loader2 className="w-3 h-3 animate-spin inline-block mr-1" /> : null}
            {cta}
          </button>
        </div>
      </div>
    </div>
  );
}
