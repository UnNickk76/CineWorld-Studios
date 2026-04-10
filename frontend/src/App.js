// force rebuild - alias fix 2026-03-28
import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
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
  Wallet, Bell, HelpCircle, Info, Music, BookOpen, Medal, Eye, EyeOff, Play,
  ArrowLeft, ArrowRight, UserPlus, UserCheck, Handshake, Target, Clock, RotateCcw,
  Download, Smartphone, Share2, Link2, Copy, QrCode, CheckCircle, Zap, Lightbulb, Bug,
  KeyRound, AlertCircle, Mail, Tv, Swords, Shield, Flame, History, ArrowUpCircle, Pen, Save, Megaphone, Store, Radio, Disc
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
import { AuthContext, LanguageContext, AuthProvider, LanguageProvider, useTranslations, API, PlayerPopupContext, usePlayerPopup, ProductionMenuContext, useProductionMenu } from './contexts';
import { SKILL_TRANSLATIONS } from './constants';
import { PageTransition, PageSkeleton } from './components/PageTransition';
import { LoadingSpinner, ErrorBoundary } from './components/ErrorBoundary';
import { GameStoreProvider, useGameStore } from './contexts/GameStore';
import { ConfirmProvider, useConfirm } from './components/ConfirmDialog';
import { NotificationProvider, useNotifications } from './components/NotificationProvider';
import { VelionOverlay } from './components/VelionOverlay';
import { VelionPanel, shouldAutoShowTutorial } from './components/VelionPanel';
import { GuestTutorial } from './components/GuestTutorial';

// Lazy-load pages from separate files for code-splitting
const ReleaseNotes = React.lazy(() => import('./pages/ReleaseNotes'));
const TutorialPage = React.lazy(() => import('./pages/TutorialPage'));
const SystemNotesPage = React.lazy(() => import('./pages/SystemNotesPage'));
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
import { PWAInstallBanner } from './components/PWAInstallBanner';
const DownloadAppPage = React.lazy(() => import('./pages/DownloadAppPage'));
const FeedbackBoard = React.lazy(() => import('./pages/FeedbackBoard'));
const FestivalsPage = React.lazy(() => import('./pages/FestivalsPage'));
const FilmDetail = React.lazy(() => import('./pages/FilmDetail'));
const FilmMarketplace = React.lazy(() => import('./pages/FilmMarketplace'));
const FilmWizard = React.lazy(() => import('./pages/FilmWizard'));
const FilmPipeline = React.lazy(() => import('./pages/FilmPipeline'));
const PipelineV2 = React.lazy(() => import('./pages/PipelineV2'));
const FriendsPage = React.lazy(() => import('./pages/FriendsPage'));
const InfrastructurePage = React.lazy(() => import('./pages/InfrastructurePage'));
const ActingSchool = React.lazy(() => import('./pages/ActingSchool'));
const LeaderboardPage = React.lazy(() => import('./pages/LeaderboardPage'));
const MajorPage = React.lazy(() => import('./pages/MajorPage'));
const MarketplacePage = React.lazy(() => import('./pages/MarketplacePage'));
const ContestsPage = React.lazy(() => import('./pages/ContestsPage'));
const ContestPage = React.lazy(() => import('./pages/ContestPage'));
const MiniGamesPage = React.lazy(() => import('./pages/MiniGamesPage'));
import LoginRewardPopup from './components/LoginRewardPopup';
import { AutoTickNotifications } from './components/AutoTickNotifications';
import TutorialModal from './components/TutorialModal';
import DashboardTour from './components/DashboardTour';
const MyFilms = React.lazy(() => import('./pages/MyFilms'));
const NotificationsPage = React.lazy(() => import('./pages/NotificationsPage'));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage'));
const ResetPasswordPage = React.lazy(() => import('./pages/ResetPasswordPage'));
const SagasSeriesPage = React.lazy(() => import('./pages/SagasSeriesPage'));
const PasswordRecoveryPage = React.lazy(() => import('./pages/PasswordRecoveryPage'));
const NicknameRecoveryPage = React.lazy(() => import('./pages/NicknameRecoveryPage'));
const StatisticsPage = React.lazy(() => import('./pages/StatisticsPage'));
const EmergingScreenplays = React.lazy(() => import('./pages/EmergingScreenplays'));
const PlayerPublicProfile = React.lazy(() => import('./pages/PlayerPublicProfile'));
const SeriesTVPipeline = React.lazy(() => import('./pages/SeriesTVPipeline'));
const SeriesDetail = React.lazy(() => import('./pages/SeriesDetail'));
const AnimePipeline = React.lazy(() => import('./pages/AnimePipeline'));
const SequelPipeline = React.lazy(() => import('./pages/SequelPipeline'));
const EmittenteTVPage = React.lazy(() => import('./pages/EmittenteTVPage'));
const TVStationPage = React.lazy(() => import('./pages/TVStationPage'));
const AllTVStationsPage = React.lazy(() => import('./pages/AllTVStationsPage'));
const CastingAgencyPage = React.lazy(() => import('./pages/CastingAgencyPage'));
const AdminPage = React.lazy(() => import('./pages/AdminPage'));
const HqPage = React.lazy(() => import('./pages/HqPage'));
const PvPArenaPage = React.lazy(() => import('./pages/PvPArenaPage'));
const EventHistoryPage = React.lazy(() => import('./pages/EventHistoryPage'));
const StrutturePage = React.lazy(() => import('./pages/StrutturePage'));
const AgenziaPage = React.lazy(() => import('./pages/AgenziaPage'));
const StrategicoPage = React.lazy(() => import('./pages/StrategicoPage'));

// ==================== COMPONENTS ====================

// Module-level flag: prevents donate popup from re-triggering on component remounts
let _donatePopupChecked = false;


const VelionMenuControl = () => {
  const [mode, setMode] = React.useState(() => window.__velionMode || 'on');

  React.useEffect(() => {
    const handler = () => setMode(window.__velionMode || 'on');
    window.addEventListener('velion-mode-changed', handler);
    return () => window.removeEventListener('velion-mode-changed', handler);
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full relative">
            <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, transparent 100%)' }} />
            <img src="/velion.png" alt="" className="w-full h-full object-contain rounded-full relative z-10" style={{ mixBlendMode: 'screen', filter: 'brightness(1.4) contrast(1.3)' }} />
          </div>
          <span className="text-xs text-gray-300">Assistente Velion</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { 
              window.dispatchEvent(new Event('velion-show'));
              window.dispatchEvent(new Event('velion-tutorial-open'));
            }}
            className="text-[10px] text-cyan-400 hover:text-cyan-300 px-2 py-1 rounded-md hover:bg-cyan-500/10 transition-colors"
            data-testid="menu-velion-btn"
          >
            Apri
          </button>
          <button
            onClick={() => window.dispatchEvent(new Event('velion-toggle-mode'))}
            className={`relative w-9 h-5 rounded-full transition-colors ${mode === 'on' ? 'bg-cyan-500/30' : 'bg-white/10'}`}
            data-testid="velion-mode-toggle"
          >
            <div className={`absolute top-0.5 w-4 h-4 rounded-full transition-all ${
              mode === 'on' ? 'left-[18px] bg-cyan-400' : 'left-0.5 bg-gray-500'
            }`} />
          </button>
        </div>
      </div>
      {mode === 'off' && (
        <p className="text-[10px] text-gray-600 mt-1 pl-8">Riattiva Velion per suggerimenti automatici</p>
      )}
    </div>
  );
};

// ─── GUEST CONVERT MODAL (Loss Aversion) ─────────────────────────
const GuestConvertModalContent = ({ user, api, form, setForm, converting, setConverting, onSuccess, onDismiss }) => {
  const [phase, setPhase] = useState('hook'); // 'hook' | 'form'
  const [stats, setStats] = useState({ films: 0, earnings: 0 });

  useEffect(() => {
    if (!user) return;
    const films = user.total_lifetime_revenue > 0 ? Math.max(1, Math.round(user.total_lifetime_revenue / 500000)) : 0;
    setStats({
      films: films || (user.funds > 1000000 ? 1 : 0),
      earnings: user.funds || 0,
    });
    // Haptic feedback
    try { navigator?.vibrate?.([20]); } catch {}
  }, [user]);

  // Fetch actual film count
  useEffect(() => {
    if (!api) return;
    api.get('/film-pipeline/all').then(r => {
      const count = r.data?.films?.length || r.data?.length || 0;
      if (count > 0) setStats(s => ({ ...s, films: count }));
    }).catch(() => {});
  }, [api]);

  const formatMoney = (n) => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
    return String(n);
  };

  const handleConvert = async () => {
    setConverting(true);
    try {
      const res = await api.post('/auth/convert', form);
      localStorage.removeItem('cineworld_guest_start');
      if (res.data.access_token) localStorage.setItem('cineworld_token', res.data.access_token);
      localStorage.setItem('show_dashboard_tour', '1');
      toast.success('Account registrato! I tuoi progressi sono salvi');
      onSuccess();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella conversione');
    } finally {
      setConverting(false);
    }
  };

  if (phase === 'hook') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2 }}
        className="p-5 text-center"
      >
        <DialogTitle className="sr-only">Salva progressi</DialogTitle>
        <DialogDescription className="sr-only">Registrati per non perdere i tuoi progressi</DialogDescription>

        {/* Icon */}
        <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
          <Film className="w-7 h-7 text-red-400" />
        </div>

        {/* Title */}
        <h2 className="text-lg font-extrabold text-white mb-3">Non perdere il tuo studio</h2>

        {/* Stats - dynamic */}
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3 mb-3 space-y-2 text-left">
          <p className="text-[11px] text-gray-400 mb-2">Hai già iniziato a costruire qualcosa:</p>
          {stats.films > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                <Film className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <span className="text-xs text-white"><strong className="text-blue-400">{stats.films}</strong> film creati</span>
            </div>
          )}
          {stats.earnings > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-yellow-500/10 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
              </div>
              <span className="text-xs text-white"><strong className="text-yellow-400">{formatMoney(stats.earnings)}</strong> CW$ guadagnati</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-cyan-500/10 flex items-center justify-center flex-shrink-0">
              <Star className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <span className="text-xs text-white">Studio in <strong className="text-cyan-400">crescita</strong></span>
          </div>
        </div>

        {/* Loss warning */}
        <p className="text-[11px] text-red-400/80 font-medium mb-4">Se esci ora, perderai tutto.</p>

        {/* CTA */}
        <motion.div
          animate={{ scale: [1, 1.02, 1] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Button
            className="w-full h-10 bg-gradient-to-r from-yellow-500 to-amber-500 hover:from-yellow-400 hover:to-amber-400 text-black font-bold text-sm rounded-xl shadow-lg shadow-yellow-500/20"
            onClick={() => setPhase('form')}
            data-testid="guest-convert-save-btn"
          >
            Salva progressi
          </Button>
        </motion.div>

        <p className="text-[9px] text-gray-600 mt-2 mb-1">Salva i tuoi progressi in pochi secondi</p>

        <button
          className="text-[10px] text-gray-600 hover:text-gray-400 transition-colors py-1"
          onClick={onDismiss}
          data-testid="guest-convert-dismiss"
        >
          Continua come ospite
        </button>
      </motion.div>
    );
  }

  // Phase: form
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2 }}
      className="p-5"
    >
      <DialogTitle className="sr-only">Registrazione</DialogTitle>
      <DialogDescription className="sr-only">Compila per salvare</DialogDescription>

      <button onClick={() => setPhase('hook')} className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-300 mb-3 transition-colors">
        <ArrowLeft className="w-3 h-3" /> Indietro
      </button>

      <h3 className="text-sm font-bold text-white mb-3 text-center">Crea il tuo account</h3>

      <div className="space-y-2.5">
        <Input
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={e => setForm(p => ({...p, email: e.target.value}))}
          className="h-9 bg-white/5 border-white/10 text-sm"
          data-testid="guest-convert-email"
        />
        <Input
          placeholder="Password (min 6 caratteri)"
          type="password"
          value={form.password}
          onChange={e => setForm(p => ({...p, password: e.target.value}))}
          className="h-9 bg-white/5 border-white/10 text-sm"
          data-testid="guest-convert-password"
        />
        <Input
          placeholder="Nickname"
          value={form.nickname}
          onChange={e => setForm(p => ({...p, nickname: e.target.value}))}
          className="h-9 bg-white/5 border-white/10 text-sm"
          data-testid="guest-convert-nickname"
        />
        <Button
          className="w-full bg-gradient-to-r from-yellow-500 to-amber-500 text-black hover:from-yellow-400 hover:to-amber-400 font-bold h-9 text-sm rounded-xl"
          disabled={converting || !form.email || !form.password || form.password.length < 6}
          onClick={handleConvert}
          data-testid="guest-convert-submit"
        >
          {converting ? 'Registrazione...' : 'Salva progressi'}
        </Button>
        <button
          className="w-full text-center text-[10px] text-gray-600 hover:text-gray-400 py-1 transition-colors"
          onClick={onDismiss}
          data-testid="guest-convert-dismiss-form"
        >
          Continua come ospite
        </button>
      </div>
    </motion.div>
  );
};

// ─── GUEST REGISTER BADGE ────────────────────────────────────
const GuestRegisterBadge = ({ onRegister }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    const seen = localStorage.getItem('cw_guest_reg_tooltip');
    if (!seen) {
      setShowTooltip(true);
      const t = setTimeout(() => { setShowTooltip(false); localStorage.setItem('cw_guest_reg_tooltip', '1'); }, 5000);
      return () => clearTimeout(t);
    }
  }, []);

  return (
    <div className="fixed bottom-[88px] right-3 z-[90]" data-testid="guest-register-badge">
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.9 }}
            className="absolute bottom-full right-0 mb-2 bg-[#111] border border-red-500/30 rounded-lg px-3 py-2 whitespace-nowrap shadow-lg shadow-red-500/10"
          >
            <p className="text-[10px] text-white font-medium">Salva i tuoi progressi registrandoti!</p>
            <div className="absolute bottom-[-5px] right-4 w-2.5 h-2.5 bg-[#111] border-r border-b border-red-500/30 rotate-45" />
          </motion.div>
        )}
      </AnimatePresence>
      <motion.button
        onClick={onRegister}
        className="flex items-center gap-1.5 bg-red-600 hover:bg-red-500 text-white rounded-full pl-3 pr-3.5 py-2 shadow-lg shadow-red-600/30 transition-colors"
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        data-testid="guest-register-btn"
      >
        <UserPlus className="w-3.5 h-3.5" />
        <span className="text-[11px] font-bold tracking-wide">Registrati</span>
      </motion.button>
    </div>
  );
};

const TopNavbar = () => {
  const { user, logout, api } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const { t } = useTranslations();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showDonateDialog, setShowDonateDialog] = useState(false);
  const [showDonatePopup, setShowDonatePopup] = useState(false);
  const [donationsEnabled, setDonationsEnabled] = useState(true);
  const [showGameTutorial, setShowGameTutorial] = useState(false);
  const [levelInfo, setLevelInfo] = useState(null);
  const { unreadCount: notificationCount } = useNotifications();
  const [releaseNotesCount, setReleaseNotesCount] = useState(0);
  const [systemNotesCount, setSystemNotesCount] = useState(0);
  const [emergingScreenplaysCount, setEmergingScreenplaysCount] = useState(0);
  const [unreadEvents, setUnreadEvents] = useState(() => parseInt(sessionStorage.getItem('cw_unread_events') || '0'));

  // Listen for unread events updates from AutoTickNotifications
  useEffect(() => {
    const handler = () => setUnreadEvents(parseInt(sessionStorage.getItem('cw_unread_events') || '0'));
    window.addEventListener('cw-unread-update', handler);
    return () => window.removeEventListener('cw-unread-update', handler);
  }, []);

  // Reset when visiting event-history
  useEffect(() => {
    if (location.pathname === '/event-history') {
      setUnreadEvents(0);
      sessionStorage.setItem('cw_unread_events', '0');
    }
  }, [location.pathname]);

  // Prefetch data on hover for instant navigation
  const gameStore = useGameStore();
  const handleNavHover = useCallback((path) => {
    if (!gameStore) return;
    const map = {
      '/dashboard': ['/dashboard/batch', '/films/my/featured?limit=9'],
      '/produce': ['/film-pipeline/all', '/film-pipeline/badges'],
      '/pvp-arena': ['/pvp-cinema/arena', '/pvp-cinema/stats'],
      '/my-films': ['/films/my'],
      '/marketplace': ['/marketplace/listings'],
    };
    const urls = map[path];
    if (urls) gameStore.prefetch(urls);
  }, [gameStore]);
  const [majorInfo, setMajorInfo] = useState(null);
  const [festivalNotifications, setFestivalNotifications] = useState([]);
  const [showOnlineUsersPanel, setShowOnlineUsersPanel] = useState(false);
  const [onlineUsersCount, setOnlineUsersCount] = useState(0);
  const [onlineUsersList, setOnlineUsersList] = useState([]);
  const [allPlayersList, setAllPlayersList] = useState([]);
  const [selectedOnlineUser, setSelectedOnlineUser] = useState(null);
  const [popupNotifications, setPopupNotifications] = useState([]);

  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const mins = Math.floor((now - date) / 60000);
    if (mins < 1) return 'ora';
    if (mins < 60) return `${mins} min fa`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h fa`;
    const days = Math.floor(hrs / 24);
    if (days === 1) return 'ieri';
    return `${days}g fa`;
  };
  const [selectedUserProfile, setSelectedUserProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [sendingFriendReq, setSendingFriendReq] = useState(null);
  const [friendshipStatus, setFriendshipStatus] = useState(null);
  const [globalPlayerPopup, setGlobalPlayerPopup] = useState(null); // unused, kept for compat
  const { openPlayerPopup: _ctxOpen, popupData, setPopupData } = usePlayerPopup();
  const [userTimezone, setUserTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Rome');
  const [popupView, setPopupView] = useState('stats'); // 'stats' or 'studio' - for global player popup
  const [profileGenreFilter, setProfileGenreFilter] = useState(null); // Genre filter for online user profile
  const [popupGenreFilter, setPopupGenreFilter] = useState(null); // Genre filter for player popup
  const [productionUnlocks, setProductionUnlocks] = useState(null);
  const { isOpen: showProductionMenu, setIsOpen: setShowProductionMenu } = useProductionMenu();
  const [showCineboardMenu, setShowCineboardMenu] = useState(false);
  const [showFilmsMenu, setShowFilmsMenu] = useState(false);
  const [loginReward, setLoginReward] = useState(null); // Login Coming Soon reward popup
  const [showGuestConvertModal, setShowGuestConvertModal] = useState(false);
  const [guestConvertForm, setGuestConvertForm] = useState({ email: '', password: '', nickname: '', production_house_name: '' });
  const [guestConverting, setGuestConverting] = useState(false);

  // Guest conversion timer - show modal after 20 minutes (only if tutorial completed)
  useEffect(() => {
    if (!user?.is_guest) return;
    if (!user?.tutorial_completed) return; // Don't show during tutorial
    const guestStart = parseInt(localStorage.getItem('cineworld_guest_start') || '0');
    const elapsed = Date.now() - guestStart;
    const TWENTY_MIN = 20 * 60 * 1000;
    const remaining = Math.max(TWENTY_MIN - elapsed, 5000);

    const timer = setTimeout(() => {
      setShowGuestConvertModal(true);
    }, remaining);

    return () => clearTimeout(timer);
  }, [user?.is_guest, user?.tutorial_completed]);

  // Core data - fetch once on mount + poll
  useEffect(() => {
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {});
    // Release notes and system notes are FROZEN - skip unread count fetch
    api.get('/emerging-screenplays/count').then(r => setEmergingScreenplaysCount(r.data.new || 0)).catch(() => {});
    api.get('/major/my').then(r => setMajorInfo(r.data)).catch(() => {});
    api.get('/production-studios/unlock-status').then(r => setProductionUnlocks(r.data)).catch(() => {});
    
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
    
    // Popup notification polling - fetch unread notifications for real-time popups
    let lastPopupTime = 0;
    const POPUP_THROTTLE_MS = 7000; // Max 1 popup every 7 seconds
    
    const fetchPopupNotifications = () => {
      api.get('/notifications/popup').then(r => {
        const notifs = r.data?.notifications || [];
        if (notifs.length > 0) {
          const now = Date.now();
          // Classify by severity
          const critical = notifs.filter(n => n.severity === 'critical');
          const medium = notifs.filter(n => n.severity === 'important');
          const soft = notifs.filter(n => n.severity === 'positive' || !n.severity);
          
          // CRITICAL: Show as prominent popup (throttled)
          if (critical.length > 0 && (now - lastPopupTime > POPUP_THROTTLE_MS)) {
            lastPopupTime = now;
            setPopupNotifications(prev => [...critical.slice(0, 2), ...prev].slice(0, 3));
            critical.forEach((n, i) => {
              setTimeout(() => {
                setPopupNotifications(prev => prev.filter(p => p.id !== n.id));
              }, 8000 + i * 2000);
            });
          }
          
          // MEDIUM: Show as lightweight toast (throttled, after critical)
          if (medium.length > 0) {
            const delay = critical.length > 0 ? POPUP_THROTTLE_MS : 0;
            setTimeout(() => {
              if (Date.now() - lastPopupTime > POPUP_THROTTLE_MS || critical.length === 0) {
                lastPopupTime = Date.now();
                medium.forEach((n, i) => {
                  setTimeout(() => {
                    toast(n.title, { 
                      description: n.message,
                      duration: 5000,
                      action: { label: 'Vai', onClick: () => {
                        api.post(`/notifications/${n.id}/read`).catch(() => {});
                        const path = n.link || (n.data?.content_id ? `/films/${n.data.content_id}` : '/notifications');
                        navigate(path);
                      }}
                    });
                  }, i * 1500);
                });
              }
            }, delay);
          }
          
          // SOFT: Only update badge count (no popup/toast)
          // Already handled by notification count update below
          
          // Count now managed by NotificationProvider
        }
      }).catch(() => {});
    };
    const popupInterval = setInterval(fetchPopupNotifications, 15000);
    setTimeout(fetchPopupNotifications, 3000); // Initial check after 3s
    
    return () => { clearInterval(festivalInterval); clearInterval(onlineInterval); clearInterval(popupInterval); };
  }, [api, userTimezone, language]);

  // Show donate popup — 2 hours after first daily login, max once per 24 solar hours
  useEffect(() => {
    if (!user || _donatePopupChecked) return;
    _donatePopupChecked = true;

    // Track daily session start in localStorage
    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    const storedDay = localStorage.getItem('cineworld_session_day');
    let sessionStart = parseInt(localStorage.getItem('cineworld_session_start') || '0', 10);

    if (storedDay !== today || !sessionStart) {
      sessionStart = Date.now();
      localStorage.setItem('cineworld_session_day', today);
      localStorage.setItem('cineworld_session_start', sessionStart.toString());
    }

    const twoHoursMs = 2 * 60 * 60 * 1000; // 2 hours
    const elapsed = Date.now() - sessionStart;
    const delay = Math.max(0, twoHoursMs - elapsed);

    const checkDonate = async () => {
      try {
        const res = await api.get('/game/donation-popup-check');
        setDonationsEnabled(true);
        if (res.data.show_popup) {
          setShowDonatePopup(true);
          api.post('/game/donation-popup-seen').catch(() => {});
        }
      } catch {
        try {
          const r = await api.get('/game/donations-status');
          setDonationsEnabled(r.data.donations_enabled);
        } catch {}
      }
    };

    // If 2h already passed today, check now (with small delay). Otherwise wait.
    const timer = setTimeout(checkDonate, delay > 0 ? delay : 5000);
    return () => clearTimeout(timer);
  }, [user]);

  // Lightweight refresh on navigation
  useEffect(() => {
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {});
    setShowProductionMenu(false);
    setShowCineboardMenu(false);
    setShowFilmsMenu(false);
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
    { path: '/create-film', icon: Clapperboard, label: language === 'it' ? 'Produci Film' : 'Produce Film' },
    { path: '/create-sequel', icon: Copy, label: language === 'it' ? 'Sequel' : 'Sequel' },
    { path: '/create-series', icon: Tv, label: 'Serie TV', locked: !productionUnlocks?.has_studio_serie_tv },
    { path: '/create-anime', icon: Sparkles, label: 'Anime', locked: !productionUnlocks?.has_studio_anime },
    { path: '/my-tv', icon: Radio, label: 'La Tua TV', locked: !productionUnlocks?.has_emittente_tv },
    { path: '/marketplace', icon: Store, label: language === 'it' ? 'Mercato' : 'Market' },
    { path: '/emerging-screenplays', icon: Pen, label: 'screenplays', notificationCount: emergingScreenplaysCount },
    { path: '/sagas', icon: BookOpen, label: 'sagas_series' },
    { path: '/hq', icon: Swords, label: language === 'it' ? 'Quartier Generale' : 'HQ' },
    { path: '/infrastructure', icon: Building, label: 'infrastructure' },
    { path: '/acting-school', icon: GraduationCap, label: 'acting_school' },
    { path: '/marketplace', icon: ShoppingBag, label: 'marketplace', disabled: true, pauseLabel: 'Marketplace (Prossimamente)' },
    { path: '/tour', icon: MapPin, label: 'tour' },
    { path: '/journal', icon: Newspaper, label: 'cinema_journal' },
    { path: '/stars', icon: Star, label: 'discovered_stars' },
    { path: '/festivals', icon: Award, label: 'festivals' },
    { path: '/social', icon: Globe, label: 'cineboard' },
    { path: '/games', icon: Trophy, label: 'contests' },
    { path: '/minigiochi', icon: Gamepad2, label: language === 'it' ? 'Minigiochi + Sfide' : 'Minigames + VS' },
    { path: '/leaderboard', icon: BarChart3, label: 'leaderboard' },
    { path: '/pvp-arena', icon: Target, label: 'Arena' },
    { path: '/chat', icon: MessageSquare, label: 'chat' },
    { path: '/releases', icon: Megaphone, label: 'release_notes', frozen: true },
    { path: '/feedback', icon: Lightbulb, label: 'feedback' },
    { path: '/tutorial', icon: HelpCircle, label: 'tutorial' },
    { path: '/system-notes', icon: Bell, label: language === 'it' ? 'Note di Sistema' : 'System Notes', frozen: true },
    { path: '/credits', icon: Info, label: 'credits' },
  ];

  const gameDate = new Date().toLocaleDateString(language === 'it' ? 'it-IT' : language === 'es' ? 'es-ES' : language === 'fr' ? 'fr-FR' : language === 'de' ? 'de-DE' : 'en-US', {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
  });
  
  // Check if we can go back
  const canGoBack = location.pathname !== '/dashboard';

  return (
    <nav className="fixed top-0 left-0 right-0 bg-[#0F0F10] border-b border-white/10 z-50 sidemenu-translate" style={{ paddingTop: 'env(safe-area-inset-top, 0px)' }}>
      <div className="max-w-7xl mx-auto h-14 px-2 sm:px-3 flex items-center justify-between">
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
          
          <div className="flex items-center gap-1.5 cursor-pointer" onClick={() => { if (location.pathname === '/dashboard') { window.dispatchEvent(new Event('dashboard-toggle-menu')); } else { navigate('/dashboard'); } }} data-testid="logo">
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
        <div className="flex items-center gap-0.5 sm:gap-1 flex-shrink-0">
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
          
          {/* Major */}
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
          
          {/* CineBoard/Social - Popup Menu */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${showCineboardMenu || location.pathname === '/social' ? 'text-green-400' : 'text-gray-400 hover:text-green-400'}`}
              onClick={() => setShowCineboardMenu(!showCineboardMenu)}
              data-testid="cineboard-btn"
              title="CineBoard"
            >
              <Trophy className="w-4 h-4" />
            </Button>
            <AnimatePresence>
              {showCineboardMenu && (
                <>
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-[60]"
                    onClick={() => setShowCineboardMenu(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.95 }}
                    transition={{ type: 'spring', damping: 25, stiffness: 400 }}
                    className="fixed top-14 left-2 right-2 sm:absolute sm:top-full sm:left-auto sm:right-0 sm:w-48 mt-1 z-[61]"
                    data-testid="cineboard-menu"
                  >
                    <div className="bg-[#111113] border border-white/10 rounded-xl p-2 shadow-2xl space-y-1">
                      <p className="text-[9px] text-gray-500 uppercase tracking-widest font-semibold px-2 mb-1">Classifiche</p>
                      <button
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                          location.pathname === '/social' && !location.search ? 'bg-green-500/20 text-green-400' : 'text-gray-300 hover:bg-white/5'
                        }`}
                        onClick={() => { navigate('/social'); setShowCineboardMenu(false); }}
                        data-testid="cineboard-menu-film"
                      >
                        <Film className="w-4 h-4 text-yellow-400" />
                        <div className="text-left"><span className="block">Film</span><span className="text-[9px] opacity-50">Top 50, Giornaliera, Settimanale</span></div>
                      </button>
                      <button
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                          location.search?.includes('view=series') ? 'bg-blue-500/20 text-blue-400' : 'text-gray-300 hover:bg-white/5'
                        }`}
                        onClick={() => { navigate('/social?view=series'); setShowCineboardMenu(false); }}
                        data-testid="cineboard-menu-series"
                      >
                        <Tv className="w-4 h-4 text-blue-400" />
                        <div className="text-left"><span className="block">Serie TV</span><span className="text-[9px] opacity-50">Trend Settimanale</span></div>
                      </button>
                      <button
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                          location.search?.includes('view=anime') ? 'bg-orange-500/20 text-orange-400' : 'text-gray-300 hover:bg-white/5'
                        }`}
                        onClick={() => { navigate('/social?view=anime'); setShowCineboardMenu(false); }}
                        data-testid="cineboard-menu-anime"
                      >
                        <Sparkles className="w-4 h-4 text-orange-400" />
                        <div className="text-left"><span className="block">Anime</span><span className="text-[9px] opacity-50">Trend Settimanale</span></div>
                      </button>
                      <div className="border-t border-white/5 my-1" />
                      <p className="text-[9px] text-gray-500 uppercase tracking-widest font-semibold px-2 mb-1">Emittenti TV</p>
                      <button
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                          location.search?.includes('view=tv-alltime') ? 'bg-red-500/20 text-red-400' : 'text-gray-300 hover:bg-white/5'
                        }`}
                        onClick={() => { navigate('/social?view=tv-alltime'); setShowCineboardMenu(false); }}
                        data-testid="cineboard-menu-tv-alltime"
                      >
                        <Radio className="w-4 h-4 text-red-400" />
                        <div className="text-left"><span className="block">Più Viste</span><span className="text-[9px] opacity-50">Di Sempre</span></div>
                      </button>
                      <button
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                          location.search?.includes('view=tv-weekly') ? 'bg-red-500/20 text-red-400' : 'text-gray-300 hover:bg-white/5'
                        }`}
                        onClick={() => { navigate('/social?view=tv-weekly'); setShowCineboardMenu(false); }}
                        data-testid="cineboard-menu-tv-weekly"
                      >
                        <Radio className="w-4 h-4 text-red-400" />
                        <div className="text-left"><span className="block">Share Settimanale</span><span className="text-[9px] opacity-50">Top Share</span></div>
                      </button>
                      <button
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                          location.search?.includes('view=tv-daily') ? 'bg-red-500/20 text-red-400' : 'text-gray-300 hover:bg-white/5'
                        }`}
                        onClick={() => { navigate('/social?view=tv-daily'); setShowCineboardMenu(false); }}
                        data-testid="cineboard-menu-tv-daily"
                      >
                        <Radio className="w-4 h-4 text-red-400" />
                        <div className="text-left"><span className="block">Share Giornaliero</span><span className="text-[9px] opacity-50">Live (ogni 5 min)</span></div>
                      </button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
          
          {/* Cinema Journal */}
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

          {/* EVENTI */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/event-history' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => navigate('/event-history')}
            data-testid="event-history-nav-btn"
            title="Eventi"
          >
            <Sparkles className="w-4 h-4" />
            {unreadEvents > 0 && (
              <span
                className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 flex items-center justify-center bg-red-500 text-white text-[9px] font-bold rounded-full px-1 leading-none animate-pulse"
                data-testid="unread-events-badge"
              >
                {unreadEvents > 99 ? '99+' : unreadEvents}
              </span>
            )}
          </Button>
          
          {/* Minigiochi - Always visible */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 ${location.pathname === '/minigiochi' ? 'text-cyan-400' : 'text-gray-400 hover:text-cyan-400'}`}
            onClick={() => navigate('/minigiochi')}
            data-testid="challenges-nav-btn"
            title="Minigiochi + Sfide"
          >
            <Gamepad2 className="w-4 h-4" />
          </Button>

          
          {/* Chat */}
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

          {/* Tutorial - Colore evidenziato */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-7 w-7 sm:h-8 sm:w-8 p-0 text-lime-400/70 hover:text-lime-400`}
            onClick={() => setShowGameTutorial(true)}
            data-testid="tutorial-nav-btn"
            title="Tutorial"
          >
            <HelpCircle className="w-4 h-4" />
          </Button>

          {/* Funds - Compact */}
          <div className="flex items-center gap-0.5 bg-yellow-500/10 px-1 sm:px-2 py-0.5 sm:py-1 rounded border border-yellow-500/20">
            <DollarSign className="w-3 h-3 text-yellow-500" />
            <span className="text-yellow-500 font-bold text-[9px] sm:text-xs" data-testid="user-funds">
              ${user?.funds >= 1000000 ? `${(user?.funds / 1000000).toFixed(1)}M` : user?.funds >= 1000 ? `${(user?.funds / 1000).toFixed(0)}K` : user?.funds?.toLocaleString() || '0'}
            </span>
          </div>

          {/* CinePass */}
          <div className="flex items-center gap-0.5 bg-cyan-500/10 px-1 sm:px-2 py-0.5 sm:py-1 rounded border border-cyan-500/20" data-testid="cinepass-badge">
            <Ticket className="w-3 h-3 text-cyan-400" />
            <span className="text-cyan-400 font-bold text-[9px] sm:text-xs" data-testid="cinepass-balance">
              {user?.cinepass ?? 100}
            </span>
          </div>
          
          {/* Online Users */}
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

          {/* Lingua: Solo italiano */}

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
                  <p className="font-semibold text-sm">{user?.production_house_name || user?.nickname}</p>
                  <p className="text-xs text-gray-400">{user?.nickname}</p>
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
            className="absolute top-14 left-0 right-0 bg-[#0a0a0a] border-b border-white/10 shadow-2xl max-h-[80vh] overflow-y-auto pb-32"
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
                  <p className="font-semibold text-sm text-white">{user?.production_house_name || user?.nickname}</p>
                  <div className="flex items-center gap-2">
                    {levelInfo && (
                      <Badge className="bg-purple-500/20 text-purple-400 text-[10px] h-4">Lv.{levelInfo.level}</Badge>
                    )}
                    <span className="text-[10px] text-gray-400">{gameDate}</span>
                  </div>
                </div>
              </div>
              {/* Lingua: Solo italiano */}
            </div>
            
            {/* Admin Panel - Sticky banner (admin only) */}
            {(user?.nickname === 'NeoMorpheus' || user?.role === 'CO_ADMIN') && (
              <button
                onClick={() => { navigate('/admin'); setMobileMenuOpen(false); }}
                className="sticky top-0 z-10 w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-red-600 to-orange-600 text-white text-xs font-bold tracking-wide"
                data-testid="admin-panel-top-btn"
              >
                <Shield className="w-4 h-4" />
                {user?.role === 'CO_ADMIN' ? 'CO-ADMIN PANEL' : 'ADMIN PANEL'}
              </button>
            )}

            {/* Mobile Navigation Grid - Compact 50% */}
            <div className="grid grid-cols-3 gap-1.5 p-2 bg-[#0a0a0a]">
              {navItems.map(item => (
                <Button
                  key={item.path + item.label}
                  variant={location.pathname === item.path ? "default" : "ghost"}
                  size="sm"
                  className={`flex flex-col items-center gap-0.5 h-10 py-1 px-1 relative rounded-lg ${
                    item.frozen ? 'opacity-35 cursor-not-allowed bg-[#1a1a1a] border border-amber-500/10' :
                    item.disabled ? 'opacity-40 cursor-not-allowed' :
                    item.locked ? 'opacity-50 bg-[#1a1a1a] text-gray-500 border border-white/5' :
                    location.pathname === item.path 
                      ? 'bg-yellow-500 text-black hover:bg-yellow-400' 
                      : 'bg-[#1a1a1a] hover:bg-[#252525] text-gray-300 border border-white/5'
                  }`}
                  onClick={() => { 
                    if (item.disabled || item.frozen) return;
                    if (item.locked) { navigate('/infrastructure'); setMobileMenuOpen(false); return; }
                    navigate(item.path); setMobileMenuOpen(false); 
                  }}
                >
                  {item.locked && <Lock className="w-2 h-2 absolute top-0.5 right-0.5 text-gray-600" />}
                  {item.frozen && <span className="absolute -top-0.5 right-0 text-[5px] text-amber-400 font-bold bg-amber-500/15 px-1 rounded">SOSPESO</span>}
                  <item.icon className="w-3 h-3" />
                  <span className="text-[7px] font-medium truncate w-full text-center leading-tight">{item.pauseLabel || t(item.label)}</span>
                  {item.notificationCount > 0 && (
                    <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
                  )}
                </Button>
              ))}
            </div>
            
            {/* Velion Assistant Control */}
            <div className="px-4 py-2.5 border-t border-white/10 bg-[#111111]">
              <VelionMenuControl />
            </div>

            {/* Tutorial Button */}
            <div className="px-4 py-2 border-t border-white/10 bg-[#111111]">
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-yellow-400 hover:bg-yellow-500/10 gap-2"
                onClick={() => { setShowGameTutorial(true); setMobileMenuOpen(false); }}
                data-testid="menu-tutorial-btn"
              >
                <HelpCircle className="w-4 h-4" />
                <span className="text-sm">Tutorial</span>
              </Button>
              <div className="grid grid-cols-2 gap-1.5 mt-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start text-cyan-400 hover:bg-cyan-500/10 gap-1.5 h-8 text-xs"
                  onClick={() => { window.dispatchEvent(new Event('velion-tutorial-open')); setMobileMenuOpen(false); }}
                  data-testid="menu-velion-tutorial-btn"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Tutorial Velion</span>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start text-amber-400 hover:bg-amber-500/10 gap-1.5 h-8 text-xs"
                  onClick={() => { window.dispatchEvent(new Event('pipeline-tutorial-open')); setMobileMenuOpen(false); }}
                  data-testid="menu-pipeline-tutorial-btn"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Pipeline Film</span>
                </Button>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-yellow-400 hover:bg-yellow-500/10 gap-2 mt-1"
                onClick={() => { navigate('/event-history'); setMobileMenuOpen(false); }}
                data-testid="menu-event-history-btn"
              >
                <Sparkles className="w-4 h-4" />
                <span className="text-sm">Eventi</span>
              </Button>
            </div>

            {/* Mobile Quick Actions - Solid Dark */}
            <div className="flex items-center justify-around p-3 border-t border-white/10 bg-[#111111]">
              <Button 
                variant="ghost" 
                size="sm" 
                className="flex flex-col items-center gap-1 h-14 px-3 text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 rounded-xl"
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
              {donationsEnabled && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="flex flex-col items-center gap-1 h-14 px-4 text-pink-400 hover:text-pink-300 hover:bg-pink-500/10 rounded-xl"
                onClick={() => { setShowDonateDialog(true); setMobileMenuOpen(false); }}
                data-testid="menu-donate-btn"
              >
                <Heart className="w-5 h-5" />
                <span className="text-[10px] font-medium">Dona</span>
              </Button>
              )}
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

      {/* Donate Fixed Button - Above bottom nav - HIDDEN on chat page */}
      {donationsEnabled && location.pathname !== '/chat' && (
      <button
        className="fixed bottom-[58px] left-0 right-0 z-40 flex sm:hidden items-center justify-center gap-1.5 py-1.5 bg-pink-500/10 backdrop-blur-sm border-t border-pink-500/15 text-pink-400/70 hover:text-pink-300 hover:bg-pink-500/15 transition-all sidemenu-translate"
        onClick={() => setShowDonateDialog(true)}
        data-testid="fixed-donate-btn"
      >
        <Heart className="w-3 h-3" />
        <span className="text-[10px] font-medium tracking-wide">Supporta lo sviluppo</span>
      </button>
      )}

      {/* Films Menu Overlay */}
      <AnimatePresence>
        {showFilmsMenu && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/60 z-[55] sm:hidden" onClick={() => setShowFilmsMenu(false)} />
            <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 40 }} transition={{ type: 'spring', damping: 25, stiffness: 350 }} className="fixed bottom-[58px] left-2 right-2 z-[56] sm:hidden" data-testid="films-menu">
              <div className="bg-[#111113] border border-white/10 rounded-2xl p-3 shadow-2xl">
                <p className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold text-center mb-2">I Miei Contenuti</p>
                <div className="grid grid-cols-3 gap-2">
                  <button className={`flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all ${location.pathname === '/films' && !location.search ? 'bg-yellow-500 text-black' : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/25 hover:bg-yellow-500/20'}`}
                    onClick={() => { navigate('/films'); setShowFilmsMenu(false); }} data-testid="films-menu-film">
                    <Film className="w-5 h-5" />
                    <span className="text-[10px] font-bold">Film</span>
                  </button>
                  <button className={`flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all ${location.search?.includes('view=series') ? 'bg-blue-500 text-white' : 'bg-blue-500/10 text-blue-400 border border-blue-500/25 hover:bg-blue-500/20'}`}
                    onClick={() => { navigate('/films?view=series'); setShowFilmsMenu(false); }} data-testid="films-menu-series">
                    <Tv className="w-5 h-5" />
                    <span className="text-[10px] font-bold">Serie TV</span>
                  </button>
                  <button className={`flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all ${location.search?.includes('view=anime') ? 'bg-orange-500 text-white' : 'bg-orange-500/10 text-orange-400 border border-orange-500/25 hover:bg-orange-500/20'}`}
                    onClick={() => { navigate('/films?view=anime'); setShowFilmsMenu(false); }} data-testid="films-menu-anime">
                    <Sparkles className="w-5 h-5" />
                    <span className="text-[10px] font-bold">Anime</span>
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Production Menu Overlay */}
      <AnimatePresence>
        {showProductionMenu && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-[55] sm:hidden"
              onClick={() => setShowProductionMenu(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 40 }}
              transition={{ type: 'spring', damping: 25, stiffness: 350 }}
              className="fixed bottom-[58px] left-2 right-2 z-[56] sm:hidden"
              data-testid="production-menu"
            >
              <div className="bg-[#111113] border border-white/10 rounded-2xl p-3 shadow-2xl">
                <div className="flex items-center justify-between mb-2.5">
                  <p className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Produci</p>
                  {(() => {
                    const locked = [!productionUnlocks?.has_studio_serie_tv, !productionUnlocks?.has_studio_anime, !productionUnlocks?.has_emittente_tv].filter(Boolean).length;
                    return locked > 0 ? (
                      <span className="text-[9px] bg-yellow-500/15 text-yellow-400 px-2 py-0.5 rounded-full font-medium" data-testid="unlockable-count">
                        {locked} da sbloccare
                      </span>
                    ) : null;
                  })()}
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {/* Film - Always available */}
                  <button
                    className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl transition-all relative ${['/create-film'].includes(location.pathname) ? 'bg-yellow-500 text-black' : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/25 hover:bg-yellow-500/20'}`}
                    onClick={() => { navigate('/create-film'); setShowProductionMenu(false); }}
                    data-testid="prod-menu-film"
                  >
                    {productionUnlocks?.pipeline_counts?.film > 0 && <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[8px] font-bold flex items-center justify-center">{productionUnlocks.pipeline_counts.film}</span>}
                    <Camera className="w-5 h-5" />
                    <span className="text-[10px] font-bold leading-tight">Film</span>
                  </button>
                  {/* Sequel - Always available */}
                  <button
                    className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl transition-all ${location.pathname === '/create-sequel' ? 'bg-amber-600 text-white' : 'bg-amber-600/10 text-amber-500 border border-amber-600/25 hover:bg-amber-600/20'}`}
                    onClick={() => { navigate('/create-sequel'); setShowProductionMenu(false); }}
                    data-testid="prod-menu-sequel"
                  >
                    <Copy className="w-5 h-5" />
                    <span className="text-[10px] font-bold leading-tight">Sequel</span>
                  </button>
                  {/* Serie TV */}
                  <button
                    className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl transition-all relative ${
                      productionUnlocks?.has_studio_serie_tv 
                        ? (location.pathname === '/create-series' ? 'bg-blue-500 text-white' : 'bg-blue-500/10 text-blue-400 border border-blue-500/25 hover:bg-blue-500/20')
                        : 'bg-white/[0.03] text-gray-600 border border-white/5 cursor-not-allowed'
                    }`}
                    onClick={() => {
                      if (productionUnlocks?.has_studio_serie_tv) { navigate('/create-series'); setShowProductionMenu(false); }
                      else { navigate('/infrastructure'); setShowProductionMenu(false); }
                    }}
                    data-testid="prod-menu-series"
                  >
                    {!productionUnlocks?.has_studio_serie_tv && <Lock className="w-3 h-3 absolute top-1 right-1 text-gray-600" />}
                    {productionUnlocks?.has_studio_serie_tv && productionUnlocks?.pipeline_counts?.series > 0 && <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[8px] font-bold flex items-center justify-center">{productionUnlocks.pipeline_counts.series}</span>}
                    <Tv className="w-5 h-5" />
                    <span className="text-[10px] font-bold leading-tight">Serie TV</span>
                  </button>
                  {/* Anime */}
                  <button
                    className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl transition-all relative ${
                      productionUnlocks?.has_studio_anime
                        ? (location.pathname === '/create-anime' ? 'bg-orange-500 text-white' : 'bg-orange-500/10 text-orange-400 border border-orange-500/25 hover:bg-orange-500/20')
                        : 'bg-white/[0.03] text-gray-600 border border-white/5 cursor-not-allowed'
                    }`}
                    onClick={() => {
                      if (productionUnlocks?.has_studio_anime) { navigate('/create-anime'); setShowProductionMenu(false); }
                      else { navigate('/infrastructure'); setShowProductionMenu(false); }
                    }}
                    data-testid="prod-menu-anime"
                  >
                    {!productionUnlocks?.has_studio_anime && <Lock className="w-3 h-3 absolute top-1 right-1 text-gray-600" />}
                    {productionUnlocks?.has_studio_anime && productionUnlocks?.pipeline_counts?.anime > 0 && <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[8px] font-bold flex items-center justify-center">{productionUnlocks.pipeline_counts.anime}</span>}
                    <Sparkles className="w-5 h-5" />
                    <span className="text-[10px] font-bold leading-tight">Anime</span>
                  </button>
                  {/* La Tua TV */}
                  <button
                    className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl transition-all relative ${
                      productionUnlocks?.has_emittente_tv
                        ? (location.pathname === '/my-tv' ? 'bg-emerald-500 text-white' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 hover:bg-emerald-500/20')
                        : 'bg-white/[0.03] text-gray-600 border border-white/5 cursor-not-allowed'
                    }`}
                    onClick={() => {
                      if (productionUnlocks?.has_emittente_tv) { navigate('/my-tv'); setShowProductionMenu(false); }
                      else { navigate('/infrastructure'); setShowProductionMenu(false); }
                    }}
                    data-testid="prod-menu-tv"
                  >
                    {!productionUnlocks?.has_emittente_tv && <Lock className="w-3 h-3 absolute top-1 right-1 text-gray-600" />}
                    <Radio className="w-5 h-5" />
                    <span className="text-[10px] font-bold leading-tight">La Tua TV</span>
                  </button>
                  {/* Empty cell for alignment */}
                  <div></div>
                  {/* Casting Agency */}
                  <button
                    className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl transition-all relative ${
                      productionUnlocks?.has_production_studio
                        ? (location.pathname === '/casting-agency' ? 'bg-purple-500 text-white' : 'bg-purple-500/10 text-purple-400 border border-purple-500/25 hover:bg-purple-500/20')
                        : 'bg-white/[0.03] text-gray-600 border border-white/5 cursor-not-allowed'
                    }`}
                    onClick={() => {
                      if (productionUnlocks?.has_production_studio) { navigate('/casting-agency'); setShowProductionMenu(false); }
                      else { navigate('/infrastructure'); setShowProductionMenu(false); }
                    }}
                    data-testid="prod-menu-casting-agency"
                  >
                    {!productionUnlocks?.has_production_studio && <Lock className="w-3 h-3 absolute top-1 right-1 text-gray-600" />}
                    <UserCheck className="w-5 h-5" />
                    <span className="text-[10px] font-bold leading-tight">Agenzia</span>
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Mobile Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-[#0F0F10]/95 backdrop-blur-md border-t border-white/10 z-50 flex sm:hidden items-center justify-around px-0 sidemenu-translate" style={{ height: 'calc(3.5rem + env(safe-area-inset-bottom, 0px))', paddingBottom: 'env(safe-area-inset-bottom, 0px)' }} data-testid="mobile-bottom-nav">
        <button className={`flex flex-col items-center gap-0.5 px-1 py-1 rounded-lg min-w-0 ${location.pathname === '/dashboard' ? 'text-yellow-400' : 'text-gray-500'}`} onClick={() => navigate('/dashboard')} onMouseEnter={() => handleNavHover('/dashboard')} onTouchStart={() => handleNavHover('/dashboard')} data-testid="bottom-nav-home">
          <Clapperboard className="w-4 h-4" />
          <span className="text-[8px]">Home</span>
        </button>
        <button className={`flex flex-col items-center gap-0.5 px-1 py-1 rounded-lg min-w-0 ${location.pathname === '/films' ? 'text-yellow-400' : showFilmsMenu ? 'text-yellow-400' : 'text-gray-500'}`} onClick={() => setShowFilmsMenu(!showFilmsMenu)} onMouseEnter={() => handleNavHover('/my-films')} onTouchStart={() => handleNavHover('/my-films')} data-testid="bottom-nav-films">
          <Film className="w-4 h-4" />
          <span className="text-[8px]">I Miei</span>
        </button>
        {/* PRODUCI! - Opens production menu */}
        <button 
          className={`flex flex-col items-center justify-center gap-0.5 px-3 py-1.5 rounded-xl min-w-0 transition-all ${showProductionMenu ? 'bg-yellow-500 text-black' : ['/create-film','/create-series','/create-anime','/my-tv'].includes(location.pathname) ? 'bg-yellow-500 text-black' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40'}`}
          onClick={() => setShowProductionMenu(!showProductionMenu)}
          data-testid="bottom-nav-produci"
          style={{ minWidth: '72px' }}
        >
          {showProductionMenu ? <X className="w-5 h-5" /> : <Camera className="w-5 h-5" />}
          <span className="text-[9px] font-bold">Produci!</span>
        </button>
        <button className={`flex flex-col items-center gap-0.5 px-1 py-1 rounded-lg min-w-0 ${location.pathname === '/marketplace' ? 'text-yellow-400' : 'text-gray-500'}`} onClick={() => navigate('/marketplace')} onMouseEnter={() => handleNavHover('/marketplace')} data-testid="bottom-nav-mercato">
          <Store className="w-4 h-4" />
          <span className="text-[8px]">Mercato</span>
        </button>
        <button className={`flex flex-col items-center gap-0.5 px-1 py-1 rounded-lg min-w-0 ${location.pathname === '/infrastructure' ? 'text-yellow-400' : 'text-gray-500'}`} onClick={() => navigate('/infrastructure')} data-testid="bottom-nav-infra">
          <Building className="w-4 h-4" />
          <span className="text-[8px]">Infra</span>
        </button>
        <button className={`flex flex-col items-center gap-0.5 px-1 py-1 rounded-lg min-w-0 ${location.pathname === '/pvp-arena' ? 'text-red-400' : 'text-gray-500'}`} onClick={() => navigate('/pvp-arena')} onMouseEnter={() => handleNavHover('/pvp-arena')} data-testid="bottom-nav-arena">
          <Disc className="w-4 h-4" />
          <span className="text-[8px]">Arena</span>
        </button>
        <button className={`relative flex flex-col items-center gap-0.5 px-1 py-1 rounded-lg min-w-0 ${location.pathname === '/notifications' ? 'text-yellow-400' : 'text-gray-500'}`} onClick={() => navigate('/notifications')} data-testid="bottom-nav-notifiche">
          <Bell className="w-4 h-4" />
          {notificationCount > 0 && <span className="absolute top-0 right-0 min-w-[12px] h-3 px-0.5 bg-red-500 text-white text-[7px] font-bold rounded-full flex items-center justify-center">{notificationCount > 9 ? '9+' : notificationCount}</span>}
          <span className="text-[8px]">Eventi</span>
        </button>
      </div>

      {/* Notification Popup Toasts - Slide from top with vibration */}
      <AnimatePresence>
        {popupNotifications.map((notif, i) => {
          const severityStyles = {
            critical: 'border-red-500/40 bg-gradient-to-r from-red-950/95 to-red-900/80',
            important: 'border-yellow-500/40 bg-gradient-to-r from-yellow-950/95 to-yellow-900/80',
            positive: 'border-green-500/40 bg-gradient-to-r from-green-950/95 to-green-900/80',
          };
          const severityIcons = {
            critical: <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />,
            important: <Clock className="w-5 h-5 text-yellow-400 flex-shrink-0" />,
            positive: <Sparkles className="w-5 h-5 text-green-400 flex-shrink-0" />,
          };
          const glowColor = {
            critical: '0 0 20px rgba(239,68,68,0.15)',
            important: '0 0 20px rgba(234,179,8,0.15)',
            positive: '0 0 20px rgba(34,197,94,0.15)',
          };
          const sev = notif.severity || 'positive';
          // Trigger vibration on mount
          if (i === 0 && typeof navigator !== 'undefined' && navigator.vibrate) {
            try { navigator.vibrate(sev === 'critical' ? [50, 50, 50] : [25]); } catch {}
          }
          return (
            <motion.div
              key={notif.id}
              initial={{ opacity: 0, y: -80, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -60, scale: 0.9 }}
              transition={{ type: 'spring', damping: 22, stiffness: 350, delay: i * 0.12 }}
              className={`fixed z-[100] left-3 right-3 sm:left-auto sm:right-3 sm:max-w-sm cursor-pointer backdrop-blur-lg border rounded-xl p-3 shadow-2xl ${severityStyles[sev] || severityStyles.positive}`}
              style={{ top: `${64 + i * 76}px`, boxShadow: glowColor[sev] || glowColor.positive }}
              onClick={() => {
                setPopupNotifications(prev => prev.filter(p => p.id !== notif.id));
                api.post(`/notifications/${notif.id}/read`).catch(() => {});
                const navPath = notif.link;
                if (navPath) { navigate(navPath); } else { navigate('/notifications'); }
              }}
              data-testid={`popup-notification-${notif.id}`}
            >
              <div className="flex items-start gap-2.5">
                <div className={`p-1.5 rounded-lg ${sev === 'critical' ? 'bg-red-500/20' : sev === 'important' ? 'bg-yellow-500/20' : 'bg-green-500/20'}`}>
                  {severityIcons[sev] || severityIcons.positive}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-xs text-white leading-tight">{notif.title}</p>
                  <p className="text-[10px] text-gray-300/80 mt-0.5 leading-snug line-clamp-2">{notif.message}</p>
                </div>
                <button
                  className="text-gray-600 hover:text-white p-0.5 flex-shrink-0 transition-colors"
                  onClick={(e) => { e.stopPropagation(); setPopupNotifications(prev => prev.filter(p => p.id !== notif.id)); }}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>

      {/* Online Users Panel */}
      <Dialog open={showOnlineUsersPanel} onOpenChange={(open) => { setShowOnlineUsersPanel(open); if(!open) { setSelectedUserProfile(null); setSelectedOnlineUser(null); setProfileGenreFilter(null); } }}>
        <DialogContent className="max-w-md max-h-[85vh] overflow-hidden bg-[#111] border-green-500/30 p-0">
          {/* If viewing a user's profile */}
          {selectedUserProfile ? (
            <div className="flex flex-col h-[80vh]">
              {/* Sticky header with back + friend request + challenge */}
              <div className="sticky top-0 z-10 bg-[#111] border-b border-white/10 p-3 flex items-center gap-2">
                <Button size="sm" variant="ghost" onClick={() => { setSelectedUserProfile(null); setSelectedOnlineUser(null); setProfileGenreFilter(null); }} className="h-7 w-7 p-0 text-gray-400">
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
                      onClick={() => { setShowOnlineUsersPanel(false); setSelectedUserProfile(null); navigate('/minigiochi'); }}
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
                          <Badge 
                            key={genre} 
                            className={`text-[10px] cursor-pointer transition-colors ${profileGenreFilter === genre ? 'bg-yellow-500/30 text-yellow-300 border border-yellow-500/50' : 'bg-white/10 text-gray-300 hover:bg-white/20'}`}
                            onClick={() => setProfileGenreFilter(profileGenreFilter === genre ? null : genre)}
                            data-testid={`profile-genre-${genre}`}
                          >
                            {genre}: {count}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Filtered films by genre */}
                  {profileGenreFilter && selectedUserProfile.recent_films?.length > 0 && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs text-gray-400 font-semibold">{language === 'it' ? `Film ${profileGenreFilter}` : `${profileGenreFilter} Films`}</p>
                        <button className="text-[10px] text-yellow-400 hover:underline" onClick={() => setProfileGenreFilter(null)}>
                          {language === 'it' ? 'Mostra tutti' : 'Show all'}
                        </button>
                      </div>
                      <div className="space-y-2">
                        {selectedUserProfile.recent_films.filter(f => f.genre?.toLowerCase() === profileGenreFilter.toLowerCase()).map(film => (
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
                        {selectedUserProfile.recent_films.filter(f => f.genre?.toLowerCase() === profileGenreFilter.toLowerCase()).length === 0 && (
                          <p className="text-[10px] text-gray-500 text-center py-2">{language === 'it' ? 'Nessun film in questa categoria' : 'No films in this category'}</p>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Recent films - only show when no genre filter */}
                  {!profileGenreFilter && selectedUserProfile.recent_films?.length > 0 && (
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
                      <span className="text-[9px] text-gray-500 whitespace-nowrap">{timeAgo(p.last_active) || 'Offline'}</span>
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
      <Dialog open={!!popupData} onOpenChange={(open) => { if(!open) { setPopupData(null); setPopupView('stats'); setPopupGenreFilter(null); } }}>
        <DialogContent className="max-w-lg max-h-[85vh] overflow-hidden bg-[#111] border-cyan-500/30 p-0">
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
              <div className="sticky top-[52px] z-10 bg-[#111]/95 backdrop-blur-md border-b border-white/10 p-2 flex gap-1.5 justify-center flex-wrap">
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
                  onClick={() => { setPopupData(null); setPopupView('stats'); navigate('/minigiochi'); }}
                  data-testid="global-challenge-btn"
                >
                  <Swords className="w-3 h-3 mr-1" /> {language === 'it' ? 'Sfida 1v1' : '1v1 Challenge'}
                </Button>
                <Button 
                  size="sm" variant="outline"
                  className="border-white/10 text-gray-300 h-7 px-3 text-[10px]"
                  onClick={() => { setPopupData(null); setPopupView('stats'); navigate('/chat'); }}
                  data-testid="global-message-btn"
                >
                  <MessageSquare className="w-3 h-3 mr-1" /> {language === 'it' ? 'Messaggio' : 'Message'}
                </Button>
                <Button 
                  size="sm"
                  className={`h-7 px-3 text-[10px] font-bold ${popupView === 'studio' ? 'bg-yellow-500 text-black' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'}`}
                  onClick={() => setPopupView(popupView === 'studio' ? 'stats' : 'studio')}
                  data-testid="global-visit-studio-btn"
                >
                  <Building className="w-3 h-3 mr-1" /> {language === 'it' ? 'Visita Studio' : 'Visit Studio'}
                </Button>
              </div>
              
              {/* Profile content */}
              <ScrollArea className="flex-1">
                {popupView === 'stats' ? (
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
                          <div key={film.id} className="flex items-center gap-2 bg-white/5 rounded-lg p-2 cursor-pointer hover:bg-white/10" onClick={() => { setPopupData(null); setPopupView('stats'); navigate(`/films/${film.id}`); }}>
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
                ) : (
                <div className="p-4 space-y-4">
                  {/* STUDIO VIEW - Dashboard style */}
                  {/* Financial Overview */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-green-500/10 rounded-lg p-2 text-center border border-green-500/20">
                      <p className="text-lg font-bold text-green-400">${((popupData.profile.stats?.total_revenue || 0)/1000000).toFixed(1)}M</p>
                      <p className="text-[9px] text-gray-400">{language === 'it' ? 'Box Office' : 'Box Office'}</p>
                    </div>
                    <div className="bg-blue-500/10 rounded-lg p-2 text-center border border-blue-500/20">
                      <p className="text-lg font-bold text-blue-400">{popupData.profile.stats?.total_films || 0}</p>
                      <p className="text-[9px] text-gray-400">{language === 'it' ? 'Film Prodotti' : 'Films Made'}</p>
                    </div>
                    <div className="bg-yellow-500/10 rounded-lg p-2 text-center border border-yellow-500/20">
                      <p className="text-lg font-bold text-yellow-400">{popupData.profile.stats?.avg_quality || 0}%</p>
                      <p className="text-[9px] text-gray-400">{language === 'it' ? 'Qualità Media' : 'Avg Quality'}</p>
                    </div>
                  </div>
                  
                  {/* Genre breakdown */}
                  {popupData.profile.genre_breakdown && Object.keys(popupData.profile.genre_breakdown).length > 0 && (
                    <div>
                      <p className="text-xs text-gray-400 mb-2 font-semibold">{language === 'it' ? 'Generi Prodotti' : 'Genres'}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {Object.entries(popupData.profile.genre_breakdown).map(([genre, count]) => (
                          <Badge 
                            key={genre} 
                            className={`text-[10px] cursor-pointer transition-colors ${popupGenreFilter === genre ? 'bg-yellow-500/30 text-yellow-300 border border-yellow-500/50' : 'bg-purple-500/20 text-purple-300 hover:bg-purple-500/30'}`}
                            onClick={() => setPopupGenreFilter(popupGenreFilter === genre ? null : genre)}
                            data-testid={`popup-genre-${genre}`}
                          >
                            {genre}: {count}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Filtered films by genre */}
                  {popupGenreFilter && popupData.profile.all_films?.length > 0 && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs text-gray-400 font-semibold">{language === 'it' ? `Film ${popupGenreFilter}` : `${popupGenreFilter} Films`}</p>
                        <button className="text-[10px] text-yellow-400 hover:underline" onClick={() => setPopupGenreFilter(null)}>
                          {language === 'it' ? 'Mostra tutti' : 'Show all'}
                        </button>
                      </div>
                      <div className="space-y-1.5">
                        {popupData.profile.all_films.filter(f => f.genre?.toLowerCase() === popupGenreFilter.toLowerCase()).map(film => (
                          <div key={film.id} className="flex items-center gap-2 bg-white/5 rounded-lg p-2 cursor-pointer hover:bg-white/10" onClick={() => { setPopupData(null); setPopupView('stats'); navigate(`/films/${film.id}`); }}>
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
                        {popupData.profile.all_films.filter(f => f.genre?.toLowerCase() === popupGenreFilter.toLowerCase()).length === 0 && (
                          <p className="text-[10px] text-gray-500 text-center py-2">{language === 'it' ? 'Nessun film in questa categoria' : 'No films in this category'}</p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Best film */}
                  {popupData.profile.best_film && (
                    <div>
                      <p className="text-xs text-gray-400 mb-2 font-semibold">{language === 'it' ? 'Miglior Film' : 'Best Film'}</p>
                      <div className="flex items-center gap-3 bg-yellow-500/10 rounded-lg p-2 border border-yellow-500/20 cursor-pointer hover:bg-yellow-500/15" onClick={() => { setPopupData(null); setPopupView('stats'); navigate(`/films/${popupData.profile.best_film.id}`); }}>
                        {popupData.profile.best_film.poster_url ? (
                          <img src={popupData.profile.best_film.poster_url} alt="" className="w-10 h-14 rounded object-cover" />
                        ) : (
                          <div className="w-10 h-14 rounded bg-gray-700 flex items-center justify-center"><Crown className="w-4 h-4 text-yellow-500" /></div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-bold truncate">{popupData.profile.best_film.title}</p>
                          <p className="text-[10px] text-gray-400">{popupData.profile.best_film.genre}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-green-400 text-sm font-bold">${((popupData.profile.best_film.revenue || popupData.profile.best_film.total_revenue || 0)/1000000).toFixed(1)}M</p>
                          <p className="text-[9px] text-gray-400">Q:{popupData.profile.best_film.quality_score?.toFixed(0)}</p>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* All Films Grid */}
                  {popupData.profile.all_films?.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-400 mb-2 font-semibold">{language === 'it' ? 'Tutti i Film' : 'All Films'} ({popupData.profile.all_films.length})</p>
                      <div className="grid grid-cols-4 sm:grid-cols-5 gap-1.5">
                        {popupData.profile.all_films.map(film => (
                          <div key={film.id} className="cursor-pointer hover:opacity-80 transition-opacity" onClick={() => { setPopupData(null); setPopupView('stats'); navigate(`/films/${film.id}`); }}>
                            <div className="aspect-[2/3] rounded overflow-hidden bg-gray-800">
                              {film.poster_url ? (
                                <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover" loading="lazy" />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center"><Film className="w-4 h-4 text-gray-600" /></div>
                              )}
                            </div>
                            <p className="text-[8px] font-semibold truncate mt-0.5">{film.title}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Awards */}
                  {popupData.profile.awards?.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-400 mb-2 font-semibold">{language === 'it' ? 'Premi Vinti' : 'Awards Won'} ({popupData.profile.awards.length})</p>
                      <div className="space-y-1">
                        {popupData.profile.awards.slice(0, 5).map((award, i) => (
                          <div key={i} className="flex items-center gap-2 bg-amber-500/10 rounded p-1.5 border border-amber-500/20">
                            <Award className="w-3 h-3 text-amber-400 shrink-0" />
                            <p className="text-[10px] truncate">{award.award_name || award.name || 'Award'}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                )}
              </ScrollArea>
            </div>
          ) : (
            <div className="p-8 flex items-center justify-center">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Donate Dialog */}
      <Dialog open={showDonateDialog} onOpenChange={setShowDonateDialog}>
        <DialogContent className="max-w-sm bg-[#111] border-pink-500/30 p-0 overflow-hidden">
          <div className="bg-gradient-to-b from-pink-500/20 to-transparent p-6 text-center">
            <Heart className="w-12 h-12 text-pink-400 mx-auto mb-3" />
            <DialogTitle className="font-['Bebas_Neue'] text-2xl text-pink-300 mb-1">Supporta CineWorld</DialogTitle>
            <p className="text-xs text-gray-400 leading-relaxed">
              Il tuo contributo ci aiuta a sviluppare nuove funzionalità e migliorare il gioco. Ogni donazione conta!
            </p>
          </div>
          <div className="px-6 pb-6 space-y-3">
            <a
              href="https://www.paypal.me/UnNickk"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-[#0070ba] hover:bg-[#005ea6] text-white font-semibold text-sm transition-colors"
              data-testid="donate-paypal-btn"
              onClick={() => setShowDonateDialog(false)}
            >
              <DollarSign className="w-4 h-4" />
              Dona con PayPal
            </a>
            <p className="text-[10px] text-gray-500 text-center leading-relaxed">
              Donazione libera - scegli tu l'importo. Verrai reindirizzato su PayPal per completare la donazione in sicurezza.
            </p>
            <button
              className="w-full text-center text-[10px] text-gray-600 hover:text-gray-400 py-1 transition-colors"
              onClick={() => setShowDonateDialog(false)}
            >
              Magari un'altra volta
            </button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Guest Conversion Modal */}
      <Dialog open={showGuestConvertModal} onOpenChange={setShowGuestConvertModal}>
        <DialogContent className="max-w-[340px] bg-[#0c0c0e] border-yellow-500/20 p-0 overflow-hidden rounded-2xl" data-testid="guest-convert-modal">
          <GuestConvertModalContent
            user={user}
            api={api}
            form={guestConvertForm}
            setForm={setGuestConvertForm}
            converting={guestConverting}
            setConverting={setGuestConverting}
            onSuccess={() => { refreshUser(); setShowGuestConvertModal(false); }}
            onDismiss={() => setShowGuestConvertModal(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Guest Registration Button - always visible for guest users */}
      {user?.is_guest && (
        <GuestRegisterBadge onRegister={() => setShowGuestConvertModal(true)} />
      )}

      {showDonatePopup && (
        <div className="fixed inset-0 z-[150] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowDonatePopup(false)}>
          <div 
            className="relative bg-[#111] border border-yellow-500/30 rounded-2xl max-w-sm w-[90%] mx-4 overflow-hidden shadow-2xl shadow-yellow-500/10"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close X */}
            <button
              className="absolute top-3 right-3 z-10 w-8 h-8 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-gray-400 hover:text-white transition-colors"
              onClick={() => setShowDonatePopup(false)}
              data-testid="donate-popup-close"
            >
              <X className="w-4 h-4" />
            </button>
            
            {/* Content */}
            <div className="p-6 pt-8 text-center">
              <Heart className="w-14 h-14 text-pink-400 mx-auto mb-4" />
              <h2 className="font-['Bebas_Neue'] text-2xl text-white mb-3 leading-tight">
                Aiutaci a far crescere<br/>
                <span className="text-yellow-400">il NOSTRO gioco</span>
              </h2>
              <p className="text-sm text-gray-400 leading-relaxed mb-6">
                CineWorld esiste grazie a voi. Con il tuo supporto possiamo continuare a sviluppare nuove funzionalità e rendere il gioco sempre migliore per tutti.
              </p>
              
              {/* Donate button */}
              <a
                href="https://www.paypal.me/UnNickk"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 w-full py-3.5 rounded-xl bg-yellow-500 hover:bg-yellow-400 text-black font-bold text-base transition-colors"
                data-testid="donate-popup-btn"
                onClick={() => setShowDonatePopup(false)}
              >
                <Heart className="w-5 h-5" />
                Dona Ora
              </a>
            </div>
          </div>
        </div>
      )}

      {showGameTutorial && <TutorialModal onClose={() => setShowGameTutorial(false)} />}

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
  const [pendingChallengePopup, setPendingChallengePopup] = useState(null);
  const [productionMenuOpen, setProductionMenuOpen] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);
  const [velionTab, setVelionTab] = useState('tutorial');
  const [velionMode, setVelionMode] = useState('on');
  const [showAutonomy, setShowAutonomy] = useState(false);
  const [showGameTutorial, setShowGameTutorial] = useState(false);
  const [showDashboardTour, setShowDashboardTour] = useState(false);
  
  // Fetch Velion mode from backend
  const [tutorialCompleted, setTutorialCompleted] = useState(true);
  useEffect(() => {
    if (!user || !api) return;
    api.get('/velion/mode').then(r => {
      const m = r.data?.mode || 'on';
      setVelionMode(m);
      window.__velionMode = m;
      if (r.data?.show_autonomy) setShowAutonomy(true);
      const tc = r.data?.tutorial_completed || false;
      setTutorialCompleted(tc);
      if (tc) localStorage.setItem('velion_tutorial_done', 'true');
    }).catch(() => {});
  }, [user, api]);

  const toggleVelionMode = async (newMode) => {
    setVelionMode(newMode);
    window.__velionMode = newMode;
    window.dispatchEvent(new Event('velion-mode-changed'));
    try { await api.put('/velion/mode', { mode: newMode }); } catch {}
  };

  // Listen for toggle from hamburger menu
  useEffect(() => {
    const handler = () => {
      const next = velionMode === 'on' ? 'off' : 'on';
      toggleVelionMode(next);
    };
    window.addEventListener('velion-toggle-mode', handler);
    return () => window.removeEventListener('velion-toggle-mode', handler);
  });

  const dismissAutonomy = async (keepOn) => {
    setShowAutonomy(false);
    try { await api.post('/velion/dismiss-autonomy'); } catch {}
    if (!keepOn) toggleVelionMode('off');
  };

  // Auto-show tutorial for new users (only when ON, skip for guest users with tutorial active)
  useEffect(() => {
    if (user?.is_guest && !user?.tutorial_completed) return; // Guest tutorial handles this
    if (user && velionMode === 'on' && shouldAutoShowTutorial(tutorialCompleted)) {
      const timer = setTimeout(() => { setVelionTab('tutorial'); setShowTutorial(true); }, 1500);
      return () => clearTimeout(timer);
    }
  }, [user, velionMode, tutorialCompleted]);

  // Listen for tutorial open event from hamburger menu
  useEffect(() => {
    const handler = () => { setVelionTab('tutorial'); setShowTutorial(true); };
    window.addEventListener('velion-tutorial-open', handler);
    return () => window.removeEventListener('velion-tutorial-open', handler);
  }, []);

  // Dashboard Tour: show automatically after first registration
  useEffect(() => {
    if (!user || user.is_guest) return;
    const flag = localStorage.getItem('show_dashboard_tour');
    const done = localStorage.getItem('dashboard_tour_done');
    if (flag === '1' && done !== '1') {
      const timer = setTimeout(() => {
        localStorage.removeItem('show_dashboard_tour');
        setShowDashboardTour(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [user]);
  
  // Check for pending challenge invites - on login + every 30s
  useEffect(() => {
    if (!user || !api) return;
    const checkChallengeInvites = () => {
      api.get('/notifications?limit=20').then(r => {
        const notifs = r.data?.notifications || r.data || [];
        const pending = notifs.find(n => 
          n.type === 'challenge_invite' && !n.read && n.data?.is_popup
        );
        if (pending && !pendingChallengePopup) setPendingChallengePopup(pending);
      }).catch(() => {});
    };
    checkChallengeInvites();
    const interval = setInterval(checkChallengeInvites, 30000);
    return () => clearInterval(interval);
  }, [user, api]);
  
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
    <ProductionMenuContext.Provider value={{ isOpen: productionMenuOpen, setIsOpen: setProductionMenuOpen }}>
    <PlayerPopupContext.Provider value={{ openPlayerPopup, popupData, setPopupData }}>
      <TopNavbar />
      <LoginRewardPopup />
      <AutoTickNotifications api={api} />
      <div style={{ paddingTop: 'env(safe-area-inset-top, 0px)' }}>
      <AnimatePresence>
        <PageTransition key={location.pathname}>
          <ErrorBoundary>
          <React.Suspense fallback={<LoadingSpinner />}>
            {children}
          </React.Suspense>
          </ErrorBoundary>
        </PageTransition>
      </AnimatePresence>
      </div>

      {/* Challenge Invite Popup */}
      {pendingChallengePopup && (
        <Dialog open={!!pendingChallengePopup} onOpenChange={(o) => { if(!o) setPendingChallengePopup(null); }}>
          <DialogContent className="bg-[#1A1A1A] border-pink-500/30 max-w-sm">
            <DialogHeader>
              <DialogTitle className="font-['Bebas_Neue'] text-2xl text-pink-400 flex items-center gap-2">
                <Swords className="w-6 h-6" /> Sfida 1v1 Ricevuta!
              </DialogTitle>
              <DialogDescription className="text-gray-300 text-sm">
                {pendingChallengePopup.message}
              </DialogDescription>
            </DialogHeader>
            <div className="flex gap-2 mt-2">
              <div className="flex-1 text-center p-3 bg-yellow-500/10 rounded-lg">
                <p className="text-xs text-gray-400">Costo</p>
                <p className="text-lg font-bold text-yellow-400">${(pendingChallengePopup.data?.participation_cost || 50000).toLocaleString()}</p>
              </div>
              <div className="flex-1 text-center p-3 bg-green-500/10 rounded-lg">
                <p className="text-xs text-gray-400">Premio</p>
                <p className="text-lg font-bold text-green-400">${(pendingChallengePopup.data?.prize_pool || 100000).toLocaleString()}</p>
              </div>
            </div>
            <DialogFooter className="flex gap-2 mt-3">
              <Button variant="outline" className="flex-1 border-gray-500" onClick={() => {
                api.post(`/notifications/${pendingChallengePopup.id}/read`).catch(() => {});
                setPendingChallengePopup(null);
              }} data-testid="decline-challenge-btn">
                Rifiuta
              </Button>
              <Button className="flex-1 bg-pink-500 hover:bg-pink-600" onClick={() => {
                api.post(`/notifications/${pendingChallengePopup.id}/read`).catch(() => {});
                setPendingChallengePopup(null);
                navigate(`/challenges?accept=${pendingChallengePopup.data?.challenge_id}`);
              }} data-testid="accept-challenge-btn">
                <Swords className="w-4 h-4 mr-1" /> Accetta Sfida!
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Guest Tutorial Guide */}
      <GuestTutorial />

      {/* Velion AI Assistant - hidden on chat page on mobile AND during guest tutorial */}
      {location.pathname !== '/chat' && !(user?.is_guest && !user?.tutorial_completed) && (
      <>
      <VelionOverlay
        onClick={() => { setVelionTab('chat'); setShowTutorial(true); }}
        onBubbleClick={(action) => { navigate(action); }}
        onHelpClick={() => setShowGameTutorial(true)}
        mode={velionMode}
      />
      </>
      )}
      <VelionPanel
        open={showTutorial}
        onClose={() => setShowTutorial(false)}
        onNavigate={(path) => { navigate(path); setShowTutorial(false); }}
        defaultTab={velionTab}
      />
      {showGameTutorial && <TutorialModal onClose={() => setShowGameTutorial(false)} />}
      {showDashboardTour && <DashboardTour onClose={() => setShowDashboardTour(false)} />}

      {/* Autonomy Prompt */}
      <AnimatePresence>
        {showAutonomy && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[90] w-[90%] max-w-sm"
            data-testid="velion-autonomy-prompt"
          >
            <div className="bg-[#0d0d10]/95 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-4 shadow-lg shadow-cyan-500/5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded-full relative flex-shrink-0">
                  <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, transparent 100%)' }} />
                  <img src="/velion.png" alt="" className="w-full h-full object-contain rounded-full relative z-10" style={{ mixBlendMode: 'screen', filter: 'brightness(1.4) contrast(1.3)' }} />
                </div>
                <span className="text-[10px] text-cyan-400 font-['Bebas_Neue'] tracking-widest">VELION</span>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed mb-3">
                Ti senti pronto a gestire il tuo studio in autonomia?
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => dismissAutonomy(true)}
                  className="flex-1 py-2 rounded-lg bg-cyan-500/15 text-cyan-400 text-xs font-medium border border-cyan-500/30 hover:bg-cyan-500/25 transition-colors"
                  data-testid="autonomy-keep-on"
                >
                  Continua con Velion
                </button>
                <button
                  onClick={() => dismissAutonomy(false)}
                  className="flex-1 py-2 rounded-lg bg-white/5 text-gray-400 text-xs font-medium border border-white/10 hover:bg-white/10 transition-colors"
                  data-testid="autonomy-go-off"
                >
                  Prova senza
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </PlayerPopupContext.Provider>
    </ProductionMenuContext.Provider>
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
    <div className="min-h-screen bg-[#0F0F10] relative">
      {/* Fixed blurred background */}
      <div className="fixed inset-0 z-0" style={{ backgroundImage: 'url(/cineworld-bg.jpg)', backgroundSize: 'cover', backgroundPosition: 'center', filter: 'blur(8px) brightness(0.15)', transform: 'scale(1.05)' }} />
      <div className="relative z-10">
      <BrowserRouter>
        <AuthProvider>
          <GameStoreProvider>
          <LanguageProvider>
            <ConfirmProvider>
            <NotificationProvider>
            <UrlManager>
              <Toaster position="top-center" theme="dark" toastOptions={{ style: { marginTop: 'calc(3.5rem + env(safe-area-inset-top, 0px))' } }} />
              <Routes>
                <Route path="/auth" element={<AuthPage />} />
                <Route path="/recovery/password" element={<PasswordRecoveryPage />} />
                <Route path="/recovery/nickname" element={<NicknameRecoveryPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/films" element={<ProtectedRoute><MyFilms /></ProtectedRoute>} />
                <Route path="/films/:id" element={<ProtectedRoute><FilmDetail /></ProtectedRoute>} />
                <Route path="/series/:id" element={<ProtectedRoute><SeriesDetail /></ProtectedRoute>} />
                <Route path="/create" element={<ProtectedRoute><PipelineV2 /></ProtectedRoute>} />
                <Route path="/create-film" element={<ProtectedRoute><PipelineV2 /></ProtectedRoute>} />
                <Route path="/pipeline-v2" element={<ProtectedRoute><PipelineV2 /></ProtectedRoute>} />
                <Route path="/create-legacy" element={<ProtectedRoute><FilmPipeline /></ProtectedRoute>} />
                <Route path="/create-series" element={<ProtectedRoute><SeriesTVPipeline /></ProtectedRoute>} />
                <Route path="/create-anime" element={<ProtectedRoute><AnimePipeline /></ProtectedRoute>} />
                <Route path="/create-sequel" element={<ProtectedRoute><SequelPipeline /></ProtectedRoute>} />
                <Route path="/my-tv" element={<ProtectedRoute><EmittenteTVPage /></ProtectedRoute>} />
                <Route path="/tv-station/:stationId" element={<ProtectedRoute><TVStationPage /></ProtectedRoute>} />
                <Route path="/tv-station-setup" element={<ProtectedRoute><TVStationPage /></ProtectedRoute>} />
                <Route path="/tv-stations" element={<ProtectedRoute><AllTVStationsPage /></ProtectedRoute>} />
                <Route path="/marketplace" element={<ProtectedRoute><FilmMarketplace /></ProtectedRoute>} />
                <Route path="/drafts" element={<ProtectedRoute><FilmMarketplace /></ProtectedRoute>} />
                <Route path="/emerging-screenplays" element={<ProtectedRoute><EmergingScreenplays /></ProtectedRoute>} />
                <Route path="/journal" element={<ProtectedRoute><CinemaJournal /></ProtectedRoute>} />
                <Route path="/stars" element={<ProtectedRoute><DiscoveredStars /></ProtectedRoute>} />
                <Route path="/releases" element={<ProtectedRoute><ReleaseNotes /></ProtectedRoute>} />
                <Route path="/feedback" element={<ProtectedRoute><FeedbackBoard /></ProtectedRoute>} />
                <Route path="/social" element={<ProtectedRoute><CineBoard /></ProtectedRoute>} />
                <Route path="/games" element={<ProtectedRoute><ContestPage /></ProtectedRoute>} />
                <Route path="/contest" element={<ProtectedRoute><ContestPage /></ProtectedRoute>} />
                <Route path="/minigiochi" element={<ProtectedRoute><MiniGamesPage /></ProtectedRoute>} />
                <Route path="/challenges" element={<ProtectedRoute><Navigate to="/minigiochi" replace /></ProtectedRoute>} />
                <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
                <Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
                <Route path="/creator-board" element={<ProtectedRoute><CreatorBoard /></ProtectedRoute>} />
                <Route path="/infrastructure" element={<ProtectedRoute><InfrastructurePage /></ProtectedRoute>} />
                <Route path="/strutture" element={<ProtectedRoute><StrutturePage /></ProtectedRoute>} />
                <Route path="/agenzia" element={<ProtectedRoute><AgenziaPage /></ProtectedRoute>} />
                <Route path="/strategico" element={<ProtectedRoute><StrategicoPage /></ProtectedRoute>} />
                <Route path="/acting-school" element={<ProtectedRoute><ActingSchool /></ProtectedRoute>} />
                <Route path="/casting-agency" element={<ProtectedRoute><CastingAgencyPage /></ProtectedRoute>} />
                <Route path="/marketplace" element={<ProtectedRoute><MarketplacePage /></ProtectedRoute>} />
                <Route path="/tour" element={<ProtectedRoute><CinemaTourPage /></ProtectedRoute>} />
                <Route path="/leaderboard" element={<ProtectedRoute><LeaderboardPage /></ProtectedRoute>} />
                <Route path="/tutorial" element={<ProtectedRoute><TutorialPage /></ProtectedRoute>} />
                <Route path="/system-notes" element={<ProtectedRoute><SystemNotesPage /></ProtectedRoute>} />
                <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />
                <Route path="/sagas" element={<ProtectedRoute><SagasSeriesPage /></ProtectedRoute>} />
                <Route path="/festivals" element={<ProtectedRoute><FestivalsPage /></ProtectedRoute>} />
                <Route path="/credits" element={<ProtectedRoute><CreditsPage /></ProtectedRoute>} />
                <Route path="/player/:id" element={<ProtectedRoute><PlayerPublicProfile /></ProtectedRoute>} />
                <Route path="/hq" element={<ProtectedRoute><HqPage /></ProtectedRoute>} />
                <Route path="/pvp-arena" element={<ProtectedRoute><PvPArenaPage /></ProtectedRoute>} />
                <Route path="/major" element={<ProtectedRoute><MajorPage /></ProtectedRoute>} />
                <Route path="/event-history" element={<ProtectedRoute><EventHistoryPage /></ProtectedRoute>} />
                <Route path="/friends" element={<ProtectedRoute><FriendsPage /></ProtectedRoute>} />
                <Route path="/notifications" element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />
                <Route path="/download" element={<DownloadAppPage />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </UrlManager>
            </NotificationProvider>
            </ConfirmProvider>
          </LanguageProvider>
          </GameStoreProvider>
        </AuthProvider>
      </BrowserRouter>
      </div>
    </div>
  );
}

export default App;

