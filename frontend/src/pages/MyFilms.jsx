// CineWorld Studio's - MyFilms
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

const MyFilms = () => {
  const { api, user } = useContext(AuthContext);
  const { t } = useTranslations();
  const [films, setFilms] = useState([]);
  const [showAdDialog, setShowAdDialog] = useState(null);
  const [adPlatforms, setAdPlatforms] = useState([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [adDays, setAdDays] = useState(7);
  const [adLoading, setAdLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { 
    api.get('/films/my').then(r=>setFilms(r.data)); 
    api.get('/advertising/platforms').then(r=>setAdPlatforms(r.data)).catch(()=>{});
  }, [api]);

  const withdrawFilm = async (filmId) => {
    try {
      await api.delete(`/films/${filmId}`);
      toast.success('Film withdrawn from theaters');
      setFilms(films.map(f => f.id === filmId ? { ...f, status: 'withdrawn' } : f));
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed');
    }
  };

  const launchAdCampaign = async (filmId) => {
    if (selectedPlatforms.length === 0) { toast.error('Select at least one platform'); return; }
    setAdLoading(true);
    try {
      const res = await api.post(`/films/${filmId}/advertise`, { platforms: selectedPlatforms, days: adDays, budget: 0 });
      toast.success(`Campaign launched! +$${res.data.revenue_boost?.toLocaleString()} revenue!`);
      setShowAdDialog(null); setSelectedPlatforms([]);
      api.get('/films/my').then(r => setFilms(r.data));
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); } 
    finally { setAdLoading(false); }
  };

  const calculateAdCost = () => selectedPlatforms.reduce((s, pId) => { const p = adPlatforms.find(x => x.id === pId); return s + (p ? p.cost_per_day * adDays : 0); }, 0);

  return (
    <div className="pt-16 pb-20 px-2 sm:px-3 max-w-7xl mx-auto" data-testid="my-films-page">
      <div className="flex items-center justify-between mb-4 sticky top-16 z-10 bg-[#0F0F10]/95 backdrop-blur-sm py-2 -mx-2 sm:-mx-3 px-2 sm:px-3" data-testid="my-films-sticky-header-main">
        <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl">{t('my_films')}</h1>
        <Button size="sm" onClick={() => navigate('/create')} className="bg-yellow-500 text-black h-8 px-2 sm:px-3 text-xs sm:text-sm"><Plus className="w-3 h-3 mr-1" /> Create</Button>
      </div>
      {films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-6 text-center"><Film className="w-10 h-10 mx-auto mb-3 text-gray-600" /><h3 className="text-base mb-2">No films yet</h3><Button onClick={() => navigate('/create')} className="bg-yellow-500 text-black text-sm">Create First Film</Button></Card>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-1.5 sm:gap-2">
          {films.map(film => (
            <Card key={film.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden hover:border-white/15 transition-colors">
              <div className="aspect-[2/3] relative cursor-pointer" onClick={() => navigate(`/films/${film.id}`)}>
                <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} alt={film.title} className="w-full h-full object-cover" loading="lazy" />
                <Badge className={`absolute top-1 right-1 text-[8px] px-1 ${film.status === 'in_theaters' ? 'bg-green-500' : 'bg-orange-500'}`}>{film.status}</Badge>
                {(film.virtual_likes > 0) && (
                  <div className="absolute top-1 left-1 bg-black/70 rounded px-1 py-0.5 flex items-center gap-0.5">
                    <Heart className="w-2 h-2 text-pink-400 fill-pink-400" />
                    <span className="text-[8px] text-pink-300">{film.virtual_likes}</span>
                  </div>
                )}
              </div>
              <CardContent className="p-1 sm:p-1.5">
                <h3 className="font-semibold text-[10px] sm:text-xs truncate">{film.title}</h3>
                <div className="flex justify-between mt-0.5 text-[9px] sm:text-[10px]">
                  <span className="text-gray-400"><Heart className="w-2 h-2 inline" /> {(film.likes_count || 0) + (film.virtual_likes || 0)}</span>
                  <span className="text-green-400">${((film.total_revenue||0)/1000).toFixed(0)}K</span>
                </div>
                {film.status === 'in_theaters' && (
                  <div className="flex gap-0.5 mt-1">
                    <Button variant="outline" size="sm" className="flex-1 h-5 text-[9px] border-yellow-500/30 text-yellow-400 px-0.5" onClick={() => setShowAdDialog(film)}>
                      <Sparkles className="w-2 h-2 mr-0.5" /> Ads
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="outline" size="sm" className="flex-1 h-5 text-[9px] border-orange-500/30 text-orange-400 px-0.5"><Trash2 className="w-2 h-2" /></Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent className="bg-[#1A1A1A] border-white/10 max-w-[90vw] sm:max-w-md">
                        <AlertDialogHeader><AlertDialogTitle className="text-base">Withdraw?</AlertDialogTitle></AlertDialogHeader>
                        <AlertDialogFooter><AlertDialogCancel className="h-8 text-sm">No</AlertDialogCancel><AlertDialogAction onClick={() => withdrawFilm(film.id)} className="bg-orange-500 h-8 text-sm">Yes</AlertDialogAction></AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <Dialog open={!!showAdDialog} onOpenChange={() => { setShowAdDialog(null); setSelectedPlatforms([]); }}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-[95vw] sm:max-w-lg">
          <DialogHeader><DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><Sparkles className="w-4 h-4 text-yellow-500" /> Advertise "{showAdDialog?.title}"</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">{adPlatforms.map(p => (
              <Card key={p.id} className={`cursor-pointer border-2 ${selectedPlatforms.includes(p.id) ? 'border-yellow-500 bg-yellow-500/10' : 'border-white/10'}`} onClick={() => setSelectedPlatforms(prev => prev.includes(p.id) ? prev.filter(x => x !== p.id) : [...prev, p.id])}>
                <CardContent className="p-2"><span className="font-semibold text-xs">{p.name}</span><p className="text-[10px] text-gray-400">${p.cost_per_day.toLocaleString()}/day • +{((p.reach_multiplier-1)*100).toFixed(0)}%</p></CardContent>
              </Card>
            ))}</div>
            <div><Label className="text-xs">Duration: {adDays} days</Label><Slider value={[adDays]} onValueChange={([v]) => setAdDays(v)} min={1} max={30} className="mt-1" /></div>
            <div className="p-2 bg-black/30 rounded flex justify-between items-center"><span className="text-xs text-gray-400">Total:</span><span className="text-lg font-bold text-yellow-500">${calculateAdCost().toLocaleString()}</span></div>
            <Button onClick={() => launchAdCampaign(showAdDialog?.id)} disabled={adLoading || selectedPlatforms.length === 0 || calculateAdCost() > (user?.funds||0)} className="w-full bg-yellow-500 text-black h-9">{adLoading ? '...' : 'Launch'}</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Film Detail

export default MyFilms;
