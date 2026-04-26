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
  Briefcase, AlertTriangle, Trash2, BookOpen, Globe, TrendingDown,
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

const GENDER_SYMBOL = { M: '♂', F: '♀', male: '♂', female: '♀' };
const GENDER_COLOR = { M: 'text-blue-400', F: 'text-pink-400', male: 'text-blue-400', female: 'text-pink-400' };

function StarRow({ count }) {
  const c = Math.max(1, Math.min(5, count || 1));
  return (
    <div className="flex items-center gap-0.5" data-testid={`stars-${c}`}>
      {[...Array(c)].map((_, i) => <Star key={i} className="w-2.5 h-2.5 text-yellow-400 fill-yellow-400" />)}
      {[...Array(5 - c)].map((_, i) => <Star key={`e${i}`} className="w-2.5 h-2.5 text-gray-700" />)}
    </div>
  );
}

function SkillsPopup({ npc, onClose }) {
  const skills = npc?.skills || {};
  const sorted = Object.entries(skills).sort(([, a], [, b]) => b - a);
  return (
    <div className="fixed inset-0 z-[125] bg-black/70 flex items-end sm:items-center justify-center p-3"
      onClick={onClose} data-testid="skills-popup">
      <div className="bg-[#111113] border border-white/10 rounded-2xl max-w-md w-full p-4 space-y-3 max-h-[80vh] overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between gap-2 flex-shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <img src={npc.avatar_url || '/avatar-placeholder.png'}
              onError={(e) => { e.currentTarget.src = '/avatar-placeholder.png'; }}
              className="w-9 h-9 rounded-full bg-gray-800 flex-shrink-0" alt="" />
            <div className="min-w-0">
              <p className="text-sm font-bold text-white truncate">{npc.name}</p>
              <div className="flex items-center gap-1.5">
                <StarRow count={npc.stars} />
                {typeof npc.fame_score === 'number' && (
                  <span className="text-[10px] text-amber-300">Fama {Math.round(npc.fame_score)}</span>
                )}
              </div>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X className="w-4 h-4" /></button>
        </div>

        {sorted.length === 0 ? (
          <p className="text-xs text-gray-500 text-center py-6">Nessuna skill disponibile.</p>
        ) : (
          <div className="space-y-1.5 overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin' }}>
            {sorted.map(([k, v]) => {
              const pct = Math.min(100, Math.max(0, parseInt(v) || 0));
              const color = pct >= 90 ? 'from-yellow-400 to-amber-400' :
                            pct >= 70 ? 'from-emerald-400 to-green-500' :
                            pct >= 40 ? 'from-blue-400 to-sky-500' :
                            'from-gray-500 to-gray-600';
              const textColor = pct >= 90 ? 'text-yellow-300' :
                                pct >= 70 ? 'text-emerald-300' :
                                pct >= 40 ? 'text-blue-300' :
                                'text-gray-400';
              return (
                <div key={k} data-testid={`skill-row-${k}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-gray-300 capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className={`text-[10px] font-bold ${textColor}`}>{pct}</span>
                  </div>
                  <div className="h-1 bg-black/40 rounded-full overflow-hidden mt-0.5">
                    <div className={`h-full bg-gradient-to-r ${color} transition-all`}
                      style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
        <p className="text-[9px] text-gray-600 italic flex-shrink-0">
          {npc.nationality || '—'}{npc.age ? ` • ${npc.age} anni` : ''}{npc.gender ? ` • ${npc.gender}` : ''}
        </p>
      </div>
    </div>
  );
}

function NpcCard({ npc, role, onPreEngage, onShowSkills, busy, accentClass }) {
  const skills = npc.skills || {};
  const top3 = Object.entries(skills).sort(([, a], [, b]) => b - a).slice(0, 3);
  return (
    <Card className={`bg-[#0F0F10] border ${accentClass} hover:border-yellow-500/40 transition-all`}
      data-testid={`npc-card-${npc.id}`}>
      <CardContent className="p-2.5">
        <div className="flex items-start gap-2.5">
          <button onClick={() => onShowSkills(npc)} className="flex-shrink-0"
            data-testid={`avatar-${npc.id}`} title="Vedi skill">
            <img
              src={npc.avatar_url || '/avatar-placeholder.png'}
              alt={npc.name}
              onError={(e) => { e.currentTarget.src = '/avatar-placeholder.png'; }}
              className="w-10 h-10 rounded-full bg-gray-800 object-cover hover:ring-2 hover:ring-yellow-500/40 transition"
            />
          </button>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <button onClick={() => onShowSkills(npc)}
                className="text-xs sm:text-sm font-semibold text-white truncate hover:text-yellow-300 underline decoration-dotted underline-offset-2 text-left"
                data-testid={`name-${npc.id}`} title="Vedi skill">
                {npc.name}
              </button>
              {npc.gender && GENDER_SYMBOL[npc.gender] && (
                <span className={`text-sm font-bold ${GENDER_COLOR[npc.gender] || ''}`}>{GENDER_SYMBOL[npc.gender]}</span>
              )}
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
              {prop.npc_gender && GENDER_SYMBOL[prop.npc_gender] && (
                <span className={`text-sm font-bold ${GENDER_COLOR[prop.npc_gender] || ''}`}>{GENDER_SYMBOL[prop.npc_gender]}</span>
              )}
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

function RosterCard({ eng, busy, onRelease, onOpenDiary, onShowSkills }) {
  const snap = eng.npc_snapshot || {};
  const isThreat = eng.contract_status === 'threatened';
  const dr = eng.days_remaining ?? 0;
  const urgent = isThreat || dr < 7;
  return (
    <Card className={`bg-[#0F0F10] border ${
      isThreat ? 'border-red-500/40 animate-pulse' :
      urgent ? 'border-orange-500/40' :
      'border-white/10'
    }`} data-testid={`roster-card-${eng.id}`}>
      <CardContent className="p-2.5">
        <div className="flex items-start gap-2.5">
          <button onClick={() => onShowSkills?.({ ...snap, ...eng, name: snap.name, skills: snap.skills || eng.skills })}
            className="flex-shrink-0" title="Vedi skill" data-testid={`roster-avatar-${eng.id}`}>
            <img
              src={snap.avatar_url || '/avatar-placeholder.png'}
              onError={(e) => { e.currentTarget.src = '/avatar-placeholder.png'; }}
              className="w-10 h-10 rounded-full bg-gray-800 object-cover hover:ring-2 hover:ring-yellow-500/40 transition" alt="" />
          </button>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs sm:text-sm font-semibold text-white truncate">{snap.name}</span>
              {snap.gender && GENDER_SYMBOL[snap.gender] && (
                <span className={`text-sm font-bold ${GENDER_COLOR[snap.gender] || ''}`}>{GENDER_SYMBOL[snap.gender]}</span>
              )}
              <span className="text-base">{eng.happiness_emoji || '🙂'}</span>
              <Badge className="bg-white/5 text-gray-300 text-[8px] h-3.5 border border-white/10 px-1">
                {ROLE_TABS.find(r => r.key === eng.role)?.label || eng.role}
              </Badge>
              <StarRow count={eng.npc_stars} />
              {onOpenDiary && (
                <button onClick={onOpenDiary} className="text-amber-300 hover:text-amber-200 ml-auto"
                  title="Diario emotivo" data-testid={`open-diary-${eng.id}`}>
                  <BookOpen className="w-3 h-3" />
                </button>
              )}
            </div>
            <p className="text-[10px] text-gray-500 mt-0.5">
              {isThreat ? (
                <span className="text-red-300 font-semibold">
                  <AlertTriangle className="w-3 h-3 inline mr-0.5" />
                  Rescissione tra {eng.grace_days_remaining ?? 3}gg — usalo in un film!
                </span>
              ) : (
                <>Contratto: <span className={urgent ? 'text-orange-300 font-semibold' : 'text-gray-300'}>{dr}gg</span> rimanenti
                {' • '}Felicità: <span className="text-amber-300">{eng.happiness_score ?? 75}</span></>
              )}
            </p>
            {eng.cast_role_intended && (
              <p className="text-[9px] text-gray-600 mt-0.5">Ruolo: {eng.cast_role_intended}</p>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
          <div className="text-[10px] text-gray-500">
            Pagato: <span className="text-yellow-300">${(eng.fee_paid || 0).toLocaleString()}</span>
          </div>
          <Button size="sm" variant="ghost"
            className="h-6 px-2 text-[10px] text-red-400 hover:text-red-300 hover:bg-red-500/10"
            onClick={() => onRelease(eng)} disabled={busy}
            data-testid={`release-roster-${eng.id}`}>
            {busy ? <RefreshCw className="w-3 h-3 animate-spin" /> : <><Trash2 className="w-3 h-3 mr-1" />Libera</>}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function UnderContractCard({ item, busy, onMakeOffer }) {
  const isThreat = item.is_threatened;
  return (
    <Card className={`bg-[#0F0F10] border ${
      isThreat ? 'border-red-500/40 animate-pulse' : 'border-white/10'
    }`} data-testid={`under-contract-${item.engagement_id}`}>
      <CardContent className="p-2.5">
        <div className="flex items-start gap-2.5">
          <img src={item.npc_avatar_url || '/avatar-placeholder.png'}
            onError={(e) => { e.currentTarget.src = '/avatar-placeholder.png'; }}
            className="w-10 h-10 rounded-full bg-gray-800 object-cover flex-shrink-0" alt="" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs sm:text-sm font-semibold text-white truncate">{item.npc_name}</span>
              {item.npc_gender && GENDER_SYMBOL[item.npc_gender] && (
                <span className={`text-sm font-bold ${GENDER_COLOR[item.npc_gender] || ''}`}>{GENDER_SYMBOL[item.npc_gender]}</span>
              )}
              <span className="text-base">{item.happiness_emoji || '🙂'}</span>
              <Badge className="bg-white/5 text-gray-300 text-[8px] h-3.5 border border-white/10 px-1">
                {ROLE_TABS.find(r => r.key === item.role)?.label || item.role}
              </Badge>
              <StarRow count={item.npc_stars} />
            </div>
            <p className="text-[10px] text-gray-400 mt-0.5">
              <Briefcase className="w-2.5 h-2.5 inline mr-0.5" />
              {item.owner_studio} · <span className={isThreat ? 'text-red-300 font-semibold' : 'text-gray-300'}>{item.days_remaining}gg al termine</span>
            </p>
            {isThreat && (
              <p className="text-[9px] text-red-400 font-semibold mt-0.5">
                <AlertTriangle className="w-2.5 h-2.5 inline mr-0.5" />
                NPC sta per rescindere — momento ideale per un'offerta!
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
          <div className="text-[10px] text-gray-400">
            Min. offerta: <span className="text-yellow-300 font-bold">${(item.min_buyout_offer || 0).toLocaleString()}</span>
          </div>
          <Button size="sm" className="h-7 px-2.5 text-[10px] bg-red-600 hover:bg-red-700"
            onClick={() => onMakeOffer(item)} disabled={busy}
            data-testid={`make-offer-${item.engagement_id}`}>
            {busy ? <RefreshCw className="w-3 h-3 animate-spin" /> : <>Fai Offerta <DollarSign className="w-3 h-3 ml-0.5" /></>}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function BuyoutDialog({ item, onConfirm, onCancel, submitting }) {
  const minOffer = item?.min_buyout_offer || 0;
  const [amount, setAmount] = useState(minOffer);
  const [message, setMessage] = useState('');
  const lock = Math.floor(amount * 0.10);
  return (
    <div className="fixed inset-0 z-[120] bg-black/70 flex items-end sm:items-center justify-center p-3"
      onClick={() => !submitting && onCancel()}
      data-testid="buyout-dialog">
      <div className="bg-[#111113] border border-white/10 rounded-2xl max-w-md w-full p-4 space-y-3"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <img src={item.npc_avatar_url || '/avatar-placeholder.png'}
              onError={(e) => { e.currentTarget.src = '/avatar-placeholder.png'; }}
              className="w-9 h-9 rounded-full bg-gray-800 flex-shrink-0" alt="" />
            <div className="min-w-0">
              <p className="text-sm font-bold text-white truncate">{item.npc_name}</p>
              <p className="text-[10px] text-gray-400">Offerta acquisto · da {item.owner_studio}</p>
            </div>
          </div>
          <button onClick={onCancel} disabled={submitting} className="text-gray-500 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div>
          <p className="text-[10px] text-gray-400 mb-1">Importo offerta (min ${minOffer.toLocaleString()})</p>
          <input type="number" min={minOffer} step={1000}
            value={amount} onChange={(e) => setAmount(parseInt(e.target.value) || 0)}
            className="w-full bg-black/40 border border-white/10 rounded-lg px-2 py-1.5 text-sm text-white"
            data-testid="buyout-amount-input" />
        </div>
        <div>
          <p className="text-[10px] text-gray-400 mb-1">Messaggio (opzionale)</p>
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={2}
            placeholder="Convinci l'owner..."
            className="w-full bg-black/40 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white resize-none" />
        </div>
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-2.5 text-[10px] text-amber-200 space-y-0.5">
          <p>💡 Pagherai subito <span className="font-bold text-amber-300">${lock.toLocaleString()}</span> di lock (10%).</p>
          <p>Se l'owner accetta, paghi il resto e ricevi l'NPC alla scadenza del suo contratto.</p>
          <p>Se rifiuta, perdi il lock. Se contro-offre, decidi se accettare.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" className="flex-1 h-9 text-xs" onClick={onCancel} disabled={submitting}
            data-testid="buyout-cancel">Annulla</Button>
          <Button className="flex-1 h-9 text-xs bg-red-600 hover:bg-red-700"
            onClick={() => onConfirm({ amount, message })} disabled={submitting || amount < minOffer}
            data-testid="buyout-confirm">
            {submitting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Invia offerta'}
          </Button>
        </div>
      </div>
    </div>
  );
}

function DiaryPopup({ engId, npcName, api, onClose }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    api.get(`/talent-scout/diary/${engId}`)
      .then(res => { if (active) { setText(res.data?.diary || ''); setLoading(false); } })
      .catch(() => { if (active) { setText('Il talento non ha lasciato pensieri oggi.'); setLoading(false); } });
    return () => { active = false; };
  }, [engId, api]);
  return (
    <div className="fixed inset-0 z-[120] bg-black/70 flex items-end sm:items-center justify-center p-3"
      onClick={onClose} data-testid="diary-popup">
      <div className="bg-gradient-to-br from-[#1A1A1B] to-[#0B0B0C] border border-amber-500/30 rounded-2xl max-w-sm w-full p-4 space-y-3"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-amber-400" />
            <p className="text-sm font-bold text-amber-200">Diario di {npcName}</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X className="w-4 h-4" /></button>
        </div>
        {loading ? (
          <div className="text-center py-4 text-gray-500"><RefreshCw className="w-4 h-4 animate-spin mx-auto" /></div>
        ) : (
          <p className="text-sm text-gray-200 italic leading-relaxed">"{text}"</p>
        )}
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
  const [roster, setRoster] = useState([]);
  const [underContract, setUnderContract] = useState([]);
  const [showOnlyUnhappy, setShowOnlyUnhappy] = useState(true);
  const [pendingBuyout, setPendingBuyout] = useState(null);
  const [diaryFor, setDiaryFor] = useState(null); // {eng_id, name}
  const [skillsNpc, setSkillsNpc] = useState(null); // npc obj per popup skill
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

  const loadRoster = useCallback(async () => {
    try {
      const res = await api.get('/talent-scout/my-roster');
      setRoster(res.data?.items || []);
    } catch { /* ignore */ }
  }, [api]);

  const loadUnderContract = useCallback(async (onlyUnhappy = true) => {
    setLoading(true);
    try {
      const res = await api.get(`/market/talents/under-contract?only_unhappy=${onlyUnhappy}&limit=60`);
      setUnderContract(res.data?.items || []);
    } catch (e) {
      toast.error('Errore caricamento contratti');
    }
    setLoading(false);
  }, [api]);

  useEffect(() => {
    if (!open) return;
    loadPerks();
    loadProposals();
    loadRoster();
    loadRole(tab === 'proposed' || tab === 'roster' ? 'actor' : tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (!open) return;
    if (tab === 'proposed') {
      loadProposals();
    } else if (tab === 'roster') {
      loadRoster();
    } else if (tab === 'under_contract') {
      loadUnderContract(showOnlyUnhappy);
    } else if (!roleData[tab]) {
      loadRole(tab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, open, showOnlyUnhappy]);

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
      await Promise.all([loadPerks(), loadProposals(), loadRoster()]);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore accettazione');
    }
    setBusyId(null);
  };

  const releaseEngagement = async (eng) => {
    if (!window.confirm(`Liberare ${eng.npc_snapshot?.name || 'questo talento'}? La fee non sarà rimborsata.`)) return;
    setBusyId(eng.id);
    try {
      await api.post(`/talent-scout/release/${eng.id}`);
      toast.success('Talento liberato');
      await Promise.all([loadPerks(), loadRoster()]);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore liberazione');
    }
    setBusyId(null);
  };

  const submitBuyoutOffer = async ({ amount, message }) => {
    if (!pendingBuyout) return;
    setBusyId(pendingBuyout.engagement_id);
    try {
      await api.post(`/market/talents/buyout-offer/${pendingBuyout.engagement_id}`, {
        offered_amount: amount, message,
      });
      toast.success(`Offerta inviata. Lock pagato: $${Math.floor(amount * 0.10).toLocaleString()}`);
      setPendingBuyout(null);
      await loadUnderContract(showOnlyUnhappy);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore invio offerta');
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
                onPreEngage={(n) => startPreEngage(n, role)}
                onShowSkills={(n) => setSkillsNpc(n)} />
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
            onClick={() => setTab('under_contract')}
            className={`flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-semibold border transition-all whitespace-nowrap ${
              tab === 'under_contract'
                ? 'border-red-500/40 bg-red-500/10 text-red-300'
                : 'border-white/10 text-gray-400 hover:bg-white/5'
            }`}
            data-testid="tab-under-contract"
          >
            <Globe className="w-3 h-3" />
            Sotto Contratto
          </button>
          <button
            onClick={() => setTab('roster')}
            className={`flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-semibold border transition-all whitespace-nowrap relative ${
              tab === 'roster'
                ? 'border-amber-500/40 bg-amber-500/10 text-amber-300'
                : 'border-white/10 text-gray-400 hover:bg-white/5'
            }`}
            data-testid="tab-roster"
          >
            <Briefcase className="w-3 h-3" />
            Mio Roster
            {roster.length > 0 && (
              <span className={`absolute -top-1 -right-1 min-w-[14px] h-[14px] px-1 rounded-full text-[8px] font-bold text-white flex items-center justify-center ${
                roster.some(r => r.contract_status === 'threatened') ? 'bg-red-500 animate-pulse' :
                roster.some(r => (r.days_remaining ?? 99) < 7) ? 'bg-orange-500' :
                'bg-amber-500'
              }`}>
                {roster.length}
              </span>
            )}
          </button>
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
          ) : tab === 'roster' ? (
            <div className="space-y-2.5">
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-2.5">
                <p className="text-[10px] text-amber-200">
                  <Briefcase className="w-3 h-3 inline mr-1 align-text-bottom" />
                  Talenti pre-ingaggiati. La felicità decade se non li usi: gli infelici minacceranno di andarsene.
                  <span className="block mt-1 text-amber-400/70">😊 felice • 🙂 ok • 😐 neutro • 😠 scontento • 😡 in rescissione</span>
                  <span className="block mt-0.5 text-amber-400/70">Tocca <BookOpen className="w-2.5 h-2.5 inline" /> sulla card per leggere il diario emotivo.</span>
                </p>
              </div>
              {roster.length === 0 ? (
                <div className="text-center py-10 text-gray-500">
                  <Briefcase className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p className="text-xs">Nessun talento pre-ingaggiato.</p>
                  <p className="text-[10px] text-gray-600 mt-1">Vai sui tab dei ruoli per esplorare il mercato.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {roster.map(r => (
                    <RosterCard key={r.id} eng={r} busy={busyId === r.id}
                      onRelease={releaseEngagement}
                      onOpenDiary={() => setDiaryFor({ eng_id: r.id, name: r.npc_snapshot?.name || 'Talento' })}
                      onShowSkills={(n) => setSkillsNpc(n)} />
                  ))}
                </div>
              )}
            </div>
          ) : tab === 'under_contract' ? (
            <div className="space-y-2.5">
              <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-2.5 flex items-center justify-between gap-2">
                <p className="text-[10px] text-red-200 flex-1">
                  <TrendingDown className="w-3 h-3 inline mr-1 align-text-bottom" />
                  Talenti pre-ingaggiati da ALTRI player. Più sono infelici, più è probabile rubarli.
                </p>
                <button onClick={() => setShowOnlyUnhappy(v => !v)}
                  className={`text-[9px] px-2 py-1 rounded font-bold border whitespace-nowrap ${
                    showOnlyUnhappy ? 'bg-red-500/20 border-red-500/40 text-red-200' :
                    'bg-white/5 border-white/10 text-gray-400'
                  }`}
                  data-testid="toggle-only-unhappy">
                  {showOnlyUnhappy ? '😡 Solo infelici' : '🌐 Tutti'}
                </button>
              </div>
              {loading ? (
                <div className="text-center py-8 text-gray-500"><RefreshCw className="w-5 h-5 animate-spin mx-auto" /></div>
              ) : underContract.length === 0 ? (
                <div className="text-center py-10 text-gray-500">
                  <Globe className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p className="text-xs">Nessun talento sotto contratto trovato.</p>
                  <p className="text-[10px] text-gray-600 mt-1">{showOnlyUnhappy ? 'Prova a togliere il filtro.' : 'Nessun altro player ha ingaggi attivi al momento.'}</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {underContract.map(it => (
                    <UnderContractCard key={it.engagement_id} item={it} busy={busyId === it.engagement_id}
                      onMakeOffer={(item) => setPendingBuyout(item)} />
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

        {/* Buyout offer dialog */}
        {pendingBuyout && (
          <BuyoutDialog
            item={pendingBuyout}
            submitting={busyId === pendingBuyout.engagement_id}
            onConfirm={submitBuyoutOffer}
            onCancel={() => setPendingBuyout(null)}
          />
        )}

        {/* Diary popup */}
        {diaryFor && (
          <DiaryPopup
            engId={diaryFor.eng_id}
            npcName={diaryFor.name}
            api={api}
            onClose={() => setDiaryFor(null)}
          />
        )}

        {/* Skills popup */}
        {skillsNpc && (
          <SkillsPopup npc={skillsNpc} onClose={() => setSkillsNpc(null)} />
        )}
      </DialogContent>
    </Dialog>
  );
}
