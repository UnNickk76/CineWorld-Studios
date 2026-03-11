// CineWorld Studio's - ProfilePage
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

const ProfilePage = () => {
  const { api, user, refreshUser, logout } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslations();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [showAiGenerator, setShowAiGenerator] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [generatingAi, setGeneratingAi] = useState(false);
  const [customAvatarUrl, setCustomAvatarUrl] = useState('');
  const [levelInfo, setLevelInfo] = useState(null);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [resetToken, setResetToken] = useState(null);
  const [resetting, setResetting] = useState(false);

  useEffect(() => { 
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {}); 
  }, [api]);

  const saveProfile = async () => {
    setSaving(true);
    try { 
      if (customAvatarUrl) {
        await api.put('/auth/avatar', { avatar_url: customAvatarUrl, avatar_source: 'custom' });
      }
      await api.put('/auth/profile', { language }); 
      await refreshUser(); 
      toast.success('Salvato!'); 
    }
    catch (e) { toast.error('Errore'); }
    finally { setSaving(false); }
  };

  const generateAiAvatar = async () => {
    if (!aiPrompt.trim()) { toast.error('Inserisci una descrizione'); return; }
    setGeneratingAi(true);
    try {
      const res = await api.post('/avatar/generate', { description: aiPrompt, style: 'portrait' });
      setCustomAvatarUrl(res.data.avatar_url);
      setShowAiGenerator(false);
      toast.success('Avatar generato!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Generazione fallita');
    } finally {
      setGeneratingAi(false);
    }
  };

  const requestReset = async () => {
    setResetting(true);
    try {
      const res = await api.post('/auth/reset/request');
      setResetToken(res.data.confirm_token);
      toast.warning(res.data.warning);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setResetting(false);
    }
  };

  const confirmReset = async () => {
    if (!resetToken) return;
    setResetting(true);
    try {
      const res = await api.post('/auth/reset/confirm', { confirm_token: resetToken });
      toast.success(res.data.message);
      setShowResetDialog(false);
      setResetToken(null);
      await refreshUser();
      navigate('/dashboard');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="pt-16 pb-20 px-2 sm:px-3 max-w-2xl mx-auto" data-testid="profile-page">
      <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl mb-4">{t('profile')}</h1>
      
      {/* Level & Fame Card */}
      {levelInfo && (
        <Card className="bg-gradient-to-r from-purple-500/20 to-yellow-500/20 border-purple-500/30 mb-4">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Star className="w-6 h-6 text-purple-400" />
                <span className="font-['Bebas_Neue'] text-2xl">Level {levelInfo.level}</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-yellow-400" />
                <span className="text-yellow-400 font-semibold">Fame: {levelInfo.fame?.toFixed(0) || 50}</span>
              </div>
            </div>
            <Progress value={levelInfo.progress_percent} className="h-2 mb-1" />
            <p className="text-xs text-gray-400">{levelInfo.current_xp} / {levelInfo.xp_for_next_level} XP per il prossimo livello</p>
          </CardContent>
        </Card>
      )}
      
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-3 sm:p-4">
          <div className="flex items-center gap-3 mb-4">
            <Avatar className="w-14 sm:w-16 h-14 sm:h-16 border-2 border-yellow-500/30">
              <AvatarImage src={customAvatarUrl || user?.avatar_url} />
              <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xl">{user?.nickname?.[0]}</AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold">{user?.nickname}</h2>
                {user?.nickname === 'NeoMorpheus' && (
                  <Badge className="bg-purple-500 text-white text-[10px] px-1.5 py-0">Creator</Badge>
                )}
              </div>
              <p className="text-xs sm:text-sm text-gray-400">{user?.production_house_name}</p>
              <p className="text-[10px] sm:text-xs text-gray-500">Owner: {user?.owner_name}</p>
            </div>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="text-center p-2 rounded bg-white/5"><p className="text-base sm:text-lg font-bold">{(user?.likeability_score || 50).toFixed(0)}</p><p className="text-[10px] sm:text-xs text-gray-400">Like</p></div>
            <div className="text-center p-2 rounded bg-white/5"><p className="text-base sm:text-lg font-bold">{(user?.interaction_score || 50).toFixed(0)}</p><p className="text-[10px] sm:text-xs text-gray-400">Social</p></div>
            <div className="text-center p-2 rounded bg-white/5"><p className="text-base sm:text-lg font-bold">{(user?.character_score || 50).toFixed(0)}</p><p className="text-[10px] sm:text-xs text-gray-400">Char</p></div>
          </div>
          
          {/* Avatar Section - Only AI or Custom URL */}
          <div className="space-y-3 mb-4">
            <Label className="text-xs font-semibold">Cambia Avatar</Label>
            
            {customAvatarUrl && (
              <div className="p-2 bg-yellow-500/10 rounded border border-yellow-500/30 flex items-center gap-2">
                <Avatar className="w-10 h-10"><AvatarImage src={customAvatarUrl} /></Avatar>
                <span className="text-xs text-yellow-400 flex-1">Nuovo Avatar</span>
                <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => setCustomAvatarUrl('')}>
                  <X className="w-3 h-3" />
                </Button>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-2">
              <Button variant="outline" className="h-20 flex-col border-purple-500/30 hover:bg-purple-500/10" onClick={() => setShowAiGenerator(true)}>
                <Sparkles className="w-6 h-6 text-purple-400 mb-1" />
                <span className="text-xs">Genera con AI</span>
              </Button>
              <div className="border border-white/10 rounded-lg p-2">
                <Label className="text-[10px] text-gray-400 mb-1 block">URL Immagine</Label>
                <Input 
                  value={customAvatarUrl} 
                  onChange={e => setCustomAvatarUrl(e.target.value)} 
                  placeholder="https://..." 
                  className="h-8 text-xs bg-black/20 border-white/10"
                />
              </div>
            </div>
          </div>
          
          <div className="space-y-2 mb-4">
            <Label className="text-xs">Language</Label>
            <Select value={language} onValueChange={setLanguage}><SelectTrigger className="bg-black/20 border-white/10 h-8 sm:h-9 text-sm"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="en">English</SelectItem><SelectItem value="it">Italiano</SelectItem><SelectItem value="es">Español</SelectItem><SelectItem value="fr">Français</SelectItem><SelectItem value="de">Deutsch</SelectItem></SelectContent></Select>
          </div>
          <Button onClick={saveProfile} disabled={saving} className="w-full bg-yellow-500 text-black mb-2 h-8 sm:h-9 text-sm">{saving ? 'Saving...' : 'Save Changes'}</Button>
          
          {/* Reset Player Button */}
          <Button variant="outline" className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10 h-8 sm:h-9 text-sm" onClick={() => setShowResetDialog(true)}>
            <RefreshCw className="w-3 sm:w-3.5 h-3 sm:h-3.5 mr-2" /> Reset Totale Player
          </Button>
        </CardContent>
      </Card>

      {/* Reset Dialog - Doppia Conferma */}
      <Dialog open={showResetDialog} onOpenChange={(open) => { setShowResetDialog(open); if(!open) setResetToken(null); }}>
        <DialogContent className="bg-[#1A1A1A] border-red-500/30 max-w-[95vw] sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" /> Reset Totale Player
            </DialogTitle>
          </DialogHeader>
          {!resetToken ? (
            <div className="space-y-4">
              <div className="bg-red-500/10 border border-red-500/30 rounded p-3">
                <p className="text-sm text-red-300 font-semibold mb-2">⚠️ ATTENZIONE: Azione IRREVERSIBILE!</p>
                <p className="text-xs text-gray-300">Perderai TUTTO:</p>
                <ul className="text-xs text-gray-400 list-disc list-inside mt-1 space-y-0.5">
                  <li>Tutti i film prodotti</li>
                  <li>Tutte le infrastrutture</li>
                  <li>Tutti i premi vinti</li>
                  <li>Livello, XP, Fama</li>
                  <li>Messaggi e chat</li>
                </ul>
              </div>
              <p className="text-sm text-gray-300">Tornerai a: Livello 1, $10M, 50 Fama</p>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => setShowResetDialog(false)}>Annulla</Button>
                <Button className="flex-1 bg-red-500 hover:bg-red-600" onClick={requestReset} disabled={resetting}>
                  {resetting ? 'Attendi...' : 'Richiedi Reset'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-3">
                <p className="text-sm text-yellow-300 font-semibold">🔐 Conferma Finale</p>
                <p className="text-xs text-gray-300 mt-1">Token valido per 5 minuti. Clicca "CONFERMA RESET" per procedere.</p>
              </div>
              <p className="text-center text-lg font-bold text-red-400">Sei ASSOLUTAMENTE sicuro?</p>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => { setShowResetDialog(false); setResetToken(null); }}>No, Annulla</Button>
                <Button className="flex-1 bg-red-600 hover:bg-red-700" onClick={confirmReset} disabled={resetting}>
                  {resetting ? 'Resetting...' : 'CONFERMA RESET'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* AI Avatar Generator Dialog */}
      <Dialog open={showAiGenerator} onOpenChange={setShowAiGenerator}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-[95vw] sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-yellow-500" /> Generate AI Avatar
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs mb-2 block">Describe your avatar</Label>
              <Input 
                value={aiPrompt} 
                onChange={e => setAiPrompt(e.target.value)} 
                placeholder="e.g., professional film director, elegant actress with glasses..."
                className="h-9 bg-black/20 border-white/10 text-sm"
              />
              <p className="text-[10px] text-gray-500 mt-1">Be specific: gender, age, style, profession...</p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {['Young male producer', 'Elegant female director', 'Veteran actor with beard', 'Glamorous actress'].map(preset => (
                <Button key={preset} variant="outline" size="sm" className="h-7 text-[10px] justify-start" onClick={() => setAiPrompt(preset)}>
                  {preset}
                </Button>
              ))}
            </div>
            <Button 
              onClick={generateAiAvatar} 
              disabled={generatingAi || !aiPrompt.trim()} 
              className="w-full bg-yellow-500 text-black h-9"
            >
              {generatingAi ? 'Generating...' : 'Generate Avatar'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Infrastructure Page

export default ProfilePage;
