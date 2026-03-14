import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, useTranslations } from '../contexts';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { toast } from 'sonner';
import { GraduationCap, User, Star, Clock, Check, Unlock, Lock, RefreshCw, Sparkles, AlertTriangle } from 'lucide-react';
import { LoadingSpinner } from '../components/ErrorBoundary';
import { SKILL_TRANSLATIONS } from '../constants';

const ActingSchool = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const [status, setStatus] = useState(null);
  const [recruits, setRecruits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [completeDialog, setCompleteDialog] = useState(null);
  const [engagementMonths, setEngagementMonths] = useState(3);

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

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await fetchStatus();
      await fetchRecruits();
      setLoading(false);
    };
    load();
    const interval = setInterval(fetchStatus, 30000);
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

  const SkillBar = ({ name, value, max = 100 }) => (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-gray-400 w-28 truncate">{SKILL_TRANSLATIONS?.[name]?.[language] || name}</span>
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${value}%`, background: value > 70 ? '#22c55e' : value > 40 ? '#eab308' : '#ef4444' }} />
      </div>
      <span className="text-[10px] font-mono text-gray-300 w-6 text-right">{value}</span>
    </div>
  );

  if (loading) return <LoadingSpinner />;

  if (!status?.has_school) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] text-white p-4 pt-16">
        <Card className="bg-[#1A1A1B] border-gray-800 max-w-md mx-auto mt-20">
          <CardContent className="p-8 text-center">
            <GraduationCap className="w-16 h-16 mx-auto text-yellow-400 mb-4" />
            <h2 className="text-xl font-bold mb-2">{language === 'it' ? 'Scuola di Recitazione' : 'Acting School'}</h2>
            <p className="text-gray-400 mb-4">{status?.message || (language === 'it' ? 'Acquista una Scuola di Recitazione nella sezione Infrastrutture per iniziare a formare attori!' : 'Buy an Acting School in Infrastructure to start training actors!')}</p>
            <Button onClick={() => window.location.href = '/infrastructure'} className="bg-yellow-600 hover:bg-yellow-700">
              {language === 'it' ? 'Vai alle Infrastrutture' : 'Go to Infrastructure'}
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
              Livello {status.school_level} &bull; {status.available_slots}/{status.max_slots} {language === 'it' ? 'slot disponibili' : 'slots available'}
            </p>
          </div>
          <Badge variant="outline" className="border-yellow-500/40 text-yellow-400">
            {status.training_count} in formazione &bull; {status.ready_count} pronti
          </Badge>
        </div>

        {/* Trainees in Training */}
        {status.trainees?.filter(t => t.status === 'training').length > 0 && (
          <Card className="bg-[#1A1A1B] border-gray-800" data-testid="trainees-training">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><Clock className="w-4 h-4 text-blue-400" />{language === 'it' ? 'In Formazione' : 'Training'}</CardTitle>
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
                      <SkillBar key={k} name={k} value={v} />
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Ready Trainees */}
        {status.trainees?.filter(t => t.status === 'ready').length > 0 && (
          <Card className="bg-[#1A1A1B] border-green-900/50" data-testid="trainees-ready">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><Check className="w-4 h-4 text-green-400" />{language === 'it' ? 'Formazione Completata!' : 'Training Complete!'}</CardTitle>
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
                      <SkillBar key={k} name={k} value={v} />
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1 bg-green-700 hover:bg-green-800 text-xs" onClick={() => setCompleteDialog({ ...t, preferAction: 'keep' })} data-testid={`keep-${t.id}`}>
                      <Lock className="w-3 h-3 mr-1" />{language === 'it' ? 'Tieni nel Cast' : 'Keep'}
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1 text-xs border-gray-600" onClick={() => completeTraining(t.id, 'release')} data-testid={`release-${t.id}`}>
                      <Unlock className="w-3 h-3 mr-1" />{language === 'it' ? 'Libera' : 'Release'}
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Kept Actors */}
        {status.kept_actors?.length > 0 && (
          <Card className="bg-[#1A1A1B] border-gray-800" data-testid="kept-actors">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><Star className="w-4 h-4 text-yellow-400" />{language === 'it' ? 'Cast Personale' : 'Personal Cast'} ({status.kept_actors.length})</CardTitle>
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

        {/* Available Recruits */}
        {status.available_slots > 0 && (
          <Card className="bg-[#1A1A1B] border-gray-800" data-testid="recruits-section">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2"><User className="w-4 h-4 text-cyan-400" />{language === 'it' ? 'Reclute Disponibili' : 'Available Recruits'}</CardTitle>
                <span className="text-[10px] text-gray-500">{language === 'it' ? 'Nuove reclute ogni giorno' : 'New recruits daily'}</span>
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
                              {r.age} {language === 'it' ? 'anni' : 'yo'} &bull; {r.is_promising
                                ? <span className="text-green-400">{language === 'it' ? 'Promettente' : 'Promising'}</span>
                                : <span className="text-gray-500">{language === 'it' ? 'Standard' : 'Standard'}</span>}
                            </p>
                          </div>
                        </div>
                        <Button size="sm" className="bg-cyan-700 hover:bg-cyan-800 text-xs h-7" onClick={() => startTraining(r.id)} data-testid={`train-${r.id}`}>
                          <GraduationCap className="w-3 h-3 mr-1" />$200K
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-1">
                        {Object.entries(r.initial_skills || {}).map(([k, v]) => (
                          <SkillBar key={k} name={k} value={v} />
                        ))}
                      </div>
                    </div>
                  ))}
                  {recruits.length === 0 && (
                    <p className="text-center text-gray-500 text-sm py-8">{language === 'it' ? 'Nessuna recluta disponibile oggi' : 'No recruits available today'}</p>
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
            <DialogTitle>{language === 'it' ? 'Tieni nel Cast Personale' : 'Keep in Personal Cast'}</DialogTitle>
            <DialogDescription className="text-gray-400">
              {completeDialog?.name} {language === 'it' ? 'sarà disponibile solo per i tuoi film a costo zero.' : 'will be available only for your films at no cost.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">{language === 'it' ? 'Durata ingaggio (mesi)' : 'Engagement (months)'}</label>
              <div className="flex gap-2">
                {[1, 3, 6, 12].map(m => (
                  <Button key={m} size="sm" variant={engagementMonths === m ? 'default' : 'outline'} className={`text-xs ${engagementMonths === m ? 'bg-yellow-600' : 'border-gray-600'}`} onClick={() => setEngagementMonths(m)}>
                    {m} {m === 1 ? (language === 'it' ? 'mese' : 'month') : (language === 'it' ? 'mesi' : 'months')}
                  </Button>
                ))}
              </div>
            </div>
            <div className="p-2 bg-black/30 rounded border border-gray-800">
              <p className="text-xs text-gray-400">{language === 'it' ? 'Stipendio mensile stimato' : 'Estimated monthly salary'}</p>
              <p className="text-lg font-bold text-yellow-400">${((50000 + 30 * 500)).toLocaleString()}/mese</p>
            </div>
            <Button className="w-full bg-green-700 hover:bg-green-800" onClick={() => completeTraining(completeDialog.id, 'keep')} data-testid="confirm-keep">
              {language === 'it' ? 'Conferma Ingaggio' : 'Confirm Engagement'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ActingSchool;
