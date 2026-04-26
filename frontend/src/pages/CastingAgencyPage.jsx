import React, { useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Users, Star, Briefcase, Trash2, RefreshCw, ChevronRight, BookOpen, Award, Shield, Swords, Heart, Sparkles, Search, Pen, Diamond, ChevronDown, ChevronUp, UserPlus, Lock, Unlock, FileSignature, Clapperboard, ArrowRight, Zap } from 'lucide-react';
import { AuthContext } from '../contexts';
import { useConfirm } from '../components/ConfirmDialog';
import FreeAgentsMarketModal from '../components/FreeAgentsMarketModal';
import TalentMarketModal from '../components/TalentMarketModal';

const GENRE_ICONS = {
  action: Swords, comedy: Sparkles, drama: Heart, horror: Shield,
  sci_fi: Star, romance: Heart, thriller: Shield, animation: Sparkles,
  fantasy: Star, musical: Sparkles, western: Swords, war: Shield,
  noir: Shield, adventure: Swords, biographical: BookOpen, documentary: BookOpen
};

function SkillBar({ name, value, cap }) {
  const pct = Math.min(100, value);
  const capPct = cap ? Math.min(100, cap) : 100;
  return (
    <div className="flex items-center gap-2 text-[10px]">
      <span className="w-24 text-gray-400 truncate">{name}</span>
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full relative">
        {cap && <div className="absolute h-full rounded-full bg-yellow-900/30" style={{ width: `${capPct}%` }} />}
        <div className={`absolute h-full rounded-full ${value >= 80 ? 'bg-emerald-500' : value >= 60 ? 'bg-cyan-500' : value >= 40 ? 'bg-amber-500' : 'bg-red-500'}`}
          style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 text-right font-mono text-gray-300">{value}</span>
    </div>
  );
}

function ActorCard({ actor, onFire, onSendToSchool, onRelease, firing, sendingToSchool, releasing }) {
  const [expanded, setExpanded] = useState(false);
  const skills = actor.skills || {};
  const avgSkill = Object.values(skills).length > 0
    ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length)
    : 0;

  // Contract countdown
  const contractDays = actor.contract_expires_at
    ? Math.max(0, Math.ceil((new Date(actor.contract_expires_at) - new Date()) / (1000 * 60 * 60 * 24)))
    : null;
  const contractColor = contractDays === null ? 'text-gray-500'
    : contractDays > 14 ? 'text-emerald-400'
    : contractDays > 3 ? 'text-amber-400' : 'text-red-400';

  return (
    <Card className="bg-[#1A1A1B] border-gray-800 hover:border-gray-700 transition-all" data-testid={`agency-actor-${actor.id}`}>
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <img src={actor.avatar_url} alt={actor.name} className="w-10 h-10 rounded-full bg-gray-800" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-semibold truncate">{actor.name}</span>
              <span className={`text-xs font-bold ${actor.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>{actor.gender === 'female' ? '♀' : '♂'}</span>
              {actor.is_legendary && <Badge className="bg-yellow-500/20 text-yellow-400 text-[8px] h-4">Leggendario</Badge>}
              {[...Array(actor.stars || 2)].map((_, i) => <Star key={i} className="w-2.5 h-2.5 text-yellow-500 fill-yellow-500" />)}
            </div>
            <p className="text-[10px] text-gray-500">
              {actor.nationality} &bull; {actor.age} anni &bull; Skill media: <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>
              &bull; Film: {actor.films_count || 0}
              {contractDays !== null && (
                <> &bull; <span className={contractColor} data-testid={`contract-days-${actor.id}`}>📜 {contractDays}gg</span></>
              )}
              {actor.loyalty_score > 0 && (
                <> &bull; <span className="text-purple-400" title="Bonus loyalty CWSv">💜 +{Math.round(actor.loyalty_score)}%</span></>
              )}
            </p>
            <div className="flex flex-wrap gap-1 mt-1">
              {(actor.strong_genres_names || actor.strong_genres || []).map((g, i) => (
                <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[8px] h-4 border border-emerald-800/40">{typeof g === 'string' ? g : g}</Badge>
              ))}
              {(actor.adaptable_genre_name || actor.adaptable_genre) && (
                <Badge className="bg-amber-500/15 text-amber-400 text-[8px] h-4 border border-amber-800/40">
                  ~ {actor.adaptable_genre_name || actor.adaptable_genre}
                </Badge>
              )}
            </div>
          </div>
          <div className="flex flex-col gap-1 flex-shrink-0">
            <Button size="sm" variant="ghost" className="h-6 text-[9px] text-gray-400 hover:text-white"
              onClick={() => setExpanded(!expanded)}>
              <ChevronRight className={`w-3 h-3 transition-transform ${expanded ? 'rotate-90' : ''}`} /> Skill
            </Button>
            {onFire && (
              <Button size="sm" variant="ghost" className="h-6 text-[9px] text-red-400 hover:text-red-300 hover:bg-red-500/10"
                onClick={() => onFire(actor.id)} disabled={firing} data-testid={`fire-actor-${actor.id}`}>
                {firing ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
              </Button>
            )}
            {onSendToSchool && (
              <Button size="sm" variant="ghost" className="h-6 text-[9px] text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10"
                onClick={() => onSendToSchool(actor.id)} disabled={sendingToSchool} data-testid={`send-to-school-${actor.id}`}>
                {sendingToSchool ? <RefreshCw className="w-3 h-3 animate-spin" /> : <BookOpen className="w-3 h-3" />}
              </Button>
            )}
            {onRelease && (
              <Button size="sm" variant="ghost" className="h-6 text-[9px] text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                title="Libera (va al Mercato Free Agents)"
                onClick={() => onRelease(actor.id)} disabled={releasing} data-testid={`release-actor-${actor.id}`}>
                {releasing ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Unlock className="w-3 h-3" />}
              </Button>
            )}
          </div>
        </div>

        {expanded && (
          <div className="mt-2 pt-2 border-t border-gray-800 space-y-0.5">
            {Object.entries(skills).map(([name, value]) => (
              <SkillBar key={name} name={name} value={value} cap={actor.skill_caps?.[name]} />
            ))}
            {actor.agency_name && <p className="text-[9px] text-purple-400 mt-1">Agenzia: {actor.agency_name}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RecruitCard({ recruit, onRecruit, recruiting, canRecruit }) {
  const disabled = recruit.already_recruited || recruiting || !canRecruit;
  return (
    <Card className={`border transition-all ${recruit.already_recruited ? 'bg-gray-900/50 border-gray-800 opacity-60' : recruit.is_legendary ? 'bg-yellow-500/5 border-yellow-800/50' : 'bg-[#1A1A1B] border-gray-800 hover:border-cyan-800/50'}`}
      data-testid={`recruit-${recruit.id}`}>
      <CardContent className="p-3">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${recruit.is_legendary ? 'bg-yellow-500/20 text-yellow-400' : 'bg-gray-800 text-gray-400'}`}>
            {recruit.name.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold">{recruit.name}</span>
              <span className={`text-[10px] font-bold ${recruit.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>{recruit.gender === 'female' ? '\u2640' : '\u2642'}</span>
              {recruit.is_legendary && <Badge className="bg-yellow-500/20 text-yellow-400 text-[7px] h-3.5">Leggenda</Badge>}
              <span className="text-[9px] text-gray-500">{recruit.nationality} &bull; {recruit.age} anni</span>
            </div>
            <p className="text-[9px] text-gray-500">Skill base: <span className="text-cyan-400">{recruit.base_skill}</span></p>
            <div className="flex flex-wrap gap-1 mt-0.5">
              {(recruit.strong_genres_names || []).map((g, i) => (
                <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[7px] h-3.5">{g}</Badge>
              ))}
              {recruit.adaptable_genre_name && (
                <Badge className="bg-amber-500/15 text-amber-400 text-[7px] h-3.5">~ {recruit.adaptable_genre_name}</Badge>
              )}
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-[10px] text-yellow-400 font-medium">${(recruit.cost / 1000).toFixed(0)}K</p>
            <Button size="sm" className={`h-6 text-[9px] mt-1 ${disabled ? 'bg-gray-700' : 'bg-cyan-700 hover:bg-cyan-800'}`}
              disabled={disabled} onClick={() => onRecruit(recruit.id)} data-testid={`recruit-btn-${recruit.id}`}>
              {recruit.already_recruited ? 'Reclutato' : recruiting ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Recluta'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SchoolTab({ api, slotsAvailable, actionId, onTransfer, onReload }) {
  const [students, setStudents] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    api.get('/agency/actors-for-casting').then(r => {
      setStudents(r.data.school_students || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [api]);

  if (loading) return <div className="text-center py-8 text-gray-500"><RefreshCw className="w-5 h-5 animate-spin mx-auto" /></div>;

  return (
    <div className="space-y-2" data-testid="school-tab">
      <div className="p-2 rounded border border-cyan-800/30 bg-cyan-500/5">
        <p className="text-[10px] text-cyan-300">
          Gli studenti della Scuola di Recitazione possono essere trasferiti nella tua Agenzia come attori permanenti.
          Puoi anche mandare i tuoi attori dell'agenzia alla scuola per migliorare le loro skill (dal tab "I miei Attori").
        </p>
      </div>
      {students.length === 0 ? (
        <div className="text-center py-10 text-gray-500">
          <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-30" />
          <p className="text-sm">Nessuno studente nella scuola.</p>
          <p className="text-xs text-gray-600 mt-1">Manda un attore alla scuola o iscrivi nuove reclute dalla Scuola di Recitazione.</p>
        </div>
      ) : (
        students.map(student => {
          const skills = student.skills || {};
          const avgSkill = Object.values(skills).length > 0
            ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;
          return (
            <Card key={student.id} className="bg-[#1A1A1B] border-cyan-800/30" data-testid={`school-student-${student.id}`}>
              <CardContent className="p-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-cyan-500/20 flex items-center justify-center text-sm font-bold text-cyan-400">
                    {student.name?.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-semibold">{student.name}</span>
                      <Badge className="text-[7px] bg-cyan-500/15 text-cyan-400 h-3.5">Studente</Badge>
                      {student.status === 'max_potential' && <Badge className="text-[7px] bg-emerald-500/15 text-emerald-400 h-3.5">Potenziale Massimo</Badge>}
                      {student.from_agency && <Badge className="text-[7px] bg-purple-500/15 text-purple-400 h-3.5">Ex Agenzia</Badge>}
                    </div>
                    <p className="text-[10px] text-gray-500">
                      Skill media: <span className={avgSkill >= 70 ? 'text-emerald-400' : avgSkill >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>
                      {student.nationality && <> &bull; {student.nationality}</>}
                    </p>
                    <div className="flex flex-wrap gap-0.5 mt-0.5">
                      {(student.strong_genres_names || []).map((g, i) => <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                      {student.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[6px] h-3">~ {student.adaptable_genre_name}</Badge>}
                    </div>
                  </div>
                  <Button size="sm" className="bg-purple-600 hover:bg-purple-700 text-[10px] h-7 px-3"
                    onClick={() => onTransfer(student.id)} disabled={actionId === student.id || slotsAvailable <= 0}
                    data-testid={`transfer-to-agency-${student.id}`}>
                    {actionId === student.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <><Users className="w-3 h-3 mr-1" /> Trasferisci in Agenzia</>}
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })
      )}
    </div>
  );
}


function ScoutTalentsTab({ api, slotsAvailable, onReload }) {
  const [talents, setTalents] = React.useState([]);
  const [scoutLevel, setScoutLevel] = React.useState(0);
  const [loading, setLoading] = React.useState(true);
  const [actionId, setActionId] = React.useState(null);
  const [expandedSkills, setExpandedSkills] = React.useState({});
  const [recruitedCount, setRecruitedCount] = React.useState(0);
  const [totalGenerated, setTotalGenerated] = React.useState(0);

  const load = React.useCallback(() => {
    api.get('/agency/scout-talents').then(r => {
      setTalents(r.data.talents || []);
      setScoutLevel(r.data.scout_level || 0);
      setRecruitedCount(r.data.recruited_count || 0);
      setTotalGenerated(r.data.total_generated || 0);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [api]);

  React.useEffect(() => { load(); }, [load]);

  const recruit = async (talentId) => {
    setActionId(talentId);
    try {
      const res = await api.post(`/agency/recruit-scout-talent/${talentId}`);
      toast.success(res.data.message);
      load(); onReload();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionId(null);
  };

  if (loading) return <div className="text-center py-8"><RefreshCw className="w-5 h-5 animate-spin mx-auto text-gray-500" /></div>;

  return (
    <div className="space-y-2" data-testid="scout-talents-tab">
      <div className="p-2 rounded border border-amber-800/30 bg-amber-500/5">
        <p className="text-[10px] text-amber-300">
          Il tuo Talent Scout (Lv{scoutLevel}) trova giovani talenti con potenziale nascosto! Vengono rinnovati ogni settimana.
          {scoutLevel >= 4 && ' Include anche Diamanti Grezzi con potenziale massimo!'}
        </p>
      </div>
      {talents.length === 0 ? (
        <div className="text-center py-10 text-gray-500">
          {recruitedCount > 0 ? (
            <>
              <UserPlus className="w-8 h-8 mx-auto mb-2 text-emerald-500/50" />
              <p className="text-sm text-emerald-400">Hai reclutato tutti i {recruitedCount} talenti di questa settimana!</p>
              <p className="text-xs text-gray-500 mt-1">Sono ora nella tab "I miei Attori". Nuovi talenti la prossima settimana.</p>
            </>
          ) : (
            <>
              <Search className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Lo scout sta cercando nuovi talenti... Torna presto!</p>
            </>
          )}
        </div>
      ) : (
        talents.map(talent => {
          const skills = talent.skills || {};
          const avgSkill = Object.values(skills).length > 0 ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length) : 0;
          const maxCap = Math.max(...Object.values(talent.skill_caps || {}), 0);
          const skillsOpen = expandedSkills[talent.id];
          return (
            <Card key={talent.id} className={`${talent.is_diamond ? 'bg-[#1a1a0e] border-yellow-500/30' : 'bg-[#1A1A1B] border-amber-800/30'}`} data-testid={`scout-talent-${talent.id}`}>
              <CardContent className="p-3">
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${talent.is_diamond ? 'bg-yellow-500/30 text-yellow-400' : 'bg-amber-500/20 text-amber-400'}`}>
                    {talent.is_diamond ? <Diamond className="w-4 h-4" /> : talent.name?.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-semibold">{talent.name}</span>
                      <span className={`text-[10px] font-bold ${talent.gender === 'female' ? 'text-pink-400' : 'text-cyan-400'}`}>{talent.gender === 'female' ? '\u2640' : '\u2642'}</span>
                      {talent.is_diamond && <Badge className="text-[7px] bg-yellow-500/20 text-yellow-400 h-3.5 animate-pulse">Diamante Grezzo</Badge>}
                      <Badge className="text-[7px] bg-amber-500/15 text-amber-400 h-3.5">{talent.age}a</Badge>
                    </div>
                    <p className="text-[9px] text-gray-500">
                      {talent.nationality}{' \u2022 '}Skill: <span className={avgSkill >= 40 ? 'text-cyan-400' : 'text-amber-400'}>{avgSkill}</span>{' \u2022 '}Cap max: <span className="text-emerald-400">{maxCap}</span>{' \u2022 '}Talento: <span className="text-purple-400">{Math.round(talent.hidden_talent * 100)}%</span>
                    </p>
                    <div className="flex flex-wrap gap-0.5 mt-0.5">
                      {(talent.strong_genres_names || []).map((g, i) => <Badge key={i} className="bg-emerald-500/15 text-emerald-400 text-[6px] h-3">{g}</Badge>)}
                      {talent.adaptable_genre_name && <Badge className="bg-amber-500/15 text-amber-400 text-[6px] h-3">~ {talent.adaptable_genre_name}</Badge>}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className="text-[10px] text-yellow-400 font-bold">${talent.cost?.toLocaleString()}</span>
                    <Button size="sm" className={`h-7 px-3 text-[10px] ${talent.is_diamond ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-amber-600 hover:bg-amber-700'}`}
                      onClick={() => recruit(talent.id)} disabled={actionId === talent.id || slotsAvailable <= 0}
                      data-testid={`recruit-talent-${talent.id}`}>
                      {actionId === talent.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Recluta'}
                    </Button>
                  </div>
                </div>
                {/* Skill toggle */}
                {Object.keys(skills).length > 0 && (
                  <div className="mt-1">
                    <button className="text-[8px] text-amber-400 hover:text-amber-300 flex items-center gap-0.5"
                      onClick={() => setExpandedSkills(p => ({...p, [talent.id]: !p[talent.id]}))}>
                      {skillsOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      {skillsOpen ? 'Nascondi Skill' : 'Mostra Skill'}
                    </button>
                    {skillsOpen && (
                      <div className="grid grid-cols-3 gap-x-3 gap-y-0.5 mt-1 px-1">
                        {Object.entries(skills).sort(([,a],[,b]) => b - a).map(([k, v]) => (
                          <div key={k} className="flex items-center gap-1">
                            <span className="text-[8px] text-gray-500 capitalize w-16 truncate">{k.replace(/_/g, ' ')}</span>
                            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden relative">
                              <div className={`h-full rounded-full ${v >= 60 ? 'bg-emerald-500' : v >= 40 ? 'bg-cyan-500' : 'bg-amber-500'}`} style={{width: `${v}%`}} />
                              <div className="absolute top-0 h-full border-r border-dashed border-purple-400/50" style={{left: `${talent.skill_caps?.[k] || 100}%`}} />
                            </div>
                            <span className="text-[8px] text-gray-400 w-5 text-right">{v}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })
      )}
    </div>
  );
}

function ScoutScreenplaysTab({ api }) {
  const navigate = useNavigate();
  const [screenplays, setScreenplays] = React.useState([]);
  const [myScreenplays, setMyScreenplays] = React.useState([]);
  const [scoutLevel, setScoutLevel] = React.useState(0);
  const [loading, setLoading] = React.useState(true);
  const [actionId, setActionId] = React.useState(null);
  const [purchasedCount, setPurchasedCount] = React.useState(0);
  const [pendingSp, setPendingSp] = React.useState(null);   // screenplay awaiting mode choice
  const [modeLoading, setModeLoading] = React.useState(false);

  const load = React.useCallback(() => {
    Promise.all([
      api.get('/agency/scout-screenplays'),
      api.get('/agency/my-screenplays')
    ]).then(([scout, mine]) => {
      setScreenplays(scout.data.screenplays || []);
      setScoutLevel(scout.data.scout_level || 0);
      setMyScreenplays(mine.data.screenplays || []);
      setPurchasedCount((mine.data.screenplays?.length || 0) + (mine.data.used_count || 0));
    }).catch(() => {}).finally(() => setLoading(false));
  }, [api]);

  React.useEffect(() => { load(); }, [load]);

  const openPurchaseModal = (sp) => { setPendingSp(sp); };

  const confirmMode = async (mode) => {
    if (!pendingSp) return;
    setModeLoading(true);
    try {
      const res = await api.post('/purchased-screenplays/create-v3-project', {
        screenplay_id: pendingSp.id,
        source: 'agency',
        mode,
      });
      toast.success(res.data.message);
      setPendingSp(null);
      // Cinematic curtain reveal
      try {
        window.dispatchEvent(new CustomEvent('cineworld:curtain-reveal', {
          detail: {
            title: res.data.project?.title || pendingSp.title,
            subtitle: mode === 'veloce' ? 'Scout Agenzia · fast track' : 'Scout Agenzia · pipeline guidata',
          },
        }));
      } catch {}
      const pid = res.data.project_id;
      setTimeout(() => { if (pid) navigate(`/create-film?p=${pid}`); }, 2400);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setModeLoading(false);
    }
  };

  if (loading) return <div className="text-center py-8"><RefreshCw className="w-5 h-5 animate-spin mx-auto text-gray-500" /></div>;

  return (
    <div className="space-y-2" data-testid="scout-screenplays-tab">
      <div className="p-2 rounded border border-emerald-800/30 bg-emerald-500/5">
        <p className="text-[10px] text-emerald-300">
          Il tuo Talent Scout Sceneggiatori (Lv{scoutLevel}) trova sceneggiature pronte da usare nei tuoi film! Rinnovate settimanalmente.
          {scoutLevel >= 3 && ' Include anche sceneggiature di autori famosi!'}
        </p>
      </div>
      {screenplays.length === 0 ? (
        <div className="text-center py-10 text-gray-500">
          <Pen className="w-8 h-8 mx-auto mb-2 opacity-30" />
          <p className="text-sm">Nessuna sceneggiatura disponibile questa settimana.</p>
        </div>
      ) : (
        screenplays.map(sp => (
          <Card key={sp.id} className={`${sp.is_famous_writer ? 'bg-[#1a1a0e] border-yellow-500/20' : 'bg-[#1A1A1B] border-emerald-800/30'}`} data-testid={`scout-screenplay-${sp.id}`}>
            <CardContent className="p-3">
              <div className="flex items-center gap-3">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${sp.is_famous_writer ? 'bg-yellow-500/20 text-yellow-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                  <Pen className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-semibold">{sp.title}</span>
                    {sp.is_famous_writer && <Badge className="text-[7px] bg-yellow-500/20 text-yellow-400 h-3.5">Autore Famoso</Badge>}
                  </div>
                  <p className="text-[9px] text-gray-500">
                    di {sp.writer_name}{' \u2022 '}{sp.genre_name}{' \u2022 '}Qualita: <span className={sp.quality >= 70 ? 'text-emerald-400' : sp.quality >= 50 ? 'text-cyan-400' : 'text-amber-400'}>{sp.quality}/100</span>
                  </p>
                  <p className="text-[9px] text-gray-600 mt-0.5 line-clamp-1">{sp.synopsis}</p>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span className="text-[10px] text-yellow-400 font-bold">${sp.cost?.toLocaleString()}</span>
                  <Button size="sm" className="h-7 px-3 text-[10px] bg-emerald-600 hover:bg-emerald-700"
                    onClick={() => openPurchaseModal(sp)} disabled={actionId === sp.id}
                    data-testid={`buy-screenplay-${sp.id}`}>
                    {actionId === sp.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Acquista'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))
      )}

      {/* My purchased screenplays */}
      {myScreenplays.length > 0 && (
        <div className="mt-4 space-y-2">
          <h3 className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5" /> Le Mie Sceneggiature ({myScreenplays.length} disponibili)
          </h3>
          <p className="text-[9px] text-gray-500">Usa queste sceneggiature quando crei un nuovo film in "Produci Film".</p>
          {myScreenplays.map(sp => (
            <Card key={sp.id} className="bg-[#1A1A1B] border-emerald-800/20" data-testid={`my-screenplay-${sp.id}`}>
              <CardContent className="p-2.5">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-emerald-500/15 flex items-center justify-center">
                    <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-semibold">{sp.title}</span>
                    <p className="text-[9px] text-gray-500">
                      di {sp.writer_name} {'\u2022'} {sp.genre_name} {'\u2022'} Qualita: <span className="text-emerald-400">{sp.quality}/100</span>
                    </p>
                  </div>
                  <Badge className="text-[8px] bg-emerald-500/15 text-emerald-400 h-4">Pronta</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Purchase Mode Modal — Avanzata / Veloce */}
      {pendingSp && (() => {
        const baseRaw = pendingSp.cost || 0;
        // Agency discount: 60% off base. Veloce multiplies by 2.
        const avanzataCost = Math.max(1000, Math.round(baseRaw * 0.4));
        const velociCost = Math.max(1000, Math.round(baseRaw * 2 * 0.4));
        return (
          <div className="fixed inset-0 bg-black/70 z-[70] flex items-center justify-center p-3" onClick={() => !modeLoading && setPendingSp(null)}>
            <div className="bg-[#111113] border border-white/10 rounded-xl max-w-md w-full p-4 space-y-3" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-sm font-bold text-white">{pendingSp.title}</div>
                  <div className="text-[10px] text-gray-400">di {pendingSp.writer_name} — Qualità {pendingSp.quality}/100</div>
                </div>
                <Badge className="text-[8px] bg-emerald-500/20 text-emerald-300 h-4">Sconto Agenzia -60%</Badge>
              </div>
              <p className="text-[10px] text-gray-500">Scegli come produrre il film da questa sceneggiatura.</p>

              <button
                onClick={() => confirmMode('avanzata')}
                disabled={modeLoading}
                className="w-full bg-emerald-500/5 hover:bg-emerald-500/10 border border-emerald-500/30 hover:border-emerald-500/60 rounded-lg p-3 text-left transition-all disabled:opacity-40"
                data-testid="agency-mode-avanzata">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Clapperboard className="w-4 h-4 text-emerald-400" />
                    <div>
                      <div className="font-bold text-xs">Avanzata</div>
                      <div className="text-[9px] text-white/50">Pipeline guidata, XP piena</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-emerald-400 text-xs">${avanzataCost.toLocaleString()}</div>
                    <ArrowRight className="w-3 h-3 text-white/30 ml-auto" />
                  </div>
                </div>
              </button>

              <button
                onClick={() => confirmMode('veloce')}
                disabled={modeLoading}
                className="w-full bg-orange-500/5 hover:bg-orange-500/10 border border-orange-500/30 hover:border-orange-500/60 rounded-lg p-3 text-left transition-all disabled:opacity-40"
                data-testid="agency-mode-veloce">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-orange-400" />
                    <div>
                      <div className="font-bold text-xs">Veloce</div>
                      <div className="text-[9px] text-white/50">Solo locandina + trailer. -50% XP</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-orange-400 text-xs">${velociCost.toLocaleString()}</div>
                    <ArrowRight className="w-3 h-3 text-white/30 ml-auto" />
                  </div>
                </div>
              </button>

              <Button size="sm" variant="ghost" className="w-full text-[10px]" onClick={() => setPendingSp(null)} disabled={modeLoading}>
                Annulla
              </Button>
            </div>
          </div>
        );
      })()}
    </div>
  );
}


function ExclusiveContractsTab({ api }) {
  const [agencies, setAgencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);
  const [contractInfo, setContractInfo] = useState({ active_contracts: 0, max_contracts: 2, slots_available: 2 });
  const gameConfirm = useConfirm();

  const load = useCallback(async () => {
    try {
      const res = await api.get('/pipeline-v3/exclusive-contracts');
      setAgencies(res.data.agencies || []);
      setContractInfo(res.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [api]);

  useEffect(() => { load(); }, [load]);

  const sign = async (agencyId, agencyName, costCp) => {
    if (!await gameConfirm({
      title: `Contratto Esclusivo: ${agencyName}`,
      subtitle: `Costa ${costCp} CinePass. Durata 30 giorni. Cast 4+ stelle, triplo proposte, -20% costi, 1 attore esclusivo.`,
      confirmLabel: `Firma (${costCp} CP)`
    })) return;
    setActionId(agencyId);
    try {
      const res = await api.post('/pipeline-v3/sign-exclusive-contract', { agency_id: agencyId });
      toast.success(res.data.message);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionId(null);
  };

  if (loading) return <div className="text-center py-8 text-gray-500"><RefreshCw className="w-5 h-5 animate-spin mx-auto mb-1" /><p className="text-xs">Caricamento agenzie...</p></div>;

  const activeContracts = agencies.filter(a => a.contract?.is_active);
  const available = agencies.filter(a => !a.contract?.is_active);

  return (
    <div className="space-y-3" data-testid="contracts-tab">
      {/* Status */}
      <div className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-amber-500/5 border border-amber-500/15">
        <p className="text-[9px] text-amber-400 font-bold">Attivi: {contractInfo.active_contracts}/{contractInfo.max_contracts}</p>
        <p className="text-[8px] text-gray-500">{contractInfo.slots_available} slot liberi</p>
      </div>

      {/* Active Contracts */}
      {activeContracts.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[8px] text-amber-400 uppercase font-bold">Contratti Attivi</p>
          {activeContracts.map(ag => {
            const exp = ag.contract?.expires_at ? new Date(ag.contract.expires_at) : null;
            const daysLeft = exp ? Math.max(0, Math.ceil((exp - new Date()) / 86400000)) : 0;
            return (
              <Card key={ag.id} className="bg-amber-500/5 border-amber-500/20">
                <CardContent className="p-2.5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-bold text-amber-300 flex items-center gap-1">
                        <FileSignature className="w-3 h-3" /> {ag.name}
                      </p>
                      <p className="text-[9px] text-gray-400">{ag.region} | Rep {ag.reputation} | {(ag.specialization || []).join(', ')}</p>
                    </div>
                    <Badge className="bg-amber-500/20 text-amber-400 text-[8px]">{daysLeft}g rimasti</Badge>
                  </div>
                  <div className="grid grid-cols-4 gap-1 mt-2 text-[8px]">
                    <div className="p-1 rounded bg-black/30 border border-amber-800/30 text-center">
                      <p className="text-gray-500">Stelle</p>
                      <p className="text-amber-400 font-bold">4+</p>
                    </div>
                    <div className="p-1 rounded bg-black/30 border border-amber-800/30 text-center">
                      <p className="text-gray-500">Proposte</p>
                      <p className="text-amber-400 font-bold">x3</p>
                    </div>
                    <div className="p-1 rounded bg-black/30 border border-amber-800/30 text-center">
                      <p className="text-gray-500">Sconto</p>
                      <p className="text-emerald-400 font-bold">-20%</p>
                    </div>
                    <div className="p-1 rounded bg-black/30 border border-amber-800/30 text-center">
                      <p className="text-gray-500">Esclusivo</p>
                      <p className="text-yellow-400 font-bold">{ag.contract?.exclusive_actor?.name?.split(' ')[0] || 'Si'}</p>
                    </div>
                  </div>
                  {ag.contract?.exclusive_actor && (
                    <div className="mt-1.5 flex items-center gap-2 px-2 py-1 rounded bg-yellow-500/5 border border-yellow-500/15">
                      <Diamond className="w-3 h-3 text-yellow-400 shrink-0" />
                      <div>
                        <p className="text-[9px] font-bold text-yellow-300">Attore Esclusivo: {ag.contract.exclusive_actor.name}</p>
                        <p className="text-[7px] text-gray-500">{ag.contract.exclusive_actor.nationality} | CRc {ag.contract.exclusive_actor.crc} | {ag.contract.exclusive_actor.fame_category}</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Available Agencies */}
      <p className="text-[8px] text-gray-500 uppercase font-bold">Agenzie Disponibili ({available.length})</p>
      <div className="space-y-1 max-h-64 overflow-y-auto">
        {available.map(ag => (
          <div key={ag.id} className={`flex flex-col gap-1.5 p-2 rounded-lg border ${
            ag.is_preferred ? 'bg-emerald-500/5 border-emerald-500/15' : 'bg-[#1A1A1B] border-gray-800 hover:border-amber-800/40'
          }`}>
            <div className="flex items-center gap-1.5 min-w-0">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1 flex-wrap">
                  <span className="text-[9px] font-bold text-white truncate">{ag.name}</span>
                  {ag.is_preferred && <Unlock className="w-2.5 h-2.5 text-emerald-400 shrink-0" />}
                </div>
                <p className="text-[7px] text-gray-500 truncate">{ag.region} | Rep {ag.reputation} | {(ag.specialization || []).slice(0, 2).join(', ')}</p>
              </div>
              <Button size="sm" variant="outline" disabled={contractInfo.slots_available <= 0 || actionId === ag.id}
                className="text-[7px] h-6 px-2 border-amber-700/50 text-amber-400 hover:bg-amber-500/10 shrink-0 whitespace-nowrap"
                onClick={() => sign(ag.id, ag.name, ag.cost_cp)}
                data-testid={`sign-contract-${ag.id}`}>
                {actionId === ag.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <>{ag.cost_cp} CP</>}
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="text-[8px] text-gray-600 space-y-0.5 px-1">
        <p>Contratto Esclusivo: cast 4+ stelle, x3 proposte, -20% costi, 1 attore esclusivo/mese.</p>
        <p>Costo: 10-25 CinePass in base alla reputazione. Durata: 30 giorni. Max 2 contratti attivi.</p>
      </div>
    </div>
  );
}



export default function CastingAgencyPage() {
  const { api } = useContext(AuthContext);
  const gameConfirm = useConfirm();
  const [tab, setTab] = useState('actors');
  const [info, setInfo] = useState(null);
  const [actors, setActors] = useState([]);
  const [recruits, setRecruits] = useState([]);
  const [recruitsInfo, setRecruitsInfo] = useState({});
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);
  const [showFreeAgents, setShowFreeAgents] = useState(false);

  const releaseActor = async (actorId) => {
    const actor = actors.find(a => a.id === actorId);
    if (!await gameConfirm({ title: `Liberare ${actor?.name}?`, subtitle: 'Lo metti nel Mercato Free Agents. Altri produttori potranno ingaggiarlo.', confirmLabel: 'Libera' })) return;
    setActionId(actorId);
    try {
      await api.post(`/agency/release-actor/${actorId}`);
      toast.success(`${actor?.name} è stato liberato`);
      loadInfo(); loadActors();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionId(null); }
  };

  const loadInfo = useCallback(async () => {
    try {
      const res = await api.get('/agency/info');
      setInfo(res.data);
    } catch (e) {
      if (e.response?.status === 404) {
        setInfo({ error: true, message: e.response.data.detail });
      }
    }
  }, [api]);

  const loadActors = useCallback(async () => {
    try {
      const res = await api.get('/agency/actors');
      setActors(res.data.actors || []);
    } catch (e) { console.error(e); }
  }, [api]);

  const loadRecruits = useCallback(async () => {
    try {
      const res = await api.get('/agency/recruits');
      setRecruits(res.data.recruits || []);
      setRecruitsInfo(res.data);
    } catch (e) { console.error(e); }
  }, [api]);

  useEffect(() => {
    Promise.all([loadInfo(), loadActors(), loadRecruits()]).finally(() => setLoading(false));
  }, [loadInfo, loadActors, loadRecruits]);

  const recruit = async (recruitId) => {
    setActionId(recruitId);
    try {
      const res = await api.post('/agency/recruit', { recruit_id: recruitId });
      toast.success(res.data.message);
      loadInfo(); loadActors(); loadRecruits();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionId(null); }
  };

  const fire = async (actorId) => {
    if (!await gameConfirm({ title: 'Licenziare questo attore?', subtitle: 'Diventerà disponibile per tutti i produttori.', confirmLabel: 'Licenzia' })) return;
    setActionId(actorId);
    try {
      const res = await api.post(`/agency/fire/${actorId}`);
      toast.success(res.data.message);
      loadInfo(); loadActors();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionId(null); }
  };

  const sendToSchool = async (actorId) => {
    const actor = actors.find(a => a.id === actorId);
    const costMap = {2: 50000, 3: 100000, 4: 200000, 5: 400000};
    const cost = costMap[actor?.stars || 2] || 50000;
    if (!await gameConfirm({ title: `Manda ${actor?.name} a Scuola?`, subtitle: `Costo iscrizione: $${cost.toLocaleString()}\nInclude 30 giorni di training.`, confirmLabel: 'Iscrivimi' })) return;
    setActionId(actorId);
    try {
      const res = await api.post(`/agency/send-to-school/${actorId}`);
      toast.success(res.data.message);
      loadInfo(); loadActors();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionId(null); }
  };

  const transferFromSchool = async (studentId) => {
    if (!await gameConfirm({ title: 'Trasferire in Agenzia?', subtitle: 'Lo studente diventerà un attore permanente della tua Agenzia.', confirmLabel: 'Trasferisci' })) return;
    setActionId(studentId);
    try {
      const res = await api.post(`/agency/transfer-from-school/${studentId}`);
      toast.success(res.data.message);
      loadInfo(); loadActors();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionId(null); }
  };

  if (loading) return <div className="text-center py-12 text-gray-500"><RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" /><p>Caricamento agenzia...</p></div>;

  if (info?.error) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <Briefcase className="w-12 h-12 mx-auto mb-3 text-gray-600" />
        <h2 className="text-lg font-semibold mb-2">Agenzia di Casting</h2>
        <p className="text-sm text-gray-400 mb-4">{info.message}</p>
        <Button onClick={() => window.location.href = '/infrastructure'} className="bg-purple-700 hover:bg-purple-800">
          Vai alle Infrastrutture
        </Button>
      </div>
    );
  }

  const slotsAvailable = info?.slots_available || 0;

  return (
    <div className="max-w-4xl mx-auto space-y-4" data-testid="casting-agency-page">
      {/* Agency Header */}
      <div className="relative overflow-hidden rounded-lg border border-purple-800/40 bg-gradient-to-r from-purple-900/20 to-[#1A1A1B] p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-purple-300">{info?.agency_name || 'La tua Agenzia'}</h1>
            <p className="text-xs text-gray-400 mt-0.5">Livello {info?.level || 1} &bull; Attori: {info?.current_actors || 0}/{info?.max_actors || 12} &bull; Studenti: {info?.school_students || 0}{info?.school_level > 0 ? ` (Scuola Lv${info.school_level})` : ''}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-purple-500/20 text-purple-400 text-xs px-3 py-1">
              {slotsAvailable} slot disponibili
            </Badge>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        <Button size="sm" variant={tab === 'actors' ? 'default' : 'outline'}
          className={tab === 'actors' ? 'bg-purple-700 hover:bg-purple-800' : 'border-gray-700'}
          onClick={() => setTab('actors')} data-testid="tab-actors">
          <Users className="w-3.5 h-3.5 mr-1" /> I miei Attori ({actors.length})
        </Button>
        <Button size="sm" variant={tab === 'recruits' ? 'default' : 'outline'}
          className={tab === 'recruits' ? 'bg-cyan-700 hover:bg-cyan-800' : 'border-gray-700'}
          onClick={() => setTab('recruits')} data-testid="tab-recruits">
          <Star className="w-3.5 h-3.5 mr-1" /> Reclute Settimanali ({recruits.filter(r => !r.already_recruited).length})
        </Button>
        <Button size="sm" variant={tab === 'school' ? 'default' : 'outline'}
          className={tab === 'school' ? 'bg-cyan-700 hover:bg-cyan-800' : 'border-gray-700'}
          onClick={() => setTab('school')} data-testid="tab-school">
          <BookOpen className="w-3.5 h-3.5 mr-1" /> Scuola {info?.school_level > 0 ? `(Lv${info.school_level})` : ''} ({info?.school_students || 0})
        </Button>
        {info?.talent_scout_actors > 0 && (
          <Button size="sm" variant={tab === 'scout-actors' ? 'default' : 'outline'}
            className={tab === 'scout-actors' ? 'bg-amber-700 hover:bg-amber-800' : 'border-gray-700'}
            onClick={() => setTab('scout-actors')} data-testid="tab-scout-actors">
            <Search className="w-3.5 h-3.5 mr-1" /> Scout Talenti (Lv{info.talent_scout_actors})
          </Button>
        )}
        {info?.talent_scout_screenwriters > 0 && (
          <Button size="sm" variant={tab === 'scout-screenplays' ? 'default' : 'outline'}
            className={tab === 'scout-screenplays' ? 'bg-emerald-700 hover:bg-emerald-800' : 'border-gray-700'}
            onClick={() => setTab('scout-screenplays')} data-testid="tab-scout-screenplays">
            <Pen className="w-3.5 h-3.5 mr-1" /> Scout Sceneggiature (Lv{info.talent_scout_screenwriters})
          </Button>
        )}
        <Button size="sm" variant={tab === 'contracts' ? 'default' : 'outline'}
          className={tab === 'contracts' ? 'bg-amber-700 hover:bg-amber-800' : 'border-gray-700'}
          onClick={() => setTab('contracts')} data-testid="tab-contracts">
          <FileSignature className="w-3.5 h-3.5 mr-1" /> Contratti Agenzie
        </Button>
      </div>

      {/* Actors Tab */}
      {tab === 'actors' && (
        <div className="space-y-2">
          {/* Free Agents Market entry */}
          <Button onClick={() => setShowFreeAgents(true)} data-testid="open-free-agents-market"
                  className="w-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 text-amber-200 hover:from-amber-500/30 hover:to-orange-500/30 h-9">
            <Users className="w-4 h-4 mr-2" />
            Mercato Attori Liberi
            <ChevronRight className="w-3 h-3 ml-1" />
          </Button>
          {/* Talent Market — Sistema Pre-Ingaggio (Talenti Vivente) */}
          <Button onClick={() => setShowTalentMarket(true)} data-testid="open-talent-market"
                  className="w-full bg-gradient-to-r from-yellow-500/20 to-amber-500/20 border border-yellow-500/30 text-yellow-200 hover:from-yellow-500/30 hover:to-amber-500/30 h-9">
            <Sparkles className="w-4 h-4 mr-2" />
            Mercato Talenti (Pre-ingaggio)
            <ChevronRight className="w-3 h-3 ml-1" />
          </Button>
          {actors.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              <Users className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Nessun attore nella tua agenzia.</p>
              <p className="text-xs text-gray-600 mt-1">Vai alla tab "Reclute Settimanali" per ingaggiare i primi attori!</p>
            </div>
          ) : (
            actors.map(actor => (
              <ActorCard key={actor.id} actor={actor} onFire={fire} onSendToSchool={sendToSchool}
                onRelease={releaseActor} releasing={actionId === actor.id}
                firing={actionId === actor.id} sendingToSchool={actionId === actor.id} />
            ))
          )}
        </div>
      )}

      {/* Recruits Tab */}
      {tab === 'recruits' && (
        <div className="space-y-2">
          <div className="p-2 rounded border border-cyan-800/30 bg-cyan-500/5">
            <p className="text-[10px] text-cyan-300">
              Nuove reclute ogni settimana. Puoi reclutarne fino a {slotsAvailable} (slot disponibili). Le reclute non scelte scompariranno a fine settimana.
            </p>
          </div>
          {recruits.length === 0 ? (
            <p className="text-center text-sm text-gray-500 py-8">Nessuna recluta disponibile.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {recruits.map(r => (
                <RecruitCard key={r.id} recruit={r} onRecruit={recruit}
                  recruiting={actionId === r.id} canRecruit={slotsAvailable > 0} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* School Tab - Transfer students to Agency */}
      {tab === 'school' && (
        <SchoolTab api={api} slotsAvailable={slotsAvailable} actionId={actionId}
          onTransfer={transferFromSchool} onReload={() => { loadInfo(); loadActors(); }} />
      )}

      {/* Scout Talents Tab */}
      {tab === 'scout-actors' && (
        <ScoutTalentsTab api={api} slotsAvailable={slotsAvailable} onReload={() => { loadInfo(); loadActors(); }} />
      )}

      {/* Scout Screenplays Tab */}
      {tab === 'scout-screenplays' && (
        <ScoutScreenplaysTab api={api} />
      )}

      {/* Exclusive Contracts Tab */}
      {tab === 'contracts' && (
        <ExclusiveContractsTab api={api} />
      )}

      {/* Bonus info */}
      <Card className="bg-[#1A1A1B] border-gray-800">
        <CardContent className="p-3">
          <h3 className="text-xs font-semibold text-amber-400 mb-1.5 flex items-center gap-1"><Award className="w-3.5 h-3.5" /> Bonus Attori Agenzia</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px]">
            <div className="p-1.5 rounded bg-black/30 border border-gray-800">
              <p className="text-gray-400">1 attore</p>
              <p className="text-emerald-400 font-semibold">+25% XP/Fama</p>
            </div>
            <div className="p-1.5 rounded bg-black/30 border border-gray-800">
              <p className="text-gray-400">2 attori</p>
              <p className="text-emerald-400 font-semibold">+35% XP/Fama</p>
            </div>
            <div className="p-1.5 rounded bg-black/30 border border-gray-800">
              <p className="text-gray-400">3 attori</p>
              <p className="text-cyan-400 font-semibold">+50% XP/Fama</p>
            </div>
            <div className="p-1.5 rounded bg-black/30 border border-gray-800">
              <p className="text-gray-400">4+ attori</p>
              <p className="text-yellow-400 font-semibold">+70% XP/Fama</p>
            </div>
          </div>
          <p className="text-[9px] text-gray-500 mt-1.5">Gli attori migliorano gradualmente dopo ogni film. Crescita basata su qualità del film e talento nascosto.</p>
        </CardContent>
      </Card>

      <FreeAgentsMarketModal
        open={showFreeAgents}
        onClose={() => setShowFreeAgents(false)}
        onSigned={() => { loadActors(); loadInfo(); }}
      />
      <TalentMarketModal
        open={showTalentMarket}
        onClose={() => setShowTalentMarket(false)}
      />
    </div>
  );
}
