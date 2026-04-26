import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { RefreshCw, Users, Building2, UserCircle, Sparkles, ImageIcon, Wand2 } from 'lucide-react';

/**
 * AdminAvatarsTab — Step C: audit + apply avatar mancanti.
 */
export default function AdminAvatarsTab({ api }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [scope, setScope] = useState('all');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/avatars/audit');
      setData(res.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore audit');
    }
    setLoading(false);
  }, [api]);

  useEffect(() => { load(); }, [load]);

  const applyMissing = async () => {
    if (!window.confirm(`Applicare avatar dicebear coerenti (sesso, etnia) a tutti gli NPC sprovvisti${scope !== 'all' ? ` di tipo "${scope}"` : ''}?`)) return;
    setApplying(true);
    try {
      const res = await api.post(`/admin/avatars/apply-missing?only=${scope}`);
      toast.success(`Avatar applicati: ${res.data?.applied || 0}`);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore');
    }
    setApplying(false);
  };

  const regenerateAll = async () => {
    if (!window.confirm(`⚠️ Rigenerare COMPLETAMENTE l'avatar di tutti gli NPC${scope !== 'all' ? ` di tipo "${scope}"` : ''}? Sostituirà anche quelli esistenti.`)) return;
    setApplying(true);
    try {
      const res = await api.post(`/admin/avatars/regenerate-all?only=${scope}`);
      toast.success(`Avatar rigenerati: ${res.data?.regenerated || 0}`);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore');
    }
    setApplying(false);
  };

  if (loading || !data) {
    return <div className="text-center py-12 text-gray-500" data-testid="admin-avatars-loading">
      <RefreshCw className="w-5 h-5 animate-spin mx-auto" />
    </div>;
  }

  const { players, production_houses, npcs } = data;

  return (
    <div className="space-y-3" data-testid="admin-avatars-tab">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <ImageIcon className="w-4 h-4 text-pink-400" />
            Audit Avatar
          </h2>
          <p className="text-[10px] text-gray-500 mt-0.5">Verifica copertura avatar di Player, Case di Produzione, NPC.</p>
        </div>
        <Button size="sm" variant="outline" className="text-xs h-7" onClick={load}>
          <RefreshCw className="w-3 h-3 mr-1" /> Aggiorna
        </Button>
      </div>

      {/* PLAYERS */}
      <Card className="bg-[#111113] border-white/5">
        <CardContent className="p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-bold text-blue-200">Player</h3>
            <Badge className="bg-white/5 text-gray-300 text-[9px] h-4 border border-white/10 px-1.5">{players.total}</Badge>
          </div>
          <div className="grid grid-cols-3 gap-2 text-[10px]">
            <Stat label="Custom" val={players.with_custom} color="text-emerald-400" />
            <Stat label="Avatar base" val={players.with_base} color="text-amber-400" />
            <Stat label="Senza" val={players.without} color="text-red-400" />
          </div>
          <p className="text-[9px] text-gray-500 italic">I player gestiscono autonomamente il proprio avatar.</p>
        </CardContent>
      </Card>

      {/* PRODUCTION HOUSES */}
      <Card className="bg-[#111113] border-white/5">
        <CardContent className="p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-emerald-200">Case di Produzione</h3>
            <Badge className="bg-white/5 text-gray-300 text-[9px] h-4 border border-white/10 px-1.5">{production_houses.total}</Badge>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <Stat label="Logo custom" val={production_houses.with_custom} color="text-emerald-400" />
            <Stat label="Logo default" val={production_houses.with_base} color="text-amber-400" />
          </div>
          <p className="text-[9px] text-gray-500 italic">I logo delle case di produzione sono gestiti dai player.</p>
        </CardContent>
      </Card>

      {/* NPCs */}
      <Card className="bg-[#111113] border-pink-500/20">
        <CardContent className="p-3 space-y-2.5">
          <div className="flex items-center gap-2">
            <UserCircle className="w-4 h-4 text-pink-400" />
            <h3 className="text-sm font-bold text-pink-200">NPC (registi, attori, sceneggiatori, compositori, ...)</h3>
            <Badge className="bg-pink-500/20 text-pink-300 text-[9px] h-4 border border-pink-500/30 px-1.5">{npcs.total.toLocaleString()}</Badge>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <Stat label="Con avatar" val={npcs.with_avatar} color="text-emerald-400" big />
            <Stat label="Senza avatar" val={npcs.without_avatar} color="text-red-400" big />
          </div>

          {/* Breakdown */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            {Object.entries(npcs.by_type || {}).map(([type, b]) => {
              const pct = b.total ? Math.round((b.with_avatar / b.total) * 100) : 0;
              return (
                <div key={type} className="rounded-lg border border-white/5 bg-black/20 p-1.5"
                  data-testid={`npc-type-${type}`}>
                  <p className="text-[9px] uppercase font-bold text-gray-400 tracking-wider">{type}</p>
                  <p className="text-[10px] text-white">{b.with_avatar} / {b.total}</p>
                  <div className="h-1 bg-black/40 rounded-full mt-0.5 overflow-hidden">
                    <div className={`h-full ${pct === 100 ? 'bg-emerald-500' : pct >= 70 ? 'bg-amber-500' : 'bg-red-500'}`}
                      style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Apply controls */}
          <div className="border-t border-white/10 pt-2.5 space-y-2">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] text-gray-400">Scope:</span>
              {['all', 'actor', 'director', 'screenwriter', 'composer', 'illustrator'].map(s => (
                <button key={s}
                  onClick={() => setScope(s)}
                  disabled={applying}
                  className={`text-[9px] px-2 py-0.5 rounded font-bold border ${
                    scope === s ? 'bg-pink-500/20 text-pink-200 border-pink-500/40' :
                    'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10'
                  }`}
                  data-testid={`avatars-scope-${s}`}>
                  {s === 'all' ? 'Tutti' : s}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button size="sm" className="h-8 text-xs bg-pink-600 hover:bg-pink-700"
                onClick={applyMissing} disabled={applying}
                data-testid="apply-missing-avatars-btn">
                {applying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : (
                  <><Wand2 className="w-3.5 h-3.5 mr-1.5" /> Applica mancanti</>
                )}
              </Button>
              <Button size="sm" variant="outline" className="h-8 text-xs border-amber-500/30 text-amber-300 hover:bg-amber-500/10"
                onClick={regenerateAll} disabled={applying}
                data-testid="regenerate-all-avatars-btn">
                <Sparkles className="w-3.5 h-3.5 mr-1.5" /> Rigenera TUTTI
              </Button>
            </div>
            <p className="text-[9px] text-gray-500 italic leading-relaxed">
              💡 Avatar generati con dicebear-personas, coerenti con sesso e etnia (skin color derivato da nationality NPC).
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, val, color, big = false }) {
  return (
    <div className="rounded-lg border border-white/5 bg-black/20 p-1.5">
      <p className="text-[8px] uppercase font-bold text-gray-500 tracking-wider">{label}</p>
      <p className={`${big ? 'text-base' : 'text-sm'} font-bold ${color || 'text-white'}`}>
        {(val || 0).toLocaleString()}
      </p>
    </div>
  );
}
