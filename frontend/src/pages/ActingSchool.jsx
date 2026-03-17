import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, useTranslations } from '../contexts';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { toast } from 'sonner';
import { GraduationCap, User, Star, Clock, Check, Unlock, Lock, RefreshCw, Sparkles, AlertTriangle, Award, TrendingUp, DollarSign, X } from 'lucide-react';
import { LoadingSpinner } from '../components/ErrorBoundary';
import { SKILL_TRANSLATIONS } from '../constants';

const SkillBar = ({ name, value, max = 100, language }) => (
  <div className="flex items-center gap-2">
    <span className="text-[10px] text-gray-400 w-28 truncate">{SKILL_TRANSLATIONS?.[name]?.[language] || name}</span>
    <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(100, value)}%`, background: value > 70 ? '#22c55e' : value > 40 ? '#eab308' : '#ef4444' }} />
    </div>
    <span className="text-[10px] font-mono text-gray-300 w-6 text-right">{value}</span>
  </div>
);

const ActingSchool = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const [status, setStatus] = useState(null);
  const [recruits, setRecruits] = useState([]);
  const [castingStudents, setCastingStudents] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completeDialog, setCompleteDialog] = useState(null);
  const [engagementMonths, setEngagementMonths] = useState(3);
  const [actionLoading, setActionLoading] = useState(null);

  const fetchStatus = async () => {
    try {
      const res = await api.get('/acting-school/status');
      setStatus(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchRecruits = async () => {
    try {
      const res = await api.get('/acting-school/recruits');
      setRecruits(res.data.recruits || []);
    } catch (e) {
      if (e.response?.status !== 404) console.error(e);
    }
  };

  const fetchCastingStudents = async () => {
    try {
      const res = await api.get('/acting-school/casting-students');
      setCastingStudents(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([fetchStatus(), fetchRecruits(), fetchCastingStudents()]);
      setLoading(false);
    };
    load();
    const interval = setInterval(() => {
      fetchStatus();
      fetchCastingStudents();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const startTraining = async (recruitId) => {
    try {
      const res = await api.post('/acting-school/train', { recruit_id: recruitId });
      toast.success(res.data.message);
      refreshUser();
      fetchStatus();
      fetchRecruits();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const completeTraining = async (traineeId, action) => {
    try {
      const res = await api.post(`/acting-school/complete/${traineeId}`, {
        action,
        engagement_months: action === 'keep' ? engagementMonths : undefined
      });
      toast.success(res.data.message);
      setCompleteDialog(null);
      refreshUser();
      fetchStatus();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
  };

  const graduateStudent = async (studentId) => {
    setActionLoading(studentId);
    try {
      const res = await api.post(`/acting-school/graduate/${studentId}`);
      toast.success(res.data.message);
      refreshUser();
      fetchCastingStudents();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setActionLoading(null);
    }
  };

  const payTraining = async (studentId) => {
    setActionLoading(studentId);
    try {
      const res = await api.post(`/acting-school/pay-training/${studentId}`);
      toast.success(res.data.message);
      refreshUser();
      fetchCastingStudents();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setActionLoading(null);
    }
  };

  const dismissStudent = async (studentId) => {
    setActionLoading(studentId);
    try {
      const res = await api.post(`/acting-school/dismiss/${studentId}`);
      toast.success(res.data.message);
      fetchCastingStudents();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return <LoadingSpinner />;

  if (!status?.has_school) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] text-white p-4 pt-16">
        <Card className="bg-[#1A1A1B] border-gray-800 max-w-md mx-auto mt-20">
          <CardContent className="p-8 text-center">
            <GraduationCap className="w-16 h-16 mx-auto text-yellow-400 mb-4" />
            <h2 className="text-xl font-bold mb-2">Scuola di Recitazione</h2>
            <p className="text-gray-400 mb-4">{status?.message || 'Acquista una Scuola di Recitazione nella sezione Infrastrutture per iniziare a formare attori!'}</p>
            <Button onClick={() => window.location.href = '/infrastructure'} className="bg-yellow-600 hover:bg-yellow-700">
              Vai alle Infrastrutture
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white p-4 pt-16 pb-20">
      <div className="max-w-4xl mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <GraduationCap className="w-6 h-6 text-yellow-400" />
              {status.school_name}
            </h1>
            <p className="text-xs text-gray-400">
              Livello {status.school_level} &bull; {status.training_count} occupati / {status.available_slots} disponibili
            </p>
          </div>
          <Badge variant="outline" className="border-yellow-500/40 text-yellow-400">
            {status.training_count} in formazione &bull; {status.ready_count} pronti
          </Badge>
        </div>

        {/* ==================== CASTING AGENCY STUDENTS SECTION ==================== */}
        {castingStudents?.has_school && (
          <Card className="bg-[#1A1A1B] border-cyan-900/50" data-testid="casting-students-section">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Award className="w-4 h-4 text-cyan-400" />
                  Studenti dall'Agenzia Casting
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge className="bg-cyan-500/20 text-cyan-400 text-[10px]">
                    {castingStudents.used} occupati / {castingStudents.capacity - castingStudents.used} disponibili
                  </Badge>
                  <Badge className="bg-gray-700 text-gray-300 text-[10px]">
                    Costo: ${(castingStudents.daily_cost || 0).toLocaleString()}/giorno
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {castingStudents.students?.length > 0 ? (
                castingStudents.students.map(s => (
                  <div key={s.id} className={`p-3 rounded-lg border transition-all ${
                    s.all_maxed 
                      ? 'bg-amber-950/20 border-amber-600/40' 
                      : s.can_graduate 
                        ? 'bg-green-950/20 border-green-600/40' 
                        : 'bg-black/30 border-cyan-900/30'
                  }`} data-testid={`casting-student-${s.id}`}>
                    {/* Student header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <img src={s.avatar_url} alt="" className="w-9 h-9 rounded-full bg-gray-700" />
                        <div>
                          <p className="text-sm font-medium">{s.name}</p>
                          <p className="text-[10px] text-gray-500">
                            {s.age} anni &bull; {s.nationality} &bull; 
                            {s.is_legendary 
                              ? <span className="text-yellow-400 ml-1">Leggendario</span> 
                              : <span className="text-gray-500 ml-1">Standard</span>}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Badge className={`text-[9px] ${
                          s.all_maxed ? 'bg-amber-500/20 text-amber-400' : 
                          s.can_graduate ? 'bg-green-500/20 text-green-400' : 
                          'bg-cyan-500/20 text-cyan-300'
                        }`}>
                          {s.all_maxed ? 'Max Potenziale' : s.can_graduate ? 'Pronto al diploma' : `${Math.round(s.elapsed_hours)}h`}
                        </Badge>
                      </div>
                    </div>

                    {/* Max potential warning */}
                    {s.all_maxed && (
                      <div className="flex items-center gap-2 p-2 mb-2 bg-amber-500/10 rounded border border-amber-500/20" data-testid={`max-potential-${s.id}`}>
                        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                        <p className="text-[11px] text-amber-300">
                          Questo attore ha raggiunto il suo potenziale massimo. Non migliorerà ulteriormente.
                          {s.can_graduate && ' Diplomalo per aggiungerlo al tuo cast!'}
                        </p>
                      </div>
                    )}

                    {/* Skills grid */}
                    <div className="grid grid-cols-2 gap-1 mb-2">
                      {Object.entries(s.current_skills || {}).map(([k, v]) => (
                        <SkillBar key={k} name={k} value={v} language={language} />
                      ))}
                    </div>

                    {/* Training info */}
                    <div className="flex items-center justify-between text-[10px] text-gray-500 mb-2">
                      <span>Giorni: {s.training_days} &bull; Pagati: {s.paid_days}</span>
                      {!s.all_maxed && (
                        <span className="flex items-center gap-1 text-cyan-400">
                          <TrendingUp className="w-3 h-3" /> In miglioramento
                        </span>
                      )}
                    </div>

                    {/* Payment warning */}
                    {s.needs_payment && s.total_due > 0 && (
                      <div className="flex items-center justify-between p-2 mb-2 bg-red-500/10 rounded border border-red-500/20">
                        <div className="flex items-center gap-1.5">
                          <DollarSign className="w-3.5 h-3.5 text-red-400" />
                          <span className="text-[11px] text-red-300">
                            Formazione da pagare: ${s.total_due.toLocaleString()} ({s.unpaid_days} giorni)
                          </span>
                        </div>
                        <Button 
                          size="sm" 
                          className="bg-red-700 hover:bg-red-800 text-[10px] h-6 px-2"
                          onClick={() => payTraining(s.id)}
                          disabled={actionLoading === s.id}
                          data-testid={`pay-training-${s.id}`}
                        >
                          {actionLoading === s.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Paga'}
                        </Button>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex gap-2">
                      {s.can_graduate && (
                        <Button 
                          size="sm" 
                          className="flex-1 bg-green-700 hover:bg-green-800 text-xs"
                          onClick={() => graduateStudent(s.id)}
                          disabled={actionLoading === s.id || (s.needs_payment && s.total_due > 0)}
                          data-testid={`graduate-${s.id}`}
                        >
                          {actionLoading === s.id ? <RefreshCw className="w-3 h-3 animate-spin mr-1" /> : <GraduationCap className="w-3 h-3 mr-1" />}
                          Diploma
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="text-xs border-gray-600 text-gray-400"
                        onClick={() => dismissStudent(s.id)}
                        disabled={actionLoading === s.id}
                        data-testid={`dismiss-${s.id}`}
                      >
                        <X className="w-3 h-3 mr-1" /> Rimuovi
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <Award className="w-10 h-10 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">Nessuno studente dall'Agenzia Casting</p>
                  <p className="text-[10px] mt-1">Vai allo Studio di Produzione &rarr; Agenzia Casting per inviare attori alla scuola</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* ==================== TRAINEES IN TRAINING ==================== */}
        {status.trainees?.filter(t => t.status === 'training').length > 0 && (
          <Card className="bg-[#1A1A1B] border-gray-800" data-testid="trainees-training">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><Clock className="w-4 h-4 text-blue-400" />In Formazione</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {status.trainees.filter(t => t.status === 'training').map(t => (
                <div key={t.id} className="p-3 bg-black/30 rounded-lg border border-gray-800">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <img src={t.avatar_url} alt="" className="w-8 h-8 rounded-full bg-gray-700" />
                      <div>
                        <p className="text-sm font-medium">{t.name}</p>
                        <p className="text-[10px] text-gray-500">{t.age} anni &bull; {t.is_promising ? <span className="text-green-400">Promettente</span> : <span className="text-gray-500">Standard</span>}</p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-400">{t.progress}%</span>
                  </div>
                  <Progress value={t.progress} className="h-1.5 mb-2" />
                  <div className="grid grid-cols-2 gap-1">
                    {Object.entries(t.current_skills || {}).map(([k, v]) => (
                      <SkillBar key={k} name={k} value={v} language={language} />
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* ==================== READY TRAINEES ==================== */}
        {status.trainees?.filter(t => t.status === 'ready').length > 0 && (
          <Card className="bg-[#1A1A1B] border-green-900/50" data-testid="trainees-ready">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><Check className="w-4 h-4 text-green-400" />Formazione Completata!</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {status.trainees.filter(t => t.status === 'ready').map(t => (
                <div key={t.id} className="p-3 bg-black/30 rounded-lg border border-green-900/40">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <img src={t.avatar_url} alt="" className="w-8 h-8 rounded-full bg-gray-700" />
                      <div>
                        <p className="text-sm font-medium">{t.name}</p>
                        <p className="text-[10px] text-gray-500">{t.age} anni</p>
                      </div>
                    </div>
                    <Sparkles className="w-4 h-4 text-yellow-400" />
                  </div>
                  <div className="grid grid-cols-2 gap-1 mb-3">
                    {Object.entries(t.current_skills || {}).map(([k, v]) => (
                      <SkillBar key={k} name={k} value={v} language={language} />
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1 bg-green-700 hover:bg-green-800 text-xs" onClick={() => setCompleteDialog({ ...t, preferAction: 'keep' })} data-testid={`keep-${t.id}`}>
                      <Lock className="w-3 h-3 mr-1" />Tieni nel Cast
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1 text-xs border-gray-600" onClick={() => completeTraining(t.id, 'release')} data-testid={`release-${t.id}`}>
                      <Unlock className="w-3 h-3 mr-1" />Libera
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* ==================== KEPT ACTORS ==================== */}
        {status.kept_actors?.length > 0 && (
          <Card className="bg-[#1A1A1B] border-gray-800" data-testid="kept-actors">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><Star className="w-4 h-4 text-yellow-400" />Cast Personale ({status.kept_actors.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {status.kept_actors.map(a => (
                <div key={a.id} className="p-2 bg-black/30 rounded-lg border border-gray-800 flex items-center gap-3">
                  <img src={a.avatar_url} alt="" className="w-8 h-8 rounded-full bg-gray-700" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{a.name}</p>
                    <p className="text-[10px] text-gray-500">${a.monthly_salary?.toLocaleString()}/mese</p>
                  </div>
                  <Badge className="bg-yellow-900/40 text-yellow-400 text-[10px]">Nel tuo cast</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* ==================== AVAILABLE RECRUITS ==================== */}
        {status.available_slots > 0 && (
          <Card className="bg-[#1A1A1B] border-gray-800" data-testid="recruits-section">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2"><User className="w-4 h-4 text-cyan-400" />Reclute Disponibili</CardTitle>
                <span className="text-[10px] text-gray-500">Nuove reclute ogni giorno</span>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-2 pr-2">
                  {recruits.map(r => (
                    <div key={r.id} className="p-3 bg-black/30 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <img src={r.avatar_url} alt="" className="w-8 h-8 rounded-full bg-gray-700" />
                          <div>
                            <p className="text-sm font-medium">{r.name}</p>
                            <p className="text-[10px] text-gray-500">
                              {r.age} anni &bull; {r.is_promising
                                ? <span className="text-green-400">Promettente</span>
                                : <span className="text-gray-500">Standard</span>}
                            </p>
                          </div>
                        </div>
                        <Button size="sm" className="bg-cyan-700 hover:bg-cyan-800 text-xs h-7" onClick={() => startTraining(r.id)} data-testid={`train-${r.id}`}>
                          <GraduationCap className="w-3 h-3 mr-1" />$200K
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-1">
                        {Object.entries(r.initial_skills || {}).map(([k, v]) => (
                          <SkillBar key={k} name={k} value={v} language={language} />
                        ))}
                      </div>
                    </div>
                  ))}
                  {recruits.length === 0 && (
                    <p className="text-center text-gray-500 text-sm py-8">Nessuna recluta disponibile oggi</p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Keep Dialog */}
      <Dialog open={!!completeDialog} onOpenChange={() => setCompleteDialog(null)}>
        <DialogContent className="bg-[#1A1A1B] border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle>Tieni nel Cast Personale</DialogTitle>
            <DialogDescription className="text-gray-400">
              {completeDialog?.name} sarà disponibile solo per i tuoi film a costo zero.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Durata ingaggio (mesi)</label>
              <div className="flex gap-2">
                {[1, 3, 6, 12].map(m => (
                  <Button key={m} size="sm" variant={engagementMonths === m ? 'default' : 'outline'} className={`text-xs ${engagementMonths === m ? 'bg-yellow-600' : 'border-gray-600'}`} onClick={() => setEngagementMonths(m)}>
                    {m} {m === 1 ? 'mese' : 'mesi'}
                  </Button>
                ))}
              </div>
            </div>
            <div className="p-2 bg-black/30 rounded border border-gray-800">
              <p className="text-xs text-gray-400">Stipendio mensile stimato</p>
              <p className="text-lg font-bold text-yellow-400">
                {completeDialog?.current_skills ? 
                  `$${(50000 + Math.round(Object.values(completeDialog.current_skills).reduce((a,b)=>a+b,0) / Object.keys(completeDialog.current_skills).length) * 500).toLocaleString()}/mese`
                  : '~$65,000/mese'}
              </p>
            </div>
            <Button className="w-full bg-green-700 hover:bg-green-800" onClick={() => completeTraining(completeDialog.id, 'keep')} data-testid="confirm-keep">
              Conferma Ingaggio
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ActingSchool;
