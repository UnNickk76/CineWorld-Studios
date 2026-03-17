import React, { useState, useEffect, useContext, useCallback } from 'react';
import { AuthContext, useTranslations } from '../contexts';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import {
  Pencil, ClipboardList, Users, BookOpen, Clapperboard, Play,
  HelpCircle, Star, MapPin, Clock, Check, X, DollarSign,
  Zap, ChevronRight, RefreshCw, ThumbsDown, ThumbsUp, ShoppingCart, Film
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
  const [subgenre, setSubgenre] = useState('');
  const [preScreenplay, setPreScreenplay] = useState('');
  const [location, setLocation] = useState('');
  const [genres, setGenres] = useState({});
  const [locations, setLocations] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState(1); // 1=title/genre, 2=screenplay, 3=location

  useEffect(() => {
    api.get('/genres').then(r => setGenres(r.data || {})).catch(() => {});
    api.get('/locations').then(r => setLocations(r.data || [])).catch(() => {});
  }, [api]);

  const handleSubmit = async () => {
    if (!title.trim() || !genre || !subgenre || preScreenplay.length < 100 || !location) {
      toast.error('Compila tutti i campi. La sinossi deve avere almeno 100 caratteri.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/film-pipeline/create', {
        title, genre, subgenre, pre_screenplay: preScreenplay, location_name: location
      });
      toast.success(res.data.message);
      setTitle(''); setGenre(''); setSubgenre(''); setPreScreenplay(''); setLocation(''); setStep(1);
      refreshUser(); refreshCounts();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setSubmitting(false);
    }
  };

  const subgenres = genres[genre]?.subgenres || [];

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
              <div className="grid grid-cols-4 gap-1.5">
                {Object.entries(genres).map(([key, val]) => (
                  <button key={key} onClick={() => { setGenre(key); setSubgenre(''); }}
                    className={`px-2 py-1.5 rounded text-[10px] border transition-all ${genre === key ? 'border-yellow-500 bg-yellow-500/10 text-yellow-400' : 'border-gray-700 text-gray-400 hover:border-gray-600'}`}
                    data-testid={`genre-${key}`}>{val.name}</button>
                ))}
              </div>
            </div>
            {genre && subgenres.length > 0 && (
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Sottogenere</label>
                <div className="flex flex-wrap gap-1.5">
                  {subgenres.map(sg => (
                    <button key={sg} onClick={() => setSubgenre(sg)}
                      className={`px-2 py-1 rounded text-[10px] border transition-all ${subgenre === sg ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400' : 'border-gray-700 text-gray-400 hover:border-gray-600'}`}
                      data-testid={`subgenre-${sg}`}>{sg}</button>
                  ))}
                </div>
              </div>
            )}
            <Button disabled={!title.trim() || !genre || !subgenre} onClick={() => setStep(2)}
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
              <span className="text-yellow-400">{title}</span> &bull; {genres[genre]?.name} &bull; {subgenre}
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
              <span className="text-yellow-400">{title}</span> &bull; {genres[genre]?.name} &bull; {subgenre}
            </div>
            <div className="grid grid-cols-2 gap-1.5 max-h-[300px] overflow-y-auto pr-1">
              {locations.map(loc => (
                <button key={loc.name} onClick={() => setLocation(loc.name)}
                  className={`p-2 rounded text-left border transition-all ${location === loc.name ? 'border-green-500 bg-green-500/10' : 'border-gray-700 hover:border-gray-600'}`}
                  data-testid={`loc-${loc.name.replace(/\s/g, '-')}`}>
                  <p className="text-xs font-medium text-gray-200 truncate">{loc.name}</p>
                  <p className="text-[9px] text-gray-500">${loc.cost_per_day?.toLocaleString()}/giorno &bull; {loc.category}</p>
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(2)} className="border-gray-700 text-gray-400">Indietro</Button>
              <Button disabled={!location || submitting} onClick={handleSubmit}
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
  const [activeTab, setActiveTab] = useState('creation');
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
        {activeTab === 'screenplay' && <PlaceholderTab icon={BookOpen} name="Sceneggiatura & Locandina" />}
        {activeTab === 'pre_production' && <PlaceholderTab icon={Clapperboard} name="Pre-Produzione" />}
        {activeTab === 'shooting' && <PlaceholderTab icon={Play} name="Ciak! Si Gira!" />}
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
