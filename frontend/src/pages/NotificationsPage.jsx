// CineWorld Studio's - NotificationsPage
// Dynamic notification system with severity levels and narrative style

import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, LanguageContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Film, Star, Award, TrendingUp, Clock, Users, Bell,
  X, Check, Info, Loader2, RefreshCw, Trash2,
  Heart, MessageSquare, Swords, Trophy, Target,
  ChevronRight, AlertTriangle, AlertCircle, Sparkles,
  Flame, Eye, Zap, UserPlus, UserCheck, Crown, GraduationCap,
  Mail, BarChart3, CheckCircle, TrendingDown, Camera, Gavel, MapPin
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { useNotifications } from '../components/NotificationProvider';
import { Tv, Building, Gamepad2, DollarSign } from 'lucide-react';

const CATEGORY_TABS = [
  { key: 'all', label: 'Tutte', icon: Bell },
  { key: 'production', label: 'Produzione', icon: Film },
  { key: 'tv_episodes', label: 'TV', icon: Tv },
  { key: 'economy', label: 'Economia', icon: DollarSign },
  { key: 'events', label: 'Eventi', icon: Flame },
  { key: 'social', label: 'Social', icon: Heart },
  { key: 'infrastructure', label: 'Infra', icon: Building },
  { key: 'arena', label: 'Arena', icon: Swords },
  { key: 'minigames', label: 'Giochi', icon: Gamepad2 },
];

const NotificationsPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const { refreshNotifications, categoryStats } = useNotifications();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actorPopup, setActorPopup] = useState(null);
  const [filter, setFilter] = useState('all'); // all, critical, important, positive
  const [categoryFilter, setCategoryFilter] = useState('all');
  
  const loadNotifications = React.useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: '80' });
      if (categoryFilter !== 'all') params.append('category', categoryFilter);
      const res = await api.get(`/notifications?${params.toString()}`);
      setNotifications(res.data.notifications);
    } catch (e) {}
    setLoading(false);
  }, [api, categoryFilter]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);
  
  const markAllRead = async () => {
    try {
      await api.post('/notifications/read', { notification_ids: [] });
      loadNotifications();
      refreshNotifications();
      toast.success('Tutte le notifiche segnate come lette');
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
      setNotifications(prev => prev.filter(n => n.id !== id));
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
      acting_school: <GraduationCap className="w-5 h-5 text-yellow-400" />,
      like: <Heart className="w-5 h-5 text-red-400" />,
      like_received: <Heart className="w-5 h-5 text-red-400" />,
      private_message: <MessageSquare className="w-5 h-5 text-blue-400" />,
      private_message_received: <MessageSquare className="w-5 h-5 text-blue-400" />,
      coming_soon: <Clock className="w-5 h-5 text-yellow-400" />,
      coming_soon_support: <Flame className="w-5 h-5 text-green-400" />,
      coming_soon_boycott: <AlertTriangle className="w-5 h-5 text-red-400" />,
      coming_soon_time_change: <Clock className="w-5 h-5 text-orange-400" />,
      coming_soon_completed: <CheckCircle className="w-5 h-5 text-yellow-400" />,
      phase_completed: <CheckCircle className="w-5 h-5 text-green-400" />,
      production_problem: <AlertCircle className="w-5 h-5 text-red-400" />,
      legal_action_won: <Gavel className="w-5 h-5 text-green-400" />,
      legal_action_lost: <Gavel className="w-5 h-5 text-red-400" />,
      pvp_counter_attack: <Swords className="w-5 h-5 text-orange-400" />,
      high_revenue: <TrendingUp className="w-5 h-5 text-green-400" />,
      flop_warning: <TrendingDown className="w-5 h-5 text-red-400" />,
      chart_entry: <BarChart3 className="w-5 h-5 text-green-400" />,
      film_interaction: <Eye className="w-5 h-5 text-cyan-400" />,
      film_city_impact: <MapPin className="w-5 h-5 text-amber-400" />,
      speed_up_used: <Zap className="w-5 h-5 text-yellow-400" />,
      film_release: <Camera className="w-5 h-5 text-yellow-400" />,
      system: <Info className="w-5 h-5 text-gray-400" />
    };
    return icons[type] || icons.system;
  };

  const getSeverityBadge = (notif) => {
    const sev = notif.severity || notif.priority;
    if (sev === 'critical' || sev === 'high') {
      return <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-[9px] px-1.5 py-0">Critica</Badge>;
    }
    if (sev === 'important' || sev === 'medium') {
      return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 text-[9px] px-1.5 py-0">Importante</Badge>;
    }
    if (sev === 'positive' || sev === 'low') {
      return <Badge className="bg-green-500/20 text-green-400 border-green-500/30 text-[9px] px-1.5 py-0">Positiva</Badge>;
    }
    return null;
  };

  const getSeverityBorder = (notif) => {
    const sev = notif.severity;
    if (sev === 'critical') return 'border-l-2 border-l-red-500';
    if (sev === 'important') return 'border-l-2 border-l-yellow-500';
    if (sev === 'positive') return 'border-l-2 border-l-green-500';
    return '';
  };

  const handleNotifClick = (notif) => {
    if (!notif.read) markAsRead(notif.id);
    if (notif.type === 'acting_school' && notif.data?.actor_name) {
      setActorPopup(notif.data);
      return;
    }
    // Direct link takes priority (PvP notifications set link to /hq)
    const navPath = notif.link || notif.data?.path;
    if (navPath) { 
      navigate(navPath); return; 
    }
    // Film-related notifications → open film popup
    const filmTypes = [
      'coming_soon', 'coming_soon_support', 'coming_soon_boycott', 'coming_soon_time_change',
      'coming_soon_completed', 'phase_completed', 'production_problem', 'film_interaction'
    ];
    const projectId = notif.data?.project_id || notif.data?.film_project_id;
    if (filmTypes.includes(notif.type) && projectId) {
      navigate(`/create-film?film=${projectId}`);
      return;
    }
    // Fallback: type-based routing
    const typeRoutes = {
      'challenge_invite': notif.data?.challenge_id ? `/challenges?accept=${notif.data.challenge_id}` : '/challenges',
      'challenge_won': '/challenges', 'challenge_lost': '/challenges',
      'versus_result': '/challenges', 'challenge_accepted': '/challenges',
      'challenge_completed': '/challenges', 'challenge_cancelled': '/challenges',
      'challenge_welcome': '/challenges',
      'offline_battle_result': '/challenges', 'offline_challenge_result': '/challenges',
      'film_released': '/my-films', 'trailer_ready': '/my-films',
      'festival_nomination': '/festivals', 'festival_award': '/festivals',
      'friend_request': '/friends', 'friend_accepted': '/friends',
      'major_invite': '/major',
      'private_message': '/chat', 'private_message_received': '/chat',
      'coming_soon_support': '/create-film', 'coming_soon_boycott': '/create-film',
      'coming_soon_time_change': '/create-film', 'coming_soon_completed': '/create-film',
      'phase_completed': '/create-film', 'production_problem': '/create-film',
      'legal_action_won': '/hq', 'legal_action_lost': '/hq',
      'pvp_counter_attack': '/hq',
      'high_revenue': '/films', 'flop_warning': '/films',
      'film_interaction': '/create-film', 'like_received': '/films',
      'system': '/release-notes', 'welcome': '/',
    };
    const route = typeRoutes[notif.type];
    if (route) navigate(route);
  };

  const filteredNotifs = notifications.filter(n => {
    if (filter === 'all') return true;
    const sev = n.severity || (n.priority === 'high' ? 'critical' : n.priority === 'medium' ? 'important' : 'positive');
    return sev === filter;
  });

  const unreadCount = notifications.filter(n => !n.read).length;
  const criticalCount = notifications.filter(n => !n.read && (n.severity === 'critical' || n.priority === 'high')).length;

  if (loading) return <div className="pt-16 p-4 text-center"><Loader2 className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;

  return (
    <div className="pt-16 pb-20 px-3 max-w-2xl mx-auto" data-testid="notifications-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bell className="w-7 h-7 text-yellow-500" />
          <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl">Notifiche</h1>
          {unreadCount > 0 && (
            <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-xs">{unreadCount} nuove</Badge>
          )}
        </div>
        <div className="flex gap-1.5">
          <Button size="sm" variant="ghost" className="h-8 w-8 p-0" onClick={loadNotifications} data-testid="refresh-notifications">
            <RefreshCw className="w-4 h-4" />
          </Button>
          {unreadCount > 0 && (
            <Button size="sm" variant="outline" className="h-8 text-xs" onClick={markAllRead} data-testid="mark-all-read">
              <Check className="w-3.5 h-3.5 mr-1" /> Segna tutto
            </Button>
          )}
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-1 mb-2 overflow-x-auto pb-1 scrollbar-hide" data-testid="category-tabs">
        {CATEGORY_TABS.map(cat => {
          const Icon = cat.icon;
          const count = cat.key === 'all' ? 0 : (categoryStats[cat.key] || 0);
          return (
            <button
              key={cat.key}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-medium transition-all whitespace-nowrap ${
                categoryFilter === cat.key
                  ? 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30'
                  : 'bg-white/5 text-gray-500 hover:bg-white/10 hover:text-gray-300'
              }`}
              onClick={() => { setCategoryFilter(cat.key); setLoading(true); }}
              data-testid={`category-${cat.key}`}
            >
              <Icon className="w-3 h-3" /> {cat.label}
              {count > 0 && (
                <span className="min-w-[14px] h-3.5 px-1 bg-red-500/80 text-white text-[8px] font-bold rounded-full flex items-center justify-center">{count}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Severity Filter Tabs */}
      <div className="flex gap-1.5 mb-3 overflow-x-auto pb-1">
        {[
          { key: 'all', label: 'Tutte', color: 'text-white' },
          { key: 'critical', label: 'Critiche', color: 'text-red-400', icon: <AlertTriangle className="w-3.5 h-3.5" /> },
          { key: 'important', label: 'Importanti', color: 'text-yellow-400', icon: <Clock className="w-3.5 h-3.5" /> },
          { key: 'positive', label: 'Positive', color: 'text-green-400', icon: <Sparkles className="w-3.5 h-3.5" /> },
        ].map(f => (
          <button
            key={f.key}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap ${
              filter === f.key 
                ? `bg-white/15 ${f.color} border border-white/20` 
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
            onClick={() => setFilter(f.key)}
            data-testid={`filter-${f.key}`}
          >
            {f.icon} {f.label}
            {f.key === 'critical' && criticalCount > 0 && (
              <span className="min-w-[16px] h-4 px-1 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center ml-0.5">{criticalCount}</span>
            )}
          </button>
        ))}
      </div>

      {/* Notification List */}
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-2 sm:p-3">
          {filteredNotifs.length === 0 ? (
            <div className="text-center py-10">
              <Bell className="w-10 h-10 mx-auto text-gray-500/30 mb-2" />
              <p className="text-gray-500 text-sm">{filter === 'all' ? 'Nessuna notifica' : `Nessuna notifica ${filter === 'critical' ? 'critica' : filter === 'important' ? 'importante' : 'positiva'}`}</p>
            </div>
          ) : (
            <div className="space-y-1">
              <AnimatePresence initial={false}>
                {filteredNotifs.map((notif, idx) => (
                  <motion.div
                    key={notif.id}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2, delay: idx * 0.02 }}
                    className={`flex items-start gap-2.5 p-2.5 rounded-lg cursor-pointer transition-colors ${
                      notif.read 
                        ? 'bg-white/3 hover:bg-white/5' 
                        : 'bg-white/8 hover:bg-white/12 border border-white/10'
                    } ${getSeverityBorder(notif)}`}
                    onClick={() => handleNotifClick(notif)}
                    data-testid={`notification-${notif.id}`}
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      {getIconForType(notif.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      {/* CineWorld News source badge */}
                      {notif.source === 'CineWorld News' && (
                        <div className="flex items-center gap-1 mb-0.5">
                          <span className="text-[8px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-yellow-500/15 text-yellow-400 border border-yellow-500/20">CineWorld News</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <p className={`font-semibold text-sm leading-tight ${notif.read ? 'text-gray-300' : 'text-white'}`}>{notif.title}</p>
                        {!notif.read && getSeverityBadge(notif)}
                        {notif.data?.group_count > 1 && (
                          <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[9px] px-1.5 py-0">x{notif.data.group_count}</Badge>
                        )}
                      </div>
                      <p className={`text-xs mt-0.5 leading-snug ${notif.read ? 'text-gray-500' : 'text-gray-400'}`}>{notif.message}</p>
                      {/* Event description */}
                      {notif.data?.event_desc && (
                        <p className="text-[10px] text-gray-500 mt-0.5 italic leading-snug">"{notif.data.event_desc}"</p>
                      )}
                      {/* Effect in minutes with color */}
                      {notif.data?.effect_minutes != null && notif.data.effect_minutes !== 0 && (
                        <div className="flex items-center gap-1 mt-1">
                          <Clock className="w-3 h-3 flex-shrink-0" style={{ color: notif.data.effect_minutes > 0 ? '#f87171' : '#4ade80' }} />
                          <span className="text-[10px] font-bold" style={{ color: notif.data.effect_minutes > 0 ? '#f87171' : '#4ade80' }}>
                            {notif.data.effect_minutes > 0 ? '+' : ''}{notif.data.effect_minutes} min
                          </span>
                          <span className="text-[9px] text-gray-600 ml-0.5">
                            {notif.data.effect_minutes > 0 ? 'Tempo aumentato' : 'Tempo ridotto'}
                          </span>
                        </div>
                      )}
                      {/* Boycott type */}
                      {notif.data?.boycott_type && (
                        <div className="flex items-center gap-1 mt-1">
                          <AlertTriangle className="w-3 h-3 text-red-400 flex-shrink-0" />
                          <span className="text-[10px] text-red-400 font-medium">{notif.data.boycott_type}</span>
                        </div>
                      )}
                      <p className="text-[10px] text-gray-600 mt-1">
                        {new Date(notif.created_at).toLocaleDateString('it-IT', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        className="text-gray-600 hover:text-red-400 p-1 transition-colors"
                        onClick={(e) => { e.stopPropagation(); deleteNotification(notif.id); }}
                        data-testid={`delete-notif-${notif.id}`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                      <ChevronRight className="w-4 h-4 text-gray-600" />
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Acting School Actor Popup */}
      <Dialog open={!!actorPopup} onOpenChange={() => setActorPopup(null)}>
        <DialogContent className="bg-[#1A1A1B] border-gray-800 text-white max-w-md" data-testid="actor-popup">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-yellow-400" />
              {actorPopup?.actor_name}
            </DialogTitle>
            <DialogDescription className="text-gray-400">
              {actorPopup?.action === 'kept' 
                ? `${actorPopup?.trainer || '?'} lo utilizzer\u00e0 nei suoi film`
                : 'Disponibile per tutti i produttori!'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <Badge className={`text-xs ${
                actorPopup?.category === 'star' ? 'bg-yellow-900/60 text-yellow-300' :
                actorPopup?.category === 'known' ? 'bg-blue-900/60 text-blue-300' :
                actorPopup?.category === 'emerging' ? 'bg-green-900/60 text-green-300' :
                'bg-gray-800 text-gray-400'
              }`}>
                {actorPopup?.category === 'star' ? 'Star' : actorPopup?.category === 'known' ? 'Conosciuto' : actorPopup?.category === 'emerging' ? 'Emergente' : 'Sconosciuto'}
              </Badge>
              {actorPopup?.imdb_rating && (
                <span className="text-xs text-yellow-400 flex items-center gap-1">
                  <Star className="w-3 h-3" /> {actorPopup.imdb_rating.toFixed(1)} IMDb
                </span>
              )}
            </div>
            <div className="space-y-1.5">
              {actorPopup?.skills && Object.entries(actorPopup.skills).map(([key, val]) => {
                const change = actorPopup?.skill_changes?.[key] || 0;
                return (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-400 w-28 truncate">
                    {SKILL_TRANSLATIONS?.[key]?.[language] || key}
                  </span>
                  <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${val}%`, background: val > 70 ? '#22c55e' : val > 40 ? '#eab308' : '#ef4444' }} />
                  </div>
                  <span className="text-[10px] font-mono text-gray-300 w-6 text-right">{val}</span>
                  {change !== 0 && (
                    <span className={`text-[10px] font-bold ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {change > 0 ? '\u25b2' : '\u25bc'}
                    </span>
                  )}
                </div>
                );
              })}
            </div>
            {actorPopup?.action === 'released' && actorPopup?.cost_per_film && (
              <div className="pt-2 border-t border-gray-800">
                <p className="text-xs text-gray-400 mb-2">
                  Costo per film: <span className="text-white font-bold">${actorPopup.cost_per_film.toLocaleString()}</span>
                </p>
                <Button 
                  className="w-full bg-cyan-700 hover:bg-cyan-800" 
                  onClick={() => { setActorPopup(null); navigate('/create-film'); }}
                  data-testid="hire-from-notification"
                >
                  <Film className="w-4 h-4 mr-2" />
                  Ingaggia - Crea un Film
                </Button>
              </div>
            )}
            {actorPopup?.action === 'kept' && (
              <div className="pt-2 border-t border-gray-800 text-center">
                <p className="text-xs text-gray-500 italic">
                  Questo attore e' nel cast privato del produttore
                </p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default NotificationsPage;
