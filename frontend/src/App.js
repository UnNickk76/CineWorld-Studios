import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import confetti from 'canvas-confetti';
import { 
  Film, Home, Users, MessageSquare, BarChart3, User, LogOut, Plus, Heart, 
  Globe, Calendar, DollarSign, Star, Clapperboard, Camera, MapPin, Sparkles,
  Send, Image, ChevronRight, ChevronDown, ChevronLeft, Menu, X, Settings, 
  Gamepad2, Trophy, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, Trash2,
  Check, XCircle, Newspaper, MessageCircle, Building, Building2, GraduationCap,
  Award, Crown, Landmark, Car, ShoppingBag, Ticket, Popcorn, ChevronUp, Lock,
  Wallet, Bell, HelpCircle, Info, Music, BookOpen, Medal, Eye, EyeOff,
  ArrowLeft, ArrowRight, UserPlus, UserCheck, Handshake, Target, Clock, RotateCcw,
  Download, Smartphone, Share2, Link2, Copy, QrCode, CheckCircle, Zap, Lightbulb, Bug,
  KeyRound, AlertCircle, Mail, Tv
} from 'lucide-react';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from './components/ui/avatar';
import { ScrollArea } from './components/ui/scroll-area';
import { Slider } from './components/ui/slider';
import { Textarea } from './components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription, DialogFooter } from './components/ui/dialog';
import { Label } from './components/ui/label';
import { Calendar as CalendarComponent } from './components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './components/ui/popover';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './components/ui/alert-dialog';
import { Checkbox } from './components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from './components/ui/radio-group';
import { format } from 'date-fns';
import { motion, AnimatePresence } from 'framer-motion';
import '@/App.css';

// Import from refactored modules
import { AuthContext, LanguageContext, AuthProvider, LanguageProvider, useTranslations } from './contexts';
import { SKILL_TRANSLATIONS } from './constants';

// Import pages from separate files
import ReleaseNotes from './pages/ReleaseNotes';
import TutorialPage from './pages/TutorialPage';
import CreditsPage from './pages/CreditsPage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Top Navbar Component
const TopNavbar = () => {
  const { user, logout, api } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslations();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [levelInfo, setLevelInfo] = useState(null);
  const [notificationCount, setNotificationCount] = useState(0);
  const [releaseNotesCount, setReleaseNotesCount] = useState(0);
  const [majorInfo, setMajorInfo] = useState(null);
  const [festivalNotifications, setFestivalNotifications] = useState([]);
  const [userTimezone, setUserTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Rome');

  useEffect(() => {
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {});
    api.get('/notifications/count').then(r => setNotificationCount(r.data.unread_count)).catch(() => {});
    api.get('/release-notes/unread-count').then(r => setReleaseNotesCount(r.data.unread_count)).catch(() => {});
    api.get('/major/my').then(r => setMajorInfo(r.data)).catch(() => {});
    
    // Festival notifications polling
    const fetchFestivalNotifications = () => {
      api.get(`/festivals/notifications?timezone=${userTimezone}&language=${language}`)
        .then(r => {
          const notifs = r.data.notifications || [];
          setFestivalNotifications(notifs);
          // Show toast for starting ceremonies
          notifs.filter(n => n.type === 'starting').forEach(n => {
            toast.info(n.message, { duration: 10000 });
          });
        }).catch(() => {});
    };
    
    fetchFestivalNotifications();
    const interval = setInterval(fetchFestivalNotifications, 60000); // Check every minute
    
    return () => clearInterval(interval);
  }, [api, user?.total_xp, location.pathname, userTimezone, language]);

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'dashboard' },
    { path: '/films', icon: Film, label: 'my_films' },
    { path: '/create', icon: Plus, label: 'create_film' },
    { path: '/drafts', icon: Clock, label: 'drafts_preengagement' },
    { path: '/pre-engagement', icon: Users, label: 'pre_engagement' },
    { path: '/sagas', icon: BookOpen, label: 'sagas_series' },
    { path: '/infrastructure', icon: Building, label: 'infrastructure' },
    { path: '/marketplace', icon: ShoppingBag, label: 'marketplace' },
    { path: '/tour', icon: MapPin, label: 'tour' },
    { path: '/journal', icon: Newspaper, label: 'cinema_journal' },
    { path: '/stars', icon: Star, label: 'discovered_stars' },
    { path: '/festivals', icon: Award, label: 'festivals' },
    { path: '/social', icon: Trophy, label: 'cineboard' },
    { path: '/games', icon: Gamepad2, label: 'mini_games' },
    { path: '/leaderboard', icon: Trophy, label: 'leaderboard' },
    { path: '/chat', icon: MessageSquare, label: 'chat' },
    { path: '/releases', icon: Sparkles, label: 'release_notes', notificationCount: releaseNotesCount },
    { path: '/feedback', icon: Lightbulb, label: 'feedback' },
    { path: '/tutorial', icon: HelpCircle, label: 'tutorial' },
    { path: '/credits', icon: Info, label: 'credits' },
  ];

  const gameDate = new Date().toLocaleDateString(language === 'it' ? 'it-IT' : language === 'es' ? 'es-ES' : language === 'fr' ? 'fr-FR' : language === 'de' ? 'de-DE' : 'en-US', {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
  });
  
  // Check if we can go back
  const canGoBack = location.pathname !== '/dashboard' && window.history.length > 1;

  return (
    <nav className="fixed top-0 left-0 right-0 h-14 bg-[#0F0F10] border-b border-white/10 z-50">
      <div className="max-w-7xl mx-auto h-full px-2 sm:px-3 flex items-center justify-between">
        {/* Left section: Logo */}
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
          {/* Back Button - Hidden on very small screens */}
          {canGoBack && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="hidden sm:flex h-8 w-8 p-0 text-gray-400 hover:text-white"
              onClick={() => navigate(-1)}
              data-testid="back-btn"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
          )}
          
          <div className="flex items-center gap-1.5 cursor-pointer" onClick={() => navigate('/dashboard')} data-testid="logo">
            <Clapperboard className="w-6 h-6 sm:w-7 sm:h-7 text-yellow-500" />
            <span className="font-['Bebas_Neue'] text-base sm:text-lg tracking-wide hidden sm:block">CineWorld</span>
          </div>
        </div>

        {/* Center: Desktop Navigation (limited items) - Hidden on mobile */}
        <div className="hidden lg:flex items-center gap-0.5 flex-1 justify-center overflow-hidden">
          {navItems.slice(0, 8).map(item => (
            <Button
              key={item.path}
              variant={location.pathname === item.path ? "default" : "ghost"}
              size="sm"
              className={`gap-1 px-2 h-8 flex-shrink-0 ${location.pathname === item.path ? 'bg-yellow-500 text-black hover:bg-yellow-400' : 'text-gray-400 hover:text-white'}`}
              onClick={() => navigate(item.path)}
              data-testid={`nav-${item.label}`}
            >
              <item.icon className="w-3.5 h-3.5" />
              <span className="hidden xl:inline text-xs">{t(item.label)}</span>
            </Button>
          ))}
        </div>

        {/* Right section: Quick Icons + Mobile Menu */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Festival/TV Button - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${festivalNotifications.length > 0 ? 'text-yellow-400 animate-pulse' : location.pathname === '/festivals' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => festivalNotifications.length > 0 ? navigate(`/festivals?live=${festivalNotifications[0].festival_id}`) : navigate('/festivals')}
            data-testid="festival-tv-btn"
            title={festivalNotifications.length > 0 ? (festivalNotifications[0].message || 'Festival Live') : (language === 'it' ? 'Festival' : 'Festivals')}
          >
            <Tv className="w-4 h-4" />
            {festivalNotifications.length > 0 && festivalNotifications[0].type === 'starting' && (
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full animate-ping"></span>
            )}
          </Button>
          
          {/* Major - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/major' ? 'text-purple-400' : 'text-gray-400 hover:text-purple-400'}`}
            onClick={() => navigate('/major')}
            data-testid="major-btn"
            title="Major"
          >
            <Crown className="w-4 h-4" />
          </Button>
          
          {/* Infrastructure - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/infrastructure' ? 'text-blue-400' : 'text-gray-400 hover:text-blue-400'}`}
            onClick={() => navigate('/infrastructure')}
            data-testid="infrastructure-btn"
            title={language === 'it' ? 'Infrastrutture' : 'Infrastructure'}
          >
            <Building2 className="w-4 h-4" />
          </Button>
          
          {/* Social/Chat - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/social' ? 'text-green-400' : 'text-gray-400 hover:text-green-400'}`}
            onClick={() => navigate('/social')}
            data-testid="social-btn"
            title={language === 'it' ? 'Social & Chat' : 'Social & Chat'}
          >
            <MessageSquare className="w-4 h-4" />
          </Button>
          
          {/* Notifications - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/notifications' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => navigate('/notifications')}
            data-testid="notifications-btn"
          >
            <Bell className="w-4 h-4" />
            {notificationCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[12px] h-3 px-0.5 bg-red-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                {notificationCount > 9 ? '9+' : notificationCount}
              </span>
            )}
          </Button>

          {/* Funds - Compact */}
          <div className="flex items-center gap-0.5 bg-yellow-500/10 px-1 sm:px-2 py-0.5 sm:py-1 rounded border border-yellow-500/20">
            <DollarSign className="w-3 h-3 text-yellow-500" />
            <span className="text-yellow-500 font-bold text-[9px] sm:text-xs" data-testid="user-funds">
              ${user?.funds >= 1000000 ? `${(user?.funds / 1000000).toFixed(1)}M` : user?.funds >= 1000 ? `${(user?.funds / 1000).toFixed(0)}K` : user?.funds?.toLocaleString() || '0'}
            </span>
          </div>
          
          {/* Friends - Hidden on very small mobile */}
          <Button
            variant="ghost"
            size="sm"
            className={`hidden sm:flex relative h-8 w-8 p-0 ${location.pathname === '/friends' ? 'text-cyan-400' : 'text-gray-400 hover:text-cyan-400'}`}
            onClick={() => navigate('/friends')}
            data-testid="friends-btn"
            title={language === 'it' ? 'Amici' : 'Friends'}
          >
            <UserPlus className="w-4 h-4" />
          </Button>
          
          {/* Level Badge - Hidden on mobile */}
          {levelInfo && (
            <div className="hidden lg:flex items-center gap-1.5 bg-purple-500/10 px-2 py-1 rounded border border-purple-500/20 cursor-pointer" onClick={() => navigate('/profile')}>
              <Star className="w-3 h-3 text-purple-400" />
              <span className="text-purple-400 font-bold text-xs">Lv.{levelInfo.level}</span>
            </div>
          )}

          {/* Language selector - Hidden on small screens */}
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="hidden md:flex w-12 h-7 text-xs bg-transparent border-white/10 px-1" data-testid="language-selector">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">EN</SelectItem>
              <SelectItem value="it">IT</SelectItem>
              <SelectItem value="es">ES</SelectItem>
              <SelectItem value="fr">FR</SelectItem>
              <SelectItem value="de">DE</SelectItem>
            </SelectContent>
          </Select>

          {/* Profile Avatar - Hidden on mobile */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" className="hidden md:flex p-1 h-8 w-8" data-testid="profile-menu">
                <Avatar className="w-7 h-7 border border-yellow-500/30">
                  <AvatarImage src={user?.avatar_url} />
                  <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xs">
                    {user?.nickname?.[0]?.toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-48 bg-[#1A1A1A] border-white/10 p-2">
              <div className="space-y-1">
                <div className="border-b border-white/10 pb-2 mb-2">
                  <p className="font-semibold text-sm">{user?.nickname}</p>
                  <p className="text-xs text-gray-400">{user?.production_house_name}</p>
                  {levelInfo && (
                    <div className="flex items-center gap-1 mt-1">
                      <Badge className="bg-purple-500/20 text-purple-400 text-[10px] h-4">Lv.{levelInfo.level}</Badge>
                      <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px] h-4">Fame {user?.fame?.toFixed(0) || 50}</Badge>
                    </div>
                  )}
                </div>
                <Button variant="ghost" size="sm" className="w-full justify-start gap-2 h-8" onClick={() => navigate('/profile')} data-testid="profile-btn">
                  <User className="w-3.5 h-3.5" /> {t('profile')}
                </Button>
                <Button variant="ghost" size="sm" className="w-full justify-start gap-2 h-8 text-red-400 hover:text-red-300 hover:bg-red-500/10" onClick={logout} data-testid="logout-btn">
                  <LogOut className="w-3.5 h-3.5" /> {t('logout')}
                </Button>
              </div>
            </PopoverContent>
          </Popover>

          {/* MOBILE HAMBURGER MENU - Always visible on mobile */}
          <Button 
            variant="ghost" 
            className="lg:hidden flex items-center justify-center p-1 h-8 w-8 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10" 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            data-testid="mobile-menu-btn"
          >
            {mobileMenuOpen ? <X className="w-5 h-5 text-white" /> : <Menu className="w-5 h-5 text-white" />}
          </Button>
        </div>
      </div>

      {/* Mobile Menu Dropdown - SOLID DARK BACKGROUND */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="lg:hidden absolute top-14 left-0 right-0 bg-[#0a0a0a] border-b border-white/10 shadow-2xl max-h-[80vh] overflow-y-auto"
          >
            {/* Mobile User Info Header */}
            <div className="flex items-center justify-between px-3 py-3 bg-[#111111] border-b border-white/10">
              <div className="flex items-center gap-3">
                <Avatar className="w-10 h-10 border-2 border-yellow-500/50">
                  <AvatarImage src={user?.avatar_url} />
                  <AvatarFallback className="bg-yellow-500/20 text-yellow-500">
                    {user?.nickname?.[0]?.toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold text-sm text-white">{user?.nickname}</p>
                  <div className="flex items-center gap-2">
                    {levelInfo && (
                      <Badge className="bg-purple-500/20 text-purple-400 text-[10px] h-4">Lv.{levelInfo.level}</Badge>
                    )}
                    <span className="text-[10px] text-gray-400">{gameDate}</span>
                  </div>
                </div>
              </div>
              {/* Language Selector in Mobile */}
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="w-14 h-8 text-xs bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">EN</SelectItem>
                  <SelectItem value="it">IT</SelectItem>
                  <SelectItem value="es">ES</SelectItem>
                  <SelectItem value="fr">FR</SelectItem>
                  <SelectItem value="de">DE</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Mobile Navigation Grid - Solid Background */}
            <div className="grid grid-cols-3 gap-2 p-3 bg-[#0a0a0a]">
              {navItems.map(item => (
                <Button
                  key={item.path}
                  variant={location.pathname === item.path ? "default" : "ghost"}
                  size="sm"
                  className={`flex flex-col items-center gap-1.5 h-16 py-2 px-1 relative rounded-xl ${
                    location.pathname === item.path 
                      ? 'bg-yellow-500 text-black hover:bg-yellow-400' 
                      : 'bg-[#1a1a1a] hover:bg-[#252525] text-gray-300 border border-white/5'
                  }`}
                  onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}
                >
                  <item.icon className="w-5 h-5" />
                  <span className="text-[9px] font-medium truncate w-full text-center leading-tight">{t(item.label)}</span>
                  {item.notificationCount > 0 && (
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                  )}
                </Button>
              ))}
            </div>
            
            {/* Mobile Quick Actions - Solid Dark */}
            <div className="flex items-center justify-around p-3 border-t border-white/10 bg-[#111111]">
              <Button 
                variant="ghost" 
                size="sm" 
                className="flex flex-col items-center gap-1 h-14 px-4 text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 rounded-xl"
                onClick={() => { navigate('/major'); setMobileMenuOpen(false); }}
              >
                <Crown className="w-5 h-5" />
                <span className="text-[10px] font-medium">Major</span>
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                className="flex flex-col items-center gap-1 h-14 px-4 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-xl"
                onClick={() => { navigate('/friends'); setMobileMenuOpen(false); }}
              >
                <UserPlus className="w-5 h-5" />
                <span className="text-[10px] font-medium">{language === 'it' ? 'Amici' : 'Friends'}</span>
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                className="flex flex-col items-center gap-1 h-14 px-4 text-green-400 hover:text-green-300 hover:bg-green-500/10 rounded-xl"
                onClick={() => { navigate('/profile'); setMobileMenuOpen(false); }}
              >
                <User className="w-5 h-5" />
                <span className="text-[10px] font-medium">{language === 'it' ? 'Profilo' : 'Profile'}</span>
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                className="flex flex-col items-center gap-1 h-14 px-4 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl"
                onClick={() => { logout(); setMobileMenuOpen(false); }}
              >
                <LogOut className="w-5 h-5" />
                <span className="text-[10px] font-medium">{language === 'it' ? 'Esci' : 'Logout'}</span>
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

// Password Recovery Page
const PasswordRecoveryPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/recovery/request`, {
        email,
        recovery_type: 'password'
      });
      setSent(true);
      toast.success(language === 'it' ? 'Controlla la tua email!' : 'Check your email!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardHeader className="text-center space-y-3">
            <div className="flex justify-center">
              <KeyRound className="w-12 h-12 text-yellow-500" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-2xl">
              {language === 'it' ? 'Recupera Password' : 'Reset Password'}
            </CardTitle>
            <CardDescription className="text-xs">
              {language === 'it' 
                ? 'Inserisci la tua email per ricevere il link di reset'
                : 'Enter your email to receive a reset link'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center">
                  <Mail className="w-8 h-8 text-green-500" />
                </div>
                <p className="text-green-400">
                  {language === 'it' 
                    ? 'Email inviata! Controlla la tua casella di posta.'
                    : 'Email sent! Check your inbox.'}
                </p>
                <Button variant="outline" onClick={() => navigate('/auth')} className="mt-4">
                  {language === 'it' ? 'Torna al Login' : 'Back to Login'}
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1">
                  <Label className="text-xs">Email</Label>
                  <Input
                    type="email"
                    placeholder="email@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className="h-10 bg-black/20 border-white/10"
                    required
                    data-testid="recovery-email-input"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold"
                  disabled={loading}
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : (language === 'it' ? 'Invia Link' : 'Send Link')}
                </Button>
                <Button variant="ghost" onClick={() => navigate('/auth')} className="w-full text-gray-400">
                  {language === 'it' ? 'Torna al Login' : 'Back to Login'}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

// Nickname Recovery Page
const NicknameRecoveryPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/recovery/request`, {
        email,
        recovery_type: 'nickname'
      });
      setSent(true);
      toast.success(language === 'it' ? 'Controlla la tua email!' : 'Check your email!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardHeader className="text-center space-y-3">
            <div className="flex justify-center">
              <User className="w-12 h-12 text-yellow-500" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-2xl">
              {language === 'it' ? 'Recupera Nickname' : 'Recover Nickname'}
            </CardTitle>
            <CardDescription className="text-xs">
              {language === 'it' 
                ? 'Inserisci la tua email per ricevere il tuo nickname'
                : 'Enter your email to receive your nickname'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center">
                  <Mail className="w-8 h-8 text-green-500" />
                </div>
                <p className="text-green-400">
                  {language === 'it' 
                    ? 'Email inviata! Troverai il tuo nickname nel messaggio.'
                    : 'Email sent! You\'ll find your nickname in the message.'}
                </p>
                <Button variant="outline" onClick={() => navigate('/auth')} className="mt-4">
                  {language === 'it' ? 'Torna al Login' : 'Back to Login'}
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1">
                  <Label className="text-xs">Email</Label>
                  <Input
                    type="email"
                    placeholder="email@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className="h-10 bg-black/20 border-white/10"
                    required
                    data-testid="nickname-recovery-email-input"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold"
                  disabled={loading}
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : (language === 'it' ? 'Invia Nickname' : 'Send Nickname')}
                </Button>
                <Button variant="ghost" onClick={() => navigate('/auth')} className="w-full text-gray-400">
                  {language === 'it' ? 'Torna al Login' : 'Back to Login'}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

// Reset Password Page (with token from email)
const ResetPasswordPage = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [tokenValid, setTokenValid] = useState(null);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/auth/recovery/verify-token/${token}`)
        .then(res => setTokenValid(res.data.valid))
        .catch(() => setTokenValid(false));
    } else {
      setTokenValid(false);
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error(language === 'it' ? 'Le password non coincidono' : 'Passwords do not match');
      return;
    }
    if (password.length < 6) {
      toast.error(language === 'it' ? 'Password troppo corta (min 6 caratteri)' : 'Password too short (min 6 chars)');
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/recovery/reset-password`, {
        token,
        new_password: password
      });
      setSuccess(true);
      toast.success(language === 'it' ? 'Password aggiornata!' : 'Password updated!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally {
      setLoading(false);
    }
  };

  if (tokenValid === null) {
    return (
      <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-yellow-500" />
      </div>
    );
  }

  if (!tokenValid) {
    return (
      <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center p-4">
        <Card className="bg-[#1A1A1A] border-white/10 max-w-md w-full">
          <CardContent className="pt-6 text-center space-y-4">
            <AlertCircle className="w-16 h-16 mx-auto text-red-500" />
            <h2 className="text-xl font-bold text-red-400">
              {language === 'it' ? 'Link non valido o scaduto' : 'Invalid or expired link'}
            </h2>
            <p className="text-gray-400 text-sm">
              {language === 'it' 
                ? 'Richiedi un nuovo link di reset dalla pagina di login.'
                : 'Request a new reset link from the login page.'}
            </p>
            <Button onClick={() => navigate('/auth')} className="bg-yellow-500 text-black hover:bg-yellow-400">
              {language === 'it' ? 'Torna al Login' : 'Back to Login'}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardHeader className="text-center space-y-3">
            <div className="flex justify-center">
              <KeyRound className="w-12 h-12 text-yellow-500" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-2xl">
              {language === 'it' ? 'Nuova Password' : 'New Password'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center">
                  <Check className="w-8 h-8 text-green-500" />
                </div>
                <p className="text-green-400">
                  {language === 'it' ? 'Password aggiornata con successo!' : 'Password updated successfully!'}
                </p>
                <Button onClick={() => navigate('/auth')} className="bg-yellow-500 text-black hover:bg-yellow-400">
                  {language === 'it' ? 'Vai al Login' : 'Go to Login'}
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1">
                  <Label className="text-xs">{language === 'it' ? 'Nuova Password' : 'New Password'}</Label>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    className="h-10 bg-black/20 border-white/10"
                    required
                    minLength={6}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{language === 'it' ? 'Conferma Password' : 'Confirm Password'}</Label>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    className="h-10 bg-black/20 border-white/10"
                    required
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold"
                  disabled={loading}
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : (language === 'it' ? 'Aggiorna Password' : 'Update Password')}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

// Auth Page
const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login, register } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslations();
  const navigate = useNavigate();

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
        await login(formData.email, formData.password);
      } else {
        await register({ ...formData, age: parseInt(formData.age), language });
      }
      toast.success(isLogin ? 'Welcome back!' : 'Account created!');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center p-4 pb-20 cinema-gradient">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <Card className="bg-[#1A1A1A] border-white/10 relative">
          {/* Language Selector */}
          <div className="absolute top-4 right-4 z-10">
            <div className="flex items-center gap-1 bg-black/40 rounded-full p-1">
              <button
                onClick={() => setLanguage('it')}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  language === 'it' ? 'bg-yellow-500 text-black' : 'text-gray-400 hover:text-white'
                }`}
              >
                🇮🇹 IT
              </button>
              <button
                onClick={() => setLanguage('en')}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  language === 'en' ? 'bg-yellow-500 text-black' : 'text-gray-400 hover:text-white'
                }`}
              >
                🇬🇧 EN
              </button>
            </div>
          </div>
          
          <CardHeader className="text-center space-y-3 pb-4 pt-12">
            <div className="flex justify-center">
              <Clapperboard className="w-12 h-12 text-yellow-500" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-2xl tracking-wide">CineWorld Studio's</CardTitle>
            <CardDescription className="text-xs">
              {isLogin 
                ? (language === 'it' ? 'Accedi alla tua casa di produzione' : 'Sign in to your production house')
                : (language === 'it' ? 'Crea il tuo impero cinematografico' : 'Create your production empire')}
            </CardDescription>
            <Badge className="bg-purple-500/20 text-purple-400 text-[10px]">BETA TEST</Badge>
          </CardHeader>
          <CardContent>
            {/* Download App Button */}
            <Button
              variant="outline"
              className="w-full mb-4 border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10"
              onClick={() => navigate('/download')}
            >
              <Smartphone className="w-4 h-4 mr-2" />
              {language === 'it' ? 'Scarica App per iPhone/Android' : 'Download App for iPhone/Android'}
            </Button>
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

              <Button 
                type="submit" 
                className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold uppercase tracking-wider h-9 text-sm"
                disabled={loading || (!isLogin && !acceptedTerms)}
                data-testid="auth-submit-btn"
              >
                {loading ? 'Loading...' : isLogin ? 'Sign In' : 'Create Account'}
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
                {isLogin ? "Don't have an account? Register" : 'Already have an account? Sign In'}
              </button>
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
      toast.error(e.response?.data?.detail || 'Error');
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
      toast.error(e.response?.data?.detail || 'Error');
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
                <p className="text-lg font-bold text-pink-500">{profile.stats?.total_likes}</p>
                <p className="text-xs text-gray-400">{t('likes')}</p>
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
            
            {/* Actions */}
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
                  <div key={film.id} className="bg-black/30 rounded p-2 flex justify-between items-center cursor-pointer hover:bg-black/50 transition-colors" onClick={() => { setShowStatsDetail(false); navigate(`/films/${film.id}`); }}>
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
        
      case 'likes':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-pink-500/10 rounded p-3 text-center">
                <p className="text-2xl font-bold text-pink-500">{detailedStats.likes?.total || 0}</p>
                <p className="text-xs text-gray-400">{t('total')} {t('likes')}</p>
              </div>
              <div className="bg-blue-500/10 rounded p-3 text-center">
                <p className="text-2xl font-bold text-blue-500">{(detailedStats.likes?.average_per_film || 0).toFixed(1)}</p>
                <p className="text-xs text-gray-400">{t('avgPerFilm')}</p>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-2">{t('topFilms')} ({t('likes')})</h4>
              <div className="space-y-1">
                {(detailedStats.films?.top_by_likes || []).map((film, i) => (
                  <div key={film.id} className="bg-black/30 rounded p-2 flex justify-between items-center cursor-pointer hover:bg-black/50 transition-colors" onClick={() => { setShowStatsDetail(false); navigate(`/films/${film.id}`); }}>
                    <span className="text-xs hover:text-yellow-500">{i + 1}. {film.title}</span>
                    <span className="text-xs text-pink-500">{film.likes} likes</span>
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
      likes: language === 'it' ? 'Dettagli Like' : 'Likes Details',
      quality: language === 'it' ? 'Dettagli Qualità' : 'Quality Details'
    };
    return titles[statType] || 'Details';
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
const Dashboard = () => {
  const { user, api, refreshUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [stats, setStats] = useState(null);
  const [films, setFilms] = useState([]);
  const [challenges, setChallenges] = useState({ daily: [], weekly: [] });
  const [catchupData, setCatchupData] = useState(null);
  const [pendingRevenue, setPendingRevenue] = useState(null);
  const [collecting, setCollecting] = useState(false);
  const navigate = useNavigate();
  
  // Stats detail modal state
  const [showStatsDetail, setShowStatsDetail] = useState(false);
  const [selectedStatType, setSelectedStatType] = useState(null);
  
  const openStatDetail = (statType) => {
    setSelectedStatType(statType);
    setShowStatsDetail(true);
  };

  const loadPendingRevenue = async () => {
    try {
      const res = await api.get('/revenue/pending-all');
      setPendingRevenue(res.data);
    } catch (e) {
      console.error('Error loading pending revenue:', e);
    }
  };

  const handleCollectAll = async () => {
    if (!pendingRevenue?.can_collect) return;
    setCollecting(true);
    try {
      const res = await api.post('/revenue/collect-all');
      toast.success(res.data.message, { duration: 5000 });
      refreshUser();
      loadPendingRevenue();
      // Refresh stats
      const statsRes = await api.get('/statistics/my');
      setStats(statsRes.data);
    } catch (e) {
      toast.error('Errore nella riscossione');
    } finally {
      setCollecting(false);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        // First, process offline catch-up
        const catchupRes = await api.post('/catchup/process');
        if (catchupRes.data.catchup_revenue > 0) {
          setCatchupData(catchupRes.data);
          toast.success(
            language === 'it' 
              ? `Bentornato! Recuperati $${catchupRes.data.catchup_revenue.toLocaleString()} per ${catchupRes.data.hours_missed} ore offline!`
              : `Welcome back! Collected $${catchupRes.data.catchup_revenue.toLocaleString()} for ${catchupRes.data.hours_missed} hours offline!`,
            { duration: 6000 }
          );
          // Refresh user data to update funds
          refreshUser();
        }
        
        const [statsRes, filmsRes, challengesRes, pendingRes] = await Promise.all([
          api.get('/statistics/my'),
          api.get('/films/my/featured?limit=4'),  // Use featured films sorted by attendance
          api.get('/challenges'),
          api.get('/revenue/pending-all')
        ]);
        setStats(statsRes.data);
        setFilms(filmsRes.data);  // Already limited and sorted by backend
        setChallenges(challengesRes.data);
        setPendingRevenue(pendingRes.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
    
    // Setup heartbeat to track activity (every 5 minutes)
    const heartbeatInterval = setInterval(() => {
      api.post('/activity/heartbeat').catch(() => {});
    }, 5 * 60 * 1000);

    // Refresh pending revenue every minute
    const revenueInterval = setInterval(loadPendingRevenue, 60000);
    
    return () => {
      clearInterval(heartbeatInterval);
      clearInterval(revenueInterval);
    };
  }, [api]);

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="dashboard">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-4">
        <h1 className="font-['Bebas_Neue'] text-3xl md:text-4xl mb-1">
          {t('welcome')}, <span className="text-yellow-500">{user?.nickname}</span>
        </h1>
        <p className="text-gray-400 text-sm">{user?.production_house_name}</p>
      </motion.div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-4">
        {[
          { label: 'Films', value: stats?.total_films || 0, icon: Film, color: 'yellow', statType: 'films' },
          { label: 'Revenue', value: `$${((stats?.total_revenue || 0) / 1000000).toFixed(1)}M`, icon: DollarSign, color: 'green', statType: 'revenue' },
          { label: 'Likes', value: stats?.total_likes || 0, icon: Heart, color: 'red', statType: 'likes' },
          { label: 'Quality', value: `${(stats?.average_quality || 0).toFixed(0)}%`, icon: Star, color: 'blue', statType: 'quality' }
        ].map((stat, i) => (
          <Card 
            key={stat.label} 
            className="bg-[#1A1A1A] border-white/5 cursor-pointer hover:border-white/20 transition-colors"
            onClick={() => openStatDetail(stat.statType)}
            data-testid={`stat-card-${stat.statType}`}
          >
            <CardContent className="p-2.5 flex items-center gap-2">
              <stat.icon className={`w-5 h-5 text-${stat.color}-500`} />
              <div>
                <p className="text-lg font-bold">{stat.value}</p>
                <p className="text-xs text-gray-400">{stat.label}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-500 ml-auto" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Collect All Revenue Card */}
      {pendingRevenue && (
        <Card className={`mb-4 border ${pendingRevenue.can_collect ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/10 border-green-500/30' : 'bg-[#1A1A1A] border-white/5'}`}>
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${pendingRevenue.can_collect ? 'bg-green-500' : 'bg-gray-600'}`}>
                  <Wallet className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-['Bebas_Neue'] text-lg">
                    {language === 'it' ? 'INCASSI DA RISCUOTERE' : 'PENDING REVENUE'}
                  </h3>
                  <div className="flex items-center gap-4 text-xs text-gray-400">
                    <span>🎬 Film: ${(pendingRevenue.film_pending || 0).toLocaleString()}</span>
                    <span>🏢 Infra: ${(pendingRevenue.infra_pending || 0).toLocaleString()}</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-xl font-bold ${pendingRevenue.can_collect ? 'text-green-400' : 'text-gray-500'}`}>
                  ${(pendingRevenue.total_pending || 0).toLocaleString()}
                </p>
                <Button 
                  size="sm"
                  disabled={!pendingRevenue.can_collect || collecting}
                  onClick={handleCollectAll}
                  className={pendingRevenue.can_collect 
                    ? 'bg-green-500 hover:bg-green-600 text-white' 
                    : 'bg-gray-700 text-gray-400'
                  }
                  data-testid="collect-all-btn"
                >
                  {collecting ? '...' : (language === 'it' ? 'Riscuoti Tutto' : 'Collect All')}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Financial Overview Card */}
      {stats && (
        <Card className="mb-4 bg-[#1A1A1A] border-white/5">
          <CardContent className="p-3">
            <h3 className="font-['Bebas_Neue'] text-lg mb-2 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              {language === 'it' ? 'BILANCIO FINANZIARIO' : 'FINANCIAL OVERVIEW'}
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-2 bg-red-500/10 rounded-lg border border-red-500/20">
                <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'Speso' : 'Spent'}</p>
                <p className="font-bold text-red-400">
                  ${((stats.total_spent || 0) / 1000000).toFixed(2)}M
                </p>
                <div className="text-[10px] text-gray-500 mt-1">
                  <div>Film: ${((stats.total_film_costs || 0) / 1000000).toFixed(1)}M</div>
                  <div>Infra: ${((stats.total_infra_costs || 0) / 1000000).toFixed(1)}M</div>
                </div>
              </div>
              <div className="text-center p-2 bg-green-500/10 rounded-lg border border-green-500/20">
                <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'Guadagnato' : 'Earned'}</p>
                <p className="font-bold text-green-400">
                  ${((stats.total_earned || 0) / 1000000).toFixed(2)}M
                </p>
                <div className="text-[10px] text-gray-500 mt-1">
                  <div>Film: ${((stats.total_revenue || 0) / 1000000).toFixed(1)}M</div>
                  <div>Infra: ${((stats.total_infra_revenue || 0) / 1000000).toFixed(1)}M</div>
                </div>
              </div>
              <div className={`text-center p-2 rounded-lg border ${(stats.profit_loss || 0) >= 0 ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-orange-500/10 border-orange-500/20'}`}>
                <p className="text-xs text-gray-400 mb-1">{language === 'it' ? 'Profitto/Perdita' : 'Profit/Loss'}</p>
                <p className={`font-bold ${(stats.profit_loss || 0) >= 0 ? 'text-emerald-400' : 'text-orange-400'}`}>
                  {(stats.profit_loss || 0) >= 0 ? '+' : ''}${((stats.profit_loss || 0) / 1000000).toFixed(2)}M
                </p>
                <div className="text-[10px] text-gray-500 mt-1 flex items-center justify-center gap-1">
                  {(stats.profit_loss || 0) >= 0 ? (
                    <><TrendingUp className="w-3 h-3 text-emerald-400" /> {language === 'it' ? 'In Profitto' : 'Profitable'}</>
                  ) : (
                    <><TrendingDown className="w-3 h-3 text-orange-400" /> {language === 'it' ? 'In Perdita' : 'In Loss'}</>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-3 gap-2 mb-4">
        {[
          { label: 'Like', value: (stats?.likeability_score || 50).toFixed(0), icon: Heart, color: 'pink' },
          { label: 'Social', value: (stats?.interaction_score || 50).toFixed(0), icon: Users, color: 'blue' },
          { label: 'Char', value: (stats?.character_score || 50).toFixed(0), icon: Star, color: 'yellow' }
        ].map(s => (
          <Card key={s.label} className="bg-[#1A1A1A] border-white/5">
            <CardContent className="p-2 text-center">
              <s.icon className={`w-4 h-4 mx-auto mb-1 text-${s.color}-500`} />
              <p className="text-base font-bold">{s.value}</p>
              <p className="text-xs text-gray-400">{s.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
        <Card className="bg-gradient-to-br from-red-500/20 to-red-600/5 border-red-500/20 cursor-pointer" onClick={() => navigate('/festivals')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-red-500 rounded-lg"><Award className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Festival' : 'Festivals'}</h3><p className="text-xs text-gray-400">{language === 'it' ? 'Premi cinema' : 'Awards'}</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border-yellow-500/20 cursor-pointer" onClick={() => navigate('/create')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-yellow-500 rounded-lg"><Plus className="w-5 h-5 text-black" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{t('create_film')}</h3><p className="text-xs text-gray-400">New blockbuster</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-500/20 to-orange-600/5 border-orange-500/20 cursor-pointer" onClick={() => navigate('/pre-engagement')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-orange-500 rounded-lg"><Users className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Pre-Ingaggio' : 'Pre-Engage'}</h3><p className="text-xs text-gray-400">{language === 'it' ? 'Ingaggia cast' : 'Engage cast'}</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/5 border-blue-500/20 cursor-pointer" onClick={() => navigate('/games')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-blue-500 rounded-lg"><Gamepad2 className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{t('mini_games')}</h3><p className="text-xs text-gray-400">Earn rewards</p></div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-500/20 to-purple-600/5 border-purple-500/20 cursor-pointer" onClick={() => navigate('/social')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-purple-500 rounded-lg"><Globe className="w-5 h-5 text-white" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{t('social')}</h3><p className="text-xs text-gray-400">Explore films</p></div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-[#1A1A1A] border-white/5 mb-4">
        <CardHeader className="pb-2 pt-3 px-3">
          <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
            <Trophy className="w-4 h-4 text-yellow-500" /> {t('challenges')}
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3">
          <Tabs defaultValue="daily">
            <TabsList className="h-7 mb-2"><TabsTrigger value="daily" className="text-xs h-6 px-2">{t('daily')}</TabsTrigger><TabsTrigger value="weekly" className="text-xs h-6 px-2">{t('weekly')}</TabsTrigger></TabsList>
            <TabsContent value="daily" className="mt-0">
              <div className="space-y-1.5">{challenges.daily.slice(0, 3).map(c => (
                <div key={c.id} className="flex items-center justify-between p-1.5 rounded bg-white/5">
                  <div><p className="text-xs font-semibold">{c.name}</p><p className="text-xs text-gray-400">{c.current}/{c.target}</p></div>
                  <p className="text-xs text-yellow-500">${c.reward.toLocaleString()}</p>
                </div>
              ))}</div>
            </TabsContent>
            <TabsContent value="weekly" className="mt-0">
              <div className="space-y-1.5">{challenges.weekly.slice(0, 3).map(c => (
                <div key={c.id} className="flex items-center justify-between p-1.5 rounded bg-white/5">
                  <div><p className="text-xs font-semibold">{c.name}</p><p className="text-xs text-gray-400">{c.current}/{c.target}</p></div>
                  <p className="text-xs text-yellow-500">${c.reward.toLocaleString()}</p>
                </div>
              ))}</div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {films.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-['Bebas_Neue'] text-xl">{t('my_films')}</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/films')} className="h-7 text-xs">View All <ChevronRight className="w-3 h-3 ml-1" /></Button>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            {films.map(film => (
              <Card key={film.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden cursor-pointer" onClick={() => navigate(`/films/${film.id}`)}>
                <div className="aspect-[2/3] relative">
                  <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} alt={film.title} className="w-full h-full object-cover" />
                  {film.is_sequel && (
                    <div className="absolute top-1 right-1 bg-purple-600/90 text-white text-[8px] px-1.5 py-0.5 rounded font-bold">
                      SEQUEL #{film.sequel_number || 2}
                    </div>
                  )}
                </div>
                <CardContent className="p-2">
                  <h3 className="font-semibold text-xs truncate">
                    {film.title}{film.subtitle && <span className="text-gray-400">: {film.subtitle}</span>}
                  </h3>
                  <div className="flex justify-between mt-1 text-xs text-gray-400"><span><Heart className="w-2.5 h-2.5 inline" /> {film.likes_count}</span><span className="text-green-400">${(film.total_revenue || 0).toLocaleString()}</span></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
      
      {/* Stats Detail Modal */}
      <StatsDetailModal
        isOpen={showStatsDetail}
        onClose={() => setShowStatsDetail(false)}
        statType={selectedStatType}
        api={api}
      />
    </div>
  );
};

// Mini Games Page with REAL Questions
const MiniGamesPage = () => {
  const { api, refreshUser } = useContext(AuthContext);
  const { t } = useTranslations();
  const [games, setGames] = useState([]);
  const [challenges, setChallenges] = useState({ daily: [], weekly: [] });
  const [currentGame, setCurrentGame] = useState(null);
  const [gameSession, setGameSession] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState([]);
  const [gameResult, setGameResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      const [gamesRes, challengesRes] = await Promise.all([api.get('/minigames'), api.get('/challenges')]);
      setGames(gamesRes.data);
      setChallenges(challengesRes.data);
    };
    fetchData();
  }, [api]);

  const startGame = async (game) => {
    setLoading(true);
    try {
      const res = await api.post(`/minigames/${game.id}/start`);
      setCurrentGame(game);
      setGameSession(res.data);
      setCurrentQuestionIndex(0);
      setSelectedAnswers([]);
      setGameResult(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Cannot start game');
    } finally {
      setLoading(false);
    }
  };

  const selectAnswer = (answer) => {
    const newAnswers = [...selectedAnswers];
    newAnswers[currentQuestionIndex] = { question_index: currentQuestionIndex, answer };
    setSelectedAnswers(newAnswers);
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < gameSession.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const submitGame = async () => {
    setLoading(true);
    try {
      const res = await api.post('/minigames/submit', {
        game_id: currentGame.id,
        session_id: gameSession.session_id,
        answers: selectedAnswers
      });
      setGameResult(res.data);
      refreshUser();
    } catch (err) {
      toast.error('Failed to submit game');
    } finally {
      setLoading(false);
    }
  };

  const closeGame = () => {
    setCurrentGame(null);
    setGameSession(null);
    setGameResult(null);
    setSelectedAnswers([]);
    setCurrentQuestionIndex(0);
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="minigames-page">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4">{t('mini_games')}</h1>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        {games.map(game => (
          <Card key={game.id} className="bg-[#1A1A1A] border-white/5">
            <CardContent className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-2 bg-yellow-500/20 rounded-lg"><Gamepad2 className="w-5 h-5 text-yellow-500" /></div>
                <div><h3 className="font-semibold text-sm">{game.name}</h3><p className="text-xs text-gray-400">{game.description}</p></div>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-gray-400">Reward:</span>
                <span className="text-sm text-yellow-500">${game.reward_min.toLocaleString()} - ${game.reward_max.toLocaleString()}</span>
              </div>
              <Button onClick={() => startGame(game)} disabled={loading} className="w-full h-8 bg-yellow-500 text-black hover:bg-yellow-400 text-sm">
                Play Now
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Game Modal */}
      <Dialog open={!!gameSession} onOpenChange={() => !loading && closeGame()}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl">{currentGame?.name}</DialogTitle>
          </DialogHeader>
          
          {!gameResult ? (
            <div className="space-y-4">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Question {currentQuestionIndex + 1} of {gameSession?.questions?.length}</span>
                <span>{selectedAnswers.filter(Boolean).length} answered</span>
              </div>
              <Progress value={((currentQuestionIndex + 1) / (gameSession?.questions?.length || 1)) * 100} className="h-1.5" />
              
              {gameSession?.questions?.[currentQuestionIndex] && (
                <div className="space-y-3">
                  <p className="font-semibold">{gameSession.questions[currentQuestionIndex].question}</p>
                  <RadioGroup 
                    value={selectedAnswers[currentQuestionIndex]?.answer || ''} 
                    onValueChange={selectAnswer}
                  >
                    {gameSession.questions[currentQuestionIndex].options.map((option, i) => (
                      <div key={i} className="flex items-center space-x-2 p-2 rounded border border-white/10 hover:border-yellow-500/50 cursor-pointer">
                        <RadioGroupItem value={option} id={`option-${i}`} />
                        <Label htmlFor={`option-${i}`} className="cursor-pointer flex-1 text-sm">{option}</Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>
              )}
              
              <div className="flex gap-2">
                {currentQuestionIndex < (gameSession?.questions?.length || 0) - 1 ? (
                  <Button onClick={nextQuestion} disabled={!selectedAnswers[currentQuestionIndex]} className="flex-1 bg-yellow-500 text-black">Next</Button>
                ) : (
                  <Button onClick={submitGame} disabled={loading || selectedAnswers.length < (gameSession?.questions?.length || 0)} className="flex-1 bg-green-500 hover:bg-green-400">Submit Answers</Button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-center py-4">
                <div className={`text-5xl mb-2 ${gameResult.score_percentage >= 60 ? 'text-green-500' : 'text-red-500'}`}>
                  {gameResult.score_percentage}%
                </div>
                <p className="text-gray-400">{gameResult.correct_answers} / {gameResult.total_questions} correct</p>
                <p className="text-2xl font-bold text-yellow-500 mt-2">+${gameResult.reward.toLocaleString()}</p>
              </div>
              
              <ScrollArea className="h-48">
                <div className="space-y-2">
                  {gameResult.results.map((r, i) => (
                    <div key={i} className={`p-2 rounded border ${r.is_correct ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'}`}>
                      <p className="text-xs font-semibold mb-1">{r.question}</p>
                      <div className="flex items-center gap-1 text-xs">
                        {r.is_correct ? <Check className="w-3 h-3 text-green-500" /> : <XCircle className="w-3 h-3 text-red-500" />}
                        <span>Your answer: {r.your_answer}</span>
                      </div>
                      {!r.is_correct && <p className="text-xs text-green-400 mt-1">Correct: {r.correct_answer}</p>}
                    </div>
                  ))}
                </div>
              </ScrollArea>
              
              <Button onClick={closeGame} className="w-full">Close</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <h2 className="font-['Bebas_Neue'] text-2xl mb-3 flex items-center gap-2"><Trophy className="w-5 h-5 text-yellow-500" /> {t('challenges')}</h2>
      <Tabs defaultValue="daily">
        <TabsList><TabsTrigger value="daily">{t('daily')}</TabsTrigger><TabsTrigger value="weekly">{t('weekly')}</TabsTrigger></TabsList>
        <TabsContent value="daily"><div className="grid gap-2">{challenges.daily.map(c => (
          <Card key={c.id} className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3 flex justify-between items-center">
            <div><h4 className="font-semibold text-sm">{c.name}</h4><p className="text-xs text-gray-400">{c.description}</p><Progress value={(c.current / c.target) * 100} className="h-1.5 mt-1 w-32" /></div>
            <p className="text-yellow-500 font-bold">${c.reward.toLocaleString()}</p>
          </CardContent></Card>
        ))}</div></TabsContent>
        <TabsContent value="weekly"><div className="grid gap-2">{challenges.weekly.map(c => (
          <Card key={c.id} className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3 flex justify-between items-center">
            <div><h4 className="font-semibold text-sm">{c.name}</h4><p className="text-xs text-gray-400">{c.description}</p><Progress value={(c.current / c.target) * 100} className="h-1.5 mt-1 w-32" /></div>
            <p className="text-yellow-500 font-bold">${c.reward.toLocaleString()}</p>
          </CardContent></Card>
        ))}</div></TabsContent>
      </Tabs>
    </div>
  );
};

// Film Wizard - simplified
const FilmWizard = () => {
  const { api, user, updateFunds } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [sponsors, setSponsors] = useState([]);
  const [locations, setLocations] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [screenwriters, setScreenwriters] = useState([]);
  const [directors, setDirectors] = useState([]);
  const [actors, setActors] = useState([]);
  const [composers, setComposers] = useState([]);
  const [genres, setGenres] = useState({});
  const [actorRoles, setActorRoles] = useState([]);
  const [resumedDraftId, setResumedDraftId] = useState(null);
  
  // New states for cast filtering
  const [castCategories, setCastCategories] = useState([]);
  const [availableSkills, setAvailableSkills] = useState({
    screenwriters: [], directors: [], actors: [], composers: []
  });
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSkill, setSelectedSkill] = useState('all');
  const [skillSearchQuery, setSkillSearchQuery] = useState('');
  
  // Rejection system states
  const [refusedIds, setRefusedIds] = useState(new Set());
  const [rejectionModal, setRejectionModal] = useState(null);
  const [checkingOffer, setCheckingOffer] = useState(null);
  
  // Pre-engagement states
  const [preEngagedCast, setPreEngagedCast] = useState(null);
  const [preFilmId, setPreFilmId] = useState(null);
  const [dismissModal, setDismissModal] = useState(null);

  const [filmData, setFilmData] = useState({
    title: '', subtitle: '', genre: 'action', subgenres: [], release_date: new Date().toISOString().split('T')[0],
    weeks_in_theater: 4, sponsor_id: null, equipment_package: 'Standard', locations: [], location_days: {},
    screenwriter_id: '', director_id: '', composer_id: '', actors: [], extras_count: 50, extras_cost: 50000,
    screenplay: '', screenplay_source: 'manual', screenplay_prompt: '', 
    soundtrack_prompt: '', soundtrack_description: '',
    poster_url: '', poster_prompt: '', ad_duration_seconds: 0, ad_revenue: 0,
    is_sequel: false, sequel_parent_id: null
  });
  const [myFilmsForSequel, setMyFilmsForSequel] = useState([]);
  const [releaseDate, setReleaseDate] = useState(new Date());
  const steps = [{num:1,title:'Title'},{num:2,title:'Sponsor'},{num:3,title:'Equipment'},{num:4,title:'Writer'},{num:5,title:'Director'},{num:6,title:'Composer'},{num:7,title:'Cast'},{num:8,title:'Script'},{num:9,title:'Soundtrack'},{num:10,title:'Poster'},{num:11,title:'Ads'},{num:12,title:'Review'}];

  // Function to save draft (pause)
  const saveDraft = async (reason = 'paused') => {
    setSavingDraft(true);
    try {
      const draftData = {
        ...filmData,
        current_step: step,
        paused_reason: reason
      };
      const res = await api.post('/films/drafts', draftData);
      toast.success(language === 'it' ? 'Bozza salvata! Puoi riprendere dalla pagina "Film Incompleti"' : 'Draft saved! You can resume from "Incomplete Films"');
      if (reason === 'paused') {
        navigate('/drafts');
      }
    } catch (e) {
      toast.error(language === 'it' ? 'Errore nel salvataggio della bozza' : 'Error saving draft');
    } finally {
      setSavingDraft(false);
    }
  };
  
  // Load draft from URL params or localStorage
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const draftId = params.get('draft');
    if (draftId) {
      loadDraft(draftId);
    }
  }, []);
  
  const loadDraft = async (draftId) => {
    try {
      const res = await api.get(`/films/drafts/${draftId}`);
      const draft = res.data;
      setFilmData({
        title: draft.title || '',
        genre: draft.genre || 'action',
        subgenres: draft.subgenres || [],
        release_date: draft.release_date || new Date().toISOString().split('T')[0],
        weeks_in_theater: draft.weeks_in_theater || 4,
        sponsor_id: draft.sponsor_id,
        equipment_package: draft.equipment_package || 'Standard',
        locations: draft.locations || [],
        location_days: draft.location_days || {},
        screenwriter_id: draft.screenwriter_id || '',
        director_id: draft.director_id || '',
        composer_id: draft.composer_id || '',
        actors: draft.actors || [],
        extras_count: draft.extras_count || 50,
        extras_cost: draft.extras_cost || 50000,
        screenplay: draft.screenplay || '',
        screenplay_source: draft.screenplay_source || 'manual',
        screenplay_prompt: draft.screenplay_prompt || '',
        soundtrack_prompt: draft.soundtrack_prompt || '',
        soundtrack_description: draft.soundtrack_description || '',
        poster_url: draft.poster_url || '',
        poster_prompt: draft.poster_prompt || '',
        ad_duration_seconds: draft.ad_duration_seconds || 0,
        ad_revenue: draft.ad_revenue || 0
      });
      setStep(draft.current_step || 1);
      setResumedDraftId(draftId);
      
      // Check if this draft comes from a pre-film
      if (draft.from_pre_film && draft.pre_film_id) {
        setPreFilmId(draft.pre_film_id);
        setPreEngagedCast(draft.pre_engaged_cast || null);
        
        // Pre-fill cast IDs from pre-engaged cast
        const preCast = draft.pre_engaged_cast || {};
        if (preCast.screenwriter?.id) {
          setFilmData(prev => ({...prev, screenwriter_id: preCast.screenwriter.id}));
        }
        if (preCast.director?.id) {
          setFilmData(prev => ({...prev, director_id: preCast.director.id}));
        }
        if (preCast.composer?.id) {
          setFilmData(prev => ({...prev, composer_id: preCast.composer.id}));
        }
        if (preCast.actors?.length > 0) {
          setFilmData(prev => ({
            ...prev, 
            actors: preCast.actors.map(a => ({
              id: a.id,
              role: 'Lead',
              fee: a.offered_fee
            }))
          }));
        }
        
        toast.info(language === 'it' 
          ? 'Cast pre-ingaggiato caricato. Puoi mantenerlo o congedarlo (con penale).'
          : 'Pre-engaged cast loaded. You can keep or dismiss them (with penalty).');
      }
      
      toast.success(language === 'it' ? 'Bozza caricata!' : 'Draft loaded!');
    } catch (e) {
      toast.error(language === 'it' ? 'Errore nel caricamento della bozza' : 'Error loading draft');
    }
  };

  // Auto-save every 30 seconds
  const [lastAutoSave, setLastAutoSave] = useState(null);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  
  useEffect(() => {
    if (!autoSaveEnabled || !filmData.title) return;
    
    const autoSaveInterval = setInterval(async () => {
      // Only auto-save if there's meaningful data
      if (filmData.title || filmData.genre !== 'action' || filmData.screenplay || filmData.actors.length > 0) {
        try {
          const draftData = {
            ...filmData,
            current_step: step,
            paused_reason: 'autosave'
          };
          await api.post('/films/drafts', draftData);
          setLastAutoSave(new Date());
          // Silent save - no toast to avoid spam
        } catch (e) {
          // Silent fail for auto-save
          console.log('Auto-save failed:', e);
        }
      }
    }, 30000); // 30 seconds
    
    return () => clearInterval(autoSaveInterval);
  }, [filmData, step, autoSaveEnabled, api]);

  // Save before page unload
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (filmData.title || filmData.screenplay || filmData.actors.length > 0) {
        // Try to save draft synchronously (best effort)
        const draftData = {
          ...filmData,
          current_step: step,
          paused_reason: 'browser_close'
        };
        // Use sendBeacon for reliable save on page close
        const blob = new Blob([JSON.stringify(draftData)], { type: 'application/json' });
        navigator.sendBeacon?.(`${api.defaults.baseURL}/films/drafts`, blob);
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [filmData, step, api]);

  useEffect(() => { 
    api.get('/sponsors').then(r=>setSponsors(r.data)); 
    api.get('/locations').then(r=>setLocations(r.data)); 
    api.get('/equipment').then(r=>setEquipment(r.data));
    api.get('/genres').then(r=>setGenres(r.data));
    api.get('/actor-roles').then(r=>setActorRoles(r.data));
    api.get('/films/my/for-sequel').then(r=>setMyFilmsForSequel(r.data.films || [])).catch(()=>{});
  }, [api]);
  
  const fetchPeople = async (type, category = '', skill = '') => {
    let url = `/${type}?limit=200`;
    if (category && category !== 'all') url += `&category=${category}`;
    if (skill && skill !== 'all') url += `&skill=${skill}`;
    
    const res = await api.get(url);
    if(type==='screenwriters') {
      setScreenwriters(res.data.screenwriters);
      setAvailableSkills(prev => ({...prev, screenwriters: res.data.available_skills || []}));
    }
    else if(type==='directors') {
      setDirectors(res.data.directors);
      setAvailableSkills(prev => ({...prev, directors: res.data.available_skills || []}));
    }
    else if(type==='actors') {
      setActors(res.data.actors);
      setAvailableSkills(prev => ({...prev, actors: res.data.available_skills || []}));
    }
    else if(type==='composers') {
      setComposers(res.data.composers);
      setAvailableSkills(prev => ({...prev, composers: res.data.available_skills || []}));
    }
    if (res.data.categories) setCastCategories(res.data.categories);
  };
  
  useEffect(() => { 
    if(step===4) { fetchPeople('screenwriters', selectedCategory, selectedSkill); }
    if(step===5) { fetchPeople('directors', selectedCategory, selectedSkill); }
    if(step===6) { fetchPeople('composers', selectedCategory, selectedSkill); }
    if(step===7) { fetchPeople('actors', selectedCategory, selectedSkill); }
  }, [step, selectedCategory, selectedSkill]);
  
  // Reset filters when changing steps
  useEffect(() => {
    setSelectedCategory('all');
    setSelectedSkill('all');
    setSkillSearchQuery('');
  }, [step]);

  const generateScreenplay = async () => { 
    setGenerating(true); 
    try { 
      const res = await api.post('/ai/screenplay', { genre: filmData.genre, title: filmData.title, language, tone: 'dramatic', length: 'medium', custom_prompt: filmData.screenplay_prompt }); 
      setFilmData({...filmData, screenplay: res.data.screenplay, screenplay_source: 'ai'}); 
      toast.success(language === 'it' ? 'Sceneggiatura generata!' : 'Screenplay generated!'); 
    } catch(e) { 
      console.error('Screenplay generation error:', e);
      toast.error(language === 'it' ? 'Errore generazione sceneggiatura. Riprova.' : 'Screenplay generation error. Try again.'); 
    } finally { 
      setGenerating(false); 
    }
  };
  const generatePoster = async () => { 
    setGenerating(true); 
    try { 
      const res = await api.post('/ai/poster', { title: filmData.title, genre: filmData.genre, description: filmData.poster_prompt || filmData.title, style: 'cinematic' }); 
      if (res.data.poster_url && res.data.poster_url.startsWith('data:')) {
        setFilmData({...filmData, poster_url: res.data.poster_url}); 
        toast.success(language === 'it' ? 'Locandina generata!' : 'Poster generated!'); 
      } else {
        toast.error(language === 'it' ? 'Generazione fallita, riprova' : 'Generation failed, try again');
      }
    } catch(e) { 
      console.error('Poster generation error:', e);
      toast.error(language === 'it' ? 'Errore generazione locandina. Riprova.' : 'Poster generation error. Try again.'); 
    } finally { 
      setGenerating(false); 
    }
  };
  const generateSoundtrack = async () => { 
    setGenerating(true); 
    try { 
      const res = await api.post('/ai/soundtrack-description', { title: filmData.title, genre: filmData.genre, mood: 'epic', custom_prompt: filmData.soundtrack_prompt, language }); 
      setFilmData({...filmData, soundtrack_description: res.data.description}); 
      toast.success(language === 'it' ? 'Descrizione colonna sonora generata!' : 'Soundtrack description generated!'); 
    } catch(e) { 
      console.error('Soundtrack generation error:', e);
      toast.error(language === 'it' ? 'Errore generazione. Riprova.' : 'Generation error. Try again.'); 
    } finally { 
      setGenerating(false); 
    }
  };
  
  // Load rejections on mount
  useEffect(() => {
    api.get('/cast/rejections').then(r => {
      setRefusedIds(new Set(r.data.refused_ids || []));
    }).catch(() => {});
  }, [api]);
  
  // Function to make an offer to a cast member
  const makeOffer = async (person, personType, onAccept) => {
    // If already refused, don't allow clicking
    if (refusedIds.has(person.id)) {
      return;
    }
    
    setCheckingOffer(person.id);
    
    try {
      const res = await api.post('/cast/offer', {
        person_id: person.id,
        person_type: personType,
        film_genre: filmData.genre
      });
      
      if (res.data.accepted) {
        // Accepted! Proceed with selection
        onAccept();
        toast.success(res.data.message);
      } else {
        // Refused!
        setRefusedIds(prev => new Set([...prev, person.id]));
        setRejectionModal({
          name: res.data.person_name,
          type: res.data.person_type,
          reason: res.data.reason,
          stars: res.data.stars,
          fame: res.data.fame,
          alreadyRefused: res.data.already_refused
        });
      }
    } catch (e) {
      toast.error('Errore nella comunicazione');
      // On error, allow selection anyway
      onAccept();
    } finally {
      setCheckingOffer(null);
    }
  };
  
  const calculateBudget = () => { const eq = equipment.find(e=>e.name===filmData.equipment_package)||{cost:0}; let loc=0; filmData.locations.forEach(l=>{const lo=locations.find(x=>x.name===l); if(lo)loc+=lo.cost_per_day*(filmData.location_days[l]||7);}); return eq.cost+loc+filmData.extras_cost; };
  const getSponsorBudget = () => { if(!filmData.sponsor_id)return 0; const s=sponsors.find(x=>x.name===filmData.sponsor_id); return s?.budget_offer||0; };
  
  // Tier popup state
  const [tierPopup, setTierPopup] = useState(null);
  
  const TIER_STYLES = {
    masterpiece: { bg: 'from-yellow-500/30 to-amber-500/30', border: 'border-yellow-500', text: 'text-yellow-400', emoji: '🏆' },
    epic: { bg: 'from-purple-500/30 to-pink-500/30', border: 'border-purple-500', text: 'text-purple-400', emoji: '⭐' },
    excellent: { bg: 'from-blue-500/30 to-cyan-500/30', border: 'border-blue-500', text: 'text-blue-400', emoji: '✨' },
    promising: { bg: 'from-green-500/30 to-emerald-500/30', border: 'border-green-500', text: 'text-green-400', emoji: '🌟' },
    flop: { bg: 'from-red-500/30 to-orange-500/30', border: 'border-red-500', text: 'text-red-400', emoji: '💔' },
    normal: { bg: 'from-gray-500/30 to-slate-500/30', border: 'border-gray-500', text: 'text-gray-400', emoji: '🎬' }
  };
  
  const handleSubmit = async () => { 
    setLoading(true); 
    try { 
      const res = await api.post('/films', {...filmData, release_date: releaseDate.toISOString()}); 
      
      // Check if film got a special tier
      const tier = res.data.film_tier || 'normal';
      const tierStyle = TIER_STYLES[tier] || TIER_STYLES.normal;
      
      if (tier !== 'normal') {
        // Show tier popup for special tiers
        setTierPopup({
          tier: tier,
          style: tierStyle,
          filmTitle: res.data.title,
          opening: res.data.opening_day_revenue,
          tierName: tier === 'masterpiece' ? 'Capolavoro' : 
                   tier === 'epic' ? 'Epico' : 
                   tier === 'excellent' ? 'Eccellente' : 
                   tier === 'promising' ? 'Promettente' : 
                   tier === 'flop' ? 'Possibile Flop' : 'Standard',
          message: tier === 'flop' 
            ? 'Non preoccuparti! A volte i flop diventano cult...' 
            : 'Il pubblico è entusiasta!',
          filmId: res.data.id
        });
      } else {
        toast.success(`Film created! Opening: $${res.data.opening_day_revenue.toLocaleString()}`);
        navigate(`/films/${res.data.id}`);
      }
      
      updateFunds(user.funds - calculateBudget() + getSponsorBudget() + filmData.ad_revenue + res.data.opening_day_revenue); 
    } catch(e) { 
      toast.error(e.response?.data?.detail||'Failed'); 
    } finally { 
      setLoading(false); 
    }
  };

  const getRoleName = (roleId) => {
    const role = actorRoles.find(r => r.id === roleId);
    if (!role) return roleId;
    const langKey = `name_${language}`;
    return role[langKey] || role.name;
  };

  // Check if a cast member is pre-engaged
  const isPreEngaged = (castType, castId) => {
    if (!preEngagedCast) return false;
    if (castType === 'actor') {
      return preEngagedCast.actors?.some(a => a.id === castId);
    }
    return preEngagedCast[castType]?.id === castId;
  };

  // Get pre-engaged cast info
  const getPreEngagedInfo = (castType, castId) => {
    if (!preEngagedCast) return null;
    if (castType === 'actor') {
      return preEngagedCast.actors?.find(a => a.id === castId);
    }
    return preEngagedCast[castType];
  };

  // Handle dismissing pre-engaged cast
  const handleDismissCast = async (castType, castId) => {
    if (!preFilmId) return;
    
    try {
      const res = await api.post(`/pre-films/${preFilmId}/dismiss-cast?cast_type=${castType}&cast_id=${castId}`);
      setDismissModal({
        castType,
        castId,
        ...res.data
      });
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  // Confirm dismissal
  const confirmDismissal = async () => {
    if (!dismissModal || !preFilmId) return;
    
    try {
      // Actually release the cast
      await api.post(`/pre-films/${preFilmId}/release`, {
        pre_film_id: preFilmId,
        cast_type: dismissModal.castType,
        cast_id: dismissModal.castId
      });
      
      toast.success(`${dismissModal.cast_name} ${language === 'it' ? 'congedato' : 'dismissed'}`);
      
      // Update local state
      if (dismissModal.castType === 'screenwriter') {
        setFilmData(prev => ({...prev, screenwriter_id: ''}));
      } else if (dismissModal.castType === 'director') {
        setFilmData(prev => ({...prev, director_id: ''}));
      } else if (dismissModal.castType === 'composer') {
        setFilmData(prev => ({...prev, composer_id: ''}));
      } else if (dismissModal.castType === 'actor') {
        setFilmData(prev => ({
          ...prev,
          actors: prev.actors.filter(a => a.id !== dismissModal.castId)
        }));
      }
      
      // Update pre-engaged cast state
      setPreEngagedCast(prev => {
        if (!prev) return prev;
        if (dismissModal.castType === 'actor') {
          return {...prev, actors: prev.actors.filter(a => a.id !== dismissModal.castId)};
        }
        return {...prev, [dismissModal.castType]: null};
      });
      
      setDismissModal(null);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const PersonCard = ({ person, isSelected, onSelect, showRoleSelect = false, currentRole = null, onRoleChange = null, roleType = 'actor' }) => {
    const isRefused = refusedIds.has(person.id);
    const isChecking = checkingOffer === person.id;
    
    // Generate star display
    const renderStars = (count) => {
      return Array(5).fill(0).map((_, i) => (
        <Star key={i} className={`w-2.5 h-2.5 ${i < count ? 'fill-yellow-500 text-yellow-500' : 'text-gray-600'}`} />
      ));
    };
    
    const getFameColor = (category) => {
      switch(category) {
        case 'superstar': return 'text-purple-400 bg-purple-500/20';
        case 'famous': return 'text-yellow-400 bg-yellow-500/20';
        case 'rising': return 'text-blue-400 bg-blue-500/20';
        case 'known': return 'text-green-400 bg-green-500/20';
        default: return 'text-gray-400 bg-gray-500/20';
      }
    };
    
    const getCategoryColor = (category) => {
      switch(category) {
        case 'recommended': return 'text-emerald-400 bg-emerald-500/20';
        case 'star': return 'text-purple-400 bg-purple-500/20';
        case 'known': return 'text-blue-400 bg-blue-500/20';
        case 'emerging': return 'text-orange-400 bg-orange-500/20';
        case 'unknown': return 'text-gray-400 bg-gray-500/20';
        default: return 'text-gray-400 bg-gray-500/20';
      }
    };
    
    const getCategoryName = (category) => {
      const names = {
        recommended: language === 'it' ? 'Consigliato' : 'Recommended',
        star: 'Star',
        known: language === 'it' ? 'Conosciuto' : 'Known',
        emerging: language === 'it' ? 'Emergente' : 'Emerging',
        unknown: language === 'it' ? 'Sconosciuto' : 'Unknown'
      };
      return names[category] || category;
    };
    
    // Get primary skills display
    const primarySkillsDisplay = person.primary_skills_translated || person.primary_skills || [];
    const secondarySkillDisplay = person.secondary_skill_translated || person.secondary_skill;
    
    // Handle click with offer system
    const handleClick = () => {
      if (isRefused || isChecking) return;
      makeOffer(person, roleType, onSelect);
    };
    
    return (
      <Card 
        className={`border-2 transition-all ${
          isRefused 
            ? 'bg-red-950/30 border-red-500/30 cursor-not-allowed opacity-60' 
            : isChecking
              ? 'bg-[#1A1A1A] border-yellow-500/50 animate-pulse cursor-wait'
              : isSelected 
                ? 'bg-[#1A1A1A] border-yellow-500 ring-1 ring-yellow-500/50 cursor-pointer' 
                : 'bg-[#1A1A1A] border-white/10 hover:border-white/20 cursor-pointer'
        }`} 
        onClick={handleClick}
      >
        <CardContent className="p-2 relative">
          {/* Refused overlay */}
          {isRefused && (
            <div className="absolute top-1 right-1 z-10">
              <Badge className="bg-red-500/80 text-white text-[8px] flex items-center gap-1">
                <XCircle className="w-2.5 h-2.5" />
                {language === 'it' ? 'Ha rifiutato' : 'Refused'}
              </Badge>
            </div>
          )}
          
          {/* Loading overlay */}
          {isChecking && (
            <div className="absolute inset-0 bg-black/30 flex items-center justify-center z-10 rounded-lg">
              <div className="text-xs text-yellow-400 animate-pulse">
                {language === 'it' ? 'Contattando...' : 'Contacting...'}
              </div>
            </div>
          )}
          
          {/* Header: Avatar, Name, Cost */}
          <div className="flex items-start gap-2 mb-1.5">
            <Avatar className="w-10 h-10 flex-shrink-0"><AvatarImage src={person.avatar_url} /><AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xs">{person.name[0]}</AvatarFallback></Avatar>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1 flex-wrap">
                <h4 className="font-semibold text-xs truncate max-w-[100px]">{person.name}</h4>
                <span className="text-[10px] text-gray-400">{person.gender === 'female' ? '♀' : '♂'}</span>
                {person.is_hidden_gem && <Sparkles className="w-2.5 h-2.5 text-green-500" title="Hidden Gem!" />}
                {person.has_worked_with_us && (
                  <Badge className="text-[8px] h-3.5 px-1 bg-cyan-500/20 text-cyan-400 whitespace-nowrap">
                    {language === 'it' ? 'Ha lavorato con noi' : 'Worked with us'}
                  </Badge>
                )}
              </div>
              {/* Primary & Secondary Skills inline */}
              <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                {primarySkillsDisplay.slice(0, 2).map((skill, idx) => (
                  <span key={idx} className="text-[9px] text-yellow-400 bg-yellow-500/10 px-1 py-0.5 rounded">
                    {skill}
                  </span>
                ))}
                {secondarySkillDisplay && (
                  <span className="text-[9px] text-gray-400 bg-white/5 px-1 py-0.5 rounded">
                    {secondarySkillDisplay}
                  </span>
                )}
              </div>
              <p className="text-[10px] text-gray-400 mt-0.5">{person.nationality} • {person.age}yo • {person.years_active}y exp</p>
            </div>
            <p className="text-yellow-500 font-bold text-xs whitespace-nowrap">${((person.cost_per_film || 0)/1000).toFixed(0)}K</p>
          </div>
          
          {/* Stars, Category row */}
          <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
            {person.stars && (
              <div className="flex items-center gap-0.5" title={`${person.stars} stelle`}>
                {renderStars(person.stars)}
              </div>
            )}
            {person.category && (
              <Badge className={`text-[8px] h-4 px-1 ${getCategoryColor(person.category)}`}>
                {person.category_translated || getCategoryName(person.category)}
              </Badge>
            )}
            {person.fame_category && (
              <Badge className={`text-[8px] h-4 px-1 ${getFameColor(person.fame_category)}`}>
                {person.fame_category === 'superstar' ? 'Superstar' : 
                 person.fame_category === 'famous' ? (language === 'it' ? 'Famoso' : 'Famous') : 
                 person.fame_category === 'rising' ? (language === 'it' ? 'In Ascesa' : 'Rising') : 
                 person.fame_category === 'known' ? (language === 'it' ? 'Noto' : 'Known') : 
                 (language === 'it' ? 'Sconosciuto' : 'Unknown')}
              </Badge>
            )}
          </div>
          
          {/* Skills grid - show only 4 */}
          <div className="grid grid-cols-2 gap-0.5">
            {Object.entries(person.skills||{}).slice(0,4).map(([s,v])=><SkillBadge key={s} name={s} value={v} change={person.skill_changes?.[s]||0} language={language} />)}
          </div>
          
          {showRoleSelect && isSelected && (
            <div className="mt-2 pt-2 border-t border-white/10" onClick={e => e.stopPropagation()}>
              <Select value={currentRole} onValueChange={onRoleChange}>
                <SelectTrigger className="h-7 text-xs bg-black/20 border-white/10">
                  <SelectValue placeholder="Select role..." />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A]">
                  {actorRoles.map(r => (
                    <SelectItem key={r.id} value={r.id} className="text-xs">{getRoleName(r.id)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const toggleSubgenre = (subgenre) => {
    if (filmData.subgenres.includes(subgenre)) {
      setFilmData({...filmData, subgenres: filmData.subgenres.filter(s => s !== subgenre)});
    } else if (filmData.subgenres.length < 3) {
      setFilmData({...filmData, subgenres: [...filmData.subgenres, subgenre]});
    } else {
      toast.error('Max 3 sub-genres allowed');
    }
  };

  const renderStep = () => {
    switch(step) {
      case 1: return (<div className="space-y-3">
        <div><Label className="text-xs">{language === 'it' ? 'Titolo' : 'Title'} *</Label><Input value={filmData.title} onChange={e=>setFilmData({...filmData,title:e.target.value})} placeholder={language === 'it' ? 'Titolo del film...' : 'Film title...'} className="h-10 bg-black/20 border-white/10" data-testid="film-title-input" /></div>
        
        {/* Subtitle - optional, required for sequels */}
        <div>
          <Label className="text-xs">{language === 'it' ? 'Sottotitolo' : 'Subtitle'} {filmData.is_sequel && <span className="text-red-400">*</span>}</Label>
          <Input 
            value={filmData.subtitle} 
            onChange={e=>setFilmData({...filmData,subtitle:e.target.value})} 
            placeholder={language === 'it' ? 'es. "La Vendetta", "Il Ritorno"...' : 'e.g. "The Revenge", "The Return"...'} 
            className="h-9 bg-black/20 border-white/10" 
            data-testid="film-subtitle-input" 
          />
          <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Opzionale. Obbligatorio per i sequel.' : 'Optional. Required for sequels.'}</p>
        </div>
        
        {/* Sequel checkbox and parent selection */}
        <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Checkbox 
              id="is-sequel" 
              checked={filmData.is_sequel}
              onCheckedChange={(checked) => setFilmData({...filmData, is_sequel: checked, sequel_parent_id: checked ? filmData.sequel_parent_id : null})}
            />
            <Label htmlFor="is-sequel" className="text-sm cursor-pointer">
              {language === 'it' ? 'Questo è un sequel' : 'This is a sequel'}
            </Label>
          </div>
          
          {filmData.is_sequel && (
            <div className="pl-6 space-y-2">
              <Label className="text-xs">{language === 'it' ? 'Seleziona il film originale' : 'Select original film'} *</Label>
              {myFilmsForSequel.length > 0 ? (
                <Select value={filmData.sequel_parent_id || ''} onValueChange={v => {
                  const parent = myFilmsForSequel.find(f => f.id === v);
                  setFilmData({...filmData, sequel_parent_id: v, genre: parent?.genre || filmData.genre});
                }}>
                  <SelectTrigger className="h-9 bg-black/30 border-white/10">
                    <SelectValue placeholder={language === 'it' ? 'Seleziona...' : 'Select...'} />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1A1A1A] max-h-[200px]">
                    {myFilmsForSequel.map(f => (
                      <SelectItem key={f.id} value={f.id} className="text-xs">
                        <div className="flex items-center gap-2">
                          <span>{f.full_title}</span>
                          <Badge className={`text-[8px] ${f.film_tier === 'masterpiece' ? 'bg-yellow-500/20 text-yellow-400' : f.film_tier === 'possible_flop' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20'}`}>
                            Q:{f.quality_score}
                          </Badge>
                          {f.sequel_count > 0 && <span className="text-[9px] text-gray-400">({f.sequel_count} sequel)</span>}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-xs text-gray-400">{language === 'it' ? 'Nessun film disponibile. Crea prima un film.' : 'No films available. Create a film first.'}</p>
              )}
              
              {filmData.sequel_parent_id && (
                <div className="text-xs bg-black/30 rounded p-2">
                  {(() => {
                    const parent = myFilmsForSequel.find(f => f.id === filmData.sequel_parent_id);
                    if (!parent) return null;
                    const bonus = parent.quality_score >= 70 ? '+' : parent.quality_score < 40 ? '-' : '±';
                    const bonusColor = parent.quality_score >= 70 ? 'text-green-400' : parent.quality_score < 40 ? 'text-red-400' : 'text-yellow-400';
                    return (
                      <div className="flex items-center gap-2">
                        <TrendingUp className={`w-3 h-3 ${bonusColor}`} />
                        <span className={bonusColor}>
                          {language === 'it' 
                            ? `Bonus sequel: ${bonus} (basato su qualità ${parent.quality_score})`
                            : `Sequel bonus: ${bonus} (based on quality ${parent.quality_score})`}
                        </span>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div>
          <Label className="text-xs">{t('genre')} *</Label>
          <Select value={filmData.genre} onValueChange={v=>setFilmData({...filmData, genre:v, subgenres: []})} disabled={filmData.is_sequel && filmData.sequel_parent_id}>
            <SelectTrigger className="h-9 bg-black/20 border-white/10"><SelectValue /></SelectTrigger>
            <SelectContent className="bg-[#1A1A1A] max-h-[200px]">
              {Object.entries(genres).map(([key, g])=><SelectItem key={key} value={key}>{g.name}</SelectItem>)}
            </SelectContent>
          </Select>
          {filmData.is_sequel && filmData.sequel_parent_id && (
            <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Il genere è ereditato dal film originale' : 'Genre inherited from original film'}</p>
          )}
        </div>
        {genres[filmData.genre] && (
          <div>
            <Label className="text-xs">Sub-genres (max 3)</Label>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {genres[filmData.genre].subgenres.map(sg => (
                <Badge 
                  key={sg}
                  variant={filmData.subgenres.includes(sg) ? "default" : "outline"}
                  className={`cursor-pointer text-xs ${filmData.subgenres.includes(sg) ? 'bg-yellow-500 text-black hover:bg-yellow-600' : 'hover:bg-white/10'}`}
                  onClick={() => toggleSubgenre(sg)}
                >
                  {sg} {filmData.subgenres.includes(sg) && <X className="w-2.5 h-2.5 ml-1" />}
                </Badge>
              ))}
            </div>
            {filmData.subgenres.length > 0 && (
              <p className="text-xs text-gray-400 mt-1">Selected: {filmData.subgenres.join(', ')}</p>
            )}
          </div>
        )}
        <div><Label className="text-xs">{t('release_date')}</Label><Popover><PopoverTrigger asChild><Button variant="outline" className="w-full h-9 justify-start bg-black/20 border-white/10"><Calendar className="w-3 h-3 mr-2" />{format(releaseDate,'PPP')}</Button></PopoverTrigger><PopoverContent className="w-auto p-0 bg-[#1A1A1A] border-white/10"><CalendarComponent mode="single" selected={releaseDate} onSelect={setReleaseDate} disabled={d=>d<new Date(new Date().setHours(0,0,0,0))} /></PopoverContent></Popover></div>
        <div><Label className="text-xs">Weeks: {filmData.weeks_in_theater}</Label><Slider value={[filmData.weeks_in_theater]} onValueChange={([v])=>setFilmData({...filmData,weeks_in_theater:v})} min={1} max={12} /></div>
      </div>);
      case 2: return (<div className="space-y-2">
        <Card className={`border-2 cursor-pointer ${!filmData.sponsor_id?'border-yellow-500':'border-white/10'}`} onClick={()=>setFilmData({...filmData,sponsor_id:null})}><CardContent className="p-2 flex items-center gap-2"><X className="w-4 h-4" /><span className="text-sm">No Sponsor</span></CardContent></Card>
        {sponsors.map(s=><Card key={s.name} className={`border-2 cursor-pointer ${filmData.sponsor_id===s.name?'border-yellow-500':'border-white/10'}`} onClick={()=>setFilmData({...filmData,sponsor_id:s.name})}><CardContent className="p-2 flex justify-between items-center"><span className="text-sm">{s.name}</span><div className="text-right"><span className="text-green-400 text-sm">+${s.budget_offer.toLocaleString()}</span><span className="text-red-400 text-xs ml-2">-{s.revenue_share}%</span></div></CardContent></Card>)}
      </div>);
      case 3: return (<div className="space-y-3">
        <div><Label className="text-xs">Equipment</Label><div className="space-y-1">{equipment.map(e=><Card key={e.name} className={`border-2 cursor-pointer ${filmData.equipment_package===e.name?'border-yellow-500':'border-white/10'}`} onClick={()=>setFilmData({...filmData,equipment_package:e.name})}><CardContent className="p-2 flex justify-between"><span className="text-sm">{e.name} <span className="text-gray-400">(+{e.quality_bonus}%)</span></span><span className="text-yellow-500 text-sm">${e.cost.toLocaleString()}</span></CardContent></Card>)}</div></div>
        <div><Label className="text-xs">Locations</Label><div className="grid grid-cols-2 gap-1">{locations.map(l=>{const sel=filmData.locations.includes(l.name);return<Card key={l.name} className={`border-2 cursor-pointer ${sel?'border-yellow-500':'border-white/10'}`} onClick={()=>{if(sel)setFilmData({...filmData,locations:filmData.locations.filter(x=>x!==l.name)});else setFilmData({...filmData,locations:[...filmData.locations,l.name],location_days:{...filmData.location_days,[l.name]:7}});}}><CardContent className="p-1.5 text-xs"><span>{l.name}</span><span className="text-yellow-500 block">${l.cost_per_day.toLocaleString()}/day</span></CardContent></Card>;})}</div></div>
      </div>);
      case 4: case 5:
        const people45 = step===4?screenwriters:directors;
        const selId = step===4?filmData.screenwriter_id:filmData.director_id;
        const roleType45 = step===4?'screenwriters':'directors';
        const skills45 = step===4?availableSkills.screenwriters:availableSkills.directors;
        return (<div className="space-y-2">
          {/* Filters Row */}
          <div className="flex flex-wrap gap-2 p-2 bg-black/20 rounded border border-white/10">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="h-7 w-[140px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Categoria...' : 'Category...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte' : 'All'}</SelectItem>
                <SelectItem value="recommended" className="text-xs">{language === 'it' ? 'Consigliati' : 'Recommended'}</SelectItem>
                <SelectItem value="star" className="text-xs">Star</SelectItem>
                <SelectItem value="known" className="text-xs">{language === 'it' ? 'Conosciuti' : 'Known'}</SelectItem>
                <SelectItem value="emerging" className="text-xs">{language === 'it' ? 'Emergenti' : 'Emerging'}</SelectItem>
                <SelectItem value="unknown" className="text-xs">{language === 'it' ? 'Sconosciuti' : 'Unknown'}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSkill} onValueChange={setSelectedSkill}>
              <SelectTrigger className="h-7 w-[150px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Filtra skill...' : 'Filter skill...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte le skill' : 'All skills'}</SelectItem>
                {skills45.map(sk => (
                  <SelectItem key={sk} value={sk} className="text-xs">{sk}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="h-7" onClick={()=>fetchPeople(roleType45, selectedCategory, selectedSkill)}><RefreshCw className="w-3 h-3 mr-1" />Refresh</Button>
          </div>
          <p className="text-xs text-gray-400">{people45.length} {step===4?(language==='it'?'sceneggiatori':'screenwriters'):(language==='it'?'registi':'directors')} {language==='it'?'trovati':'found'}</p>
          <ScrollArea className="h-[380px] sm:h-[420px]"><div className="space-y-1.5 pr-2">{people45.map(p=>{const isSel=selId===p.id;return<PersonCard key={p.id} person={p} isSelected={isSel} roleType={step===4?'screenwriter':'director'} onSelect={()=>{if(step===4)setFilmData({...filmData,screenwriter_id:p.id});else setFilmData({...filmData,director_id:p.id});}} />;})}</div></ScrollArea>
        </div>);
      case 6:
        return (<div className="space-y-2">
          {/* Filters Row */}
          <div className="flex flex-wrap gap-2 p-2 bg-black/20 rounded border border-white/10">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="h-7 w-[140px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Categoria...' : 'Category...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte' : 'All'}</SelectItem>
                <SelectItem value="recommended" className="text-xs">{language === 'it' ? 'Consigliati' : 'Recommended'}</SelectItem>
                <SelectItem value="star" className="text-xs">Star</SelectItem>
                <SelectItem value="known" className="text-xs">{language === 'it' ? 'Conosciuti' : 'Known'}</SelectItem>
                <SelectItem value="emerging" className="text-xs">{language === 'it' ? 'Emergenti' : 'Emerging'}</SelectItem>
                <SelectItem value="unknown" className="text-xs">{language === 'it' ? 'Sconosciuti' : 'Unknown'}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSkill} onValueChange={setSelectedSkill}>
              <SelectTrigger className="h-7 w-[150px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Filtra skill...' : 'Filter skill...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte le skill' : 'All skills'}</SelectItem>
                {availableSkills.composers.map(sk => (
                  <SelectItem key={sk} value={sk} className="text-xs">{sk}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="h-7" onClick={()=>fetchPeople('composers', selectedCategory, selectedSkill)}><RefreshCw className="w-3 h-3 mr-1" />Refresh</Button>
          </div>
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-400"><Music className="w-3 h-3 inline mr-1" />{composers.length} {language==='it'?'compositori trovati':'composers found'}</p>
          </div>
          <ScrollArea className="h-[380px] sm:h-[420px]">
            <div className="space-y-1.5 pr-2">
              {composers.map(p => {
                const isSel = filmData.composer_id === p.id;
                return <PersonCard key={p.id} person={p} isSelected={isSel} roleType="composer" onSelect={() => setFilmData({...filmData, composer_id: p.id})} />;
              })}
            </div>
          </ScrollArea>
        </div>);
      case 7:
        return (<div className="space-y-2">
          {/* Filters Row */}
          <div className="flex flex-wrap gap-2 p-2 bg-black/20 rounded border border-white/10">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="h-7 w-[140px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Categoria...' : 'Category...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte' : 'All'}</SelectItem>
                <SelectItem value="recommended" className="text-xs">{language === 'it' ? 'Consigliati' : 'Recommended'}</SelectItem>
                <SelectItem value="star" className="text-xs">Star</SelectItem>
                <SelectItem value="known" className="text-xs">{language === 'it' ? 'Conosciuti' : 'Known'}</SelectItem>
                <SelectItem value="emerging" className="text-xs">{language === 'it' ? 'Emergenti' : 'Emerging'}</SelectItem>
                <SelectItem value="unknown" className="text-xs">{language === 'it' ? 'Sconosciuti' : 'Unknown'}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSkill} onValueChange={setSelectedSkill}>
              <SelectTrigger className="h-7 w-[150px] text-xs bg-black/30 border-white/10">
                <SelectValue placeholder={language === 'it' ? 'Filtra skill...' : 'Filter skill...'} />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A]">
                <SelectItem value="all" className="text-xs">{language === 'it' ? 'Tutte le skill' : 'All skills'}</SelectItem>
                {availableSkills.actors.map(sk => (
                  <SelectItem key={sk} value={sk} className="text-xs">{sk}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="h-7" onClick={()=>fetchPeople('actors', selectedCategory, selectedSkill)}><RefreshCw className="w-3 h-3 mr-1" />Refresh</Button>
          </div>
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-400">{language === 'it' ? 'Selezionati' : 'Selected'}: {filmData.actors.length} {language === 'it' ? 'attori' : 'actors'} • {actors.length} {language === 'it' ? 'disponibili' : 'available'}</p>
          </div>
          {filmData.actors.length > 0 && (
            <div className="flex flex-wrap gap-1 p-2 bg-black/20 rounded border border-white/10">
              {filmData.actors.map(a => {
                const actor = actors.find(ac => ac.id === a.actor_id);
                return actor ? (
                  <Badge key={a.actor_id} className="bg-yellow-500/20 text-yellow-500 text-xs">
                    {actor.name} ({getRoleName(a.role)})
                    <X className="w-2.5 h-2.5 ml-1 cursor-pointer" onClick={() => setFilmData({...filmData, actors: filmData.actors.filter(x => x.actor_id !== a.actor_id)})} />
                  </Badge>
                ) : null;
              })}
            </div>
          )}
          <ScrollArea className="h-[320px] sm:h-[360px]">
            <div className="space-y-1.5 pr-2">
              {actors.map(p => {
                const selectedActor = filmData.actors.find(a => a.actor_id === p.id);
                const isSel = !!selectedActor;
                return (
                  <PersonCard 
                    key={p.id} 
                    person={p} 
                    isSelected={isSel}
                    roleType="actor"
                    showRoleSelect={true}
                    currentRole={selectedActor?.role || 'protagonist'}
                    onRoleChange={(newRole) => {
                      setFilmData({
                        ...filmData, 
                        actors: filmData.actors.map(a => a.actor_id === p.id ? {...a, role: newRole} : a)
                      });
                    }}
                    onSelect={() => {
                      if (isSel) {
                        setFilmData({...filmData, actors: filmData.actors.filter(a => a.actor_id !== p.id)});
                      } else {
                        setFilmData({...filmData, actors: [...filmData.actors, {actor_id: p.id, role: 'protagonist'}]});
                      }
                    }} 
                  />
                );
              })}
            </div>
          </ScrollArea>
          <div><Label className="text-xs">Extras: {filmData.extras_count} (${filmData.extras_cost.toLocaleString()})</Label><Slider value={[filmData.extras_count]} onValueChange={([v])=>setFilmData({...filmData,extras_count:v,extras_cost:v*1000})} min={0} max={500} step={10} /></div>
        </div>);
      case 8: return (<div className="space-y-3">
        <div className="flex gap-2"><Button variant={filmData.screenplay_source==='manual'?'default':'outline'} size="sm" onClick={()=>setFilmData({...filmData,screenplay_source:'manual'})} className={filmData.screenplay_source==='manual'?'bg-yellow-500 text-black':''}>Manuale</Button><Button variant="outline" size="sm" onClick={generateScreenplay} disabled={generating||!filmData.title}><Sparkles className="w-3 h-3 mr-1" />{generating?'...':'Genera con AI'}</Button></div>
        <Input value={filmData.screenplay_prompt} onChange={e=>setFilmData({...filmData,screenplay_prompt:e.target.value})} placeholder="La tua idea per la sceneggiatura... (opzionale per AI)" className="bg-black/20 border-white/10 text-sm" />
        <Textarea value={filmData.screenplay} onChange={e=>setFilmData({...filmData,screenplay:e.target.value})} placeholder="Sceneggiatura..." className="min-h-[200px] bg-black/20 border-white/10" />
      </div>);
      case 9: return (<div className="space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Music className="w-5 h-5 text-purple-400" />
          <p className="text-sm">Genera una descrizione per la colonna sonora AI</p>
        </div>
        <Input value={filmData.soundtrack_prompt} onChange={e=>setFilmData({...filmData,soundtrack_prompt:e.target.value})} placeholder="Il tuo concept per la colonna sonora... (es: epica orchestrale con cori)" className="bg-black/20 border-white/10 text-sm" />
        <Button variant="outline" onClick={generateSoundtrack} disabled={generating||!filmData.title} className="border-purple-500/30 text-purple-400">
          <Sparkles className="w-3 h-3 mr-1" />{generating?'Generazione...':'Genera Descrizione AI'}
        </Button>
        {filmData.soundtrack_description && (
          <Card className="bg-purple-500/10 border-purple-500/30">
            <CardContent className="p-3">
              <p className="text-sm text-purple-200">{filmData.soundtrack_description}</p>
            </CardContent>
          </Card>
        )}
        <p className="text-xs text-gray-500">La descrizione verrà usata per generare la colonna sonora nel trailer del film.</p>
      </div>);
      case 10: return (<div className="grid md:grid-cols-2 gap-3">
        <div className="space-y-2">
          <Textarea value={filmData.poster_prompt} onChange={e=>setFilmData({...filmData,poster_prompt:e.target.value})} placeholder="Describe poster..." className="min-h-[100px] bg-black/20 border-white/10" />
          <Button onClick={generatePoster} disabled={generating} className="w-full bg-yellow-500 text-black"><Sparkles className="w-3 h-3 mr-1" />{generating?'...':'Generate AI Poster'}</Button>
          <Input value={filmData.poster_url} onChange={e=>setFilmData({...filmData,poster_url:e.target.value})} placeholder="Or paste URL..." className="bg-black/20 border-white/10" />
        </div>
        <div className="aspect-[2/3] bg-[#1A1A1A] rounded border border-white/10 overflow-hidden">{filmData.poster_url?<img src={filmData.poster_url} alt="Poster" className="w-full h-full object-cover" />:<div className="w-full h-full flex items-center justify-center text-gray-500"><Image className="w-10 h-10 opacity-50" /></div>}</div>
      </div>);
      case 11: return (<div className="space-y-3">
        <p className="text-xs text-gray-400">Ads give immediate revenue but may reduce satisfaction.</p>
        <div><Label className="text-xs">Duration: {filmData.ad_duration_seconds}s</Label><Slider value={[filmData.ad_duration_seconds]} onValueChange={([v])=>setFilmData({...filmData,ad_duration_seconds:v,ad_revenue:v*5000})} min={0} max={180} step={15} /></div>
        <Card className="bg-[#1A1A1A] border-white/10"><CardContent className="p-3"><div className="flex justify-between"><span>Immediate Revenue</span><span className="text-green-400 text-lg">+${filmData.ad_revenue.toLocaleString()}</span></div>{filmData.ad_duration_seconds>60&&<p className="text-xs text-yellow-500 mt-1">⚠️ High ads may reduce satisfaction</p>}</CardContent></Card>
      </div>);
      case 12:
        const budget=calculateBudget(), sponsor=getSponsorBudget(), net=budget-sponsor-filmData.ad_revenue;
        return (<Card className="bg-[#1A1A1A] border-white/10"><CardHeader className="pb-2"><CardTitle className="font-['Bebas_Neue'] text-xl">{filmData.title}</CardTitle><CardDescription>{t(filmData.genre)} • {filmData.weeks_in_theater}w</CardDescription></CardHeader><CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs"><div><span className="text-gray-400">Release</span><p>{format(releaseDate,'PPP')}</p></div><div><span className="text-gray-400">Sponsor</span><p>{filmData.sponsor_id||'None'}</p></div><div><span className="text-gray-400">Equipment</span><p>{filmData.equipment_package}</p></div><div><span className="text-gray-400">Cast</span><p>{filmData.actors.length}+{filmData.extras_count}</p></div><div><span className="text-gray-400">Composer</span><p>{composers.find(c=>c.id===filmData.composer_id)?.name||'None'}</p></div></div>
          <div className="pt-2 border-t border-white/10 space-y-1 text-sm"><div className="flex justify-between"><span>Budget</span><span className="text-red-400">-${budget.toLocaleString()}</span></div>{sponsor>0&&<div className="flex justify-between"><span>Sponsor</span><span className="text-green-400">+${sponsor.toLocaleString()}</span></div>}{filmData.ad_revenue>0&&<div className="flex justify-between"><span>Ads</span><span className="text-green-400">+${filmData.ad_revenue.toLocaleString()}</span></div>}<div className="flex justify-between font-bold pt-1 border-t border-white/10"><span>Net</span><span className={net>0?'text-red-400':'text-green-400'}>${Math.abs(net).toLocaleString()}</span></div></div>
        </CardContent></Card>);
      default: return null;
    }
  };

  const canProceed = () => { switch(step){ case 1:return filmData.title&&filmData.genre; case 3:return filmData.locations.length>0; case 4:return filmData.screenwriter_id; case 5:return filmData.director_id; case 6:return filmData.composer_id; case 7:return filmData.actors.length>0; case 8:return filmData.screenplay; default:return true; }};

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="film-wizard">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2 overflow-x-auto pb-1">{steps.map((s,i)=>(<div key={s.num} className="flex items-center"><div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step===s.num?'bg-yellow-500 text-black':step>s.num?'bg-green-500 text-white':'bg-gray-700 text-gray-400'}`}>{step>s.num?'✓':s.num}</div>{i<steps.length-1&&<div className={`w-3 h-0.5 mx-0.5 ${step>s.num?'bg-green-500':'bg-gray-700'}`} />}</div>))}</div>
        <h2 className="font-['Bebas_Neue'] text-xl">{steps[step-1].title}</h2>
      </div>
      <Card className="bg-[#1A1A1A] border-white/10"><CardContent className="p-3"><AnimatePresence mode="wait"><motion.div key={step} initial={{opacity:0,x:20}} animate={{opacity:1,x:0}} exit={{opacity:0,x:-20}}>{renderStep()}</motion.div></AnimatePresence></CardContent></Card>
      <div className="flex justify-between items-center mt-3">
        <div className="flex gap-2 items-center">
          <Button variant="outline" size="sm" onClick={()=>setStep(step-1)} disabled={step===1}>Previous</Button>
          <Button variant="outline" size="sm" onClick={()=>saveDraft('paused')} disabled={savingDraft} className="text-orange-400 border-orange-400/50 hover:bg-orange-500/10">
            {savingDraft ? '...' : (language === 'it' ? 'Metti in Pausa' : 'Pause')}
          </Button>
          {lastAutoSave && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <CheckCircle className="w-3 h-3 text-green-500" />
              {language === 'it' ? 'Salvato' : 'Saved'} {lastAutoSave.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
            </span>
          )}
        </div>
        {step<12?<Button size="sm" onClick={()=>setStep(step+1)} disabled={!canProceed()} className="bg-yellow-500 text-black">Next <ChevronRight className="w-3 h-3 ml-1" /></Button>:<Button size="sm" onClick={handleSubmit} disabled={loading||calculateBudget()-getSponsorBudget()-filmData.ad_revenue>user.funds} className="bg-yellow-500 text-black">{loading?'...':'Create Film'}</Button>}
      </div>

      {/* Rejection Modal */}
      {rejectionModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setRejectionModal(null)}>
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] border border-red-500/50 rounded-lg p-6 max-w-sm w-full"
            onClick={e => e.stopPropagation()}
            data-testid="rejection-modal"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                <XCircle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h3 className="font-bold text-lg text-red-400">
                  {language === 'it' ? 'Offerta Rifiutata' : 'Offer Rejected'}
                </h3>
                <p className="text-sm text-gray-400">{rejectionModal.name}</p>
              </div>
            </div>
            
            <div className="bg-black/30 rounded-lg p-4 mb-4">
              <p className="text-sm text-gray-300 italic">"{rejectionModal.reason}"</p>
            </div>
            
            {rejectionModal.alreadyRefused && (
              <p className="text-xs text-yellow-500 mb-3">
                {language === 'it' 
                  ? '⚠️ Questa persona ha già rifiutato la tua offerta oggi.' 
                  : '⚠️ This person already refused your offer today.'}
              </p>
            )}
            
            <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
              {rejectionModal.stars && (
                <div className="flex items-center gap-1">
                  {Array(5).fill(0).map((_, i) => (
                    <Star key={i} className={`w-3 h-3 ${i < rejectionModal.stars ? 'fill-yellow-500 text-yellow-500' : 'text-gray-600'}`} />
                  ))}
                </div>
              )}
              {rejectionModal.fame && (
                <span>{language === 'it' ? 'Fama' : 'Fame'}: {rejectionModal.fame}</span>
              )}
            </div>
            
            <Button 
              className="w-full bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30"
              onClick={() => setRejectionModal(null)}
              data-testid="rejection-modal-close"
            >
              {language === 'it' ? 'Ho capito' : 'I understand'}
            </Button>
          </motion.div>
        </div>
      )}

      {/* Film Tier Celebration Popup */}
      {tierPopup && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4" onClick={() => { setTierPopup(null); navigate(`/films/${tierPopup.filmId}`); }}>
          <motion.div 
            initial={{ scale: 0.5, opacity: 0, rotate: -10 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            transition={{ type: "spring", damping: 10 }}
            className={`bg-gradient-to-br ${tierPopup.style.bg} ${tierPopup.style.border} border-2 rounded-2xl p-8 max-w-md w-full text-center relative overflow-hidden`}
            onClick={e => e.stopPropagation()}
            data-testid="tier-popup"
          >
            {/* Confetti effect for positive tiers */}
            {tierPopup.tier !== 'flop' && (
              <div className="absolute inset-0 pointer-events-none">
                {Array(20).fill(0).map((_, i) => (
                  <motion.div
                    key={i}
                    className="absolute w-3 h-3 rounded-full"
                    style={{
                      background: ['#FFD700', '#FF6B6B', '#4ECDC4', '#A855F7', '#3B82F6'][i % 5],
                      left: `${Math.random() * 100}%`,
                      top: `-10%`
                    }}
                    animate={{
                      y: [0, 500],
                      x: [0, (Math.random() - 0.5) * 100],
                      rotate: [0, 360 * (Math.random() > 0.5 ? 1 : -1)],
                      opacity: [1, 0]
                    }}
                    transition={{
                      duration: 2 + Math.random(),
                      delay: Math.random() * 0.5,
                      repeat: Infinity
                    }}
                  />
                ))}
              </div>
            )}
            
            {/* Emoji and Title */}
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 1 }}
              className="text-7xl mb-4"
            >
              {tierPopup.style.emoji}
            </motion.div>
            
            <h2 className={`font-['Bebas_Neue'] text-4xl ${tierPopup.style.text} mb-2`}>
              {tierPopup.tier === 'flop' ? 'Uh oh...' : 'Congratulazioni!'}
            </h2>
            
            <p className="text-xl text-white mb-2">
              {language === 'it' ? 'Hai creato un possibile' : "You've created a potential"}
            </p>
            
            <h3 className={`font-['Bebas_Neue'] text-5xl ${tierPopup.style.text} mb-4`}>
              {tierPopup.tierName}!
            </h3>
            
            <p className="text-lg text-gray-300 mb-4">"{tierPopup.filmTitle}"</p>
            
            <div className={`bg-black/30 rounded-lg p-4 mb-4 ${tierPopup.style.border} border`}>
              <p className="text-sm text-gray-300 mb-2">{tierPopup.message}</p>
              <p className="text-2xl font-bold text-green-400">
                {language === 'it' ? 'Incasso apertura' : 'Opening'}: ${tierPopup.opening?.toLocaleString()}
              </p>
              {tierPopup.tier !== 'flop' && tierPopup.tier !== 'normal' && (
                <p className="text-xs text-gray-400 mt-2">
                  {language === 'it' ? `Bonus giornaliero: +${TIER_STYLES[tierPopup.tier] ? ['5%', '3%', '2%', '1%'][['masterpiece', 'epic', 'excellent', 'promising'].indexOf(tierPopup.tier)] : '0%'}` : `Daily bonus: +${['5%', '3%', '2%', '1%'][['masterpiece', 'epic', 'excellent', 'promising'].indexOf(tierPopup.tier)] || '0%'}`}
                </p>
              )}
              {tierPopup.tier === 'flop' && (
                <p className="text-xs text-orange-300 mt-2">
                  {language === 'it' ? 'Ma non arrenderti! A volte i flop diventano cult!' : "But don't give up! Sometimes flops become cult classics!"}
                </p>
              )}
            </div>
            
            <Button 
              className={`w-full ${tierPopup.tier === 'flop' ? 'bg-red-600 hover:bg-red-700' : 'bg-yellow-500 hover:bg-yellow-600'} text-black font-bold text-lg py-6`}
              onClick={() => { setTierPopup(null); navigate(`/films/${tierPopup.filmId}`); }}
            >
              {language === 'it' ? 'Vai al Film' : 'Go to Film'} <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </motion.div>
        </div>
      )}
      
      {/* Dismiss Pre-Engaged Cast Modal */}
      {dismissModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setDismissModal(null)}>
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }} 
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] rounded-xl p-6 max-w-md w-full border border-red-500/30"
            onClick={e => e.stopPropagation()}
          >
            <div className="text-center mb-4">
              <div className="w-16 h-16 mx-auto bg-red-500/20 rounded-full flex items-center justify-center mb-3">
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>
              <h2 className="font-['Bebas_Neue'] text-2xl text-red-400">
                {language === 'it' ? 'Congedare Cast' : 'Dismiss Cast'}
              </h2>
              <p className="text-lg font-semibold mt-2">{dismissModal.cast_name}</p>
            </div>
            
            <div className="bg-black/30 rounded-lg p-4 mb-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">{language === 'it' ? 'Anticipo perso' : 'Lost advance'}:</span>
                <span className="text-red-400 font-bold">${dismissModal.advance_lost?.toLocaleString()}</span>
              </div>
              {dismissModal.additional_penalty > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">{language === 'it' ? 'Penale aggiuntiva' : 'Additional penalty'}:</span>
                  <span className="text-red-400 font-bold">${dismissModal.additional_penalty?.toLocaleString()}</span>
                </div>
              )}
              <div className="border-t border-white/10 pt-2 flex justify-between">
                <span className="text-gray-300 font-semibold">{language === 'it' ? 'Costo totale' : 'Total cost'}:</span>
                <span className="text-red-400 font-bold text-lg">${dismissModal.total_cost?.toLocaleString()}</span>
              </div>
              <p className="text-xs text-gray-500 text-center mt-2">
                {language === 'it' ? `Penale: ${dismissModal.penalty_percent?.toFixed(0)}%` : `Penalty: ${dismissModal.penalty_percent?.toFixed(0)}%`}
              </p>
            </div>
            
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setDismissModal(null)} className="flex-1">
                {language === 'it' ? 'Annulla' : 'Cancel'}
              </Button>
              <Button onClick={confirmDismissal} className="flex-1 bg-red-600 hover:bg-red-700">
                {language === 'it' ? 'Congeda' : 'Dismiss'}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

// ==================== PRE-ENGAGEMENT PAGE ====================

const GENRES_LIST = [
  { id: 'action', name: 'Action', nameIt: 'Azione' },
  { id: 'comedy', name: 'Comedy', nameIt: 'Commedia' },
  { id: 'drama', name: 'Drama', nameIt: 'Drammatico' },
  { id: 'horror', name: 'Horror', nameIt: 'Horror' },
  { id: 'scifi', name: 'Sci-Fi', nameIt: 'Fantascienza' },
  { id: 'thriller', name: 'Thriller', nameIt: 'Thriller' },
  { id: 'romance', name: 'Romance', nameIt: 'Romantico' },
  { id: 'animation', name: 'Animation', nameIt: 'Animazione' },
  { id: 'documentary', name: 'Documentary', nameIt: 'Documentario' },
  { id: 'fantasy', name: 'Fantasy', nameIt: 'Fantasy' },
];

const PreEngagementPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('my-prefilms');
  const [preFilms, setPreFilms] = useState([]);
  const [expiredIdeas, setExpiredIdeas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEngageModal, setShowEngageModal] = useState(false);
  const [selectedPreFilm, setSelectedPreFilm] = useState(null);
  const [castType, setCastType] = useState('screenwriter');
  const [availableCast, setAvailableCast] = useState([]);
  const [loadingCast, setLoadingCast] = useState(false);
  const [negotiation, setNegotiation] = useState(null);
  
  // Create pre-film form
  const [newPreFilm, setNewPreFilm] = useState({ title: '', subtitle: '', genre: '', screenplay_draft: '', is_sequel: false, sequel_parent_id: null });
  const [myFilmsForPreSequel, setMyFilmsForPreSequel] = useState([]);

  useEffect(() => {
    loadData();
    // Load films for sequel selection
    api.get('/films/my/for-sequel').then(r=>setMyFilmsForPreSequel(r.data.films || [])).catch(()=>{});
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [preFilmsRes, expiredRes] = await Promise.all([
        api.get('/pre-films'),
        api.get('/pre-films/public/expired')
      ]);
      setPreFilms(preFilmsRes.data.pre_films || []);
      setExpiredIdeas(expiredRes.data.expired_ideas || []);
      
      // Check for rescissions on each pre-film
      for (const pf of preFilmsRes.data.pre_films || []) {
        if (pf.status === 'active' && !pf.is_expired) {
          try {
            const rescRes = await api.get(`/pre-films/${pf.id}/check-rescissions`);
            if (rescRes.data.rescissions?.length > 0) {
              for (const resc of rescRes.data.rescissions) {
                // Process rescission and notify user
                const processRes = await api.post(`/pre-films/${pf.id}/process-rescission?cast_type=${resc.cast_type}&cast_id=${resc.cast_id}`);
                toast.warning(`${resc.cast_name} ha rescisso il contratto per "${pf.title}". Anticipo rimborsato: $${resc.advance_to_refund.toLocaleString()}`);
              }
              // Reload data after rescissions
              const updatedRes = await api.get('/pre-films');
              setPreFilms(updatedRes.data.pre_films || []);
            }
          } catch (e) {
            // Silently fail rescission checks
          }
        }
      }
    } catch (e) {
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const createPreFilm = async () => {
    if (!newPreFilm.title || !newPreFilm.genre || !newPreFilm.screenplay_draft) {
      toast.error(language === 'it' ? 'Compila tutti i campi' : 'Fill all fields');
      return;
    }
    // Sequel validation
    if (newPreFilm.is_sequel && !newPreFilm.subtitle) {
      toast.error(language === 'it' ? 'Sottotitolo obbligatorio per i sequel' : 'Subtitle required for sequels');
      return;
    }
    if (newPreFilm.is_sequel && !newPreFilm.sequel_parent_id) {
      toast.error(language === 'it' ? 'Seleziona il film originale' : 'Select original film');
      return;
    }
    try {
      const res = await api.post('/pre-films', newPreFilm);
      if (res.data.success) {
        toast.success(res.data.message);
        setShowCreateModal(false);
        setNewPreFilm({ title: '', subtitle: '', genre: '', screenplay_draft: '', is_sequel: false, sequel_parent_id: null });
        loadData();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const loadAvailableCast = async (type) => {
    setLoadingCast(true);
    setCastType(type);
    try {
      const typeMap = { screenwriter: 'screenwriters', director: 'directors', composer: 'composers', actor: 'actors' };
      const res = await api.get(`/cast/available?type=${typeMap[type]}`);
      setAvailableCast(res.data.cast || []);
    } catch (e) {
      toast.error('Errore nel caricamento cast');
    } finally {
      setLoadingCast(false);
    }
  };

  const openEngageModal = (preFilm, type) => {
    setSelectedPreFilm(preFilm);
    setCastType(type);
    setNegotiation(null);
    loadAvailableCast(type);
    setShowEngageModal(true);
  };

  const engageCast = async (castMember, offeredFee) => {
    try {
      const res = await api.post(`/pre-films/${selectedPreFilm.id}/engage`, {
        pre_film_id: selectedPreFilm.id,
        cast_type: castType,
        cast_id: castMember.id,
        offered_fee: offeredFee
      });
      
      if (res.data.accepted) {
        toast.success(res.data.message);
        setShowEngageModal(false);
        loadData();
      } else {
        // Show negotiation options
        setNegotiation({
          ...res.data,
          cast_member: castMember,
          offered_fee: offeredFee
        });
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const renegotiate = async (newOffer) => {
    try {
      const res = await api.post(`/negotiations/${negotiation.negotiation_id}/renegotiate`, {
        pre_film_id: selectedPreFilm.id,
        cast_type: castType,
        cast_id: negotiation.cast_member.id,
        new_offer: newOffer,
        negotiation_id: negotiation.negotiation_id
      });
      
      if (res.data.accepted) {
        toast.success(res.data.message);
        setShowEngageModal(false);
        setNegotiation(null);
        loadData();
      } else if (res.data.final_rejection) {
        toast.error(res.data.message);
        setNegotiation(null);
      } else {
        setNegotiation(prev => ({
          ...prev,
          requested_fee: res.data.requested_fee,
          rejection_count: res.data.rejection_count
        }));
        toast.warning(res.data.message);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const releaseCast = async (preFilmId, type, castId, castName) => {
    if (!confirm(language === 'it' 
      ? `Sei sicuro di voler congedare ${castName}? Perderai l'anticipo e potresti dover pagare una penale.`
      : `Are you sure you want to dismiss ${castName}? You'll lose the advance and may have to pay a penalty.`
    )) return;
    
    try {
      const res = await api.post(`/pre-films/${preFilmId}/release`, {
        pre_film_id: preFilmId,
        cast_type: type,
        cast_id: castId
      });
      
      if (res.data.success) {
        toast.success(`${castName} ${language === 'it' ? 'congedato' : 'dismissed'}. ${language === 'it' ? 'Penale' : 'Penalty'}: ${res.data.penalty_percent.toFixed(0)}% ($${res.data.total_cost.toLocaleString()})`);
        loadData();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const convertToFilm = async (preFilmId) => {
    try {
      const res = await api.post(`/pre-films/${preFilmId}/convert`);
      if (res.data.success) {
        toast.success(res.data.message);
        navigate('/create', { state: { draftId: res.data.draft_id, fromPreFilm: true } });
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const getCastTypeLabel = (type) => {
    const labels = {
      screenwriter: language === 'it' ? 'Sceneggiatori' : 'Screenwriters',
      director: language === 'it' ? 'Registi' : 'Directors',
      composer: language === 'it' ? 'Musicisti' : 'Composers',
      actor: language === 'it' ? 'Attori' : 'Actors'
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="pt-20 p-4 flex justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-yellow-500" />
      </div>
    );
  }

  return (
    <div className="pt-20 pb-24 px-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-['Bebas_Neue'] text-3xl">{language === 'it' ? 'Pre-Ingaggio Cast' : 'Pre-Engagement'}</h1>
          <p className="text-sm text-gray-400">{language === 'it' ? 'Ingaggia il cast prima di creare il film' : 'Engage cast before creating your film'}</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="bg-orange-500 hover:bg-orange-600">
          <Plus className="w-4 h-4 mr-2" /> {language === 'it' ? 'Nuovo Pre-Film' : 'New Pre-Film'}
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="bg-black/20">
          <TabsTrigger value="my-prefilms">{language === 'it' ? 'I Miei Pre-Film' : 'My Pre-Films'} ({preFilms.length})</TabsTrigger>
          <TabsTrigger value="public-ideas">{language === 'it' ? 'Idee Pubbliche' : 'Public Ideas'} ({expiredIdeas.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="my-prefilms" className="mt-4">
          {preFilms.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-8 text-center">
                <Users className="w-12 h-12 mx-auto text-gray-500 mb-4" />
                <h3 className="text-lg font-bold mb-2">{language === 'it' ? 'Nessun Pre-Film' : 'No Pre-Films'}</h3>
                <p className="text-sm text-gray-400 mb-4">{language === 'it' ? 'Crea un pre-film per iniziare ad ingaggiare il cast in anticipo' : 'Create a pre-film to start engaging cast in advance'}</p>
                <Button onClick={() => setShowCreateModal(true)} className="bg-orange-500">
                  <Plus className="w-4 h-4 mr-2" /> {language === 'it' ? 'Crea Pre-Film' : 'Create Pre-Film'}
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {preFilms.map(pf => (
                <Card key={pf.id} className={`bg-[#1A1A1A] border-white/10 ${pf.is_expired ? 'opacity-60' : ''}`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-['Bebas_Neue'] text-xl">{pf.title}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge className="bg-purple-500/20 text-purple-400">{GENRES_LIST.find(g => g.id === pf.genre)?.[language === 'it' ? 'nameIt' : 'name'] || pf.genre}</Badge>
                          {pf.is_expired ? (
                            <Badge className="bg-red-500/20 text-red-400">{language === 'it' ? 'Scaduto' : 'Expired'}</Badge>
                          ) : (
                            <Badge className="bg-green-500/20 text-green-400">{pf.days_remaining} {language === 'it' ? 'giorni rimasti' : 'days left'}</Badge>
                          )}
                        </div>
                      </div>
                      {!pf.is_expired && (
                        <Button onClick={() => convertToFilm(pf.id)} className="bg-yellow-500 text-black hover:bg-yellow-400">
                          <Clapperboard className="w-4 h-4 mr-2" /> {language === 'it' ? 'Crea Film' : 'Create Film'}
                        </Button>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-400 mb-4 italic">"{pf.screenplay_draft}"</p>
                    
                    {/* Pre-engaged cast */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                      {['screenwriter', 'director', 'composer'].map(type => {
                        const engaged = pf.pre_engaged_cast?.[type];
                        return (
                          <div key={type} className="bg-black/30 rounded-lg p-3">
                            <p className="text-[10px] text-gray-500 uppercase mb-2">{getCastTypeLabel(type)}</p>
                            {engaged ? (
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-sm font-semibold">{engaged.name || 'Loading...'}</p>
                                  <p className="text-[10px] text-green-400">${engaged.offered_fee?.toLocaleString()}</p>
                                </div>
                                {!pf.is_expired && (
                                  <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-red-400 hover:bg-red-500/20"
                                    onClick={() => releaseCast(pf.id, type, engaged.id, engaged.name)}>
                                    <X className="w-3 h-3" />
                                  </Button>
                                )}
                              </div>
                            ) : (
                              <Button size="sm" variant="outline" className="w-full h-8 text-xs" onClick={() => openEngageModal(pf, type)} disabled={pf.is_expired}>
                                <Plus className="w-3 h-3 mr-1" /> {language === 'it' ? 'Ingaggia' : 'Engage'}
                              </Button>
                            )}
                          </div>
                        );
                      })}
                      
                      {/* Actors */}
                      <div className="bg-black/30 rounded-lg p-3">
                        <p className="text-[10px] text-gray-500 uppercase mb-2">{getCastTypeLabel('actor')} ({pf.pre_engaged_cast?.actors?.length || 0})</p>
                        {pf.pre_engaged_cast?.actors?.length > 0 && (
                          <div className="space-y-1 mb-2 max-h-20 overflow-y-auto">
                            {pf.pre_engaged_cast.actors.map(actor => (
                              <div key={actor.id} className="flex items-center justify-between text-xs bg-black/30 rounded px-2 py-1">
                                <span>{actor.name || 'Loading...'}</span>
                                {!pf.is_expired && (
                                  <button className="text-red-400 hover:text-red-300" onClick={() => releaseCast(pf.id, 'actor', actor.id, actor.name)}>
                                    <X className="w-3 h-3" />
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                        <Button size="sm" variant="outline" className="w-full h-8 text-xs" onClick={() => openEngageModal(pf, 'actor')} disabled={pf.is_expired}>
                          <Plus className="w-3 h-3 mr-1" /> {language === 'it' ? 'Aggiungi' : 'Add'}
                        </Button>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{language === 'it' ? 'Anticipi pagati' : 'Advances paid'}: ${pf.total_advance_paid?.toLocaleString() || 0}</span>
                      <span>{language === 'it' ? 'Creato' : 'Created'}: {new Date(pf.created_at).toLocaleDateString()}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="public-ideas" className="mt-4">
          {expiredIdeas.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-8 text-center">
                <Lightbulb className="w-12 h-12 mx-auto text-gray-500 mb-4" />
                <h3 className="text-lg font-bold mb-2">{language === 'it' ? 'Nessuna Idea Pubblica' : 'No Public Ideas'}</h3>
                <p className="text-sm text-gray-400">{language === 'it' ? 'Le idee scadute di altri produttori appariranno qui' : 'Expired ideas from other producers will appear here'}</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {expiredIdeas.map(idea => (
                <Card key={idea.id} className="bg-[#1A1A1A] border-white/10">
                  <CardContent className="p-4">
                    <h3 className="font-['Bebas_Neue'] text-lg">{idea.title}</h3>
                    <Badge className="bg-purple-500/20 text-purple-400 mt-1">{GENRES_LIST.find(g => g.id === idea.genre)?.[language === 'it' ? 'nameIt' : 'name'] || idea.genre}</Badge>
                    <p className="text-sm text-gray-400 mt-2 italic">"{idea.screenplay_draft}"</p>
                    <p className="text-[10px] text-gray-500 mt-3">{language === 'it' ? 'Idea di' : 'Idea by'}: {idea.creator_nickname} ({idea.creator_production_house})</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create Pre-Film Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowCreateModal(false)}>
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }} 
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] rounded-xl p-6 max-w-md w-full border border-white/10 max-h-[80vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <h2 className="font-['Bebas_Neue'] text-2xl mb-4">{language === 'it' ? 'Crea Pre-Film' : 'Create Pre-Film'}</h2>
            
            <div className="space-y-4">
              <div>
                <Label className="text-xs">{language === 'it' ? 'Titolo (provvisorio)' : 'Title (provisional)'}</Label>
                <Input 
                  value={newPreFilm.title} 
                  onChange={e => setNewPreFilm({...newPreFilm, title: e.target.value})}
                  placeholder={language === 'it' ? 'Il titolo del tuo film...' : 'Your film title...'}
                  className="bg-black/30 border-white/10"
                />
              </div>
              
              {/* Subtitle for sequels */}
              <div>
                <Label className="text-xs">{language === 'it' ? 'Sottotitolo' : 'Subtitle'} {newPreFilm.is_sequel && <span className="text-red-400">*</span>}</Label>
                <Input 
                  value={newPreFilm.subtitle} 
                  onChange={e => setNewPreFilm({...newPreFilm, subtitle: e.target.value})}
                  placeholder={language === 'it' ? 'es. "La Vendetta"...' : 'e.g. "The Revenge"...'}
                  className="bg-black/30 border-white/10"
                />
                <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Opzionale. Obbligatorio per i sequel.' : 'Optional. Required for sequels.'}</p>
              </div>
              
              {/* Sequel checkbox */}
              <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <Checkbox 
                    id="prefilm-is-sequel" 
                    checked={newPreFilm.is_sequel}
                    onCheckedChange={(checked) => setNewPreFilm({...newPreFilm, is_sequel: checked, sequel_parent_id: checked ? newPreFilm.sequel_parent_id : null})}
                  />
                  <Label htmlFor="prefilm-is-sequel" className="text-sm cursor-pointer">
                    {language === 'it' ? 'Questo è un sequel' : 'This is a sequel'}
                  </Label>
                </div>
                
                {newPreFilm.is_sequel && (
                  <div className="pl-6 space-y-2">
                    <Label className="text-xs">{language === 'it' ? 'Film originale' : 'Original film'} *</Label>
                    {myFilmsForPreSequel.length > 0 ? (
                      <select 
                        value={newPreFilm.sequel_parent_id || ''} 
                        onChange={e => {
                          const parent = myFilmsForPreSequel.find(f => f.id === e.target.value);
                          setNewPreFilm({...newPreFilm, sequel_parent_id: e.target.value, genre: parent?.genre || newPreFilm.genre});
                        }}
                        className="w-full h-9 rounded-md bg-black/30 border border-white/10 px-3 text-sm"
                      >
                        <option value="">{language === 'it' ? 'Seleziona...' : 'Select...'}</option>
                        {myFilmsForPreSequel.map(f => (
                          <option key={f.id} value={f.id}>{f.full_title} (Q:{f.quality_score})</option>
                        ))}
                      </select>
                    ) : (
                      <p className="text-xs text-gray-400">{language === 'it' ? 'Nessun film disponibile' : 'No films available'}</p>
                    )}
                  </div>
                )}
              </div>
              
              <div>
                <Label className="text-xs">{language === 'it' ? 'Genere' : 'Genre'}</Label>
                <select 
                  value={newPreFilm.genre} 
                  onChange={e => setNewPreFilm({...newPreFilm, genre: e.target.value})}
                  className="w-full h-10 rounded-md bg-black/30 border border-white/10 px-3 text-sm"
                  disabled={newPreFilm.is_sequel && newPreFilm.sequel_parent_id}
                >
                  <option value="">{language === 'it' ? 'Seleziona genere...' : 'Select genre...'}</option>
                  {GENRES_LIST.map(g => (
                    <option key={g.id} value={g.id}>{language === 'it' ? g.nameIt : g.name}</option>
                  ))}
                </select>
                {newPreFilm.is_sequel && newPreFilm.sequel_parent_id && (
                  <p className="text-[10px] text-gray-500 mt-1">{language === 'it' ? 'Genere ereditato' : 'Genre inherited'}</p>
                )}
              </div>
              
              <div>
                <Label className="text-xs">{language === 'it' ? 'Bozza Sceneggiatura (20-200 caratteri)' : 'Screenplay Draft (20-200 chars)'}</Label>
                <textarea 
                  value={newPreFilm.screenplay_draft} 
                  onChange={e => setNewPreFilm({...newPreFilm, screenplay_draft: e.target.value.slice(0, 200)})}
                  placeholder={language === 'it' ? 'Una breve descrizione della trama...' : 'A brief plot description...'}
                  className="w-full h-24 rounded-md bg-black/30 border border-white/10 px-3 py-2 text-sm resize-none"
                  maxLength={200}
                />
                <p className="text-[10px] text-gray-500 text-right">{newPreFilm.screenplay_draft.length}/200</p>
              </div>
              
              <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-3">
                <p className="text-xs text-orange-400">
                  {language === 'it' 
                    ? `Hai 20 giorni per completare il film. Se non lo fai, l'idea diventerà pubblica.`
                    : `You have 20 days to complete the film. If you don't, the idea will become public.`}
                </p>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <Button variant="outline" onClick={() => setShowCreateModal(false)} className="flex-1">
                {language === 'it' ? 'Annulla' : 'Cancel'}
              </Button>
              <Button onClick={createPreFilm} className="flex-1 bg-orange-500 hover:bg-orange-600">
                {language === 'it' ? 'Crea' : 'Create'}
              </Button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Engage Cast Modal */}
      {showEngageModal && selectedPreFilm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => { setShowEngageModal(false); setNegotiation(null); }}>
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }} 
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] rounded-xl p-6 max-w-2xl w-full border border-white/10 max-h-[80vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <h2 className="font-['Bebas_Neue'] text-2xl mb-2">
              {language === 'it' ? 'Ingaggia' : 'Engage'} {getCastTypeLabel(castType)}
            </h2>
            <p className="text-sm text-gray-400 mb-4">{language === 'it' ? 'per' : 'for'} "{selectedPreFilm.title}"</p>
            
            {/* Negotiation View */}
            {negotiation && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-4">
                <h3 className="font-bold text-red-400 mb-2">{negotiation.cast_name} {language === 'it' ? 'ha rifiutato!' : 'rejected!'}</h3>
                <p className="text-sm text-gray-300 mb-3">{negotiation.message}</p>
                
                {negotiation.can_renegotiate && (
                  <div className="space-y-3">
                    <p className="text-sm">{language === 'it' ? 'Richiesta' : 'Requested'}: <span className="text-yellow-400 font-bold">${negotiation.requested_fee?.toLocaleString()}</span></p>
                    
                    <div className="flex gap-2">
                      <Input 
                        type="number" 
                        placeholder={language === 'it' ? 'Nuova offerta...' : 'New offer...'}
                        className="bg-black/30 border-white/10"
                        id="renegotiate-offer"
                      />
                      <Button onClick={() => {
                        const input = document.getElementById('renegotiate-offer');
                        const value = parseFloat(input.value);
                        if (value > 0) renegotiate(value);
                      }} className="bg-yellow-500 text-black">
                        {language === 'it' ? 'Offri' : 'Offer'}
                      </Button>
                      <Button variant="outline" onClick={() => {
                        renegotiate(negotiation.requested_fee);
                      }} className="border-green-500 text-green-400">
                        {language === 'it' ? 'Accetta Richiesta' : 'Accept Request'}
                      </Button>
                    </div>
                    
                    <Button variant="ghost" onClick={() => setNegotiation(null)} className="w-full text-gray-400">
                      {language === 'it' ? 'Cerca altro cast' : 'Find other cast'}
                    </Button>
                  </div>
                )}
              </div>
            )}
            
            {/* Cast Tabs */}
            {!negotiation && (
              <>
                <Tabs value={castType} onValueChange={(v) => { setCastType(v); loadAvailableCast(v); }} className="mb-4">
                  <TabsList className="bg-black/20">
                    <TabsTrigger value="screenwriter">{language === 'it' ? 'Sceneggiatori' : 'Screenwriters'}</TabsTrigger>
                    <TabsTrigger value="director">{language === 'it' ? 'Registi' : 'Directors'}</TabsTrigger>
                    <TabsTrigger value="composer">{language === 'it' ? 'Musicisti' : 'Composers'}</TabsTrigger>
                    <TabsTrigger value="actor">{language === 'it' ? 'Attori' : 'Actors'}</TabsTrigger>
                  </TabsList>
                </Tabs>
                
                {loadingCast ? (
                  <div className="flex justify-center py-8">
                    <RefreshCw className="w-6 h-6 animate-spin text-yellow-500" />
                  </div>
                ) : (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {availableCast.map(cast => (
                      <CastEngageRow key={cast.id} cast={cast} onEngage={engageCast} language={language} />
                    ))}
                    {availableCast.length === 0 && (
                      <p className="text-center text-gray-500 py-4">{language === 'it' ? 'Nessun cast disponibile' : 'No cast available'}</p>
                    )}
                  </div>
                )}
              </>
            )}
            
            <Button variant="outline" onClick={() => { setShowEngageModal(false); setNegotiation(null); }} className="w-full mt-4">
              {language === 'it' ? 'Chiudi' : 'Close'}
            </Button>
          </motion.div>
        </div>
      )}
    </div>
  );
};

// Cast Row for Engagement
const CastEngageRow = ({ cast, onEngage, language }) => {
  const [offer, setOffer] = useState(cast.fee || 50000);
  const [showOffer, setShowOffer] = useState(false);
  
  return (
    <div className="bg-black/30 rounded-lg p-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <img 
          src={cast.avatar_url || `https://api.dicebear.com/9.x/personas/svg?seed=${cast.id}`} 
          alt={cast.name} 
          className="w-10 h-10 rounded-full"
        />
        <div>
          <p className="font-semibold">{cast.name}</p>
          <div className="flex items-center gap-2">
            <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">Fame: {cast.fame || 50}</Badge>
            <span className="text-xs text-green-400">${cast.fee?.toLocaleString() || '50,000'}</span>
          </div>
        </div>
      </div>
      
      {showOffer ? (
        <div className="flex items-center gap-2">
          <Input 
            type="number" 
            value={offer} 
            onChange={e => setOffer(parseFloat(e.target.value) || 0)}
            className="w-28 h-8 text-sm bg-black/30"
          />
          <Button size="sm" onClick={() => onEngage(cast, offer)} className="bg-orange-500 hover:bg-orange-600 h-8">
            {language === 'it' ? 'Offri' : 'Offer'}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setShowOffer(false)} className="h-8">
            <X className="w-4 h-4" />
          </Button>
        </div>
      ) : (
        <Button size="sm" onClick={() => setShowOffer(true)} className="bg-orange-500/20 text-orange-400 hover:bg-orange-500/30">
          {language === 'it' ? 'Ingaggia' : 'Engage'}
        </Button>
      )}
    </div>
  );
};

// ==================== END PRE-ENGAGEMENT PAGE ====================

// Film Drafts (Incomplete Films) Board
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

  if (loading) {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-1/3"></div>
          <div className="h-24 bg-gray-700 rounded"></div>
          <div className="h-24 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

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
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl">{t('my_films')}</h1>
        <Button size="sm" onClick={() => navigate('/create')} className="bg-yellow-500 text-black h-8 px-2 sm:px-3 text-xs sm:text-sm"><Plus className="w-3 h-3 mr-1" /> Create</Button>
      </div>
      {films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-6 text-center"><Film className="w-10 h-10 mx-auto mb-3 text-gray-600" /><h3 className="text-base mb-2">No films yet</h3><Button onClick={() => navigate('/create')} className="bg-yellow-500 text-black text-sm">Create First Film</Button></Card>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3">
          {films.map(film => (
            <Card key={film.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden">
              <div className="aspect-[2/3] relative cursor-pointer" onClick={() => navigate(`/films/${film.id}`)}>
                <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} alt={film.title} className="w-full h-full object-cover" />
                <Badge className={`absolute top-1 right-1 text-[10px] ${film.status === 'in_theaters' ? 'bg-green-500' : 'bg-orange-500'}`}>{film.status}</Badge>
              </div>
              <CardContent className="p-1.5 sm:p-2">
                <h3 className="font-semibold text-xs sm:text-sm truncate">{film.title}</h3>
                <div className="flex justify-between mt-1 text-[10px] sm:text-xs">
                  <span className="text-gray-400"><Heart className="w-2.5 h-2.5 inline" /> {film.likes_count}</span>
                  <span className="text-green-400">${((film.total_revenue||0)/1000).toFixed(0)}K</span>
                </div>
                {film.status === 'in_theaters' && (
                  <div className="flex gap-1 mt-1.5">
                    <Button variant="outline" size="sm" className="flex-1 h-6 text-[10px] border-yellow-500/30 text-yellow-400 px-1" onClick={() => setShowAdDialog(film)}>
                      <Sparkles className="w-2.5 h-2.5 mr-0.5" /> Ads
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="outline" size="sm" className="flex-1 h-6 text-[10px] border-orange-500/30 text-orange-400 px-1"><Trash2 className="w-2.5 h-2.5" /></Button>
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
const FilmDetail = () => {
  const { api, user } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [film, setFilm] = useState(null);
  const [expandedCountry, setExpandedCountry] = useState(null);
  const [actorRoles, setActorRoles] = useState([]);
  const [hourlyRevenue, setHourlyRevenue] = useState(null);
  const [durationStatus, setDurationStatus] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [trailerStatus, setTrailerStatus] = useState(null);
  const [generatingTrailer, setGeneratingTrailer] = useState(false);
  const [rereleaseStatus, setRereleaseStatus] = useState(null);
  const [rereleasing, setRereleasing] = useState(false);
  const [distribution, setDistribution] = useState(null);
  const [showLikersPopup, setShowLikersPopup] = useState(false);
  const [likers, setLikers] = useState([]);
  const [loadingLikers, setLoadingLikers] = useState(false);
  const [showEndRunPopup, setShowEndRunPopup] = useState(false);
  const [endRunData, setEndRunData] = useState(null);
  // Virtual Audience System
  const [virtualAudience, setVirtualAudience] = useState(null);
  const navigate = useNavigate();
  
  // One-time actions state
  const [filmActions, setFilmActions] = useState(null);
  const [performingAction, setPerformingAction] = useState(null);

  const loadFilm = async () => {
    const id = window.location.pathname.split('/').pop(); 
    const [filmRes, rolesRes, trailerRes, actionsRes, distRes, virtualRes] = await Promise.all([
      api.get(`/films/${id}`),
      api.get('/actor-roles').catch(() => ({ data: [] })),
      api.get(`/films/${id}/trailer-status`).catch(() => ({ data: null })),
      api.get(`/films/${id}/actions`).catch(() => ({ data: null })),
      api.get(`/films/${id}/distribution`).catch(() => ({ data: null })),
      api.get(`/films/${id}/virtual-audience`).catch(() => ({ data: null }))
    ]);
    setFilm(filmRes.data);
    setActorRoles(rolesRes.data);
    if (trailerRes.data) setTrailerStatus(trailerRes.data);
    if (actionsRes.data) setFilmActions(actionsRes.data);
    if (distRes.data) setDistribution(distRes.data);
    if (virtualRes.data) setVirtualAudience(virtualRes.data);
    
    // Load hourly revenue and duration status for in-theater films
    if (filmRes.data.status === 'in_theaters') {
      const [hourlyRes, durationRes] = await Promise.all([
        api.get(`/films/${id}/hourly-revenue`).catch(() => null),
        api.get(`/films/${id}/duration-status`).catch(() => null)
      ]);
      if (hourlyRes) setHourlyRevenue(hourlyRes.data);
      if (durationRes) setDurationStatus(durationRes.data);
    }
    
    // Load re-release status for withdrawn/completed films
    if (filmRes.data.status === 'withdrawn' || filmRes.data.status === 'completed') {
      const rereleaseRes = await api.get(`/films/${id}/rerelease-status`).catch(() => null);
      if (rereleaseRes) setRereleaseStatus(rereleaseRes.data);
      
      // Check if we should show end-of-run expectations popup (only for owner, only once per session)
      const shownKey = `endrun_shown_${id}`;
      if (filmRes.data.user_id === user?.id && !sessionStorage.getItem(shownKey) && filmRes.data.film_tier) {
        try {
          const expectationsRes = await api.get(`/films/${id}/tier-expectations`);
          if (expectationsRes.data) {
            setEndRunData(expectationsRes.data);
            setShowEndRunPopup(true);
            sessionStorage.setItem(shownKey, 'true');
          }
        } catch (e) {
          // Silently fail
        }
      }
    }
  };
  
  const handleRerelease = async () => {
    if (!rereleaseStatus?.can_rerelease) return;
    
    setRereleasing(true);
    try {
      const res = await api.post(`/films/${film.id}/rerelease`);
      toast.success(res.data.message);
      toast.info(`Incasso apertura: $${res.data.opening_revenue.toLocaleString()}`);
      loadFilm();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setRereleasing(false);
    }
  };

  useEffect(() => { loadFilm(); }, [api]);
  
  // Load likers when popup opens - must be before early return
  useEffect(() => {
    if (showLikersPopup && film) {
      const loadLikersData = async () => {
        setLoadingLikers(true);
        try {
          const res = await api.get(`/films/${film.id}/likes`);
          setLikers(res.data.likers || []);
        } catch (e) {
          toast.error('Errore nel caricamento');
        } finally {
          setLoadingLikers(false);
        }
      };
      loadLikersData();
    }
  }, [showLikersPopup, film?.id, api]);
  
  if (!film) return <div className="pt-16 p-4 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;
  
  // Check if current user is the owner
  const isOwner = filmActions?.is_owner || film.user_id === user?.id;
  
  // Check if action is available
  const isActionAvailable = (actionName) => {
    if (!isOwner) return false;
    if (!filmActions) return true; // Default to available if not loaded
    return filmActions.actions?.[actionName]?.available;
  };
  
  // Perform create star action
  const performCreateStar = async (actorId) => {
    if (!isActionAvailable('create_star')) {
      toast.error(language === 'it' ? 'Azione già utilizzata' : 'Action already used');
      return;
    }
    setPerformingAction('create_star');
    try {
      const res = await api.post(`/films/${film.id}/action/create-star?actor_id=${actorId}`);
      toast.success(res.data.message);
      loadFilm(); // Reload to update actions state
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
    setPerformingAction(null);
  };
  
  // Perform skill boost action
  const performSkillBoost = async () => {
    if (!isActionAvailable('skill_boost')) {
      toast.error(language === 'it' ? 'Azione già utilizzata' : 'Action already used');
      return;
    }
    setPerformingAction('skill_boost');
    try {
      const res = await api.post(`/films/${film.id}/action/skill-boost`);
      toast.success(res.data.message);
      // Show individual boosts
      res.data.boosted_cast?.forEach(b => {
        toast.info(`${b.name}: ${b.skill} +${b.boost}`);
      });
      loadFilm();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
    setPerformingAction(null);
  };

  const processHourlyRevenue = async () => {
    setProcessing(true);
    try {
      const res = await api.post(`/films/${film.id}/process-hourly-revenue`);
      if (res.data.processed) {
        toast.success(`Incasso orario: $${res.data.revenue.toLocaleString()}!`);
        if (res.data.special_event) {
          toast.success(`Evento speciale: ${res.data.special_event}!`);
        }
        loadFilm();
      } else {
        toast.info(`Attendi ${Math.ceil(res.data.wait_seconds / 60)} minuti per il prossimo incasso.`);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
    setProcessing(false);
  };

  const extendFilm = async () => {
    try {
      const res = await api.post(`/films/${film.id}/extend?extra_days=3`);
      toast.success(`Film esteso di ${res.data.extra_days} giorni! Fame +${res.data.fame_bonus}. Estensioni rimaste: ${res.data.extensions_remaining}`);
      loadFilm();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Impossibile estendere');
    }
  };

  const checkStarDiscoveries = async () => {
    try {
      const res = await api.post(`/films/${film.id}/check-star-discoveries`);
      if (res.data.total_found > 0) {
        res.data.discoveries.forEach(d => toast.success(d.announcement));
      } else {
        toast.info('Nessuna nuova stella scoperta questa volta.');
      }
    } catch (e) {
      toast.error('Errore nel controllo scoperte');
    }
  };

  const evolveSkills = async () => {
    try {
      const res = await api.post(`/films/${film.id}/evolve-cast-skills`);
      if (res.data.total_evolved > 0) {
        toast.success(`${res.data.total_evolved} membri del cast hanno evoluto le loro skill!`);
      } else {
        toast.info('Nessun cambiamento nelle skill del cast.');
      }
    } catch (e) {
      toast.error('Errore nell\'evoluzione skill');
    }
  };

  const generateTrailer = async (duration = 8) => {
    setGeneratingTrailer(true);
    try {
      const res = await api.post('/ai/generate-trailer', { film_id: film.id, duration: duration, style: 'cinematic' });
      if (res.data.status === 'exists') {
        toast.info('Il trailer esiste già!');
        setTrailerStatus({ has_trailer: true, trailer_url: res.data.trailer_url });
      } else {
        toast.success(res.data.message);
        // Poll for trailer status
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await api.get(`/films/${film.id}/trailer-status`);
            setTrailerStatus(statusRes.data);
            if (statusRes.data.has_trailer || statusRes.data.error) {
              clearInterval(pollInterval);
              setGeneratingTrailer(false);
              if (statusRes.data.has_trailer) {
                toast.success('Trailer generato con successo! +5 bonus qualità');
              } else if (statusRes.data.error) {
                toast.error('Errore nella generazione del trailer. Puoi riprovare.');
              }
              loadFilm(); // Reload to update filmActions
            }
          } catch (e) {
            clearInterval(pollInterval);
            setGeneratingTrailer(false);
          }
        }, 10000); // Poll ogni 10 secondi
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella generazione del trailer');
      setGeneratingTrailer(false);
    }
  };

  const getRoleName = (roleId) => {
    const role = actorRoles.find(r => r.id === roleId);
    if (!role) return roleId;
    const langKey = `name_${language}`;
    return role[langKey] || role.name;
  };

  const getRoleBadge = (role) => {
    const badges = {
      protagonist: { color: 'bg-yellow-500/20 text-yellow-500', label: getRoleName('protagonist') },
      co_protagonist: { color: 'bg-blue-500/20 text-blue-400', label: getRoleName('co_protagonist') },
      antagonist: { color: 'bg-red-500/20 text-red-400', label: getRoleName('antagonist') },
      supporting: { color: 'bg-gray-500/20 text-gray-400', label: getRoleName('supporting') },
      cameo: { color: 'bg-purple-500/20 text-purple-400', label: getRoleName('cameo') }
    };
    const badge = badges[role] || badges.supporting;
    return <Badge className={`${badge.color} text-[10px] h-4`}>{badge.label}</Badge>;
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="film-detail-page">
      <div className="grid lg:grid-cols-3 gap-4">
        <Card className="bg-[#1A1A1A] border-white/10 overflow-hidden">
          <div className="aspect-[2/3] relative">
            <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'} alt={film.title} className="w-full h-full object-cover" />
            {film.is_sequel && (
              <div className="absolute top-2 right-2 bg-purple-600 text-white text-xs px-2 py-1 rounded-lg font-bold shadow-lg">
                SEQUEL #{film.sequel_number || 2}
              </div>
            )}
          </div>
          <CardContent className="p-3">
            <h1 className="font-['Bebas_Neue'] text-xl mb-1">{film.title}</h1>
            {film.subtitle && (
              <h2 className="text-gray-400 text-sm mb-2">{film.subtitle}</h2>
            )}
            {/* Sequel bonus info */}
            {film.sequel_bonus_applied && (
              <div className={`text-xs p-2 rounded mb-2 ${film.sequel_bonus_applied.multiplier >= 1 ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                <div className="flex items-center gap-1">
                  <TrendingUp className={`w-3 h-3 ${film.sequel_bonus_applied.multiplier >= 1 ? 'text-green-400' : 'text-red-400'}`} />
                  <span className={film.sequel_bonus_applied.multiplier >= 1 ? 'text-green-400' : 'text-red-400'}>
                    {film.sequel_bonus_applied.reason}
                  </span>
                </div>
                <p className="text-gray-400 text-[10px] mt-1">
                  Sequel di "{film.sequel_bonus_applied.parent_title}" • Bonus: {film.sequel_bonus_applied.multiplier >= 1 ? '+' : ''}{((film.sequel_bonus_applied.multiplier - 1) * 100).toFixed(0)}%
                </p>
              </div>
            )}
            <div className="flex flex-wrap gap-1.5 mb-2">
              <Badge className="bg-yellow-500/20 text-yellow-500 text-xs">{t(film.genre)}</Badge>
              {film.subgenres?.map(sg => <Badge key={sg} variant="outline" className="text-[10px] h-4 border-gray-600">{sg}</Badge>)}
              <Badge className={`text-xs ${film.status==='in_theaters'?'bg-green-500':film.status==='withdrawn'?'bg-orange-500':'bg-gray-500'}`}>{film.status}</Badge>
            </div>
            
            {/* IMDb-style Rating */}
            <div className="flex items-center gap-3 mb-3 p-2 rounded bg-yellow-500/10 border border-yellow-500/20">
              <div className="text-center">
                <div className="flex items-center gap-1">
                  <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                  <span className="text-2xl font-bold text-yellow-500">{film.imdb_rating?.toFixed(1) || '0.0'}</span>
                </div>
                <p className="text-[10px] text-gray-400">IMDb Rating</p>
              </div>
              {film.user_avg_rating > 0 && (
                <div className="text-center border-l border-white/10 pl-3">
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-blue-400" />
                    <span className="text-lg font-bold text-blue-400">{film.user_avg_rating?.toFixed(1)}</span>
                  </div>
                  <p className="text-[10px] text-gray-400">{film.rating_count || 0} {language === 'it' ? 'voti' : 'votes'}</p>
                </div>
              )}
              {film.cineboard_score && (
                <div className="text-center border-l border-white/10 pl-3">
                  <span className="text-lg font-bold text-purple-400">{film.cineboard_score?.toFixed(0)}</span>
                  <p className="text-[10px] text-gray-400">CineScore</p>
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              <div 
                className="text-center p-2 rounded bg-white/5 cursor-pointer hover:bg-white/10 transition-colors"
                onClick={() => setShowLikersPopup(true)}
                data-testid="likes-count-btn"
              >
                <Heart className="w-4 h-4 mx-auto mb-0.5 text-pink-400" />
                <p className="font-bold text-sm">{film.likes_count}</p>
                <p className="text-[9px] text-gray-500">{language === 'it' ? 'Like Giocatori' : 'Player Likes'}</p>
              </div>
              <div className="text-center p-2 rounded bg-white/5">
                <Heart className="w-4 h-4 mx-auto mb-0.5 text-red-500 fill-red-500" />
                <p className="font-bold text-sm">{virtualAudience?.virtual_likes?.toLocaleString() || 0}</p>
                <p className="text-[9px] text-gray-500">{language === 'it' ? 'Like Pubblico' : 'Audience Likes'}</p>
              </div>
            </div>
            
            {/* Virtual Audience Bonus Display */}
            {virtualAudience?.bonuses && virtualAudience.bonuses.money_bonus_percent > 0 && (
              <div className="mt-2 p-2 rounded bg-gradient-to-r from-red-500/10 to-pink-500/10 border border-red-500/20">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">{language === 'it' ? 'Bonus Pubblico' : 'Audience Bonus'}</span>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-green-500/20 text-green-400 text-[10px]">
                      +{virtualAudience.bonuses.money_bonus_percent}% {language === 'it' ? 'ricavi' : 'revenue'}
                    </Badge>
                    <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">
                      +{virtualAudience.bonuses.rating_bonus} rating
                    </Badge>
                  </div>
                </div>
              </div>
            )}
            
            {/* Virtual Reviews Section */}
            {virtualAudience?.reviews && virtualAudience.reviews.length > 0 && (
              <div className="mt-2 pt-2 border-t border-white/10">
                <h4 className="text-[10px] font-semibold text-gray-400 mb-1.5 uppercase flex items-center gap-1">
                  <MessageCircle className="w-3 h-3" />
                  {language === 'it' ? 'Recensioni Pubblico' : 'Audience Reviews'}
                </h4>
                <div className="space-y-1.5 max-h-32 overflow-y-auto">
                  {virtualAudience.reviews.slice(0, 3).map((review, idx) => (
                    <div key={idx} className={`p-1.5 rounded text-xs ${review.sentiment === 'positive' ? 'bg-green-500/10 border-l-2 border-green-500' : review.sentiment === 'negative' ? 'bg-red-500/10 border-l-2 border-red-500' : 'bg-white/5 border-l-2 border-gray-500'}`}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="font-medium text-[10px]">{review.reviewer?.display || 'Anonymous'}</span>
                        <span className={`font-bold ${review.rating >= 7 ? 'text-green-400' : review.rating <= 4 ? 'text-red-400' : 'text-yellow-400'}`}>
                          ⭐ {review.rating}
                        </span>
                      </div>
                      <p className="text-gray-300 italic text-[10px] leading-tight">"{review.text}"</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-2 mt-2">
              <div className="text-center p-2 rounded bg-white/5"><DollarSign className="w-4 h-4 mx-auto mb-0.5 text-green-400" /><p className="font-bold text-sm">${(film.total_revenue||0).toLocaleString()}</p><p className="text-[9px] text-gray-500">{language === 'it' ? 'Incasso Totale' : 'Total Revenue'}</p></div>
              <div className="text-center p-2 rounded bg-white/5"><BarChart3 className="w-4 h-4 mx-auto mb-0.5 text-blue-400" /><p className="font-bold text-sm">{film.actual_weeks_in_theater || 0}</p><p className="text-[9px] text-gray-500">{language === 'it' ? 'Settimane' : 'Weeks'}</p></div>
            </div>
            <div className="mt-2 pt-2 border-t border-white/10 space-y-1">
              <div className="flex justify-between text-xs"><span className="text-gray-400">Quality</span><span>{film.quality_score?.toFixed(0)}%</span></div><Progress value={film.quality_score} className="h-1.5" />
              <div className="flex justify-between text-xs"><span className="text-gray-400">Satisfaction</span><span>{(film.audience_satisfaction||50).toFixed(0)}%</span></div><Progress value={film.audience_satisfaction||50} className="h-1.5" />
            </div>
            
            {/* Synopsis */}
            {film.synopsis && (
              <div className="mt-3 pt-3 border-t border-white/10">
                <h4 className="text-xs font-semibold text-gray-400 mb-1 uppercase">{language === 'it' ? 'Trama' : 'Synopsis'}</h4>
                <p className="text-sm text-gray-300 leading-relaxed">{film.synopsis}</p>
              </div>
            )}
          </CardContent>
        </Card>
        <div className="lg:col-span-2 space-y-4">
          {/* Hourly Revenue Section - Only for films in theaters */}
          {film.status === 'in_theaters' && (
            <Card className="bg-gradient-to-r from-green-500/10 to-yellow-500/10 border-green-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-400" /> Incassi Orari
                </CardTitle>
              </CardHeader>
              <CardContent>
                {hourlyRevenue && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                    <div className="p-2 rounded bg-black/20 text-center">
                      <p className="text-[10px] text-gray-400">Stima Oraria</p>
                      <p className="text-lg font-bold text-green-400">${hourlyRevenue.revenue?.toLocaleString()}</p>
                    </div>
                    <div className="p-2 rounded bg-black/20 text-center">
                      <p className="text-[10px] text-gray-400">Giorni in Sala</p>
                      <p className="text-lg font-bold">{hourlyRevenue.days_in_theater || durationStatus?.current_days || 1}</p>
                    </div>
                    <div className="p-2 rounded bg-black/20 text-center">
                      <p className="text-[10px] text-gray-400">Moltiplicatore</p>
                      <p className="text-lg font-bold text-yellow-400">x{((hourlyRevenue.factors?.quality_mult || 1) * (hourlyRevenue.factors?.genre_mult || 1)).toFixed(2)}</p>
                    </div>
                    <div className="p-2 rounded bg-black/20 text-center">
                      <p className="text-[10px] text-gray-400">Imprevedibilità</p>
                      <p className="text-lg font-bold">{((hourlyRevenue.factors?.unpredictability || 1) * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  {/* Hourly revenue - always available for owner */}
                  {isOwner && (
                    <Button onClick={processHourlyRevenue} disabled={processing} className="bg-green-600 hover:bg-green-500">
                      {processing ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : <DollarSign className="w-4 h-4 mr-1" />}
                      {language === 'it' ? 'Incassa Ora' : 'Collect Now'}
                    </Button>
                  )}
                  {/* Create Star - ONE TIME */}
                  {isOwner && (
                    <Button 
                      variant="outline" 
                      onClick={checkStarDiscoveries} 
                      disabled={!isActionAvailable('create_star') || performingAction === 'create_star'}
                      className={`border-yellow-500/30 ${!isActionAvailable('create_star') ? 'opacity-50 cursor-not-allowed' : 'text-yellow-400'}`}
                      title={!isActionAvailable('create_star') ? (language === 'it' ? 'Già utilizzato' : 'Already used') : ''}
                    >
                      <Star className="w-4 h-4 mr-1" /> {language === 'it' ? 'Crea Stella' : 'Create Star'}
                      {!isActionAvailable('create_star') && <Lock className="w-3 h-3 ml-1" />}
                    </Button>
                  )}
                  {/* Skill Boost - ONE TIME */}
                  {isOwner && (
                    <Button 
                      variant="outline" 
                      onClick={performSkillBoost} 
                      disabled={!isActionAvailable('skill_boost') || performingAction === 'skill_boost'}
                      className={`border-blue-500/30 ${!isActionAvailable('skill_boost') ? 'opacity-50 cursor-not-allowed' : 'text-blue-400'}`}
                      title={!isActionAvailable('skill_boost') ? (language === 'it' ? 'Già utilizzato' : 'Already used') : ''}
                    >
                      {performingAction === 'skill_boost' ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : <TrendingUp className="w-4 h-4 mr-1" />}
                      {language === 'it' ? 'Boost Skill Cast' : 'Boost Cast Skills'}
                      {!isActionAvailable('skill_boost') && <Lock className="w-3 h-3 ml-1" />}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Duration Status */}
          {film.status === 'in_theaters' && durationStatus && (
            <Card className={`border ${durationStatus.status === 'extend' ? 'bg-green-500/10 border-green-500/30' : durationStatus.status === 'withdraw_early' ? 'bg-red-500/10 border-red-500/30' : 'bg-[#1A1A1A] border-white/10'}`}>
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-yellow-500" /> Stato Programmazione
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{durationStatus.current_days}</p>
                    <p className="text-[10px] text-gray-400">Giorni trascorsi</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">{durationStatus.planned_days}</p>
                    <p className="text-[10px] text-gray-400">Giorni pianificati</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-yellow-400">{durationStatus.days_remaining}</p>
                    <p className="text-[10px] text-gray-400">Giorni rimanenti</p>
                  </div>
                </div>
                <div className="p-2 rounded bg-black/20 mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">Performance Score:</span>
                    <span className={`font-bold ${durationStatus.score > 0 ? 'text-green-400' : durationStatus.score < 0 ? 'text-red-400' : 'text-gray-400'}`}>{durationStatus.score > 0 ? '+' : ''}{durationStatus.score}</span>
                  </div>
                  <div className="text-[10px] text-gray-400">
                    {durationStatus.reasons?.slice(0, 3).map((r, i) => <div key={i}>{r}</div>)}
                  </div>
                </div>
                {durationStatus.status === 'extend' && durationStatus.can_extend && (
                  <div className="p-3 rounded bg-green-500/20 border border-green-500/30 mb-3">
                    <p className="text-green-400 font-semibold flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Film idoneo per estensione!</p>
                    <p className="text-xs text-gray-300">Puoi estendere fino a {durationStatus.max_days_per_extension || 3} giorni extra.</p>
                    <p className="text-xs text-green-300">Fame bonus: +{durationStatus.fame_change}</p>
                    <p className="text-[10px] text-gray-400 mt-1">Estensioni: {durationStatus.extension_count || 0}/{durationStatus.max_extensions || 3}</p>
                    <Button onClick={extendFilm} size="sm" className="mt-2 bg-green-600">Estendi di 3 giorni</Button>
                  </div>
                )}
                {durationStatus.status === 'extend' && !durationStatus.can_extend && durationStatus.extension_count < 3 && (
                  <div className="p-3 rounded bg-yellow-500/20 border border-yellow-500/30 mb-3">
                    <p className="text-yellow-400 font-semibold flex items-center gap-2"><Clock className="w-4 h-4" /> Estensione in cooldown</p>
                    <p className="text-xs text-gray-300">Attendi {durationStatus.days_until_next_extension} giorni prima di estendere.</p>
                    <p className="text-[10px] text-gray-400">Estensioni: {durationStatus.extension_count || 0}/{durationStatus.max_extensions || 3}</p>
                  </div>
                )}
                {durationStatus.extension_count >= 3 && (
                  <div className="p-3 rounded bg-gray-500/20 border border-gray-500/30 mb-3">
                    <p className="text-gray-400 font-semibold flex items-center gap-2"><Check className="w-4 h-4" /> Estensioni esaurite</p>
                    <p className="text-xs text-gray-400">Hai usato tutte le 3 estensioni disponibili.</p>
                    <p className="text-[10px] text-gray-500">Giorni totali aggiunti: +{durationStatus.total_extension_days || 0}</p>
                  </div>
                )}
                {durationStatus.status === 'withdraw_early' && (
                  <div className="p-3 rounded bg-red-500/20 border border-red-500/30">
                    <p className="text-red-400 font-semibold flex items-center gap-2"><TrendingDown className="w-4 h-4" /> Performance scarsa</p>
                    <p className="text-xs text-gray-300">Il film potrebbe essere ritirato anticipatamente.</p>
                    <p className="text-xs text-red-300">Fame penalty: {durationStatus.fame_change}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
          
          {/* Re-release Section - For withdrawn/completed films owned by user */}
          {isOwner && (film.status === 'withdrawn' || film.status === 'completed') && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-purple-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  <RotateCcw className="w-5 h-5 text-purple-400" /> 
                  {language === 'it' ? 'Rimetti in Sala' : 'Re-release'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {rereleaseStatus?.can_rerelease ? (
                  <div className="space-y-3">
                    <p className="text-sm text-gray-300">
                      {language === 'it' 
                        ? 'Puoi rimettere questo film nelle sale cinematografiche!'
                        : 'You can bring this film back to theaters!'}
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-2 rounded bg-black/20 text-center">
                        <p className="text-[10px] text-gray-400">{language === 'it' ? 'Costo' : 'Cost'}</p>
                        <p className="text-lg font-bold text-yellow-400">${rereleaseStatus.cost?.toLocaleString()}</p>
                      </div>
                      <div className="p-2 rounded bg-black/20 text-center">
                        <p className="text-[10px] text-gray-400">{language === 'it' ? 'Uscite precedenti' : 'Previous releases'}</p>
                        <p className="text-lg font-bold">{rereleaseStatus.times_released || 1}</p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500">
                      {language === 'it' 
                        ? `Costo: 30% del budget originale ($${rereleaseStatus.original_budget?.toLocaleString()})`
                        : `Cost: 30% of original budget ($${rereleaseStatus.original_budget?.toLocaleString()})`}
                    </p>
                    <Button 
                      onClick={handleRerelease} 
                      disabled={rereleasing || (user?.funds || 0) < rereleaseStatus.cost}
                      className="w-full bg-purple-600 hover:bg-purple-500"
                    >
                      {rereleasing ? (
                        <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> {language === 'it' ? 'Rilancio...' : 'Releasing...'}</>
                      ) : (
                        <><RotateCcw className="w-4 h-4 mr-2" /> {language === 'it' ? 'Rimetti in Sala' : 'Re-release'} - ${rereleaseStatus.cost?.toLocaleString()}</>
                      )}
                    </Button>
                  </div>
                ) : rereleaseStatus?.days_remaining > 0 ? (
                  <div className="space-y-3">
                    <p className="text-sm text-gray-300">
                      {language === 'it' 
                        ? 'Questo film non può essere ancora rimesso in sala.'
                        : 'This film cannot be re-released yet.'}
                    </p>
                    <div className="p-3 rounded bg-black/20 text-center">
                      <Clock className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
                      <p className="text-2xl font-bold text-yellow-400">{rereleaseStatus.days_remaining}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'giorni rimanenti' : 'days remaining'}</p>
                    </div>
                    <p className="text-xs text-gray-500 text-center">
                      {language === 'it' 
                        ? 'Devi aspettare 7 giorni dalla rimozione prima di poter rimettere il film in sala.'
                        : 'You must wait 7 days after withdrawal before re-releasing.'}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">
                    {rereleaseStatus?.reason || (language === 'it' ? 'Verifica stato in corso...' : 'Checking status...')}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Cinema Distribution Section - Where the film is showing */}
          {distribution && distribution.current_cinemas > 0 && (
            <Card className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-blue-400" /> 
                  {language === 'it' ? 'In Programmazione' : 'Now Showing In'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                  <div className="p-2 rounded bg-black/20 text-center">
                    <p className="text-[10px] text-gray-400">{language === 'it' ? 'Cinema' : 'Cinemas'}</p>
                    <p className="text-xl font-bold text-blue-400">{distribution.current_cinemas}</p>
                  </div>
                  <div className="p-2 rounded bg-black/20 text-center">
                    <p className="text-[10px] text-gray-400">{language === 'it' ? 'Spettatori' : 'Viewers'}</p>
                    <p className="text-xl font-bold text-green-400">{distribution.current_attendance?.toLocaleString()}</p>
                  </div>
                  <div className="p-2 rounded bg-black/20 text-center">
                    <p className="text-[10px] text-gray-400">{language === 'it' ? 'Media/Cinema' : 'Avg/Cinema'}</p>
                    <p className="text-xl font-bold">{distribution.avg_attendance_per_cinema}</p>
                  </div>
                  <div className="p-2 rounded bg-black/20 text-center">
                    <p className="text-[10px] text-gray-400">{language === 'it' ? 'Totale Storico' : 'Total All-Time'}</p>
                    <p className="text-xl font-bold text-purple-400">{(distribution.cumulative_attendance || 0).toLocaleString()}</p>
                  </div>
                </div>
                
                {/* Country distribution */}
                <div className="space-y-1.5">
                  <p className="text-xs text-gray-400 uppercase font-semibold mb-2">
                    {language === 'it' ? 'Distribuzione per Paese' : 'Distribution by Country'}
                  </p>
                  {distribution.distribution?.map((country, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 rounded bg-black/20">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{
                          country.country_code === 'US' ? '🇺🇸' :
                          country.country_code === 'IT' ? '🇮🇹' :
                          country.country_code === 'FR' ? '🇫🇷' :
                          country.country_code === 'DE' ? '🇩🇪' :
                          country.country_code === 'UK' ? '🇬🇧' :
                          country.country_code === 'ES' ? '🇪🇸' :
                          country.country_code === 'JP' ? '🇯🇵' :
                          country.country_code === 'CN' ? '🇨🇳' :
                          country.country_code === 'BR' ? '🇧🇷' :
                          country.country_code === 'MX' ? '🇲🇽' : '🌍'
                        }</span>
                        <span className="font-medium">{country.country_name}</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <span className="text-blue-400">{country.cinemas} {language === 'it' ? 'cinema' : 'cinemas'}</span>
                        <span className="text-green-400">{country.total_attendance?.toLocaleString()} {language === 'it' ? 'spett.' : 'viewers'}</span>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Trend indicator */}
                <div className="mt-3 pt-3 border-t border-white/10 flex items-center justify-between">
                  <span className="text-xs text-gray-400">{language === 'it' ? 'Tendenza' : 'Trend'}</span>
                  <span className={`flex items-center gap-1 text-sm font-semibold ${
                    distribution.trend === 'growing' ? 'text-green-400' :
                    distribution.trend === 'declining' ? 'text-red-400' :
                    distribution.trend === 'stable' ? 'text-yellow-400' : 'text-gray-400'
                  }`}>
                    {distribution.trend === 'growing' && <><TrendingUp className="w-4 h-4" /> {language === 'it' ? 'In Crescita' : 'Growing'}</>}
                    {distribution.trend === 'declining' && <><TrendingDown className="w-4 h-4" /> {language === 'it' ? 'In Calo' : 'Declining'}</>}
                    {distribution.trend === 'stable' && <><span>→</span> {language === 'it' ? 'Stabile' : 'Stable'}</>}
                    {distribution.trend === 'new' && <><Sparkles className="w-4 h-4" /> {language === 'it' ? 'Nuovo' : 'New'}</>}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Cast Section */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2"><CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><Users className="w-4 h-4 text-yellow-500" /> Cast & Crew</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {/* Director & Screenwriter */}
              <div className="grid grid-cols-2 gap-2">
                {film.director && (
                  <div className="p-2 rounded bg-white/5">
                    <p className="text-[10px] text-gray-500 uppercase mb-1">Director</p>
                    <div className="flex items-center gap-2">
                      <Avatar className="w-8 h-8"><AvatarImage src={film.director.avatar_url} /><AvatarFallback className="text-[10px] bg-yellow-500/20">{film.director.name?.[0]}</AvatarFallback></Avatar>
                      <div>
                        <p className="text-sm font-semibold">{film.director.name} <span className={`${film.director.gender === 'female' ? 'text-pink-400' : 'text-blue-400'}`}>{film.director.gender === 'female' ? '♀' : '♂'}</span></p>
                        <p className="text-[10px] text-gray-400">{film.director.nationality}</p>
                      </div>
                    </div>
                  </div>
                )}
                {film.screenwriter && (
                  <div className="p-2 rounded bg-white/5">
                    <p className="text-[10px] text-gray-500 uppercase mb-1">Screenwriter</p>
                    <div className="flex items-center gap-2">
                      <Avatar className="w-8 h-8"><AvatarImage src={film.screenwriter.avatar_url} /><AvatarFallback className="text-[10px] bg-yellow-500/20">{film.screenwriter.name?.[0]}</AvatarFallback></Avatar>
                      <div>
                        <p className="text-sm font-semibold">{film.screenwriter.name} <span className={`${film.screenwriter.gender === 'female' ? 'text-pink-400' : 'text-blue-400'}`}>{film.screenwriter.gender === 'female' ? '♀' : '♂'}</span></p>
                        <p className="text-[10px] text-gray-400">{film.screenwriter.nationality}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              {/* Actors */}
              {film.cast?.length > 0 && (
                <div>
                  <p className="text-[10px] text-gray-500 uppercase mb-2">Cast ({film.cast.length} actors)</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {film.cast.map(actor => (
                      <div key={actor.id || actor.actor_id} className="flex items-center gap-2 p-2 rounded bg-white/5">
                        <Avatar className="w-8 h-8"><AvatarImage src={actor.avatar_url} /><AvatarFallback className="text-[10px] bg-yellow-500/20">{actor.name?.[0]}</AvatarFallback></Avatar>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            <p className="text-sm font-semibold truncate">{actor.name}</p>
                            <span className={`text-xs ${actor.gender === 'female' ? 'text-pink-400' : 'text-blue-400'}`}>{actor.gender === 'female' ? '♀' : '♂'}</span>
                          </div>
                          <p className="text-[10px] text-gray-400">{actor.nationality}</p>
                        </div>
                        {actor.role && getRoleBadge(actor.role)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
          {/* Trailer Section */}
          <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30" data-testid="trailer-section">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <Film className="w-5 h-5 text-purple-400" /> Trailer Video
                {trailerStatus?.has_trailer && <Badge className="bg-green-500/20 text-green-400 text-xs ml-2">Generato</Badge>}
              </CardTitle>
              <CardDescription className="text-xs">Genera un trailer AI per il tuo film (+5 bonus qualità)</CardDescription>
            </CardHeader>
            <CardContent>
              {trailerStatus?.has_trailer && trailerStatus.trailer_url ? (
                <div className="space-y-3">
                  <div className="aspect-video bg-black rounded-lg overflow-hidden">
                    <video 
                      src={`${BACKEND_URL}${trailerStatus.trailer_url}`} 
                      controls 
                      className="w-full h-full"
                      poster={film.poster_url}
                    >
                      Il tuo browser non supporta i video.
                    </video>
                  </div>
                  <p className="text-xs text-green-400 text-center">Trailer generato! Il tuo film ha ricevuto +5 bonus qualità.</p>
                </div>
              ) : trailerStatus?.generating || generatingTrailer ? (
                <div className="text-center py-8 space-y-3">
                  <RefreshCw className="w-10 h-10 mx-auto text-purple-400 animate-spin" />
                  <p className="text-purple-300">Generazione trailer in corso...</p>
                  <p className="text-xs text-gray-400">Questo processo richiede 2-5 minuti. Puoi tornare più tardi.</p>
                  <Progress value={33} className="h-1.5 max-w-xs mx-auto" />
                </div>
              ) : trailerStatus?.error ? (
                <div className="text-center py-6 space-y-3">
                  <AlertTriangle className="w-10 h-10 mx-auto text-red-400" />
                  <p className="text-red-400">{language === 'it' ? 'Errore nella generazione del trailer' : 'Error generating trailer'}</p>
                  <p className="text-xs text-gray-500">{trailerStatus.error}</p>
                  <div className="flex flex-col items-center gap-2">
                    <p className="text-xs text-gray-400">{language === 'it' ? 'Riprova la generazione:' : 'Retry generation:'}</p>
                    <div className="flex gap-2">
                      <Button onClick={() => generateTrailer(4)} variant="outline" size="sm" className="border-purple-500/30 text-purple-400">
                        4 sec
                      </Button>
                      <Button onClick={() => generateTrailer(8)} size="sm" className="bg-purple-600 hover:bg-purple-500">
                        <RefreshCw className="w-3 h-3 mr-1" /> 8 sec ($50,000)
                      </Button>
                      <Button onClick={() => generateTrailer(12)} variant="outline" size="sm" className="border-purple-500/30 text-purple-400">
                        12 sec
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 space-y-3">
                  <Film className="w-12 h-12 mx-auto text-purple-400/50" />
                  <p className="text-gray-400 text-sm">
                    {language === 'it' ? 'Nessun trailer generato per questo film' : 'No trailer generated for this film'}
                  </p>
                  {/* Only show generation buttons if owner */}
                  {isOwner && (
                    <div className="flex flex-col items-center gap-3">
                      <div className="flex gap-2">
                        <Button 
                          onClick={() => generateTrailer(4)} 
                          disabled={generatingTrailer || !isActionAvailable('generate_trailer')}
                          variant="outline"
                          className={`border-purple-500/30 ${!isActionAvailable('generate_trailer') ? 'opacity-50' : 'text-purple-400'}`}
                          data-testid="generate-trailer-4s"
                        >
                          4 sec
                        </Button>
                        <Button 
                          onClick={() => generateTrailer(8)} 
                          disabled={generatingTrailer || !isActionAvailable('generate_trailer')}
                          className={`${!isActionAvailable('generate_trailer') ? 'opacity-50 bg-purple-600/50' : 'bg-purple-600 hover:bg-purple-500'}`}
                          data-testid="generate-trailer-btn"
                        >
                          <Sparkles className="w-4 h-4 mr-2" />
                          8 sec ($50,000)
                        </Button>
                        <Button 
                          onClick={() => generateTrailer(12)} 
                          disabled={generatingTrailer || !isActionAvailable('generate_trailer')}
                          variant="outline"
                          className={`border-purple-500/30 ${!isActionAvailable('generate_trailer') ? 'opacity-50' : 'text-purple-400'}`}
                          data-testid="generate-trailer-12s"
                        >
                          12 sec
                        </Button>
                      </div>
                      <p className="text-[10px] text-gray-500">Generato da Sora 2 • +5 bonus qualità</p>
                    </div>
                  )}
                  {!isOwner && (
                    <p className="text-xs text-gray-500">
                      {language === 'it' ? 'Solo il proprietario può generare il trailer' : 'Only the owner can generate the trailer'}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Likers Popup */}
      {showLikersPopup && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowLikersPopup(false)}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#1A1A1A] border border-white/10 rounded-xl p-4 max-w-md w-full max-h-[70vh] overflow-hidden"
            onClick={e => e.stopPropagation()}
            data-testid="likers-popup"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
                <Heart className="w-5 h-5 text-red-400 fill-red-400" />
                {language === 'it' ? `Chi ha messo Like (${film.likes_count || 0})` : `Who Liked (${film.likes_count || 0})`}
              </h3>
              <button onClick={() => setShowLikersPopup(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <ScrollArea className="h-[50vh]">
              {loadingLikers ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto text-yellow-500" />
                </div>
              ) : likers.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Heart className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p>{language === 'it' ? 'Nessun like ancora' : 'No likes yet'}</p>
                </div>
              ) : (
                <div className="space-y-2 pr-2">
                  {likers.map((liker, idx) => (
                    <div 
                      key={idx} 
                      className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors"
                      onClick={() => { setShowLikersPopup(false); navigate(`/player/${liker.user_id}`); }}
                    >
                      <img 
                        src={liker.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${liker.nickname}`} 
                        alt={liker.nickname}
                        className="w-10 h-10 rounded-full"
                      />
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{liker.nickname}</p>
                        <p className="text-xs text-gray-400">{liker.production_house}</p>
                      </div>
                      <div className="text-[10px] text-gray-500">
                        {new Date(liker.liked_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </motion.div>
        </div>
      )}
      
      {/* End of Run Expectations Popup */}
      {showEndRunPopup && endRunData && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4" onClick={() => setShowEndRunPopup(false)}>
          <motion.div
            initial={{ scale: 0.8, opacity: 0, y: 50 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            transition={{ type: 'spring', duration: 0.6 }}
            className={`bg-gradient-to-br ${
              endRunData.exceeded ? 'from-yellow-500/30 to-amber-500/30 border-yellow-500' :
              endRunData.met_expectations ? 'from-green-500/30 to-emerald-500/30 border-green-500' :
              'from-red-500/30 to-orange-500/30 border-red-500'
            } border-2 rounded-2xl p-6 max-w-md w-full text-center relative overflow-hidden`}
            onClick={e => e.stopPropagation()}
            data-testid="end-run-popup"
          >
            {/* Background decoration */}
            {endRunData.exceeded && (
              <div className="absolute inset-0 overflow-hidden pointer-events-none">
                {[...Array(20)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="absolute text-2xl"
                    initial={{ y: -20, x: Math.random() * 300, opacity: 0 }}
                    animate={{ y: 400, opacity: [0, 1, 1, 0], rotate: 360 }}
                    transition={{ duration: 3, delay: i * 0.15, repeat: Infinity }}
                  >
                    {['🎉', '⭐', '🏆', '✨'][i % 4]}
                  </motion.div>
                ))}
              </div>
            )}
            
            {/* Main icon */}
            <motion.div 
              className="text-6xl mb-4"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              {endRunData.exceeded ? '🏆' : endRunData.met_expectations ? '✅' : '📊'}
            </motion.div>
            
            {/* Title */}
            <h2 className={`font-['Bebas_Neue'] text-3xl mb-2 ${
              endRunData.exceeded ? 'text-yellow-400' :
              endRunData.met_expectations ? 'text-green-400' : 'text-orange-400'
            }`}>
              {language === 'it' ? 'Programmazione Terminata!' : 'Theater Run Complete!'}
            </h2>
            
            {/* Film title */}
            <p className="text-lg text-gray-300 mb-4">"{endRunData.film_title}"</p>
            
            {/* Tier Badge */}
            {endRunData.tier && endRunData.tier !== 'normal' && (
              <div className={`inline-block px-4 py-1 rounded-full mb-4 ${
                endRunData.tier === 'masterpiece' ? 'bg-yellow-500/30 text-yellow-400' :
                endRunData.tier === 'epic' ? 'bg-purple-500/30 text-purple-400' :
                endRunData.tier === 'excellent' ? 'bg-blue-500/30 text-blue-400' :
                endRunData.tier === 'promising' ? 'bg-green-500/30 text-green-400' :
                endRunData.tier === 'flop' ? 'bg-red-500/30 text-red-400' : 'bg-gray-500/30 text-gray-400'
              }`}>
                {endRunData.film_tier_info?.emoji} {endRunData.film_tier_info?.name || endRunData.tier}
              </div>
            )}
            
            {/* Stats comparison */}
            <div className="bg-black/30 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">{language === 'it' ? 'Previsto' : 'Expected'}</p>
                  <p className="text-xl font-bold text-gray-300">${endRunData.expected_revenue?.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">{language === 'it' ? 'Effettivo' : 'Actual'}</p>
                  <p className={`text-xl font-bold ${
                    endRunData.ratio >= 1 ? 'text-green-400' : 'text-red-400'
                  }`}>${endRunData.actual_revenue?.toLocaleString()}</p>
                </div>
              </div>
              
              {/* Performance ratio bar */}
              <div className="relative h-4 bg-black/40 rounded-full overflow-hidden mb-2">
                <motion.div 
                  className={`absolute h-full rounded-full ${
                    endRunData.ratio >= 1.2 ? 'bg-yellow-500' :
                    endRunData.ratio >= 1 ? 'bg-green-500' :
                    endRunData.ratio >= 0.8 ? 'bg-orange-500' : 'bg-red-500'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, (endRunData.ratio || 0) * 100)}%` }}
                  transition={{ duration: 1, delay: 0.3 }}
                />
                <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-white/30"></div>
              </div>
              <p className={`text-sm font-bold ${
                endRunData.ratio >= 1.2 ? 'text-yellow-400' :
                endRunData.ratio >= 1 ? 'text-green-400' :
                endRunData.ratio >= 0.8 ? 'text-orange-400' : 'text-red-400'
              }`}>
                {((endRunData.ratio || 0) * 100).toFixed(0)}% {language === 'it' ? 'delle aspettative' : 'of expectations'}
              </p>
            </div>
            
            {/* Message */}
            <p className={`text-lg mb-4 ${
              endRunData.message_type === 'success' ? 'text-green-400' :
              endRunData.message_type === 'positive' ? 'text-blue-400' :
              endRunData.message_type === 'negative' ? 'text-red-400' : 'text-gray-300'
            }`}>
              {endRunData.message}
            </p>
            
            {/* Special messages for surprises */}
            {endRunData.exceeded && endRunData.tier === 'flop' && (
              <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3 mb-4">
                <p className="text-yellow-400 font-bold text-sm">
                  {language === 'it' 
                    ? '🎭 Il film che era un "Possibile Flop" è diventato un successo inaspettato!'
                    : '🎭 The "Potential Flop" turned into an unexpected hit!'}
                </p>
              </div>
            )}
            
            {!endRunData.met_expectations && endRunData.tier !== 'flop' && (
              <div className="bg-orange-500/20 border border-orange-500/50 rounded-lg p-3 mb-4">
                <p className="text-orange-400 font-bold text-sm">
                  {language === 'it' 
                    ? '📉 Nonostante le aspettative, il film non ha performato come previsto.'
                    : '📉 Despite expectations, the film underperformed.'}
                </p>
              </div>
            )}
            
            <Button 
              className={`w-full font-bold text-lg py-6 ${
                endRunData.exceeded ? 'bg-yellow-500 hover:bg-yellow-600 text-black' :
                endRunData.met_expectations ? 'bg-green-600 hover:bg-green-700' : 'bg-orange-600 hover:bg-orange-700'
              }`}
              onClick={() => setShowEndRunPopup(false)}
            >
              {language === 'it' ? 'Continua' : 'Continue'}
            </Button>
          </motion.div>
        </div>
      )}
    </div>
  );
};

// Discovered Stars - Hall of Fame with hiring
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
const FeedbackBoard = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('suggestions');
  const [suggestions, setSuggestions] = useState([]);
  const [bugs, setBugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formType, setFormType] = useState('suggestion');
  
  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('feature');
  const [severity, setSeverity] = useState('medium');
  const [steps, setSteps] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, [api]);

  const loadData = async () => {
    try {
      const [sugRes, bugRes] = await Promise.all([
        api.get('/suggestions'),
        api.get('/bug-reports')
      ]);
      setSuggestions(sugRes.data.suggestions || []);
      setBugs(bugRes.data.bug_reports || []);
    } catch (e) {
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitSuggestion = async () => {
    if (!title.trim() || !description.trim()) {
      toast.error(language === 'it' ? 'Compila tutti i campi' : 'Fill all fields');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/suggestions', { title, description, category, is_anonymous: isAnonymous });
      toast.success(res.data.message);
      setTitle('');
      setDescription('');
      setIsAnonymous(false);
      setShowForm(false);
      loadData();
    } catch (e) {
      toast.error('Errore nell\'invio');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitBug = async () => {
    if (!title.trim() || !description.trim()) {
      toast.error(language === 'it' ? 'Compila tutti i campi' : 'Fill all fields');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/bug-reports', { 
        title, 
        description, 
        severity,
        steps_to_reproduce: steps || null,
        is_anonymous: isAnonymous
      });
      toast.success(res.data.message);
      setTitle('');
      setDescription('');
      setSteps('');
      setIsAnonymous(false);
      setShowForm(false);
      loadData();
    } catch (e) {
      toast.error('Errore nell\'invio');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVote = async (suggestionId) => {
    try {
      const res = await api.post(`/suggestions/${suggestionId}/vote`);
      toast.success(res.data.message);
      loadData();
    } catch (e) {
      toast.error('Errore');
    }
  };

  const getCategoryColor = (cat) => {
    const colors = {
      feature: 'bg-blue-500/20 text-blue-400',
      improvement: 'bg-green-500/20 text-green-400',
      ui: 'bg-purple-500/20 text-purple-400',
      gameplay: 'bg-yellow-500/20 text-yellow-400',
      other: 'bg-gray-500/20 text-gray-400'
    };
    return colors[cat] || colors.other;
  };

  const getSeverityColor = (sev) => {
    const colors = {
      low: 'bg-green-500/20 text-green-400',
      medium: 'bg-yellow-500/20 text-yellow-400',
      high: 'bg-orange-500/20 text-orange-400',
      critical: 'bg-red-500/20 text-red-400'
    };
    return colors[sev] || colors.medium;
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-gray-500/20 text-gray-400',
      under_review: 'bg-blue-500/20 text-blue-400',
      approved: 'bg-green-500/20 text-green-400',
      rejected: 'bg-red-500/20 text-red-400',
      implemented: 'bg-purple-500/20 text-purple-400',
      open: 'bg-yellow-500/20 text-yellow-400',
      investigating: 'bg-blue-500/20 text-blue-400',
      in_progress: 'bg-orange-500/20 text-orange-400',
      resolved: 'bg-green-500/20 text-green-400',
      closed: 'bg-gray-500/20 text-gray-400',
      wont_fix: 'bg-red-500/20 text-red-400'
    };
    return colors[status] || colors.pending;
  };

  const getCategoryName = (cat) => {
    const names = {
      feature: language === 'it' ? 'Nuova Funzione' : 'New Feature',
      improvement: language === 'it' ? 'Miglioramento' : 'Improvement',
      ui: 'UI/UX',
      gameplay: 'Gameplay',
      other: language === 'it' ? 'Altro' : 'Other'
    };
    return names[cat] || cat;
  };

  const getStatusName = (status) => {
    const names = {
      pending: language === 'it' ? 'In Attesa' : 'Pending',
      under_review: language === 'it' ? 'In Revisione' : 'Under Review',
      approved: language === 'it' ? 'Approvato' : 'Approved',
      rejected: language === 'it' ? 'Rifiutato' : 'Rejected',
      implemented: language === 'it' ? 'Implementato' : 'Implemented',
      open: language === 'it' ? 'Aperto' : 'Open',
      investigating: language === 'it' ? 'In Analisi' : 'Investigating',
      in_progress: language === 'it' ? 'In Corso' : 'In Progress',
      resolved: language === 'it' ? 'Risolto' : 'Resolved',
      closed: language === 'it' ? 'Chiuso' : 'Closed',
      wont_fix: language === 'it' ? 'Non Risolveremo' : 'Won\'t Fix'
    };
    return names[status] || status;
  };

  if (loading) {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-1/3"></div>
          {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-700 rounded"></div>)}
        </div>
      </div>
    );
  }

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="feedback-board">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="h-8 w-8">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl flex items-center gap-2">
            <MessageSquare className="w-6 h-6 text-cyan-400" />
            {language === 'it' ? 'SUGGERIMENTI & BUG' : 'FEEDBACK & BUGS'}
          </h1>
          <p className="text-sm text-gray-400">
            {language === 'it' ? 'Aiutaci a migliorare il gioco!' : 'Help us improve the game!'}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <Button 
          variant={activeTab === 'suggestions' ? 'default' : 'outline'}
          onClick={() => setActiveTab('suggestions')}
          className={activeTab === 'suggestions' ? 'bg-cyan-500 text-black' : ''}
        >
          <Lightbulb className="w-4 h-4 mr-2" />
          {language === 'it' ? 'Suggerimenti' : 'Suggestions'} ({suggestions.length})
        </Button>
        <Button 
          variant={activeTab === 'bugs' ? 'default' : 'outline'}
          onClick={() => setActiveTab('bugs')}
          className={activeTab === 'bugs' ? 'bg-red-500 text-white' : ''}
        >
          <Bug className="w-4 h-4 mr-2" />
          Bug ({bugs.length})
        </Button>
      </div>

      {/* Add New Button */}
      <div className="mb-4">
        <Button 
          onClick={() => {
            setFormType(activeTab === 'suggestions' ? 'suggestion' : 'bug');
            setShowForm(true);
          }}
          className={activeTab === 'suggestions' ? 'bg-cyan-500 text-black' : 'bg-red-500 text-white'}
        >
          <Plus className="w-4 h-4 mr-2" />
          {activeTab === 'suggestions' 
            ? (language === 'it' ? 'Nuovo Suggerimento' : 'New Suggestion')
            : (language === 'it' ? 'Segnala Bug' : 'Report Bug')
          }
        </Button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowForm(false)}>
          <Card className="bg-[#1A1A1A] border-white/10 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {formType === 'suggestion' ? (
                  <><Lightbulb className="w-5 h-5 text-cyan-400" /> {language === 'it' ? 'Nuovo Suggerimento' : 'New Suggestion'}</>
                ) : (
                  <><Bug className="w-5 h-5 text-red-400" /> {language === 'it' ? 'Segnala Bug' : 'Report Bug'}</>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>{language === 'it' ? 'Titolo' : 'Title'} *</Label>
                <Input 
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder={formType === 'suggestion' 
                    ? (language === 'it' ? 'Es: Aggiungi modalità multiplayer' : 'Ex: Add multiplayer mode')
                    : (language === 'it' ? 'Es: Il pulsante non funziona' : 'Ex: Button not working')
                  }
                  className="bg-black/20 border-white/10"
                />
              </div>
              <div>
                <Label>{language === 'it' ? 'Descrizione' : 'Description'} *</Label>
                <Textarea 
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder={language === 'it' ? 'Descrivi in dettaglio...' : 'Describe in detail...'}
                  className="bg-black/20 border-white/10 min-h-[100px]"
                />
              </div>
              
              {formType === 'suggestion' ? (
                <div>
                  <Label>{language === 'it' ? 'Categoria' : 'Category'}</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger className="bg-black/20 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#1A1A1A]">
                      <SelectItem value="feature">{language === 'it' ? 'Nuova Funzione' : 'New Feature'}</SelectItem>
                      <SelectItem value="improvement">{language === 'it' ? 'Miglioramento' : 'Improvement'}</SelectItem>
                      <SelectItem value="ui">UI/UX</SelectItem>
                      <SelectItem value="gameplay">Gameplay</SelectItem>
                      <SelectItem value="other">{language === 'it' ? 'Altro' : 'Other'}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <>
                  <div>
                    <Label>{language === 'it' ? 'Gravità' : 'Severity'}</Label>
                    <Select value={severity} onValueChange={setSeverity}>
                      <SelectTrigger className="bg-black/20 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1A1A1A]">
                        <SelectItem value="low">{language === 'it' ? 'Bassa' : 'Low'}</SelectItem>
                        <SelectItem value="medium">{language === 'it' ? 'Media' : 'Medium'}</SelectItem>
                        <SelectItem value="high">{language === 'it' ? 'Alta' : 'High'}</SelectItem>
                        <SelectItem value="critical">{language === 'it' ? 'Critica' : 'Critical'}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>{language === 'it' ? 'Passi per Riprodurre (opzionale)' : 'Steps to Reproduce (optional)'}</Label>
                    <Textarea 
                      value={steps}
                      onChange={e => setSteps(e.target.value)}
                      placeholder={language === 'it' ? '1. Vai a...\n2. Clicca su...\n3. Il bug appare' : '1. Go to...\n2. Click on...\n3. Bug appears'}
                      className="bg-black/20 border-white/10 min-h-[80px]"
                    />
                  </div>
                </>
              )}
              
              {/* Anonymous Toggle */}
              <div className="flex items-center gap-3 p-3 bg-black/20 rounded-lg border border-white/10">
                <input 
                  type="checkbox" 
                  id="anonymous-toggle"
                  checked={isAnonymous}
                  onChange={(e) => setIsAnonymous(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-500"
                />
                <label htmlFor="anonymous-toggle" className="flex-1 cursor-pointer">
                  <p className="text-sm font-medium">
                    {language === 'it' ? 'Invia in modo anonimo' : 'Submit anonymously'}
                  </p>
                  <p className="text-xs text-gray-400">
                    {language === 'it' 
                      ? 'Il tuo nome non sarà visibile agli altri giocatori' 
                      : 'Your name won\'t be visible to other players'}
                  </p>
                </label>
                {isAnonymous && <EyeOff className="w-4 h-4 text-gray-400" />}
              </div>
              
              <div className="flex gap-2 pt-2">
                <Button variant="outline" onClick={() => setShowForm(false)} className="flex-1">
                  {language === 'it' ? 'Annulla' : 'Cancel'}
                </Button>
                <Button 
                  onClick={formType === 'suggestion' ? handleSubmitSuggestion : handleSubmitBug}
                  disabled={submitting}
                  className={formType === 'suggestion' ? 'bg-cyan-500 text-black flex-1' : 'bg-red-500 text-white flex-1'}
                >
                  {submitting ? '...' : (language === 'it' ? 'Invia' : 'Submit')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Content */}
      {activeTab === 'suggestions' ? (
        <div className="space-y-3">
          {suggestions.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-8 text-center text-gray-400">
                <Lightbulb className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>{language === 'it' ? 'Nessun suggerimento ancora. Sii il primo!' : 'No suggestions yet. Be the first!'}</p>
              </CardContent>
            </Card>
          ) : (
            suggestions.map(s => (
              <Card key={s.id} className="bg-[#1A1A1A] border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    {/* Vote Column */}
                    <div className="flex flex-col items-center gap-1">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => handleVote(s.id)}
                        className={`h-8 w-8 p-0 ${s.user_has_voted ? 'text-cyan-400' : 'text-gray-400'}`}
                      >
                        <ChevronUp className="w-5 h-5" />
                      </Button>
                      <span className={`font-bold text-lg ${s.votes > 0 ? 'text-cyan-400' : 'text-gray-500'}`}>
                        {s.votes}
                      </span>
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <h3 className="font-semibold">{s.title}</h3>
                        <Badge className={getCategoryColor(s.category)}>{getCategoryName(s.category)}</Badge>
                        <Badge className={getStatusColor(s.status)}>{getStatusName(s.status)}</Badge>
                      </div>
                      <p className="text-sm text-gray-400 mb-2">{s.description}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        {s.is_anonymous ? (
                          <>
                            <EyeOff className="w-3 h-3" />
                            <span className="italic">{language === 'it' ? 'Anonimo' : 'Anonymous'}</span>
                          </>
                        ) : (
                          <>
                            <Avatar className="w-4 h-4">
                              <AvatarImage src={s.user_avatar} />
                              <AvatarFallback className="text-[8px]">{s.user_nickname?.[0]}</AvatarFallback>
                            </Avatar>
                            <span>{s.user_nickname}</span>
                          </>
                        )}
                        <span>•</span>
                        <span>{new Date(s.created_at).toLocaleDateString()}</span>
                      </div>
                      {s.admin_response && (
                        <div className="mt-2 p-2 bg-cyan-500/10 rounded border border-cyan-500/30">
                          <p className="text-xs text-cyan-400 font-semibold mb-1">Risposta Admin:</p>
                          <p className="text-xs text-gray-300">{s.admin_response}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {bugs.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-8 text-center text-gray-400">
                <Bug className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>{language === 'it' ? 'Nessun bug segnalato. Ottimo!' : 'No bugs reported. Great!'}</p>
              </CardContent>
            </Card>
          ) : (
            bugs.map(b => (
              <Card key={b.id} className="bg-[#1A1A1A] border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-start gap-2 mb-2 flex-wrap">
                    <h3 className="font-semibold">{b.title}</h3>
                    <Badge className={getSeverityColor(b.severity)}>
                      {b.severity.toUpperCase()}
                    </Badge>
                    <Badge className={getStatusColor(b.status)}>{getStatusName(b.status)}</Badge>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">{b.description}</p>
                  {b.steps_to_reproduce && (
                    <div className="text-xs text-gray-500 mb-2 p-2 bg-black/20 rounded">
                      <span className="font-semibold">{language === 'it' ? 'Passi per riprodurre:' : 'Steps to reproduce:'}</span>
                      <pre className="whitespace-pre-wrap mt-1">{b.steps_to_reproduce}</pre>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    {b.is_anonymous ? (
                      <>
                        <EyeOff className="w-3 h-3" />
                        <span className="italic">{language === 'it' ? 'Anonimo' : 'Anonymous'}</span>
                      </>
                    ) : (
                      <>
                        <Avatar className="w-4 h-4">
                          <AvatarImage src={b.user_avatar} />
                          <AvatarFallback className="text-[8px]">{b.user_nickname?.[0]}</AvatarFallback>
                        </Avatar>
                        <span>{b.user_nickname}</span>
                      </>
                    )}
                    <span>•</span>
                    <span>{new Date(b.created_at).toLocaleDateString()}</span>
                  </div>
                  {b.admin_response && (
                    <div className="mt-2 p-2 bg-green-500/10 rounded border border-green-500/30">
                      <p className="text-xs text-green-400 font-semibold mb-1">Risposta Admin:</p>
                      <p className="text-xs text-gray-300">{b.admin_response}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// Cinema Journal - Newspaper style film reviews
const CinemaJournal = () => {
  const { api, user } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [films, setFilms] = useState([]);
  const [news, setNews] = useState([]);
  const [discoveredStars, setDiscoveredStars] = useState([]);
  const [recentTrailers, setRecentTrailers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [comment, setComment] = useState('');
  const navigate = useNavigate();

  useEffect(() => { 
    Promise.all([
      api.get('/films/cinema-journal'),
      api.get('/cinema-news'),
      api.get('/discovered-stars')
    ]).then(([filmsRes, newsRes, starsRes]) => {
      setFilms(filmsRes.data.films);
      setRecentTrailers(filmsRes.data.recent_trailers || []);
      setNews(newsRes.data.news || []);
      setDiscoveredStars(starsRes.data.stars || []);
    }).finally(() => setLoading(false)); 
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

  return (
    <div className="pt-16 pb-20 px-3 max-w-5xl mx-auto" data-testid="cinema-journal-page">
      <div className="text-center mb-6">
        <h1 className="font-['Playfair_Display'] text-4xl md:text-5xl font-bold italic tracking-tight">
          {t('cinema_journal')}
        </h1>
        <div className="flex items-center justify-center gap-2 mt-2">
          <div className="h-px w-16 bg-yellow-500/50" />
          <Newspaper className="w-4 h-4 text-yellow-500" />
          <div className="h-px w-16 bg-yellow-500/50" />
        </div>
        <p className="text-gray-400 text-sm mt-2 italic">The finest productions, ranked by excellence</p>
      </div>

      {/* Recent Trailers Section */}
      {recentTrailers.length > 0 && (
        <Card className="bg-gradient-to-r from-pink-500/10 to-purple-500/10 border-purple-500/30 mb-6 overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Film className="w-5 h-5 text-purple-400" />
              <h2 className="font-['Bebas_Neue'] text-xl tracking-wide">{language === 'it' ? 'NUOVI TRAILER' : 'NEW TRAILERS'}</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {recentTrailers.slice(0, 5).map(film => (
                <div 
                  key={film.id} 
                  onClick={() => navigate(`/film/${film.id}`)}
                  className="relative group cursor-pointer rounded-lg overflow-hidden bg-black/30 hover:bg-black/50 transition-colors"
                >
                  <div className="aspect-video relative">
                    {film.poster_url ? (
                      <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                        <Film className="w-10 h-10 text-purple-400" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="bg-purple-500 rounded-full p-3">
                        <Clapperboard className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <Badge className="absolute top-2 right-2 bg-purple-500/80 text-white text-xs">
                      TRAILER
                    </Badge>
                  </div>
                  <div className="p-2">
                    <h3 className="font-semibold text-sm truncate">{film.title}</h3>
                    <p className="text-xs text-gray-400">{film.owner?.production_house_name || 'Unknown Studio'}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Breaking News - Star Discoveries */}
      {news.length > 0 && (
        <Card className="bg-gradient-to-r from-yellow-500/10 to-purple-500/10 border-yellow-500/30 mb-6 overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-yellow-500" />
              <h2 className="font-['Bebas_Neue'] text-xl tracking-wide">BREAKING NEWS</h2>
            </div>
            <div className="space-y-3">
              {news.slice(0, 3).map(item => (
                <div key={item.id} className="flex items-start gap-3 p-3 bg-black/30 rounded-lg">
                  {item.person_avatar && (
                    <Avatar className="w-12 h-12 ring-2 ring-yellow-500">
                      <AvatarImage src={item.person_avatar} />
                      <AvatarFallback className="bg-yellow-500/20 text-yellow-500">{item.person_name?.[0]}</AvatarFallback>
                    </Avatar>
                  )}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-yellow-500">{item.title_localized}</h3>
                      {item.importance === 'high' && <Badge className="bg-red-500/20 text-red-400 text-[10px]">HOT</Badge>}
                    </div>
                    <p className="text-sm text-gray-300 mt-1">{item.content_localized}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                      <span>Scoperto da {item.discoverer_name}</span>
                      <span>•</span>
                      <span>{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Discovered Stars Hall of Fame */}
      {discoveredStars.length > 0 && (
        <Card className="bg-[#1A1A1A] border-purple-500/30 mb-6">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Award className="w-5 h-5 text-purple-400" />
              <h2 className="font-['Bebas_Neue'] text-xl tracking-wide">HALL OF FAME - STELLE SCOPERTE</h2>
            </div>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {discoveredStars.slice(0, 8).map(star => (
                <div key={star.id} className="flex-shrink-0 w-24 text-center">
                  <Avatar className="w-16 h-16 mx-auto ring-2 ring-purple-500">
                    <AvatarImage src={star.avatar_url} />
                    <AvatarFallback className="bg-purple-500/20 text-purple-400">{star.name?.[0]}</AvatarFallback>
                  </Avatar>
                  <p className="text-xs font-semibold mt-1 truncate">{star.name}</p>
                  <p className="text-[10px] text-gray-500">by {star.discoverer?.nickname}</p>
                  <Badge className="bg-purple-500/20 text-purple-400 text-[10px] mt-1">Superstar</Badge>
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
const CineBoard = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const [activeTab, setActiveTab] = useState('now_playing');
  const [films, setFilms] = useState([]);
  const [attendanceData, setAttendanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const t = (key) => {
    const translations = {
      cineboard: language === 'it' ? 'CineBoard' : 'CineBoard',
      nowPlaying: language === 'it' ? 'In Sala (Top 50)' : 'Now Playing (Top 50)',
      hallOfFame: language === 'it' ? 'Hall of Fame' : 'Hall of Fame',
      attendance: language === 'it' ? 'Affluenze' : 'Attendance',
      rank: language === 'it' ? 'Pos' : 'Rank',
      score: language === 'it' ? 'Punteggio' : 'Score',
      noFilms: language === 'it' ? 'Nessun film in classifica' : 'No films in rankings',
      quality: language === 'it' ? 'Qualità' : 'Quality',
      revenue: language === 'it' ? 'Incassi' : 'Revenue',
      likes: language === 'it' ? 'Like' : 'Likes'
    };
    return translations[key] || key;
  };

  useEffect(() => {
    setLoading(true);
    if (activeTab === 'attendance') {
      api.get('/cineboard/attendance')
        .then(r => setAttendanceData(r.data))
        .catch(() => setAttendanceData(null))
        .finally(() => setLoading(false));
    } else {
      const endpoint = activeTab === 'now_playing' ? '/cineboard/now-playing' : '/cineboard/hall-of-fame';
      api.get(endpoint)
        .then(r => setFilms(r.data.films || []))
        .catch(() => setFilms([]))
        .finally(() => setLoading(false));
    }
  }, [api, activeTab]);

  const handleLike = async (filmId) => {
    try {
      const res = await api.post(`/films/${filmId}/like`);
      setFilms(films.map(f => f.id === filmId ? { ...f, user_liked: res.data.liked, likes_count: res.data.likes_count } : f));
    } catch (e) {
      if (e.response?.data?.detail?.includes('tuoi film')) {
        toast.error(language === 'it' ? 'Non puoi mettere like ai tuoi film!' : "You can't like your own films!");
      } else {
        console.error(e);
      }
    }
  };

  const getRankBadge = (rank) => {
    if (rank === 1) return 'bg-yellow-500 text-black';
    if (rank === 2) return 'bg-gray-300 text-black';
    if (rank === 3) return 'bg-amber-600 text-white';
    if (rank <= 10) return 'bg-purple-500/20 text-purple-400';
    return 'bg-white/10 text-gray-400';
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="cineboard-page">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <Trophy className="w-8 h-8 text-yellow-500" />
        <div>
          <h1 className="font-['Bebas_Neue'] text-3xl">{t('cineboard')}</h1>
          <p className="text-xs text-gray-400">
            {language === 'it' ? 'Classifica film basata su qualità, incassi, popolarità e premi' : 'Film rankings based on quality, revenue, popularity and awards'}
          </p>
        </div>
      </div>
      
      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-4">
        <TabsList className="grid w-full grid-cols-3 bg-[#1A1A1A]">
          <TabsTrigger value="now_playing" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black text-xs sm:text-sm">
            <Film className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">{t('nowPlaying')}</span>
            <span className="sm:hidden">Top 50</span>
          </TabsTrigger>
          <TabsTrigger value="hall_of_fame" className="data-[state=active]:bg-purple-500 data-[state=active]:text-white text-xs sm:text-sm">
            <Award className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">{t('hallOfFame')}</span>
            <span className="sm:hidden">Fame</span>
          </TabsTrigger>
          <TabsTrigger value="attendance" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white text-xs sm:text-sm">
            <Users className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">{t('attendance')}</span>
            <span className="sm:hidden">Affluenza</span>
          </TabsTrigger>
        </TabsList>
      </Tabs>
      
      {/* Score Legend */}
      <Card className="bg-[#1A1A1A] border-white/10 p-3 mb-4">
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-gray-400">{language === 'it' ? 'Qualità 30%' : 'Quality 30%'}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-gray-400">{language === 'it' ? 'Incassi 25%' : 'Revenue 25%'}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-pink-500"></div>
            <span className="text-gray-400">{language === 'it' ? 'Popolarità 20%' : 'Popularity 20%'}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span className="text-gray-400">{language === 'it' ? 'Premi 15%' : 'Awards 15%'}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="text-gray-400">{language === 'it' ? 'Longevità 10%' : 'Longevity 10%'}</span>
          </div>
        </div>
      </Card>
      
      {/* Film List - Only for now_playing and hall_of_fame tabs */}
      {activeTab !== 'attendance' && (loading ? (
        <div className="text-center py-8 text-gray-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
          {language === 'it' ? 'Caricamento classifica...' : 'Loading rankings...'}
        </div>
      ) : films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
          <Film className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <h3 className="text-lg mb-2">{t('noFilms')}</h3>
        </Card>
      ) : (
        <div className="space-y-2">
          {films.map((film, index) => (
            <Card key={film.id} className={`bg-[#1A1A1A] border-white/10 overflow-hidden ${film.rank <= 3 ? 'border-yellow-500/30' : ''}`}>
              <div className="flex">
                {/* Rank Badge */}
                <div className={`w-12 flex items-center justify-center ${getRankBadge(film.rank)} font-bold text-lg`}>
                  #{film.rank}
                </div>
                
                {/* Poster */}
                <div className="w-20 flex-shrink-0 cursor-pointer" onClick={() => navigate(`/films/${film.id}`)}>
                  <img 
                    src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300'} 
                    alt={film.title} 
                    className="w-full h-full object-cover"
                  />
                </div>
                
                {/* Info */}
                <CardContent className="flex-1 p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 
                        className="font-semibold text-sm cursor-pointer hover:text-yellow-500 truncate" 
                        onClick={() => navigate(`/films/${film.id}`)}
                      >
                        {film.title}
                      </h3>
                      <p className="text-[10px] text-gray-400 truncate">
                        {film.owner?.production_house_name || 'Unknown Studio'}
                      </p>
                    </div>
                    
                    {/* IMDb-style Rating */}
                    <div className="flex items-center gap-1 bg-yellow-500/20 px-2 py-1 rounded ml-2">
                      <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
                      <span className="font-bold text-yellow-500 text-sm">{film.imdb_rating?.toFixed(1) || '0.0'}</span>
                    </div>
                  </div>
                  
                  {/* Stats Row */}
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <Badge className="bg-white/10 text-gray-300 text-[10px] h-5">{film.genre}</Badge>
                    <span className="text-[10px] text-yellow-400"><Star className="w-3 h-3 inline" /> {film.quality_score?.toFixed(0)}%</span>
                    <span className="text-[10px] text-green-400">${((film.total_revenue || 0) / 1000000).toFixed(1)}M</span>
                    
                    {/* CineBoard Score */}
                    <div className="ml-auto flex items-center gap-1">
                      <span className="text-[10px] text-gray-500">{t('score')}:</span>
                      <span className={`font-bold text-sm ${film.cineboard_score >= 70 ? 'text-yellow-400' : film.cineboard_score >= 50 ? 'text-green-400' : 'text-gray-400'}`}>
                        {film.cineboard_score?.toFixed(1)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Action Row */}
                  <div className="flex items-center gap-2 mt-2">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className={`h-6 px-2 ${film.user_liked ? 'text-red-400' : 'text-gray-400'}`} 
                      onClick={() => handleLike(film.id)}
                    >
                      <Heart className={`w-3.5 h-3.5 mr-1 ${film.user_liked ? 'fill-red-400' : ''}`} /> 
                      {film.likes_count || 0}
                    </Button>
                    
                    {film.hall_of_fame && (
                      <Badge className="bg-purple-500/20 text-purple-400 text-[10px]">
                        <Trophy className="w-3 h-3 mr-1" /> Hall of Fame
                      </Badge>
                    )}
                    
                    {film.awards?.length > 0 && (
                      <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">
                        <Award className="w-3 h-3 mr-1" /> {film.awards.length}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </div>
            </Card>
          ))}
        </div>
      ))}

      {/* Attendance Tab Content */}
      {activeTab === 'attendance' && (
        loading ? (
          <div className="text-center py-8 text-gray-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
            {language === 'it' ? 'Caricamento affluenze...' : 'Loading attendance data...'}
          </div>
        ) : !attendanceData ? (
          <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
            <Users className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <h3 className="text-lg mb-2">{language === 'it' ? 'Nessun dato disponibile' : 'No data available'}</h3>
          </Card>
        ) : (
        <div className="space-y-4">
          {/* Global Stats */}
          <Card className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/30">
            <CardContent className="p-4">
              <h3 className="font-['Bebas_Neue'] text-lg mb-3 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                {language === 'it' ? 'Statistiche Globali' : 'Global Stats'}
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="text-center p-3 rounded-lg bg-black/20">
                  <p className="text-2xl font-bold text-blue-400">{attendanceData.global_stats?.total_films_in_theaters || 0}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Film in Sala' : 'Films Showing'}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-black/20">
                  <p className="text-2xl font-bold text-green-400">{(attendanceData.global_stats?.total_cinemas_showing || 0).toLocaleString()}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Cinema Totali' : 'Total Cinemas'}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-black/20">
                  <p className="text-2xl font-bold text-purple-400">{(attendanceData.global_stats?.total_current_attendance || 0).toLocaleString()}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Spettatori Ora' : 'Current Viewers'}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-black/20">
                  <p className="text-2xl font-bold text-yellow-400">{attendanceData.global_stats?.avg_attendance_per_cinema || 0}</p>
                  <p className="text-xs text-gray-400">{language === 'it' ? 'Media/Cinema' : 'Avg/Cinema'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Top 20 Now Playing */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <Film className="w-5 h-5 text-yellow-500" />
                {language === 'it' ? 'Top 20 - Più Programmati (Ora)' : 'Top 20 - Most Screened (Now)'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {attendanceData.top_now_playing?.length === 0 ? (
                <p className="text-center text-gray-400 py-4">{language === 'it' ? 'Nessun film in programmazione' : 'No films currently showing'}</p>
              ) : (
                attendanceData.top_now_playing?.map((film, idx) => (
                  <div 
                    key={film.id} 
                    className="flex items-center gap-3 p-2 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors"
                    onClick={() => navigate(`/film/${film.id}`)}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      idx === 0 ? 'bg-yellow-500 text-black' :
                      idx === 1 ? 'bg-gray-300 text-black' :
                      idx === 2 ? 'bg-amber-600 text-white' :
                      'bg-white/10 text-gray-400'
                    }`}>
                      {film.rank}
                    </div>
                    <div className="w-10 h-14 rounded bg-gray-800 overflow-hidden flex-shrink-0">
                      {film.poster_url && <img src={film.poster_url} alt="" className="w-full h-full object-cover" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate">{film.title}</p>
                      <p className="text-xs text-gray-400 truncate">{film.owner?.production_house_name || film.owner?.nickname}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-blue-400">{film.current_cinemas}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'cinema' : 'cinemas'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-400">{film.current_attendance?.toLocaleString()}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'spettatori' : 'viewers'}</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Top 20 All-Time */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                <Trophy className="w-5 h-5 text-purple-500" />
                {language === 'it' ? 'Top 20 - Più Programmati (All-Time)' : 'Top 20 - Most Screened (All-Time)'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {attendanceData.top_all_time?.length === 0 ? (
                <p className="text-center text-gray-400 py-4">{language === 'it' ? 'Nessun dato storico' : 'No historical data'}</p>
              ) : (
                attendanceData.top_all_time?.map((film, idx) => (
                  <div 
                    key={film.id} 
                    className="flex items-center gap-3 p-2 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors"
                    onClick={() => navigate(`/film/${film.id}`)}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      idx === 0 ? 'bg-yellow-500 text-black' :
                      idx === 1 ? 'bg-gray-300 text-black' :
                      idx === 2 ? 'bg-amber-600 text-white' :
                      'bg-white/10 text-gray-400'
                    }`}>
                      {film.rank}
                    </div>
                    <div className="w-10 h-14 rounded bg-gray-800 overflow-hidden flex-shrink-0">
                      {film.poster_url && <img src={film.poster_url} alt="" className="w-full h-full object-cover" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate">{film.title}</p>
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-gray-400 truncate">{film.owner?.production_house_name || film.owner?.nickname}</p>
                        <Badge className={`text-[9px] ${film.status === 'in_theaters' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                          {film.status === 'in_theaters' ? (language === 'it' ? 'In Sala' : 'Showing') : (language === 'it' ? 'Archivio' : 'Archive')}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-purple-400">{(film.total_screenings || 0).toLocaleString()}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'proiezioni' : 'screenings'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-cyan-400">{(film.cumulative_attendance || 0).toLocaleString()}</p>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'totale spett.' : 'total viewers'}</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
        )
      )}
    </div>
  );
};

// Chat Page
const ChatPage = () => {
  const { api, user } = useContext(AuthContext);
  const { t } = useTranslations();
  const [rooms, setRooms] = useState({ public: [], private: [] });
  const [activeRoom, setActiveRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [activeTab, setActiveTab] = useState('public');
  const [showUsers, setShowUsers] = useState(false);
  const [loadingDM, setLoadingDM] = useState(null);
  
  // User profile modal state
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [showUserProfile, setShowUserProfile] = useState(false);

  // Fetch rooms and online users
  useEffect(() => {
    const fetchData = async () => {
      const [roomsRes, onlineRes, allUsersRes] = await Promise.all([
        api.get('/chat/rooms'),
        api.get('/users/online'),
        api.get('/users/all')
      ]);
      setRooms(roomsRes.data);
      setOnlineUsers(onlineRes.data);
      setAllUsers(allUsersRes.data);
      if (roomsRes.data.public.length > 0 && !activeRoom) {
        setActiveRoom(roomsRes.data.public[0]);
      }
    };
    fetchData();
  }, [api]);

  // Heartbeat to track online status
  useEffect(() => {
    const heartbeat = async () => {
      try { await api.post('/users/heartbeat'); } catch(e) {}
    };
    heartbeat();
    const interval = setInterval(heartbeat, 60000);
    return () => clearInterval(interval);
  }, [api]);

  // Refresh online users periodically
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [onlineRes, roomsRes] = await Promise.all([
          api.get('/users/online'),
          api.get('/chat/rooms')
        ]);
        setOnlineUsers(onlineRes.data);
        setRooms(roomsRes.data);
      } catch(e) {}
    }, 30000);
    return () => clearInterval(interval);
  }, [api]);

  // Fetch messages when room changes
  useEffect(() => {
    if (activeRoom) {
      api.get(`/chat/rooms/${activeRoom.id}/messages`).then(r => setMessages(r.data));
    }
  }, [activeRoom, api]);

  // Auto-refresh messages
  useEffect(() => {
    if (!activeRoom) return;
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/chat/rooms/${activeRoom.id}/messages`);
        setMessages(res.data);
      } catch(e) {}
    }, 5000);
    return () => clearInterval(interval);
  }, [activeRoom, api]);

  const sendMessage = async () => {
    if (!newMessage.trim() || !activeRoom) return;
    await api.post('/chat/messages', { room_id: activeRoom.id, content: newMessage, message_type: 'text' });
    setNewMessage('');
    const res = await api.get(`/chat/rooms/${activeRoom.id}/messages`);
    setMessages(res.data);
  };

  const startDirectMessage = async (targetUserId) => {
    setLoadingDM(targetUserId);
    try {
      const res = await api.post(`/chat/direct/${targetUserId}`);
      // Refresh rooms to include the new private chat
      const roomsRes = await api.get('/chat/rooms');
      setRooms(roomsRes.data);
      setActiveRoom(res.data);
      setActiveTab('private');
      setShowUsers(false);
    } catch(e) {
      toast.error('Could not start chat');
    } finally {
      setLoadingDM(null);
    }
  };

  const OnlineIndicator = ({ isOnline }) => (
    <span className={`inline-block w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-gray-500'}`} />
  );

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto h-[calc(100vh-5rem)]" data-testid="chat-page">
      <div className="grid lg:grid-cols-4 gap-3 h-full">
        {/* Sidebar */}
        <Card className="bg-[#1A1A1A] border-white/10 lg:col-span-1 flex flex-col">
          <CardHeader className="pb-2 pt-3 px-3">
            <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center justify-between">
              {t('chat')}
              <Button variant="ghost" size="sm" className="h-6 px-2" onClick={() => setShowUsers(!showUsers)} data-testid="toggle-users-btn">
                <Users className="w-3 h-3 mr-1" />
                <span className="text-xs text-green-500">{onlineUsers.length}</span>
              </Button>
            </CardTitle>
          </CardHeader>
          
          {showUsers ? (
            <CardContent className="p-2 flex-1 overflow-hidden">
              <p className="text-xs text-gray-400 mb-2 px-1">Online Users ({onlineUsers.length})</p>
              <ScrollArea className="h-full">
                <div className="space-y-1">
                  {onlineUsers.length === 0 ? (
                    <p className="text-xs text-gray-500 text-center py-4">No users online</p>
                  ) : (
                    onlineUsers.map(u => (
                      <div
                        key={u.id}
                        className="w-full flex items-center gap-2 p-2 rounded hover:bg-white/5"
                        data-testid={`user-row-${u.id}`}
                      >
                        {/* Clickable avatar and name - opens profile */}
                        <button 
                          onClick={() => { if (!u.is_bot) { setSelectedUserId(u.id); setShowUserProfile(true); }}}
                          className="flex items-center gap-2 flex-1 min-w-0 text-left"
                          disabled={u.is_bot}
                        >
                          <Avatar className="w-7 h-7 cursor-pointer">
                            <AvatarImage src={u.avatar_url} />
                            <AvatarFallback className="text-xs bg-yellow-500/20 text-yellow-500">{u.nickname?.[0]}</AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1">
                              <OnlineIndicator isOnline={true} />
                              <span className="text-xs font-semibold truncate hover:text-yellow-500 cursor-pointer">{u.nickname}</span>
                              {u.is_bot && u.is_moderator && <Badge className="h-4 px-1 text-[10px] bg-red-500/20 text-red-400">MOD</Badge>}
                              {u.is_bot && !u.is_moderator && <Badge className="h-4 px-1 text-[10px] bg-blue-500/20 text-blue-400">BOT</Badge>}
                            </div>
                            <p className="text-xs text-gray-500 truncate">{u.is_bot ? u.role : u.production_house_name}</p>
                          </div>
                        </button>
                        {/* DM button */}
                        {!u.is_bot && (
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="h-7 w-7 p-0"
                            onClick={() => startDirectMessage(u.id)}
                            disabled={loadingDM === u.id}
                            data-testid={`dm-user-${u.id}`}
                          >
                            {loadingDM === u.id ? (
                              <span className="text-xs text-gray-400">...</span>
                            ) : (
                              <MessageSquare className="w-3.5 h-3.5 text-gray-400 hover:text-yellow-500" />
                            )}
                          </Button>
                        )}
                      </div>
                    ))
                  )}
                  
                  {allUsers.filter(u => !onlineUsers.some(o => o.id === u.id)).length > 0 && (
                    <>
                      <p className="text-xs text-gray-400 mt-3 mb-2 px-1 border-t border-white/10 pt-2">All Users</p>
                      {allUsers.filter(u => !onlineUsers.some(o => o.id === u.id)).slice(0, 10).map(u => (
                        <div
                          key={u.id}
                          className="w-full flex items-center gap-2 p-2 rounded hover:bg-white/5 opacity-60"
                          data-testid={`user-row-${u.id}`}
                        >
                          {/* Clickable avatar and name - opens profile */}
                          <button 
                            onClick={() => { setSelectedUserId(u.id); setShowUserProfile(true); }}
                            className="flex items-center gap-2 flex-1 min-w-0 text-left"
                          >
                            <Avatar className="w-7 h-7 cursor-pointer">
                              <AvatarImage src={u.avatar_url} />
                              <AvatarFallback className="text-xs bg-gray-500/20">{u.nickname?.[0]}</AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1">
                                <OnlineIndicator isOnline={false} />
                                <span className="text-xs truncate hover:text-yellow-500 cursor-pointer">{u.nickname}</span>
                              </div>
                            </div>
                          </button>
                          {/* DM button */}
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="h-7 w-7 p-0"
                            onClick={() => startDirectMessage(u.id)}
                            disabled={loadingDM === u.id}
                            data-testid={`dm-user-${u.id}`}
                          >
                            <MessageSquare className="w-3.5 h-3.5 text-gray-500 hover:text-yellow-500" />
                          </Button>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          ) : (
            <CardContent className="p-2 flex-1 overflow-hidden">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="w-full h-7 mb-2">
                  <TabsTrigger value="public" className="flex-1 text-xs h-6">Public</TabsTrigger>
                  <TabsTrigger value="private" className="flex-1 text-xs h-6">
                    Private {rooms.private.length > 0 && <Badge className="ml-1 h-4 px-1 text-xs bg-yellow-500/20 text-yellow-500">{rooms.private.length}</Badge>}
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="public" className="mt-0">
                  <ScrollArea className="h-[calc(100%-2rem)]">
                    {rooms.public.map(room => (
                      <button
                        key={room.id}
                        className={`w-full text-left p-2 rounded text-sm mb-1 ${activeRoom?.id === room.id ? 'bg-yellow-500/20 text-yellow-500' : 'hover:bg-white/5'}`}
                        onClick={() => setActiveRoom(room)}
                        data-testid={`room-${room.id}`}
                      >
                        <MessageSquare className="w-3 h-3 inline mr-2" />{room.name}
                      </button>
                    ))}
                  </ScrollArea>
                </TabsContent>
                
                <TabsContent value="private" className="mt-0">
                  <ScrollArea className="h-[calc(100%-2rem)]">
                    {rooms.private.length === 0 ? (
                      <div className="text-center py-4">
                        <p className="text-xs text-gray-500 mb-2">No private chats</p>
                        <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setShowUsers(true)}>
                          <Users className="w-3 h-3 mr-1" /> Start a chat
                        </Button>
                      </div>
                    ) : (
                      rooms.private.map(room => (
                        <button
                          key={room.id}
                          className={`w-full text-left p-2 rounded mb-1 ${activeRoom?.id === room.id ? 'bg-yellow-500/20' : 'hover:bg-white/5'}`}
                          onClick={() => setActiveRoom(room)}
                          data-testid={`private-room-${room.id}`}
                        >
                          <div className="flex items-center gap-2">
                            <Avatar className="w-6 h-6">
                              <AvatarImage src={room.other_user?.avatar_url} />
                              <AvatarFallback className="text-xs">{room.other_user?.nickname?.[0]}</AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1">
                                <OnlineIndicator isOnline={room.other_user?.is_online} />
                                <span className={`text-xs font-semibold truncate ${activeRoom?.id === room.id ? 'text-yellow-500' : ''}`}>
                                  {room.other_user?.nickname}
                                </span>
                              </div>
                              {room.last_message && (
                                <p className="text-xs text-gray-500 truncate">{room.last_message.content}</p>
                              )}
                            </div>
                          </div>
                        </button>
                      ))
                    )}
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            </CardContent>
          )}
        </Card>

        {/* Chat Area */}
        <Card className="bg-[#1A1A1A] border-white/10 lg:col-span-3 flex flex-col">
          {activeRoom ? (
            <>
              <CardHeader className="pb-2 pt-3 px-3 border-b border-white/10">
                <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                  {activeRoom.is_private && activeRoom.other_user ? (
                    <>
                      <Avatar className="w-6 h-6">
                        <AvatarImage src={activeRoom.other_user.avatar_url} />
                        <AvatarFallback className="text-xs">{activeRoom.other_user.nickname?.[0]}</AvatarFallback>
                      </Avatar>
                      <span>{activeRoom.other_user.nickname}</span>
                      <OnlineIndicator isOnline={activeRoom.other_user.is_online} />
                    </>
                  ) : (
                    <><MessageSquare className="w-4 h-4" /> {activeRoom.name}</>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 p-3 overflow-hidden flex flex-col">
                <ScrollArea className="flex-1">
                  <div className="space-y-2">
                    {messages.length === 0 ? (
                      <div className="text-center py-8 text-gray-500 text-sm">
                        No messages yet. Start the conversation!
                      </div>
                    ) : (
                      messages.map(msg => (
                        <div key={msg.id} className={`flex ${msg.sender_id === user.id ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[70%] px-3 py-1.5 rounded-xl text-sm ${
                            msg.message_type === 'trailer_announcement' 
                              ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-bl-sm cursor-pointer hover:from-purple-500/30 hover:to-pink-500/30'
                              : msg.sender_id === user.id 
                                ? 'bg-yellow-500 text-black rounded-br-sm' 
                                : msg.sender?.is_bot 
                                  ? 'bg-blue-500/20 border border-blue-500/30 rounded-bl-sm' 
                                  : 'bg-white/10 rounded-bl-sm'
                          }`}
                          onClick={() => msg.message_type === 'trailer_announcement' && msg.film_id && navigate(`/film/${msg.film_id}`)}
                          >
                            {msg.sender_id !== user.id && !activeRoom.is_private && (
                              <div className="flex items-center gap-1 mb-0.5">
                                <p className="text-xs font-semibold">{msg.sender?.nickname || msg.user?.nickname}</p>
                                {(msg.sender?.is_bot || msg.user_id === 'system_bot') && <Badge className="h-3 px-1 text-[8px] bg-blue-500/30 text-blue-400">BOT</Badge>}
                              </div>
                            )}
                            {msg.message_type === 'trailer_announcement' ? (
                              <div className="flex items-center gap-2">
                                <Film className="w-5 h-5 text-purple-400" />
                                <div>
                                  <p>{msg.content}</p>
                                  <p className="text-xs text-purple-300 mt-1">{language === 'it' ? 'Clicca per vedere' : 'Click to watch'}</p>
                                </div>
                              </div>
                            ) : (
                              <p>{msg.content}</p>
                            )}
                            <p className={`text-xs mt-0.5 ${msg.sender_id === user.id ? 'text-black/50' : 'text-gray-500'}`}>
                              {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
                <div className="flex gap-2 mt-2 pt-2 border-t border-white/10">
                  <Input
                    value={newMessage}
                    onChange={e => setNewMessage(e.target.value)}
                    placeholder="Type a message..."
                    className="h-8 bg-black/20 border-white/10"
                    onKeyPress={e => e.key === 'Enter' && sendMessage()}
                    data-testid="chat-input"
                  />
                  <Button onClick={sendMessage} size="sm" className="bg-yellow-500 text-black h-8 px-3" data-testid="send-message-btn">
                    <Send className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </CardContent>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
              <div className="text-center">
                <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-30" />
                <p>Select a room or start a direct message</p>
              </div>
            </div>
          )}
        </Card>
      </div>
      
      {/* User Profile Modal */}
      <UserProfileModal 
        userId={selectedUserId} 
        isOpen={showUserProfile} 
        onClose={() => setShowUserProfile(false)} 
        api={api}
      />
    </div>
  );
};

// Statistics Page
const StatisticsPage = () => {
  const { api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [globalStats, setGlobalStats] = useState(null);
  const [myStats, setMyStats] = useState(null);

  useEffect(() => { Promise.all([api.get('/statistics/global'), api.get('/statistics/my')]).then(([g, m]) => { setGlobalStats(g.data); setMyStats(m.data); }); }, [api]);

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="statistics-page">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4">{t('statistics')}</h1>
      <Tabs defaultValue="my">
        <TabsList className="mb-3"><TabsTrigger value="my">My Stats</TabsTrigger><TabsTrigger value="global">Global</TabsTrigger></TabsList>
        <TabsContent value="my"><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {[{l:'Films',v:myStats?.total_films||0,i:Film},{l:'Revenue',v:`$${(myStats?.total_revenue||0).toLocaleString()}`,i:DollarSign},{l:'Likes',v:myStats?.total_likes||0,i:Heart},{l:'Quality',v:`${(myStats?.average_quality||0).toFixed(0)}%`,i:Star}].map(s=>(
            <Card key={s.l} className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3"><s.i className="w-5 h-5 mb-1 text-yellow-500" /><p className="text-xl font-bold">{s.v}</p><p className="text-xs text-gray-400">{s.l}</p></CardContent></Card>
          ))}
        </div></TabsContent>
        <TabsContent value="global"><div className="grid sm:grid-cols-3 gap-3">
          <Card className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3"><Film className="w-5 h-5 mb-1 text-yellow-500" /><p className="text-xl font-bold">{globalStats?.total_films||0}</p><p className="text-xs text-gray-400">Total Films</p></CardContent></Card>
          <Card className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3"><Users className="w-5 h-5 mb-1 text-blue-500" /><p className="text-xl font-bold">{globalStats?.total_users||0}</p><p className="text-xs text-gray-400">Producers</p></CardContent></Card>
          <Card className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3"><DollarSign className="w-5 h-5 mb-1 text-green-500" /><p className="text-xl font-bold">${(globalStats?.total_box_office||0).toLocaleString()}</p><p className="text-xs text-gray-400">Box Office</p></CardContent></Card>
        </div></TabsContent>
      </Tabs>
    </div>
  );
};

// Profile Page with AI Avatar Generation
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
              <h2 className="text-base sm:text-lg font-bold">{user?.nickname}</h2>
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
const InfrastructurePage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [infraTypes, setInfraTypes] = useState([]);
  const [myInfra, setMyInfra] = useState({ infrastructure: [], grouped: {} });
  const [cities, setCities] = useState({});
  const [selectedType, setSelectedType] = useState(null);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [customName, setCustomName] = useState('');
  const [purchasing, setPurchasing] = useState(false);
  const [showPurchaseDialog, setShowPurchaseDialog] = useState(false);
  const [levelInfo, setLevelInfo] = useState(null);
  
  // Infrastructure detail dialog state
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedInfra, setSelectedInfra] = useState(null);
  const [infraDetail, setInfraDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [prices, setPrices] = useState({});
  const [savingPrices, setSavingPrices] = useState(false);
  
  // Film management state
  const [showAddFilmDialog, setShowAddFilmDialog] = useState(false);
  const [showRentFilmDialog, setShowRentFilmDialog] = useState(false);
  const [myFilms, setMyFilms] = useState([]);
  const [rentalFilms, setRentalFilms] = useState([]);
  const [selectedFilmToAdd, setSelectedFilmToAdd] = useState(null);
  const [selectedFilmToRent, setSelectedFilmToRent] = useState(null);
  const [rentalWeeks, setRentalWeeks] = useState(1);
  const [addingFilm, setAddingFilm] = useState(false);
  const [rentingFilm, setRentingFilm] = useState(false);
  const [removingFilm, setRemovingFilm] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get('/infrastructure/types'),
      api.get('/infrastructure/my'),
      api.get('/infrastructure/cities'),
      api.get('/player/level-info')
    ]).then(([types, my, citiesData, level]) => {
      setInfraTypes(types.data);
      setMyInfra(my.data);
      setCities(citiesData.data);
      setLevelInfo(level.data);
    });
  }, [api]);

  const getIcon = (iconName) => {
    const icons = { film: Film, car: Car, 'shopping-bag': ShoppingBag, building: Building, 'building-2': Building2, 'graduation-cap': GraduationCap, landmark: Landmark, crown: Crown, award: Award, 'ferris-wheel': Star, clapperboard: Clapperboard };
    return icons[iconName] || Building;
  };

  const handlePurchase = async () => {
    if (!selectedType || !selectedCountry || !selectedCity) return;
    setPurchasing(true);
    try {
      const res = await api.post('/infrastructure/purchase', {
        type: selectedType.id,
        city_name: selectedCity,
        country: selectedCountry,
        custom_name: customName || null
      });
      toast.success(`Acquistato! Hai speso $${res.data.cost.toLocaleString()}`);
      setShowPurchaseDialog(false);
      // Refresh
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Acquisto fallito');
    } finally {
      setPurchasing(false);
    }
  };

  const getCityPrice = () => {
    if (!selectedType || !selectedCountry || !selectedCity) return 0;
    const city = cities[selectedCountry]?.find(c => c.name === selectedCity);
    if (!city) return selectedType.base_cost;
    return Math.round(selectedType.base_cost * city.cost_multiplier);
  };

  const openInfraDetail = async (infra) => {
    setSelectedInfra(infra);
    setLoadingDetail(true);
    setShowDetailDialog(true);
    try {
      const res = await api.get(`/infrastructure/${infra.id}`);
      setInfraDetail(res.data);
      setPrices(res.data.prices || { ticket: 12, popcorn: 8, drinks: 5, combo: 18 });
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nel caricamento');
      setShowDetailDialog(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  const savePrices = async () => {
    if (!selectedInfra) return;
    setSavingPrices(true);
    try {
      await api.put(`/infrastructure/${selectedInfra.id}/prices`, { prices });
      toast.success('Prezzi aggiornati!');
      // Refresh infrastructure list
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setSavingPrices(false);
    }
  };

  const openAddFilmDialog = async () => {
    try {
      const res = await api.get('/films/my-available');
      setMyFilms(res.data);
      setShowAddFilmDialog(true);
    } catch (e) {
      toast.error('Errore nel caricamento dei film');
    }
  };

  const openRentFilmDialog = async () => {
    try {
      const res = await api.get('/films/available-for-rental');
      setRentalFilms(res.data);
      setShowRentFilmDialog(true);
    } catch (e) {
      toast.error('Errore nel caricamento dei film');
    }
  };

  const addFilmToCinema = async () => {
    if (!selectedFilmToAdd || !selectedInfra) return;
    setAddingFilm(true);
    try {
      const res = await api.post(`/infrastructure/${selectedInfra.id}/add-film`, {
        film_id: selectedFilmToAdd.id
      });
      toast.success(`"${selectedFilmToAdd.title}" aggiunto alla programmazione!`);
      setInfraDetail({...infraDetail, films_showing: res.data.films_showing});
      setShowAddFilmDialog(false);
      setSelectedFilmToAdd(null);
      // Refresh my infra
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setAddingFilm(false);
    }
  };

  const rentFilmForCinema = async () => {
    if (!selectedFilmToRent || !selectedInfra) return;
    setRentingFilm(true);
    try {
      const res = await api.post(`/infrastructure/${selectedInfra.id}/rent-film`, {
        film_id: selectedFilmToRent.id,
        weeks: rentalWeeks
      });
      toast.success(`"${selectedFilmToRent.title}" affittato per ${rentalWeeks} settimane! ${res.data.owner_name} ha ricevuto $${res.data.owner_received.toLocaleString()}`);
      setInfraDetail({...infraDetail, films_showing: res.data.films_showing});
      setShowRentFilmDialog(false);
      setSelectedFilmToRent(null);
      setRentalWeeks(1);
      // Refresh my infra and user
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setRentingFilm(false);
    }
  };

  const removeFilmFromCinema = async (filmId) => {
    if (!selectedInfra) return;
    setRemovingFilm(filmId);
    try {
      const res = await api.delete(`/infrastructure/${selectedInfra.id}/films/${filmId}`);
      toast.success('Film rimosso dalla programmazione');
      setInfraDetail({...infraDetail, films_showing: res.data.films_showing});
      // Refresh
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setRemovingFilm(null);
    }
  };

  const [pendingRevenue, setPendingRevenue] = useState(null);
  const [collectingRevenue, setCollectingRevenue] = useState(false);

  const loadPendingRevenue = async (infraId) => {
    try {
      const res = await api.get(`/infrastructure/${infraId}/pending-revenue`);
      setPendingRevenue(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const collectRevenue = async () => {
    if (!selectedInfra) return;
    setCollectingRevenue(true);
    try {
      const res = await api.post(`/infrastructure/${selectedInfra.id}/collect-revenue`);
      toast.success(`Riscossi $${res.data.collected.toLocaleString()}! (${res.data.hours_accumulated}h accumulate)`);
      setPendingRevenue({...pendingRevenue, pending: 0, hours_accumulated: 0});
      // Refresh
      const my = await api.get('/infrastructure/my');
      setMyInfra(my.data);
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setCollectingRevenue(false);
    }
  };

  // Load pending revenue when opening detail dialog
  useEffect(() => {
    if (showDetailDialog && selectedInfra) {
      loadPendingRevenue(selectedInfra.id);
    }
  }, [showDetailDialog, selectedInfra]);

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="infrastructure-page">
      {/* Level Progress */}
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

      {/* My Infrastructure */}
      <Card className="bg-[#1A1A1A] border-white/10 mb-4">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
            <Building className="w-5 h-5 text-yellow-500" /> Le Mie Infrastrutture ({myInfra.total_count || 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {myInfra.infrastructure.length === 0 ? (
            <p className="text-gray-400 text-center py-6">Non hai ancora infrastrutture. Raggiungi il livello 5 per acquistare il tuo primo cinema!</p>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {myInfra.infrastructure.map(infra => {
                const Icon = getIcon(INFRASTRUCTURE_TYPES?.[infra.type]?.icon || 'building');
                return (
                  <Card key={infra.id} className="bg-white/5 border-white/10 cursor-pointer hover:border-yellow-500/50 transition-colors" onClick={() => openInfraDetail(infra)}>
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                          <Icon className="w-5 h-5 text-yellow-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-sm truncate">{infra.custom_name}</h3>
                          <p className="text-[10px] text-gray-400">{infra.city?.name}, {infra.country}</p>
                        </div>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">Ricavi totali:</span>
                        <span className="text-green-400">${(infra.total_revenue || 0).toLocaleString()}</span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Available Infrastructure Types */}
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-yellow-500" /> Infrastrutture Disponibili
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {infraTypes.map(infra => {
              const Icon = getIcon(infra.icon);
              const canBuy = infra.can_purchase;
              return (
                <Card key={infra.id} className={`border transition-all ${canBuy ? 'bg-white/5 border-green-500/30 hover:border-green-500' : 'bg-white/5 border-white/10 opacity-60'}`}>
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${canBuy ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
                        {canBuy ? <Icon className="w-5 h-5 text-green-500" /> : <Lock className="w-5 h-5 text-gray-500" />}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-sm">{language === 'it' ? infra.name_it : infra.name}</h3>
                        <div className="flex gap-1">
                          <Badge className={`text-[10px] h-4 ${infra.meets_level ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                            Lv.{infra.level_required}
                          </Badge>
                          <Badge className={`text-[10px] h-4 ${infra.meets_fame ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                            Fame {infra.fame_required}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <p className="text-[10px] text-gray-400 mb-2 line-clamp-2">{language === 'it' ? infra.description_it : infra.description}</p>
                    <div className="flex justify-between items-center">
                      <span className="text-yellow-500 font-semibold text-sm">${infra.base_cost?.toLocaleString()}</span>
                      <Button size="sm" className="h-7 text-xs" disabled={!canBuy} onClick={() => { setSelectedType(infra); setShowPurchaseDialog(true); }}>
                        {canBuy ? 'Acquista' : 'Bloccato'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Purchase Dialog */}
      <Dialog open={showPurchaseDialog} onOpenChange={setShowPurchaseDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl">Acquista {selectedType?.name_it || selectedType?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs">Nome personalizzato</Label>
              <Input value={customName} onChange={e => setCustomName(e.target.value)} placeholder={`${user?.nickname}'s ${selectedType?.name}`} className="h-9 bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">Paese</Label>
              <Select value={selectedCountry} onValueChange={v => { setSelectedCountry(v); setSelectedCity(''); }}>
                <SelectTrigger className="h-9 bg-black/20 border-white/10"><SelectValue placeholder="Seleziona paese" /></SelectTrigger>
                <SelectContent>
                  {Object.keys(cities).map(country => (
                    <SelectItem key={country} value={country}>{country}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedCountry && (
              <div>
                <Label className="text-xs">Città</Label>
                <Select value={selectedCity} onValueChange={setSelectedCity}>
                  <SelectTrigger className="h-9 bg-black/20 border-white/10"><SelectValue placeholder="Seleziona città" /></SelectTrigger>
                  <SelectContent>
                    {cities[selectedCountry]?.map(city => (
                      <SelectItem key={city.name} value={city.name}>
                        {city.name} (x{city.cost_multiplier})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {selectedCity && (
              <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Costo totale:</span>
                  <span className="text-yellow-500 font-bold">${getCityPrice().toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>I tuoi fondi:</span>
                  <span className={user?.funds >= getCityPrice() ? 'text-green-400' : 'text-red-400'}>${user?.funds?.toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPurchaseDialog(false)}>Annulla</Button>
            <Button onClick={handlePurchase} disabled={purchasing || !selectedCity || user?.funds < getCityPrice()} className="bg-yellow-500 text-black">
              {purchasing ? 'Acquistando...' : 'Conferma Acquisto'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Infrastructure Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Building className="w-5 h-5 text-yellow-500" /> {selectedInfra?.custom_name || 'Dettaglio Infrastruttura'}
            </DialogTitle>
            <DialogDescription>
              {selectedInfra?.city?.name}, {selectedInfra?.country} • {selectedInfra?.type}
            </DialogDescription>
          </DialogHeader>
          
          {loadingDetail ? (
            <div className="text-center py-8">Caricamento...</div>
          ) : infraDetail && (
            <div className="space-y-4">
              {/* Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-white/5 rounded border border-white/10">
                  <p className="text-xs text-gray-400">Ricavi totali</p>
                  <p className="text-lg font-bold text-green-400">${(infraDetail.total_revenue || 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-white/5 rounded border border-white/10">
                  <p className="text-xs text-gray-400">Film in programmazione</p>
                  <p className="text-lg font-bold text-yellow-500">{infraDetail.films_showing?.length || 0}</p>
                </div>
              </div>

              {/* Revenue Collection */}
              {pendingRevenue && (
                <div className="p-3 bg-gradient-to-r from-green-500/10 to-yellow-500/10 rounded border border-green-500/30">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-sm flex items-center gap-2">
                      <Wallet className="w-4 h-4 text-green-500" /> Incassi da Riscuotere
                    </h4>
                    <Badge className={pendingRevenue.is_maxed ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}>
                      {pendingRevenue.hours_accumulated?.toFixed(1)}h / 4h
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-2xl font-bold text-green-400">${pendingRevenue.pending?.toLocaleString()}</p>
                      <p className="text-xs text-gray-400">${pendingRevenue.hourly_rate?.toLocaleString()}/ora</p>
                    </div>
                    <Button 
                      onClick={collectRevenue}
                      disabled={collectingRevenue || pendingRevenue.pending < 1}
                      className="bg-green-500 hover:bg-green-400 text-black font-bold"
                    >
                      {collectingRevenue ? 'Riscuotendo...' : 'Riscuoti Ora'}
                    </Button>
                  </div>
                  {pendingRevenue.is_maxed && (
                    <p className="text-xs text-red-400 mt-2">⚠️ Incassi al massimo! Riscuoti per continuare ad accumulare.</p>
                  )}
                </div>
              )}

              {/* Prices Section */}
              {['cinema', 'megaplex', 'drive_in', 'mall'].includes(selectedInfra?.type) && (
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-yellow-500" /> Imposta Prezzi
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-xs">Biglietto ($)</Label>
                      <Input
                        type="number"
                        value={prices.ticket || 12}
                        onChange={e => setPrices({...prices, ticket: parseInt(e.target.value) || 0})}
                        className="h-9 bg-black/20 border-white/10"
                        min={1}
                        max={50}
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Popcorn ($)</Label>
                      <Input
                        type="number"
                        value={prices.popcorn || 8}
                        onChange={e => setPrices({...prices, popcorn: parseInt(e.target.value) || 0})}
                        className="h-9 bg-black/20 border-white/10"
                        min={1}
                        max={30}
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Bevande ($)</Label>
                      <Input
                        type="number"
                        value={prices.drinks || 5}
                        onChange={e => setPrices({...prices, drinks: parseInt(e.target.value) || 0})}
                        className="h-9 bg-black/20 border-white/10"
                        min={1}
                        max={20}
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Combo ($)</Label>
                      <Input
                        type="number"
                        value={prices.combo || 18}
                        onChange={e => setPrices({...prices, combo: parseInt(e.target.value) || 0})}
                        className="h-9 bg-black/20 border-white/10"
                        min={1}
                        max={60}
                      />
                    </div>
                  </div>
                  <Button 
                    onClick={savePrices} 
                    disabled={savingPrices}
                    className="w-full bg-yellow-500 text-black hover:bg-yellow-400"
                  >
                    {savingPrices ? 'Salvando...' : 'Salva Prezzi'}
                  </Button>
                </div>
              )}

              {/* Film Management Section */}
              {['cinema', 'megaplex', 'drive_in', 'mall', 'multiplex_small', 'multiplex_medium', 'multiplex_large'].includes(selectedInfra?.type) && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-sm flex items-center gap-2">
                      <Film className="w-4 h-4 text-yellow-500" /> Programmazione Film
                    </h4>
                    <span className="text-xs text-gray-400">
                      {infraDetail?.films_showing?.length || 0} / {infraDetail?.type_info?.screens || 4} schermi
                    </span>
                  </div>
                  
                  {/* Films showing */}
                  {infraDetail?.films_showing?.length > 0 ? (
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {infraDetail.films_showing.map(film => (
                        <div key={film.film_id} className="flex items-center gap-2 p-2 bg-white/5 rounded border border-white/10">
                          {film.poster_url && (
                            <img src={film.poster_url} alt="" className="w-10 h-14 object-cover rounded" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold truncate">{film.title}</p>
                            <div className="flex items-center gap-2 text-xs text-gray-400">
                              <span>⭐ {film.imdb_rating || '?'}</span>
                              <Badge className={`text-[9px] h-4 ${film.is_owned ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                {film.is_owned ? '100% ricavi' : `${film.revenue_share_renter || 70}% ricavi`}
                              </Badge>
                              {film.is_rented && film.rental_end && (
                                <span className="text-yellow-400">
                                  Scade: {new Date(film.rental_end).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                          <Button 
                            size="sm" 
                            variant="destructive" 
                            className="h-7 w-7 p-0"
                            disabled={removingFilm === film.film_id}
                            onClick={() => removeFilmFromCinema(film.film_id)}
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-gray-500 text-sm py-3">Nessun film in programmazione</p>
                  )}
                  
                  {/* Add Film Buttons */}
                  {(infraDetail?.films_showing?.length || 0) < (infraDetail?.type_info?.screens || 4) && (
                    <div className="grid grid-cols-2 gap-2">
                      <Button 
                        variant="outline" 
                        className="h-9 text-xs"
                        onClick={openAddFilmDialog}
                      >
                        <Plus className="w-3 h-3 mr-1" /> I Miei Film
                      </Button>
                      <Button 
                        className="h-9 text-xs bg-blue-500 hover:bg-blue-400"
                        onClick={openRentFilmDialog}
                      >
                        <ShoppingBag className="w-3 h-3 mr-1" /> Affitta Film
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>Chiudi</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Own Film Dialog */}
      <Dialog open={showAddFilmDialog} onOpenChange={setShowAddFilmDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <Film className="w-5 h-5 text-yellow-500" /> Aggiungi i Tuoi Film
            </DialogTitle>
            <DialogDescription>Seleziona un tuo film da proiettare. Riceverai il 100% dei ricavi.</DialogDescription>
          </DialogHeader>
          
          {myFilms.length === 0 ? (
            <div className="text-center py-6">
              <Film className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <p className="text-gray-400">Non hai ancora creato nessun film.</p>
              <Button className="mt-3" onClick={() => { setShowAddFilmDialog(false); setShowDetailDialog(false); navigate('/create'); }}>
                Crea un Film
              </Button>
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {myFilms.map(film => (
                <div 
                  key={film.id} 
                  className={`flex items-center gap-3 p-2 rounded border cursor-pointer transition-colors ${
                    selectedFilmToAdd?.id === film.id 
                      ? 'bg-yellow-500/20 border-yellow-500' 
                      : 'bg-white/5 border-white/10 hover:border-yellow-500/50'
                  }`}
                  onClick={() => setSelectedFilmToAdd(film)}
                >
                  {film.poster_url && (
                    <img src={film.poster_url} alt="" className="w-12 h-16 object-cover rounded" />
                  )}
                  <div className="flex-1">
                    <p className="font-semibold text-sm">{film.title}</p>
                    <p className="text-xs text-gray-400">{film.genre} • ⭐ {film.imdb_rating}</p>
                    <p className="text-xs text-green-400">Ricavi: ${(film.total_revenue || 0).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddFilmDialog(false)}>Annulla</Button>
            <Button 
              onClick={addFilmToCinema} 
              disabled={!selectedFilmToAdd || addingFilm}
              className="bg-yellow-500 text-black"
            >
              {addingFilm ? 'Aggiungendo...' : 'Aggiungi'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rent Film Dialog */}
      <Dialog open={showRentFilmDialog} onOpenChange={setShowRentFilmDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-blue-500" /> Affitta Film di Altri Giocatori
            </DialogTitle>
            <DialogDescription>Affitta film popolari. Paghi l'affitto e ricevi il 70% dei ricavi.</DialogDescription>
          </DialogHeader>
          
          {rentalFilms.length === 0 ? (
            <div className="text-center py-6">
              <Film className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <p className="text-gray-400">Nessun film disponibile per l'affitto al momento.</p>
            </div>
          ) : (
            <>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {rentalFilms.map(film => (
                  <div 
                    key={film.id} 
                    className={`flex items-center gap-3 p-2 rounded border cursor-pointer transition-colors ${
                      selectedFilmToRent?.id === film.id 
                        ? 'bg-blue-500/20 border-blue-500' 
                        : 'bg-white/5 border-white/10 hover:border-blue-500/50'
                    }`}
                    onClick={() => setSelectedFilmToRent(film)}
                  >
                    {film.poster_url && (
                      <img src={film.poster_url} alt="" className="w-12 h-16 object-cover rounded" />
                    )}
                    <div className="flex-1">
                      <p className="font-semibold text-sm">{film.title}</p>
                      <p className="text-xs text-gray-400">{film.genre} • ⭐ {film.imdb_rating} • ❤️ {film.likes_count}</p>
                      <p className="text-xs text-gray-500">di {film.owner?.nickname || 'Unknown'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-yellow-500 font-bold text-sm">${film.weekly_rental?.toLocaleString()}</p>
                      <p className="text-[10px] text-gray-400">/settimana</p>
                    </div>
                  </div>
                ))}
              </div>
              
              {selectedFilmToRent && (
                <div className="p-3 bg-blue-500/10 rounded border border-blue-500/20 mt-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">Durata affitto:</span>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" className="h-7 w-7 p-0" onClick={() => setRentalWeeks(Math.max(1, rentalWeeks - 1))}>-</Button>
                      <span className="w-8 text-center font-bold">{rentalWeeks}</span>
                      <Button size="sm" variant="outline" className="h-7 w-7 p-0" onClick={() => setRentalWeeks(Math.min(12, rentalWeeks + 1))}>+</Button>
                      <span className="text-sm">settimane</span>
                    </div>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Costo totale:</span>
                    <span className="text-yellow-500 font-bold">${(selectedFilmToRent.weekly_rental * rentalWeeks).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>Al proprietario (30%):</span>
                    <span>${(selectedFilmToRent.weekly_rental * rentalWeeks * 0.3).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xs text-green-400 mt-1">
                    <span>Tuoi ricavi futuri:</span>
                    <span>70% degli incassi</span>
                  </div>
                </div>
              )}
            </>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowRentFilmDialog(false); setSelectedFilmToRent(null); }}>Annulla</Button>
            <Button 
              onClick={rentFilmForCinema} 
              disabled={!selectedFilmToRent || rentingFilm || (user?.funds < (selectedFilmToRent?.weekly_rental * rentalWeeks))}
              className="bg-blue-500 hover:bg-blue-400"
            >
              {rentingFilm ? 'Affittando...' : `Affitta per $${selectedFilmToRent ? (selectedFilmToRent.weekly_rental * rentalWeeks).toLocaleString() : 0}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Placeholder for infrastructure detail route
const INFRASTRUCTURE_TYPES = {};

// Infrastructure Marketplace Page
const MarketplacePage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [listings, setListings] = useState([]);
  const [myListings, setMyListings] = useState([]);
  const [myOffers, setMyOffers] = useState([]);
  const [myInfra, setMyInfra] = useState([]);
  const [canTrade, setCanTrade] = useState(false);
  const [requiredLevel, setRequiredLevel] = useState(15);
  const [currentLevel, setCurrentLevel] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('browse');
  
  // Sell dialog state
  const [showSellDialog, setShowSellDialog] = useState(false);
  const [selectedInfra, setSelectedInfra] = useState(null);
  const [valuation, setValuation] = useState(null);
  const [askingPrice, setAskingPrice] = useState(0);
  const [listing, setListing] = useState(false);
  
  // Offer dialog state
  const [showOfferDialog, setShowOfferDialog] = useState(false);
  const [selectedListing, setSelectedListing] = useState(null);
  const [offerPrice, setOfferPrice] = useState(0);
  const [making, setMaking] = useState(false);

  useEffect(() => {
    loadData();
  }, [api]);

  const loadData = async () => {
    try {
      const [marketRes, myRes, infraRes] = await Promise.all([
        api.get('/marketplace'),
        api.get('/marketplace/my-listings'),
        api.get('/infrastructure/my')
      ]);
      setListings(marketRes.data.listings);
      setCanTrade(marketRes.data.can_trade);
      setRequiredLevel(marketRes.data.required_level);
      setCurrentLevel(marketRes.data.current_level);
      setMyListings(myRes.data.my_listings);
      setMyOffers(myRes.data.my_offers);
      setMyInfra(infraRes.data.infrastructure);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const openSellDialog = async (infra) => {
    setSelectedInfra(infra);
    try {
      const res = await api.get(`/infrastructure/${infra.id}/valuation`);
      setValuation(res.data);
      setAskingPrice(res.data.suggested_price);
      setShowSellDialog(true);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella valutazione');
    }
  };

  const createListing = async () => {
    setListing(true);
    try {
      await api.post('/marketplace/list', {
        infrastructure_id: selectedInfra.id,
        asking_price: askingPrice
      });
      toast.success('Infrastruttura messa in vendita!');
      setShowSellDialog(false);
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setListing(false);
    }
  };

  const cancelListing = async (listingId) => {
    try {
      await api.delete(`/marketplace/listing/${listingId}`);
      toast.success('Annuncio cancellato');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const openOfferDialog = (listing) => {
    setSelectedListing(listing);
    setOfferPrice(listing.asking_price);
    setShowOfferDialog(true);
  };

  const makeOffer = async () => {
    setMaking(true);
    try {
      await api.post('/marketplace/offer', {
        listing_id: selectedListing.id,
        offer_price: offerPrice
      });
      toast.success('Offerta inviata!');
      setShowOfferDialog(false);
      loadData();
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setMaking(false);
    }
  };

  const acceptOffer = async (listingId, offerId) => {
    try {
      const res = await api.post(`/marketplace/offer/${listingId}/accept/${offerId}`);
      toast.success(`Vendita completata! Hai ricevuto $${res.data.sold_price.toLocaleString()}`);
      loadData();
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const rejectOffer = async (listingId, offerId) => {
    try {
      await api.post(`/marketplace/offer/${listingId}/reject/${offerId}`);
      toast.success('Offerta rifiutata');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  if (loading) return <div className="pt-20 text-center">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="marketplace-page">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
          <ShoppingBag className="w-7 h-7 text-yellow-500" /> Marketplace Infrastrutture
        </h1>
        {!canTrade && (
          <Badge className="bg-red-500/20 text-red-400 flex items-center gap-1">
            <Lock className="w-3 h-3" /> Richiesto Lv.{requiredLevel} (Attuale: Lv.{currentLevel})
          </Badge>
        )}
      </div>

      {!canTrade && (
        <Card className="bg-yellow-500/10 border-yellow-500/30 mb-4">
          <CardContent className="p-4 flex items-center gap-3">
            <Lock className="w-8 h-8 text-yellow-500" />
            <div>
              <h3 className="font-semibold">Marketplace Bloccato</h3>
              <p className="text-sm text-gray-400">
                Devi raggiungere il livello {requiredLevel} per comprare e vendere infrastrutture con altri giocatori. 
                Attualmente sei al livello {currentLevel}.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="browse">Sfoglia ({listings.length})</TabsTrigger>
          <TabsTrigger value="my-listings">I Miei Annunci ({myListings.filter(l => l.status === 'active').length})</TabsTrigger>
          <TabsTrigger value="sell">Vendi</TabsTrigger>
        </TabsList>

        <TabsContent value="browse">
          {listings.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
              <Building className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <h3 className="text-lg mb-2">Nessun annuncio attivo</h3>
              <p className="text-gray-400">Al momento non ci sono infrastrutture in vendita.</p>
            </Card>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {listings.map(listing => (
                <Card key={listing.id} className="bg-[#1A1A1A] border-white/10">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-12 h-12 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                        <Building className="w-6 h-6 text-yellow-500" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold">{listing.infrastructure.custom_name}</h3>
                        <p className="text-xs text-gray-400">{listing.infrastructure.city?.name}, {listing.infrastructure.country}</p>
                      </div>
                    </div>
                    <div className="space-y-1 text-sm mb-3">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Tipo:</span>
                        <span>{listing.infrastructure.type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Ricavi totali:</span>
                        <span className="text-green-400">${listing.infrastructure.total_revenue?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Film in programmazione:</span>
                        <span>{listing.infrastructure.films_showing}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Venditore:</span>
                        <span>{listing.seller?.nickname}</span>
                      </div>
                    </div>
                    <div className="p-2 bg-yellow-500/10 rounded border border-yellow-500/20 mb-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Prezzo richiesto:</span>
                        <span className="text-yellow-500 font-bold text-lg">${listing.asking_price?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-400">
                        <span>Valore stimato:</span>
                        <span>${listing.calculated_value?.toLocaleString()}</span>
                      </div>
                    </div>
                    <Button 
                      className="w-full bg-yellow-500 text-black hover:bg-yellow-400" 
                      disabled={!canTrade || listing.seller_id === user?.id}
                      onClick={() => openOfferDialog(listing)}
                    >
                      {listing.seller_id === user?.id ? 'Il tuo annuncio' : 'Fai un\'offerta'}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="my-listings">
          {myListings.filter(l => l.status === 'active').length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
              <Ticket className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <h3 className="text-lg mb-2">Nessun annuncio attivo</h3>
              <p className="text-gray-400">Non hai infrastrutture in vendita.</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {myListings.filter(l => l.status === 'active').map(listing => (
                <Card key={listing.id} className="bg-[#1A1A1A] border-white/10">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Building className="w-8 h-8 text-yellow-500" />
                        <div>
                          <h3 className="font-semibold">{listing.infrastructure.custom_name}</h3>
                          <p className="text-xs text-gray-400">Prezzo: ${listing.asking_price?.toLocaleString()}</p>
                        </div>
                      </div>
                      <Button variant="destructive" size="sm" onClick={() => cancelListing(listing.id)}>
                        <X className="w-4 h-4" /> Annulla
                      </Button>
                    </div>
                    {listing.offers?.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-semibold text-sm">Offerte ricevute ({listing.offers.filter(o => o.status === 'pending').length})</h4>
                        {listing.offers.filter(o => o.status === 'pending').map(offer => (
                          <div key={offer.id} className="flex items-center justify-between p-2 bg-white/5 rounded">
                            <div>
                              <p className="font-semibold">{offer.buyer_nickname}</p>
                              <p className="text-yellow-500">${offer.offer_price?.toLocaleString()}</p>
                            </div>
                            <div className="flex gap-2">
                              <Button size="sm" className="bg-green-500 hover:bg-green-400" onClick={() => acceptOffer(listing.id, offer.id)}>
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button size="sm" variant="destructive" onClick={() => rejectOffer(listing.id, offer.id)}>
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="sell">
          {myInfra.length === 0 ? (
            <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
              <Building className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <h3 className="text-lg mb-2">Nessuna infrastruttura</h3>
              <p className="text-gray-400 mb-4">Non hai infrastrutture da vendere.</p>
              <Button onClick={() => navigate('/infrastructure')} className="bg-yellow-500 text-black">
                Acquista Infrastrutture
              </Button>
            </Card>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {myInfra.map(infra => {
                const isListed = myListings.some(l => l.infrastructure_id === infra.id && l.status === 'active');
                return (
                  <Card key={infra.id} className={`bg-[#1A1A1A] border-white/10 ${isListed ? 'opacity-60' : ''}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                          <Building className="w-5 h-5 text-yellow-500" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm">{infra.custom_name}</h3>
                          <p className="text-xs text-gray-400">{infra.city?.name}, {infra.country}</p>
                        </div>
                      </div>
                      <div className="text-xs text-gray-400 mb-3">
                        Tipo: {infra.type} • Ricavi: ${infra.total_revenue?.toLocaleString()}
                      </div>
                      <Button 
                        className="w-full" 
                        disabled={!canTrade || isListed}
                        onClick={() => openSellDialog(infra)}
                      >
                        {isListed ? 'Già in vendita' : 'Metti in vendita'}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Sell Dialog */}
      <Dialog open={showSellDialog} onOpenChange={setShowSellDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl">Vendi Infrastruttura</DialogTitle>
            <DialogDescription>Imposta il prezzo per {selectedInfra?.custom_name}</DialogDescription>
          </DialogHeader>
          {valuation && (
            <div className="space-y-4">
              <div className="p-3 bg-white/5 rounded border border-white/10">
                <h4 className="font-semibold mb-2">Valutazione</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-gray-400">Valore base:</span> <span>${valuation.factors?.base_value?.toLocaleString()}</span></div>
                  <div><span className="text-gray-400">Moltiplicatore livello:</span> <span>x{valuation.factors?.level_multiplier}</span></div>
                  <div><span className="text-gray-400">Moltiplicatore fama:</span> <span>x{valuation.factors?.fame_multiplier}</span></div>
                  <div><span className="text-gray-400">Bonus ricavi:</span> <span>+${valuation.factors?.revenue_bonus?.toLocaleString()}</span></div>
                </div>
              </div>
              <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
                <div className="flex justify-between mb-1">
                  <span>Valore stimato:</span>
                  <span className="text-yellow-500 font-bold">${valuation.calculated_value?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Range prezzo:</span>
                  <span>${valuation.min_price?.toLocaleString()} - ${valuation.max_price?.toLocaleString()}</span>
                </div>
              </div>
              <div>
                <Label className="text-xs">Prezzo richiesto</Label>
                <Input 
                  type="number" 
                  value={askingPrice} 
                  onChange={e => setAskingPrice(parseInt(e.target.value) || 0)}
                  min={valuation.min_price}
                  max={valuation.max_price}
                  className="h-10 bg-black/20 border-white/10"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Min: ${valuation.min_price?.toLocaleString()} • Max: ${valuation.max_price?.toLocaleString()}
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSellDialog(false)}>Annulla</Button>
            <Button 
              onClick={createListing} 
              disabled={listing || askingPrice < valuation?.min_price || askingPrice > valuation?.max_price}
              className="bg-yellow-500 text-black"
            >
              {listing ? 'Pubblicando...' : 'Pubblica Annuncio'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Offer Dialog */}
      <Dialog open={showOfferDialog} onOpenChange={setShowOfferDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl">Fai un'offerta</DialogTitle>
            <DialogDescription>{selectedListing?.infrastructure?.custom_name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-3 bg-white/5 rounded border border-white/10">
              <div className="flex justify-between mb-1">
                <span className="text-gray-400">Prezzo richiesto:</span>
                <span className="text-yellow-500">${selectedListing?.asking_price?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>Valore stimato:</span>
                <span>${selectedListing?.calculated_value?.toLocaleString()}</span>
              </div>
            </div>
            <div>
              <Label className="text-xs">La tua offerta</Label>
              <Input 
                type="number" 
                value={offerPrice} 
                onChange={e => setOfferPrice(parseInt(e.target.value) || 0)}
                min={1}
                className="h-10 bg-black/20 border-white/10"
              />
            </div>
            <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
              <div className="flex justify-between">
                <span>I tuoi fondi:</span>
                <span className={user?.funds >= offerPrice ? 'text-green-400' : 'text-red-400'}>
                  ${user?.funds?.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowOfferDialog(false)}>Annulla</Button>
            <Button 
              onClick={makeOffer} 
              disabled={making || offerPrice < 1 || user?.funds < offerPrice}
              className="bg-yellow-500 text-black"
            >
              {making ? 'Inviando...' : 'Invia Offerta'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Festivals Page
const FestivalsPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
  const location = useLocation();
  const [festivals, setFestivals] = useState([]);
  const [customFestivals, setCustomFestivals] = useState([]);
  const [selectedFestival, setSelectedFestival] = useState(null);
  const [currentEdition, setCurrentEdition] = useState(null);
  const [selectedCustomFestival, setSelectedCustomFestival] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [leaderboardPeriod, setLeaderboardPeriod] = useState('all_time');
  const [myAwards, setMyAwards] = useState(null);
  const [activeTab, setActiveTab] = useState('festivals');
  const [voting, setVoting] = useState(false);
  const [creationCost, setCreationCost] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newFestival, setNewFestival] = useState({ name: '', description: '', poster_prompt: '', categories: ['best_film', 'best_director', 'best_actor'], base_participation_cost: 10000, duration_days: 7 });
  const [myFilms, setMyFilms] = useState([]);
  const [selectedFilmIds, setSelectedFilmIds] = useState([]);
  const [participating, setParticipating] = useState(false);
  // Live Ceremony states
  const [liveCeremony, setLiveCeremony] = useState(null);
  const [showLiveCeremony, setShowLiveCeremony] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [sendingChat, setSendingChat] = useState(false);
  const chatRefreshInterval = useRef(null);
  const [autoOpenLiveId, setAutoOpenLiveId] = useState(null);

  // Capture live parameter from URL immediately
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const liveId = params.get('live');
    if (liveId) {
      setAutoOpenLiveId(liveId);
      window.history.replaceState({}, '', '/festivals');
    }
  }, [location.search]);

  const periodLabels = {
    'monthly': language === 'it' ? 'Questo Mese' : language === 'es' ? 'Este Mes' : 'This Month',
    'yearly': language === 'it' ? 'Quest\'Anno' : language === 'es' ? 'Este Año' : 'This Year',
    'all_time': language === 'it' ? 'Di Sempre' : language === 'es' ? 'De Todos Los Tiempos' : 'All Time'
  };

  const categoryOptions = [
    { id: 'best_film', name: language === 'it' ? 'Miglior Film' : 'Best Film' },
    { id: 'best_director', name: language === 'it' ? 'Miglior Regia' : 'Best Director' },
    { id: 'best_actor', name: language === 'it' ? 'Miglior Attore' : 'Best Actor' },
    { id: 'best_actress', name: language === 'it' ? 'Miglior Attrice' : 'Best Actress' },
    { id: 'best_screenplay', name: language === 'it' ? 'Miglior Sceneggiatura' : 'Best Screenplay' },
    { id: 'best_soundtrack', name: language === 'it' ? 'Miglior Colonna Sonora' : 'Best Soundtrack' },
    { id: 'audience_choice', name: language === 'it' ? 'Premio del Pubblico' : 'Audience Choice' },
  ];

  useEffect(() => {
    loadFestivals();
    loadCustomFestivals();
    loadLeaderboard();
    loadMyAwards();
    loadCreationCost();
  }, [language]);

  const loadFestivals = async () => {
    try {
      const res = await api.get(`/festivals?language=${language}`);
      setFestivals(res.data.festivals);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCustomFestivals = async () => {
    try {
      const res = await api.get('/custom-festivals');
      setCustomFestivals(res.data.festivals || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCreationCost = async () => {
    try {
      const res = await api.get('/custom-festivals/creation-cost');
      setCreationCost(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCustomFestivalDetails = async (festivalId) => {
    try {
      const res = await api.get(`/custom-festivals/${festivalId}`);
      setSelectedCustomFestival(res.data);
      // Load user's films for participation
      const filmsRes = await api.get('/films/my');
      setMyFilms(filmsRes.data || []);
    } catch (e) {
      toast.error('Errore caricamento festival');
    }
  };

  const createCustomFestival = async () => {
    if (!newFestival.name.trim()) { toast.error('Inserisci un nome'); return; }
    setCreating(true);
    try {
      const res = await api.post('/custom-festivals/create', newFestival);
      toast.success(res.data.message);
      setShowCreateDialog(false);
      setNewFestival({ name: '', description: '', poster_prompt: '', categories: ['best_film'], base_participation_cost: 10000, duration_days: 7 });
      loadCustomFestivals();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore creazione');
    } finally {
      setCreating(false);
    }
  };

  const participateInFestival = async () => {
    if (!selectedCustomFestival || selectedFilmIds.length === 0) return;
    setParticipating(true);
    try {
      const res = await api.post('/custom-festivals/participate', { festival_id: selectedCustomFestival.id, film_ids: selectedFilmIds });
      toast.success(res.data.message);
      loadCustomFestivalDetails(selectedCustomFestival.id);
      setSelectedFilmIds([]);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore partecipazione');
    } finally {
      setParticipating(false);
    }
  };

  const loadFestivalEdition = async (festivalId) => {
    try {
      const res = await api.get(`/festivals/${festivalId}/current?language=${language}`);
      setCurrentEdition(res.data);
      setSelectedFestival(festivalId);
    } catch (e) {
      toast.error('Errore caricamento festival');
    }
  };

  const loadLeaderboard = async (period = leaderboardPeriod) => {
    try {
      const res = await api.get(`/festivals/awards/leaderboard?period=${period}&language=${language}`);
      setLeaderboard(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadMyAwards = async () => {
    try {
      const res = await api.get(`/festivals/my-awards?language=${language}`);
      setMyAwards(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleVote = async (categoryId, nomineeId) => {
    if (!currentEdition || voting) return;
    setVoting(true);
    try {
      await api.post('/festivals/vote', {
        festival_id: selectedFestival,
        edition_id: currentEdition.id,
        category: categoryId,
        nominee_id: nomineeId
      });
      toast.success('+5 XP per il voto!');
      loadFestivalEdition(selectedFestival);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore votazione');
    } finally {
      setVoting(false);
    }
  };

  // Live Ceremony functions
  const [viewingBonus, setViewingBonus] = useState({ viewing_minutes: 0, bonus_percent: 0 });
  
  const loadLiveCeremony = async (festivalId) => {
    try {
      const res = await api.get(`/festivals/${festivalId}/live-ceremony?language=${language}`);
      setLiveCeremony(res.data);
      // Join as viewer and get bonus info
      const joinRes = await api.post(`/festivals/${festivalId}/join-ceremony`);
      if (joinRes.data) {
        setViewingBonus({
          viewing_minutes: joinRes.data.viewing_minutes || 0,
          bonus_percent: joinRes.data.bonus_percent || 0
        });
      }
    } catch (e) {
      console.error('Error loading live ceremony:', e);
    }
  };

  const openLiveCeremony = (festival) => {
    setSelectedFestival(festival.id);
    loadLiveCeremony(festival.id);
    setShowLiveCeremony(true);
    // Start chat refresh interval (also pings for viewing bonus)
    chatRefreshInterval.current = setInterval(() => {
      loadLiveCeremony(festival.id);
    }, 5000);  // Ping every 5 seconds to track viewing time
  };

  const closeLiveCeremony = () => {
    setShowLiveCeremony(false);
    setLiveCeremony(null);
    if (chatRefreshInterval.current) {
      clearInterval(chatRefreshInterval.current);
    }
  };

  // Auto-open live ceremony when festivals are loaded and autoOpenLiveId is set
  useEffect(() => {
    if (autoOpenLiveId && festivals.length > 0) {
      const fest = festivals.find(f => f.id === autoOpenLiveId);
      if (fest) {
        openLiveCeremony(fest);
        setAutoOpenLiveId(null);
      }
    }
  }, [autoOpenLiveId, festivals]);

  const sendChatMessage = async () => {
    if (!chatMessage.trim() || !liveCeremony) return;
    setSendingChat(true);
    try {
      await api.post('/festivals/ceremony/chat', {
        festival_id: liveCeremony.festival_id,
        edition_id: liveCeremony.edition_id,
        message: chatMessage
      });
      setChatMessage('');
      loadLiveCeremony(liveCeremony.festival_id);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore invio messaggio');
    } finally {
      setSendingChat(false);
    }
  };

  useEffect(() => {
    return () => {
      if (chatRefreshInterval.current) {
        clearInterval(chatRefreshInterval.current);
      }
    };
  }, []);

  // Audio playback for TTS announcements
  const audioRef = useRef(null);
  const [playingAudio, setPlayingAudio] = useState(false);
  const [announcingCategory, setAnnouncingCategory] = useState(null);
  const [subtitleText, setSubtitleText] = useState('');
  const [subtitleVisible, setSubtitleVisible] = useState(false);
  const [winnerName, setWinnerName] = useState('');
  const [categoryWon, setCategoryWon] = useState('');
  const [showSpotlight, setShowSpotlight] = useState(false);

  // Confetti effects for winner announcement
  const fireConfetti = () => {
    // Gold confetti burst from sides
    const colors = ['#FFD700', '#FFA500', '#FFFF00', '#FFE4B5'];
    
    // Left side burst
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { x: 0, y: 0.6 },
      colors: colors,
      angle: 60
    });
    
    // Right side burst
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { x: 1, y: 0.6 },
      colors: colors,
      angle: 120
    });
    
    // Center celebration after small delay
    setTimeout(() => {
      confetti({
        particleCount: 150,
        spread: 100,
        origin: { x: 0.5, y: 0.5 },
        colors: colors,
        startVelocity: 45,
        gravity: 1.2
      });
    }, 500);
    
    // Star-shaped burst
    setTimeout(() => {
      const end = Date.now() + 1500;
      const interval = setInterval(() => {
        if (Date.now() > end) {
          clearInterval(interval);
          return;
        }
        confetti({
          particleCount: 20,
          spread: 360,
          origin: { x: Math.random(), y: Math.random() - 0.2 },
          colors: colors,
          ticks: 100,
          gravity: 0.8,
          scalar: 1.2,
          shapes: ['star']
        });
      }, 150);
    }, 1000);
  };

  const playAnnouncementAudio = (audioUrl, text, winner, category) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    setPlayingAudio(true);
    setSubtitleText(text);
    setWinnerName(winner);
    setCategoryWon(category);
    setSubtitleVisible(true);
    setShowSpotlight(true);
    
    // Fire confetti when winner name is revealed (after ~2 seconds)
    setTimeout(() => fireConfetti(), 2000);
    
    audio.play();
    audio.onended = () => {
      setPlayingAudio(false);
      // Keep subtitle visible for 2 more seconds after audio ends
      setTimeout(() => {
        setSubtitleVisible(false);
        setShowSpotlight(false);
      }, 2000);
    };
    audio.onerror = () => {
      setPlayingAudio(false);
      setSubtitleVisible(false);
      setShowSpotlight(false);
    };
  };

  const announceWinnerWithAudio = async (categoryId) => {
    if (!liveCeremony) return;
    setAnnouncingCategory(categoryId);
    try {
      const res = await api.post(`/festivals/${liveCeremony.festival_id}/announce-with-audio/${categoryId}?language=${language}`);
      if (res.data.success) {
        // Refresh ceremony data
        loadLiveCeremony(liveCeremony.festival_id);
        // Play audio with subtitles if available
        if (res.data.audio?.audio_url) {
          const announcementText = res.data.announcement_text?.[language] || res.data.announcement_text?.['en'] || '';
          playAnnouncementAudio(
            res.data.audio.audio_url, 
            announcementText,
            res.data.winner?.name || '',
            res.data.category_name || ''
          );
        }
        toast.success(`${language === 'it' ? 'Vincitore' : 'Winner'}: ${res.data.winner.name}!`);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore annuncio');
    } finally {
      setAnnouncingCategory(null);
    }
  };

  const getPrestigeStars = (prestige) => '⭐'.repeat(prestige);

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="festivals-page">
      {/* Navigation bar with festival icons */}
      <div className="flex items-center justify-between mb-4 bg-[#1A1A1A] rounded-lg p-2 sticky top-16 z-10 overflow-x-auto">
        <Button variant="ghost" size="sm" onClick={() => window.history.back()} className="text-gray-400 hover:text-white flex-shrink-0">
          <ArrowLeft className="w-4 h-4 mr-1" />
          {language === 'it' ? 'Indietro' : 'Back'}
        </Button>
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Official Festivals with specific icons */}
          {festivals.map((fest, idx) => {
            // Assign specific icons based on festival name/type
            const getFestivalIcon = (name) => {
              const lowerName = name.toLowerCase();
              if (lowerName.includes('golden') || lowerName.includes('oro') || lowerName.includes('star')) return <Star className="w-3.5 h-3.5" />;
              if (lowerName.includes('spotlight') || lowerName.includes('riflettori')) return <Sparkles className="w-3.5 h-3.5" />;
              if (lowerName.includes('cinema') || lowerName.includes('film')) return <Film className="w-3.5 h-3.5" />;
              return <Award className="w-3.5 h-3.5" />;
            };
            const getIconColor = (name) => {
              const lowerName = name.toLowerCase();
              if (lowerName.includes('golden') || lowerName.includes('oro') || lowerName.includes('star')) return 'text-yellow-400';
              if (lowerName.includes('spotlight') || lowerName.includes('riflettori')) return 'text-purple-400';
              if (lowerName.includes('cinema') || lowerName.includes('film')) return 'text-blue-400';
              return 'text-gray-400';
            };
            return (
              <Button 
                key={fest.id}
                variant="ghost" 
                size="sm" 
                onClick={() => { setActiveTab('festivals'); loadFestivalEdition(fest.id); }}
                className={`text-xs px-2 gap-1 ${selectedFestival === fest.id ? 'text-yellow-400 bg-yellow-500/10' : getIconColor(fest.name)}`}
              >
                {getFestivalIcon(fest.name)}
                <span className="hidden sm:inline">{fest.name.split(' ')[0]}</span>
                {fest.is_active && <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>}
              </Button>
            );
          })}
          {/* Separator */}
          {customFestivals.length > 0 && <div className="w-px h-5 bg-white/20 mx-1"></div>}
          {/* Custom/Player Festivals */}
          {customFestivals.slice(0, 4).map(fest => (
            <Button 
              key={fest.id}
              variant="ghost" 
              size="sm" 
              onClick={() => { setActiveTab('custom'); setSelectedCustomFestival(fest); }}
              className={`text-xs px-2 gap-1 ${selectedCustomFestival?.id === fest.id ? 'text-purple-400 bg-purple-500/10' : 'text-purple-300'}`}
              title={fest.name}
            >
              <Crown className="w-3.5 h-3.5" />
              <span className="hidden sm:inline max-w-[60px] truncate">{fest.name.split(' ')[0]}</span>
              {fest.is_active && <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>}
            </Button>
          ))}
        </div>
      </div>

      <div className="text-center mb-6">
        <Award className="w-12 h-12 text-yellow-500 mx-auto mb-2" />
        <h1 className="font-['Bebas_Neue'] text-3xl">{language === 'it' ? 'Festival del Cinema' : language === 'es' ? 'Festivales de Cine' : 'Film Festivals'}</h1>
        <p className="text-gray-400 text-sm">{language === 'it' ? 'Vota i migliori film e vinci premi!' : 'Vote for the best films and win awards!'}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 justify-center flex-wrap">
        <Button variant={activeTab === 'festivals' ? 'default' : 'outline'} onClick={() => setActiveTab('festivals')} className={activeTab === 'festivals' ? 'bg-yellow-500 text-black' : ''}>
          <Star className="w-4 h-4 mr-2" />{language === 'it' ? 'Festival Ufficiali' : 'Official Festivals'}
        </Button>
        <Button variant={activeTab === 'custom' ? 'default' : 'outline'} onClick={() => setActiveTab('custom')} className={activeTab === 'custom' ? 'bg-purple-500 text-white' : ''}>
          <Crown className="w-4 h-4 mr-2" />{language === 'it' ? 'Festival dei Player' : 'Player Festivals'}
        </Button>
        <Button variant={activeTab === 'leaderboard' ? 'default' : 'outline'} onClick={() => setActiveTab('leaderboard')} className={activeTab === 'leaderboard' ? 'bg-yellow-500 text-black' : ''}>
          <Trophy className="w-4 h-4 mr-2" />{language === 'it' ? 'Classifica' : 'Leaderboard'}
        </Button>
        <Button variant={activeTab === 'my_awards' ? 'default' : 'outline'} onClick={() => setActiveTab('my_awards')} className={activeTab === 'my_awards' ? 'bg-yellow-500 text-black' : ''}>
          <Medal className="w-4 h-4 mr-2" />{language === 'it' ? 'I Miei Premi' : 'My Awards'}
        </Button>
      </div>

      {/* Festivals Tab */}
      {activeTab === 'festivals' && (
        <div className="space-y-4">
          {!selectedFestival ? (
            <div className="grid md:grid-cols-3 gap-4">
              {festivals.map(fest => (
                <Card key={fest.id} className={`bg-[#1A1A1A] border-white/10 cursor-pointer hover:border-yellow-500/50 transition-colors ${fest.is_active ? 'ring-2 ring-yellow-500' : ''}`} onClick={() => loadFestivalEdition(fest.id)}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="font-['Bebas_Neue'] text-lg text-yellow-400">{fest.name}</CardTitle>
                      <span className="text-lg">{getPrestigeStars(fest.prestige)}</span>
                    </div>
                    {fest.is_active && (
                      <div className="flex items-center gap-2">
                        <Badge className="bg-green-500/20 text-green-400 w-fit">{language === 'it' ? 'IN CORSO' : 'ACTIVE'}</Badge>
                        <Button 
                          size="sm" 
                          onClick={(e) => { e.stopPropagation(); openLiveCeremony(fest); }}
                          className="bg-red-500 hover:bg-red-600 text-white text-xs h-6 px-2"
                        >
                          <Tv className="w-3 h-3 mr-1" />{language === 'it' ? 'LIVE' : 'LIVE'}
                        </Button>
                      </div>
                    )}
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-400 text-xs mb-3">{fest.description}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">
                        {language === 'it' ? 'Cerimonia' : 'Ceremony'}: {fest.ceremony_day}/{language === 'it' ? 'mese' : 'month'} {language === 'it' ? 'alle' : 'at'} {fest.ceremony_time || '21:30'}
                      </span>
                      <Badge variant="outline" className={fest.voting_type === 'player' ? 'border-purple-500 text-purple-400' : 'border-blue-500 text-blue-400'}>
                        {fest.voting_type === 'player' ? (language === 'it' ? 'Voto Giocatori' : 'Player Vote') : 'AI'}
                      </Badge>
                    </div>
                    <div className="mt-3 pt-3 border-t border-white/10 grid grid-cols-3 gap-2 text-center text-xs">
                      <div><p className="text-yellow-400 font-bold">+{fest.rewards.xp}</p><p className="text-gray-500">XP</p></div>
                      <div><p className="text-purple-400 font-bold">+{fest.rewards.fame}</p><p className="text-gray-500">{language === 'it' ? 'Fama' : 'Fame'}</p></div>
                      <div><p className="text-green-400 font-bold">${(fest.rewards.money/1000).toFixed(0)}K</p><p className="text-gray-500">{language === 'it' ? 'Denaro' : 'Money'}</p></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : currentEdition && (
            <div>
              <Button variant="ghost" onClick={() => {setSelectedFestival(null); setCurrentEdition(null);}} className="mb-4">
                <ChevronLeft className="w-4 h-4 mr-1" />{language === 'it' ? 'Torna ai Festival' : 'Back to Festivals'}
              </Button>
              
              <Card className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-yellow-500/30 mb-6">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-['Bebas_Neue'] text-2xl text-yellow-400">{currentEdition.festival_name}</CardTitle>
                    {currentEdition.can_vote && <Badge className="bg-purple-500/20 text-purple-400">{language === 'it' ? 'VOTA ORA' : 'VOTE NOW'}</Badge>}
                  </div>
                  <CardDescription>{language === 'it' ? `Edizione ${currentEdition.month}/${currentEdition.year}` : `Edition ${currentEdition.month}/${currentEdition.year}`}</CardDescription>
                </CardHeader>
              </Card>

              <div className="space-y-4">
                {currentEdition.categories?.map(cat => (
                  <Card key={cat.category_id} className="bg-[#1A1A1A] border-white/10">
                    <CardHeader className="pb-2">
                      <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2">
                        <Award className="w-5 h-5 text-yellow-500" />
                        {cat.name}
                        {cat.user_voted && <Badge className="bg-green-500/20 text-green-400 text-xs ml-2">{language === 'it' ? 'Votato' : 'Voted'}</Badge>}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
                        {cat.nominees?.map(nom => (
                          <div key={nom.id} className={`p-3 rounded-lg border ${cat.user_voted === nom.id ? 'bg-yellow-500/20 border-yellow-500' : 'bg-white/5 border-white/10 hover:border-white/30'} ${currentEdition.can_vote && !cat.user_voted ? 'cursor-pointer' : ''}`}
                            onClick={() => currentEdition.can_vote && !cat.user_voted && handleVote(cat.category_id, nom.id)}>
                            <div className="flex items-center gap-2 mb-2">
                              {nom.poster_url || nom.avatar_url ? (
                                <img src={nom.poster_url || nom.avatar_url} alt="" className="w-10 h-10 rounded object-cover" />
                              ) : (
                                <div className="w-10 h-10 rounded bg-white/10 flex items-center justify-center"><User className="w-5 h-5 text-gray-500" /></div>
                              )}
                              <div className="flex-1 min-w-0">
                                <p className="font-semibold text-sm truncate">{nom.name}</p>
                                {nom.film_title && <p className="text-xs text-gray-400 truncate">{nom.film_title}</p>}
                              </div>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-gray-500">{nom.votes || 0} {language === 'it' ? 'voti' : 'votes'}</span>
                              {currentEdition.can_vote && !cat.user_voted && <Button size="sm" className="h-6 text-xs bg-yellow-500 text-black hover:bg-yellow-400" disabled={voting}>{language === 'it' ? 'Vota' : 'Vote'}</Button>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Custom Festivals Tab */}
      {activeTab === 'custom' && (
        <div className="space-y-4">
          {/* Create Button */}
          {creationCost && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30">
              <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="font-['Bebas_Neue'] text-lg text-purple-400">{language === 'it' ? 'Crea il Tuo Festival' : 'Create Your Festival'}</h3>
                  <p className="text-xs text-gray-400">
                    {creationCost.can_create 
                      ? `Costo: $${creationCost.creation_cost?.toLocaleString()} • Livello ${creationCost.user_level}`
                      : `Richiesto Livello ${creationCost.required_level} (sei ${creationCost.user_level})`}
                  </p>
                </div>
                <Button 
                  onClick={() => setShowCreateDialog(true)} 
                  disabled={!creationCost.can_create}
                  className="bg-purple-500 hover:bg-purple-400"
                >
                  <Plus className="w-4 h-4 mr-2" />{language === 'it' ? 'Crea Festival' : 'Create Festival'}
                </Button>
              </CardContent>
            </Card>
          )}

          {!selectedCustomFestival ? (
            <div className="grid md:grid-cols-2 gap-4">
              {customFestivals.length === 0 ? (
                <Card className="bg-[#1A1A1A] border-white/10 col-span-2">
                  <CardContent className="p-8 text-center">
                    <Crown className="w-12 h-12 text-purple-400/50 mx-auto mb-2" />
                    <p className="text-gray-400">{language === 'it' ? 'Nessun festival dei player attivo. Creane uno!' : 'No player festivals active. Create one!'}</p>
                  </CardContent>
                </Card>
              ) : customFestivals.map(fest => (
                <Card key={fest.id} className="bg-[#1A1A1A] border-white/10 cursor-pointer hover:border-purple-500/50 transition-colors" onClick={() => loadCustomFestivalDetails(fest.id)}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="font-['Bebas_Neue'] text-lg text-purple-400">{fest.name}</CardTitle>
                      <Badge className={fest.status === 'open' ? 'bg-green-500/20 text-green-400' : fest.status === 'live' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}>
                        {fest.status === 'open' ? 'APERTO' : fest.status === 'live' ? 'LIVE' : fest.status.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-400 text-xs mb-2">{fest.description?.substring(0, 100)}...</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <User className="w-3 h-3" /> {fest.creator_name}
                      <span>•</span>
                      <span>${fest.prize_pool?.toLocaleString()} montepremi</span>
                    </div>
                    {fest.poster_url && <img src={fest.poster_url} alt="" className="mt-2 w-full h-32 object-cover rounded" />}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div>
              <Button variant="ghost" onClick={() => {setSelectedCustomFestival(null); setSelectedFilmIds([]);}} className="mb-4">
                <ChevronLeft className="w-4 h-4 mr-1" />{language === 'it' ? 'Torna ai Festival' : 'Back'}
              </Button>
              
              <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30 mb-4">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-['Bebas_Neue'] text-2xl text-purple-400">{selectedCustomFestival.name}</CardTitle>
                    <Badge className={selectedCustomFestival.status === 'open' ? 'bg-green-500/20 text-green-400' : 'bg-purple-500/20 text-purple-400'}>
                      {selectedCustomFestival.status?.toUpperCase()}
                    </Badge>
                  </div>
                  <CardDescription>
                    {language === 'it' ? 'Creato da' : 'Created by'} {selectedCustomFestival.creator_name} • 
                    Montepremi: ${selectedCustomFestival.prize_pool?.toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-300 mb-4">{selectedCustomFestival.description}</p>
                  
                  {/* Participation Section */}
                  {selectedCustomFestival.status === 'open' && !selectedCustomFestival.user_participating && (
                    <Card className="bg-black/30 border-white/10 mb-4">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">{language === 'it' ? 'Partecipa!' : 'Participate!'}</CardTitle>
                        <CardDescription className="text-xs">
                          {language === 'it' 
                            ? `Costo base: $${selectedCustomFestival.base_participation_cost?.toLocaleString()} per film` 
                            : `Base cost: $${selectedCustomFestival.base_participation_cost?.toLocaleString()} per film`}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ScrollArea className="h-[150px] mb-3">
                          <div className="space-y-2">
                            {myFilms.map((film, i) => {
                              const isSelected = selectedFilmIds.includes(film.id);
                              const cost = Math.floor(selectedCustomFestival.base_participation_cost * Math.pow(1.5, selectedFilmIds.indexOf(film.id) > -1 ? selectedFilmIds.indexOf(film.id) : selectedFilmIds.length));
                              return (
                                <div key={film.id} className={`p-2 rounded flex items-center justify-between cursor-pointer ${isSelected ? 'bg-purple-500/20 border border-purple-500' : 'bg-white/5 hover:bg-white/10'}`}
                                  onClick={() => {
                                    if (isSelected) {
                                      setSelectedFilmIds(selectedFilmIds.filter(id => id !== film.id));
                                    } else if (selectedFilmIds.length < (selectedCustomFestival.creator_id === user?.id ? 1 : 10)) {
                                      setSelectedFilmIds([...selectedFilmIds, film.id]);
                                    }
                                  }}>
                                  <span className="text-sm">{film.title}</span>
                                  {isSelected && <Check className="w-4 h-4 text-purple-400" />}
                                </div>
                              );
                            })}
                          </div>
                        </ScrollArea>
                        <Button onClick={participateInFestival} disabled={participating || selectedFilmIds.length === 0} className="w-full bg-purple-500">
                          {participating ? 'Iscrizione...' : `Iscrivi ${selectedFilmIds.length} film`}
                        </Button>
                      </CardContent>
                    </Card>
                  )}
                  
                  {selectedCustomFestival.user_participating && (
                    <Badge className="bg-green-500/20 text-green-400 mb-4">{language === 'it' ? 'Stai partecipando!' : 'You are participating!'}</Badge>
                  )}
                  
                  {/* Categories */}
                  <div className="flex flex-wrap gap-2">
                    {selectedCustomFestival.categories?.map(cat => (
                      <Badge key={cat.id} variant="outline" className="border-purple-500/30">{cat.name}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* Create Festival Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-[#1A1A1A] border-purple-500/30 max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl text-purple-400 flex items-center gap-2">
              <Crown className="w-5 h-5" /> {language === 'it' ? 'Crea il Tuo Festival' : 'Create Your Festival'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 max-h-[60vh] overflow-y-auto">
            <div>
              <Label className="text-xs">{language === 'it' ? 'Nome del Festival' : 'Festival Name'}</Label>
              <Input value={newFestival.name} onChange={e => setNewFestival({...newFestival, name: e.target.value})} placeholder="Il Mio Festival..." className="bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Descrizione' : 'Description'}</Label>
              <Textarea value={newFestival.description} onChange={e => setNewFestival({...newFestival, description: e.target.value})} placeholder="Descrivi il tuo festival..." className="bg-black/20 border-white/10 h-20" />
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Prompt Locandina AI (opzionale)' : 'Poster AI Prompt (optional)'}</Label>
              <Input value={newFestival.poster_prompt} onChange={e => setNewFestival({...newFestival, poster_prompt: e.target.value})} placeholder="Stile elegante, colori dorati..." className="bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Categorie Premio' : 'Award Categories'}</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {categoryOptions.map(cat => (
                  <Badge key={cat.id} variant={newFestival.categories.includes(cat.id) ? 'default' : 'outline'} className={`cursor-pointer ${newFestival.categories.includes(cat.id) ? 'bg-purple-500' : 'hover:bg-white/10'}`}
                    onClick={() => {
                      if (newFestival.categories.includes(cat.id)) {
                        setNewFestival({...newFestival, categories: newFestival.categories.filter(c => c !== cat.id)});
                      } else {
                        setNewFestival({...newFestival, categories: [...newFestival.categories, cat.id]});
                      }
                    }}>
                    {cat.name}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs">{language === 'it' ? 'Costo Partecipazione' : 'Participation Cost'}</Label>
                <Input type="number" value={newFestival.base_participation_cost} onChange={e => setNewFestival({...newFestival, base_participation_cost: parseInt(e.target.value) || 10000})} className="bg-black/20 border-white/10" />
              </div>
              <div>
                <Label className="text-xs">{language === 'it' ? 'Durata (giorni)' : 'Duration (days)'}</Label>
                <Input type="number" value={newFestival.duration_days} onChange={e => setNewFestival({...newFestival, duration_days: parseInt(e.target.value) || 7})} min={1} max={30} className="bg-black/20 border-white/10" />
              </div>
            </div>
            {creationCost && (
              <Card className="bg-purple-500/10 border-purple-500/30">
                <CardContent className="p-3">
                  <div className="flex justify-between items-center">
                    <span>{language === 'it' ? 'Costo Creazione' : 'Creation Cost'}</span>
                    <span className="text-purple-400 font-bold">${creationCost.creation_cost?.toLocaleString()}</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>{language === 'it' ? 'Annulla' : 'Cancel'}</Button>
            <Button onClick={createCustomFestival} disabled={creating || !newFestival.name || newFestival.categories.length === 0} className="bg-purple-500">
              {creating ? 'Creazione...' : language === 'it' ? 'Crea Festival' : 'Create Festival'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div>
          <div className="flex gap-2 mb-4 justify-center">
            {['monthly', 'yearly', 'all_time'].map(p => (
              <Button key={p} variant={leaderboardPeriod === p ? 'default' : 'outline'} size="sm" onClick={() => {setLeaderboardPeriod(p); loadLeaderboard(p);}} className={leaderboardPeriod === p ? 'bg-yellow-500 text-black' : ''}>
                {periodLabels[p]}
              </Button>
            ))}
          </div>
          
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader><CardTitle className="font-['Bebas_Neue'] text-xl">{language === 'it' ? 'Classifica Premi' : 'Awards Leaderboard'} - {periodLabels[leaderboardPeriod]}</CardTitle></CardHeader>
            <CardContent>
              {leaderboard?.leaderboard?.length > 0 ? (
                <div className="space-y-2">
                  {leaderboard.leaderboard.map((entry, i) => (
                    <div key={entry.user_id} className={`flex items-center gap-3 p-3 rounded ${i < 3 ? 'bg-yellow-500/10' : 'bg-white/5'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${i === 0 ? 'bg-yellow-500 text-black' : i === 1 ? 'bg-gray-400 text-black' : i === 2 ? 'bg-amber-600 text-black' : 'bg-white/10'}`}>
                        {entry.rank}
                      </div>
                      <img src={entry.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${entry.nickname}`} alt="" className="w-10 h-10 rounded-full" />
                      <div className="flex-1">
                        <p className="font-semibold">{entry.nickname}</p>
                        <p className="text-xs text-gray-400">Lv.{entry.level} • {entry.fame} {language === 'it' ? 'Fama' : 'Fame'}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-yellow-400 font-bold">{entry.total_awards} <Trophy className="w-4 h-4 inline" /></p>
                        <p className="text-xs text-gray-500">{entry.total_prestige} prestige</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">{language === 'it' ? 'Nessun premio assegnato ancora' : 'No awards yet'}</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* My Awards Tab */}
      {activeTab === 'my_awards' && (
        <div>
          {myAwards?.stats && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30 mb-6">
              <CardContent className="p-6">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <Trophy className="w-8 h-8 text-yellow-500 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-yellow-400">{myAwards.stats.total_awards}</p>
                    <p className="text-xs text-gray-400">{language === 'it' ? 'Premi Totali' : 'Total Awards'}</p>
                  </div>
                  <div>
                    <Star className="w-8 h-8 text-purple-400 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-purple-400">{Object.keys(myAwards.stats.by_festival).length}</p>
                    <p className="text-xs text-gray-400">{language === 'it' ? 'Festival Vinti' : 'Festivals Won'}</p>
                  </div>
                  <div>
                    <Award className="w-8 h-8 text-pink-400 mx-auto mb-1" />
                    <p className="text-2xl font-bold text-pink-400">{Object.keys(myAwards.stats.by_category).length}</p>
                    <p className="text-xs text-gray-400">{language === 'it' ? 'Categorie' : 'Categories'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader><CardTitle className="font-['Bebas_Neue'] text-xl">{language === 'it' ? 'I Miei Premi' : 'My Awards'}</CardTitle></CardHeader>
            <CardContent>
              {myAwards?.awards?.length > 0 ? (
                <div className="space-y-2">
                  {myAwards.awards.map(award => (
                    <div key={award.id} className="flex items-center gap-3 p-3 bg-white/5 rounded">
                      <Award className="w-8 h-8 text-yellow-500" />
                      <div className="flex-1">
                        <p className="font-semibold text-yellow-400">{award.category_name}</p>
                        <p className="text-sm">{award.winner_name}</p>
                        <p className="text-xs text-gray-400">{award.festival_name} • {award.film_title}</p>
                      </div>
                      <div className="text-right text-xs text-gray-500">
                        {award.month}/{award.year}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Trophy className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400">{language === 'it' ? 'Non hai ancora vinto premi. Partecipa ai festival!' : 'No awards yet. Participate in festivals!'}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Live Ceremony Modal */}
      {showLiveCeremony && liveCeremony && (
        <div className="fixed inset-0 bg-black/95 z-50 flex flex-col" onClick={closeLiveCeremony}>
          
          {/* Spotlight Effect */}
          {showSpotlight && (
            <div className="fixed inset-0 z-[55] pointer-events-none overflow-hidden">
              {/* Radial spotlight from top */}
              <motion.div
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px]"
                style={{
                  background: 'radial-gradient(ellipse at center top, rgba(255,215,0,0.3) 0%, rgba(255,215,0,0.1) 30%, transparent 70%)',
                }}
              />
              {/* Moving spotlight beams */}
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-0 left-1/4 w-32 h-[100vh] origin-top"
                style={{
                  background: 'linear-gradient(180deg, rgba(255,215,0,0.2) 0%, transparent 100%)',
                  transform: 'rotate(-15deg)',
                }}
              />
              <motion.div
                animate={{ rotate: [0, -10, 10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                className="absolute top-0 right-1/4 w-32 h-[100vh] origin-top"
                style={{
                  background: 'linear-gradient(180deg, rgba(255,215,0,0.2) 0%, transparent 100%)',
                  transform: 'rotate(15deg)',
                }}
              />
              {/* Golden particles */}
              {[...Array(20)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-2 h-2 bg-yellow-400 rounded-full"
                  initial={{ 
                    x: Math.random() * window.innerWidth, 
                    y: -20,
                    opacity: 0 
                  }}
                  animate={{ 
                    y: window.innerHeight + 20,
                    opacity: [0, 1, 1, 0],
                    scale: [0.5, 1, 0.5]
                  }}
                  transition={{ 
                    duration: 3 + Math.random() * 2,
                    repeat: Infinity,
                    delay: Math.random() * 2,
                    ease: "linear"
                  }}
                />
              ))}
            </div>
          )}

          {/* Subtitle Overlay */}
          {subtitleVisible && (
            <motion.div 
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 50 }}
              className="fixed inset-0 z-[60] pointer-events-none flex items-center justify-center"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
              <div className="absolute bottom-20 left-0 right-0 px-8">
                <motion.div 
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  className="max-w-3xl mx-auto text-center"
                >
                  {/* Category name */}
                  <motion.p 
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-yellow-500 text-lg font-semibold mb-2 uppercase tracking-wider"
                  >
                    {categoryWon}
                  </motion.p>
                  
                  {/* Main subtitle text */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="bg-black/70 backdrop-blur-sm rounded-xl px-8 py-6 border border-yellow-500/30"
                  >
                    <p className="text-white text-2xl md:text-3xl font-['Bebas_Neue'] leading-relaxed">
                      {subtitleText}
                    </p>
                  </motion.div>
                  
                  {/* Winner spotlight */}
                  {winnerName && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 1.5, type: "spring", stiffness: 200 }}
                      className="mt-6"
                    >
                      <div className="inline-flex items-center gap-3 bg-yellow-500 text-black px-6 py-3 rounded-full">
                        <Trophy className="w-6 h-6" />
                        <span className="text-xl font-bold">{winnerName}</span>
                        <Trophy className="w-6 h-6" />
                      </div>
                    </motion.div>
                  )}
                  
                  {/* Audio wave animation */}
                  {playingAudio && (
                    <div className="mt-4 flex justify-center gap-1">
                      {[...Array(5)].map((_, i) => (
                        <motion.div
                          key={i}
                          className="w-1 bg-yellow-500 rounded-full"
                          animate={{ height: [8, 24, 8] }}
                          transition={{ 
                            duration: 0.5, 
                            repeat: Infinity, 
                            delay: i * 0.1,
                            ease: "easeInOut"
                          }}
                        />
                      ))}
                    </div>
                  )}
                </motion.div>
              </div>
            </motion.div>
          )}

          <div className="flex-1 overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            {/* Main ceremony area - scrollable */}
            <div className="flex-1 p-3 sm:p-4 overflow-y-auto min-h-0">
              <div className="max-w-4xl mx-auto">
                {/* Header - Mobile Optimized */}
                <div className="flex items-start justify-between mb-4 gap-2">
                  <div className="flex-1 min-w-0">
                    <h1 className="font-['Bebas_Neue'] text-xl sm:text-3xl text-yellow-400 flex items-center gap-2 truncate">
                      <Tv className="w-5 h-5 sm:w-8 sm:h-8 flex-shrink-0" />
                      <span className="truncate">{liveCeremony.festival_name}</span>
                    </h1>
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs sm:text-sm text-gray-400 mt-1">
                      <span className="flex items-center gap-1">
                        <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                        LIVE • {liveCeremony.viewers_count} {language === 'it' ? 'spettatori' : 'viewers'}
                      </span>
                      <span className="px-1.5 py-0.5 bg-green-500/20 rounded-full text-green-400 text-[10px] sm:text-xs flex items-center gap-1">
                        <TrendingUp className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                        +{viewingBonus.bonus_percent.toFixed(1)}% ({viewingBonus.viewing_minutes.toFixed(0)}min)
                      </span>
                    </div>
                    {playingAudio && (
                      <span className="inline-flex items-center gap-1 text-green-400 text-xs mt-1">
                        <Music className="w-3 h-3 animate-bounce" />
                        {language === 'it' ? 'Audio...' : 'Playing...'}
                      </span>
                    )}
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={closeLiveCeremony} 
                    className="bg-red-500/10 border-red-500/50 hover:bg-red-500 hover:text-white h-8 px-2 sm:px-3 flex-shrink-0"
                  >
                    <X className="w-4 h-4" />
                    <span className="hidden sm:inline ml-1">{language === 'it' ? 'Chiudi' : 'Close'}</span>
                  </Button>
                </div>

                {/* Categories with odds/papabili - Mobile Optimized */}
                <div className="space-y-3">
                  {liveCeremony.categories?.map((cat, idx) => (
                    <Card key={cat.category_id} className={`bg-[#1A1A1A] border-white/10 ${cat.is_announced ? 'border-yellow-500/50' : ''}`}>
                      <CardHeader className="pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <CardTitle className="font-['Bebas_Neue'] text-base sm:text-lg flex items-center gap-2">
                            <Award className="w-4 h-4 sm:w-5 sm:h-5 text-yellow-500" />
                            {cat.category_name}
                          </CardTitle>
                          <div className="flex items-center gap-2 flex-wrap">
                            {cat.is_announced ? (
                              <Badge className="bg-yellow-500 text-black text-[10px] sm:text-xs">{language === 'it' ? 'VINCITORE' : 'WINNER'}</Badge>
                            ) : cat.favorite && (
                              <Badge className="bg-purple-500/20 text-purple-400 text-[10px] sm:text-xs">
                                {language === 'it' ? 'Papabile' : 'Fav'}: {cat.favorite.name.split(' ')[0]} ({cat.favorite.win_probability}%)
                              </Badge>
                            )}
                            {!cat.is_announced && (
                              <Button 
                                size="sm"
                                onClick={() => announceWinnerWithAudio(cat.category_id)}
                                disabled={announcingCategory === cat.category_id}
                                className="bg-red-500 hover:bg-red-600 text-white text-[10px] sm:text-xs h-6 sm:h-7 px-2"
                              >
                                {announcingCategory === cat.category_id ? (
                                  <RefreshCw className="w-3 h-3 animate-spin" />
                                ) : (
                                  <><Music className="w-3 h-3 mr-1" />{language === 'it' ? 'Annuncia' : 'Announce'}</>
                                )}
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
                        <div className="grid gap-1.5 sm:gap-2">
                          {cat.nominees?.map(nom => (
                            <div 
                              key={nom.id} 
                              className={`flex items-center gap-2 sm:gap-3 p-1.5 sm:p-2 rounded transition-all ${cat.winner?.id === nom.id ? 'bg-yellow-500/20 border border-yellow-500 animate-pulse' : 'bg-white/5'}`}
                            >
                              <div className="flex-1 min-w-0">
                                <p className={`font-medium text-sm sm:text-base truncate ${cat.winner?.id === nom.id ? 'text-yellow-400' : ''}`}>
                                  {nom.name}
                                  {cat.winner?.id === nom.id && <Trophy className="w-3 h-3 sm:w-4 sm:h-4 inline ml-1 text-yellow-500" />}
                                </p>
                                {nom.film_title && <p className="text-[10px] sm:text-xs text-gray-400 truncate">{nom.film_title}</p>}
                              </div>
                              <div className="text-right flex-shrink-0">
                                <div className="text-xs sm:text-sm font-bold" style={{color: `hsl(${nom.win_probability * 1.2}, 70%, 50%)`}}>
                                  {nom.win_probability}%
                                </div>
                                <div className="text-[9px] sm:text-xs text-gray-500">{nom.votes} {language === 'it' ? 'voti' : 'votes'}</div>
                              </div>
                              {/* Win probability bar */}
                              <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-gradient-to-r from-purple-500 to-yellow-500 transition-all"
                                  style={{width: `${nom.win_probability}%`}}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>

            {/* Chat sidebar - responsive for mobile */}
            <div className="w-full md:w-80 bg-[#0D0D0D] border-t md:border-t-0 md:border-l border-white/10 flex flex-col max-h-[40vh] md:max-h-none">
              <div className="p-3 border-b border-white/10 flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  {language === 'it' ? 'Chat Live' : 'Live Chat'}
                </h3>
                {/* Close button for mobile */}
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={closeLiveCeremony}
                  className="md:hidden h-7 w-7 p-0 text-gray-400 hover:text-red-400"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              
              {/* Chat messages */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-[100px]">
                {liveCeremony.chat_messages?.map(msg => (
                  <div key={msg.id} className="text-sm">
                    <span className="font-semibold text-yellow-400">{msg.nickname}:</span>
                    <span className="text-gray-300 ml-1">{msg.message}</span>
                  </div>
                ))}
                {(!liveCeremony.chat_messages || liveCeremony.chat_messages.length === 0) && (
                  <p className="text-gray-500 text-center text-sm">{language === 'it' ? 'Nessun messaggio ancora' : 'No messages yet'}</p>
                )}
              </div>
              
              {/* Chat input */}
              <div className="p-2 md:p-3 border-t border-white/10">
                <div className="flex gap-2">
                  <Input 
                    value={chatMessage}
                    onChange={e => setChatMessage(e.target.value)}
                    placeholder={language === 'it' ? 'Scrivi...' : 'Type...'}
                    className="flex-1 bg-white/5 border-white/10 text-sm h-9 md:h-8"
                    maxLength={200}
                    onKeyDown={e => e.key === 'Enter' && sendChatMessage()}
                  />
                  <Button 
                    size="sm" 
                    onClick={sendChatMessage} 
                    disabled={sendingChat || !chatMessage.trim()}
                    className="bg-yellow-500 text-black h-9 md:h-8 px-3"
                  >
                    <Send className="w-4 h-4 md:w-3 md:h-3" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Sagas & Series Page
const SagasSeriesPage = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const [activeTab, setActiveTab] = useState('sagas');
  const [myFilms, setMyFilms] = useState([]);
  const [mySagas, setMySagas] = useState([]);
  const [mySeries, setMySeries] = useState([]);
  const [canCreateSequel, setCanCreateSequel] = useState(null);
  const [canCreateSeries, setCanCreateSeries] = useState(null);
  const [canCreateAnime, setCanCreateAnime] = useState(null);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [showCreateSeriesDialog, setShowCreateSeriesDialog] = useState(false);
  const [seriesType, setSeriesType] = useState('tv_series');
  const [creating, setCreating] = useState(false);
  const [newSeries, setNewSeries] = useState({ title: '', genre: 'drama', episodes_count: 10, episode_length: 45, synopsis: '' });

  const labels = {
    sagas: language === 'it' ? 'Saghe & Sequel' : 'Sagas & Sequels',
    series: language === 'it' ? 'Serie TV' : 'TV Series',
    anime: language === 'it' ? 'Anime' : 'Anime',
    create_sequel: language === 'it' ? 'Crea Sequel' : 'Create Sequel',
    create_series: language === 'it' ? 'Crea Serie TV' : 'Create TV Series',
    create_anime: language === 'it' ? 'Crea Anime' : 'Create Anime',
    required_level: language === 'it' ? 'Livello richiesto' : 'Required level',
    required_fame: language === 'it' ? 'Fama richiesta' : 'Required fame',
    no_films: language === 'it' ? 'Non hai film idonei per creare sequel' : 'No eligible films for sequel',
    select_film: language === 'it' ? 'Seleziona un film per creare un sequel' : 'Select a film to create a sequel',
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [filmsRes, seriesRes, sequelCheck, tvCheck, animeCheck] = await Promise.all([
        api.get('/films/my'),
        api.get('/series/my').catch(() => ({ data: { series: [] } })),
        api.get('/saga/can-create').catch(() => ({ data: { can_create: false } })),
        api.get('/series/can-create?series_type=tv_series').catch(() => ({ data: { can_create: false } })),
        api.get('/series/can-create?series_type=anime').catch(() => ({ data: { can_create: false } })),
      ]);
      setMyFilms(filmsRes.data || []);
      setMySeries(seriesRes.data?.series || []);
      setCanCreateSequel(sequelCheck.data);
      setCanCreateSeries(tvCheck.data);
      setCanCreateAnime(animeCheck.data);
      
      // Group films into sagas
      const sagas = {};
      (filmsRes.data || []).forEach(film => {
        if (film.saga_id) {
          if (!sagas[film.saga_id]) sagas[film.saga_id] = [];
          sagas[film.saga_id].push(film);
        }
      });
      setMySagas(Object.values(sagas));
    } catch (e) {
      console.error(e);
    }
  };

  const createSequel = async (filmId) => {
    setCreating(true);
    try {
      const res = await api.post(`/films/${filmId}/create-sequel`);
      toast.success(res.data.message || 'Sequel creato!');
      loadData();
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore creazione sequel');
    } finally {
      setCreating(false);
    }
  };

  const createSeries = async () => {
    if (!newSeries.title.trim()) { toast.error('Inserisci un titolo'); return; }
    setCreating(true);
    try {
      const res = await api.post('/series/create', { ...newSeries, series_type: seriesType });
      toast.success(`${seriesType === 'anime' ? 'Anime' : 'Serie TV'} creata! +200 XP`);
      setShowCreateSeriesDialog(false);
      setNewSeries({ title: '', genre: 'drama', episodes_count: 10, episode_length: 45, synopsis: '' });
      loadData();
      refreshUser();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore creazione');
    } finally {
      setCreating(false);
    }
  };

  const genres = ['action', 'comedy', 'drama', 'horror', 'sci-fi', 'romance', 'thriller', 'fantasy', 'animation'];

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="sagas-series-page">
      <div className="text-center mb-6">
        <BookOpen className="w-12 h-12 text-purple-500 mx-auto mb-2" />
        <h1 className="font-['Bebas_Neue'] text-3xl">{language === 'it' ? 'Saghe e Serie' : 'Sagas & Series'}</h1>
        <p className="text-gray-400 text-sm">{language === 'it' ? 'Espandi il tuo universo cinematografico' : 'Expand your cinematic universe'}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 justify-center flex-wrap">
        <Button variant={activeTab === 'sagas' ? 'default' : 'outline'} onClick={() => setActiveTab('sagas')} className={activeTab === 'sagas' ? 'bg-purple-500' : ''}>
          <Film className="w-4 h-4 mr-2" />{labels.sagas}
        </Button>
        <Button variant={activeTab === 'series' ? 'default' : 'outline'} onClick={() => setActiveTab('series')} className={activeTab === 'series' ? 'bg-blue-500' : ''}>
          <Clapperboard className="w-4 h-4 mr-2" />{labels.series}
        </Button>
        <Button variant={activeTab === 'anime' ? 'default' : 'outline'} onClick={() => setActiveTab('anime')} className={activeTab === 'anime' ? 'bg-pink-500' : ''}>
          <Star className="w-4 h-4 mr-2" />{labels.anime}
        </Button>
      </div>

      {/* Sagas Tab */}
      {activeTab === 'sagas' && (
        <div className="space-y-4">
          {/* Requirements Card */}
          <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30">
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="font-['Bebas_Neue'] text-lg text-purple-400">{labels.create_sequel}</h3>
                  <p className="text-xs text-gray-400">
                    {canCreateSequel?.can_create 
                      ? `${language === 'it' ? 'Puoi creare sequel!' : 'You can create sequels!'}`
                      : `${labels.required_level}: ${canCreateSequel?.required_level || 15} (${language === 'it' ? 'sei' : "you're"} ${canCreateSequel?.current_level || 1}) • ${labels.required_fame}: ${canCreateSequel?.required_fame || 100} (${language === 'it' ? 'hai' : "you have"} ${canCreateSequel?.current_fame || 50})`}
                  </p>
                </div>
                {canCreateSequel?.can_create && (
                  <Badge className="bg-green-500/20 text-green-400">{language === 'it' ? 'Sbloccato!' : 'Unlocked!'}</Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Eligible Films for Sequel */}
          {canCreateSequel?.can_create && (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg">{labels.select_film}</CardTitle>
              </CardHeader>
              <CardContent>
                {myFilms.filter(f => f.status !== 'in_production' && !f.is_sequel).length === 0 ? (
                  <p className="text-gray-400 text-center py-4">{labels.no_films}</p>
                ) : (
                  <ScrollArea className="h-[300px]">
                    <div className="grid sm:grid-cols-2 gap-3">
                      {myFilms.filter(f => f.status !== 'in_production' && !f.is_sequel).map(film => (
                        <Card key={film.id} className="bg-white/5 border-white/10">
                          <CardContent className="p-3">
                            <div className="flex items-center gap-3">
                              {film.poster_url && !film.poster_url.startsWith('data:') ? (
                                <img src={film.poster_url} alt="" className="w-12 h-16 object-cover rounded" />
                              ) : (
                                <div className="w-12 h-16 bg-white/10 rounded flex items-center justify-center"><Film className="w-6 h-6 text-gray-500" /></div>
                              )}
                              <div className="flex-1 min-w-0">
                                <p className="font-semibold truncate">{film.title}</p>
                                <p className="text-xs text-gray-400">{film.genre} • {film.sequel_count || 0} sequel</p>
                              </div>
                              <Button size="sm" onClick={() => createSequel(film.id)} disabled={creating || (film.sequel_count || 0) >= 5} className="bg-purple-500 hover:bg-purple-400">
                                <Plus className="w-4 h-4" />
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          )}

          {/* Existing Sagas */}
          {mySagas.length > 0 && (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardHeader className="pb-2">
                <CardTitle className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Le Tue Saghe' : 'Your Sagas'}</CardTitle>
              </CardHeader>
              <CardContent>
                {mySagas.map((saga, i) => (
                  <div key={i} className="p-3 bg-white/5 rounded mb-2">
                    <p className="font-semibold mb-2">{saga[0]?.saga_name || `Saga ${i+1}`}</p>
                    <div className="flex gap-2 overflow-x-auto pb-2">
                      {saga.map((film, j) => (
                        <div key={film.id} className="flex-shrink-0 w-20 text-center">
                          <div className="w-20 h-28 bg-white/10 rounded mb-1 flex items-center justify-center text-xs">#{j+1}</div>
                          <p className="text-xs truncate">{film.title}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Series Tab */}
      {activeTab === 'series' && (
        <div className="space-y-4">
          <Card className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/30">
            <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="font-['Bebas_Neue'] text-lg text-blue-400">{labels.create_series}</h3>
                <p className="text-xs text-gray-400">
                  {canCreateSeries?.can_create 
                    ? `${language === 'it' ? 'Puoi creare serie TV!' : 'You can create TV series!'}`
                    : `${labels.required_level}: ${canCreateSeries?.required_level || 20} • ${labels.required_fame}: ${canCreateSeries?.required_fame || 200}`}
                </p>
              </div>
              <Button onClick={() => { setSeriesType('tv_series'); setShowCreateSeriesDialog(true); }} disabled={!canCreateSeries?.can_create} className="bg-blue-500 hover:bg-blue-400">
                <Plus className="w-4 h-4 mr-2" />{labels.create_series}
              </Button>
            </CardContent>
          </Card>

          {/* My Series */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'Le Tue Serie TV' : 'Your TV Series'}</CardTitle>
            </CardHeader>
            <CardContent>
              {mySeries.filter(s => s.series_type === 'tv_series').length === 0 ? (
                <p className="text-gray-400 text-center py-8">{language === 'it' ? 'Non hai ancora serie TV' : 'No TV series yet'}</p>
              ) : (
                <div className="grid sm:grid-cols-2 gap-3">
                  {mySeries.filter(s => s.series_type === 'tv_series').map(series => (
                    <Card key={series.id} className="bg-white/5 border-white/10">
                      <CardContent className="p-3">
                        <div className="flex items-center gap-3">
                          <Clapperboard className="w-10 h-10 text-blue-400" />
                          <div className="flex-1">
                            <p className="font-semibold">{series.title}</p>
                            <p className="text-xs text-gray-400">{series.episodes_count} episodi • {series.genre}</p>
                            <Badge className={series.status === 'in_production' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'} variant="outline">
                              {series.status === 'in_production' ? 'In Produzione' : series.status}
                            </Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Anime Tab */}
      {activeTab === 'anime' && (
        <div className="space-y-4">
          <Card className="bg-gradient-to-r from-pink-500/10 to-purple-500/10 border-pink-500/30">
            <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="font-['Bebas_Neue'] text-lg text-pink-400">{labels.create_anime}</h3>
                <p className="text-xs text-gray-400">
                  {canCreateAnime?.can_create 
                    ? `${language === 'it' ? 'Puoi creare anime!' : 'You can create anime!'}`
                    : `${labels.required_level}: ${canCreateAnime?.required_level || 25} • ${labels.required_fame}: ${canCreateAnime?.required_fame || 300}`}
                </p>
              </div>
              <Button onClick={() => { setSeriesType('anime'); setShowCreateSeriesDialog(true); }} disabled={!canCreateAnime?.can_create} className="bg-pink-500 hover:bg-pink-400">
                <Plus className="w-4 h-4 mr-2" />{labels.create_anime}
              </Button>
            </CardContent>
          </Card>

          {/* My Anime */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Bebas_Neue'] text-lg">{language === 'it' ? 'I Tuoi Anime' : 'Your Anime'}</CardTitle>
            </CardHeader>
            <CardContent>
              {mySeries.filter(s => s.series_type === 'anime').length === 0 ? (
                <p className="text-gray-400 text-center py-8">{language === 'it' ? 'Non hai ancora anime' : 'No anime yet'}</p>
              ) : (
                <div className="grid sm:grid-cols-2 gap-3">
                  {mySeries.filter(s => s.series_type === 'anime').map(series => (
                    <Card key={series.id} className="bg-white/5 border-white/10">
                      <CardContent className="p-3">
                        <div className="flex items-center gap-3">
                          <Star className="w-10 h-10 text-pink-400" />
                          <div className="flex-1">
                            <p className="font-semibold">{series.title}</p>
                            <p className="text-xs text-gray-400">{series.episodes_count} episodi • {series.genre}</p>
                            <Badge className={series.status === 'in_production' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'} variant="outline">
                              {series.status === 'in_production' ? 'In Produzione' : series.status}
                            </Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Series/Anime Dialog */}
      <Dialog open={showCreateSeriesDialog} onOpenChange={setShowCreateSeriesDialog}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
              {seriesType === 'anime' ? <Star className="w-5 h-5 text-pink-400" /> : <Clapperboard className="w-5 h-5 text-blue-400" />}
              {seriesType === 'anime' ? labels.create_anime : labels.create_series}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs">{language === 'it' ? 'Titolo' : 'Title'}</Label>
              <Input value={newSeries.title} onChange={e => setNewSeries({...newSeries, title: e.target.value})} placeholder={seriesType === 'anime' ? 'Il mio anime...' : 'La mia serie...'} className="bg-black/20 border-white/10" />
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Genere' : 'Genre'}</Label>
              <select value={newSeries.genre} onChange={e => setNewSeries({...newSeries, genre: e.target.value})} className="w-full h-9 rounded bg-black/20 border border-white/10 text-sm px-2">
                {genres.map(g => <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs">{language === 'it' ? 'Episodi' : 'Episodes'}</Label>
                <Input type="number" value={newSeries.episodes_count} onChange={e => setNewSeries({...newSeries, episodes_count: parseInt(e.target.value) || 10})} min={1} max={100} className="bg-black/20 border-white/10" />
              </div>
              <div>
                <Label className="text-xs">{language === 'it' ? 'Durata (min)' : 'Length (min)'}</Label>
                <Input type="number" value={newSeries.episode_length} onChange={e => setNewSeries({...newSeries, episode_length: parseInt(e.target.value) || 45})} min={10} max={120} className="bg-black/20 border-white/10" />
              </div>
            </div>
            <div>
              <Label className="text-xs">{language === 'it' ? 'Sinossi' : 'Synopsis'}</Label>
              <Textarea value={newSeries.synopsis} onChange={e => setNewSeries({...newSeries, synopsis: e.target.value})} placeholder={language === 'it' ? 'La trama della serie...' : 'Series plot...'} className="bg-black/20 border-white/10 h-20" />
            </div>
            <Card className="bg-white/5 border-white/10">
              <CardContent className="p-3">
                <div className="flex justify-between items-center">
                  <span>{language === 'it' ? 'Budget totale' : 'Total budget'}</span>
                  <span className="text-yellow-400 font-bold">${((seriesType === 'anime' ? 30000 : 50000) * newSeries.episodes_count).toLocaleString()}</span>
                </div>
              </CardContent>
            </Card>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateSeriesDialog(false)}>{language === 'it' ? 'Annulla' : 'Cancel'}</Button>
            <Button onClick={createSeries} disabled={creating || !newSeries.title} className={seriesType === 'anime' ? 'bg-pink-500' : 'bg-blue-500'}>
              {creating ? '...' : language === 'it' ? 'Crea' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Leaderboard Page
const LeaderboardPage = () => {
  const { api, user } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [globalLeaderboard, setGlobalLeaderboard] = useState([]);
  const [localLeaderboard, setLocalLeaderboard] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('global');

  useEffect(() => {
    api.get('/leaderboard/global?limit=50').then(r => {
      setGlobalLeaderboard(r.data.leaderboard);
      setLoading(false);
    });
  }, [api]);

  const loadLocalLeaderboard = async (country) => {
    setSelectedCountry(country);
    const res = await api.get(`/leaderboard/local/${country}?limit=50`);
    setLocalLeaderboard(res.data.leaderboard);
  };

  const getRankBadge = (rank) => {
    if (rank === 1) return <div className="w-6 h-6 rounded-full bg-yellow-500 flex items-center justify-center text-black font-bold text-xs">1</div>;
    if (rank === 2) return <div className="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center text-black font-bold text-xs">2</div>;
    if (rank === 3) return <div className="w-6 h-6 rounded-full bg-amber-600 flex items-center justify-center text-black font-bold text-xs">3</div>;
    return <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-gray-400 font-bold text-xs">{rank}</div>;
  };

  const PlayerRow = ({ player, showRank = true }) => (
    <div className="flex items-center gap-3 p-2 rounded hover:bg-white/5 cursor-pointer" onClick={() => navigate(`/player/${player.id}`)}>
      {showRank && getRankBadge(player.rank)}
      <Avatar className="w-8 h-8 border border-white/10">
        <AvatarImage src={player.avatar_url} />
        <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xs">{player.nickname?.[0]}</AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1">
          <span className="font-semibold text-sm truncate">{player.nickname}</span>
          <Badge className="bg-purple-500/20 text-purple-400 text-[10px] h-4">Lv.{player.level_info?.level || 0}</Badge>
        </div>
        <p className="text-[10px] text-gray-400 truncate">{player.production_house_name}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold text-yellow-500">{player.leaderboard_score?.toFixed(1)}</p>
        <p className="text-[10px] text-gray-400">Fame: {player.fame?.toFixed(0) || 50}</p>
      </div>
    </div>
  );

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="leaderboard-page">
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2">
            <Trophy className="w-6 h-6 text-yellow-500" /> Classifica
          </CardTitle>
          <CardDescription>La classifica si basa sulla media di Livello, Fama e Ricavi</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-black/20 mb-4">
              <TabsTrigger value="global" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                <Globe className="w-4 h-4 mr-1" /> Globale
              </TabsTrigger>
              <TabsTrigger value="local" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                <MapPin className="w-4 h-4 mr-1" /> Locale
              </TabsTrigger>
            </TabsList>

            <TabsContent value="global">
              {loading ? (
                <div className="text-center py-8"><RefreshCw className="w-6 h-6 animate-spin mx-auto text-yellow-500" /></div>
              ) : (
                <ScrollArea className="h-[500px]">
                  <div className="space-y-1">
                    {globalLeaderboard.map(player => <PlayerRow key={player.id} player={player} />)}
                  </div>
                </ScrollArea>
              )}
            </TabsContent>

            <TabsContent value="local">
              <div className="mb-4">
                <Select value={selectedCountry} onValueChange={loadLocalLeaderboard}>
                  <SelectTrigger className="h-9 bg-black/20 border-white/10">
                    <SelectValue placeholder="Seleziona un paese" />
                  </SelectTrigger>
                  <SelectContent>
                    {['USA', 'Italy', 'Spain', 'France', 'Germany', 'UK', 'Japan', 'China', 'Brazil', 'India'].map(c => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {localLeaderboard.length > 0 ? (
                <ScrollArea className="h-[450px]">
                  <div className="space-y-1">
                    {localLeaderboard.map(player => <PlayerRow key={player.id} player={player} />)}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-center text-gray-400 py-8">Seleziona un paese per vedere la classifica locale</p>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

// Player Public Profile Page
const PlayerPublicProfile = () => {
  const { api, user } = useContext(AuthContext);
  const { t } = useTranslations();
  const navigate = useNavigate();
  const [player, setPlayer] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const playerId = window.location.pathname.split('/').pop();
    api.get(`/players/${playerId}/profile`).then(r => {
      setPlayer(r.data);
      setLoading(false);
    }).catch(() => {
      toast.error('Giocatore non trovato');
      navigate('/leaderboard');
    });
  }, [api, navigate]);

  if (loading) return <div className="pt-16 flex items-center justify-center h-96"><RefreshCw className="w-8 h-8 animate-spin text-yellow-500" /></div>;
  if (!player) return null;

  return (
    <div className="pt-16 pb-20 px-3 max-w-2xl mx-auto" data-testid="player-profile-page">
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <Avatar className="w-20 h-20 border-2 border-yellow-500/30">
              <AvatarImage src={player.avatar_url} />
              <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-2xl">{player.nickname?.[0]}</AvatarFallback>
            </Avatar>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-['Bebas_Neue'] text-2xl">{player.nickname}</h1>
                <Badge className="bg-purple-500/20 text-purple-400">Lv.{player.level}</Badge>
              </div>
              <p className="text-gray-400">{player.production_house_name}</p>
              <div className="flex items-center gap-2 mt-1">
                <Badge className="bg-yellow-500/20 text-yellow-400">Fame: {player.fame?.toFixed(0)}</Badge>
                <Badge className={`${player.fame_tier?.name === 'Legend' ? 'bg-yellow-500 text-black' : 'bg-white/10'}`}>
                  {player.fame_tier?.name}
                </Badge>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            <div className="p-3 rounded bg-white/5 text-center">
              <Film className="w-5 h-5 mx-auto mb-1 text-yellow-500" />
              <p className="text-lg font-bold">{player.films_count}</p>
              <p className="text-xs text-gray-400">Film</p>
            </div>
            <div className="p-3 rounded bg-white/5 text-center">
              <Building className="w-5 h-5 mx-auto mb-1 text-blue-400" />
              <p className="text-lg font-bold">{player.infrastructure_count}</p>
              <p className="text-xs text-gray-400">Infrastrutture</p>
            </div>
            <div className="p-3 rounded bg-white/5 text-center">
              <Heart className="w-5 h-5 mx-auto mb-1 text-red-400" />
              <p className="text-lg font-bold">{player.total_likes_received}</p>
              <p className="text-xs text-gray-400">Like ricevuti</p>
            </div>
            <div className="p-3 rounded bg-white/5 text-center">
              <Trophy className="w-5 h-5 mx-auto mb-1 text-yellow-500" />
              <p className="text-lg font-bold">{player.leaderboard_score?.toFixed(1)}</p>
              <p className="text-xs text-gray-400">Punteggio</p>
            </div>
          </div>

          {/* Level Progress */}
          <div className="p-3 rounded bg-purple-500/10 border border-purple-500/20 mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span>Level {player.level}</span>
              <span className="text-purple-400">{player.level_info?.current_xp} / {player.level_info?.xp_for_next_level} XP</span>
            </div>
            <Progress value={player.level_info?.progress_percent || 0} className="h-2" />
          </div>

          {player.id !== user?.id && (
            <Button className="w-full bg-yellow-500 text-black" onClick={() => navigate(`/chat?dm=${player.id}`)}>
              <MessageSquare className="w-4 h-4 mr-2" /> Invia Messaggio
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Cinema Tour Page
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
const MajorPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const [majorData, setMajorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', description: '', max_members: 20, logo_prompt: '' });
  const [creating, setCreating] = useState(false);
  const [inviteUserId, setInviteUserId] = useState('');
  const [allUsers, setAllUsers] = useState([]);
  
  const t = (key) => {
    const translations = {
      major: language === 'it' ? 'Major' : 'Major',
      createMajor: language === 'it' ? 'Crea Major' : 'Create Major',
      yourMajor: language === 'it' ? 'La Tua Major' : 'Your Major',
      noMajor: language === 'it' ? 'Non sei in una Major' : "You're not in a Major",
      levelRequired: language === 'it' ? 'Richiesto livello 20 per creare' : 'Level 20 required to create',
      members: language === 'it' ? 'Membri' : 'Members',
      invite: language === 'it' ? 'Invita' : 'Invite',
      weeklyChallenge: language === 'it' ? 'Sfida Settimanale' : 'Weekly Challenge',
      bonuses: language === 'it' ? 'Bonus' : 'Bonuses',
      activities: language === 'it' ? 'Attività' : 'Activities',
      rankings: language === 'it' ? 'Classifiche' : 'Rankings'
    };
    return translations[key] || key;
  };
  
  useEffect(() => {
    Promise.all([
      api.get('/major/my'),
      api.get('/users/all')  // Include offline users for invites
    ]).then(([major, users]) => {
      setMajorData(major.data);
      setAllUsers(users.data || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [api]);
  
  const createMajor = async () => {
    try {
      setCreating(true);
      if (createForm.logo_prompt) {
        toast.info(language === 'it' ? 'Generazione logo in corso...' : 'Generating logo...', { duration: 10000 });
      }
      const res = await api.post('/major/create', createForm);
      toast.success(language === 'it' ? 'Major creata con successo!' : 'Major created successfully!');
      setShowCreateModal(false);
      const major = await api.get('/major/my');
      setMajorData(major.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setCreating(false);
    }
  };
  
  const inviteUser = async (userId) => {
    try {
      await api.post('/major/invite', { user_id: userId });
      toast.success(language === 'it' ? 'Invito inviato!' : 'Invite sent!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
  };
  
  if (loading) return <div className="pt-16 p-4 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;
  
  return (
    <div className="pt-16 pb-6 px-3 max-w-4xl mx-auto">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4 flex items-center gap-2">
        <Crown className="w-8 h-8 text-purple-500" />
        {t('major')}
      </h1>
      
      {!majorData?.has_major ? (
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardContent className="p-6 text-center">
            <Crown className="w-16 h-16 mx-auto text-purple-500/50 mb-4" />
            <h2 className="text-xl font-semibold mb-2">{t('noMajor')}</h2>
            <p className="text-gray-400 mb-4">
              {language === 'it' 
                ? 'Crea la tua Major e unisci altri produttori!' 
                : 'Create your Major and unite other producers!'}
            </p>
            
            {/* Requirements */}
            <div className="flex justify-center gap-4 mb-4">
              <div className={`p-2 rounded-lg ${(majorData?.user_level || 0) >= (majorData?.required_level || 20) ? 'bg-green-500/20 border border-green-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Livello' : 'Level'}</p>
                <p className={`font-bold ${(majorData?.user_level || 0) >= (majorData?.required_level || 20) ? 'text-green-400' : 'text-red-400'}`}>
                  {majorData?.user_level || 0}/{majorData?.required_level || 20}
                </p>
              </div>
              <div className={`p-2 rounded-lg ${majorData?.user_funds >= (majorData?.creation_cost || 5000000) ? 'bg-green-500/20 border border-green-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Costo' : 'Cost'}</p>
                <p className={`font-bold ${majorData?.user_funds >= (majorData?.creation_cost || 5000000) ? 'text-green-400' : 'text-red-400'}`}>
                  ${((majorData?.creation_cost || 5000000) / 1000000).toFixed(0)}M
                </p>
              </div>
            </div>
            
            {majorData?.can_create ? (
              <Button className="bg-purple-600 hover:bg-purple-500" onClick={() => setShowCreateModal(true)}>
                <Plus className="w-4 h-4 mr-2" /> {t('createMajor')}
              </Button>
            ) : (
              <div className="space-y-2">
                <Badge className="bg-gray-500/20 text-gray-400">
                  {language === 'it' ? 'Requisiti non soddisfatti' : 'Requirements not met'}
                </Badge>
                <p className="text-xs text-gray-500">
                  {language === 'it' ? 'Fondi disponibili: ' : 'Available funds: '}
                  ${(majorData?.user_funds || 0).toLocaleString()}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Major Header */}
          <Card className="bg-gradient-to-r from-purple-900/30 to-purple-600/10 border-purple-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                {majorData.major?.logo_url ? (
                  <img src={majorData.major.logo_url} alt="" className="w-16 h-16 rounded-lg" />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Crown className="w-8 h-8 text-purple-500" />
                  </div>
                )}
                <div className="flex-1">
                  <h2 className="text-2xl font-bold">{majorData.major?.name}</h2>
                  <p className="text-sm text-gray-400">{majorData.major?.description}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="bg-purple-500/20 text-purple-400">Level {majorData.level}</Badge>
                    <Badge className="bg-white/10 text-gray-300">{majorData.members?.length}/{majorData.major?.max_members} {t('members')}</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Bonuses */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-500" />
                {t('bonuses')}
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded bg-green-500/10 text-center">
                <p className="text-2xl font-bold text-green-500">+{majorData.bonuses?.quality_bonus}%</p>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Qualità' : 'Quality'}</p>
              </div>
              <div className="p-3 rounded bg-yellow-500/10 text-center">
                <p className="text-2xl font-bold text-yellow-500">+{majorData.bonuses?.revenue_bonus}%</p>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Incassi' : 'Revenue'}</p>
              </div>
              <div className="p-3 rounded bg-purple-500/10 text-center">
                <p className="text-2xl font-bold text-purple-500">+{majorData.bonuses?.xp_bonus}%</p>
                <p className="text-xs text-gray-400">XP</p>
              </div>
            </CardContent>
          </Card>
          
          {/* Weekly Challenge */}
          {majorData.weekly_challenge && (
            <Card className="bg-[#1A1A1A] border-yellow-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Target className="w-5 h-5 text-yellow-500" />
                  {t('weeklyChallenge')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <h3 className="font-semibold">{majorData.weekly_challenge.name?.[language] || majorData.weekly_challenge.name?.en || majorData.weekly_challenge.name}</h3>
                <p className="text-sm text-gray-400 mb-2">{majorData.weekly_challenge.description?.[language] || majorData.weekly_challenge.description?.en || majorData.weekly_challenge.description}</p>
                <div className="flex gap-2">
                  <Badge className="bg-yellow-500/20 text-yellow-400">+{majorData.weekly_challenge.rewards?.xp} XP</Badge>
                  <Badge className="bg-green-500/20 text-green-400">+${(majorData.weekly_challenge.rewards?.funds / 1000).toFixed(0)}K</Badge>
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Major Activities */}
          {majorData.activities && Object.keys(majorData.activities).length > 0 && (
            <Card className="bg-[#1A1A1A] border-purple-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Zap className="w-5 h-5 text-purple-500" />
                  {t('activities')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2">
                  {Object.entries(majorData.activities).map(([key, activity]) => (
                    <div key={key} className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm">{activity.name?.[language] || activity.name?.en}</h4>
                          <p className="text-xs text-gray-400 mt-1">{activity.description?.[language] || activity.description?.en}</p>
                        </div>
                        {activity.bonus && (
                          <div className="flex flex-col gap-1 ml-2">
                            {activity.bonus.quality && <Badge className="text-[10px] bg-blue-500/20 text-blue-400">+{activity.bonus.quality}% {language === 'it' ? 'Qualità' : 'Quality'}</Badge>}
                            {activity.bonus.revenue && <Badge className="text-[10px] bg-green-500/20 text-green-400">+{activity.bonus.revenue}% {language === 'it' ? 'Incassi' : 'Revenue'}</Badge>}
                            {activity.bonus.revenue_multiplier && <Badge className="text-[10px] bg-green-500/20 text-green-400">x{activity.bonus.revenue_multiplier} {language === 'it' ? 'Incassi' : 'Revenue'}</Badge>}
                            {activity.bonus.likes && <Badge className="text-[10px] bg-pink-500/20 text-pink-400">+{activity.bonus.likes} Likes</Badge>}
                          </div>
                        )}
                        {activity.discount_percent && (
                          <Badge className="text-[10px] bg-yellow-500/20 text-yellow-400">-{activity.discount_percent}%</Badge>
                        )}
                      </div>
                      {activity.cooldown_hours && (
                        <p className="text-[10px] text-gray-500 mt-2">
                          {language === 'it' ? 'Disponibile ogni' : 'Available every'} {activity.cooldown_hours < 24 ? `${activity.cooldown_hours}h` : `${Math.round(activity.cooldown_hours / 24)}d`}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Members */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center justify-between">
                <span className="flex items-center gap-2"><Users className="w-5 h-5" /> {t('members')}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {majorData.members?.map(member => (
                  <div key={member.user_id} className="flex items-center gap-3 p-2 rounded bg-white/5">
                    <Avatar className="w-10 h-10">
                      <AvatarImage src={member.avatar_url} />
                      <AvatarFallback className="bg-purple-500/20 text-purple-500">{member.nickname?.[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <p className="font-semibold text-sm">{member.nickname}</p>
                      <Badge className={`text-[10px] h-4 ${member.role === 'founder' ? 'bg-yellow-500/20 text-yellow-400' : member.role === 'vice' ? 'bg-purple-500/20 text-purple-400' : 'bg-white/10 text-gray-400'}`}>
                        {MAJOR_ROLES[member.role]?.[language] || member.role}
                      </Badge>
                    </div>
                    <span className="text-xs text-gray-400">Lv.{member.level}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          
          {/* All Users - Invite Section */}
          {(majorData.my_role === 'founder' || majorData.my_role === 'vice') && (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-400" />
                  {language === 'it' ? 'Invita Nuovi Membri' : 'Invite New Members'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Input 
                  placeholder={language === 'it' ? 'Cerca utente per nome...' : 'Search user by name...'} 
                  className="bg-black/30 border-white/10 mb-3"
                  value={inviteUserId}
                  onChange={(e) => setInviteUserId(e.target.value)}
                />
                
                {/* Tabs for Online/Offline */}
                <Tabs defaultValue="all" className="w-full">
                  <TabsList className="grid w-full grid-cols-3 bg-black/30">
                    <TabsTrigger value="all" className="text-xs">
                      {language === 'it' ? 'Tutti' : 'All'} ({allUsers.filter(u => !majorData.members?.some(m => m.user_id === u.id)).length})
                    </TabsTrigger>
                    <TabsTrigger value="online" className="text-xs">
                      <span className="w-2 h-2 rounded-full bg-green-500 mr-1"></span>
                      Online ({allUsers.filter(u => u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length})
                    </TabsTrigger>
                    <TabsTrigger value="offline" className="text-xs">
                      <span className="w-2 h-2 rounded-full bg-gray-500 mr-1"></span>
                      Offline ({allUsers.filter(u => !u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length})
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="all">
                    <ScrollArea className="h-60 mt-2">
                      <div className="space-y-1">
                        {allUsers
                          .filter(u => !majorData.members?.some(m => m.user_id === u.id))
                          .filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase()))
                          .map(u => (
                            <div key={u.id} className="flex items-center justify-between p-2 rounded bg-white/5 hover:bg-white/10 transition-colors">
                              <div className="flex items-center gap-3">
                                <span className={`w-2 h-2 rounded-full ${u.is_online ? 'bg-green-500' : 'bg-gray-500'}`}></span>
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={u.avatar_url} />
                                  <AvatarFallback className="bg-blue-500/20 text-blue-400 text-xs">{u.nickname?.[0]}</AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="text-sm font-medium">{u.nickname}</p>
                                  <p className="text-[10px] text-gray-500">{u.production_house_name} • Lv.{u.level || 0}</p>
                                </div>
                              </div>
                              <Button size="sm" variant="outline" className="border-purple-500/30 text-purple-400 h-8" onClick={() => inviteUser(u.id)}>
                                <Send className="w-3 h-3 mr-1" /> {t('invite')}
                              </Button>
                            </div>
                          ))}
                        {allUsers.filter(u => !majorData.members?.some(m => m.user_id === u.id)).filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase())).length === 0 && (
                          <p className="text-sm text-gray-500 text-center py-4">
                            {language === 'it' ? 'Nessun utente trovato' : 'No users found'}
                          </p>
                        )}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                  
                  <TabsContent value="online">
                    <ScrollArea className="h-60 mt-2">
                      <div className="space-y-1">
                        {allUsers
                          .filter(u => u.is_online && !majorData.members?.some(m => m.user_id === u.id))
                          .filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase()))
                          .map(u => (
                            <div key={u.id} className="flex items-center justify-between p-2 rounded bg-white/5 hover:bg-white/10 transition-colors">
                              <div className="flex items-center gap-3">
                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={u.avatar_url} />
                                  <AvatarFallback className="bg-green-500/20 text-green-400 text-xs">{u.nickname?.[0]}</AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="text-sm font-medium">{u.nickname}</p>
                                  <p className="text-[10px] text-gray-500">{u.production_house_name} • Lv.{u.level || 0}</p>
                                </div>
                              </div>
                              <Button size="sm" variant="outline" className="border-purple-500/30 text-purple-400 h-8" onClick={() => inviteUser(u.id)}>
                                <Send className="w-3 h-3 mr-1" /> {t('invite')}
                              </Button>
                            </div>
                          ))}
                        {allUsers.filter(u => u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length === 0 && (
                          <p className="text-sm text-gray-500 text-center py-4">
                            {language === 'it' ? 'Nessun utente online' : 'No users online'}
                          </p>
                        )}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                  
                  <TabsContent value="offline">
                    <ScrollArea className="h-60 mt-2">
                      <div className="space-y-1">
                        {allUsers
                          .filter(u => !u.is_online && !majorData.members?.some(m => m.user_id === u.id))
                          .filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase()))
                          .map(u => (
                            <div key={u.id} className="flex items-center justify-between p-2 rounded bg-white/5 hover:bg-white/10 transition-colors">
                              <div className="flex items-center gap-3">
                                <span className="w-2 h-2 rounded-full bg-gray-500"></span>
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={u.avatar_url} />
                                  <AvatarFallback className="bg-gray-500/20 text-gray-400 text-xs">{u.nickname?.[0]}</AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="text-sm font-medium">{u.nickname}</p>
                                  <p className="text-[10px] text-gray-500">{u.production_house_name} • Lv.{u.level || 0}</p>
                                </div>
                              </div>
                              <Button size="sm" variant="outline" className="border-purple-500/30 text-purple-400 h-8" onClick={() => inviteUser(u.id)}>
                                <Send className="w-3 h-3 mr-1" /> {t('invite')}
                              </Button>
                            </div>
                          ))}
                        {allUsers.filter(u => !u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length === 0 && (
                          <p className="text-sm text-gray-500 text-center py-4">
                            {language === 'it' ? 'Nessun utente offline' : 'No users offline'}
                          </p>
                        )}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
        </div>
      )}
      
      {/* Create Major Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="bg-[#1A1A1A] border-white/10">
          <DialogHeader>
            <DialogTitle>{t('createMajor')}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{language === 'it' ? 'Nome' : 'Name'}</Label>
              <Input value={createForm.name} onChange={e => setCreateForm({...createForm, name: e.target.value})} placeholder="Major Studios" className="bg-black/30 border-white/10" />
            </div>
            <div>
              <Label>{language === 'it' ? 'Descrizione' : 'Description'}</Label>
              <Input value={createForm.description} onChange={e => setCreateForm({...createForm, description: e.target.value})} placeholder={language === 'it' ? 'La nostra missione...' : 'Our mission...'} className="bg-black/30 border-white/10" />
            </div>
            <div>
              <Label>{language === 'it' ? 'Max Membri' : 'Max Members'} ({createForm.max_members})</Label>
              <Slider value={[createForm.max_members]} onValueChange={([v]) => setCreateForm({...createForm, max_members: v})} min={5} max={50} step={5} />
            </div>
            <div>
              <Label className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                {language === 'it' ? 'Logo AI (opzionale)' : 'AI Logo (optional)'}
              </Label>
              <Input 
                value={createForm.logo_prompt} 
                onChange={e => setCreateForm({...createForm, logo_prompt: e.target.value})} 
                placeholder={language === 'it' ? 'Es: Leone dorato, stile classico Hollywood...' : 'E.g: Golden lion, classic Hollywood style...'} 
                className="bg-black/30 border-white/10" 
              />
              <p className="text-xs text-gray-500 mt-1">
                {language === 'it' 
                  ? 'Descrivi lo stile del logo che vuoi generare con AI' 
                  : 'Describe the logo style you want to generate with AI'}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
              <p className="text-sm text-purple-400 text-center">
                <DollarSign className="w-4 h-4 inline mr-1" />
                {language === 'it' ? 'Costo creazione: ' : 'Creation cost: '}
                <span className="font-bold">${(majorData?.creation_cost || 5000000).toLocaleString()}</span>
              </p>
            </div>
            <Button 
              className="w-full bg-purple-600 hover:bg-purple-500" 
              onClick={createMajor}
              disabled={creating || !createForm.name.trim()}
            >
              {creating ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> {language === 'it' ? 'Creazione in corso...' : 'Creating...'}</>
              ) : (
                t('createMajor')
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ==================== FRIENDS PAGE ====================
const FriendsPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('friends');
  const [friends, setFriends] = useState([]);
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [requests, setRequests] = useState({ incoming: [], outgoing: [] });
  const [loading, setLoading] = useState(true);
  const [allUsers, setAllUsers] = useState([]);
  
  const t = (key) => {
    const translations = {
      friends: language === 'it' ? 'Amici' : 'Friends',
      followers: language === 'it' ? 'Follower' : 'Followers',
      following: language === 'it' ? 'Seguiti' : 'Following',
      requests: language === 'it' ? 'Richieste' : 'Requests',
      addFriend: language === 'it' ? 'Aggiungi Amico' : 'Add Friend',
      accept: language === 'it' ? 'Accetta' : 'Accept',
      reject: language === 'it' ? 'Rifiuta' : 'Reject',
      follow: language === 'it' ? 'Segui' : 'Follow',
      unfollow: language === 'it' ? 'Non Seguire' : 'Unfollow',
      removeFriend: language === 'it' ? 'Rimuovi' : 'Remove',
      pending: language === 'it' ? 'In attesa' : 'Pending'
    };
    return translations[key] || key;
  };
  
  useEffect(() => {
    loadData();
  }, [api]);
  
  const loadData = async () => {
    setLoading(true);
    try {
      const [friendsRes, followersRes, followingRes, requestsRes, usersRes] = await Promise.all([
        api.get('/friends'),
        api.get('/followers'),
        api.get('/following'),
        api.get('/friends/requests'),
        api.get('/users/online')
      ]);
      setFriends(friendsRes.data.friends);
      setFollowers(followersRes.data.followers);
      setFollowing(followingRes.data.following);
      setRequests(requestsRes.data);
      setAllUsers(usersRes.data || []);
    } catch (e) {}
    setLoading(false);
  };
  
  const sendFriendRequest = async (userId) => {
    try {
      await api.post('/friends/request', { user_id: userId });
      toast.success(language === 'it' ? 'Richiesta inviata!' : 'Request sent!');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
  };
  
  const acceptRequest = async (requestId) => {
    try {
      await api.post(`/friends/request/${requestId}/accept`);
      toast.success(language === 'it' ? 'Amicizia accettata!' : 'Friendship accepted!');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
  };
  
  const rejectRequest = async (requestId) => {
    try {
      await api.post(`/friends/request/${requestId}/reject`);
      loadData();
    } catch (e) {}
  };
  
  const followUser = async (userId) => {
    try {
      await api.post(`/follow/${userId}`);
      toast.success(language === 'it' ? 'Ora segui questo utente!' : 'Now following!');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
  };
  
  const unfollowUser = async (userId) => {
    try {
      await api.delete(`/follow/${userId}`);
      loadData();
    } catch (e) {}
  };
  
  const removeFriend = async (friendId) => {
    try {
      await api.delete(`/friends/${friendId}`);
      loadData();
    } catch (e) {}
  };
  
  if (loading) return <div className="pt-16 p-4 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;
  
  return (
    <div className="pt-16 pb-6 px-3 max-w-2xl mx-auto">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4 flex items-center gap-2">
        <Users className="w-8 h-8 text-blue-500" />
        {t('friends')} & {t('followers')}
      </h1>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-4 mb-4">
          <TabsTrigger value="friends" className="text-xs">
            {t('friends')} ({friends.length})
          </TabsTrigger>
          <TabsTrigger value="followers" className="text-xs">
            {t('followers')} ({followers.length})
          </TabsTrigger>
          <TabsTrigger value="following" className="text-xs">
            {t('following')} ({following.length})
          </TabsTrigger>
          <TabsTrigger value="requests" className="text-xs relative">
            {t('requests')}
            {requests.incoming?.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-[10px] rounded-full flex items-center justify-center">{requests.incoming.length}</span>
            )}
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="friends">
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardContent className="p-4">
              {friends.length === 0 ? (
                <p className="text-center text-gray-400 py-8">{language === 'it' ? 'Nessun amico' : 'No friends yet'}</p>
              ) : (
                <div className="space-y-2">
                  {friends.map(friend => (
                    <div key={friend.id} className="flex items-center gap-3 p-2 rounded bg-white/5 cursor-pointer" onClick={() => navigate(`/player/${friend.id}`)}>
                      <Avatar className="w-10 h-10">
                        <AvatarImage src={friend.avatar_url} />
                        <AvatarFallback className="bg-blue-500/20 text-blue-500">{friend.nickname?.[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{friend.nickname}</p>
                        <p className="text-xs text-gray-400">{friend.production_house_name}</p>
                      </div>
                      {friend.is_online && <span className="w-2 h-2 bg-green-500 rounded-full"></span>}
                      <Button size="sm" variant="ghost" className="h-8 text-red-400" onClick={(e) => { e.stopPropagation(); removeFriend(friend.id); }}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="followers">
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardContent className="p-4">
              {followers.length === 0 ? (
                <p className="text-center text-gray-400 py-8">{language === 'it' ? 'Nessun follower' : 'No followers yet'}</p>
              ) : (
                <div className="space-y-2">
                  {followers.map(follower => (
                    <div key={follower.id} className="flex items-center gap-3 p-2 rounded bg-white/5 cursor-pointer" onClick={() => navigate(`/player/${follower.id}`)}>
                      <Avatar className="w-10 h-10">
                        <AvatarImage src={follower.avatar_url} />
                        <AvatarFallback className="bg-pink-500/20 text-pink-500">{follower.nickname?.[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{follower.nickname}</p>
                        <p className="text-xs text-gray-400">{follower.production_house_name}</p>
                      </div>
                      {!following.some(f => f.id === follower.id) && (
                        <Button size="sm" variant="outline" className="h-8 border-blue-500/30 text-blue-400" onClick={(e) => { e.stopPropagation(); followUser(follower.id); }}>
                          {t('follow')}
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="following">
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardContent className="p-4">
              {following.length === 0 ? (
                <p className="text-center text-gray-400 py-8">{language === 'it' ? 'Non segui nessuno' : 'Not following anyone'}</p>
              ) : (
                <div className="space-y-2">
                  {following.map(user => (
                    <div key={user.id} className="flex items-center gap-3 p-2 rounded bg-white/5 cursor-pointer" onClick={() => navigate(`/player/${user.id}`)}>
                      <Avatar className="w-10 h-10">
                        <AvatarImage src={user.avatar_url} />
                        <AvatarFallback className="bg-blue-500/20 text-blue-500">{user.nickname?.[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{user.nickname}</p>
                        <p className="text-xs text-gray-400">{user.production_house_name}</p>
                      </div>
                      <Button size="sm" variant="ghost" className="h-8 text-gray-400" onClick={(e) => { e.stopPropagation(); unfollowUser(user.id); }}>
                        {t('unfollow')}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="requests">
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardContent className="p-4">
              <h3 className="font-semibold mb-3">{language === 'it' ? 'Richieste Ricevute' : 'Incoming Requests'}</h3>
              {requests.incoming?.length === 0 ? (
                <p className="text-center text-gray-400 py-4">{language === 'it' ? 'Nessuna richiesta' : 'No requests'}</p>
              ) : (
                <div className="space-y-2 mb-6">
                  {requests.incoming.map(req => (
                    <div key={req.request.id} className="flex items-center gap-3 p-2 rounded bg-white/5">
                      <Avatar className="w-10 h-10">
                        <AvatarImage src={req.user?.avatar_url} />
                        <AvatarFallback className="bg-blue-500/20 text-blue-500">{req.user?.nickname?.[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{req.user?.nickname}</p>
                      </div>
                      <Button size="sm" className="h-8 bg-green-600" onClick={() => acceptRequest(req.request.id)}>
                        <Check className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="ghost" className="h-8 text-red-400" onClick={() => rejectRequest(req.request.id)}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              
              <h3 className="font-semibold mb-3">{language === 'it' ? 'Richieste Inviate' : 'Sent Requests'}</h3>
              {requests.outgoing?.length === 0 ? (
                <p className="text-center text-gray-400 py-4">{language === 'it' ? 'Nessuna richiesta inviata' : 'No sent requests'}</p>
              ) : (
                <div className="space-y-2">
                  {requests.outgoing.map(req => (
                    <div key={req.request.id} className="flex items-center gap-3 p-2 rounded bg-white/5">
                      <Avatar className="w-10 h-10">
                        <AvatarImage src={req.user?.avatar_url} />
                        <AvatarFallback className="bg-gray-500/20">{req.user?.nickname?.[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{req.user?.nickname}</p>
                      </div>
                      <Badge className="bg-yellow-500/20 text-yellow-400">{t('pending')}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// ==================== DOWNLOAD APP PAGE ====================
const DownloadAppPage = () => {
  const { language } = useContext(LanguageContext);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isAndroid, setIsAndroid] = useState(false);
  
  useEffect(() => {
    // Detect platform
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    setIsIOS(/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream);
    setIsAndroid(/android/i.test(userAgent));
    
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
    }
    
    // Listen for install prompt (Android/Desktop)
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    });
    
    // Listen for successful install
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setDeferredPrompt(null);
    });
  }, []);
  
  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setIsInstalled(true);
    }
    setDeferredPrompt(null);
  };
  
  const appUrl = window.location.origin;
  
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-4 pt-20">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <img src="/icons/icon-192x192.png" alt="CineWorld" className="w-24 h-24 mx-auto rounded-2xl shadow-lg mb-4" />
          <h1 className="text-3xl font-['Bebas_Neue'] text-yellow-500">CineWorld Studio's</h1>
          <Badge className="bg-purple-500/20 text-purple-400 mt-2">BETA TEST</Badge>
          <p className="text-gray-400 mt-2">
            {language === 'it' 
              ? 'Gioco multiplayer di produzione cinematografica'
              : 'Multiplayer movie production game'}
          </p>
        </div>
        
        {isInstalled ? (
          <Card className="bg-green-500/10 border-green-500/30 mb-6">
            <CardContent className="p-6 text-center">
              <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
              <h2 className="text-xl font-semibold text-green-400">
                {language === 'it' ? 'App Installata!' : 'App Installed!'}
              </h2>
              <p className="text-gray-400 mt-2">
                {language === 'it' 
                  ? 'Puoi trovare CineWorld nella tua home screen.'
                  : 'You can find CineWorld on your home screen.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Android / Desktop Install */}
            {(isAndroid || deferredPrompt) && (
              <Card className="bg-[#1A1A1A] border-green-500/30 mb-6">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Smartphone className="w-8 h-8 text-green-500" />
                    <div>
                      <h2 className="font-semibold">
                        {isAndroid ? 'Android' : 'Desktop'}
                      </h2>
                      <p className="text-xs text-gray-400">
                        {language === 'it' ? 'Installazione diretta' : 'Direct installation'}
                      </p>
                    </div>
                  </div>
                  <Button 
                    onClick={handleInstall}
                    className="w-full bg-green-600 hover:bg-green-500"
                    disabled={!deferredPrompt}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    {language === 'it' ? 'Installa App' : 'Install App'}
                  </Button>
                </CardContent>
              </Card>
            )}
            
            {/* iOS Instructions */}
            {isIOS && (
              <Card className="bg-[#1A1A1A] border-blue-500/30 mb-6">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Smartphone className="w-8 h-8 text-blue-500" />
                    <div>
                      <h2 className="font-semibold">iPhone / iPad</h2>
                      <p className="text-xs text-gray-400">
                        {language === 'it' ? 'Installazione manuale' : 'Manual installation'}
                      </p>
                    </div>
                  </div>
                  <div className="space-y-4 text-sm">
                    <div className="flex items-start gap-3 p-3 rounded bg-black/30">
                      <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold shrink-0">1</span>
                      <div>
                        <p className="font-medium">{language === 'it' ? 'Apri Safari' : 'Open Safari'}</p>
                        <p className="text-gray-400 text-xs">
                          {language === 'it' ? 'Deve essere Safari, non Chrome o altri browser' : 'Must be Safari, not Chrome or other browsers'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded bg-black/30">
                      <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold shrink-0">2</span>
                      <div>
                        <p className="font-medium">{language === 'it' ? 'Tocca l\'icona Condividi' : 'Tap the Share icon'}</p>
                        <p className="text-gray-400 text-xs">
                          {language === 'it' ? 'Il quadrato con la freccia in basso' : 'The square with arrow at bottom'}
                        </p>
                        <Share2 className="w-6 h-6 mt-1 text-blue-400" />
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded bg-black/30">
                      <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold shrink-0">3</span>
                      <div>
                        <p className="font-medium">{language === 'it' ? 'Seleziona "Aggiungi a Home"' : 'Select "Add to Home Screen"'}</p>
                        <p className="text-gray-400 text-xs">
                          {language === 'it' ? 'Scorri le opzioni e tocca questa voce' : 'Scroll the options and tap this item'}
                        </p>
                        <Plus className="w-6 h-6 mt-1 text-blue-400" />
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded bg-black/30">
                      <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold shrink-0">4</span>
                      <div>
                        <p className="font-medium">{language === 'it' ? 'Conferma "Aggiungi"' : 'Confirm "Add"'}</p>
                        <p className="text-gray-400 text-xs">
                          {language === 'it' ? 'L\'app apparirà sulla tua home screen' : 'The app will appear on your home screen'}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Generic Instructions for other browsers */}
            {!isIOS && !isAndroid && !deferredPrompt && (
              <Card className="bg-[#1A1A1A] border-yellow-500/30 mb-6">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Globe className="w-8 h-8 text-yellow-500" />
                    <div>
                      <h2 className="font-semibold">{language === 'it' ? 'Browser Desktop' : 'Desktop Browser'}</h2>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-4">
                    {language === 'it' 
                      ? 'Cerca l\'icona di installazione nella barra degli indirizzi del browser, oppure usa il menu per "Installa app".'
                      : 'Look for the install icon in the browser address bar, or use the menu to "Install app".'}
                  </p>
                </CardContent>
              </Card>
            )}
          </>
        )}
        
        {/* Share Link */}
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Link2 className="w-5 h-5 text-yellow-500" />
              {language === 'it' ? 'Condividi con amici' : 'Share with friends'}
            </h3>
            <div className="flex gap-2">
              <Input 
                value={appUrl} 
                readOnly 
                className="bg-black/30 border-white/10 text-sm"
              />
              <Button 
                variant="outline" 
                className="border-yellow-500/30 text-yellow-400 shrink-0"
                onClick={() => {
                  navigator.clipboard.writeText(appUrl);
                  toast.success(language === 'it' ? 'Link copiato!' : 'Link copied!');
                }}
              >
                <Copy className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {language === 'it' 
                ? 'Invia questo link ai tuoi amici per farli giocare!'
                : 'Send this link to your friends to let them play!'}
            </p>
          </CardContent>
        </Card>
        
        {/* QR Code placeholder */}
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6 text-center">
            <h3 className="font-semibold mb-3">{language === 'it' ? 'Scansiona QR Code' : 'Scan QR Code'}</h3>
            <div className="w-40 h-40 mx-auto bg-white p-2 rounded-lg">
              {/* Simple QR-like pattern */}
              <div className="w-full h-full bg-black rounded flex items-center justify-center text-white text-xs">
                <QrCode className="w-20 h-20" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              {language === 'it' 
                ? 'Scansiona con la fotocamera del telefono'
                : 'Scan with your phone camera'}
            </p>
          </CardContent>
        </Card>
        
        {/* Beta Notice */}
        <div className="text-center text-xs text-gray-500 mt-8 pb-8">
          <p>CineWorld Studio's - Beta Test v1.0</p>
          <p className="mt-1">
            {language === 'it' 
              ? 'L\'app si aggiorna automaticamente. Nessun download dagli store richiesto.'
              : 'The app updates automatically. No store download required.'}
          </p>
        </div>
      </div>
    </div>
  );
};

// ==================== NOTIFICATIONS PAGE ====================
const NotificationsPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const t = (key) => ({
    notifications: language === 'it' ? 'Notifiche' : 'Notifications',
    markAllRead: language === 'it' ? 'Segna tutto letto' : 'Mark all read',
    noNotifications: language === 'it' ? 'Nessuna notifica' : 'No notifications'
  }[key] || key);
  
  useEffect(() => {
    loadNotifications();
  }, [api]);
  
  const loadNotifications = async () => {
    try {
      const res = await api.get('/notifications?limit=50');
      setNotifications(res.data.notifications);
    } catch (e) {}
    setLoading(false);
  };
  
  const markAllRead = async () => {
    try {
      await api.post('/notifications/read', { notification_ids: [] });
      loadNotifications();
    } catch (e) {}
  };
  
  const markAsRead = async (id) => {
    try {
      await api.post('/notifications/read', { notification_ids: [id] });
      loadNotifications();
    } catch (e) {}
  };
  
  const deleteNotification = async (id) => {
    try {
      await api.delete(`/notifications/${id}`);
      loadNotifications();
    } catch (e) {}
  };
  
  const getIconForType = (type) => {
    const icons = {
      friend_request: <UserPlus className="w-5 h-5 text-blue-400" />,
      friend_accepted: <UserCheck className="w-5 h-5 text-green-400" />,
      major_invite: <Crown className="w-5 h-5 text-purple-400" />,
      major_joined: <Users className="w-5 h-5 text-purple-400" />,
      new_film: <Film className="w-5 h-5 text-yellow-400" />,
      new_follower: <UserPlus className="w-5 h-5 text-pink-400" />,
      message: <MessageSquare className="w-5 h-5 text-blue-400" />,
      festival: <Award className="w-5 h-5 text-yellow-400" />,
      festival_countdown: <Clock className="w-5 h-5 text-orange-400" />,
      award_won: <Trophy className="w-5 h-5 text-yellow-400" />,
      achievement: <Star className="w-5 h-5 text-yellow-400" />,
      major_challenge: <Target className="w-5 h-5 text-red-400" />,
      level_up: <TrendingUp className="w-5 h-5 text-green-400" />,
      system: <Info className="w-5 h-5 text-gray-400" />
    };
    return icons[type] || icons.system;
  };
  
  if (loading) return <div className="pt-16 p-4 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;
  
  return (
    <div className="pt-16 pb-6 px-3 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
          <Bell className="w-8 h-8 text-yellow-500" />
          {t('notifications')}
        </h1>
        {notifications.some(n => !n.read) && (
          <Button size="sm" variant="outline" onClick={markAllRead}>
            <Check className="w-4 h-4 mr-1" /> {t('markAllRead')}
          </Button>
        )}
      </div>
      
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-4">
          {notifications.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="w-12 h-12 mx-auto text-gray-500/50 mb-3" />
              <p className="text-gray-400">{t('noNotifications')}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {notifications.map(notif => (
                <div 
                  key={notif.id} 
                  className={`flex items-start gap-3 p-3 rounded cursor-pointer transition-colors ${notif.read ? 'bg-white/5' : 'bg-yellow-500/10 border border-yellow-500/20'}`}
                  onClick={() => { 
                    if (!notif.read) markAsRead(notif.id);
                    if (notif.link) navigate(notif.link);
                  }}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {getIconForType(notif.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm">{notif.title}</p>
                    <p className="text-xs text-gray-400">{notif.message}</p>
                    <p className="text-[10px] text-gray-500 mt-1">
                      {new Date(notif.created_at).toLocaleDateString(language === 'it' ? 'it-IT' : 'en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-gray-400" onClick={(e) => { e.stopPropagation(); deleteNotification(notif.id); }}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center"><Clapperboard className="w-10 h-10 text-yellow-500 animate-pulse" /></div>;
  if (!user) return <Navigate to="/auth" replace />;
  return <><TopNavbar />{children}</>;
};

// Main App
// URL Manager - Saves current URL and shows redirect message if needed
const UrlManager = ({ children }) => {
  const [showUrlChanged, setShowUrlChanged] = useState(false);
  const [newUrl, setNewUrl] = useState('');

  useEffect(() => {
    const currentUrl = window.location.origin;
    
    // Save current URL to backend
    axios.post(`${API}/game-url`, { url: currentUrl }).catch(() => {});
    
    // Check if there's a saved URL in localStorage that differs
    const savedUrl = localStorage.getItem('cineworld_last_url');
    if (savedUrl && savedUrl !== currentUrl) {
      // URL has changed - show notification
      setNewUrl(currentUrl);
      setShowUrlChanged(true);
    }
    
    // Always save the current URL
    localStorage.setItem('cineworld_last_url', currentUrl);
  }, []);

  return (
    <>
      {showUrlChanged && (
        <div className="fixed top-0 left-0 right-0 bg-gradient-to-r from-yellow-500 to-amber-500 text-black py-2 px-4 z-[100] flex items-center justify-center gap-3 text-sm">
          <Bell className="w-4 h-4" />
          <span className="font-medium">Il gioco si è spostato! Salva questo nuovo link:</span>
          <code className="bg-black/20 px-2 py-0.5 rounded text-xs">{newUrl}</code>
          <Button 
            size="sm" 
            variant="secondary"
            className="h-6 text-xs"
            onClick={() => {
              navigator.clipboard.writeText(newUrl);
              toast.success('Link copiato!');
            }}
          >
            <Copy className="w-3 h-3 mr-1" /> Copia
          </Button>
          <button 
            onClick={() => setShowUrlChanged(false)}
            className="ml-2 hover:bg-black/20 rounded p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {children}
    </>
  );
};

function App() {
  return (
    <div className="min-h-screen bg-[#0F0F10]">
      <BrowserRouter>
        <AuthProvider>
          <LanguageProvider>
            <UrlManager>
              <Toaster position="top-center" theme="dark" />
              <Routes>
                <Route path="/auth" element={<AuthPage />} />
                <Route path="/recovery/password" element={<PasswordRecoveryPage />} />
                <Route path="/recovery/nickname" element={<NicknameRecoveryPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/films" element={<ProtectedRoute><MyFilms /></ProtectedRoute>} />
                <Route path="/films/:id" element={<ProtectedRoute><FilmDetail /></ProtectedRoute>} />
                <Route path="/create" element={<ProtectedRoute><FilmWizard /></ProtectedRoute>} />
                <Route path="/drafts" element={<ProtectedRoute><FilmDrafts /></ProtectedRoute>} />
                <Route path="/pre-engagement" element={<ProtectedRoute><PreEngagementPage /></ProtectedRoute>} />
                <Route path="/journal" element={<ProtectedRoute><CinemaJournal /></ProtectedRoute>} />
                <Route path="/stars" element={<ProtectedRoute><DiscoveredStars /></ProtectedRoute>} />
                <Route path="/releases" element={<ProtectedRoute><ReleaseNotes /></ProtectedRoute>} />
                <Route path="/feedback" element={<ProtectedRoute><FeedbackBoard /></ProtectedRoute>} />
                <Route path="/social" element={<ProtectedRoute><CineBoard /></ProtectedRoute>} />
                <Route path="/games" element={<ProtectedRoute><MiniGamesPage /></ProtectedRoute>} />
                <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
                <Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
                <Route path="/infrastructure" element={<ProtectedRoute><InfrastructurePage /></ProtectedRoute>} />
                <Route path="/marketplace" element={<ProtectedRoute><MarketplacePage /></ProtectedRoute>} />
                <Route path="/tour" element={<ProtectedRoute><CinemaTourPage /></ProtectedRoute>} />
                <Route path="/leaderboard" element={<ProtectedRoute><LeaderboardPage /></ProtectedRoute>} />
                <Route path="/tutorial" element={<ProtectedRoute><TutorialPage /></ProtectedRoute>} />
                <Route path="/sagas" element={<ProtectedRoute><SagasSeriesPage /></ProtectedRoute>} />
                <Route path="/festivals" element={<ProtectedRoute><FestivalsPage /></ProtectedRoute>} />
                <Route path="/credits" element={<ProtectedRoute><CreditsPage /></ProtectedRoute>} />
                <Route path="/player/:id" element={<ProtectedRoute><PlayerPublicProfile /></ProtectedRoute>} />
                <Route path="/major" element={<ProtectedRoute><MajorPage /></ProtectedRoute>} />
                <Route path="/friends" element={<ProtectedRoute><FriendsPage /></ProtectedRoute>} />
                <Route path="/notifications" element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />
                <Route path="/download" element={<DownloadAppPage />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </UrlManager>
          </LanguageProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
