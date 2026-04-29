/**
 * NegotiateModal — modale di negoziazione diritti LA.
 * - Slider buyer/seller share 50%-80%
 * - Switch esclusivo / non esclusivo
 * - Slider royalty 2-5%
 * - Slider prezzo entro range dinamico
 * - Auto-quote dal backend ad ogni cambio parametro
 */
import React, { useEffect, useState, useCallback } from 'react';
import { X, Loader2, Send, AlertTriangle } from 'lucide-react';

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
  if (!r.ok) {
    const e = new Error(typeof d.detail === 'string' ? d.detail : `HTTP ${r.status}`);
    e.status = r.status; throw e;
  }
  return d;
}

export default function NegotiateModal({ origin, onClose, onSent, mode = 'offer', existingOffer = null }) {
  // mode: 'offer' (buyer) | 'counter' (seller)
  const [buyerPct, setBuyerPct] = useState(existingOffer?.buyer_share_pct ?? 0.70);
  const [exclusive, setExclusive] = useState(existingOffer?.exclusive ?? true);
  const [royalty, setRoyalty] = useState(existingOffer?.royalty_pct ?? 0.03);
  const [price, setPrice] = useState(existingOffer?.offered_price ?? null);
  const [quote, setQuote] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [note, setNote] = useState('');

  const fetchQuote = useCallback(async () => {
    if (!origin) return;
    try {
      const params = new URLSearchParams({
        origin_id: origin.id,
        origin_kind: origin.kind,
        buyer_share_pct: buyerPct,
        exclusive,
        royalty_pct: royalty,
      });
      const d = await api(`/api/live-action-market/quote?${params}`);
      setQuote(d);
      // Adatta prezzo se fuori range
      if (price === null || price < d.min_offer || price > d.max_offer) {
        setPrice(d.suggested_offer);
      }
    } catch (e) {
      setError(e.message);
    }
  }, [origin, buyerPct, exclusive, royalty]); // eslint-disable-line

  useEffect(() => { fetchQuote(); }, [fetchQuote]);

  const submit = async () => {
    if (!quote || !price) return;
    setBusy(true); setError(null);
    try {
      if (mode === 'counter' && existingOffer) {
        await api(`/api/live-action-market/offers/${existingOffer.id}/counter`, 'POST', {
          offered_price: price, buyer_share_pct: buyerPct, exclusive, royalty_pct: royalty, note,
        });
      } else {
        await api('/api/live-action-market/offers', 'POST', {
          origin_id: origin.id, origin_kind: origin.kind,
          offered_price: price, buyer_share_pct: buyerPct, exclusive, royalty_pct: royalty,
        });
      }
      onSent && onSent();
    } catch (e) {
      setError(e.message);
    }
    setBusy(false);
  };

  const fmtMoney = (v) => `$${Number(v || 0).toLocaleString()}`;
  const isCounter = mode === 'counter';

  return (
    <div className="fixed inset-0 z-[60] bg-black/85 backdrop-blur-sm flex items-end sm:items-center justify-center p-3" onClick={() => !busy && onClose()}>
      <div className="w-full max-w-md max-h-[92vh] rounded-2xl border border-cyan-500/40 bg-gradient-to-br from-cyan-950/70 to-gray-900/95 flex flex-col overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="px-4 py-3 flex items-center justify-between border-b border-cyan-500/20 shrink-0">
          <h3 className="text-sm font-bold text-cyan-200">
            {isCounter ? 'Controproposta' : 'Offerta diritti'}
          </h3>
          <button onClick={onClose} disabled={busy} className="text-gray-400" data-testid="negotiate-close">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
          <div className="rounded-lg bg-black/30 p-2 border border-gray-800">
            <p className="text-[10px] text-gray-400 uppercase font-bold">Opera</p>
            <p className="text-sm text-white truncate">{origin.title}</p>
            <p className="text-[10px] text-gray-500">
              {origin.kind === 'anime' ? 'Anime' : 'Animazione'} · CWSv {origin.cwsv?.toFixed(1)} · {origin.spectators?.toLocaleString() || 0} spettatori
            </p>
          </div>

          {/* Esclusività */}
          <div>
            <p className="text-[10px] text-gray-400 uppercase font-bold mb-1">Esclusività</p>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => setExclusive(true)}
                className={`px-3 py-2 rounded-lg border text-[11px] font-bold ${exclusive ? 'bg-cyan-500/20 border-cyan-500/60 text-cyan-200' : 'bg-gray-900 border-gray-700 text-gray-400'}`}
                data-testid="excl-on">
                Esclusivo
              </button>
              <button onClick={() => setExclusive(false)}
                className={`px-3 py-2 rounded-lg border text-[11px] font-bold ${!exclusive ? 'bg-cyan-500/20 border-cyan-500/60 text-cyan-200' : 'bg-gray-900 border-gray-700 text-gray-400'}`}
                data-testid="excl-off">
                Non esclusivo (-40%)
              </button>
            </div>
          </div>

          {/* Spartizione ricavi */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] text-gray-400 uppercase font-bold">Ricavi cinema</span>
              <span className="text-[10px] text-cyan-300 font-mono">
                Acq {Math.round(buyerPct * 100)}% / Vend {100 - Math.round(buyerPct * 100)}%
              </span>
            </div>
            <input type="range" min="0.50" max="0.80" step="0.05" value={buyerPct}
              onChange={(e) => setBuyerPct(parseFloat(e.target.value))}
              disabled={busy}
              className="w-full" data-testid="buyer-pct-slider" />
            <p className="text-[9px] text-gray-500 mt-0.5">Più al venditore = prezzo più basso</p>
          </div>

          {/* Royalty */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] text-gray-400 uppercase font-bold">Royalty al venditore</span>
              <span className="text-[10px] text-cyan-300 font-mono">{(royalty * 100).toFixed(1)}%</span>
            </div>
            <input type="range" min="0.02" max="0.05" step="0.005" value={royalty}
              onChange={(e) => setRoyalty(parseFloat(e.target.value))}
              disabled={busy}
              className="w-full" data-testid="royalty-slider" />
            <p className="text-[9px] text-gray-500 mt-0.5">% post-uscita su TV/merchandise</p>
          </div>

          {/* Prezzo */}
          {quote && (
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-[10px] text-gray-400 uppercase font-bold">Offerta</span>
                <span className="text-sm text-cyan-200 font-bold font-mono">{fmtMoney(price)}</span>
              </div>
              <input type="range" min={quote.min_offer} max={quote.max_offer} step="10000"
                value={price || quote.suggested_offer}
                onChange={(e) => setPrice(parseInt(e.target.value))}
                disabled={busy}
                className="w-full" data-testid="price-slider" />
              <div className="flex justify-between text-[9px] text-gray-500">
                <span>min {fmtMoney(quote.min_offer)}</span>
                <span>suggerito {fmtMoney(quote.suggested_offer)}</span>
                <span>max {fmtMoney(quote.max_offer)}</span>
              </div>
            </div>
          )}

          {isCounter && (
            <div>
              <p className="text-[10px] text-gray-400 uppercase font-bold mb-1">Nota (opzionale)</p>
              <textarea value={note} onChange={(e) => setNote(e.target.value)}
                disabled={busy} maxLength={300}
                placeholder="Es: voglio almeno 60% dei ricavi"
                rows={2}
                className="w-full text-[11px] px-2 py-1 rounded bg-black/40 border border-gray-700 text-white resize-none"
                data-testid="counter-note"
              />
            </div>
          )}

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 p-2 flex items-start gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" />
              <p className="text-[10px] text-red-200">{error}</p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2 p-3 border-t border-cyan-500/20 shrink-0">
          <button onClick={onClose} disabled={busy}
            className="px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-gray-200 text-xs font-bold disabled:opacity-50"
            data-testid="negotiate-cancel">
            Annulla
          </button>
          <button onClick={submit} disabled={busy || !price}
            className="px-3 py-2 rounded-lg bg-cyan-500/30 border border-cyan-500/60 text-cyan-100 text-xs font-bold disabled:opacity-50 flex items-center justify-center gap-1"
            data-testid="negotiate-submit">
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            {isCounter ? 'Controproponi' : 'Invia offerta'}
          </button>
        </div>
      </div>
    </div>
  );
}
