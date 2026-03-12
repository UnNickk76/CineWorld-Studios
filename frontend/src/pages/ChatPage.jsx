// CineWorld Studio's - ChatPage
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

// useTranslations imported from contexts

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

  const UserProfileModal = ({ userId, isOpen, onClose }) => {
    const { language } = useContext(LanguageContext);
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [friendStatus, setFriendStatus] = useState(null);
    const [actionLoading, setActionLoading] = useState(null);
    const navigate = useNavigate();
    
    useEffect(() => {
      if (isOpen && userId) {
        setLoading(true);
        Promise.all([
          api.get(`/users/${userId}/full-profile`),
          api.get('/friends'),
          api.get('/friends/requests')
        ]).then(([profileRes, friendsRes, requestsRes]) => {
          setProfile(profileRes.data);
          const isFriend = friendsRes.data?.some(f => f.id === userId);
          const hasPendingRequest = requestsRes.data?.outgoing?.some(r => r.user?.id === userId);
          setFriendStatus(isFriend ? 'friends' : hasPendingRequest ? 'pending' : 'none');
          setLoading(false);
        }).catch(() => setLoading(false));
      }
    }, [isOpen, userId]);
    
    if (!isOpen) return null;
    
    const sendFriendRequest = async () => {
      try {
        setActionLoading('friend');
        await api.post('/friends/request', { user_id: userId });
        setFriendStatus('pending');
        toast.success(language === 'it' ? 'Richiesta di amicizia inviata!' : 'Friend request sent!');
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Error');
      } finally { setActionLoading(null); }
    };
    

    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="user-profile-modal">
          {loading ? (
            <div className="flex items-center justify-center py-12"><div className="animate-spin h-8 w-8 border-2 border-yellow-500 border-t-transparent rounded-full"></div></div>
          ) : profile ? (
            <>
              <DialogHeader>
                <div className="flex items-center gap-4">
                  <Avatar className="w-16 h-16"><AvatarImage src={profile.user?.avatar_url} /><AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xl">{profile.user?.nickname?.[0]}</AvatarFallback></Avatar>
                  <div>
                    <DialogTitle className="text-xl flex items-center gap-2">{profile.user?.nickname}
                      {profile.is_online ? <Badge className="bg-green-500/20 text-green-400 text-xs">Online</Badge> : <Badge className="bg-gray-500/20 text-gray-400 text-xs">Offline</Badge>}
                    </DialogTitle>
                    <p className="text-sm text-gray-400">{profile.user?.production_house_name}</p>
                  </div>
                </div>
              </DialogHeader>
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 my-4">
                {[{l:'Film',v:profile.stats?.total_films,c:'text-yellow-500'},{l:'Revenue',v:`$${((profile.stats?.total_revenue||0)/1e6).toFixed(1)}M`,c:'text-green-500'},{l:'Like',v:profile.stats?.total_likes,c:'text-pink-500'},{l:'Qualità',v:`${profile.stats?.avg_quality||0}%`,c:'text-blue-500'},{l:'Premi',v:profile.stats?.awards_count,c:'text-purple-500'},{l:'Infra',v:profile.stats?.infrastructure_count,c:'text-orange-500'}].map(s=>(
                  <div key={s.l} className="bg-black/30 rounded p-2 text-center"><p className={`text-lg font-bold ${s.c}`}>{s.v}</p><p className="text-xs text-gray-400">{s.l}</p></div>
                ))}
              </div>
              {!profile.is_own_profile && (
                <div className="flex flex-wrap gap-2 mt-4">
                  <Button className="flex-1 bg-yellow-500 text-black hover:bg-yellow-400" onClick={() => { onClose(); navigate('/chat'); }}><MessageSquare className="w-4 h-4 mr-2" /> Messaggio</Button>
                  {friendStatus === 'friends' ? <Button variant="outline" className="flex-1 border-green-500/30 text-green-400" disabled><UserCheck className="w-4 h-4 mr-2" /> Amici</Button>
                   : friendStatus === 'pending' ? <Button variant="outline" className="flex-1 border-yellow-500/30 text-yellow-400" disabled><Clock className="w-4 h-4 mr-2" /> In Attesa</Button>
                   : <Button variant="outline" className="flex-1 border-blue-500/30 text-blue-400 hover:bg-blue-500/10" onClick={sendFriendRequest} disabled={actionLoading === 'friend'}><UserPlus className="w-4 h-4 mr-2" /> Amicizia</Button>}
                </div>
              )}
            </>
          ) : <div className="text-center py-12 text-gray-400">User not found</div>}
        </DialogContent>
      </Dialog>
    );
  };

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

  // Refresh rooms periodically (online users already polled by TopNavbar)
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const roomsRes = await api.get('/chat/rooms');
        setRooms(roomsRes.data);
      } catch(e) {}
    }, 60000);
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
    }, 10000); // Was 5s, now 10s
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
                              <span className="text-xs font-semibold truncate hover:text-yellow-500 cursor-pointer" onClick={(e) => { e.stopPropagation(); if(!u.is_bot) { const pp = document.querySelector('[data-player-popup-ctx]'); } }}><ClickableNickname userId={u.is_bot ? null : u.id} nickname={u.nickname} className="text-xs font-semibold" /></span>
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
                                <span className="text-xs truncate hover:text-yellow-500 cursor-pointer"><ClickableNickname userId={u.id} nickname={u.nickname} className="text-xs" /></span>
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
                          <div className={`max-w-[70%] px-3 py-1.5 rounded-xl text-sm ${
                            msg.type === 'creator_reply'
                              ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-2 border-purple-500/50 rounded-bl-sm'
                              : msg.message_type === 'trailer_announcement' 
                                ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-bl-sm cursor-pointer hover:from-purple-500/30 hover:to-pink-500/30'
                                : msg.sender_id === user.id 
                                  ? 'bg-yellow-500 text-black rounded-br-sm' 
                                  : msg.sender?.is_bot 
                                    ? 'bg-blue-500/20 border border-blue-500/30 rounded-bl-sm' 
                                    : 'bg-white/10 rounded-bl-sm'
                          }`}
                          onClick={() => msg.message_type === 'trailer_announcement' && msg.film_id && navigate(`/film/${msg.film_id}`)}
                          >
                            {msg.type === 'creator_reply' && (
                              <div className="flex items-center gap-1 mb-1">
                                <Mail className="w-4 h-4 text-purple-400" />
                                <Badge className="h-4 px-1.5 text-[10px] bg-purple-500 text-white">CREATOR</Badge>
                              </div>
                            )}
                            {msg.sender_id !== user.id && !activeRoom.is_private && msg.type !== 'creator_reply' && (
                              <div className="flex items-center gap-1 mb-0.5">
                                <p className="text-xs font-semibold"><ClickableNickname userId={msg.sender_id || msg.user_id} nickname={msg.sender?.nickname || msg.user?.nickname} className="text-xs font-semibold" /></p>
                                {(msg.sender?.is_bot || msg.user_id === 'system_bot') && <Badge className="h-3 px-1 text-[8px] bg-blue-500/30 text-blue-400">BOT</Badge>}
                              </div>
                            )}
                            {msg.message_type === 'trailer_announcement' ? (
                              <div className="flex items-center gap-2">
                                <Film className="w-5 h-5 text-purple-400" />
                                <div>
                                  <p>{msg.content}</p>
                                  <p className="text-xs text-purple-300 mt-1">{language === 'it' ? 'Clicca per vedere' : 'Click to watch'}</p>
                                </div>
                              </div>
                            ) : (
                              <p>{msg.content}</p>
                            )}
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

export default ChatPage;
