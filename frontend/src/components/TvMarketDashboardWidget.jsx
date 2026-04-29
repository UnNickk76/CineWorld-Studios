/**
 * TvMarketDashboardWidget — Cruscotto Produttore TV.
 *
 * Mostra aggregati e quick-actions per il sistema mercato diritti:
 *   • Offerte ricevute pendenti (badge alert)
 *   • Offerte fatte (status)
 *   • Contratti attivi (con countdown)
 *   • Storico contratti completati
 *
 * Embeddable nella Dashboard. Mobile-first, espandibile in modale full-screen.
 */
import React, { useEffect, useState, useContext, useMemo } from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { AuthContext } from '../contexts';
import { Tv, X, Inbox, Send, FileText, Clock, AlertCircle, Check, ArrowRight, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const fmtMoney = (n) => `$${Number(n || 0).toLocaleString('it-IT')}`;

function daysUntil(iso) {
  if (!iso) return null;
  try {
    const ms = new Date(iso).getTime() - Date.now();
    const d = Math.ceil(ms / (24 * 3600 * 1000));
    return d;
  } catch { return null; }
}

export default function TvMarketDashboardWidget() {
  const { api } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [incoming, setIncoming] = useState([]);
  const [outgoing, setOutgoing] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState('incoming');
  const [acting, setActing] = useState(null); // {offerId, action}

  // Auto-open dal deep-link delle notifiche: ?widget=tv-market&tab=incoming|outgoing|active|history
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      if (params.get('widget') === 'tv-market') {
        const t = params.get('tab');
        if (['incoming', 'outgoing', 'active', 'history'].includes(t)) setTab(t);
        setOpen(true);
        // Pulisce l'URL per evitare riaperture in loop dopo refresh
        const url = new URL(window.location.href);
        url.searchParams.delete('widget'); url.searchParams.delete('tab');
        window.history.replaceState({}, '', url.toString());
      }
    } catch { /* no-op */ }
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [a, b, c] = await Promise.all([
        api.get('/tv-market/incoming-offers').then(r => r.data?.offers || []).catch(() => []),
        api.get('/tv-market/my-offers').then(r => r.data?.offers || []).catch(() => []),
        api.get('/tv-market/contracts/mine').then(r => r.data?.contracts || []).catch(() => []),
      ]);
      setIncoming(a);
      setOutgoing(b);
      setContracts(c);
    } finally { setLoading(false); }
  };

  useEffect(() => { loadAll(); /* eslint-disable-next-line */ }, []);

  // Counters
  const pendingIncoming = useMemo(() => incoming.filter(o => o.status === 'pending').length, [incoming]);
  const counteredAwaitingMe = useMemo(() => outgoing.filter(o => o.status === 'countered_by_owner_pending_buyer').length, [outgoing]);
  const activeContracts = useMemo(() => contracts.filter(c => c.status === 'active' || c.status === 'pending_cinema'), [contracts]);
  const completedContracts = useMemo(() => contracts.filter(c => c.status === 'completed'), [contracts]);

  const totalAlerts = pendingIncoming + counteredAwaitingMe;

  const decideOffer = async (offerId, action) => {
    setActing({ offerId, action });
    try {
      await api.post(`/tv-market/offers/${offerId}/${action}`);
      toast.success(action === 'accept' ? 'Offerta accettata!' : 'Offerta rifiutata');
      await loadAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally { setActing(null); }
  };

  // ── Header card (compact, sempre visibile) ─────────────
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        data-testid="tv-market-dashboard-widget"
        className="w-full p-3 rounded-xl bg-gradient-to-br from-amber-900/30 via-orange-900/20 to-black border border-amber-500/25 hover:border-amber-400/50 active:scale-[0.99] transition-all touch-manipulation text-left relative overflow-hidden"
      >
        {/* Glow background */}
        <div className="absolute -top-12 -right-12 w-32 h-32 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative">
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center flex-shrink-0">
                <Tv size={14} className="text-amber-300" />
              </div>
              <div className="min-w-0">
                <h3 className="text-[12px] font-black uppercase tracking-wider text-white font-['Bebas_Neue']">
                  Cruscotto TV Market
                </h3>
                <p className="text-[9px] text-white/50 truncate">Vendita & affitto diritti TV</p>
              </div>
            </div>
            {totalAlerts > 0 && (
              <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500 text-white text-[9px] font-bold animate-pulse" data-testid="tv-market-alerts-badge">
                <AlertCircle size={10} /> {totalAlerts}
              </div>
            )}
          </div>

          <div className="grid grid-cols-4 gap-1.5">
            <Stat icon={Inbox} count={pendingIncoming} label="Offerte ricevute" alert={pendingIncoming > 0} color="rose" />
            <Stat icon={Send} count={outgoing.length} label="Offerte fatte" color="cyan" />
            <Stat icon={Clock} count={activeContracts.length} label="Contratti attivi" color="amber" />
            <Stat icon={FileText} count={completedContracts.length} label="Storico" color="slate" />
          </div>
        </div>
      </button>

      {/* Modal full panel */}
      <Dialog open={open} onOpenChange={(v) => !v && setOpen(false)}>
        <DialogContent className="max-w-md p-0 bg-[#0b0b0d] border border-amber-500/20 max-h-[92vh] overflow-hidden flex flex-col" data-testid="tv-market-dashboard-modal">
          <div className="px-4 pt-3 pb-3 border-b border-white/10 flex-shrink-0 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Tv size={16} className="text-amber-300" />
              <h2 className="text-sm font-bold text-white font-['Bebas_Neue'] tracking-wide text-base">Cruscotto TV Market</h2>
            </div>
            <button onClick={() => setOpen(false)} className="text-white/40 hover:text-white p-1" aria-label="Chiudi" data-testid="tv-market-dashboard-close">
              <X size={16} />
            </button>
          </div>

          <div className="flex border-b border-white/5 flex-shrink-0 overflow-x-auto">
            <TabBtn active={tab === 'incoming'} onClick={() => setTab('incoming')} icon={Inbox} label="Ricevute" badge={pendingIncoming} testid="tv-market-tab-incoming" />
            <TabBtn active={tab === 'outgoing'} onClick={() => setTab('outgoing')} icon={Send} label="Inviate" badge={counteredAwaitingMe} testid="tv-market-tab-outgoing" />
            <TabBtn active={tab === 'active'} onClick={() => setTab('active')} icon={Clock} label="Attivi" testid="tv-market-tab-active" />
            <TabBtn active={tab === 'history'} onClick={() => setTab('history')} icon={FileText} label="Storico" testid="tv-market-tab-history" />
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-3" data-testid="tv-market-dashboard-body">
            {loading && (
              <div className="flex items-center justify-center py-4 text-white/50 text-[11px]"><Loader2 size={14} className="animate-spin mr-1.5"/> Caricamento…</div>
            )}

            {!loading && tab === 'incoming' && (
              incoming.length === 0
                ? <Empty msg="Nessuna offerta ricevuta. Pubblica i tuoi contenuti sul mercato per ricevere proposte!" />
                : <div className="space-y-2">
                    {incoming.map(o => (
                      <IncomingOfferRow key={o.id} offer={o} onAccept={() => decideOffer(o.id, 'accept')} onReject={() => decideOffer(o.id, 'reject')} acting={acting} />
                    ))}
                  </div>
            )}

            {!loading && tab === 'outgoing' && (
              outgoing.length === 0
                ? <Empty msg="Non hai ancora fatto offerte. Esplora il mercato per trovare contenuti da trasmettere!" />
                : <div className="space-y-2">
                    {outgoing.map(o => <OutgoingOfferRow key={o.id} offer={o} onAccept={() => decideOffer(o.id, 'accept')} acting={acting} />)}
                  </div>
            )}

            {!loading && tab === 'active' && (
              activeContracts.length === 0
                ? <Empty msg="Nessun contratto attivo. Acquista o vendi diritti TV per aprire contratti!" />
                : <div className="space-y-2">
                    {activeContracts.map(c => <ContractRow key={c.id} contract={c} />)}
                  </div>
            )}

            {!loading && tab === 'history' && (
              completedContracts.length === 0
                ? <Empty msg="Storico vuoto. I contratti completati appariranno qui." />
                : <div className="space-y-2">
                    {completedContracts.map(c => <ContractRow key={c.id} contract={c} historic />)}
                  </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ───── Sub-components ─────────────────────────────────────
const Stat = ({ icon: Icon, count, label, alert, color }) => {
  const colors = {
    rose:  alert ? 'bg-rose-500/15 border-rose-500/40 text-rose-200' : 'bg-white/5 border-white/10 text-white/60',
    cyan:  'bg-cyan-500/10 border-cyan-500/25 text-cyan-200',
    amber: 'bg-amber-500/10 border-amber-500/25 text-amber-200',
    slate: 'bg-slate-500/10 border-slate-500/25 text-slate-200',
  };
  return (
    <div className={`p-1.5 rounded-lg border ${colors[color] || colors.slate} flex flex-col items-center text-center`}>
      <Icon size={11} className="mb-0.5" />
      <div className="text-sm font-black leading-none">{count}</div>
      <div className="text-[8px] font-bold uppercase tracking-wide leading-tight mt-0.5 opacity-80">{label}</div>
    </div>
  );
};

const TabBtn = ({ active, onClick, icon: Icon, label, badge, testid }) => (
  <button onClick={onClick} data-testid={testid}
    className={`flex-1 py-2 text-[10px] font-bold flex items-center justify-center gap-1 touch-manipulation transition-colors min-w-[70px] relative ${
      active ? 'text-amber-300 border-b-2 border-amber-400' : 'text-white/50 hover:text-white/80'
    }`}>
    <Icon size={11} /> {label}
    {badge > 0 && (
      <span className="ml-0.5 inline-flex items-center justify-center min-w-[14px] h-3.5 px-1 rounded-full bg-rose-500 text-white text-[8px] font-black">{badge}</span>
    )}
  </button>
);

const Empty = ({ msg }) => (
  <div className="text-center py-8">
    <Tv size={28} className="inline text-white/20 mb-2" />
    <p className="text-[11px] text-white/50 italic max-w-[260px] mx-auto leading-snug">{msg}</p>
  </div>
);

const StatusPill = ({ status }) => {
  const map = {
    pending:                              { label: 'PENDING',         cls: 'bg-amber-400 text-black' },
    accepted:                             { label: 'ACCETTATA',       cls: 'bg-emerald-500 text-black' },
    rejected:                             { label: 'RIFIUTATA',       cls: 'bg-rose-500/20 text-rose-200 border border-rose-500/40' },
    rejected_listing_sold:                { label: 'CHIUSA',          cls: 'bg-white/10 text-white/60' },
    rejected_conflict:                    { label: 'CONFLITTO',       cls: 'bg-rose-500/20 text-rose-200 border border-rose-500/40' },
    expired:                              { label: 'SCADUTA',         cls: 'bg-white/10 text-white/50' },
    countered_by_owner_pending_buyer:     { label: 'CONTROPROPOSTA',  cls: 'bg-cyan-500 text-black' },
  };
  const cfg = map[status] || { label: (status || '?').toUpperCase(), cls: 'bg-white/10 text-white/60' };
  return <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-wider ${cfg.cls}`}>{cfg.label}</span>;
};

const IncomingOfferRow = ({ offer, onAccept, onReject, acting }) => {
  const isActing = acting?.offerId === offer.id;
  const isPending = offer.status === 'pending';
  return (
    <div className={`p-2 rounded-lg border ${isPending ? 'bg-amber-500/5 border-amber-500/30' : 'bg-white/[0.02] border-white/5'}`} data-testid={`tv-market-incoming-${offer.id}`}>
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-bold text-white truncate">{offer.content_title || offer.buyer_house || offer.buyer_nickname || 'Buyer'}</div>
          <div className="text-[9px] text-white/50 truncate">📺 {offer.buyer_house || offer.buyer_nickname || 'Buyer'} · {offer.station_name} · {new Date(offer.created_at).toLocaleDateString('it-IT')}</div>
        </div>
        <StatusPill status={offer.status} />
      </div>
      <div className="grid grid-cols-3 gap-1 mt-1.5 text-[10px]">
        <Tiny label="Offerta" value={fmtMoney(offer.offered_money)} />
        <Tiny label="Modo" value={offer.mode_proposed === 'full' ? '100%' : '50%'} />
        <Tiny label="Durata" value={`${offer.duration_days_proposed}gg`} />
      </div>
      {offer.message && <p className="text-[9px] text-white/60 italic mt-1 truncate">"{offer.message}"</p>}
      {isPending && (
        <div className="flex gap-1 mt-2">
          <button onClick={onAccept} disabled={isActing} className="flex-1 py-1 rounded bg-emerald-500 hover:bg-emerald-400 text-black text-[10px] font-bold touch-manipulation disabled:opacity-50" data-testid={`tv-market-incoming-accept-${offer.id}`}>
            {isActing && acting?.action === 'accept' ? '…' : <><Check size={10} className="inline" /> Accetta</>}
          </button>
          <button onClick={onReject} disabled={isActing} className="flex-1 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-200 text-[10px] font-bold touch-manipulation disabled:opacity-50" data-testid={`tv-market-incoming-reject-${offer.id}`}>
            {isActing && acting?.action === 'reject' ? '…' : <><X size={10} className="inline" /> Rifiuta</>}
          </button>
        </div>
      )}
    </div>
  );
};

const OutgoingOfferRow = ({ offer, onAccept, acting }) => {
  const isActing = acting?.offerId === offer.id;
  const isCountered = offer.status === 'countered_by_owner_pending_buyer';
  return (
    <div className={`p-2 rounded-lg border ${isCountered ? 'bg-cyan-500/5 border-cyan-500/30' : 'bg-white/[0.02] border-white/5'}`} data-testid={`tv-market-outgoing-${offer.id}`}>
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-bold text-white truncate">{offer.content_title || `📦 Listing #${offer.listing_id?.slice(0, 8)}`}</div>
          <div className="text-[9px] text-white/50 truncate">{new Date(offer.created_at).toLocaleDateString('it-IT')}</div>
        </div>
        <StatusPill status={offer.status} />
      </div>
      <div className="grid grid-cols-3 gap-1 mt-1.5 text-[10px]">
        <Tiny label="Offerta" value={fmtMoney(isCountered ? offer.counter_money : offer.offered_money)} />
        <Tiny label="Modo" value={offer.mode_proposed === 'full' ? '100%' : '50%'} />
        <Tiny label="Durata" value={`${isCountered ? offer.counter_duration_days : offer.duration_days_proposed}gg`} />
      </div>
      {isCountered && (
        <div className="mt-2 p-1.5 rounded bg-cyan-500/10 border border-cyan-500/30">
          <p className="text-[9px] text-cyan-200 mb-1">L'owner ha proposto: <strong>{fmtMoney(offer.counter_money)}</strong> · {offer.counter_duration_days}gg</p>
          {offer.counter_message && <p className="text-[8px] text-cyan-100/70 italic">"{offer.counter_message}"</p>}
          <button onClick={onAccept} disabled={isActing} className="w-full mt-1 py-1 rounded bg-cyan-500 hover:bg-cyan-400 text-black text-[10px] font-bold touch-manipulation disabled:opacity-50" data-testid={`tv-market-outgoing-accept-counter-${offer.id}`}>
            {isActing ? '…' : <><Check size={10} className="inline" /> Accetta controproposta</>}
          </button>
        </div>
      )}
    </div>
  );
};

const ContractRow = ({ contract, historic }) => {
  const days = daysUntil(contract.end_at);
  const dangerSoon = !historic && days !== null && days <= 3;
  const isPending = contract.status === 'pending_cinema';
  const startDays = isPending ? daysUntil(contract.start_at) : null;
  return (
    <div className={`p-2 rounded-lg border ${historic ? 'bg-white/[0.02] border-white/5 opacity-80' : (isPending ? 'bg-violet-500/5 border-violet-500/30' : (dangerSoon ? 'bg-rose-500/5 border-rose-500/30' : (contract.mode === 'full' ? 'bg-amber-500/5 border-amber-500/30' : 'bg-cyan-500/5 border-cyan-500/30')))}`} data-testid={`tv-market-contract-${contract.id}`}>
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-bold text-white truncate">{contract.content_title || `Contratto #${contract.id?.slice(0, 8)}`}</div>
          <div className="text-[9px] text-white/50 truncate flex items-center gap-1">
            <span>{contract.content_type === 'film' || contract.content_collection === 'films' ? 'Film' : (contract.content_type === 'anime' ? 'Anime' : 'Serie TV')}</span>
            {isPending && <span className="text-violet-300 font-bold">· In attesa fine cinema</span>}
          </div>
        </div>
        <span className={`text-[8px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded ${contract.mode === 'full' ? 'bg-amber-500 text-black' : 'bg-cyan-500 text-black'}`}>
          {contract.mode === 'full' ? '100%' : '50%'}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-1 mt-1.5 text-[10px]">
        <Tiny label="Pagato" value={fmtMoney(contract.money_paid)} />
        <Tiny label="Durata" value={`${contract.duration_days}gg`} />
        <Tiny
          label={isPending ? 'Parte tra' : (historic ? 'Concluso' : (dangerSoon ? 'Scade tra' : 'Resta'))}
          value={isPending ? (startDays !== null ? `${startDays}gg` : '—') : (historic ? new Date(contract.end_at).toLocaleDateString('it-IT') : (days !== null ? `${days}gg` : '—'))}
          alert={dangerSoon} />
      </div>
    </div>
  );
};

const Tiny = ({ label, value, alert }) => (
  <div>
    <div className="text-[7px] uppercase text-white/40 font-bold">{label}</div>
    <div className={`text-[10px] font-bold ${alert ? 'text-rose-300' : 'text-white'}`}>{value}</div>
  </div>
);
