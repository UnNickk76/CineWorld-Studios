// CineWorld Studio's — MySagasPage
// Pagina dedicata alle saghe del player. Mostra:
//  • Timeline di ogni saga con tutti i capitoli (rilasciato/in produzione/pianificato)
//  • Pulsante "+ Nuovo Capitolo" se si possono creare altri capitoli
//  • Stats aggregate (CWSv medio, incassi totali)
//  • Modale per concludere/abbandonare la saga
//  • Modale per creare il prossimo capitolo (con subtitle)

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import {
  BookOpen, Plus, Sparkles, Clock, CheckCircle2, XCircle, AlertCircle,
  ChevronRight, Loader2, Award, Film, TrendingUp, TrendingDown, Calendar,
  Pause, Play, ArrowLeft, Star, Wallet, BarChart3, Lightbulb,
} from 'lucide-react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import { Progress } from '../components/ui/progress';
import { AuthContext } from '../contexts';
import { SagaBadge } from '../components/saga/SagaBadge';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_COLOR = {
  active: 'bg-emerald-500/20 text-emerald-200 border-emerald-700/50',
  concluded: 'bg-amber-500/20 text-amber-200 border-amber-700/50',
  abandoned: 'bg-rose-500/20 text-rose-200 border-rose-700/50',
  paused: 'bg-zinc-500/20 text-zinc-200 border-zinc-700/50',
};

const STATUS_LABEL = {
  active: 'Attiva',
  concluded: 'Conclusa',
  abandoned: 'Abbandonata',
  paused: 'In pausa',
};

const fmtMoney = (v) => `$${Math.round(Number(v || 0)).toLocaleString('it-IT')}`;

const MySagasPage = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sagaIdParam = searchParams.get('saga_id');
  const [sagas, setSagas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSagaId, setActiveSagaId] = useState(null);
  const [activeSagaDetail, setActiveSagaDetail] = useState(null);
  const [creatingChapter, setCreatingChapter] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSubtitle, setNewSubtitle] = useState('');
  const [showConcludeModal, setShowConcludeModal] = useState(false);

  const fetchSagas = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.get(`${API}/api/sagas/list`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSagas(res.data.sagas || []);
    } catch (e) {
      toast.error('Impossibile caricare le saghe');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchSagaDetail = useCallback(async (sagaId) => {
    try {
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.get(`${API}/api/sagas/${sagaId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setActiveSagaDetail(res.data);
    } catch (e) {
      toast.error('Errore caricamento dettaglio saga');
    }
  }, []);

  useEffect(() => {
    fetchSagas();
  }, [fetchSagas]);

  // Apri automaticamente la saga indicata via ?saga_id=
  useEffect(() => {
    if (!sagaIdParam || sagas.length === 0) return;
    const found = sagas.find(s => s.id === sagaIdParam);
    if (found) setActiveSagaId(sagaIdParam);
  }, [sagaIdParam, sagas]);

  useEffect(() => {
    if (activeSagaId) fetchSagaDetail(activeSagaId);
    else setActiveSagaDetail(null);
  }, [activeSagaId, fetchSagaDetail]);

  const handleCreateNextChapter = async () => {
    if (!newSubtitle.trim()) {
      toast.error('Inserisci un sottotitolo per il capitolo');
      return;
    }
    try {
      setCreatingChapter(true);
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.post(`${API}/api/sagas/create-next-chapter`, {
        saga_id: activeSagaId,
        subtitle: newSubtitle.trim(),
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Capitolo creato! Apri Pipeline V3 per completarlo.');
      const newProj = res.data.project;
      setShowCreateModal(false);
      setNewSubtitle('');
      // Vai alla pipeline V3 con il nuovo progetto
      if (newProj?.id) {
        navigate(`/pipeline-v3?project_id=${newProj.id}&saga=1`);
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore creazione capitolo');
    } finally {
      setCreatingChapter(false);
    }
  };

  const handleConcludeSaga = async () => {
    try {
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.post(`${API}/api/sagas/conclude`, {
        saga_id: activeSagaId, confirm: true,
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const fp = res.data.fame_penalty || 0;
      if (fp > 0) {
        toast.warning(`Saga abbandonata. Penalità fama: -${fp}`);
      } else {
        toast.success('Saga conclusa con successo!');
      }
      setShowConcludeModal(false);
      setActiveSagaId(null);
      fetchSagas();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore conclusione saga');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-20">
      <div className="sticky top-0 z-20 backdrop-blur-md bg-zinc-950/80 border-b border-zinc-800/60">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg hover:bg-zinc-800/60 transition"
            data-testid="sagas-back-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-amber-400" />
            <h1 className="text-lg sm:text-xl font-bold">Le Mie Saghe</h1>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6">
        {sagas.length === 0 ? (
          <EmptyState onGoToPipeline={() => navigate('/pipeline-v3')} />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sagas.map((s) => (
              <SagaCard
                key={s.id}
                saga={s}
                onClick={() => setActiveSagaId(s.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Saga Detail Modal */}
      <Dialog open={!!activeSagaId} onOpenChange={(o) => !o && setActiveSagaId(null)}>
        <DialogContent className="max-w-2xl bg-zinc-950 border-zinc-800 text-zinc-100 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-amber-300 flex items-center gap-2 text-lg">
              <BookOpen className="w-5 h-5" />
              {activeSagaDetail?.saga?.title || 'Saga'}
            </DialogTitle>
            <DialogDescription className="text-zinc-400 text-xs">
              {activeSagaDetail?.saga?.kind === 'animation' ? 'Animazione' : 'Film'} •{' '}
              {activeSagaDetail?.saga?.genre} •{' '}
              {STATUS_LABEL[activeSagaDetail?.saga?.status] || 'Attiva'}
            </DialogDescription>
          </DialogHeader>

          {activeSagaDetail && (
            <SagaDetailView
              detail={activeSagaDetail}
              onCreateChapter={() => setShowCreateModal(true)}
              onConclude={() => setShowConcludeModal(true)}
              onChapterClick={(c) => {
                if (c.film_id || c.id) {
                  navigate(`/films/${c.film_id || c.id}`);
                }
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Create Next Chapter Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-md bg-zinc-950 border-zinc-800 text-zinc-100">
          <DialogHeader>
            <DialogTitle className="text-amber-300 flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Nuovo Capitolo Saga
            </DialogTitle>
            <DialogDescription className="text-zinc-400 text-xs">
              Inserisci il sottotitolo del Cap. {(activeSagaDetail?.saga?.current_chapter_count || 0) + 1}.
              La pretrama sarà generata da AI in coerenza con i capitoli precedenti.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs font-semibold text-zinc-300 mb-1 block">
                Sottotitolo del capitolo
              </label>
              <Input
                value={newSubtitle}
                onChange={(e) => setNewSubtitle(e.target.value)}
                placeholder="es. Il Risveglio"
                maxLength={80}
                className="bg-zinc-900 border-zinc-800"
                data-testid="saga-new-chapter-subtitle"
              />
              <div className="text-[11px] text-zinc-500 mt-1">
                Titolo finale: <span className="text-amber-300 font-semibold">
                  {activeSagaDetail?.saga?.title} Capitolo {(activeSagaDetail?.saga?.current_chapter_count || 0) + 1}
                  {newSubtitle && `: ${newSubtitle}`}
                </span>
              </div>
            </div>

            <div className="rounded-lg bg-emerald-950/30 border border-emerald-700/30 p-2.5 text-[11px] text-emerald-200/90">
              💰 Costo capitolo: <strong>70%</strong> rispetto al cap. 1 (riuso asset).
              Pipeline V3 pre-compilata: locandina, pretrama, trailer base, cast.
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setShowCreateModal(false)}
              data-testid="saga-cancel-create"
            >
              Annulla
            </Button>
            <Button
              onClick={handleCreateNextChapter}
              disabled={creatingChapter || !newSubtitle.trim()}
              className="bg-amber-600 hover:bg-amber-500"
              data-testid="saga-confirm-create"
            >
              {creatingChapter ? (
                <><Loader2 className="w-4 h-4 mr-1 animate-spin" /> Creo...</>
              ) : (
                <>Crea Capitolo</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Conclude Saga Modal */}
      <Dialog open={showConcludeModal} onOpenChange={setShowConcludeModal}>
        <DialogContent className="max-w-md bg-zinc-950 border-zinc-800 text-zinc-100">
          <DialogHeader>
            <DialogTitle className="text-rose-300 flex items-center gap-2">
              <Pause className="w-5 h-5" />
              Concludi Saga
            </DialogTitle>
            <DialogDescription className="text-zinc-400 text-xs">
              Sei sicuro di voler concludere la saga «{activeSagaDetail?.saga?.title}»?
            </DialogDescription>
          </DialogHeader>
          <ConcludeWarning saga={activeSagaDetail?.saga} />
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowConcludeModal(false)} data-testid="saga-cancel-conclude">
              Annulla
            </Button>
            <Button onClick={handleConcludeSaga} className="bg-rose-700 hover:bg-rose-600" data-testid="saga-confirm-conclude">
              Conferma Conclusione
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ── Sub-components ──────────────────────────────────────────────────────

const EmptyState = ({ onGoToPipeline }) => (
  <div className="text-center py-16">
    <BookOpen className="w-16 h-16 text-amber-400/50 mx-auto mb-4" />
    <h2 className="text-xl font-bold text-zinc-200 mb-2">Nessuna saga ancora</h2>
    <p className="text-sm text-zinc-400 max-w-md mx-auto mb-6 leading-relaxed">
      Le saghe sono film a capitoli pianificati. Per crearne una, vai a creare un nuovo film
      in Pipeline V3 o LAMPO e marca <span className="text-amber-300 font-semibold">«Film a Capitoli»</span> all'ultimo step prima del rilascio.
    </p>
    <Button onClick={onGoToPipeline} className="bg-amber-600 hover:bg-amber-500" data-testid="sagas-go-pipeline">
      <Film className="w-4 h-4 mr-1.5" /> Crea il tuo primo capitolo
    </Button>
  </div>
);

const SagaCard = ({ saga, onClick }) => {
  const { stats } = saga;
  const tot = saga.total_planned_chapters;
  const rel = stats?.released_count || 0;
  const pct = tot > 0 ? Math.round((rel / tot) * 100) : 0;

  return (
    <Card
      onClick={onClick}
      className="bg-gradient-to-br from-zinc-900 via-zinc-950 to-zinc-900 border-zinc-800 hover:border-amber-700/60 cursor-pointer transition group"
      data-testid={`saga-card-${saga.id}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="font-bold text-amber-200 text-sm leading-tight line-clamp-2 group-hover:text-amber-100">
            {saga.title}
          </h3>
          <Badge className={`text-[9px] ${STATUS_COLOR[saga.status] || ''}`}>
            {STATUS_LABEL[saga.status] || saga.status}
          </Badge>
        </div>

        <div className="text-[10px] text-zinc-500 mb-2 flex items-center gap-2">
          <span>{saga.kind === 'animation' ? '🎨 Animazione' : '🎬 Film'}</span>
          <span>•</span>
          <span>{saga.genre}</span>
        </div>

        <div className="space-y-1 mb-3">
          <div className="flex items-baseline justify-between text-[11px]">
            <span className="text-zinc-400">Progresso</span>
            <span className="text-amber-300 font-bold">{rel}/{tot} capitoli</span>
          </div>
          <Progress value={pct} className="h-1.5 bg-zinc-800" />
        </div>

        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div className="rounded bg-zinc-900/60 p-1.5 border border-zinc-800/60">
            <div className="text-zinc-500">Incassi</div>
            <div className="text-emerald-300 font-bold truncate">{fmtMoney(stats?.total_revenue || 0)}</div>
          </div>
          <div className="rounded bg-zinc-900/60 p-1.5 border border-zinc-800/60">
            <div className="text-zinc-500">CWSv medio</div>
            <div className="text-cyan-300 font-bold">{(stats?.avg_cwsv || 0).toFixed(1)}/10</div>
          </div>
        </div>

        {stats?.active_in_pipeline > 0 && (
          <div className="mt-2 text-[10px] text-amber-300 flex items-center gap-1">
            <Loader2 className="w-3 h-3 animate-spin" />
            {stats.active_in_pipeline} in produzione
          </div>
        )}

        {saga.trilogy_bonus_awarded && (
          <div className="mt-2 text-[10px] text-amber-300 flex items-center gap-1 font-bold">
            <Award className="w-3 h-3" /> Trilogia Completata
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const SagaDetailView = ({ detail, onCreateChapter, onConclude, onChapterClick }) => {
  const { saga, chapters, can_create_next, create_blocked_reason, advise_stop, advise_message,
    can_continue_beyond_planned, next_release_blocked_until, active_in_pipeline } = detail;

  const totalRev = chapters.reduce((s, c) => s + (c.total_revenue || 0), 0);
  const avgCwsv = chapters.length > 0
    ? chapters.reduce((s, c) => s + (c.cwsv || 0), 0) / chapters.length
    : 0;

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="rounded-lg bg-zinc-900/60 border border-zinc-800 p-2">
          <div className="text-zinc-500 text-[10px]">Capitoli rilasciati</div>
          <div className="text-amber-300 font-bold">{chapters.length}/{saga.total_planned_chapters}</div>
        </div>
        <div className="rounded-lg bg-zinc-900/60 border border-zinc-800 p-2">
          <div className="text-zinc-500 text-[10px]">Incassi totali</div>
          <div className="text-emerald-300 font-bold truncate">{fmtMoney(totalRev)}</div>
        </div>
        <div className="rounded-lg bg-zinc-900/60 border border-zinc-800 p-2">
          <div className="text-zinc-500 text-[10px]">CWSv medio</div>
          <div className="text-cyan-300 font-bold">{avgCwsv.toFixed(1)}/10</div>
        </div>
      </div>

      {/* Velion advisor message */}
      {advise_stop && advise_message && (
        <div className="rounded-lg border border-rose-700/50 bg-rose-950/30 p-3 text-xs text-rose-200" data-testid="saga-advise-stop">
          <div className="flex items-center gap-1.5 font-semibold mb-1">
            <Lightbulb className="w-3.5 h-3.5" /> Consiglio Velion AI
          </div>
          {advise_message}
        </div>
      )}
      {can_continue_beyond_planned && !advise_stop && (
        <div className="rounded-lg border border-amber-700/50 bg-amber-950/30 p-3 text-xs text-amber-200" data-testid="saga-can-extend">
          <div className="flex items-center gap-1.5 font-semibold mb-1">
            <TrendingUp className="w-3.5 h-3.5" /> Saga in successo!
          </div>
          Hai sbloccato la possibilità di superare il numero di capitoli pianificato. Continua finché vuoi!
        </div>
      )}

      {/* Capitoli timeline */}
      <div className="space-y-2">
        <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Capitoli</h4>
        {chapters.length === 0 ? (
          <div className="text-xs text-zinc-500 italic">Nessun capitolo ancora rilasciato.</div>
        ) : (
          chapters.map((c) => (
            <div
              key={c.id || c.film_id || c.chapter_number}
              onClick={() => onChapterClick?.(c)}
              className="flex items-center gap-3 rounded-lg bg-zinc-900/60 border border-zinc-800 p-2.5 hover:border-amber-700/40 cursor-pointer transition"
              data-testid={`saga-chapter-${c.chapter_number}`}
            >
              <SagaBadge chapterNumber={c.chapter_number} totalChapters={saga.total_planned_chapters}
                cliffhanger={c.saga_cliffhanger} size="md" position="inline" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-amber-200 truncate">
                  {c.saga_subtitle || c.title}
                </div>
                <div className="flex items-center gap-2 text-[10px] text-zinc-500">
                  <span><Star className="w-2.5 h-2.5 inline mb-0.5" /> {(c.cwsv || 0).toFixed(1)}/10</span>
                  <span>•</span>
                  <span>{fmtMoney(c.total_revenue)}</span>
                  {c.is_lampo && <>
                    <span>•</span>
                    <span className="text-yellow-400">⚡ LAMPO</span>
                  </>}
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-zinc-600" />
            </div>
          ))
        )}
      </div>

      {/* Create next chapter */}
      {saga.status === 'active' && (
        <div className="border-t border-zinc-800 pt-3 space-y-2">
          {next_release_blocked_until && (
            <div className="rounded-lg border border-cyan-700/50 bg-cyan-950/20 p-2.5 text-[11px] text-cyan-200" data-testid="saga-next-blocked">
              <Clock className="w-3.5 h-3.5 inline mr-1 -mt-0.5" />
              Il prossimo capitolo potrà uscire dopo il <strong>{String(next_release_blocked_until).slice(0, 10)}</strong>
              {' '}(termine cinema cap. precedente).
            </div>
          )}

          {can_create_next ? (
            <Button
              onClick={onCreateChapter}
              className="w-full bg-amber-600 hover:bg-amber-500"
              data-testid="saga-btn-create-next"
            >
              <Plus className="w-4 h-4 mr-1" />
              Crea Capitolo {saga.current_chapter_count + 1}
              {active_in_pipeline > 0 && (
                <span className="ml-2 text-[10px] opacity-80">({active_in_pipeline} in produzione)</span>
              )}
            </Button>
          ) : (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-2.5 text-[11px] text-zinc-400" data-testid="saga-cannot-create">
              <AlertCircle className="w-3.5 h-3.5 inline mr-1 -mt-0.5" />
              {create_blocked_reason || 'Non puoi creare nuovi capitoli ora.'}
            </div>
          )}

          <Button
            onClick={onConclude}
            variant="outline"
            className="w-full border-rose-800/50 text-rose-300 hover:bg-rose-950/30"
            data-testid="saga-btn-conclude"
          >
            <Pause className="w-4 h-4 mr-1" /> Concludi/Abbandona Saga
          </Button>
        </div>
      )}
    </div>
  );
};

const ConcludeWarning = ({ saga }) => {
  if (!saga) return null;
  const total = saga.total_planned_chapters || 0;
  const rel = saga.released_count || 0;
  const pct = total > 0 ? rel / total : 0;

  if (pct < 0.5 && total >= 3) {
    const missing = total - rel;
    const penalty = Math.min(25, missing * 5);
    return (
      <div className="rounded-lg bg-rose-950/40 border border-rose-700/50 p-3 text-xs text-rose-200 my-2">
        <div className="flex items-center gap-1.5 font-bold mb-1">
          <AlertCircle className="w-4 h-4" /> Attenzione — Penalità Fama
        </div>
        Hai realizzato solo {rel}/{total} capitoli ({Math.round(pct * 100)}%). I fan si sentiranno traditi.
        <div className="mt-2 text-rose-300 font-semibold">
          Penalità stimata: <span className="text-base">-{penalty} fama</span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-amber-950/30 border border-amber-700/50 p-3 text-xs text-amber-200 my-2">
      Saga conclusa naturalmente ({rel}/{total} capitoli). Nessuna penalità.
    </div>
  );
};

export default MySagasPage;
