// CineWorld Studio's - MajorPage
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

// useTranslations imported from contexts

const MajorPage = () => {
  const { api, user } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const [majorData, setMajorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', description: '', max_members: 20, logo_prompt: '' });
  const [creating, setCreating] = useState(false);
  const [inviteUserId, setInviteUserId] = useState('');
  const [allUsers, setAllUsers] = useState([]);
  
  const t = (key) => {
    const translations = {
      major: language === 'it' ? 'Major' : 'Major',
      createMajor: language === 'it' ? 'Crea Major' : 'Create Major',
      yourMajor: language === 'it' ? 'La Tua Major' : 'Your Major',
      noMajor: language === 'it' ? 'Non sei in una Major' : "You're not in a Major",
      levelRequired: language === 'it' ? 'Richiesto livello 20 per creare' : 'Level 20 required to create',
      members: language === 'it' ? 'Membri' : 'Members',
      invite: language === 'it' ? 'Invita' : 'Invite',
      weeklyChallenge: language === 'it' ? 'Sfida Settimanale' : 'Weekly Challenge',
      bonuses: language === 'it' ? 'Bonus' : 'Bonuses',
      activities: language === 'it' ? 'Attività' : 'Activities',
      rankings: language === 'it' ? 'Classifiche' : 'Rankings'
    };
    return translations[key] || key;
  };
  
  useEffect(() => {
    Promise.all([
      api.get('/major/my'),
      api.get('/users/all')  // Include offline users for invites
    ]).then(([major, users]) => {
      setMajorData(major.data);
      setAllUsers(users.data || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [api]);
  
  const createMajor = async () => {
    try {
      setCreating(true);
      if (createForm.logo_prompt) {
        toast.info(language === 'it' ? 'Generazione logo in corso...' : 'Generating logo...', { duration: 10000 });
      }
      const res = await api.post('/major/create', createForm);
      toast.success(language === 'it' ? 'Major creata con successo!' : 'Major created successfully!');
      setShowCreateModal(false);
      const major = await api.get('/major/my');
      setMajorData(major.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setCreating(false);
    }
  };
  
  const inviteUser = async (userId) => {
    try {
      await api.post('/major/invite', { user_id: userId });
      toast.success(language === 'it' ? 'Invito inviato!' : 'Invite sent!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
  };
  
  if (loading) return <div className="pt-16 p-4 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;
  
  return (
    <div className="pt-16 pb-6 px-3 max-w-4xl mx-auto">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4 flex items-center gap-2">
        <Crown className="w-8 h-8 text-purple-500" />
        {t('major')}
      </h1>
      
      {!majorData?.has_major ? (
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardContent className="p-6 text-center">
            <Crown className="w-16 h-16 mx-auto text-purple-500/50 mb-4" />
            <h2 className="text-xl font-semibold mb-2">{t('noMajor')}</h2>
            <p className="text-gray-400 mb-4">
              {language === 'it' 
                ? 'Crea la tua Major e unisci altri produttori!' 
                : 'Create your Major and unite other producers!'}
            </p>
            
            {/* Requirements */}
            <div className="flex justify-center gap-4 mb-4">
              <div className={`p-2 rounded-lg ${(majorData?.user_level || 0) >= (majorData?.required_level || 20) ? 'bg-green-500/20 border border-green-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Livello' : 'Level'}</p>
                <p className={`font-bold ${(majorData?.user_level || 0) >= (majorData?.required_level || 20) ? 'text-green-400' : 'text-red-400'}`}>
                  {majorData?.user_level || 0}/{majorData?.required_level || 20}
                </p>
              </div>
              <div className={`p-2 rounded-lg ${majorData?.user_funds >= (majorData?.creation_cost || 5000000) ? 'bg-green-500/20 border border-green-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Costo' : 'Cost'}</p>
                <p className={`font-bold ${majorData?.user_funds >= (majorData?.creation_cost || 5000000) ? 'text-green-400' : 'text-red-400'}`}>
                  ${((majorData?.creation_cost || 5000000) / 1000000).toFixed(0)}M
                </p>
              </div>
            </div>
            
            {majorData?.can_create ? (
              <Button className="bg-purple-600 hover:bg-purple-500" onClick={() => setShowCreateModal(true)}>
                <Plus className="w-4 h-4 mr-2" /> {t('createMajor')}
              </Button>
            ) : (
              <div className="space-y-2">
                <Badge className="bg-gray-500/20 text-gray-400">
                  {language === 'it' ? 'Requisiti non soddisfatti' : 'Requirements not met'}
                </Badge>
                <p className="text-xs text-gray-500">
                  {language === 'it' ? 'Fondi disponibili: ' : 'Available funds: '}
                  ${(majorData?.user_funds || 0).toLocaleString()}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Major Header */}
          <Card className="bg-gradient-to-r from-purple-900/30 to-purple-600/10 border-purple-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                {majorData.major?.logo_url ? (
                  <img src={majorData.major.logo_url} alt="" className="w-16 h-16 rounded-lg" />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Crown className="w-8 h-8 text-purple-500" />
                  </div>
                )}
                <div className="flex-1">
                  <h2 className="text-2xl font-bold">{majorData.major?.name}</h2>
                  <p className="text-sm text-gray-400">{majorData.major?.description}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="bg-purple-500/20 text-purple-400">Level {majorData.level}</Badge>
                    <Badge className="bg-white/10 text-gray-300">{majorData.members?.length}/{majorData.major?.max_members} {t('members')}</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Bonuses */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-500" />
                {t('bonuses')}
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded bg-green-500/10 text-center">
                <p className="text-2xl font-bold text-green-500">+{majorData.bonuses?.quality_bonus}%</p>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Qualità' : 'Quality'}</p>
              </div>
              <div className="p-3 rounded bg-yellow-500/10 text-center">
                <p className="text-2xl font-bold text-yellow-500">+{majorData.bonuses?.revenue_bonus}%</p>
                <p className="text-xs text-gray-400">{language === 'it' ? 'Incassi' : 'Revenue'}</p>
              </div>
              <div className="p-3 rounded bg-purple-500/10 text-center">
                <p className="text-2xl font-bold text-purple-500">+{majorData.bonuses?.xp_bonus}%</p>
                <p className="text-xs text-gray-400">XP</p>
              </div>
            </CardContent>
          </Card>
          
          {/* Weekly Challenge */}
          {majorData.weekly_challenge && (
            <Card className="bg-[#1A1A1A] border-yellow-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Target className="w-5 h-5 text-yellow-500" />
                  {t('weeklyChallenge')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <h3 className="font-semibold">{majorData.weekly_challenge.name?.[language] || majorData.weekly_challenge.name?.en || majorData.weekly_challenge.name}</h3>
                <p className="text-sm text-gray-400 mb-2">{majorData.weekly_challenge.description?.[language] || majorData.weekly_challenge.description?.en || majorData.weekly_challenge.description}</p>
                <div className="flex gap-2">
                  <Badge className="bg-yellow-500/20 text-yellow-400">+{majorData.weekly_challenge.rewards?.xp} XP</Badge>
                  <Badge className="bg-green-500/20 text-green-400">+${(majorData.weekly_challenge.rewards?.funds / 1000).toFixed(0)}K</Badge>
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Major Activities */}
          {majorData.activities && Object.keys(majorData.activities).length > 0 && (
            <Card className="bg-[#1A1A1A] border-purple-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Zap className="w-5 h-5 text-purple-500" />
                  {t('activities')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2">
                  {Object.entries(majorData.activities).map(([key, activity]) => (
                    <div key={key} className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm">{activity.name?.[language] || activity.name?.en}</h4>
                          <p className="text-xs text-gray-400 mt-1">{activity.description?.[language] || activity.description?.en}</p>
                        </div>
                        {activity.bonus && (
                          <div className="flex flex-col gap-1 ml-2">
                            {activity.bonus.quality && <Badge className="text-[10px] bg-blue-500/20 text-blue-400">+{activity.bonus.quality}% {language === 'it' ? 'Qualità' : 'Quality'}</Badge>}
                            {activity.bonus.revenue && <Badge className="text-[10px] bg-green-500/20 text-green-400">+{activity.bonus.revenue}% {language === 'it' ? 'Incassi' : 'Revenue'}</Badge>}
                            {activity.bonus.revenue_multiplier && <Badge className="text-[10px] bg-green-500/20 text-green-400">x{activity.bonus.revenue_multiplier} {language === 'it' ? 'Incassi' : 'Revenue'}</Badge>}
                            {activity.bonus.likes && <Badge className="text-[10px] bg-pink-500/20 text-pink-400">+{activity.bonus.likes} Likes</Badge>}
                          </div>
                        )}
                        {activity.discount_percent && (
                          <Badge className="text-[10px] bg-yellow-500/20 text-yellow-400">-{activity.discount_percent}%</Badge>
                        )}
                      </div>
                      {activity.cooldown_hours && (
                        <p className="text-[10px] text-gray-500 mt-2">
                          {language === 'it' ? 'Disponibile ogni' : 'Available every'} {activity.cooldown_hours < 24 ? `${activity.cooldown_hours}h` : `${Math.round(activity.cooldown_hours / 24)}d`}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Members */}
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center justify-between">
                <span className="flex items-center gap-2"><Users className="w-5 h-5" /> {t('members')}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {majorData.members?.map(member => (
                  <div key={member.user_id} className="flex items-center gap-3 p-2 rounded bg-white/5">
                    <Avatar className="w-10 h-10">
                      <AvatarImage src={member.avatar_url} />
                      <AvatarFallback className="bg-purple-500/20 text-purple-500">{member.nickname?.[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <p className="font-semibold text-sm"><ClickableNickname userId={member.user_id || member.id} nickname={member.nickname} /></p>
                      <Badge className={`text-[10px] h-4 ${member.role === 'founder' ? 'bg-yellow-500/20 text-yellow-400' : member.role === 'vice' ? 'bg-purple-500/20 text-purple-400' : 'bg-white/10 text-gray-400'}`}>
                        {MAJOR_ROLES[member.role]?.[language] || member.role}
                      </Badge>
                    </div>
                    <span className="text-xs text-gray-400">Lv.{member.level}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          
          {/* All Users - Invite Section */}
          {(majorData.my_role === 'founder' || majorData.my_role === 'vice') && (
            <Card className="bg-[#1A1A1A] border-white/10">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-400" />
                  {language === 'it' ? 'Invita Nuovi Membri' : 'Invite New Members'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Input 
                  placeholder={language === 'it' ? 'Cerca utente per nome...' : 'Search user by name...'} 
                  className="bg-black/30 border-white/10 mb-3"
                  value={inviteUserId}
                  onChange={(e) => setInviteUserId(e.target.value)}
                />
                
                {/* Tabs for Online/Offline */}
                <Tabs defaultValue="all" className="w-full">
                  <TabsList className="grid w-full grid-cols-3 bg-black/30">
                    <TabsTrigger value="all" className="text-xs">
                      {language === 'it' ? 'Tutti' : 'All'} ({allUsers.filter(u => !majorData.members?.some(m => m.user_id === u.id)).length})
                    </TabsTrigger>
                    <TabsTrigger value="online" className="text-xs">
                      <span className="w-2 h-2 rounded-full bg-green-500 mr-1"></span>
                      Online ({allUsers.filter(u => u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length})
                    </TabsTrigger>
                    <TabsTrigger value="offline" className="text-xs">
                      <span className="w-2 h-2 rounded-full bg-gray-500 mr-1"></span>
                      Offline ({allUsers.filter(u => !u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length})
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="all">
                    <ScrollArea className="h-60 mt-2">
                      <div className="space-y-1">
                        {allUsers
                          .filter(u => !majorData.members?.some(m => m.user_id === u.id))
                          .filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase()))
                          .map(u => (
                            <div key={u.id} className="flex items-center justify-between p-2 rounded bg-white/5 hover:bg-white/10 transition-colors">
                              <div className="flex items-center gap-3">
                                <span className={`w-2 h-2 rounded-full ${u.is_online ? 'bg-green-500' : 'bg-gray-500'}`}></span>
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={u.avatar_url} />
                                  <AvatarFallback className="bg-blue-500/20 text-blue-400 text-xs">{u.nickname?.[0]}</AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="text-sm font-medium">{u.nickname}</p>
                                  <p className="text-[10px] text-gray-500">{u.production_house_name} • Lv.{u.level || 0}</p>
                                </div>
                              </div>
                              <Button size="sm" variant="outline" className="border-purple-500/30 text-purple-400 h-8" onClick={() => inviteUser(u.id)}>
                                <Send className="w-3 h-3 mr-1" /> {t('invite')}
                              </Button>
                            </div>
                          ))}
                        {allUsers.filter(u => !majorData.members?.some(m => m.user_id === u.id)).filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase())).length === 0 && (
                          <p className="text-sm text-gray-500 text-center py-4">
                            {language === 'it' ? 'Nessun utente trovato' : 'No users found'}
                          </p>
                        )}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                  
                  <TabsContent value="online">
                    <ScrollArea className="h-60 mt-2">
                      <div className="space-y-1">
                        {allUsers
                          .filter(u => u.is_online && !majorData.members?.some(m => m.user_id === u.id))
                          .filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase()))
                          .map(u => (
                            <div key={u.id} className="flex items-center justify-between p-2 rounded bg-white/5 hover:bg-white/10 transition-colors">
                              <div className="flex items-center gap-3">
                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={u.avatar_url} />
                                  <AvatarFallback className="bg-green-500/20 text-green-400 text-xs">{u.nickname?.[0]}</AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="text-sm font-medium">{u.nickname}</p>
                                  <p className="text-[10px] text-gray-500">{u.production_house_name} • Lv.{u.level || 0}</p>
                                </div>
                              </div>
                              <Button size="sm" variant="outline" className="border-purple-500/30 text-purple-400 h-8" onClick={() => inviteUser(u.id)}>
                                <Send className="w-3 h-3 mr-1" /> {t('invite')}
                              </Button>
                            </div>
                          ))}
                        {allUsers.filter(u => u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length === 0 && (
                          <p className="text-sm text-gray-500 text-center py-4">
                            {language === 'it' ? 'Nessun utente online' : 'No users online'}
                          </p>
                        )}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                  
                  <TabsContent value="offline">
                    <ScrollArea className="h-60 mt-2">
                      <div className="space-y-1">
                        {allUsers
                          .filter(u => !u.is_online && !majorData.members?.some(m => m.user_id === u.id))
                          .filter(u => !inviteUserId || u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase()))
                          .map(u => (
                            <div key={u.id} className="flex items-center justify-between p-2 rounded bg-white/5 hover:bg-white/10 transition-colors">
                              <div className="flex items-center gap-3">
                                <span className="w-2 h-2 rounded-full bg-gray-500"></span>
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={u.avatar_url} />
                                  <AvatarFallback className="bg-gray-500/20 text-gray-400 text-xs">{u.nickname?.[0]}</AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="text-sm font-medium">{u.nickname}</p>
                                  <p className="text-[10px] text-gray-500">{u.production_house_name} • Lv.{u.level || 0}</p>
                                </div>
                              </div>
                              <Button size="sm" variant="outline" className="border-purple-500/30 text-purple-400 h-8" onClick={() => inviteUser(u.id)}>
                                <Send className="w-3 h-3 mr-1" /> {t('invite')}
                              </Button>
                            </div>
                          ))}
                        {allUsers.filter(u => !u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length === 0 && (
                          <p className="text-sm text-gray-500 text-center py-4">
                            {language === 'it' ? 'Nessun utente offline' : 'No users offline'}
                          </p>
                        )}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
        </div>
      )}
      
      {/* Create Major Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="bg-[#1A1A1A] border-white/10">
          <DialogHeader>
            <DialogTitle>{t('createMajor')}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{language === 'it' ? 'Nome' : 'Name'}</Label>
              <Input value={createForm.name} onChange={e => setCreateForm({...createForm, name: e.target.value})} placeholder="Major Studios" className="bg-black/30 border-white/10" />
            </div>
            <div>
              <Label>{language === 'it' ? 'Descrizione' : 'Description'}</Label>
              <Input value={createForm.description} onChange={e => setCreateForm({...createForm, description: e.target.value})} placeholder={language === 'it' ? 'La nostra missione...' : 'Our mission...'} className="bg-black/30 border-white/10" />
            </div>
            <div>
              <Label>{language === 'it' ? 'Max Membri' : 'Max Members'} ({createForm.max_members})</Label>
              <Slider value={[createForm.max_members]} onValueChange={([v]) => setCreateForm({...createForm, max_members: v})} min={5} max={50} step={5} />
            </div>
            <div>
              <Label className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                {language === 'it' ? 'Logo AI (opzionale)' : 'AI Logo (optional)'}
              </Label>
              <Input 
                value={createForm.logo_prompt} 
                onChange={e => setCreateForm({...createForm, logo_prompt: e.target.value})} 
                placeholder={language === 'it' ? 'Es: Leone dorato, stile classico Hollywood...' : 'E.g: Golden lion, classic Hollywood style...'} 
                className="bg-black/30 border-white/10" 
              />
              <p className="text-xs text-gray-500 mt-1">
                {language === 'it' 
                  ? 'Descrivi lo stile del logo che vuoi generare con AI' 
                  : 'Describe the logo style you want to generate with AI'}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
              <p className="text-sm text-purple-400 text-center">
                <DollarSign className="w-4 h-4 inline mr-1" />
                {language === 'it' ? 'Costo creazione: ' : 'Creation cost: '}
                <span className="font-bold">${(majorData?.creation_cost || 5000000).toLocaleString()}</span>
              </p>
            </div>
            <Button 
              className="w-full bg-purple-600 hover:bg-purple-500" 
              onClick={createMajor}
              disabled={creating || !createForm.name.trim()}
            >
              {creating ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> {language === 'it' ? 'Creazione in corso...' : 'Creating...'}</>
              ) : (
                t('createMajor')
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ==================== FRIENDS PAGE ====================

export default MajorPage;
