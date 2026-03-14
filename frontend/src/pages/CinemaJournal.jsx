// CineWorld Studio's - CinemaJournal
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding, MessageCircle
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

const CinemaJournal = () => {
  const { api, user } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [films, setFilms] = useState([]);
  const [news, setNews] = useState([]);
  const [discoveredStars, setDiscoveredStars] = useState([]);
  const [recentTrailers, setRecentTrailers] = useState([]);
  const [recentPosters, setRecentPosters] = useState([]);
  const [virtualReviews, setVirtualReviews] = useState([]);
  const [otherNews, setOtherNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [comment, setComment] = useState('');
  const [showAllNews, setShowAllNews] = useState(false);
  const [showVirtualReviews, setShowVirtualReviews] = useState(false);
  const [showOtherNews, setShowOtherNews] = useState(false);
  const [showHallOfFame, setShowHallOfFame] = useState(false);
  const [hiringStarId, setHiringStarId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => { 
    Promise.all([
      api.get('/films/cinema-journal'),
      api.get('/cinema-news'),
      api.get('/discovered-stars'),
      api.get('/journal/virtual-reviews'),
      api.get('/journal/other-news')
    ]).then(([filmsRes, newsRes, starsRes, reviewsRes, otherRes]) => {
      setFilms(filmsRes.data.films);
      setRecentTrailers(filmsRes.data.recent_trailers || []);
      setRecentPosters(filmsRes.data.recent_posters || []);
      setNews(newsRes.data.news || []);
      setDiscoveredStars(starsRes.data.stars || []);
      setVirtualReviews(reviewsRes.data?.reviews || []);
      setOtherNews(otherRes.data?.news || []);
    }).catch(e => console.error(e)).finally(() => setLoading(false)); 
  }, [api]);

  const handleRate = async (filmId, rating) => {
    const res = await api.post(`/films/${filmId}/rate`, { rating });
    setFilms(films.map(f => f.id === filmId ? { 
      ...f, 
      user_rating: rating, 
      average_rating: res.data.average_rating,
      ratings_count: res.data.ratings_count 
    } : f));
    toast.success(`Voted ${rating} stars!`);
  };

  const handleComment = async (filmId) => {
    if (!comment.trim()) return;
    await api.post(`/films/${filmId}/comment`, { content: comment });
    setComment('');
    const res = await api.get('/films/cinema-journal');
    setFilms(res.data.films);
    toast.success('Comment added!');
  };

  const handleLike = async (filmId) => {
    const res = await api.post(`/films/${filmId}/like`);
    setFilms(films.map(f => f.id === filmId ? { ...f, user_liked: res.data.liked, likes_count: res.data.likes_count } : f));
  };

  const hireStar = async (starId) => {
    setHiringStarId(starId);
    try {
      await api.post(`/stars/${starId}/hire`);
      toast.success(language === 'it' ? 'Star ingaggiata!' : 'Star hired!');
      const starsRes = await api.get('/discovered-stars');
      setDiscoveredStars(starsRes.data.stars || []);
    } catch (e) {
      toast.error(e.response?.data?.detail || (language === 'it' ? 'Errore nell\'ingaggio' : 'Hire failed'));
    } finally {
      setHiringStarId(null);
    }
  };

  const StarRating = ({ value, onChange, readonly = false, size = 'md' }) => {
    const stars = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5];
    const sizeClass = size === 'sm' ? 'w-3 h-3' : 'w-5 h-5';

    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map(star => (
          <button 
            key={star} 
            disabled={readonly}
            className={`${readonly ? '' : 'cursor-pointer hover:scale-110'} transition-transform`}
            onClick={() => !readonly && onChange && onChange(star)}
          >
            <Star 
              className={`${sizeClass} ${value >= star ? 'fill-yellow-500 text-yellow-500' : value >= star - 0.5 ? 'fill-yellow-500/50 text-yellow-500' : 'text-gray-600'}`} 
            />
          </button>
        ))}
        {!readonly && (
          <button onClick={() => onChange && onChange(value - 0.5 >= 0 ? value - 0.5 : value + 0.5)} className="ml-1 text-xs text-gray-400 hover:text-yellow-500">
            ½
          </button>
        )}
      </div>
    );
  };

  const getRoleBadge = (role) => {
    const badges = {
      protagonist: { color: 'bg-yellow-500/20 text-yellow-500', label: 'Lead' },
      co_protagonist: { color: 'bg-blue-500/20 text-blue-400', label: 'Co-Lead' },
      antagonist: { color: 'bg-red-500/20 text-red-400', label: 'Villain' },
      supporting: { color: 'bg-gray-500/20 text-gray-400', label: 'Support' },
      cameo: { color: 'bg-purple-500/20 text-purple-400', label: 'Cameo' }
    };
    const badge = badges[role] || badges.supporting;
    return <Badge className={`${badge.color} text-[10px] h-4`}>{badge.label}</Badge>;
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="pt-16 pb-20 px-3 max-w-5xl mx-auto" data-testid="cinema-journal-page">
      {/* All News Dialog */}
      <Dialog open={showAllNews} onOpenChange={setShowAllNews}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden bg-[#1A1A1A] border-yellow-500/30">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2 text-yellow-400">
              <Newspaper className="w-6 h-6" /> {language === 'it' ? 'TUTTE LE NEWS' : 'ALL NEWS'}
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[60vh] pr-4">
            <div className="space-y-3">
              {news.length === 0 ? (
                <div className="text-center py-8 text-gray-400">{language === 'it' ? 'Nessuna news al momento' : 'No news at the moment'}</div>
              ) : (
                news.map(item => (
                  <Card 
                    key={item.id} 
                    className="bg-white/5 border-white/10 cursor-pointer hover:bg-white/10"
                    onClick={() => { if (item.film_id) { setShowAllNews(false); navigate(`/film/${item.film_id}`); }}}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">{item.type || 'NEWS'}</Badge>
                        {item.importance === 'high' && <Badge className="bg-red-500/20 text-red-400 text-[10px]">HOT</Badge>}
                      </div>
                      <h3 className="font-semibold text-sm">{item.title_localized || item.title}</h3>
                      <p className="text-xs text-gray-400 mt-1">{item.content_localized || item.content}</p>
                      <p className="text-[10px] text-gray-500 mt-2">{new Date(item.created_at).toLocaleString()}</p>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Virtual Reviews Dialog */}
      <Dialog open={showVirtualReviews} onOpenChange={setShowVirtualReviews}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden bg-[#1A1A1A] border-pink-500/30">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2 text-pink-400">
              <MessageCircle className="w-6 h-6" /> {language === 'it' ? 'VOCI DAL PUBBLICO' : 'AUDIENCE VOICES'}
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[60vh] pr-4">
            <div className="space-y-3">
              {virtualReviews.length === 0 ? (
                <div className="text-center py-8 text-gray-400">{language === 'it' ? 'Nessuna recensione del pubblico' : 'No audience reviews'}</div>
              ) : (
                virtualReviews.map((review, idx) => (
                  <Card 
                    key={idx} 
                    className="bg-pink-500/5 border-pink-500/20 cursor-pointer hover:bg-pink-500/10"
                    onClick={() => { if (review.film_id) { setShowVirtualReviews(false); navigate(`/film/${review.film_id}`); }}}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start gap-3">
                        <Avatar className="w-10 h-10">
                          <AvatarFallback className="bg-pink-500/20 text-pink-400">{review.reviewer_name?.[0] || '?'}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-sm">{review.reviewer_name}</span>
                            <div className="flex items-center gap-1">
                              {[1,2,3,4,5].map(s => (
                                <Star key={s} className={`w-3 h-3 ${s <= review.rating ? 'fill-yellow-500 text-yellow-500' : 'text-gray-600'}`} />
                              ))}
                            </div>
                          </div>
                          <p className="text-xs text-gray-400">{review.reviewer_info}</p>
                          <p className="text-sm mt-2 italic">"{review.comment}"</p>
                          <p className="text-[10px] text-pink-400 mt-1">🎬 {review.film_title}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Breaking News Dialog (was "Other News") */}
      <Dialog open={showOtherNews} onOpenChange={setShowOtherNews}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden bg-[#1A1A1A] border-red-500/30">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2 text-red-400">
              <Flame className="w-6 h-6" /> BREAKING NEWS
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[60vh] pr-4">
            <div className="space-y-3">
              {otherNews.length === 0 ? (
                <div className="text-center py-8 text-gray-400">{language === 'it' ? 'Nessuna breaking news' : 'No breaking news'}</div>
              ) : (
                otherNews.map((item, idx) => (
                  <Card 
                    key={idx} 
                    className={`cursor-pointer hover:bg-white/10 ${
                      item.category === 'trending' ? 'bg-red-500/10 border-red-500/20' :
                      item.category === 'star' ? 'bg-yellow-500/10 border-yellow-500/20' :
                      item.category === 'record' ? 'bg-green-500/10 border-green-500/20' :
                      'bg-purple-500/10 border-purple-500/20'
                    }`}
                    onClick={() => { if (item.link) { setShowOtherNews(false); navigate(item.link); }}}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className={`text-[10px] ${
                          item.category === 'trending' ? 'bg-red-500/20 text-red-400' :
                          item.category === 'star' ? 'bg-yellow-500/20 text-yellow-400' :
                          item.category === 'record' ? 'bg-green-500/20 text-green-400' :
                          'bg-purple-500/20 text-purple-400'
                        }`}>
                          {item.category === 'trending' ? 'TRENDING' :
                           item.category === 'star' ? 'STAR' :
                           item.category === 'record' ? 'RECORD' :
                           'NEWS'}
                        </Badge>
                      </div>
                      <h3 className="font-semibold text-sm">{item.title}</h3>
                      <p className="text-xs text-gray-400 mt-1">{item.content}</p>
                      {item.timestamp && <p className="text-[10px] text-gray-500 mt-2">{item.timestamp}</p>}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Hall of Fame Dialog - Discovered Stars */}
      <Dialog open={showHallOfFame} onOpenChange={setShowHallOfFame}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden bg-[#1A1A1A] border-amber-500/30">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2 text-amber-400">
              <Award className="w-6 h-6" /> HALL OF FAME
            </DialogTitle>
            <p className="text-gray-400 text-sm">{language === 'it' ? 'Le nuove stelle del cinema - clicca per pre-ingaggiare!' : 'New cinema stars - click to pre-hire!'}</p>
          </DialogHeader>
          <ScrollArea className="h-[60vh] pr-4">
            <div className="space-y-3">
              {discoveredStars.length === 0 ? (
                <div className="text-center py-8 text-gray-400">{language === 'it' ? 'Nessuna star scoperta' : 'No discovered stars'}</div>
              ) : (
                discoveredStars.map(star => (
                  <Card 
                    key={star.id} 
                    className="bg-amber-500/5 border-amber-500/20 hover:bg-amber-500/10 transition-all"
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center gap-3">
                        <Avatar className="w-14 h-14 ring-2 ring-amber-500">
                          <AvatarImage src={star.avatar_url} />
                          <AvatarFallback className="bg-amber-500/20 text-amber-400 font-bold">{star.name?.[0]}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <p className="font-semibold text-amber-300">{star.name}</p>
                          <p className="text-[10px] text-gray-500">{star.type === 'actor' ? (language === 'it' ? 'Attore' : 'Actor') : star.type === 'director' ? (language === 'it' ? 'Regista' : 'Director') : star.type}</p>
                          <div className="flex items-center gap-2 mt-1">
                            {star.stars && <div className="flex">{[...Array(Math.min(5, star.stars || 0))].map((_, i) => <Star key={i} className="w-3 h-3 fill-yellow-500 text-yellow-500" />)}</div>}
                            <span className="text-[10px] text-gray-400">{language === 'it' ? 'Scoperto da' : 'Discovered by'} {star.discoverer?.nickname}</span>
                          </div>
                          {star.skills && (
                            <div className="flex gap-1 mt-1 flex-wrap">
                              {Object.entries(star.skills || {}).slice(0, 3).map(([k, v]) => {
                                const change = star?.skill_changes?.[k] || 0;
                                return (
                                <Badge key={k} className="bg-white/10 text-[9px] h-4">
                                  {k}: {v}
                                  {change !== 0 && <span className={change > 0 ? 'text-green-400 ml-0.5' : 'text-red-400 ml-0.5'}>{change > 0 ? '▲' : '▼'}</span>}
                                </Badge>
                                );
                              })}
                            </div>
                          )}
                        </div>
                        <Button 
                          size="sm" 
                          className="bg-amber-500 hover:bg-amber-600 text-black font-bold h-8 px-3"
                          onClick={() => hireStar(star.id)}
                          disabled={hiringStarId === star.id}
                          data-testid={`hire-star-${star.id}`}
                        >
                          {hiringStarId === star.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : (language === 'it' ? 'Ingaggia' : 'Hire')}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      <div className="text-center mb-6">
        <h1 className="font-['Playfair_Display'] text-4xl md:text-5xl font-bold italic tracking-tight">
          {t('cinema_journal')}
        </h1>
        <div className="flex items-center justify-center gap-2 mt-2">
          <div className="h-px w-16 bg-yellow-500/50" />
          <Newspaper className="w-4 h-4 text-yellow-500" />
          <div className="h-px w-16 bg-yellow-500/50" />
        </div>
        <p className="text-gray-400 text-sm mt-2 italic">{language === 'it' ? 'Le migliori produzioni, classificate per eccellenza' : 'The finest productions, ranked by excellence'}</p>
      </div>

      {/* Sticky Category Bar - stays fixed when scrolling */}
      <div className="sticky top-14 z-40 bg-[#0D0D0D]/95 backdrop-blur-md border-b border-white/10 -mx-3 px-2 py-1.5 mb-6">
        <div className="flex justify-start sm:justify-center gap-1.5 overflow-x-auto no-scrollbar max-w-5xl mx-auto">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowAllNews(true)}
            className="border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10 text-[10px] sm:text-xs h-7 px-2 sm:px-3 flex-shrink-0"
            data-testid="journal-news-btn"
          >
            <Newspaper className="w-3 h-3 mr-1" /> News
            {news.length > 0 && <Badge className="ml-1 bg-yellow-500/30 text-yellow-300 text-[8px] h-3.5 px-1">{news.length}</Badge>}
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowVirtualReviews(true)}
            className="border-pink-500/30 text-pink-400 hover:bg-pink-500/10 text-[10px] sm:text-xs h-7 px-2 sm:px-3 flex-shrink-0"
            data-testid="journal-audience-btn"
          >
            <MessageCircle className="w-3 h-3 mr-1" /> {language === 'it' ? 'Pubblico' : 'Audience'}
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowOtherNews(true)}
            className="border-red-500/30 text-red-400 hover:bg-red-500/10 text-[10px] sm:text-xs h-7 px-2 sm:px-3 flex-shrink-0"
            data-testid="journal-breaking-btn"
          >
            <Flame className="w-3 h-3 mr-1" /> Breaking
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowHallOfFame(true)}
            className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 text-[10px] sm:text-xs h-7 px-2 sm:px-3 flex-shrink-0"
            data-testid="journal-halloffame-btn"
          >
            <Award className="w-3 h-3 mr-1" /> Hall of Fame
            {discoveredStars.length > 0 && <Badge className="ml-1 bg-amber-500/30 text-amber-300 text-[8px] h-3.5 px-1">{discoveredStars.length}</Badge>}
          </Button>
        </div>
      </div>

      {/* Recent Posters Section - 4 per row */}
      {recentPosters.length > 0 && (
        <Card className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-yellow-500/30 mb-6 overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Film className="w-5 h-5 text-yellow-400" />
              <h2 className="font-['Bebas_Neue'] text-xl tracking-wide">{language === 'it' ? 'NUOVE LOCANDINE' : 'NEW POSTERS'}</h2>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {recentPosters.slice(0, 20).map(film => (
                <div 
                  key={film.id} 
                  onClick={() => navigate(`/film/${film.id}`)}
                  className="relative group cursor-pointer rounded-lg overflow-hidden bg-black/30 hover:ring-2 hover:ring-yellow-500 transition-all"
                >
                  <div className="aspect-[2/3] relative">
                    <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    {/* Virtual Likes Badge */}
                    {(film.virtual_likes > 0 || film.likes_count > 0) && (
                      <div className="absolute top-1 left-1 bg-black/70 rounded px-1.5 py-0.5 flex items-center gap-1">
                        <Heart className="w-2.5 h-2.5 text-red-400 fill-red-400" />
                        <span className="text-[9px] text-white">{((film.virtual_likes || 0) + (film.likes_count || 0)).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                  <div className="absolute bottom-0 left-0 right-0 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <p className="text-[10px] font-semibold truncate text-white">{film.title}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Trailers Section - 4 per row */}
      {recentTrailers.length > 0 && (
        <Card className="bg-gradient-to-r from-pink-500/10 to-purple-500/10 border-purple-500/30 mb-6 overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Clapperboard className="w-5 h-5 text-purple-400" />
              <h2 className="font-['Bebas_Neue'] text-xl tracking-wide">{language === 'it' ? 'NUOVI TRAILER' : 'NEW TRAILERS'}</h2>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {recentTrailers.slice(0, 20).map(film => (
                <div 
                  key={film.id} 
                  onClick={() => navigate(`/film/${film.id}`)}
                  className="relative group cursor-pointer rounded-lg overflow-hidden bg-black/30 hover:ring-2 hover:ring-purple-500 transition-all"
                >
                  <div className="aspect-video relative">
                    {film.poster_url ? (
                      <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                        <Film className="w-6 h-6 text-purple-400" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="bg-purple-500 rounded-full p-2">
                        <Clapperboard className="w-4 h-4 text-white" />
                      </div>
                    </div>
                    <Badge className="absolute top-1 right-1 bg-purple-500/80 text-white text-[8px] px-1">
                      TRAILER
                    </Badge>
                    {/* Virtual Likes Badge */}
                    {(film.virtual_likes > 0 || film.likes_count > 0) && (
                      <div className="absolute bottom-1 left-1 bg-black/70 rounded px-1.5 py-0.5 flex items-center gap-1">
                        <Heart className="w-2.5 h-2.5 text-red-400 fill-red-400" />
                        <span className="text-[9px] text-white">{((film.virtual_likes || 0) + (film.likes_count || 0)).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                  <div className="p-1.5">
                    <h3 className="font-semibold text-[10px] truncate">{film.title}</h3>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}


      {loading ? (
        <div className="text-center py-8 text-gray-400">Loading the latest news...</div>
      ) : films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
          <Newspaper className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <h3 className="text-lg mb-2">No films in theaters yet</h3>
          <p className="text-gray-400 text-sm">The cinema world awaits your masterpiece!</p>
        </Card>
      ) : (
        <div className="space-y-6">
          {films.map((film, idx) => (
            <Card key={film.id} className="bg-[#1A1A1A] border-white/10 overflow-hidden">
              <div className="md:flex">
                {/* Poster */}
                <div className="md:w-48 flex-shrink-0 relative">
                  <img 
                    src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} 
                    alt={film.title} 
                    className="w-full h-64 md:h-full object-cover cursor-pointer"
                    onClick={() => navigate(`/films/${film.id}`)}
                  />
                  {idx < 3 && (
                    <div className="absolute top-2 left-2">
                      <Badge className={`${idx === 0 ? 'bg-yellow-500 text-black' : idx === 1 ? 'bg-gray-300 text-black' : 'bg-amber-700 text-white'} font-bold`}>
                        #{idx + 1}
                      </Badge>
                    </div>
                  )}
                </div>
                
                {/* Content */}
                <CardContent className="flex-1 p-4">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h2 className="font-['Playfair_Display'] text-2xl font-bold cursor-pointer hover:text-yellow-500" onClick={() => navigate(`/films/${film.id}`)}>
                        {film.title}
                      </h2>
                      <p className="text-sm text-gray-400">
                        by <span className="text-yellow-500">{film.owner?.production_house_name}</span>
                        {film.director_details && <> • Directed by <span className="text-gray-300">{film.director_details.name}</span></>}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge className="bg-yellow-500/20 text-yellow-500">{film.genre}</Badge>
                      {film.subgenres?.length > 0 && (
                        <div className="flex gap-1">
                          {film.subgenres.slice(0, 2).map(sg => (
                            <Badge key={sg} variant="outline" className="text-[10px] h-4 border-gray-600">{sg}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Description/Screenplay excerpt */}
                  <p className="text-sm text-gray-300 mb-3 line-clamp-2 italic">
                    "{film.screenplay?.substring(0, 150) || 'A captivating story awaits...'}..."
                  </p>
                  
                  {/* Main Cast */}
                  {film.main_cast?.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Starring</p>
                      <div className="flex flex-wrap gap-2">
                        {film.main_cast.map(actor => (
                          <div key={actor.id} className="flex items-center gap-1.5 bg-white/5 rounded-full pl-1 pr-2 py-0.5">
                            <Avatar className="w-5 h-5">
                              <AvatarImage src={actor.avatar_url} />
                              <AvatarFallback className="text-[8px] bg-yellow-500/20">{actor.name?.[0]}</AvatarFallback>
                            </Avatar>
                            <span className="text-xs">{actor.name}</span>
                            <span className={`text-[10px] ${actor.gender === 'female' ? 'text-pink-400' : 'text-blue-400'}`}>
                              {actor.gender === 'female' ? '♀' : '♂'}
                            </span>
                            {getRoleBadge(actor.role)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Stats & Rating */}
                  <div className="flex items-center justify-between border-t border-white/10 pt-3 mt-3">
                    <div className="flex items-center gap-4">
                      <Button variant="ghost" size="sm" className={`h-7 px-2 ${film.user_liked ? 'text-red-400' : 'text-gray-400'}`} onClick={() => handleLike(film.id)}>
                        <Heart className={`w-3.5 h-3.5 mr-1 ${film.user_liked ? 'fill-red-400' : ''}`} /> {film.likes_count || 0}
                      </Button>
                      <span className="text-xs text-gray-400">
                        <DollarSign className="w-3 h-3 inline" />{((film.total_revenue || 0) / 1000000).toFixed(1)}M
                      </span>
                      <span className="text-xs text-gray-400">
                        <Star className="w-3 h-3 inline text-yellow-500" /> {film.quality_score?.toFixed(0)}%
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {film.average_rating !== null && (
                        <div className="flex items-center gap-1 text-xs text-gray-400">
                          <StarRating value={film.average_rating} readonly size="sm" />
                          <span>({film.ratings_count})</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* User Rating */}
                  <div className="border-t border-white/10 pt-3 mt-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">Your rating:</span>
                        <StarRating 
                          value={film.user_rating || 0} 
                          onChange={(r) => handleRate(film.id, r)}
                        />
                      </div>
                      <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => setSelectedFilm(selectedFilm === film.id ? null : film.id)}>
                        <MessageCircle className="w-3 h-3 mr-1" /> Comment
                      </Button>
                    </div>
                    
                    {/* Comment input */}
                    {selectedFilm === film.id && (
                      <div className="mt-2 flex gap-2">
                        <Input 
                          value={comment} 
                          onChange={e => setComment(e.target.value)} 
                          placeholder="Write your review..." 
                          className="h-8 text-sm bg-black/20 border-white/10"
                        />
                        <Button size="sm" className="h-8 bg-yellow-500 text-black" onClick={() => handleComment(film.id)}>
                          <Send className="w-3 h-3" />
                        </Button>
                      </div>
                    )}
                    
                    {/* Recent comments */}
                    {film.recent_comments?.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {film.recent_comments.map(c => (
                          <div key={c.id} className="flex items-start gap-2 text-xs bg-white/5 rounded p-1.5">
                            <Avatar className="w-4 h-4">
                              <AvatarImage src={c.user?.avatar_url} />
                              <AvatarFallback className="text-[8px]">{c.user?.nickname?.[0]}</AvatarFallback>
                            </Avatar>
                            <div>
                              <span className="font-semibold text-yellow-500">{c.user?.nickname}</span>
                              <span className="text-gray-400 ml-1">{c.content}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Social Feed - Shows OTHER players' films
// ==================== CINEBOARD - Film Rankings ====================

export default CinemaJournal;
