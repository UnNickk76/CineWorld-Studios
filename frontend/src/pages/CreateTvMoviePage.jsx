// CineWorld Studio's — Pagina creazione "Film per la TV"
// Riusa la pipeline V3 caricando il progetto creato con flag is_tv_movie=True.

import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Radio, ArrowLeft, Tv as TvIcon, Loader2, Lock, ArrowRight, X, Plus, Sparkles } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { GENRES as V3_GENRES, GENRE_LABELS, SUBGENRE_MAP } from '../components/v3/V3Shared';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CreateTvMoviePage() {
  const navigate = useNavigate();
  const token = localStorage.getItem('cineworld_token');
  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);

  const [loading, setLoading] = useState(true);
  const [eligible, setEligible] = useState(false);
  const [stations, setStations] = useState([]);

  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState(V3_GENRES[0]);
  const [subgenres, setSubgenres] = useState([]); // max 3
  const [preplot, setPreplot] = useState('');
  const [stationId, setStationId] = useState('');
  const [creating, setCreating] = useState(false);
  const [bonusInfo, setBonusInfo] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get(`${API}/api/tv-movies/check-eligibility`, { headers });
        setEligible(r.data.eligible);
        setStations(r.data.stations || []);
        if (r.data.stations?.length) setStationId(r.data.stations[0].id);
      } catch (e) {
        toast.error('Errore caricamento');
      } finally {
        setLoading(false);
      }
    })();
  }, [headers]);

  // Bonus genere↔stile (refresh on station/genre change)
  useEffect(() => {
    if (!stationId || !genre) { setBonusInfo(null); return; }
    let alive = true;
    (async () => {
      try {
        const r = await axios.get(`${API}/api/tv-movies/genre-style-bonus/${stationId}/${genre.toLowerCase()}`, { headers });
        if (alive) setBonusInfo(r.data);
      } catch (_) { /* ignore */ }
    })();
    return () => { alive = false; };
  }, [stationId, genre, headers]);

  const subgenreOptions = SUBGENRE_MAP[genre] || [];

  const toggleSubgenre = (sg) => {
    setSubgenres(prev => {
      if (prev.includes(sg)) return prev.filter(x => x !== sg);
      if (prev.length >= 3) {
        toast.info('Massimo 3 sottogeneri');
        return prev;
      }
      return [...prev, sg];
    });
  };

  // Reset subgenres when genre changes
  useEffect(() => { setSubgenres([]); }, [genre]);

  const handleCreate = async () => {
    if (!title.trim() || !preplot.trim() || !stationId) {
      toast.error('Compila titolo, pretrama e seleziona la TV');
      return;
    }
    setCreating(true);
    try {
      const r = await axios.post(`${API}/api/tv-movies/create`, {
        title: title.trim(),
        genre,
        subgenre: subgenres[0] || null,
        subgenres,
        preplot: preplot.trim(),
        target_station_id: stationId,
      }, { headers });
      toast.success(`"${title}" creato! Ora avanza nella pipeline.`);
      navigate(`/create-film?p=${r.data.project.id}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore creazione');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-rose-500 animate-spin" />
      </div>
    );
  }

  if (!eligible) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] p-4 pb-24">
        <div className="max-w-md mx-auto">
          <Button size="sm" variant="ghost" onClick={() => navigate(-1)} className="mb-3 text-gray-400" data-testid="back-btn">
            <ArrowLeft className="w-4 h-4 mr-1" /> Indietro
          </Button>
          <Card className="bg-rose-500/10 border-rose-500/30">
            <CardContent className="p-5 text-center space-y-3">
              <Lock className="w-10 h-10 mx-auto text-rose-300" />
              <h2 className="font-['Bebas_Neue'] text-xl text-white tracking-widest">FILM PER LA TV BLOCCATO</h2>
              <p className="text-xs text-rose-100">Per creare film TV devi possedere almeno una <span className="font-bold">stazione TV</span>.</p>
              <Button onClick={() => navigate('/infrastructure?focus=tv_station')} className="w-full bg-rose-500 hover:bg-rose-600" data-testid="goto-infra-tv-btn">
                Costruisci la tua TV <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B] p-4 pb-24" data-testid="create-tv-movie-page">
      <div className="max-w-md mx-auto space-y-4">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={() => navigate(-1)} className="text-gray-400" data-testid="back-btn">
            <ArrowLeft className="w-4 h-4 mr-1" /> Indietro
          </Button>
          <div className="flex items-center gap-2 ml-auto">
            <Radio className="w-5 h-5 text-rose-400" />
            <h1 className="font-['Bebas_Neue'] text-lg text-white tracking-widest">FILM PER LA TV</h1>
          </div>
        </div>

        {/* Form */}
        <Card className="bg-[#111113] border-white/5">
          <CardContent className="p-4 space-y-3">
            <div>
              <Label className="text-[10px] text-gray-400 uppercase tracking-wider mb-1 block">Titolo</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Es. Notte di Stelle" maxLength={120} data-testid="tv-movie-title-input" />
            </div>

            <div>
              <Label className="text-[10px] text-gray-400 uppercase tracking-wider mb-1 block">Genere</Label>
              <select value={genre} onChange={(e) => setGenre(e.target.value)} className="w-full bg-[#0d0d0f] border border-white/10 rounded-md px-3 py-2 text-xs text-white" data-testid="tv-movie-genre-select">
                {V3_GENRES.map(g => <option key={g} value={g}>{GENRE_LABELS[g]}</option>)}
              </select>
              {bonusInfo && bonusInfo.matches && (
                <div className="mt-1.5 flex items-center gap-1.5 px-2 py-1 rounded bg-emerald-500/15 border border-emerald-500/30" data-testid="genre-style-bonus-active">
                  <Sparkles className="w-3 h-3 text-emerald-400" />
                  <span className="text-[10px] text-emerald-300 font-bold">+{bonusInfo.bonus_pct}% CWSv (genere preferito da {bonusInfo.station_name})</span>
                </div>
              )}
            </div>

            {/* Sottogeneri (max 3) */}
            {subgenreOptions.length > 0 && (
              <div>
                <Label className="text-[10px] text-gray-400 uppercase tracking-wider mb-1 block">
                  Sottogeneri <span className="text-gray-600 normal-case">(max 3)</span>
                </Label>
                {subgenres.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-1.5">
                    {subgenres.map(sg => (
                      <button key={sg} type="button" onClick={() => toggleSubgenre(sg)}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-[10px] text-rose-200"
                        data-testid={`subgenre-selected-${sg}`}>
                        {sg} <X className="w-2.5 h-2.5" />
                      </button>
                    ))}
                  </div>
                )}
                <div className="flex flex-wrap gap-1 max-h-28 overflow-y-auto bg-[#0d0d0f] border border-white/10 rounded p-1.5">
                  {subgenreOptions.filter(sg => !subgenres.includes(sg)).map(sg => (
                    <button key={sg} type="button" onClick={() => toggleSubgenre(sg)}
                      className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-[9px] text-gray-300"
                      data-testid={`subgenre-option-${sg}`}>
                      <Plus className="w-2.5 h-2.5" /> {sg}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <Label className="text-[10px] text-gray-400 uppercase tracking-wider mb-1 block">Pretrama</Label>
              <Textarea value={preplot} onChange={(e) => setPreplot(e.target.value)} placeholder="Idea base del film (l'AI espandera' la sceneggiatura)" maxLength={2000} rows={3} data-testid="tv-movie-preplot-input" />
            </div>

            <div>
              <Label className="text-[10px] text-gray-400 uppercase tracking-wider mb-1 block">TV di Destinazione</Label>
              <div className="space-y-1.5">
                {stations.map(s => {
                  const sel = stationId === s.id;
                  return (
                    <button key={s.id} type="button" onClick={() => setStationId(s.id)}
                      className={`w-full flex items-center gap-2 p-2 rounded-lg border transition-all ${sel ? 'border-rose-500 bg-rose-500/15' : 'border-white/10 bg-[#0d0d0f] hover:border-white/20'}`}
                      data-testid={`tv-movie-station-${s.id}`}>
                      <TvIcon className={`w-4 h-4 ${sel ? 'text-rose-400' : 'text-gray-500'}`} />
                      <div className="flex-1 text-left">
                        <p className="text-xs text-white font-bold">{s.name}</p>
                        <p className="text-[9px] text-gray-500">{s.nation || ''}{s.preferred_genres?.length ? ` · preferisce ${s.preferred_genres.slice(0, 3).join(', ')}` : ''}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <Button onClick={handleCreate} disabled={creating || !title.trim() || !preplot.trim() || !stationId}
              className="w-full bg-gradient-to-r from-rose-500 to-pink-500 hover:opacity-95 text-white font-bold mt-2"
              data-testid="create-tv-movie-btn">
              {creating ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <Radio className="w-4 h-4 mr-1.5" />}
              Crea Film TV
            </Button>

            <p className="text-[9px] text-gray-500 text-center pt-1 leading-relaxed" data-testid="ai-hint">
              Locandina, sceneggiatura e trailer AI (3 opzioni) saranno generati nei passi successivi della pipeline V3.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
