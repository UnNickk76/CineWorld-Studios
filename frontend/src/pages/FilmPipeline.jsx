import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  Pencil, ClipboardList, Users, BookOpen, Clapperboard, Play,
  HelpCircle, Star, MapPin, Clock, Check, X, DollarSign,
  Zap, ChevronRight, RefreshCw, ThumbsDown, ThumbsUp, ShoppingCart, Film, TrendingUp
} from 'lucide-react';

const TABS = [
  { id: 'creation', icon: Pencil, label: 'Creazione', desc: 'Crea una nuova proposta: titolo, genere, sinossi e location' },
  { id: 'proposals', icon: ClipboardList, label: 'Proposte', desc: 'Film proposti con pre-valutazione IMDb. Scarta o prosegui al casting' },
  { id: 'casting', icon: Users, label: 'Casting', desc: 'Gli agenti propongono candidati per il cast del tuo film' },
  { id: 'screenplay', icon: BookOpen, label: 'Sceneggiatura', desc: 'Sceneggiatura completa e creazione della locandina (Fase 2)' },
  { id: 'pre_production', icon: Clapperboard, label: 'Pre-Produzione', desc: 'Film pronti per le riprese. Rimasterizza o lancia il Ciak! (Fase 2)' },
  { id: 'shooting', icon: Play, label: 'Ciak! Si Gira!', desc: 'Film in fase di ripresa. Velocizza o attendi il completamento (Fase 2)' },
];

// ============ CREATION TAB ============
const CreationTab = ({ api, refreshUser, refreshCounts }) => {
  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('');
  const [selectedSubgenres, setSelectedSubgenres] = useState([]);
  const [preScreenplay, setPreScreenplay] = useState('');
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [locFilter, setLocFilter] = useState('all');
  const [genres, setGenres] = useState({});
  const [locations, setLocations] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState(1); // 1=title/genre, 2=screenplay, 3=location

  useEffect(() => {
    api.get('/genres').then(r => setGenres(r.data || {})).catch(() => {});
    api.get('/locations').then(r => setLocations(r.data || [])).catch(() => {});
  }, [api]);

  const toggleSubgenre = (sg) => {
    if (selectedSubgenres.includes(sg)) {
      setSelectedSubgenres(selectedSubgenres.filter(s => s !== sg));
    } else if (selectedSubgenres.length < 3) {
      setSelectedSubgenres([...selectedSubgenres, sg]);
    }
  };

  const toggleLocation = (name) => {
    if (selectedLocations.includes(name)) {
      setSelectedLocations(selectedLocations.filter(l => l !== name));
    } else {
      setSelectedLocations([...selectedLocations, name]);
    }
  };

  const handleSubmit = async () => {
    if (!title.trim() || !genre || selectedSubgenres.length === 0 || preScreenplay.length < 100 || selectedLocations.length === 0) {
      toast.error('Compila tutti i campi. Seleziona almeno 1 sottogenere e 1 location.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/film-pipeline/create', {
        title, genre, subgenres: selectedSubgenres, pre_screenplay: preScreenplay, locations: selectedLocations
      });
      toast.success(res.data.message);
      setTitle(''); setGenre(''); setSelectedSubgenres([]); setPreScreenplay(''); setSelectedLocations([]); setStep(1);
      refreshUser(); refreshCounts();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setSubmitting(false);
    }
  };

  const subgenresList = genres[genre]?.subgenres || [];

  const CATEGORY_LABELS = { studios: 'Studi', cities: 'Citta', nature: 'Natura', historical: 'Storici' };
  const categories = ['all', ...new Set(locations.map(l => l.category))];
  const filteredLocations = locFilter === 'all' ? locations : locations.filter(l => l.category === locFilter);

  return (
    <div className="space-y-4">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
        {['Titolo & Genere', 'Pre-Sceneggiatura', 'Location'].map((s, i) => (
          <React.Fragment key={i}>
            {i > 0 && <ChevronRight className="w-3 h-3" />}
            <span className={`px-2 py-0.5 rounded ${step === i + 1 ? 'bg-yellow-500/20 text-yellow-400 font-medium' : 'text-gray-600'}`}>{s}</span>
          </React.Fragment>
        ))}
      </div>

      {step === 1 && (
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><Film className="w-4 h-4 text-yellow-400" />Titolo & Genere</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Titolo del Film</label>
              <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Il titolo del tuo capolavoro..."
                className="bg-black/30 border-gray-700 text-white" maxLength={80} data-testid="film-title-input" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Genere</label>
              <Select value={genre} onValueChange={v => { setGenre(v); setSelectedSubgenres([]); }}>
                <SelectTrigger className="bg-black/30 border-gray-700 text-white" data-testid="genre-select">
                  <SelectValue placeholder="Seleziona un genere..." />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(genres).map(([key, val]) => (
                    <SelectItem key={key} value={key} data-testid={`genre-${key}`}>{val.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {genre && subgenresList.length > 0 && (
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Sottogenere (max 3)</label>
                <div className="flex flex-wrap gap-1.5">
                  {subgenresList.map(sg => (
                    <Badge key={sg} variant={selectedSubgenres.includes(sg) ? "default" : "outline"}
                      className={`cursor-pointer text-[10px] px-2 py-1 transition-all ${selectedSubgenres.includes(sg) ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50 hover:bg-cyan-500/30' : 'border-gray-700 text-gray-400 hover:border-gray-500'}`}
                      onClick={() => toggleSubgenre(sg)}
                      data-testid={`subgenre-${sg}`}>{sg}</Badge>
                  ))}
                </div>
                {selectedSubgenres.length > 0 && (
                  <p className="text-[10px] text-cyan-400 mt-1">{selectedSubgenres.length}/3 selezionati</p>
                )}
              </div>
            )}
            <Button disabled={!title.trim() || !genre || selectedSubgenres.length === 0} onClick={() => setStep(2)}
              className="w-full bg-yellow-600 hover:bg-yellow-700" data-testid="step1-next">
              Avanti <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><BookOpen className="w-4 h-4 text-cyan-400" />Pre-Sceneggiatura</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="p-2 bg-black/30 rounded border border-gray-800 text-[10px] text-gray-500">
              <span className="text-yellow-400">{title}</span> &bull; {genres[genre]?.name} &bull; {selectedSubgenres.join(', ')}
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Scrivi la sinossi del tuo film (100-500 caratteri)</label>
              <Textarea value={preScreenplay} onChange={e => setPreScreenplay(e.target.value.slice(0, 500))}
                placeholder="Racconta brevemente la trama del tuo film... La tua creativita' influenzera' la valutazione!"
                className="bg-black/30 border-gray-700 text-white min-h-[120px]" data-testid="pre-screenplay-input" />
              <div className="flex justify-between mt-1">
                <span className={`text-[10px] ${preScreenplay.length < 100 ? 'text-red-400' : preScreenplay.length >= 400 ? 'text-green-400' : 'text-yellow-400'}`}>
                  {preScreenplay.length}/500 {preScreenplay.length < 100 ? '(minimo 100)' : preScreenplay.length >= 400 ? 'Eccellente!' : ''}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)} className="border-gray-700 text-gray-400">Indietro</Button>
              <Button disabled={preScreenplay.length < 100} onClick={() => setStep(3)}
                className="flex-1 bg-cyan-600 hover:bg-cyan-700" data-testid="step2-next">
                Avanti <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <Card className="bg-[#1A1A1B] border-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><MapPin className="w-4 h-4 text-green-400" />Location</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="p-2 bg-black/30 rounded border border-gray-800 text-[10px] text-gray-500">
              <span className="text-yellow-400">{title}</span> &bull; {genres[genre]?.name} &bull; {selectedSubgenres.join(', ')}
            </div>
            {/* Category filter */}
            <div className="flex flex-wrap gap-1">
              {categories.map(cat => (
                <button key={cat} onClick={() => setLocFilter(cat)}
                  className={`px-2 py-1 rounded text-[10px] border transition-all ${locFilter === cat ? 'border-green-500 bg-green-500/10 text-green-400' : 'border-gray-700 text-gray-500 hover:border-gray-600'}`}
                  data-testid={`loc-filter-${cat}`}>
                  {cat === 'all' ? 'Tutti' : CATEGORY_LABELS[cat] || cat}
                </button>
              ))}
            </div>
            {selectedLocations.length > 0 && (
              <p className="text-[10px] text-green-400">{selectedLocations.length} location selezionate</p>
            )}
            <div className="grid grid-cols-2 gap-1.5 max-h-[300px] overflow-y-auto pr-1">
              {filteredLocations.map(loc => (
                <button key={loc.name} onClick={() => toggleLocation(loc.name)}
                  className={`p-2 rounded text-left border transition-all ${selectedLocations.includes(loc.name) ? 'border-green-500 bg-green-500/10' : 'border-gray-700 hover:border-gray-600'}`}
                  data-testid={`loc-${loc.name.replace(/\s/g, '-')}`}>
                  <p className="text-xs font-medium text-gray-200 truncate">{loc.name}</p>
                  <p className="text-[9px] text-gray-500">${loc.cost_per_day?.toLocaleString()}/giorno &bull; {CATEGORY_LABELS[loc.category] || loc.category}</p>
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(2)} className="border-gray-700 text-gray-400">Indietro</Button>
              <Button disabled={selectedLocations.length === 0 || submitting} onClick={handleSubmit}
                className="flex-1 bg-green-600 hover:bg-green-700" data-testid="submit-proposal">
                {submitting ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : <Star className="w-4 h-4 mr-1" />}
                Proponi Film (1 CP)
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// ============ PROPOSALS TAB ============
const ProposalsTab = ({ api, refreshUser, refreshCounts }) => {
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const res = await api.get('/film-pipeline/proposals');
      setProposals(res.data.proposals || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); }, [fetch]);

  const discard = async (id) => {
    try {
      const res = await api.post(`/film-pipeline/${id}/discard`);
      toast.success(res.data.message);
      fetch(); refreshCounts();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const advance = async (id) => {
    try {
      const res = await api.post(`/film-pipeline/${id}/advance-to-casting`);
      toast.success(res.data.message);
      fetch(); refreshUser(); refreshCounts();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;
  if (!proposals.length) return <div className="text-center py-12 text-gray-500"><ClipboardList className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessuna proposta. Crea un film nella sezione Creazione!</p></div>;

  return (
    <div className="space-y-3">
      {proposals.map(p => (
        <Card key={p.id} className="bg-[#1A1A1B] border-gray-800" data-testid={`proposal-${p.id}`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h3 className="font-semibold text-sm">{p.title}</h3>
                <p className="text-[10px] text-gray-500">{p.genre} &bull; {p.subgenre} &bull; {p.location?.name}</p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-yellow-400" />
                  <span className={`text-lg font-bold ${p.pre_imdb_score >= 7 ? 'text-green-400' : p.pre_imdb_score >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {p.pre_imdb_score}
                  </span>
                </div>
                <p className="text-[9px] text-gray-600">Pre-IMDb</p>
              </div>
            </div>
            <p className="text-[10px] text-gray-400 mb-2 line-clamp-2 italic">"{p.pre_screenplay}"</p>
            {/* Factors */}
            <div className="flex flex-wrap gap-1 mb-2">
              {Object.entries(p.pre_imdb_factors || {}).map(([k, v]) => (
                <span key={k} className="text-[9px] px-1.5 py-0.5 bg-white/5 rounded text-gray-400">{k.replace(/_/g, ' ')}: {v}</span>
              ))}
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" className="text-xs border-red-800 text-red-400 hover:bg-red-500/10"
                onClick={() => discard(p.id)} data-testid={`discard-${p.id}`}>
                <ThumbsDown className="w-3 h-3 mr-1" /> Scarta
              </Button>
              <Button size="sm" className="flex-1 bg-cyan-700 hover:bg-cyan-800 text-xs"
                onClick={() => advance(p.id)} data-testid={`advance-${p.id}`}>
                <Users className="w-3 h-3 mr-1" /> Prosegui al Casting (2 CP)
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// ============ CASTING TAB ============
const CastingTab = ({ api, refreshUser, refreshCounts }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);

  const fetch = useCallback(async () => {
    try {
      const res = await api.get('/film-pipeline/casting');
      setFilms(res.data.casting_films || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); const i = setInterval(fetch, 30000); return () => clearInterval(i); }, [fetch]);

  const speedUp = async (filmId, roleType) => {
    setActionLoading(`speed-${filmId}-${roleType}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/speed-up-casting`, { role_type: roleType });
      toast.success(res.data.message);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const selectCast = async (filmId, roleType, proposalId) => {
    setActionLoading(`select-${proposalId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/select-cast`, { role_type: roleType, proposal_id: proposalId });
      if (res.data.accepted) {
        toast.success(res.data.message);
        if (res.data.casting_complete) toast.success('Casting completo! Puoi procedere alla sceneggiatura.');
      } else {
        toast.error(res.data.message);
      }
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const advanceToScreenplay = async (filmId) => {
    setActionLoading(`adv-${filmId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/advance-to-screenplay`);
      toast.success(res.data.message);
      refreshUser(); refreshCounts(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;
  if (!films.length) return <div className="text-center py-12 text-gray-500"><Users className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessun film in casting.</p></div>;

  const roleLabels = { directors: 'Regista', screenwriters: 'Sceneggiatore', actors: 'Attori', composers: 'Compositore' };
  const roleIcons = { directors: '🎬', screenwriters: '📝', actors: '🎭', composers: '🎵' };

  return (
    <div className="space-y-3">
      {films.map(f => {
        const cast = f.cast || {};
        const castComplete = cast.director && cast.screenwriter && cast.composer && cast.actors?.length > 0;
        return (
          <Card key={f.id} className="bg-[#1A1A1B] border-gray-800" data-testid={`casting-film-${f.id}`}>
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-sm">{f.title}</h3>
                  <p className="text-[10px] text-gray-500">{f.genre} &bull; {f.subgenre} &bull; Pre-IMDb: <span className="text-yellow-400">{f.pre_imdb_score}</span></p>
                </div>
                {castComplete && (
                  <Button size="sm" className="bg-green-700 hover:bg-green-800 text-xs" onClick={() => advanceToScreenplay(f.id)}
                    disabled={actionLoading === `adv-${f.id}`} data-testid={`advance-screenplay-${f.id}`}>
                    {actionLoading === `adv-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3 mr-1" />}
                    Prosegui (2 CP)
                  </Button>
                )}
              </div>

              <Button variant="outline" size="sm" className="w-full text-xs border-gray-700 mb-2"
                onClick={() => setSelectedFilm(selectedFilm === f.id ? null : f.id)}>
                {selectedFilm === f.id ? 'Chiudi Casting' : 'Gestisci Casting'}
              </Button>

              {selectedFilm === f.id && (
                <div className="space-y-3 mt-2">
                  {Object.entries(f.cast_proposals || {}).map(([role, proposals]) => {
                    const selected = role === 'actors' ? cast.actors?.length > 0 : cast[role === 'directors' ? 'director' : role === 'screenwriters' ? 'screenwriter' : 'composer'];
                    const available = proposals.filter(p => p.status === 'available');
                    const pending = proposals.filter(p => p.status === 'pending');

                    return (
                      <div key={role} className={`p-2 rounded border ${selected ? 'border-green-800 bg-green-500/5' : 'border-gray-700'}`}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-medium">{roleIcons[role]} {roleLabels[role]}</span>
                          {selected ? (
                            <Badge className="bg-green-500/20 text-green-400 text-[9px]">
                              <Check className="w-3 h-3 mr-0.5" />
                              {role === 'actors' ? `${cast.actors.length} scelti` : 'Scelto'}
                            </Badge>
                          ) : (
                            <div className="flex items-center gap-1">
                              <Badge className="bg-cyan-500/20 text-cyan-400 text-[9px]">{available.length} disponibili</Badge>
                              {pending.length > 0 && (
                                <Button size="sm" className="h-5 px-1.5 text-[9px] bg-yellow-600 hover:bg-yellow-700"
                                  disabled={actionLoading === `speed-${f.id}-${role}`}
                                  onClick={() => speedUp(f.id, role)}>
                                  <Zap className="w-2.5 h-2.5 mr-0.5" /> Sblocca ({pending.length})
                                </Button>
                              )}
                            </div>
                          )}
                        </div>

                        {!selected && available.map(prop => (
                          <div key={prop.id} className="flex items-center justify-between p-1.5 mb-1 bg-black/20 rounded border border-gray-800">
                            <div className="flex-1">
                              <p className="text-xs font-medium">{prop.person?.name}</p>
                              <p className="text-[9px] text-gray-500">
                                da {prop.agent_name} &bull; ${prop.cost?.toLocaleString()}
                                {prop.person?.skills && (
                                  <span className="ml-1 text-gray-600">
                                    &bull; Avg: {Math.round(Object.values(prop.person.skills).reduce((a, b) => a + b, 0) / Math.max(1, Object.keys(prop.person.skills).length))}
                                  </span>
                                )}
                              </p>
                            </div>
                            <Button size="sm" className="h-6 px-2 text-[10px] bg-cyan-700 hover:bg-cyan-800"
                              disabled={actionLoading === `select-${prop.id}`}
                              onClick={() => selectCast(f.id, role, prop.id)} data-testid={`select-${prop.id}`}>
                              {actionLoading === `select-${prop.id}` ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ThumbsUp className="w-3 h-3 mr-0.5" />}
                              Scegli
                            </Button>
                          </div>
                        ))}

                        {!selected && pending.length > 0 && available.length === 0 && (
                          <div className="flex items-center gap-1.5 p-2 text-[10px] text-gray-500">
                            <Clock className="w-3 h-3 animate-pulse text-yellow-500" />
                            {pending.length} agenti in arrivo...
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

// ============ SCREENPLAY TAB ============
const ScreenplayTab = ({ api, refreshUser, refreshCounts }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState({});
  const [manualText, setManualText] = useState({});
  const [actionLoading, setActionLoading] = useState(null);

  const fetch = useCallback(async () => {
    try { const res = await api.get('/film-pipeline/screenplay'); setFilms(res.data.films || []); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); }, [fetch]);

  const writeScreenplay = async (filmId) => {
    const m = mode[filmId] || 'ai';
    setActionLoading(filmId);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/write-screenplay`, {
        mode: m, manual_text: m === 'manual' ? manualText[filmId] || '' : undefined
      });
      toast.success(res.data.message);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const advance = async (filmId) => {
    setActionLoading(`adv-${filmId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/advance-to-preproduction`);
      toast.success(res.data.message);
      refreshUser(); refreshCounts(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;
  if (!films.length) return <div className="text-center py-12 text-gray-500"><BookOpen className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessun film in fase sceneggiatura.</p></div>;

  return (
    <div className="space-y-3">
      {films.map(f => (
        <Card key={f.id} className="bg-[#1A1A1B] border-gray-800" data-testid={`screenplay-film-${f.id}`}>
          <CardContent className="p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-sm">{f.title}</h3>
                <p className="text-[10px] text-gray-500">{f.genre} &bull; {f.subgenre} &bull; Pre-IMDb: <span className="text-yellow-400">{f.pre_imdb_score}</span></p>
              </div>
              {f.screenplay && (
                <Button size="sm" className="bg-green-700 hover:bg-green-800 text-xs" onClick={() => advance(f.id)}
                  disabled={actionLoading === `adv-${f.id}`} data-testid={`advance-preprod-${f.id}`}>
                  <ChevronRight className="w-3 h-3 mr-1" /> Pre-Produzione (3 CP)
                </Button>
              )}
            </div>

            {/* Pre-screenplay (always visible, not editable) */}
            <div className="p-2 bg-yellow-500/5 rounded border border-yellow-500/20">
              <p className="text-[9px] text-yellow-400 font-medium mb-0.5">Pre-Sceneggiatura (originale)</p>
              <p className="text-[10px] text-gray-400 italic">"{f.pre_screenplay}"</p>
            </div>

            {f.screenplay ? (
              <div className="p-2 bg-green-500/5 rounded border border-green-500/20">
                <p className="text-[9px] text-green-400 font-medium mb-0.5">Sceneggiatura completata ({f.screenplay_mode === 'ai' ? 'AI' : f.screenplay_mode === 'manual' ? 'Manuale' : 'Solo Pre'})</p>
                <p className="text-[10px] text-gray-300 line-clamp-4">{f.screenplay}</p>
              </div>
            ) : (
              <>
                <div className="flex gap-1.5">
                  {[
                    { id: 'ai', label: 'AI ($80K)', desc: 'Sceneggiatura generata da AI' },
                    { id: 'pre_only', label: 'Solo Pre ($0)', desc: 'Malus -15% qualita' },
                    { id: 'manual', label: 'Scrivi ($20K)', desc: 'Scrivi tu la sceneggiatura' }
                  ].map(opt => (
                    <button key={opt.id} onClick={() => setMode(prev => ({ ...prev, [f.id]: opt.id }))}
                      className={`flex-1 p-2 rounded text-center border transition-all ${(mode[f.id] || 'ai') === opt.id ? 'border-cyan-500 bg-cyan-500/10' : 'border-gray-700'}`}>
                      <p className="text-[10px] font-medium text-gray-200">{opt.label}</p>
                      <p className="text-[8px] text-gray-500">{opt.desc}</p>
                    </button>
                  ))}
                </div>

                {(mode[f.id] || 'ai') === 'manual' && (
                  <Textarea value={manualText[f.id] || ''} onChange={e => setManualText(prev => ({ ...prev, [f.id]: e.target.value }))}
                    placeholder="Scrivi la sceneggiatura completa basandoti sulla pre-sceneggiatura sopra..."
                    className="bg-black/30 border-gray-700 text-white min-h-[100px] text-xs" />
                )}

                <Button onClick={() => writeScreenplay(f.id)} disabled={actionLoading === f.id}
                  className="w-full bg-cyan-700 hover:bg-cyan-800 text-xs" data-testid={`write-screenplay-${f.id}`}>
                  {actionLoading === f.id ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <BookOpen className="w-3 h-3 mr-1" />}
                  {(mode[f.id] || 'ai') === 'ai' ? 'Genera Sceneggiatura AI' : (mode[f.id] || 'ai') === 'manual' ? 'Salva Sceneggiatura' : 'Usa Solo Pre-Sceneggiatura'}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// ============ PRE-PRODUCTION TAB ============
const PreProductionTab = ({ api, refreshUser, refreshCounts }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

  const fetch = useCallback(async () => {
    try { const res = await api.get('/film-pipeline/pre-production'); setFilms(res.data.films || []); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); const i = setInterval(fetch, 30000); return () => clearInterval(i); }, [fetch]);

  const remaster = async (filmId) => {
    setActionLoading(`rem-${filmId}`);
    try { const res = await api.post(`/film-pipeline/${filmId}/remaster`); toast.success(res.data.message); refreshUser(); fetch(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
  };

  const speedUpRemaster = async (filmId) => {
    setActionLoading(`speed-${filmId}`);
    try { const res = await api.post(`/film-pipeline/${filmId}/speed-up-remaster`); toast.success(res.data.message); refreshUser(); fetch(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
  };

  const startShooting = async (filmId) => {
    setActionLoading(`shoot-${filmId}`);
    try { const res = await api.post(`/film-pipeline/${filmId}/start-shooting`); toast.success(res.data.message); refreshUser(); refreshCounts(); fetch(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;
  if (!films.length) return <div className="text-center py-12 text-gray-500"><Clapperboard className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessun film in pre-produzione.</p></div>;

  return (
    <div className="space-y-3">
      {films.map(f => {
        const remasterInProgress = f.remaster_started_at && !f.remaster_completed;
        const remasterDone = f.remaster_completed;
        return (
          <Card key={f.id} className="bg-[#1A1A1B] border-gray-800" data-testid={`preprod-film-${f.id}`}>
            <CardContent className="p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-sm">{f.title}</h3>
                  <p className="text-[10px] text-gray-500">Pre-IMDb: <span className="text-yellow-400">{f.pre_imdb_score}</span>
                    {remasterDone && <span className="text-green-400 ml-1"> +{f.remaster_quality_boost}% remaster</span>}
                  </p>
                </div>
                {f.screenplay_mode && (
                  <Badge className={`text-[9px] ${f.screenplay_mode === 'ai' ? 'bg-cyan-500/20 text-cyan-400' : f.screenplay_mode === 'manual' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-600/20 text-gray-400'}`}>
                    {f.screenplay_mode === 'ai' ? 'AI' : f.screenplay_mode === 'manual' ? 'Manuale' : 'Base'}
                  </Badge>
                )}
              </div>

              {remasterInProgress && (
                <div className="p-2 bg-yellow-500/10 rounded border border-yellow-500/20">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <RefreshCw className="w-3 h-3 animate-spin text-yellow-400" />
                      <span className="text-[10px] text-yellow-300">Rimasterizzazione in corso... {Math.round(f.remaster_remaining_minutes || 0)} min</span>
                    </div>
                    <Button size="sm" className="h-5 px-2 text-[9px] bg-yellow-600 hover:bg-yellow-700"
                      disabled={actionLoading === `speed-${f.id}`} onClick={() => speedUpRemaster(f.id)}>
                      <Zap className="w-2.5 h-2.5 mr-0.5" /> $40K
                    </Button>
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                {!f.remaster_started_at && (
                  <Button size="sm" variant="outline" className="text-xs border-yellow-700 text-yellow-400"
                    disabled={actionLoading === `rem-${f.id}`} onClick={() => remaster(f.id)} data-testid={`remaster-${f.id}`}>
                    <Star className="w-3 h-3 mr-1" /> Rimasterizza
                  </Button>
                )}
                <Button size="sm" className="flex-1 bg-red-700 hover:bg-red-800 text-xs"
                  disabled={remasterInProgress || actionLoading === `shoot-${f.id}`}
                  onClick={() => startShooting(f.id)} data-testid={`ciak-${f.id}`}>
                  <Play className="w-3 h-3 mr-1" /> Ciak! (3 CP)
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

// ============ SHOOTING TAB ============
const ShootingTab = ({ api, refreshUser, refreshCounts }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [releaseResult, setReleaseResult] = useState(null);

  const fetch = useCallback(async () => {
    try { const res = await api.get('/film-pipeline/shooting'); setFilms(res.data.films || []); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); const i = setInterval(fetch, 15000); return () => clearInterval(i); }, [fetch]);

  const speedUp = async (filmId, option) => {
    setActionLoading(`speed-${filmId}`);
    try { const res = await api.post(`/film-pipeline/${filmId}/speed-up-shooting`, { option }); toast.success(res.data.message); refreshUser(); fetch(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Errore'); } finally { setActionLoading(null); }
  };

  const release = async (filmId) => {
    setActionLoading(`rel-${filmId}`);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/release`);
      setReleaseResult(res.data);
      toast.success(`${res.data.title} al cinema! Qualita: ${res.data.quality_score}`);
      refreshUser(); refreshCounts(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  if (loading) return <div className="text-center py-8 text-gray-500">Caricamento...</div>;

  return (
    <div className="space-y-3">
      {films.length === 0 && !releaseResult && (
        <div className="text-center py-12 text-gray-500"><Play className="w-10 h-10 mx-auto mb-2 opacity-30" /><p>Nessun film in ripresa.</p></div>
      )}

      {films.map(f => {
        const progress = Math.min(100, ((f.shooting_day_current || 0) / Math.max(1, f.shooting_days || 5)) * 100);
        const completed = f.shooting_completed || progress >= 100;
        return (
          <Card key={f.id} className={`bg-[#1A1A1B] ${completed ? 'border-green-800' : 'border-gray-800'}`} data-testid={`shooting-film-${f.id}`}>
            <CardContent className="p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-sm">{f.title}</h3>
                  <p className="text-[10px] text-gray-500">
                    Giorno {f.shooting_day_current || 0}/{f.shooting_days || 5}
                    {!completed && f.shooting_hours_remaining != null && <span> &bull; ~{Math.round(f.shooting_hours_remaining * 60)}min rimanenti</span>}
                  </p>
                </div>
                {completed ? (
                  <Badge className="bg-green-500/20 text-green-400 text-[10px]">Completato!</Badge>
                ) : (
                  <Badge className="bg-blue-500/20 text-blue-400 text-[10px]">{Math.round(progress)}%</Badge>
                )}
              </div>

              {/* Progress bar */}
              <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all bg-gradient-to-r from-blue-500 to-green-500" style={{ width: `${progress}%` }} />
              </div>

              {completed ? (
                <Button className="w-full bg-green-700 hover:bg-green-800 text-xs" disabled={actionLoading === `rel-${f.id}`}
                  onClick={() => release(f.id)} data-testid={`release-${f.id}`}>
                  {actionLoading === `rel-${f.id}` ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <Film className="w-3 h-3 mr-1" />}
                  Rilascia al Cinema!
                </Button>
              ) : (
                <div className="flex gap-1.5">
                  <Button size="sm" variant="outline" className="flex-1 text-[9px] border-gray-700" disabled={actionLoading === `speed-${f.id}`}
                    onClick={() => speedUp(f.id, 'fast')}>
                    <Zap className="w-2.5 h-2.5 mr-0.5" /> 50% ($50K)
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1 text-[9px] border-yellow-700 text-yellow-400" disabled={actionLoading === `speed-${f.id}`}
                    onClick={() => speedUp(f.id, 'faster')}>
                    <Zap className="w-2.5 h-2.5 mr-0.5" /> 80% ($90K)
                  </Button>
                  <Button size="sm" className="flex-1 text-[9px] bg-red-700 hover:bg-red-800" disabled={actionLoading === `speed-${f.id}`}
                    onClick={() => speedUp(f.id, 'instant')}>
                    <Zap className="w-2.5 h-2.5 mr-0.5" /> Subito! ($150K)
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}

      {/* Release Result Dialog */}
      {releaseResult && (
        <Card className="bg-[#1A1A1B] border-yellow-600 ring-1 ring-yellow-500/30" data-testid="release-result">
          <CardContent className="p-4 text-center space-y-3">
            <Film className="w-10 h-10 mx-auto text-yellow-400" />
            <h2 className="text-lg font-bold">{releaseResult.title}</h2>
            <div className={`text-3xl font-black ${releaseResult.quality_score >= 70 ? 'text-green-400' : releaseResult.quality_score >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
              {releaseResult.quality_score}
            </div>
            <Badge className={`${releaseResult.tier === 'masterpiece' ? 'bg-yellow-500 text-black' : releaseResult.tier === 'excellent' ? 'bg-green-500/30 text-green-400' : 'bg-gray-600'}`}>
              {releaseResult.tier_label}
            </Badge>
            <div className="text-left space-y-1 text-[10px] text-gray-400 p-2 bg-black/30 rounded">
              <p className="text-xs font-medium text-gray-200 mb-1">Riepilogo Costi</p>
              <p>Denaro totale: <span className="text-yellow-400">${releaseResult.cost_summary?.total_money?.toLocaleString()}</span></p>
              <p>CinePass totali: <span className="text-cyan-400">{releaseResult.cost_summary?.total_cinepass} CP</span></p>
              <p className="mt-1 text-xs font-medium text-gray-200">Modificatori</p>
              <p>Pre-IMDb: {releaseResult.modifiers?.pre_imdb} | Sceneggiatura: {releaseResult.modifiers?.screenplay > 0 ? '+' : ''}{releaseResult.modifiers?.screenplay}</p>
              <p>Remaster: +{releaseResult.modifiers?.remaster || 0} | Buzz: {releaseResult.modifiers?.buzz > 0 ? '+' : ''}{releaseResult.modifiers?.buzz}</p>
              <p>Cast: {releaseResult.modifiers?.cast_quality}</p>
              <p className="text-green-400 mt-1">+{releaseResult.xp_gained} XP guadagnati!</p>
            </div>
            <Button onClick={() => setReleaseResult(null)} variant="outline" className="border-gray-700 text-xs">Chiudi</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// ============ BUZZ SECTION ============
const BuzzSection = ({ api, refreshUser }) => {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState(null);

  const fetch = useCallback(async () => {
    try { const res = await api.get('/film-pipeline/buzz'); setFilms(res.data.films || []); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }, [api]);

  useEffect(() => { fetch(); }, [fetch]);

  const vote = async (filmId, voteType) => {
    setVoting(filmId);
    try {
      const res = await api.post(`/film-pipeline/${filmId}/buzz-vote`, { vote: voteType });
      toast.success(res.data.message);
      refreshUser(); fetch();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setVoting(null); }
  };

  if (loading || !films.length) return null;

  return (
    <Card className="bg-[#1A1A1B] border-purple-900/50 mt-4" data-testid="buzz-section">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-purple-400" /> Film in Arrivo — Vota l'Hype!
        </CardTitle>
        <p className="text-[10px] text-gray-500">Vota i film di altri produttori e guadagna CinePass</p>
      </CardHeader>
      <CardContent className="space-y-2">
        {films.map(f => (
          <div key={f.id} className="p-2 bg-black/30 rounded border border-purple-900/20" data-testid={`buzz-film-${f.id}`}>
            <div className="flex items-center justify-between mb-1">
              <div>
                <p className="text-xs font-medium">{f.title}</p>
                <p className="text-[9px] text-gray-500">{f.genre} &bull; di {f.owner_nickname} &bull; Pre-IMDb: {f.pre_imdb_score}</p>
              </div>
              <div className="text-[9px] text-gray-600">{f.total_votes} voti</div>
            </div>
            <p className="text-[9px] text-gray-500 italic mb-1.5">"{f.pre_screenplay}"</p>
            <div className="flex gap-1.5">
              <Button size="sm" className="flex-1 h-6 text-[9px] bg-green-700 hover:bg-green-800" disabled={voting === f.id}
                onClick={() => vote(f.id, 'high')} data-testid={`buzz-high-${f.id}`}>
                Hype!
              </Button>
              <Button size="sm" variant="outline" className="flex-1 h-6 text-[9px] border-gray-600" disabled={voting === f.id}
                onClick={() => vote(f.id, 'medium')}>
                Interessante
              </Button>
              <Button size="sm" variant="outline" className="flex-1 h-6 text-[9px] border-red-800 text-red-400" disabled={voting === f.id}
                onClick={() => vote(f.id, 'low')}>
                Meh
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

// ============ PLACEHOLDER TAB (Phase 2) ============
const PlaceholderTab = ({ icon: Icon, name }) => (
  <div className="text-center py-16 text-gray-500">
    <Icon className="w-12 h-12 mx-auto mb-3 opacity-20" />
    <p className="text-sm font-medium mb-1">{name}</p>
    <p className="text-[10px]">In arrivo nella Fase 2</p>
  </div>
);

// ============ MAIN PAGE ============
const FilmPipeline = () => {
  const { api, refreshUser } = useContext(AuthContext);
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'creation';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [counts, setCounts] = useState({});
  const [showInfo, setShowInfo] = useState(false);

  const refreshCounts = useCallback(async () => {
    try {
      const res = await api.get('/film-pipeline/counts');
      setCounts(res.data);
    } catch (e) { console.error(e); }
  }, [api]);

  useEffect(() => { refreshCounts(); }, [refreshCounts]);

  const getCount = (tab) => {
    const map = {
      creation: counts.creation || 0,
      proposals: counts.proposed || 0,
      casting: counts.casting || 0,
      screenplay: counts.screenplay || 0,
      pre_production: counts.pre_production || 0,
      shooting: counts.shooting || 0
    };
    return map[tab] || 0;
  };

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white p-4 pt-16 pb-20">
      <div className="max-w-lg mx-auto">
        {/* Top Icon Bar */}
        <div className="flex items-center justify-center gap-1 mb-4 bg-[#111] rounded-lg p-1.5 border border-gray-800" data-testid="pipeline-tabs">
          {TABS.map(tab => {
            const count = getCount(tab.id);
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`relative flex items-center justify-center w-10 h-10 rounded-lg transition-all ${
                  isActive ? 'bg-yellow-500/20 text-yellow-400 ring-1 ring-yellow-500/40' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                }`} data-testid={`tab-${tab.id}`}>
                <Icon className="w-4.5 h-4.5" />
                {count > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-[8px] text-white flex items-center justify-center font-bold">
                    {count}
                  </span>
                )}
              </button>
            );
          })}
          <button onClick={() => setShowInfo(true)}
            className="flex items-center justify-center w-10 h-10 rounded-lg text-gray-600 hover:text-gray-400 hover:bg-white/5 transition-all"
            data-testid="info-btn">
            <HelpCircle className="w-4.5 h-4.5" />
          </button>
        </div>

        {/* Max films info */}
        {counts.max_simultaneous && (
          <p className="text-[10px] text-gray-600 text-center mb-3">
            Film attivi: {counts.total_active || 0}/{counts.max_simultaneous}
          </p>
        )}

        {/* Tab Content */}
        {activeTab === 'creation' && <CreationTab api={api} refreshUser={refreshUser} refreshCounts={refreshCounts} />}
        {activeTab === 'proposals' && <ProposalsTab api={api} refreshUser={refreshUser} refreshCounts={refreshCounts} />}
        {activeTab === 'casting' && <CastingTab api={api} refreshUser={refreshUser} refreshCounts={refreshCounts} />}
        {activeTab === 'screenplay' && <ScreenplayTab api={api} refreshUser={refreshUser} refreshCounts={refreshCounts} />}
        {activeTab === 'pre_production' && <PreProductionTab api={api} refreshUser={refreshUser} refreshCounts={refreshCounts} />}
        {activeTab === 'shooting' && <ShootingTab api={api} refreshUser={refreshUser} refreshCounts={refreshCounts} />}

        {/* Buzz Section - visible when on shooting tab */}
        {activeTab === 'shooting' && <BuzzSection api={api} refreshUser={refreshUser} />}
      </div>

      {/* Info Dialog */}
      <Dialog open={showInfo} onOpenChange={setShowInfo}>
        <DialogContent className="bg-[#1A1A1B] border-gray-800 text-white max-w-sm">
          <DialogHeader>
            <DialogTitle>Guida alla Produzione</DialogTitle>
            <DialogDescription className="text-gray-400">Le fasi per creare il tuo film</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            {TABS.map(tab => {
              const Icon = tab.icon;
              return (
                <div key={tab.id} className="flex items-start gap-3 p-2 rounded bg-black/20">
                  <Icon className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-medium">{tab.label}</p>
                    <p className="text-[10px] text-gray-500">{tab.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FilmPipeline;
