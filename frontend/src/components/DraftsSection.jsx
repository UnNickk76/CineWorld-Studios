import React, { useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import {
  FileText, ChevronDown, ChevronUp, Trash2, Play, AlertTriangle,
  Clock, Film, RefreshCw, Shield, Tv, Sparkles
} from 'lucide-react';

const STATUS_LABELS = {
  draft: 'Bozza',
  proposed: 'Proposta',
  ready_for_casting: 'Pronto Casting',
  pending_release: 'In Attesa Rilascio',
  coming_soon: 'Coming Soon',
  concept: 'Concept',
  casting: 'Casting',
  screenplay: 'Sceneggiatura',
  production: 'Produzione',
  ready_to_release: 'Pronto al Rilascio',
};

const STATUS_COLORS = {
  draft: 'bg-gray-500/15 text-gray-400 border-gray-500/20',
  proposed: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  ready_for_casting: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  pending_release: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  coming_soon: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
  concept: 'bg-gray-500/15 text-gray-400 border-gray-500/20',
  casting: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  screenplay: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
  production: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/20',
  ready_to_release: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
};

const TYPE_ICONS = {
  film: Film,
  tv_series: Tv,
  anime: Sparkles,
};

const TYPE_LABELS = {
  film: 'Film',
  tv_series: 'Serie TV',
  anime: 'Anime',
};

export function DraftsSection({ api, onResume, onRefresh }) {
  const navigate = useNavigate();
  const [drafts, setDrafts] = useState([]);
  const [stuckFilms, setStuckFilms] = useState([]);
  const [seriesDrafts, setSeriesDrafts] = useState([]);
  const [stuckSeries, setStuckSeries] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [diagnosing, setDiagnosing] = useState(false);

  const loadDrafts = useCallback(async () => {
    try {
      const [filmRes, seriesRes] = await Promise.all([
        api.get('/film-pipeline/drafts'),
        api.get('/series-pipeline/drafts').catch(() => ({ data: { drafts: [], stuck_series: [] } }))
      ]);
      setDrafts(filmRes.data.drafts || []);
      setStuckFilms(filmRes.data.stuck_films || []);
      setSeriesDrafts(seriesRes.data.drafts || []);
      setStuckSeries(seriesRes.data.stuck_series || []);
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
      const data = res.data;
      const breakdown = data.status_breakdown || {};
      const limbo = data.limbo_count || 0;
      const ghosts = data.ghost_count || 0;
      
      const statusParts = Object.entries(breakdown).map(([k, v]) => `${k}: ${v}`).join(', ');
      
      if (limbo > 0 || ghosts > 0) {
        let msg = '';
        if (limbo > 0) msg += `${limbo} film nel LIMBO (completati ma mai in "I Miei"). `;
        if (ghosts > 0) msg += `${ghosts} FANTASMI (in pipeline ma gia rilasciati). `;
        msg += `Clicca "Recupera" per fixare! [${statusParts}]`;
        toast.error(msg, { duration: 10000 });
      } else {
        toast.success(
          `Tutto OK! ${data.total_projects} progetti, ${data.active_in_pipeline} in pipeline, ${data.total_released_films} rilasciati.`, 
          { duration: 5000 }
        );
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
      const { recovered_count, cleaned_count } = res.data;
      if (recovered_count > 0 || cleaned_count > 0) {
        let msg = '';
        if (recovered_count > 0) msg += `${recovered_count} film recuperati dal limbo! `;
        if (cleaned_count > 0) msg += `${cleaned_count} duplicati fantasma puliti!`;
        toast.success(msg, { duration: 8000 });
        loadDrafts();
        onRefresh?.();
      } else {
        toast.success('Nessun problema trovato. Tutti i film sono coerenti.');
      }
    } catch (e) {
      toast.error('Errore recupero');
    }
  };

  const totalItems = drafts.length + stuckFilms.length + seriesDrafts.length + stuckSeries.length;

  const allItems = [
    ...drafts.map(d => ({ ...d, _type: 'draft', _content: 'film' })),
    ...stuckFilms.map(f => ({ ...f, _type: 'stuck', _content: 'film' })),
    ...seriesDrafts.map(d => ({ ...d, _type: 'draft', _content: d.type || 'tv_series' })),
    ...stuckSeries.map(s => ({ ...s, _type: 'stuck', _content: s.type || 'tv_series' }))
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
        {totalItems > 0 && (
          <Badge className="bg-amber-500/15 text-amber-400 text-[9px] h-5 border border-amber-500/20">
            {totalItems}
          </Badge>
        )}
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
          {allItems.length === 0 ? (
            <div className="p-3 rounded-lg border border-dashed border-gray-700/50 text-center">
              <Shield className="w-5 h-5 mx-auto mb-1 text-gray-700" />
              <p className="text-[10px] text-gray-500">Nessuna bozza salvata</p>
              <p className="text-[8px] text-gray-600">Usa "Diagnostica" per controllare i tuoi film</p>
            </div>
          ) : allItems.map(item => {
            const IconComp = TYPE_ICONS[item._content] || Film;
            const typeLabel = TYPE_LABELS[item._content] || 'Film';
            return (
            <Card
              key={`${item._content}-${item.id}`}
              className={`bg-[#111113] border-white/5 overflow-hidden ${item._type === 'stuck' ? 'border-l-2 border-l-amber-500/50' : ''}`}
              data-testid={`draft-item-${item.id}`}
            >
              <CardContent className="p-2.5">
                <div className="flex items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <IconComp className="w-3 h-3 text-gray-500 flex-shrink-0" />
                      <p className="text-xs font-semibold text-white truncate">{item.title || 'Senza Titolo'}</p>
                      {item._content !== 'film' && (
                        <Badge className="text-[7px] h-3.5 bg-violet-500/15 text-violet-400 border border-violet-500/20">
                          {typeLabel}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <Badge className={`text-[8px] h-4 border ${STATUS_COLORS[item.status] || 'bg-gray-500/15 text-gray-400 border-gray-500/20'}`}>
                        {STATUS_LABELS[item.status] || item.status}
                      </Badge>
                      {item.genre && (
                        <span className="text-[8px] text-gray-500">{item.genre}</span>
                      )}
                      {item.num_episodes > 0 && (
                        <span className="text-[8px] text-gray-500">{item.num_episodes} ep.</span>
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
                      onClick={() => {
                        if (item._content === 'tv_series') {
                          navigate('/series-tv');
                        } else if (item._content === 'anime') {
                          navigate('/anime');
                        } else {
                          onResume?.(item);
                        }
                      }}
                      data-testid={`resume-draft-${item.id}`}
                    >
                      <Play className="w-3 h-3 mr-0.5" /> Riprendi
                    </Button>
                    {item._type === 'draft' && item._content === 'film' && (
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
          );})}
        </div>
      )}
    </div>
  );
}
