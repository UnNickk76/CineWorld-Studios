// CineWorld - TV Movie Schedule Phase
// Sostituisce La Prima + Distribution per i film TV. Permette di scegliere data/ora airing + slot.
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Radio, Clock, Calendar, Loader2, Check, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const SLOTS = [
  { key: 'prime',   label: 'Prime Time', range: '21:00-23:00', share: 'Max share', cost: '100%' },
  { key: 'daytime', label: 'Daytime',    range: '14:00-18:00', share: '70% share', cost: '50%' },
  { key: 'late',    label: 'Late Night', range: '23:00-02:00', share: '50% share', cost: '30%' },
  { key: 'morning', label: 'Morning',    range: '08:00-12:00', share: '40% share', cost: '20%' },
];

export default function TvMovieSchedulePhase({ selected, onAdvance, loading, currentStep }) {
  const token = localStorage.getItem('cineworld_token');
  const headers = { Authorization: `Bearer ${token}` };

  const initialDate = selected.tv_air_datetime ? new Date(selected.tv_air_datetime) : null;
  const [date, setDate] = useState(initialDate ? initialDate.toISOString().slice(0, 10) : '');
  const [time, setTime] = useState(initialDate ? initialDate.toISOString().slice(11, 16) : '21:00');
  const [slot, setSlot] = useState(selected.tv_time_slot || 'prime');
  const [saving, setSaving] = useState(false);
  const [releaseTypeSet, setReleaseTypeSet] = useState(!!selected.release_type);

  // Auto-imposta release_type='tv_direct' (al posto di 'direct'/'premiere')
  useEffect(() => {
    if (releaseTypeSet) return;
    (async () => {
      try {
        await axios.post(`${API}/api/pipeline-v3/films/${selected.id}/set-release-type`, { release_type: 'direct' }, { headers });
        setReleaseTypeSet(true);
      } catch (_) { /* ignore */ }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected.id]);

  const minDateTime = new Date(Date.now() + 60 * 60 * 1000).toISOString().slice(0, 10);

  const saveAiring = async () => {
    if (!date || !time) {
      toast.error('Imposta data e ora');
      return;
    }
    setSaving(true);
    try {
      const dt = new Date(`${date}T${time}:00`).toISOString();
      await axios.post(`${API}/api/tv-movies/${selected.id}/schedule-airing`, {
        air_datetime: dt,
        time_slot: slot,
      }, { headers });
      toast.success('Airing programmato');
      // Avanza direttamente a release_pending (skip la_prima + distribution)
      if (currentStep === 'la_prima' || currentStep === 'marketing') {
        await onAdvance('release_pending');
      } else if (currentStep === 'distribution') {
        await onAdvance('release_pending');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore programmazione');
    }
    setSaving(false);
  };

  return (
    <div className="p-3 space-y-3" data-testid="tv-movie-schedule-phase">
      <div className="flex items-center gap-2">
        <Radio className="w-5 h-5 text-rose-400" />
        <h3 className="font-['Bebas_Neue'] text-base text-white tracking-widest">PROGRAMMAZIONE TV</h3>
      </div>

      <Card className="bg-gradient-to-br from-rose-500/15 to-pink-500/10 border-rose-500/30">
        <CardContent className="p-3">
          <p className="text-[11px] text-rose-100 leading-relaxed">
            Il film andra' in onda su <span className="font-bold text-white">{selected.target_station_name || 'la tua TV'}</span>.
            Niente La Prima, niente cinema — uscita diretta in palinsesto. Scegli quando trasmetterlo.
          </p>
        </CardContent>
      </Card>

      <Card className="bg-[#111113] border-white/5">
        <CardContent className="p-3 space-y-3">
          <div>
            <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1.5 flex items-center gap-1"><Calendar className="w-3 h-3" /> Data</p>
            <input type="date" value={date} min={minDateTime} onChange={(e) => setDate(e.target.value)} className="w-full bg-[#0d0d0f] border border-white/10 rounded-md px-3 py-2 text-xs text-white" data-testid="tv-airing-date" />
          </div>

          <div>
            <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1.5 flex items-center gap-1"><Clock className="w-3 h-3" /> Ora</p>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className="w-full bg-[#0d0d0f] border border-white/10 rounded-md px-3 py-2 text-xs text-white" data-testid="tv-airing-time" />
          </div>

          <div>
            <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1.5">Slot Orario</p>
            <div className="grid grid-cols-2 gap-1.5">
              {SLOTS.map(s => {
                const sel = slot === s.key;
                return (
                  <button key={s.key} type="button" onClick={() => setSlot(s.key)}
                    className={`text-left rounded-lg p-2 border transition-all ${sel ? 'border-rose-500 bg-rose-500/15' : 'border-white/10 bg-[#0d0d0f] hover:border-white/20'}`}
                    data-testid={`slot-${s.key}`}>
                    <p className="text-[11px] font-bold text-white">{s.label}</p>
                    <p className="text-[8px] text-gray-500">{s.range}</p>
                    <p className="text-[8px] text-emerald-400/80">{s.share}</p>
                    <p className="text-[8px] text-amber-400/80">Costo: {s.cost}</p>
                    {sel && <Check className="w-3 h-3 text-rose-400 absolute" style={{ top: 4, right: 4 }} />}
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      <Button onClick={saveAiring} disabled={saving || loading || !date || !time}
        className="w-full bg-gradient-to-r from-rose-500 to-pink-500 hover:opacity-95 text-white font-bold"
        data-testid="confirm-tv-airing-btn">
        {saving ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <ArrowRight className="w-4 h-4 mr-1.5" />}
        Programma e Procedi al Rilascio
      </Button>
    </div>
  );
}
