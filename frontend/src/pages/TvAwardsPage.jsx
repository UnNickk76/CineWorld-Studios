// CineWorld - TV Awards Page (FASE 3)
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Trophy, Loader2 } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';

const API = process.env.REACT_APP_BACKEND_URL;

export default function TvAwardsPage() {
  const navigate = useNavigate();
  const token = localStorage.getItem('cineworld_token');
  const headers = { Authorization: `Bearer ${token}` };

  const [year, setYear] = useState(new Date().getFullYear());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    axios.get(`${API}/api/tv-awards/leaderboard?year=${year}`, { headers })
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year]);

  const cats = data?.categories || [];
  const lb = data?.leaderboard || {};

  return (
    <div className="min-h-screen bg-[#0A0A0B] p-3 pb-24" data-testid="tv-awards-page">
      <div className="max-w-md mx-auto space-y-4">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={() => navigate(-1)} className="text-gray-400" data-testid="back-btn">
            <ArrowLeft className="w-4 h-4 mr-1" /> Indietro
          </Button>
          <div className="flex items-center gap-2 ml-auto">
            <Trophy className="w-5 h-5 text-amber-400" />
            <h1 className="font-['Bebas_Neue'] text-lg text-white tracking-widest">TV AWARDS</h1>
          </div>
        </div>

        <Card className="bg-gradient-to-br from-amber-500/15 to-yellow-500/10 border-amber-500/30">
          <CardContent className="p-3">
            <p className="text-[11px] text-amber-100 leading-relaxed">
              I migliori Film TV dell'anno per CWSv. Categoria, regia, attori — direttamente dalla tua programmazione.
            </p>
            <div className="mt-2 flex items-center gap-2">
              <label className="text-[10px] text-amber-300/80">Anno:</label>
              <select value={year} onChange={(e) => setYear(parseInt(e.target.value))} className="bg-[#0d0d0f] border border-white/10 rounded px-2 py-1 text-xs text-white" data-testid="tv-awards-year-select">
                {[2026, 2025, 2024].map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
          </CardContent>
        </Card>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
          </div>
        )}

        {!loading && cats.map(cat => {
          const arr = lb[cat.key] || [];
          return (
            <Card key={cat.key} className="bg-[#111113] border-white/5" data-testid={`tv-awards-${cat.key}`}>
              <CardContent className="p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{cat.icon}</span>
                  <p className="text-[12px] font-bold text-white tracking-wide uppercase">{cat.label}</p>
                </div>
                {arr.length === 0 ? (
                  <p className="text-[10px] text-gray-500 italic">Nessun candidato per il {year}</p>
                ) : (
                  <div className="space-y-1.5">
                    {arr.slice(0, 5).map((item, i) => (
                      <div key={item.film_id || item.id || i} className="flex items-center gap-2 p-1.5 rounded bg-white/3 border border-white/5">
                        <span className={`text-[14px] font-bold w-5 text-center ${i === 0 ? 'text-amber-400' : i === 1 ? 'text-gray-300' : i === 2 ? 'text-amber-700' : 'text-gray-500'}`}>{i + 1}</span>
                        {item.poster_url && <img src={item.poster_url} alt="" className="w-6 h-9 rounded object-cover" />}
                        <div className="flex-1 min-w-0">
                          <p className="text-[11px] text-white font-bold truncate">{item.title || item.name}</p>
                          <p className="text-[9px] text-gray-500 truncate">{item.station ? `📺 ${item.station}` : item.films ? `${item.films} film TV` : ''}</p>
                        </div>
                        <span className="text-[10px] font-black text-emerald-400">{item.cwsv_display || item.score?.toFixed?.(1) || '—'}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
