import React, { useEffect, useState, useContext } from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import { AuthContext } from '../../contexts';

/**
 * BanBanner — banner fixed in fondo visibile a tutti gli utenti con is_banned=true.
 * Glow animato, timer countdown, messaggio del 5° ban.
 */
export default function BanBanner() {
  const { user, api } = useContext(AuthContext);
  const [status, setStatus] = useState(null);
  const [remaining, setRemaining] = useState(null);

  useEffect(() => {
    if (!user) { setStatus(null); return; }
    let mounted = true;
    const fetchStatus = async () => {
      try {
        const r = await api.get('/me/ban-status');
        if (mounted) setStatus(r.data);
      } catch { /* ignore */ }
    };
    fetchStatus();
    const i = setInterval(fetchStatus, 60000); // refresh every 60s
    return () => { mounted = false; clearInterval(i); };
  }, [user?.id, api]);

  // Countdown
  useEffect(() => {
    if (!status?.is_banned || status.is_permanent || !status.remaining_seconds) {
      setRemaining(null);
      return;
    }
    let s = status.remaining_seconds;
    setRemaining(s);
    const t = setInterval(() => {
      s -= 1;
      if (s <= 0) { setRemaining(0); clearInterval(t); }
      else setRemaining(s);
    }, 1000);
    return () => clearInterval(t);
  }, [status]);

  if (!status?.is_banned) return null;

  const fmt = (sec) => {
    if (sec == null) return '—';
    const d = Math.floor(sec / 86400);
    const h = Math.floor((sec % 86400) / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    if (d > 0) return `${d}g ${h}h ${m}m`;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    return `${m}m ${s}s`;
  };

  const banNum = status.ban_count_total || 0;
  const max = status.max_bans_before_deletion || 5;

  return (
    <>
      <style>{`
        @keyframes banGlow {
          0%, 100% { box-shadow: 0 0 14px rgba(244,63,94,0.45), 0 0 32px rgba(244,63,94,0.25); }
          50% { box-shadow: 0 0 24px rgba(244,63,94,0.7), 0 0 56px rgba(244,63,94,0.45); }
        }
        .ban-banner-glow { animation: banGlow 2s ease-in-out infinite; }
      `}</style>
      <div
        className="fixed bottom-2 left-2 right-2 z-[200] rounded-xl border border-rose-500/50 bg-rose-950/30 backdrop-blur-md ban-banner-glow pointer-events-auto"
        data-testid="ban-banner"
        style={{ background: 'rgba(20, 5, 10, 0.55)' }}
      >
        <div className="px-3 py-2 flex items-center gap-2.5">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-rose-500/20 flex items-center justify-center">
            <AlertTriangle className="w-4 h-4 text-rose-300" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-1.5 py-0.5 rounded bg-rose-500/30 border border-rose-500/50 text-rose-100 text-[9px] font-black uppercase tracking-wider">BAN</span>
              {status.is_permanent ? (
                <span className="text-[11px] font-bold text-rose-100">Sospensione permanente</span>
              ) : (
                <span className="text-[11px] font-bold text-rose-100 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {fmt(remaining ?? status.remaining_seconds)}
                </span>
              )}
              <span className="text-[9px] text-rose-300/80 font-bold">
                {banNum}/{max} ban
              </span>
            </div>
            <p className="text-[9px] text-rose-200/85 leading-tight mt-0.5">
              Sola lettura. {status.is_chat_muted ? 'Chat bloccata. ' : ''}
              <span className="text-amber-300 font-bold">Ricorda! Al {max}° ban verrai eliminato dal gioco.</span>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
