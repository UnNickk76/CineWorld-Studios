import React, { useState, useEffect, useRef, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, LanguageContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PlayerBadge } from '../components/PlayerBadge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import {
  Send, Users, MessageSquare, X, Heart, Film, Lightbulb, Coffee,
  ChevronRight, Loader2, UserPlus, UserCheck, Clock, Mail, ImagePlus, ZoomIn, Trash2, Flag,
  Gamepad2, Swords
} from 'lucide-react';
import { ClickableNickname } from '../components/shared';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
function UserProfileModal({ userId, isOpen, onClose, api, onStartDM, onReportUser, onChallenge }) {
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
                <Button size="sm" className="flex-1 bg-cyan-600 hover:bg-cyan-700 text-[10px] h-7"
                  onClick={() => { onClose(); onChallenge(userId, data.user?.nickname); }}
                  data-testid="social-card-challenge-btn">
                  <Gamepad2 className="w-3 h-3 mr-1" /> Sfida
                </Button>
                <Button size="sm" variant="outline" className="text-[10px] h-7 border-gray-700 px-2"
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
            {/* Report user button */}
            {!data.is_own_profile && (
              <Button size="sm" variant="outline" className="w-full text-[10px] h-7 border-red-500/20 text-red-400 hover:bg-red-500/10"
                onClick={() => { onClose(); onReportUser(userId, data.user?.nickname); }}
                data-testid="social-card-report-btn">
                <Flag className="w-3 h-3 mr-1" />Segnala Utente
              </Button>
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


/* ─── Report Modal ─── */
function ReportModal({ isOpen, onClose, onSubmit, targetLabel }) {
  const [reason, setReason] = useState('');
  const [sending, setSending] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    setSending(true);
    await onSubmit(reason);
    setSending(false);
    setReason('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[90] bg-black/70 flex items-center justify-center p-4" onClick={onClose} data-testid="report-modal">
      <div className="bg-[#111113] border border-red-500/30 rounded-xl max-w-sm w-full p-4 space-y-3" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-2">
          <Flag className="w-4 h-4 text-red-400" />
          <span className="text-sm font-bold text-white">Segnala {targetLabel}</span>
        </div>
        <textarea
          value={reason}
          onChange={e => setReason(e.target.value)}
          placeholder="Motivo della segnalazione (opzionale)..."
          className="w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none resize-none h-20"
          data-testid="report-reason-input"
        />
        <div className="flex gap-2 justify-end">
          <Button size="sm" variant="outline" className="text-xs border-gray-700 text-gray-400" onClick={onClose} disabled={sending}>
            Annulla
          </Button>
          <Button size="sm" className="bg-red-600 hover:bg-red-700 text-xs" onClick={handleSubmit} disabled={sending} data-testid="report-submit-btn">
            {sending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Flag className="w-3 h-3 mr-1" />}
            Invia Segnalazione
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ─── Fullscreen Image Viewer ─── */
function ImageViewer({ src, onClose }) {
  if (!src) return null;
  return (
    <div className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-4" onClick={onClose} data-testid="image-viewer">
      <button className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20" onClick={onClose}><X className="w-5 h-5 text-white" /></button>
      <img src={src} alt="" className="max-w-full max-h-full object-contain rounded-lg" onClick={e => e.stopPropagation()} />
    </div>
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
  const [viewImage, setViewImage] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [reportTarget, setReportTarget] = useState(null); // {type, id, label}
  const [challengeTarget, setChallengeTarget] = useState(null); // {userId, nickname}
  const [arcadeGames, setArcadeGames] = useState([]);
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Mobile keyboard detection via visualViewport API
  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;
    const onResize = () => {
      const isKb = vv.height < window.innerHeight * 0.75;
      setKeyboardOpen(isKb);
      if (isKb && chatContainerRef.current) {
        chatContainerRef.current.style.height = `${vv.height}px`;
      } else if (chatContainerRef.current) {
        chatContainerRef.current.style.height = '';
      }
      // Scroll input into view when keyboard opens
      if (isKb) {
        setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
      }
    };
    vv.addEventListener('resize', onResize);
    return () => vv.removeEventListener('resize', onResize);
  }, []);

  // Auto-scroll
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Fetch rooms + presence on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [roomsRes, presRes, gamesRes] = await Promise.all([
          api.get('/chat/rooms'),
          api.get('/users/presence'),
          api.get('/arcade/games'),
        ]);
        setRooms(roomsRes.data);
        setPresenceUsers(presRes.data?.users || []);
        setArcadeGames(gamesRes.data || []);
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

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !activeRoom) return;
    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = '';

    // Validate client-side
    const allowed = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type)) {
      toast.error('Solo immagini JPG, PNG o WEBP');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Immagine troppo grande (max 5MB)');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const uploadRes = await api.post('/chat/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const imageUrl = uploadRes.data.image_url;

      // Send as image message
      await api.post('/chat/messages', {
        room_id: activeRoom.id,
        content: '',
        message_type: 'image',
        image_url: imageUrl
      });
      // Refresh messages
      const r = await api.get(`/chat/rooms/${activeRoom.id}/messages`);
      setMessages(r.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore upload immagine');
    } finally {
      setUploading(false);
    }
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

  const submitReport = async (reason) => {
    if (!reportTarget) return;
    try {
      await api.post('/reports', {
        target_type: reportTarget.type,
        target_id: reportTarget.id,
        reason,
      });
      toast.success('Segnalazione inviata! Un admin la revisioner\u00e0.');
    } catch (e) {
      const detail = e.response?.data?.detail || 'Errore';
      toast.error(detail);
    }
  };

  const sendChallenge = async (gameId) => {
    if (!challengeTarget) return;
    try {
      const res = await api.post('/arcade/chat-challenge', {
        target_user_id: challengeTarget.userId,
        game_id: gameId,
      });
      toast.success(res.data.message || 'Sfida inviata!');
      setChallengeTarget(null);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore invio sfida'); }
  };

  const onlineCount = presenceUsers.filter(u => u.presence === 'online').length;
  const recentCount = presenceUsers.filter(u => u.presence === 'recent').length;

  return (
    <div ref={chatContainerRef} className={`pt-14 ${keyboardOpen ? 'pb-0' : 'pb-16'} h-[100dvh] flex flex-col bg-[#0A0A0B] overflow-x-hidden`} data-testid="chat-page">
      {/* ─── Top bar: room name + toggles ─── */}
      <div className="flex items-center gap-2 px-2 py-1.5 border-b border-white/5 flex-shrink-0 bg-[#0e0e10]">
        {/* Rooms toggle (mobile) */}
        <button
          className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-semibold bg-white/5 hover:bg-white/10 transition-colors md:hidden"
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
      <div className="flex-1 flex min-h-0 relative overflow-hidden">

        {/* ─── ROOMS PANEL (desktop: always visible, mobile: overlay) ─── */}
        <div className={`
          ${showPanel === 'rooms' ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          absolute md:static inset-y-0 left-0 z-30 w-[75vw] max-w-[220px] md:w-44
          bg-[#0e0e10] border-r border-white/5
          transition-transform duration-200 ease-out
          flex flex-col
        `}>
          <div className="p-2 flex-shrink-0">
            <div className="flex items-center justify-between mb-2">
              <p className="text-[9px] text-gray-500 uppercase tracking-widest font-bold">Stanze</p>
              <button className="md:hidden" onClick={() => setShowPanel(null)}><X className="w-3.5 h-3.5 text-gray-500" /></button>
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
                          <span className={`text-[10px] font-semibold truncate ${isActive ? 'text-yellow-400' : 'text-gray-300'}`}><PlayerBadge badge={room.other_user?.badge} badgeExpiry={room.other_user?.badge_expiry} badges={room.other_user?.badges} size="xs" />{room.other_user?.nickname}</span>
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
                      <div key={msg.id} className={`group/msg flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
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
                                <PlayerBadge badge={msg.sender?.badge} badgeExpiry={msg.sender?.badge_expiry} badges={msg.sender?.badges} size="xs" /><ClickableNickname userId={msg.sender_id} nickname={msg.sender?.nickname || '?'} className="text-[10px] font-bold" />
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
                          ) : msg.message_type === 'image' && msg.image_url ? (
                            <div>
                              {msg.content && <p className="whitespace-pre-wrap mb-1">{msg.content}</p>}
                              <img
                                src={msg.image_url.startsWith('/') ? `${BACKEND_URL}${msg.image_url}` : msg.image_url}
                                alt=""
                                className="max-w-[200px] max-h-[200px] rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                                onClick={(e) => { e.stopPropagation(); setViewImage(msg.image_url.startsWith('/') ? `${BACKEND_URL}${msg.image_url}` : msg.image_url); }}
                                loading="lazy"
                                data-testid={`chat-image-${msg.id}`}
                              />
                              {isOwn && (Date.now() - new Date(msg.created_at).getTime()) < 120000 && (
                                <button
                                  className="mt-1 text-[8px] text-red-400/70 hover:text-red-400 transition-colors"
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    try {
                                      await api.delete(`/chat/messages/${msg.id}/image`);
                                      setMessages(prev => prev.map(m => m.id === msg.id
                                        ? { ...m, message_type: 'text', content: 'Immagine eliminata', image_url: null, deleted: true }
                                        : m
                                      ));
                                    } catch (err) { toast.error(err.response?.data?.detail || 'Errore'); }
                                  }}
                                  data-testid={`delete-image-${msg.id}`}
                                >
                                  <Trash2 className="w-2.5 h-2.5 inline mr-0.5" />Elimina
                                </button>
                              )}
                            </div>
                          ) : msg.deleted ? (
                            <p className="text-gray-500 italic text-[10px]">{msg.content}</p>
                          ) : msg.type === 'minigame_challenge' ? (
                            <div className="flex items-center gap-2 py-1" data-testid={`challenge-msg-${msg.id}`}>
                              <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center shrink-0">
                                <Gamepad2 className="w-4 h-4 text-cyan-400" />
                              </div>
                              <div className="flex-1">
                                <p className="text-[11px] font-semibold text-cyan-400">{msg.data?.game_name || 'Minigioco'}</p>
                                <p className="text-[10px]">{msg.content}</p>
                              </div>
                              {!isOwn && msg.data?.challenge_id && (
                                <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700 text-[9px] h-6 px-2"
                                  onClick={() => navigate('/minigiochi')}
                                  data-testid={`accept-challenge-${msg.id}`}>
                                  <Swords className="w-3 h-3 mr-0.5" /> Gioca
                                </Button>
                              )}
                            </div>
                          ) : <p className="whitespace-pre-wrap break-words">{msg.content}</p>}
                          <p className={`text-[9px] mt-0.5 ${isOwn ? 'text-black/40' : 'text-gray-600'}`}>
                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                          {/* Report button (visible on hover, only for others' messages) */}
                          {!isOwn && !isBot && !msg.deleted && (
                            <button
                              className="opacity-0 group-hover/msg:opacity-100 transition-opacity mt-0.5 text-[8px] text-gray-600 hover:text-red-400 flex items-center gap-0.5"
                              onClick={(e) => { e.stopPropagation(); setReportTarget({ type: msg.message_type === 'image' ? 'image' : 'message', id: msg.id, label: msg.message_type === 'image' ? 'immagine' : 'messaggio' }); }}
                              data-testid={`report-msg-${msg.id}`}
                            >
                              <Flag className="w-2.5 h-2.5" />Segnala
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Input - sticky bottom with high z-index */}
              <div className="flex items-center gap-1 px-2 py-1.5 border-t border-white/5 flex-shrink-0 bg-[#0e0e10] sticky bottom-0 z-50">
                {/* Image upload button */}
                <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden"
                  onChange={handleImageUpload} data-testid="chat-file-input" />
                <button
                  className="flex-shrink-0 p-1.5 rounded-md text-gray-500 hover:text-yellow-400 hover:bg-white/5 transition-colors disabled:opacity-30"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading || !activeRoom}
                  data-testid="chat-upload-btn"
                >
                  {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ImagePlus className="w-4 h-4" />}
                </button>
                <Input
                  ref={inputRef}
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  placeholder={language === 'it' ? 'Scrivi un messaggio...' : 'Type a message...'}
                  className="h-8 text-xs bg-black/30 border-white/10 flex-1 min-w-0"
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMsg()}
                  onFocus={() => setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 300)}
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
          ${showPanel === 'users' ? 'translate-x-0' : 'translate-x-full md:translate-x-0'}
          absolute md:static inset-y-0 right-0 z-30 w-[75vw] max-w-[220px] md:w-48
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
            <button className="md:hidden" onClick={() => setShowPanel(null)}><X className="w-3.5 h-3.5 text-gray-500" /></button>
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
                        }`}><PlayerBadge badge={u.badge} badgeExpiry={u.badge_expiry} badges={u.badges} size="xs" />{u.nickname}</span>
                        {u.is_bot && u.is_moderator && <Badge className="h-3 px-0.5 text-[6px] bg-red-500/20 text-red-400">MOD</Badge>}
                        {u.is_bot && !u.is_moderator && <Badge className="h-3 px-0.5 text-[6px] bg-blue-500/20 text-blue-400">BOT</Badge>}
                      </div>
                      <p className="text-[7px] text-gray-600 truncate">
                        {u.is_bot ? u.role : u.game_status === 'playing' ? (
                          <span className="text-cyan-400">In gioco</span>
                        ) : u.game_status === 'in_vs' ? (
                          <span className="text-purple-400">In VS 1v1</span>
                        ) : u.production_house_name}
                      </p>
                    </div>
                  </button>

                  {/* DM + Challenge buttons */}
                  {!u.is_bot && (
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-0.5">
                      <button
                        className="p-0.5 rounded hover:bg-white/10"
                        onClick={() => startDM(u.id)}
                        disabled={loadingDM === u.id}
                        data-testid={`dm-user-${u.id}`}
                        title="Messaggio"
                      >
                        {loadingDM === u.id
                          ? <Loader2 className="w-3 h-3 text-gray-400 animate-spin" />
                          : <MessageSquare className="w-3 h-3 text-gray-500 hover:text-yellow-400" />}
                      </button>
                      <button
                        className="p-0.5 rounded hover:bg-white/10"
                        onClick={() => setChallengeTarget({ userId: u.id, nickname: u.nickname })}
                        data-testid={`challenge-user-${u.id}`}
                        title="Sfida Minigioco"
                      >
                        <Gamepad2 className="w-3 h-3 text-gray-500 hover:text-cyan-400" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Backdrop for mobile panels */}
        {showPanel && (
          <div className="absolute inset-0 bg-black/50 z-20 md:hidden" onClick={() => setShowPanel(null)} />
        )}
      </div>

      {/* User Profile Modal */}
      <UserProfileModal
        userId={profileUserId}
        isOpen={!!profileUserId}
        onClose={() => setProfileUserId(null)}
        api={api}
        onStartDM={startDM}
        onChallenge={(uid, nickname) => {
          setProfileUserId(null);
          setChallengeTarget({ userId: uid, nickname });
        }}
        onReportUser={(uid, nickname) => {
          setProfileUserId(null);
          setReportTarget({ type: 'user', id: uid, label: `utente "${nickname}"` });
        }}
      />

      {/* Report Modal */}
      <ReportModal
        isOpen={!!reportTarget}
        onClose={() => setReportTarget(null)}
        onSubmit={submitReport}
        targetLabel={reportTarget?.label || ''}
      />

      {/* Fullscreen Image Viewer */}
      <ImageViewer src={viewImage} onClose={() => setViewImage(null)} />

      {/* Game Picker Dialog for Chat Challenges */}
      {challengeTarget && (
        <Dialog open={!!challengeTarget} onOpenChange={() => setChallengeTarget(null)}>
          <DialogContent className="bg-[#111113] border-cyan-500/20 max-w-sm max-h-[70vh] overflow-y-auto p-4" data-testid="game-picker-dialog">
            <DialogHeader>
              <DialogTitle className="text-sm flex items-center gap-2">
                <Gamepad2 className="w-4 h-4 text-cyan-400" />
                Sfida {challengeTarget.nickname}
              </DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-1.5 mt-2">
              {arcadeGames.map(g => (
                <button key={g.id}
                  className="flex items-center gap-2 p-2 rounded-lg bg-white/5 hover:bg-cyan-500/10 border border-transparent hover:border-cyan-500/30 transition-all text-left"
                  onClick={() => sendChallenge(g.id)}
                  data-testid={`pick-game-${g.id}`}>
                  <Gamepad2 className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span className="text-[11px] font-medium truncate">{g.name}</span>
                </button>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default ChatPage;
