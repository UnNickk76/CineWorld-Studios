// CineWorld Studio's - MajorPage
// Extracted from App.js for modularity

import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, LanguageContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ScrollArea } from '../components/ui/scroll-area';
import { Slider } from '../components/ui/slider';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, Clapperboard, Send, Settings, Zap, Globe, Trophy, Shield, Swords, Home,
  Plus, Save, Building, Sparkles, Crown, Megaphone, AlertTriangle, CheckCircle,
  BarChart3, DollarSign, Target, Loader2, RefreshCw, Film, Star
} from 'lucide-react';
import { ClickableNickname } from '../components/shared';

const MAJOR_ROLES = {
  founder: { it: 'Fondatore', en: 'Founder' },
  vice: { it: 'Vice', en: 'Vice' },
  member: { it: 'Membro', en: 'Member' },
  manager: { it: 'Manager', en: 'Manager' }
};

const STUDIO_LEVELS = [
  { value: 'studio', label_it: 'Studio Indipendente', label_en: 'Independent Studio', color: 'text-gray-400', bg: 'bg-gray-500/20' },
  { value: 'mini_major', label_it: 'Mini Major', label_en: 'Mini Major', color: 'text-blue-400', bg: 'bg-blue-500/20' },
  { value: 'major', label_it: 'Major', label_en: 'Major', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
];

const SECTIONS = [
  { id: 'panoramica', icon: Home, it: 'Panoramica', en: 'Overview' },
  { id: 'attivita', icon: Zap, it: 'Attività', en: 'Activities' },
  { id: 'membri', icon: Users, it: 'Membri', en: 'Members' },
  { id: 'gestione', icon: Settings, it: 'Gestione', en: 'Management' },
  { id: 'guerra', icon: Swords, it: 'Guerra', en: 'War' },
];

const WAR_DURATIONS_H = { short: 24, medium: 48, long: 72 };

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
  const [bonusForm, setBonusForm] = useState({ marketing: 0, casting: 0, production: 0 });
  const [triggeringEvent, setTriggeringEvent] = useState(false);
  const [settingLevel, setSettingLevel] = useState(false);
  const [allMajors, setAllMajors] = useState([]);
  const [warHistory, setWarHistory] = useState([]);
  const [selectedOpponent, setSelectedOpponent] = useState('');
  const [calculatingWar, setCalculatingWar] = useState(false);
  const [lastWarResult, setLastWarResult] = useState(null);
  const [activeSection, setActiveSection] = useState('panoramica');
  
  // Timed War state
  const [activeWar, setActiveWar] = useState(null);
  const [warDuration, setWarDuration] = useState('medium');
  const [declaringWar, setDeclaringWar] = useState(false);
  const [striking, setStriking] = useState(false);
  const [strikeResult, setStrikeResult] = useState(null);

  // Section refs removed — using tab-based rendering

  const t = (key) => {
    const translations = {
      major: language === 'it' ? 'Major' : 'Major',
      createMajor: language === 'it' ? 'Crea Major' : 'Create Major',
      yourMajor: language === 'it' ? 'La Tua Major' : 'Your Major',
      noMajor: language === 'it' ? 'Non sei in una Major' : "You're not in a Major",
      members: language === 'it' ? 'Membri' : 'Members',
      invite: language === 'it' ? 'Invita' : 'Invite',
      weeklyChallenge: language === 'it' ? 'Sfida Settimanale' : 'Weekly Challenge',
      bonuses: language === 'it' ? 'Bonus' : 'Bonuses',
      activities: language === 'it' ? 'Attività' : 'Activities',
    };
    return translations[key] || key;
  };

  // Data loading
  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [major, users] = await Promise.all([
          api.get('/major/my'),
          api.get('/users/all')
        ]);
        if (!mounted) return;
        setMajorData(major.data);
        setAllUsers(users.data || []);
        const mb = major.data?.major?.major_bonuses;
        if (mb) setBonusForm({ marketing: mb.marketing || 0, casting: mb.casting || 0, production: mb.production || 0 });
      } catch (err) {
        console.error('Major load error:', err);
      }
      if (mounted) setLoading(false);
    };
    load();
    return () => { mounted = false; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!majorData?.has_major) return;
    const loadWar = async () => {
      try {
        const [majorsRes, warsRes] = await Promise.all([
          api.get('/major/all').catch(() => ({ data: { majors: [] } })),
          api.get('/major/wars').catch(() => ({ data: { wars: [] } }))
        ]);
        setAllMajors(majorsRes.data?.majors || []);
        setWarHistory(warsRes.data?.wars || []);
      } catch (err) {
        console.error('War data error:', err);
      }
    };
    loadWar();
  }, [majorData?.has_major]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load active war
  useEffect(() => {
    if (!majorData?.has_major) return;
    api.get('/major/war/active').then(r => setActiveWar(r.data)).catch(() => {});
  }, [majorData?.has_major]); // eslint-disable-line react-hooks/exhaustive-deps

  // Tab-based navigation — no scroll spy

  const reloadMajorData = async () => {
    try {
      const res = await api.get('/major/my');
      setMajorData(res.data);
      const mb = res.data?.major?.major_bonuses;
      if (mb) setBonusForm({ marketing: mb.marketing || 0, casting: mb.casting || 0, production: mb.production || 0 });
    } catch (err) {
      console.error('Major reload error:', err);
    }
  };

  const createMajor = async () => {
    try {
      setCreating(true);
      if (createForm.logo_prompt) toast.info(language === 'it' ? 'Generazione logo in corso...' : 'Generating logo...', { duration: 10000 });
      await api.post('/major/create', createForm);
      toast.success(language === 'it' ? 'Major creata con successo!' : 'Major created successfully!');
      setShowCreateModal(false);
      const major = await api.get('/major/my');
      setMajorData(major.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nella creazione');
    } finally { setCreating(false); }
  };

  const inviteUser = async (userId) => {
    try {
      await api.post('/major/invite', { user_id: userId });
      toast.success(language === 'it' ? 'Invito inviato!' : 'Invite sent!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const setStudioLevel = async (newLevel) => {
    if (!majorData?.major?.id) return;
    try {
      setSettingLevel(true);
      await api.post('/major/set-level', { major_id: majorData.major.id, new_level: newLevel });
      toast.success(language === 'it' ? 'Livello aggiornato!' : 'Level updated!');
      await reloadMajorData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setSettingLevel(false); }
  };

  const setMemberRole = async (userId, role) => {
    try {
      await api.post('/major/set-role', { user_id: userId, role });
      toast.success(language === 'it' ? 'Ruolo aggiornato!' : 'Role updated!');
      await reloadMajorData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const saveBonuses = async () => {
    try {
      await api.post('/major/set-bonuses', bonusForm);
      toast.success(language === 'it' ? 'Bonus salvati!' : 'Bonuses saved!');
      await reloadMajorData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const triggerEvent = async () => {
    try {
      setTriggeringEvent(true);
      const res = await api.post('/major/trigger-event');
      const ev = res.data?.event;
      const evName = language === 'it' ? ev?.name_it : ev?.name_en;
      toast.success(`${ev?.positive ? '' : ''} ${evName}`);
      await reloadMajorData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setTriggeringEvent(false); }
  };

  const calculateWar = async () => {
    if (!selectedOpponent) return;
    try {
      setCalculatingWar(true);
      const res = await api.post('/major/war/calculate', { opponent_major_id: selectedOpponent });
      setLastWarResult(res.data?.war);
      toast.success(language === 'it' ? 'Guerra calcolata!' : 'War calculated!');
      const warsRes = await api.get('/major/wars').catch(() => ({ data: { wars: [] } }));
      setWarHistory(warsRes.data?.wars || []);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setCalculatingWar(false); }
  };

  const declareTimedWar = async () => {
    if (!selectedOpponent) return;
    try {
      setDeclaringWar(true);
      const res = await api.post('/major/war/declare', { opponent_major_id: selectedOpponent, duration: warDuration });
      setActiveWar({ has_war: true, war: res.data.war, is_major_a: true, my_score: 0, enemy_score: 0, my_strikes: 0, my_role: 'founder', time_remaining_seconds: WAR_DURATIONS_H[warDuration] * 3600 });
      toast.success('Guerra dichiarata!');
      refreshUser();
      const warsRes = await api.get('/major/wars').catch(() => ({ data: { wars: [] } }));
      setWarHistory(warsRes.data?.wars || []);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setDeclaringWar(false); }
  };

  const executeWarStrike = async (targetType) => {
    if (!activeWar?.war?.id) return;
    try {
      setStriking(true);
      const res = await api.post('/major/war/strike', { war_id: activeWar.war.id, target_type: targetType });
      setStrikeResult(res.data);
      toast.success(res.data.message);
      refreshUser();
      api.get('/major/war/active').then(r => setActiveWar(r.data)).catch(() => {});
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setStriking(false); }
  };

  if (loading) return <div className="pt-16 p-4 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto text-yellow-500" /></div>;

  // Sections visible depends on role
  const isFounder = majorData?.my_role === 'founder';
  const visibleSections = majorData?.has_major
    ? SECTIONS.filter(s => s.id !== 'gestione' || isFounder)
    : [];

  return (
    <div className="pt-16 pb-24 max-w-4xl mx-auto" data-testid="major-page">
      {/* Page Header */}
      <div className="px-3 mb-2">
        <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
          <Crown className="w-8 h-8 text-purple-500" />
          {t('major')}
        </h1>
      </div>

      {!majorData?.has_major ? (
        <NoMajorView majorData={majorData} language={language} t={t} onCreateClick={() => setShowCreateModal(true)} />
      ) : (
        <>
          {/* Sticky Internal Navbar */}
          <nav
            className="sticky top-[52px] z-30 bg-[#0a0a0a]/95 backdrop-blur-sm border-b border-white/5 mb-3"
            data-testid="major-section-nav"
          >
            <div className="flex overflow-x-auto no-scrollbar px-2 gap-1" style={{ WebkitOverflowScrolling: 'touch' }}>
              {visibleSections.map((sec) => {
                const Icon = sec.icon;
                const isActive = activeSection === sec.id;
                return (
                  <button
                    key={sec.id}
                    onClick={() => setActiveSection(sec.id)}
                    className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium whitespace-nowrap border-b-2 transition-colors shrink-0 ${
                      isActive
                        ? 'border-purple-500 text-purple-400'
                        : 'border-transparent text-gray-500 hover:text-gray-300'
                    }`}
                    data-testid={`major-tab-${sec.id}`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {sec[language] || sec.en}
                  </button>
                );
              })}
            </div>
          </nav>

          <div className="px-3 space-y-4">
            {/* ===== PANORAMICA ===== */}
            {activeSection === 'panoramica' && (
            <section id="panoramica">
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
                        <Badge className="bg-purple-500/20 text-purple-400">{language === 'it' ? 'Livello' : 'Level'} {majorData.level}</Badge>
                        <Badge className="bg-white/10 text-gray-300">{majorData.members?.length}/{majorData.major?.max_members} {t('members')}</Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Bonuses */}
              <Card className="bg-[#1A1A1A] border-white/10 mt-3">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-yellow-500" /> {t('bonuses')}
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
                <Card className="bg-[#1A1A1A] border-yellow-500/30 mt-3">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Target className="w-5 h-5 text-yellow-500" /> {t('weeklyChallenge')}
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
            </section>
            )}

            {/* ===== ATTIVITA ===== */}
            {activeSection === 'attivita' && (
            <section id="attivita">
              {majorData.activities && Object.keys(majorData.activities).length > 0 && (
                <Card className="bg-[#1A1A1A] border-purple-500/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Zap className="w-5 h-5 text-purple-500" /> {t('activities')}
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
            </section>
            )}

            {/* ===== MEMBRI ===== */}
            {activeSection === 'membri' && (
            <section id="membri">
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

              {/* Invite Section (Founder/Vice) */}
              {(majorData.my_role === 'founder' || majorData.my_role === 'vice') && (
                <Card className="bg-[#1A1A1A] border-white/10 mt-3">
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
                    <Tabs defaultValue="all" className="w-full">
                      <TabsList className="grid w-full grid-cols-3 bg-black/30">
                        <TabsTrigger value="all" className="text-xs">
                          {language === 'it' ? 'Tutti' : 'All'} ({allUsers.filter(u => !majorData.members?.some(m => m.user_id === u.id)).length})
                        </TabsTrigger>
                        <TabsTrigger value="online" className="text-xs">
                          <span className="w-2 h-2 rounded-full bg-green-500 mr-1" />
                          Online ({allUsers.filter(u => u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length})
                        </TabsTrigger>
                        <TabsTrigger value="offline" className="text-xs">
                          <span className="w-2 h-2 rounded-full bg-gray-500 mr-1" />
                          Offline ({allUsers.filter(u => !u.is_online && !majorData.members?.some(m => m.user_id === u.id)).length})
                        </TabsTrigger>
                      </TabsList>
                      {['all', 'online', 'offline'].map(tabVal => (
                        <TabsContent key={tabVal} value={tabVal}>
                          <ScrollArea className="h-60 mt-2">
                            <div className="space-y-1">
                              {allUsers
                                .filter(u => {
                                  if (majorData.members?.some(m => m.user_id === u.id)) return false;
                                  if (inviteUserId && !u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase())) return false;
                                  if (tabVal === 'online') return u.is_online;
                                  if (tabVal === 'offline') return !u.is_online;
                                  return true;
                                })
                                .map(u => (
                                  <div key={u.id} className="flex items-center justify-between p-2 rounded bg-white/5 hover:bg-white/10 transition-colors">
                                    <div className="flex items-center gap-3">
                                      <span className={`w-2 h-2 rounded-full ${u.is_online ? 'bg-green-500' : 'bg-gray-500'}`} />
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
                              {allUsers.filter(u => {
                                if (majorData.members?.some(m => m.user_id === u.id)) return false;
                                if (inviteUserId && !u.nickname?.toLowerCase().includes(inviteUserId.toLowerCase())) return false;
                                if (tabVal === 'online') return u.is_online;
                                if (tabVal === 'offline') return !u.is_online;
                                return true;
                              }).length === 0 && (
                                <p className="text-sm text-gray-500 text-center py-4">
                                  {language === 'it' ? 'Nessun utente trovato' : 'No users found'}
                                </p>
                              )}
                            </div>
                          </ScrollArea>
                        </TabsContent>
                      ))}
                    </Tabs>
                  </CardContent>
                </Card>
              )}
            </section>
            )}

            {/* ===== GESTIONE (Founder Only) ===== */}
            {activeSection === 'gestione' && isFounder && (
              <section id="gestione">
                {/* Studio Level */}
                <Card className="bg-[#1A1A1A] border-yellow-500/20" data-testid="admin-studio-level">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Building className="w-4 h-4 text-yellow-500" />
                      {language === 'it' ? 'Livello Studio' : 'Studio Level'}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {language === 'it' ? 'Imposta il livello della tua Major' : 'Set your Major level'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-2 flex-wrap">
                      {STUDIO_LEVELS.map(sl => {
                        const isCurrent = (majorData.major?.studio_level || 'studio') === sl.value;
                        return (
                          <Button
                            key={sl.value} size="sm"
                            variant={isCurrent ? 'default' : 'outline'}
                            className={isCurrent ? `${sl.bg} ${sl.color} border ${sl.color.replace('text-', 'border-')}/30` : 'border-white/10 text-gray-400'}
                            disabled={settingLevel || isCurrent}
                            onClick={() => setStudioLevel(sl.value)}
                            data-testid={`studio-level-${sl.value}`}
                          >
                            {settingLevel ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                            {language === 'it' ? sl.label_it : sl.label_en}
                          </Button>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Roles */}
                <Card className="bg-[#1A1A1A] border-yellow-500/20 mt-3" data-testid="admin-roles">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Shield className="w-4 h-4 text-yellow-500" />
                      {language === 'it' ? 'Ruoli Membri' : 'Member Roles'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {majorData.members?.filter(m => m.role !== 'founder').map(member => (
                        <div key={member.user_id} className="flex items-center gap-3 p-2 rounded bg-white/5">
                          <Avatar className="w-8 h-8">
                            <AvatarImage src={member.avatar_url} />
                            <AvatarFallback className="bg-purple-500/20 text-purple-400 text-xs">{member.nickname?.[0]}</AvatarFallback>
                          </Avatar>
                          <span className="flex-1 text-sm font-medium truncate">{member.nickname}</span>
                          <Select defaultValue={member.role} onValueChange={(val) => setMemberRole(member.user_id, val)}>
                            <SelectTrigger className="w-[120px] h-8 text-xs bg-black/30 border-white/10" data-testid={`role-select-${member.user_id}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-[#1A1A1A] border-white/10">
                              <SelectItem value="manager">Manager</SelectItem>
                              <SelectItem value="member">{language === 'it' ? 'Membro' : 'Member'}</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      ))}
                      {majorData.members?.filter(m => m.role !== 'founder').length === 0 && (
                        <p className="text-xs text-gray-500 text-center py-2">
                          {language === 'it' ? 'Nessun membro da gestire' : 'No members to manage'}
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Department Bonuses */}
                <Card className="bg-[#1A1A1A] border-yellow-500/20 mt-3" data-testid="admin-bonuses">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-yellow-500" />
                      {language === 'it' ? 'Bonus Reparti' : 'Department Bonuses'}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {language === 'it' ? 'Distribuisci bonus ai reparti (0-25)' : 'Distribute bonuses to departments (0-25)'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {[
                      { key: 'marketing', icon: <Megaphone className="w-4 h-4 text-cyan-400" />, color: 'cyan' },
                      { key: 'casting', icon: <Users className="w-4 h-4 text-pink-400" />, color: 'pink' },
                      { key: 'production', icon: <Clapperboard className="w-4 h-4 text-green-400" />, color: 'green' }
                    ].map(dep => (
                      <div key={dep.key} className="flex items-center gap-3">
                        {dep.icon}
                        <span className="text-sm capitalize w-20">{dep.key}</span>
                        <Slider
                          value={[bonusForm[dep.key]]}
                          onValueChange={([v]) => setBonusForm(prev => ({ ...prev, [dep.key]: v }))}
                          min={0} max={25} step={1}
                          className="flex-1"
                        />
                        <Badge className={`bg-${dep.color}-500/20 text-${dep.color}-400 w-10 justify-center`}>
                          +{bonusForm[dep.key]}
                        </Badge>
                      </div>
                    ))}
                    <Button size="sm" className="w-full bg-yellow-600 hover:bg-yellow-500 text-black font-semibold mt-2" onClick={saveBonuses} data-testid="save-bonuses-btn">
                      <Save className="w-3 h-3 mr-1" /> {language === 'it' ? 'Salva Bonus' : 'Save Bonuses'}
                    </Button>
                  </CardContent>
                </Card>

                {/* Trigger Event */}
                <Card className="bg-[#1A1A1A] border-yellow-500/20 mt-3" data-testid="admin-events">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Zap className="w-4 h-4 text-yellow-500" />
                      {language === 'it' ? 'Evento Major' : 'Major Event'}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {language === 'it' ? 'Attiva un evento casuale (cooldown 6h)' : 'Trigger a random event (6h cooldown)'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {majorData.major?.active_event && (
                      <div className={`p-3 rounded-lg mb-3 border ${majorData.major.active_event.positive ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                        <div className="flex items-center gap-2 mb-1">
                          {majorData.major.active_event.positive ? <CheckCircle className="w-4 h-4 text-green-400" /> : <AlertTriangle className="w-4 h-4 text-red-400" />}
                          <span className="font-semibold text-sm">
                            {language === 'it' ? majorData.major.active_event.name_it : majorData.major.active_event.name_en}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400">
                          {language === 'it' ? majorData.major.active_event.desc_it : majorData.major.active_event.desc_en}
                        </p>
                        <div className="flex gap-1 mt-2">
                          {Object.entries(majorData.major.active_event.effect || {}).map(([k, v]) => (
                            <Badge key={k} className={`text-[10px] ${v > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                              {k}: {v > 0 ? '+' : ''}{v}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    <Button size="sm" className="w-full bg-purple-600 hover:bg-purple-500" disabled={triggeringEvent} onClick={triggerEvent} data-testid="trigger-event-btn">
                      {triggeringEvent ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Zap className="w-3 h-3 mr-1" />}
                      {language === 'it' ? 'Attiva Evento' : 'Trigger Event'}
                    </Button>
                  </CardContent>
                </Card>
              </section>
            )}

            {/* ===== GUERRA ===== */}
            {activeSection === 'guerra' && (
            <section id="guerra">
              {/* Active Timed War */}
              {activeWar?.has_war && activeWar.war?.status === 'active' && (
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
                  <Card className="bg-gradient-to-br from-red-950/30 to-orange-950/20 border-red-500/30" data-testid="active-war-panel">
                    <CardContent className="p-4">
                      {/* War Header */}
                      <div className="text-center mb-3">
                        <div className="flex items-center justify-center gap-2 mb-1">
                          <Swords className="w-5 h-5 text-red-400 animate-pulse"/>
                          <span className="text-xs font-bold text-red-400 uppercase tracking-widest">Guerra in Corso</span>
                        </div>
                        <div className="flex items-center justify-center gap-3 text-sm">
                          <span className={`font-bold ${activeWar.is_major_a ? 'text-yellow-400' : 'text-white'}`}>{activeWar.war.major_a_name}</span>
                          <span className="text-gray-500">vs</span>
                          <span className={`font-bold ${!activeWar.is_major_a ? 'text-yellow-400' : 'text-white'}`}>{activeWar.war.major_b_name}</span>
                        </div>
                      </div>

                      {/* Score */}
                      <div className="grid grid-cols-3 gap-2 mb-3">
                        <div className="p-2 bg-yellow-500/10 rounded border border-yellow-500/15 text-center">
                          <p className="text-[10px] text-gray-400">Il Tuo Punteggio</p>
                          <p className="text-xl font-bold text-yellow-400">{activeWar.my_score || 0}</p>
                        </div>
                        <div className="p-2 bg-white/5 rounded border border-white/10 text-center">
                          <p className="text-[10px] text-gray-400">Tempo</p>
                          <p className="text-sm font-bold text-white">{activeWar.time_remaining_seconds > 0 ? `${Math.floor(activeWar.time_remaining_seconds / 3600)}h ${Math.floor((activeWar.time_remaining_seconds % 3600) / 60)}m` : 'Terminata'}</p>
                        </div>
                        <div className="p-2 bg-red-500/10 rounded border border-red-500/15 text-center">
                          <p className="text-[10px] text-gray-400">Nemico</p>
                          <p className="text-xl font-bold text-red-400">{activeWar.enemy_score || 0}</p>
                        </div>
                      </div>

                      {/* Strike Buttons */}
                      {(activeWar.my_role === 'founder' || activeWar.my_role === 'manager') && activeWar.time_remaining_seconds > 0 && (
                        <>
                          <p className="text-[10px] text-gray-400 text-center mb-2">Colpi (3 CP | Cooldown 2h)</p>
                          <div className="grid grid-cols-3 gap-2">
                            {[
                              { type: 'infra', label: 'Infrastrutture', icon: Building, color: 'from-orange-600 to-red-600' },
                              { type: 'film', label: 'Film', icon: Film, color: 'from-purple-600 to-pink-600' },
                              { type: 'fame', label: 'Fama', icon: Star, color: 'from-cyan-600 to-blue-600' },
                            ].map(s => (
                              <Button key={s.type} size="sm" disabled={striking}
                                onClick={() => executeWarStrike(s.type)}
                                className={`h-10 text-[10px] font-bold bg-gradient-to-r ${s.color} hover:opacity-90`}
                                data-testid={`war-strike-${s.type}`}>
                                <s.icon className="w-3 h-3 mr-1"/>{s.label}
                              </Button>
                            ))}
                          </div>
                        </>
                      )}

                      {/* Strike Result */}
                      <AnimatePresence>
                        {strikeResult && (
                          <motion.div initial={{opacity:0,y:5}} animate={{opacity:1,y:0}} exit={{opacity:0}} className="mt-2 p-2 bg-green-500/10 rounded border border-green-500/15 text-center">
                            <p className="text-xs text-green-400 font-semibold">+{strikeResult.score_gain} punti!</p>
                            <p className="text-[10px] text-gray-400">{strikeResult.description}</p>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* War Events Log */}
                      {activeWar.war.events?.length > 0 && (
                        <div className="mt-3 space-y-1 max-h-32 overflow-y-auto">
                          <p className="text-[10px] text-gray-500 uppercase font-bold">Cronologia Guerra</p>
                          {activeWar.war.events.slice(-6).reverse().map((ev, i) => (
                            <div key={i} className="flex items-center gap-2 p-1.5 bg-white/[0.03] rounded text-[10px]">
                              <Swords className="w-3 h-3 text-red-400 flex-shrink-0"/>
                              <span className="text-gray-400 flex-1 truncate"><span className="text-white font-semibold">{ev.striker}</span> ({ev.major}) - {ev.desc}</span>
                              <span className="text-yellow-400 font-bold flex-shrink-0">+{ev.score}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* Completed War Result */}
              {activeWar?.war?.status === 'completed' && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                  <Card className={`border ${activeWar.war.winner === majorData.major?.id ? 'bg-green-900/20 border-green-500/40' : 'bg-red-900/20 border-red-500/40'}`}>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold mb-1">
                        {activeWar.war.winner === majorData.major?.id ? 'VITTORIA!' : 'SCONFITTA'}
                      </div>
                      <div className="flex items-center justify-center gap-4 text-sm">
                        <span className="font-semibold">{activeWar.war.major_a_name}</span>
                        <span className="text-yellow-400 font-mono">{activeWar.war.score_a}</span>
                        <span className="text-gray-500">vs</span>
                        <span className="text-yellow-400 font-mono">{activeWar.war.score_b}</span>
                        <span className="font-semibold">{activeWar.war.major_b_name}</span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* Last Quick War Result */}
              {lastWarResult && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                  <Card className={`border mt-2 ${lastWarResult.winner === majorData.major?.id ? 'bg-green-900/20 border-green-500/40' : 'bg-red-900/20 border-red-500/40'}`}>
                    <CardContent className="p-4 text-center">
                      <div className="text-lg font-bold mb-1">
                        {lastWarResult.winner === majorData.major?.id ? 'VITTORIA!' : 'SCONFITTA'}
                      </div>
                      <div className="flex items-center justify-center gap-4 text-sm">
                        <span className="font-semibold">{lastWarResult.major_a_name}</span>
                        <span className="text-yellow-400 font-mono">{lastWarResult.score_a}</span>
                        <span className="text-gray-500">vs</span>
                        <span className="text-yellow-400 font-mono">{lastWarResult.score_b}</span>
                        <span className="font-semibold">{lastWarResult.major_b_name}</span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* War Declare (Founder only) */}
              {isFounder && !activeWar?.has_war && (
                <Card className="bg-[#1A1A1A] border-red-500/20 mt-3" data-testid="war-declare">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Swords className="w-4 h-4 text-red-500" />
                      Dichiara Guerra
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Scegli tipo e avversario. Costo: $1M
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {/* Duration selector */}
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { id: 'short', label: '24h', desc: 'Blitz' },
                        { id: 'medium', label: '48h', desc: 'Standard' },
                        { id: 'long', label: '72h', desc: 'Epica' },
                      ].map(d => (
                        <button key={d.id} onClick={() => setWarDuration(d.id)}
                          className={`p-2 rounded-lg text-center border transition-all ${warDuration === d.id ? 'bg-red-500/15 border-red-500/25 text-red-400' : 'bg-white/5 border-white/8 text-gray-500'}`}
                          data-testid={`war-duration-${d.id}`}>
                          <p className="text-sm font-bold">{d.label}</p>
                          <p className="text-[9px]">{d.desc}</p>
                        </button>
                      ))}
                    </div>

                    <div className="flex gap-2">
                      <Select value={selectedOpponent} onValueChange={setSelectedOpponent}>
                        <SelectTrigger className="flex-1 h-9 text-sm bg-black/30 border-white/10" data-testid="war-opponent-select">
                          <SelectValue placeholder="Seleziona avversario..." />
                        </SelectTrigger>
                        <SelectContent className="bg-[#1A1A1A] border-white/10">
                          {allMajors.map(m => (
                            <SelectItem key={m.id} value={m.id}>{m.name} {m.studio_level ? `(${m.studio_level})` : ''}</SelectItem>
                          ))}
                          {allMajors.length === 0 && (
                            <div className="p-2 text-xs text-gray-500 text-center">Nessuna Major avversaria</div>
                          )}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <Button size="sm" className="bg-red-600 hover:bg-red-500" disabled={declaringWar || !selectedOpponent} onClick={declareTimedWar} data-testid="declare-timed-war-btn">
                        {declaringWar ? <Loader2 className="w-3 h-3 animate-spin mr-1"/> : <Swords className="w-3 h-3 mr-1"/>}
                        Guerra {WAR_DURATIONS_H[warDuration]}h
                      </Button>
                      <Button size="sm" variant="outline" className="border-gray-600 text-gray-400" disabled={calculatingWar || !selectedOpponent} onClick={calculateWar} data-testid="calculate-war-btn">
                        {calculatingWar ? <Loader2 className="w-3 h-3 animate-spin mr-1"/> : <BarChart3 className="w-3 h-3 mr-1"/>}
                        Rapida
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* War History */}
              {warHistory.length > 0 && (
                <Card className="bg-[#1A1A1A] border-white/10 mt-3" data-testid="war-history">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-gray-400" />
                      Storico Guerre
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {warHistory.slice(0, 5).map(war => {
                        const won = war.winner === majorData.major?.id;
                        const isActive = war.status === 'active';
                        return (
                          <div key={war.id} className={`flex items-center gap-2 p-2 rounded text-xs ${isActive ? 'bg-red-500/10 border border-red-500/20 animate-pulse' : won ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                            <Badge className={`text-[10px] ${isActive ? 'bg-red-500/20 text-red-400' : won ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                              {isActive ? 'LIVE' : won ? 'W' : 'L'}
                            </Badge>
                            <span className="flex-1 truncate">
                              {war.major_a_name} <span className="text-yellow-400">{war.score_a}</span>
                              {' vs '}
                              <span className="text-yellow-400">{war.score_b}</span> {war.major_b_name}
                            </span>
                            <span className="text-gray-500 text-[10px]">
                              {war.duration_hours ? `${war.duration_hours}h` : ''} {war.created_at ? new Date(war.created_at).toLocaleDateString() : ''}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}
            </section>
            )}
          </div>
        </>
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
                {language === 'it' ? 'Descrivi lo stile del logo che vuoi generare con AI' : 'Describe the logo style you want to generate with AI'}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
              <p className="text-sm text-purple-400 text-center">
                <DollarSign className="w-4 h-4 inline mr-1" />
                {language === 'it' ? 'Costo creazione: ' : 'Creation cost: '}
                <span className="font-bold">${(majorData?.creation_cost || 5000000).toLocaleString()}</span>
              </p>
            </div>
            <Button className="w-full bg-purple-600 hover:bg-purple-500" onClick={createMajor} disabled={creating || !createForm.name.trim()}>
              {creating ? <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> {language === 'it' ? 'Creazione in corso...' : 'Creating...'}</> : t('createMajor')}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Extracted "No Major" view
function NoMajorView({ majorData, language, t, onCreateClick }) {
  return (
    <div className="px-3">
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-6 text-center">
          <Crown className="w-16 h-16 mx-auto text-purple-500/50 mb-4" />
          <h2 className="text-xl font-semibold mb-2">{t('noMajor')}</h2>
          <p className="text-gray-400 mb-4">
            {language === 'it' ? 'Crea la tua Major e unisci altri produttori!' : 'Create your Major and unite other producers!'}
          </p>
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
            <Button className="bg-purple-600 hover:bg-purple-500" onClick={onCreateClick}>
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
    </div>
  );
}

export default MajorPage;
