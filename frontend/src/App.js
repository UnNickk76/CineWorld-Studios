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
  KeyRound, AlertCircle, Mail, Tv, Swords, Shield, Flame, History, ArrowUpCircle
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
import './App.css';

// Import from refactored modules
import { AuthContext, LanguageContext, AuthProvider, LanguageProvider, useTranslations, API, PlayerPopupContext, usePlayerPopup } from './contexts';
import { SKILL_TRANSLATIONS } from './constants';
import { PageTransition, PageSkeleton } from './components/PageTransition';

// Lazy-load pages from separate files for code-splitting
const ReleaseNotes = React.lazy(() => import('./pages/ReleaseNotes'));
const TutorialPage = React.lazy(() => import('./pages/TutorialPage'));
const CreditsPage = React.lazy(() => import('./pages/CreditsPage'));

// Extracted pages (lazy-loaded)
const AuthPage = React.lazy(() => import('./pages/AuthPage'));
const ChallengesPage = React.lazy(() => import('./pages/ChallengesPage'));
const ChatPage = React.lazy(() => import('./pages/ChatPage'));
const CineBoard = React.lazy(() => import('./pages/CineBoard'));
const CinemaJournal = React.lazy(() => import('./pages/CinemaJournal'));
const CinemaTourPage = React.lazy(() => import('./pages/CinemaTourPage'));
const CreatorBoard = React.lazy(() => import('./pages/CreatorBoard'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const DiscoveredStars = React.lazy(() => import('./pages/DiscoveredStars'));
const DownloadAppPage = React.lazy(() => import('./pages/DownloadAppPage'));
const FeedbackBoard = React.lazy(() => import('./pages/FeedbackBoard'));
const FestivalsPage = React.lazy(() => import('./pages/FestivalsPage'));
const FilmDetail = React.lazy(() => import('./pages/FilmDetail'));
const FilmDrafts = React.lazy(() => import('./pages/FilmDrafts'));
const FilmWizard = React.lazy(() => import('./pages/FilmWizard'));
const FriendsPage = React.lazy(() => import('./pages/FriendsPage'));
const InfrastructurePage = React.lazy(() => import('./pages/InfrastructurePage'));
const LeaderboardPage = React.lazy(() => import('./pages/LeaderboardPage'));
const MajorPage = React.lazy(() => import('./pages/MajorPage'));
const MarketplacePage = React.lazy(() => import('./pages/MarketplacePage'));
const MiniGamesPage = React.lazy(() => import('./pages/MiniGamesPage'));
const MyFilms = React.lazy(() => import('./pages/MyFilms'));
const NotificationsPage = React.lazy(() => import('./pages/NotificationsPage'));
const PreEngagementPage = React.lazy(() => import('./pages/PreEngagementPage'));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage'));
const ResetPasswordPage = React.lazy(() => import('./pages/ResetPasswordPage'));
const SagasSeriesPage = React.lazy(() => import('./pages/SagasSeriesPage'));
const PasswordRecoveryPage = React.lazy(() => import('./pages/PasswordRecoveryPage'));
const NicknameRecoveryPage = React.lazy(() => import('./pages/NicknameRecoveryPage'));
const StatisticsPage = React.lazy(() => import('./pages/StatisticsPage'));
const PlayerPublicProfile = React.lazy(() => import('./pages/PlayerPublicProfile'));

// ==================== COMPONENTS ====================

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
  const [showOnlineUsersPanel, setShowOnlineUsersPanel] = useState(false);
  const [onlineUsersCount, setOnlineUsersCount] = useState(0);
  const [onlineUsersList, setOnlineUsersList] = useState([]);
  const [allPlayersList, setAllPlayersList] = useState([]);
  const [selectedOnlineUser, setSelectedOnlineUser] = useState(null);
  const [selectedUserProfile, setSelectedUserProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [sendingFriendReq, setSendingFriendReq] = useState(null);
  const [friendshipStatus, setFriendshipStatus] = useState(null);
  const [globalPlayerPopup, setGlobalPlayerPopup] = useState(null); // unused, kept for compat
  const { openPlayerPopup: _ctxOpen, popupData, setPopupData } = usePlayerPopup();
  const [userTimezone, setUserTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Rome');

  // Core data - fetch once on mount + poll
  useEffect(() => {
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {});
    api.get('/notifications/count').then(r => setNotificationCount(r.data.unread_count)).catch(() => {});
    api.get('/release-notes/unread-count').then(r => setReleaseNotesCount(r.data.unread_count)).catch(() => {});
    api.get('/major/my').then(r => setMajorInfo(r.data)).catch(() => {});
    
    // Online users + all players polling
    const fetchOnlineUsers = () => {
      api.get('/users/online').then(r => {
        const users = r.data.filter(u => !u.is_bot);
        setOnlineUsersList(r.data);
        setOnlineUsersCount(users.length);
      }).catch(() => {});
      api.get('/users/all-players').then(r => {
        setAllPlayersList(r.data);
      }).catch(() => {});
    };
    fetchOnlineUsers();
    const onlineInterval = setInterval(fetchOnlineUsers, 60000);
    
    // Festival notifications polling
    const fetchFestivalNotifications = () => {
      api.get(`/festivals/notifications?timezone=${userTimezone}&language=${language}`)
        .then(r => {
          const notifs = r.data.notifications || [];
          setFestivalNotifications(notifs);
          notifs.filter(n => n.type === 'starting').forEach(n => {
            toast.info(n.message, { duration: 10000 });
          });
        }).catch(() => {});
    };
    
    fetchFestivalNotifications();
    const festivalInterval = setInterval(fetchFestivalNotifications, 60000);
    
    return () => { clearInterval(festivalInterval); clearInterval(onlineInterval); };
  }, [api, userTimezone, language]);

  // Lightweight refresh on navigation - only notification counts
  useEffect(() => {
    api.get('/notifications/count').then(r => setNotificationCount(r.data.unread_count)).catch(() => {});
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {});
  }, [location.pathname]);


  const viewUserProfile = async (userId) => {
    setLoadingProfile(true);
    setSelectedOnlineUser(userId);
    setFriendshipStatus(null);
    try {
      const [profileRes, friendRes] = await Promise.all([
        api.get(`/users/${userId}/full-profile`),
        api.get(`/friends/status/${userId}`)
      ]);
      setSelectedUserProfile(profileRes.data);
      setFriendshipStatus(friendRes.data);
    } catch(e) {
      toast.error(language === 'it' ? 'Errore caricamento profilo' : 'Profile load error');
    } finally {
      setLoadingProfile(false);
    }
  };

  // Global popup - opens from any nickname click (managed by ProtectedRoute context)
  const { openPlayerPopup } = usePlayerPopup();

  const sendFriendRequest = async (friendId) => {
    setSendingFriendReq(friendId);
    try {
      await api.post('/friends/request', { user_id: friendId });
      toast.success(language === 'it' ? 'Richiesta di amicizia inviata!' : 'Friend request sent!');
      setFriendshipStatus({ status: 'pending_sent' });
    } catch(e) {
      const detail = e.response?.data?.detail || '';
      if (detail.includes('already') || detail.includes('già')) {
        toast.info(language === 'it' ? 'Richiesta già inviata' : 'Request already sent');
      } else {
        toast.error(detail || (language === 'it' ? 'Errore invio richiesta' : 'Request failed'));
      }
    } finally {
      setSendingFriendReq(null);
    }
  };

  const removeFriend = async (friendId) => {
    setSendingFriendReq(friendId);
    try {
      await api.delete(`/friends/${friendId}`);
      toast.success(language === 'it' ? 'Amico rimosso' : 'Friend removed');
      setFriendshipStatus({ status: 'none' });
    } catch(e) {
      toast.error(e.response?.data?.detail || (language === 'it' ? 'Errore rimozione' : 'Remove failed'));
    } finally {
      setSendingFriendReq(null);
    }
  };

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
  const canGoBack = location.pathname !== '/dashboard';

  return (
    <nav className="fixed top-0 left-0 right-0 h-14 bg-[#0F0F10] border-b border-white/10 z-50">
      <div className="max-w-7xl mx-auto h-full px-2 sm:px-3 flex items-center justify-between">
        {/* Left section: Logo */}
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
          {/* Back Button - Always visible on non-Dashboard pages */}
          {canGoBack && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="flex h-8 w-8 p-0 text-gray-400 hover:text-white"
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
          {/* Festival/TV Button - Only visible when a live festival is starting */}
          {festivalNotifications.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 text-yellow-400 animate-pulse`}
            onClick={() => navigate(`/festivals?live=${festivalNotifications[0].festival_id}`)}
            data-testid="festival-tv-btn"
            title={festivalNotifications[0].message || 'Festival Live'}
          >
            <Tv className="w-4 h-4" />
            {festivalNotifications[0].type === 'starting' && (
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full animate-ping"></span>
            )}
          </Button>
          )}
          
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
          
          {/* CineBoard/Social - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/social' ? 'text-green-400' : 'text-gray-400 hover:text-green-400'}`}
            onClick={() => navigate('/social')}
            data-testid="cineboard-btn"
            title="CineBoard"
          >
            <Globe className="w-4 h-4" />
          </Button>
          
          {/* Cinema Journal - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/journal' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => navigate('/journal')}
            data-testid="journal-nav-btn"
            title={language === 'it' ? 'Giornale del Cinema' : 'Cinema Journal'}
          >
            <Newspaper className="w-4 h-4" />
          </Button>
          
          {/* Challenges/Sfide - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/challenges' ? 'text-pink-400' : 'text-gray-400 hover:text-pink-400'}`}
            onClick={() => navigate('/challenges')}
            data-testid="challenges-nav-btn"
            title={language === 'it' ? 'Contest' : 'Contest'}
          >
            <Swords className="w-4 h-4" />
          </Button>
          
          {/* Chat - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/chat' ? 'text-cyan-400' : 'text-gray-400 hover:text-cyan-400'}`}
            onClick={() => navigate('/chat')}
            data-testid="chat-nav-btn"
            title="Chat"
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
          
          {/* Online Users - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${showOnlineUsersPanel ? 'text-green-400' : 'text-gray-400 hover:text-green-400'}`}
            onClick={() => setShowOnlineUsersPanel(true)}
            data-testid="online-users-btn"
            title={language === 'it' ? 'Utenti Online' : 'Online Users'}
          >
            <Users className="w-4 h-4" />
            {onlineUsersCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[12px] h-3 px-0.5 bg-green-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                {onlineUsersCount > 9 ? '9+' : onlineUsersCount}
              </span>
            )}
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
                {user?.nickname === 'NeoMorpheus' && (
                  <Button variant="ghost" size="sm" className="w-full justify-start gap-2 h-8 text-purple-400 hover:text-purple-300 hover:bg-purple-500/10" onClick={() => navigate('/creator-board')} data-testid="creator-board-btn">
                    <Mail className="w-3.5 h-3.5" /> Creator Board
                  </Button>
                )}
                <Button variant="ghost" size="sm" className="w-full justify-start gap-2 h-8 text-red-400 hover:text-red-300 hover:bg-red-500/10" onClick={logout} data-testid="logout-btn">
                  <LogOut className="w-3.5 h-3.5" /> {t('logout')}
                </Button>
              </div>
            </PopoverContent>
          </Popover>

          {/* HAMBURGER MENU - Visible on all screen sizes */}
          <Button 
            variant="ghost" 
            className="flex items-center justify-center p-1 h-8 w-8 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10" 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            data-testid="mobile-menu-btn"
          >
            {mobileMenuOpen ? <X className="w-5 h-5 text-white" /> : <Menu className="w-5 h-5 text-white" />}
          </Button>
        </div>
      </div>

      {/* Menu Dropdown - Visible on all screens */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute top-14 left-0 right-0 bg-[#0a0a0a] border-b border-white/10 shadow-2xl max-h-[80vh] overflow-y-auto"
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

      {/* Online Users Panel */}
      <Dialog open={showOnlineUsersPanel} onOpenChange={(open) => { setShowOnlineUsersPanel(open); if(!open) { setSelectedUserProfile(null); setSelectedOnlineUser(null); } }}>
        <DialogContent className="max-w-md max-h-[85vh] overflow-hidden bg-[#111] border-green-500/30 p-0">
          {/* If viewing a user's profile */}
          {selectedUserProfile ? (
            <div className="flex flex-col h-[80vh]">
              {/* Sticky header with back + friend request + challenge */}
              <div className="sticky top-0 z-10 bg-[#111] border-b border-white/10 p-3 flex items-center gap-2">
                <Button size="sm" variant="ghost" onClick={() => { setSelectedUserProfile(null); setSelectedOnlineUser(null); }} className="h-7 w-7 p-0 text-gray-400">
                  <ArrowLeft className="w-4 h-4" />
                </Button>
                <div className="flex-1">
                  <p className="font-bold text-sm">{selectedUserProfile.user?.nickname}</p>
                  <p className="text-[10px] text-gray-500">{selectedUserProfile.user?.production_house_name}</p>
                </div>
                {!selectedUserProfile.is_own_profile && (
                  <div className="flex gap-1.5">
                    {friendshipStatus?.status === 'friends' ? (
                      <Button 
                        size="sm"
                        variant="outline"
                        className="border-red-500/30 text-red-400 hover:bg-red-500/10 h-7 px-2 text-[10px]"
                        onClick={() => removeFriend(selectedUserProfile.user?.id)}
                        disabled={sendingFriendReq === selectedUserProfile.user?.id}
                        data-testid="profile-remove-friend-btn"
                      >
                        {sendingFriendReq === selectedUserProfile.user?.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <><UserCheck className="w-3 h-3 mr-1" />{language === 'it' ? 'Rimuovi' : 'Remove'}</>}
                      </Button>
                    ) : friendshipStatus?.status === 'pending_sent' ? (
                      <Button size="sm" variant="outline" className="border-gray-500/30 text-gray-400 h-7 px-2 text-[10px]" disabled>
                        <Clock className="w-3 h-3 mr-1" /> {language === 'it' ? 'In attesa' : 'Pending'}
                      </Button>
                    ) : (
                      <Button 
                        size="sm"
                        className="bg-cyan-500 hover:bg-cyan-600 text-black h-7 px-2 text-[10px] font-bold"
                        onClick={() => sendFriendRequest(selectedUserProfile.user?.id)}
                        disabled={sendingFriendReq === selectedUserProfile.user?.id}
                        data-testid="profile-add-friend-btn"
                      >
                        {sendingFriendReq === selectedUserProfile.user?.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <><UserPlus className="w-3 h-3 mr-1" />{language === 'it' ? 'Amicizia' : 'Add'}</>}
                      </Button>
                    )}
                    <Button 
                      size="sm"
                      className="bg-pink-500 hover:bg-pink-600 text-white h-7 px-2 text-[10px] font-bold"
                      onClick={() => { setShowOnlineUsersPanel(false); setSelectedUserProfile(null); navigate('/challenges'); }}
                      data-testid="profile-challenge-btn"
                    >
                      <Swords className="w-3 h-3 mr-1" /> 1v1
                    </Button>
                  </div>
                )}
              </div>
              
              {/* Profile content scrollable */}
              <ScrollArea className="flex-1">
                <div className="p-4 space-y-4">
                  {/* User avatar + level */}
                  <div className="flex items-center gap-4">
                    <Avatar className="w-16 h-16 ring-2 ring-green-500">
                      <AvatarImage src={selectedUserProfile.user?.avatar_url} />
                      <AvatarFallback className="bg-green-500/20 text-green-400 text-xl font-bold">{selectedUserProfile.user?.nickname?.[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-purple-500/20 text-purple-400">Lv.{selectedUserProfile.stats?.level || 1}</Badge>
                        {selectedUserProfile.is_online && <Badge className="bg-green-500/20 text-green-400 text-[9px]">ONLINE</Badge>}
                      </div>
                      <p className="text-gray-400 text-xs mt-1">{selectedUserProfile.user?.bio || ''}</p>
                    </div>
                  </div>
                  
                  {/* Stats grid */}
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: language === 'it' ? 'Film' : 'Films', value: selectedUserProfile.stats?.total_films || 0, color: 'text-blue-400' },
                      { label: language === 'it' ? 'Incassi' : 'Revenue', value: `$${((selectedUserProfile.stats?.total_revenue || 0)/1000000).toFixed(1)}M`, color: 'text-green-400' },
                      { label: language === 'it' ? 'Qualità Media' : 'Avg Quality', value: selectedUserProfile.stats?.avg_quality || 0, color: 'text-yellow-400' },
                      { label: 'XP', value: selectedUserProfile.stats?.xp || 0, color: 'text-purple-400' },
                      { label: language === 'it' ? 'Premi' : 'Awards', value: selectedUserProfile.stats?.awards_count || 0, color: 'text-amber-400' },
                      { label: 'Fame', value: selectedUserProfile.stats?.fame || 0, color: 'text-pink-400' },
                    ].map((stat, i) => (
                      <div key={i} className="bg-white/5 rounded-lg p-2 text-center">
                        <p className={`font-bold text-sm ${stat.color}`}>{stat.value}</p>
                        <p className="text-[10px] text-gray-500">{stat.label}</p>
                      </div>
                    ))}
                  </div>
                  
                  {/* Genre breakdown */}
                  {selectedUserProfile.genre_breakdown && Object.keys(selectedUserProfile.genre_breakdown).length > 0 && (
                    <div>
                      <p className="text-xs text-gray-400 mb-2 font-semibold">{language === 'it' ? 'Generi preferiti' : 'Favorite Genres'}</p>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(selectedUserProfile.genre_breakdown).sort((a,b) => b[1]-a[1]).slice(0,5).map(([genre, count]) => (
                          <Badge key={genre} className="bg-white/10 text-gray-300 text-[10px]">{genre}: {count}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Recent films */}
                  {selectedUserProfile.recent_films?.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-400 mb-2 font-semibold">{language === 'it' ? 'Film recenti' : 'Recent Films'}</p>
                      <div className="space-y-2">
                        {selectedUserProfile.recent_films.slice(0, 6).map(film => (
                          <div key={film.id} className="flex items-center gap-2 bg-white/5 rounded-lg p-2 cursor-pointer hover:bg-white/10" onClick={() => { setShowOnlineUsersPanel(false); navigate(`/films/${film.id}`); }}>
                            {film.poster_url ? (
                              <img src={film.poster_url} alt="" className="w-10 h-14 rounded object-cover" />
                            ) : (
                              <div className="w-10 h-14 rounded bg-gray-700 flex items-center justify-center"><Film className="w-4 h-4 text-gray-500" /></div>
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-semibold truncate">{film.title}</p>
                              <div className="flex items-center gap-2 text-[10px] text-gray-500">
                                <span>{film.genre}</span>
                                <span>Q: {film.quality_score?.toFixed(0)}</span>
                                {film.film_tier && film.film_tier !== 'normal' && (
                                  <Badge className="bg-yellow-500/20 text-yellow-400 text-[8px] h-3">{film.film_tier}</Badge>
                                )}
                              </div>
                            </div>
                            <span className="text-green-400 text-[10px] font-bold">${((film.total_revenue || film.revenue || 0)/1000000).toFixed(1)}M</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          ) : (
            /* Online + Offline users list */
            <div className="flex flex-col h-[80vh]">
              <DialogHeader className="p-4 pb-2 border-b border-white/10">
                <DialogTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2 text-green-400">
                  <Users className="w-5 h-5" /> {language === 'it' ? 'GIOCATORI' : 'PLAYERS'}
                  <Badge className="bg-green-500/20 text-green-400 ml-2">{allPlayersList.filter(u => u.is_online).length} online</Badge>
                </DialogTitle>
              </DialogHeader>
              
              <ScrollArea className="flex-1">
                <div className="p-3 space-y-1">
                  {/* Online players */}
                  {allPlayersList.filter(u => u.is_online).length > 0 && (
                    <p className="text-[10px] text-green-400 uppercase tracking-wider font-bold px-1 py-1">{language === 'it' ? 'Online' : 'Online'} ({allPlayersList.filter(u => u.is_online).length})</p>
                  )}
                  {allPlayersList.filter(u => u.is_online).map(p => (
                    <div 
                      key={p.id} 
                      className="flex items-center gap-3 p-2 rounded-lg bg-green-500/5 hover:bg-green-500/10 cursor-pointer transition-all"
                      onClick={() => viewUserProfile(p.id)}
                      data-testid={`player-online-${p.id}`}
                    >
                      <div className="relative">
                        <Avatar className="w-9 h-9">
                          <AvatarImage src={p.avatar_url} />
                          <AvatarFallback className="bg-green-500/20 text-green-400 font-bold text-xs">{(p.nickname || '?')[0]}</AvatarFallback>
                        </Avatar>
                        <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-[#111]"></span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm truncate">{p.nickname}</p>
                        <p className="text-[10px] text-gray-500 truncate">{p.production_house_name || ''}</p>
                      </div>
                      {p.level && <Badge className="bg-purple-500/20 text-purple-400 text-[9px]">Lv.{p.level}</Badge>}
                      <ChevronRight className="w-4 h-4 text-gray-600" />
                    </div>
                  ))}
                  
                  {/* Offline players */}
                  {allPlayersList.filter(u => !u.is_online).length > 0 && (
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold px-1 py-1 mt-3 border-t border-white/5 pt-2">{language === 'it' ? 'Offline' : 'Offline'} ({allPlayersList.filter(u => !u.is_online).length})</p>
                  )}
                  {allPlayersList.filter(u => !u.is_online).map(p => (
                    <div 
                      key={p.id} 
                      className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.02] hover:bg-white/5 cursor-pointer transition-all opacity-70"
                      onClick={() => viewUserProfile(p.id)}
                      data-testid={`player-offline-${p.id}`}
                    >
                      <div className="relative">
                        <Avatar className="w-9 h-9">
                          <AvatarImage src={p.avatar_url} />
                          <AvatarFallback className="bg-gray-700 text-gray-400 font-bold text-xs">{(p.nickname || '?')[0]}</AvatarFallback>
                        </Avatar>
                        <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-gray-600 rounded-full border-2 border-[#111]"></span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm truncate text-gray-400">{p.nickname}</p>
                        <p className="text-[10px] text-gray-600 truncate">{p.production_house_name || ''}</p>
                      </div>
                      {p.level && <Badge className="bg-gray-700/50 text-gray-500 text-[9px]">Lv.{p.level}</Badge>}
                      <ChevronRight className="w-4 h-4 text-gray-700" />
                    </div>
                  ))}

                  {allPlayersList.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <Users className="w-10 h-10 mx-auto mb-2 opacity-30" />
                      <p>{language === 'it' ? 'Nessun giocatore trovato' : 'No players found'}</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          )}
          
          {loadingProfile && (
            <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-20">
              <RefreshCw className="w-8 h-8 text-green-400 animate-spin" />
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Global Player Popup - Opens from any nickname click */}
      <Dialog open={!!popupData} onOpenChange={(open) => { if(!open) setPopupData(null); }}>
        <DialogContent className="max-w-sm max-h-[85vh] overflow-hidden bg-[#111] border-cyan-500/30 p-0">
          {popupData?.profile ? (
            <div className="flex flex-col max-h-[80vh]">
              {/* Sticky header with actions */}
              <div className="sticky top-0 z-10 bg-[#111] border-b border-white/10 p-3 flex items-center gap-2">
                <Avatar className="w-10 h-10 ring-2 ring-cyan-500">
                  <AvatarImage src={popupData.profile.user?.avatar_url} />
                  <AvatarFallback className="bg-cyan-500/20 text-cyan-400 font-bold">{popupData.profile.user?.nickname?.[0]}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-sm truncate">{popupData.profile.user?.nickname}</p>
                  <p className="text-[10px] text-gray-500 truncate">{popupData.profile.user?.production_house_name}</p>
                </div>
              </div>
              
              {/* Action buttons - sticky */}
              <div className="sticky top-[52px] z-10 bg-[#111]/95 backdrop-blur-md border-b border-white/10 p-2 flex gap-1.5 justify-center">
                {popupData.friendStatus?.status === 'friends' ? (
                  <Button 
                    size="sm" variant="outline"
                    className="border-red-500/30 text-red-400 hover:bg-red-500/10 h-7 px-3 text-[10px]"
                    onClick={() => removeFriend(popupData.profile.user?.id)}
                    disabled={sendingFriendReq === popupData.profile.user?.id}
                    data-testid="global-remove-friend-btn"
                  >
                    {sendingFriendReq === popupData.profile.user?.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <><UserCheck className="w-3 h-3 mr-1" />{language === 'it' ? 'Rimuovi Amico' : 'Remove Friend'}</>}
                  </Button>
                ) : popupData.friendStatus?.status === 'pending_sent' ? (
                  <Button size="sm" variant="outline" className="border-gray-500/30 text-gray-400 h-7 px-3 text-[10px]" disabled>
                    <Clock className="w-3 h-3 mr-1" /> {language === 'it' ? 'Richiesta Inviata' : 'Request Sent'}
                  </Button>
                ) : (
                  <Button 
                    size="sm"
                    className="bg-cyan-500 hover:bg-cyan-600 text-black h-7 px-3 text-[10px] font-bold"
                    onClick={() => sendFriendRequest(popupData.profile.user?.id)}
                    disabled={sendingFriendReq === popupData.profile.user?.id}
                    data-testid="global-add-friend-btn"
                  >
                    {sendingFriendReq === popupData.profile.user?.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <><UserPlus className="w-3 h-3 mr-1" />{language === 'it' ? 'Richiedi Amicizia' : 'Add Friend'}</>}
                  </Button>
                )}
                <Button 
                  size="sm"
                  className="bg-pink-500 hover:bg-pink-600 text-white h-7 px-3 text-[10px] font-bold"
                  onClick={() => { setPopupData(null); navigate('/challenges'); }}
                  data-testid="global-challenge-btn"
                >
                  <Swords className="w-3 h-3 mr-1" /> {language === 'it' ? 'Sfida 1v1' : '1v1 Challenge'}
                </Button>
                <Button 
                  size="sm" variant="outline"
                  className="border-white/10 text-gray-300 h-7 px-3 text-[10px]"
                  onClick={() => { setPopupData(null); navigate('/chat'); }}
                  data-testid="global-message-btn"
                >
                  <MessageSquare className="w-3 h-3 mr-1" /> {language === 'it' ? 'Messaggio' : 'Message'}
                </Button>
              </div>
              
              {/* Profile content */}
              <ScrollArea className="flex-1">
                <div className="p-4 space-y-4">
                  {/* Stats grid */}
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: language === 'it' ? 'Film' : 'Films', value: popupData.profile.stats?.total_films || 0, color: 'text-blue-400' },
                      { label: language === 'it' ? 'Incassi' : 'Revenue', value: `$${((popupData.profile.stats?.total_revenue || 0)/1000000).toFixed(1)}M`, color: 'text-green-400' },
                      { label: language === 'it' ? 'Qualità' : 'Quality', value: popupData.profile.stats?.avg_quality || 0, color: 'text-yellow-400' },
                      { label: 'XP', value: popupData.profile.stats?.xp || 0, color: 'text-purple-400' },
                      { label: language === 'it' ? 'Premi' : 'Awards', value: popupData.profile.stats?.awards_count || 0, color: 'text-amber-400' },
                      { label: 'Lv.', value: popupData.profile.stats?.level || 1, color: 'text-cyan-400' },
                    ].map((stat, i) => (
                      <div key={i} className="bg-white/5 rounded-lg p-2 text-center">
                        <p className={`font-bold text-sm ${stat.color}`}>{stat.value}</p>
                        <p className="text-[10px] text-gray-500">{stat.label}</p>
                      </div>
                    ))}
                  </div>
                  
                  {/* Recent films */}
                  {popupData.profile.recent_films?.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-400 mb-2 font-semibold">{language === 'it' ? 'Film recenti' : 'Recent Films'}</p>
                      <div className="space-y-1.5">
                        {popupData.profile.recent_films.slice(0, 5).map(film => (
                          <div key={film.id} className="flex items-center gap-2 bg-white/5 rounded-lg p-2 cursor-pointer hover:bg-white/10" onClick={() => { setPopupData(null); navigate(`/films/${film.id}`); }}>
                            {film.poster_url ? (
                              <img src={film.poster_url} alt="" className="w-8 h-12 rounded object-cover" />
                            ) : (
                              <div className="w-8 h-12 rounded bg-gray-700 flex items-center justify-center"><Film className="w-3 h-3 text-gray-500" /></div>
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-semibold truncate">{film.title}</p>
                              <p className="text-[10px] text-gray-500">{film.genre} - Q:{film.quality_score?.toFixed(0)}</p>
                            </div>
                            <span className="text-green-400 text-[10px]">${((film.total_revenue||0)/1000000).toFixed(1)}M</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          ) : (
            <div className="p-8 flex items-center justify-center">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </nav>
  );
};

// Password Recovery Page

// ==================== ROUTING ====================

const ProtectedRoute = ({ children }) => {
  const { user, loading, api } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  const [popupData, setPopupData] = useState(null);
  
  const openPlayerPopup = async (userId) => {
    if (!userId || userId === user?.id) return;
    setPopupData({ userId, loading: true });
    try {
      const [profileRes, friendRes] = await Promise.all([
        api.get(`/users/${userId}/full-profile`),
        api.get(`/friends/status/${userId}`)
      ]);
      setPopupData({ userId, profile: profileRes.data, friendStatus: friendRes.data, loading: false });
    } catch(e) {
      setPopupData(null);
    }
  };
  
  if (loading) return <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center"><Clapperboard className="w-10 h-10 text-yellow-500 animate-pulse" /></div>;
  if (!user) return <Navigate to="/auth" replace />;
  return (
    <PlayerPopupContext.Provider value={{ openPlayerPopup, popupData, setPopupData }}>
      <TopNavbar />
      <AnimatePresence mode="wait">
        <PageTransition key={location.pathname}>
          <React.Suspense fallback={<PageSkeleton />}>
            {children}
          </React.Suspense>
        </PageTransition>
      </AnimatePresence>
    </PlayerPopupContext.Provider>
  );
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
                <Route path="/challenges" element={<ProtectedRoute><ChallengesPage /></ProtectedRoute>} />
                <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
                <Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
                <Route path="/creator-board" element={<ProtectedRoute><CreatorBoard /></ProtectedRoute>} />
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

