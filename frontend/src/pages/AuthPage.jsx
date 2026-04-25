// CineWorld Studio's - AuthPage
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
import TutorialModal from '../components/TutorialModal';
import { VelionLoginBubble } from '../components/VelionLoginBubble';
import { PWAInstallBanner } from '../components/PWAInstallBanner';
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding,
  Smartphone
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';

// useTranslations imported from contexts

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);
  const [guestLoading, setGuestLoading] = useState(false);
  const { login, register, guestLogin } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslations();
  const navigate = useNavigate();

  const handleGuestLogin = async () => {
    setGuestLoading(true);
    try {
      await guestLogin();
      toast.success('Benvenuto ospite! Esplora il gioco liberamente');
      navigate('/dashboard');
    } catch (err) {
      toast.error('Errore nella creazione dell\'account ospite');
    } finally {
      setGuestLoading(false);
    }
  };

  const [formData, setFormData] = useState({
    email: '', password: '', nickname: '', production_house_name: '', owner_name: '', 
    language: 'en', age: '', gender: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!isLogin && !acceptedTerms) {
      toast.error('You must accept the community guidelines');
      return;
    }
    
    if (!isLogin && parseInt(formData.age) < 18) {
      toast.error('You must be 18 or older to register');
      return;
    }
    
    setLoading(true);
    try {
      if (isLogin) {
        await login(formData.email, formData.password, rememberMe);
      } else {
        await register({ ...formData, age: parseInt(formData.age), language });
        localStorage.setItem('show_dashboard_tour', '1');
      }
      toast.success(isLogin ? 'Bentornato!' : 'Account creato!');
      navigate('/dashboard');
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 401) {
        toast.error(detail || 'Email o password non validi');
      } else if (status === 500) {
        toast.error('Errore server. Riprova tra qualche secondo.');
      } else if (!err.response) {
        toast.error('Connessione al server non riuscita. Verifica la tua connessione.');
      } else {
        toast.error(detail || 'Sessione scaduta, effettua nuovamente l\'accesso');
      }
      // Clear any stale tokens
      localStorage.removeItem('cineworld_token');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center p-4 pb-20 cinema-gradient">
      <VelionLoginBubble onStart={() => {
        handleGuestLogin();
      }} />
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <Card className="bg-[#1A1A1A] border-white/10 relative">
          {/* Language Selector removed - Italian only */}
          
          <CardHeader className="text-center space-y-3 pb-4 pt-6">
            <div className="flex justify-center">
              <img src="/cineworld-logo.jpg" alt="CineWorld Studios" className="w-24 h-24 rounded-2xl shadow-lg shadow-yellow-500/20" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-3xl sm:text-4xl tracking-wide">CineWorld Studio's</CardTitle>
            <p className="text-sm sm:text-base text-gray-300 leading-snug px-2">
              Costruisci il tuo studio cinematografico e sfida altri player tra hype, sabotaggi e successo al botteghino.
            </p>
            <Button
              variant="ghost"
              size="sm"
              className="text-yellow-400 hover:bg-yellow-500/10 text-xs gap-1.5"
              onClick={() => setShowTutorial(true)}
              data-testid="auth-tutorial-btn"
            >
              <HelpCircle className="w-3.5 h-3.5" /> Come si gioca?
            </Button>
            <Badge className="bg-purple-500/20 text-purple-400 text-[10px]">BETA TEST</Badge>
            <PWAInstallBanner variant="inline" />
          </CardHeader>

          {showTutorial && <TutorialModal onClose={() => setShowTutorial(false)} />}
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-2.5">
              <div className="space-y-1">
                <Label className="text-xs">Email</Label>
                <Input
                  type="email"
                  placeholder="producer@cineworld.com"
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                  className="h-8 text-sm bg-black/20 border-white/10"
                  required
                  data-testid="email-input"
                />
              </div>
              
              <div className="space-y-1">
                <Label className="text-xs">Password</Label>
                <div className="relative">
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={e => setFormData({ ...formData, password: e.target.value })}
                    className="h-8 text-sm bg-black/20 border-white/10 pr-10"
                    required
                    data-testid="password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                    data-testid="toggle-password"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {!isLogin && (
                <>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <Label className="text-xs">{t('age')} (18+) *</Label>
                      <Input
                        type="number"
                        min="18"
                        max="120"
                        placeholder="18"
                        value={formData.age}
                        onChange={e => setFormData({ ...formData, age: e.target.value })}
                        className="h-8 text-sm bg-black/20 border-white/10"
                        required
                        data-testid="age-input"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">{t('gender')} *</Label>
                      <Select value={formData.gender} onValueChange={v => setFormData({ ...formData, gender: v })}>
                        <SelectTrigger className="h-8 text-sm bg-black/20 border-white/10" data-testid="gender-select">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="male">{t('male')}</SelectItem>
                          <SelectItem value="female">{t('female')}</SelectItem>
                          <SelectItem value="other">{t('other')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs">Nickname</Label>
                    <Input
                      placeholder="Your producer name"
                      value={formData.nickname}
                      onChange={e => setFormData({ ...formData, nickname: e.target.value })}
                      className="h-8 text-sm bg-black/20 border-white/10"
                      required
                      data-testid="nickname-input"
                    />
                  </div>
                  
                  <div className="space-y-1">
                    <Label className="text-xs">Production House</Label>
                    <Input
                      placeholder="e.g., Golden Star Productions"
                      value={formData.production_house_name}
                      onChange={e => setFormData({ ...formData, production_house_name: e.target.value })}
                      className="h-8 text-sm bg-black/20 border-white/10"
                      required
                      data-testid="production-house-input"
                    />
                  </div>
                  
                  <div className="space-y-1">
                    <Label className="text-xs">Owner Name</Label>
                    <Input
                      placeholder="Real or fictional"
                      value={formData.owner_name}
                      onChange={e => setFormData({ ...formData, owner_name: e.target.value })}
                      className="h-8 text-sm bg-black/20 border-white/10"
                      required
                      data-testid="owner-name-input"
                    />
                  </div>

                  <Card className="bg-red-500/10 border-red-500/30">
                    <CardContent className="p-2">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-red-400">{t('adult_warning')}</p>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="flex items-start gap-2">
                    <Checkbox 
                      id="terms" 
                      checked={acceptedTerms}
                      onCheckedChange={setAcceptedTerms}
                      data-testid="terms-checkbox"
                    />
                    <label htmlFor="terms" className="text-xs text-gray-400 leading-tight cursor-pointer">
                      I confirm I am 18+ and agree to the community guidelines.
                    </label>
                  </div>
                </>
              )}

              {isLogin && (
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="remember-me"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-3.5 h-3.5 accent-yellow-500 cursor-pointer"
                    data-testid="remember-me-checkbox"
                  />
                  <label htmlFor="remember-me" className="text-xs text-gray-400 cursor-pointer">
                    {language === 'it' ? 'Ricordami' : 'Remember me'}
                  </label>
                </div>
              )}

              <Button 
                type="submit" 
                className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold uppercase tracking-wider h-9 text-sm"
                disabled={loading || (!isLogin && !acceptedTerms)}
                data-testid="auth-submit-btn"
              >
                {loading ? 'Caricamento...' : isLogin ? 'Accedi' : 'Crea Account'}
              </Button>
            </form>

            {/* Recovery Links - Only show on login */}
            {isLogin && (
              <div className="mt-3 flex justify-center gap-4 text-[10px]">
                <button
                  type="button"
                  className="text-yellow-500/70 hover:text-yellow-400 underline"
                  onClick={() => navigate('/recovery/password')}
                  data-testid="forgot-password-link"
                >
                  {language === 'it' ? 'Password dimenticata?' : 'Forgot password?'}
                </button>
                <button
                  type="button"
                  className="text-yellow-500/70 hover:text-yellow-400 underline"
                  onClick={() => navigate('/recovery/nickname')}
                  data-testid="forgot-nickname-link"
                >
                  {language === 'it' ? 'Nickname dimenticato?' : 'Forgot nickname?'}
                </button>
              </div>
            )}

            <div className="mt-3 text-center">
              <button
                type="button"
                className="text-gray-400 hover:text-white text-xs"
                onClick={() => setIsLogin(!isLogin)}
                data-testid="toggle-auth-mode"
              >
                {isLogin ? "Non hai un account? Registrati" : 'Hai già un account? Accedi'}
              </button>
            </div>

            {/* Guest Login */}
            <div className="mt-4 pt-3 border-t border-white/10 text-center">
              <button
                type="button"
                className="group flex items-center justify-center gap-2 mx-auto px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-yellow-500/30 transition-all text-sm text-gray-400 hover:text-yellow-400"
                onClick={handleGuestLogin}
                disabled={guestLoading}
                data-testid="guest-login-btn"
              >
                {guestLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Gamepad2 className="w-4 h-4 group-hover:text-yellow-400 transition-colors" />
                )}
                {guestLoading ? 'Creazione...' : 'Prova senza registrarti'}
              </button>
              <p className="text-[9px] text-gray-600 mt-1">Gioca subito, registrati dopo per salvare i progressi</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

// Skill Badge Component
const SkillBadge = ({ name, value, change, language = 'it' }) => {
  const getBgColor = () => {
    if (change > 0) return 'bg-green-500/20 border-green-500/30';
    if (change < 0) return 'bg-red-500/20 border-red-500/30';
    return 'bg-white/5 border-white/10';
  };
  
  // Translate skill name
  const translatedName = SKILL_TRANSLATIONS[name]?.[language] || SKILL_TRANSLATIONS[name]?.['en'] || name;

  return (
    <div className={`flex items-center justify-between px-1.5 py-0.5 rounded border ${getBgColor()}`}>
      <span className="text-xs truncate mr-1">{translatedName}</span>
      <div className="flex items-center gap-0.5">
        <span className={`font-bold text-xs ${change > 0 ? 'text-green-500' : change < 0 ? 'text-red-500' : ''}`}>
          {value}
        </span>
        {change > 0 && <TrendingUp className="w-2.5 h-2.5 text-green-500" />}
        {change < 0 && <TrendingDown className="w-2.5 h-2.5 text-red-500" />}
      </div>
    </div>
  );
};

// User Profile Modal Component
const ChangePasswordSection = ({ api, language }) => {
  const [showForm, setShowForm] = useState(false);
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [saving, setSaving] = useState(false);
  
  const handleChange = async () => {
    if (newPw.length < 6) { toast.error(language === 'it' ? 'Minimo 6 caratteri' : 'Minimum 6 characters'); return; }
    if (newPw !== confirmPw) { toast.error(language === 'it' ? 'Le password non corrispondono' : 'Passwords do not match'); return; }
    setSaving(true);
    try {
      await api.post('/auth/change-password', { current_password: currentPw, new_password: newPw });
      toast.success(language === 'it' ? 'Password aggiornata!' : 'Password updated!');
      setShowForm(false); setCurrentPw(''); setNewPw(''); setConfirmPw('');
    } catch(e) {
      toast.error(e.response?.data?.detail || (language === 'it' ? 'Errore aggiornamento' : 'Update error'));
    }
    setSaving(false);
  };
  
  if (!showForm) return (
    <div className="mt-4">
      <Button variant="outline" className="w-full border-white/10 text-gray-400 h-9 text-sm" onClick={() => setShowForm(true)} data-testid="change-password-btn">
        <Lock className="w-4 h-4 mr-2" /> {language === 'it' ? 'Cambia Password' : 'Change Password'}
      </Button>
    </div>
  );
  
  return (
    <div className="mt-4 space-y-2 p-3 bg-black/30 rounded-lg border border-white/10">
      <h4 className="text-sm font-semibold flex items-center gap-2"><Lock className="w-4 h-4 text-yellow-500" /> {language === 'it' ? 'Cambia Password' : 'Change Password'}</h4>
      <Input type="password" placeholder={language === 'it' ? 'Password attuale' : 'Current password'} value={currentPw} onChange={e => setCurrentPw(e.target.value)} className="bg-black/20 border-white/10 h-9" data-testid="current-password-input" />
      <Input type="password" placeholder={language === 'it' ? 'Nuova password (min 6 car.)' : 'New password (min 6 char.)'} value={newPw} onChange={e => setNewPw(e.target.value)} className="bg-black/20 border-white/10 h-9" data-testid="new-password-input" />
      <Input type="password" placeholder={language === 'it' ? 'Conferma nuova password' : 'Confirm new password'} value={confirmPw} onChange={e => setConfirmPw(e.target.value)} className="bg-black/20 border-white/10 h-9" data-testid="confirm-password-input" />
      <div className="flex gap-2">
        <Button className="flex-1 bg-yellow-500 text-black h-9 text-sm" onClick={handleChange} disabled={saving} data-testid="save-password-btn">
          {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : (language === 'it' ? 'Salva' : 'Save')}
        </Button>
        <Button variant="outline" className="border-white/10 h-9 text-sm" onClick={() => { setShowForm(false); setCurrentPw(''); setNewPw(''); setConfirmPw(''); }}>
          {language === 'it' ? 'Annulla' : 'Cancel'}
        </Button>
      </div>
    </div>
  );
};

const UserProfileModal = ({ userId, isOpen, onClose, api }) => {
  const { language } = useContext(LanguageContext);
  const { user } = useContext(AuthContext);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [friendStatus, setFriendStatus] = useState(null); // 'friends', 'pending', 'none'
  const [myMajor, setMyMajor] = useState(null);
  const navigate = useNavigate();
  
  useEffect(() => {
    if (isOpen && userId) {
      setLoading(true);
      Promise.all([
        api.get(`/users/${userId}/full-profile`),
        api.get('/friends'),
        api.get('/friends/requests'),
        api.get('/major/my')
      ]).then(([profileRes, friendsRes, requestsRes, majorRes]) => {
        setProfile(profileRes.data);
        
        // Check friend status
        const isFriend = friendsRes.data?.some(f => f.id === userId);
        const hasPendingRequest = requestsRes.data?.outgoing?.some(r => r.user?.id === userId);
        setFriendStatus(isFriend ? 'friends' : hasPendingRequest ? 'pending' : 'none');
        
        // Check if user has a Major and can invite
        setMyMajor(majorRes.data?.has_major ? majorRes.data : null);
        
        setLoading(false);
      }).catch(err => {
        console.error(err);
        setLoading(false);
      });
    }
  }, [isOpen, userId, api]);
  
  if (!isOpen) return null;
  
  const t = (key) => {
    const translations = {
      level: language === 'it' ? 'Livello' : 'Level',
      films: language === 'it' ? 'Film' : 'Films',
      revenue: language === 'it' ? 'Incassi' : 'Revenue',
      likes: language === 'it' ? 'Like' : 'Likes',
      quality: language === 'it' ? 'Qualità Media' : 'Avg Quality',
      awards: language === 'it' ? 'Premi' : 'Awards',
      infrastructure: language === 'it' ? 'Infrastrutture' : 'Infrastructure',
      sendMessage: language === 'it' ? 'Messaggio' : 'Message',
      viewFilms: language === 'it' ? 'Vedi Film' : 'View Films',
      close: language === 'it' ? 'Chiudi' : 'Close',
      online: language === 'it' ? 'Online' : 'Online',
      offline: language === 'it' ? 'Offline' : 'Offline',
      bestFilm: language === 'it' ? 'Miglior Film' : 'Best Film',
      recentFilms: language === 'it' ? 'Film Recenti' : 'Recent Films',
      addFriend: language === 'it' ? 'Amicizia' : 'Add Friend',
      pendingRequest: language === 'it' ? 'In Attesa' : 'Pending',
      alreadyFriends: language === 'it' ? 'Amici' : 'Friends',
      inviteToMajor: language === 'it' ? 'Invita Major' : 'Invite to Major',
      invited: language === 'it' ? 'Invitato' : 'Invited',
      alreadyInMajor: language === 'it' ? 'In una Major' : 'In a Major'
    };
    return translations[key] || key;
  };
  
  const sendFriendRequest = async () => {
    try {
      setActionLoading('friend');
      await api.post('/friends/request', { user_id: userId });
      setFriendStatus('pending');
      toast.success(language === 'it' ? 'Richiesta di amicizia inviata!' : 'Friend request sent!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setActionLoading(null);
    }
  };
  
  const inviteToMajor = async () => {
    try {
      setActionLoading('major');
      await api.post('/major/invite', { user_id: userId });
      toast.success(language === 'it' ? 'Invito alla Major inviato!' : 'Major invitation sent!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setActionLoading(null);
    }
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="user-profile-modal">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin h-8 w-8 border-2 border-yellow-500 border-t-transparent rounded-full"></div>
          </div>
        ) : profile ? (
          <>
            <DialogHeader>
              <div className="flex items-center gap-4">
                <Avatar className="w-16 h-16">
                  <AvatarImage src={profile.user?.avatar_url} />
                  <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xl">{profile.user?.nickname?.[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <DialogTitle className="text-xl flex items-center gap-2">
                    {profile.user?.nickname}
                    {profile.is_online ? (
                      <Badge className="bg-green-500/20 text-green-400 text-xs">{t('online')}</Badge>
                    ) : (
                      <Badge className="bg-gray-500/20 text-gray-400 text-xs">{t('offline')}</Badge>
                    )}
                  </DialogTitle>
                  <p className="text-sm text-gray-400">{profile.user?.production_house_name}</p>
                  <p className="text-xs text-yellow-500">{t('level')} {profile.stats?.level}</p>
                </div>
              </div>
            </DialogHeader>
            
            {/* Stats Grid */}
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 my-4">
              <div className="bg-black/30 rounded p-2 text-center">
                <p className="text-lg font-bold text-yellow-500">{profile.stats?.total_films}</p>
                <p className="text-xs text-gray-400">{t('films')}</p>
              </div>
              <div className="bg-black/30 rounded p-2 text-center">
                <p className="text-lg font-bold text-green-500">${(profile.stats?.total_revenue / 1000000).toFixed(1)}M</p>
                <p className="text-xs text-gray-400">{t('revenue')}</p>
              </div>
              <div className="bg-black/30 rounded p-2 text-center">
                <p className="text-lg font-bold text-blue-500">{profile.stats?.avg_quality}%</p>
                <p className="text-xs text-gray-400">{t('quality')}</p>
              </div>
              <div className="bg-black/30 rounded p-2 text-center">
                <p className="text-lg font-bold text-purple-500">{profile.stats?.awards_count}</p>
                <p className="text-xs text-gray-400">{t('awards')}</p>
              </div>
              <div className="bg-black/30 rounded p-2 text-center">
                <p className="text-lg font-bold text-orange-500">{profile.stats?.infrastructure_count}</p>
                <p className="text-xs text-gray-400">{t('infrastructure')}</p>
              </div>
            </div>
            
            {/* Best Film */}
            {profile.best_film && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <Trophy className="w-4 h-4 text-yellow-500" />
                  {t('bestFilm')}
                </h4>
                <Card className="bg-black/30 border-yellow-500/30 cursor-pointer hover:border-yellow-500/50 transition-colors" onClick={() => { onClose(); navigate(`/films/${profile.best_film.id}`); }}>
                  <CardContent className="p-3 flex items-center gap-3">
                    {profile.best_film.poster_url && (
                      <img src={profile.best_film.poster_url} alt="" className="w-12 h-16 object-cover rounded" />
                    )}
                    <div className="flex-1">
                      <p className="font-semibold hover:text-yellow-500">{profile.best_film.title}</p>
                      <p className="text-xs text-gray-400">{profile.best_film.genre} • {profile.best_film.quality_score || 0}% quality</p>
                      <p className="text-xs text-green-500">${((profile.best_film.revenue || 0) / 1000000).toFixed(2)}M revenue</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
            
            {/* Recent Films */}
            {profile.recent_films?.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <Film className="w-4 h-4 text-blue-500" />
                  {t('recentFilms')}
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {profile.recent_films.slice(0, 4).map(film => (
                    <Card key={film.id} className="bg-black/30 border-white/10 cursor-pointer hover:border-yellow-500/30 transition-colors" onClick={() => { onClose(); navigate(`/films/${film.id}`); }}>
                      <CardContent className="p-2">
                        <p className="text-xs font-semibold truncate hover:text-yellow-500">{film.title}</p>
                        <p className="text-[10px] text-gray-400">{film.genre}</p>
                        <p className="text-[10px] text-yellow-500">{film.quality_score}%</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
            
            {/* Actions for other users */}
            {!profile.is_own_profile && (
              <div className="flex flex-wrap gap-2 mt-4">
                {/* Send Message */}
                <Button 
                  className="flex-1 bg-yellow-500 text-black hover:bg-yellow-400"
                  onClick={() => {
                    onClose();
                    navigate('/chat');
                  }}
                  data-testid="send-message-btn"
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  {t('sendMessage')}
                </Button>
                
                {/* Friend Request */}
                {friendStatus === 'friends' ? (
                  <Button variant="outline" className="flex-1 border-green-500/30 text-green-400" disabled>
                    <UserCheck className="w-4 h-4 mr-2" />
                    {t('alreadyFriends')}
                  </Button>
                ) : friendStatus === 'pending' ? (
                  <Button variant="outline" className="flex-1 border-yellow-500/30 text-yellow-400" disabled>
                    <Clock className="w-4 h-4 mr-2" />
                    {t('pendingRequest')}
                  </Button>
                ) : (
                  <Button 
                    variant="outline" 
                    className="flex-1 border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                    onClick={sendFriendRequest}
                    disabled={actionLoading === 'friend'}
                  >
                    {actionLoading === 'friend' ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <UserPlus className="w-4 h-4 mr-2" />
                    )}
                    {t('addFriend')}
                  </Button>
                )}
                
                {/* Invite to Major */}
                {myMajor?.has_major && (myMajor.my_role === 'founder' || myMajor.my_role === 'vice') && (
                  profile.user?.major_id ? (
                    <Button variant="outline" className="flex-1 border-gray-500/30 text-gray-400" disabled>
                      <Crown className="w-4 h-4 mr-2" />
                      {t('alreadyInMajor')}
                    </Button>
                  ) : (
                    <Button 
                      variant="outline" 
                      className="flex-1 border-purple-500/30 text-purple-400 hover:bg-purple-500/10"
                      onClick={inviteToMajor}
                      disabled={actionLoading === 'major'}
                    >
                      {actionLoading === 'major' ? (
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Crown className="w-4 h-4 mr-2" />
                      )}
                      {t('inviteToMajor')}
                    </Button>
                  )
                )}
              </div>
            )}
            
            {/* Change Password - Own Profile */}
            {profile.is_own_profile && (
              <ChangePasswordSection api={api} language={language} />
            )}
          </>
        ) : (
          <div className="text-center py-12 text-gray-400">User not found</div>
        )}
      </DialogContent>
    </Dialog>
  );
};

// Stats Detail Modal Component
const StatsDetailModal = ({ isOpen, onClose, statType, api }) => {
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const [detailedStats, setDetailedStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      api.get('/stats/detailed')
        .then(res => {
          setDetailedStats(res.data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [isOpen, api]);
  
  if (!isOpen) return null;
  
  const t = (key) => {
    const translations = {
      films: language === 'it' ? 'Film' : 'Films',
      revenue: language === 'it' ? 'Incassi' : 'Revenue',
      likes: language === 'it' ? 'Like' : 'Likes',
      quality: language === 'it' ? 'Qualità' : 'Quality',
      byGenre: language === 'it' ? 'Per Genere' : 'By Genre',
      topFilms: language === 'it' ? 'Top Film' : 'Top Films',
      distribution: language === 'it' ? 'Distribuzione' : 'Distribution',
      excellent: language === 'it' ? 'Eccellente' : 'Excellent',
      good: language === 'it' ? 'Buono' : 'Good',
      average: language === 'it' ? 'Medio' : 'Average',
      poor: language === 'it' ? 'Scarso' : 'Poor',
      total: language === 'it' ? 'Totale' : 'Total',
      avgPerFilm: language === 'it' ? 'Media per Film' : 'Average per Film'
    };
    return translations[key] || key;
  };
  
  const renderContent = () => {
    if (!detailedStats) return null;
    
    switch(statType) {
      case 'films':
        return (
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-semibold mb-2">{t('byGenre')}</h4>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(detailedStats.films?.by_genre || {}).map(([genre, count]) => (
                  <div key={genre} className="bg-black/30 rounded p-2 flex justify-between">
                    <span className="text-xs text-gray-400">{genre}</span>
                    <span className="text-xs font-bold text-yellow-500">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-2">{t('quality')} {t('distribution')}</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-green-500/10 rounded p-2 text-center">
                  <p className="text-lg font-bold text-green-500">{detailedStats.films?.by_quality?.excellent || 0}</p>
                  <p className="text-xs text-gray-400">{t('excellent')} (80%+)</p>
                </div>
                <div className="bg-blue-500/10 rounded p-2 text-center">
                  <p className="text-lg font-bold text-blue-500">{detailedStats.films?.by_quality?.good || 0}</p>
                  <p className="text-xs text-gray-400">{t('good')} (60-79%)</p>
                </div>
                <div className="bg-yellow-500/10 rounded p-2 text-center">
                  <p className="text-lg font-bold text-yellow-500">{detailedStats.films?.by_quality?.average || 0}</p>
                  <p className="text-xs text-gray-400">{t('average')} (40-59%)</p>
                </div>
                <div className="bg-red-500/10 rounded p-2 text-center">
                  <p className="text-lg font-bold text-red-500">{detailedStats.films?.by_quality?.poor || 0}</p>
                  <p className="text-xs text-gray-400">{t('poor')} (&lt;40%)</p>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-2">{t('topFilms')} ({t('revenue')})</h4>
              <div className="space-y-1">
                {(detailedStats.films?.top_by_revenue || []).map((film, i) => (
                  <div key={film.id} className="bg-black/30 rounded p-2 flex justify-between items-center cursor-pointer hover:bg-black/50 transition-colors" onClick={() => { onClose(); navigate(`/films/${film.id}`); }}>
                    <span className="text-xs hover:text-yellow-500">{i + 1}. {film.title}</span>
                    <span className="text-xs text-green-500">${(film.revenue / 1000000).toFixed(2)}M</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
        
      case 'revenue':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-green-500/10 rounded p-3 text-center border border-green-500/20">
                <p className="text-2xl font-bold text-green-500">${((detailedStats.revenue?.total || 0) / 1000000).toFixed(2)}M</p>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Box Office Attuale' : 'Current Box Office'}</p>
              </div>
              <div className="bg-blue-500/10 rounded p-3 text-center border border-blue-500/20">
                <p className="text-2xl font-bold text-blue-500">${((detailedStats.revenue?.average_per_film || 0) / 1000000).toFixed(2)}M</p>
                <p className="text-xs text-gray-400">{t('avgPerFilm')}</p>
              </div>
            </div>
            {detailedStats.revenue?.estimated_total > 0 && (
              <div className="bg-purple-500/10 rounded p-3 border border-purple-500/20">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-xs text-gray-400">{language === 'it' ? 'Stima Finale (4 settimane)' : 'Estimated Final (4 weeks)'}</p>
                    <p className="text-xl font-bold text-purple-400">${((detailedStats.revenue?.estimated_total || 0) / 1000000).toFixed(2)}M</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-purple-400 opacity-50" />
                </div>
                <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Basata su affluenza e qualità attuali' : 'Based on current attendance and quality'}</p>
              </div>
            )}
            <div>
              <h4 className="text-sm font-semibold mb-2">{t('byGenre')}</h4>
              <div className="space-y-1">
                {Object.entries(detailedStats.revenue?.by_genre || {}).sort((a, b) => b[1] - a[1]).map(([genre, amount]) => (
                  <div key={genre} className="bg-black/30 rounded p-2 flex justify-between">
                    <span className="text-xs text-gray-400">{genre}</span>
                    <span className="text-xs font-bold text-green-500">${(amount / 1000000).toFixed(2)}M</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
        
      case 'quality':
        return (
          <div className="space-y-4">
            <div className="bg-blue-500/10 rounded p-4 text-center">
              <p className="text-3xl font-bold text-blue-500">{(detailedStats.quality?.average || 0).toFixed(1)}%</p>
              <p className="text-sm text-gray-400">{t('average')} {t('quality')}</p>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-2">{t('distribution')}</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-green-500/10 rounded p-2 text-center">
                  <p className="text-lg font-bold text-green-500">{detailedStats.quality?.distribution?.excellent || 0}</p>
                  <p className="text-xs text-gray-400">{t('excellent')} (80%+)</p>
                </div>
                <div className="bg-blue-500/10 rounded p-2 text-center">
                  <p className="text-lg font-bold text-blue-500">{detailedStats.quality?.distribution?.good || 0}</p>
                  <p className="text-xs text-gray-400">{t('good')} (60-79%)</p>
                </div>
                <div className="bg-yellow-500/10 rounded p-2 text-center">
                  <p className="text-lg font-bold text-yellow-500">{detailedStats.quality?.distribution?.average || 0}</p>
                  <p className="text-xs text-gray-400">{t('average')} (40-59%)</p>
                </div>
                <div className="bg-red-500/10 rounded p-2 text-center">
                  <p className="text-lg font-bold text-red-500">{detailedStats.quality?.distribution?.poor || 0}</p>
                  <p className="text-xs text-gray-400">{t('poor')} (&lt;40%)</p>
                </div>
              </div>
            </div>
          </div>
        );
        
      default:
        return <p className="text-gray-400 text-center py-8">Select a stat to view details</p>;
    }
  };
  
  const getTitleForStat = () => {
    const titles = {
      films: language === 'it' ? 'Dettagli Film' : 'Films Details',
      revenue: language === 'it' ? 'Dettagli Incassi' : 'Revenue Details',
      quality: language === 'it' ? 'Dettagli Qualità' : 'Quality Details'
    };
    return titles[statType] || 'Dettagli';
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md" data-testid="stats-detail-modal">
        <DialogHeader>
          <DialogTitle>{getTitleForStat()}</DialogTitle>
        </DialogHeader>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin h-8 w-8 border-2 border-yellow-500 border-t-transparent rounded-full"></div>
          </div>
        ) : (
          renderContent()
        )}
      </DialogContent>
    </Dialog>
  );
};

// Dashboard Page

export default AuthPage;
