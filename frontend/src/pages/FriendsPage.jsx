// CineWorld Studio's - FriendsPage
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
import { ClickableNickname } from '../components/shared';
import { LoadingSpinner } from '../components/ErrorBoundary';
import { StudioName } from '../components/StudioName';

// useTranslations imported from contexts

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
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };
  
  const acceptRequest = async (requestId) => {
    try {
      await api.post(`/friends/request/${requestId}/accept`);
      toast.success(language === 'it' ? 'Amicizia accettata!' : 'Friendship accepted!');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
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
      toast.error(e.response?.data?.detail || 'Errore');
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
  

  if (loading) return <LoadingSpinner />;

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
                        <p className="font-semibold text-sm"><ClickableNickname userId={friend.user_id || friend.id} nickname={friend.nickname} /></p>
                        <p className="text-xs text-gray-400"><StudioName name={friend.production_house_name} logoUrl={friend.logo_url} /></p>
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
                        <p className="text-xs text-gray-400"><StudioName name={follower.production_house_name} logoUrl={follower.logo_url} /></p>
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
                        <p className="text-xs text-gray-400"><StudioName name={user.production_house_name} logoUrl={user.logo_url} /></p>
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

// ==================== DOWNLOAD APP PAGE ====================

export default FriendsPage;
