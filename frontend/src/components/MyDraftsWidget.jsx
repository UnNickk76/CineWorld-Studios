import React, { useContext, useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Film, Tv, Sparkles, Zap, BookOpen, RefreshCw, ChevronRight, Clock } from 'lucide-react';

/**
 * MyDraftsWidget — mostra le bozze in lavorazione dell'utente.
 * Aggrega tutte le pipeline (V3 film/serie/anime/sequel, LAMPO, sceneggiature pronte).
 * Click sulla card → naviga alla pipeline corretta in base alla collection.
 */

const TYPE_META = {
  film:                 { icon: Film,      color: 'text-yellow-400', bg: 'bg-yellow-500/10', label: 'Film' },
  series:               { icon: Tv,        color: 'text-blue-400',   bg: 'bg-blue-500/10',   label: 'Serie' },
  anime:                { icon: Sparkles,  color: 'text-orange-400', bg: 'bg-orange-500/10', label: 'Anime' },
  sequel:               { icon: Film,      color: 'text-purple-400', bg: 'bg-purple-500/10', label: 'Sequel' },
  lampo_film:           { icon: Zap,       color: 'text-pink-400',   bg: 'bg-pink-500/10',   label: 'LAMPO Film' },
  lampo_series:         { icon: Zap,       color: 'text-pink-400',   bg: 'bg-pink-500/10',   label: 'LAMPO Serie' },
  lampo_anime:          { icon: Zap,       color: 'text-pink-400',   bg: 'bg-pink-500/10',   label: 'LAMPO Anime' },
  purchased_screenplay: { icon: BookOpen,  color: 'text-emerald-400',bg: 'bg-emerald-500/10',label: 'Sceneggiatura' },
};

const STATE_LABELS = {
  idea: 'Bozza · Idea',
  hype: 'Locandina',
  cast: 'Casting',
  prep: 'Preparazione',
  ciak: 'Riprese',
  finalcut: 'Final Cut',
  marketing: 'Marketing',
  la_prima: 'La Prima',
  distribution: 'Distribuzione',
  release_pending: 'In uscita',
  draft: 'Bozza',
  generating: 'Generazione AI',
  lampo_ready: 'Pronto al rilascio',
  in_progress: 'In lavorazione',
};

function pipelineRouteFor(item) {
  if (item.is_lampo) return `/lampo/${item.id}`;
  if (item.is_purchased) return `/purchased-screenplays/${item.id}`;
  if (item.collection === 'series_projects_v3') return `/series-pipeline/${item.id}`;
  if (item.collection === 'sequel_projects') return `/sequel/${item.id}`;
  return `/pipeline/${item.id}`;
}

export default function MyDraftsWidget({ compact = false }) {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await api.get('/my/drafts?limit=20');
      setItems(res.data?.items || []);
    } catch { /* ignore */ }
    setLoading(false);
  }, [api]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="rounded-lg border border-white/10 bg-[#0F0F10] p-3 flex items-center justify-center" data-testid="my-drafts-loading">
        <RefreshCw className="w-4 h-4 animate-spin text-gray-500" />
      </div>
    );
  }

  if (items.length === 0) return null;

  return (
    <div className="rounded-lg border border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-transparent p-2.5 space-y-2"
      data-testid="my-drafts-widget">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <h3 className="text-[11px] font-bold text-amber-200 uppercase tracking-wide">In lavorazione</h3>
          <Badge className="bg-amber-500/20 text-amber-300 text-[9px] h-4 border border-amber-500/30 px-1.5">
            {items.length}
          </Badge>
        </div>
      </div>
      <div className={`grid ${compact ? 'grid-cols-2' : 'grid-cols-1 sm:grid-cols-2'} gap-1.5`}>
        {items.slice(0, compact ? 4 : 8).map(item => {
          const meta = TYPE_META[item.content_type] || TYPE_META.film;
          const Icon = meta.icon;
          const stateLabel = STATE_LABELS[item.pipeline_state] || item.pipeline_state || 'Bozza';
          return (
            <button key={`${item.collection}-${item.id}`}
              onClick={() => navigate(pipelineRouteFor(item))}
              className={`text-left rounded-lg border border-white/10 ${meta.bg} hover:border-white/25 transition-all p-2 group`}
              data-testid={`draft-${item.id}`}>
              <div className="flex items-start gap-2">
                {item.poster_url ? (
                  <img src={item.poster_url} alt=""
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    className="w-8 h-10 object-cover rounded flex-shrink-0 bg-black/40" />
                ) : (
                  <div className={`w-8 h-10 rounded ${meta.bg} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-3.5 h-3.5 ${meta.color}`} />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <Icon className={`w-2.5 h-2.5 ${meta.color} flex-shrink-0`} />
                    <span className={`text-[8px] font-bold ${meta.color} uppercase tracking-wider`}>{meta.label}</span>
                  </div>
                  <p className="text-[10px] font-semibold text-white truncate group-hover:text-yellow-200">{item.title}</p>
                  <p className="text-[9px] text-gray-500 truncate">
                    {stateLabel}
                    {item.progress_pct != null && <span className="text-amber-300 ml-1">· {item.progress_pct}%</span>}
                  </p>
                </div>
                <ChevronRight className="w-3 h-3 text-gray-600 group-hover:text-yellow-400 mt-1 flex-shrink-0" />
              </div>
            </button>
          );
        })}
      </div>
      {items.length > (compact ? 4 : 8) && (
        <button onClick={() => navigate('/films?tab=film&filter=draft')}
          className="w-full text-[9px] text-amber-400 hover:text-amber-300 py-1 border-t border-amber-500/10 mt-1"
          data-testid="my-drafts-show-all">
          Vedi tutti ({items.length}) →
        </button>
      )}
    </div>
  );
}
