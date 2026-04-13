import React, { useEffect, useState, useContext } from 'react';
import { AuthContext } from '../contexts';
import { toast } from 'sonner';
import { Wrench, Trash2, Film, Loader2, AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from './ui/button';

export default function AdminFilmRecovery() {
  const { api } = useContext(AuthContext);
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fixing, setFixing] = useState(null); // null | 'all' | film_id
  const [progress, setProgress] = useState(0);

  const loadFilms = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/recovery/broken-films');
      setFilms(res.data?.films || []);
    } catch { setFilms([]); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadFilms(); }, []);

  const fixAll = async () => {
    setFixing('all');
    setProgress(0);
    const total = films.length;
    let done = 0;
    for (const f of films) {
      try {
        await api.post(`/admin/recovery/fix-one/${f.id}`);
      } catch {}
      done++;
      setProgress(Math.round((done / total) * 100));
    }
    setFixing(null);
    toast.success(`${done} film riparati!`);
    await loadFilms();
  };

  const fixOne = async (id) => {
    setFixing(id);
    setProgress(0);
    try {
      const iv = setInterval(() => setProgress(p => Math.min(90, p + 15)), 200);
      await api.post(`/admin/recovery/fix-one/${id}`);
      clearInterval(iv);
      setProgress(100);
      toast.success('Film riparato!');
      setTimeout(async () => { setFixing(null); await loadFilms(); }, 500);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
      setFixing(null);
    }
  };

  const deleteFilm = async (id, title) => {
    if (!window.confirm(`Eliminare definitivamente "${title}"?`)) return;
    try {
      await api.delete(`/admin/recovery/delete/${id}`);
      toast.success('Film eliminato');
      await loadFilms();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          Anti-Limbo Film ({films.length})
        </h3>
        <Button size="sm" variant="destructive" onClick={fixAll} disabled={!!fixing || films.length === 0}
          className="text-[10px] h-7 bg-red-600 hover:bg-red-700">
          {fixing === 'all' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Wrench className="w-3 h-3 mr-1" />}
          Ripara TUTTI
        </Button>
      </div>

      {/* Progress bar */}
      {fixing && (
        <div className="space-y-1">
          <div className="h-2 rounded-full bg-gray-800 overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-red-500 to-yellow-500 transition-all duration-300" style={{ width: `${progress}%` }} />
          </div>
          <p className="text-[9px] text-gray-400 text-center">{fixing === 'all' ? 'Riparazione batch...' : 'Riparazione...'} {progress}%</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-6"><Loader2 className="w-5 h-5 text-gray-500 animate-spin" /></div>
      ) : films.length === 0 ? (
        <div className="flex items-center gap-2 py-4 px-3 rounded-lg bg-green-500/10 border border-green-500/20">
          <CheckCircle className="w-4 h-4 text-green-400" />
          <p className="text-[10px] text-green-400">Nessun film nel limbo!</p>
        </div>
      ) : (
        <div className="space-y-1.5 max-h-[50vh] overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
          {films.map(f => (
            <div key={f.id} className="flex items-center gap-2 p-2 rounded-lg bg-gray-800/50 border border-gray-700/50">
              {f.poster_url ? (
                <img src={f.poster_url} alt="" className="w-8 h-12 object-cover rounded flex-shrink-0" onError={e => { e.target.style.display = 'none'; }} />
              ) : (
                <div className="w-8 h-12 rounded bg-gray-700 flex items-center justify-center flex-shrink-0"><Film className="w-3 h-3 text-gray-500" /></div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-[10px] font-bold text-white truncate">{f.title || 'Senza titolo'}</p>
                <p className="text-[8px] text-gray-500">{f.pipeline_state || f.status || '?'} | {f.owner_nickname}</p>
              </div>
              <div className="flex gap-1 flex-shrink-0">
                <Button size="sm" className="h-6 px-2 text-[8px] bg-yellow-600 hover:bg-yellow-700" onClick={() => fixOne(f.id)} disabled={!!fixing}>
                  <Wrench className="w-2.5 h-2.5" />
                </Button>
                <Button size="sm" variant="destructive" className="h-6 px-2 text-[8px]" onClick={() => deleteFilm(f.id, f.title)} disabled={!!fixing}>
                  <Trash2 className="w-2.5 h-2.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
