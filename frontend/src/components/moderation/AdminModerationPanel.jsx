import React, { useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts';
import { AlertTriangle, ShieldOff, ShieldCheck, MessageSquareOff, MessageSquare, Trash2, X, Loader2, Search, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import BanDurationModal from './BanDurationModal';
import CineConfirm from '../v3/CineConfirm';

const CAT_LABELS = {
  inappropriato: '⚠️ Inappropriato',
  spam: '📨 Spam',
  plagio: '📑 Plagio',
  offensivo: '🚫 Offensivo',
  altro: '❓ Altro',
};

export default function AdminModerationPanel() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [tab, setTab] = useState('content'); // content | users
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  // User search
  const [query, setQuery] = useState('');
  const [userResults, setUserResults] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userHistory, setUserHistory] = useState(null);

  // Ban modal
  const [banTarget, setBanTarget] = useState(null);
  const [banBusy, setBanBusy] = useState(false);
  // Velion confirms
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [reportConfirm, setReportConfirm] = useState(null);
  const [unbanConfirm, setUnbanConfirm] = useState(null);

  const loadReports = async () => {
    setLoading(true);
    try {
      const r = await api.get('/admin/reports');
      setItems(r.data.items || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore caricamento segnalazioni');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadReports(); }, []);

  const dismiss = async (reportId, contentId) => {
    setBusyId(reportId);
    try {
      await api.post(`/admin/reports/${reportId}/dismiss`);
      toast.success('Segnalazione archiviata');
      await loadReports();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore');
    } finally {
      setBusyId(null);
    }
  };

  const deleteContent = (group) => setDeleteConfirm(group);
  const confirmDelete = async () => {
    const group = deleteConfirm;
    if (!group) return;
    setBusyId(group.content_id);
    try {
      await api.delete(`/admin/content/${group.content_type}/${group.content_id}`);
      toast.success('Contenuto eliminato + segnalazione automatica inviata');
      setDeleteConfirm(null);
      await loadReports();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore');
    } finally {
      setBusyId(null);
    }
  };

  const openContent = (group) => {
    if (group.content_type === 'lampo') navigate(`/lampo/${group.content_id}`);
    else navigate(`/film/${group.content_id}`);
  };

  // ─── User tab ───
  const searchUsers = async () => {
    if (!query.trim()) return;
    try {
      const r = await api.get(`/admin/search-users?q=${encodeURIComponent(query.trim())}`);
      setUserResults(r.data.users || r.data || []);
    } catch (e) {
      toast.error('Errore ricerca utenti');
    }
  };

  const selectUser = async (u) => {
    setSelectedUser(u);
    try {
      const r = await api.get(`/admin/reports/user/${u.id}`);
      setUserHistory(r.data);
    } catch (e) {
      toast.error('Errore caricamento storico');
    }
  };

  const handleManualReport = () => {
    if (!selectedUser) return;
    setReportConfirm(selectedUser);
  };
  const confirmManualReport = async () => {
    if (!reportConfirm) return;
    try {
      await api.post(`/admin/users/${reportConfirm.id}/manual-report`, { category: 'inappropriato', notes: 'Segnalazione admin' });
      toast.success('Segnalazione inviata + notifica al player');
      setReportConfirm(null);
      await selectUser(selectedUser);
    } catch (e) { toast.error(e?.response?.data?.detail || 'Errore'); }
  };

  const handleConfirmBan = async ({ duration, reason }) => {
    setBanBusy(true);
    try {
      await api.post(`/admin/users/${banTarget.id}/ban`, { duration, reason });
      toast.success(`Ban applicato: ${duration}`);
      setBanTarget(null);
      if (selectedUser?.id === banTarget.id) await selectUser(selectedUser);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore');
    } finally { setBanBusy(false); }
  };

  const handleUnban = (u) => setUnbanConfirm(u);
  const confirmUnban = async () => {
    if (!unbanConfirm) return;
    try {
      await api.post(`/admin/users/${unbanConfirm.id}/unban`, { reason: 'Sblocco admin' });
      toast.success('Utente sbloccato');
      setUnbanConfirm(null);
      if (selectedUser?.id === unbanConfirm.id) await selectUser(selectedUser);
    } catch (e) { toast.error(e?.response?.data?.detail || 'Errore'); }
  };

  const handleChatToggle = async (u) => {
    try {
      const path = u.is_chat_muted ? `/admin/users/${u.id}/chat-unmute` : `/admin/users/${u.id}/chat-mute`;
      await api.post(path);
      toast.success(u.is_chat_muted ? 'Chat sbloccata' : 'Chat bloccata');
      if (selectedUser?.id === u.id) await selectUser(selectedUser);
    } catch (e) { toast.error('Errore'); }
  };

  return (
    <div className="space-y-3" data-testid="admin-moderation-panel">
      <div className="flex gap-1.5">
        <button onClick={() => setTab('content')} data-testid="mod-tab-content" className={`flex-1 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${tab === 'content' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-zinc-900/40 text-zinc-400 border border-zinc-700'}`}>
          🚨 Locandine ({items.length})
        </button>
        <button onClick={() => setTab('users')} data-testid="mod-tab-users" className={`flex-1 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${tab === 'users' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-zinc-900/40 text-zinc-400 border border-zinc-700'}`}>
          👥 Segnalazioni Utenti
        </button>
      </div>

      {tab === 'content' && (
        <>
          {loading ? (
            <div className="text-center py-6 text-zinc-500"><Loader2 className="w-5 h-5 animate-spin inline" /></div>
          ) : items.length === 0 ? (
            <div className="text-center py-8 text-zinc-500 text-xs">Nessuna locandina segnalata.</div>
          ) : (
            <div className="space-y-2">
              {items.map(g => (
                <div key={g.content_id} className="rounded-xl border border-rose-500/20 bg-rose-950/10 p-3" data-testid={`mod-report-${g.content_id}`}>
                  <div className="flex gap-3">
                    {g.content_poster_url ? (
                      <button onClick={() => openContent(g)} className="flex-shrink-0">
                        <img src={g.content_poster_url} alt={g.content_title} className="w-16 h-22 object-cover rounded border border-zinc-700 hover:border-rose-400" />
                      </button>
                    ) : (
                      <div className="w-16 h-22 bg-zinc-800 rounded flex items-center justify-center text-[8px] text-zinc-500">{g.content_type}</div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="px-1.5 py-0.5 rounded bg-rose-500/30 border border-rose-500/50 text-rose-100 text-[9px] font-black">{g.count}× SEGN.</span>
                        {g.target_is_admin && <span className="px-1.5 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-200 text-[9px] font-black">ADMIN/MOD</span>}
                        <span className="text-[10px] font-bold text-white truncate">{g.content_title}</span>
                      </div>
                      <p className="text-[9px] text-zinc-400 mb-1">@{g.target_user_nickname} · {g.content_type}</p>
                      <div className="flex flex-wrap gap-1 mb-1.5">
                        {(g.categories || []).map(c => (
                          <span key={c} className="text-[8px] px-1 py-0.5 rounded bg-zinc-800 text-zinc-300">{CAT_LABELS[c] || c}</span>
                        ))}
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        <button onClick={() => openContent(g)} data-testid={`mod-open-${g.content_id}`} className="px-2 py-1 rounded text-[9px] font-bold bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25 flex items-center gap-1">
                          <ExternalLink className="w-2.5 h-2.5" /> Apri
                        </button>
                        <button onClick={() => deleteContent(g)} disabled={busyId === g.content_id} data-testid={`mod-delete-${g.content_id}`} className="px-2 py-1 rounded text-[9px] font-bold bg-rose-500/15 border border-rose-500/30 text-rose-300 hover:bg-rose-500/25 flex items-center gap-1 disabled:opacity-50">
                          <Trash2 className="w-2.5 h-2.5" /> Elimina
                        </button>
                        {(g.reports || []).slice(0, 1).map(r => (
                          <button key={r.id} onClick={() => dismiss(r.id, g.content_id)} disabled={busyId === r.id} data-testid={`mod-dismiss-${r.id}`} className="px-2 py-1 rounded text-[9px] font-bold bg-zinc-700 border border-zinc-600 text-zinc-300 hover:bg-zinc-600 flex items-center gap-1 disabled:opacity-50">
                            <X className="w-2.5 h-2.5" /> Archivia 1
                          </button>
                        ))}
                      </div>
                      {g.reports && g.reports.length > 0 && g.reports[0].notes && (
                        <p className="text-[9px] text-zinc-400 italic mt-1.5 line-clamp-2">"{g.reports[0].notes}" — @{g.reports[0].reporter_nickname}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'users' && (
        <>
          <div className="flex gap-1.5">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchUsers()}
              placeholder="Cerca utente per nickname o email…"
              data-testid="mod-user-search"
              className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-2.5 py-2 text-xs text-white"
            />
            <button onClick={searchUsers} className="px-3 rounded-lg bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-[10px] font-bold flex items-center gap-1">
              <Search className="w-3 h-3" /> Cerca
            </button>
          </div>

          {userResults.length > 0 && (
            <div className="rounded-lg border border-zinc-700 bg-zinc-900/40 p-1.5 space-y-1">
              {userResults.slice(0, 10).map(u => (
                <button key={u.id} onClick={() => selectUser(u)} data-testid={`mod-select-user-${u.id}`} className={`w-full text-left px-2 py-1.5 rounded text-xs flex items-center justify-between gap-2 ${selectedUser?.id === u.id ? 'bg-cyan-500/15 text-cyan-200' : 'text-zinc-300 hover:bg-zinc-800'}`}>
                  <span className="truncate">@{u.nickname}</span>
                  <span className="flex items-center gap-1.5 flex-shrink-0">
                    {u.is_banned && <span className="text-[8px] px-1 py-0.5 rounded bg-rose-500/30 text-rose-200 font-bold">BAN</span>}
                    {u.is_chat_muted && <span className="text-[8px] px-1 py-0.5 rounded bg-amber-500/30 text-amber-200 font-bold">MUTE</span>}
                  </span>
                </button>
              ))}
            </div>
          )}

          {selectedUser && userHistory && (
            <div className="rounded-xl border border-zinc-700 bg-zinc-900/40 p-3 space-y-2.5" data-testid="mod-user-detail">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-bold text-white">@{selectedUser.nickname}</p>
                  <p className="text-[9px] text-zinc-400">{userHistory.user.email}</p>
                </div>
                <div className="flex items-center gap-1">
                  {userHistory.user.is_banned && <span className="text-[8px] px-1.5 py-0.5 rounded bg-rose-500/30 text-rose-200 font-bold">BAN</span>}
                  {userHistory.user.is_chat_muted && <span className="text-[8px] px-1.5 py-0.5 rounded bg-amber-500/30 text-amber-200 font-bold">CHAT MUTED</span>}
                  {userHistory.user.is_deleted && <span className="text-[8px] px-1.5 py-0.5 rounded bg-zinc-700 text-zinc-300 font-bold">ELIMINATO</span>}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-rose-500/10 border border-rose-500/30 p-2 text-center">
                  <p className="text-[8px] uppercase text-rose-300 font-bold">Segnalazioni Attive</p>
                  <p className="text-2xl font-black text-rose-200">{userHistory.report_count_active}/{userHistory.report_threshold}</p>
                  {userHistory.next_decay_at && <p className="text-[7px] text-rose-400/70">Decay: {new Date(userHistory.next_decay_at).toLocaleDateString('it-IT')}</p>}
                </div>
                <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-2 text-center">
                  <p className="text-[8px] uppercase text-amber-300 font-bold">Ban Totali</p>
                  <p className="text-2xl font-black text-amber-200">{userHistory.ban_count_total}/{userHistory.max_bans_before_deletion}</p>
                  <p className="text-[7px] text-amber-400/70">Al {userHistory.max_bans_before_deletion}° → eliminazione</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5">
                <button onClick={handleManualReport} disabled={userHistory.user.is_deleted} data-testid="mod-manual-report-btn" className="flex-1 px-2 py-1.5 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 text-[10px] font-bold hover:bg-rose-500/25 disabled:opacity-50 flex items-center justify-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Segnala
                </button>
                {userHistory.user.is_banned ? (
                  <button onClick={() => handleUnban(selectedUser)} data-testid="mod-unban-btn" className="flex-1 px-2 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold hover:bg-emerald-500/25 flex items-center justify-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> Sbanna
                  </button>
                ) : (
                  <button onClick={() => setBanTarget(selectedUser)} disabled={userHistory.user.is_deleted} data-testid="mod-ban-btn" className="flex-1 px-2 py-1.5 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 text-[10px] font-bold hover:bg-rose-500/25 disabled:opacity-50 flex items-center justify-center gap-1">
                    <ShieldOff className="w-3 h-3" /> Ban
                  </button>
                )}
                <button onClick={() => handleChatToggle({ ...selectedUser, is_chat_muted: userHistory.user.is_chat_muted })} data-testid="mod-chat-toggle-btn" className="flex-1 px-2 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-300 text-[10px] font-bold hover:bg-amber-500/25 flex items-center justify-center gap-1">
                  {userHistory.user.is_chat_muted ? <><MessageSquare className="w-3 h-3" /> Sblocca chat</> : <><MessageSquareOff className="w-3 h-3" /> Muta chat</>}
                </button>
              </div>

              {userHistory.bans?.length > 0 && (
                <div>
                  <p className="text-[9px] uppercase text-zinc-400 font-bold mb-1">Storico Ban ({userHistory.bans.length})</p>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {userHistory.bans.map(b => (
                      <div key={b.id} className="text-[9px] bg-zinc-950 rounded p-1.5 flex justify-between gap-2">
                        <span className="text-rose-300">#{b.ban_number} {b.duration_label}</span>
                        <span className="text-zinc-400">{new Date(b.started_at).toLocaleDateString('it-IT')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {userHistory.reports?.length > 0 && (
                <div>
                  <p className="text-[9px] uppercase text-zinc-400 font-bold mb-1">Segnalazioni ricevute ({userHistory.reports.length})</p>
                  <div className="space-y-1 max-h-40 overflow-y-auto">
                    {userHistory.reports.map(r => (
                      <div key={r.id} className="text-[9px] bg-zinc-950 rounded p-1.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-rose-300 font-bold">{CAT_LABELS[r.category] || r.category}</span>
                          <span className="text-zinc-500">{new Date(r.created_at).toLocaleDateString('it-IT')}</span>
                        </div>
                        <p className="text-zinc-400 truncate">{r.content_title}</p>
                        {r.notes && <p className="text-zinc-500 italic">"{r.notes}"</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      <BanDurationModal
        open={!!banTarget}
        target={banTarget}
        onCancel={() => setBanTarget(null)}
        onConfirm={handleConfirmBan}
        busy={banBusy}
      />
      <CineConfirm
        open={!!deleteConfirm}
        title={`Eliminare "${deleteConfirm?.content_title}"?`}
        subtitle={`Verrà eliminato il contenuto e inviata una segnalazione automatica al proprietario @${deleteConfirm?.target_user_nickname} con motivo "violazione regole interne".`}
        confirmLabel="Conferma Eliminazione"
        confirmTone="rose"
        onConfirm={confirmDelete}
        onCancel={() => setDeleteConfirm(null)}
      />
      <CineConfirm
        open={!!reportConfirm}
        title={`Segnalare @${reportConfirm?.nickname}?`}
        subtitle="Verrà inviata una notifica standard al player. Il counter sale di 1."
        confirmLabel="Conferma Segnalazione"
        confirmTone="rose"
        onConfirm={confirmManualReport}
        onCancel={() => setReportConfirm(null)}
      />
      <CineConfirm
        open={!!unbanConfirm}
        title={`Sbloccare @${unbanConfirm?.nickname}?`}
        subtitle="Il counter dei ban totali resta invariato."
        confirmLabel="Conferma Sblocco"
        confirmTone="amber"
        onConfirm={confirmUnban}
        onCancel={() => setUnbanConfirm(null)}
      />
    </div>
  );
}
