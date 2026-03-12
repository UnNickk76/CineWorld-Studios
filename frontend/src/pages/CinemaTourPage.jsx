// CineWorld Studio's - CinemaTourPage
// Extracted from App.js for modularity

import React, { useState, useEffect, useRef, useCallback, useMemo, useContext } from 'react';
import { useNavigate, useLocation, useSearchParams, useParams } from 'react-router-dom';
import { AuthContext, LanguageContext, PlayerPopupContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ScrollArea } from '../components/ui/scroll-area';
import { Slider } from '../components/ui/slider';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '../components/ui/alert-dialog';
import { Checkbox } from '../components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import {
  Film, Star, Award, TrendingUp, Clock, Play, Pause, Volume2, Users, Clapperboard,
  Send, Image, ChevronRight, ChevronDown, ChevronLeft, Menu, X, Settings,
  Zap, Globe, Trophy, Shield, Swords, Heart, MessageSquare, Bell, Home,
  Plus, Minus, Search, Filter, Trash2, Edit, Save, Copy, ExternalLink,
  Check, AlertCircle, Info, HelpCircle, Loader2, RefreshCw, Download,
  Eye, EyeOff, Lock, Unlock, Mail, Phone, Calendar, MapPin, Building,
  Sparkles, Flame, Target, Gamepad2, Music, Palette, Camera, Video,
  BookOpen, Newspaper, Gift, Crown, Medal, Gem, Coins, Wallet,
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, MoreHorizontal, MoreVertical,
  ChevronUp, ChevronsUpDown, Lightbulb, Megaphone, Share2, ThumbsUp,
  ThumbsDown, Bookmark, Flag, AlertTriangle, XCircle, CheckCircle,
  BarChart3, PieChart, Activity, Percent, DollarSign, Hash, AtSign,
  Scissors, Wand2, Brush, Layers, Grid, List, LayoutGrid, Table,
  CircleDollarSign, Store, Package, ShoppingCart, Tag, Receipt,
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const CinemaTourPage = () => {
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [featuredCinemas, setFeaturedCinemas] = useState([]);
  const [activeEvents, setActiveEvents] = useState([]);
  const [myVisits, setMyVisits] = useState({ visits_today: 0, cinemas: [] });
  const [loading, setLoading] = useState(true);
  const [selectedCinema, setSelectedCinema] = useState(null);
  const [cinemaDetails, setCinemaDetails] = useState(null);
  const [reviewRating, setReviewRating] = useState(4);
  const [reviewComment, setReviewComment] = useState('');

  useEffect(() => {
    Promise.all([
      api.get('/tour/featured?limit=12'),
      api.get('/events/active'),
      api.get('/tour/my-visits')
    ]).then(([featured, events, visits]) => {
      setFeaturedCinemas(featured.data);
      setActiveEvents(events.data.events);
      setMyVisits(visits.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [api]);

  const visitCinema = async (cinemaId) => {
    try {
      const res = await api.post(`/tour/cinema/${cinemaId}/visit`);
      toast.success(res.data.message + ` (+${res.data.xp_gained} XP)`);
      const visits = await api.get('/tour/my-visits');
      setMyVisits(visits.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const viewCinemaDetails = async (cinemaId) => {
    setSelectedCinema(cinemaId);
    const res = await api.get(`/tour/cinema/${cinemaId}`);
    setCinemaDetails(res.data);
  };

  const submitReview = async () => {
    try {
      const res = await api.post(`/tour/cinema/${selectedCinema}/review?rating=${reviewRating}&comment=${encodeURIComponent(reviewComment)}`);
      toast.success(`Recensione inviata! (+${res.data.xp_gained} XP)`);
      setReviewComment('');
      viewCinemaDetails(selectedCinema);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const getTierColor = (tier) => {
    const colors = {
      gold: 'from-yellow-500/30 to-yellow-600/30 border-yellow-500',
      purple: 'from-purple-500/30 to-purple-600/30 border-purple-500',
      blue: 'from-blue-500/30 to-blue-600/30 border-blue-500',
      green: 'from-green-500/30 to-green-600/30 border-green-500',
      yellow: 'from-yellow-400/20 to-yellow-500/20 border-yellow-400',
      red: 'from-red-500/20 to-red-600/20 border-red-500'
    };
    return colors[tier] || colors.green;
  };

  if (loading) return <div className="pt-16 flex items-center justify-center h-96"><RefreshCw className="w-8 h-8 animate-spin text-yellow-500" /></div>;


  if (loading) return <LoadingSpinner />;

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="tour-page">
      {/* Active Events Banner */}
      {activeEvents.length > 0 && (
        <div className="mb-4">
          <h2 className="font-['Bebas_Neue'] text-lg mb-2 flex items-center gap-2">
            <Award className="w-5 h-5 text-yellow-500" /> Eventi Mondiali Attivi
          </h2>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {activeEvents.map(event => (
              <Card key={event.id} className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-yellow-500/30 min-w-[200px] flex-shrink-0">
                <CardContent className="p-3">
                  <h3 className="font-semibold text-sm">{event.name_it || event.name}</h3>
                  <p className="text-[10px] text-gray-400">{event.days_remaining} giorni rimanenti</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* My Visits Today */}
      <Card className="bg-[#1A1A1A] border-white/10 mb-4">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
            <MapPin className="w-5 h-5 text-green-400" /> Le Mie Visite Oggi ({myVisits.visits_today})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {myVisits.cinemas.length === 0 ? (
            <p className="text-gray-400 text-sm">Non hai ancora visitato nessun cinema oggi. Esplora e guadagna XP!</p>
          ) : (
            <div className="flex gap-2 overflow-x-auto">
              {myVisits.cinemas.map(c => (
                <Badge key={c.id} className="bg-green-500/20 text-green-400">{c.custom_name}</Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Featured Cinemas */}
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
            <Building className="w-5 h-5 text-yellow-500" /> Cinema in Evidenza
          </CardTitle>
          <CardDescription>Visita i cinema degli altri giocatori e lascia recensioni</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {featuredCinemas.map(cinema => (
              <Card key={cinema.id} className={`bg-gradient-to-br ${getTierColor(cinema.tour_rating?.tier?.color)} border overflow-hidden`}>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    {cinema.logo_url ? (
                      <img src={cinema.logo_url} alt="" className="w-10 h-10 rounded object-cover" />
                    ) : (
                      <div className="w-10 h-10 rounded bg-yellow-500/20 flex items-center justify-center">
                        <Building className="w-5 h-5 text-yellow-500" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-sm truncate">{cinema.name}</h3>
                      <p className="text-[10px] text-gray-400">{cinema.city?.name}, {cinema.country}</p>
                    </div>
                    <Badge className={`text-[10px] ${cinema.tour_rating?.tier?.color === 'gold' ? 'bg-yellow-500 text-black' : 'bg-white/10'}`}>
                      {cinema.tour_rating?.score}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-gray-400 mb-2">
                    <span>{cinema.films_showing} film in sala</span>
                    <span>{cinema.tour_rating?.tier?.name_it || cinema.tour_rating?.tier?.name}</span>
                  </div>
                  <div className="flex items-center gap-1 mb-2">
                    <Avatar className="w-5 h-5"><AvatarImage src={cinema.owner?.avatar_url} /></Avatar>
                    <span className="text-xs text-gray-300">{cinema.owner?.nickname}</span>
                  </div>
                  <div className="flex gap-1">
                    <Button size="sm" className="flex-1 h-7 text-xs bg-yellow-500 text-black" onClick={() => viewCinemaDetails(cinema.id)}>
                      Dettagli
                    </Button>
                    <Button size="sm" variant="outline" className="h-7 text-xs border-green-500/30 text-green-400" onClick={() => visitCinema(cinema.id)} disabled={cinema.owner?.id === user?.id}>
                      Visita
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cinema Details Dialog */}
      <Dialog open={!!selectedCinema} onOpenChange={() => setSelectedCinema(null)}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-2xl max-h-[80vh] overflow-y-auto">
          {cinemaDetails && (
            <>
              <DialogHeader>
                <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
                  {cinemaDetails.cinema.custom_name}
                  <Badge className="bg-yellow-500/20 text-yellow-400">{cinemaDetails.tour_rating?.score}/100</Badge>
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                {/* Owner Info */}
                <div className="flex items-center gap-3 p-3 bg-white/5 rounded">
                  <Avatar className="w-10 h-10"><AvatarImage src={cinemaDetails.owner?.avatar_url} /></Avatar>
                  <div>
                    <p className="font-semibold">{cinemaDetails.owner?.nickname}</p>
                    <p className="text-xs text-gray-400">{cinemaDetails.owner?.production_house_name}</p>
                  </div>
                  <Badge className="ml-auto bg-yellow-500/20 text-yellow-400">Fame: {cinemaDetails.owner?.fame?.toFixed(0)}</Badge>
                </div>

                {/* Cinema Info */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2 bg-white/5 rounded">
                    <p className="text-[10px] text-gray-400">Tipo</p>
                    <p className="font-semibold text-sm">{cinemaDetails.type_info?.name_it || cinemaDetails.type_info?.name}</p>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <p className="text-[10px] text-gray-400">Posizione</p>
                    <p className="font-semibold text-sm">{cinemaDetails.cinema.city?.name}, {cinemaDetails.cinema.country}</p>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <p className="text-[10px] text-gray-400">Schermi</p>
                    <p className="font-semibold text-sm">{cinemaDetails.type_info?.screens || 0}</p>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <p className="text-[10px] text-gray-400">Visite</p>
                    <p className="font-semibold text-sm">{cinemaDetails.visitor_count || 0}</p>
                  </div>
                </div>

                {/* Films Showing */}
                {cinemaDetails.films_showing.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Film in Programmazione</h4>
                    <div className="flex gap-2 overflow-x-auto">
                      {cinemaDetails.films_showing.map(film => (
                        <div key={film.title} className="min-w-[100px] flex-shrink-0">
                          <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=200'} alt={film.title} className="w-full h-32 object-cover rounded" />
                          <p className="text-[10px] truncate mt-1">{film.title}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reviews */}
                <div>
                  <h4 className="text-sm font-semibold mb-2">Recensioni</h4>
                  {cinemaDetails.reviews?.length > 0 ? (
                    <ScrollArea className="h-32">
                      <div className="space-y-2">
                        {cinemaDetails.reviews.map(review => (
                          <div key={review.id} className="p-2 bg-white/5 rounded">
                            <div className="flex items-center gap-2 mb-1">
                              <Avatar className="w-5 h-5"><AvatarImage src={review.user_avatar} /></Avatar>
                              <span className="text-xs font-semibold">{review.user_nickname}</span>
                              <span className="text-yellow-500 text-xs">{'★'.repeat(Math.floor(review.rating))}</span>
                            </div>
                            <p className="text-xs text-gray-300">{review.comment}</p>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  ) : (
                    <p className="text-gray-400 text-sm">Nessuna recensione ancora.</p>
                  )}
                </div>

                {/* Leave Review */}
                {cinemaDetails.cinema.owner_id !== user?.id && (
                  <div className="border-t border-white/10 pt-3">
                    <h4 className="text-sm font-semibold mb-2">Lascia una Recensione</h4>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs">Voto:</span>
                      {[1,2,3,4,5].map(n => (
                        <button key={n} onClick={() => setReviewRating(n)} className={`text-lg ${n <= reviewRating ? 'text-yellow-500' : 'text-gray-600'}`}>★</button>
                      ))}
                    </div>
                    <Textarea value={reviewComment} onChange={e => setReviewComment(e.target.value)} placeholder="Scrivi un commento..." className="h-16 text-sm bg-black/20 border-white/10 mb-2" />
                    <Button onClick={submitReview} className="w-full bg-yellow-500 text-black">Invia Recensione (+10 XP)</Button>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ==================== MAJOR ROLES DEFINITION ====================
const MAJOR_ROLES = {
  founder: { en: 'Founder', it: 'Fondatore' },
  vice: { en: 'Vice President', it: 'Vice Presidente' },
  senior_producer: { en: 'Senior Producer', it: 'Produttore Senior' },
  member: { en: 'Member', it: 'Membro' }
};

// ==================== MAJOR PAGE ====================

export default CinemaTourPage;
