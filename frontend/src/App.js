import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import { 
  Film, Home, Users, MessageSquare, BarChart3, User, LogOut, Plus, Heart, 
  Globe, Calendar, DollarSign, Star, Clapperboard, Camera, MapPin, Sparkles,
  Send, Image, ChevronRight, ChevronDown, ChevronLeft, Menu, X, Settings, 
  Gamepad2, Trophy, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, Trash2,
  Check, XCircle, Newspaper, MessageCircle, Building, Building2, GraduationCap,
  Award, Crown, Landmark, Car, ShoppingBag, Ticket, Popcorn, ChevronUp, Lock,
  Wallet, Bell, HelpCircle, Info, Music, BookOpen, Medal, Eye, EyeOff,
  ArrowLeft, UserPlus, UserCheck, Handshake, Target, Clock
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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context
const AuthContext = createContext(null);
const LanguageContext = createContext(null);

// Translations hook
const useTranslations = () => {
  const { language, translations } = useContext(LanguageContext);
  return { t: (key) => translations[key] || key, language };
};

// Auth Provider with auto-login
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('cineworld_token'));

  const api = axios.create({
    baseURL: API,
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  // Auto-login on app load
  useEffect(() => {
    if (token) {
      api.get('/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('cineworld_token');
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    localStorage.setItem('cineworld_token', res.data.access_token);
    if (res.data.user?.language) {
      localStorage.setItem('cineworld_lang', res.data.user.language);
    }
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data;
  };

  const register = async (data) => {
    const res = await api.post('/auth/register', data);
    localStorage.setItem('cineworld_token', res.data.access_token);
    if (res.data.user?.language) {
      localStorage.setItem('cineworld_lang', res.data.user.language);
    }
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('cineworld_token');
    setToken(null);
    setUser(null);
  };

  const updateFunds = (newFunds) => {
    setUser(prev => ({ ...prev, funds: newFunds }));
  };

  const refreshUser = async () => {
    const res = await api.get('/auth/me');
    setUser(res.data);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, token, api, updateFunds, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Language Provider
const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(localStorage.getItem('cineworld_lang') || 'en');
  const [translations, setTranslations] = useState({});

  // Listen for localStorage changes (from login/register)
  useEffect(() => {
    const handleStorageChange = () => {
      const storedLang = localStorage.getItem('cineworld_lang');
      if (storedLang && storedLang !== language) {
        setLanguage(storedLang);
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    // Also check periodically for same-tab changes
    const interval = setInterval(() => {
      const storedLang = localStorage.getItem('cineworld_lang');
      if (storedLang && storedLang !== language) {
        setLanguage(storedLang);
      }
    }, 500);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, [language]);

  useEffect(() => {
    axios.get(`${API}/translations/${language}`)
      .then(res => setTranslations(res.data))
      .catch(() => {});
    localStorage.setItem('cineworld_lang', language);
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, translations }}>
      {children}
    </LanguageContext.Provider>
  );
};

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
  const [majorInfo, setMajorInfo] = useState(null);

  useEffect(() => {
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {});
    api.get('/notifications/count').then(r => setNotificationCount(r.data.unread_count)).catch(() => {});
    api.get('/major/my').then(r => setMajorInfo(r.data)).catch(() => {});
  }, [api, user?.total_xp, location.pathname]);

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'dashboard' },
    { path: '/films', icon: Film, label: 'my_films' },
    { path: '/create', icon: Plus, label: 'create_film' },
    { path: '/sagas', icon: BookOpen, label: 'sagas_series' },
    { path: '/infrastructure', icon: Building, label: 'infrastructure' },
    { path: '/marketplace', icon: ShoppingBag, label: 'marketplace' },
    { path: '/tour', icon: MapPin, label: 'tour' },
    { path: '/journal', icon: Newspaper, label: 'cinema_journal' },
    { path: '/festivals', icon: Award, label: 'festivals' },
    { path: '/social', icon: Users, label: 'social' },
    { path: '/games', icon: Gamepad2, label: 'mini_games' },
    { path: '/leaderboard', icon: Trophy, label: 'leaderboard' },
    { path: '/chat', icon: MessageSquare, label: 'chat' },
    { path: '/tutorial', icon: HelpCircle, label: 'tutorial' },
    { path: '/credits', icon: Info, label: 'credits' },
  ];

  const gameDate = new Date().toLocaleDateString(language === 'it' ? 'it-IT' : language === 'es' ? 'es-ES' : language === 'fr' ? 'fr-FR' : language === 'de' ? 'de-DE' : 'en-US', {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
  });
  
  // Check if we can go back
  const canGoBack = location.pathname !== '/dashboard' && window.history.length > 1;

  return (
    <nav className="fixed top-0 left-0 right-0 h-14 bg-[#0F0F10]/95 backdrop-blur-md border-b border-white/10 z-50">
      <div className="max-w-7xl mx-auto h-full px-3 flex items-center justify-between">
        {/* Left section: Back button + Logo */}
        <div className="flex items-center gap-2">
          {/* Back Button */}
          {canGoBack && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-8 w-8 p-0 text-gray-400 hover:text-white"
              onClick={() => navigate(-1)}
              data-testid="back-btn"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
          )}
          
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/dashboard')} data-testid="logo">
            <Clapperboard className="w-7 h-7 text-yellow-500" />
            <span className="font-['Bebas_Neue'] text-lg tracking-wide hidden sm:block">CineWorld</span>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-0.5">
          {navItems.map(item => (
            <Button
              key={item.path}
              variant={location.pathname === item.path ? "default" : "ghost"}
              size="sm"
              className={`gap-1 px-2 h-8 ${location.pathname === item.path ? 'bg-yellow-500 text-black hover:bg-yellow-400' : 'text-gray-400 hover:text-white'}`}
              onClick={() => navigate(item.path)}
              data-testid={`nav-${item.label}`}
            >
              <item.icon className="w-3.5 h-3.5" />
              <span className="hidden xl:inline text-xs">{t(item.label)}</span>
            </Button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {/* Major Icon */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-8 w-8 p-0 ${location.pathname === '/major' ? 'text-purple-400' : 'text-gray-400 hover:text-purple-400'}`}
            onClick={() => navigate('/major')}
            data-testid="major-btn"
            title={majorInfo?.has_major ? majorInfo.major?.name : (language === 'it' ? 'Major' : 'Major')}
          >
            <Crown className="w-4 h-4" />
            {majorInfo?.has_major && (
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-purple-500 rounded-full"></span>
            )}
          </Button>
          
          {/* Notifications Icon */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-8 w-8 p-0 ${location.pathname === '/notifications' ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
            onClick={() => navigate('/notifications')}
            data-testid="notifications-btn"
          >
            <Bell className="w-4 h-4" />
            {notificationCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {notificationCount > 99 ? '99+' : notificationCount}
              </span>
            )}
          </Button>
          
          {/* Friends Icon */}
          <Button
            variant="ghost"
            size="sm"
            className={`relative h-8 w-8 p-0 ${location.pathname === '/friends' ? 'text-blue-400' : 'text-gray-400 hover:text-blue-400'}`}
            onClick={() => navigate('/friends')}
            data-testid="friends-btn"
          >
            <UserPlus className="w-4 h-4" />
          </Button>
          
          {/* Level Badge */}
          {levelInfo && (
            <div className="hidden md:flex items-center gap-1.5 bg-purple-500/10 px-2 py-1 rounded border border-purple-500/20 cursor-pointer" onClick={() => navigate('/profile')} title={`${levelInfo.current_xp}/${levelInfo.xp_for_next_level} XP`}>
              <Star className="w-3 h-3 text-purple-400" />
              <span className="text-purple-400 font-bold text-xs">Lv.{levelInfo.level}</span>
              <div className="w-12 h-1.5 bg-purple-900/50 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full transition-all" style={{width: `${levelInfo.progress_percent}%`}} />
              </div>
            </div>
          )}

          <div className="hidden md:flex items-center gap-1.5 text-xs text-gray-400">
            <Calendar className="w-3 h-3" />
            <span className="hidden lg:inline">{gameDate}</span>
          </div>

          <div className="flex items-center gap-1 bg-yellow-500/10 px-2 py-1 rounded border border-yellow-500/20">
            <DollarSign className="w-3 h-3 text-yellow-500" />
            <span className="text-yellow-500 font-bold text-xs" data-testid="user-funds">
              ${user?.funds?.toLocaleString() || '0'}
            </span>
          </div>

          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="w-12 h-7 text-xs bg-transparent border-white/10 px-1" data-testid="language-selector">
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

          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" className="p-1 h-8 w-8" data-testid="profile-menu">
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

          <Button variant="ghost" className="lg:hidden p-1 h-8 w-8" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
        </div>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="lg:hidden absolute top-14 left-0 right-0 bg-[#0F0F10] border-b border-white/10 p-3"
          >
            {/* Mobile Level Display */}
            {levelInfo && (
              <div className="flex items-center gap-2 mb-3 p-2 bg-purple-500/10 rounded border border-purple-500/20">
                <Star className="w-4 h-4 text-purple-400" />
                <span className="text-purple-400 font-bold">Level {levelInfo.level}</span>
                <div className="flex-1 h-2 bg-purple-900/50 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 rounded-full" style={{width: `${levelInfo.progress_percent}%`}} />
                </div>
                <span className="text-[10px] text-purple-300">{levelInfo.current_xp}/{levelInfo.xp_for_next_level}</span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              {navItems.map(item => (
                <Button
                  key={item.path}
                  variant={location.pathname === item.path ? "default" : "ghost"}
                  size="sm"
                  className={`gap-2 justify-start h-9 ${location.pathname === item.path ? 'bg-yellow-500 text-black' : ''}`}
                  onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}
                >
                  <item.icon className="w-4 h-4" />
                  {t(item.label)}
                </Button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
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
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardHeader className="text-center space-y-3 pb-4">
            <div className="flex justify-center">
              <Clapperboard className="w-12 h-12 text-yellow-500" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-2xl tracking-wide">CineWorld Studio's</CardTitle>
            <CardDescription className="text-xs">
              {isLogin ? 'Sign in to your production house' : 'Create your production empire'}
            </CardDescription>
          </CardHeader>
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

              <Button 
                type="submit" 
                className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold uppercase tracking-wider h-9 text-sm"
                disabled={loading || (!isLogin && !acceptedTerms)}
                data-testid="auth-submit-btn"
              >
                {loading ? 'Loading...' : isLogin ? 'Sign In' : 'Create Account'}
              </Button>
            </form>

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
// Skill translations map
const SKILL_TRANSLATIONS = {
  // Screenwriter skills
  dialogue: { en: 'Dialogue', it: 'Dialoghi' },
  plot_structure: { en: 'Plot Structure', it: 'Struttura Trama' },
  character_development: { en: 'Character Dev.', it: 'Sviluppo Personaggi' },
  originality: { en: 'Originality', it: 'Originalità' },
  adaptation: { en: 'Adaptation', it: 'Adattamento' },
  pacing: { en: 'Pacing', it: 'Ritmo' },
  world_building: { en: 'World Building', it: 'Creazione Mondi' },
  emotional_impact: { en: 'Emotional Impact', it: 'Impatto Emotivo' },
  // Director skills
  vision: { en: 'Vision', it: 'Visione' },
  leadership: { en: 'Leadership', it: 'Leadership' },
  actor_direction: { en: 'Actor Direction', it: 'Direzione Attori' },
  visual_style: { en: 'Visual Style', it: 'Stile Visivo' },
  storytelling: { en: 'Storytelling', it: 'Narrazione' },
  technical: { en: 'Technical', it: 'Tecnico' },
  innovation: { en: 'Innovation', it: 'Innovazione' },
  // Composer skills
  melodic: { en: 'Melodic Comp.', it: 'Comp. Melodica' },
  orchestration: { en: 'Orchestration', it: 'Orchestrazione' },
  emotional_scoring: { en: 'Emotional Scoring', it: 'Musica Emotiva' },
  genre_versatility: { en: 'Genre Versatility', it: 'Versatilità Generi' },
  sound_design: { en: 'Sound Design', it: 'Sound Design' },
  theme_development: { en: 'Theme Dev.', it: 'Sviluppo Temi' },
  // Actor skills
  drama: { en: 'Drama', it: 'Dramma' },
  comedy: { en: 'Comedy', it: 'Commedia' },
  action: { en: 'Action', it: 'Azione' },
  romance: { en: 'Romance', it: 'Romantico' },
  horror: { en: 'Horror', it: 'Horror' },
  sci_fi: { en: 'Sci-Fi', it: 'Fantascienza' },
  voice_acting: { en: 'Voice Acting', it: 'Doppiaggio' },
  improvisation: { en: 'Improvisation', it: 'Improvvisazione' },
};

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
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  useEffect(() => {
    if (isOpen && userId) {
      setLoading(true);
      api.get(`/users/${userId}/full-profile`)
        .then(res => {
          setProfile(res.data);
          setLoading(false);
        })
        .catch(err => {
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
      sendMessage: language === 'it' ? 'Invia Messaggio' : 'Send Message',
      viewFilms: language === 'it' ? 'Vedi Film' : 'View Films',
      close: language === 'it' ? 'Chiudi' : 'Close',
      online: language === 'it' ? 'Online' : 'Online',
      offline: language === 'it' ? 'Offline' : 'Offline',
      bestFilm: language === 'it' ? 'Miglior Film' : 'Best Film',
      recentFilms: language === 'it' ? 'Film Recenti' : 'Recent Films'
    };
    return translations[key] || key;
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
                <Card className="bg-black/30 border-yellow-500/30">
                  <CardContent className="p-3 flex items-center gap-3">
                    {profile.best_film.poster_url && (
                      <img src={profile.best_film.poster_url} alt="" className="w-12 h-16 object-cover rounded" />
                    )}
                    <div className="flex-1">
                      <p className="font-semibold">{profile.best_film.title}</p>
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
                    <Card key={film.id} className="bg-black/30 border-white/10">
                      <CardContent className="p-2">
                        <p className="text-xs font-semibold truncate">{film.title}</p>
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
              <div className="flex gap-2 mt-4">
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
                  <div key={film.id} className="bg-black/30 rounded p-2 flex justify-between items-center">
                    <span className="text-xs">{i + 1}. {film.title}</span>
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
              <div className="bg-green-500/10 rounded p-3 text-center">
                <p className="text-2xl font-bold text-green-500">${((detailedStats.revenue?.total || 0) / 1000000).toFixed(2)}M</p>
                <p className="text-xs text-gray-400">{t('total')}</p>
              </div>
              <div className="bg-blue-500/10 rounded p-3 text-center">
                <p className="text-2xl font-bold text-blue-500">${((detailedStats.revenue?.average_per_film || 0) / 1000000).toFixed(2)}M</p>
                <p className="text-xs text-gray-400">{t('avgPerFilm')}</p>
              </div>
            </div>
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
                  <div key={film.id} className="bg-black/30 rounded p-2 flex justify-between items-center">
                    <span className="text-xs">{i + 1}. {film.title}</span>
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
  const navigate = useNavigate();
  
  // Stats detail modal state
  const [showStatsDetail, setShowStatsDetail] = useState(false);
  const [selectedStatType, setSelectedStatType] = useState(null);
  
  const openStatDetail = (statType) => {
    setSelectedStatType(statType);
    setShowStatsDetail(true);
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
        
        const [statsRes, filmsRes, challengesRes] = await Promise.all([
          api.get('/statistics/my'),
          api.get('/films/my'),
          api.get('/challenges')
        ]);
        setStats(statsRes.data);
        setFilms(filmsRes.data.slice(0, 4));
        setChallenges(challengesRes.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
    
    // Setup heartbeat to track activity (every 5 minutes)
    const heartbeatInterval = setInterval(() => {
      api.post('/activity/heartbeat').catch(() => {});
    }, 5 * 60 * 1000);
    
    return () => clearInterval(heartbeatInterval);
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

      <div className="grid md:grid-cols-3 gap-3 mb-4">
        <Card className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border-yellow-500/20 cursor-pointer" onClick={() => navigate('/create')}>
          <CardContent className="p-3 flex items-center gap-2">
            <div className="p-2 bg-yellow-500 rounded-lg"><Plus className="w-5 h-5 text-black" /></div>
            <div><h3 className="font-['Bebas_Neue'] text-lg">{t('create_film')}</h3><p className="text-xs text-gray-400">New blockbuster</p></div>
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
                <div className="aspect-[2/3] relative"><img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} alt={film.title} className="w-full h-full object-cover" /></div>
                <CardContent className="p-2">
                  <h3 className="font-semibold text-xs truncate">{film.title}</h3>
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
  const [sponsors, setSponsors] = useState([]);
  const [locations, setLocations] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [screenwriters, setScreenwriters] = useState([]);
  const [directors, setDirectors] = useState([]);
  const [actors, setActors] = useState([]);
  const [composers, setComposers] = useState([]);
  const [genres, setGenres] = useState({});
  const [actorRoles, setActorRoles] = useState([]);
  
  // New states for cast filtering
  const [castCategories, setCastCategories] = useState([]);
  const [availableSkills, setAvailableSkills] = useState({
    screenwriters: [], directors: [], actors: [], composers: []
  });
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSkill, setSelectedSkill] = useState('all');
  const [skillSearchQuery, setSkillSearchQuery] = useState('');

  const [filmData, setFilmData] = useState({
    title: '', genre: 'action', subgenres: [], release_date: new Date().toISOString().split('T')[0],
    weeks_in_theater: 4, sponsor_id: null, equipment_package: 'Standard', locations: [], location_days: {},
    screenwriter_id: '', director_id: '', composer_id: '', actors: [], extras_count: 50, extras_cost: 50000,
    screenplay: '', screenplay_source: 'manual', screenplay_prompt: '', 
    soundtrack_prompt: '', soundtrack_description: '',
    poster_url: '', poster_prompt: '', ad_duration_seconds: 0, ad_revenue: 0
  });
  const [releaseDate, setReleaseDate] = useState(new Date());
  const steps = [{num:1,title:'Title'},{num:2,title:'Sponsor'},{num:3,title:'Equipment'},{num:4,title:'Writer'},{num:5,title:'Director'},{num:6,title:'Composer'},{num:7,title:'Cast'},{num:8,title:'Script'},{num:9,title:'Soundtrack'},{num:10,title:'Poster'},{num:11,title:'Ads'},{num:12,title:'Review'}];

  useEffect(() => { 
    api.get('/sponsors').then(r=>setSponsors(r.data)); 
    api.get('/locations').then(r=>setLocations(r.data)); 
    api.get('/equipment').then(r=>setEquipment(r.data));
    api.get('/genres').then(r=>setGenres(r.data));
    api.get('/actor-roles').then(r=>setActorRoles(r.data));
  }, [api]);
  
  const fetchPeople = async (type, category = '', skill = '') => {
    let url = `/${type}?limit=40`;
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

  const generateScreenplay = async () => { setGenerating(true); try { const res = await api.post('/ai/screenplay', { genre: filmData.genre, title: filmData.title, language, tone: 'dramatic', length: 'medium', custom_prompt: filmData.screenplay_prompt }); setFilmData({...filmData, screenplay: res.data.screenplay, screenplay_source: 'ai'}); toast.success('Sceneggiatura generata!'); } catch(e) { toast.error('Errore'); } finally { setGenerating(false); }};
  const generatePoster = async () => { setGenerating(true); try { const res = await api.post('/ai/poster', { title: filmData.title, genre: filmData.genre, description: filmData.poster_prompt || filmData.title, style: 'cinematic' }); setFilmData({...filmData, poster_url: res.data.poster_url}); toast.success('Poster generated!'); } catch(e) { toast.error('Failed'); } finally { setGenerating(false); }};
  const generateSoundtrack = async () => { setGenerating(true); try { const res = await api.post('/ai/soundtrack-description', { title: filmData.title, genre: filmData.genre, mood: 'epic', custom_prompt: filmData.soundtrack_prompt }); setFilmData({...filmData, soundtrack_description: res.data.description}); toast.success('Descrizione colonna sonora generata!'); } catch(e) { toast.error('Errore generazione'); } finally { setGenerating(false); }};
  
  const calculateBudget = () => { const eq = equipment.find(e=>e.name===filmData.equipment_package)||{cost:0}; let loc=0; filmData.locations.forEach(l=>{const lo=locations.find(x=>x.name===l); if(lo)loc+=lo.cost_per_day*(filmData.location_days[l]||7);}); return eq.cost+loc+filmData.extras_cost; };
  const getSponsorBudget = () => { if(!filmData.sponsor_id)return 0; const s=sponsors.find(x=>x.name===filmData.sponsor_id); return s?.budget_offer||0; };
  
  const handleSubmit = async () => { setLoading(true); try { const res = await api.post('/films', {...filmData, release_date: releaseDate.toISOString()}); toast.success(`Film created! Opening: $${res.data.opening_day_revenue.toLocaleString()}`); updateFunds(user.funds - calculateBudget() + getSponsorBudget() + filmData.ad_revenue + res.data.opening_day_revenue); navigate(`/films/${res.data.id}`); } catch(e) { toast.error(e.response?.data?.detail||'Failed'); } finally { setLoading(false); }};

  const getRoleName = (roleId) => {
    const role = actorRoles.find(r => r.id === roleId);
    if (!role) return roleId;
    const langKey = `name_${language}`;
    return role[langKey] || role.name;
  };

  const PersonCard = ({ person, isSelected, onSelect, showRoleSelect = false, currentRole = null, onRoleChange = null, roleType = 'actor' }) => {
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
    
    return (
      <Card className={`bg-[#1A1A1A] border-2 cursor-pointer transition-all ${isSelected ? 'border-yellow-500 ring-1 ring-yellow-500/50' : 'border-white/10 hover:border-white/20'}`} onClick={onSelect}>
        <CardContent className="p-2">
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
        <div><Label className="text-xs">Title *</Label><Input value={filmData.title} onChange={e=>setFilmData({...filmData,title:e.target.value})} placeholder="Film title..." className="h-10 bg-black/20 border-white/10" data-testid="film-title-input" /></div>
        <div>
          <Label className="text-xs">{t('genre')} *</Label>
          <Select value={filmData.genre} onValueChange={v=>setFilmData({...filmData, genre:v, subgenres: []})}>
            <SelectTrigger className="h-9 bg-black/20 border-white/10"><SelectValue /></SelectTrigger>
            <SelectContent className="bg-[#1A1A1A] max-h-[200px]">
              {Object.entries(genres).map(([key, g])=><SelectItem key={key} value={key}>{g.name}</SelectItem>)}
            </SelectContent>
          </Select>
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
      <div className="flex justify-between mt-3">
        <Button variant="outline" size="sm" onClick={()=>setStep(step-1)} disabled={step===1}>Previous</Button>
        {step<12?<Button size="sm" onClick={()=>setStep(step+1)} disabled={!canProceed()} className="bg-yellow-500 text-black">Next <ChevronRight className="w-3 h-3 ml-1" /></Button>:<Button size="sm" onClick={handleSubmit} disabled={loading||calculateBudget()-getSponsorBudget()-filmData.ad_revenue>user.funds} className="bg-yellow-500 text-black">{loading?'...':'Create Film'}</Button>}
      </div>
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
  const navigate = useNavigate();
  
  // One-time actions state
  const [filmActions, setFilmActions] = useState(null);
  const [performingAction, setPerformingAction] = useState(null);

  const loadFilm = async () => {
    const id = window.location.pathname.split('/').pop(); 
    const [filmRes, rolesRes, trailerRes, actionsRes] = await Promise.all([
      api.get(`/films/${id}`),
      api.get('/actor-roles').catch(() => ({ data: [] })),
      api.get(`/films/${id}/trailer-status`).catch(() => ({ data: null })),
      api.get(`/films/${id}/actions`).catch(() => ({ data: null }))
    ]);
    setFilm(filmRes.data);
    setActorRoles(rolesRes.data);
    if (trailerRes.data) setTrailerStatus(trailerRes.data);
    if (actionsRes.data) setFilmActions(actionsRes.data);
    
    // Load hourly revenue and duration status for in-theater films
    if (filmRes.data.status === 'in_theaters') {
      const [hourlyRes, durationRes] = await Promise.all([
        api.get(`/films/${id}/hourly-revenue`).catch(() => null),
        api.get(`/films/${id}/duration-status`).catch(() => null)
      ]);
      if (hourlyRes) setHourlyRevenue(hourlyRes.data);
      if (durationRes) setDurationStatus(durationRes.data);
    }
  };

  useEffect(() => { loadFilm(); }, [api]);
  
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
      const res = await api.post(`/films/${film.id}/extend?extra_days=7`);
      toast.success(`Film esteso di ${res.data.extra_days} giorni! Fame +${res.data.fame_bonus}`);
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
          <div className="aspect-[2/3]"><img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'} alt={film.title} className="w-full h-full object-cover" /></div>
          <CardContent className="p-3">
            <h1 className="font-['Bebas_Neue'] text-xl mb-2">{film.title}</h1>
            <div className="flex flex-wrap gap-1.5 mb-2">
              <Badge className="bg-yellow-500/20 text-yellow-500 text-xs">{t(film.genre)}</Badge>
              {film.subgenres?.map(sg => <Badge key={sg} variant="outline" className="text-[10px] h-4 border-gray-600">{sg}</Badge>)}
              <Badge className={`text-xs ${film.status==='in_theaters'?'bg-green-500':film.status==='withdrawn'?'bg-orange-500':'bg-gray-500'}`}>{film.status}</Badge>
              {film.imdb_rating && <Badge className="bg-yellow-600/20 text-yellow-600 text-xs">IMDb {film.imdb_rating}</Badge>}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="text-center p-2 rounded bg-white/5"><Heart className="w-4 h-4 mx-auto mb-0.5 text-red-400" /><p className="font-bold text-sm">{film.likes_count}</p></div>
              <div className="text-center p-2 rounded bg-white/5"><DollarSign className="w-4 h-4 mx-auto mb-0.5 text-green-400" /><p className="font-bold text-sm">${(film.total_revenue||0).toLocaleString()}</p></div>
            </div>
            <div className="mt-2 pt-2 border-t border-white/10 space-y-1">
              <div className="flex justify-between text-xs"><span className="text-gray-400">Quality</span><span>{film.quality_score?.toFixed(0)}%</span></div><Progress value={film.quality_score} className="h-1.5" />
              <div className="flex justify-between text-xs"><span className="text-gray-400">Satisfaction</span><span>{(film.audience_satisfaction||50).toFixed(0)}%</span></div><Progress value={film.audience_satisfaction||50} className="h-1.5" />
            </div>
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
                {durationStatus.status === 'extend' && (
                  <div className="p-3 rounded bg-green-500/20 border border-green-500/30 mb-3">
                    <p className="text-green-400 font-semibold flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Film idoneo per estensione!</p>
                    <p className="text-xs text-gray-300">Puoi estendere fino a {durationStatus.extension_days} giorni extra.</p>
                    <p className="text-xs text-green-300">Fame bonus: +{durationStatus.fame_change}</p>
                    <Button onClick={extendFilm} size="sm" className="mt-2 bg-green-600">Estendi di 7 giorni</Button>
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
          {/* Box Office */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2"><CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2"><Globe className="w-4 h-4 text-yellow-500" /> {t('box_office')}</CardTitle></CardHeader>
            <CardContent>
              {Object.keys(film.box_office||{}).length===0?<p className="text-gray-400 text-center py-4 text-sm">Box office data after release</p>:(
                <ScrollArea className="h-[250px]"><div className="space-y-1.5 pr-2">{Object.entries(film.box_office).map(([country,data])=>(
                  <div key={country} className="border border-white/10 rounded overflow-hidden">
                    <button className="w-full p-2 flex justify-between items-center hover:bg-white/5 text-sm" onClick={()=>setExpandedCountry(expandedCountry===country?null:country)}><span className="font-semibold">{country}</span><div className="flex items-center gap-2"><span className="text-green-400">${data.total_revenue?.toLocaleString()}</span>{expandedCountry===country?<ChevronDown className="w-3 h-3" />:<ChevronRight className="w-3 h-3" />}</div></button>
                    {expandedCountry===country&&<div className="p-2 pt-0 border-t border-white/10 bg-black/20">{Object.entries(data.cities||{}).map(([city,cd])=><div key={city} className="flex justify-between py-0.5 text-xs"><span>{city}</span><span className="text-green-400">${cd.revenue?.toLocaleString()}</span></div>)}</div>}
                  </div>
                ))}</div></ScrollArea>
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
const SocialFeed = () => {
  const { api, user } = useContext(AuthContext);
  const { t } = useTranslations();
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => { 
    api.get('/films/social/feed')
      .then(r => setFilms(r.data.films))
      .finally(() => setLoading(false)); 
  }, [api]);

  const handleLike = async (filmId) => {
    const res = await api.post(`/films/${filmId}/like`);
    setFilms(films.map(f => f.id === filmId ? { ...f, user_liked: res.data.liked, likes_count: res.data.likes_count } : f));
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="social-feed-page">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4">{t('social')}</h1>
      
      {loading ? (
        <div className="text-center py-8 text-gray-400">Loading...</div>
      ) : films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center">
          <Users className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <h3 className="text-lg mb-2">No films from other players yet</h3>
          <p className="text-gray-400 text-sm">Be the first to create a film and share it!</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {films.map(film => (
            <Card key={film.id} className="bg-[#1A1A1A] border-white/10 overflow-hidden">
              <div className="flex">
                <div className="w-24 flex-shrink-0 cursor-pointer" onClick={() => navigate(`/films/${film.id}`)}>
                  <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300'} alt={film.title} className="w-full h-full object-cover" />
                </div>
                <CardContent className="flex-1 p-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-sm cursor-pointer hover:text-yellow-500" onClick={() => navigate(`/films/${film.id}`)}>{film.title}</h3>
                      <p className="text-xs text-gray-400">by {film.owner?.production_house_name || 'Unknown'}</p>
                    </div>
                    <Badge className="bg-yellow-500/20 text-yellow-500 text-xs">{t(film.genre)}</Badge>
                  </div>
                  <div className="flex items-center gap-3 mt-2">
                    <Button variant="ghost" size="sm" className={`h-7 px-2 ${film.user_liked ? 'text-red-400' : 'text-gray-400'}`} onClick={() => handleLike(film.id)}>
                      <Heart className={`w-3.5 h-3.5 mr-1 ${film.user_liked ? 'fill-red-400' : ''}`} /> {film.likes_count}
                    </Button>
                    <span className="text-xs text-gray-400"><Star className="w-3 h-3 inline mr-0.5 text-yellow-500" />{film.quality_score?.toFixed(0)}%</span>
                    <span className="text-xs text-green-400">${(film.total_revenue || 0).toLocaleString()}</span>
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
                          <div className={`max-w-[70%] px-3 py-1.5 rounded-xl text-sm ${msg.sender_id === user.id ? 'bg-yellow-500 text-black rounded-br-sm' : msg.sender?.is_bot ? 'bg-blue-500/20 border border-blue-500/30 rounded-bl-sm' : 'bg-white/10 rounded-bl-sm'}`}>
                            {msg.sender_id !== user.id && !activeRoom.is_private && (
                              <div className="flex items-center gap-1 mb-0.5">
                                <p className="text-xs font-semibold">{msg.sender?.nickname}</p>
                                {msg.sender?.is_bot && msg.sender?.is_moderator && <Badge className="h-3 px-1 text-[8px] bg-red-500/30 text-red-400">MOD</Badge>}
                                {msg.sender?.is_bot && !msg.sender?.is_moderator && <Badge className="h-3 px-1 text-[8px] bg-blue-500/30 text-blue-400">BOT</Badge>}
                              </div>
                            )}
                            <p>{msg.content}</p>
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

// Tutorial Page
const TutorialPage = () => {
  const { api } = useContext(AuthContext);
  const [tutorial, setTutorial] = useState({ steps: [] });
  const [currentStep, setCurrentStep] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/game/tutorial').then(r => setTutorial(r.data)).catch(console.error);
  }, [api]);

  const iconMap = {
    film: Film, clapperboard: Clapperboard, users: Users, trophy: Trophy,
    building: Building, 'dollar-sign': DollarSign, gamepad: Gamepad2
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="tutorial-page">
      <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2 mb-6">
        <HelpCircle className="w-7 h-7 text-yellow-500" /> Tutorial
      </h1>
      
      <div className="grid gap-4">
        {tutorial.steps.map((step, index) => {
          const IconComp = iconMap[step.icon] || Star;
          return (
            <Card 
              key={step.id}
              className={`bg-[#1A1A1A] border-white/10 cursor-pointer transition-all ${currentStep === index ? 'ring-2 ring-yellow-500' : ''}`}
              onClick={() => setCurrentStep(index)}
            >
              <CardContent className="p-4 flex items-start gap-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${currentStep === index ? 'bg-yellow-500 text-black' : 'bg-white/10'}`}>
                  <IconComp className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{step.id}. {step.title}</h3>
                  <p className="text-gray-400 text-sm mt-1">{step.description}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      
      <div className="mt-6 text-center">
        <Button onClick={() => navigate('/dashboard')} className="bg-yellow-500 text-black">
          Inizia a Giocare!
        </Button>
      </div>
    </div>
  );
};

// Festivals Page
const FestivalsPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
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

  const getPrestigeStars = (prestige) => '⭐'.repeat(prestige);

  return (
    <div className="pt-16 pb-20 px-3 max-w-6xl mx-auto" data-testid="festivals-page">
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
                    {fest.is_active && <Badge className="bg-green-500/20 text-green-400 w-fit">{language === 'it' ? 'IN CORSO' : 'ACTIVE'}</Badge>}
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-400 text-xs mb-3">{fest.description}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">{language === 'it' ? 'Prossimo' : 'Next'}: {fest.next_date}</span>
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

// Credits Page
const CreditsPage = () => {
  const { api } = useContext(AuthContext);
  const [credits, setCredits] = useState(null);

  useEffect(() => {
    api.get('/game/credits').then(r => setCredits(r.data)).catch(console.error);
  }, [api]);

  if (!credits) return <div className="pt-20 text-center">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="credits-page">
      <div className="text-center mb-8">
        <Clapperboard className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
        <h1 className="font-['Bebas_Neue'] text-4xl">{credits.game_title}</h1>
        <p className="text-gray-400">Versione {credits.version}</p>
      </div>
      
      <Card className="bg-[#1A1A1A] border-white/10 mb-6">
        <CardContent className="p-6">
          <h2 className="font-['Bebas_Neue'] text-2xl mb-4 text-yellow-500">Credits</h2>
          <div className="space-y-4">
            {credits.credits.map((credit, i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-white/5 rounded-lg border border-white/10">
                <Award className="w-10 h-10 text-yellow-500 flex-shrink-0" />
                <div>
                  <p className="font-bold text-lg">{credit.name}</p>
                  <p className="text-sm text-yellow-400 font-semibold">{credit.role}</p>
                  <p className="text-xs text-gray-400 mt-1">{credit.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      <Card className="bg-[#1A1A1A] border-white/10 mb-6">
        <CardContent className="p-6">
          <h2 className="font-['Bebas_Neue'] text-xl mb-3">Tecnologie Utilizzate</h2>
          <div className="flex flex-wrap gap-2">
            {credits.technologies.map((tech, i) => (
              <Badge key={i} className="bg-white/10 text-sm py-1">{tech}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Legal Section */}
      {credits.legal && (
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6">
            <h2 className="font-['Bebas_Neue'] text-xl mb-4 text-gray-300">Note Legali</h2>
            <div className="space-y-4 text-sm text-gray-400">
              <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
                <p className="text-yellow-400 font-semibold">{credits.legal.trademark}</p>
              </div>
              <p className="italic">{credits.legal.disclaimer}</p>
              <div className="border-t border-white/10 pt-3">
                <p className="font-semibold text-gray-300 mb-2">Diritti Riservati:</p>
                <ul className="list-disc list-inside space-y-1">
                  {credits.legal.rights.map((right, i) => (
                    <li key={i}>{right}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Special Thanks */}
      {credits.special_thanks && (
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6">
            <h2 className="font-['Bebas_Neue'] text-xl mb-3">Ringraziamenti Speciali</h2>
            <div className="flex flex-wrap gap-2">
              {credits.special_thanks.map((thanks, i) => (
                <Badge key={i} variant="outline" className="border-yellow-500/30 text-yellow-400">{thanks}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      <div className="text-center space-y-2 mt-8 pt-6 border-t border-white/10">
        <p className="text-yellow-500 font-semibold">{credits.copyright}</p>
        {credits.legal && (
          <p className="text-gray-500 text-xs">Proprietario: {credits.legal.owner}</p>
        )}
      </div>
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
          
          {/* Members */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center justify-between">
                <span className="flex items-center gap-2"><Users className="w-5 h-5" /> {t('members')}</span>
                {(majorData.my_role === 'founder' || majorData.my_role === 'vice') && (
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button size="sm" variant="outline" className="border-purple-500/30 text-purple-400">
                        <UserPlus className="w-4 h-4 mr-1" /> {t('invite')}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="bg-[#1A1A1A] border-white/10 w-64">
                      <p className="text-sm mb-2">{language === 'it' ? 'Invita utente' : 'Invite user'}</p>
                      <Input 
                        placeholder={language === 'it' ? 'Cerca utente...' : 'Search user...'} 
                        className="bg-black/30 border-white/10 h-8 text-xs mb-2"
                        onChange={(e) => setInviteUserId(e.target.value)}
                      />
                      <ScrollArea className="h-40">
                        {allUsers
                          .filter(u => !majorData.members?.some(m => m.user_id === u.id))
                          .filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase()))
                          .map(u => (
                          <Button key={u.id} variant="ghost" size="sm" className="w-full justify-between h-8 mb-1" onClick={() => inviteUser(u.id)}>
                            <span className="flex items-center gap-2">
                              <span className={`w-2 h-2 rounded-full ${u.is_online ? 'bg-green-500' : 'bg-gray-500'}`}></span>
                              <span className="text-xs">{u.nickname}</span>
                              <span className="text-[10px] text-gray-500">Lv.{u.level || 0}</span>
                            </span>
                            <Send className="w-3 h-3" />
                          </Button>
                        ))}
                        {allUsers.filter(u => !majorData.members?.some(m => m.user_id === u.id)).length === 0 && (
                          <p className="text-xs text-gray-500 text-center py-2">
                            {language === 'it' ? 'Nessun utente disponibile' : 'No users available'}
                          </p>
                        )}
                      </ScrollArea>
                    </PopoverContent>
                  </Popover>
                )}
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
function App() {
  return (
    <div className="min-h-screen bg-[#0F0F10]">
      <BrowserRouter>
        <AuthProvider>
          <LanguageProvider>
            <Toaster position="top-center" theme="dark" />
            <Routes>
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/films" element={<ProtectedRoute><MyFilms /></ProtectedRoute>} />
              <Route path="/films/:id" element={<ProtectedRoute><FilmDetail /></ProtectedRoute>} />
              <Route path="/create" element={<ProtectedRoute><FilmWizard /></ProtectedRoute>} />
              <Route path="/journal" element={<ProtectedRoute><CinemaJournal /></ProtectedRoute>} />
              <Route path="/social" element={<ProtectedRoute><SocialFeed /></ProtectedRoute>} />
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
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </LanguageProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
