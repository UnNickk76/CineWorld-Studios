// CineWorld Studio's - DownloadAppPage
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
  Handshake, UserPlus, UserMinus, UserCheck, Users2, PersonStanding,
  Link2
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';

// useTranslations imported from contexts

const DownloadAppPage = () => {
  const { language } = useContext(LanguageContext);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isAndroid, setIsAndroid] = useState(false);
  
  useEffect(() => {
    // Detect platform
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    setIsIOS(/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream);
    setIsAndroid(/android/i.test(userAgent));
    
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
    }
    
    // Listen for install prompt (Android/Desktop)
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    });
    
    // Listen for successful install
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setDeferredPrompt(null);
    });
  }, []);
  
  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setIsInstalled(true);
    }
    setDeferredPrompt(null);
  };
  
  const appUrl = window.location.origin;
  
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-4 pt-20">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <img src="/icons/icon-192x192.png" alt="CineWorld" className="w-24 h-24 mx-auto rounded-2xl shadow-lg mb-4" />
          <h1 className="text-3xl font-['Bebas_Neue'] text-yellow-500">CineWorld Studio's</h1>
          <Badge className="bg-purple-500/20 text-purple-400 mt-2">BETA TEST</Badge>
          <p className="text-gray-400 mt-2">
            {language === 'it' 
              ? 'Gioco multiplayer di produzione cinematografica'
              : 'Multiplayer movie production game'}
          </p>
        </div>
        
        {isInstalled ? (
          <Card className="bg-green-500/10 border-green-500/30 mb-6">
            <CardContent className="p-6 text-center">
              <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
              <h2 className="text-xl font-semibold text-green-400">
                {language === 'it' ? 'App Installata!' : 'App Installed!'}
              </h2>
              <p className="text-gray-400 mt-2">
                {language === 'it' 
                  ? 'Puoi trovare CineWorld nella tua home screen.'
                  : 'You can find CineWorld on your home screen.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Android / Desktop Install */}
            {(isAndroid || deferredPrompt) && (
              <Card className="bg-[#1A1A1A] border-green-500/30 mb-6">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Smartphone className="w-8 h-8 text-green-500" />
                    <div>
                      <h2 className="font-semibold">
                        {isAndroid ? 'Android' : 'Desktop'}
                      </h2>
                      <p className="text-xs text-gray-400">
                        {language === 'it' ? 'Installazione diretta' : 'Direct installation'}
                      </p>
                    </div>
                  </div>
                  <Button 
                    onClick={handleInstall}
                    className="w-full bg-green-600 hover:bg-green-500"
                    disabled={!deferredPrompt}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    {language === 'it' ? 'Installa App' : 'Install App'}
                  </Button>
                </CardContent>
              </Card>
            )}
            
            {/* iOS Instructions */}
            {isIOS && (
              <Card className="bg-[#1A1A1A] border-blue-500/30 mb-6">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Smartphone className="w-8 h-8 text-blue-500" />
                    <div>
                      <h2 className="font-semibold">iPhone / iPad</h2>
                      <p className="text-xs text-gray-400">
                        {language === 'it' ? 'Installazione manuale' : 'Manual installation'}
                      </p>
                    </div>
                  </div>
                  <div className="space-y-4 text-sm">
                    <div className="flex items-start gap-3 p-3 rounded bg-black/30">
                      <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold shrink-0">1</span>
                      <div>
                        <p className="font-medium">{language === 'it' ? 'Apri Safari' : 'Open Safari'}</p>
                        <p className="text-gray-400 text-xs">
                          {language === 'it' ? 'Deve essere Safari, non Chrome o altri browser' : 'Must be Safari, not Chrome or other browsers'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded bg-black/30">
                      <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold shrink-0">2</span>
                      <div>
                        <p className="font-medium">{language === 'it' ? 'Tocca l\'icona Condividi' : 'Tap the Share icon'}</p>
                        <p className="text-gray-400 text-xs">
                          {language === 'it' ? 'Il quadrato con la freccia in basso' : 'The square with arrow at bottom'}
                        </p>
                        <Share2 className="w-6 h-6 mt-1 text-blue-400" />
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded bg-black/30">
                      <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold shrink-0">3</span>
                      <div>
                        <p className="font-medium">{language === 'it' ? 'Seleziona "Aggiungi a Home"' : 'Select "Add to Home Screen"'}</p>
                        <p className="text-gray-400 text-xs">
                          {language === 'it' ? 'Scorri le opzioni e tocca questa voce' : 'Scroll the options and tap this item'}
                        </p>
                        <Plus className="w-6 h-6 mt-1 text-blue-400" />
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-3 rounded bg-black/30">
                      <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold shrink-0">4</span>
                      <div>
                        <p className="font-medium">{language === 'it' ? 'Conferma "Aggiungi"' : 'Confirm "Add"'}</p>
                        <p className="text-gray-400 text-xs">
                          {language === 'it' ? 'L\'app apparirà sulla tua home screen' : 'The app will appear on your home screen'}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Generic Instructions for other browsers */}
            {!isIOS && !isAndroid && !deferredPrompt && (
              <Card className="bg-[#1A1A1A] border-yellow-500/30 mb-6">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Globe className="w-8 h-8 text-yellow-500" />
                    <div>
                      <h2 className="font-semibold">{language === 'it' ? 'Browser Desktop' : 'Desktop Browser'}</h2>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-4">
                    {language === 'it' 
                      ? 'Cerca l\'icona di installazione nella barra degli indirizzi del browser, oppure usa il menu per "Installa app".'
                      : 'Look for the install icon in the browser address bar, or use the menu to "Install app".'}
                  </p>
                </CardContent>
              </Card>
            )}
          </>
        )}
        
        {/* Share Link */}
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Link2 className="w-5 h-5 text-yellow-500" />
              {language === 'it' ? 'Condividi con amici' : 'Share with friends'}
            </h3>
            <div className="flex gap-2">
              <Input 
                value={appUrl} 
                readOnly 
                className="bg-black/30 border-white/10 text-sm"
              />
              <Button 
                variant="outline" 
                className="border-yellow-500/30 text-yellow-400 shrink-0"
                onClick={() => {
                  navigator.clipboard.writeText(appUrl);
                  toast.success(language === 'it' ? 'Link copiato!' : 'Link copied!');
                }}
              >
                <Copy className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {language === 'it' 
                ? 'Invia questo link ai tuoi amici per farli giocare!'
                : 'Send this link to your friends to let them play!'}
            </p>
          </CardContent>
        </Card>
        
        {/* QR Code placeholder */}
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6 text-center">
            <h3 className="font-semibold mb-3">{language === 'it' ? 'Scansiona QR Code' : 'Scan QR Code'}</h3>
            <div className="w-40 h-40 mx-auto bg-white p-2 rounded-lg">
              {/* Simple QR-like pattern */}
              <div className="w-full h-full bg-black rounded flex items-center justify-center text-white text-xs">
                <QrCode className="w-20 h-20" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              {language === 'it' 
                ? 'Scansiona con la fotocamera del telefono'
                : 'Scan with your phone camera'}
            </p>
          </CardContent>
        </Card>
        
        {/* Beta Notice */}
        <div className="text-center text-xs text-gray-500 mt-8 pb-8">
          <p>CineWorld Studio's - Beta Test v1.0</p>
          <p className="mt-1">
            {language === 'it' 
              ? 'L\'app si aggiorna automaticamente. Nessun download dagli store richiesto.'
              : 'The app updates automatically. No store download required.'}
          </p>
        </div>
      </div>
    </div>
  );
};

// ==================== NOTIFICATIONS PAGE ====================

export default DownloadAppPage;
