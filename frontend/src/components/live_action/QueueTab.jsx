/**
 * QueueTab — contratti acquistati ma LA non ancora avviato.
 * Click → avvia produzione (delegando a CreateLiveActionPage flow esistente).
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Loader2, Clock, Play, Star, Zap, AlertTriangle } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;
async function api(path, method = 'GET', body = null) {
  const tk = localStorage.getItem('cineworld_token');
  const r = await fetch(`${API}${path}`, {
    method, headers: { Authorization: `Bearer ${tk}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await r.text();
  let d = {};
  try { d = t ? JSON.parse(t) : {}; } catch { d = { detail: t }; }
  if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : `HTTP ${r.status}`);
  return d;
}

const fmtMoney = (v) => `$${Number(v || 0).toLocaleString()}`;
const daysLeft = (iso) => {
  if (!iso) return 0;
  const ms = new Date(iso).getTime() - Date.now();
  return Math.max(0, Math.floor(ms / 86400000));
};

export default function QueueTab({ onProduce, onToast }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);
  const [mode, setMode] = useState('classic'); // produzione default

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await api('/api/live-action-market/contracts/pending');
      setItems(d.items || []);
    } catch (e) { onToast && onToast(e.message, 'error'); }
    setLoading(false);
  }, []); // eslint-disable-line
  useEffect(() => { load(); }, [load]);

  const startProduction = async (contract) => {
    setBusy(contract.id);
    try {
      const d = await api('/api/live-action/create', 'POST', {
        contract_id: contract.id,
        origin_id: contract.origin_id,
        origin_kind: contract.origin_kind,
        mode,
      });
      onToast && onToast('Live Action avviato!');
      onProduce && onProduce(d);
    } catch (e) {
      onToast && onToast(e.message, 'error');
    }
    setBusy(null);
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></div>;
  }
  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-xs space-y-2" data-testid="la-queue-empty">
        <p>Nessun contratto in coda.</p>
        <p className="text-[10px]">Acquista i diritti dal Marketplace per averli qui.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2" data-testid="la-queue-tab">
      {/* Mode selector */}
      <div className="grid grid-cols-2 gap-2">
        <button onClick={() => setMode('classic')}
          className={`px-3 py-1.5 rounded-lg border text-[10px] font-bold ${mode === 'classic' ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-200' : 'bg-gray-900 border-gray-700 text-gray-400'}`}
          data-testid="queue-mode-classic">
          Pipeline V3
        </button>
        <button onClick={() => setMode('lampo')}
          className={`px-3 py-1.5 rounded-lg border text-[10px] font-bold flex items-center justify-center gap-1 ${mode === 'lampo' ? 'bg-amber-500/20 border-amber-500/50 text-amber-200' : 'bg-gray-900 border-gray-700 text-gray-400'}`}
          data-testid="queue-mode-lampo">
          <Zap className="w-3 h-3" />LAMPO
        </button>
      </div>

      {items.map(c => {
        const dleft = daysLeft(c.expires_at);
        const expiringSoon = dleft <= 7;
        return (
          <div key={c.id} className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3 space-y-2" data-testid={`la-contract-${c.id}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-amber-200 truncate">{c.origin_title}</p>
                <p className="text-[9px] text-gray-500">{c.origin_kind === 'anime' ? 'Anime' : 'Animazione'} · {c.exclusive ? 'Esclusivo' : 'Non esclusivo'}</p>
              </div>
              <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold flex items-center gap-1 ${expiringSoon ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'}`}>
                {expiringSoon && <AlertTriangle className="w-2.5 h-2.5" />}
                <Clock className="w-2.5 h-2.5" />{dleft}gg
              </span>
            </div>
            <div className="grid grid-cols-3 gap-1.5 text-[9px]">
              <div className="bg-black/40 rounded p-1.5"><p className="text-gray-500">Pagato</p><p className="text-cyan-300 font-mono">{fmtMoney(c.price_paid)}</p></div>
              <div className="bg-black/40 rounded p-1.5"><p className="text-gray-500">Acq/Vend</p><p className="text-cyan-300 font-mono">{Math.round(c.buyer_share_pct * 100)}/{Math.round(c.seller_share_pct * 100)}%</p></div>
              <div className="bg-black/40 rounded p-1.5"><p className="text-gray-500">Royalty</p><p className="text-cyan-300 font-mono">{(c.royalty_pct * 100).toFixed(1)}%</p></div>
            </div>
            <button onClick={() => startProduction(c)} disabled={busy === c.id}
              className="w-full px-3 py-2 rounded-lg bg-pink-500/30 border border-pink-500/60 text-pink-100 text-xs font-bold disabled:opacity-50 flex items-center justify-center gap-2"
              data-testid={`start-prod-${c.id}`}>
              {busy === c.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              {busy === c.id ? 'Avvio...' : `Avvia produzione (${mode === 'lampo' ? 'LAMPO' : 'V3'})`}
            </button>
          </div>
        );
      })}
    </div>
  );
}
