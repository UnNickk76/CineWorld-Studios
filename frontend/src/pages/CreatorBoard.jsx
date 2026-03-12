// CineWorld Studio's - CreatorBoard
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

const CreatorBoard = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);
  const [filter, setFilter] = useState('all');
  const [activeTab, setActiveTab] = useState('messages'); // messages, releases
  const [releaseTitle, setReleaseTitle] = useState('');
  const [releaseChanges, setReleaseChanges] = useState([{ type: 'new', text: '' }]);
  const [publishingRelease, setPublishingRelease] = useState(false);

  useEffect(() => {
    loadMessages();
  }, []);

  const loadMessages = async () => {
    try {
      const res = await api.get('/creator/messages');
      setMessages(res.data.messages);
    } catch (e) {
      if (e.response?.status === 403) {
        navigate('/');
        toast.error('Accesso negato');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async (messageId) => {
    if (!replyText.trim()) return;
    
    setSending(true);
    try {
      await api.post(`/creator/messages/${messageId}/reply`, { reply: replyText });
      toast.success('Risposta inviata!');
      setReplyingTo(null);
      setReplyText('');
      loadMessages();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore invio risposta');
    } finally {
      setSending(false);
    }
  };

  const markAsRead = async (messageId) => {
    try {
      await api.post(`/creator/messages/${messageId}/mark-read`);
      loadMessages();
    } catch (e) {}
  };

  const filteredMessages = messages.filter(m => {
    if (filter === 'all') return true;
    if (filter === 'unread') return m.status === 'unread';
    if (filter === 'replied') return m.status === 'replied';
    return true;
  });

  const unreadCount = messages.filter(m => m.status === 'unread').length;

  const publishRelease = async () => {
    if (!releaseTitle.trim() || releaseChanges.every(c => !c.text.trim())) {
      toast.error('Inserisci titolo e almeno una modifica');
      return;
    }
    setPublishingRelease(true);
    try {
      const validChanges = releaseChanges.filter(c => c.text.trim());
      const res = await api.post('/release-notes', { title: releaseTitle, changes: validChanges });
      toast.success(res.data.message || 'Note di rilascio pubblicate!');
      setReleaseTitle('');
      setReleaseChanges([{ type: 'new', text: '' }]);
    } catch(e) {
      toast.error(e.response?.data?.detail || 'Errore pubblicazione');
    } finally {
      setPublishingRelease(false);
    }
  };

  const addChangeRow = () => setReleaseChanges([...releaseChanges, { type: 'new', text: '' }]);
  const removeChangeRow = (idx) => setReleaseChanges(releaseChanges.filter((_, i) => i !== idx));
  const updateChange = (idx, field, value) => {
    const updated = [...releaseChanges];
    updated[idx] = { ...updated[idx], [field]: value };
    setReleaseChanges(updated);
  };

  if (loading) return <div className="pt-20 text-center">Caricamento...</div>;


  if (loading) return <LoadingSpinner />;

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="creator-board">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => navigate('/')} className="p-1"><ArrowLeft className="w-5 h-5" /></Button>
            <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
              <Mail className="w-8 h-8 text-purple-500" />
              CREATOR BOARD
              {unreadCount > 0 && <Badge className="bg-red-500">{unreadCount}</Badge>}
            </h1>
          </div>
          <Button variant="outline" size="sm" onClick={loadMessages}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-gray-400 text-sm">Messaggi ricevuti dai player</p>
      </motion.div>

      {/* Tabs: Messages / Release Notes */}
      <div className="flex gap-2 mb-4">
        <Button size="sm" variant={activeTab === 'messages' ? 'default' : 'outline'} onClick={() => setActiveTab('messages')} className={activeTab === 'messages' ? 'bg-purple-500' : ''}>
          <Mail className="w-4 h-4 mr-1" /> Messaggi {unreadCount > 0 && <Badge className="ml-1 bg-red-500 text-xs">{unreadCount}</Badge>}
        </Button>
        <Button size="sm" variant={activeTab === 'releases' ? 'default' : 'outline'} onClick={() => setActiveTab('releases')} className={activeTab === 'releases' ? 'bg-amber-500 text-black' : ''}>
          <Newspaper className="w-4 h-4 mr-1" /> Note Rilascio
        </Button>
      </div>

      {activeTab === 'releases' && (
        <Card className="bg-[#1A1A1A] border-amber-500/20 mb-6">
          <CardContent className="p-4">
            <h3 className="font-['Bebas_Neue'] text-xl text-amber-400 mb-3 flex items-center gap-2">
              <Newspaper className="w-5 h-5" /> PUBBLICA NUOVA RELEASE
            </h3>
            <div className="space-y-3">
              <Input 
                placeholder="Titolo della release (es: Sistema Sfide v2)"
                value={releaseTitle} 
                onChange={e => setReleaseTitle(e.target.value)}
                className="bg-black/30 border-white/10"
                data-testid="release-title-input"
              />
              
              {releaseChanges.map((change, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <select 
                    value={change.type} 
                    onChange={e => updateChange(idx, 'type', e.target.value)}
                    className="bg-black/50 border border-white/10 rounded px-2 py-1.5 text-sm w-32"
                  >
                    <option value="new">Novità</option>
                    <option value="improvement">Miglioria</option>
                    <option value="fix">Fix</option>
                  </select>
                  <Input 
                    placeholder="Descrizione modifica..."
                    value={change.text} 
                    onChange={e => updateChange(idx, 'text', e.target.value)}
                    className="bg-black/30 border-white/10 flex-1"
                  />
                  {releaseChanges.length > 1 && (
                    <Button size="sm" variant="ghost" onClick={() => removeChangeRow(idx)} className="text-red-400 h-8 w-8 p-0">
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={addChangeRow} className="border-white/10">
                  <Plus className="w-4 h-4 mr-1" /> Aggiungi riga
                </Button>
                <Button 
                  className="bg-amber-500 hover:bg-amber-600 text-black font-bold flex-1"
                  onClick={publishRelease}
                  disabled={publishingRelease || !releaseTitle.trim()}
                  data-testid="publish-release-btn"
                >
                  {publishingRelease ? 'Pubblicazione...' : 'Pubblica Release'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'messages' && (<>
      {/* Filters */}
      <div className="flex gap-2 mb-4">
        {['all', 'unread', 'replied'].map(f => (
          <Button
            key={f}
            size="sm"
            variant={filter === f ? 'default' : 'outline'}
            onClick={() => setFilter(f)}
            className={filter === f ? 'bg-purple-500' : ''}
          >
            {f === 'all' ? 'Tutti' : f === 'unread' ? 'Non letti' : 'Risposti'}
            {f === 'unread' && unreadCount > 0 && <Badge className="ml-1 bg-red-500 text-xs">{unreadCount}</Badge>}
          </Button>
        ))}
      </div>

      {/* Messages List */}
      <div className="space-y-4">
        {filteredMessages.length === 0 ? (
          <Card className="bg-[#1A1A1A] border-white/5">
            <CardContent className="p-8 text-center">
              <Mail className="w-12 h-12 mx-auto mb-3 text-gray-500" />
              <p className="text-gray-400">Nessun messaggio {filter !== 'all' ? `(${filter})` : ''}</p>
            </CardContent>
          </Card>
        ) : (
          filteredMessages.map(msg => (
            <Card 
              key={msg.id} 
              className={`transition-all ${msg.status === 'unread' ? 'bg-purple-500/10 border-purple-500/30' : 'bg-[#1A1A1A] border-white/5'}`}
              onClick={() => msg.status === 'unread' && markAsRead(msg.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Avatar className="w-10 h-10">
                      <AvatarFallback className="bg-purple-500/20 text-purple-400">{msg.from_nickname?.[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-semibold">{msg.from_nickname}</p>
                      <p className="text-xs text-gray-400">{msg.from_email}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className={msg.status === 'unread' ? 'bg-red-500' : msg.status === 'replied' ? 'bg-green-500' : 'bg-gray-500'}>
                      {msg.status === 'unread' ? 'Nuovo' : msg.status === 'replied' ? 'Risposto' : 'Letto'}
                    </Badge>
                    <p className="text-xs text-gray-500 mt-1">{new Date(msg.created_at).toLocaleString()}</p>
                  </div>
                </div>

                <div className="bg-black/30 rounded-lg p-3 mb-3">
                  <p className="font-semibold text-purple-400 text-sm mb-2">📬 {msg.subject}</p>
                  <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                </div>

                {/* Reply Section */}
                {msg.reply && (
                  <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 mb-3">
                    <p className="text-xs text-green-400 mb-1">✓ Tua risposta ({new Date(msg.replied_at).toLocaleString()}):</p>
                    <p className="text-sm">{msg.reply}</p>
                  </div>
                )}

                {!msg.reply && (
                  <>
                    {replyingTo === msg.id ? (
                      <div className="space-y-3">
                        <Textarea
                          placeholder="Scrivi la tua risposta..."
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          className="bg-black/30 border-white/10"
                        />
                        <div className="flex gap-2">
                          <Button 
                            className="bg-green-500 hover:bg-green-600 flex-1"
                            onClick={() => handleReply(msg.id)}
                            disabled={sending || !replyText.trim()}
                          >
                            {sending ? 'Invio...' : 'Invia Risposta'}
                          </Button>
                          <Button variant="outline" onClick={() => { setReplyingTo(null); setReplyText(''); }}>
                            Annulla
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <Button 
                        variant="outline" 
                        className="w-full border-purple-500/30 text-purple-400"
                        onClick={() => setReplyingTo(msg.id)}
                      >
                        <Send className="w-4 h-4 mr-2" /> Rispondi
                      </Button>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
      </>)}
    </div>
  );
};

// Profile Page with AI Avatar Generation

export default CreatorBoard;
