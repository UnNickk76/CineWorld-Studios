// CineWorld Studio's — Finance Page (/finanze)
// Full financial dashboard: balance, P&L, cashflow, breakdown, cinepass, bank.

import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import {
  ArrowLeft, TrendingUp, TrendingDown, DollarSign, Ticket, Landmark,
  Wallet, PieChart as PieIcon, BarChart3, History, ChevronRight, Loader2, Globe, MapPin, Building2, X
} from 'lucide-react';
import UserStripBanner from '../components/UserStripBanner';  // not used — handled globally

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
  const [filmsHistory, setFilmsHistory] = useState([]);
  const [selectedFilmDetail, setSelectedFilmDetail] = useState(null);
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
    try {
      const r = await api.get('/finance/films-history');
      setFilmsHistory(r.data?.films || []);
    } catch {
      setFilmsHistory([]);
    }
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
          <HistoryTab films={filmsHistory} onOpen={(f) => setSelectedFilmDetail(f)} />
        )}
      </div>

      {/* Film Detail Modal */}
      {selectedFilmDetail && <FilmDetailModal film={selectedFilmDetail} onClose={() => setSelectedFilmDetail(null)} />}
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
  const totalIn = statements?.total_income || 0;
  const [expensesByType, setExpensesByType] = useState(null);
  const [expenseTab, setExpenseTab] = useState('all');
  const { api } = useContext(AuthContext);

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get('/finance/expenses-by-type');
        setExpensesByType(r.data || null);
      } catch { setExpensesByType(null); }
    })();
  }, [api]);

  const activeExpense = expensesByType?.[expenseTab] || { total: 0, count: 0, label: '—' };
  return (
    <div className="space-y-4">
      {/* Cashflow mini chart */}
      <div className="p-3 bg-[#0f0d10] rounded-xl border border-white/5">
        <div className="flex items-center gap-1 mb-2">
          <BarChart3 className="w-3.5 h-3.5 text-sky-300" />
          <p className="text-[10px] font-bold text-sky-200 tracking-wider uppercase">Flusso Giornaliero</p>
        </div>
        <CashflowChart series={cashflow || []} />
      </div>

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

      {/* Expense by content type (Tutti / Film / Serie TV / Anime) */}
      <div className="p-3 bg-rose-500/5 rounded-xl border border-rose-500/20" data-testid="expense-type-panel">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1">
            <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
            <p className="text-[10px] font-bold text-rose-200 tracking-wider uppercase">Uscite</p>
          </div>
          <p className="text-[11px] font-bold text-rose-100">{fmt(activeExpense.total)}</p>
        </div>
        <div className="grid grid-cols-4 gap-1 mb-2">
          {[
            { k: 'all', label: 'Tutti' },
            { k: 'film', label: 'Film' },
            { k: 'series', label: 'Serie TV' },
            { k: 'anime', label: 'Anime' },
          ].map(t => {
            const v = expensesByType?.[t.k]?.total || 0;
            const active = expenseTab === t.k;
            return (
              <button key={t.k} onClick={() => setExpenseTab(t.k)}
                className={`py-1.5 px-1 rounded-md text-[9px] font-bold transition-all
                  ${active ? 'bg-rose-500 text-white shadow-[0_0_8px_rgba(244,63,94,0.4)]' : 'bg-white/5 text-gray-400 hover:text-rose-300 border border-white/5'}`}
                data-testid={`expense-tab-${t.k}`}>
                <div>{t.label}</div>
                <div className="text-[8px] opacity-80 mt-0.5">{fmtShort(v)}</div>
              </button>
            );
          })}
        </div>
        <div className="text-center py-1 text-[10px] text-gray-400">
          {activeExpense.total > 0 ? (
            <span>{activeExpense.count} transazioni · <b className="text-rose-200">{fmt(activeExpense.total)}</b> totali</span>
          ) : (
            <span>Nessuna uscita in questa categoria</span>
          )}
        </div>
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
  // Filter out days with zero activity — these make the chart look like a solid band
  const active = (series || []).filter(d => (d.income || 0) > 0 || (d.expense || 0) > 0);
  if (!active || active.length === 0) {
    return <p className="text-[10px] text-gray-600 text-center py-3">Nessuna attività nel periodo</p>;
  }
  const w = 320, h = 90, padTop = 12, padBottom = 18, padX = 6;
  const chartH = h - padTop - padBottom;
  const maxVal = Math.max(1, ...active.map(d => Math.max(d.income || 0, d.expense || 0)));
  // Bar width: max 18px, min 4px, distributed evenly across active days
  const slotW = Math.min(40, (w - padX * 2) / active.length);
  const barGroupW = Math.max(6, slotW * 0.7);
  const barW = Math.max(3, (barGroupW - 2) / 2);
  const fmtDay = (d) => {
    try { const dt = new Date(d); return `${dt.getDate()}/${dt.getMonth() + 1}`; } catch { return d; }
  };
  const fmtK = (v) => v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M` : v >= 1_000 ? `${Math.round(v / 1_000)}K` : `${v}`;
  const midY = padTop + chartH / 2;
  return (
    <div>
      <div className="flex items-center justify-between mb-1 text-[8px] text-gray-500 uppercase tracking-wider">
        <span>Max: <b className="text-emerald-300">{fmtK(maxVal)}</b></span>
        <span>{active.length} {active.length === 1 ? 'giorno' : 'giorni'} attivi</span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ height: h }} data-testid="cashflow-chart">
        {/* Horizontal grid lines */}
        <line x1={padX} y1={padTop} x2={w - padX} y2={padTop} stroke="rgba(255,255,255,0.04)" strokeDasharray="1 2" />
        <line x1={padX} y1={midY} x2={w - padX} y2={midY} stroke="rgba(255,255,255,0.1)" />
        <line x1={padX} y1={h - padBottom} x2={w - padX} y2={h - padBottom} stroke="rgba(255,255,255,0.04)" strokeDasharray="1 2" />
        {/* Bars grouped: income (left, green) + expense (right, red) */}
        {active.map((d, i) => {
          const gx = padX + i * slotW + (slotW - barGroupW) / 2;
          const inH = ((d.income || 0) / maxVal) * (chartH / 2 - 2);
          const exH = ((d.expense || 0) / maxVal) * (chartH / 2 - 2);
          return (
            <g key={d.day || i}>
              {d.income > 0 && <rect x={gx} y={midY - inH} width={barW} height={inH} fill="url(#gradGreen)" rx="1.5" />}
              {d.expense > 0 && <rect x={gx + barW + 2} y={midY + 1} width={barW} height={exH} fill="url(#gradRed)" rx="1.5" />}
              <text x={gx + barGroupW / 2} y={h - 4} fill="rgba(200,200,200,0.55)" fontSize="8" textAnchor="middle">{fmtDay(d.day)}</text>
            </g>
          );
        })}
        <defs>
          <linearGradient id="gradGreen" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#059669" stopOpacity="0.7" />
          </linearGradient>
          <linearGradient id="gradRed" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#be123c" stopOpacity="0.7" />
          </linearGradient>
        </defs>
      </svg>
      <div className="flex items-center justify-center gap-3 mt-1">
        <span className="flex items-center gap-1 text-[8px] text-gray-400"><span className="w-1.5 h-1.5 rounded-sm bg-emerald-400" /> Entrate</span>
        <span className="flex items-center gap-1 text-[8px] text-gray-400"><span className="w-1.5 h-1.5 rounded-sm bg-rose-400" /> Uscite</span>
      </div>
    </div>
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
          <p className="text-[9px] text-gray-600 mt-1">Gli incassi verranno categorizzati qui per continente/nazione/città</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {items.map((i, idx) => <AccordionGeoRow key={`${scope}-${i.name}-${idx}`} item={i} scope={scope} />)}
        </div>
      )}
    </div>
  );
}

function AccordionGeoRow({ item, scope }) {
  const [expanded, setExpanded] = useState(false);
  const [children, setChildren] = useState(null);
  const [loading, setLoading] = useState(false);
  const { api } = useContext(AuthContext);

  const childScope = scope === 'continent' ? 'nation' : scope === 'nation' ? 'city' : null;

  const toggle = async () => {
    if (!childScope) return;
    if (expanded) { setExpanded(false); return; }
    if (!children) {
      setLoading(true);
      try {
        const r = await api.get(`/finance/breakdown?scope=${childScope}&parent=${encodeURIComponent(item.name)}&parent_scope=${scope}`);
        setChildren(r.data?.items || []);
      } catch { setChildren([]); }
      setLoading(false);
    }
    setExpanded(true);
  };

  const isZero = item.total === 0;
  return (
    <div className={`rounded-lg border ${isZero ? 'border-white/5 bg-[#0a080b] opacity-60' : 'border-white/5 bg-[#0f0d10]'}`} data-testid={`accordion-${item.name}`}>
      <button onClick={toggle} className="w-full p-2 text-left active:scale-[0.99] transition-transform" disabled={!childScope}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 flex-1 min-w-0">
            {childScope && <ChevronRight className={`w-3 h-3 text-amber-400 transition-transform flex-shrink-0 ${expanded ? 'rotate-90' : ''}`} />}
            <p className="text-[11px] font-semibold text-white truncate">{item.name}</p>
          </div>
          <p className={`text-[11px] font-bold ${isZero ? 'text-gray-500' : 'text-amber-300'}`}>{fmt(item.total)}</p>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-amber-400 to-amber-500" style={{ width: `${Math.min(100, item.share_pct)}%` }} />
          </div>
          <p className="text-[9px] text-gray-500 w-10 text-right">{item.share_pct}%</p>
        </div>
      </button>
      {expanded && (
        <div className="px-2 pb-2 space-y-1 border-t border-white/5">
          {loading ? (
            <div className="flex items-center justify-center py-3"><Loader2 className="w-3 h-3 animate-spin text-amber-400" /></div>
          ) : !children || children.length === 0 ? (
            <p className="text-[9px] text-gray-600 text-center py-2">Nessun dato</p>
          ) : children.map((c, i) => (
            <div key={i} className="flex items-center justify-between p-1.5 rounded bg-black/30">
              <p className="text-[10px] text-gray-300">{c.name}</p>
              <p className="text-[10px] font-bold text-amber-300">{fmt(c.total)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function HistoryTab({ films, onOpen }) {
  if (!films || films.length === 0) {
    return (
      <div className="text-center py-14" data-testid="history-empty">
        <History className="w-8 h-8 text-gray-700 mx-auto mb-2" />
        <p className="text-[11px] text-gray-500">Nessun film rilasciato</p>
        <p className="text-[9px] text-gray-600 mt-1">Distribuisci un film per vederlo qui</p>
      </div>
    );
  }
  return (
    <div className="space-y-2" data-testid="history-films-grid">
      <p className="text-[9px] text-gray-500 uppercase tracking-wider">Tap su una locandina per i dettagli</p>
      <div className="grid grid-cols-5 gap-1.5" data-testid="films-poster-grid">
        {films.map(f => (
          <FilmPosterMini key={f.id} film={f} onClick={() => onOpen(f)} />
        ))}
      </div>
    </div>
  );
}

function FilmPosterMini({ film, onClick }) {
  const profitColor = film.profit >= 0 ? 'text-emerald-300' : 'text-rose-300';
  return (
    <button onClick={onClick} className="flex flex-col items-center gap-0.5 active:scale-95 transition-transform" data-testid={`film-poster-${film.id}`}>
      <div className="relative w-full aspect-[2/3] rounded-md overflow-hidden bg-black border border-white/10 hover:border-amber-500/40">
        {film.poster_url ? (
          <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover" loading="lazy"
               onError={(e) => { e.target.style.display = 'none'; }} />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-amber-900/30 to-black flex items-center justify-center">
            <History className="w-4 h-4 text-amber-400/50" />
          </div>
        )}
        {film.has_la_prima && (
          <div className="absolute top-0.5 left-0.5 bg-amber-500/90 text-black text-[6px] font-black px-1 py-px rounded leading-none tracking-wide">LP</div>
        )}
      </div>
      <p className="text-[8px] text-white font-semibold truncate w-full leading-tight">{film.title}</p>
      <p className={`text-[7px] font-bold ${profitColor}`} data-testid={`film-profit-${film.id}`}>
        {film.profit >= 0 ? '+' : ''}{fmtShort(film.profit)}
      </p>
    </button>
  );
}

function FilmDetailModal({ film, onClose }) {
  if (!film) return null;
  const profitColor = film.profit >= 0 ? 'text-emerald-300' : 'text-rose-300';
  const profitBg = film.profit >= 0 ? 'bg-emerald-500/10 border-emerald-500/25' : 'bg-rose-500/10 border-rose-500/25';
  return (
    <div className="fixed inset-0 z-[2000] bg-black/80 flex items-end sm:items-center justify-center p-0 sm:p-4" onClick={onClose} data-testid="film-detail-modal">
      <div onClick={(e) => e.stopPropagation()}
           className="w-full sm:max-w-md bg-[#0f0d10] border-t sm:border border-amber-500/30 rounded-t-2xl sm:rounded-2xl max-h-[90vh] overflow-y-auto">
        {/* Header with poster */}
        <div className="relative p-3 border-b border-white/10">
          <button onClick={onClose} className="absolute top-2 right-2 w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-white active:scale-90 transition-transform z-10" data-testid="film-detail-close">
            <X className="w-4 h-4" />
          </button>
          <div className="flex gap-3">
            <div className="w-16 aspect-[2/3] rounded-md overflow-hidden bg-black border border-white/10 flex-shrink-0">
              {film.poster_url ? (
                <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-amber-900/30 to-black" />
              )}
            </div>
            <div className="flex-1 min-w-0 pr-7">
              <p className="text-[9px] text-amber-400/70 tracking-wider uppercase">Film</p>
              <h3 className="text-lg font-black text-white leading-tight truncate" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>{film.title}</h3>
              <p className="text-[9px] text-gray-500 mt-0.5">{film.days_in_theaters} {film.days_in_theaters === 1 ? 'giorno' : 'giorni'} al cinema</p>
            </div>
          </div>
        </div>

        {/* Fixed stats */}
        <div className="p-3 space-y-2">
          <div className="grid grid-cols-3 gap-1.5">
            <div className="p-2 rounded-lg bg-rose-500/5 border border-rose-500/15">
              <p className="text-[8px] text-rose-300/80 uppercase tracking-wider">Costo</p>
              <p className="text-[11px] font-bold text-rose-200" data-testid="film-detail-cost">{fmt(film.total_cost)}</p>
            </div>
            <div className="p-2 rounded-lg bg-amber-500/5 border border-amber-500/15">
              <p className="text-[8px] text-amber-300/80 uppercase tracking-wider">Totale</p>
              <p className="text-[11px] font-bold text-amber-200" data-testid="film-detail-total">{fmt(film.total_revenue)}</p>
            </div>
            <div className={`p-2 rounded-lg border ${profitBg}`}>
              <p className="text-[8px] uppercase tracking-wider opacity-80">Profit</p>
              <p className={`text-[11px] font-bold ${profitColor}`} data-testid="film-detail-profit">
                {film.profit >= 0 ? '+' : ''}{fmt(film.profit)}
              </p>
            </div>
          </div>

          {/* La Prima section */}
          {film.has_la_prima && (
            <div className="p-2.5 rounded-lg bg-gradient-to-r from-amber-500/10 to-transparent border border-amber-500/25" data-testid="film-detail-la-prima">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="text-[9px] font-black text-amber-300 tracking-[0.2em] uppercase">La Prima</span>
                  {film.la_prima_city && <span className="text-[9px] text-amber-200/70">· {film.la_prima_city}{film.la_prima_nation ? `, ${film.la_prima_nation}` : ''}</span>}
                </div>
                <span className="text-[11px] font-bold text-amber-300">{fmt(film.la_prima_revenue)}</span>
              </div>
              <p className="text-[8px] text-amber-200/60 mt-0.5">Incasso delle 24h di premiere</p>
            </div>
          )}

          {/* Daily timeline */}
          <div className="mt-1">
            <p className="text-[9px] text-gray-500 uppercase tracking-wider mb-1.5">Incassi giornalieri al cinema</p>
            {(!film.daily_revenues || film.daily_revenues.length === 0) ? (
              <p className="text-[10px] text-gray-600 text-center py-6">Nessun incasso giornaliero ancora registrato.<br/>Aggiornato ogni 24h dal debutto.</p>
            ) : (
              <div className="space-y-1">
                {film.daily_revenues.map((d, i) => {
                  const maxVal = Math.max(...film.daily_revenues.map(x => x.total));
                  const pct = maxVal > 0 ? (d.total / maxVal) * 100 : 0;
                  const dayLabel = d.day ? `Giorno ${d.day}` : d.date;
                  return (
                    <div key={i} className="p-2 rounded bg-[#0a080b] border border-white/5" data-testid={`film-day-${i}`}>
                      <div className="flex items-center justify-between">
                        <p className="text-[10px] font-semibold text-white">{dayLabel}</p>
                        <p className="text-[11px] font-bold text-emerald-300">+{fmt(d.total)}</p>
                      </div>
                      <div className="h-1 bg-white/5 rounded-full overflow-hidden mt-1">
                        <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400" style={{ width: `${pct}%` }} />
                      </div>
                      <p className="text-[8px] text-gray-600 mt-0.5">{d.date}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
