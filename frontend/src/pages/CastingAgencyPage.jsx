import React, { useState, useEffect, useCallback, useContext } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Users, Star, Briefcase, Trash2, RefreshCw, ChevronRight, BookOpen, Award, Shield, Swords, Heart, Sparkles } from 'lucide-react';
import { AuthContext } from '../contexts';

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

function ActorCard({ actor, onFire, onSendToSchool, firing, sendingToSchool }) {
  const [expanded, setExpanded] = useState(false);
  const skills = actor.skills || {};
  const avgSkill = Object.values(skills).length > 0
    ? Math.round(Object.values(skills).reduce((a, b) => a + b, 0) / Object.values(skills).length)
    : 0;

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

export default function CastingAgencyPage() {
  const { api } = useContext(AuthContext);
  const [tab, setTab] = useState('actors');
  const [info, setInfo] = useState(null);
  const [actors, setActors] = useState([]);
  const [recruits, setRecruits] = useState([]);
  const [recruitsInfo, setRecruitsInfo] = useState({});
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);

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
    if (!window.confirm('Vuoi davvero licenziare questo attore? Diventerà disponibile per tutti.')) return;
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
    if (!window.confirm(`Manda ${actor?.name} alla Scuola di Recitazione?\nCosto iscrizione: $${cost.toLocaleString()}\nInclude 30 giorni di training.`)) return;
    setActionId(actorId);
    try {
      const res = await api.post(`/agency/send-to-school/${actorId}`);
      toast.success(res.data.message);
      loadInfo(); loadActors();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionId(null); }
  };

  const transferFromSchool = async (studentId) => {
    if (!window.confirm('Trasferire questo studente nella tua Agenzia come attore permanente?')) return;
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
            <p className="text-xs text-gray-400 mt-0.5">Livello {info?.level || 1} &bull; Attori: {info?.current_actors || 0}/{info?.max_actors || 12} &bull; Studenti: {info?.school_students || 0}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-purple-500/20 text-purple-400 text-xs px-3 py-1">
              {slotsAvailable} slot disponibili
            </Badge>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
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
          <BookOpen className="w-3.5 h-3.5 mr-1" /> Scuola ({info?.school_students || 0})
        </Button>
      </div>

      {/* Actors Tab */}
      {tab === 'actors' && (
        <div className="space-y-2">
          {actors.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              <Users className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Nessun attore nella tua agenzia.</p>
              <p className="text-xs text-gray-600 mt-1">Vai alla tab "Reclute Settimanali" per ingaggiare i primi attori!</p>
            </div>
          ) : (
            actors.map(actor => (
              <ActorCard key={actor.id} actor={actor} onFire={fire} onSendToSchool={sendToSchool}
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
    </div>
  );
}
