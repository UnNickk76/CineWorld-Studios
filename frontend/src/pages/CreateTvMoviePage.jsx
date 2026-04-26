// CineWorld Studio's — Pagina creazione "Film per la TV"
// Permette al player con TV station di creare un film TV scegliendo subito la stazione di destinazione.
// Riusa la pipeline V3 caricando il progetto creato con flag is_tv_movie=True.

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Radio, ArrowLeft, Tv as TvIcon, Loader2, Sparkles, Lock, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const GENRES = [
  'Azione', 'Avventura', 'Commedia', 'Dramma', 'Thriller', 'Horror',
  'Romantico', 'Fantascienza', 'Fantasy', 'Mistero', 'Crime', 'Documentario',
  'Biografico', 'Storico', 'Musicale', 'Western', 'Famiglia',
];

export default function CreateTvMoviePage() {
  const navigate = useNavigate();
  const token = localStorage.getItem('cineworld_token');
  const headers = { Authorization: `Bearer ${token}` };

  const [loading, setLoading] = useState(true);
  const [eligible, setEligible] = useState(false);
  const [stations, setStations] = useState([]);
  const [costInfo, setCostInfo] = useState(null);

  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState(GENRES[0]);
  const [preplot, setPreplot] = useState('');
  const [stationId, setStationId] = useState('');
  const [creating, setCreating] = useState(false);
  const [bonusInfo, setBonusInfo] = useState(null);

  // Re-check bonus genere↔stile ogni volta che genere o stazione cambiano
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stationId, genre]);

  useEffect(() => {
    (async () => {
      try {
        const [r1, r2] = await Promise.all([
          axios.get(`${API}/api/tv-movies/check-eligibility`, { headers }),
          axios.get(`${API}/api/tv-movies/cost-modifier`, { headers }),
        ]);
        setEligible(r1.data.eligible);
        setStations(r1.data.stations || []);
        if (r1.data.stations?.length) setStationId(r1.data.stations[0].id);
        setCostInfo(r2.data);
      } catch (e) {
        toast.error('Errore caricamento');
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
        preplot: preplot.trim(),
        target_station_id: stationId,
      }, { headers });
      toast.success(`"${title}" creato! Ora avanza nella pipeline.`);
      // Naviga alla pipeline V3 con il progetto pre-selezionato
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

        {/* Info banner */}
        {costInfo && (
          <Card className="bg-gradient-to-br from-rose-500/15 to-pink-500/10 border-rose-500/30">
            <CardContent className="p-3 space-y-1">
              <div className="flex items-center gap-1.5 text-rose-300">
                <Sparkles className="w-3.5 h-3.5" />
                <span className="text-[11px] font-bold">PIPELINE TV — VANTAGGI</span>
              </div>
              <ul className="text-[10px] text-rose-100/80 space-y-0.5 leading-relaxed pl-1">
                <li>• Costi ridotti del <span className="font-bold text-white">-{costInfo.discount_pct}%</span> rispetto a un film cinema</li>
                <li>• Max <span className="font-bold text-white">{costInfo.max_release_cp} CP</span> al rilascio finale</li>
                <li>• Max <span className="font-bold text-white">{costInfo.max_speedup_cp} CP</span> per velocizzazioni</li>
                <li>• Niente La Prima, niente cinema → uscita diretta in TV</li>
                <li>• Hype +15 alla creazione (visibilità immediata)</li>
              </ul>
            </CardContent>
          </Card>
        )}

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
                {GENRES.map(g => <option key={g} value={g}>{g}</option>)}
              </select>
              {/* FASE 2: indicatore bonus genere↔stile */}
              {bonusInfo && bonusInfo.matches && (
                <div className="mt-1.5 flex items-center gap-1.5 px-2 py-1 rounded bg-emerald-500/15 border border-emerald-500/30" data-testid="genre-style-bonus-active">
                  <Sparkles className="w-3 h-3 text-emerald-400" />
                  <span className="text-[10px] text-emerald-300 font-bold">+{bonusInfo.bonus_pct}% CWSv (genere preferito da {bonusInfo.station_name})</span>
                </div>
              )}
              {bonusInfo && !bonusInfo.matches && bonusInfo.preferred_genres?.length > 0 && (
                <p className="mt-1 text-[9px] text-gray-500" data-testid="genre-style-hint">{bonusInfo.station_name} preferisce: {bonusInfo.preferred_genres.join(', ')}</p>
              )}
            </div>

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
                        <p className="text-[9px] text-gray-500">Lv {s.level} · {s.style}</p>
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
