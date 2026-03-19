// CineWorld - Anime Pipeline
// Full production pipeline for anime series

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Sparkles, ArrowRight, Users, Pen, Play, Lock, Loader2, Trash2, Check, Star } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

const STEPS = [
  { id: 'concept', label: 'Concept', icon: Sparkles, color: 'orange' },
  { id: 'casting', label: 'Casting', icon: Users, color: 'pink' },
  { id: 'screenplay', label: 'Sceneggiatura', icon: Pen, color: 'cyan' },
  { id: 'production', label: 'Produzione', icon: Play, color: 'amber' },
  { id: 'completed', label: 'Completato', icon: Star, color: 'yellow' },
];

const STATUS_TO_STEP = { concept: 0, casting: 1, screenplay: 2, production: 3, ready_to_release: 3, completed: 4 };

export default function AnimePipeline() {
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [genres, setGenres] = useState({});
  const [mySeries, setMySeries] = useState([]);
  const [activeSeries, setActiveSeries] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const [title, setTitle] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [numEpisodes, setNumEpisodes] = useState(12);
  const [description, setDescription] = useState('');
  const [availableActors, setAvailableActors] = useState([]);
  const [selectedCast, setSelectedCast] = useState([]);
  const [prodStatus, setProdStatus] = useState(null);
  const [castingMode, setCastingMode] = useState(null);
  const [agencyActors, setAgencyActors] = useState({ effective: [], school: [] });
  const [agencyInfo, setAgencyInfo] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [genresRes, seriesRes] = await Promise.all([
        api.get('/series-pipeline/genres?series_type=anime'),
        api.get('/series-pipeline/my?series_type=anime'),
      ]);
      setGenres(genresRes.data.genres || {});
      setMySeries(seriesRes.data.series || []);
      const inProgress = (seriesRes.data.series || []).find(s => !['completed', 'cancelled'].includes(s.status));
      if (inProgress) setActiveSeries(inProgress);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    if (activeSeries?.status === 'casting') {
      api.get(`/series-pipeline/${activeSeries.id}/available-actors`).then(r => {
        setAvailableActors(r.data.actors || []);
      }).catch(() => {});
      api.get('/agency/actors-for-casting').then(r => {
        setAgencyActors({ effective: r.data.effective_actors || [], school: r.data.school_students || [] });
        setAgencyInfo(r.data);
      }).catch(() => {});
    }
  }, [activeSeries?.status, activeSeries?.id, api]);

  useEffect(() => {
    if (activeSeries?.status === 'production') {
      const poll = () => {
        api.get(`/series-pipeline/${activeSeries.id}/production-status`).then(r => {
          setProdStatus(r.data);
          if (r.data.complete) setActiveSeries(prev => ({ ...prev, status: 'ready_to_release' }));
        }).catch(() => {});
      };
      poll();
      const interval = setInterval(poll, 10000);
      return () => clearInterval(interval);
    }
  }, [activeSeries?.status, activeSeries?.id, api]);

  const createSeries = async () => {
    if (!title.trim() || !selectedGenre) return toast.error('Inserisci titolo e genere');
    setActionLoading(true);
    try {
      const res = await api.post('/series-pipeline/create', {
        title, genre: selectedGenre, num_episodes: numEpisodes,
        series_type: 'anime', description
      });
      toast.success(`"${title}" creato! Costo: $${res.data.cost?.toLocaleString()}`);
      setActiveSeries(res.data.series);
      setTitle(''); setDescription('');
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const advanceToCasting = async () => {
    setActionLoading(true);
    try {
      await api.post(`/series-pipeline/${activeSeries.id}/advance-to-casting`);
      setActiveSeries(prev => ({ ...prev, status: 'casting' }));
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const selectCast = async () => {
    if (selectedCast.length === 0) return toast.error('Seleziona almeno una guest star');
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/select-cast`, {
        cast: selectedCast.map(c => ({ actor_id: c.actor_id, role: c.role || 'Guest Star Vocale' }))
      });
      toast.success(`Guest Star ingaggiate! Costo: $${res.data.total_salary?.toLocaleString()}`);
      setActiveSeries(prev => ({ ...prev, cast: res.data.cast }));
      setSelectedCast([]);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const submitAgencyCastAnime = async () => {
    const selected = selectedCast.filter(c => c.is_agency);
    if (selected.length === 0) return toast.error("Seleziona almeno un attore dall'agenzia");
    setActionLoading(true);
    try {
      const res = await api.post(`/agency/cast-for-series/${activeSeries.id}`, {
        actor_ids: selected.map(c => ({ actor_id: c.actor_id, role: c.role, source: c.source || 'effective' }))
      });
      toast.success(res.data.message);
      setActiveSeries(prev => ({ ...prev, cast: res.data.cast }));
      setSelectedCast([]);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const advanceToScreenplay = async () => {
    setActionLoading(true);
    try {
      await api.post(`/series-pipeline/${activeSeries.id}/advance-to-screenplay`);
      setActiveSeries(prev => ({ ...prev, status: 'screenplay' }));
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const writeScreenplay = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/write-screenplay`, { mode: 'ai' }, { timeout: 120000 });
      setActiveSeries(prev => ({ ...prev, screenplay: { text: res.data.screenplay } }));
      toast.success('Sceneggiatura generata!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const startProduction = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/start-production`);
      setActiveSeries(prev => ({ ...prev, status: 'production', production_duration_minutes: res.data.duration_minutes }));
      toast.success(`Produzione avviata! Durata: ${res.data.duration_minutes} minuti`);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const releaseSeries = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/release`);
      toast.success(`Anime completato! Qualità: ${res.data.quality?.score}/100 (+${res.data.xp_reward} XP)`);
      setActiveSeries(null);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const discardSeries = async () => {
    if (!window.confirm('Vuoi cancellare questo anime? Rimborso 50%.')) return;
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/discard`);
      toast.success(`Anime cancellato. Rimborso: $${res.data.refund?.toLocaleString()}`);
      setActiveSeries(null);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const toggleCastMember = (actor, role) => {
    setSelectedCast(prev => {
      const exists = prev.find(c => c.actor_id === actor.id);
      if (exists) return prev.filter(c => c.actor_id !== actor.id);
      return [...prev, { actor_id: actor.id, name: actor.name, role, skill: actor.skill }];
    });
  };

  const currentStep = activeSeries ? (STATUS_TO_STEP[activeSeries.status] ?? 0) : -1;

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-orange-400 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
      <div className="max-w-2xl mx-auto px-3">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4 mt-2">
          <div className="p-2.5 bg-orange-500/20 rounded-xl border border-orange-500/30">
            <Sparkles className="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <h1 className="font-['Bebas_Neue'] text-2xl text-orange-400" data-testid="anime-pipeline-title">Pipeline Anime</h1>
            <p className="text-xs text-gray-500">Produci il tuo anime originale</p>
          </div>
        </div>

        {/* Step Progress */}
        {activeSeries && (
          <div className="flex items-center gap-1 mb-4 px-1" data-testid="anime-steps">
            {STEPS.map((step, i) => (
              <React.Fragment key={step.id}>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-semibold transition-all ${
                  i === currentStep ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                  i < currentStep ? 'bg-white/5 text-gray-400' : 'bg-white/[0.02] text-gray-600'
                }`}>
                  {i < currentStep ? <Check className="w-3 h-3" /> : <step.icon className="w-3 h-3" />}
                  <span className="hidden sm:inline">{step.label}</span>
                </div>
                {i < STEPS.length - 1 && <div className={`flex-1 h-px ${i < currentStep ? 'bg-white/20' : 'bg-white/5'}`} />}
              </React.Fragment>
            ))}
          </div>
        )}

        {!activeSeries ? (
          <div className="space-y-4">
            <Card className="bg-[#111113] border-orange-500/20" data-testid="create-anime-form">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg font-['Bebas_Neue'] text-orange-400">Nuovo Anime</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input placeholder="Titolo dell'anime" value={title} onChange={e => setTitle(e.target.value)} className="bg-white/5 border-white/10 text-white" data-testid="anime-title-input" />
                <div>
                  <label className="text-xs text-gray-400 mb-1.5 block">Genere</label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {Object.entries(genres).map(([key, g]) => (
                      <button key={key}
                        className={`px-3 py-2 rounded-lg text-xs font-medium transition-all text-left ${selectedGenre === key ? 'bg-orange-500 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10 border border-white/5'}`}
                        onClick={() => { setSelectedGenre(key); setNumEpisodes(g.ep_range[0]); }}
                        data-testid={`anime-genre-${key}`}
                      >
                        <span className="block font-semibold">{g.name_it}</span>
                        {g.desc && <span className="block text-[9px] opacity-70 mt-0.5">{g.desc}</span>}
                      </button>
                    ))}
                  </div>
                </div>
                {selectedGenre && (
                  <div>
                    <label className="text-xs text-gray-400 mb-1 block">
                      Episodi ({genres[selectedGenre]?.ep_range[0]}-{genres[selectedGenre]?.ep_range[1]})
                    </label>
                    <div className="flex items-center gap-2">
                      <input type="range"
                        min={genres[selectedGenre]?.ep_range[0]}
                        max={genres[selectedGenre]?.ep_range[1]}
                        value={numEpisodes}
                        onChange={e => setNumEpisodes(parseInt(e.target.value))}
                        className="flex-1 accent-orange-500"
                        data-testid="anime-episodes-slider"
                      />
                      <span className="text-sm font-bold text-orange-400 w-8 text-center">{numEpisodes}</span>
                    </div>
                    <p className="text-[10px] text-gray-500 mt-1">
                      Costo: ${((numEpisodes * 80000 * (genres[selectedGenre]?.cost_mult || 1))).toLocaleString()} | Produzione: {numEpisodes * 12} min
                    </p>
                  </div>
                )}
                <Input placeholder="Descrizione (opzionale)" value={description} onChange={e => setDescription(e.target.value)} className="bg-white/5 border-white/10 text-white" data-testid="anime-description-input" />
                <Button className="w-full bg-orange-500 hover:bg-orange-600 text-white" onClick={createSeries} disabled={actionLoading || !title.trim() || !selectedGenre} data-testid="create-anime-btn">
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                  Crea Anime
                </Button>
              </CardContent>
            </Card>

            {mySeries.filter(s => s.status === 'completed').length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Anime Completati</h3>
                <div className="space-y-2">
                  {mySeries.filter(s => s.status === 'completed').map(s => (
                    <Card key={s.id} className="bg-[#111113] border-white/5" data-testid={`completed-anime-${s.id}`}>
                      <CardContent className="p-3 flex items-center gap-3">
                        {s.poster_url && <img src={posterSrc(s.poster_url)} alt="" className="w-12 h-16 rounded object-cover" loading="lazy" />}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-bold truncate">{s.title}</p>
                          <p className="text-[10px] text-gray-500">{s.genre_name} - {s.num_episodes} ep.</p>
                        </div>
                        <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">{s.quality_score}/100</Badge>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3" data-testid="active-anime-pipeline">
            {/* Anime Header */}
            <Card className="bg-[#111113] border-orange-500/20">
              <CardContent className="p-3 flex items-center gap-3">
                {activeSeries.poster_url ? (
                  <img src={posterSrc(activeSeries.poster_url)} alt="" className="w-16 h-24 rounded-lg object-cover" />
                ) : (
                  <div className="w-16 h-24 rounded-lg bg-orange-500/10 flex items-center justify-center border border-orange-500/20">
                    <Sparkles className="w-8 h-8 text-orange-400/50" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg font-bold truncate" data-testid="active-anime-title">{activeSeries.title}</h2>
                  <p className="text-xs text-gray-400">{activeSeries.genre_name} - {activeSeries.num_episodes} episodi</p>
                  <Badge className="bg-orange-500/20 text-orange-400 text-[10px] mt-1">{activeSeries.status}</Badge>
                </div>
                <button onClick={discardSeries} className="p-2 text-red-400/60 hover:text-red-400" data-testid="discard-anime-btn">
                  <Trash2 className="w-4 h-4" />
                </button>
              </CardContent>
            </Card>

            {/* CONCEPT */}
            {activeSeries.status === 'concept' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <Card className="bg-[#111113] border-orange-500/10">
                  <CardContent className="p-4 text-center space-y-3">
                    <Sparkles className="w-10 h-10 text-orange-400 mx-auto" />
                    <p className="text-sm text-gray-300">Il concept dell'anime è pronto! Procedi al casting.</p>
                    <Button className="w-full bg-orange-500 hover:bg-orange-600" onClick={advanceToCasting} disabled={actionLoading} data-testid="anime-advance-casting-btn">
                      Vai al Casting <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* CASTING */}
            {activeSeries.status === 'casting' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                {activeSeries.cast?.length > 0 && (
                  <Card className="bg-[#111113] border-pink-500/10">
                    <CardHeader className="pb-1"><CardTitle className="text-sm text-pink-400">Cast Selezionato</CardTitle></CardHeader>
                    <CardContent className="p-3 pt-0">
                      {activeSeries.cast.map((c, i) => (
                        <div key={i} className="flex items-center justify-between text-xs bg-pink-500/5 rounded-lg px-2 py-1.5 mb-1">
                          <span className="font-medium">{c.name}</span>
                          <div className="flex items-center gap-1">
                            <Badge className="text-[9px] bg-white/5">{c.role}</Badge>
                            {c.is_agency_actor && <Badge className="text-[7px] bg-purple-500/20 text-purple-400">Agenzia</Badge>}
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* Casting mode choice - Anime: Guest Star Vocali */}
                {!castingMode && (
                  <div className="p-3 rounded-lg border border-pink-500/20 bg-pink-500/5 space-y-2" data-testid="anime-casting-mode-choice">
                    <p className="text-xs font-semibold text-pink-300">Guest Star Vocali (Opzionale)</p>
                    <p className="text-[9px] text-gray-400">Ingaggia attori famosi per dare la voce ai personaggi! Costa molto ma migliora qualità e fama.</p>
                    <div className="grid grid-cols-2 gap-2">
                      {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                        <Button size="sm" className="h-auto py-2 bg-purple-600 hover:bg-purple-700 text-left flex-col items-start"
                          onClick={() => setCastingMode('agency')} data-testid="anime-cast-agency">
                          <span className="text-xs font-semibold flex items-center gap-1"><Users className="w-3.5 h-3.5" /> Dalla tua Agenzia</span>
                          <span className="text-[9px] text-purple-200/70 mt-0.5">{agencyActors.effective.length + agencyActors.school.length} attori</span>
                        </Button>
                      )}
                      <Button size="sm" className="h-auto py-2 bg-pink-600 hover:bg-pink-700 text-left flex-col items-start"
                        onClick={() => setCastingMode('market')} data-testid="anime-cast-market">
                        <span className="text-xs font-semibold flex items-center gap-1"><Star className="w-3.5 h-3.5" /> Guest Star Famose</span>
                        <span className="text-[9px] text-pink-200/70 mt-0.5">Solo attori celebri</span>
                      </Button>
                    </div>
                    <Button size="sm" variant="outline" className="w-full text-xs text-gray-400 border-white/10 hover:bg-white/5 mt-1"
                      onClick={advanceToScreenplay} disabled={actionLoading} data-testid="anime-skip-casting">
                      {actionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <ArrowRight className="w-3.5 h-3.5 mr-1" />}
                      Procedi senza Guest Star
                    </Button>
                  </div>
                )}

                {/* Agency casting for anime */}
                {castingMode === 'agency' && (
                  <Card className="bg-[#111113] border-purple-500/10">
                    <CardHeader className="pb-1">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm text-purple-400">I tuoi Attori come Guest Star</CardTitle>
                        <Button size="sm" variant="ghost" className="h-6 text-[9px] text-gray-400" onClick={() => setCastingMode('market')}>Guest Star dal Mercato</Button>
                      </div>
                    </CardHeader>
                    <CardContent className="p-3 pt-0">
                      <div className="space-y-1.5 max-h-60 overflow-y-auto">
                        {[...agencyActors.effective.map(a => ({...a, _source: 'effective'})), ...agencyActors.school.map(a => ({...a, _source: 'school'}))].map(actor => {
                          const alreadyCast = activeSeries.cast?.some(c => c.actor_id === actor.id);
                          const isSelected = selectedCast.find(c => c.actor_id === actor.id);
                          const skills = actor.skills || {};
                          const avgSkill = Object.values(skills).length > 0
                            ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;
                          return (
                            <div key={actor.id} className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer border ${
                              alreadyCast ? 'bg-green-500/5 border-green-500/20 opacity-60' : isSelected ? 'bg-purple-500/15 border-purple-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-white/5'
                            }`} onClick={() => !alreadyCast && setSelectedCast(prev => {
                              const exists = prev.find(c => c.actor_id === actor.id);
                              if (exists) return prev.filter(c => c.actor_id !== actor.id);
                              return [...prev, { actor_id: actor.id, name: actor.name, role: 'Guest Star Vocale', is_agency: true, source: actor._source }];
                            })} data-testid={`anime-agency-actor-${actor.id}`}>
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${actor._source === 'school' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-purple-500/20 text-purple-400'}`}>
                                {actor.name?.charAt(0)}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1">
                                  <p className="text-xs font-medium truncate">{actor.name}</p>
                                  {actor._source === 'school' && <Badge className="text-[7px] bg-cyan-500/15 text-cyan-400 h-3.5">Studente</Badge>}
                                  <Badge className="text-[7px] bg-pink-500/15 text-pink-400 h-3.5">Guest Star</Badge>
                                </div>
                                <div className="flex items-center gap-1 flex-wrap">
                                  <span className="text-[9px] text-gray-500">Skill: {avgSkill}</span>
                                  {(actor.strong_genres_names || []).map((g, i) => <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                                </div>
                              </div>
                              {isSelected && <Check className="w-4 h-4 text-purple-400" />}
                              {alreadyCast && <Badge className="text-[8px] bg-green-500/20 text-green-400">Nel cast</Badge>}
                            </div>
                          );
                        })}
                      </div>
                      {selectedCast.filter(c => c.is_agency).length > 0 && (
                        <Button className="w-full mt-2 bg-purple-500 hover:bg-purple-600" onClick={submitAgencyCastAnime} disabled={actionLoading} data-testid="anime-confirm-agency-cast">
                          {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Users className="w-4 h-4 mr-2" />}
                          Conferma Guest Star dall'Agenzia ({selectedCast.filter(c => c.is_agency).length})
                        </Button>
                      )}
                      <p className="text-[9px] text-amber-400 mt-1">Bonus: +20-70% XP e Fama con i tuoi attori!</p>
                      <Button size="sm" variant="outline" className="w-full text-[10px] text-gray-400 border-white/10 hover:bg-white/5 mt-2"
                        onClick={advanceToScreenplay} disabled={actionLoading}>
                        Procedi senza altre Guest Star <ArrowRight className="w-3 h-3 ml-1" />
                      </Button>
                    </CardContent>
                  </Card>
                )}

                {/* Market casting — Guest Star Famose */}
                {castingMode === 'market' && (
                <Card className="bg-[#111113] border-pink-500/10">
                  <CardHeader className="pb-1">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm text-pink-400">Guest Star Vocali</CardTitle>
                      <div className="flex gap-1">
                        {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                          <Button size="sm" variant="ghost" className="h-6 text-[9px] text-gray-400" onClick={() => setCastingMode('agency')}>I tuoi Attori</Button>
                        )}
                      </div>
                    </div>
                    <p className="text-[9px] text-gray-500 mt-1">Attori famosi che prestano la voce ai personaggi. Costano molto ma danno un bonus qualità e fama!</p>
                  </CardHeader>
                  <CardContent className="p-3 pt-0 space-y-3">
                    {availableActors.length === 0 ? (
                      <p className="text-xs text-gray-500 text-center py-4">Nessuna guest star disponibile al momento.</p>
                    ) : (
                      <div className="space-y-1.5 max-h-[400px] overflow-y-auto">
                        {availableActors.map(actor => {
                          const isSelected = selectedCast.find(c => c.actor_id === actor.id);
                          const alreadyCast = activeSeries.cast?.some(c => c.actor_id === actor.id);
                          const skills = actor.skills || {};
                          const avgSkill = Object.values(skills).length > 0
                            ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : actor.skill || 50;
                          return (
                            <div key={actor.id} className={`p-2 rounded-lg transition-all border ${
                              alreadyCast ? 'bg-green-500/5 border-green-500/20 opacity-60' : isSelected ? 'bg-pink-500/15 border-pink-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-white/5'
                            }`} data-testid={`anime-guest-star-${actor.id}`}>
                              <div className="flex items-center gap-2 cursor-pointer" onClick={() => !alreadyCast && toggleCastMember(actor, 'Guest Star Vocale')}>
                                {actor.avatar_url ? (
                                  <img src={actor.avatar_url} alt="" className="w-9 h-9 rounded-full bg-gray-800" />
                                ) : (
                                  <div className="w-9 h-9 rounded-full bg-yellow-500/20 flex items-center justify-center text-xs font-bold text-yellow-400">{actor.name?.charAt(0)}</div>
                                )}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1">
                                    <p className="text-xs font-semibold truncate">{actor.name}</p>
                                    <span className={`text-[10px] font-bold ${actor.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>{actor.gender === 'female' ? '\u2640' : '\u2642'}</span>
                                    <Badge className={`text-[6px] h-3 ${actor.fame_category === 'superstar' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-orange-500/20 text-orange-400'}`}>
                                      {actor.fame_category === 'superstar' ? 'Superstar' : 'Famoso'}
                                    </Badge>
                                    {[...Array(actor.stars || 4)].map((_, i) => <Star key={i} className="w-2.5 h-2.5 text-yellow-500 fill-yellow-500" />)}
                                  </div>
                                  <p className="text-[9px] text-gray-500">{actor.nationality} {actor.age ? `\u2022 ${actor.age} anni` : ''} \u2022 Skill: <span className="text-emerald-400">{avgSkill}</span></p>
                                  <div className="flex flex-wrap gap-0.5 mt-0.5">
                                    {(actor.strong_genres_names || []).map((g, i) => <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                                    {actor.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[6px] h-3">~ {actor.adaptable_genre_name}</Badge>}
                                  </div>
                                </div>
                                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                                  <span className="text-[9px] text-red-400 font-bold">${(actor.salary || 0).toLocaleString()}</span>
                                  <Badge className="text-[6px] bg-pink-500/15 text-pink-400 h-3">Guest Star</Badge>
                                  {isSelected && <Check className="w-3.5 h-3.5 text-pink-400" />}
                                  {alreadyCast && <Badge className="text-[7px] bg-green-500/20 text-green-400">Nel cast</Badge>}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                    {selectedCast.filter(c => !c.is_agency).length > 0 && (
                      <Button className="w-full mt-2 bg-pink-500 hover:bg-pink-600" onClick={selectCast} disabled={actionLoading} data-testid="anime-confirm-guest-stars-btn">
                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Star className="w-4 h-4 mr-2" />}
                        Ingaggia Guest Star ({selectedCast.filter(c => !c.is_agency).length}) — ${selectedCast.filter(c => !c.is_agency).reduce((sum, c) => sum + ((availableActors.find(a => a.id === c.actor_id) || {}).salary || 0), 0).toLocaleString()}
                      </Button>
                    )}
                    <Button size="sm" variant="outline" className="w-full text-[10px] text-gray-400 border-white/10 hover:bg-white/5"
                      onClick={advanceToScreenplay} disabled={actionLoading} data-testid="anime-skip-guest-stars">
                      {actionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <ArrowRight className="w-3.5 h-3.5 mr-1" />}
                      Procedi senza Guest Star
                    </Button>
                  </CardContent>
                </Card>
                )}
                {activeSeries.cast?.length > 0 && castingMode && (
                  <Button className="w-full bg-cyan-500 hover:bg-cyan-600" onClick={advanceToScreenplay} disabled={actionLoading} data-testid="anime-advance-screenplay-btn">
                    Vai alla Sceneggiatura <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                )}
              </motion.div>
            )}

            {/* SCREENPLAY */}
            {activeSeries.status === 'screenplay' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <Card className="bg-[#111113] border-cyan-500/10">
                  <CardHeader className="pb-1"><CardTitle className="text-sm text-cyan-400">Sceneggiatura</CardTitle></CardHeader>
                  <CardContent className="p-3 pt-0 space-y-3">
                    {activeSeries.screenplay?.text ? (
                      <div className="bg-black/30 rounded-lg p-3 max-h-64 overflow-y-auto">
                        <p className="text-xs text-gray-300 whitespace-pre-line">{activeSeries.screenplay.text}</p>
                      </div>
                    ) : (
                      <div className="text-center py-6">
                        <Pen className="w-8 h-8 text-cyan-400/40 mx-auto mb-2" />
                        <p className="text-xs text-gray-500 mb-3">Genera la sceneggiatura del tuo anime con l'AI</p>
                        <Button className="bg-cyan-500 hover:bg-cyan-600" onClick={writeScreenplay} disabled={actionLoading} data-testid="anime-generate-screenplay-btn">
                          {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Pen className="w-4 h-4 mr-2" />}
                          Genera Sceneggiatura AI
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
                {activeSeries.screenplay?.text && (
                  <Button className="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold" onClick={startProduction} disabled={actionLoading} data-testid="anime-start-production-btn">
                    {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                    Avvia Produzione
                  </Button>
                )}
              </motion.div>
            )}

            {/* PRODUCTION */}
            {(activeSeries.status === 'production' || activeSeries.status === 'ready_to_release') && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <Card className="bg-[#111113] border-amber-500/10">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-amber-400">Produzione Anime</span>
                      <span className="text-xs text-gray-400">
                        {prodStatus?.complete || activeSeries.status === 'ready_to_release' ? 'Completata!' : `${prodStatus?.remaining_minutes?.toFixed(0) || '?'} min`}
                      </span>
                    </div>
                    <Progress value={prodStatus?.progress || (activeSeries.status === 'ready_to_release' ? 100 : 0)} className="h-2" />
                    {(prodStatus?.complete || activeSeries.status === 'ready_to_release') && (
                      <Button className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold" onClick={releaseSeries} disabled={actionLoading} data-testid="anime-release-btn">
                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Star className="w-4 h-4 mr-2" />}
                        Rilascia Anime!
                      </Button>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
