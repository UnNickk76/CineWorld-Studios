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
    if (selectedCast.length === 0) return toast.error('Seleziona almeno un attore');
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/select-cast`, {
        cast: selectedCast.map(c => ({ actor_id: c.actor_id, role: c.role }))
      });
      toast.success(`Cast confermato! Stipendi: $${res.data.total_salary?.toLocaleString()}`);
      setActiveSeries(prev => ({ ...prev, cast: res.data.cast }));
      setSelectedCast([]);
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
                          <Badge className="text-[9px] bg-white/5">{c.role}</Badge>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
                <Card className="bg-[#111113] border-pink-500/10">
                  <CardHeader className="pb-1"><CardTitle className="text-sm text-pink-400">Doppiatori Disponibili</CardTitle></CardHeader>
                  <CardContent className="p-3 pt-0">
                    {availableActors.length === 0 ? (
                      <p className="text-xs text-gray-500 text-center py-4">Nessun attore disponibile. Assumi dall'Agenzia Casting!</p>
                    ) : (
                      <div className="space-y-1.5 max-h-60 overflow-y-auto">
                        {availableActors.filter(a => !a.in_school).map(actor => {
                          const isSelected = selectedCast.find(c => c.actor_id === actor.id);
                          return (
                            <div key={actor.id} className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer border ${
                              isSelected ? 'bg-pink-500/15 border-pink-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-white/5'
                            }`} onClick={() => toggleCastMember(actor, 'Supporto')} data-testid={`anime-actor-${actor.id}`}>
                              <div className="w-8 h-8 rounded-full bg-pink-500/20 flex items-center justify-center text-xs font-bold text-pink-400">{actor.name?.charAt(0)}</div>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium truncate">{actor.name}</p>
                                <p className="text-[10px] text-gray-500">Skill: {actor.skill}</p>
                              </div>
                              {isSelected && (
                                <select className="bg-[#1a1a1a] text-xs rounded px-1.5 py-1 border border-white/10 text-white"
                                  value={isSelected.role} onClick={e => e.stopPropagation()}
                                  onChange={e => setSelectedCast(prev => prev.map(c => c.actor_id === actor.id ? { ...c, role: e.target.value } : c))}>
                                  <option value="Protagonista">Protagonista</option>
                                  <option value="Co-Protagonista">Co-Protagonista</option>
                                  <option value="Antagonista">Antagonista</option>
                                  <option value="Supporto">Supporto</option>
                                </select>
                              )}
                              {isSelected && <Check className="w-4 h-4 text-pink-400" />}
                            </div>
                          );
                        })}
                      </div>
                    )}
                    {selectedCast.length > 0 && (
                      <Button className="w-full mt-2 bg-pink-500 hover:bg-pink-600" onClick={selectCast} disabled={actionLoading} data-testid="anime-confirm-cast-btn">
                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Users className="w-4 h-4 mr-2" />}
                        Conferma Cast ({selectedCast.length})
                      </Button>
                    )}
                  </CardContent>
                </Card>
                {activeSeries.cast?.length > 0 && (
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
