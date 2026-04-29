import React, { useEffect, useState, useContext } from 'react';
import { AuthContext } from '../contexts';
import { toast } from 'sonner';
import { Wrench, Trash2, Film, Loader2, AlertTriangle, CheckCircle, Image as ImageIcon, Gauge } from 'lucide-react';
import { Button } from './ui/button';

export default function AdminFilmRecovery() {
  const { api } = useContext(AuthContext);
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fixing, setFixing] = useState(null); // null | 'all' | film_id
  const [progress, setProgress] = useState(0);

  // Stuck content (anime/series senza poster)
  const [stuck, setStuck] = useState([]);
  const [stuckLoading, setStuckLoading] = useState(false);
  const [rescuing, setRescuing] = useState(false);

  // Legacy film data preview
  const [legacy, setLegacy] = useState(null);
  const [legacyLoading, setLegacyLoading] = useState(false);
  const [applyingLegacy, setApplyingLegacy] = useState(false);

  const loadFilms = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/recovery/broken-films');
      setFilms(res.data?.films || []);
    } catch { setFilms([]); }
    finally { setLoading(false); }
  };

  const loadStuck = async () => {
    setStuckLoading(true);
    try {
      const res = await api.get('/admin/recovery/stuck-content');
      setStuck(res.data?.items || []);
    } catch { setStuck([]); }
    setStuckLoading(false);
  };

  const rescueAllStuck = async () => {
    setRescuing(true);
    try {
      const r = await api.post('/admin/recovery/rescue-stuck-content', { ids: [] });
      toast.success(`${r.data?.rescued || 0} contenuti recuperati con placeholder`, { duration: 4000 });
      await loadStuck();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore rescue');
    }
    setRescuing(false);
  };

  const rescueOne = async (item) => {
    setRescuing(true);
    try {
      await api.post('/admin/recovery/rescue-stuck-content', { ids: [{ id: item.id, collection: item.collection }] });
      toast.success(`"${item.title}" recuperato`);
      await loadStuck();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setRescuing(false);
  };

  const loadLegacyPreview = async () => {
    setLegacyLoading(true);
    try {
      const r = await api.get('/admin/recovery/legacy-film-preview');
      setLegacy(r.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore preview');
      setLegacy(null);
    }
    setLegacyLoading(false);
  };

  const applyLegacyFix = async () => {
    if (!legacy?.count) return;
    setApplyingLegacy(true);
    try {
      const r = await api.post('/admin/recovery/legacy-film-fix');
      const s = r.data?.summary || {};
      toast.success(`${r.data?.patched || 0} film aggiornati`, {
        description: `Durate: ${s.duration_minutes}, Qualita: ${s.quality_score}, Hype: ${s.hype}`,
        duration: 5000,
      });
      await loadLegacyPreview();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore applicazione');
    }
    setApplyingLegacy(false);
  };

  useEffect(() => {
    loadFilms();
    loadStuck();
  }, []);

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

  const restoreToDraft = async (id, title) => {
    if (!window.confirm(`Riportare "${title}" in stato bozza? Sarà visibile in "I Miei Progetti".`)) return;
    setFixing(id);
    try {
      await api.post(`/admin/recovery/restore-to-draft/${id}`);
      toast.success('Riportato in bozza! Lo trovi in "I Miei Progetti".');
      await loadFilms();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    }
    setFixing(null);
  };

  return (
    <div className="space-y-5">
      {/* ═══ STUCK CONTENT (anime/serie senza poster) ═══ */}
      <section className="space-y-2 rounded-xl border border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-transparent p-3" data-testid="stuck-content-section">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
            <ImageIcon className="w-4 h-4 text-amber-400" />
            Contenuti bloccati senza locandina ({stuck.length})
          </h3>
          <div className="flex gap-1.5">
            <Button size="sm" variant="outline" className="h-7 text-[10px] border-amber-500/30 text-amber-300" onClick={loadStuck} disabled={stuckLoading}>
              {stuckLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Ricarica'}
            </Button>
            <Button size="sm" onClick={rescueAllStuck} disabled={rescuing || stuck.length === 0} className="h-7 text-[10px] bg-amber-500 hover:bg-amber-400 text-black" data-testid="rescue-all-stuck-btn">
              {rescuing ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Wrench className="w-3 h-3 mr-1" />}
              Recupera tutti
            </Button>
          </div>
        </div>
        <p className="text-[9px] text-amber-200/70 leading-tight">
          Anime/serie/film in fase iniziale senza poster vengono soft-lockati. Il recupero applica una locandina placeholder che puoi rigenerare manualmente dopo.
        </p>
        {stuckLoading ? (
          <div className="flex items-center justify-center py-4"><Loader2 className="w-5 h-5 text-amber-400 animate-spin" /></div>
        ) : stuck.length === 0 ? (
          <div className="flex items-center gap-2 py-2 px-3 rounded-lg bg-green-500/10 border border-green-500/20">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <p className="text-[10px] text-green-400">Nessun contenuto bloccato!</p>
          </div>
        ) : (
          <div className="space-y-1 max-h-[30vh] overflow-y-auto">
            {stuck.map(s => (
              <div key={`${s.collection}-${s.id}`} className="flex items-center gap-2 p-2 rounded-lg bg-[#111113] border border-white/5" data-testid={`stuck-item-${s.id}`}>
                <div className="w-7 h-10 rounded bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
                  <ImageIcon className="w-3 h-3 text-amber-500/60" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-bold text-white truncate">{s.title}</p>
                  <p className="text-[8px] text-gray-500">{s.content_type} · {s.state} · <span className="text-gray-600">{s.collection}</span></p>
                </div>
                <Button size="sm" className="h-6 px-2 text-[8px] bg-amber-500/20 border border-amber-500/30 text-amber-300 hover:bg-amber-500/30" onClick={() => rescueOne(s)} disabled={rescuing}>
                  <Wrench className="w-2.5 h-2.5" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ═══ LEGACY FILM DATA FIX ═══ */}
      <section className="space-y-2 rounded-xl border border-sky-500/20 bg-gradient-to-br from-sky-500/5 to-transparent p-3" data-testid="legacy-fix-section">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
            <Gauge className="w-4 h-4 text-sky-400" />
            Fix dati legacy film
          </h3>
          <div className="flex gap-1.5">
            <Button size="sm" variant="outline" className="h-7 text-[10px] border-sky-500/30 text-sky-300" onClick={loadLegacyPreview} disabled={legacyLoading} data-testid="legacy-preview-btn">
              {legacyLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Analizza'}
            </Button>
            <Button size="sm" onClick={applyLegacyFix} disabled={applyingLegacy || !legacy?.count} className="h-7 text-[10px] bg-sky-500 hover:bg-sky-400 text-black" data-testid="legacy-apply-btn">
              {applyingLegacy ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Wrench className="w-3 h-3 mr-1" />}
              Applica {legacy?.count ? `(${legacy.count})` : ''}
            </Button>
          </div>
        </div>
        <p className="text-[9px] text-sky-200/70 leading-tight">
          Ricalcola <b>durata</b>, <b>qualità</b> e <b>hype</b> mancanti sui film legacy usando categoria durata, budget tier, rating, likes e trend.
        </p>
        {legacy && (
          <div className="space-y-1.5">
            <div className="grid grid-cols-3 gap-1.5">
              <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-center">
                <p className="text-[8px] text-sky-300 uppercase tracking-wider">Durata</p>
                <p className="text-sm font-bold text-sky-100">{legacy.fields_to_fix?.duration_minutes || 0}</p>
              </div>
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                <p className="text-[8px] text-emerald-300 uppercase tracking-wider">Qualità</p>
                <p className="text-sm font-bold text-emerald-100">{legacy.fields_to_fix?.quality_score || 0}</p>
              </div>
              <div className="p-2 rounded-lg bg-pink-500/10 border border-pink-500/20 text-center">
                <p className="text-[8px] text-pink-300 uppercase tracking-wider">Hype</p>
                <p className="text-sm font-bold text-pink-100">{legacy.fields_to_fix?.hype || 0}</p>
              </div>
            </div>
            {legacy.count > 0 && (
              <div className="max-h-[30vh] overflow-y-auto space-y-1" data-testid="legacy-preview-list">
                {(legacy.items || []).slice(0, 30).map(i => (
                  <div key={i.id} className="flex items-center justify-between p-1.5 rounded bg-[#111113] border border-white/5">
                    <div className="flex-1 min-w-0 pr-2">
                      <p className="text-[10px] font-semibold text-white truncate">{i.title}</p>
                      <p className="text-[8px] text-gray-500">
                        {Object.entries(i.changes).map(([k, v]) => `${k}: ${v}`).join(' · ')}
                      </p>
                    </div>
                  </div>
                ))}
                {legacy.count > 30 && <p className="text-[9px] text-gray-500 text-center pt-1">+ altri {legacy.count - 30} film</p>}
              </div>
            )}
          </div>
        )}
      </section>

      {/* ═══ ANTI-LIMBO (esistente) ═══ */}
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
                <Button size="sm" className="h-6 px-2 text-[8px] bg-yellow-600 hover:bg-yellow-700" onClick={() => fixOne(f.id)} disabled={!!fixing} title="Fix (forza completion)">
                  <Wrench className="w-2.5 h-2.5" />
                </Button>
                <Button size="sm" className="h-6 px-2 text-[8px] bg-blue-600 hover:bg-blue-700" onClick={() => restoreToDraft(f.id, f.title || 'Senza titolo')} disabled={!!fixing} title="Riporta in Bozza" data-testid={`restore-draft-${f.id}`}>
                  📝
                </Button>
                <Button size="sm" variant="destructive" className="h-6 px-2 text-[8px]" onClick={() => deleteFilm(f.id, f.title)} disabled={!!fixing} title="Elimina definitivamente">
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
