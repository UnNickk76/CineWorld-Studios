import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import { 
  Film, Home, Users, MessageSquare, BarChart3, User, LogOut, Plus, Heart, 
  Globe, Calendar, DollarSign, Star, Clapperboard, Camera, MapPin, Sparkles,
  Send, Image, ChevronRight, ChevronDown, Menu, X, Settings, 
  Gamepad2, Trophy, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, Trash2,
  Check, XCircle
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
  const { user, logout } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslations();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'dashboard' },
    { path: '/films', icon: Film, label: 'my_films' },
    { path: '/create', icon: Plus, label: 'create_film' },
    { path: '/social', icon: Users, label: 'social' },
    { path: '/games', icon: Gamepad2, label: 'mini_games' },
    { path: '/chat', icon: MessageSquare, label: 'chat' },
    { path: '/statistics', icon: BarChart3, label: 'statistics' },
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
            <div className="flex items-center gap-1"><h4 className="font-semibold text-xs truncate">{person.name}</h4>{person.is_star && <Star className="w-2.5 h-2.5 fill-yellow-500 text-yellow-500" />}</div>
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

// My Films with Withdraw Option
const MyFilms = () => {
  const { api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [films, setFilms] = useState([]);
  const navigate = useNavigate();

  useEffect(() => { api.get('/films/my').then(r=>setFilms(r.data)); }, [api]);

  const withdrawFilm = async (filmId) => {
    try {
      await api.delete(`/films/${filmId}`);
      toast.success('Film withdrawn from theaters');
      setFilms(films.map(f => f.id === filmId ? { ...f, status: 'withdrawn' } : f));
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="my-films-page">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-['Bebas_Neue'] text-3xl">{t('my_films')}</h1>
        <Button size="sm" onClick={() => navigate('/create')} className="bg-yellow-500 text-black"><Plus className="w-3 h-3 mr-1" /> Create</Button>
      </div>
      {films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-8 text-center"><Film className="w-12 h-12 mx-auto mb-3 text-gray-600" /><h3 className="text-lg mb-2">No films yet</h3><Button onClick={() => navigate('/create')} className="bg-yellow-500 text-black">Create First Film</Button></Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {films.map(film => (
            <Card key={film.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden">
              <div className="aspect-[2/3] relative cursor-pointer" onClick={() => navigate(`/films/${film.id}`)}>
                <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} alt={film.title} className="w-full h-full object-cover" />
                <Badge className={`absolute top-2 right-2 ${film.status === 'in_theaters' ? 'bg-green-500' : film.status === 'withdrawn' ? 'bg-orange-500' : 'bg-gray-500'}`}>{film.status}</Badge>
              </div>
              <CardContent className="p-2">
                <h3 className="font-semibold text-sm truncate cursor-pointer" onClick={() => navigate(`/films/${film.id}`)}>{film.title}</h3>
                <div className="flex justify-between mt-1 text-xs">
                  <span className="text-gray-400"><Heart className="w-3 h-3 inline" /> {film.likes_count}</span>
                  <span className="text-green-400">${(film.total_revenue || 0).toLocaleString()}</span>
                </div>
                {film.status === 'in_theaters' && (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full mt-2 h-7 text-xs border-orange-500/30 text-orange-400 hover:bg-orange-500/10">
                        <Trash2 className="w-3 h-3 mr-1" /> Withdraw
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent className="bg-[#1A1A1A] border-white/10">
                      <AlertDialogHeader>
                        <AlertDialogTitle>Withdraw Film?</AlertDialogTitle>
                        <AlertDialogDescription>This will remove "{film.title}" from all theaters. You will stop earning revenue.</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={() => withdrawFilm(film.id)} className="bg-orange-500">Withdraw</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Film Detail
const FilmDetail = () => {
  const { api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [film, setFilm] = useState(null);
  const [expandedCountry, setExpandedCountry] = useState(null);

  useEffect(() => { const id = window.location.pathname.split('/').pop(); api.get(`/films/${id}`).then(r=>setFilm(r.data)); }, [api]);
  if (!film) return <div className="pt-16 p-4 text-center">Loading...</div>;

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="film-detail-page">
      <div className="grid lg:grid-cols-3 gap-4">
        <Card className="bg-[#1A1A1A] border-white/10 overflow-hidden">
          <div className="aspect-[2/3]"><img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'} alt={film.title} className="w-full h-full object-cover" /></div>
          <CardContent className="p-3">
            <h1 className="font-['Bebas_Neue'] text-xl mb-2">{film.title}</h1>
            <div className="flex gap-1.5 mb-2"><Badge className="bg-yellow-500/20 text-yellow-500 text-xs">{t(film.genre)}</Badge><Badge className={`text-xs ${film.status==='in_theaters'?'bg-green-500':film.status==='withdrawn'?'bg-orange-500':'bg-gray-500'}`}>{film.status}</Badge></div>
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
        <div className="lg:col-span-2">
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

// Profile Page
const ProfilePage = () => {
  const { api, user, refreshUser, logout } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslations();
  const navigate = useNavigate();
  const [avatars, setAvatars] = useState([]);
  const [selectedAvatar, setSelectedAvatar] = useState(user?.avatar_id);
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.get('/avatars').then(r => setAvatars(r.data)); }, [api]);

  const saveProfile = async () => {
    setSaving(true);
    try { await api.put('/auth/profile', { avatar_id: selectedAvatar, language }); await refreshUser(); toast.success('Saved!'); }
    catch (e) { toast.error('Failed'); }
    finally { setSaving(false); }
  };

  const resetPlayer = async () => {
    try { await api.post('/auth/reset'); await refreshUser(); toast.success('Player reset!'); navigate('/dashboard'); }
    catch (e) { toast.error('Failed'); }
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-2xl mx-auto" data-testid="profile-page">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4">{t('profile')}</h1>
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-4">
          <div className="flex items-center gap-3 mb-4">
            <Avatar className="w-16 h-16 border-2 border-yellow-500/30"><AvatarImage src={user?.avatar_url} /><AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xl">{user?.nickname?.[0]}</AvatarFallback></Avatar>
            <div><h2 className="text-lg font-bold">{user?.nickname}</h2><p className="text-sm text-gray-400">{user?.production_house_name}</p><p className="text-xs text-gray-500">Owner: {user?.owner_name}</p></div>
          </div>
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="text-center p-2 rounded bg-white/5"><p className="text-lg font-bold">{(user?.likeability_score || 50).toFixed(0)}</p><p className="text-xs text-gray-400">Like</p></div>
            <div className="text-center p-2 rounded bg-white/5"><p className="text-lg font-bold">{(user?.interaction_score || 50).toFixed(0)}</p><p className="text-xs text-gray-400">Social</p></div>
            <div className="text-center p-2 rounded bg-white/5"><p className="text-lg font-bold">{(user?.character_score || 50).toFixed(0)}</p><p className="text-xs text-gray-400">Char</p></div>
          </div>
          <div className="space-y-3 mb-4">
            <Label className="text-xs">Avatar</Label>
            <div className="grid grid-cols-5 gap-1.5">{avatars.map(a => (
              <button key={a.id} className={`p-0.5 rounded border-2 ${selectedAvatar === a.id ? 'border-yellow-500' : 'border-transparent hover:border-white/20'}`} onClick={() => setSelectedAvatar(a.id)}>
                <Avatar className="w-full aspect-square"><AvatarImage src={a.url} /></Avatar>
              </button>
            ))}</div>
          </div>
          <div className="space-y-2 mb-4">
            <Label className="text-xs">Language</Label>
            <Select value={language} onValueChange={setLanguage}><SelectTrigger className="bg-black/20 border-white/10 h-9"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="en">English</SelectItem><SelectItem value="it">Italiano</SelectItem><SelectItem value="es">Español</SelectItem><SelectItem value="fr">Français</SelectItem><SelectItem value="de">Deutsch</SelectItem></SelectContent></Select>
          </div>
          <Button onClick={saveProfile} disabled={saving} className="w-full bg-yellow-500 text-black mb-2 h-9">{saving ? 'Saving...' : 'Save Changes'}</Button>
          <AlertDialog>
            <AlertDialogTrigger asChild><Button variant="outline" className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10 h-9"><RefreshCw className="w-3.5 h-3.5 mr-2" /> Reset Player</Button></AlertDialogTrigger>
            <AlertDialogContent className="bg-[#1A1A1A] border-white/10"><AlertDialogHeader><AlertDialogTitle>Reset Player?</AlertDialogTitle><AlertDialogDescription>This deletes all films, resets funds to $10M, and clears progress.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction onClick={resetPlayer} className="bg-red-500">Reset</AlertDialogAction></AlertDialogFooter></AlertDialogContent>
          </AlertDialog>
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
              <Route path="/social" element={<ProtectedRoute><SocialFeed /></ProtectedRoute>} />
              <Route path="/games" element={<ProtectedRoute><MiniGamesPage /></ProtectedRoute>} />
              <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
              <Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
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
