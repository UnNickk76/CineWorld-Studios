import React, { useState, useEffect, useContext } from 'react';
import { X, Film, Star, Clock, MapPin, Users, Megaphone, Globe, Award, TrendingUp, Heart, Trash2, AlertTriangle } from 'lucide-react';
import { AuthContext } from '../../contexts';

const GENRE_LABELS = {
  action: 'Azione', comedy: 'Commedia', drama: 'Dramma', horror: 'Horror',
  sci_fi: 'Fantascienza', romance: 'Romance', thriller: 'Thriller',
  animation: 'Animazione', documentary: 'Documentario', fantasy: 'Fantasy',
  adventure: 'Avventura', musical: 'Musical', western: 'Western',
  biographical: 'Biografico', mystery: 'Mistero', war: 'Guerra',
  crime: 'Crime', noir: 'Noir', historical: 'Storico',
};

export default function FilmDetailV3({ filmId, onClose }) {
  const { api } = useContext(AuthContext);
  const [film, setFilm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (!filmId) return;
    setLoading(true);
    api.get(`/pipeline-v3/released-film/${filmId}`).then(r => {
      setFilm(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filmId, api]);

  const withdrawFromTheaters = async () => {
    setActionLoading(true);
    try {
      // Find source project id
      const pid = film?.source_project_id;
      if (pid) {
        await api.post(`/pipeline-v3/films/${pid}/withdraw-theaters`);
      }
      onClose?.();
    } catch (e) { /* */ }
    setActionLoading(false);
  };

  if (!filmId) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-end sm:items-center justify-center" onClick={onClose}>
      <div className="bg-gray-950 border-t sm:border border-gray-800 rounded-t-2xl sm:rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()} style={{ overscrollBehavior: 'contain' }}>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" />
          </div>
        ) : !film ? (
          <div className="text-center py-20 text-gray-500 text-sm">Film non trovato</div>
        ) : (
          <>
            {/* Header with poster */}
            <div className="relative">
              {film.poster_url ? (
                <img src={film.poster_url} alt="" className="w-full aspect-[2/3] object-cover rounded-t-2xl" />
              ) : (
                <div className="w-full aspect-[2/3] bg-gray-900 flex items-center justify-center rounded-t-2xl">
                  <Film className="w-12 h-12 text-gray-700" />
                </div>
              )}
              {/* Gradient overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-gray-950 via-gray-950/40 to-transparent" />
              {/* Close button */}
              <button onClick={onClose} className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/60 flex items-center justify-center">
                <X className="w-4 h-4 text-white" />
              </button>
              {/* LIVE badge */}
              {film.status === 'in_theaters' && (
                <div className="absolute top-3 left-3 flex items-center gap-1 bg-black/60 rounded-full px-2 py-1">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  <span className="text-[8px] font-bold text-green-400">LIVE AL CINEMA</span>
                </div>
              )}
              {/* Title on poster */}
              <div className="absolute bottom-4 left-4 right-4">
                <h2 className="text-xl font-black text-white drop-shadow-lg">{film.title}</h2>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <span className="text-[8px] px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 font-bold">{GENRE_LABELS[film.genre] || film.genre}</span>
                  {film.film_duration_label && <span className="text-[8px] text-gray-300 flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" />{film.film_duration_label}</span>}
                  {film.film_format && <span className="text-[8px] text-gray-400 capitalize">{film.film_format}</span>}
                </div>
              </div>
            </div>

            {/* Stats bar */}
            <div className="px-4 py-3 grid grid-cols-4 gap-2 border-b border-gray-800/50">
              <div className="text-center">
                <p className="text-[7px] text-gray-500 uppercase">In Sala</p>
                <p className="text-sm font-bold text-green-400">{film.days_in_theater || 0}g</p>
              </div>
              <div className="text-center">
                <p className="text-[7px] text-gray-500 uppercase">Rimanenti</p>
                <p className="text-sm font-bold text-yellow-400">{film.days_remaining || 0}g</p>
              </div>
              <div className="text-center">
                <p className="text-[7px] text-gray-500 uppercase">Likes</p>
                <p className="text-sm font-bold text-pink-400 flex items-center justify-center gap-0.5">
                  <Heart className="w-3 h-3" />{(film.likes_count || film.virtual_likes || 0).toLocaleString()}
                </p>
              </div>
              <div className="text-center">
                <p className="text-[7px] text-gray-500 uppercase">Incasso</p>
                <p className="text-sm font-bold text-emerald-400">${((film.total_revenue || 0) / 1000).toFixed(0)}K</p>
              </div>
            </div>

            {/* Producer */}
            <div className="px-4 py-2 border-b border-gray-800/50 flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-[8px] font-bold text-white">
                {(film.producer?.nickname || '?')[0]}
              </div>
              <div>
                <p className="text-[9px] font-bold text-white">{film.producer?.nickname || 'Produttore'}</p>
                <p className="text-[7px] text-gray-500">{film.producer?.production_house_name || ''}</p>
              </div>
            </div>

            {/* Cast */}
            {film.cast && (
              <div className="px-4 py-3 border-b border-gray-800/50">
                <p className="text-[8px] text-gray-500 uppercase font-bold mb-1.5">Cast</p>
                <div className="flex flex-wrap gap-1">
                  {film.cast.director && (
                    <span className="text-[7px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      Regia: {film.cast.director.name}
                    </span>
                  )}
                  {(film.cast.actors || []).map((a, i) => (
                    <span key={i} className="text-[7px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      {a.name} ({a.cast_role || 'attore'})
                    </span>
                  ))}
                  {film.cast.composer && (
                    <span className="text-[7px] px-1.5 py-0.5 rounded bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                      Musiche: {film.cast.composer.name}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Synopsis */}
            {film.preplot && (
              <div className="px-4 py-3 border-b border-gray-800/50">
                <p className="text-[8px] text-gray-500 uppercase font-bold mb-1">Trama</p>
                <p className="text-[9px] text-gray-400 leading-relaxed">{film.preplot}</p>
              </div>
            )}

            {/* Sponsors */}
            {film.selected_sponsors?.length > 0 && (
              <div className="px-4 py-3 border-b border-gray-800/50">
                <p className="text-[8px] text-gray-500 uppercase font-bold mb-1">Sponsor</p>
                <div className="flex flex-wrap gap-1">
                  {film.selected_sponsors.map((s, i) => (
                    <span key={i} className="text-[7px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20">
                      {s.sponsor_name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="px-4 py-4 space-y-2">
              {/* Withdraw from theaters */}
              {film.status === 'in_theaters' && (
                <>
                  {!showWithdraw ? (
                    <button onClick={() => setShowWithdraw(true)}
                      className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400 text-[9px] font-bold">
                      <Trash2 className="w-3.5 h-3.5" /> Togli dalle sale
                    </button>
                  ) : (
                    <div className="p-3 rounded-lg bg-orange-500/5 border border-orange-500/20 space-y-2">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-orange-400" />
                        <p className="text-[9px] text-orange-300 font-bold">Confermi?</p>
                      </div>
                      <p className="text-[8px] text-gray-400">Il film verra rimosso da tutte le sale.</p>
                      <div className="flex gap-2">
                        <button onClick={() => setShowWithdraw(false)}
                          className="flex-1 py-1.5 rounded-lg border border-gray-700 text-gray-400 text-[8px] font-bold">Annulla</button>
                        <button onClick={withdrawFromTheaters} disabled={actionLoading}
                          className="flex-1 py-1.5 rounded-lg bg-orange-500/20 border border-orange-500/40 text-orange-400 text-[8px] font-bold disabled:opacity-50">
                          {actionLoading ? '...' : 'Conferma'}
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
