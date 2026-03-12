// CineWorld Studio's - FilmDrafts
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

const FilmDrafts = () => {
  const { api } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadDrafts();
  }, []);

  const loadDrafts = async () => {
    try {
      const res = await api.get('/films/drafts');
      setDrafts(res.data.drafts || []);
    } catch (e) {
      toast.error('Errore nel caricamento delle bozze');
    } finally {
      setLoading(false);
    }
  };

  const deleteDraft = async (draftId) => {
    setDeletingId(draftId);
    try {
      await api.delete(`/films/drafts/${draftId}`);
      toast.success(language === 'it' ? 'Bozza eliminata' : 'Draft deleted');
      setDrafts(drafts.filter(d => d.id !== draftId));
    } catch (e) {
      toast.error('Errore');
    } finally {
      setDeletingId(null);
    }
  };

  const resumeDraft = (draftId) => {
    navigate(`/create?draft=${draftId}`);
  };

  const getStepName = (stepNum) => {
    const steps = ['', 'Titolo', 'Sponsor', 'Equip.', 'Scrittore', 'Regista', 'Compositore', 'Cast', 'Script', 'Musica', 'Poster', 'Ads', 'Review'];
    return steps[stepNum] || `Step ${stepNum}`;
  };

  const getReasonBadge = (reason) => {
    switch(reason) {
      case 'paused':
        return <Badge className="bg-orange-500/20 text-orange-400">{language === 'it' ? 'In Pausa' : 'Paused'}</Badge>;
      case 'autosave':
        return <Badge className="bg-blue-500/20 text-blue-400">{language === 'it' ? 'Auto-salvato' : 'Auto-saved'}</Badge>;
      case 'browser_close':
        return <Badge className="bg-purple-500/20 text-purple-400">{language === 'it' ? 'Recuperato' : 'Recovered'}</Badge>;
      case 'error':
        return <Badge className="bg-red-500/20 text-red-400">{language === 'it' ? 'Errore' : 'Error'}</Badge>;
      default:
        return <Badge className="bg-gray-500/20 text-gray-400">{language === 'it' ? 'Incompleto' : 'Incomplete'}</Badge>;
    }
  };

  if (loading) return <LoadingSpinner />;


  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="film-drafts-page">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="h-8 w-8">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl flex items-center gap-2">
          <Film className="w-6 h-6 text-orange-400" />
          {language === 'it' ? 'Film Incompleti' : 'Incomplete Films'}
        </h1>
      </div>

      {drafts.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardContent className="py-12 text-center">
            <Film className="w-16 h-16 mx-auto mb-4 text-gray-600" />
            <p className="text-gray-400 text-lg">
              {language === 'it' ? 'Nessun film in sospeso' : 'No incomplete films'}
            </p>
            <p className="text-gray-500 text-sm mt-2">
              {language === 'it' ? 'I film messi in pausa o con errori appariranno qui' : 'Paused or errored films will appear here'}
            </p>
            <Button onClick={() => navigate('/create')} className="mt-4 bg-yellow-500 text-black">
              <Plus className="w-4 h-4 mr-2" />
              {language === 'it' ? 'Crea Nuovo Film' : 'Create New Film'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {drafts.map(draft => (
            <Card key={draft.id} className="bg-[#1A1A1A] border-white/10 hover:border-orange-500/30 transition-colors">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-lg truncate">
                        {draft.title || (language === 'it' ? 'Senza Titolo' : 'Untitled')}
                      </h3>
                      {getReasonBadge(draft.paused_reason)}
                    </div>
                    
                    <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-400">
                      {draft.genre_display && (
                        <span className="flex items-center gap-1">
                          <Film className="w-3 h-3" />
                          {draft.genre_display}
                        </span>
                      )}
                      {draft.director_name && (
                        <span className="flex items-center gap-1">
                          <Clapperboard className="w-3 h-3" />
                          {draft.director_name}
                        </span>
                      )}
                      {draft.actors_count > 0 && (
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {draft.actors_count} {language === 'it' ? 'attori' : 'actors'}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 mt-3">
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        {language === 'it' ? 'Fermo a:' : 'Stopped at:'}
                      </div>
                      <Badge variant="outline" className="text-xs">
                        Step {draft.current_step}/12 - {getStepName(draft.current_step)}
                      </Badge>
                    </div>
                    
                    {draft.updated_at && (
                      <p className="text-xs text-gray-500 mt-2">
                        {language === 'it' ? 'Ultimo salvataggio:' : 'Last saved:'} {new Date(draft.updated_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  
                  <div className="flex flex-col gap-2">
                    <Button 
                      onClick={() => resumeDraft(draft.id)} 
                      className="bg-green-600 hover:bg-green-700 text-white"
                      size="sm"
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      {language === 'it' ? 'Riprendi' : 'Resume'}
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => deleteDraft(draft.id)}
                      disabled={deletingId === draft.id}
                      className="text-red-400 border-red-400/50 hover:bg-red-500/10"
                    >
                      {deletingId === draft.id ? '...' : (
                        <>
                          <Trash2 className="w-3 h-3 mr-1" />
                          {language === 'it' ? 'Elimina' : 'Delete'}
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// My Films with Withdraw Option and Advertising

export default FilmDrafts;
