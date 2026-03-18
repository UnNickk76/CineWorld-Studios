// CineWorld - Emittente TV Page
// TV Network management: broadcast schedule, ratings, revenue

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Radio, Tv, Sparkles, Lock, Clock, Users, DollarSign, TrendingUp, Loader2, Plus, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TIMESLOTS = {
  daytime: { label: 'Daytime', time: '10:00-18:00', color: 'yellow', audienceMult: '0.5x', costDay: '$5,000' },
  prime_time: { label: 'Prime Time', time: '20:00-23:00', color: 'red', audienceMult: '1.5x', costDay: '$15,000' },
  late_night: { label: 'Late Night', time: '23:00-02:00', color: 'purple', audienceMult: '0.8x', costDay: '$8,000' },
};

export default function EmittenteTVPage() {
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [emittente, setEmittente] = useState(null);
  const [hasEmittente, setHasEmittente] = useState(false);
  const [completedSeries, setCompletedSeries] = useState([]);
  const [broadcasts, setBroadcasts] = useState([]);
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [unlockRes, seriesRes, animeRes] = await Promise.all([
        api.get('/production-studios/unlock-status'),
        api.get('/series-pipeline/my?series_type=tv_series'),
        api.get('/series-pipeline/my?series_type=anime'),
      ]);

      setHasEmittente(unlockRes.data.has_emittente_tv);

      if (unlockRes.data.has_emittente_tv) {
        // Load broadcasts
        try {
          const bRes = await api.get('/emittente-tv/broadcasts');
          setBroadcasts(bRes.data.broadcasts || []);
          setEmittente(bRes.data.emittente || null);
        } catch {
          setEmittente(unlockRes.data.studios?.emittente_tv || null);
        }
      }

      const allSeries = [
        ...(seriesRes.data.series || []).filter(s => s.status === 'completed').map(s => ({ ...s, label: 'Serie TV' })),
        ...(animeRes.data.series || []).filter(s => s.status === 'completed').map(s => ({ ...s, label: 'Anime' })),
      ];
      setCompletedSeries(allSeries);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [api]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
    </div>
  );

  if (!hasEmittente) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
        <div className="max-w-lg mx-auto px-4 flex flex-col items-center justify-center min-h-[60vh]">
          <div className="p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20 mb-4">
            <Radio className="w-12 h-12 text-emerald-400" />
          </div>
          <h1 className="font-['Bebas_Neue'] text-3xl text-emerald-400 mb-2" data-testid="emittente-locked-title">Emittente TV</h1>
          <p className="text-sm text-gray-400 text-center mb-6 max-w-xs">
            Costruisci la tua emittente televisiva per trasmettere serie TV e anime. Guadagna dalle entrate pubblicitarie!
          </p>
          <Card className="bg-[#111113] border-emerald-500/20 w-full max-w-sm">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Livello richiesto</span>
                <span className="text-sm font-bold text-emerald-400">18</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Fama richiesta</span>
                <span className="text-sm font-bold text-emerald-400">200</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Costo costruzione</span>
                <span className="text-sm font-bold text-yellow-400">$5,000,000</span>
              </div>
              <Button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white" onClick={() => navigate('/infrastructure')} data-testid="go-to-infra-btn">
                <Lock className="w-4 h-4 mr-2" /> Vai alle Infrastrutture
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
      <div className="max-w-2xl mx-auto px-3">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4 mt-2">
          <div className="p-2.5 bg-emerald-500/20 rounded-xl border border-emerald-500/30">
            <Radio className="w-6 h-6 text-emerald-400" />
          </div>
          <div className="flex-1">
            <h1 className="font-['Bebas_Neue'] text-2xl text-emerald-400" data-testid="emittente-title">La Tua TV</h1>
            <p className="text-xs text-gray-500">Gestisci il palinsesto della tua emittente</p>
          </div>
          {emittente && (
            <Badge className="bg-emerald-500/20 text-emerald-400">Liv. {emittente.level || 1}</Badge>
          )}
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <Card className="bg-[#111113] border-white/5">
            <CardContent className="p-2 text-center">
              <Users className="w-4 h-4 text-blue-400 mx-auto mb-1" />
              <p className="text-lg font-bold text-white">{(emittente?.total_audience_reached || 0).toLocaleString()}</p>
              <p className="text-[9px] text-gray-500">Audience</p>
            </CardContent>
          </Card>
          <Card className="bg-[#111113] border-white/5">
            <CardContent className="p-2 text-center">
              <DollarSign className="w-4 h-4 text-green-400 mx-auto mb-1" />
              <p className="text-lg font-bold text-white">${(emittente?.total_ad_revenue || 0).toLocaleString()}</p>
              <p className="text-[9px] text-gray-500">Ricavi Ads</p>
            </CardContent>
          </Card>
          <Card className="bg-[#111113] border-white/5">
            <CardContent className="p-2 text-center">
              <Tv className="w-4 h-4 text-purple-400 mx-auto mb-1" />
              <p className="text-lg font-bold text-white">{broadcasts.length}</p>
              <p className="text-[9px] text-gray-500">In Onda</p>
            </CardContent>
          </Card>
        </div>

        {/* Timeslots / Schedule */}
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Palinsesto</h3>
        <div className="space-y-2 mb-4">
          {Object.entries(TIMESLOTS).map(([key, slot]) => {
            const broadcast = broadcasts.find(b => b.timeslot === key);
            return (
              <Card key={key} className={`bg-[#111113] border-${slot.color}-500/10`} data-testid={`timeslot-${key}`}>
                <CardContent className="p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <Clock className={`w-4 h-4 text-${slot.color}-400`} />
                      <span className="text-sm font-bold">{slot.label}</span>
                      <span className="text-[10px] text-gray-500">{slot.time}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] text-gray-500">Audience {slot.audienceMult}</span>
                      <span className="text-[9px] text-yellow-400">{slot.costDay}/g</span>
                    </div>
                  </div>
                  {broadcast ? (
                    <div className="bg-white/[0.03] rounded-lg p-2 flex items-center gap-2">
                      <div className="w-8 h-10 rounded bg-emerald-500/10 flex items-center justify-center">
                        {broadcast.type === 'anime' ? <Sparkles className="w-4 h-4 text-orange-400" /> : <Tv className="w-4 h-4 text-blue-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{broadcast.series_title}</p>
                        <p className="text-[10px] text-gray-500">Ep. {broadcast.current_episode}/{broadcast.total_episodes}</p>
                      </div>
                      <Badge className="bg-green-500/20 text-green-400 text-[9px]">In Onda</Badge>
                    </div>
                  ) : (
                    <div className="bg-white/[0.02] rounded-lg p-3 flex items-center justify-center border border-dashed border-white/10">
                      <p className="text-xs text-gray-600">Slot libero</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Available Series to Broadcast */}
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Serie Disponibili</h3>
        {completedSeries.length === 0 ? (
          <Card className="bg-[#111113] border-white/5">
            <CardContent className="p-6 text-center">
              <Tv className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              <p className="text-xs text-gray-500">Nessuna serie completata. Produci una Serie TV o un Anime per trasmetterli!</p>
              <div className="flex gap-2 mt-3 justify-center">
                <Button size="sm" variant="outline" className="text-xs border-blue-500/30 text-blue-400" onClick={() => navigate('/create-series')} data-testid="go-to-series-btn">
                  <Tv className="w-3 h-3 mr-1" /> Serie TV
                </Button>
                <Button size="sm" variant="outline" className="text-xs border-orange-500/30 text-orange-400" onClick={() => navigate('/create-anime')} data-testid="go-to-anime-btn">
                  <Sparkles className="w-3 h-3 mr-1" /> Anime
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {completedSeries.map(s => (
              <Card key={s.id} className="bg-[#111113] border-white/5" data-testid={`available-series-${s.id}`}>
                <CardContent className="p-3 flex items-center gap-3">
                  <div className={`w-10 h-14 rounded flex items-center justify-center ${s.type === 'anime' ? 'bg-orange-500/10' : 'bg-blue-500/10'}`}>
                    {s.type === 'anime' ? <Sparkles className="w-5 h-5 text-orange-400" /> : <Tv className="w-5 h-5 text-blue-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold truncate">{s.title}</p>
                    <p className="text-[10px] text-gray-500">{s.label} - {s.genre_name} - {s.num_episodes} ep.</p>
                  </div>
                  <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px]">{s.quality_score}/100</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Info Card */}
        <Card className="bg-[#111113] border-emerald-500/10 mt-4">
          <CardContent className="p-3">
            <p className="text-[10px] text-gray-500 leading-relaxed">
              L'Emittente TV trasmette le tue serie TV e anime. Assegna una serie a uno slot del palinsesto per generare ascolti e ricavi pubblicitari giornalieri. 
              Prime Time genera la massima audience (1.5x), Daytime è economico (0.5x), Late Night è per il pubblico di nicchia (0.8x).
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
