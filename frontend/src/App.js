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
  Gamepad2, Trophy, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, Trash2, Coins,
  Check, XCircle, Newspaper, MessageCircle, Building, Building2, GraduationCap,
  Award, Crown, Landmark, Car, ShoppingBag, Ticket, Popcorn, ChevronUp, Lock,
  Wallet, Bell, HelpCircle, Info, Music, BookOpen, Medal, Eye, EyeOff, Play,
  ArrowLeft, ArrowRight, UserPlus, UserCheck, Handshake, Target, Clock, RotateCcw,
  Download, Smartphone, Share2, Link2, Copy, QrCode, CheckCircle, Zap, Lightbulb, Bug,
  Palette, Briefcase, Rocket,
  KeyRound, AlertCircle, Mail, Tv, Swords, Shield, Flame, History, ArrowUpCircle, Pen, Save, Megaphone, Store, Radio, RadioTower, Disc, Video, Loader2
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
import './styles/film-strip-menu.css';
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
import { RadioProvider, useRadio } from './contexts/RadioContext';
import { RadioPromoBanner } from './components/RadioPromoBanner';
import { RadioFloatingPlayer } from './components/RadioFloatingPlayer';
import { NowPlayingBanner } from './components/NowPlayingBanner';
import { RadioStationsPopup } from './components/RadioStationsPopup';
import { CompareProducersModal } from './components/CompareProducersModal';
import { AvatarWithLogo } from './components/StudioName';
import { PullToRefresh } from './components/PullToRefresh';
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
const LaPrimaEvents = React.lazy(() => import('./pages/LaPrimaEvents'));
const TrailerEventsPage = React.lazy(() => import('./pages/TrailerEventsPage'));
const CinemaJournal = React.lazy(() => import('./pages/CinemaJournal'));
const CinemaTourPage = React.lazy(() => import('./pages/CinemaTourPage'));
const CreatorBoard = React.lazy(() => import('./pages/CreatorBoard'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const DiscoveredStars = React.lazy(() => import('./pages/DiscoveredStars'));
import { PWAInstallBanner } from './components/PWAInstallBanner';
import UserStripBanner from './components/UserStripBanner';
import QuickCommandsPanel from './components/QuickCommandsPanel';
import GuestRegisterDialog from './components/GuestRegisterDialog';
import FilmActionsSheet from './components/FilmActionsSheet';
import WalletBadge from './components/WalletBadge';
const DownloadAppPage = React.lazy(() => import('./pages/DownloadAppPage'));
const FeedbackBoard = React.lazy(() => import('./pages/FeedbackBoard'));
const FestivalsPage = React.lazy(() => import('./pages/FestivalsPage'));
const FilmDetail = React.lazy(() => import('./pages/FilmDetail'));
const FilmMarketplace = React.lazy(() => import('./pages/FilmMarketplace'));
const MarketV2Page = React.lazy(() => import('./pages/MarketV2Page'));
const MedalsChallengePage = React.lazy(() => import('./pages/MedalsChallengePage'));
const FilmWizard = React.lazy(() => import('./pages/FilmWizard'));
const FilmPipeline = React.lazy(() => import('./pages/FilmPipeline'));
const PipelineV2 = React.lazy(() => import('./pages/PipelineV2'));
const PipelineV3 = React.lazy(() => import('./pages/PipelineV3'));
const FriendsPage = React.lazy(() => import('./pages/FriendsPage'));
const InfrastructurePage = React.lazy(() => import('./pages/InfrastructurePage'));
const ParcoStudioPage = React.lazy(() => import('./pages/ParcoStudioPage'));
const ActingSchool = React.lazy(() => import('./pages/ActingSchool'));
const LeaderboardPage = React.lazy(() => import('./pages/LeaderboardPage'));
const MajorPage = React.lazy(() => import('./pages/MajorPage'));
const MarketplacePage = React.lazy(() => import('./pages/MarketplacePage'));
const ContestsPage = React.lazy(() => import('./pages/ContestsPage'));
const ContestPage = React.lazy(() => import('./pages/ContestPage'));
const MiniGamesPage = React.lazy(() => import('./pages/MiniGamesPage'));
import LoginRewardPopup from './components/LoginRewardPopup';
import { AutoTickNotifications } from './components/AutoTickNotifications';
import { LevelUpToast } from './components/LevelUpToast';
import { PrestigeTierToast } from './components/PrestigeTierToast';
import { CinematicCurtainReveal } from './components/CinematicCurtainReveal';
import TutorialModal from './components/TutorialModal';
import DashboardTour from './components/DashboardTour';
const MyFilms = React.lazy(() => import('./pages/MyFilms'));
const NotificationsPage = React.lazy(() => import('./pages/NotificationsPage'));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage'));
const ResetPasswordPage = React.lazy(() => import('./pages/ResetPasswordPage'));
const SagasSeriesPage = React.lazy(() => import('./pages/SagasSeriesPage'));
const PlayerContentPage = React.lazy(() => import('./pages/PlayerContentPage'));
const PasswordRecoveryPage = React.lazy(() => import('./pages/PasswordRecoveryPage'));
const NicknameRecoveryPage = React.lazy(() => import('./pages/NicknameRecoveryPage'));
const StatisticsPage = React.lazy(() => import('./pages/StatisticsPage'));
const EmergingScreenplays = React.lazy(() => import('./pages/EmergingScreenplays'));
const PlayerPublicProfile = React.lazy(() => import('./pages/PlayerPublicProfile'));
const SeriesTVPipeline = React.lazy(() => import('./pages/SeriesTVPipelineV3'));
const SeriesDetail = React.lazy(() => import('./pages/SeriesDetail'));
const AnimePipeline = React.lazy(() => import('./pages/AnimePipelineV3'));
const SequelPipeline = React.lazy(() => import('./pages/SequelPipeline'));
const EmittenteTVPage = React.lazy(() => import('./pages/EmittenteTVPage'));
const TVStationPage = React.lazy(() => import('./pages/TVStationPage'));
const AllTVStationsPage = React.lazy(() => import('./pages/AllTVStationsPage'));
const CastingAgencyPage = React.lazy(() => import('./pages/CastingAgencyPage'));
const TalentMarketPage = React.lazy(() => import('./pages/TalentMarketPage'));
const MyDraftsPage = React.lazy(() => import('./pages/MyDraftsPage'));
const CreateTvMoviePage = React.lazy(() => import('./pages/CreateTvMoviePage'));
const TvAwardsPage = React.lazy(() => import('./pages/TvAwardsPage'));
const AdminPage = React.lazy(() => import('./pages/AdminPage'));
const HqPage = React.lazy(() => import('./pages/HqPage'));
const PvPArenaPage = React.lazy(() => import('./pages/PvPArenaPage'));
const EventHistoryPage = React.lazy(() => import('./pages/EventHistoryPage'));
const StrutturePage = React.lazy(() => import('./pages/StrutturePage'));
const AgenziaPage = React.lazy(() => import('./pages/AgenziaPage'));
const StrategicoPage = React.lazy(() => import('./pages/StrategicoPage'));
const FinancePage = React.lazy(() => import('./pages/FinancePage'));
const SpectatorsPage = React.lazy(() => import('./pages/SpectatorsPage'));
const BankPage = React.lazy(() => import('./pages/BankPage'));

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

// ═══════════════════════════════════════════════════════════════
//  MOBILE BOTTOM NAV — 11 items + Comandi Rapidi
// ═══════════════════════════════════════════════════════════════
const MobileBottomNav = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setIsOpen: setShowProductionMenu } = useProductionMenu();
  const [showQuickCommands, setShowQuickCommands] = useState(false);
  const [showIMiei, setShowIMiei] = useState(false);
  const [showRadioPopup, setShowRadioPopup] = useState(false);
  const { banner: radioBanner, reactivateBanner } = useRadio();
  const radioLocked = !radioBanner?.user_has_tv;

  const handleRadioClick = async () => {
    if (radioLocked) {
      // Utente senza Emittente TV: rianima il banner promo 80%
      const ok = await reactivateBanner();
      if (ok) toast.success('📻 Banner promo riattivato! Sconto 80% disponibile.');
      else toast.info("Non puoi accedere alla radio senza un'Emittente TV");
    } else {
      setShowRadioPopup(true);
    }
  };

  const items = [
    { path: '/social', icon: Globe, label: 'CineBoard', testid: 'bn-cineboard' },
    { path: '/leaderboard', icon: BarChart3, label: 'Classifiche', testid: 'bn-classifiche' },
    { path: '/festivals', icon: Medal, label: 'Festival', testid: 'bn-festival' },
    { path: null, icon: Heart, label: 'Dona', testid: 'bn-dona', action: () => window.open('https://www.paypal.me/UnNickk', '_blank'), donate: true },
    { path: '/journal', icon: Newspaper, label: 'CineJournal', testid: 'bn-journal' },
    { path: '/marketplace', icon: Store, label: 'Mercato', testid: 'bn-mercato' },
    { path: null, icon: Film, label: 'I Miei', testid: 'bn-films', action: () => { setShowIMiei(!showIMiei); setShowQuickCommands(false); }, imiei: true },
    { path: '/banca', icon: Landmark, label: 'Banca', testid: 'bn-banca' },
    { path: null, icon: RadioTower, label: 'Radio', testid: 'bn-radio', action: handleRadioClick, radio: true, locked: radioLocked },
    { path: '/minigiochi', icon: Gamepad2, label: 'Minigiochi', testid: 'bn-minigiochi' },
    { path: '/event-history', icon: Sparkles, label: 'Eventi', testid: 'bn-eventi' },
    { path: null, icon: Zap, label: 'Rapidi', testid: 'bn-rapidi', action: () => setShowQuickCommands(!showQuickCommands), quick: true },
  ];

  const quickCommands = [
    { icon: Pen, label: 'Sceneggiature', path: '/emerging-screenplays' },
    { icon: Tv, label: 'Le mie TV', path: '/my-tv' },
    { icon: Building, label: 'Infrastrutture', path: '/infrastructure' },
    { icon: Target, label: 'Arena', path: '/pvp-arena' },
    { icon: Coins, label: 'Contest', path: '/games' },
    { icon: BookOpen, label: 'Saghe', path: '/sagas' },
    { icon: Star, label: 'Stelle', path: '/stars' },
    { icon: User, label: 'Profilo', path: '/profile' },
  ];

  return (
    <>
      {/* I Miei Popup — Film / Serie TV / Anime */}
      <AnimatePresence>
        {showIMiei && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-[55] sm:hidden" onClick={() => setShowIMiei(false)} />
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 400 }}
              className="fixed bottom-[52px] left-1/2 -translate-x-1/2 z-[56] sm:hidden w-36" data-testid="imiei-panel"
            >
              <div className="bg-[#111113] border border-white/10 rounded-xl overflow-hidden shadow-2xl">
                <p className="text-[9px] text-yellow-500/60 uppercase tracking-widest font-semibold px-3 pt-2 pb-1">I Miei Contenuti</p>
                {[
                  { icon: Film, label: 'Film', path: '/films?tab=film' },
                  { icon: BookOpen, label: 'Saghe e Sequel', path: '/films?tab=saghe' },
                  { icon: Tv, label: 'Serie TV', path: '/films?tab=serie' },
                  { icon: Sparkles, label: 'Anime', path: '/films?tab=anime' },
                ].map(c => (
                  <button key={c.path}
                    className={`w-full flex items-center gap-2.5 py-2.5 px-3 text-[11px] transition-all ${location.pathname === c.path ? 'bg-yellow-500/15 text-yellow-400' : 'text-gray-300 hover:bg-white/5'}`}
                    onClick={() => { navigate(c.path); setShowIMiei(false); }}
                    data-testid={`imiei-${c.label.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <c.icon className="w-4 h-4 text-yellow-500/70" />
                    <span>{c.label}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Quick Commands Popup */}
      <AnimatePresence>
        {showQuickCommands && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-[55] sm:hidden" onClick={() => setShowQuickCommands(false)} />
            <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 30 }}
              transition={{ type: 'spring', damping: 25, stiffness: 400 }}
              className="fixed bottom-[52px] left-1 right-1 z-[56] sm:hidden" data-testid="quick-commands-panel"
            >
              <QuickCommandsPanel onClose={() => setShowQuickCommands(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Bottom Nav Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-[#0F0F10]/95 backdrop-blur-md border-t border-white/10 z-50 sm:hidden sidemenu-translate"
        style={{ height: 'calc(3.2rem + env(safe-area-inset-bottom, 0px))', paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
        data-testid="mobile-bottom-nav"
      >
        <div className="flex items-center justify-between h-full px-0.5">
          {items.map(item => {
            const isActive = item.path && location.pathname === item.path;
            return (
              <button key={item.testid}
                className={`flex flex-col items-center justify-center gap-0 flex-1 min-w-0 py-0.5 rounded transition-colors ${
                  item.donate ? 'text-pink-400 animate-pulse' :
                  item.highlight ? 'text-yellow-400' :
                  item.quick ? (showQuickCommands ? 'text-yellow-400' : 'text-orange-400/70') :
                  item.imiei ? (showIMiei ? 'text-blue-300' : (isActive ? 'text-blue-300' : 'text-blue-400')) :
                  item.radio ? (item.locked ? 'text-gray-600 opacity-60' : 'text-red-400 hover:text-red-300') :
                  isActive ? 'text-yellow-400' : 'text-gray-500'
                }`}
                style={item.donate ? { animationDuration: '2s' } : {}}
                onClick={() => item.action ? item.action() : navigate(item.path)}
                data-testid={item.testid}
              >
                <div className="relative">
                  <item.icon className="w-3.5 h-3.5" />
                  {item.radio && item.locked && (
                    <Lock className="w-2 h-2 absolute -bottom-0.5 -right-0.5 text-gray-400" strokeWidth={3} />
                  )}
                </div>
                <span className="text-[6.5px] leading-tight mt-0.5 truncate w-full text-center">{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Popup selezione stazioni radio (triggered dall'icona Radio della bottom nav) */}
      <RadioStationsPopup open={showRadioPopup} onClose={() => setShowRadioPopup(false)} />
    </>
  );
};

// ═══════════════════════════════════════════════════════════════
//  GLOBAL SIDE MENU — Works on all pages
// ═══════════════════════════════════════════════════════════════
const GlobalSideMenu = () => {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const { api, user } = useContext(AuthContext);
  const { setIsOpen: openProductionMenu } = useProductionMenu();
  const [categories, setCategories] = useState({ has_strutture: false, has_agenzia: false, has_strategico: false });
  const [menuBadges, setMenuBadges] = useState({ produci: 0, contest: false });

  useEffect(() => {
    if (open && api) {
      api.get('/infrastructure/owned-categories').then(r => setCategories(r.data)).catch(() => {});
    }
  }, [open, api]);

  // Load badge counts on mount + when menu opens
  useEffect(() => {
    if (!api) return;
    const loadBadges = () => {
      api.get('/pipeline-v2/production-counts').then(r => setMenuBadges(prev => ({ ...prev, produci: r.data?.total || 0 }))).catch(() => {});
      api.get('/games/active-contests').then(r => {
        const contests = Array.isArray(r.data) ? r.data : (r.data?.contests || []);
        setMenuBadges(prev => ({ ...prev, contest: contests.length > 0 }));
      }).catch(() => {});
    };
    loadBadges();
    if (open) loadBadges();
  }, [open, api]);

  // Listen for global toggle
  useEffect(() => {
    const toggle = () => setOpen(p => { const next = !p; if (typeof navigator !== 'undefined' && navigator.vibrate) try { navigator.vibrate(15); } catch {} return next; });
    const openEv = () => { setOpen(true); if (typeof navigator !== 'undefined' && navigator.vibrate) try { navigator.vibrate(15); } catch {} };
    const closeEv = () => { setOpen(false); if (typeof navigator !== 'undefined' && navigator.vibrate) try { navigator.vibrate(10); } catch {} };
    window.addEventListener('global-sidemenu-toggle', toggle);
    window.addEventListener('global-sidemenu-open', openEv);
    window.addEventListener('global-sidemenu-close', closeEv);
    // Legacy compat
    window.addEventListener('dashboard-toggle-menu', toggle);
    return () => {
      window.removeEventListener('global-sidemenu-toggle', toggle);
      window.removeEventListener('global-sidemenu-open', openEv);
      window.removeEventListener('global-sidemenu-close', closeEv);
      window.removeEventListener('dashboard-toggle-menu', toggle);
      delete document.body.dataset.sidemenu;
    };
  }, []);

  // Expose badge state for CIACK indicator + push body attribute
  useEffect(() => {
    window.__sideMenuOpen = open;
    window.__menuHasBadge = menuBadges.produci > 0 || menuBadges.contest;
    window.dispatchEvent(new Event('menu-badge-update'));
    // Toggle body data attribute for CSS push
    if (open) {
      document.body.dataset.sidemenu = 'open';
    } else {
      delete document.body.dataset.sidemenu;
      // Reset horizontal scroll when menu closes
      if (window.scrollX > 0) window.scrollTo({ left: 0, behavior: 'smooth' });
    }
  }, [open, menuBadges]);

  const go = (path) => { setOpen(false); navigate(path); };
  const goProduci = () => { setOpen(false); openProductionMenu(true); };

  const menuItems = [
    { icon: Video, label: "Produci", action: goProduci, badge: menuBadges.produci > 0 },
    { icon: Pen, label: "Sceneggiature", action: () => go('/emerging-screenplays') },
    { icon: Store, label: "Mercato", action: () => go('/marketplace') },
    { icon: Trophy, label: "Sfide & Medaglie", action: () => go('/challenges') },
    { icon: Tv, label: "Le mie TV", action: () => go('/my-tv') },
    { icon: Building, label: "Infrastrutture", action: () => go('/infrastructure') },
    ...(categories.has_strutture ? [{ icon: Building2, label: "Strutture", action: () => go('/strutture') }] : []),
    ...(categories.has_agenzia ? [{ icon: Users, label: "Agenzia", action: () => go('/agenzia') }] : []),
    ...(categories.has_strategico ? [{ icon: Shield, label: "Strategico", action: () => go('/strategico') }] : []),
    { icon: Gamepad2, label: "Minigiochi", action: () => go('/minigiochi') },
    { icon: Coins, label: "Contest", action: () => go('/games'), badge: menuBadges.contest },
    { icon: Target, label: "Arena", action: () => go('/pvp-arena') },
    { icon: Award, label: "Festival", action: () => go('/festivals') },
  ];

  return (
    <>
      <div
        className={`fixed top-0 left-0 h-full w-[24%] min-w-[82px] max-w-[110px] z-[48] transform transition-transform duration-300 ${open ? "translate-x-0" : "-translate-x-full"}`}
        data-testid="global-side-menu"
        style={{ background: '#050505', overflow: 'hidden', touchAction: 'pan-y' }}
      >
        {/* LAYER 1: Animated film strip background */}
        <div className="film-strip-bg" aria-hidden="true" />
        {/* LAYER 2: Sprocket holes — z-5, always on top */}
        <div className="film-perfs film-perfs-left" aria-hidden="true" />
        <div className="film-perfs film-perfs-right" aria-hidden="true" />

        {/* LAYER 3: Central content area — margin 16px from edges */}
        <div className="film-content-area flex flex-col h-full" style={{ paddingTop: '48px' }}>

          {/* TOP FIXED: Funds + CinePass + Admin */}
          <div className="flex-shrink-0 pb-1 space-y-1">
            <div className="flex gap-0.5">
              <div className="flex-1 flex items-center justify-center gap-0.5 py-1 rounded border border-yellow-500/25 bg-yellow-500/8" data-testid="menu-funds">
                <DollarSign className="w-2.5 h-2.5 text-yellow-500" />
                <span className="text-yellow-500 font-bold text-[8px]">
                  {user?.funds >= 1000000 ? `${(user?.funds / 1000000).toFixed(1)}M` : user?.funds >= 1000 ? `${(user?.funds / 1000).toFixed(0)}K` : user?.funds?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex-1 flex items-center justify-center gap-0.5 py-1 rounded border border-cyan-500/25 bg-cyan-500/8" data-testid="menu-cinepass">
                <Ticket className="w-2.5 h-2.5 text-cyan-400" />
                <span className="text-cyan-400 font-bold text-[8px]">{user?.cinepass ?? 100}</span>
              </div>
            </div>
            {(user?.nickname === 'NeoMorpheus' || user?.role === 'CO_ADMIN') && (
              <button onClick={() => { setOpen(false); navigate('/admin'); }}
                className="w-full flex items-center justify-center gap-1 py-1.5 rounded bg-red-600/80 hover:bg-red-600 text-white text-[9px] font-bold transition-colors"
                data-testid="menu-admin-panel">
                <Settings className="w-3 h-3" />
                <span>ADMIN</span>
              </button>
            )}
          </div>

          {/* MIDDLE: Scrollable frames */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden" style={{ scrollbarWidth: 'none' }}>
            {menuItems.map(item => (
              <button key={item.label} className="film-frame-btn relative" onClick={item.action}
                data-testid={`global-menu-${item.label.toLowerCase().replace(/\s+/g, '-')}`}>
                <item.icon className="mb-0.5 text-yellow-500/80 mx-auto" style={{ width: 16, height: 16 }} />
                <span className="text-[8.5px] text-center leading-tight text-gray-300/80 block w-full">{item.label}</span>
                {item.badge && <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500 shadow-[0_0_4px_rgba(239,68,68,0.5)]" />}
              </button>
            ))}
            {/* Titoli di Coda */}
            <button onClick={() => { setOpen(false); window.dispatchEvent(new Event('open-titoli-di-coda')); }}
              className="film-frame-btn" data-testid="menu-titoli-di-coda">
              <Menu className="w-3.5 h-3.5 mb-0.5 text-gray-400 mx-auto" />
              <span className="text-[8px] text-center leading-tight text-gray-400 block w-full">Titoli di Coda</span>
            </button>
          </div>

          {/* BOTTOM FIXED: Banner donazioni + Esci */}
          <div className="flex-shrink-0" style={{ paddingBottom: 'calc(56px + env(safe-area-inset-bottom, 0px))' }}>
            {/* Banner donazioni arancione */}
            <div className="mx-1 mb-1 px-2 py-1.5 rounded bg-gradient-to-r from-orange-600/30 to-amber-600/20 border border-orange-500/25 cursor-pointer"
              onClick={() => { setOpen(false); window.open('https://www.paypal.me/UnNickk', '_blank'); }}
              data-testid="menu-donate-banner">
              <p className="text-[8px] font-bold text-orange-300 text-center leading-tight">Sostieni CineWorld</p>
              <p className="text-[6px] text-orange-400/60 text-center">Il tuo supporto conta!</p>
            </div>
            {/* Esci */}
            <button onClick={() => { setOpen(false); window.dispatchEvent(new Event('confirm-logout')); }}
              className="film-exit-btn" data-testid="menu-esci">
              <LogOut className="w-3 h-3" />
              <span>Esci</span>
            </button>
          </div>

        </div>
      </div>
    </>
  );
};

// ═══════════════════════════════════════════════════════════════
//  SWIPE — Solo dashboard: destra apre menu, sinistra chiude
// ═══════════════════════════════════════════════════════════════

const SwipeNavigator = () => {
  const location = useLocation();

  useEffect(() => {
    let startX = 0, startY = 0, startTarget = null;

    const isScrollable = (el) => {
      let n = el;
      while (n && n !== document.body) {
        if (n.scrollWidth > n.clientWidth + 2) {
          const s = window.getComputedStyle(n);
          if (s.overflowX === 'auto' || s.overflowX === 'scroll') return true;
        }
        n = n.parentElement;
      }
      return false;
    };

    const onStart = (e) => { startX = e.touches[0].clientX; startY = e.touches[0].clientY; startTarget = e.target; };
    const onEnd = (e) => {
      const dx = e.changedTouches[0].clientX - startX;
      const dy = e.changedTouches[0].clientY - startY;
      if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy)) return;
      if (isScrollable(startTarget)) return;

      const menuOpen = !!window.__sideMenuOpen;
      if (menuOpen && dx < 0) { window.dispatchEvent(new Event('global-sidemenu-close')); return; }
      if (!menuOpen && location.pathname === '/dashboard' && dx > 0) { window.dispatchEvent(new Event('global-sidemenu-open')); }
    };

    document.addEventListener('touchstart', onStart, { passive: true });
    document.addEventListener('touchend', onEnd, { passive: true });
    return () => { document.removeEventListener('touchstart', onStart); document.removeEventListener('touchend', onEnd); };
  }, [location.pathname]);

  return null;
};

// ═══════════════════════════════════════════════════════════════
//  TITOLI DI CODA — Full navigation grid (replaces hamburger)
// ═══════════════════════════════════════════════════════════════
const TitoliDiCoda = ({ open, setOpen, navItems, user, navigate, logout, language, t, levelInfo, setShowGameTutorial }) => {
  // Listen for open event from side menu
  useEffect(() => {
    const handler = () => setOpen(true);
    window.addEventListener('open-titoli-di-coda', handler);
    return () => window.removeEventListener('open-titoli-di-coda', handler);
  }, [setOpen]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center" data-testid="titoli-di-coda">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setOpen(false)} />
      <div className="relative w-full max-w-md bg-[#0F0F10] border-t border-white/10 rounded-t-2xl max-h-[85vh] overflow-hidden flex flex-col" style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
        {/* Header - FIXED */}
        <div className="flex-shrink-0 bg-[#0F0F10]/95 backdrop-blur-md z-10 flex items-center justify-between px-4 py-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Video className="w-5 h-5 text-yellow-500" />
            <span className="font-['Bebas_Neue'] text-base tracking-widest text-gray-300">Titoli di Coda</span>
          </div>
          <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-gray-400" onClick={() => setOpen(false)}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* SCROLLABLE content */}
        <div className="flex-1 overflow-y-auto" style={{ scrollbarWidth: 'none' }}>
          {/* User info */}
          <div className="px-4 py-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center">
                <User className="w-4 h-4 text-yellow-500" />
              </div>
              <div>
                <p className="text-white text-xs font-bold">{user?.nickname || 'Player'}</p>
                {levelInfo && <p className="text-[9px] text-gray-400">Lv.{levelInfo.level} {levelInfo.title}</p>}
              </div>
            </div>
          </div>

          {/* Navigation grid */}
          <div className="p-3">
            <p className="text-[9px] text-gray-500 uppercase tracking-widest font-semibold mb-2 px-1">Navigazione</p>
            <div className="grid grid-cols-4 gap-1.5">
              {navItems.filter(i => !i.locked).map(item => (
                <button key={`${item.path}-${item.label}`}
                  className="relative flex flex-col items-center gap-1 py-2 px-1 rounded-lg border border-white/5 text-gray-400 text-[8px] hover:bg-white/5 hover:text-white transition-all"
                  onClick={() => { navigate(item.path); setOpen(false); }}
                  data-testid={`tdc-${item.label}`}
                >
                  <item.icon className="w-3.5 h-3.5" />
                  <span className="truncate w-full text-center px-0.5 leading-tight">{typeof item.label === 'string' && item.label.length > 11 ? item.label.slice(0, 11) + '..' : item.label}</span>
                  {item.notificationCount > 0 && (
                    <span className="absolute -top-1 -right-1 min-w-[14px] h-3.5 px-1 bg-red-500 rounded-full text-[8px] font-bold text-white flex items-center justify-center">
                      {item.notificationCount > 9 ? '9+' : item.notificationCount}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="px-3 pb-3 space-y-1.5">
            <button className="w-full flex items-center gap-2 py-2 px-3 rounded-lg text-gray-400 text-[10px] hover:bg-white/5 transition-colors"
              onClick={() => { navigate('/profile'); setOpen(false); }}>
              <User className="w-3.5 h-3.5" /> Profilo
            </button>
            <button className="w-full flex items-center gap-2 py-2 px-3 rounded-lg text-gray-400 text-[10px] hover:bg-white/5 transition-colors"
              onClick={() => { setShowGameTutorial(true); setOpen(false); }}>
              <HelpCircle className="w-3.5 h-3.5" /> Tutorial
            </button>
          </div>
        </div>

        {/* Footer FIXED - Esci SOPRA banner donazioni */}
        <div className="flex-shrink-0 px-3 pb-2 pt-1 border-t border-white/5 bg-[#0F0F10]">
          <button className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-red-400 text-[10px] font-bold hover:bg-red-500/15 transition-colors border border-red-500/20"
            onClick={() => { setOpen(false); window.dispatchEvent(new Event('confirm-logout')); }}
            data-testid="titoli-esci">
            <LogOut className="w-3.5 h-3.5" /> Esci dal gioco
          </button>
        </div>
      </div>
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
  const [prodCounts, setProdCounts] = useState({ total: 0, film: 0, series: 0, anime: 0 });
  const [loginReward, setLoginReward] = useState(null); // Login Coming Soon reward popup
  const [showGuestConvertModal, setShowGuestConvertModal] = useState(false);
  const [guestConvertForm, setGuestConvertForm] = useState({ email: '', password: '', nickname: '', production_house_name: '' });
  const [guestConverting, setGuestConverting] = useState(false);

  // Guest conversion timer - show modal after 20 minutes (only if tutorial completed)
  // Fetch production counts for badge
  useEffect(() => {
    if (api && user) {
      api.get('/pipeline-v2/production-counts').then(r => setProdCounts(r.data)).catch(() => {});
      const iv = setInterval(() => { api.get('/pipeline-v2/production-counts').then(r => setProdCounts(r.data)).catch(() => {}); }, 60000);
      return () => clearInterval(iv);
    }
  }, [api, user]);
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
    { path: '/create-film', icon: Video, label: language === 'it' ? 'Produci Film' : 'Produce Film' },
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
    { path: '/tv-awards', icon: Trophy, label: 'TV Awards' },
    { path: '/social', icon: Globe, label: 'cineboard' },
    { path: '/games', icon: Coins, label: 'contests' },
    { path: '/minigiochi', icon: Gamepad2, label: language === 'it' ? 'Minigiochi + Sfide' : 'Minigames + VS' },
    { path: '/leaderboard', icon: BarChart3, label: 'leaderboard' },
    { path: '/pvp-arena', icon: Target, label: 'Arena' },
    { path: '/major', icon: Crown, label: language === 'it' ? 'Major' : 'Major' },
    { path: '/events/la-prima', icon: Trophy, label: language === 'it' ? 'La Prima' : 'La Prima' },
    { path: '/events/trailers', icon: Sparkles, label: language === 'it' ? 'Ev. Trailer' : 'Trailer Ev.' },
    { path: '/event-history', icon: Zap, label: language === 'it' ? 'Eventi' : 'Events' },
    { path: '/creator-board', icon: Palette, label: language === 'it' ? 'Creator' : 'Creator' },
    { path: '/statistics', icon: BarChart3, label: language === 'it' ? 'Statistiche' : 'Statistics' },
    { path: '/friends', icon: Users, label: language === 'it' ? 'Amici' : 'Friends' },
    { path: '/notifications', icon: Bell, label: language === 'it' ? 'Notifiche' : 'Notifications' },
    { path: '/parco-studio', icon: Camera, label: language === 'it' ? 'Parco Studio' : 'Studio Lot' },
    { path: '/strutture', icon: Briefcase, label: language === 'it' ? 'Strutture' : 'Buildings' },
    { path: '/agenzia', icon: Users, label: language === 'it' ? 'Agenzia' : 'Agency' },
    { path: '/strategico', icon: Rocket, label: language === 'it' ? 'Strategia' : 'Strategy' },
    { path: '/finanze', icon: Landmark, label: language === 'it' ? 'Finanza' : 'Finance' },
    { path: '/banca', icon: Landmark, label: language === 'it' ? 'Banca' : 'Bank' },
    { path: '/drafts', icon: Pen, label: language === 'it' ? 'Bozze' : 'Drafts' },
    { path: '/tv-stations', icon: Radio, label: language === 'it' ? 'TV Stations' : 'TV Stations' },
    { path: '/medals', icon: Medal, label: language === 'it' ? 'Medaglie' : 'Medals' },
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
      <div className="max-w-7xl mx-auto h-11 px-0.5 flex items-center justify-between">
        {/* 8 icone principali: CIACK HOME PRODUCI ARENA LE MIE TV MAJOR CHAT NOTIFICHE */}
        <div className="flex items-center gap-0 w-full justify-between">
          {/* CIACK — apre SideMenu (foto 3: drawer con filmstrip, Produci/Sceneggiature/Mercato/...) */}
          <Button variant="ghost" size="sm" className="relative flex flex-col h-10 w-8 p-0 text-yellow-500 hover:text-yellow-400 flex-shrink-0"
            onClick={() => { window.dispatchEvent(new Event('global-sidemenu-toggle')); if (typeof navigator !== 'undefined' && navigator.vibrate) try { navigator.vibrate(15); } catch {} }}
            data-testid="ciack-btn" aria-label="Menu">
            <Clapperboard className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Menù</span>
            {(prodCounts.total > 0) && <span className="absolute top-0 -right-0.5 w-2 h-2 rounded-full bg-red-500 shadow-[0_0_4px_rgba(239,68,68,0.5)]" />}
          </Button>
          {/* HOME */}
          <Button variant="ghost" size="sm" className={`flex flex-col h-10 w-8 p-0 flex-shrink-0 ${location.pathname === '/dashboard' ? 'text-yellow-400' : 'text-gray-400 hover:text-white'}`}
            onClick={() => navigate('/dashboard')} data-testid="home-btn" aria-label="Home">
            <Home className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Home</span>
          </Button>
          {/* PRODUCI — gold, pulse when active */}
          <Button variant="ghost" size="sm" className={`relative flex flex-col h-10 w-8 p-0 flex-shrink-0 text-yellow-500 hover:text-yellow-400 ${prodCounts.total > 0 ? 'animate-pulse' : ''}`}
            style={prodCounts.total > 0 ? { animationDuration: '2.5s' } : {}}
            onClick={() => setShowProductionMenu(!showProductionMenu)} data-testid="top-nav-produci" aria-label="Produci">
            <Video className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Produci</span>
            {prodCounts.total > 0 && (
              <span className="absolute top-0 -right-0.5 min-w-[10px] h-2.5 px-0.5 bg-red-500 text-white text-[7px] font-bold rounded-full flex items-center justify-center">
                {prodCounts.total > 9 ? '9+' : prodCounts.total}
              </span>
            )}
          </Button>
          {/* ARENA */}
          <Button variant="ghost" size="sm" className={`flex flex-col h-10 w-8 p-0 flex-shrink-0 ${location.pathname === '/pvp-arena' ? 'text-red-400' : 'text-gray-400 hover:text-red-400'}`}
            onClick={() => navigate('/pvp-arena')} data-testid="top-nav-arena" aria-label="Arena">
            <Target className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Arena</span>
          </Button>
          {/* LE MIE TV */}
          <Button variant="ghost" size="sm" className={`flex flex-col h-10 w-8 p-0 flex-shrink-0 ${location.pathname === '/my-tv' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => navigate('/my-tv')} data-testid="top-nav-tv" aria-label="Le Mie TV">
            <Tv className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Le Mie TV</span>
          </Button>
          {/* MAJOR */}
          <Button variant="ghost" size="sm" className={`flex flex-col h-10 w-8 p-0 flex-shrink-0 ${location.pathname === '/major' ? 'text-purple-400' : 'text-gray-400 hover:text-purple-400'}`}
            onClick={() => navigate('/major')} data-testid="top-nav-major" aria-label="Major">
            <Crown className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Major</span>
          </Button>
          {/* INFRA */}
          <Button variant="ghost" size="sm" className={`flex flex-col h-10 w-8 p-0 flex-shrink-0 ${location.pathname === '/infrastructure' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => navigate('/infrastructure')} data-testid="top-nav-infra" aria-label="Infrastrutture">
            <Building className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Infra</span>
          </Button>
          {/* 3D PARCO STUDIO */}
          <Button variant="ghost" size="sm" className={`relative flex flex-col h-10 w-8 p-0 flex-shrink-0 ${location.pathname === '/parco-studio' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => navigate('/parco-studio')} data-testid="top-nav-parco3d" aria-label="Parco Studio 3D">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              <polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" />
            </svg>
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Parco 3D</span>
          </Button>
          {/* CHAT */}
          <Button variant="ghost" size="sm" className={`flex flex-col h-10 w-8 p-0 flex-shrink-0 ${location.pathname === '/chat' ? 'text-cyan-400' : 'text-gray-400 hover:text-cyan-400'}`}
            onClick={() => navigate('/chat')} data-testid="top-nav-chat" aria-label="Chat">
            <MessageSquare className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Chat</span>
          </Button>
          {/* NOTIFICHE */}
          <Button variant="ghost" size="sm" className={`relative flex flex-col h-10 w-8 p-0 flex-shrink-0 ${location.pathname === '/notifications' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => navigate('/notifications')} data-testid="top-nav-notifiche" aria-label="Notifiche">
            <Bell className="w-3.5 h-3.5" />
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">Notifiche</span>
            {notificationCount > 0 && (
              <span className="absolute top-0 -right-0.5 min-w-[12px] h-3 px-0.5 bg-red-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                {notificationCount > 9 ? '9+' : notificationCount}
              </span>
            )}
          </Button>
          {/* Funds (Wallet Badge with delta arrows) */}
          <WalletBadge onClick={() => navigate('/finanze')} />
          {/* CinePass */}
          <div className="flex flex-col items-center bg-cyan-500/10 px-1 py-0.5 rounded border border-cyan-500/20 flex-shrink-0">
            <div className="flex items-center">
              <Ticket className="w-2 h-2 text-cyan-400" />
              <span className="text-cyan-400 font-bold text-[7px]" data-testid="cinepass-balance">{user?.cinepass ?? 100}</span>
            </div>
            <span className="text-[6px] text-cyan-400/70 leading-none">CinePass</span>
          </div>
          {/* Online Users — opens panel */}
          <Button variant="ghost" size="sm" className="relative flex flex-col h-10 w-8 p-0 text-green-400/70 hover:text-green-400 flex-shrink-0"
            onClick={() => setShowOnlineUsersPanel(!showOnlineUsersPanel)} data-testid="top-nav-online" aria-label="Utenti Online">
            <div className="relative flex items-center justify-center">
              <Users className="w-3.5 h-3.5" />
              {onlineUsersCount > 0 && (
                <span className="absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full bg-green-400 shadow-[0_0_4px_rgba(74,222,128,0.8)] animate-pulse" />
              )}
            </div>
            <span className="text-[7px] leading-none mt-0.5 truncate w-full text-center">
              <span className="text-green-400 font-bold" data-testid="online-count-badge">{onlineUsersCount}</span>
              <span className="text-gray-400"> online</span>
            </span>
          </Button>
        </div>
      </div>

      {showGameTutorial && !(user?.is_guest && !user?.tutorial_completed) && <TutorialModal onClose={() => setShowGameTutorial(false)} />}

      {/* Online Users Panel */}
      {showOnlineUsersPanel && (
        <div className="fixed inset-0 z-[100]" data-testid="online-users-panel">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowOnlineUsersPanel(false)} />
          <div className="absolute top-12 right-1 w-72 max-h-[75vh] bg-[#111113] border border-white/10 rounded-xl shadow-2xl overflow-hidden">
            <div className="sticky top-0 bg-[#111113] px-3 py-2 border-b border-white/5 flex items-center justify-between z-10">
              <span className="text-xs font-bold text-green-400">Giocatori ({allPlayersList.filter(u => !u.is_bot).length})</span>
              <button onClick={() => setShowOnlineUsersPanel(false)} className="text-gray-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>
            <div className="max-h-[65vh] overflow-y-auto">
              {/* ONLINE section */}
              {(() => {
                const onlineReal = onlineUsersList.filter(u => !u.is_bot);
                const offlinePlayers = allPlayersList.filter(u => !u.is_bot && !onlineReal.find(o => o.nickname === u.nickname));
                const timeAgo = (dateStr) => {
                  if (!dateStr) return '';
                  try {
                    const d = new Date(dateStr);
                    const now = new Date();
                    const diff = Math.floor((now - d) / 1000);
                    if (diff < 60) return 'ora';
                    if (diff < 3600) return `${Math.floor(diff/60)}m fa`;
                    if (diff < 86400) return `${Math.floor(diff/3600)}h fa`;
                    if (diff < 604800) return `${Math.floor(diff/86400)}g fa`;
                    return `${Math.floor(diff/604800)}sett fa`;
                  } catch { return ''; }
                };
                return (
                  <>
                    {onlineReal.length > 0 && (
                      <div className="px-2 pt-2 pb-1">
                        <p className="text-[8px] text-green-500 font-bold uppercase tracking-widest px-1 mb-1">Online ({onlineReal.length})</p>
                        {onlineReal.map(u => (
                          <div key={u.id || u.nickname} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer"
                            onClick={() => {
                              const uid = u.id || u.user_id;
                              if (!uid) { toast.error('Profilo non disponibile'); return; }
                              setShowOnlineUsersPanel(false);
                              openPlayerPopup(uid);
                            }}>
                            <div className="w-2 h-2 rounded-full bg-green-400 flex-shrink-0 shadow-[0_0_4px_rgba(74,222,128,0.5)]" />
                            <span className="text-xs text-gray-200 truncate flex-1">{u.nickname}</span>
                            {u.level > 0 && <span className="text-[8px] text-gray-500">Lv.{u.level}</span>}
                            <span className="text-[8px] text-green-500">ora</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="px-2 pt-1 pb-2">
                      <p className="text-[8px] text-gray-500 font-bold uppercase tracking-widest px-1 mb-1">Offline ({offlinePlayers.length})</p>
                      {offlinePlayers.slice(0, 30).map(u => (
                        <div key={u.id || u.nickname} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer"
                          onClick={() => {
                            const uid = u.id || u.user_id;
                            if (!uid) { toast.error('Profilo non disponibile'); return; }
                            setShowOnlineUsersPanel(false);
                            openPlayerPopup(uid);
                          }}>
                          <div className="w-2 h-2 rounded-full bg-gray-600 flex-shrink-0" />
                          <span className="text-xs text-gray-400 truncate flex-1">{u.nickname}</span>
                          {u.level > 0 && <span className="text-[8px] text-gray-600">Lv.{u.level}</span>}
                          <span className="text-[8px] text-gray-600">{timeAgo(u.last_active || u.last_login)}</span>
                        </div>
                      ))}
                      {offlinePlayers.length === 0 && onlineReal.length === 0 && (
                        <p className="text-[10px] text-gray-500 text-center py-4">Nessun giocatore</p>
                      )}
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* PRODUCI MENU — Bottom sheet with production options */}
      {showProductionMenu && (
        <div className="fixed inset-0 z-[100]" data-testid="produci-menu">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowProductionMenu(false)} />
          <div className="absolute bottom-0 left-0 right-0 bg-[#111113] border-t border-yellow-500/20 rounded-t-2xl shadow-2xl"
            style={{ paddingBottom: 'calc(60px + env(safe-area-inset-bottom, 0px))' }}>
            <div className="px-4 py-3 flex items-center justify-between border-b border-white/5">
              <span className="font-['Bebas_Neue'] text-base tracking-widest text-yellow-500">Produci</span>
              <button onClick={() => setShowProductionMenu(false)} className="text-gray-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>
            <div className="grid grid-cols-3 gap-2 p-3">
              {[
                { icon: Video, label: 'Film', path: '/create-film', color: 'bg-yellow-500/15 border-yellow-500/30 text-yellow-400', count: prodCounts.film },
                { icon: Radio, label: 'Film TV', path: '/create-tv-movie', color: 'bg-rose-500/15 border-rose-500/30 text-rose-400', count: 0, locked: !productionUnlocks?.has_emittente_tv, lockReason: 'Devi possedere una TV' },
                { icon: Copy, label: 'Sequel', path: '/create-sequel', color: 'bg-orange-500/15 border-orange-500/30 text-orange-400', count: 0 },
                { icon: Tv, label: 'Serie TV', path: '/create-series', color: 'bg-blue-500/15 border-blue-500/30 text-blue-400', count: prodCounts.series },
                { icon: Sparkles, label: 'Anime', path: '/create-anime', color: 'bg-amber-600/15 border-amber-600/30 text-amber-400', count: prodCounts.anime },
                { icon: BookOpen, label: 'Sceneggiature', path: '/emerging-screenplays', color: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400', count: 0 },
                { icon: Users, label: 'Agenzia', path: '/agenzia', color: 'bg-purple-500/15 border-purple-500/30 text-purple-400', count: 0 },
                { icon: Clock, label: 'Bozze', path: '/le-mie-bozze', color: 'bg-amber-500/15 border-amber-500/30 text-amber-400', count: 0 },
              ].map(item => (
                <button key={item.path}
                  className={`relative flex flex-col items-center justify-center gap-1.5 py-3 rounded-xl border ${item.color} transition-all ${item.locked ? 'opacity-50 cursor-not-allowed grayscale' : 'hover:scale-105 active:scale-95'}`}
                  onClick={() => {
                    if (item.locked) { toast.info(item.lockReason || 'Bloccato'); return; }
                    setShowProductionMenu(false); navigate(item.path);
                  }}
                  data-testid={`produci-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <item.icon className="w-6 h-6" />
                  <span className="text-[10px] font-bold">{item.label}</span>
                  {item.locked && <Lock className="absolute top-1 left-1 w-3 h-3 text-gray-500" />}
                  {!item.locked && item.count > 0 && (
                    <span className="absolute top-1 right-1 min-w-[14px] h-3.5 px-1 bg-red-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                      {item.count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TITOLI DI CODA — Full navigation grid (ex hamburger menu) */}
      <TitoliDiCoda open={mobileMenuOpen} setOpen={setMobileMenuOpen} navItems={navItems} user={user} navigate={navigate} logout={logout} language={language} t={t} levelInfo={levelInfo} setShowGameTutorial={setShowGameTutorial} />

    </nav>
  );
};


// Password Recovery Page

// ==================== ROUTING ====================

// ═══ CHALLENGE NOTIFICATION HANDLER — polls for incoming challenges ═══
const ChallengeNotificationHandler = ({ api, user, navigate }) => {
  const confirm = useConfirm();
  const [lastChecked, setLastChecked] = useState('');

  useEffect(() => {
    if (!api || !user?.id) return;
    const check = async () => {
      try {
        const r = await api.get('/api/challenges/pending');
        const challenges = Array.isArray(r.data) ? r.data : r.data?.challenges || [];
        for (const ch of challenges) {
          if (ch.id === lastChecked) continue;
          setLastChecked(ch.id);
          const ok = await confirm({
            title: `Sfida da ${ch.challenger_name}!`,
            subtitle: `Minigioco: ${ch.game_id?.replace(/_/g, ' ')}${ch.bet_amount > 0 ? ` — Scommessa: $${ch.bet_amount.toLocaleString()}` : ''}`,
            confirmLabel: 'Accetta!',
            cancelLabel: 'Rifiuta',
          });
          try {
            await api.post(`/api/challenges/${ch.id}/respond`, { accept: ok });
            if (ok) {
              toast.success(`Sfida accettata! Gioco: ${ch.game_id?.replace(/_/g, ' ')}`);
              navigate(`/minigiochi?challenge=${ch.id}&game=${ch.game_id}`);
            } else {
              toast('Sfida rifiutata');
            }
          } catch {}
          break; // Handle one at a time
        }
      } catch {}
    };
    const iv = setInterval(check, 8000);
    check();
    return () => clearInterval(iv);
  }, [api, user?.id, confirm, lastChecked, navigate]);

  return null;
};



// ═══ PLAYER PROFILE POPUP — Stats + Messaggia + Sfida Minigiochi ═══
const PlayerProfilePopup = ({ data, onClose, navigate, api, user, onCompare }) => {
  const confirm = useConfirm();
  const p = data.profile;
  const [showGames, setShowGames] = useState(false);
  const [gamesList, setGamesList] = useState([]);
  const [challengeLoading, setChallengeLoading] = useState('');
  const [showFilmography, setShowFilmography] = useState(false);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const [followersCount, setFollowersCount] = useState(p?.followers_count || 0);
  const followingCount = p?.following_count || 0;
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
  const isSelf = user?.id === data.userId;

  // Fetch all minigames from backend
  useEffect(() => {
    if (showGames && gamesList.length === 0) {
      api.get('/api/arcade/games').then(r => setGamesList(Array.isArray(r.data) ? r.data : r.data || [])).catch(() => {});
    }
  }, [showGames, gamesList.length, api]);

  // Fetch follow status
  useEffect(() => {
    if (!isSelf && data.userId) {
      api.get(`/players/${data.userId}/is-following`)
        .then(r => setIsFollowing(!!r.data?.is_following))
        .catch(() => {});
    }
  }, [data.userId, isSelf, api]);

  const toggleFollow = async () => {
    setFollowLoading(true);
    try {
      if (isFollowing) {
        await api.delete(`/follow/${data.userId}`);
        setIsFollowing(false);
        setFollowersCount(c => Math.max(0, c - 1));
        toast.success(`Non segui più ${p.nickname}`);
      } else {
        await api.post(`/follow/${data.userId}`);
        setIsFollowing(true);
        setFollowersCount(c => c + 1);
        toast.success(`Ora segui ${p.nickname}!`);
      }
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setFollowLoading(false); }
  };

  const handleMessage = async () => {
    const ok = await confirm({ title: `Messaggia ${p.nickname}?`, subtitle: 'Verrai portato nella chat privata.', confirmLabel: 'Vai alla chat', cancelLabel: 'Annulla' });
    if (ok) { onClose(); navigate(`/chat?dm=${data.userId}`); }
  };

  const handleChallenge = async (gameId) => {
    const gameName = gamesList.find(g => g.id === gameId)?.name || gameId;
    const ok = await confirm({ title: `Sfidare ${p.nickname}?`, subtitle: `Gioco: ${gameName}`, confirmLabel: 'Sfida!', cancelLabel: 'Annulla' });
    if (!ok) return;
    setChallengeLoading(gameId);
    try {
      await api.post('/api/challenges/send', { opponent_id: data.userId, game_id: gameId, bet_amount: 0 });
      toast.success(`Sfida inviata a ${p.nickname}!`);
      setShowGames(false);
    } catch (e) { toast.error(e.message || 'Errore invio sfida'); }
    setChallengeLoading('');
  };

  const avatarSrc = p.avatar_url?.startsWith('data:') ? p.avatar_url : p.avatar_url?.startsWith('/') ? `${BACKEND_URL}${p.avatar_url}` : p.avatar_url;
  const logoSrc = p.logo_url?.startsWith('data:') ? p.logo_url : p.logo_url?.startsWith('/') ? `${BACKEND_URL}${p.logo_url}` : p.logo_url;
  // best_film ora arriva dall'endpoint /players/:id/profile come oggetto { title, quality_score, cwsv_display }
  const bestFilmTitle = typeof p.best_film === 'string' ? p.best_film : p.best_film?.title;
  const bestFilmCwsv = typeof p.best_film === 'object' ? p.best_film?.cwsv_display : p.best_cwsv_display;

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center px-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60" />
      <div className="relative w-full max-w-sm bg-[#111113] rounded-2xl border border-yellow-500/20 overflow-hidden" onClick={e => e.stopPropagation()} data-testid="player-profile-popup">
        {/* Header with avatar + logo */}
        <div className="relative p-4 bg-gradient-to-b from-yellow-500/10 to-transparent">
          <button onClick={onClose} className="absolute top-2 right-2 text-gray-500"><X className="w-5 h-5" /></button>
          <div className="flex items-center gap-3">
            <button
              onClick={() => { onClose(); navigate(`/player/${data.userId}/content`); }}
              className="focus:outline-none hover:scale-105 transition-transform"
              title="Vai ai contenuti del produttore"
              data-testid="popup-avatar-studio-link">
              <AvatarWithLogo avatarUrl={avatarSrc} logoUrl={logoSrc} nickname={p.nickname} size="sm" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-['Bebas_Neue'] text-xl text-yellow-400 tracking-wide">{p.nickname}</h3>
                {!isSelf && (
                  <button
                    onClick={toggleFollow}
                    disabled={followLoading}
                    className={`flex items-center gap-1 px-2 py-0.5 rounded-full border text-[8px] font-bold transition-colors disabled:opacity-50 ${
                      isFollowing
                        ? 'bg-green-500/10 border-green-500/30 text-green-400 hover:bg-green-500/20'
                        : 'bg-blue-500/10 border-blue-500/30 text-blue-400 hover:bg-blue-500/20'
                    }`}
                    data-testid="popup-follow-btn">
                    {isFollowing ? <UserCheck className="w-2.5 h-2.5" /> : <UserPlus className="w-2.5 h-2.5" />}
                    {isFollowing ? 'Seguito' : 'Segui'}
                  </button>
                )}
              </div>
              {p.production_house_name && (
                <button
                  onClick={() => { onClose(); navigate(`/player/${data.userId}/content`); }}
                  className="text-[10px] text-gray-400 hover:text-yellow-400 underline decoration-dotted decoration-gray-600 hover:decoration-yellow-400 transition-colors"
                  data-testid="popup-studio-link">
                  {p.production_house_name}
                </button>
              )}
              <div className="flex items-center gap-2 mt-0.5" data-testid="popup-social-counts">
                <span className="text-[9px] text-gray-500">
                  <span className="text-white font-bold">{followersCount.toLocaleString()}</span> follower
                </span>
                <span className="text-gray-700">·</span>
                <span className="text-[9px] text-gray-500">
                  <span className="text-white font-bold">{followingCount.toLocaleString()}</span> seguiti
                </span>
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                {p.level && <span className="text-[8px] font-bold text-yellow-500/80 bg-yellow-500/10 border border-yellow-500/20 rounded px-1 py-0.5">LV {p.level}</span>}
                {p.fame != null && <span className="text-[8px] text-amber-400/70 bg-amber-500/10 border border-amber-500/15 rounded px-1 py-0.5">Fama {p.fame?.toLocaleString()}</span>}
                <span className={`w-2 h-2 rounded-full ${p.is_online ? 'bg-green-400' : 'bg-gray-600'}`} />
              </div>
            </div>
          </div>
        </div>

        {/* Stats grid */}
        <div className="px-4 pb-2">
          <div className="grid grid-cols-4 gap-1.5">
            {[
              { label: 'Film', value: p.total_films || 0, color: 'text-yellow-400' },
              { label: 'Serie TV', value: p.total_series || 0, color: 'text-blue-400' },
              { label: 'Anime', value: p.total_anime || 0, color: 'text-pink-400' },
              { label: 'CWSv', value: p.avg_cwsv > 0 ? (p.avg_cwsv % 1 === 0 ? p.avg_cwsv : p.avg_cwsv.toFixed(1)) : '—', color: 'text-amber-400' },
            ].map(s => (
              <div key={s.label} className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
                <p className={`text-[11px] font-bold ${s.color}`}>{s.value}</p>
                <p className="text-[7px] text-gray-600">{s.label}</p>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-1.5 mt-1.5">
            <div className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
              <p className="text-[11px] font-bold text-green-400">{p.total_revenue ? `$${p.total_revenue >= 1e6 ? `${(p.total_revenue/1e6).toFixed(1)}M` : `${Math.floor(p.total_revenue/1000)}K`}` : '$0'}</p>
              <p className="text-[7px] text-gray-600">Revenue</p>
            </div>
            <div className="text-center p-1.5 rounded bg-white/[0.03] border border-white/5">
              <p className="text-[11px] font-bold text-cyan-400">{(p.total_films || 0) + (p.total_series || 0) + (p.total_anime || 0)}</p>
              <p className="text-[7px] text-gray-600">Produzioni</p>
            </div>
          </div>
          {bestFilmTitle && (
            <div className="mt-2 p-2 rounded-lg bg-gradient-to-br from-yellow-500/10 to-yellow-500/5 border border-yellow-500/20" data-testid="popup-best-production">
              <p className="text-[7px] text-gray-500 uppercase tracking-wider font-bold mb-1">Miglior Produzione</p>
              <div className="flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-400 fill-yellow-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-bold text-white truncate">{bestFilmTitle}</p>
                  {bestFilmCwsv && <p className="text-[9px] text-yellow-400">CWSv {bestFilmCwsv}</p>}
                </div>
              </div>
            </div>
          )}
          {/* Filmografia collassabile */}
          {Array.isArray(p.filmography) && p.filmography.length > 0 && (
            <div className="mt-2" data-testid="popup-filmography">
              <button
                onClick={() => setShowFilmography(v => !v)}
                className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-colors"
                data-testid="popup-filmography-toggle">
                <span className="text-[8px] text-gray-500 uppercase tracking-wider font-bold">Filmografia recente ({p.filmography.length})</span>
                <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform ${showFilmography ? 'rotate-180' : ''}`} />
              </button>
              {showFilmography && (
                <div className="mt-1 space-y-0.5 rounded-lg bg-white/[0.02] border border-white/5 p-2">
                  {p.filmography.slice(0, 5).map((f, i) => {
                    const TypeIcon = f.type === 'anime' ? Sparkles : f.type === 'tv_series' ? Tv : Film;
                    const typeColor = f.type === 'anime' ? 'text-pink-400' : f.type === 'tv_series' ? 'text-blue-400' : 'text-yellow-400';
                    const cwsvNum = f.quality_score || 0;
                    const cwsvColor = cwsvNum >= 8 ? 'text-yellow-400' : cwsvNum >= 6 ? 'text-green-400' : cwsvNum >= 4 ? 'text-orange-400' : 'text-red-400';
                    return (
                      <div key={i} className="flex items-center gap-2 py-1">
                        <span className="text-[8px] text-gray-600 w-3">{i + 1}.</span>
                        <TypeIcon className={`w-2.5 h-2.5 ${typeColor} flex-shrink-0`} />
                        <span className="text-[10px] text-gray-300 flex-1 truncate">{f.title}</span>
                        <span className={`text-[10px] font-bold ${cwsvColor}`}>{f.cwsv_display || '—'}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
          {p.challenge_stats && (
            <div className="mt-1 flex items-center gap-2 px-2 py-1 bg-white/[0.02] rounded border border-white/5">
              <Swords className="w-3 h-3 text-pink-400/50" />
              <p className="text-[8px] text-gray-400">Sfide: <span className="text-green-400">{p.challenge_stats.wins || 0}W</span> / <span className="text-red-400">{p.challenge_stats.losses || 0}L</span></p>
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="px-4 pb-3 space-y-1.5">
          {!showGames ? (
            <>
            <div className="flex gap-2">
              <button onClick={handleMessage} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-blue-500/10 border border-blue-500/25 text-blue-400 hover:bg-blue-500/20 transition-colors text-[10px] font-bold" data-testid="popup-message-btn">
                <MessageCircle className="w-3.5 h-3.5" /> Messaggia
              </button>
              <button onClick={() => setShowGames(true)} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-pink-500/10 border border-pink-500/25 text-pink-400 hover:bg-pink-500/20 transition-colors text-[10px] font-bold" data-testid="popup-challenge-btn">
                <Swords className="w-3.5 h-3.5" /> Sfida
              </button>
            </div>
            {onCompare && data.userId !== user?.id && (
              <button onClick={() => onCompare(data.userId)} className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-purple-500/10 border border-purple-500/25 text-purple-400 hover:bg-purple-500/20 transition-colors text-[10px] font-bold" data-testid="popup-compare-btn">
                <BarChart3 className="w-3.5 h-3.5" /> Confronta con me
              </button>
            )}
            {data.userId !== user?.id && (
              <button onClick={() => { onClose(); navigate(`/player/${data.userId}/content`); }} className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 hover:bg-emerald-500/20 transition-colors text-[10px] font-bold" data-testid="popup-view-content-btn">
                <Film className="w-3.5 h-3.5" /> I Suoi Contenuti
              </button>
            )}
            </>
          ) : (
            <div className="space-y-1">
              <p className="text-[9px] text-gray-400 font-bold">Scegli minigioco:</p>
              <div className="max-h-[220px] overflow-y-auto space-y-1">
                {gamesList.length === 0 ? (
                  <p className="text-[9px] text-gray-500 text-center py-2">Caricamento giochi...</p>
                ) : gamesList.map(g => (
                  <button key={g.id} onClick={() => handleChallenge(g.id)} disabled={challengeLoading === g.id}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/5 hover:bg-pink-500/10 hover:border-pink-500/20 transition-colors active:scale-[0.98]" data-testid={`challenge-game-${g.id}`}>
                    <span className="text-[10px] text-white font-bold flex-1 text-left">{g.name}</span>
                    <span className="text-[7px] text-gray-500 truncate max-w-[120px]">{g.desc}</span>
                    {challengeLoading === g.id && <Loader2 className="w-3 h-3 animate-spin ml-1 text-pink-400" />}
                  </button>
                ))}
              </div>
              <button onClick={() => setShowGames(false)} className="w-full text-[9px] text-gray-500 py-1">Indietro</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};


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
  const [compareProducerId, setCompareProducerId] = useState(null);

  // Listen for player popup events from ContentTemplate and other components
  useEffect(() => {
    const handler = (e) => {
      const nickname = e.detail?.nickname;
      if (nickname && api) {
        setPopupData({ loading: true });
        api.get(`/auth/player-profile/${nickname}`).then(r => {
          setPopupData({ profile: r.data || r, userId: (r.data || r).user_id, loading: false });
        }).catch(() => setPopupData(null));
      }
    };
    window.addEventListener('open-player-popup', handler);
    return () => window.removeEventListener('open-player-popup', handler);
  }, [api]);
  
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
    // Bug guard: se non c'è userId, avvertiamo invece di chiudere silenziosamente
    if (!userId) {
      toast.error('Profilo non disponibile');
      return;
    }
    // Se è il proprio profilo, porta l'utente direttamente alla propria pagina profilo
    if (userId === user?.id) {
      navigate('/profile');
      return;
    }
    setPopupData({ userId, loading: true });
    try {
      // Usa lo stesso endpoint del popup produttore (da locandina film): funziona su tutti i giocatori
      const [profileRes, friendRes] = await Promise.all([
        api.get(`/players/${userId}/profile`),
        api.get(`/friends/status/${userId}`).catch(() => ({ data: { status: 'none' } }))
      ]);
      const profile = profileRes.data || {};
      setPopupData({ userId, profile, friendStatus: friendRes.data, loading: false });
    } catch(e) {
      console.warn('openPlayerPopup failed', e);
      toast.error('Impossibile caricare il profilo');
      setPopupData(null);
    }
  };
  
  if (loading) return <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center"><Video className="w-10 h-10 text-yellow-500 animate-pulse" /></div>;
  if (!user) return <Navigate to="/auth" replace />;

  return (
    <ProductionMenuContext.Provider value={{ isOpen: productionMenuOpen, setIsOpen: setProductionMenuOpen }}>
    <PlayerPopupContext.Provider value={{ openPlayerPopup, popupData, setPopupData }}>
      <TopNavbar />
      <GlobalSideMenu />
      <GuestRegisterDialog />
      <FilmActionsSheet />
      <SwipeNavigator />
      <LoginRewardPopup />
      <AutoTickNotifications api={api} />
      <LevelUpToast />
      <PrestigeTierToast />
      <CinematicCurtainReveal />
      <div className="main-content-push" style={{ paddingTop: 'env(safe-area-inset-top, 0px)' }}>
      <UserStripBanner />
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
        open={showTutorial && !(user?.is_guest && !user?.tutorial_completed)}
        onClose={() => setShowTutorial(false)}
        onNavigate={(path) => { navigate(path); setShowTutorial(false); }}
        defaultTab={velionTab}
      />
      {showGameTutorial && !(user?.is_guest && !user?.tutorial_completed) && <TutorialModal onClose={() => setShowGameTutorial(false)} />}
      {showDashboardTour && !(user?.is_guest && !user?.tutorial_completed) && <DashboardTour onClose={() => setShowDashboardTour(false)} />}

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

      {/* ═══ PLAYER PROFILE POPUP ═══ */}
      {popupData && popupData.loading && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center px-4" onClick={() => setPopupData(null)} data-testid="player-profile-loading">
          <div className="absolute inset-0 bg-black/60" />
          <div className="relative bg-[#111113] rounded-2xl border border-yellow-500/20 p-6 flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-yellow-400 animate-spin" />
            <span className="text-sm text-gray-300">Caricamento profilo…</span>
          </div>
        </div>
      )}
      {popupData && !popupData.loading && popupData.profile && (
        <PlayerProfilePopup data={popupData} onClose={() => setPopupData(null)} navigate={navigate} api={api} user={user}
          onCompare={(pid) => { setPopupData(null); setCompareProducerId(pid); }} />
      )}

      {/* ═══ COMPARE PRODUCERS MODAL ═══ */}
      <CompareProducersModal open={!!compareProducerId} onClose={() => setCompareProducerId(null)} compareWithId={compareProducerId} />

      {/* ═══ CHALLENGE NOTIFICATION POPUP ═══ */}
      <ChallengeNotificationHandler api={api} user={user} navigate={navigate} />

      {/* ═══ BOTTOM NAVBAR MOBILE ═══ */}
      <MobileBottomNav />

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
          <Bell className="w-3.5 h-3.5" />
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
      <PullToRefresh>
      {children}
      </PullToRefresh>
    </>
  );
};

// Logout with custom confirm dialog
const LogoutConfirmHandler = () => {
  const confirm = useConfirm();
  const { logout, user } = useContext(AuthContext);

  useEffect(() => {
    const handler = async () => {
      const isGuest = user?.is_guest;
      const ok = await confirm({
        title: isGuest ? 'Uscire dalla sessione Guest?' : 'Uscire dal gioco?',
        subtitle: isGuest
          ? 'Se esci ora perderai TUTTI i progressi della sessione guest. Non potrai recuperarli!'
          : 'Sei sicuro di voler effettuare il logout?',
        confirmLabel: isGuest ? 'Esci e cancella tutto' : 'Esci',
        cancelLabel: 'Annulla',
      });
      if (ok) logout();
    };
    window.addEventListener('confirm-logout', handler);
    return () => window.removeEventListener('confirm-logout', handler);
  }, [confirm, logout, user?.is_guest]);

  return null;
};

// ═══ PAGE_TITLES and StickyPageHeader removed — back arrow is now in UserStripBanner ═══

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
            <LogoutConfirmHandler />
            <NotificationProvider>
            <RadioProvider>
            <UrlManager>
              <Toaster position="top-center" theme="dark" toastOptions={{ style: { marginTop: 'calc(3.5rem + env(safe-area-inset-top, 0px))' } }} />
              <RadioPromoBanner />
              <RadioFloatingPlayer />
              <NowPlayingBanner />
              <Routes>
                <Route path="/auth" element={<AuthPage />} />
                <Route path="/recovery/password" element={<PasswordRecoveryPage />} />
                <Route path="/recovery/nickname" element={<NicknameRecoveryPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/events/la-prima" element={<ProtectedRoute><LaPrimaEvents /></ProtectedRoute>} />
                <Route path="/events/trailers" element={<ProtectedRoute><TrailerEventsPage /></ProtectedRoute>} />
                <Route path="/films" element={<ProtectedRoute><MyFilms /></ProtectedRoute>} />
                <Route path="/films/:id" element={<ProtectedRoute><FilmDetail /></ProtectedRoute>} />
                <Route path="/player/:playerId/content" element={<ProtectedRoute><PlayerContentPage /></ProtectedRoute>} />
                <Route path="/series/:id" element={<ProtectedRoute><SeriesDetail /></ProtectedRoute>} />
                <Route path="/create" element={<ProtectedRoute><PipelineV3 /></ProtectedRoute>} />
                <Route path="/create-film" element={<ProtectedRoute><PipelineV3 /></ProtectedRoute>} />
                <Route path="/pipeline-v2" element={<ProtectedRoute><PipelineV2 /></ProtectedRoute>} />
                <Route path="/pipeline-v3" element={<ProtectedRoute><PipelineV3 /></ProtectedRoute>} />
                <Route path="/create-legacy" element={<ProtectedRoute><FilmPipeline /></ProtectedRoute>} />
                <Route path="/create-series" element={<ProtectedRoute><SeriesTVPipeline /></ProtectedRoute>} />
                <Route path="/create-anime" element={<ProtectedRoute><AnimePipeline /></ProtectedRoute>} />
                <Route path="/create-sequel" element={<ProtectedRoute><SequelPipeline /></ProtectedRoute>} />
                <Route path="/my-tv" element={<ProtectedRoute><EmittenteTVPage /></ProtectedRoute>} />
                <Route path="/tv-station/:stationId" element={<ProtectedRoute><TVStationPage /></ProtectedRoute>} />
                <Route path="/tv-station-setup" element={<ProtectedRoute><TVStationPage /></ProtectedRoute>} />
                <Route path="/tv-stations" element={<ProtectedRoute><AllTVStationsPage /></ProtectedRoute>} />
                <Route path="/marketplace" element={<ProtectedRoute><MarketV2Page /></ProtectedRoute>} />
                <Route path="/market" element={<ProtectedRoute><MarketV2Page /></ProtectedRoute>} />
                <Route path="/finanze" element={<ProtectedRoute><FinancePage /></ProtectedRoute>} />
                <Route path="/spettatori" element={<ProtectedRoute><SpectatorsPage /></ProtectedRoute>} />
                <Route path="/banca" element={<ProtectedRoute><BankPage /></ProtectedRoute>} />
                <Route path="/challenges" element={<ProtectedRoute><MedalsChallengePage /></ProtectedRoute>} />
                <Route path="/medals" element={<ProtectedRoute><MedalsChallengePage /></ProtectedRoute>} />
                <Route path="/drafts" element={<ProtectedRoute><FilmMarketplace /></ProtectedRoute>} />
                <Route path="/emerging-screenplays" element={<ProtectedRoute><EmergingScreenplays /></ProtectedRoute>} />
                <Route path="/le-mie-bozze" element={<ProtectedRoute><MyDraftsPage /></ProtectedRoute>} />
                <Route path="/create-tv-movie" element={<ProtectedRoute><CreateTvMoviePage /></ProtectedRoute>} />
                <Route path="/tv-awards" element={<ProtectedRoute><TvAwardsPage /></ProtectedRoute>} />
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
                <Route path="/parco-studio" element={<ProtectedRoute><ParcoStudioPage /></ProtectedRoute>} />
                <Route path="/strutture" element={<ProtectedRoute><StrutturePage /></ProtectedRoute>} />
                <Route path="/agenzia" element={<ProtectedRoute><CastingAgencyPage /></ProtectedRoute>} />
                <Route path="/strategico" element={<ProtectedRoute><StrategicoPage /></ProtectedRoute>} />
                <Route path="/acting-school" element={<ProtectedRoute><ActingSchool /></ProtectedRoute>} />
                <Route path="/casting-agency" element={<ProtectedRoute><CastingAgencyPage /></ProtectedRoute>} />
                <Route path="/talent-market" element={<ProtectedRoute><TalentMarketPage /></ProtectedRoute>} />
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
            </RadioProvider>
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

