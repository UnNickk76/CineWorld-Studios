// CineWorld Studio's - LeaderboardPage
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

const LeaderboardPage = () => {
  const { api, user } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();
  const [globalLeaderboard, setGlobalLeaderboard] = useState([]);
  const [localLeaderboard, setLocalLeaderboard] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('global');

  useEffect(() => {
    api.get('/leaderboard/global?limit=50').then(r => {
      setGlobalLeaderboard(r.data.leaderboard);
      setLoading(false);
    });
  }, [api]);

  const loadLocalLeaderboard = async (country) => {
    setSelectedCountry(country);
    const res = await api.get(`/leaderboard/local/${country}?limit=50`);
    setLocalLeaderboard(res.data.leaderboard);
  };

  const getRankBadge = (rank) => {
    if (rank === 1) return <div className="w-6 h-6 rounded-full bg-yellow-500 flex items-center justify-center text-black font-bold text-xs">1</div>;
    if (rank === 2) return <div className="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center text-black font-bold text-xs">2</div>;
    if (rank === 3) return <div className="w-6 h-6 rounded-full bg-amber-600 flex items-center justify-center text-black font-bold text-xs">3</div>;
    return <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-gray-400 font-bold text-xs">{rank}</div>;
  };

  const PlayerRow = ({ player, showRank = true }) => (
    <div className="flex items-center gap-3 p-2 rounded hover:bg-white/5 cursor-pointer" onClick={() => navigate(`/player/${player.id}`)}>
      {showRank && getRankBadge(player.rank)}
      <Avatar className="w-8 h-8 border border-white/10">
        <AvatarImage src={player.avatar_url} />
        <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-xs">{player.nickname?.[0]}</AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1">
          <ClickableNickname userId={player.id} nickname={player.nickname} className="font-semibold text-sm" />
          <Badge className="bg-purple-500/20 text-purple-400 text-[10px] h-4">Lv.{player.level_info?.level || 0}</Badge>
        </div>
        <p className="text-[10px] text-gray-400 truncate">{player.production_house_name}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold text-yellow-500">{player.leaderboard_score?.toFixed(1)}</p>
        <p className="text-[10px] text-gray-400">Fame: {player.fame?.toFixed(0) || 50}</p>
      </div>
    </div>
  );

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="leaderboard-page">
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="font-['Bebas_Neue'] text-2xl flex items-center gap-2">
            <Trophy className="w-6 h-6 text-yellow-500" /> Classifica
          </CardTitle>
          <CardDescription>La classifica si basa sulla media di Livello, Fama e Ricavi</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-black/20 mb-4">
              <TabsTrigger value="global" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                <Globe className="w-4 h-4 mr-1" /> Globale
              </TabsTrigger>
              <TabsTrigger value="local" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                <MapPin className="w-4 h-4 mr-1" /> Locale
              </TabsTrigger>
            </TabsList>

            <TabsContent value="global">
              {loading ? (
                <div className="text-center py-8"><RefreshCw className="w-6 h-6 animate-spin mx-auto text-yellow-500" /></div>
              ) : (
                <ScrollArea className="h-[500px]">
                  <div className="space-y-1">
                    {globalLeaderboard.map(player => <PlayerRow key={player.id} player={player} />)}
                  </div>
                </ScrollArea>
              )}
            </TabsContent>

            <TabsContent value="local">
              <div className="mb-4">
                <Select value={selectedCountry} onValueChange={loadLocalLeaderboard}>
                  <SelectTrigger className="h-9 bg-black/20 border-white/10">
                    <SelectValue placeholder="Seleziona un paese" />
                  </SelectTrigger>
                  <SelectContent>
                    {['USA', 'Italy', 'Spain', 'France', 'Germany', 'UK', 'Japan', 'China', 'Brazil', 'India'].map(c => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {localLeaderboard.length > 0 ? (
                <ScrollArea className="h-[450px]">
                  <div className="space-y-1">
                    {localLeaderboard.map(player => <PlayerRow key={player.id} player={player} />)}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-center text-gray-400 py-8">Seleziona un paese per vedere la classifica locale</p>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

// Player Public Profile Page

export default LeaderboardPage;
