// CineWorld Studio's — LocationCoherenceBar
// Mostra in real-time la coerenza delle location selezionate vs genere/pretrama.
// Barra colorata 0-100 (rosso/arancio/giallo/verde) + advice + AI deep analysis on demand.

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Sparkles, AlertTriangle, CheckCircle2, Loader2, MapPin, Award, Wand2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_COLORS = {
  optimal: { ring: 'ring-emerald-500/50', bar: 'from-emerald-400 to-emerald-600', text: 'text-emerald-300', bg: 'bg-emerald-950/30', icon: CheckCircle2 },
  low: { ring: 'ring-orange-500/50', bar: 'from-orange-400 to-orange-600', text: 'text-orange-300', bg: 'bg-orange-950/30', icon: AlertTriangle },
  high: { ring: 'ring-rose-500/50', bar: 'from-rose-400 to-rose-600', text: 'text-rose-300', bg: 'bg-rose-950/30', icon: AlertTriangle },
  neutral: { ring: 'ring-zinc-700', bar: 'from-zinc-500 to-zinc-700', text: 'text-zinc-400', bg: 'bg-zinc-900/40', icon: MapPin },
};

export const LocationCoherenceBar = ({ genre, preplot, locations = [] }) => {
  const [data, setData] = useState(null);
  const [loadingAi, setLoadingAi] = useState(false);
  const [aiActivated, setAiActivated] = useState(false);

  const checkQuick = useCallback(async () => {
    try {
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.post(`${API}/api/locations/coherence-check`,
        { genre: genre || 'drama', preplot: preplot || '', locations: locations || [], use_ai: false },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setData(res.data);
    } catch { /* silent */ }
  }, [genre, preplot, locations]);

  useEffect(() => {
    if (genre) checkQuick();
  }, [genre, locations.length, checkQuick]);

  const checkDeep = async () => {
    setLoadingAi(true);
    try {
      const token = localStorage.getItem('cineworld_token');
      const res = await axios.post(`${API}/api/locations/coherence-check`,
        { genre: genre || 'drama', preplot: preplot || '', locations: locations || [], use_ai: true },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setData(res.data);
      setAiActivated(true);
    } catch { /* silent */ } finally { setLoadingAi(false); }
  };

  if (!data) return null;
  const status = data.quick?.status || 'neutral';
  const style = STATUS_COLORS[status] || STATUS_COLORS.neutral;
  const Icon = style.icon;
  const score = data.final_score;

  return (
    <div className={`rounded-xl ring-1 ${style.ring} ${style.bg} p-2.5 space-y-2`} data-testid="location-coherence-bar">
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${style.text} flex-shrink-0`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-300">Coerenza Location</span>
            <span className={`text-base font-black ${style.text}`} data-testid="coherence-score">{score}/100</span>
            {data.perfect_score_achieved && (
              <span className="text-[8px] font-black px-1.5 py-0.5 rounded-full bg-amber-500/30 text-amber-200 ring-1 ring-amber-500/50 ml-1 animate-pulse">
                <Award className="w-2.5 h-2.5 inline mb-0.5" /> PERFETTA
              </span>
            )}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">
            Sweet spot {genre}: <strong className="text-zinc-200">{data.quick?.sweet_spot_min}-{data.quick?.sweet_spot_max}</strong> location
            <span className="ml-1.5">·</span>
            <span className="ml-1.5">Tue: {locations.length}</span>
          </div>
        </div>
      </div>

      {/* Bar */}
      <div className="h-1.5 rounded-full bg-zinc-900 overflow-hidden">
        <motion.div
          className={`h-full bg-gradient-to-r ${style.bar}`}
          initial={{ width: '0%' }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.4 }}
        />
      </div>

      {/* Advice */}
      {data.quick?.advice && (
        <div className={`text-[10px] ${style.text} leading-snug`}>
          💡 {data.quick.advice}
        </div>
      )}

      {/* CWSv impact */}
      {data.cwsv_modifier !== 0 && (
        <div className={`text-[10px] flex items-center gap-1 ${data.cwsv_modifier > 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
          <Sparkles className="w-2.5 h-2.5" />
          Impatto CWSv: {data.cwsv_modifier > 0 ? '+' : ''}{data.cwsv_modifier}
        </div>
      )}

      {/* AI deep analysis trigger */}
      {!aiActivated && (preplot || '').trim().length > 50 && locations.length >= 1 && (
        <button
          onClick={checkDeep}
          disabled={loadingAi}
          className="w-full text-[10px] font-bold py-1.5 rounded-lg bg-violet-500/20 ring-1 ring-violet-500/50 text-violet-200 hover:bg-violet-500/30 disabled:opacity-50 flex items-center justify-center gap-1"
          data-testid="coherence-ai-check"
        >
          {loadingAi ? (
            <><Loader2 className="w-3 h-3 animate-spin" /> Analisi AI in corso…</>
          ) : (
            <><Wand2 className="w-3 h-3" /> Analisi AI profonda</>
          )}
        </button>
      )}

      {/* AI suggestions */}
      {data.ai && data.ai.suggested_locations?.length > 0 && (
        <div className="rounded-lg bg-violet-950/40 ring-1 ring-violet-700/30 p-2">
          <div className="text-[9px] font-bold text-violet-300 uppercase tracking-wider mb-1">
            🤖 Location consigliate dall'AI
          </div>
          <div className="flex flex-wrap gap-1">
            {data.ai.suggested_locations.map((s, i) => (
              <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-200" data-testid={`ai-suggestion-${i}`}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* AI warnings */}
      {data.ai && data.ai.warnings?.length > 0 && (
        <div className="rounded-lg bg-rose-950/40 ring-1 ring-rose-700/30 p-2">
          <div className="text-[9px] font-bold text-rose-300 uppercase tracking-wider mb-1">
            ⚠️ Location fuori posto
          </div>
          <div className="space-y-0.5">
            {data.ai.warnings.map((w, i) => (
              <div key={i} className="text-[10px] text-rose-200 leading-snug" data-testid={`ai-warning-${i}`}>
                • {w}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default LocationCoherenceBar;
