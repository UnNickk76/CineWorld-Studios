/**
 * TvMarketModal — Mercato Diritti TV
 *
 * Comportamento dinamico in base al ruolo:
 *  • Owner del contenuto: pubblica/aggiorna il listing, vede offerte ricevute
 *    e può accettare/rifiutare/contropore.
 *  • Altro player con TV: fa un'offerta sul listing pubblico.
 *  • Player senza TV: vede stato del mercato in sola lettura.
 *
 * Mobile-first, bottom-sheet style su mobile, dialog su desktop.
 */
import React, { useEffect, useMemo, useState, useContext } from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { AuthContext } from '../contexts';
import { Tv, X, Crown, Users, Lock, AlertTriangle, Check, Loader2, Send, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

const fmtMoney = (n) => `$${Number(n || 0).toLocaleString('it-IT')}`;
const fmtCP = (n) => `${Number(n || 0).toLocaleString('it-IT')} CP`;

const MODE_DESC = {
  full:  { title: 'Esclusiva 100%', desc: 'Tu prendi tutti i diritti TV. Il proprietario NON può trasmettere durante il contratto. Costo elevato ma audience garantita.', color: 'amber' },
  split: { title: 'Co-licenza 50%',  desc: 'Tu paghi al proprietario il 50% del prezzo. Entrambi potete trasmettere su tutte le vostre TV. Le visualizzazioni si dividono.', color: 'cyan' },
};

export default function TvMarketModal({ open, onClose, content }) {
  const { api, user } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [suggestion, setSuggestion] = useState(null);
  const [listing, setListing] = useState(null);            // listing aperto, se c'è
  const [incomingOffers, setIncomingOffers] = useState([]);// per owner
  const [activeContracts, setActiveContracts] = useState([]);
  const [myStations, setMyStations] = useState([]);

  // form pubblicazione (owner)
  const [pubMode, setPubMode] = useState('split');
  const [pubMoney, setPubMoney] = useState(0);
  const [pubCredits, setPubCredits] = useState(0);
  const [pubDuration, setPubDuration] = useState(7);
  const [pubNotes, setPubNotes] = useState('');

  // form offerta (buyer)
  const [offerMode, setOfferMode] = useState('split');
  const [offerMoney, setOfferMoney] = useState(0);
  const [offerCredits, setOfferCredits] = useState(0);
  const [offerDuration, setOfferDuration] = useState(7);
  const [offerStation, setOfferStation] = useState('');
  const [offerMessage, setOfferMessage] = useState('');

  const isOwner = !!content && content.user_id === user?.id;
  const collection = useMemo(() => {
    if (!content) return null;
    if (content.type === 'tv_series' || content.type === 'anime') return 'tv_series';
    return 'films';
  }, [content]);

  const hasActiveFullContract = useMemo(
    () => activeContracts.some(c => c.mode === 'full'),
    [activeContracts]
  );

  // ── Loaders ─────────────────────────────────────────
  const loadAll = async () => {
    if (!content?.id || !collection) return;
    setLoading(true);
    try {
      // Suggested prices
      const sug = await api.post('/tv-market/suggested-price', {
        content_id: content.id,
        content_collection: collection,
      }).then(r => r.data?.prices).catch(() => null);
      setSuggestion(sug);
      if (sug?.split) {
        setPubMoney(sug.split.money);
        setPubCredits(sug.split.credits);
        setOfferMoney(sug.split.money);
        setOfferCredits(sug.split.credits);
      }

      // Active contracts (visibili a tutti)
      const ac = await api.get(`/tv-market/contracts/active/${content.id}`).then(r => r.data?.contracts || []).catch(() => []);
      setActiveContracts(ac);

      // Listings pubblici → trova quello del nostro contenuto
      const all = await api.get('/tv-market/listings').then(r => r.data?.listings || []).catch(() => []);
      const mine = all.find(l => l.content_id === content.id) || null;
      setListing(mine);

      // Owner: offerte ricevute
      if (content.user_id === user?.id) {
        const inc = await api.get('/tv-market/incoming-offers').then(r => r.data?.offers || []).catch(() => []);
        const filtered = inc.filter(o => o.content_id === content.id);
        setIncomingOffers(filtered);
      }

      // Buyer: carica le proprie TV
      if (content.user_id !== user?.id) {
        try {
          const stations = await api.get('/tv-stations/my').then(r => r.data?.stations || r.data || []);
          setMyStations(Array.isArray(stations) ? stations : []);
          if (Array.isArray(stations) && stations.length > 0 && !offerStation) {
            setOfferStation(stations[0].id);
          }
        } catch { setMyStations([]); }
      }
    } finally { setLoading(false); }
  };

  useEffect(() => { if (open) loadAll(); /* eslint-disable-next-line */ }, [open, content?.id]);

  // ── Owner actions ──────────────────────────────────
  const publishListing = async () => {
    setLoading(true);
    try {
      await api.post('/tv-market/list', {
        content_id: content.id,
        content_collection: collection,
        mode: pubMode,
        asking_money: Math.max(0, parseInt(pubMoney || 0)),
        asking_credits: Math.max(0, parseInt(pubCredits || 0)),
        duration_days: Math.max(1, parseInt(pubDuration || 7)),
        notes: pubNotes,
      });
      toast.success('Contenuto pubblicato sul mercato!');
      await loadAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore pubblicazione');
    } finally { setLoading(false); }
  };

  const cancelListing = async () => {
    if (!listing?.id) return;
    if (!window.confirm('Vuoi davvero ritirare il contenuto dal mercato? Tutte le offerte pendenti verranno annullate.')) return;
    setLoading(true);
    try {
      await api.delete(`/tv-market/listings/${listing.id}`);
      toast.success('Listing annullato');
      await loadAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally { setLoading(false); }
  };

  const decideOffer = async (offerId, action, body) => {
    setLoading(true);
    try {
      const url = `/tv-market/offers/${offerId}/${action}`;
      await api.post(url, body || {});
      toast.success(action === 'accept' ? 'Offerta accettata!' : action === 'reject' ? 'Offerta rifiutata' : 'Controproposta inviata');
      await loadAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally { setLoading(false); }
  };

  // ── Buyer action ───────────────────────────────────
  const sendOffer = async () => {
    if (!offerStation) return toast.error('Seleziona una tua stazione TV');
    setLoading(true);
    try {
      if (listing?.id) {
        // Standard offer on an open listing
        await api.post(`/tv-market/listings/${listing.id}/offer`, {
          station_id: offerStation,
          offered_money: Math.max(0, parseInt(offerMoney || 0)),
          offered_credits: Math.max(0, parseInt(offerCredits || 0)),
          mode_proposed: offerMode,
          duration_days_proposed: Math.max(1, parseInt(offerDuration || 7)),
          message: offerMessage,
        });
      } else {
        // Spontaneous offer (no listing): direct to owner
        await api.post(`/tv-market/content/${content.id}/spontaneous-offer`, {
          content_id: content.id,
          content_collection: collection,
          station_id: offerStation,
          offered_money: Math.max(0, parseInt(offerMoney || 0)),
          offered_credits: Math.max(0, parseInt(offerCredits || 0)),
          mode_proposed: offerMode,
          duration_days_proposed: Math.max(1, parseInt(offerDuration || 7)),
          message: offerMessage,
        });
      }
      toast.success('Offerta inviata!');
      await loadAll();
      setActiveTab('overview');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore offerta');
    } finally { setLoading(false); }
  };

  if (!content) return null;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent
        className="max-w-md p-0 bg-[#0b0b0d] border border-amber-500/20 max-h-[92vh] overflow-hidden flex flex-col"
        data-testid="tv-market-modal"
      >
        {/* HEADER */}
        <div className="px-4 pt-3 pb-3 border-b border-white/10 flex-shrink-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <Tv size={18} className="text-amber-400 flex-shrink-0" />
              <div className="min-w-0">
                <h2 className="text-base font-bold text-white truncate font-['Bebas_Neue'] tracking-wide">
                  Mercato Diritti TV
                </h2>
                <p className="text-[10px] text-white/50 truncate">"{content.title}"</p>
              </div>
            </div>
            <button onClick={onClose} className="text-white/40 hover:text-white p-1 -mr-1 flex-shrink-0" data-testid="tv-market-close" aria-label="Chiudi">
              <X size={16} />
            </button>
          </div>

          {/* Status banner */}
          {hasActiveFullContract && (
            <div className="mt-2 px-2 py-1.5 rounded bg-amber-500/10 border border-amber-500/30 flex items-center gap-1.5">
              <Lock size={11} className="text-amber-300" />
              <p className="text-[10px] text-amber-200">Contratto esclusivo (100%) attivo. Il proprietario non può trasmettere fino alla scadenza.</p>
            </div>
          )}
        </div>

        {/* TABS */}
        <div className="flex border-b border-white/5 flex-shrink-0">
          <TabBtn active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} icon={Tv} label="Panoramica" />
          {isOwner ? (
            <>
              <TabBtn active={activeTab === 'publish'} onClick={() => setActiveTab('publish')} icon={Crown} label={listing ? 'Modifica' : 'Pubblica'} />
              <TabBtn active={activeTab === 'offers'} onClick={() => setActiveTab('offers')} icon={Users} label={`Offerte ${incomingOffers.length ? `(${incomingOffers.length})` : ''}`} />
            </>
          ) : (
            <TabBtn active={activeTab === 'offer'} onClick={() => setActiveTab('offer')} icon={Send} label="Fai Offerta" />
          )}
        </div>

        {/* BODY */}
        <div className="flex-1 overflow-y-auto px-4 py-3" data-testid="tv-market-body">
          {loading && (
            <div className="flex items-center justify-center py-4 text-white/50 text-[11px]"><Loader2 size={14} className="animate-spin mr-1.5"/> Caricamento…</div>
          )}

          {/* PANORAMICA */}
          {activeTab === 'overview' && (
            <Overview
              suggestion={suggestion}
              listing={listing}
              activeContracts={activeContracts}
              isOwner={isOwner}
              onCancelListing={cancelListing}
            />
          )}

          {/* PUBBLICA (owner) */}
          {activeTab === 'publish' && isOwner && (
            <PublishForm
              listing={listing}
              suggestion={suggestion}
              pubMode={pubMode} setPubMode={setPubMode}
              pubMoney={pubMoney} setPubMoney={setPubMoney}
              pubCredits={pubCredits} setPubCredits={setPubCredits}
              pubDuration={pubDuration} setPubDuration={setPubDuration}
              pubNotes={pubNotes} setPubNotes={setPubNotes}
              onPublish={publishListing}
              loading={loading}
            />
          )}

          {/* OFFERTE (owner) */}
          {activeTab === 'offers' && isOwner && (
            <OffersList
              offers={incomingOffers}
              onAccept={(id) => decideOffer(id, 'accept')}
              onReject={(id) => decideOffer(id, 'reject')}
              onCounter={(id, body) => decideOffer(id, 'counter', body)}
              loading={loading}
            />
          )}

          {/* FAI OFFERTA (buyer) */}
          {activeTab === 'offer' && !isOwner && (
            <OfferForm
              listing={listing}
              suggestion={suggestion}
              myStations={myStations}
              offerStation={offerStation} setOfferStation={setOfferStation}
              offerMode={offerMode} setOfferMode={setOfferMode}
              offerMoney={offerMoney} setOfferMoney={setOfferMoney}
              offerCredits={offerCredits} setOfferCredits={setOfferCredits}
              offerDuration={offerDuration} setOfferDuration={setOfferDuration}
              offerMessage={offerMessage} setOfferMessage={setOfferMessage}
              onSend={sendOffer}
              loading={loading}
              hasActiveFullContract={hasActiveFullContract}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Sub-components ────────────────────────────────────
const TabBtn = ({ active, onClick, icon: Icon, label }) => (
  <button
    onClick={onClick}
    className={`flex-1 py-2 text-[10px] font-bold flex items-center justify-center gap-1 touch-manipulation transition-colors ${
      active ? 'text-amber-300 border-b-2 border-amber-400' : 'text-white/50 hover:text-white/80'
    }`}
    data-testid={`tv-market-tab-${label.toLowerCase().replace(/\s/g, '-')}`}
  >
    <Icon size={12} /> {label}
  </button>
);

const Overview = ({ suggestion, listing, activeContracts, isOwner, onCancelListing }) => (
  <div>
    {/* Listing status */}
    {listing ? (
      <div className="mb-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
        <div className="text-[10px] uppercase tracking-wider text-emerald-300 font-bold mb-1">📡 In vendita sul mercato</div>
        <div className="grid grid-cols-2 gap-2 mt-2">
          <Stat label="Prezzo" value={`${fmtMoney(listing.asking_money)} + ${listing.asking_credits} CP`} />
          <Stat label="Modalità default" value={listing.mode_default === 'full' ? 'Esclusiva 100%' : 'Co-licenza 50%'} />
          <Stat label="Durata proposta" value={`${listing.duration_days} giorni`} />
          <Stat label="Pubblicato" value={new Date(listing.created_at).toLocaleDateString('it-IT')} />
        </div>
        {isOwner && (
          <button onClick={onCancelListing} className="mt-2 w-full py-1.5 text-[10px] font-bold rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border border-rose-500/30 touch-manipulation" data-testid="tv-market-cancel-listing">
            Ritira dal Mercato
          </button>
        )}
      </div>
    ) : (
      <div className="mb-3 p-3 rounded-lg bg-white/[0.02] border border-white/5 text-center">
        <p className="text-[11px] text-white/50">{isOwner ? 'Non hai ancora pubblicato questo contenuto sul mercato.' : 'Questo contenuto non è sul mercato — puoi comunque inviare un\'offerta spontanea al proprietario tramite "Fai Offerta".'}</p>
      </div>
    )}

    {/* Active contracts */}
    {activeContracts.length > 0 && (
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-wider text-white/60 font-bold mb-1.5">📺 Contratti attivi</div>
        <div className="space-y-1.5">
          {activeContracts.map(c => (
            <div key={c.id} className={`p-2 rounded-lg border ${c.mode === 'full' ? 'bg-amber-500/5 border-amber-500/30' : 'bg-cyan-500/5 border-cyan-500/30'}`}>
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-bold text-white">{c.station_name}</span>
                <span className={`text-[9px] uppercase font-bold ${c.mode === 'full' ? 'text-amber-300' : 'text-cyan-300'}`}>
                  {c.mode === 'full' ? '100%' : '50%'}
                </span>
              </div>
              <div className="text-[9px] text-white/50 mt-0.5">
                Fino al {new Date(c.end_at).toLocaleDateString('it-IT')} ({c.duration_days}gg) · {fmtMoney(c.money_paid)}
              </div>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Suggested prices */}
    {suggestion && (
      <div className="mb-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
        <div className="text-[10px] uppercase tracking-wider text-white/60 font-bold mb-2">💡 Valore di mercato suggerito</div>
        <div className="space-y-2">
          <PriceTier mode="split" data={suggestion.split} />
          <PriceTier mode="full" data={suggestion.full} />
        </div>
      </div>
    )}
  </div>
);

const PriceTier = ({ mode, data }) => {
  const cfg = MODE_DESC[mode];
  const isFull = mode === 'full';
  return (
    <div className={`p-2 rounded ${isFull ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-cyan-500/5 border border-cyan-500/20'}`}>
      <div className="flex items-center justify-between mb-1">
        <span className={`text-[10px] font-bold ${isFull ? 'text-amber-300' : 'text-cyan-300'}`}>{cfg.title}</span>
        <span className="font-mono text-[11px] text-white font-bold">{fmtMoney(data.money)} + {data.credits} CP</span>
      </div>
      <p className="text-[9px] text-white/55 leading-snug">{cfg.desc}</p>
    </div>
  );
};

const Stat = ({ label, value }) => (
  <div>
    <div className="text-[8px] uppercase text-white/40 font-bold">{label}</div>
    <div className="text-[10px] text-white font-bold truncate">{value}</div>
  </div>
);

const PublishForm = ({ listing, suggestion, pubMode, setPubMode, pubMoney, setPubMoney, pubCredits, setPubCredits, pubDuration, setPubDuration, pubNotes, setPubNotes, onPublish, loading }) => (
  <div>
    {listing ? (
      <div className="mb-3 px-2 py-1.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-[10px] text-emerald-200">
        ✓ Già pubblicato. Per modificare, ritira e ripubblica.
      </div>
    ) : (
      <p className="text-[10px] text-white/60 mb-3 italic">Imposta i termini di base. I buyer potranno comunque proporre offerte personalizzate.</p>
    )}

    <div className="space-y-2.5">
      <div>
        <label className="text-[9px] uppercase font-bold text-white/60">Modalità default</label>
        <div className="grid grid-cols-2 gap-1.5 mt-1">
          {['split', 'full'].map(m => (
            <button key={m} onClick={() => setPubMode(m)} disabled={!!listing} data-testid={`tv-market-pub-mode-${m}`}
              className={`py-2 rounded text-[10px] font-bold touch-manipulation ${
                pubMode === m
                  ? (m === 'full' ? 'bg-amber-500 text-black' : 'bg-cyan-500 text-black')
                  : 'bg-white/5 text-white/60'
              } disabled:opacity-50`}>
              {MODE_DESC[m].title}
            </button>
          ))}
        </div>
        <p className="text-[8px] text-white/50 mt-1">{MODE_DESC[pubMode].desc}</p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <NumInput label="Denaro ($)" value={pubMoney} onChange={setPubMoney} disabled={!!listing} testid="tv-market-pub-money" />
        <NumInput label="Crediti (CP)" value={pubCredits} onChange={setPubCredits} disabled={!!listing} testid="tv-market-pub-credits" />
      </div>
      <NumInput label="Durata (giorni)" value={pubDuration} onChange={setPubDuration} disabled={!!listing} testid="tv-market-pub-duration" />

      <div>
        <label className="text-[9px] uppercase font-bold text-white/60">Note (opzionale)</label>
        <textarea
          value={pubNotes} onChange={e => setPubNotes(e.target.value)}
          maxLength={300} disabled={!!listing}
          placeholder="Es: Solo offerte serie. Preferisco contratti brevi..."
          className="w-full mt-1 rounded bg-black/40 border border-white/10 px-2 py-1.5 text-[11px] text-white"
          rows={2}
          data-testid="tv-market-pub-notes"
        />
      </div>

      {suggestion && (
        <div className="p-2 rounded bg-white/[0.02] border border-white/5">
          <div className="text-[8px] uppercase text-white/50 font-bold mb-1">Suggerimenti AI</div>
          <button
            onClick={() => { setPubMoney(suggestion[pubMode].money); setPubCredits(suggestion[pubMode].credits); }}
            disabled={!!listing}
            className="w-full text-left py-1 px-1.5 rounded bg-white/5 hover:bg-white/10 text-[10px] text-white/80 disabled:opacity-50 touch-manipulation"
            data-testid="tv-market-pub-use-suggested"
          >
            ⚡ Usa prezzo consigliato: {fmtMoney(suggestion[pubMode].money)} + {suggestion[pubMode].credits} CP
          </button>
        </div>
      )}

      <button
        onClick={onPublish} disabled={loading || !!listing}
        className="w-full py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-black text-[12px] disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
        data-testid="tv-market-publish-btn"
      >
        {loading ? 'Pubblicazione…' : listing ? 'Già pubblicato' : 'PUBBLICA SUL MERCATO'}
      </button>
    </div>
  </div>
);

const OfferForm = ({ listing, suggestion, myStations, offerStation, setOfferStation, offerMode, setOfferMode, offerMoney, setOfferMoney, offerCredits, setOfferCredits, offerDuration, setOfferDuration, offerMessage, setOfferMessage, onSend, loading, hasActiveFullContract }) => {
  if (!myStations || myStations.length === 0) {
    return (
      <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-center">
        <Tv size={20} className="inline text-rose-300 mb-1.5" />
        <p className="text-[11px] text-rose-200 font-bold">Nessuna TV in tuo possesso</p>
        <p className="text-[10px] text-white/60 mt-1">Per acquistare diritti devi prima costruire una stazione TV (Infrastrutture).</p>
      </div>
    );
  }
  return (
    <div className="space-y-2.5">
      {!listing && (
        <div className="p-2 rounded bg-cyan-500/10 border border-cyan-500/30 flex items-start gap-1.5">
          <Send size={12} className="text-cyan-300 mt-0.5 flex-shrink-0" />
          <p className="text-[10px] text-cyan-100 leading-snug">
            <span className="font-bold">Offerta spontanea</span> — questo contenuto non è sul mercato, ma puoi proporre direttamente al proprietario. Lui decide se accettare.
          </p>
        </div>
      )}
      {hasActiveFullContract && (
        <div className="p-2 rounded bg-amber-500/10 border border-amber-500/30 flex items-center gap-1.5">
          <Lock size={12} className="text-amber-300" />
          <p className="text-[10px] text-amber-200">Esiste già un contratto esclusivo (100%). Le tue offerte verranno considerate alla scadenza.</p>
        </div>
      )}

      <div>
        <label className="text-[9px] uppercase font-bold text-white/60">La tua stazione TV</label>
        <select value={offerStation} onChange={e => setOfferStation(e.target.value)} data-testid="tv-market-offer-station"
          className="w-full mt-1 h-9 rounded bg-black/40 border border-white/10 text-[11px] px-2 text-white">
          {myStations.map(s => (
            <option key={s.id} value={s.id}>{s.custom_name || s.name || 'TV'}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-[9px] uppercase font-bold text-white/60">Modalità diritti</label>
        <div className="grid grid-cols-2 gap-1.5 mt-1">
          {['split', 'full'].map(m => (
            <button key={m} onClick={() => setOfferMode(m)} data-testid={`tv-market-offer-mode-${m}`}
              className={`py-2 rounded text-[10px] font-bold touch-manipulation ${
                offerMode === m
                  ? (m === 'full' ? 'bg-amber-500 text-black' : 'bg-cyan-500 text-black')
                  : 'bg-white/5 text-white/60'
              }`}>
              {MODE_DESC[m].title}
            </button>
          ))}
        </div>
        <p className="text-[8px] text-white/50 mt-1">{MODE_DESC[offerMode].desc}</p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <NumInput label="La tua offerta ($)" value={offerMoney} onChange={setOfferMoney} testid="tv-market-offer-money" />
        <NumInput label="Crediti (CP)" value={offerCredits} onChange={setOfferCredits} testid="tv-market-offer-credits" />
      </div>
      <NumInput label="Durata (giorni)" value={offerDuration} onChange={setOfferDuration} testid="tv-market-offer-duration" />

      <div>
        <label className="text-[9px] uppercase font-bold text-white/60">Messaggio al proprietario (opzionale)</label>
        <textarea value={offerMessage} onChange={e => setOfferMessage(e.target.value)} rows={2} maxLength={300}
          placeholder="Es: Voglio darle visibilità sul mio canale prime time…"
          className="w-full mt-1 rounded bg-black/40 border border-white/10 px-2 py-1.5 text-[11px] text-white"
          data-testid="tv-market-offer-message" />
      </div>

      {suggestion && (
        <div className="p-2 rounded bg-white/[0.02] border border-white/5">
          <button onClick={() => { setOfferMoney(suggestion[offerMode].money); setOfferCredits(suggestion[offerMode].credits); }}
            className="w-full text-left py-1 px-1.5 rounded bg-white/5 hover:bg-white/10 text-[10px] text-white/80 touch-manipulation"
            data-testid="tv-market-offer-use-suggested">
            ⚡ Usa prezzo consigliato: {fmtMoney(suggestion[offerMode].money)} + {suggestion[offerMode].credits} CP
          </button>
        </div>
      )}

      <div className="p-2 rounded bg-amber-500/5 border border-amber-500/20">
        <p className="text-[9px] text-amber-200/90 leading-snug italic">
          ⚠ L'offerta blocca i fondi solo all'accettazione. Il proprietario può accettare, rifiutare o controproporre.
        </p>
      </div>

      <button onClick={onSend} disabled={loading}
        className="w-full py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-black text-[12px] disabled:opacity-50 touch-manipulation"
        data-testid="tv-market-send-offer-btn">
        {loading ? 'Invio…' : 'INVIA OFFERTA'}
      </button>
    </div>
  );
};

const OffersList = ({ offers, onAccept, onReject, onCounter, loading }) => {
  const [counterFor, setCounterFor] = useState(null);
  if (offers.length === 0) {
    return <p className="text-[10px] text-white/50 italic text-center py-6">Nessuna offerta ricevuta su questo contenuto.</p>;
  }
  return (
    <div className="space-y-2">
      {offers.map(o => (
        <OfferRow key={o.id} offer={o} loading={loading}
          onAccept={() => onAccept(o.id)}
          onReject={() => onReject(o.id)}
          onCounter={(body) => onCounter(o.id, body)}
          counterOpen={counterFor === o.id}
          setCounterOpen={(v) => setCounterFor(v ? o.id : null)}
        />
      ))}
    </div>
  );
};

const OfferRow = ({ offer, onAccept, onReject, onCounter, counterOpen, setCounterOpen, loading }) => {
  const isPending = offer.status === 'pending';
  const isCountered = offer.status === 'countered_by_owner_pending_buyer';
  const [cMoney, setCMoney] = useState(offer.offered_money);
  const [cCredits, setCCredits] = useState(offer.offered_credits);
  const [cDuration, setCDuration] = useState(offer.duration_days_proposed);
  const [cMsg, setCMsg] = useState('');
  return (
    <div className={`p-2.5 rounded-lg border ${isPending ? 'bg-amber-500/5 border-amber-500/30' : 'bg-white/[0.02] border-white/5'}`} data-testid={`tv-market-offer-row-${offer.id}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-bold text-white truncate">{offer.buyer_house || offer.buyer_nickname || 'Buyer'}</div>
          <div className="text-[9px] text-white/50">📺 {offer.station_name}</div>
        </div>
        <span className={`text-[8px] uppercase font-bold px-1.5 py-0.5 rounded ${
          isPending ? 'bg-amber-400 text-black' :
          isCountered ? 'bg-cyan-500 text-black' :
          offer.status === 'accepted' ? 'bg-emerald-500 text-black' :
          'bg-white/10 text-white/60'
        }`}>
          {isPending ? 'PENDING' : isCountered ? 'CONTROPROPOSTA' : offer.status.replace(/_/g, ' ').toUpperCase()}
        </span>
      </div>
      <div className="mt-1.5 grid grid-cols-3 gap-1.5 text-[10px]">
        <div>
          <div className="text-[8px] uppercase text-white/40 font-bold">Offerta</div>
          <div className="text-white font-bold">{fmtMoney(offer.offered_money)}</div>
          <div className="text-white/60">{offer.offered_credits} CP</div>
        </div>
        <div>
          <div className="text-[8px] uppercase text-white/40 font-bold">Modo</div>
          <div className="text-white font-bold">{offer.mode_proposed === 'full' ? '100%' : '50%'}</div>
        </div>
        <div>
          <div className="text-[8px] uppercase text-white/40 font-bold">Durata</div>
          <div className="text-white font-bold">{offer.duration_days_proposed}gg</div>
        </div>
      </div>
      {offer.message && (
        <p className="mt-1.5 text-[9px] text-white/70 italic">"{offer.message}"</p>
      )}

      {isPending && (
        <div className="mt-2 flex gap-1">
          <button onClick={onAccept} disabled={loading}
            className="flex-1 py-1.5 rounded bg-emerald-500 hover:bg-emerald-400 text-black text-[10px] font-bold touch-manipulation disabled:opacity-50"
            data-testid={`tv-market-offer-accept-${offer.id}`}>
            <Check size={11} className="inline" /> Accetta
          </button>
          <button onClick={() => setCounterOpen(!counterOpen)} disabled={loading}
            className="flex-1 py-1.5 rounded bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-200 text-[10px] font-bold touch-manipulation disabled:opacity-50"
            data-testid={`tv-market-offer-counter-${offer.id}`}>
            ⇄ Controproponi
          </button>
          <button onClick={onReject} disabled={loading}
            className="flex-1 py-1.5 rounded bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-200 text-[10px] font-bold touch-manipulation disabled:opacity-50"
            data-testid={`tv-market-offer-reject-${offer.id}`}>
            <X size={11} className="inline" /> Rifiuta
          </button>
        </div>
      )}

      {counterOpen && (
        <div className="mt-2 p-2 rounded bg-cyan-500/5 border border-cyan-500/20 space-y-1.5">
          <p className="text-[9px] text-cyan-200 font-bold">La tua controproposta:</p>
          <div className="grid grid-cols-3 gap-1.5">
            <NumInput label="$" value={cMoney} onChange={setCMoney} small />
            <NumInput label="CP" value={cCredits} onChange={setCCredits} small />
            <NumInput label="gg" value={cDuration} onChange={setCDuration} small />
          </div>
          <textarea value={cMsg} onChange={e => setCMsg(e.target.value)} rows={1} maxLength={300}
            placeholder="Messaggio…"
            className="w-full rounded bg-black/40 border border-white/10 px-2 py-1 text-[10px] text-white" />
          <button onClick={() => onCounter({ counter_money: parseInt(cMoney || 0), counter_credits: parseInt(cCredits || 0), counter_duration_days: parseInt(cDuration || 7), message: cMsg })}
            disabled={loading}
            className="w-full py-1.5 rounded bg-cyan-500 hover:bg-cyan-400 text-black text-[10px] font-bold touch-manipulation disabled:opacity-50">
            <ArrowRight size={11} className="inline" /> Invia controproposta
          </button>
        </div>
      )}
    </div>
  );
};

const NumInput = ({ label, value, onChange, disabled, testid, small }) => (
  <div>
    <label className={`uppercase font-bold text-white/60 ${small ? 'text-[8px]' : 'text-[9px]'}`}>{label}</label>
    <input
      type="number" min="0"
      value={value || ''}
      onChange={e => onChange(e.target.value === '' ? '' : parseInt(e.target.value || 0))}
      disabled={disabled}
      data-testid={testid}
      className={`w-full mt-0.5 rounded bg-black/40 border border-white/10 px-2 py-1.5 text-white disabled:opacity-50 ${small ? 'text-[10px]' : 'text-[11px]'}`}
    />
  </div>
);
