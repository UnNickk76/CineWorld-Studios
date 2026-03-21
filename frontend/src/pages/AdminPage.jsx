import React, { useState, useEffect, useContext, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Shield, Search, DollarSign, Coins, Users, ChevronRight, Minus, Plus } from 'lucide-react';
import { AuthContext } from '../contexts';

export default function AdminPage() {
  const { api, user } = useContext(AuthContext);
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [moneyAmount, setMoneyAmount] = useState('');
  const [cpAmount, setCpAmount] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  const isAdmin = user?.nickname === 'NeoMorpheus';

  const searchUsers = useCallback(async (q) => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/search-users?q=${encodeURIComponent(q)}`);
      setUsers(res.data.users || []);
    } catch (e) {
      if (e.response?.status === 403) toast.error('Accesso negato');
      else toast.error('Errore ricerca');
    } finally { setLoading(false); }
  }, [api]);

  useEffect(() => {
    if (isAdmin) searchUsers('');
  }, [isAdmin, searchUsers]);

  const handleSearch = (e) => {
    e.preventDefault();
    searchUsers(searchQuery);
  };

  const modifyFunds = async (nickname, amount) => {
    if (!amount || isNaN(amount)) return;
    setActionLoading(`money-${nickname}`);
    try {
      const res = await api.post('/admin/add-money', { nickname, amount: Number(amount) });
      toast.success(`${nickname}: $${res.data.old_funds.toLocaleString()} → $${res.data.new_funds.toLocaleString()}`);
      setMoneyAmount('');
      searchUsers(searchQuery);
      if (selectedUser?.nickname === nickname) {
        setSelectedUser(prev => ({ ...prev, funds: res.data.new_funds }));
      }
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
      if (selectedUser?.nickname === nickname) {
        setSelectedUser(prev => ({ ...prev, cinepass: res.data.new_cinepass }));
      }
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    finally { setActionLoading(null); }
  };

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
      <div className="max-w-lg mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center gap-2.5 mb-2">
          <div className="p-2 bg-red-500/15 rounded-lg"><Shield className="w-5 h-5 text-red-400" /></div>
          <div>
            <h1 className="text-lg font-black text-white tracking-tight">Pannello Admin</h1>
            <p className="text-[10px] text-gray-500">Gestione utenti, denaro e crediti</p>
          </div>
        </div>

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
        <div className="space-y-1.5" data-testid="admin-user-list">
          {users.map(u => (
            <Card key={u.id}
              className={`bg-[#111113] cursor-pointer transition-all ${selectedUser?.id === u.id ? 'border-red-500/40 ring-1 ring-red-500/20' : 'border-white/5 hover:border-gray-700'}`}
              onClick={() => { setSelectedUser(u); setMoneyAmount(''); setCpAmount(''); }}
              data-testid={`admin-user-${u.nickname}`}>
              <CardContent className="p-2.5 flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500/20 to-orange-500/20 flex items-center justify-center text-xs font-bold text-red-400">
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
                {selectedUser.nickname}
                <Badge className="bg-gray-800 text-gray-400 text-[8px] ml-auto">LV {Math.floor((selectedUser.xp || 0) / 1000)}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0 space-y-3">
              {/* Current balances */}
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
                    disabled={!moneyAmount || actionLoading}
                    data-testid="admin-money-add">
                    <Plus className="w-3 h-3" />
                  </Button>
                  <Button size="sm" className="bg-red-700 hover:bg-red-600 text-[10px] h-7 px-2"
                    onClick={() => modifyFunds(selectedUser.nickname, -Math.abs(Number(moneyAmount)))}
                    disabled={!moneyAmount || actionLoading}
                    data-testid="admin-money-remove">
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
                    disabled={!cpAmount || actionLoading}
                    data-testid="admin-cp-add">
                    <Plus className="w-3 h-3" />
                  </Button>
                  <Button size="sm" className="bg-red-700 hover:bg-red-600 text-[10px] h-7 px-2"
                    onClick={() => modifyCinepass(selectedUser.nickname, -Math.abs(Number(cpAmount)))}
                    disabled={!cpAmount || actionLoading}
                    data-testid="admin-cp-remove">
                    <Minus className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
