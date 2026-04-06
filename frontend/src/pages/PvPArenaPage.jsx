import React, { useState, useEffect, useCallback, useContext } from 'react';
import { AuthContext } from '../contexts';
import { useSWR, useGameStore } from '../contexts/GameStore';
import { motion, AnimatePresence } from 'framer-motion';
import { Swords, Shield, Heart, Bomb, TrendingUp, Clock, Film, Share2, Users, Award, ThumbsDown, Eye, Newspaper, Sparkles, Flame, Skull, ChevronRight, BarChart3, History, X, Check, AlertTriangle, Target, PartyPopper, Laugh, Star, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { OutcomePopup, getOutcomeType, parseOutcome } from '../components/OutcomePopup';

const ICON_MAP = {
  Share2, Users, PartyPopper, Award, Newspaper, ThumbsDown, Eye, Bomb,
  Flame, Heart, Laugh, Sparkles, Skull,
};

const STATUS_LABELS = {
  'in_sala': { label: 'In Sala', color: 'text-green-400 bg-green-500/15' },
  'coming_soon': { label: 'Coming Soon', color: 'text-yellow-400 bg-yellow-500/15' },
  'anteprima': { label: 'Anteprima', color: 'text-cyan-400 bg-cyan-500/15' },
  'in_aggiornamento': { label: 'In Aggiornamento', color: 'text-amber-400 bg-amber-500/15' },
};

const GROUP_COLORS = {
  red: { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400', accent: 'from-red-600 to-orange-600' },
  pink: { bg: 'bg-pink-500/10', border: 'border-pink-500/20', text: 'text-pink-400', accent: 'from-pink-600 to-rose-600' },
  yellow: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', text: 'text-yellow-400', accent: 'from-yellow-600 to-amber-600' },
  purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/20', text: 'text-purple-400', accent: 'from-purple-600 to-indigo-600' },
  green: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', accent: 'from-emerald-600 to-teal-600' },
};

export default function PvPArenaPage() {
  const { user, api, refreshUser } = useContext(AuthContext);
  const [tab, setTab] = useState('arena');
  const [arenaData, setArenaData] = useState(null);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState(null);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [filmDetail, setFilmDetail] = useState(null);
  const [actionResult, setActionResult] = useState(null);
  const [outcomePopup, setOutcomePopup] = useState(null);
  const [loading, setLoading] = useState(false);

  // Arena Mirata state
  const [arenaTargets, setArenaTargets] = useState(null);
  const [arenaAttackResult, setArenaAttackResult] = useState(null);
  const [attackingTarget, setAttackingTarget] = useState(null);
  const [arenaHistory, setArenaHistory] = useState(null);

  // SWR: instant data from cache, revalidate in background
  const { data: arenaRaw, mutate: refreshArena } = useSWR('/pvp-cinema/arena');
  const { data: statsRaw, mutate: refreshStats } = useSWR('/pvp-cinema/stats');

  useEffect(() => { if (arenaRaw) setArenaData(arenaRaw); }, [arenaRaw]);
  useEffect(() => { if (statsRaw) setStats(statsRaw); }, [statsRaw]);

  const loadArena = useCallback(() => {
    refreshArena();
    refreshStats();
  }, [refreshArena, refreshStats]);

  const loadHistory = async () => {
    try {
      const r = await api.get('/pvp-cinema/history');
      setHistory(r.data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { if (tab === 'report') loadHistory(); }, [tab]);

  // Load arena targets when mirata tab is selected
  useEffect(() => {
    if (tab === 'mirata') {
      api.get('/pvp/arena-targets').then(r => setArenaTargets(r.data)).catch(() => {});
      api.get('/pvp/arena-history').then(r => setArenaHistory(r.data)).catch(() => {});
    }
  }, [tab]);

  const executeArenaAttack = async (targetUserId, category) => {
    setAttackingTarget(`${targetUserId}_${category}`);
    setArenaAttackResult(null);
    try {
      const r = await api.post('/pvp/arena-attack', { target_user_id: targetUserId, target_category: category });
      setArenaAttackResult(r.data);
      refreshUser();
      // Refresh targets
      api.get('/pvp/arena-targets').then(res => setArenaTargets(res.data)).catch(() => {});
      api.get('/pvp/arena-history').then(res => setArenaHistory(res.data)).catch(() => {});
    } catch (e) {
      setArenaAttackResult({ success: false, message: e.response?.data?.detail || 'Errore' });
    }
    setAttackingTarget(null);
  };

  const openFilm = async (filmId) => {
    setSelectedFilm(filmId);
    setActionResult(null);
    try {
      const r = await api.get(`/pvp-cinema/film/${filmId}`);
      setFilmDetail(r.data);
    } catch (e) { console.error(e); }
  };

  const executeAction = async (category, actionId) => {
    if (!filmDetail) return;
    setLoading(true);
    setActionResult(null);
    try {
      const endpoint = category === 'support' ? '/pvp-cinema/support' : '/pvp-cinema/boycott';
      const r = await api.post(endpoint, { film_id: filmDetail.id, action_id: actionId });
      setActionResult(r.data);
      // Show outcome popup
      const outcome = parseOutcome(category, r.data);
      const otype = getOutcomeType(category, outcome);
      setOutcomePopup({
        type: otype,
        title: filmDetail.title,
        message: r.data.message || '',
      });
      refreshUser();
      loadArena();
      const fd = await api.get(`/pvp-cinema/film/${filmDetail.id}`);
      setFilmDetail(fd.data);
    } catch (e) {
      setActionResult({ success: false, message: e.response?.data?.detail || 'Errore' });
    }
    setLoading(false);
  };

  const executeDefend = async () => {
    if (!filmDetail) return;
    setLoading(true);
    try {
      const r = await api.post('/pvp-cinema/defend', { film_id: filmDetail.id, action_id: 'defend' });
      setActionResult(r.data);
      refreshUser();
      const fd = await api.get(`/pvp-cinema/film/${filmDetail.id}`);
      setFilmDetail(fd.data);
    } catch (e) {
      setActionResult({ success: false, message: e.response?.data?.detail || 'Errore' });
    }
    setLoading(false);
  };

  const tabs = [
    { id: 'arena', label: 'Arena', icon: Swords },
    { id: 'mirata', label: 'Mirata', icon: Target },
    { id: 'report', label: 'Report', icon: History },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0B] pt-16" style={{ paddingBottom: 'calc(6rem + env(safe-area-inset-bottom, 0px))' }} data-testid="pvp-arena-page">
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-red-950/40 via-transparent to-transparent" />
        <div className="relative px-4 pt-5 pb-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg shadow-red-500/20">
              <Swords className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">Arena PvP</h1>
              <p className="text-[10px] text-gray-500">Supporta i tuoi film, boicotta i nemici</p>
            </div>
            {stats && (
              <div className="ml-auto flex items-center gap-1.5 bg-white/5 px-2.5 py-1 rounded-full border border-white/10">
                <Flame className="w-3 h-3 text-orange-400" />
                <span className="text-xs font-bold text-white">{stats.actions_remaining}</span>
                <span className="text-[9px] text-gray-500">/{stats.max_actions_per_hour}</span>
              </div>
            )}
          </div>

          {stats && (
            <div className="flex gap-2" data-testid="pvp-stats-bar">
              <MiniStat icon={<Heart className="w-3 h-3" />} value={stats.total_support} label="Supporto" c="emerald" />
              <MiniStat icon={<Bomb className="w-3 h-3" />} value={stats.total_boycott} label="Boicotto" c="red" />
              <MiniStat icon={<Target className="w-3 h-3" />} value={`${stats.boycott_success_rate}%`} label="Successo" c="orange" />
              <MiniStat icon={<Shield className="w-3 h-3" />} value={stats.attacks_received} label="Subiti" c="purple" />
            </div>
          )}
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1.5 px-4 mb-3">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${tab === t.id ? 'bg-red-500/15 text-red-400 border border-red-500/25' : 'bg-white/5 text-gray-500 border border-transparent'}`}
            data-testid={`pvp-tab-${t.id}`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      <div className="px-4">
        {/* ARENA TAB */}
        {tab === 'arena' && arenaData && (
          <div className="space-y-4">
            {/* Prossimamente Section */}
            {(() => {
              const upcoming = Object.values(arenaData.genre_sections).flatMap(s => s.films.filter(f => f.film_status === 'coming_soon' || f.film_status === 'in_aggiornamento' || f.film_status === 'anteprima'));
              if (upcoming.length === 0) return null;
              return (
                <div data-testid="arena-prossimamente">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-4 h-4 text-yellow-400" />
                    <span className="text-xs font-bold text-yellow-400">Prossimamente</span>
                    <span className="text-[9px] text-gray-600 bg-white/5 px-1.5 py-0.5 rounded">{upcoming.length}</span>
                  </div>
                  <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
                    {upcoming.map(film => (
                      <FilmMiniCard key={film.id} film={film} onClick={() => openFilm(film.id)} userId={user?.id} />
                    ))}
                  </div>
                </div>
              );
            })()}

            {Object.entries(arenaData.genre_sections).map(([gid, section]) => {
              if (section.films.length === 0) return null;
              const colors = GROUP_COLORS[section.color] || GROUP_COLORS.red;
              const GroupIcon = ICON_MAP[section.icon] || Flame;
              return (
                <div key={gid} data-testid={`genre-section-${gid}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-6 h-6 rounded-md ${colors.bg} flex items-center justify-center`}>
                      <GroupIcon className={`w-3.5 h-3.5 ${colors.text}`} />
                    </div>
                    <span className={`text-xs font-bold ${colors.text}`}>{section.name}</span>
                    <span className="text-[9px] text-gray-600 bg-white/5 px-1.5 py-0.5 rounded">{section.films.length}</span>
                  </div>
                  <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
                    {section.films.map(film => (
                      <FilmMiniCard key={film.id} film={film} onClick={() => openFilm(film.id)} userId={user?.id} />
                    ))}
                  </div>
                </div>
              );
            })}
            {Object.values(arenaData.genre_sections).every(s => s.films.length === 0) && (
              <div className="text-center py-16 text-gray-600">
                <Swords className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p className="text-sm">L'arena e' vuota</p>
                <p className="text-[11px] text-gray-700 mt-1">Rilascia un film per iniziare!</p>
              </div>
            )}
          </div>
        )}


        {/* ARENA MIRATA TAB */}
        {tab === 'mirata' && (
          <div className="space-y-4" data-testid="arena-mirata-tab">
            {/* Attack Result Banner */}
            <AnimatePresence>
              {arenaAttackResult && (
                <motion.div initial={{opacity:0,y:-10}} animate={{opacity:1,y:0}} exit={{opacity:0}}
                  className={`p-3 rounded-xl border ${arenaAttackResult.blocked ? 'bg-yellow-500/10 border-yellow-500/20' : arenaAttackResult.success ? 'bg-red-500/10 border-red-500/20' : 'bg-gray-500/10 border-gray-500/15'}`}>
                  <div className="flex items-start gap-2">
                    {arenaAttackResult.blocked ? <Shield className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5"/> : arenaAttackResult.success ? <Bomb className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5"/> : <AlertTriangle className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5"/>}
                    <div>
                      <p className="text-xs text-white font-semibold">{arenaAttackResult.message}</p>
                      {arenaAttackResult.defense_log?.map((d,i) => (<p key={i} className="text-[10px] text-gray-400 mt-0.5">{d}</p>))}
                      {arenaAttackResult.effects && !arenaAttackResult.blocked && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {arenaAttackResult.effects.revenue_loss && <span className="text-[9px] px-1 py-0.5 rounded bg-red-500/15 text-red-400">-${arenaAttackResult.effects.revenue_loss.toLocaleString()}</span>}
                          {arenaAttackResult.effects.fame_mod && <span className="text-[9px] px-1 py-0.5 rounded bg-red-500/15 text-red-400">Fama {arenaAttackResult.effects.fame_mod}</span>}
                          {arenaAttackResult.effects.hype_mod && <span className="text-[9px] px-1 py-0.5 rounded bg-red-500/15 text-red-400">Hype {arenaAttackResult.effects.hype_mod}</span>}
                        </div>
                      )}
                    </div>
                    <button onClick={() => setArenaAttackResult(null)} className="ml-auto text-gray-500 hover:text-white"><X className="w-3.5 h-3.5"/></button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Cost info */}
            {arenaTargets && (
              <div className="flex items-center gap-2 p-2 bg-red-500/5 rounded-lg border border-red-500/10">
                <Target className="w-4 h-4 text-red-400"/>
                <span className="text-[10px] text-gray-400">Costo attacco: <span className="text-red-400 font-bold">{arenaTargets.attack_cost_cp} CP</span> | Cooldown: 12h per target | Richiede Div. Operativa</span>
              </div>
            )}

            {/* Targets */}
            {arenaTargets?.targets?.length > 0 ? (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-red-400 uppercase">Bersagli Disponibili ({arenaTargets.targets.length})</h4>
                {arenaTargets.targets.map(t => (
                  <div key={t.user_id} className="p-3 bg-white/[0.03] rounded-xl border border-white/8" data-testid={`arena-target-${t.user_id}`}>
                    <div className="flex items-center gap-2 mb-2">
                      {t.avatar_url ? <img src={t.avatar_url} alt="" className="w-8 h-8 rounded-full bg-gray-700"/> : <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center"><Users className="w-4 h-4 text-gray-500"/></div>}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-white truncate">{t.nickname}</p>
                        <p className="text-[9px] text-gray-500">{t.production_house || 'Studio'} | Lv.{t.level} | Fama {t.fame} | {t.infra_count} infra</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {t.available_categories.map(cat => {
                        const catColors = {cinema:'from-yellow-600 to-orange-600',tv:'from-cyan-600 to-blue-600',commerciale:'from-green-600 to-emerald-600',agenzie:'from-purple-600 to-pink-600'};
                        const isAttacking = attackingTarget === `${t.user_id}_${cat.id}`;
                        return (
                          <Button key={cat.id} size="sm" disabled={isAttacking}
                            onClick={() => executeArenaAttack(t.user_id, cat.id)}
                            className={`h-8 text-[10px] font-bold bg-gradient-to-r ${catColors[cat.id] || 'from-red-600 to-orange-600'} hover:opacity-90`}
                            data-testid={`arena-attack-${t.user_id}-${cat.id}`}>
                            {isAttacking ? <Loader2 className="w-3 h-3 animate-spin mr-1"/> : <Target className="w-3 h-3 mr-1"/>}
                            {cat.label}
                          </Button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-600">
                <Target className="w-10 h-10 mx-auto mb-2 opacity-20"/>
                <p className="text-sm">Nessun bersaglio disponibile</p>
                <p className="text-[10px] text-gray-700 mt-1">I player con infrastrutture appariranno qui</p>
              </div>
            )}

            {/* Arena Attack History */}
            {arenaHistory?.attacks?.length > 0 && (
              <div className="space-y-2 mt-3">
                <h4 className="text-xs font-bold text-gray-400 uppercase">Cronologia Attacchi Mirati</h4>
                {arenaHistory.attacks.slice(0, 8).map((a, i) => (
                  <div key={a.id || i} className={`flex items-center gap-2 p-2 rounded-lg border ${a.is_attacker ? (a.blocked ? 'bg-yellow-500/5 border-yellow-500/10' : 'bg-red-500/5 border-red-500/10') : 'bg-orange-500/5 border-orange-500/10'}`}>
                    {a.blocked ? <Shield className="w-3.5 h-3.5 text-yellow-400"/> : a.is_attacker ? <Bomb className="w-3.5 h-3.5 text-red-400"/> : <AlertTriangle className="w-3.5 h-3.5 text-orange-400"/>}
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] font-semibold text-white truncate">{a.is_attacker ? `Tu -> ${a.other_nickname}` : `${a.other_nickname} -> Te`} ({a.category})</p>
                      <p className="text-[9px] text-gray-500">{a.blocked ? 'Bloccato' : 'Riuscito'}</p>
                    </div>
                    <span className="text-[8px] text-gray-600">{a.created_at ? new Date(a.created_at).toLocaleDateString('it-IT') : ''}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* REPORT TAB */}
        {tab === 'report' && (
          <div className="space-y-3">
            {history?.stats && (
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="bg-emerald-500/10 border border-emerald-500/15 rounded-lg p-2 text-center">
                  <p className="text-lg font-bold text-emerald-400">+{history.stats.total_bonus_given}%</p>
                  <p className="text-[9px] text-gray-500">Bonus dati</p>
                </div>
                <div className="bg-red-500/10 border border-red-500/15 rounded-lg p-2 text-center">
                  <p className="text-lg font-bold text-red-400">-{history.stats.total_damage_dealt}%</p>
                  <p className="text-[9px] text-gray-500">Danni inflitti</p>
                </div>
                <div className="bg-orange-500/10 border border-orange-500/15 rounded-lg p-2 text-center">
                  <p className="text-lg font-bold text-orange-400">{history.stats.boycott_success_rate}%</p>
                  <p className="text-[9px] text-gray-500">% Successo</p>
                </div>
              </div>
            )}

            {history?.against_me?.length > 0 && (
              <div>
                <h3 className="text-[11px] font-bold text-red-400 uppercase mb-2">Attacchi Subiti</h3>
                {history.against_me.slice(0, 5).map((a, i) => (
                  <ActionHistoryRow key={a.id || i} action={a} isIncoming />
                ))}
              </div>
            )}

            <div>
              <h3 className="text-[11px] font-bold text-gray-400 uppercase mb-2">Le Tue Azioni</h3>
              {(!history?.my_actions || history.my_actions.length === 0) && (
                <p className="text-xs text-gray-600 text-center py-6">Nessuna azione ancora</p>
              )}
              {history?.my_actions?.map((a, i) => (
                <ActionHistoryRow key={a.id || i} action={a} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Film Detail + Action Modal */}
      <Dialog open={!!selectedFilm} onOpenChange={() => { setSelectedFilm(null); setFilmDetail(null); setActionResult(null); }}>
        <DialogContent className="bg-[#111113] border-white/10 max-w-md max-h-[85vh] overflow-y-auto p-0" style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
          {filmDetail && (
            <FilmActionPanel
              film={filmDetail}
              arenaData={arenaData}
              actionResult={actionResult}
              loading={loading}
              onAction={executeAction}
              onDefend={executeDefend}
              onClose={() => { setSelectedFilm(null); setFilmDetail(null); setActionResult(null); }}
            />
          )}
        </DialogContent>
      </Dialog>

      {outcomePopup && (
        <OutcomePopup
          open={!!outcomePopup}
          onClose={() => setOutcomePopup(null)}
          outcomeType={outcomePopup.type}
          title={outcomePopup.title}
          message={outcomePopup.message}
        />
      )}
    </div>
  );
}

/* ============ MINI STAT ============ */
function MiniStat({ icon, value, label, c }) {
  const cls = {
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/15',
    red: 'text-red-400 bg-red-500/10 border-red-500/15',
    orange: 'text-orange-400 bg-orange-500/10 border-orange-500/15',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/15',
  };
  return (
    <div className={`flex-1 p-1.5 rounded-lg border ${cls[c]}`}>
      <div className="flex items-center gap-1">{icon}<span className="text-[8px] text-gray-500">{label}</span></div>
      <p className="text-sm font-bold">{value}</p>
    </div>
  );
}

/* ============ FILM MINI CARD ============ */
function FilmMiniCard({ film, onClick, userId }) {
  const isMine = film.user_id === userId;
  const st = STATUS_LABELS[film.film_status] || STATUS_LABELS.in_sala;
  const API_URL = process.env.REACT_APP_BACKEND_URL;

  // Hype-based border glow
  const hype = film.hype_score || 0;
  const hypeBorder = hype >= 30 ? 'ring-1 ring-orange-500/40' : hype < 10 && hype > 0 ? 'ring-1 ring-red-500/30' : '';

  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`flex-shrink-0 w-[100px] rounded-xl overflow-hidden border transition-all ${isMine ? 'border-yellow-500/30 bg-yellow-500/5' : 'border-white/8 bg-white/[0.03]'} hover:border-white/20 ${hypeBorder}`}
      data-testid={`arena-film-${film.id}`}
    >
      {/* Poster */}
      <div className="relative w-full h-[130px] bg-gray-900">
        {film.poster_url ? (
          <img
            src={film.poster_url?.startsWith('http') ? film.poster_url : `${API_URL}${film.poster_url}`}
            alt={film.title}
            className="w-full h-full object-cover"
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Film className="w-6 h-6 text-gray-700" />
          </div>
        )}
        {/* Status badge */}
        <div className={`absolute top-1 left-1 px-1 py-0.5 rounded text-[7px] font-bold ${st.color}`}>
          {st.label}
        </div>
        {isMine && (
          <div className="absolute top-1 right-1 w-4 h-4 rounded-full bg-yellow-500/90 flex items-center justify-center">
            <Star className="w-2.5 h-2.5 text-black" />
          </div>
        )}
        {/* PvP modifier */}
        {film.pvp_revenue_modifier && film.pvp_revenue_modifier !== 0 && (
          <div className={`absolute bottom-1 right-1 px-1 py-0.5 rounded text-[7px] font-bold ${film.pvp_revenue_modifier > 0 ? 'bg-green-500/80 text-white' : 'bg-red-500/80 text-white'}`}>
            {film.pvp_revenue_modifier > 0 ? '+' : ''}{film.pvp_revenue_modifier.toFixed(1)}%
          </div>
        )}
      </div>
      <div className="p-1.5">
        <p className="text-[10px] font-semibold text-white truncate leading-tight">{film.title}</p>
        <p className="text-[8px] text-gray-500 truncate">{isMine ? 'Il tuo' : film.nickname}</p>
      </div>
    </motion.button>
  );
}

/* ============ FILM ACTION PANEL ============ */
function FilmActionPanel({ film, arenaData, actionResult, loading, onAction, onDefend, onClose }) {
  const [actionTab, setActionTab] = useState('support');
  const st = STATUS_LABELS[film.film_status] || STATUS_LABELS.in_sala;
  const API_URL = process.env.REACT_APP_BACKEND_URL;

  const supportTypes = arenaData?.support_types || {};
  const boycottTypes = arenaData?.boycott_types || {};

  // Check if there are undefended boycotts against this film
  const hasUndefendedAttack = film.is_mine && film.recent_actions?.some(a => a.category === 'boycott' && a.success);

  return (
    <div data-testid="film-action-panel">
      {/* Header with poster */}
      <div className="relative h-48 overflow-hidden">
        {film.poster_url ? (
          <img
            src={film.poster_url?.startsWith('http') ? film.poster_url : `${API_URL}${film.poster_url}`}
            alt={film.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-b from-gray-800 to-gray-900 flex items-center justify-center">
            <Film className="w-12 h-12 text-gray-700" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-[#111113] via-[#111113]/60 to-transparent" />
        <div className="absolute bottom-3 left-4 right-4">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${st.color}`}>{st.label}</span>
            {film.is_mine && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold text-yellow-400 bg-yellow-500/15">IL TUO</span>}
          </div>
          <h2 className="text-base font-bold text-white leading-tight">{film.title}</h2>
          <p className="text-[10px] text-gray-400">{film.owner_nickname} {film.owner_studio ? `- ${film.owner_studio}` : ''}</p>
        </div>
      </div>

      <div className="px-4 pb-4">
        {/* Film Stats */}
        <div className="grid grid-cols-4 gap-1.5 my-3">
          <FilmStatBox label="Qualita" value={film.quality_score?.toFixed(0) || '?'} color="text-cyan-400" />
          <FilmStatBox label="Hype" value={film.hype_score || '0'} color="text-orange-400" />
          <FilmStatBox label="Incassi" value={film.total_revenue ? `$${(film.total_revenue / 1000000).toFixed(1)}M` : (film.opening_day_revenue ? `$${(film.opening_day_revenue / 1000000).toFixed(1)}M` : '-')} color="text-green-400" />
          <FilmStatBox label="PvP" value={`${(film.pvp_revenue_modifier || 0) >= 0 ? '+' : ''}${(film.pvp_revenue_modifier || 0).toFixed(1)}%`} color={film.pvp_revenue_modifier >= 0 ? 'text-green-400' : 'text-red-400'} />
        </div>

        {/* Action Result */}
        <AnimatePresence>
          {actionResult && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={`p-3 rounded-xl mb-3 border ${actionResult.boycott_success === false ? 'bg-red-500/10 border-red-500/20' : actionResult.boycott_success === true ? 'bg-orange-500/10 border-orange-500/20' : actionResult.success ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}
              data-testid="action-result"
            >
              <div className="flex items-start gap-2">
                {actionResult.boycott_success === false ? (
                  <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                ) : actionResult.success ? (
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <X className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                )}
                <p className="text-xs text-gray-300 leading-relaxed">{actionResult.message}</p>
              </div>
              {actionResult.success_rate && (
                <p className="text-[9px] text-gray-500 mt-1 ml-6">Probabilita successo: {actionResult.success_rate}%</p>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Defend Button */}
        {hasUndefendedAttack && (
          <Button
            onClick={onDefend}
            disabled={loading}
            className="w-full mb-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white"
            data-testid="defend-btn"
          >
            <Shield className="w-4 h-4 mr-2" /> Difendi Film (2 CP)
          </Button>
        )}

        {/* Action Tabs */}
        <div className="flex gap-1 mb-3">
          <button
            onClick={() => setActionTab('boycott')}
            className={`flex-1 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${actionTab === 'boycott' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-white/5 text-gray-500'}`}
            data-testid="boycott-tab"
          >
            <Bomb className="w-3 h-3 inline mr-1" />Boicotta
          </button>
          <button
            onClick={() => setActionTab('support')}
            className={`flex-1 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${actionTab === 'support' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-white/5 text-gray-500'}`}
            data-testid="support-tab"
          >
            <Heart className="w-3 h-3 inline mr-1" />Supporto
          </button>
        </div>

        {/* Action List */}
        <div className="space-y-2">
          {actionTab === 'support' && Object.entries(supportTypes).map(([aid, cfg]) => {
            const onCooldown = film.cooldowns?.[aid];
            const ActionIcon = ICON_MAP[cfg.icon] || Heart;
            return (
              <button
                key={aid}
                onClick={() => !onCooldown && !loading && onAction('support', aid)}
                disabled={onCooldown || loading}
                className={`w-full p-2.5 rounded-xl text-left border transition-all ${onCooldown ? 'opacity-30 bg-white/[0.02] border-white/5' : 'bg-emerald-500/5 border-emerald-500/15 hover:bg-emerald-500/10 active:scale-[0.98]'}`}
                data-testid={`action-${aid}`}
              >
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/15 flex items-center justify-center flex-shrink-0">
                    {loading ? <div className="w-3 h-3 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" /> : <ActionIcon className="w-3.5 h-3.5 text-emerald-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-semibold text-white">{cfg.name}</p>
                    <p className="text-[9px] text-gray-500 truncate">{cfg.desc}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-[9px] text-emerald-400 font-bold">+{cfg.base_bonus_min}-{cfg.base_bonus_max}%</p>
                    <p className="text-[8px] text-gray-600">${(cfg.cost_funds/1000).toFixed(0)}K + {cfg.cost_cp}CP</p>
                  </div>
                </div>
                {onCooldown && <p className="text-[8px] text-gray-600 mt-1 ml-9">Cooldown attivo ({cfg.cooldown_minutes}min)</p>}
              </button>
            );
          })}

          {actionTab === 'boycott' && Object.entries(boycottTypes).map(([aid, cfg]) => {
            const onCooldown = film.cooldowns?.[aid];
            const ActionIcon = ICON_MAP[cfg.icon] || Bomb;
            return (
              <button
                key={aid}
                onClick={() => !onCooldown && !loading && !film.is_mine && onAction('boycott', aid)}
                disabled={onCooldown || loading || film.is_mine}
                className={`w-full p-2.5 rounded-xl text-left border transition-all ${onCooldown ? 'opacity-30 bg-white/[0.02] border-white/5' : 'bg-red-500/5 border-red-500/15 hover:bg-red-500/10'}`}
                data-testid={`action-${aid}`}
              >
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-red-500/15 flex items-center justify-center flex-shrink-0">
                    <ActionIcon className="w-3.5 h-3.5 text-red-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-semibold text-white">{cfg.name}</p>
                    <p className="text-[9px] text-gray-500 truncate">{cfg.desc}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-[9px] text-red-400 font-bold">-{cfg.base_damage_min}-{cfg.base_damage_max}%</p>
                    <p className="text-[8px] text-yellow-500/70">Successo ~{cfg.success_base}%</p>
                    <p className="text-[8px] text-gray-600">${(cfg.cost_funds/1000).toFixed(0)}K + {cfg.cost_cp}CP</p>
                  </div>
                </div>
                {onCooldown && <p className="text-[8px] text-gray-600 mt-1 ml-9">Cooldown attivo ({cfg.cooldown_minutes}min)</p>}
                {!onCooldown && !film.is_mine && (
                  <div className="flex items-center gap-1 mt-1 ml-9">
                    <AlertTriangle className="w-2.5 h-2.5 text-yellow-500/50" />
                    <p className="text-[8px] text-yellow-500/50">Ritorsione: -{cfg.backfire_min}-{cfg.backfire_max}% sui tuoi film</p>
                  </div>
                )}
              </button>
            );
          })}

        </div>

        {/* Recent Actions on this film */}
        {film.recent_actions?.length > 0 && (
          <div className="mt-4">
            <h4 className="text-[10px] font-bold text-gray-500 uppercase mb-1.5">Azioni recenti su questo film</h4>
            {film.recent_actions.map((a, i) => (
              <div key={i} className={`flex items-center gap-2 py-1.5 border-b border-white/5 ${a.success ? (a.category === 'support' ? 'text-emerald-400' : 'text-red-400') : 'text-gray-500'}`}>
                {a.category === 'support' ? <Heart className="w-3 h-3" /> : <Bomb className="w-3 h-3" />}
                <span className="text-[10px] flex-1">{a.action_name}</span>
                <span className="text-[9px]">{a.success ? `${a.effect_pct > 0 ? '+' : ''}${a.effect_pct?.toFixed(1)}%` : 'Fallito'}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function FilmStatBox({ label, value, color }) {
  return (
    <div className="bg-white/5 rounded-lg p-1.5 text-center border border-white/5">
      <p className={`text-sm font-bold ${color}`}>{value}</p>
      <p className="text-[8px] text-gray-500">{label}</p>
    </div>
  );
}

function ActionHistoryRow({ action, isIncoming }) {
  const isSupport = action.category === 'support';
  const isSuccess = action.success;
  const timeAgo = (ts) => {
    if (!ts) return '';
    const d = (Date.now() - new Date(ts).getTime()) / 60000;
    if (d < 60) return `${Math.round(d)}m fa`;
    if (d < 1440) return `${Math.round(d/60)}h fa`;
    return `${Math.round(d/1440)}g fa`;
  };

  return (
    <div className={`flex items-center gap-2 p-2 rounded-lg mb-1.5 border ${isIncoming ? 'bg-red-500/5 border-red-500/10' : isSupport ? 'bg-emerald-500/5 border-emerald-500/10' : (isSuccess ? 'bg-orange-500/5 border-orange-500/10' : 'bg-gray-500/5 border-gray-500/10')}`}>
      {isSupport ? <Heart className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" /> : isSuccess ? <Bomb className="w-3.5 h-3.5 text-red-400 flex-shrink-0" /> : <AlertTriangle className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />}
      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-semibold text-white truncate">
          {isIncoming ? `${action.attacker_nickname || '?'} -> ` : ''}{action.action_name}
        </p>
        <p className="text-[9px] text-gray-500 truncate">{action.target_film_title}</p>
      </div>
      <div className="text-right flex-shrink-0">
        <p className={`text-[10px] font-bold ${isSuccess ? (isSupport ? 'text-emerald-400' : 'text-red-400') : 'text-gray-500'}`}>
          {isSuccess ? `${action.effect_pct > 0 ? '+' : ''}${action.effect_pct?.toFixed(1)}%` : 'Fallito'}
        </p>
        <p className="text-[8px] text-gray-600">{timeAgo(action.created_at)}</p>
      </div>
    </div>
  );
}
