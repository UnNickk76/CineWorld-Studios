import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import { 
  Film, Home, Users, MessageSquare, BarChart3, User, LogOut, Plus, Heart, 
  Globe, Calendar, DollarSign, Star, Clapperboard, Camera, MapPin, Sparkles,
  Send, Image, Mic, ChevronRight, ChevronDown, Menu, X, Settings, Search
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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Label } from './components/ui/label';
import { Calendar as CalendarComponent } from './components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './components/ui/popover';
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

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, token, api, updateFunds }}>
      {children}
    </AuthContext.Provider>
  );
};

// Language Provider
const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(localStorage.getItem('cineworld_lang') || 'en');
  const [translations, setTranslations] = useState({});
  const { token } = useContext(AuthContext) || {};

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
    { path: '/chat', icon: MessageSquare, label: 'chat' },
    { path: '/statistics', icon: BarChart3, label: 'statistics' },
  ];

  const gameDate = new Date().toLocaleDateString(language === 'it' ? 'it-IT' : language === 'es' ? 'es-ES' : language === 'fr' ? 'fr-FR' : language === 'de' ? 'de-DE' : 'en-US', {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
  });

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 bg-[#0F0F10]/95 backdrop-blur-md border-b border-white/10 z-50">
      <div className="max-w-7xl mx-auto h-full px-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')} data-testid="logo">
          <Clapperboard className="w-8 h-8 text-yellow-500" />
          <span className="font-['Bebas_Neue'] text-2xl tracking-wide hidden sm:block">CineWorld Studio's</span>
        </div>

        {/* Desktop Nav */}
        <div className="hidden lg:flex items-center gap-1">
          {navItems.map(item => (
            <Button
              key={item.path}
              variant={location.pathname === item.path ? "default" : "ghost"}
              className={`gap-2 ${location.pathname === item.path ? 'bg-yellow-500 text-black hover:bg-yellow-400' : 'text-gray-400 hover:text-white'}`}
              onClick={() => navigate(item.path)}
              data-testid={`nav-${item.label}`}
            >
              <item.icon className="w-4 h-4" />
              <span className="hidden xl:inline">{t(item.label)}</span>
            </Button>
          ))}
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-4">
          {/* Game Date */}
          <div className="hidden md:flex items-center gap-2 text-sm text-gray-400">
            <Calendar className="w-4 h-4" />
            <span>{gameDate}</span>
          </div>

          {/* Funds */}
          <div className="flex items-center gap-2 bg-yellow-500/10 px-3 py-1.5 rounded-lg border border-yellow-500/20">
            <DollarSign className="w-4 h-4 text-yellow-500" />
            <span className="text-yellow-500 font-bold" data-testid="user-funds">
              ${user?.funds?.toLocaleString() || '0'}
            </span>
          </div>

          {/* Language Selector */}
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="w-16 h-9 bg-transparent border-white/10" data-testid="language-selector">
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

          {/* Profile */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" className="gap-2 p-1" data-testid="profile-menu">
                <Avatar className="w-8 h-8 border border-yellow-500/30">
                  <AvatarImage src={user?.avatar_url} />
                  <AvatarFallback className="bg-yellow-500/20 text-yellow-500">
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

          {/* Mobile Menu Toggle */}
          <Button variant="ghost" className="lg:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </Button>
        </div>
      </div>

      {/* Mobile Menu */}
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

// Login/Register Page
const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const { login, register } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '', password: '', nickname: '', production_house_name: '', owner_name: '', language: 'en'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register({ ...formData, language });
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
              <Clapperboard className="w-16 h-16 text-yellow-500" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-4xl tracking-wide">CineWorld Studio's</CardTitle>
            <CardDescription>
              {isLogin ? 'Sign in to your production house' : 'Create your production empire'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  placeholder="producer@cineworld.com"
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                  className="bg-black/20 border-white/10"
                  required
                  data-testid="email-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Password</Label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={e => setFormData({ ...formData, password: e.target.value })}
                  className="bg-black/20 border-white/10"
                  required
                  data-testid="password-input"
                />
              </div>

              {!isLogin && (
                <>
                  <div className="space-y-2">
                    <Label>Nickname</Label>
                    <Input
                      placeholder="Your producer name"
                      value={formData.nickname}
                      onChange={e => setFormData({ ...formData, nickname: e.target.value })}
                      className="bg-black/20 border-white/10"
                      required
                      data-testid="nickname-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Production House Name</Label>
                    <Input
                      placeholder="e.g., Paramount Pictures"
                      value={formData.production_house_name}
                      onChange={e => setFormData({ ...formData, production_house_name: e.target.value })}
                      className="bg-black/20 border-white/10"
                      required
                      data-testid="production-house-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Owner Name</Label>
                    <Input
                      placeholder="Real or fictional"
                      value={formData.owner_name}
                      onChange={e => setFormData({ ...formData, owner_name: e.target.value })}
                      className="bg-black/20 border-white/10"
                      required
                      data-testid="owner-name-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Language</Label>
                    <Select value={language} onValueChange={(v) => { setLanguage(v); setFormData({ ...formData, language: v }); }}>
                      <SelectTrigger className="bg-black/20 border-white/10" data-testid="register-language-select">
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
                </>
              )}

              <Button 
                type="submit" 
                className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold uppercase tracking-wider"
                disabled={loading}
                data-testid="auth-submit-btn"
              >
                {loading ? 'Loading...' : isLogin ? 'Sign In' : 'Create Account'}
              </Button>
            </form>

            <div className="mt-6 text-center">
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

// Dashboard Page
const Dashboard = () => {
  const { user, api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [stats, setStats] = useState(null);
  const [films, setFilms] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, filmsRes] = await Promise.all([
          api.get('/statistics/my'),
          api.get('/films/my')
        ]);
        setStats(statsRes.data);
        setFilms(filmsRes.data.slice(0, 4));
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, [api]);

  return (
    <div className="pt-20 pb-8 px-4 max-w-7xl mx-auto" data-testid="dashboard">
      {/* Welcome Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="font-['Bebas_Neue'] text-5xl md:text-6xl mb-2">
          {t('welcome')}, <span className="text-yellow-500">{user?.nickname}</span>
        </h1>
        <p className="text-gray-400 text-lg">{user?.production_house_name}</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
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
              <CardContent className="p-4 flex items-center gap-4">
                <div className={`p-3 rounded-lg bg-${stat.color}-500/10`}>
                  <stat.icon className={`w-6 h-6 text-${stat.color}-500`} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-sm text-gray-400">{stat.label}</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/5 border-yellow-500/20 cursor-pointer card-hover" onClick={() => navigate('/create')} data-testid="quick-create-film">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-4 bg-yellow-500 rounded-xl">
              <Plus className="w-8 h-8 text-black" />
            </div>
            <div>
              <h3 className="font-['Bebas_Neue'] text-2xl">{t('create_film')}</h3>
              <p className="text-gray-400">Start your next blockbuster</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/5 border-blue-500/20 cursor-pointer card-hover" onClick={() => navigate('/social')} data-testid="quick-social">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-4 bg-blue-500 rounded-xl">
              <Globe className="w-8 h-8 text-white" />
            </div>
            <div>
              <h3 className="font-['Bebas_Neue'] text-2xl">Explore Films</h3>
              <p className="text-gray-400">Discover what others are creating</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Films */}
      {films.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-['Bebas_Neue'] text-3xl">{t('my_films')}</h2>
            <Button variant="ghost" onClick={() => navigate('/films')} data-testid="view-all-films">
              View All <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {films.map((film, i) => (
              <motion.div
                key={film.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
              >
                <Card className="bg-[#1A1A1A] border-white/5 overflow-hidden group cursor-pointer card-hover" onClick={() => navigate(`/films/${film.id}`)}>
                  <div className="poster-aspect relative">
                    <img 
                      src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} 
                      alt={film.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="poster-overlay" />
                    <div className="absolute bottom-0 left-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Badge className={film.status === 'in_theaters' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}>
                        {film.status}
                      </Badge>
                    </div>
                  </div>
                  <CardContent className="p-4">
                    <h3 className="font-semibold truncate">{film.title}</h3>
                    <div className="flex items-center justify-between mt-2 text-sm text-gray-400">
                      <span className="flex items-center gap-1">
                        <Heart className="w-3 h-3" /> {film.likes_count}
                      </span>
                      <span className="flex items-center gap-1">
                        <DollarSign className="w-3 h-3" /> {(film.daily_revenues?.reduce((a, b) => a + b.net_revenue, 0) || 0).toLocaleString()}
                      </span>
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

// My Films Page
const MyFilms = () => {
  const { api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/films/my')
      .then(res => setFilms(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [api]);

  if (loading) {
    return <div className="pt-20 p-4 text-center">Loading...</div>;
  }

  return (
    <div className="pt-20 pb-8 px-4 max-w-7xl mx-auto" data-testid="my-films-page">
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-['Bebas_Neue'] text-4xl md:text-5xl">{t('my_films')}</h1>
        <Button onClick={() => navigate('/create')} className="bg-yellow-500 text-black hover:bg-yellow-400" data-testid="create-new-film-btn">
          <Plus className="w-4 h-4 mr-2" /> {t('create_film')}
        </Button>
      </div>

      {films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-12 text-center">
          <Film className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <h3 className="text-xl mb-2">No films yet</h3>
          <p className="text-gray-400 mb-4">Start creating your first blockbuster!</p>
          <Button onClick={() => navigate('/create')} className="bg-yellow-500 text-black hover:bg-yellow-400">
            Create Your First Film
          </Button>
        </Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {films.map((film, i) => (
            <motion.div
              key={film.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card 
                className="bg-[#1A1A1A] border-white/5 overflow-hidden group cursor-pointer card-hover"
                onClick={() => navigate(`/films/${film.id}`)}
                data-testid={`film-card-${film.id}`}
              >
                <div className="poster-aspect relative">
                  <img 
                    src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=400'} 
                    alt={film.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="poster-overlay" />
                  <div className="absolute top-3 right-3">
                    <Badge className={
                      film.status === 'in_theaters' ? 'bg-green-500 text-white' :
                      film.status === 'in_production' ? 'bg-blue-500 text-white' :
                      'bg-gray-500 text-white'
                    }>
                      {film.status}
                    </Badge>
                  </div>
                </div>
                <CardContent className="p-4 space-y-3">
                  <h3 className="font-semibold text-lg truncate">{film.title}</h3>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="border-yellow-500/30 text-yellow-500">{t(film.genre)}</Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-1 text-gray-400">
                      <Heart className="w-3 h-3 text-red-400" /> {film.likes_count}
                    </div>
                    <div className="flex items-center gap-1 text-gray-400">
                      <Star className="w-3 h-3 text-yellow-400" /> {film.quality_score?.toFixed(0)}%
                    </div>
                  </div>
                  <div className="pt-2 border-t border-white/5">
                    <p className="text-sm text-gray-400">Total Revenue</p>
                    <p className="text-lg font-bold text-green-400">
                      ${(film.daily_revenues?.reduce((a, b) => a + b.net_revenue, 0) || 0).toLocaleString()}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

// Film Creation Wizard
const FilmWizard = () => {
  const { api, user, updateFunds } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  // Data from API
  const [sponsors, setSponsors] = useState([]);
  const [locations, setLocations] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [screenwriters, setScreenwriters] = useState([]);
  const [directors, setDirectors] = useState([]);
  const [actors, setActors] = useState([]);

  // Form state
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
    { num: 3, title: 'Equipment & Locations', icon: Camera },
    { num: 4, title: 'Screenwriter', icon: Sparkles },
    { num: 5, title: 'Director', icon: Clapperboard },
    { num: 6, title: 'Cast', icon: Users },
    { num: 7, title: 'Screenplay', icon: Film },
    { num: 8, title: 'Poster', icon: Image },
    { num: 9, title: 'Advertising', icon: DollarSign },
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
      toast.success('Film created successfully!');
      updateFunds(user.funds - calculateBudget() + getSponsorBudget() + filmData.ad_revenue);
      navigate(`/films/${res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create film');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch(step) {
      case 1: // Title & Genre
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label className="text-lg">Film Title *</Label>
              <Input
                value={filmData.title}
                onChange={e => setFilmData({ ...filmData, title: e.target.value })}
                placeholder="Enter your film title..."
                className="text-xl h-14 bg-black/20 border-white/10"
                data-testid="film-title-input"
              />
              <p className="text-sm text-gray-400">A great title can boost initial audience interest!</p>
            </div>

            <div className="space-y-2">
              <Label className="text-lg">{t('genre')} *</Label>
              <Select value={filmData.genre} onValueChange={v => setFilmData({ ...filmData, genre: v })}>
                <SelectTrigger className="h-12 bg-black/20 border-white/10" data-testid="genre-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {['action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance', 'thriller', 'animation', 'documentary', 'fantasy'].map(g => (
                    <SelectItem key={g} value={g}>{t(g)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-lg">{t('release_date')} *</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start h-12 bg-black/20 border-white/10" data-testid="release-date-btn">
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
              <Label className="text-lg">Weeks in Theater</Label>
              <div className="flex items-center gap-4">
                <Slider
                  value={[filmData.weeks_in_theater]}
                  onValueChange={([v]) => setFilmData({ ...filmData, weeks_in_theater: v })}
                  min={1}
                  max={12}
                  step={1}
                  className="flex-1"
                />
                <span className="text-xl font-bold w-12 text-center">{filmData.weeks_in_theater}</span>
              </div>
            </div>
          </div>
        );

      case 2: // Sponsor
        return (
          <div className="space-y-6">
            <p className="text-gray-400">Choose a sponsor to get additional funding. They will take a percentage of box office revenue.</p>
            <div className="grid gap-4">
              <Card 
                className={`bg-[#1A1A1A] border-2 cursor-pointer transition-colors ${!filmData.sponsor_id ? 'border-yellow-500' : 'border-white/10 hover:border-white/20'}`}
                onClick={() => setFilmData({ ...filmData, sponsor_id: null })}
                data-testid="no-sponsor-option"
              >
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="w-12 h-12 bg-gray-700 rounded-lg flex items-center justify-center">
                    <X className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-semibold">No Sponsor</h4>
                    <p className="text-sm text-gray-400">Keep 100% of box office revenue</p>
                  </div>
                </CardContent>
              </Card>
              
              {sponsors.map(sponsor => (
                <Card 
                  key={sponsor.name}
                  className={`bg-[#1A1A1A] border-2 cursor-pointer transition-colors ${filmData.sponsor_id === sponsor.name ? 'border-yellow-500' : 'border-white/10 hover:border-white/20'}`}
                  onClick={() => setFilmData({ ...filmData, sponsor_id: sponsor.name })}
                  data-testid={`sponsor-${sponsor.name}`}
                >
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-yellow-500/20 to-yellow-600/10 rounded-lg flex items-center justify-center">
                        <DollarSign className="w-6 h-6 text-yellow-500" />
                      </div>
                      <div>
                        <h4 className="font-semibold">{sponsor.name}</h4>
                        <div className="flex items-center gap-1 mt-1">
                          {[...Array(sponsor.rating)].map((_, i) => (
                            <Star key={i} className="w-3 h-3 fill-yellow-500 text-yellow-500" />
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-green-400 font-bold">+${sponsor.budget_offer.toLocaleString()}</p>
                      <p className="text-sm text-red-400">-{sponsor.revenue_share}% revenue</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );

      case 3: // Equipment & Locations
        return (
          <div className="space-y-6">
            <div className="space-y-4">
              <Label className="text-lg">Equipment Package</Label>
              <div className="grid gap-3">
                {equipment.map(eq => (
                  <Card 
                    key={eq.name}
                    className={`bg-[#1A1A1A] border-2 cursor-pointer transition-colors ${filmData.equipment_package === eq.name ? 'border-yellow-500' : 'border-white/10 hover:border-white/20'}`}
                    onClick={() => setFilmData({ ...filmData, equipment_package: eq.name })}
                    data-testid={`equipment-${eq.name}`}
                  >
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">{eq.name}</h4>
                        <p className="text-sm text-gray-400">Quality Bonus: +{eq.quality_bonus}%</p>
                      </div>
                      <p className="text-yellow-500 font-bold">${eq.cost.toLocaleString()}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <Label className="text-lg">Filming Locations</Label>
              <div className="grid sm:grid-cols-2 gap-3">
                {locations.map(loc => {
                  const isSelected = filmData.locations.includes(loc.name);
                  return (
                    <Card 
                      key={loc.name}
                      className={`bg-[#1A1A1A] border-2 cursor-pointer transition-colors ${isSelected ? 'border-yellow-500' : 'border-white/10 hover:border-white/20'}`}
                      onClick={() => {
                        if (isSelected) {
                          const newLocations = filmData.locations.filter(l => l !== loc.name);
                          const newDays = { ...filmData.location_days };
                          delete newDays[loc.name];
                          setFilmData({ ...filmData, locations: newLocations, location_days: newDays });
                        } else {
                          setFilmData({ 
                            ...filmData, 
                            locations: [...filmData.locations, loc.name],
                            location_days: { ...filmData.location_days, [loc.name]: 7 }
                          });
                        }
                      }}
                      data-testid={`location-${loc.name}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <MapPin className="w-4 h-4 text-yellow-500" />
                          <h4 className="font-semibold">{loc.name}</h4>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <Badge variant="outline" className="border-white/20">{loc.type}</Badge>
                          <span className="text-yellow-500">${loc.cost_per_day.toLocaleString()}/day</span>
                        </div>
                        {isSelected && (
                          <div className="mt-3 pt-3 border-t border-white/10">
                            <Label className="text-xs">Days: {filmData.location_days[loc.name]}</Label>
                            <Slider
                              value={[filmData.location_days[loc.name] || 7]}
                              onValueChange={([v]) => setFilmData({ 
                                ...filmData, 
                                location_days: { ...filmData.location_days, [loc.name]: v }
                              })}
                              min={1}
                              max={30}
                              onClick={e => e.stopPropagation()}
                            />
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          </div>
        );

      case 4: // Screenwriter
      case 5: // Director
      case 6: // Cast
        const peopleType = step === 4 ? 'screenwriters' : step === 5 ? 'directors' : 'actors';
        const people = step === 4 ? screenwriters : step === 5 ? directors : actors;
        const selectedId = step === 4 ? filmData.screenwriter_id : step === 5 ? filmData.director_id : null;

        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-gray-400">
                {step === 6 ? `Selected: ${filmData.actors.length} actors` : 'Choose your team member'}
              </p>
              <Button variant="outline" size="sm" onClick={() => fetchPeople(peopleType)} data-testid="refresh-people">
                Refresh List
              </Button>
            </div>
            <ScrollArea className="h-[400px]">
              <div className="grid gap-3 pr-4">
                {people.map(person => {
                  const isSelected = step === 6 
                    ? filmData.actors.some(a => a.actor_id === person.id)
                    : selectedId === person.id;
                  
                  return (
                    <Card 
                      key={person.id}
                      className={`bg-[#1A1A1A] border-2 cursor-pointer transition-colors ${isSelected ? 'border-yellow-500' : 'border-white/10 hover:border-white/20'}`}
                      onClick={() => {
                        if (step === 4) {
                          setFilmData({ ...filmData, screenwriter_id: person.id });
                        } else if (step === 5) {
                          setFilmData({ ...filmData, director_id: person.id });
                        } else {
                          if (isSelected) {
                            setFilmData({ 
                              ...filmData, 
                              actors: filmData.actors.filter(a => a.actor_id !== person.id) 
                            });
                          } else {
                            setFilmData({ 
                              ...filmData, 
                              actors: [...filmData.actors, { actor_id: person.id, role: 'Lead' }] 
                            });
                          }
                        }
                      }}
                      data-testid={`person-${person.id}`}
                    >
                      <CardContent className="p-4 flex items-center gap-4">
                        <Avatar className="w-14 h-14 border-2 border-white/10">
                          <AvatarImage src={person.avatar_url} />
                          <AvatarFallback className="bg-yellow-500/20 text-yellow-500">
                            {person.name[0]}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold">{person.name}</h4>
                            {person.is_star && <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />}
                          </div>
                          <p className="text-sm text-gray-400">{person.nationality} • Age {person.age}</p>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {person.primary_skills?.slice(0, 2).map(skill => (
                              <Badge key={skill} variant="outline" className="text-xs border-yellow-500/30 text-yellow-500">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-yellow-500 font-bold">${person.cost_per_film?.toLocaleString()}</p>
                          <div className="flex items-center gap-1 mt-1">
                            {[...Array(Math.min(5, Math.ceil(person.trust_level / 20)))].map((_, i) => (
                              <Star key={i} className="w-3 h-3 fill-yellow-500/50 text-yellow-500/50" />
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </ScrollArea>

            {step === 6 && (
              <div className="space-y-4 pt-4 border-t border-white/10">
                <Label className="text-lg">Extras</Label>
                <div className="flex items-center gap-4">
                  <span className="text-gray-400">Count:</span>
                  <Slider
                    value={[filmData.extras_count]}
                    onValueChange={([v]) => setFilmData({ 
                      ...filmData, 
                      extras_count: v,
                      extras_cost: v * 1000
                    })}
                    min={0}
                    max={500}
                    step={10}
                    className="flex-1"
                  />
                  <span className="font-bold w-16 text-right">{filmData.extras_count}</span>
                </div>
                <p className="text-sm text-gray-400">Cost: ${filmData.extras_cost.toLocaleString()}</p>
              </div>
            )}
          </div>
        );

      case 7: // Screenplay
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <Button 
                variant={filmData.screenplay_source === 'manual' ? 'default' : 'outline'}
                onClick={() => setFilmData({ ...filmData, screenplay_source: 'manual' })}
                className={filmData.screenplay_source === 'manual' ? 'bg-yellow-500 text-black' : ''}
                data-testid="manual-screenplay-btn"
              >
                Write Manually
              </Button>
              <Button 
                variant={filmData.screenplay_source === 'ai' ? 'default' : 'outline'}
                onClick={generateScreenplay}
                disabled={generating || !filmData.title}
                className={filmData.screenplay_source === 'ai' ? 'bg-yellow-500 text-black' : ''}
                data-testid="ai-screenplay-btn"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                {generating ? 'Generating...' : 'Generate with AI'}
              </Button>
            </div>

            <Textarea
              value={filmData.screenplay}
              onChange={e => setFilmData({ ...filmData, screenplay: e.target.value })}
              placeholder="Write your screenplay here or generate with AI..."
              className="min-h-[300px] bg-black/20 border-white/10"
              data-testid="screenplay-textarea"
            />
          </div>
        );

      case 8: // Poster
        return (
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Label>Poster Guidelines (Optional)</Label>
                <Textarea
                  value={filmData.poster_prompt}
                  onChange={e => setFilmData({ ...filmData, poster_prompt: e.target.value })}
                  placeholder="Describe what you want in the poster..."
                  className="min-h-[150px] bg-black/20 border-white/10"
                  data-testid="poster-prompt-input"
                />
                <Button 
                  onClick={generatePoster}
                  disabled={generating || !filmData.title}
                  className="w-full bg-yellow-500 text-black hover:bg-yellow-400"
                  data-testid="generate-poster-btn"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  {generating ? 'Generating Poster...' : 'Generate AI Poster'}
                </Button>
                <p className="text-xs text-gray-400">Or paste a URL:</p>
                <Input
                  value={filmData.poster_url}
                  onChange={e => setFilmData({ ...filmData, poster_url: e.target.value })}
                  placeholder="https://..."
                  className="bg-black/20 border-white/10"
                  data-testid="poster-url-input"
                />
              </div>
              <div className="aspect-[2/3] bg-[#1A1A1A] rounded-lg overflow-hidden border border-white/10">
                {filmData.poster_url ? (
                  <img src={filmData.poster_url} alt="Poster Preview" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <Image className="w-16 h-16 mx-auto mb-2 opacity-50" />
                      <p>Poster Preview</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 9: // Advertising
        return (
          <div className="space-y-6">
            <p className="text-gray-400">
              Add in-film advertisements for immediate revenue. Too many ads may reduce audience satisfaction.
            </p>
            
            <div className="space-y-4">
              <Label className="text-lg">Ad Duration (seconds)</Label>
              <div className="flex items-center gap-4">
                <Slider
                  value={[filmData.ad_duration_seconds]}
                  onValueChange={([v]) => setFilmData({ 
                    ...filmData, 
                    ad_duration_seconds: v,
                    ad_revenue: v * 5000
                  })}
                  min={0}
                  max={180}
                  step={15}
                  className="flex-1"
                />
                <span className="font-bold w-20 text-right">{filmData.ad_duration_seconds}s</span>
              </div>
            </div>

            <Card className="bg-[#1A1A1A] border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-gray-400">Immediate Revenue</span>
                  <span className="text-2xl font-bold text-green-400">+${filmData.ad_revenue.toLocaleString()}</span>
                </div>
                {filmData.ad_duration_seconds > 60 && (
                  <div className="flex items-center gap-2 text-yellow-500">
                    <span className="text-sm">⚠️ High ad duration may reduce audience attendance</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        );

      case 10: // Review
        const totalBudget = calculateBudget();
        const sponsorBudget = getSponsorBudget();
        const netCost = totalBudget - sponsorBudget - filmData.ad_revenue;

        return (
          <div className="space-y-6">
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardHeader>
                <CardTitle className="font-['Bebas_Neue'] text-3xl">{filmData.title}</CardTitle>
                <CardDescription>{t(filmData.genre)} • {filmData.weeks_in_theater} weeks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-400">Release Date</p>
                    <p className="font-semibold">{format(releaseDate, 'PPP')}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Sponsor</p>
                    <p className="font-semibold">{filmData.sponsor_id || 'None'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Equipment</p>
                    <p className="font-semibold">{filmData.equipment_package}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Locations</p>
                    <p className="font-semibold">{filmData.locations.length} selected</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Cast Size</p>
                    <p className="font-semibold">{filmData.actors.length} actors + {filmData.extras_count} extras</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Ads</p>
                    <p className="font-semibold">{filmData.ad_duration_seconds}s</p>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/10 space-y-2">
                  <div className="flex justify-between">
                    <span>Total Budget</span>
                    <span className="text-red-400">-${totalBudget.toLocaleString()}</span>
                  </div>
                  {sponsorBudget > 0 && (
                    <div className="flex justify-between">
                      <span>Sponsor Funding</span>
                      <span className="text-green-400">+${sponsorBudget.toLocaleString()}</span>
                    </div>
                  )}
                  {filmData.ad_revenue > 0 && (
                    <div className="flex justify-between">
                      <span>Ad Revenue</span>
                      <span className="text-green-400">+${filmData.ad_revenue.toLocaleString()}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-lg font-bold pt-2 border-t border-white/10">
                    <span>Net Cost</span>
                    <span className={netCost > 0 ? 'text-red-400' : 'text-green-400'}>
                      ${Math.abs(netCost).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-400">
                    <span>Your Funds After</span>
                    <span>${(user.funds - netCost).toLocaleString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
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
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4 overflow-x-auto pb-2">
          {steps.map((s, i) => (
            <div key={s.num} className="flex items-center">
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                  step === s.num ? 'step-active' : step > s.num ? 'step-completed' : 'step-pending'
                }`}
              >
                {step > s.num ? '✓' : s.num}
              </div>
              {i < steps.length - 1 && (
                <div className={`w-4 sm:w-8 h-0.5 mx-1 ${step > s.num ? 'bg-green-500' : 'bg-gray-700'}`} />
              )}
            </div>
          ))}
        </div>
        <h2 className="font-['Bebas_Neue'] text-3xl">{steps[step - 1].title}</h2>
      </div>

      {/* Step Content */}
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              {renderStepContent()}
            </motion.div>
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6">
        <Button
          variant="outline"
          onClick={() => setStep(step - 1)}
          disabled={step === 1}
          data-testid="wizard-prev-btn"
        >
          Previous
        </Button>
        
        {step < 10 ? (
          <Button
            onClick={() => setStep(step + 1)}
            disabled={!canProceed()}
            className="bg-yellow-500 text-black hover:bg-yellow-400"
            data-testid="wizard-next-btn"
          >
            Next <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={loading || calculateBudget() - getSponsorBudget() - filmData.ad_revenue > user.funds}
            className="bg-yellow-500 text-black hover:bg-yellow-400"
            data-testid="wizard-submit-btn"
          >
            {loading ? 'Creating...' : 'Create Film'}
          </Button>
        )}
      </div>
    </div>
  );
};

// Film Detail Page
const FilmDetail = () => {
  const { api } = useContext(AuthContext);
  const { t } = useTranslations();
  const { id } = window.location.pathname.split('/').pop();
  const [film, setFilm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedCountry, setExpandedCountry] = useState(null);

  useEffect(() => {
    const filmId = window.location.pathname.split('/').pop();
    api.get(`/films/${filmId}`)
      .then(res => setFilm(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [api]);

  if (loading) return <div className="pt-20 p-4 text-center">Loading...</div>;
  if (!film) return <div className="pt-20 p-4 text-center">Film not found</div>;

  const totalRevenue = film.daily_revenues?.reduce((a, b) => a + b.net_revenue, 0) || 0;

  return (
    <div className="pt-20 pb-8 px-4 max-w-7xl mx-auto" data-testid="film-detail-page">
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Poster & Info */}
        <div className="lg:col-span-1">
          <Card className="bg-[#1A1A1A] border-white/10 overflow-hidden">
            <div className="poster-aspect">
              <img 
                src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=600'} 
                alt={film.title}
                className="w-full h-full object-cover"
              />
            </div>
            <CardContent className="p-6 space-y-4">
              <h1 className="font-['Bebas_Neue'] text-3xl">{film.title}</h1>
              <div className="flex items-center gap-2">
                <Badge className="bg-yellow-500/20 text-yellow-500 border-yellow-500/30">{t(film.genre)}</Badge>
                <Badge className={film.status === 'in_theaters' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}>
                  {film.status}
                </Badge>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Quality Score</span>
                  <span className="font-bold">{film.quality_score?.toFixed(1)}%</span>
                </div>
                <Progress value={film.quality_score} className="h-2" />
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                <div className="text-center">
                  <Heart className="w-6 h-6 mx-auto mb-1 text-red-400" />
                  <p className="text-xl font-bold">{film.likes_count}</p>
                  <p className="text-xs text-gray-400">Likes</p>
                </div>
                <div className="text-center">
                  <DollarSign className="w-6 h-6 mx-auto mb-1 text-green-400" />
                  <p className="text-xl font-bold">${totalRevenue.toLocaleString()}</p>
                  <p className="text-xs text-gray-400">Revenue</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Box Office */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader>
              <CardTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2">
                <Globe className="w-6 h-6 text-yellow-500" />
                {t('box_office')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(film.box_office || {}).length === 0 ? (
                <p className="text-gray-400 text-center py-8">Box office data will appear after release</p>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-2 pr-4">
                    {Object.entries(film.box_office).map(([country, data]) => (
                      <div key={country} className="border border-white/10 rounded-lg overflow-hidden">
                        <button
                          className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
                          onClick={() => setExpandedCountry(expandedCountry === country ? null : country)}
                          data-testid={`country-${country}`}
                        >
                          <div className="flex items-center gap-3">
                            <Globe className="w-5 h-5 text-yellow-500" />
                            <span className="font-semibold">{country}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-green-400 font-bold">${data.total_revenue?.toLocaleString()}</span>
                            {expandedCountry === country ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                          </div>
                        </button>
                        {expandedCountry === country && (
                          <div className="p-4 pt-0 border-t border-white/10 bg-black/20">
                            <div className="grid gap-2">
                              {Object.entries(data.cities || {}).map(([city, cityData]) => (
                                <div key={city} className="flex items-center justify-between p-2 rounded bg-white/5">
                                  <span className="text-sm">{city}</span>
                                  <div className="text-right text-sm">
                                    <span className="text-green-400">${cityData.revenue?.toLocaleString()}</span>
                                    <span className="text-gray-400 ml-2">({cityData.theaters} theaters)</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>

          {/* Daily Revenue Chart */}
          {film.daily_revenues?.length > 0 && (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardHeader>
                <CardTitle className="font-['Bebas_Neue'] text-2xl">Daily Revenue</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[200px] flex items-end gap-1">
                  {film.daily_revenues.map((day, i) => {
                    const maxRevenue = Math.max(...film.daily_revenues.map(d => d.net_revenue));
                    const height = (day.net_revenue / maxRevenue) * 100;
                    return (
                      <div 
                        key={i}
                        className="flex-1 bg-yellow-500/30 hover:bg-yellow-500/50 transition-colors rounded-t"
                        style={{ height: `${height}%` }}
                        title={`Day ${day.day}: $${day.net_revenue.toLocaleString()}`}
                      />
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
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
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/films/social/feed')
      .then(res => setFilms(res.data.films))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [api]);

  const handleLike = async (filmId) => {
    try {
      const res = await api.post(`/films/${filmId}/like`);
      setFilms(films.map(f => 
        f.id === filmId 
          ? { ...f, user_liked: res.data.liked, likes_count: res.data.likes_count }
          : f
      ));
    } catch (err) {
      toast.error('Failed to like film');
    }
  };

  if (loading) return <div className="pt-20 p-4 text-center">Loading...</div>;

  return (
    <div className="pt-20 pb-8 px-4 max-w-4xl mx-auto" data-testid="social-feed-page">
      <h1 className="font-['Bebas_Neue'] text-4xl md:text-5xl mb-8">{t('social')}</h1>

      {films.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10 p-12 text-center">
          <Film className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <h3 className="text-xl mb-2">No films to show</h3>
          <p className="text-gray-400">Be the first to release a film!</p>
        </Card>
      ) : (
        <div className="space-y-6">
          {films.map((film, i) => (
            <motion.div
              key={film.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="bg-[#1A1A1A] border-white/10 overflow-hidden" data-testid={`social-film-${film.id}`}>
                <div className="flex">
                  <div className="w-32 sm:w-40 flex-shrink-0">
                    <img 
                      src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=300'} 
                      alt={film.title}
                      className="w-full h-full object-cover cursor-pointer"
                      onClick={() => navigate(`/films/${film.id}`)}
                    />
                  </div>
                  <CardContent className="flex-1 p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 
                          className="font-semibold text-lg cursor-pointer hover:text-yellow-500"
                          onClick={() => navigate(`/films/${film.id}`)}
                        >
                          {film.title}
                        </h3>
                        <p className="text-sm text-gray-400">
                          by {film.owner?.production_house_name || 'Unknown Studio'}
                        </p>
                      </div>
                      <Badge className="bg-yellow-500/20 text-yellow-500">{t(film.genre)}</Badge>
                    </div>
                    
                    <div className="flex items-center gap-4 mt-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        className={`gap-2 ${film.user_liked ? 'text-red-400' : 'text-gray-400'}`}
                        onClick={() => handleLike(film.id)}
                        data-testid={`like-btn-${film.id}`}
                      >
                        <Heart className={`w-5 h-5 ${film.user_liked ? 'fill-red-400' : ''}`} />
                        {film.likes_count}
                      </Button>
                      <div className="flex items-center gap-1 text-gray-400">
                        <Star className="w-4 h-4 text-yellow-500" />
                        <span>{film.quality_score?.toFixed(0)}%</span>
                      </div>
                    </div>
                  </CardContent>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

// Chat Page
const ChatPage = () => {
  const { api, user } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const [rooms, setRooms] = useState({ public: [], private: [] });
  const [activeRoom, setActiveRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get('/chat/rooms')
      .then(res => {
        setRooms(res.data);
        if (res.data.public.length > 0) {
          setActiveRoom(res.data.public[0]);
        }
      })
      .catch(console.error);
  }, [api]);

  useEffect(() => {
    if (activeRoom) {
      setLoading(true);
      api.get(`/chat/rooms/${activeRoom.id}/messages`)
        .then(res => setMessages(res.data))
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [activeRoom, api]);

  const sendMessage = async () => {
    if (!newMessage.trim() || !activeRoom) return;

    try {
      await api.post('/chat/messages', {
        room_id: activeRoom.id,
        content: newMessage,
        message_type: 'text'
      });
      setNewMessage('');
      // Refresh messages
      const res = await api.get(`/chat/rooms/${activeRoom.id}/messages`);
      setMessages(res.data);
    } catch (err) {
      toast.error('Failed to send message');
    }
  };

  return (
    <div className="pt-20 pb-8 px-4 max-w-6xl mx-auto h-[calc(100vh-5rem)]" data-testid="chat-page">
      <div className="grid lg:grid-cols-4 gap-4 h-full">
        {/* Rooms List */}
        <Card className="bg-[#1A1A1A] border-white/10 lg:col-span-1 overflow-hidden">
          <CardHeader className="border-b border-white/10 pb-4">
            <CardTitle className="font-['Bebas_Neue'] text-xl">{t('chat')}</CardTitle>
          </CardHeader>
          <CardContent className="p-2">
            <div className="space-y-1">
              <p className="text-xs text-gray-400 px-2 py-1">Public Rooms</p>
              {rooms.public.map(room => (
                <button
                  key={room.id}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeRoom?.id === room.id ? 'bg-yellow-500/20 text-yellow-500' : 'hover:bg-white/5'
                  }`}
                  onClick={() => setActiveRoom(room)}
                  data-testid={`room-${room.id}`}
                >
                  <MessageSquare className="w-4 h-4 inline mr-2" />
                  {room.name}
                </button>
              ))}
              
              {rooms.private.length > 0 && (
                <>
                  <p className="text-xs text-gray-400 px-2 py-1 mt-4">Private Chats</p>
                  {rooms.private.map(room => (
                    <button
                      key={room.id}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        activeRoom?.id === room.id ? 'bg-yellow-500/20 text-yellow-500' : 'hover:bg-white/5'
                      }`}
                      onClick={() => setActiveRoom(room)}
                    >
                      {room.name}
                    </button>
                  ))}
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Chat Area */}
        <Card className="bg-[#1A1A1A] border-white/10 lg:col-span-3 flex flex-col overflow-hidden">
          {activeRoom ? (
            <>
              <CardHeader className="border-b border-white/10 pb-4">
                <CardTitle className="font-['Bebas_Neue'] text-xl">{activeRoom.name}</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 p-4 overflow-hidden flex flex-col">
                <ScrollArea className="flex-1 pr-4">
                  {loading ? (
                    <div className="text-center py-8 text-gray-400">Loading messages...</div>
                  ) : messages.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">No messages yet. Start the conversation!</div>
                  ) : (
                    <div className="space-y-4">
                      {messages.map(msg => {
                        const isOwn = msg.sender_id === user.id;
                        return (
                          <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[70%] ${isOwn ? 'chat-bubble-user' : 'chat-bubble-other'} px-4 py-2`}>
                              {!isOwn && (
                                <p className="text-xs font-semibold mb-1">{msg.sender?.nickname}</p>
                              )}
                              <p>{msg.content}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </ScrollArea>
                
                <div className="flex gap-2 mt-4 pt-4 border-t border-white/10">
                  <Input
                    value={newMessage}
                    onChange={e => setNewMessage(e.target.value)}
                    placeholder="Type a message..."
                    className="bg-black/20 border-white/10"
                    onKeyPress={e => e.key === 'Enter' && sendMessage()}
                    data-testid="chat-input"
                  />
                  <Button onClick={sendMessage} className="bg-yellow-500 text-black hover:bg-yellow-400" data-testid="send-message-btn">
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              Select a room to start chatting
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/statistics/global'),
      api.get('/statistics/my')
    ])
      .then(([globalRes, myRes]) => {
        setGlobalStats(globalRes.data);
        setMyStats(myRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [api]);

  if (loading) return <div className="pt-20 p-4 text-center">Loading...</div>;

  return (
    <div className="pt-20 pb-8 px-4 max-w-7xl mx-auto" data-testid="statistics-page">
      <h1 className="font-['Bebas_Neue'] text-4xl md:text-5xl mb-8">{t('statistics')}</h1>

      <Tabs defaultValue="my" className="space-y-6">
        <TabsList className="bg-[#1A1A1A] border border-white/10">
          <TabsTrigger value="my" data-testid="my-stats-tab">My Statistics</TabsTrigger>
          <TabsTrigger value="global" data-testid="global-stats-tab">Global</TabsTrigger>
        </TabsList>

        <TabsContent value="my">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Total Films', value: myStats?.total_films || 0, icon: Film, color: 'yellow' },
              { label: 'Total Revenue', value: `$${(myStats?.total_revenue || 0).toLocaleString()}`, icon: DollarSign, color: 'green' },
              { label: 'Total Likes', value: myStats?.total_likes || 0, icon: Heart, color: 'red' },
              { label: 'Avg Quality', value: `${(myStats?.average_quality || 0).toFixed(1)}%`, icon: Star, color: 'blue' }
            ].map(stat => (
              <Card key={stat.label} className="bg-[#1A1A1A] border-white/5">
                <CardContent className="p-6">
                  <stat.icon className={`w-8 h-8 mb-4 text-${stat.color}-500`} />
                  <p className="text-3xl font-bold mb-1">{stat.value}</p>
                  <p className="text-gray-400">{stat.label}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="global">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-[#1A1A1A] border-white/5">
              <CardContent className="p-6">
                <Film className="w-8 h-8 mb-4 text-yellow-500" />
                <p className="text-3xl font-bold mb-1">{globalStats?.total_films || 0}</p>
                <p className="text-gray-400">Total Films</p>
              </CardContent>
            </Card>
            <Card className="bg-[#1A1A1A] border-white/5">
              <CardContent className="p-6">
                <Users className="w-8 h-8 mb-4 text-blue-500" />
                <p className="text-3xl font-bold mb-1">{globalStats?.total_users || 0}</p>
                <p className="text-gray-400">Total Producers</p>
              </CardContent>
            </Card>
            <Card className="bg-[#1A1A1A] border-white/5">
              <CardContent className="p-6">
                <DollarSign className="w-8 h-8 mb-4 text-green-500" />
                <p className="text-3xl font-bold mb-1">${(globalStats?.total_box_office || 0).toLocaleString()}</p>
                <p className="text-gray-400">Global Box Office</p>
              </CardContent>
            </Card>
          </div>

          {globalStats?.genre_distribution && Object.keys(globalStats.genre_distribution).length > 0 && (
            <Card className="bg-[#1A1A1A] border-white/5 mt-6">
              <CardHeader>
                <CardTitle className="font-['Bebas_Neue'] text-2xl">Genre Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(globalStats.genre_distribution).map(([genre, count]) => {
                    const total = Object.values(globalStats.genre_distribution).reduce((a, b) => a + b, 0);
                    const percentage = (count / total) * 100;
                    return (
                      <div key={genre} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{t(genre)}</span>
                          <span>{count} films ({percentage.toFixed(1)}%)</span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Profile Page
const ProfilePage = () => {
  const { api, user } = useContext(AuthContext);
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslations();
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    nickname: user?.nickname || '',
    avatar_url: user?.avatar_url || ''
  });

  const handleSave = async () => {
    try {
      await api.put('/auth/profile', formData);
      toast.success('Profile updated!');
      setEditing(false);
    } catch (err) {
      toast.error('Failed to update profile');
    }
  };

  return (
    <div className="pt-20 pb-8 px-4 max-w-2xl mx-auto" data-testid="profile-page">
      <h1 className="font-['Bebas_Neue'] text-4xl md:text-5xl mb-8">{t('profile')}</h1>

      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-6 space-y-6">
          <div className="flex items-center gap-6">
            <Avatar className="w-24 h-24 border-4 border-yellow-500/30">
              <AvatarImage src={user?.avatar_url} />
              <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-3xl">
                {user?.nickname?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-2xl font-bold">{user?.nickname}</h2>
              <p className="text-gray-400">{user?.production_house_name}</p>
              <p className="text-sm text-gray-500">Owner: {user?.owner_name}</p>
            </div>
          </div>

          <div className="space-y-4 pt-4 border-t border-white/10">
            <div className="space-y-2">
              <Label>Nickname</Label>
              <Input
                value={formData.nickname}
                onChange={e => setFormData({ ...formData, nickname: e.target.value })}
                disabled={!editing}
                className="bg-black/20 border-white/10"
                data-testid="profile-nickname-input"
              />
            </div>

            <div className="space-y-2">
              <Label>Avatar URL</Label>
              <Input
                value={formData.avatar_url}
                onChange={e => setFormData({ ...formData, avatar_url: e.target.value })}
                disabled={!editing}
                placeholder="https://..."
                className="bg-black/20 border-white/10"
                data-testid="profile-avatar-input"
              />
            </div>

            <div className="space-y-2">
              <Label>Language</Label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="bg-black/20 border-white/10" data-testid="profile-language-select">
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
          </div>

          <div className="flex gap-2 pt-4">
            {editing ? (
              <>
                <Button onClick={handleSave} className="bg-yellow-500 text-black hover:bg-yellow-400" data-testid="save-profile-btn">
                  Save Changes
                </Button>
                <Button variant="outline" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              </>
            ) : (
              <Button onClick={() => setEditing(true)} variant="outline" data-testid="edit-profile-btn">
                <Settings className="w-4 h-4 mr-2" /> Edit Profile
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center">
        <Clapperboard className="w-16 h-16 text-yellow-500 animate-pulse" />
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/auth" replace />;
  }
  
  return (
    <>
      <TopNavbar />
      {children}
    </>
  );
};

// Main App
function App() {
  return (
    <div className="min-h-screen bg-[#0F0F10]">
      <BrowserRouter>
        <AuthProvider>
          <LanguageProvider>
            <Toaster position="top-right" theme="dark" />
            <Routes>
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/films" element={<ProtectedRoute><MyFilms /></ProtectedRoute>} />
              <Route path="/films/:id" element={<ProtectedRoute><FilmDetail /></ProtectedRoute>} />
              <Route path="/create" element={<ProtectedRoute><FilmWizard /></ProtectedRoute>} />
              <Route path="/social" element={<ProtectedRoute><SocialFeed /></ProtectedRoute>} />
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
