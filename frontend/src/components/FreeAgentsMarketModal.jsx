import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { X, Star, Users, DollarSign, Clock, Send } from 'lucide-react';
import { toast } from 'sonner';

/**
 * Free Agents Market — attori liberati dai propri ex-roster.
 * Player con Agenzia + Scuola hanno sconti più alti (-45%).
 * Ingaggio con sistema rifiuti (1-3 rinegoziazioni possibili).
 */
export default function FreeAgentsMarketModal({ open, onClose, onSigned }) {
  const { api } = useContext(AuthContext);
  const [items, setItems] = useState([]);
  const [perks, setPerks] = useState(null);
  const [discountPct, setDiscountPct] = useState(0);
  const [loading, setLoading] = useState(false);
  const [signFor, setSignFor] = useState(null); // actor object
  const [duration, setDuration] = useState(30);
  const [offer, setOffer] = useState(0);
  const [renegotiations, setRenegotiations] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get('/market/free-agents');
      setItems(res.data?.items || []);
      setPerks(res.data?.perks || null);
      setDiscountPct(res.data?.discount_pct || 0);
    } catch (e) {
      toast.error('Errore caricamento');
    }
    setLoading(false);
  };

  useEffect(() => { if (open) load(); /* eslint-disable-next-line */ }, [open]);

  const startSign = (actor) => {
    setSignFor(actor);
    setDuration(30);
    setOffer(actor.list_price_30d || 0);
    setRenegotiations(0);
  };

  const submit = async () => {
    if (!signFor) return;
    setSubmitting(true);
    try {
      const res = await api.post(`/market/free-agents/sign/${signFor.id}`, {
        duration_days: duration,
        offered_fee: offer,
      });
      if (res.data?.success) {
        toast.success(`Contratto firmato! ${signFor.name} ora è nel tuo roster.`);
        setSignFor(null);
        await load();
        if (onSigned) onSigned(res.data.actor);
      } else if (res.data?.rejected) {
        if (renegotiations >= 2) {
          toast.error(`Rifiutato definitivamente: "${res.data.message}"`);
          setSignFor(null);
        } else {
          toast.warning(`"${res.data.message}" Suggerito: $${res.data.suggested_fee?.toLocaleString()}`);
          setOffer(res.data.suggested_fee || offer);
          setRenegotiations(renegotiations + 1);
        }
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Errore');
    }
    setSubmitting(false);
  };

  const computeOfferFromDuration = (days) => {
    if (!signFor) return 0;
    const mult = days === 30 ? 1 : days === 90 ? 2.5 : 4.5;
    return Math.round(signFor.list_price_30d * mult);
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose && onClose()}>
      <DialogContent className="max-w-md p-0 bg-[#0D0D0F] border border-amber-500/30">
        <div className="px-4 py-3 border-b border-amber-500/20 flex items-center gap-2">
          <Users className="w-5 h-5 text-amber-400" />
          <h2 className="text-base font-bold text-amber-100" data-testid="free-agents-title">Mercato Attori Liberi</h2>
          <button onClick={onClose} className="ml-auto p-1 text-white/50 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {perks && (
          <div className="px-4 py-2 border-b border-amber-500/10 bg-amber-500/5 flex items-center gap-2 flex-wrap">
            <span className={`text-[9px] px-2 py-0.5 rounded font-bold ${perks.agency ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-800 text-gray-500'}`}>
              {perks.agency ? '✓ Agenzia' : '✗ Agenzia'}
            </span>
            <span className={`text-[9px] px-2 py-0.5 rounded font-bold ${perks.school ? 'bg-emerald-500/20 text-emerald-300' : 'bg-gray-800 text-gray-500'}`}>
              {perks.school ? '✓ Scuola' : '✗ Scuola'}
            </span>
            {discountPct > 0 && (
              <span className="text-[9px] px-2 py-0.5 rounded font-bold bg-amber-500/30 text-amber-200 ml-auto">
                Sconto -{discountPct}%
              </span>
            )}
          </div>
        )}

        <div className="px-4 py-3 max-h-[60vh] overflow-y-auto space-y-2">
          {loading && <p className="text-center text-[11px] text-gray-500 py-4">Caricamento...</p>}
          {!loading && items.length === 0 && (
            <div className="text-center py-6">
              <p className="text-[11px] text-gray-500">Nessun attore libero al momento.</p>
              <p className="text-[9px] text-gray-600 mt-1">Quando i player liberano i loro attori, compaiono qui.</p>
            </div>
          )}
          {items.map(actor => (
            <div key={actor.id} className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.03] border border-white/5"
                 data-testid={`free-agent-${actor.id}`}>
              <img src={actor.avatar_url} alt="" className="w-10 h-10 rounded-full bg-gray-800" />
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-bold text-white truncate">{actor.name}</p>
                <div className="flex items-center gap-1 text-[8px] text-gray-500">
                  {Array.from({ length: actor.stars || 1 }).map((_, i) => (
                    <Star key={i} className="w-2 h-2 text-yellow-400 fill-yellow-400" />
                  ))}
                  <span>· {actor.nationality}</span>
                </div>
                <p className="text-[8px] text-gray-600 mt-0.5">
                  Liberato da {actor.former_owner_nickname || 'Anonimo'}
                </p>
              </div>
              <div className="text-right">
                <p className="text-[10px] font-bold text-emerald-400">${(actor.list_price_30d || 0).toLocaleString()}</p>
                <p className="text-[7px] text-gray-500">30gg</p>
                <button
                  onClick={() => startSign(actor)}
                  data-testid={`free-agent-sign-${actor.id}`}
                  className="mt-1 text-[8px] px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 font-bold hover:bg-amber-500/30">
                  INGAGGIA
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Sign sheet */}
        {signFor && (
          <div className="border-t border-amber-500/30 px-4 py-3 bg-amber-500/5">
            <p className="text-[10px] text-amber-300 font-bold uppercase mb-2">Firma {signFor.name}</p>
            <div className="grid grid-cols-3 gap-1.5 mb-2">
              {[30, 90, 180].map(d => (
                <button key={d} onClick={() => { setDuration(d); setOffer(computeOfferFromDuration(d)); }}
                        className={`px-2 py-1.5 rounded text-[9px] font-bold border ${duration === d ? 'bg-amber-500/30 border-amber-400 text-amber-200' : 'bg-white/5 border-white/10 text-gray-400'}`}
                        data-testid={`free-agent-duration-${d}`}>
                  {d}gg
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-3 h-3 text-amber-400" />
              <input type="number" value={offer} onChange={e => setOffer(parseInt(e.target.value) || 0)}
                     className="flex-1 bg-black/40 border border-amber-500/20 rounded px-2 py-1 text-[11px] text-white"
                     data-testid="free-agent-offer-input" />
            </div>
            {renegotiations > 0 && (
              <p className="text-[9px] text-amber-400 mb-2">Tentativo {renegotiations + 1}/3</p>
            )}
            <div className="flex gap-2">
              <button onClick={() => setSignFor(null)}
                      className="flex-1 py-1.5 rounded bg-white/5 text-[10px] text-gray-400">
                Annulla
              </button>
              <button onClick={submit} disabled={submitting}
                      data-testid="free-agent-submit-offer"
                      className="flex-1 py-1.5 rounded bg-gradient-to-r from-amber-500 to-orange-500 text-black text-[10px] font-bold disabled:opacity-50">
                {submitting ? '...' : <><Send className="w-3 h-3 inline mr-1" />Offri</>}
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
