import React, { useState, useEffect, useContext, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Shield, ShieldCheck, Search, DollarSign, Coins, ChevronRight, Minus, Plus, Film, Users, Trash2, AlertTriangle, X, Loader2, Flag, Eye, CheckCircle, XCircle, Wrench, Crown, Star, UserCog, Clock, Ban, Upload, Download } from 'lucide-react';
import { AuthContext } from '../contexts';
import { PlayerBadge } from '../components/PlayerBadge';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

/* ─── Tab config by role ─── */
const ADMIN_TABS = [
  { id: 'users', label: 'Gestione Utenti', icon: Users },
  { id: 'films', label: 'Gestione Film', icon: Film },
  { id: 'roles', label: 'Gestione Ruoli', icon: UserCog },
  { id: 'reports', label: 'Segnalazioni', icon: Flag },
  { id: 'deletions', label: 'Cancellazioni', icon: Trash2 },
  { id: 'maintenance', label: 'Manutenzione', icon: Wrench },
];

const COADMIN_TABS = [
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
                  <PlayerBadge badge={u.badge} badgeExpiry={u.badge_expiry} badges={u.badges} size="sm" />
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

            {/* Badge controls */}
            <div className="space-y-1.5">
              <p className="text-[10px] text-amber-400 font-semibold flex items-center gap-1"><Crown className="w-3 h-3" /> Badge Utente</p>
              <p className="text-[8px] text-gray-500">Attuale: <span className="text-amber-300">{selectedUser.badge || 'none'}</span> {selectedUser.badge_expiry && selectedUser.badge !== 'none' ? `(scade: ${new Date(selectedUser.badge_expiry).toLocaleDateString()})` : ''}</p>
              <div className="flex gap-1.5">
                {[{ val: 'none', label: 'Nessuno', cls: 'bg-gray-700 hover:bg-gray-600' }, { val: 'cinevip', label: 'CineVIP', cls: 'bg-yellow-700 hover:bg-yellow-600' }, { val: 'cinestar', label: 'CineSTAR', cls: 'bg-amber-600 hover:bg-amber-500' }].map(b => (
                  <Button key={b.val} size="sm" className={`text-[10px] h-7 px-2 flex-1 ${b.cls} ${selectedUser.badge === b.val ? 'ring-1 ring-white/40' : ''}`}
                    disabled={actionLoading}
                    onClick={async () => {
                      setActionLoading('badge');
                      try {
                        await api.post('/admin/set-badge', { nickname: selectedUser.nickname, badge: b.val });
                        toast.success(`Badge ${b.label} assegnato a ${selectedUser.nickname}`);
                        setSelectedUser(prev => ({ ...prev, badge: b.val, badge_expiry: b.val === 'none' ? null : new Date(Date.now() + 7*24*60*60*1000).toISOString() }));
                        searchUsers(searchQuery);
                      } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
                      setActionLoading(null);
                    }}
                    data-testid={`admin-badge-${b.val}`}>
                    {b.val === 'cinevip' && <Crown className="w-3 h-3 mr-0.5" />}
                    {b.val === 'cinestar' && <Star className="w-3 h-3 mr-0.5" />}
                    {b.label}
                  </Button>
                ))}
              </div>
              <p className="text-[8px] text-gray-600">Durata: 7 giorni dalla assegnazione</p>
            </div>

            {/* Permanent Badge controls */}
            <div className="space-y-1.5">
              <p className="text-[10px] text-red-400 font-semibold flex items-center gap-1"><Shield className="w-3 h-3" /> Badge Permanenti</p>
              <div className="flex gap-1.5">
                {[
                  { key: 'cineadmin', label: 'CineADMIN', icon: Shield, cls: 'bg-red-800 hover:bg-red-700', activeCls: 'ring-1 ring-red-400', color: 'text-red-400' },
                  { key: 'cinemod', label: 'CineMOD', icon: ShieldCheck, cls: 'bg-blue-800 hover:bg-blue-700', activeCls: 'ring-1 ring-blue-400', color: 'text-blue-400' },
                ].map(b => {
                  const isActive = selectedUser.badges?.[b.key];
                  return (
                    <Button key={b.key} size="sm" className={`text-[10px] h-7 px-2 flex-1 ${b.cls} ${isActive ? b.activeCls : 'opacity-60'}`}
                      disabled={actionLoading}
                      onClick={async () => {
                        setActionLoading('perm-badge');
                        try {
                          await api.post('/admin/set-perm-badge', { nickname: selectedUser.nickname, badge_type: b.key, active: !isActive });
                          toast.success(`${b.label} ${!isActive ? 'assegnato' : 'rimosso'} a ${selectedUser.nickname}`);
                          setSelectedUser(prev => ({ ...prev, badges: { ...prev.badges, [b.key]: !isActive } }));
                          searchUsers(searchQuery);
                        } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
                        setActionLoading(null);
                      }}
                      data-testid={`admin-perm-${b.key}`}>
                      <b.icon className={`w-3 h-3 mr-0.5 ${b.color}`} />
                      {isActive ? `Rimuovi ${b.label}` : `Assegna ${b.label}`}
                    </Button>
                  );
                })}
              </div>
              <p className="text-[8px] text-gray-600">Permanenti — rimovibili solo manualmente</p>
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

/* ─── Maintenance Tab (Rewritten — Advanced) ─── */
function MaintenanceTab({ api }) {
  const [username, setUsername] = useState('');
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [targetUser, setTargetUser] = useState('');

  const searchProjects = async (nick) => {
    if (!nick.trim()) return;
    setLoading(true);
    setProjects([]);
    setStats(null);
    try {
      const res = await api.get(`/admin/maintenance/projects?username=${encodeURIComponent(nick.trim())}`);
      setProjects(res.data.projects || []);
      setTargetUser(res.data.user || nick);
      setStats({ total: res.data.total, broken: res.data.broken, stuck: res.data.stuck, incomplete: res.data.incomplete });
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore ricerca'); }
    finally { setLoading(false); }
  };

  const execAction = async (projectId, projectType, action) => {
    const key = `${projectId}-${action}`;
    setActionLoading(key);
    try {
      const res = await api.post('/admin/maintenance/fix-project', { project_id: projectId, project_type: projectType, action });
      const d = res.data;
      if (action === 'auto_fix') toast.success(`Auto-fix: ${(d.fixes || []).join(', ')}`);
      else if (action === 'force_step') toast.success(d.message || 'Step avanzato');
      else if (action === 'complete_project') toast.success(d.message || 'Progetto completato');
      else if (action === 'reset_step') toast.success(d.message || 'Step precedente');
      searchProjects(targetUser);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore azione'); }
    finally { setActionLoading(null); }
  };

  const FLAG_CONFIG = {
    'OK': { label: 'OK', color: 'bg-green-500/20 text-green-400', border: 'border-green-500/20' },
    'STUCK': { label: 'FERMO', color: 'bg-yellow-500/20 text-yellow-400', border: 'border-yellow-500/30' },
    'LOOP': { label: 'LOOP', color: 'bg-orange-500/20 text-orange-400', border: 'border-orange-500/30' },
    'INCOMPLETE': { label: 'INCOMPLETO', color: 'bg-purple-500/20 text-purple-400', border: 'border-purple-500/30' },
    'BROKEN': { label: 'ROTTO', color: 'bg-red-500/20 text-red-400', border: 'border-red-500/30' },
  };

  const TYPE_CONFIG = {
    'film': { label: 'Film', color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    'serie': { label: 'Serie TV', color: 'text-blue-400', bg: 'bg-blue-500/10' },
    'anime': { label: 'Anime', color: 'text-pink-400', bg: 'bg-pink-500/10' },
  };

  return (
    <div className="space-y-4" data-testid="maintenance-tab">
      {/* Search */}
      <Card className="bg-[#111113] border-amber-500/20">
        <CardContent className="p-3 space-y-2">
          <p className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
            <Search className="w-3.5 h-3.5" /> Cerca Progetti Utente
          </p>
          <form onSubmit={(e) => { e.preventDefault(); searchProjects(username); }} className="flex gap-2">
            <input type="text" value={username} onChange={e => setUsername(e.target.value)}
              placeholder="Nickname utente..."
              className="flex-1 bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 focus:border-amber-500/50 focus:outline-none"
              data-testid="maint-search-input" />
            <Button type="submit" size="sm" className="bg-amber-600 hover:bg-amber-700 text-xs px-4" disabled={loading || !username.trim()}
              data-testid="maint-search-btn">
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Analizza'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Stats summary */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="maint-stats">
          {[
            { label: 'Totale', value: stats.total, color: 'text-white' },
            { label: 'Rotti', value: stats.broken, color: stats.broken > 0 ? 'text-red-400' : 'text-gray-500' },
            { label: 'Fermi', value: stats.stuck, color: stats.stuck > 0 ? 'text-yellow-400' : 'text-gray-500' },
            { label: 'Incompleti', value: stats.incomplete, color: stats.incomplete > 0 ? 'text-purple-400' : 'text-gray-500' },
          ].map(s => (
            <div key={s.label} className="bg-[#111113] border border-white/5 rounded-lg p-2 text-center">
              <p className={`text-lg font-black ${s.color}`}>{s.value}</p>
              <p className="text-[8px] text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Project cards — mobile-first vertical layout */}
      {projects.length > 0 && (
        <div className="space-y-2 max-h-[60vh] overflow-y-auto pb-2" data-testid="maint-projects">
          <p className="text-[10px] text-gray-500">{projects.length} progetti per <span className="text-white font-semibold">{targetUser}</span></p>
          {projects.map(p => {
            const fc = FLAG_CONFIG[p.flag] || FLAG_CONFIG.OK;
            const tc = TYPE_CONFIG[p.type] || TYPE_CONFIG.film;
            const progress = p.pipeline_total > 0 ? Math.round((p.pipeline_index / (p.pipeline_total - 1)) * 100) : 0;

            return (
              <Card key={p.id} className={`bg-[#0e0e10] ${fc.border}`} data-testid={`maint-project-${p.id}`}>
                <CardContent className="p-3 space-y-2">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${tc.bg} ${tc.color}`}>{tc.label}</span>
                        <Badge className={`text-[8px] h-4 ${fc.color}`}>{fc.label}</Badge>
                        {p.is_legacy && <span className="text-[7px] text-orange-400 bg-orange-500/10 px-1 rounded">LEGACY</span>}
                      </div>
                      <p className="text-xs font-semibold text-white mt-1 truncate">{p.title}</p>
                    </div>
                    <span className="text-[9px] text-gray-500 flex-shrink-0 whitespace-nowrap">{p.idle_text}</span>
                  </div>

                  {/* Status + progress bar */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[9px]">
                      <span className="text-gray-400">
                        Step: <span className="text-white font-semibold">{p.status}</span>
                        {p.next_step && <span className="text-gray-600"> → {p.next_step}</span>}
                      </span>
                      <span className="text-gray-500">{progress}%</span>
                    </div>
                    <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-amber-500 to-red-500 rounded-full transition-all" style={{ width: `${progress}%` }} />
                    </div>
                  </div>

                  {/* Issues */}
                  {p.issues.length > 0 && (
                    <div className="space-y-0.5">
                      {p.issues.map((issue, i) => (
                        <p key={i} className="text-[9px] text-gray-400 flex items-start gap-1">
                          <AlertTriangle className="w-3 h-3 text-yellow-500 flex-shrink-0 mt-0.5" />
                          {issue}
                        </p>
                      ))}
                    </div>
                  )}

                  {/* Data indicators */}
                  <div className="flex gap-2 flex-wrap">
                    {[
                      { label: 'Cast', ok: p.has_cast },
                      { label: 'Genere', ok: p.has_genre },
                      { label: 'Script', ok: p.has_screenplay },
                      { label: 'Poster', ok: p.has_poster },
                    ].map(d => (
                      <span key={d.label} className={`text-[8px] px-1.5 py-0.5 rounded ${d.ok ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                        {d.ok ? <CheckCircle className="w-2.5 h-2.5 inline mr-0.5" /> : <XCircle className="w-2.5 h-2.5 inline mr-0.5" />}
                        {d.label}
                      </span>
                    ))}
                    {p.quality_score != null && (
                      <span className="text-[8px] px-1.5 py-0.5 rounded bg-yellow-500/10 text-yellow-400">Q: {Math.round(p.quality_score)}%</span>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div className="grid grid-cols-2 gap-1.5 pt-1">
                    <Button size="sm" className="bg-emerald-700 hover:bg-emerald-600 text-[9px] h-7"
                      onClick={() => execAction(p.id, p.type, 'auto_fix')}
                      disabled={!!actionLoading} data-testid={`maint-autofix-${p.id}`}>
                      {actionLoading === `${p.id}-auto_fix` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wrench className="w-3 h-3 mr-0.5" />}
                      Fix Automatico
                    </Button>
                    <Button size="sm" className="bg-blue-700 hover:bg-blue-600 text-[9px] h-7"
                      onClick={() => execAction(p.id, p.type, 'force_step')}
                      disabled={!!actionLoading || !p.next_step} data-testid={`maint-force-${p.id}`}>
                      {actionLoading === `${p.id}-force_step` ? <Loader2 className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3 mr-0.5" />}
                      Forza Step
                    </Button>
                    <Button size="sm" className="bg-amber-700 hover:bg-amber-600 text-[9px] h-7"
                      onClick={() => execAction(p.id, p.type, 'complete_project')}
                      disabled={!!actionLoading} data-testid={`maint-complete-${p.id}`}>
                      {actionLoading === `${p.id}-complete_project` ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3 mr-0.5" />}
                      Completa
                    </Button>
                    <Button size="sm" variant="outline" className="text-[9px] h-7 border-gray-700 text-gray-400 hover:bg-white/5"
                      onClick={() => execAction(p.id, p.type, 'reset_step')}
                      disabled={!!actionLoading || !p.prev_step} data-testid={`maint-reset-${p.id}`}>
                      {actionLoading === `${p.id}-reset_step` ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3 mr-0.5" />}
                      Reset Step
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {stats && projects.length === 0 && !loading && (
        <div className="text-center py-8">
          <CheckCircle className="w-8 h-8 text-green-500/40 mx-auto mb-2" />
          <p className="text-xs text-gray-500">Nessun progetto attivo per <span className="text-white">{targetUser}</span></p>
        </div>
      )}

    </div>
  );
}

/* ─── Roles Management Tab (ADMIN only) ─── */
function RolesTab({ api }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  const searchUsers = useCallback(async (q) => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/search-users?q=${encodeURIComponent(q)}`);
      setUsers(res.data.users || []);
    } catch { toast.error('Errore ricerca'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { searchUsers(''); }, [searchUsers]);

  const setRole = async (userId, nickname, role) => {
    setActionLoading(userId);
    try {
      await api.post('/admin/set-user-role', { user_id: userId, role });
      toast.success(`${nickname} impostato come ${role}`);
      searchUsers(searchQuery);
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const ROLE_COLORS = {
    'ADMIN': 'bg-red-500/20 text-red-400 border-red-500/30',
    'CO_ADMIN': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    'MOD': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    'USER': 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };

  return (
    <div className="space-y-3" data-testid="admin-roles-tab">
      <form onSubmit={(e) => { e.preventDefault(); searchUsers(searchQuery); }}>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              placeholder="Cerca utente..."
              className="w-full bg-[#111113] border border-gray-800 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-gray-600 focus:border-amber-500/50 focus:outline-none"
              data-testid="roles-search-input" />
          </div>
          <Button type="submit" size="sm" className="bg-amber-600 hover:bg-amber-700 text-xs px-3" disabled={loading}
            data-testid="roles-search-btn">
            {loading ? '...' : 'Cerca'}
          </Button>
        </div>
      </form>

      <div className="space-y-1.5 max-h-[65vh] overflow-y-auto" data-testid="roles-user-list">
        {users.map(u => {
          const role = u.role || 'USER';
          const isNeo = u.nickname === 'NeoMorpheus';
          return (
            <Card key={u.id} className={`bg-[#111113] border-white/5 ${isNeo ? 'border-red-500/30' : ''}`} data-testid={`role-user-${u.nickname}`}>
              <CardContent className="p-2.5 flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500/20 to-red-500/20 flex items-center justify-center text-xs font-bold text-amber-400 flex-shrink-0">
                  {u.nickname?.[0]?.toUpperCase() || '?'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-white truncate">{u.nickname}</p>
                  <p className="text-[9px] text-gray-500 truncate">{u.email}</p>
                </div>
                <Badge className={`text-[8px] h-5 px-2 ${ROLE_COLORS[role] || ROLE_COLORS.USER}`}>{role}</Badge>
                {!isNeo && (
                  <div className="flex gap-1 flex-shrink-0">
                    {['CO_ADMIN', 'MOD', 'USER'].map(r => (
                      <button key={r}
                        disabled={actionLoading === u.id || role === r}
                        onClick={() => setRole(u.id, u.nickname, r)}
                        className={`px-1.5 py-0.5 rounded text-[8px] font-semibold transition-all disabled:opacity-30 ${
                          role === r ? 'bg-white/10 text-white' : 'bg-white/5 text-gray-500 hover:bg-white/10 hover:text-white'
                        }`}
                        data-testid={`set-role-${u.nickname}-${r}`}>
                        {r === 'CO_ADMIN' ? 'Co-Admin' : r === 'MOD' ? 'Mod' : 'User'}
                      </button>
                    ))}
                  </div>
                )}
                {isNeo && <span className="text-[8px] text-red-400 font-bold flex-shrink-0">PROTETTO</span>}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Deletions Tab (ADMIN only) ─── */
function DeletionsTab({ api }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  const loadRequests = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/deletion-requests');
      setRequests(res.data.requests || []);
    } catch { toast.error('Errore caricamento richieste'); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { loadRequests(); }, [loadRequests]);

  const handleAction = async (userId, action) => {
    setActionLoading(`${userId}-${action}`);
    try {
      await api.post(`/admin/deletion/${userId}/${action}`);
      const msgs = {
        'approve': 'Countdown 10 giorni avviato',
        'reject': 'Richiesta rifiutata (cooldown 5 giorni)',
        'final-approve': 'Account eliminato definitivamente',
        'final-reject': 'Cancellazione annullata',
      };
      toast.success(msgs[action] || 'Azione completata');
      loadRequests();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

  const STATUS_CONFIG = {
    'requested': { label: 'Richiesta', color: 'bg-yellow-500/20 text-yellow-400', icon: Clock },
    'countdown_active': { label: 'Countdown', color: 'bg-orange-500/20 text-orange-400', icon: Clock },
    'user_confirmed': { label: 'Confermato', color: 'bg-red-500/20 text-red-400', icon: AlertTriangle },
    'final_pending': { label: 'In Attesa Finale', color: 'bg-red-500/30 text-red-300', icon: AlertTriangle },
  };

  return (
    <div className="space-y-3" data-testid="admin-deletions-tab">
      <div className="flex items-center justify-between">
        <p className="text-[10px] text-gray-500">{requests.length} richieste in corso</p>
        <Button size="sm" variant="outline" className="text-[10px] h-6 border-gray-700 text-gray-400"
          onClick={loadRequests} disabled={loading} data-testid="deletions-refresh-btn">
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Aggiorna'}
        </Button>
      </div>

      {requests.length === 0 && !loading ? (
        <div className="text-center py-8">
          <CheckCircle className="w-8 h-8 text-gray-700 mx-auto mb-2" />
          <p className="text-xs text-gray-600">Nessuna richiesta di cancellazione in corso</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[65vh] overflow-y-auto" data-testid="deletions-list">
          {requests.map(r => {
            const cfg = STATUS_CONFIG[r.deletion_status] || { label: r.deletion_status, color: 'bg-gray-500/20 text-gray-400', icon: Clock };
            const StatusIcon = cfg.icon;
            const countdownEnd = r.deletion_countdown_end ? new Date(r.deletion_countdown_end) : null;
            const daysLeft = countdownEnd ? Math.max(0, Math.ceil((countdownEnd - new Date()) / (1000*60*60*24))) : null;

            return (
              <Card key={r.id} className="bg-[#111113] border-white/5" data-testid={`deletion-card-${r.id}`}>
                <CardContent className="p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-red-500/10 flex items-center justify-center text-xs font-bold text-red-400">
                        {r.nickname?.[0]?.toUpperCase() || '?'}
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-white">{r.nickname}</p>
                        <p className="text-[9px] text-gray-500">{r.email}</p>
                      </div>
                    </div>
                    <Badge className={`text-[8px] h-5 ${cfg.color}`}>
                      <StatusIcon className="w-3 h-3 mr-0.5" />{cfg.label}
                    </Badge>
                  </div>

                  {r.deletion_reason && (
                    <p className="text-[10px] text-gray-400 bg-black/30 rounded px-2 py-1">Motivo: "{r.deletion_reason}"</p>
                  )}

                  {r.deletion_requested_by_name && (
                    <p className="text-[9px] text-gray-500">Richiesto da: <span className="text-amber-400">{r.deletion_requested_by_name}</span></p>
                  )}

                  {daysLeft !== null && r.deletion_status === 'countdown_active' && (
                    <p className="text-[10px] text-orange-400 font-semibold">Countdown: {daysLeft} giorni rimanenti</p>
                  )}

                  {/* Actions based on status */}
                  <div className="flex gap-1.5 pt-1">
                    {r.deletion_status === 'requested' && (
                      <>
                        <Button size="sm" className="bg-red-600 hover:bg-red-700 text-[10px] h-6 px-2 flex-1"
                          onClick={() => handleAction(r.id, 'approve')}
                          disabled={!!actionLoading} data-testid={`deletion-approve-${r.id}`}>
                          <CheckCircle className="w-3 h-3 mr-0.5" /> Approva (10gg)
                        </Button>
                        <Button size="sm" variant="outline" className="text-[10px] h-6 px-2 flex-1 border-gray-700 text-gray-400"
                          onClick={() => handleAction(r.id, 'reject')}
                          disabled={!!actionLoading} data-testid={`deletion-reject-${r.id}`}>
                          <Ban className="w-3 h-3 mr-0.5" /> Rifiuta
                        </Button>
                      </>
                    )}
                    {(r.deletion_status === 'user_confirmed' || r.deletion_status === 'final_pending') && (
                      <>
                        <Button size="sm" className="bg-red-600 hover:bg-red-700 text-[10px] h-6 px-2 flex-1"
                          onClick={() => handleAction(r.id, 'final-approve')}
                          disabled={!!actionLoading} data-testid={`deletion-final-approve-${r.id}`}>
                          <Trash2 className="w-3 h-3 mr-0.5" /> Elimina Definitivamente
                        </Button>
                        <Button size="sm" variant="outline" className="text-[10px] h-6 px-2 flex-1 border-gray-700 text-gray-400"
                          onClick={() => handleAction(r.id, 'final-reject')}
                          disabled={!!actionLoading} data-testid={`deletion-final-reject-${r.id}`}>
                          <XCircle className="w-3 h-3 mr-0.5" /> Annulla
                        </Button>
                      </>
                    )}
                    {r.deletion_status === 'countdown_active' && (
                      <p className="text-[9px] text-gray-500 italic">In attesa della scadenza del countdown...</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── DB Management Card (rendered directly by AdminPage — bypasses prop issues) ─── */
function DbManagementCard({ api }) {
  const [importFile, setImportFile] = useState(null);
  const [importFileName, setImportFileName] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [dbLoading, setDbLoading] = useState(null);
  const [dbResult, setDbResult] = useState(null);

  return (
    <Card className="bg-[#111113] border-indigo-500/30" data-testid="db-management-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-indigo-400 flex items-center gap-2">
          <Wrench className="w-4 h-4" />
          Gestione Database
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-xs text-gray-400">Esporta, importa (safe) o resetta (hard) il database completo.</p>

        {/* EXPORT */}
        <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold"
          disabled={dbLoading === 'export'}
          data-testid="db-export-btn"
          onClick={async () => {
            setDbLoading('export');
            setDbResult(null);
            try {
              const token = localStorage.getItem('cineworld_token');
              const backendUrl = process.env.REACT_APP_BACKEND_URL;
              const downloadUrl = `${backendUrl}/api/admin/db/download-backup?token=${token}`;
              window.open(downloadUrl, '_blank');
              toast.success('Download backup avviato!');
            } catch (e) { toast.error('Errore avvio download'); }
            finally { setDbLoading(null); }
          }}>
          {dbLoading === 'export' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Download className="w-3 h-3 mr-1" />}
          Scarica Backup
        </Button>

        {dbResult?.type === 'export' && (
          <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-2 text-[10px] text-indigo-300">
            Esportati: {Object.entries(dbResult.counts).map(([k,v]) => `${k}: ${v}`).join(' | ')}
          </div>
        )}

        {/* TEXTAREA JSON */}
        <div className="w-full">
          <input
            type="file"
            accept=".json,.zip"
            id="db-import-file"
            className="hidden"
            data-testid="db-import-file"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              setImportFile(file);
              setImportFileName(`${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`);
              toast.success(`File selezionato: ${file.name}`);
            }}
          />
          <label htmlFor="db-import-file">
            <Button
              type="button"
              className="w-full bg-gray-700 hover:bg-gray-600 text-white text-xs font-semibold cursor-pointer"
              disabled={dbLoading === 'reading'}
              onClick={() => document.getElementById('db-import-file').click()}
              data-testid="db-import-file-btn"
            >
              <Upload className="w-3 h-3 mr-1" />
              {dbLoading === 'reading' ? 'Caricamento...' : importFileName ? `${importFileName}` : 'Carica file (.json / .zip)'}
            </Button>
          </label>
        </div>

        {/* IMPORT SAFE */}
        <Button className="w-full bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold"
          disabled={dbLoading === 'import-safe' || !importFile}
          data-testid="db-import-safe-btn"
          onClick={async () => {
            setDbLoading('import-safe');
            setDbResult(null);
            try {
              const formData = new FormData();
              formData.append('file', importFile);
              const res = await api.post('/admin/db/import-file-safe', formData, {
                timeout: 300000,
                headers: { 'Content-Type': 'multipart/form-data' }
              });
              toast.success('Import safe completato');
              setDbResult({ type: 'import-safe', stats: res.data.stats });
            } catch (e) {
              toast.error(e.response?.data?.detail || 'Errore import');
            }
            finally { setDbLoading(null); }
          }}>
          {dbLoading === 'import-safe' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <CheckCircle className="w-3 h-3 mr-1" />}
          Import Safe (upsert)
        </Button>

        {dbResult?.type === 'import-safe' && dbResult.stats && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-2 text-[10px] text-emerald-300 space-y-0.5">
            {Object.entries(dbResult.stats).map(([k,v]) => (
              <p key={k}>{k}: +{v.inserted} inseriti, ~{v.updated} aggiornati, -{v.skipped} saltati</p>
            ))}
          </div>
        )}

        {/* IMPORT HARD SEPARATOR */}
        <div className="border-t border-red-500/20 pt-3 mt-2">
          <p className="text-[10px] text-red-400 font-bold mb-2 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> Hard Reset — Cancella e reimporta tutto
          </p>
          <input
            type="text"
            placeholder='Scrivi CONFERMO per procedere'
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            className="w-full bg-black/60 text-red-400 text-xs border border-red-500/30 p-2 rounded-lg placeholder-red-800 focus:border-red-500/60 focus:outline-none"
            data-testid="db-hard-confirm-input"
          />
          <Button className="w-full mt-2 bg-red-700 hover:bg-red-600 text-white text-xs font-semibold"
            disabled={dbLoading === 'import-hard' || !importFile || confirmText !== 'CONFERMO'}
            data-testid="db-import-hard-btn"
            onClick={async () => {
              if (confirmText !== 'CONFERMO') { toast.error('Devi scrivere CONFERMO'); return; }
              setDbLoading('import-hard');
              setDbResult(null);
              try {
                const formData = new FormData();
                formData.append('file', importFile);
                const res = await api.post('/admin/db/import-file-hard?confirm=CONFERMO', formData, {
                  timeout: 300000,
                  headers: { 'Content-Type': 'multipart/form-data' }
                });
                toast.success('Import HARD completato');
                setDbResult({ type: 'import-hard', stats: res.data.stats });
                setConfirmText('');
              } catch (e) {
                toast.error(e.response?.data?.detail || 'Errore import hard');
              }
              finally { setDbLoading(null); }
            }}>
            {dbLoading === 'import-hard' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Trash2 className="w-3 h-3 mr-1" />}
            Import HARD (reset)
          </Button>

          {dbResult?.type === 'import-hard' && dbResult.stats && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-2 mt-2 text-[10px] text-red-300 space-y-0.5">
              <p className="font-bold">Reset completato:</p>
              {Object.entries(dbResult.stats).map(([k,v]) => (
                <p key={k}>{k}: {v.deleted} eliminati, {v.inserted} reinseriti</p>
              ))}
              {dbResult.backup && (
                <p className="text-gray-500 mt-1">Backup: {Object.entries(dbResult.backup).map(([k,v]) => `${k}: ${v}`).join(' | ')}</p>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/* ─── Main Admin Page ─── */
export default function AdminPage() {
  const { api, user } = useContext(AuthContext);
  const isAdmin = user?.nickname === 'NeoMorpheus';
  const isCoadmin = user?.role === 'CO_ADMIN';
  const hasAccess = isAdmin || isCoadmin;
  const tabs = isAdmin ? ADMIN_TABS : COADMIN_TABS;
  const [activeTab, setActiveTab] = useState(tabs[0]?.id || 'reports');

  if (!hasAccess) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center p-4">
        <Card className="bg-[#111113] border-red-500/30 max-w-sm w-full">
          <CardContent className="p-6 text-center">
            <Shield className="w-10 h-10 mx-auto mb-3 text-red-500/50" />
            <p className="text-sm text-red-400 font-semibold">Accesso Negato</p>
            <p className="text-xs text-gray-500 mt-1">Permessi insufficienti per accedere a questa pagina.</p>
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
          <div className={`p-2 rounded-lg ${isAdmin ? 'bg-red-500/15' : 'bg-amber-500/15'}`}>
            <Shield className={`w-5 h-5 ${isAdmin ? 'text-red-400' : 'text-amber-400'}`} />
          </div>
          <div>
            <h1 className="text-lg font-black text-white tracking-tight">
              {isAdmin ? 'Pannello Admin' : 'Pannello Co-Admin'}
            </h1>
            <p className="text-[10px] text-gray-500">
              {isAdmin ? 'Controllo completo del sistema' : 'Segnalazioni e manutenzione'}
            </p>
          </div>
          <Badge className={`ml-auto text-[9px] h-5 ${isAdmin ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
            {isAdmin ? 'ADMIN' : 'CO_ADMIN'}
          </Badge>
        </div>

        {/* Tabs — scroll orizzontale su mobile */}
        <div className="flex gap-1 bg-[#111113] rounded-lg p-1 border border-white/5 overflow-x-auto no-scrollbar" data-testid="admin-tabs">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center justify-center gap-1.5 py-2.5 px-3 sm:px-4 rounded-md text-xs font-semibold transition-all whitespace-nowrap flex-shrink-0 min-w-[44px] sm:min-w-0 sm:flex-1 ${
                  isActive
                    ? (isAdmin ? 'bg-red-600 text-white' : 'bg-amber-600 text-white')
                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                }`}
                data-testid={`admin-tab-${tab.id}`}>
                <Icon className="w-4 h-4 sm:w-3.5 sm:h-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        {activeTab === 'users' && isAdmin && <UsersTab api={api} />}
        {activeTab === 'films' && isAdmin && <FilmsTab api={api} />}
        {activeTab === 'roles' && isAdmin && <RolesTab api={api} />}
        {activeTab === 'reports' && <ReportsTab api={api} />}
        {activeTab === 'deletions' && isAdmin && <DeletionsTab api={api} />}
        {activeTab === 'maintenance' && <MaintenanceTab api={api} />}
        {activeTab === 'maintenance' && isAdmin && <DbManagementCard api={api} />}
      </div>
    </div>
  );
}
