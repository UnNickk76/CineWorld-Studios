// CineWorld - Sequel Pipeline (Aligned with Film Pipeline)
// Select parent film → Create sequel → Redirect to normal pipeline

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Copy, Check, Film, Loader2, ArrowRight, Star } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const posterSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

export default function SequelPipeline() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [eligibleFilms, setEligibleFilms] = useState([]);
  const [mySequels, setMySequels] = useState({ active: [], released: [] });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [subtitle, setSubtitle] = useState('');
  const [selectedFilm, setSelectedFilm] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [filmsRes, sequelsRes] = await Promise.all([
        api.get('/sequel-pipeline/eligible-films'),
        api.get('/sequel-pipeline/my'),
      ]);
      setEligibleFilms(filmsRes.data.films || []);
      setMySequels(sequelsRes.data || { active: [], released: [] });
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  const createSequel = async () => {
    if (!selectedFilm || !subtitle.trim()) return toast.error('Seleziona un film e inserisci un sottotitolo');
    setActionLoading(true);
    try {
      await api.post('/sequel-pipeline/create', { parent_film_id: selectedFilm.id, subtitle });
      toast.success('Sequel creato! Vai alla Pipeline per continuare.');
      navigate('/pipeline');
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setActionLoading(false);
  };

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
      <div className="max-w-2xl mx-auto px-3">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4 mt-2">
          <div className="p-2.5 bg-amber-600/20 rounded-xl border border-amber-600/30">
            <Copy className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <h1 className="font-['Bebas_Neue'] text-2xl text-amber-500" data-testid="sequel-pipeline-title">Crea Sequel</h1>
            <p className="text-xs text-gray-500">Scegli il film da continuare, poi prosegui nella Pipeline Film</p>
          </div>
        </div>

        {/* Active Sequel Projects in Pipeline */}
        {mySequels.active?.length > 0 && (
          <div className="mb-4">
            <h3 className="text-xs font-semibold text-amber-400 mb-2 uppercase tracking-wider">Sequel in lavorazione</h3>
            <div className="space-y-1.5">
              {mySequels.active.map(s => (
                <Card key={s.id} className="bg-amber-500/5 border-amber-500/20 cursor-pointer hover:bg-amber-500/10 transition-colors"
                  onClick={() => navigate('/pipeline')} data-testid={`active-sequel-${s.id}`}>
                  <CardContent className="p-2.5 flex items-center gap-2.5">
                    <Film className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold truncate">{s.title}</p>
                      <p className="text-[10px] text-gray-500">Cap. {s.sequel_number} | {s.status}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-amber-400/50" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Create New Sequel */}
        <Card className="bg-[#111113] border-amber-600/20 mb-4" data-testid="sequel-select-form">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-['Bebas_Neue'] text-amber-500">Nuovo Sequel</CardTitle>
            <p className="text-[10px] text-gray-500">Il sequel entrera nella pipeline film standard con cast pre-compilato</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {eligibleFilms.length === 0 ? (
              <div className="text-center py-6">
                <Film className="w-10 h-10 text-gray-600 mx-auto mb-2" />
                <p className="text-xs text-gray-500">Nessun film disponibile. Completa un film prima!</p>
              </div>
            ) : (
              <>
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {eligibleFilms.map(f => (
                    <div key={f.id}
                      className={`flex items-center gap-2.5 p-2 rounded-lg cursor-pointer border transition-all ${
                        selectedFilm?.id === f.id ? 'bg-amber-500/15 border-amber-500/30' : 'bg-white/[0.02] border-white/5 hover:bg-white/5'
                      }`}
                      onClick={() => setSelectedFilm(f)}
                      data-testid={`eligible-film-${f.id}`}
                    >
                      {f.poster_url ? (
                        <img src={posterSrc(f.poster_url)} alt="" className="w-8 h-12 rounded object-cover" loading="lazy" />
                      ) : (
                        <div className="w-8 h-12 rounded bg-amber-500/10 flex items-center justify-center"><Film className="w-4 h-4 text-amber-500/50" /></div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold truncate">{f.title}</p>
                        <p className="text-[10px] text-gray-500">{f.genre} | Q: {f.quality_score || '?'}/100</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <Badge className="bg-amber-600/20 text-amber-400 text-[9px]">Cap. {f.next_sequel_number}</Badge>
                        <p className="text-[9px] text-green-400 mt-0.5">+{f.saga_bonus_percent}%</p>
                      </div>
                      {selectedFilm?.id === f.id && <Check className="w-4 h-4 text-amber-400 flex-shrink-0" />}
                    </div>
                  ))}
                </div>
                {selectedFilm && (
                  <>
                    <Input
                      placeholder={`${selectedFilm.title}: ...sottotitolo`}
                      value={subtitle}
                      onChange={e => setSubtitle(e.target.value)}
                      className="bg-white/5 border-white/10 text-white"
                      data-testid="sequel-subtitle-input"
                    />
                    <div className="bg-amber-500/5 rounded-lg p-2 border border-amber-500/10 text-[10px] text-gray-400 space-y-0.5">
                      <p><span className="text-amber-400 font-medium">Titolo: </span>{selectedFilm.title}: {subtitle || '...'}</p>
                      <p><span className="text-green-400 font-medium">Saga bonus: </span>+{selectedFilm.saga_bonus_percent}% qualita</p>
                      <p><span className="text-purple-400 font-medium">Cast: </span>Ereditato dal film originale (modificabile)</p>
                    </div>
                    <Button
                      className="w-full bg-amber-600 hover:bg-amber-700 text-white"
                      onClick={createSequel}
                      disabled={actionLoading || !subtitle.trim()}
                      data-testid="create-sequel-btn"
                    >
                      {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                      Crea Sequel e Vai alla Pipeline
                    </Button>
                  </>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Released Sequels */}
        {mySequels.released?.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Sequel Rilasciati</h3>
            <div className="space-y-1.5">
              {mySequels.released.map(s => (
                <Card key={s.id} className="bg-[#111113] border-white/5 cursor-pointer hover:bg-white/5 transition-colors"
                  onClick={() => navigate(`/films/${s.id}`)} data-testid={`released-sequel-${s.id}`}>
                  <CardContent className="p-2.5 flex items-center gap-2.5">
                    {s.poster_url ? (
                      <img src={posterSrc(s.poster_url)} alt="" className="w-8 h-12 rounded object-cover" loading="lazy" />
                    ) : (
                      <div className="w-8 h-12 rounded bg-yellow-500/10 flex items-center justify-center"><Star className="w-3 h-3 text-yellow-500/50" /></div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold truncate">{s.title}</p>
                      <p className="text-[10px] text-gray-500">Cap. {s.sequel_number} | {s.genre}</p>
                    </div>
                    <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">{s.quality_score}/100</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
