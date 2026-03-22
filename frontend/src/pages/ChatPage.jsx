import React, { useState, useEffect, useRef, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, LanguageContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import {
  Send, Users, MessageSquare, X, Heart, Film, Lightbulb, Coffee,
  ChevronRight, Loader2, UserPlus, UserCheck, Clock, Mail
} from 'lucide-react';
import { ClickableNickname } from '../components/shared';

const ROOM_ICONS = {
  'generale': MessageSquare,
  'produzioni': Film,
  'strategie': Lightbulb,
  'offtopic': Coffee,
  'general': MessageSquare,
  'producers': Film,
  'box-office': MessageSquare,
};

/* ─── Presence dot ─── */
function PresenceDot({ presence, size = 'sm' }) {
  const s = size === 'sm' ? 'w-2 h-2' : 'w-2.5 h-2.5';
  const colors = {
    online: 'bg-green-500',
    recent: 'bg-yellow-500',
    offline: 'bg-red-500/60',
  };
  return <span className={`inline-block ${s} rounded-full ${colors[presence] || colors.offline}`} />;
}

/* ─── User Profile Modal (Social Card with films) ─── */
function UserProfileModal({ userId, isOpen, onClose, api, onStartDM }) {
  const { language } = useContext(LanguageContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [friendStatus, setFriendStatus] = useState('none');
  const [films, setFilms] = useState([]);
  const navigate = useNavigate();
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (isOpen && userId) {
      setLoading(true);
      api.get(`/users/${userId}/social-card`)
        .then(r => {
          setData(r.data);
          setFilms(r.data.films || []);
          setFriendStatus(r.data.friend_status || 'none');
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [isOpen, userId, api]);

  const sendFriendRequest = async () => {
    try {
      setActionLoading('friend');
      await api.post('/friends/request', { user_id: userId });
      setFriendStatus('pending');
      toast.success(language === 'it' ? 'Richiesta di amicizia inviata!' : 'Friend request sent!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const handleLikeFilm = async (filmId) => {
    try {
      const res = await api.post(`/films/${filmId}/like`);
      setFilms(prev => prev.map(f => f.id === filmId
        ? { ...f, user_liked: res.data.liked, likes_count: res.data.likes_count }
        : f
      ));
    } catch (e) {
      const msg = e.response?.data?.detail || '';
      if (msg.includes('tuoi film')) toast.error('Non puoi mettere like ai tuoi film!');
      else toast.error(msg || 'Errore');
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#111113] border-white/10 max-w-md max-h-[85vh] overflow-y-auto p-0" data-testid="user-profile-modal">
        {loading ? (
          <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-yellow-500 animate-spin" /></div>
        ) : data ? (
          <div className="p-4 space-y-3">
            <DialogHeader>
              <div className="flex items-center gap-3">
                <Avatar className="w-11 h-11">
                  <AvatarImage src={data.user?.avatar_url} />
                  <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-lg">{data.user?.nickname?.[0]}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <DialogTitle className="text-sm flex items-center gap-1.5">
                    {data.user?.nickname}
                    <PresenceDot presence={data.is_online ? 'online' : 'offline'} size="md" />
                  </DialogTitle>
                  <p className="text-[10px] text-gray-500">{data.user?.production_house_name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {data.user?.level && <Badge className="h-4 text-[8px] bg-yellow-500/15 text-yellow-400">Lv.{data.user.level}</Badge>}
                  </div>
                </div>
              </div>
            </DialogHeader>

            {/* Action buttons */}
            {!data.is_own_profile && (
              <div className="flex gap-1.5">
                <Button size="sm" className="flex-1 bg-yellow-500 text-black hover:bg-yellow-400 text-[10px] h-7"
                  onClick={() => { onClose(); onStartDM(userId); }}
                  data-testid="social-card-dm-btn">
                  <MessageSquare className="w-3 h-3 mr-1" /> Messaggio
                </Button>
                <Button size="sm" variant="outline" className="flex-1 text-[10px] h-7 border-gray-700"
                  onClick={() => { onClose(); navigate(`/player/${userId}`); }}
                  data-testid="social-card-profile-btn">
                  Profilo <ChevronRight className="w-3 h-3 ml-0.5" />
                </Button>
                {friendStatus === 'friends'
                  ? <Button size="sm" variant="outline" className="h-7 px-2 border-green-500/30 text-green-400" disabled><UserCheck className="w-3 h-3" /></Button>
                  : friendStatus === 'pending'
                    ? <Button size="sm" variant="outline" className="h-7 px-2 border-yellow-500/30 text-yellow-400" disabled><Clock className="w-3 h-3" /></Button>
                    : <Button size="sm" variant="outline" className="h-7 px-2 border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                        onClick={sendFriendRequest} disabled={actionLoading === 'friend'}
                        data-testid="social-card-friend-btn">
                        <UserPlus className="w-3 h-3" />
                      </Button>
                }
              </div>
            )}

            {/* Films section */}
            <div>
              <p className="text-[9px] text-gray-500 uppercase tracking-widest font-bold mb-1.5">
                {language === 'it' ? 'Ultimi Film' : 'Recent Films'} ({films.length})
              </p>
              {films.length === 0 ? (
                <div className="text-center py-4 bg-black/20 rounded-lg">
                  <Film className="w-5 h-5 text-gray-700 mx-auto mb-1" />
                  <p className="text-[10px] text-gray-600">{language === 'it' ? 'Nessun film ancora' : 'No films yet'}</p>
                </div>
              ) : (
                <div className="grid grid-cols-6 gap-1" data-testid="social-card-films">
                  {films.map(f => (
                    <div key={f.id} className="group relative rounded overflow-hidden bg-[#0a0a0c] border border-white/5 hover:border-yellow-500/30 transition-all"
                      data-testid={`social-film-${f.id}`}>
                      {/* Poster - clickable */}
                      <div className="aspect-[2/3] relative cursor-pointer" onClick={() => { onClose(); navigate(`/films/${f.id}`); }}>
                        {f.poster_url ? (
                          <img src={f.poster_url.startsWith('/') ? `${BACKEND_URL}${f.poster_url}` : f.poster_url}
                            alt={f.title} loading="lazy" className="w-full h-full object-cover"
                            onError={e => { e.target.style.display = 'none'; }} />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-gray-900">
                            <Film className="w-2.5 h-2.5 text-gray-700" />
                          </div>
                        )}
                        {/* Like overlay at bottom */}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-0.5 pb-0.5 pt-1.5">
                          <button
                            className={`flex items-center gap-0.5 ${f.user_liked ? 'text-red-400' : 'text-white/60 hover:text-red-400'}`}
                            onClick={(e) => { e.stopPropagation(); handleLikeFilm(f.id); }}
                            data-testid={`social-like-${f.id}`}
                          >
                            <Heart className={`w-2 h-2 ${f.user_liked ? 'fill-red-400' : ''}`} />
                            <span className="text-[6px] font-bold">{f.likes_count || 0}</span>
                          </button>
                        </div>
                      </div>
                      {/* Title */}
                      <div className="px-0.5 py-px">
                        <p className="text-[6px] text-white truncate leading-tight" title={f.title}>{f.title}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : <p className="text-center py-8 text-gray-500 text-sm">Utente non trovato</p>}
      </DialogContent>
    </Dialog>
  );
}


/* ═══════════════ MAIN CHAT PAGE ═══════════════ */
const ChatPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();

  const [rooms, setRooms] = useState({ public: [], private: [] });
  const [activeRoom, setActiveRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [presenceUsers, setPresenceUsers] = useState([]);
  const [showPanel, setShowPanel] = useState(null); // null | 'rooms' | 'users'
  const [activeTab, setActiveTab] = useState('public'); // public | private
  const [loadingDM, setLoadingDM] = useState(null);
  const [profileUserId, setProfileUserId] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Fetch rooms + presence on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [roomsRes, presRes] = await Promise.all([
          api.get('/chat/rooms'),
          api.get('/users/presence')
        ]);
        setRooms(roomsRes.data);
        setPresenceUsers(presRes.data?.users || []);
        if (!activeRoom && roomsRes.data.public.length > 0) {
          setActiveRoom(roomsRes.data.public[0]);
        }
      } catch {}
    };
    fetchData();
  }, [api]);

  // Heartbeat
  useEffect(() => {
    const hb = async () => { try { await api.post('/users/heartbeat'); } catch {} };
    hb();
    const iv = setInterval(hb, 60000);
    return () => clearInterval(iv);
  }, [api]);

  // Refresh presence & rooms every 30s
  useEffect(() => {
    const iv = setInterval(async () => {
      try {
        const [roomsRes, presRes] = await Promise.all([
          api.get('/chat/rooms'),
          api.get('/users/presence')
        ]);
        setRooms(roomsRes.data);
        setPresenceUsers(presRes.data?.users || []);
      } catch {}
    }, 30000);
    return () => clearInterval(iv);
  }, [api]);

  // Fetch messages on room change + auto-refresh
  useEffect(() => {
    if (!activeRoom) return;
    const fetchMsgs = async () => {
      try {
        const r = await api.get(`/chat/rooms/${activeRoom.id}/messages`);
        setMessages(r.data);
      } catch {}
    };
    fetchMsgs();
    const iv = setInterval(fetchMsgs, 8000);
    return () => clearInterval(iv);
  }, [activeRoom, api]);

  const sendMsg = async () => {
    if (!newMessage.trim() || !activeRoom) return;
    try {
      await api.post('/chat/messages', { room_id: activeRoom.id, content: newMessage, message_type: 'text' });
      setNewMessage('');
      const r = await api.get(`/chat/rooms/${activeRoom.id}/messages`);
      setMessages(r.data);
    } catch { toast.error('Errore invio messaggio'); }
  };

  const startDM = async (targetId) => {
    setLoadingDM(targetId);
    try {
      const res = await api.post(`/chat/direct/${targetId}`);
      const roomsRes = await api.get('/chat/rooms');
      setRooms(roomsRes.data);
      setActiveRoom(res.data);
      setActiveTab('private');
      setShowPanel(null);
    } catch { toast.error('Impossibile avviare chat'); }
    finally { setLoadingDM(null); }
  };

  const onlineCount = presenceUsers.filter(u => u.presence === 'online').length;
  const recentCount = presenceUsers.filter(u => u.presence === 'recent').length;

  return (
    <div className="pt-14 pb-16 h-screen flex flex-col bg-[#0A0A0B]" data-testid="chat-page">
      {/* ─── Top bar: room name + toggles ─── */}
      <div className="flex items-center gap-2 px-2 py-1.5 border-b border-white/5 flex-shrink-0 bg-[#0e0e10]">
        {/* Rooms toggle (mobile) */}
        <button
          className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-semibold bg-white/5 hover:bg-white/10 transition-colors lg:hidden"
          onClick={() => setShowPanel(showPanel === 'rooms' ? null : 'rooms')}
          data-testid="toggle-rooms-btn"
        >
          <MessageSquare className="w-3 h-3" />
          Stanze
        </button>

        {/* Current room name */}
        <div className="flex-1 min-w-0 text-center">
          {activeRoom && (
            <div className="flex items-center justify-center gap-1.5">
              {(() => { const Icon = ROOM_ICONS[activeRoom.id] || MessageSquare; return <Icon className="w-3.5 h-3.5 text-yellow-400" />; })()}
              <span className="text-xs font-bold text-white truncate">
                {activeRoom.is_private && activeRoom.other_user ? activeRoom.other_user.nickname : activeRoom.name}
              </span>
              {activeRoom.is_private && activeRoom.other_user && (
                <PresenceDot presence={activeRoom.other_user.is_online ? 'online' : 'offline'} />
              )}
            </div>
          )}
        </div>

        {/* Users toggle */}
        <button
          className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-semibold bg-white/5 hover:bg-white/10 transition-colors"
          onClick={() => setShowPanel(showPanel === 'users' ? null : 'users')}
          data-testid="toggle-users-btn"
        >
          <Users className="w-3 h-3" />
          <span className="text-green-400">{onlineCount}</span>
          {recentCount > 0 && <span className="text-yellow-400">+{recentCount}</span>}
        </button>
      </div>

      {/* ─── Main area: panels + chat ─── */}
      <div className="flex-1 flex min-h-0 relative">

        {/* ─── ROOMS PANEL (desktop: always visible, mobile: overlay) ─── */}
        <div className={`
          ${showPanel === 'rooms' ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          absolute lg:static inset-y-0 left-0 z-30 w-52 lg:w-44
          bg-[#0e0e10] border-r border-white/5
          transition-transform duration-200 ease-out
          flex flex-col
        `}>
          <div className="p-2 flex-shrink-0">
            <div className="flex items-center justify-between mb-2">
              <p className="text-[9px] text-gray-500 uppercase tracking-widest font-bold">Stanze</p>
              <button className="lg:hidden" onClick={() => setShowPanel(null)}><X className="w-3.5 h-3.5 text-gray-500" /></button>
            </div>

            {/* Public / Private tabs */}
            <div className="flex gap-1 mb-2">
              <button
                className={`flex-1 text-[9px] font-semibold py-1 rounded ${activeTab === 'public' ? 'bg-yellow-500/20 text-yellow-400' : 'text-gray-500 hover:text-gray-300'}`}
                onClick={() => setActiveTab('public')}
                data-testid="tab-public"
              >Pubbliche</button>
              <button
                className={`flex-1 text-[9px] font-semibold py-1 rounded relative ${activeTab === 'private' ? 'bg-yellow-500/20 text-yellow-400' : 'text-gray-500 hover:text-gray-300'}`}
                onClick={() => setActiveTab('private')}
                data-testid="tab-private"
              >
                Private
                {rooms.private.length > 0 && <Badge className="absolute -top-1 -right-1 h-3.5 min-w-[14px] px-0.5 text-[8px] bg-yellow-500 text-black">{rooms.private.length}</Badge>}
              </button>
            </div>
          </div>

          <ScrollArea className="flex-1 px-2 pb-2">
            {activeTab === 'public' ? (
              <div className="space-y-0.5">
                {rooms.public.map(room => {
                  const Icon = ROOM_ICONS[room.id] || MessageSquare;
                  const isActive = activeRoom?.id === room.id;
                  return (
                    <button key={room.id}
                      className={`w-full text-left px-2 py-1.5 rounded-md transition-all flex items-center gap-2 ${
                        isActive ? 'bg-yellow-500/15 text-yellow-400' : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
                      }`}
                      onClick={() => { setActiveRoom(room); setShowPanel(null); }}
                      data-testid={`room-${room.id}`}
                    >
                      <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="text-[10px] font-semibold truncate">{room.name}</p>
                        {room.description && <p className="text-[8px] text-gray-600 truncate">{room.description}</p>}
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="space-y-0.5">
                {rooms.private.length === 0 ? (
                  <div className="text-center py-4">
                    <Mail className="w-5 h-5 text-gray-700 mx-auto mb-1" />
                    <p className="text-[10px] text-gray-600 mb-1">Nessuna chat privata</p>
                    <p className="text-[8px] text-gray-700">Clicca su un giocatore per iniziare</p>
                  </div>
                ) : rooms.private.map(room => {
                  const isActive = activeRoom?.id === room.id;
                  const lastTime = room.last_message?.created_at
                    ? new Date(room.last_message.created_at).toLocaleDateString([], { day: '2-digit', month: '2-digit' })
                    : '';
                  return (
                    <button key={room.id}
                      className={`w-full text-left px-2 py-1.5 rounded-md transition-all flex items-center gap-2 ${
                        isActive ? 'bg-yellow-500/15' : 'hover:bg-white/5'
                      }`}
                      onClick={() => { setActiveRoom(room); setShowPanel(null); }}
                      data-testid={`private-room-${room.id}`}
                    >
                      <div className="relative flex-shrink-0">
                        <Avatar className="w-6 h-6">
                          <AvatarImage src={room.other_user?.avatar_url} />
                          <AvatarFallback className="text-[8px] bg-gray-800">{room.other_user?.nickname?.[0]}</AvatarFallback>
                        </Avatar>
                        <span className={`absolute -bottom-px -right-px w-2 h-2 rounded-full border border-[#0e0e10] ${
                          room.other_user?.is_online ? 'bg-green-500' : 'bg-red-500/50'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <span className={`text-[10px] font-semibold truncate ${isActive ? 'text-yellow-400' : 'text-gray-300'}`}>{room.other_user?.nickname}</span>
                          {lastTime && <span className="text-[7px] text-gray-600 flex-shrink-0">{lastTime}</span>}
                        </div>
                        {room.last_message && <p className="text-[8px] text-gray-600 truncate">{room.last_message.content}</p>}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* ─── CHAT AREA ─── */}
        <div className="flex-1 flex flex-col min-h-0 min-w-0">
          {activeRoom ? (
            <>
              {/* Messages */}
              <ScrollArea className="flex-1 min-h-0 px-2 py-1">
                <div className="space-y-1.5">
                  {messages.length === 0 ? (
                    <div className="text-center py-12 text-gray-600 text-xs">
                      <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-20" />
                      {language === 'it' ? 'Nessun messaggio. Inizia la conversazione!' : 'No messages yet. Start the conversation!'}
                    </div>
                  ) : messages.map(msg => {
                    const isOwn = msg.sender_id === user?.id;
                    const isBot = msg.sender?.is_bot || msg.user_id === 'system_bot';
                    const isTrailer = msg.message_type === 'trailer_announcement';
                    const isCreator = msg.type === 'creator_reply';
                    return (
                      <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] sm:max-w-[70%] px-2.5 py-1.5 rounded-xl text-xs ${
                          isCreator ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-bl-sm'
                          : isTrailer ? 'bg-purple-500/15 border border-purple-500/20 rounded-bl-sm cursor-pointer hover:bg-purple-500/20'
                          : isOwn ? 'bg-yellow-500 text-black rounded-br-sm'
                          : isBot ? 'bg-blue-500/15 border border-blue-500/20 rounded-bl-sm'
                          : 'bg-white/8 rounded-bl-sm'
                        }`}
                          onClick={() => isTrailer && msg.film_id && navigate(`/film/${msg.film_id}`)}
                        >
                          {isCreator && (
                            <div className="flex items-center gap-1 mb-0.5">
                              <Mail className="w-3 h-3 text-purple-400" />
                              <Badge className="h-3 px-1 text-[7px] bg-purple-500 text-white">CREATOR</Badge>
                            </div>
                          )}
                          {!isOwn && !activeRoom.is_private && !isCreator && (
                            <div className="flex items-center gap-1 mb-0.5">
                              <span className="text-[10px] font-bold">
                                <ClickableNickname userId={msg.sender_id} nickname={msg.sender?.nickname || '?'} className="text-[10px] font-bold" />
                              </span>
                              {isBot && <Badge className="h-3 px-0.5 text-[7px] bg-blue-500/30 text-blue-400">BOT</Badge>}
                            </div>
                          )}
                          {isTrailer ? (
                            <div className="flex items-center gap-1.5">
                              <Film className="w-4 h-4 text-purple-400 flex-shrink-0" />
                              <div>
                                <p>{msg.content}</p>
                                <p className="text-[9px] text-purple-300 mt-0.5">{language === 'it' ? 'Clicca per vedere' : 'Click to watch'}</p>
                              </div>
                            </div>
                          ) : <p className="whitespace-pre-wrap">{msg.content}</p>}
                          <p className={`text-[9px] mt-0.5 ${isOwn ? 'text-black/40' : 'text-gray-600'}`}>
                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Input */}
              <div className="flex gap-1.5 px-2 py-1.5 border-t border-white/5 flex-shrink-0 bg-[#0e0e10]">
                <Input
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  placeholder={language === 'it' ? 'Scrivi un messaggio...' : 'Type a message...'}
                  className="h-8 text-xs bg-black/30 border-white/10"
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMsg()}
                  data-testid="chat-input"
                />
                <Button onClick={sendMsg} size="sm" className="bg-yellow-500 text-black h-8 w-8 p-0" data-testid="send-message-btn">
                  <Send className="w-3.5 h-3.5" />
                </Button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-600">
              <div className="text-center">
                <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-15" />
                <p className="text-xs">{language === 'it' ? 'Seleziona una stanza per chattare' : 'Select a room to chat'}</p>
              </div>
            </div>
          )}
        </div>

        {/* ─── USERS PANEL (right side) ─── */}
        <div className={`
          ${showPanel === 'users' ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
          absolute lg:static inset-y-0 right-0 z-30 w-56 lg:w-48
          bg-[#0e0e10] border-l border-white/5
          transition-transform duration-200 ease-out
          flex flex-col
        `}>
          <div className="p-2 flex-shrink-0 flex items-center justify-between">
            <p className="text-[9px] text-gray-500 uppercase tracking-widest font-bold">
              Giocatori
              <span className="text-green-400 ml-1">{onlineCount}</span>
              {recentCount > 0 && <span className="text-yellow-400 ml-0.5">+{recentCount}</span>}
            </p>
            <button className="lg:hidden" onClick={() => setShowPanel(null)}><X className="w-3.5 h-3.5 text-gray-500" /></button>
          </div>

          <ScrollArea className="flex-1 px-1 pb-2">
            <div className="space-y-px">
              {presenceUsers.map(u => (
                <div key={u.id}
                  className="flex items-center gap-1.5 px-1.5 py-1 rounded hover:bg-white/5 group"
                  data-testid={`user-row-${u.id}`}
                >
                  {/* Clickable avatar + name */}
                  <button
                    className="flex items-center gap-1.5 flex-1 min-w-0 text-left"
                    onClick={() => { if (!u.is_bot) setProfileUserId(u.id); }}
                    disabled={u.is_bot}
                  >
                    <div className="relative flex-shrink-0">
                      <Avatar className="w-5 h-5">
                        <AvatarImage src={u.avatar_url} />
                        <AvatarFallback className="text-[8px] bg-gray-800">{u.nickname?.[0]}</AvatarFallback>
                      </Avatar>
                      <span className={`absolute -bottom-px -right-px w-2 h-2 rounded-full border border-[#0e0e10] ${
                        u.presence === 'online' ? 'bg-green-500' : u.presence === 'recent' ? 'bg-yellow-500' : 'bg-red-500/50'
                      }`} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1">
                        <span className={`text-[10px] font-medium truncate ${
                          u.presence === 'online' ? 'text-white' : u.presence === 'recent' ? 'text-gray-400' : 'text-gray-600'
                        }`}>{u.nickname}</span>
                        {u.is_bot && u.is_moderator && <Badge className="h-3 px-0.5 text-[6px] bg-red-500/20 text-red-400">MOD</Badge>}
                        {u.is_bot && !u.is_moderator && <Badge className="h-3 px-0.5 text-[6px] bg-blue-500/20 text-blue-400">BOT</Badge>}
                      </div>
                      <p className="text-[7px] text-gray-600 truncate">{u.is_bot ? u.role : u.production_house_name}</p>
                    </div>
                  </button>

                  {/* DM button */}
                  {!u.is_bot && (
                    <button
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-white/10"
                      onClick={() => startDM(u.id)}
                      disabled={loadingDM === u.id}
                      data-testid={`dm-user-${u.id}`}
                    >
                      {loadingDM === u.id
                        ? <Loader2 className="w-3 h-3 text-gray-400 animate-spin" />
                        : <MessageSquare className="w-3 h-3 text-gray-500 hover:text-yellow-400" />}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Backdrop for mobile panels */}
        {showPanel && (
          <div className="absolute inset-0 bg-black/50 z-20 lg:hidden" onClick={() => setShowPanel(null)} />
        )}
      </div>

      {/* User Profile Modal */}
      <UserProfileModal
        userId={profileUserId}
        isOpen={!!profileUserId}
        onClose={() => setProfileUserId(null)}
        api={api}
        onStartDM={startDM}
      />
    </div>
  );
};

export default ChatPage;
