// CineWorld Studio's — Bank Page (/banca)
// Loans + CinePass exchange + Infrastructure upgrade.

import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { toast } from 'sonner';
import {
  ArrowLeft, Landmark, Ticket, DollarSign, Loader2, TrendingUp,
  Building2, Coins, CreditCard, CheckCircle, AlertTriangle, ArrowRight, Clock
} from 'lucide-react';
import UserStripBanner from '../components/UserStripBanner';  // not used — handled globally

const fmt = (n) => {
  const v = Number(n || 0);
  if (Math.abs(v) >= 1_000_000) return `$${(v / 1_000_000).toFixed(2)}M`;
  if (Math.abs(v) >= 1_000) return `$${(v / 1_000).toFixed(1)}K`;
  return `$${v.toLocaleString()}`;
};

export default function BankPage() {
  const { api, refreshUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('loans'); // loans | exchange | infra

  // Loan form
  const [loanAmount, setLoanAmount] = useState(100000);
  const [loanDuration, setLoanDuration] = useState(7);
  const [takingLoan, setTakingLoan] = useState(false);

  // Exchange form
  const [exchangeDir, setExchangeDir] = useState('buy_cp'); // buy_cp | sell_cp
  const [cpAmount, setCpAmount] = useState(10);
  const [exchanging, setExchanging] = useState(false);

  // Infra upgrade
  const [upgrading, setUpgrading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get('/bank/status');
      setStatus(r.data);
      if (r.data?.can_borrow) setLoanAmount(Math.min(100000, r.data.can_borrow));
    } catch { /* noop */ }
    setLoading(false);
  };
  useEffect(() => { load(); }, []); // eslint-disable-line

  const takeLoan = async () => {
    setTakingLoan(true);
    try {
      const r = await api.post('/bank/take-loan', { amount: loanAmount, installments: loanDuration });
      toast.success(r.data?.message || 'Prestito erogato');
      await refreshUser?.();
      await load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore prestito'); }
    setTakingLoan(false);
  };

  const repayLoan = async (loanId) => {
    if (!window.confirm("Vuoi estinguere il prestito in un'unica soluzione?")) return;
    try {
      const r = await api.post(`/bank/repay-loan/${loanId}`);
      toast.success(r.data?.message || 'Prestito estinto');
      await refreshUser?.();
      await load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
  };

  const doExchange = async () => {
    setExchanging(true);
    try {
      const r = await api.post('/bank/exchange', { direction: exchangeDir, amount: cpAmount });
      toast.success(r.data?.message);
      await refreshUser?.();
      await load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setExchanging(false);
  };

  const upgradeInfra = async () => {
    setUpgrading(true);
    try {
      const r = await api.post('/bank/upgrade-infra');
      toast.success(r.data?.message);
      await refreshUser?.();
      await load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Errore'); }
    setUpgrading(false);
  };

  if (loading || !status) {
    return <div className="min-h-screen bg-[#07060a] flex items-center justify-center"><Loader2 className="w-6 h-6 text-amber-400 animate-spin" /></div>;
  }

  const infra = status.infra;
  const nextTier = status.next_level;

  // Calculate loan interest preview
  const durationMult = { 3: 0.3, 7: 0.6, 14: 1.0, 30: 1.6 }[loanDuration] || 0.6;
  const estInterest = Math.round(loanAmount * (infra.interest_pct / 100) * durationMult);
  const estTotal = loanAmount + estInterest;
  const estDaily = Math.round(estTotal / loanDuration);

  return (
    <div className="min-h-screen bg-[#07060a] text-white pb-10" data-testid="bank-page">
      <div className="px-3 pt-3 pb-2 flex items-center gap-2">
        <button onClick={() => navigate(-1)} className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-amber-300 active:scale-90 transition-transform" data-testid="bank-back">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1">
          <p className="text-[9px] text-amber-400/70 tracking-[0.3em] font-bold uppercase">CineBank</p>
          <h1 className="text-lg font-black text-white leading-tight" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>Banca</h1>
        </div>
        <Landmark className="w-5 h-5 text-amber-400" />
      </div>

      {/* Infra status card → click va alla tab Upgrade */}
      <button onClick={() => setTab('infra')} className="w-full mx-0 text-left" data-testid="bank-infra-card-click">
      <div className="mx-3 rounded-xl p-4 bg-gradient-to-br from-amber-500/15 via-[#1a1208] to-[#0a0706] border border-amber-500/30 active:scale-[0.99] transition-transform" data-testid="bank-infra-card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[9px] text-amber-300/70 tracking-wider uppercase">La Tua Infrastruttura</p>
            <p className="text-lg font-black text-amber-100" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
              Lv {infra.level} · {infra.label}
            </p>
          </div>
          <Building2 className="w-8 h-8 text-amber-400/70" />
        </div>
        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-amber-500/15">
          <div className="text-center">
            <p className="text-[8px] text-gray-500 uppercase">Max Prestito</p>
            <p className="text-[11px] font-bold text-amber-200">{fmt(infra.max_loan_for_you)}</p>
          </div>
          <div className="text-center">
            <p className="text-[8px] text-gray-500 uppercase">Interesse</p>
            <p className="text-[11px] font-bold text-amber-200">{infra.interest_pct}%</p>
          </div>
          <div className="text-center">
            <p className="text-[8px] text-gray-500 uppercase">Disponibile</p>
            <p className="text-[11px] font-bold text-emerald-300">{fmt(status.can_borrow)}</p>
          </div>
        </div>
        {infra.level === 0 && (
          <p className="text-[9px] text-amber-300/70 text-center mt-2">
            <Building2 className="w-3 h-3 inline mr-0.5" />
            Clicca qui per <b className="underline">acquistare Infrastruttura Banca</b> (tab Upgrade)
          </p>
        )}
      </div>
      </button>

      {/* Tabs */}
      <div className="mx-3 mt-3 flex gap-1 bg-[#0f0d10] rounded-lg p-1">
        <TabBtn active={tab === 'loans'} onClick={() => setTab('loans')} icon={<Coins className="w-3.5 h-3.5" />} label="Prestiti" testId="bt-loans" />
        <TabBtn active={tab === 'exchange'} onClick={() => setTab('exchange')} icon={<Ticket className="w-3.5 h-3.5" />} label="Cambio" testId="bt-exchange" />
        <TabBtn active={tab === 'infra'} onClick={() => setTab('infra')} icon={<Building2 className="w-3.5 h-3.5" />} label="Upgrade" testId="bt-infra" />
      </div>

      <div className="mx-3 mt-3">
        {tab === 'loans' && (
          <div className="space-y-4">
            {/* Active loans */}
            {status.active_loans.length > 0 && (
              <div className="p-3 bg-sky-500/5 rounded-xl border border-sky-500/20">
                <p className="text-[10px] font-bold text-sky-200 tracking-wider uppercase mb-2">Prestiti Attivi</p>
                {status.active_loans.map(loan => (
                  <div key={loan.id} className="p-2 bg-[#0f0d10] rounded-lg mb-1.5" data-testid={`active-loan-${loan.id}`}>
                    <div className="flex items-center justify-between">
                      <p className="text-[11px] font-bold text-white">{fmt(loan.principal)} · {loan.installments}g</p>
                      <p className="text-[9px] text-sky-300">Rata: {fmt(loan.daily_payment)}/g</p>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-sky-400 to-sky-500" style={{ width: `${((loan.paid_installments / loan.installments) * 100).toFixed(0)}%` }} />
                      </div>
                      <p className="text-[9px] text-sky-300">{loan.paid_installments}/{loan.installments}</p>
                    </div>
                    <div className="flex items-center justify-between mt-1.5">
                      <p className="text-[9px] text-gray-500"><Clock className="w-2.5 h-2.5 inline mr-0.5" /> Residuo: {fmt(loan.remaining_amount)}</p>
                      <button onClick={() => repayLoan(loan.id)} className="px-2 py-0.5 rounded bg-rose-500/20 border border-rose-500/40 text-[9px] text-rose-200 hover:bg-rose-500/30 active:scale-95 transition-transform" data-testid={`repay-loan-${loan.id}`}>
                        Estingui
                      </button>
                    </div>
                  </div>
                ))}
                <p className="text-[9px] text-gray-500 text-center mt-1">Debito totale: {fmt(status.total_debt)}</p>
              </div>
            )}

            {/* New loan form */}
            <div className="p-3 bg-emerald-500/5 rounded-xl border border-emerald-500/20" data-testid="new-loan-form">
              <div className="flex items-center gap-1 mb-2">
                <Coins className="w-3.5 h-3.5 text-emerald-400" />
                <p className="text-[10px] font-bold text-emerald-200 tracking-wider uppercase">Richiedi Prestito</p>
              </div>
              <p className="text-[9px] text-gray-400 mb-2">Importo ($)</p>
              <div className="px-3">
                <input
                  type="range"
                  min={10000}
                  max={Math.max(10000, status.can_borrow)}
                  step={10000}
                  value={Math.min(loanAmount, Math.max(10000, status.can_borrow))}
                  onChange={(e) => setLoanAmount(Number(e.target.value))}
                  disabled={status.can_borrow < 10000}
                  className="w-full accent-emerald-400 disabled:opacity-40 block"
                  style={{ maxWidth: '100%' }}
                  data-testid="loan-amount-slider"
                />
                <div className="flex justify-between text-[8px] text-gray-500 mt-0.5 px-0.5">
                  <span>{fmt(10000)}</span>
                  <span>{fmt(Math.max(10000, status.can_borrow))}</span>
                </div>
              </div>
              <p className="text-center text-xl font-bold text-emerald-200 my-1" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>{fmt(loanAmount)}</p>

              <p className="text-[9px] text-gray-400 mt-3 mb-1">Durata (giorni)</p>
              <div className="grid grid-cols-4 gap-1">
                {[3, 7, 14, 30].map(d => (
                  <button key={d} onClick={() => setLoanDuration(d)}
                    className={`py-2 rounded text-[11px] font-bold ${loanDuration === d ? 'bg-emerald-500 text-black' : 'bg-white/5 text-gray-300 border border-white/10'}`}
                    data-testid={`loan-duration-${d}`}>
                    {d}g
                  </button>
                ))}
              </div>

              <div className="mt-3 p-2 rounded-lg bg-black/30 border border-emerald-500/10">
                <div className="flex justify-between text-[9px] text-gray-400">
                  <span>Capitale</span><span className="text-white">{fmt(loanAmount)}</span>
                </div>
                <div className="flex justify-between text-[9px] text-gray-400">
                  <span>Interessi ({infra.interest_pct}% × {durationMult}x)</span><span className="text-rose-300">+{fmt(estInterest)}</span>
                </div>
                <div className="flex justify-between text-[10px] font-bold border-t border-white/5 pt-1 mt-1">
                  <span className="text-emerald-200">Totale da restituire</span><span className="text-emerald-200">{fmt(estTotal)}</span>
                </div>
                <div className="flex justify-between text-[9px] text-gray-400">
                  <span>Rata giornaliera</span><span className="text-sky-300">{fmt(estDaily)}/g</span>
                </div>
              </div>

              <button onClick={takeLoan} disabled={takingLoan || loanAmount <= 0 || loanAmount > status.can_borrow}
                className="w-full mt-3 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-400 text-black font-bold text-[11px] hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
                data-testid="take-loan-btn">
                {takingLoan ? <Loader2 className="w-3 h-3 animate-spin inline mr-1" /> : <CheckCircle className="w-3 h-3 inline mr-1" />}
                Ricevi {fmt(loanAmount)}
              </button>

              {loanAmount > status.can_borrow && (
                <p className="text-[9px] text-rose-300 mt-1 text-center">
                  <AlertTriangle className="w-3 h-3 inline mr-0.5" /> Supera il limite disponibile
                </p>
              )}
            </div>
          </div>
        )}

        {tab === 'exchange' && (
          <div className="p-3 bg-sky-500/5 rounded-xl border border-sky-500/20 space-y-3" data-testid="exchange-form">
            <div className="flex items-center gap-1 mb-1">
              <Ticket className="w-3.5 h-3.5 text-sky-400" />
              <p className="text-[10px] font-bold text-sky-200 tracking-wider uppercase">Cambio $ ↔ CinePass</p>
            </div>
            <div className="grid grid-cols-2 gap-1">
              <button onClick={() => setExchangeDir('buy_cp')}
                className={`py-2 rounded text-[10px] font-bold ${exchangeDir === 'buy_cp' ? 'bg-sky-500 text-black' : 'bg-white/5 text-gray-300 border border-white/10'}`}
                data-testid="exchange-buy">
                Compra CP ($ → CP)
              </button>
              <button onClick={() => setExchangeDir('sell_cp')}
                className={`py-2 rounded text-[10px] font-bold ${exchangeDir === 'sell_cp' ? 'bg-sky-500 text-black' : 'bg-white/5 text-gray-300 border border-white/10'}`}
                data-testid="exchange-sell">
                Vendi CP (CP → $)
              </button>
            </div>
            <p className="text-[9px] text-gray-400">Quantità CinePass</p>
            <input type="number" min={1} value={cpAmount} onChange={(e) => setCpAmount(Math.max(1, Number(e.target.value)))}
              className="w-full bg-[#0f0d10] border border-sky-500/30 rounded px-2 py-2 text-white text-sm text-center"
              data-testid="exchange-amount-input" />
            <div className="p-2 rounded-lg bg-black/30 border border-sky-500/15">
              <div className="flex justify-between text-[10px]">
                <span className="text-gray-400">Tasso</span>
                <span className="text-white">{exchangeDir === 'buy_cp' ? fmt(status.cinepass_rate.buy) : fmt(status.cinepass_rate.sell)} / CP</span>
              </div>
              <div className="flex justify-between text-[11px] font-bold border-t border-white/5 pt-1 mt-1">
                <span className="text-sky-200">{exchangeDir === 'buy_cp' ? 'Costo totale' : 'Ricavo'}</span>
                <span className={exchangeDir === 'buy_cp' ? 'text-rose-300' : 'text-emerald-300'}>
                  {exchangeDir === 'buy_cp' ? '-' : '+'}{fmt(cpAmount * (exchangeDir === 'buy_cp' ? status.cinepass_rate.buy : status.cinepass_rate.sell))}
                </span>
              </div>
            </div>
            <button onClick={doExchange} disabled={exchanging || cpAmount <= 0}
              className="w-full py-2 rounded-lg bg-gradient-to-r from-sky-500 to-sky-400 text-black font-bold text-[11px] hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
              data-testid="exchange-submit-btn">
              {exchanging ? <Loader2 className="w-3 h-3 animate-spin inline mr-1" /> : <ArrowRight className="w-3 h-3 inline mr-1" />}
              {exchangeDir === 'buy_cp' ? 'Compra' : 'Vendi'} {cpAmount} CP
            </button>
          </div>
        )}

        {tab === 'infra' && (
          <div className="space-y-3" data-testid="infra-tab">
            {nextTier ? (
              <div className="p-3 bg-gradient-to-br from-amber-500/15 to-transparent rounded-xl border border-amber-500/30">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-[9px] text-amber-300/70 uppercase tracking-wider">Prossimo livello</p>
                    <p className="text-lg font-black text-amber-100" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
                      Lv {nextTier.level} · {nextTier.label}
                    </p>
                  </div>
                  <Building2 className="w-8 h-8 text-amber-400/50" />
                </div>
                <div className="grid grid-cols-2 gap-2 my-2">
                  <div className="p-2 bg-black/20 rounded">
                    <p className="text-[8px] text-gray-500 uppercase">Max Prestito</p>
                    <p className="text-[11px] font-bold text-amber-200">{fmt(nextTier.max_loan_base)}</p>
                  </div>
                  <div className="p-2 bg-black/20 rounded">
                    <p className="text-[8px] text-gray-500 uppercase">Interesse</p>
                    <p className="text-[11px] font-bold text-amber-200">{nextTier.interest_pct}%</p>
                  </div>
                </div>
                <p className="text-[10px] text-gray-400 mb-2">
                  Costo upgrade: <b className="text-rose-300">{fmt(nextTier.upgrade_cost)}</b>
                  {nextTier.upgrade_cinepass > 0 && (
                    <span className="ml-2">+ <b className="text-sky-300">{nextTier.upgrade_cinepass} CP</b></span>
                  )}
                </p>
                <button onClick={upgradeInfra} disabled={upgrading}
                  className="w-full py-2 rounded-lg bg-gradient-to-r from-amber-500 to-yellow-300 text-black font-bold text-[11px] hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
                  data-testid="upgrade-infra-btn">
                  {upgrading ? <Loader2 className="w-3 h-3 animate-spin inline mr-1" /> : <TrendingUp className="w-3 h-3 inline mr-1" />}
                  Potenzia a {nextTier.label}
                </button>
              </div>
            ) : (
              <div className="p-4 text-center bg-amber-500/10 rounded-xl border border-amber-500/30">
                <CheckCircle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                <p className="text-sm font-bold text-amber-200">Livello massimo raggiunto</p>
                <p className="text-[10px] text-gray-400 mt-1">Empire Bank attiva</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TabBtn({ active, onClick, icon, label, testId }) {
  return (
    <button onClick={onClick} data-testid={testId}
      className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-md text-[10px] font-semibold transition-all
        ${active ? 'bg-amber-500 text-black shadow-[0_0_10px_rgba(212,175,55,0.4)]' : 'text-gray-400 hover:text-amber-300'}`}>
      {icon} {label}
    </button>
  );
}
