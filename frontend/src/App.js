import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import { 
  Film, Home, Users, MessageSquare, BarChart3, User, LogOut, Plus, Heart, 
  Globe, Calendar, DollarSign, Star, Clapperboard, Camera, MapPin, Sparkles,
  Send, Image, ChevronRight, ChevronDown, Menu, X, Settings, 
  Gamepad2, Trophy, RefreshCw, AlertTriangle, TrendingUp, TrendingDown
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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from './components/ui/dialog';
import { Label } from './components/ui/label';
import { Calendar as CalendarComponent } from './components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './components/ui/popover';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './components/ui/alert-dialog';
import { Checkbox } from './components/ui/checkbox';
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

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('cineworld_token'));

  const api = axios.create({
    baseURL: API,
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

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
    <nav className="fixed top-0 left-0 right-0 h-16 bg-[#0F0F10]/95 backdrop-blur-md border-b border-white/10 z-50">
      <div className="max-w-7xl mx-auto h-full px-4 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')} data-testid="logo">
          <Clapperboard className="w-8 h-8 text-yellow-500" />
          <span className="font-['Bebas_Neue'] text-xl tracking-wide hidden sm:block">CineWorld Studio's</span>
        </div>

        <div className="hidden lg:flex items-center gap-1">
          {navItems.map(item => (
            <Button
              key={item.path}
              variant={location.pathname === item.path ? "default" : "ghost"}
              size="sm"
              className={`gap-1.5 ${location.pathname === item.path ? 'bg-yellow-500 text-black hover:bg-yellow-400' : 'text-gray-400 hover:text-white'}`}
              onClick={() => navigate(item.path)}
              data-testid={`nav-${item.label}`}
            >
              <item.icon className="w-4 h-4" />
              <span className="hidden xl:inline text-xs">{t(item.label)}</span>
            </Button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 text-xs text-gray-400">
            <Calendar className="w-3 h-3" />
            <span>{gameDate}</span>
          </div>

          <div className="flex items-center gap-1.5 bg-yellow-500/10 px-2 py-1 rounded-lg border border-yellow-500/20">
            <DollarSign className="w-3 h-3 text-yellow-500" />
            <span className="text-yellow-500 font-bold text-sm" data-testid="user-funds">
              ${user?.funds?.toLocaleString() || '0'}
            </span>
          </div>

          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="w-14 h-8 text-xs bg-transparent border-white/10" data-testid="language-selector">
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
              <Button variant="ghost" className="gap-2 p-1" data-testid="profile-menu">
                <Avatar className="w-8 h-8 border border-yellow-500/30">
                  <AvatarImage src={user?.avatar_url} />
                  <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xs">
                    {user?.nickname?.[0]?.toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 bg-[#1A1A1A] border-white/10">
              <div className="space-y-3">
                <div className="border-b border-white/10 pb-3">
                  <p className="font-semibold">{user?.nickname}</p>
                  <p className="text-sm text-gray-400">{user?.production_house_name}</p>
                </div>
                <Button variant="ghost" className="w-full justify-start gap-2" onClick={() => navigate('/profile')} data-testid="profile-btn">
                  <User className="w-4 h-4" /> {t('profile')}
                </Button>
                <Button variant="ghost" className="w-full justify-start gap-2 text-red-400 hover:text-red-300 hover:bg-red-500/10" onClick={logout} data-testid="logout-btn">
                  <LogOut className="w-4 h-4" /> {t('logout')}
                </Button>
              </div>
            </PopoverContent>
          </Popover>

          <Button variant="ghost" className="lg:hidden p-1" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
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
            className="lg:hidden absolute top-16 left-0 right-0 bg-[#0F0F10] border-b border-white/10 p-4"
          >
            <div className="grid grid-cols-2 gap-2">
              {navItems.map(item => (
                <Button
                  key={item.path}
                  variant={location.pathname === item.path ? "default" : "ghost"}
                  size="sm"
                  className={`gap-2 justify-start ${location.pathname === item.path ? 'bg-yellow-500 text-black' : ''}`}
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

// Auth Page with Age/Gender
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
    <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center p-4 cinema-gradient">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardHeader className="text-center space-y-4">
            <div className="flex justify-center">
              <Clapperboard className="w-14 h-14 text-yellow-500" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-3xl tracking-wide">CineWorld Studio's</CardTitle>
            <CardDescription>
              {isLogin ? 'Sign in to your production house' : 'Create your production empire'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="space-y-1">
                <Label className="text-xs">Email</Label>
                <Input
                  type="email"
                  placeholder="producer@cineworld.com"
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                  className="h-9 bg-black/20 border-white/10"
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
                  className="h-9 bg-black/20 border-white/10"
                  required
                  data-testid="password-input"
                />
              </div>

              {!isLogin && (
                <>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <Label className="text-xs">{t('age')} *</Label>
                      <Input
                        type="number"
                        min="18"
                        max="120"
                        placeholder="18+"
                        value={formData.age}
                        onChange={e => setFormData({ ...formData, age: e.target.value })}
                        className="h-9 bg-black/20 border-white/10"
                        required
                        data-testid="age-input"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">{t('gender')} *</Label>
                      <Select value={formData.gender} onValueChange={v => setFormData({ ...formData, gender: v })}>
                        <SelectTrigger className="h-9 bg-black/20 border-white/10" data-testid="gender-select">
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
                      className="h-9 bg-black/20 border-white/10"
                      required
                      data-testid="nickname-input"
                    />
                  </div>
                  
                  <div className="space-y-1">
                    <Label className="text-xs">Production House Name</Label>
                    <Input
                      placeholder="e.g., Paramount Pictures"
                      value={formData.production_house_name}
                      onChange={e => setFormData({ ...formData, production_house_name: e.target.value })}
                      className="h-9 bg-black/20 border-white/10"
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
                      className="h-9 bg-black/20 border-white/10"
                      required
                      data-testid="owner-name-input"
                    />
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs">Language</Label>
                    <Select value={language} onValueChange={(v) => { setLanguage(v); setFormData({ ...formData, language: v }); }}>
                      <SelectTrigger className="h-9 bg-black/20 border-white/10" data-testid="register-language-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="it">Italiano</SelectItem>
                        <SelectItem value="es">Español</SelectItem>
                        <SelectItem value="fr">Français</SelectItem>
                        <SelectItem value="de">Deutsch</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Adult Warning */}
                  <Card className="bg-red-500/10 border-red-500/30">
                    <CardContent className="p-3">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-red-400">
                          {t('adult_warning')}
                        </p>
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
                      I confirm I am 18+ years old and agree to the community guidelines. I understand that sharing inappropriate content involving minors is prohibited.
                    </label>
                  </div>
                </>
              )}

              <Button 
                type="submit" 
                className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold uppercase tracking-wider h-10"
                disabled={loading || (!isLogin && !acceptedTerms)}
                data-testid="auth-submit-btn"
              >
                {loading ? 'Loading...' : isLogin ? 'Sign In' : 'Create Account'}
              </Button>
            </form>

            <div className="mt-4 text-center">
              <button
                type="button"
                className="text-gray-400 hover:text-white text-sm"
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

// Skill Display Component with color changes
const SkillBadge = ({ name, value, change }) => {
  const getChangeIcon = () => {
    if (change > 0) return <TrendingUp className="w-3 h-3 text-green-500" />;
    if (change < 0) return <TrendingDown className="w-3 h-3 text-red-500" />;
    return null;
  };

  const getBgColor = () => {
    if (change > 0) return 'bg-green-500/20 border-green-500/30';
    if (change < 0) return 'bg-red-500/20 border-red-500/30';
    return 'bg-white/5 border-white/10';
  };

  return (
    <div className={`flex items-center justify-between px-2 py-1 rounded border ${getBgColor()}`}>
      <span className="text-xs truncate">{name}</span>
      <div className="flex items-center gap-1">
        <span className={`font-bold text-sm ${change > 0 ? 'text-green-500' : change < 0 ? 'text-red-500' : ''}`}>
          {value}
        </span>
        {getChangeIcon()}
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
    <div className="pt-20 pb-8 px-4 max-w-7xl mx-auto" data-testid="dashboard">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="font-['Bebas_Neue'] text-4xl md:text-5xl mb-1">
          {t('welcome')}, <span className="text-yellow-500">{user?.nickname}</span>
        </h1>
        <p className="text-gray-400">{user?.production_house_name}</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {[
          { label: 'Total Films', value: stats?.total_films || 0, icon: Film, color: 'yellow' },
          { label: 'Box Office', value: `$${(stats?.total_revenue || 0).toLocaleString()}`, icon: DollarSign, color: 'green' },
          { label: 'Total Likes', value: stats?.total_likes || 0, icon: Heart, color: 'red' },
          { label: 'Avg Quality', value: `${(stats?.average_quality || 0).toFixed(1)}%`, icon: Star, color: 'blue' }
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card className="bg-[#1A1A1A] border-white/5 card-hover">
              <CardContent className="p-3 flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-${stat.color}-500/10`}>
                  <stat.icon className={`w-5 h-5 text-${stat.color}-500`} />
                </div>
                <div>
                  <p className="text-xl font-bold">{stat.value}</p>
                  <p className="text-xs text-gray-400">{stat.label}</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Player Scores */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <Card className="bg-[#1A1A1A] border-white/5">
          <CardContent className="p-3 text-center">
            <Heart className="w-5 h-5 mx-auto mb-1 text-pink-500" />
            <p className="text-lg font-bold">{(stats?.likeability_score || 50).toFixed(0)}</p>
            <p className="text-xs text-gray-400">Likeability</p>
          </CardContent>
        </Card>
        <Card className="bg-[#1A1A1A] border-white/5">
          <CardContent className="p-3 text-center">
            <Users className="w-5 h-5 mx-auto mb-1 text-blue-500" />
            <p className="text-lg font-bold">{(stats?.interaction_score || 50).toFixed(0)}</p>
            <p className="text-xs text-gray-400">Interaction</p>
          </CardContent>
        </Card>
        <Card className="bg-[#1A1A1A] border-white/5">
          <CardContent className="p-3 text-center">
            <Star className="w-5 h-5 mx-auto mb-1 text-yellow-500" />
            <p className="text-lg font-bold">{(stats?.character_score || 50).toFixed(0)}</p>
            <p className="text-xs text-gray-400">Character</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <Card className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border-yellow-500/20 cursor-pointer card-hover" onClick={() => navigate('/create')} data-testid="quick-create-film">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-3 bg-yellow-500 rounded-xl">
              <Plus className="w-6 h-6 text-black" />
            </div>
            <div>
              <h3 className="font-['Bebas_Neue'] text-xl">{t('create_film')}</h3>
              <p className="text-xs text-gray-400">Start your next blockbuster</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/5 border-blue-500/20 cursor-pointer card-hover" onClick={() => navigate('/games')} data-testid="quick-games">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-3 bg-blue-500 rounded-xl">
              <Gamepad2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-['Bebas_Neue'] text-xl">{t('mini_games')}</h3>
              <p className="text-xs text-gray-400">Earn rewards while waiting</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/20 to-purple-600/5 border-purple-500/20 cursor-pointer card-hover" onClick={() => navigate('/social')} data-testid="quick-social">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-3 bg-purple-500 rounded-xl">
              <Globe className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-['Bebas_Neue'] text-xl">Explore Films</h3>
              <p className="text-xs text-gray-400">Discover what others are creating</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Challenges */}
      <Card className="bg-[#1A1A1A] border-white/5 mb-6">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-500" /> {t('challenges')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="daily">
            <TabsList className="mb-3">
              <TabsTrigger value="daily" className="text-xs">{t('daily')}</TabsTrigger>
              <TabsTrigger value="weekly" className="text-xs">{t('weekly')}</TabsTrigger>
            </TabsList>
            <TabsContent value="daily">
              <div className="grid gap-2">
                {challenges.daily.slice(0, 3).map(c => (
                  <div key={c.id} className="flex items-center justify-between p-2 rounded bg-white/5">
                    <div>
                      <p className="text-sm font-semibold">{c.name}</p>
                      <p className="text-xs text-gray-400">{c.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-400">{c.current}/{c.target}</p>
                      <p className="text-sm text-yellow-500">${c.reward.toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>
            <TabsContent value="weekly">
              <div className="grid gap-2">
                {challenges.weekly.slice(0, 3).map(c => (
                  <div key={c.id} className="flex items-center justify-between p-2 rounded bg-white/5">
                    <div>
                      <p className="text-sm font-semibold">{c.name}</p>
                      <p className="text-xs text-gray-400">{c.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-400">{c.current}/{c.target}</p>
                      <p className="text-sm text-yellow-500">${c.reward.toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Recent Films */}
      {films.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-['Bebas_Neue'] text-2xl">{t('my_films')}</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/films')} data-testid="view-all-films">
              View All <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {films.map((film, i) => (
              <motion.div
                key={film.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
              >
                <Card className="bg-[#1A1A1A] border-white/5 overflow-hidden group cursor-pointer card-hover" onClick={() => navigate(`/films/${film.id}`)}>
                  <div className="aspect-[2/3] relative">
                    <img 
                      src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} 
                      alt={film.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="poster-overlay" />
                  </div>
                  <CardContent className="p-3">
                    <h3 className="font-semibold text-sm truncate">{film.title}</h3>
                    <div className="flex items-center justify-between mt-1 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Heart className="w-3 h-3" /> {film.likes_count}
                      </span>
                      <span className="text-green-400">${(film.total_revenue || 0).toLocaleString()}</span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Mini Games Page
const MiniGamesPage = () => {
  const { api, refreshUser } = useContext(AuthContext);
  const { t } = useTranslations();
  const [games, setGames] = useState([]);
  const [challenges, setChallenges] = useState({ daily: [], weekly: [] });
  const [playing, setPlaying] = useState(null);
  const [gameScore, setGameScore] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      const [gamesRes, challengesRes] = await Promise.all([
        api.get('/minigames'),
        api.get('/challenges')
      ]);
      setGames(gamesRes.data);
      setChallenges(challengesRes.data);
    };
    fetchData();
  }, [api]);

  const playGame = async (game) => {
    setPlaying(game);
    setGameScore(0);
    
    // Simulate game playing
    await new Promise(resolve => setTimeout(resolve, 2000));
    const score = Math.floor(Math.random() * 100);
    setGameScore(score);
    
    try {
      const res = await api.post(`/minigames/${game.id}/play`, {
        game_id: game.id,
        score: score,
        correct_answers: Math.floor(score / 10)
      });
      toast.success(`You earned $${res.data.reward.toLocaleString()}!`);
      refreshUser();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Game error');
    }
    
    setPlaying(null);
  };

  const claimChallenge = async (challengeId, type) => {
    try {
      const res = await api.post(`/challenges/${challengeId}/claim?challenge_type=${type}`);
      toast.success(`Claimed $${res.data.reward.toLocaleString()}!`);
      refreshUser();
      // Refresh challenges
      const challengesRes = await api.get('/challenges');
      setChallenges(challengesRes.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Claim failed');
    }
  };

  return (
    <div className="pt-20 pb-8 px-4 max-w-6xl mx-auto" data-testid="minigames-page">
      <h1 className="font-['Bebas_Neue'] text-4xl mb-6">{t('mini_games')}</h1>

      {/* Games Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {games.map(game => (
          <Card key={game.id} className="bg-[#1A1A1A] border-white/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-yellow-500/20 rounded-lg">
                  <Gamepad2 className="w-6 h-6 text-yellow-500" />
                </div>
                <div>
                  <h3 className="font-semibold">{game.name}</h3>
                  <p className="text-xs text-gray-400">{game.description}</p>
                </div>
              </div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-gray-400">Reward:</span>
                <span className="text-sm text-yellow-500">
                  ${game.reward_min.toLocaleString()} - ${game.reward_max.toLocaleString()}
                </span>
              </div>
              <Button 
                onClick={() => playGame(game)}
                disabled={playing === game}
                className="w-full bg-yellow-500 text-black hover:bg-yellow-400"
                data-testid={`play-${game.id}`}
              >
                {playing === game ? 'Playing...' : 'Play Now'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Challenges */}
      <h2 className="font-['Bebas_Neue'] text-3xl mb-4 flex items-center gap-2">
        <Trophy className="w-6 h-6 text-yellow-500" /> {t('challenges')}
      </h2>
      
      <Tabs defaultValue="daily" className="space-y-4">
        <TabsList>
          <TabsTrigger value="daily">{t('daily')}</TabsTrigger>
          <TabsTrigger value="weekly">{t('weekly')}</TabsTrigger>
        </TabsList>

        <TabsContent value="daily">
          <div className="grid gap-3">
            {challenges.daily.map(c => (
              <Card key={c.id} className="bg-[#1A1A1A] border-white/5">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold">{c.name}</h4>
                    <p className="text-sm text-gray-400">{c.description}</p>
                    <div className="mt-2">
                      <Progress value={(c.current / c.target) * 100} className="h-2" />
                      <p className="text-xs text-gray-400 mt-1">{c.current} / {c.target}</p>
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-yellow-500 font-bold">${c.reward.toLocaleString()}</p>
                    {c.completed && !c.claimed && (
                      <Button 
                        size="sm" 
                        onClick={() => claimChallenge(c.id, 'daily')}
                        className="mt-2 bg-green-500 hover:bg-green-400"
                      >
                        Claim
                      </Button>
                    )}
                    {c.claimed && <Badge className="mt-2 bg-gray-500">Claimed</Badge>}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="weekly">
          <div className="grid gap-3">
            {challenges.weekly.map(c => (
              <Card key={c.id} className="bg-[#1A1A1A] border-white/5">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold">{c.name}</h4>
                    <p className="text-sm text-gray-400">{c.description}</p>
                    <div className="mt-2">
                      <Progress value={(c.current / c.target) * 100} className="h-2" />
                      <p className="text-xs text-gray-400 mt-1">{c.current} / {c.target}</p>
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-yellow-500 font-bold">${c.reward.toLocaleString()}</p>
                    {c.completed && !c.claimed && (
                      <Button 
                        size="sm" 
                        onClick={() => claimChallenge(c.id, 'weekly')}
                        className="mt-2 bg-green-500 hover:bg-green-400"
                      >
                        Claim
                      </Button>
                    )}
                    {c.claimed && <Badge className="mt-2 bg-gray-500">Claimed</Badge>}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Film Wizard (simplified for brevity - keep same structure as before)
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

  const [filmData, setFilmData] = useState({
    title: '',
    genre: 'action',
    release_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    weeks_in_theater: 4,
    sponsor_id: null,
    equipment_package: 'Standard',
    locations: [],
    location_days: {},
    screenwriter_id: '',
    director_id: '',
    actors: [],
    extras_count: 50,
    extras_cost: 50000,
    screenplay: '',
    screenplay_source: 'manual',
    poster_url: '',
    poster_prompt: '',
    ad_duration_seconds: 0,
    ad_revenue: 0
  });

  const [releaseDate, setReleaseDate] = useState(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000));

  const steps = [
    { num: 1, title: 'Title & Genre', icon: Film },
    { num: 2, title: 'Sponsor', icon: DollarSign },
    { num: 3, title: 'Equipment', icon: Camera },
    { num: 4, title: 'Screenwriter', icon: Sparkles },
    { num: 5, title: 'Director', icon: Clapperboard },
    { num: 6, title: 'Cast', icon: Users },
    { num: 7, title: 'Screenplay', icon: Film },
    { num: 8, title: 'Poster', icon: Image },
    { num: 9, title: 'Ads', icon: DollarSign },
    { num: 10, title: 'Review', icon: Star }
  ];

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sponsorsRes, locationsRes, equipmentRes] = await Promise.all([
          api.get('/sponsors'),
          api.get('/locations'),
          api.get('/equipment')
        ]);
        setSponsors(sponsorsRes.data);
        setLocations(locationsRes.data);
        setEquipment(equipmentRes.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, [api]);

  const fetchPeople = async (type) => {
    try {
      const res = await api.get(`/${type}`, { params: { lang: language } });
      if (type === 'screenwriters') setScreenwriters(res.data.screenwriters);
      else if (type === 'directors') setDirectors(res.data.directors);
      else if (type === 'actors') setActors(res.data.actors);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (step === 4) fetchPeople('screenwriters');
    if (step === 5) fetchPeople('directors');
    if (step === 6) fetchPeople('actors');
  }, [step]);

  const generateScreenplay = async () => {
    setGenerating(true);
    try {
      const res = await api.post('/ai/screenplay', {
        genre: filmData.genre,
        title: filmData.title,
        language: language,
        tone: 'dramatic',
        length: 'medium'
      });
      setFilmData({ ...filmData, screenplay: res.data.screenplay, screenplay_source: 'ai' });
      toast.success('Screenplay generated!');
    } catch (err) {
      toast.error('Failed to generate screenplay');
    } finally {
      setGenerating(false);
    }
  };

  const generatePoster = async () => {
    setGenerating(true);
    try {
      const res = await api.post('/ai/poster', {
        title: filmData.title,
        genre: filmData.genre,
        description: filmData.poster_prompt || filmData.title,
        style: 'cinematic'
      });
      setFilmData({ ...filmData, poster_url: res.data.poster_url });
      toast.success('Poster generated!');
    } catch (err) {
      toast.error('Failed to generate poster');
    } finally {
      setGenerating(false);
    }
  };

  const calculateBudget = () => {
    const eq = equipment.find(e => e.name === filmData.equipment_package) || { cost: 0 };
    let locCost = 0;
    filmData.locations.forEach(locName => {
      const loc = locations.find(l => l.name === locName);
      if (loc) {
        locCost += loc.cost_per_day * (filmData.location_days[locName] || 7);
      }
    });
    return eq.cost + locCost + filmData.extras_cost;
  };

  const getSponsorBudget = () => {
    if (!filmData.sponsor_id) return 0;
    const sponsor = sponsors.find(s => s.name === filmData.sponsor_id);
    return sponsor?.budget_offer || 0;
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await api.post('/films', {
        ...filmData,
        release_date: releaseDate.toISOString()
      });
      toast.success(`Film created! Opening day revenue: $${res.data.opening_day_revenue.toLocaleString()}`);
      updateFunds(user.funds - calculateBudget() + getSponsorBudget() + filmData.ad_revenue + res.data.opening_day_revenue);
      navigate(`/films/${res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create film');
    } finally {
      setLoading(false);
    }
  };

  // Render person card with skills
  const PersonCard = ({ person, isSelected, onSelect, type }) => (
    <Card 
      className={`bg-[#1A1A1A] border-2 cursor-pointer transition-colors ${isSelected ? 'border-yellow-500' : 'border-white/10 hover:border-white/20'}`}
      onClick={onSelect}
    >
      <CardContent className="p-3">
        <div className="flex items-center gap-3 mb-2">
          <Avatar className="w-12 h-12 border-2 border-white/10">
            <AvatarImage src={person.avatar_url} />
            <AvatarFallback className="bg-yellow-500/20 text-yellow-500">{person.name[0]}</AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1">
              <h4 className="font-semibold text-sm truncate">{person.name}</h4>
              {person.is_star && <Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />}
            </div>
            <p className="text-xs text-gray-400">{person.nationality} • Age {person.age}</p>
          </div>
          <p className="text-yellow-500 font-bold text-sm">${(person.cost_per_film || 0).toLocaleString()}</p>
        </div>
        <div className="grid grid-cols-2 gap-1">
          {Object.entries(person.skills || {}).slice(0, 4).map(([skill, value]) => (
            <SkillBadge 
              key={skill} 
              name={skill} 
              value={value} 
              change={person.skill_changes?.[skill] || 0} 
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );

  const renderStepContent = () => {
    switch(step) {
      case 1:
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Film Title *</Label>
              <Input
                value={filmData.title}
                onChange={e => setFilmData({ ...filmData, title: e.target.value })}
                placeholder="Enter your film title..."
                className="h-12 bg-black/20 border-white/10"
                data-testid="film-title-input"
              />
            </div>
            <div className="space-y-2">
              <Label>{t('genre')} *</Label>
              <Select value={filmData.genre} onValueChange={v => setFilmData({ ...filmData, genre: v })}>
                <SelectTrigger className="h-10 bg-black/20 border-white/10" data-testid="genre-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  {GENRES.map(g => (
                    <SelectItem key={g} value={g} data-testid={`genre-option-${g}`}>{t(g)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>{t('release_date')} *</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start h-10 bg-black/20 border-white/10">
                    <Calendar className="mr-2 h-4 w-4" />
                    {format(releaseDate, 'PPP')}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0 bg-[#1A1A1A] border-white/10">
                  <CalendarComponent
                    mode="single"
                    selected={releaseDate}
                    onSelect={setReleaseDate}
                    disabled={(date) => date < new Date()}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
            <div className="space-y-2">
              <Label>Weeks in Theater: {filmData.weeks_in_theater}</Label>
              <Slider
                value={[filmData.weeks_in_theater]}
                onValueChange={([v]) => setFilmData({ ...filmData, weeks_in_theater: v })}
                min={1}
                max={12}
                step={1}
              />
              <p className="text-xs text-gray-400">Actual duration may vary based on audience satisfaction</p>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-3">
            <Card 
              className={`bg-[#1A1A1A] border-2 cursor-pointer ${!filmData.sponsor_id ? 'border-yellow-500' : 'border-white/10'}`}
              onClick={() => setFilmData({ ...filmData, sponsor_id: null })}
            >
              <CardContent className="p-3 flex items-center gap-3">
                <X className="w-5 h-5 text-gray-400" />
                <span>No Sponsor</span>
              </CardContent>
            </Card>
            {sponsors.map(sponsor => (
              <Card 
                key={sponsor.name}
                className={`bg-[#1A1A1A] border-2 cursor-pointer ${filmData.sponsor_id === sponsor.name ? 'border-yellow-500' : 'border-white/10'}`}
                onClick={() => setFilmData({ ...filmData, sponsor_id: sponsor.name })}
              >
                <CardContent className="p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <DollarSign className="w-5 h-5 text-yellow-500" />
                    <span>{sponsor.name}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-green-400">+${sponsor.budget_offer.toLocaleString()}</p>
                    <p className="text-xs text-red-400">-{sponsor.revenue_share}% share</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Equipment Package</Label>
              <div className="grid gap-2">
                {equipment.map(eq => (
                  <Card 
                    key={eq.name}
                    className={`bg-[#1A1A1A] border-2 cursor-pointer ${filmData.equipment_package === eq.name ? 'border-yellow-500' : 'border-white/10'}`}
                    onClick={() => setFilmData({ ...filmData, equipment_package: eq.name })}
                  >
                    <CardContent className="p-3 flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{eq.name}</p>
                        <p className="text-xs text-gray-400">+{eq.quality_bonus}% quality</p>
                      </div>
                      <p className="text-yellow-500">${eq.cost.toLocaleString()}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Label>Filming Locations</Label>
              <div className="grid sm:grid-cols-2 gap-2">
                {locations.map(loc => {
                  const isSelected = filmData.locations.includes(loc.name);
                  return (
                    <Card 
                      key={loc.name}
                      className={`bg-[#1A1A1A] border-2 cursor-pointer ${isSelected ? 'border-yellow-500' : 'border-white/10'}`}
                      onClick={() => {
                        if (isSelected) {
                          setFilmData({ ...filmData, locations: filmData.locations.filter(l => l !== loc.name) });
                        } else {
                          setFilmData({ 
                            ...filmData, 
                            locations: [...filmData.locations, loc.name],
                            location_days: { ...filmData.location_days, [loc.name]: 7 }
                          });
                        }
                      }}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm">{loc.name}</span>
                          <span className="text-xs text-yellow-500">${loc.cost_per_day.toLocaleString()}/day</span>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          </div>
        );

      case 4:
      case 5:
      case 6:
        const people = step === 4 ? screenwriters : step === 5 ? directors : actors;
        const selectedId = step === 4 ? filmData.screenwriter_id : step === 5 ? filmData.director_id : null;
        const personType = step === 4 ? 'screenwriter' : step === 5 ? 'director' : 'actor';
        
        return (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-400">
                {step === 6 ? `Selected: ${filmData.actors.length} actors` : 'Choose your team member'}
              </p>
              <Button variant="outline" size="sm" onClick={() => fetchPeople(personType + 's')}>
                <RefreshCw className="w-3 h-3 mr-1" /> Refresh
              </Button>
            </div>
            <ScrollArea className="h-[350px]">
              <div className="grid gap-2 pr-2">
                {people.map(person => {
                  const isSelected = step === 6 
                    ? filmData.actors.some(a => a.actor_id === person.id)
                    : selectedId === person.id;
                  
                  return (
                    <PersonCard 
                      key={person.id}
                      person={person}
                      isSelected={isSelected}
                      type={personType}
                      onSelect={() => {
                        if (step === 4) {
                          setFilmData({ ...filmData, screenwriter_id: person.id });
                        } else if (step === 5) {
                          setFilmData({ ...filmData, director_id: person.id });
                        } else {
                          if (isSelected) {
                            setFilmData({ ...filmData, actors: filmData.actors.filter(a => a.actor_id !== person.id) });
                          } else {
                            setFilmData({ ...filmData, actors: [...filmData.actors, { actor_id: person.id, role: 'Lead' }] });
                          }
                        }
                      }}
                    />
                  );
                })}
              </div>
            </ScrollArea>
            {step === 6 && (
              <div className="space-y-2 pt-3 border-t border-white/10">
                <Label>Extras: {filmData.extras_count}</Label>
                <Slider
                  value={[filmData.extras_count]}
                  onValueChange={([v]) => setFilmData({ ...filmData, extras_count: v, extras_cost: v * 1000 })}
                  min={0}
                  max={500}
                  step={10}
                />
                <p className="text-xs text-gray-400">Cost: ${filmData.extras_cost.toLocaleString()}</p>
              </div>
            )}
          </div>
        );

      case 7:
        return (
          <div className="space-y-4">
            <div className="flex gap-2">
              <Button 
                variant={filmData.screenplay_source === 'manual' ? 'default' : 'outline'}
                onClick={() => setFilmData({ ...filmData, screenplay_source: 'manual' })}
                className={filmData.screenplay_source === 'manual' ? 'bg-yellow-500 text-black' : ''}
              >
                Write Manually
              </Button>
              <Button 
                variant={filmData.screenplay_source === 'ai' ? 'default' : 'outline'}
                onClick={generateScreenplay}
                disabled={generating || !filmData.title}
                className={filmData.screenplay_source === 'ai' ? 'bg-yellow-500 text-black' : ''}
              >
                <Sparkles className="w-4 h-4 mr-1" />
                {generating ? 'Generating...' : 'AI Generate'}
              </Button>
            </div>
            <Textarea
              value={filmData.screenplay}
              onChange={e => setFilmData({ ...filmData, screenplay: e.target.value })}
              placeholder="Write your screenplay..."
              className="min-h-[250px] bg-black/20 border-white/10"
            />
          </div>
        );

      case 8:
        return (
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <Label>Poster Guidelines</Label>
              <Textarea
                value={filmData.poster_prompt}
                onChange={e => setFilmData({ ...filmData, poster_prompt: e.target.value })}
                placeholder="Describe your poster..."
                className="min-h-[120px] bg-black/20 border-white/10"
              />
              <Button 
                onClick={generatePoster}
                disabled={generating}
                className="w-full bg-yellow-500 text-black hover:bg-yellow-400"
              >
                <Sparkles className="w-4 h-4 mr-1" />
                {generating ? 'Generating...' : 'Generate AI Poster'}
              </Button>
              <Input
                value={filmData.poster_url}
                onChange={e => setFilmData({ ...filmData, poster_url: e.target.value })}
                placeholder="Or paste URL..."
                className="bg-black/20 border-white/10"
              />
            </div>
            <div className="aspect-[2/3] bg-[#1A1A1A] rounded-lg overflow-hidden border border-white/10">
              {filmData.poster_url ? (
                <img src={filmData.poster_url} alt="Poster" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-500">
                  <Image className="w-12 h-12 opacity-50" />
                </div>
              )}
            </div>
          </div>
        );

      case 9:
        return (
          <div className="space-y-4">
            <p className="text-gray-400 text-sm">Add in-film ads for immediate revenue. Too many may reduce satisfaction.</p>
            <div className="space-y-2">
              <Label>Ad Duration: {filmData.ad_duration_seconds}s</Label>
              <Slider
                value={[filmData.ad_duration_seconds]}
                onValueChange={([v]) => setFilmData({ ...filmData, ad_duration_seconds: v, ad_revenue: v * 5000 })}
                min={0}
                max={180}
                step={15}
              />
            </div>
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-4">
                <div className="flex justify-between items-center">
                  <span>Immediate Revenue</span>
                  <span className="text-xl text-green-400">+${filmData.ad_revenue.toLocaleString()}</span>
                </div>
                {filmData.ad_duration_seconds > 60 && (
                  <p className="text-xs text-yellow-500 mt-2">⚠️ High ad duration may reduce audience satisfaction</p>
                )}
              </CardContent>
            </Card>
          </div>
        );

      case 10:
        const totalBudget = calculateBudget();
        const sponsorBudget = getSponsorBudget();
        const netCost = totalBudget - sponsorBudget - filmData.ad_revenue;
        
        return (
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader>
              <CardTitle className="font-['Bebas_Neue'] text-2xl">{filmData.title}</CardTitle>
              <CardDescription>{t(filmData.genre)} • {filmData.weeks_in_theater} weeks</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-400">Release</p>
                  <p>{format(releaseDate, 'PPP')}</p>
                </div>
                <div>
                  <p className="text-gray-400">Sponsor</p>
                  <p>{filmData.sponsor_id || 'None'}</p>
                </div>
                <div>
                  <p className="text-gray-400">Equipment</p>
                  <p>{filmData.equipment_package}</p>
                </div>
                <div>
                  <p className="text-gray-400">Cast</p>
                  <p>{filmData.actors.length} actors + {filmData.extras_count} extras</p>
                </div>
              </div>
              <div className="pt-3 border-t border-white/10 space-y-1">
                <div className="flex justify-between"><span>Budget</span><span className="text-red-400">-${totalBudget.toLocaleString()}</span></div>
                {sponsorBudget > 0 && <div className="flex justify-between"><span>Sponsor</span><span className="text-green-400">+${sponsorBudget.toLocaleString()}</span></div>}
                {filmData.ad_revenue > 0 && <div className="flex justify-between"><span>Ads</span><span className="text-green-400">+${filmData.ad_revenue.toLocaleString()}</span></div>}
                <div className="flex justify-between font-bold pt-2 border-t border-white/10">
                  <span>Net Cost</span>
                  <span className={netCost > 0 ? 'text-red-400' : 'text-green-400'}>${Math.abs(netCost).toLocaleString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch(step) {
      case 1: return filmData.title && filmData.genre;
      case 3: return filmData.locations.length > 0;
      case 4: return filmData.screenwriter_id;
      case 5: return filmData.director_id;
      case 6: return filmData.actors.length > 0;
      case 7: return filmData.screenplay;
      default: return true;
    }
  };

  return (
    <div className="pt-20 pb-8 px-4 max-w-4xl mx-auto" data-testid="film-wizard">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3 overflow-x-auto pb-2">
          {steps.map((s, i) => (
            <div key={s.num} className="flex items-center">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                step === s.num ? 'bg-yellow-500 text-black' : step > s.num ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-400'
              }`}>
                {step > s.num ? '✓' : s.num}
              </div>
              {i < steps.length - 1 && <div className={`w-4 h-0.5 mx-1 ${step > s.num ? 'bg-green-500' : 'bg-gray-700'}`} />}
            </div>
          ))}
        </div>
        <h2 className="font-['Bebas_Neue'] text-2xl">{steps[step - 1].title}</h2>
      </div>

      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-4">
          <AnimatePresence mode="wait">
            <motion.div key={step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
              {renderStepContent()}
            </motion.div>
          </AnimatePresence>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between mt-4">
        <Button variant="outline" onClick={() => setStep(step - 1)} disabled={step === 1}>Previous</Button>
        {step < 10 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canProceed()} className="bg-yellow-500 text-black hover:bg-yellow-400">
            Next <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        ) : (
          <Button onClick={handleSubmit} disabled={loading || calculateBudget() - getSponsorBudget() - filmData.ad_revenue > user.funds} className="bg-yellow-500 text-black hover:bg-yellow-400">
            {loading ? 'Creating...' : 'Create Film'}
          </Button>
        )}
      </div>
    </div>
  );
};

const GENRES = ['action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance', 'thriller', 'animation', 'documentary', 'fantasy'];

// Profile Page with Avatar Selection
const ProfilePage = () => {
  const { api, user, refreshUser, logout } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslations();
  const navigate = useNavigate();
  const [avatars, setAvatars] = useState([]);
  const [selectedAvatar, setSelectedAvatar] = useState(user?.avatar_id);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/avatars').then(res => setAvatars(res.data));
  }, [api]);

  const saveProfile = async () => {
    setSaving(true);
    try {
      await api.put('/auth/profile', { avatar_id: selectedAvatar, language });
      await refreshUser();
      toast.success('Profile updated!');
    } catch (err) {
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const resetPlayer = async () => {
    try {
      await api.post('/auth/reset');
      await refreshUser();
      toast.success('Player reset successfully!');
      navigate('/dashboard');
    } catch (err) {
      toast.error('Failed to reset player');
    }
  };

  return (
    <div className="pt-20 pb-8 px-4 max-w-2xl mx-auto" data-testid="profile-page">
      <h1 className="font-['Bebas_Neue'] text-4xl mb-6">{t('profile')}</h1>

      <Card className="bg-[#1A1A1A] border-white/10 mb-6">
        <CardContent className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <Avatar className="w-20 h-20 border-4 border-yellow-500/30">
              <AvatarImage src={user?.avatar_url} />
              <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-2xl">{user?.nickname?.[0]}</AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-xl font-bold">{user?.nickname}</h2>
              <p className="text-gray-400">{user?.production_house_name}</p>
              <p className="text-sm text-gray-500">Owner: {user?.owner_name}</p>
            </div>
          </div>

          {/* Player Scores */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="text-center p-3 rounded bg-white/5">
              <p className="text-xl font-bold">{(user?.likeability_score || 50).toFixed(0)}</p>
              <p className="text-xs text-gray-400">Likeability</p>
            </div>
            <div className="text-center p-3 rounded bg-white/5">
              <p className="text-xl font-bold">{(user?.interaction_score || 50).toFixed(0)}</p>
              <p className="text-xs text-gray-400">Interaction</p>
            </div>
            <div className="text-center p-3 rounded bg-white/5">
              <p className="text-xl font-bold">{(user?.character_score || 50).toFixed(0)}</p>
              <p className="text-xs text-gray-400">Character</p>
            </div>
          </div>

          {/* Avatar Selection */}
          <div className="space-y-3 mb-6">
            <Label>Choose Avatar</Label>
            <div className="grid grid-cols-5 gap-2">
              {avatars.map(avatar => (
                <button
                  key={avatar.id}
                  className={`p-1 rounded-lg border-2 transition-colors ${selectedAvatar === avatar.id ? 'border-yellow-500' : 'border-transparent hover:border-white/20'}`}
                  onClick={() => setSelectedAvatar(avatar.id)}
                >
                  <Avatar className="w-full aspect-square">
                    <AvatarImage src={avatar.url} />
                  </Avatar>
                </button>
              ))}
            </div>
          </div>

          {/* Language */}
          <div className="space-y-2 mb-6">
            <Label>Language</Label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="bg-black/20 border-white/10">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="it">Italiano</SelectItem>
                <SelectItem value="es">Español</SelectItem>
                <SelectItem value="fr">Français</SelectItem>
                <SelectItem value="de">Deutsch</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button onClick={saveProfile} disabled={saving} className="w-full bg-yellow-500 text-black hover:bg-yellow-400 mb-3">
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>

          {/* Reset Player */}
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10">
                <RefreshCw className="w-4 h-4 mr-2" /> Reset Player
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="bg-[#1A1A1A] border-white/10">
              <AlertDialogHeader>
                <AlertDialogTitle>Reset Player?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will delete all your films, reset your funds to $10,000,000, and clear all progress. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={resetPlayer} className="bg-red-500 hover:bg-red-400">
                  Reset
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>
    </div>
  );
};

// My Films Page (simplified)
const MyFilms = () => {
  const { api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [films, setFilms] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/films/my').then(res => setFilms(res.data));
  }, [api]);

  return (
    <div className="pt-20 pb-8 px-4 max-w-7xl mx-auto" data-testid="my-films-page">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-['Bebas_Neue'] text-4xl">{t('my_films')}</h1>
        <Button onClick={() => navigate('/create')} className="bg-yellow-500 text-black hover:bg-yellow-400">
          <Plus className="w-4 h-4 mr-2" /> {t('create_film')}
        </Button>
      </div>

      {films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-12 text-center">
          <Film className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <h3 className="text-xl mb-2">No films yet</h3>
          <Button onClick={() => navigate('/create')} className="bg-yellow-500 text-black">Create Your First Film</Button>
        </Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {films.map(film => (
            <Card key={film.id} className="bg-[#1A1A1A] border-white/5 overflow-hidden cursor-pointer card-hover" onClick={() => navigate(`/films/${film.id}`)}>
              <div className="aspect-[2/3] relative">
                <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} alt={film.title} className="w-full h-full object-cover" />
                <Badge className={`absolute top-2 right-2 ${film.status === 'in_theaters' ? 'bg-green-500' : 'bg-gray-500'}`}>{film.status}</Badge>
              </div>
              <CardContent className="p-3">
                <h3 className="font-semibold truncate">{film.title}</h3>
                <div className="flex justify-between mt-2 text-sm">
                  <span className="flex items-center gap-1 text-gray-400"><Heart className="w-3 h-3" /> {film.likes_count}</span>
                  <span className="text-green-400">${(film.total_revenue || 0).toLocaleString()}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Film Detail, Social Feed, Chat, Statistics pages - keep similar structure as before but simplified
const FilmDetail = () => {
  const { api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [film, setFilm] = useState(null);
  const [expandedCountry, setExpandedCountry] = useState(null);

  useEffect(() => {
    const filmId = window.location.pathname.split('/').pop();
    api.get(`/films/${filmId}`).then(res => setFilm(res.data));
  }, [api]);

  if (!film) return <div className="pt-20 p-4 text-center">Loading...</div>;

  return (
    <div className="pt-20 pb-8 px-4 max-w-7xl mx-auto" data-testid="film-detail-page">
      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="bg-[#1A1A1A] border-white/10 overflow-hidden">
          <div className="aspect-[2/3]">
            <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'} alt={film.title} className="w-full h-full object-cover" />
          </div>
          <CardContent className="p-4">
            <h1 className="font-['Bebas_Neue'] text-2xl mb-2">{film.title}</h1>
            <div className="flex gap-2 mb-3">
              <Badge className="bg-yellow-500/20 text-yellow-500">{t(film.genre)}</Badge>
              <Badge className={film.status === 'in_theaters' ? 'bg-green-500' : 'bg-gray-500'}>{film.status}</Badge>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center p-2 rounded bg-white/5">
                <Heart className="w-5 h-5 mx-auto mb-1 text-red-400" />
                <p className="font-bold">{film.likes_count}</p>
                <p className="text-xs text-gray-400">Likes</p>
              </div>
              <div className="text-center p-2 rounded bg-white/5">
                <DollarSign className="w-5 h-5 mx-auto mb-1 text-green-400" />
                <p className="font-bold">${(film.total_revenue || 0).toLocaleString()}</p>
                <p className="text-xs text-gray-400">Revenue</p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-white/10">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Quality</span>
                <span>{film.quality_score?.toFixed(0)}%</span>
              </div>
              <Progress value={film.quality_score} className="mt-1 h-2" />
              <div className="flex justify-between text-sm mt-2">
                <span className="text-gray-400">Satisfaction</span>
                <span>{(film.audience_satisfaction || 50).toFixed(0)}%</span>
              </div>
              <Progress value={film.audience_satisfaction || 50} className="mt-1 h-2" />
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader>
              <CardTitle className="font-['Bebas_Neue'] text-xl flex items-center gap-2">
                <Globe className="w-5 h-5 text-yellow-500" /> {t('box_office')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(film.box_office || {}).length === 0 ? (
                <p className="text-gray-400 text-center py-6">Box office data will appear after release</p>
              ) : (
                <ScrollArea className="h-[300px]">
                  <div className="space-y-2 pr-2">
                    {Object.entries(film.box_office).map(([country, data]) => (
                      <div key={country} className="border border-white/10 rounded overflow-hidden">
                        <button
                          className="w-full p-3 flex items-center justify-between hover:bg-white/5"
                          onClick={() => setExpandedCountry(expandedCountry === country ? null : country)}
                        >
                          <span className="font-semibold">{country}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-green-400">${data.total_revenue?.toLocaleString()}</span>
                            {expandedCountry === country ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                          </div>
                        </button>
                        {expandedCountry === country && (
                          <div className="p-3 pt-0 border-t border-white/10 bg-black/20">
                            {Object.entries(data.cities || {}).map(([city, cityData]) => (
                              <div key={city} className="flex justify-between py-1 text-sm">
                                <span>{city}</span>
                                <span className="text-green-400">${cityData.revenue?.toLocaleString()}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Social Feed Page
const SocialFeed = () => {
  const { api, user } = useContext(AuthContext);
  const { t } = useTranslations();
  const [films, setFilms] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/films/social/feed').then(res => setFilms(res.data.films));
  }, [api]);

  const handleLike = async (filmId) => {
    const res = await api.post(`/films/${filmId}/like`);
    setFilms(films.map(f => f.id === filmId ? { ...f, user_liked: res.data.liked, likes_count: res.data.likes_count } : f));
  };

  return (
    <div className="pt-20 pb-8 px-4 max-w-4xl mx-auto" data-testid="social-feed-page">
      <h1 className="font-['Bebas_Neue'] text-4xl mb-6">{t('social')}</h1>
      <div className="space-y-4">
        {films.map(film => (
          <Card key={film.id} className="bg-[#1A1A1A] border-white/10 overflow-hidden">
            <div className="flex">
              <div className="w-28 flex-shrink-0">
                <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300'} alt={film.title} className="w-full h-full object-cover cursor-pointer" onClick={() => navigate(`/films/${film.id}`)} />
              </div>
              <CardContent className="flex-1 p-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold cursor-pointer hover:text-yellow-500" onClick={() => navigate(`/films/${film.id}`)}>{film.title}</h3>
                    <p className="text-xs text-gray-400">by {film.owner?.production_house_name}</p>
                  </div>
                  <Badge className="bg-yellow-500/20 text-yellow-500 text-xs">{t(film.genre)}</Badge>
                </div>
                <div className="flex items-center gap-3 mt-3">
                  <Button variant="ghost" size="sm" className={film.user_liked ? 'text-red-400' : 'text-gray-400'} onClick={() => handleLike(film.id)}>
                    <Heart className={`w-4 h-4 mr-1 ${film.user_liked ? 'fill-red-400' : ''}`} /> {film.likes_count}
                  </Button>
                  <span className="text-sm text-gray-400"><Star className="w-3 h-3 inline mr-1 text-yellow-500" />{film.quality_score?.toFixed(0)}%</span>
                </div>
              </CardContent>
            </div>
          </Card>
        ))}
      </div>
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

  useEffect(() => {
    api.get('/chat/rooms').then(res => {
      setRooms(res.data);
      if (res.data.public.length > 0) setActiveRoom(res.data.public[0]);
    });
  }, [api]);

  useEffect(() => {
    if (activeRoom) {
      api.get(`/chat/rooms/${activeRoom.id}/messages`).then(res => setMessages(res.data));
    }
  }, [activeRoom, api]);

  const sendMessage = async () => {
    if (!newMessage.trim() || !activeRoom) return;
    await api.post('/chat/messages', { room_id: activeRoom.id, content: newMessage, message_type: 'text' });
    setNewMessage('');
    const res = await api.get(`/chat/rooms/${activeRoom.id}/messages`);
    setMessages(res.data);
  };

  return (
    <div className="pt-20 pb-8 px-4 max-w-6xl mx-auto h-[calc(100vh-5rem)]" data-testid="chat-page">
      <div className="grid lg:grid-cols-4 gap-4 h-full">
        <Card className="bg-[#1A1A1A] border-white/10 lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="font-['Bebas_Neue'] text-lg">{t('chat')}</CardTitle>
          </CardHeader>
          <CardContent className="p-2">
            {rooms.public.map(room => (
              <button key={room.id} className={`w-full text-left p-2 rounded text-sm ${activeRoom?.id === room.id ? 'bg-yellow-500/20 text-yellow-500' : 'hover:bg-white/5'}`} onClick={() => setActiveRoom(room)}>
                <MessageSquare className="w-3 h-3 inline mr-2" />{room.name}
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-[#1A1A1A] border-white/10 lg:col-span-3 flex flex-col">
          {activeRoom ? (
            <>
              <CardHeader className="pb-2 border-b border-white/10">
                <CardTitle className="font-['Bebas_Neue'] text-lg">{activeRoom.name}</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 p-3 overflow-hidden flex flex-col">
                <ScrollArea className="flex-1">
                  <div className="space-y-3">
                    {messages.map(msg => (
                      <div key={msg.id} className={`flex ${msg.sender_id === user.id ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[70%] px-3 py-2 rounded-xl ${msg.sender_id === user.id ? 'bg-yellow-500 text-black rounded-br-sm' : 'bg-white/10 rounded-bl-sm'}`}>
                          {msg.sender_id !== user.id && <p className="text-xs font-semibold mb-1">{msg.sender?.nickname}</p>}
                          <p className="text-sm">{msg.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
                <div className="flex gap-2 mt-3 pt-3 border-t border-white/10">
                  <Input value={newMessage} onChange={e => setNewMessage(e.target.value)} placeholder="Type a message..." className="bg-black/20 border-white/10" onKeyPress={e => e.key === 'Enter' && sendMessage()} />
                  <Button onClick={sendMessage} className="bg-yellow-500 text-black"><Send className="w-4 h-4" /></Button>
                </div>
              </CardContent>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">Select a room</div>
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

  useEffect(() => {
    Promise.all([api.get('/statistics/global'), api.get('/statistics/my')]).then(([g, m]) => {
      setGlobalStats(g.data);
      setMyStats(m.data);
    });
  }, [api]);

  return (
    <div className="pt-20 pb-8 px-4 max-w-7xl mx-auto" data-testid="statistics-page">
      <h1 className="font-['Bebas_Neue'] text-4xl mb-6">{t('statistics')}</h1>
      <Tabs defaultValue="my">
        <TabsList className="mb-4">
          <TabsTrigger value="my">My Stats</TabsTrigger>
          <TabsTrigger value="global">Global</TabsTrigger>
        </TabsList>
        <TabsContent value="my">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Films', value: myStats?.total_films || 0, icon: Film },
              { label: 'Revenue', value: `$${(myStats?.total_revenue || 0).toLocaleString()}`, icon: DollarSign },
              { label: 'Likes', value: myStats?.total_likes || 0, icon: Heart },
              { label: 'Quality', value: `${(myStats?.average_quality || 0).toFixed(1)}%`, icon: Star }
            ].map(s => (
              <Card key={s.label} className="bg-[#1A1A1A] border-white/5">
                <CardContent className="p-4">
                  <s.icon className="w-6 h-6 mb-2 text-yellow-500" />
                  <p className="text-2xl font-bold">{s.value}</p>
                  <p className="text-sm text-gray-400">{s.label}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="global">
          <div className="grid sm:grid-cols-3 gap-4">
            <Card className="bg-[#1A1A1A] border-white/5">
              <CardContent className="p-4">
                <Film className="w-6 h-6 mb-2 text-yellow-500" />
                <p className="text-2xl font-bold">{globalStats?.total_films || 0}</p>
                <p className="text-sm text-gray-400">Total Films</p>
              </CardContent>
            </Card>
            <Card className="bg-[#1A1A1A] border-white/5">
              <CardContent className="p-4">
                <Users className="w-6 h-6 mb-2 text-blue-500" />
                <p className="text-2xl font-bold">{globalStats?.total_users || 0}</p>
                <p className="text-sm text-gray-400">Producers</p>
              </CardContent>
            </Card>
            <Card className="bg-[#1A1A1A] border-white/5">
              <CardContent className="p-4">
                <DollarSign className="w-6 h-6 mb-2 text-green-500" />
                <p className="text-2xl font-bold">${(globalStats?.total_box_office || 0).toLocaleString()}</p>
                <p className="text-sm text-gray-400">Global Box Office</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center"><Clapperboard className="w-12 h-12 text-yellow-500 animate-pulse" /></div>;
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
