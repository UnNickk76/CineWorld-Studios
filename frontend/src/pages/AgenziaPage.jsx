import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, GraduationCap, Search, BookOpen, Star, Clock, Sparkles,
  X, DollarSign, AlertTriangle, Lock, Unlock, ArrowUpCircle, Ticket, ChevronRight
} from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';

const TABS = [
  { id: 'attori', label: 'Attori', icon: Users, color: 'cyan' },
  { id: 'scuola', label: 'Scuola', icon: GraduationCap, color: 'green' },
  { id: 'scout', label: 'Scout', icon: Search, color: 'purple' },
  { id: 'sceneggiature', label: 'Sceneggiature', icon: BookOpen, color: 'yellow' },
];

export default function AgenziaPage() {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('attori');
  const [loading, setLoading] = useState(true);
  const [ownedInfra, setOwnedInfra] = useState([]);
  // School
  const [schoolStatus, setSchoolStatus] = useState(null);
  const [schoolRecruits, setSchoolRecruits] = useState([]);
  const [castingStudents, setCastingStudents] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  // Actors
  const [actors, setActors] = useState([]);

  useEffect(() => {
    loadAll();
  }, [api]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [infraRes, schoolRes, recruitsRes, castingRes, actorsRes] = await Promise.all([
        api.get('/infrastructure/my'),
        api.get('/acting-school/status').catch(() => ({ data: null })),
        api.get('/acting-school/recruits').catch(() => ({ data: { recruits: [] } })),
        api.get('/acting-school/casting-students').catch(() => ({ data: null })),
        api.get('/casting-agency/my-actors').catch(() => ({ data: [] })),
      ]);
      const agenziaTypes = ['cinema_school', 'talent_scout_actors', 'talent_scout_screenwriters'];
      setOwnedInfra((infraRes.data.infrastructure || []).filter(i => agenziaTypes.includes(i.type)));
      setSchoolStatus(schoolRes.data);
      setSchoolRecruits(recruitsRes.data.recruits || recruitsRes.data || []);
      setCastingStudents(castingRes.data);
      setActors(Array.isArray(actorsRes.data) ? actorsRes.data : actorsRes.data?.actors || []);
    } catch {}
    setLoading(false);
  };

  const schoolAction = async (action, id, extra = {}) => {
    setActionLoading(id || action);
    try {
      let r;
      if (action === 'train') r = await api.post('/acting-school/train', { recruit_id: id });
      else if (action === 'keep') r = await api.post(`/acting-school/complete/${id}`, { action: 'keep' });
      else if (action === 'release') r = await api.post(`/acting-school/complete/${id}`, { action: 'release' });
      else if (action === 'pay') r = await api.post(`/acting-school/pay-training/${id}`);
      else if (action === 'graduate') r = await api.post(`/acting-school/graduate/${id}`);
      else if (action === 'dismiss') r = await api.post(`/acting-school/dismiss/${id}`);
      if (r?.data?.message) toast.success(r.data.message);
      refreshUser();
      await loadAll();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(null);
  };

  const hasSchool = ownedInfra.some(i => i.type === 'cinema_school');
  const hasScoutActors = ownedInfra.some(i => i.type === 'talent_scout_actors');
  const hasScoutWriters = ownedInfra.some(i => i.type === 'talent_scout_screenwriters');

  if (loading) return <div className="pt-20 text-center text-gray-500">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 max-w-2xl mx-auto px-3" data-testid="agenzia-page">
      <div className="mb-4">
        <h1 className="font-['Bebas_Neue'] text-2xl tracking-wide">Agenzia</h1>
        <p className="text-xs text-gray-500">Gestisci attori, scuola, scout e sceneggiature</p>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-4 gap-1.5 mb-4">
        {TABS.map(tab => {
          const TabIcon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex flex-col items-center gap-1 py-2 rounded-xl text-[10px] font-medium border transition-all ${
                isActive
                  ? `bg-${tab.color}-500/15 border-${tab.color}-500/30 text-${tab.color}-400 shadow-[0_0_10px_rgba(100,200,255,0.06)]`
                  : 'bg-white/3 border-white/5 text-gray-500 hover:text-gray-300'
              }`}
              data-testid={`agenzia-tab-${tab.id}`}
            >
              <TabIcon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ===== ATTORI TAB ===== */}
      {activeTab === 'attori' && (
        <div className="space-y-3" data-testid="agenzia-attori">
          {/* Kept actors from school */}
          {schoolStatus?.kept_actors?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-yellow-400 uppercase flex items-center gap-1.5"><Star className="w-3.5 h-3.5" /> Cast Personale ({schoolStatus.kept_actors.length})</h4>
              {schoolStatus.kept_actors.map(a => (
                <div key={a.id} className="flex items-center gap-2.5 p-2.5 bg-white/3 rounded-xl border border-yellow-500/15">
                  <img src={a.avatar_url} alt="" className="w-9 h-9 rounded-full bg-gray-700" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{a.name}</p>
                    <p className="text-[10px] text-gray-500">${a.monthly_salary?.toLocaleString()}/mese</p>
                  </div>
                  <Badge className="bg-yellow-900/40 text-yellow-400 text-[9px]">Nel cast</Badge>
                </div>
              ))}
            </div>
          )}
          {/* Casting agency actors */}
          {actors.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-cyan-400 uppercase flex items-center gap-1.5"><Users className="w-3.5 h-3.5" /> Agenzia Cast ({actors.length})</h4>
              {actors.map(a => (
                <div key={a.id || a.name} className="flex items-center gap-2.5 p-2.5 bg-white/3 rounded-xl border border-cyan-500/15">
                  <img src={a.avatar_url || a.photo_url || ''} alt="" className="w-9 h-9 rounded-full bg-gray-700" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{a.name}</p>
                    <p className="text-[10px] text-gray-500">{a.nationality || ''} {a.age ? `${a.age} anni` : ''}</p>
                  </div>
                  {a.talent_score && <Badge className="bg-purple-500/20 text-purple-400 text-[9px]">Talento {a.talent_score}</Badge>}
                </div>
              ))}
            </div>
          )}
          {(!schoolStatus?.kept_actors?.length && !actors.length) && (
            <div className="text-center py-12 text-gray-500">
              <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Nessun attore nel cast</p>
              <p className="text-[10px] text-gray-600 mt-1">Forma attori nella Scuola di Recitazione</p>
            </div>
          )}
        </div>
      )}

      {/* ===== SCUOLA TAB ===== */}
      {activeTab === 'scuola' && (
        <div className="space-y-3" data-testid="agenzia-scuola">
          {!hasSchool ? (
            <div className="text-center py-12 text-gray-500">
              <GraduationCap className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Scuola di Recitazione non posseduta</p>
              <Button variant="outline" className="mt-3 text-xs" onClick={() => navigate('/infrastructure')}>Acquista in Infrastrutture</Button>
            </div>
          ) : (
            <>
              {/* School stats */}
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2.5 bg-yellow-500/10 rounded-xl border border-yellow-500/20 text-center">
                  <p className="text-[9px] text-gray-400">Livello</p>
                  <p className="text-lg font-bold text-yellow-400">{schoolStatus?.school_level || 1}</p>
                </div>
                <div className="p-2.5 bg-cyan-500/10 rounded-xl border border-cyan-500/20 text-center">
                  <p className="text-[9px] text-gray-400">Slot</p>
                  <p className="text-lg font-bold text-cyan-400">{schoolStatus?.available_slots || 0}/{schoolStatus?.max_slots || 1}</p>
                </div>
                <div className="p-2.5 bg-green-500/10 rounded-xl border border-green-500/20 text-center">
                  <p className="text-[9px] text-gray-400">In Corso</p>
                  <p className="text-lg font-bold text-green-400">{schoolStatus?.training_count || 0}</p>
                </div>
              </div>

              {/* Trainees in training */}
              {schoolStatus?.trainees?.filter(t => t.status === 'training').map(t => (
                <div key={t.id} className="p-3 bg-blue-500/5 rounded-xl border border-blue-500/15">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <img src={t.avatar_url} alt="" className="w-8 h-8 rounded-full bg-gray-700" />
                      <div>
                        <p className="text-sm font-medium">{t.name}</p>
                        <p className="text-[10px] text-gray-500">{t.age} anni {t.is_promising && <span className="text-green-400">Promettente</span>}</p>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-blue-400">{t.progress}%</span>
                  </div>
                  <Progress value={t.progress} className="h-1.5 mb-2" />
                  <div className="grid grid-cols-2 gap-0.5">
                    {Object.entries(t.current_skills || {}).map(([k, v]) => (
                      <div key={k} className="flex items-center gap-1">
                        <span className="text-[9px] text-gray-500 w-20 truncate">{SKILL_TRANSLATIONS?.[k]?.[language] || k}</span>
                        <div className="flex-1 h-1 bg-gray-800 rounded-full"><div className="h-full rounded-full" style={{ width: `${v}%`, background: v > 70 ? '#22c55e' : v > 40 ? '#eab308' : '#ef4444' }} /></div>
                        <span className="text-[9px] text-gray-400 w-4 text-right">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {/* Casting students */}
              {castingStudents?.students?.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-cyan-400 uppercase flex items-center gap-1.5"><GraduationCap className="w-3.5 h-3.5" /> Studenti Casting ({castingStudents.used}/{castingStudents.capacity})</h4>
                  {castingStudents.students.map(s => (
                    <div key={s.id} className={`p-3 rounded-xl border ${s.all_maxed ? 'bg-amber-500/5 border-amber-500/15' : s.can_graduate ? 'bg-green-500/5 border-green-500/15' : 'bg-cyan-500/5 border-cyan-500/15'}`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <img src={s.avatar_url} alt="" className="w-8 h-8 rounded-full bg-gray-700" />
                          <div>
                            <p className="text-sm font-medium">{s.name}</p>
                            <p className="text-[10px] text-gray-500">{s.age} anni {s.is_legendary && <span className="text-yellow-400">Leggendario</span>}</p>
                          </div>
                        </div>
                        <Badge className={`text-[9px] ${s.all_maxed ? 'bg-amber-500/20 text-amber-400' : s.can_graduate ? 'bg-green-500/20 text-green-400' : 'bg-cyan-500/20 text-cyan-300'}`}>
                          {s.all_maxed ? 'Max' : s.can_graduate ? 'Pronto!' : `${Math.round(s.elapsed_hours)}h`}
                        </Badge>
                      </div>
                      {s.all_maxed && <p className="text-[10px] text-amber-300 mb-2 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Potenziale massimo. {s.can_graduate && 'Diplomalo!'}</p>}
                      <div className="grid grid-cols-2 gap-0.5 mb-2">
                        {Object.entries(s.current_skills || {}).map(([k, v]) => (
                          <div key={k} className="flex items-center gap-1">
                            <span className="text-[9px] text-gray-500 w-20 truncate">{SKILL_TRANSLATIONS?.[k]?.[language] || k}</span>
                            <div className="flex-1 h-1 bg-gray-800 rounded-full"><div className="h-full rounded-full" style={{ width: `${Math.min(100, v)}%`, background: v > 70 ? '#22c55e' : v > 40 ? '#eab308' : '#ef4444' }} /></div>
                            <span className="text-[9px] text-gray-400 w-4 text-right">{v}</span>
                          </div>
                        ))}
                      </div>
                      {s.needs_payment && s.total_due > 0 && (
                        <div className="flex items-center justify-between p-1.5 mb-2 bg-red-500/10 rounded border border-red-500/15">
                          <span className="text-[10px] text-red-300">Da pagare: ${s.total_due.toLocaleString()}</span>
                          <Button size="sm" className="bg-red-700 text-[10px] h-5 px-2" disabled={actionLoading === s.id} onClick={() => schoolAction('pay', s.id)}>Paga</Button>
                        </div>
                      )}
                      <div className="flex gap-2">
                        {s.can_graduate && <Button size="sm" className="flex-1 bg-green-700 text-xs" disabled={actionLoading === s.id || (s.needs_payment && s.total_due > 0)} onClick={() => schoolAction('graduate', s.id)}><GraduationCap className="w-3 h-3 mr-1" /> Diploma</Button>}
                        <Button size="sm" variant="outline" className="text-xs border-gray-600 text-gray-400" disabled={actionLoading === s.id} onClick={() => schoolAction('dismiss', s.id)}><X className="w-3 h-3 mr-1" /> Rimuovi</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Ready trainees */}
              {schoolStatus?.trainees?.filter(t => t.status === 'ready').map(t => (
                <div key={t.id} className="p-3 bg-green-500/5 rounded-xl border border-green-500/15">
                  <div className="flex items-center gap-2 mb-2">
                    <img src={t.avatar_url} alt="" className="w-8 h-8 rounded-full bg-gray-700" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{t.name} <Sparkles className="w-3 h-3 inline text-green-400" /></p>
                      <p className="text-[10px] text-gray-500">{t.age} anni - Formazione completata!</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-0.5 mb-2">
                    {Object.entries(t.current_skills || {}).map(([k, v]) => (
                      <div key={k} className="flex items-center gap-1">
                        <span className="text-[9px] text-gray-500 w-20 truncate">{SKILL_TRANSLATIONS?.[k]?.[language] || k}</span>
                        <div className="flex-1 h-1 bg-gray-800 rounded-full"><div className="h-full rounded-full" style={{ width: `${v}%`, background: v > 70 ? '#22c55e' : v > 40 ? '#eab308' : '#ef4444' }} /></div>
                        <span className="text-[9px] text-gray-400 w-4 text-right">{v}</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1 bg-green-700 text-xs" onClick={() => schoolAction('keep', t.id)}><Lock className="w-3 h-3 mr-1" /> Tieni</Button>
                    <Button size="sm" variant="outline" className="flex-1 text-xs border-gray-600" onClick={() => schoolAction('release', t.id)}><Unlock className="w-3 h-3 mr-1" /> Libera</Button>
                  </div>
                </div>
              ))}

              {/* Available recruits */}
              {schoolStatus?.available_slots > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-cyan-400 uppercase flex items-center gap-1.5"><Users className="w-3.5 h-3.5" /> Reclute Disponibili</h4>
                  {schoolRecruits.map(r => (
                    <div key={r.id} className="p-2.5 bg-white/3 rounded-xl border border-white/8">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <img src={r.avatar_url} alt="" className="w-7 h-7 rounded-full bg-gray-700" />
                          <div>
                            <p className="text-sm font-medium">{r.name}</p>
                            <p className="text-[10px] text-gray-500">{r.age} anni {r.is_promising ? <span className="text-green-400">Promettente</span> : 'Standard'}</p>
                          </div>
                        </div>
                        <Button size="sm" className="bg-cyan-700 text-[10px] h-7" disabled={actionLoading === r.id} onClick={() => schoolAction('train', r.id)}>
                          <GraduationCap className="w-3 h-3 mr-1" />$200K +3<Ticket className="w-2.5 h-2.5 ml-0.5" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-0.5">
                        {Object.entries(r.initial_skills || {}).map(([k, v]) => (
                          <div key={k} className="flex items-center gap-1">
                            <span className="text-[9px] text-gray-500 w-20 truncate">{SKILL_TRANSLATIONS?.[k]?.[language] || k}</span>
                            <div className="flex-1 h-1 bg-gray-800 rounded-full"><div className="h-full rounded-full" style={{ width: `${v}%`, background: v > 70 ? '#22c55e' : v > 40 ? '#eab308' : '#ef4444' }} /></div>
                            <span className="text-[9px] text-gray-400 w-4 text-right">{v}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                  {schoolRecruits.length === 0 && <p className="text-center text-gray-600 text-xs py-3">Nessuna recluta disponibile oggi</p>}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ===== SCOUT TAB ===== */}
      {activeTab === 'scout' && (
        <div className="space-y-3" data-testid="agenzia-scout">
          {hasScoutActors && (
            <div className="p-4 bg-purple-500/5 rounded-xl border border-purple-500/15">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg bg-purple-500/15 flex items-center justify-center"><Search className="w-5 h-5 text-purple-400" /></div>
                <div>
                  <h4 className="text-sm font-semibold">Talent Scout Attori</h4>
                  <p className="text-[10px] text-gray-500">Scopre giovani talenti per la tua Agenzia Cast</p>
                </div>
              </div>
              <Badge className="bg-purple-500/20 text-purple-400 text-[10px]">Attivo Lv.{ownedInfra.find(i => i.type === 'talent_scout_actors')?.level || 1}</Badge>
            </div>
          )}
          {hasScoutWriters && (
            <div className="p-4 bg-yellow-500/5 rounded-xl border border-yellow-500/15">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg bg-yellow-500/15 flex items-center justify-center"><BookOpen className="w-5 h-5 text-yellow-400" /></div>
                <div>
                  <h4 className="text-sm font-semibold">Talent Scout Sceneggiatori</h4>
                  <p className="text-[10px] text-gray-500">Trova sceneggiature pronte per i tuoi film</p>
                </div>
              </div>
              <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">Attivo Lv.{ownedInfra.find(i => i.type === 'talent_scout_screenwriters')?.level || 1}</Badge>
            </div>
          )}
          {!hasScoutActors && !hasScoutWriters && (
            <div className="text-center py-12 text-gray-500">
              <Search className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Nessun Talent Scout posseduto</p>
              <Button variant="outline" className="mt-3 text-xs" onClick={() => navigate('/infrastructure')}>Acquista in Infrastrutture</Button>
            </div>
          )}
        </div>
      )}

      {/* ===== SCENEGGIATURE TAB ===== */}
      {activeTab === 'sceneggiature' && (
        <div className="space-y-3" data-testid="agenzia-sceneggiature">
          <div className="p-4 bg-yellow-500/5 rounded-xl border border-yellow-500/15">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-yellow-500/15 flex items-center justify-center"><BookOpen className="w-5 h-5 text-yellow-400" /></div>
              <div>
                <h4 className="text-sm font-semibold">Sceneggiature Emergenti</h4>
                <p className="text-[10px] text-gray-500">Esplora e acquista sceneggiature pronte per la produzione</p>
              </div>
            </div>
            <Button className="w-full h-9 bg-yellow-600 hover:bg-yellow-500 text-black font-semibold text-xs" onClick={() => navigate('/emerging-screenplays')}>
              Vai alle Sceneggiature <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
          {!hasScoutWriters && (
            <p className="text-center text-[10px] text-gray-600 py-2">Acquista il Talent Scout Sceneggiatori per ricevere proposte esclusive</p>
          )}
        </div>
      )}
    </div>
  );
}
