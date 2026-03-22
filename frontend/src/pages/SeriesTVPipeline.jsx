// CineWorld - TV Series Pipeline
// Full production pipeline for TV series

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tv, ArrowRight, ArrowLeft, Users, Pen, Play, Film, Lock, Loader2, Trash2, Check, Star, X, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

const STEPS = [
  { id: 'concept', label: 'Concept', icon: Tv, color: 'blue' },
  { id: 'casting', label: 'Casting', icon: Users, color: 'purple' },
  { id: 'screenplay', label: 'Sceneggiatura', icon: Pen, color: 'emerald' },
  { id: 'production', label: 'Produzione', icon: Play, color: 'orange' },
  { id: 'completed', label: 'Completata', icon: Star, color: 'yellow' },
];

const STATUS_TO_STEP = { concept: 0, casting: 1, screenplay: 2, production: 3, ready_to_release: 3, completed: 4 };

export default function SeriesTVPipeline() {
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [genres, setGenres] = useState({});
  const [mySeries, setMySeries] = useState([]);
  const [activeSeries, setActiveSeries] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Concept form
  const [title, setTitle] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [numEpisodes, setNumEpisodes] = useState(10);
  const [description, setDescription] = useState('');

  // Casting
  const [availableActors, setAvailableActors] = useState([]);
  const [selectedCast, setSelectedCast] = useState([]);
  const [castingMode, setCastingMode] = useState(null); // null | 'agency' | 'market'
  const [agencyActors, setAgencyActors] = useState({ effective: [], school: [] });
  const [agencyInfo, setAgencyInfo] = useState(null);
  const [expandedSkills, setExpandedSkills] = useState({});

  // Production
  const [prodStatus, setProdStatus] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [genresRes, seriesRes] = await Promise.all([
        api.get('/series-pipeline/genres?series_type=tv_series'),
        api.get('/series-pipeline/my?series_type=tv_series'),
      ]);
      setGenres(genresRes.data.genres || {});
      setMySeries(seriesRes.data.series || []);
      
      // Auto-select active series (first in-progress)
      const inProgress = (seriesRes.data.series || []).find(s => !['completed', 'cancelled'].includes(s.status));
      if (inProgress) setActiveSeries(inProgress);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  // Load actors when in casting
  useEffect(() => {
    if (activeSeries?.status === 'casting') {
      api.get(`/series-pipeline/${activeSeries.id}/available-actors`).then(r => {
        setAvailableActors(r.data.actors || []);
      }).catch(() => {});
      // Also load agency actors
      api.get('/agency/actors-for-casting').then(r => {
        setAgencyActors({ effective: r.data.effective_actors || [], school: r.data.school_students || [] });
        setAgencyInfo(r.data);
      }).catch(() => {});
    }
  }, [activeSeries?.status, activeSeries?.id, api]);

  // Poll production status
  useEffect(() => {
    if (activeSeries?.status === 'production') {
      const poll = () => {
        api.get(`/series-pipeline/${activeSeries.id}/production-status`).then(r => {
          setProdStatus(r.data);
          if (r.data.complete) {
            setActiveSeries(prev => ({ ...prev, status: 'ready_to_release' }));
          }
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
        series_type: 'tv_series', description
      });
      toast.success(`"${title}" creata! Costo: $${res.data.cost?.toLocaleString()}`);
      setActiveSeries(res.data.series);
      setTitle(''); setDescription('');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella creazione');
    }
    setActionLoading(false);
  };

  const advanceToCasting = async () => {
    setActionLoading(true);
    try {
      await api.post(`/series-pipeline/${activeSeries.id}/advance-to-casting`);
      setActiveSeries(prev => ({ ...prev, status: 'casting' }));
      toast.success('Fase casting iniziata!');
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
      toast.success(`Cast selezionato! Stipendi totali: $${res.data.total_salary?.toLocaleString()}`);
      setActiveSeries(prev => ({ ...prev, cast: res.data.cast }));
      setSelectedCast([]);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const submitAgencyCastSeries = async () => {
    const selected = selectedCast.filter(c => c.is_agency);
    if (selected.length === 0) return toast.error('Seleziona almeno un attore dall\'agenzia');
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
      toast.success('Fase sceneggiatura iniziata!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const writeScreenplay = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/write-screenplay`, { mode: 'ai' }, { timeout: 120000 });
      setActiveSeries(prev => ({ ...prev, screenplay: { text: res.data.screenplay } }));
      toast.success('Sceneggiatura generata!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore generazione'); }
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

  const [releaseCard, setReleaseCard] = React.useState(null);
  const [releasePoster, setReleasePoster] = React.useState(null);
  const [posterPolling, setPosterPolling] = React.useState(false);
  const [releasePhase, setReleasePhase] = React.useState(0);
  const [posterMode, setPosterMode] = React.useState({});
  const [posterPrompt, setPosterPrompt] = React.useState({});
  const [posterLoading, setPosterLoading] = React.useState(null);
  const [expandedPoster, setExpandedPoster] = React.useState(null);

  const generateSeriesPoster = async (seriesId) => {
    const mode = posterMode[seriesId] || 'ai_auto';
    setPosterLoading(seriesId);
    try {
      const body = { mode };
      if (mode === 'ai_custom') body.custom_prompt = posterPrompt[seriesId] || '';
      const res = await api.post(`/series-pipeline/${seriesId}/generate-poster`, body, { timeout: 120000 });
      toast.success(res.data.message || 'Locandina generata!');
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore generazione poster'); }
    finally { setPosterLoading(null); }
  };

  // Quick poster generation (reuses generateSeriesPoster with auto mode)
  const generatePoster = async (seriesId) => {
    setPosterLoading(seriesId);
    try {
      const res = await api.post(`/series-pipeline/${seriesId}/generate-poster`, { mode: 'ai' }, { timeout: 120000 });
      toast.success(res.data.message || 'Locandina generata!');
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore generazione poster'); }
    finally { setPosterLoading(null); }
  };

  const releaseSeries = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/release`, {}, { timeout: 60000 });
      setReleaseCard(res.data);
      setReleasePoster(null);
      setPosterPolling(true);
      // Cinematic reveal sequence
      setReleasePhase(1);
      setTimeout(() => setReleasePhase(2), 1400);
      setTimeout(() => setReleasePhase(3), 3000);
      // Start polling for poster
      const seriesId = activeSeries.id;
      let attempts = 0;
      const pollInterval = setInterval(async () => {
        attempts++;
        try {
          const posterRes = await api.get(`/series-pipeline/${seriesId}/poster-status`);
          if (posterRes.data.ready && posterRes.data.poster_url) {
            setReleasePoster(posterRes.data.poster_url);
            setPosterPolling(false);
            clearInterval(pollInterval);
          }
        } catch {}
        if (attempts >= 30) { setPosterPolling(false); clearInterval(pollInterval); }
      }, 2000);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const closeReleaseCard = () => {
    setReleaseCard(null);
    setReleasePoster(null);
    setPosterPolling(false);
    setReleasePhase(0);
    setActiveSeries(null);
    loadData();
  };

  const discardSeries = async () => {
    if (!window.confirm('Vuoi cancellare questa serie? Riceverai un rimborso del 50%.')) return;
    setActionLoading(true);
    try {
      const res = await api.post(`/series-pipeline/${activeSeries.id}/discard`);
      toast.success(`Serie cancellata. Rimborso: $${res.data.refund?.toLocaleString()}`);
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
      <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
      <div className="max-w-2xl mx-auto px-3">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4 mt-2">
          <div className="p-2.5 bg-blue-500/20 rounded-xl border border-blue-500/30">
            <Tv className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="font-['Bebas_Neue'] text-2xl text-blue-400" data-testid="series-pipeline-title">Pipeline Serie TV</h1>
            <p className="text-xs text-gray-500">Produci la tua serie televisiva</p>
          </div>
        </div>

        {/* Step Progress */}
        {activeSeries && (
          <div className="flex items-center gap-1 mb-4 px-1" data-testid="series-steps">
            {STEPS.map((step, i) => (
              <React.Fragment key={step.id}>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-semibold transition-all ${
                  i === currentStep ? `bg-${step.color}-500/20 text-${step.color}-400 border border-${step.color}-500/30` :
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

        {/* No active series - show create form or completed list */}
        {!activeSeries ? (
          <div className="space-y-4">
            {/* Create New Series */}
            <Card className="bg-[#111113] border-blue-500/20" data-testid="create-series-form">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg font-['Bebas_Neue'] text-blue-400">Nuova Serie TV</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="Titolo della serie"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  className="bg-white/5 border-white/10 text-white"
                  data-testid="series-title-input"
                />
                <div>
                  <label className="text-xs text-gray-400 mb-1.5 block">Genere</label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {Object.entries(genres).map(([key, g]) => (
                      <button
                        key={key}
                        className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                          selectedGenre === key ? 'bg-blue-500 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10 border border-white/5'
                        }`}
                        onClick={() => { setSelectedGenre(key); setNumEpisodes(g.ep_range[0]); }}
                        data-testid={`genre-${key}`}
                      >
                        {g.name_it}
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
                      <input
                        type="range"
                        min={genres[selectedGenre]?.ep_range[0]}
                        max={genres[selectedGenre]?.ep_range[1]}
                        value={numEpisodes}
                        onChange={e => setNumEpisodes(parseInt(e.target.value))}
                        className="flex-1 accent-blue-500"
                        data-testid="episodes-slider"
                      />
                      <span className="text-sm font-bold text-blue-400 w-8 text-center">{numEpisodes}</span>
                    </div>
                    <p className="text-[10px] text-gray-500 mt-1">
                      Costo stimato: ${((numEpisodes * 150000 * (genres[selectedGenre]?.cost_mult || 1))).toLocaleString()}
                    </p>
                  </div>
                )}
                <Input
                  placeholder="Descrizione breve (opzionale)"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  className="bg-white/5 border-white/10 text-white"
                  data-testid="series-description-input"
                />
                <Button
                  className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                  onClick={createSeries}
                  disabled={actionLoading || !title.trim() || !selectedGenre}
                  data-testid="create-series-btn"
                >
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Tv className="w-4 h-4 mr-2" />}
                  Crea Serie TV
                </Button>
              </CardContent>
            </Card>

            {/* Completed Series */}
            {mySeries.filter(s => s.status === 'completed').length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Serie Completate</h3>
                <div className="space-y-2">
                  {mySeries.filter(s => s.status === 'completed').map(s => (
                    <Card key={s.id} className="bg-[#111113] border-white/5 cursor-pointer hover:border-white/15 transition-colors" data-testid={`completed-series-${s.id}`}
                      onClick={() => navigate(`/series/${s.id}`)}>
                      <CardContent className="p-3">
                        <div className="flex items-center gap-3">
                          {s.poster_url ? (
                            <img src={posterSrc(s.poster_url)} alt="" className="w-12 h-16 rounded object-cover" loading="lazy" />
                          ) : (
                            <div className="w-12 h-16 rounded bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                              <Film className="w-5 h-5 text-purple-400/50" />
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-bold truncate">{s.title}</p>
                            <p className="text-[10px] text-gray-500">{s.genre_name} - {s.num_episodes} ep. - S{s.season_number}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">{s.quality_score}/100</Badge>
                            <button
                              onClick={(e) => { e.stopPropagation(); setExpandedPoster(expandedPoster === s.id ? null : s.id); }}
                              className="p-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 transition-all"
                              data-testid={`poster-toggle-${s.id}`}>
                              <Sparkles className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>

                        {/* Poster management section */}
                        {expandedPoster === s.id && (
                          <div className="mt-3 p-2.5 rounded-lg border border-purple-500/20 bg-purple-500/5">
                            <p className="text-[10px] text-purple-400 font-semibold mb-2">
                              {s.poster_url ? 'Rigenera Locandina' : 'Crea Locandina'}
                            </p>
                            
                            {s.poster_url && (
                              <div className="flex justify-center mb-2">
                                <img src={posterSrc(s.poster_url)} alt="Locandina" className="w-20 h-28 object-cover rounded border border-purple-500/20" />
                              </div>
                            )}

                            <div className="flex gap-1 mb-2">
                              {[
                                { id: 'ai_auto', label: 'AI Automatica' },
                                { id: 'ai_custom', label: 'AI + Prompt' },
                              ].map(opt => (
                                <button key={opt.id} onClick={() => setPosterMode(p => ({...p, [s.id]: opt.id}))}
                                  className={`flex-1 p-1.5 rounded text-center border transition-all text-[9px] ${(posterMode[s.id] || 'ai_auto') === opt.id ? 'border-purple-500 bg-purple-500/10 text-purple-300' : 'border-gray-700 text-gray-400'}`}
                                  data-testid={`poster-mode-${opt.id}-${s.id}`}>
                                  {opt.label}
                                </button>
                              ))}
                            </div>

                            {(posterMode[s.id] || 'ai_auto') === 'ai_custom' && (
                              <input type="text" placeholder="Descrivi la locandina che vuoi..."
                                value={posterPrompt[s.id] || ''} onChange={e => setPosterPrompt(p => ({...p, [s.id]: e.target.value}))}
                                className="w-full mb-2 text-[10px] bg-black/30 border border-gray-700 rounded p-1.5 text-white"
                                data-testid={`poster-prompt-${s.id}`} />
                            )}

                            <Button size="sm" className="w-full bg-purple-700 hover:bg-purple-800 text-[10px] h-7"
                              onClick={() => generateSeriesPoster(s.id)} disabled={posterLoading === s.id}
                              data-testid={`generate-poster-${s.id}`}>
                              {posterLoading === s.id ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Sparkles className="w-3 h-3 mr-1" />}
                              {s.poster_url ? 'Rigenera Locandina' : 'Crea Locandina'}
                            </Button>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Active Series Pipeline */
          <div className="space-y-3" data-testid="active-series-pipeline">
            {/* Series Header */}
            <Card className="bg-[#111113] border-blue-500/20">
              <CardContent className="p-3 flex items-center gap-3">
                {activeSeries.poster_url ? (
                  <img src={posterSrc(activeSeries.poster_url)} alt="" className="w-16 h-24 rounded-lg object-cover" />
                ) : (
                  <div className="w-16 h-24 rounded-lg bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                    <Tv className="w-8 h-8 text-blue-400/50" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg font-bold truncate" data-testid="active-series-title">{activeSeries.title}</h2>
                  <p className="text-xs text-gray-400">{activeSeries.genre_name} - {activeSeries.num_episodes} episodi</p>
                  <Badge className="bg-blue-500/20 text-blue-400 text-[10px] mt-1">{activeSeries.status}</Badge>
                </div>
                <button onClick={discardSeries} className="p-2 text-red-400/60 hover:text-red-400 transition-colors" data-testid="discard-series-btn">
                  <Trash2 className="w-4 h-4" />
                </button>
              </CardContent>
            </Card>

            {/* CONCEPT PHASE */}
            {activeSeries.status === 'concept' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <Card className="bg-[#111113] border-blue-500/10">
                  <CardContent className="p-4 text-center space-y-3">
                    <Tv className="w-10 h-10 text-blue-400 mx-auto" />
                    <p className="text-sm text-gray-300">Il concept della serie è pronto! Procedi al casting per selezionare il cast.</p>
                    <Button className="w-full bg-blue-500 hover:bg-blue-600" onClick={advanceToCasting} disabled={actionLoading} data-testid="advance-to-casting-btn">
                      {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                      Vai al Casting <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* CASTING PHASE */}
            {activeSeries.status === 'casting' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                {/* Already selected cast */}
                {(activeSeries.cast?.length > 0) && (
                  <Card className="bg-[#111113] border-purple-500/10">
                    <CardHeader className="pb-1"><CardTitle className="text-sm text-purple-400">Cast Selezionato</CardTitle></CardHeader>
                    <CardContent className="p-3 pt-0">
                      <div className="space-y-1.5">
                        {activeSeries.cast.map((c, i) => (
                          <div key={i} className="flex items-center justify-between text-xs bg-purple-500/5 rounded-lg px-2 py-1.5">
                            <span className="font-medium">{c.name}</span>
                            <div className="flex items-center gap-2">
                              <Badge className="text-[9px] bg-white/5">{c.role}</Badge>
                              {c.is_agency_actor && <Badge className="text-[8px] bg-purple-500/20 text-purple-400">Agenzia</Badge>}
                              <span className="text-gray-500">${c.season_salary?.toLocaleString()}/stagione</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Casting mode choice */}
                {!castingMode && (agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                  <div className="p-3 rounded-lg border border-purple-500/20 bg-purple-500/5 space-y-2" data-testid="series-casting-mode-choice">
                    <p className="text-xs font-semibold text-purple-300">Come vuoi ingaggiare gli attori?</p>
                    <div className="grid grid-cols-2 gap-2">
                      <Button size="sm" className="h-auto py-2 bg-purple-600 hover:bg-purple-700 text-left flex-col items-start"
                        onClick={() => setCastingMode('agency')} data-testid="series-cast-agency">
                        <span className="text-xs font-semibold flex items-center gap-1"><Users className="w-3.5 h-3.5" /> Dalla tua Agenzia</span>
                        <span className="text-[9px] text-purple-200/70 mt-0.5">{agencyActors.effective.length} attori + {agencyActors.school.length} studenti</span>
                      </Button>
                      <Button size="sm" className="h-auto py-2 bg-cyan-600 hover:bg-cyan-700 text-left flex-col items-start"
                        onClick={() => setCastingMode('market')} data-testid="series-cast-market">
                        <span className="text-xs font-semibold flex items-center gap-1"><Star className="w-3.5 h-3.5" /> Dal Mercato</span>
                        <span className="text-[9px] text-cyan-200/70 mt-0.5">Attori assunti e disponibili</span>
                      </Button>
                    </div>
                  </div>
                )}

                {/* Agency casting mode */}
                {(castingMode === 'agency') && (
                  <Card className="bg-[#111113] border-purple-500/10">
                    <CardHeader className="pb-1">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm text-purple-400">Attori dalla tua Agenzia</CardTitle>
                        <Button size="sm" variant="ghost" className="h-6 text-[9px] text-gray-400" onClick={() => setCastingMode('market')}>Passa al Mercato</Button>
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
                            <div key={actor.id} className={`flex items-center gap-2 p-2 rounded-lg transition-all cursor-pointer border ${
                              alreadyCast ? 'bg-green-500/5 border-green-500/20 opacity-60' : isSelected ? 'bg-purple-500/15 border-purple-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-white/5'
                            }`} onClick={() => !alreadyCast && setSelectedCast(prev => {
                              const exists = prev.find(c => c.actor_id === actor.id);
                              if (exists) return prev.filter(c => c.actor_id !== actor.id);
                              return [...prev, { actor_id: actor.id, name: actor.name, role: 'Supporto', is_agency: true, source: actor._source }];
                            })} data-testid={`series-agency-actor-${actor.id}`}>
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${actor._source === 'school' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-purple-500/20 text-purple-400'}`}>
                                {actor.name?.charAt(0)}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1">
                                  <p className="text-xs font-medium truncate">{actor.name}</p>
                                  {actor._source === 'school' && <Badge className="text-[7px] bg-cyan-500/15 text-cyan-400 h-3.5">Studente</Badge>}
                                  {actor.is_legendary && <Badge className="text-[7px] bg-yellow-500/20 text-yellow-400 h-3.5">Leggenda</Badge>}
                                </div>
                                <p className="text-[10px] text-gray-500">Skill: {avgSkill}</p>
                                <div className="flex flex-wrap gap-0.5">
                                  {(actor.strong_genres_names || []).map((g, i) => <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                                  {actor.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[6px] h-3">~ {actor.adaptable_genre_name}</Badge>}
                                </div>
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
                              {isSelected && <Check className="w-4 h-4 text-purple-400" />}
                              {alreadyCast && <Badge className="text-[8px] bg-green-500/20 text-green-400">Nel cast</Badge>}
                            </div>
                          );
                        })}
                      </div>
                      {selectedCast.filter(c => c.is_agency).length > 0 && (
                        <Button className="w-full mt-2 bg-purple-500 hover:bg-purple-600 text-white" onClick={submitAgencyCastSeries} disabled={actionLoading} data-testid="confirm-agency-cast-series">
                          {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Users className="w-4 h-4 mr-2" />}
                          Aggiungi dall'Agenzia ({selectedCast.filter(c => c.is_agency).length})
                        </Button>
                      )}
                      <p className="text-[9px] text-amber-400 mt-1">Bonus: +20-70% XP e Fama per serie con i tuoi attori!</p>
                    </CardContent>
                  </Card>
                )}

                {/* Market casting mode - Available actors to cast */}
                {(castingMode === 'market' || (!castingMode && agencyActors.effective.length === 0 && agencyActors.school.length === 0)) && (
                <Card className="bg-[#111113] border-purple-500/10">
                  <CardHeader className="pb-1">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm text-purple-400">Casting</CardTitle>
                      {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                        <Button size="sm" variant="ghost" className="h-6 text-[9px] text-gray-400" onClick={() => setCastingMode('agency')}>Gestisci Agenzia</Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="p-3 pt-0 space-y-3">
                    {/* Agency actors in primo piano */}
                    {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && (
                      <div className="space-y-1.5" data-testid="market-agency-section">
                        <p className="text-[10px] font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-1">
                          <Users className="w-3 h-3" /> I tuoi Attori
                          <Badge className="text-[7px] bg-amber-500/15 text-amber-400 h-3 ml-1">Bonus XP/Fama</Badge>
                        </p>
                        <div className="space-y-1 max-h-48 overflow-y-auto">
                          {[...agencyActors.effective.map(a => ({...a, _source: 'effective'})), ...agencyActors.school.map(a => ({...a, _source: 'school'}))].map(actor => {
                            const alreadyCast = activeSeries.cast?.some(c => c.actor_id === actor.id);
                            const isSelected = selectedCast.find(c => c.actor_id === actor.id);
                            const skills = actor.skills || {};
                            const avgSkill = Object.values(skills).length > 0
                              ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;
                            const skillsExpanded = expandedSkills[`ag-${actor.id}`];
                            return (
                              <div key={actor.id} className={`p-1.5 rounded-lg transition-all border ${
                                alreadyCast ? 'bg-green-500/5 border-green-500/20 opacity-60' : isSelected ? 'bg-purple-500/15 border-purple-500/30' : 'bg-purple-500/5 border-purple-500/15 hover:bg-purple-500/10'
                              }`} data-testid={`market-agency-actor-${actor.id}`}>
                                <div className="flex items-center gap-2 cursor-pointer" onClick={() => !alreadyCast && setSelectedCast(prev => {
                                  const exists = prev.find(c => c.actor_id === actor.id);
                                  if (exists) return prev.filter(c => c.actor_id !== actor.id);
                                  return [...prev, { actor_id: actor.id, name: actor.name, role: 'Supporto', is_agency: true, source: actor._source }];
                                })}>
                                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold ${actor._source === 'school' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-purple-500/20 text-purple-400'}`}>
                                    {actor.name?.charAt(0)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-1">
                                      <p className="text-[11px] font-medium truncate">{actor.name}</p>
                                      {actor._source === 'school' && <Badge className="text-[6px] bg-cyan-500/15 text-cyan-400 h-3">Studente</Badge>}
                                      <Badge className="text-[6px] bg-purple-500/15 text-purple-400 h-3">Agenzia</Badge>
                                    </div>
                                    <div className="flex items-center gap-1 flex-wrap">
                                      <span className="text-[9px] text-gray-500">Skill: {avgSkill}</span>
                                      {(actor.strong_genres_names || []).map((g, i) => <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                                      {actor.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[6px] h-3">~ {actor.adaptable_genre_name}</Badge>}
                                    </div>
                                  </div>
                                  {isSelected && (
                                    <select className="bg-[#1a1a1a] text-[9px] rounded px-1 py-0.5 border border-white/10 text-white"
                                      value={isSelected.role} onClick={e => e.stopPropagation()}
                                      onChange={e => setSelectedCast(prev => prev.map(c => c.actor_id === actor.id ? { ...c, role: e.target.value } : c))}>
                                      <option value="Protagonista">Protagonista</option>
                                      <option value="Co-Protagonista">Co-Protagonista</option>
                                      <option value="Antagonista">Antagonista</option>
                                      <option value="Supporto">Supporto</option>
                                    </select>
                                  )}
                                  {isSelected && <Check className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />}
                                  {alreadyCast && <Badge className="text-[7px] bg-green-500/20 text-green-400">Nel cast</Badge>}
                                </div>
                                {/* Skill toggle for agency actors */}
                                {Object.keys(skills).length > 0 && (
                                  <div className="mt-1">
                                    <button className="text-[8px] text-purple-400 hover:text-purple-300 flex items-center gap-0.5"
                                      onClick={e => { e.stopPropagation(); setExpandedSkills(p => ({...p, [`ag-${actor.id}`]: !p[`ag-${actor.id}`]})); }}>
                                      {skillsExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                      {skillsExpanded ? 'Nascondi Skill' : 'Mostra Skill'}
                                    </button>
                                    {skillsExpanded && (
                                      <div className="grid grid-cols-3 gap-x-3 gap-y-0.5 mt-1 px-1">
                                        {Object.entries(skills).sort(([,a],[,b]) => b - a).map(([k, v]) => (
                                          <div key={k} className="flex items-center gap-1">
                                            <span className="text-[8px] text-gray-500 capitalize w-16 truncate">{k.replace(/_/g, ' ')}</span>
                                            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                              <div className={`h-full rounded-full ${v >= 80 ? 'bg-emerald-500' : v >= 60 ? 'bg-cyan-500' : v >= 40 ? 'bg-amber-500' : 'bg-red-500'}`} style={{width: `${v}%`}} />
                                            </div>
                                            <span className="text-[8px] text-gray-400 w-5 text-right">{v}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                        {selectedCast.filter(c => c.is_agency).length > 0 && (
                          <Button size="sm" className="w-full bg-purple-500 hover:bg-purple-600 text-white text-xs" onClick={submitAgencyCastSeries} disabled={actionLoading} data-testid="market-confirm-agency-cast">
                            {actionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Users className="w-3.5 h-3.5 mr-1" />}
                            Aggiungi dall'Agenzia ({selectedCast.filter(c => c.is_agency).length})
                          </Button>
                        )}
                      </div>
                    )}

                    {/* Divider */}
                    {(agencyActors.effective.length > 0 || agencyActors.school.length > 0) && availableActors.filter(a => !a.in_school).length > 0 && (
                      <div className="border-t border-white/5 pt-2">
                        <p className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1">
                          <Star className="w-3 h-3" /> Mercato Libero
                        </p>
                      </div>
                    )}
                    {availableActors.length === 0 ? (
                      <p className="text-xs text-gray-500 text-center py-4">Nessun attore disponibile. Assumi attori dall'Agenzia Casting!</p>
                    ) : (
                      <div className="space-y-1.5 max-h-[400px] overflow-y-auto">
                        {availableActors.filter(a => !a.in_school).map(actor => {
                          const isSelected = selectedCast.find(c => c.actor_id === actor.id);
                          const alreadyCast = activeSeries.cast?.some(c => c.actor_id === actor.id);
                          const skills = actor.skills || {};
                          const avgSkill = Object.values(skills).length > 0
                            ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : actor.skill || 50;
                          const skillsExpanded = expandedSkills[actor.id];
                          return (
                            <div key={actor.id} className={`p-2 rounded-lg transition-all border ${
                              alreadyCast ? 'bg-green-500/5 border-green-500/20 opacity-60' : isSelected ? 'bg-purple-500/15 border-purple-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-white/5'
                            }`} data-testid={`market-actor-${actor.id}`}>
                              <div className="flex items-center gap-2 cursor-pointer" onClick={() => !alreadyCast && toggleCastMember(actor, 'Supporto')}>
                                {actor.avatar_url ? (
                                  <img src={actor.avatar_url} alt="" className="w-9 h-9 rounded-full bg-gray-800" />
                                ) : (
                                  <div className="w-9 h-9 rounded-full bg-purple-500/20 flex items-center justify-center text-xs font-bold text-purple-400">
                                    {actor.name?.charAt(0)}
                                  </div>
                                )}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1">
                                    <p className="text-xs font-semibold truncate">{actor.name}</p>
                                    <span className={`text-[10px] font-bold ${actor.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>{actor.gender === 'female' ? '\u2640' : '\u2642'}</span>
                                    {actor.is_legendary && <Badge className="text-[7px] bg-yellow-500/20 text-yellow-400 h-3.5">Leggenda</Badge>}
                                    {[...Array(actor.stars || 2)].map((_, i) => <Star key={i} className="w-2.5 h-2.5 text-yellow-500 fill-yellow-500" />)}
                                  </div>
                                  <p className="text-[9px] text-gray-500">
                                    {actor.nationality} {actor.age ? <>{' \u2022 '}{actor.age} anni</> : ''}{' \u2022 '}Skill: <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>{' \u2022 '}Film: {actor.films_count || 0}
                                  </p>
                                  <div className="flex flex-wrap gap-0.5 mt-0.5">
                                    {(actor.strong_genres_names || []).map((g, i) => <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                                    {actor.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[6px] h-3">~ {actor.adaptable_genre_name}</Badge>}
                                  </div>
                                  {actor.agency_name && <p className="text-[8px] text-gray-600 mt-0.5">Agenzia: {actor.agency_name}</p>}
                                </div>
                                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                                  <span className="text-[9px] text-yellow-400">${(actor.salary || actor.cost_per_film || 0).toLocaleString()}</span>
                                  {isSelected && (
                                    <select className="bg-[#1a1a1a] text-[9px] rounded px-1 py-0.5 border border-white/10 text-white"
                                      value={isSelected.role} onClick={e => e.stopPropagation()}
                                      onChange={e => setSelectedCast(prev => prev.map(c => c.actor_id === actor.id ? { ...c, role: e.target.value } : c))}>
                                      <option value="Protagonista">Protagonista</option>
                                      <option value="Co-Protagonista">Co-Protagonista</option>
                                      <option value="Antagonista">Antagonista</option>
                                      <option value="Supporto">Supporto</option>
                                    </select>
                                  )}
                                  {isSelected && <Check className="w-3.5 h-3.5 text-purple-400" />}
                                  {alreadyCast && <Badge className="text-[7px] bg-green-500/20 text-green-400">Nel cast</Badge>}
                                </div>
                              </div>
                              {/* Skill toggle */}
                              {Object.keys(skills).length > 0 && (
                                <div className="mt-1">
                                  <button className="text-[8px] text-purple-400 hover:text-purple-300 flex items-center gap-0.5"
                                    onClick={e => { e.stopPropagation(); setExpandedSkills(p => ({...p, [actor.id]: !p[actor.id]})); }}
                                    data-testid={`toggle-skills-${actor.id}`}>
                                    {skillsExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                    {skillsExpanded ? 'Nascondi Skill' : 'Mostra Skill'}
                                  </button>
                                  {skillsExpanded && (
                                    <div className="grid grid-cols-3 gap-x-3 gap-y-0.5 mt-1 px-1">
                                      {Object.entries(skills).sort(([,a],[,b]) => b - a).map(([k, v]) => (
                                        <div key={k} className="flex items-center gap-1">
                                          <span className="text-[8px] text-gray-500 capitalize w-16 truncate">{k.replace(/_/g, ' ')}</span>
                                          <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                            <div className={`h-full rounded-full ${v >= 80 ? 'bg-emerald-500' : v >= 60 ? 'bg-cyan-500' : v >= 40 ? 'bg-amber-500' : 'bg-red-500'}`} style={{width: `${v}%`}} />
                                          </div>
                                          <span className="text-[8px] text-gray-400 w-5 text-right">{v}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                    {selectedCast.filter(c => !c.is_agency).length > 0 && (
                      <Button className="w-full mt-2 bg-purple-500 hover:bg-purple-600 text-white" onClick={selectCast} disabled={actionLoading} data-testid="confirm-cast-btn">
                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Users className="w-4 h-4 mr-2" />}
                        Conferma Cast ({selectedCast.filter(c => !c.is_agency).length})
                      </Button>
                    )}
                  </CardContent>
                </Card>
                )}

                {/* Advance button (if cast selected) */}
                {activeSeries.cast?.length > 0 && (
                  <Button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white" onClick={advanceToScreenplay} disabled={actionLoading} data-testid="advance-to-screenplay-btn">
                    Vai alla Sceneggiatura <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                )}
              </motion.div>
            )}

            {/* SCREENPLAY PHASE */}
            {activeSeries.status === 'screenplay' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <Card className="bg-[#111113] border-emerald-500/10">
                  <CardHeader className="pb-1"><CardTitle className="text-sm text-emerald-400">Sceneggiatura</CardTitle></CardHeader>
                  <CardContent className="p-3 pt-0 space-y-3">
                    {activeSeries.screenplay?.text ? (
                      <div className="bg-black/30 rounded-lg p-3 max-h-64 overflow-y-auto">
                        <p className="text-xs text-gray-300 whitespace-pre-line">{activeSeries.screenplay.text}</p>
                      </div>
                    ) : (
                      <div className="text-center py-6">
                        <Pen className="w-8 h-8 text-emerald-400/40 mx-auto mb-2" />
                        <p className="text-xs text-gray-500 mb-3">Genera la sceneggiatura con l'AI per il concept della serie</p>
                        <Button className="bg-emerald-500 hover:bg-emerald-600 text-white" onClick={writeScreenplay} disabled={actionLoading} data-testid="generate-screenplay-btn">
                          {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Pen className="w-4 h-4 mr-2" />}
                          Genera Sceneggiatura AI
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {activeSeries.screenplay?.text && (
                  <Button className="w-full bg-orange-500 hover:bg-orange-600 text-white" onClick={startProduction} disabled={actionLoading} data-testid="start-production-btn">
                    {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                    Avvia Produzione <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                )}
              </motion.div>
            )}

            {/* PRODUCTION PHASE */}
            {(activeSeries.status === 'production' || activeSeries.status === 'ready_to_release') && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <Card className="bg-[#111113] border-orange-500/10">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-orange-400">Produzione</span>
                      <span className="text-xs text-gray-400">
                        {prodStatus?.complete || activeSeries.status === 'ready_to_release' 
                          ? 'Completata!' 
                          : `${prodStatus?.remaining_minutes?.toFixed(0) || '?'} min rimanenti`}
                      </span>
                    </div>
                    <Progress value={prodStatus?.progress || (activeSeries.status === 'ready_to_release' ? 100 : 0)} className="h-2" />
                    
                    {/* Speed up button - visible during active production */}
                    {activeSeries.status === 'production' && !prodStatus?.complete && (
                      <Button 
                        className="w-full bg-gradient-to-r from-amber-600 to-orange-500 hover:from-amber-500 hover:to-orange-400 text-black text-xs font-bold h-8" 
                        onClick={async () => {
                          setActionLoading('speedup');
                          try {
                            const res = await api.post(`/series-pipeline/${activeSeries.id}/speed-up-production`, {}, { timeout: 15000 });
                            toast.success(res.data.message);
                            refreshUser();
                            // Re-check production status
                            const ps = await api.get(`/series-pipeline/${activeSeries.id}/production-status`);
                            setProdStatus(ps.data);
                          } catch (e) { toast.error(e.response?.data?.detail || 'Errore accelerazione'); }
                          finally { setActionLoading(null); }
                        }} 
                        disabled={actionLoading}
                        data-testid="speed-up-production-btn">
                        {actionLoading === 'speedup' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <span className="mr-1">⚡</span>}
                        Accelera Produzione (-30%)
                        <span className="ml-1 text-[9px] opacity-70">({(activeSeries.num_episodes || 10) <= 8 ? 15 : (activeSeries.num_episodes || 10) <= 16 ? 20 : 25} CP)</span>
                      </Button>
                    )}

                    {(prodStatus?.complete || activeSeries.status === 'ready_to_release') && (
                      <div className="space-y-2">
                        {/* Poster generation pre-release */}
                        {!activeSeries.poster_url && (
                          <Button className="w-full bg-purple-600 hover:bg-purple-500 text-white text-xs" 
                            onClick={() => generatePoster(activeSeries.id)} disabled={actionLoading || posterLoading === activeSeries.id}
                            data-testid="pre-release-poster-btn">
                            {posterLoading === activeSeries.id ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Sparkles className="w-3 h-3 mr-1" />}
                            {posterLoading === activeSeries.id ? 'Generazione...' : 'Genera Locandina'}
                          </Button>
                        )}
                        {activeSeries.poster_url && (
                          <div className="flex items-center gap-2 p-2 bg-purple-500/5 rounded border border-purple-500/10">
                            <img src={posterSrc(activeSeries.poster_url)} alt="" className="w-8 h-12 rounded object-cover" />
                            <span className="text-[10px] text-purple-300 flex-1">Locandina pronta</span>
                            <button onClick={() => generatePoster(activeSeries.id)} disabled={posterLoading === activeSeries.id}
                              className="text-[9px] text-purple-400 hover:underline">
                              {posterLoading === activeSeries.id ? 'Generazione...' : 'Rigenera'}
                            </button>
                          </div>
                        )}
                        <Button className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold" onClick={releaseSeries} disabled={actionLoading} data-testid="release-series-btn">
                          {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Star className="w-4 h-4 mr-2" />}
                          Rilascia Serie!
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>
        )}
      </div>

    {/* Cinematic Release Experience */}
    {releaseCard && releasePhase > 0 && (() => {
      const evt = releaseCard.release_event;
      const hasEvent = evt && evt.id !== 'quiet_release_series' && evt.id !== 'quiet_release_anime' && evt.id !== 'nothing_special';
      const isAnimeType = releaseCard.type === 'anime';
      const accentColor = isAnimeType ? 'pink' : 'purple';
      const isRare = hasEvent && evt.rarity === 'rare';

      return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="release-card-modal">
          <div className="absolute inset-0 bg-black/90 backdrop-blur-md"
            style={{ animation: 'rcFadeIn 0.5s ease-out' }}
            onClick={() => { if (releasePhase >= 3) closeReleaseCard(); }} />

          <div className="relative w-full max-w-sm z-10">
            {/* Phase 1: Title */}
            <div className="text-center mb-4" style={{ animation: 'rcSlideUp 0.8s ease-out both' }}>
              <Badge className={`mx-auto mb-2 ${isAnimeType ? 'bg-pink-500/20 text-pink-400' : 'bg-purple-500/20 text-purple-400'} text-[10px]`}
                style={{ animation: 'rcFadeIn 0.5s ease-out 0.2s both' }}>
                {isAnimeType ? 'Anime' : 'Serie TV'} Completata!
              </Badge>
              <h1 className="text-xl font-black text-white tracking-tight"
                style={{ animation: 'rcScaleIn 0.6s ease-out 0.4s both' }}>
                {releaseCard.title}
              </h1>
              <p className={`text-[10px] ${isAnimeType ? 'text-pink-400/70' : 'text-purple-400/70'} uppercase mt-0.5`}
                style={{ animation: 'rcFadeIn 0.4s ease-out 0.6s both' }}>
                {releaseCard.genre} - {releaseCard.episodes_count} episodi
              </p>
            </div>

            {/* Phase 2: Event reveal */}
            {releasePhase >= 2 && hasEvent && (() => {
              const borderC = evt.type === 'positive' ? 'border-emerald-500' : evt.type === 'negative' ? 'border-red-500' : 'border-amber-500';
              const bgGrad = evt.type === 'positive' ? 'from-emerald-950/80 to-[#111]' : evt.type === 'negative' ? 'from-red-950/80 to-[#111]' : 'from-amber-950/80 to-[#111]';
              const txtC = evt.type === 'positive' ? 'text-emerald-400' : evt.type === 'negative' ? 'text-red-400' : 'text-amber-400';
              const glowC = evt.type === 'positive' ? 'shadow-emerald-500/30' : evt.type === 'negative' ? 'shadow-red-500/30' : 'shadow-amber-500/30';

              return (
                <div className={`relative rounded-xl border-2 ${borderC} bg-gradient-to-b ${bgGrad} p-3.5 shadow-lg ${glowC} ${isRare ? 'ring-2 ring-purple-500/50' : ''}`}
                  style={{ animation: isRare ? 'rcShakeIn 0.7s ease-out both' : 'rcEventReveal 0.7s ease-out both' }}
                  data-testid="release-event">

                  {isRare && <div className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/10 to-transparent"
                      style={{ animation: 'rcShimmer 2s ease-in-out infinite' }} />
                  </div>}

                  <div className="flex justify-center mb-2">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      evt.type === 'positive' ? 'bg-emerald-500/20' : evt.type === 'negative' ? 'bg-red-500/20' : 'bg-amber-500/20'
                    }`} style={{ animation: 'rcPulse 1.5s ease-in-out infinite' }}>
                      <span className="text-xl">{evt.type === 'positive' ? '⚡' : evt.type === 'negative' ? '💥' : '🔀'}</span>
                    </div>
                  </div>

                  <div className="text-center mb-1.5">
                    {isRare && <Badge className="bg-purple-500/30 text-purple-300 text-[7px] mb-1 border border-purple-500/40">EVENTO RARO</Badge>}
                    <h3 className={`text-xs font-black ${txtC} uppercase tracking-wider`}>{evt.name}</h3>
                  </div>

                  <p className="text-[10px] text-gray-300 text-center leading-relaxed mb-2"
                    style={{ animation: 'rcFadeIn 0.5s ease-out 0.3s both' }}>{evt.description}</p>

                  <div className="flex justify-center gap-3 text-[10px] font-bold" style={{ animation: 'rcFadeIn 0.4s ease-out 0.5s both' }}>
                    {evt.quality_modifier !== 0 && (
                      <div className={`px-2 py-0.5 rounded-full ${evt.quality_modifier > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                        Qualita {evt.quality_modifier > 0 ? '+' : ''}{evt.quality_modifier}
                      </div>
                    )}
                    {evt.revenue_modifier !== 0 && (
                      <div className={`px-2 py-0.5 rounded-full ${evt.revenue_modifier > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                        Incassi {evt.revenue_modifier > 0 ? '+' : ''}{evt.revenue_modifier}%
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}

            {/* Phase 3: Full results compact */}
            {releasePhase >= 3 && (
              <div className="mt-3 space-y-2" style={{ animation: 'rcSlideUp 0.6s ease-out both' }}>
                <Card className={`bg-[#151517] ${isAnimeType ? 'border-pink-600/30' : 'border-purple-600/30'} overflow-hidden`}>
                  <CardContent className="p-3 space-y-2.5">
                    {/* Poster + Score row */}
                    <div className="flex items-center gap-3">
                      <div className="w-14 h-20 flex-shrink-0">
                        {releasePoster ? (
                          <img src={posterSrc(releasePoster)} alt="Locandina" className={`w-full h-full object-cover rounded border ${isAnimeType ? 'border-pink-500/20' : 'border-purple-500/20'} shadow-lg`} />
                        ) : posterPolling ? (
                          <div className={`w-full h-full rounded ${isAnimeType ? 'bg-pink-500/5 border-pink-500/20' : 'bg-purple-500/5 border-purple-500/20'} border flex items-center justify-center animate-pulse`}>
                            <Sparkles className={`w-4 h-4 ${isAnimeType ? 'text-pink-500/50' : 'text-purple-500/50'}`} />
                          </div>
                        ) : (
                          <div className={`w-full h-full rounded ${isAnimeType ? 'bg-pink-500/5' : 'bg-purple-500/5'} border border-white/5 flex items-center justify-center`}>
                            <Film className="w-5 h-5 text-gray-600" />
                          </div>
                        )}
                      </div>
                      <div className="flex-1">
                        {/* Stats grid */}
                        <div className="grid grid-cols-3 gap-1.5 text-center">
                          <div className={`p-1.5 rounded ${isAnimeType ? 'bg-pink-500/10 border-pink-500/20' : 'bg-yellow-500/10 border-yellow-500/20'} border`}>
                            <p className={`text-lg font-black ${releaseCard.quality?.score >= 70 ? 'text-green-400' : releaseCard.quality?.score >= 50 ? 'text-yellow-400' : 'text-red-400'}`}
                              style={{ animation: 'rcCountUp 0.5s ease-out both' }}>
                              {releaseCard.quality?.score || 0}
                            </p>
                            <p className="text-[7px] text-gray-500">QUALITA</p>
                          </div>
                          <div className="p-1.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                            <p className="text-sm font-bold text-emerald-400">${((releaseCard.total_revenue || 0) / 1000000).toFixed(1)}M</p>
                            <p className="text-[7px] text-gray-500">INCASSO</p>
                          </div>
                          <div className="p-1.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                            <p className="text-sm font-bold text-cyan-400">{releaseCard.audience_rating || 0}</p>
                            <p className="text-[7px] text-gray-500">VOTO</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Badges */}
                    <div className="flex flex-wrap gap-1 justify-center">
                      <Badge className="bg-purple-500/20 text-purple-400 text-[9px]">+{releaseCard.xp_reward} XP</Badge>
                      <Badge className="bg-pink-500/20 text-pink-400 text-[9px]">+{releaseCard.fame_bonus} Fama</Badge>
                      <Badge className="bg-cyan-500/20 text-cyan-400 text-[9px]">{releaseCard.episodes_count} ep.</Badge>
                    </div>

                    {/* Audience comments (compact) */}
                    {releaseCard.audience_comments?.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-[8px] text-gray-500 uppercase">Commenti</p>
                        {releaseCard.audience_comments.slice(0, 2).map((c, i) => (
                          <div key={i} className={`px-2 py-1 rounded text-[9px] border ${
                            c.sentiment === 'positive' ? 'bg-emerald-500/5 border-emerald-500/15 text-emerald-300' :
                            c.sentiment === 'negative' ? 'bg-red-500/5 border-red-500/15 text-red-300' :
                            'bg-amber-500/5 border-amber-500/15 text-amber-300'
                          }`}>
                            "{c.text}" <Badge className={`ml-1 text-[7px] h-3 ${c.rating >= 7 ? 'bg-emerald-500/20 text-emerald-400' : c.rating >= 5 ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'}`}>{c.rating}</Badge>
                          </div>
                        ))}
                      </div>
                    )}

                    <Button className={`w-full ${isAnimeType ? 'bg-pink-600 hover:bg-pink-500' : 'bg-purple-600 hover:bg-purple-500'} text-white text-xs font-bold`}
                      onClick={closeReleaseCard} data-testid="close-release-card">
                      Chiudi
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* CSS Animations */}
          <style>{`
            @keyframes rcFadeIn { from { opacity: 0; } to { opacity: 1; } }
            @keyframes rcSlideUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
            @keyframes rcScaleIn { from { opacity: 0; transform: scale(0.85); } to { opacity: 1; transform: scale(1); } }
            @keyframes rcEventReveal { from { opacity: 0; transform: scale(0.9) translateY(12px); } to { opacity: 1; transform: scale(1) translateY(0); } }
            @keyframes rcShakeIn {
              0% { opacity: 0; transform: scale(0.8); }
              40% { opacity: 1; transform: scale(1.04); }
              55% { transform: scale(1) rotate(-1deg); }
              70% { transform: scale(1.02) rotate(1deg); }
              85% { transform: scale(1) rotate(-0.5deg); }
              100% { transform: scale(1) rotate(0); }
            }
            @keyframes rcShimmer { 0%, 100% { transform: translateX(-100%); } 50% { transform: translateX(100%); } }
            @keyframes rcCountUp { from { opacity: 0; transform: scale(0.5); } to { opacity: 1; transform: scale(1); } }
            @keyframes rcPulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.08); } }
          `}</style>
        </div>
      );
    })()}
    </div>
  );
}
