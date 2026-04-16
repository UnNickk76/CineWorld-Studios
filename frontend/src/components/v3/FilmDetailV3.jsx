import React, { useState, useEffect, useContext } from 'react';
import {
  X, Film, Star, Clock, MapPin, Users, Megaphone, Globe, Award, TrendingUp,
  Heart, Trash2, AlertTriangle, ChevronDown, ChevronUp, DollarSign,
  Clapperboard, Eye, BarChart3, Tv, Zap, Music, Pen, Theater
} from 'lucide-react';
import { AuthContext } from '../../contexts';
import { toast } from 'sonner';

const GENRE_LABELS = {
  action: 'Azione', comedy: 'Commedia', drama: 'Dramma', horror: 'Horror',
  sci_fi: 'Fantascienza', romance: 'Romance', thriller: 'Thriller',
  animation: 'Animazione', documentary: 'Documentario', fantasy: 'Fantasy',
  adventure: 'Avventura', musical: 'Musical', western: 'Western',
  biographical: 'Biografico', mystery: 'Mistero', war: 'Guerra',
  crime: 'Crime', noir: 'Noir', historical: 'Storico',
};

const PERF_MAP = {
  great: { label: 'Straordinario', color: '#4ade80' },
  good: { label: 'Ottimo', color: '#34d399' },
  ok: { label: 'Discreto', color: '#facc15' },
  declining: { label: 'In calo', color: '#fb923c' },
  bad: { label: 'Scarso', color: '#f87171' },
  flop: { label: 'Flop', color: '#ef4444' },
};

/* ─── Stat Box ─── */
const StatBox = ({ label, value, color = 'text-white', icon: Icon, sub }) => (
  <div className="text-center p-2 rounded-lg bg-white/[0.02] border border-white/5" data-testid={`stat-${label.toLowerCase().replace(/\s/g,'-')}`}>
    <div className="text-[8px] text-gray-500 uppercase tracking-wider flex items-center justify-center gap-0.5 mb-0.5">
      {Icon && <Icon className="w-2.5 h-2.5" />}{label}
    </div>
    <div className={`text-sm font-bold ${color}`}>{value}</div>
    {sub && <div className="text-[7px] text-gray-600">{sub}</div>}
  </div>
);

/* ─── Cast Member Card ─── */
const CastMemberCard = ({ person, role, roleColor, roleBg }) => {
  const [open, setOpen] = useState(false);
  const skills = person?.skills || {};
  const skillEntries = Object.entries(skills);
  const avgSkill = skillEntries.length > 0
    ? Math.round(skillEntries.reduce((a, [, v]) => a + v, 0) / skillEntries.length)
    : 0;

  return (
    <div className={`rounded-lg border ${roleBg} overflow-hidden`}>
      <div className="flex items-center gap-2 p-2 cursor-pointer" onClick={() => skillEntries.length > 0 && setOpen(!open)}>
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${roleColor}`}>
          {person?.name?.charAt(0) || '?'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 flex-wrap">
            <span className="text-[10px] font-semibold text-white truncate">{person?.name || 'N/D'}</span>
            {person?.gender && (
              <span className={`text-[9px] font-bold ${person.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>
                {person.gender === 'female' ? '♀' : '♂'}
              </span>
            )}
            {[...Array(person?.stars || Math.min(5, Math.ceil(avgSkill / 20)))].map((_, i) => (
              <Star key={i} className="w-2 h-2 text-yellow-500 fill-yellow-500" />
            ))}
          </div>
          <div className="text-[8px] text-gray-500">
            {role}{avgSkill > 0 && <> &bull; Skill <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span></>}
            {person?.nationality && <> &bull; {person.nationality}</>}
          </div>
        </div>
        {skillEntries.length > 0 && (
          <div className="flex-shrink-0">
            {open ? <ChevronUp className="w-3 h-3 text-gray-500" /> : <ChevronDown className="w-3 h-3 text-gray-500" />}
          </div>
        )}
      </div>
      {open && skillEntries.length > 0 && (
        <div className="px-2 pb-2 grid grid-cols-2 gap-1 border-t border-white/5 pt-1.5">
          {skillEntries.map(([name, val]) => (
            <div key={name} className="flex items-center gap-1">
              <span className="text-[7px] text-gray-500 truncate w-16">{name.replace(/_/g, ' ')}</span>
              <div className="flex-1 h-1 bg-gray-800 rounded-full">
                <div className={`h-full rounded-full ${val >= 80 ? 'bg-emerald-500' : val >= 60 ? 'bg-cyan-500' : val >= 40 ? 'bg-amber-500' : 'bg-red-500'}`}
                  style={{ width: `${Math.min(100, val)}%` }} />
              </div>
              <span className="text-[7px] font-mono text-gray-400 w-4 text-right">{val}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/* ─── ADV Panel ─── */
const AdvPanel = ({ filmId, api, onDone }) => {
  const [platforms, setPlatforms] = useState([]);
  const [selected, setSelected] = useState([]);
  const [days, setDays] = useState(3);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get('/advertising/platforms').then(r => {
      const data = Array.isArray(r.data) ? r.data : r.data.platforms || r.data;
      setPlatforms(data);
    }).catch(() => {});
  }, [api]);

  const totalCost = selected.reduce((acc, pid) => {
    const p = platforms.find(x => x.id === pid);
    return acc + (p ? p.cost_per_day * days : 0);
  }, 0);

  const toggle = (pid) => setSelected(prev =>
    prev.includes(pid) ? prev.filter(x => x !== pid) : [...prev, pid]
  );

  const launch = async () => {
    if (selected.length === 0) return toast.error('Seleziona almeno una piattaforma');
    setLoading(true);
    try {
      const r = await api.post(`/films/${filmId}/advertise`, {
        platforms: selected, days, budget: totalCost,
      });
      toast.success(`Campagna lanciata! Revenue boost: $${(r.data.revenue_boost || 0).toLocaleString()}`);
      onDone?.();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore campagna ADV');
    }
    setLoading(false);
  };

  return (
    <div className="space-y-2" data-testid="adv-panel">
      <p className="text-[9px] text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1">
        <Megaphone className="w-3 h-3" /> Campagna Pubblicitaria
      </p>
      <div className="space-y-1">
        {platforms.map(p => (
          <button key={p.id} onClick={() => toggle(p.id)}
            className={`w-full flex items-center justify-between p-2 rounded-lg border text-left transition-all ${
              selected.includes(p.id)
                ? 'border-cyan-500/40 bg-cyan-500/10'
                : 'border-white/5 bg-white/[0.02] hover:border-white/10'
            }`} data-testid={`adv-platform-${p.id}`}>
            <div>
              <span className="text-[9px] font-semibold text-white">{p.name_it || p.name}</span>
              <span className="text-[7px] text-gray-500 ml-1">x{p.reach_multiplier}</span>
            </div>
            <span className="text-[8px] text-yellow-400 font-bold">${(p.cost_per_day * days).toLocaleString()}</span>
          </button>
        ))}
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-[8px] text-gray-500">Giorni:</span>
        {[1, 3, 5, 7].map(d => (
          <button key={d} onClick={() => setDays(d)}
            className={`px-2 py-0.5 rounded text-[8px] font-bold border transition-all ${
              days === d ? 'border-cyan-500 bg-cyan-500/15 text-cyan-400' : 'border-gray-700 text-gray-500'
            }`}>{d}g</button>
        ))}
      </div>
      {selected.length > 0 && (
        <div className="flex items-center justify-between px-1">
          <span className="text-[8px] text-gray-400">Costo totale</span>
          <span className="text-[10px] font-bold text-yellow-400">${totalCost.toLocaleString()}</span>
        </div>
      )}
      <button onClick={launch} disabled={loading || selected.length === 0}
        className="w-full py-2 rounded-lg bg-cyan-600/20 border border-cyan-500/30 text-cyan-400 text-[9px] font-bold disabled:opacity-40 transition-all hover:bg-cyan-600/30"
        data-testid="launch-adv-btn">
        {loading ? '...' : `Lancia Campagna ($${totalCost.toLocaleString()})`}
      </button>
    </div>
  );
};

/* ═══════════════════════ MAIN COMPONENT ═══════════════════════ */

export default function FilmDetailV3({ filmId, onClose }) {
  const { api, user } = useContext(AuthContext);
  const [film, setFilm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [showAdv, setShowAdv] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [reviews, setReviews] = useState([]);
  const [expandCast, setExpandCast] = useState(false);
  const [expandSynopsis, setExpandSynopsis] = useState(false);

  /* ─── Load film data ─── */
  useEffect(() => {
    if (!filmId) return;
    setLoading(true);
    api.get(`/pipeline-v3/released-film/${filmId}`).then(r => {
      setFilm(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filmId, api]);

  /* ─── Load virtual reviews ─── */
  useEffect(() => {
    if (!filmId) return;
    api.get(`/films/${filmId}/virtual-audience`).then(r => {
      setReviews(r.data?.reviews || []);
    }).catch(() => {});
  }, [filmId, api]);

  /* ─── Actions ─── */
  const withdrawFromTheaters = async () => {
    setActionLoading(true);
    try {
      const pid = film?.source_project_id;
      if (pid) {
        await api.post(`/pipeline-v3/films/${pid}/withdraw-theaters`);
        toast.success('Film ritirato dalle sale');
      }
      onClose?.();
    } catch (e) { toast.error('Errore nel ritiro'); }
    setActionLoading(false);
  };

  const deleteFilm = async () => {
    setActionLoading(true);
    try {
      await api.post(`/pipeline-v3/films/${filmId}/delete-film`);
      toast.success('Film eliminato permanentemente');
      onClose?.();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore eliminazione'); }
    setActionLoading(false);
  };

  if (!filmId) return null;

  const isOwner = film?.user_id === user?.id;
  const isLive = film?.status === 'in_theaters';

  /* ─── Derived data ─── */
  const cast = film?.cast || {};
  const director = cast.director;
  const actors = cast.actors || [];
  const composer = cast.composer;
  const screenwriter = cast.screenwriter;
  const distZones = film?.distribution_zones || [];
  const sponsors = film?.selected_sponsors || [];
  const revenue = film?.total_revenue || 0;
  const quality = film?.quality_score;
  const cinemas = film?.current_cinemas || 0;
  const likes = film?.likes_count || film?.virtual_likes || 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-end sm:items-center justify-center" onClick={onClose} data-testid="film-detail-v3-modal">
      <div className="bg-[#0a0a0c] border-t sm:border border-gray-800/60 rounded-t-2xl sm:rounded-2xl w-full max-w-[420px] max-h-[92vh] overflow-y-auto"
        onClick={e => e.stopPropagation()} style={{ overscrollBehavior: 'contain' }}>

        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
          </div>
        ) : !film ? (
          <div className="text-center py-24 text-gray-500 text-sm">Film non trovato</div>
        ) : (
          <>
            {/* ═══ POSTER HEADER ═══ */}
            <div className="relative">
              {film.poster_url ? (
                <img src={film.poster_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${film.poster_url}` : film.poster_url}
                  alt="" className="w-full aspect-[3/4] object-cover rounded-t-2xl" />
              ) : (
                <div className="w-full aspect-[3/4] bg-gray-900 flex items-center justify-center rounded-t-2xl">
                  <Film className="w-14 h-14 text-gray-700" />
                </div>
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0c] via-[#0a0a0c]/50 to-transparent" />

              <button onClick={onClose} className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/60 backdrop-blur-sm flex items-center justify-center border border-white/10 hover:bg-black/80 transition-colors" data-testid="close-film-detail">
                <X className="w-4 h-4 text-white" />
              </button>

              {/* Status badge */}
              {isLive && (
                <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/60 backdrop-blur-sm rounded-full px-2.5 py-1 border border-green-500/20">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  <span className="text-[8px] font-black text-green-400 tracking-wider">AL CINEMA</span>
                </div>
              )}
              {film.status === 'completed' && (
                <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/60 backdrop-blur-sm rounded-full px-2.5 py-1 border border-gray-500/20">
                  <span className="text-[8px] font-black text-gray-400 tracking-wider">FUORI SALA</span>
                </div>
              )}

              {/* Title overlay */}
              <div className="absolute bottom-4 left-4 right-4">
                <h2 className="text-xl font-black text-white drop-shadow-lg leading-tight" data-testid="film-title">{film.title}</h2>
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                  <span className="text-[8px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 font-bold border border-amber-500/20">
                    {GENRE_LABELS[film.genre] || film.genre}
                  </span>
                  {film.subgenre && (
                    <span className="text-[8px] px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-400 font-bold border border-purple-500/20">
                      {GENRE_LABELS[film.subgenre] || film.subgenre}
                    </span>
                  )}
                  {film.film_duration_label && (
                    <span className="text-[8px] text-gray-300 flex items-center gap-0.5">
                      <Clock className="w-2.5 h-2.5" />{film.film_duration_label}
                    </span>
                  )}
                  {film.film_format && film.film_format !== 'standard' && (
                    <span className="text-[8px] text-blue-400 uppercase font-bold">{film.film_format}</span>
                  )}
                </div>
              </div>
            </div>

            {/* ═══ STATS GRID ═══ */}
            <div className="px-3 py-3 grid grid-cols-4 gap-1.5" data-testid="film-stats-grid">
              <StatBox label="Sala" value={`${film.days_in_theater || 0}g`} color="text-green-400" icon={Clapperboard}
                sub={isLive ? `${film.days_remaining || 0}g rimasti` : 'concluso'} />
              <StatBox label="Incasso" value={`$${revenue >= 1000000 ? (revenue/1000000).toFixed(1)+'M' : revenue >= 1000 ? (revenue/1000).toFixed(0)+'K' : revenue}`}
                color="text-emerald-400" icon={DollarSign} />
              <StatBox label="Likes" value={likes.toLocaleString()} color="text-pink-400" icon={Heart} />
              <StatBox label="Cinema" value={cinemas} color="text-cyan-400" icon={Globe}
                sub={distZones.length > 0 ? `${distZones.length} zone` : ''} />
            </div>

            {/* Quality bar */}
            {quality != null && (
              <div className="px-4 pb-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[8px] text-gray-500 uppercase tracking-wider">Qualità</span>
                  <span className={`text-xs font-bold ${quality >= 75 ? 'text-emerald-400' : quality >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {quality}/100
                  </span>
                </div>
                <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${quality >= 75 ? 'bg-emerald-500' : quality >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${quality}%` }} />
                </div>
              </div>
            )}

            {/* ═══ PRODUCER ═══ */}
            <div className="px-4 py-2.5 border-t border-white/5 flex items-center gap-2.5" data-testid="film-producer">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500/30 to-cyan-500/30 flex items-center justify-center text-[10px] font-bold text-white border border-white/10">
                {(film.producer?.nickname || '?')[0]}
              </div>
              <div>
                <p className="text-[10px] font-bold text-white">{film.producer?.nickname || 'Produttore'}</p>
                <p className="text-[8px] text-gray-500">{film.producer?.production_house_name || 'Studio indipendente'}</p>
              </div>
              {isOwner && <span className="ml-auto text-[7px] px-1.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-bold">TUO</span>}
            </div>

            {/* ═══ CAST ═══ */}
            {(director || actors.length > 0 || composer || screenwriter) && (
              <div className="px-4 py-3 border-t border-white/5" data-testid="film-cast-section">
                <button className="flex items-center justify-between w-full mb-2" onClick={() => setExpandCast(!expandCast)}>
                  <span className="text-[9px] text-gray-400 uppercase font-bold tracking-wider flex items-center gap-1">
                    <Users className="w-3 h-3" /> Cast & Crew
                    <span className="text-[8px] text-gray-600 font-normal ml-1">
                      ({[director, screenwriter, composer, ...actors].filter(Boolean).length} persone)
                    </span>
                  </span>
                  {expandCast ? <ChevronUp className="w-3.5 h-3.5 text-gray-500" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-500" />}
                </button>

                {!expandCast ? (
                  /* Compact view */
                  <div className="flex flex-wrap gap-1">
                    {director && (
                      <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium">
                        Regia: {director.name}
                      </span>
                    )}
                    {actors.slice(0, 3).map((a, i) => (
                      <span key={i} className="text-[7px] px-1.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">
                        {a.name} {a.cast_role ? `(${a.cast_role})` : ''}
                      </span>
                    ))}
                    {actors.length > 3 && <span className="text-[7px] text-gray-500 self-center">+{actors.length - 3} altri</span>}
                    {composer && (
                      <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 font-medium">
                        Musiche: {composer.name}
                      </span>
                    )}
                  </div>
                ) : (
                  /* Expanded view with skills */
                  <div className="space-y-1.5">
                    {director && <CastMemberCard person={director} role="Regia" roleColor="bg-purple-500/20 text-purple-400" roleBg="border-purple-500/15 bg-purple-500/5" />}
                    {screenwriter && <CastMemberCard person={screenwriter} role="Sceneggiatura" roleColor="bg-emerald-500/20 text-emerald-400" roleBg="border-emerald-500/15 bg-emerald-500/5" />}
                    {actors.map((a, i) => (
                      <CastMemberCard key={i} person={a} role={a.cast_role || 'Attore'} roleColor="bg-cyan-500/20 text-cyan-400" roleBg="border-cyan-500/15 bg-cyan-500/5" />
                    ))}
                    {composer && <CastMemberCard person={composer} role="Compositore" roleColor="bg-yellow-500/20 text-yellow-400" roleBg="border-yellow-500/15 bg-yellow-500/5" />}
                  </div>
                )}
              </div>
            )}

            {/* ═══ SYNOPSIS ═══ */}
            {film.preplot && (
              <div className="px-4 py-3 border-t border-white/5" data-testid="film-synopsis">
                <button className="flex items-center justify-between w-full mb-1" onClick={() => setExpandSynopsis(!expandSynopsis)}>
                  <span className="text-[9px] text-gray-400 uppercase font-bold tracking-wider flex items-center gap-1">
                    <Pen className="w-3 h-3" /> Trama
                  </span>
                  {expandSynopsis ? <ChevronUp className="w-3 h-3 text-gray-500" /> : <ChevronDown className="w-3 h-3 text-gray-500" />}
                </button>
                <div className={expandSynopsis ? '' : 'max-h-[60px] overflow-hidden relative'}>
                  <p className="text-[9px] text-gray-400 leading-relaxed italic">"{film.preplot}"</p>
                  {!expandSynopsis && <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-[#0a0a0c] to-transparent" />}
                </div>
              </div>
            )}

            {/* ═══ DISTRIBUTION ZONES ═══ */}
            {distZones.length > 0 && (
              <div className="px-4 py-3 border-t border-white/5" data-testid="film-distribution">
                <p className="text-[9px] text-gray-400 uppercase font-bold tracking-wider mb-1.5 flex items-center gap-1">
                  <Globe className="w-3 h-3" /> Distribuzione
                </p>
                <div className="flex flex-wrap gap-1">
                  {film.distribution_world && (
                    <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-bold">Mondiale</span>
                  )}
                  {distZones.map((z, i) => (
                    <span key={i} className="text-[7px] px-1.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      {typeof z === 'string' ? z : z.name || z.continent || 'Zona'}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* ═══ SPONSORS ═══ */}
            {sponsors.length > 0 && (
              <div className="px-4 py-3 border-t border-white/5" data-testid="film-sponsors">
                <p className="text-[9px] text-gray-400 uppercase font-bold tracking-wider mb-1.5 flex items-center gap-1">
                  <Award className="w-3 h-3" /> Sponsor
                </p>
                <div className="flex flex-wrap gap-1">
                  {sponsors.map((s, i) => (
                    <span key={i} className="text-[7px] px-2 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 font-medium">
                      {s.sponsor_name || s.name}
                      {s.contribution && <span className="text-green-500/60 ml-1">${(s.contribution / 1000).toFixed(0)}K</span>}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* ═══ VIRTUAL REVIEWS ═══ */}
            {reviews.length > 0 && (
              <div className="px-4 py-3 border-t border-white/5" data-testid="film-reviews">
                <p className="text-[9px] text-gray-400 uppercase font-bold tracking-wider mb-2 flex items-center gap-1">
                  <Eye className="w-3 h-3" /> Recensioni Pubblico
                </p>
                <div className="space-y-1.5">
                  {reviews.slice(0, 3).map((r, i) => (
                    <div key={i} className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-[8px] font-semibold text-white">{r.reviewer_name || r.author || 'Anonimo'}</span>
                        <div className="flex items-center gap-0.5">
                          {[...Array(5)].map((_, s) => (
                            <Star key={s} className={`w-2 h-2 ${s < (r.rating || r.score || 3) ? 'text-yellow-500 fill-yellow-500' : 'text-gray-700'}`} />
                          ))}
                        </div>
                      </div>
                      <p className="text-[8px] text-gray-400 leading-relaxed line-clamp-2">{r.text || r.content || r.review || ''}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ═══ ACTION BUTTONS ═══ */}
            {isOwner && (
              <div className="px-4 py-4 border-t border-white/5 space-y-2" data-testid="film-actions">

                {/* ADV Button */}
                {isLive && (
                  <>
                    {!showAdv ? (
                      <button onClick={() => setShowAdv(true)}
                        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-bold hover:bg-cyan-500/15 transition-all"
                        data-testid="open-adv-btn">
                        <Megaphone className="w-3.5 h-3.5" /> Lancia Pubblicità (ADV)
                      </button>
                    ) : (
                      <div className="p-3 rounded-lg border border-cyan-500/20 bg-cyan-500/5">
                        <AdvPanel filmId={filmId} api={api} onDone={() => {
                          setShowAdv(false);
                          api.get(`/pipeline-v3/released-film/${filmId}`).then(r => setFilm(r.data)).catch(() => {});
                        }} />
                        <button onClick={() => setShowAdv(false)} className="w-full mt-2 text-[8px] text-gray-500 hover:text-gray-300">Chiudi ADV</button>
                      </div>
                    )}
                  </>
                )}

                {/* Withdraw from theaters (Orange) */}
                {isLive && (
                  <>
                    {!showWithdraw ? (
                      <button onClick={() => setShowWithdraw(true)}
                        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400 text-[10px] font-bold hover:bg-orange-500/15 transition-all"
                        data-testid="withdraw-btn">
                        <Trash2 className="w-3.5 h-3.5" /> Ritira dalle Sale
                      </button>
                    ) : (
                      <div className="p-3 rounded-lg bg-orange-500/5 border border-orange-500/20 space-y-2">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-orange-400" />
                          <p className="text-[10px] text-orange-300 font-bold">Ritirare il film?</p>
                        </div>
                        <p className="text-[8px] text-gray-400">Il film verrà rimosso da tutte le sale cinematografiche. L'incasso accumulato resterà invariato.</p>
                        <div className="flex gap-2">
                          <button onClick={() => setShowWithdraw(false)}
                            className="flex-1 py-1.5 rounded-lg border border-gray-700 text-gray-400 text-[9px] font-bold hover:bg-gray-800 transition-all">Annulla</button>
                          <button onClick={withdrawFromTheaters} disabled={actionLoading}
                            className="flex-1 py-1.5 rounded-lg bg-orange-500/20 border border-orange-500/40 text-orange-400 text-[9px] font-bold disabled:opacity-50 hover:bg-orange-500/30 transition-all"
                            data-testid="confirm-withdraw-btn">
                            {actionLoading ? '...' : 'Conferma Ritiro'}
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* Delete film (Red) */}
                {!showDelete ? (
                  <button onClick={() => setShowDelete(true)}
                    className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-500/8 border border-red-500/15 text-red-400/70 text-[10px] font-bold hover:bg-red-500/15 hover:text-red-400 transition-all"
                    data-testid="delete-film-btn">
                    <Trash2 className="w-3.5 h-3.5" /> Elimina Film
                  </button>
                ) : (
                  <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/20 space-y-2">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                      <p className="text-[10px] text-red-300 font-bold">Eliminazione permanente!</p>
                    </div>
                    <p className="text-[8px] text-gray-400">Il film verrà eliminato definitivamente dal database. Questa azione è irreversibile.</p>
                    <div className="flex gap-2">
                      <button onClick={() => setShowDelete(false)}
                        className="flex-1 py-1.5 rounded-lg border border-gray-700 text-gray-400 text-[9px] font-bold hover:bg-gray-800 transition-all">Annulla</button>
                      <button onClick={deleteFilm} disabled={actionLoading}
                        className="flex-1 py-1.5 rounded-lg bg-red-500/20 border border-red-500/40 text-red-400 text-[9px] font-bold disabled:opacity-50 hover:bg-red-500/30 transition-all"
                        data-testid="confirm-delete-btn">
                        {actionLoading ? '...' : 'Elimina per Sempre'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Bottom padding for mobile */}
            <div className="h-4" />
          </>
        )}
      </div>
    </div>
  );
}
