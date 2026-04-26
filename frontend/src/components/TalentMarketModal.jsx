import React, { useContext, useEffect, useState, useCallback } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { toast } from 'sonner';
import {
  X, Star, Users, Pen, Music, Palette, Clapperboard,
  Sparkles, Search, RefreshCw, Lock, Mail, Clock, DollarSign, ChevronRight, Award,
} from 'lucide-react';

/**
 * Talent Market Modal — Sistema Talenti Vivente (Fase 1).
 * 5 ruoli + tab "Proposti a me" per offerte spontanee.
 * Visibilità e quantità ingaggiabili scalano con il livello dell'infra Talent Scout/Agenzia
 * di ciascun ruolo (vedi backend/routes/talent_market.py).
 */

const ROLE_TABS = [
  { key: 'actor', label: 'Attori', icon: Users, color: 'text-pink-300', accent: 'border-pink-500/40 bg-pink-500/10' },
  { key: 'director', label: 'Registi', icon: Clapperboard, color: 'text-amber-300', accent: 'border-amber-500/40 bg-amber-500/10' },
  { key: 'screenwriter', label: 'Sceneggiatori', icon: Pen, color: 'text-emerald-300', accent: 'border-emerald-500/40 bg-emerald-500/10' },
  { key: 'composer', label: 'Compositori', icon: Music, color: 'text-cyan-300', accent: 'border-cyan-500/40 bg-cyan-500/10' },
  { key: 'illustrator', label: 'Disegnatori', icon: Palette, color: 'text-purple-300', accent: 'border-purple-500/40 bg-purple-500/10' },
];

const DURATION_PRESETS = [
  { days: 30, label: '30g', mult: 1.0 },
  { days: 60, label: '60g', mult: 1.85 },
  { days: 90, label: '90g', mult: 2.55 },
  { days: 180, label: '180g', mult: 4.6 },
];

function StarRow({ count }) {
  const c = Math.max(1, Math.min(5, count || 1));
  return (
    <div className="flex items-center gap-0.5" data-testid={`stars-${c}`}>
      {[...Array(c)].map((_, i) => <Star key={i} className="w-2.5 h-2.5 text-yellow-400 fill-yellow-400" />)}
      {[...Array(5 - c)].map((_, i) => <Star key={`e${i}`} className="w-2.5 h-2.5 text-gray-700" />)}
    </div>
  );
}

function NpcCard({ npc, role, onPreEngage, busy, accentClass }) {
  const skills = npc.skills || {};
  const top3 = Object.entries(skills).sort(([, a], [, b]) => b - a).slice(0, 3);
  return (
    <Card className={`bg-[#0F0F10] border ${accentClass} hover:border-yellow-500/40 transition-all`}
      data-testid={`npc-card-${npc.id}`}>
      <CardContent className="p-2.5">
        <div className="flex items-start gap-2.5">
          <img
            src={npc.avatar_url || '/avatar-placeholder.png'}
            alt={npc.name}
            onError={(e) => { e.currentTarget.src = '/avatar-placeholder.png'; }}
            className="w-10 h-10 rounded-full bg-gray-800 object-cover flex-shrink-0"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs sm:text-sm font-semibold text-white truncate">{npc.name}</span>
              <StarRow count={npc.stars} />
            </div>
            <p className="text-[10px] text-gray-500 mt-0.5">
              {npc.nationality || '—'}{npc.age ? ` • ${npc.age}a` : ''}
              {typeof npc.fame_score === 'number' && (
                <> • <span className="text-amber-300">Fama {Math.round(npc.fame_score)}</span></>
              )}
            </p>
            {top3.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {top3.map(([k, v]) => (
                  <Badge key={k} className="bg-white/5 text-gray-300 text-[8px] h-3.5 border border-white/10 px-1">
                    {k.replace(/_/g, ' ')} <span className="text-emerald-300 ml-0.5">{v}</span>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
          <div className="text-[10px] text-gray-400">
            <span className="text-gray-500">Pre-ingaggio 30g</span>{' '}
            <span className="text-yellow-400 font-bold">${(npc.pre_engage_fee_30d || 0).toLocaleString()}</span>
          </div>
          <Button
            size="sm"
            className="h-7 px-2.5 text-[10px] bg-yellow-600 hover:bg-yellow-700"
            onClick={() => onPreEngage(npc)}
            disabled={busy}
            data-testid={`pre-engage-btn-${npc.id}`}
          >
            {busy ? <RefreshCw className="w-3 h-3 animate-spin" /> : <>Pre-ingaggia <ChevronRight className="w-3 h-3 ml-0.5" /></>}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ProposalCard({ prop, onAccept, busy }) {
  return (
    <Card className="bg-gradient-to-br from-purple-900/20 to-[#1A1A1B] border-purple-500/30">
      <CardContent className="p-2.5">
        <div className="flex items-start gap-2.5">
          <img
            src={prop.npc_avatar_url || '/avatar-placeholder.png'}
            alt={prop.npc_name}
            onError={(e) => { e.currentTarget.src = '/avatar-placeholder.png'; }}
            className="w-10 h-10 rounded-full bg-gray-800 object-cover flex-shrink-0"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs sm:text-sm font-semibold text-white truncate">{prop.npc_name}</span>
              <Badge className="bg-purple-500/20 text-purple-300 text-[8px] h-3.5 border border-purple-500/30 px-1">
                {ROLE_TABS.find(r => r.key === prop.role)?.label || prop.role}
              </Badge>
              <StarRow count={prop.npc_stars} />
            </div>
            <p className="text-[10px] text-gray-400 italic mt-1 line-clamp-2">"{prop.message}"</p>
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
          <div className="text-[10px] text-gray-400">
            <span className="text-gray-500">Offerta 30g</span>{' '}
            <span className="text-emerald-400 font-bold">${(prop.proposed_fee_30d || 0).toLocaleString()}</span>
          </div>
          <Button size="sm" className="h-7 px-2.5 text-[10px] bg-purple-600 hover:bg-purple-700"
            onClick={() => onAccept(prop)} disabled={busy}
            data-testid={`accept-prop-btn-${prop.id}`}>
            {busy ? <RefreshCw className="w-3 h-3 animate-spin" /> : <>Accetta <ChevronRight className="w-3 h-3 ml-0.5" /></>}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function PerkBar({ perks, role }) {
  const p = perks?.[role];
  if (!p) return null;
  if (!p.level) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-2.5 flex items-center gap-2">
        <Lock className="w-4 h-4 text-red-400" />
        <div className="flex-1">
          <p className="text-[11px] text-red-300 font-semibold">Infrastruttura mancante</p>
          <p className="text-[9px] text-red-400/70">Costruisci un'agenzia / talent scout per questo ruolo per accedere al mercato.</p>
        </div>
      </div>
    );
  }
  const slotPct = Math.min(100, Math.round((p.slot_used / Math.max(1, p.slot_total)) * 100));
  return (
    <div className="rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-2.5" data-testid={`perks-${role}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <Award className="w-3.5 h-3.5 text-yellow-400" />
          <span className="text-[11px] font-bold text-yellow-200">Lv {p.level}</span>
          <span className="text-[9px] text-gray-400">• Sconto {p.discount_pct}%</span>
          <span className="text-[9px] text-gray-400">• Max {p.max_duration_days}g</span>
        </div>
        <Badge className="bg-yellow-500/20 text-yellow-300 text-[9px] h-4 border border-yellow-500/30 px-1.5">
          {p.slot_used}/{p.slot_total} slot
        </Badge>
      </div>
      <div className="h-1 bg-black/40 rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-yellow-500 to-amber-500 transition-all"
          style={{ width: `${slotPct}%` }} />
      </div>
    </div>
  );
}

function PreEngageDialog({ npc, role, perks, onConfirm, onCancel, submitting }) {
  const p = perks?.[role];
  const maxDur = p?.max_duration_days || 30;
  const [duration, setDuration] = useState(30);
  const [castRole, setCastRole] = useState('supporting');

  const baseFee30 = npc?.pre_engage_fee_30d || 0;
  const mult = DURATION_PRESETS.find(d => d.days === duration)?.mult || 1.0;
  const finalFee = Math.max(1000, Math.round(baseFee30 * mult));

  return (
    <div className="fixed inset-0 z-[120] bg-black/70 flex items-end sm:items-center justify-center p-3"
      onClick={() => !submitting && onCancel()}
      data-testid="pre-engage-dialog">
      <div className="bg-[#111113] border border-white/10 rounded-2xl max-w-md w-full p-4 space-y-3"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <img src={npc.avatar_url || '/avatar-placeholder.png'}
              onError={(e) => { e.currentTarget.src = '/avatar-placeholder.png'; }}
              className="w-9 h-9 rounded-full bg-gray-800 flex-shrink-0" alt="" />
            <div className="min-w-0">
              <p className="text-sm font-bold text-white truncate">{npc.name}</p>
              <p className="text-[10px] text-gray-400">Pre-ingaggio · {ROLE_TABS.find(r => r.key === role)?.label}</p>
            </div>
          </div>
          <button onClick={onCancel} disabled={submitting} className="text-gray-500 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Duration picker */}
        <div>
          <p className="text-[10px] text-gray-400 mb-1">Durata contratto</p>
          <div className="grid grid-cols-4 gap-1.5">
            {DURATION_PRESETS.map(d => {
              const locked = d.days > maxDur;
              const active = duration === d.days;
              return (
                <button key={d.days}
                  onClick={() => !locked && setDuration(d.days)}
                  disabled={locked || submitting}
                  className={`py-1.5 px-1 rounded-lg border text-[10px] font-bold transition-all ${
                    active ? 'border-yellow-500 bg-yellow-500/10 text-yellow-300'
                      : locked ? 'border-white/5 bg-white/[0.02] text-gray-600 cursor-not-allowed'
                      : 'border-white/10 bg-white/[0.03] text-gray-300 hover:border-white/20'
                  }`}
                  data-testid={`duration-${d.days}`}
                >
                  {d.label}{locked && <Lock className="w-2.5 h-2.5 inline ml-0.5" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Cast role - only for actors */}
        {role === 'actor' && (
          <div>
            <p className="text-[10px] text-gray-400 mb-1">Ruolo previsto</p>
            <div className="grid grid-cols-3 gap-1.5">
              {[
                { v: 'protagonist', l: 'Protag.' },
                { v: 'co_protagonist', l: 'Co-prot.' },
                { v: 'antagonist', l: 'Antag.' },
                { v: 'supporting', l: 'Support.' },
                { v: 'cameo', l: 'Cameo' },
              ].map(o => (
                <button key={o.v}
                  onClick={() => setCastRole(o.v)}
                  disabled={submitting}
                  className={`py-1 px-1 rounded border text-[9px] transition-all ${
                    castRole === o.v ? 'border-pink-500 bg-pink-500/10 text-pink-300'
                      : 'border-white/10 bg-white/[0.03] text-gray-300 hover:border-white/20'
                  }`}
                  data-testid={`cast-role-${o.v}`}
                >{o.l}</button>
              ))}
            </div>
          </div>
        )}

        {/* Cost breakdown */}
        <div className="rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-2.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-gray-400">Costo totale</span>
            <span className="text-yellow-400 font-bold text-base">${finalFee.toLocaleString()}</span>
          </div>
          <p className="text-[9px] text-gray-500 mt-0.5">
            Sconto Lv: {p?.discount_pct || 0}% • Moltiplicatore durata x{mult}
          </p>
        </div>

        <div className="flex gap-2">
          <Button variant="ghost" className="flex-1 h-9 text-xs" onClick={onCancel} disabled={submitting}
            data-testid="pre-engage-cancel">Annulla</Button>
          <Button className="flex-1 h-9 text-xs bg-yellow-600 hover:bg-yellow-700"
            onClick={() => onConfirm({ duration, castRole, fee: finalFee })}
            disabled={submitting}
            data-testid="pre-engage-confirm">
            {submitting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Conferma'}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function TalentMarketModal({ open, onClose }) {
  const { api } = useContext(AuthContext);
  const [tab, setTab] = useState('actor');
  const [perks, setPerks] = useState(null);
  const [roleData, setRoleData] = useState({}); // {role: {items, infra_level, ...}}
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [pendingPreEngage, setPendingPreEngage] = useState(null); // {npc, role}

  const loadPerks = useCallback(async () => {
    try {
      const res = await api.get('/talent-scout/perks');
      setPerks(res.data?.perks || null);
    } catch { /* ignore */ }
  }, [api]);

  const loadRole = useCallback(async (role) => {
    setLoading(true);
    try {
      const res = await api.get(`/market/talents?role=${role}&limit=60`);
      setRoleData(prev => ({ ...prev, [role]: res.data }));
    } catch (e) {
      toast.error('Errore caricamento mercato');
    }
    setLoading(false);
  }, [api]);

  const loadProposals = useCallback(async () => {
    try {
      const res = await api.get('/market/talents/proposed-to-me');
      setProposals(res.data?.items || []);
    } catch { /* ignore */ }
  }, [api]);

  useEffect(() => {
    if (!open) return;
    loadPerks();
    loadProposals();
    loadRole(tab === 'proposed' ? 'actor' : tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (!open) return;
    if (tab === 'proposed') {
      loadProposals();
    } else if (!roleData[tab]) {
      loadRole(tab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, open]);

  const startPreEngage = (npc, role) => setPendingPreEngage({ npc, role });

  const confirmPreEngage = async ({ duration, castRole }) => {
    if (!pendingPreEngage) return;
    const { npc, role } = pendingPreEngage;
    setBusyId(npc.id);
    try {
      const body = {
        role,
        duration_days: duration,
        ...(role === 'actor' ? { cast_role_intended: castRole } : {}),
      };
      const res = await api.post(`/market/talents/pre-engage/${npc.id}`, body);
      toast.success(`Pre-ingaggio firmato! Costo: $${res.data.fee?.toLocaleString()}`);
      setPendingPreEngage(null);
      await Promise.all([loadPerks(), loadRole(role)]);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore pre-ingaggio');
    }
    setBusyId(null);
  };

  const acceptProposal = async (prop) => {
    setBusyId(prop.id);
    try {
      const res = await api.post(`/market/talents/proposed/${prop.id}/accept?duration_days=30`);
      toast.success(`Proposta accettata! Costo: $${res.data.fee?.toLocaleString()}`);
      await Promise.all([loadPerks(), loadProposals()]);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore accettazione');
    }
    setBusyId(null);
  };

  const renderRoleTab = (role) => {
    const data = roleData[role];
    const tabConfig = ROLE_TABS.find(r => r.key === role);
    if (!data && loading) {
      return <div className="text-center py-8 text-gray-500"><RefreshCw className="w-5 h-5 animate-spin mx-auto" /></div>;
    }
    if (!data) return null;
    const items = data.items || [];
    return (
      <div className="space-y-2.5">
        <PerkBar perks={perks} role={role} />
        {items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Search className="w-7 h-7 mx-auto mb-2 opacity-30" />
            <p className="text-xs">Nessun NPC disponibile a questo livello.</p>
            <p className="text-[10px] text-gray-600 mt-1">Sali di livello sull'infra "{tabConfig?.label}" per vederne di più.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {items.map(npc => (
              <NpcCard key={npc.id} npc={npc} role={role}
                accentClass={tabConfig?.accent || 'border-white/10'}
                busy={busyId === npc.id}
                onPreEngage={(n) => startPreEngage(n, role)} />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className="w-[96vw] max-w-3xl bg-[#0B0B0C] border border-white/10 p-0 max-h-[90vh] overflow-hidden flex flex-col"
        data-testid="talent-market-modal"
      >
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between px-3 py-2.5 border-b border-white/5 bg-gradient-to-r from-yellow-500/10 to-amber-500/5">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <div>
              <h2 className="text-sm font-bold text-yellow-200 leading-none">Mercato Talenti</h2>
              <p className="text-[9px] text-gray-400 leading-none mt-0.5">Pre-ingaggia NPCs · scalato sul tuo Talent Scout</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white p-1" data-testid="talent-market-close">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex-shrink-0 flex gap-1 overflow-x-auto px-2 py-2 border-b border-white/5"
          style={{ scrollbarWidth: 'none' }}>
          {ROLE_TABS.map(t => (
            <button key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-semibold border transition-all whitespace-nowrap ${
                tab === t.key
                  ? `${t.accent} ${t.color}`
                  : 'border-white/10 text-gray-400 hover:bg-white/5'
              }`}
              data-testid={`tab-${t.key}`}
            >
              <t.icon className="w-3 h-3" />
              {t.label}
            </button>
          ))}
          <button
            onClick={() => setTab('proposed')}
            className={`flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-semibold border transition-all whitespace-nowrap relative ${
              tab === 'proposed'
                ? 'border-purple-500/40 bg-purple-500/10 text-purple-300'
                : 'border-white/10 text-gray-400 hover:bg-white/5'
            }`}
            data-testid="tab-proposed"
          >
            <Mail className="w-3 h-3" />
            Proposti a me
            {proposals.length > 0 && (
              <span className="absolute -top-1 -right-1 min-w-[14px] h-[14px] px-1 bg-purple-500 rounded-full text-[8px] font-bold text-white flex items-center justify-center">
                {proposals.length}
              </span>
            )}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-3" style={{ scrollbarWidth: 'thin' }}>
          {tab === 'proposed' ? (
            <div className="space-y-2.5">
              <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-2.5">
                <p className="text-[10px] text-purple-200">
                  <Mail className="w-3 h-3 inline mr-1 align-text-bottom" />
                  NPCs che si sono proposti spontaneamente a te. Le offerte scadono in 48h.
                </p>
              </div>
              {proposals.length === 0 ? (
                <div className="text-center py-10 text-gray-500">
                  <Mail className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p className="text-xs">Nessuna proposta al momento.</p>
                  <p className="text-[10px] text-gray-600 mt-1">Più visibilità ha il tuo studio, più NPCs ti contatteranno.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {proposals.map(p => (
                    <ProposalCard key={p.id} prop={p} busy={busyId === p.id} onAccept={acceptProposal} />
                  ))}
                </div>
              )}
            </div>
          ) : (
            renderRoleTab(tab)
          )}
        </div>

        {/* Pre-engage dialog */}
        {pendingPreEngage && (
          <PreEngageDialog
            npc={pendingPreEngage.npc}
            role={pendingPreEngage.role}
            perks={perks}
            submitting={busyId === pendingPreEngage.npc.id}
            onConfirm={confirmPreEngage}
            onCancel={() => setPendingPreEngage(null)}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
