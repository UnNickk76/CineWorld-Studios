import React, { useContext, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { DollarSign, Ticket, Trophy, Star } from 'lucide-react';

/**
 * UserStripBanner
 * Thin gold semi-transparent fixed strip shown BELOW the top navbar on
 * every page EXCEPT Dashboard. Clickable → navigates to Dashboard.
 * Shows mini double overlapping avatars, username, production house on one row.
 * Mobile-first. Matches the text size of navbar labels (text-[9px]).
 */
export default function UserStripBanner() {
  const { user } = useContext(AuthContext);
  const location = useLocation();
  const navigate = useNavigate();

  // Hide on Dashboard (home) and auth pages
  const onDashboard = location.pathname === '/' || location.pathname === '/dashboard';
  const onAuth = location.pathname.startsWith('/auth');

  if (!user || onDashboard || onAuth) return null;

  const avatar = user.avatar_url || user.avatar || null;
  const nickname = user.nickname || user.name || 'Player';
  const studio = user.studio_name || user.studio || user.production_house || `Studio ${nickname}`;
  const funds = user.funds ?? 0;
  const cinepass = user.cinepass ?? user.cine_pass ?? 0;
  const pstar = user.pstar ?? 0;
  const tstar = user.tstar ?? 0;

  // Add a body class while the banner is visible so content pages can add top padding.
  // Also measure the real TopNavbar height once and expose as --topnav-h.
  useEffect(() => {
    document.body.classList.add('has-user-strip');
    let rafId;
    const measure = () => {
      const nav = document.querySelector('nav.fixed.top-0');
      if (nav) {
        const h = nav.getBoundingClientRect().height;
        if (h > 0) document.documentElement.style.setProperty('--topnav-h', `${Math.round(h)}px`);
      } else {
        rafId = requestAnimationFrame(measure);
      }
    };
    measure();
    window.addEventListener('resize', measure);
    return () => {
      document.body.classList.remove('has-user-strip');
      cancelAnimationFrame(rafId);
      window.removeEventListener('resize', measure);
    };
  }, []);

  const fmtMoney = (n) => {
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
    return `$${n}`;
  };

  return (
    <button
      type="button"
      onClick={() => navigate('/dashboard')}
      data-testid="user-strip-banner"
      aria-label="Vai alla Dashboard per vedere tutte le stats"
      className="user-strip-banner fixed left-0 right-0 z-[45] w-full flex items-center gap-2 px-3 py-1.5 border-b border-yellow-500/25 active:scale-[0.995] transition"
      style={{
        top: 'calc(var(--topnav-h, 56px) + env(safe-area-inset-top, 0px))',
        background: 'linear-gradient(90deg, rgba(250,204,21,0.18) 0%, rgba(180,140,30,0.10) 50%, rgba(250,204,21,0.16) 100%)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
      }}
    >
      {/* Double overlapping avatars */}
      <div className="flex items-center shrink-0" style={{ width: 28 }}>
        <div
          className="w-4 h-4 rounded-full border border-yellow-500/50 bg-gray-900 overflow-hidden"
          style={{ zIndex: 1 }}
          aria-hidden="true"
        >
          {avatar ? (
            <img src={avatar} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-yellow-600/40 to-amber-700/40" />
          )}
        </div>
        <div
          className="w-4 h-4 rounded-full border border-amber-400/60 bg-gray-900 overflow-hidden -ml-2"
          style={{ zIndex: 2 }}
          aria-hidden="true"
        >
          {avatar ? (
            <img src={avatar} alt="" className="w-full h-full object-cover opacity-80" />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-amber-500/50 to-yellow-700/50" />
          )}
        </div>
      </div>

      {/* User info — one row */}
      <div className="flex-1 min-w-0 flex items-center gap-1.5 overflow-hidden">
        <span className="text-[9px] sm:text-[10px] font-bold text-yellow-300 truncate" data-testid="user-strip-nickname">
          {nickname}
        </span>
        <span className="text-[9px] text-gray-500 shrink-0">·</span>
        <span className="text-[9px] sm:text-[10px] text-yellow-200/70 truncate italic" data-testid="user-strip-studio" title={studio}>
          {studio}
        </span>
      </div>

      {/* Quick stats */}
      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
        <span className="flex items-center gap-0.5 text-[9px] font-bold text-green-300" title="Soldi">
          <DollarSign className="w-2.5 h-2.5" />{fmtMoney(funds)}
        </span>
        <span className="flex items-center gap-0.5 text-[9px] font-bold text-cyan-300" title="CinePass">
          <Ticket className="w-2.5 h-2.5" />{cinepass}
        </span>
        {pstar > 0 && (
          <span className="hidden xs:flex items-center gap-0.5 text-[9px] font-bold text-yellow-400" title="PStar">
            <Trophy className="w-2.5 h-2.5" />{Math.round(pstar)}
          </span>
        )}
        {tstar > 0 && (
          <span className="hidden xs:flex items-center gap-0.5 text-[9px] font-bold text-amber-400" title="TStar">
            <Star className="w-2.5 h-2.5" />{Math.round(tstar)}
          </span>
        )}
      </div>
    </button>
  );
}
