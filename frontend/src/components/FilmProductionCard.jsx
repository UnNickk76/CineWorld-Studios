import React from 'react';
import { Star, Film, Clock, Flame, Check } from 'lucide-react';
import { Badge } from './ui/badge';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const STATUS_LABELS = {
  proposed: 'Proposta',
  coming_soon: 'Coming Soon',
  ready_for_casting: 'Pronto Casting',
  casting: 'Casting',
  screenplay: 'Sceneggiatura',
  pre_production: 'Pre-Produzione',
  shooting: 'In Ripresa',
  pending_release: 'Pronto al Rilascio',
  remastering: 'In Rimasterizzazione',
  completed: 'Completato',
  released: 'Rilasciato',
};

const STATUS_COLORS = {
  proposed: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  coming_soon: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  ready_for_casting: 'bg-green-500/20 text-green-400 border-green-500/30',
  casting: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  screenplay: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  pre_production: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  shooting: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  pending_release: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  remastering: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  completed: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  released: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const STEP_CONFIG_IMMEDIATE = [
  { id: 'proposta', color: 'bg-yellow-500' },
  { id: 'casting', color: 'bg-cyan-500' },
  { id: 'script', color: 'bg-emerald-500' },
  { id: 'produzione', color: 'bg-blue-500' },
  { id: 'uscita', color: 'bg-purple-500' },
];

const STEP_CONFIG_CS = [
  { id: 'proposta', color: 'bg-yellow-500' },
  { id: 'poster', color: 'bg-purple-500' },
  { id: 'hype', color: 'bg-orange-500' },
  { id: 'casting', color: 'bg-cyan-500' },
  { id: 'script', color: 'bg-emerald-500' },
  { id: 'produzione', color: 'bg-blue-500' },
  { id: 'uscita', color: 'bg-purple-500' },
];

function getStepIndex(film) {
  const isCS = film.release_type === 'coming_soon' || film.status === 'ready_for_casting' || film.status === 'coming_soon';
  const s = film.status;

  if (isCS) {
    if (s === 'proposed' && !film.poster_url) return 1; // poster step
    if (s === 'proposed' && film.poster_url) return 2; // ready to launch CS
    if (s === 'coming_soon') return 2; // hype active
    if (s === 'ready_for_casting') return 3; // casting
    if (s === 'casting') return 3;
    if (s === 'screenplay') return 4;
    if (s === 'pre_production') return 5;
    if (s === 'shooting') return 6;
    return 0;
  } else {
    if (s === 'proposed') return 0; // proposta done, needs advance
    if (s === 'ready_for_casting') return 1;
    if (s === 'casting') return 1;
    if (s === 'screenplay') return 2;
    if (s === 'pre_production') return 3;
    if (s === 'shooting') return 4;
    return 0;
  }
}

function CardMiniStepBar({ film }) {
  const isCS = film.release_type === 'coming_soon' || film.status === 'ready_for_casting' || film.status === 'coming_soon';
  const steps = isCS ? STEP_CONFIG_CS : STEP_CONFIG_IMMEDIATE;
  const currentIdx = getStepIndex(film);

  return (
    <div className="flex items-center gap-[2px] mb-2" data-testid="card-mini-step-bar">
      {steps.map((step, i) => (
        <div
          key={step.id}
          className={`h-[3px] rounded-full flex-1 transition-all ${
            i < currentIdx ? `${step.color} opacity-70`
            : i === currentIdx ? `${step.color}`
            : 'bg-gray-800'
          }`}
        />
      ))}
    </div>
  );
}

export function FilmProductionCard({ film, onClick, countdown }) {
  const posterSrc = film.poster_url
    ? (film.poster_url.startsWith('/') ? `${API_URL}${film.poster_url}` : film.poster_url)
    : null;

  const isCSActive = film.status === 'coming_soon' && countdown;
  const isCSExpired = film.status === 'coming_soon' && !countdown && film.scheduled_release_at;

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-xl border border-gray-800/60 bg-[#131314] hover:bg-[#1a1a1c] hover:border-gray-700/60 transition-all group film-card-hover"
      data-testid={`film-card-${film.id}`}
    >
      <CardMiniStepBar film={film} />

      <div className="flex items-start gap-3">
        {posterSrc ? (
          <img
            src={posterSrc}
            alt=""
            className="w-14 h-20 object-cover rounded-lg flex-shrink-0 border border-white/5"
          />
        ) : (
          <div className="w-14 h-20 rounded-lg bg-gray-800/50 flex items-center justify-center flex-shrink-0 border border-white/5">
            <Film className="w-5 h-5 text-gray-600" />
          </div>
        )}

        <div className="flex-1 min-w-0">
          <h3 className="font-['Bebas_Neue'] text-base text-white truncate group-hover:text-yellow-400 transition-colors">
            {film.title}
          </h3>
          <p className="text-[10px] text-gray-500 truncate">
            {film.genre} {film.subgenre ? `\u2022 ${film.subgenre}` : ''} {film.location?.name ? `\u2022 ${film.location.name}` : ''}
          </p>

          <div className="flex items-center gap-1.5 mt-1">
            <Star className="w-3 h-3 text-yellow-400" />
            <span className={`text-sm font-bold ${
              film.pre_imdb_score >= 7 ? 'text-green-400' : film.pre_imdb_score >= 5 ? 'text-yellow-400' : 'text-red-400'
            }`}>
              {film.pre_imdb_score}
            </span>
            <span className="text-[8px] text-gray-600">Pre-IMDb</span>

            <Badge className={`ml-auto text-[8px] h-4 ${STATUS_COLORS[film.status] || 'bg-gray-600/20 text-gray-400'}`}>
              {STATUS_LABELS[film.status] || film.status}
            </Badge>
          </div>

          <p className="text-[9px] text-gray-500 mt-1 line-clamp-1 italic">
            "{film.pre_screenplay}"
          </p>

          {isCSActive && (
            <div className="flex items-center gap-1 mt-1">
              <Flame className="w-3 h-3 text-orange-400 animate-pulse" />
              <Clock className="w-2.5 h-2.5 text-cyan-400" />
              <span className="text-[10px] font-bold text-cyan-400">{countdown}</span>
              {film.hype_score > 0 && (
                <span className="text-[9px] text-orange-400 ml-1">Hype: {film.hype_score}</span>
              )}
            </div>
          )}
          {isCSExpired && (
            <div className="flex items-center gap-1 mt-1">
              <Check className="w-3 h-3 text-green-400" />
              <span className="text-[10px] font-bold text-green-400">Pronto per il Casting!</span>
            </div>
          )}
        </div>
      </div>
    </button>
  );
}
