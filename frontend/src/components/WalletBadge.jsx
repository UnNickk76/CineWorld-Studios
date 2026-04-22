// CineWorld Studio's — Wallet Badge with delta arrows + floating toast
// Shows current funds; when funds changes, flashes ▲/▼ arrow + "+X" label for 3s
// and fires a subtle toast via sonner.

import React, { useEffect, useRef, useState, useContext } from 'react';
import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react';
import { AuthContext } from '../contexts';
import { toast } from 'sonner';

const fmt = (n) => {
  if (n == null) return '0';
  const v = Number(n);
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return v.toLocaleString();
};

export default function WalletBadge({ onClick }) {
  const { user, api, refreshUser } = useContext(AuthContext);
  const funds = user?.funds ?? 0;
  const prevFundsRef = useRef(null);
  const [delta, setDelta] = useState(null); // { amount, direction }
  const [hideTimer, setHideTimer] = useState(null);

  // Poll user funds every 60s to catch revenue ticks
  useEffect(() => {
    if (!refreshUser) return;
    const iv = setInterval(() => { refreshUser(); }, 60000);
    return () => clearInterval(iv);
  }, [refreshUser]);

  // Track funds change → show delta
  useEffect(() => {
    if (prevFundsRef.current == null) {
      prevFundsRef.current = funds;
      return;
    }
    const diff = funds - prevFundsRef.current;
    if (diff !== 0) {
      const dir = diff > 0 ? 'up' : 'down';
      setDelta({ amount: Math.abs(diff), direction: dir });
      if (hideTimer) clearTimeout(hideTimer);
      const t = setTimeout(() => setDelta(null), 3200);
      setHideTimer(t);
      // Fetch the recent transaction details for a better toast
      if (api) {
        api.get('/wallet/recent-deltas').then(r => {
          const txs = r.data?.transactions || [];
          const last = txs[0];
          if (!last) return;
          const who = last.title || last.source;
          const where = last.geo?.city ? ` (${last.geo.city})` : last.geo?.continent ? ` [${last.geo.continent}]` : '';
          if (dir === 'up') {
            toast.success(`+$${fmt(Math.abs(last.amount))}`, { description: `${who}${where}`, duration: 2500 });
          } else {
            toast.error(`-$${fmt(Math.abs(last.amount))}`, { description: `${who}${where}`, duration: 2500 });
          }
        }).catch(() => {});
      }
    }
    prevFundsRef.current = funds;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [funds]);

  return (
    <button
      onClick={onClick}
      className="relative flex flex-col items-center bg-yellow-500/10 px-1 py-0.5 rounded border border-yellow-500/20 flex-shrink-0 active:scale-95 transition-transform"
      data-testid="wallet-badge"
    >
      <div className="flex items-center">
        <DollarSign className="w-2 h-2 text-yellow-500" />
        <span className="text-yellow-500 font-bold text-[7px]" data-testid="user-funds">
          {funds >= 1_000_000 ? `${(funds / 1_000_000).toFixed(1)}M` : funds >= 1_000 ? `${(funds / 1_000).toFixed(0)}K` : funds?.toLocaleString() || '0'}
        </span>
      </div>
      <span className="text-[6px] text-yellow-500/70 leading-none">Soldi</span>
      {delta && (
        <div
          className={`absolute -top-2 -right-1 pointer-events-none flex items-center gap-0.5 px-1 py-0.5 rounded-full text-[7px] font-black tracking-tight ${
            delta.direction === 'up'
              ? 'bg-green-500/90 text-black shadow-[0_0_6px_rgba(72,220,100,0.6)]'
              : 'bg-red-500/90 text-white shadow-[0_0_6px_rgba(240,80,80,0.6)]'
          } animate-[walletDelta_3s_ease-out]`}
          data-testid="wallet-delta"
        >
          {delta.direction === 'up' ? <TrendingUp className="w-2 h-2" /> : <TrendingDown className="w-2 h-2" />}
          {delta.direction === 'up' ? '+' : '-'}{fmt(delta.amount)}
        </div>
      )}
      <style>{`
        @keyframes walletDelta {
          0% { transform: translateY(0) scale(0.9); opacity: 0; }
          15% { transform: translateY(-6px) scale(1.1); opacity: 1; }
          80% { transform: translateY(-10px) scale(1); opacity: 1; }
          100% { transform: translateY(-14px) scale(0.9); opacity: 0; }
        }
      `}</style>
    </button>
  );
}
