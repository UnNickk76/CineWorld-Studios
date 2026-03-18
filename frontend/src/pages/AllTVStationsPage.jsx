// CineWorld - All TV Stations (Public Listing)
import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Radio, Globe, Eye, Film, Loader2 } from 'lucide-react';

export default function AllTVStationsPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/tv-stations/public/all').then(r => {
      setStations(r.data.stations || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [api]);

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center pt-16">
      <Loader2 className="w-8 h-8 text-red-400 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white pb-20 pt-16">
      <div className="max-w-2xl mx-auto px-3">
        <div className="flex items-center gap-3 mb-4 mt-2">
          <div className="p-2 bg-red-500/20 rounded-xl border border-red-500/30">
            <Radio className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <h1 className="font-['Bebas_Neue'] text-2xl text-red-400" data-testid="all-tv-title">Emittenti TV</h1>
            <p className="text-[10px] text-gray-500">Tutte le emittenti televisive dei giocatori</p>
          </div>
        </div>

        {stations.length === 0 ? (
          <div className="text-center py-12">
            <Radio className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Nessuna emittente attiva</p>
            <p className="text-gray-600 text-xs mt-1">Sii il primo a crearne una!</p>
          </div>
        ) : (
          <div className="space-y-2">
            {stations.map(s => (
              <Card
                key={s.id}
                className="bg-[#111113] border-white/5 hover:border-red-500/20 cursor-pointer transition-all"
                onClick={() => navigate(`/tv-station/${s.id}`)}
                data-testid={`public-station-${s.id}`}
              >
                <CardContent className="p-3 flex items-center gap-3">
                  <div className="p-2 bg-red-500/10 rounded-lg flex-shrink-0">
                    <Radio className="w-5 h-5 text-red-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold truncate">{s.station_name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Globe className="w-2.5 h-2.5 text-gray-500" />
                      <span className="text-[10px] text-gray-500">{s.nation}</span>
                      <span className="text-[10px] text-gray-600">|</span>
                      <span className="text-[10px] text-gray-400">{s.owner_nickname}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <div className="text-center">
                      <p className="text-xs font-bold text-cyan-400">{s.current_share || 0}%</p>
                      <p className="text-[8px] text-gray-600">Share</p>
                    </div>
                    <div className="text-center">
                      <Badge className="bg-white/5 text-gray-400 text-[9px]">
                        <Film className="w-2.5 h-2.5 mr-0.5" /> {s.content_count || 0}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
