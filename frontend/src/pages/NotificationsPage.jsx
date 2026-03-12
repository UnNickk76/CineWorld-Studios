// CineWorld Studio's - NotificationsPage
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { LoadingSpinner } from '../components/ErrorBoundary';

// useTranslations imported from contexts

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
      challenge_welcome: <Swords className="w-5 h-5 text-pink-400" />,
      challenge_invite: <Swords className="w-5 h-5 text-pink-400" />,
      challenge_won: <Trophy className="w-5 h-5 text-green-400" />,
      challenge_lost: <Swords className="w-5 h-5 text-red-400" />,
      creator_reply: <Mail className="w-5 h-5 text-purple-400" />,
      system: <Info className="w-5 h-5 text-gray-400" />
    };
    return icons[type] || icons.system;
  };
  
  if (loading) return <div className="pt-16 p-4 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;
  

  if (loading) return <LoadingSpinner />;

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
                    // Smart navigation based on notification type
                    const navPath = notif.link || notif.data?.path;
                    if (navPath) {
                      navigate(navPath);
                    } else {
                      // Fallback routing based on notification type
                      const typeRoutes = {
                        'versus_result': '/challenges',
                        'challenge_accepted': '/challenges',
                        'challenge_completed': '/challenges',
                        'challenge_cancelled': '/challenges',
                        'challenge_welcome': '/challenges',
                        'offline_battle_result': '/challenges',
                        'offline_challenge_result': '/challenges',
                        'offline_challenge_report': '/challenges',
                        'film_released': notif.data?.film_id ? `/film/${notif.data.film_id}` : '/my-films',
                        'trailer_ready': notif.data?.film_id ? `/film/${notif.data.film_id}` : '/my-films',
                        'trailer_generated': notif.data?.film_id ? `/film/${notif.data.film_id}` : '/my-films',
                        'trailer_announcement': notif.data?.film_id ? `/film/${notif.data.film_id}` : '/my-films',
                        'trailer_error': notif.data?.film_id ? `/film/${notif.data.film_id}` : '/my-films',
                        'festival_nomination': '/festivals',
                        'festival_award': '/festivals',
                        'festival_started': '/festivals',
                        'friend_request': '/social',
                        'friend_accepted': '/social',
                        'major_invite': '/social',
                        'review_published': notif.data?.film_id ? `/film/${notif.data.film_id}` : '/my-films',
                        'minigame_challenge': '/games',
                        'box_office_update': notif.data?.film_id ? `/film/${notif.data.film_id}` : '/my-films',
                      };
                      const route = typeRoutes[notif.type];
                      if (route) navigate(route);
                    }
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
                  {(notif.link || notif.data?.path || notif.data?.film_id || ['versus_result','challenge_accepted','challenge_completed','offline_battle_result','offline_challenge_result','offline_challenge_report','film_released','trailer_ready','trailer_generated','festival_nomination','festival_award','friend_request','review_published','minigame_challenge'].includes(notif.type)) && (
                    <ChevronRight className="w-4 h-4 text-gray-500 flex-shrink-0 self-center" />
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default NotificationsPage;
