import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import { 
  Film, Home, Users, MessageSquare, BarChart3, User, LogOut, Plus, Heart, 
  Globe, Calendar, DollarSign, Star, Clapperboard, Camera, MapPin, Sparkles,
  Send, Image, ChevronRight, ChevronDown, Menu, X, Settings, 
  Gamepad2, Trophy, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, Trash2,
  Check, XCircle, Newspaper, MessageCircle, Building, Building2, GraduationCap,
  Award, Crown, Landmark, Car, ShoppingBag, Ticket, Popcorn, ChevronUp, Lock
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
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data;
  };

  const register = async (data) => {
    const res = await api.post('/auth/register', data);
    localStorage.setItem('cineworld_token', res.data.access_token);
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

  useEffect(() => {
    api.get('/player/level-info').then(r => setLevelInfo(r.data)).catch(() => {});
  }, [api, user?.total_xp]);

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'dashboard' },
    { path: '/films', icon: Film, label: 'my_films' },
    { path: '/create', icon: Plus, label: 'create_film' },
    { path: '/infrastructure', icon: Building, label: 'infrastructure' },
    { path: '/tour', icon: MapPin, label: 'tour' },
    { path: '/journal', icon: Newspaper, label: 'cinema_journal' },
    { path: '/social', icon: Users, label: 'social' },
    { path: '/games', icon: Gamepad2, label: 'mini_games' },
    { path: '/leaderboard', icon: Trophy, label: 'leaderboard' },
    { path: '/chat', icon: MessageSquare, label: 'chat' },
  ];

  const gameDate = new Date().toLocaleDateString(language === 'it' ? 'it-IT' : language === 'es' ? 'es-ES' : language === 'fr' ? 'fr-FR' : language === 'de' ? 'de-DE' : 'en-US', {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
  });

  return (
    <nav className="fixed top-0 left-0 right-0 h-14 bg-[#0F0F10]/95 backdrop-blur-md border-b border-white/10 z-50">
      <div className="max-w-7xl mx-auto h-full px-3 flex items-center justify-between">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/dashboard')} data-testid="logo">
          <Clapperboard className="w-7 h-7 text-yellow-500" />
          <span className="font-['Bebas_Neue'] text-lg tracking-wide hidden sm:block">CineWorld</span>
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
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={e => setFormData({ ...formData, password: e.target.value })}
                  className="h-8 text-sm bg-black/20 border-white/10"
                  required
                  data-testid="password-input"
                />
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
const SkillBadge = ({ name, value, change }) => {
  const getBgColor = () => {
    if (change > 0) return 'bg-green-500/20 border-green-500/30';
    if (change < 0) return 'bg-red-500/20 border-red-500/30';
    return 'bg-white/5 border-white/10';
  };

  return (
    <div className={`flex items-center justify-between px-1.5 py-0.5 rounded border ${getBgColor()}`}>
      <span className="text-xs truncate mr-1">{name}</span>
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

// Dashboard Page
const Dashboard = () => {
  const { user, api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [stats, setStats] = useState(null);
  const [films, setFilms] = useState([]);
  const [challenges, setChallenges] = useState({ daily: [], weekly: [] });
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
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
          { label: 'Films', value: stats?.total_films || 0, icon: Film, color: 'yellow' },
          { label: 'Revenue', value: `$${((stats?.total_revenue || 0) / 1000000).toFixed(1)}M`, icon: DollarSign, color: 'green' },
          { label: 'Likes', value: stats?.total_likes || 0, icon: Heart, color: 'red' },
          { label: 'Quality', value: `${(stats?.average_quality || 0).toFixed(0)}%`, icon: Star, color: 'blue' }
        ].map((stat, i) => (
          <Card key={stat.label} className="bg-[#1A1A1A] border-white/5">
            <CardContent className="p-2.5 flex items-center gap-2">
              <stat.icon className={`w-5 h-5 text-${stat.color}-500`} />
              <div>
                <p className="text-lg font-bold">{stat.value}</p>
                <p className="text-xs text-gray-400">{stat.label}</p>
              </div>
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
  const [genres, setGenres] = useState({});
  const [actorRoles, setActorRoles] = useState([]);

  const [filmData, setFilmData] = useState({
    title: '', genre: 'action', subgenres: [], release_date: new Date().toISOString().split('T')[0],
    weeks_in_theater: 4, sponsor_id: null, equipment_package: 'Standard', locations: [], location_days: {},
    screenwriter_id: '', director_id: '', actors: [], extras_count: 50, extras_cost: 50000,
    screenplay: '', screenplay_source: 'manual', poster_url: '', poster_prompt: '', ad_duration_seconds: 0, ad_revenue: 0
  });
  const [releaseDate, setReleaseDate] = useState(new Date());
  const steps = [{num:1,title:'Title'},{num:2,title:'Sponsor'},{num:3,title:'Equipment'},{num:4,title:'Writer'},{num:5,title:'Director'},{num:6,title:'Cast'},{num:7,title:'Script'},{num:8,title:'Poster'},{num:9,title:'Ads'},{num:10,title:'Review'}];

  useEffect(() => { 
    api.get('/sponsors').then(r=>setSponsors(r.data)); 
    api.get('/locations').then(r=>setLocations(r.data)); 
    api.get('/equipment').then(r=>setEquipment(r.data));
    api.get('/genres').then(r=>setGenres(r.data));
    api.get('/actor-roles').then(r=>setActorRoles(r.data));
  }, [api]);
  
  const fetchPeople = async (type) => {
    const res = await api.get(`/${type}`);
    if(type==='screenwriters') setScreenwriters(res.data.screenwriters);
    else if(type==='directors') setDirectors(res.data.directors);
    else if(type==='actors') setActors(res.data.actors);
  };
  useEffect(() => { if(step===4)fetchPeople('screenwriters'); if(step===5)fetchPeople('directors'); if(step===6)fetchPeople('actors'); }, [step]);

  const generateScreenplay = async () => { setGenerating(true); try { const res = await api.post('/ai/screenplay', { genre: filmData.genre, title: filmData.title, language, tone: 'dramatic', length: 'medium' }); setFilmData({...filmData, screenplay: res.data.screenplay, screenplay_source: 'ai'}); toast.success('Screenplay generated!'); } catch(e) { toast.error('Failed'); } finally { setGenerating(false); }};
  const generatePoster = async () => { setGenerating(true); try { const res = await api.post('/ai/poster', { title: filmData.title, genre: filmData.genre, description: filmData.poster_prompt || filmData.title, style: 'cinematic' }); setFilmData({...filmData, poster_url: res.data.poster_url}); toast.success('Poster generated!'); } catch(e) { toast.error('Failed'); } finally { setGenerating(false); }};
  
  const calculateBudget = () => { const eq = equipment.find(e=>e.name===filmData.equipment_package)||{cost:0}; let loc=0; filmData.locations.forEach(l=>{const lo=locations.find(x=>x.name===l); if(lo)loc+=lo.cost_per_day*(filmData.location_days[l]||7);}); return eq.cost+loc+filmData.extras_cost; };
  const getSponsorBudget = () => { if(!filmData.sponsor_id)return 0; const s=sponsors.find(x=>x.name===filmData.sponsor_id); return s?.budget_offer||0; };
  
  const handleSubmit = async () => { setLoading(true); try { const res = await api.post('/films', {...filmData, release_date: releaseDate.toISOString()}); toast.success(`Film created! Opening: $${res.data.opening_day_revenue.toLocaleString()}`); updateFunds(user.funds - calculateBudget() + getSponsorBudget() + filmData.ad_revenue + res.data.opening_day_revenue); navigate(`/films/${res.data.id}`); } catch(e) { toast.error(e.response?.data?.detail||'Failed'); } finally { setLoading(false); }};

  const getRoleName = (roleId) => {
    const role = actorRoles.find(r => r.id === roleId);
    if (!role) return roleId;
    const langKey = `name_${language}`;
    return role[langKey] || role.name;
  };

  const PersonCard = ({ person, isSelected, onSelect, showRoleSelect = false, currentRole = null, onRoleChange = null }) => (
    <Card className={`bg-[#1A1A1A] border-2 cursor-pointer ${isSelected ? 'border-yellow-500' : 'border-white/10'}`} onClick={onSelect}>
      <CardContent className="p-2">
        <div className="flex items-center gap-2 mb-1.5">
          <Avatar className="w-10 h-10"><AvatarImage src={person.avatar_url} /><AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xs">{person.name[0]}</AvatarFallback></Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1">
              <h4 className="font-semibold text-xs truncate">{person.name}</h4>
              <span className="text-[10px] text-gray-400">{person.gender === 'female' ? '♀' : '♂'}</span>
              {person.is_star && <Star className="w-2.5 h-2.5 fill-yellow-500 text-yellow-500" />}
            </div>
            <p className="text-xs text-gray-400">{person.nationality} • {person.age}yo</p>
          </div>
          <p className="text-yellow-500 font-bold text-xs">${(person.cost_per_film/1000).toFixed(0)}K</p>
        </div>
        <div className="grid grid-cols-2 gap-0.5">{Object.entries(person.skills||{}).slice(0,4).map(([s,v])=><SkillBadge key={s} name={s} value={v} change={person.skill_changes?.[s]||0} />)}</div>
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
        return (<div className="space-y-2">
          <div className="flex justify-between items-center"><p className="text-xs text-gray-400"></p><Button variant="outline" size="sm" className="h-7" onClick={()=>fetchPeople(step===4?'screenwriters':'directors')}><RefreshCw className="w-3 h-3 mr-1" />Refresh</Button></div>
          <ScrollArea className="h-[280px]"><div className="space-y-1.5 pr-2">{people45.map(p=>{const isSel=selId===p.id;return<PersonCard key={p.id} person={p} isSelected={isSel} onSelect={()=>{if(step===4)setFilmData({...filmData,screenwriter_id:p.id});else setFilmData({...filmData,director_id:p.id});}} />;})}</div></ScrollArea>
        </div>);
      case 6:
        return (<div className="space-y-2">
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-400">Selected: {filmData.actors.length} actors</p>
            <Button variant="outline" size="sm" className="h-7" onClick={()=>fetchPeople('actors')}><RefreshCw className="w-3 h-3 mr-1" />Refresh</Button>
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
          <ScrollArea className="h-[200px]">
            <div className="space-y-1.5 pr-2">
              {actors.map(p => {
                const selectedActor = filmData.actors.find(a => a.actor_id === p.id);
                const isSel = !!selectedActor;
                return (
                  <PersonCard 
                    key={p.id} 
                    person={p} 
                    isSelected={isSel}
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
      case 7: return (<div className="space-y-3">
        <div className="flex gap-2"><Button variant={filmData.screenplay_source==='manual'?'default':'outline'} size="sm" onClick={()=>setFilmData({...filmData,screenplay_source:'manual'})} className={filmData.screenplay_source==='manual'?'bg-yellow-500 text-black':''}>Manual</Button><Button variant="outline" size="sm" onClick={generateScreenplay} disabled={generating||!filmData.title}><Sparkles className="w-3 h-3 mr-1" />{generating?'...':'AI Generate'}</Button></div>
        <Textarea value={filmData.screenplay} onChange={e=>setFilmData({...filmData,screenplay:e.target.value})} placeholder="Screenplay..." className="min-h-[200px] bg-black/20 border-white/10" />
      </div>);
      case 8: return (<div className="grid md:grid-cols-2 gap-3">
        <div className="space-y-2">
          <Textarea value={filmData.poster_prompt} onChange={e=>setFilmData({...filmData,poster_prompt:e.target.value})} placeholder="Describe poster..." className="min-h-[100px] bg-black/20 border-white/10" />
          <Button onClick={generatePoster} disabled={generating} className="w-full bg-yellow-500 text-black"><Sparkles className="w-3 h-3 mr-1" />{generating?'...':'Generate AI Poster'}</Button>
          <Input value={filmData.poster_url} onChange={e=>setFilmData({...filmData,poster_url:e.target.value})} placeholder="Or paste URL..." className="bg-black/20 border-white/10" />
        </div>
        <div className="aspect-[2/3] bg-[#1A1A1A] rounded border border-white/10 overflow-hidden">{filmData.poster_url?<img src={filmData.poster_url} alt="Poster" className="w-full h-full object-cover" />:<div className="w-full h-full flex items-center justify-center text-gray-500"><Image className="w-10 h-10 opacity-50" /></div>}</div>
      </div>);
      case 9: return (<div className="space-y-3">
        <p className="text-xs text-gray-400">Ads give immediate revenue but may reduce satisfaction.</p>
        <div><Label className="text-xs">Duration: {filmData.ad_duration_seconds}s</Label><Slider value={[filmData.ad_duration_seconds]} onValueChange={([v])=>setFilmData({...filmData,ad_duration_seconds:v,ad_revenue:v*5000})} min={0} max={180} step={15} /></div>
        <Card className="bg-[#1A1A1A] border-white/10"><CardContent className="p-3"><div className="flex justify-between"><span>Immediate Revenue</span><span className="text-green-400 text-lg">+${filmData.ad_revenue.toLocaleString()}</span></div>{filmData.ad_duration_seconds>60&&<p className="text-xs text-yellow-500 mt-1">⚠️ High ads may reduce satisfaction</p>}</CardContent></Card>
      </div>);
      case 10:
        const budget=calculateBudget(), sponsor=getSponsorBudget(), net=budget-sponsor-filmData.ad_revenue;
        return (<Card className="bg-[#1A1A1A] border-white/10"><CardHeader className="pb-2"><CardTitle className="font-['Bebas_Neue'] text-xl">{filmData.title}</CardTitle><CardDescription>{t(filmData.genre)} • {filmData.weeks_in_theater}w</CardDescription></CardHeader><CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs"><div><span className="text-gray-400">Release</span><p>{format(releaseDate,'PPP')}</p></div><div><span className="text-gray-400">Sponsor</span><p>{filmData.sponsor_id||'None'}</p></div><div><span className="text-gray-400">Equipment</span><p>{filmData.equipment_package}</p></div><div><span className="text-gray-400">Cast</span><p>{filmData.actors.length}+{filmData.extras_count}</p></div></div>
          <div className="pt-2 border-t border-white/10 space-y-1 text-sm"><div className="flex justify-between"><span>Budget</span><span className="text-red-400">-${budget.toLocaleString()}</span></div>{sponsor>0&&<div className="flex justify-between"><span>Sponsor</span><span className="text-green-400">+${sponsor.toLocaleString()}</span></div>}{filmData.ad_revenue>0&&<div className="flex justify-between"><span>Ads</span><span className="text-green-400">+${filmData.ad_revenue.toLocaleString()}</span></div>}<div className="flex justify-between font-bold pt-1 border-t border-white/10"><span>Net</span><span className={net>0?'text-red-400':'text-green-400'}>${Math.abs(net).toLocaleString()}</span></div></div>
        </CardContent></Card>);
      default: return null;
    }
  };

  const canProceed = () => { switch(step){ case 1:return filmData.title&&filmData.genre; case 3:return filmData.locations.length>0; case 4:return filmData.screenwriter_id; case 5:return filmData.director_id; case 6:return filmData.actors.length>0; case 7:return filmData.screenplay; default:return true; }};

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="film-wizard">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2 overflow-x-auto pb-1">{steps.map((s,i)=>(<div key={s.num} className="flex items-center"><div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step===s.num?'bg-yellow-500 text-black':step>s.num?'bg-green-500 text-white':'bg-gray-700 text-gray-400'}`}>{step>s.num?'✓':s.num}</div>{i<steps.length-1&&<div className={`w-3 h-0.5 mx-0.5 ${step>s.num?'bg-green-500':'bg-gray-700'}`} />}</div>))}</div>
        <h2 className="font-['Bebas_Neue'] text-xl">{steps[step-1].title}</h2>
      </div>
      <Card className="bg-[#1A1A1A] border-white/10"><CardContent className="p-3"><AnimatePresence mode="wait"><motion.div key={step} initial={{opacity:0,x:20}} animate={{opacity:1,x:0}} exit={{opacity:0,x:-20}}>{renderStep()}</motion.div></AnimatePresence></CardContent></Card>
      <div className="flex justify-between mt-3">
        <Button variant="outline" size="sm" onClick={()=>setStep(step-1)} disabled={step===1}>Previous</Button>
        {step<10?<Button size="sm" onClick={()=>setStep(step+1)} disabled={!canProceed()} className="bg-yellow-500 text-black">Next <ChevronRight className="w-3 h-3 ml-1" /></Button>:<Button size="sm" onClick={handleSubmit} disabled={loading||calculateBudget()-getSponsorBudget()-filmData.ad_revenue>user.funds} className="bg-yellow-500 text-black">{loading?'...':'Create Film'}</Button>}
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
  const navigate = useNavigate();

  const loadFilm = async () => {
    const id = window.location.pathname.split('/').pop(); 
    const [filmRes, rolesRes] = await Promise.all([
      api.get(`/films/${id}`),
      api.get('/actor-roles').catch(() => ({ data: [] }))
    ]);
    setFilm(filmRes.data);
    setActorRoles(rolesRes.data);
    
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
                  <Button onClick={processHourlyRevenue} disabled={processing} className="bg-green-600 hover:bg-green-500">
                    {processing ? <RefreshCw className="w-4 h-4 animate-spin mr-1" /> : <DollarSign className="w-4 h-4 mr-1" />}
                    Incassa Ora
                  </Button>
                  <Button variant="outline" onClick={checkStarDiscoveries} className="border-yellow-500/30 text-yellow-400">
                    <Star className="w-4 h-4 mr-1" /> Cerca Stelle
                  </Button>
                  <Button variant="outline" onClick={evolveSkills} className="border-blue-500/30 text-blue-400">
                    <TrendingUp className="w-4 h-4 mr-1" /> Evolvi Skill Cast
                  </Button>
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
  const [loading, setLoading] = useState(true);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [comment, setComment] = useState('');
  const navigate = useNavigate();

  useEffect(() => { 
    api.get('/films/cinema-journal')
      .then(r => setFilms(r.data.films))
      .finally(() => setLoading(false)); 
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
                      <button
                        key={u.id}
                        onClick={() => startDirectMessage(u.id)}
                        disabled={loadingDM === u.id}
                        className="w-full flex items-center gap-2 p-2 rounded hover:bg-white/5 text-left"
                        data-testid={`dm-user-${u.id}`}
                      >
                        <Avatar className="w-7 h-7">
                          <AvatarImage src={u.avatar_url} />
                          <AvatarFallback className="text-xs bg-yellow-500/20 text-yellow-500">{u.nickname?.[0]}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            <OnlineIndicator isOnline={true} />
                            <span className="text-xs font-semibold truncate">{u.nickname}</span>
                            {u.is_bot && u.is_moderator && <Badge className="h-4 px-1 text-[10px] bg-red-500/20 text-red-400">MOD</Badge>}
                            {u.is_bot && !u.is_moderator && <Badge className="h-4 px-1 text-[10px] bg-blue-500/20 text-blue-400">BOT</Badge>}
                          </div>
                          <p className="text-xs text-gray-500 truncate">{u.is_bot ? u.role : u.production_house_name}</p>
                        </div>
                        {!u.is_bot && (loadingDM === u.id ? (
                          <span className="text-xs text-gray-400">...</span>
                        ) : (
                          <MessageSquare className="w-3 h-3 text-gray-400" />
                        ))}
                      </button>
                    ))
                  )}
                  
                  {allUsers.filter(u => !onlineUsers.some(o => o.id === u.id)).length > 0 && (
                    <>
                      <p className="text-xs text-gray-400 mt-3 mb-2 px-1 border-t border-white/10 pt-2">All Users</p>
                      {allUsers.filter(u => !onlineUsers.some(o => o.id === u.id)).slice(0, 10).map(u => (
                        <button
                          key={u.id}
                          onClick={() => startDirectMessage(u.id)}
                          disabled={loadingDM === u.id}
                          className="w-full flex items-center gap-2 p-2 rounded hover:bg-white/5 text-left opacity-60"
                          data-testid={`dm-user-${u.id}`}
                        >
                          <Avatar className="w-7 h-7">
                            <AvatarImage src={u.avatar_url} />
                            <AvatarFallback className="text-xs bg-gray-500/20">{u.nickname?.[0]}</AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1">
                              <OnlineIndicator isOnline={false} />
                              <span className="text-xs truncate">{u.nickname}</span>
                            </div>
                          </div>
                          <MessageSquare className="w-3 h-3 text-gray-500" />
                        </button>
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

  const resetPlayer = async () => {
    try { await api.post('/auth/reset'); await refreshUser(); toast.success('Player resettato!'); navigate('/dashboard'); }
    catch (e) { toast.error('Errore'); }
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
          <AlertDialog>
            <AlertDialogTrigger asChild><Button variant="outline" className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10 h-8 sm:h-9 text-sm"><RefreshCw className="w-3 sm:w-3.5 h-3 sm:h-3.5 mr-2" /> Reset Player</Button></AlertDialogTrigger>
            <AlertDialogContent className="bg-[#1A1A1A] border-white/10 max-w-[90vw] sm:max-w-md"><AlertDialogHeader><AlertDialogTitle className="text-base">Reset Player?</AlertDialogTitle><AlertDialogDescription className="text-sm">This deletes all films, resets funds to $10M, and clears progress.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel className="h-8 text-sm">Cancel</AlertDialogCancel><AlertDialogAction onClick={resetPlayer} className="bg-red-500 h-8 text-sm">Reset</AlertDialogAction></AlertDialogFooter></AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>
      
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
  const { api, user } = useContext(AuthContext);
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
                  <Card key={infra.id} className="bg-white/5 border-white/10 cursor-pointer hover:border-yellow-500/50 transition-colors" onClick={() => navigate(`/infrastructure/${infra.id}`)}>
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
    </div>
  );
};

// Placeholder for infrastructure detail route
const INFRASTRUCTURE_TYPES = {};

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
              <Route path="/tour" element={<ProtectedRoute><CinemaTourPage /></ProtectedRoute>} />
              <Route path="/leaderboard" element={<ProtectedRoute><LeaderboardPage /></ProtectedRoute>} />
              <Route path="/player/:id" element={<ProtectedRoute><PlayerPublicProfile /></ProtectedRoute>} />
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
