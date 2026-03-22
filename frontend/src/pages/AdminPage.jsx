import React, { useState, useEffect, useContext, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Shield, Search, DollarSign, Coins, ChevronRight, Minus, Plus, Film, Users, Trash2, AlertTriangle, X, Loader2 } from 'lucide-react';
import { AuthContext } from '../contexts';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

/* ─── Tab constants ─── */
const TABS = [
  { id: 'users', label: 'Gestione Utenti', icon: Users },
  { id: 'films', label: 'Gestione Film', icon: Film },
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

      {/* Film grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 max-h-[60vh] overflow-y-auto pb-2"
        data-testid="admin-film-grid">
        {films.map(f => (
          <div key={f.id} className="group relative bg-[#111113] border border-white/5 rounded-lg overflow-hidden hover:border-red-500/30 transition-all"
            data-testid={`admin-film-card-${f.id}`}>
            {/* Poster */}
            <div className="aspect-[2/3] bg-gray-900 relative">
              {f.poster_url ? (
                <img src={`${API_BASE}${f.poster_url}`} alt={f.title}
                  className="w-full h-full object-cover"
                  onError={e => { e.target.style.display='none'; }} />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Film className="w-6 h-6 text-gray-700" />
                </div>
              )}
              {/* Delete overlay on hover */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/60 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                <Button size="sm" className="bg-red-600 hover:bg-red-700 text-[10px] h-7 px-2"
                  onClick={() => setDeleteTarget(f)}
                  data-testid={`admin-film-delete-${f.id}`}>
                  <Trash2 className="w-3 h-3 mr-1" /> Elimina
                </Button>
              </div>
            </div>
            {/* Info */}
            <div className="p-1.5">
              <p className="text-[10px] font-semibold text-white truncate leading-tight" title={f.title}>{f.title}</p>
              <p className="text-[8px] text-gray-500 truncate">{f.studio_name}</p>
              <div className="flex items-center gap-1 mt-0.5">
                {f.genre && <Badge className="text-[6px] h-3 bg-gray-800 text-gray-400 px-1">{f.genre}</Badge>}
                {f.quality_score != null && <span className="text-[8px] text-yellow-500">{Math.round(f.quality_score)}%</span>}
              </div>
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
      <div className="max-w-4xl mx-auto space-y-4">
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
      </div>
    </div>
  );
}
