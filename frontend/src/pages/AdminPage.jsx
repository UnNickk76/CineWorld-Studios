import React, { useState, useEffect, useContext, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Shield, Search, DollarSign, Coins, ChevronRight, Minus, Plus, Film, Users, Trash2, AlertTriangle, X, Loader2, Flag, Eye, CheckCircle, XCircle, Wrench } from 'lucide-react';
import { AuthContext } from '../contexts';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

/* ─── Tab constants ─── */
const TABS = [
  { id: 'users', label: 'Gestione Utenti', icon: Users },
  { id: 'films', label: 'Gestione Film', icon: Film },
  { id: 'reports', label: 'Segnalazioni', icon: Flag },
  { id: 'maintenance', label: 'Manutenzione', icon: Wrench },
];

/* ─── Confirm Modal ─── */
function ConfirmModal({ open, title, message, onConfirm, onCancel, loading }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" data-testid="confirm-modal">
      <Card className="bg-[#111113] border-red-500/40 max-w-sm w-full">
        <CardContent className="p-5 space-y-4">
          <div className="flex items-center gap-2 text-red-400">
            <AlertTriangle className="w-5 h-5" />
            <span className="text-sm font-bold">{title}</span>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed">{message}</p>
          <div className="flex gap-2 justify-end">
            <Button size="sm" variant="outline" className="text-xs border-gray-700 text-gray-400 hover:bg-gray-800"
              onClick={onCancel} disabled={loading} data-testid="confirm-cancel-btn">
              Annulla
            </Button>
            <Button size="sm" className="bg-red-600 hover:bg-red-700 text-xs" onClick={onConfirm} disabled={loading}
              data-testid="confirm-delete-btn">
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3 mr-1" />}
              Conferma Eliminazione
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/* ─── Users Tab ─── */
function UsersTab({ api }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [moneyAmount, setMoneyAmount] = useState('');
  const [cpAmount, setCpAmount] = useState('');
  const [actionLoading, setActionLoading] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const searchUsers = useCallback(async (q) => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/search-users?q=${encodeURIComponent(q)}`);
      setUsers(res.data.users || []);
    } catch { toast.error('Errore ricerca'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { searchUsers(''); }, [searchUsers]);

  const handleSearch = (e) => { e.preventDefault(); searchUsers(searchQuery); };

  const modifyFunds = async (nickname, amount) => {
    if (!amount || isNaN(amount)) return;
    setActionLoading(`money-${nickname}`);
    try {
      const res = await api.post('/admin/add-money', { nickname, amount: Number(amount) });
      toast.success(`${nickname}: $${res.data.old_funds.toLocaleString()} → $${res.data.new_funds.toLocaleString()}`);
      setMoneyAmount('');
      searchUsers(searchQuery);
      if (selectedUser?.nickname === nickname) setSelectedUser(prev => ({ ...prev, funds: res.data.new_funds }));
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const modifyCinepass = async (nickname, amount) => {
    if (!amount || isNaN(amount)) return;
    setActionLoading(`cp-${nickname}`);
    try {
      const res = await api.post('/admin/add-cinepass', { nickname, amount: Number(amount) });
      toast.success(`${nickname}: ${res.data.old_cinepass} CP → ${res.data.new_cinepass} CP`);
      setCpAmount('');
      searchUsers(searchQuery);
      if (selectedUser?.nickname === nickname) setSelectedUser(prev => ({ ...prev, cinepass: res.data.new_cinepass }));
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const handleDeleteUser = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      const res = await api.delete(`/admin/delete-user/${deleteTarget.id}`);
      const d = res.data;
      toast.success(`Utente "${deleteTarget.nickname}" eliminato. Contenuti rimossi: ${Object.entries(d.deleted_content || {}).map(([k,v]) => `${k}:${v}`).join(', ') || 'nessuno'}`);
      setDeleteTarget(null);
      if (selectedUser?.id === deleteTarget.id) setSelectedUser(null);
      searchUsers(searchQuery);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore eliminazione'); }
    finally { setDeleteLoading(false); }
  };

  return (
    <div className="space-y-3" data-testid="admin-users-tab">
      <ConfirmModal
        open={!!deleteTarget}
        title="Eliminazione Definitiva Utente"
        message={`Confermi eliminazione definitiva di "${deleteTarget?.nickname}" (${deleteTarget?.email})? Verranno eliminati TUTTI i dati collegati: film, serie TV, anime, classifiche, profilo. Questa azione e' IRREVERSIBILE.`}
        onConfirm={handleDeleteUser}
        onCancel={() => setDeleteTarget(null)}
        loading={deleteLoading}
      />

      {/* Search */}
      <form onSubmit={handleSearch}>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              placeholder="Cerca per username..."
              className="w-full bg-[#111113] border border-gray-800 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none"
              data-testid="admin-search-input" />
          </div>
          <Button type="submit" size="sm" className="bg-red-600 hover:bg-red-700 text-xs px-3" disabled={loading}
            data-testid="admin-search-btn">
            {loading ? '...' : 'Cerca'}
          </Button>
        </div>
      </form>

      {/* User list */}
      <div className="space-y-1.5 max-h-[40vh] overflow-y-auto" data-testid="admin-user-list">
        {users.map(u => (
          <Card key={u.id}
            className={`bg-[#111113] cursor-pointer transition-all ${selectedUser?.id === u.id ? 'border-red-500/40 ring-1 ring-red-500/20' : 'border-white/5 hover:border-gray-700'}`}
            onClick={() => { setSelectedUser(u); setMoneyAmount(''); setCpAmount(''); }}
            data-testid={`admin-user-${u.nickname}`}>
            <CardContent className="p-2.5 flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500/20 to-orange-500/20 flex items-center justify-center text-xs font-bold text-red-400 flex-shrink-0">
                {u.nickname?.[0]?.toUpperCase() || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold truncate">{u.nickname}</span>
                  {u.role && <Badge className="text-[7px] h-3.5 bg-purple-500/20 text-purple-400">{u.role}</Badge>}
                </div>
                <p className="text-[9px] text-gray-500 truncate">{u.production_house_name || u.email}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-[10px] text-yellow-400 font-mono">${(u.funds || 0).toLocaleString()}</p>
                <p className="text-[9px] text-cyan-400 font-mono">{u.cinepass || 0} CP</p>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
            </CardContent>
          </Card>
        ))}
        {users.length === 0 && !loading && (
          <p className="text-center text-xs text-gray-600 py-4">Nessun utente trovato</p>
        )}
      </div>

      {/* Selected user panel */}
      {selectedUser && (
        <Card className="bg-[#0e0e10] border-red-500/30" data-testid="admin-user-panel">
          <CardHeader className="pb-2 pt-3 px-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-red-500/30 to-orange-500/30 flex items-center justify-center text-xs font-bold text-red-400">
                {selectedUser.nickname?.[0]?.toUpperCase()}
              </div>
              <span className="flex-1">{selectedUser.nickname}</span>
              <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-7 px-2 text-[10px]"
                onClick={(e) => { e.stopPropagation(); setDeleteTarget(selectedUser); }}
                data-testid="admin-delete-user-btn">
                <Trash2 className="w-3 h-3 mr-1" /> Elimina
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0 space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded-lg bg-yellow-500/5 border border-yellow-500/20 text-center">
                <DollarSign className="w-3.5 h-3.5 text-yellow-400 mx-auto mb-0.5" />
                <p className="text-sm font-bold text-yellow-400">${(selectedUser.funds || 0).toLocaleString()}</p>
                <p className="text-[8px] text-gray-500">DENARO</p>
              </div>
              <div className="p-2 rounded-lg bg-cyan-500/5 border border-cyan-500/20 text-center">
                <Coins className="w-3.5 h-3.5 text-cyan-400 mx-auto mb-0.5" />
                <p className="text-sm font-bold text-cyan-400">{selectedUser.cinepass || 0}</p>
                <p className="text-[8px] text-gray-500">CINEPASS</p>
              </div>
            </div>

            {/* Money controls */}
            <div className="space-y-1.5">
              <p className="text-[10px] text-yellow-400 font-semibold flex items-center gap-1"><DollarSign className="w-3 h-3" /> Modifica Denaro</p>
              <div className="flex gap-1.5">
                <input type="number" value={moneyAmount} onChange={e => setMoneyAmount(e.target.value)}
                  placeholder="Importo (es: 1000000)"
                  className="flex-1 bg-black/40 border border-gray-700 rounded px-2 py-1.5 text-xs text-white focus:border-yellow-500/50 focus:outline-none"
                  data-testid="admin-money-input" />
                <Button size="sm" className="bg-emerald-700 hover:bg-emerald-600 text-[10px] h-7 px-2"
                  onClick={() => modifyFunds(selectedUser.nickname, Math.abs(Number(moneyAmount)))}
                  disabled={!moneyAmount || actionLoading} data-testid="admin-money-add">
                  <Plus className="w-3 h-3" />
                </Button>
                <Button size="sm" className="bg-red-700 hover:bg-red-600 text-[10px] h-7 px-2"
                  onClick={() => modifyFunds(selectedUser.nickname, -Math.abs(Number(moneyAmount)))}
                  disabled={!moneyAmount || actionLoading} data-testid="admin-money-remove">
                  <Minus className="w-3 h-3" />
                </Button>
              </div>
            </div>

            {/* CinePass controls */}
            <div className="space-y-1.5">
              <p className="text-[10px] text-cyan-400 font-semibold flex items-center gap-1"><Coins className="w-3 h-3" /> Modifica CinePass</p>
              <div className="flex gap-1.5">
                <input type="number" value={cpAmount} onChange={e => setCpAmount(e.target.value)}
                  placeholder="Quantita (es: 50)"
                  className="flex-1 bg-black/40 border border-gray-700 rounded px-2 py-1.5 text-xs text-white focus:border-cyan-500/50 focus:outline-none"
                  data-testid="admin-cp-input" />
                <Button size="sm" className="bg-emerald-700 hover:bg-emerald-600 text-[10px] h-7 px-2"
                  onClick={() => modifyCinepass(selectedUser.nickname, Math.abs(Number(cpAmount)))}
                  disabled={!cpAmount || actionLoading} data-testid="admin-cp-add">
                  <Plus className="w-3 h-3" />
                </Button>
                <Button size="sm" className="bg-red-700 hover:bg-red-600 text-[10px] h-7 px-2"
                  onClick={() => modifyCinepass(selectedUser.nickname, -Math.abs(Number(cpAmount)))}
                  disabled={!cpAmount || actionLoading} data-testid="admin-cp-remove">
                  <Minus className="w-3 h-3" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/* ─── Films Tab ─── */
function FilmsTab({ api }) {
  const [films, setFilms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const loadFilms = useCallback(async (q = '') => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/all-films?q=${encodeURIComponent(q)}`);
      setFilms(res.data.films || []);
    } catch { toast.error('Errore caricamento film'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadFilms(); }, [loadFilms]);

  const handleSearch = (e) => { e.preventDefault(); loadFilms(searchQuery); };

  const handleDeleteFilm = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await api.delete(`/admin/delete-film/${deleteTarget.id}`);
      toast.success(`Film "${deleteTarget.title}" eliminato definitivamente`);
      setDeleteTarget(null);
      loadFilms(searchQuery);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore eliminazione'); }
    finally { setDeleteLoading(false); }
  };

  return (
    <div className="space-y-3" data-testid="admin-films-tab">
      <ConfirmModal
        open={!!deleteTarget}
        title="Eliminazione Definitiva Film"
        message={`Confermi eliminazione definitiva del film "${deleteTarget?.title}" di ${deleteTarget?.studio_name}? Il film verra' rimosso da classifiche e liste pubbliche. Questa azione e' IRREVERSIBILE.`}
        onConfirm={handleDeleteFilm}
        onCancel={() => setDeleteTarget(null)}
        loading={deleteLoading}
      />

      {/* Search */}
      <form onSubmit={handleSearch}>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              placeholder="Cerca film per titolo..."
              className="w-full bg-[#111113] border border-gray-800 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none"
              data-testid="admin-film-search-input" />
          </div>
          <Button type="submit" size="sm" className="bg-red-600 hover:bg-red-700 text-xs px-3" disabled={loading}
            data-testid="admin-film-search-btn">
            {loading ? '...' : 'Cerca'}
          </Button>
        </div>
      </form>

      <p className="text-[10px] text-gray-500">{films.length} film trovati</p>

      {/* Compact film grid: 8 mobile / 12 tablet / 16 desktop */}
      <div className="grid gap-1 max-h-[70vh] overflow-y-auto pb-2"
        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))' }}
        data-testid="admin-film-grid">
        {films.map(f => (
          <div key={f.id} className="group relative bg-[#0d0d0f] border border-white/5 rounded overflow-hidden hover:border-red-500/40 transition-all"
            data-testid={`admin-film-card-${f.id}`}>
            {/* Mini poster */}
            <div className="aspect-[2/3] bg-gray-900 relative">
              {f.poster_url ? (
                <img src={`${API_BASE}${f.poster_url}`} alt={f.title} loading="lazy"
                  className="w-full h-full object-cover"
                  onError={e => { e.target.style.display='none'; }} />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Film className="w-3.5 h-3.5 text-gray-700" />
                </div>
              )}
              {/* Delete icon - always visible, top-right */}
              <button
                className="absolute top-0.5 right-0.5 w-4 h-4 rounded-full bg-red-600/80 hover:bg-red-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => { e.stopPropagation(); setDeleteTarget(f); }}
                data-testid={`admin-film-delete-${f.id}`}>
                <Trash2 className="w-2 h-2 text-white" />
              </button>
              {/* Quality badge */}
              {f.quality_score != null && (
                <span className="absolute bottom-0.5 right-0.5 text-[7px] font-bold bg-black/70 text-yellow-400 px-0.5 rounded leading-none py-px">
                  {Math.round(f.quality_score)}%
                </span>
              )}
            </div>
            {/* Compact info */}
            <div className="px-0.5 py-0.5">
              <p className="text-[7px] font-semibold text-white truncate leading-tight" title={f.title}>{f.title}</p>
              <p className="text-[6px] text-gray-500 truncate leading-tight">{f.studio_name}</p>
            </div>
          </div>
        ))}
      </div>

      {films.length === 0 && !loading && (
        <p className="text-center text-xs text-gray-600 py-8">Nessun film trovato</p>
      )}
    </div>
  );
}

/* ─── Reports Tab ─── */
function ReportsTab({ api }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('pending');
  const [actionLoading, setActionLoading] = useState(null);

  const loadReports = useCallback(async (status) => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/reports?status=${status}`);
      setReports(res.data.reports || []);
    } catch { toast.error('Errore caricamento segnalazioni'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadReports(filter); }, [filter, loadReports]);

  const resolveReport = async (reportId, action) => {
    setActionLoading(reportId);
    try {
      await api.post(`/admin/reports/${reportId}/resolve?action=${action}`);
      toast.success(action === 'delete_content' ? 'Contenuto rimosso e segnalazione risolta' : 'Segnalazione archiviata');
      loadReports(filter);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const TYPE_LABELS = { message: 'Messaggio', image: 'Immagine', user: 'Utente' };
  const TYPE_COLORS = { message: 'bg-blue-500/20 text-blue-400', image: 'bg-purple-500/20 text-purple-400', user: 'bg-orange-500/20 text-orange-400' };
  const STATUS_COLORS = { pending: 'bg-yellow-500/20 text-yellow-400', resolved: 'bg-green-500/20 text-green-400', dismissed: 'bg-gray-500/20 text-gray-400' };

  return (
    <div className="space-y-3" data-testid="admin-reports-tab">
      {/* Filter buttons */}
      <div className="flex gap-1.5 flex-wrap">
        {['pending', 'resolved', 'dismissed', 'all'].map(f => (
          <button key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-full text-[10px] font-semibold transition-all ${
              filter === f ? 'bg-red-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
            data-testid={`report-filter-${f}`}>
            {f === 'pending' ? 'In attesa' : f === 'resolved' ? 'Risolte' : f === 'dismissed' ? 'Archiviate' : 'Tutte'}
          </button>
        ))}
      </div>

      <p className="text-[10px] text-gray-500">{reports.length} segnalazioni trovate</p>

      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 text-red-400 animate-spin" /></div>
      ) : reports.length === 0 ? (
        <div className="text-center py-8">
          <Flag className="w-8 h-8 text-gray-700 mx-auto mb-2" />
          <p className="text-xs text-gray-600">Nessuna segnalazione {filter !== 'all' ? `con stato "${filter}"` : ''}</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[70vh] overflow-y-auto pb-2" data-testid="admin-reports-list">
          {reports.map(r => (
            <Card key={r.id} className="bg-[#111113] border-white/5 hover:border-white/10 transition-all" data-testid={`report-card-${r.id}`}>
              <CardContent className="p-3 space-y-2">
                {/* Header row */}
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-1.5">
                    <Badge className={`text-[8px] h-4 ${TYPE_COLORS[r.target_type] || 'bg-gray-500/20 text-gray-400'}`}>
                      {TYPE_LABELS[r.target_type] || r.target_type}
                    </Badge>
                    <Badge className={`text-[8px] h-4 ${STATUS_COLORS[r.status] || ''}`}>
                      {r.status === 'pending' ? 'In attesa' : r.status === 'resolved' ? 'Risolta' : 'Archiviata'}
                    </Badge>
                  </div>
                  <span className="text-[9px] text-gray-600">
                    {r.created_at ? new Date(r.created_at).toLocaleString('it-IT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>

                {/* Reporter */}
                <p className="text-[10px] text-gray-400">
                  Segnalato da: <span className="text-white font-semibold">{r.reporter_nickname || '?'}</span>
                </p>

                {/* Reason */}
                {r.reason && (
                  <div className="bg-black/30 rounded-lg px-2.5 py-1.5">
                    <p className="text-[10px] text-gray-300">"{r.reason}"</p>
                  </div>
                )}

                {/* Snapshot */}
                {r.snapshot && (
                  <div className="bg-black/20 rounded-lg px-2.5 py-1.5 border border-white/5">
                    {r.target_type === 'user' ? (
                      <div className="flex items-center gap-2">
                        <Users className="w-3 h-3 text-orange-400 flex-shrink-0" />
                        <div>
                          <p className="text-[10px] text-white font-semibold">{r.snapshot.nickname}</p>
                          <p className="text-[9px] text-gray-500">{r.snapshot.email}</p>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <p className="text-[9px] text-gray-500 mb-0.5">
                          Da: <span className="text-gray-300">{r.snapshot.sender_nickname || '?'}</span>
                          {r.snapshot.room_id && <span className="ml-1 text-gray-600">in #{r.snapshot.room_id}</span>}
                        </p>
                        {r.snapshot.content && (
                          <p className="text-[10px] text-gray-300 break-words">"{r.snapshot.content}"</p>
                        )}
                        {r.snapshot.image_url && (
                          <img
                            src={r.snapshot.image_url.startsWith('/') ? `${API_BASE}${r.snapshot.image_url}` : r.snapshot.image_url}
                            alt="" className="mt-1 max-h-24 rounded border border-white/10"
                            onError={e => { e.target.style.display = 'none'; }}
                          />
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Action buttons (only for pending) */}
                {r.status === 'pending' && (
                  <div className="flex gap-1.5 pt-1">
                    {r.target_type !== 'user' && (
                      <Button size="sm" className="bg-red-600 hover:bg-red-700 text-[10px] h-6 px-2"
                        onClick={() => resolveReport(r.id, 'delete_content')}
                        disabled={actionLoading === r.id}
                        data-testid={`report-delete-${r.id}`}>
                        {actionLoading === r.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3 mr-0.5" />}
                        Rimuovi Contenuto
                      </Button>
                    )}
                    <Button size="sm" variant="outline" className="text-[10px] h-6 px-2 border-gray-700 text-gray-400 hover:bg-white/5"
                      onClick={() => resolveReport(r.id, 'dismiss')}
                      disabled={actionLoading === r.id}
                      data-testid={`report-dismiss-${r.id}`}>
                      <XCircle className="w-3 h-3 mr-0.5" />
                      Archivia
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Maintenance Tab ─── */
function MaintenanceTab({ api }) {
  const [repairLoading, setRepairLoading] = useState(false);
  const [repairResult, setRepairResult] = useState(null);

  const repairDatabase = async () => {
    setRepairLoading(true);
    setRepairResult(null);
    try {
      const res = await api.post('/admin/repair-database');
      setRepairResult(res.data);
      if (res.data.total_fixed > 0) {
        toast.success(`${res.data.total_fixed} problemi logici risolti!`);
      } else {
        toast.success('Nessun problema logico trovato');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore durante la riparazione');
    } finally {
      setRepairLoading(false);
    }
  };

  const actionLabels = {
    'proposed': 'Reset a Proposta',
    'concept': 'Reset a Concept',
    'discarded': 'Scartato',
    'ready_for_casting': 'Sbloccato a Ready for Casting',
  };

  const categoryLabels = {
    'films_invalid_status': 'Film - Stato invalido',
    'films_stuck_casting': 'Film - Bloccati in Casting',
    'films_stuck_screenplay': 'Film - Bloccati in Sceneggiatura',
    'films_stuck_preproduction': 'Film - Bloccati in Pre-Produzione',
    'films_stuck_coming_soon': 'Film - Coming Soon scaduti',
    'films_missing_basics': 'Film - Dati base mancanti',
    'series_invalid_status': 'Serie - Stato invalido',
    'series_stuck_casting': 'Serie - Bloccate in Casting',
    'series_stuck_screenplay': 'Serie - Bloccate in Sceneggiatura',
    'series_stuck_production': 'Serie - Bloccate in Produzione',
    'series_stuck_coming_soon': 'Serie - Coming Soon scaduti',
    'series_missing_basics': 'Serie - Dati base mancanti',
  };

  return (
    <div className="space-y-4" data-testid="maintenance-tab">
      <Card className="bg-[#111113] border-yellow-500/30">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-yellow-400 flex items-center gap-2">
            <Wrench className="w-4 h-4" />
            Riparazione Database Avanzata
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-gray-400 leading-relaxed">
            Analizza TUTTI i progetti nel database e verifica la <span className="text-yellow-400 font-semibold">coerenza logica del flusso</span>:
          </p>
          <ul className="text-xs text-gray-500 space-y-1 list-disc list-inside">
            <li>Film in Casting senza proposte → reset a Proposta</li>
            <li>Film in Sceneggiatura senza cast completo → reset a Proposta</li>
            <li>Film in Sceneggiatura senza sinossi/genere → reset a Proposta</li>
            <li>Film in Pre-Produzione senza sceneggiatura → reset a Proposta</li>
            <li>Coming Soon con timer scaduto mai rilasciati → sbloccati</li>
            <li>Serie senza cast/genere/episodi nelle fasi avanzate → reset</li>
            <li>Progetti con stati invalidi o dati base mancanti → scartati</li>
          </ul>
          <Button
            onClick={repairDatabase}
            disabled={repairLoading}
            className="bg-yellow-600 hover:bg-yellow-700 text-black font-semibold w-full"
            data-testid="repair-database-btn"
          >
            {repairLoading ? (
              <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Analisi e riparazione in corso...</>
            ) : (
              <><Wrench className="w-4 h-4 mr-2" /> Analizza e Ripara Database</>
            )}
          </Button>

          {repairResult && (
            <div className="space-y-3">
              {/* Stats summary */}
              <Card className="border border-blue-500/30 bg-blue-500/5">
                <CardContent className="p-3">
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div>
                      <p className="text-lg font-black text-white">{repairResult.films_analyzed ?? 0}</p>
                      <p className="text-[9px] text-gray-500">Film analizzati</p>
                    </div>
                    <div>
                      <p className="text-lg font-black text-white">{repairResult.series_analyzed ?? 0}</p>
                      <p className="text-[9px] text-gray-500">Serie analizzate</p>
                    </div>
                    <div>
                      <p className={`text-lg font-black ${repairResult.total_fixed > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                        {repairResult.total_fixed}
                      </p>
                      <p className="text-[9px] text-gray-500">Problemi risolti</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Detailed report */}
              {repairResult.total_fixed > 0 && repairResult.report && (
                <Card className="border border-yellow-500/20 bg-yellow-500/5">
                  <CardContent className="p-3 space-y-3">
                    <p className="text-xs font-bold text-yellow-400">Dettaglio riparazioni:</p>
                    {Object.entries(repairResult.report).map(([key, items]) => (
                      items.length > 0 && (
                        <div key={key} className="space-y-1">
                          <p className="text-[10px] text-yellow-400 font-semibold">{categoryLabels[key] || key} ({items.length})</p>
                          {items.map((item, i) => (
                            <div key={i} className="bg-black/30 rounded px-2 py-1.5 space-y-0.5">
                              <p className="text-[10px] text-white font-medium">{item.title || item.id}</p>
                              <p className="text-[9px] text-gray-500">{item.reason}</p>
                              <Badge className={`text-[8px] ${item.action === 'discarded' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                                {actionLabels[item.action] || item.action}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      )
                    ))}
                  </CardContent>
                </Card>
              )}

              {repairResult.total_fixed === 0 && (
                <Card className="border border-green-500/20 bg-green-500/5">
                  <CardContent className="p-3 text-center">
                    <CheckCircle className="w-6 h-6 text-green-400 mx-auto mb-1" />
                    <p className="text-xs text-green-400 font-semibold">Tutti i progetti sono logicamente coerenti</p>
                    <p className="text-[9px] text-gray-500 mt-1">{repairResult.total_analyzed} progetti analizzati, nessun blocco trovato</p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ─── Main Admin Page ─── */
export default function AdminPage() {
  const { api, user } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('users');
  const isAdmin = user?.nickname === 'NeoMorpheus';

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center p-4">
        <Card className="bg-[#111113] border-red-500/30 max-w-sm w-full">
          <CardContent className="p-6 text-center">
            <Shield className="w-10 h-10 mx-auto mb-3 text-red-500/50" />
            <p className="text-sm text-red-400 font-semibold">Accesso Negato</p>
            <p className="text-xs text-gray-500 mt-1">Solo gli amministratori possono accedere a questa pagina.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B] p-4 pb-24" data-testid="admin-page">
      <div className="max-w-[1600px] mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center gap-2.5 mb-1">
          <div className="p-2 bg-red-500/15 rounded-lg"><Shield className="w-5 h-5 text-red-400" /></div>
          <div>
            <h1 className="text-lg font-black text-white tracking-tight">Pannello Admin</h1>
            <p className="text-[10px] text-gray-500">Gestione utenti, film, denaro e crediti</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-[#111113] rounded-lg p-1 border border-white/5" data-testid="admin-tabs">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-md text-xs font-semibold transition-all ${
                  isActive ? 'bg-red-600 text-white' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                }`}
                data-testid={`admin-tab-${tab.id}`}>
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        {activeTab === 'users' && <UsersTab api={api} />}
        {activeTab === 'films' && <FilmsTab api={api} />}
        {activeTab === 'reports' && <ReportsTab api={api} />}
        {activeTab === 'maintenance' && <MaintenanceTab api={api} />}
      </div>
    </div>
  );
}
