import React, { useState, useEffect, useContext, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, LanguageContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Star, Clock, Film, Users, MapPin, Clapperboard, Music, Pen,
  ChevronLeft, ChevronRight, Crown, Sparkles, Eye, ShoppingCart,
  Package, Scissors, Timer, ArrowRight, DollarSign, Award
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function StarRating({ rating, size = 'md' }) {
  const sizeClass = size === 'lg' ? 'text-2xl' : size === 'sm' ? 'text-sm' : 'text-lg';
  const color = rating >= 8 ? 'text-yellow-400' : rating >= 6 ? 'text-emerald-400' : rating >= 4 ? 'text-orange-400' : 'text-red-400';
  return (
    <div className="flex items-center gap-1.5">
      <Star className={`${size === 'lg' ? 'w-6 h-6' : 'w-4 h-4'} fill-current ${color}`} />
      <span className={`font-bold ${sizeClass} ${color}`}>{rating}</span>
    </div>
  );
}

function CastAvatar({ person, role, small }) {
  const s = small ? 'w-8 h-8' : 'w-10 h-10';
  return (
    <div className="flex items-center gap-2">
      <img src={person.avatar_url} alt={person.name} className={`${s} rounded-full bg-white/10`} />
      <div className="min-w-0">
        <div className="text-sm font-medium truncate">{person.name}</div>
        <div className="text-xs text-white/50 flex items-center gap-1">
          {role && <span>{role}</span>}
          {person.stars && <span className="text-yellow-400">{'★'.repeat(person.stars)}</span>}
        </div>
      </div>
    </div>
  );
}

function TimeRemaining({ expiresAt }) {
  const [remaining, setRemaining] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const exp = new Date(expiresAt);
      const diff = exp - now;
      if (diff <= 0) { setRemaining('Scaduta'); return; }
      const hours = Math.floor(diff / 3600000);
      const mins = Math.floor((diff % 3600000) / 60000);
      setRemaining(`${hours}h ${mins}m`);
    };
    update();
    const interval = setInterval(update, 60000);
    return () => clearInterval(interval);
  }, [expiresAt]);

  const isUrgent = remaining.startsWith('0h') || remaining.startsWith('1h') || remaining.startsWith('2h');
  return (
    <div className={`flex items-center gap-1 text-xs ${isUrgent ? 'text-red-400' : 'text-white/50'}`}>
      <Timer className="w-3 h-3" />
      <span>{remaining}</span>
    </div>
  );
}

export default function EmergingScreenplays() {
  const { api, user, refreshUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [screenplays, setScreenplays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedScreenplay, setSelectedScreenplay] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [accepting, setAccepting] = useState(false);

  const fetchScreenplays = async () => {
    try {
      const res = await api.get('/emerging-screenplays');
      setScreenplays(res.data);
      // Mark as seen
      await api.post('/emerging-screenplays/mark-seen');
    } catch (err) {
      console.error('Error fetching screenplays:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchScreenplays(); }, []);

  const handleAccept = async (mode) => {
    if (!selectedScreenplay) return;
    setAccepting(true);
    try {
      const res = await api.post('/purchased-screenplays/create-v3-project', {
        screenplay_id: selectedScreenplay.id,
        source: 'emerging',
        mode,  // 'avanzata' | 'veloce'
      });
      toast.success(res.data.message);
      await refreshUser();
      setShowDetail(false);
      // Fire cinematic curtain reveal
      try {
        window.dispatchEvent(new CustomEvent('cineworld:curtain-reveal', {
          detail: {
            title: res.data.project?.title || selectedScreenplay.title,
            subtitle: mode === 'veloce' ? 'Modalità Veloce · fast track' : 'Modalità Avanzata · pipeline guidata',
          },
        }));
      } catch {}
      // Navigate into Pipeline V3 with the new project auto-selected (after curtain)
      const pid = res.data.project_id;
      setTimeout(() => {
        if (pid) navigate(`/create-film?p=${pid}`);
        else navigate('/produci');
      }, 2400);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nell\'acquisto');
    } finally {
      setAccepting(false);
    }
  };

  const genreColors = {
    action: 'bg-red-500/20 text-red-300', comedy: 'bg-yellow-500/20 text-yellow-300',
    drama: 'bg-blue-500/20 text-blue-300', horror: 'bg-purple-500/20 text-purple-300',
    sci_fi: 'bg-cyan-500/20 text-cyan-300', romance: 'bg-pink-500/20 text-pink-300',
    thriller: 'bg-orange-500/20 text-orange-300', animation: 'bg-green-500/20 text-green-300',
    documentary: 'bg-teal-500/20 text-teal-300', fantasy: 'bg-indigo-500/20 text-indigo-300',
    musical: 'bg-fuchsia-500/20 text-fuchsia-300', western: 'bg-amber-500/20 text-amber-300',
    war: 'bg-stone-500/20 text-stone-300', noir: 'bg-gray-500/20 text-gray-300',
    adventure: 'bg-emerald-500/20 text-emerald-300', biographical: 'bg-violet-500/20 text-violet-300',
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-yellow-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white pb-20 pt-16">
      {/* Header */}
      <div className="bg-[#0a0a0a]/95 border-b border-white/5 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')} data-testid="back-btn">
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="font-['Bebas_Neue'] text-2xl tracking-wide" data-testid="page-title">Sceneggiature Emergenti</h1>
            <p className="text-xs text-white/40">Sceneggiature pronte da produrre - scegli e produci!</p>
          </div>
          <Badge className="ml-auto bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
            {screenplays.length} disponibili
          </Badge>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 mt-6">
        {screenplays.length === 0 ? (
          <div className="text-center py-20">
            <Pen className="w-12 h-12 mx-auto text-white/20 mb-4" />
            <h2 className="font-['Bebas_Neue'] text-xl text-white/40">Nessuna sceneggiatura disponibile</h2>
            <p className="text-sm text-white/30 mt-2">Nuove sceneggiature appariranno presto. Torna a controllare!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="screenplays-grid">
            <AnimatePresence>
              {screenplays.map((sp, idx) => (
                <motion.div
                  key={sp.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.08 }}
                >
                  <Card
                    className="bg-white/[0.03] border-white/10 hover:border-yellow-500/30 transition-all cursor-pointer group"
                    onClick={() => { setSelectedScreenplay(sp); setShowDetail(true); }}
                    data-testid={`screenplay-card-${sp.id}`}
                  >
                    <CardContent className="p-4 space-y-3">
                      {/* Title + Genre */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <h3 className="font-['Playfair_Display'] text-lg font-bold truncate group-hover:text-yellow-400 transition-colors">
                              {sp.title}
                            </h3>
                            {sp.is_bestseller && (
                              <span
                                className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-[0_0_12px_rgba(255,120,40,0.5)] animate-pulse"
                                title={`${sp.recent_purchases_7d} studi l'hanno scelta negli ultimi 7 giorni`}
                                data-testid={`bestseller-badge-${sp.id}`}
                              >
                                🔥 Bestseller
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            <Badge className={`text-xs ${genreColors[sp.genre] || 'bg-white/10 text-white/60'}`}>
                              {sp.genre}
                            </Badge>
                            {sp.subgenres?.slice(0, 2).map(sg => (
                              <Badge key={sg} variant="outline" className="text-xs border-white/10 text-white/40">{sg}</Badge>
                            ))}
                          </div>
                        </div>
                        <TimeRemaining expiresAt={sp.expires_at} />
                      </div>

                      {/* Synopsis preview */}
                      <p className="text-sm text-white/50 line-clamp-2">{sp.synopsis}</p>

                      {/* Screenwriter */}
                      <div className="flex items-center gap-2 bg-white/5 rounded-lg p-2">
                        <Pen className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                        <CastAvatar person={sp.screenwriter} role="Sceneggiatore" small />
                        {sp.is_new_screenwriter && (
                          <Badge className="ml-auto bg-emerald-500/20 text-emerald-400 text-xs">Nuovo</Badge>
                        )}
                      </div>

                      {/* Ratings + Cost */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="text-center">
                            <div className="text-xs text-white/40">Trama</div>
                            <StarRating rating={sp.story_rating} size="sm" />
                          </div>
                          <div className="text-center">
                            <div className="text-xs text-white/40">+Cast</div>
                            <StarRating rating={sp.full_package_rating} size="sm" />
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-white/40">da</div>
                          <div className="font-bold text-yellow-400">${(sp.screenplay_cost / 1000).toFixed(0)}K</div>
                        </div>
                      </div>

                      {/* Cast preview */}
                      <div className="flex items-center gap-1 overflow-hidden">
                        <Users className="w-3 h-3 text-white/30 flex-shrink-0" />
                        <div className="flex -space-x-2">
                          {[sp.proposed_cast?.director, ...(sp.proposed_cast?.actors || [])].filter(Boolean).slice(0, 5).map((p, i) => (
                            <img key={i} src={p.avatar_url} alt="" className="w-6 h-6 rounded-full border border-black/50" />
                          ))}
                        </div>
                        <span className="text-xs text-white/30 ml-1">
                          {(sp.proposed_cast?.actors?.length || 0) + 1} membri
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Detail Dialog */}
      <Dialog open={showDetail} onOpenChange={setShowDetail}>
        <DialogContent className="bg-[#111] border-white/10 text-white max-w-2xl max-h-[90vh] overflow-y-auto">
          {selectedScreenplay && (
            <>
              <DialogHeader>
                <DialogTitle className="font-['Playfair_Display'] text-2xl">{selectedScreenplay.title}</DialogTitle>
                <DialogDescription className="text-white/50">
                  <div className="flex items-center gap-2 flex-wrap mt-1">
                    <Badge className={genreColors[selectedScreenplay.genre] || 'bg-white/10'}>
                      {selectedScreenplay.genre}
                    </Badge>
                    {selectedScreenplay.subgenres?.map(sg => (
                      <Badge key={sg} variant="outline" className="border-white/10 text-white/40">{sg}</Badge>
                    ))}
                    <TimeRemaining expiresAt={selectedScreenplay.expires_at} />
                  </div>
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 mt-2">
                {/* Synopsis */}
                <div className="bg-white/5 rounded-lg p-4">
                  <h4 className="font-['Bebas_Neue'] text-sm text-yellow-500 mb-2">Sinossi</h4>
                  <p className="text-sm text-white/70 leading-relaxed">{selectedScreenplay.synopsis}</p>
                </div>

                {/* Ratings side by side */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/5 rounded-lg p-3 text-center">
                    <div className="text-xs text-white/40 mb-1">Rating Solo Trama</div>
                    <StarRating rating={selectedScreenplay.story_rating} size="lg" />
                    <div className="text-xs text-white/30 mt-1">Basato sulla sceneggiatura</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3 text-center">
                    <div className="text-xs text-white/40 mb-1">Rating Trama + Cast</div>
                    <StarRating rating={selectedScreenplay.full_package_rating} size="lg" />
                    <div className="text-xs text-white/30 mt-1">Con il cast proposto</div>
                  </div>
                </div>

                {/* Screenwriter */}
                <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-lg p-3">
                  <div className="flex items-center gap-1 mb-2">
                    <Pen className="w-4 h-4 text-yellow-500" />
                    <h4 className="font-['Bebas_Neue'] text-sm text-yellow-500">Sceneggiatore</h4>
                    {selectedScreenplay.is_new_screenwriter && (
                      <Badge className="ml-2 bg-emerald-500/20 text-emerald-400 text-xs">Nuovo talento</Badge>
                    )}
                  </div>
                  <CastAvatar person={selectedScreenplay.screenwriter} role={`${selectedScreenplay.screenwriter.stars}★ - ${selectedScreenplay.screenwriter.fame_category}`} />
                </div>

                {/* Proposed Cast */}
                <div>
                  <h4 className="font-['Bebas_Neue'] text-sm text-white/60 mb-2 flex items-center gap-1">
                    <Users className="w-4 h-4" /> Cast Proposto
                  </h4>
                  <div className="space-y-2">
                    {/* Director */}
                    <div className="bg-white/5 rounded-lg p-2 flex items-center gap-2">
                      <Clapperboard className="w-4 h-4 text-blue-400 flex-shrink-0" />
                      <CastAvatar person={selectedScreenplay.proposed_cast.director} role="Regista" small />
                    </div>
                    {/* Actors */}
                    {selectedScreenplay.proposed_cast.actors?.map((actor, i) => (
                      <div key={actor.id || i} className="bg-white/5 rounded-lg p-2 flex items-center gap-2">
                        <Film className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <CastAvatar person={actor} role={actor.role} small />
                      </div>
                    ))}
                    {/* Composer */}
                    {selectedScreenplay.proposed_cast.composer && (
                      <div className="bg-white/5 rounded-lg p-2 flex items-center gap-2">
                        <Music className="w-4 h-4 text-purple-400 flex-shrink-0" />
                        <CastAvatar person={selectedScreenplay.proposed_cast.composer} role="Compositore" small />
                      </div>
                    )}
                  </div>
                </div>

                {/* Locations + Equipment */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="flex items-center gap-1 mb-1">
                      <MapPin className="w-3 h-3 text-white/40" />
                      <span className="text-xs text-white/40">Location</span>
                    </div>
                    {selectedScreenplay.proposed_locations?.map(loc => (
                      <div key={loc} className="text-sm text-white/70">{loc} ({selectedScreenplay.proposed_location_days?.[loc] || 7}gg)</div>
                    ))}
                  </div>
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="flex items-center gap-1 mb-1">
                      <Package className="w-3 h-3 text-white/40" />
                      <span className="text-xs text-white/40">Equipaggiamento</span>
                    </div>
                    <div className="text-sm text-white/70">{selectedScreenplay.proposed_equipment}</div>
                  </div>
                </div>

                {/* Important note */}
                <div className="bg-yellow-500/5 border border-yellow-500/10 rounded-lg p-3 text-xs text-white/50">
                  <Award className="w-4 h-4 text-yellow-500 inline mr-1" />
                  Il rating finale del film dipenderà anche dai fattori classici di produzione. Il valore visualizzato è una stima indicativa.
                </div>

                {/* Purchase Options */}
                <div className="space-y-3 pt-2">
                  <h4 className="font-['Bebas_Neue'] text-lg text-center">Scegli come produrre</h4>

                  {(() => {
                    const baseCost = selectedScreenplay.full_package_cost || 0;
                    const velociCost = baseCost * 2;
                    const canAvanzata = (user?.funds || 0) >= baseCost;
                    const canVeloce = (user?.funds || 0) >= velociCost;
                    return (
                      <>
                        {/* AVANZATA — guided pipeline */}
                        <button
                          onClick={() => handleAccept('avanzata')}
                          disabled={accepting || !canAvanzata}
                          className="w-full bg-emerald-500/5 hover:bg-emerald-500/10 border border-emerald-500/30 hover:border-emerald-500/60 rounded-xl p-4 text-left transition-all disabled:opacity-40 group"
                          data-testid="screenplay-mode-avanzata"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                                <Clapperboard className="w-5 h-5 text-emerald-400" />
                              </div>
                              <div className="min-w-0">
                                <div className="font-bold text-sm group-hover:text-emerald-400 transition-colors">Avanzata</div>
                                <div className="text-xs text-white/50 leading-tight">Pipeline guidata: tutti i passaggi cinematici sbloccati, +XP piena</div>
                              </div>
                            </div>
                            <div className="text-right flex-shrink-0">
                              <div className="font-bold text-emerald-400">${(baseCost / 1000).toFixed(0)}K</div>
                              <ArrowRight className="w-4 h-4 text-white/30 ml-auto" />
                            </div>
                          </div>
                        </button>

                        {/* VELOCE — fast track */}
                        <button
                          onClick={() => handleAccept('veloce')}
                          disabled={accepting || !canVeloce}
                          className="w-full bg-orange-500/5 hover:bg-orange-500/10 border border-orange-500/30 hover:border-orange-500/60 rounded-xl p-4 text-left transition-all disabled:opacity-40 group"
                          data-testid="screenplay-mode-veloce"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0">
                                <Sparkles className="w-5 h-5 text-orange-400" />
                              </div>
                              <div className="min-w-0">
                                <div className="font-bold text-sm group-hover:text-orange-400 transition-colors">Veloce</div>
                                <div className="text-xs text-white/50 leading-tight">Tutto pronto: crea solo locandina e trailer. Salta timers e La Prima. -50% XP.</div>
                              </div>
                            </div>
                            <div className="text-right flex-shrink-0">
                              <div className="font-bold text-orange-400">${(velociCost / 1000).toFixed(0)}K</div>
                              <ArrowRight className="w-4 h-4 text-white/30 ml-auto" />
                            </div>
                          </div>
                        </button>

                        {!canAvanzata && (
                          <p className="text-center text-xs text-red-400">
                            Fondi insufficienti per Avanzata (hai ${(user?.funds / 1000).toFixed(0)}K)
                          </p>
                        )}
                      </>
                    );
                  })()}
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
