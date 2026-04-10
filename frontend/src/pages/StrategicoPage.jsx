import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  Shield, Search, Swords, Scale, Target, ArrowUpCircle, ChevronRight, Lock
} from 'lucide-react';

const PVP_DIVISIONS = [
  { type: 'pvp_operative', label: 'Divisione Operativa', desc: 'Esegui boicottaggi difensivi e contro-attacchi mirati ai sabotatori.', icon: Swords, color: 'red' },
  { type: 'pvp_investigative', label: 'Divisione Investigativa', desc: 'Indaga sui boicottaggi ricevuti per scoprire il responsabile.', icon: Search, color: 'cyan' },
  { type: 'pvp_legal', label: 'Divisione Legale', desc: 'Avvia azioni legali contro sabotatori identificati. Richiede Investigativa.', icon: Scale, color: 'purple' },
];

export default function StrategicoPage() {
  const { api, user, refreshUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [ownedPvP, setOwnedPvP] = useState([]);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(null);
  const [upgradeInfos, setUpgradeInfos] = useState({});
  const [securityData, setSecurityData] = useState({});

  useEffect(() => {
    loadData();
  }, [api]);

  const loadData = async () => {
    setLoading(true);
    try {
      const infraRes = await api.get('/infrastructure/my');
      const pvpTypes = ['pvp_operative', 'pvp_investigative', 'pvp_legal'];
      const pvpInfra = (infraRes.data.infrastructure || []).filter(i => pvpTypes.includes(i.type));
      setOwnedPvP(pvpInfra);

      // Load upgrade info for each
      const upgradePromises = pvpInfra.map(i =>
        api.get(`/infrastructure/${i.id}/upgrade-info`).then(r => [i.id, r.data]).catch(() => [i.id, null])
      );
      const secPromises = pvpInfra.map(i =>
        api.get(`/infrastructure/${i.id}/security`).then(r => [i.id, r.data]).catch(() => [i.id, null])
      );
      const [upgrades, securities] = await Promise.all([
        Promise.all(upgradePromises),
        Promise.all(secPromises),
      ]);
      setUpgradeInfos(Object.fromEntries(upgrades));
      setSecurityData(Object.fromEntries(securities));
    } catch {}
    setLoading(false);
  };

  const handleUpgrade = async (infraId) => {
    setUpgrading(infraId);
    try {
      const r = await api.post(`/infrastructure/${infraId}/upgrade`);
      toast.success(`Upgrade al Livello ${r.data.new_level}!`);
      refreshUser();
      await loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore upgrade'); }
    setUpgrading(null);
  };

  if (loading) return <div className="pt-20 text-center text-gray-500">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 max-w-2xl mx-auto px-3" data-testid="strategico-page">
      <div className="mb-4">
        <h1 className="font-['Bebas_Neue'] text-2xl tracking-wide">Strategico</h1>
        <p className="text-xs text-gray-500">Divisioni PvP: investigazione, operazioni e azioni legali</p>
      </div>

      {/* Overall threat level */}
      {ownedPvP.length > 0 && (
        <div className="mb-4 p-3 bg-gradient-to-r from-red-500/8 to-cyan-500/8 rounded-xl border border-white/8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-cyan-400" />
              <span className="text-sm font-semibold">Stato Difesa</span>
            </div>
            <Button variant="outline" className="h-7 text-[10px] border-red-500/20 text-red-400" onClick={() => navigate('/pvp-arena')}>
              Arena PvP <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Divisions */}
      <div className="space-y-3">
        {PVP_DIVISIONS.map(div => {
          const owned = ownedPvP.find(i => i.type === div.type);
          const DivIcon = div.icon;
          const upInfo = owned ? upgradeInfos[owned.id] : null;
          const sec = owned ? securityData[owned.id] : null;

          return (
            <div
              key={div.type}
              className={`rounded-xl border overflow-hidden transition-all ${
                owned
                  ? `bg-${div.color}-500/5 border-${div.color}-500/15`
                  : 'bg-white/2 border-white/5 opacity-50'
              }`}
              data-testid={`strategico-${div.type}`}
            >
              <div className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${owned ? `bg-${div.color}-500/15` : 'bg-white/5'}`}>
                    {owned ? <DivIcon className={`w-5 h-5 text-${div.color}-400`} /> : <Lock className="w-5 h-5 text-gray-600" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold">{div.label}</h3>
                      {owned && <Badge className={`text-[9px] bg-${div.color}-500/20 text-${div.color}-400`}>Lv.{owned.level || 1}</Badge>}
                    </div>
                    <p className="text-[10px] text-gray-500">{div.desc}</p>
                  </div>
                </div>

                {owned ? (
                  <div className="space-y-2 mt-3">
                    {/* Security stats */}
                    {sec && (
                      <div className="grid grid-cols-3 gap-2">
                        <div className="p-2 bg-black/20 rounded-lg text-center">
                          <p className="text-[9px] text-gray-400">Attacchi 7g</p>
                          <p className="text-sm font-bold text-red-400">{sec.recent_attacks_7d || 0}</p>
                        </div>
                        <div className="p-2 bg-black/20 rounded-lg text-center">
                          <p className="text-[9px] text-gray-400">Bloccati</p>
                          <p className="text-sm font-bold text-green-400">{sec.blocked_attacks_7d || 0}</p>
                        </div>
                        <div className="p-2 bg-black/20 rounded-lg text-center">
                          <p className="text-[9px] text-gray-400">Legali</p>
                          <p className="text-sm font-bold text-blue-400">{sec.active_legal_blocks || 0}</p>
                        </div>
                      </div>
                    )}

                    {/* Upgrade */}
                    {upInfo && upInfo.current_level < upInfo.max_level && (
                      <Button
                        className={`w-full h-8 text-[11px] ${upInfo.can_upgrade ? `bg-gradient-to-r from-${div.color}-600 to-${div.color}-500 text-white` : 'bg-gray-700 text-gray-400'}`}
                        disabled={!upInfo.can_upgrade || upgrading === owned.id}
                        onClick={() => handleUpgrade(owned.id)}
                      >
                        <ArrowUpCircle className="w-3 h-3 mr-1" />
                        {upgrading === owned.id ? '...' : `Lv.${upInfo.next_level} ($${upInfo.upgrade_cost?.toLocaleString()})`}
                      </Button>
                    )}
                    {upInfo && upInfo.current_level >= upInfo.max_level && (
                      <Badge className={`w-full h-8 flex items-center justify-center bg-${div.color}-500/20 text-${div.color}-400 text-[11px]`}>Livello Massimo</Badge>
                    )}
                  </div>
                ) : (
                  <Button variant="outline" className="w-full h-8 text-[11px] mt-2 border-white/10" onClick={() => navigate('/infrastructure')}>
                    <Lock className="w-3 h-3 mr-1" /> Acquista in Infrastrutture
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
