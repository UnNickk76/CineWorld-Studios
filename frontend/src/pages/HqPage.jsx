import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Shield, Gavel, ArrowUp, Lock, Zap, DollarSign, Loader2,
  ChevronRight, AlertTriangle, CheckCircle, Star, Swords, Clock, History, Building
} from 'lucide-react';

const DIVISION_ICONS = {
  investigative: Search,
  operative: Shield,
  legal: Gavel,
};

const DIVISION_COLORS = {
  investigative: { bg: 'from-cyan-500/20 to-cyan-900/10', border: 'border-cyan-500/30', text: 'text-cyan-400', badge: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30', glow: 'shadow-cyan-500/20' },
  operative: { bg: 'from-orange-500/20 to-orange-900/10', border: 'border-orange-500/30', text: 'text-orange-400', badge: 'bg-orange-500/15 text-orange-400 border-orange-500/30', glow: 'shadow-orange-500/20' },
  legal: { bg: 'from-purple-500/20 to-purple-900/10', border: 'border-purple-500/30', text: 'text-purple-400', badge: 'bg-purple-500/15 text-purple-400 border-purple-500/30', glow: 'shadow-purple-500/20' },
};

const DivisionCard = ({ divId, data, onUpgrade, upgrading, playerFunds, playerCp, navigate }) => {
  const colors = DIVISION_COLORS[divId];
  const Icon = DIVISION_ICONS[divId];
  const config = data.config;
  const level = data.level;
  const maxLevel = config.max_level;
  const progressPct = (level / maxLevel) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card className={`bg-[#111113] border ${colors.border} overflow-hidden hover:shadow-lg ${colors.glow} transition-all duration-300`}>
        <div className={`h-1.5 bg-gradient-to-r ${colors.bg}`} />
        <CardContent className="p-4 sm:p-5 space-y-4">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 sm:w-11 sm:h-11 rounded-lg bg-gradient-to-br ${colors.bg} flex items-center justify-center border ${colors.border}`}>
                <Icon className={`w-5 h-5 ${colors.text}`} />
              </div>
              <div>
                <h3 className="font-['Bebas_Neue'] text-lg sm:text-xl tracking-wide text-white">{config.name}</h3>
                <p className="text-xs text-gray-500 leading-snug max-w-[220px]">{config.desc}</p>
              </div>
            </div>
            <Badge className={`${colors.badge} border text-xs font-bold px-2 py-0.5`} data-testid={`div-level-${divId}`}>
              Lv {level}
            </Badge>
          </div>

          {/* Level Progress */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-gray-500">
              <span>Progresso</span>
              <span>{level}/{maxLevel}</span>
            </div>
            <Progress value={progressPct} className="h-2 bg-white/5" />
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-0.5">Azioni Oggi</p>
              <p className="text-base font-bold text-white" data-testid={`daily-remaining-${divId}`}>
                {data.daily_remaining}<span className="text-gray-500 font-normal text-xs">/{data.daily_limit}</span>
              </p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-0.5">Limite Giornaliero</p>
              <p className="text-base font-bold text-white">{data.daily_limit}</p>
            </div>
          </div>

          {/* Upgrade / Purchase Section */}
          {level === 0 ? (
            /* NOT purchased yet - redirect to Infrastructure board */
            <div className="bg-black/30 rounded-lg p-3 space-y-2 border border-dashed border-white/10 text-center">
              <Lock className={`w-5 h-5 mx-auto ${colors.text} opacity-50`} />
              <p className="text-xs text-gray-400">Non ancora acquistata</p>
              <Button
                size="sm"
                className="w-full h-8 text-xs bg-yellow-600/80 hover:bg-yellow-600 text-white font-bold"
                onClick={() => navigate('/infrastructure')}
                data-testid={`buy-from-infra-${divId}`}
              >
                <Building className="w-3.5 h-3.5 mr-1.5" />
                Acquista da Infrastrutture
              </Button>
            </div>
          ) : data.next_level ? (
            <div className="bg-black/30 rounded-lg p-3 space-y-3 border border-white/5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400 flex items-center gap-1.5">
                  <ArrowUp className="w-3.5 h-3.5" /> Livello {data.next_level}
                </span>
                {data.can_upgrade ? (
                  <Badge className="bg-green-500/15 text-green-400 border-green-500/30 border text-[10px]">Disponibile</Badge>
                ) : (
                  <Badge className="bg-red-500/10 text-red-400 border-red-500/20 border text-[10px]">Bloccato</Badge>
                )}
              </div>
              {data.next_cost && (
                <div className="flex gap-3 text-xs">
                  <span className={`flex items-center gap-1 ${playerFunds >= (data.next_cost.funds || 0) ? 'text-green-400' : 'text-red-400'}`}>
                    <DollarSign className="w-3 h-3" />
                    {(data.next_cost.funds || 0).toLocaleString()}
                  </span>
                  <span className={`flex items-center gap-1 ${playerCp >= (data.next_cost.cinepass || 0) ? 'text-green-400' : 'text-red-400'}`}>
                    <Zap className="w-3 h-3" />
                    {data.next_cost.cinepass} CP
                  </span>
                </div>
              )}
              {!data.can_upgrade && data.upgrade_reason && (
                <p className="text-[10px] text-red-400/80 flex items-center gap-1">
                  <Lock className="w-3 h-3 flex-shrink-0" /> {data.upgrade_reason}
                </p>
              )}
              <Button
                size="sm"
                className={`w-full h-9 text-xs font-bold tracking-wider uppercase ${
                  data.can_upgrade
                    ? `bg-gradient-to-r ${colors.bg} ${colors.text} ${colors.border} border hover:brightness-125`
                    : 'bg-white/5 text-gray-600 cursor-not-allowed'
                }`}
                disabled={!data.can_upgrade || upgrading}
                onClick={() => onUpgrade(divId)}
                data-testid={`upgrade-btn-${divId}`}
              >
                {upgrading ? <Loader2 className="w-4 h-4 animate-spin" /> : (
                  <>
                    <ArrowUp className="w-3.5 h-3.5 mr-1.5" />
                    Migliora a Lv {data.next_level}
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="bg-yellow-500/5 rounded-lg p-3 border border-yellow-500/20 text-center">
              <p className="text-xs text-yellow-500 font-semibold flex items-center justify-center gap-1.5">
                <Star className="w-3.5 h-3.5" /> Livello Massimo Raggiunto
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

const LegalHistoryItem = ({ action, userId }) => {
  const isAttacker = action.is_attacker;
  const won = action.success;

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border ${
      won ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20'
    }`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
        won ? 'bg-green-500/20' : 'bg-red-500/20'
      }`}>
        {won ? <CheckCircle className="w-4 h-4 text-green-400" /> : <AlertTriangle className="w-4 h-4 text-red-400" />}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">
          {isAttacker ? `Causa vs ${action.other_nickname}` : `Causa da ${action.other_nickname}`}
        </p>
        <p className="text-[10px] text-gray-500">
          {won
            ? (isAttacker ? `Vittoria! Penalita' $${(action.penalty_funds || 0).toLocaleString()}` : 'Hai perso la causa')
            : (isAttacker ? `Persa. -$${(action.own_penalty_funds || 0).toLocaleString()}, -${action.fame_loss || 0} fama` : 'Causa respinta')
          }
        </p>
      </div>
      <Badge className={`text-[9px] ${won ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
        {action.probability}%
      </Badge>
    </div>
  );
};

const HqPage = () => {
  const { api, user } = useContext(AuthContext);
  const { t } = useTranslations();
  const navigate = useNavigate();

  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const res = await api.get('/pvp/status');
      setStatus(res.data);
    } catch (err) {
      toast.error("Errore nel caricamento dello stato HQ");
    }
  }, [api]);

  const loadHistory = useCallback(async () => {
    try {
      const res = await api.get('/pvp/legal-history');
      setHistory(res.data.actions || []);
    } catch {
      // silent
    }
  }, [api]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([loadStatus(), loadHistory()]);
      setLoading(false);
    };
    init();
  }, [loadStatus, loadHistory]);

  const handleUpgrade = async (divisionId) => {
    setUpgrading(divisionId);
    try {
      const res = await api.post('/pvp/upgrade', { division: divisionId });
      toast.success(res.data.message);
      await loadStatus();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Errore nell'upgrade");
    } finally {
      setUpgrading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" data-testid="hq-loading">
        <Loader2 className="w-8 h-8 animate-spin text-yellow-500" />
      </div>
    );
  }

  if (!status) return null;

  const divisions = status.divisions || {};

  return (
    <div className="min-h-screen pt-16 pb-24 px-3 sm:px-4" data-testid="hq-page">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-yellow-500/30 to-amber-600/10 flex items-center justify-center border border-yellow-500/30">
              <Swords className="w-5 h-5 text-yellow-500" />
            </div>
            <div>
              <h1 className="font-['Bebas_Neue'] text-3xl sm:text-4xl tracking-wide text-white">Quartier Generale</h1>
              <p className="text-xs text-gray-500">Gestisci le tue divisioni PvP e difendi il tuo impero.</p>
            </div>
          </div>

          {/* Player Stats Bar */}
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge className="bg-white/5 border border-white/10 text-gray-300 text-xs gap-1">
              <Star className="w-3 h-3 text-yellow-500" /> Fama: {status.player_fame}
            </Badge>
            <Badge className="bg-white/5 border border-white/10 text-gray-300 text-xs gap-1">
              <Zap className="w-3 h-3 text-purple-400" /> Lv {status.player_level}
            </Badge>
            <Badge className="bg-white/5 border border-white/10 text-gray-300 text-xs gap-1">
              <DollarSign className="w-3 h-3 text-green-400" /> ${(status.funds || 0).toLocaleString()}
            </Badge>
            <Badge className="bg-white/5 border border-white/10 text-gray-300 text-xs gap-1">
              <Zap className="w-3 h-3 text-yellow-400" /> {status.cinepass} CP
            </Badge>
            {status.pending_legal_actions > 0 && (
              <Badge className="bg-red-500/15 text-red-400 border-red-500/30 border text-xs gap-1 animate-pulse">
                <AlertTriangle className="w-3 h-3" /> {status.pending_legal_actions} cause in arrivo
              </Badge>
            )}
          </div>
        </motion.div>

        {/* Divisions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {['investigative', 'operative', 'legal'].map((divId) => (
            <DivisionCard
              key={divId}
              divId={divId}
              data={divisions[divId]}
              onUpgrade={handleUpgrade}
              upgrading={upgrading === divId}
              playerFunds={status.funds || 0}
              playerCp={status.cinepass || 0}
              navigate={navigate}
            />
          ))}
        </div>

        {/* Legal History Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-full"
            data-testid="toggle-legal-history"
          >
            <History className="w-4 h-4" />
            <span>Storico Cause Legali</span>
            <ChevronRight className={`w-4 h-4 transition-transform ${showHistory ? 'rotate-90' : ''}`} />
            {history.length > 0 && (
              <Badge className="bg-white/5 text-gray-400 text-[10px] ml-auto">{history.length}</Badge>
            )}
          </button>
          <AnimatePresence>
            {showHistory && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="space-y-2 mt-3">
                  {history.length === 0 ? (
                    <p className="text-xs text-gray-600 text-center py-6">Nessuna causa legale ancora.</p>
                  ) : (
                    history.map((action) => (
                      <LegalHistoryItem key={action.id} action={action} userId={user?.id} />
                    ))
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Info Card */}
        <Card className="bg-[#111113] border border-white/5">
          <CardContent className="p-4 space-y-3">
            <h3 className="font-['Bebas_Neue'] text-lg tracking-wide text-yellow-500">Come Funziona</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-gray-400">
              <div className="space-y-1">
                <p className="text-cyan-400 font-semibold flex items-center gap-1"><Search className="w-3 h-3" /> Investigativa</p>
                <p>Indaga sui boicottaggi ricevuti. Scopri chi ti ha sabotato per contrattaccare o avviare cause legali.</p>
              </div>
              <div className="space-y-1">
                <p className="text-orange-400 font-semibold flex items-center gap-1"><Shield className="w-3 h-3" /> Operativa</p>
                <p>Difendi i tuoi contenuti (riduce danni) o lancia contro-attacchi mirati a sabotatori identificati.</p>
              </div>
              <div className="space-y-1">
                <p className="text-purple-400 font-semibold flex items-center gap-1"><Gavel className="w-3 h-3" /> Legale</p>
                <p>Avvia cause legali contro sabotatori identificati. In caso di vittoria, il nemico perde fondi e subisce penalita'.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HqPage;
