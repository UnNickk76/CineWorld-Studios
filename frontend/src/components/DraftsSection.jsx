import React, { useState, useEffect, useCallback, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import {
  FileText, ChevronDown, ChevronUp, Trash2, Play, AlertTriangle,
  Clock, Film, RefreshCw, Shield
} from 'lucide-react';

const STATUS_LABELS = {
  draft: 'Bozza',
  proposed: 'Proposta',
  ready_for_casting: 'Pronto Casting',
  pending_release: 'In Attesa Rilascio',
  coming_soon: 'Coming Soon',
};

const STATUS_COLORS = {
  draft: 'bg-gray-500/15 text-gray-400 border-gray-500/20',
  proposed: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  ready_for_casting: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  pending_release: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  coming_soon: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
};

export function DraftsSection({ api, onResume, onRefresh }) {
  const [drafts, setDrafts] = useState([]);
  const [stuckFilms, setStuckFilms] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [diagnosing, setDiagnosing] = useState(false);

  const loadDrafts = useCallback(async () => {
    try {
      const res = await api.get('/film-pipeline/drafts');
      setDrafts(res.data.drafts || []);
      setStuckFilms(res.data.stuck_films || []);
    } catch (e) {
      console.error('Error loading drafts:', e);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    loadDrafts();
  }, [loadDrafts]);

  const handleDeleteDraft = async (draftId) => {
    try {
      await api.delete(`/film-pipeline/draft/${draftId}`);
      toast.success('Bozza eliminata');
      loadDrafts();
      onRefresh?.();
    } catch (e) {
      toast.error('Errore eliminazione bozza');
    }
  };

  const handleDiagnose = async () => {
    setDiagnosing(true);
    try {
      const res = await api.get('/film-pipeline/diagnose');
      const invisible = res.data.invisible_projects || [];
      if (invisible.length > 0) {
        toast.error(`Trovati ${invisible.length} film invisibili!`);
      } else {
        toast.success(`Tutti i ${res.data.total_projects} film sono visibili.`);
      }
    } catch (e) {
      toast.error('Errore diagnostica');
    } finally {
      setDiagnosing(false);
    }
  };

  const handleRecoverAll = async () => {
    try {
      const res = await api.post('/film-pipeline/admin/recover-all');
      if (res.data.recovered_count > 0) {
        toast.success(`${res.data.recovered_count} film recuperati!`);
        loadDrafts();
        onRefresh?.();
      } else {
        toast.success('Nessun film perso trovato.');
      }
    } catch (e) {
      toast.error('Errore recupero');
    }
  };

  const totalItems = drafts.length + stuckFilms.length;
  if (loading || totalItems === 0) return null;

  const allItems = [
    ...drafts.map(d => ({ ...d, _type: 'draft' })),
    ...stuckFilms.map(f => ({ ...f, _type: 'stuck' }))
  ];

  return (
    <div className="mb-4" data-testid="drafts-section">
      <button
        className="w-full flex items-center gap-2 py-2 text-left group"
        onClick={() => setExpanded(!expanded)}
        data-testid="drafts-toggle"
      >
        <Shield className="w-4 h-4 text-amber-500" />
        <span className="font-['Bebas_Neue'] text-base text-amber-400">Bozze & Recupero</span>
        <Badge className="bg-amber-500/15 text-amber-400 text-[9px] h-5 border border-amber-500/20">
          {totalItems}
        </Badge>
        <div className="flex-1" />
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>

      {expanded && (
        <div className="space-y-2 mt-1">
          {/* Diagnostica e Recupero */}
          <div className="flex gap-2 mb-2">
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-[10px] border-amber-500/20 text-amber-400 hover:bg-amber-500/10"
              onClick={handleDiagnose}
              disabled={diagnosing}
              data-testid="diagnose-btn"
            >
              {diagnosing ? <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> : <AlertTriangle className="w-3 h-3 mr-1" />}
              Diagnostica
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-[10px] border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/10"
              onClick={handleRecoverAll}
              data-testid="recover-all-btn"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Recupera Film Persi
            </Button>
          </div>

          {/* Lista Bozze e Film Bloccati */}
          {allItems.map(item => (
            <Card
              key={item.id}
              className={`bg-[#111113] border-white/5 overflow-hidden ${item._type === 'stuck' ? 'border-l-2 border-l-amber-500/50' : ''}`}
              data-testid={`draft-item-${item.id}`}
            >
              <CardContent className="p-2.5">
                <div className="flex items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <Film className="w-3 h-3 text-gray-500 flex-shrink-0" />
                      <p className="text-xs font-semibold text-white truncate">{item.title || 'Senza Titolo'}</p>
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <Badge className={`text-[8px] h-4 border ${STATUS_COLORS[item.status] || 'bg-gray-500/15 text-gray-400 border-gray-500/20'}`}>
                        {STATUS_LABELS[item.status] || item.status}
                      </Badge>
                      {item.genre && (
                        <span className="text-[8px] text-gray-500">{item.genre}</span>
                      )}
                      {item.scheduled_release_at && (
                        <span className="text-[8px] text-orange-400 flex items-center gap-0.5">
                          <Clock className="w-2.5 h-2.5" />
                          {new Date(item.scheduled_release_at).toLocaleDateString('it-IT')}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-[10px] text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => onResume?.(item)}
                      data-testid={`resume-draft-${item.id}`}
                    >
                      <Play className="w-3 h-3 mr-0.5" /> Riprendi
                    </Button>
                    {item._type === 'draft' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-red-400/60 hover:text-red-400 hover:bg-red-500/10"
                        onClick={() => handleDeleteDraft(item.id)}
                        data-testid={`delete-draft-${item.id}`}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
