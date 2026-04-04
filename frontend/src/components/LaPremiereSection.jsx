// CineWorld Studio's - La Prima (Premiere) Component
// Shows premiere info box on film detail page

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Slider } from '../components/ui/slider';
import { toast } from 'sonner';
import { MapPin, Clock, Calendar, Sparkles, Star, Film } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const OUTCOME_LABELS = {
  standing_ovation: { label: 'Standing Ovation', color: 'text-yellow-400', bg: 'bg-yellow-500/20 border-yellow-500/40' },
  warm_reception: { label: 'Accoglienza Calorosa', color: 'text-green-400', bg: 'bg-green-500/20 border-green-500/40' },
  mixed_reaction: { label: 'Pubblico Diviso', color: 'text-orange-400', bg: 'bg-orange-500/20 border-orange-500/40' },
  lukewarm: { label: 'Accoglienza Tiepida', color: 'text-gray-400', bg: 'bg-gray-500/20 border-gray-500/40' },
};

export const LaPremiereSection = ({ film, filmId: filmIdProp, project, api: apiProp, isOwner, onUpdate }) => {
  const [premiereData, setPremiereData] = useState(null);
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [setupOpen, setSetupOpen] = useState(false);
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('20:00');
  const [delayDays, setDelayDays] = useState(3);

  const filmId = filmIdProp || film?.id;

  // Support both: api passed as prop (FilmDetail) or from AuthContext (FilmPipeline)
  const { api: ctxApi } = React.useContext(require('../contexts').AuthContext);
  const api = apiProp || ctxApi;

  const fetchStatus = useCallback(async () => {
    if (!filmId || !api) return;
    try {
      const res = await api.get(`/la-prima/status/${filmId}`);
      setPremiereData(res.data);
    } catch (e) { /* silent */ }
  }, [filmId, api]);

  const fetchCities = useCallback(async () => {
    if (!api) return;
    try {
      const res = await api.get('/la-prima/cities');
      setCities(res.data.cities || []);
    } catch (e) { /* silent */ }
  }, [api]);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const handleEnable = async () => {
    setLoading(true);
    try {
      const res = await api.post(`/la-prima/enable/${filmId}`);
      toast.success('La Prima attivata!');
      fetchStatus();
      fetchCities();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore');
    }
    setLoading(false);
  };

  const handleSetup = async () => {
    if (!selectedCity || !selectedDate) {
      toast.error('Seleziona citta\' e data');
      return;
    }
    setLoading(true);
    const datetimeISO = `${selectedDate}T${selectedTime}:00Z`;
    try {
      const res = await api.post(`/la-prima/setup/${filmId}`, {
        city: selectedCity,
        datetime: datetimeISO,
        release_delay_days: delayDays,
      });
      toast.success(res.data.message || 'La Prima configurata!');
      setSetupOpen(false);
      fetchStatus();
      if (onUpdate) onUpdate();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore');
    }
    setLoading(false);
  };

  const premiere = premiereData?.premiere;
  const canEnable = premiereData?.can_enable;

  // Don't show for non-eligible films unless already has premiere
  if (!premiere?.enabled && !canEnable) return null;

  // Countdown calculation
  const getCountdown = () => {
    if (!premiere?.datetime) return null;
    const target = new Date(premiere.datetime);
    const now = new Date();
    const diff = target - now;
    if (diff <= 0) return 'Evento concluso';
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    if (days > 0) return `${days}g ${hours}h`;
    return `${hours}h`;
  };

  const outcomeInfo = premiere?.outcome ? OUTCOME_LABELS[premiere.outcome] : null;

  return (
    <Card data-testid="la-prima-section" className="border border-amber-500/30 bg-gradient-to-br from-amber-500/5 to-orange-500/5">
      <CardHeader className="pb-2">
        <CardTitle className="font-['Bebas_Neue'] text-lg flex items-center gap-2 text-amber-400">
          <Sparkles className="w-5 h-5" />
          La Prima
          {premiere?.enabled && premiere?.city && (
            <Badge data-testid="la-prima-status-badge" className="ml-auto text-xs bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {premiere.outcome ? 'Completata' : 'Programmata'}
            </Badge>
          )}
          {premiere?.enabled && !premiere?.city && (
            <Badge className="ml-auto text-xs bg-blue-500/20 text-blue-300 border border-blue-500/30">
              Da configurare
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Not enabled yet — show enable button */}
        {!premiere?.enabled && canEnable && isOwner && (
          <div data-testid="la-prima-enable" className="text-center py-4">
            <p className="text-sm text-gray-400 mb-3">
              Organizza un evento esclusivo di anteprima per il tuo film.
              Scegli la citta' giusta e il momento perfetto per massimizzare l'impatto.
            </p>
            <p className="text-xs text-gray-500 mb-4">
              Opzionale — Non sempre conveniente. L'impatto dipende dalla citta', dal timing e dal cast.
            </p>
            <Button
              data-testid="la-prima-enable-btn"
              onClick={handleEnable}
              disabled={loading}
              variant="outline"
              className="border-amber-500/50 text-amber-400 hover:bg-amber-500/10"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              {loading ? 'Attivazione...' : 'Attiva La Prima'}
            </Button>
          </div>
        )}

        {/* Enabled but not configured — show setup */}
        {premiere?.enabled && !premiere?.city && isOwner && (
          <div data-testid="la-prima-setup" className="text-center py-3">
            <p className="text-sm text-gray-400 mb-3">
              La Prima e' attiva! Configura citta', data e tempistica.
            </p>
            <Dialog open={setupOpen} onOpenChange={(open) => { setSetupOpen(open); if (open && cities.length === 0) fetchCities(); }}>
              <DialogTrigger asChild>
                <Button
                  data-testid="la-prima-setup-btn"
                  variant="outline"
                  className="border-amber-500/50 text-amber-400 hover:bg-amber-500/10"
                >
                  <MapPin className="w-4 h-4 mr-2" />
                  Configura La Prima
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0A0A0A] border-white/10 max-w-md">
                <DialogHeader>
                  <DialogTitle className="font-['Bebas_Neue'] text-xl text-amber-400">Configura La Prima</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-2">
                  {/* City selection */}
                  <div>
                    <label className="text-xs text-gray-400 mb-1 block">Citta'</label>
                    <Select value={selectedCity} onValueChange={setSelectedCity}>
                      <SelectTrigger data-testid="la-prima-city-select" className="bg-[#1A1A1A] border-white/10">
                        <SelectValue placeholder="Scegli citta'..." />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1A1A1A] border-white/10 max-h-60">
                        {cities.map(c => (
                          <SelectItem key={c.name} value={c.name}>
                            <span className="flex items-center gap-2">
                              <MapPin className="w-3 h-3 text-amber-400" />
                              {c.name}
                              <span className="text-gray-500 text-xs">— {c.vibe}</span>
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Date */}
                  <div>
                    <label className="text-xs text-gray-400 mb-1 block">Data</label>
                    <input
                      data-testid="la-prima-date-input"
                      type="date"
                      value={selectedDate}
                      onChange={e => setSelectedDate(e.target.value)}
                      className="w-full bg-[#1A1A1A] border border-white/10 rounded-md px-3 py-2 text-sm text-white"
                    />
                  </div>

                  {/* Time */}
                  <div>
                    <label className="text-xs text-gray-400 mb-1 block">Orario (UTC)</label>
                    <input
                      data-testid="la-prima-time-input"
                      type="time"
                      value={selectedTime}
                      onChange={e => setSelectedTime(e.target.value)}
                      className="w-full bg-[#1A1A1A] border border-white/10 rounded-md px-3 py-2 text-sm text-white"
                    />
                  </div>

                  {/* Delay days */}
                  <div>
                    <label className="text-xs text-gray-400 mb-1 block">
                      Giorni prima dell'uscita: <span className="text-amber-400 font-bold">{delayDays}</span>
                    </label>
                    <Slider
                      data-testid="la-prima-delay-slider"
                      value={[delayDays]}
                      onValueChange={v => setDelayDays(v[0])}
                      min={1} max={6} step={1}
                      className="mt-2"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>1g (poco buzz)</span>
                      <span>3g (ideale)</span>
                      <span>6g (hype cala)</span>
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    data-testid="la-prima-confirm-btn"
                    onClick={handleSetup}
                    disabled={loading || !selectedCity || !selectedDate}
                    className="bg-amber-500 hover:bg-amber-600 text-black font-bold"
                  >
                    {loading ? 'Conferma...' : 'Conferma La Prima'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        )}

        {/* Configured — show info + image placeholder */}
        {premiere?.enabled && premiere?.city && (
          <div data-testid="la-prima-info" className="space-y-3">
            {/* City + Date row */}
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-amber-400" />
                <span data-testid="la-prima-city" className="text-sm font-medium text-white">{premiere.city}</span>
              </div>
              {premiere.datetime && (
                <div className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-amber-400" />
                  <span data-testid="la-prima-datetime" className="text-sm text-gray-300">
                    {new Date(premiere.datetime).toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' })}
                    {' '}
                    {new Date(premiere.datetime).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              )}
              {premiere.release_delay_days && (
                <div className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-amber-400" />
                  <span className="text-sm text-gray-400">{premiere.release_delay_days}g prima dell'uscita</span>
                </div>
              )}
            </div>

            {/* Countdown or Outcome */}
            {!premiere.outcome && getCountdown() && (
              <div data-testid="la-prima-countdown" className="flex items-center gap-2 bg-amber-500/10 rounded-lg px-3 py-2 border border-amber-500/20">
                <Clock className="w-4 h-4 text-amber-400 animate-pulse" />
                <span className="text-sm text-amber-300">Countdown: <span className="font-bold">{getCountdown()}</span></span>
              </div>
            )}

            {outcomeInfo && (
              <div data-testid="la-prima-outcome" className={`flex items-center gap-2 rounded-lg px-3 py-2 border ${outcomeInfo.bg}`}>
                <Star className={`w-4 h-4 ${outcomeInfo.color}`} />
                <span className={`text-sm font-medium ${outcomeInfo.color}`}>{outcomeInfo.label}</span>
              </div>
            )}

            {/* IMAGE PLACEHOLDER — 16:9 ratio */}
            <div
              data-testid="la-prima-image-placeholder"
              className="relative w-full aspect-video rounded-lg overflow-hidden bg-gradient-to-br from-[#1A1A1A] to-[#0D0D0D] border border-white/5 flex items-center justify-center"
            >
              <div className="text-center space-y-2 opacity-40">
                <Film className="w-10 h-10 mx-auto text-amber-500" />
                <p className="text-xs text-gray-500 uppercase tracking-widest">Premiere Event</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default LaPremiereSection;
