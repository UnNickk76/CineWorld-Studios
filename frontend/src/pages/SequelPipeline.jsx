// CineWorld - Sequel Pipeline
// Reduced pipeline for sequel creation: Select parent → Confirm Cast → Screenplay → Production → Release

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Copy, ArrowRight, Users, Pen, Play, Star, Loader2, Trash2, Check, Film, TrendingUp, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

const STEPS = [
  { id: 'select', label: 'Seleziona', icon: Film },
  { id: 'casting', label: 'Cast', icon: Users },
  { id: 'screenplay', label: 'Sceneggiatura', icon: Pen },
  { id: 'production', label: 'Produzione', icon: Play },
  { id: 'completed', label: 'Completato', icon: Star },
];

const STATUS_TO_STEP = { select: 0, casting: 1, screenplay: 2, production: 3, ready_to_release: 3, completed: 4 };

export default function SequelPipeline() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [eligibleFilms, setEligibleFilms] = useState([]);
  const [mySequels, setMySequels] = useState([]);
  const [activeSequel, setActiveSequel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [subtitle, setSubtitle] = useState('');
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [prodStatus, setProdStatus] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [filmsRes, sequelsRes] = await Promise.all([
        api.get('/sequel-pipeline/eligible-films'),
        api.get('/sequel-pipeline/my'),
      ]);
      setEligibleFilms(filmsRes.data.films || []);
      setMySequels(sequelsRes.data.sequels || []);
      const inProgress = (sequelsRes.data.sequels || []).find(s => !['completed', 'cancelled'].includes(s.status));
      if (inProgress) setActiveSequel(inProgress);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    if (activeSequel?.status === 'production') {
      const poll = () => {
        api.get(`/sequel-pipeline/${activeSequel.id}/production-status`).then(r => {
          setProdStatus(r.data);
          if (r.data.complete) setActiveSequel(prev => ({ ...prev, status: 'ready_to_release' }));
        }).catch(() => {});
      };
      poll();
      const interval = setInterval(poll, 5000);
      return () => clearInterval(interval);
    }
  }, [activeSequel?.status, activeSequel?.id, api]);

  const createSequel = async () => {
    if (!selectedFilm || !subtitle.trim()) return toast.error('Seleziona un film e inserisci un sottotitolo');
    setActionLoading(true);
    try {
      const res = await api.post('/sequel-pipeline/create', { parent_film_id: selectedFilm.id, subtitle });
      toast.success(`Sequel creato! Costo: $${res.data.cost?.toLocaleString()}`);
      setActiveSequel(res.data.sequel);
      setSubtitle('');
      setSelectedFilm(null);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const confirmCast = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/sequel-pipeline/${activeSequel.id}/confirm-cast`);
      toast.success(`Cast confermato! Stipendi: $${res.data.cast_salary?.toLocaleString()} (sconto 30%)`);
      setActiveSequel(prev => ({ ...prev, status: 'screenplay' }));
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const writeScreenplay = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/sequel-pipeline/${activeSequel.id}/write-screenplay`);
      setActiveSequel(prev => ({ ...prev, screenplay: { text: res.data.screenplay }, status: 'screenplay' }));
      toast.success('Sceneggiatura sequel generata!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const startProduction = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/sequel-pipeline/${activeSequel.id}/start-production`);
      setActiveSequel(prev => ({ ...prev, status: 'production' }));
      toast.success(`Produzione avviata! (${res.data.duration_minutes} min - crew esperta)`);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const releaseSequel = async () => {
    setActionLoading(true);
    try {
      const res = await api.post(`/sequel-pipeline/${activeSequel.id}/release`);
      const bd = res.data.breakdown || {};
      toast.success(`Sequel completato! Qualità: ${res.data.quality}/100 (Saga: +${bd.saga_bonus}%${bd.fatigue_malus < 0 ? `, Fatigue: ${bd.fatigue_malus}` : ''})`);
      setActiveSequel(null);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const discardSequel = async () => {
    if (!window.confirm('Vuoi cancellare questo sequel? Rimborso 50%.')) return;
    setActionLoading(true);
    try {
      const res = await api.post(`/sequel-pipeline/${activeSequel.id}/discard`);
      toast.success(`Sequel cancellato. Rimborso: $${res.data.refund?.toLocaleString()}`);
      setActiveSequel(null);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  const currentStep = activeSequel ? (STATUS_TO_STEP[activeSequel.status] ?? 0) : 0;

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
      <div className="max-w-2xl mx-auto px-3">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4 mt-2">
          <div className="p-2.5 bg-amber-600/20 rounded-xl border border-amber-600/30">
            <Copy className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <h1 className="font-['Bebas_Neue'] text-2xl text-amber-500" data-testid="sequel-pipeline-title">Pipeline Sequel</h1>
            <p className="text-xs text-gray-500">Continua le tue saghe cinematografiche</p>
          </div>
        </div>

        {/* Step Progress */}
        {activeSequel && (
          <div className="flex items-center gap-1 mb-4 px-1" data-testid="sequel-steps">
            {STEPS.map((step, i) => (
              <React.Fragment key={step.id}>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-semibold transition-all ${
                  i === currentStep ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
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

        {!activeSequel ? (
          <div className="space-y-4">
            {/* Select Film for Sequel */}
            <Card className="bg-[#111113] border-amber-600/20" data-testid="sequel-select-form">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg font-['Bebas_Neue'] text-amber-500">Nuovo Sequel</CardTitle>
                <p className="text-[10px] text-gray-500">Seleziona il film da continuare e inserisci il sottotitolo</p>
              </CardHeader>
              <CardContent className="space-y-3">
                {eligibleFilms.length === 0 ? (
                  <div className="text-center py-6">
                    <Film className="w-10 h-10 text-gray-600 mx-auto mb-2" />
                    <p className="text-xs text-gray-500">Nessun film disponibile per un sequel. Completa un film prima!</p>
                  </div>
                ) : (
                  <>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {eligibleFilms.map(f => (
                        <div key={f.id}
                          className={`flex items-center gap-2.5 p-2 rounded-lg cursor-pointer border transition-all ${
                            selectedFilm?.id === f.id ? 'bg-amber-500/15 border-amber-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-white/5'
                          }`}
                          onClick={() => setSelectedFilm(f)}
                          data-testid={`eligible-film-${f.id}`}
                        >
                          {f.poster_url ? (
                            <img src={posterSrc(f.poster_url)} alt="" className="w-8 h-12 rounded object-cover" loading="lazy" />
                          ) : (
                            <div className="w-8 h-12 rounded bg-amber-500/10 flex items-center justify-center"><Film className="w-4 h-4 text-amber-500/50" /></div>
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold truncate">{f.title}</p>
                            <p className="text-[10px] text-gray-500">{f.genre} | Qualità: {f.quality_score || f.quality || '?'}/100</p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <Badge className="bg-amber-600/20 text-amber-400 text-[9px]">Cap. {f.next_sequel_number}</Badge>
                            <p className="text-[9px] text-green-400 mt-0.5">+{f.saga_bonus_percent}% saga</p>
                            {f.sequel_count >= 3 && <p className="text-[9px] text-red-400/70">Rischio fatigue</p>}
                          </div>
                          {selectedFilm?.id === f.id && <Check className="w-4 h-4 text-amber-400 flex-shrink-0" />}
                        </div>
                      ))}
                    </div>
                    {selectedFilm && (
                      <>
                        <Input
                          placeholder={`${selectedFilm.title}: ...sottotitolo`}
                          value={subtitle}
                          onChange={e => setSubtitle(e.target.value)}
                          className="bg-white/5 border-white/10 text-white"
                          data-testid="sequel-subtitle-input"
                        />
                        <div className="bg-amber-500/5 rounded-lg p-2 border border-amber-500/10">
                          <p className="text-[10px] text-gray-400">
                            <span className="text-amber-400 font-medium">Titolo: </span>
                            {selectedFilm.title}{subtitle ? `: ${subtitle}` : ''}
                          </p>
                          <p className="text-[10px] text-gray-400">
                            <span className="text-green-400 font-medium">Bonus saga: </span>+{selectedFilm.saga_bonus_percent}% qualità
                          </p>
                          <p className="text-[10px] text-gray-400">
                            <span className="text-yellow-400 font-medium">Costo: </span>$300,000 (60% del normale)
                          </p>
                        </div>
                        <Button
                          className="w-full bg-amber-600 hover:bg-amber-700 text-white"
                          onClick={createSequel}
                          disabled={actionLoading || !subtitle.trim()}
                          data-testid="create-sequel-btn"
                        >
                          {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                          Crea Sequel
                        </Button>
                      </>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Completed Sequels */}
            {mySequels.filter(s => s.status === 'completed').length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Sequel Completati</h3>
                <div className="space-y-2">
                  {mySequels.filter(s => s.status === 'completed').map(s => (
                    <Card key={s.id} className="bg-[#111113] border-white/5" data-testid={`completed-sequel-${s.id}`}>
                      <CardContent className="p-3 flex items-center gap-3">
                        {s.poster_url && <img src={posterSrc(s.poster_url)} alt="" className="w-10 h-14 rounded object-cover" loading="lazy" />}
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-bold truncate">{s.title}</p>
                          <p className="text-[10px] text-gray-500">Cap. {s.sequel_number} | {s.genre}</p>
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
          <div className="space-y-3" data-testid="active-sequel-pipeline">
            {/* Sequel Header */}
            <Card className="bg-[#111113] border-amber-600/20">
              <CardContent className="p-3 flex items-center gap-3">
                {activeSequel.poster_url ? (
                  <img src={posterSrc(activeSequel.poster_url)} alt="" className="w-14 h-20 rounded-lg object-cover" />
                ) : (
                  <div className="w-14 h-20 rounded-lg bg-amber-600/10 flex items-center justify-center"><Copy className="w-7 h-7 text-amber-500/50" /></div>
                )}
                <div className="flex-1 min-w-0">
                  <h2 className="text-base font-bold truncate" data-testid="active-sequel-title">{activeSequel.title}</h2>
                  <p className="text-[10px] text-gray-400">Capitolo {activeSequel.sequel_number} | {activeSequel.genre}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="bg-amber-600/20 text-amber-400 text-[9px]">{activeSequel.status}</Badge>
                    <Badge className="bg-green-500/20 text-green-400 text-[9px]">+{activeSequel.saga_bonus_percent}% saga</Badge>
                  </div>
                </div>
                <button onClick={discardSequel} className="p-2 text-red-400/60 hover:text-red-400" data-testid="discard-sequel-btn">
                  <Trash2 className="w-4 h-4" />
                </button>
              </CardContent>
            </Card>

            {/* CASTING - Confirm inherited cast */}
            {activeSequel.status === 'casting' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <Card className="bg-[#111113] border-purple-500/10">
                  <CardHeader className="pb-1">
                    <CardTitle className="text-sm text-purple-400">Cast Ereditato (Sconto 30%)</CardTitle>
                  </CardHeader>
                  <CardContent className="p-3 pt-0">
                    {(activeSequel.cast || []).length === 0 ? (
                      <p className="text-xs text-gray-500 text-center py-4">Nessun cast ereditato dal film originale.</p>
                    ) : (
                      <div className="space-y-1.5">
                        {activeSequel.cast.map((c, i) => (
                          <div key={i} className="flex items-center justify-between text-xs bg-purple-500/5 rounded-lg px-2 py-1.5">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center text-[10px] font-bold text-purple-400">{c.name?.charAt(0)}</div>
                              <span className="font-medium">{c.name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge className="text-[9px] bg-white/5">{c.role}</Badge>
                              <span className="text-gray-500">${c.salary?.toLocaleString()}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <Button className="w-full mt-3 bg-purple-500 hover:bg-purple-600 text-white" onClick={confirmCast} disabled={actionLoading} data-testid="confirm-sequel-cast-btn">
                      {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Users className="w-4 h-4 mr-2" />}
                      Conferma Cast e Prosegui
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* SCREENPLAY */}
            {activeSequel.status === 'screenplay' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <Card className="bg-[#111113] border-emerald-500/10">
                  <CardHeader className="pb-1"><CardTitle className="text-sm text-emerald-400">Sceneggiatura Sequel</CardTitle></CardHeader>
                  <CardContent className="p-3 pt-0 space-y-3">
                    {activeSequel.screenplay?.text ? (
                      <div className="bg-black/30 rounded-lg p-3 max-h-56 overflow-y-auto">
                        <p className="text-xs text-gray-300 whitespace-pre-line">{activeSequel.screenplay.text}</p>
                      </div>
                    ) : (
                      <div className="text-center py-6">
                        <Pen className="w-8 h-8 text-emerald-400/40 mx-auto mb-2" />
                        <p className="text-xs text-gray-500 mb-3">L'AI creerà una continuazione della storia del film originale</p>
                        <Button className="bg-emerald-500 hover:bg-emerald-600 text-white" onClick={writeScreenplay} disabled={actionLoading} data-testid="generate-sequel-screenplay-btn">
                          {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Pen className="w-4 h-4 mr-2" />}
                          Genera Sceneggiatura AI
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
                {activeSequel.screenplay?.text && (
                  <Button className="w-full bg-orange-500 hover:bg-orange-600 text-white" onClick={startProduction} disabled={actionLoading} data-testid="start-sequel-production-btn">
                    {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                    Avvia Produzione Rapida (5 min)
                  </Button>
                )}
              </motion.div>
            )}

            {/* PRODUCTION */}
            {(activeSequel.status === 'production' || activeSequel.status === 'ready_to_release') && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <Card className="bg-[#111113] border-orange-500/10">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-orange-400">Produzione Sequel</span>
                      <span className="text-xs text-gray-400">
                        {prodStatus?.complete || activeSequel.status === 'ready_to_release' ? 'Completata!' : `${prodStatus?.remaining_minutes?.toFixed(0) || '?'} min`}
                      </span>
                    </div>
                    <Progress value={prodStatus?.progress || (activeSequel.status === 'ready_to_release' ? 100 : 0)} className="h-2" />
                    <p className="text-[10px] text-gray-500 text-center">Crew esperta, produzione accelerata</p>
                    {(prodStatus?.complete || activeSequel.status === 'ready_to_release') && (
                      <Button className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold" onClick={releaseSequel} disabled={actionLoading} data-testid="release-sequel-btn">
                        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Star className="w-4 h-4 mr-2" />}
                        Rilascia Sequel!
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
