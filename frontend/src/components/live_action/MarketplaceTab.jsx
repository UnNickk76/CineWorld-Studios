/**
 * MarketplaceTab — Marketplace LA: opere di altri player + offerte ricevute/inviate.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Loader2, Star, Film, User, MessageCircle, Send, Inbox } from 'lucide-react';
import NegotiateModal from './NegotiateModal';

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

export default function MarketplaceTab({ onToast }) {
  const [view, setView] = useState('browse'); // browse | inbox | sent
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [negotiate, setNegotiate] = useState(null); // { origin } or { existingOffer }
  const [counter, setCounter] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      let endpoint = '/api/live-action-market/marketplace';
      if (view === 'inbox') endpoint = '/api/live-action-market/offers/inbox';
      if (view === 'sent') endpoint = '/api/live-action-market/offers/sent';
      const d = await api(endpoint);
      setItems(d.items || []);
    } catch (e) { onToast && onToast(e.message, 'error'); }
    setLoading(false);
  }, [view]); // eslint-disable-line

  useEffect(() => { load(); }, [load]);

  const handleAccept = async (offer) => {
    try {
      await api(`/api/live-action-market/offers/${offer.id}/accept`, 'POST');
      onToast && onToast('Offerta accettata! Diritti venduti.');
      load();
    } catch (e) { onToast && onToast(e.message, 'error'); }
  };

  const handleReject = async (offer) => {
    if (!confirm('Rifiutare l\'offerta?')) return;
    try {
      await api(`/api/live-action-market/offers/${offer.id}/reject`, 'POST');
      onToast && onToast('Offerta rifiutata');
      load();
    } catch (e) { onToast && onToast(e.message, 'error'); }
  };

  return (
    <div className="space-y-3" data-testid="la-marketplace-tab">
      {/* Sub-tab */}
      <div className="flex gap-1">
        {[
          { id: 'browse', label: 'Esplora', icon: Film },
          { id: 'inbox', label: 'Ricevute', icon: Inbox },
          { id: 'sent', label: 'Inviate', icon: Send },
        ].map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => setView(t.id)}
              className={`flex-1 px-2 py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 ${view === t.id ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-500/40' : 'bg-gray-900 text-gray-400 border border-gray-800'}`}
              data-testid={`la-market-sub-${t.id}`}>
              <Icon className="w-3 h-3" />{t.label}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-500"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-xs">
          {view === 'browse' && 'Nessuna opera disponibile sul marketplace al momento.'}
          {view === 'inbox' && 'Nessuna offerta ricevuta. Listate i vostri anime per ricevere proposte!'}
          {view === 'sent' && 'Non hai ancora inviato offerte.'}
        </div>
      ) : view === 'browse' ? (
        <div className="grid grid-cols-2 gap-2">
          {items.map(o => (
            <button key={o.id}
              onClick={() => setNegotiate({ origin: o })}
              className="text-left rounded-xl border border-gray-800 hover:border-cyan-500/50 bg-gray-900/40 p-2 active:scale-95 transition-all"
              data-testid={`la-origin-${o.id}`}>
              <div className="aspect-[2/3] rounded-lg bg-gray-800 overflow-hidden mb-2 relative">
                {o.poster_url ? <img src={o.poster_url} alt="" className="w-full h-full object-cover" />
                  : <div className="w-full h-full flex items-center justify-center"><Film className="w-8 h-8 text-gray-700" /></div>}
                <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded-full bg-black/80 text-[8px] font-bold uppercase">
                  {o.kind === 'anime' ? <span className="text-purple-300">Anime</span> : <span className="text-amber-300">Animaz.</span>}
                </div>
                {o.active_listing && (
                  <div className="absolute bottom-1 right-1 px-1.5 py-0.5 rounded bg-emerald-500/90 text-[8px] font-bold text-black">IN VENDITA</div>
                )}
              </div>
              <p className="text-[10px] font-bold text-white truncate">{o.title}</p>
              <p className="text-[9px] text-gray-500 truncate flex items-center gap-1">
                <User className="w-2.5 h-2.5" />{o.owner_nickname || 'Sconosciuto'}
              </p>
              <div className="flex items-center gap-2 mt-1 text-[8px] text-gray-400">
                <span className="flex items-center gap-0.5"><Star className="w-2.5 h-2.5 text-yellow-400" />{o.cwsv?.toFixed(1)}</span>
                <span>·</span>
                <span>{o.days_since_release}gg</span>
              </div>
              <p className="text-[9px] text-cyan-400 font-mono mt-1">~{fmtMoney(o.base_price)}</p>
            </button>
          ))}
        </div>
      ) : (
        // INBOX / SENT
        <ul className="space-y-2">
          {items.map(o => (
            <li key={o.id} className="rounded-xl border border-gray-800 bg-gray-900/40 p-3" data-testid={`la-offer-${o.id}`}>
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-bold text-white truncate">{o.origin_title}</p>
                  <p className="text-[9px] text-gray-500">
                    {view === 'inbox' ? `da ${o.buyer_nickname || 'sconosciuto'}` : `a ${o.owner_id?.slice(0, 8) || ''}`}
                    · {o.exclusive ? 'Esclusivo' : 'Non esclusivo'}
                  </p>
                </div>
                <span className={`text-[8px] px-1.5 py-0.5 rounded-full font-bold uppercase ${
                  o.status === 'pending' ? 'bg-amber-500/20 text-amber-300'
                  : o.status === 'countered' ? 'bg-blue-500/20 text-blue-300'
                  : o.status === 'accepted' ? 'bg-emerald-500/20 text-emerald-300'
                  : 'bg-red-500/20 text-red-300'
                }`}>
                  {o.status === 'pending' ? 'In attesa' : o.status === 'countered' ? 'Controproposta' : o.status === 'accepted' ? 'Accettata' : 'Rifiutata'}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[9px] mb-2">
                <div className="bg-black/40 rounded p-1.5">
                  <p className="text-gray-500">Prezzo</p>
                  <p className="text-cyan-300 font-mono font-bold">{fmtMoney(o.offered_price)}</p>
                </div>
                <div className="bg-black/40 rounded p-1.5">
                  <p className="text-gray-500">Acq/Vend</p>
                  <p className="text-cyan-300 font-mono">{Math.round(o.buyer_share_pct * 100)}%/{Math.round(o.seller_share_pct * 100)}%</p>
                </div>
                <div className="bg-black/40 rounded p-1.5">
                  <p className="text-gray-500">Royalty</p>
                  <p className="text-cyan-300 font-mono">{(o.royalty_pct * 100).toFixed(1)}%</p>
                </div>
              </div>
              {view === 'inbox' && (o.status === 'pending' || o.status === 'countered') && (
                <div className="grid grid-cols-3 gap-1.5">
                  <button onClick={() => handleAccept(o)}
                    className="px-2 py-1.5 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-[10px] font-bold"
                    data-testid={`accept-${o.id}`}>
                    Accetta
                  </button>
                  <button onClick={() => setCounter({ existingOffer: o, origin: { id: o.origin_id, kind: o.origin_kind, title: o.origin_title, cwsv: 5, spectators: 0 } })}
                    className="px-2 py-1.5 rounded bg-blue-500/20 border border-blue-500/40 text-blue-300 text-[10px] font-bold flex items-center justify-center gap-1"
                    data-testid={`counter-${o.id}`}>
                    <MessageCircle className="w-3 h-3" />Contropr.
                  </button>
                  <button onClick={() => handleReject(o)}
                    className="px-2 py-1.5 rounded bg-red-500/15 border border-red-500/30 text-red-300 text-[10px] font-bold"
                    data-testid={`reject-${o.id}`}>
                    Rifiuta
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {negotiate && (
        <NegotiateModal origin={negotiate.origin} mode="offer"
          onClose={() => setNegotiate(null)}
          onSent={() => { setNegotiate(null); onToast && onToast('Offerta inviata!'); load(); }}
        />
      )}
      {counter && (
        <NegotiateModal origin={counter.origin} existingOffer={counter.existingOffer} mode="counter"
          onClose={() => setCounter(null)}
          onSent={() => { setCounter(null); onToast && onToast('Controproposta inviata!'); load(); }}
        />
      )}
    </div>
  );
}
