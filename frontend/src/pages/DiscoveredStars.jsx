// CineWorld Studio's - DiscoveredStars
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

// useTranslations imported from contexts

const DiscoveredStars = () => {
  const { api, user, updateFunds } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [stars, setStars] = useState([]);
  const [hiredStars, setHiredStars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStar, setSelectedStar] = useState(null);
  const [hiring, setHiring] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [starsRes, hiredRes] = await Promise.all([
        api.get('/discovered-stars?limit=50'),
        api.get('/stars/hired')
      ]);
      setStars(starsRes.data.stars || []);
      setHiredStars(hiredRes.data.hired_stars || []);
    } catch (e) {
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const hireStar = async (star) => {
    if (star.is_hired_by_user) {
      toast.info(language === 'it' ? 'Hai già ingaggiato questa star!' : 'You already hired this star!');
      return;
    }
    
    if (user.funds < star.hire_cost) {
      toast.error(language === 'it' ? `Fondi insufficienti! Servono $${star.hire_cost.toLocaleString()}` : `Not enough funds! Need $${star.hire_cost.toLocaleString()}`);
      return;
    }
    
    setHiring(true);
    try {
      const res = await api.post(`/stars/${star.id}/hire`);
      toast.success(res.data.message);
      updateFunds(-star.hire_cost);
      loadData();
      setSelectedStar(null);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setHiring(false);
    }
  };

  const getSkillColor = (value) => {
    if (value >= 90) return 'text-yellow-400';
    if (value >= 75) return 'text-green-400';
    if (value >= 50) return 'text-blue-400';
    return 'text-gray-400';
  };

  const getTypeLabel = (type) => {
    const labels = {
      'actor': language === 'it' ? 'Attore' : 'Actor',
      'director': language === 'it' ? 'Regista' : 'Director',
      'screenwriter': language === 'it' ? 'Sceneggiatore' : 'Screenwriter',
      'composer': language === 'it' ? 'Compositore' : 'Composer'
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[1,2,3,4,5,6].map(i => <div key={i} className="h-48 bg-gray-700 rounded"></div>)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="discovered-stars-page">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="h-8 w-8">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl flex items-center gap-2">
          <Star className="w-6 h-6 text-yellow-400" />
          {language === 'it' ? 'STELLE SCOPERTE' : 'DISCOVERED STARS'}
        </h1>
      </div>

      {/* Hired Stars Section */}
      {hiredStars.length > 0 && (
        <Card className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border-green-500/30 mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-green-400" />
              {language === 'it' ? 'Star Ingaggiate per il Prossimo Film' : 'Stars Hired for Next Film'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {hiredStars.map(hire => (
                <div key={hire.id} className="flex items-center gap-2 bg-green-500/20 rounded-full px-3 py-1">
                  <img src={hire.star_details?.avatar_url || 'https://api.dicebear.com/9.x/personas/svg?seed=star'} alt="" className="w-6 h-6 rounded-full" />
                  <span className="text-sm font-medium">{hire.star_name}</span>
                  <Badge className="text-[10px] bg-green-500/30">{getTypeLabel(hire.star_type)}</Badge>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">
              {language === 'it' ? 'Queste star saranno automaticamente disponibili quando crei un nuovo film' : 'These stars will be automatically available when you create a new film'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* All Discovered Stars */}
      {stars.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardContent className="py-12 text-center">
            <Star className="w-16 h-16 mx-auto mb-4 text-gray-600" />
            <p className="text-gray-400 text-lg">
              {language === 'it' ? 'Nessuna stella scoperta ancora' : 'No discovered stars yet'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {stars.map(star => (
            <Card 
              key={star.id} 
              className={`bg-[#1A1A1A] border-white/10 hover:border-yellow-500/30 transition-all cursor-pointer ${star.is_hired_by_user ? 'ring-2 ring-green-500/50' : ''}`}
              onClick={() => setSelectedStar(star)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="relative">
                    <img src={star.avatar_url || 'https://api.dicebear.com/9.x/personas/svg?seed=' + star.id} alt={star.name} className="w-16 h-16 rounded-lg object-cover" />
                    <div className="absolute -top-1 -right-1 flex">
                      {[...Array(star.stars || 3)].map((_, i) => (
                        <Star key={i} className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                      ))}
                    </div>
                    {star.is_hired_by_user && (
                      <Badge className="absolute -bottom-1 -right-1 bg-green-500 text-white text-[8px]">
                        <Check className="w-2 h-2" />
                      </Badge>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">{star.name}</h3>
                    <p className="text-xs text-gray-400">{getTypeLabel(star.type)}</p>
                    <p className="text-xs text-gray-500">{star.nationality}</p>
                    {star.discoverer && (
                      <p className="text-[10px] text-purple-400 mt-1">
                        {language === 'it' ? 'Scoperta da' : 'Discovered by'}: {star.discoverer.production_house_name || star.discoverer.nickname}
                      </p>
                    )}
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <Badge className="bg-yellow-500/20 text-yellow-400">
                    Fame: {star.fame_score || 50}
                  </Badge>
                  <span className="text-sm font-bold text-green-400">
                    ${star.hire_cost?.toLocaleString()}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Star Detail Modal */}
      {selectedStar && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setSelectedStar(null)}>
          <Card className="bg-[#1A1A1A] border-yellow-500/30 max-w-lg w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <img src={selectedStar.avatar_url || 'https://api.dicebear.com/9.x/personas/svg?seed=' + selectedStar.id} alt={selectedStar.name} className="w-20 h-20 rounded-lg object-cover" />
                  <div>
                    <CardTitle className="text-xl">{selectedStar.name}</CardTitle>
                    <p className="text-sm text-gray-400">{getTypeLabel(selectedStar.type)} • {selectedStar.nationality}</p>
                    <div className="flex mt-1">
                      {[...Array(selectedStar.stars || 3)].map((_, i) => (
                        <Star key={i} className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                      ))}
                    </div>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setSelectedStar(null)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Skills */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold mb-2 text-gray-400">{language === 'it' ? 'SKILLS' : 'SKILLS'}</h4>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(selectedStar.skills || {}).map(([skill, value]) => (
                    <div key={skill} className="flex items-center justify-between bg-white/5 rounded px-2 py-1">
                      <span className="text-xs capitalize">{skill.replace(/_/g, ' ')}</span>
                      <span className={`text-sm font-bold ${getSkillColor(value)}`}>{value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                <div className="bg-white/5 rounded p-2 text-center">
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Fama' : 'Fame'}</p>
                  <p className="text-lg font-bold text-yellow-400">{selectedStar.fame_score || 50}</p>
                </div>
                <div className="bg-white/5 rounded p-2 text-center">
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Film' : 'Films'}</p>
                  <p className="text-lg font-bold">{selectedStar.films_count || 0}</p>
                </div>
                <div className="bg-white/5 rounded p-2 text-center">
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Qualità Media' : 'Avg Quality'}</p>
                  <p className="text-lg font-bold text-blue-400">{selectedStar.avg_film_quality || 50}</p>
                </div>
              </div>

              {/* Discoverer */}
              {selectedStar.discoverer && (
                <div className="bg-purple-500/10 rounded-lg p-3 mb-4">
                  <p className="text-xs text-purple-400">
                    {language === 'it' ? 'Scoperta da' : 'Discovered by'}: <span className="font-semibold">{selectedStar.discoverer.production_house_name || selectedStar.discoverer.nickname}</span>
                  </p>
                </div>
              )}

              {/* Hire Button */}
              <div className="flex items-center justify-between pt-4 border-t border-white/10">
                <div>
                  <p className="text-sm text-gray-400">{language === 'it' ? 'Costo Ingaggio' : 'Hire Cost'}</p>
                  <p className="text-2xl font-bold text-green-400">${selectedStar.hire_cost?.toLocaleString()}</p>
                </div>
                {selectedStar.is_hired_by_user ? (
                  <Badge className="bg-green-500/20 text-green-400 text-sm py-2 px-4">
                    <Check className="w-4 h-4 mr-1" />
                    {language === 'it' ? 'Già Ingaggiata' : 'Already Hired'}
                  </Badge>
                ) : (
                  <Button 
                    onClick={() => hireStar(selectedStar)}
                    disabled={hiring || user.funds < selectedStar.hire_cost}
                    className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold"
                  >
                    {hiring ? '...' : (
                      <>
                        <UserPlus className="w-4 h-4 mr-2" />
                        {language === 'it' ? 'INGAGGIA' : 'HIRE'}
                      </>
                    )}
                  </Button>
                )}
              </div>
              {user.funds < selectedStar.hire_cost && !selectedStar.is_hired_by_user && (
                <p className="text-xs text-red-400 text-right mt-2">
                  {language === 'it' ? `Ti mancano $${(selectedStar.hire_cost - user.funds).toLocaleString()}` : `You need $${(selectedStar.hire_cost - user.funds).toLocaleString()} more`}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

// ==================== FEEDBACK BOARD (Suggestions & Bug Reports) ====================

export default DiscoveredStars;
