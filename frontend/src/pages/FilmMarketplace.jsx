import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, useTranslations } from '../contexts';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { toast } from 'sonner';
import {
  Store, Film, DollarSign, Tag, Clock, User, MapPin, Star,
  ShoppingCart, Loader2, RefreshCw, AlertTriangle, Clapperboard,
  Sparkles, TrendingUp, Search
} from 'lucide-react';
import { Input } from '../components/ui/input';

const PHASE_LABELS = {
  'proposed': 'Proposte',
  'casting': 'Casting',
  'screenplay': 'Sceneggiatura',
  'pre_production': 'Pre-Produzione',
  'shooting': 'Riprese'
};

const PHASE_COLORS = {
  'proposed': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'casting': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  'screenplay': 'bg-green-500/20 text-green-400 border-green-500/30',
  'pre_production': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'shooting': 'bg-red-500/20 text-red-400 border-red-500/30'
};

const FilmMarketplace = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useTranslations();
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(null);
  const [selectedFilm, setSelectedFilm] = useState(null);
  const [search, setSearch] = useState('');

  const fetchMarketplace = async () => {
    setLoading(true);
    try {
      const res = await api.get('/film-pipeline/marketplace');
      setFilms(res.data.films || []);
    } catch (e) {
      toast.error('Errore nel caricamento del mercato');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMarketplace(); }, []);

  const buyFilm = async (film) => {
    if (user?.funds < film.sale_price) {
      toast.error(`Fondi insufficienti! Servono $${film.sale_price.toLocaleString()}`);
      return;
    }
    setBuying(film.id);
    try {
      const res = await api.post(`/film-pipeline/marketplace/buy/${film.id}`);
      toast.success(res.data.message);
      setSelectedFilm(null);
      refreshUser();
      fetchMarketplace();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore nell\'acquisto');
    } finally {
      setBuying(null);
    }
  };

  const filtered = films.filter(f =>
    f.title?.toLowerCase().includes(search.toLowerCase()) ||
    f.genre?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#0A0A0B] pt-16 pb-20 px-3 sm:px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-xl">
              <Store className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl tracking-wide">
                {language === 'it' ? 'Mercato Film' : 'Film Market'}
              </h1>
              <p className="text-xs text-gray-400">
                {language === 'it' ? 'Acquista i diritti di film scartati da altri produttori' : 'Buy rights to films discarded by other producers'}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchMarketplace} disabled={loading} data-testid="marketplace-refresh">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder={language === 'it' ? 'Cerca per titolo o genere...' : 'Search by title or genre...'}
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9 bg-black/30 border-gray-700 text-white"
            data-testid="marketplace-search"
          />
        </div>

        {/* Film Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-amber-400" />
          </div>
        ) : filtered.length === 0 ? (
          <Card className="bg-[#1A1A1A] border-white/10">
            <CardContent className="p-8 text-center">
              <Store className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <h3 className="text-lg font-semibold mb-1">
                {search ? (language === 'it' ? 'Nessun risultato' : 'No results') : (language === 'it' ? 'Il mercato e vuoto' : 'Market is empty')}
              </h3>
              <p className="text-sm text-gray-400">
                {search
                  ? (language === 'it' ? 'Prova con altri termini di ricerca' : 'Try different search terms')
                  : (language === 'it' ? 'Quando altri produttori scartano un film, apparira qui per l\'acquisto!' : 'When other producers discard films, they will appear here!')}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map(film => (
              <Card
                key={film.id}
                className="bg-[#1A1A1A] border-white/10 hover:border-amber-500/30 transition-all cursor-pointer"
                onClick={() => setSelectedFilm(film)}
                data-testid={`market-film-${film.id}`}
              >
                <CardContent className="p-3">
                  {/* Poster + Info */}
                  <div className="flex gap-3">
                    {film.poster_url ? (
                      <img src={film.poster_url} alt={film.title} className="w-16 h-24 rounded object-cover flex-shrink-0" />
                    ) : (
                      <div className="w-16 h-24 rounded bg-gray-800 flex items-center justify-center flex-shrink-0">
                        <Film className="w-6 h-6 text-gray-600" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-sm truncate">{film.title}</h3>
                      <div className="flex items-center gap-1.5 mt-1">
                        <Badge variant="outline" className="text-[9px] h-4 px-1.5">{film.genre}</Badge>
                        {film.subgenre && <Badge variant="outline" className="text-[9px] h-4 px-1.5">{film.subgenre}</Badge>}
                      </div>
                      <div className="flex items-center gap-1 mt-1.5 text-[10px] text-gray-400">
                        <User className="w-3 h-3" />
                        <span>{film.discarded_by_nickname || 'Produttore'}</span>
                      </div>
                      {film.pre_imdb_score && (
                        <div className="flex items-center gap-1 mt-1 text-[10px]">
                          <Star className="w-3 h-3 text-yellow-400" />
                          <span className="text-yellow-400">Pre-IMDb: {film.pre_imdb_score.toFixed(1)}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Phase + Price */}
                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/5">
                    <Badge className={`text-[9px] h-5 ${PHASE_COLORS[film.status_before_discard] || PHASE_COLORS['proposed']}`}>
                      {PHASE_LABELS[film.status_before_discard] || film.status_before_discard || 'Proposte'}
                    </Badge>
                    <div className="flex items-center gap-1">
                      <DollarSign className="w-3.5 h-3.5 text-green-400" />
                      <span className="font-bold text-green-400 text-sm">${film.sale_price?.toLocaleString()}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Detail Dialog */}
        <Dialog open={!!selectedFilm} onOpenChange={() => setSelectedFilm(null)}>
          <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md">
            {selectedFilm && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Clapperboard className="w-5 h-5 text-amber-400" />
                    {selectedFilm.title}
                  </DialogTitle>
                  <DialogDescription>
                    {language === 'it' ? 'Dettagli del film in vendita' : 'Film details for sale'}
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-3 mt-2">
                  {selectedFilm.poster_url && (
                    <img src={selectedFilm.poster_url} alt={selectedFilm.title} className="w-full h-48 object-cover rounded-lg" />
                  )}

                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="bg-black/30 rounded-lg p-2">
                      <span className="text-gray-400 text-xs">Genere</span>
                      <p className="font-medium">{selectedFilm.genre}</p>
                    </div>
                    <div className="bg-black/30 rounded-lg p-2">
                      <span className="text-gray-400 text-xs">Sottogenere</span>
                      <p className="font-medium">{selectedFilm.subgenre || '-'}</p>
                    </div>
                    <div className="bg-black/30 rounded-lg p-2">
                      <span className="text-gray-400 text-xs">Location</span>
                      <p className="font-medium">{selectedFilm.location_name || '-'}</p>
                    </div>
                    <div className="bg-black/30 rounded-lg p-2">
                      <span className="text-gray-400 text-xs">Fase raggiunta</span>
                      <p className="font-medium">{PHASE_LABELS[selectedFilm.status_before_discard] || 'Proposte'}</p>
                    </div>
                  </div>

                  {selectedFilm.pre_imdb_score && (
                    <div className="flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-2">
                      <Star className="w-4 h-4 text-yellow-400" />
                      <span className="text-sm">Pre-IMDb: <strong className="text-yellow-400">{selectedFilm.pre_imdb_score.toFixed(1)}</strong></span>
                    </div>
                  )}

                  {selectedFilm.pre_screenplay && (
                    <div className="bg-black/30 rounded-lg p-2">
                      <span className="text-gray-400 text-xs">Sinossi</span>
                      <p className="text-xs text-gray-300 mt-1 line-clamp-3">{selectedFilm.pre_screenplay}</p>
                    </div>
                  )}

                  {selectedFilm.cast && Object.keys(selectedFilm.cast).length > 0 && (
                    <div className="bg-black/30 rounded-lg p-2">
                      <span className="text-gray-400 text-xs">Cast incluso</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedFilm.cast.director && (
                          <Badge className="text-[9px] bg-purple-500/20 text-purple-400">Regista: {selectedFilm.cast.director.name}</Badge>
                        )}
                        {selectedFilm.cast.screenwriter && (
                          <Badge className="text-[9px] bg-blue-500/20 text-blue-400">Sceneg: {selectedFilm.cast.screenwriter.name}</Badge>
                        )}
                        {selectedFilm.cast.actors?.map((a, i) => (
                          <Badge key={i} className="text-[9px] bg-green-500/20 text-green-400">{a.name}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                    <div>
                      <span className="text-xs text-gray-400">{language === 'it' ? 'Prezzo di acquisto' : 'Purchase price'}</span>
                      <p className="text-xl font-bold text-green-400">${selectedFilm.sale_price?.toLocaleString()}</p>
                      <span className="text-[10px] text-gray-500">{language === 'it' ? 'Il 70% va al produttore originale' : '70% goes to original producer'}</span>
                    </div>
                    <Button
                      className="bg-green-600 hover:bg-green-500 text-white"
                      onClick={() => buyFilm(selectedFilm)}
                      disabled={buying === selectedFilm.id || (user?.funds || 0) < selectedFilm.sale_price}
                      data-testid="buy-film-btn"
                    >
                      {buying === selectedFilm.id ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-1" />
                      ) : (
                        <ShoppingCart className="w-4 h-4 mr-1" />
                      )}
                      {language === 'it' ? 'Acquista' : 'Buy'}
                    </Button>
                  </div>

                  {(user?.funds || 0) < selectedFilm.sale_price && (
                    <div className="flex items-center gap-2 text-red-400 text-xs">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>{language === 'it' ? 'Fondi insufficienti per questo acquisto' : 'Insufficient funds for this purchase'}</span>
                    </div>
                  )}

                  <p className="text-[10px] text-gray-500 text-center">
                    {language === 'it'
                      ? 'Acquistando, il film entrera nella tua pipeline dalla fase in cui era stato lasciato.'
                      : 'By purchasing, the film enters your pipeline from the phase it was left in.'}
                  </p>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default FilmMarketplace;
