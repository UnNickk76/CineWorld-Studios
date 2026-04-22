// CineWorld Studio's — Finance Page (/finanze)
// Full financial dashboard: balance, P&L, cashflow, breakdown, cinepass, bank.

import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import {
  ArrowLeft, TrendingUp, TrendingDown, DollarSign, Ticket, Landmark,
  Wallet, PieChart as PieIcon, BarChart3, History, ChevronRight, Loader2, Globe, MapPin, Building2
} from 'lucide-react';
import UserStripBanner from '../components/UserStripBanner';

const fmt = (n) => {
  const v = Number(n || 0);
  if (Math.abs(v) >= 1_000_000) return `$${(v / 1_000_000).toFixed(2)}M`;
  if (Math.abs(v) >= 1_000) return `$${(v / 1_000).toFixed(1)}K`;
  return `$${v.toLocaleString()}`;
};
const fmtShort = (n) => {
  const v = Number(n || 0);
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return v.toLocaleString();
};

const SRC_LABELS = {
  box_office: { label: 'Box Office', color: '#f5c24b', icon: '🎬' },
  la_prima: { label: 'La Prima', color: '#fb7185', icon: '✨' },
  tv_broadcast: { label: 'TV', color: '#6366f1', icon: '📺' },
  market: { label: 'Mercato', color: '#10b981', icon: '🛒' },
  production: { label: 'Produzione', color: '#f97316', icon: '🎭' },
  cast: { label: 'Cast', color: '#eab308', icon: '👥' },
  marketing: { label: 'Marketing', color: '#8b5cf6', icon: '📢' },
  infrastructure: { label: 'Infrastrutture', color: '#64748b', icon: '🏢' },
  bank_loan: { label: 'Prestito', color: '#06b6d4', icon: '💰' },
  bank_repay: { label: 'Rata', color: '#f43f5e', icon: '📉' },
  cinepass_exchange: { label: 'CinePass', color: '#14b8a6', icon: '🎟️' },
  other: { label: 'Altro', color: '#9ca3af', icon: '❓' },
};

export default function FinancePage() {
  const { api, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview'); // overview | breakdown | history
  const [overview, setOverview] = useState(null);
  const [statements, setStatements] = useState(null);
  const [cashflow, setCashflow] = useState([]);
  const [breakdown, setBreakdown] = useState({ items: [], scope: 'continent' });
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [ov, stm, cf, bd] = await Promise.all([
          api.get('/finance/overview'),
          api.get(`/finance/statements?days=${period}`),
          api.get(`/finance/cashflow?days=${period}`),
          api.get(`/finance/breakdown?scope=continent&days=${period}`),
        ]);
        setOverview(ov.data);
        setStatements(stm.data);
        setCashflow(cf.data?.series || []);
        setBreakdown({ items: bd.data?.items || [], scope: 'continent' });
      } catch {
        /* noop */
      }
      setLoading(false);
    })();
  }, [api, period]);

  const loadHistory = async () => {
    const r = await api.get('/wallet/transactions?limit=100');
    setTxs(r.data?.transactions || []);
  };

  useEffect(() => {
    if (tab === 'history') loadHistory();
  }, [tab]); // eslint-disable-line

  const changeBreakdownScope = async (scope) => {
    const r = await api.get(`/finance/breakdown?scope=${scope}&days=${period}`);
    setBreakdown({ items: r.data?.items || [], scope });
  };

  return (
    <div className="min-h-screen bg-[#07060a] text-white pb-10" data-testid="finance-page">
      <UserStripBanner />
      <div className="px-3 pt-3 pb-2 flex items-center gap-2">
        <button onClick={() => navigate(-1)} className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-amber-300 active:scale-90 transition-transform" data-testid="finance-back">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1">
          <p className="text-[9px] text-amber-400/70 tracking-[0.3em] font-bold uppercase">CineWorld</p>
          <h1 className="text-lg font-black text-white leading-tight" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>Finanze</h1>
        </div>
        <select value={period} onChange={(e) => setPeriod(Number(e.target.value))}
          className="bg-[#161215] border border-amber-500/20 text-amber-200 text-[10px] px-2 py-1 rounded" data-testid="finance-period-select">
          <option value={1}>24h</option>
          <option value={7}>7 giorni</option>
          <option value={30}>30 giorni</option>
          <option value={90}>90 giorni</option>
        </select>
      </div>

      {/* Balance card */}
      <div className="mx-3 rounded-xl p-4 bg-gradient-to-br from-amber-500/20 via-[#1a1208] to-[#0a0706] border border-amber-500/30 shadow-[0_0_20px_rgba(212,175,55,0.15)]">
        <div className="flex items-center gap-2 mb-1">
          <Wallet className="w-4 h-4 text-amber-400" />
          <p className="text-[9px] text-amber-300/80 tracking-wider uppercase">Saldo Attuale</p>
        </div>
        <p className="text-2xl font-black text-amber-100" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
          {fmt(overview?.balance)}
        </p>
        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-amber-500/15">
          <MiniStat label="Entrate" value={fmt(overview?.income?.[`d${period}`])} color="emerald" arrow="up" />
          <MiniStat label="Uscite" value={fmt(overview?.expenses?.[`d${period}`])} color="rose" arrow="down" />
          <MiniStat label="Netto" value={fmt(overview?.net?.[`d${period}`])} color={overview?.net?.[`d${period}`] >= 0 ? 'emerald' : 'rose'} arrow={overview?.net?.[`d${period}`] >= 0 ? 'up' : 'down'} />
        </div>
      </div>

      {/* Tabs */}
      <div className="mx-3 mt-3 flex gap-1 bg-[#0f0d10] rounded-lg p-1">
        <TabBtn active={tab === 'overview'} onClick={() => setTab('overview')} icon={<PieIcon className="w-3.5 h-3.5" />} label="Conto" testId="ft-overview" />
        <TabBtn active={tab === 'breakdown'} onClick={() => setTab('breakdown')} icon={<Globe className="w-3.5 h-3.5" />} label="Geo" testId="ft-breakdown" />
        <TabBtn active={tab === 'history'} onClick={() => setTab('history')} icon={<History className="w-3.5 h-3.5" />} label="Storico" testId="ft-history" />
        <TabBtn active={false} onClick={() => navigate('/banca')} icon={<Landmark className="w-3.5 h-3.5" />} label="Banca" testId="ft-bank" />
      </div>

      <div className="mx-3 mt-3">
        {loading ? (
          <div className="flex items-center justify-center py-14"><Loader2 className="w-6 h-6 text-amber-400 animate-spin" /></div>
        ) : tab === 'overview' ? (
          <OverviewTab statements={statements} cashflow={cashflow} />
        ) : tab === 'breakdown' ? (
          <BreakdownTab breakdown={breakdown} changeScope={changeBreakdownScope} />
        ) : (
          <HistoryTab txs={txs} />
        )}
      </div>
    </div>
  );
}

function MiniStat({ label, value, color, arrow }) {
  const cls = {
    emerald: 'text-emerald-300', rose: 'text-rose-300', amber: 'text-amber-200',
  }[color] || 'text-gray-300';
  const Arrow = arrow === 'up' ? TrendingUp : TrendingDown;
  return (
    <div className="text-center">
      <p className="text-[8px] text-gray-500 uppercase tracking-wider">{label}</p>
      <div className="flex items-center justify-center gap-0.5">
        <Arrow className={`w-2.5 h-2.5 ${cls}`} />
        <p className={`text-[11px] font-bold ${cls}`}>{value}</p>
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

function OverviewTab({ statements, cashflow }) {
  const income = statements?.income_by_source || [];
  const expense = statements?.expense_by_source || [];
  const totalIn = statements?.total_income || 0;
  const totalOut = statements?.total_expense || 0;
  return (
    <div className="space-y-4">
      {/* Cashflow mini chart */}
      {cashflow.length > 0 && (
        <div className="p-3 bg-[#0f0d10] rounded-xl border border-white/5">
          <div className="flex items-center gap-1 mb-2">
            <BarChart3 className="w-3.5 h-3.5 text-sky-300" />
            <p className="text-[10px] font-bold text-sky-200 tracking-wider uppercase">Flusso Giornaliero</p>
          </div>
          <CashflowChart series={cashflow} />
        </div>
      )}

      {/* Income by source */}
      <div className="p-3 bg-emerald-500/5 rounded-xl border border-emerald-500/20">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <p className="text-[10px] font-bold text-emerald-200 tracking-wider uppercase">Entrate</p>
          </div>
          <p className="text-[11px] font-bold text-emerald-100">{fmt(totalIn)}</p>
        </div>
        {income.length === 0 ? (
          <p className="text-[10px] text-gray-500 text-center py-3">Nessuna entrata nel periodo</p>
        ) : income.map(i => <SourceRow key={`in-${i.source}`} item={i} total={totalIn} direction="in" />)}
      </div>

      {/* Expense by source */}
      <div className="p-3 bg-rose-500/5 rounded-xl border border-rose-500/20">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1">
            <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
            <p className="text-[10px] font-bold text-rose-200 tracking-wider uppercase">Uscite</p>
          </div>
          <p className="text-[11px] font-bold text-rose-100">{fmt(totalOut)}</p>
        </div>
        {expense.length === 0 ? (
          <p className="text-[10px] text-gray-500 text-center py-3">Nessuna uscita nel periodo</p>
        ) : expense.map(i => <SourceRow key={`out-${i.source}`} item={i} total={totalOut} direction="out" />)}
      </div>

      {/* Net profit */}
      <div className={`p-3 rounded-xl border ${statements?.net_profit >= 0 ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-rose-500/10 border-rose-500/30'}`}>
        <p className="text-[9px] text-gray-400 uppercase tracking-wider">Profitto Netto</p>
        <p className={`text-xl font-black ${statements?.net_profit >= 0 ? 'text-emerald-200' : 'text-rose-200'}`} style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
          {statements?.net_profit >= 0 ? '+' : ''}{fmt(statements?.net_profit)}
        </p>
      </div>
    </div>
  );
}

function SourceRow({ item, total, direction }) {
  const meta = SRC_LABELS[item.source] || SRC_LABELS.other;
  const pct = total > 0 ? Math.round((item.amount / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 py-1.5" data-testid={`source-row-${item.source}`}>
      <div className="w-6 h-6 rounded-md flex items-center justify-center text-[10px]" style={{ background: `${meta.color}25`, border: `1px solid ${meta.color}50` }}>
        {meta.icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className="text-[10px] text-white font-semibold">{meta.label}</p>
          <p className="text-[10px] font-bold" style={{ color: meta.color }}>{direction === 'in' ? '+' : '-'}{fmt(item.amount)}</p>
        </div>
        <div className="h-1 bg-white/5 rounded-full overflow-hidden mt-0.5">
          <div className="h-full rounded-full" style={{ width: `${pct}%`, background: meta.color }} />
        </div>
      </div>
    </div>
  );
}

function CashflowChart({ series }) {
  const w = 320, h = 60, pad = 2;
  const maxVal = Math.max(1, ...series.map(d => Math.max(d.income || 0, d.expense || 0)));
  const barW = Math.max(3, (w - pad * 2) / series.length - 2);
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-[60px]">
      {series.map((d, i) => {
        const x = pad + i * ((w - pad * 2) / series.length);
        const inH = (d.income / maxVal) * (h / 2 - 2);
        const exH = (d.expense / maxVal) * (h / 2 - 2);
        return (
          <g key={d.day}>
            <rect x={x} y={h / 2 - inH} width={barW} height={inH} fill="rgba(72,220,120,0.75)" rx="1" />
            <rect x={x} y={h / 2 + 1} width={barW} height={exH} fill="rgba(240,100,100,0.75)" rx="1" />
          </g>
        );
      })}
      <line x1={0} y1={h / 2} x2={w} y2={h / 2} stroke="rgba(255,255,255,0.1)" strokeWidth="0.5" />
    </svg>
  );
}

function BreakdownTab({ breakdown, changeScope }) {
  const { items, scope } = breakdown;
  return (
    <div className="space-y-3">
      <div className="flex gap-1 bg-[#0f0d10] rounded-lg p-1" data-testid="breakdown-scope-tabs">
        {['continent', 'nation', 'city'].map(s => (
          <button key={s} onClick={() => changeScope(s)}
            data-testid={`scope-${s}`}
            className={`flex-1 py-1.5 rounded-md text-[10px] font-bold ${scope === s ? 'bg-amber-500 text-black' : 'text-gray-500'}`}>
            {s === 'continent' ? <Globe className="w-3 h-3 inline mr-1" /> : s === 'nation' ? <Building2 className="w-3 h-3 inline mr-1" /> : <MapPin className="w-3 h-3 inline mr-1" />}
            {s === 'continent' ? 'Continenti' : s === 'nation' ? 'Nazioni' : 'Città'}
          </button>
        ))}
      </div>
      {items.length === 0 ? (
        <div className="text-center py-14">
          <Globe className="w-8 h-8 text-gray-700 mx-auto mb-2" />
          <p className="text-[11px] text-gray-500">Nessun dato geografico</p>
          <p className="text-[9px] text-gray-600 mt-1">Gli incassi La Prima verranno categorizzati qui</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {items.map((i, idx) => (
            <div key={`${scope}-${i.name}`} className="p-2 bg-[#0f0d10] rounded-lg border border-white/5" data-testid={`breakdown-${idx}`}>
              <div className="flex items-center justify-between">
                <p className="text-[11px] font-semibold text-white">{i.name}</p>
                <p className="text-[11px] font-bold text-amber-300">{fmt(i.total)}</p>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-amber-400 to-amber-500" style={{ width: `${i.share_pct}%` }} />
                </div>
                <p className="text-[9px] text-gray-500 w-10 text-right">{i.share_pct}%</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function HistoryTab({ txs }) {
  if (txs.length === 0) return <div className="text-center py-14"><History className="w-8 h-8 text-gray-700 mx-auto mb-2" /><p className="text-[11px] text-gray-500">Nessuna transazione</p></div>;
  return (
    <div className="space-y-1">
      {txs.map(t => {
        const meta = SRC_LABELS[t.source] || SRC_LABELS.other;
        const isIn = t.direction === 'in';
        return (
          <div key={t.id} className="flex items-center gap-2 p-2 bg-[#0f0d10] rounded-lg border border-white/5" data-testid={`tx-${t.id}`}>
            <div className="w-7 h-7 rounded-md flex items-center justify-center text-[10px] flex-shrink-0" style={{ background: `${meta.color}25`, border: `1px solid ${meta.color}50` }}>
              {meta.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[10px] text-white font-semibold truncate">{t.title || meta.label}</p>
              <p className="text-[8px] text-gray-500">
                {meta.label}{t.geo?.city ? ` · ${t.geo.city}` : t.geo?.continent ? ` · ${t.geo.continent}` : ''} · {new Date(t.created_at).toLocaleString('it-IT', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            <p className={`text-[11px] font-bold ${isIn ? 'text-emerald-300' : 'text-rose-300'}`}>
              {isIn ? '+' : '-'}{fmtShort(Math.abs(t.amount))}
            </p>
          </div>
        );
      })}
    </div>
  );
}
